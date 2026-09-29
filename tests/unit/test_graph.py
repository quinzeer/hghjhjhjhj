"""Graph planner (studio/core/graph.py): topological order, content-addressed replay, locked manifest,
hash-bound gates, publication guard, budget reservations and leases, first write wins, run modes, partial runs."""

from __future__ import annotations

import contextlib
import datetime as dt
import logging
import os
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from graph_fakes import (
    DictDecisionSource,
    InMemoryArtifactStore,
    InMemoryLedger,
    ManualClock,
    SubjectBlindDecisionSource,
)

from studio.core.artifacts import LocalArtifactStore
from studio.core.costs import SqlCostLedger
from studio.core.db import make_engine
from studio.core.graph import (
    DEFAULT_LEASE,
    CostNotSettled,
    CycleError,
    Graph,
    GraphError,
    Runner,
    RunResult,
    StepOutputError,
    decision_refusal,
    partial_run,
    run_step_key,
)
from studio.core.hashing import step_key
from studio.core.interfaces import (
    ArtifactMissing,
    ArtifactStore,
    BudgetExceeded,
    Cap,
    CostLedger,
    DecisionSource,
    GateNotApproved,
    Reservation,
    StepSpec,
    StoredArtifact,
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
)

RUN = "run-1"
VIDEO_SCOPE = "video:run-1"
DAY_SCOPE = "day:2026-09-28"
SCOPES = (VIDEO_SCOPE, DAY_SCOPE)
CPU, GPU, LLM, HUMAN = ResourceClass.CPU, ResourceClass.GPU, ResourceClass.LLM, ResourceClass.HUMAN
GPU_S, KWH = CostKind.GPU_SECONDS, CostKind.KWH
GPU_ESTIMATE = 10.0
StepFn = Callable[[Mapping[str, StoredArtifact], Mapping[str, Any]], tuple[bytes, str, str]]


