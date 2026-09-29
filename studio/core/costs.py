"""Cost ledger: caps, atomic reservations and measured entries (ADR-001 decision 5).

A job reserves its estimated cost on every scope it belongs to (video, day, month…) before it starts. The
check `spent + reserved + amount <= cap` and the insert of the reservation happen in one transaction:
- Postgres: the cap rows of the scopes involved are locked with `SELECT ... FOR UPDATE`, in scope order so
  that two reservations over the same scopes cannot deadlock; spent and reserved amounts are then read in
  a single statement (one snapshot), so a concurrent `settle` is seen either before or after, never half.
- SQLite: `BEGIN IMMEDIATE` (see `db.py`) already serialises every write transaction.

Amounts are counted in integer millionths of a unit, so sums are exact and the cap check has no float
tolerance: a reserved amount is rounded up, a cap down (whatever is reserved fits under the cap as given),
a measured quantity to the nearest millionth (entries also keep the quantity exactly as measured).

A scope without a cap for a kind is unlimited for that kind. Reservation states:
`active` -> `settled` (measured cost recorded) | `released` (job did not run) | `reaped` (lease expired: the
worker is presumed dead). A lease is valid up to and including `lease_until`; a live job keeps it with
`renew`, which also takes a reaped reservation back if the caps still allow it (or raises BudgetExceeded:
the job must stop). A reaped reservation can still be settled: a worker declared dead may have been alive,
and the cost it measured was really incurred.

Timestamps are stored in UTC. A naive lease or `reap_expired(now)` is taken as UTC; a naive entry time is
refused, since the entry could not be read back as it was given.
"""

from __future__ import annotations

import datetime as dt
import math
import uuid
from collections.abc import Callable, Sequence
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Connection,
    Engine,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    RowMapping,
    String,
    Table,
    false,
    func,
    insert,
    select,
    union_all,
    update,
)

from studio.core.db import UtcDateTime, as_utc, create_tables, dialect_insert
from studio.core.interfaces import BudgetExceeded, Cap, Reservation, StudioError
from studio.domain import CostEntry, CostKind

ACTIVE = "active"
SETTLED = "settled"
RELEASED = "released"
REAPED = "reaped"
MICRO = 1_000_000  # ledger unit: a millionth of a cost unit (micro-euro, microsecond, micro-token…)
MAX_AMOUNT = 1e12  # per cap, reservation or entry: keeps sums of micro-units far inside 64-bit integers


class ReservationError(StudioError):
    """Unknown reservation, or a transition its current state forbids (e.g. settling it twice)."""


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


_metadata = MetaData()

caps = Table(
    "caps",
    _metadata,
    Column("scope", String(255), primary_key=True),
    Column("kind", String(64), primary_key=True),
    Column("limit_micro", BigInteger, nullable=False),
)

reservations = Table(
    "reservations",
    _metadata,
    Column("id", String(32), primary_key=True),
    Column("kind", String(64), nullable=False),
    Column("amount_micro", BigInteger, nullable=False),
    Column("lease_until", UtcDateTime(), nullable=False),
    Column("status", String(16), nullable=False),
    CheckConstraint(f"status IN ('{ACTIVE}', '{SETTLED}', '{RELEASED}', '{REAPED}')", name="ck_reservations_status"),
    Index("ix_reservations_status_lease", "status", "lease_until"),
)

reservation_scopes = Table(
    "reservation_scopes",
    _metadata,
    Column("reservation_id", String(32), ForeignKey("reservations.id"), primary_key=True),
    Column("scope", String(255), primary_key=True),
    Index("ix_reservation_scopes_scope", "scope"),
)

