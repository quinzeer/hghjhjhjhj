"""GpuDispatcher over a real SqlJobQueue (SQLite): routing, model affinity, finals before drafts,
cooperative preemption.

Every test that takes the `d` fixture runs twice: once on the SqlJobQueue itself (set-based reads, guarded
claim, release) and once behind `ProtocolOnlyQueueMock`, which exposes only the JobQueue protocol and so
drives the dispatcher's `pending()`-scanning fallback."""

from __future__ import annotations

import datetime as dt
import threading
import time
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from studio.core.db import make_engine
from studio.core.interfaces import Job, JobQueue, Lease
from studio.core.queue import JobStatus, SqlJobQueue
from studio.core.scheduler import DRAFT_OFFSET, YIELD_REASON, GpuDispatcher, effective_priority, gpu_queue
from studio.domain import ResourceClass

T0 = dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.UTC)
LEASE = dt.timedelta(minutes=5)
MODES = ("sql", "protocol-only")


def job(key: str, *, priority: int = 10, resource: ResourceClass = ResourceClass.GPU, **kw: object) -> Job:
    return Job(step_key=key, step_name="shot", run_id="run-1", resource=resource, priority=priority, **kw)  # type: ignore[arg-type]


@pytest.fixture
def q(tmp_path: Path) -> SqlJobQueue:
    queue = SqlJobQueue(make_engine(f"sqlite:///{tmp_path / 'queue.db'}"))
    queue.create_schema()
    return queue


@pytest.fixture(params=MODES)
def mode(request: pytest.FixtureRequest) -> str:
    return str(request.param)


def dispatcher(q: SqlJobQueue, mode: str, gpus: int = 4) -> GpuDispatcher:
    return GpuDispatcher(q if mode == "sql" else ProtocolOnlyQueueMock(q), gpus=gpus)


@pytest.fixture
def d(q: SqlJobQueue, mode: str) -> GpuDispatcher:
    return dispatcher(q, mode)


def keys(jobs: list[Job]) -> list[str]:
    return [j.step_key for j in jobs]


# ------------------------------------------------------------------ routing


def test_non_gpu_resources_have_fixed_queues(d: GpuDispatcher) -> None:
    assert d.route(job("c", resource=ResourceClass.CPU)) == "cpu"
    assert d.route(job("l", resource=ResourceClass.LLM)) == "llm"
    assert d.route(job("h", resource=ResourceClass.HUMAN)) == "human"
    assert d.submit(job("c", resource=ResourceClass.CPU, model_id="whatever")) == "cpu"


def test_gpu_jobs_go_to_the_least_loaded_card_lowest_index_first(d: GpuDispatcher, q: SqlJobQueue) -> None:
    assert d.gpu_queues == ("gpu0", "gpu1", "gpu2", "gpu3")
    routed = [d.submit(job(f"j{i}")) for i in range(6)]
    assert routed == ["gpu0", "gpu1", "gpu2", "gpu3", "gpu0", "gpu1"]
    assert keys(q.pending("gpu1")) == ["j1", "j5"]


def test_load_counts_waiting_jobs_only(d: GpuDispatcher, q: SqlJobQueue) -> None:
    for i in range(8):
        d.submit(job(f"j{i}"))  # two per card
    assert q.claim("gpu2", "gpu2", T0, LEASE) is not None
    assert q.claim("gpu2", "gpu2", T0, LEASE) is not None
    assert d.route(job("next")) == "gpu2"  # its jobs are running, nothing waits there
    assert q.enqueue(job("elsewhere"), "cpu")
    assert d.route(job("next")) == "gpu2"  # other queues do not weigh on the cards


