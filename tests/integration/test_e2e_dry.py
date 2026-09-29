"""The dry run end to end: one video through every step with mock adapters (MISSION §9, phase 1 exit criteria).

The full Short is produced once for the module (about 30 s); the scenarios that need a second video use a three-scene
script (hook, set-up, pay-off) so that each stays around ten seconds.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import socket
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pipeline_fakes import EditedNarrationLLM, QuotaAtAgentLLM, RejectingReviewer, channel

from studio.adapters.llm_base import LLMRunner
from studio.core.artifacts import LocalArtifactStore
from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.interfaces import StudioError
from studio.domain import GateName, RunManifest, SceneRole, VideoFormat
from studio.media import qa
from studio.pipeline.driver import DryRunConfig, GateRejected, RunPaused, run_dry
from studio.pipeline.mock_agents import MockStudioLLM
from studio.scenario.skill_json import from_skill_json

pytestmark = pytest.mark.media

SHORT_ROLES = (SceneRole.HOOK, SceneRole.SETUP, SceneRole.PAYOFF)
NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)


@dataclass
class Run:
    config: DryRunConfig
    report: dict[str, Any]

    @property
    def folder(self) -> Path:
        return self.config.out_dir / self.config.channel.id / self.config.format.value

    def manifest(self) -> dict[str, Any]:
        loaded: dict[str, Any] = json.loads((self.folder / "manifest.json").read_text(encoding="utf-8"))
        return loaded


def config_for(out: Path, *, llm: LLMRunner | None = None, fmt: VideoFormat = VideoFormat.SHORT, **kw: Any) -> DryRunConfig:
    return DryRunConfig(channel=channel(), format=fmt, out_dir=out, llm=llm, **kw)


def small_llm() -> MockStudioLLM:
    return MockStudioLLM(roles=SHORT_ROLES)


@pytest.fixture(scope="module")
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
def short_run(media_tools: None, offline: list[str], tmp_path_factory: pytest.TempPathFactory) -> Run:
    config = config_for(tmp_path_factory.mktemp("e2e-short"))
    return Run(config, run_dry(config))


# ------------------------------------------------------------------ the full Short


def test_the_first_run_executes_every_step_and_leaves_nothing_waiting(short_run: Run) -> None:
    report = short_run.report
    assert report["waiting"] == [] and report["skipped"] == []
    assert report["step_count"] == len(report["executed"]) == 4 + 1 + 4 * 6 + 7
    assert report["executed"][:4] == ["idea", "package", "g1", "script"] and report["executed"][-1] == "publish_plan"
    assert report["rounds"] >= 3  # the run stopped at G1, then at the compliance gate and G2, and resumed each time


def test_report_and_manifest_carry_the_word_mock(short_run: Run) -> None:
    report = short_run.report
    assert report["mock"] is True and report["dry_run"] is True and report["manifest_mock"] is True
    assert short_run.manifest()["mock"] is True and short_run.manifest()["dry_run"] is True
    assert report["adapters"] and all("mock" in a for a in report["adapters"])
    assert json.loads((short_run.folder / "report.json").read_text(encoding="utf-8")) == report


def test_the_render_is_a_1080x1920_constant_rate_video_of_the_expected_length(short_run: Run) -> None:
    info = qa.probe(Path(short_run.report["render_path"]))
    assert (info.width, info.height) == (1080, 1920) and info.fps == pytest.approx(30.0) and info.has_audio
    assert info.duration_s == pytest.approx(short_run.report["duration_expected_s"], abs=0.1)
    assert short_run.report["qa_defects"] == []


def test_the_loudness_of_the_render_hits_the_platform_target(short_run: Run) -> None:
    lufs, true_peak = qa.loudness(Path(short_run.report["render_path"]))
    assert lufs == pytest.approx(-14.0, abs=1.0) and true_peak <= -1.0


def test_the_outputs_for_people_are_written(short_run: Run) -> None:
    assert (short_run.folder / "render.mp4").stat().st_size > 10_000
    costs = json.loads((short_run.folder / "costs.json").read_text(encoding="utf-8"))
    assert {e["kind"] for e in costs} >= {"gpu_seconds", "claude_calls"}
    assert all(e["run_id"] == short_run.report["run_id"] for e in costs)
    doc = json.loads((short_run.folder / "script.scenes.json").read_text(encoding="utf-8"))
    script, package = from_skill_json(doc, short_run.report["idea_id"])
    assert len(script.scenes) == short_run.report["scene_count"] == 6 and package.format is VideoFormat.SHORT


def test_every_ledger_entry_belongs_to_a_step_of_the_manifest(short_run: Run) -> None:
    keys = set(short_run.manifest()["step_keys"].values())
    costs = json.loads((short_run.folder / "costs.json").read_text(encoding="utf-8"))
    assert costs and {e["step_key"] for e in costs} <= keys
    assert short_run.report["costs"]["gpu_seconds"] > 0 and short_run.report["costs"]["claude_calls"] == 3


def test_the_delivered_render_is_a_copy_of_the_stored_artifact_not_a_link_to_it(short_run: Run) -> None:
    store = LocalArtifactStore(
        short_run.config.out_dir / "state" / "cas", make_engine(f"sqlite:///{short_run.config.out_dir / 'state' / 'studio.db'}")
    )
    stored = store.get(short_run.report["render_key"]).path
    delivered = short_run.folder / "render.mp4"
    assert stored.read_bytes() == delivered.read_bytes()
    assert delivered.stat().st_ino != stored.stat().st_ino and delivered.stat().st_nlink == 1


def test_the_publication_plan_is_private_and_bound_to_the_render(short_run: Run) -> None:
    plan = short_run.report["publication"]
    assert plan["privacy"] == "private" and plan["render_key"] == short_run.report["render_key"]
    assert plan["contains_synthetic_media"] is True and plan["external_id"] is None and plan["publish_at"] is None
    assert "AI-generated" in plan["description"]


def test_each_gate_holds_a_decision_on_the_exact_artifact_it_judged(short_run: Run) -> None:
    locked = short_run.manifest()["locked"]
    decisions = SqlDecisionStore(make_engine(f"sqlite:///{short_run.config.out_dir / 'state' / 'studio.db'}"))
    assert decisions.get(GateName.G1, locked["package"]).approved  # type: ignore[union-attr]
    for gate in (GateName.COMPLIANCE, GateName.G2):
        decision = decisions.get(gate, locked["assemble"])
        assert decision is not None and decision.approved and decision.subject_key == short_run.report["render_key"]
    assert decisions.get(GateName.G2, locked["package"]) is None  # a decision on one artifact says nothing about another


def test_no_network_connection_was_attempted(short_run: Run, offline: list[str]) -> None:
    assert offline == []


def test_a_second_run_executes_nothing_and_writes_the_same_render(short_run: Run) -> None:
    before = (short_run.folder / "render.mp4").read_bytes()
    again = run_dry(short_run.config)
    assert again["executed"] == [] and len(again["skipped"]) == short_run.report["step_count"] and again["waiting"] == []
    assert again["render_key"] == short_run.report["render_key"]
    assert (short_run.folder / "render.mp4").read_bytes() == before
    assert again["costs"] == short_run.report["costs"]  # nothing ran, nothing was charged


# ------------------------------------------------------------------ local edits recompute locally


def test_editing_the_words_of_one_scene_recomputes_one_voice_and_no_shot(media_tools: None, tmp_path: Path) -> None:
    config = config_for(tmp_path, llm=small_llm())
    base = Run(config, run_dry(config))
    assert base.report["step_count"] == 4 + 1 + 4 * 3 + 7

    (base.folder / "manifest.json").unlink()  # a new revision of the video: its outputs are not locked yet
    edited = run_dry(config_for(tmp_path, llm=EditedNarrationLLM(1, small_llm())))

    # The script changed, so the cheap extraction steps run again; their outputs are identical, so nothing that
    # depends on them but the edited scene does (early cutoff: a step key follows the content of its inputs).
    assert {"line_S02", "voice_S02"} <= set(edited["executed"])
    untouched = ("shot_", "voice_S01", "voice_S03", "music")
    assert not [s for s in edited["executed"] if s.startswith(untouched)], edited["executed"]
    assert {"mix", "assemble", "qa", "compliance", "g2", "publish_plan"} <= set(edited["executed"])
    assert edited["render_key"] != base.report["render_key"]
    extra_gpu = edited["costs"]["gpu_seconds"] - base.report["costs"]["gpu_seconds"]
    assert 0 < extra_gpu < 5  # one voice; the shots alone had cost hundreds of GPU seconds


# ------------------------------------------------------------------ a killed process resumes


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


def committed_steps(database: Path) -> int:
    try:
        with sqlite3.connect(database, timeout=5) as conn:
            return int(conn.execute("select count(*) from step_outputs").fetchone()[0])
    except sqlite3.Error:  # the file or the table does not exist yet
        return 0


def test_a_process_killed_in_the_middle_of_a_run_resumes_without_redoing_finished_steps(
    media_tools: None, tmp_path: Path
) -> None:
    database = tmp_path / "state" / "studio.db"
    child = subprocess.Popen(
        [sys.executable, "-c", KILLED_RUN.format(tests=str(TESTS_DIR), out=str(tmp_path))],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 120
        while committed_steps(database) < 14 and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert child.poll() is None, f"the run ended before the kill: {child.communicate()}"
        child.kill()  # SIGKILL: no finally block, no cleanup, whatever step was running is abandoned
    finally:
        child.kill()
        child.communicate()
    finished_before_the_kill = committed_steps(database)
    assert 14 <= finished_before_the_kill < 24

    report = run_dry(config_for(tmp_path, llm=small_llm()))
    assert report["waiting"] == [] and report["qa_defects"] == []
    assert len(report["skipped"]) >= finished_before_the_kill - 3  # the gates leave no output of their own
    assert len(report["executed"]) + len(report["skipped"]) == report["step_count"] == 24
    assert 0 < len(report["executed"]) < report["step_count"]  # something was left to do, and not everything
    assert qa.probe(Path(report["render_path"])).duration_s == pytest.approx(report["duration_expected_s"], abs=0.1)

    cas = tmp_path / "state" / "cas"
    objects = [f for f in cas.rglob("*") if f.is_file() and len(f.name) == 64]
    assert objects
    for obj in objects:  # the kill left no half-written object under a content address
        assert hashlib.sha256(obj.read_bytes()).hexdigest() == obj.name


# ------------------------------------------------------------------ gates, quota and manifests


def test_a_rejection_at_g1_stops_the_run_before_the_script(media_tools: None, tmp_path: Path) -> None:
    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(tmp_path, reviewer=RejectingReviewer(GateName.G1)))
    assert raised.value.gate == "g1" and raised.value.step == "g1"
    locked = json.loads((tmp_path / "channel-a" / "short" / "manifest.json").read_text(encoding="utf-8"))["locked"]
    assert set(locked) == {"idea", "package"}  # what was resolved is kept, nothing after the gate ran
    assert not (tmp_path / "channel-a" / "short" / "report.json").exists()


def test_the_compliance_officer_blocks_publication_of_a_script_with_an_open_loop(media_tools: None, tmp_path: Path) -> None:
    llm = MockStudioLLM(roles=(SceneRole.HOOK, SceneRole.CONTENT))  # opens Q1 and never closes it
    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(tmp_path, llm=llm))
    assert raised.value.gate == "compliance" and "never closed" in raised.value.reason
    locked = json.loads((tmp_path / "channel-a" / "short" / "manifest.json").read_text(encoding="utf-8"))["locked"]
    assert "assemble" in locked and "publish_plan" not in locked and "g2" not in locked
    assert not (tmp_path / "channel-a" / "short" / "report.json").exists()


def test_a_human_rejection_at_g2_also_stops_publication(media_tools: None, tmp_path: Path) -> None:
    with pytest.raises(GateRejected) as raised:
        run_dry(config_for(tmp_path, llm=small_llm(), reviewer=RejectingReviewer(GateName.G2)))
    assert raised.value.gate == "g2"
    locked = json.loads((tmp_path / "channel-a" / "short" / "manifest.json").read_text(encoding="utf-8"))["locked"]
    assert "assemble" in locked and "g2" not in locked and "publish_plan" not in locked


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
