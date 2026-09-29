"""QuotaManager: pause on QuotaExhausted, automatic resume at the reset, priorities, economy mode, usage
accounting, and thread safety."""

from __future__ import annotations

import datetime as dt
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import pytest

from studio.adapters.llm_base import LLMUsage, QuotaExhausted
from studio.core.quota import (
    DEFAULT_PAUSE,
    ECONOMY_MODEL,
    MAX_UNKNOWN_PAUSE,
    Priority,
    QuotaManager,
    QuotaState,
    UsageTotals,
    as_priority,
)

UTC = dt.UTC
PARIS = dt.timezone(dt.timedelta(hours=2))
NOON = dt.datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ALL = tuple(Priority)


class MockClock:
    """Settable clock (test double)."""

    def __init__(self, now: dt.datetime) -> None:
        self.now = now
        self._lock = threading.Lock()

    def __call__(self) -> dt.datetime:
        with self._lock:
            return self.now

    def set(self, now: dt.datetime) -> None:
        with self._lock:
            self.now = now


def at(hour: int, minute: int = 0, day: int = 28, tz: dt.tzinfo = UTC) -> dt.datetime:
    return dt.datetime(2026, 9, day, hour, minute, tzinfo=tz)


def usage(tokens: int = 10, model: str = "claude-sonnet-x") -> LLMUsage:
    return LLMUsage(
        input_tokens=tokens,
        output_tokens=2 * tokens,
        cache_read_tokens=3 * tokens,
        cache_creation_tokens=4 * tokens,
        duration_ms=100,
        num_turns=1,
        model=model,
    )


# ------------------------------------------------------------------ priorities


def test_priority_order_follows_the_dbos_convention() -> None:
    assert [(p.name, p.value) for p in Priority] == [("COMPLIANCE_AND_SCRIPTS", 0), ("CRITIQUE", 1), ("SCOUT", 2)]
    assert sorted([Priority.SCOUT, Priority.COMPLIANCE_AND_SCRIPTS, Priority.CRITIQUE]) == list(Priority)


def test_int_priorities_get_the_same_treatment() -> None:
    # Job.priority is an int: before the fix, `can_run(2)` bypassed economy mode (identity check on SCOUT).
    quota = QuotaManager(MockClock(at(12)), night_window=(1, 7), economy=True)

    assert quota.can_run(2) is False and quota.can_run(Priority.SCOUT) is False
    assert quota.next_run_at(2) == quota.next_run_at(Priority.SCOUT) == at(1, day=29)
    assert quota.can_run(0) and quota.can_run(1)
    assert as_priority(2) is Priority.SCOUT


@pytest.mark.parametrize("bad", [3, -1, True, "2", 1.0])
def test_unknown_priorities_are_refused(bad: object) -> None:
    quota = QuotaManager(MockClock(NOON))
    with pytest.raises(ValueError):
        quota.can_run(cast(Any, bad))
    with pytest.raises(ValueError):
        quota.next_run_at(cast(Any, bad))


def test_everything_runs_when_not_paused_and_not_in_economy() -> None:
    quota = QuotaManager(MockClock(NOON))
    assert all(quota.can_run(p) for p in ALL)
    assert all(quota.next_run_at(p) == NOON for p in ALL)
    assert quota.paused_until is None and not quota.is_paused()


# ------------------------------------------------------------------ pause and resume


def test_pause_until_reset_then_automatic_resume() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)
    reset = NOON + dt.timedelta(hours=2, minutes=13)

    assert quota.on_exhausted(QuotaExhausted("limit", reset_at=reset)) == reset
    assert quota.paused_until == reset
    assert not any(quota.can_run(p) for p in ALL)  # even compliance waits: there is no quota left
    assert all(quota.next_run_at(p) == reset for p in (Priority.COMPLIANCE_AND_SCRIPTS, Priority.CRITIQUE))

    clock.set(reset - dt.timedelta(seconds=1))
    assert not quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)

    clock.set(reset)
    assert all(quota.can_run(p) for p in ALL)
    assert quota.paused_until is None
    assert quota.exhaustions == 1


