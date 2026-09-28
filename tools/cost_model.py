#!/usr/bin/env python3
"""Cost model per format (MISSION §6.4, §9 phase 0). Prints the tables of docs/COST_MODEL.md.

Every parameter carries its origin: `economics.md [Sn]` (sourced) or `HC#` (sizing hypothesis,
replaced by measurements from `make bench-models` / `make gpu-smoke` in phase 3 and by Claude
usage fields in phase 2). Scenarios: favourable / central / unfavourable for the studio, so every
parameter's `low` field holds its favourable value (e.g. the highest RPM, the lowest power draw).

Usage: python3 tools/cost_model.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

SCENARIOS = ("low", "central", "high")


@dataclass(frozen=True)
class Param:
    low: float
    central: float
    high: float
    unit: str
    origin: str

    def __getitem__(self, scenario: str) -> float:
        return getattr(self, scenario)


P: dict[str, Param] = {
    # sourced (docs/research/economics.md)
    "kwh_price": Param(0.2001, 0.2001, 0.2001, "€/kWh", "economics.md [S14][S8]"),
    "system_power_w": Param(1140, 1400, 1500, "W, 4 GPU en charge", "economics.md (inférence depuis [S9], faible)"),
    "gpu_price": Param(
        430, 600, 950, "€ par carte (occasion)", "HC2 : non sourcé (seule source trouvée, economics.md S27, bloquée)"
    ),
    "claude_sub": Param(87.70, 90.0, 105.24, "€/mois, Max 5x", "HC5 : 87,70 € HT (economics.md [S10][S13]) ; haut = +20 % TVA"),
    "rpm_long_fr": Param(3.50, 2.29, 1.20, "$/1000 vues", "economics.md [S15]"),
    "usd_per_eur": Param(1.1403, 1.1403, 1.1403, "$ pour 1 €", "economics.md [S13]"),
    # hypotheses (to be measured)
    "idle_power_w": Param(80, 120, 200, "W, machine au repos", "HC1"),
    "amort_years": Param(4, 3, 2, "ans (amortissement linéaire des 4 cartes, coût fixe)", "HC2"),
    # one full 720p pass ≈ 190 GPU-s/s (< 9 min per 5 s on a 4090, video-image-models.md, ×1.75 on a 4070 Ti Super:
    # inference). Central = 3 distilled drafts (≈ 0.1 pass each) + 1 full final pass + upscale ≈ 260;
    # favourable = everything distilled; unfavourable = 4 undistilled passes.
    "gps_gen_video": Param(60, 260, 800, "GPU-s par s finale", "HC3 (Wan 2.2 : brouillons ×3 + final 720p + upscale)"),
    "gps_blender": Param(24, 96, 480, "GPU-s par s finale", "HC3 (EEVEE majoritaire, Cycles ponctuel, 24 i/s)"),
    "gps_image_25d": Param(4, 12, 40, "GPU-s par s finale", "HC3 (image + variantes + parallaxe)"),
    "gps_motion": Param(0.5, 2, 5, "GPU-s par s finale", "HC3 (Remotion + NVENC)"),
    "gps_tts": Param(0.3, 0.75, 2, "GPU-s par s de voix", "HC3 (Qwen3-TTS, régénérations incluses)"),
    "retake_long": Param(1.1, 1.2, 1.5, "facteur de reprises", "HC4"),
    "retake_short": Param(1.15, 1.3, 1.8, "facteur de reprises", "HC4"),
    "studio_claude_share": Param(0.3, 0.5, 0.7, "part de l'abonnement consommée par le studio", "HC5"),
    "short_claude_weight": Param(0.15, 0.25, 0.4, "usage Claude d'un Short / d'un long", "HC5"),
    "weekly_capacity_util": Param(0.8, 0.7, 0.5, "part des 4 cartes disponible pour la production", "HC6"),
    "g1_accept": Param(0.7, 0.5, 0.3, "part des idées présentées en G1 acceptées", "HC8"),
}

FORMATS = {
    "long": {
        "seconds": 600,
        "mix": {"gen_video": 0.20, "blender": 0.35, "image_25d": 0.25, "motion": 0.20},
        "retake": "retake_long",
    },
    "short": {
        "seconds": 40,
        "mix": {"gen_video": 0.40, "blender": 0.30, "image_25d": 0.30, "motion": 0.0},
        "retake": "retake_short",
    },
}
CADENCE = {"channels": 2, "long_per_week": 1, "short_per_week": 3}  # docs/PARAMETERS.md
# MISSION §11: G1 ≈ 3 min per idea shown, G2 ≈ 10 min (long), G3 ≈ 1 min (long only: no Test & Compare for Shorts)
GATE_MIN = {"long": {"g1": 3.0, "g2": 10.0, "g3": 1.0}, "short": {"g1": 1.0, "g2": 2.0, "g3": 0.0}}
WEEKS_PER_MONTH = 52 / 12


def gpu_hours(fmt: str, s: str) -> float:
    f = FORMATS[fmt]
    visual = sum(share * f["seconds"] * P[f"gps_{tech}"][s] for tech, share in f["mix"].items())
    return (visual * P[f["retake"]][s] + f["seconds"] * P["gps_tts"][s]) / 3600


def energy_eur_per_gpu_hour(s: str) -> float:
    return P["system_power_w"][s] / 4 / 1000 * P["kwh_price"][s]


def claude_eur(fmt: str, s: str) -> float:
    per_month_units = (
        CADENCE["channels"]
        * WEEKS_PER_MONTH
        * (CADENCE["long_per_week"] + CADENCE["short_per_week"] * P["short_claude_weight"][s])
    )
    unit = P["claude_sub"][s] * P["studio_claude_share"][s] / per_month_units
    return unit if fmt == "long" else unit * P["short_claude_weight"][s]


def per_video(fmt: str, s: str) -> dict[str, float]:
    """Marginal cost (energy + Claude share) and full cost (+ share of fixed costs, pro rata GPU hours)."""
    gh = gpu_hours(fmt, s)
    out = {"gpu_h": gh, "energy_eur": gh * energy_eur_per_gpu_hour(s), "claude_eur": claude_eur(fmt, s)}
    out["marginal_eur"] = out["energy_eur"] + out["claude_eur"]
    fixed = fixed_monthly(s)
    planned_month = capacity(s)["gpu_h_planned_week"] * WEEKS_PER_MONTH
    out["fixed_share_eur"] = (fixed["idle_energy_eur"] + fixed["amortization_eur"]) * gh / planned_month
    out["full_eur"] = out["marginal_eur"] + out["fixed_share_eur"]
    g = GATE_MIN[fmt]
    out["human_min"] = g["g1"] / P["g1_accept"][s] + g["g2"] + g["g3"]  # rejected ideas cost G1 time too
    return out


def capacity(s: str) -> dict[str, float]:
    weekly = 4 * 24 * 7 * P["weekly_capacity_util"][s]
    load = CADENCE["channels"] * (
        CADENCE["long_per_week"] * gpu_hours("long", s) + CADENCE["short_per_week"] * gpu_hours("short", s)
    )
    return {"gpu_h_available_week": weekly, "gpu_h_planned_week": load, "utilization": load / weekly}


def fixed_monthly(s: str) -> dict[str, float]:
    idle = P["idle_power_w"][s] / 1000 * 24 * 365 / 12 * P["kwh_price"][s]
    amortization = 4 * P["gpu_price"][s] / P["amort_years"][s] / 12
    return {"idle_energy_eur": idle, "amortization_eur": amortization, "claude_sub_eur": P["claude_sub"][s]}


def breakeven_views(s: str) -> float:
    """Monetized long-form views needed to cover the long's marginal cost (after YPP entry only)."""
    eur_per_1000 = P["rpm_long_fr"][s] / P["usd_per_eur"][s]
    return per_video("long", s)["full_eur"] / eur_per_1000 * 1000