class Calls:
    """Thread-safe count of step executions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {}

    def hit(self, name: str) -> None:
        with self._lock:
            self._counts[name] = self._counts.get(name, 0) + 1

    def __getitem__(self, name: str) -> int:
        with self._lock:
            return self._counts.get(name, 0)


class Env:
    def __init__(self, decisions: DecisionSource | None = None) -> None:
        self.clock = ManualClock()
        self.store = InMemoryArtifactStore(self.clock)
        self.ledger = InMemoryLedger(self.clock)
        self.decisions = decisions if decisions is not None else DictDecisionSource()
        self.calls = Calls()
        self.runner = Runner(self.store, self.ledger, self.decisions, self.clock, "cpu")

    def rewire(self) -> None:
        """Rebuild the runner after replacing a backend."""
        self.runner = Runner(self.store, self.ledger, self.decisions, self.clock, "cpu")

    def run(
        self, graph: Graph, run_id: str = RUN, manifest: RunManifest | None = None, **kw: Any
    ) -> tuple[RunResult, RunManifest]:
        return self.runner.run(graph, run_id, SCOPES, manifest, "channel-a", VideoFormat.SHORT, **kw)

    def det(self, name: str, ignore: Sequence[str] = (), seconds: float = 0.0) -> StepFn:
        """Deterministic step: its output is a function of its params (minus `ignore`) and its input keys."""

        def run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            self.calls.hit(name)
            self.clock.advance(seconds)
            payload = {
                "step": name,
                "params": {k: v for k, v in params.items() if k not in ignore},
                "inputs": {k: a.key for k, a in inputs.items()},
            }
            return canonical_json(payload).encode(), "json", "application/json"

        return run

    def rand(self, name: str, seconds: float = 0.0) -> StepFn:
        """Non-deterministic step (a diffusion sample, an LLM answer): new bytes on every call."""

        def run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            self.calls.hit(name)
            self.clock.advance(seconds)
            return os.urandom(32), "video", "video/mp4"

        return run

    def fixed(self, name: str, data: bytes, kind: str = "json", media_type: str = "application/json") -> StepFn:
        """Step that always returns `data`."""

        def run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            self.calls.hit(name)
            return data, kind, media_type

        return run

    def step(
        self,
        name: str,
        inputs: tuple[str, ...] = (),
        *,
        run: StepFn | None = None,
        resource: ResourceClass = CPU,
        params: Mapping[str, Any] | None = None,
        version: str = "1",
        estimated: Mapping[CostKind, float] | None = None,
        gate: GateName | None = None,
        requires: tuple[tuple[GateName, str], ...] = (),
    ) -> StepSpec:
        if estimated is None:  # a GPU step must declare its GPU time (Graph refuses it otherwise)
            estimated = {GPU_S: GPU_ESTIMATE} if resource is GPU and gate is None else {}
        return StepSpec(
            name=name,
            version=version,
            inputs=inputs,
            params=params or {},
            resource=resource,
            run=run or self.det(name),
            estimated_cost=estimated,
            gate=gate,
            requires_approval=requires,
        )

    def gate(self, name: str, subject: str, gate: GateName) -> StepSpec:
        return self.step(name, (subject,), resource=HUMAN, gate=gate, run=self.forbidden(name))

    def forbidden(self, name: str) -> StepFn:
        def run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            raise AssertionError(f"gate step {name} must never run code")

        return run


def decision(
    gate: GateName, subject_key: str, agent: Verdict = Verdict.APPROVE, human: Verdict = Verdict.APPROVE, **kw: Any
) -> GateDecision:
    return GateDecision(gate=gate, subject_key=subject_key, agent_verdict=agent, human_verdict=human, **kw)


@pytest.fixture
def env() -> Env:
    return Env()


def noop_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
    return b"x", "text", "text/plain"


def spec(name: str, *inputs: str, **kw: Any) -> StepSpec:
    base: dict[str, Any] = dict(name=name, version="1", inputs=inputs, params={}, resource=CPU, run=noop_run)
    base.update(kw)
    return StepSpec(**base)


def mock_key(step: StepSpec, inputs: Mapping[str, str] | None = None) -> str:
    """Key of `step` in the default mode of these tests (dry run on mocks)."""
    return run_step_key(step, step.version, inputs or {}, dry_run=True, mock=True)


def statuses(ledger: InMemoryLedger) -> list[tuple[CostKind, str]]:
    return [(r.kind, ledger.status(r.id)) for r in ledger.reservations()]


# ------------------------------------------------------------------ fakes honour the protocols


def test_fakes_implement_the_core_protocols() -> None:
    assert isinstance(InMemoryArtifactStore(), ArtifactStore)
    assert isinstance(InMemoryLedger(), CostLedger)
    assert isinstance(DictDecisionSource(), DecisionSource)
    assert isinstance(SubjectBlindDecisionSource(), DecisionSource)


@pytest.mark.parametrize(
    ("kind", "media_type"),
    [("mp4", "video/mp4"), ("", "video/mp4"), ("video", "mp4"), ("video", "")],
)
def test_fake_store_refuses_what_the_sql_store_refuses(tmp_path: Path, kind: str, media_type: str) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'index.db'}")
    try:
        real = LocalArtifactStore(tmp_path / "store", engine)
        real.create_schema()
        for store in (InMemoryArtifactStore(), real):
            with pytest.raises(ValueError):
                store.put_bytes(b"frames", kind=kind, media_type=media_type)
            assert store.put_bytes(b"frames", kind="video", media_type="video/mp4").size_bytes == 6
    finally:
        engine.dispose()


def test_fake_ledger_refuses_a_non_positive_lease() -> None:
    with pytest.raises(ValueError, match="lease"):
        InMemoryLedger().reserve([DAY_SCOPE], GPU_S, 1.0, dt.timedelta(0))


# ------------------------------------------------------------------ graph: order and validation


def test_topological_order_puts_inputs_first_and_keeps_declaration_order_otherwise() -> None:
    graph = Graph([spec("c", "a", "b"), spec("a"), spec("b"), spec("d", "c"), spec("e")])
    assert graph.names == ("a", "b", "c", "d", "e")
    assert [s.name for s in graph.steps] == ["c", "a", "b", "d", "e"]
    assert graph.ancestors("d") == {"a", "b", "c"}
    assert graph.descendants("a") == {"c", "d"}
    assert graph.descendants("e") == frozenset()
    assert [s.name for s in graph] == list(graph.names) and len(graph) == 5
    assert "a" in graph and "z" not in graph and graph["c"].inputs == ("a", "b")
    with pytest.raises(KeyError):
        graph.descendants("z")


def test_valid_declaration_order_is_kept_as_is() -> None:
    steps = [spec("x"), spec("a"), spec("y", "x"), spec("b", "a"), spec("z", "y", "b")]
    assert Graph(steps).names == ("x", "a", "y", "b", "z")


def test_order_respects_every_edge_on_a_wide_graph() -> None:
    steps = [spec(f"s{i}", *(f"s{j}" for j in range(i) if (i * 7 + j) % 3 == 0)) for i in range(30)]
    shuffled = steps[15:] + steps[:15]
    order = Graph(shuffled).names
    position = {name: i for i, name in enumerate(order)}
    assert sorted(order) == sorted(s.name for s in steps)
    for s in steps:
        for name in s.inputs:
            assert position[name] < position[s.name]
    assert Graph(shuffled).names == order  # stable: same input, same order


def test_cycle_is_detected_and_named() -> None:
    with pytest.raises(CycleError) as err:
        Graph([spec("d"), spec("a", "c"), spec("b", "a"), spec("c", "b", "d")])
    assert set(err.value.cycle) == {"a", "b", "c"}
    assert "d" not in err.value.cycle
    assert str(err.value) == "dependency cycle: a -> b -> c -> a"


def test_self_loop_is_a_cycle() -> None:
    with pytest.raises(CycleError) as err:
        Graph([spec("a", "a")])
    assert err.value.cycle == ("a",)


@pytest.mark.parametrize(
    ("steps", "message"),
    [
        ([spec("a"), spec("a")], "duplicate step name"),
        ([spec("a", "ghost")], "unknown inputs"),
        ([spec("a"), spec("b", "a", "a")], "lists an input twice"),
        ([spec("a", version="")], "needs a version"),
        ([spec("")], "needs a name"),
        ([spec("a", params={"when": object()})], "JSON-serialisable"),
        ([spec("a", estimated_cost={GPU_S: -1.0})], "finite and > 0"),
        ([spec("a", estimated_cost={GPU_S: float("nan")})], "finite and > 0"),
        ([spec("a", estimated_cost={GPU_S: "ten"})], "finite and > 0"),
        ([spec("a", estimated_cost={KWH: 0.0})], "finite and > 0"),
        ([spec("a", estimated_cost={"gpu_hours": 1.0})], "unknown cost kind"),
        ([spec("a", resource="tpu")], "tpu"),
        ([spec("a"), spec("g", "a", gate="g9")], "g9"),
        ([spec("a"), spec("b", "a", requires_approval=(("g9", "a"),))], "g9"),
        ([spec("a", resource=GPU)], "gpu_seconds estimate"),
        ([spec("a", resource=GPU, estimated_cost={KWH: 0.1})], "gpu_seconds estimate"),
    ],
)
def test_invalid_graphs_are_refused(steps: list[StepSpec], message: str) -> None:
    with pytest.raises(GraphError, match=message):
        Graph(steps)


def test_gate_step_has_exactly_one_input_its_subject() -> None:
    with pytest.raises(GraphError, match="exactly one input"):
        Graph([spec("g1", gate=GateName.G1)])
    with pytest.raises(GraphError, match="exactly one input"):
        Graph([spec("a"), spec("b"), spec("g1", "a", "b", gate=GateName.G1)])
    with pytest.raises(GraphError, match="cannot itself require"):
        Graph([spec("a"), spec("g1", "a", gate=GateName.G1, requires_approval=((GateName.COMPLIANCE, "a"),))])
    assert Graph([spec("a"), spec("g1", "a", gate=GateName.G1)]).names == ("a", "g1")


def test_approval_subject_must_be_upstream_of_the_step() -> None:
    with pytest.raises(GraphError, match="unknown step"):
        Graph([spec("publish", requires_approval=((GateName.G2, "render"),))])
    with pytest.raises(GraphError, match="not upstream"):
        Graph([spec("render"), spec("publish", requires_approval=((GateName.G2, "render"),))])
    ok = Graph(
        [
            spec("render"),
            spec("g2", "render", gate=GateName.G2),
            spec("publish", "g2", requires_approval=((GateName.G2, "render"),)),
        ]
    )
    assert ok.names == ("render", "g2", "publish")


# ------------------------------------------------------------------ runner: execution and replay


def pipeline(env: Env) -> Graph:
    return Graph(
        [
            env.step("idea", resource=LLM, params={"topic": "bridges"}),
            env.step("script", ("idea",), resource=LLM),
            env.step("voice", ("script",), resource=GPU, run=env.det("voice", seconds=4.0)),
            env.step("assemble", ("script", "voice")),
        ]
    )


def test_first_run_executes_every_step_and_locks_keys_in_the_manifest(env: Env) -> None:
    graph = pipeline(env)
    result, manifest = env.run(graph)

    assert result.executed == ["idea", "script", "voice", "assemble"]
    assert result.skipped == result.waiting == result.blocked == []
    # keys chain through upstream *output* keys
    for s in graph.order:
        inputs = {name: result.outputs[name] for name in s.inputs}
        assert result.step_keys[s.name] == mock_key(s, inputs)
        assert env.store.step_output(result.step_keys[s.name]) == result.outputs[s.name]
        assert env.store.pinned_by(result.outputs[s.name]) == {RUN}
    assert manifest.locked == result.outputs
    assert manifest.step_keys == result.step_keys
    assert manifest.versions == {name: "1" for name in graph.names}
    assert (manifest.run_id, manifest.channel_id, manifest.format) == (RUN, "channel-a", VideoFormat.SHORT)
    assert manifest.dry_run is True and manifest.mock is True
    assert list(manifest.costs) == env.ledger.entries(RUN) == result.costs
    assert RunManifest.model_validate_json(manifest.model_dump_json()) == manifest


def test_real_run_keys_follow_the_hashing_formula_and_other_modes_are_salted(env: Env) -> None:
    graph = pipeline(env)
    real, _ = env.run(graph, run_id="real", dry_run=False, mock=False)

    for s in graph.order:
        inputs = {name: real.outputs[name] for name in s.inputs}
        assert real.step_keys[s.name] == step_key(s.name, s.version, inputs, s.params, s.seed)
    modes = [(dry_run, mock) for dry_run in (True, False) for mock in (True, False)]
    keys = {run_step_key(graph["idea"], "1", {}, dry_run=d, mock=m) for d, m in modes}
    assert len(keys) == 4


def test_real_run_never_reuses_an_output_of_a_mock_dry_run(env: Env) -> None:
    dry, _ = env.run(Graph([env.step("render", resource=GPU, run=env.fixed("mock", b"mock-render", "video", "video/mp4"))]))
    real_graph = Graph([env.step("render", resource=GPU, run=env.fixed("real", b"real-render", "video", "video/mp4"))])

    real, manifest = env.run(real_graph, run_id="real-1", dry_run=False, mock=False)

    assert real.executed == ["render"] and real.skipped == []
    assert env.store.data(manifest.locked["render"]) == b"real-render"
    assert (manifest.dry_run, manifest.mock) == (False, False)
    assert real.step_keys["render"] != dry.step_keys["render"]
    # nor a dry run on real adapters, nor a real run on mock adapters: each mode has its own key space
    for run_id, dry_run, mock in (("real-dry", True, False), ("mock-real", False, True)):
        other, _ = env.run(real_graph, run_id=run_id, dry_run=dry_run, mock=mock)
        assert other.executed == ["render"]
    assert (env.calls["mock"], env.calls["real"]) == (1, 3)
    # and each mode still replays for free
    again, _ = env.run(real_graph, run_id="real-2", dry_run=False, mock=False)
    assert again.executed == [] and again.outputs == real.outputs


def test_replay_with_the_manifest_executes_nothing(env: Env) -> None:
    graph = pipeline(env)
    first, manifest = env.run(graph)
    entries_before = env.ledger.entries()
    reservations_before = env.ledger.reservations()

    replay, replayed = env.run(graph, manifest=manifest)

    assert replay.executed == []
    assert replay.skipped == ["idea", "script", "voice", "assemble"]
    assert replay.outputs == first.outputs and replay.step_keys == first.step_keys
    assert [env.calls[n] for n in graph.names] == [1, 1, 1, 1]
    assert env.ledger.entries() == entries_before
    assert env.ledger.reservations() == reservations_before
    assert replayed.locked == manifest.locked and replayed.costs == manifest.costs


def test_replay_of_a_new_run_reuses_committed_outputs(env: Env) -> None:
    graph = pipeline(env)
    first, _ = env.run(graph)
    other, manifest = env.run(graph, run_id="run-2")
    assert other.executed == []
    assert other.outputs == first.outputs
    assert all(env.store.pinned_by(k) == {RUN, "run-2"} for k in other.outputs.values())
    assert manifest.costs == ()


def test_non_deterministic_step_is_not_rerun_on_replay_thanks_to_the_manifest(env: Env) -> None:
    graph = Graph([env.step("shot", resource=GPU, run=env.rand("shot")), env.step("grade", ("shot",))])
    first, manifest = env.run(graph)
    env.store.forget_step_outputs()  # the store no longer knows which output each step produced

    replay, _ = env.run(graph, manifest=manifest)
    assert replay.executed == []
    assert replay.outputs == first.outputs
    assert env.calls["shot"] == 1 and env.calls["grade"] == 1

    # control: the same situation without the manifest re-samples the shot, which cascades downstream
    fresh, _ = env.run(graph, run_id="run-2")
    assert fresh.executed == ["shot", "grade"]
    assert fresh.outputs["shot"] != first.outputs["shot"]
    assert fresh.step_keys["grade"] != first.step_keys["grade"]


def reviewed(env: Env, script_version: str, script_params: Mapping[str, Any] | None = None) -> Graph:
    return Graph(
        [
            env.step("script", resource=LLM, run=env.rand("script"), version=script_version, params=script_params),
            env.step("render", ("script",), resource=GPU, run=env.rand("render", seconds=600.0), estimated={GPU_S: 900.0}),
            env.gate("g2", "render", GateName.G2),
        ]
    )


def test_version_bump_keeps_a_locked_video_and_its_gates(env: Env) -> None:
    first, manifest = env.run(reviewed(env, "1"))
    assert isinstance(env.decisions, DictDecisionSource)
    env.decisions.put(decision(GateName.G2, first.outputs["render"]))
    approved, manifest = env.run(reviewed(env, "1"), manifest=manifest)
    assert approved.executed == ["g2"]
    gpu_spent = env.ledger.spent(VIDEO_SCOPE, GPU_S)

    bumped, relocked = env.run(reviewed(env, "2"), manifest=manifest)

    # ADR-001: a new agent version does not invalidate a video in progress (no GPU cascade, no gate re-paid)
    assert bumped.executed == [] and bumped.waiting == []
    assert bumped.outputs == approved.outputs and bumped.step_keys == approved.step_keys
    assert bumped.kept_versions == {"script": "1"}
    assert relocked.locked == manifest.locked and relocked.versions["script"] == "1"
    assert env.calls["script"] == env.calls["render"] == 1
    assert env.ledger.spent(VIDEO_SCOPE, GPU_S) == gpu_spent == 600.0

    # a real change of input still recomputes, with the graph's version
    moved, moved_manifest = env.run(reviewed(env, "2", {"tone": "dry"}), manifest=relocked)
    assert moved.executed == ["script", "render"] and moved.waiting == ["g2"]
    assert moved_manifest.versions["script"] == "2" and moved.kept_versions == {}

    # and a new video uses the new version
    fresh, fresh_manifest = env.run(reviewed(env, "2"), run_id="run-2")
    assert fresh.executed == ["script", "render"] and fresh_manifest.versions["script"] == "2"


def test_upgrade_replaces_a_locked_output_on_explicit_request(env: Env) -> None:
    first, manifest = env.run(reviewed(env, "1"))

    result, relocked = env.run(reviewed(env, "2"), manifest=manifest, upgrade=("script",))

    assert result.executed == ["script", "render"]
    assert result.waiting == ["g2"]  # the new render needs its own G2
    assert result.kept_versions == {}
    assert relocked.versions["script"] == "2"
    assert relocked.locked["script"] != first.outputs["script"]
    assert env.store.pinned_by(first.outputs["script"]) == set()
    # upgrading steps whose version did not change is a plain replay
    again, _ = env.run(reviewed(env, "2"), manifest=relocked, upgrade=("script", "render"))
    assert again.executed == [] and again.skipped == ["script", "render"]


def test_lost_locked_output_is_recomputed(env: Env) -> None:
    graph = Graph([env.step("shot", resource=GPU, run=env.rand("shot")), env.step("grade", ("shot",))])
    first, manifest = env.run(graph)
    env.store.lose(first.outputs["shot"])

    result, relocked = env.run(graph, manifest=manifest)

    assert result.executed == ["shot", "grade"]
    assert env.store.has(relocked.locked["shot"])
    assert relocked.locked["shot"] != first.outputs["shot"]


def test_upstream_param_change_reruns_downstream_and_only_it(env: Env) -> None:
    def build(level: int) -> Graph:
        return Graph(
            [
                env.step("a"),
                env.step("b", ("a",), params={"level": level}),
                env.step("c", ("b",)),
                env.step("d", ("a",)),
                env.step("x"),
                env.step("y", ("x",)),
            ]
        )

    first, manifest = env.run(build(1))
    second, relocked = env.run(build(2), manifest=manifest)

    assert second.executed == ["b", "c"]
    assert second.skipped == ["a", "d", "x", "y"]
    assert {n: env.calls[n] for n in "abcdxy"} == {"a": 1, "b": 2, "c": 2, "d": 1, "x": 1, "y": 1}
    changed = {n for n in first.outputs if first.outputs[n] != second.outputs[n]}
    assert changed == {"b", "c"} == set(build(2).descendants("b")) | {"b"}
    assert {n for n in relocked.locked if relocked.locked[n] != manifest.locked[n]} == {"b", "c"}
    # outputs no longer referenced by the manifest are released for retention, the others stay pinned
    assert env.store.pinned_by(first.outputs["b"]) == env.store.pinned_by(first.outputs["c"]) == set()
    assert env.store.pinned_by(first.outputs["a"]) == {RUN}
    assert env.store.pinned_for(RUN) == set(relocked.locked.values())


def test_param_change_that_leaves_the_output_identical_stops_there(env: Env) -> None:
    def build(note: str) -> Graph:
        return Graph(
            [
                env.step("a"),
                env.step("b", ("a",), params={"note": note}, run=env.det("b", ignore=("note",))),
                env.step("c", ("b",)),
            ]
        )

    first, manifest = env.run(build("draft"))
    second, _ = env.run(build("final"), manifest=manifest)

    assert second.executed == ["b"]
    assert second.skipped == ["a", "c"]
    assert second.step_keys["b"] != first.step_keys["b"]
    assert second.outputs["b"] == first.outputs["b"]


class UnpinFailsStore(InMemoryArtifactStore):
    """A store whose unpin breaks (index unreachable): a pin left behind only delays retention."""

    def unpin(self, artifact_key: str, owner: str) -> None:
        raise ConnectionError("index unreachable")


def test_a_failing_unpin_does_not_lose_the_manifest(caplog: pytest.LogCaptureFixture) -> None:
    env = Env()
    env.store = UnpinFailsStore(env.clock)
    env.rewire()
    first, manifest = env.run(Graph([env.step("a", params={"n": 1})]))

    with caplog.at_level(logging.ERROR, logger="studio.core.graph"):
        second, relocked = env.run(Graph([env.step("a", params={"n": 2})]), manifest=manifest)

    assert relocked.locked == second.outputs != first.outputs
    assert any("could not unpin" in r.getMessage() for r in caplog.records)
    assert env.store.pinned_by(first.outputs["a"]) == {RUN}


# ------------------------------------------------------------------ human gates


def gated(env: Env) -> Graph:
    return Graph(
        [
            env.step("package", resource=LLM, params={"angle": "a"}),
            env.gate("g1", "package", GateName.G1),
            env.step("script", ("package", "g1"), resource=LLM),
            env.step("voice", ("script",), resource=GPU),
            env.step("side", ("package",)),
        ]
    )


def test_gate_without_decision_waits_and_blocks_downstream(env: Env) -> None:
    result, manifest = env.run(gated(env))

    assert result.waiting == ["g1"]
    assert result.executed == ["package", "side"]
    assert result.blocked == ["script", "voice"]
    assert env.calls["script"] == env.calls["voice"] == 0
    assert "no g1 decision" in result.reasons["g1"]
    assert set(manifest.locked) == {"package", "side"}
    assert "script" not in result.step_keys


@pytest.mark.parametrize(
    ("agent", "human", "reason"),
    [
        (Verdict.APPROVE, Verdict.PENDING, "g1 pending"),
        (Verdict.PENDING, Verdict.PENDING, "g1 pending"),
        (Verdict.APPROVE, Verdict.REJECT, "g1 rejected"),
        (Verdict.REJECT, Verdict.APPROVE, "g1 rejected"),  # the human cannot override an agent rejection at G1
    ],
)
def test_undecided_or_rejected_gate_waits_with_its_reason(env: Env, agent: Verdict, human: Verdict, reason: str) -> None:
    graph = gated(env)
    first, _ = env.run(graph)
    assert isinstance(env.decisions, DictDecisionSource)
    env.decisions.put(decision(GateName.G1, first.outputs["package"], agent, human, agent_reasons=("weak title",)))

    result, _ = env.run(graph, run_id="run-2")

    assert result.waiting == ["g1"]
    assert result.reasons["g1"].startswith(reason)
    if "rejected" in reason:
        assert "weak title" in result.reasons["g1"]
    assert env.calls["script"] == 0


def test_approved_gate_records_its_decision_and_unblocks_downstream(env: Env) -> None:
    graph = gated(env)
    first, manifest = env.run(graph)
    approval = decision(GateName.G1, first.outputs["package"], human_note="go")
    assert isinstance(env.decisions, DictDecisionSource)
    env.decisions.put(approval)

    second, manifest = env.run(graph, manifest=manifest)

    assert second.executed == ["g1", "script", "voice"]
    assert second.skipped == ["package", "side"]
    assert env.store.data(second.outputs["g1"]) == approval.canonical_json().encode()
    assert env.store.get(second.outputs["g1"]).media_type == "application/json"
    assert manifest.locked["g1"] == second.outputs["g1"]

    third, _ = env.run(graph, manifest=manifest)
    assert third.executed == []


def test_gate_decision_is_bound_to_the_exact_subject_hash(env: Env) -> None:
    def build(angle: str) -> Graph:
        g = gated(env)
        return Graph([env.step("package", resource=LLM, params={"angle": angle}), *g.steps[1:]])

    first, manifest = env.run(build("a"))
    assert isinstance(env.decisions, DictDecisionSource)
    env.decisions.put(decision(GateName.G1, first.outputs["package"]))
    approved, manifest = env.run(build("a"), manifest=manifest)
    assert "script" in approved.executed

    changed, relocked = env.run(build("b"), manifest=manifest)

    assert changed.executed == ["package", "side"]
    assert changed.waiting == ["g1"]  # a new package hash needs a new decision
    assert changed.blocked == ["script", "voice"]
    assert set(relocked.locked) == {"package", "side"}  # stale locks of the blocked steps are dropped
    assert env.store.pinned_by(approved.outputs["script"]) == set()


def test_gate_ignores_a_decision_about_another_subject() -> None:
    blind = Env(SubjectBlindDecisionSource([decision(GateName.G1, "f" * 64)]))

    result, _ = blind.run(gated(blind))

    assert result.waiting == ["g1"]
    assert "about " + "f" * 64 in result.reasons["g1"]


# ------------------------------------------------------------------ publication guard (ADR-001 decision 8)


def render_step(env: Env, cut: int) -> StepSpec:
    return env.step("render", resource=GPU, params={"cut": cut})


def publishing(env: Env, cut: int, guarded: bool = True) -> Graph:
    requires = ((GateName.COMPLIANCE, "render"), (GateName.G2, "render")) if guarded else ()
    return Graph([render_step(env, cut), env.step("publish", ("render",), requires=requires, estimated={CostKind.EUR: 0.01})])


def render_key(cut: int) -> str:
    """Output key of the render step, computed on a separate store."""
    probe = Env()
    result, _ = probe.run(Graph([render_step(probe, cut)]))
    return result.outputs["render"]


def approving_env(*decisions: GateDecision) -> tuple[Env, DictDecisionSource]:
    source = DictDecisionSource(decisions)
    env = Env(source)
    return env, source


def test_publication_runs_with_compliance_and_g2_on_the_render_hash() -> None:
    key = render_key(1)
    env, _ = approving_env(decision(GateName.COMPLIANCE, key, human=Verdict.PENDING), decision(GateName.G2, key))

    result, manifest = env.run(publishing(env, 1))

    assert result.executed == ["render", "publish"]
    assert manifest.locked["publish"] == result.outputs["publish"]


@pytest.mark.parametrize(
    ("decisions", "why"),
    [
        pytest.param(lambda k: [decision(GateName.G2, k)], "no compliance decision", id="no-compliance-verdict"),
        pytest.param(lambda k: [decision(GateName.COMPLIANCE, k)], "no g2 decision", id="no-g2"),
        pytest.param(
            lambda k: [decision(GateName.COMPLIANCE, k, agent=Verdict.REJECT, human=Verdict.APPROVE), decision(GateName.G2, k)],
            "compliance rejected",
            id="compliance-rejected-human-approves",
        ),
        pytest.param(
            lambda k: [decision(GateName.COMPLIANCE, k, agent=Verdict.PENDING), decision(GateName.G2, k)],
            "compliance pending",
            id="compliance-pending",
        ),
        pytest.param(
            lambda k: [decision(GateName.COMPLIANCE, k), decision(GateName.G2, k, human=Verdict.PENDING)],
            "g2 pending",
            id="g2-pending",
        ),
    ],
)
def test_publication_refused_without_both_approvals(decisions: Callable[[str], list[GateDecision]], why: str) -> None:
    env, _ = approving_env(*decisions(render_key(1)))

    with pytest.raises(GateNotApproved, match=why):
        env.run(publishing(env, 1))

    assert env.calls["render"] == 1
    assert env.calls["publish"] == 0
    # refused before any reservation: only the render reserved (and settled) its GPU time
    assert statuses(env.ledger) == [(GPU_S, "settled")]


def test_publication_refused_with_g2_on_an_old_render_hash() -> None:
    old = render_key(1)
    env, decisions = approving_env(decision(GateName.COMPLIANCE, old), decision(GateName.G2, old))
    first, manifest = env.run(publishing(env, 1))
    assert first.executed == ["render", "publish"]

    new = render_key(2)
    decisions.put(decision(GateName.COMPLIANCE, new))  # compliance re-checked the new render, G2 did not
    with pytest.raises(GateNotApproved, match="no g2 decision on " + new):
        env.run(publishing(env, 2), manifest=manifest)
    assert env.calls["publish"] == 1


def test_publication_refused_when_the_source_returns_a_decision_about_an_old_hash() -> None:
    old = render_key(1)
    env = Env(SubjectBlindDecisionSource([decision(GateName.COMPLIANCE, old), decision(GateName.G2, old)]))

    with pytest.raises(GateNotApproved, match="is about " + old):
        env.run(publishing(env, 2))
    assert env.calls["publish"] == 0


def test_publication_guard_is_checked_before_reusing_a_stored_output(env: Env) -> None:
    # another graph declared the same publish step without the guard and bound its output in the store
    env.run(publishing(env, 1, guarded=False), run_id="other-run")
    assert env.calls["publish"] == 1

    with pytest.raises(GateNotApproved, match="no compliance decision") as err:
        env.run(publishing(env, 1))

    partial = partial_run(err.value)
    assert partial is not None and "publish" not in partial.manifest.locked
    assert partial.result.skipped == ["render"]


def test_publication_guard_is_checked_before_reusing_a_locked_output(env: Env) -> None:
    _, manifest = env.run(publishing(env, 1, guarded=False))  # locked while the step had no guard
    env.store.forget_step_outputs()

    with pytest.raises(GateNotApproved, match="no compliance decision"):
        env.run(publishing(env, 1), manifest=manifest)
    assert env.calls["publish"] == 1


def test_withdrawn_verdict_stops_the_replay_of_an_approved_publication() -> None:
    key = render_key(1)
    env, decisions = approving_env(decision(GateName.COMPLIANCE, key), decision(GateName.G2, key))
    first, manifest = env.run(publishing(env, 1))
    assert first.executed == ["render", "publish"]
    replay, manifest = env.run(publishing(env, 1), manifest=manifest)
    assert replay.executed == []  # still approved: the replay stays free

    decisions.put(decision(GateName.COMPLIANCE, key, agent=Verdict.REJECT, agent_reasons=("unlicensed music",)))

    with pytest.raises(GateNotApproved, match="compliance rejected .*unlicensed music"):
        env.run(publishing(env, 1), manifest=manifest)
    assert env.calls["publish"] == 1


def test_decision_refusal_checks_gate_subject_and_verdict() -> None:
    key = "a" * 64
    assert decision_refusal(decision(GateName.G2, key), GateName.G2, key) is None
    assert decision_refusal(decision(GateName.G1, key), GateName.G2, key) is not None
    assert decision_refusal(decision(GateName.G2, "b" * 64), GateName.G2, key) is not None
    assert decision_refusal(None, GateName.G2, key) == f"no g2 decision on {key}"
    reason = decision_refusal(
        decision(GateName.COMPLIANCE, key, agent=Verdict.REJECT, agent_reasons=("claim",)), GateName.COMPLIANCE, key
    )
    assert reason == "compliance rejected (agent reject, human approve): claim"


def test_full_demo_flow_waits_at_each_gate_then_publishes() -> None:
    env = Env()
    decisions = env.decisions
    assert isinstance(decisions, DictDecisionSource)
    graph = Graph(
        [
            env.step("package", resource=LLM),
            env.gate("g1", "package", GateName.G1),
            env.step("script", ("package", "g1")),
            env.step("assemble", ("script",), resource=GPU),
            env.gate("compliance", "assemble", GateName.COMPLIANCE),
            env.gate("g2", "assemble", GateName.G2),
            env.step(
                "publish_plan",
                ("assemble", "compliance", "g2"),
                requires=((GateName.COMPLIANCE, "assemble"), (GateName.G2, "assemble")),
            ),
        ]
    )
    r1, m = env.run(graph)
    assert (r1.executed, r1.waiting) == (["package"], ["g1"])
    decisions.put(decision(GateName.G1, r1.outputs["package"]))
    r2, m = env.run(graph, manifest=m)
    assert (r2.executed, r2.waiting, r2.blocked) == (["g1", "script", "assemble"], ["compliance", "g2"], ["publish_plan"])
    decisions.put(decision(GateName.COMPLIANCE, r2.outputs["assemble"], human=Verdict.PENDING))
    decisions.put(decision(GateName.G2, r2.outputs["assemble"]))
    r3, m = env.run(graph, manifest=m)
    assert r3.executed == ["compliance", "g2", "publish_plan"]
    r4, _ = env.run(graph, manifest=m)
    assert r4.executed == [] and r4.skipped == list(graph.names)


# ------------------------------------------------------------------ budget and costs


def test_cap_exceeded_raises_and_the_step_never_runs(env: Env) -> None:
    env.ledger.set_cap(Cap(VIDEO_SCOPE, GPU_S, 60.0))
    graph = Graph([env.step("shot", resource=GPU, estimated={GPU_S: 90.0})])

    with pytest.raises(BudgetExceeded):
        env.run(graph)

    assert env.calls["shot"] == 0
    assert env.ledger.reservations() == []
    assert env.store.step_output_count() == 0 and env.store.put_count == 0


def test_exhausted_gpu_cap_stops_the_next_gpu_step(env: Env) -> None:
    env.ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 60.0))
    graph = Graph(
        [
            env.step("a", resource=GPU, run=env.det("a", seconds=60.0), estimated={GPU_S: 60.0}),
            env.step("b", ("a",), resource=GPU, run=env.det("b", seconds=900.0), estimated={GPU_S: 1.0}),
        ]
    )

    with pytest.raises(BudgetExceeded):
        env.run(graph)

    assert env.calls["a"] == 1 and env.calls["b"] == 0
    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 60.0


def test_cap_exceeded_on_a_second_kind_gives_back_the_first_reservation(env: Env) -> None:
    env.ledger.set_cap(Cap(DAY_SCOPE, KWH, 1.0))
    graph = Graph([env.step("shot", resource=GPU, estimated={GPU_S: 30.0, KWH: 2.0})])

    with pytest.raises(BudgetExceeded):
        env.run(graph)

    assert env.calls["shot"] == 0
    assert statuses(env.ledger) == [(GPU_S, "released")]
    assert env.ledger.reserved(VIDEO_SCOPE, GPU_S) == 0.0


def test_measured_cost_is_settled_and_counts_against_the_cap(env: Env) -> None:
    env.ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 30.0))
    graph = Graph(
        [
            env.step("a", resource=GPU, run=env.det("a", seconds=25.0), estimated={GPU_S: 10.0}),
            env.step("b", ("a",), resource=GPU, estimated={GPU_S: 10.0}),
        ]
    )
    # on estimates alone b would fit (10 + 10 <= 30); the measured 25 s of a leave no room for it
    with pytest.raises(BudgetExceeded):
        env.run(graph)
    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 25.0
    assert env.calls["a"] == 1 and env.calls["b"] == 0


def test_claude_call_cap_stops_the_second_llm_step(env: Env) -> None:
    env.ledger.set_cap(Cap(DAY_SCOPE, CostKind.CLAUDE_CALLS, 1.0))
    graph = Graph([env.step("idea", resource=LLM), env.step("package", ("idea",), resource=LLM)])

    with pytest.raises(BudgetExceeded):
        env.run(graph)

    assert env.calls["idea"] == 1 and env.calls["package"] == 0
    assert [(e.kind, e.quantity, e.estimated) for e in env.ledger.entries()] == [(CostKind.CLAUDE_CALLS, 1.0, False)]


def test_costs_are_measured_where_possible_and_flagged_as_estimates_otherwise(env: Env) -> None:
    graph = Graph(
        [
            env.step("shot", resource=GPU, run=env.det("shot", seconds=12.5), estimated={GPU_S: 5.0, KWH: 0.2}),
            env.step("idea", resource=LLM, run=env.det("idea", seconds=3.0), estimated={CostKind.CLAUDE_SECONDS: 10.0}),
            env.step("mix", ("shot",), estimated={CostKind.EUR: 0.01}),
            env.step("free", ("mix",)),
        ]
    )
    result, manifest = env.run(graph)

    by_step = {
        name: [(e.kind, e.quantity, e.estimated) for e in result.costs if e.step_key == key]
        for name, key in result.step_keys.items()
    }
    assert by_step["shot"] == [(GPU_S, 12.5, False), (KWH, 0.2, True)]
    assert by_step["idea"] == [(CostKind.CLAUDE_CALLS, 1.0, False), (CostKind.CLAUDE_SECONDS, 3.0, False)]
    assert by_step["mix"] == [(CostKind.EUR, 0.01, True)]
    assert by_step["free"] == []
    assert all(e.run_id == RUN for e in result.costs)
    assert list(manifest.costs) == result.costs == env.ledger.entries(RUN)
    assert env.ledger.spent(VIDEO_SCOPE, GPU_S) == env.ledger.spent(DAY_SCOPE, GPU_S) == 12.5
    assert all(env.ledger.status(r.id) == "settled" for r in env.ledger.reservations())


def test_reservation_lease_scales_with_the_time_estimate(env: Env) -> None:
    runner = env.runner
    assert runner.lease_for(env.step("s", resource=GPU, estimated={GPU_S: 10.0})) == DEFAULT_LEASE
    assert runner.lease_for(env.step("s", resource=GPU, estimated={GPU_S: 7200.0})) == dt.timedelta(hours=6)
    llm = env.step("s", resource=LLM, estimated={CostKind.CLAUDE_SECONDS: 2000.0})
    assert runner.lease_for(llm) == dt.timedelta(seconds=6000)
    assert runner.lease_for(env.step("s")) == DEFAULT_LEASE

    start = env.clock()
    env.run(Graph([env.step("shot", resource=GPU, estimated={GPU_S: 7200.0, KWH: 0.5})]))
    assert {r.lease_until - start for r in env.ledger.reservations()} == {dt.timedelta(hours=6)}


def test_reservation_outlives_a_step_longer_than_the_default_lease() -> None:
    env = Env()
    env.ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 8000.0))
    other_runner = Runner(env.store, env.ledger, env.decisions, env.clock, "gpu1")
    other = Graph([env.step("other", resource=GPU, run=env.det("other", seconds=7200.0), estimated={GPU_S: 7200.0})])
    seen: dict[str, Any] = {}

    def long_shot(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.calls.hit("long")
        env.clock.advance(3700.0)  # still running after 1 h 01 min: the periodic reaper passes
        seen["reaped"] = env.ledger.reap_expired(env.clock())
        try:
            other_runner.run(other, "run-2", SCOPES, None, "channel-a", VideoFormat.SHORT)
            seen["other"] = "ran"
        except BudgetExceeded:
            seen["other"] = "refused"
        env.clock.advance(3500.0)
        return b"long shot", "video", "video/mp4"

    env.run(Graph([env.step("long", resource=GPU, run=long_shot, estimated={GPU_S: 7200.0})]))

    assert seen == {"reaped": [], "other": "refused"}  # 7200 held + 7200 asked > 8000
    assert env.calls["other"] == 0
    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 7200.0


class Abort(BaseException):
    """Not an Exception: an interrupt must release the reservation too."""


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("ComfyUI crashed"), Abort()],
    ids=["exception", "base-exception"],
)
def test_step_failure_charges_the_measured_gpu_time_and_releases_the_rest(env: Env, failure: BaseException) -> None:
    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.calls.hit("shot")
        env.clock.advance(7.0)
        raise failure

    graph = Graph([env.step("shot", resource=GPU, run=crash, estimated={GPU_S: 40.0, KWH: 0.1})])

    with pytest.raises(type(failure)) as err:
        env.run(graph)

    assert err.value is failure
    assert env.calls["shot"] == 1
    # the GPU seconds it burnt are in the ledger; the kWh, which the runner cannot measure, are released
    assert sorted(status for _, status in statuses(env.ledger)) == ["released", "settled"]
    assert env.ledger.reserved(VIDEO_SCOPE, GPU_S) == 0.0
    assert [(e.kind, e.quantity, e.estimated) for e in env.ledger.entries()] == [(GPU_S, 7.0, False)]
    assert env.ledger.spent(VIDEO_SCOPE, GPU_S) == 7.0
    assert env.store.step_output_count() == 0
    partial = partial_run(err.value)
    assert partial is not None
    assert partial.result.unbilled == []
    assert [(e.kind, e.quantity) for e in partial.manifest.costs] == [(GPU_S, 7.0)]  # the report matches the ledger
    assert "shot: 7 gpu_seconds consumed by the failed attempt and charged" in err.value.__notes__
    assert partial.manifest.locked == {}


def test_a_failed_attempt_counts_against_the_cap_of_the_retry(env: Env) -> None:
    """Burnt GPU time is not free: two failed 7 s attempts leave 8 s under a 22 s cap, not 22."""
    env.ledger.set_cap(Cap(VIDEO_SCOPE, GPU_S, 22.0))

    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.clock.advance(7.0)
        raise RuntimeError("out of memory")

    graph = Graph([env.step("shot", resource=GPU, run=crash, estimated={GPU_S: 10.0})])
    for _ in range(2):
        with pytest.raises(RuntimeError):
            env.run(graph)
    assert env.ledger.spent(VIDEO_SCOPE, GPU_S) == 14.0
    with pytest.raises(BudgetExceeded):  # 14 spent + 10 estimated > 22
        env.run(graph)


def test_failure_of_a_step_the_runner_does_not_measure_releases_everything(env: Env) -> None:
    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.clock.advance(5.0)
        raise RuntimeError("ffmpeg exited with 1")

    with pytest.raises(RuntimeError) as err:
        env.run(Graph([env.step("mix", run=crash, estimated={CostKind.EUR: 0.01})]))

    partial = partial_run(err.value)
    assert partial is not None and partial.result.unbilled == [] and partial.result.costs == []
    assert not getattr(err.value, "__notes__", [])
    assert statuses(env.ledger) == [(CostKind.EUR, "released")]
    assert env.ledger.entries() == []


class SettleRefusingLedger(InMemoryLedger):
    """A ledger that cannot record anything (database down)."""

    def settle(self, reservation_id: str, entry: CostEntry) -> None:
        raise ConnectionError("ledger unreachable")


def test_a_failed_attempt_the_ledger_cannot_record_is_reported_as_unbilled(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    env.ledger = SettleRefusingLedger(env.clock)
    env.rewire()

    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.clock.advance(4.0)
        raise RuntimeError("CUDA error")

    with caplog.at_level(logging.ERROR, logger="studio.core.graph"), pytest.raises(RuntimeError) as err:
        env.run(Graph([env.step("shot", resource=GPU, run=crash)]))
    partial = partial_run(err.value)
    assert partial is not None
    assert [(e.kind, e.quantity) for e in partial.result.unbilled] == [(GPU_S, 4.0)]
    assert any("could not charge the failed attempt of shot" in r.getMessage() for r in caplog.records)


class FrozenError(Exception):
    """An exception that refuses new attributes and notes (as some C extensions raise)."""

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is frozen")

    def add_note(self, note: str) -> None:
        raise TypeError("frozen")


def test_an_exception_that_cannot_carry_the_partial_run_still_propagates(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    failure = FrozenError("CUDA error")

    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.clock.advance(3.0)
        raise failure

    with caplog.at_level(logging.ERROR, logger="studio.core.graph"), pytest.raises(FrozenError) as err:
        env.run(Graph([env.step("shot", resource=GPU, run=crash)]))

    assert err.value is failure
    assert partial_run(err.value) is None
    messages = [r.getMessage() for r in caplog.records]
    assert any("could not attach the partial manifest" in m for m in messages)
    assert statuses(env.ledger) == [(GPU_S, "settled")]  # charged although the exception refuses notes
    assert [e.quantity for e in env.ledger.entries()] == [3.0]


class DiskFull(OSError):
    pass


class DiskFullStore(InMemoryArtifactStore):
    """A store that cannot write video (disk full) but still writes small JSON."""

    def put_bytes(self, data: bytes, *, kind: str, media_type: str) -> StoredArtifact:
        if kind == "video":
            raise DiskFull("No space left on device")
        return super().put_bytes(data, kind=kind, media_type=media_type)


def test_store_failure_after_the_step_keeps_its_measured_cost() -> None:
    env = Env()
    env.store = DiskFullStore(env.clock)
    env.rewire()
    env.ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 60.0))
    graph = Graph([env.step("shot", resource=GPU, run=env.rand("shot", seconds=40.0), estimated={GPU_S: 40.0})])

    with pytest.raises(DiskFull) as err:
        env.run(graph)

    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 40.0  # the GPU time was used: it is charged
    assert env.ledger.reserved(DAY_SCOPE, GPU_S) == 0.0
    assert statuses(env.ledger) == [(GPU_S, "settled")]
    assert env.store.step_output_count() == 0
    partial = partial_run(err.value)
    assert partial is not None and [e.quantity for e in partial.manifest.costs] == [40.0]
    # a retry loop cannot burn GPU time past the cap: the second attempt no longer fits
    with pytest.raises(BudgetExceeded):
        for _ in range(5):
            with contextlib.suppress(DiskFull):
                env.run(graph)
    assert env.calls["shot"] == 1
    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 40.0


class SettleFailsLedger(InMemoryLedger):
    """A ledger that cannot record one kind of cost (database down in the middle of a settlement)."""

    def __init__(self, clock: ManualClock, failing: CostKind | None) -> None:
        super().__init__(clock)
        self.failing = failing

    def settle(self, reservation_id: str, entry: CostEntry) -> None:
        if entry.kind is self.failing:
            raise ConnectionError("ledger unreachable")
        super().settle(reservation_id, entry)


def test_settle_failure_keeps_the_output_out_of_the_store() -> None:
    env = Env()
    ledger = SettleFailsLedger(env.clock, KWH)
    env.ledger = ledger
    env.rewire()
    graph = Graph([env.step("shot", resource=GPU, run=env.rand("shot", seconds=300.0), estimated={GPU_S: 300.0, KWH: 0.1})])

    with pytest.raises(CostNotSettled) as err:
        env.run(graph)

    assert isinstance(err.value.__cause__, ConnectionError)
    assert statuses(ledger) == [(GPU_S, "settled"), (KWH, "active")]  # never released
    assert env.store.put_count == 0 and env.store.step_output_count() == 0
    ((reservation_id, entry),) = err.value.pending
    assert (entry.kind, entry.quantity, entry.estimated) == (KWH, 0.1, True)
    # the orchestrator settles the missing entry later, even after the reaper went by
    ledger.failing = None
    assert ledger.reap_expired(env.clock() + dt.timedelta(days=1)) == [reservation_id]
    ledger.settle(reservation_id, entry)
    assert ledger.spent(VIDEO_SCOPE, KWH) == 0.1
    # nothing was bound, so the next run pays again for what it uses instead of reusing an unpaid output
    result, manifest = env.run(graph)
    assert result.executed == ["shot"] and env.calls["shot"] == 2
    assert ledger.spent(VIDEO_SCOPE, GPU_S) == 600.0


@pytest.mark.parametrize(
    ("output", "message"),
    [
        pytest.param((b"frames", "mp4", "video/mp4"), "unknown artifact kind 'mp4'", id="kind"),
        pytest.param((b"frames", "video", "mp4"), "invalid media type", id="media-type"),
        pytest.param(("frames", "video", "video/mp4"), "expected bytes", id="data"),
        pytest.param([b"frames", "video", "video/mp4"], "must return", id="shape"),
    ],
)
def test_output_the_store_would_refuse_is_rejected_after_its_cost_is_settled(env: Env, output: Any, message: str) -> None:
    def bad(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> Any:
        env.calls.hit("shot")
        env.clock.advance(10.0)
        return output

    graph = Graph([env.step("shot", resource=GPU, run=bad, estimated={GPU_S: 30.0})])

    with pytest.raises(StepOutputError, match=message):
        env.run(graph)

    assert env.ledger.spent(DAY_SCOPE, GPU_S) == 10.0
    assert statuses(env.ledger) == [(GPU_S, "settled")]
    assert env.store.put_count == 0


class ReleaseFailsLedger(InMemoryLedger):
    """A ledger whose release breaks (database down): the reaper will free the reservation later."""

    def release(self, reservation_id: str) -> None:
        raise ConnectionError("ledger unreachable")


def test_a_failing_release_does_not_hide_the_step_error(caplog: pytest.LogCaptureFixture) -> None:
    env = Env()
    env.ledger = ReleaseFailsLedger(env.clock)
    env.runner = Runner(env.store, env.ledger, env.decisions, env.clock, "cpu")
    failure = RuntimeError("ffmpeg exited with 1")

    def crash(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        raise failure

    # a cost the runner cannot measure is released on failure (a measured GPU cost is charged instead)
    graph = Graph([env.step("mix", run=crash, estimated={CostKind.EUR: 0.01})])
    with caplog.at_level(logging.ERROR, logger="studio.core.graph"), pytest.raises(RuntimeError) as err:
        env.run(graph)

    assert err.value is failure
    assert any("could not release reservation" in r.getMessage() for r in caplog.records)
    # still active: the lease reaper is what frees it after a crash
    (reservation,) = env.ledger.reservations()
    assert env.ledger.status(reservation.id) == "active"
    assert env.ledger.reap_expired(env.clock() + dt.timedelta(hours=2)) == [reservation.id]
    assert env.ledger.reserved(VIDEO_SCOPE, CostKind.EUR) == 0.0


class PurgeRacesPinStore(InMemoryArtifactStore):
    """Retention purges an unpinned artifact between the runner's existence check and its pin."""

    def __init__(self, victim: str | None = None, **kw: Any) -> None:
        super().__init__(**kw)
        self.victim = victim

    def pin(self, artifact_key: str, owner: str) -> None:
        if artifact_key == self.victim:
            self.victim = None
            self.lose(artifact_key)
        super().pin(artifact_key, owner)


