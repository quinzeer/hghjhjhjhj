#!/usr/bin/env python3
"""Phase 1 gate (MISSION §9, docs/design/phase1.md): exit 0 only if every criterion holds.

1. lint: ruff + mypy strict;
2. tests green, coverage >= 80 % on the core (studio/domain, core, scenario, pipeline);
3. e2e dry run: a Short 1080x1920 and a long 1920x1080 through mocks, with manifest and cost ledger,
   validated by ffprobe (resolution, constant frame rate, duration, video + audio streams);
4. a second run executes nothing and yields the same render;
5. every report and manifest produced with mocks says "mock".
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ("studio/domain", "studio/core", "studio/scenario", "studio/pipeline")
MIN_COVERAGE = 80.0
TARGETS = {"short": (1080, 1920), "long": (1920, 1080)}
DURATION_TOLERANCE_S = 0.15


@dataclass
class Check:
    label: str
    ok: bool = True
    details: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.details.append(msg)


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def check_lint() -> Check:
    chk = Check("Lint : ruff + mypy strict")
    for cmd in (
        ["uv", "run", "--group", "dev", "ruff", "check", "studio", "tests", "tools"],
        ["uv", "run", "--group", "dev", "ruff", "format", "--check", "studio", "tests", "tools"],
        ["uv", "run", "--group", "dev", "mypy"],
    ):
        r = run(cmd)
        if r.returncode != 0:
            chk.fail(f"{' '.join(cmd[4:])} : {(r.stdout + r.stderr).strip().splitlines()[-1:]}")
    return chk


def check_tests(cov_json: Path) -> Check:
    chk = Check(f"Tests verts et couverture ≥ {MIN_COVERAGE:g} % sur le cœur")
    r = run(["uv", "run", "--group", "dev", "pytest", "-q", "--cov=studio", f"--cov-report=json:{cov_json}"])
    tail = (r.stdout.strip().splitlines() or ["?"])[-1]
    chk.details.append(f"pytest : {tail}")
    if r.returncode != 0:
        chk.fail("pytest en échec")
        return chk
    data = json.loads(cov_json.read_text())
    covered = total = 0
    for path, info in data.get("files", {}).items():
        rel = Path(path).resolve().relative_to(ROOT).as_posix() if Path(path).is_absolute() else path
        if rel.startswith(CORE):
            covered += info["summary"]["covered_lines"]
            total += info["summary"]["num_statements"]
    pct = 100.0 * covered / total if total else 0.0
    chk.details.append(f"couverture du cœur : {pct:.1f} % ({covered}/{total} lignes)")
    if pct < MIN_COVERAGE:
        chk.fail(f"couverture du cœur {pct:.1f} % < {MIN_COVERAGE:g} %")
    return chk


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return json.loads(r.stdout)


def check_e2e(out: Path, channel: str) -> list[Check]:
    checks = []
    for fmt, (width, height) in TARGETS.items():
        chk = Check(f"e2e-dry {channel} {fmt} : rendu {width}×{height}, manifeste, coûts, mock, replay")
        cmd = ["uv", "run", "studio", "run", "--channel", channel, "--format", fmt, "--dry-run", "--out", str(out)]
        first = run(cmd)
        if first.returncode != 0:
            chk.fail(f"1re exécution en échec : {(first.stdout + first.stderr).strip()[-400:]}")
            checks.append(chk)
            continue
        folder = out / channel / fmt
        try:
            report = json.loads((folder / "report.json").read_text())
            manifest = json.loads((folder / "manifest.json").read_text())
            costs = json.loads((folder / "costs.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            chk.fail(f"sorties manquantes ou illisibles : {exc}")
            checks.append(chk)
            continue
        if not report.get("executed"):
            chk.fail("1re exécution : aucune étape exécutée")
        if report.get("qa_defects"):
            chk.fail(f"défauts QA : {report['qa_defects']}")
        if report.get("waiting"):
            chk.fail(f"étapes en attente : {report['waiting']}")
        if report.get("mock") is not True or manifest.get("mock") is not True:
            chk.fail("report.json et manifest.json doivent porter mock=true")
        if not all("mock" in a for a in report.get("adapters", [])) or not report.get("adapters"):
            chk.fail(f"adaptateurs non mock ou absents : {report.get('adapters')}")
        if not costs:
            chk.fail("registre de coûts vide")
        render = Path(report.get("render_path", ""))
        if not render.is_absolute():
            render = folder / render
        try:
            info = probe(render)
        except (RuntimeError, OSError) as exc:
            chk.fail(f"ffprobe : {exc}")
            checks.append(chk)
            continue
        video = [s for s in info["streams"] if s.get("codec_type") == "video"]
        audio = [s for s in info["streams"] if s.get("codec_type") == "audio"]
        if not video or not audio:
            chk.fail(f"pistes : vidéo={len(video)} audio={len(audio)}")
        else:
            v = video[0]
            if (v.get("width"), v.get("height")) != (width, height):
                chk.fail(f"résolution {v.get('width')}×{v.get('height')} ≠ {width}×{height}")
            if v.get("r_frame_rate") != v.get("avg_frame_rate"):
                chk.fail(f"cadence variable : r={v.get('r_frame_rate')} avg={v.get('avg_frame_rate')}")
            duration = float(info["format"].get("duration", 0))
            expected = float(report.get("duration_expected_s", -1))
            if abs(duration - expected) > DURATION_TOLERANCE_S:
                chk.fail(f"durée {duration:.2f} s ≠ attendue {expected:.2f} s")
            chk.details.append(f"{render.name} : {v.get('width')}×{v.get('height')} @ {v.get('r_frame_rate')}, {duration:.2f} s")
        second = run(cmd)
        if second.returncode != 0:
            chk.fail("2e exécution en échec")
        else:
            report2 = json.loads((folder / "report.json").read_text())
            if report2.get("executed"):
                chk.fail(f"2e exécution : étapes réexécutées {report2['executed']}")
            if report2.get("render_key") != report.get("render_key"):
                chk.fail("2e exécution : rendu différent")
            chk.details.append(f"replay : {len(report2.get('skipped', []))} étapes réutilisées, 0 exécutée")
        checks.append(chk)
    return checks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", default="channel-a")
    ap.add_argument("--skip-tests", action="store_true", help="e2e only (debug)")
    args = ap.parse_args(argv)
    checks: list[Check] = []
    with tempfile.TemporaryDirectory() as tmp:
        if not args.skip_tests:
            checks.append(check_lint())
            checks.append(check_tests(Path(tmp) / "coverage.json"))
        checks += check_e2e(Path(tmp) / "e2e", args.channel)
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    ci_chk = Check("CI GitHub Actions présente")
    if not ci.is_file():
        ci_chk.fail(".github/workflows/ci.yml absent")
    checks.append(ci_chk)
    for c in checks:
        print(f"{'✓' if c.ok else '✗'} {c.label}")
        for d in c.details:
            print(f"    {'·' if c.ok else '-'} {d}")
    failed = sum(not c.ok for c in checks)
    print(f"\nverify-phase-1 : {len(checks) - failed}/{len(checks)} contrôles OK" + (f", {failed} en échec" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
