"""Deterministic mocks of every media adapter protocol (docs/design/phase1.md, MISSION §3.2).

Each mock renders a real file with ffmpeg (so the pipeline, QA and ffprobe run for real) and costs no GPU
time. Outputs are a pure function of the inputs and of the render environment: colours, frequencies and
noise seeds come from the SHA-256 of the prompt (or text) and the seed, so the same call under the same
`ffmpeg.media_fingerprint()` gives the same bytes and a different prompt or seed gives different bytes.
Every id and spec carries `mock`, and every result's metadata says `"mock": True`.
"""

from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from studio.adapters.base import AdapterSpec, CritiqueResult, MediaResult, Transcript
from studio.core.interfaces import StudioError
from studio.domain import AdapterKind, AdapterStatus, LicenseClass, canonical_json, sha256_hex
from studio.media import ffmpeg
from studio.media.qa import probe

MOCK_LICENSE_URL = "n/a (mock)"
DEFAULT_WORDS_PER_MINUTE = 160.0
DEFECT_MARKER = "[mock-defect]"


class MockTranscriptMissing(StudioError):
    """The mock transcriber only understands audio made by MockTextToSpeech (it reads its sidecar)."""


def mock_spec(adapter_id: str, kind: AdapterKind) -> AdapterSpec:
    """Spec of a mock: accepted licence, mock status, no measured figure (nothing to measure)."""
    if "mock" not in adapter_id:
        raise ValueError(f"a mock id must contain 'mock': {adapter_id!r}")
    return AdapterSpec(
        id=adapter_id,
        kind=kind,
        vram_gb=None,
        gpu_seconds_per_output_second=None,
        max_width=None,
        max_height=None,
        max_duration_s=None,
        license_class=LicenseClass.ACCEPTED,
        license_url=MOCK_LICENSE_URL,
        status=AdapterStatus.MOCK,
    )


def derive_digest(adapter_id: str, **inputs: Any) -> bytes:
    """SHA-256 of the canonical JSON of an adapter's inputs: the only source of variation of a mock."""
    return bytes.fromhex(sha256_hex(canonical_json({"adapter": adapter_id, **inputs})))


def derive_color(digest: bytes) -> str:
    """Mid-range colour (each channel in 40..215) so a white label stays readable."""
    return "#" + "".join(f"{40 + b % 176:02x}" for b in digest[:3])


def derive_frequency(digest: bytes, low_hz: float, high_hz: float) -> float:
    """Frequency in [low_hz, high_hz) on a 0.01 Hz grid."""
    steps = max(1, int(round((high_hz - low_hz) * 100)))
    return round(low_hz + (int.from_bytes(digest[3:7], "big") % steps) / 100, 2)


def transcript_sidecar(audio: Path) -> Path:
    """Text file written next to a MockTextToSpeech output (`voice.wav` → `voice.wav.txt`)."""
    audio = Path(audio)
    return audio.with_name(audio.name + ".txt")


# Striped locks pairing a TTS output with its transcript sidecar: the audio and the text are two files, so
# a writer and a reader of the same path hold the same lock (a bounded set, whatever the number of paths).
_PAIR_LOCKS: tuple[threading.Lock, ...] = tuple(threading.Lock() for _ in range(64))


def _pair_lock(audio: Path) -> threading.Lock:
    return _PAIR_LOCKS[hash(os.path.normcase(os.path.abspath(audio))) % len(_PAIR_LOCKS)]


def _media_type(out: Path) -> str:
    return {
        ".png": "image/png",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
    }.get(Path(out).suffix.lower(), "application/octet-stream")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.partial-{uuid.uuid4().hex[:12]}")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


class _MockAdapter:
    adapter_id: str
    kind: AdapterKind

    def __init__(self) -> None:
        self.spec = mock_spec(self.adapter_id, self.kind)

    def _result(self, path: Path, **metadata: Any) -> MediaResult:
        return MediaResult(
            path=Path(path),
            media_type=_media_type(path),
            gpu_seconds=0.0,
            metadata={"mock": True, "adapter_id": self.spec.id, **metadata},
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.spec.id!r})"


