"""Steps of the dry-run production graph (docs/design/phase1.md, ADR-001).

The graph is built in two stages because its shape depends on the script (one voice and one shot per
scene): `front_steps` (idea → package → G1 → script) always exists, `production_steps(script)` is added once
the script is known. Both stages use the same step names, versions and parameters, so the second stage
reuses every output of the first (a step key never depends on the graph it sits in).

Content addressing gives each scene two cache lines: `line_<id>` extracts what the voice needs (narration, tone,
duration) and `visual_<id>` what the shot needs (visual prompt, duration) from the script, and voice and shot
depend on their own artifact only. Editing the words of one scene, at the same length, recomputes one voice and
no shot: the GPU-heavy picture stays cached. A scene's start time is in neither artifact, so a change of
length upstream does not invalidate the scenes after it.

Every adapter here is a mock (`Production.from_mocks`); the step code does not know it: it calls the adapter
protocols of `studio.adapters.base`.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from studio.adapters.base import (
    ImageToVideo,
    MusicGenerator,
    TextToImage,
    TextToSpeech,
    TextToVideo,
    VisionCritic,
)
from studio.adapters.llm_base import LLMResult, LLMRunner, usage_costs
from studio.adapters.mock import (
    MockImageToVideo,
    MockMusicGenerator,
    MockTextToImage,
    MockTextToSpeech,
    MockTextToVideo,
    MockVisionCritic,
)
from studio.core.hashing import bytes_key, file_key
from studio.core.interfaces import StepSpec, StoredArtifact, StudioError
from studio.domain import (
    Channel,
    CostKind,
    GateName,
    Idea,
    Package,
    Platform,
    Privacy,
    Publication,
    PublicationCandidate,
    Render,
    ResourceClass,
    Script,
    ShotTechnique,
    StudioModel,
    VideoFormat,
    canonical_json,
)
from studio.media import ffmpeg, qa
from studio.pipeline.mock_agents import MockProceduralRenderer, MockStudioLLM, choose_technique
from studio.scenario.skill_json import from_skill_json

STEP_VERSION = "1"
CANDIDATE_VERSION = "2"  # 2: the candidate names the script and the QA report the judges read (critic B3)
DRAFT_DIVISOR = 4  # drafts render at a quarter of the final definition (MISSION §6.5)
MAX_SHOT_ATTEMPTS = 2  # bounded regeneration after a blocking critique
LLM_SECONDS_ESTIMATE = 120.0
# Placeholders that only size the reservation of a Claude call: the measured usage of the call replaces them.
# Phase 2 replaces them with the figures measured on real calls (NEEDS_HUMAN H7, then the editorial bench).
LLM_INPUT_TOKENS_ESTIMATE = 30_000.0
LLM_OUTPUT_TOKENS_ESTIMATE = 8_000.0
# GPU seconds per output second and per technique: docs/COST_MODEL.md, hypothesis HC3, replaced by
# measurements in phase 3. Techniques absent here run on the CPU.
GPU_SECONDS_PER_SECOND = {ShotTechnique.GEN_VIDEO: 260.0, ShotTechnique.BLENDER: 96.0, ShotTechnique.IMAGE_25D: 12.0}
TTS_GPU_SECONDS_PER_SECOND = 0.75
MUSIC_GPU_SECONDS_PER_SECOND = 0.5
LUFS_TARGET = -14.0
TRUE_PEAK_CEILING = -1.0

_SCRIPT_SCHEMA = {"type": "object", "required": ["version", "format", "langue", "scenes"]}


class ShotRejected(StudioError):
    """The visual critic blocked every attempt at a shot."""


@dataclass(frozen=True)
class FormatSpec:
    width: int
    height: int
    fps: int


FORMATS: dict[VideoFormat, FormatSpec] = {
    VideoFormat.SHORT: FormatSpec(1080, 1920, 30),
    VideoFormat.LONG: FormatSpec(1920, 1080, 30),
}


@dataclass(frozen=True)
class Production:
    """One video's channel, format and adapters. All adapters are mocks in the dry run."""

    channel: Channel
    format: VideoFormat
    seed: int
    llm: LLMRunner
    tts: TextToSpeech
    t2i: TextToImage
    i2v: ImageToVideo
    t2v: TextToVideo
    music: MusicGenerator
    critic: VisionCritic
    renderer: MockProceduralRenderer
    cwd: Path  # working directory handed to the LLM runner
    run_id: str  # the video this production makes: part of what the publication gates judge
    tmp: Path  # where steps work (a killed process leaves its scratch files here, cleaned at the next start)

    @classmethod
    def from_mocks(
        cls,
        channel: Channel,
        fmt: VideoFormat,
        seed: int = 0,
        llm: LLMRunner | None = None,
        cwd: Path | None = None,
        run_id: str | None = None,
        tmp: Path | None = None,
    ) -> Production:
        return cls(
            channel=channel,
            format=fmt,
            seed=seed,
            run_id=run_id or f"dry-{channel.id}-{fmt.value}-{seed}",
            tmp=tmp if tmp is not None else Path(tempfile.gettempdir()),
            llm=llm if llm is not None else MockStudioLLM(),
            tts=MockTextToSpeech(),
            t2i=MockTextToImage(),
            i2v=MockImageToVideo(),
            t2v=MockTextToVideo(),
            music=MockMusicGenerator(),
            critic=MockVisionCritic(),
            renderer=MockProceduralRenderer(),
            cwd=cwd if cwd is not None else Path.cwd(),
        )

    @property
    def spec(self) -> FormatSpec:
        return FORMATS[self.format]

    def adapters(self) -> tuple[Any, ...]:
        return (self.llm, self.tts, self.t2i, self.i2v, self.t2v, self.music, self.critic, self.renderer)

    def adapter_ids(self) -> list[str]:
        """Ids of every adapter this production can call (a report lists them: each must say `mock`)."""
        return sorted(a.spec.id for a in self.adapters())

    @property
    def is_mock(self) -> bool:
        """True when any adapter is a mock: the run it makes is a mock run, whatever its caller declares."""
        return any(a.spec.is_mock for a in self.adapters())

    def shot_uses_mock(self, technique: ShotTechnique) -> bool:
        makers = {
            ShotTechnique.GEN_VIDEO: (self.t2v,),
            ShotTechnique.IMAGE_25D: (self.t2i, self.i2v),
        }.get(technique, (self.renderer,))
        return any(a.spec.is_mock for a in (*makers, self.critic))

    def shot_adapter_ids(self, technique: ShotTechnique) -> list[str]:
        """Ids of the adapters that make a shot of `technique`, and judge it. Only these belong in the shot's step
        params: another backend (the LLM, the voice) must not change the key of a GPU-heavy step."""
        if technique is ShotTechnique.GEN_VIDEO:
            ids = [self.t2v.spec.id]
        elif technique is ShotTechnique.IMAGE_25D:
            ids = [self.t2i.spec.id, self.i2v.spec.id]
        else:  # BLENDER, MOTION, ARCHIVE: procedural rendering
            ids = [self.renderer.spec.id]
        return sorted([*ids, self.critic.spec.id])