def test_a_card_that_holds_the_model_wins_even_when_busier(d: GpuDispatcher, q: SqlJobQueue) -> None:
    for i in range(3):
        assert q.enqueue(job(f"backlog{i}"), "gpu2")
    d.mark_loaded(2, "wan22")
    assert d.loaded(2) == "wan22"
    assert d.route(job("w", model_id="wan22")) == "gpu2"
    assert d.submit(job("w", model_id="wan22")) == "gpu2"
    assert d.route(job("f", model_id="flux-schnell")) == "gpu0"  # not loaded anywhere: least loaded card
    assert d.route(job("n")) == "gpu0"  # no model: least loaded card


def test_affinity_among_several_cards_picks_the_least_loaded(d: GpuDispatcher, q: SqlJobQueue) -> None:
    d.mark_loaded(1, "wan22")
    d.mark_loaded(3, "wan22")
    assert q.enqueue(job("b1"), "gpu1")
    assert q.enqueue(job("b2"), "gpu1")
    assert q.enqueue(job("b3"), "gpu3")
    assert d.route(job("w", model_id="wan22")) == "gpu3"
    assert q.enqueue(job("b4"), "gpu3")
    assert d.route(job("w", model_id="wan22")) == "gpu1"  # tie: lowest index


def test_unloading_a_model_removes_the_affinity(d: GpuDispatcher, q: SqlJobQueue) -> None:
    assert q.enqueue(job("b"), "gpu0")
    d.mark_loaded(0, "wan22")
    assert d.route(job("w", model_id="wan22")) == "gpu0"
    d.mark_loaded(0, None)
    assert d.loaded(0) is None
    assert d.route(job("w", model_id="wan22")) == "gpu1"


def test_submit_respects_the_global_step_lock(d: GpuDispatcher, q: SqlJobQueue) -> None:
    assert d.submit(job("same")) == "gpu0"
    d.mark_loaded(3, "wan22")
    assert d.submit(job("same", model_id="wan22")) is None  # would route to gpu3, but the key is taken
    assert d.submit(job("same", resource=ResourceClass.CPU)) is None
    assert keys(q.pending()) == ["same"]
    assert q.pending("gpu3") == []


def test_a_sql_queue_is_never_scanned_job_by_job(tmp_path: Path) -> None:
    # Routing and claiming must cost one aggregate query, not a deserialisation of the whole backlog.
    q = PendingForbiddenQueueMock(make_engine(f"sqlite:///{tmp_path / 'queue.db'}"))
    q.create_schema()
    d = GpuDispatcher(q, gpus=4)
    d.mark_loaded(1, "wan22")
    for i in range(12):
        assert d.submit(job(f"j{i}", draft=i % 2 == 0, model_id="wan22" if i % 3 == 0 else None)) is not None
    assert q.queued_counts(d.gpu_queues) == {"gpu0": 3, "gpu1": 4, "gpu2": 3, "gpu3": 2}
    # gpu0: j1 j5 (finals) j10; gpu1: j3 j9 (finals) j0 j6; gpu2: j7 j11 (finals) j2; gpu3: j4 j8 (drafts only)
    order: list[str | None] = []
    for _ in range(4):
        for card in range(4):
            lease = d.claim_for(card, f"gpu{card}", T0, LEASE)
            order.append(lease.job.step_key if lease else None)
            if lease is not None:
                assert d.should_yield(lease) is False  # a started draft saw no final waiting
                q.complete(lease)
    assert order == ["j1", "j3", "j7", None, "j5", "j9", "j11", "j4", "j10", "j0", "j2", "j8", None, "j6", None, None]
    assert d.final_waiting() is False


# ------------------------------------------------------------------ priority


def test_effective_priority_puts_every_final_before_every_draft() -> None:
    assert effective_priority(job("f", priority=7)) == 7
    assert effective_priority(job("d", priority=7, draft=True)) == 7 + DRAFT_OFFSET
    worst_final = effective_priority(job("f", priority=DRAFT_OFFSET - 1))
    best_draft = effective_priority(job("d", priority=0, draft=True))
    assert worst_final < best_draft
    for bad in (-1, DRAFT_OFFSET, DRAFT_OFFSET + 5):
        with pytest.raises(ValueError, match="priority"):
            effective_priority(job("x", priority=bad))


