#!/usr/bin/env python3
"""Environment health check (MISSION §6): fails if ANTHROPIC_API_KEY exists anywhere we can see.

Phase 0 scope: build-plane checks only. GPU, Docker and ffmpeg checks arrive with phases 1 and 3.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_VAR = "ANTHROPIC_API_KEY"


def main() -> int:
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

    if sys.version_info < (3, 11):
        errors.append(f"Python {sys.version.split()[0]} < 3.11 (le vérificateur de phase 0 exige ≥ 3.11).")
    for tool in ("git", "uv"):
        if shutil.which(tool) is None:
            errors.append(f"outil manquant : {tool}")
    for tool in ("claude", "ffmpeg", "ffprobe", "docker", "nvidia-smi"):
        notes.append(f"{tool}: {'présent' if shutil.which(tool) else 'absent (requis plus tard sur la machine GPU)'}")
    token = "présent" if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") else "absent (requis sur la machine d'exécution, phase 2)"
    notes.append(f"CLAUDE_CODE_OAUTH_TOKEN: {token}")

    for n in notes:
        print(f"  · {n}")
    for e in errors:
        print(f"  ✗ {e}")
    print("doctor : OK" if not errors else f"doctor : {len(errors)} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
