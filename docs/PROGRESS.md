# Journal de progression

Entrées datées, la plus récente en haut. Chaque affirmation « fait » est suivie de la commande qui le prouve et de sa sortie.

## 2026-09-29 — Session 2 : phase 1 (squelette, contrats, mocks)

### Fait
- **Contrats et schémas** : 15 contrats Pydantic v2 figés et stricts, un JSON Schema par contrat (`schemas/`), mapping sans perte avec le JSON de scènes du skill (fixtures aux contenus inventés).
- **Cœur** (`studio/core`) : magasin d'artefacts adressé par contenu (fichiers + index SQL, premier écrit gagne, épinglage), registre des coûts à plafonds et réservations atomiques à bail, file de tâches SQL avec verrou global par clé d'étape et jeton de fencing, répartiteur GPU (affinité de modèle, finaux avant brouillons), planificateur de graphe avec manifeste verrouillé et portes liées au hash, décisions de porte en SQL, gestionnaire de quota Claude.
- **Adaptateurs et média** : `ClaudeCodeRunner` (`claude -p`, jamais `--bare`, refuse `ANTHROPIC_API_KEY`), LLM mock, mocks de tous les protocoles qui écrivent de vrais fichiers, `studio/media` (ffmpeg déterministe, QA §8, `media_fingerprint()`).
- **Parcours à blanc** (`studio/pipeline`, `studio/cli.py`) : idée → packaging → G1 → script → une voix et un plan par scène → musique → mixage −14 LUFS → assemblage → QA → conformité → G2 → plan de publication privé, sans réseau. `studio run --channel A --format short --dry-run`.
- **Essai DBOS 3.1.0** (19 tests, vrais processus, Postgres) puis **ADR-001 révisé** : file tirée maison retenue, DBOS mis de côté (décision 12), décisions 13 à 19, table scénarios de panne → tests (33 tests cités, existence vérifiée).
- **Outillage** : `make doctor-execution`, porte de phase 1 (aucun test ignoré, Postgres et ffmpeg exigés), CI qui lance la porte, `dbos` déplacé dans le groupe `dev` et `sqlalchemy` déclaré (elle venait de `dbos`).
- **Volume** : 18 commits, `studio/` 9 175 lignes (35 fichiers), `tests/` 14 442 lignes (26 fichiers de test).

### Défauts trouvés pendant l'intégration et corrigés
1. Les fichiers écrits par lot étaient exclus par `.git/info/exclude` : ruff les ignorait. Une fois visibles, 8 constats (imports inutilisés, ligne trop longue), corrigés.
2. La clé d'un plan GPU portait l'id du LLM : changer de LLM relançait tous les plans. Le test « retoucher une scène » l'a révélé ; les paramètres d'un plan ne nomment plus que les adaptateurs qui le fabriquent (`Production.shot_adapter_ids`).
3. Le pilote demandait G2 à l'humain après un refus de conformité ; la conformité est répondue d'abord et arrête la vidéo.
4. Le rendu livré était un lien dur vers le magasin : un outil qui l'éditerait sur place corromprait l'artefact. C'est une copie atomique.
5. Un `manifest.json` d'un autre run plantait avec une trace ; c'est une erreur claire, jamais un écrasement.
6. `sqlalchemy` n'était qu'une dépendance implicite de `dbos`.
7. La porte de phase 1 cherchait « N skipped » dans la dernière ligne de pytest, absente avec `-qq` : elle lit maintenant le rapport JUnit (`tests/tools/test_verify_phase1.py`).
8. Les jetons factices des tests de rédaction faisaient tomber la porte de phase 0 à 12/14 : liste exacte de deux jetons, comparés comme jetons entiers, dans l'arbre et dans l'historique.
9. Mutation testing du module média par son agent : 56 mutants sur 56 tués ; un mutant (`timeout` ignoré) faisait pendre un test, qui a reçu une échéance propre.