@pytest.mark.parametrize("reset_at", [None, NOON - dt.timedelta(minutes=5), NOON])
def test_unknown_or_past_reset_pauses_for_one_hour(reset_at: dt.datetime | None) -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)

    assert quota.on_exhausted(QuotaExhausted("limit", reset_at=reset_at)) == NOON + DEFAULT_PAUSE
    assert DEFAULT_PAUSE == dt.timedelta(hours=1)
    clock.set(NOON + dt.timedelta(minutes=59))
    assert not quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)
    clock.set(NOON + dt.timedelta(hours=1))
    assert quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)


def test_naive_reset_is_read_as_utc() -> None:
    quota = QuotaManager(MockClock(NOON))
    naive = dt.datetime(2026, 9, 28, 15, 0)
    assert quota.on_exhausted(QuotaExhausted("limit", reset_at=naive)) == dt.datetime(2026, 9, 28, 15, 0, tzinfo=UTC)


def test_a_later_reset_extends_an_earlier_one_never_shortens() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)
    late, early = NOON + dt.timedelta(hours=5), NOON + dt.timedelta(hours=2)

    quota.on_exhausted(QuotaExhausted("weekly", reset_at=late))
    assert quota.on_exhausted(QuotaExhausted("session", reset_at=early)) == late
    assert quota.paused_until == late

    clock.set(late)  # the pause elapsed: a new, earlier reset applies again
    new_reset = late + dt.timedelta(minutes=30)
    assert quota.on_exhausted(QuotaExhausted("session", reset_at=new_reset)) == new_reset


def test_concurrent_exhaustions_keep_the_latest_reset() -> None:
    quota = QuotaManager(MockClock(NOON))
    rng = random.Random(7)
    resets = [NOON + dt.timedelta(minutes=rng.randint(1, 600)) for _ in range(200)]
    barrier = threading.Barrier(8)

    def worker(chunk: list[dt.datetime]) -> None:
        barrier.wait()
        for reset in chunk:
            quota.on_exhausted(QuotaExhausted("limit", reset_at=reset))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, [resets[i::8] for i in range(8)]))

    assert quota.paused_until == max(resets)
    assert quota.exhaustions == 200


def test_manual_resume() -> None:
    quota = QuotaManager(MockClock(NOON))
    quota.on_exhausted(QuotaExhausted("limit"))
    quota.resume()
    assert quota.can_run(Priority.SCOUT)
    assert quota.state() == QuotaState()  # the backoff is forgotten too


# ------------------------------------------------------------------ unknown reset: growing backoff


def exhaust_at_pause_end(quota: QuotaManager, clock: MockClock) -> dt.timedelta:
    """The first call after the pause hits the limit again: returns the new pause length."""
    now = clock()
    until = quota.on_exhausted(QuotaExhausted("You've hit your weekly limit"))
    clock.set(until)
    return until - now


def test_unknown_reset_backoff_doubles_up_to_the_cap() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)

    pauses = [exhaust_at_pause_end(quota, clock) for _ in range(6)]
    assert pauses == [dt.timedelta(hours=h) for h in (1, 2, 4, 8, 8, 8)]
    assert MAX_UNKNOWN_PAUSE == dt.timedelta(hours=8)


def test_backoff_restarts_after_a_quiet_period_or_a_known_reset() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)
    exhaust_at_pause_end(quota, clock)
    exhaust_at_pause_end(quota, clock)

    clock.set(clock() + DEFAULT_PAUSE + dt.timedelta(minutes=1))  # calls went through for a while
    assert exhaust_at_pause_end(quota, clock) == DEFAULT_PAUSE

    exhaust_at_pause_end(quota, clock)  # 2 h
    known = clock() + dt.timedelta(minutes=20)
    assert quota.on_exhausted(QuotaExhausted("session", reset_at=known)) == known
    clock.set(known)
    assert exhaust_at_pause_end(quota, clock) == DEFAULT_PAUSE


