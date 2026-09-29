#!/usr/bin/env python3
"""Phase 1 gate (MISSION §9, docs/design/phase1.md): exit 0 only if every criterion holds.

1. lint: ruff + mypy strict;
2. tests green with none skipped (Postgres and ffmpeg required), coverage >= 80 % on the core (studio/domain, core,
   scenario, pipeline);
3. e2e dry run: a Short 1080x1920 and a long 1920x1080 through mocks, judged by what this gate measures itself, not by
   what the run reports about itself: ffprobe (resolution, constant frame rate, tracks), the length of the render
   against the sum of the script's scenes, the loudness and true peak (ffmpeg, EBU R128), the sha256 of the delivered
   render against its key, the lengths of the audio and video tracks;
4. a second run executes nothing: the state folder is unchanged, whatever the report says: every row of every table
   (but the date of the last put of an artifact) and the name, size, inode and modification time of every stored file;
5. every JSON the run writes (report, manifest, costs, scenes) and every cost entry says "mock".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ("studio/domain", "studio/core", "studio/scenario", "studio/pipeline")
MIN_COVERAGE = 80.0
TARGETS = {"short": (1080, 1920), "long": (1920, 1080)}
DURATION_TOLERANCE_S = 0.15
AV_TOLERANCE_S = 0.25  # audio and video tracks of a render end within this of each other
LUFS_TARGET, LUFS_TOLERANCE = -14.0, 1.0
TRUE_PEAK_CEILING = -1.0
JSON_OUTPUTS = ("report.json", "manifest.json", "costs.json", "script.scenes.json")


@dataclass
class Check:
    label: str
    ok: bool = True
    details: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.details.append(msg)


def run(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


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


def junit_totals(junit_xml: Path) -> dict[str, int]:
    """Tests, skipped, failures and errors summed over every suite of a pytest JUnit report."""
    root = ET.parse(junit_xml).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {key: sum(int(suite.get(key, 0)) for suite in suites) for key in ("tests", "skipped", "failures", "errors")}


def check_tests(cov_json: Path) -> Check:
    chk = Check(f"Tests verts, aucun ignoré, couverture ≥ {MIN_COVERAGE:g} % sur le cœur")
    if not os.environ.get("STUDIO_TEST_PG_URL"):
        chk.fail(
            "STUDIO_TEST_PG_URL absent : les preuves Postgres (SKIP LOCKED, verrous, essai DBOS) ne tourneraient pas. "
            "Exemple : STUDIO_TEST_PG_URL=postgresql+psycopg://postgres@localhost:5432/studio_it"
        )
        return chk
    # STUDIO_REQUIRE_MEDIA turns a missing ffmpeg into a failure instead of a skip: a green run carries the media proofs.
    env = {**os.environ, "STUDIO_REQUIRE_MEDIA": "1"}
    junit = cov_json.with_name("junit.xml")
    cmd = ["uv", "run", "--group", "dev", "pytest", "-q", "--cov=studio", f"--cov-report=json:{cov_json}", f"--junitxml={junit}"]
    r = run(cmd, env=env)
    if not junit.is_file():
        chk.fail("pytest n'a produit aucun rapport JUnit")
        return chk
    totals = junit_totals(junit)
    chk.details.append(
        f"pytest : {totals['tests']} tests, {totals['skipped']} ignoré(s), "
        f"{totals['failures']} échec(s), {totals['errors']} erreur(s)"
    )
    if totals["skipped"]:
        chk.fail(f"{totals['skipped']} test(s) ignoré(s) : une preuve ignorée ne prouve rien")
    if r.returncode != 0:
        chk.fail("pytest en échec")
        return chk
    if not cov_json.is_file():
        chk.fail("pytest n'a produit aucun rapport de couverture")
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


def measure_loudness(path: Path) -> tuple[float, float]:
    """Integrated loudness (LUFS) and true peak (dBTP) of a file, measured here with ffmpeg (EBU R128), so that the gate
    does not take the studio's own QA at its word."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    if r.returncode != 0 or "Summary:" not in r.stderr:
        raise RuntimeError(r.stderr.strip()[-300:])
    summary = r.stderr[r.stderr.rindex("Summary:") :]
    integrated = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary)
    if not integrated or not peak:
        raise RuntimeError("ffmpeg gave no loudness summary")
    return float(integrated.group(1)), float(peak.group(1))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Columns a replay legitimately rewrites: `artifacts.created_at` moves at every put, and a replay puts the token of each
