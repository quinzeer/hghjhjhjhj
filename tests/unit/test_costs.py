"""SqlCostLedger on SQLite: caps, atomic multi-scope reservations, settle, release, reaping."""

from __future__ import annotations

import datetime as dt
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select

from studio.core.costs import MAX_AMOUNT, ReservationError, SqlCostLedger, reservation_scopes, reservations
from studio.core.db import make_engine
from studio.core.interfaces import BudgetExceeded, Cap, CostLedger, Reservation
from studio.domain import CostEntry, CostKind

T0 = dt.datetime(2026, 9, 28, 8, 0, tzinfo=dt.UTC)
LEASE = dt.timedelta(minutes=1)
EUR = CostKind.EUR
GPU = CostKind.GPU_SECONDS
THREADS = 8


class MockClock:
    """Controllable clock injected into the ledger (test double)."""

    def __init__(self, start: dt.datetime) -> None:
        self.now = start

    def __call__(self) -> dt.datetime:
        return self.now


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(f"sqlite:///{tmp_path / 'ledger.db'}")
    yield eng
    eng.dispose()


@pytest.fixture
def ledger(engine: Engine) -> SqlCostLedger:
    led = SqlCostLedger(engine, clock=MockClock(T0))
    led.create_schema()
    return led


def entry(quantity: float, kind: CostKind = EUR, run_id: str = "run-1", step: str = "a") -> CostEntry:
    return CostEntry(run_id=run_id, step_key=step * 64, kind=kind, quantity=quantity, at=T0)


def reservation_rows(engine: Engine) -> tuple[int, int]:
    with engine.connect() as conn:
        n_res = conn.execute(select(func.count()).select_from(reservations)).scalar()
        n_scopes = conn.execute(select(func.count()).select_from(reservation_scopes)).scalar()
    return int(n_res or 0), int(n_scopes or 0)


def run_concurrently[T](n: int, fn: Callable[[int], T]) -> list[T]:
    """Run fn(i) in n threads released together by a barrier; re-raise the first error."""
    barrier = threading.Barrier(n, timeout=30)

    def task(i: int) -> T:
        barrier.wait()
        return fn(i)

    with ThreadPoolExecutor(max_workers=n) as pool:
        return [f.result(timeout=120) for f in [pool.submit(task, i) for i in range(n)]]


# ------------------------------------------------------------------ caps and reservations


def test_implements_protocol(ledger: SqlCostLedger) -> None:
    assert isinstance(ledger, CostLedger)


def test_an_entry_keeps_its_mock_flag_through_the_ledger(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("video:1", EUR, 10))
    for flag in (False, True):
        r = ledger.reserve(["video:1"], EUR, 1, LEASE)
        ledger.settle(r.id, entry(1).model_copy(update={"mock": flag, "step_key": str(int(flag)) * 64}))
    assert [e.mock for e in ledger.entries("run-1")] == [False, True]


def test_scope_without_cap_is_unlimited(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["video:run-1"], EUR, 1e12, LEASE)
    assert ledger.reserved("video:run-1", EUR) == 1e12
    assert ledger.cap("video:run-1", EUR) is None
    assert res.lease_until == T0 + LEASE


def test_reservation_counts_on_every_scope(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:2026-09-28", "video:run-1", "day:2026-09-28"], EUR, 2.5, LEASE)
    assert res.scopes == ("day:2026-09-28", "video:run-1")
    assert ledger.reserved("day:2026-09-28", EUR) == 2.5
    assert ledger.reserved("video:run-1", EUR) == 2.5
    assert ledger.spent("day:2026-09-28", EUR) == 0


def test_caps_are_per_kind(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    ledger.reserve(["day:1"], EUR, 1000, LEASE)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], GPU, 11, LEASE)


def test_set_cap_replaces_the_limit(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 5))
    ledger.reserve(["day:1"], EUR, 5, LEASE)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.set_cap(Cap("day:1", EUR, 6))
    assert ledger.cap("day:1", EUR) == 6
    ledger.reserve(["day:1"], EUR, 1, LEASE)


