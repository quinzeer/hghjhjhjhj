"""The suite runs against whatever database STUDIO_TEST_PG_URL names: it must never wipe one (critic R7)."""

from __future__ import annotations

import re
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\b(drop\s+table|drop\s+database|truncate\s+table|drop_all)\b", re.IGNORECASE)


def test_no_test_wipes_a_table_or_a_database_it_does_not_own() -> None:
    """A test that needs Postgres creates a schema of its own and drops that schema, nothing else."""
    offenders = []
    for path in sorted(TESTS.rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FORBIDDEN.search(line):
                offenders.append(f"{path.relative_to(TESTS)}:{number}: {line.strip()}")
    assert offenders == []


def test_the_guard_recognises_what_it_forbids() -> None:
    assert FORBIDDEN.search('conn.execute(text("DROP TABLE IF EXISTS gate_decisions"))')
    assert FORBIDDEN.search("metadata.drop_all(engine)")
    assert not FORBIDDEN.search("conn.execute(text(f'DROP SCHEMA \"{name}\" CASCADE'))")
