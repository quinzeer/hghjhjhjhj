"""Dry-run driver: one video, end to end, through mock adapters (docs/design/phase1.md).

`run_dry` runs the graph the way production will: a run stops at every gate that has no decision, a reviewer
records one, and the run resumes with every finished step reused. Here the reviewers are mocks; in
production the compliance agent and the human (validation UI) write the same `GateDecision` rows.

State lives under `out_dir/state` (SQLite index, cost ledger, decisions, content-addressed files), so a
second invocation with the same channel, format and seed reuses everything: it executes no step and writes
the same render. Files for people go under `out_dir/<channel>/<format>/`.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import shutil
import uuid
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from studio.adapters.llm_base import LLMRunner, QuotaExhausted
from studio.core.artifacts import LocalArtifactStore
from studio.core.costs import SqlCostLedger
from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.graph import Graph, Runner, RunResult, partial_run
from studio.core.interfaces import Cap, StepSpec, StudioError
from studio.core.quota import QuotaManager
from studio.domain import (
    Channel,
    CostKind,
    GateDecision,
    GateName,
    Idea,
    Package,
    RunManifest,
    Script,
    VideoFormat,
)
from studio.pipeline.mock_agents import MockComplianceOfficer, MockReviewer
from studio.pipeline.steps import Production, front_steps, production_steps
from studio.scenario.skill_json import to_skill_json

MAX_ROUNDS = 8  # a video has 3 gates; more rounds than that means a gate never gets its approval
# Caps of docs/COST_MODEL.md § Plafonds (initial values, adjustable by ADR): GPU seconds and Claude calls.
GPU_CAP_S = {VideoFormat.LONG: 36 * 3600.0, VideoFormat.SHORT: 4 * 3600.0}
CLAUDE_CALL_CAP = {VideoFormat.LONG: 80.0, VideoFormat.SHORT: 20.0}
GPU_CAP_DAY_S = 80 * 3600.0
GPU_CAP_MONTH_S = 600 * 3600.0
PAUSE_EXIT = "paused"


class GateRejected(StudioError):
    """A gate holds a rejection: the run cannot continue until the subject changes or a new verdict is recorded."""

    def __init__(self, gate: str, step: str, reason: str) -> None:
        super().__init__(f"{gate} rejected at step {step!r}: {reason}")
        self.gate, self.step, self.reason = gate, step, reason


class RunPaused(StudioError):
    """The Claude subscription's usage limit was hit: resume after `resume_at`."""

    def __init__(self, resume_at: dt.datetime, message: str) -> None:
        super().__init__(f"paused until {resume_at.isoformat()}: {message}")
        self.resume_at = resume_at


class Reviewer(Protocol):
    """Answers G1 and G2 (the human's gates)."""

    def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision: ...


class ComplianceReviewer(Protocol):
    """Answers the compliance gate from the artifacts it judges."""

    def review(self, script: Script, qa_report: Mapping[str, Any], render_key: str, now: dt.datetime) -> GateDecision: ...


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
    officer: ComplianceReviewer | None = None  # default: MockComplianceOfficer (checks the script and the QA report)

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