### Preuves
```
$ STUDIO_TEST_PG_URL=postgresql+psycopg://postgres@localhost:5432/studio_lead make verify-phase-1
✓ Lint : ruff + mypy strict
✓ Tests verts, aucun ignoré, couverture ≥ 80 % sur le cœur
    · pytest : 1279 tests, 0 ignoré(s), 0 échec(s), 0 erreur(s)
    · couverture du cœur : 99.1 % (2728/2754 lignes)
✓ e2e-dry channel-a short : rendu 1080×1920, manifeste, coûts, mock, replay
    · render.mp4 : 1080×1920 @ 30/1, 23.30 s
    · replay : 36 étapes réutilisées, 0 exécutée
✓ e2e-dry channel-a long : rendu 1920×1080, manifeste, coûts, mock, replay
    · render.mp4 : 1920×1080 @ 30/1, 46.50 s
    · replay : 60 étapes réutilisées, 0 exécutée
✓ CI GitHub Actions présente

verify-phase-1 : 5/5 contrôles OK        (7 min 47 s)

$ make e2e-dry            # 1re exécution
channel   channel-a  format short  run dry-channel-a-short-0  [mock, dry-run]
steps     36 executed, 0 reused, 0 waiting
channel   channel-a  format long  run dry-channel-a-long-0  [mock, dry-run]
steps     54 executed, 6 reused, 0 waiting      # 6 voix identiques à celles du Short : réutilisées

$ make e2e-dry            # rejeu
steps     0 executed, 36 reused, 0 waiting
steps     0 executed, 60 reused, 0 waiting

$ ffprobe var/e2e/channel-a/short/render.mp4
stream|codec_name=h264|codec_type=video|width=1080|height=1920|r_frame_rate=30/1|avg_frame_rate=30/1
stream|codec_name=aac|codec_type=audio|sample_rate=48000|channels=2
format|duration=23.300000
$ ffprobe var/e2e/channel-a/long/render.mp4
stream|codec_name=h264|codec_type=video|width=1920|height=1080|r_frame_rate=30/1|avg_frame_rate=30/1
stream|codec_name=aac|codec_type=audio|sample_rate=48000|channels=2
format|duration=46.500000

$ make verify-phase-0
verify-phase-0 : 13/14 contrôles OK, 1 en échec        # seul échec : outliers mesurés (NEEDS_HUMAN H0)

$ make doctor-execution   # sur la VM cloud, sans GPU : les trois manques attendus
  ✗ nvidia-smi absent : pilote NVIDIA non installé
  ✗ le démon Docker ne répond pas (docker info)
  ✗ CLAUDE_CODE_OAUTH_TOKEN absent : les agents `claude -p` ne pourraient pas s'authentifier sur l'abonnement
```
Preuves ciblées : `tests/integration/test_e2e_dry.py` (rejeu à zéro exécution et même fichier, retouche d'une scène = une voix et aucun plan, refus aux portes G1, conformité et G2, pause puis reprise sur limite d'usage, **arrêt brutal (SIGKILL) au milieu d'une vidéo puis reprise sans refaire les étapes finies ni corrompre un objet du magasin**, aucun appel réseau tenté).

### État
Phase 1 : critères de sortie remplis en local ; revue `critic` à suivre. Phase 0 : **ouverte** (H0, clé d'API YouTube ; H1, dépôt public).

## 2026-09-28 — Session 1 (fin) : contre-revue `critic` et corrections

### Fait
- Contre-revue `critic` (opus) : **acceptée avec réserves**. Elle a démontré que 12 lignes d'outliers tapées à la main faisaient passer la porte à 14/14 (R1), que des notes et des ADR creux passaient encore (R2), et relevé des trous dans l'ADR-001 (R3), une note modèles contradictoire (R4) et des sources non ouvertes (R5).
- Corrections :
  - R1 : `tools/outliers.py --save` garde les mesures brutes ; la porte recalcule chaque ratio à partir de ces fichiers ; `make verify-phase-0-online` re-mesure par l'API avant toute clôture. L'attaque a été rejouée sur une copie du dépôt : les lignes forgées sont écartées ;
  - R2 : tableau de constats d'au moins 3 lignes ; nombre minimal de mots par section ; une source ne compte que si elle appuie une ligne de tableau ; ADR répétitifs ou sans renvoi `note.md [Sn]` refusés ;
  - R3 : l'ADR-001 ajoute un verrou global par étape, un identifiant d'exécuteur DBOS par worker, l'interruption effective des étapes GPU et un nettoyeur des réservations de budget ;
  - R4 : PuLID et LTX-2 sont corrigés dans le corps de la note, et la dépendance InsightFace est sourcée sur `pulid/pipeline.py` (fichier vérifié) ;
  - R5 : la source EUR-Lex non ouverte est retirée ; le prix d'une carte passe en « non sourcé » ;
  - R6 : médiane nulle, arrondi du ratio et « | » dans un nom de chaîne sont gérés ;
  - R7 : vidéo générative à 260 GPU-s/s au central, déduit du seul repère publié.
- Préalablement : l'affirmation TechCrunch sur le comptage des vues (17/08/2026) a été ouverte et vérifiée.
- Non corrigeable par moi : l'historique git public contient encore les brouillons retirés (NEEDS_HUMAN H1).

### Preuves
```
$ make test
69 passed in 0.42s

$ make lint
All checks passed!

$ make verify-phase-0
verify-phase-0 : 13/14 contrôles OK, 1 en échec

$ python3 tools/verify_phase0.py --online   # sans clé
    - re-mesure API : --online exige YOUTUBE_API_KEY
```
État : phase 0 **ouverte**. Seul critère non rempli : la preuve de demande mesurée (NEEDS_HUMAN H0). Clôture = `make verify-phase-0-online` à 14/14, puis revue `critic` finale.

## 2026-09-28 — Session 1 (suite) : recherches livrées, revue `critic`, corrections

### Fait
- 9 notes de recherche livrées : `platform-policies`, `apis`, `video-image-models`, `audio-models`, `craft`, `economics`, `infra`, `channel-concepts` (fusion de deux lots).
- ADR-001 à ADR-004, `docs/COST_MODEL.md` (généré par `tools/cost_model.py`), `tools/outliers.py` (mesure des outliers via l'API YouTube Data).
- Revue `critic` (opus) : **refusée**. 3 bloquants (preuves absentes de PROGRESS ; vérificateur permissif, démontré par des notes creuses qui passaient ; seuil de 8 sources datées atteint par remplissage) et 8 majeurs. Corrections :
  - vérificateur v2 : ne compte que les sources datées **et citées** ; constats sourcés ou étiquetés ; « officiel » refusé pour forums et wikis ; sources non ouvertes refusées ; ADR aux sous-sections non vides et références `note.md [Sn]` résolues ; tables de coût identiques à la sortie du script ; outliers comptés seulement s'ils sont mesurés par l'API avec un ratio cohérent ; historique git scanné pour les secrets ;
  - faits faux corrigés : Digital Omnibus (règlement (UE) 2026/1744, délai art. 50(2) au 02/12/2026 ; vérifié sur Cuatrecasas) ; RPM « France éducation 12 $ » requalifié (panel sans pays) ; PuLID refusé (dépendance InsightFace) ; loi 2023-451 limitée à l'influence rémunérée ;
  - ADR-001 révisé : DBOS (fonctions de file vérifiées dans sa doc) + scénarios de panne traités ; ADR-002 : PuLID refusé, LTX-2 hors shortlist, seconde famille vidéo ; ADR-004 : médiane à âge comparable ;
  - modèle de coût : origines honnêtes (valeurs choisies marquées HC), défavorable vidéo à 800 GPU-s/s, temps humain avec rejets G1 (17 min par long au central, au-dessus du plafond de 15 min : constat), postes non chiffrés listés ;
  - dépôt public : brouillons `_work/` (extraits du skill privé) retirés et ignorés ; restent dans l'historique (NEEDS_HUMAN H1).
- Incident de méthode tracé (NEEDS_HUMAN H13) : un sous-agent a lu par script des pages YouTube ; données non comptées, règle ajoutée au rôle `researcher`.

### Preuves (relancées après corrections)
```
$ make doctor
doctor : OK

$ make test
64 passed in 0.37s

$ make lint
All checks passed!

$ python3 tools/outliers.py video dQw4w9WgXcQ   # sans clé : refus propre
YOUTUBE_API_KEY absente : voir docs/NEEDS_HUMAN.md (H0).
exit=2

$ make verify-phase-0
✓ Fichiers d'état (MISSION, CLAUDE, PLAN, PROGRESS, DECISIONS, NEEDS_HUMAN)
✓ Sous-agents de construction (MISSION §10)
✓ Note de recherche platform-policies.md
✓ Note de recherche apis.md
✓ Note de recherche video-image-models.md
✓ Note de recherche audio-models.md
✓ Note de recherche craft.md
✓ Note de recherche economics.md
✓ Note de recherche infra.md
✗ Concepts de chaînes (6 classés, ≥ 2 outliers chacun)
✓ ADR-001 et ADR-002 complets, sourcés, sans TODO
✓ docs/COST_MODEL.md (coût par format, hypothèses explicites)
✓ docs/PLAN.md détaillé (phases 0-7, tâches cochables)
✓ Aucun secret ni fichier .env versionné (MISSION §3.7, §12)
verify-phase-0 : 13/14 contrôles OK, 1 en échec
```
Seul échec restant : la preuve de demande mesurée (bloquée par NEEDS_HUMAN H0, clé `YOUTUBE_API_KEY`).

## 2026-09-28 — Session 1 : lancement de la phase 0

### Fait
- `docs/MISSION.md` enregistré mot pour mot, commit `docs: mission initiale` (c77e887).
  Preuve : `sha256sum docs/MISSION.md` → `45eb93fad125d40b…` (217 lignes).
- Skill `scenariste-youtube` trouvé dans la session et lu (36 640 octets). **Non copié** dans le dépôt : le dépôt est public (NEEDS_HUMAN H1).
- Format des sous-agents vérifié dans la documentation officielle (code.claude.com/docs/en/sub-agents, consultée le 2026-09-28) :
  champs `name`, `description` obligatoires ; `tools`, `model` (`sonnet`, `opus`, `haiku`, `fable`, ID complet ou `inherit`) facultatifs.
  9 fichiers créés ; frontmatter validé par un parseur YAML.
- Écarts relevés dans l'outillage : `claude --help` (v2.1.283) n'affiche pas `--max-turns` ; `--json-schema` existe ; `--bare` n'utilise pas l'auth OAuth. Vérification détaillée confiée à `docs/research/apis.md`.
- `tools/verify_phase0.py` (porte de phase 0, stdlib) + `tools/doctor.py` + 22 tests.
- 9 recherches lancées en parallèle (rôle `researcher`, modèle sonnet) : platform-policies, apis, video-image-models, audio-models, craft, economics, infra, concepts lot A (C01-C06), concepts lot B (C07-C12).
  Les définitions `.claude/agents/` créées pendant la session ne sont pas encore chargées : les recherches tournent sur l'agent générique avec le rôle `researcher` injecté dans la consigne.
- Paramètres du §0 vides → hypothèses prudentes dans `docs/PARAMETERS.md`, actions dans `docs/NEEDS_HUMAN.md` (H1-H12).

### Preuves
```
$ make doctor
  · claude: présent
  · ffmpeg: absent (requis plus tard sur la machine GPU)
  · ffprobe: absent (requis plus tard sur la machine GPU)
  · docker: présent
  · nvidia-smi: absent (requis plus tard sur la machine GPU)
  · CLAUDE_CODE_OAUTH_TOKEN: absent (requis sur la machine d'exécution, phase 2)
doctor : OK

$ make test
22 passed in 0.23s

$ make lint
All checks passed!

$ make verify-phase-0   # attendu en échec tant que les notes et ADR ne sont pas livrés
verify-phase-0 : 2/13 contrôles OK, 11 en échec
```
