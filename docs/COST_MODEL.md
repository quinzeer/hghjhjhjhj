# Modèle de coût

> Version 3 · 2026-09-28 · Phase 0, révisée après la revue et la contre-revue `critic`. Tables générées par `python3 tools/cost_model.py` (reproductible, testé par `tests/tools/test_cost_model.py` ; `make verify-phase-0` vérifie que les tables ci-dessous sont identiques à la sortie du script).
> Faits sourcés : `docs/research/economics.md`. Hypothèses de dimensionnement : HC1 à HC8 ci-dessous, à remplacer par des mesures en phase 2 (usage Claude) et en phase 3 (`make bench-models`, `make gpu-smoke`).

## Ce qu'il faut retenir

1. **Si HC3 se confirme, l'argent n'est pas la contrainte.** Scénario central : un long de 10 min coûte ≈ 4,2 € de coût marginal (électricité en charge + part d'abonnement Claude) et ≈ 11,5 € de coût complet. Les décaissements propres au studio sont l'électricité, ≈ 30 €/mois à la cadence de lancement. HC3 (GPU-s par seconde produite) n'a été mesuré sur aucune RTX 4070 Ti Super : c'est la première mesure de la phase 3.
2. **Le GPU n'est pas non plus la contrainte au lancement** : occupation ≈ 10 % (central), 68 % dans le scénario défavorable. On peut donc dépenser des heures GPU en brouillons et en sélection.
3. **Le temps humain est la contrainte la plus serrée.** En comptant les idées rejetées en G1, un long demande ≈ 17 min de portes (central), au-dessus du plafond de 15 min de MISSION §11. Pour le tenir, il faut que ≥ 75 % des idées présentées en G1 soient acceptées (le seuil ≥ 75/100 du `strategist` doit filtrer en amont) ou que G1 se fasse par lots.
4. **Les autres contraintes réelles** : le quota Claude (partagé avec l'usage interactif ; limites absolues non publiées, `apis.md`) et la probabilité de succès (loi de puissance : 86,93 % des vidéos YouTube font moins de 1 000 vues, `economics.md` [S23]).
5. **Avant l'entrée au YPP, le revenu est nul.** Le coût complet d'un long est couvert à partir de ≈ 5 700 vues au RPM France généraliste (central, avant impôts), seulement une fois la chaîne partenaire. L'entrée est plus difficile à partir du 01/02/2027 : 8 000 h de visionnage au lieu de 4 000 (`economics.md` [S5]).
6. **Les coûts fixes pèsent ≈ 63 % du coût complet d'un long au lancement** : augmenter la cadence baisse le coût unitaire, si la qualité, la conformité et le temps humain suivent.

## Hypothèses

| ID | Hypothèse | Valeur centrale | Mesure qui la remplace |
|---|---|---|---|
| HC1 | Consommation de la machine au repos | 120 W | wattmètre sur la prise (NEEDS_HUMAN H6) |
| HC2 | Amortissement linéaire des 4 cartes, coût fixe ; prix d'une carte **non sourcé** (la seule source trouvée, `economics.md` S27, était bloquée) | 3 ans ; 600 € | prix d'achat réel des cartes (NEEDS_HUMAN H6) |
| HC3 | GPU-s par seconde finale, par technique : vidéo générative 260 (1 passe 720p complète ≈ 190, déduite du seul repère publié : moins de 9 min pour 5 s sur RTX 4090, ×1,75 estimé pour une 4070 Ti Super ; + 3 brouillons distillés + upscale ; défavorable 800 = 4 passes non distillées), Blender 96, image 2,5D 12, motion design 2, voix 0,75 | voir table | `make bench-models` et `make gpu-smoke` (phase 3) ; aucune valeur mesurée sur RTX 4070 Ti Super (`video-image-models.md`, questions ouvertes) |
| HC4 | Facteur de reprises (plans régénérés après critique) | 1,2 long ; 1,3 Short | taux de rejet du `visual_critic` (phase 3) |
| HC5 | Abonnement Max 5x : 87,70 € HT sourcé, 90 € central choisi, 105,24 € avec TVA (applicabilité non confirmée) ; part consommée par le studio ; poids d'un Short face à un long | 50 % ; 0,25 | champs d'usage de `claude -p --output-format json` (phase 2) |
| HC6 | Part des 4 cartes disponible pour la production | 70 % | journal de l'ordonnanceur (phase 3) |
| HC7 | Durée moyenne de visionnage d'un long de 10 min | 4 min | YouTube Analytics (phase 6) |
| HC8 | Part des idées présentées en G1 acceptées | 50 % | journal des portes (phase 2) |

Mix de plans (MISSION §6.6, matrice des familles de plans de `video-image-models.md`) : long = 20 % vidéo générative, 35 % Blender, 25 % image animée en 2,5D, 20 % motion design ; Short = 40 % génératif, 30 % Blender, 30 % 2,5D. `generation_engineer` choisit le mix réel de chaque vidéo ; ces proportions servent au dimensionnement.

## Postes non chiffrés

Faute de source, ces postes ne sont pas inventés. Ils sont listés pour que leur absence soit visible :
- **Stockage** : disques pour les artefacts et les masters (prix €/To non sourcé, `economics.md` questions ouvertes) ; la rétention (ADR-001) borne le volume.
- **Autre matériel** : CPU, alimentation, disques, mini-PC (amortissement non chiffré).
- **Bande passante d'upload** : nulle en marginal sur un abonnement Internet forfaitaire (hypothèse), mais une vidéo 4K prend du temps à téléverser.
- **Supervision humaine hors portes** : lecture de NEEDS_HUMAN, revue des PR hebdomadaires de playbooks (phase 6).
- **Impôts et cotisations** : dépendent de la structure juridique (NEEDS_HUMAN H10) ; le point mort est calculé avant impôts.
- **Passage à Max 20x** : si le quota Max 5x ne suffit pas (≈ +90 € HT par mois, `economics.md` [S10]).
- **Upscaling 4K** : exclu tant que le benchmark n'a pas montré qu'il tient la qualité (MISSION §8).

## Long format (10 min, 1920×1080 par défaut)

- Heures GPU : 4 (favorable) · 17,9 (central) · 85 (défavorable). Les deux paramètres qui dominent sont les GPU-s de la vidéo générative et de Blender : ce sont les premiers à mesurer.
- À 4 cartes, le central représente ≈ 4 h 30 de temps réel si le travail se répartit bien.
- Entrée au YPP : 4 000 h = 60 000 vues à 4 min de visionnage moyen (HC7) ; 8 000 h après le 01/02/2027 = 120 000 vues.

## Short (40 s, 1080×1920)

- Heures GPU : 0,4 · 2,0 · 9,5. Dans la déclinaison « 1 idée → 1 long + 3 Shorts » (phase 4), les Shorts réutilisent les assets du long (rendus Blender, images, voix) : leur coût réel sera plus bas, et le modèle ne compte pas cette réutilisation.
- Revenu : à partir du 01/02/2027, le partage des revenus Shorts n'existe qu'au-delà de 10 M de vues Shorts sur 90 jours (`economics.md` [S5]). Le Short sert à la découverte et renvoie vers le long.

## Plafonds (valeurs initiales, ajustables par ADR)

Le registre des coûts **réserve** le coût estimé avant qu'un worker prenne une tâche (ADR-001, décision 5) ; un plafond atteint arrête la vidéo concernée et crée une alerte.

| Portée | Heures GPU | Claude | Humain |
|---|---|---|---|
| Par long | 36 GPU-h (≈ 2× le central) | 80 appels `claude -p`, dont 15 sur Opus au plus | 15 min (MISSION §11) |
| Par Short | 4 GPU-h | 20 appels, dont 3 sur Opus au plus | 5 min |
| Par jour | 80 GPU-h | file `llm` en pause dès qu'une limite d'usage est signalée ; plage 01:00-07:00 réservée au studio | 30 min (`docs/PARAMETERS.md`) |
| Par mois | 600 GPU-h (≈ 42 € d'électricité en charge, central) | alerte si le studio dépasse 50 % de l'usage mesuré de l'abonnement | — |

Le §0 exprime le plafond Claude en « % de fenêtre ». Anthropic ne publie pas les limites absolues des offres Max (`apis.md`), donc ce pourcentage ne peut pas encore être calculé. Le plafond est posé en nombre d'appels, puis sera recalibré en phase 2 sur l'usage mesuré et sur les messages de limite atteinte.

## Tables générées

### Paramètres

| Paramètre | Favorable | Central | Défavorable | Unité | Origine |
|---|---|---|---|---|---|
| `kwh_price` | 0,2001 | 0,2001 | 0,2001 | €/kWh | economics.md [S14][S8] |
| `system_power_w` | 1 140 | 1 400 | 1 500 | W, 4 GPU en charge | economics.md (inférence depuis [S9], faible) |
| `gpu_price` | 430 | 600 | 950 | € par carte (occasion) | HC2 : non sourcé (seule source trouvée, economics.md S27, bloquée) |
| `claude_sub` | 87,7 | 90 | 105,24 | €/mois, Max 5x | HC5 : 87,70 € HT (economics.md [S10][S13]) ; haut = +20 % TVA |
| `rpm_long_fr` | 3,5 | 2,29 | 1,2 | $/1000 vues | economics.md [S15] |
| `usd_per_eur` | 1,1403 | 1,1403 | 1,1403 | $ pour 1 € | economics.md [S13] |
| `idle_power_w` | 80 | 120 | 200 | W, machine au repos | HC1 |
| `amort_years` | 4 | 3 | 2 | ans (amortissement linéaire des 4 cartes, coût fixe) | HC2 |
| `gps_gen_video` | 60 | 260 | 800 | GPU-s par s finale | HC3 (Wan 2.2 : brouillons ×3 + final 720p + upscale) |
| `gps_blender` | 24 | 96 | 480 | GPU-s par s finale | HC3 (EEVEE majoritaire, Cycles ponctuel, 24 i/s) |
| `gps_image_25d` | 4 | 12 | 40 | GPU-s par s finale | HC3 (image + variantes + parallaxe) |
| `gps_motion` | 0,5 | 2 | 5 | GPU-s par s finale | HC3 (Remotion + NVENC) |
| `gps_tts` | 0,3 | 0,75 | 2 | GPU-s par s de voix | HC3 (Qwen3-TTS, régénérations incluses) |
| `retake_long` | 1,1 | 1,2 | 1,5 | facteur de reprises | HC4 |
| `retake_short` | 1,15 | 1,3 | 1,8 | facteur de reprises | HC4 |
| `studio_claude_share` | 0,3 | 0,5 | 0,7 | part de l'abonnement consommée par le studio | HC5 |
| `short_claude_weight` | 0,15 | 0,25 | 0,4 | usage Claude d'un Short / d'un long | HC5 |
| `weekly_capacity_util` | 0,8 | 0,7 | 0,5 | part des 4 cartes disponible pour la production | HC6 |
| `g1_accept` | 0,7 | 0,5 | 0,3 | part des idées présentées en G1 acceptées | HC8 |

### Coût d'un long (600 s ; mix : gen_video 20 %, blender 35 %, image_25d 25 %, motion 20 %)

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU (cartes × heures) | 4,0 | 17,9 | 85,1 |
| Électricité en charge (€) | 0,23 | 1,26 | 6,38 |
| Part d'abonnement Claude (€) | 2,09 | 2,97 | 3,86 |
| **Coût marginal (€)** | 2,32 | 4,22 | 10,25 |
| Part des coûts fixes : repos + amortissement (€) | 4,17 | 7,30 | 16,19 |
| **Coût complet (€)** | 6,50 | 11,52 | 26,44 |
| Temps humain aux portes, rejets G1 inclus (min) | 15 | 17 | 21 |

### Coût d'un short (40 s ; mix : gen_video 40 %, blender 30 %, image_25d 30 %)

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU (cartes × heures) | 0,4 | 2,0 | 9,5 |
| Électricité en charge (€) | 0,02 | 0,14 | 0,72 |
| Part d'abonnement Claude (€) | 0,31 | 0,74 | 1,55 |
| **Coût marginal (€)** | 0,34 | 0,88 | 2,26 |
| Part des coûts fixes : repos + amortissement (€) | 0,44 | 0,81 | 1,82 |
| **Coût complet (€)** | 0,77 | 1,69 | 4,08 |
| Temps humain aux portes, rejets G1 inclus (min) | 3 | 4 | 5 |

### Capacité hebdomadaire (cadence en vigueur : 2 chaînes × (1 long + 3 Shorts))

| Indicateur | Favorable | Central | Défavorable |
|---|---|---|---|
| Heures GPU disponibles / semaine | 538 | 470 | 336 |
| Heures GPU planifiées / semaine | 10,5 | 47,7 | 227,4 |
| Taux d'occupation | 2 % | 10 % | 68 % |

### Coûts fixes mensuels

| Poste | Favorable | Central | Défavorable |
|---|---|---|---|
| Électricité au repos (€) | 11,69 | 17,53 | 29,21 |
| Amortissement des 4 cartes (€) | 35,83 | 66,67 | 158,33 |
| Abonnement Claude Max 5x (€, partagé avec l'usage interactif) | 87,70 | 90,00 | 105,24 |

### Point mort d'un long (après entrée au YPP)

| Indicateur | Favorable | Central | Défavorable |
|---|---|---|---|
| Vues pour couvrir le coût complet, avant impôts (RPM rapporté à toutes les vues) | 2 116 | 5 737 | 25 125 |
