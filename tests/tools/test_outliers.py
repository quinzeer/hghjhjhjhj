"""tools/outliers.py against a mock YouTube Data API (no network, no key)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("outliers", ROOT / "tools" / "outliers.py")
assert _spec and _spec.loader
ol = importlib.util.module_from_spec(_spec)
sys.modules["outliers"] = ol
_spec.loader.exec_module(ol)

NOW = dt.datetime(2026, 9, 28, tzinfo=dt.UTC)


class MockYouTubeApi:
    """Mock of the three endpoints used; records calls to check quota use."""

    def __init__(self, videos: list[dict]):
        self.videos = {v["id"]: v for v in videos}
        self.order = sorted(videos, key=lambda v: v["published"], reverse=True)
        self.calls: list[str] = []

    def __call__(self, endpoint: str, params: dict[str, str]) -> dict:
        self.calls.append(endpoint)
        if endpoint == "channels":
            return {"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}, "snippet": {"title": "Chan"}}]}
        if endpoint == "playlistItems":
            start = int(params.get("pageToken") or 0)
            page = self.order[start : start + 50]
            data = {"items": [{"contentDetails": {"videoId": v["id"], "videoPublishedAt": v["published"]}} for v in page]}
            if start + 50 < len(self.order):
                data["nextPageToken"] = str(start + 50)
            return data
        if endpoint == "videos":
            items = []
            for vid in params["id"].split(","):
                v = self.videos[vid]
                items.append(
                    {
                        "id": vid,
                        "snippet": {
                            "title": v["title"],
                            "channelId": "UC1",
                            "channelTitle": "Chan",
                            "publishedAt": v["published"],
                        },
                        "statistics": {"viewCount": str(v["views"])},
                        "contentDetails": {"duration": v["duration"]},
                    }
                )
            return {"items": items}
        raise AssertionError(endpoint)


def make_channel(n: int = 80, spike: int = 60) -> list[dict]:
    """n weekly long uploads at 10k views, one Short per week at 1M views, and one long spike."""
    vids = []
    for i in range(n):
        day = NOW - dt.timedelta(days=7 * (n - i))
        vid = f"L{i:010d}"
        vids.append(
            {
                "id": vid,
                "title": f"long {i}",
                "published": day.isoformat().replace("+00:00", "Z"),
                "views": 50_000 if i == spike else 10_000,
                "duration": "PT12M3S",
            }
        )
        vids.append(
            {
                "id": f"S{i:010d}",
                "title": f"short {i}",
                "published": (day + dt.timedelta(days=1)).isoformat().replace("+00:00", "Z"),
                "views": 1_000_000,
                "duration": "PT45S",
            }
        )
    return vids


def test_ratio_uses_previous_uploads_of_same_format() -> None:
    api = MockYouTubeApi(make_channel())
    [m] = ol.measure_videos(api, ["https://www.youtube.com/watch?v=L0000000060"], window=30, now=NOW)
    assert m.format == "long"
    assert m.baseline_n == 30
    assert m.baseline_median == 10_000  # Shorts at 1M views are excluded from the long baseline
    assert m.ratio == 5.0
    assert "search" not in api.calls  # search.list costs 100 units: never used


def test_scan_finds_only_the_spike() -> None:
    api = MockYouTubeApi(make_channel())
    found = ol.scan_channels(api, ["@chan"], months=18, min_ratio=3, window=30, now=NOW)
    assert [m.video_id for m in found] == ["L0000000060"]


def test_recent_video_gets_no_ratio() -> None:
    vids = make_channel(n=40, spike=39)
    vids[-2]["published"] = (NOW - dt.timedelta(days=2)).isoformat().replace("+00:00", "Z")  # the spike, 2 days old
    [m] = ol.measure_videos(MockYouTubeApi(vids), ["L0000000039"], window=30, now=NOW)
    assert m.ratio is None
    assert "moins de 7 j" in m.method


@pytest.mark.parametrize(("iso", "seconds"), [("PT45S", 45), ("PT12M3S", 723), ("PT1H0M1S", 3601), ("P1DT1S", 86401), ("", 0)])
def test_parse_duration(iso: str, seconds: int) -> None:
    assert ol.parse_duration(iso) == seconds


@pytest.mark.parametrize(
    "ref",
    ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://youtu.be/dQw4w9WgXcQ", "https://youtube.com/shorts/dQw4w9WgXcQ"],
)
def test_video_id(ref: str) -> None:
    assert ol.video_id(ref) == "dQw4w9WgXcQ"


def test_markdown_rows_satisfy_phase0_outlier_pattern() -> None:
    api = MockYouTubeApi(make_channel())
    md = ol.to_markdown(ol.measure_videos(api, ["L0000000060"], window=30, now=NOW), lang="en")
    assert "5,0×" in md
    spec = importlib.util.spec_from_file_location("vp", ROOT / "tools" / "verify_phase0.py")
    assert spec and spec.loader
    vp = importlib.util.module_from_spec(spec)
    sys.modules["vp"] = vp
    spec.loader.exec_module(vp)
    assert vp.OUTLIER_URL.search(md)


def test_missing_key_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert ol.main(["video", "dQw4w9WgXcQ"]) == 2
