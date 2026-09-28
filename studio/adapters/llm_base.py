"""LLM contract (MISSION §6 « Claude à l'exécution »): one interface, several backends.

The production backend is `ClaudeCodeRunner` (`claude -p` on the subscription, never an API key, never
`--bare`). A mock backend replays recorded outputs for tests. A future backend plugs in by configuration
without touching the agents.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from studio.adapters.base import AdapterSpec
from studio.core.interfaces import StudioError


class QuotaExhausted(StudioError):
    """The subscription's usage limit was hit: pause the `llm` queue until `reset_at` (None = unknown)."""

    def __init__(self, message: str, reset_at: dt.datetime | None = None) -> None:
        super().__init__(message)
        self.reset_at = reset_at


class LLMOutputInvalid(StudioError):
    """Output did not validate against the requested schema, even after the bounded retry."""


class ForbiddenAuth(StudioError):
    """An API key is visible, or the call would bypass the subscription (e.g. `--bare`)."""


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    duration_ms: int = 0
    num_turns: int = 0
    model: str = ""


@dataclass(frozen=True)
class LLMResult:
    output: Any  # dict when a schema was given, else str
    usage: LLMUsage
    session_id: str
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMRunner(Protocol):
    spec: AdapterSpec

    def run(
        self,
        *,
        agent: str,
        prompt: str,
        model: str,
        json_schema: dict[str, Any] | None,
        max_turns: int,
        allowed_tools: Sequence[str],
        cwd: Path,
    ) -> LLMResult: ...
