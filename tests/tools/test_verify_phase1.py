"""The phase 1 gate must fail closed: no Postgres, a skipped test or thin core coverage each turn it red."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("studio_verify_phase1", ROOT / "tools" / "verify_phase1.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the gate declares dataclasses, which look their module up by name
    spec.loader.exec_module(module)
    return module


gate = load_gate()

PG_URL = "postgresql+psycopg://postgres@localhost:5432/studio_it"


def junit(tests: int = 10, skipped: int = 0, failures: int = 0, errors: int = 0) -> str:
    suite = f'name="pytest" tests="{tests}" skipped="{skipped}" failures="{failures}" errors="{errors}"'
    return f"<testsuites><testsuite {suite}/></testsuites>"


def coverage(core: tuple[int, int] = (99, 100)) -> str:
    covered, statements = core
    files = {
        "studio/core/graph.py": {"summary": {"covered_lines": covered, "num_statements": statements}},
        "studio/media/ffmpeg.py": {"summary": {"covered_lines": 0, "num_statements": 1000}},  # outside the core: not counted
    }
    return json.dumps({"files": files})


class FakePytest:
    """Stands in for `uv run pytest`: writes the reports a real run would leave, remembers its environment."""

    def __init__(self, xml: str, cov: str, returncode: int = 0) -> None:
        self.xml, self.cov, self.returncode = xml, cov, returncode
        self.env: dict[str, str] | None = None

    def __call__(self, cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        self.env = env
        for arg in cmd:
            if arg.startswith("--junitxml="):
                Path(arg.split("=", 1)[1]).write_text(self.xml, encoding="utf-8")
            if arg.startswith("--cov-report=json:"):
                Path(arg.split(":", 1)[1]).write_text(self.cov, encoding="utf-8")
        return subprocess.CompletedProcess(cmd, self.returncode, "", "")


@pytest.fixture
def with_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STUDIO_TEST_PG_URL", PG_URL)


def check(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake: FakePytest) -> Any:
    monkeypatch.setattr(gate, "run", fake)
    return gate.check_tests(tmp_path / "coverage.json")


def test_junit_totals_sum_every_suite(tmp_path: Path) -> None:
    report = tmp_path / "j.xml"
    report.write_text(
        '<testsuites><testsuite tests="3" skipped="1" failures="0" errors="0"/>'
        '<testsuite tests="2" skipped="0" failures="1" errors="1"/></testsuites>',
        encoding="utf-8",
    )
    assert gate.junit_totals(report) == {"tests": 5, "skipped": 1, "failures": 1, "errors": 1}
    report.write_text('<testsuite tests="4" skipped="0" failures="0" errors="0"/>', encoding="utf-8")
    assert gate.junit_totals(report)["tests"] == 4


def test_without_a_postgres_url_the_gate_fails_before_running_anything(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("STUDIO_TEST_PG_URL", raising=False)
    fake = FakePytest(junit(), coverage())
    result = check(monkeypatch, tmp_path, fake)
    assert not result.ok and "STUDIO_TEST_PG_URL absent" in result.details[0]
    assert fake.env is None  # pytest never started


def test_a_clean_run_passes_and_pytest_is_told_that_media_proofs_are_required(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_postgres: None
) -> None:
    fake = FakePytest(junit(tests=1250), coverage())
    result = check(monkeypatch, tmp_path, fake)
    assert result.ok, result.details
    assert "1250 tests, 0 ignoré(s)" in result.details[0] and "99.0 %" in result.details[1]
    assert fake.env is not None and fake.env["STUDIO_REQUIRE_MEDIA"] == "1"


def test_a_single_skipped_test_fails_the_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_postgres: None) -> None:
    result = check(monkeypatch, tmp_path, FakePytest(junit(skipped=1), coverage()))
    assert not result.ok and any("1 test(s) ignoré(s)" in d for d in result.details)


def test_a_failing_pytest_fails_the_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_postgres: None) -> None:
    result = check(monkeypatch, tmp_path, FakePytest(junit(failures=2), coverage(), returncode=1))
    assert not result.ok and "pytest en échec" in result.details


def test_a_run_that_leaves_no_junit_report_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_postgres: None
) -> None:
    class Silent(FakePytest):
        def __call__(
            self, cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 0, "", "")

    result = check(monkeypatch, tmp_path, Silent("", ""))
    assert not result.ok and "aucun rapport JUnit" in result.details[0]


def test_core_coverage_below_the_threshold_fails_and_files_outside_the_core_do_not_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_postgres: None
) -> None:
    thin = check(monkeypatch, tmp_path, FakePytest(junit(), coverage((79, 100))))
    assert not thin.ok and any("79.0 % < 80 %" in d for d in thin.details)
    enough = check(monkeypatch, tmp_path, FakePytest(junit(), coverage((80, 100))))
    assert enough.ok, enough.details


# ------------------------------------------------------------------ the gate checks the render itself (critic I4)


def make_render(
    path: Path,
    *,
    width: int = 320,
    height: int = 568,
    seconds: float = 3.0,
    audio_db: float | None = 7.8,
    audio_seconds: float | None = None,
) -> None:
    """A small H.264 + AAC file: ffmpeg sine boosted by 7.8 dB measures about -14 LUFS."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s={width}x{height}:r=30:d={seconds}",
    ]
    if audio_db is not None:
        length = audio_seconds if audio_seconds is not None else seconds
        cmd += [
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={length}",
            "-af",
            f"volume={audio_db}dB",
            "-c:a",
            "aac",
        ]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True)


