"""SqlJobQueue and GpuDispatcher on Postgres: SKIP LOCKED claims, global step lock under concurrency,
fencing races, timestamptz handling. Skipped unless STUDIO_TEST_PG_URL is set.

The module works in a schema of its own, created for the session and dropped at the end: whatever database
STUDIO_TEST_PG_URL points to, its tables are never touched."""

from __future__ import annotations

import datetime as dt
import os
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import pytest
from sqlalchemy import Engine, delete, select, text

from studio.core.db import make_engine
from studio.core.interfaces import Job, Lease, StepClaimed
from studio.core.queue import JobStatus, SqlJobQueue, step_claims
from studio.core.scheduler import DRAFT_OFFSET, GpuDispatcher, gpu_queue
from studio.domain import ResourceClass

PG_URL = os.environ.get("STUDIO_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not PG_URL, reason="STUDIO_TEST_PG_URL is not set"),
]

T0 = dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.UTC)
LEASE = dt.timedelta(seconds=30)


def job(key: str, priority: int = 0, **kw: Any) -> Job:
    return Job(step_key=key, step_name="shot", run_id="run-pg", resource=ResourceClass.GPU, priority=priority, **kw)


def default_schema_state(conn: Any) -> tuple[str, int | None]:
    """Name of the database's default schema and the row count of its `step_claims` (None: no such table)."""
    schema = str(conn.execute(text("SELECT current_schema()")).scalar_one())
    exists = conn.execute(text("SELECT to_regclass(quote_ident(current_schema()) || '.step_claims')")).scalar_one()
    rows = None if exists is None else int(conn.execute(text(f'SELECT count(*) FROM "{schema}".step_claims')).scalar_one())
    return schema, rows


@pytest.fixture(scope="module")
def admin() -> Iterator[Engine]:
    """Engine on the target database as configured (default schema): used only for DDL and checks."""
    eng = make_engine(PG_URL)
    assert eng.dialect.name == "postgresql"
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def schema(admin: Engine) -> Iterator[str]:
    name = f"test_queue_{uuid.uuid4().hex[:12]}"
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{name}"'))
    yield name
    with admin.begin() as conn:
        conn.execute(text(f'DROP SCHEMA "{name}" CASCADE'))


@pytest.fixture(scope="module")
def default_state_before(admin: Engine, schema: str) -> tuple[str, int | None]:
    with admin.connect() as conn:
        return default_schema_state(conn)


@pytest.fixture(scope="module")
def engine(admin: Engine, schema: str, default_state_before: tuple[str, int | None]) -> Engine:
    """Same pool, but every table of the queue resolves to the private schema."""
    return admin.execution_options(schema_translate_map={None: schema})


@pytest.fixture
def q(engine: Engine) -> Iterator[SqlJobQueue]:
    queue = SqlJobQueue(engine)
    queue.create_schema()
    with engine.begin() as conn:
        conn.execute(delete(step_claims))
    yield queue
    with engine.begin() as conn:
        conn.execute(delete(step_claims))


