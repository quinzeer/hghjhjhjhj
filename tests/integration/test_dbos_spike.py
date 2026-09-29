"""DBOS spike required by ADR-001 (Consequences): the five functions the architecture relies on, checked with
real executor subprocesses (`dbos_spike_worker.py`) against Postgres. Results: docs/design/dbos-spike.md.

(1) routing with `listen_queues` + distinct executor ids; (2) priority under `worker_concurrency=1`, and what
that limit covers; (3) `deduplication_id` scope (same queue refused, other queue accepted); (4) workflow
timeout cancels the workflow and its children, what happens to a long step in flight, and manual
cancellation; (5) SIGKILL recovery limited to the executor that restarts, and the paths that break it:
child workflows through DBOS's internal queue, two live processes with one executor id, resume after a
cancellation; (6) GPU sub-jobs: the deadlock of a parent waiting on its own queue, and the retained form.
(7) and (8) check the harness itself and the claims of the design document.

Each test gets its own DBOS system schema, dropped at teardown, and kills every subprocess it started.
Workers get the database URL through their environment and die with the test process (stdin pipe); SIGTERM
and SIGHUP become KeyboardInterrupt while a spike runs, so the teardown still runs when a run is stopped.
The test process only uses `DBOSClient` (no DBOS instance, no workflow code). Imports nothing from studio/.
Skipped unless STUDIO_TEST_PG_URL is set.
"""

from __future__ import annotations

import ast
import importlib.metadata
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import FrameType
from typing import Any, cast

import pytest
import sqlalchemy as sa
from dbos import DBOSClient, EnqueueOptions, WorkflowStatus
from dbos._error import DBOSQueueDeduplicatedError

PG_URL = os.environ.get("STUDIO_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not PG_URL, reason="STUDIO_TEST_PG_URL is not set"),
]

REPO = Path(__file__).resolve().parents[2]
SPIKE_DOC = REPO / "docs" / "design" / "dbos-spike.md"
INTERFACES = REPO / "studio" / "core" / "interfaces.py"
WORKER_SCRIPT = Path(__file__).with_name("dbos_spike_worker.py")
# Must match dbos_spike_worker.py.
APP_NAME = "studio-dbos-spike"
DB_URL_ENV = "DBOS_SPIKE_DB_URL"
EXIT_LOCK_HELD = 4
EXIT_LOCK_LOST = 5
EXIT_PARENT_GONE = 6
INTERNAL_QUEUE = "_dbos_internal_queue"

TERMINAL = {"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"}
STARTUP_TIMEOUT_S = 30.0
RUN_TIMEOUT_S = 30.0
QUIET_S = 2.5  # more than two polling intervals of every executor: time for something that must not happen
STOP_SIGNALS = (signal.SIGTERM, signal.SIGHUP)


def wait_until[T](check: Callable[[], T | None], timeout: float, what: str, interval: float = 0.05) -> T:
    """Poll `check` until it returns a truthy value (an empty list or None means: not yet)."""
    deadline = time.monotonic() + timeout
    while True:
        value = check()
        if value:
            return value
        if time.monotonic() > deadline:
            raise AssertionError(f"timed out after {timeout:.0f}s waiting for {what}")
        time.sleep(interval)


def report(point: str, **facts: Any) -> None:
    """One line per spike point, quoted in docs/design/dbos-spike.md (visible with `pytest -s`)."""
    print(f"\nSPIKE {point}: " + " ".join(f"{key}={value!r}" for key, value in facts.items()), flush=True)


def pg_engine(url: str = PG_URL) -> sa.Engine:
    return sa.create_engine(sa.make_url(url).set(drivername="postgresql+psycopg"))


def schema_exists(schema: str) -> bool:
    engine = pg_engine()
    try:
        with engine.connect() as conn:
            query = sa.text("SELECT count(*) FROM pg_namespace WHERE nspname = :name")
            return bool(conn.execute(query, {"name": schema}).scalar_one())
    finally:
        engine.dispose()


def drop_schema(url: str, schema: str) -> None:
    engine = pg_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(sa.text("SET lock_timeout = '20s'"))
            conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    finally:
        engine.dispose()


def live_processes(fragment: str) -> dict[int, list[str]]:
    """argv of every live (not zombie) process whose command line contains `fragment`."""
    found: dict[int, list[str]] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().split(b"\0")
            state = (entry / "stat").read_text().rsplit(")", 1)[1].split()[0]
        except (OSError, IndexError):
            continue  # the process ended meanwhile
        if state != "Z" and any(fragment.encode() in arg for arg in argv):
            found[int(entry.name)] = [arg.decode(errors="replace") for arg in argv if arg]
    return found


@dataclass(frozen=True)
class Marker:
    at: float
    executor_id: str
    pid: int
    note: str


@dataclass
class Worker:
    name: str
    proc: subprocess.Popen[bytes]
    log: Path

    @property
    def pid(self) -> int:
        return self.proc.pid

    def text(self) -> str:
        return self.log.read_text(encoding="utf-8", errors="replace") if self.log.exists() else ""

    def kill(self) -> None:
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=10)
        if self.proc.stdin is not None:
            self.proc.stdin.close()


