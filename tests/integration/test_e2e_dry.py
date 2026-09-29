"""The dry run end to end: one video through every step with mock adapters (MISSION §9, phase 1 exit criteria).

The full Short is produced once for the module (about 30 s). Scenarios that need another video start from a
three-scene run (hook, set-up, pay-off), produced once and cloned, so that each stays within a few seconds.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from pipeline_fakes import EditedNarrationLLM, NoDisclosureLLM, QuotaAtAgentLLM, RejectingReviewer, channel

from studio.adapters.llm_base import LLMRunner
from studio.core.artifacts import LocalArtifactStore
from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.graph import ManifestMismatch
from studio.core.interfaces import StudioError
from studio.domain import GateDecision, GateName, RunManifest, SceneRole, Verdict, VideoFormat
from studio.media import qa
from studio.pipeline.driver import DryRunConfig, GateRejected, RunPaused, StateBusy, run_dry
from studio.pipeline.mock_agents import MockStudioLLM, build_idea, build_package, build_script_doc
from studio.scenario.skill_json import from_skill_json

pytestmark = pytest.mark.media

SHORT_ROLES = (SceneRole.HOOK, SceneRole.SETUP, SceneRole.PAYOFF)
LONG_ROLES = (SceneRole.HOOK, SceneRole.SETUP, SceneRole.CONTENT, SceneRole.RELAUNCH, SceneRole.PAYOFF, SceneRole.CTA)
NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)
FULL_SHORT_STEPS = 4 + 1 + 4 * 6 + 8  # front, timeline, four steps per scene, music..qa, candidate, two gates, plan
SMALL_STEPS = 4 + 1 + 4 * 3 + 8


@dataclass
class Run:
    config: DryRunConfig
    report: dict[str, Any]

    @property
    def folder(self) -> Path:
        return self.config.out_dir / self.config.channel.id / self.config.format.value

    @property
    def database(self) -> Path:
        return self.config.out_dir / "state" / "studio.db"

    def manifest(self) -> dict[str, Any]:
        loaded: dict[str, Any] = json.loads((self.folder / "manifest.json").read_text(encoding="utf-8"))
        return loaded

    def decisions(self) -> SqlDecisionStore:
        return SqlDecisionStore(make_engine(f"sqlite:///{self.database}"))

    def store(self) -> LocalArtifactStore:
        return LocalArtifactStore(self.config.out_dir / "state" / "cas", make_engine(f"sqlite:///{self.database}"))

    def query(self, sql: str) -> list[tuple[Any, ...]]:
        with sqlite3.connect(self.database, timeout=10) as conn:
            return [tuple(row) for row in conn.execute(sql).fetchall()]


def config_for(out: Path, *, llm: LLMRunner | None = None, fmt: VideoFormat = VideoFormat.SHORT, **kw: Any) -> DryRunConfig:
    return DryRunConfig(channel=channel(), format=fmt, out_dir=out, llm=llm, **kw)


def small_llm(roles: tuple[SceneRole, ...] = SHORT_ROLES) -> MockStudioLLM:
    return MockStudioLLM(roles=roles)


def clone(run: Run, where: Path) -> Run:
    """A copy of a finished run's folder (SQLite files are consistent once `run_dry` has disposed its engine)."""
    target = where / "clone"
    shutil.copytree(run.config.out_dir, target)
    return Run(replace(run.config, out_dir=target), run.report)


@pytest.fixture(scope="module", autouse=True)
def offline() -> Iterator[list[str]]:
    """Any attempt to open a connection during the module's runs is recorded and refused."""
    attempts: list[str] = []

    def refuse(*args: object, **kwargs: object) -> Any:
        attempts.append(repr(args)[:120])
        raise OSError("network access is forbidden in a dry run")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, "connect", refuse)
        mp.setattr(socket.socket, "connect_ex", refuse)
        mp.setattr(socket, "getaddrinfo", refuse)
        yield attempts


@pytest.fixture(scope="module")
def short_run(media_tools: None, tmp_path_factory: pytest.TempPathFactory) -> Run:
    config = config_for(tmp_path_factory.mktemp("e2e-short"))
    return Run(config, run_dry(config))


