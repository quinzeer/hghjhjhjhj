"""Domain contracts: strictness, structural invariants, gate semantics, stable hashing."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from studio.core.hashing import bytes_key, step_key
from studio.domain import (
    AIDisclosure,
    ControlBlock,
    GateDecision,
    GateName,
    IdeaScore,
    Package,
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
        (GateName.COMPLIANCE, Verdict.APPROVE, Verdict.PENDING, True),
        (GateName.COMPLIANCE, Verdict.REJECT, Verdict.APPROVE, False),  # a human cannot lift a compliance block
        (GateName.COMPLIANCE, Verdict.APPROVE, Verdict.REJECT, False),
    ],
)
def test_gate_semantics(gate: GateName, agent: Verdict, human: Verdict, approved: bool) -> None:
    d = GateDecision(gate=gate, subject_key=H, agent_verdict=agent, human_verdict=human, decided_at=dt.datetime(2026, 9, 28))
    assert d.approved is approved


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
