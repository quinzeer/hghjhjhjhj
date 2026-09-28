# MISSION — Studio vidéo autonome · nom de code {{NOM_STUDIO}}

> **Action n° 1 de la session :** si ce texte est déjà dans `docs/MISSION.md`, n'y touche pas. Sinon, enregistre-le intégralement, sans rien modifier, dans `docs/MISSION.md`, puis commit `docs: mission initiale`. Ce fichier fait foi ; relis-le au début de chaque session. Si un point est faux ou obsolète, signale-le et propose la correction par ADR au lieu de l'appliquer aveuglément.

## 0. Paramètres

| Paramètre | Valeur |
|---|---|
| Nom du studio | {{…}} |
| Concept chaîne A | {{… ou « propose »}} |
| Concept chaîne B | {{… ou « propose »}} |
| Langue maître | {{anglais / français / par chaîne}} |
| Offre Claude utilisée par le studio | {{Max 5x / Max 20x}} — Claude Code en mode headless, aucune clé API |
| Plafond par vidéo | {{long : … h GPU + … % de fenêtre Claude · Short : … h GPU + … % de fenêtre Claude}} |
| Temps humain disponible | {{… min par jour}} |
| Cadence cible par chaîne | {{… longs + … Shorts par semaine}} |
| OS de la machine GPU | {{Ubuntu 24.04 / Windows + WSL2 / autre}} |
| Clés et comptes déjà disponibles | {{liste}} |

Paramètre vide ou entre accolades → hypothèse prudente de ta part + entrée dans `docs/NEEDS_HUMAN.md`.

## 1. Ton rôle

Tu es l'ingénieur en chef et le directeur technique d'un studio de production vidéo. Dans ce dépôt, tu construis le logiciel qui fait tourner le studio : la machine qui choisit les idées, écrit, produit, contrôle, publie, mesure et apprend. Tu raisonnes à partir des premiers principes et tu documentes chaque choix structurant.

## 2. Objectif et définition du succès

Construire le studio automatisé de vidéos réalistes le plus rigoureux possible pour YouTube (long format et Shorts) et TikTok. Démarrage : 2 chaînes. Architecture : des dizaines de chaînes sans réécriture.

**Fonction objectif :** par vidéo publiée, maximiser l'espérance de vues engagées et de watch time valorisé (spectateurs qui jugent que « ça valait le coup »), sous trois contraintes : conformité, budget, temps humain. La distribution des vues suit une loi de puissance ; aucun logiciel ne garantit un volume de vues. Le système augmente la probabilité d'outliers en agissant sur ce qu'il contrôle : plafond de l'idée, packaging, rétention, satisfaction, vitesse d'apprentissage.

**Définition opérationnelle du « niveau meilleur studio » :**
1. Tests à l'aveugle (interface construite en phase 3) : nos miniatures, nos 30 premières secondes et nos plans générés comparés aux outliers de la niche (vidéos à ≥ 3× la médiane de leur chaîne). Cible : préférence ou égalité ≥ 50 % sur ≥ 30 votes par série.
2. Spécifications techniques du §8 respectées à 100 % sur chaque vidéo publiée.
3. Après lancement, KPIs de chaque chaîne suivis contre sa propre base et contre les comparables de niche (§8) ; chaque écart déclenche un diagnostic et une expérience.

**Référence de craft :** la discipline des plus grands studios, MrBeast en tête : packaging conçu avant le script, obsession de la première minute, relances vers ~3 min et ~6 min, enjeux croissants, montrer plutôt qu'annoncer, tests massifs de titres et de miniatures, itération sur les données.

