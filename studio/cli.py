"""`studio` command line (docs/design/phase1.md, contract of `make e2e-dry`).

    studio run --channel channel-a --format short --dry-run --out var/e2e

Phase 1 offers the dry run only: every adapter is a mock, nothing leaves the machine, and the report says `mock`.
Exit codes: 0 done, 1 failure, 2 usage error, 3 a gate holds a rejection, 75 paused until the Claude usage limit
resets (EX_TEMPFAIL: run the same command again after the printed time).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

from studio.core.interfaces import StudioError
from studio.domain import Channel, VideoFormat
from studio.pipeline.driver import DryRunConfig, GateRejected, RunPaused, run_dry

CHANNELS_DIR = Path(__file__).resolve().parent / "config" / "channels"
EXIT_FAILURE = 1
EXIT_GATE_REJECTED = 3
EXIT_PAUSED = 75


class UsageError(StudioError):
    """The command line names something that does not exist or asks for something Phase 1 does not do."""


def load_channels(directory: Path = CHANNELS_DIR) -> dict[str, Channel]:
    """Every channel of `directory` (one YAML file each), by id."""
    channels: dict[str, Channel] = {}
    for path in sorted(directory.glob("*.yaml")):
        channel = Channel.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if channel.id in channels:
            raise UsageError(f"channel id {channel.id!r} is defined twice (last in {path.name})")
        channels[channel.id] = channel
    return channels


def resolve_channel(name: str, channels: dict[str, Channel]) -> Channel:
    """Find a channel by id (`channel-a`) or by its short letter (`a`, `A`), case-insensitively."""
    wanted = name.strip().lower()
    for candidate in (wanted, f"channel-{wanted}"):
        for channel_id, channel in channels.items():
            if channel_id.lower() == candidate:
                return channel
    raise UsageError(f"unknown channel {name!r}; known channels: {', '.join(sorted(channels)) or 'none'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run one video through the step graph")
    run.add_argument("--channel", required=True, help="channel id (channel-a) or short letter (a)")
    run.add_argument("--format", required=True, choices=[f.value for f in VideoFormat], help="short (9:16) or long (16:9)")
    run.add_argument("--dry-run", action="store_true", help="mock adapters only, no network (the only mode of phase 1)")
    run.add_argument("--out", required=True, type=Path, help="output folder (state and reports live under it)")
    run.add_argument("--seed", type=int, default=0, help="seed of the run (same seed, same bytes)")
    run.add_argument("--run-id", default=None, help="run identifier (default: derived from channel, format and seed)")
    run.add_argument("--channels-dir", type=Path, default=CHANNELS_DIR, help="folder of channel YAML files")
    return parser


def _run(args: argparse.Namespace) -> int:
    if not args.dry_run:
        raise UsageError("phase 1 runs mock adapters only: add --dry-run (real adapters arrive in phase 2 and later)")
    channel = resolve_channel(args.channel, load_channels(args.channels_dir))
    fmt = VideoFormat(args.format)
    if fmt not in channel.formats:
        raise UsageError(f"channel {channel.id!r} does not publish the {fmt.value!r} format")
    config = DryRunConfig(channel=channel, format=fmt, out_dir=args.out, seed=args.seed, run_id=args.run_id)
    report = run_dry(config)
    print(f"channel   {report['channel_id']}  format {report['format']}  run {report['run_id']}  [mock, dry-run]")
    print(f"steps     {len(report['executed'])} executed, {len(report['skipped'])} reused, {len(report['waiting'])} waiting")
    print(f"render    {report['render_path']}  ({report['duration_expected_s']:.1f} s expected, {report['scene_count']} scenes)")
    print(f"report    {Path(report['render_path']).with_name('report.json')}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _run(args)
    except UsageError as exc:
        parser.error(str(exc))  # exits with status 2
    except GateRejected as exc:
        print(f"studio: {exc}", file=sys.stderr)
        return EXIT_GATE_REJECTED
    except RunPaused as exc:
        print(f"studio: {exc}", file=sys.stderr)
        return EXIT_PAUSED
    except StudioError as exc:
        print(f"studio: {exc}", file=sys.stderr)
        return EXIT_FAILURE
    parser.error(f"unknown command {args.command!r}")
    return 2  # pragma: no cover  (parser.error exits)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
