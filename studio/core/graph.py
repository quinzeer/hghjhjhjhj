"""Content-addressed graph planner with a locked run manifest and hash-bound gates (ADR-001 decisions 2, 5, 6, 8, 9).

`Graph` validates a list of `StepSpec` and orders it. `Runner.run` walks that order; every step gets a key
(`run_step_key`: `hashing.step_key` over its name, version, params, seed and the *output artifact keys* of its
inputs, salted in a dry or mock run so that such outputs never serve a real run) and is resolved by the first
rule that applies:

d. a step with `requires_approval` is checked first (publication guard, ADR-001 decision 8): `GateNotApproved`
   unless every listed gate approved the exact current output of its subject, in the mode of this run. Nothing
   can bypass it, not even a locked or stored output of the step; a replay that is still approved stays free
   (a read of decisions);
c. gate step: it never reuses anything. Every run reads the decision about the exact output of its subject; an
   approval in the mode of this run becomes the step's output, a small canonical JSON with no date or note
   (so the keys downstream of a gate do not depend on when it was answered). No decision, a pending one, a
   rejection, a revoked approval or a mock decision in a real run leaves the gate waiting, drops its lock and
   blocks everything downstream;
a. the run manifest locked an output for this step under the key computed with the version it was locked
   with: reuse it if the store confirms it (the store binds that step key to that very output), even when the
   step is not deterministic (LLM call, diffusion sample) and even when the graph now declares a new version
   (ADR-001: a new version does not invalidate a video in progress unless `upgrade` names the step), so a
   replay never re-pays a GPU hour or a Claude call. A lock the store contradicts is refused: a manifest is
   trusted for what it says about this run, never for what the store holds;
b. the store already binds an output to this step key: reuse it;
e. otherwise the step runs under budget reservations: reserve -> run -> settle with the measured cost -> check
   the output -> store -> commit (first write wins). While it runs, a heartbeat renews its reservations (a
   step slower than estimated keeps its budget). What the step measured itself (Claude tokens) replaces the
   estimate. An exception raised by the step still charges what it measurably burnt (GPU seconds, the Claude
   call, the tokens the exception reports) and releases what it cannot measure; once the step has returned,
   its cost stays in the ledger whatever fails next, and no output is stored unless its cost was recorded.

The mode of a run (`mock`) is the caller's declaration or'ed with the steps' own: a graph that holds a step
flagged `mock` cannot run as a real run. Every entry the run writes to the ledger carries it.

Every resolved output is locked in the returned manifest and pinned with `owner=run_id`. Graph steps that are
not resolved this time (waiting gate, blocked downstream) lose their previous locks, and artifacts no longer
referenced by the manifest are unpinned so retention may reclaim them. When `run` raises, the exception
carries the partial result and manifest (`partial_run(exc)`): persist that manifest like a returned one.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import heapq
import logging
import math
import threading
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass, field

from studio.core import hashing
from studio.core.artifacts import KINDS
from studio.core.interfaces import (
    ArtifactMissing,
    ArtifactStore,
    CostLedger,
    DecisionSource,
    GateNotApproved,
    PlanResult,
    Reservation,
    StepSpec,
    StoredArtifact,
    StudioError,
)
from studio.domain import (
    CostEntry,
    CostKind,
    GateDecision,
    GateName,
    ResourceClass,
    RunManifest,
    Verdict,
    VideoFormat,
    canonical_json,
    sha256_hex,
)

log = logging.getLogger(__name__)

DEFAULT_LEASE = dt.timedelta(hours=1)
# A reservation's lease covers LEASE_FACTOR times the step's longest time estimate: the reaper must not free
# the budget of a step that is merely slower than estimated (only a heartbeat would remove this bound).
LEASE_FACTOR = 3.0
DECISION_KIND = "json"
DECISION_MEDIA_TYPE = "application/json"
_DURATION_KINDS = frozenset({CostKind.GPU_SECONDS, CostKind.CLAUDE_SECONDS})
_PARTIAL_ATTR = "_studio_partial_run"


# ------------------------------------------------------------------ errors


class GraphError(ValueError):
    """The steps do not form a valid graph (a programming error, raised when the graph is built)."""


class CycleError(GraphError):
    """The dependencies loop. `cycle` lists the steps of one loop, upstream first."""

    def __init__(self, cycle: Sequence[str]) -> None:
        self.cycle = tuple(cycle)
        super().__init__("dependency cycle: " + " -> ".join((*self.cycle, self.cycle[0])))


class StepOutputError(ValueError):
    """A step returned something the store refuses (not `(bytes, kind, media_type)`, unknown kind, malformed
    media type). The check runs after the step's cost was settled: the work was done and is paid."""


class ManifestMismatch(StudioError):
    """The manifest locks an output that the store contradicts: it was edited, or it belongs to another store."""


class CostNotSettled(StudioError):
    """A step ran but the ledger did not record (part of) its measured cost. Its output was not stored, so no
    run can reuse an output whose cost is missing. The unsettled reservations stay held until settled or
    reaped; `pending` lists (reservation id, entry) for the orchestrator to settle later (a reaped reservation
    can still be settled)."""

    def __init__(self, message: str, pending: Sequence[tuple[str, CostEntry]]) -> None:
        super().__init__(message)
        self.pending = tuple(pending)


