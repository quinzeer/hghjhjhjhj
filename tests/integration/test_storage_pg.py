"""Artifact store and cost ledger on Postgres: row locks, first-write-wins and caps under real concurrency.

Each test runs in its own schema (search_path), so the database can be shared with other test modules. The
schema name carries the creating process id: schemas left behind by a killed run are dropped by the next one.
Every connection has a lock timeout, so a regression that makes a test wait on a lock fails instead of hanging.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import Connection, Engine, event, func, insert, make_url, select, text

from studio.core.artifacts import LocalArtifactStore, artifacts, pins, step_outputs
from studio.core.costs import ReservationError, SqlCostLedger, caps, reservation_scopes, reservations
from studio.core.db import make_engine
from studio.core.hashing import bytes_key
from studio.core.interfaces import ArtifactMissing, BudgetExceeded, Cap
from studio.domain import CostEntry, CostKind

PG_URL = os.environ.get("STUDIO_TEST_PG_URL", "")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not PG_URL, reason="STUDIO_TEST_PG_URL is not set"),
]

T0 = dt.datetime(2026, 9, 1, 12, 0, tzinfo=dt.UTC)
LEASE = dt.timedelta(minutes=1)
GPU = CostKind.GPU_SECONDS
THREADS = 8
LOCK_TIMEOUT = "10s"
SCHEMA_PREFIX = "test_storage_"
REPO_ROOT = Path(__file__).resolve().parents[2]


class MockClock:
    """Controllable clock injected into the store and the ledger (test double)."""

    def __init__(self, start: dt.datetime) -> None:
        self.now = start

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, delta: dt.timedelta) -> None:
        self.now += delta


def pg_url(search_path: str | None = None) -> str:
    options = f"-c lock_timeout={LOCK_TIMEOUT}" + (f" -c search_path={search_path}" if search_path else "")
    return make_url(PG_URL).update_query_dict({"options": options}).render_as_string(hide_password=False)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def drop_orphan_schemas(admin: Engine) -> list[str]:
    """Drop the schemas of this module whose creating process is gone (and those of the older, pid-less
    naming). Process ids are local: the test database is assumed not to be shared across hosts."""
    dropped = []
    with admin.begin() as conn:
        names = conn.execute(text("SELECT nspname FROM pg_namespace WHERE starts_with(nspname, :p)"), {"p": SCHEMA_PREFIX})
        for name in names.scalars().all():
            match = re.fullmatch(rf"{SCHEMA_PREFIX}(?:(\d+)_)?[0-9a-f]{{12}}", name)
            if match and (match.group(1) is None or not process_alive(int(match.group(1)))):
                conn.execute(text(f'DROP SCHEMA "{name}" CASCADE'))
                dropped.append(name)
    return dropped


@pytest.fixture(scope="module")
def admin() -> Iterator[Engine]:
    eng = make_engine(pg_url())
    drop_orphan_schemas(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def pg(admin: Engine) -> Iterator[Engine]:
    schema = f"{SCHEMA_PREFIX}{os.getpid()}_{uuid.uuid4().hex[:12]}"
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    eng = make_engine(pg_url(schema))
    try:
        yield eng
    finally:
        eng.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


@pytest.fixture
def clock() -> MockClock:
    return MockClock(T0)


@pytest.fixture
def store(tmp_path: Path, pg: Engine, clock: MockClock) -> LocalArtifactStore:
    s = LocalArtifactStore(tmp_path / "store", pg, clock=clock)
    s.create_schema()
    return s


@pytest.fixture
def ledger(pg: Engine, clock: MockClock) -> SqlCostLedger:
    led = SqlCostLedger(pg, clock=clock)
    led.create_schema()
    return led


def put_text(store: LocalArtifactStore, value: str) -> str:
    return store.put_bytes(value.encode(), kind="text", media_type="text/plain").key


def entry(quantity: float, run_id: str = "run-1") -> CostEntry:
    return CostEntry(run_id=run_id, step_key="a" * 64, kind=GPU, quantity=quantity, at=T0)


def run_concurrently[T](n: int, fn: Callable[[int], T]) -> list[T]:
    """Run fn(i) in n threads released together by a barrier; re-raise the first error."""
    barrier = threading.Barrier(n, timeout=30)

    def task(i: int) -> T:
        barrier.wait()
        return fn(i)

    with ThreadPoolExecutor(max_workers=n) as pool:
        return [f.result(timeout=120) for f in [pool.submit(task, i) for i in range(n)]]


def wait_for_backend(admin: Engine, needle: str, *, lock_wait: bool, timeout: float = 10.0) -> bool:
    """Wait until another backend of this database runs a query that contains `needle` (and, with
    `lock_wait`, waits on a lock while doing so). False on timeout."""
    query = text(
        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() "
        "AND state = 'active' AND query ILIKE :needle AND (NOT :lock_wait OR wait_event_type = 'Lock')"
    )
    deadline = time.monotonic() + timeout
    with admin.connect() as conn:
        while time.monotonic() < deadline:
            found = conn.execute(query, {"needle": f"%{needle}%", "lock_wait": lock_wait}).scalar()
            conn.rollback()  # pg_stat_activity is a snapshot taken once per transaction
            if found:
                return True
            time.sleep(0.001)
    return False


def wait_until_lock_wait(admin: Engine, needle: str, timeout: float = 10.0) -> None:
    if not wait_for_backend(admin, needle, lock_wait=True, timeout=timeout):
        raise AssertionError(f"no backend waited on a lock for a query containing {needle!r}")


def in_background[T](fn: Callable[[], T]) -> tuple[ThreadPoolExecutor, Future[T]]:
    pool = ThreadPoolExecutor(max_workers=1)
    return pool, pool.submit(fn)


# Child process: runs a purge and SIGKILLs itself right after the first file is unlinked, before the commit.
PURGE_KILLED_AFTER_FIRST_UNLINK = """
import datetime as dt, os, signal, sys
from pathlib import Path
from studio.core.artifacts import LocalArtifactStore
from studio.core.db import make_engine

