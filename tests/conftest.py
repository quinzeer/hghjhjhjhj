"""Shared fixtures."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

REQUIRE_MEDIA_ENV = "STUDIO_REQUIRE_MEDIA"
PG_URL_ENV = "STUDIO_TEST_PG_URL"
NOT_REQUIRED = frozenset({"", "0", "false", "no", "off"})


@pytest.fixture(scope="session")
def media_tools() -> None:
    """ffmpeg and ffprobe are on PATH. Without them the requesting test is skipped, unless STUDIO_REQUIRE_MEDIA
    is set (`make verify-phase-1` and the CI set it): a green run then always carries the media proofs."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    if os.environ.get(REQUIRE_MEDIA_ENV, "").strip().lower() not in NOT_REQUIRED:
        pytest.fail(f"ffmpeg/ffprobe are missing and {REQUIRE_MEDIA_ENV} is set")
    pytest.skip("ffmpeg/ffprobe are not on PATH")


def studio_table_names() -> list[str]:
    """Every table the studio's own modules declare."""
    from studio.core import artifacts, costs, decisions, queue

    metadata = (artifacts._metadata, costs._metadata, decisions._metadata, queue.metadata)
    return sorted({name for md in metadata for name in md.tables})


def default_schema_fingerprint(url: str) -> dict[str, str] | None:
    """A digest of the rows of each studio table found in the default schema of the database at `url`
    (None when the database cannot be reached)."""
    from studio.core.db import make_engine

    engine = make_engine(url)
    try:
        with engine.connect() as conn:
            listing = "select table_name from information_schema.tables where table_schema = current_schema()"
            present = {row[0] for row in conn.execute(text(listing))}
            rows = "select md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from \"{}\" t"
            return {name: str(conn.execute(text(rows.format(name))).scalar()) for name in studio_table_names() if name in present}
    except SQLAlchemyError:
        return None
    finally:
        engine.dispose()


def changed_tables(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


@pytest.fixture(scope="session", autouse=True)
def default_schema_untouched() -> Iterator[None]:
    """The suite runs against whatever database STUDIO_TEST_PG_URL names, and its tests work in schemas of their own
    (critic R7). This turns that rule into a check: the studio's tables in the default schema hold the same rows after
    the suite as before it. A write there is a test that left its schema, or another process using the same database."""
    url = os.environ.get(PG_URL_ENV, "")
    before = default_schema_fingerprint(url) if url else None
    yield
    if before is None:
        return
    after = default_schema_fingerprint(url)
    if after is None:
        return
    if changed := changed_tables(before, after):
        pytest.fail(
            f"the default schema of {PG_URL_ENV} changed during the suite ({', '.join(changed)}): "
            "a test wrote outside a schema of its own, or another process used the same database",
            pytrace=False,
        )