entries = Table(
    "entries",
    _metadata,
    Column("id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True),
    Column("run_id", String(255), nullable=False, index=True),
    Column("step_key", String(64), nullable=False),
    Column("kind", String(64), nullable=False),
    Column("quantity", Float, nullable=False),  # as measured, returned by `entries()`
    Column("quantity_micro", BigInteger, nullable=False),  # as counted by `spent()` and the cap checks
    Column("estimated", Boolean, nullable=False),
    Column("mock", Boolean, nullable=False, server_default=false()),  # measured on a mock adapter: never real spending
    Column("at", UtcDateTime(), nullable=False),
)

entry_scopes = Table(
    "entry_scopes",
    _metadata,
    Column("entry_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("entries.id"), primary_key=True),
    Column("scope", String(255), primary_key=True),
    Index("ix_entry_scopes_scope", "scope"),
)


def _check_amount(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= MAX_AMOUNT:
        raise ValueError(f"{name} must be a finite number in [0, {MAX_AMOUNT:g}], got {value!r}")
    return value


def to_micro(value: float, rounding: str) -> int:
    """`value` in millionths, rounded as asked (the float's shortest decimal form is taken as exact)."""
    return int((Decimal(repr(float(value))) * MICRO).to_integral_value(rounding=rounding))


def _units(micro: int) -> float:
    return micro / MICRO


def _normalise_scopes(scopes: Sequence[str]) -> list[str]:
    if isinstance(scopes, str):
        raise TypeError("scopes must be a sequence of scope names, not a single string")
    wanted = sorted(set(scopes))
    if not wanted or any(not s for s in wanted):
        raise ValueError("at least one non-empty scope is required")
    return wanted


class SqlCostLedger:
    """`CostLedger` on the SQL database behind `engine` (Postgres in production, SQLite in tests)."""

    def __init__(self, engine: Engine, *, clock: Callable[[], dt.datetime] = _utcnow) -> None:
        self.engine = engine
        self._clock = clock

    def create_schema(self) -> None:
        """Create the ledger tables if they do not exist (idempotent, concurrency-safe)."""
        create_tables(self.engine, _metadata)

    # ------------------------------------------------------------------ caps and reservations

    def set_cap(self, cap: Cap) -> None:
        """Create or replace the cap of (scope, kind)."""
        limit = to_micro(_check_amount("cap limit", cap.limit), ROUND_FLOOR)
        if not cap.scope:
            raise ValueError("cap scope is required")
        kind = CostKind(cap.kind).value
        with self.engine.begin() as conn:
            stmt = dialect_insert(conn, caps).values(scope=cap.scope, kind=kind, limit_micro=limit)
            conn.execute(stmt.on_conflict_do_update(index_elements=[caps.c.scope, caps.c.kind], set_={"limit_micro": limit}))

    def cap(self, scope: str, kind: CostKind) -> float | None:
        """The cap of (scope, kind), or None when that scope is unlimited for that kind."""
        with self.engine.connect() as conn:
            value = conn.execute(
                select(caps.c.limit_micro).where(caps.c.scope == scope, caps.c.kind == CostKind(kind).value)
            ).scalar()
        return None if value is None else _units(int(value))

    def reserve(self, scopes: Sequence[str], kind: CostKind, amount: float, lease: dt.timedelta) -> Reservation:
        """Reserve `amount` (rounded up to a millionth) on every scope at once, or raise BudgetExceeded and
        reserve nothing."""
        kind = CostKind(kind)
        amount_micro = to_micro(_check_amount("amount", amount), ROUND_CEILING)
        wanted = _normalise_scopes(scopes)
        if lease <= dt.timedelta(0):
            raise ValueError("lease must be positive")
        reservation = Reservation(
            id=uuid.uuid4().hex,
            scopes=tuple(wanted),
            kind=kind,
            amount=_units(amount_micro),
            lease_until=as_utc(self._clock()) + lease,
        )
        with self.engine.begin() as conn:
            self._check_room(conn, wanted, kind, amount_micro)
            conn.execute(
                insert(reservations).values(
                    id=reservation.id,
                    kind=kind.value,
                    amount_micro=amount_micro,
                    lease_until=reservation.lease_until,
                    status=ACTIVE,
                )
            )
            conn.execute(insert(reservation_scopes), [{"reservation_id": reservation.id, "scope": s} for s in wanted])
        return reservation

    def renew(self, reservation_id: str, lease_until: dt.datetime) -> Reservation:
        """Extend the lease of a live job's reservation (from its heartbeat), so that the reaper leaves it.

        The lease is never shortened. A reservation reaped meanwhile is taken back only if every capped scope
        still has room for it; otherwise BudgetExceeded and it stays reaped: the job must stop."""
        until = as_utc(lease_until)
        if until <= as_utc(self._clock()):
            raise ValueError(f"lease_until must be in the future, got {until.isoformat()}")
        with self.engine.begin() as conn:
            row = self._lock_reservation(conn, reservation_id)
            status, kind, amount_micro = str(row["status"]), CostKind(row["kind"]), int(row["amount_micro"])
            if status not in (ACTIVE, REAPED):
                raise ReservationError(f"reservation {reservation_id} is {status}: it cannot be renewed")
            scopes = self._scopes_of(conn, reservation_id)
            if status == REAPED:
                self._check_room(conn, scopes, kind, amount_micro)
            until = max(until, as_utc(row["lease_until"]))
            conn.execute(update(reservations).where(reservations.c.id == reservation_id).values(status=ACTIVE, lease_until=until))
        return Reservation(id=reservation_id, scopes=tuple(scopes), kind=kind, amount=_units(amount_micro), lease_until=until)

    def settle(self, reservation_id: str, entry: CostEntry) -> None:
        """Mark the reservation settled and record `entry` on each of its scopes, in one transaction."""
        if entry.at.tzinfo is None or entry.at.utcoffset() is None:
            raise ValueError(f"entry time must be timezone-aware, got {entry.at.isoformat()}")
        _check_amount("entry quantity", entry.quantity)
        with self.engine.begin() as conn:
            row = self._lock_reservation(conn, reservation_id)
            status, kind = str(row["status"]), str(row["kind"])
            if entry.kind.value != kind:
                raise ValueError(f"entry kind {entry.kind.value} does not match reservation kind {kind}")
            if status not in (ACTIVE, REAPED):
                raise ReservationError(f"reservation {reservation_id} is {status}: it cannot be settled")
            conn.execute(update(reservations).where(reservations.c.id == reservation_id).values(status=SETTLED))
            self._insert_entry(conn, entry, self._scopes_of(conn, reservation_id))

    def release(self, reservation_id: str) -> None:
        """Give an active reservation back. Releasing a released or reaped one is a no-op."""
        with self.engine.begin() as conn:
            status = str(self._lock_reservation(conn, reservation_id)["status"])
            if status == SETTLED:
                raise ReservationError(f"reservation {reservation_id} is already settled")
            if status == ACTIVE:
                conn.execute(update(reservations).where(reservations.c.id == reservation_id).values(status=RELEASED))

    def reap_expired(self, now: dt.datetime) -> list[str]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                update(reservations)
                .where(reservations.c.status == ACTIVE, reservations.c.lease_until < as_utc(now))
                .values(status=REAPED)
                .returning(reservations.c.id)
            ).all()
        return sorted(str(row[0]) for row in rows)

    # ------------------------------------------------------------------ reads

    def spent(self, scope: str, kind: CostKind) -> float:
        query = (
            select(func.coalesce(func.sum(entries.c.quantity_micro), 0))
            .select_from(entries.join(entry_scopes, entry_scopes.c.entry_id == entries.c.id))
            .where(entry_scopes.c.scope == scope, entries.c.kind == CostKind(kind).value)
        )
        with self.engine.connect() as conn:
            return _units(int(conn.execute(query).scalar() or 0))

    def reserved(self, scope: str, kind: CostKind) -> float:
        query = (
            select(func.coalesce(func.sum(reservations.c.amount_micro), 0))
            .select_from(reservations.join(reservation_scopes, reservation_scopes.c.reservation_id == reservations.c.id))
            .where(
                reservation_scopes.c.scope == scope,
                reservations.c.kind == CostKind(kind).value,
                reservations.c.status == ACTIVE,
            )
        )
        with self.engine.connect() as conn:
            return _units(int(conn.execute(query).scalar() or 0))

    def status(self, reservation_id: str) -> str:
        """Current state of a reservation: active, settled, released or reaped."""
        with self.engine.connect() as conn:
            value = conn.execute(select(reservations.c.status).where(reservations.c.id == reservation_id)).scalar()
        if value is None:
            raise ReservationError(f"unknown reservation {reservation_id}")
        return str(value)

    def entries(self, run_id: str | None = None) -> list[CostEntry]:
        query = select(entries).order_by(entries.c.id)
        if run_id is not None:
            query = query.where(entries.c.run_id == run_id)
        with self.engine.connect() as conn:
            rows = conn.execute(query).all()
        return [self._entry(row._mapping) for row in rows]

    # ------------------------------------------------------------------ internals

    @classmethod
    def _check_room(cls, conn: Connection, scopes: list[str], kind: CostKind, amount_micro: int) -> None:
        """Raise BudgetExceeded unless every capped scope has room for `amount_micro` more. Locks the caps."""
        limits = cls._lock_caps(conn, scopes, kind)
        used = cls._usage(conn, list(limits), kind) if limits else {}
        for scope, limit in limits.items():
            current = used.get(scope, 0)
            if current + amount_micro > limit:
                raise BudgetExceeded(
                    f"{kind.value} on {scope}: {_units(current):g} spent or reserved"
                    f" + {_units(amount_micro):g} requested > cap {_units(limit):g}"
                )

    @staticmethod
    def _lock_caps(conn: Connection, scopes: list[str], kind: CostKind) -> dict[str, int]:
        """Caps of `kind` on `scopes`, locked in scope order (FOR UPDATE is omitted by SQLite)."""
        rows = conn.execute(
            select(caps.c.scope, caps.c.limit_micro)
            .where(caps.c.kind == kind.value, caps.c.scope.in_(scopes))
            .order_by(caps.c.scope)
            .with_for_update()
        ).all()
        return {str(row[0]): int(row[1]) for row in rows}

    @staticmethod
    def _usage(conn: Connection, scopes: list[str], kind: CostKind) -> dict[str, int]:
        """spent + active reservations per scope, read in one statement (one snapshot)."""
        spent_q = (
            select(entry_scopes.c.scope.label("scope"), entries.c.quantity_micro.label("value"))
            .select_from(entry_scopes.join(entries, entry_scopes.c.entry_id == entries.c.id))
            .where(entries.c.kind == kind.value, entry_scopes.c.scope.in_(scopes))
        )
        held_q = (
            select(reservation_scopes.c.scope.label("scope"), reservations.c.amount_micro.label("value"))
            .select_from(reservation_scopes.join(reservations, reservation_scopes.c.reservation_id == reservations.c.id))
            .where(
                reservations.c.kind == kind.value,
                reservations.c.status == ACTIVE,
                reservation_scopes.c.scope.in_(scopes),
            )
        )
        both = union_all(spent_q, held_q).subquery()
        rows = conn.execute(select(both.c.scope, func.sum(both.c.value)).group_by(both.c.scope)).all()
        return {str(row[0]): int(row[1] or 0) for row in rows}

    @staticmethod
    def _lock_reservation(conn: Connection, reservation_id: str) -> RowMapping:
        row = conn.execute(
            select(reservations.c.status, reservations.c.kind, reservations.c.amount_micro, reservations.c.lease_until)
            .where(reservations.c.id == reservation_id)
            .with_for_update()
        ).one_or_none()
        if row is None:
            raise ReservationError(f"unknown reservation {reservation_id}")
        return row._mapping

    @staticmethod
    def _scopes_of(conn: Connection, reservation_id: str) -> list[str]:
        rows = conn.execute(
            select(reservation_scopes.c.scope)
            .where(reservation_scopes.c.reservation_id == reservation_id)
            .order_by(reservation_scopes.c.scope)
        ).all()
        return [str(row[0]) for row in rows]

    @staticmethod
    def _insert_entry(conn: Connection, entry: CostEntry, scopes: list[str]) -> None:
        entry_id = conn.execute(
            insert(entries)
            .values(
                run_id=entry.run_id,
                step_key=entry.step_key,
                kind=entry.kind.value,
                quantity=entry.quantity,
                quantity_micro=to_micro(entry.quantity, ROUND_HALF_EVEN),
                estimated=entry.estimated,
                mock=entry.mock,
                at=entry.at,
            )
            .returning(entries.c.id)
        ).scalar()
        if scopes:
            conn.execute(insert(entry_scopes), [{"entry_id": entry_id, "scope": s} for s in scopes])

    @staticmethod
    def _entry(m: RowMapping) -> CostEntry:
        return CostEntry(
            run_id=str(m["run_id"]),
            step_key=str(m["step_key"]),
            kind=CostKind(m["kind"]),
            quantity=float(m["quantity"]),
            estimated=bool(m["estimated"]),
            mock=bool(m["mock"]),
            at=m["at"],
        )
