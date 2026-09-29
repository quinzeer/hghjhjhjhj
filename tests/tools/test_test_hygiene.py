"""The suite runs against whatever database STUDIO_TEST_PG_URL names: it must never wipe one (critic R7)."""

from __future__ import annotations

import re
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(
    r"\b(drop\s+(table|database|owned)|drop\s+schema\s+(if\s+exists\s+)?\"?public\"?|truncate|delete\s+from|drop_all)\b"
    r"|\.drop\(\s*\w*(engine|conn)",
    re.IGNORECASE,
)


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
    forbidden = [
        'conn.execute(text("DROP TABLE IF EXISTS gate_decisions"))',
        'conn.execute(text("TRUNCATE gate_decisions"))',
        'conn.execute(text("DELETE FROM gate_decisions"))',
        'conn.execute(text("DROP SCHEMA public CASCADE"))',
        "conn.execute(text('drop schema if exists \"public\" cascade'))",
        'conn.execute(text("DROP OWNED BY postgres"))',
        'conn.execute(text("DROP DATABASE studio_it"))',
        "gate_decisions.drop(engine)",
        "metadata.drop_all(engine)",
    ]
    for line in forbidden:
        assert FORBIDDEN.search(line), line


def test_the_guard_leaves_the_schemas_a_test_owns_alone() -> None:
    allowed = [
        "conn.execute(text(f'DROP SCHEMA \"{name}\" CASCADE'))",
        "conn.execute(text(f'DROP SCHEMA IF EXISTS \"{schema}\" CASCADE'))",
        "conn.execute(delete(step_claims))",
        "path.write_bytes(data[:4])  # a copy tool truncated the file",
    ]
    for line in allowed:
        assert not FORBIDDEN.search(line), line
