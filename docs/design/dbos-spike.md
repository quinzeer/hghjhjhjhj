# Essai DBOS demandé par ADR-001

> Version 2 · 2026-09-28 · DBOS Transact **3.1.0** (MIT, installé dans `.venv`) · Postgres local · Python 3.12.
> Tests : `tests/integration/test_dbos_spike.py` (19 tests, marqueur `postgres`). Processus exécuteur : `tests/integration/dbos_spike_worker.py`.
> Référence : ADR-001, section « Conséquences » (un test par fonction requise ; si un test échoue, bascule sur A4).
> Version 2 : après revue critique. Ajouts : deux processus vivants avec le même identifiant (5c) et verrou d'exécuteur (5d), reprise après annulation (5e, 5f), sous-jobs GPU (6), concurrence par carte (2b), annulation manuelle (4b), correspondance avec `JobQueue`, mesures sur 10 exécutions.

## Dispositif

- Chaque exécuteur est un **vrai sous-processus Python** (`dbos_spike_worker.py`). Il prend d'abord un verrou consultatif Postgres sur son identifiant d'exécuteur (point 5d), puis lance DBOS en appelant `DBOS.listen_queues([...])` avant `DBOS.launch()`, enregistre les files et affiche `READY`. Le processus de test n'embarque aucune instance DBOS : il enfile et observe avec `DBOSClient` seulement.
- Files enregistrées : `gpu0`, `gpu1`, `gpu2` avec `worker_concurrency=1` **et** `global_concurrency=1`, soit une tâche à la fois par carte, même si deux processus écoutent la file (point 2b). `worker_only` porte `worker_concurrency=1` seul et sert de témoin. `cpu` n'a pas de limite. `gpu2` n'a jamais d'écouteur : c'est un témoin négatif.
- `application_version` fixée à `spike-1` : un exécuteur relancé doit avoir la même version pour reprendre ses workflows (voir point 5).
- Chaque test crée son propre schéma système (`dbos_spike_<hex>`), le supprime à la fin et tue (SIGKILL) tous ses sous-processus, même en cas d'échec. Aucun appel réseau : sans `conductor_key`, DBOS ne contacte aucun service (la seule URL externe est un message de log).
- L'URL de la base passe aux exécuteurs par la variable d'environnement `DBOS_SPIKE_DB_URL`, jamais par `argv` : `ps` montre `argv` à tous les utilisateurs (test 7a).
- Un exécuteur meurt avec le processus de test. Son stdin est un tube tenu par pytest, et il sort (code 6) dès qu'il lit la fin de flux, ce qui arrive aussi quand pytest reçoit SIGKILL (test 7c). Pendant un essai, SIGTERM et SIGHUP deviennent `KeyboardInterrupt`, si bien que pytest exécute encore le nettoyage (processus et schéma) quand un délai CI ou un `kill` l'arrête (test 7b).
- Les étapes écrivent des marqueurs horodatés `<epoch> <executor_id> <pid> <note>` : les tests vérifient quel processus a exécuté quoi, et quand, sans se fier à la valeur de retour du workflow.

Commande de preuve (toute la suite) :

```
STUDIO_TEST_PG_URL=postgresql://postgres@localhost:5432/studio_w7 \
  uv run --group dev pytest tests/integration/test_dbos_spike.py -s
```

Résultat : `19 passed` en RUNTIME_S s environ ; relancée RUNS fois de suite sans échec, et aucun schéma `dbos_spike_%` ni processus `dbos_spike_worker.py` restant après coup (`psql … -c "select nspname from pg_namespace where nspname like 'dbos_spike%'"` et `ps -eo args | grep dbos_spike_worker` vides). Sans `STUDIO_TEST_PG_URL`, les 19 tests sont sautés (`STUDIO_TEST_PG_URL is not set`). Un point isolé se relance avec `-k test_1`, `-k test_5c`, etc.

## Synthèse

| # | Fonction requise par ADR-001 | Résultat | Tests |
|---|---|---|---|
| 1 | Routage par `listen_queues`, identifiant d'exécuteur distinct | **réussi** | `test_1` |
| 2 | Priorité avec `worker_concurrency=1` | **réussi** (piège : priorité omise = la plus urgente) ; **limite** : `worker_concurrency` compte par processus, pas par carte, d'où `global_concurrency=1` | `test_2`, `test_2b` |
| 3 | `deduplication_id` | **limite confirmée** : refus dans la même file, acceptation dans une autre, libération à la fin | `test_3` |
| 4 | Timeout qui annule le workflow et ses enfants | **réussi** ; une étape synchrone en cours n'est **pas** interrompue ; une annulation manuelle n'atteint les enfants qu'avec `cancel_children=True` | `test_4`, `test_4b` |
| 5 | Reprise après SIGKILL limitée à l'exécuteur relancé | **réussi** pour le workflow de file ; **trois limites** : enfant lancé par `start_workflow` (5b), deux processus vivants avec le même identifiant (5c, corrigé par le verrou d'exécuteur, 5d), reprise d'un workflow annulé sans file (5e, corrigée en passant la file d'origine, 5f) | `test_5`, `test_5b` à `test_5f` |
| 6 | Enchaînement d'étapes GPU (question soulevée par 5b) | **interblocage** si un parent attend un enfant dans sa propre file `gpuN` ; **réussi** avec un orchestrateur dans `cpu` | `test_6a`, `test_6b` |

