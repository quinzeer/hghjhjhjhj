#!/usr/bin/env python3
"""Phase 0 gate: checks every exit criterion of MISSION §9 phase 0.

Exit code 0 only if all checks pass. Standard library only (Python >= 3.11),
so it runs on a fresh clone before any dependency is installed.

Usage:
    python3 tools/verify_phase0.py                 # full gate
    python3 tools/verify_phase0.py --note PATH     # one research note
    python3 tools/verify_phase0.py --json          # machine-readable report
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_NOTES = (
    "platform-policies.md",
    "apis.md",
    "video-image-models.md",
    "audio-models.md",
    "craft.md",
    "economics.md",
)
# Notes whose claims are about platform rules or APIs need official sources.
OFFICIAL_REQUIRED = {"platform-policies.md": 3, "apis.md": 3}
MIN_DATED_SOURCES = 8
NOTE_SECTIONS = ("synthese", "constats", "ecarts avec mission", "questions ouvertes", "sources")
SOURCE_COLUMNS = ("id", "titre", "url", "date source", "consulte", "type", "confiance")
SOURCE_TYPES = {"officiel", "publication", "presse", "praticien", "donnees"}
CONFIDENCE = {"elevee", "moyenne", "faible"}
UNDATED = {"s.d.", "sd", "n.d.", "nd"}

MIN_CONCEPTS = 6
MIN_OUTLIERS_PER_CONCEPT = 2
# An outlier counts only if its table row shows a measured ratio >= 3x (MISSION §2) and a
# publication date within RECENT_DAYS ("récents", MISSION §9 phase 0; 18 months, see CLAUDE.md).
MIN_OUTLIER_RATIO = 3.0
RECENT_DAYS = 548
CONCEPT_FIELDS = {
    "rpm": ("rpm",),
    "legitimite": ("legitimite",),
    "risque": ("risque",),
    "serialite": ("serialite", "series"),
    "cout": ("cout",),
}
OUTLIER_URL = re.compile(
    r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/|tiktok\.com/@[^/\s|]+/video/)[^\s|)]+"
)

# "officiel" is for platform, regulator, vendor or licence texts: never forums, wikis or placeholders.
NOT_OFFICIAL_URL = re.compile(
    r"example\.|/discussions?/|/issues/|/pull/|wikipedia\.org|fandom\.com|reddit\.com|medium\.com|substack\.com"
)
# A source that was never opened cannot be cited; one read only through a search summary cannot be "élevée".
NOTE_MIN_CONSTATS = 3
NOTE_MIN_WORDS = {"synthese": 40, "ecarts avec mission": 15, "questions ouvertes": 5}
ADR_MIN_DISTINCT_WORDS = 25
MIN_BASELINE = 10  # an outlier ratio needs at least this many comparison videos
OUTLIER_DIR = Path("docs/research/outliers")
NOT_OPENED = re.compile(
    r"(?:HTTP|code|erreur)\s*404|404\s*(?:not found|introuvable)|non ouvert|not opened|jamais ouvert|pas pu [êe]tre ouvert",
    re.IGNORECASE,
)
WEAKLY_READ = re.compile(r"\b403\b|bloqu|inaccessible|via (?:un )?r[ée]sum|vue? (?:en|via|dans un) r[ée]sultat", re.IGNORECASE)
OUTLIER_METHOD = "API YouTube Data v3"  # rows produced by tools/outliers.py
RATIO_TOLERANCE = 0.05

ADR_REQUIRED = ("ADR-001", "ADR-002")
ADR_SECTIONS = (
    "statut",
    "contexte",
    "options",
    "decision",
    "consequences",
    "cout d'un retour arriere",
    "sources",
)
ADR_MIN_WORDS = {"contexte": 40, "options": 40, "decision": 40}
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|à compléter|a completer", re.IGNORECASE)

SUBAGENTS = {
    "architect": "opus",
    "researcher": "sonnet",
    "pipeline-engineer": "inherit",
    "media-engineer": "inherit",
    "ml-engineer": "inherit",
    "eval-engineer": "inherit",
    "compliance-reviewer": "opus",
    "security-reviewer": "sonnet",
    "critic": "opus",
}
CLAUDE_MD_MAX_LINES = 150
SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    # [ \t]* (not \s*) so an empty value followed by a newline is not read as a secret
    re.compile(r"(?m)^[ \t]*(?:export[ \t]+)?ANTHROPIC_API_KEY[ \t]*=[ \t]*[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?m)^[ \t]*(?:export[ \t]+)?CLAUDE_CODE_OAUTH_TOKEN[ \t]*=[ \t]*[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?m)^[ \t]*(?:export[ \t]+)?YOUTUBE_API_KEY[ \t]*=[ \t]*[A-Za-z0-9_\-]{12,}"),
)


# Placeholder tokens that tests feed to the redaction code of the Claude runner. They have the shape of a key on purpose
# (the code under test must recognise the shape) and are listed one by one: a real key never equals one of them, and a
# lookalike that is not in this set, or that continues past its end, still fails the gate. The tests now build them at run
# time, so no file of the tree holds them; the set stays because the history of the branch does and cannot be rewritten.
KNOWN_FAKE_SECRETS = frozenset({"sk-ant-api03-FAKEfake0123456789", "sk-ant-api03-not-a-real-key"})
_TOKEN_CHARS = r"A-Za-z0-9_\-"
_KNOWN_FAKES = re.compile(
    rf"(?<![{_TOKEN_CHARS}])(?:{'|'.join(re.escape(f) for f in sorted(KNOWN_FAKE_SECRETS))})(?![{_TOKEN_CHARS}])"
)


def without_known_fakes(text: str) -> str:
    """`text` with each listed placeholder token (as a whole token) removed."""
    return _KNOWN_FAKES.sub("", text)


def norm(text: str) -> str:
    """Lowercase, strip accents and surrounding spaces/markup for tolerant matching."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("’", "'")
    return re.sub(r"\s+", " ", text.strip().strip("*`_").lower())