def test_budget_exceeded_reserves_nothing_on_any_scope(ledger: SqlCostLedger, engine: Engine) -> None:
    ledger.set_cap(Cap("a:video", EUR, 100))
    ledger.set_cap(Cap("z:month", EUR, 5))  # sorted last: the scopes before it pass their check
    ledger.reserve(["z:month"], EUR, 1, LEASE)
    before = reservation_rows(engine)
    with pytest.raises(BudgetExceeded, match="z:month"):
        ledger.reserve(["a:video", "m:uncapped", "z:month"], EUR, 4.5, LEASE)
    assert reservation_rows(engine) == before
    assert ledger.reserved("a:video", EUR) == 0
    assert ledger.reserved("m:uncapped", EUR) == 0
    assert ledger.reserved("z:month", EUR) == 1


def test_exact_fit_is_accepted_despite_float_rounding(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 0.3))
    ledger.reserve(["day:1"], EUR, 0.1, LEASE)
    ledger.reserve(["day:1"], EUR, 0.2, LEASE)  # 0.1 + 0.2 == 0.30000000000000004 in floats
    assert ledger.reserved("day:1", EUR) == 0.3
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], EUR, 0.001, LEASE)


def test_cap_is_never_exceeded_even_by_a_millionth(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 10))
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], EUR, 10 + 1e-8, LEASE)  # rounded up to 10.000001
    assert ledger.reserve(["day:1"], EUR, 10, LEASE).amount == 10
    assert ledger.reserved("day:1", EUR) == 10
    ledger.set_cap(Cap("day:2", EUR, 1.0000009))  # rounded down to 1.0
    assert ledger.cap("day:2", EUR) == 1.0
    assert ledger.reserve(["day:2"], EUR, 0.1234561, LEASE).amount == 0.123457  # what is actually held
    for _ in range(8):
        ledger.reserve(["day:2"], EUR, 0.1, LEASE)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:2"], EUR, 0.076544, LEASE)
    ledger.reserve(["day:2"], EUR, 0.076543, LEASE)
    assert ledger.reserved("day:2", EUR) == 1.0


def test_amounts_are_bounded(ledger: SqlCostLedger) -> None:
    ledger.reserve(["day:1"], EUR, MAX_AMOUNT, LEASE)
    with pytest.raises(ValueError):
        ledger.reserve(["day:1"], EUR, MAX_AMOUNT * 1.001, LEASE)
    with pytest.raises(ValueError):
        ledger.set_cap(Cap("day:1", EUR, float("inf")))


def test_concurrent_reservations_never_exceed_the_cap(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    ledger.set_cap(Cap("video:1", GPU, 100))

    def worker(_i: int) -> tuple[int, int]:
        ok = refused = 0
        for _ in range(5):
            try:
                ledger.reserve(["day:1", "video:1"], GPU, 1.0, LEASE)
                ok += 1
            except BudgetExceeded:
                refused += 1
        return ok, refused

    results = run_concurrently(THREADS, worker)
    assert sum(ok for ok, _ in results) == 10
    assert sum(refused for _, refused in results) == THREADS * 5 - 10
    assert ledger.reserved("day:1", GPU) == 10
    assert ledger.reserved("video:1", GPU) == 10


def test_input_validation(ledger: SqlCostLedger) -> None:
    for bad_amount in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ledger.reserve(["day:1"], EUR, bad_amount, LEASE)
    with pytest.raises(ValueError):
        ledger.reserve([], EUR, 1, LEASE)
    with pytest.raises(ValueError):
        ledger.reserve([""], EUR, 1, LEASE)
    with pytest.raises(TypeError):
        ledger.reserve("day:1", EUR, 1, LEASE)
    with pytest.raises(ValueError):
        ledger.reserve(["day:1"], EUR, 1, dt.timedelta(0))
    with pytest.raises(ValueError):
        ledger.set_cap(Cap("day:1", EUR, -5))
    with pytest.raises(ValueError):
        ledger.set_cap(Cap("", EUR, 5))
    with pytest.raises(ReservationError):
        ledger.status("no-such-reservation")


def test_default_clock_is_utc_now(engine: Engine) -> None:
    plain = SqlCostLedger(engine)
    plain.create_schema()
    before = dt.datetime.now(dt.UTC)
    res = plain.reserve(["day:1"], EUR, 1, LEASE)
    assert before + LEASE <= res.lease_until <= dt.datetime.now(dt.UTC) + LEASE


def test_create_schema_is_idempotent(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 5))
    ledger.reserve(["day:1"], EUR, 2, LEASE)
    ledger.create_schema()
    assert ledger.cap("day:1", EUR) == 5
    assert ledger.reserved("day:1", EUR) == 2


