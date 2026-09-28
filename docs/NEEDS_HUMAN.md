# Actions humaines requises

Trié par urgence. Chaque entrée : quoi faire, pourquoi, comment vérifier que c'est fait, ce que Claude fait en attendant. Une entrée traitée passe dans « Résolu » avec la date.

## 🔴 Urgent

### H0 — Clé d'API YouTube Data en lecture seule (bloque la fin de la phase 0)
- **Pourquoi** : la preuve de demande des concepts (≥ 2 outliers récents mesurés par concept) ne peut se faire légitimement que par l'API officielle (ADR-004). Sans clé, `make verify-phase-0` reste à 13/14.
- **Quoi** : Google Cloud Console → nouveau projet → activer « YouTube Data API v3 » → Identifiants → Créer une clé API → la restreindre à cette API. Puis, dans les paramètres de l'environnement cloud (menu de l'environnement dans la barre de titre de la session → Modifier), ajouter la variable **`YOUTUBE_API_KEY`**. Ne pas la coller dans le chat ni dans le dépôt.
- **Vérification** : dans une nouvelle session, `python3 tools/outliers.py channel @GeographyNow --months 18` affiche un tableau (code 0). Coût : quelques unités sur les 10 000 du quota quotidien.
- **En attendant** : concepts classés sur les 80 points hors demande ; listes de chaînes à mesurer prêtes dans `docs/research/channel-concepts.md`.

### H1 — Dépôt public : décider de sa visibilité
- **Constat (2026-09-28)** : `quinzeer/hghjhjhjhj` est **public**. Tout ce qui est poussé (mission, stratégie de chaînes, futures bibles, dossiers d'audit API, prompts des agents) est lisible par tous.
- **Recommandation** : passer le dépôt en privé (GitHub → Settings → General → Danger Zone → Change repository visibility → Private). Coût : les minutes GitHub Actions deviennent limitées sur un compte gratuit (vérifie ton offre GitHub).
- **Vérification** : le badge « Private » apparaît à côté du nom du dépôt.
- **En attendant** : je ne copie pas ton skill `scenariste-youtube` dans `knowledge/imports/` (il deviendrait public) ; les agents le lisent depuis ta session. Aucun secret n'est jamais versionné (`make verify-phase-0` le contrôle).

### H2 — Choisir les concepts des chaînes A et B
- **Quoi** : lire `docs/research/channel-concepts.md` (6 concepts classés) et répondre « A = Cx, B = Cy », ou proposer autre chose.
- **Recommandation** : A = « Civilisations reconstruites » (C02 + C07), B = « Échelles de l'espace et du temps » (C03 + C09). Alternative à coût minimal pour B : C11 Géographie et données. Le choix définitif gagne à attendre la mesure de H0 (le classement peut s'inverser).
- **Pourquoi** : la phase 2 (bibles de chaîne, `knowledge/`, bancs éditoriaux) en dépend.
- **Vérification** : `docs/PARAMETERS.md` passe les deux lignes « Concept chaîne » en `confirmé`.
- **En attendant** : phase 1 (squelette, contrats, mocks) avance sans dépendre du concept.

### H3 — Valider ou corriger les paramètres du §0 et l'ADR-003
- **Quoi** : relire `docs/PARAMETERS.md` (hypothèses : Max 5x, 30 min/jour, 1 long + 3 Shorts par semaine et par chaîne, Ubuntu 24.04 natif, langue par chaîne) et corriger ce qui est faux.
- **Langue** : anglais (audience et RPM plus élevés), français (arbitrage possible sur certains concepts) ou master anglais + piste audio française.
- **ADR-003** : valider les corrections proposées à la mission (Wan 2.7 fermé, WSL2 incompatible, seuils YPP 2027, cible −14 LUFS non officielle…). Après accord, j'ajoute un erratum daté en fin de `docs/MISSION.md`.
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

## ⚪ Pour information

### H13 — Incident de méthode pendant la recherche (2026-09-28)
- Un sous-agent de recherche (lot B des concepts) a lu par script quelques pages publiques de YouTube, dont des pages de résultats de recherche (`/results`, interdites par le `robots.txt` de YouTube), pour estimer des vues. Volume : quelques dizaines de requêtes au plus, sans compte ni clé.
- **Mesures prises** : ces chiffres ne comptent pas comme preuve (marqués « indice, non compté ») ; la définition du `researcher` interdit désormais tout accès automatisé à youtube.com et tiktok.com (ADR-004) ; la mesure passe par l'API officielle.
- Aucune action requise de ta part.

## Résolu

(aucun)