@pytest.fixture(scope="module")
def small_run(media_tools: None, tmp_path_factory: pytest.TempPathFactory) -> Run:
    config = config_for(tmp_path_factory.mktemp("e2e-small"), llm=small_llm())
    return Run(config, run_dry(config))


def ffmpeg_loudness(path: Path) -> tuple[float, float]:
    """Integrated loudness and true peak measured straight with ffmpeg (EBU R128), not through the studio's QA."""
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stderr
    summary = out[out.rindex("Summary:") :]
    integrated = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))  # type: ignore[union-attr]
    peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))  # type: ignore[union-attr]
    return integrated, peak


def script_duration_from_the_source_of_the_mock(
    fmt: VideoFormat, roles: tuple[SceneRole, ...] | None = None
) -> tuple[float, int]:
    """Total length and scene count of the mock script, computed here from the mock's own template: an oracle that
    does not read anything the pipeline produced."""
    brief: dict[str, Any] = {"channel": {"id": "channel-a"}, "format": fmt.value, "language": "en", "seed": 0}
    idea = build_idea(brief)
    package = build_package({**brief, "idea": idea})
    doc = build_script_doc({**brief, "idea": idea, "package": package}, roles)
    return round(sum(float(s["duree_s"]) for s in doc["scenes"]), 1), len(doc["scenes"])


# ------------------------------------------------------------------ the full Short


def test_the_first_run_executes_every_step_and_leaves_nothing_waiting(short_run: Run) -> None:
    report = short_run.report
    assert report["waiting"] == [] and report["skipped"] == []
    assert report["step_count"] == len(report["executed"]) == FULL_SHORT_STEPS
    assert report["executed"][:4] == ["idea", "package", "g1", "script"] and report["executed"][-1] == "publish_plan"
    assert report["rounds"] >= 3  # the run stopped at G1, then at the compliance gate and G2, and resumed each time


def test_every_json_file_of_a_dry_run_says_mock(short_run: Run) -> None:
    report = short_run.report
    assert report["mock"] is True and report["dry_run"] is True and report["manifest_mock"] is True
    assert short_run.manifest()["mock"] is True and short_run.manifest()["dry_run"] is True
    assert report["adapters"] and all("mock" in a for a in report["adapters"])
    files = sorted(short_run.folder.glob("*.json"))
    assert [f.name for f in files] == ["costs.json", "manifest.json", "report.json", "script.scenes.json"]
    for file in files:
        data = json.loads(file.read_text(encoding="utf-8"))
        assert data["mock"] is True, file.name  # each of them, not only the report and the manifest
    assert json.loads((short_run.folder / "report.json").read_text(encoding="utf-8")) == report


def test_the_costs_file_says_its_figures_measure_mocks_and_each_entry_carries_the_flag(short_run: Run) -> None:
    costs = json.loads((short_run.folder / "costs.json").read_text(encoding="utf-8"))
    assert costs["dry_run"] is True and "never real spending" in costs["note"]
    entries = costs["entries"]
    assert entries and all(e["mock"] is True for e in entries)
    assert {e["kind"] for e in entries} >= {"gpu_seconds", "claude_calls", "claude_input_tokens", "claude_output_tokens"}
    assert all(e["run_id"] == short_run.report["run_id"] for e in entries)


def test_the_tokens_of_the_claude_calls_are_recorded_from_their_usage(short_run: Run) -> None:
    costs = short_run.report["costs"]
    assert costs["claude_calls"] == 3
    assert costs["claude_input_tokens"] > 0 and costs["claude_output_tokens"] > 0
    entries = json.loads((short_run.folder / "costs.json").read_text(encoding="utf-8"))["entries"]
    tokens = [e for e in entries if e["kind"] == "claude_input_tokens"]
    assert len(tokens) == 3 and not any(e["estimated"] for e in tokens)  # measured from the usage, not the estimate