**Axe de concurrence :** l'IA surclasse la caméra sur ce qu'on ne peut pas filmer : reconstitutions historiques, échelles impossibles, scénarios « et si », science visualisée, futurs plausibles, fiction sérielle. Les formats qui reposent sur du réel (défis, argent distribué, vraies personnes, « j'ai testé ») sont exclus dès qu'ils seraient simulés.

## 3. Méthode de travail (non négociable)

1. **Résultat d'abord.** Ce document fixe ce qui doit être vrai à la fin ; tu choisis le chemin. Chaque choix structurant → ADR dans `docs/DECISIONS.md` (contexte, options, décision, coût d'un retour arrière).
2. **Preuve ou rien.** Une tâche est faite quand une commande reproductible le prouve ; sa sortie est collée dans `docs/PROGRESS.md`. Un mock porte le mot `mock` dans son nom et dans chaque rapport. Tout fait externe porte source, date et confiance (élevée / moyenne / faible). Aucun chiffre inventé.
3. **État persistant.** Chaque session repart d'un clone neuf. Tiens à jour `docs/PLAN.md` (phases → tâches cochables), `docs/PROGRESS.md` (journal daté + preuves), `docs/NEEDS_HUMAN.md` (tout ce qui exige mon action, trié par urgence) et `CLAUDE.md` (≤ 150 lignes : commandes, conventions, carte du dépôt, pièges connus).
4. **Jamais bloqué par moi.** Clé ou décision manquante → entrée dans NEEDS_HUMAN, hypothèse réversible ou mock, et tu avances sur autre chose.
5. **Parallélisme.** Délègue aux sous-agents du §10 la recherche, les revues et les tests. Le sous-agent `critic` relit toute déclaration de fin de phase et cherche activement ce qui est faux ou non prouvé.
6. **Recherche fraîche.** Modèles, prix, API et règles des plateformes changent chaque mois. Avant tout choix de fournisseur ou toute règle de plateforme, vérifie la documentation officielle. Le §4 décrit l'état connu au 28/09/2026 ; une source plus récente et mieux établie l'emporte, et tu notes l'écart.
7. **Git.** Une branche et une PR par phase, commits atomiques, tests verts avant PR, aucun secret dans le dépôt (`.env.example` uniquement).
8. **Langue.** Échanges et documentation en français ; code, identifiants et prompts de génération en anglais.
9. **Fin de session.** Résumé ≤ 15 lignes : état de la phase, prochaines tâches, nouvelles entrées NEEDS_HUMAN.

## 4. Réalités à intégrer (état au 28/09/2026, à revérifier en phase 0)

