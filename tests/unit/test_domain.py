"""Domain contracts: strictness, structural invariants, gate semantics, stable hashing."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

from studio.core.hashing import bytes_key, file_key, step_key
from studio.domain import (
    AIDisclosure,
    ControlBlock,
    CostEntry,
    CostKind,
    GateDecision,
    GateName,
    IdeaScore,
    Package,
    Platform,
    Privacy,
    Publication,
    PublicationCandidate,
    Scene,
    SceneLoops,
    SceneRole,
    Script,
    ThumbnailConcept,
    Verdict,
    VideoFormat,
)

H = "a" * 64


def scene(i: int, start: float, dur: float, **kw: object) -> Scene:
    return Scene(id=f"S{i:02d}", role=SceneRole.CONTENT, start_s=start, duration_s=dur, **kw)


def script(scenes: tuple[Scene, ...], **kw: object) -> Script:
    base: dict[str, object] = dict(
        idea_id="idea-1",
        format=VideoFormat.SHORT,
        language="en",
        words_per_minute=160,
        promise="You will see how it was built.",
        titles=("A title",),
        disclosure=AIDisclosure(required=True, reason="realistic reconstruction"),
        control=ControlBlock(publishable=True),
        scenes=scenes,
    )
    base.update(kw)
    return Script(**base)  # type: ignore[arg-type]


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Scene(id="S01", role=SceneRole.HOOK, start_s=0, duration_s=1, colour="red")  # type: ignore[call-arg]


def test_models_are_frozen() -> None:
    s = scene(1, 0, 2)
    with pytest.raises(ValidationError):
        s.duration_s = 3  # type: ignore[misc]


def test_timeline_must_be_contiguous() -> None:
    ok = script((scene(1, 0, 2.5), scene(2, 2.5, 3)))
    assert ok.duration_s == 5.5
    with pytest.raises(ValidationError, match="contiguous"):
        script((scene(1, 0, 2.5), scene(2, 4.0, 3)))


def test_timeline_tolerance_is_not_defeated_by_float_noise() -> None:
    assert 1.05 - 1.0 > 0.05  # the raw float difference exceeds the tolerance by 4e-17
    assert script((scene(1, 0, 1.0), scene(2, 1.05, 1.0))).duration_s == 2.05
    with pytest.raises(ValidationError, match="contiguous"):
        script((scene(1, 0, 1.0), scene(2, 1.06, 1.0)))


def test_scene_ids_unique() -> None:
    with pytest.raises(ValidationError, match="unique"):
        script((scene(1, 0, 2), scene(1, 2, 2)))


def test_open_loops_are_reported() -> None:
    s = script(
        (
            scene(1, 0, 2, loops=SceneLoops(opens=("Q1", "Q2"))),
            scene(2, 2, 2, loops=SceneLoops(closes=("Q1",))),
        )
    )
    assert s.open_loops() == {"Q2"}


def test_control_block_consistency() -> None:
    with pytest.raises(ValidationError):
        ControlBlock(publishable=False)
    with pytest.raises(ValidationError):
        ControlBlock(publishable=True, blocking_reasons=("fake event",))
    assert not ControlBlock(publishable=False, blocking_reasons=("x",)).publishable


def test_idea_score_total_must_match_criteria() -> None:
    assert IdeaScore(criteria={"a": 40, "b": 38}, total=78).total == 78
    with pytest.raises(ValidationError):
        IdeaScore(criteria={"a": 40, "b": 38}, total=90)


def test_package_rules() -> None:
    thumb = ThumbnailConcept(id="A", concept="scale", elements=("pyramid",))
    Package(idea_id="i", format=VideoFormat.LONG, titles=("t",), thumbnails=(thumb,))
    with pytest.raises(ValidationError, match="thumbnail"):
        Package(idea_id="i", format=VideoFormat.LONG, titles=("t",))
    with pytest.raises(ValidationError, match="first frame"):
        Package(idea_id="i", format=VideoFormat.SHORT, titles=("t",))
    with pytest.raises(ValidationError, match="unique"):
        Package(idea_id="i", format=VideoFormat.LONG, titles=("t",), thumbnails=(thumb, thumb))


@pytest.mark.parametrize(
    ("gate", "agent", "human", "approved"),
    [
        (GateName.G2, Verdict.APPROVE, Verdict.APPROVE, True),
        (GateName.G2, Verdict.APPROVE, Verdict.PENDING, False),
        (GateName.G2, Verdict.REJECT, Verdict.APPROVE, False),
        # MISSION §11: the compliance gate records the agent's decision AND the human's, and is never automated
        (GateName.COMPLIANCE, Verdict.APPROVE, Verdict.APPROVE, True),
        (GateName.COMPLIANCE, Verdict.APPROVE, Verdict.PENDING, False),  # the agent alone does not approve
        (GateName.COMPLIANCE, Verdict.PENDING, Verdict.APPROVE, False),  # nor does the human without the agent
        (GateName.COMPLIANCE, Verdict.REJECT, Verdict.APPROVE, False),  # a human cannot lift a compliance block
        (GateName.COMPLIANCE, Verdict.APPROVE, Verdict.REJECT, False),
    ],
)
def test_gate_semantics(gate: GateName, agent: Verdict, human: Verdict, approved: bool) -> None:
    d = GateDecision(gate=gate, subject_key=H, agent_verdict=agent, human_verdict=human, decided_at=dt.datetime(2026, 9, 28))
    assert d.approved is approved


def test_a_decision_is_real_unless_a_mock_reviewer_wrote_it() -> None:
    real = GateDecision(gate=GateName.G1, subject_key=H, agent_verdict=Verdict.APPROVE, human_verdict=Verdict.APPROVE)
    assert real.mock is False
    assert real.model_copy(update={"mock": True}).content_hash() != real.content_hash()


def test_a_cost_entry_is_real_unless_it_measures_a_mock() -> None:
    kwargs: dict[str, object] = dict(run_id="r", step_key=H, kind=CostKind.GPU_SECONDS, quantity=3.0, at=dt.datetime(2026, 9, 29))
    assert CostEntry(**kwargs).mock is False  # type: ignore[arg-type]
    assert CostEntry(**kwargs, mock=True).mock is True  # type: ignore[arg-type]


def test_a_publication_candidate_changes_hash_with_anything_the_platform_will_show() -> None:
    def candidate(**changes: object) -> PublicationCandidate:
        publication = Publication(
            platform=Platform.YOUTUBE, render_key=H, title="A title", description="text", contains_synthetic_media=True
        ).model_copy(update={k: v for k, v in changes.items() if k in Publication.model_fields})
        return PublicationCandidate(
            run_id=str(changes.get("run_id", "run-1")),
            channel_id=str(changes.get("channel_id", "channel-a")),
            script_key=str(changes.get("script_key", "c" * 64)),
            qa_key=str(changes.get("qa_key", "d" * 64)),
            publication=publication,
        )

    base = candidate().content_hash()
    assert candidate().content_hash() == base
    for change in (
        {"title": "Another title"},
        {"description": "other text"},
        {"contains_synthetic_media": False},
        {"render_key": "b" * 64},
        {"privacy": Privacy.PUBLIC},
        {"run_id": "run-2"},
        {"channel_id": "channel-b"},
        {"script_key": "e" * 64},  # the judges read the script: another script, another subject
        {"qa_key": "f" * 64},  # and the QA report
    ):
        assert candidate(**change).content_hash() != base, change


def test_content_hash_is_stable_and_sensitive() -> None:
    a = scene(1, 0, 2, voice_over="Hello")
    b = scene(1, 0, 2, voice_over="Hello")
    c = scene(1, 0, 2, voice_over="Hello!")
    assert a.content_hash() == b.content_hash() != c.content_hash()
    assert len(a.content_hash()) == 64


def test_step_key_properties() -> None:
    k = step_key("render", "1", {"script": H}, {"fps": 30}, seed=1)
    assert k == step_key("render", "1", {"script": H}, {"fps": 30}, seed=1)
    assert k != step_key("render", "2", {"script": H}, {"fps": 30}, seed=1)
    assert k != step_key("render", "1", {"script": "b" * 64}, {"fps": 30}, seed=1)
    assert k != step_key("render", "1", {"script": H}, {"fps": 25}, seed=1)
    assert k != step_key("render", "1", {"script": H}, {"fps": 30}, seed=2)
    with pytest.raises(ValueError):
        step_key("", "1", {}, {})
    assert bytes_key(b"x") == bytes_key(b"x") != bytes_key(b"y")


def test_file_key_is_the_key_of_the_bytes(tmp_path: Path) -> None:
    path = tmp_path / "blob.bin"
    path.write_bytes(b"x" * 3_000_000)  # more than one read chunk
    assert file_key(path) == bytes_key(b"x" * 3_000_000)