def fmt_num(x: float, digits: int = 2) -> str:
    return f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")


def markdown() -> str:
    out = [
        "### Paramètres",
        "",
        "| Paramètre | Favorable | Central | Défavorable | Unité | Origine |",
        "|---|---|---|---|---|---|",
    ]
    for name, p in P.items():
        out.append(
            f"| `{name}` | {fmt_num(p.low, 4).rstrip('0').rstrip(',')} | {fmt_num(p.central, 4).rstrip('0').rstrip(',')} "
            f"| {fmt_num(p.high, 4).rstrip('0').rstrip(',')} | {p.unit} | {p.origin} |"
        )
    for fmt in FORMATS:
        f = FORMATS[fmt]
        mix = ", ".join(f"{k} {int(v * 100)} %" for k, v in f["mix"].items() if v)
        out += [
            "",
            f"### Coût d'un {fmt} ({f['seconds']} s ; mix : {mix})",
            "",
            "| Poste | Favorable | Central | Défavorable |",
            "|---|---|---|---|",
        ]
        rows = {s: per_video(fmt, s) for s in SCENARIOS}
        for key, label, d in [
            ("gpu_h", "Heures GPU (cartes × heures)", 1),
            ("energy_eur", "Électricité en charge (€)", 2),
            ("claude_eur", "Part d'abonnement Claude (€)", 2),
            ("marginal_eur", "**Coût marginal (€)**", 2),
            ("fixed_share_eur", "Part des coûts fixes : repos + amortissement (€)", 2),
            ("full_eur", "**Coût complet (€)**", 2),
            ("human_min", "Temps humain aux portes, rejets G1 inclus (min)", 0),
        ]:
            out.append(f"| {label} | " + " | ".join(fmt_num(rows[s][key], d) for s in SCENARIOS) + " |")
    out += [
        "",
        "### Capacité hebdomadaire (cadence en vigueur : "
        f"{CADENCE['channels']} chaînes × ({CADENCE['long_per_week']} long + {CADENCE['short_per_week']} Shorts))",
        "",
        "| Indicateur | Favorable | Central | Défavorable |",
        "|---|---|---|---|",
    ]
    caps = {s: capacity(s) for s in SCENARIOS}
    out.append(
        "| Heures GPU disponibles / semaine | "
        + " | ".join(fmt_num(caps[s]["gpu_h_available_week"], 0) for s in SCENARIOS)
        + " |"
    )
    out.append(
        "| Heures GPU planifiées / semaine | " + " | ".join(fmt_num(caps[s]["gpu_h_planned_week"], 1) for s in SCENARIOS) + " |"
    )
    out.append("| Taux d'occupation | " + " | ".join(f"{caps[s]['utilization'] * 100:.0f} %" for s in SCENARIOS) + " |")
    fixed = {s: fixed_monthly(s) for s in SCENARIOS}
    out += [
        "",
        "### Coûts fixes mensuels",
        "",
        "| Poste | Favorable | Central | Défavorable |",
        "|---|---|---|---|",
        "| Électricité au repos (€) | " + " | ".join(fmt_num(fixed[s]["idle_energy_eur"]) for s in SCENARIOS) + " |",
        "| Amortissement des 4 cartes (€) | " + " | ".join(fmt_num(fixed[s]["amortization_eur"]) for s in SCENARIOS) + " |",
        "| Abonnement Claude Max 5x (€, partagé avec l'usage interactif) | "
        + " | ".join(fmt_num(fixed[s]["claude_sub_eur"]) for s in SCENARIOS)
        + " |",
        "",
        "### Point mort d'un long (après entrée au YPP)",
        "",
        "| Indicateur | Favorable | Central | Défavorable |",
        "|---|---|---|---|",
        "| Vues pour couvrir le coût complet, avant impôts (RPM rapporté à toutes les vues) | "
        + " | ".join(fmt_num(breakeven_views(s), 0) for s in SCENARIOS)
        + " |",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.json:
        data = {
            s: {"long": per_video("long", s), "short": per_video("short", s), "capacity": capacity(s), "fixed": fixed_monthly(s)}
            for s in SCENARIOS
        }
        print(json.dumps(data, indent=2))
    else:
        print(markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