Aucun échec des cinq fonctions demandées : la bascule sur A4 prévue par ADR-001 n'est pas déclenchée. Les limites sont couvertes par des précautions (section « Conclusion »). En revanche, le Protocol `JobQueue` ne correspond pas au modèle de DBOS et doit être révisé avant tout backend DBOS (section « Correspondance avec le Protocol `JobQueue` »).

## 1. Routage : `listen_queues` et identifiant d'exécuteur

**Résultat : réussi.**

Protocole : deux exécuteurs vivants et inoccupés. `gpu0` reçoit son identifiant par la configuration (`DBOSConfig["executor_id"]`), `gpu1` par la variable d'environnement `DBOS__VMID`. Le test enfile en alternance 4 workflows `whoami` dans `gpu0` et 4 dans `gpu1`, plus un dans `gpu2` (sans écouteur). Chaque workflow renvoie l'`executor_id` et le PID du processus qui l'a exécuté ; le test compare aussi la colonne `executor_id` de la ligne `workflow_status`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_1`

```
SPIKE 1-routing: gpu0_queue_ran_on=['gpu0', 'gpu0', 'gpu0', 'gpu0'] gpu1_queue_ran_on=['gpu1', 'gpu1', 'gpu1', 'gpu1'] gpu2_without_listener='ENQUEUED'
--- gpu0.log
(dbos:_dbos.py:571) Executor ID: gpu0
READY executor_id=gpu0 listen=gpu0 pid=9894
--- gpu1.log
(dbos:_dbos.py:571) Executor ID: gpu1
READY executor_id=gpu1 listen=gpu1 pid=9917
```

Chaque workflow a tourné dans le processus de sa file (PID vérifié) ; le workflow de `gpu2` reste `ENQUEUED`, sans exécuteur, 2,5 s après la fin des autres : `listen_queues` filtre bien les files.

Lecture du code (DBOS 3.1.0) :
- identifiant d'exécuteur : `DBOS__VMID`, sinon `"local"` (`_dbos.py:499`, `_utils.py:125`) ; `DBOSConfig["executor_id"]` l'emporte sur la variable (`_dbos.py:509-510`). **Si `conductor_key` est fourni, DBOS remplace l'identifiant par un UUID aléatoire** à chaque lancement (`_dbos.py:569-570`) ;
- `listen_queues` prend des **noms** et doit être appelé avant `launch()` (`_dbos.py:3779`) ; les files sont des lignes de la table `queues` (`register_queue` après `launch()`, avec une politique `on_conflict`), filtrées par nom d'application ;
- le fil des files ignore toute file absente de la liste (`_queue.py:842`), **sauf la file interne `_dbos_internal_queue`, écoutée par tout processus** (`_queue.py:851`) : voir 5b et 5e.

## 2. Priorité et concurrence

### 2a. Priorité avec `worker_concurrency=1`

**Résultat : réussi.** Piège relevé : une priorité omise vaut 0, soit la plus urgente.

Protocole : un seul exécuteur `gpu0`. Un workflow `blocker` occupe l'unique place (il attend un message `DBOS.recv`). Six workflows sont enfilés dans un ordre que le FIFO conserverait : `p30-first`, `p10`, `p30-second`, `p20`, `unset` (sans priorité), `p1`. Après 2 s, tous sont encore `ENQUEUED` (la place est prise). Le test libère le bloqueur puis lit l'ordre d'exécution dans le journal des marqueurs. Il vérifie aussi, par les horodatages d'étapes, qu'une étape ne commence qu'après la fin de la précédente.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_2_`

```
SPIKE 2-priority: enqueue_order=['p30-first', 'p10', 'p30-second', 'p20', 'unset', 'p1'] execution_order=['blocker', 'unset', 'p1', 'p10', 'p20', 'p30-first', 'p30-second']
```

Constats :
- ordre croissant de priorité, puis FIFO à priorité égale (`ORDER BY priority ASC, created_at ASC`, `_sys_db.py:4809`) ; plus petit = plus urgent, comme `Job.priority` ;
- les priorités explicites valent de 1 à 2 147 483 647 (`_context.py:41`) ; **omise, elle vaut 0** et passe devant tout (constaté : `unset` sort en premier). Une étape enfilée sans priorité doublerait donc les finaux ;
- la priorité ne préempte rien : elle choisit seulement la prochaine tâche quand une place se libère.

### 2b. `worker_concurrency` compte par processus, pas par carte

**Résultat : limite confirmée**, corrigée par `global_concurrency=1`.

`worker_concurrency` est comparé au nombre de workflows **du processus qui sonde** (`_sys_db.py:4703-4707`, compteur local) ; `global_concurrency` compte les workflows `PENDING` de la file dans la base, tous processus confondus (`_sys_db.py:4730-4739`). Protocole : deux processus écoutent `gpu0` et `worker_only`, avec deux identifiants différents (`gpu0` et `gpu0-stray`, image d'un second service mal configuré). Deux `blocker` sont enfilés dans chaque file.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_2b`

```
SPIKE 2b-concurrency: worker_only_running_at_once=['gpu0', 'gpu0-stray'] gpu0_statuses_with_two_listeners=['ENQUEUED', 'PENDING'] gpu0_ran_on=['gpu0-stray', 'gpu0-stray']
```

