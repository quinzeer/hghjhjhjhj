"""The phase 1 gate must fail closed: no Postgres, a skipped test or thin core coverage each turn it red."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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
