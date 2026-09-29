"""studio.media: deterministic ffmpeg renders, atomic outputs, loudness normalisation and the MISSION §8 checks.

Media proofs need ffmpeg. Without it they are skipped, unless STUDIO_REQUIRE_MEDIA=1 turns the skip into a failure:
`make verify-phase-1` and the CI must export it, so that a green run always carries the proofs.
"""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import wave
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from studio.media import ffmpeg, qa
from studio.media.ffmpeg import FFmpegError, MediaError, MediaToolMissing

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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partial_files(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.rglob("*") if ".partial-" in p.name)


def wav_frames(path: Path) -> tuple[int, int, int, bytes]:
    with wave.open(str(path)) as w:
        return w.getnframes(), w.getnchannels(), w.getframerate(), w.readframes(w.getnframes())


def make_vfr(out: Path) -> Path:
    """30 frames at 30 fps then 30 frames at 10 fps: a variable frame rate file."""
    ffmpeg.run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=320x240:r=30:d=2",
            "-vf",
            "setpts='if(lt(N,30),N,30+(N-30)*3)/(30*TB)'",
            "-fps_mode",
            "passthrough",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ]
    )
    return out


def make_hidden_vfr(folder: Path) -> Path:
    """Frames lasting 1/60, 1/30 and 1/15 s whose rate fields still agree (r_frame_rate == avg_frame_rate)."""
    spacing = "if(lt(N,60),2*N,120+6*floor((N-60)/3)+if(eq(mod(N-60,3),0),0,if(eq(mod(N-60,3),1),1,5)))/(60*TB)"
    for frames in range(236, 250):
        out = folder / f"hidden_vfr_{frames}.mp4"
        ffmpeg.run_ffmpeg(
            ["-f", "lavfi", "-i", "testsrc2=s=320x240:r=60:d=5", "-vf", f"setpts='{spacing}'", "-frames:v", str(frames)]
            + ["-fps_mode", "passthrough", "-video_track_timescale", "60", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
        )
        stream = ffmpeg.ffprobe_json(out)["streams"][0]
        if stream["r_frame_rate"] == stream["avg_frame_rate"]:
            return out
    raise AssertionError("no frame count gave matching rate fields")


def make_peaky(out: Path) -> Path:
    """Quiet white noise with a clipped spike: loudnorm must limit to honour the true-peak ceiling."""
    ffmpeg.run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=d=6:c=white:r=48000:a=0.05:s=7",
            "-af",
            "volume=enable='between(t,1,1.01)':volume=15,pan=stereo|c0=c0|c1=c0",
            "-c:a",
            "pcm_s16le",
            str(out),
        ]
    )
    return out


# ------------------------------------------------------------------ pure validation (no ffmpeg run)


def test_normalize_color_accepts_hex_and_names_only() -> None:
    assert ffmpeg.normalize_color("#336699") == "0x336699"
    assert ffmpeg.normalize_color("0xabcdef") == "0xABCDEF"
    assert ffmpeg.normalize_color("Red") == "red"
    for bad in ("#12345", "0x1234567", "336699", "red:s=10x10", "white,drawtext=text=x", "", "red@0.5"):
        with pytest.raises(ValueError):
            ffmpeg.normalize_color(bad)


def test_escape_filter_value_escapes_both_levels() -> None:
    assert ffmpeg.escape_filter_value("/a/b.ttf") == "/a/b.ttf"
    assert ffmpeg.escape_filter_value("a:b") == "a\\\\:b"
    assert ffmpeg.escape_filter_value("it's") == "it\\\\\\'s"
    assert ffmpeg.escape_filter_value("x,y;[z]") == "x\\,y\\;\\[z\\]"


@pytest.mark.parametrize(
    "call",
    [
        lambda out: ffmpeg.color_clip(out / "a.mp4", 1081, 1920, 30, 1.0, "red"),
        lambda out: ffmpeg.color_clip(out / "a.mp4", 1080, 1920, 0, 1.0, "red"),
        lambda out: ffmpeg.color_clip(out / "a.mp4", 1080, 1920, 30, 0.0, "red"),
        lambda out: ffmpeg.color_clip(out / "a.avi", 1080, 1920, 30, 1.0, "red"),
        lambda out: ffmpeg.color_clip(out / "a.mp4", 1080, 1920, 30, 1.0, "red:s=2x2"),
        lambda out: ffmpeg.tone(out / "t.wav", 1.0, 30_000.0),
        lambda out: ffmpeg.tone(out / "t.wav", 1.0, 440.0, channels=3),
        lambda out: ffmpeg.tone(out / "t.wav", 1.0, 440.0, amplitude=1.5),
        lambda out: ffmpeg.tone(out / "t.mp3", 1.0, 440.0),
        lambda out: ffmpeg.noise(out / "n.wav", 1.0, 1, color="plaid"),
        lambda out: ffmpeg.silence(out / "s.wav", -1.0),
        lambda out: ffmpeg.concat_videos(out / "c.mp4", []),
        lambda out: ffmpeg.concat_audio(out / "c.wav", []),
        lambda out: ffmpeg.mix_audio(out / "m.wav", out / "v.wav", out / "b.wav", bed_gain_db=3.0),
        lambda out: ffmpeg.loudnorm_two_pass(out / "l.wav", out / "x.wav", target_lufs=0.0),
        lambda out: ffmpeg.loudnorm_two_pass(out / "l.wav", out / "x.wav", true_peak_db=1.0),
    ],
)
def test_invalid_arguments_are_refused_before_rendering(tmp_path: Path, call: Callable[[Path], Path]) -> None:
    with pytest.raises(ValueError):
        call(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_missing_tools_raise_a_clear_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ffmpeg.FFMPEG_ENV, raising=False)
    monkeypatch.delenv(ffmpeg.FFPROBE_ENV, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(MediaToolMissing, match="ffmpeg not found"):
        ffmpeg.ffmpeg_bin()
    with pytest.raises(MediaToolMissing, match="ffprobe not found"):
        ffmpeg.ffprobe_bin()
    monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(tmp_path / "nope"))
    with pytest.raises(MediaToolMissing, match="does not exist"):
        ffmpeg.ffmpeg_bin()
    with pytest.raises(MediaToolMissing):
        ffmpeg.color_clip(tmp_path / "a.mp4", 64, 64, 30, 1.0, "red")
    assert partial_files(tmp_path) == []


def test_font_selection_honours_the_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ffmpeg.FONT_ENV, "none")
    assert ffmpeg.find_font() is None
    assert ffmpeg.drawtext_available() is False
    monkeypatch.setenv(ffmpeg.FONT_ENV, str(tmp_path / "missing.ttf"))
    with pytest.raises(MediaError, match="does not exist"):
        ffmpeg.find_font()
    font = tmp_path / "font.ttf"
    font.write_bytes(b"not really a font")
    monkeypatch.setenv(ffmpeg.FONT_ENV, str(font))
    assert ffmpeg.find_font() == font


# ------------------------------------------------------------------ probe


@media
def test_probe_is_exact_on_a_vertical_1080x1920_30fps_clip(tmp_path: Path) -> None:
    clip = ffmpeg.color_clip(tmp_path / "short.mp4", 1080, 1920, 30, 2.0, "#336699")
    p = qa.probe(clip)
    assert (p.width, p.height) == (1080, 1920)
    assert (p.fps_num, p.fps_den) == (30, 1)
    assert p.fps == 30.0
    assert p.constant_frame_rate is True
    assert p.duration_s == pytest.approx(2.0, abs=1e-6)
    assert p.has_video is True and p.has_audio is False
    assert p.video_codec == "h264" and p.audio_codec is None
    assert p.pix_fmt == "yuv420p"
    stream = ffmpeg.ffprobe_json(clip)["streams"][0]
    assert int(stream["nb_frames"]) == 60
    assert stream["color_space"] == "bt709"


@media
def test_probe_detects_variable_frame_rate(tmp_path: Path) -> None:
    p = qa.probe(make_vfr(tmp_path / "vfr.mp4"))
    assert p.has_video is True
    assert p.constant_frame_rate is False