def test_concurrent_create_schema_on_a_fresh_database(engine: Engine) -> None:
    run_concurrently(THREADS, lambda _i: SqlCostLedger(engine).create_schema())
    ledger = SqlCostLedger(engine)
    ledger.set_cap(Cap("day:1", EUR, 5))
    assert ledger.reserve(["day:1"], EUR, 5, LEASE).amount == 5


# ------------------------------------------------------------------ settle and release


def test_settle_replaces_the_reservation_even_above_the_estimate(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 4))
    res = ledger.reserve(["day:1", "video:1"], EUR, 3, LEASE)
    measured = entry(5.0)
    ledger.settle(res.id, measured)
    assert ledger.status(res.id) == "settled"
    for scope in ("day:1", "video:1"):
        assert ledger.reserved(scope, EUR) == 0
        assert ledger.spent(scope, EUR) == 5.0
    assert ledger.entries("run-1") == [measured]
    # spent (5) is now above the cap (4): nothing more can be reserved on that scope
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], EUR, 0.5, LEASE)


def test_settle_is_rejected_twice_after_release_or_for_another_kind(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], EUR, 1, LEASE)
    with pytest.raises(ValueError, match="kind"):
        ledger.settle(res.id, entry(1, kind=GPU))
    ledger.settle(res.id, entry(1))
    with pytest.raises(ReservationError):
        ledger.settle(res.id, entry(1))
    released = ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.release(released.id)
    with pytest.raises(ReservationError):
        ledger.settle(released.id, entry(1))
    with pytest.raises(ReservationError):
        ledger.settle("no-such-reservation", entry(1))
    assert ledger.spent("day:1", EUR) == 1


def test_release_gives_the_budget_back(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", EUR, 5))
    res = ledger.reserve(["day:1"], EUR, 5, LEASE)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.release(res.id)
    ledger.release(res.id)  # idempotent
    assert ledger.status(res.id) == "released"
    assert ledger.reserved("day:1", EUR) == 0
    assert ledger.spent("day:1", EUR) == 0
    again = ledger.reserve(["day:1"], EUR, 5, LEASE)
    ledger.settle(again.id, entry(5))
    with pytest.raises(ReservationError):
        ledger.release(again.id)
    with pytest.raises(ReservationError):
        ledger.release("no-such-reservation")


def test_settle_refuses_a_naive_entry_time(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], EUR, 1, LEASE)
    naive = CostEntry(run_id="run-1", step_key="a" * 64, kind=EUR, quantity=1, at=dt.datetime(2026, 9, 28, 8, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        ledger.settle(res.id, naive)
    assert ledger.status(res.id) == "active"
    assert ledger.entries() == []
    paris = dt.timezone(dt.timedelta(hours=2))
    aware = naive.model_copy(update={"at": dt.datetime(2026, 9, 28, 10, 0, tzinfo=paris)})
    ledger.settle(res.id, aware)
    assert ledger.entries() == [aware]  # the same instant, read back in UTC


def test_entries_keep_the_measured_quantity_and_spent_counts_millionths(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 1, LEASE)
    measured = entry(12.3456789012, kind=GPU)
    ledger.settle(res.id, measured)
    assert ledger.entries() == [measured]
    assert ledger.spent("day:1", GPU) == 12.345679


def test_concurrent_double_settle_records_the_cost_once(ledger: SqlCostLedger) -> None:
    rounds = 10
    for _ in range(rounds):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def settle(_k: int, rid: str = res.id) -> str:
            try:
                ledger.settle(rid, entry(1.5, kind=GPU))
            except ReservationError:
                return "refused"
            return "settled"

        assert sorted(run_concurrently(2, settle)) == ["refused", "settled"]
    assert len(ledger.entries()) == rounds
    assert ledger.spent("day:1", GPU) == 1.5 * rounds


def test_concurrent_settle_and_release_leave_a_consistent_state(ledger: SqlCostLedger) -> None:
    for i in range(10):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def race(k: int, rid: str = res.id, run: str = f"run-{i}") -> str:
            try:
                if k == 0:
                    ledger.settle(rid, entry(2, kind=GPU, run_id=run))
                else:
                    ledger.release(rid)
            except ReservationError:
                return "refused"
            return "done"

        settle_outcome, release_outcome = run_concurrently(2, race)
        recorded = ledger.entries(f"run-{i}")
        if ledger.status(res.id) == "settled":
            assert (settle_outcome, len(recorded)) == ("done", 1)
            assert release_outcome == "refused"  # releasing a settled reservation is refused
        else:
            assert ledger.status(res.id) == "released"
            assert (settle_outcome, release_outcome, recorded) == ("refused", "done", [])
    assert ledger.reserved("day:1", GPU) == 0
    assert ledger.spent("day:1", GPU) == 2 * len(ledger.entries())


def test_entries_are_filtered_by_run(ledger: SqlCostLedger) -> None:
    for run in ("run-1", "run-2", "run-1"):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)
        ledger.settle(res.id, entry(1, kind=GPU, run_id=run))
    assert [e.run_id for e in ledger.entries("run-1")] == ["run-1", "run-1"]
    assert [e.run_id for e in ledger.entries()] == ["run-1", "run-2", "run-1"]
    assert ledger.entries("run-3") == []


# ------------------------------------------------------------------ reaping


def test_reap_expired_frees_the_budget_of_a_crashed_worker(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 5))
    crashed = ledger.reserve(["day:1"], GPU, 5, LEASE)  # the worker dies: no settle, no release
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], GPU, 1, dt.timedelta(hours=1))
    assert ledger.reap_expired(T0 + dt.timedelta(seconds=30)) == []  # lease still running
    assert ledger.reserved("day:1", GPU) == 5

    assert ledger.reap_expired(T0 + LEASE + dt.timedelta(seconds=1)) == [crashed.id]
    assert ledger.status(crashed.id) == "reaped"
    assert ledger.reserved("day:1", GPU) == 0
    assert ledger.reap_expired(T0 + dt.timedelta(hours=2)) == []  # already reaped
    ledger.reserve(["day:1"], GPU, 5, dt.timedelta(hours=1))


