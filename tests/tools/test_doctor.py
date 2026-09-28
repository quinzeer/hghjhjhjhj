"""make doctor must fail whenever ANTHROPIC_API_KEY is defined (MISSION §6)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

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
