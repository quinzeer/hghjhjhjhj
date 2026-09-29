"""Dry-run driver: one video, end to end, through mock adapters (docs/design/phase1.md).

`run_dry` runs the graph the way production will: a run stops at every gate that has no decision, a reviewer
records one, and the run resumes with every finished step reused. Here the reviewers are mocks; in
production the compliance agent and the human (validation UI) write the same `GateDecision` rows.

State lives under `out_dir/state` (SQLite index, cost ledger, decisions, content-addressed files, scratch
files), so a second invocation with the same channel, format and seed reuses everything: it executes no step
and writes the same render. Files for people go under `out_dir/<channel>/<format>/`; every JSON among them says
`mock`. One process at a time owns a state folder: a second `studio run` on it is refused, and a process that
was killed leaves nothing that blocks the next one (its reservations are freed, its scratch files removed).
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
import os
import shutil
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from studio.adapters.llm_base import LLMRunner, QuotaExhausted
from studio.core.artifacts import LocalArtifactStore
from studio.core.costs import SqlCostLedger
from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.graph import Graph, Runner, RunResult, partial_run
from studio.core.hashing import file_key
from studio.core.interfaces import Cap, StepSpec, StudioError
from studio.core.quota import QuotaManager
from studio.domain import (
    Channel,
    CostKind,
    GateDecision,
    GateName,
    Idea,
    Package,
    PublicationCandidate,
    RunManifest,
    Script,
    Verdict,
    VideoFormat,
)
from studio.pipeline.mock_agents import MockComplianceOfficer, MockReviewer
from studio.pipeline.steps import Production, front_steps, production_steps
from studio.scenario.skill_json import ROOT_KEY, to_skill_json

MAX_ROUNDS = 8  # a video has 3 gates; more rounds than that means a gate never gets its approval
# Caps of docs/COST_MODEL.md § Plafonds (initial values, adjustable by ADR): GPU seconds and Claude calls.
GPU_CAP_S = {VideoFormat.LONG: 36 * 3600.0, VideoFormat.SHORT: 4 * 3600.0}
CLAUDE_CALL_CAP = {VideoFormat.LONG: 80.0, VideoFormat.SHORT: 20.0}
GPU_CAP_DAY_S = 80 * 3600.0
GPU_CAP_MONTH_S = 600 * 3600.0
FAR_FUTURE = dt.datetime(9999, 12, 31, tzinfo=dt.UTC)
COSTS_NOTE = (
    "Entries measured on mock adapters: GPU seconds are CPU seconds of a stand-in, Claude calls are scripted "
    "answers. They are never real spending and never add up with it."
)


class GateRejected(StudioError):
    """A gate holds a rejection: the run cannot continue until the subject changes or a new verdict is recorded."""

    def __init__(self, gate: str, step: str, reason: str) -> None:
        super().__init__(f"{gate} rejected at step {step!r}: {reason}")
        self.gate, self.step, self.reason = gate, step, reason


class GateWaiting(StudioError):
    """A gate holds no verdict yet (the human's half of a decision, typically): the run stops there and refuses nothing."""

    def __init__(self, gate: str, step: str, reason: str) -> None:
        super().__init__(f"{gate} is waiting at step {step!r}: {reason}")
        self.gate, self.step, self.reason = gate, step, reason


class RunPaused(StudioError):
    """The Claude subscription's usage limit was hit: resume after `resume_at`."""

    def __init__(self, resume_at: dt.datetime, message: str) -> None:
        super().__init__(f"paused until {resume_at.isoformat()}: {message}")
        self.resume_at = resume_at


class StateBusy(StudioError):
    """Another process is running in this state folder."""


class Reviewer(Protocol):
    """Answers G1 and G2 (the human's gates), and the human's half of the compliance decision."""

    def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision: ...


class ComplianceReviewer(Protocol):
    """Answers the agent's half of the compliance gate from the artifacts it judges."""

    def review(
        self,
        script: Script,
        qa_report: Mapping[str, Any],
        candidate: PublicationCandidate,
        candidate_key: str,
        now: dt.datetime,
    ) -> GateDecision: ...


@dataclass(frozen=True)
class DryRunConfig:
    channel: Channel
    format: VideoFormat
    out_dir: Path
    seed: int = 0
    run_id: str | None = None
    database_url: str | None = None  # default: SQLite under out_dir/state
    llm: LLMRunner | None = None  # default: the scripted mock LLM
    reviewer: Reviewer | None = None  # default: MockReviewer (approves)
    officer: ComplianceReviewer | None = None  # default: MockComplianceOfficer (script, QA report, candidate)

    @property
    def effective_run_id(self) -> str:
        return self.run_id or f"dry-{self.channel.id}-{self.format.value}-{self.seed}"


@dataclass
class _Tally:
    """What happened over every round of one invocation."""

    executed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    rounds: int = 0

    def absorb(self, result: RunResult) -> None:
        self.rounds += 1
        self.executed += [s for s in result.executed if s not in self.executed]
        self.skipped = [s for s in result.skipped if s not in self.executed]


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _deliver(store: LocalArtifactStore, key: str, dst: Path) -> None:
    """Put a stored file next to the reports, once the store has re-hashed it and the copy has too.

    A copy, never a hard link: the store's files are shared by hash, and a tool that edits `dst` in place would
    corrupt the artifact for every run that uses it. `store.verify` hashes the stored bytes on every delivery (a
    content address is only worth what a read of it verifies) and removes a corrupt object, so that the next run
    recomputes it instead of failing on it again; the copy is hashed before it takes its place; `dst` is left alone
    when it already holds these bytes."""
    if not store.verify(key):
        raise StudioError(
            f"stored artifact {key} is corrupt or missing (a corrupt file was removed from the store): "
            "nothing was delivered; run again to recompute it"
        )
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_file() and file_key(dst) == key:
        return
    tmp = dst.with_name(f".{dst.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        shutil.copy2(store.get(key).path, tmp)
        if (actual := file_key(tmp)) != key:
            raise StudioError(f"the copy of {key} hashes to {actual}: nothing was delivered")
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)


@contextlib.contextmanager
def _owning(state: Path) -> Iterator[None]:
    """Exclusive, non-blocking ownership of a state folder for the life of the process (released by the kernel
    when the process dies, however it dies)."""
    state.mkdir(parents=True, exist_ok=True)
    with (state / ".run.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise StateBusy(f"another studio run is using {state}: wait for it, or use another --out folder") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _clear_leftovers(state: Path, folder: Path) -> None:
    """What a killed predecessor left behind: scratch directories and half-written JSON files. The caller owns the
    state folder, so nothing in there belongs to a live process."""
    shutil.rmtree(state / "tmp", ignore_errors=True)
    for stale in folder.glob(".*.tmp"):
        stale.unlink(missing_ok=True)


class _Autopilot:
    """The mock reviewers that answer the gates of a dry run.

    Nobody looked at anything: every decision it returns says `mock`, whatever the reviewer or the officer it
    delegates to declares. A decision merged from two halves is a mock as soon as one of them is (a real
    officer's verdict next to a stand-in human's answer is not a real approval)."""

    def __init__(
        self,
        store: LocalArtifactStore,
        clock: Callable[[], dt.datetime],
        reviewer: Reviewer | None = None,
        officer: ComplianceReviewer | None = None,
    ) -> None:
        self.store, self.clock = store, clock
        self.reviewer: Reviewer = reviewer or MockReviewer()
        self.officer: ComplianceReviewer = officer or MockComplianceOfficer()

    def decide(self, gate: GateName, subject_key: str) -> GateDecision:
        now = self.clock()
        if gate is not GateName.COMPLIANCE:
            return self._as_mock(self.reviewer.decide(gate, subject_key, now))
        # The officer reads what the candidate names: the script and the QA report whose keys are part of the subject
        # it judges, never whatever the run happens to hold under those step names.
        candidate = PublicationCandidate.model_validate_json(self._read(subject_key))
        script = Script.model_validate_json(self._read(candidate.script_key))
        qa_report = json.loads(self._read(candidate.qa_key))
        agent = self.officer.review(script, qa_report, candidate, subject_key, now)
        if agent.agent_verdict is Verdict.REJECT:
            return self._as_mock(agent)  # a blocked candidate is never put to the human
        human = self.reviewer.decide(gate, subject_key, now)  # the compliance gate records the agent's AND the human's
        merged = agent.model_copy(update={"human_verdict": human.human_verdict, "human_note": human.human_note})
        return self._as_mock(merged)

    @staticmethod
    def _as_mock(decision: GateDecision) -> GateDecision:
        return decision if decision.mock else decision.model_copy(update={"mock": True})

    def _read(self, key: str) -> str:
        return self.store.get(key).path.read_text(encoding="utf-8")


def _why(decision: GateDecision) -> str:
    """Why a decision does not approve, in the words of whoever refused."""
    if decision.human_verdict is Verdict.REJECT:
        return decision.human_note or "refused by the human, no note"
    return "; ".join(decision.agent_reasons) or decision.human_note or "no reason recorded"


def _waiting_for(decision: GateDecision) -> str:
    """Whose verdict a decision that neither approves nor rejects is missing."""
    halves = (("the agent", decision.agent_verdict), ("the human", decision.human_verdict))
    missing = [who for who, verdict in halves if verdict is Verdict.PENDING]
    return f"no verdict from {' and '.join(missing) or 'anyone'} yet"


def _drive(
    runner: Runner,
    graph: Graph,
    config: DryRunConfig,
    production: Production,
    scopes: list[str],
    manifest: RunManifest | None,
    autopilot: _Autopilot,
    decisions: SqlDecisionStore,
    folder: Path,
    tally: _Tally,
) -> tuple[RunResult, RunManifest]:
    """Run `graph`, answering each waiting gate, until nothing waits."""
    for _ in range(MAX_ROUNDS):
        try:
            result, manifest = runner.run(
                graph,
                config.effective_run_id,
                scopes,
                manifest,
                config.channel.id,
                config.format,
                dry_run=True,
                mock=production.is_mock,
            )
        except BaseException as exc:  # keep what the run resolved: its outputs are pinned in the partial manifest
            partial = partial_run(exc)
            if partial is not None:
                _write_json(folder / "manifest.json", partial.manifest.model_dump(mode="json"))
            raise
        _write_json(folder / "manifest.json", manifest.model_dump(mode="json"))
        tally.absorb(result)
        if not result.waiting:
            return result, manifest
        # The compliance verdict comes first: a candidate it blocks is never put to the human at G2 (MISSION §11).
        for name in sorted(result.waiting, key=lambda n: graph[n].gate is not GateName.COMPLIANCE):
            step: StepSpec = graph[name]
            gate = GateName(step.gate) if step.gate is not None else None
            if gate is None:
                raise StudioError(f"step {name!r} waits but is not a gate")
            subject = result.outputs[step.inputs[0]]
            existing = decisions.get(gate, subject)
            if existing is not None and existing.rejected:  # a recorded refusal
                raise GateRejected(gate.value, name, result.reasons.get(name, _why(existing)))
            if existing is not None and existing.mock != production.is_mock:  # the runner has said why in `reasons`
                raise StudioError(result.reasons.get(name, f"the {gate.value} decision on {subject} does not apply to this run"))
            if existing is not None and existing.approved:
                continue  # approved since the runner looked (another process, a human): the next round takes it
            decision = autopilot.decide(gate, subject)  # no decision yet, or a mock one still missing a verdict
            decisions.put(decision)
            if decision.rejected:
                raise GateRejected(gate.value, name, _why(decision))
            if not decision.approved:
                raise GateWaiting(gate.value, name, _waiting_for(decision))
    raise StudioError(f"gates still waiting after {MAX_ROUNDS} rounds")


def _summarise_costs(ledger: SqlCostLedger, run_id: str) -> dict[str, float]:
    totals: defaultdict[str, float] = defaultdict(float)
    for entry in ledger.entries(run_id):
        totals[entry.kind.value] += entry.quantity
    return {kind: round(total, 3) for kind, total in sorted(totals.items())}


def _load_manifest(path: Path, run_id: str) -> RunManifest | None:
    """The manifest a previous invocation left in `path`, if any; it must belong to `run_id`."""
    if not path.is_file():
        return None
    try:
        manifest = RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise StudioError(f"{path} is not a valid run manifest: {exc}") from exc
    if manifest.run_id != run_id:
        raise StudioError(
            f"{path} belongs to run {manifest.run_id!r}, not {run_id!r}: "
            "use another output folder, or remove the file to start over"
        )
    return manifest


def _contract_message(exc: ValidationError, state: Path) -> str:
    """A document that does not fit the contract it is read under, in words (never the raw trace, never its content)."""
    first = exc.errors(include_input=False, include_url=False)[0]
    where = ".".join(str(part) for part in first["loc"]) or "(root)"
    return (
        f"a document does not match the {exc.title} contract of this version of the studio "
        f"({exc.error_count()} error(s); first: {where}: {first['msg']}). A state written by another version of the "
        f"studio can cause this: the dry-run state under {state} can be removed, or use another --out folder"
    )


def run_dry(config: DryRunConfig, *, clock: Callable[[], dt.datetime] | None = None) -> dict[str, Any]:
    """Run one video through mock adapters and return its report (also written to `report.json`)."""
    clock = clock or (lambda: dt.datetime.now(dt.UTC))
    out_dir = config.out_dir.resolve()
    state = out_dir / "state"
    folder = out_dir / config.channel.id / config.format.value
    with _owning(state):
        try:
            return _run_owned(config, out_dir, state, folder, clock)
        except ValidationError as exc:
            raise StudioError(_contract_message(exc, state)) from exc


def _run_owned(
    config: DryRunConfig, out_dir: Path, state: Path, folder: Path, clock: Callable[[], dt.datetime]
) -> dict[str, Any]:
    folder.mkdir(parents=True, exist_ok=True)
    _clear_leftovers(state, folder)
    (folder / "report.json").unlink(missing_ok=True)  # a report on disk always describes the latest run that finished
    engine = make_engine(config.database_url or f"sqlite:///{state / 'studio.db'}")
    store = LocalArtifactStore(state / "cas", engine)
    ledger = SqlCostLedger(engine)
    decisions = SqlDecisionStore(engine)
    for backend in (store, ledger, decisions):
        backend.create_schema()
    if config.database_url is None:
        # The database is this folder's own and this process owns the folder: every reservation still active belongs
        # to a predecessor that died, whatever date its lease runs to.
        ledger.reap_expired(FAR_FUTURE)
    # A shared database has live writers this process knows nothing about: their reservations are theirs until
    # their lease runs out, and only expired leases are freed (`Runner.run` does it, at its start of every round).

    run_id = config.effective_run_id
    now = clock()
    fmt = config.format
    scopes = [f"video:{run_id}", f"day:{now:%Y-%m-%d}", f"month:{now:%Y-%m}"]
    ledger.set_cap(Cap(scopes[0], CostKind.GPU_SECONDS, GPU_CAP_S[fmt]))
    ledger.set_cap(Cap(scopes[0], CostKind.CLAUDE_CALLS, CLAUDE_CALL_CAP[fmt]))
    ledger.set_cap(Cap(scopes[1], CostKind.GPU_SECONDS, GPU_CAP_DAY_S))
    ledger.set_cap(Cap(scopes[2], CostKind.GPU_SECONDS, GPU_CAP_MONTH_S))

    manifest = _load_manifest(folder / "manifest.json", run_id)
    production = Production.from_mocks(
        config.channel, fmt, config.seed, config.llm, cwd=out_dir, run_id=run_id, tmp=state / "tmp"
    )
    runner = Runner(store, ledger, decisions, clock, executor_id="dry-run")
    autopilot = _Autopilot(store, clock, config.reviewer, config.officer)
    tally = _Tally()
    quota = QuotaManager(clock)

    try:
        front = Graph(front_steps(production))
        result, manifest = _drive(runner, front, config, production, scopes, manifest, autopilot, decisions, folder, tally)
        script = Script.model_validate_json(store.get(result.outputs["script"]).path.read_text(encoding="utf-8"))
        full = Graph(front_steps(production) + production_steps(production, script))
        result, manifest = _drive(runner, full, config, production, scopes, manifest, autopilot, decisions, folder, tally)
        return _write_outputs(config, production, store, ledger, result, manifest, script, tally, folder)
    except QuotaExhausted as exc:
        raise RunPaused(quota.on_exhausted(exc), str(exc)) from exc
    finally:
        engine.dispose()  # closes the SQLite files (and folds their write-ahead log back into them)


def _write_outputs(
    config: DryRunConfig,
    production: Production,
    store: LocalArtifactStore,
    ledger: SqlCostLedger,
    result: RunResult,
    manifest: RunManifest,
    script: Script,
    tally: _Tally,
    folder: Path,
) -> dict[str, Any]:
    def read(step: str) -> str:
        return store.get(result.outputs[step]).path.read_text(encoding="utf-8")

    run_id = config.effective_run_id
    render_key = result.outputs["assemble"]
    render_path = folder / "render.mp4"
    _deliver(store, render_key, render_path)
    package = Package.model_validate_json(read("package"))
    idea = Idea.model_validate_json(read("idea"))
    # The skill's scene document, marked as a mock at its root (the format keeps unknown root fields as they are).
    root = {**dict(script.extras.get(ROOT_KEY, {})), "mock": True}  # type: ignore[call-overload]
    marked = script.model_copy(update={"extras": {**script.extras, ROOT_KEY: root}})
    _write_json(folder / "script.scenes.json", to_skill_json(marked, package))
    entries = ledger.entries(run_id)
    _write_json(
        folder / "costs.json",
        {
            "mock": production.is_mock,
            "dry_run": True,
            "note": COSTS_NOTE,
            "entries": [e.model_dump(mode="json") for e in entries],
        },
    )
    candidate = json.loads(read("publish_plan"))
    report: dict[str, Any] = {
        "run_id": run_id,
        "channel_id": config.channel.id,
        "format": config.format.value,
        "dry_run": True,
        "mock": production.is_mock,
        "adapters": production.adapter_ids(),
        "idea_id": idea.id,
        "executed": tally.executed,
        "skipped": tally.skipped,
        "waiting": result.waiting,
        "rounds": tally.rounds,
        "render_key": render_key,
        "render_path": str(render_path),
        "candidate_key": result.outputs["candidate"],
        "duration_expected_s": script.duration_s,
        "scene_count": len(script.scenes),
        "qa_defects": json.loads(read("qa"))["defects"],
        "publication": candidate["publication"],
        "costs": _summarise_costs(ledger, run_id),
        "step_count": len(result.step_keys),
        "manifest_mock": manifest.mock,
    }
    _write_json(folder / "report.json", report)
    return report
