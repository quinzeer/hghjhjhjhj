# Actions humaines requises

Trié par urgence. Chaque entrée : quoi faire, pourquoi, comment vérifier que c'est fait, ce que Claude fait en attendant. Une entrée traitée passe dans « Résolu » avec la date.

## 🔴 Urgent

### H1 — Dépôt public : décider de sa visibilité
- **Constat (2026-09-28)** : `quinzeer/hghjhjhjhj` est **public**. Tout ce qui est poussé (mission, stratégie de chaînes, futures bibles, dossiers d'audit API, prompts des agents) est lisible par tous.
- **Recommandation** : passer le dépôt en privé (GitHub → Settings → General → Danger Zone → Change repository visibility → Private). Coût : les minutes GitHub Actions deviennent limitées sur un compte gratuit (vérifie ton offre GitHub).
- **Vérification** : le badge « Private » apparaît à côté du nom du dépôt.
- **En attendant** : je ne copie pas ton skill `scenariste-youtube` dans `knowledge/imports/` (il deviendrait public) ; les agents le lisent depuis ta session. Aucun secret n'est jamais versionné (`make verify-phase-0` le contrôle).

### H2 — Choisir les concepts des chaînes A et B
- **Quoi** : lire `docs/research/channel-concepts.md` (6 concepts classés) et répondre « A = Cx, B = Cy », ou proposer autre chose.
- **Pourquoi** : la phase 2 (bibles de chaîne, `knowledge/`, bancs éditoriaux) en dépend.
- **Vérification** : `docs/PARAMETERS.md` passe les deux lignes « Concept chaîne » en `confirmé`.
- **En attendant** : phase 1 (squelette, contrats, mocks) avance sans dépendre du concept.

### H3 — Valider ou corriger les paramètres du §0
- **Quoi** : relire `docs/PARAMETERS.md` (hypothèses : Max 5x, 30 min/jour, 1 long + 3 Shorts par semaine et par chaîne, Ubuntu 24.04, langue par chaîne) et corriger ce qui est faux.
- **Vérification** : chaque ligne corrigée passe en `confirmé` avec la date.

## 🟠 Avant la phase 2-3

### H4 — Déposer le pipeline `usine-video`
- Absent du dépôt (MISSION §5). Dépose-le dans un dépôt privé accessible à la session, ou ici une fois le dépôt privé.
- **En attendant** : j'écris des adaptateurs aux interfaces documentées (Kokoro, Wan 2.2, Remotion, faster-whisper) sans reprendre son code.

### H5 — Voix du narrateur Qwen3-TTS
- Fournir, **hors dépôt public** : les fichiers de référence du timbre, les paramètres de génération, le script MLX actuel et la mesure Whisper à 92 %.
- **Pourquoi** : portage CUDA (phase 3) et contrôle WER ≤ 3 % (§8).

### H6 — Préparer la machine GPU
- Installer Ubuntu 24.04 (ou confirmer un autre OS), pilote NVIDIA, Docker + NVIDIA Container Toolkit.
- **Vérification** : `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` liste les 4 cartes.
- Choisir comment `make gpu-smoke` sera lancé : par toi, ou via Remote Control depuis une session Claude Code.

### H7 — Jeton Claude Code pour le studio
- Sur la machine d'exécution : `claude setup-token`, puis placer la valeur dans `.env` (`CLAUDE_CODE_OAUTH_TOKEN=`), jamais dans le dépôt.
- **Vérification** : `make doctor` affiche « CLAUDE_CODE_OAUTH_TOKEN: présent » et aucune erreur.

## 🟡 À lancer tôt (délais externes de plusieurs semaines)

### H8 — Comptes développeur YouTube
- Projet Google Cloud dédié, écran de consentement OAuth, API YouTube Data v3 + Analytics activées, une **chaîne de test**.
- **Pourquoi tôt** : sans audit, les vidéos uploadées par l'API restent privées ; l'audit et l'extension de quota prennent du temps (détails et délais dans `docs/research/apis.md`).

### H9 — Application développeur TikTok
- Créer l'app (Content Posting API), préparer l'audit Direct Post. En attendant l'audit : publication privée ou brouillon uniquement.

### H10 — Structure juridique
- Particulier, micro-entreprise ou société, et nombre de salariés : conditionne la licence Remotion, les revenus YPP et la fiscalité.

## ⚪ Organisation

### H11 — Fichiers hors sujet et branche par défaut
- Le dépôt contient un autre projet (`nginx/`, `prod/`, `www/` : correctifs de sécurité d'un CRM) et sa branche par défaut est `claude/verify-crm-data-access-9cEQh`.
- **Options** : (a) dépôt dédié au studio (recommandé : historique propre, visibilité réglable) ; (b) garder ce dépôt, déplacer le CRM ailleurs et changer la branche par défaut.
- **En attendant** : je ne touche pas à ces fichiers.

### H12 — Branches et PR par phase
- La mission demande « une branche et une PR par phase » ; cette session est contrainte de travailler sur `claude/upbeat-mayer-0q4cyb`. La phase 0 y est développée. Dis-moi si tu veux une PR de phase 0 depuis cette branche et vers quelle base (la branche par défaut actuelle est celle du CRM).

## Résolu

(aucun)
