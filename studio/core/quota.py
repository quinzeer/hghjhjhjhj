"""Claude quota manager (ADR-001 decision 7 and failure scenario « limite d'usage Claude atteinte »).

- `record` accumulates the measured usage of every call (totals, per model, and a rolling history for
  window sums such as the subscription's 5-hour window). Failed calls count too: the runner's exceptions
  carry the usage of the attempts they wasted (`studio.adapters.claude_code.call_usage`).
- `on_exhausted` pauses the `llm` queue until the reset time carried by QuotaExhausted; a later reset always
  wins. When the reset time is unknown (or already past) the pause is `default_pause` (1 h), doubled for each
  unknown-reset exhaustion that comes back within `default_pause` of the end of the previous one, up to
  `max_pause` (8 h): a weekly limit whose date could not be read then costs a handful of failed calls instead
  of one per hour. A known reset, or a quiet period, starts the doubling over.
- The pause lifts by itself: every check compares the clock with the reset time.
- Priorities (lower = more urgent, the DBOS convention): compliance and scripts, then critique, then scout.
  `can_run` and `next_run_at` take a Priority or its int value (`Job.priority`); anything else is refused.
  In economy mode, scout calls only run inside the night window and non-creative calls asking for Opus get
  Sonnet.

The pause lives in memory: exactly one QuotaManager serves the `llm` queue of an execution process, and
several processes do not share it. `state()` returns a JSON-serialisable QuotaState and the `state`
argument restores it, so the queue wiring can persist the pause and survive a restart.

Times come from the injected clock, which must return aware datetimes; the night window `(start, end)` is
read in the clock's zone, `start` inclusive and `end` exclusive, and may wrap midnight (e.g. `(22, 6)`).
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from studio.adapters.llm_base import LLMUsage, QuotaExhausted

log = logging.getLogger(__name__)

DEFAULT_PAUSE = dt.timedelta(hours=1)
MAX_UNKNOWN_PAUSE = dt.timedelta(hours=8)
DEFAULT_HISTORY = dt.timedelta(days=7)  # the subscription also has a weekly cap
ECONOMY_MODEL = "sonnet"


class Priority(IntEnum):
    COMPLIANCE_AND_SCRIPTS = 0
    CRITIQUE = 1
    SCOUT = 2


def as_priority(priority: int) -> Priority:
    """The Priority of `priority` (a Priority or its int value); ValueError otherwise."""
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValueError(f"priority must be a Priority or its int value, got {priority!r}")
    return Priority(priority)  # ValueError when out of range


@dataclass(frozen=True)
class UsageTotals:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    duration_ms: int = 0

    def plus(self, usage: LLMUsage) -> UsageTotals:
        return UsageTotals(
            calls=self.calls + 1,
            input_tokens=self.input_tokens + usage.input_tokens,
            output_tokens=self.output_tokens + usage.output_tokens,
            cache_read_tokens=self.cache_read_tokens + usage.cache_read_tokens,
            cache_creation_tokens=self.cache_creation_tokens + usage.cache_creation_tokens,
            duration_ms=self.duration_ms + usage.duration_ms,
        )


def _aware(value: dt.datetime | None, what: str) -> dt.datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{what} must be timezone-aware")
    return value


@dataclass(frozen=True)
class QuotaState:
    """What must survive a restart: the pause and the unknown-reset backoff."""

    paused_until: dt.datetime | None = None
    unknown_streak: int = 0
    unknown_until: dt.datetime | None = None  # end of the last pause taken for an unknown reset

    def __post_init__(self) -> None:
        _aware(self.paused_until, "paused_until")
        _aware(self.unknown_until, "unknown_until")
        if isinstance(self.unknown_streak, bool) or not isinstance(self.unknown_streak, int) or self.unknown_streak < 0:
            raise ValueError("unknown_streak must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {
            "paused_until": self.paused_until.isoformat() if self.paused_until else None,
            "unknown_streak": self.unknown_streak,
            "unknown_until": self.unknown_until.isoformat() if self.unknown_until else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> QuotaState:
        def when(key: str) -> dt.datetime | None:
            value = data.get(key)
            return dt.datetime.fromisoformat(value) if isinstance(value, str) else None

        return cls(
            paused_until=when("paused_until"),
            unknown_streak=int(data.get("unknown_streak", 0)),
            unknown_until=when("unknown_until"),
        )


def _is_opus(model: str) -> bool:
    return "opus" in model.lower()


class QuotaManager:
    """Thread-safe: the `llm` workers of one process share one instance."""

    def __init__(
        self,
        clock: Callable[[], dt.datetime],
        night_window: tuple[int, int] = (1, 7),
        economy: bool = False,
        *,
        default_pause: dt.timedelta = DEFAULT_PAUSE,
        max_pause: dt.timedelta = MAX_UNKNOWN_PAUSE,
        history: dt.timedelta = DEFAULT_HISTORY,
        state: QuotaState | None = None,
    ) -> None:
        start, end = night_window
        if not (0 <= start <= 23 and 0 <= end <= 24 and start != end):
            raise ValueError(
                f"night_window must be (start, end) hours with 0 <= start <= 23, 0 <= end <= 24, start != end: {night_window}"
            )
        if default_pause <= dt.timedelta(0) or history <= dt.timedelta(0):
            raise ValueError("default_pause and history must be positive")
        if max_pause < default_pause:
            raise ValueError("max_pause must be at least default_pause")
        self._clock = clock
        self.night_window = (start, end)
        self.economy = economy
        self.default_pause = default_pause
        self.max_pause = max_pause
        self.history = history
        self._lock = threading.Lock()
        restored = state or QuotaState()
        self._paused_until = restored.paused_until
        self._unknown_streak = restored.unknown_streak
        self._unknown_until = restored.unknown_until
        self._totals = UsageTotals()
        self._by_model: dict[str, UsageTotals] = {}
        self._recent: deque[tuple[dt.datetime, LLMUsage]] = deque()
        self.exhaustions = 0

    # -------------------------------------------------------------- clock

    def now(self) -> dt.datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("the quota clock must return timezone-aware datetimes")
        return now

    # -------------------------------------------------------------- usage

    def record(self, usage: LLMUsage) -> None:
        now = self.now()
        with self._lock:
            self._totals = self._totals.plus(usage)
            model = usage.model or "unknown"
            self._by_model[model] = self._by_model.get(model, UsageTotals()).plus(usage)
            self._recent.append((now, usage))
            horizon = now - self.history
            while self._recent and self._recent[0][0] < horizon:
                self._recent.popleft()

    def totals(self, model: str | None = None) -> UsageTotals:
        with self._lock:
            if model is None:
                return self._totals
            return self._by_model.get(model, UsageTotals())

    def usage_since(self, window: dt.timedelta) -> UsageTotals:
        """Usage recorded during the last `window` (at most `history` back)."""
        horizon = self.now() - window
        with self._lock:
            recent = [usage for at, usage in self._recent if at >= horizon]
        totals = UsageTotals()
        for usage in recent:
            totals = totals.plus(usage)
        return totals

    # -------------------------------------------------------------- pause

    def _backoff(self, streak: int) -> dt.timedelta:
        pause = self.default_pause
        for _ in range(1, streak):
            if pause >= self.max_pause:
                break
            pause *= 2
        return min(pause, self.max_pause)

    def _unknown_pause(self, now: dt.datetime) -> dt.timedelta:
        """Pause for an unknown reset; the caller holds the lock."""
        ended = self._unknown_until
        if ended is not None and now < ended:
            self._unknown_streak = max(self._unknown_streak, 1)  # another worker hit the same limit: same step
        elif ended is not None and now - ended <= self.default_pause:
            # the limit was still there right after the last pause; the step stops growing at max_pause
            if self._backoff(self._unknown_streak) < self.max_pause:
                self._unknown_streak = max(self._unknown_streak, 0) + 1
        else:
            self._unknown_streak = 1
        return self._backoff(self._unknown_streak)

    def on_exhausted(self, exc: QuotaExhausted) -> dt.datetime:
        """Pause every priority until the reset; returns the effective end of the pause."""
        now = self.now()
        reset = exc.reset_at
        if reset is not None and (reset.tzinfo is None or reset.utcoffset() is None):
            reset = reset.replace(tzinfo=dt.UTC)
        known = reset is not None and reset > now
        with self._lock:
            self.exhaustions += 1
            if known and reset is not None:
                until = reset
                self._unknown_streak, self._unknown_until = 0, None
            else:
                until = now + self._unknown_pause(now)
                if self._unknown_until is None or until > self._unknown_until:
                    self._unknown_until = until
            if self._paused_until is None or self._paused_until <= now or until > self._paused_until:
                self._paused_until = until
            effective = self._paused_until
            streak = self._unknown_streak
        log.warning(
            "claude quota exhausted: llm queue paused until %s (reset %s)",
            effective.isoformat(),
            "known" if known else f"unknown, backoff step {streak}",
        )
        return effective

    @property
    def paused_until(self) -> dt.datetime | None:
        """End of the current pause, or None when not paused (an elapsed pause is cleared here)."""
        now = self.now()
        with self._lock:
            if self._paused_until is not None and now >= self._paused_until:
                log.info("claude quota pause over at %s: llm queue resumed", self._paused_until.isoformat())
                self._paused_until = None
            return self._paused_until

    def is_paused(self) -> bool:
        return self.paused_until is not None

    def resume(self) -> None:
        """Operator override: lift the pause now and forget the backoff."""
        with self._lock:
            self._paused_until = None
            self._unknown_streak, self._unknown_until = 0, None

    def state(self) -> QuotaState:
        with self._lock:
            return QuotaState(
                paused_until=self._paused_until, unknown_streak=self._unknown_streak, unknown_until=self._unknown_until
            )

    # -------------------------------------------------------------- scheduling

    def in_night_window(self, at: dt.datetime | None = None) -> bool:
        hour = (at or self.now()).hour
        start, end = self.night_window
        return start <= hour < end if start < end else hour >= start or hour < end

    def _deferred_to_night(self, priority: Priority) -> bool:
        return self.economy and priority == Priority.SCOUT

    def can_run(self, priority: int) -> bool:
        level = as_priority(priority)
        if self.is_paused():
            return False
        return not (self._deferred_to_night(level) and not self.in_night_window())

    def next_run_at(self, priority: int) -> dt.datetime:
        """Earliest time a call of `priority` may start (now when it may start now)."""
        level = as_priority(priority)
        now = self.now()
        paused = self.paused_until
        at = paused.astimezone(now.tzinfo) if paused is not None else now  # the window is read in the clock's zone
        if self._deferred_to_night(level) and not self.in_night_window(at):
            start_hour = self.night_window[0]
            start = at.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            if start <= at:
                start += dt.timedelta(days=1)
            return start
        return at

    def choose_model(self, requested: str, creative: bool) -> str:
        """In economy mode a non-creative call that asks for Opus runs on Sonnet; everything else is kept."""
        if self.economy and not creative and _is_opus(requested):
            return ECONOMY_MODEL
        return requested
