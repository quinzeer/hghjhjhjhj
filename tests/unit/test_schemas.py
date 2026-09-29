"""JSON Schema export: the versioned schemas/ equal a fresh export, and `--check` catches any drift."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import studio.schemas.export as export_module
from studio.domain import CONTRACTS
from studio.scenario.skill_json import from_skill_json
from studio.schemas.export import SchemaDirNotFound, check, default_dir, export, find_checkout, main, render

ROOT = Path(__file__).resolve().parents[2]
REPO_SCHEMAS = ROOT / "schemas"
NAMES = sorted(f"{model.__name__}.schema.json" for model in CONTRACTS)


def schema(directory: Path, name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((directory / f"{name}.schema.json").read_text(encoding="utf-8")))


def test_versioned_schemas_match_the_models(capsys: pytest.CaptureFixture[str]) -> None:
    assert default_dir() == REPO_SCHEMAS
    assert sorted(p.name for p in REPO_SCHEMAS.glob("*.schema.json")) == NAMES
    assert check(REPO_SCHEMAS) == []
    assert main(["--check"]) == 0
    assert f"{len(CONTRACTS)} schemas up to date" in capsys.readouterr().out


def test_module_entry_point_checks_the_repository() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "studio.schemas.export", "--check"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr


def test_export_writes_one_canonical_file_per_contract(tmp_path: Path) -> None:
    written = export(tmp_path)
    assert sorted(p.name for p in written) == NAMES
    assert sorted(p.name for p in tmp_path.iterdir()) == NAMES
    for model in CONTRACTS:
        text = (tmp_path / f"{model.__name__}.schema.json").read_text(encoding="utf-8")
        assert json.loads(text) == model.model_json_schema()
        assert text == json.dumps(json.loads(text), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        assert text.endswith("}\n") and "\r" not in text
    for path in written:
        assert stat.S_IMODE(path.stat().st_mode) == 0o644  # readable by everyone, as a plain write would leave it


def test_export_is_idempotent(tmp_path: Path) -> None:
    export(tmp_path)
    first = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    export(tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == first


def test_exported_schemas_are_valid_and_as_strict_as_the_models(tmp_path: Path) -> None:
    export(tmp_path)
    for name in NAMES:
        Draft202012Validator.check_schema(json.loads((tmp_path / name).read_text(encoding="utf-8")))

    doc = json.loads((ROOT / "tests" / "fixtures" / "skill_scenes_long.json").read_text(encoding="utf-8"))
    script, package = from_skill_json(doc, "lighthouse-lens")
    for name, instance in (("Script", script.model_dump(mode="json")), ("Package", package.model_dump(mode="json"))):
        validator = schema(tmp_path, name)
        assert list(validator.iter_errors(instance)) == []
        assert list(validator.iter_errors({**instance, "colour": "red"}))  # unknown field refused, as by the model

    scene = script.scenes[0].model_dump(mode="json")
    assert list(schema(tmp_path, "Scene").iter_errors({**scene, "role": "cadre"}))  # English wire values only


def test_check_is_green_after_export_and_red_after_an_edit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    export(tmp_path)
    assert main(["--check", "--dir", str(tmp_path)]) == 0
    capsys.readouterr()

    target = tmp_path / "Script.schema.json"
    text = target.read_text(encoding="utf-8")
    assert '"title": "Script"' in text
    target.write_text(text.replace('"title": "Script"', '"title": "Scripts"'), encoding="utf-8")
    assert main(["--check", "--dir", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert f"differs: {target}" in err
    assert "Scene.schema.json" not in err  # only the edited file is reported

    export(tmp_path)
    assert main(["--check", "--dir", str(tmp_path)]) == 0


def test_check_catches_a_whitespace_only_change(tmp_path: Path) -> None:
    export(tmp_path)
    target = tmp_path / "Scene.schema.json"
    target.write_text(target.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    assert json.loads(target.read_text(encoding="utf-8")) == json.loads((REPO_SCHEMAS / "Scene.schema.json").read_text())
    assert main(["--check", "--dir", str(tmp_path)]) == 1


def test_check_is_red_when_a_file_is_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    export(tmp_path)
    (tmp_path / "Package.schema.json").unlink()
    assert main(["--check", "--dir", str(tmp_path)]) == 1
    assert "missing:" in capsys.readouterr().err


def test_check_on_an_absent_directory_reports_every_file_and_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "nowhere"
    problems = check(target)
    assert len(problems) == len(CONTRACTS) and all(p.startswith("missing: ") for p in problems)
    assert main(["--check", "--dir", str(target)]) == 1
    assert not target.exists()


def test_stale_schema_of_a_removed_contract_is_flagged_then_removed(tmp_path: Path) -> None:
    export(tmp_path)
    stale = tmp_path / "Retired.schema.json"
    stale.write_text("{}\n", encoding="utf-8")
    other = tmp_path / "README.md"
    other.write_text("kept\n", encoding="utf-8")
    assert check(tmp_path) == [f"unexpected: {stale}"]
    export(tmp_path)
    assert not stale.exists()
    assert other.read_text(encoding="utf-8") == "kept\n"
    assert check(tmp_path) == []


def test_main_writes_without_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "nested" / "schemas"
    assert main(["--dir", str(out)]) == 0
    assert f"wrote {len(CONTRACTS)} schemas" in capsys.readouterr().out
    assert check(out) == []


# ------------------------------------------------------------------ atomic writes

WRITER = """
import sys
from pathlib import Path
from studio.schemas.export import export
target, rounds = Path(sys.argv[1]), int(sys.argv[2])
export(target)
print("ready", flush=True)
for _ in range(rounds):
    export(target)