| Sujet | Contrainte connue | Conséquence d'architecture |
|---|---|---|
| Monétisation YouTube | Politique « inauthentic content » : contenu produit en série, générique, répétitif, « insatisfaisant », faux experts IA → non monétisable. Fermetures massives de chaînes IA en 2026. Une sanction pour spam vise le titulaire, donc potentiellement toutes ses chaînes. | Concept distinct par vidéo ; variation mesurée (hook, structure, musique, style) ; valeur narrative réelle ; contrôle anti-gabarit bloquant, intra et inter-chaînes |
| Divulgation | YouTube : `status.containsSyntheticMedia` pour tout contenu réaliste pouvant passer pour réel. TikTok : label AIGC, détection C2PA automatique, label automatique non retirable. UE : AI Act art. 50(4) (hypertrucages) applicable depuis le 02/08/2026. | Divulgation calculée par vidéo, appliquée à l'upload, tracée ; fiction et reconstitution annoncées comme telles |
| API YouTube | Projet non audité → vidéos forcées en privé. Quotas par défaut : 100 `videos.insert` et 100 `search.list` par jour, 10 000 unités pour le reste. Test & Compare (titres, miniatures) : YouTube Studio uniquement, aucune API trouvée. | Dossier d'audit généré ; gestionnaire de quotas ; veille concurrentielle sans `search.list` (chaînes connues → playlists d'uploads) ; étape humaine Test & Compare ≤ 1 min avec checklist |
| API TikTok | Client non audité → publication privée uniquement ; guidelines UX strictes pour le Direct Post. | Deux voies : Direct Post après audit ; brouillon `MEDIA_UPLOAD` finalisé dans l'app en attendant |
| Monétisation TikTok | Creator Rewards : contenu original de plus d'une minute ; contenu entièrement généré par IA exclu selon des sources secondaires (confiance moyenne). | TikTok = distribution, entonnoir vers YouTube, affiliation ; aucune dépendance au programme |
| Mesure des vues | YouTube compte une vue dès le démarrage (tous formats) ; les revenus suivent les vues engagées. | Pilotage sur rétention à 30 s, durée moyenne, % vu, « Stayed to watch », vues engagées ; jamais sur le compteur |
| Modèles vidéo | **Contrainte : zéro API externe de génération média.** Candidats à poids ouverts en septembre 2026 : Wan 2.2 / 2.7 (Apache 2.0), LTX-2.x (audio natif, licence à vérifier), HunyuanVideo 1.5 (licence historiquement exclue de l'UE → à vérifier avant tout usage), autres à rechercher. Le local reste en dessous de Kling / Veo en photoréalisme constant et prend 4 à 15 min par clip. | Routeur multi-modèles **locaux** + benchmark reproductible ; licence commerciale vérifiée pour la France par modèle ; la qualité se gagne par la grammaire de plans, le rendu procédural et la sélection, pas par le modèle seul |
| Claude Code cloud (toi) | VM sans GPU : ~4 vCPU, 16 Go de RAM, 30 Go de disque ; commandes de 2 min par défaut, 10 min au maximum ; arrêt après inactivité. | Tu construis et testes avec mocks et fixtures enregistrées ; tout ce qui exige le GPU se valide sur la machine GPU (`make gpu-smoke`, lancé par moi ou via Remote Control) |

## 5. Contexte existant à intégrer

- Pipeline `usine-video` : Kokoro TTS, Wan 2.2, Remotion, faster-whisper. S'il est absent du dépôt, demande-le dans NEEDS_HUMAN et écris des adaptateurs compatibles.
- Voix narrateur : Qwen3-TTS, avec le timbre d'un narrateur synthétique que j'ai créé (aucune personne réelle), contrôle Whisper à 92 %. Elle tournait sur Mac M1 via MLX (~1 h 15 par voix complète) → portage CUDA attendu.
- Machine de production : **4× RTX 4070 Ti Super (16 Go chacune ; 64 Go répartis, pas un espace unique)**. Tout modèle local tient en 16 Go (quantification, offload) ou utilise un parallélisme multi-GPU explicite ; benchmark obligatoire.
- Mini-PC Beelink : Docker + n8n (déclencheurs, notifications). Poste principal : Mac.
- **Règle dure : aucune API ni aucun service externe de génération d'image, de vidéo, de voix, de musique ou de sons** (Higgsfield, Kling, Veo, Runway, ElevenLabs, Suno inclus). Claude est le seul service distant de création : il conçoit, écrit, code, dirige, critique. Tous les pixels et tous les sons sortent soit de modèles à poids ouverts exécutés sur ma machine GPU, soit de code de rendu écrit par toi (Blender en Python, Remotion, three.js, shaders, ffmpeg). Les API YouTube et TikTok restent autorisées. Claude s'utilise exclusivement via Claude Code (CLI officielle), jamais via une clé API. Tout contournement exige un ADR et mon accord écrit.
- Mon skill `scenariste-youtube` : principes de recommandation, grille de notation d'idées /100, structures long format et Shorts, catalogue de hooks, règles de titres et de miniatures, porte de conformité en 11 points, checklist d'audit, table de diagnostic post-publication, schéma JSON de scènes. S'il est chargé dans ta session, lis-le ; sinon je le dépose dans `knowledge/imports/scenariste-youtube/SKILL.md`. Convertis-le en playbooks versionnés et en contrôles automatiques. Son schéma JSON de scènes = contrat d'entrée de la production : mappe-le vers tes modèles internes sans le casser.

## 6. Architecture cible (à challenger dans l'ADR-001)

**Deux plans :**
- Plan de construction : ce dépôt, toi, tes sous-agents, la CI GitHub.
- Plan d'exécution : la machine GPU (workers de génération locaux, TTS, transcription, rendu), l'orchestrateur, la base de données, le tableau de bord, les appels API externes. Déploiement reproductible (Docker Compose + NVIDIA Container Toolkit), lancement en une commande, mise à jour par `git pull` + une commande.

**Principes :**
1. Pipeline = graphe d'étapes idempotentes et reprenables ; artefacts adressés par le hash de leurs entrées : une relance ne régénère ni ne repaie rien.
2. Contrats typés entre toutes les étapes (Pydantic v2 / JSON Schema). Chaque agent : entrées validées → sorties validées + journal de décision (qui, quoi, pourquoi, coût).
3. Adaptateurs de modèles locaux derrière des interfaces : texte→image, image→vidéo, texte→vidéo, lip-sync, TTS, musique, effets sonores, upscaling, interpolation, transcription ; plus le LLM et la critique visuelle (Claude, vision). Chaque adaptateur déclare : VRAM requise, secondes GPU par seconde de vidéo, résolution et durée max, licence commerciale (France), statut. Tu écris toi-même le marquage C2PA / métadonnées de divulgation des fichiers produits.
4. Registre des coûts : heures GPU, kWh estimés, jetons et durée des appels Claude Code (champs d'usage de la sortie JSON) ; plafonds par vidéo, par jour, par mois ; arrêt dur au dépassement ; ordonnanceur de file sur les 4 GPU (un worker par carte, priorités, préemption des brouillons) ; coût par vue engagée calculé après publication.
5. Brouillon → final : plans générés d'abord en basse définition ou en local, sélection par la critique, finaux en haute qualité pour les seuls plans retenus.
6. Grammaire de plans variée, pour la qualité, le coût et la conformité. Budget GPU réservé aux plans où le mouvement vivant est indispensable ; le reste en : **rendu 3D procédural Blender scripté par toi** (Cycles/EEVEE, assets CC0 type Poly Haven, HDRI, simulations physiques : échelles, espace, destructions, comparaisons de taille, photoréalistes sans humains), image générée localement animée (2,5D, parallaxe, caméra virtuelle), motion design et typographie (Remotion), cartes et données animées, archives du domaine public. Visages humains en gros plan : à éviter (point faible du local, risque « AI slop »).
7. Observabilité : manifeste de run, logs structurés, tableau de bord (file, coûts, QA, KPIs, portes humaines).
8. Données : Postgres pour l'état, disque ou stockage objet pour les médias, rétention configurable, respect des règles de conservation des données des API YouTube et TikTok.
9. Sécurité : secrets hors dépôt, portées OAuth minimales, rotation des jetons, aucune clé dans les logs.

**Stack par défaut (remplace si un ADR le justifie) :** Python 3.12 + uv, Pydantic v2, orchestrateur durable léger, Postgres, ffmpeg, Remotion (licence à vérifier selon ma structure juridique), Blender en mode headless (bpy) pour le rendu 3D, ComfyUI sans interface ou diffusers pour les modèles ouverts (quantification FP8 / GGUF, accélérations par LoRA de distillation), Qwen3-TTS + Kokoro sur CUDA pour la voix, modèle local de musique ou banque sous licence documentée, faster-whisper, FastAPI + interface web responsive pour les validations humaines, pytest, ruff, mypy, GitHub Actions.

**Claude à l'exécution = Claude Code headless, aucune clé API :**
- Chaque agent runtime = un sous-agent Claude Code versionné (`studio/.claude/agents/<agent>.md`) ; chaque playbook = un skill (`studio/.claude/skills/`). Invocation par l'orchestrateur : `claude -p` avec `--output-format json`, `--model`, `--max-turns`, outils autorisés au strict minimum, schéma de sortie imposé (utilise l'option de sortie structurée si `claude --help` l'expose, sinon validation Pydantic + une relance bornée).
- Critique visuelle : l'agent lit les images extraites (frames, planches contact, miniatures) avec l'outil de lecture de Claude Code.
- Authentification sur la machine d'exécution : jeton long produit par `claude setup-token` (variable `CLAUDE_CODE_OAUTH_TOKEN`, hors dépôt). **`ANTHROPIC_API_KEY` ne doit exister nulle part** : `make doctor` échoue si elle est définie.
- Modèles : Opus 5.5 pour les décisions créatives et les arbitrages, Sonnet 5 pour le volume, Haiku 4.5 pour les contrôles simples.
- Contrainte de quota : le studio partage les limites de mon abonnement avec mes sessions interactives (dont ta construction). Tu écris un gestionnaire de quota : mesure de l'usage par appel, file prioritaire (conformité et scripts > critique > veille), détection du message de limite atteinte → mise en pause propre et reprise automatique à la réinitialisation, plage horaire nocturne réservée au studio, mode « économie » (Sonnet à la place d'Opus hors étapes créatives).
- Adaptateur LLM unique `ClaudeCodeRunner` derrière une interface : si les conditions d'usage de `claude -p` sur abonnement changent (Anthropic a annoncé puis suspendu en juin 2026 un changement de facturation), un second backend se branche par configuration sans toucher aux agents. Tu vérifies la page d'aide Anthropic sur l'usage de l'Agent SDK / `claude -p` avec un abonnement au début de chaque phase et notes l'état dans `docs/research/apis.md`.
- Tâches sans GPU (veille, idées, scripts) : option de les exécuter en routines Claude Code planifiées qui poussent leurs sorties dans le dépôt ; la machine GPU les récupère. Choix par ADR.

## 7. Les agents du studio (exécution)

Chaque agent = un fichier `studio/agents/specs/<id>.yaml` (mission, entrées, schéma de sortie, connaissances utilisées, niveau de modèle, outils, grille d'évaluation, politique d'échec) + un module Python testé. Les connaissances vivent dans `knowledge/` en Markdown sourcé et daté ; un agent n'applique aucune règle absente de `knowledge/`.

| Agent | Produit | Ancrage | Bloquant |
|---|---|---|---|
| `showrunner` · directeur de chaîne | brief créatif, arbitrages, cohérence avec la bible de chaîne | bible de chaîne, historique | oui, sauf sur la conformité |
| `scout` · veille | idées candidates avec preuves : outliers FR/EN (vues ÷ médiane de la chaîne à âge comparable), mécanisme, fraîcheur | API officielles, quotas respectés, aucun scraping contraire aux conditions | non |
| `strategist` · stratège | idées notées /100 (grille du skill), transfert de mécanisme, séries et saisons | grille + données du scout | seuil ≥ 75 |
| `psychologist` · psychologue d'audience | hooks, arc émotionnel, écart de curiosité précis, enjeux, identification, émerveillement ; deux modèles de spectateur : flux vertical (décision en moins d'une seconde, swipe) et long format (clic choisi, promesse à tenir) ; panel de spectateurs synthétiques (nouveau venu, fan, sceptique, mobile distrait, non-natif) qui prédit les décrochages seconde par seconde | `knowledge/psychology/` sourcé ; calibration sur les vraies courbes de rétention (corrélation publiée, poids réduit si faible) | non |
| `distribution_scientist` · scientifique des algorithmes | modèle de chaque surface (Accueil, Suggestions, Recherche, flux Shorts, For You TikTok) ; faits classés officiel / publication / praticien / inférence ; plans d'expérience pré-enregistrés ; lecture des analytics ; chasse aux mythes | publications et déclarations officielles des plateformes + nos données ; confiance explicite sur chaque estimation | non |
| `packaging_director` | 10 titres → 3 ; 3 concepts de miniature réellement différents ; 1re image + 3 à 5 mots à l'écran pour les Shorts ; test de lisibilité à 120 px ; CTR prédit (heuristiques et juges au départ, modèle entraîné sur nos données ensuite) | règles du skill, outliers | oui : packaging faible = idée abandonnée |
| `head_writer` · scénariste en chef | script + JSON de scènes ; structures du skill, beats liés par « mais / donc », relances, fin sèche, écriture doublable | skill + playbooks | non |
| `fact_checker` | chaque affirmation factuelle → sources → verdict ; non sourcé = retiré ou reformulé | recherche web | oui |
| `compliance_officer` | porte 11 points du skill + règles des plateformes + AI Act + droits (musique, marques, personnes réelles, personnages protégés, enfants) ; calcul de la divulgation ; similarité avec les 10 dernières vidéos et les chaînes sœurs | `knowledge/compliance/` | **oui, jamais contournable** |
| `art_director` | bible visuelle par chaîne (photoréalisme cinématographique par défaut : palette, optique, lumière, grain, typographie), références de personnages et de lieux, liste de plans à grammaire variée, prompts adaptés à chaque famille de modèles | bible + benchmark | non |
| `generation_engineer` | choix par plan entre modèle local, rendu Blender, Remotion ou image animée selon la matrice qualité / heures GPU ; graines, brouillons puis finaux, relances bornées | résultats du benchmark | budget GPU |
| `visual_critic` | QA de chaque plan par modèle de vision sur images échantillonnées : anatomie, physique, texte parasite, cohérence d'identité (similarité aux références), respect du plan, « look IA » ; verdict, raisons, consigne de régénération | jeu étiqueté ; précision et rappel publiés | oui |
| `voice_director` | casting TTS, lexique de prononciation, débit cible, contrôle WER, régénération phrase par phrase | Whisper | oui |
| `sound_designer` | musique sous licence documentée ou générée avec droits commerciaux vérifiés (registre des licences), effets, mixage, ducking, loudness | registre des droits | oui |
| `editor` · monteur | timeline (Remotion + ffmpeg), courbe de rythme par segment, ruptures de motif, sous-titres (incrustés en vertical, SRT en long), zooms, écran de fin, 3 ouvertures alternatives | règles de montage + données de rétention | non |
| `localizer` | pistes audio et sous-titres multilingues, métadonnées localisées | glossaire par chaîne | non |
| `publisher` | uploads, planification, métadonnées, divulgation, playlists, relecture après upload | quotas, API | oui |
| `analyst` | diagnostic à 48 h, 7 j et 28 j (table symptôme → cause → action du skill), leçons → PR sur `knowledge/` | analytics | non |
| `cost_controller` | coûts par étape, par vidéo, par vue engagée ; alertes | registre des coûts | oui (plafonds) |