# ------------------------------------------------------------------ helpers


def _model_out(model: StudioModel) -> tuple[bytes, str, str]:
    return model.canonical_json().encode("utf-8"), "json", "application/json"


def _json_out(data: Any) -> tuple[bytes, str, str]:
    return canonical_json(data).encode("utf-8"), "json", "application/json"


def _load(artifact: StoredArtifact) -> Any:
    return json.loads(artifact.path.read_text(encoding="utf-8"))


@contextlib.contextmanager
def _workdir(p: Production) -> Iterator[Path]:
    p.tmp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="studio-step-", dir=p.tmp) as directory:
        yield Path(directory)


def verify_artifact(artifact: StoredArtifact) -> None:
    """Raise unless the stored bytes still hash to their key (a store object can rot or be edited in place)."""
    actual = file_key(artifact.path)
    if actual != artifact.key:
        raise StudioError(f"stored artifact {artifact.key} is corrupt: its bytes hash to {actual}")


def _stage(artifact: StoredArtifact, workdir: Path, name: str) -> Path:
    """Expose a stored file under a name with the right suffix (the store names files by hash)."""
    dst = workdir / name
    try:
        os.link(artifact.path, dst)
    except OSError:
        shutil.copy2(artifact.path, dst)
    return dst


def _file_out(path: Path, kind: str, media_type: str) -> tuple[bytes, str, str]:
    return path.read_bytes(), kind, media_type


