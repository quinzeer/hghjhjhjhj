"""ffmpeg / ffprobe toolbox (MISSION §8): every render and measurement of the studio goes through here.

Rules:
- ffmpeg runs as a subprocess with an argument list, never through a shell; failures raise `FFmpegError`
  with the exit code and the tail of stderr (decoded leniently: a non-UTF-8 byte never raises).
- Determinism contract: the same inputs rendered under the same `media_fingerprint()` give the same bytes.
  The fingerprint (16 hex digits) names what the bytes depend on besides the inputs: the ffmpeg build
  (version, compiler, configuration, libav* versions), the libx264 core, the CPU (architecture and feature
  flags), the `-cpuflags` pin and the label font. Render steps MUST put `media_fingerprint()` in their
  parameters (cache key, manifest): outputs are content-addressed, and machines whose fingerprints differ
  are not promised the same bytes. The promise holds per build and per CPU instruction set: the AAC encoder,
  swresample and swscale pick AVX2/FMA3 code paths whose float rounding differs from the SSE2 ones, and
  glibc's libm picks FMA variants of sin/exp/pow at run time.
- What the module does for reproducibility: libx264 runs single-threaded with bitexact flags, no metadata,
  yuv420p and a constant frame rate; ffmpeg's own SIMD dispatch is pinned to the architecture baseline
  (`-cpuflags`, `pinned_cpuflags`), which makes the tested chains identical across SIMD levels. The pin
  narrows the CPU dependence without reaching glibc's libm, so the fingerprint keeps the CPU flags.
- Outputs are atomic: ffmpeg writes a hidden temporary file next to `out`, renamed only on success, so a
  failed or concurrent render never leaves a truncated file behind.
- Every render takes a keyword `timeout_s`; video renders default to a budget proportional to the work
  (`video_timeout_s`), everything else to DEFAULT_TIMEOUT_S.
- Studio audio standard: 48 kHz, stereo, PCM s16 in WAV (AAC 192 kb/s inside MP4/M4A).
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Iterator, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from studio.core.interfaces import StudioError

DEFAULT_SAMPLE_RATE = 48_000
DEFAULT_TIMEOUT_S = 900.0
# Measured on the 4-vCPU build VM (2026-09-28, ffmpeg 6.1.1, libx264 veryfast, one thread, cpuflags pinned):
# scale_pad of 10 s of testsrc2 (detailed moving content) took 12.2 s to 1920x1080 and 48.7 s to 3840x2160,
# i.e. about 1.2 s of wall time per second of 1080p media, proportional to the pixel count.
X264_SECONDS_PER_1080P_SECOND = 1.25
TIMEOUT_SAFETY = 4.0
X264_PRESET = "veryfast"
X264_CRF = 18
AAC_BITRATE = "192k"
EBU_R128_BLOCK_S = 0.4  # shortest input with a defined integrated loudness (one gating block)
FONT_ENV = "STUDIO_FONT_FILE"  # path to a .ttf/.otf, or "none" to disable labels
FFMPEG_ENV = "STUDIO_FFMPEG"
FFPROBE_ENV = "STUDIO_FFPROBE"
CPUFLAGS_ENV = "STUDIO_FFMPEG_CPUFLAGS"  # overrides the pinned baseline; "native" lets ffmpeg detect the CPU
CPUINFO_PATH = Path("/proc/cpuinfo")  # where `media_fingerprint` reads the CPU feature flags

VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv"})
AUDIO_SUFFIXES = frozenset({".wav", ".m4a"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"})
_MOOV_SUFFIXES = frozenset({".mp4", ".mov", ".m4a"})
# SIMD level every CPU of the architecture has (x86-64 baseline: SSE2; AArch64 baseline: NEON).
BASELINE_CPUFLAGS: dict[str, str] = {
    "x86_64": "sse2",
    "amd64": "sse2",
    "aarch64": "armv8+neon",
    "arm64": "armv8+neon",
}
# Fallback fonts, tried in order (Linux distributions, then macOS). Order matters for determinism.
FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
)
# Extra true-peak headroom tried by `loudnorm_two_pass` until the measured result honours the ceiling.
_TP_MARGINS_DB = (0.3, 1.0, 2.0)
# loudnorm accepts measured_I and measured_thresh only up to 0 LUFS: hotter sources are attenuated first.
_HOT_SOURCE_LUFS = -1.0
_ATTENUATED_SOURCE_LUFS = -23.0

_HEX_COLOR = re.compile(r"^(?:#|0x|0X)([0-9a-fA-F]{6})$")
_NAMED_COLOR = re.compile(r"^[A-Za-z]{3,32}$")
_CPUFLAGS = re.compile(r"^[A-Za-z0-9_.+-]{1,64}$")
_EBUR128_SUMMARY = re.compile(
    r"Summary:.*?\bI:\s*(?P<i>-?inf|[-+]?\d+(?:\.\d+)?)\s*LUFS.*?\bPeak:\s*(?P<tp>-?inf|[-+]?\d+(?:\.\d+)?)\s*dBFS",
    re.S,
)
_LOUDNORM_JSON = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.S)
_X264_STREAM = re.compile(r"x264 - (core [^-]+?) - ")  # the SEI message libx264 writes in every stream
_CPU_FLAG_KEYS = frozenset({"flags", "features"})  # /proc/cpuinfo: x86 says "flags", ARM says "Features"


# ------------------------------------------------------------------ errors


class MediaError(StudioError):
    """A media operation could not produce a valid result."""


class MediaToolMissing(MediaError):
    """ffmpeg or ffprobe is not installed (or not where the environment says)."""


class FFmpegError(MediaError):
    """ffmpeg or ffprobe exited with an error or timed out (`returncode` is None on a timeout)."""

    def __init__(self, cmd: Sequence[str], returncode: int | None, stderr: str) -> None:
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        tail = " | ".join(line.strip() for line in stderr.strip().splitlines()[-8:] if line.strip())
        status = "timed out" if returncode is None else f"exit {returncode}"
        super().__init__(f"{Path(self.cmd[0]).name} failed ({status}): {tail or 'no error output'}")


# ------------------------------------------------------------------ process helpers


def _tool(env_var: str, name: str) -> str:
    configured = os.environ.get(env_var)
    if configured:
        if not Path(configured).is_file():
            raise MediaToolMissing(f"{env_var}={configured} does not exist")
        return configured
    found = shutil.which(name)
    if found is None:
        raise MediaToolMissing(f"{name} not found on PATH (install ffmpeg, or set {env_var})")
    return found


def ffmpeg_bin() -> str:
    return _tool(FFMPEG_ENV, "ffmpeg")


def ffprobe_bin() -> str:
    return _tool(FFPROBE_ENV, "ffprobe")


def pinned_cpuflags() -> str | None:
    """`-cpuflags` value given to every ffmpeg run: $STUDIO_FFMPEG_CPUFLAGS, else the architecture baseline.

    None (no pinning, output may depend on the CPU) for "native" or an architecture without a known baseline."""
    configured = os.environ.get(CPUFLAGS_ENV, "").strip()
    if configured:
        if configured.lower() == "native":
            return None
        if not _CPUFLAGS.match(configured):
            raise MediaError(f"{CPUFLAGS_ENV}={configured!r} is not a cpuflags value")
        return configured
    return BASELINE_CPUFLAGS.get(platform.machine().lower())


def _p(path: Path) -> str:
    """Absolute path for an ffmpeg argument: never read as an option (`-x.mp4`) or a protocol (`a:b.mp4`)."""
    return str(Path(path).absolute())


def _decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    return data if isinstance(data, str) else data.decode("utf-8", errors="replace")


def _exec(cmd: list[str], timeout_s: float) -> subprocess.CompletedProcess[str]:
    """Run `cmd`; its output is decoded as UTF-8 with replacement (tags and paths may hold any byte)."""
    try:
        raw = subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(cmd, None, _decode(exc.stderr)) from exc
    result = subprocess.CompletedProcess(cmd, raw.returncode, _decode(raw.stdout), _decode(raw.stderr))
    if result.returncode != 0:
        raise FFmpegError(cmd, result.returncode, result.stderr)
    return result


def run_ffmpeg(
    args: Sequence[str], *, timeout_s: float | None = None, loglevel: str = "error"
) -> subprocess.CompletedProcess[str]:
    """Run ffmpeg with `args` (no shell). Filters run single-threaded and SIMD is pinned (`pinned_cpuflags`)
    so results are reproducible. `timeout_s` defaults to the module's DEFAULT_TIMEOUT_S, read at call time."""
    pin = pinned_cpuflags()
    cmd = [
        ffmpeg_bin(),
        "-hide_banner",
        "-nostdin",
        "-nostats",
        "-loglevel",
        loglevel,
        "-y",
        *(["-cpuflags", pin] if pin else []),
        "-filter_threads",
        "1",
        "-filter_complex_threads",
        "1",
        *args,
    ]
    return _exec(cmd, DEFAULT_TIMEOUT_S if timeout_s is None else timeout_s)