def test_reap_keeps_a_lease_that_ends_exactly_now(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 1, LEASE)
    assert ledger.reap_expired(T0 + LEASE) == []  # valid up to and including lease_until
    assert ledger.reap_expired(T0 + LEASE + dt.timedelta(microseconds=1)) == [res.id]


def test_release_of_a_reaped_reservation_keeps_it_reaped(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 2, LEASE)
    assert ledger.reap_expired(T0 + dt.timedelta(minutes=5)) == [res.id]
    ledger.release(res.id)  # a no-op: the reaper already gave the budget back
    assert ledger.status(res.id) == "reaped"
    ledger.settle(res.id, entry(3, kind=GPU))  # the worker was alive after all
    assert ledger.spent("day:1", GPU) == 3


def test_reap_ignores_settled_and_released_reservations(ledger: SqlCostLedger) -> None:
    settled = ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.settle(settled.id, entry(1))
    released = ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.release(released.id)
    expired = ledger.reserve(["day:1"], EUR, 1, LEASE)
    assert ledger.reap_expired(T0 + dt.timedelta(days=1)) == [expired.id]
    assert (ledger.status(settled.id), ledger.status(released.id)) == ("settled", "released")


def test_reap_compares_instants_whatever_the_time_zone(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], EUR, 1, LEASE)  # lease until 08:01 UTC
    paris = dt.timezone(dt.timedelta(hours=2))
    assert ledger.reap_expired(dt.datetime(2026, 9, 28, 10, 0, 30, tzinfo=paris)) == []  # 08:00:30 UTC
    assert ledger.reap_expired(dt.datetime(2026, 9, 28, 10, 1, 30, tzinfo=paris)) == [res.id]


def test_late_settle_after_reap_still_records_the_cost(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 2, LEASE)
    assert ledger.reap_expired(T0 + dt.timedelta(minutes=5)) == [res.id]
    ledger.settle(res.id, entry(3, kind=GPU))  # the worker was slow, not dead: its cost is real
    assert ledger.status(res.id) == "settled"
    assert ledger.spent("day:1", GPU) == 3
    assert ledger.reserved("day:1", GPU) == 0


def test_concurrent_settle_and_reap_record_the_cost_once(ledger: SqlCostLedger) -> None:
    rounds = 10
    late = T0 + dt.timedelta(minutes=5)
    for i in range(rounds):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def race(k: int, rid: str = res.id) -> None:
            if k == 0:
                ledger.settle(rid, entry(2, kind=GPU))
            else:
                ledger.reap_expired(late)

        run_concurrently(2, race)
        assert ledger.status(res.id) == "settled"
        assert ledger.spent("day:1", GPU) == 2 * (i + 1)
    assert ledger.reserved("day:1", GPU) == 0
    assert len(ledger.entries("run-1")) == rounds


