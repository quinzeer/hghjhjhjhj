"""Gate decisions in SQL (ADR-001 decisions 8 and 9): where the validation UI, the compliance agent and the
strategist agent record their verdicts, and where the graph runner reads them (`DecisionSource`).

A decision is bound to one exact artifact: the key of a package for G1, of the final render for G2 and for
the compliance verdict. Recording a decision on the same (gate, subject) again replaces it, which is how a
human verdict arrives after the agent's: the agent writes `agent_verdict`, the UI later writes the whole
decision with `human_verdict` set. A new subject (a new render) has no decision: the gate waits again.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Callable

from sqlalchemy import Column, Engine, MetaData, String, Table, Text, select

from studio.core.db import UtcDateTime, create_tables, dialect_insert
from studio.domain import GateDecision, GateName, Verdict

_metadata = MetaData()

gate_decisions = Table(
    "gate_decisions",
    _metadata,
    Column("gate", String(16), primary_key=True),
    Column("subject_key", String(64), primary_key=True),
    Column("agent_verdict", String(16), nullable=False),
    Column("human_verdict", String(16), nullable=False),
    Column("agent_reasons", Text, nullable=False),
    Column("human_note", Text, nullable=False),
    Column("decided_at", UtcDateTime(), nullable=True),
    Column("recorded_at", UtcDateTime(), nullable=False),
)


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class SqlDecisionStore:
    """`DecisionSource` on SQLAlchemy Core (Postgres in production, SQLite for local dry runs)."""

    def __init__(self, engine: Engine, *, clock: Callable[[], dt.datetime] = _utcnow) -> None:
        self.engine = engine
        self._clock = clock

    def create_schema(self) -> None:
        create_tables(self.engine, _metadata)

    def put(self, decision: GateDecision) -> None:
        """Record `decision`, replacing any earlier decision on the same (gate, subject)."""
        values = {
            "gate": decision.gate.value,
            "subject_key": decision.subject_key,
            "agent_verdict": decision.agent_verdict.value,
            "human_verdict": decision.human_verdict.value,
            "agent_reasons": json.dumps(list(decision.agent_reasons), ensure_ascii=False),
            "human_note": decision.human_note,
            "decided_at": decision.decided_at,
            "recorded_at": self._clock(),
        }
        with self.engine.begin() as conn:
            insert = dialect_insert(conn, gate_decisions).values(**values)
            update = {k: v for k, v in values.items() if k not in ("gate", "subject_key")}
            conn.execute(insert.on_conflict_do_update(index_elements=["gate", "subject_key"], set_=update))

    def get(self, gate: GateName, subject_key: str) -> GateDecision | None:
        with self.engine.connect() as conn:
            row = (
                conn.execute(
                    select(gate_decisions).where(
                        gate_decisions.c.gate == GateName(gate).value, gate_decisions.c.subject_key == subject_key
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return GateDecision(
            gate=GateName(row["gate"]),
            subject_key=row["subject_key"],
            agent_verdict=Verdict(row["agent_verdict"]),
            human_verdict=Verdict(row["human_verdict"]),
            agent_reasons=tuple(json.loads(row["agent_reasons"])),
            human_note=row["human_note"],
            decided_at=row["decided_at"],
        )