def _never(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
    raise StudioError("a gate step waits for a decision; it never runs code")


def _even(n: int) -> int:
    return max(2, n // 2 * 2)


def _brief(p: Production, **extra: Any) -> dict[str, Any]:
    ch = p.channel
    return {
        "channel": {"id": ch.id, "language": ch.language, "concept": ch.concept},
        "format": p.format.value,
        "language": ch.language,
        "seed": p.seed,
        **extra,
    }


def _ask(p: Production, agent: str, brief: Mapping[str, Any], schema: dict[str, Any]) -> LLMResult:
    return p.llm.run(
        agent=agent,
        prompt=canonical_json(brief),
        model="opus",  # creative decisions run on the strongest tier (MISSION §6)
        json_schema=schema,
        max_turns=8,
        allowed_tools=(),
        cwd=p.cwd,
    )


def _model_out_with_usage(model: StudioModel, result: LLMResult) -> tuple[bytes, str, str, dict[CostKind, float]]:
    """A model as the step's output, and the tokens of the call that produced it as what the step measured."""
    data, kind, media_type = _model_out(model)
    return data, kind, media_type, usage_costs(result.usage)


def contract_fingerprint(*schemas: Mapping[str, Any]) -> str:
    """SHA-256 of the JSON Schemas a step's output is written under.

    It is a parameter of the step, like `media_fingerprint()` for a render: a step whose output contract changes gets
    another key, so an output cached under the old contract is not served again, and an approval given to one candidate
    does not open the gates of another. The manifest keeps an in-flight video across a change of a step's *version*,
    never across a change of its parameters (critic R1: a candidate cached by the previous version was served again,
    with its approvals)."""
    return bytes_key(canonical_json(list(schemas)).encode("utf-8"))


def _agent_params(p: Production, agent: str, *schemas: Mapping[str, Any]) -> dict[str, Any]:
    """What besides its inputs an agent step's output depends on: the agent, the backend, the brief and the contracts."""
    return {"agent": agent, "backend": p.llm.spec.id, "brief": _brief(p), "contract": contract_fingerprint(*schemas)}


def line_step_name(index: int) -> str:
    return f"line_S{index + 1:02d}"


def visual_step_name(index: int) -> str:
    return f"visual_S{index + 1:02d}"


def voice_step_name(index: int) -> str:
    return f"voice_S{index + 1:02d}"


def shot_step_name(index: int) -> str:
    return f"shot_S{index + 1:02d}"


# ------------------------------------------------------------------ stage 1: idea -> package -> G1 -> script


def front_steps(p: Production) -> list[StepSpec]:
    def idea_run(
        inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]
    ) -> tuple[bytes, str, str, dict[CostKind, float]]:
        result = _ask(p, "strategist", _brief(p), Idea.model_json_schema())
        idea = Idea.model_validate(result.output)
        if idea.channel_id != p.channel.id:
            raise StudioError(f"the strategist proposed an idea for channel {idea.channel_id!r}, not {p.channel.id!r}")
        return _model_out_with_usage(idea, result)

    def package_run(
        inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]
    ) -> tuple[bytes, str, str, dict[CostKind, float]]:
        idea = Idea.model_validate(_load(inputs["idea"]))
        result = _ask(p, "packaging_director", _brief(p, idea=idea.model_dump(mode="json")), Package.model_json_schema())
        package = Package.model_validate(result.output)
        if package.idea_id != idea.id or package.format is not p.format:
            raise StudioError("the packaging does not match the idea or the format it was asked for")
        return _model_out_with_usage(package, result)

    def script_run(
        inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]
    ) -> tuple[bytes, str, str, dict[CostKind, float]]:
        idea = Idea.model_validate(_load(inputs["idea"]))
        package = Package.model_validate(_load(inputs["package"]))
        brief = _brief(p, idea=idea.model_dump(mode="json"), package=package.model_dump(mode="json"))
        result = _ask(p, "head_writer", brief, _SCRIPT_SCHEMA)
        script, _ = from_skill_json(result.output, idea.id)
        if script.format is not p.format:
            raise StudioError(f"the head writer produced a {script.format.value} script for a {p.format.value} video")
        return _model_out_with_usage(script, result)

    llm_cost = {
        CostKind.CLAUDE_SECONDS: LLM_SECONDS_ESTIMATE,
        CostKind.CLAUDE_INPUT_TOKENS: LLM_INPUT_TOKENS_ESTIMATE,
        CostKind.CLAUDE_OUTPUT_TOKENS: LLM_OUTPUT_TOKENS_ESTIMATE,
    }
    mock = p.llm.spec.is_mock
    return [
        StepSpec(
            "idea",
            STEP_VERSION,
            (),
            _agent_params(p, "strategist", Idea.model_json_schema()),
            ResourceClass.LLM,
            idea_run,
            estimated_cost=llm_cost,
            mock=mock,
        ),
        StepSpec(
            "package",
            STEP_VERSION,
            ("idea",),
            _agent_params(p, "packaging_director", Package.model_json_schema()),
            ResourceClass.LLM,
            package_run,
            estimated_cost=llm_cost,
            mock=mock,
        ),
        StepSpec("g1", STEP_VERSION, ("package",), {}, ResourceClass.HUMAN, _never, gate=GateName.G1),
        StepSpec(
            "script",
            STEP_VERSION,
            ("idea", "package", "g1"),
            _agent_params(p, "head_writer", _SCRIPT_SCHEMA, Script.model_json_schema()),
            ResourceClass.LLM,
            script_run,
            estimated_cost=llm_cost,
            mock=mock,
        ),
    ]