def test_output_purged_while_being_reused_is_recomputed() -> None:
    env = Env()
    store = PurgeRacesPinStore(clock=env.clock)
    env.store = store
    env.rewire()
    graph = Graph([env.step("shot", resource=GPU, run=env.rand("shot")), env.step("grade", ("shot",))])
    first, _ = env.run(graph, run_id="run-0")
    store.unpin(first.outputs["shot"], "run-0")
    store.victim = first.outputs["shot"]

    second, manifest = env.run(graph)

    assert second.executed == ["shot", "grade"]
    assert env.calls["shot"] == 2
    assert not store.has(first.outputs["shot"])
    assert store.step_output(second.step_keys["shot"]) == manifest.locked["shot"] != first.outputs["shot"]
    with pytest.raises(ArtifactMissing):
        store.get(first.outputs["shot"])


# ------------------------------------------------------------------ partial runs (the run raised)


def test_aborted_run_hands_back_a_manifest_that_keeps_pins_in_line(env: Env) -> None:
    _, manifest = env.run(Graph([render_step(env, 0)]))
    renders = [manifest.locked["render"]]

    for cut in (1, 2, 3):  # three renders refused by the publication guard
        with pytest.raises(GateNotApproved) as err:
            env.run(publishing(env, cut), manifest=manifest)
        partial = partial_run(err.value)
        assert partial is not None
        manifest = partial.manifest
        render = partial.result.outputs["render"]
        # the render awaiting its approvals stays locked and pinned; the one it supersedes is released
        assert manifest.locked == {"render": render}
        assert env.store.pinned_for(RUN) == {render}
        renders.append(render)

    _, manifest = env.run(Graph([render_step(env, 4)]), manifest=manifest)

    assert env.store.pinned_for(RUN) == set(manifest.locked.values())
    env.clock.advance(10 * 86400)
    assert env.store.purge_unpinned(dt.timedelta(days=1)) == sorted(renders)
    assert all(env.store.has(k) for k in manifest.locked.values())