def run_threads(n: int, target: Callable[[int], None]) -> list[BaseException]:
    errors: list[BaseException] = []

    def wrapped(i: int) -> None:
        try:
            target(i)
        except BaseException as exc:  # pragma: no cover - reported to the caller
            errors.append(exc)

    threads = [threading.Thread(target=wrapped, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    assert not any(t.is_alive() for t in threads), "a worker thread hung"
    return errors


# ------------------------------------------------------------------ claims


def test_eight_threads_claiming_one_queue_never_get_the_same_job(q: SqlJobQueue) -> None:
    n_jobs = 240
    for i in range(n_jobs):
        assert q.enqueue(job(f"job-{i:03d}", priority=i % 7), "gpu0")
    barrier = threading.Barrier(8)
    claimed: list[tuple[str, str]] = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        barrier.wait()
        while (lease := q.claim("gpu0", f"w{i}", T0, LEASE)) is not None:
            with lock:
                claimed.append((lease.job.step_key, lease.executor_id))

    assert run_threads(8, worker) == []
    counts = Counter(key for key, _ in claimed)
    assert len(claimed) == n_jobs and set(counts.values()) == {1}
    for key, executor in claimed:
        rec = q.record(key)
        assert rec is not None and (rec.status, rec.executor_id, rec.attempt) == (JobStatus.RUNNING, executor, 1)
    assert len({executor for _, executor in claimed}) > 1


def test_claim_skips_a_locked_row_instead_of_waiting(q: SqlJobQueue, engine: Engine) -> None:
    assert q.enqueue(job("a", priority=0), "gpu0")
    assert q.enqueue(job("b", priority=1), "gpu0")
    result: dict[str, Any] = {}

    def claimer() -> None:
        result["lease"] = q.claim("gpu0", "w", T0, LEASE)

    with engine.connect() as locker:
        tx = locker.begin()
        locked = locker.execute(select(step_claims.c.step_key).where(step_claims.c.step_key == "a").with_for_update()).all()
        assert [r.step_key for r in locked] == ["a"]
        thread = threading.Thread(target=claimer)
        thread.start()
        thread.join(timeout=10)
        finished_while_locked = not thread.is_alive()
        tx.rollback()
    thread.join()
    assert finished_while_locked, "claim blocked on a locked row (SKIP LOCKED missing)"
    assert result["lease"] is not None and result["lease"].job.step_key == "b"
    rec = q.record("a")
    assert rec is not None and rec.status is JobStatus.QUEUED


def test_priority_then_age_order(q: SqlJobQueue) -> None:
    for key, prio in [("late-urgent", 3), ("z-old", 5), ("a-new", 5), ("draft", 1_000_002), ("top", 0)]:
        assert q.enqueue(job(key, priority=prio), "gpu1")
    order = []
    while (lease := q.claim("gpu1", "gpu1", T0, LEASE)) is not None:
        order.append(lease.job.step_key)
    assert order == ["top", "late-urgent", "z-old", "a-new", "draft"]


# ------------------------------------------------------------------ global step lock


def enqueue_race(q: SqlJobQueue, key: str, n: int = 8) -> list[str]:
    """`n` threads enqueue `key` at once, each on its own queue; returns the queues that were accepted."""
    barrier = threading.Barrier(n)
    accepted: list[str] = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        barrier.wait()
        if q.enqueue(job(key), f"queue{i}"):
            with lock:
                accepted.append(f"queue{i}")

    assert run_threads(n, worker) == []
    return accepted


def test_concurrent_enqueues_of_one_key_on_different_queues_admit_exactly_one(q: SqlJobQueue) -> None:
    for round_ in range(10):
        key = f"step-{round_}"
        accepted = enqueue_race(q, key)
        assert len(accepted) == 1
        rec = q.record(key)
        assert rec is not None and rec.queue == accepted[0] and rec.status is JobStatus.QUEUED
    assert len(q.pending()) == 10


def test_concurrent_reenqueues_of_a_done_key_admit_exactly_one(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "gpu0", T0, LEASE)
    assert lease is not None
    q.complete(lease)
    barrier = threading.Barrier(8)
    results: list[bool] = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        barrier.wait()
        ok = q.enqueue(job("a", payload={"from": i}), f"gpu{i % 4}")
        with lock:
            results.append(ok)

    assert run_threads(8, worker) == []
    assert sorted(results) == [False] * 7 + [True]
    assert len(q.pending()) == 1


# ------------------------------------------------------------------ leases and fencing


def test_a_dead_executor_cannot_touch_the_job_of_its_replacement(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    dead = q.claim("gpu0", "gpu0", T0, dt.timedelta(seconds=10))
    assert dead is not None
    assert q.expire(T0 + dt.timedelta(seconds=11)) == ["a"]
    heir = q.claim("gpu0", "gpu0", T0 + dt.timedelta(seconds=12), LEASE)
    assert heir is not None and heir.attempt == 2
    with pytest.raises(StepClaimed):
        q.heartbeat(dead, T0 + dt.timedelta(seconds=13), LEASE)
    with pytest.raises(StepClaimed):
        q.complete(dead)
    with pytest.raises(StepClaimed):
        q.fail(dead, "zombie", retry=True)
    q.complete(q.heartbeat(heir, T0 + dt.timedelta(seconds=20), LEASE))
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.attempt) == (JobStatus.DONE, 2)


def heartbeat_expire_race(q: SqlJobQueue, lease: Lease, late: dt.datetime) -> tuple[Lease | None, list[str]]:
    """Heartbeat `lease` and expire leases at `late` from two threads at once."""
    barrier = threading.Barrier(2)
    outcome: dict[str, Any] = {}

    def racer(n: int) -> None:
        barrier.wait()
        if n == 0:
            try:
                outcome["heartbeat"] = q.heartbeat(lease, late, dt.timedelta(seconds=30))
            except StepClaimed:
                outcome["heartbeat"] = None
        else:
            outcome["expired"] = q.expire(late)

    assert run_threads(2, racer) == []
    return outcome["heartbeat"], outcome["expired"]


def test_heartbeat_and_expire_racing_on_a_stale_lease_have_one_winner(q: SqlJobQueue) -> None:
    rounds = 20
    for i in range(rounds):
        assert q.enqueue(job(f"r{i:02d}"), "gpu2")
    for i in range(rounds):
        key = f"r{i:02d}"
        lease = q.claim("gpu2", "gpu2", T0, dt.timedelta(seconds=10))
        assert lease is not None and lease.job.step_key == key
        late = T0 + dt.timedelta(seconds=11)
        renewed, expired = heartbeat_expire_race(q, lease, late)
        rec = q.record(key)
        assert rec is not None
        if renewed is not None:
            assert expired == [] and rec.status is JobStatus.RUNNING
            assert rec.lease_until == late + dt.timedelta(seconds=30)
            q.complete(renewed)
        else:
            assert expired == [key] and rec.status is JobStatus.QUEUED
            assert rec.attempt == 1 and rec.executor_id is None
            retaken = q.claim("gpu2", "gpu2", late, LEASE)
            assert retaken is not None and retaken.job.step_key == key and retaken.attempt == 2
            q.complete(retaken)


def test_concurrent_workers_complete_every_job_exactly_once_despite_retries(q: SqlJobQueue) -> None:
    n_jobs = 90
    for i in range(n_jobs):
        assert q.enqueue(job(f"job-{i:02d}"), "cpu")
    completions: list[str] = []
    retried: set[str] = set()
    lock = threading.Lock()

    def worker(i: int) -> None:
        while (lease := q.claim("cpu", f"w{i}", T0, LEASE)) is not None:
            key = lease.job.step_key
            with lock:
                retry = key not in retried and int(key[-2:]) % 4 == 0
                if retry:
                    retried.add(key)
            if retry:
                q.fail(lease, "transient", retry=True)
                continue
            q.complete(lease)
            with lock:
                completions.append(key)

    assert run_threads(8, worker) == []
    assert sorted(completions) == sorted(f"job-{i:02d}" for i in range(n_jobs))
    for i in range(n_jobs):
        rec = q.record(f"job-{i:02d}")
        assert rec is not None and rec.status is JobStatus.DONE and rec.attempt == (2 if i % 4 == 0 else 1)


def test_timestamps_are_compared_in_utc_whatever_the_offset(q: SqlJobQueue) -> None:
    paris = dt.timezone(dt.timedelta(hours=2))
    new_york = dt.timezone(dt.timedelta(hours=-4))
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0.astimezone(paris), dt.timedelta(seconds=10))
    assert lease is not None and lease.lease_until == T0 + dt.timedelta(seconds=10)
    rec = q.record("a")
    assert rec is not None and rec.lease_until == T0 + dt.timedelta(seconds=10)
    assert rec.lease_until.utcoffset() == dt.timedelta(0)
    assert q.expire((T0 + dt.timedelta(seconds=10)).astimezone(new_york)) == []
    assert q.expire((T0 + dt.timedelta(seconds=10, microseconds=1)).astimezone(new_york)) == ["a"]


# ------------------------------------------------------------------ dispatcher on Postgres


def test_dispatcher_never_starts_a_draft_while_a_final_waits(q: SqlJobQueue) -> None:
    d = GpuDispatcher(q, gpus=4)
    d.mark_loaded(3, "final-model")
    n_finals, n_drafts = 10, 20
    for i in range(n_finals):
        assert d.submit(job(f"final-{i:02d}", priority=50, model_id="final-model")) == "gpu3"
    for i in range(n_drafts):
        assert d.submit(job(f"draft-{i:02d}", priority=0, draft=True, model_id="draft-model")) is not None
    assert all(q.pending(gpu_queue(c)) for c in range(3))
    claimed: list[str] = []
    violations: list[str] = []
    lock = threading.Lock()
    deadline = time.monotonic() + 60

    def card_worker(card: int) -> None:
        while time.monotonic() < deadline:
            with lock:
                if len(claimed) == n_finals + n_drafts:
                    return
            lease = d.claim_for(card, f"gpu{card}", T0, LEASE)
            if lease is None:
                time.sleep(0.002)
                continue
            if lease.job.draft:
                waiting = [j.step_key for c in range(4) for j in q.pending(gpu_queue(c)) if not j.draft]
                if waiting:
                    with lock:
                        violations.append(f"{lease.job.step_key} on gpu{card} while {waiting} waited")
            else:
                time.sleep(0.005)
            q.complete(lease)
            with lock:
                claimed.append(lease.job.step_key)

    assert run_threads(4, card_worker) == []
    assert violations == []
    assert sorted(claimed) == sorted([f"final-{i:02d}" for i in range(n_finals)] + [f"draft-{i:02d}" for i in range(n_drafts)])


# ------------------------------------------------------------------ isolation of the test database


def test_the_queue_tables_live_in_a_private_schema(
    q: SqlJobQueue, admin: Engine, schema: str, default_state_before: tuple[str, int | None]
) -> None:
    assert q.enqueue(job("probe"), "gpu0")
    with admin.connect() as conn:
        where = (
            conn.execute(text("SELECT table_schema FROM information_schema.tables WHERE table_name = 'step_claims'"))
            .scalars()
            .all()
        )
        assert schema in where
        assert conn.execute(text(f'SELECT count(*) FROM "{schema}".step_claims')).scalar_one() == 1
        default, rows = default_schema_state(conn)
    assert default != schema
    assert (default, rows) == default_state_before  # the database's own step_claims (if any) is untouched


# ------------------------------------------------------------------ finals before drafts, release, idempotence


def test_finals_are_claimed_before_drafts_whatever_their_priority(q: SqlJobQueue) -> None:
    for key, prio, draft in [("d0", 0, True), ("f9", 9, False), ("d1", 1, True), ("f-big", 2_000_000, False)]:
        assert q.enqueue(job(key, priority=prio, draft=draft), "gpu0")
    assert [j.step_key for j in q.pending("gpu0")] == ["f9", "f-big", "d0", "d1"]
    order = []
    while (lease := q.claim("gpu0", "gpu0", T0, LEASE)) is not None:
        order.append(lease.job.step_key)
    assert order == ["f9", "f-big", "d0", "d1"]


def test_set_based_reads(q: SqlJobQueue) -> None:
    for key, queue, draft in [("a", "gpu0", True), ("b", "gpu0", True), ("c", "gpu2", False), ("h", "human", False)]:
        assert q.enqueue(job(key, draft=draft), queue)
    assert q.queued_counts(["gpu0", "gpu1", "gpu2"]) == {"gpu0": 2, "gpu1": 0, "gpu2": 1}
    assert q.final_queued(["gpu0", "gpu1"]) is False
    assert q.final_queued(["gpu0", "gpu2"]) is True
    assert q.claim("gpu2", "gpu2", T0, LEASE) is not None
    assert q.final_queued(["gpu0", "gpu1", "gpu2", "gpu3"]) is False


def test_complete_and_terminal_fail_are_idempotent_for_the_same_lease(q: SqlJobQueue) -> None:
    for key in ["a", "b"]:
        assert q.enqueue(job(key), "cpu")
    a = q.claim("cpu", "cpu", T0, LEASE)
    b = q.claim("cpu", "cpu", T0, LEASE)
    assert a is not None and b is not None
    q.complete(a)
    q.complete(a)
    q.fail(b, "bad input", retry=False)
    q.fail(b, "bad input", retry=False)
    with pytest.raises(StepClaimed):
        q.fail(a, "late", retry=False)
    with pytest.raises(StepClaimed):
        q.complete(b)
    ra, rb = q.record("a"), q.record("b")
    assert ra is not None and rb is not None
    assert (ra.status, ra.attempt, rb.status, rb.attempt) == (JobStatus.DONE, 1, JobStatus.FAILED, 1)


def test_release_does_not_count_an_attempt(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a", draft=True), "gpu0")
    for _ in range(3):
        lease = q.claim("gpu0", "gpu0", T0, LEASE)
        assert lease is not None and lease.attempt == 1
        q.release(lease)
        with pytest.raises(StepClaimed):
            q.complete(lease)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.QUEUED, 0, 3)


def test_a_guarded_claim_skips_locked_rows_and_still_blocks_drafts(q: SqlJobQueue, engine: Engine) -> None:
    gpus = ["gpu0", "gpu1"]
    assert q.enqueue(job("final", priority=0), "gpu0")
    assert q.enqueue(job("draft", priority=0, draft=True), "gpu0")
    result: dict[str, Any] = {}

    def claimer() -> None:
        result["lease"] = q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus)

    with engine.connect() as locker:
        tx = locker.begin()
        locked = locker.execute(select(step_claims.c.step_key).where(step_claims.c.step_key == "final").with_for_update()).all()
        assert [r.step_key for r in locked] == ["final"]
        thread = threading.Thread(target=claimer)
        thread.start()
        thread.join(timeout=10)
        finished_while_locked = not thread.is_alive()
        tx.rollback()
    thread.join()
    assert finished_while_locked, "a guarded claim blocked on a locked row"
    assert result["lease"] is None  # the locked final is skipped, and it still holds the draft back
    lease = q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus)
    assert lease is not None and lease.job.step_key == "final"
    draft = q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus)
    assert draft is not None and draft.job.step_key == "draft"