# ------------------------------------------------------------------ graph


class Graph:
    """A validated DAG of steps with a stable topological order.

    Checks: unique non-empty names, a version per step, inputs that name known steps (no duplicates), JSON
    params, finite positive cost estimates (a zero reservation would pass an exhausted cap: omit the kind
    instead), a `gpu_seconds` estimate on every GPU step, no cycle; a gate step has exactly one input (its
    subject) and no approval requirement of its own; every `requires_approval` subject is upstream of the step.

    The order is the topological order closest to the declaration order: among the steps whose inputs are
    all placed, the one declared first comes first, so a list declared in a valid order keeps its order.
    """

    def __init__(self, steps: Sequence[StepSpec]) -> None:
        self._steps = tuple(steps)
        self._by_name: dict[str, StepSpec] = {}
        for step in self._steps:
            if not step.name:
                raise GraphError("every step needs a name")
            if not step.version:
                raise GraphError(f"step {step.name!r} needs a version")
            if step.name in self._by_name:
                raise GraphError(f"duplicate step name {step.name!r}")
            self._by_name[step.name] = step
        for step in self._steps:
            self._check_step(step)
        self._order = self._toposort()
        self._ancestors: dict[str, frozenset[str]] = {}
        for step in self._order:
            upstream: set[str] = set()
            for name in step.inputs:
                upstream.add(name)
                upstream |= self._ancestors[name]
            self._ancestors[step.name] = frozenset(upstream)
        for step in self._steps:
            for gate, subject in step.requires_approval:
                if subject not in self._by_name:
                    raise GraphError(f"step {step.name!r} requires {gate} on unknown step {subject!r}")
                if subject not in self._ancestors[step.name]:
                    raise GraphError(
                        f"step {step.name!r} requires {gate} on {subject!r}, which is not upstream of it: "
                        "the approved output could not be known when the step runs"
                    )
            if step.publishes:
                self._check_publishing_step(step)

    def _check_publishing_step(self, step: StepSpec) -> None:
        """A publishing step needs the compliance verdict and G2 on one and the same upstream candidate step."""
        subjects: dict[str, set[str]] = {}
        for gate, subject in step.requires_approval:
            subjects.setdefault(GateName(gate).value, set()).add(subject)
        both = subjects.get(GateName.COMPLIANCE.value, set()) & subjects.get(GateName.G2.value, set())
        if not both:
            raise GraphError(
                f"step {step.name!r} publishes: it must require the {GateName.COMPLIANCE.value} verdict and "
                f"{GateName.G2.value} on the same upstream step (requires_approval has {sorted(subjects)})"
            )
        if not any(self._by_name[subject].candidate for subject in both):
            raise GraphError(
                f"step {step.name!r} publishes: the subject of its approvals ({sorted(both)}) must be a candidate step "
                "(candidate=True), the output that carries everything the judges read, not a bare render"
            )

    def _check_step(self, step: StepSpec) -> None:
        if len(set(step.inputs)) != len(step.inputs):
            raise GraphError(f"step {step.name!r} lists an input twice: {step.inputs}")
        unknown = [name for name in step.inputs if name not in self._by_name]
        if unknown:
            raise GraphError(f"step {step.name!r} has unknown inputs {unknown}")
        try:
            canonical_json(dict(step.params))
        except (TypeError, ValueError) as exc:
            raise GraphError(f"step {step.name!r}: params must be JSON-serialisable ({exc})") from exc
        try:
            resource = ResourceClass(step.resource)
            for gate, _ in step.requires_approval:
                GateName(gate)
            if step.gate is not None:
                GateName(step.gate)
        except ValueError as exc:
            raise GraphError(f"step {step.name!r}: {exc}") from exc
        kinds: set[CostKind] = set()
        for kind, amount in step.estimated_cost.items():
            try:
                kinds.add(CostKind(kind))
            except ValueError as exc:
                raise GraphError(f"step {step.name!r}: unknown cost kind {kind!r}") from exc
            if isinstance(amount, bool) or not isinstance(amount, int | float) or not math.isfinite(amount) or amount <= 0:
                raise GraphError(
                    f"step {step.name!r}: estimated {kind} must be finite and > 0, got {amount!r} "
                    "(omit a kind the step does not consume: a zero reservation passes an exhausted cap)"
                )
        if step.gate is not None:
            if len(step.inputs) != 1:
                raise GraphError(f"gate step {step.name!r} needs exactly one input (its subject), got {step.inputs}")
            if step.requires_approval:
                raise GraphError(f"gate step {step.name!r} cannot itself require approvals")
        elif resource is ResourceClass.GPU and CostKind.GPU_SECONDS not in kinds:
            raise GraphError(
                f"GPU step {step.name!r} needs a gpu_seconds estimate: it is what its reservation holds against the caps"
            )

    def _toposort(self) -> tuple[StepSpec, ...]:
        index = {step.name: i for i, step in enumerate(self._steps)}
        missing = {step.name: len(step.inputs) for step in self._steps}
        dependents: dict[str, list[str]] = {step.name: [] for step in self._steps}
        for step in self._steps:
            for name in step.inputs:
                dependents[name].append(step.name)
        ready = [index[name] for name, count in missing.items() if count == 0]
        heapq.heapify(ready)
        order: list[StepSpec] = []
        while ready:
            step = self._steps[heapq.heappop(ready)]
            order.append(step)
            for name in dependents[step.name]:
                missing[name] -= 1
                if missing[name] == 0:
                    heapq.heappush(ready, index[name])
        if len(order) != len(self._steps):
            raise CycleError(self._find_cycle({name for name, count in missing.items() if count > 0}))
        return tuple(order)

    def _find_cycle(self, stuck: set[str]) -> list[str]:
        # Every stuck step has at least one stuck input, so following them must come back to a visited step.
        current = next(step.name for step in self._steps if step.name in stuck)
        path: list[str] = []
        position: dict[str, int] = {}
        while current not in position:
            position[current] = len(path)
            path.append(current)
            current = next(name for name in self._by_name[current].inputs if name in stuck)
        cycle = list(reversed(path[position[current] :]))  # upstream first
        first = min(range(len(cycle)), key=lambda i: self._steps.index(self._by_name[cycle[i]]))
        return cycle[first:] + cycle[:first]

    @property
    def steps(self) -> tuple[StepSpec, ...]:
        """Steps in declaration order."""
        return self._steps

    @property
    def order(self) -> tuple[StepSpec, ...]:
        """Steps in topological order."""
        return self._order

    @property
    def names(self) -> tuple[str, ...]:
        """Step names in topological order."""
        return tuple(step.name for step in self._order)

    def ancestors(self, name: str) -> frozenset[str]:
        """Every step `name` depends on, directly or not (KeyError for an unknown step)."""
        return self._ancestors[name]

    def descendants(self, name: str) -> frozenset[str]:
        """Every step that depends on `name`, directly or not (KeyError for an unknown step)."""
        if name not in self._by_name:
            raise KeyError(name)
        return frozenset(n for n, upstream in self._ancestors.items() if name in upstream)

    def __getitem__(self, name: str) -> StepSpec:
        return self._by_name[name]

    def __contains__(self, name: object) -> bool:
        return name in self._by_name

    def __iter__(self) -> Iterator[StepSpec]:
        return iter(self._order)

    def __len__(self) -> int:
        return len(self._steps)


