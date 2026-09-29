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

- Python 3.12, `uv`, Pydantic v2, SQLAlchemy Core (dépendance directe ; elle venait de DBOS, sorti des dépendances d'exécution : ADR-001 décision 12), ruff, mypy strict sur `studio/`.
- Aucun appel réseau dans les tests unitaires ; les tests Postgres sont marqués `postgres` et lisent `STUDIO_TEST_PG_URL` ; les tests qui lancent ffmpeg sont marqués `media`.
- Un mock porte `mock` dans son identifiant, sa spec et chaque rapport.
- Aucun secret dans le code, les fixtures ou les logs.
- Les règles éditoriales privées (grille, seuils, formules) ne sont pas codées en dur : elles viendront de `knowledge/` en phase 2.

## Contrat de `make e2e-dry`

Commande : `uv run studio run --channel <id|lettre> --format <short|long> --dry-run --out <dossier> [--seed N] [--run-id ID]`, lancée par `make e2e-dry` pour `channel-a` en `short` puis en `long` dans `var/e2e/`. Sans `--dry-run` la commande refuse (code 2) : la phase 1 ne contient que des mocks.

Codes de sortie : 0 terminé · 1 échec (dont `StateBusy` : un autre `studio run` tient le dossier d'état) · 2 usage · 3 une porte tient un refus (`GateRejected`, y compris une approbation révoquée après coup) · 75 pause jusqu'à la réinitialisation du quota Claude (`RunPaused`, `EX_TEMPFAIL` : relancer la même commande après l'heure affichée).

Graphe de démonstration (tout adaptateur est un mock). Il se construit en deux temps, parce que sa forme dépend du script (une voix et un plan par scène) : `front_steps` (`idea` → `package` → `g1` → `script`) puis `production_steps(script)`. Les deux temps utilisent les mêmes noms, versions et paramètres : la seconde passe réutilise les sorties de la première.

| Étape | Ressource | Entrées | Rôle |
|---|---|---|---|
| `idea` | llm | — | idée (agent `strategist`, sortie validée contre le schéma `Idea`) ; l'usage de l'appel (jetons) est rendu comme mesure |
| `package` | llm | `idea` | titres, miniatures, première image (agent `packaging_director`, schéma `Package`) |
| `g1` | human | `package` | porte G1 sur le hash du package |
| `script` | llm | `idea`, `package`, `g1` | scènes au format du skill (agent `head_writer`), converties par `studio/scenario/skill_json.py` |
| `timeline` | cpu | `script` | durées de scène et durée totale |
| `line_SNN` | cpu | `script` | ce que la voix lit : texte, ton, durée de la scène |
| `visual_SNN` | cpu | `script` | ce que le plan montre : prompt visuel, durée de la scène |
| `voice_SNN` | gpu | `line_SNN` | voix off de la scène (`MockTextToSpeech`) |
| `shot_SNN` | gpu ou cpu | `visual_SNN` | brouillon au quart de la définition → critique visuelle mock → final ; 2 tentatives au plus ; technique par scène (Blender, 2.5D, vidéo générée, motion) |
| `music` | gpu | `timeline` | lit musical (mock) |
| `mix` | cpu | `timeline`, `voice_*`, `music` | voix calées sur leur scène, lit −18 dB sous la voix, loudnorm deux passes vers −14 LUFS / −1 dBTP |
| `assemble` | cpu | `mix`, `shot_*` | concaténation à 30 i/s constants, multiplexage de la piste audio |
| `qa` | cpu | `assemble`, `timeline` | `studio/media/qa.check_render` (résolution, cadence, durée, pistes, loudness, true peak) : aucun défaut attendu |
| `candidate` | cpu | `script`, `assemble`, `qa` | le **candidat de publication** (`PublicationCandidate`) : ce que la plateforme montrera (titre, description, vie privée, drapeaux de divulgation), lié au hash du rendu, à la chaîne et à la vidéo ; vérifie le hash du rendu avant de le nommer |
| `compliance` | human | `candidate` | verdict conformité sur le hash du candidat : l'agent (`MockComplianceOfficer` applique des contrôles réels sur le script, le rapport QA et le candidat) **et** l'humain ; un refus de l'un ou de l'autre bloque ; répondu **avant** G2 et sans demander l'humain si l'agent refuse |
| `g2` | human | `candidate` | porte G2 sur le hash du candidat |
| `publish_plan` | cpu | `candidate`, `assemble`, `qa`, `compliance`, `g2` | libère le candidat approuvé à l'octet près, après avoir refusé tout défaut QA, un candidat qui nomme un autre rendu et un rendu dont les octets ne correspondent plus à leur hash ; `requires_approval` = conformité + G2 sur le candidat, `publishes` : le graphe refuse à sa construction une étape de publication sans ces deux garde-fous ; **aucun appel réseau** |

Lignes de cache. `line_SNN` et `visual_SNN` extraient du script ce dont la voix et le plan dépendent, sans l'heure de début de la scène. Une clé d'étape suit le contenu de ses entrées (coupure précoce) : retoucher les mots d'une scène à longueur égale relance le script, les extractions, **une** voix, le mixage, l'assemblage, la QA, le candidat et les portes ; aucun plan, aucune musique, aucune autre voix. Le test `test_editing_the_words_of_one_scene_recomputes_one_voice_and_no_shot` le prouve. Les paramètres d'un plan nomment les seuls adaptateurs qui le fabriquent et le jugent (`Production.shot_adapter_ids`) : changer de LLM ne relance pas un plan. La sortie d'une porte est un JSON canonique sans date ni note : les clés en aval d'une porte sont les mêmes d'une exécution à l'autre.

Portes. Chaque porte relit sa décision à chaque tour (une approbation révoquée arrête la vidéo) ; une décision porte son mode (`mock`) et ne s'applique qu'à une exécution du même mode ; les décisions mock ne remplacent jamais une décision réelle. Le manifeste est recoupé avec le magasin.

Un seul processus par dossier d'état : `state/.run.lock`. Le propriétaire libère au démarrage les réservations, les fichiers de travail et les JSON à demi écrits d'un prédécesseur tué (`SIGKILL`). Sa reprise saute les étapes finies.

Les mocks se choisissent un sujet selon le concept de la chaîne (ADR-005) : A parle de reconstruction d'ouvrages, B d'échelles de temps. Le texte est inventé, sans prétention factuelle. Le LLM mock rapporte un usage scripté (environ quatre caractères par jeton) pour faire tourner la comptabilité des jetons.

Sorties dans `<dossier>/<channel>/<format>/` (le dossier est résolu en chemin absolu). **Chaque JSON dit `mock`** (`"mock": true` à la racine) :
- `report.json` : `run_id`, `channel_id`, `format`, `dry_run`, `mock` (true), `adapters` (ids, tous contenant `mock`), `idea_id`, `executed`, `skipped`, `waiting`, `rounds`, `render_key`, `render_path`, `candidate_key`, `duration_expected_s`, `scene_count`, `qa_defects`, `publication`, `costs` (total par type, jetons compris), `step_count`, `manifest_mock`. Le rapport d'une exécution précédente est supprimé au démarrage : un `report.json` présent décrit la dernière exécution terminée ;
- `manifest.json` (`RunManifest`, réécrit après chaque tour, y compris quand un tour échoue : les sorties résolues restent verrouillées) ;
- `costs.json` : `{"mock": true, "dry_run": true, "note": …, "entries": [...]}` ; chaque entrée du registre porte `"mock": true` (secondes GPU = secondes de processeur d'un substitut, appels Claude scriptés : jamais une dépense réelle) ;
- `script.scenes.json` : le script re-sérialisé au format du skill, marqué `mock` à sa racine ;
- `render.mp4` : copie du rendu du magasin, jamais un lien ; son hash est vérifié avant la livraison.
- L'état (index SQLite, registre des coûts, décisions, fichiers adressés par contenu, fichiers de travail) vit dans `<dossier>/state/`.

Une seconde exécution sur le même dossier donne `executed == []`, le même `render_key` et le même fichier. Un `manifest.json` d'un autre `run_id` est refusé (`StudioError`), jamais écrasé.