@media
@pytest.mark.parametrize("suffix", [".mp4", ".mov", ".mkv"])
@pytest.mark.parametrize("fps", [24, 25, 30, Fraction(30000, 1001), 60], ids=["24", "25", "30", "29.97", "60"])
def test_a_constant_rate_render_is_never_reported_variable(tmp_path: Path, suffix: str, fps: int | Fraction) -> None:
    """No false alarm: a compliant file must not be rejected (and regenerated). MKV counts milliseconds, where a
    30 fps frame lasts 33.33 ticks: the spacing check tolerates the one-tick rounding."""
    clip = ffmpeg.color_clip(tmp_path / f"c{suffix}", 128, 72, fps, 2.0, "red")
    p = qa.probe(clip)
    assert p.constant_frame_rate is True
    assert Fraction(p.fps_num, p.fps_den) == Fraction(fps)
    assert codes(qa.check_render(clip, 128, 72, fps, 2.0)) == {"no_audio"}  # the clip carries no audio: nothing else


@media
def test_probe_audio_only_file(tmp_path: Path) -> None:
    p = qa.probe(ffmpeg.tone(tmp_path / "t.wav", 1.5, 440.0))
    assert p.has_video is False and p.has_audio is True
    assert (p.width, p.height, p.fps_num, p.fps_den) == (0, 0, 0, 1)
    assert p.constant_frame_rate is False
    assert (p.audio_codec, p.sample_rate, p.channels) == ("pcm_s16le", 48_000, 2)
    assert p.duration_s == pytest.approx(1.5, abs=1e-6)


@media
def test_probe_of_a_non_media_file_raises_ffmpeg_error(tmp_path: Path) -> None:
    junk = tmp_path / "junk.mp4"
    junk.write_text("this is not a video")
    with pytest.raises(FFmpegError) as err:
        qa.probe(junk)
    assert err.value.returncode not in (0, None)
    assert "ffprobe failed (exit" in str(err.value)
    assert err.value.stderr.strip()


# ------------------------------------------------------------------ determinism


def render_chain(folder: Path) -> dict[str, Path]:
    """One of everything, as the pipeline chains them."""
    folder.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    out["clip_a"] = ffmpeg.color_clip(folder / "a.mp4", 360, 640, 30, 1.0, "#224466", label="Scene 1: it's [on]")
    out["image"] = ffmpeg.still_image(folder / "i.png", 320, 180, "#aa3300", label="still")
    out["clip_b"] = ffmpeg.image_clip(folder / "b.mp4", out["image"], 1.0, 25, band_color="#00ff00", label="moving")
    out["concat"] = ffmpeg.concat_videos(folder / "c.mp4", [out["clip_a"], out["clip_b"]])
    out["clip_c"] = ffmpeg.color_clip(folder / "cc.mp4", 360, 640, 30, 0.5, "#664422")
    out["joined"] = ffmpeg.concat_videos(folder / "j.mp4", [out["clip_a"], out["clip_c"]])
    out["scaled"] = ffmpeg.scale_pad(folder / "s.mp4", out["concat"], 640, 360, 30)
    out["voice1"] = ffmpeg.tone(folder / "v1.wav", 0.75, 220.0)
    out["voice2"] = ffmpeg.tone(folder / "v2.wav", 1.25, 247.5)
    out["voice"] = ffmpeg.concat_audio(folder / "v.wav", [out["voice1"], out["voice2"]])
    out["music"] = ffmpeg.chord(folder / "m.wav", 2.0, [110.0, 165.0, 220.0])
    out["sfx"] = ffmpeg.noise(folder / "n.wav", 0.5, 42)
    out["gap"] = ffmpeg.silence(folder / "g.wav", 0.25)
    out["mix"] = ffmpeg.mix_audio(folder / "mix.wav", out["voice"], out["music"])
    out["norm"] = ffmpeg.loudnorm_two_pass(folder / "norm.wav", out["mix"])
    out["render"] = ffmpeg.mux(folder / "render.mp4", out["scaled"], out["norm"])
    return out


@media
def test_same_inputs_give_the_same_bytes_across_two_renders(tmp_path: Path) -> None:
    first = render_chain(tmp_path / "one")
    second = render_chain(tmp_path / "two")
    assert {k: sha(p) for k, p in first.items()} == {k: sha(p) for k, p in second.items()}
    assert len({sha(p) for p in first.values()}) == len(first)  # nothing degenerate: every output differs
    assert qa.check_render(first["render"], 640, 360, 30, 2.0) == []


@media
def test_vertical_1080x1920_render_is_deterministic(tmp_path: Path) -> None:
    a = ffmpeg.color_clip(tmp_path / "a.mp4", 1080, 1920, 30, 1.0, "#336699", label="hook")
    b = ffmpeg.color_clip(tmp_path / "sub" / "b.mp4", 1080, 1920, 30, 1.0, "#336699", label="hook")
    assert sha(a) == sha(b)


@media
def test_different_inputs_give_different_bytes(tmp_path: Path) -> None:
    base = sha(ffmpeg.color_clip(tmp_path / "a.mp4", 320, 240, 30, 1.0, "#336699"))
    assert sha(ffmpeg.color_clip(tmp_path / "b.mp4", 320, 240, 30, 1.0, "#339966")) != base
    assert sha(ffmpeg.color_clip(tmp_path / "c.mp4", 320, 240, 25, 1.0, "#336699")) != base
    assert sha(ffmpeg.color_clip(tmp_path / "d.mp4", 320, 240, 30, 1.2, "#336699")) != base
    assert sha(ffmpeg.tone(tmp_path / "t1.wav", 1.0, 440.0)) != sha(ffmpeg.tone(tmp_path / "t2.wav", 1.0, 440.01))
    assert sha(ffmpeg.noise(tmp_path / "n1.wav", 1.0, 1)) != sha(ffmpeg.noise(tmp_path / "n2.wav", 1.0, 2))
    assert sha(ffmpeg.noise(tmp_path / "n3.wav", 1.0, 1)) == sha(ffmpeg.noise(tmp_path / "n4.wav", 1.0, 1))


@media
def test_label_is_drawn_when_a_font_exists_and_skipped_otherwise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    font = ffmpeg.find_font()
    if font is None or not ffmpeg.drawtext_available():
        pytest.skip("no font or no drawtext filter in this ffmpeg build")
    plain = sha(ffmpeg.color_clip(tmp_path / "plain.mp4", 320, 240, 30, 0.5, "#336699"))
    hostile = "It's 50% off: [now], really; %{pts} \\ done"
    labelled = sha(ffmpeg.color_clip(tmp_path / "label.mp4", 320, 240, 30, 0.5, "#336699", label=hostile))
    other = sha(ffmpeg.color_clip(tmp_path / "other.mp4", 320, 240, 30, 0.5, "#336699", label="another label"))
    assert len({plain, labelled, other}) == 3

    # the same font behind a path full of filtergraph metacharacters renders the very same bytes
    odd_dir = tmp_path / "we'ird: [fonts], x; y"
    odd_dir.mkdir()
    shutil.copy(font, odd_dir / font.name)
    monkeypatch.setenv(ffmpeg.FONT_ENV, str(odd_dir / font.name))
    assert sha(ffmpeg.color_clip(tmp_path / "odd.mp4", 320, 240, 30, 0.5, "#336699", label=hostile)) == labelled

    monkeypatch.setenv(ffmpeg.FONT_ENV, "none")
    assert sha(ffmpeg.color_clip(tmp_path / "nofont.mp4", 320, 240, 30, 0.5, "#336699", label=hostile)) == plain


@media
def test_no_shell_is_involved(tmp_path: Path) -> None:
    out = tmp_path / "x $(touch pwned) ; touch pwned2 .mp4"
    ffmpeg.color_clip(out, 64, 64, 10, 0.2, "red")
    assert out.is_file()
    assert not (tmp_path / "pwned").exists() and not (tmp_path / "pwned2").exists()


