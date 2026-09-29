# Journal de progression

Entrées datées, la plus récente en haut. Chaque affirmation « fait » est suivie de la commande qui le prouve et de sa sortie.

## 2026-09-29 — Session 2 : phase 1 (squelette, contrats, mocks)

### Fait
- **Contrats et schémas** : 16 contrats Pydantic v2 figés et stricts, un JSON Schema par contrat (`schemas/`), mapping sans perte avec le JSON de scènes du skill (fixtures aux contenus inventés).
- **Cœur** (`studio/core`) : magasin d'artefacts adressé par contenu (fichiers + index SQL, premier écrit gagne, épinglage), registre des coûts à plafonds et réservations atomiques à bail (jetons Claude compris, chaque entrée dit si elle mesure un mock), file de tâches SQL avec verrou global par clé d'étape et jeton de fencing, répartiteur GPU (composants prouvés à part, branchés en phase 3), planificateur de graphe avec manifeste verrouillé recoupé avec le magasin et portes relues à chaque tour, décisions de porte en SQL, gestionnaire de quota Claude.
- **Adaptateurs et média** : `ClaudeCodeRunner` (`claude -p`, jamais `--bare`, refuse `ANTHROPIC_API_KEY`), LLM mock, mocks de tous les protocoles qui écrivent de vrais fichiers, `studio/media` (ffmpeg déterministe, QA §8, `media_fingerprint()`).
- **Parcours à blanc** (`studio/pipeline`, `studio/cli.py`) : idée → packaging → G1 → script → une voix et un plan par scène → musique → mixage −14 LUFS → assemblage → QA → **candidat de publication** → conformité (agent et humain) → G2 → plan de publication privé, sans réseau. `studio run --channel A --format short --dry-run`.
- **Essai DBOS 3.1.0** (19 tests, vrais processus, Postgres) puis **ADR-001 révisé** : file tirée maison retenue, DBOS mis de côté (décision 12), décisions 13 à 20, table pannes → tests (60 tests cités, existence vérifiée).
- **Outillage** : `make doctor-execution`, porte de phase 1 qui mesure elle-même, CI qui la lance, `dbos` dans le groupe `dev`, `sqlalchemy` déclaré.
- **Volume** : `studio/` ≈ 9 500 lignes, `tests/` ≈ 15 500 lignes, 1 351 tests.

