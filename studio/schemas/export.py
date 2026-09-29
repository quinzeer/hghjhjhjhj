"""JSON Schema export of every domain contract (`studio.domain.CONTRACTS`) to `schemas/<Name>.schema.json`.

The versioned files are the published form of the contracts: `--check` fails when they drift from the models,
so a contract change cannot land without its regenerated schema.

    python -m studio.schemas.export            # regenerate schemas/ of the source checkout
    python -m studio.schemas.export --check    # exit 1 if a file differs, is missing or is unexpected

Without --dir, the target is `schemas/` next to the pyproject.toml of the `studio` project, looked up from this
module's location, then from the working directory; outside a source checkout, --dir is required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import tomllib
from collections.abc import Iterable, Sequence
from pathlib import Path

from studio.core.interfaces import StudioError
from studio.domain import CONTRACTS

PROJECT_NAME = "studio"
SUFFIX = ".schema.json"
FILE_MODE = 0o644


class SchemaDirNotFound(StudioError):
    """No source checkout of the studio project to hold the versioned schemas."""


def is_checkout(directory: Path) -> bool:
    """True when `directory` holds the pyproject.toml of the studio project."""
    pyproject = directory / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    project = data.get("project")
    return isinstance(project, dict) and project.get("name") == PROJECT_NAME


def find_checkout(start: Path) -> Path | None:
    """The closest directory at or above `start` that is a source checkout of the studio project."""
    start = start.resolve()
    return next((d for d in (start, *start.parents) if is_checkout(d)), None)


def default_dir(starts: Iterable[Path] | None = None) -> Path:
    """`schemas/` of the source checkout found from `starts` (default: this module's folder, then the cwd).

    From an editable install, or a virtualenv inside the checkout, the module's folder leads to the checkout; an
    installed copy elsewhere never yields a path inside site-packages.
    """
    for start in (Path(__file__).parent, Path.cwd()) if starts is None else starts:
        checkout = find_checkout(start)
        if checkout is not None:
            return checkout / "schemas"
    raise SchemaDirNotFound(
        f"no source checkout of the {PROJECT_NAME!r} project (pyproject.toml) above this module or the working "
        "directory; pass --dir"
    )


def render() -> dict[str, str]:
    """File name -> exact file text (sorted keys, 2-space indent, trailing newline)."""
    return {
        f"{model.__name__}{SUFFIX}": json.dumps(model.model_json_schema(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        for model in CONTRACTS
    }


def _write_atomic(path: Path, text: str) -> None:
    """Readers see the old file or the new one, never a partial write; a failure leaves the old file in place."""
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.chmod(FILE_MODE)  # mkstemp creates 0600
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def export(dir: Path) -> list[Path]:
    """Write one schema per contract into `dir`, then remove schema files of contracts that no longer exist."""
    dir.mkdir(parents=True, exist_ok=True)
    expected = render()
    written = []
    for name, text in expected.items():
        path = dir / name
        _write_atomic(path, text)
        written.append(path)
    for stale in sorted(dir.glob(f"*{SUFFIX}")):
        if stale.name not in expected:
            stale.unlink()
    return written


def check(dir: Path) -> list[str]:
    """Differences between `dir` and a fresh export, one line per file; empty when they are identical."""
    expected = render()
    problems = []
    for name, text in expected.items():
        path = dir / name
        if not path.is_file():
            problems.append(f"missing: {path}")
        elif path.read_bytes() != text.encode("utf-8"):
            problems.append(f"differs: {path}")
    if dir.is_dir():
        problems += [f"unexpected: {p}" for p in sorted(dir.glob(f"*{SUFFIX}")) if p.name not in expected]
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m studio.schemas.export", description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare instead of writing; exit 1 on any drift")
    parser.add_argument("--dir", type=Path, help="schema directory (default: schemas/ of the source checkout)")
    args = parser.parse_args(argv)
    if args.dir is None:
        try:
            args.dir = default_dir()
        except SchemaDirNotFound as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.check:
        problems = check(args.dir)
        for line in problems:
            print(line, file=sys.stderr)
        if problems:
            print("schemas are stale: run `python -m studio.schemas.export`", file=sys.stderr)
            return 1
        print(f"{len(CONTRACTS)} schemas up to date in {args.dir}")
        return 0
    paths = export(args.dir)
    print(f"wrote {len(paths)} schemas to {args.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
