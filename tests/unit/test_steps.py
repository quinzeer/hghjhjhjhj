"""Shape of the dry-run graph and behaviour of its steps: cache lines, gates, publication guard, bounded regeneration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from pipeline_fakes import channel

from studio.adapters.base import CritiqueResult
from studio.adapters.mock import MockVisionCritic
from studio.core.graph import Graph
from studio.core.interfaces import StepSpec, StoredArtifact, StudioError
from studio.domain import CostKind, GateName, ResourceClass, SceneRole, Script, VideoFormat, canonical_json
from studio.pipeline import steps as steps_module
from studio.pipeline.mock_agents import MockStudioLLM, build_idea, build_package, build_script_doc
from studio.pipeline.steps import (
    FORMATS,
    MAX_SHOT_ATTEMPTS,
    Production,
    ShotRejected,
    front_steps,
    line_step_name,
    production_steps,
    shot_step_name,
    visual_step_name,
    voice_step_name,
)
from studio.scenario.skill_json import from_skill_json

SHORT_ROLES = (SceneRole.HOOK, SceneRole.SETUP, SceneRole.PAYOFF)


def production(fmt: VideoFormat = VideoFormat.SHORT, *, seed: int = 0, roles: tuple[SceneRole, ...] | None = None) -> Production:
    return Production.from_mocks(channel(), fmt, seed, MockStudioLLM(roles=roles), cwd=Path("."))


def script_of(fmt: VideoFormat = VideoFormat.SHORT, roles: tuple[SceneRole, ...] | None = None) -> Script:
    brief: dict[str, Any] = {"channel": {"id": "channel-a"}, "format": fmt.value, "language": "en", "seed": 0}
    idea = build_idea(brief)
    package = build_package({**brief, "idea": idea})
    return from_skill_json(build_script_doc({**brief, "idea": idea, "package": package}, roles), idea["id"])[0]


def by_name(steps: list[StepSpec]) -> dict[str, StepSpec]:
    return {s.name: s for s in steps}


def stored(tmp_path: Path, name: str, data: Any) -> StoredArtifact:
    path = tmp_path / name
    path.write_text(canonical_json(data), encoding="utf-8")
    return StoredArtifact(key="a" * 64, kind="json", media_type="application/json", size_bytes=path.stat().st_size, path=path)


# ------------------------------------------------------------------ the front of the graph


def test_the_front_of_the_graph_is_idea_package_g1_script() -> None:
    steps = front_steps(production())
    assert [s.name for s in steps] == ["idea", "package", "g1", "script"]
    s = by_name(steps)
    assert s["g1"].gate is GateName.G1 and s["g1"].resource is ResourceClass.HUMAN and s["g1"].inputs == ("package",)
    assert s["script"].inputs == ("idea", "package", "g1")  # the script waits for the G1 approval
    assert all(s[n].resource is ResourceClass.LLM and s[n].estimated_cost for n in ("idea", "package", "script"))
    Graph(steps)


def test_agent_steps_are_keyed_on_the_backend_the_seed_and_the_channel() -> None:
    base = by_name(front_steps(production()))
    reseeded = by_name(front_steps(production(seed=1)))
    other_backend = by_name(front_steps(production(roles=SHORT_ROLES)))
    for name in ("idea", "package", "script"):
        assert base[name].params != reseeded[name].params
        assert base[name].params != other_backend[name].params
    assert base["idea"].params["backend"] == "mock-studio-llm"
    assert base["idea"].params["brief"]["channel"]["id"] == "channel-a"


def test_a_gate_step_runs_no_code() -> None:
    gate = by_name(front_steps(production()))["g1"]
    with pytest.raises(StudioError, match="waits for a decision"):
        gate.run({}, {})


def test_the_adapter_ids_of_a_production_all_say_mock() -> None:
    ids = production().adapter_ids()
    assert len(ids) == 8 and all("mock" in i for i in ids) and ids == sorted(ids)


def test_formats_are_1080p_at_30_fps_in_both_orientations() -> None:
    assert (FORMATS[VideoFormat.SHORT].width, FORMATS[VideoFormat.SHORT].height) == (1080, 1920)
    assert (FORMATS[VideoFormat.LONG].width, FORMATS[VideoFormat.LONG].height) == (1920, 1080)
    assert {f.fps for f in FORMATS.values()} == {30}


# ------------------------------------------------------------------ the production stage (needs ffmpeg for the media fingerprint)


@pytest.mark.media
def test_the_production_stage_has_two_cache_lines_a_voice_and_a_shot_per_scene(media_tools: None) -> None:
    p, script = production(), script_of()
    steps = front_steps(p) + production_steps(p, script)
    n = len(script.scenes)
    assert len(steps) == 4 + 1 + 4 * n + 7
    graph = Graph(steps)  # unique names, known inputs, no cycle, a GPU estimate on every GPU step
    s = by_name(steps)
    for i in range(n):
        assert s[line_step_name(i)].inputs == ("script",) and s[visual_step_name(i)].inputs == ("script",)
        assert s[voice_step_name(i)].inputs == (line_step_name(i),)  # a voice depends on the words, not on the picture
        assert s[shot_step_name(i)].inputs == (visual_step_name(i),)  # a shot depends on the picture, not on the words
        assert s[voice_step_name(i)].resource is ResourceClass.GPU
    assert s["mix"].inputs == ("timeline", *(voice_step_name(i) for i in range(n)), "music")
    assert s["assemble"].inputs == ("mix", *(shot_step_name(i) for i in range(n)))
    assert graph.order[-1].name == "publish_plan"


@pytest.mark.media
def test_the_long_format_has_more_steps_than_the_short(media_tools: None) -> None:
    short = front_steps(production()) + production_steps(production(), script_of())
    long_p = production(VideoFormat.LONG)
    long = front_steps(long_p) + production_steps(long_p, script_of(VideoFormat.LONG))
    assert len(long) > len(short)
    assert by_name(long)["assemble"].params["width"] == 1920 and by_name(short)["assemble"].params["width"] == 1080


@pytest.mark.media
def test_publication_needs_the_compliance_verdict_and_g2_on_the_exact_render(media_tools: None) -> None:
    p = production()
    s = by_name(front_steps(p) + production_steps(p, script_of()))
    publish = s["publish_plan"]
    assert publish.requires_approval == ((GateName.COMPLIANCE, "assemble"), (GateName.G2, "assemble"))
    assert {"compliance", "g2", "assemble", "qa"} <= set(publish.inputs)
    assert s["compliance"].gate is GateName.COMPLIANCE and s["g2"].gate is GateName.G2
    assert s["compliance"].inputs == ("assemble",) == s["g2"].inputs  # both judge the render itself


@pytest.mark.media
def test_every_render_step_carries_the_media_fingerprint(media_tools: None) -> None:
    p = production()
    s = by_name(front_steps(p) + production_steps(p, script_of(roles=SHORT_ROLES)))
    fingerprints = {s[n].params["media"] for n in ("music", "mix", "assemble", "qa", "voice_S01", "shot_S01")}
    assert len(fingerprints) == 1 and re.fullmatch(r"[0-9a-f]{16}", fingerprints.pop())


@pytest.mark.media
def test_gpu_steps_declare_the_gpu_seconds_they_reserve(media_tools: None) -> None:
    p = production(VideoFormat.LONG)
    steps = front_steps(p) + production_steps(p, script_of(VideoFormat.LONG))
    gpu = [s for s in steps if s.resource is ResourceClass.GPU]
    assert gpu and all(s.estimated_cost.get(CostKind.GPU_SECONDS, 0) > 0 and s.model_id for s in gpu)
    assert all(CostKind.GPU_SECONDS not in s.estimated_cost for s in steps if s.resource is not ResourceClass.GPU)


@pytest.mark.media
def test_steps_are_the_same_whatever_stage_builds_them(media_tools: None) -> None:
    p, script = production(), script_of()
    front_only = by_name(front_steps(p))
    full = by_name(front_steps(p) + production_steps(p, script))
    for name, step in front_only.items():
        assert (step.version, step.inputs, step.params) == (full[name].version, full[name].inputs, full[name].params)


# ------------------------------------------------------------------ step code


class Blocking:
    """A critic that blocks the first `blocked` critiques, then lets the shot through."""

    def __init__(self, blocked: int) -> None:
        self.spec = MockVisionCritic().spec
        self.blocked, self.calls = blocked, 0

    def critique(self, frames: list[Path], shot_brief: str) -> CritiqueResult:
        self.calls += 1
        if self.calls <= self.blocked:
            return CritiqueResult(blocking=True, defects=("mock: warped hands",), regeneration_hint="again")
        return CritiqueResult(blocking=False, defects=(), regeneration_hint="")


def shot_step(critic: Any, tmp_path: Path) -> tuple[StepSpec, dict[str, StoredArtifact]]:
    import dataclasses

    p = dataclasses.replace(production(roles=SHORT_ROLES), critic=critic)
    step = by_name(front_steps(p) + production_steps(p, script_of(roles=SHORT_ROLES)))["shot_S01"]
    visual = stored(tmp_path, "visual.json", {"visual_prompt_en": "a stone arch, wide frame", "duration_s": 1.0})
    return step, {"visual_S01": visual}


@pytest.mark.media
def test_a_blocked_shot_is_regenerated_once_then_delivered(media_tools: None, tmp_path: Path) -> None:
    critic = Blocking(blocked=1)
    step, inputs = shot_step(critic, tmp_path)
    data, kind, media_type = step.run(inputs, step.params)
    assert kind == "video" and media_type == "video/mp4" and data[4:8] == b"ftyp"
    assert critic.calls == 2  # first draft blocked, the second one passed


@pytest.mark.media
def test_a_shot_the_critic_keeps_blocking_fails_after_a_bounded_number_of_attempts(media_tools: None, tmp_path: Path) -> None:
    critic = Blocking(blocked=99)
    step, inputs = shot_step(critic, tmp_path)
    with pytest.raises(ShotRejected, match="warped hands"):
        step.run(inputs, step.params)
    assert critic.calls == MAX_SHOT_ATTEMPTS == steps_module.MAX_SHOT_ATTEMPTS
