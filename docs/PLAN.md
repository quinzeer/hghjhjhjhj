# Plan

Source : `docs/MISSION.md` §9. Chaque phase se ferme par la même procédure, dans cet ordre :

1. `make verify-phase-N` → code 0 ; sortie collée dans `docs/PROGRESS.md`.
2. Revue du sous-agent `critic` sur la déclaration de fin ; ses réserves bloquantes sont corrigées ou acceptées par ADR.
3. PR de phase → revue `/code-review` → corrections → merge (après accord humain).
4. Résumé de fin de session (≤ 15 lignes).

Légende : `[x]` fait et prouvé (preuve dans PROGRESS) · `[ ]` à faire · `[~]` en cours.

## Phase 0 — Recherche et cadrage

Critère de sortie : `make verify-phase-0` → 0.

- [x] `docs/MISSION.md` enregistré tel quel (commit `docs: mission initiale`)
- [x] Fichiers d'état : `CLAUDE.md`, `docs/PLAN.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/NEEDS_HUMAN.md`, `docs/PARAMETERS.md`
- [x] 9 sous-agents de construction dans `.claude/agents/` (format vérifié dans la doc Claude Code, frontmatter validé)
- [x] `make verify-phase-0` v1 + 19 tests (`tests/tools/`) ; `make doctor` v1
- [x] `docs/research/platform-policies.md` (29 sources, 20 officielles)
- [x] `docs/research/apis.md` (43 sources, dont l'état de l'usage de `claude -p` sur abonnement)
- [x] `docs/research/video-image-models.md` (66 sources)
- [x] `docs/research/audio-models.md`
- [x] `docs/research/craft.md`
- [x] `docs/research/economics.md`
- [x] `docs/research/infra.md` (hors liste de la mission, nécessaire à l'ADR-001)
- [x] `docs/research/channel-concepts.md` : fusion des lots A et B, top 6 classé hors preuve de demande
- [ ] Preuve de demande mesurée par l'API (≥ 2 outliers récents par concept) — bloqué par H0 (clé `YOUTUBE_API_KEY`)
- [x] ADR-001 architecture
- [x] ADR-002 stratégie fournisseurs (modèles locaux, licences) ; ADR-003 corrections proposées ; ADR-004 preuve de demande
- [x] `docs/COST_MODEL.md` (généré par `tools/cost_model.py`, testé)
- [~] Revue `critic` de la phase 0
- [ ] Choix humain des concepts (H2) → hors critère de sortie, bloque la phase 2

## Phase 1 — Squelette, contrats, mocks

Critère de sortie : `make verify-phase-1` → 0 (contient `make test`, couverture ≥ 80 % sur le cœur, `make e2e-dry` rejoué deux fois sans régénération, contrôles `ffprobe`).

- [ ] Structure du dépôt `studio/` (paquet Python 3.12, uv, ruff, mypy strict sur le cœur)
- [ ] Modèles de domaine Pydantic v2 : Channel, Series, Idea, Package, Script, Scene, Shot, Asset, Render, Publication, Metric, Experiment, CostEntry
- [ ] Export JSON Schema de chaque contrat + test de non-régression des schémas
- [ ] Mapping bidirectionnel du JSON de scènes du skill `scenariste-youtube` (v1.0) ↔ modèles internes, testé sur fixtures, sans perte
- [ ] Orchestrateur retenu par l'ADR-001 : graphe d'étapes idempotentes, reprise après crash testée
- [ ] Stockage d'artefacts adressé par hash (entrées + version de code + paramètres) ; relance = zéro recalcul (test)
- [ ] Registre des coûts (heures GPU, kWh, usage Claude) + plafonds avec arrêt dur (test)
- [ ] Ordonnanceur de file multi-GPU simulé (4 workers mock, priorités, préemption des brouillons)
- [ ] Interfaces d'adaptateurs (texte→image, image→vidéo, texte→vidéo, lip-sync, TTS, musique, SFX, upscaling, interpolation, transcription, LLM, critique visuelle) + mocks déterministes nommés `mock`
- [ ] `ClaudeCodeRunner` (interface + backend `claude -p` + backend mock) et gestionnaire de quota (détection de limite, pause, reprise) testés sur sorties enregistrées
- [ ] CLI `studio run --channel A --format short --dry-run`
- [ ] `make e2e-dry` : un Short 1080×1920 et un long 16:9 de démonstration via mocks, manifeste + registre de coûts, validés par `ffprobe`
- [ ] `make doctor` v2 (Docker, GPU, ffmpeg côté machine d'exécution)
- [ ] CI GitHub Actions : lint, types, tests, `make verify-phase-0`, `make e2e-dry`
- [ ] `make verify-phase-1`

## Phase 2 — Cerveau éditorial

Critère de sortie : `make eval-editorial` (100 % des cas pièges bloqués ; ≥ 90 % des scripts passent les contrôles déterministes ; accord entre juges publié ; usage Claude moyen par script affiché).

- [ ] Skill `scenariste-youtube` converti en playbooks versionnés (`studio/.claude/skills/`) et contrôles déterministes (durée = mots ÷ débit, hook, boucles, tics d'écriture IA, longueur des titres) — après H1
- [ ] `knowledge/` sourcé et daté : plateformes, psychologie, craft, conformité (dérivé des notes de phase 0)
- [ ] Specs YAML + sous-agents runtime : showrunner, scout, strategist, psychologist, distribution_scientist, packaging_director, head_writer, fact_checker, compliance_officer
- [ ] Contrôle anti-gabarit intra et inter-chaînes (similarité avec les 10 dernières vidéos et les chaînes sœurs)
- [ ] Banc `evals/editorial/` : ≥ 20 sujets de référence + ≥ 15 cas pièges, rapport HTML
- [ ] Bibles des chaînes A et B (après H2)
- [ ] Porte G1 (idée + packaging) dans l'interface mobile, décisions agent et humain enregistrées

## Phase 3 — Production image, vidéo, voix, son

Critère de sortie : tests d'adaptateurs sur fixtures (cloud) ; `make gpu-smoke` sur la machine GPU (sortie dans PROGRESS) ; rappel du `visual_critic` ≥ 0,8 sur les défauts bloquants ; audio conforme au §8.

- [ ] Bibles visuelles par chaîne (art_director)
- [ ] ≥ 2 adaptateurs vidéo à poids ouverts, ≥ 1 image, upscaler, interpolation (shortlist ADR-002)
- [ ] Bibliothèque Blender procédurale ≥ 10 gabarits paramétrables
- [ ] TTS Qwen3 + Kokoro sur CUDA (portage de la voix du narrateur, H5), contrôle WER
- [ ] Musique et SFX locaux ou sous licence documentée ; registre des droits
- [ ] `make bench-models` : liste de plans figée → matrice qualité / coût / latence + votes à l'aveugle
- [ ] `visual_critic` + jeu étiqueté ≥ 100 clips, précision/rappel publiés
- [ ] `docs/CAPACITY.md` : minutes GPU par minute finale, cadence tenable par chaîne
- [ ] Marquage C2PA / métadonnées de divulgation des fichiers produits

## Phase 4 — Montage et packaging

Critère de sortie : `make e2e-real IDEA=<id>` sur la machine GPU, rapport QA vert, lisibilité des miniatures, distance entre concepts ≥ seuil.

- [ ] Monteur (Remotion + ffmpeg) : courbe de rythme, ruptures de motif, sous-titres, écran de fin
- [ ] 3 ouvertures alternatives par long
- [ ] Miniatures : génération + composition du texte, test à 120 px (OCR + vision), 3 concepts distants
- [ ] Déclinaisons : 1 idée → 1 long + 3 Shorts + 3 TikTok réécrits pour le format
- [ ] Porte G2 dans l'interface mobile

## Phase 5 — Publication et conformité plateforme

Critère de sortie : upload privé réussi sur une chaîne de test + relecture `videos.list` qui confirme chaque champ ; tests de contrat des API sur fixtures.

- [ ] Upload YouTube reprenable : `containsSyntheticMedia`, localisations, sous-titres, miniature, planification, playlists
- [ ] TikTok : Direct Post après audit, sinon brouillon
- [ ] Gestionnaire de quotas YouTube / TikTok
- [ ] Dossiers d'audit YouTube et TikTok (usage, confidentialité, vidéo du flux OAuth) — H8, H9
- [ ] Checklist et fichiers pour la porte G3 (Test & Compare)

## Phase 6 — Boucle d'apprentissage

Critère de sortie : `make learn-dry` produit, sur données synthétiques, un diagnostic et des propositions d'expériences.

- [ ] Ingestion analytics (ce que chaque API expose réellement, cf. `docs/research/apis.md`)
- [ ] Diagnostic automatique (table symptôme → cause → action du skill)
- [ ] Cadre d'expériences : hypothèse pré-enregistrée, taille d'échantillon, analyse bayésienne
- [ ] Prédicteurs CTR / rétention quand l'échantillon suffit, calibration publiée
- [ ] PR hebdomadaire de mise à jour des playbooks

## Phase 7 — Multi-chaînes et autonomie

Critère de sortie : chaîne fictive n° 3 ajoutée sans toucher au code ; le contrôle de diversité bloque les quasi-doublons des fixtures.

- [ ] Ajout d'une chaîne par fichier de configuration (bible, watchlist, voix, style)
- [ ] Contrôle de diversité inter-chaînes
- [ ] Échelle d'autonomie du §11 (retrait mesuré des portes G1/G2)
- [ ] Alertes (n8n, e-mail ou Telegram) ; tableau de bord coûts et KPIs
