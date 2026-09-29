# CLAUDE.md — Studio vidéo autonome

Ce dépôt construit le logiciel d'un studio vidéo automatisé (YouTube long + Shorts, TikTok).
`docs/MISSION.md` fait foi : ne le modifie jamais ; une correction passe par un ADR dans `docs/DECISIONS.md`.

## Début de chaque session (clone neuf)
1. Lire `docs/MISSION.md`, puis `docs/PLAN.md`, la dernière entrée de `docs/PROGRESS.md`, `docs/NEEDS_HUMAN.md`, `docs/PARAMETERS.md`.
2. `make doctor` puis `make test`.
3. Au début de chaque phase : revérifier l'état de l'usage de `claude -p` sur abonnement (page d'aide Anthropic) et le noter dans `docs/research/apis.md`.

## Commandes
| Commande | Rôle |
|---|---|
| `make help` | liste des cibles |
| `make doctor` | santé de l'environnement ; échoue si `ANTHROPIC_API_KEY` est définie |
| `make verify-phase-0` | porte de sortie de la phase 0 (`tools/verify_phase0.py`, stdlib, Python ≥ 3.11) |
| `python3 tools/verify_phase0.py --note docs/research/X.md` | contrôle d'une seule note |
| `make test` / `make lint` / `make fmt` | pytest / ruff + mypy strict (via `uv run --group dev`) |
| `make verify-phase-1` | porte de la phase 1 (`tools/verify_phase1.py`) : lint, suite complète **sans test ignoré** (exige `STUDIO_TEST_PG_URL` et ffmpeg), couverture ≥ 80 % du cœur, `make e2e-dry` lancé deux fois |
| `make e2e-dry` | parcours à blanc par les mocks : un Short et un long dans `var/e2e/` (`uv run studio run --channel a --format short --dry-run --out DIR` ; sortie 0 ok, 1 échec, 2 usage, 3 porte refusée, 4 porte en attente d'un verdict, 75 quota Claude à attendre ; un dossier `var/e2e` d'une version plus ancienne du code est refusé en clair : le supprimer) |
| `make doctor-execution` | santé de la machine GPU (ffmpeg, Docker, 4 cartes, jeton Claude) |
| `make check` | doctor + lint + test : à passer avant toute PR |
| `make verify-phase-0-online` | idem + re-mesure des outliers par l'API : obligatoire avant de clore la phase 0 |
| `python3 tools/outliers.py channel @handle … --save docs/research/outliers/<date>.json` | outliers via l'API YouTube Data ; `--save` garde les mesures brutes que la porte recalcule |
| `python3 tools/cost_model.py` | tables de `docs/COST_MODEL.md` (régénérer après tout changement de paramètre) |

## Carte du dépôt
```
docs/MISSION.md        mission (immuable)
docs/PARAMETERS.md     valeurs en vigueur du §0 (hypothèse / confirmé)
docs/PLAN.md           phases → tâches cochables
docs/PROGRESS.md       journal daté + sorties des commandes de preuve
docs/DECISIONS.md      ADR
docs/NEEDS_HUMAN.md    actions humaines, triées par urgence
docs/COST_MODEL.md     coût par format, plafonds
docs/research/         notes sourcées (_TEMPLATE.md = format imposé ; _work/ = brouillons, ignorés par git)
.claude/agents/        9 sous-agents de construction (MISSION §10)
tools/                 vérificateurs et outillage (stdlib)
tests/                 pytest
studio/                paquet Python 3.12 (phase 1) : domain/ (contrats Pydantic v2 figés), core/ (hachage, magasin d'artefacts, coûts,
                       file SQL, répartiteur GPU, graphe, quota, décisions), adapters/ (interfaces, mocks, ClaudeCodeRunner),
                       media/ (ffmpeg, QA), scenario/ (JSON de scènes du skill), pipeline/ (étapes et pilote du parcours à blanc),
                       schemas/ (export), cli.py, config/channels/*.yaml
schemas/               JSON Schema exportés des contrats (test de non-régression)
tests/                 unit/, integration/ (Postgres, ffmpeg, essai DBOS), tools/, fixtures/, pipeline_fakes.py
nginx/ prod/ www/      AUTRE PROJET (CRM) — ne pas toucher (NEEDS_HUMAN H11)
```
Arrivent en phase 2 : `knowledge/`, `evals/`, `studio/.claude/agents|skills/` (agents runtime).

## Règles non négociables (résumé de MISSION §3, §5, §12)
- **Preuve ou rien** : une tâche est faite quand une commande reproductible le prouve ; sortie collée dans PROGRESS.
- **Mock** : tout mock porte `mock` dans son nom et dans chaque rapport.
- **Faits externes** : source + date + confiance (élevée / moyenne / faible). Aucun chiffre inventé.
- **Aucune génération média distante** : pixels et sons = modèles à poids ouverts locaux ou code de rendu (Blender, Remotion, ffmpeg…). Claude = seul service distant de création, via Claude Code uniquement, jamais par clé API.
- **Secrets** : jamais dans le dépôt ni les logs ; `.env.example` seulement. `ANTHROPIC_API_KEY` ne doit exister nulle part.
- **Conformité** : la porte `compliance_officer` n'est jamais contournable ni automatisable.
- **Langue** : docs et échanges en français ; code, identifiants, prompts de génération en anglais.
- Style d'écriture : pas de définition par contraste (« ce n'est pas X, c'est Y ») ; affirmer directement.

## Notes de recherche (`docs/research/`)
- Format : `docs/research/_TEMPLATE.md`. Sections : Synthèse, Constats, Écarts avec MISSION §4, Questions ouvertes, Sources.
- Table Sources : `ID | Titre | URL | Date source | Consulté | Type | Confiance`.
  Type ∈ officiel, publication, presse, praticien, données. Chaque `[Sn]` cité existe dans la table.
- Critères phase 0 : ≥ 8 sources datées **et citées** par note ; ≥ 3 officielles citées pour `platform-policies.md` et `apis.md`.
- Chaque ligne de « Constats » cite [Sn] ou se déclare « Inférence » / « non trouvé ».
- Une URL citée a été ouverte. Source bloquée ou lue via un résultat de recherche : confiance ≤ moyenne. Non ouverte : retirée.
- « officiel » = plateforme, régulateur, éditeur, fichier de licence ; jamais un forum, une discussion Hugging Face ou Wikipédia.
- Outlier (phase 0) : ratio ≥ 3× contre les 30 vidéos du même format les plus proches en date, publication ≤ 18 mois,
  **recalculé depuis les mesures brutes** `docs/research/outliers/*.json`. Jamais d'accès automatisé à youtube.com (ADR-004).

## ADR (`docs/DECISIONS.md`)
Titre `## ADR-NNN — …` puis `### Statut`, `### Contexte`, `### Options`, `### Décision`, `### Conséquences`,
`### Coût d'un retour arrière`, `### Sources`. Aucun TODO/TBD : l'inconnu devient une hypothèse avec son test.

## Revue `critic` du 2026-09-28 (phase 0)
Refus motivé → corrigé : vérificateur renforcé, faits faux corrigés (Digital Omnibus, RPM France, PuLID),
ADR-001 révisé (DBOS + scénarios de panne). Ne jamais relâcher ces contrôles pour faire passer une porte.

## Fin de phase (procédure fixe)
`make verify-phase-N` → sortie dans PROGRESS → revue `critic` → PR → `/code-review` → merge après accord humain.
Fin de session : résumé ≤ 15 lignes (état de la phase, prochaines tâches, nouvelles entrées NEEDS_HUMAN).

## Git
- Branche de travail imposée par la session : `claude/upbeat-mayer-0q4cyb` (la mission veut une branche par phase : voir NEEDS_HUMAN H12).
- Commits atomiques, messages `type: résumé` (docs, feat, fix, test, chore).
- Push : `git push -u origin <branche>` ; PR uniquement quand la phase est prouvée et que l'humain l'a demandée.

## Sous-agents
- Construction : `.claude/agents/` (architect, researcher, pipeline-engineer, media-engineer, ml-engineer,
  eval-engineer, compliance-reviewer, security-reviewer, critic).
- Les définitions sont chargées au démarrage de la session : dans la session qui les crée ou les modifie,
  déléguer via un agent générique en lui donnant le rôle à jouer (fichier `.claude/agents/<nom>.md`).
- `critic` relit toute déclaration de fin de phase.

## Pièges connus
- **Un test ignoré ne prouve rien.** Les tests `media` (ffmpeg) et `postgres` (`STUDIO_TEST_PG_URL`) s'ignorent sans leur dépendance ;
  `STUDIO_REQUIRE_MEDIA=1` (CI, `make verify-phase-1`) transforme l'absence de ffmpeg en échec, et la porte exige l'URL Postgres.
- **Clés d'étape** : les exécutions `dry_run` et les mocks salent leurs clés (une sortie mock ne sert jamais une exécution réelle).
  Les paramètres d'une étape ne nomment que ce qui peut changer sa sortie : un plan GPU ne porte pas l'id du LLM
  (`Production.shot_adapter_ids`), sinon changer de LLM relancerait des heures de GPU. Le contrat de sortie d'une étape est un paramètre
  (`contract_fingerprint` : empreinte des JSON Schemas) : modifier un contrat modèle change la clé des étapes qui écrivent sous lui, jamais celle d'un plan.
- **Portes de publication** : la conformité et G2 jugent le **candidat de publication** (rendu + titre + description + divulgation + chaîne + vidéo), pas le rendu seul ;
  la conformité exige l'agent **et** l'humain ; une décision porte son mode (`mock`) ; une porte relit sa décision à chaque tour ; une étape `publishes` exige les deux portes (ADR-001 décisions 17 et 20).
- **Un seul `studio run` par dossier d'état** (`state/.run.lock`) ; un processus tué se rattrape au démarrage suivant (réservations, fichiers de travail).
- **File de tâches** : ADR-001 décision 12 : `SqlJobQueue` (tirée, avec fencing), pas DBOS. `dbos` n'est qu'une dépendance de test (essai rejouable).
- **Dépôt public** (2026-09-28) : ne jamais y copier de contenu privé de l'utilisateur (skill `scenariste-youtube`,
  voix, bibles) tant que H1 n'est pas réglé.
- VM cloud : 4 vCPU, 16 Go RAM, pas de GPU, commandes ≤ 10 min. Tout ce qui exige un GPU = mock ici,
  `make gpu-smoke` sur la machine GPU.
- `claude --help` (v2.1.283) n'affiche plus `--max-turns` ; `--json-schema` existe (sortie structurée).
  `--bare` ignore l'auth OAuth et deviendra le défaut de `-p` : `ClaudeCodeRunner` doit s'en protéger (ADR-001).
- Python système = 3.11 ; `uv` fournit 3.12 (`/usr/bin/python3.12`) pour le projet. Le vérificateur de phase 0
  reste en stdlib pour tourner sans installation.
- Machine GPU : 4× RTX 4070 Ti Super 16 Go, Ada sm_89, sans NVLink : pas d'espace VRAM unifié de 64 Go.
- La branche par défaut du dépôt appartient à un autre projet (CRM) : ne pas s'en servir comme base sans accord.
