"""In-memory test doubles for the graph runner.

These are fakes (small working implementations), not mocks: they implement the core Protocols
(`ArtifactStore`, `CostLedger`, `DecisionSource`) with the observable semantics of the SQL implementations
(first write wins, pins protect from purge, atomic reservations against caps) and refuse what they refuse
(artifact kinds outside `artifacts.KINDS`, malformed media types, non-positive leases), so that a graph passing
on the fakes does not fail on `LocalArtifactStore` / `SqlCostLedger`. They add inspection helpers for
assertions. Every shared structure is guarded by a lock so that concurrent runners can share them.
"""

from __future__ import annotations

import datetime as dt
import math
import threading
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from studio.core.artifacts import KINDS
from studio.core.costs import ReservationError
from studio.core.hashing import bytes_key
from studio.core.interfaces import ArtifactMissing, BudgetExceeded, Cap, Reservation, StoredArtifact
from studio.domain import CostEntry, CostKind, GateDecision, GateName

_TOLERANCE = 1e-9


class ManualClock:
    """A clock that moves only when told to (a step "takes" N seconds by calling `advance(N)`)."""

    def __init__(self, start: dt.datetime | None = None) -> None:
        self._now = start or dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.UTC)
        self._lock = threading.Lock()

    def __call__(self) -> dt.datetime:
        with self._lock:
            return self._now

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._now += dt.timedelta(seconds=seconds)


# ------------------------------------------------------------------ artifacts


@dataclass
class _Blob:
    data: bytes
    kind: str
    media_type: str
    created_at: dt.datetime


class InMemoryArtifactStore:
    """`ArtifactStore` in a dict. Paths are placeholders: read content with `data(key)`."""

    def __init__(self, clock: Callable[[], dt.datetime] | None = None) -> None:
        self._clock = clock or ManualClock()
        self._lock = threading.Lock()
        self._blobs: dict[str, _Blob] = {}
        self._step_outputs: dict[str, str] = {}
        self._pins: dict[str, set[str]] = {}
        self.put_count = 0

    def _stored(self, key: str, blob: _Blob) -> StoredArtifact:
        return StoredArtifact(
            key=key,
            kind=blob.kind,
            media_type=blob.media_type,
            size_bytes=len(blob.data),
            path=Path("/in-memory") / key[:2] / key,
        )

    def put_bytes(self, data: bytes, *, kind: str, media_type: str) -> StoredArtifact:
        if kind not in KINDS:  # same rules as LocalArtifactStore._check_meta
            raise ValueError(f"unknown artifact kind {kind!r}; expected one of {sorted(KINDS)}")
        if not media_type or "/" not in media_type:
            raise ValueError(f"invalid media type: {media_type!r}")
        key = bytes_key(data)
        with self._lock:
            self.put_count += 1
            now = self._clock()
            blob = self._blobs.setdefault(key, _Blob(bytes(data), kind, media_type, now))
            blob.created_at = max(blob.created_at, now)  # retention counts from the latest put
            return self._stored(key, blob)

    def put_file(self, src: Path, *, kind: str, media_type: str) -> StoredArtifact:
        return self.put_bytes(Path(src).read_bytes(), kind=kind, media_type=media_type)

    def get(self, key: str) -> StoredArtifact:
        with self._lock:
            blob = self._blobs.get(key)
            if blob is None:
                raise ArtifactMissing(key)
            return self._stored(key, blob)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._blobs

    def commit_step_output(self, step_key: str, artifact_key: str) -> str:
        with self._lock:
            if artifact_key not in self._blobs:
                raise ArtifactMissing(f"{artifact_key}: cannot bind step {step_key} to an unstored artifact")
            return self._step_outputs.setdefault(step_key, artifact_key)

    def step_output(self, step_key: str) -> str | None:
        with self._lock:
            return self._step_outputs.get(step_key)

    def pin(self, artifact_key: str, owner: str) -> None:
        if not owner:
            raise ValueError("owner is required")
        with self._lock:
            if artifact_key not in self._blobs:
                raise ArtifactMissing(f"{artifact_key}: cannot pin an unstored artifact")
            self._pins.setdefault(artifact_key, set()).add(owner)

    def pinned(self, owner: str) -> list[str]:
        with self._lock:
            return sorted(key for key, owners in self._pins.items() if owner in owners)

    def unpin(self, artifact_key: str, owner: str) -> None:
        with self._lock:
            owners = self._pins.get(artifact_key)
            if owners is not None:
                owners.discard(owner)
                if not owners:
                    del self._pins[artifact_key]

    def purge_unpinned(self, older_than: dt.timedelta) -> list[str]:
        if older_than < dt.timedelta(0):
            raise ValueError("older_than must be >= 0")
        cutoff = self._clock() - older_than
        with self._lock:
            keys = sorted(k for k, b in self._blobs.items() if b.created_at < cutoff and k not in self._pins)
            self._drop(keys)
        return keys

    def _drop(self, keys: Iterable[str]) -> None:
        gone = set(keys)
        for key in gone:
            self._blobs.pop(key, None)
            self._pins.pop(key, None)
        for step_key in [s for s, a in self._step_outputs.items() if a in gone]:
            del self._step_outputs[step_key]

    # ------------------------------------------------------------------ inspection and fault injection

    def data(self, key: str) -> bytes:
        with self._lock:
            blob = self._blobs.get(key)
            if blob is None:
                raise ArtifactMissing(key)
            return blob.data

    def pinned_by(self, key: str) -> set[str]:
        with self._lock:
            return set(self._pins.get(key, set()))

    def pinned_for(self, owner: str) -> set[str]:
        """Every artifact `owner` pins, as a set (same as `pinned`, kept for the existing assertions)."""
        return set(self.pinned(owner))

    def step_output_count(self) -> int:
        with self._lock:
            return len(self._step_outputs)

    def forget_step_outputs(self) -> None:
        """Lose every step -> output link but keep the bytes: an index rebuilt from the CAS, or a store
        migrated by copying artifacts only."""
        with self._lock:
            self._step_outputs.clear()

    def lose(self, key: str) -> None:
        """Destroy an artifact whatever its pins (disk loss), with the step links pointing to it."""
        with self._lock:
            self._drop([key])