# ------------------------------------------------------------------ results


@dataclass(frozen=True)
class WastedOutput:
    """An output computed in vain: another producer committed the same step key first (first write wins).

    Its cost was really incurred, so it stays in the ledger and in the manifest; the discarded artifact is
    unpinned at the end of the run unless the run uses it elsewhere."""

    step: str
    step_key: str
    discarded_key: str
    kept_key: str
    costs: tuple[CostEntry, ...]


@dataclass
class RunResult(PlanResult):
    """`PlanResult` plus what a report needs to explain a run.

    A gate recorded this time counts as executed. `blocked` lists the steps downstream of a waiting gate (no
    key can be computed for them); `reasons` says why each waiting gate waits. A step that raised is charged
    what it measurably burnt (its entries are in `costs` and in the manifest); `unbilled` holds only what the
    ledger failed to record, for the orchestrator to settle later. `kept_versions` maps a step to the version its
    locked output was kept under while the graph declares another one."""

    blocked: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)
    costs: list[CostEntry] = field(default_factory=list)
    wasted: list[WastedOutput] = field(default_factory=list)
    unbilled: list[CostEntry] = field(default_factory=list)
    kept_versions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PartialRun:
    """What a `Runner.run` that raised had resolved: the outputs it produced (a render awaiting its G2, the
    costs already paid) are locked and pinned in `manifest`, which the caller persists like a returned one."""

    result: RunResult
    manifest: RunManifest


def partial_run(exc: BaseException) -> PartialRun | None:
    """The partial run carried by an exception raised from `Runner.run`, or None."""
    value = getattr(exc, _PARTIAL_ATTR, None)
    return value if isinstance(value, PartialRun) else None


# ------------------------------------------------------------------ keys, decisions and costs


def run_step_key(step: StepSpec, version: str, inputs: Mapping[str, str], *, dry_run: bool, mock: bool) -> str:
    """Key of `step` in a run of the given mode.

    A real run uses `hashing.step_key` as is. A dry or mock run salts it, so each mode has a key space of its
    own and the store can never hand a real run a mock render or a dry-run publication plan (MISSION §3.2); a
    manifest of one mode is already refused by the others."""
    key = hashing.step_key(step.name, version, inputs, step.params, step.seed)
    if not dry_run and not mock:
        return key
    return sha256_hex(canonical_json({"step_key": key, "dry_run": dry_run, "mock": mock}))