@media
def test_relative_paths_that_look_like_options_or_protocols(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clip = ffmpeg.color_clip(Path("-clip:1.mp4"), 64, 64, 10, 0.5, "red")
    voice = ffmpeg.tone(Path("-voice:fr.wav"), 0.5, 440.0)
    joined = ffmpeg.concat_videos(Path("sub") / "-joined:x.mp4", [clip, clip])
    final = ffmpeg.mux(Path("-final:v1.mp4"), joined, voice)
    p = qa.probe(final)
    assert (p.has_video, p.has_audio) == (True, True)
    assert p.duration_s == pytest.approx(1.0, abs=0.03)
    assert (tmp_path / "-final:v1.mp4").is_file()


# ------------------------------------------------------------------ audio


@media
def test_audio_generators_are_exact_to_the_sample(tmp_path: Path) -> None:
    frames, channels, rate, _ = wav_frames(ffmpeg.tone(tmp_path / "t.wav", 1.2345, 440.0))
    assert (frames, channels, rate) == (59_256, 2, 48_000)
    frames, channels, rate, data = wav_frames(ffmpeg.silence(tmp_path / "s.wav", 0.5, channels=1))
    assert (frames, channels, rate) == (24_000, 1, 48_000)
    assert data == bytes(len(data))
    frames, channels, _, _ = wav_frames(ffmpeg.noise(tmp_path / "n.wav", 0.75, 9))
    assert (frames, channels) == (36_000, 2)
    frames, _, rate, _ = wav_frames(ffmpeg.chord(tmp_path / "c.wav", 2.0, [100.0, 150.0], 44_100))
    assert (frames, rate) == (88_200, 44_100)


@media
def test_concat_audio_and_mix_keep_durations(tmp_path: Path) -> None:
    a = ffmpeg.tone(tmp_path / "a.wav", 0.5, 220.0, channels=1)
    b = ffmpeg.silence(tmp_path / "b.wav", 0.25)
    c = ffmpeg.tone(tmp_path / "c.wav", 0.75, 330.0)
    joined = ffmpeg.concat_audio(tmp_path / "j.wav", [a, b, c])
    frames, channels, _, _ = wav_frames(joined)
    assert (frames, channels) == (72_000, 2)
    bed = ffmpeg.chord(tmp_path / "bed.wav", 5.0, [80.0, 120.0])
    mixed = ffmpeg.mix_audio(tmp_path / "mix.wav", joined, bed)
    assert wav_frames(mixed)[0] == 72_000  # the mix lasts as long as the voice
    voice_lufs, _ = qa.loudness(joined)
    mixed_lufs, _ = qa.loudness(mixed)
    assert abs(mixed_lufs - voice_lufs) < 1.0  # the bed sits well under the voice


@media
def test_loudness_of_silence(tmp_path: Path) -> None:
    integrated, peak = qa.loudness(ffmpeg.silence(tmp_path / "s.wav", 1.0))
    assert integrated == -70.0
    assert peak == float("-inf")


@media
@pytest.mark.parametrize("amplitude", [0.02, 0.08, 0.95])
def test_loudnorm_brings_a_tone_to_minus_14_lufs_under_minus_1_dbtp(tmp_path: Path, amplitude: float) -> None:
    src = ffmpeg.tone(tmp_path / "src.wav", 5.0, 440.0, amplitude=amplitude)
    before, _ = qa.loudness(src)
    assert abs(before + 14.0) > 2.0  # the source really is off target
    out = ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", src)
    integrated, peak = qa.loudness(out)
    assert abs(integrated + 14.0) <= 1.0
    assert peak <= -1.0
    assert wav_frames(out)[:3] == (240_000, 2, 48_000)


@media
def test_loudnorm_limits_a_peaky_source_and_honours_other_targets(tmp_path: Path) -> None:
    src = make_peaky(tmp_path / "peaky.wav")
    _, source_peak = qa.loudness(src)
    assert source_peak > -1.0
    integrated, peak = qa.loudness(ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", src))
    assert abs(integrated + 14.0) <= 1.0
    assert peak <= -1.0
    integrated, peak = qa.loudness(ffmpeg.loudnorm_two_pass(tmp_path / "out23.wav", src, -23.0, -2.0))
    assert abs(integrated + 23.0) <= 1.0
    assert peak <= -2.0


@media
def test_loudnorm_refuses_silence(tmp_path: Path) -> None:
    with pytest.raises(MediaError, match="silent") as err:
        ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", ffmpeg.silence(tmp_path / "s.wav", 2.0))
    assert "shorter" not in str(err.value)
    assert not (tmp_path / "out.wav").exists()
    assert partial_files(tmp_path) == []


# ------------------------------------------------------------------ video assembly


@media
def test_concat_videos_joins_clips_of_different_sizes_and_rates(tmp_path: Path) -> None:
    a = ffmpeg.color_clip(tmp_path / "a.mp4", 320, 240, 30, 1.0, "red")
    b = ffmpeg.color_clip(tmp_path / "b.mp4", 640, 360, 25, 1.0, "blue")
    joined = qa.probe(ffmpeg.concat_videos(tmp_path / "j.mp4", [a, b]))
    assert (joined.width, joined.height, joined.fps_num, joined.fps_den) == (320, 240, 30, 1)
    assert joined.constant_frame_rate is True
    assert joined.duration_s == pytest.approx(2.0, abs=1e-6)
    forced = qa.probe(ffmpeg.concat_videos(tmp_path / "f.mp4", [a, b, a], width=1080, height=1920, fps=Fraction(24)))
    assert (forced.width, forced.height, forced.fps_num) == (1080, 1920, 24)
    assert forced.duration_s == pytest.approx(3.0, abs=1e-6)
    assert forced.has_audio is False


def packet_hashes(path: Path) -> list[str]:
    """SHA-256 of every compressed video packet, in stream order."""
    cmd = [ffmpeg.ffprobe_bin(), "-v", "error", "-select_streams", "v:0", "-show_data_hash", "sha256"]
    cmd += ["-show_entries", "packet=data_hash", "-of", "csv=p=0", str(path)]
    lines = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split()
    assert lines
    return lines


@media
def test_concat_videos_joins_matching_clips_losslessly(tmp_path: Path) -> None:
    a = ffmpeg.color_clip(tmp_path / "it's a.mp4", 320, 240, 30, 1.0, "red", label="one")
    b = ffmpeg.color_clip(tmp_path / "b.mp4", 320, 240, 30, 0.7, "blue")
    joined = ffmpeg.concat_videos(tmp_path / "j.mp4", [a, b, a])
    p = qa.probe(joined)
    assert (p.width, p.height, p.fps_num, p.constant_frame_rate) == (320, 240, 30, True)
    assert p.duration_s == pytest.approx(2.7, abs=1e-6)
    # stream copy: the compressed packets are the source packets, untouched
    assert packet_hashes(joined) == packet_hashes(a) + packet_hashes(b) + packet_hashes(a)
    ffmpeg.run_ffmpeg(["-xerror", "-i", str(joined), "-f", "null", "-"])  # decodes end to end without error
    reencoded = ffmpeg.concat_videos(tmp_path / "r.mp4", [a, b, a], fps=25)
    r = qa.probe(reencoded)
    assert (r.fps_num, r.constant_frame_rate) == (25, True)
    assert r.duration_s == pytest.approx(2.72, abs=1e-6)  # 30 + 21 + 30 frames re-timed to 25 fps: 68 frames
    assert packet_hashes(reencoded) != packet_hashes(joined)


@media
def test_scale_pad_reformats_and_keeps_audio(tmp_path: Path) -> None:
    clip = ffmpeg.color_clip(tmp_path / "a.mp4", 320, 240, 25, 2.0, "red")
    vertical = qa.probe(ffmpeg.scale_pad(tmp_path / "v.mp4", clip, 1080, 1920, 30))
    assert (vertical.width, vertical.height, vertical.fps_num, vertical.fps_den) == (1080, 1920, 30, 1)
    assert vertical.constant_frame_rate is True
    assert vertical.duration_s == pytest.approx(2.0, abs=1e-6)
    assert vertical.has_audio is False
    with_audio = ffmpeg.mux(tmp_path / "m.mp4", clip, ffmpeg.tone(tmp_path / "t.wav", 2.0, 440.0))
    wide = qa.probe(ffmpeg.scale_pad(tmp_path / "w.mp4", with_audio, 1920, 1080, 30))
    assert (wide.width, wide.height, wide.has_audio, wide.audio_codec) == (1920, 1080, True, "aac")


@media
@pytest.mark.parametrize("audio_s", [1.3, 2.0, 3.7])
def test_mux_fits_the_audio_to_the_video(tmp_path: Path, audio_s: float) -> None:
    video = ffmpeg.color_clip(tmp_path / "v.mp4", 320, 240, 30, 2.0, "red")
    muxed = ffmpeg.mux(tmp_path / "m.mp4", video, ffmpeg.tone(tmp_path / "t.wav", audio_s, 440.0))
    p = qa.probe(muxed)
    assert p.has_video and p.has_audio
    assert p.duration_s == pytest.approx(2.0, abs=0.03)
    streams = {s["codec_type"]: s for s in ffmpeg.ffprobe_json(muxed)["streams"]}
    assert float(streams["audio"]["duration"]) == pytest.approx(2.0, abs=0.03)
    assert sha(muxed) != sha(video)


# ------------------------------------------------------------------ failures and concurrency


@media
def test_failed_render_leaves_no_partial_file_and_keeps_the_previous_output(tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    ffmpeg.color_clip(out, 64, 64, 10, 0.2, "red")
    before = sha(out)
    junk = tmp_path / "junk.wav"
    junk.write_text("garbage")
    video = ffmpeg.color_clip(tmp_path / "v.mp4", 64, 64, 10, 0.5, "blue")
    with pytest.raises(FFmpegError, match="ffmpeg failed"):
        ffmpeg.mux(out, video, junk)  # fails inside ffmpeg, after the output was reserved
    assert sha(out) == before
    assert partial_files(tmp_path) == []
    with pytest.raises(FFmpegError, match="ffprobe failed"):
        ffmpeg.concat_videos(out, [video, tmp_path / "junk.wav"])
    assert sha(out) == before


@media
def test_timeout_kills_ffmpeg_mid_write_and_cleans_up(tmp_path: Path) -> None:
    out = tmp_path / "long.mp4"
    # 90 s of 1080x1920 take several seconds to encode: far above the timeout, yet a broken `timeout_s` fails
    # this test in seconds instead of letting the encode run to the end
    with pytest.raises(FFmpegError, match="timed out") as err:
        ffmpeg.color_clip(out, 1080, 1920, 30, 90.0, "red", timeout_s=1.5)
    assert err.value.returncode is None
    assert not out.exists()
    assert partial_files(tmp_path) == []


@media
def test_concurrent_renders_of_the_same_output_are_safe(tmp_path: Path) -> None:
    reference = sha(ffmpeg.color_clip(tmp_path / "ref.mp4", 320, 240, 30, 1.0, "#123456", label="same"))
    target = tmp_path / "shared" / "clip.mp4"
    barrier = threading.Barrier(6)

    def render(_: int) -> str:
        barrier.wait()
        return sha(ffmpeg.color_clip(target, 320, 240, 30, 1.0, "#123456", label="same"))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(render, range(6)))
    assert set(results) == {reference}
    assert sha(target) == reference
    assert partial_files(tmp_path) == []


# ------------------------------------------------------------------ check_render


@pytest.fixture(scope="module")
def renders(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    require_ffmpeg()
    d = tmp_path_factory.mktemp("renders")
    video = ffmpeg.color_clip(d / "video.mp4", 1080, 1920, 30, 2.0, "#336699")
    tone = ffmpeg.tone(d / "tone.wav", 2.0, 440.0)
    quiet = ffmpeg.tone(d / "quiet.wav", 2.0, 440.0, amplitude=0.01)
    hot = ffmpeg.tone(d / "hot.wav", 2.0, 440.0, amplitude=0.99)
    wrong_size = ffmpeg.scale_pad(d / "small.mp4", video, 720, 1280, 30)
    audio_only = d / "audio.m4a"
    ffmpeg.run_ffmpeg(["-i", str(tone), "-c:a", "aac", str(audio_only)])
    norm = ffmpeg.loudnorm_two_pass(d / "norm.wav", tone)
    return {
        "good": ffmpeg.mux(d / "good.mp4", video, norm),
        "silent_track_missing": video,
        "too_quiet": ffmpeg.mux(d / "quiet.mp4", video, quiet),
        "too_hot": ffmpeg.mux(d / "hot.mp4", video, hot),
        "wrong_size": ffmpeg.mux(d / "wrong_size.mp4", wrong_size, norm),
        "vfr": make_vfr(d / "vfr.mp4"),
        "audio_only": audio_only,
    }


def codes(defects: list[str]) -> set[str]:
    return {d.split(":", 1)[0] for d in defects}


@media
def test_check_render_passes_a_compliant_short(renders: dict[str, Path]) -> None:
    assert qa.check_render(renders["good"], 1080, 1920, 30, 2.0) == []


@media
def test_check_render_detects_wrong_resolution(renders: dict[str, Path]) -> None:
    defects = qa.check_render(renders["wrong_size"], 1080, 1920, 30, 2.0)
    assert codes(defects) == {"resolution"}
    assert "720x1280" in defects[0]
    assert codes(qa.check_render(renders["good"], 1920, 1080, 30, 2.0)) == {"resolution"}


@media
def test_check_render_detects_wrong_duration(renders: dict[str, Path]) -> None:
    assert codes(qa.check_render(renders["good"], 1080, 1920, 30, 2.5)) == {"duration"}
    assert codes(qa.check_render(renders["good"], 1080, 1920, 30, 1.85)) == {"duration"}
    assert qa.check_render(renders["good"], 1080, 1920, 30, 2.08) == []  # inside the 0.1 s tolerance
    assert qa.check_render(renders["good"], 1080, 1920, 30, 2.5, tolerance_s=0.6) == []


@media
def test_check_render_detects_missing_audio_track(renders: dict[str, Path]) -> None:
    defects = qa.check_render(renders["silent_track_missing"], 1080, 1920, 30, 2.0)
    assert codes(defects) == {"no_audio"}


@media
def test_check_render_detects_loudness_off_target(renders: dict[str, Path]) -> None:
    assert codes(qa.check_render(renders["too_quiet"], 1080, 1920, 30, 2.0)) == {"loudness"}
    assert codes(qa.check_render(renders["too_hot"], 1080, 1920, 30, 2.0)) == {"loudness", "true_peak"}
    # the targets are parameters, not constants
    integrated, _ = qa.loudness(renders["too_quiet"])
    assert qa.check_render(renders["too_quiet"], 1080, 1920, 30, 2.0, lufs_target=integrated) == []


@media
def test_check_render_detects_frame_rate_problems(renders: dict[str, Path]) -> None:
    assert codes(qa.check_render(renders["good"], 1080, 1920, 25, 2.0)) == {"frame_rate"}
    vfr = qa.check_render(renders["vfr"], 320, 240, 30, 3.8)
    assert {"variable_frame_rate", "no_audio"} <= codes(vfr)


@media
def test_check_render_tells_29_97_from_30_fps(tmp_path: Path) -> None:
    ntsc = ffmpeg.color_clip(tmp_path / "ntsc.mp4", 320, 240, Fraction(30000, 1001), 2.0, "red")
    p = qa.probe(ntsc)
    assert (p.fps_num, p.fps_den, p.constant_frame_rate) == (30000, 1001, True)
    assert "frame_rate" in codes(qa.check_render(ntsc, 320, 240, 30, p.duration_s))
    assert "frame_rate" not in codes(qa.check_render(ntsc, 320, 240, Fraction(30000, 1001), p.duration_s))


@media
def test_check_render_loudness_window_is_plus_or_minus_one_lufs(tmp_path: Path, renders: dict[str, Path]) -> None:
    """MISSION §8: -14 LUFS ±1. Renders 0.8 LU inside the window pass, 1.2 LU outside it are reported (defaults)."""
    video = renders["silent_track_missing"]
    tone = ffmpeg.tone(tmp_path / "tone.wav", 2.0, 440.0, amplitude=0.3)
    for target, expected in ((-13.2, set()), (-14.8, set()), (-12.8, {"loudness"}), (-15.2, {"loudness"})):
        norm = ffmpeg.loudnorm_two_pass(tmp_path / f"n{target}.wav", tone, target_lufs=target)
        render = ffmpeg.mux(tmp_path / f"r{target}.mp4", video, norm)
        assert codes(qa.check_render(render, 1080, 1920, 30, 2.0)) == expected, target


@media
def test_check_render_reports_unreadable_and_video_less_files(tmp_path: Path, renders: dict[str, Path]) -> None:
    junk = tmp_path / "junk.mp4"
    junk.write_bytes(b"\x00" * 64)
    defects = qa.check_render(junk, 1080, 1920, 30, 2.0)
    assert codes(defects) == {"unreadable"}
    assert codes(qa.check_render(tmp_path / "missing.mp4", 1080, 1920, 30, 2.0)) == {"unreadable"}
    assert "no_video" in codes(qa.check_render(renders["audio_only"], 1080, 1920, 30, 2.0))


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
    assert kind == "skip" and REQUIRE_MEDIA_ENV in reason  # the reason says how to make it a failure
    for off in ("", "0", "false", "No", "OFF"):
        monkeypatch.setenv(REQUIRE_MEDIA_ENV, off)
        assert guard_outcome(available=False)[0] == "skip", off
    for on in ("1", "true", "yes", "anything"):  # an unknown value fails closed
        monkeypatch.setenv(REQUIRE_MEDIA_ENV, on)
        kind, reason = guard_outcome(available=False)
        assert kind == "fail" and "mandatory" in reason, on
        assert guard_outcome(available=True)[0] == "run", on  # with ffmpeg the proofs simply run


def run_pytest(args: list[str], *, path: str | None = None, **env: str) -> subprocess.CompletedProcess[str]:
    """pytest in a child process (the interpreter is called by absolute path, so `path` may hide ffmpeg)."""
    hidden = {REQUIRE_MEDIA_ENV, ffmpeg.FFMPEG_ENV, ffmpeg.FFPROBE_ENV}
    child_env = {k: v for k, v in os.environ.items() if k not in hidden}
    child_env.update(env)
    if path is not None:
        child_env["PATH"] = path
    cmd = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider", *args]
    return subprocess.run(cmd, cwd=REPO, env=child_env, capture_output=True, text=True, timeout=300, check=False)


@pytest.mark.parametrize(
    "target",
    [
        "tests/unit/test_media.py::test_probe_is_exact_on_a_vertical_1080x1920_30fps_clip",
        "tests/unit/test_mock_adapters.py::test_default_tts_speaks_eight_words_in_exactly_three_seconds",
    ],
)
def test_a_green_run_cannot_hide_missing_media_proofs(target: str, tmp_path: Path) -> None:
    """The review's situation: no ffmpeg on PATH. The skip is loud, and STUDIO_REQUIRE_MEDIA turns it into a failure."""
    no_ffmpeg = tmp_path / "empty-path"
    no_ffmpeg.mkdir()
    lenient = run_pytest([target, "-rs"], path=str(no_ffmpeg))
    assert lenient.returncode == 0 and "1 skipped" in lenient.stdout, lenient.stdout + lenient.stderr
    assert REQUIRE_MEDIA_ENV in lenient.stdout
    strict = run_pytest([target], path=str(no_ffmpeg), **{REQUIRE_MEDIA_ENV: "1"})
    assert strict.returncode == 1, strict.stdout + strict.stderr
    assert re.search(r"\b1 (failed|error)", strict.stdout) and "skipped" not in strict.stdout, strict.stdout


MANDATORY_MEDIA_PROOFS = (
    "test_probe_is_exact_on_a_vertical_1080x1920_30fps_clip",
    "test_probe_detects_variable_frame_rate",
    "test_same_inputs_give_the_same_bytes_across_two_renders",
    "test_different_inputs_give_different_bytes",
    "test_loudnorm_brings_a_tone_to_minus_14_lufs_under_minus_1_dbtp",
    "test_check_render_detects_wrong_resolution",
    "test_check_render_detects_wrong_duration",
    "test_check_render_detects_missing_audio_track",
    "test_check_render_detects_loudness_off_target",
    "test_render_commands_carry_every_determinism_flag",
    "test_renders_do_not_depend_on_the_cpu_simd_level",
    "test_media_fingerprint_is_short_and_stable_across_calls_and_processes",
)


def test_mandatory_proofs_are_selected_by_the_media_marker() -> None:
    for name in MANDATORY_MEDIA_PROOFS:
        marks = {m.name for m in getattr(globals()[name], "pytestmark", [])}
        assert "media" in marks, name
        assert "usefixtures" in marks, name  # skips or fails, never passes vacuously, without ffmpeg


def test_the_media_marker_collects_every_mandatory_proof() -> None:
    """`pytest -m media` really lists them (the review found a mandatory proof missing from that selection)."""
    listing = run_pytest(["tests/unit/test_media.py", "-m", "media", "--collect-only"])
    assert listing.returncode == 0, listing.stdout + listing.stderr
    for name in MANDATORY_MEDIA_PROOFS:
        assert f"::{name}" in listing.stdout, name


class ExecRecorder:
    """Spy on `ffmpeg._exec`: records every command line and its timeout, then runs it for real."""

    def __init__(self, real: Callable[[list[str], float], subprocess.CompletedProcess[str]]) -> None:
        self.real = real
        self.calls: list[tuple[list[str], float]] = []

    def __call__(self, cmd: list[str], timeout_s: float) -> subprocess.CompletedProcess[str]:
        self.calls.append((list(cmd), timeout_s))
        return self.real(cmd, timeout_s)

    def ffmpeg_runs(self) -> list[tuple[list[str], float]]:
        tool = ffmpeg.ffmpeg_bin()
        return [(c, t) for c, t in self.calls if c[0] == tool and "-filters" not in c and "-version" not in c]

    def renders(self) -> list[tuple[list[str], float]]:
        return [(c, t) for c, t in self.ffmpeg_runs() if ".partial-" in c[-1]]


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> ExecRecorder:
    spy = ExecRecorder(ffmpeg._exec)
    monkeypatch.setattr(ffmpeg, "_exec", spy)
    return spy


def has_pair(cmd: list[str], flag: str, value: str) -> bool:
    return any(a == flag and b == value for a, b in zip(cmd, cmd[1:], strict=False))


@pytest.fixture(scope="module")
def flag_sources(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    require_ffmpeg()
    d = tmp_path_factory.mktemp("flag-sources")
    clip = ffmpeg.color_clip(d / "clip.mp4", 64, 64, 10, 0.5, "red")
    tone = ffmpeg.tone(d / "tone.wav", 1.0, 440.0, amplitude=0.1)
    return {
        "clip": clip,
        "clip2": ffmpeg.color_clip(d / "clip2.mp4", 64, 64, 10, 0.5, "blue"),
        "wide": ffmpeg.color_clip(d / "wide.mp4", 96, 64, 10, 0.5, "green"),
        "image": ffmpeg.still_image(d / "image.png", 64, 64, "#336699"),
        "tone": tone,
        "bed": ffmpeg.chord(d / "bed.wav", 1.0, [110.0, 165.0]),
        "with_audio": ffmpeg.mux(d / "with_audio.mp4", clip, tone),
    }


T = 123.0  # an explicit timeout: every ffmpeg run of the call must receive it
COMMON = (("-fflags", "+bitexact"), ("-map_metadata", "-1"), ("-filter_threads", "1"))
VIDEO = (("-threads", "1"), ("-pix_fmt", "yuv420p"), ("-fps_mode", "cfr"), ("-flags:v", "+bitexact"))
AUDIO = (("-flags:a", "+bitexact"),)
PNG = (("-threads", "1"), ("-flags:v", "+bitexact"), ("-update", "1"))
COPY = (("-c:v", "copy"),)
FLAG_CASES: dict[str, tuple[Callable[[dict[str, Path], Path], Path], tuple[tuple[str, str], ...]]] = {
    "color_clip": (lambda s, d: ffmpeg.color_clip(d / "o.mp4", 64, 64, 10, 0.5, "red", label="x", timeout_s=T), VIDEO),
    "image_clip": (lambda s, d: ffmpeg.image_clip(d / "o.mp4", s["image"], 0.5, 10, band_color="red", timeout_s=T), VIDEO),
    "still_image": (lambda s, d: ffmpeg.still_image(d / "o.png", 64, 64, "red", label="x", timeout_s=T), PNG),
    "scale_pad": (lambda s, d: ffmpeg.scale_pad(d / "o.mp4", s["with_audio"], 128, 128, 25, timeout_s=T), VIDEO + AUDIO),
    "concat_copy": (lambda s, d: ffmpeg.concat_videos(d / "o.mp4", [s["clip"], s["clip2"]], timeout_s=T), COPY),
    "concat_reencode": (lambda s, d: ffmpeg.concat_videos(d / "o.mp4", [s["clip"], s["wide"]], timeout_s=T), VIDEO),
    "mux": (lambda s, d: ffmpeg.mux(d / "o.mp4", s["clip"], s["tone"], timeout_s=T), AUDIO + COPY),
    "tone": (lambda s, d: ffmpeg.tone(d / "o.wav", 0.5, 440.0, timeout_s=T), AUDIO),
    "chord": (lambda s, d: ffmpeg.chord(d / "o.m4a", 0.5, [220.0, 330.0], timeout_s=T), AUDIO),
    "noise": (lambda s, d: ffmpeg.noise(d / "o.wav", 0.5, 7, timeout_s=T), AUDIO),
    "silence": (lambda s, d: ffmpeg.silence(d / "o.wav", 0.5, timeout_s=T), AUDIO),
    "concat_audio": (lambda s, d: ffmpeg.concat_audio(d / "o.wav", [s["tone"], s["bed"]], timeout_s=T), AUDIO),
    "mix_audio": (lambda s, d: ffmpeg.mix_audio(d / "o.wav", s["tone"], s["bed"], timeout_s=T), AUDIO),
    "loudnorm_two_pass": (lambda s, d: ffmpeg.loudnorm_two_pass(d / "o.wav", s["tone"], timeout_s=T), AUDIO),
}


@media
@pytest.mark.parametrize("name", sorted(FLAG_CASES))
def test_render_commands_carry_every_determinism_flag(
    name: str, flag_sources: dict[str, Path], recorder: ExecRecorder, tmp_path: Path
) -> None:
    call, required = FLAG_CASES[name]
    out = call(flag_sources, tmp_path)
    assert out.is_file()
    [(cmd, _)] = recorder.renders()
    pin = ffmpeg.pinned_cpuflags()
    for flag, value in (*COMMON, *required, *((("-cpuflags", pin),) if pin else ())):
        assert has_pair(cmd, flag, value), f"{name}: {flag} {value} missing from {cmd}"
    runs = recorder.ffmpeg_runs()
    assert runs and all(timeout == T for _, timeout in runs), [t for _, t in runs]
    if pin:  # measurement passes feed the render too (loudnorm parameters)
        assert all(has_pair(c, "-cpuflags", pin) for c, _ in runs)


@media
def test_video_renders_get_a_timeout_proportional_to_the_work(
    tmp_path: Path, recorder: ExecRecorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ffmpeg, "DEFAULT_TIMEOUT_S", 1.0)  # a low floor, so the computed budget shows
    per_1080p_second = ffmpeg.X264_SECONDS_PER_1080P_SECOND * ffmpeg.TIMEOUT_SAFETY
    clip = ffmpeg.color_clip(tmp_path / "v.mp4", 1080, 1920, 30, 2.0, "red")
    assert recorder.renders()[-1][1] == pytest.approx(2.0 * per_1080p_second)
    ffmpeg.scale_pad(tmp_path / "s.mp4", clip, 1920, 1080, 30)
    assert recorder.renders()[-1][1] == pytest.approx(2.0 * per_1080p_second)
    ffmpeg.concat_videos(tmp_path / "c.mp4", [clip, clip])
    assert recorder.renders()[-1][1] == pytest.approx(4.0 * per_1080p_second)
    ffmpeg.tone(tmp_path / "t.wav", 1.0, 440.0)
    assert recorder.renders()[-1][1] == 1.0  # audio work: the module default
    monkeypatch.undo()
    # a 10-minute 4K master is budgeted in hours, not the 900 s that used to kill it at ~3 min of media
    assert ffmpeg.video_timeout_s(600.0, 3840, 2160) == pytest.approx(600 * 4 * per_1080p_second)
    assert ffmpeg.video_timeout_s(0.5, 64, 64) == ffmpeg.DEFAULT_TIMEOUT_S


def test_pinned_cpuflags_follow_the_architecture_and_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ffmpeg.CPUFLAGS_ENV, raising=False)

    def mock_machine(name: str) -> Callable[[], str]:
        return lambda: name

    for machine, expected in (("x86_64", "sse2"), ("AMD64", "sse2"), ("aarch64", "armv8+neon"), ("riscv64", None)):
        monkeypatch.setattr(ffmpeg.platform, "machine", mock_machine(machine))
        assert ffmpeg.pinned_cpuflags() == expected, machine
    monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, "native")
    assert ffmpeg.pinned_cpuflags() is None
    monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, "sse2+ssse3")
    assert ffmpeg.pinned_cpuflags() == "sse2+ssse3"
    monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, "sse2 -i /etc/passwd")
    with pytest.raises(MediaError, match=ffmpeg.CPUFLAGS_ENV):
        ffmpeg.pinned_cpuflags()