# ------------------------------------------------------------------ stage 2: one voice and one shot per scene


def _draft_or_final(
    p: Production,
    technique: ShotTechnique,
    brief: str,
    width: int,
    height: int,
    duration_s: float,
    fps: int,
    seed: int,
    out: Path,
    workdir: Path,
) -> None:
    """Render one clip with the adapter the technique calls for."""
    if technique is ShotTechnique.GEN_VIDEO:
        p.t2v.generate(brief, width=width, height=height, duration_s=duration_s, fps=fps, seed=seed, out=out)
    elif technique is ShotTechnique.IMAGE_25D:
        still = workdir / f"still-{out.stem}.png"
        p.t2i.generate(brief, width=width, height=height, seed=seed, out=still)
        p.i2v.animate(still, brief, duration_s=duration_s, fps=fps, seed=seed, out=out)
    else:  # BLENDER, MOTION, ARCHIVE: procedural rendering, no generative model
        p.renderer.render(brief, width=width, height=height, duration_s=duration_s, fps=fps, seed=seed, out=out)


def _shot_run(p: Production, index: int, visual_step: str, technique: ShotTechnique) -> Any:
    spec = p.spec

    def run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        visual = _load(inputs[visual_step])
        brief, duration = visual["visual_prompt_en"], float(visual["duration_s"])
        with _workdir(p) as wd:
            final = wd / "shot.mp4"
            for attempt in range(MAX_SHOT_ATTEMPTS):
                seed = int(params["seed"]) + attempt
                draft = wd / f"draft-{attempt}.mp4"
                _draft_or_final(
                    p, technique, brief, _even(spec.width // DRAFT_DIVISOR), _even(spec.height // DRAFT_DIVISOR),
                    duration, spec.fps, seed, draft, wd,
                )  # fmt: skip
                critique = p.critic.critique([draft], brief)
                if not critique.blocking:
                    _draft_or_final(p, technique, brief, spec.width, spec.height, duration, spec.fps, seed, final, wd)
                    return _file_out(final, "video", "video/mp4")
            raise ShotRejected(
                f"{shot_step_name(index)}: the critic blocked {MAX_SHOT_ATTEMPTS} attempts: {list(critique.defects)}"
            )

    return run


def production_steps(p: Production, script: Script) -> list[StepSpec]:
    """Steps that follow the script; the caller passes `front_steps(p) + production_steps(p, script)`."""
    spec = p.spec
    media = ffmpeg.media_fingerprint()  # what the bytes of a render depend on besides the inputs
    tts_id, music_id = p.tts.spec.id, p.music.spec.id
    steps: list[StepSpec] = []

    def timeline_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        s = Script.model_validate(_load(inputs["script"]))
        return _json_out({"duration_s": s.duration_s, "scene_durations": [sc.duration_s for sc in s.scenes]})

    steps.append(StepSpec("timeline", STEP_VERSION, ("script",), {}, ResourceClass.CPU, timeline_run))

    for i, scene in enumerate(script.scenes):
        line_name, visual_name, voice_name, shot_name = (
            line_step_name(i),
            visual_step_name(i),
            voice_step_name(i),
            shot_step_name(i),
        )
        technique = choose_technique(scene, i)

        def line_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any], i: int = i) -> tuple[bytes, str, str]:
            scene_i = Script.model_validate(_load(inputs["script"])).scenes[i]
            return _json_out({"voice_over": scene_i.voice_over, "tone": scene_i.tone, "duration_s": scene_i.duration_s})

        def visual_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any], i: int = i) -> tuple[bytes, str, str]:
            scene_i = Script.model_validate(_load(inputs["script"])).scenes[i]
            return _json_out({"visual_prompt_en": scene_i.visual_prompt_en, "duration_s": scene_i.duration_s})

        def voice_run(
            inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any], line_name: str = line_name
        ) -> tuple[bytes, str, str]:
            data = _load(inputs[line_name])
            with _workdir(p) as wd:
                out = wd / "voice.wav"
                if data["voice_over"].strip():
                    p.tts.speak(data["voice_over"], voice_id=params["voice_id"], language=params["language"], out=out)
                else:
                    ffmpeg.silence(out, float(data["duration_s"]))
                return _file_out(out, "audio", "audio/wav")

        steps.append(StepSpec(line_name, STEP_VERSION, ("script",), {"index": i}, ResourceClass.CPU, line_run))
        steps.append(StepSpec(visual_name, STEP_VERSION, ("script",), {"index": i}, ResourceClass.CPU, visual_run))
        steps.append(
            StepSpec(
                voice_name,
                STEP_VERSION,
                (line_name,),
                {"voice_id": p.channel.voice_id, "language": p.channel.language, "adapter": tts_id, "media": media},
                ResourceClass.GPU,
                voice_run,
                estimated_cost={CostKind.GPU_SECONDS: max(1.0, TTS_GPU_SECONDS_PER_SECOND * scene.duration_s)},
                model_id=tts_id,
                mock=p.tts.spec.is_mock,
            )
        )
        gpu_rate = GPU_SECONDS_PER_SECOND.get(technique)
        steps.append(
            StepSpec(
                shot_name,
                STEP_VERSION,
                (visual_name,),
                {
                    "technique": technique.value,
                    "width": spec.width,
                    "height": spec.height,
                    "fps": spec.fps,
                    "seed": p.seed + i,
                    "adapters": p.shot_adapter_ids(technique),
                    "media": media,
                },
                ResourceClass.GPU if gpu_rate is not None else ResourceClass.CPU,
                _shot_run(p, i, visual_name, technique),
                estimated_cost={CostKind.GPU_SECONDS: max(1.0, (gpu_rate or 0.0) * scene.duration_s)} if gpu_rate else {},
                model_id=technique.value,
                mock=p.shot_uses_mock(technique),
            )
        )

    def music_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        timeline = _load(inputs["timeline"])
        with _workdir(p) as wd:
            out = wd / "bed.wav"
            p.music.compose(params["brief"], duration_s=float(timeline["duration_s"]), seed=int(params["seed"]), out=out)
            return _file_out(out, "audio", "audio/wav")

    def mix_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        durations = _load(inputs["timeline"])["scene_durations"]
        with _workdir(p) as wd:
            parts: list[Path] = []
            for i, target in enumerate(durations):
                voice = _stage(inputs[voice_step_name(i)], wd, f"voice{i}.wav")
                gap = float(target) - qa.probe(voice).duration_s
                if gap < -0.05:
                    raise StudioError(f"{voice_step_name(i)} is {-gap:.2f} s longer than its scene")
                if gap > 0.001:  # pad each voice to its scene so that voice and picture stay in step
                    parts.append(ffmpeg.concat_audio(wd / f"scene{i}.wav", [voice, ffmpeg.silence(wd / f"pad{i}.wav", gap)]))
                else:
                    parts.append(voice)
            track = ffmpeg.concat_audio(wd / "voice.wav", parts)
            bed = _stage(inputs["music"], wd, "bed.wav")
            mixed = ffmpeg.mix_audio(wd / "mixed.wav", track, bed, bed_gain_db=float(params["bed_gain_db"]))
            master = ffmpeg.loudnorm_two_pass(
                wd / "master.wav", mixed, target_lufs=float(params["lufs"]), true_peak_db=float(params["true_peak_db"])
            )
            return _file_out(master, "audio", "audio/wav")

    def assemble_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        with _workdir(p) as wd:
            clips = [_stage(inputs[shot_step_name(i)], wd, f"shot{i}.mp4") for i in range(len(script.scenes))]
            video = ffmpeg.concat_videos(wd / "video.mp4", clips, width=spec.width, height=spec.height, fps=spec.fps)
            master = _stage(inputs["mix"], wd, "master.wav")
            return _file_out(ffmpeg.mux(wd / "render.mp4", video, master), "video", "video/mp4")

    def qa_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        expected = float(_load(inputs["timeline"])["duration_s"])
        with _workdir(p) as wd:
            render = _stage(inputs["assemble"], wd, "render.mp4")
            defects = qa.check_render(render, spec.width, spec.height, spec.fps, expected)
            info = qa.probe(render)
            lufs, peak = qa.loudness(render) if info.has_audio else (None, None)
        described = Render(
            format=p.format,
            width=info.width,
            height=info.height,
            fps=info.fps,
            duration_s=info.duration_s,
            video_key=inputs["assemble"].key,
            has_audio=info.has_audio,
            integrated_lufs=lufs,
            true_peak_dbtp=peak,
        )
        return _json_out({"render": described.model_dump(mode="json"), "defects": defects})

    def candidate_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        """Everything the platform will show, bound to the render, the channel and the run: this is what the compliance
        officer and the human judge, so that nothing published can differ from what they saw."""
        s = Script.model_validate(_load(inputs["script"]))
        verify_artifact(inputs["assemble"])
        note = "AI-generated reconstruction." if s.disclosure.required else ""
        candidate = PublicationCandidate(
            run_id=params["run_id"],
            channel_id=params["channel_id"],
            script_key=inputs["script"].key,  # the judges read the script and the QA report: their keys are part of the subject
            qa_key=inputs["qa"].key,
            publication=Publication(
                platform=Platform.YOUTUBE,
                render_key=inputs["assemble"].key,
                title=s.titles[0],
                description="\n\n".join(part for part in (s.promise, note) if part),
                privacy=Privacy.PRIVATE,  # a dry run plans a private upload and makes no network call
                contains_synthetic_media=s.disclosure.required,
            ),
        )
        return _model_out(candidate)

    def publish_run(inputs: Mapping[str, StoredArtifact], params: Mapping[str, Any]) -> tuple[bytes, str, str]:
        """Release the approved candidate, byte for byte, once nothing about it has changed or decayed."""
        candidate = PublicationCandidate.model_validate(_load(inputs["candidate"]))
        render = inputs["assemble"]
        if candidate.publication.render_key != render.key:
            raise StudioError("the approved candidate names another render than the one assembled")
        if (candidate.script_key, candidate.qa_key) != (inputs["script"].key, inputs["qa"].key):
            raise StudioError("the approved candidate was judged on another script or QA report than the ones in hand")
        verify_artifact(render)  # the bytes about to be published are the bytes that were judged
        defects = _load(inputs["qa"])["defects"]
        if defects:  # MISSION §8: every published video passes the technical checks
            raise StudioError(f"the render has technical defects and cannot be published: {defects}")
        released = inputs["candidate"].path.read_bytes()
        if bytes_key(released) != inputs["candidate"].key:  # byte for byte what the gates approved, or nothing
            raise StudioError(f"the approved candidate {inputs['candidate'].key} changed on disk after it was approved")
        return released, "json", "application/json"

    steps += [
        StepSpec(
            "music",
            STEP_VERSION,
            ("timeline",),
            {"brief": f"ambient bed for {p.channel.concept}", "seed": p.seed, "adapter": music_id, "media": media},
            ResourceClass.GPU,
            music_run,
            estimated_cost={CostKind.GPU_SECONDS: max(1.0, MUSIC_GPU_SECONDS_PER_SECOND * script.duration_s)},
            model_id=music_id,
            mock=p.music.spec.is_mock,
        ),
        StepSpec(
            "mix",
            STEP_VERSION,
            ("timeline", *(voice_step_name(i) for i in range(len(script.scenes))), "music"),
            {"bed_gain_db": -18.0, "lufs": LUFS_TARGET, "true_peak_db": TRUE_PEAK_CEILING, "media": media},
            ResourceClass.CPU,
            mix_run,
        ),
        StepSpec(
            "assemble",
            STEP_VERSION,
            ("mix", *(shot_step_name(i) for i in range(len(script.scenes)))),
            {"width": spec.width, "height": spec.height, "fps": spec.fps, "media": media},
            ResourceClass.CPU,
            assemble_run,
        ),
        StepSpec(
            "qa",
            STEP_VERSION,
            ("assemble", "timeline"),
            {"media": media, "contract": contract_fingerprint(Render.model_json_schema())},
            ResourceClass.CPU,
            qa_run,
        ),
        StepSpec(
            "candidate",
            CANDIDATE_VERSION,
            ("script", "assemble", "qa"),
            {
                "run_id": p.run_id,
                "channel_id": p.channel.id,
                "contract": contract_fingerprint(PublicationCandidate.model_json_schema()),
            },
            ResourceClass.CPU,
            candidate_run,
            candidate=True,
        ),
        # Both gates judge the candidate: a changed title, description or disclosure is another hash, so another decision.
        StepSpec("compliance", STEP_VERSION, ("candidate",), {}, ResourceClass.HUMAN, _never, gate=GateName.COMPLIANCE),
        StepSpec("g2", STEP_VERSION, ("candidate",), {}, ResourceClass.HUMAN, _never, gate=GateName.G2),
        StepSpec(
            "publish_plan",
            CANDIDATE_VERSION,
            ("candidate", "script", "assemble", "qa", "compliance", "g2"),
            {},
            ResourceClass.CPU,
            publish_run,
            # publication guard (ADR-001 decision 8): the exact candidate must carry a compliance approval and a G2
            requires_approval=((GateName.COMPLIANCE, "candidate"), (GateName.G2, "candidate")),
            publishes=True,
        ),
    ]
    return steps
