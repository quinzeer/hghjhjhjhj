"""Executor process for the DBOS spike (ADR-001, Consequences). Standalone: imports nothing from `studio/`.

The spike tests start several copies of this script as real subprocesses, each with its own executor id and
its own queues, against one Postgres system database (one fresh schema per test):

    DBOS_SPIKE_DB_URL=URL python dbos_spike_worker.py --schema S --markers DIR --listen gpu0 [--executor-id gpu0]

The database URL comes from the environment, never from argv (argv is world-readable through `ps`).
Without `--executor-id`, DBOS reads the executor id from the `DBOS__VMID` environment variable.

Before launching DBOS, the process takes a Postgres session advisory lock keyed on (app, schema, executor id)
and keeps it for its whole life: a second live process with the same executor id is refused (exit 4) instead
of recovering, and re-running, the workflows the first one is still executing. If the lock connection is lost,
the process exits at once (exit 5). `--no-executor-lock` reproduces stock DBOS behaviour for the spike.

The process prints `READY ...` once DBOS is launched and the spike queues are registered, then serves until it
is killed. With `--exit-on-stdin-eof` it also exits (exit 6) when its stdin reaches end of file, which is what
happens when the parent that holds the other end of the pipe dies, whatever the signal. With
`--exit-after-recovery` it launches, waits until DBOS has re-enqueued its own pending workflows, prints
`RECOVERED ...` and exits at once, before its queue threads poll (they first wait one polling interval).

Workflows write timestamped marker lines (`<epoch> <executor_id> <pid> <note>`) into `--markers`, so the
tests can see which process ran which step, and when, without trusting the workflow's own return value.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from dbos import DBOS, DBOSConfig, SetWorkflowTimeout
from sqlalchemy.pool import NullPool

APP_NAME = "studio-dbos-spike"
APP_VERSION = "spike-1"  # fixed, so a restarted executor recovers the workflows of its previous life
DB_URL_ENV = "DBOS_SPIKE_DB_URL"
# name -> (worker_concurrency, global_concurrency). One job at a time per GPU card, enforced per process AND
# across processes; `worker_only` is the per-process limit alone (control queue for the spike); `cpu` has no
# limit; `gpu2` has no listener in the tests.
QUEUES: dict[str, tuple[int | None, int | None]] = {
    "gpu0": (1, 1),
    "gpu1": (1, 1),
    "gpu2": (1, 1),
    "worker_only": (1, None),
    "cpu": (None, None),
}
RELEASE_POLL_S = 0.05
RELEASE_WAIT_MAX_S = 120.0
LOCK_POLL_S = 0.1
LOCK_CHECK_S = 0.5

EXIT_LOCK_HELD = 4
EXIT_LOCK_LOST = 5
EXIT_PARENT_GONE = 6

MARKERS = Path(".")


def mark(name: str, note: str = "") -> None:
    line = f"{time.time():.3f} {DBOS.executor_id} {os.getpid()} {note}".rstrip() + "\n"
    with open(MARKERS / name, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


# ------------------------------------------------------------------ (1) routing


@DBOS.step()
def whoami_step(tag: str) -> dict[str, Any]:
    return {"executor_id": DBOS.executor_id, "pid": os.getpid(), "tag": tag}


@DBOS.workflow()
def whoami(tag: str) -> dict[str, Any]:
    return whoami_step(tag)


# ------------------------------------------------------------------ (2) priority, (3) deduplication


@DBOS.step()
def record_step(tag: str) -> str:
    mark("order", tag)
    return tag


@DBOS.workflow()
def record_order(tag: str) -> str:
    return record_step(tag)


@DBOS.workflow()
def blocker(tag: str) -> str:
    """Occupy the executor until the test sends a message on topic `go` (durable wait, no busy loop)."""
    message = DBOS.recv("go", timeout_seconds=90)
    record_step(tag)
    return f"{tag}:{message}"


# ------------------------------------------------------------------ (4) timeouts


@DBOS.step()
def long_sync_step(label: str, seconds: float) -> str:
    mark(f"{label}.long.start")
    time.sleep(seconds)  # stands for a blocking GPU call (CUDA kernel, ComfyUI HTTP wait)
    mark(f"{label}.long.end")
    return label


@DBOS.step()
def after_step(label: str) -> str:
    mark(f"{label}.after")
    return label


@DBOS.workflow()
def timeout_child(seconds: float) -> str:
    long_sync_step("child", seconds)
    return after_step("child")


@DBOS.workflow()
def timeout_parent(seconds: float) -> str:
    child = DBOS.start_workflow(timeout_child, seconds)
    long_sync_step("parent", seconds)
    after_step("parent")
    return child.get_result()


@DBOS.workflow()
def start_with_timeout(timeout_s: float, work_s: float) -> str:
    """Start `timeout_parent` under SetWorkflowTimeout and return its id without waiting for it."""
    with SetWorkflowTimeout(timeout_s):
        handle = DBOS.start_workflow(timeout_parent, work_s)
    return handle.get_workflow_id()


def blocking_work(label: str, seconds: float) -> None:
    time.sleep(seconds)
    mark(f"{label}.thread_end")


@DBOS.step(preemptible=True)
async def preemptible_step(label: str, seconds: float, in_thread: bool) -> str:
    mark(f"{label}.long.start")
    try:
        if in_thread:
            await asyncio.to_thread(blocking_work, label, seconds)
        else:
            await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        mark(f"{label}.interrupted")
        raise
    mark(f"{label}.long.end")
    return label


@DBOS.step()
async def after_step_async(label: str) -> str:
    mark(f"{label}.after")
    return label


@DBOS.workflow()
async def timeout_async(label: str, seconds: float, in_thread: bool) -> str:
    await preemptible_step(label, seconds, in_thread)
    return await after_step_async(label)


# ------------------------------------------------------------------ (5) recovery


@DBOS.step()
def counted_step(label: str) -> str:
    mark(f"{label}.runs")
    return DBOS.executor_id


@DBOS.step()
def wait_release_step(label: str) -> str:
    """Record an attempt, block until the test creates `<markers>/release` (the step to kill), record its end."""
    mark(f"{label}.attempts")
    deadline = time.monotonic() + RELEASE_WAIT_MAX_S
    while not (MARKERS / "release").exists():
        if time.monotonic() > deadline:
            raise TimeoutError(f"{label}: release marker never appeared")
        time.sleep(RELEASE_POLL_S)
    mark(f"{label}.done")
    return DBOS.executor_id


@DBOS.workflow()
def resumable(label: str) -> dict[str, str]:
    first = counted_step(f"{label}.s1")
    second = wait_release_step(f"{label}.s2")
    return {"s1_executor": first, "s2_executor": second}


@DBOS.workflow()
def child_work(label: str) -> str:
    return wait_release_step(label)


@DBOS.workflow()
def parent_with_child(label: str) -> dict[str, str]:
    parent_executor = counted_step(f"{label}.parent")
    child = DBOS.start_workflow(child_work, f"{label}.child")
    return {"parent_executor": parent_executor, "child_executor": child.get_result()}


# ------------------------------------------------------------------ (6) GPU sub-jobs


@DBOS.workflow()
def await_child_in_queue(label: str, queue: str) -> dict[str, str]:
    """Enqueue `child_work` explicitly in `queue`, then wait for it: a sub-job with a durable queue."""
    parent_executor = counted_step(f"{label}.parent")
    handle = DBOS.enqueue_workflow(queue, child_work, f"{label}.child")
    mark(f"{label}.child_enqueued")
    return {"parent_executor": parent_executor, "child_executor": handle.get_result()}


# ------------------------------------------------------------------ process


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--schema", required=True)
    parser.add_argument("--markers", required=True, type=Path)
    parser.add_argument("--listen", default="", help="comma-separated queue names; empty = no user queue")
    parser.add_argument("--executor-id", default=None, help="DBOS config executor_id; unset = DBOS__VMID")
    parser.add_argument("--exit-after-recovery", action="store_true")
    parser.add_argument("--exit-on-stdin-eof", action="store_true", help="die with the parent holding stdin")
    parser.add_argument("--no-executor-lock", action="store_true", help="stock DBOS: no single-process guard")
    parser.add_argument("--lock-wait", type=float, default=10.0, help="seconds to wait for the executor lock")
    return parser.parse_args(argv)


def executor_lock_key(app: str, schema: str, executor_id: str) -> int:
    """Signed 64-bit key for `pg_try_advisory_lock`, one per (application, system schema, executor id)."""
    digest = hashlib.sha256(f"{app}\0{schema}\0{executor_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=True)


def hold_executor_lock(url: str, key: int, wait_s: float) -> sa.Connection | None:
    """Take the session advisory lock on a dedicated connection (kept open), or None if another process holds it.

    Waiting a little covers a restart right after SIGKILL: the dead process's backend releases the lock only
    once Postgres notices the closed socket."""
    engine = sa.create_engine(sa.make_url(url).set(drivername="postgresql+psycopg"), poolclass=NullPool)
    conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    deadline = time.monotonic() + wait_s
    while not conn.execute(sa.text("SELECT pg_try_advisory_lock(:key)"), {"key": key}).scalar_one():
        if time.monotonic() >= deadline:
            conn.close()
            engine.dispose()
            return None
        time.sleep(LOCK_POLL_S)
    return conn


def watch_executor_lock(conn: sa.Connection) -> None:
    """Exit at once when the lock connection dies: from then on another process may take the executor id."""
    while True:
        time.sleep(LOCK_CHECK_S)
        try:
            conn.execute(sa.text("SELECT 1")).scalar_one()
        except Exception as exc:  # any failure means the session, hence the lock, may be gone
            print(f"LOCK LOST {type(exc).__name__}", flush=True)
            os._exit(EXIT_LOCK_LOST)


def watch_stdin_eof() -> None:
    while os.read(0, 4096):
        pass
    print("PARENT GONE", flush=True)
    os._exit(EXIT_PARENT_GONE)


def wait_own_recovery(timeout_s: float = 20.0) -> int:
    """Wait until no PENDING workflow is left on this executor (startup recovery re-enqueues them)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        pending = DBOS.list_workflows(status="PENDING", executor_id=DBOS.executor_id, load_input=False, load_output=False)
        if not pending:
            return 0
        time.sleep(0.01)
    return len(pending)


