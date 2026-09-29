"""Mock adapters and the adapter registry: protocols, specs, determinism, and registration rules.

Media proofs need ffmpeg. Without it they are skipped, unless STUDIO_REQUIRE_MEDIA=1 turns the skip into a failure
(`make verify-phase-1` and the CI must export it). The guard below repeats the one of test_media.py.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import wave
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from studio.adapters import mock, registry
from studio.adapters.base import (
    AdapterSpec,
    ImageToVideo,
    Interpolator,
    LipSync,
    MediaResult,
    MusicGenerator,
    SoundEffects,
    TextToImage,
    TextToSpeech,
    TextToVideo,
    Transcriber,
    Upscaler,
    VisionCritic,
)
from studio.adapters.llm_base import LLMResult, LLMRunner, LLMUsage
from studio.adapters.mock import (
    MOCK_CLASSES,
    MOCK_LICENSE_URL,
    MockImageToVideo,
    MockInterpolator,
    MockLipSync,
    MockMusicGenerator,
    MockSoundEffects,
    MockTextToImage,
    MockTextToSpeech,
    MockTextToVideo,
    MockTranscriber,
    MockTranscriptMissing,
    MockUpscaler,
    MockVisionCritic,
    derive_color,
    derive_digest,
    derive_frequency,
    mock_spec,
    transcript_sidecar,
)
from studio.adapters.mock_llm import MOCK_LLM_ID, MockLLMRunner
from studio.adapters.registry import AdapterNotFound, AdapterRegistry, AdapterRejected
from studio.domain import AdapterKind, AdapterStatus, LicenseClass
from studio.media import ffmpeg, qa

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
REQUIRE_MEDIA_ENV = "STUDIO_REQUIRE_MEDIA"
NOT_REQUIRED = frozenset({"", "0", "false", "no", "off"})
REPO = Path(__file__).resolve().parents[2]


def media_is_required(environ: Mapping[str, str] = os.environ) -> bool:
    """STUDIO_REQUIRE_MEDIA is set to anything but 0/false/no/off (an unknown value fails closed)."""
    return environ.get(REQUIRE_MEDIA_ENV, "").strip().lower() not in NOT_REQUIRED


def require_ffmpeg(available: bool = HAS_FFMPEG) -> None:
    """Media proofs run when ffmpeg exists; without it they skip, or FAIL under STUDIO_REQUIRE_MEDIA."""
    if available:
        return
    if media_is_required():
        pytest.fail(f"ffmpeg/ffprobe not on PATH and {REQUIRE_MEDIA_ENV} is set: the media proofs are mandatory", pytrace=False)
    pytest.skip(f"ffmpeg/ffprobe not on PATH: media proofs skipped (set {REQUIRE_MEDIA_ENV}=1 to make this a failure)")


@pytest.fixture
def ffmpeg_required() -> None:
    require_ffmpeg()


def media(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Tests that launch ffmpeg: marked `media`, and they fail without ffmpeg under STUDIO_REQUIRE_MEDIA."""
    return pytest.mark.media(pytest.mark.usefixtures("ffmpeg_required")(fn))


