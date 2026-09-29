"""SqlDecisionStore: decisions bound to an exact subject, replaced by a later decision on the same subject."""

from __future__ import annotations

import datetime as dt
import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from studio.core.db import make_engine
from studio.core.decisions import SqlDecisionStore
from studio.core.interfaces import DecisionSource
from studio.domain import GateDecision, GateName, Verdict

A = "a" * 64
B = "b" * 64
NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)


@pytest.fixture(params=["sqlite", "postgres"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SqlDecisionStore:
    if request.param == "sqlite":
        engine = make_engine(f"sqlite:///{tmp_path / 'd.db'}")
    else:
        url = os.environ.get("STUDIO_TEST_PG_URL")
        if not url:
            pytest.skip("STUDIO_TEST_PG_URL not set")
        engine = make_engine(url)
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS gate_decisions"))
    s = SqlDecisionStore(engine)
    s.create_schema()
    return s


def decision(gate: GateName = GateName.G2, subject: str = A, **kw: object) -> GateDecision:
    base: dict[str, object] = dict(gate=gate, subject_key=subject, agent_verdict=Verdict.APPROVE, decided_at=NOON)
    base.update(kw)
    return GateDecision(**base)  # type: ignore[arg-type]


def test_satisfies_the_decision_source_protocol(store: SqlDecisionStore) -> None:
    assert isinstance(store, DecisionSource)


def test_unknown_subject_has_no_decision(store: SqlDecisionStore) -> None:
    assert store.get(GateName.G1, A) is None


def test_put_then_get_round_trips_every_field(store: SqlDecisionStore) -> None:
    d = decision(
        GateName.COMPLIANCE,
        agent_reasons=("script publishable", "disclosure present — “réaliste”"),
        human_verdict=Verdict.PENDING,
        human_note="vu sur téléphone",
    )
    store.put(d)
    assert store.get(GateName.COMPLIANCE, A) == d


def test_a_decision_is_bound_to_its_gate_and_its_exact_subject(store: SqlDecisionStore) -> None:
    store.put(decision(GateName.G2, A))
    assert store.get(GateName.G2, B) is None  # a new render needs a new decision
    assert store.get(GateName.G1, A) is None  # another gate is not this decision


def test_a_later_decision_on_the_same_subject_replaces_the_earlier_one(store: SqlDecisionStore) -> None:
    store.put(decision(human_verdict=Verdict.PENDING))
    store.put(decision(human_verdict=Verdict.APPROVE, human_note="ok"))
    got = store.get(GateName.G2, A)
    assert got is not None and got.approved and got.human_note == "ok"


def test_the_same_decision_can_be_recorded_twice(store: SqlDecisionStore) -> None:
    d = decision(human_verdict=Verdict.APPROVE)
    store.put(d)
    store.put(d)
    assert store.get(GateName.G2, A) == d


def test_a_rejection_is_kept_as_a_rejection(store: SqlDecisionStore) -> None:
    store.put(decision(GateName.COMPLIANCE, agent_verdict=Verdict.REJECT, agent_reasons=("fake event shown as real",)))
    got = store.get(GateName.COMPLIANCE, A)
    assert got is not None and not got.approved and got.agent_reasons == ("fake event shown as real",)


def test_two_stores_on_one_database_see_each_other(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'shared.db'}"
    first, second = SqlDecisionStore(make_engine(url)), SqlDecisionStore(make_engine(url))
    first.create_schema()
    second.create_schema()  # idempotent
    first.put(decision())
    assert second.get(GateName.G2, A) == decision()


def test_gate_names_are_validated_on_read(store: SqlDecisionStore) -> None:
    with pytest.raises(ValueError):
        store.get("not-a-gate", A)  # type: ignore[arg-type]


def test_unique_table_per_database(store: SqlDecisionStore) -> None:
    # sanity: the schema creation of one test does not leak rows into another
    assert store.get(GateName.G2, uuid.uuid4().hex * 2) is None
