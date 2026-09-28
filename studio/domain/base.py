"""Base contract: every object that crosses a step boundary is a frozen, strict Pydantic model.

Canonical JSON (sorted keys, no whitespace, UTF-8) is the only serialisation used for hashing, so the
same content always gives the same key whatever the producer (MISSION §6, principles 1 and 2).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict


def canonical_json(data: Any) -> str:
    """Deterministic JSON text: sorted keys, compact separators, non-ASCII kept as is."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_hex(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


class StudioModel(BaseModel):
    """Strict, immutable contract. Unknown fields are rejected, values are validated on assignment."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    def canonical_json(self) -> str:
        return canonical_json(self.model_dump(mode="json"))

    def content_hash(self) -> str:
        """SHA-256 of the canonical JSON: identical content, identical hash."""
        return sha256_hex(self.canonical_json())
