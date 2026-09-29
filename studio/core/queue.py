"""SQL job queue with a global lock per step key (ADR-001 decision 3, plan B "A4" behind `JobQueue`).

One row per step key in `step_claims`: the primary key *is* the global lock, whatever the queue, so a step
can be queued or running at most once across `gpu0`..`gpu3`, `cpu`, `llm` and `human`.

- Claim order inside a queue: every final before every draft (`draft` column), then the lowest priority,
  then the oldest enqueue. Finals therefore pass first whatever path enqueued them.
- Claiming uses `SELECT … FOR UPDATE SKIP LOCKED` on Postgres; on SQLite, `BEGIN IMMEDIATE` (see
  `studio.core.db`) serialises every write transaction. On an engine that does neither (a plain SQLite
  engine), a claim that loses a race to another claimer selects again instead of failing.
- `attempt` counts the claims of a step key over its whole life and is never reset, so the pair
  `(executor_id, attempt)` is a fencing token: `heartbeat`, `complete` and `fail` only succeed for the live
  lease, and a worker declared dead cannot overwrite the work of its replacement. The one exception is
  `release`, which hands back a claim that started no work: its attempt is not counted and its number is
  reissued by the next claim, so the releasing caller must drop that lease.
- `complete` and `fail(retry=False)` are idempotent for the lease that ended the step (a retry after an
  uncertain commit succeeds); any other lease gets StepClaimed.
- Every datetime must be timezone-aware; values are stored in UTC.
- On SQLite, use a file database: an in-memory one is private to each pooled connection.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Final

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ColumnElement,
    Connection,
    DateTime,
    Dialect,
    Engine,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    TypeDecorator,
    cast,
    false,
    func,
    insert,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError

from studio.core.db import create_tables
from studio.core.interfaces import Job, Lease, StepClaimed
from studio.domain import ResourceClass


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


_QUEUED = JobStatus.QUEUED.value
_RUNNING = JobStatus.RUNNING.value
_DONE = JobStatus.DONE.value
_FAILED = JobStatus.FAILED.value

# A claim selects again when another claimer took its row first (only possible on an engine that does not
# serialise writers). Each lost race means another claim succeeded, so a handful of rounds is plenty.
CLAIM_ROUNDS: Final = 16


class UtcDateTime(TypeDecorator[dt.datetime]):
    """Timezone-aware datetime stored in UTC; naive values are refused.

    SQLite has no timezone type: values are stored as naive UTC text, whose lexical order is the
    chronological order, and read back as aware UTC datetimes."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        if value is None:
            return None
        utc = _aware_utc(value, "datetime")
        return utc.replace(tzinfo=None) if dialect.name == "sqlite" else utc

    def process_result_value(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=dt.UTC) if value.tzinfo is None else value.astimezone(dt.UTC)


metadata = MetaData()

step_claims = Table(
    "step_claims",
    metadata,
    Column("step_key", String, primary_key=True),
    Column("queue", String, nullable=False),
    Column("status", String(16), nullable=False),
    Column("draft", Boolean, nullable=False),
    Column("priority", BigInteger, nullable=False),
    # Enqueue order, the tie-breaker after priority ("oldest first"). Retries, releases and expiries keep it.
    Column("seq", BigInteger, nullable=False),
    Column("attempt", Integer, nullable=False),
    # Claims handed back unstarted by `release` (diagnostics: they are not counted in `attempt`).
    Column("yields", Integer, nullable=False),
    Column("executor_id", String, nullable=True),
    Column("lease_until", UtcDateTime, nullable=True),
    Column("payload", JSON, nullable=False),
    Column("last_error", Text, nullable=True),
    Column("updated_at", UtcDateTime, nullable=False),
    CheckConstraint("status IN ('queued', 'running', 'done', 'failed')", name="ck_step_claims_status"),
    CheckConstraint("attempt >= 0", name="ck_step_claims_attempt"),
    CheckConstraint("yields >= 0", name="ck_step_claims_yields"),
    CheckConstraint(
        "status <> 'running' OR (executor_id IS NOT NULL AND lease_until IS NOT NULL)",
        name="ck_step_claims_running_lease",
    ),
    Index("ix_step_claims_claim", "queue", "status", "draft", "priority", "seq"),
    Index("ix_step_claims_lease", "status", "lease_until"),
    Index("ix_step_claims_seq", "seq"),
)


