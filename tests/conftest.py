"""Shared fixtures."""

from __future__ import annotations

import os
import shutil

import pytest

REQUIRE_MEDIA_ENV = "STUDIO_REQUIRE_MEDIA"
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