def test_concurrent_hits_of_the_same_unknown_limit_do_not_escalate() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)
    barrier = threading.Barrier(8)

    def worker(_: int) -> dt.datetime:
        barrier.wait()
        return quota.on_exhausted(QuotaExhausted("limit"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        ends = set(pool.map(worker, range(8)))

    assert ends == {NOON + DEFAULT_PAUSE}
    assert quota.state().unknown_streak == 1


def test_weekly_limit_with_an_unreadable_reset_costs_few_calls() -> None:
    # Review finding: with a fixed 1 h pause, a weekly reset 5 days away cost 120 failed calls.
    clock = MockClock(NOON)
    quota = QuotaManager(clock)
    real_reset = NOON + dt.timedelta(days=5)
    failed = 0
    while clock() < real_reset:
        failed += 1
        exhaust_at_pause_end(quota, clock)
    assert failed <= 20
    assert clock() - real_reset < MAX_UNKNOWN_PAUSE  # the queue resumes at most one step late


# ------------------------------------------------------------------ restart


def test_pause_and_backoff_survive_a_restart() -> None:
    clock = MockClock(NOON)
    before = QuotaManager(clock)
    exhaust_at_pause_end(before, clock)
    before.on_exhausted(QuotaExhausted("weekly"))  # 2 h pause, step 2
    stored = json.dumps(before.state().to_dict())

    after = QuotaManager(clock, state=QuotaState.from_dict(json.loads(stored)))  # a new process
    assert after.paused_until == clock() + dt.timedelta(hours=2)
    assert not after.can_run(Priority.COMPLIANCE_AND_SCRIPTS)
    clock.set(clock() + dt.timedelta(hours=2))
    assert after.can_run(Priority.COMPLIANCE_AND_SCRIPTS)
    assert exhaust_at_pause_end(after, clock) == dt.timedelta(hours=4)  # the backoff went on


def test_state_is_validated() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        QuotaState(paused_until=dt.datetime(2026, 9, 28, 12))
    with pytest.raises(ValueError):
        QuotaState(unknown_streak=-1)
    assert QuotaState.from_dict({}) == QuotaState()


# ------------------------------------------------------------------ economy and night window


@pytest.mark.parametrize(
    ("now", "scout_runs"),
    [(at(12), False), (at(0, 59), False), (at(1), True), (at(3, 30), True), (at(6, 59), True), (at(7), False)],
)
def test_economy_defers_scout_outside_the_night_window(now: dt.datetime, scout_runs: bool) -> None:
    quota = QuotaManager(MockClock(now), night_window=(1, 7), economy=True)

    assert quota.can_run(Priority.SCOUT) is scout_runs
    assert quota.can_run(Priority.CRITIQUE)
    assert quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)


def test_without_economy_scout_runs_any_time() -> None:
    quota = QuotaManager(MockClock(at(12)), economy=False)
    assert quota.can_run(Priority.SCOUT)
    quota.economy = True  # the operator switches economy on at run time
    assert not quota.can_run(Priority.SCOUT)


@pytest.mark.parametrize(("hour", "inside"), [(22, True), (23, True), (0, True), (5, True), (6, False), (12, False), (21, False)])
def test_night_window_may_wrap_midnight(hour: int, inside: bool) -> None:
    quota = QuotaManager(MockClock(at(hour)), night_window=(22, 6), economy=True)
    assert quota.in_night_window() is inside
    assert quota.can_run(Priority.SCOUT) is inside


def test_night_window_is_read_in_the_clock_zone() -> None:
    # 23:30 UTC is 01:30 in UTC+2: inside a (1, 7) window for a clock that reports UTC+2 time
    quota = QuotaManager(MockClock(at(23, 30).astimezone(PARIS)), economy=True)
    assert quota.can_run(Priority.SCOUT)


def test_next_run_at_for_deferred_scout() -> None:
    clock = MockClock(at(12))
    quota = QuotaManager(clock, night_window=(1, 7), economy=True)

    assert quota.next_run_at(Priority.SCOUT) == at(1, day=29)
    assert quota.next_run_at(Priority.CRITIQUE) == at(12)

    quota.on_exhausted(QuotaExhausted("limit", reset_at=at(3, day=29)))  # reset inside the window
    assert quota.next_run_at(Priority.SCOUT) == at(3, day=29)

    wrap = QuotaManager(MockClock(at(12)), night_window=(22, 6), economy=True)
    assert wrap.next_run_at(Priority.SCOUT) == at(22)


def test_next_run_at_after_a_pause_that_ends_outside_the_window() -> None:
    quota = QuotaManager(MockClock(at(0, 10, tz=PARIS)), night_window=(1, 7), economy=True)
    quota.on_exhausted(QuotaExhausted("limit", reset_at=at(9, tz=PARIS)))
    assert quota.next_run_at(Priority.SCOUT) == at(1, day=29, tz=PARIS)
    assert quota.next_run_at(Priority.CRITIQUE) == at(9, tz=PARIS)


@pytest.mark.parametrize(
    ("economy", "requested", "creative", "expected"),
    [
        (True, "opus", False, ECONOMY_MODEL),
        (True, "claude-opus-5-5", False, ECONOMY_MODEL),
        (True, "Opus", False, ECONOMY_MODEL),
        (True, "opus", True, "opus"),
        (True, "sonnet", False, "sonnet"),
        (True, "haiku", False, "haiku"),
        (False, "opus", False, "opus"),
        (False, "claude-opus-5-5", False, "claude-opus-5-5"),
    ],
)
def test_choose_model(economy: bool, requested: str, creative: bool, expected: str) -> None:
    quota = QuotaManager(MockClock(NOON), economy=economy)
    assert quota.choose_model(requested, creative) == expected
    assert ECONOMY_MODEL == "sonnet"


# ------------------------------------------------------------------ usage accounting


def test_record_accumulates_totals_per_model_and_windows() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock)

    quota.record(usage(10))
    clock.set(NOON + dt.timedelta(hours=4))
    quota.record(usage(1, model="claude-opus-x"))
    clock.set(NOON + dt.timedelta(hours=6))
    quota.record(usage(100))

    assert quota.totals() == UsageTotals(
        calls=3, input_tokens=111, output_tokens=222, cache_read_tokens=333, cache_creation_tokens=444, duration_ms=300
    )
    assert quota.totals("claude-opus-x").calls == 1
    assert quota.totals("claude-sonnet-x").input_tokens == 110
    assert quota.totals("never-used") == UsageTotals()
    # the subscription's rolling 5-hour window: only the last two calls
    last_5h = quota.usage_since(dt.timedelta(hours=5))
    assert (last_5h.calls, last_5h.input_tokens) == (2, 101)


