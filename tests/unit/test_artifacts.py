"""LocalArtifactStore on SQLite: dedup, atomic writes, first-write-wins commits, pins and purge."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, func, select

import studio.core.artifacts as artifacts_module
from studio.core.artifacts import LocalArtifactStore, artifacts
from studio.core.db import make_engine
from studio.core.hashing import bytes_key
from studio.core.interfaces import ArtifactMissing, ArtifactStore

T0 = dt.datetime(2026, 9, 1, 12, 0, tzinfo=dt.UTC)
THREADS = 8
REPO_ROOT = Path(__file__).resolve().parents[2]

# Child process: runs a purge and SIGKILLs itself right after the first file is unlinked, before the commit.
PURGE_KILLED_AFTER_FIRST_UNLINK = """
import datetime as dt, os, signal, sys
from pathlib import Path
from studio.core.artifacts import LocalArtifactStore
from studio.core.db import make_engine

url, root, now, older_than_s = sys.argv[1:5]
store = LocalArtifactStore(Path(root), make_engine(url), clock=lambda: dt.datetime.fromisoformat(now))
real_unlink = Path.unlink

def unlink_then_die_mock(self, missing_ok=False):
    real_unlink(self, missing_ok=missing_ok)
    os.kill(os.getpid(), signal.SIGKILL)

