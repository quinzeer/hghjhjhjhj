"""Content-addressed artifact store: files on the local disk, index in SQL (ADR-001 decision 6).

Layout: ``<root>/cas/<first two hex digits>/<sha256>``. A file is written to a temporary file in its final
directory, fsynced, then renamed with ``os.replace``: a reader never sees a partial file.

Consistency rules
- A file is on disk before its index row is committed. An artifact is readable only if its row exists and
  its file has the indexed size; otherwise it reads as missing (``get``, ``has``, ``step_output``) and the
  next ``put`` of the same bytes rewrites the file.
- Retention counts from the latest ``put``: storing bytes that are already present moves ``created_at``
  forward (never backward), so an artifact a producer has just been handed is not purged as old.
- ``commit_step_output`` is first-write-wins: ``INSERT ... ON CONFLICT DO NOTHING``, then the bound key is
  read back under a row lock, so every concurrent producer of a step gets the same answer. The one
  exception is a winner whose output is no longer readable: the step is rebound to the caller's output,
  otherwise a replan could never recompute it.
- A purge deletes rows, then files, then commits. If it dies between an unlink and the commit, the rows
  come back without their files: they read as missing, steps bound to them are rebound by the next commit,
  and the next purge removes them.
- Pins and step outputs reference ``artifacts.key`` by foreign key. On Postgres a purge locks the rows it
  deletes (``FOR UPDATE SKIP LOCKED``): a concurrent put, pin or commit either makes the purge skip that
  artifact or waits for it (a put then stores the artifact again; a pin or commit fails with
  ``ArtifactMissing``). On SQLite, ``BEGIN IMMEDIATE`` (see ``db.py``) serialises every write transaction.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import logging
import os
import re
import tempfile
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO

from sqlalchemy import (
    BigInteger,
    Column,
    ColumnElement,
    Connection,
    DateTime,
    Engine,
    ForeignKey,
    MetaData,
    Row,
    String,
    Table,
    delete,
    exists,
    func,
    select,
    update,
)
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Dialect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import TypeDecorator

from studio.core.db import UtcDateTime, create_tables, dialect_insert
from studio.core.hashing import bytes_key
from studio.core.interfaces import ArtifactMissing, StoredArtifact

log = logging.getLogger(__name__)

KINDS = frozenset({"image", "video", "audio", "subtitle", "json", "text"})
_KEY_RE = re.compile(r"^[0-9a-f]{64}$")
_CHUNK = 1 << 20
_BATCH = 500
_COMMIT_ATTEMPTS = 5
def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _greatest(conn: Connection, a: ColumnElement[Any], b: ColumnElement[Any]) -> ColumnElement[Any]:
    """SQL maximum of two values (SQLite's two-argument `max` is its `greatest`)."""
    return func.greatest(a, b) if conn.dialect.name == "postgresql" else func.max(a, b)


_metadata = MetaData()

artifacts = Table(
    "artifacts",
    _metadata,
    Column("key", String(64), primary_key=True),
    Column("kind", String(16), nullable=False),
    Column("media_type", String(255), nullable=False),
    Column("size_bytes", BigInteger, nullable=False),
    Column("created_at", UtcDateTime(), nullable=False, index=True),
)

step_outputs = Table(
    "step_outputs",
    _metadata,
    Column("step_key", String(128), primary_key=True),
    Column("artifact_key", String(64), ForeignKey("artifacts.key"), nullable=False, index=True),
    Column("committed_at", UtcDateTime(), nullable=False),
)

pins = Table(
    "pins",
    _metadata,
    Column("artifact_key", String(64), ForeignKey("artifacts.key"), primary_key=True),
    Column("owner", String(255), primary_key=True),
)


def _check_key(key: str) -> None:
    if not _KEY_RE.fullmatch(key):
        raise ValueError(f"not an artifact key (64 lowercase hex digits): {key!r}")


def _check_meta(kind: str, media_type: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"unknown artifact kind {kind!r}; expected one of {sorted(KINDS)}")
    if not media_type or "/" not in media_type:
        raise ValueError(f"invalid media type: {media_type!r}")


def _present(path: Path, size: int) -> bool:
    try:
        return path.is_file() and path.stat().st_size == size
    except OSError:
        return False


def _hash_file(src: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with src.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _write_atomic(path: Path, fill: Callable[[BinaryIO], None]) -> None:
    """Write through a temporary file in the destination directory, then rename it over `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fill(fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _batches(keys: Sequence[str]) -> Iterator[Sequence[str]]:
    for i in range(0, len(keys), _BATCH):
        yield keys[i : i + _BATCH]


class LocalArtifactStore:
    """`ArtifactStore` on a local directory, indexed in the SQL database behind `engine`.

    Storing bytes that are already present rewrites nothing and returns the existing entry, including the
    kind and media type it was first stored with. `clock` (aware UTC) stamps `created_at`, the time of the
    latest put, from which retention counts."""

    def __init__(self, root: Path, engine: Engine, *, clock: Callable[[], dt.datetime] = _utcnow) -> None:
        self.root = Path(root)
        self.cas = self.root / "cas"
        self.engine = engine
        self._clock = clock

    def create_schema(self) -> None:
        """Create the directory and the index tables if they do not exist (idempotent, concurrency-safe)."""
        self.cas.mkdir(parents=True, exist_ok=True)
        create_tables(self.engine, _metadata)

    def path_for(self, key: str) -> Path:
        _check_key(key)
        return self.cas / key[:2] / key

    # ------------------------------------------------------------------ writes

    def put_bytes(self, data: bytes, *, kind: str, media_type: str) -> StoredArtifact:
        _check_meta(kind, media_type)

        def fill(fh: BinaryIO) -> None:
            fh.write(data)

        return self._store(bytes_key(data), len(data), kind, media_type, fill)

    def put_file(self, src: Path, *, kind: str, media_type: str) -> StoredArtifact:
        """Stream `src` into the store: hashed first, then copied only if absent, the copy being re-hashed
        so that a source modified in between is refused (ValueError) instead of stored under a wrong key."""
        _check_meta(kind, media_type)
        src = Path(src)
        key, size = _hash_file(src)

        def fill(fh: BinaryIO) -> None:
            digest = hashlib.sha256()
            with src.open("rb") as s:
                for chunk in iter(lambda: s.read(_CHUNK), b""):
                    digest.update(chunk)
                    fh.write(chunk)
            if digest.hexdigest() != key:
                raise ValueError(f"{src} changed while being stored")

        return self._store(key, size, kind, media_type, fill)

    def _store(self, key: str, size: int, kind: str, media_type: str, fill: Callable[[BinaryIO], None]) -> StoredArtifact:
        path = self.path_for(key)
        if not _present(path, size):
            _write_atomic(path, fill)
        with self.engine.begin() as conn:
            stmt = dialect_insert(conn, artifacts).values(
                key=key, kind=kind, media_type=media_type, size_bytes=size, created_at=self._clock()
            )
            # An update rather than DO NOTHING: it restarts the retention age, and it locks the row, so a
            # concurrent purge either skips it, or has already deleted it (the insert then succeeds).
            latest = _greatest(conn, artifacts.c.created_at, stmt.excluded.created_at)
            conn.execute(stmt.on_conflict_do_update(index_elements=[artifacts.c.key], set_={"created_at": latest}))
            row = conn.execute(select(artifacts).where(artifacts.c.key == key)).one()
            if not _present(path, size):  # a purge removed the file after the first check
                _write_atomic(path, fill)
        return self._stored(row)

    def commit_step_output(self, step_key: str, artifact_key: str) -> str:
        """First write wins; a winner whose output is no longer readable is replaced by `artifact_key`."""
        if not step_key:
            raise ValueError("step_key is required")
        _check_key(artifact_key)
        for _ in range(_COMMIT_ATTEMPTS):
            with self.engine.begin() as conn:
                if self._indexed_size(conn, artifact_key) is None:
                    raise ArtifactMissing(f"{artifact_key}: cannot bind step {step_key} to an unstored artifact")
                now = self._clock()
                stmt = dialect_insert(conn, step_outputs).values(step_key=step_key, artifact_key=artifact_key, committed_at=now)
                try:
                    conn.execute(stmt.on_conflict_do_nothing(index_elements=[step_outputs.c.step_key]))
                    bound = conn.execute(
                        select(step_outputs.c.artifact_key).where(step_outputs.c.step_key == step_key).with_for_update()
                    ).scalar()
                    if bound is None:
                        continue  # the winner was purged between our insert and the read: try again
                    if bound == artifact_key or self._readable(conn, str(bound)):
                        return str(bound)
                    conn.execute(
                        update(step_outputs)
                        .where(step_outputs.c.step_key == step_key, step_outputs.c.artifact_key == bound)
                        .values(artifact_key=artifact_key, committed_at=now)
                    )
                except IntegrityError as exc:  # foreign key: purged between the check and the write
                    raise ArtifactMissing(f"{artifact_key}: purged while binding step {step_key}") from exc
            log.warning("step %s was bound to %s, which is no longer readable: rebound to %s", step_key, bound, artifact_key)
            return artifact_key
        raise RuntimeError(f"could not bind step {step_key} after {_COMMIT_ATTEMPTS} attempts")

    def pin(self, artifact_key: str, owner: str) -> None:
        _check_key(artifact_key)
        if not owner:
            raise ValueError("owner is required")
        with self.engine.begin() as conn:
            if conn.execute(select(artifacts.c.key).where(artifacts.c.key == artifact_key)).first() is None:
                raise ArtifactMissing(f"{artifact_key}: cannot pin an unstored artifact")
            stmt = dialect_insert(conn, pins).values(artifact_key=artifact_key, owner=owner)
            try:
                conn.execute(stmt.on_conflict_do_nothing(index_elements=[pins.c.artifact_key, pins.c.owner]))
            except IntegrityError as exc:
                raise ArtifactMissing(f"{artifact_key}: purged while being pinned") from exc

    def unpin(self, artifact_key: str, owner: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(pins).where(pins.c.artifact_key == artifact_key, pins.c.owner == owner))

    def purge_unpinned(self, older_than: dt.timedelta) -> list[str]:
        """Delete unpinned artifacts whose latest put is before `now - older_than`, with the step links that
        point to them (so a replan recomputes those steps). Returns the purged keys, sorted."""
        if older_than < dt.timedelta(0):
            raise ValueError("older_than must be >= 0")
        cutoff = self._clock() - older_than
        is_pinned = exists().where(pins.c.artifact_key == artifacts.c.key)
        with self.engine.begin() as conn:
            candidates = [
                str(row[0])
                for row in conn.execute(
                    select(artifacts.c.key)
                    .where(artifacts.c.created_at < cutoff, ~is_pinned)
                    .order_by(artifacts.c.key)
                    .with_for_update(skip_locked=True)
                ).all()
            ]
            pinned = self._pinned_among(conn, candidates)
            keys = [k for k in candidates if k not in pinned]
            for batch in _batches(keys):
                conn.execute(delete(step_outputs).where(step_outputs.c.artifact_key.in_(batch)))
                conn.execute(delete(artifacts).where(artifacts.c.key.in_(batch)))
            for key in keys:
                self.path_for(key).unlink(missing_ok=True)
        return keys

    @staticmethod
    def _pinned_among(conn: Connection, keys: Sequence[str]) -> set[str]:
        """Keys pinned now. The purge's candidate query filters pins with its statement snapshot, so a pin
        committed after that snapshot but before the row was locked is only visible to a new statement."""
        pinned: set[str] = set()
        for batch in _batches(keys):
            rows = conn.execute(select(pins.c.artifact_key).where(pins.c.artifact_key.in_(batch))).all()
            pinned.update(str(row[0]) for row in rows)
        return pinned

    # ------------------------------------------------------------------ reads

    def get(self, key: str) -> StoredArtifact:
        if not _KEY_RE.fullmatch(key):
            raise ArtifactMissing(f"{key!r}: not an artifact key")
        with self.engine.connect() as conn:
            row = conn.execute(select(artifacts).where(artifacts.c.key == key)).one_or_none()
        if row is None:
            raise ArtifactMissing(f"{key}: not in the index")
        stored = self._stored(row)
        if not _present(stored.path, stored.size_bytes):
            raise ArtifactMissing(f"{key}: indexed but missing on disk, or not of its indexed size ({stored.path})")
        return stored

    def has(self, key: str) -> bool:
        try:
            self.get(key)
        except ArtifactMissing:
            return False
        return True

    def verify(self, key: str) -> bool:
        """Re-hash the stored file: True when it matches its key. A corrupt file is deleted, so that it reads
        as missing and the next put of the right bytes rewrites it; False then, and when it is missing."""
        try:
            stored = self.get(key)
            with stored.path.open("rb") as fh:
                digest = hashlib.file_digest(fh, "sha256").hexdigest()
                inode = os.fstat(fh.fileno()).st_ino
        except (ArtifactMissing, FileNotFoundError):
            return False
        if digest == key:
            return True
        log.warning("artifact %s is corrupt on disk (content hashes to %s): file removed", key, digest)
        with contextlib.suppress(FileNotFoundError):
            if stored.path.stat().st_ino == inode:  # not a good copy written in the meantime
                stored.path.unlink()
        return False

    def step_output(self, step_key: str) -> str | None:
        """The output bound to this step, or None when there is none or it is no longer readable (the step
        must then be recomputed, and its next commit replaces the binding)."""
        with self.engine.connect() as conn:
            bound = conn.execute(select(step_outputs.c.artifact_key).where(step_outputs.c.step_key == step_key)).scalar()
            if bound is None or not self._readable(conn, str(bound)):
                return None
        return str(bound)

    def pinned(self, owner: str) -> list[str]:
        """Keys pinned by `owner`, sorted."""
        with self.engine.connect() as conn:
            rows = conn.execute(select(pins.c.artifact_key).where(pins.c.owner == owner).order_by(pins.c.artifact_key))
            return [str(row[0]) for row in rows.all()]

    def pinned_by(self, artifact_key: str) -> list[str]:
        """Owners that pin this artifact, sorted."""
        with self.engine.connect() as conn:
            rows = conn.execute(select(pins.c.owner).where(pins.c.artifact_key == artifact_key).order_by(pins.c.owner))
            return [str(row[0]) for row in rows.all()]

    @staticmethod
    def _indexed_size(conn: Connection, key: str) -> int | None:
        size = conn.execute(select(artifacts.c.size_bytes).where(artifacts.c.key == key)).scalar()
        return None if size is None else int(size)

    def _readable(self, conn: Connection, key: str) -> bool:
        """Indexed, and its file is on disk with the indexed size."""
        size = self._indexed_size(conn, key)
        return size is not None and _present(self.path_for(key), size)

    def _stored(self, row: Row[Any]) -> StoredArtifact:
        m = row._mapping
        key = str(m["key"])
        return StoredArtifact(
            key=key,
            kind=str(m["kind"]),
            media_type=str(m["media_type"]),
            size_bytes=int(m["size_bytes"]),
            path=self.path_for(key),
        )