"""


def test_a_reader_never_sees_a_partial_schema_while_export_rewrites_it(tmp_path: Path) -> None:
    expected = {name: text.encode("utf-8") for name, text in render().items()}
    writer = subprocess.Popen([sys.executable, "-c", WRITER, str(tmp_path), "60"], cwd=ROOT, stdout=subprocess.PIPE, text=True)
    assert writer.stdout is not None and writer.stdout.readline() == "ready\n"
    passes, torn = 0, []
    while writer.poll() is None:  # every rewrite carries the same text: any other content is a torn read
        for name, data in expected.items():
            try:
                seen = (tmp_path / name).read_bytes()
            except FileNotFoundError:
                seen = b"<missing>"
            if seen != data:
                torn.append(f"{name}: {len(seen)} of {len(data)} bytes")
        passes += 1
    assert writer.wait() == 0
    assert passes >= 100  # the reads really overlapped the rewrites
    assert torn == []
    assert check(tmp_path) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == NAMES  # no temporary file left behind


def test_a_failed_export_leaves_every_previous_file_whole(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    export(tmp_path)
    (tmp_path / "Script.schema.json").write_text("{}\n", encoding="utf-8")  # out of date: export must replace it
    (tmp_path / "Retired.schema.json").write_text("{}\n", encoding="utf-8")  # stale: export must remove it
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}

    def mock_crash_before_replace(src: object, dst: object) -> None:  # the process dies before publishing a file
        raise OSError("mock crash")

    monkeypatch.setattr(os, "replace", mock_crash_before_replace)
    with pytest.raises(OSError, match="mock crash"):
        export(tmp_path)
    monkeypatch.undo()
    # nothing truncated, no temporary file left, the stale file not yet removed: the next export starts clean
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    export(tmp_path)
    assert check(tmp_path) == []


# ------------------------------------------------------------------ default directory


def make_checkout(root: Path, name: str = "studio") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n', encoding="utf-8")
    return root


def installed_module_dir(venv: Path) -> Path:
    """Where studio/schemas/ lands when the wheel is installed into `venv`."""
    path = venv / "lib" / "python3.12" / "site-packages" / "studio" / "schemas"
    path.mkdir(parents=True)
    return path


def test_default_dir_follows_the_imported_module_to_its_checkout() -> None:
    assert find_checkout(Path(export_module.__file__)) == ROOT
    assert find_checkout(ROOT / "tests" / "unit") == ROOT
    assert default_dir() == REPO_SCHEMAS


def test_the_imported_module_wins_over_another_checkout_in_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The schemas describe the models that are imported: they belong to the checkout those models come from."""
    monkeypatch.chdir(make_checkout(tmp_path / "other-worktree"))
    assert default_dir() == REPO_SCHEMAS


def test_default_dir_through_a_virtualenv_inside_the_checkout(tmp_path: Path) -> None:
    checkout = make_checkout(tmp_path / "repo")
    assert default_dir([installed_module_dir(checkout / ".venv"), tmp_path]) == checkout / "schemas"


def test_default_dir_skips_other_projects_then_tries_the_working_directory(tmp_path: Path) -> None:
    other = make_checkout(tmp_path / "other", name="not-studio")
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "pyproject.toml").write_text("[project\n", encoding="utf-8")
    checkout = make_checkout(tmp_path / "broken" / "repo")
    (checkout / "docs").mkdir()
    assert default_dir([installed_module_dir(other / ".venv"), checkout / "docs"]) == checkout / "schemas"


def test_default_dir_outside_any_checkout_fails_clearly(tmp_path: Path) -> None:
    make_checkout(tmp_path / "other", name="not-studio")
    with pytest.raises(SchemaDirNotFound, match="pass --dir"):
        default_dir([installed_module_dir(tmp_path / "venv"), tmp_path / "other"])


def test_installed_copy_never_writes_into_site_packages(tmp_path: Path) -> None:
    site = tmp_path / "venv" / "lib" / "python3.12" / "site-packages"
    shutil.copytree(ROOT / "studio", site / "studio", ignore=shutil.ignore_patterns("__pycache__"))
    work = tmp_path / "work"
    work.mkdir()
    env = {**os.environ, "PYTHONPATH": str(site)}

    def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, check=False)

    probe = run("-c", "import studio.schemas.export as m; print(m.__file__)", cwd=work)
    assert probe.stdout.strip() == str(site / "studio" / "schemas" / "export.py")  # the installed copy is what runs

    for args in (["--check"], []):
        outside = run("-m", "studio.schemas.export", *args, cwd=work)
        assert outside.returncode == 2, outside.stderr
        assert "no source checkout of the 'studio' project" in outside.stderr and "pass --dir" in outside.stderr
    assert not (site / "schemas").exists() and list(work.iterdir()) == []

    explicit = run("-m", "studio.schemas.export", "--check", "--dir", str(REPO_SCHEMAS), cwd=work)
    assert explicit.returncode == 0, explicit.stderr

    # from inside the checkout, the working directory leads to it even though the module lives elsewhere
    code = (
        f"import sys; sys.path.insert(0, {str(site)!r}); import studio.schemas.export as m; "
        f"assert m.__file__.startswith({str(site)!r}); raise SystemExit(m.main(['--check']))"
    )
    inside = run("-c", code, cwd=ROOT / "tests")
    assert inside.returncode == 0, inside.stderr
    assert f"up to date in {REPO_SCHEMAS}" in inside.stdout