# ------------------------------------------------------------------ costs


@dataclass
class _Held:
    reservation: Reservation
    status: str = "active"


@dataclass
class _Entry:
    entry: CostEntry
    scopes: tuple[str, ...]


class InMemoryLedger:
    """`CostLedger` with caps: a reservation fails atomically when any capped scope would pass its limit
    (`spent + reserved + amount <= cap`). A scope without a cap is unlimited."""

    def __init__(self, clock: Callable[[], dt.datetime] | None = None) -> None:
        self.clock = clock or ManualClock()
        self._lock = threading.Lock()
        self._caps: dict[tuple[str, CostKind], float] = {}
        self._held: dict[str, _Held] = {}
        self._entries: list[_Entry] = []

    def set_cap(self, cap: Cap) -> None:
        with self._lock:
            self._caps[(cap.scope, CostKind(cap.kind))] = float(cap.limit)

    def reserve(self, scopes: Sequence[str], kind: CostKind, amount: float, lease: dt.timedelta) -> Reservation:
        if isinstance(scopes, str) or not scopes or not all(scopes):
            raise ValueError("at least one non-empty scope is required")
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f"amount must be finite and >= 0, got {amount!r}")
        if lease <= dt.timedelta(0):
            raise ValueError("lease must be positive")
        kind = CostKind(kind)
        wanted = tuple(sorted(set(scopes)))
        with self._lock:
            for scope in wanted:
                limit = self._caps.get((scope, kind))
                if limit is None:
                    continue
                used = self._spent(scope, kind) + self._reserved(scope, kind)
                if used + amount > limit + _TOLERANCE * max(1.0, abs(limit)):
                    raise BudgetExceeded(f"{kind.value} on {scope}: {used:g} + {amount:g} > cap {limit:g}")
            reservation = Reservation(
                id=uuid.uuid4().hex, scopes=wanted, kind=kind, amount=float(amount), lease_until=self.clock() + lease
            )
            self._held[reservation.id] = _Held(reservation)
            return reservation

    def renew(self, reservation_id: str, lease_until: dt.datetime) -> Reservation:
        """Extend a lease, never shorten it; a reaped reservation is taken back only if every capped scope
        has room for it (else BudgetExceeded); a settled or released one cannot be renewed."""
        if lease_until <= self.clock():
            raise ValueError(f"lease_until must be in the future, got {lease_until.isoformat()}")
        with self._lock:
            held = self._held.get(reservation_id)
            if held is None:
                raise ReservationError(f"unknown reservation {reservation_id}")
            if held.status not in ("active", "reaped"):
                raise ReservationError(f"reservation {reservation_id} is {held.status}: it cannot be renewed")
            reservation = held.reservation
            if held.status == "reaped":
                for scope in reservation.scopes:
                    limit = self._caps.get((scope, reservation.kind))
                    if limit is None:
                        continue
                    used = self._spent(scope, reservation.kind) + self._reserved(scope, reservation.kind)
                    if used + reservation.amount > limit + _TOLERANCE * max(1.0, abs(limit)):
                        raise BudgetExceeded(f"{reservation.kind.value} on {scope}: no room to take {reservation.id} back")
            renewed = Reservation(
                id=reservation.id,
                scopes=reservation.scopes,
                kind=reservation.kind,
                amount=reservation.amount,
                lease_until=max(reservation.lease_until, lease_until),
            )
            self._held[reservation_id] = _Held(renewed, "active")
            return renewed

    def settle(self, reservation_id: str, entry: CostEntry) -> None:
        with self._lock:
            held = self._held[reservation_id]
            if entry.kind is not held.reservation.kind:
                raise ValueError("entry kind does not match the reservation kind")
            if held.status not in ("active", "reaped"):
                raise ValueError(f"reservation {reservation_id} is {held.status}: it cannot be settled")
            held.status = "settled"
            self._entries.append(_Entry(entry, held.reservation.scopes))

    def release(self, reservation_id: str) -> None:
        with self._lock:
            held = self._held[reservation_id]
            if held.status == "settled":
                raise ValueError(f"reservation {reservation_id} is already settled")
            if held.status == "active":
                held.status = "released"

    def reap_expired(self, now: dt.datetime) -> list[str]:
        with self._lock:
            expired = [h for h in self._held.values() if h.status == "active" and h.reservation.lease_until < now]
            for held in expired:
                held.status = "reaped"
            return sorted(h.reservation.id for h in expired)

    def spent(self, scope: str, kind: CostKind) -> float:
        with self._lock:
            return self._spent(scope, CostKind(kind))

    def reserved(self, scope: str, kind: CostKind) -> float:
        with self._lock:
            return self._reserved(scope, CostKind(kind))

    def entries(self, run_id: str | None = None) -> list[CostEntry]:
        with self._lock:
            return [e.entry for e in self._entries if run_id is None or e.entry.run_id == run_id]

    def _spent(self, scope: str, kind: CostKind) -> float:
        return sum(e.entry.quantity for e in self._entries if e.entry.kind is kind and scope in e.scopes)

    def _reserved(self, scope: str, kind: CostKind) -> float:
        return sum(
            h.reservation.amount
            for h in self._held.values()
            if h.status == "active" and h.reservation.kind is kind and scope in h.reservation.scopes
        )

    # ------------------------------------------------------------------ inspection

    def reservations(self) -> list[Reservation]:
        """Every reservation ever made, oldest first."""
        with self._lock:
            return [h.reservation for h in self._held.values()]

    def status(self, reservation_id: str) -> str:
        with self._lock:
            return self._held[reservation_id].status


# ------------------------------------------------------------------ decisions


class DictDecisionSource:
    """`DecisionSource` keyed by (gate, subject key), as the validation UI stores decisions."""

    def __init__(self, decisions: Iterable[GateDecision] = ()) -> None:
        self._lock = threading.Lock()
        self._decisions: dict[tuple[GateName, str], GateDecision] = {}
        for decision in decisions:
            self.put(decision)

    def put(self, decision: GateDecision) -> None:
        with self._lock:
            self._decisions[(decision.gate, decision.subject_key)] = decision

    def get(self, gate: GateName, subject_key: str) -> GateDecision | None:
        with self._lock:
            return self._decisions.get((GateName(gate), subject_key))


class SubjectBlindDecisionSource:
    """A faulty `DecisionSource` that answers with the latest decision of a gate whatever subject is asked
    about (e.g. a UI that returns "the G2 of this video"). The runner must not trust it blindly."""

    def __init__(self, decisions: Iterable[GateDecision] = ()) -> None:
        self._latest: dict[GateName, GateDecision] = {d.gate: d for d in decisions}

    def get(self, gate: GateName, subject_key: str) -> GateDecision | None:
        return self._latest.get(GateName(gate))