def _image_input_args(path: Path) -> list[str]:
    """Read an image file as exactly that file: no `%d` sequence pattern expansion by the image2 demuxer."""
    return ["-f", "image2", "-pattern_type", "none"] if Path(path).suffix.lower() in IMAGE_SUFFIXES else []


def ffprobe_json(path: Path, *, timeout_s: float = 60.0, data_hash: bool = False) -> dict[str, Any]:
    """Streams and format of `path` as ffprobe's JSON (`data_hash`: add each stream's `extradata_hash`)."""
    extra = ["-show_data_hash", "sha256"] if data_hash else []
    cmd = [ffprobe_bin(), "-v", "error", *extra, "-show_streams", "-show_format", "-of", "json"]
    cmd += [*_image_input_args(path), _p(path)]
    data = json.loads(_exec(cmd, timeout_s).stdout or "{}")
    if not isinstance(data, dict):
        raise MediaError(f"unexpected ffprobe output for {path}")
    return data


@functools.lru_cache(maxsize=8)
def _version_text(ffmpeg: str) -> str:
    return _exec([ffmpeg, "-hide_banner", "-version"], 30.0).stdout


def render_environment() -> dict[str, str | None]:
    """What a render's bytes depend on besides its inputs, readable side by side in a manifest: the ffmpeg
    build (first line, and a digest of the whole `-version` text), the architecture, the `-cpuflags` pin and
    the label font. `media_fingerprint()` condenses it, with the libx264 core and the CPU flags, into the
    value that content-addressed steps carry."""
    version = _version_text(ffmpeg_bin())
    font = find_font()
    return {
        "ffmpeg_version": (version.splitlines() or [""])[0],
        "ffmpeg_build_sha256": hashlib.sha256(version.encode("utf-8")).hexdigest(),
        "machine": platform.machine().lower(),
        "cpuflags": pinned_cpuflags() or "native",
        "font_sha256": hashlib.sha256(font.read_bytes()).hexdigest() if font is not None else None,
    }