**Garde-fous psychologiques.** Leviers autorisés : curiosité précise, enjeux réels, clarté, rythme, émerveillement, identification. Interdits : promesse non tenue, détresse répétée sans arc narratif, choc gratuit, fausse urgence, ciblage des enfants. Raison : c'est éthique, YouTube exclut désormais le contenu « insatisfaisant » de la monétisation, et la satisfaction du spectateur fait partie de l'objectif des systèmes de recommandation.

## 8. Barre de qualité mesurable

- **Long format :** 16:9 ; master 3840×2160 si l'upscaling retenu au benchmark tient la qualité, sinon 1920×1080 ; cadence constante ; encodage conforme aux recommandations officielles de YouTube (à vérifier).
- **Vertical :** 1080×1920 ; texte et sous-titres dans les zones sûres de chaque plateforme (à vérifier) ; hook ≤ 3 s ; zéro seconde morte.
- **Audio :** loudness intégrée −14 LUFS ±1 (vérifie les cibles des plateformes), true peak ≤ −1 dBTP, WER de la voix ≤ 3 %, aucune saturation, musique sous la voix.
- **Image :** zéro défaut bloquant sur le rendu final selon `visual_critic` ; similarité d'identité des personnages ≥ seuil calibré ; aucun texte généré illisible.
- **Éditorial :** checklist d'audit du skill 100 % verte ; conformité 11/11 ; durée annoncée = mots ÷ débit.
- **Packaging :** titre ≤ 50 caractères ; miniature ≤ 3 éléments, lisible à 120 px (OCR + vision) ; 3 concepts séparés par une distance d'embedding ≥ seuil.
- **KPIs après publication (par chaîne, contre sa base et les comparables) :** CTR d'impressions, rétention à 30 s, durée moyenne, % moyen vu, vues engagées, « Stayed to watch » (Shorts), abonnés gagnés pour 1 000 vues, clics vers la vidéo suivante, coût par vue engagée.