def _copy_out(src: Path, dst: Path) -> None:
    """Copy a stored file next to the reports, atomically, unless `dst` already is that copy.

    A copy, never a hard link: the store's files are shared by hash, and a tool that edits `dst` in place would
    corrupt the artifact for every run that uses it."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    source = src.stat()
    with contextlib.suppress(FileNotFoundError):
        delivered = dst.stat()
        if (delivered.st_size, delivered.st_mtime_ns) == (source.st_size, source.st_mtime_ns):
            return
    tmp = dst.with_name(f".{dst.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        shutil.copy2(src, tmp)  # keeps the modification time, which is how a later run recognises its copy
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)


class _Autopilot:
    """The mock reviewers that answer the gates of a dry run."""

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

    def decide(self, gate: GateName, subject_key: str, outputs: Mapping[str, str]) -> Any:
        now = self.clock()
        if gate is GateName.COMPLIANCE:
            script = Script.model_validate_json(self._read(outputs["script"]))
            qa_report = json.loads(self._read(outputs["qa"]))
            return self.officer.review(script, qa_report, subject_key, now)
        return self.reviewer.decide(gate, subject_key, now)

    def _read(self, key: str) -> str:
        return self.store.get(key).path.read_text(encoding="utf-8")


def _drive(
    runner: Runner,
    graph: Graph,
    config: DryRunConfig,
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
                mock=True,
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
        # The compliance verdict comes first: a render it blocks is never put to the human at G2 (MISSION §11).
        for name in sorted(result.waiting, key=lambda n: graph[n].gate is not GateName.COMPLIANCE):
            step: StepSpec = graph[name]
            gate = GateName(step.gate) if step.gate is not None else None
            if gate is None:
                raise StudioError(f"step {name!r} waits but is not a gate")
            subject = result.outputs[step.inputs[0]]
            if decisions.get(gate, subject) is not None:  # a decision exists and the gate still waits: a rejection
                raise GateRejected(gate.value, name, result.reasons.get(name, "no reason recorded"))
            decision = autopilot.decide(gate, subject, result.outputs)
            decisions.put(decision)
            if not decision.approved:
                raise GateRejected(gate.value, name, _why(decision))
    raise StudioError(f"gates still waiting after {MAX_ROUNDS} rounds")


def _why(decision: GateDecision) -> str:
    return "; ".join(decision.agent_reasons) or decision.human_note or "no reason recorded"


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


def _summarise_costs(ledger: SqlCostLedger, run_id: str) -> dict[str, float]:
    totals: defaultdict[str, float] = defaultdict(float)
    for entry in ledger.entries(run_id):
        totals[entry.kind.value] += entry.quantity
    return {kind: round(total, 3) for kind, total in sorted(totals.items())}


def run_dry(config: DryRunConfig, *, clock: Callable[[], dt.datetime] | None = None) -> dict[str, Any]:
    """Run one video through mock adapters and return its report (also written to `report.json`)."""
    clock = clock or (lambda: dt.datetime.now(dt.UTC))
    state = config.out_dir / "state"
    folder = config.out_dir / config.channel.id / config.format.value
    state.mkdir(parents=True, exist_ok=True)
    engine = make_engine(config.database_url or f"sqlite:///{state / 'studio.db'}")
    store = LocalArtifactStore(state / "cas", engine)
    ledger = SqlCostLedger(engine)
    decisions = SqlDecisionStore(engine)
    for backend in (store, ledger, decisions):
        backend.create_schema()

    run_id = config.effective_run_id
    now = clock()
    fmt = config.format
    scopes = [f"video:{run_id}", f"day:{now:%Y-%m-%d}", f"month:{now:%Y-%m}"]
    ledger.set_cap(Cap(scopes[0], CostKind.GPU_SECONDS, GPU_CAP_S[fmt]))
    ledger.set_cap(Cap(scopes[0], CostKind.CLAUDE_CALLS, CLAUDE_CALL_CAP[fmt]))
    ledger.set_cap(Cap(scopes[1], CostKind.GPU_SECONDS, GPU_CAP_DAY_S))
    ledger.set_cap(Cap(scopes[2], CostKind.GPU_SECONDS, GPU_CAP_MONTH_S))

    manifest = _load_manifest(folder / "manifest.json", run_id)
    production = Production.from_mocks(config.channel, fmt, config.seed, config.llm, cwd=config.out_dir)
    runner = Runner(store, ledger, decisions, clock, executor_id="dry-run")
    autopilot = _Autopilot(store, clock, config.reviewer, config.officer)
    tally = _Tally()
    quota = QuotaManager(clock)

    try:
        front = Graph(front_steps(production))
        result, manifest = _drive(runner, front, config, scopes, manifest, autopilot, decisions, folder, tally)
        script = Script.model_validate_json(store.get(result.outputs["script"]).path.read_text(encoding="utf-8"))
        full = Graph(front_steps(production) + production_steps(production, script))
        result, manifest = _drive(runner, full, config, scopes, manifest, autopilot, decisions, folder, tally)
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

    render_key = result.outputs["assemble"]
    render_path = folder / "render.mp4"
    _copy_out(store.get(render_key).path, render_path)
    package = Package.model_validate_json(read("package"))
    idea = Idea.model_validate_json(read("idea"))
    _write_json(folder / "script.scenes.json", to_skill_json(script, package))
    entries = ledger.entries(config.effective_run_id)
    _write_json(folder / "costs.json", [e.model_dump(mode="json") for e in entries])
    report: dict[str, Any] = {
        "run_id": config.effective_run_id,
        "channel_id": config.channel.id,
        "format": config.format.value,
        "dry_run": True,
        "mock": True,
        "adapters": production.adapter_ids(),
        "idea_id": idea.id,
        "executed": tally.executed,
        "skipped": tally.skipped,
        "waiting": result.waiting,
        "rounds": tally.rounds,
        "render_key": render_key,
        "render_path": str(render_path),
        "duration_expected_s": script.duration_s,
        "scene_count": len(script.scenes),
        "qa_defects": json.loads(read("qa"))["defects"],
        "publication": json.loads(read("publish_plan")),
        "costs": _summarise_costs(ledger, config.effective_run_id),
        "step_count": len(result.step_keys),
        "manifest_mock": manifest.mock,
    }
    _write_json(folder / "report.json", report)
    return report