def test_submit_refuses_an_out_of_range_priority(d: GpuDispatcher, q: SqlJobQueue) -> None:
    with pytest.raises(ValueError):
        d.submit(job("x", priority=DRAFT_OFFSET, draft=True))
    assert q.pending() == []


def test_a_final_passes_before_a_draft_submitted_earlier(d: GpuDispatcher, q: SqlJobQueue) -> None:
    assert d.submit(job("draft", priority=0, draft=True, resource=ResourceClass.CPU)) == "cpu"
    assert d.submit(job("final", priority=DRAFT_OFFSET - 1, resource=ResourceClass.CPU)) == "cpu"
    assert keys(q.pending("cpu")) == ["final", "draft"]
    first = q.claim("cpu", "cpu", T0, LEASE)
    second = q.claim("cpu", "cpu", T0, LEASE)
    assert first is not None and first.job.step_key == "final" and first.job.priority == DRAFT_OFFSET - 1
    assert second is not None and second.job.step_key == "draft" and second.job.priority == DRAFT_OFFSET
    assert second.job.draft is True


def test_claim_for_takes_the_final_of_its_own_queue_first(d: GpuDispatcher, q: SqlJobQueue) -> None:
    d.mark_loaded(0, "wan22")
    for key, draft in [("d1", True), ("d2", True), ("f1", False), ("d3", True), ("f2", False)]:
        assert d.submit(job(key, priority=1, draft=draft, model_id="wan22")) == "gpu0"
    order = []
    while (lease := d.claim_for(0, "gpu0", T0, LEASE)) is not None:
        order.append(lease.job.step_key)
        q.complete(lease)
    assert order == ["f1", "f2", "d1", "d2", "d3"]


def test_a_raw_enqueue_cannot_start_a_draft_before_a_final_of_its_queue(d: GpuDispatcher, q: SqlJobQueue) -> None:
    # A caller holding only the JobQueue protocol skips submit() and its priority offset.
    assert q.enqueue(job("draft", priority=0, draft=True), "gpu0")
    assert q.enqueue(job("final", priority=9), "gpu0")
    assert d.final_waiting() is True
    order = []
    while (lease := d.claim_for(0, "gpu0", T0, LEASE)) is not None:
        order.append(lease.job.step_key)
        q.complete(lease)
    assert order == ["final", "draft"]


def test_a_raw_enqueue_cannot_start_a_draft_while_a_final_waits_on_another_card(d: GpuDispatcher, q: SqlJobQueue) -> None:
    assert q.enqueue(job("draft", priority=0, draft=True), "gpu0")
    assert q.enqueue(job("final", priority=DRAFT_OFFSET - 1), "gpu1")
    assert d.claim_for(0, "gpu0", T0, LEASE) is None
    final = d.claim_for(1, "gpu1", T0, LEASE)
    assert final is not None and final.job.step_key == "final"
    draft = d.claim_for(0, "gpu0", T0, LEASE)
    assert draft is not None and draft.job.step_key == "draft" and draft.attempt == 1


# ------------------------------------------------------------------ cooperative preemption


def test_no_draft_starts_while_a_final_waits_on_another_card(d: GpuDispatcher, q: SqlJobQueue) -> None:
    d.mark_loaded(1, "wan22")
    assert d.submit(job("final", model_id="wan22")) == "gpu1"
    assert d.submit(job("draft", draft=True, priority=0)) == "gpu0"
    assert d.final_waiting() is True

    assert d.claim_for(0, "gpu0", T0, LEASE) is None
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.QUEUED, 0, 0)  # never started

    final = d.claim_for(1, "gpu1", T0, LEASE)
    assert final is not None and final.job.step_key == "final"
    assert d.final_waiting() is False  # a running final no longer blocks drafts
    draft = d.claim_for(0, "gpu0", T0, LEASE)
    assert draft is not None and draft.job.step_key == "draft" and draft.attempt == 1