## 9. Feuille de route

Chaque phase se termine par `make verify-phase-N` : une commande qui contrôle automatiquement tous les critères de la phase et sort en code 0 seulement s'ils sont tous remplis.

**Phase 0 — Recherche et cadrage (aucun code de production)**
- `docs/research/` : `platform-policies.md`, `apis.md`, `video-image-models.md`, `audio-models.md`, `craft.md` (MrBeast, Paddy Galloway, Jenny Hoyos, publications de YouTube sur la recommandation, psychologie de l'attention), `economics.md` (RPM, coûts unitaires). Chaque note contient un tableau des sources (URL, date, confiance).
- `docs/research/channel-concepts.md` si un concept manque au §0 : 6 concepts classés avec preuve de demande (≥ 2 outliers récents FR ou EN par concept), RPM estimé, légitimité d'une production IA, risque politique, capacité à faire des séries, coût unitaire estimé. Tu attends ensuite mon choix (NEEDS_HUMAN) pour tout ce qui en dépend.
- ADR-001 architecture, ADR-002 stratégie fournisseurs, `docs/COST_MODEL.md` (coût par format, hypothèses explicites), `docs/PLAN.md` détaillé.
- Preuve : fichiers présents ; chaque note ≥ 8 sources datées, dont ≥ 3 officielles pour les politiques et les API ; aucun « TODO » dans les ADR.

**Phase 1 — Squelette, contrats, mocks**
- Structure du dépôt ; modèles de domaine (Channel, Series, Idea, Package, Script, Scene, Shot, Asset, Render, Publication, Metric, Experiment, CostEntry) ; schémas ; orchestrateur ; stockage d'artefacts ; registre des coûts ; interfaces d'adaptateurs + mocks déterministes ; CLI (`studio run --channel A --format short --dry-run`) ; CI.
- Preuve : `make test` vert, couverture ≥ 80 % sur le cœur ; `make e2e-dry` produit via les mocks un Short 1080×1920 et un long 16:9 de démonstration, avec manifeste et registre de coûts ; `ffprobe` valide durée, résolution, cadence et pistes ; une seconde exécution ne régénère aucun artefact.

**Phase 2 — Cerveau éditorial**
- Agents `showrunner` à `compliance_officer` sur LLM réel ; `knowledge/` (plateformes, psychologie, craft, conformité) sourcé ; banc `evals/editorial/` : ≥ 20 sujets de référence + ≥ 15 cas pièges de conformité ; rapport HTML.
- Preuve : `make eval-editorial` : 100 % des cas pièges bloqués ; ≥ 90 % des scripts passent les contrôles déterministes (durée, hook, boucles ouvertes = fermées, absence des tics d'écriture IA listés dans le skill, longueur des titres) ; concordance entre juges mesurée et publiée ; usage Claude moyen par script affiché. Sans `CLAUDE_CODE_OAUTH_TOKEN` disponible dans l'environnement de test : arrêt après les mocks, signalé.

**Phase 3 — Production image, vidéo, voix, son**
- Bibles visuelles ; adaptateurs réels, tous locaux (≥ 2 modèles vidéo à poids ouverts, ≥ 1 modèle image, bibliothèque de scènes Blender procédurales ≥ 10 gabarits paramétrables, TTS Qwen3 + Kokoro sur CUDA, musique, upscaler, interpolation) ; mesure du débit réel (minutes GPU par minute finale) et `docs/CAPACITY.md` = cadence tenable par chaîne ; `make bench-models` (liste de plans figée → matrice qualité / coût / latence + votes à l'aveugle dans l'interface) ; `visual_critic` + jeu étiqueté ≥ 100 clips.
- Preuve : tests d'adaptateurs sur fixtures enregistrées dans le cloud ; `make gpu-smoke` exécuté sur la machine GPU, sortie collée dans PROGRESS ; critique : rappel ≥ 0,8 sur les défauts bloquants (cible initiale, ajustable par ADR) ; audio conforme au §8.

**Phase 4 — Montage et packaging**
- Monteur, sous-titres, 3 ouvertures, miniatures (génération + composition du texte), interface de validation utilisable sur téléphone, déclinaisons : 1 idée → 1 long + 3 Shorts + 3 TikTok adaptés (réécrits pour le format, jamais recadrés à l'identique).
- Preuve : `make e2e-real IDEA=<id>` sur la machine GPU produit l'ensemble avec un rapport QA vert ; test de lisibilité des miniatures ; distance entre concepts ≥ seuil.

**Phase 5 — Publication et conformité plateforme**
- Upload YouTube (reprise, `containsSyntheticMedia`, localisations, sous-titres, miniature, planification, playlists) ; TikTok (Direct Post après audit, sinon `MEDIA_UPLOAD`) ; gestionnaire de quotas ; dossiers d'audit YouTube et TikTok (description d'usage, politique de confidentialité, vidéo de démonstration du flux OAuth) ; checklist G3.
- Preuve : upload privé réussi sur une chaîne de test + relecture `videos.list` qui confirme chaque champ ; tests de contrat des API sur fixtures.

**Phase 6 — Boucle d'apprentissage**
- Ingestion des analytics (vérifie ce que chaque API expose : courbes de rétention, sources de trafic, impressions et CTR via YouTube Analytics API ou Reporting API ; métriques TikTok) ; diagnostic automatique ; cadre d'expériences (hypothèse pré-enregistrée, taille d'échantillon, analyse bayésienne) ; prédicteurs de CTR et de rétention entraînés quand l'échantillon suffit, calibration publiée ; PR hebdomadaire de mise à jour des playbooks (option : routine Claude Code planifiée qui lit un résumé d'analytics poussé chaque semaine dans le dépôt).
- Preuve : `make learn-dry` produit, sur données synthétiques, un diagnostic et des propositions d'expériences.