def main(argv: list[str]) -> int:
    global MARKERS
    args = parse_args(argv)
    url = os.environ.get(DB_URL_ENV)
    if not url:
        print(f"{DB_URL_ENV} is not set", file=sys.stderr, flush=True)
        return 2
    MARKERS = args.markers
    MARKERS.mkdir(parents=True, exist_ok=True)
    if args.exit_on_stdin_eof:
        threading.Thread(target=watch_stdin_eof, name="stdin-eof", daemon=True).start()
    executor_id = args.executor_id or os.environ.get("DBOS__VMID") or "local"  # same resolution as DBOS
    if not args.no_executor_lock:
        key = executor_lock_key(APP_NAME, args.schema, executor_id)
        lock = hold_executor_lock(url, key, args.lock_wait)
        if lock is None:
            print(f"REFUSED executor_id={executor_id} reason=executor-lock-held pid={os.getpid()}", flush=True)
            return EXIT_LOCK_HELD
        backend: int = lock.execute(sa.text("SELECT pg_backend_pid()")).scalar_one()
        print(f"LOCKED executor_id={executor_id} backend_pid={backend} pid={os.getpid()}", flush=True)
        threading.Thread(target=watch_executor_lock, args=(lock,), name="executor-lock", daemon=True).start()
    listen = [name for name in args.listen.split(",") if name]
    config: DBOSConfig = {
        "name": APP_NAME,
        "system_database_url": url,
        "dbos_system_schema": args.schema,
        "application_version": APP_VERSION,
        "log_level": "INFO",
    }
    if args.executor_id is not None:
        config["executor_id"] = args.executor_id
    DBOS(config=config)
    DBOS.listen_queues(listen)
    DBOS.launch()
    if args.exit_after_recovery:
        left = wait_own_recovery()
        print(f"RECOVERED executor_id={DBOS.executor_id} left_pending={left}", flush=True)
        os._exit(0 if left == 0 else 3)  # no graceful shutdown: this life must not dequeue anything
    for name, (worker_concurrency, global_concurrency) in QUEUES.items():
        DBOS.register_queue(
            name,
            worker_concurrency=worker_concurrency,
            global_concurrency=global_concurrency,
            on_conflict="never_update",
        )
    print(f"READY executor_id={DBOS.executor_id} listen={','.join(listen)} pid={os.getpid()}", flush=True)
    threading.Event().wait()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