def test_the_render_is_a_1080x1920_constant_rate_video_lasting_as_long_as_the_script(short_run: Run) -> None:
    render = Path(short_run.report["render_path"])
    info = qa.probe(render)
    assert (info.width, info.height) == (1080, 1920) and info.fps == pytest.approx(30.0) and info.has_audio
    expected, scenes = script_duration_from_the_source_of_the_mock(VideoFormat.SHORT)
    assert short_run.report["scene_count"] == scenes and info.duration_s == pytest.approx(expected, abs=0.15)
    assert short_run.report["qa_defects"] == []


def test_the_loudness_of_the_render_hits_the_platform_target(short_run: Run) -> None:
    lufs, true_peak = ffmpeg_loudness(Path(short_run.report["render_path"]))
    assert lufs == pytest.approx(-14.0, abs=1.0) and true_peak <= -1.0


def test_the_scene_document_round_trips_into_the_skill_format(short_run: Run) -> None:
    doc = json.loads((short_run.folder / "script.scenes.json").read_text(encoding="utf-8"))
    script, package = from_skill_json(doc, short_run.report["idea_id"])
    assert len(script.scenes) == short_run.report["scene_count"] == 6 and package.format is VideoFormat.SHORT


def test_every_ledger_entry_belongs_to_a_step_of_the_manifest(short_run: Run) -> None:
    keys = set(short_run.manifest()["step_keys"].values())
    entries = json.loads((short_run.folder / "costs.json").read_text(encoding="utf-8"))["entries"]
    assert {e["step_key"] for e in entries} <= keys and short_run.report["costs"]["gpu_seconds"] > 0


def test_the_delivered_render_is_a_copy_of_the_stored_artifact_not_a_link_to_it(short_run: Run) -> None:
    stored = short_run.store().get(short_run.report["render_key"]).path
    delivered = short_run.folder / "render.mp4"
    assert stored.read_bytes() == delivered.read_bytes()
    assert delivered.stat().st_ino != stored.stat().st_ino and delivered.stat().st_nlink == 1
    assert hashlib.sha256(delivered.read_bytes()).hexdigest() == short_run.report["render_key"]


def test_the_publication_plan_is_private_and_bound_to_the_render_the_channel_and_the_run(short_run: Run) -> None:
    plan = short_run.report["publication"]
    assert plan["privacy"] == "private" and plan["render_key"] == short_run.report["render_key"]
    assert plan["contains_synthetic_media"] is True and plan["external_id"] is None and plan["publish_at"] is None
    assert "AI-generated" in plan["description"]
    stored = json.loads(short_run.store().get(short_run.manifest()["locked"]["publish_plan"]).path.read_text(encoding="utf-8"))
    assert stored["run_id"] == short_run.report["run_id"] and stored["channel_id"] == "channel-a"
    assert short_run.manifest()["locked"]["publish_plan"] == short_run.report["candidate_key"]  # released byte for byte


def test_each_gate_holds_a_mock_decision_on_the_exact_artifact_it_judged(short_run: Run) -> None:
    locked = short_run.manifest()["locked"]
    decisions = short_run.decisions()
    g1 = decisions.get(GateName.G1, locked["package"])
    assert g1 is not None and g1.approved and g1.mock
    for gate in (GateName.COMPLIANCE, GateName.G2):  # both judge the candidate, not the render alone
        decision = decisions.get(gate, locked["candidate"])
        assert decision is not None and decision.approved and decision.mock
        assert decision.subject_key == short_run.report["candidate_key"]
        assert decisions.get(gate, locked["assemble"]) is None
    compliance = decisions.get(GateName.COMPLIANCE, locked["candidate"])
    assert compliance is not None and compliance.agent_verdict is Verdict.APPROVE and compliance.human_verdict is Verdict.APPROVE
    assert decisions.get(GateName.G2, locked["package"]) is None  # a decision on one artifact says nothing about another


def test_a_second_run_executes_nothing_and_writes_the_same_render(short_run: Run) -> None:
    before = (short_run.folder / "render.mp4").read_bytes()
    again = run_dry(short_run.config)
    assert again["executed"] == [] and len(again["skipped"]) == short_run.report["step_count"] and again["waiting"] == []
    assert again["render_key"] == short_run.report["render_key"]
    assert (short_run.folder / "render.mp4").read_bytes() == before
    assert again["costs"] == short_run.report["costs"]  # nothing ran, nothing was charged