def mock_cpu_ffmpeg(folder: Path, name: str, mask: str) -> Path:
    """ffmpeg as it behaves on a CPU with fewer SIMD extensions: `-cpuflags <mask>` forced first."""
    script = folder / f"mock_cpu_{name}_ffmpeg"
    script.write_text(f'#!/bin/sh\nexec {shlex.quote(ffmpeg.ffmpeg_bin())} -cpuflags {shlex.quote(mask)} "$@"\n')
    script.chmod(0o755)
    return script


def cpu_has(*flags: str) -> bool:
    try:
        text = Path("/proc/cpuinfo").read_text()
    except OSError:
        return False
    found = {w for line in text.splitlines() if line.startswith("flags") for w in line.split()}
    return set(flags) <= found


CPU_MASKS = {"avx_only": "-avx2-fma3-avx512-avx512icl", "no_simd": "0"}


@media
def test_renders_do_not_depend_on_the_cpu_simd_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reference = {k: sha(p) for k, p in render_chain(tmp_path / "native").items()}
    for name, mask in CPU_MASKS.items():
        monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(mock_cpu_ffmpeg(tmp_path, name, mask)))
        assert {k: sha(p) for k, p in render_chain(tmp_path / name).items()} == reference, name


@media
def test_without_the_pin_the_aac_encoder_follows_the_cpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The comparison above has teeth: unpinned, the same ffmpeg build encodes different AAC bytes per CPU."""
    if not cpu_has("avx2", "fma"):
        pytest.skip("the unpinned difference shows on AVX2+FMA CPUs only")
    clip = ffmpeg.color_clip(tmp_path / "v.mp4", 64, 64, 10, 1.0, "red")
    voice = ffmpeg.tone(tmp_path / "t.wav", 1.0, 440.0)
    monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, "native")
    native = sha(ffmpeg.mux(tmp_path / "native.mp4", clip, voice))
    monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(mock_cpu_ffmpeg(tmp_path, "avx_only", CPU_MASKS["avx_only"])))
    assert sha(ffmpeg.mux(tmp_path / "avx_only.mp4", clip, voice)) != native


@media
def test_render_environment_names_what_the_bytes_depend_on(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = ffmpeg.render_environment()
    assert set(env) == {"ffmpeg_version", "ffmpeg_build_sha256", "machine", "cpuflags", "font_sha256"}
    assert str(env["ffmpeg_version"]).startswith("ffmpeg version")
    assert env["cpuflags"] == (ffmpeg.pinned_cpuflags() or "native")
    assert ffmpeg.render_environment() == env
    # an older CPU is the same environment: the bytes do not change (test above)
    monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(mock_cpu_ffmpeg(tmp_path, "avx_only", CPU_MASKS["avx_only"])))
    assert ffmpeg.render_environment() == env
    font = tmp_path / "other.ttf"
    font.write_bytes(b"another font")
    monkeypatch.setenv(ffmpeg.FONT_ENV, str(font))
    assert ffmpeg.render_environment()["font_sha256"] == hashlib.sha256(b"another font").hexdigest()
    monkeypatch.setenv(ffmpeg.FONT_ENV, "none")
    assert ffmpeg.render_environment()["font_sha256"] is None
    monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, "native")
    assert ffmpeg.render_environment()["cpuflags"] == "native"


# ------------------------------------------------------------------ media_fingerprint: the guarantee is per build + CPU

FAKE_VERSION = """\
ffmpeg version 6.1.1-3ubuntu5 Copyright (c) 2000-2023 the FFmpeg developers
built with gcc 13 (Ubuntu 13.2.0-23ubuntu3)
configuration: --prefix=/usr --enable-gpl --enable-libx264 --enable-shared
libavutil      58. 29.100 / 58. 29.100
libavcodec     60. 31.102 / 60. 31.102
libavformat    60. 16.100 / 60. 16.100
libavdevice    60.  3.100 / 60.  3.100
libavfilter     9. 12.100 /  9. 12.100
libswscale      7.  5.100 /  7.  5.100
libswresample   4. 12.100 /  4. 12.100
libpostproc    57.  3.100 / 57.  3.100
"""
FAKE_X264 = "core 164 r3108 31e19f9"
FAKE_CPU = "avx avx2 fma sse2"


def simulated_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
    *,
    version: str = FAKE_VERSION,
    x264: str = FAKE_X264,
    cpu: str = FAKE_CPU,
    pin: str | None = None,
    font: Path | None = None,
) -> str:
    """media_fingerprint() of a simulated ffmpeg build on a simulated CPU: nothing is run."""
    monkeypatch.setenv(ffmpeg.FONT_ENV, "none" if font is None else str(font))
    if pin is None:
        monkeypatch.delenv(ffmpeg.CPUFLAGS_ENV, raising=False)
    else:
        monkeypatch.setenv(ffmpeg.CPUFLAGS_ENV, pin)
    monkeypatch.setattr(ffmpeg, "ffmpeg_bin", lambda: "/simulated/ffmpeg")
    monkeypatch.setattr(ffmpeg, "_version_text", lambda _path: version)
    monkeypatch.setattr(ffmpeg, "_x264_core", lambda _path: x264)
    monkeypatch.setattr(ffmpeg, "_cpu_flags", lambda: cpu)
    return ffmpeg.media_fingerprint()


def test_media_fingerprint_is_16_hex_digits_and_stable_for_one_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    first = simulated_fingerprint(monkeypatch)
    assert re.fullmatch(r"[0-9a-f]{16}", first)
    assert simulated_fingerprint(monkeypatch) == first


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("6.1.1-3ubuntu5 Copyright", "6.1.2-1 Copyright"),
        ("built with gcc 13", "built with gcc 14"),
        ("--enable-libx264", "--disable-libx264"),
        ("libavcodec     60. 31.102 / 60. 31.102", "libavcodec     60. 31.103 / 60. 31.103"),
        ("libswresample   4. 12.100 /  4. 12.100", "libswresample   4. 12.101 /  4. 12.101"),
        ("libavfilter     9. 12.100 /  9. 12.100", "libavfilter     9. 13.100 /  9. 13.100"),
        ("libswscale      7.  5.100 /  7.  5.100", "libswscale      7.  6.100 /  7.  6.100"),
    ],
    ids=["version", "compiler", "configuration", "libavcodec", "libswresample", "libavfilter", "libswscale"],
)
def test_media_fingerprint_changes_with_the_ffmpeg_build(monkeypatch: pytest.MonkeyPatch, old: str, new: str) -> None:
    assert old in FAKE_VERSION
    base = simulated_fingerprint(monkeypatch)
    assert simulated_fingerprint(monkeypatch, version=FAKE_VERSION.replace(old, new)) != base


def test_media_fingerprint_changes_with_the_cpu_the_pin_the_x264_core_and_the_font(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = simulated_fingerprint(monkeypatch)
    assert simulated_fingerprint(monkeypatch, cpu="avx sse2") != base  # fewer instruction sets
    assert simulated_fingerprint(monkeypatch, pin="sse2+ssse3") != base
    assert simulated_fingerprint(monkeypatch, x264="core 165 r3200 abcdef0") != base
    font = tmp_path / "other.ttf"
    font.write_bytes(b"another font")
    assert simulated_fingerprint(monkeypatch, font=font) != base
    monkeypatch.setattr(ffmpeg.platform, "machine", lambda: "riscv64")
    assert simulated_fingerprint(monkeypatch) != base


def test_cpu_flags_come_from_the_flags_line_of_cpuinfo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    info = tmp_path / "cpuinfo"
    monkeypatch.setattr(ffmpeg, "CPUINFO_PATH", info)
    machine = ffmpeg.platform.machine().lower()
    info.write_text("processor\t: 0\nflags\t\t: fpu sse2 avx2\nmodel name\t: X\n\nprocessor\t: 1\nflags\t\t: avx2 sse2 fpu\n")
    assert ffmpeg._cpu_flags() == "avx2 fpu sse2"  # order-insensitive; identical cores merge
    info.write_text("processor\t: 0\nflags\t\t: fpu sse2 avx2\n\nprocessor\t: 1\nflags\t\t: fpu sse2\n")
    assert ffmpeg._cpu_flags() == "avx2 fpu sse2|fpu sse2"  # a hybrid CPU keeps both flag sets
    info.write_text("processor\t: 0\nFeatures\t: fp asimd aes\n")
    assert ffmpeg._cpu_flags() == "aes asimd fp"
    info.write_text("model name\t: no flags line here\n")
    assert ffmpeg._cpu_flags() == machine
    monkeypatch.setattr(ffmpeg, "CPUINFO_PATH", tmp_path / "missing")
    assert ffmpeg._cpu_flags() == machine
    monkeypatch.undo()
    assert ffmpeg._cpu_flags()  # this machine: never empty


def test_x264_core_is_read_from_the_stream_ffmpeg_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = (
        "\x00\x00\x01\x06\x05��E�x264 - core 164 r3108 31e19f9 - H.264/MPEG-4 AVC codec - Copyleft 2003-2023"
        " - http://www.videolan.org/x264.html - options: cabac=1 ref=1 deblock=1:0:0"
    )

    def mock_exec(cmd: list[str], timeout_s: float) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, stream, "")

    monkeypatch.setattr(ffmpeg, "_exec", mock_exec)
    assert ffmpeg._x264_core("/simulated/with-x264/ffmpeg") == "core 164 r3108 31e19f9"

    def mock_exec_without_x264(cmd: list[str], timeout_s: float) -> subprocess.CompletedProcess[str]:
        raise FFmpegError(cmd, 1, "Unknown encoder 'libx264'")

    monkeypatch.setattr(ffmpeg, "_exec", mock_exec_without_x264)
    assert ffmpeg._x264_core("/simulated/without-x264/ffmpeg") == "none"


def test_the_module_documents_that_render_steps_carry_the_fingerprint() -> None:
    doc = ffmpeg.__doc__ or ""
    assert "media_fingerprint()" in doc
    assert "MUST" in doc and "parameters" in doc


@media
def test_media_fingerprint_is_short_and_stable_across_calls_and_processes() -> None:
    fingerprint = ffmpeg.media_fingerprint()
    assert re.fullmatch(r"[0-9a-f]{16}", fingerprint)
    assert ffmpeg.media_fingerprint() == fingerprint
    code = "from studio.media import ffmpeg; print(ffmpeg.media_fingerprint())"
    child = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, check=True, timeout=120)
    assert child.stdout.strip() == fingerprint  # a new process computes the same value


@media
def test_the_fingerprint_names_the_x264_core_that_every_h264_stream_carries(tmp_path: Path) -> None:
    core = ffmpeg._x264_core(ffmpeg.ffmpeg_bin())
    assert re.fullmatch(r"core \d+.*", core), core
    clip = ffmpeg.color_clip(tmp_path / "a.mp4", 64, 64, 10, 0.5, "red")
    assert f"x264 - {core} - ".encode() in clip.read_bytes()  # the bytes really depend on it


@media
def test_non_utf8_bytes_in_tool_output_never_raise(tmp_path: Path, renders: dict[str, Path]) -> None:
    tagged = tmp_path / "tagged.mp4"
    cmd = [os.fsencode(ffmpeg.ffmpeg_bin()), b"-v", b"error", b"-y", b"-i", os.fsencode(renders["good"]), b"-c", b"copy"]
    subprocess.run([*cmd, b"-metadata", b"title=Caf\xe9 latin-1", os.fsencode(tagged)], check=True)
    assert b"Caf\xe9 latin-1" in tagged.read_bytes()  # a raw Latin-1 byte, printed by ffmpeg at loglevel info
    assert qa.check_render(tagged, 1080, 1920, 30, 2.0) == []
    integrated, _ = qa.loudness(tagged)
    assert abs(integrated + 14.0) <= 1.0
    assert ffmpeg.loudnorm_two_pass(tmp_path / "n.wav", tagged).is_file()
    assert ffmpeg.mux(tmp_path / "m.mp4", tagged, tmp_path / "n.wav").is_file()
    missing = tmp_path / os.fsdecode(b"caf\xe9-missing.mp4")  # a non-UTF-8 file name in the error message
    with pytest.raises(FFmpegError, match="ffprobe failed"):
        qa.probe(missing)
    assert codes(qa.check_render(missing, 1080, 1920, 30, 2.0)) == {"unreadable"}


@media
def test_variable_frame_rate_behind_matching_rate_fields_is_detected(tmp_path: Path) -> None:
    vfr = make_hidden_vfr(tmp_path)
    stream = ffmpeg.ffprobe_json(vfr)["streams"][0]
    assert stream["r_frame_rate"] == stream["avg_frame_rate"]  # the rate fields are fooled
    p = qa.probe(vfr)
    assert p.constant_frame_rate is False
    assert "variable_frame_rate" in codes(qa.check_render(vfr, p.width, p.height, p.fps, p.duration_s))
    # concat_videos must not stream-copy it: the result is re-encoded at a constant rate
    joined = ffmpeg.concat_videos(tmp_path / "joined.mp4", [vfr, vfr])
    assert packet_hashes(joined) != packet_hashes(vfr) * 2
    j = qa.probe(joined)
    assert j.constant_frame_rate is True
    assert qa.check_render(joined, j.width, j.height, j.fps, j.duration_s) == ["no_audio: the file has no audio track"]


@media
def test_loudnorm_retries_with_more_headroom_then_gives_up_leaving_out_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = ffmpeg.tone(tmp_path / "src.wav", 3.0, 440.0, amplitude=0.1)
    out = tmp_path / "out.wav"
    out.write_bytes(b"previous render")
    ceilings: list[float] = []
    real_measure = ffmpeg._loudnorm_measure

    def spy_loudnorm_measure(*args: Any) -> dict[str, float]:
        ceilings.append(args[2])
        return real_measure(*args)

    def mock_measure_loudness(path: Path, *, timeout_s: float | None = None) -> tuple[float, float]:
        assert ".partial-" in path.name  # the attempt is judged before it replaces `out`
        return -14.0, -0.5  # always above the -1 dBTP ceiling

    monkeypatch.setattr(ffmpeg, "_loudnorm_measure", spy_loudnorm_measure)
    monkeypatch.setattr(ffmpeg, "measure_loudness", mock_measure_loudness)
    with pytest.raises(MediaError, match=r"true peak -0\.5 dBTP still above -1\.0"):
        ffmpeg.loudnorm_two_pass(out, src)
    assert ceilings == pytest.approx([-1.3, -2.0, -3.0])
    assert out.read_bytes() == b"previous render"
    assert partial_files(tmp_path) == []


@media
def test_loudnorm_keeps_the_attempt_that_honours_the_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = ffmpeg.tone(tmp_path / "src.wav", 3.0, 440.0, amplitude=0.1)
    real_loudness = ffmpeg.measure_loudness
    verdicts: list[float] = []

    def mock_measure_loudness_hot_twice(path: Path, *, timeout_s: float | None = None) -> tuple[float, float]:
        integrated, peak = real_loudness(path, timeout_s=timeout_s)
        verdicts.append(peak)
        return (integrated, 0.5) if len(verdicts) <= 2 else (integrated, peak)

    monkeypatch.setattr(ffmpeg, "measure_loudness", mock_measure_loudness_hot_twice)
    out = ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", src)
    monkeypatch.undo()
    assert len(verdicts) == 3
    integrated, peak = qa.loudness(out)
    assert abs(integrated + 14.0) <= 1.0 and peak <= -1.0
    assert partial_files(tmp_path) == []


@media
def test_loudnorm_attenuates_sources_louder_than_0_lufs(tmp_path: Path) -> None:
    hot = ffmpeg.tone(tmp_path / "hot.wav", 5.0, 12_000.0, amplitude=0.99)
    before, _ = qa.loudness(hot)
    assert before > 0.0  # loudnorm rejects measured_I above 0 LUFS
    integrated, peak = qa.loudness(ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", hot))
    assert abs(integrated + 14.0) <= 1.0
    assert peak <= -1.0


@media
def test_loudnorm_tells_a_too_short_source_from_a_silent_one(tmp_path: Path) -> None:
    word = ffmpeg.tone(tmp_path / "word.wav", 0.375, 220.0)  # one word of the mock voice
    with pytest.raises(MediaError, match="shorter than one EBU R128 gating block") as err:
        ffmpeg.loudnorm_two_pass(tmp_path / "out.wav", word)
    assert "silent" not in str(err.value)
    assert not (tmp_path / "out.wav").exists()
    block = ffmpeg.loudnorm_two_pass(tmp_path / "block.wav", ffmpeg.tone(tmp_path / "b.wav", 0.5, 220.0))
    assert abs(qa.loudness(block)[0] + 14.0) <= 1.0  # one gating block is enough


@media
def test_paths_with_percent_signs_are_literal(tmp_path: Path) -> None:
    image = ffmpeg.still_image(tmp_path / "shot_%03d.png", 64, 36, "red")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["shot_%03d.png"]
    p = qa.probe(image)
    assert (p.width, p.height) == (64, 36)
    clip = ffmpeg.image_clip(tmp_path / "clip_%d.mp4", image, 0.5, 10)
    assert qa.probe(clip).duration_s == pytest.approx(0.5, abs=1e-6)
    wide = ffmpeg.concat_videos(tmp_path / "all_%02d.mp4", [clip, image], width=128, height=72, fps=10)
    assert (qa.probe(wide).width, qa.probe(wide).height) == (128, 72)
    assert partial_files(tmp_path) == []


def mock_slow_tool(folder: Path, name: str) -> Path:
    """A tool that hangs, as ffmpeg does on a stuck input."""
    script = folder / f"mock_slow_{name}"
    script.write_text("#!/bin/sh\nexec sleep 30\n")
    script.chmod(0o755)
    return script


def mock_slow_packets_ffprobe(folder: Path) -> Path:
    """An ffprobe that lists the streams normally but hangs on the packet listing (the second call of `probe`)."""
    script = folder / "mock_slow_packets_ffprobe"
    script.write_text(
        f'#!/bin/sh\ncase "$*" in *packet=pts*) exec sleep 30;; esac\nexec {shlex.quote(ffmpeg.ffprobe_bin())} "$@"\n'
    )
    script.chmod(0o755)
    return script


@media
def test_the_probe_timeout_also_bounds_the_frame_spacing_check(
    tmp_path: Path, renders: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ffmpeg.FFPROBE_ENV, str(mock_slow_packets_ffprobe(tmp_path)))
    started = time.monotonic()
    with pytest.raises(FFmpegError, match="timed out") as err:
        qa.probe(renders["good"], timeout_s=5.0)
    assert err.value.returncode is None and "packet=pts" in " ".join(err.value.cmd)  # the second call, not the first
    assert time.monotonic() - started < 25  # the 5 s budget, not the 30 s the tool would take


@media
def test_check_render_raises_on_a_broken_environment_instead_of_blaming_the_file(
    tmp_path: Path, renders: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    good = renders["good"]
    monkeypatch.setenv(ffmpeg.FFPROBE_ENV, str(tmp_path / "nonexistent-ffprobe"))
    with pytest.raises(MediaToolMissing):
        qa.check_render(good, 1080, 1920, 30, 2.0)
    slow_probe = mock_slow_tool(tmp_path, "ffprobe")
    monkeypatch.setenv(ffmpeg.FFPROBE_ENV, str(slow_probe))
    with pytest.raises(FFmpegError, match="timed out") as err:
        qa.check_render(good, 1080, 1920, 30, 2.0, timeout_s=2.0)
    assert (err.value.returncode, err.value.cmd[0]) == (None, str(slow_probe))
    monkeypatch.delenv(ffmpeg.FFPROBE_ENV)
    monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(tmp_path / "nonexistent-ffmpeg"))
    with pytest.raises(MediaToolMissing):
        qa.check_render(good, 1080, 1920, 30, 2.0)
    slow_ffmpeg = mock_slow_tool(tmp_path, "ffmpeg")
    monkeypatch.setenv(ffmpeg.FFMPEG_ENV, str(slow_ffmpeg))
    with pytest.raises(FFmpegError, match="timed out") as err:  # the probe passed; the loudness measure hung
        qa.check_render(good, 1080, 1920, 30, 2.0, timeout_s=2.0)
    assert (err.value.returncode, err.value.cmd[0]) == (None, str(slow_ffmpeg))
    monkeypatch.delenv(ffmpeg.FFMPEG_ENV)
    assert qa.check_render(good, 1080, 1920, 30, 2.0) == []  # the file was compliant all along