def decision_refusal(decision: GateDecision | None, gate: GateName, subject_key: str, *, mock_run: bool) -> str | None:
    """None when `decision` approves `gate` on exactly `subject_key` in a run of this mode, else why it does not.

    A decision written by a mock reviewer applies to mock runs only, and a real reviewer's to real runs only:
    the decision store is keyed by the artifact's hash, and deterministic mock work can reproduce the bytes of
    another run."""
    if decision is None:
        return f"no {gate.value} decision on {subject_key}"
    if decision.gate is not gate or decision.subject_key != subject_key:
        return f"the {decision.gate.value} decision found is about {decision.subject_key}, not {gate.value} on {subject_key}"
    if decision.mock != mock_run:
        written, run = ("mock", "real") if decision.mock else ("real", "mock")
        return f"the {gate.value} decision was written by a {written} reviewer: it does not apply to a {run} run"
    if decision.approved:
        return None
    verdicts = f"agent {decision.agent_verdict.value}, human {decision.human_verdict.value}"
    if Verdict.REJECT in (decision.agent_verdict, decision.human_verdict):
        details = "; ".join(s for s in (*decision.agent_reasons, decision.human_note) if s)
        return f"{gate.value} rejected ({verdicts})" + (f": {details}" if details else "")
    return f"{gate.value} pending ({verdicts})"


def _reservation_plan(step: StepSpec) -> dict[CostKind, float]:
    """Amount to reserve per kind: the estimates, plus one Claude call for an LLM step."""
    plan = {CostKind(kind): float(amount) for kind, amount in step.estimated_cost.items()}
    if ResourceClass(step.resource) is ResourceClass.LLM:
        plan[CostKind.CLAUDE_CALLS] = max(plan.get(CostKind.CLAUDE_CALLS, 0.0), 1.0)
    return dict(sorted(plan.items(), key=lambda item: item[0].value))


def _measured(step: StepSpec, kind: CostKind, elapsed_s: float, reported: Mapping[CostKind, float]) -> float | None:
    """The quantity known for this kind (reported by the step or its exception, else measured by the runner), or
    None when only the estimate is known."""
    if kind in reported:
        return reported[kind]
    resource = ResourceClass(step.resource)
    if resource is ResourceClass.GPU and kind is CostKind.GPU_SECONDS:
        return elapsed_s
    if resource is ResourceClass.LLM and kind is CostKind.CLAUDE_CALLS:
        return 1.0
    if resource is ResourceClass.LLM and kind is CostKind.CLAUDE_SECONDS:
        return elapsed_s
    return None


def _valid_costs(value: object) -> dict[CostKind, float]:
    """The well-formed entries of a `{kind: quantity}` mapping (unknown kinds and bad quantities are skipped)."""
    costs: dict[CostKind, float] = {}
    if isinstance(value, Mapping):
        for raw_kind, quantity in value.items():
            try:
                kind = CostKind(raw_kind)
            except ValueError:
                continue
            if isinstance(quantity, int | float) and not isinstance(quantity, bool) and math.isfinite(quantity) and quantity >= 0:
                costs[kind] = float(quantity)
    return costs


def _reported_by_step(output: object) -> dict[CostKind, float]:
    """What a step measured itself: the fourth element of its result, when it is a well-formed mapping."""
    return _valid_costs(output[3]) if isinstance(output, tuple) and len(output) == 4 else {}


def _reported_by_exception(exc: BaseException) -> dict[CostKind, float]:
    """What a failing call reports it consumed (`measured_costs`, e.g. the tokens of a refused Claude call)."""
    return _valid_costs(getattr(exc, "measured_costs", None))


def _check_output(step: StepSpec, output: object) -> tuple[bytes, str, str]:
    """The step's `(data, kind, media_type)`, checked against the store's rules before anything is written.

    A step may add a fourth element, `{CostKind: quantity}`, for what it measured itself (Claude tokens)."""
    if not isinstance(output, tuple) or len(output) not in (3, 4):
        raise StepOutputError(f"step {step.name!r} must return (data, kind, media_type[, measured]), got {type(output).__name__}")
    data, kind, media_type = output[:3]
    if not isinstance(data, bytes):
        raise StepOutputError(f"step {step.name!r} returned {type(data).__name__} data, expected bytes")
    if not isinstance(kind, str) or kind not in KINDS:
        raise StepOutputError(f"step {step.name!r} returned unknown artifact kind {kind!r}; expected one of {sorted(KINDS)}")
    if not isinstance(media_type, str) or "/" not in media_type:
        raise StepOutputError(f"step {step.name!r} returned an invalid media type {media_type!r}")
    if len(output) == 4:
        measured = output[3]
        if not isinstance(measured, Mapping) or len(_valid_costs(measured)) != len(measured):
            raise StepOutputError(f"step {step.name!r} returned measured costs that are not {{CostKind: finite quantity >= 0}}")
    return data, kind, media_type


# ------------------------------------------------------------------ runner


@dataclass
class _RunState:
    """Everything one `Runner.run` call accumulates (the runner itself keeps no state)."""

    run_id: str
    scopes: tuple[str, ...]
    base: RunManifest
    dry_run: bool
    mock: bool
    upgrade: frozenset[str]
    result: RunResult
    versions: dict[str, str] = field(default_factory=dict)  # step name -> version its output was produced with
    pinned: set[str] = field(default_factory=set)  # every artifact this call pinned for run_id
    processed: set[str] = field(default_factory=set)  # steps resolved, waiting or blocked (not those never reached)


