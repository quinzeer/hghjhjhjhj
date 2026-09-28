"""Adapter contracts (MISSION §6.3). Every local model or renderer sits behind one of these protocols and
declares its specification; mocks implement the same protocols and carry `mock` in their name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from studio.domain import AdapterKind, AdapterStatus, LicenseClass


@dataclass(frozen=True)
class AdapterSpec:
    """What an adapter declares (MISSION §6.3). Values are measured by `make bench-models`, never guessed."""

    id: str  # e.g. "mock-text-to-image", "wan22-ti2v-5b"
    kind: AdapterKind
    vram_gb: float | None  # None = not measured yet
    gpu_seconds_per_output_second: float | None
    max_width: int | None
    max_height: int | None
    max_duration_s: float | None
    license_class: LicenseClass
    license_url: str
    status: AdapterStatus

    @property
    def is_mock(self) -> bool:
        return self.status is AdapterStatus.MOCK or "mock" in self.id


@dataclass(frozen=True)
class MediaResult:
    path: Path
    media_type: str
    gpu_seconds: float  # measured (0 for CPU-only mocks)
    metadata: dict[str, Any]


@runtime_checkable
class TextToImage(Protocol):
    spec: AdapterSpec

    def generate(self, prompt: str, *, width: int, height: int, seed: int, out: Path) -> MediaResult: ...


@runtime_checkable
class ImageToVideo(Protocol):
    spec: AdapterSpec

    def animate(self, image: Path, prompt: str, *, duration_s: float, fps: int, seed: int, out: Path) -> MediaResult: ...


@runtime_checkable
class TextToVideo(Protocol):
    spec: AdapterSpec

    def generate(
        self, prompt: str, *, width: int, height: int, duration_s: float, fps: int, seed: int, out: Path
    ) -> MediaResult: ...


@runtime_checkable
class TextToSpeech(Protocol):
    spec: AdapterSpec

    def speak(self, text: str, *, voice_id: str, language: str, out: Path) -> MediaResult: ...


@runtime_checkable
class MusicGenerator(Protocol):
    spec: AdapterSpec

    def compose(self, brief: str, *, duration_s: float, seed: int, out: Path) -> MediaResult: ...


@runtime_checkable
class SoundEffects(Protocol):
    spec: AdapterSpec

    def effect(self, brief: str, *, duration_s: float, seed: int, out: Path) -> MediaResult: ...


@runtime_checkable
class Upscaler(Protocol):
    spec: AdapterSpec

    def upscale(self, video: Path, *, width: int, height: int, out: Path) -> MediaResult: ...


@runtime_checkable
class Interpolator(Protocol):
    spec: AdapterSpec

    def interpolate(self, video: Path, *, fps: int, out: Path) -> MediaResult: ...


@runtime_checkable
class LipSync(Protocol):
    spec: AdapterSpec

    def sync(self, video: Path, audio: Path, *, out: Path) -> MediaResult: ...


@dataclass(frozen=True)
class Transcript:
    text: str
    words: tuple[tuple[str, float, float], ...]  # (word, start_s, end_s)
    language: str


@runtime_checkable
class Transcriber(Protocol):
    spec: AdapterSpec

    def transcribe(self, audio: Path, *, language: str) -> Transcript: ...


@dataclass(frozen=True)
class CritiqueResult:
    blocking: bool
    defects: tuple[str, ...]
    regeneration_hint: str


@runtime_checkable
class VisionCritic(Protocol):
    spec: AdapterSpec

    def critique(self, frames: list[Path], shot_brief: str) -> CritiqueResult: ...
