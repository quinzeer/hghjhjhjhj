#!/usr/bin/env python3
"""Measure YouTube outliers through the official YouTube Data API v3 (no scraping).

Outlier ratio = views of a video ÷ median views of the `window` uploads of the same channel and
format that are closest to it in publication date, before and after (MISSION §7: "à âge
comparable"). Using only older uploads would inflate the ratio on a growing channel (older videos
were published to a smaller audience). Uploads younger than MIN_AGE_DAYS are left out of the
baseline, and a target that young gets no ratio. Format: Short = ≤ 180 s and a vertical player
(`player.embedHeight > embedWidth`); duration alone is used when the API gives no player size.

Quota cost (default 10 000 units/day): 1 unit per API call; a channel scan of 18 months
costs a few units per 50 uploads. `search.list` (100 units) is never used.

Usage:
    YOUTUBE_API_KEY=... python3 tools/outliers.py video <url-or-id> [...]
    YOUTUBE_API_KEY=... python3 tools/outliers.py channel @handle [...] --months 18 --min-ratio 3
Output: markdown rows ready for docs/research/channel-concepts.md (or --json).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass

API = "https://www.googleapis.com/youtube/v3/"
SHORT_MAX_SECONDS = 180
MIN_AGE_DAYS = 7  # views of younger videos are not settled yet
Fetch = Callable[[str, dict[str, str]], dict]


@dataclass
class Video:
    id: str
    title: str
    channel_id: str
    channel_title: str
    published: dt.datetime
    views: int
    seconds: int
    vertical: bool | None = None

    @property
    def is_short(self) -> bool:
        return self.seconds <= SHORT_MAX_SECONDS and self.vertical is not False


@dataclass
class Measure:
    video_id: str
    url: str
    title: str
    channel: str
    published: str
    views: int
    format: str
    baseline_median: float | None
    baseline_n: int
    ratio: float | None
    method: str


def http_fetch(api_key: str) -> Fetch:
    def fetch(endpoint: str, params: dict[str, str]) -> dict:
        query = urllib.parse.urlencode({**params, "key": api_key})
        with urllib.request.urlopen(f"{API}{endpoint}?{query}", timeout=30) as resp:
            return json.load(resp)

    return fetch


def parse_duration(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def video_id(value: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", value)
    if m:
        return m.group(1)
    if re.fullmatch(r"[\w-]{11}", value):
        return value
    raise ValueError(f"identifiant de vidéo illisible : {value}")


def chunks(items: list[str], size: int = 50) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def get_videos(fetch: Fetch, ids: list[str]) -> list[Video]:
    out: list[Video] = []
    for batch in chunks(ids):
        params = {"part": "snippet,statistics,contentDetails,player", "id": ",".join(batch), "maxWidth": "1000"}
        data = fetch("videos", params)
        for item in data.get("items", []):
            sn, st = item.get("snippet", {}), item.get("statistics", {})
            if "viewCount" not in st or "publishedAt" not in sn:  # hidden counts, private or deleted: unusable
                continue
            player = item.get("player", {})
            h, w = player.get("embedHeight"), player.get("embedWidth")
            out.append(
                Video(
                    id=item["id"],
                    title=sn["title"],
                    channel_id=sn["channelId"],
                    channel_title=sn["channelTitle"],
                    published=parse_time(sn["publishedAt"]),
                    views=int(st["viewCount"]),
                    seconds=parse_duration(item.get("contentDetails", {}).get("duration", "")),
                    vertical=(int(h) > int(w)) if h and w else None,
                )
            )
    return out


def channel_uploads_playlist(fetch: Fetch, channel: str) -> tuple[str, str]:
    """(uploads playlist id, channel title) from a channel id (UC…) or a @handle."""
    params = {"part": "contentDetails,snippet"}
    if channel.startswith("@"):
        params["forHandle"] = channel
    else:
        params["id"] = channel
    items = fetch("channels", params).get("items", [])
    if not items:
        raise LookupError(f"chaîne introuvable : {channel}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"], items[0]["snippet"]["title"]


def upload_ids(fetch: Fetch, playlist: str, since: dt.datetime, max_pages: int = 40) -> list[str]:
    """Upload ids from newest back to `since` (inclusive), newest first."""
    ids: list[str] = []
    token = ""
    for _ in range(max_pages):
        params = {"part": "contentDetails", "playlistId": playlist, "maxResults": "50"}
        if token:
            params["pageToken"] = token
        data = fetch("playlistItems", params)
        stop = False
        for item in data.get("items", []):
            cd = item.get("contentDetails", {})
            if "videoPublishedAt" not in cd:  # private or deleted upload
                continue
            if parse_time(cd["videoPublishedAt"]) < since:
                stop = True
                break
            ids.append(cd["videoId"])
        token = data.get("nextPageToken", "")
        if stop or not token:
            break
    return ids


def measure(target: Video, history: list[Video], window: int, now: dt.datetime) -> Measure:
    """Compare target with the `window` same-format uploads closest to it in publication date."""
    settled = [
        v for v in history if v.id != target.id and v.is_short == target.is_short and (now - v.published).days >= MIN_AGE_DAYS
    ]
    same = sorted(settled, key=lambda v: abs((v.published - target.published).total_seconds()))[:window]
    fmt = "short" if target.is_short else "long"
    old_enough = (now - target.published).days >= MIN_AGE_DAYS
    median = statistics.median(v.views for v in same) if same else None
    ratio = round(target.views / median, 2) if median and old_enough else None
    method = f"API YouTube Data v3 ; médiane des {len(same)} {fmt}s de la chaîne les plus proches en date"
    if not old_enough:
        method += f" ; vidéo de moins de {MIN_AGE_DAYS} j : ratio non calculé"
    return Measure(
        video_id=target.id,
        url=f"https://www.youtube.com/watch?v={target.id}",
        title=target.title,
        channel=target.channel_title,
        published=target.published.date().isoformat(),
        views=target.views,
        format=fmt,
        baseline_median=median,
        baseline_n=len(same),
        ratio=ratio,
        method=method,
    )


def history_for(fetch: Fetch, channel_id: str, since: dt.datetime) -> tuple[list[Video], str]:
    playlist, title = channel_uploads_playlist(fetch, channel_id)
    return get_videos(fetch, upload_ids(fetch, playlist, since)), title


def measure_videos(fetch: Fetch, refs: list[str], window: int, now: dt.datetime) -> list[Measure]:
    targets = get_videos(fetch, [video_id(r) for r in refs])
    out = []
    for t in targets:
        # uploads before and after the target: go back up to 3 years before it (cap)
        history, _ = history_for(fetch, t.channel_id, t.published - dt.timedelta(days=3 * 365))
        out.append(measure(t, history, window, now))
    return out


def scan_channels(
    fetch: Fetch, channels: list[str], months: int, min_ratio: float, window: int, now: dt.datetime
) -> list[Measure]:
    out = []
    since = now - dt.timedelta(days=int(months * 30.44))
    for ch in channels:
        history, _ = history_for(fetch, ch, since - dt.timedelta(days=3 * 365))
        for v in history:
            if v.published >= since:
                m = measure(v, history, window, now)
                if m.ratio is not None and m.ratio >= min_ratio and m.baseline_n >= 10:
                    out.append(m)
    return sorted(out, key=lambda m: m.ratio or 0, reverse=True)


def to_markdown(rows: list[Measure], lang: str = "?") -> str:
    lines = [
        "| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        median = f"{m.baseline_median:,.0f}".replace(",", " ") if m.baseline_median is not None else "n/d"
        ratio = f"{m.ratio:.1f}×".replace(".", ",") if m.ratio is not None else "non calculé"
        title = m.title.replace("|", "/")
        views = f"{m.views:,}".replace(",", " ")
        lines.append(f"| {title} | {m.channel} | {lang} | {m.published} | {views} | {median} ({m.method}) | {ratio} | {m.url} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("video", help="mesurer des vidéos précises")
    pv.add_argument("refs", nargs="+")
    pc = sub.add_parser("channel", help="lister les outliers récents de chaînes (@handle ou UC…)")
    pc.add_argument("channels", nargs="+")
    pc.add_argument("--months", type=int, default=18)
    pc.add_argument("--min-ratio", type=float, default=3.0)
    for p in (pv, pc):
        p.add_argument("--window", type=int, default=30)
        p.add_argument("--lang", default="?")
        p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("YOUTUBE_API_KEY absente : voir docs/NEEDS_HUMAN.md (H0).", file=sys.stderr)
        return 2
    fetch = http_fetch(key)
    now = dt.datetime.now(dt.UTC)
    if args.cmd == "video":
        rows = measure_videos(fetch, args.refs, args.window, now)
    else:
        rows = scan_channels(fetch, args.channels, args.months, args.min_ratio, args.window, now)
    print(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2) if args.json else to_markdown(rows, args.lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