class Runner:
    """Plans and runs a `Graph` for one video (one `run_id`) against a store, a ledger and a decision source.

    The runner keeps no state between calls: several runners (or threads) may share the same backends, the
    store's first-write-wins commit arbitrating a step computed twice. A reservation's lease is the longest of
    `lease` and `lease_factor` times the step's time estimate (GPU or Claude seconds); while the step runs, a
    heartbeat extends it every `renew_every` (default a third of `lease`), so a slow step keeps its budget."""

    def __init__(
        self,
        store: ArtifactStore,
        ledger: CostLedger,
        decisions: DecisionSource,
        clock: Callable[[], dt.datetime],
        executor_id: str,
        lease: dt.timedelta = DEFAULT_LEASE,
        lease_factor: float = LEASE_FACTOR,
        renew_every: dt.timedelta | None = None,
    ) -> None:
        if not executor_id:
            raise ValueError("executor_id is required")
        if lease <= dt.timedelta(0):
            raise ValueError("lease must be positive")
        if not math.isfinite(lease_factor) or lease_factor < 1:
            raise ValueError("lease_factor must be finite and >= 1")
        renew_every = lease / 3 if renew_every is None else renew_every
        if renew_every <= dt.timedelta(0):
            raise ValueError("renew_every must be positive")
        self.store = store
        self.ledger = ledger
        self.decisions = decisions
        self.clock = clock
        self.executor_id = executor_id
        self.lease = lease
        self.lease_factor = lease_factor
        self.renew_every = renew_every

    def run(
        self,
        graph: Graph,
        run_id: str,
        scopes: Sequence[str],
        manifest: RunManifest | None = None,
        channel_id: str | None = None,
        format: VideoFormat | None = None,
        dry_run: bool = True,
        mock: bool = True,
        upgrade: Collection[str] = (),
    ) -> tuple[RunResult, RunManifest]:
        """Resolve every step it can; return what happened and the updated manifest.

        `scopes` are the budget scopes every reservation is made on (video, day, month…). A new run needs
        `channel_id` and `format`; a resumed run passes its manifest, which must match `run_id` and `dry_run`
        (a dry-run manifest is never reused by a real run, nor the reverse). `mock` says whether the graph's
        steps use mock adapters: it salts the step keys and makes the manifest's `mock` flag sticky. `upgrade`
        names the steps whose locked output must give way to the graph's new version of the step.

        Raises `GateNotApproved` (publication guard), `BudgetExceeded` (a cap would be passed), `CostNotSettled`,
        `StepOutputError` and whatever a step raises; nothing is left reserved by the runner when they propagate,
        except a cost the ledger failed to settle. The exception carries the partial run (`partial_run`)."""
        if isinstance(scopes, str):
            raise TypeError("scopes must be a sequence of scope names, not a single string")
        scope_list = tuple(scopes)
        if not scope_list or not all(scope_list):
            raise ValueError("at least one non-empty budget scope is required")
        if isinstance(upgrade, str):
            raise TypeError("upgrade must be a collection of step names, not a single string")
        unknown = sorted(set(upgrade) - set(graph.names))
        if unknown:
            raise ValueError(f"cannot upgrade unknown steps {unknown}")
        mock_steps = [step.name for step in graph.steps if step.mock]
        if mock_steps and not mock:
            raise ValueError(f"steps {mock_steps} use mock adapters: a graph that holds them runs as a mock run (mock=True)")
        # Reservations whose lease ran out belong to a worker that died mid-step: free their budget before reserving.
        self.ledger.reap_expired(self.clock())
        base = self._base_manifest(run_id, manifest, channel_id, format, dry_run, mock)
        state = _RunState(
            run_id=run_id,
            scopes=scope_list,
            base=base,
            dry_run=dry_run,
            mock=mock,
            upgrade=frozenset(upgrade),
            result=RunResult(run_id=run_id, step_keys={}, outputs={}, executed=[], skipped=[], waiting=[]),
        )
        try:
            for step in graph.order:
                self._resolve(step, state)
                state.processed.add(step.name)
        except BaseException as exc:
            self._attach_partial(exc, state)
            raise
        return state.result, self._lock(state)

    # ------------------------------------------------------------------ resolution rules

    def _resolve(self, step: StepSpec, state: _RunState) -> None:
        result = state.result
        if any(name not in result.outputs for name in step.inputs):
            result.blocked.append(step.name)
            return
        inputs = {name: result.outputs[name] for name in step.inputs}
        if step.requires_approval:
            self._check_approvals(step, result.outputs, state)
        key = run_step_key(step, step.version, inputs, dry_run=state.dry_run, mock=state.mock)
        if step.gate is not None:
            result.step_keys[step.name] = key
            state.versions[step.name] = step.version
            self._resolve_gate(step, GateName(step.gate), key, inputs, state)
            return
        reused = self._reuse(step, key, inputs, state)
        if reused is not None:
            key, output, version = reused
            result.step_keys[step.name] = key
            state.versions[step.name] = version
            result.skipped.append(step.name)
            result.outputs[step.name] = output
            return
        result.step_keys[step.name] = key
        state.versions[step.name] = step.version
        output = self._execute(step, key, inputs, state)
        result.executed.append(step.name)
        result.outputs[step.name] = output

    def _reuse(self, step: StepSpec, key: str, inputs: Mapping[str, str], state: _RunState) -> tuple[str, str, str] | None:
        """(step key, output, version) of a locked or stored output of this step, or None."""
        base = state.base
        locked = base.locked.get(step.name)
        locked_key = base.step_keys.get(step.name)
        if locked is not None and locked_key is not None:
            locked_version = base.versions.get(step.name, step.version)
            version = step.version if step.name in state.upgrade else locked_version
            lock_key = (
                key if version == step.version else run_step_key(step, version, inputs, dry_run=state.dry_run, mock=state.mock)
            )
            if lock_key == locked_key:
                bound_to_lock = self.store.step_output(locked_key)
                if bound_to_lock is not None and bound_to_lock != locked:
                    raise ManifestMismatch(
                        f"the manifest of run {state.run_id!r} locks step {step.name!r} to {locked}, but the store binds "
                        f"its step key to {bound_to_lock}: the manifest was edited or belongs to another store"
                    )
                if self._hold(locked, state):
                    if bound_to_lock is None:  # the store lost its link but kept the artifact: the manifest restores it
                        if self.store.commit_step_output(locked_key, locked) != locked:
                            raise ManifestMismatch(
                                f"step {step.name!r} was bound to another output while its lock was being restored"
                            )
                    if version != step.version:
                        state.result.kept_versions[step.name] = version
                        log.info(
                            "step %s keeps its output locked under version %s (graph declares %s)",
                            step.name,
                            version,
                            step.version,
                            extra=self._log_extra(step, locked_key, state.run_id, artifact=locked),
                        )
                    return locked_key, locked, version
                log.warning(
                    "locked output of %s is missing from the store: recomputing",
                    step.name,
                    extra=self._log_extra(step, key, state.run_id, artifact=locked),
                )
        bound = self.store.step_output(key)
        if bound is not None and self._hold(bound, state):
            return key, bound, step.version
        return None

    def _hold(self, artifact_key: str, state: _RunState) -> bool:
        """Pin an existing artifact for this run; False when it is gone (purged or lost)."""
        if not self.store.has(artifact_key):
            return False
        try:
            self.store.pin(artifact_key, state.run_id)
        except ArtifactMissing:
            return False
        state.pinned.add(artifact_key)
        return True

    def _resolve_gate(self, step: StepSpec, gate: GateName, key: str, inputs: Mapping[str, str], state: _RunState) -> None:
        """Read the decision about the exact output of the gate's subject, every run.

        An approval in this run's mode becomes the gate's output; anything else leaves the gate waiting, whatever
        an earlier run locked: a revoked approval stops the video at once."""
        result = state.result
        (subject_key,) = inputs.values()
        decision = self.decisions.get(gate, subject_key)
        refusal = decision_refusal(decision, gate, subject_key, mock_run=state.mock)
        if refusal is not None:
            result.reasons[step.name] = refusal
            result.waiting.append(step.name)
            log.info("gate %s waiting: %s", step.name, refusal, extra=self._log_extra(step, key, state.run_id))
            return
        token = canonical_json({"gate": gate.value, "subject_key": subject_key, "approved": True}).encode("utf-8")
        stored = self.store.put_bytes(token, kind=DECISION_KIND, media_type=DECISION_MEDIA_TYPE)
        already = self.store.step_output(key) == stored.key
        bound = self._commit(key, stored, state)
        result.outputs[step.name] = self._adopt(step, key, stored, bound, (), state)
        (result.skipped if already else result.executed).append(step.name)

    def _check_approvals(self, step: StepSpec, outputs: Mapping[str, str], state: _RunState) -> None:
        for gate_value, subject in step.requires_approval:
            gate = GateName(gate_value)
            subject_key = outputs[subject]  # the subject is upstream (Graph) and the step is not blocked
            refusal = decision_refusal(self.decisions.get(gate, subject_key), gate, subject_key, mock_run=state.mock)
            if refusal is not None:
                raise GateNotApproved(f"{step.name} needs {gate.value} on {subject!r}: {refusal}")

    def _execute(self, step: StepSpec, key: str, inputs: Mapping[str, str], state: _RunState) -> str:
        resolved: dict[str, StoredArtifact] = {name: self.store.get(artifact) for name, artifact in inputs.items()}
        lease = self.lease_for(step)
        reservations: list[Reservation] = []
        started: dt.datetime | None = None
        try:
            for kind, amount in _reservation_plan(step).items():
                reservations.append(self.ledger.reserve(state.scopes, kind, amount, lease))
        except BaseException:
            self._release(reservations, step, key, state.run_id)
            raise
        stop = threading.Event()
        heartbeat: threading.Thread | None = None
        if reservations:
            heartbeat = threading.Thread(
                target=self._renew_loop,
                args=(stop, tuple(reservations), lease, step, key, state.run_id),
                name=f"renew-{step.name}",
                daemon=True,
            )
            heartbeat.start()
        try:
            started = self.clock()
            output: object = step.run(resolved, step.params)
        except BaseException as exc:
            stop.set()
            if heartbeat is not None:
                heartbeat.join()
            self._charge_failed(exc, step, key, reservations, started, state)
            raise
        stop.set()
        if heartbeat is not None:
            heartbeat.join()
        elapsed_s = max(0.0, (self.clock() - started).total_seconds())
        # From here on the work is done: its cost is recorded before anything else can fail.
        costs = self._settle(step, key, reservations, elapsed_s, _reported_by_step(output), state)
        data, kind_name, media_type = _check_output(step, output)
        stored = self.store.put_bytes(data, kind=kind_name, media_type=media_type)
        bound = self._commit(key, stored, state)
        log.info("step %s executed", step.name, extra=self._log_extra(step, key, state.run_id, artifact=stored.key))
        return self._adopt(step, key, stored, bound, costs, state)

    def _renew_loop(
        self,
        stop: threading.Event,
        reservations: Sequence[Reservation],
        lease: dt.timedelta,
        step: StepSpec,
        key: str,
        run_id: str,
    ) -> None:
        """Heartbeat of a running step: extend its reservations' lease until `stop` is set."""
        while not stop.wait(self.renew_every.total_seconds()):
            until = self.clock() + lease
            for reservation in reservations:
                try:
                    self.ledger.renew(reservation.id, until)
                except Exception:  # the step carries on; at worst the reaper frees this reservation early
                    log.exception("could not renew reservation %s", reservation.id, extra=self._log_extra(step, key, run_id))

    def lease_for(self, step: StepSpec) -> dt.timedelta:
        """Lease of the step's reservations: long enough that the reaper leaves a slow but live step alone."""
        seconds = max(
            (float(amount) for kind, amount in step.estimated_cost.items() if CostKind(kind) in _DURATION_KINDS),
            default=0.0,
        )
        return max(self.lease, dt.timedelta(seconds=self.lease_factor * seconds))

    def _settle(
        self,
        step: StepSpec,
        key: str,
        reservations: Sequence[Reservation],
        elapsed_s: float,
        reported: Mapping[CostKind, float],
        state: _RunState,
    ) -> tuple[CostEntry, ...]:
        """Settle every reservation with the measured cost (the estimate, flagged, when it cannot be measured).

        Never releases: a reservation the ledger fails to settle stays held until settled or reaped."""
        at = self.clock()
        settled: list[CostEntry] = []
        pending: list[tuple[str, CostEntry]] = []
        first_error: Exception | None = None
        for reservation in reservations:
            measured = _measured(step, reservation.kind, elapsed_s, reported)
            entry = CostEntry(
                run_id=state.run_id,
                step_key=key,
                kind=reservation.kind,
                quantity=reservation.amount if measured is None else measured,
                estimated=measured is None,
                mock=state.mock,
                at=at,
            )
            try:
                self.ledger.settle(reservation.id, entry)
            except Exception as exc:
                first_error = first_error or exc
                pending.append((reservation.id, entry))
                log.exception("could not settle reservation %s", reservation.id, extra=self._log_extra(step, key, state.run_id))
            else:
                settled.append(entry)
        state.result.costs.extend(settled)
        if pending:
            kinds = ", ".join(entry.kind.value for _, entry in pending)
            raise CostNotSettled(
                f"step {step.name!r} ran but its {kinds} cost was not recorded: output not stored", pending
            ) from first_error
        return tuple(settled)

    def _charge_failed(
        self,
        exc: BaseException,
        step: StepSpec,
        key: str,
        reservations: Sequence[Reservation],
        started: dt.datetime | None,
        state: _RunState,
    ) -> None:
        """A step that raised burnt what it burnt: charge the measured cost, release what cannot be measured.

        Never replaces the step's own error. A cost the ledger fails to record goes to `RunResult.unbilled`."""
        if started is None:
            self._release(reservations, step, key, state.run_id)
            return
        try:
            at = self.clock()
            elapsed_s = max(0.0, (at - started).total_seconds())
            reported = _reported_by_exception(exc)
            for reservation in reservations:
                measured = _measured(step, reservation.kind, elapsed_s, reported)
                if measured is None:
                    self._release([reservation], step, key, state.run_id)
                    continue
                entry = CostEntry(
                    run_id=state.run_id, step_key=key, kind=reservation.kind, quantity=measured, mock=state.mock, at=at
                )
                try:
                    self.ledger.settle(reservation.id, entry)
                except Exception:
                    log.exception(
                        "could not charge the failed attempt of %s", step.name, extra=self._log_extra(step, key, state.run_id)
                    )
                    state.result.unbilled.append(entry)
                    continue
                state.result.costs.append(entry)
                with contextlib.suppress(Exception):  # some C-extension exceptions refuse notes
                    exc.add_note(f"{step.name}: {measured:g} {reservation.kind.value} consumed by the failed attempt and charged")
            log.warning(
                "step %s failed after %.1f s: measured cost charged",
                step.name,
                elapsed_s,
                extra=self._log_extra(step, key, state.run_id),
            )
        except Exception:  # reporting must never replace the step's own error
            log.exception("could not charge the failed attempt of %s", step.name, extra=self._log_extra(step, key, state.run_id))

    def _commit(self, key: str, stored: StoredArtifact, state: _RunState) -> str:
        """Pin our output (so retention cannot take it meanwhile), then bind the step: first write wins."""
        self.store.pin(stored.key, state.run_id)
        state.pinned.add(stored.key)
        return self.store.commit_step_output(key, stored.key)

    def _adopt(
        self,
        step: StepSpec,
        key: str,
        stored: StoredArtifact,
        bound: str,
        costs: tuple[CostEntry, ...],
        state: _RunState,
    ) -> str:
        """Keep the output actually bound; when another producer won, hold its output and log ours as waste.

        The discarded artifact is not unpinned here: the same bytes may be another step's output of this run.
        `_lock` unpins whatever the final manifest does not reference."""
        if bound == stored.key:
            return bound
        self.store.pin(bound, state.run_id)
        state.pinned.add(bound)
        state.result.wasted.append(WastedOutput(step.name, key, stored.key, bound, costs))
        log.warning(
            "step %s was committed first by another producer: output discarded, cost logged as waste",
            step.name,
            extra=self._log_extra(step, key, state.run_id, artifact=stored.key),
        )
        return bound

    def _release(self, reservations: Sequence[Reservation], step: StepSpec, key: str, run_id: str) -> None:
        for reservation in reservations:
            try:
                self.ledger.release(reservation.id)
            except Exception:  # the lease reaper frees it later; the original error matters more
                log.exception("could not release reservation %s", reservation.id, extra=self._log_extra(step, key, run_id))

    # ------------------------------------------------------------------ manifest

    @staticmethod
    def _base_manifest(
        run_id: str,
        manifest: RunManifest | None,
        channel_id: str | None,
        format: VideoFormat | None,
        dry_run: bool,
        mock: bool,
    ) -> RunManifest:
        if not run_id:
            raise ValueError("run_id is required")
        if manifest is None:
            if channel_id is None or format is None:
                raise ValueError("a new run needs channel_id and format")
            return RunManifest(run_id=run_id, channel_id=channel_id, format=format, dry_run=dry_run, mock=mock)
        if manifest.run_id != run_id:
            raise ValueError(f"manifest belongs to run {manifest.run_id!r}, not {run_id!r}")
        if channel_id is not None and channel_id != manifest.channel_id:
            raise ValueError(f"manifest is for channel {manifest.channel_id!r}, not {channel_id!r}")
        if format is not None and VideoFormat(format) is not manifest.format:
            raise ValueError(f"manifest is for format {manifest.format.value!r}, not {format!r}")
        if manifest.dry_run != dry_run:
            raise ValueError(f"manifest has dry_run={manifest.dry_run}: it cannot be reused with dry_run={dry_run}")
        return manifest

    def _lock(self, state: _RunState) -> RunManifest:
        """The manifest after this call, and the pins brought in line with it.

        Locks of processed steps not resolved this time are stale (their inputs changed or wait for a gate);
        locks of steps never reached (the run raised before them) and of steps outside the graph are kept."""
        base, result = state.base, state.result
        locked = {name: key for name, key in base.locked.items() if name not in state.processed}
        step_keys = {name: key for name, key in base.step_keys.items() if name not in state.processed}
        versions = {name: v for name, v in base.versions.items() if name not in state.processed}
        for name, artifact_key in result.outputs.items():
            locked[name] = artifact_key
            step_keys[name] = result.step_keys[name]
            versions[name] = state.versions[name]
        manifest = RunManifest(
            run_id=base.run_id,
            channel_id=base.channel_id,
            format=base.format,
            dry_run=base.dry_run,
            locked=locked,
            step_keys=step_keys,
            costs=(*base.costs, *result.costs),
            versions=versions,
            mock=base.mock or state.mock,
        )
        for stale in sorted((set(base.locked.values()) | state.pinned) - set(locked.values())):
            try:
                self.store.unpin(stale, base.run_id)
            except Exception:  # a pin left behind only delays retention; the manifest matters more
                log.exception("could not unpin %s for run %s", stale, base.run_id)
        return manifest

    def _attach_partial(self, exc: BaseException, state: _RunState) -> None:
        try:
            setattr(exc, _PARTIAL_ATTR, PartialRun(state.result, self._lock(state)))
        except Exception:  # the original error must propagate unchanged
            log.exception("could not attach the partial manifest of run %s", state.run_id)

    def _log_extra(self, step: StepSpec, key: str, run_id: str, artifact: str | None = None) -> dict[str, str]:
        extra = {"run_id": run_id, "step": step.name, "step_key": key, "executor_id": self.executor_id}
        if artifact is not None:
            extra["artifact_key"] = artifact
        return extra
