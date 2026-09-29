"""Tests for tools/verify_phase0.py: the gate must accept a compliant repo and reject each defect."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("verify_phase0", ROOT / "tools" / "verify_phase0.py")
assert _spec and _spec.loader
vp = importlib.util.module_from_spec(_spec)
sys.modules["verify_phase0"] = vp
_spec.loader.exec_module(vp)

TODAY = dt.date(2026, 9, 28)


def sources_table(n: int, official: int = 3, date: str = "2026-07-16", consulted: str = "2026-09-28") -> str:
    rows = [
        "| ID | Titre | URL | Date source | Consulté | Type | Confiance |",
        "|---|---|---|---|---|---|---|",
    ]
    for i in range(1, n + 1):
        typ = "officiel" if i <= official else "presse"
        rows.append(f"| S{i} | Source {i} | https://src.test/{i} | {date} | {consulted} | {typ} | élevée |")
    return "\n".join(rows)


ALL_CITED = " ".join(f"[S{i}]" for i in range(1, 9))


SYNTH = (
    "La synthèse résume les faits qui changent l'architecture du studio, chacun avec sa source, sa date et sa "
    "confiance, puis précise ce qui reste incertain et ce que le studio doit en conclure pour ses règles de "
    "production, de conformité et de publication, sans rien inventer au passage."
)


def note(n_sources: int = 8, official: int = 3, cite: str = ALL_CITED, **kw: str) -> str:
    rows = "\n".join(f"| {i} | Fait précis numéro {i} | [S{i}] | élevée | Règle {i} |" for i in range(2, 9))
    return f"""# Note

## Synthèse

{SYNTH} {cite}.

## Constats

| # | Constat | Sources | Confiance | Conséquence |
|---|---|---|---|---|
| 1 | Fait | [S1, S3] | élevée | Règle |
{rows}

## Écarts avec MISSION §4

Aucun écart constaté sur les affirmations de la mission couvertes par cette note, qui restent exactes [S2].

## Questions ouvertes

- Rien d'important ne reste ouvert pour cette note.

## Sources

{sources_table(n_sources, official, **kw)}
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


MEASURED = "API YouTube Data v3 ; médiane des 30 longs de la chaîne les plus proches en date"


def record(vid: str, views: int = 1_000_000, published: str = "2026-01-10", median: int = 100_000) -> dict:
    return {
        "video_id": vid,
        "views": views,
        "published": published,
        "method": MEASURED,
        "baseline_views": [median] * 30,
        "baseline_ids": [f"b{i:010d}" for i in range(30)],
    }


def concept(k: int, outliers: int = 2) -> str:
    urls = "\n".join(
        f"| V{j} | Chaîne | en | 2026-01-10 | 1 000 000 | 100 000 ({MEASURED}) | 10,0× "
        f"| https://www.youtube.com/watch?v=abc{k}{j} |"
        for j in range(outliers)
    )
    return f"""### C{k:02d} — Concept {k}

Preuve de demande [S1] :

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane | Ratio | URL |
|---|---|---|---|---|---|---|---|
{urls}

RPM estimé : 3-6 $. Légitimité : forte. Risque politique : faible. Sérialité : 40 épisodes. Coût unitaire : moyen.
"""


def concepts_doc(n: int = 6, outliers: int = 2) -> str:
    body = note().replace(
        "## Questions ouvertes",
        "## Classement\n\n1. C01\n\n" + "\n".join(concept(k, outliers) for k in range(1, n + 1)) + "\n## Questions ouvertes",
    )
    return body


WORDS = (
    "Ce paragraphe décrit les contraintes, les options comparées et la décision avec assez de détail pour être relu "
    "par un humain qui doit comprendre pourquoi ce choix a été fait, ce qu'il coûte, ce qui le ferait changer et "
    "comment on le vérifie en pratique."
)

ADR_OK = f"""# Décisions

## ADR-001 — Architecture

### Statut
Accepté.
### Contexte
{WORDS} Voir `economics.md` [S1].
### Options
{WORDS}
### Décision
{WORDS}
### Conséquences
Tests de phase 1.
### Coût d'un retour arrière
Faible.
### Sources
`economics.md` [S2].

## ADR-002 — Fournisseurs

### Statut
Accepté.
### Contexte
{WORDS}
### Options
{WORDS}
### Décision
{WORDS}
### Conséquences
Benchmark.
### Coût d'un retour arrière
Moyen.
### Sources
`economics.md` [S3].
"""