# gate again. Every other column of every table, and every stored file, stays byte for byte and date for date.
VOLATILE_COLUMNS = frozenset({("artifacts", "created_at")})


def state_snapshot(state: Path) -> dict[str, str]:
    """One digest per table of the index (every row, every column but the volatile ones) and one for the stored files
    (name, size, inode, modification time). A run that wipes the state and recomputes it to the same rows still leaves
    other timestamps and other inodes, so counting rows or hashing names would not see it."""
    snapshot: dict[str, str] = {}
    db = state / "studio.db"
    if db.is_file():
        with sqlite3.connect(db, timeout=10) as conn:
            tables = [
                r[0] for r in conn.execute("select name from sqlite_master where type = 'table' and name not like 'sqlite_%'")
            ]
            for table in sorted(tables):
                columns = [r[1] for r in conn.execute(f'pragma table_info("{table}")') if (table, r[1]) not in VOLATILE_COLUMNS]
                selected = ", ".join(f'"{c}"' for c in columns) or "1"
                rows = conn.execute(f'select {selected} from "{table}" order by {selected}').fetchall()  # noqa: S608 (names from the schema)
                snapshot[f"table {table}"] = hashlib.sha256(repr(rows).encode()).hexdigest()
    cas = state / "cas"
    stored = sorted((f.name, s.st_size, s.st_ino, s.st_mtime_ns) for f in cas.rglob("*") if f.is_file() for s in [f.stat()])
    snapshot["fichiers du magasin"] = hashlib.sha256(repr(stored if cas.is_dir() else []).encode()).hexdigest()
    return snapshot