def write_outputs(folder: Path, *, scene_seconds: tuple[float, ...] = (1.5, 1.5), **changes: Any) -> dict[str, Any]:
    """The four JSON files and the render of a good run, with `changes` applied to the report."""
    import hashlib

    folder.mkdir(parents=True, exist_ok=True)
    render = folder / "render.mp4"
    make_render(render, **{k: v for k, v in changes.pop("render", {}).items()})
    total = round(sum(scene_seconds), 1)
    report: dict[str, Any] = {
        "mock": True, "executed": ["idea"], "skipped": [], "waiting": [], "qa_defects": [], "adapters": ["mock-tts"],
        "render_path": str(render), "render_key": hashlib.sha256(render.read_bytes()).hexdigest(),
        "duration_expected_s": total, "scene_count": len(scene_seconds), "step_count": 2,
    }  # fmt: skip
    report.update(changes)
    (folder / "report.json").write_text(json.dumps(report))
    (folder / "manifest.json").write_text(json.dumps({"mock": True, "step_keys": {"a": "1", "b": "2"}}))
    entry = {"mock": True, "kind": "gpu_seconds", "quantity": 1.0}
    (folder / "costs.json").write_text(json.dumps({"mock": True, "entries": [entry]}))
    (folder / "script.scenes.json").write_text(json.dumps({"mock": True, "scenes": [{"duree_s": s} for s in scene_seconds]}))
    return report


@pytest.fixture
def folder(tmp_path: Path, media_tools: None) -> Path:
    return tmp_path / "run"


def judge(folder: Path, report: dict[str, Any], width: int = 320, height: int = 568) -> Any:
    chk = gate.Check("render")
    gate.check_render(chk, folder, report, width, height)
    return chk


@pytest.mark.media
def test_a_good_render_passes_every_independent_check(folder: Path) -> None:
    chk = judge(folder, write_outputs(folder))
    assert chk.ok, chk.details
    assert "320×568" in chk.details[0] and "LUFS" in chk.details[0]