def agent_file(name: str, model: str) -> str:
    return f"---\nname: {name}\ndescription: Rôle {name}.\nmodel: {model}\n---\n\nPrompt.\n"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    for rel in ("docs/MISSION.md", "docs/PROGRESS.md", "docs/NEEDS_HUMAN.md"):
        write(tmp_path / rel, "# x\n")
    write(tmp_path / "CLAUDE.md", "# Claude\n")
    write(tmp_path / "docs/DECISIONS.md", ADR_OK)
    write(tmp_path / "docs/PLAN.md", "\n".join(f"## Phase {n} — X\n\n- [ ] tâche\n" for n in range(8)))
    write(
        tmp_path / "docs/COST_MODEL.md",
        "# Coûts\n\nParamètres : docs/research/economics.md\n\n## Hypothèses\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        "## Long format\n\nx\n\n## Short\n\ny\n\n## Tables générées\n\n| t |\n|---|\n",
    )
    for name, model in vp.SUBAGENTS.items():
        write(tmp_path / ".claude/agents" / f"{name}.md", agent_file(name, model))
    for name in vp.REQUIRED_NOTES:
        write(tmp_path / "docs/research" / name, note())
    write(tmp_path / "docs/research/channel-concepts.md", concepts_doc())
    recs = [record(f"abc{k}{j}") for k in range(1, 7) for j in range(2)]
    write(tmp_path / "docs/research/outliers/fixture.json", json.dumps(recs))
    return tmp_path


def failures(checks: list) -> list[str]:
    return [d for c in checks if not c.ok for d in c.details]


def test_compliant_repo_passes(repo: Path) -> None:
    checks = vp.run_all(repo, TODAY)
    assert failures(checks) == []
    assert vp.main(["--root", str(repo), "--today", "2026-09-28"]) == 0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (note(n_sources=7), "sources datées"),
        (note(date="s.d."), "sources datées"),
        (note(date="2026-12-01"), "futur"),
        (note(consulted="2026-10-01"), "consultation dans le futur"),
        (note(cite="[S1] [S42]"), "S42"),
        (note().replace("## Questions ouvertes", "## Autre"), "questions ouvertes"),
        (note().replace("| élevée |\n", "| haute |\n"), "confiance"),
        (note().replace("presse", "blog"), "type"),
        (note() + "\nTODO: finir\n", "inachevé"),
    ],
)
def test_note_defects_are_rejected(tmp_path: Path, text: str, expected: str) -> None:
    chk = vp.check_note(write(tmp_path / "x.md", text), TODAY)
    assert not chk.ok
    assert any(expected in d for d in chk.details), chk.details


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (note().replace("| [S8] |", "| — |"), "datées et citées"),
        (note().replace(SYNTH, "Court."), "synthese"),
        (note().replace("https://src.test/1 ", "https://huggingface.co/x/discussions/2 "), "forum"),
        (note().replace("https://src.test/2 ", "https://en.wikipedia.org/wiki/X "), "forum"),
        (note().replace("| Source 3 |", "| Source 3 (HTTP 404) |"), "non ouverte"),
        (note().replace("| Source 4 |", "| Source 4 (vue en résultat de recherche) |"), "indirectement"),
        (
            note().replace(
                "| 2026-07-16 | 2026-09-28 | officiel | élevée |", "| 2026-09-20 | 2026-09-10 | officiel | élevée |", 1
            ),
            "postérieure",
        ),
        (note().replace("| 1 | Fait | [S1, S3] |", "| 1 | Fait | presse |"), "constat sans source"),
    ],
)
def test_hollow_notes_are_rejected(tmp_path: Path, text: str, expected: str) -> None:
    chk = vp.check_note(write(tmp_path / "x.md", text), TODAY)
    assert not chk.ok
    assert any(expected in d for d in chk.details), chk.details


def test_labelled_inference_or_absence_is_accepted(tmp_path: Path) -> None:
    for label in ("Inférence (non sourcé)", "non trouvé"):
        extra = f"| 1 | Fait | [S1, S3] | élevée | Règle |\n| 9 | Fait sans source | {label} | faible | Règle |"
        text = note().replace("| 1 | Fait | [S1, S3] | élevée | Règle |", extra)
        assert vp.check_note(write(tmp_path / "x.md", text), TODAY).ok


def test_policy_note_needs_three_official_sources(tmp_path: Path) -> None:
    chk = vp.check_note(write(tmp_path / "apis.md", note(official=2)), TODAY)
    assert not chk.ok
    assert any("officielles" in d for d in chk.details)
    assert vp.check_note(write(tmp_path / "craft.md", note(official=0)), TODAY).ok