class LateFinalQueueMock(SqlJobQueue):
    """A real SqlJobQueue that commits a final on gpu1 right after each claim on gpu0 (the window between
    the claim's snapshot and the dispatcher's re-check)."""

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.finals = 0

    def claim(
        self, queue: str, executor_id: str, now: dt.datetime, lease: dt.timedelta, *, drafts_blocked_by: Sequence[str] = ()
    ) -> Lease | None:
        claimed = super().claim(queue, executor_id, now, lease, drafts_blocked_by=drafts_blocked_by)
        if queue == "gpu0" and claimed is not None:
            self.finals += 1
            assert self.enqueue(job(f"late-final-{self.finals}", priority=5), "gpu1")
        return claimed


def test_a_draft_released_after_a_race_keeps_its_attempt_count(q: SqlJobQueue, engine: Engine) -> None:
    racing = LateFinalQueueMock(engine)
    d = GpuDispatcher(racing, gpus=2)
    assert d.submit(job("draft", draft=True)) == "gpu0"
    for n in range(1, 4):
        assert d.claim_for(0, "gpu0", T0, LEASE) is None
        final = d.claim_for(1, "gpu1", T0, LEASE)
        assert final is not None and final.job.step_key == f"late-final-{n}"
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.QUEUED, 0, 3)