class MockTextToImage(_MockAdapter):
    adapter_id = "mock-text-to-image"
    kind = AdapterKind.TEXT_TO_IMAGE

    def generate(self, prompt: str, *, width: int, height: int, seed: int, out: Path) -> MediaResult:
        color = derive_color(derive_digest(self.adapter_id, prompt=prompt, seed=seed))
        ffmpeg.still_image(out, width, height, color, label=prompt)
        return self._result(out, color=color, seed=seed, width=width, height=height)


class MockImageToVideo(_MockAdapter):
    adapter_id = "mock-image-to-video"
    kind = AdapterKind.IMAGE_TO_VIDEO

    def animate(self, image: Path, prompt: str, *, duration_s: float, fps: int, seed: int, out: Path) -> MediaResult:
        color = derive_color(derive_digest(self.adapter_id, prompt=prompt, seed=seed))
        ffmpeg.image_clip(out, image, duration_s, fps, band_color=color, label=prompt)
        return self._result(out, band_color=color, seed=seed, duration_s=duration_s, fps=fps)


class MockTextToVideo(_MockAdapter):
    adapter_id = "mock-text-to-video"
    kind = AdapterKind.TEXT_TO_VIDEO

    def generate(self, prompt: str, *, width: int, height: int, duration_s: float, fps: int, seed: int, out: Path) -> MediaResult:
        color = derive_color(derive_digest(self.adapter_id, prompt=prompt, seed=seed))
        ffmpeg.color_clip(out, width, height, fps, duration_s, color, label=prompt)
        return self._result(out, color=color, seed=seed, width=width, height=height, duration_s=duration_s, fps=fps)


class MockTextToSpeech(_MockAdapter):
    """A tone lasting words ÷ (words_per_minute / 60), plus a sidecar with the text for MockTranscriber.

    Within a process, the audio and its sidecar are replaced together: concurrent calls on one `out`
    never leave the audio of one text next to the transcript of another."""

    adapter_id = "mock-tts"
    kind = AdapterKind.TTS

    def __init__(self, words_per_minute: float = DEFAULT_WORDS_PER_MINUTE) -> None:
        if not words_per_minute > 0:
            raise ValueError(f"words_per_minute must be > 0, got {words_per_minute!r}")
        super().__init__()
        self.words_per_minute = float(words_per_minute)

    def duration_for(self, text: str) -> float:
        return len(text.split()) * 60.0 / self.words_per_minute

    def speak(self, text: str, *, voice_id: str, language: str, out: Path) -> MediaResult:
        words = text.split()
        if not words:
            raise ValueError("nothing to say: the text has no words")
        duration = self.duration_for(text)
        digest = derive_digest(self.adapter_id, text=text, voice_id=voice_id, language=language)
        freq = derive_frequency(digest, 110.0, 330.0)
        sidecar = transcript_sidecar(out)
        with _pair_lock(out):
            ffmpeg.tone(out, duration, freq, amplitude=0.2)
            _write_text_atomic(sidecar, text)
        return self._result(
            out,
            freq_hz=freq,
            words=len(words),
            words_per_minute=self.words_per_minute,
            duration_s=duration,
            voice_id=voice_id,
            language=language,
            transcript_path=str(sidecar),
        )


class MockMusicGenerator(_MockAdapter):
    adapter_id = "mock-music"
    kind = AdapterKind.MUSIC

    def compose(self, brief: str, *, duration_s: float, seed: int, out: Path) -> MediaResult:
        root = derive_frequency(derive_digest(self.adapter_id, brief=brief, seed=seed), 80.0, 160.0)
        freqs = [root, round(root * 1.5, 2), round(root * 2, 2)]  # root, fifth, octave
        ffmpeg.chord(out, duration_s, freqs, amplitude=0.2)
        return self._result(out, freqs_hz=freqs, seed=seed, duration_s=duration_s)