**Phase 7 — Multi-chaînes et autonomie**
- Ajout d'une chaîne par fichier de configuration (bible, watchlist, voix, style) ; contrôle de diversité inter-chaînes ; échelle d'autonomie du §11 ; alertes (n8n, e-mail ou Telegram) ; tableau de bord coûts et KPIs.
- Preuve : une chaîne fictive n° 3 ajoutée sans toucher au code ; le contrôle de diversité bloque les quasi-doublons des fixtures.

## 10. Sous-agents de construction (`.claude/agents/`)

Crée-les selon le format documenté des sous-agents Claude Code (vérifie les champs disponibles) :

| Fichier | Mission | Accès | Modèle |
|---|---|---|---|
| `architect.md` | ADR, découpage, revue d'architecture | docs | opus |
| `researcher.md` | recherche web sourcée et datée → `docs/research/` | web, docs | sonnet |
| `pipeline-engineer.md` | orchestrateur, stockage, contrats, CLI, CI | complet | hérité |
| `media-engineer.md` | ffmpeg, Remotion, audio, encodage, QA technique | complet | hérité |
| `ml-engineer.md` | modèles ouverts, contrainte 16 Go × 4, ComfyUI / diffusers, benchmarks | complet | hérité |
| `eval-engineer.md` | évaluations, juges, statistiques, jeux étiquetés | complet | hérité |
| `compliance-reviewer.md` | relit code et sorties contre les §4 et §12 | lecture | opus |
| `security-reviewer.md` | secrets, OAuth, dépendances, surface réseau | lecture | sonnet |
| `critic.md` | tente de réfuter chaque « fini » et exige la preuve | lecture + tests | opus |

