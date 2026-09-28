"""SQL engine shared by the artifact index, the cost ledger and the job queue (SQLAlchemy 2 Core).

- Postgres (production, ADR-001): row locks, `FOR UPDATE SKIP LOCKED` for the queue.
- SQLite (tests, local dry runs): WAL + `BEGIN IMMEDIATE`, so every write transaction is serialised and a
  read-then-write inside one transaction cannot race another writer.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event


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