def test_every_card_starts_its_own_final_when_finals_wait_on_all_cards(d: GpuDispatcher, q: SqlJobQueue) -> None:
    for card in range(4):
        d.mark_loaded(card, f"m{card}")
        assert d.submit(job(f"draft-{card}", draft=True, model_id=f"m{card}")) == f"gpu{card}"
        assert d.submit(job(f"final-{card}", model_id=f"m{card}")) == f"gpu{card}"
    started = [d.claim_for(card, f"gpu{card}", T0, LEASE) for card in range(4)]
    assert [(s.job.step_key, s.attempt) if s else None for s in started] == [(f"final-{c}", 1) for c in range(4)]
    for card in range(4):
        rec = q.record(f"final-{card}")
        assert rec is not None and (rec.status, rec.yields, rec.last_error) == (JobStatus.RUNNING, 0, None)
    drafts = [d.claim_for(card, f"gpu{card}", T0, LEASE) for card in range(4)]  # every final is running now
    assert [s.job.step_key if s else None for s in drafts] == [f"draft-{c}" for c in range(4)]


def test_a_final_never_yields_to_a_final_waiting_on_another_card(d: GpuDispatcher, q: SqlJobQueue) -> None:
    d.mark_loaded(0, "a")
    d.mark_loaded(1, "b")
    assert d.submit(job("fa", model_id="a")) == "gpu0"
    assert d.submit(job("fb", model_id="b")) == "gpu1"
    lease = d.claim_for(0, "gpu0", T0, LEASE)
    assert lease is not None and (lease.job.step_key, lease.attempt) == ("fa", 1)
    rec = q.record("fa")
    assert rec is not None and (rec.status, rec.yields, rec.last_error) == (JobStatus.RUNNING, 0, None)
    assert keys(q.pending()) == ["fb"]


def test_finals_waiting_outside_the_gpu_queues_do_not_block_gpu_drafts(d: GpuDispatcher, q: SqlJobQueue) -> None:
    # A human gate can wait for days: only finals waiting on a GPU card hold drafts back.
    assert d.submit(job("gate", resource=ResourceClass.HUMAN)) == "human"
    assert d.submit(job("mux", resource=ResourceClass.CPU)) == "cpu"
    assert d.submit(job("script", resource=ResourceClass.LLM)) == "llm"
    assert d.submit(job("draft", draft=True)) == "gpu0"
    assert d.final_waiting() is False
    lease = d.claim_for(0, "gpu0", T0, LEASE)
    assert lease is not None and (lease.job.step_key, lease.attempt) == ("draft", 1)
    assert d.should_yield(lease) is False


def test_claim_for_on_an_empty_card_returns_none(d: GpuDispatcher) -> None:
    assert d.claim_for(3, "gpu3", T0, LEASE) is None
    assert d.submit(job("f")) == "gpu0"
    assert d.claim_for(3, "gpu3", T0, LEASE) is None


def test_a_final_enqueued_before_the_claim_blocks_the_draft_without_starting_it(q: SqlJobQueue) -> None:
    # On a SqlJobQueue the check and the claim share one transaction: the draft is not even claimed.
    hooked = HookedSqlQueueMock(q, before_claim=lambda inner: inner.enqueue(job("late-final", priority=5), "gpu1"))
    d = GpuDispatcher(hooked, gpus=4)
    assert q.enqueue(job("draft", priority=DRAFT_OFFSET, draft=True), "gpu0")
    assert d.claim_for(0, "gpu0", T0, LEASE) is None
    assert hooked.claims == 1
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.attempt, rec.yields, rec.last_error) == (JobStatus.QUEUED, 0, 0, None)