@dataclass
class Check:
    id: str
    label: str
    ok: bool = True
    details: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.details.append(msg)

    def info(self, msg: str) -> None:
        self.details.append(msg)


# ---------------------------------------------------------------- markdown


def headings(text: str, level: int) -> list[tuple[int, str]]:
    """(line index, normalized title) for headings of exactly `level`."""
    out = []
    prefix = "#" * level + " "
    for i, line in enumerate(text.splitlines()):
        if line.startswith(prefix) and not line.startswith(prefix + "#"):
            out.append((i, norm(line[len(prefix) :])))
    return out


def section(text: str, title_prefix: str, level: int = 2) -> str | None:
    """Body of the first heading at `level` whose normalized title starts with title_prefix."""
    lines = text.splitlines()
    heads = headings(text, level)
    for i, title in heads:
        if title.startswith(title_prefix):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                m = re.match(r"^(#+) ", lines[j])
                if m and len(m.group(1)) <= level:
                    end = j
                    break
            return "\n".join(lines[i + 1 : end])
    return None


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def tables(body: str) -> list[list[list[str]]]:
    """All pipe tables in body; each table = header row + data rows (separator dropped)."""
    result: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in body.splitlines():
        if line.strip().startswith("|"):
            row = split_row(line)
            if all(re.fullmatch(r":?-{3,}:?", c) for c in row if c):
                continue
            current.append(row)
        elif current:
            result.append(current)
            current = []
    if current:
        result.append(current)
    return result


# ---------------------------------------------------------------- dates


def parse_date(value: str) -> tuple[str, dt.date] | None:
    """('day'|'month'|'year', earliest date) or None."""
    value = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return "day", dt.date.fromisoformat(value)
        if re.fullmatch(r"\d{4}-\d{2}", value):
            y, m = map(int, value.split("-"))
            return "month", dt.date(y, m, 1)
        if re.fullmatch(r"\d{4}", value):
            return "year", dt.date(int(value), 1, 1)
    except ValueError:
        return None
    return None


def in_future(parsed: tuple[str, dt.date], today: dt.date) -> bool:
    precision, d = parsed
    if precision == "day":
        return d > today
    if precision == "month":
        return (d.year, d.month) > (today.year, today.month)
    return d.year > today.year