Avec `worker_concurrency=1` seul, les deux tâches tournent en même temps, une par processus : sur une carte, ce serait deux modèles en VRAM. Avec `global_concurrency=1` en plus, la seconde tâche de `gpu0` reste `ENQUEUED` et ne sort de la file (`dequeued_at`) qu'après la fin de la première (`completed_at`). Sans `global_concurrency`, ce test échoue (vérifié en retirant la limite du worker).

## 3. `deduplication_id` : portée d'une seule file

**Résultat : limite confirmée**, celle qui justifie le verrou global d'ADR-001.

Protocole : deux exécuteurs `gpu0` et `gpu1`. Un `blocker` est enfilé dans `gpu0` avec `deduplication_id = K` (K joue le rôle d'une clé d'étape) et démarre. Puis :
1. second enfilage de K dans `gpu0` → **refusé** (`DBOSQueueDeduplicatedError`) ; aucune ligne créée ;
2. même enfilage avec `duplication_policy="return-existing"` → renvoie l'identifiant du premier workflow ;
3. enfilage de K dans `gpu1` → **accepté** : les deux workflows sont `PENDING` en même temps, l'un sur `gpu0`, l'autre sur `gpu1`. La même clé d'étape tourne sur deux cartes ;
4. après la fin (`SUCCESS`) du premier, sa colonne `deduplication_id` est remise à `NULL` et un nouvel enfilage de K dans `gpu0` est **accepté** et exécuté.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_3`

```
SPIKE 3-dedup: same_queue='DBOSQueueDeduplicatedError' return_existing_is_first=True other_queue_running_on='gpu1' same_key_after_success='accepted'
```

Lecture du code : l'unicité est un index partiel `UNIQUE (queue_name, deduplication_id) WHERE deduplication_id IS NOT NULL` (`_migration.py:728`) ; l'identifiant est effacé quand le workflow se termine (`_sys_db.py:1134`), est annulé (`cancel_workflows`) ou expire (`cancel_timed_out_workflows`). DBOS protège donc contre un doublon **en attente ou en cours dans la même file**, jamais entre files, ni après la fin de l'étape.

## 4. Timeout et annulation

### 4a. Timeout : annulation du workflow, de ses enfants, et sort de l'étape en cours

**Résultat : réussi** pour l'annulation. Une étape synchrone en cours n'est **pas interrompue** : seule l'étape suivante est empêchée.

Protocole (un exécuteur `cpu`, timeout 2 s) :
- a) `SetWorkflowTimeout(2.0)` dans un workflow DBOS lance `timeout_parent`, qui démarre un enfant `timeout_child` puis exécute une étape synchrone de 6 s (`time.sleep`, image d'un appel GPU bloquant) suivie d'une étape `after` ; l'enfant fait de même ;
- b) deux workflows asynchrones enfilés par `DBOSClient` avec `workflow_timeout=2.0` (l'option d'enfilage équivalente) : une étape `@DBOS.step(preemptible=True)` qui attend `asyncio.sleep(30)`, et une autre qui attend `asyncio.to_thread(time.sleep, 8)`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_4_`. Extrait d'une exécution :

```
SPIKE 4-timeout: statuses={'parent': 'CANCELLED', 'child': 'CANCELLED', 'async_sleep': 'CANCELLED', 'async_thread': 'CANCELLED'} cancel_after_deadline_s={'parent': 1.0, 'child': 1.0, 'async_sleep': 0.02, 'async_thread': 0.02} sync_step_ran_past_cancel_s={'parent': 3.04, 'child': 3.04} preemptible_interrupt_delay_s=0.03 thread_kept_running_s=5.98 parent_checkpointed_steps=['timeout_child', 'long_sync_step']
--- cpu.log
(dbos:_core.py:791) Workflow 51ab15b4-…-1 was cancelled during execution. Waiting for the recorded outcome
(dbos:_core.py:791) Workflow 51ab15b4-…-1-1 was cancelled during execution. Waiting for the recorded outcome
```

Mesures sur **10 exécutions** du test (minimum et maximum de chaque valeur), produites par :

```
for i in $(seq 1 10); do
  STUDIO_TEST_PG_URL=postgresql://postgres@localhost:5432/studio_w7 \
    uv run --group dev pytest tests/integration/test_dbos_spike.py -s -q -k test_4_timeout | grep "SPIKE 4-timeout"
done
```

| Cas | Observé (10 exécutions) |
|---|---|
| parent et enfant | `CANCELLED` tous les deux à chaque exécution ; l'enfant hérite de l'échéance du parent (`workflow_deadline_epoch_ms` identiques) |
| retard de l'annulation sur l'échéance (`cancel_after_deadline_s`) | de 0,01 à 1,01 s ; borne : un balayage par seconde (`_SWEEP_POLLING_INTERVAL_SEC = 1.0`), le test tolère 2,5 s |
| étape **synchrone** en cours (`sync_step_ran_past_cancel_s`) | **non interrompue** : elle finit de 3,04 à 4,04 s après l'annulation, à son terme normal ; son résultat est même enregistré (`long_sync_step` figure dans les étapes du parent) ; l'étape `after` ne démarre jamais |
| étape **asynchrone `preemptible=True`** qui attend de l'asyncio (`preemptible_interrupt_delay_s`) | interrompue (`CancelledError`) de 0,03 à 1,00 s après l'annulation : DBOS relit l'état toutes les secondes (`_PREEMPTIBLE_POLL_INTERVAL_SEC = 1.0`) |
| étape asynchrone préemptible qui attend un **thread** (`thread_kept_running_s`) | l'`await` est interrompu, **le thread continue** jusqu'à son terme (de 4,97 à 5,98 s de plus) |