def test_month_precision_dates_are_accepted(tmp_path: Path) -> None:
    assert vp.check_note(write(tmp_path / "x.md", note(date="2026-09")), TODAY).ok
    assert vp.check_note(write(tmp_path / "y.md", note(date="2014")), TODAY).ok


def test_concepts_need_six_sections_and_two_outliers(tmp_path: Path) -> None:
    chk = vp.check_concepts(write(tmp_path / "channel-concepts.md", concepts_doc(n=5)), TODAY)
    assert any("< 6" in d for d in chk.details)
    chk = vp.check_concepts(write(tmp_path / "channel-concepts.md", concepts_doc(outliers=1)), TODAY)
    assert any("outlier" in d for d in chk.details)


@pytest.mark.parametrize(
    ("row", "recs", "counted"),
    [
        (f"| V | C | en | 2026-01-10 | 1 000 000 | 100 000 ({MEASURED}) | 10× | https://youtu.be/abcdefghijk |", None, True),
        (
            f"| V | C | en | 2026-01-10 | 340 000 | 100 000 ({MEASURED}) | 3,4× | https://youtu.be/abcdefghijk |",
            record("abcdefghijk", views=340_000),
            True,
        ),
        (
            f"| V | C | en | 2026-01-10 | 296 000 | 100 000 ({MEASURED}) | 3,0× | https://youtu.be/abcdefghijk |",
            record("abcdefghijk", views=296_000),
            False,  # 2.96 recomputed: rounding in the table does not help
        ),
        (
            f"| V | C | en | 2023-05-01 | 1 000 000 | 100 000 ({MEASURED}) | 10× | https://youtu.be/abcdefghijk |",
            record("abcdefghijk", published="2023-05-01"),
            False,
        ),
        (f"| V | C | en | 2026-01-10 | 1 000 000 | 100 000 ({MEASURED}) | 10× | https://youtu.be/zzzzzzzzzzz |", None, False),
        (
            f"| V | C | en | 2026-01-10 | 2 000 000 | 100 000 ({MEASURED}) | 20× | https://youtu.be/abcdefghijk |",
            None,
            False,  # table says 2 M views, raw measurement says 1 M
        ),
        (
            f"| V | C | en | 2026-01-10 | 1 000 000 | 100 000 ({MEASURED}) | 10× | https://youtu.be/abcdefghijk |",
            {**record("abcdefghijk"), "baseline_views": [100_000] * 5},
            False,  # baseline too small
        ),
        (
            f"| V | C | en | 2026-01-10 | 1 000 000 | 0 ({MEASURED}) | 10× | https://youtu.be/abcdefghijk |",
            {**record("abcdefghijk"), "baseline_views": [0] * 30},
            False,  # zero median must fail cleanly, not crash
        ),
    ],
)
def test_outlier_rows_must_match_raw_measurements(row: str, recs: dict | None, counted: bool) -> None:
    rec = recs or record("abcdefghijk")
    ok, rejected = vp.measured_outliers(row, TODAY, {rec["video_id"]: rec})
    assert bool(ok) is counted, rejected


def test_hand_typed_outlier_rows_do_not_count() -> None:
    """The contre-revue forged 12 rows that claimed the API method: without raw records they must not count."""
    row = "| V | C | en | 2026-01-10 | 400 000 | 100 000 (API YouTube Data v3 ; inventé) | 4,0× | https://youtu.be/FAKE0000001 |"
    ok, rejected = vp.measured_outliers(row, TODAY, {})
    assert not ok and "absent des mesures brutes" in rejected[0]


def test_concepts_not_required_once_confirmed(repo: Path) -> None:
    (repo / "docs/research/channel-concepts.md").unlink()
    assert vp.concepts_required(repo)
    write(
        repo / "docs/PARAMETERS.md",
        "| Paramètre | Valeur | Statut |\n|---|---|---|\n"
        "| Concept chaîne A | x | confirmé |\n| Concept chaîne B | y | confirmé |\n",
    )
    assert not vp.concepts_required(repo)
    assert failures(vp.run_all(repo, TODAY)) == []