# ---------------------------------------------------------------- notes


def cited_ids(text: str, tables_only: bool = False) -> set[str]:
    """IDs cited as [S1], [S1, S3] or [S1][S2] in the body (before '## Sources').

    tables_only: count only citations inside table rows, where a source backs one precise claim
    (a list of 8 sources in one sentence proves nothing)."""
    before = text.split("\n## Sources", 1)[0] if "\n## Sources" in text else text
    if tables_only:
        before = "\n".join(line for line in before.splitlines() if line.strip().startswith("|"))
    cited: set[str] = set()
    for group in re.findall(r"\[([^\]]+)\]", before):
        if re.fullmatch(r"\s*S\d+(\s*[,;]\s*S\d+)*\s*", group):
            cited.update(re.findall(r"S\d+", group))
    return cited


def source_rows(text: str) -> list[list[str]] | None:
    body = section(text, "sources")
    if body is None:
        return None
    tbls = [t for t in tables(body) if t and [norm(c) for c in t[0]][: len(SOURCE_COLUMNS)] == list(SOURCE_COLUMNS)]
    return tbls[0][1:] if tbls else None


def check_sources(text: str, name: str, today: dt.date, chk: Check, min_official: int = 0) -> None:
    rows = source_rows(text)
    if rows is None:
        chk.fail(f"{name}: section '## Sources' ou table des sources absente (colonnes : {', '.join(SOURCE_COLUMNS)})")
        return
    cited = cited_ids(text)
    backing = cited_ids(text, tables_only=True)
    ids: set[str] = set()
    urls: set[str] = set()
    dated = official = 0
    for r, row in enumerate(rows, start=1):
        if len(row) < len(SOURCE_COLUMNS):
            chk.fail(f"{name}: ligne source {r} incomplète ({len(row)} colonnes)")
            continue
        sid, title, url, date_src, consulted, typ, conf = row[:7]
        where = f"{name}: {sid or f'ligne {r}'}"
        if not re.fullmatch(r"S\d+", sid):
            chk.fail(f"{where}: ID invalide (attendu S1, S2…)")
        elif sid in ids:
            chk.fail(f"{where}: ID dupliqué")
        ids.add(sid)
        url = url.strip("<>")
        if not re.fullmatch(r"https?://\S+", url):
            chk.fail(f"{where}: URL invalide '{url}'")
        elif "example.com" in url:
            chk.fail(f"{where}: URL d'exemple du gabarit")
        elif url in urls:
            chk.info(f"{where}: URL déjà citée (toléré)")
        urls.add(url)
        row_text = " ".join(row)
        if NOT_OPENED.search(row_text):
            chk.fail(f"{where}: source déclarée non ouverte : à ouvrir ou à retirer")
        if WEAKLY_READ.search(row_text) and norm(conf) == "elevee":
            chk.fail(f"{where}: source lue indirectement ou bloquée : confiance « élevée » impossible")
        parsed_c = parse_date(consulted)
        if parsed_c is None or parsed_c[0] != "day":
            chk.fail(f"{where}: date de consultation illisible '{consulted}' (AAAA-MM-JJ)")
            parsed_c = None
        elif in_future(parsed_c, today):
            chk.fail(f"{where}: consultation dans le futur '{consulted}'")
        is_dated = False
        if norm(date_src) not in UNDATED:
            parsed = parse_date(date_src)
            if parsed is None:
                chk.fail(f"{where}: date source illisible '{date_src}'")
            elif in_future(parsed, today) or (parsed_c and parsed[1] > parsed_c[1]):
                chk.fail(f"{where}: date source postérieure à la consultation ou dans le futur '{date_src}'")
            else:
                is_dated = True
        if norm(typ) not in SOURCE_TYPES:
            chk.fail(f"{where}: type '{typ}' hors liste {sorted(SOURCE_TYPES)}")
        elif norm(typ) == "officiel" and NOT_OFFICIAL_URL.search(url):
            chk.fail(f"{where}: typé « officiel » mais l'URL est un forum, un wiki ou un exemple")
        if norm(conf) not in CONFIDENCE:
            chk.fail(f"{where}: confiance '{conf}' hors liste")
        if sid in backing:  # only sources that back a claim in a table row count toward the thresholds
            dated += is_dated
            official += norm(typ) == "officiel"
    if dated < MIN_DATED_SOURCES:
        chk.fail(f"{name}: {dated} sources datées et citées dans un tableau < {MIN_DATED_SOURCES}")
    if official < min_official:
        chk.fail(f"{name}: {official} sources officielles citées < {min_official}")
    uncited = sorted(ids - cited, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    chk.info(f"{name}: {len(rows)} sources, {dated} datées et citées dans un tableau, {official} officielles citées")
    if uncited:
        chk.info(f"{name}: sources jamais citées (non comptées) : {', '.join(uncited)}")
    missing = sorted(cited - ids, key=lambda x: int(x[1:]))
    if missing:
        chk.fail(f"{name}: références citées sans source : {', '.join(missing)}")
    if not cited:
        chk.fail(f"{name}: aucune référence [Sn] dans le corps de la note")


def check_constats(text: str, name: str, chk: Check) -> None:
    """Every row of the '## Constats' table cites a source, or is labelled an inference or an absence of evidence."""
    body = section(text, "constats")
    if body is None:
        return
    tbls = tables(body)
    if not tbls or len(tbls[0]) - 1 < NOTE_MIN_CONSTATS:
        chk.fail(f"{name}: la section Constats doit contenir un tableau d'au moins {NOTE_MIN_CONSTATS} constats")
    for tbl in tbls[:1]:
        for row in tbl[1:]:
            joined = " ".join(row)
            confidence = norm(row[3]) if len(row) > 3 else ""
            if NOT_OPENED.search(joined) and "elevee" in confidence:
                chk.fail(f"{name}: constat appuyé sur une source non ouverte mais noté « élevée » : « {joined[:60]} »")
            labelled = any(k in norm(joined) for k in ("inference", "non trouve", "non verifi", "absence"))
            if not re.search(r"\[\s*S\d+", joined) and not labelled:
                chk.fail(
                    f"{name}: constat sans source ni mention « inférence » : « {row[1][:60] if len(row) > 1 else joined[:60]} »"
                )


def check_note(path: Path, today: dt.date, min_official: int | None = None) -> Check:
    name = path.name
    chk = Check(f"note:{name}", f"Note de recherche {name}")
    if not path.is_file():
        chk.fail(f"{path} absent")
        return chk
    text = path.read_text(encoding="utf-8")
    titles = [t for _, t in headings(text, 2)]
    for sec in NOTE_SECTIONS:
        if not any(t.startswith(sec) for t in titles):
            chk.fail(f"{name}: section '## {sec}' absente")
    if PLACEHOLDER.search(text):
        chk.fail(f"{name}: marqueur de travail inachevé (TODO/TBD/…) présent")
    for sec, minimum in NOTE_MIN_WORDS.items():
        body = section(text, sec)
        if body is not None and len(re.findall(r"\w+", body)) < minimum:
            chk.fail(f"{name}: section '{sec}' trop courte (< {minimum} mots)")
    if min_official is None:
        min_official = OFFICIAL_REQUIRED.get(name, 0)
    check_constats(text, name, chk)
    check_sources(text, name, today, chk, min_official)
    return chk


def concepts_required(root: Path) -> bool:
    """channel-concepts.md is required unless both concepts are confirmed by the human."""
    params = root / "docs" / "PARAMETERS.md"
    if not params.is_file():
        return True
    confirmed = 0
    for tbl in tables(params.read_text(encoding="utf-8")):
        header = [norm(c) for c in tbl[0]]
        if "parametre" not in header or "statut" not in header:
            continue
        p, s = header.index("parametre"), header.index("statut")
        for row in tbl[1:]:
            if len(row) > max(p, s) and norm(row[p]).startswith("concept chaine") and norm(row[s]).startswith("confirme"):
                confirmed += 1
    return confirmed < 2


def load_outlier_records(root: Path) -> dict[str, dict]:
    """Raw measurements written by `tools/outliers.py --save`, by video id."""
    records: dict[str, dict] = {}
    folder = root / OUTLIER_DIR
    for f in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            for rec in json.loads(f.read_text(encoding="utf-8")):
                if isinstance(rec, dict) and rec.get("video_id"):
                    records[rec["video_id"]] = rec
        except (json.JSONDecodeError, OSError):
            continue
    return records


def record_ratio(rec: dict) -> float | None:
    """Ratio recomputed from the raw baseline, or None when the record cannot support one."""
    views = rec.get("baseline_views") or []
    if len(views) < MIN_BASELINE or OUTLIER_METHOD not in rec.get("method", ""):
        return None
    median = statistics.median(views)
    return rec["views"] / median if median > 0 else None


def measured_outliers(body: str, today: dt.date, records: dict[str, dict] | None = None) -> tuple[set[str], list[str]]:
    """Outlier URLs whose row matches a raw measurement: recomputed ratio >= 3x, recent, same numbers."""
    records = records or {}
    ok: set[str] = set()
    rejected: list[str] = []
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        urls = OUTLIER_URL.findall(line)
        if not urls:
            continue
        cells = split_row(line)
        vid = re.search(r"(?:v=|youtu\.be/|shorts/|video/)([\w-]+)", urls[0])
        vid = vid.group(1) if vid else urls[0][-11:]
        # columns: Vidéo | Chaîne | Langue | Publiée | Vues | Médiane (méthode) | Ratio | URL
        numbers = [
            int(re.sub(r"[\s\u202f\u00a0]", "", m.group(0)))
            for c in cells[4:6]
            if (m := re.match(r"\d{1,3}(?:[\s\u202f\u00a0]\d{3})+|\d+", c.strip()))
        ]
        rec = records.get(vid)
        ratio = record_ratio(rec) if rec else None
        published = parse_date(rec.get("published", "")) if rec else None
        if rec is None:
            rejected.append(f"{vid} absent des mesures brutes ({OUTLIER_DIR}/*.json, tools/outliers.py --save)")
        elif ratio is None:
            rejected.append(f"{vid} mesure brute inexploitable (méthode ou base < {MIN_BASELINE} vidéos)")
        elif ratio < MIN_OUTLIER_RATIO:
            rejected.append(f"{vid} ratio recalculé {ratio:.2f} < {MIN_OUTLIER_RATIO:g}")
        elif published is None or (today - published[1]).days > RECENT_DAYS:
            rejected.append(f"{vid} non récent ou non daté")
        elif len(numbers) < 2 or numbers[0] != rec["views"] or abs(numbers[1] - statistics.median(rec["baseline_views"])) > 1:
            rejected.append(f"{vid} vues ou médiane du tableau différentes de la mesure brute")
        else:
            ok.add(urls[0])
    return ok, rejected


def online_recheck(root: Path, records: dict[str, dict], counted_ids: set[str]) -> list[str]:
    """Re-measure counted outliers through the API (views drift: ±25 % tolerated). Returns problems."""
    if not os.environ.get("YOUTUBE_API_KEY"):
        return ["--online exige YOUTUBE_API_KEY"]
    spec = importlib.util.spec_from_file_location("outliers", root / "tools" / "outliers.py")
    if spec is None or spec.loader is None:
        return ["tools/outliers.py introuvable"]
    ol = importlib.util.module_from_spec(spec)
    sys.modules["outliers"] = ol
    spec.loader.exec_module(ol)
    fetch = ol.http_fetch(os.environ["YOUTUBE_API_KEY"])
    now = dt.datetime.now(dt.UTC)
    problems = []
    for m in ol.measure_videos(fetch, sorted(counted_ids), 30, now):
        before = record_ratio(records[m.video_id]) or 0
        if m.ratio is None or m.ratio < MIN_OUTLIER_RATIO or abs(m.ratio - before) > 0.25 * before:
            problems.append(f"{m.video_id} : ratio enregistré {before:.2f}, re-mesuré {m.ratio}")
    missing = counted_ids - {m.video_id for m in ol.measure_videos(fetch, sorted(counted_ids), 30, now)}
    problems += [f"{v} : introuvable par l'API" for v in sorted(missing)]
    return problems


def check_concepts(path: Path, today: dt.date, root: Path | None = None, online: bool = False) -> Check:
    chk = check_note(path, today)
    root = root or path.resolve().parents[2]
    records = load_outlier_records(root)
    counted_ids: set[str] = set()
    chk.id, chk.label = "concepts", "Concepts de chaînes (6 classés, ≥ 2 outliers chacun)"
    if not path.is_file():
        return chk
    text = path.read_text(encoding="utf-8")
    heads = [(i, t) for i, t in headings(text, 3) if re.match(r"c\d+\b", t)]
    if len(heads) < MIN_CONCEPTS:
        chk.fail(f"{len(heads)} sections concept '### Cn — …' < {MIN_CONCEPTS}")
    lines = text.splitlines()
    for n, (i, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        for j in range(i + 1, end):
            if re.match(r"^#{1,3} ", lines[j]):
                end = j
                break
        body = "\n".join(lines[i + 1 : end])
        outliers, rejected = measured_outliers(body, today, records)
        counted_ids |= {u.rsplit("=", 1)[-1].rsplit("/", 1)[-1] for u in outliers}
        if len(outliers) < MIN_OUTLIERS_PER_CONCEPT:
            why = f" ; lignes écartées : {'; '.join(rejected[:3])}" if rejected else ""
            chk.fail(
                f"{title[:40]} : {len(outliers)} outlier(s) mesuré(s) (ratio ≥ {MIN_OUTLIER_RATIO:g}×, "
                f"publié depuis ≤ {RECENT_DAYS} j) < {MIN_OUTLIERS_PER_CONCEPT}{why}"
            )
        nb = norm(body)
        for fld, keys in CONCEPT_FIELDS.items():
            if not any(k in nb for k in keys):
                chk.fail(f"{title[:40]} : champ '{fld}' absent")
    if section(text, "classement") is None:
        chk.fail("section '## Classement' absente")
    if online:
        for problem in online_recheck(root, records, counted_ids):
            chk.fail(f"re-mesure API : {problem}")
    elif counted_ids:
        chk.info("outliers vérifiés contre les mesures brutes ; lancer --online (clé API) avant de clore la phase")
    return chk


# ---------------------------------------------------------------- other gates


def check_state_files(root: Path) -> Check:
    chk = Check("state", "Fichiers d'état (MISSION, CLAUDE, PLAN, PROGRESS, DECISIONS, NEEDS_HUMAN)")
    for rel in ("docs/MISSION.md", "CLAUDE.md", "docs/PLAN.md", "docs/PROGRESS.md", "docs/DECISIONS.md", "docs/NEEDS_HUMAN.md"):
        if not (root / rel).is_file():
            chk.fail(f"{rel} absent")
    claude_md = root / "CLAUDE.md"
    if claude_md.is_file():
        n = len(claude_md.read_text(encoding="utf-8").splitlines())
        if n > CLAUDE_MD_MAX_LINES:
            chk.fail(f"CLAUDE.md : {n} lignes > {CLAUDE_MD_MAX_LINES}")
        else:
            chk.info(f"CLAUDE.md : {n} lignes")
    return chk


def frontmatter(text: str) -> dict[str, str] | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if kv:
            out[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return out


def check_subagents(root: Path) -> Check:
    chk = Check("subagents", "Sous-agents de construction (MISSION §10)")
    for name, model in SUBAGENTS.items():
        path = root / ".claude" / "agents" / f"{name}.md"
        if not path.is_file():
            chk.fail(f"{path.relative_to(root)} absent")
            continue
        fm = frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            chk.fail(f"{name}: frontmatter YAML absent")
            continue
        if fm.get("name") != name:
            chk.fail(f"{name}: champ name = '{fm.get('name')}'")
        if not fm.get("description"):
            chk.fail(f"{name}: description vide")
        if fm.get("model") != model:
            chk.fail(f"{name}: model = '{fm.get('model')}', attendu '{model}'")
    return chk


def check_decisions(root: Path) -> Check:
    chk = Check("adr", "ADR-001 et ADR-002 complets, sourcés, sans TODO")
    path = root / "docs" / "DECISIONS.md"
    if not path.is_file():
        chk.fail("docs/DECISIONS.md absent")
        return chk
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    adr_heads = [(i, line) for i, line in enumerate(lines) if re.match(r"^## ADR-\d{3}\b", line)]
    for adr in ADR_REQUIRED:
        found = [k for k, (_, line) in enumerate(adr_heads) if line.startswith(f"## {adr}")]
        if not found:
            chk.fail(f"{adr} absent (titre attendu '## {adr} — …')")
            continue
        k = found[0]
        start = adr_heads[k][0]
        end = adr_heads[k + 1][0] if k + 1 < len(adr_heads) else len(lines)
        body = "\n".join(lines[start:end])
        subsections = {}
        for m in re.finditer(r"^### (.+)\n((?:(?!^### |^## ).*\n?)*)", body + "\n", re.M):
            subsections[norm(m.group(1))] = m.group(2)
        for sec in ADR_SECTIONS:
            content = next((v for k2, v in subsections.items() if k2.startswith(sec)), None)
            if content is None:
                chk.fail(f"{adr}: sous-section '### {sec}' absente")
                continue
            tokens = re.findall(r"\w+", content.lower())
            words = len(tokens)
            if words == 0:
                chk.fail(f"{adr}: sous-section '{sec}' vide")
            elif words < ADR_MIN_WORDS.get(sec, 1):
                chk.fail(f"{adr}: sous-section '{sec}' trop courte ({words} mots < {ADR_MIN_WORDS[sec]})")
            elif sec in ADR_MIN_WORDS and len(set(tokens)) < ADR_MIN_DISTINCT_WORDS:
                chk.fail(f"{adr}: sous-section '{sec}' répétitive ({len(set(tokens))} mots distincts)")
            if sec == "sources" and not re.search(r"[\w-]+\.md`?\s*\[S\d+", content):
                chk.fail(f"{adr}: '### Sources' sans renvoi `note.md [Sn]` vers une note de recherche")
        if PLACEHOLDER.search(body):
            chk.fail(f"{adr}: contient TODO/TBD/FIXME/XXX/« à compléter »")
        check_cross_refs(root, body, adr, chk)
    return chk


def check_cross_refs(root: Path, text: str, where: str, chk: Check) -> None:
    """Every `note.md [Sn] [Sm]` reference points to an existing source of that note."""
    for m in re.finditer(r"`?([\w-]+\.md)`?((?:\s*\[S\d+(?:\s*[,;]\s*S\d+)*\])+)", text):
        note = root / "docs" / "research" / m.group(1)
        refs = set(re.findall(r"S\d+", m.group(2)))
        if not note.is_file():
            chk.fail(f"{where}: renvoie à {m.group(1)} qui n'existe pas dans docs/research/")
            continue
        rows = source_rows(note.read_text(encoding="utf-8")) or []
        known = {row[0] for row in rows if row}
        missing = sorted(refs - known)
        if missing:
            chk.fail(f"{where}: {m.group(1)} {', '.join(missing)} introuvable(s)")


def check_cost_model(root: Path) -> Check:
    chk = Check("cost", "docs/COST_MODEL.md (coût par format, hypothèses explicites)")
    path = root / "docs" / "COST_MODEL.md"
    if not path.is_file():
        chk.fail("docs/COST_MODEL.md absent")
        return chk
    text = path.read_text(encoding="utf-8")
    titles = [t for _, t in headings(text, 2)]
    for want in ("hypotheses", "long", "short"):
        if not any(want in t for t in titles):
            chk.fail(f"section '## …{want}…' absente")
    if not tables(text):
        chk.fail("aucune table chiffrée")
    if PLACEHOLDER.search(text):
        chk.fail("contient TODO/TBD/FIXME/XXX")
    if "economics.md" not in text:
        chk.fail("ne renvoie pas aux paramètres sourcés de docs/research/economics.md")
    generated = section(text, "tables generees")
    gen_path = root / "tools" / "cost_model.py"
    if generated is None:
        chk.fail("section '## Tables générées' absente")
    elif gen_path.is_file():
        try:
            out = subprocess.run([sys.executable, str(gen_path)], capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            chk.fail(f"tools/cost_model.py ne s'exécute pas : {exc}")
        else:
            if generated.strip() != out.strip():
                chk.fail("les tables diffèrent de la sortie de tools/cost_model.py : régénérer")
    check_cross_refs(root, text, "COST_MODEL", chk)
    return chk


def check_plan(root: Path) -> Check:
    chk = Check("plan", "docs/PLAN.md détaillé (phases 0-7, tâches cochables)")
    path = root / "docs" / "PLAN.md"
    if not path.is_file():
        chk.fail("docs/PLAN.md absent")
        return chk
    text = path.read_text(encoding="utf-8")
    for n in range(8):
        body = section(text, f"phase {n}")
        if body is None:
            chk.fail(f"section '## Phase {n} …' absente")
        elif not re.search(r"^\s*- \[[ xX]\] ", body, re.M):
            chk.fail(f"Phase {n} : aucune tâche cochable")
    return chk


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout.decode()
        return [root / p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def check_secrets(root: Path) -> Check:
    chk = Check("secrets", "Aucun secret ni fichier .env versionné (MISSION §3.7, §12)")
    for path in tracked_files(root):
        rel = path.relative_to(root).as_posix()
        if re.search(r"(^|/)\.env($|\.)", rel) and not rel.endswith(".env.example"):
            chk.fail(f"{rel}: fichier .env versionné")
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        text = without_known_fakes(text)
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                chk.fail(f"{rel}: motif de secret '{pat.pattern[:30]}…'")
    try:
        history = subprocess.run(
            ["git", "log", "--all", "-p", "--no-color", "--unified=0"], cwd=root, capture_output=True, check=True
        ).stdout.decode("utf-8", "ignore")
    except (OSError, subprocess.CalledProcessError):
        chk.info("historique git illisible : seul l'arbre de travail a été scanné")
        return chk
    added = without_known_fakes(
        "\n".join(line[1:] for line in history.splitlines() if line.startswith("+") and not line.startswith("+++"))
    )
    for pat in SECRET_PATTERNS:
        if pat.search(added):
            chk.fail(f"historique git : motif de secret '{pat.pattern[:30]}…' dans un commit passé")
    return chk


# ---------------------------------------------------------------- driver


def run_all(root: Path, today: dt.date, online: bool = False) -> list[Check]:
    research = root / "docs" / "research"
    checks = [check_state_files(root), check_subagents(root)]
    for name in REQUIRED_NOTES:
        checks.append(check_note(research / name, today))
    extra = (
        sorted(
            p
            for p in research.glob("*.md")
            if p.name not in REQUIRED_NOTES and p.name != "channel-concepts.md" and not p.name.startswith("_")
        )
        if research.is_dir()
        else []
    )
    for path in extra:
        checks.append(check_note(path, today))
    if concepts_required(root):
        checks.append(check_concepts(research / "channel-concepts.md", today, root, online))
    checks += [check_decisions(root), check_cost_model(root), check_plan(root), check_secrets(root)]
    return checks


def report(checks: list[Check], as_json: bool) -> None:
    if as_json:
        print(json.dumps([c.__dict__ for c in checks], ensure_ascii=False, indent=2))
        return
    for c in checks:
        print(f"{'✓' if c.ok else '✗'} {c.label}")
        for d in c.details:
            print(f"    {'·' if c.ok else '-'} {d}")
    failed = sum(not c.ok for c in checks)
    tail = f", {failed} en échec" if failed else ""
    print(f"\nverify-phase-0 : {len(checks) - failed}/{len(checks)} contrôles OK{tail}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--note", type=Path, help="check a single research note")
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--online", action="store_true", help="re-measure counted outliers through the YouTube API")
    args = ap.parse_args(argv)
    if args.note:
        path = args.note if args.note.is_absolute() else Path.cwd() / args.note
        if path.name == "channel-concepts.md":
            checks = [check_concepts(path, args.today, args.root.resolve(), args.online)]
        else:
            checks = [check_note(path, args.today)]
    else:
        checks = run_all(args.root.resolve(), args.today, args.online)
    report(checks, args.json)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