def test_a_draft_handed_back_after_a_race_keeps_its_attempt_count(q: SqlJobQueue) -> None:
    # A final committed right after the draft's claim (the Postgres window): the draft is released, and
    # releasing it, however often, does not spend an attempt it never ran.
    finals = iter(range(5))

    def final_lands_on_gpu1(inner: SqlJobQueue) -> None:
        n = next(finals, None)
        if n is not None:
            assert inner.enqueue(job(f"final-{n}", priority=5), "gpu1")

    hooked = HookedSqlQueueMock(q, after_claim=final_lands_on_gpu1)
    d = GpuDispatcher(hooked, gpus=2)
    assert d.submit(job("draft", priority=0, draft=True)) == "gpu0"
    for n in range(5):
        assert d.claim_for(0, "gpu0", T0, LEASE) is None
        final = d.claim_for(1, "gpu1", T0, LEASE)  # the gpu1 worker starts the final that just arrived
        assert final is not None and (final.job.step_key, final.attempt) == (f"final-{n}", 1)
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.attempt, rec.yields, rec.executor_id) == (JobStatus.QUEUED, 0, 5, None)
    draft = d.claim_for(0, "gpu0", T0, LEASE)
    assert draft is not None and draft.job.step_key == "draft" and draft.attempt == 1


def test_a_draft_whose_claim_was_already_lost_is_not_released_twice(q: SqlJobQueue) -> None:
    def take_over_then_add_a_final(inner: SqlJobQueue) -> None:
        later = T0 + LEASE + dt.timedelta(seconds=1)
        assert inner.expire(later) == ["draft"]
        assert inner.claim("gpu0", "gpu0-heir", later, LEASE) is not None
        assert inner.enqueue(job("final", priority=5), "gpu1")

    hooked = HookedSqlQueueMock(q, after_claim=take_over_then_add_a_final)
    d = GpuDispatcher(hooked, gpus=2)
    assert d.submit(job("draft", draft=True)) == "gpu0"
    assert d.claim_for(0, "gpu0", T0, LEASE) is None
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.executor_id, rec.attempt, rec.yields) == (JobStatus.RUNNING, "gpu0-heir", 2, 0)


def test_on_a_protocol_only_queue_a_handed_back_draft_counts_an_attempt(q: SqlJobQueue) -> None:
    # Documented fallback: without `release`, the dispatcher yields through fail(retry=True).
    racing = ProtocolOnlyQueueMock(q, before_claim=lambda inner: inner.enqueue(job("late-final", priority=5), "gpu1"))
    d = GpuDispatcher(racing, gpus=4)
    assert q.enqueue(job("draft", priority=DRAFT_OFFSET, draft=True), "gpu0")

    assert d.claim_for(0, "gpu0", T0, LEASE) is None
    rec = q.record("draft")
    assert rec is not None
    assert (rec.status, rec.executor_id, rec.attempt, rec.last_error) == (JobStatus.QUEUED, None, 1, YIELD_REASON)

    assert d.claim_for(0, "gpu0", T0, LEASE) is None  # still blocked by the waiting final
    final = d.claim_for(1, "gpu1", T0, LEASE)
    assert final is not None and final.job.step_key == "late-final"
    draft = d.claim_for(0, "gpu0", T0, LEASE)
    assert draft is not None and draft.job.step_key == "draft" and draft.attempt == 2


def test_should_yield_tells_a_running_draft_to_stop(d: GpuDispatcher) -> None:
    d.submit(job("draft", draft=True))
    d.submit(job("final-a"))
    final = d.claim_for(1, "gpu1", T0, LEASE)  # gpu1 holds "final-a" (least loaded after gpu0)
    draft = d.claim_for(0, "gpu0", T0, LEASE)
    assert final is not None and final.job.step_key == "final-a"
    assert draft is not None and draft.job.step_key == "draft"
    assert d.should_yield(draft) is False
    d.mark_loaded(3, "wan22")
    assert d.submit(job("final-b", model_id="wan22")) == "gpu3"
    assert d.should_yield(draft) is True
    assert d.should_yield(final) is False


# ------------------------------------------------------------------ concurrency