def test_aborted_run_keeps_the_locks_of_the_steps_it_did_not_reach(env: Env) -> None:
    def build(topic: str) -> Graph:
        return Graph(
            [
                env.step("idea", resource=LLM, params={"topic": topic}),
                env.step("shot", ("idea",), resource=GPU, run=env.rand("shot"), estimated={GPU_S: 50.0}),
                env.step("grade", ("shot",)),
            ]
        )

    first, manifest = env.run(build("bridges"))
    env.ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 1.0))

    with pytest.raises(BudgetExceeded) as err:
        env.run(build("tunnels"), manifest=manifest)

    partial = partial_run(err.value)
    assert partial is not None
    assert partial.result.executed == ["idea"]
    new_idea = partial.result.outputs["idea"]
    assert partial.manifest.locked == {**manifest.locked, "idea": new_idea}
    assert partial.manifest.step_keys["shot"] == manifest.step_keys["shot"]
    assert env.store.pinned_by(first.outputs["shot"]) == env.store.pinned_by(new_idea) == {RUN}
    assert env.store.pinned_by(first.outputs["idea"]) == set()
    assert list(partial.manifest.costs) == [*manifest.costs, *partial.result.costs] == env.ledger.entries(RUN)


class RacedStore(InMemoryArtifactStore):
    """Another producer binds the step key `victim` first, with other bytes, just before this runner commits it."""

    def __init__(self, clock: ManualClock) -> None:
        super().__init__(clock)
        self.victim: str | None = None

    def commit_step_output(self, step_key: str, artifact_key: str) -> str:
        if step_key == self.victim:
            self.victim = None
            other = self.put_bytes(b"other producer", kind="json", media_type="application/json")
            super().commit_step_output(step_key, other.key)
        return super().commit_step_output(step_key, artifact_key)