class MockSoundEffects(_MockAdapter):
    adapter_id = "mock-sfx"
    kind = AdapterKind.SFX

    def effect(self, brief: str, *, duration_s: float, seed: int, out: Path) -> MediaResult:
        digest = derive_digest(self.adapter_id, brief=brief, seed=seed)
        noise_seed = int.from_bytes(digest[:4], "big")
        color = ("white", "pink", "brown")[digest[4] % 3]
        ffmpeg.noise(out, duration_s, noise_seed, color=color, amplitude=0.25)
        return self._result(out, noise_seed=noise_seed, noise_color=color, seed=seed, duration_s=duration_s)


class MockUpscaler(_MockAdapter):
    adapter_id = "mock-upscale"
    kind = AdapterKind.UPSCALE

    def upscale(self, video: Path, *, width: int, height: int, out: Path) -> MediaResult:
        src = probe(video)
        ffmpeg.scale_pad(out, video, width, height, Fraction(src.fps_num, src.fps_den))
        return self._result(out, width=width, height=height, source=f"{src.width}x{src.height}")


class MockInterpolator(_MockAdapter):
    adapter_id = "mock-interpolate"
    kind = AdapterKind.INTERPOLATE

    def interpolate(self, video: Path, *, fps: int, out: Path) -> MediaResult:
        src = probe(video)
        ffmpeg.scale_pad(out, video, src.width, src.height, fps)
        return self._result(out, fps=fps, source_fps=f"{src.fps_num}/{src.fps_den}")


class MockLipSync(_MockAdapter):
    adapter_id = "mock-lip-sync"
    kind = AdapterKind.LIP_SYNC

    def sync(self, video: Path, audio: Path, *, out: Path) -> MediaResult:
        ffmpeg.mux(out, video, audio)
        return self._result(out)


class MockTranscriber(_MockAdapter):
    """Returns the exact text MockTextToSpeech spoke, words spread evenly over the audio's duration."""

    adapter_id = "mock-transcribe"
    kind = AdapterKind.TRANSCRIBE

    def transcribe(self, audio: Path, *, language: str) -> Transcript:
        sidecar = transcript_sidecar(audio)
        with _pair_lock(audio):
            if not sidecar.is_file():
                raise MockTranscriptMissing(f"{audio}: no {sidecar.name} (only MockTextToSpeech output can be transcribed)")
            text = sidecar.read_text(encoding="utf-8")
            duration = probe(audio).duration_s
        tokens = text.split()
        step = duration / len(tokens) if tokens else 0.0
        words = tuple((w, round(i * step, 3), round((i + 1) * step, 3)) for i, w in enumerate(tokens))
        return Transcript(text=text, words=words, language=language)


class MockVisionCritic(_MockAdapter):
    """Blocks when frames are missing or empty, or when the brief carries `defect_marker`; passes otherwise."""

    adapter_id = "mock-vision-critic"
    kind = AdapterKind.VISION_CRITIC

    def __init__(self, defect_marker: str = DEFECT_MARKER) -> None:
        super().__init__()
        self.defect_marker = defect_marker

    def critique(self, frames: Sequence[Path], shot_brief: str) -> CritiqueResult:
        defects: list[str] = []
        if not frames:
            defects.append("mock: no frame to critique")
        for frame in frames:
            path = Path(frame)
            if not path.is_file() or path.stat().st_size == 0:
                defects.append(f"mock: frame {path.name} is missing or empty")
        if self.defect_marker and self.defect_marker in shot_brief:
            defects.append(f"mock: defect requested by the brief marker {self.defect_marker}")
        if defects:
            return CritiqueResult(blocking=True, defects=tuple(defects), regeneration_hint="mock: regenerate the shot")
        return CritiqueResult(blocking=False, defects=(), regeneration_hint="mock: no visual analysis performed")


MOCK_CLASSES: tuple[type[_MockAdapter], ...] = (
    MockTextToImage,
    MockImageToVideo,
    MockTextToVideo,
    MockTextToSpeech,
    MockMusicGenerator,
    MockSoundEffects,
    MockUpscaler,
    MockInterpolator,
    MockLipSync,
    MockTranscriber,
    MockVisionCritic,
)
