"""`studio run`: channel lookup, usage errors, exit codes."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest

from studio import cli
from studio.cli import CHANNELS_DIR, UsageError, load_channels, main, resolve_channel
from studio.core.interfaces import StudioError
from studio.pipeline.driver import DryRunConfig, GateRejected, RunPaused

NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)

CHANNEL_YAML = """\
id: {id}
name: Test channel
language: en
concept: a concept
formats: {formats}
voice_id: narrator-main
visual_bible: knowledge/bibles/x.md
"""


def write_channel(directory: Path, name: str, channel_id: str, formats: str = "[long, short]") -> None:
    (directory / f"{name}.yaml").write_text(CHANNEL_YAML.format(id=channel_id, formats=formats), encoding="utf-8")


def fake_report(out: Path) -> dict[str, Any]:
    return {
        "channel_id": "channel-a",
        "format": "short",
        "run_id": "dry-channel-a-short-0",
        "executed": ["idea", "package"],
        "skipped": ["g1"],
        "waiting": [],
        "render_path": str(out / "channel-a" / "short" / "render.mp4"),
        "duration_expected_s": 23.2,
        "scene_count": 6,
    }


# ------------------------------------------------------------------ channels


def test_the_shipped_channels_load_and_carry_their_adr005_identity() -> None:
    channels = load_channels(CHANNELS_DIR)
    assert set(channels) == {"channel-a", "channel-b"}
    assert channels["channel-a"].voice_id == "narrator-main" and channels["channel-b"].language == "en"


@pytest.mark.parametrize("name", ["channel-a", "a", "A", " Channel-A "])
def test_a_channel_is_found_by_id_or_by_its_letter(name: str) -> None:
    assert resolve_channel(name, load_channels()).id == "channel-a"


def test_an_unknown_channel_lists_the_known_ones() -> None:
    with pytest.raises(UsageError, match="known channels: channel-a, channel-b"):
        resolve_channel("zzz", load_channels())
    with pytest.raises(UsageError, match="known channels: none"):
        resolve_channel("a", {})


def test_a_channel_id_defined_twice_is_refused(tmp_path: Path) -> None:
    write_channel(tmp_path, "one", "channel-x")
    write_channel(tmp_path, "two", "channel-x")
    with pytest.raises(UsageError, match="defined twice"):
        load_channels(tmp_path)


# ------------------------------------------------------------------ command line


def test_run_needs_dry_run_in_phase_1(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["run", "--channel", "a", "--format", "short", "--out", str(tmp_path)])
    assert exit_.value.code == 2
    assert "add --dry-run" in capsys.readouterr().err


def test_an_unknown_channel_is_a_usage_error(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["run", "--channel", "nope", "--format", "short", "--dry-run", "--out", str(tmp_path)])
    assert exit_.value.code == 2 and "unknown channel 'nope'" in capsys.readouterr().err


def test_a_format_the_channel_does_not_publish_is_a_usage_error(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    write_channel(tmp_path, "solo", "channel-long-only", "[long]")
    with pytest.raises(SystemExit) as exit_:
        main(
            [
                "run",
                "--channel",
                "long-only",
                "--format",
                "short",
                "--dry-run",
                "--out",
                str(tmp_path / "o"),
                "--channels-dir",
                str(tmp_path),
            ]
        )
    assert exit_.value.code == 2 and "does not publish the 'short' format" in capsys.readouterr().err


def test_a_missing_format_or_channel_is_refused_by_the_parser(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["run", "--channel", "a", "--dry-run", "--out", str(tmp_path)])
    assert exit_.value.code == 2
    with pytest.raises(SystemExit) as exit_:
        main(["run", "--channel", "a", "--format", "medium", "--dry-run", "--out", str(tmp_path)])
    assert exit_.value.code == 2


def test_a_command_is_required() -> None:
    with pytest.raises(SystemExit) as exit_:
        main([])
    assert exit_.value.code == 2


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["--help"])
    assert exit_.value.code == 0 and "dry run only" in capsys.readouterr().out


def test_a_successful_run_prints_where_the_render_and_the_report_are(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    seen: list[DryRunConfig] = []

    def fake_run(config: DryRunConfig) -> dict[str, Any]:
        seen.append(config)
        return fake_report(config.out_dir)

    monkeypatch.setattr(cli, "run_dry", fake_run)
    assert main(["run", "--channel", "A", "--format", "short", "--dry-run", "--out", str(tmp_path), "--seed", "3"]) == 0
    out = capsys.readouterr().out
    assert "[mock, dry-run]" in out and "2 executed, 1 reused, 0 waiting" in out
    assert str(tmp_path / "channel-a" / "short" / "render.mp4") in out and "report.json" in out
    assert seen[0].channel.id == "channel-a" and seen[0].seed == 3 and seen[0].out_dir == tmp_path


@pytest.mark.parametrize(
    ("error", "code", "text"),
    [
        (GateRejected("compliance", "compliance", "loops left open"), 3, "compliance rejected at step 'compliance'"),
        (RunPaused(NOON, "usage limit"), 75, "paused until 2026-09-29T12:00:00+00:00"),
        (StudioError("disk full"), 1, "disk full"),
    ],
)
def test_failures_have_their_own_exit_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path, error: StudioError, code: int, text: str
) -> None:
    def fail(config: DryRunConfig) -> dict[str, Any]:
        raise error

    monkeypatch.setattr(cli, "run_dry", fail)
    assert main(["run", "--channel", "a", "--format", "long", "--dry-run", "--out", str(tmp_path)]) == code
    assert text in capsys.readouterr().err
