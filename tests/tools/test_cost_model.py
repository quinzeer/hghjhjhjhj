"""Sanity properties of tools/cost_model.py (the numbers themselves are hypotheses, the arithmetic is not)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("cost_model", ROOT / "tools" / "cost_model.py")
assert _spec and _spec.loader
cm = importlib.util.module_from_spec(_spec)
sys.modules["cost_model"] = cm
_spec.loader.exec_module(cm)


def test_every_parameter_has_an_origin() -> None:
    for name, p in cm.P.items():
        assert p.origin.startswith(("economics.md", "H")), name


@pytest.mark.parametrize("fmt", ["long", "short"])
def test_scenarios_are_ordered_and_full_cost_covers_marginal(fmt: str) -> None:
    rows = [cm.per_video(fmt, s) for s in cm.SCENARIOS]
    assert rows[0]["gpu_h"] < rows[1]["gpu_h"] < rows[2]["gpu_h"]
    assert rows[0]["marginal_eur"] < rows[1]["marginal_eur"] < rows[2]["marginal_eur"]
    for r in rows:
        assert r["full_eur"] >= r["marginal_eur"] > 0


def test_central_long_gpu_hours_match_hand_computation() -> None:
    # 600 s × (0.20×180 + 0.35×96 + 0.25×12 + 0.20×2) × 1.2 + 600 × 0.75, in hours
    expected = (600 * (0.20 * 180 + 0.35 * 96 + 0.25 * 12 + 0.20 * 2) * 1.2 + 600 * 0.75) / 3600
    assert cm.gpu_hours("long", "central") == pytest.approx(expected)


def test_fixed_costs_are_fully_allocated_at_planned_cadence() -> None:
    s = "central"
    fixed = cm.fixed_monthly(s)
    per_month = cm.CADENCE["channels"] * cm.WEEKS_PER_MONTH
    allocated = per_month * (
        cm.CADENCE["long_per_week"] * cm.per_video("long", s)["fixed_share_eur"]
        + cm.CADENCE["short_per_week"] * cm.per_video("short", s)["fixed_share_eur"]
    )
    assert allocated == pytest.approx(fixed["idle_energy_eur"] + fixed["amortization_eur"])


def test_markdown_renders() -> None:
    md = cm.markdown()
    assert "Coût d'un long" in md and "Coût d'un short" in md and "Point mort" in md
