"""The session guard that keeps the suite inside its own schemas (critic R7): it sees a write to a studio table of the
default schema. Skipped unless STUDIO_TEST_PG_URL is set."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from conftest import changed_tables, default_schema_fingerprint
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url

from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.domain import GateDecision, GateName, Verdict

PG_URL = os.environ.get("STUDIO_TEST_PG_URL", "")

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(not PG_URL, reason="STUDIO_TEST_PG_URL is not set")]


@pytest.fixture
def default_like_schema() -> Iterator[tuple[str, Engine]]:
    """A schema of its own that plays the default one: the URL puts it first on the search path."""
    admin = make_engine(PG_URL)
    schema = f"test_guard_{uuid.uuid4().hex[:12]}"
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = make_url(PG_URL).update_query_dict({"options": f"-c search_path={schema}"}).render_as_string(hide_password=False)
    try:
        yield url, admin
    finally:
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def test_the_guard_sees_a_row_written_to_a_studio_table_of_the_default_schema(default_like_schema: tuple[str, Engine]) -> None:
    url, _ = default_like_schema
    store = SqlDecisionStore(make_engine(url))
    store.create_schema()
    before = default_schema_fingerprint(url)
    assert before is not None and set(before) == {"gate_decisions"}
    assert default_schema_fingerprint(url) == before  # reading changes nothing

    store.put(GateDecision(gate=GateName.G2, subject_key="a" * 64, agent_verdict=Verdict.APPROVE, human_verdict=Verdict.APPROVE))
    after = default_schema_fingerprint(url)
    assert after is not None and changed_tables(before, after) == ["gate_decisions"]

    store.put(GateDecision(gate=GateName.G2, subject_key="a" * 64, agent_verdict=Verdict.APPROVE, human_verdict=Verdict.REJECT))
    rewritten = default_schema_fingerprint(url)  # the same row count, another content: a count of rows would not see it
    assert rewritten is not None and changed_tables(after, rewritten) == ["gate_decisions"]


def test_the_guard_sees_a_studio_table_that_appears_or_vanishes(default_like_schema: tuple[str, Engine]) -> None:
    url, admin = default_like_schema
    empty = default_schema_fingerprint(url)
    assert empty == {}
    SqlDecisionStore(make_engine(url)).create_schema()
    created = default_schema_fingerprint(url)
    assert created is not None and changed_tables(empty or {}, created) == ["gate_decisions"]


def test_a_database_that_cannot_be_reached_has_no_fingerprint() -> None:
    assert default_schema_fingerprint("postgresql+psycopg://nobody@127.0.0.1:1/none?connect_timeout=1") is None
