#!/usr/bin/env python3
"""Environment health check (MISSION §6): fails if ANTHROPIC_API_KEY exists anywhere we can see.

    doctor.py                    build plane (this repository, CI, the cloud VM): no GPU needed
    doctor.py --role execution   execution plane (the GPU machine): also needs Docker, the GPUs and a Claude token

The build plane needs ffmpeg for the media proofs; with STUDIO_REQUIRE_MEDIA set (CI, `make verify-phase-1`) its
absence is an error, otherwise a note.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_VAR = "ANTHROPIC_API_KEY"
REQUIRE_MEDIA_ENV = "STUDIO_REQUIRE_MEDIA"
GPU_COUNT_ENV = "STUDIO_GPU_COUNT"
DEFAULT_GPU_COUNT = 4  # MISSION §5: 4x RTX 4070 Ti Super
ENCODERS = ("libx264", "aac")  # what studio.media writes
Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _run(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(cmd), capture_output=True, text=True, timeout=30)


def media_required(environ: dict[str, str] | os._Environ[str] = os.environ) -> bool:
    return environ.get(REQUIRE_MEDIA_ENV, "").strip().lower() not in {"", "0", "false", "no", "off"}


def check_ffmpeg(errors: list[str], notes: list[str], *, required: bool, run: Runner = _run) -> None:
    """ffmpeg and ffprobe on PATH, and the two encoders the studio writes with."""
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        (errors if required else notes).append(f"{' et '.join(missing)} absent : les preuves média ne peuvent pas tourner")
        return
    result = run(["ffmpeg", "-hide_banner", "-encoders"])
    absent = [enc for enc in ENCODERS if not re.search(rf"\b{enc}\b", result.stdout)]
    if absent:
        (errors if required else notes).append(f"ffmpeg sans l'encodeur {', '.join(absent)}")
    else:
        notes.append(f"ffmpeg, ffprobe : présents ({', '.join(ENCODERS)} disponibles)")


def check_gpus(errors: list[str], notes: list[str], *, expected: int, run: Runner = _run) -> None:
    """`nvidia-smi -L` lists exactly the number of GPUs the machine is meant to have (one worker per card)."""
    if shutil.which("nvidia-smi") is None:
        errors.append("nvidia-smi absent : pilote NVIDIA non installé")
        return
    result = run(["nvidia-smi", "-L"])
    cards = re.findall(r"^GPU (\d+): ([^(]+)", result.stdout, flags=re.MULTILINE)
    if result.returncode != 0 or not cards:
        errors.append(f"nvidia-smi -L ne liste aucune carte (code {result.returncode})")
    elif len(cards) != expected:
        errors.append(f"{len(cards)} carte(s) vue(s), {expected} attendue(s) ({GPU_COUNT_ENV} pour changer)")
    else:
        notes.append(f"{len(cards)} carte(s) : " + " ; ".join(f"{i} {name.strip()}" for i, name in cards))


def check_docker(errors: list[str], notes: list[str], *, run: Runner = _run) -> None:
    if shutil.which("docker") is None:
        errors.append("docker absent")
        return
    result = run(["docker", "info", "--format", "{{.ServerVersion}}"])
    if result.returncode != 0:
        errors.append("le démon Docker ne répond pas (docker info)")
    else:
        notes.append(f"docker : démon {result.stdout.strip() or '?'} joignable")


def check_claude_settings(errors: list[str], notes: list[str]) -> None:
    """Fail when a Claude Code settings file (user, project, local, managed) would bypass the subscription
    (`apiKeyHelper`, or an API key in `env`). Needs the studio package; skipped before `uv sync`."""
    sys.path.insert(0, str(ROOT))
    try:
        from studio.adapters.claude_code import check_settings, settings_files
        from studio.adapters.llm_base import ForbiddenAuth
    except (ImportError, SyntaxError):
        notes.append("réglages Claude Code non contrôlés (dépendances absentes : uv sync)")
        return
    finally:
        sys.path.remove(str(ROOT))
    try:
        check_settings(settings_files(os.environ, ROOT))
    except ForbiddenAuth as exc:
        errors.append(str(exc))
    else:
        notes.append("réglages Claude Code : aucun contournement de l'abonnement")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--role", choices=("build", "execution"), default="build")
    args = parser.parse_args(argv)
    errors: list[str] = []
    notes: list[str] = []

    if os.environ.get(FORBIDDEN_VAR) is not None:
        errors.append(f"{FORBIDDEN_VAR} est définie dans l'environnement : le studio n'utilise que Claude Code sur abonnement.")
    for env_file in (ROOT / ".env", Path.home() / ".env"):
        if env_file.is_file() and any(
            line.split("=", 1)[0].strip().removeprefix("export ").strip() == FORBIDDEN_VAR
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        ):
            errors.append(f"{FORBIDDEN_VAR} est définie dans {env_file}.")

    check_claude_settings(errors, notes)

    if sys.version_info < (3, 11):
        errors.append(f"Python {sys.version.split()[0]} < 3.11 (le vérificateur de phase 0 exige ≥ 3.11).")
    for tool in ("git", "uv"):
        if shutil.which(tool) is None:
            errors.append(f"outil manquant : {tool}")
    execution = args.role == "execution"
    check_ffmpeg(errors, notes, required=execution or media_required())
    if execution:
        expected = int(os.environ.get(GPU_COUNT_ENV, DEFAULT_GPU_COUNT))
        check_gpus(errors, notes, expected=expected)
        check_docker(errors, notes)
        for tool in ("claude",):
            if shutil.which(tool) is None:
                errors.append(f"outil manquant : {tool}")
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            errors.append(
                "CLAUDE_CODE_OAUTH_TOKEN absent : les agents `claude -p` ne pourraient pas s'authentifier sur l'abonnement"
            )
    else:
        for tool in ("claude", "docker", "nvidia-smi"):
            notes.append(
                f"{tool}: {'présent' if shutil.which(tool) else 'absent (requis sur la machine GPU : doctor --role execution)'}"
            )

    for n in notes:
        print(f"  · {n}")
    for e in errors:
        print(f"  ✗ {e}")
    print("doctor : OK" if not errors else f"doctor : {len(errors)} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