def changed_parts(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Which parts of the state differ between two snapshots (a part that appeared or vanished counts)."""
    return sorted(part for part in before.keys() | after.keys() if before.get(part) != after.get(part))


def scenes_total(doc: dict) -> tuple[float, int]:
    """Total length and scene count from the scene document: the sum of each scene's own duration."""
    scenes = doc.get("scenes", [])
    return round(sum(float(scene["duree_s"]) for scene in scenes), 1), len(scenes)


def check_render(chk: Check, folder: Path, report: dict, width: int, height: int) -> Path | None:
    """Independent checks of one render: the file must satisfy the criteria whatever the report claims."""
    render = Path(report.get("render_path", ""))
    if not render.is_absolute():
        render = folder / render
    try:
        info = probe(render)
    except (RuntimeError, OSError) as exc:
        chk.fail(f"ffprobe : {exc}")
        return None
    video = [s for s in info["streams"] if s.get("codec_type") == "video"]
    audio = [s for s in info["streams"] if s.get("codec_type") == "audio"]
    if not video or not audio:
        chk.fail(f"pistes : vidéo={len(video)} audio={len(audio)}")
        return render
    v, a = video[0], audio[0]
    if (v.get("width"), v.get("height")) != (width, height):
        chk.fail(f"résolution {v.get('width')}×{v.get('height')} ≠ {width}×{height}")
    if v.get("r_frame_rate") != v.get("avg_frame_rate"):
        chk.fail(f"cadence variable : r={v.get('r_frame_rate')} avg={v.get('avg_frame_rate')}")
    duration = float(info["format"].get("duration", 0))
    try:
        doc = json.loads((folder / "script.scenes.json").read_text())
        expected, scene_count = scenes_total(doc)
    except (OSError, ValueError, KeyError) as exc:
        chk.fail(f"script.scenes.json illisible : {exc}")
        expected, scene_count = -1.0, -1
    if abs(duration - expected) > DURATION_TOLERANCE_S:
        chk.fail(f"durée {duration:.2f} s ≠ somme des scènes du script {expected:.2f} s")
    if report.get("scene_count") != scene_count:
        chk.fail(f"le rapport annonce {report.get('scene_count')} scènes, le script en a {scene_count}")
    if abs(float(report.get("duration_expected_s", -1)) - expected) > 0.05:
        chk.fail(f"duration_expected_s du rapport ({report.get('duration_expected_s')}) ≠ script ({expected})")
    if abs(float(v.get("duration", duration)) - float(a.get("duration", duration))) > AV_TOLERANCE_S:
        chk.fail(f"pistes de longueurs différentes : vidéo {v.get('duration')} s, audio {a.get('duration')} s")
    if file_sha256(render) != report.get("render_key"):
        chk.fail("le sha256 du rendu livré n'est pas la render_key du rapport")
    try:
        lufs, peak = measure_loudness(render)
    except RuntimeError as exc:
        chk.fail(f"mesure de loudness impossible : {exc}")
    else:
        if abs(lufs - LUFS_TARGET) > LUFS_TOLERANCE:
            chk.fail(f"loudness {lufs:.1f} LUFS hors de {LUFS_TARGET:g} ± {LUFS_TOLERANCE:g}")
        if peak > TRUE_PEAK_CEILING:
            chk.fail(f"crête vraie {peak:.1f} dBTP au-dessus de {TRUE_PEAK_CEILING:g}")
        chk.details.append(
            f"{render.name} : {width}×{height} @ {v.get('r_frame_rate')}, {duration:.2f} s, {lufs:.1f} LUFS, {peak:.1f} dBTP"
        )
    return render


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
            docs = {name: json.loads((folder / name).read_text()) for name in JSON_OUTPUTS}
        except (OSError, json.JSONDecodeError) as exc:
            chk.fail(f"sorties manquantes ou illisibles : {exc}")
            checks.append(chk)
            continue
        report, manifest, costs = docs["report.json"], docs["manifest.json"], docs["costs.json"]
        if not report.get("executed"):
            chk.fail("1re exécution : aucune étape exécutée")
        if report.get("qa_defects"):
            chk.fail(f"défauts QA : {report['qa_defects']}")
        if report.get("waiting"):
            chk.fail(f"étapes en attente : {report['waiting']}")
        for name, doc in docs.items():  # criterion 5: every JSON the run writes says mock, not only two of them
            if doc.get("mock") is not True:
                chk.fail(f"{name} doit porter mock=true")
        if not all("mock" in a for a in report.get("adapters", [])) or not report.get("adapters"):
            chk.fail(f"adaptateurs non mock ou absents : {report.get('adapters')}")
        entries = costs.get("entries", [])
        if not entries or not all(e.get("mock") is True for e in entries):
            chk.fail("registre de coûts vide ou dont une entrée ne porte pas mock=true")
        if len(manifest.get("step_keys", {})) != report.get("step_count"):
            chk.fail("le manifeste ne compte pas autant d'étapes que le rapport")
        render = check_render(chk, folder, report, width, height)
        if render is None:
            checks.append(chk)
            continue
        before, stamp = state_snapshot(out / "state"), (render.stat().st_ino, render.stat().st_mtime_ns)
        second = run(cmd)
        if second.returncode != 0:
            chk.fail("2e exécution en échec")
        else:
            report2 = json.loads((folder / "report.json").read_text())
            if report2.get("executed"):
                chk.fail(f"2e exécution : étapes réexécutées {report2['executed']}")
            if report2.get("render_key") != report.get("render_key"):
                chk.fail("2e exécution : rendu différent")
            changed = changed_parts(before, state_snapshot(out / "state"))  # independent of what the report says it did
            if changed:
                chk.fail(f"2e exécution : l'état a changé ({', '.join(changed)}) : ce n'est pas un simple rejeu")
            if (render.stat().st_ino, render.stat().st_mtime_ns) != stamp:
                chk.details.append("le rendu livré a été réécrit à l'identique")
            verdict = "" if changed else ", état inchangé (lignes, dates et fichiers du magasin)"
            chk.details.append(f"replay : {len(report2.get('skipped', []))} étapes réutilisées, 0 exécutée{verdict}")
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