# Claim order inside a queue: finals (draft = false sorts first), lowest priority, oldest enqueue.
_CLAIM_ORDER: Final = (step_claims.c.draft, step_claims.c.priority, step_claims.c.seq, step_claims.c.step_key)


def _final_queued_clause(queues: Sequence[str]) -> ColumnElement[bool]:
    other = step_claims.alias("final_waiting")
    return (
        select(other.c.step_key)
        .where(other.c.queue.in_(list(queues)), other.c.status == _QUEUED, other.c.draft == false())
        .exists()
    )


@dataclass(frozen=True)
class JobRecord:
    """Current state of one step key in the queue (inspection and diagnostics)."""

    job: Job
    queue: str
    status: JobStatus
    priority: int
    attempt: int
    yields: int
    executor_id: str | None
    lease_until: dt.datetime | None
    last_error: str | None
    updated_at: dt.datetime


class SqlJobQueue:
    """`JobQueue` on SQLAlchemy Core, for Postgres (production) and SQLite (tests, local dry runs).

    Beyond the protocol, it offers what `studio.core.scheduler.GpuDispatcher` needs to stay cheap with a
    large backlog: set-based reads (`queued_counts`, `final_queued`), a claim that refuses drafts while a
    final waits (`drafts_blocked_by`) and `release`."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_schema(self) -> None:
        """Create the queue table if missing (idempotent, safe when several workers start at once)."""
        create_tables(self._engine, metadata)

    # ------------------------------------------------------------ JobQueue

    def enqueue(self, job: Job, queue: str) -> bool:
        _check_name(queue, "queue")
        _check_name(job.step_key, "step_key")
        values: dict[str, Any] = {
            "queue": queue,
            "status": _QUEUED,
            "draft": bool(job.draft),
            "priority": job.priority,
            "executor_id": None,
            "lease_until": None,
            "payload": _job_to_json(job),
            "last_error": None,
            "updated_at": _wall_clock(),
        }
        t = step_claims
        try:
            with self._engine.begin() as conn:
                values["seq"] = _next_seq(conn)
                rearmed = conn.execute(
                    update(t).where(t.c.step_key == job.step_key, t.c.status.in_((_DONE, _FAILED))).values(**values)
                )
                if rearmed.rowcount == 1:
                    return True
                if conn.execute(select(t.c.step_key).where(t.c.step_key == job.step_key)).first() is not None:
                    return False  # queued or running somewhere: the global lock is taken
                conn.execute(insert(t).values(step_key=job.step_key, attempt=0, yields=0, **values))
                return True
        except IntegrityError as exc:
            # A concurrent enqueue inserted the same step key first and holds the lock.
            if _is_unique_violation(exc):
                return False
            raise

    def claim(
        self,
        queue: str,
        executor_id: str,
        now: dt.datetime,
        lease: dt.timedelta,
        *,
        drafts_blocked_by: Sequence[str] = (),
    ) -> Lease | None:
        """Claim the next queued job of `queue` (finals, then lowest priority, then oldest).

        With `drafts_blocked_by`, a draft is not claimed while a final is queued in any of those queues;
        the check runs in the claim's own transaction (atomic on SQLite; on Postgres it sees the finals
        committed before the claim, so a caller that must be exact re-checks after the claim)."""
        _check_name(queue, "queue")
        _check_name(executor_id, "executor_id")
        now = _aware_utc(now, "now")
        _check_positive(lease, "lease")
        t = step_claims
        conditions: list[ColumnElement[bool]] = [t.c.queue == queue, t.c.status == _QUEUED]
        if drafts_blocked_by:
            conditions.append(or_(t.c.draft == false(), ~_final_queued_clause(drafts_blocked_by)))
        head = (
            select(t.c.step_key, t.c.attempt, t.c.payload)
            .where(*conditions)
            .order_by(*_CLAIM_ORDER)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        until = now + lease
        with self._engine.begin() as conn:
            for _ in range(CLAIM_ROUNDS):
                row = conn.execute(head).first()
                if row is None:
                    return None
                attempt = int(row.attempt) + 1
                taken = conn.execute(
                    update(t)
                    .where(t.c.step_key == row.step_key, t.c.status == _QUEUED)
                    .values(
                        status=_RUNNING, attempt=attempt, executor_id=executor_id, lease_until=until, updated_at=_wall_clock()
                    )
                )
                if taken.rowcount == 1:
                    return Lease(
                        job=_job_from_json(row.payload), executor_id=executor_id, queue=queue, attempt=attempt, lease_until=until
                    )
                # Another claimer took this row between our select and our update: select again.
        raise RuntimeError(f"claim on {queue}: lost {CLAIM_ROUNDS} races in a row; the engine does not serialise writers")

    def heartbeat(self, lease: Lease, now: dt.datetime, extend: dt.timedelta) -> Lease:
        """Renew a live lease until `now + extend`.

        A lease past its deadline can still be renewed until `expire` hands the job over: nobody else
        holds it in the meantime."""
        now = _aware_utc(now, "now")
        _check_positive(extend, "extend")
        until = now + extend
        self._fenced_update(lease, lease_until=until)
        return replace(lease, lease_until=until)

    def complete(self, lease: Lease) -> None:
        """Mark the step done. Repeating it with the same lease is a no-op (retry after an uncertain commit)."""
        self._fenced_update(lease, ended_as=_DONE, status=_DONE, lease_until=None, last_error=None)

    def fail(self, lease: Lease, error: str, retry: bool) -> None:
        """retry=True puts the job back in its queue at its original place; retry=False marks it failed
        (repeating that with the same lease is a no-op)."""
        if retry:
            self._fenced_update(lease, status=_QUEUED, executor_id=None, lease_until=None, last_error=error)
        else:
            self._fenced_update(lease, ended_as=_FAILED, status=_FAILED, lease_until=None, last_error=error)

    def expire(self, now: dt.datetime) -> list[str]:
        now = _aware_utc(now, "now")
        t = step_claims
        reason = (
            literal("lease expired (executor ")
            + t.c.executor_id
            + literal(", attempt ")
            + cast(t.c.attempt, String)
            + literal(")")
        )
        with self._engine.begin() as conn:
            rows = conn.execute(
                update(t)
                .where(t.c.status == _RUNNING, t.c.lease_until < now)
                .values(status=_QUEUED, executor_id=None, lease_until=None, last_error=reason, updated_at=_wall_clock())
                .returning(t.c.step_key)
            ).all()
        return sorted(str(r.step_key) for r in rows)

    def pending(self, queue: str | None = None) -> list[Job]:
        """Queued jobs (not running ones), in claim order."""
        t = step_claims
        stmt = select(t.c.payload).where(t.c.status == _QUEUED)
        if queue is not None:
            stmt = stmt.where(t.c.queue == queue)
        stmt = stmt.order_by(*_CLAIM_ORDER)
        with self._engine.begin() as conn:
            return [_job_from_json(r.payload) for r in conn.execute(stmt)]

    # ------------------------------------------------------------ dispatcher support

    def release(self, lease: Lease) -> None:
        """Hand back a live claim that started no work (cooperative yield): the job returns to its place,
        `attempt` goes back to its previous value and `yields` counts the hand-back. Drop the lease: its
        attempt number is reissued by the next claim."""
        self._fenced_update(
            lease,
            status=_QUEUED,
            executor_id=None,
            lease_until=None,
            attempt=step_claims.c.attempt - 1,
            yields=step_claims.c.yields + 1,
        )

    def queued_counts(self, queues: Sequence[str] | None = None) -> dict[str, int]:
        """Number of queued jobs per queue: every queue of `queues` (0 when empty), or every non-empty
        queue when `queues` is None. One aggregate query, whatever the backlog."""
        t = step_claims
        stmt = select(t.c.queue, func.count()).where(t.c.status == _QUEUED).group_by(t.c.queue)
        counts: dict[str, int] = {}
        if queues is not None:
            if not queues:
                return {}
            stmt = stmt.where(t.c.queue.in_(list(queues)))
            counts = dict.fromkeys(queues, 0)
        with self._engine.begin() as conn:
            counts.update({str(r[0]): int(r[1]) for r in conn.execute(stmt)})
        return counts

    def final_queued(self, queues: Sequence[str]) -> bool:
        """True when a final (non-draft) job is queued, not yet started, in any of `queues`."""
        if not queues:
            return False
        with self._engine.begin() as conn:
            return bool(conn.execute(select(_final_queued_clause(queues))).scalar_one())

    # ------------------------------------------------------------ inspection

    def record(self, step_key: str) -> JobRecord | None:
        t = step_claims
        with self._engine.begin() as conn:
            row = conn.execute(select(t).where(t.c.step_key == step_key)).first()
        if row is None:
            return None
        return JobRecord(
            job=_job_from_json(row.payload),
            queue=row.queue,
            status=JobStatus(row.status),
            priority=int(row.priority),
            attempt=int(row.attempt),
            yields=int(row.yields),
            executor_id=row.executor_id,
            lease_until=row.lease_until,
            last_error=row.last_error,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------------ internals

    def _fenced_update(self, lease: Lease, *, ended_as: str | None = None, **values: Any) -> None:
        """Apply `values` only if `lease` is still the live claim of its step key, else raise StepClaimed.

        With `ended_as`, a row already in that terminal status under this very lease counts as success."""
        t = step_claims
        token = (t.c.step_key == lease.job.step_key, t.c.executor_id == lease.executor_id, t.c.attempt == lease.attempt)
        with self._engine.begin() as conn:
            res = conn.execute(update(t).where(*token, t.c.status == _RUNNING).values(updated_at=_wall_clock(), **values))
            if res.rowcount == 1:
                return
            if ended_as is not None and conn.execute(select(t.c.step_key).where(*token, t.c.status == ended_as)).first():
                return
        current = self.record(lease.job.step_key)
        state = "absent" if current is None else f"{current.status} (executor {current.executor_id}, attempt {current.attempt})"
        raise StepClaimed(
            f"step {lease.job.step_key}: lease of executor {lease.executor_id} attempt {lease.attempt} is no longer live; "
            f"row is {state}"
        )


# ------------------------------------------------------------------ helpers


def _next_seq(conn: Connection) -> int:
    # Concurrent Postgres enqueues may draw the same value: they are then ordered by step key.
    return int(conn.execute(select(func.coalesce(func.max(step_claims.c.seq), 0) + 1)).scalar_one())


def _job_to_json(job: Job) -> dict[str, Any]:
    data: dict[str, Any] = {
        "step_key": job.step_key,
        "step_name": job.step_name,
        "run_id": job.run_id,
        "resource": ResourceClass(job.resource).value,
        "priority": job.priority,
        "payload": dict(job.payload),
        "model_id": job.model_id,
        "draft": job.draft,
        "timeout_s": job.timeout_s,
    }
    try:
        json.dumps(data, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"job {job.step_key} is not JSON-serialisable: {exc}") from exc
    return data


def _job_from_json(data: dict[str, Any]) -> Job:
    return Job(
        step_key=data["step_key"],
        step_name=data["step_name"],
        run_id=data["run_id"],
        resource=ResourceClass(data["resource"]),
        priority=int(data["priority"]),
        payload=data["payload"],
        model_id=data["model_id"],
        draft=bool(data["draft"]),
        timeout_s=float(data["timeout_s"]),
    )


def _aware_utc(value: dt.datetime, name: str) -> dt.datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(dt.UTC)


def _wall_clock() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _check_name(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _check_positive(value: dt.timedelta, name: str) -> None:
    if value <= dt.timedelta(0):
        raise ValueError(f"{name} must be positive")


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    return getattr(orig, "sqlstate", None) == "23505" or "UNIQUE constraint failed" in str(orig)