PROTOCOL_OF: dict[type, type] = {
    MockTextToImage: TextToImage,
    MockImageToVideo: ImageToVideo,
    MockTextToVideo: TextToVideo,
    MockTextToSpeech: TextToSpeech,
    MockMusicGenerator: MusicGenerator,
    MockSoundEffects: SoundEffects,
    MockUpscaler: Upscaler,
    MockInterpolator: Interpolator,
    MockLipSync: LipSync,
    MockTranscriber: Transcriber,
    MockVisionCritic: VisionCritic,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


# ------------------------------------------------------------------ protocols and specs


def test_there_is_one_mock_per_media_protocol() -> None:
    assert len(MOCK_CLASSES) == 11
    assert set(MOCK_CLASSES) == set(PROTOCOL_OF)
    kinds = [cls().spec.kind for cls in MOCK_CLASSES]
    assert len(set(kinds)) == len(kinds)
    assert set(kinds) == set(AdapterKind) - {AdapterKind.LLM}


@pytest.mark.media  # a mandatory proof of the module: selected by `-m media` (it needs no ffmpeg)
@pytest.mark.parametrize("cls", MOCK_CLASSES, ids=lambda c: c.__name__)
def test_each_mock_satisfies_its_protocol(cls: type) -> None:
    adapter = cls()
    assert isinstance(adapter, PROTOCOL_OF[cls])
    assert isinstance(adapter, registry.PROTOCOLS[adapter.spec.kind])
    # the runtime check is not vacuous; it only compares member names, so the two `generate` protocols
    # cannot be told apart by isinstance (the registry compares signatures for that)
    same_shape = {TextToImage, TextToVideo}
    own = PROTOCOL_OF[cls]
    others = [p for c, p in PROTOCOL_OF.items() if c is not cls and not {p, own} <= same_shape]
    assert not any(isinstance(adapter, p) for p in others)


@pytest.mark.parametrize("cls", MOCK_CLASSES, ids=lambda c: c.__name__)
def test_each_mock_declares_a_mock_spec(cls: type) -> None:
    spec: AdapterSpec = cls().spec
    assert "mock" in spec.id
    assert spec.status is AdapterStatus.MOCK
    assert spec.is_mock is True
    assert spec.license_class is LicenseClass.ACCEPTED
    assert spec.license_url == MOCK_LICENSE_URL == "n/a (mock)"
    assert (spec.vram_gb, spec.gpu_seconds_per_output_second) == (None, None)
    assert (spec.max_width, spec.max_height, spec.max_duration_s) == (None, None, None)
    assert "mock" in cls.__name__.lower() and "mock" in repr(cls())


def test_mock_spec_requires_mock_in_the_id() -> None:
    with pytest.raises(ValueError, match="mock"):
        mock_spec("wan22-ti2v-5b", AdapterKind.TEXT_TO_VIDEO)


def test_derivations_are_stable_and_input_sensitive() -> None:
    d1 = derive_digest("mock-x", prompt="a fox", seed=1)
    assert d1 == derive_digest("mock-x", seed=1, prompt="a fox")  # canonical: argument order is irrelevant
    assert d1 != derive_digest("mock-x", prompt="a fox", seed=2)
    assert d1 != derive_digest("mock-x", prompt="a fox ", seed=1)
    assert d1 != derive_digest("mock-y", prompt="a fox", seed=1)
    color = derive_color(d1)
    assert len(color) == 7 and color.startswith("#")
    assert all(40 <= int(color[i : i + 2], 16) <= 215 for i in (1, 3, 5))
    freqs = {derive_frequency(derive_digest("mock-x", seed=s), 110.0, 330.0) for s in range(200)}
    assert all(110.0 <= f < 330.0 for f in freqs)
    assert len(freqs) > 190  # a fine grid: seeds rarely collide


def test_transcript_sidecar_sits_next_to_the_audio(tmp_path: Path) -> None:
    assert transcript_sidecar(tmp_path / "voice.wav") == tmp_path / "voice.wav.txt"


# ------------------------------------------------------------------ determinism of every rendering mock


@pytest.fixture(scope="module")
def sources(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    require_ffmpeg()
    d = tmp_path_factory.mktemp("sources")
    return {
        "image": ffmpeg.still_image(d / "image.png", 320, 180, "#446688"),
        "video": ffmpeg.color_clip(d / "video.mp4", 320, 240, 30, 1.0, "#884422"),
        "video2": ffmpeg.color_clip(d / "video2.mp4", 320, 240, 30, 1.0, "#228844"),
        "audio": ffmpeg.tone(d / "audio.wav", 1.0, 220.0),
        "audio2": ffmpeg.tone(d / "audio2.wav", 1.0, 330.0),
    }


Call = Callable[[dict[str, Path], Path, dict[str, Any]], MediaResult]


def _t2i(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"prompt": "a lighthouse at dusk", "seed": 1} | kw
    return MockTextToImage().generate(args["prompt"], width=320, height=180, seed=args["seed"], out=d / "img.png")


def _i2v(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"prompt": "slow push-in", "seed": 1} | kw
    return MockImageToVideo().animate(src["image"], args["prompt"], duration_s=1.0, fps=24, seed=args["seed"], out=d / "i2v.mp4")


def _t2v(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"prompt": "waves on a reef", "seed": 1} | kw
    return MockTextToVideo().generate(
        args["prompt"], width=320, height=240, duration_s=1.0, fps=30, seed=args["seed"], out=d / "t2v.mp4"
    )


def _tts(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"text": "Il était une fois un phare", "voice_id": "narrator", "language": "fr"} | kw
    return MockTextToSpeech().speak(args["text"], voice_id=args["voice_id"], language=args["language"], out=d / "voice.wav")


def _music(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"brief": "calm ambient bed", "seed": 1} | kw
    return MockMusicGenerator().compose(args["brief"], duration_s=1.5, seed=args["seed"], out=d / "music.wav")


def _sfx(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"brief": "door slam", "seed": 1} | kw
    return MockSoundEffects().effect(args["brief"], duration_s=0.5, seed=args["seed"], out=d / "sfx.wav")


def _upscale(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"video": "video", "width": 640, "height": 480} | kw
    return MockUpscaler().upscale(src[args["video"]], width=args["width"], height=args["height"], out=d / "up.mp4")


def _interpolate(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"video": "video", "fps": 60} | kw
    return MockInterpolator().interpolate(src[args["video"]], fps=args["fps"], out=d / "interp.mp4")


def _lipsync(src: dict[str, Path], d: Path, kw: dict[str, Any]) -> MediaResult:
    args = {"video": "video", "audio": "audio"} | kw
    return MockLipSync().sync(src[args["video"]], src[args["audio"]], out=d / "sync.mp4")


CASES: dict[str, tuple[Call, list[dict[str, Any]]]] = {
    "text_to_image": (_t2i, [{"prompt": "a lighthouse at dawn"}, {"seed": 2}]),
    "image_to_video": (_i2v, [{"prompt": "slow pull-out"}, {"seed": 2}]),
    "text_to_video": (_t2v, [{"prompt": "waves on a cliff"}, {"seed": 2}]),
    "tts": (_tts, [{"text": "Il était une fois un bateau"}, {"voice_id": "other"}, {"language": "en"}]),
    "music": (_music, [{"brief": "tense drone"}, {"seed": 2}]),
    "sfx": (_sfx, [{"brief": "glass break"}, {"seed": 2}]),
    "upscale": (_upscale, [{"width": 480, "height": 640}, {"video": "video2"}]),
    "interpolate": (_interpolate, [{"fps": 50}, {"video": "video2"}]),
    "lip_sync": (_lipsync, [{"audio": "audio2"}, {"video": "video2"}]),
}


def _stable(metadata: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metadata.items() if k != "transcript_path"}


@media
@pytest.mark.parametrize("name", sorted(CASES))
def test_same_input_gives_the_same_bytes(name: str, sources: dict[str, Path], tmp_path: Path) -> None:
    call, _ = CASES[name]
    first = call(sources, tmp_path / "one", {})
    second = call(sources, tmp_path / "two", {})
    assert first.path.is_file() and second.path.is_file()
    assert sha(first.path) == sha(second.path)
    assert _stable(first.metadata) == _stable(second.metadata)
    assert first.media_type == second.media_type


@media
@pytest.mark.parametrize("font", ["system", "none"])
@pytest.mark.parametrize("name", sorted(CASES))
def test_different_inputs_give_different_bytes(
    name: str, font: str, sources: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if font == "none":  # no label: only the derived colour, frequency or seed can tell two inputs apart
        monkeypatch.setenv(ffmpeg.FONT_ENV, "none")
    call, variants = CASES[name]
    hashes = [sha(call(sources, tmp_path / "base", {}).path)]
    for i, overrides in enumerate(variants):
        hashes.append(sha(call(sources, tmp_path / f"variant{i}", overrides).path))
    assert len(set(hashes)) == len(hashes), f"{name}: {variants}"


@media
@pytest.mark.parametrize("name", sorted(CASES))
def test_results_are_labelled_mock_and_cost_no_gpu(name: str, sources: dict[str, Path], tmp_path: Path) -> None:
    call, _ = CASES[name]
    result = call(sources, tmp_path, {})
    assert result.gpu_seconds == 0.0
    assert result.metadata["mock"] is True
    assert "mock" in result.metadata["adapter_id"]
    expected = {".png": "image/png", ".mp4": "video/mp4", ".wav": "audio/wav"}[result.path.suffix]
    assert result.media_type == expected


# ------------------------------------------------------------------ outputs have the requested shape


@media
def test_visual_mocks_render_the_requested_format(sources: dict[str, Path], tmp_path: Path) -> None:
    image = qa.probe(_t2i(sources, tmp_path, {}).path)
    assert (image.width, image.height, image.video_codec) == (320, 180, "png")
    shot = MockTextToVideo().generate("hook", width=1080, height=1920, duration_s=2.0, fps=30, seed=3, out=tmp_path / "s.mp4")
    assert qa.check_render(shot.path, 1080, 1920, 30, 2.0) == ["no_audio: the file has no audio track"]
    animated = qa.probe(_i2v(sources, tmp_path, {}).path)
    assert (animated.width, animated.height, animated.fps_num, animated.constant_frame_rate) == (320, 180, 24, True)
    assert animated.duration_s == pytest.approx(1.0, abs=1e-6)


@media
def test_video_transform_mocks(sources: dict[str, Path], tmp_path: Path) -> None:
    up = qa.probe(MockUpscaler().upscale(sources["video"], width=1080, height=1920, out=tmp_path / "up.mp4").path)
    assert (up.width, up.height, up.fps_num, up.constant_frame_rate) == (1080, 1920, 30, True)
    assert up.duration_s == pytest.approx(1.0, abs=1e-6)
    fast = qa.probe(_interpolate(sources, tmp_path, {}).path)
    assert (fast.width, fast.height, fast.fps_num, fast.constant_frame_rate) == (320, 240, 60, True)
    assert fast.duration_s == pytest.approx(1.0, abs=1e-6)
    synced = qa.probe(_lipsync(sources, tmp_path, {}).path)
    assert synced.has_video and synced.has_audio
    assert synced.duration_s == pytest.approx(1.0, abs=0.03)


@media
def test_audio_mocks_last_exactly_the_requested_time(sources: dict[str, Path], tmp_path: Path) -> None:
    assert wav_seconds(_music(sources, tmp_path, {}).path) == 1.5
    assert wav_seconds(_sfx(sources, tmp_path, {}).path) == 0.5


@media
@pytest.mark.parametrize(
    ("text", "wpm", "seconds"),
    [
        ("one two three four five six seven eight", 160.0, 3.0),  # 8 words / (160/60)
        ("un deux trois quatre cinq", 120.0, 2.5),
        ("  spaced\tout \n words  ", 160.0, 1.125),
    ],
)
def test_tts_duration_is_words_divided_by_rate(tmp_path: Path, text: str, wpm: float, seconds: float) -> None:
    tts = MockTextToSpeech(words_per_minute=wpm)
    assert tts.duration_for(text) == seconds
    result = tts.speak(text, voice_id="narrator", language="fr", out=tmp_path / "v.wav")
    assert wav_seconds(result.path) == seconds
    assert result.metadata["duration_s"] == seconds
    assert result.metadata["words"] == len(text.split())
    assert transcript_sidecar(result.path).read_text(encoding="utf-8") == text


def test_tts_refuses_empty_text_and_bad_rates(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no words"):
        MockTextToSpeech().speak(" \n\t", voice_id="v", language="fr", out=tmp_path / "v.wav")
    assert list(tmp_path.iterdir()) == []
    for rate in (0.0, -160.0):
        with pytest.raises(ValueError):
            MockTextToSpeech(words_per_minute=rate)


@media
def test_transcriber_returns_exactly_what_tts_said(tmp_path: Path) -> None:
    text = "Là-bas, l'été dernier : 42 % des « vidéos » ont… disparu !"
    spoken = MockTextToSpeech().speak(text, voice_id="narrator", language="fr", out=tmp_path / "scene.wav")
    transcript = MockTranscriber().transcribe(spoken.path, language="fr")
    assert transcript.text == text
    assert transcript.language == "fr"
    assert [w for w, _, _ in transcript.words] == text.split()
    assert transcript.words[0][1] == 0.0
    for (_, _, end), (_, start, _) in zip(transcript.words, transcript.words[1:], strict=False):
        assert end == start
    assert transcript.words[-1][2] == pytest.approx(spoken.metadata["duration_s"], abs=0.002)


@media
def test_transcriber_refuses_audio_it_cannot_know(sources: dict[str, Path]) -> None:
    with pytest.raises(MockTranscriptMissing, match="audio.wav.txt"):
        MockTranscriber().transcribe(sources["audio"], language="fr")


def test_vision_critic_verdicts(tmp_path: Path) -> None:
    frame = tmp_path / "f1.png"
    frame.write_bytes(b"\x89PNG not empty")
    empty = tmp_path / "f2.png"
    empty.write_bytes(b"")
    critic = MockVisionCritic()
    ok = critic.critique([frame], "a calm harbour")
    assert (ok.blocking, ok.defects) == (False, ())
    assert "mock" in ok.regeneration_hint
    assert critic.critique([frame], "a calm harbour") == ok

    missing = critic.critique([frame, tmp_path / "gone.png", empty], "a calm harbour")
    assert missing.blocking is True
    assert len(missing.defects) == 2 and "gone.png" in missing.defects[0] and "f2.png" in missing.defects[1]
    assert all("mock" in d for d in missing.defects)

    assert critic.critique([], "anything").blocking is True
    flagged = critic.critique([frame], "harbour [mock-defect] melting hands")
    assert flagged.blocking is True and "mock-defect" in flagged.defects[0]
    custom = MockVisionCritic(defect_marker="#bad")
    assert custom.critique([frame], "harbour [mock-defect]").blocking is False
    assert custom.critique([frame], "harbour #bad").blocking is True


# ------------------------------------------------------------------ concurrency


@media
def test_parallel_mocks_match_sequential_results(tmp_path: Path) -> None:
    texts = [f"scene number {i} says {' '.join(['word'] * (i + 1))}" for i in range(8)]
    tts = MockTextToSpeech()
    sequential = [
        sha(tts.speak(t, voice_id="v", language="en", out=tmp_path / "seq" / f"{i}.wav").path) for i, t in enumerate(texts)
    ]
    barrier = threading.Barrier(8)

    def speak(i: int) -> str:
        barrier.wait()
        return sha(tts.speak(texts[i], voice_id="v", language="en", out=tmp_path / "par" / f"{i}.wav").path)

    with ThreadPoolExecutor(max_workers=8) as pool:
        parallel = list(pool.map(speak, range(8)))
    assert parallel == sequential
    assert len(set(sequential)) == 8


@media
def test_concurrent_writers_of_one_output_leave_one_valid_file(tmp_path: Path) -> None:
    reference = sha(
        MockTextToVideo().generate("x", width=160, height=120, duration_s=0.5, fps=10, seed=4, out=tmp_path / "r.mp4").path
    )
    out = tmp_path / "shared" / "shot.mp4"
    barrier = threading.Barrier(6)

    def render(_: int) -> str:
        barrier.wait()
        return sha(MockTextToVideo().generate("x", width=160, height=120, duration_s=0.5, fps=10, seed=4, out=out).path)

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert set(pool.map(render, range(6))) == {reference}
    assert sha(out) == reference
    assert [p.name for p in out.parent.iterdir()] == ["shot.mp4"]


# ------------------------------------------------------------------ registry


def _spec(adapter_id: str, kind: AdapterKind, **changes: Any) -> AdapterSpec:
    return dataclasses.replace(mock_spec("mock-template", kind), id=adapter_id, **changes)


class MockCandidateUpscaler:
    """Test double standing for a real local adapter (candidate status, no `mock` in its id)."""

    def __init__(self, adapter_id: str = "seedvr2-candidate", **changes: Any) -> None:
        changes.setdefault("status", AdapterStatus.CANDIDATE)
        self.spec = _spec(adapter_id, AdapterKind.UPSCALE, **changes)

    def upscale(self, video: Path, *, width: int, height: int, out: Path) -> MediaResult:
        raise NotImplementedError


class MockLLMRunnerDouble:
    def __init__(self) -> None:
        self.spec = _spec("mock-llm-double", AdapterKind.LLM)

    def run(
        self,
        *,
        agent: str,
        prompt: str,
        model: str,
        json_schema: dict[str, Any] | None,
        max_turns: int,
        allowed_tools: Sequence[str],
        cwd: Path,
    ) -> LLMResult:
        return LLMResult(output="mock", usage=LLMUsage(), session_id="mock-session")


class MockMislabelled:
    """Claims to be a TTS but only implements the text-to-image method."""

    def __init__(self) -> None:
        self.spec = _spec("mock-mislabelled", AdapterKind.TTS)

    def generate(self, prompt: str, *, width: int, height: int, seed: int, out: Path) -> MediaResult:
        raise NotImplementedError


class MockImageAsVideo:
    """A text-to-image adapter declared as text-to-video: same method name, different signature."""

    def __init__(self) -> None:
        self.spec = _spec("mock-image-as-video", AdapterKind.TEXT_TO_VIDEO)

    def generate(self, prompt: str, *, width: int, height: int, seed: int, out: Path) -> MediaResult:
        raise NotImplementedError


class MockExtendedTextToVideo:
    """Extra optional parameters and a different positional order of keywords are fine."""

    def __init__(self) -> None:
        self.spec = _spec("mock-extended-t2v", AdapterKind.TEXT_TO_VIDEO)

    def generate(
        self,
        prompt: str,
        *,
        out: Path,
        seed: int,
        fps: int,
        duration_s: float,
        height: int,
        width: int,
        negative_prompt: str = "",
    ) -> MediaResult:
        raise NotImplementedError


class MockTtsWithRequiredExtra:
    def __init__(self) -> None:
        self.spec = _spec("mock-tts-extra", AdapterKind.TTS)

    def speak(self, text: str, *, voice_id: str, language: str, out: Path, emotion: str) -> MediaResult:
        raise NotImplementedError


class MockWithoutSpec:
    def speak(self, text: str, *, voice_id: str, language: str, out: Path) -> MediaResult:
        raise NotImplementedError


def test_default_mocks_cover_every_media_kind_with_fresh_instances() -> None:
    mocks = registry.default_mocks()
    assert set(mocks) == set(AdapterKind) - {AdapterKind.LLM}
    for kind, adapter in mocks.items():
        assert adapter.spec.kind is kind
        assert isinstance(adapter, registry.PROTOCOLS[kind])
    again = registry.default_mocks()
    assert all(again[k] is not mocks[k] for k in mocks)


def test_default_registry_serves_every_mock_by_id() -> None:
    reg = registry.default_registry()
    assert reg.kinds() == sorted(AdapterKind)  # every kind, the LLM included
    for kind, adapter in registry.default_mocks().items():
        spec: AdapterSpec = adapter.spec
        assert reg.ids(kind) == [spec.id]
        assert type(reg.get(kind, spec.id)) is type(adapter)
    assert reg.ids(AdapterKind.LLM) == [MOCK_LLM_ID] == ["mock-llm"]


def test_unknown_adapter_is_a_clear_error() -> None:
    reg = registry.default_registry()
    with pytest.raises(AdapterNotFound, match="mock-tts"):
        reg.get(AdapterKind.TTS, "qwen3-tts")
    with pytest.raises(AdapterNotFound, match="mock-llm"):  # the message lists what is registered
        reg.get(AdapterKind.LLM, "claude-code")
    with pytest.raises(AdapterNotFound):
        reg.get(AdapterKind.MUSIC, "mock-tts")  # an id is looked up within its kind only
    with pytest.raises(AdapterNotFound, match="none"):
        AdapterRegistry().get(AdapterKind.LLM, "mock-llm")


def test_the_llm_mock_is_in_the_default_registry_of_a_fresh_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Steps ask the registry for `mock-llm` and never import the adapter: it must be there from the start."""
    reg = registry.default_registry()
    llm = reg.get(AdapterKind.LLM, "mock-llm")
    assert isinstance(llm, MockLLMRunner) and isinstance(llm, LLMRunner)
    assert llm.spec.is_mock and llm.spec.status is AdapterStatus.MOCK
    assert registry.default_registry().get(AdapterKind.LLM, "mock-llm") is not llm  # fresh instances, as the media mocks
    monkeypatch.setattr(registry, "_default", None)  # the process-wide registry, built on first use
    assert isinstance(registry.get(AdapterKind.LLM, "mock-llm"), MockLLMRunner)
    code = (
        "from studio.adapters import registry; from studio.domain import AdapterKind; "
        "print(type(registry.get(AdapterKind.LLM, 'mock-llm')).__name__)"
    )
    child = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, timeout=120, check=False)
    assert (child.returncode, child.stdout.strip()) == (0, "MockLLMRunner"), child.stderr


def test_module_level_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "_default", None)
    tts = registry.get(AdapterKind.TTS, "mock-tts")
    assert isinstance(tts, MockTextToSpeech)
    assert registry.get(AdapterKind.TTS, "mock-tts") is tts  # one process-wide registry
    llm = MockLLMRunnerDouble()
    registry.register(llm)
    assert registry.get(AdapterKind.LLM, "mock-llm-double") is llm
    candidate = MockCandidateUpscaler()
    registry.register(candidate)
    assert registry.get(AdapterKind.UPSCALE, "seedvr2-candidate") is candidate
    assert registry.get(AdapterKind.UPSCALE, "mock-upscale") is not candidate


@pytest.mark.parametrize(
    ("make", "reason"),
    [
        (MockWithoutSpec, "no AdapterSpec"),
        (MockMislabelled, "does not implement the tts protocol"),
        (MockImageAsVideo, "lacks keyword parameter 'duration_s'"),
        (MockTtsWithRequiredExtra, "unexpected parameter 'emotion'"),
        (lambda: MockCandidateUpscaler("mock-upscale-2"), "a mock must"),  # candidate named like a mock
        (lambda: MockCandidateUpscaler("seedvr2", status=AdapterStatus.MOCK), "a mock must"),  # mock not named mock
        (lambda: MockCandidateUpscaler("hunyuan-upscale", license_class=LicenseClass.REFUSED), "ADR-002"),
        (lambda: MockCandidateUpscaler("topaz", license_class=LicenseClass.CLOSED), "ADR-002"),
    ],
)
def test_registration_rules(make: Callable[[], object], reason: str) -> None:
    reg = AdapterRegistry()
    with pytest.raises(AdapterRejected, match=reason):
        reg.register(make())
    assert reg.kinds() == []


def test_compatible_signatures_are_accepted() -> None:
    reg = AdapterRegistry()
    reg.register(MockExtendedTextToVideo())
    reg.register(MockLLMRunnerDouble())
    for adapter in registry.default_mocks().values():
        reg.register(adapter)
    assert len(reg.kinds()) == len(AdapterKind)


def test_conditional_licences_are_accepted() -> None:
    reg = AdapterRegistry()
    reg.register(MockCandidateUpscaler("ltx2-upscale", license_class=LicenseClass.CONDITIONAL))
    assert reg.ids(AdapterKind.UPSCALE) == ["ltx2-upscale"]


def test_duplicates_are_refused_unless_replaced() -> None:
    reg = AdapterRegistry()
    first, second = MockCandidateUpscaler(), MockCandidateUpscaler()
    reg.register(first)
    with pytest.raises(AdapterRejected, match="already registered"):
        reg.register(second)
    assert reg.get(AdapterKind.UPSCALE, "seedvr2-candidate") is first
    reg.register(second, replace=True)
    assert reg.get(AdapterKind.UPSCALE, "seedvr2-candidate") is second


def test_concurrent_registration_of_one_id_admits_exactly_one() -> None:
    reg = AdapterRegistry()
    candidates = [MockCandidateUpscaler() for _ in range(16)]
    barrier = threading.Barrier(16)

    def attempt(i: int) -> bool:
        barrier.wait()
        try:
            reg.register(candidates[i])
        except AdapterRejected:
            return False
        return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes = list(pool.map(attempt, range(16)))
    assert outcomes.count(True) == 1
    winner = candidates[outcomes.index(True)]
    assert reg.get(AdapterKind.UPSCALE, "seedvr2-candidate") is winner


def test_concurrent_registration_of_distinct_ids_keeps_them_all() -> None:
    reg = AdapterRegistry()
    barrier = threading.Barrier(16)

    def attempt(i: int) -> None:
        barrier.wait()
        reg.register(MockCandidateUpscaler(f"upscaler-{i:02d}"))

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(attempt, range(16)))
    assert reg.ids(AdapterKind.UPSCALE) == [f"upscaler-{i:02d}" for i in range(16)]


# ------------------------------------------------------------------ regressions of the adversarial review


def guard_outcome(available: bool) -> tuple[str, str]:
    """What `require_ffmpeg` does: ("skip" | "fail" | "run", message). A wrong outcome is an assertion failure of the
    caller, never a skipped test (an unexpected Skipped escaping a test would silently skip it)."""
    try:
        require_ffmpeg(available=available)
    except pytest.skip.Exception as exc:
        return "skip", str(exc)
    except pytest.fail.Exception as exc:
        return "fail", str(exc)
    return "run", ""


def test_media_proofs_skip_without_ffmpeg_and_fail_when_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(REQUIRE_MEDIA_ENV, raising=False)
    kind, reason = guard_outcome(available=False)
    assert kind == "skip" and REQUIRE_MEDIA_ENV in reason
    for off in ("", "0", "false", "No", "OFF"):
        monkeypatch.setenv(REQUIRE_MEDIA_ENV, off)
        assert guard_outcome(available=False)[0] == "skip", off
    for on in ("1", "true", "yes", "anything"):  # an unknown value fails closed
        monkeypatch.setenv(REQUIRE_MEDIA_ENV, on)
        kind, reason = guard_outcome(available=False)
        assert kind == "fail" and "mandatory" in reason, on
        assert guard_outcome(available=True)[0] == "run", on


MANDATORY_MOCK_PROOFS = (
    "test_each_mock_satisfies_its_protocol",
    "test_same_input_gives_the_same_bytes",
    "test_different_inputs_give_different_bytes",
    "test_default_tts_speaks_eight_words_in_exactly_three_seconds",
)


def test_mandatory_proofs_are_selected_by_the_media_marker() -> None:
    for name in MANDATORY_MOCK_PROOFS:
        marks = {m.name for m in getattr(globals()[name], "pytestmark", [])}
        assert "media" in marks, name


def test_the_media_marker_collects_the_mandatory_mock_proofs() -> None:
    """`pytest -m media` really lists them, the isinstance proof of every mock included (missing at review time)."""
    cmd = [sys.executable, "-m", "pytest", "tests/unit/test_mock_adapters.py", "-m", "media", "--collect-only", "-q"]
    cmd += ["-o", "addopts=", "-p", "no:cacheprovider"]
    listing = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=300, check=False)
    assert listing.returncode == 0, listing.stdout + listing.stderr
    for name in MANDATORY_MOCK_PROOFS:
        assert f"::{name}" in listing.stdout, name
    assert len(re.findall(r"::test_each_mock_satisfies_its_protocol\[", listing.stdout)) == len(MOCK_CLASSES)


def test_tts_default_rate_is_160_words_per_minute() -> None:
    tts = MockTextToSpeech()
    assert tts.words_per_minute == 160.0
    assert tts.duration_for("one two three four five six seven eight") == 3.0


@media
def test_default_tts_speaks_eight_words_in_exactly_three_seconds(tmp_path: Path) -> None:
    text = "one two three four five six seven eight"
    result = MockTextToSpeech().speak(text, voice_id="narrator", language="en", out=tmp_path / "v.wav")
    assert wav_seconds(result.path) == 3.0
    assert result.metadata["words_per_minute"] == 160.0
    assert result.metadata["duration_s"] == 3.0


class MockRenderer:
    """Stands in for the ffmpeg renderers: records the colour each visual mock asks for, renders nothing."""

    def __init__(self) -> None:
        self.colors: list[str] = []

    def still_image(self, out: Path, width: int, height: int, color: str, label: str | None = None) -> Path:
        self.colors.append(color)
        return out

    def image_clip(self, out: Path, image: Path, duration_s: float, fps: float, **kw: Any) -> Path:
        self.colors.append(kw["band_color"])
        return out

    def color_clip(
        self, out: Path, width: int, height: int, fps: float, duration_s: float, color: str, label: str | None = None
    ) -> Path:
        self.colors.append(color)
        return out


VisualCall = Callable[[str, int, Path], MediaResult]
VISUAL: dict[str, tuple[VisualCall, str]] = {
    "text_to_image": (
        lambda prompt, seed, d: MockTextToImage().generate(prompt, width=64, height=64, seed=seed, out=d / "i.png"),
        "color",
    ),
    "image_to_video": (
        lambda prompt, seed, d: MockImageToVideo().animate(
            d / "src.png", prompt, duration_s=1.0, fps=24, seed=seed, out=d / "v.mp4"
        ),
        "band_color",
    ),
    "text_to_video": (
        lambda prompt, seed, d: MockTextToVideo().generate(
            prompt, width=64, height=64, duration_s=1.0, fps=30, seed=seed, out=d / "v.mp4"
        ),
        "color",
    ),
}


@pytest.mark.parametrize("name", sorted(VISUAL))
def test_visual_mock_colour_derives_from_the_prompt_and_the_seed(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ffmpeg: a label drawn with the prompt must not be what tells two prompts apart."""
    renderer = MockRenderer()
    for fn in ("still_image", "image_clip", "color_clip"):
        monkeypatch.setattr(ffmpeg, fn, getattr(renderer, fn))
    call, key = VISUAL[name]
    results = [
        call("a lighthouse at dusk", 1, tmp_path),
        call("a lighthouse at dusk", 1, tmp_path),
        call("a lighthouse at dawn", 1, tmp_path),  # only the prompt changes
        call("a lighthouse at dusk", 2, tmp_path),  # only the seed changes
    ]
    colors = [r.metadata[key] for r in results]
    assert renderer.colors == colors  # the renderer receives the colour the metadata reports
    assert colors[0] == colors[1]
    assert colors[2] != colors[0]
    assert colors[3] != colors[0]
    assert all(len(c) == 7 and c.startswith("#") for c in colors)


@media
def test_concurrent_speakers_of_one_path_leave_a_matching_transcript(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "voice.wav"
    short, long = "two words", "this sentence has exactly eight words in it"
    entered = threading.Event()
    real_write = mock._write_text_atomic

    def mock_slow_sidecar_writer(path: Path, text: str) -> None:
        if text == short:
            entered.set()  # the short text's audio is already in place
            time.sleep(1.0)
        real_write(path, text)

    monkeypatch.setattr(mock, "_write_text_atomic", mock_slow_sidecar_writer)
    tts = MockTextToSpeech()
    first = threading.Thread(target=tts.speak, args=(short,), kwargs={"voice_id": "v", "language": "en", "out": out})
    first.start()
    assert entered.wait(30)
    tts.speak(long, voice_id="v", language="en", out=out)
    first.join()
    transcript = MockTranscriber().transcribe(out, language="en")
    assert wav_seconds(out) == tts.duration_for(transcript.text)  # audio and transcript come from one call
    assert transcript.text == long


@media
def test_transcriber_waits_for_a_writer_of_the_same_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The reading side of the pair: a transcription never mixes the new audio with the previous text."""
    out = tmp_path / "voice.wav"
    tts = MockTextToSpeech()
    tts.speak("two words", voice_id="v", language="en", out=out)  # the previous version, on disk
    long = "this sentence has exactly eight words in it"
    entered = threading.Event()
    real_write = mock._write_text_atomic

    def mock_slow_sidecar_writer(path: Path, text: str) -> None:
        entered.set()  # the new audio is already in place, the new text is not
        time.sleep(1.0)
        real_write(path, text)

    monkeypatch.setattr(mock, "_write_text_atomic", mock_slow_sidecar_writer)
    writer = threading.Thread(target=tts.speak, args=(long,), kwargs={"voice_id": "v", "language": "en", "out": out})
    writer.start()
    assert entered.wait(30)
    transcript = MockTranscriber().transcribe(out, language="en")
    writer.join()
    assert transcript.text == long
    assert transcript.words[-1][2] == pytest.approx(tts.duration_for(long), abs=0.002)


@media
def test_mock_outputs_with_a_percent_in_their_name(tmp_path: Path) -> None:
    image = MockTextToImage().generate("a fox", width=64, height=64, seed=1, out=tmp_path / "shot_%03d.png")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["shot_%03d.png"]
    clip = MockImageToVideo().animate(image.path, "pan", duration_s=0.5, fps=10, seed=1, out=tmp_path / "clip_%d.mp4")
    assert qa.probe(clip.path).duration_s == pytest.approx(0.5, abs=1e-6)