Lecture du code : `preemptible=True` et `timeout_seconds` d'étape sont refusés sur une étape synchrone (`_core.py:2475`) ; un workflow enfilé reçoit son échéance **au moment où il sort de la file** (`_sys_db.py:4861-4874`), l'attente en file ne compte donc pas ; le balayage des échéances porte sur toute l'application (`_sys_db.py:4582`), si bien qu'un exécuteur vivant annule aussi les workflows expirés d'un exécuteur mort.

### 4b. Annulation manuelle : les enfants ne suivent qu'avec `cancel_children=True`

**Résultat : limite**, à traiter par une précaution.

Le timeout atteint les enfants parce qu'ils héritent de l'échéance (4a). Une annulation manuelle, comme celle du chien de garde de progression d'ADR-001, ne les atteint pas par défaut : `cancel_workflow(…, cancel_children=False)` (`_dbos.py:2045`, `_client.py:766`). Protocole : deux `parent_with_child` dans `cpu`, dont l'enfant est dans une étape en cours. L'un est annulé sans option, l'autre avec `cancel_children=True`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_4b`

```
SPIKE 4b-cancel: after_cancel={'plain': 'CANCELLED', 'plain.child': 'PENDING', 'cascade': 'CANCELLED', 'cascade.child': 'CANCELLED'} plain_child_final='SUCCESS'
```

L'enfant du parent annulé sans option continue et se termine en `SUCCESS` : son travail GPU aurait continué sans personne pour l'attendre. Avec `cancel_children=True`, l'enfant passe `CANCELLED`. Son étape synchrone en cours va quand même à son terme, comme en 4a.

## 5. Reprise après SIGKILL

**Résultat : réussi** pour le workflow enfilé dans `gpuN` (5a). **Trois limites** : un enfant lancé par `DBOS.start_workflow` (5b) ; deux processus vivants avec le même identifiant (5c, corrigé en 5d) ; la reprise d'un workflow annulé (5e, corrigée en 5f).

### 5a. Reprise par le même identifiant, et par lui seul

Protocole : `gpu0` exécute `resumable` (étape 1 comptée, puis étape 2 qui attend un fichier `release`). Pendant l'étape 2, le processus reçoit SIGKILL. Un exécuteur `gpu1` démarre alors et tourne 3 s. Puis le fichier `release` est créé et un nouveau processus démarre avec l'identifiant `gpu0`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k "test_5_"`

```
SPIKE 5-recovery: after_kill=('PENDING', 'gpu0') after_gpu1_start=('PENDING', 'gpu0') result={'s1_executor': 'gpu0', 's2_executor': 'gpu0'} step1_runs=1 step2_attempts=['gpu0', 'gpu0']
--- gpu1.log
(dbos:_dbos.py:656) No workflows to recover from application version spike-1
--- gpu0-life2.log
LOCKED executor_id=gpu0 backend_pid=… pid=…
(dbos:_dbos.py:571) Executor ID: gpu0
(dbos:_dbos.py:652) Recovering 1 workflows from application version spike-1
```

Constats :
- après le SIGKILL, le workflow reste `PENDING` sur `gpu0` ; `gpu1` ne le touche pas (ni au démarrage, ni ensuite) ;
- le processus relancé avec l'identifiant `gpu0` obtient le verrou d'exécuteur (libéré par la mort du précédent), reprend le workflow et le termine. L'étape 1, enregistrée, n'est pas rejouée. **L'étape 2 interrompue repart de son début** : deux tentatives, sur `gpu0`, par deux PID différents. Une étape est donc exécutée au moins une fois, pas exactement une fois ;
- mécanisme : au lancement, DBOS ne cherche que les workflows `PENDING` de **son identifiant et de sa version d'application** (`_sys_db.py:2617`), puis les remet dans **leur file d'origine** (`reenqueue_for_recovery`, `_sys_db.py:5073`, `coalesce(queue_name, '_dbos_internal_queue')`).

### 5b. Limite : un enfant lancé par `start_workflow` peut changer de carte

Un enfant lancé par `DBOS.start_workflow` n'a pas de file (`queue_name` NULL). À la reprise, DBOS le remet dans `_dbos_internal_queue`, que **tous** les exécuteurs écoutent quel que soit `listen_queues`. Protocole déterministe : `gpu0` exécute `parent_with_child` ; pendant l'étape de l'enfant, SIGKILL ; `gpu1` démarre ; `gpu0` redémarre, remet ses deux workflows en file puis meurt aussitôt, avant son premier sondage (mode `--exit-after-recovery`, image d'un redémarrage qui plante au chargement du modèle) ; enfin `gpu0` redémarre normalement.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_5b`

```
SPIKE 5b-child-recovery: child_queue_before_kill=None child_attempts=['gpu0', 'gpu1'] child_queue_after_recovery='_dbos_internal_queue' parent_after_recovery=('ENQUEUED', 'gpu0') parent_result={'parent_executor': 'gpu0', 'child_executor': 'gpu1'}
--- gpu0-life2.log
(dbos:_dbos.py:652) Recovering 2 workflows from application version spike-1
RECOVERED executor_id=gpu0 left_pending=0
```

L'enfant d'un workflow de `gpu0` a été exécuté par `gpu1` ; le parent, lui, est resté dans la file `gpu0` et s'est terminé plus tard sur `gpu0` avec le résultat produit sur `gpu1`. Quand `gpu0` redémarre sans incident, l'enfant va au premier exécuteur qui sonde la file interne : c'est une course entre toutes les cartes vivantes. La forme retenue pour enchaîner des étapes GPU est au point 6.

### 5c. Limite : deux processus vivants avec le même identifiant exécutent deux fois l'étape en cours

C'est le scénario « worker considéré mort mais encore vivant » d'ADR-001, ou un redémarrage qui chevauche l'ancien processus. Au lancement, DBOS reprend **tous** les workflows `PENDING` de son identifiant (`_dbos.py:645-658`, `_sys_db.py:2617`) sans vérifier qu'aucun autre processus vivant ne porte cet identifiant. `reenqueue_for_recovery` repasse le workflow en `ENQUEUED`, si bien que `global_concurrency=1` ne compte plus l'exécution en cours et ne protège pas. Protocole (DBOS nu, option `--no-executor-lock`) : le processus A (`gpu0`) est dans l'étape 2 de `resumable` ; un processus B démarre avec l'identifiant `gpu0` pendant que A vit.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_5c`