### Revue `critic` du 2026-09-29 : refusée, corrigée
La 1re revue (HEAD `ef03588`, 3 h, 181 appels d'outils) a reproduit la porte (5/5) puis **refusé** la phase : 2 bloquants, 10 importants, 7 mineurs. Elle avait raison sur les deux bloquants.

| Constat | Ce que la revue a démontré | Correction | Preuve (mutant correspondant tué) |
|---|---|---|---|
| B1 conformité contournable | une v2 du script coupait la divulgation IA ; le rendu restait identique, donc les décisions (sur le hash du rendu) servaient et le plan devenait « non synthétique » sans que personne soit sollicité | `PublicationCandidate` : la conformité et G2 jugent le hash de ce que la plateforme montrera, lié à la chaîne et à la vidéo ; `publish_plan` le libère à l'octet près | `test_a_title_or_a_disclosure_changed_after_the_approvals_needs_new_approvals` |
| B2 `costs.json` sans `mock` | 0 occurrence du mot dans `costs.json` ; des appels au LLM mock présentés comme mesurés | `costs.json` enveloppé, `CostEntry.mock`, `script.scenes.json` marqué, la porte lit les quatre JSON | `test_every_json_file_of_a_dry_run_says_mock` |
| I1 approbations mock valides en « réel » | `Runner.run(dry_run=False, mock=False)` publiait avec les décisions du pilote mock | `GateDecision.mock` vérifié à chaque lecture ; un graphe qui contient une étape mock refuse `mock=False` ; le pilote dérive le mode des adaptateurs | `test_a_decision_applies_only_to_a_run_of_its_own_mode` |
| I2 ordre conformité avant G2 non prouvé | un mutant (tri inversé) laissait la suite verte | le test exige qu'aucun humain ne soit sollicité et qu'aucune décision G2 existe | `test_the_compliance_officer_blocks_a_script_with_an_open_loop_and_no_human_is_asked_at_g2` |
| I3 aucun nettoyeur ne tourne | 14 `SIGKILL` pendant une étape GPU bloquaient la vidéo pour de bon (988 s GPU réservées par arrêt, plafond 14 400) | `reap_expired` au début de chaque tour ; le propriétaire du dossier libère tout, vide `state/tmp`, retire les JSON à demi écrits | `test_repeated_kills_during_gpu_steps_leave_no_reservation_and_the_video_still_finishes` |
| I4 la porte croit le rapport | une variante qui retire la dernière scène du rendu passait 5/5 | durée = somme des scènes du script, loudness et crête mesurées par la porte, sha256, longueurs des pistes, instantané de l'état au rejeu, `mock` partout ; `check_e2e`, `check_render`, `check_lint` testés | `tests/tools/test_verify_phase1.py` |
| I5 la QA ne bloque pas | un défaut QA + un officier qui approuve donnaient un plan | `publish_plan` refuse tout défaut QA, un autre rendu, un rendu dont les octets ont changé | `test_the_publication_plan_refuses_a_render_with_technical_defects_whoever_approved_it` |
| I6 révocation, corruption, manifeste | G2 révoqué : la porte verrouillée ne relisait pas ; objet du magasin corrompu livré ; manifeste édité : la vidéo B publiait le rendu de A | portes relues à chaque tour (code 3, verrous retirés) ; hash vérifié à la livraison et à la publication ; verrou recoupé avec le magasin (`ManifestMismatch`) | `test_a_revoked_approval_stops_the_replay_with_a_rejection_and_leaves_no_report`, `test_a_stored_render_rotted_in_place_is_never_delivered`, `test_a_manifest_edited_to_lock_another_render_is_refused` |
| I7 file et verrou d'étape non branchés ; deux `studio run` concurrents | 5 appels Claude facturés au lieu de 3 ; faux refus en code 3 (course sur la lecture de décision) | verrou exclusif du dossier d'état (`StateBusy`) ; course corrigée (un refus n'est conclu que sur une décision qui ne l'approuve pas) ; l'ADR dit « composant prouvé à part, intégration en phase 3 » | `test_a_second_run_on_a_folder_another_process_owns_is_refused_not_run_in_parallel` |
| I8 jetons non comptés | `result.usage` jeté | une étape rend l'usage de l'appel comme mesure, l'exception d'un appel refusé aussi | `test_the_tokens_of_the_claude_calls_are_recorded_from_their_usage` |
| I9 conformité automatisable | agent `APPROVE` + humain en attente = approuvé | l'agent ET l'humain, le refus de l'un bloque (MISSION §11) | `test_gate_semantics`, `test_the_compliance_decision_needs_the_agent_and_the_human` |
| I10 structure du skill publique | le schéma de scènes est dans le dépôt public depuis `84f9469` | **décision humaine** : NEEDS_HUMAN H1 | (ne se corrige pas dans le code) |
| m1 à m7 | preuve périmée, fixtures transcrites, `/tmp` pollué, clés d'étape horodatées, docs périmées, liste de faux jetons, « jamais » trop fort | sortie de porte déterministe, `state/tmp`, docs et ADR corrigés, faux jetons construits à l'exécution, H14 pour l'enregistrement de vraies sorties | voir ADR-001 décisions 14, 15, 20 |

**Limites reconnues, dites dans l'ADR** : la file, le répartiteur et le verrou d'étape ne sont pas branchés au `Runner` (phase 3) ; « les étapes GPU continuent pendant la pause de quota » n'est pas prouvé ; les fixtures de `ClaudeCodeRunner` sont transcrites, pas enregistrées (H14) ; la structure du skill est déjà publique (H1).

### Défauts trouvés pendant l'intégration et corrigés
1. Les fichiers écrits par lot étaient exclus par `.git/info/exclude` : ruff les ignorait. Une fois visibles, 8 constats, corrigés.
2. La clé d'un plan GPU portait l'id du LLM : changer de LLM relançait tous les plans. Le test « retoucher une scène » l'a révélé ; les paramètres d'un plan ne nomment plus que les adaptateurs qui le fabriquent.
3. Le rendu livré était un lien dur vers le magasin : c'est une copie atomique, vérifiée par hash.
4. `sqlalchemy` n'était qu'une dépendance implicite de `dbos`.
5. La porte de phase 1 cherchait « N skipped » dans la dernière ligne de pytest, absente avec `-qq` : elle lit le rapport JUnit.
6. Les jetons factices des tests faisaient tomber la porte de phase 0 à 12/14 : liste exacte de deux jetons dans l'outil, et plus aucun jeton dans l'arbre.
7. Mutation testing du module média par son agent : 56 mutants sur 56 tués. Mutation testing de ces corrections : **19 mutants sur 19 tués**, chacun par le test prévu.

### Preuves
```
$ STUDIO_TEST_PG_URL=postgresql+psycopg://postgres@localhost:5432/studio_lead make verify-phase-1
✓ Lint : ruff + mypy strict
✓ Tests verts, aucun ignoré, couverture ≥ 80 % sur le cœur
    · pytest : 1351 tests, 0 ignoré(s), 0 échec(s), 0 erreur(s)
    · couverture du cœur : 99.0 % (2876/2906 lignes)
✓ e2e-dry channel-a short : rendu 1080×1920, manifeste, coûts, mock, replay
    · render.mp4 : 1080×1920 @ 30/1, 23.30 s, -14.0 LUFS, -11.4 dBTP
    · replay : 37 étapes réutilisées, 0 exécutée, état inchangé
✓ e2e-dry channel-a long : rendu 1920×1080, manifeste, coûts, mock, replay
    · render.mp4 : 1920×1080 @ 30/1, 46.50 s, -14.0 LUFS, -10.8 dBTP
    · replay : 61 étapes réutilisées, 0 exécutée, état inchangé
✓ CI GitHub Actions présente

verify-phase-1 : 5/5 contrôles OK        (9 min 34 s)

$ make verify-phase-0
verify-phase-0 : 13/14 contrôles OK, 1 en échec        # seul échec : outliers mesurés (NEEDS_HUMAN H0)
```
Les durées, loudness et crêtes ci-dessus sont mesurées par la porte elle-même (somme des scènes du script, ffmpeg EBU R128), pas lues dans le rapport. Preuves ciblées : `tests/integration/test_e2e_dry.py` (31 tests : rejeu à zéro exécution, retouche d'une scène = une voix et aucun plan, refus aux portes, divulgation modifiée après approbation, révocation, corruption, manifeste échangé, deux processus, arrêts brutaux répétés, pause puis reprise sur limite d'usage, aucun appel réseau tenté).

### État
Phase 1 : critères de sortie remplis en local, 1re revue `critic` refusée puis corrigée ; **2e revue à passer**. Phase 0 : **ouverte** (H0, clé d'API YouTube ; H1, dépôt public).

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