url, root, now, older_than_s = sys.argv[1:5]
store = LocalArtifactStore(Path(root), make_engine(url), clock=lambda: dt.datetime.fromisoformat(now))
real_unlink = Path.unlink

def unlink_then_die_mock(self, missing_ok=False):
    real_unlink(self, missing_ok=missing_ok)
    os.kill(os.getpid(), signal.SIGKILL)

Path.unlink = unlink_then_die_mock
store.purge_unpinned(dt.timedelta(seconds=float(older_than_s)))
sys.exit("the purge ran to completion: it was not killed")
"""


def purge_killed_after_first_unlink(
    engine: Engine, store: LocalArtifactStore, now: dt.datetime, older_than: dt.timedelta
) -> None:
    url = engine.url.render_as_string(hide_password=False)
    args = [url, str(store.root), now.isoformat(), str(older_than.total_seconds())]
    proc = subprocess.run(
        [sys.executable, "-c", PURGE_KILLED_AFTER_FIRST_UNLINK, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == -signal.SIGKILL, proc.stderr


def old_rows(keys: Sequence[str]) -> list[dict[str, object]]:
    return [{"key": k, "kind": "text", "media_type": "text/plain", "size_bytes": 1, "created_at": T0} for k in keys]


def test_orphan_schemas_of_dead_processes_are_dropped(admin: Engine) -> None:
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()  # reaped: no process has this pid any more
    dead = f"{SCHEMA_PREFIX}{child.pid}_{uuid.uuid4().hex[:12]}"
    legacy = f"{SCHEMA_PREFIX}{uuid.uuid4().hex[:12]}"
    live = f"{SCHEMA_PREFIX}{os.getpid()}_{uuid.uuid4().hex[:12]}"
    with admin.begin() as conn:
        for name in (dead, legacy, live):
            conn.execute(text(f'CREATE SCHEMA "{name}"'))
    try:
        dropped = drop_orphan_schemas(admin)
        assert dead in dropped and legacy in dropped and live not in dropped
    finally:
        with admin.begin() as conn:
            for name in (dead, legacy, live):
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{name}" CASCADE'))


# ------------------------------------------------------------------ artifact store


def test_pg_schema_is_idempotent_and_puts_deduplicate(store: LocalArtifactStore, pg: Engine) -> None:
    store.create_schema()
    data = b"rendered frame" * 1000
    keys = run_concurrently(THREADS, lambda _i: store.put_bytes(data, kind="image", media_type="image/png").key)
    assert set(keys) == {bytes_key(data)}
    with pg.connect() as conn:
        assert conn.execute(select(func.count()).select_from(artifacts)).scalar() == 1
    assert [p.name for p in store.cas.rglob("*") if p.is_file()] == [bytes_key(data)]


def test_pg_concurrent_commits_all_get_the_same_winner(store: LocalArtifactStore) -> None:
    for round_ in range(5):
        step = f"{round_:064x}"
        candidates = [put_text(store, f"round {round_} producer {i}") for i in range(THREADS)]
        results = run_concurrently(THREADS, lambda i, c=candidates, s=step: store.commit_step_output(s, c[i]))
        assert len(set(results)) == 1, results
        assert results[0] in candidates
        assert store.step_output(step) == results[0]


def test_pg_purge_spares_pinned_and_clears_step_links(store: LocalArtifactStore, clock: MockClock) -> None:
    old_unpinned = put_text(store, "old draft")
    old_pinned = put_text(store, "old but in a manifest")
    store.commit_step_output("1" * 64, old_unpinned)
    store.commit_step_output("2" * 64, old_pinned)
    store.pin(old_pinned, "run-1")
    clock.advance(dt.timedelta(days=10))
    recent = put_text(store, "fresh draft")

    assert store.purge_unpinned(dt.timedelta(days=7)) == [old_unpinned]
    assert not store.has(old_unpinned)
    assert store.step_output("1" * 64) is None
    assert store.has(old_pinned) and store.step_output("2" * 64) == old_pinned
    assert store.has(recent)
    store.unpin(old_pinned, "run-1")
    assert store.purge_unpinned(dt.timedelta(days=7)) == [old_pinned]
    assert store.step_output("2" * 64) is None


def test_pg_purge_skips_an_artifact_whose_pin_is_in_flight(store: LocalArtifactStore, pg: Engine, clock: MockClock) -> None:
    key = put_text(store, "about to be referenced by a manifest")
    clock.advance(dt.timedelta(days=10))
    with pg.connect() as other:
        tx = other.begin()
        other.execute(insert(pins).values(artifact_key=key, owner="run-late"))  # holds a key-share lock
        pool, purge = in_background(lambda: store.purge_unpinned(dt.timedelta(days=7)))
        try:
            assert purge.result(timeout=10) == []  # skipped the locked row instead of waiting or deleting it
        finally:
            tx.commit()
            pool.shutdown()
    assert store.pinned_by(key) == ["run-late"]
    assert store.has(key)
    assert store.purge_unpinned(dt.timedelta(days=7)) == []


@pytest.mark.parametrize("operation", ["commit_step_output", "pin"])
def test_pg_reference_racing_a_purge_raises_missing(store: LocalArtifactStore, pg: Engine, admin: Engine, operation: str) -> None:
    key = put_text(store, "being purged")
    with pg.connect() as purger:
        tx = purger.begin()
        purger.execute(select(artifacts.c.key).where(artifacts.c.key == key).with_for_update())
        purger.execute(artifacts.delete().where(artifacts.c.key == key))
        if operation == "pin":
            pool, fut = in_background(lambda: store.pin(key, "run-1"))
            needle = "INSERT INTO pins"
        else:
            pool, fut = in_background(lambda: store.commit_step_output("3" * 64, key))
            needle = "INSERT INTO step_outputs"
        try:
            wait_until_lock_wait(admin, needle)  # its existence check passed; the foreign key waits on our lock
        finally:
            tx.commit()
        with pytest.raises(ArtifactMissing):
            fut.result(timeout=10)
        pool.shutdown()
    assert store.step_output("3" * 64) is None
    assert store.pinned_by(key) == []


def test_pg_commit_retries_when_the_winner_is_purged_mid_transaction(store: LocalArtifactStore, pg: Engine) -> None:
    step = "4" * 64
    winner, late = put_text(store, "first producer"), put_text(store, "second producer")
    assert store.commit_step_output(step, winner) == winner
    fired: list[str] = []

    def purge_before_read_back_mock(_conn: object, _cursor: object, statement: str, *_args: object) -> None:
        # Right after our INSERT ... DO NOTHING saw the winner, another session purges it and commits.
        if not fired and statement.startswith("SELECT step_outputs.artifact_key"):
            fired.append(statement)
            with pg.begin() as other:
                other.execute(step_outputs.delete().where(step_outputs.c.artifact_key == winner))
                other.execute(artifacts.delete().where(artifacts.c.key == winner))

    event.listen(pg, "before_cursor_execute", purge_before_read_back_mock)
    try:
        assert store.commit_step_output(step, late) == late  # re-inserted on the next attempt
    finally:
        event.remove(pg, "before_cursor_execute", purge_before_read_back_mock)
    assert fired
    assert store.step_output(step) == late


def test_pg_concurrent_create_schema_on_a_fresh_database(pg: Engine, tmp_path: Path) -> None:
    def start(i: int) -> None:
        LocalArtifactStore(tmp_path / f"worker-{i}", pg).create_schema()
        SqlCostLedger(pg).create_schema()

    run_concurrently(THREADS, start)
    store = LocalArtifactStore(tmp_path / "worker-0", pg)
    key = put_text(store, "after a concurrent start")
    assert store.commit_step_output("a" * 64, key) == key
    ledger = SqlCostLedger(pg)
    ledger.set_cap(Cap("day:1", GPU, 1))
    assert ledger.reserve(["day:1"], GPU, 1, LEASE).amount == 1


def test_pg_storing_the_same_bytes_again_restarts_the_retention_age(store: LocalArtifactStore, clock: MockClock) -> None:
    key = put_text(store, "deterministic render")
    clock.advance(dt.timedelta(days=10))
    assert put_text(store, "deterministic render") == key
    assert store.purge_unpinned(dt.timedelta(days=7)) == []
    clock.now = T0  # a lagging clock never moves the age backwards
    put_text(store, "deterministic render")
    clock.now = T0 + dt.timedelta(days=17)
    assert store.purge_unpinned(dt.timedelta(days=7)) == []
    clock.advance(dt.timedelta(microseconds=1))
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]


def test_pg_put_racing_a_purge_returns_a_readable_artifact(
    store: LocalArtifactStore, pg: Engine, admin: Engine, clock: MockClock
) -> None:
    data = b"re-rendered while the retention job runs"
    key = store.put_bytes(data, kind="text", media_type="text/plain").key
    clock.advance(dt.timedelta(days=10))
    with pg.connect() as purger:
        tx = purger.begin()  # a purge that has selected and locked this old, unpinned artifact
        purger.execute(select(artifacts.c.key).where(artifacts.c.key == key).with_for_update(skip_locked=True))
        pool, put = in_background(lambda: store.put_bytes(data, kind="text", media_type="text/plain"))
        try:
            wait_until_lock_wait(admin, "INSERT INTO artifacts")  # the put waits for the purge's row lock...
            purger.execute(artifacts.delete().where(artifacts.c.key == key))
            store.path_for(key).unlink()  # ...while the purge deletes the row and the file
        finally:
            tx.commit()
        stored = put.result(timeout=10)
        pool.shutdown()
    assert stored.key == key
    assert store.has(key) and stored.path.read_bytes() == data  # what the put returned is there
    assert store.purge_unpinned(dt.timedelta(days=7)) == []  # stored again now: recent


def test_pg_purge_killed_between_unlink_and_commit_then_replan_recomputes(
    store: LocalArtifactStore, pg: Engine, clock: MockClock
) -> None:
    step = "7" * 64
    old = store.put_bytes(b"take generated on day 0", kind="text", media_type="text/plain")
    assert store.commit_step_output(step, old.key) == old.key
    clock.advance(dt.timedelta(days=10))

    purge_killed_after_first_unlink(pg, store, clock.now, dt.timedelta(days=7))

    assert not old.path.exists()  # the file went before the kill...
    with pg.connect() as conn:  # ...but the server rolled the transaction back
        assert conn.execute(select(func.count()).select_from(artifacts)).scalar() == 1
    assert not store.has(old.key)
    assert store.step_output(step) is None
    new = store.put_bytes(b"take regenerated on day 10", kind="text", media_type="text/plain")
    assert store.commit_step_output(step, new.key) == new.key
    assert store.step_output(step) == new.key
    assert store.purge_unpinned(dt.timedelta(days=7)) == [old.key]
    assert store.step_output(step) == new.key


def test_pg_concurrent_commits_rebind_an_unreadable_output_to_one_winner(store: LocalArtifactStore) -> None:
    for round_ in range(5):
        step = f"{round_ + 100:064x}"
        lost = store.put_bytes(f"lost take {round_}".encode(), kind="text", media_type="text/plain")
        store.commit_step_output(step, lost.key)
        lost.path.unlink()
        candidates = [put_text(store, f"round {round_} replanner {i}") for i in range(THREADS)]
        results = run_concurrently(THREADS, lambda i, c=candidates, s=step: store.commit_step_output(s, c[i]))
        assert len(set(results)) == 1, results
        assert results[0] in candidates
        assert store.step_output(step) == results[0]


def test_pg_pin_committed_during_the_purge_scan_is_spared(
    store: LocalArtifactStore, pg: Engine, admin: Engine, clock: MockClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = "f" * 64  # sorts last: the scan locks it after every other candidate
    fillers = [f"{i:064x}" for i in range(30_000)]
    real_pinned_among = LocalArtifactStore._pinned_among
    rechecks: list[set[str]] = []

    def pinned_among_spy_mock(conn: Connection, keys: Sequence[str]) -> set[str]:
        found = real_pinned_among(conn, keys)
        rechecks.append(found)
        return found

    monkeypatch.setattr(LocalArtifactStore, "_pinned_among", staticmethod(pinned_among_spy_mock))
    clock.advance(dt.timedelta(days=10))
    for _attempt in range(5):
        with pg.begin() as conn:
            conn.execute(insert(artifacts), old_rows([*fillers, target]))
        with pg.connect() as pinner:
            tx = pinner.begin()
            pinner.execute(insert(pins).values(artifact_key=target, owner="run-late"))  # not committed yet
            pool, purge = in_background(lambda: store.purge_unpinned(dt.timedelta(days=7)))
            try:
                wait_for_backend(admin, "SKIP LOCKED", lock_wait=False)  # the scan runs: its snapshot misses the pin
            finally:
                tx.commit()  # committed before the scan reaches (and would skip) the target
            purged = purge.result(timeout=60)  # a pinned row deleted would fail on the foreign key
            pool.shutdown()
        assert purged == fillers
        assert store.pinned_by(target) == ["run-late"]
        if target in rechecks[-1]:
            return  # the scan selected the pinned target and the re-check spared it
        store.unpin(target, "run-late")  # the pin landed outside the window: try again
        with pg.begin() as conn:
            conn.execute(artifacts.delete().where(artifacts.c.key == target))
    pytest.fail("the pin never landed between the purge's snapshot and its lock on the target")


# ------------------------------------------------------------------ cost ledger


def test_pg_concurrent_reservations_never_exceed_the_cap(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    ledger.set_cap(Cap("video:1", GPU, 100))

    def worker(_i: int) -> int:
        ok = 0
        for _ in range(5):
            try:
                ledger.reserve(["video:1", "day:1"], GPU, 1.0, LEASE)
                ok += 1
            except BudgetExceeded:
                pass
        return ok

    assert sum(run_concurrently(THREADS, worker)) == 10
    assert ledger.reserved("day:1", GPU) == 10
    assert ledger.reserved("video:1", GPU) == 10


def test_pg_reserve_waits_for_a_concurrent_reservation_then_sees_it(ledger: SqlCostLedger, pg: Engine, admin: Engine) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    with pg.connect() as other:
        tx = other.begin()  # another reserver, midway through its transaction
        other.execute(select(caps).where(caps.c.scope == "day:1").with_for_update())
        other.execute(
            insert(reservations).values(
                id="other", kind=GPU.value, amount_micro=8_000_000, lease_until=T0 + LEASE, status="active"
            )
        )
        other.execute(insert(reservation_scopes).values(reservation_id="other", scope="day:1"))
        pool, fut = in_background(lambda: ledger.reserve(["day:1"], GPU, 5.0, LEASE))
        try:
            wait_until_lock_wait(admin, "FROM caps")
        finally:
            tx.commit()
        with pytest.raises(BudgetExceeded):  # 8 committed + 5 > 10: the waiter re-read after the lock
            fut.result(timeout=10)
        pool.shutdown()
    assert ledger.reserved("day:1", GPU) == 8


def test_pg_opposite_scope_orders_do_not_deadlock(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("a:video", GPU, 1000))
    ledger.set_cap(Cap("b:day", GPU, 1000))

    def worker(i: int) -> int:
        scopes = ["a:video", "b:day"] if i % 2 else ["b:day", "a:video"]
        for _ in range(20):
            res = ledger.reserve(scopes, GPU, 1.0, LEASE)
            ledger.settle(res.id, entry(1.0))
        return 20

    assert sum(run_concurrently(THREADS, worker)) == THREADS * 20
    assert ledger.spent("a:video", GPU) == ledger.spent("b:day", GPU) == THREADS * 20
    assert ledger.reserved("a:video", GPU) == 0


def test_pg_budget_exceeded_reserves_nothing_on_any_scope(ledger: SqlCostLedger, pg: Engine) -> None:
    ledger.set_cap(Cap("a:video", GPU, 100))
    ledger.set_cap(Cap("z:month", GPU, 5))
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["a:video", "m:uncapped", "z:month"], GPU, 6, LEASE)
    with pg.connect() as conn:
        assert conn.execute(select(func.count()).select_from(reservations)).scalar() == 0
        assert conn.execute(select(func.count()).select_from(reservation_scopes)).scalar() == 0
    assert ledger.reserved("a:video", GPU) == 0


def test_pg_settle_release_and_reap(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    settled = ledger.reserve(["day:1"], GPU, 3, LEASE)
    ledger.settle(settled.id, entry(4.5))  # measured above the estimate
    released = ledger.reserve(["day:1"], GPU, 2, LEASE)
    ledger.release(released.id)
    crashed = ledger.reserve(["day:1"], GPU, 5.5, LEASE)  # never settled: the worker died
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], GPU, 1, LEASE)
    assert ledger.reap_expired(T0 + dt.timedelta(seconds=30)) == []
    assert ledger.reap_expired(T0 + dt.timedelta(minutes=2)) == [crashed.id]
    assert ledger.spent("day:1", GPU) == 4.5
    assert ledger.reserved("day:1", GPU) == 0
    assert [ledger.status(r.id) for r in (settled, released, crashed)] == ["settled", "released", "reaped"]
    ledger.reserve(["day:1"], GPU, 5.5, LEASE)
    assert ledger.entries("run-1") == [entry(4.5)]


def test_pg_concurrent_settle_and_reap_record_the_cost_once(ledger: SqlCostLedger) -> None:
    late = T0 + dt.timedelta(minutes=5)
    for i in range(10):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def race(k: int, rid: str = res.id) -> None:
            if k == 0:
                ledger.settle(rid, entry(2))
            else:
                ledger.reap_expired(late)

        run_concurrently(2, race)
        assert ledger.status(res.id) == "settled"
        assert ledger.spent("day:1", GPU) == 2 * (i + 1)
    assert ledger.reserved("day:1", GPU) == 0


def test_pg_cap_is_exact_to_the_millionth(ledger: SqlCostLedger) -> None:
    ledger.set_cap(Cap("day:1", GPU, 0.3))
    first = ledger.reserve(["day:1"], GPU, 0.1, LEASE)
    ledger.reserve(["day:1"], GPU, 0.2, LEASE)
    assert ledger.reserved("day:1", GPU) == 0.3
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:1"], GPU, 1e-6, LEASE)
    ledger.settle(first.id, entry(0.1))
    assert ledger.spent("day:1", GPU) == 0.1
    ledger.set_cap(Cap("day:2", GPU, 10))
    with pytest.raises(BudgetExceeded):
        ledger.reserve(["day:2"], GPU, 10 + 1e-8, LEASE)


def test_pg_reap_keeps_a_lease_that_ends_exactly_now(ledger: SqlCostLedger) -> None:
    res = ledger.reserve(["day:1"], GPU, 1, LEASE)
    assert ledger.reap_expired(T0 + LEASE) == []
    assert ledger.reap_expired(T0 + LEASE + dt.timedelta(microseconds=1)) == [res.id]


def test_pg_concurrent_double_settle_records_the_cost_once(ledger: SqlCostLedger) -> None:
    rounds = 30
    for _ in range(rounds):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def settle(_k: int, rid: str = res.id) -> str:
            try:
                ledger.settle(rid, entry(1.5))
            except ReservationError:
                return "refused"
            return "settled"

        assert sorted(run_concurrently(2, settle)) == ["refused", "settled"]
    assert len(ledger.entries()) == rounds
    assert ledger.spent("day:1", GPU) == 1.5 * rounds


def test_pg_concurrent_settle_and_release_leave_a_consistent_state(ledger: SqlCostLedger) -> None:
    for i in range(20):
        res = ledger.reserve(["day:1"], GPU, 1, LEASE)

        def race(k: int, rid: str = res.id, run: str = f"run-{i}") -> str:
            try:
                if k == 0:
                    ledger.settle(rid, entry(2, run_id=run))
                else:
                    ledger.release(rid)
            except ReservationError:
                return "refused"
            return "done"

        settle_outcome, release_outcome = run_concurrently(2, race)
        recorded = ledger.entries(f"run-{i}")
        if ledger.status(res.id) == "settled":
            assert (settle_outcome, release_outcome, len(recorded)) == ("done", "refused", 1)
        else:
            assert ledger.status(res.id) == "released"
            assert (settle_outcome, release_outcome, recorded) == ("refused", "done", [])
    assert ledger.reserved("day:1", GPU) == 0
    assert ledger.spent("day:1", GPU) == 2 * len(ledger.entries())


def test_pg_renew_racing_the_reaper_keeps_the_reservation_once(ledger: SqlCostLedger) -> None:
    late = T0 + dt.timedelta(minutes=5)
    for _ in range(20):
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


def test_pg_reaped_reservations_taken_back_concurrently_never_exceed_the_cap(ledger: SqlCostLedger) -> None:
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


def test_pg_renew_waits_for_a_concurrent_reap_then_respects_the_cap(ledger: SqlCostLedger, pg: Engine, admin: Engine) -> None:
    ledger.set_cap(Cap("day:1", GPU, 10))
    slow = ledger.reserve(["day:1"], GPU, 10, LEASE)
    with pg.connect() as reaper:
        tx = reaper.begin()  # a reaper midway: the lease expired, and another job got the freed budget
        reaper.execute(reservations.update().where(reservations.c.id == slow.id).values(status="reaped"))
        reaper.execute(
            insert(reservations).values(
                id="other", kind=GPU.value, amount_micro=10_000_000, lease_until=T0 + LEASE, status="active"
            )
        )
        reaper.execute(insert(reservation_scopes).values(reservation_id="other", scope="day:1"))
        pool, renew = in_background(lambda: ledger.renew(slow.id, T0 + dt.timedelta(hours=1)))
        try:
            wait_until_lock_wait(admin, "FOR UPDATE")  # the renew reads the reservation under a row lock
        finally:
            tx.commit()
        with pytest.raises(BudgetExceeded):  # it then sees the reap, and no room is left
            renew.result(timeout=10)
        pool.shutdown()
    assert ledger.status(slow.id) == "reaped"
    assert ledger.reserved("day:1", GPU) == 10