def run_card_workers(d: GpuDispatcher, q: SqlJobQueue, expected: int, gpus: int = 4) -> tuple[list[str], list[str]]:
    """One thread per card claims through `d` until `expected` jobs are done. A draft started while a final
    is queued on any card is a violation (no final is enqueued during the run, so the check is exact)."""
    claimed: list[str] = []
    violations: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()
    deadline = time.monotonic() + 30

    def card_worker(card: int) -> None:
        try:
            while time.monotonic() < deadline:
                with lock:
                    if len(claimed) == expected:
                        return
                lease = d.claim_for(card, f"gpu{card}", T0, LEASE)
                if lease is None:
                    time.sleep(0.002)
                    continue
                if lease.job.draft:
                    waiting = [j.step_key for c in range(gpus) for j in q.pending(gpu_queue(c)) if not j.draft]
                    if waiting:
                        with lock:
                            violations.append(f"{lease.job.step_key} on gpu{card} while {waiting} waited")
                else:
                    time.sleep(0.005)  # a final takes a while: drafts elsewhere must keep waiting
                q.complete(lease)
                with lock:
                    claimed.append(lease.job.step_key)
        except BaseException as exc:  # reported below
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=card_worker, args=(c,)) for c in range(gpus)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    return claimed, violations


def submit_finals_on_several_cards(d: GpuDispatcher, q: SqlJobQueue) -> list[str]:
    """14 finals on gpu0, gpu1 and gpu3 (model affinity), then 24 drafts spread over every card."""
    d.mark_loaded(0, "m0")
    d.mark_loaded(1, "m1")
    d.mark_loaded(3, "m3")
    submitted = []
    for model, n in [("m0", 3), ("m1", 3), ("m3", 8)]:
        for i in range(n):
            key = f"final-{model}-{i}"
            assert d.submit(job(key, priority=i, model_id=model)) == f"gpu{model[1]}"
            submitted.append(key)
    for i in range(24):
        assert d.submit(job(f"draft-{i:02d}", priority=0, draft=True, model_id="draft-model")) is not None
        submitted.append(f"draft-{i:02d}")
    finals_on = {c for c in range(4) if any(not j.draft for j in q.pending(gpu_queue(c)))}
    drafts_on = {c for c in range(4) if any(j.draft for j in q.pending(gpu_queue(c)))}
    assert finals_on == {0, 1, 3} and drafts_on == {0, 1, 2, 3}
    return submitted


def test_four_card_workers_with_finals_on_several_cards(d: GpuDispatcher, q: SqlJobQueue) -> None:
    submitted = submit_finals_on_several_cards(d, q)
    claimed, violations = run_card_workers(d, q, len(submitted))
    assert violations == []
    counts = Counter(claimed)
    assert sorted(counts) == sorted(submitted) and set(counts.values()) == {1}
    for key in submitted:
        rec = q.record(key)
        assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.DONE, 1, 0), key


def test_four_card_workers_never_start_a_draft_while_a_final_waits(d: GpuDispatcher, q: SqlJobQueue) -> None:
    d.mark_loaded(3, "final-model")
    n_finals, n_drafts = 12, 24
    for i in range(n_finals):
        assert d.submit(job(f"final-{i:02d}", model_id="final-model")) == "gpu3"
    for i in range(n_drafts):
        assert d.submit(job(f"draft-{i:02d}", draft=True, model_id="draft-model")) is not None
    assert all(len(q.pending(gpu_queue(c))) > 0 for c in range(3))
    claimed, violations = run_card_workers(d, q, n_finals + n_drafts)
    assert violations == []
    counts = Counter(claimed)
    assert len(counts) == n_finals + n_drafts and set(counts.values()) == {1}


# ------------------------------------------------------------------ validation