class ProtocolOnlyQueueMock:
    """Exposes only the JobQueue protocol of a real queue: drives the dispatcher's pending()-scan path."""

    def __init__(self, inner: SqlJobQueue) -> None:
        self.enqueue = inner.enqueue
        self.claim = inner.claim
        self.heartbeat = inner.heartbeat
        self.complete = inner.complete
        self.fail = inner.fail
        self.expire = inner.expire
        self.pending = inner.pending


@pytest.mark.parametrize("mode", ["sql", "protocol-only"])
def test_four_card_workers_with_finals_on_several_cards(q: SqlJobQueue, mode: str) -> None:
    d = GpuDispatcher(q if mode == "sql" else ProtocolOnlyQueueMock(q), gpus=4)  # type: ignore[arg-type]
    for card in (0, 1, 3):
        d.mark_loaded(card, f"m{card}")
    finals = [f"final-m{card}-{i}" for card, n in [(0, 3), (1, 3), (3, 8)] for i in range(n)]
    for key in finals:
        card = int(key.split("-")[1][1])
        assert d.submit(job(key, priority=int(key[-1]), model_id=f"m{card}")) == f"gpu{card}"
    drafts = [f"draft-{i:02d}" for i in range(24)]
    for key in drafts:
        assert d.submit(job(key, priority=0, draft=True, model_id="draft-model")) is not None
    assert {c for c in range(4) if any(j.draft for j in q.pending(gpu_queue(c)))} == {0, 1, 2, 3}

    claimed: list[str] = []
    violations: list[str] = []
    lock = threading.Lock()
    deadline = time.monotonic() + 60
    expected = len(finals) + len(drafts)

    def card_worker(card: int) -> None:
        while time.monotonic() < deadline:
            with lock:
                if len(claimed) == expected:
                    return
            lease = d.claim_for(card, f"gpu{card}", T0, LEASE)
            if lease is None:
                time.sleep(0.002)
                continue
            if lease.job.draft:
                waiting = [j.step_key for c in range(4) for j in q.pending(gpu_queue(c)) if not j.draft]
                if waiting:
                    with lock:
                        violations.append(f"{lease.job.step_key} on gpu{card} while {waiting} waited")
            else:
                time.sleep(0.005)
            q.complete(lease)
            with lock:
                claimed.append(lease.job.step_key)

    assert run_threads(4, card_worker) == []
    assert violations == []
    assert sorted(claimed) == sorted(finals + drafts)
    for key in finals + drafts:
        rec = q.record(key)
        assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.DONE, 1, 0), key


def test_a_raw_enqueue_cannot_start_a_draft_before_a_final(q: SqlJobQueue) -> None:
    d = GpuDispatcher(q, gpus=2)
    assert q.enqueue(job("draft", priority=0, draft=True), "gpu0")
    assert q.enqueue(job("final", priority=DRAFT_OFFSET - 1), "gpu0")
    first = d.claim_for(0, "gpu0", T0, LEASE)
    assert first is not None and first.job.step_key == "final"