```
SPIKE 5c-duplicate-executor: first_alive_when_second_ran=True step_attempts=['pid=11053', 'pid=11203'] step_completions=2 workflow='SUCCESS'
--- gpu0-B.log
(dbos:_dbos.py:652) Recovering 1 workflows from application version spike-1
T5C_ABORT
```

L'étape a tourné **deux fois en parallèle** (deux PID) et s'est terminée deux fois. DBOS ne garde que le premier résultat enregistré et abandonne l'autre exécution (`_core.py:835`), mais le travail GPU a bien été fait deux fois. Le verrou `step_claims` du répartiteur ne protège pas ce cas : les deux exécutions sont le **même** workflow, donc toutes deux « détentrices » d'un jeton qui ne porterait que `workflow_id` ou `executor_id`.

### 5d. Correction : verrou consultatif d'exécuteur

Avant `DBOS.launch()`, le worker ouvre une connexion dédiée et prend `pg_try_advisory_lock(k)`, où `k` est dérivé de (application, schéma système, identifiant d'exécuteur). Il garde cette connexion toute sa vie. Si le verrou reste pris au-delà d'un court délai (`--lock-wait`, qui couvre la fermeture de la session d'un processus tout juste tué), il affiche `REFUSED` et sort (code 4) **sans lancer DBOS**, donc sans rien reprendre. Un fil vérifie la connexion toutes les 0,5 s ; s'il la perd, le processus sort aussitôt (code 5), car un autre processus peut désormais prendre l'identifiant.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_5d`

```
SPIKE 5d-executor-lock: second_exit_code=4 step_attempts=1 workflow='SUCCESS' lock_lost_exit_code=5 restart_after_lock_loss=True
--- gpu0-B.log
REFUSED executor_id=gpu0 reason=executor-lock-held pid=…
```

Le second `gpu0` sort en erreur sans journal DBOS (ni `Executor ID`, ni `Recovering`). L'étape n'a qu'une tentative et qu'une fin, et `gpu1` démarre normalement (un verrou par identifiant). Après `pg_terminate_backend` sur la session du verrou, A sort avec le code 5 et un nouveau `gpu0` démarre. Le test 5a vérifie de son côté qu'un redémarrage après SIGKILL obtient bien le verrou. Sans verrou, 5d échoue (vérifié sur une copie du worker dont le verrou n'est jamais refusé).

Limite résiduelle : entre la perte de la session du verrou et la sortie du processus (au plus 0,5 s, plus la durée d'un appel bloquant), l'ancien processus peut encore écrire. Le jeton de fencing d'une étape GPU doit donc identifier **l'instance de processus** (par exemple un UUID tiré au démarrage, ou le PID du serveur de la session du verrou), pas seulement `workflow_id` ou `executor_id`. L'écriture d'artefact « premier écrit gagne » reste la dernière barrière.

### 5e. Limite : reprendre un workflow annulé sans file l'envoie sur n'importe quelle carte

`cancel_workflows` et le balayage des timeouts mettent `queue_name` à NULL (`_sys_db.py:1185`, `_sys_db.py:4614`). `resume_workflow` sans `queue_name` remet le workflow dans `_dbos_internal_queue` (`_sys_db.py:1240`), et `fork_workflow` fait de même (`_sys_db.py:1722`). Les commandes `dbos workflow resume` et `dbos workflow fork` n'ont **aucune option de file** (`cli/cli.py:622-640` et `645-690`). Protocole : un `blocker` enfilé dans `gpu0` avec `workflow_timeout=1.0` est annulé par son échéance ; `gpu0` meurt, `gpu1` vit ; on appelle `client.resume_workflow(wf)`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_5e`

```
SPIKE 5e-resume-without-queue: after_timeout=('CANCELLED', None) resumed_queue='_dbos_internal_queue' ran_on='gpu1'
```

Le travail GPU de `gpu0` a tourné sur `gpu1`. Si plusieurs cartes vivent, c'est une course entre elles, comme en 5b. Autre effet : la reprise efface l'échéance (`_sys_db.py:1243`) et le workflow reçoit un **nouveau délai complet** quand il ressort de la file (`_sys_db.py:4861-4874`).

### 5f. Correction : reprendre avec la file d'origine

Même mise en place, puis `client.resume_workflow(wf, queue_name="gpu0")`.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_5f`

```
SPIKE 5f-resume-with-queue: after_timeout=('CANCELLED', None) while_gpu0_down=('ENQUEUED', 'gpu0') ran_on='gpu0'
```

Tant que `gpu0` est arrêté, le workflow attend dans `gpu0` : `gpu1`, vivant, ne le prend pas. Il tourne sur le `gpu0` relancé. Comme DBOS efface la file à l'annulation, c'est au répartiteur de conserver la file `gpuN` d'origine de chaque workflow d'étape.

## 6. Enchaîner des étapes GPU

### 6a. Interblocage : un parent qui attend un enfant dans sa propre file

La version 1 de ce document proposait, pour un sous-workflow GPU, de l'enfiler explicitement dans la même file `gpuN`. Avec `worker_concurrency=1`, c'est un interblocage. Le parent occupe l'unique place de la file, il ne la libère qu'à son retour, et il attend l'enfant, qui ne peut pas sortir de la file.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_6a`

```
SPIKE 6a-same-queue-child: parent_child_queue=('PENDING', 'ENQUEUED', 'gpu0')
```

L'enfant n'a jamais démarré (aucun marqueur), alors qu'il aurait fini aussitôt. Un parent dans `gpu0` qui attendrait un enfant dans `gpu1` ne bloquerait pas, mais il immobiliserait la carte `gpu0` sans rien y calculer.

### 6b. Forme retenue : orchestrateur dans `cpu`, jobs GPU enfilés dans leur `gpuN`

Le parent qui enchaîne des étapes GPU vit dans `cpu`, où il n'occupe aucune carte. Il enfile chaque job GPU explicitement dans sa file avec `DBOS.enqueue_workflow("gpuN", …)`, puis attend le résultat. Protocole : pendant l'étape du job GPU, `gpu0` reçoit SIGKILL ; `gpu1` démarre après la mort de `gpu0` ; puis `gpu0` redémarre.

Commande : `... pytest tests/integration/test_dbos_spike.py -s -k test_6b`

```
SPIKE 6b-cpu-orchestrator: child_queue_after_recovery='gpu0' child_attempts=['gpu0', 'gpu0'] parent_result={'parent_executor': 'cpu', 'child_executor': 'gpu0'}
```

Le job garde sa file `gpu0` pendant la panne. `gpu1` ne le reprend pas, et le `gpu0` relancé le termine (deux tentatives, deux PID de `gpu0`). Le parent se termine sur `cpu` avec le résultat produit sur `gpu0`.

## 7. Hygiène du dispositif

| Test | Ce qu'il prouve | Sans la correction |
|---|---|---|
| `test_7a` | l'URL de la base (mot de passe compris) n'apparaît pas dans `/proc/<pid>/cmdline` d'un exécuteur, qui atteint pourtant la base | l'ancienne version passait `--db-url <url>` : `ps -eo args` montrait le mot de passe |
| `test_7b` | un pytest qui reçoit SIGTERM au milieu du test 4 sort avec le code 2 (`INTERRUPTED`), ne laisse aucun exécuteur et supprime son schéma | pytest mourait aussitôt (code −15), les exécuteurs restaient rattachés au PID 1 et le schéma restait en base (vérifié sur une copie sans gestionnaire de signal) |
| `test_7c` | un exécuteur dont le stdin atteint la fin de flux sort (code 6), ce qui couvre un pytest tué par SIGKILL | l'exécuteur attendait indéfiniment (vérifié sur une copie qui ignore la fin de flux) |

```
SPIKE 7b-sigterm: child_exit_code=2 workers_left=0 schema_left=False
```

## Correspondance avec le Protocol `JobQueue`

`studio/core/interfaces.py` définit `JobQueue` sur le modèle d'A4, une file **tirée** : un appelant prend une tâche (`claim`), reçoit un bail, le renouvelle, puis le solde. `SqlJobQueue` (`studio/core/queue.py`) en tire un jeton de fencing `(executor_id, attempt)`. DBOS suit un modèle **poussé dans le processus** : le fil de file du processus qui écoute défile et exécute lui-même le workflow (`execute_dequeued_workflow`, `_core.py:1170`). Il n'offre ni prise, ni bail, ni battement, et il ré-exécute sous le même `executor_id` (5c). Méthode par méthode :

| Méthode de `JobQueue` | Équivalent DBOS 3.1.0 | Écart |
|---|---|---|
| `enqueue(job, queue) -> bool` | `DBOSClient.enqueue` / `DBOS.enqueue_workflow` avec `deduplication_id`, `priority`, `workflow_timeout` ; refus par `DBOSQueueDeduplicatedError` | le refus ne vaut que dans une file (point 3) : le `False` « toutes files confondues » exige de prendre `step_claims` avant l'enfilage, hors de DBOS |
| `claim(queue, executor_id, now, lease) -> Lease` | aucun : le processus qui écoute la file défile et exécute lui-même | pas d'objet `Lease` rendu à un appelant ; le choix de la carte se fait à l'enfilage, plus au moment de la prise |
| `heartbeat(lease, now, extend) -> Lease` | aucun bail : un workflow `PENDING` reste attribué à son `executor_id` sans échéance | la vivacité doit venir d'ailleurs : verrou d'exécuteur (5d) et bail `step_claims` renouvelé par l'étape elle-même |
| `complete(lease)` | retour du workflow → `SUCCESS` ; un second résultat du même workflow est abandonné (`_core.py:835`) sans erreur pour l'exécution perdante | aucun jeton vérifié : deux exécutions vivantes du même workflow sont toutes deux légitimes (5c) |
| `fail(lease, error, retry)` | exception → `ERROR`, état final ; relance = `retries_allowed` d'une étape, ou `resume_workflow` / `fork_workflow` explicite avec `queue_name` (5e, 5f) | la relance d'un workflow terminé est une opération d'exploitation, pas un état de la file ; `attempt` ≈ `recovery_attempts` |
| `expire(now) -> list[str]` | aucun équivalent temporel : un exécuteur mort n'est repris qu'au redémarrage de son identifiant (5a) ; `workflow_timeout` **annule** (état final) et ne remet pas en file | une carte morte qui ne redémarre pas garde ses workflows `PENDING` : le répartiteur doit le détecter (bail `step_claims` expiré), annuler avec `cancel_children=True`, puis reprendre avec `queue_name` sur une autre carte |
| `pending(queue) -> list[Job]` | `DBOSClient.list_queued_workflows(queue_name=…)` | équivalent (lecture) |

Conséquence : **DBOS ne peut pas implémenter le Protocol `JobQueue` actuel**, et la conclusion ci-dessous ne peut pas « se reporter dans `JobQueue` » telle quelle. Avant tout backend DBOS, le Protocol doit être révisé en deux ports :
1. un port **répartiteur** : `enqueue` (prise de `step_claims` puis enfilage dans `gpuN`), `pending`, `cancel` et `resume(queue)`, où la reprise passe toujours la file d'origine ;
2. un port **garde d'étape**, porté par `step_claims` et commun aux deux backends : l'étape elle-même prend le bail avec un jeton de fencing qui identifie l'instance de processus, le renouvelle pendant le calcul et le solde à l'écriture de l'artefact.

`claim`, `heartbeat` et `expire` restent propres au backend tiré (A4). Impact sur ADR-001 : la phrase « Plan B derrière la même interface `JobQueue` » suppose une interface commune qui n'existe pas encore. Aujourd'hui l'interface est taillée pour le plan B, et c'est le plan A (DBOS) qui n'y entre pas. Le coût de retour arrière « faible à moyen » d'ADR-001 vaut une fois cette révision faite. La modification de `studio/core/interfaces.py` sort du périmètre de cet essai : elle est demandée séparément. Le test `test_8a` vérifie que chaque méthode du Protocol figure dans le tableau ci-dessus.

## Autres constats (lecture du code)

- **Version d'application.** La reprise et le défilement filtrent sur la version d'application (`_sys_db.py:2617`, `start_queued_workflows`). Par défaut DBOS la calcule à partir du code source des workflows : après `make update` avec un code modifié, les workflows `PENDING` de l'ancienne version ne sont plus repris automatiquement par la nouvelle.
- **Tentatives de reprise.** `max_recovery_attempts` vaut 100 par défaut (`_registrations.py:10`) ; au-delà, le workflow passe `MAX_RECOVERY_ATTEMPTS_EXCEEDED`. Un workflow qui fait planter la carte (OOM) serait relancé jusqu'à 100 fois.
- **Identifiant par défaut.** Sans configuration ni `DBOS__VMID`, l'identifiant vaut `"local"` pour tous les processus : deux workers mal configurés reprendraient les workflows l'un de l'autre, et le verrou d'exécuteur de 5d empêcherait le second de démarrer.
- **Version de DBOS.** `pyproject.toml` épingle `dbos>=3.1,<4` dans le groupe `dev` (ADR-001 décision 12 : DBOS n'est plus une dépendance d'exécution) ; `uv.lock` fixe 3.1.0. Les constats ci-dessus (API, comportements, numéros de ligne) valent pour 3.1.0 seulement.

## Conclusion

**DBOS Transact 3.1.0 est retenu pour ADR-001, sous les précautions suivantes.** Les cinq fonctions exigées fonctionnent sur de vrais processus contre Postgres, et aucune ne déclenche la bascule sur A4. L'essai a trouvé des limites. Certaines étaient anticipées par l'ADR (déduplication par file, étape non interrompue). D'autres sont nouvelles : identifiant partagé par deux processus vivants, reprise hors de la file d'origine, concurrence comptée par processus, annulation sans les enfants. Toutes se traitent par les précautions ci-dessous, à porter par le répartiteur, les workers et un Protocol `JobQueue` révisé (section précédente).

1. **Verrou global par clé d'étape (obligatoire).** `deduplication_id` n'agit que dans une file et disparaît à la fin, à l'annulation ou à l'expiration du workflow (point 3). Le répartiteur prend d'abord le verrou `step_claims` (bail + battement), vérifie que l'artefact de l'étape n'existe pas déjà, puis enfile dans `gpuN` avec `deduplication_id = clé d'étape` comme seconde barrière. `duplication_policy="return-existing"` rend l'enfilage idempotent dans une même file.
2. **Identifiant d'exécuteur unique et un seul processus vivant par identifiant.** Mécanisme vérifié : `DBOSConfig["executor_id"]` (prioritaire) ou `DBOS__VMID`. Chaque service Compose fixe `gpu0`…`gpu3`, `cpu`, `llm`. Le worker refuse de démarrer si l'identifiant vaut `local` ou sort de cette liste. Pas de `conductor_key` : DBOS remplacerait l'identifiant par un UUID aléatoire. Avant `DBOS.launch()`, le worker prend un **verrou consultatif de session** `pg_try_advisory_lock` sur son identifiant et le garde toute sa vie. Il refuse de démarrer si le verrou est pris, et il sort s'il perd la connexion du verrou (5c, 5d). Le **jeton de fencing** d'une étape GPU identifie l'instance de processus, pas seulement `workflow_id` ou `executor_id`.
3. **Version d'application fixe.** `application_version` est fixée explicitement dans la configuration et changée seulement lors d'un changement incompatible des workflows. `make update` vide d'abord les files ou reprend les workflows restants (bifurcation vers la nouvelle version) avant de redémarrer les workers.
4. **Interruption des étapes GPU.** DBOS n'interrompt jamais une étape synchrone : le timeout annule le workflow et ses enfants, puis seule l'étape suivante est empêchée (point 4a). Une étape GPU sera donc **asynchrone et `preemptible=True`**. Elle attendra ComfyUI par HTTP/websocket et, sur `CancelledError`, appellera l'API d'interruption de ComfyUI ou arrêtera l'instance (le chien de garde de progression d'ADR-001 reste nécessaire). Un appel bloquant placé dans un thread continuerait après l'annulation : jamais de calcul GPU dans `asyncio.to_thread`, mais un sous-processus tué explicitement. Une relance attend la libération du verrou d'étape. Le résultat d'une étape terminée après l'annulation peut encore être enregistré : l'écriture d'artefact « premier écrit gagne » le traite comme toute sortie arrivée en second.
5. **Enchaînement des étapes GPU (remplace la précaution 5 de la version 1).** Pas de travail GPU dans un enfant `start_workflow`, qui peut changer de carte à la reprise (5b). Pas de sous-workflow GPU attendu par un parent qui occupe une file `gpuN` : dans la même file, c'est un interblocage (6a) ; dans une autre, la carte du parent reste immobilisée. Une suite d'étapes GPU sur une même carte s'écrit en **étapes d'un seul workflow**. Sinon, chaque job GPU est **indépendant** : il est enfilé par le répartiteur, ou par un **orchestrateur qui vit dans `cpu`**, explicitement dans sa file avec `DBOS.enqueue_workflow("gpuN", …)`. La reprise le remet alors dans cette file (6b). En défense, l'étape GPU vérifie au démarrage que `DBOS.executor_id` correspond à sa carte et échoue sinon.
6. **Priorité toujours explicite** (de 1 à 2³¹−1, plus petit = plus urgent) : une priorité omise vaut 0 et passerait devant les finaux. Les classes d'ADR-001 (finaux avant brouillons ; conformité et scripts avant critique et veille) se traduisent en plages fixes.
7. **Tentatives bornées.** `max_recovery_attempts` réduit (par exemple 3) sur les workflows GPU ; l'état `MAX_RECOVERY_ATTEMPTS_EXCEEDED` est remonté comme un échec de l'étape.
8. **Au moins une fois.** Une étape interrompue par un arrêt brutal repart de son début (point 5a). Les étapes GPU restent idempotentes grâce aux clés d'étape et à l'écriture d'artefact « premier écrit gagne ».
9. **Une tâche à la fois par carte : `worker_concurrency=1` et `global_concurrency=1`.** `worker_concurrency` compte par processus (2b). `global_concurrency=1` sur chaque `gpuN` est une défense peu coûteuse contre un second écouteur mal configuré. Elle ne remplace pas le verrou d'exécuteur, car elle ne voit pas le doublon de 5c.
10. **Toute annulation d'un workflow d'étape passe `cancel_children=True`** (chien de garde, arrêt manuel), ou bien l'étape n'a pas d'enfant (4b).
11. **Tout `resume` ou `fork` d'un workflow GPU passe `queue_name=<gpuN d'origine>`.** Le répartiteur conserve cette file, puisque DBOS l'efface à l'annulation (5e, 5f). `dbos workflow resume` et `dbos workflow fork`, qui n'ont pas d'option de file, sont **interdits en exploitation** : la reprise passe par l'outil du studio. Une reprise redonne un délai complet au workflow.
12. **Version de DBOS épinglée.** Contrainte `dbos>=3.1,<4` dans le groupe `dev` de `pyproject.toml` (posée à la fin de la phase 1). **Cet essai est relancé à chaque montée de version de DBOS**, même mineure. `test_8b` échoue tant que la version installée diffère de celle qu'indique l'en-tête de ce document.

Mise à jour à prévoir dans ADR-001 (hors du périmètre de cet essai) :
- la phrase « L'annulation DBOS n'agissant qu'entre deux étapes » vaut pour les étapes synchrones ; une étape asynchrone `preemptible=True` est interrompue en moins d'une seconde environ ;
- le « mécanisme exact » de l'identifiant d'exécuteur est vérifié ; le scénario « Worker qui redémarre » s'accompagne du verrou d'exécuteur (précaution 2), et le scénario « worker considéré mort mais encore vivant » du jeton de fencing par instance de processus ;
- le cas des enfants et des sous-jobs GPU (précaution 5), la reprise avec la file d'origine (précaution 11) et `cancel_children=True` (précaution 10) s'ajoutent aux scénarios de panne ;
- « Plan B derrière la même interface `JobQueue` » suppose la révision du Protocol décrite plus haut.
