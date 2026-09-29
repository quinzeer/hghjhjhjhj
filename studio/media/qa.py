"""Technical checks of a render (MISSION §8): resolution, constant frame rate, duration, tracks, loudness.

`check_render` returns a list of defects; an empty list means the file is compliant. Each defect starts
with a stable code (`resolution:`, `frame_rate:`, `variable_frame_rate:`, `duration:`, `no_video:`,
`no_audio:`, `loudness:`, `true_peak:`, `unreadable:`) followed by a human-readable explanation.
A broken environment is not a defect of the file: a missing ffmpeg/ffprobe (`MediaToolMissing`) or a
timeout (`FFmpegError` with `returncode is None`) propagates, so a compliant render is never condemned
(and regenerated) because of the machine that checked it.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from studio.media.ffmpeg import (
    FFmpegError,
    MediaError,
    MediaToolMissing,
    ffprobe_json,
    frame_spacing_is_uniform,
    measure_loudness,
    stream_fps,
)

FPS_TOLERANCE = 0.01
PROBE_TIMEOUT_S = 60.0


@dataclass(frozen=True)
class ProbeResult:
    path: Path
    width: int  # 0 without a video track
    height: int
    fps_num: int  # 0/1 without a video track
    fps_den: int
    # r_frame_rate == avg_frame_rate AND every frame timestamp 1/fps after the previous one (to one tick)
    constant_frame_rate: bool
    duration_s: float  # container duration (0.0 when unknown, e.g. a still image)
    has_video: bool
    has_audio: bool
    video_codec: str | None
    audio_codec: str | None
    pix_fmt: str | None = None
    sample_rate: int | None = None
    channels: int | None = None

    @property
    def fps(self) -> float:
        return self.fps_num / self.fps_den if self.fps_den else 0.0


def _duration(info: dict[str, Any]) -> float:
    raw = info.get("format", {}).get("duration")
    if raw not in (None, "N/A"):
        return float(raw)
    streams = [float(s["duration"]) for s in info.get("streams", []) if s.get("duration") not in (None, "N/A")]
    return max(streams, default=0.0)


def probe(path: Path, *, timeout_s: float | None = None) -> ProbeResult:
    """Describe the first video track (cover art excluded) and the first audio track of `path`."""
    info = ffprobe_json(Path(path), timeout_s=PROBE_TIMEOUT_S if timeout_s is None else timeout_s)
    streams: list[dict[str, Any]] = info.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    v = videos[0] if videos else None
    a = audios[0] if audios else None
    fps = stream_fps(v) if v is not None else Fraction(0)
    return ProbeResult(
        path=Path(path),
        width=int(v.get("width", 0)) if v is not None else 0,
        height=int(v.get("height", 0)) if v is not None else 0,
        fps_num=fps.numerator if v is not None else 0,
        fps_den=fps.denominator if v is not None else 1,
        constant_frame_rate=v is not None and frame_spacing_is_uniform(Path(path), v, timeout_s=timeout_s),
        duration_s=_duration(info),
        has_video=v is not None,
        has_audio=a is not None,
        video_codec=v.get("codec_name") if v is not None else None,
        audio_codec=a.get("codec_name") if a is not None else None,
        pix_fmt=v.get("pix_fmt") if v is not None else None,
        sample_rate=int(a["sample_rate"]) if a is not None and a.get("sample_rate") else None,
        channels=int(a["channels"]) if a is not None and a.get("channels") else None,
    )


def loudness(path: Path, *, timeout_s: float | None = None) -> tuple[float, float]:
    """(integrated loudness in LUFS, true peak in dBTP) of the first audio track, via ebur128=peak=true."""
    return measure_loudness(Path(path), timeout_s=timeout_s)


def _environment_failure(exc: MediaError) -> bool:
    return isinstance(exc, MediaToolMissing) or (isinstance(exc, FFmpegError) and exc.returncode is None)


def check_render(
    path: Path,
    expected_width: int,
    expected_height: int,
    expected_fps: float | Fraction,
    expected_duration_s: float,
    tolerance_s: float = 0.1,
    lufs_target: float = -14.0,
    lufs_tol: float = 1.0,
    max_true_peak: float = -1.0,
    *,
    timeout_s: float | None = None,
) -> list[str]:
    """Every deviation of `path` from the MISSION §8 technical bar; an empty list means compliant.

    Raises MediaToolMissing, or FFmpegError on a timeout: the file was not judged."""
    try:
        p = probe(Path(path), timeout_s=timeout_s)
    except MediaError as exc:
        if _environment_failure(exc):
            raise
        return [f"unreadable: {exc}"]
    except (OSError, ValueError) as exc:
        return [f"unreadable: {exc}"]
    defects: list[str] = []
    if not p.has_video:
        defects.append("no_video: the file has no video track")
    else:
        if (p.width, p.height) != (expected_width, expected_height):
            defects.append(f"resolution: {p.width}x{p.height}, expected {expected_width}x{expected_height}")
        if abs(p.fps - float(expected_fps)) > FPS_TOLERANCE:
            defects.append(f"frame_rate: {p.fps_num}/{p.fps_den} fps, expected {float(expected_fps):g}")
        if not p.constant_frame_rate:
            defects.append("variable_frame_rate: frames are not evenly spaced at the nominal rate")
    if abs(p.duration_s - expected_duration_s) > tolerance_s:
        defects.append(f"duration: {p.duration_s:.3f} s, expected {expected_duration_s:.3f} s (±{tolerance_s:g} s)")
    if not p.has_audio:
        defects.append("no_audio: the file has no audio track")
        return defects
    try:
        integrated, true_peak = loudness(Path(path), timeout_s=timeout_s)
    except MediaError as exc:
        if _environment_failure(exc):
            raise
        defects.append(f"unreadable: loudness measurement failed: {exc}")
        return defects
    if abs(integrated - lufs_target) > lufs_tol:
        defects.append(f"loudness: {integrated:.1f} LUFS, expected {lufs_target:g} ±{lufs_tol:g} LUFS")
    if true_peak > max_true_peak:
        defects.append(f"true_peak: {true_peak:.1f} dBTP, maximum {max_true_peak:g} dBTP")
    return defects
