# Journal de progression

Entrées datées, la plus récente en haut. Chaque affirmation « fait » est suivie de la commande qui le prouve et de sa sortie.

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