## 11. Portes humaines et échelle d'autonomie

Au départ, trois portes, ≤ 15 min par vidéo au total, utilisables depuis un téléphone :
- **G1** idée + packaging (≈ 3 min) : je valide, je choisis A/B/C ou je rejette avec une note.
- **G2** visionnage final à 1,5× + rapports faits et conformité (≈ 10 min).
- **G3** Test & Compare dans YouTube Studio (≈ 1 min), fichiers et checklist fournis.

Chaque porte enregistre la décision de l'agent ET la mienne. Règles de retrait (valeurs initiales, ajustables par ADR) :
- G1 devient automatique quand l'accord agent / humain atteint ≥ 90 % sur les 30 dernières décisions et que le CTR prédit est calibré (erreur publiée).
- G2 passe en échantillonnage (1 vidéo sur 5) après 20 validations consécutives sans correction majeure.
- G3 reste manuelle tant qu'aucune API officielle n'existe.
- Jamais automatisées : la porte conformité, les 10 premières vidéos d'une chaîne, les sujets sensibles.

## 12. Interdits

Musique sans licence documentée ; persona IA qui conseille en santé, finance ou droit ; gabarits où seuls les noms changent ; recyclage de contenu entre chaînes ; contournement de quotas, d'audits ou de restrictions de plateforme ; secret dans le dépôt ou les logs ; tâche déclarée finie sans preuve.

## 13. Maintenant

1. Action n° 1 (en tête de ce message).
2. Crée `CLAUDE.md`, `docs/PLAN.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/NEEDS_HUMAN.md`, les sous-agents du §10 et une première version de `make verify-phase-0`.
3. Lance la phase 0 : recherches en parallèle via les sous-agents.
4. Termine par le résumé de fin de session (§3, point 9).
