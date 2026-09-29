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
from typing import Any, Literal, Protocol, runtime_checkable

from studio.adapters.base import AdapterSpec
from studio.core.interfaces import StudioError
from studio.domain import CostKind


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    duration_ms: int = 0
    num_turns: int = 0
    model: str = ""


def usage_costs(usage: LLMUsage) -> dict[CostKind, float]:
    """The ledger quantities of one call's usage (MISSION §6.4): every token the model read (fresh, cache
    creation and cache reads) and every token it wrote."""
    return {
        CostKind.CLAUDE_INPUT_TOKENS: float(usage.input_tokens + usage.cache_creation_tokens + usage.cache_read_tokens),
        CostKind.CLAUDE_OUTPUT_TOKENS: float(usage.output_tokens),
    }


class LLMCallError(StudioError):
    """Base of every failed LLM call. `usage` sums every attempt made: a failed call still costs quota,
    so the cost ledger logs it (the graph runner reads `measured_costs` when a step raises)."""

    def __init__(self, message: str, usage: LLMUsage | None = None) -> None:
        super().__init__(message)
        self.usage: LLMUsage = usage if usage is not None else LLMUsage()

    @property
    def measured_costs(self) -> dict[CostKind, float]:
        return usage_costs(self.usage)


class QuotaExhausted(LLMCallError):
    """The subscription's usage limit was hit: pause the `llm` queue until `reset_at` (None = unknown).

    `kind` tells a plan limit ("quota", may last hours) from a short server-side throttle ("rate")."""

    def __init__(
        self,
        message: str,
        reset_at: dt.datetime | None = None,
        *,
        usage: LLMUsage | None = None,
        kind: Literal["quota", "rate"] = "quota",
    ) -> None:
        super().__init__(message, usage)
        self.reset_at = reset_at
        self.kind = kind


class LLMOutputInvalid(LLMCallError):
    """Output did not validate against the requested schema, even after the bounded retry."""


class ForbiddenAuth(LLMCallError):
    """An API key is visible, or the call would bypass the subscription (e.g. `--bare`)."""


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