@dataclass
class Spike:
    url: str
    schema: str
    markers: Path
    logs: Path
    workers: list[Worker] = field(default_factory=list)
    _client: DBOSClient | None = None

    # ---------------------------------------------------------------- processes

    def start(
        self,
        name: str,
        *,
        listen: list[str],
        executor_id: str | None = None,
        vmid: str | None = None,
        exit_after_recovery: bool = False,
        executor_lock: bool = True,
        lock_wait: float | None = None,
        until: str = "READY",
        exit_code: int | None = None,
    ) -> Worker:
        """Start an executor subprocess and wait for `until` in its output (then for `exit_code`, if given)."""
        env = {k: v for k, v in os.environ.items() if k not in ("DBOS__VMID", DB_URL_ENV)}
        env["PYTHONUNBUFFERED"] = "1"
        env[DB_URL_ENV] = self.url  # never in argv: `ps` shows argv to every user
        if vmid is not None:
            env["DBOS__VMID"] = vmid
        cmd = [
            sys.executable,
            "-u",
            str(WORKER_SCRIPT),
            "--schema",
            self.schema,
            "--markers",
            str(self.markers),
            "--listen",
            ",".join(listen),
            "--exit-on-stdin-eof",
        ]
        if executor_id is not None:
            cmd += ["--executor-id", executor_id]
        if exit_after_recovery:
            cmd.append("--exit-after-recovery")
            until, exit_code = "RECOVERED", 0
        if not executor_lock:
            cmd.append("--no-executor-lock")
        if lock_wait is not None:
            cmd += ["--lock-wait", str(lock_wait)]
        log = self.logs / f"{name}.log"
        with open(log, "wb") as out:
            # stdin stays a pipe held by this process: when it dies, whatever the signal, the worker reads EOF.
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT, env=env)
        worker = Worker(name, proc, log)
        self.workers.append(worker)

        def started() -> bool:
            if until in worker.text():
                return True
            if proc.poll() is not None:
                raise AssertionError(f"{name} exited with {proc.returncode} before {until}:\n{worker.text()[-3000:]}")
            return False

        wait_until(started, STARTUP_TIMEOUT_S, f"{name} {until}")
        if exit_code is not None:
            assert proc.wait(timeout=10) == exit_code, worker.text()[-3000:]
        return worker

    # ---------------------------------------------------------------- client side

    @property
    def client(self) -> DBOSClient:
        if self._client is None:  # the schema exists once a first worker has launched
            self._client = DBOSClient(system_database_url=self.url, dbos_system_schema=self.schema, application_name=APP_NAME)
        return self._client

    def enqueue(self, workflow: str, queue: str, *args: Any, **options: Any) -> str:
        opts = cast(EnqueueOptions, {"workflow_name": workflow, "queue_name": queue, **options})
        return self.client.enqueue(opts, *args).get_workflow_id()

    def status(self, workflow_id: str) -> WorkflowStatus:
        rows = self.client.list_workflows(workflow_ids=[workflow_id])
        assert len(rows) == 1, f"workflow {workflow_id} not found"
        return rows[0]

    def wait_status(self, workflow_id: str, expected: str, timeout: float = RUN_TIMEOUT_S) -> WorkflowStatus:
        def reached() -> WorkflowStatus | None:
            st = self.status(workflow_id)
            if st.status == expected:
                return st
            if st.status in TERMINAL:
                raise AssertionError(f"{workflow_id} ended {st.status} (expected {expected}): {st.error!r}")
            return None

        try:
            return wait_until(reached, timeout, f"{workflow_id} -> {expected}")
        except AssertionError as exc:
            raise AssertionError(f"{exc}\n{self.logs_tail()}") from None

    def children(self, parent_id: str) -> list[WorkflowStatus]:
        return self.client.list_workflows(parent_workflow_id=parent_id)

    def marks(self, name: str) -> list[Marker]:
        path = self.markers / name
        if not path.exists():
            return []
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            at, executor_id, pid, *note = line.split(" ", 3)
            out.append(Marker(float(at), executor_id, int(pid), note[0] if note else ""))
        return out

    def wait_marks(self, name: str, count: int = 1, timeout: float = 20.0) -> list[Marker]:
        def enough() -> list[Marker] | None:
            found = self.marks(name)
            return found if len(found) >= count else None

        return wait_until(enough, timeout, f"{count} x marker {name}")

    def mark_time(self, name: str) -> float:
        found = self.marks(name)
        assert len(found) == 1, f"marker {name}: {found}"
        return found[0].at

    def release(self) -> None:
        """Let every `wait_release_step` in flight, or to come, finish."""
        (self.markers / "release").touch()

    def logs_tail(self) -> str:
        return "\n".join(f"--- {w.name}\n{w.text()[-2000:]}" for w in self.workers)

    # ---------------------------------------------------------------- teardown

    def close(self) -> None:
        for worker in self.workers:
            worker.kill()
        if self._client is not None:
            self._client.destroy()
        drop_schema(self.url, self.schema)


