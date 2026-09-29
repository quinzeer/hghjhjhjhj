"""GPU dispatcher (ADR-001 decision 3): picks the queue of each job and starts jobs card by card.

- Routing: a GPU job goes to a card that already holds its model in VRAM (loading one costs tens of
  seconds), otherwise to the card with the fewest waiting jobs (ties: lowest index). CPU, LLM and human
  jobs go to the `cpu`, `llm` and `human` queues.
- Priority: finals always pass before drafts. A job's priority must lie in [0, DRAFT_OFFSET); a draft is
  enqueued with `priority + DRAFT_OFFSET`, so a queue that orders by priority alone also takes finals
  first, and the lease returned by a claim carries that effective priority. `SqlJobQueue` additionally
  orders finals first by itself, whatever path enqueued them.
- Cooperative preemption: a card does not start a draft while a final waits on any GPU card (finals
  waiting on the `cpu`, `llm` or `human` queues do not count), and a running draft can poll `should_yield`
  between its sub-steps.

With a `SqlJobQueue`, the dispatcher uses its set-based reads and its guarded claim, so the cost of a call
does not grow with the backlog, and a draft handed back after a race keeps its attempt count. Any other
`JobQueue` works through `pending()` scans; there a handed-back draft goes through `fail(retry=True)`,
which counts an attempt.

The loaded-model map lives in memory: workers report it with `mark_loaded` when they load or unload.
"""

from __future__ import annotations

import datetime as dt
import threading
from collections.abc import Sequence
from dataclasses import replace
from typing import Final, Protocol

from studio.core.interfaces import DispatchableQueue, Job, JobQueue, Lease, StepClaimed
from studio.domain import ResourceClass

DRAFT_OFFSET: Final = 1_000_000
YIELD_REASON: Final = "yielded: a final job is waiting on a GPU card"

_FIXED_QUEUES: Final = {ResourceClass.CPU: "cpu", ResourceClass.LLM: "llm", ResourceClass.HUMAN: "human"}


def gpu_queue(card: int) -> str:
    return f"gpu{card}"


def effective_priority(job: Job) -> int:
    """Queue priority of `job` (lower = sooner): every final comes before every draft."""
    if not 0 <= job.priority < DRAFT_OFFSET:
        raise ValueError(f"job {job.step_key}: priority must be in [0, {DRAFT_OFFSET}), got {job.priority}")
    return job.priority + DRAFT_OFFSET if job.draft else job.priority


class _DispatchOps(Protocol):
    """The four operations the dispatcher reads and claims through: `DispatchableQueue` provides them
    natively, `_PendingScan` builds them over any `JobQueue`."""

    def claim(
        self,
        queue: str,
        executor_id: str,
        now: dt.datetime,
        lease: dt.timedelta,
        *,
        drafts_blocked_by: Sequence[str] = (),
    ) -> Lease | None: ...

    def queued_counts(self, queues: Sequence[str]) -> dict[str, int]: ...

    def final_queued(self, queues: Sequence[str]) -> bool: ...

    def release(self, lease: Lease) -> None: ...


class _PendingScan:
    """`_DispatchOps` over any `JobQueue`, by scanning `pending()`: each call costs O(backlog), and a
    handed-back draft goes through `fail(retry=True)`, which counts an attempt."""

    def __init__(self, queue: JobQueue) -> None:
        self._queue = queue

    def claim(
        self,
        queue: str,
        executor_id: str,
        now: dt.datetime,
        lease: dt.timedelta,
        *,
        drafts_blocked_by: Sequence[str] = (),
    ) -> Lease | None:
        # Only the queue's own finals may pass while a final waits elsewhere; the queue claims them first
        # (effective priority).
        if drafts_blocked_by and all(job.draft for job in self._queue.pending(queue)) and self.final_queued(drafts_blocked_by):
            return None
        return self._queue.claim(queue, executor_id, now, lease)

    def queued_counts(self, queues: Sequence[str]) -> dict[str, int]:
        return {queue: len(self._queue.pending(queue)) for queue in queues}

    def final_queued(self, queues: Sequence[str]) -> bool:
        return any(not job.draft for queue in queues for job in self._queue.pending(queue))

    def release(self, lease: Lease) -> None:
        self._queue.fail(lease, YIELD_REASON, retry=True)


class GpuDispatcher:
    def __init__(self, queue: JobQueue, gpus: int = 4) -> None:
        if gpus < 1:
            raise ValueError("gpus must be at least 1")
        self._queue = queue
        self._ops: _DispatchOps = queue if isinstance(queue, DispatchableQueue) else _PendingScan(queue)
        self._gpus = gpus
        self._loaded: list[str | None] = [None] * gpus
        self._lock = threading.Lock()

    @property
    def gpu_queues(self) -> tuple[str, ...]:
        return tuple(gpu_queue(card) for card in range(self._gpus))

    # ------------------------------------------------------------ loaded models

    def mark_loaded(self, card: int, model_id: str | None) -> None:
        """Record the model now resident on `card` (None: nothing loaded)."""
        self._check_card(card)
        with self._lock:
            self._loaded[card] = model_id

    def loaded(self, card: int) -> str | None:
        self._check_card(card)
        with self._lock:
            return self._loaded[card]

    # ------------------------------------------------------------ routing

    def route(self, job: Job) -> str:
        resource = ResourceClass(job.resource)
        if resource is not ResourceClass.GPU:
            return _FIXED_QUEUES[resource]
        with self._lock:
            loaded = list(self._loaded)
        cards = list(range(self._gpus))
        if job.model_id is not None:
            cards = [card for card in cards if loaded[card] == job.model_id] or cards
        waiting = self._ops.queued_counts([gpu_queue(card) for card in cards])
        return gpu_queue(min(cards, key=lambda card: (waiting[gpu_queue(card)], card)))

    def submit(self, job: Job) -> str | None:
        """Route and enqueue `job`; returns its queue, or None when its step key is already queued or
        running anywhere (global lock)."""
        prioritised = replace(job, priority=effective_priority(job))
        queue = self.route(job)
        return queue if self._queue.enqueue(prioritised, queue) else None

    # ------------------------------------------------------------ claiming

    def final_waiting(self) -> bool:
        """True when a final job is queued (not yet started) on any GPU card."""
        return self._ops.final_queued(self.gpu_queues)

    def should_yield(self, lease: Lease) -> bool:
        """Cooperative preemption: a running draft should stop at its next checkpoint."""
        return lease.job.draft and self.final_waiting()

    def claim_for(self, card: int, executor_id: str, now: dt.datetime, lease: dt.timedelta) -> Lease | None:
        """Claim the next job of `card`'s queue: its finals first, and a draft only while no final waits on
        any GPU card."""
        self._check_card(card)
        claimed = self._ops.claim(gpu_queue(card), executor_id, now, lease, drafts_blocked_by=self.gpu_queues)
        if claimed is None or not claimed.job.draft or not self.final_waiting():
            return claimed
        # A final was enqueued while the draft was being claimed: hand the draft back before it starts (it
        # keeps its place in the queue).
        try:
            self._ops.release(claimed)
        except StepClaimed:
            pass  # the claim was already lost (expired and taken over): nothing started here either
        return None

    def _check_card(self, card: int) -> None:
        if not 0 <= card < self._gpus:
            raise ValueError(f"card must be in [0, {self._gpus}), got {card}")