def test_card_indices_and_gpu_count_are_checked(q: SqlJobQueue, mode: str) -> None:
    with pytest.raises(ValueError, match="gpus"):
        dispatcher(q, mode, gpus=0)
    d = dispatcher(q, mode, gpus=2)
    assert d.gpu_queues == ("gpu0", "gpu1")
    for bad in (-1, 2):
        with pytest.raises(ValueError, match="card"):
            d.mark_loaded(bad, "m")
        with pytest.raises(ValueError, match="card"):
            d.claim_for(bad, "gpu", T0, LEASE)
        with pytest.raises(ValueError, match="card"):
            d.loaded(bad)
    assert d.submit(job("a")) == "gpu0"
    assert d.submit(job("b")) == "gpu1"
    assert d.submit(job("c")) == "gpu0"


# ------------------------------------------------------------------ test doubles


class ProtocolOnlyQueueMock:
    """Delegates the seven JobQueue methods to a real queue and exposes nothing else, so the dispatcher
    takes its `pending()`-scanning path. `before_claim` runs right before each claim (a racing enqueue)."""

    def __init__(self, inner: SqlJobQueue, before_claim: Callable[[SqlJobQueue], object] | None = None) -> None:
        self.inner = inner
        self.before_claim = before_claim

    def enqueue(self, job: Job, queue: str) -> bool:
        return self.inner.enqueue(job, queue)

    def claim(self, queue: str, executor_id: str, now: dt.datetime, lease: dt.timedelta) -> Lease | None:
        if self.before_claim is not None:
            hook, self.before_claim = self.before_claim, None
            hook(self.inner)
        return self.inner.claim(queue, executor_id, now, lease)

    def heartbeat(self, lease: Lease, now: dt.datetime, extend: dt.timedelta) -> Lease:
        return self.inner.heartbeat(lease, now, extend)

    def complete(self, lease: Lease) -> None:
        self.inner.complete(lease)

    def fail(self, lease: Lease, error: str, retry: bool) -> None:
        self.inner.fail(lease, error, retry)

    def expire(self, now: dt.datetime) -> list[str]:
        return self.inner.expire(now)

    def pending(self, queue: str | None = None) -> list[Job]:
        return self.inner.pending(queue)


class HookedSqlQueueMock(SqlJobQueue):
    """A real SqlJobQueue on the same database whose claims on `gpu0` run a hook just before and/or just
    after the claim transaction, to reproduce an enqueue racing the dispatcher's claim."""

    def __init__(
        self,
        inner: SqlJobQueue,
        before_claim: Callable[[SqlJobQueue], object] | None = None,
        after_claim: Callable[[SqlJobQueue], object] | None = None,
    ) -> None:
        super().__init__(inner._engine)
        self.inner = inner
        self.before_claim = before_claim
        self.after_claim = after_claim
        self.claims = 0

    def claim(
        self,
        queue: str,
        executor_id: str,
        now: dt.datetime,
        lease: dt.timedelta,
        *,
        drafts_blocked_by: Sequence[str] = (),
    ) -> Lease | None:
        if queue != "gpu0":
            return super().claim(queue, executor_id, now, lease, drafts_blocked_by=drafts_blocked_by)
        self.claims += 1
        if self.before_claim is not None:
            self.before_claim(self.inner)
        claimed = super().claim(queue, executor_id, now, lease, drafts_blocked_by=drafts_blocked_by)
        if claimed is not None and self.after_claim is not None:
            self.after_claim(self.inner)
        return claimed


class PendingForbiddenQueueMock(SqlJobQueue):
    """A real SqlJobQueue whose `pending()` fails the test: proves the dispatcher never scans it."""

    def pending(self, queue: str | None = None) -> list[Job]:
        raise AssertionError(f"pending({queue!r}) scanned the backlog")


def test_the_protocol_only_double_really_hides_the_extensions(q: SqlJobQueue) -> None:
    double = ProtocolOnlyQueueMock(q)
    assert isinstance(double, JobQueue)
    assert not hasattr(double, "release") and not hasattr(double, "queued_counts")