@pytest.fixture
def spike(tmp_path: Path) -> Iterator[Spike]:
    markers = tmp_path / "markers"
    logs = tmp_path / "logs"
    markers.mkdir()
    logs.mkdir()
    s = Spike(url=PG_URL, schema=f"dbos_spike_{uuid.uuid4().hex[:12]}", markers=markers, logs=logs)
    deferred: list[int] = []

    def interrupt(signum: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt(f"signal {signum}")  # pytest then runs this fixture's teardown

    def defer(signum: int, frame: FrameType | None) -> None:
        deferred.append(signum)

    main_thread = threading.current_thread() is threading.main_thread()
    previous = {sig: signal.signal(sig, interrupt) for sig in STOP_SIGNALS} if main_thread else {}
    try:
        yield s
    finally:
        for sig in previous:
            signal.signal(sig, defer)  # a stop request must not cut the cleanup short
        try:
            s.close()
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
        if deferred:
            raise KeyboardInterrupt(f"signal {deferred[0]} during teardown")


# ====================================================================== (1) routing


def test_1_listen_queues_routes_each_queue_to_its_own_executor(spike: Spike) -> None:
    gpu0 = spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")  # executor id from DBOSConfig
    gpu1 = spike.start("gpu1", listen=["gpu1"], vmid="gpu1")  # executor id from DBOS__VMID
    assert "Executor ID: gpu0" in gpu0.text()
    assert "Executor ID: gpu1" in gpu1.text()
    pids = {"gpu0": gpu0.pid, "gpu1": gpu1.pid}

    # Interleaved enqueues, both executors idle: without routing they would share the work.
    wf_ids: dict[str, list[str]] = {"gpu0": [], "gpu1": []}
    for i in range(4):
        for queue in ("gpu0", "gpu1"):
            wf_ids[queue].append(spike.enqueue("whoami", queue, f"{queue}-{i}"))
    orphan = spike.enqueue("whoami", "gpu2", "gpu2-0")  # registered queue, no listener

    ran_on: dict[str, list[str]] = {"gpu0": [], "gpu1": []}
    for queue, ids in wf_ids.items():
        for wf in ids:
            st = spike.wait_status(wf, "SUCCESS")
            assert st.queue_name == queue
            assert st.executor_id == queue, f"{wf} enqueued in {queue} ran on {st.executor_id}"
            out = st.output
            assert isinstance(out, dict)
            assert (out["executor_id"], out["pid"]) == (queue, pids[queue])
            ran_on[queue].append(out["executor_id"])

    time.sleep(QUIET_S)
    orphan_status = spike.status(orphan)
    assert orphan_status.status == "ENQUEUED"
    assert orphan_status.executor_id is None
    report(
        "1-routing",
        gpu0_queue_ran_on=ran_on["gpu0"],
        gpu1_queue_ran_on=ran_on["gpu1"],
        gpu2_without_listener=orphan_status.status,
    )


# ====================================================================== (2) priority


def test_2_priority_orders_execution_under_worker_concurrency_one(spike: Spike) -> None:
    spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")  # gpu0 is registered with worker_concurrency=1
    block = spike.enqueue("blocker", "gpu0", "blocker", priority=1)
    spike.wait_status(block, "PENDING")

    # Enqueued in an order that FIFO would keep: only priority can produce the expected order.
    plan: list[tuple[str, int | None]] = [
        ("p30-first", 30),
        ("p10", 10),
        ("p30-second", 30),
        ("p20", 20),
        ("unset", None),
        ("p1", 1),
    ]
    ids: dict[str, str] = {}
    for tag, priority in plan:
        options = {} if priority is None else {"priority": priority}
        ids[tag] = spike.enqueue("record_order", "gpu0", tag, **options)

    time.sleep(2.0)  # the only slot is held by the blocker: nothing else may start
    assert {tag: spike.status(wf).status for tag, wf in ids.items()} == dict.fromkeys(ids, "ENQUEUED")
    assert spike.status(ids["unset"]).priority == 0  # DBOS default when priority is omitted

    spike.client.send(block, "go", "go")
    spike.wait_status(block, "SUCCESS")
    for wf in ids.values():
        spike.wait_status(wf, "SUCCESS")

    order = [m.note for m in spike.marks("order")]
    assert order == ["blocker", "unset", "p1", "p10", "p20", "p30-first", "p30-second"]

    # One at a time: each step starts after the previous workflow's step has completed.
    steps = [spike.client.list_workflow_steps(ids[tag])[0] for tag in order[1:]]
    for previous, current in zip(steps, steps[1:], strict=False):
        assert previous["completed_at_epoch_ms"] is not None and current["started_at_epoch_ms"] is not None
        assert current["started_at_epoch_ms"] >= previous["completed_at_epoch_ms"]
    report("2-priority", enqueue_order=[t for t, _ in plan], execution_order=order)


def test_2b_worker_concurrency_is_per_process_global_concurrency_holds_across_processes(spike: Spike) -> None:
    """`worker_concurrency=1` limits one process, not one card: a second process that listens to the same queue
    (misconfigured service, different executor id) runs a second job at once. `global_concurrency=1`, which the
    worker sets on every `gpuN`, holds across processes. `worker_only` is the per-process limit alone."""
    spike.start("gpu0", listen=["gpu0", "worker_only"], executor_id="gpu0")
    spike.start("gpu0-stray", listen=["gpu0", "worker_only"], executor_id="gpu0-stray")
    per_process = [spike.enqueue("blocker", "worker_only", f"w{i}") for i in range(2)]
    per_card = [spike.enqueue("blocker", "gpu0", f"g{i}") for i in range(2)]

    running = [spike.wait_status(wf, "PENDING") for wf in per_process]
    assert sorted(str(st.executor_id) for st in running) == ["gpu0", "gpu0-stray"]  # two jobs of one queue at once
    wait_until(lambda: [wf for wf in per_card if spike.status(wf).status == "PENDING"], RUN_TIMEOUT_S, "a gpu0 job")
    time.sleep(QUIET_S)
    card_statuses = sorted(spike.status(wf).status for wf in per_card)
    assert card_statuses == ["ENQUEUED", "PENDING"]

    for wf in per_process + per_card:
        spike.client.send(wf, "go", "go")  # a message sent before the recv is kept for it
    done = [spike.wait_status(wf, "SUCCESS") for wf in per_card]
    first, second = sorted(done, key=lambda st: st.dequeued_at or 0)
    assert first.completed_at is not None and second.dequeued_at is not None
    assert second.dequeued_at >= first.completed_at  # the second gpu0 job waited for the first to end
    for wf in per_process:
        spike.wait_status(wf, "SUCCESS")
    report(
        "2b-concurrency",
        worker_only_running_at_once=sorted(str(st.executor_id) for st in running),
        gpu0_statuses_with_two_listeners=card_statuses,
        gpu0_ran_on=[st.executor_id for st in (first, second)],
    )


# ====================================================================== (3) deduplication


def test_3_deduplication_id_is_scoped_to_one_queue(spike: Spike) -> None:
    spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")
    spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")
    key = "step-" + uuid.uuid4().hex  # stands for a step key

    first = spike.enqueue("blocker", "gpu0", "first", deduplication_id=key)
    spike.wait_status(first, "PENDING")

    with pytest.raises(DBOSQueueDeduplicatedError) as refused:
        spike.enqueue("blocker", "gpu0", "same-queue", deduplication_id=key)
    attached = spike.enqueue("blocker", "gpu0", "attach", deduplication_id=key, duplication_policy="return-existing")
    assert attached == first

    other = spike.enqueue("blocker", "gpu1", "other-queue", deduplication_id=key)  # accepted: another queue
    other_status = spike.wait_status(other, "PENDING")
    first_status = spike.status(first)
    # The same step key is now running on two executors at once.
    assert (first_status.status, first_status.executor_id) == ("PENDING", "gpu0")
    assert (other_status.status, other_status.executor_id) == ("PENDING", "gpu1")
    assert len(spike.client.list_workflows(name="blocker")) == 2  # the refused enqueue left no row

    for wf in (first, other):
        spike.client.send(wf, "go", "go")
        spike.wait_status(wf, "SUCCESS")
    assert spike.status(first).deduplication_id is None  # released on completion

    again = spike.enqueue("record_order", "gpu0", "again", deduplication_id=key)  # accepted after completion
    spike.wait_status(again, "SUCCESS")
    assert Counter(m.note for m in spike.marks("order")) == Counter({"first": 1, "other-queue": 1, "again": 1})
    report(
        "3-dedup",
        same_queue=type(refused.value).__name__,
        return_existing_is_first=attached == first,
        other_queue_running_on=other_status.executor_id,
        same_key_after_success="accepted",
    )


# ====================================================================== (4) timeouts and cancellation


def test_4_timeout_cancels_workflow_and_children_but_not_a_running_sync_step(spike: Spike) -> None:
    spike.start("cpu", listen=["cpu"], executor_id="cpu")
    timeout_s, work_s = 2.0, 6.0

    # a) SetWorkflowTimeout inside DBOS: parent (sync long step) with a child (sync long step).
    launcher = spike.enqueue("start_with_timeout", "cpu", timeout_s, work_s)
    parent_id = spike.wait_status(launcher, "SUCCESS").output
    assert isinstance(parent_id, str)
    # b) EnqueueOptions.workflow_timeout from a client: async workflows with a preemptible step.
    async_sleep = spike.enqueue("timeout_async", "cpu", "async_sleep", 30.0, False, workflow_timeout=timeout_s)
    async_thread = spike.enqueue("timeout_async", "cpu", "async_thread", 8.0, True, workflow_timeout=timeout_s)

    parent = spike.wait_status(parent_id, "CANCELLED", timeout=15)
    kids = spike.children(parent_id)
    assert [k.name for k in kids] == ["timeout_child"]
    child = spike.wait_status(kids[0].workflow_id, "CANCELLED", timeout=15)
    assert child.workflow_deadline_epoch_ms == parent.workflow_deadline_epoch_ms  # inherited deadline
    sleep_st = spike.wait_status(async_sleep, "CANCELLED", timeout=15)
    thread_st = spike.wait_status(async_thread, "CANCELLED", timeout=15)

    def cancelled_at(st: WorkflowStatus) -> float:
        assert st.completed_at is not None
        return st.completed_at / 1000

    # The timeout sweep runs about once a second: cancellation lands shortly after the deadline, never before.
    cancel_lag = {}
    for label, st in (("parent", parent), ("child", child), ("async_sleep", sleep_st), ("async_thread", thread_st)):
        assert st.workflow_deadline_epoch_ms is not None
        lag = cancelled_at(st) - st.workflow_deadline_epoch_ms / 1000
        assert 0.0 <= lag <= 2.5, f"{label}: cancelled {lag:.2f}s after its deadline"
        cancel_lag[label] = round(lag, 2)

    for name in ("parent.long.end", "child.long.end", "async_thread.thread_end"):
        spike.wait_marks(name, timeout=15)
    time.sleep(1.5)  # room for a next step that must never start

    # Sync steps are not interrupted: they run to their end after the cancellation; the next step never starts.
    sync_overrun = {}
    for label, st in (("parent", parent), ("child", child)):
        overrun = spike.mark_time(f"{label}.long.end") - cancelled_at(st)
        assert overrun > 1.0, f"{label}: long step ended {overrun:.2f}s after cancellation"
        assert spike.marks(f"{label}.after") == []
        sync_overrun[label] = round(overrun, 2)

    # Async preemptible step awaiting asyncio: interrupted about one poll interval after the cancellation.
    sleep_delay = spike.mark_time("async_sleep.interrupted") - cancelled_at(sleep_st)
    assert -0.2 <= sleep_delay <= 3.0, sleep_delay
    assert spike.marks("async_sleep.long.end") == [] and spike.marks("async_sleep.after") == []

    # Async preemptible step awaiting a thread: the await is interrupted, the thread runs to its end.
    thread_delay = spike.mark_time("async_thread.interrupted") - cancelled_at(thread_st)
    assert -0.2 <= thread_delay <= 3.0, thread_delay
    thread_overrun = spike.mark_time("async_thread.thread_end") - spike.mark_time("async_thread.interrupted")
    assert thread_overrun > 1.0, thread_overrun
    assert spike.marks("async_thread.long.end") == [] and spike.marks("async_thread.after") == []

    # The in-flight step that outlived the cancellation is still checkpointed; the next one never ran.
    parent_steps = [s["function_name"] for s in spike.client.list_workflow_steps(parent_id)]
    assert parent_steps == ["timeout_child", "long_sync_step"]
    report(
        "4-timeout",
        statuses={
            "parent": parent.status,
            "child": child.status,
            "async_sleep": sleep_st.status,
            "async_thread": thread_st.status,
        },
        cancel_after_deadline_s=cancel_lag,
        sync_step_ran_past_cancel_s=sync_overrun,
        preemptible_interrupt_delay_s=round(sleep_delay, 2),
        thread_kept_running_s=round(thread_overrun, 2),
        parent_checkpointed_steps=parent_steps,
    )


def test_4b_manual_cancel_reaches_children_only_with_cancel_children(spike: Spike) -> None:
    """A timeout reaches the children through the inherited deadline (test 4); a manual cancellation, such as
    the progress watchdog of ADR-001, does not unless it passes `cancel_children=True`."""
    spike.start("cpu", listen=["cpu"], executor_id="cpu")
    plain = spike.enqueue("parent_with_child", "cpu", "plain")
    cascade = spike.enqueue("parent_with_child", "cpu", "cascade")
    spike.wait_marks("plain.child.attempts")
    spike.wait_marks("cascade.child.attempts")
    (plain_child,) = spike.children(plain)
    (cascade_child,) = spike.children(cascade)

    spike.client.cancel_workflow(plain)  # DBOS default: cancel_children=False
    spike.client.cancel_workflow(cascade, cancel_children=True)
    after_cancel = {
        "plain": spike.status(plain).status,
        "plain.child": spike.status(plain_child.workflow_id).status,
        "cascade": spike.status(cascade).status,
        "cascade.child": spike.status(cascade_child.workflow_id).status,
    }
    assert after_cancel == {"plain": "CANCELLED", "plain.child": "PENDING", "cascade": "CANCELLED", "cascade.child": "CANCELLED"}

    spike.release()
    orphan = spike.wait_status(plain_child.workflow_id, "SUCCESS")  # the child of a cancelled parent ran to its end
    spike.wait_marks("cascade.child.done")  # the in-flight sync step of the cancelled child still finishes
    time.sleep(1.5)
    assert spike.status(cascade_child.workflow_id).status == "CANCELLED"
    assert spike.status(plain).status == "CANCELLED"
    report("4b-cancel", after_cancel=after_cancel, plain_child_final=orphan.status)


# ====================================================================== (5) recovery


def test_5_sigkill_recovery_resumes_on_same_executor_id_only(spike: Spike) -> None:
    life1 = spike.start("gpu0-life1", listen=["gpu0"], executor_id="gpu0")
    wf = spike.enqueue("resumable", "gpu0", "job")
    spike.wait_marks("job.s2.attempts")  # step 2 in progress
    life1.kill()  # SIGKILL in the middle of step 2
    assert life1.proc.returncode == -signal.SIGKILL
    killed = spike.status(wf)
    assert (killed.status, killed.executor_id) == ("PENDING", "gpu0")

    gpu1 = spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")
    time.sleep(3.0)  # gpu1 startup recovery + several queue polls
    untouched = spike.status(wf)
    assert (untouched.status, untouched.executor_id, untouched.queue_name) == ("PENDING", "gpu0", "gpu0")
    assert len(spike.marks("job.s2.attempts")) == 1
    assert "No workflows to recover" in gpu1.text()

    spike.release()
    life2 = spike.start("gpu0-life2", listen=["gpu0"], executor_id="gpu0")
    assert "LOCKED executor_id=gpu0" in life2.text()  # the executor lock of the killed life was released
    done = spike.wait_status(wf, "SUCCESS")
    assert done.executor_id == "gpu0"
    assert done.output == {"s1_executor": "gpu0", "s2_executor": "gpu0"}
    assert "Recovering 1 workflows" in life2.text()
    assert [m.executor_id for m in spike.marks("job.s1.runs")] == ["gpu0"]  # checkpointed, not re-run
    attempts = [(m.executor_id, m.pid) for m in spike.marks("job.s2.attempts")]
    assert attempts == [("gpu0", life1.pid), ("gpu0", life2.pid)]  # the interrupted step restarts from its beginning
    report(
        "5-recovery",
        after_kill=(killed.status, killed.executor_id),
        after_gpu1_start=(untouched.status, untouched.executor_id),
        result=done.output,
        step1_runs=1,
        step2_attempts=[executor for executor, _ in attempts],
    )


def test_5b_recovered_child_workflow_goes_to_internal_queue_any_executor_can_run(spike: Spike) -> None:
    """Limit found in the code (`_recovery.py`, `_queue.py`): a child started with `DBOS.start_workflow`
    has no queue; recovery re-enqueues it on `_dbos_internal_queue`, which every executor polls whatever
    `listen_queues` says. Deterministic setup: gpu0 restarts, recovers, dies again before its first poll."""
    life1 = spike.start("gpu0-life1", listen=["gpu0"], executor_id="gpu0")
    parent = spike.enqueue("parent_with_child", "gpu0", "job")
    spike.wait_marks("job.child.attempts")  # child step in progress
    (child,) = spike.children(parent)
    assert (child.queue_name, child.executor_id, child.status) == (None, "gpu0", "PENDING")
    life1.kill()

    spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")
    spike.start("gpu0-life2", listen=[], executor_id="gpu0", exit_after_recovery=True)
    spike.release()

    child_done = spike.wait_status(child.workflow_id, "SUCCESS")
    assert child_done.executor_id == "gpu1", "the child of a gpu0 workflow ran on the gpu1 executor"
    assert child_done.queue_name == INTERNAL_QUEUE
    attempts = [m.executor_id for m in spike.marks("job.child.attempts")]
    assert attempts == ["gpu0", "gpu1"]
    parent_waiting = spike.status(parent)
    assert (parent_waiting.status, parent_waiting.queue_name) == ("ENQUEUED", "gpu0")  # the parent kept its queue

    spike.start("gpu0-life3", listen=["gpu0"], executor_id="gpu0")
    parent_done = spike.wait_status(parent, "SUCCESS")
    assert parent_done.output == {"parent_executor": "gpu0", "child_executor": "gpu1"}
    assert [m.executor_id for m in spike.marks("job.parent.runs")] == ["gpu0"]
    report(
        "5b-child-recovery",
        child_queue_before_kill=child.queue_name,
        child_attempts=attempts,
        child_queue_after_recovery=child_done.queue_name,
        parent_after_recovery=(parent_waiting.status, parent_waiting.queue_name),
        parent_result=parent_done.output,
    )


def test_5c_two_live_processes_with_one_executor_id_run_the_same_step_twice(spike: Spike) -> None:
    """Stock DBOS (`--no-executor-lock`): startup recovery takes every PENDING workflow of its executor id
    (`_sys_db.get_pending_workflows`) without checking that the process which runs it is dead. A second process
    started while the first still lives (overlapping restart, worker thought dead) re-runs the step in flight,
    although `gpu0` has `worker_concurrency=1` and `global_concurrency=1`."""
    first = spike.start("gpu0-A", listen=["gpu0"], executor_id="gpu0", executor_lock=False)
    wf = spike.enqueue("resumable", "gpu0", "job")
    spike.wait_marks("job.s2.attempts")
    second = spike.start("gpu0-B", listen=["gpu0"], executor_id="gpu0", executor_lock=False)

    attempts = spike.wait_marks("job.s2.attempts", count=2)
    assert first.proc.poll() is None  # the first process is alive, still inside the step
    assert [(m.executor_id, m.pid) for m in attempts] == [("gpu0", first.pid), ("gpu0", second.pid)]
    assert "Recovering 1 workflows" in second.text()

    spike.release()
    done = spike.wait_status(wf, "SUCCESS")
    finished = spike.wait_marks("job.s2.done", count=2)
    assert sorted(m.pid for m in finished) == sorted([first.pid, second.pid])  # the GPU work was done twice
    assert [m.executor_id for m in spike.marks("job.s1.runs")] == ["gpu0"]
    report(
        "5c-duplicate-executor",
        first_alive_when_second_ran=True,
        step_attempts=[f"pid={m.pid}" for m in attempts],
        step_completions=len(finished),
        workflow=done.status,
    )


def test_5d_executor_lock_refuses_a_second_live_process_with_the_same_id(spike: Spike) -> None:
    """The fix for 5c: a session advisory lock on the executor id, taken before `DBOS.launch()` and held for
    the life of the process. A second `gpu0` exits without launching DBOS, so without recovering anything;
    another id is not affected; losing the lock session ends the process."""
    first = spike.start("gpu0-A", listen=["gpu0"], executor_id="gpu0")
    assert "LOCKED executor_id=gpu0" in first.text()
    wf = spike.enqueue("resumable", "gpu0", "job")
    spike.wait_marks("job.s2.attempts")

    second = spike.start("gpu0-B", listen=["gpu0"], executor_id="gpu0", lock_wait=1.0, until="REFUSED", exit_code=EXIT_LOCK_HELD)
    assert "Executor ID" not in second.text() and "Recovering" not in second.text()  # DBOS never launched
    spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")  # one lock per executor id
    time.sleep(QUIET_S)
    assert [m.pid for m in spike.marks("job.s2.attempts")] == [first.pid]

    spike.release()
    done = spike.wait_status(wf, "SUCCESS")
    assert [(m.executor_id, m.pid) for m in spike.wait_marks("job.s2.done")] == [("gpu0", first.pid)]
    assert [m.pid for m in spike.marks("job.s2.attempts")] == [first.pid]

    found = re.search(r"LOCKED executor_id=gpu0 backend_pid=(\d+)", first.text())
    assert found is not None
    engine = pg_engine()
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT pg_terminate_backend(:pid)"), {"pid": int(found.group(1))})
    finally:
        engine.dispose()
    assert first.proc.wait(timeout=10) == EXIT_LOCK_LOST
    assert "LOCK LOST" in first.text()
    third = spike.start("gpu0-C", listen=["gpu0"], executor_id="gpu0")  # the id is free again
    report(
        "5d-executor-lock",
        second_exit_code=second.proc.returncode,
        step_attempts=len(spike.marks("job.s2.attempts")),
        workflow=done.status,
        lock_lost_exit_code=first.proc.returncode,
        restart_after_lock_loss="READY" in third.text(),
    )


def cancelled_gpu0_job(spike: Spike) -> tuple[str, WorkflowStatus, Worker]:
    """A gpu0 job cancelled by its timeout, its gpu0 executor then dead, and a live gpu1 executor. The message
    the job waits for is sent before the resume, so a resumed job completes at once wherever it runs."""
    gpu0 = spike.start("gpu0-life1", listen=["gpu0"], executor_id="gpu0")
    gpu1 = spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")
    wf = spike.enqueue("blocker", "gpu0", "timed", workflow_timeout=1.0)
    spike.wait_status(wf, "PENDING")
    cancelled = spike.wait_status(wf, "CANCELLED", timeout=10)
    assert (cancelled.queue_name, cancelled.executor_id) == (None, "gpu0")  # DBOS erases the queue on cancel
    gpu0.kill()
    spike.client.send(wf, "go", "go")
    return wf, cancelled, gpu1


def test_5e_resume_after_timeout_without_queue_moves_the_gpu_job_to_another_card(spike: Spike) -> None:
    """`cancel_workflows` and the timeout sweep set `queue_name=NULL`; `resume_workflow` without `queue_name`
    (the only form of `dbos workflow resume`) re-enqueues on `_dbos_internal_queue`, which every executor polls."""
    wf, cancelled, _ = cancelled_gpu0_job(spike)
    spike.client.resume_workflow(wf)
    resumed = spike.status(wf)
    assert resumed.queue_name == INTERNAL_QUEUE
    done = spike.wait_status(wf, "SUCCESS")
    assert (done.executor_id, done.queue_name) == ("gpu1", INTERNAL_QUEUE)
    assert [(m.executor_id, m.note) for m in spike.marks("order")] == [("gpu1", "timed")]
    report(
        "5e-resume-without-queue",
        after_timeout=(cancelled.status, cancelled.queue_name),
        resumed_queue=resumed.queue_name,
        ran_on=done.executor_id,
    )


def test_5f_resume_with_the_original_queue_keeps_the_gpu_job_on_its_card(spike: Spike) -> None:
    """The fix for 5e: the dispatcher keeps the original `gpuN` (DBOS erased it) and resumes with it."""
    wf, cancelled, _ = cancelled_gpu0_job(spike)
    spike.client.resume_workflow(wf, queue_name="gpu0")
    time.sleep(QUIET_S)
    waiting = spike.status(wf)
    assert (waiting.status, waiting.queue_name) == ("ENQUEUED", "gpu0")  # the live gpu1 executor leaves it
    assert spike.marks("order") == []

    life2 = spike.start("gpu0-life2", listen=["gpu0"], executor_id="gpu0")
    done = spike.wait_status(wf, "SUCCESS")
    assert (done.executor_id, done.queue_name) == ("gpu0", "gpu0")
    assert [(m.executor_id, m.pid) for m in spike.marks("order")] == [("gpu0", life2.pid)]
    report(
        "5f-resume-with-queue",
        after_timeout=(cancelled.status, cancelled.queue_name),
        while_gpu0_down=(waiting.status, waiting.queue_name),
        ran_on=done.executor_id,
    )


# ====================================================================== (6) GPU sub-jobs


def test_6a_parent_awaiting_a_child_in_its_own_gpu_queue_deadlocks(spike: Spike) -> None:
    """With `worker_concurrency=1`, a parent that waits on a child enqueued in its own queue holds the only slot
    (a workflow frees it when it returns): the child never leaves the queue."""
    spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")
    spike.release()  # a child that ran would finish at once
    parent = spike.enqueue("await_child_in_queue", "gpu0", "job", "gpu0")
    spike.wait_marks("job.child_enqueued")
    time.sleep(QUIET_S + 1.0)
    (child,) = spike.children(parent)
    state = (spike.status(parent).status, child.status, child.queue_name)
    assert state == ("PENDING", "ENQUEUED", "gpu0")
    assert spike.marks("job.child.attempts") == []
    report("6a-same-queue-child", parent_child_queue=state)


def test_6b_orchestrator_in_cpu_awaits_gpu_jobs_that_recover_on_their_own_card(spike: Spike) -> None:
    """Retained form: the parent that chains GPU jobs lives in `cpu` (it holds no card), enqueues each GPU job
    explicitly in its `gpuN` with `DBOS.enqueue_workflow`, and waits. The job keeps its queue across a SIGKILL:
    a live gpu1 leaves it, the restarted gpu0 resumes it."""
    spike.start("cpu", listen=["cpu"], executor_id="cpu")
    life1 = spike.start("gpu0-life1", listen=["gpu0"], executor_id="gpu0")
    parent = spike.enqueue("await_child_in_queue", "cpu", "job", "gpu0")
    spike.wait_marks("job.child.attempts")
    (child,) = spike.children(parent)
    assert (child.queue_name, child.executor_id, child.status) == ("gpu0", "gpu0", "PENDING")
    assert spike.status(parent).executor_id == "cpu"

    life1.kill()
    gpu1 = spike.start("gpu1", listen=["gpu1"], executor_id="gpu1")
    time.sleep(QUIET_S)
    orphan = spike.status(child.workflow_id)
    assert (orphan.status, orphan.executor_id, orphan.queue_name) == ("PENDING", "gpu0", "gpu0")
    assert "No workflows to recover" in gpu1.text()

    spike.release()
    life2 = spike.start("gpu0-life2", listen=["gpu0"], executor_id="gpu0")
    child_done = spike.wait_status(child.workflow_id, "SUCCESS")
    assert (child_done.executor_id, child_done.queue_name) == ("gpu0", "gpu0")
    parent_done = spike.wait_status(parent, "SUCCESS")
    assert parent_done.output == {"parent_executor": "cpu", "child_executor": "gpu0"}
    attempts = [(m.executor_id, m.pid) for m in spike.marks("job.child.attempts")]
    assert attempts == [("gpu0", life1.pid), ("gpu0", life2.pid)]
    report(
        "6b-cpu-orchestrator",
        child_queue_after_recovery=child_done.queue_name,
        child_attempts=[executor for executor, _ in attempts],
        parent_result=parent_done.output,
    )


# ====================================================================== (7) harness hygiene


def test_7a_database_url_reaches_workers_by_environment_not_argv(spike: Spike) -> None:
    url = sa.make_url(PG_URL)
    if url.password is None:
        url = url.set(password="spike-not-a-secret")  # the local server trusts; it must still never show in argv
    spike.url = url.render_as_string(hide_password=False)
    worker = spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")
    wf = spike.enqueue("whoami", "gpu0", "argv")
    spike.wait_status(wf, "SUCCESS")  # the worker did reach the database
    argv = Path(f"/proc/{worker.pid}/cmdline").read_bytes().split(b"\0")
    password = str(url.password).encode()
    assert not any(password in arg for arg in argv)
    assert not any(b"postgresql" in arg or b"@" in arg for arg in argv)


def test_7b_terminated_run_kills_its_workers_and_drops_its_schema(tmp_path: Path) -> None:
    """A CI timeout or `kill` sends SIGTERM to pytest: the running spike must still stop its workers and drop
    its schema. Runs test 4 in a child pytest and terminates it once its worker has created the schema."""
    inner_tmp = tmp_path / "inner"
    node = f"{Path(__file__).resolve()}::test_4_timeout_cancels_workflow_and_children_but_not_a_running_sync_step"
    env = {**os.environ, "STUDIO_TEST_PG_URL": PG_URL}
    log = tmp_path / "inner.log"
    cmd = [sys.executable, "-m", "pytest", node, "-q", "-s", "-p", "no:cacheprovider", f"--basetemp={inner_tmp}"]
    with open(log, "wb") as out:
        inner = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, env=env, cwd=REPO)
    schema: str | None = None
    try:

        def running_schema() -> str | None:
            for argv in live_processes(str(inner_tmp)).values():
                if "--schema" in argv and schema_exists(name := argv[argv.index("--schema") + 1]):
                    return name
            return None

        schema = wait_until(running_schema, 60, "a worker of the child run with its schema")
        inner.send_signal(signal.SIGTERM)
        code = inner.wait(timeout=60)
        wait_until(lambda: not live_processes(str(inner_tmp)), 10, "the workers of the child run to exit")
        output = log.read_text(errors="replace")
        assert code == pytest.ExitCode.INTERRUPTED, output[-3000:]
        assert "KeyboardInterrupt" in output
        assert not schema_exists(schema)
        report("7b-sigterm", child_exit_code=code, workers_left=0, schema_left=False)
    finally:
        if inner.poll() is None:
            inner.kill()
            inner.wait(timeout=10)
        for pid in live_processes(str(inner_tmp)):
            os.kill(pid, signal.SIGKILL)
        if schema is not None:
            drop_schema(PG_URL, schema)


