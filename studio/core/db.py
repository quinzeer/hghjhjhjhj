"""SQL engine shared by the artifact index, the cost ledger and the job queue (SQLAlchemy 2 Core).

- Postgres (production, ADR-001): row locks, `FOR UPDATE SKIP LOCKED` for the queue.
- SQLite (tests, local dry runs): WAL + `BEGIN IMMEDIATE`, so every write transaction is serialised and a
  read-then-write inside one transaction cannot race another writer.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Connection, DateTime, Engine, MetaData, Table, create_engine, event, func, inspect, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from studio.core.interfaces import StudioError

# Postgres advisory lock (any fixed int64) taken by every `create_tables` of the studio's SQL tables.
SCHEMA_LOCK_KEY = 0x5354_5544_494F_0001


def make_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(engine, "connect")
        def _on_connect(dbapi_conn: Any, _record: Any) -> None:
            dbapi_conn.isolation_level = None  # let the "begin" hook below emit BEGIN itself
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        @event.listens_for(engine, "begin")
        def _on_begin(conn: Any) -> None:
            conn.exec_driver_sql("BEGIN IMMEDIATE")

        return engine
    return create_engine(url, pool_pre_ping=True)


def is_sqlite(engine: Engine) -> bool:
    return engine.dialect.name == "sqlite"


def as_utc(value: dt.datetime) -> dt.datetime:
    """Aware UTC datetime; a naive value is taken as UTC."""
    return value.replace(tzinfo=dt.UTC) if value.tzinfo is None else value.astimezone(dt.UTC)


class UtcDateTime(TypeDecorator[dt.datetime]):
    """Aware UTC timestamps on every backend. SQLite has no time zone type and compares timestamps as
    text, so values are normalised to UTC before binding and read back as aware UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        if value is None:
            return None
        utc = as_utc(value)
        return utc.replace(tzinfo=None) if dialect.name == "sqlite" else utc

    def process_result_value(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        return None if value is None else as_utc(value)


def dialect_insert(conn: Connection, table: Table) -> postgresql.Insert | sqlite.Insert:
    """Dialect INSERT that supports ON CONFLICT (Postgres and SQLite only)."""
    name = conn.dialect.name
    if name == "postgresql":
        return postgresql.insert(table)
    if name == "sqlite":
        return sqlite.insert(table)
    raise NotImplementedError(f"unsupported SQL dialect: {name}")


class SchemaMismatch(StudioError):
    """The database holds tables written by another version of the studio."""


def create_tables(engine: Engine, metadata: MetaData) -> None:
    """Create the missing tables of `metadata`; idempotent, and safe when several workers start at once.

    `create_all` checks for a table and creates it in separate statements, so on Postgres two concurrent
    calls can both decide to create it and one fails: a transaction-scoped advisory lock serialises them.
    On SQLite the `BEGIN IMMEDIATE` transaction already does.

    A table that exists is never altered (there is no migration yet): its columns must be the declared ones,
    or the call raises `SchemaMismatch` in words, instead of the first insert failing on a missing column."""
    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(select(func.pg_advisory_xact_lock(SCHEMA_LOCK_KEY)))
        metadata.create_all(conn)
        _check_columns(conn, metadata)


def _check_columns(conn: Connection, metadata: MetaData) -> None:
    inspector = inspect(conn)
    translate = conn.get_execution_options().get("schema_translate_map") or {}  # reflection does not apply it by itself
    problems: list[str] = []
    for table in metadata.sorted_tables:
        found = {column["name"] for column in inspector.get_columns(table.name, schema=translate.get(table.schema))}
        declared = {column.name for column in table.columns}
        if declared - found:
            problems.append(f"table {table.name!r} lacks the column(s) {sorted(declared - found)}")
        if found - declared:
            problems.append(f"table {table.name!r} has the unknown column(s) {sorted(found - declared)}")
    if problems:
        raise SchemaMismatch(
            "the database was written by another version of the studio: " + "; ".join(problems) + ". "
            "The state folder of a dry run (`<out>/state`) can be removed; there is no migration yet."
        )
