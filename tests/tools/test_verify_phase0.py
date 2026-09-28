"""Tests for tools/verify_phase0.py: the gate must accept a compliant repo and reject each defect."""

from __future__ import annotations

import datetime as dt
import importlib.util
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


def note(n_sources: int = 8, official: int = 3, cite: str = "[S1] [S2]", **kw: str) -> str:
    return f"""# Note

## Synthèse

Fait établi {cite}.

## Constats

| # | Constat | Sources | Confiance | Conséquence |
|---|---|---|---|---|
| 1 | Fait | [S1, S3] | élevée | Règle |

## Écarts avec MISSION §4

Aucun écart [S2].

## Questions ouvertes

- Rien.

## Sources

{sources_table(n_sources, official, **kw)}
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def concept(k: int, outliers: int = 2) -> str:
    urls = "\n".join(
        f"| V{j} | Chaîne | en | 2026-01 | 1 M | 100 k | 10× | https://www.youtube.com/watch?v=abc{k}{j} |"
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


ADR_OK = """# Décisions

## ADR-001 — Architecture

### Statut
Accepté.
### Contexte
X.
### Options
A, B.
### Décision
A.
### Coût d'un retour arrière
Faible.

## ADR-002 — Fournisseurs

### Statut
Accepté.
### Contexte
X.
### Options
A, B.
### Décision
B.
### Coût d'un retour arrière
Moyen.
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
        "## Long format\n\nx\n\n## Short\n\ny\n",
    )
    for name, model in vp.SUBAGENTS.items():
        write(tmp_path / ".claude/agents" / f"{name}.md", agent_file(name, model))
    for name in vp.REQUIRED_NOTES:
        write(tmp_path / "docs/research" / name, note())
    write(tmp_path / "docs/research/channel-concepts.md", concepts_doc())
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
    ("row", "counted"),
    [
        ("| V | C | en | 2026-01-10 | 1 M | 100 k | 10× | https://youtu.be/abcdefghijk |", True),
        ("| V | C | en | 2026-01 | 1 M | 100 k | 3,4× | https://youtu.be/abcdefghijk |", True),
        ("| V | C | en | 2026-01-10 | 1 M | 100 k | 2,9× | https://youtu.be/abcdefghijk |", False),
        ("| V | C | en | 2026-01-10 | 1 M | 100 k | non calculé | https://youtu.be/abcdefghijk |", False),
        ("| V | C | en | 2023-05-01 | 1 M | 100 k | 12× | https://youtu.be/abcdefghijk |", False),
        ("| V | C | en | s.d. | 1 M | 100 k | 12× | https://youtu.be/abcdefghijk |", False),
    ],
)
def test_outlier_rows_need_measured_ratio_and_recent_date(row: str, counted: bool) -> None:
    ok, _ = vp.measured_outliers(row, TODAY)
    assert bool(ok) is counted


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
    write(repo / "docs/DECISIONS.md", ADR_OK.replace("### Options\nA, B.\n### Décision\nB.", "### Décision\nB."))
    assert any("options" in d for d in vp.check_decisions(repo).details)


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


def test_plan_needs_every_phase(repo: Path) -> None:
    write(repo / "docs/PLAN.md", "## Phase 0 — X\n\n- [ ] a\n")
    assert any("Phase 7" in d for d in vp.check_plan(repo).details)