def test_7c_worker_exits_when_the_process_holding_its_stdin_is_gone(spike: Spike) -> None:
    """When pytest dies without a teardown (SIGKILL), the kernel closes its end of each worker's stdin pipe."""
    worker = spike.start("gpu0", listen=["gpu0"], executor_id="gpu0")
    assert worker.proc.stdin is not None
    worker.proc.stdin.close()
    assert worker.proc.wait(timeout=10) == EXIT_PARENT_GONE
    assert "PARENT GONE" in worker.text()


# ====================================================================== (8) claims of the design document


def test_8a_design_doc_maps_every_jobqueue_method_to_dbos() -> None:
    """The document must say, for each method of the `JobQueue` Protocol, what DBOS offers in its place."""
    tree = ast.parse(INTERFACES.read_text(encoding="utf-8"))
    (protocol,) = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "JobQueue"]
    methods = [node.name for node in protocol.body if isinstance(node, ast.FunctionDef)]
    assert {"enqueue", "claim", "heartbeat", "complete", "fail", "expire"} <= set(methods)
    doc = SPIKE_DOC.read_text(encoding="utf-8")
    heading = "\n## Correspondance avec le Protocol `JobQueue`\n"
    assert heading in doc
    section = doc.split(heading, 1)[1].split("\n## ", 1)[0]
    table_rows = [line for line in section.splitlines() if line.startswith("| `")]
    mapped = {m.group(1) for line in table_rows if (m := re.match(r"\| `(\w+)", line))}
    assert set(methods) <= mapped, f"unmapped JobQueue methods: {sorted(set(methods) - mapped)}"


def test_8b_installed_dbos_is_the_version_the_spike_validated() -> None:
    """The conclusion holds for one DBOS version: an upgrade fails here until the spike is run again."""
    doc = SPIKE_DOC.read_text(encoding="utf-8")
    found = re.search(r"DBOS Transact \*\*(\d+\.\d+\.\d+)\*\*", doc)
    assert found is not None
    assert importlib.metadata.version("dbos") == found.group(1)
