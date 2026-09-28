# Conception de la phase 1 — squelette, contrats, mocks

> Version 1 · 2026-09-28 · Référence : MISSION §6 et §9 phase 1, ADR-001 (architecture), ADR-002 (fournisseurs).
> Ce document fixe la répartition des modules et les invariants à prouver par des tests. Les interfaces font foi : `studio/core/interfaces.py`, `studio/adapters/base.py`, `studio/adapters/llm_base.py`, `studio/domain/`.

## Critère de sortie (MISSION §9)

`make verify-phase-1` sort en 0 seulement si :
1. `make test` est vert et la couverture est ≥ 80 % sur le cœur (`studio/domain`, `studio/core`, `studio/scenario`, `studio/pipeline`) ;
2. `make e2e-dry` produit, via les mocks, un Short 1080×1920 et un long 1920×1080, chacun avec son manifeste et son registre de coûts ;
3. `ffprobe` valide durée, résolution, cadence constante et présence des pistes vidéo et audio ;
4. une seconde exécution de `make e2e-dry` ne régénère aucun artefact (0 étape exécutée) ;
5. chaque rapport et chaque manifeste produit avec un mock porte le mot `mock`.

## Carte des modules

| Module | Rôle | Invariants à tester |
|---|---|---|
| `studio/domain/` (fait) | contrats Pydantic v2 figés, stricts | refus des champs inconnus ; timeline contiguë ; décision de porte liée au hash |
| `studio/core/hashing.py` (fait) | clé d'étape | même entrée → même clé ; toute entrée modifiée → clé différente |
| `studio/core/artifacts.py` | stockage adressé par contenu + index SQL (SQLAlchemy Core, SQLite ou Postgres) | déduplication ; « premier écrit gagne » sur `commit_step_output` sous concurrence ; épinglage ; purge qui épargne les épinglés |
| `studio/core/costs.py` | registre des coûts, plafonds, réservations atomiques | 8 threads concurrents ne dépassent jamais un plafond ; `settle` remplace la réservation ; `reap_expired` libère après un crash |
| `studio/core/queue.py` | file de tâches SQL + verrou global par clé d'étape | une clé d'étape n'est enfilée qu'une fois toutes files confondues ; priorité ; bail expiré → re-claimable avec `attempt + 1` ; `SKIP LOCKED` sur Postgres |
| `studio/core/scheduler.py` | répartiteur GPU (affinité de modèle, charge, préemption des brouillons) | un final passe avant un brouillon ; affinité respectée ; pas de brouillon démarré si un final attend |
| `studio/core/graph.py` | planificateur de graphe adressé par contenu + manifeste verrouillé | ordre topologique ; replay = 0 exécution ; sortie verrouillée réutilisée même si l'étape est non déterministe ; porte humaine = attente ; publication impossible sans verdict conformité + G2 sur le même hash |
| `studio/core/quota.py` | gestionnaire de quota Claude | pause sur `QuotaExhausted`, reprise à `reset_at` ; priorités conformité/scripts > critique > veille ; mode économie |
| `studio/adapters/mock.py` | mocks déterministes de tous les adaptateurs (fichiers réels via ffmpeg) | même graine → mêmes octets ; nom et spec contiennent `mock` |
| `studio/adapters/claude_code.py` | `ClaudeCodeRunner` (`claude -p`) | jamais `--bare` ; refuse si `ANTHROPIC_API_KEY` est définie ; parse la sortie JSON et l'usage ; une relance bornée si le schéma échoue ; détecte la limite d'usage |
| `studio/adapters/mock_llm.py` | backend LLM de test (réponses enregistrées) | déterministe ; `mock` dans l'id |
| `studio/media/ffmpeg.py`, `studio/media/qa.py` | rendu et contrôles techniques (MISSION §8) | résolution, cadence constante, durée, pistes ; loudness intégrée et true peak mesurés |
| `studio/scenario/skill_json.py` | JSON de scènes du skill (v1.0) ↔ `Script` | aller-retour sans perte (champs inconnus conservés dans `extras`) |
| `studio/schemas/export.py` | export JSON Schema de chaque contrat vers `schemas/` | les schémas versionnés égalent l'export (test de non-régression) |
| `studio/pipeline/` | étapes concrètes du parcours à blanc | voir critère de sortie |
| `studio/cli.py` | `studio run --channel A --format short --dry-run` | codes de sortie ; aucun appel réseau en `--dry-run` |

## Règles communes

- Python 3.12, `uv`, Pydantic v2, SQLAlchemy Core (déjà tiré par DBOS), ruff, mypy strict sur `studio/`.
- Aucun appel réseau dans les tests unitaires ; les tests Postgres sont marqués `postgres` et lisent `STUDIO_TEST_PG_URL` ; les tests qui lancent ffmpeg sont marqués `media`.
- Un mock porte `mock` dans son identifiant, sa spec et chaque rapport.
- Aucun secret dans le code, les fixtures ou les logs.
- Les règles éditoriales privées (grille, seuils, formules) ne sont pas codées en dur : elles viendront de `knowledge/` en phase 2.

## Contrat de `make e2e-dry`

Commande : `uv run studio run --channel <id> --format <short|long> --dry-run --out <dossier>`, lancée par `make e2e-dry` pour `channel-a` en `short` puis en `long` dans `var/e2e/`.

Graphe de démonstration (tout adaptateur est un mock) :

| Étape | Ressource | Rôle |
|---|---|---|
| `idea` | llm | idée (MockLLMRunner, schéma `Idea`) |
| `package` | llm | titres et miniatures (schéma `Package`) |
| `g1` | human | porte G1 sur le package (décision mock) |
| `script` | cpu | script issu d'une fixture au format du skill, via `studio/scenario/skill_json.py` |
| `voice` | gpu | voix off (MockTextToSpeech, une piste par scène, concaténées) |
| `shots` | gpu | un plan par scène selon sa technique (mocks image / vidéo), au format cible |
| `music` | gpu | lit musical (mock) |
| `mix` | cpu | voix + musique sous la voix, loudnorm deux passes vers −14 LUFS / −1 dBTP |
| `assemble` | cpu | concaténation des plans, mise au format, multiplexage audio |
| `qa` | cpu | `studio/media/qa.check_render` : aucun défaut attendu |
| `compliance` | human | verdict conformité sur le hash du rendu (décision mock, jamais contournable) |
| `g2` | human | porte G2 sur le hash du rendu (décision mock) |
| `publish_plan` | cpu | objet `Publication` privé (`contains_synthetic_media` = divulgation du script) ; `requires_approval` = conformité + G2 sur le rendu ; **aucun appel réseau** |

Sorties dans `<dossier>/<channel>/<format>/` :
- `report.json` : `run_id`, `channel_id`, `format`, `dry_run`, `mock` (true), `adapters` (ids, tous contenant `mock`), `executed`, `skipped`, `waiting`, `render_key`, `render_path`, `qa_defects`, `publication`, `duration_expected_s` ;
- `manifest.json` (`RunManifest`), `costs.json` (entrées du registre), `render.mp4`.
Une seconde exécution sur le même dossier donne `executed == []` et le même `render_key`.
