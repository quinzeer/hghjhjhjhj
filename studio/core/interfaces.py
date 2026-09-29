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
    """The caller's lease is no longer the live claim of this step key: another executor holds it, or the
    caller's own lease expired, was released or re-queued, or the step ended in another state."""


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
        discarded (the caller logs its cost as waste). One exception: a winner whose output is no longer
        readable (purged, or its file is gone) is replaced by the caller's output, so a replan can always
        recompute the step. Raises ArtifactMissing when `artifact_key` itself is not stored."""
        ...

    def step_output(self, step_key: str) -> str | None:
        """The output bound to this step, or None when there is none or it is no longer readable (the
        step must then be recomputed)."""
        ...

    def pin(self, artifact_key: str, owner: str) -> None:
        """Reference an artifact from a manifest: pinned artifacts are never purged by retention."""
        ...

    def unpin(self, artifact_key: str, owner: str) -> None: ...

    def pinned(self, owner: str) -> list[str]:
        """Keys pinned by `owner`, sorted: lets a run release every pin it holds even when the caller
        lost its manifest."""
        ...

    def purge_unpinned(self, older_than: dt.timedelta) -> list[str]:
        """Delete unpinned artifacts whose last put is older than `older_than`, with the step bindings
        that point to them. Returns the deleted keys."""
        ...


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

    def renew(self, reservation_id: str, lease_until: dt.datetime) -> Reservation:
        """Extend the lease of an active reservation (never shortens it). A reaped reservation becomes
        active again only if every capped scope still has room, else BudgetExceeded. Called from the queue
        heartbeat, so a job that outlives its first lease keeps its reservation."""
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

    def claim(self, queue: str, executor_id: str, now: dt.datetime, lease: dt.timedelta) -> Lease | None:
        """Take the next queued job of `queue` (lowest priority number, then oldest). The lease carries the
        attempt number used as fencing token by heartbeat, complete and fail."""
        ...

    def heartbeat(self, lease: Lease, now: dt.datetime, extend: dt.timedelta) -> Lease: ...

    def complete(self, lease: Lease) -> None: ...

    def fail(self, lease: Lease, error: str, retry: bool) -> None: ...

    def expire(self, now: dt.datetime) -> list[str]:
        """Make jobs whose lease expired claimable again: the next claim gets attempt + 1. Returns their
        step keys."""
        ...

    def pending(self, queue: str | None = None) -> list[Job]: ...


@runtime_checkable
class DispatchableQueue(JobQueue, Protocol):
    """A `JobQueue` that also answers the GPU dispatcher in one set-based query, whatever the backlog
    (`SqlJobQueue`). Any other `JobQueue` still works: the dispatcher falls back to `pending()` scans."""

    def claim(
        self,
        queue: str,
        executor_id: str,
        now: dt.datetime,
        lease: dt.timedelta,
        *,
        drafts_blocked_by: Sequence[str] = (),
    ) -> Lease | None:
        """Like `JobQueue.claim`, but a draft is not claimed while a final is queued in any of
        `drafts_blocked_by`."""
        ...

    def queued_counts(self, queues: Sequence[str]) -> dict[str, int]: ...

    def final_queued(self, queues: Sequence[str]) -> bool: ...

    def release(self, lease: Lease) -> None:
        """Hand back a live claim that started no work: the job keeps its place and no attempt is spent."""
        ...


# ------------------------------------------------------------------ steps and plans


# What a step returns: the output's bytes, its artifact kind and media type, and optionally what the step measured
# itself ({CostKind: quantity}, e.g. the tokens of a Claude call), which replaces the runner's estimate.
StepOutput = tuple[bytes, str, str] | tuple[bytes, str, str, Mapping[CostKind, float]]


@dataclass(frozen=True)
class StepSpec:
    """One node of the graph. `run` receives resolved input artifacts and returns output bytes + kind."""

    name: str
    version: str
    inputs: tuple[str, ...]  # names of upstream steps
    params: Mapping[str, Any]
    resource: ResourceClass
    run: Callable[[Mapping[str, StoredArtifact], Mapping[str, Any]], StepOutput]
    seed: int = 0
    estimated_cost: Mapping[CostKind, float] = field(default_factory=dict)
    model_id: str | None = None
    draft: bool = False
    # A gate step runs no code: it waits for a decision on the output of `inputs[0]` (its subject).
    gate: GateName | None = None
    # (gate, subject step): this step may run only if that gate approved that step's exact output.
    requires_approval: tuple[tuple[GateName, str], ...] = ()
    # The step uses at least one mock adapter. A run that contains such a step is a mock run whatever its caller
    # declares (`Runner.run` refuses `mock=False`), so mock work can never pass for real work.
    mock: bool = False
    # The step releases something to the outside (a plan the publisher will upload). The graph refuses it unless
    # it requires both the compliance verdict and G2 on one and the same upstream step: nobody can add a
    # publishing step and forget the gates (ADR-001 decision 8).
    publishes: bool = False
    # The step's output is a publication candidate: everything the publication gates judge (a `PublicationCandidate`).
    # A publishing step must take its two approvals on such a step, never on a bare render.
    candidate: bool = False


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
