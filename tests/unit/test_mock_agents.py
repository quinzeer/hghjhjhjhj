"""Mock agents of the dry run: templates that satisfy the contracts, deterministic, honest about being mocks."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest

from studio.adapters.llm_base import LLMOutputInvalid
from studio.domain import (
    GateName,
    Idea,
    Package,
    SceneRole,
    Script,
    ShotTechnique,
    Verdict,
    VideoFormat,
    canonical_json,
)
from studio.pipeline import mock_agents
from studio.pipeline.mock_agents import (
    MockComplianceOfficer,
    MockProceduralRenderer,
    MockReviewer,
    MockStudioLLM,
    build_idea,
    build_package,
    build_script_doc,
    choose_technique,
    scene_duration,
)
from studio.scenario.skill_json import from_skill_json

NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)
RENDER = "c" * 64


def brief(channel: str = "channel-a", fmt: VideoFormat = VideoFormat.SHORT) -> dict[str, Any]:
    return {"channel": {"id": channel, "language": "en", "concept": "c"}, "format": fmt.value, "language": "en", "seed": 0}


def pipeline_docs(channel: str, fmt: VideoFormat, roles: tuple[SceneRole, ...] | None = None) -> tuple[Idea, Package, Script]:
    b = brief(channel, fmt)
    idea = build_idea(b)
    package = build_package({**b, "idea": idea})
    script, _ = from_skill_json(build_script_doc({**b, "idea": idea, "package": package}, roles), idea["id"])
    return Idea.model_validate(idea), Package.model_validate(package), script


def run_llm(llm: MockStudioLLM, agent: str, payload: dict[str, Any], schema: dict[str, Any] | None = None) -> Any:
    return llm.run(
        agent=agent,
        prompt=canonical_json(payload),
        model="opus",
        json_schema=schema,
        max_turns=1,
        allowed_tools=(),
        cwd=Path("."),
    )


# ------------------------------------------------------------------ the templates satisfy the contracts


@pytest.mark.parametrize("channel", ["channel-a", "channel-b", "any-other-channel"])
@pytest.mark.parametrize("fmt", [VideoFormat.SHORT, VideoFormat.LONG])
def test_every_template_validates_against_its_contract(channel: str, fmt: VideoFormat) -> None:
    idea, package, script = pipeline_docs(channel, fmt)
    assert idea.channel_id == channel
    assert package.idea_id == idea.id and package.format is fmt
    assert script.format is fmt and script.idea_id == idea.id
    assert script.titles == package.titles and script.first_frame == package.first_frame
    assert bool(package.thumbnails) is (fmt is VideoFormat.LONG)


@pytest.mark.parametrize("fmt", [VideoFormat.SHORT, VideoFormat.LONG])
def test_a_scene_sequence_ends_with_no_loop_left_open(fmt: VideoFormat) -> None:
    _, _, script = pipeline_docs("channel-a", fmt)
    assert script.open_loops() == set()
    assert script.scenes[0].role is SceneRole.HOOK


def test_the_long_format_has_more_scenes_and_lasts_longer_than_the_short() -> None:
    short, long = pipeline_docs("channel-a", VideoFormat.SHORT)[2], pipeline_docs("channel-a", VideoFormat.LONG)[2]
    assert len(long.scenes) > len(short.scenes) and long.duration_s > short.duration_s


def test_scenes_are_contiguous_and_last_a_whole_number_of_frames_at_30_fps() -> None:
    _, _, script = pipeline_docs("channel-a", VideoFormat.LONG)
    for scene in script.scenes:
        assert scene.duration_s * 30 == pytest.approx(round(scene.duration_s * 30), abs=1e-6)
    assert script.scenes[0].start_s == 0


def test_each_channel_speaks_of_its_own_concept() -> None:
    a = build_idea(brief("channel-a"))
    b = build_idea(brief("channel-b"))
    assert "aqueduct" in a["promise"] and "billion years" in b["promise"]
    assert a["id"] != b["id"]


def test_an_unknown_channel_gets_a_stable_topic() -> None:
    assert build_idea(brief("channel-zzz")) == build_idea(brief("channel-zzz"))


def test_configured_roles_shorten_the_script() -> None:
    roles = (SceneRole.HOOK, SceneRole.PAYOFF)
    _, _, script = pipeline_docs("channel-a", VideoFormat.SHORT, roles)
    assert [s.role for s in script.scenes] == list(roles)
    assert script.open_loops() == set()


def test_a_script_that_opens_a_loop_and_never_closes_it_is_detected() -> None:
    _, _, script = pipeline_docs("channel-a", VideoFormat.SHORT, (SceneRole.HOOK, SceneRole.CONTENT))
    assert script.open_loops() == {"Q1"}


def test_scene_duration_rounds_up_to_a_tenth_of_a_second() -> None:
    assert scene_duration("") == pytest.approx(mock_agents.SCENE_TAIL_S)
    assert scene_duration("one two three four") == pytest.approx(1.9)  # 4 words at 160 wpm = 1.5 s, + 0.4 s tail
    assert scene_duration("word " * 40) > scene_duration("word " * 20)
    assert scene_duration("word", words_per_minute=30) > scene_duration("word", words_per_minute=60)


def test_the_technique_policy_cycles_through_the_whole_grammar() -> None:
    _, _, script = pipeline_docs("channel-a", VideoFormat.LONG)
    seen = {choose_technique(scene, i) for i, scene in enumerate(script.scenes)}
    assert seen == {ShotTechnique.BLENDER, ShotTechnique.IMAGE_25D, ShotTechnique.GEN_VIDEO, ShotTechnique.MOTION}


# ------------------------------------------------------------------ the mock LLM


def test_the_mock_llm_says_mock_and_records_its_calls() -> None:
    llm = MockStudioLLM()
    assert "mock" in llm.spec.id and llm.spec.is_mock is True
    result = run_llm(llm, "strategist", brief())
    assert result.usage.model == llm.spec.id and result.raw["mock"] is True and "mock" in result.session_id
    assert llm.calls and llm.calls[0]["agent"] == "strategist" and llm.calls[0]["model"] == "opus"


def test_the_mock_llm_is_deterministic() -> None:
    a, b = MockStudioLLM(), MockStudioLLM()
    assert run_llm(a, "strategist", brief()).output == run_llm(b, "strategist", brief()).output
    assert run_llm(a, "strategist", brief()).session_id == run_llm(b, "strategist", brief()).session_id


def test_the_mock_llm_id_tells_which_script_shape_it_produces() -> None:
    default = MockStudioLLM()
    short = MockStudioLLM(roles=(SceneRole.HOOK, SceneRole.PAYOFF))
    other = MockStudioLLM(roles=(SceneRole.HOOK, SceneRole.CONTENT, SceneRole.PAYOFF))
    assert len({default.spec.id, short.spec.id, other.spec.id}) == 3  # the id is part of a step's key
    assert all("mock" in m.spec.id for m in (default, short, other))


def test_the_mock_llm_refuses_an_unknown_agent() -> None:
    with pytest.raises(LLMOutputInvalid, match="no template for agent 'astrologer'"):
        run_llm(MockStudioLLM(), "astrologer", brief())


def test_the_mock_llm_refuses_a_prompt_that_is_not_a_json_brief() -> None:
    with pytest.raises(LLMOutputInvalid, match="not a JSON brief"):
        MockStudioLLM().run(
            agent="strategist", prompt="plain words", model="opus", json_schema=None, max_turns=1, allowed_tools=(), cwd=Path(".")
        )


def test_the_mock_llm_checks_its_output_against_the_requested_schema() -> None:
    llm = MockStudioLLM()
    assert run_llm(llm, "strategist", brief(), Idea.model_json_schema()).output["channel_id"] == "channel-a"
    with pytest.raises(LLMOutputInvalid, match="does not match the schema"):
        run_llm(llm, "strategist", brief(), {"type": "object", "required": ["nonexistent"]})


# ------------------------------------------------------------------ reviewers


def test_the_mock_reviewer_approves_the_exact_subject_and_says_nobody_looked() -> None:
    d = MockReviewer().decide(GateName.G2, RENDER, NOON)
    assert d.approved and d.subject_key == RENDER and d.gate is GateName.G2
    assert "mock" in d.human_note and "no human" in d.human_note


def test_the_mock_officer_approves_a_clean_script() -> None:
    _, _, script = pipeline_docs("channel-a", VideoFormat.SHORT)
    d = MockComplianceOfficer().review(script, {"defects": []}, RENDER, NOON)
    assert d.approved and d.gate is GateName.COMPLIANCE and d.subject_key == RENDER
    assert all(r.startswith("mock-compliance-officer") for r in d.agent_reasons)


def test_the_mock_officer_rejects_open_loops_and_qa_defects_and_a_blocked_script() -> None:
    _, _, open_loops = pipeline_docs("channel-a", VideoFormat.SHORT, (SceneRole.HOOK, SceneRole.CONTENT))
    d = MockComplianceOfficer().review(open_loops, {"defects": ["loudness -20 LUFS"]}, RENDER, NOON)
    assert not d.approved and d.agent_verdict is Verdict.REJECT
    text = " ".join(d.agent_reasons)
    assert "never closed" in text and "loudness" in text

    _, _, script = pipeline_docs("channel-a", VideoFormat.SHORT)
    blocked = script.model_copy(
        update={"control": script.control.model_copy(update={"publishable": False, "blocking_reasons": ("fact unchecked",)})}
    )
    assert not MockComplianceOfficer().review(blocked, {"defects": []}, RENDER, NOON).approved

    silent = script.model_copy(update={"disclosure": script.disclosure.model_copy(update={"reason": "  "})})
    assert "no reason given" in " ".join(MockComplianceOfficer().review(silent, {"defects": []}, RENDER, NOON).agent_reasons)


def test_a_human_approval_cannot_lift_the_mock_officers_rejection() -> None:
    _, _, script = pipeline_docs("channel-a", VideoFormat.SHORT, (SceneRole.HOOK, SceneRole.CONTENT))
    rejected = MockComplianceOfficer().review(script, {"defects": []}, RENDER, NOON)
    assert not rejected.model_copy(update={"human_verdict": Verdict.APPROVE}).approved


# ------------------------------------------------------------------ procedural renderer


@pytest.mark.media
def test_the_mock_renderer_writes_a_clip_of_the_requested_size(media_tools: None, tmp_path: Path) -> None:
    from studio.media import qa

    renderer = MockProceduralRenderer()
    assert "mock" in renderer.spec.id
    out = tmp_path / "clip.mp4"
    result = renderer.render("a stone arch", width=320, height=180, duration_s=1.0, fps=30, seed=3, out=out)
    info = qa.probe(out)
    assert (info.width, info.height) == (320, 180) and info.duration_s == pytest.approx(1.0, abs=0.1)
    assert result.gpu_seconds == 0.0 and result.metadata["mock"] is True
    again = tmp_path / "again.mp4"
    assert (
        renderer.render("a stone arch", width=320, height=180, duration_s=1.0, fps=30, seed=3, out=again).metadata
        == result.metadata
    )