@functools.lru_cache(maxsize=8)
def _x264_core(ffmpeg: str) -> str:
    """Core (version and revision) of the libx264 behind `ffmpeg`, or "none" without libx264. Every H.264
    stream carries it in an SEI message, so the bytes of a render depend on it, yet `ffmpeg -version` does
    not name it (libx264 is a shared library). A timeout propagates: a fingerprint never varies by chance."""
    probe = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=1:d=1"]
    probe += ["-frames:v", "1", "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-f", "h264", "-"]
    try:
        stream = _exec(probe, 60.0).stdout
    except FFmpegError as exc:
        if exc.returncode is None:
            raise
        return "none"
    match = _X264_STREAM.search(stream)
    return match.group(1) if match else "unknown"


def _cpu_flags() -> str:
    """Feature flags of the CPU from /proc/cpuinfo ("flags" on x86, "Features" on ARM): sorted, one entry per
    distinct core type (`|`-separated). The architecture name when the file is unreadable or has no such line."""
    try:
        text = CPUINFO_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    entries: set[str] = set()
    for line in text.splitlines():
        key, _, value = line.partition(":")
        if key.strip().lower() in _CPU_FLAG_KEYS and value.split():
            entries.add(" ".join(sorted(set(value.split()))))
    return "|".join(sorted(entries)) or platform.machine().lower()


def media_fingerprint() -> str:
    """16 hex digits (truncated SHA-256) naming what the bytes of a render depend on besides its inputs:
    `render_environment()` (ffmpeg build, architecture, `-cpuflags` pin, label font), the libx264 core and
    the CPU's feature flags. The same inputs under the same fingerprint give the same bytes; put it in the
    parameters of every render step (cache key, manifest). Raises MediaToolMissing without ffmpeg."""
    parts = {**render_environment(), "x264": _x264_core(ffmpeg_bin()), "cpu_flags": _cpu_flags()}
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


@contextlib.contextmanager
def _atomic_output(out: Path, allowed_suffixes: frozenset[str]) -> Iterator[Path]:
    out = Path(out)
    if out.suffix.lower() not in allowed_suffixes:
        raise ValueError(f"{out.name}: extension must be one of {sorted(allowed_suffixes)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.stem}.partial-{uuid.uuid4().hex[:12]}{out.suffix}")
    try:
        yield tmp
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)


def video_timeout_s(duration_s: float, width: int, height: int) -> float:
    """Default timeout of a video render: measured x264 speed (X264_SECONDS_PER_1080P_SECOND, scaled by the
    pixel count) times TIMEOUT_SAFETY, never below DEFAULT_TIMEOUT_S."""
    work = max(duration_s, 0.0) * (width * height) / (1920 * 1080) * X264_SECONDS_PER_1080P_SECOND
    return max(DEFAULT_TIMEOUT_S, work * TIMEOUT_SAFETY)


# ------------------------------------------------------------------ argument builders


def escape_filter_value(value: str) -> str:
    """Escape a filter option value for both levels of filtergraph parsing (ffmpeg-filters, "Notes on
    filtergraph escaping"), so paths and text with `'`, `:`, `,`, `;`, `[`, `]` or `\\` stay literal."""
    level1 = re.sub(r"([\\':])", r"\\\1", value)
    return re.sub(r"([\\'\[\],;])", r"\\\1", level1)


def normalize_color(color: str) -> str:
    """`#RRGGBB`, `0xRRGGBB` or a colour name → ffmpeg colour. Anything else is refused (no filter injection)."""
    m = _HEX_COLOR.match(color)
    if m:
        return "0x" + m.group(1).upper()
    if _NAMED_COLOR.match(color):
        return color.lower()
    raise ValueError(f"invalid colour {color!r}: use #RRGGBB, 0xRRGGBB or a colour name")


def _fps(fps: float | Fraction) -> Fraction:
    if isinstance(fps, bool) or fps <= 0:
        raise ValueError(f"fps must be > 0, got {fps!r}")
    value = fps if isinstance(fps, Fraction) else Fraction(fps).limit_denominator(1001)
    if value > 240:
        raise ValueError(f"fps must be <= 240, got {fps!r}")
    return value


def parse_rate(raw: Any) -> Fraction | None:
    """ffprobe rational ("30/1", "1/15360") → Fraction; None when unknown ("0/0", "N/A") or not positive."""
    num, _, den = str(raw or "").partition("/")
    try:
        value = Fraction(int(num), int(den or "1"))
    except (ValueError, ZeroDivisionError):
        return None
    return value if value > 0 else None


def stream_fps(stream: dict[str, Any]) -> Fraction:
    """Frame rate of an ffprobe stream: `avg_frame_rate`, else `r_frame_rate`, else 0."""
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = parse_rate(stream.get(key))
        if value is not None:
            return value
    return Fraction(0)


def frame_spacing_is_uniform(path: Path, stream: dict[str, Any], *, timeout_s: float | None = None) -> bool:
    """Constant frame rate, checked frame by frame: r_frame_rate == avg_frame_rate, and every presentation
    timestamp of the video `stream` of `path` follows the previous one by 1/fps, to one time-base tick.

    The rate fields alone are not enough: a mix of 1/60, 1/30 and 1/15 s frames can average exactly 30 fps."""
    rate = parse_rate(stream.get("r_frame_rate"))
    time_base = parse_rate(stream.get("time_base"))
    if rate is None or rate != parse_rate(stream.get("avg_frame_rate")) or time_base is None:
        return False
    cmd = [ffprobe_bin(), "-v", "error", "-select_streams", str(int(stream.get("index", 0)))]
    cmd += ["-show_entries", "packet=pts", "-of", "csv=p=0", *_image_input_args(path), _p(path)]
    fields = _exec(cmd, DEFAULT_TIMEOUT_S if timeout_s is None else timeout_s).stdout.split()
    try:
        pts = sorted(int(f.strip(",")) for f in fields)
    except ValueError:  # "N/A": no timestamps to check
        return False
    ticks_per_frame = 1 / (rate * time_base)
    return all(abs(b - a - ticks_per_frame) <= 1 for a, b in zip(pts, pts[1:], strict=False))