def test_history_is_pruned_but_totals_are_kept() -> None:
    clock = MockClock(NOON)
    quota = QuotaManager(clock, history=dt.timedelta(days=7))
    quota.record(usage(5))
    clock.set(NOON + dt.timedelta(days=8))
    quota.record(usage(7))

    assert quota.usage_since(dt.timedelta(days=30)).input_tokens == 7
    assert quota.totals().input_tokens == 12


def test_concurrent_records_are_all_counted() -> None:
    quota = QuotaManager(MockClock(NOON))
    barrier = threading.Barrier(8)

    def worker(_: int) -> None:
        barrier.wait()
        for _ in range(500):
            quota.record(usage(1))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(8)))

    totals = quota.totals()
    assert totals.calls == 4000 and totals.input_tokens == 4000 and totals.output_tokens == 8000
    assert quota.usage_since(dt.timedelta(hours=1)).calls == 4000


# ------------------------------------------------------------------ configuration errors


@pytest.mark.parametrize("window", [(3, 3), (-1, 5), (1, 25), (24, 2)])
def test_invalid_night_window(window: tuple[int, int]) -> None:
    with pytest.raises(ValueError):
        QuotaManager(MockClock(NOON), night_window=window)


def test_invalid_durations() -> None:
    with pytest.raises(ValueError):
        QuotaManager(MockClock(NOON), default_pause=dt.timedelta(0))
    with pytest.raises(ValueError):
        QuotaManager(MockClock(NOON), default_pause=dt.timedelta(hours=2), max_pause=dt.timedelta(hours=1))
    with pytest.raises(ValueError):
        QuotaManager(MockClock(NOON), history=-dt.timedelta(days=1))


def test_naive_clock_is_refused() -> None:
    quota = QuotaManager(lambda: dt.datetime(2026, 9, 28, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        quota.can_run(Priority.SCOUT)
