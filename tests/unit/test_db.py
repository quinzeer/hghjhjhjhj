"""Table creation: idempotent, and refused in words when the tables come from another version (critic m-3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Column, Engine, Integer, MetaData, String, Table, inspect

from studio.core.artifacts import LocalArtifactStore
from studio.core.costs import SqlCostLedger
from studio.core.db import SchemaMismatch, create_tables, make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.interfaces import StudioError
from studio.core.queue import SqlJobQueue


def engine_in(tmp_path: Path) -> Engine:
    return make_engine(f"sqlite:///{tmp_path / 'state.db'}")


def declared() -> MetaData:
    metadata = MetaData()
    Table("things", metadata, Column("id", Integer, primary_key=True), Column("name", String(20), nullable=False))
    return metadata


def test_creating_the_same_tables_twice_changes_nothing(tmp_path: Path) -> None:
    engine = engine_in(tmp_path)
    create_tables(engine, declared())
    create_tables(engine, declared())
    assert {c["name"] for c in inspect(engine).get_columns("things")} == {"id", "name"}


def test_a_table_lacking_a_declared_column_is_refused_in_words(tmp_path: Path) -> None:
    engine = engine_in(tmp_path)
    with engine.begin() as conn:
        conn.exec_driver_sql("create table things (id integer primary key)")
    with pytest.raises(SchemaMismatch, match=r"another version of the studio.*'things' lacks the column\(s\) \['name'\]"):
        create_tables(engine, declared())


def test_a_table_with_an_unknown_column_is_refused_in_words(tmp_path: Path) -> None:
    engine = engine_in(tmp_path)
    with engine.begin() as conn:
        conn.exec_driver_sql("create table things (id integer primary key, name varchar(20) not null, colour text not null)")
    with pytest.raises(SchemaMismatch, match=r"'things' has the unknown column\(s\) \['colour'\]"):
        create_tables(engine, declared())


def test_a_schema_mismatch_is_a_studio_error_so_the_command_line_reports_it_without_a_trace() -> None:
    assert issubclass(SchemaMismatch, StudioError)


@pytest.mark.parametrize("backend", ["artifacts", "costs", "decisions", "queue"])
def test_every_backend_of_the_studio_checks_its_tables(tmp_path: Path, backend: str) -> None:
    engine = engine_in(tmp_path)
    table = {"artifacts": "artifacts", "costs": "caps", "decisions": "gate_decisions", "queue": "step_claims"}[backend]
    with engine.begin() as conn:
        conn.exec_driver_sql(f"create table {table} (something_else text)")
    schema = {
        "artifacts": lambda: LocalArtifactStore(tmp_path / "cas", engine).create_schema(),
        "costs": lambda: SqlCostLedger(engine).create_schema(),
        "decisions": lambda: SqlDecisionStore(engine).create_schema(),
        "queue": lambda: SqlJobQueue(engine).create_schema(),
    }[backend]
    with pytest.raises(SchemaMismatch, match=f"'{table}'"):
        schema()