def _fps_arg(fps: Fraction) -> str:
    return str(fps.numerator) if fps.denominator == 1 else f"{fps.numerator}/{fps.denominator}"


def _frame_count(duration_s: float, fps: Fraction) -> int:
    return max(1, round(Fraction(duration_s) * fps))


def _positive(name: str, value: float) -> None:
    if isinstance(value, bool) or not value > 0:
        raise ValueError(f"{name} must be > 0, got {value!r}")


def _even_size(width: int, height: int) -> None:
    for name, v in (("width", width), ("height", height)):
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0 or v % 2:
            raise ValueError(f"{name} must be a positive even integer (yuv420p), got {v!r}")


def _channels_layout(channels: int) -> str:
    if channels == 1:
        return "mono"
    if channels == 2:
        return "stereo"
    raise ValueError(f"channels must be 1 or 2, got {channels!r}")


def _container_args(out: Path) -> list[str]:
    args = ["-fflags", "+bitexact", "-map_metadata", "-1", "-map_chapters", "-1"]
    if out.suffix.lower() in _MOOV_SUFFIXES:
        args += ["-movflags", "+faststart"]
    return [*args, _p(out)]


def _video_codec_args(fps: Fraction) -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-preset",
        X264_PRESET,
        "-crf",
        str(X264_CRF),
        "-threads",
        "1",
        "-pix_fmt",
        "yuv420p",
        "-fps_mode",
        "cfr",
        "-r",
        _fps_arg(fps),
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-color_range",
        "tv",
        "-flags:v",
        "+bitexact",
    ]


def _audio_codec_args(out: Path, sample_rate: int) -> list[str]:
    if out.suffix.lower() == ".wav":
        codec = ["-c:a", "pcm_s16le"]
    else:
        codec = ["-c:a", "aac", "-b:a", AAC_BITRATE]
    return [*codec, "-ar", str(sample_rate), "-flags:a", "+bitexact"]


def _video_tail(fps: Fraction) -> str:
    """Last filters of every video chain: square pixels, constant cadence, BT.709 limited-range 4:2:0."""
    return f"setsar=1,fps={_fps_arg(fps)},scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"


def _fit(width: int, height: int) -> str:
    """Scale into width×height keeping the aspect ratio, then pad (letterbox or pillarbox) in black."""
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
    )


# ------------------------------------------------------------------ labels


def find_font() -> Path | None:
    """Font used for labels: $STUDIO_FONT_FILE ("none" disables labels), else the first known system font."""
    configured = os.environ.get(FONT_ENV)
    if configured is not None and configured.strip():
        if configured.strip().lower() == "none":
            return None
        path = Path(configured)
        if not path.is_file():
            raise MediaError(f"{FONT_ENV}={configured} does not exist")
        return path
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return Path(candidate)
    return None


@functools.lru_cache(maxsize=8)
def _has_filter(ffmpeg: str, name: str) -> bool:
    out = _exec([ffmpeg, "-hide_banner", "-filters"], 30.0).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if line.strip())


def drawtext_available() -> bool:
    """True when labels can be drawn: a font is found and ffmpeg was built with drawtext (libfreetype)."""
    return find_font() is not None and _has_filter(ffmpeg_bin(), "drawtext")


def _label_filter(label: str | None, width: int, height: int, workdir: Path, *, y: str = "(h-text_h)/2") -> str | None:
    if label is None or not label.strip():
        return None
    font = find_font()
    if font is None or not _has_filter(ffmpeg_bin(), "drawtext"):
        return None
    text = " ".join(label.split())[:80]
    textfile = workdir / "label.txt"
    textfile.write_text(text, encoding="utf-8")
    fontsize = max(12, min(height // 20, (3 * width) // (2 * max(len(text), 1))))
    return (
        f"drawtext=fontfile={escape_filter_value(str(font))}:textfile={escape_filter_value(str(textfile))}"
        f":expansion=none:fontsize={fontsize}:fontcolor=white:box=1:boxcolor=black@0.5"
        f":boxborderw={max(4, fontsize // 4)}:x=(w-text_w)/2:y={y}"
    )


# ------------------------------------------------------------------ video and images


def color_clip(
    out: Path,
    width: int,
    height: int,
    fps: float | Fraction,
    duration_s: float,
    color: str,
    label: str | None = None,
    *,
    timeout_s: float | None = None,
) -> Path:
    """Solid-colour H.264 clip (MP4), with `label` centred on it when a font is available (else no text)."""
    _even_size(width, height)
    _positive("duration_s", duration_s)
    rate = _fps(fps)
    frames = _frame_count(duration_s, rate)
    # The colour is converted to BT.709 YUV on a 16x16 frame, then enlarged without interpolation: the
    # same pixels as a full-size conversion, for a fraction of the cost.
    source = f"color=c={normalize_color(color)}:s=16x16:r={_fps_arg(rate)}:d={float(frames / rate) + 1.0:.6f}"
    solid = f"scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,scale={width}:{height}:flags=neighbor"
    budget = timeout_s if timeout_s is not None else video_timeout_s(float(frames / rate), width, height)
    with tempfile.TemporaryDirectory(prefix="studio-label-") as workdir, _atomic_output(out, VIDEO_SUFFIXES) as tmp:
        label_filter = _label_filter(label, width, height, Path(workdir))
        chain = [f for f in (solid, label_filter, f"setsar=1,fps={_fps_arg(rate)},format=yuv420p") if f]
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-i",
                source,
                "-vf",
                ",".join(chain),
                "-frames:v",
                str(frames),
                "-an",
                *_video_codec_args(rate),
                *_container_args(tmp),
            ],
            timeout_s=budget,
        )
    return Path(out)