def test_losing_a_race_never_unpins_an_output_the_run_uses_elsewhere() -> None:
    env = Env()
    store = RacedStore(env.clock)
    env.store = store
    env.rewire()
    same = b'{"subtitles":[]}'
    graph = Graph([env.step("a", run=env.fixed("a", same)), env.step("b", run=env.fixed("b", same))])
    store.victim = mock_key(graph["b"])

    result, manifest = env.run(graph)

    shared = manifest.locked["a"]
    assert [(w.step, w.discarded_key) for w in result.wasted] == [("b", shared)]
    assert manifest.locked["b"] != shared
    assert store.pinned_by(shared) == store.pinned_by(manifest.locked["b"]) == {RUN}
    env.clock.advance(2 * 86400)
    assert store.purge_unpinned(dt.timedelta(days=1)) == []
    assert store.has(shared)


# ------------------------------------------------------------------ concurrency: first write wins


def test_first_write_wins_between_concurrent_runners() -> None:
    n = 8
    env = Env()
    barrier = threading.Barrier(n, timeout=10)

    def sample(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.calls.hit("shot")
        barrier.wait()  # every runner has checked the store and is computing before anyone commits
        return os.urandom(32), "video", "video/mp4"

    graph = Graph([env.step("shot", resource=GPU, run=sample), env.step("grade", ("shot",))])
    runners = [Runner(env.store, env.ledger, env.decisions, env.clock, f"gpu{i % 4}") for i in range(n)]
    with ThreadPoolExecutor(n) as pool:
        futures = [
            pool.submit(r.run, graph, f"run-{i}", SCOPES, None, "channel-a", VideoFormat.SHORT) for i, r in enumerate(runners)
        ]
        results = [f.result(timeout=30) for f in futures]

    assert env.calls["shot"] == n
    kept = {result.outputs["shot"] for result, _ in results}
    assert len(kept) == 1
    winner = kept.pop()
    shot_key = results[0][0].step_keys["shot"]
    assert env.store.step_output(shot_key) == winner
    assert {manifest.locked["shot"] for _, manifest in results} == {winner}
    assert len({result.step_keys["grade"] for result, _ in results}) == 1

    wasted = [w for result, _ in results for w in result.wasted if w.step == "shot"]
    assert len(wasted) == n - 1
    assert sum(1 for result, _ in results if not any(w.step == "shot" for w in result.wasted)) == 1
    assert {w.kept_key for w in wasted} == {winner}
    discarded = {w.discarded_key for w in wasted}
    assert len(discarded) == n - 1 and winner not in discarded
    assert all(env.store.pinned_by(k) == set() for k in discarded)
    assert env.store.pinned_by(winner) == {f"run-{i}" for i in range(n)}
    # the losers' work was really paid: it stays in the ledger, attributed to each run
    shot_entries = [e for e in env.ledger.entries() if e.step_key == shot_key]
    assert len(shot_entries) == n
    assert {e for w in wasted for e in w.costs} <= set(shot_entries)


# ------------------------------------------------------------------ the runner on the SQL store and ledger


def test_runner_on_the_sql_store_and_ledger(tmp_path: Path) -> None:
    clock = ManualClock()
    engine = make_engine(f"sqlite:///{tmp_path / 'studio.db'}")
    try:
        store = LocalArtifactStore(tmp_path / "store", engine, clock=clock)
        store.create_schema()
        ledger = SqlCostLedger(engine, clock=clock)
        ledger.create_schema()
        ledger.set_cap(Cap(DAY_SCOPE, GPU_S, 100.0))
        decisions = DictDecisionSource()
        runner = Runner(store, ledger, decisions, clock, "gpu0")
        calls = Calls()

        def shot(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            calls.hit("shot")
            clock.advance(12.0)
            return os.urandom(64), "video", "video/mp4"

        def publish(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            calls.hit("publish")
            return canonical_json({"render": inputs["shot"].key}).encode(), "json", "application/json"

        def mp4(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
            clock.advance(12.0)
            return b"frames", "mp4", "video"

        requires = ((GateName.COMPLIANCE, "shot"), (GateName.G2, "shot"))
        graph = Graph(
            [
                StepSpec("idea", "1", (), {"topic": "aqueducts"}, LLM, noop_run),
                StepSpec("shot", "1", ("idea",), {}, GPU, shot, estimated_cost={GPU_S: 30.0}),
                StepSpec("g2", "1", ("shot",), {}, HUMAN, noop_run, gate=GateName.G2),
                StepSpec("publish", "1", ("shot", "g2"), {}, CPU, publish, requires_approval=requires),
            ]
        )

        def run(manifest: RunManifest | None = None) -> tuple[RunResult, RunManifest]:
            return runner.run(graph, RUN, SCOPES, manifest, "channel-a", VideoFormat.LONG)

        first, manifest = run()
        assert (first.executed, first.waiting, first.blocked) == (["idea", "shot"], ["g2"], ["publish"])
        render = first.outputs["shot"]
        decisions.put(decision(GateName.COMPLIANCE, render))
        decisions.put(decision(GateName.G2, render))
        second, manifest = run(manifest)
        assert (second.executed, second.skipped) == (["g2", "publish"], ["idea", "shot"])
        third, manifest = run(manifest)
        assert third.executed == [] and calls["shot"] == calls["publish"] == 1

        assert ledger.entries(RUN) == list(manifest.costs)
        assert ledger.spent(DAY_SCOPE, GPU_S) == 12.0
        assert all(store.pinned_by(k) == [RUN] for k in manifest.locked.values())
        assert store.get(manifest.locked["g2"]).kind == "json"

        # an output the SQL store would refuse is caught before it, and its GPU time is charged
        bad = Graph([StepSpec("bad", "1", (), {}, GPU, mp4, estimated_cost={GPU_S: 30.0})])
        with pytest.raises(StepOutputError, match="mp4"):
            runner.run(bad, "run-bad", SCOPES, None, "channel-a", VideoFormat.LONG)
        assert ledger.spent(DAY_SCOPE, GPU_S) == 24.0
        assert store.step_output(mock_key(bad["bad"])) is None
    finally:
        engine.dispose()


# ------------------------------------------------------------------ run arguments


def test_run_arguments_are_checked(env: Env) -> None:
    graph = Graph([env.step("a")])
    _, manifest = env.run(graph)
    with pytest.raises(ValueError, match="belongs to run"):
        env.run(graph, run_id="run-2", manifest=manifest)
    with pytest.raises(ValueError, match="dry_run"):
        env.run(graph, manifest=manifest, dry_run=False)
    with pytest.raises(ValueError, match="channel"):
        env.runner.run(graph, RUN, SCOPES, manifest, "channel-b")
    with pytest.raises(ValueError, match="channel_id and format"):
        env.runner.run(graph, RUN, SCOPES)
    with pytest.raises(ValueError, match="scope"):
        env.runner.run(graph, RUN, [], None, "channel-a", VideoFormat.SHORT)
    with pytest.raises(TypeError, match="scope"):
        env.runner.run(graph, RUN, VIDEO_SCOPE, None, "channel-a", VideoFormat.SHORT)
    with pytest.raises(ValueError, match="format"):
        env.runner.run(graph, RUN, SCOPES, manifest, "channel-a", VideoFormat.LONG)
    with pytest.raises(ValueError, match="run_id"):
        env.runner.run(graph, "", SCOPES, None, "channel-a", VideoFormat.SHORT)
    with pytest.raises(ValueError, match="unknown steps"):
        env.run(graph, manifest=manifest, upgrade=("ghost",))
    with pytest.raises(TypeError, match="upgrade"):
        env.run(graph, manifest=manifest, upgrade="a")
    with pytest.raises(ValueError, match="executor_id"):
        Runner(env.store, env.ledger, env.decisions, env.clock, "")
    with pytest.raises(ValueError, match="lease"):
        Runner(env.store, env.ledger, env.decisions, env.clock, "cpu", lease=dt.timedelta(0))
    with pytest.raises(ValueError, match="lease_factor"):
        Runner(env.store, env.ledger, env.decisions, env.clock, "cpu", lease_factor=0.5)


def test_mock_flag_is_sticky_across_runs(env: Env) -> None:
    graph = Graph([env.step("a")])
    _, manifest = env.run(graph, mock=True)
    _, again = env.run(graph, manifest=manifest, mock=False)
    assert again.mock is True
    _, real = env.run(graph, run_id="run-3", dry_run=False, mock=False)
    assert real.mock is False and real.dry_run is False


# ------------------------------------------------------------------ heartbeat of reservations


def test_a_running_step_keeps_its_reservations_alive_with_the_heartbeat(env: Env) -> None:
    """A step slower than its lease is not reaped while it runs: the heartbeat renews the reservation."""
    env.runner = Runner(
        env.store,
        env.ledger,
        env.decisions,
        env.clock,
        "gpu0",
        lease=dt.timedelta(seconds=10),
        renew_every=dt.timedelta(milliseconds=5),
    )
    seen: dict[str, Any] = {}

    def slow(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        first_lease = env.ledger.reservations()[0].lease_until
        env.clock.advance(8.0)
        deadline = time.monotonic() + 10.0  # wait for the heartbeat thread (real time), not for a fixed delay
        while env.ledger.reservations()[0].lease_until <= first_lease and time.monotonic() < deadline:
            time.sleep(0.005)
        env.clock.advance(8.0)  # t0 + 16 s: past the first lease (t0 + 10 s), inside the renewed one (t0 + 18 s)
        seen["reaped"] = env.ledger.reap_expired(env.clock())
        return b"video", "video", "video/mp4"

    env.run(Graph([env.step("shot", resource=GPU, run=slow, estimated={GPU_S: 1.0})]))

    assert seen["reaped"] == []
    assert statuses(env.ledger) == [(GPU_S, "settled")]


def test_without_a_heartbeat_the_same_slow_step_is_reaped(env: Env) -> None:
    """The contrast that gives the previous test its meaning."""
    env.runner = Runner(
        env.store, env.ledger, env.decisions, env.clock, "gpu0", lease=dt.timedelta(seconds=10), renew_every=dt.timedelta(hours=1)
    )
    seen: dict[str, Any] = {}

    def slow(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        env.clock.advance(16.0)
        seen["reaped"] = env.ledger.reap_expired(env.clock())
        return b"video", "video", "video/mp4"

    env.run(Graph([env.step("shot", resource=GPU, run=slow, estimated={GPU_S: 1.0})]))

    assert len(seen["reaped"]) == 1  # the budget was freed while the step was still working


def test_a_failing_heartbeat_does_not_stop_the_step(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    class BrokenRenewLedger(InMemoryLedger):
        def renew(self, reservation_id: str, lease_until: dt.datetime) -> Reservation:
            raise ConnectionError("ledger unreachable")

    env.ledger = BrokenRenewLedger(env.clock)
    env.runner = Runner(
        env.store,
        env.ledger,
        env.decisions,
        env.clock,
        "gpu0",
        lease=dt.timedelta(seconds=10),
        renew_every=dt.timedelta(milliseconds=5),
    )

    def slow(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        time.sleep(0.05)
        return b"video", "video", "video/mp4"

    with caplog.at_level(logging.ERROR, logger="studio.core.graph"):
        result, _ = env.run(Graph([env.step("shot", resource=GPU, run=slow, estimated={GPU_S: 1.0})]))

    assert result.executed == ["shot"]
    assert any("could not renew reservation" in r.getMessage() for r in caplog.records)


def test_a_step_without_reservations_starts_no_heartbeat_thread(env: Env) -> None:
    names: list[str] = []

    def spy(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        names.extend(t.name for t in threading.enumerate() if t.name.startswith("renew-"))
        return b"x", "json", "application/json"

    env.run(Graph([env.step("plain", run=spy)]))
    assert names == []


def test_renew_every_must_be_positive() -> None:
    env = Env()
    with pytest.raises(ValueError, match="renew_every"):
        Runner(env.store, env.ledger, env.decisions, env.clock, "cpu", renew_every=dt.timedelta(0))
