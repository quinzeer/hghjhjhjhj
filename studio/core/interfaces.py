"""Interfaces of the execution core (ADR-001). Implementations live next to this file; steps and agents
depend only on these protocols, so a backend (local CAS → S3, in-memory queue → Postgres/DBOS) can be
swapped by configuration.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from studio.domain import CostEntry, CostKind, GateDecision, GateName, ResourceClass

# ------------------------------------------------------------------ errors


class StudioError(Exception):
    """Base class of expected, reportable failures."""


class BudgetExceeded(StudioError):
    """A reservation would push a scope past its cap: the job must not start (hard stop)."""


class StepClaimed(StudioError):
    """Another executor holds the global lock on this step key."""


class ArtifactMissing(StudioError):
    pass


class GateNotApproved(StudioError):
    """A step that requires an approval ran into a missing or negative gate decision."""


# ------------------------------------------------------------------ artifacts


@dataclass(frozen=True)
class StoredArtifact:
    key: str  # sha256 of the bytes
    kind: str  # image | video | audio | subtitle | json | text
    media_type: str
    size_bytes: int
    path: Path


@runtime_checkable
class ArtifactStore(Protocol):
    """Content-addressed store. Writing the same bytes twice is a no-op that returns the same key."""

    def put_bytes(self, data: bytes, *, kind: str, media_type: str) -> StoredArtifact: ...

    def put_file(self, src: Path, *, kind: str, media_type: str) -> StoredArtifact: ...

    def get(self, key: str) -> StoredArtifact: ...  # raises ArtifactMissing

    def has(self, key: str) -> bool: ...

    def commit_step_output(self, step_key: str, artifact_key: str) -> str:
        """Bind a step to its output, first write wins: returns the key actually bound.

        If another producer already committed this step, its key is returned and the caller's output is
        discarded (the caller logs its cost as waste)."""
        ...

    def step_output(self, step_key: str) -> str | None: ...

    def pin(self, artifact_key: str, owner: str) -> None:
        """Reference an artifact from a manifest: pinned artifacts are never purged by retention."""
        ...

    def unpin(self, artifact_key: str, owner: str) -> None: ...

    def purge_unpinned(self, older_than: dt.timedelta) -> list[str]: ...


# ------------------------------------------------------------------ costs


@dataclass(frozen=True)
class Cap:
    scope: str  # e.g. "video:<run_id>", "day:2026-09-28", "month:2026-09"
    kind: CostKind
    limit: float


@dataclass(frozen=True)
class Reservation:
    id: str
    scopes: tuple[str, ...]
    kind: CostKind
    amount: float
    lease_until: dt.datetime


@runtime_checkable
class CostLedger(Protocol):
    """Atomic reservations against caps (ADR-001 decision 5)."""

    def set_cap(self, cap: Cap) -> None: ...

    def reserve(self, scopes: Sequence[str], kind: CostKind, amount: float, lease: dt.timedelta) -> Reservation:
        """Reserve `amount` on every scope at once, or raise BudgetExceeded and reserve nothing."""
        ...

    def settle(self, reservation_id: str, entry: CostEntry) -> None:
        """Replace the reservation by the measured cost (which may exceed the estimate)."""
        ...

    def release(self, reservation_id: str) -> None: ...

    def reap_expired(self, now: dt.datetime) -> list[str]:
        """Release reservations whose lease expired (crashed worker). Returns their ids."""
        ...

    def spent(self, scope: str, kind: CostKind) -> float: ...

    def reserved(self, scope: str, kind: CostKind) -> float: ...

    def entries(self, run_id: str | None = None) -> list[CostEntry]: ...


# ------------------------------------------------------------------ queue


@dataclass(frozen=True)
class Job:
    step_key: str
    step_name: str
    run_id: str
    resource: ResourceClass
    priority: int  # lower = more urgent (DBOS convention)
    payload: Mapping[str, Any] = field(default_factory=dict)
    model_id: str | None = None  # for GPU affinity: prefer the card that already has this model loaded
    draft: bool = False
    timeout_s: float = 3600.0


@dataclass(frozen=True)
class Lease:
    job: Job
    executor_id: str
    queue: str  # "gpu0".."gpu3", "cpu", "llm", "human"
    attempt: int
    lease_until: dt.datetime


@runtime_checkable
class JobQueue(Protocol):
    """Priority queue with global step claims (one live execution per step key, across all queues)."""

    def enqueue(self, job: Job, queue: str) -> bool:
        """False when the step key is already claimed or queued anywhere (global dedup)."""
        ...

    def claim(self, queue: str, executor_id: str, now: dt.datetime, lease: dt.timedelta) -> Lease | None: ...

    def heartbeat(self, lease: Lease, now: dt.datetime, extend: dt.timedelta) -> Lease: ...

    def complete(self, lease: Lease) -> None: ...

    def fail(self, lease: Lease, error: str, retry: bool) -> None: ...

    def expire(self, now: dt.datetime) -> list[str]:
        """Make jobs whose lease expired claimable again (attempt + 1). Returns their step keys."""
        ...

    def pending(self, queue: str | None = None) -> list[Job]: ...


# ------------------------------------------------------------------ steps and plans


@dataclass(frozen=True)
class StepSpec:
    """One node of the graph. `run` receives resolved input artifacts and returns output bytes + kind."""

    name: str
    version: str
    inputs: tuple[str, ...]  # names of upstream steps
    params: Mapping[str, Any]
    resource: ResourceClass
    run: Callable[[Mapping[str, StoredArtifact], Mapping[str, Any]], tuple[bytes, str, str]]
    seed: int = 0
    estimated_cost: Mapping[CostKind, float] = field(default_factory=dict)
    model_id: str | None = None
    draft: bool = False
    # A gate step runs no code: it waits for a decision on the output of `inputs[0]` (its subject).
    gate: GateName | None = None
    # (gate, subject step): this step may run only if that gate approved that step's exact output.
    requires_approval: tuple[tuple[GateName, str], ...] = ()


@runtime_checkable
class DecisionSource(Protocol):
    """Where gate decisions come from (validation UI, compliance agent, or a test fake)."""

    def get(self, gate: GateName, subject_key: str) -> GateDecision | None: ...


@dataclass
class PlanResult:
    run_id: str
    step_keys: dict[str, str]
    outputs: dict[str, str]  # step name -> artifact key
    executed: list[str]  # steps actually run this time (empty on a replay)
    skipped: list[str]  # steps whose output already existed
    waiting: list[str]  # human gates without a decision
