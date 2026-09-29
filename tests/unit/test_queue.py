"""SqlJobQueue on SQLite: global step lock, priority, leases, fencing, expiry, concurrent claims."""

from __future__ import annotations

import datetime as dt
import threading
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text, update

from studio.core.db import make_engine
from studio.core.interfaces import Job, JobQueue, Lease, StepClaimed
from studio.core.queue import CLAIM_ROUNDS, JobStatus, SqlJobQueue, step_claims
from studio.domain import ResourceClass

T0 = dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.UTC)
LEASE = dt.timedelta(seconds=30)


def job(key: str, priority: int = 0, **kw: object) -> Job:
    base: dict[str, object] = dict(step_key=key, step_name="render_shot", run_id="run-1", resource=ResourceClass.GPU)
    base.update(kw)
    return Job(priority=priority, **base)  # type: ignore[arg-type]


@pytest.fixture
def q(tmp_path: Path) -> SqlJobQueue:
    queue = SqlJobQueue(make_engine(f"sqlite:///{tmp_path / 'queue.db'}"))
    queue.create_schema()
    return queue


def drain(q: SqlJobQueue, queue: str) -> list[str]:
    keys: list[str] = []
    while (lease := q.claim(queue, "w", T0, LEASE)) is not None:
        keys.append(lease.job.step_key)
    return keys


# ------------------------------------------------------------------ basics


def test_implements_the_jobqueue_protocol(q: SqlJobQueue) -> None:
    assert isinstance(q, JobQueue)


