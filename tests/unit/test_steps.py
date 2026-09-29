"""Shape of the dry-run graph and behaviour of its steps: cache lines, gates, publication guard, bounded regeneration."""

from __future__ import annotations

import dataclasses
import hashlib
import re
from pathlib import Path
from typing import Any

import pytest
from pipeline_fakes import channel

from studio.adapters.base import CritiqueResult
from studio.adapters.mock import MockVisionCritic
from studio.core.graph import Graph
from studio.core.interfaces import StepSpec, StoredArtifact, StudioError
from studio.domain import (
    AdapterStatus,
    CostKind,
    GateName,
    Idea,
    Package,
    Platform,
    Publication,
    PublicationCandidate,
    Render,
    ResourceClass,
    SceneRole,
    Script,
    ShotTechnique,
    StudioModel,
    VideoFormat,
    canonical_json,
)
from studio.pipeline import steps as steps_module
from studio.pipeline.mock_agents import MockStudioLLM, build_idea, build_package, build_script_doc
from studio.pipeline.steps import (
    CANDIDATE_VERSION,
    FORMATS,
    MAX_SHOT_ATTEMPTS,
    Production,
    ShotRejected,
    contract_fingerprint,
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
    assert len(steps) == 4 + 1 + 4 * n + 8  # timeline, 4 per scene, music, mix, assemble, qa, candidate, 2 gates, plan
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
def test_publication_needs_the_compliance_verdict_and_g2_on_the_exact_candidate(media_tools: None) -> None:
    p = production()
    s = by_name(front_steps(p) + production_steps(p, script_of()))
    publish = s["publish_plan"]
    assert publish.requires_approval == ((GateName.COMPLIANCE, "candidate"), (GateName.G2, "candidate"))
    assert publish.publishes  # the graph itself refuses a publishing step without both approvals on one subject
    assert {"candidate", "compliance", "g2", "script", "assemble", "qa"} <= set(publish.inputs)
    assert s["candidate"].candidate and not publish.candidate  # the approvals bear on the step that carries what they read
    assert s["compliance"].gate is GateName.COMPLIANCE and s["g2"].gate is GateName.G2
    assert s["compliance"].inputs == ("candidate",) == s["g2"].inputs  # both judge what will be published, not the render alone
    assert s["candidate"].inputs == ("script", "assemble", "qa")
    assert s["candidate"].params == {  # a candidate belongs to one video, and is written under one contract
        "run_id": p.run_id,
        "channel_id": p.channel.id,
        "contract": contract_fingerprint(PublicationCandidate.model_json_schema()),
    }


class RealLookingAdapter:
    """Any adapter that declares itself real (no `mock` in its id, a measured status)."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.spec = dataclasses.replace(inner.spec, id=inner.spec.id.replace("mock-", "wan-"), status=AdapterStatus.RETAINED)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)


def test_a_shot_is_a_mock_as_soon_as_its_maker_or_its_critic_is() -> None:
    """Critic N9: real image and video makers judged by a mock critic still make a plan that no real run may contain."""
    p = production(roles=SHORT_ROLES)
    real = dataclasses.replace(p, t2i=RealLookingAdapter(p.t2i), i2v=RealLookingAdapter(p.i2v), t2v=RealLookingAdapter(p.t2v))
    assert not real.t2i.spec.is_mock and real.critic.spec.is_mock
    for technique in (ShotTechnique.GEN_VIDEO, ShotTechnique.IMAGE_25D):
        assert real.shot_uses_mock(technique)  # the critic is a mock
    real_critic = dataclasses.replace(real, critic=RealLookingAdapter(p.critic))
    assert not real_critic.shot_uses_mock(ShotTechnique.GEN_VIDEO) and not real_critic.shot_uses_mock(ShotTechnique.IMAGE_25D)
    assert real_critic.shot_uses_mock(ShotTechnique.BLENDER)  # the procedural renderer is still a stand-in
    assert real_critic.is_mock  # ... and so are the voice, the music and the writers


@pytest.mark.media
def test_a_step_whose_output_is_a_contract_carries_the_fingerprint_of_that_contract(media_tools: None) -> None:
    """Critic R1: an output cached under an older contract must not be served again, so the contract is a parameter."""
    p = production()
    s = by_name(front_steps(p) + production_steps(p, script_of()))
    expected = {
        "idea": (Idea.model_json_schema(),),
        "package": (Package.model_json_schema(),),
        "qa": (Render.model_json_schema(),),
        "candidate": (PublicationCandidate.model_json_schema(),),
    }
    for name, schemas in expected.items():
        assert s[name].params["contract"] == contract_fingerprint(*schemas), name
    assert len(s["script"].params["contract"]) == 64
    assert s["candidate"].version == s["publish_plan"].version == CANDIDATE_VERSION == "2"


def test_the_contract_fingerprint_follows_the_schemas_it_is_given() -> None:
    class Before(StudioModel):
        x: int

    class After(StudioModel):
        x: int
        y: int = 0

    before, after = Before.model_json_schema(), After.model_json_schema()
    assert contract_fingerprint(before) == contract_fingerprint(dict(before)) and len(contract_fingerprint(before)) == 64
    assert contract_fingerprint(before) != contract_fingerprint(after)  # a field added: another contract, another key
    assert contract_fingerprint(before, after) != contract_fingerprint(after, before)


def test_the_contract_fingerprint_ignores_documentation_and_sees_structure() -> None:
    """Critic R9: pydantic copies docstrings and descriptions into the schema; a reworded sentence is not a new contract."""

    def schema(**changes: object) -> dict[str, object]:
        base: dict[str, object] = {
            "type": "object",
            "title": "Doc",
            "description": "What a doc is.",
            "properties": {"x": {"type": "integer", "title": "X", "description": "The x.", "examples": [1], "default": 1}},
            "required": ["x"],
        }
        return {**base, **changes}

    reference = contract_fingerprint(schema())
    reworded = schema(title="Other", description="Words that say something else.")
    reworded["properties"] = {"x": {"type": "integer", "title": "Ex", "description": "Else.", "examples": [2, 3], "default": 1}}
    assert contract_fingerprint(reworded) == reference  # titles, descriptions and examples are documentation

    retyped = schema(properties={"x": {"type": "string", "default": 1}})
    grown = schema(properties={"x": {"type": "integer", "default": 1}, "y": {"type": "integer"}})
    optional = schema(required=[])
    other_default = schema(properties={"x": {"type": "integer", "default": 2}})
    for changed in (retyped, grown, optional, other_default):
        assert contract_fingerprint(changed) != reference  # what the contract accepts and what a missing field means


def test_a_field_named_like_a_documentation_keyword_is_structure_not_documentation() -> None:
    """`Publication` has a `title` and a `description`: dropping or retyping them must change the contract."""
    with_title = {"type": "object", "properties": {"title": {"type": "string", "description": "shown to viewers"}}}
    retyped = {"type": "object", "properties": {"title": {"type": "integer", "description": "shown to viewers"}}}
    renamed = {"type": "object", "properties": {"description": {"type": "string"}}}
    dropped = {"type": "object", "properties": {}}
    fingerprints = {contract_fingerprint(x) for x in (with_title, retyped, renamed, dropped)}
    assert len(fingerprints) == 4
    nested = {"$defs": {"Publication": with_title}, "$ref": "#/$defs/Publication"}
    assert contract_fingerprint(nested) != contract_fingerprint(
        {"$defs": {"Publication": retyped}, "$ref": "#/$defs/Publication"}
    )


def test_editing_the_docstring_of_a_contract_does_not_change_its_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    before = {m: contract_fingerprint(m.model_json_schema()) for m in (Idea, Package, Script, PublicationCandidate, Render)}
    for model in before:
        monkeypatch.setattr(model, "__doc__", f"A sentence that says something else about {model.__name__}.")
    assert {m: contract_fingerprint(m.model_json_schema()) for m in before} == before


@pytest.mark.media
def test_the_steps_that_use_a_mock_adapter_are_flagged_so_a_real_run_cannot_contain_them(media_tools: None) -> None:
    p = production(roles=SHORT_ROLES)
    steps = front_steps(p) + production_steps(p, script_of(roles=SHORT_ROLES))
    flagged = {s.name for s in steps if s.mock}
    assert {"idea", "package", "script", "music"} <= flagged
    assert {n for n in flagged if n.startswith("voice_") or n.startswith("shot_")} == {
        s.name for s in steps if s.name.startswith(("voice_", "shot_"))
    }
    assert p.is_mock


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


# ------------------------------------------------------------------ the publication steps (critic B1, I5, I6)


def artifact(tmp_path: Path, name: str, data: bytes, *, key: str | None = None) -> StoredArtifact:
    path = tmp_path / name
    path.write_bytes(data)
    return StoredArtifact(
        key=key or hashlib.sha256(data).hexdigest(), kind="json", media_type="application/json", size_bytes=len(data), path=path
    )


class Publishing:
    """The candidate and publish_plan steps of a production, with inputs shaped like the runner's."""

    def __init__(self, tmp_path: Path, *, defects: list[str] | None = None, rotted: bool = False) -> None:
        self.p = production(roles=SHORT_ROLES)
        self.script = script_of(roles=SHORT_ROLES)
        steps = by_name(front_steps(self.p) + production_steps(self.p, self.script))
        self.candidate_step, self.publish_step = steps["candidate"], steps["publish_plan"]
        good = b"render bytes"
        self.render = artifact(tmp_path, "render.mp4", b"rotted bytes" if rotted else good, key=hashlib.sha256(good).hexdigest())
        self.script_artifact = artifact(tmp_path, "script.json", self.script.canonical_json().encode())
        report = {"render": {"video_key": self.render.key}, "defects": defects or []}
        self.qa = artifact(tmp_path, "qa.json", canonical_json(report).encode())
        self.tmp_path = tmp_path

    def candidate(self) -> StoredArtifact:
        data, kind, _ = self.candidate_step.run(
            {"script": self.script_artifact, "assemble": self.render, "qa": self.qa}, self.candidate_step.params
        )[:3]
        assert kind == "json"
        return artifact(self.tmp_path, "candidate.json", data)

    def publish(
        self, candidate: StoredArtifact | None = None, *, script: StoredArtifact | None = None, qa: StoredArtifact | None = None
    ) -> tuple[bytes, str, str]:
        inputs = {
            "candidate": candidate or self.candidate(),
            "script": script or self.script_artifact,
            "assemble": self.render,
            "qa": qa or self.qa,
        }
        return self.publish_step.run(inputs, {})[:3]  # type: ignore[return-value]


@pytest.mark.media
def test_the_candidate_holds_everything_the_platform_will_show_bound_to_the_render_the_channel_and_the_run(
    media_tools: None, tmp_path: Path
) -> None:
    fixture = Publishing(tmp_path)
    candidate = PublicationCandidate.model_validate_json(fixture.candidate().path.read_bytes())
    assert candidate.run_id == fixture.p.run_id and candidate.channel_id == "channel-a"
    publication = candidate.publication
    assert publication.render_key == fixture.render.key and publication.title == fixture.script.titles[0]
    assert publication.contains_synthetic_media is fixture.script.disclosure.required
    assert publication.privacy.value == "private" and publication.platform is Platform.YOUTUBE
    assert publication.description.startswith(fixture.script.promise)
    assert (candidate.script_key, candidate.qa_key) == (fixture.script_artifact.key, fixture.qa.key)  # what the judges read


@pytest.mark.media
def test_a_candidate_is_not_made_from_a_render_whose_bytes_no_longer_match_their_key(media_tools: None, tmp_path: Path) -> None:
    with pytest.raises(StudioError, match="is corrupt"):
        Publishing(tmp_path, rotted=True).candidate()


@pytest.mark.media
def test_the_publication_plan_releases_the_approved_candidate_byte_for_byte(media_tools: None, tmp_path: Path) -> None:
    fixture = Publishing(tmp_path)
    candidate = fixture.candidate()
    data, kind, media_type = fixture.publish(candidate)
    assert data == candidate.path.read_bytes() and kind == "json" and media_type == "application/json"


@pytest.mark.media
def test_the_publication_plan_refuses_a_render_with_technical_defects_whoever_approved_it(
    media_tools: None, tmp_path: Path
) -> None:
    fixture = Publishing(tmp_path, defects=["true peak -0.2 dBTP is above -1.0"])
    with pytest.raises(StudioError, match="technical defects and cannot be published.*true peak"):
        fixture.publish()


@pytest.mark.media
def test_the_publication_plan_refuses_a_candidate_that_names_another_render(media_tools: None, tmp_path: Path) -> None:
    fixture = Publishing(tmp_path)
    other = PublicationCandidate.model_validate_json(fixture.candidate().path.read_bytes())
    swapped = other.model_copy(update={"publication": other.publication.model_copy(update={"render_key": "e" * 64})})
    with pytest.raises(StudioError, match="names another render"):
        fixture.publish(artifact(tmp_path, "swapped.json", swapped.canonical_json().encode()))


@pytest.mark.media
def test_the_publication_plan_refuses_a_script_or_a_qa_report_other_than_the_ones_the_judges_read(
    media_tools: None, tmp_path: Path
) -> None:
    fixture = Publishing(tmp_path)
    candidate = fixture.candidate()
    blocked = fixture.script.model_copy(
        update={"control": fixture.script.control.model_copy(update={"publishable": False, "blocking_reasons": ("defamation",)})}
    )
    with pytest.raises(StudioError, match="judged on another script or QA report"):
        fixture.publish(candidate, script=artifact(tmp_path, "blocked-script.json", blocked.canonical_json().encode()))
    with pytest.raises(StudioError, match="judged on another script or QA report"):
        fixture.publish(candidate, qa=artifact(tmp_path, "other-qa.json", b'{"defects": []}'))


@pytest.mark.media
def test_the_publication_plan_refuses_a_candidate_edited_after_the_approval(media_tools: None, tmp_path: Path) -> None:
    """Critic I-3: the release is byte for byte what the gates approved; a candidate edited in place is not released."""
    fixture = Publishing(tmp_path)
    candidate = fixture.candidate()
    raw = candidate.path.read_bytes()
    at = raw.index(b'"title":"') + len(b'"title":"')
    candidate.path.write_bytes(raw[:at] + bytes([raw[at] ^ 0x01]) + raw[at + 1 :])  # first letter of the title, same size
    with pytest.raises(StudioError, match="changed on disk after it was approved"):
        fixture.publish(candidate)


@pytest.mark.media
def test_the_publication_plan_refuses_a_render_rotted_since_it_was_approved(media_tools: None, tmp_path: Path) -> None:
    fixture = Publishing(tmp_path)
    candidate = fixture.candidate()
    fixture.render.path.write_bytes(b"rotted bytes")  # the store's object decays after the approvals
    with pytest.raises(StudioError, match="is corrupt"):
        fixture.publish(candidate)


def test_verify_artifact_hashes_the_stored_bytes(tmp_path: Path) -> None:
    from studio.pipeline.steps import verify_artifact

    good = artifact(tmp_path, "good.bin", b"abc")
    verify_artifact(good)
    with pytest.raises(StudioError, match="is corrupt"):
        verify_artifact(artifact(tmp_path, "bad.bin", b"abd", key=good.key))


def test_publication_dataclass_is_still_the_contract_the_candidate_wraps() -> None:
    fields = set(PublicationCandidate.model_fields)
    assert (
        fields == {"run_id", "channel_id", "publication", "script_key", "qa_key"}
        and PublicationCandidate.model_fields["publication"].annotation is Publication
    )