# ------------------------------------------------------------------ the long format


def test_the_long_format_renders_1920x1080_lasting_as_long_as_its_script_at_the_platform_loudness(
    media_tools: None, tmp_path: Path
) -> None:
    config = config_for(tmp_path, llm=small_llm(LONG_ROLES), fmt=VideoFormat.LONG)
    report = run_dry(config)
    render = Path(report["render_path"])
    info = qa.probe(render)
    expected, scenes = script_duration_from_the_source_of_the_mock(VideoFormat.LONG, LONG_ROLES)
    assert (info.width, info.height) == (1920, 1080) and info.fps == pytest.approx(30.0) and info.has_audio
    assert report["scene_count"] == scenes == 6 and info.duration_s == pytest.approx(expected, abs=0.15)
    lufs, true_peak = ffmpeg_loudness(render)
    assert lufs == pytest.approx(-14.0, abs=1.0) and true_peak <= -1.0
    assert report["qa_defects"] == [] and report["mock"] is True


# ------------------------------------------------------------------ local edits recompute locally, keys are reproducible


def test_editing_the_words_of_one_scene_recomputes_one_voice_and_no_shot(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    assert small_run.report["step_count"] == SMALL_STEPS

    (where.folder / "manifest.json").unlink()  # a new revision of the video: its outputs are not locked yet
    edited = run_dry(config_for(where.config.out_dir, llm=EditedNarrationLLM(1, small_llm())))

    # The script changed, so the cheap extraction steps run again; their outputs are identical, so nothing that
    # depends on them but the edited scene does (early cutoff: a step key follows the content of its inputs).
    assert {"line_S02", "voice_S02"} <= set(edited["executed"])
    untouched = ("shot_", "voice_S01", "voice_S03", "music")
    assert not [s for s in edited["executed"] if s.startswith(untouched)], edited["executed"]
    assert {"mix", "assemble", "qa", "candidate", "compliance", "g2", "publish_plan"} <= set(edited["executed"])
    assert edited["render_key"] != small_run.report["render_key"]
    extra_gpu = edited["costs"]["gpu_seconds"] - small_run.report["costs"]["gpu_seconds"]
    assert 0 < extra_gpu < 5  # one voice; the shots alone had cost hundreds of GPU seconds


def test_two_fresh_runs_of_the_same_video_give_the_same_keys_and_the_same_bytes(small_run: Run, tmp_path: Path) -> None:
    config = config_for(tmp_path / "again", llm=small_llm())
    again = Run(config, run_dry(config))
    assert again.report["render_key"] == small_run.report["render_key"]
    assert again.report["candidate_key"] == small_run.report["candidate_key"]
    assert again.manifest()["step_keys"] == small_run.manifest()["step_keys"]  # the keys downstream of a gate included
    assert again.manifest()["locked"] == small_run.manifest()["locked"]
    assert (again.folder / "render.mp4").read_bytes() == (small_run.folder / "render.mp4").read_bytes()


# ------------------------------------------------------------------ what the publication gates judge (critic B1)


def test_a_title_or_a_disclosure_changed_after_the_approvals_needs_new_approvals(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    (where.folder / "manifest.json").unlink()  # a new revision of the video
    asked: list[str] = []

    class Watching(RejectingReviewer):
        def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
            asked.append(gate.value)
            return super().decide(gate, subject_key, now)

    revised = run_dry(config_for(where.config.out_dir, llm=NoDisclosureLLM(small_llm()), reviewer=Watching(GateName.G1)))

    assert revised["render_key"] == small_run.report["render_key"]  # the render is byte for byte the approved one
    assert revised["publication"]["contains_synthetic_media"] is False  # ... yet the publication is another
    assert revised["candidate_key"] != small_run.report["candidate_key"]
    assert asked == ["compliance", "g2"]  # so the compliance verdict and the human were asked again, on the new candidate
    previous = where.decisions().get(GateName.G2, small_run.report["candidate_key"])
    assert previous is not None and previous.approved  # the approvals of the first candidate stay what they were


# ------------------------------------------------------------------ integrity of what was approved (critic I6)


def test_a_revoked_approval_stops_the_replay_with_a_rejection_and_leaves_no_report(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    candidate = where.manifest()["locked"]["candidate"]
    where.decisions().put(
        GateDecision(
            gate=GateName.G2,
            subject_key=candidate,
            agent_verdict=Verdict.APPROVE,
            human_verdict=Verdict.REJECT,
            human_note="watched it again: no",
            mock=True,
        )
    )
    with pytest.raises(GateRejected) as raised:
        run_dry(where.config)
    assert raised.value.gate == "g2" and "watched it again" in raised.value.reason
    locked = where.manifest()["locked"]
    assert "g2" not in locked and "publish_plan" not in locked  # the lock of a revoked gate is dropped, and the plan's
    assert not (where.folder / "report.json").exists()  # the report of the earlier success is not left to mislead


def test_a_stored_render_rotted_in_place_is_never_delivered(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    key = where.report["render_key"]
    stored = where.store().get(key).path
    data = bytearray(stored.read_bytes())
    for i in range(len(data) // 2, len(data) // 2 + 64):
        data[i] ^= 0xFF  # same size, other bytes
    stored.write_bytes(bytes(data))
    (where.folder / "render.mp4").unlink()
    with pytest.raises(StudioError, match="is corrupt: its bytes hash to"):
        run_dry(where.config)
    assert not (where.folder / "render.mp4").exists() and not (where.folder / "report.json").exists()


def test_a_manifest_edited_to_lock_another_render_is_refused(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    other = where.store().put_bytes(b"another video's render", kind="video", media_type="video/mp4").key
    manifest = where.manifest()
    manifest["locked"]["assemble"] = other
    (where.folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ManifestMismatch, match="locks step 'assemble'"):
        run_dry(where.config)


# ------------------------------------------------------------------ a killed process resumes (critic I3)


TESTS_DIR = Path(__file__).resolve().parents[1]
KILLED_RUN = """
import sys
from pathlib import Path
sys.path.insert(0, {tests!r})
from pipeline_fakes import channel
from studio.domain import SceneRole, VideoFormat
from studio.pipeline.driver import DryRunConfig, run_dry
from studio.pipeline.mock_agents import MockStudioLLM
roles = (SceneRole.HOOK, SceneRole.SETUP, SceneRole.PAYOFF)
run_dry(DryRunConfig(channel=channel(), format=VideoFormat.SHORT, out_dir=Path({out!r}), llm=MockStudioLLM(roles=roles)))
"""


def launch(out: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", KILLED_RUN.format(tests=str(TESTS_DIR), out=str(out))],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def scalar(database: Path, sql: str) -> int:
    try:
        with sqlite3.connect(database, timeout=5) as conn:
            return int(conn.execute(sql).fetchone()[0])
    except (sqlite3.Error, TypeError):  # the file or the table does not exist yet
        return 0


def kill_when(child: subprocess.Popen[str], database: Path, sql: str, at_least: int) -> int:
    """SIGKILL `child` as soon as `sql` counts `at_least` rows; return that count."""
    deadline = time.monotonic() + 120
    while child.poll() is None and time.monotonic() < deadline:
        if scalar(database, sql) >= at_least:
            break
        time.sleep(0.02)
    assert child.poll() is None, f"the run ended before the kill: {child.communicate()}"
    child.send_signal(signal.SIGKILL)  # no finally block, no cleanup
    child.communicate()
    return scalar(database, sql)


def test_a_process_killed_in_the_middle_of_a_run_resumes_without_redoing_finished_steps(
    media_tools: None, tmp_path: Path
) -> None:
    database = tmp_path / "state" / "studio.db"
    child = launch(tmp_path)
    finished_before_the_kill = kill_when(child, database, "select count(*) from step_outputs", 14)
    assert 14 <= finished_before_the_kill < SMALL_STEPS

    report = run_dry(config_for(tmp_path, llm=small_llm()))
    assert report["waiting"] == [] and report["qa_defects"] == []
    assert len(report["skipped"]) >= finished_before_the_kill - 3  # the gates leave no output of their own
    assert len(report["executed"]) + len(report["skipped"]) == report["step_count"] == SMALL_STEPS
    assert 0 < len(report["executed"]) < report["step_count"]  # something was left to do, and not everything
    expected, _ = script_duration_from_the_source_of_the_mock(VideoFormat.SHORT, SHORT_ROLES)
    assert qa.probe(Path(report["render_path"])).duration_s == pytest.approx(expected, abs=0.15)

    objects = [f for f in (tmp_path / "state" / "cas").rglob("*") if f.is_file() and len(f.name) == 64]
    assert objects
    for obj in objects:  # the kill left no half-written object under a content address
        assert hashlib.sha256(obj.read_bytes()).hexdigest() == obj.name


def test_repeated_kills_during_gpu_steps_leave_no_reservation_and_the_video_still_finishes(
    media_tools: None, tmp_path: Path
) -> None:
    database = tmp_path / "state" / "studio.db"
    active = "select count(*) from reservations where status = 'active'"
    active_gpu = "select count(*) from reservations where status = 'active' and kind = 'gpu_seconds'"
    for _ in range(3):  # a crash loop: every attempt dies right after a step reserved its GPU budget
        kill_when(launch(tmp_path), database, active_gpu, 1)
    assert scalar(database, active_gpu) >= 1  # the killed attempts did leave their reservations behind
    leftover = tmp_path / "state" / "tmp" / "studio-step-dead"  # what a step killed mid-work leaves in its scratch folder
    leftover.mkdir(parents=True)
    (leftover / "half.mp4").write_bytes(b"\x00" * 64)

    report = run_dry(config_for(tmp_path, llm=small_llm()))  # the next process owns the folder: it frees them
    assert report["waiting"] == [] and report["qa_defects"] == []
    assert scalar(database, active) == 0
    assert not leftover.exists()  # ... and it removes the scratch files of the dead


# ------------------------------------------------------------------ one process at a time (critic I7)


def test_a_second_run_on_a_folder_another_process_owns_is_refused_not_run_in_parallel(media_tools: None, tmp_path: Path) -> None:
    database = tmp_path / "state" / "studio.db"
    child = launch(tmp_path)
    try:
        deadline = time.monotonic() + 60
        while scalar(database, "select count(*) from step_outputs") < 1 and time.monotonic() < deadline:
            time.sleep(0.02)
        with pytest.raises(StateBusy, match="another studio run is using"):
            run_dry(config_for(tmp_path, llm=small_llm()))
    finally:
        child.send_signal(signal.SIGKILL)
        child.communicate()
    # once its owner is gone, the folder is free again (the kernel released the lock with the process)
    assert run_dry(config_for(tmp_path, llm=small_llm()))["waiting"] == []


# ------------------------------------------------------------------ gates, quota and manifests


def test_a_rejection_at_g1_stops_the_run_before_the_script(media_tools: None, tmp_path: Path) -> None:
    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(tmp_path, reviewer=RejectingReviewer(GateName.G1)))
    assert raised.value.gate == "g1" and raised.value.step == "g1"
    locked = json.loads((tmp_path / "channel-a" / "short" / "manifest.json").read_text(encoding="utf-8"))["locked"]
    assert set(locked) == {"idea", "package"}  # what was resolved is kept, nothing after the gate ran
    assert not (tmp_path / "channel-a" / "short" / "report.json").exists()


def test_the_compliance_officer_blocks_a_script_with_an_open_loop_and_no_human_is_asked_at_g2(
    media_tools: None, tmp_path: Path
) -> None:
    llm = MockStudioLLM(roles=(SceneRole.HOOK, SceneRole.CONTENT))  # opens Q1 and never closes it
    asked: list[str] = []

    class Watching(RejectingReviewer):
        def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
            asked.append(gate.value)
            return super().decide(gate, subject_key, now)

    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(tmp_path, llm=llm, reviewer=Watching(GateName.COMPLIANCE)))
    assert raised.value.gate == "compliance" and "never closed" in raised.value.reason
    assert asked == ["g1"]  # the human answered G1, and was asked neither for the compliance half nor for G2
    folder = tmp_path / "channel-a" / "short"
    locked = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["locked"]
    assert "candidate" in locked and "publish_plan" not in locked and "g2" not in locked
    database = tmp_path / "state" / "studio.db"
    assert scalar(database, "select count(*) from gate_decisions where gate = 'g2'") == 0  # G2 was never put to anyone
    assert not (folder / "report.json").exists()


def test_a_human_rejection_at_g2_also_stops_publication(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    (where.folder / "manifest.json").unlink()
    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(where.config.out_dir, llm=EditedNarrationLLM(1, small_llm()), reviewer=RejectingReviewer(GateName.G2)))
    assert raised.value.gate == "g2"
    locked = where.manifest()["locked"]
    assert "candidate" in locked and "g2" not in locked and "publish_plan" not in locked


def test_a_human_rejection_of_the_compliance_half_blocks_even_when_the_agent_approved(small_run: Run, tmp_path: Path) -> None:
    where = clone(small_run, tmp_path)
    (where.folder / "manifest.json").unlink()
    with pytest.raises(GateRejected) as raised:
        run_dry(
            config_for(
                where.config.out_dir, llm=EditedNarrationLLM(1, small_llm()), reviewer=RejectingReviewer(GateName.COMPLIANCE)
            )
        )
    assert raised.value.gate == "compliance" and "refused" in raised.value.reason  # the agent approved, the human did not
    assert "publish_plan" not in where.manifest()["locked"]


def test_the_usage_limit_pauses_the_run_and_a_later_run_resumes_it(media_tools: None, tmp_path: Path) -> None:
    llm = QuotaAtAgentLLM("packaging_director", reset_at=NOON + dt.timedelta(hours=3), inner=small_llm())
    with pytest.raises(RunPaused) as paused:
        run_dry(config_for(tmp_path, llm=llm), clock=lambda: NOON)
    assert paused.value.resume_at == NOON + dt.timedelta(hours=3)
    kept = RunManifest.model_validate_json((tmp_path / "channel-a" / "short" / "manifest.json").read_text(encoding="utf-8"))
    assert set(kept.locked) == {"idea"}  # the call that succeeded before the limit is kept

    llm.exhausted = False  # the limit reset
    report = run_dry(config_for(tmp_path, llm=llm), clock=lambda: NOON + dt.timedelta(hours=3, minutes=1))
    assert "idea" in report["skipped"] and "idea" not in report["executed"]
    assert {"package", "script", "publish_plan"} <= set(report["executed"])
    assert report["costs"]["claude_calls"] == 4  # three answers, plus the attempt the limit refused: it counts against the cap


def test_a_manifest_of_another_run_is_refused_not_overwritten(tmp_path: Path) -> None:
    folder = tmp_path / "channel-a" / "short"
    folder.mkdir(parents=True)
    other = RunManifest(run_id="another-run", channel_id="channel-a", format=VideoFormat.SHORT, dry_run=True, mock=True)
    (folder / "manifest.json").write_text(other.canonical_json(), encoding="utf-8")
    with pytest.raises(StudioError, match="belongs to run 'another-run'"):
        run_dry(config_for(tmp_path))
    assert json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["run_id"] == "another-run"


def test_a_corrupt_manifest_is_reported_as_such(tmp_path: Path) -> None:
    folder = tmp_path / "channel-a" / "short"
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(StudioError, match="not a valid run manifest"):
        run_dry(config_for(tmp_path))


def test_a_status_line_names_the_run_id_derived_from_channel_format_and_seed() -> None:
    assert config_for(Path("."), seed=7).effective_run_id == "dry-channel-a-short-7"
    assert config_for(Path("."), run_id="mine").effective_run_id == "mine"


# ------------------------------------------------------------------ last: it covers every run of the module


def test_no_network_connection_was_attempted(offline: list[str]) -> None:
    assert offline == []