@pytest.mark.media
def test_a_render_shorter_than_its_script_fails_even_when_the_report_agrees_with_the_render(folder: Path) -> None:
    write_outputs(folder)  # the script has 3.0 s of scenes ...
    short = folder / "render.mp4"
    make_render(short, seconds=1.5, audio_seconds=1.5)  # ... the render lasts 1.5 s
    import hashlib

    report = json.loads((folder / "report.json").read_text())
    report.update(
        render_key=hashlib.sha256(short.read_bytes()).hexdigest(), duration_expected_s=1.5
    )  # the report follows the render
    chk = judge(folder, report)
    assert not chk.ok and any("somme des scènes du script" in d for d in chk.details)
    assert any("duration_expected_s du rapport" in d for d in chk.details)


@pytest.mark.media
def test_a_report_that_miscounts_scenes_or_forges_the_render_key_fails(folder: Path) -> None:
    report = write_outputs(folder)
    assert not judge(folder, {**report, "scene_count": 5}).ok
    forged = judge(folder, {**report, "render_key": "0" * 64})
    assert not forged.ok and any("sha256 du rendu" in d for d in forged.details)


@pytest.mark.media
def test_a_render_at_the_wrong_loudness_fails(folder: Path) -> None:
    chk = judge(folder, write_outputs(folder, render={"audio_db": -25.0}))
    assert not chk.ok and any("LUFS hors de -14" in d for d in chk.details)


@pytest.mark.media
def test_a_render_without_audio_or_with_a_short_audio_track_fails(folder: Path) -> None:
    silent = judge(folder, write_outputs(folder, render={"audio_db": None}))
    assert not silent.ok and any("pistes : vidéo=1 audio=0" in d for d in silent.details)
    short_audio = judge(folder / "b", write_outputs(folder / "b", render={"audio_seconds": 1.0}))
    assert not short_audio.ok and any("pistes de longueurs différentes" in d for d in short_audio.details)


@pytest.mark.media
def test_a_render_of_the_wrong_size_fails(folder: Path) -> None:
    chk = judge(folder, write_outputs(folder), width=1080, height=1920)
    assert not chk.ok and any("résolution 320×568 ≠ 1080×1920" in d for d in chk.details)


def test_the_scene_total_is_the_sum_of_the_scene_durations() -> None:
    assert gate.scenes_total({"scenes": [{"duree_s": 1.25}, {"duree_s": 2.5}]}) == (3.8, 2)
    assert gate.scenes_total({}) == (0.0, 0)


def test_the_state_snapshot_sees_anything_a_replay_would_add(tmp_path: Path) -> None:
    import sqlite3

    state = tmp_path / "state"
    (state / "cas" / "ab").mkdir(parents=True)
    with sqlite3.connect(state / "studio.db") as conn:
        for table in ("artifacts", "step_outputs", "entries", "gate_decisions"):
            conn.execute(f"create table {table} (x)")
    before = gate.state_snapshot(state)
    assert gate.state_snapshot(state) == before
    with sqlite3.connect(state / "studio.db") as conn:
        conn.execute("insert into entries values (1)")
    assert gate.state_snapshot(state) != before
    before = gate.state_snapshot(state)
    (state / "cas" / "ab" / ("c" * 64)).write_bytes(b"new object")
    assert gate.state_snapshot(state) != before


