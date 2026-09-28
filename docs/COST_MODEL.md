# Modèle de coût

> Version 1 · 2026-09-28 · Phase 0. Tables générées par `python3 tools/cost_model.py` (reproductible, testé par `tests/tools/test_cost_model.py`).
> Paramètres sourcés : `docs/research/economics.md`. Paramètres de dimensionnement : hypothèses H1-H7 ci-dessous, remplacées par des mesures en phase 2 (usage Claude) et en phase 3 (`make bench-models`, `make gpu-smoke`).

## Ce qu'il faut retenir

1. **L'argent n'est pas la contrainte.** Scénario central : un long de 10 min coûte ≈ 4 € de coût marginal (électricité en charge + part d'abonnement Claude) et ≈ 11 € de coût complet. Les décaissements propres au studio se limitent à l'électricité, soit ≈ 30 €/mois à la cadence de lancement : le matériel et l'abonnement Claude sont déjà payés et partagés.
2. **Le GPU n'est pas non plus la contrainte au lancement** : occupation ≈ 8 % (central), ≤ 54 % même dans le scénario défavorable. On peut donc dépenser des heures GPU en brouillons et en sélection, ce qui fait monter la qualité.
3. **Les contraintes réelles** sont le quota Claude (partagé avec l'usage interactif, limites absolues non publiées : `apis.md`), le temps humain (13 min par long, 3 min par Short aux portes G1/G2) et la probabilité de succès (loi de puissance : 86,93 % des vidéos YouTube font moins de 1 000 vues, `economics.md` [S23]).
4. **Avant l'entrée au YPP, le revenu est nul.** Le coût complet d'un long est couvert à partir de ≈ 5 700 vues monétisées (central), mais seulement une fois la chaîne partenaire. L'entrée est plus difficile à partir du 01/02/2027 : 8 000 h de visionnage au lieu de 4 000 (`economics.md` [S5]).
5. **Les coûts fixes pèsent ≈ 65 % du coût complet d'un long au lancement.** Augmenter la cadence réduit le coût unitaire, à condition que la qualité et la conformité tiennent.

## Hypothèses

| ID | Hypothèse | Valeur centrale | Mesure qui la remplace |
|---|---|---|---|
| H1 | Consommation de la machine au repos | 120 W | wattmètre sur la prise (NEEDS_HUMAN H6) |
| H2 | Amortissement linéaire des 4 cartes, coût fixe dans le temps | 3 ans | décision humaine (renouvellement du matériel) |
| H3 | GPU-s par seconde finale, par technique : vidéo générative 180, Blender 96, image 2,5D 12, motion design 2, voix 0,75 | voir table | `make bench-models` et `make gpu-smoke` (phase 3) ; aucune de ces valeurs n'a été mesurée sur RTX 4070 Ti Super (`video-image-models.md`, questions ouvertes) |
| H4 | Facteur de reprises (plans régénérés après critique) | 1,2 long ; 1,3 Short | taux de rejet du `visual_critic` (phase 3) |
| H5 | Part de l'abonnement Claude consommée par le studio ; poids d'un Short face à un long | 50 % ; 0,25 | champs d'usage de `claude -p --output-format json` (phase 2) |
| H6 | Part des 4 cartes disponible pour la production | 70 % | journal de l'ordonnanceur (phase 3) |
| H7 | Durée moyenne de visionnage d'un long de 10 min | 4 min | YouTube Analytics (phase 6) |

Mix de plans (MISSION §6.6, `video-image-models.md` matrice des familles de plans) : long = 20 % vidéo générative, 35 % Blender, 25 % image animée en 2,5D, 20 % motion design ; Short = 40 % génératif, 30 % Blender, 30 % 2,5D. Le mix réel de chaque vidéo est choisi par `generation_engineer` ; ces proportions ne servent qu'au dimensionnement.

## Long format (10 min, 1920×1080 par défaut)

- Heures GPU : 4 (favorable) · 14,7 (central) · 69 (défavorable). Les deux paramètres qui dominent sont les GPU-s de la vidéo générative et de Blender : ce sont les premiers à mesurer.
- À 4 cartes, le central représente ≈ 3 h 40 de temps réel si le travail se répartit bien.
- Master 3840×2160 : seulement si l'upscaling retenu tient la qualité (MISSION §8) ; son coût (SeedVR2 sur toute la durée) n'est **pas** inclus et sera mesuré avant d'être activé.
- Entrée au YPP : 4 000 h = 60 000 vues à 4 min de visionnage moyen (H7) ; 8 000 h après le 01/02/2027 = 120 000 vues.

## Short (40 s, 1080×1920)

- Heures GPU : 0,4 · 1,5 · 7. Dans la déclinaison « 1 idée → 1 long + 3 Shorts » (phase 4), les Shorts réutilisent les assets du long (rendus Blender, images, voix) : leur coût marginal réel sera plus bas ; le modèle ne compte pas cette réutilisation.
- Revenu : à partir du 01/02/2027, le partage des revenus Shorts n'existe qu'au-delà de 10 M de vues Shorts sur 90 jours (`economics.md` [S5]). Le Short sert à la découverte et renvoie vers le long.

## Plafonds (valeurs initiales, ajustables par ADR)

Le registre des coûts vérifie ces plafonds **avant** de donner une tâche à un worker (ADR-001, décision 5). Dépassement = arrêt dur de la vidéo concernée + alerte.

| Portée | Heures GPU | Claude | Humain |
|---|---|---|---|
| Par long | 30 GPU-h (≈ 2× le central) | 80 appels `claude -p`, dont 15 sur Opus au plus | 15 min |
| Par Short | 4 GPU-h | 20 appels, dont 3 sur Opus au plus | 5 min |
| Par jour | 80 GPU-h | file `llm` en pause dès qu'une limite d'usage est signalée ; plage 01:00-07:00 réservée au studio | 30 min (`docs/PARAMETERS.md`) |
| Par mois | 600 GPU-h (≈ 42 € d'électricité en charge, central) | alerte si le studio dépasse 50 % de l'usage mesuré de l'abonnement | — |

Le §0 exprime le plafond Claude en « % de fenêtre ». Anthropic ne publie pas les limites absolues des offres Max (`apis.md`), donc ce pourcentage ne peut pas encore être calculé. Le plafond est posé en nombre d'appels, puis sera recalibré en phase 2 sur l'usage mesuré (champs d'usage de la sortie JSON) et sur les messages de limite atteinte.

## Tables générées

### Paramètres

| Paramètre | Favorable | Central | Défavorable | Unité | Origine |
|---|---|---|---|---|---|
| `kwh_price` | 0,2001 | 0,2001 | 0,2001 | €/kWh | economics.md [S14][S8] |
| `system_power_w` | 1 140 | 1 400 | 1 500 | W, 4 GPU en charge | economics.md (inférence depuis [S9], faible) |
| `gpu_price` | 430 | 600 | 950 | € par carte (occasion) | economics.md [S27] (faible) |
| `claude_sub` | 87,7 | 90 | 105,3 | €/mois, Max 5x | economics.md [S10][S13] |
| `rpm_long_fr` | 3,5 | 2,29 | 1,2 | $/1000 vues | economics.md [S15] |
| `usd_per_eur` | 1,1403 | 1,1403 | 1,1403 | $ pour 1 € | economics.md [S13] |
| `idle_power_w` | 80 | 120 | 200 | W, machine au repos | H1 |
| `amort_years` | 4 | 3 | 2 | ans (amortissement linéaire des 4 cartes, coût fixe) | H2 |
| `gps_gen_video` | 60 | 180 | 480 | GPU-s par s finale | H3 (Wan 2.2 : brouillons ×3 + final 720p + upscale) |
| `gps_blender` | 24 | 96 | 480 | GPU-s par s finale | H3 (EEVEE majoritaire, Cycles ponctuel, 24 i/s) |
| `gps_image_25d` | 4 | 12 | 40 | GPU-s par s finale | H3 (image + variantes + parallaxe) |
| `gps_motion` | 0,5 | 2 | 5 | GPU-s par s finale | H3 (Remotion + NVENC) |
| `gps_tts` | 0,3 | 0,75 | 2 | GPU-s par s de voix | H3 (Qwen3-TTS, régénérations incluses) |
| `retake_long` | 1,1 | 1,2 | 1,5 | facteur de reprises | H4 |
| `retake_short` | 1,15 | 1,3 | 1,8 | facteur de reprises | H4 |
| `studio_claude_share` | 0,3 | 0,5 | 0,7 | part de l'abonnement consommée par le studio | H5 |
| `short_claude_weight` | 0,15 | 0,25 | 0,4 | usage Claude d'un Short / d'un long | H5 |
| `weekly_capacity_util` | 0,8 | 0,7 | 0,5 | part des 4 cartes disponible pour la production | H6 |

### Coût d'un long (600 s ; mix : gen_video 20 %, blender 35 %, image_25d 25 %, motion 20 %)

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU (cartes × heures) | 4,0 | 14,7 | 69,1 |
| Électricité en charge (€) | 0,23 | 1,03 | 5,18 |
| Part d'abonnement Claude (€) | 2,09 | 2,97 | 3,87 |
| **Coût marginal (€)** | 2,32 | 4,00 | 9,05 |
| Part des coûts fixes : repos + amortissement (€) | 4,17 | 7,42 | 16,61 |
| **Coût complet (€)** | 6,50 | 11,42 | 25,66 |
| Temps humain (min) | 13 | 13 | 13 |

### Coût d'un short (40 s ; mix : gen_video 40 %, blender 30 %, image_25d 30 %)

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU (cartes × heures) | 0,4 | 1,5 | 7,0 |
| Électricité en charge (€) | 0,02 | 0,11 | 0,52 |
| Part d'abonnement Claude (€) | 0,31 | 0,74 | 1,55 |
| **Coût marginal (€)** | 0,34 | 0,85 | 2,07 |
| Part des coûts fixes : repos + amortissement (€) | 0,44 | 0,76 | 1,68 |
| **Coût complet (€)** | 0,77 | 1,61 | 3,75 |
| Temps humain (min) | 3 | 3 | 3 |

### Capacité hebdomadaire (cadence en vigueur : 2 chaînes × (1 long + 3 Shorts))

| Indicateur | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU disponibles / semaine | 538 | 470 | 336 |
| Heures GPU planifiées / semaine | 10,5 | 38,5 | 180,1 |
| Taux d'occupation | 2 % | 8 % | 54 % |

### Coûts fixes mensuels

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Électricité au repos (€) | 11,69 | 17,53 | 29,21 |
| Amortissement des 4 cartes (€) | 35,83 | 66,67 | 158,33 |
| Abonnement Claude Max 5x (€, partagé avec l'usage interactif) | 87,70 | 90,00 | 105,30 |

### Point mort d'un long (après entrée au YPP)

| Indicateur | Favorable | Central | Défavorable |
|---|---|---|---|
| Vues monétisées pour couvrir le coût complet | 2 116 | 5 687 | 24 379 |