def test_create_schema_is_idempotent(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    q.create_schema()
    assert [j.step_key for j in q.pending("gpu0")] == ["a"]


def test_claim_returns_the_job_intact_with_a_lease(q: SqlJobQueue) -> None:
    original = Job(
        step_key="k" * 64,
        step_name="animate",
        run_id="run-7",
        resource=ResourceClass.GPU,
        priority=12,
        payload={"prompt": "a lighthouse", "seeds": [1, 2], "nested": {"fps": 24}},
        model_id="wan22-ti2v-5b",
        draft=True,
        timeout_s=90.5,
    )
    assert q.enqueue(original, "gpu2")
    lease = q.claim("gpu2", "gpu2", T0, LEASE)
    assert lease == Lease(job=original, executor_id="gpu2", queue="gpu2", attempt=1, lease_until=T0 + LEASE)
    rec = q.record(original.step_key)
    assert rec is not None
    assert (rec.status, rec.executor_id, rec.attempt, rec.lease_until) == (JobStatus.RUNNING, "gpu2", 1, T0 + LEASE)


def test_claim_on_an_empty_or_other_queue_returns_none(q: SqlJobQueue) -> None:
    assert q.claim("gpu0", "w", T0, LEASE) is None
    assert q.enqueue(job("a"), "gpu1")
    assert q.claim("gpu0", "w", T0, LEASE) is None
    assert q.claim("cpu", "w", T0, LEASE) is None
    claimed = q.claim("gpu1", "w", T0, LEASE)
    assert claimed is not None and claimed.job.step_key == "a"
    assert q.claim("gpu1", "w", T0, LEASE) is None  # running jobs are not claimable


def test_record_of_an_unknown_key_is_none(q: SqlJobQueue) -> None:
    assert q.record("nope") is None


# ------------------------------------------------------------------ global dedup


def test_a_step_key_is_queued_once_across_all_queues(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0") is True
    for queue in ("gpu0", "gpu1", "gpu3", "cpu", "llm", "human"):
        assert q.enqueue(job("a", priority=0, draft=True), queue) is False
    assert [j.step_key for j in q.pending()] == ["a"]
    assert q.pending("gpu1") == []
    rec = q.record("a")
    assert rec is not None and rec.queue == "gpu0" and rec.job.draft is False  # the first enqueue is untouched


def test_a_running_step_key_cannot_be_enqueued_anywhere(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    assert q.claim("gpu0", "w", T0, LEASE) is not None
    for queue in ("gpu0", "gpu1", "cpu"):
        assert q.enqueue(job("a"), queue) is False
    assert q.pending() == []


def test_concurrent_enqueues_of_one_key_on_eight_queues_admit_exactly_one(q: SqlJobQueue) -> None:
    barrier = threading.Barrier(8)
    results: list[bool] = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        barrier.wait()
        ok = q.enqueue(job("same"), f"queue{i}")
        with lock:
            results.append(ok)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [False] * 7 + [True]
    assert len(q.pending()) == 1


# ------------------------------------------------------------------ re-enqueue after the end


def test_a_done_job_is_requeued_with_the_new_job_and_queue(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a", priority=5, payload={"v": 1}), "gpu0")
    first = q.claim("gpu0", "gpu0", T0, LEASE)
    assert first is not None
    q.complete(first)
    rec = q.record("a")
    assert rec is not None and rec.status is JobStatus.DONE and rec.lease_until is None

    assert q.enqueue(job("a", priority=2, payload={"v": 2}), "gpu3") is True
    assert q.pending("gpu0") == []
    again = q.claim("gpu3", "gpu3", T0, LEASE)
    assert again is not None
    assert again.job.payload == {"v": 2} and again.job.priority == 2
    assert again.attempt == 2  # attempts never restart: (executor, attempt) is never reused
    with pytest.raises(StepClaimed):
        q.complete(first)  # a lease of the previous generation stays dead


def test_a_failed_job_can_be_requeued(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "cpu")
    lease = q.claim("cpu", "cpu", T0, LEASE)
    assert lease is not None
    q.fail(lease, "ffmpeg exited 1", retry=False)
    assert q.enqueue(job("a"), "cpu") is True
    rec = q.record("a")
    assert rec is not None and rec.status is JobStatus.QUEUED and rec.last_error is None


def test_a_requeued_done_job_goes_behind_older_jobs_of_equal_priority(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    q.complete(lease)
    assert q.enqueue(job("b"), "gpu0")
    assert q.enqueue(job("a"), "gpu0")
    assert drain(q, "gpu0") == ["b", "a"]


# ------------------------------------------------------------------ order


def test_claim_takes_the_lowest_priority_value_first(q: SqlJobQueue) -> None:
    for key, prio in [("p5", 5), ("p1", 1), ("p3", 3), ("p0", 0), ("big", 2_000_000)]:
        assert q.enqueue(job(key, priority=prio), "gpu0")
    assert [j.step_key for j in q.pending("gpu0")] == ["p0", "p1", "p3", "p5", "big"]
    assert drain(q, "gpu0") == ["p0", "p1", "p3", "p5", "big"]


def test_equal_priorities_are_claimed_oldest_first_not_by_key(q: SqlJobQueue) -> None:
    for key in ["zz", "aa", "mm", "bb"]:
        assert q.enqueue(job(key, priority=7), "cpu")
    assert drain(q, "cpu") == ["zz", "aa", "mm", "bb"]


def test_pending_lists_only_queued_jobs_in_claim_order(q: SqlJobQueue) -> None:
    assert q.enqueue(job("g0", priority=3), "gpu0")
    assert q.enqueue(job("c", priority=1), "cpu")
    assert q.enqueue(job("g1", priority=2), "gpu0")
    assert q.enqueue(job("run", priority=0), "gpu0")
    assert q.claim("gpu0", "w", T0, LEASE) is not None  # takes "run"
    assert [j.step_key for j in q.pending("gpu0")] == ["g1", "g0"]
    assert [j.step_key for j in q.pending()] == ["c", "g1", "g0"]
    assert q.pending("llm") == []


def test_a_retried_job_keeps_its_place(q: SqlJobQueue) -> None:
    for key in ["first", "second"]:
        assert q.enqueue(job(key), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None and lease.job.step_key == "first"
    q.fail(lease, "CUDA out of memory", retry=True)
    rec = q.record("first")
    assert rec is not None
    assert (rec.status, rec.executor_id, rec.lease_until, rec.last_error) == (JobStatus.QUEUED, None, None, "CUDA out of memory")
    retried = q.claim("gpu0", "w", T0, LEASE)
    assert retried is not None and retried.job.step_key == "first" and retried.attempt == 2


# ------------------------------------------------------------------ complete / fail


def test_complete_marks_done_and_is_idempotent_for_the_same_lease(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    q.complete(lease)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.executor_id, rec.attempt) == (JobStatus.DONE, "w", 1)
    assert q.pending() == []
    assert q.claim("gpu0", "w", T0, LEASE) is None
    q.complete(lease)  # a retry after an uncertain commit: the step is already done by this very lease
    again = q.record("a")
    assert again is not None and (again.status, again.executor_id, again.attempt) == (JobStatus.DONE, "w", 1)
    # Only a repeated end of the same kind is a no-op; anything else by this lease is refused.
    with pytest.raises(StepClaimed, match="no longer live"):
        q.fail(lease, "late", retry=True)
    with pytest.raises(StepClaimed, match="no longer live"):
        q.fail(lease, "late", retry=False)
    with pytest.raises(StepClaimed):
        q.heartbeat(lease, T0, LEASE)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.last_error) == (JobStatus.DONE, None)


def test_a_repeated_complete_by_another_or_older_lease_is_refused(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    q.complete(lease)
    for forged in (replace(lease, executor_id="other"), replace(lease, attempt=lease.attempt + 1)):
        with pytest.raises(StepClaimed):
            q.complete(forged)
    assert q.enqueue(job("a"), "gpu0")  # a new generation of the step
    with pytest.raises(StepClaimed, match="queued"):
        q.complete(lease)
    newer = q.claim("gpu0", "w", T0, LEASE)
    assert newer is not None and newer.attempt == 2
    with pytest.raises(StepClaimed, match="running"):
        q.complete(lease)  # same executor, older attempt
    q.complete(newer)
    q.complete(newer)
    with pytest.raises(StepClaimed):
        q.complete(lease)


def test_fail_without_retry_is_idempotent_for_the_same_lease(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "cpu")
    lease = q.claim("cpu", "cpu", T0, LEASE)
    assert lease is not None
    q.fail(lease, "unsupported codec", retry=False)
    q.fail(lease, "unsupported codec (retried call)", retry=False)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.last_error, rec.attempt) == (JobStatus.FAILED, "unsupported codec", 1)
    with pytest.raises(StepClaimed, match="failed"):
        q.complete(lease)
    with pytest.raises(StepClaimed):
        q.fail(replace(lease, executor_id="other"), "x", retry=False)


def test_a_retried_fail_is_not_idempotent(q: SqlJobQueue) -> None:
    # fail(retry=True) hands the job back to the queue: the lease is dead at once, as after an expiry.
    assert q.enqueue(job("a"), "cpu")
    lease = q.claim("cpu", "cpu", T0, LEASE)
    assert lease is not None
    q.fail(lease, "transient", retry=True)
    with pytest.raises(StepClaimed, match="queued"):
        q.fail(lease, "transient", retry=True)
    with pytest.raises(StepClaimed):
        q.complete(lease)


def test_fail_without_retry_is_terminal(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    q.fail(lease, "unsupported resolution", retry=False)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.last_error, rec.lease_until) == (JobStatus.FAILED, "unsupported resolution", None)
    assert q.claim("gpu0", "w", T0, LEASE) is None
    assert q.pending() == []
    assert q.expire(T0 + dt.timedelta(days=1)) == []


# ------------------------------------------------------------------ leases, expiry, fencing


def test_heartbeat_extends_the_lease_and_protects_it_from_expiry(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, dt.timedelta(seconds=10))
    assert lease is not None
    renewed = q.heartbeat(lease, T0 + dt.timedelta(seconds=8), dt.timedelta(seconds=10))
    assert renewed.lease_until == T0 + dt.timedelta(seconds=18)
    assert (renewed.job, renewed.attempt, renewed.executor_id) == (lease.job, lease.attempt, lease.executor_id)
    assert q.expire(T0 + dt.timedelta(seconds=15)) == []
    rec = q.record("a")
    assert rec is not None and rec.status is JobStatus.RUNNING and rec.lease_until == T0 + dt.timedelta(seconds=18)
    q.complete(renewed)  # the renewed lease and the original share the same fencing token
    rec = q.record("a")
    assert rec is not None and rec.status is JobStatus.DONE


def test_heartbeat_sets_the_deadline_to_now_plus_extend_even_when_earlier(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, dt.timedelta(minutes=10))
    assert lease is not None
    shortened = q.heartbeat(lease, T0 + dt.timedelta(seconds=1), dt.timedelta(seconds=2))
    assert shortened.lease_until == T0 + dt.timedelta(seconds=3)
    rec = q.record("a")
    assert rec is not None and rec.lease_until == T0 + dt.timedelta(seconds=3)
    assert q.expire(T0 + dt.timedelta(seconds=4)) == ["a"]


def test_expire_requeues_only_running_jobs_past_their_lease(q: SqlJobQueue) -> None:
    for key in ["short", "long", "finished", "waiting"]:
        assert q.enqueue(job(key), "gpu0")
    q.claim("gpu0", "w1", T0, dt.timedelta(seconds=10))  # "short"
    q.claim("gpu0", "w2", T0, dt.timedelta(seconds=60))  # "long"
    finished = q.claim("gpu0", "w3", T0, dt.timedelta(seconds=1))
    assert finished is not None and finished.job.step_key == "finished"
    q.complete(finished)
    assert q.expire(T0 + dt.timedelta(seconds=10)) == []  # a lease is valid up to and including its deadline
    assert q.expire(T0 + dt.timedelta(seconds=10, microseconds=1)) == ["short"]
    rec = q.record("short")
    assert rec is not None
    assert (rec.status, rec.executor_id, rec.lease_until) == (JobStatus.QUEUED, None, None)
    assert rec.last_error == "lease expired (executor w1, attempt 1)"
    long_rec = q.record("long")
    assert long_rec is not None and long_rec.status is JobStatus.RUNNING
    assert q.expire(T0 + dt.timedelta(seconds=10, microseconds=1)) == []  # idempotent
    assert q.expire(T0 + dt.timedelta(hours=1)) == ["long"]
    assert [j.step_key for j in q.pending("gpu0")] == ["short", "long", "waiting"]
    done = q.record("finished")
    assert done is not None and done.status is JobStatus.DONE


def test_an_expired_job_is_reclaimable_with_attempt_plus_one(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu1")
    first = q.claim("gpu1", "gpu1", T0, LEASE)
    assert first is not None and first.attempt == 1
    assert q.expire(T0 + LEASE + dt.timedelta(seconds=1)) == ["a"]
    second = q.claim("gpu1", "gpu1", T0 + dt.timedelta(minutes=1), LEASE)
    assert second is not None and second.attempt == 2 and second.job == first.job


def test_a_dead_executor_cannot_touch_the_job_of_its_replacement(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    dead = q.claim("gpu0", "gpu0-old", T0, dt.timedelta(seconds=10))
    assert dead is not None
    assert q.expire(T0 + dt.timedelta(seconds=11)) == ["a"]
    heir = q.claim("gpu0", "gpu0-new", T0 + dt.timedelta(seconds=12), dt.timedelta(seconds=10))
    assert heir is not None and heir.attempt == 2

    with pytest.raises(StepClaimed):
        q.heartbeat(dead, T0 + dt.timedelta(seconds=13), LEASE)
    with pytest.raises(StepClaimed):
        q.complete(dead)
    with pytest.raises(StepClaimed):
        q.fail(dead, "zombie", retry=False)
    rec = q.record("a")
    assert rec is not None
    assert (rec.status, rec.executor_id, rec.attempt) == (JobStatus.RUNNING, "gpu0-new", 2)
    assert rec.lease_until == T0 + dt.timedelta(seconds=22)  # the zombie heartbeat changed nothing

    heir = q.heartbeat(heir, T0 + dt.timedelta(seconds=20), LEASE)
    q.complete(heir)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.executor_id) == (JobStatus.DONE, "gpu0-new")


def test_a_restarted_worker_with_the_same_id_is_fenced_by_attempt(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    before = q.claim("gpu0", "gpu0", T0, dt.timedelta(seconds=10))
    assert before is not None
    assert q.expire(T0 + dt.timedelta(minutes=1)) == ["a"]
    after = q.claim("gpu0", "gpu0", T0 + dt.timedelta(minutes=1), LEASE)
    assert after is not None and after.attempt == 2
    with pytest.raises(StepClaimed):
        q.complete(before)
    q.complete(after)


def test_a_forged_lease_with_another_executor_is_rejected(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    real = q.claim("gpu0", "gpu0", T0, LEASE)
    assert real is not None
    for forged in (
        Lease(job=real.job, executor_id="gpu1", queue="gpu0", attempt=real.attempt, lease_until=real.lease_until),
        Lease(job=real.job, executor_id="gpu0", queue="gpu0", attempt=real.attempt + 1, lease_until=real.lease_until),
    ):
        with pytest.raises(StepClaimed):
            q.heartbeat(forged, T0, LEASE)
        with pytest.raises(StepClaimed):
            q.complete(forged)
    unknown = Lease(job=job("ghost"), executor_id="gpu0", queue="gpu0", attempt=1, lease_until=T0)
    with pytest.raises(StepClaimed, match="absent"):
        q.complete(unknown)
    q.complete(real)


def test_a_late_heartbeat_revives_a_lease_that_was_not_yet_expired_by_the_reaper(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, dt.timedelta(seconds=10))
    assert lease is not None
    renewed = q.heartbeat(lease, T0 + dt.timedelta(seconds=20), dt.timedelta(seconds=10))
    assert q.expire(T0 + dt.timedelta(seconds=25)) == []
    q.complete(renewed)


def test_datetimes_are_compared_in_utc_whatever_their_offset(q: SqlJobQueue) -> None:
    paris = dt.timezone(dt.timedelta(hours=2))
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0.astimezone(paris), dt.timedelta(seconds=10))
    assert lease is not None and lease.lease_until == T0 + dt.timedelta(seconds=10)
    assert lease.lease_until.utcoffset() == dt.timedelta(0)
    new_york = dt.timezone(dt.timedelta(hours=-4))
    assert q.expire((T0 + dt.timedelta(seconds=5)).astimezone(new_york)) == []
    assert q.expire((T0 + dt.timedelta(seconds=11)).astimezone(new_york)) == ["a"]


# ------------------------------------------------------------------ finals before drafts


def test_finals_are_claimed_before_drafts_whatever_their_priority(q: SqlJobQueue) -> None:
    # Enqueued straight through the JobQueue protocol, without the dispatcher's priority offset.
    for key, prio, draft in [("d0", 0, True), ("f9", 9, False), ("d1", 1, True), ("f-big", 2_000_000, False)]:
        assert q.enqueue(job(key, priority=prio, draft=draft), "gpu0")
    assert [j.step_key for j in q.pending("gpu0")] == ["f9", "f-big", "d0", "d1"]
    assert [j.step_key for j in q.pending()] == ["f9", "f-big", "d0", "d1"]
    assert drain(q, "gpu0") == ["f9", "f-big", "d0", "d1"]


def test_a_requeued_step_takes_the_draft_flag_of_its_new_job(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    q.complete(lease)
    assert q.enqueue(job("a", priority=0, draft=True), "gpu0")
    assert q.enqueue(job("b", priority=50), "gpu0")
    assert drain(q, "gpu0") == ["b", "a"]


# ------------------------------------------------------------------ release


def test_release_hands_a_claim_back_without_counting_an_attempt(q: SqlJobQueue) -> None:
    for key in ["a", "b"]:
        assert q.enqueue(job(key, draft=True), "gpu0")
    lease = q.claim("gpu0", "gpu0", T0, LEASE)
    assert lease is not None and (lease.job.step_key, lease.attempt) == ("a", 1)
    q.release(lease)
    rec = q.record("a")
    assert rec is not None
    assert (rec.status, rec.attempt, rec.yields, rec.executor_id, rec.lease_until) == (JobStatus.QUEUED, 0, 1, None, None)
    with pytest.raises(StepClaimed):
        q.heartbeat(lease, T0, LEASE)
    with pytest.raises(StepClaimed):
        q.release(lease)
    again = q.claim("gpu0", "gpu0", T0, LEASE)
    assert again is not None and (again.job.step_key, again.attempt) == ("a", 1)  # same place, first real attempt
    q.complete(again)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.attempt, rec.yields) == (JobStatus.DONE, 1, 1)


def test_release_keeps_the_error_of_a_real_failure(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    first = q.claim("gpu0", "w", T0, LEASE)
    assert first is not None
    q.fail(first, "CUDA out of memory", retry=True)
    second = q.claim("gpu0", "w", T0, LEASE)
    assert second is not None and second.attempt == 2
    q.release(second)
    rec = q.record("a")
    assert rec is not None and (rec.attempt, rec.yields, rec.last_error) == (1, 1, "CUDA out of memory")


def test_release_of_a_lease_that_was_taken_over_is_refused(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    old = q.claim("gpu0", "old", T0, dt.timedelta(seconds=5))
    assert old is not None
    assert q.expire(T0 + dt.timedelta(seconds=6)) == ["a"]
    heir = q.claim("gpu0", "heir", T0 + dt.timedelta(seconds=6), LEASE)
    assert heir is not None and heir.attempt == 2
    with pytest.raises(StepClaimed):
        q.release(old)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.executor_id, rec.attempt, rec.yields) == (JobStatus.RUNNING, "heir", 2, 0)


# ------------------------------------------------------------------ set-based reads and guarded claim


def test_queued_counts_count_only_waiting_jobs(q: SqlJobQueue) -> None:
    for key, queue in [("a", "gpu0"), ("b", "gpu0"), ("c", "gpu0"), ("d", "gpu2"), ("e", "cpu")]:
        assert q.enqueue(job(key), queue)
    assert q.claim("gpu0", "w", T0, LEASE) is not None  # "a" runs
    done = q.claim("cpu", "w", T0, LEASE)
    assert done is not None
    q.complete(done)
    assert q.queued_counts(["gpu0", "gpu1", "gpu2", "cpu"]) == {"gpu0": 2, "gpu1": 0, "gpu2": 1, "cpu": 0}
    assert q.queued_counts() == {"gpu0": 2, "gpu2": 1}
    assert q.queued_counts([]) == {}


def test_final_queued_sees_only_waiting_finals_of_the_given_queues(q: SqlJobQueue) -> None:
    assert q.final_queued(["gpu0"]) is False
    assert q.enqueue(job("draft", draft=True), "gpu0")
    assert q.enqueue(job("human-gate"), "human")
    assert q.final_queued(["gpu0", "gpu1"]) is False
    assert q.final_queued(["human"]) is True
    assert q.enqueue(job("final"), "gpu1")
    assert q.final_queued(["gpu0", "gpu1"]) is True
    assert q.final_queued(["gpu0"]) is False
    assert q.final_queued([]) is False
    assert q.claim("gpu1", "w", T0, LEASE) is not None  # a running final no longer waits
    assert q.final_queued(["gpu0", "gpu1"]) is False


def test_a_guarded_claim_starts_no_draft_while_a_final_waits(q: SqlJobQueue) -> None:
    gpus = ["gpu0", "gpu1"]
    assert q.enqueue(job("draft", draft=True), "gpu0")
    assert q.enqueue(job("final-elsewhere"), "gpu1")
    assert q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus) is None
    rec = q.record("draft")
    assert rec is not None and (rec.status, rec.attempt) == (JobStatus.QUEUED, 0)
    assert q.enqueue(job("final-here", priority=99), "gpu0")
    own = q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus)
    assert own is not None and own.job.step_key == "final-here"  # the queue's own finals still pass
    assert q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=gpus) is None
    assert q.claim("gpu0", "w", T0, LEASE, drafts_blocked_by=["cpu"]) is not None  # only the listed queues block


# ------------------------------------------------------------------ engines that do not serialise writers


def claim_all_concurrently(q: SqlJobQueue, queue: str, n_threads: int = 8) -> tuple[list[str], list[BaseException]]:
    """`n_threads` workers claim `queue` until it is empty; returns the claimed keys and the errors raised."""
    barrier = threading.Barrier(n_threads)
    claimed: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        try:
            barrier.wait()
            while (lease := q.claim(queue, f"w{i}", T0, LEASE)) is not None:
                with lock:
                    claimed.append(lease.job.step_key)
        except BaseException as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return claimed, errors


def test_claims_on_a_plain_sqlite_engine_retry_lost_races_instead_of_failing(tmp_path: Path) -> None:
    # Without make_engine's BEGIN IMMEDIATE hook, two claimers can select the same row; the loser must
    # select again rather than crash.
    n_jobs = 120
    for round_ in range(3):
        engine = create_engine(f"sqlite:///{tmp_path / f'plain-{round_}.db'}")
        plain = SqlJobQueue(engine)
        plain.create_schema()
        for i in range(n_jobs):
            assert plain.enqueue(job(f"job-{i:03d}", priority=i % 5), "gpu0")
        claimed, errors = claim_all_concurrently(plain, "gpu0")
        engine.dispose()
        assert errors == []
        assert sorted(claimed) == [f"job-{i:03d}" for i in range(n_jobs)]


def test_a_claim_that_keeps_losing_races_gives_up_after_a_bounded_number_of_rounds(q: SqlJobQueue, tmp_path: Path) -> None:
    assert q.enqueue(job("a"), "gpu0")
    engine = make_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    with engine.begin() as conn:  # every claim update now changes nothing, as if another claimer always won
        conn.execute(
            text(
                "CREATE TRIGGER always_lose BEFORE UPDATE OF status ON step_claims "
                "WHEN NEW.status = 'running' BEGIN SELECT RAISE(IGNORE); END"
            )
        )
    with pytest.raises(RuntimeError, match=f"lost {CLAIM_ROUNDS} races"):
        q.claim("gpu0", "w", T0, LEASE)
    rec = q.record("a")
    assert rec is not None and (rec.status, rec.attempt) == (JobStatus.QUEUED, 0)


# ------------------------------------------------------------------ validation


def test_naive_datetimes_are_refused(q: SqlJobQueue) -> None:
    assert q.enqueue(job("a"), "gpu0")
    naive = dt.datetime(2026, 9, 28, 12, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        q.claim("gpu0", "w", naive, LEASE)
    with pytest.raises(ValueError, match="timezone-aware"):
        q.expire(naive)
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    with pytest.raises(ValueError, match="timezone-aware"):
        q.heartbeat(lease, naive, LEASE)


def test_invalid_arguments_are_refused(q: SqlJobQueue) -> None:
    with pytest.raises(ValueError, match="queue"):
        q.enqueue(job("a"), "")
    with pytest.raises(ValueError, match="step_key"):
        q.enqueue(job(""), "gpu0")
    with pytest.raises(ValueError, match="JSON"):
        q.enqueue(job("b", payload={"path": Path("/tmp/x")}), "gpu0")
    with pytest.raises(ValueError, match="JSON"):
        q.enqueue(job("c", payload={"score": float("nan")}), "gpu0")
    assert q.pending() == []
    assert q.enqueue(job("a"), "gpu0")
    with pytest.raises(ValueError, match="lease"):
        q.claim("gpu0", "w", T0, dt.timedelta(0))
    with pytest.raises(ValueError, match="executor_id"):
        q.claim("gpu0", "", T0, LEASE)
    lease = q.claim("gpu0", "w", T0, LEASE)
    assert lease is not None
    with pytest.raises(ValueError, match="extend"):
        q.heartbeat(lease, T0, dt.timedelta(seconds=-1))


def test_the_database_refuses_a_running_row_without_a_lease(q: SqlJobQueue, tmp_path: Path) -> None:
    from sqlalchemy.exc import IntegrityError

    assert q.enqueue(job("a"), "gpu0")
    engine = make_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(update(step_claims).where(step_claims.c.step_key == "a").values(status="running"))
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(update(step_claims).where(step_claims.c.step_key == "a").values(status="paused"))


# ------------------------------------------------------------------ concurrency


def test_eight_threads_claiming_one_queue_never_get_the_same_job(q: SqlJobQueue) -> None:
    n_jobs = 120
    for i in range(n_jobs):
        assert q.enqueue(job(f"job-{i:03d}", priority=i % 5), "gpu0")
    barrier = threading.Barrier(8)
    claimed: list[tuple[str, str]] = []
    lock = threading.Lock()
    errors: list[BaseException] = []

    def worker(i: int) -> None:
        try:
            barrier.wait()
            while (lease := q.claim("gpu0", f"w{i}", T0, LEASE)) is not None:
                with lock:
                    claimed.append((lease.job.step_key, lease.executor_id))
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    counts = Counter(key for key, _ in claimed)
    assert len(claimed) == n_jobs
    assert set(counts.values()) == {1}
    for key, executor in claimed:
        rec = q.record(key)
        assert rec is not None and rec.executor_id == executor and rec.attempt == 1
    assert len({executor for _, executor in claimed}) > 1  # the claims really were spread over threads


def test_concurrent_workers_complete_every_job_exactly_once_despite_retries(q: SqlJobQueue) -> None:
    n_jobs = 60
    for i in range(n_jobs):
        assert q.enqueue(job(f"job-{i:02d}"), "cpu")
    completions: list[str] = []
    lock = threading.Lock()
    failed_once: set[str] = set()

    def worker(i: int) -> None:
        while (lease := q.claim("cpu", f"w{i}", T0, LEASE)) is not None:
            key = lease.job.step_key
            with lock:
                first_time = key not in failed_once and int(key[-2:]) % 3 == 0
                if first_time:
                    failed_once.add(key)
            if first_time:
                q.fail(lease, "transient", retry=True)
                continue
            q.complete(lease)
            with lock:
                completions.append(key)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(completions) == sorted(f"job-{i:02d}" for i in range(n_jobs))
    for i in range(n_jobs):
        rec = q.record(f"job-{i:02d}")
        assert rec is not None and rec.status is JobStatus.DONE
        assert rec.attempt == (2 if i % 3 == 0 else 1)