def test_adr_with_todo_or_missing_section_fails(repo: Path) -> None:
    write(repo / "docs/DECISIONS.md", ADR_OK.replace("Faible.", "TODO"))
    assert any("TODO" in d for d in vp.check_decisions(repo).details)
    write(repo / "docs/DECISIONS.md", ADR_OK.replace("### Conséquences\nBenchmark.\n", ""))
    assert any("consequences" in d for d in vp.check_decisions(repo).details)


def test_hollow_adr_is_rejected(repo: Path) -> None:
    hollow = ADR_OK.replace("### Décision\n" + ADR_OK.split("### Décision\n")[1].split("\n")[0], "### Décision\nA.", 1)
    write(repo / "docs/DECISIONS.md", hollow)
    assert any("trop courte" in d for d in vp.check_decisions(repo).details)
    write(repo / "docs/DECISIONS.md", ADR_OK.replace("`economics.md` [S2]", "`economics.md` [S99]"))
    assert any("S99" in d for d in vp.check_decisions(repo).details)


def test_repetitive_adr_or_adr_without_sources_is_rejected(repo: Path) -> None:
    write(repo / "docs/DECISIONS.md", ADR_OK.replace(WORDS, " ".join(["mot"] * 45), 1))
    assert any("répétitive" in d for d in vp.check_decisions(repo).details)
    write(repo / "docs/DECISIONS.md", ADR_OK.replace("`economics.md` [S2].", "Néant."))
    assert any("Sources" in d for d in vp.check_decisions(repo).details)


def test_cost_model_must_match_generator(repo: Path) -> None:
    write(repo / "tools/cost_model.py", "print('| t |')\nprint('|---|')\n")
    assert vp.check_cost_model(repo).ok
    write(repo / "tools/cost_model.py", "print('| autre |')\n")
    assert any("régénérer" in d for d in vp.check_cost_model(repo).details)


def test_subagent_model_mismatch_fails(repo: Path) -> None:
    write(repo / ".claude/agents/critic.md", agent_file("critic", "sonnet"))
    assert any("critic" in d for d in vp.check_subagents(repo).details)


def test_claude_md_line_budget(repo: Path) -> None:
    write(repo / "CLAUDE.md", "x\n" * 151)
    assert not vp.check_state_files(repo).ok


def test_secret_detection(repo: Path) -> None:
    write(repo / "config.txt", "ANTHROPIC_API_KEY=sk-ant-" + "a" * 30 + "\n")
    assert not vp.check_secrets(repo).ok


def test_empty_values_in_env_example_are_not_secrets(repo: Path) -> None:
    write(repo / ".env.example", "# comment\nCLAUDE_CODE_OAUTH_TOKEN=\n# next line\nYOUTUBE_API_KEY=\n")
    assert vp.check_secrets(repo).ok
    write(repo / ".env.example", "CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-abcdef\n")
    assert not vp.check_secrets(repo).ok


FAKE_KEY = "sk-" + "ant-api03-FAKEfake0123456789"  # built here: the gate scans this file too


def test_a_listed_placeholder_token_is_not_a_secret(repo: Path) -> None:
    write(repo / "tests" / "fixture.py", f'FAKE = "{FAKE_KEY}"\nother = "x {FAKE_KEY}, y"\n')
    assert vp.check_secrets(repo).ok


@pytest.mark.parametrize(
    "text",
    [
        f'key = "{FAKE_KEY}REALSUFFIX0123"',  # continues past the listed placeholder
        f'key = "prefix-{FAKE_KEY}"',  # starts before it
        f'key = "{FAKE_KEY[:-1]}0"',  # a lookalike that is not listed (built here: this file is scanned too)
        f"ANTHROPIC_API_KEY={FAKE_KEY}0123456789\n",
    ],
)
def test_a_lookalike_of_a_listed_placeholder_is_still_a_secret(repo: Path, text: str) -> None:
    write(repo / "tests" / "fixture.py", text)
    assert not vp.check_secrets(repo).ok


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=repo, check=True, capture_output=True)


def test_the_history_scan_applies_the_same_placeholder_rule(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    write(tmp_path / "fixture.py", f'FAKE = "{FAKE_KEY}"\n')
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "fixture")
    assert vp.check_secrets(tmp_path).ok
    write(tmp_path / "leak.py", f'REAL = "{FAKE_KEY}0000"\n')
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "leak")
    assert any("historique git" in d for d in vp.check_secrets(tmp_path).details)


def test_plan_needs_every_phase(repo: Path) -> None:
    write(repo / "docs/PLAN.md", "## Phase 0 — X\n\n- [ ] a\n")
    assert any("Phase 7" in d for d in vp.check_plan(repo).details)