class FakeCli:
    """Stands in for `uv run studio run`: the first call writes a run's outputs, later ones may tamper with the state."""

    def __init__(
        self, base: Path, *, replay: Callable[[Path], None] | None = None, outputs: dict[str, Any] | None = None
    ) -> None:
        self.base, self.replay, self.outputs, self.calls = base, replay, outputs or {}, 0

    def __call__(self, cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        import sqlite3

        if cmd[0] != "uv":  # ffprobe and ffmpeg run for real: the gate measures the files the fake CLI wrote
            return subprocess.run(cmd, capture_output=True, text=True)
        out = Path(cmd[cmd.index("--out") + 1])
        fmt = cmd[cmd.index("--format") + 1]
        folder = out / cmd[cmd.index("--channel") + 1] / fmt
        width, height = gate.TARGETS[fmt]
        self.calls += 1
        if self.calls % 2 == 1:
            write_outputs(
                folder, render={"width": width, "height": height}, render_path=str(folder / "render.mp4"), **self.outputs
            )
            state = out / "state"
            (state / "cas").mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(state / "studio.db") as conn:
                for table in ("artifacts", "step_outputs", "entries", "gate_decisions"):
                    conn.execute(f"create table if not exists {table} (x)")
            report = json.loads((folder / "report.json").read_text())
            report["executed"] = ["idea"]
            (folder / "report.json").write_text(json.dumps(report))
        else:
            report = json.loads((folder / "report.json").read_text())
            report.update(executed=[], skipped=["idea"])
            (folder / "report.json").write_text(json.dumps(report))
            if self.replay:
                self.replay(out)
        return subprocess.CompletedProcess(cmd, 0, "", "")


def run_e2e(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake: FakeCli) -> list[Any]:
    monkeypatch.setattr(gate, "run", fake)
    return gate.check_e2e(tmp_path / "out", "channel-a")


@pytest.mark.media
def test_the_e2e_check_passes_a_faithful_run_and_proves_the_replay_by_the_state_it_left(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, media_tools: None
) -> None:
    checks = run_e2e(monkeypatch, tmp_path, FakeCli(tmp_path))
    assert len(checks) == 2 and all(c.ok for c in checks), [c.details for c in checks]
    assert any("état inchangé" in d for d in checks[0].details)


@pytest.mark.media
def test_a_replay_that_says_it_executed_nothing_but_changed_the_state_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, media_tools: None
) -> None:
    import sqlite3

    def touch_the_ledger(out: Path) -> None:
        with sqlite3.connect(out / "state" / "studio.db") as conn:
            conn.execute("insert into entries values (1)")

    checks = run_e2e(monkeypatch, tmp_path, FakeCli(tmp_path, replay=touch_the_ledger))
    assert not any(c.ok for c in checks)
    assert any("l'état (artefacts, étapes, coûts, décisions, fichiers) a changé" in d for c in checks for d in c.details)


@pytest.mark.media
def test_a_run_whose_json_lacks_the_word_mock_or_whose_costs_are_not_flagged_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, media_tools: None
) -> None:
    cli = FakeCli(tmp_path)

    def unmarked(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = cli(cmd)
        if cmd[0] != "uv" or cli.calls % 2 == 0:  # tamper with the first run's files only
            return result
        out = Path(cmd[cmd.index("--out") + 1])
        folder = out / cmd[cmd.index("--channel") + 1] / cmd[cmd.index("--format") + 1]
        costs = json.loads((folder / "costs.json").read_text())
        costs["entries"][0]["mock"] = False  # a cost entry that passes for a real one
        (folder / "costs.json").write_text(json.dumps(costs))
        scenes = json.loads((folder / "script.scenes.json").read_text())
        scenes.pop("mock")  # a scene document that does not say what produced it
        (folder / "script.scenes.json").write_text(json.dumps(scenes))
        return result

    monkeypatch.setattr(gate, "run", unmarked)
    checks = gate.check_e2e(tmp_path / "out", "channel-a")
    details = " ".join(d for c in checks for d in c.details)
    assert not any(c.ok for c in checks)
    assert "script.scenes.json doit porter mock=true" in details and "ne porte pas mock=true" in details


def test_the_e2e_check_reports_a_failing_first_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def boom(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, "", "studio: gpu cap")

    monkeypatch.setattr(gate, "run", boom)
    checks = gate.check_e2e(tmp_path / "out", "channel-a")
    assert len(checks) == 2 and not any(c.ok for c in checks) and "1re exécution en échec" in checks[0].details[0]


@pytest.mark.parametrize(("returncode", "ok"), [(0, True), (1, False)])
def test_the_lint_check_follows_the_exit_code_of_each_tool(monkeypatch: pytest.MonkeyPatch, returncode: int, ok: bool) -> None:
    monkeypatch.setattr(gate, "run", lambda cmd, cwd=ROOT, env=None: subprocess.CompletedProcess(cmd, returncode, "", "boom"))
    assert gate.check_lint().ok is ok
