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
| `make test` / `make lint` / `make fmt` | pytest / ruff (via `uv run --group dev`) |
| `make check` | doctor + lint + test : à passer avant toute PR |

## Carte du dépôt
```
docs/MISSION.md        mission (immuable)
docs/PARAMETERS.md     valeurs en vigueur du §0 (hypothèse / confirmé)
docs/PLAN.md           phases → tâches cochables
docs/PROGRESS.md       journal daté + sorties des commandes de preuve
docs/DECISIONS.md      ADR
docs/NEEDS_HUMAN.md    actions humaines, triées par urgence
docs/COST_MODEL.md     coût par format, plafonds
docs/research/         notes sourcées (_TEMPLATE.md = format imposé ; _work/ = brouillons)
.claude/agents/        9 sous-agents de construction (MISSION §10)
tools/                 vérificateurs et outillage (stdlib)
tests/                 pytest
nginx/ prod/ www/      AUTRE PROJET (CRM) — ne pas toucher (NEEDS_HUMAN H11)
```
Arrivent en phase 1 : `studio/` (paquet Python), `knowledge/`, `evals/`, `studio/.claude/agents|skills/` (agents runtime).

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
- Critères phase 0 : ≥ 8 sources datées par note ; ≥ 3 officielles pour `platform-policies.md` et `apis.md`.
- Une URL n'est citée que si elle a été ouverte pendant la rédaction.

## ADR (`docs/DECISIONS.md`)
Titre `## ADR-NNN — …` puis `### Statut`, `### Contexte`, `### Options`, `### Décision`, `### Conséquences`,
`### Coût d'un retour arrière`, `### Sources`. Aucun TODO/TBD : l'inconnu devient une hypothèse avec son test.

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
- **Dépôt public** (2026-09-28) : ne jamais y copier de contenu privé de l'utilisateur (skill `scenariste-youtube`,
  voix, bibles) tant que H1 n'est pas réglé.
- VM cloud : 4 vCPU, 16 Go RAM, pas de GPU, commandes ≤ 10 min. Tout ce qui exige un GPU = mock ici,
  `make gpu-smoke` sur la machine GPU.
- `claude --help` (v2.1.283) n'affiche plus `--max-turns` ; `--json-schema` existe (sortie structurée).
  `--bare` ignore l'auth OAuth : ne pas l'utiliser pour le studio.
- Python système = 3.11 ; `uv` fournit 3.12 (`/usr/bin/python3.12`) pour le projet. Le vérificateur de phase 0
  reste en stdlib pour tourner sans installation.
- Machine GPU : 4× RTX 4070 Ti Super 16 Go, Ada sm_89, sans NVLink : pas d'espace VRAM unifié de 64 Go.
- La branche par défaut du dépôt appartient à un autre projet (CRM) : ne pas s'en servir comme base sans accord.