# ------------------------------------------------------------------ renewing a lease


def test_renewed_lease_is_not_reaped(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 5, LEASE)
    renewed = ledger.renew(res.id, T0 + dt.timedelta(hours=1))  # heartbeat of a long render
    assert renewed == Reservation(res.id, res.scopes, GPU, 5, T0 + dt.timedelta(hours=1))
    assert ledger.reap_expired(T0 + dt.timedelta(minutes=5)) == []
    assert ledger.reserved("day:1", GPU) == 5
    assert ledger.renew(res.id, T0 + dt.timedelta(minutes=30)).lease_until == T0 + dt.timedelta(hours=1)  # never shortened
    assert ledger.reap_expired(T0 + dt.timedelta(hours=1, seconds=1)) == [res.id]


def test_renew_takes_back_a_reaped_reservation_only_if_the_cap_allows(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 3600))
    slow = ledger.reserve(["day:1"], GPU, 3600, dt.timedelta(hours=1))  # a 70-minute render on a one-hour lease
    assert ledger.reap_expired(T0 + dt.timedelta(minutes=61)) == [slow.id]
    other = ledger.reserve(["day:1"], GPU, 3600, dt.timedelta(hours=2))  # the budget went to another job
    with pytest.raises(BudgetExceeded):
        ledger.renew(slow.id, T0 + dt.timedelta(hours=3))  # hard stop: the slow job must not go on
    assert ledger.status(slow.id) == "reaped"
    assert ledger.reserved("day:1", GPU) == 3600
    ledger.release(other.id)
    assert ledger.renew(slow.id, T0 + dt.timedelta(hours=3)).lease_until == T0 + dt.timedelta(hours=3)
    assert ledger.status(slow.id) == "active"
    assert ledger.reserved("day:1", GPU) == 3600
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], GPU, 1, LEASE)


def test_renew_refuses_finished_unknown_and_past_leases(ledger: SqlCostLedger) -> None:
    settled = ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.settle(settled.id, entry(1))
    released = ledger.reserve(["day:1"], EUR, 1, LEASE)
    ledger.release(released.id)
    later = T0 + dt.timedelta(hours=1)
    for finished in (settled, released):
        with pytest.raises(ReservationError):
            ledger.renew(finished.id, later)
    with pytest.raises(ReservationError):
        ledger.renew("no-such-reservation", later)
    live = ledger.reserve(["day:1"], EUR, 1, LEASE)
    with pytest.raises(ValueError, match="future"):
        ledger.renew(live.id, T0)
    assert ledger.renew(live.id, later.replace(tzinfo=None)).lease_until == later  # naive is taken as UTC


def test_renew_racing_the_reaper_keeps_the_reservation_once(ledger: SqlCostLedger) -> None:
    late = T0 + dt.timedelta(minutes=5)
    for _ in range(10):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def race(k: int, rid: str = res.id) -> None:
            if k == 0:
                ledger.renew(rid, T0 + dt.timedelta(hours=1))
            else:
                ledger.reap_expired(late)

        run_concurrently(2, race)
        assert ledger.status(res.id) == "active"  # renewed first, or reaped then taken back
        assert ledger.reserved("day:1", GPU) == 1
        ledger.release(res.id)


def test_reaped_reservations_taken_back_concurrently_never_exceed_the_cap(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    reaped = [ledger.reserve(["day:1"], GPU, 1, LEASE) for _ in range(6)]
    assert len(ledger.reap_expired(T0 + dt.timedelta(minutes=5))) == 6

    def worker(i: int) -> int:
        if i < len(reaped):
            try:
                ledger.renew(reaped[i].id, T0 + dt.timedelta(hours=1))
            except BudgetExceeded:
                return 0
            return 1
        accepted = 0
        for _ in range(5):
            try:
                ledger.reserve(["day:1"], GPU, 1, LEASE)
                accepted += 1
            except BudgetExceeded:
                pass
        return accepted

    assert sum(run_concurrently(THREADS, worker)) == 10  # 16 asked for
    assert ledger.reserved("day:1", GPU) == 10