def still_image(
    out: Path, width: int, height: int, color: str, label: str | None = None, *, timeout_s: float | None = None
) -> Path:
    """Solid-colour PNG (RGB, 8 bits), with an optional label as in `color_clip`."""
    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be > 0, got {width}x{height}")
    source = f"color=c={normalize_color(color)}:s={width}x{height}:r=1:d=1"
    with tempfile.TemporaryDirectory(prefix="studio-label-") as workdir, _atomic_output(out, frozenset({".png"})) as tmp:
        chain = [f for f in (_label_filter(label, width, height, Path(workdir)), "format=rgb24") if f]
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-i",
                source,
                "-vf",
                ",".join(chain),
                "-frames:v",
                "1",
                "-c:v",
                "png",
                "-threads",
                "1",
                "-flags:v",
                "+bitexact",
                "-fflags",
                "+bitexact",
                "-map_metadata",
                "-1",
                "-update",  # one file named exactly `tmp`: no `%d` pattern expansion by the image2 muxer
                "1",
                _p(tmp),
            ],
            timeout_s=timeout_s,
        )
    return Path(out)


def image_clip(
    out: Path,
    image: Path,
    duration_s: float,
    fps: float | Fraction,
    *,
    width: int | None = None,
    height: int | None = None,
    band_color: str | None = None,
    label: str | None = None,
    timeout_s: float | None = None,
) -> Path:
    """Still image turned into a clip. A band of `band_color` slides along the bottom edge (visible motion).

    Without width/height, the image size is kept (rounded down to even numbers)."""
    _positive("duration_s", duration_s)
    rate = _fps(fps)
    frames = _frame_count(duration_s, rate)
    if width is None or height is None:
        stream = _first_video_stream(Path(image))
        width = int(stream["width"]) // 2 * 2
        height = int(stream["height"]) // 2 * 2
    _even_size(width, height)
    seconds = float(frames / rate)
    graph = [f"[0:v]{_fit(width, height)},setsar=1[bg]"]
    last = "bg"
    if band_color is not None:
        bw, bh = max(2, width // 5), max(2, height // 10)
        graph.append(f"color=c={normalize_color(band_color)}:s={bw}x{bh}:r={_fps_arg(rate)}:d={seconds + 1.0:.6f}[band]")
        graph.append(f"[bg][band]overlay=x=(W-w)*t/{seconds:.6f}:y=H-h:eval=frame:shortest=1[moving]")
        last = "moving"
    budget = timeout_s if timeout_s is not None else video_timeout_s(seconds, width, height)
    with tempfile.TemporaryDirectory(prefix="studio-label-") as workdir, _atomic_output(out, VIDEO_SUFFIXES) as tmp:
        top = _label_filter(label, width, height, Path(workdir), y="h/12")  # the source image may carry its own label
        chain = [f for f in (top, _video_tail(rate)) if f]
        graph.append(f"[{last}]{','.join(chain)}[v]")
        run_ffmpeg(
            [
                "-loop",
                "1",
                "-framerate",
                _fps_arg(rate),
                "-t",
                f"{seconds + 1.0:.6f}",
                *_image_input_args(Path(image)),
                "-i",
                _p(image),
                "-filter_complex",
                ";".join(graph),
                "-map",
                "[v]",
                "-frames:v",
                str(frames),
                "-an",
                *_video_codec_args(rate),
                *_container_args(tmp),
            ],
            timeout_s=budget,
        )
    return Path(out)


def _duration_s(path: Path, info: dict[str, Any] | None = None) -> float:
    info = ffprobe_json(path) if info is None else info
    raw = info.get("format", {}).get("duration")
    if raw in (None, "N/A"):
        raise MediaError(f"{path}: duration unknown")
    return float(raw)


def _video_budget(path: Path, width: int, height: int, timeout_s: float | None) -> float:
    """Explicit `timeout_s`, else the budget of re-encoding `path` at width×height."""
    if timeout_s is not None:
        return timeout_s
    try:
        return video_timeout_s(_duration_s(path), width, height)
    except MediaError:
        return DEFAULT_TIMEOUT_S


def scale_pad(out: Path, src: Path, width: int, height: int, fps: float | Fraction, *, timeout_s: float | None = None) -> Path:
    """Fit `src` into width×height (aspect kept, black bars) at a constant `fps`. Audio, if any, is kept (AAC)."""
    _even_size(width, height)
    rate = _fps(fps)
    budget = _video_budget(Path(src), width, height, timeout_s)
    with _atomic_output(out, VIDEO_SUFFIXES) as tmp:
        run_ffmpeg(
            [
                "-i",
                _p(src),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-vf",
                f"{_fit(width, height)},{_video_tail(rate)}",
                *_video_codec_args(rate),
                *_audio_codec_args(tmp, DEFAULT_SAMPLE_RATE),
                *_container_args(tmp),
            ],
            timeout_s=budget,
        )
    return Path(out)


# Stream parameters that must be identical for clips to be joined without re-encoding.
_COPY_KEYS = (
    "codec_name",
    "profile",
    "level",
    "width",
    "height",
    "pix_fmt",
    "sample_aspect_ratio",
    "r_frame_rate",
    "avg_frame_rate",
    "time_base",
    "color_space",
    "color_primaries",
    "color_transfer",
    "color_range",
    "extradata_hash",
)


def _first_video_stream(clip: Path, *, data_hash: bool = False) -> dict[str, Any]:
    return _clip_info(clip, data_hash=data_hash)[0]


def _clip_info(clip: Path, *, data_hash: bool = False) -> tuple[dict[str, Any], float]:
    """(first video stream, container duration in seconds or 0.0 when unknown) of `clip`."""
    info = ffprobe_json(clip, data_hash=data_hash)
    found: list[dict[str, Any]] = info.get("streams", [])
    streams = [s for s in found if s.get("codec_type") == "video"]
    if not streams:
        raise MediaError(f"{clip}: no video stream")
    try:
        duration = _duration_s(clip, info)
    except MediaError:
        duration = 0.0
    return streams[0], duration


def _concat_list_entry(path: Path) -> str:
    text = str(path.resolve())
    if "\n" in text or "\r" in text:
        raise ValueError(f"unsupported path for concatenation: {text!r}")
    return "file '" + text.replace("'", "'\\''") + "'\n"


def concat_videos(
    out: Path,
    clips: Sequence[Path],
    *,
    width: int | None = None,
    height: int | None = None,
    fps: float | Fraction | None = None,
    timeout_s: float | None = None,
) -> Path:
    """Concatenate the video tracks of `clips` in order (audio tracks are dropped: use `mux` afterwards).

    width, height and fps default to the first clip's. When every clip already has exactly those values,
    the same H.264 parameters and evenly spaced frames (as clips rendered by this module do), the streams
    are joined without re-encoding (lossless, fast); otherwise every clip is fitted to width×height at
    `fps` and re-encoded."""
    if not clips:
        raise ValueError("concat_videos needs at least one clip")
    infos = [_clip_info(Path(c), data_hash=True) for c in clips]
    streams = [s for s, _ in infos]
    width = width if width is not None else int(streams[0]["width"])
    height = height if height is not None else int(streams[0]["height"])
    rate = _fps(fps if fps is not None else stream_fps(streams[0]))
    _even_size(width, height)
    budget = timeout_s if timeout_s is not None else video_timeout_s(sum(d for _, d in infos), width, height)
    signatures = {tuple(str(s.get(k)) for k in _COPY_KEYS) for s in streams}
    copy = (
        len(signatures) == 1
        and streams[0].get("codec_name") == "h264"
        and streams[0].get("pix_fmt") == "yuv420p"
        and (int(streams[0]["width"]), int(streams[0]["height"]), stream_fps(streams[0])) == (width, height, rate)
        and all(frame_spacing_is_uniform(Path(c), s) for c, s in zip(clips, streams, strict=True))
    )
    if copy:
        with tempfile.TemporaryDirectory(prefix="studio-concat-") as workdir, _atomic_output(out, VIDEO_SUFFIXES) as tmp:
            listing = Path(workdir) / "clips.txt"
            listing.write_text("".join(_concat_list_entry(Path(c)) for c in clips), encoding="utf-8")
            run_ffmpeg(
                [
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-auto_convert",
                    "0",
                    "-i",
                    str(listing),
                    "-map",
                    "0:v:0",
                    "-c:v",
                    "copy",
                    "-an",
                    *_container_args(tmp),
                ],
                timeout_s=budget,
            )
        return Path(out)
    inputs: list[str] = []
    graph: list[str] = []
    for i, clip in enumerate(clips):
        inputs += [*_image_input_args(Path(clip)), "-i", _p(clip)]
        graph.append(f"[{i}:v:0]{_fit(width, height)},{_video_tail(rate)}[v{i}]")
    graph.append("".join(f"[v{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0[v]")
    with _atomic_output(out, VIDEO_SUFFIXES) as tmp:
        run_ffmpeg(
            [*inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-an", *_video_codec_args(rate), *_container_args(tmp)],
            timeout_s=budget,
        )
    return Path(out)


def mux(out: Path, video: Path, audio: Path, *, timeout_s: float | None = None) -> Path:
    """Video track of `video` (copied, not re-encoded) + audio track of `audio` (AAC 48 kHz).

    The audio is padded with silence or trimmed so both tracks end together: the file lasts exactly as
    long as the video."""
    stream, duration = _clip_info(Path(video))
    if duration <= 0:
        raise MediaError(f"{video}: duration unknown")
    budget = timeout_s if timeout_s is not None else video_timeout_s(duration, int(stream["width"]), int(stream["height"]))
    with _atomic_output(out, VIDEO_SUFFIXES) as tmp:
        run_ffmpeg(
            [
                "-i",
                _p(video),
                "-i",
                _p(audio),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-af",
                f"apad=whole_dur={duration:.6f},atrim=duration={duration:.6f}",
                *_audio_codec_args(tmp, DEFAULT_SAMPLE_RATE),
                *_container_args(tmp),
            ],
            timeout_s=budget,
        )
    return Path(out)


# ------------------------------------------------------------------ audio


def _audio_source(
    out: Path,
    source: str,
    duration_s: float,
    sample_rate: int,
    channels: int,
    post: str | None = None,
    *,
    timeout_s: float | None = None,
) -> Path:
    samples = round(Fraction(duration_s) * sample_rate)
    if samples < 1:
        raise ValueError(f"duration_s too short: {duration_s!r}")
    chain = [f for f in (post, f"atrim=end_sample={samples}") if f]
    with _atomic_output(out, AUDIO_SUFFIXES) as tmp:
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-i",
                source,
                "-af",
                ",".join(chain),
                "-ac",
                str(channels),
                *_audio_codec_args(tmp, sample_rate),
                *_container_args(tmp),
            ],
            timeout_s=timeout_s,
        )
    return Path(out)


def chord(
    out: Path,
    duration_s: float,
    freqs_hz: Sequence[float],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    amplitude: float = 0.25,
    channels: int = 2,
    timeout_s: float | None = None,
) -> Path:
    """Sum of sine waves of equal level; `amplitude` is the peak of the sum (0 < amplitude <= 1)."""
    _positive("duration_s", duration_s)
    _positive("sample_rate", sample_rate)
    if not freqs_hz:
        raise ValueError("at least one frequency is required")
    for f in freqs_hz:
        if isinstance(f, bool) or not 0 < f < sample_rate / 2:
            raise ValueError(f"frequency {f!r} must be in (0, {sample_rate / 2}) Hz")
    if not 0 < amplitude <= 1:
        raise ValueError(f"amplitude must be in (0, 1], got {amplitude!r}")
    each = amplitude / len(freqs_hz)
    expr = "+".join(f"{each:.6f}*sin(2*PI*{float(f):.4f}*t)" for f in freqs_hz)
    layout = _channels_layout(channels)
    source = f"aevalsrc=exprs={expr}:s={sample_rate}:c={layout}:d={duration_s + 0.1:.6f}"
    return _audio_source(out, source, duration_s, sample_rate, channels, timeout_s=timeout_s)


def tone(
    out: Path,
    duration_s: float,
    freq_hz: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    amplitude: float = 0.25,
    channels: int = 2,
    timeout_s: float | None = None,
) -> Path:
    """Pure sine wave (WAV or M4A), exact to the sample."""
    return chord(out, duration_s, [freq_hz], sample_rate, amplitude=amplitude, channels=channels, timeout_s=timeout_s)


def noise(
    out: Path,
    duration_s: float,
    seed: int,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    amplitude: float = 0.3,
    color: str = "pink",
    channels: int = 2,
    timeout_s: float | None = None,
) -> Path:
    """Seeded noise burst (white, pink, brown, blue, violet or velvet): same seed, same samples."""
    _positive("duration_s", duration_s)
    if color not in {"white", "pink", "brown", "blue", "violet", "velvet"}:
        raise ValueError(f"unknown noise colour {color!r}")
    if not 0 < amplitude <= 1:
        raise ValueError(f"amplitude must be in (0, 1], got {amplitude!r}")
    layout = _channels_layout(channels)
    source = f"anoisesrc=d={duration_s + 0.1:.6f}:c={color}:r={sample_rate}:a={amplitude:.6f}:s={seed % 2**32}"
    post = "pan=stereo|c0=c0|c1=c0" if layout == "stereo" else None
    return _audio_source(out, source, duration_s, sample_rate, channels, post, timeout_s=timeout_s)


def silence(
    out: Path, duration_s: float, sample_rate: int = DEFAULT_SAMPLE_RATE, *, channels: int = 2, timeout_s: float | None = None
) -> Path:
    """Digital silence, exact to the sample."""
    _positive("duration_s", duration_s)
    source = f"anullsrc=channel_layout={_channels_layout(channels)}:sample_rate={sample_rate}"
    return _audio_source(out, source, duration_s, sample_rate, channels, timeout_s=timeout_s)


def concat_audio(
    out: Path,
    clips: Sequence[Path],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    channels: int = 2,
    timeout_s: float | None = None,
) -> Path:
    """Concatenate audio tracks in order (resampled to `sample_rate` and `channels` first)."""
    if not clips:
        raise ValueError("concat_audio needs at least one clip")
    layout = _channels_layout(channels)
    inputs: list[str] = []
    graph: list[str] = []
    for i, clip in enumerate(clips):
        inputs += ["-i", _p(clip)]
        graph.append(f"[{i}:a:0]aresample={sample_rate},aformat=sample_rates={sample_rate}:channel_layouts={layout}[a{i}]")
    graph.append("".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[a]")
    with _atomic_output(out, AUDIO_SUFFIXES) as tmp:
        run_ffmpeg(
            [
                *inputs,
                "-filter_complex",
                ";".join(graph),
                "-map",
                "[a]",
                *_audio_codec_args(tmp, sample_rate),
                *_container_args(tmp),
            ],
            timeout_s=timeout_s,
        )
    return Path(out)


def mix_audio(
    out: Path,
    voice: Path,
    bed: Path,
    *,
    bed_gain_db: float = -18.0,
    channels: int = 2,
    timeout_s: float | None = None,
) -> Path:
    """Voice over a bed (music, ambience) attenuated by `bed_gain_db`; the mix lasts as long as the voice."""
    if bed_gain_db > 0:
        raise ValueError("the bed must sit under the voice: bed_gain_db must be <= 0")
    layout = _channels_layout(channels)
    fmt = f"aresample={DEFAULT_SAMPLE_RATE},aformat=sample_rates={DEFAULT_SAMPLE_RATE}:channel_layouts={layout}"
    graph = (
        f"[0:a:0]{fmt}[v];[1:a:0]{fmt},volume={bed_gain_db:.2f}dB[b];"
        "[v][b]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
    )
    with _atomic_output(out, AUDIO_SUFFIXES) as tmp:
        run_ffmpeg(
            [
                "-i",
                _p(voice),
                "-i",
                _p(bed),
                "-filter_complex",
                graph,
                "-map",
                "[a]",
                *_audio_codec_args(tmp, DEFAULT_SAMPLE_RATE),
                *_container_args(tmp),
            ],
            timeout_s=timeout_s,
        )
    return Path(out)


def measure_loudness(path: Path, *, timeout_s: float | None = None) -> tuple[float, float]:
    """(integrated loudness in LUFS, true peak in dBTP) of the first audio track (ebur128, peak=true).

    Silence reads as (-70.0, -inf): ebur128's absolute gate."""
    result = run_ffmpeg(
        ["-i", _p(path), "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-"],
        timeout_s=timeout_s,
        loglevel="info",
    )
    summaries = list(_EBUR128_SUMMARY.finditer(result.stderr))
    if not summaries:
        raise MediaError(f"{path}: no ebur128 summary in ffmpeg output")
    last = summaries[-1]
    return float(last.group("i")), float(last.group("tp"))


def _gain_filter(gain_db: float) -> str:
    return f"volume={gain_db:.2f}dB," if gain_db else ""


def _loudnorm_measure(
    src: Path, target_lufs: float, true_peak_db: float, lra: float, gain_db: float = 0.0, timeout_s: float | None = None
) -> dict[str, float]:
    result = run_ffmpeg(
        [
            "-i",
            _p(src),
            "-map",
            "0:a:0",
            "-af",
            f"{_gain_filter(gain_db)}loudnorm=I={target_lufs:.2f}:TP={true_peak_db:.2f}:LRA={lra:.2f}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        timeout_s=timeout_s,
        loglevel="info",
    )
    blocks = _LOUDNORM_JSON.findall(result.stderr)
    if not blocks:
        raise MediaError(f"{src}: no loudnorm measurement in ffmpeg output")
    raw = json.loads(blocks[-1])
    return {k: float(raw[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def _unmeasurable(src: Path, timeout_s: float | None) -> MediaError:
    """Why a source has no integrated loudness: too short for one EBU R128 gating block, or silent."""
    try:
        duration = _duration_s(src, ffprobe_json(src, timeout_s=60.0 if timeout_s is None else timeout_s))
    except MediaError:
        duration = math.inf
    if duration < EBU_R128_BLOCK_S:
        return MediaError(
            f"{src}: {duration:.3f} s is shorter than one EBU R128 gating block ({EBU_R128_BLOCK_S} s): "
            "integrated loudness is undefined, normalise it inside a longer track"
        )
    return MediaError(f"{src}: source is silent, loudness cannot be normalised")


def loudnorm_two_pass(
    out: Path,
    src: Path,
    target_lufs: float = -14.0,
    true_peak_db: float = -1.0,
    *,
    lra: float = 11.0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    timeout_s: float | None = None,
) -> Path:
    """EBU R128 normalisation in two passes (measure, then apply) of the first audio track of `src`.

    The true-peak ceiling is a hard guarantee: the result is measured, and the pass is redone with more
    headroom until `true peak <= true_peak_db` (MediaError if it never holds). The integrated loudness
    reaches `target_lufs` unless that ceiling forbids it (very short, very peaky input); `qa.check_render`
    reports that case. Sources louder than 0 LUFS are attenuated first (loudnorm rejects such measurements).
    Sources shorter than one gating block (0.4 s) or silent raise MediaError. Output is audio only.
    """
    if not -70.0 <= target_lufs <= -5.0:
        raise ValueError(f"target_lufs out of range: {target_lufs!r}")
    if not -9.0 <= true_peak_db <= 0.0:
        raise ValueError(f"true_peak_db out of range: {true_peak_db!r}")
    if not 1.0 <= lra <= 50.0:
        raise ValueError(f"lra out of range: {lra!r}")
    src = Path(src)
    gain_db = 0.0
    last_peak = float("nan")
    for margin in _TP_MARGINS_DB:
        tp = max(-9.0, true_peak_db - margin)
        m = _loudnorm_measure(src, target_lufs, tp, lra, gain_db, timeout_s)
        if m["input_i"] > _HOT_SOURCE_LUFS or m["input_thresh"] > _HOT_SOURCE_LUFS:
            gain_db += _ATTENUATED_SOURCE_LUFS - m["input_i"]  # linear, so the final loudness is unaffected
            m = _loudnorm_measure(src, target_lufs, tp, lra, gain_db, timeout_s)
        if not m["input_i"] > -70.0:  # -inf or the absolute gate: nothing to measure
            raise _unmeasurable(src, timeout_s)
        # A target range at least as wide as the source's keeps loudnorm in linear (transparent) mode.
        target_lra = min(50.0, max(lra, m["input_lra"]))
        af = (
            f"{_gain_filter(gain_db)}loudnorm=I={target_lufs:.2f}:TP={tp:.2f}:LRA={target_lra:.2f}"
            f":measured_I={m['input_i']:.2f}:measured_TP={m['input_tp']:.2f}:measured_LRA={m['input_lra']:.2f}"
            f":measured_thresh={m['input_thresh']:.2f}:offset={m['target_offset']:.2f}:linear=true:print_format=none"
            f",aresample={sample_rate}"
        )
        try:
            with _atomic_output(out, AUDIO_SUFFIXES) as tmp:
                run_ffmpeg(
                    ["-i", _p(src), "-map", "0:a:0", "-af", af, *_audio_codec_args(tmp, sample_rate), *_container_args(tmp)],
                    timeout_s=timeout_s,
                )
                _, peak = measure_loudness(tmp, timeout_s=timeout_s)
                if peak > true_peak_db:
                    raise _PeakAboveCeiling(peak)  # discards the attempt: `out` is left untouched
            return Path(out)
        except _PeakAboveCeiling as exc:
            last_peak = exc.peak
    raise MediaError(f"{src}: true peak {last_peak:.1f} dBTP still above {true_peak_db:.1f} after limiting")


class _PeakAboveCeiling(Exception):
    def __init__(self, peak: float) -> None:
        super().__init__(f"true peak {peak}")
        self.peak = peak