Path.unlink = unlink_then_die_mock
store.purge_unpinned(dt.timedelta(seconds=float(older_than_s)))
sys.exit("the purge ran to completion: it was not killed")
"""


def purge_killed_after_first_unlink(
    engine: Engine, store: LocalArtifactStore, now: dt.datetime, older_than: dt.timedelta
) -> None:
    url = engine.url.render_as_string(hide_password=False)
    args = [url, str(store.root), now.isoformat(), str(older_than.total_seconds())]
    proc = subprocess.run(
        [sys.executable, "-c", PURGE_KILLED_AFTER_FIRST_UNLINK, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == -signal.SIGKILL, proc.stderr


class MockClock:
    """Controllable clock injected into the store (test double)."""

    def __init__(self, start: dt.datetime) -> None:
        self.now = start

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, delta: dt.timedelta) -> None:
        self.now += delta


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(f"sqlite:///{tmp_path / 'index.db'}")
    yield eng
    eng.dispose()


@pytest.fixture
def clock() -> MockClock:
    return MockClock(T0)


@pytest.fixture
def store(tmp_path: Path, engine: Engine, clock: MockClock) -> LocalArtifactStore:
    s = LocalArtifactStore(tmp_path / "store", engine, clock=clock)
    s.create_schema()
    return s


def put_text(store: LocalArtifactStore, text: str) -> str:
    return store.put_bytes(text.encode(), kind="text", media_type="text/plain").key


def index_rows(engine: Engine) -> int:
    with engine.connect() as conn:
        return int(conn.execute(select(func.count()).select_from(artifacts)).scalar() or 0)


def cas_files(store: LocalArtifactStore) -> list[Path]:
    return sorted(p for p in store.cas.rglob("*") if p.is_file())


def run_concurrently[T](n: int, fn: Callable[[int], T]) -> list[T]:
    """Run fn(i) in n threads released together by a barrier; re-raise the first error."""
    barrier = threading.Barrier(n, timeout=30)

    def task(i: int) -> T:
        barrier.wait()
        return fn(i)

    with ThreadPoolExecutor(max_workers=n) as pool:
        return [f.result(timeout=60) for f in [pool.submit(task, i) for i in range(n)]]


# ------------------------------------------------------------------ writing and reading


def test_implements_protocol(store: LocalArtifactStore) -> None:
    assert isinstance(store, ArtifactStore)


def test_put_bytes_is_addressed_by_content(store: LocalArtifactStore) -> None:
    data = b'{"scene": 1}'
    stored = store.put_bytes(data, kind="json", media_type="application/json")
    assert stored.key == bytes_key(data)
    assert stored.path == store.root / "cas" / stored.key[:2] / stored.key
    assert stored.path.read_bytes() == data
    assert (stored.kind, stored.media_type, stored.size_bytes) == ("json", "application/json", len(data))
    assert store.get(stored.key) == stored
    assert store.has(stored.key)


def test_same_bytes_twice_is_deduplicated_without_rewrite(store: LocalArtifactStore, engine: Engine) -> None:
    first = store.put_bytes(b"same content", kind="text", media_type="text/plain")
    before = first.path.stat()
    second = store.put_bytes(b"same content", kind="text", media_type="text/plain")
    after = second.path.stat()
    assert second == first
    # os.replace would give the path a new inode: an unchanged inode and mtime prove there was no rewrite
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)
    assert index_rows(engine) == 1
    assert cas_files(store) == [first.path]


def test_different_bytes_get_different_keys(store: LocalArtifactStore) -> None:
    assert put_text(store, "a") != put_text(store, "b")


def test_put_file_uses_the_same_key_as_put_bytes(store: LocalArtifactStore, tmp_path: Path, engine: Engine) -> None:
    data = bytes(range(256)) * 12_289  # > 3 MiB: several read chunks
    src = tmp_path / "clip.mp4"
    src.write_bytes(data)
    from_file = store.put_file(src, kind="video", media_type="video/mp4")
    assert from_file.key == bytes_key(data)
    assert from_file.path.read_bytes() == data
    assert from_file.size_bytes == len(data)
    assert store.put_bytes(data, kind="video", media_type="video/mp4") == from_file
    assert index_rows(engine) == 1


def test_concurrent_puts_of_the_same_bytes_store_one_copy(store: LocalArtifactStore, engine: Engine) -> None:
    data = b"rendered frame" * 1000
    keys = run_concurrently(THREADS, lambda _i: store.put_bytes(data, kind="image", media_type="image/png").key)
    assert set(keys) == {bytes_key(data)}
    assert index_rows(engine) == 1
    assert [p.name for p in cas_files(store)] == [bytes_key(data)]  # no temporary file left behind


def test_write_goes_through_a_temporary_file_renamed_into_place(
    store: LocalArtifactStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"frame " * 10_000
    final = store.path_for(bytes_key(data))
    real_replace = os.replace
    renames: list[tuple[Path, Path]] = []

    def replace_spy_mock(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        tmp, dest = Path(src), Path(dst)
        # until the rename, the final path does not exist and the whole content sits in a sibling temporary file
        assert not dest.exists()
        assert tmp.parent == dest.parent and tmp.name.startswith(".tmp-")
        assert tmp.read_bytes() == data
        renames.append((tmp, dest))
        real_replace(src, dst)

    monkeypatch.setattr(artifacts_module.os, "replace", replace_spy_mock)
    stored = store.put_bytes(data, kind="image", media_type="image/png")
    assert [dest for _, dest in renames] == [final]
    assert not renames[0][0].exists()
    assert stored.path.read_bytes() == data


def test_source_changed_during_copy_leaves_no_file(
    store: LocalArtifactStore, tmp_path: Path, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "voice.wav"
    src.write_bytes(b"original take")
    real_hash_file = artifacts_module._hash_file

    def hash_then_modify_mock(path: Path) -> tuple[str, int]:
        result = real_hash_file(path)
        path.write_bytes(b"overwritten by another process")
        return result

    monkeypatch.setattr(artifacts_module, "_hash_file", hash_then_modify_mock)
    with pytest.raises(ValueError, match="changed while being stored"):
        store.put_file(src, kind="audio", media_type="audio/wav")
    assert cas_files(store) == []  # neither the final file nor the temporary one
    assert index_rows(engine) == 0
    assert not store.has(bytes_key(b"original take"))


def test_put_rewrites_a_file_removed_after_its_first_check(store: LocalArtifactStore, monkeypatch: pytest.MonkeyPatch) -> None:
    """A big object (no integrity check on a put): a purge removes the file between the size check and the index write."""
    big = LocalArtifactStore(store.root, store.engine, verify_reads_up_to=0)
    stored = big.put_bytes(b"raced by a purge", kind="text", media_type="text/plain")
    real_present = artifacts_module._present
    calls: list[bool] = []

    def present_then_vanish_mock(path: Path, size: int) -> bool:
        result = real_present(path, size)
        if not calls:
            path.unlink()  # a purge removes the file between the check and the index transaction
        calls.append(result)
        return result

    monkeypatch.setattr(artifacts_module, "_present", present_then_vanish_mock)
    assert big.put_bytes(b"raced by a purge", kind="text", media_type="text/plain") == stored
    assert calls == [True, False]
    assert stored.path.read_bytes() == b"raced by a purge"


def test_put_rewrites_a_small_file_removed_between_its_integrity_check_and_the_index_write(
    store: LocalArtifactStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    stored = store.put_bytes(b"raced by a purge", kind="text", media_type="text/plain")
    real_intact = LocalArtifactStore._file_intact
    real_present = artifacts_module._present
    checked: list[bool] = []
    presents: list[bool] = []

    def intact_then_vanish_mock(path: Path, key: str) -> bool:
        result = real_intact(path, key)
        if not checked:
            path.unlink()  # the purge comes after the file was found intact
        checked.append(result)
        return result

    def recording_present(path: Path, size: int) -> bool:
        presents.append(real_present(path, size))
        return presents[-1]

    monkeypatch.setattr(LocalArtifactStore, "_file_intact", staticmethod(intact_then_vanish_mock))
    monkeypatch.setattr(artifacts_module, "_present", recording_present)
    assert store.put_bytes(b"raced by a purge", kind="text", media_type="text/plain") == stored
    assert checked == [True] and presents == [True, False]  # found intact, then gone at the index write: rewritten there
    assert stored.path.read_bytes() == b"raced by a purge"


def test_put_rewrites_a_small_file_that_vanishes_between_the_size_check_and_the_integrity_check(
    store: LocalArtifactStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    stored = store.put_bytes(b"raced by a purge", kind="text", media_type="text/plain")
    real_present = artifacts_module._present
    calls: list[bool] = []

    def present_then_vanish_mock(path: Path, size: int) -> bool:
        result = real_present(path, size)
        if not calls:
            path.unlink()
        calls.append(result)
        return result

    monkeypatch.setattr(artifacts_module, "_present", present_then_vanish_mock)
    assert store.put_bytes(b"raced by a purge", kind="text", media_type="text/plain") == stored
    assert stored.path.read_bytes() == b"raced by a purge"  # the integrity check found the file gone: rewritten at once


def test_default_clock_is_utc_now(tmp_path: Path, engine: Engine) -> None:
    plain = LocalArtifactStore(tmp_path / "plain", engine)
    plain.create_schema()
    key = put_text(plain, "stamped now")
    assert plain.purge_unpinned(dt.timedelta(minutes=5)) == []
    assert plain.purge_unpinned(dt.timedelta(0)) == [key]


def test_rejects_unknown_kind_and_bad_media_type(store: LocalArtifactStore) -> None:
    with pytest.raises(ValueError, match="kind"):
        store.put_bytes(b"x", kind="spreadsheet", media_type="text/csv")
    with pytest.raises(ValueError, match="media type"):
        store.put_bytes(b"x", kind="text", media_type="")


def test_get_unknown_or_malformed_key_raises_missing(store: LocalArtifactStore) -> None:
    with pytest.raises(ArtifactMissing):
        store.get(bytes_key(b"never stored"))
    with pytest.raises(ArtifactMissing):
        store.get("../../etc/passwd")
    assert not store.has("../../etc/passwd")


def test_file_missing_on_disk_reads_missing_and_put_repairs(store: LocalArtifactStore) -> None:
    stored = store.put_bytes(b"lost on disk", kind="text", media_type="text/plain")
    stored.path.unlink()
    with pytest.raises(ArtifactMissing, match="missing on disk"):
        store.get(stored.key)
    assert not store.has(stored.key)
    assert store.put_bytes(b"lost on disk", kind="text", media_type="text/plain") == stored
    assert store.get(stored.key).path.read_bytes() == b"lost on disk"


def test_truncated_file_reads_missing_and_put_repairs(store: LocalArtifactStore) -> None:
    data = b"0123456789" * 100
    stored = store.put_bytes(data, kind="text", media_type="text/plain")
    stored.path.write_bytes(data[:4])  # a copy tool or a disk error cut the file short
    assert not store.has(stored.key)
    with pytest.raises(ArtifactMissing, match="indexed size"):
        store.get(stored.key)
    assert store.put_bytes(data, kind="text", media_type="text/plain") == stored
    assert store.get(stored.key).path.read_bytes() == data


def test_a_small_object_that_rotted_in_place_reads_as_missing_and_put_repairs_it(store: LocalArtifactStore) -> None:
    data = b"abcdefghij"
    good = store.put_bytes(data, kind="text", media_type="text/plain")
    assert store.get(good.key) == good
    good.path.write_bytes(b"XXXXXXXXXX")  # same size: only a re-hash can tell, and every read of a small object re-hashes
    with pytest.raises(ArtifactMissing, match="no longer matches its key"):
        store.get(good.key)
    assert not good.path.exists() and not store.has(good.key)  # the rotten file was removed: nothing serves it again
    assert store.put_bytes(data, kind="text", media_type="text/plain") == good and good.path.read_bytes() == data


def test_putting_the_right_bytes_again_repairs_a_small_object_corrupted_in_place(store: LocalArtifactStore) -> None:
    """Critic R5: a file of the right size and the wrong content is not 'present', even if nobody read it meanwhile."""
    data = b"gate token"
    good = store.put_bytes(data, kind="json", media_type="application/json")
    good.path.write_bytes(b"gate tokeX")  # same size, other bytes, and no read in between
    again = store.put_bytes(data, kind="json", media_type="application/json")
    assert again == good and good.path.read_bytes() == data
    assert store.get(good.key).path.read_bytes() == data


def test_a_put_does_not_re_hash_a_big_object_it_already_holds(tmp_path: Path, engine: Engine) -> None:
    """The cost of the check is bounded by the same limit as a read: a big object is verified by `verify`, not by a put."""
    store = LocalArtifactStore(tmp_path / "s", engine, verify_reads_up_to=4)
    store.create_schema()
    big = store.put_bytes(b"0123456789", kind="text", media_type="text/plain")  # bigger than the limit
    big.path.write_bytes(b"XXXXXXXXXX")
    store.put_bytes(b"0123456789", kind="text", media_type="text/plain")
    assert big.path.read_bytes() == b"XXXXXXXXXX"  # left alone
    assert not store.verify(big.key)  # ... and caught where it matters


def test_a_big_object_is_not_re_hashed_on_every_read_but_verify_still_catches_it(tmp_path: Path, engine: Engine) -> None:
    small_limit = LocalArtifactStore(tmp_path / "s", engine, verify_reads_up_to=4)
    small_limit.create_schema()
    stored = small_limit.put_bytes(b"0123456789", kind="text", media_type="text/plain")  # bigger than the limit
    stored.path.write_bytes(b"XXXXXXXXXX")
    assert small_limit.has(stored.key)  # a read of a big object trusts the index and the size
    assert not small_limit.verify(stored.key)  # verify re-hashes whatever the size
    assert not small_limit.has(stored.key)


def test_a_good_copy_that_lands_while_a_corrupt_one_is_being_judged_is_not_removed(
    store: LocalArtifactStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"abcdefghij"
    good = store.put_bytes(data, kind="text", media_type="text/plain")
    good.path.write_bytes(b"XXXXXXXXXX")  # rotten, same size
    real_digest = hashlib.file_digest

    def digest_then_replace(fh: Any, algorithm: str) -> Any:
        result = real_digest(fh, algorithm)  # what is judged is the rotten file ...
        landing = good.path.with_name("landing.tmp")
        landing.write_bytes(data)
        os.replace(landing, good.path)  # ... and a good copy lands under its name (another inode) before the removal
        return result

    monkeypatch.setattr(hashlib, "file_digest", digest_then_replace)
    assert store.verify(good.key) is False  # the file that was hashed was corrupt
    monkeypatch.setattr(hashlib, "file_digest", real_digest)
    assert good.path.read_bytes() == data and store.has(good.key)  # the good copy that replaced it was left alone


def test_verify_removes_a_corrupt_file_so_that_put_repairs_it(tmp_path: Path, engine: Engine) -> None:
    store = LocalArtifactStore(tmp_path / "trusting", engine, verify_reads_up_to=0)  # reads never re-hash
    store.create_schema()
    good = store.put_bytes(b"abcdefghij", kind="text", media_type="text/plain")
    assert store.verify(good.key)
    good.path.write_bytes(b"XXXXXXXXXX")  # same size: only a re-hash can tell
    assert store.has(good.key)
    assert not store.verify(good.key)
    assert not store.has(good.key)
    assert store.put_bytes(b"abcdefghij", kind="text", media_type="text/plain") == good
    assert good.path.read_bytes() == b"abcdefghij"
    assert store.verify(good.key)
    assert not store.verify(bytes_key(b"never stored"))


def test_create_schema_is_idempotent(store: LocalArtifactStore, engine: Engine) -> None:
    key = put_text(store, "kept")
    store.create_schema()
    store.create_schema()
    assert store.has(key)
    assert index_rows(engine) == 1


def test_concurrent_create_schema_on_a_fresh_database(tmp_path: Path, engine: Engine) -> None:
    run_concurrently(THREADS, lambda i: LocalArtifactStore(tmp_path / f"worker-{i}", engine).create_schema())
    store = LocalArtifactStore(tmp_path / "worker-0", engine)
    key = put_text(store, "after a concurrent start")
    assert store.commit_step_output("a" * 64, key) == key


# ------------------------------------------------------------------ step outputs


def test_commit_step_output_first_write_wins(store: LocalArtifactStore) -> None:
    step = "f" * 64
    first, second = put_text(store, "take 1"), put_text(store, "take 2")
    assert store.step_output(step) is None
    assert store.commit_step_output(step, first) == first
    assert store.commit_step_output(step, second) == first
    assert store.step_output(step) == first


def test_commit_step_output_requires_a_stored_artifact(store: LocalArtifactStore) -> None:
    with pytest.raises(ArtifactMissing):
        store.commit_step_output("e" * 64, bytes_key(b"never stored"))
    assert store.step_output("e" * 64) is None
    with pytest.raises(ValueError):
        store.commit_step_output("e" * 64, "not-a-key")
    with pytest.raises(ValueError):
        store.commit_step_output("", put_text(store, "orphan"))


def test_concurrent_commits_all_get_the_same_winner(store: LocalArtifactStore) -> None:
    for round_ in range(5):
        step = f"{round_:064x}"
        candidates = [put_text(store, f"round {round_} producer {i}") for i in range(THREADS)]
        results = run_concurrently(THREADS, lambda i, c=candidates, s=step: store.commit_step_output(s, c[i]))
        assert len(set(results)) == 1, results
        winner = results[0]
        assert winner in candidates
        assert store.step_output(step) == winner


@pytest.mark.parametrize("damage", ["deleted", "truncated"])
def test_step_bound_to_an_unreadable_output_is_rebound_by_the_next_commit(store: LocalArtifactStore, damage: str) -> None:
    step = "8" * 64
    lost = store.put_bytes(b"first take, lost since", kind="text", media_type="text/plain")
    assert store.commit_step_output(step, lost.key) == lost.key
    if damage == "deleted":
        lost.path.unlink()
    else:
        lost.path.write_bytes(b"first")
    assert store.step_output(step) is None  # the step must be recomputed
    redo = put_text(store, "second take, not bit-identical")
    assert store.commit_step_output(step, redo) == redo
    assert store.step_output(step) == redo
    assert store.commit_step_output(step, put_text(store, "third take")) == redo  # first write wins again


def test_concurrent_commits_rebind_an_unreadable_output_to_one_winner(store: LocalArtifactStore) -> None:
    for round_ in range(5):
        step = f"{round_ + 100:064x}"
        lost = store.put_bytes(f"lost take {round_}".encode(), kind="text", media_type="text/plain")
        store.commit_step_output(step, lost.key)
        lost.path.unlink()
        candidates = [put_text(store, f"round {round_} replanner {i}") for i in range(THREADS)]
        results = run_concurrently(THREADS, lambda i, c=candidates, s=step: store.commit_step_output(s, c[i]))
        assert len(set(results)) == 1, results
        assert results[0] in candidates
        assert store.step_output(step) == results[0]


def test_purge_killed_between_unlink_and_commit_then_replan_recomputes(
    store: LocalArtifactStore, engine: Engine, clock: MockClock
) -> None:
    step = "7" * 64
    old = store.put_bytes(b"take generated on day 0", kind="text", media_type="text/plain")
    assert store.commit_step_output(step, old.key) == old.key
    clock.advance(dt.timedelta(days=10))

    purge_killed_after_first_unlink(engine, store, clock.now, dt.timedelta(days=7))

    assert not old.path.exists()  # the file went before the kill...
    assert index_rows(engine) == 1  # ...but the transaction was rolled back
    assert not store.has(old.key)
    assert store.step_output(step) is None
    # the replan recomputes the step; its output is not bit-identical (GPU, LLM)
    new = store.put_bytes(b"take regenerated on day 10", kind="text", media_type="text/plain")
    assert store.commit_step_output(step, new.key) == new.key
    assert store.step_output(step) == new.key
    assert store.get(new.key).path.read_bytes() == b"take regenerated on day 10"
    assert store.purge_unpinned(dt.timedelta(days=7)) == [old.key]  # the next purge removes the stale row
    assert store.step_output(step) == new.key


# ------------------------------------------------------------------ pins and purge


def test_pin_and_unpin_are_idempotent(store: LocalArtifactStore) -> None:
    key = put_text(store, "manifest input")
    store.pin(key, "run-1")
    store.pin(key, "run-1")
    store.pin(key, "run-2")
    assert store.pinned_by(key) == ["run-1", "run-2"]
    store.unpin(key, "run-1")
    store.unpin(key, "run-1")
    store.unpin(key, "never-pinned")
    assert store.pinned_by(key) == ["run-2"]


def test_pin_unknown_artifact_or_empty_owner_raises(store: LocalArtifactStore) -> None:
    with pytest.raises(ArtifactMissing):
        store.pin(bytes_key(b"never stored"), "run-1")
    with pytest.raises(ValueError):
        store.pin(put_text(store, "owned by nobody"), "")


def test_purge_spares_pinned_and_recent_and_clears_step_links(store: LocalArtifactStore, clock: MockClock) -> None:
    old_unpinned = put_text(store, "old draft")
    old_pinned = put_text(store, "old but in a manifest")
    store.commit_step_output("1" * 64, old_unpinned)
    store.commit_step_output("2" * 64, old_pinned)
    store.pin(old_pinned, "run-1")
    clock.advance(dt.timedelta(days=10))
    recent = put_text(store, "fresh draft")
    unpinned_path = store.path_for(old_unpinned)

    assert store.purge_unpinned(dt.timedelta(days=7)) == [old_unpinned]

    assert not store.has(old_unpinned)
    assert not unpinned_path.exists()
    assert store.step_output("1" * 64) is None  # a replan recomputes this step
    assert store.has(old_pinned) and store.step_output("2" * 64) == old_pinned
    assert store.has(recent)
    assert store.purge_unpinned(dt.timedelta(days=7)) == []

    # the replan stores a new output and binds it
    redo = put_text(store, "old draft, recomputed")
    assert store.commit_step_output("1" * 64, redo) == redo


def test_purge_waits_for_every_owner_to_unpin(store: LocalArtifactStore, clock: MockClock) -> None:
    key = put_text(store, "shared asset")
    store.pin(key, "run-1")
    store.pin(key, "run-2")
    clock.advance(dt.timedelta(days=30))
    store.unpin(key, "run-1")
    assert store.purge_unpinned(dt.timedelta(days=7)) == []
    assert store.has(key)
    store.unpin(key, "run-2")
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]
    assert not store.has(key)


def test_storing_the_same_bytes_again_restarts_the_retention_age(store: LocalArtifactStore, clock: MockClock) -> None:
    key = put_text(store, "deterministic render")
    clock.advance(dt.timedelta(days=10))
    assert put_text(store, "deterministic render") == key  # a step produces the same bytes again, now
    assert store.purge_unpinned(dt.timedelta(days=7)) == []
    store.pin(key, "run-2")  # the producer can still reference what it was just handed
    store.unpin(key, "run-2")
    clock.advance(dt.timedelta(days=8))
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]


def test_retention_age_never_moves_backwards(store: LocalArtifactStore, clock: MockClock) -> None:
    clock.advance(dt.timedelta(days=5))
    key = put_text(store, "stored by a worker whose clock is right")
    clock.now = T0  # another worker, whose clock lags five days, stores the same bytes
    assert put_text(store, "stored by a worker whose clock is right") == key
    clock.now = T0 + dt.timedelta(days=12)
    assert store.purge_unpinned(dt.timedelta(days=7)) == []  # counted from day 5, not from day 0
    clock.advance(dt.timedelta(microseconds=1))
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]


def test_purge_keeps_an_artifact_exactly_at_the_cutoff(store: LocalArtifactStore, clock: MockClock) -> None:
    key = put_text(store, "exactly seven days old")
    clock.advance(dt.timedelta(days=7))
    assert store.purge_unpinned(dt.timedelta(days=7)) == []  # not older than the cutoff
    clock.advance(dt.timedelta(microseconds=1))
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]


def test_purged_content_can_be_stored_again(store: LocalArtifactStore, clock: MockClock) -> None:
    key = put_text(store, "comes back")
    clock.advance(dt.timedelta(days=10))
    assert store.purge_unpinned(dt.timedelta(days=7)) == [key]
    assert put_text(store, "comes back") == key
    assert store.get(key).path.read_text() == "comes back"
    assert store.purge_unpinned(dt.timedelta(days=7)) == []  # stored again now: recent


def test_purge_rejects_negative_age(store: LocalArtifactStore) -> None:
    with pytest.raises(ValueError):
        store.purge_unpinned(dt.timedelta(seconds=-1))
