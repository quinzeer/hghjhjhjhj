"""Step keys (ADR-001 decision 2): SHA-256 of everything that determines a step's output.

key = sha256(canonical_json({step, version, inputs, params, seed}))
- `inputs` maps upstream step names to their *output artifact keys*: a changed upstream output changes
  every downstream key, an unchanged one keeps them (so a replay recomputes nothing).
- `version` is bumped by hand when a step's code changes its output.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from studio.domain.base import canonical_json, sha256_hex


def step_key(
    step: str,
    version: str,
    inputs: Mapping[str, str],
    params: Mapping[str, Any],
    seed: int = 0,
) -> str:
    if not step or not version:
        raise ValueError("step and version are required")
    payload = {"step": step, "version": version, "inputs": dict(inputs), "params": dict(params), "seed": seed}
    return sha256_hex(canonical_json(payload))


def bytes_key(data: bytes) -> str:
    """Artifact key: SHA-256 of the content itself."""
    return sha256_hex(data)


def file_key(path: Path) -> str:
    """Artifact key of a file's content, read in chunks: what a stored object must still hash to."""
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()
