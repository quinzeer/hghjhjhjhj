"""make doctor must fail whenever ANTHROPIC_API_KEY is defined (MISSION §6)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run_doctor(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ROOT / "tools" / "doctor.py")], env=env, capture_output=True, text=True)


def test_doctor_fails_when_api_key_is_set() -> None:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["ANTHROPIC_API_KEY"] = "dummy"
    result = run_doctor(env)
    assert result.returncode == 1
    assert "ANTHROPIC_API_KEY" in result.stdout


def test_doctor_fails_when_api_key_is_empty_but_defined() -> None:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["ANTHROPIC_API_KEY"] = ""
    assert run_doctor(env).returncode == 1


def test_doctor_passes_without_api_key() -> None:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    result = run_doctor(env)
    assert result.returncode == 0, result.stdout


def test_doctor_fails_when_a_settings_file_sets_an_api_key_helper(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "settings.json").write_text('{"apiKeyHelper": "echo sk-fake"}', encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR")}
    env["HOME"] = str(home)
    result = run_doctor(env)
    assert result.returncode == 1
    assert "apiKeyHelper" in result.stdout


def test_doctor_fails_when_a_settings_file_puts_an_api_key_in_env(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "settings.json").write_text('{"env": {"ANTHROPIC_API_KEY": "x"}}', encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR")}
    env["HOME"] = str(home)
    result = run_doctor(env)
    assert result.returncode == 1
    assert "env.ANTHROPIC_API_KEY" in result.stdout


# ------------------------------------------------------------------ execution-plane checks (doctor v2)


def load_doctor() -> ModuleType:
    spec = importlib.util.spec_from_file_location("studio_doctor", ROOT / "tools" / "doctor.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_doctor()

FOUR_CARDS = "".join(f"GPU {i}: NVIDIA GeForce RTX 4070 Ti SUPER (UUID: GPU-{i}abc)\n" for i in range(4))


def fake_run(stdout: str = "", returncode: int = 0) -> Callable[[Sequence[str]], subprocess.CompletedProcess[str]]:
    def run(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(list(cmd), returncode, stdout, "")

    return run


def present(monkeypatch: pytest.MonkeyPatch, *tools: str) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda tool: f"/usr/bin/{tool}" if tool in tools else None)


def test_four_cards_are_listed_by_index_and_name(monkeypatch: pytest.MonkeyPatch) -> None:
    present(monkeypatch, "nvidia-smi")
    errors: list[str] = []
    notes: list[str] = []
    doctor.check_gpus(errors, notes, expected=4, run=fake_run(FOUR_CARDS))
    assert errors == [] and "4 carte(s)" in notes[0] and "3 NVIDIA GeForce RTX 4070 Ti SUPER" in notes[0]


def test_a_missing_card_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    present(monkeypatch, "nvidia-smi")
    errors: list[str] = []
    doctor.check_gpus(errors, [], expected=4, run=fake_run("".join(FOUR_CARDS.splitlines(keepends=True)[:3])))
    assert errors == ["3 carte(s) vue(s), 4 attendue(s) (STUDIO_GPU_COUNT pour changer)"]


def test_no_driver_or_a_failing_nvidia_smi_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    present(monkeypatch)
    errors: list[str] = []
    doctor.check_gpus(errors, [], expected=4, run=fake_run())
    assert "nvidia-smi absent" in errors[0]
    present(monkeypatch, "nvidia-smi")
    errors = []
    doctor.check_gpus(errors, [], expected=4, run=fake_run("", returncode=9))
    assert "ne liste aucune carte (code 9)" in errors[0]


def test_docker_needs_a_reachable_daemon(monkeypatch: pytest.MonkeyPatch) -> None:
    present(monkeypatch, "docker")
    errors: list[str] = []
    notes: list[str] = []
    doctor.check_docker(errors, notes, run=fake_run("27.3.1\n"))
    assert errors == [] and "27.3.1" in notes[0]
    doctor.check_docker(errors, notes, run=fake_run("", returncode=1))
    assert errors == ["le démon Docker ne répond pas (docker info)"]
    present(monkeypatch)
    errors = []
    doctor.check_docker(errors, [], run=fake_run())
    assert errors == ["docker absent"]


@pytest.mark.parametrize(
    ("encoders", "required", "in_errors"),
    [(" V..... libx264\n A....D aac\n", True, False), (" V..... libx264\n", True, True), (" V..... libx264\n", False, False)],
)
def test_ffmpeg_needs_the_encoders_the_studio_writes_with(
    monkeypatch: pytest.MonkeyPatch, encoders: str, required: bool, in_errors: bool
) -> None:
    present(monkeypatch, "ffmpeg", "ffprobe")
    errors: list[str] = []
    notes: list[str] = []
    doctor.check_ffmpeg(errors, notes, required=required, run=fake_run(encoders))
    assert bool(errors) is in_errors
    assert any("aac" in line for line in errors + notes)


def test_a_missing_ffmpeg_is_an_error_only_where_media_proofs_are_required(monkeypatch: pytest.MonkeyPatch) -> None:
    present(monkeypatch)
    errors: list[str] = []
    notes: list[str] = []
    doctor.check_ffmpeg(errors, notes, required=False)
    assert errors == [] and "ffmpeg et ffprobe absent" in notes[0]
    doctor.check_ffmpeg(errors, notes, required=True)
    assert "ffmpeg et ffprobe absent" in errors[0]


@pytest.mark.parametrize(
    ("value", "required"), [("", False), ("0", False), ("no", False), ("1", True), ("yes", True), ("maybe", True)]
)
def test_media_proofs_are_required_unless_the_variable_says_no(value: str, required: bool) -> None:
    assert doctor.media_required({"STUDIO_REQUIRE_MEDIA": value}) is required
    assert doctor.media_required({}) is False
