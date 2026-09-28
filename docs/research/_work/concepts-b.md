# Concepts de chaîne — lot B (C07-C12)

> Consulté le : 2026-09-28 · Auteur : researcher · Version : 1 · Portée : évalue les 6 concepts candidats C07-C12 (lot B) pour `docs/research/channel-concepts.md`, à fusionner avec le lot A. Grille et méthode de preuve issues du skill `scenariste-youtube` §2 étape 2 (non recopié ici, voir le fichier source du skill) ; contraintes de production issues de `docs/MISSION.md` §2, §4, §6 principe 6, §9. RPM détaillé : voir `docs/research/economics.md` (déjà produit par un autre passage de recherche) ; mécanique de conformité détaillée : voir `docs/research/platform-policies.md`. Cette note ne les duplique pas, elle les applique aux 6 concepts.

## Méthode de preuve de demande (à lire avant les tableaux)

Faute d'accès à SocialBlade/vidIQ/NoxInfluencer (pages payantes ou bloquées lors de cette session — codes 402/403 constatés) et le budget de recherche web (`WebSearch`) ayant été épuisé en cours de session (200/200 requêtes consommées, apparemment partagées avec d'autres activités de l'environnement), la preuve de demande ci-dessous repose sur une **méthode alternative explicite (« méthode A »)** : lecture directe, via requêtes HTTP ponctuelles, de pages publiques YouTube non authentifiées — pages de résultats de recherche par mot-clé et pages de vidéo individuelles — et extraction des vues, dates de publication et nombres d'abonnés tels qu'affichés par l'interface YouTube elle-même (données JSON intégrées à la page, pas d'API officielle, pas de compte). Toutes les pages citées ont été ouvertes le **2026-09-28**.

Limites reconnues de cette méthode, valables pour toutes les preuves ci-dessous : (1) instantané unique, pas de série temporelle auditée ; (2) les dates « il y a X mois/ans » affichées par YouTube sont approximatives (± quelques semaines), converties ici en dates calendaires en comptant depuis le 2026-09-28 ; (3) pour plusieurs chaînes, l'historique complet des vidéos n'était pas accessible (les onglets `/videos` et pages d'accueil de chaîne ne renvoient pas de liste exploitable sans JavaScript côté client) — la « médiane » a donc dû, pour C09, C10 et C11, être calculée **sur plusieurs chaînes différentes traitant du même mécanisme** plutôt que sur l'historique propre d'une seule chaîne. C'est une médiane de niche, pas une médiane de chaîne au sens strict du skill ; chaque table le signale. Confiance retenue pour toute donnée obtenue par cette méthode : **moyenne** (jamais élevée, faute d'audit tiers ; jamais faible, car il s'agit de la donnée brute affichée publiquement, pas d'une estimation).

---

## Tableau récapitulatif

| # | Concept | Note /100 | Preuve de demande | RPM estimé (indicatif) | Risque politique | Sérialité | Coût unitaire (long/Short) |
|---|---|---|---|---|---|---|---|
| C07 | Mondes disparus (archéologie reconstituée) | **82** | 2 outliers confirmés (7,9× et 3,6×) | Niche « éducation/histoire » : ~2-3 $ FR généraliste à 9-18 $ US niche forte (cf. economics.md) | Faible-moyen | Dizaines à centaines (1 site = 1 à N épisodes) | Moyen / Moyen |
| C08 | Futurs plausibles et mégaprojets | 71 | 2 signaux (3,3× confirmé ; 14× sur n=2, faible) | Pas de donnée niche dédiée ; par analogie proche du généraliste-tech | Faible | Dizaines (mégaprojets réels) + illimité (spéculatif) | Moyen / Faible-moyen |
| C09 | Terre profonde / temps géologique | 80,5 | 2 outliers confirmés (5,5× et 4,0×, second daté 2024) | Niche « éducation/science » : médiane 10,22 $ US (panel, cf. economics.md) | Faible | Dizaines (mais sujet fini — nécessite sous-arcs) | Moyen / Moyen |
| C10 | Fiction sérielle analog horror | 75,5 | 2 outliers confirmés (15,3× et 6,5×) | Niche « horreur narrée » ~4-13 $ (confiance faible, cf. economics.md) | **Moyen-élevé** | Illimité (univers inventé) | **Faible-moyen** / **Faible** |
| C11 | Géographie et données animées | **84** | 2 outliers confirmés (21,1×, daté 2024 ; et 3,7×) | Pas de donnée niche dédiée ; proche éducation par analogie | Moyen (frontières sensibles) | Illimité (actualité + evergreen) | **Faible** / **Faible** |
| C12 | Batailles et stratégies historiques | 74,5 | 2 outliers confirmés (4,0× et 3,2×) | Niche « fiction/récits » 12,82 $, mais publicité limitée sur les épisodes les plus graphiques ou d'actualité (guerre, morts) | Moyen | Dizaines (guerres et batailles distinctes) | Moyen / Moyen |

**Recommandation.** Sur preuve de demande, tous les 6 concepts passent le seuil (≥ 2 outliers, sauf le cas particulier discuté pour C08). Trois critères départagent ensuite : l'ajustement à la force du studio (rendu procédural Blender, aucun visage en gros plan), le niveau de concurrence déjà installée, et le risque de conformité. Je mettrais **C11 (géographie et données animées), C07 (mondes disparus) et C09 (Terre profonde)** dans le top pour lancer une chaîne du lot B :

- **C11** a la meilleure note (84) : demande prouvée solide, packaging très lisible (une carte qui bouge se comprend en une seconde, conforme à la règle de miniature à 120 px), risque de conformité limité à la prudence sur les tracés de frontières contestées, et surtout un **coût de production le plus faible des six** — c'est le concept qui a structurellement le moins besoin de génération vidéo IA coûteuse (dominé par Remotion/motion design, zéro visage, zéro « look IA » possible sur une carte vectorielle). Sa faiblesse est la concurrence très installée (Wendover, RealLifeLore, Geography Now, Half as Interesting) : l'angle doit être trouvé dans le sous-genre (logistique, données, frontières) plutôt que dans le format générique « pays du monde ».
- **C07** et **C09** sont les concepts qui correspondent le mieux, terme à terme, au principe 6 de MISSION §6 (rendu 3D procédural Blender pour les échelles, l'espace et les destructions, sans humains) : ce sont littéralement les cas d'usage pour lesquels cette architecture a été pensée. Les deux ont une preuve de demande propre et récente, un RPM de niche déjà documenté et favorable dans `economics.md` (éducation/science, 9-18 $ voire 10-18 $ selon la source), et une durée de vie evergreen forte.
- **C10** reste intéressant (les ratios d'outliers les plus élevés du lot, 15,3× et 6,5×, et un argument de légitimité unique : le grain VHS dégradé masque structurellement les défauts d'anatomie et de cohérence des modèles vidéo locaux, ce qui est un avantage réel) mais je le mets en 4e position à cause du risque de conformité — fiction pouvant passer pour réelle, teneur parfois graphique, et une partie du sous-genre déjà repérée en train de détourner des personnages jeunesse protégés (constaté dans les données récoltées, voir C10 §6) — à ne lancer qu'avec un cadrage éditorial et une divulgation stricts dès l'épisode 1.
- **C12** et **C08** sont en queue : C12 parce que Kings and Generals (4,2 M abonnés, 2 014 vidéos) et Epic History (3,18 M abonnés) occupent déjà le mécanisme presque à saturation, et parce qu'une partie non négligeable de la publicité y est limitée par les règles YouTube sur la violence/la guerre (voir C12 §4) ; C08 parce que c'est le concept avec le score « angle neuf » le plus bas — la recherche a fait remonter des dizaines de chaînes quasi identiques de « villes futuristes générées par IA » sans réel apport narratif, et parce que sa preuve de demande la plus solide (The B1M, 3,3×) concerne une chaîne à production humaine réelle, pas IA, ce qui limite ce que ce résultat dit vraiment de la demande pour une version générée.

---

## C07 — Mondes disparus (archéologie reconstituée)

### 1. Promesse et épisodes

Promesse type : « Tu vas voir [ville/civilisation disparue] reconstruite comme si tu y étais, à l'échelle réelle. »

5 idées d'épisodes (≤ 50 caractères) :
1. Rome, 320 après J.-C. : marcher dans la ville entière
2. Babylone sous Nabuchodonosor II, reconstruite en 3D
3. Doggerland : le pays englouti sous la mer du Nord
4. Göbekli Tepe : le plus vieux temple du monde, recréé
5. Pompéi la veille de l'éruption, minute par minute

2 idées de Shorts : « La vraie taille du Colisée, comparée à un stade actuel » ; « Ce que Babylone avait que aucune ville n'a aujourd'hui ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| Khafre Pyramid SAR Scan ANALYSIS: LOST CITY or FAKE NEWS? | Ancient Architects | EN | 2025-03-25 | 609 818 | 76 991 — médiane de 15 vidéos récentes de la chaîne (méthode A, page vidéo + recherche « ancient architects ») | **7,9×** | https://www.youtube.com/watch?v=hh9sDs05s3c |
| Ancient Rome in 3D – Virtual walking from Porta Appia to St. Peter's basilica | History in 3D | EN | ~2026-02 (approx., « il y a 7 mois » au 2026-09-28) | 179 300 | 49 642 — médiane de 6 vidéos récentes de la chaîne (méthode A, recherche « history in 3d » ; page vidéo directe indisponible, code d'erreur au moment de la vérification) | **3,6×** | https://www.youtube.com/watch?v=AVLwGCu5Ma0 |

Confiance : **moyenne** pour les deux (méthode A). La chaîne History in 3D (110 000 abonnés, vérifié sur une autre de ses vidéos) et Ancient Architects (~640 000 abonnés, vérifié sur la page vidéo) sont deux chaînes de reconstruction 3D distinctes qui confirment le même mécanisme (reconstitution 3D d'un lieu disparu avec enquête/débat archéologique).

### 3. Concurrence

- **Ancient Architects** (640 k abonnés, EN, présentateur réel Matt Sibson + illustrations/3D, pas de production IA) — chaîne de référence du secteur, cadence élevée.
- **History in 3D** (110 k abonnés, EN, reconstructions 3D pures, voix off, pas de présentateur visible) — le plus proche du modèle de production visé par ce studio.
- **Kings and Generals / Epic History** couvrent occasionnellement des reconstructions de lieux (« 3D Guide to an 18th century Ship-of-the-Line », 8,3 M vues) — concurrence indirecte, chaînes déjà énormes (voir C12).
- Saturation « AI slop » **confirmée et documentée** : article de presse (404 Media, 2025-09-03) nommant plusieurs chaînes IA de « boring/sleep history » (Sleepless Historian, Boring History Bites, History Before Sleep, The Snoozetorian, Historian Sleepy, Dreamoria) produisant en masse des vidéos d'histoire non vérifiées ; une vidéo de Sleepless Historian cumulait 2,3 M vues. Un créateur du secteur (Pete Kelly, History Time) y décrit le problème central : la vitesse de production IA sans vérification factuelle. Ce n'est pas la même sous-niche (reconstruction 3D vs. vidéo « à écouter pour dormir ») mais c'est le même espace de recommandation et la même politique YouTube qui les vise.

### 4. RPM estimé

Pas de donnée dédiée « archéologie » trouvée. Par analogie avec la niche « éducation/histoire » documentée dans `docs/research/economics.md` (panel de 300 chaînes, médiane 10,22 $/1000 vues aux États-Unis, 2026 ; France généraliste ~2,29 $, fourchette 1,20-3,50 $) : fourchette retenue **2-3 $ FR / 9-18 $ US** si le packaging est reconnu « éducatif » par les annonceurs. Confiance moyenne (source de seconde main, voir economics.md).

### 5. Légitimité d'une production IA/procédurale

- **Rendu 3D procédural Blender : part dominante.** C'est le cas d'usage exemplaire de MISSION §6 principe 6 — géométrie de bâtiments, échelle urbaine, éclairage HDRI, destructions (incendie de Rome, éruption de Pompéi) sont exactement ce que Blender/Cycles fait bien sans acteurs.
- **Modèle vidéo local : part faible**, réservée à quelques plans d'ambiance (fumée, foule en silhouette lointaine, jamais de visage en gros plan).
- **Image animée 2,5D** pour les portraits de personnages historiques (bustes, pièces de monnaie) — jamais de gros plan de visage généré.
- **Motion design** pour cartes, datations, mesures comparatives.
- **Archives du domaine public** : photos de fouilles réelles, plans d'architectes, gravures.
- Point faible du local (visages, foules) : **évité par construction**, le sujet ne l'exige pas.
- Valeur ajoutée vs. « slop » : précision géométrique et cohérence d'une vue à l'autre (mesures archéologiques réelles, sources citées), à l'opposé des chaînes de « sleep history » repérées par 404 Media qui ne vérifient pas leurs faits.

### 6. Risque politique

**Faible à moyen.** Pas de personne réelle imitée, pas de violence graphique. Le risque principal est éditorial, pas plateforme : présenter une reconstruction spéculative (débattue entre archéologues) comme un fait établi expose à des accusations de désinformation historique — d'où l'exigence stricte du `fact_checker` et la mention explicite du niveau de certitude scientifique à l'écran. Divulgation IA nécessaire si le rendu est photoréaliste au point de pouvoir passer pour un document réel (`status.containsSyntheticMedia`, voir `platform-policies.md`), ce qui est probable pour des reconstructions très réalistes de lieux ayant existé.

### 7. Sérialité

Très forte : chaque site/civilisation majeure = 1 à plusieurs épisodes (ville entière, un monument, un jour précis, un mystère non résolu). Dizaines de sites déjà identifiés dans la littérature archéologique publique (Rome, Babylone, Pompéi, Doggerland, Göbekli Tepe, Teotihuacan, Angkor, Carthage…) ; structure de saison possible par civilisation ou par question (« la ville qui a disparu sous l'eau », « la ville qu'on vient de retrouver »).

### 8. Coût unitaire qualitatif

**Long (10 min) : moyen.** Beaucoup de scènes Blender complexes (modélisation architecturale détaillée), mais réutilisables entre épisodes d'une même civilisation (bibliothèque d'assets qui s'enrichit). **Short (40 s) : moyen** — un survol aérien d'une reconstruction déjà modélisée pour le long coûte peu de GPU additionnel (réutilisation de la scène 3D, juste un nouveau rendu de caméra).

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 20/20 | 2 outliers confirmés récents, 7,9× et 3,6×, sur le même mécanisme (§2). |
| Packaging (20, éliminatoire) | 14/20 | Titre court possible, mais une miniature à fort impact sans visage humain est plus dure à obtenir (repère du skill : 69 % des miniatures « breakout » montrent un visage) — compensable par un contraste d'échelle spectaculaire. |
| Audience adressable (15) | 13,5/15 | Sujet universel (histoire ancienne), compris en une phrase. |
| Angle neuf (15) | 9/15 | Le mécanisme « reconstruction 3D de ville antique » existe déjà (Ancient Architects, History in 3D) : l'angle doit se faire sur la focalisation « destructions/échelles/comparaisons » plutôt que la reconstruction générique. |
| Intensité (10) | 7/10 | Mystère archéologique réel, mais rarement un enjeu de vie ou de mort immédiat. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Montrer la ville reconstruite dès l'ouverture est immédiat. |
| Durée de vie (5) | 5/5 | Evergreen fort, aucune dépendance à l'actualité. |
| Conformité (5, éliminatoire) | 4/5 | Pas de vrai=faux si bien sourcé et le niveau de certitude affiché ; vigilance requise sur la saturation « AI slop histoire » qui pourrait entraîner un examen renforcé de YouTube sur toute la sous-catégorie. |
| **Total** | **81,5 → 82** | |

---

## C08 — Futurs plausibles et mégaprojets

### 1. Promesse et épisodes

Promesse type : « Voici à quoi ressemblera vraiment [ville/planète/infrastructure] si on construit ce qui est déjà en projet, fondé sur la science publiée. »

5 idées d'épisodes :
1. NEOM : la ligne de 170 km qui doit sortir de terre
2. La première ville sur Mars, construite étape par étape
3. L'ascenseur spatial : ce qui manque encore pour le construire
4. Terraformer Mars en 200 ans : le vrai plan scientifique
5. La ville flottante qui doit ouvrir en 2030

2 idées de Shorts : « Pourquoi personne n'a encore construit d'ascenseur spatial » ; « La taille réelle de la ville que l'Arabie Saoudite construit ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| The World's Biggest Airport is About to Land | The B1M | EN | ~2026-09-07 (approx., « il y a 3 semaines ») | 3 966 862 | 1 184 686 — médiane de 21 vidéos récentes de la chaîne (méthode A) | **3,3×** | https://www.youtube.com/watch?v=ZnBIsRFtbsA |
| Future City 2125: 100 Years From Now | Modern-Life-Studio (chaîne IA, 28 300 abonnés) | EN | 2025-10-08 | 909 277 | 65 160 vues sur l'autre vidéo connue de la même chaîne (« Future City 2250 », 2025-07-20) — **échantillon n=2, pas une vraie médiane** | 14× (**confiance faible**, échantillon trop petit) | https://www.youtube.com/watch?v=V328AMkg5XQ |

Ces deux preuves ne sont pas parfaitement comparables : The B1M est une chaîne à **production humaine réelle** (tournage, présentateur), qui prouve la demande pour le *mécanisme* mégaprojet, pas spécifiquement pour une version générée par IA. Modern-Life-Studio est bien une chaîne IA sur le mécanisme visé (« Future City »), mais l'échantillon est trop petit (2 vidéos) pour calculer une médiane fiable — signalé comme tel. **Concept dont la preuve de demande pour la version « IA générée » reste partielle.**

### 3. Concurrence

- **The B1M** (4,07 M abonnés, EN, production humaine réelle, tournage + interviews) — référence du secteur mégaprojets.
- **Real Engineering** (5,02 M abonnés, données Wikipédia au 2026-01-20, EN, animation + narration, équipe de 4 permanents + freelances) — proche du mécanisme mais pas centré « villes futures ».
- Une niche « AI-generated future city » très active et peu différenciée a été repérée pendant la recherche : de nombreuses vidéos ambiance/4K sans structure narrative (« Future City 2250 », « Mars Colony 2100 » en boucle « no talking ambience »). Ce sont des vidéos d'ambiance, pas des documentaires avec une promesse et un payoff — **saturation AI slop constatée** sur ce sous-mécanisme précis, contrairement à C07/C09.

### 4. RPM estimé

Aucune donnée de niche dédiée trouvée (ni dans cette session, ni dans `economics.md`, qui signale explicitement l'absence de données pour « ingénierie »). Par analogie prudente avec le généraliste technologique : **inférence, confiance faible**, probablement proche du généraliste (2-6 $ selon pays) sans prime « éducation » aussi nette que C07/C09, le contenu spéculatif étant moins facilement reconnu comme « éducatif » par les classificateurs publicitaires.

### 5. Légitimité d'une production IA/procédurale

- **Blender procédural : part dominante** pour les structures, échelles, comparaisons (ville de 2100 vs. ville actuelle), cohérent avec MISSION §6.6.
- **Modèle vidéo local : part modérée**, plans d'ambiance stylisés (ciel, circulation, matériaux) — jamais de personnage en gros plan puisque le sujet ne l'exige pas.
- **Motion design fort** pour les diagrammes techniques (physique d'un ascenseur spatial, calendrier de construction).
- **Archives : quasi nulles** (sujet spéculatif par nature) sauf pour ancrer dans le réel via des images de mégaprojets existants (données publiques d'agences spatiales, permis de construire publiés).
- Valeur ajoutée vs. slop : rigueur (contraintes physiques réelles, sources scientifiques citées, `fact_checker`) face aux dizaines de chaînes de pure ambiance identifiées, qui n'ont ni promesse ni payoff.

### 6. Risque politique

**Faible.** Pas de personne réelle, pas de violence. Deux points de vigilance : (1) présenter un rendu très réaliste d'un projet non construit peut être perçu comme trompeur si le statut spéculatif n'est pas assez visible dès l'ouverture — divulgation et mention explicite « projection, non réalisé » recommandées ; (2) certains mégaprojets réels (NEOM notamment) sont associés à des controverses politiques et de droits humains dans leur pays d'origine — sujet à traiter avec prudence factuelle plutôt qu'à éviter.

### 7. Sérialité

Bonne mais plus étroite que C07/C09/C11 : le nombre de mégaprojets réels et documentés publiquement est de l'ordre de quelques dizaines à un instant donné (renouvelé par l'actualité), complété par des scénarios spéculatifs (Mars, ascenseur spatial, villes sous-marines) qui, eux, sont en nombre plus limité avant répétition. Structure de saison par thème (villes / espace / infrastructures / climat).

### 8. Coût unitaire qualitatif

**Long (10 min) : moyen** (scènes Blender complexes de mégastructures, bibliothèque d'assets réutilisable par thème). **Short (40 s) : faible-moyen** (réutilisation des mêmes scènes 3D avec un cadrage resserré).

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 16/20 | 1 outlier bien confirmé (B1M, 3,3×) mais sur une chaîne à production humaine, pas IA ; le signal spécifique à l'IA (Modern-Life-Studio) est sur un échantillon trop petit. |
| Packaging (20, éliminatoire) | 12/20 | Visuel spectaculaire facile à vendre, mais concept perçu comme générique tant l'esthétique « ville futuriste IA » est déjà omniprésente. |
| Audience adressable (15) | 12/15 | Large, curiosité technologique/urbanisme. |
| Angle neuf (15) | 7,5/15 | Niche la plus saturée du lot par du contenu IA à faible valeur narrative (constaté directement pendant la recherche). |
| Intensité (10) | 7/10 | Enjeux réels (climat, ressources, faisabilité) mais souvent traités de façon abstraite. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Image spectaculaire immédiate. |
| Durée de vie (5) | 3,5/5 | Dépend en partie de l'actualité technologique, moins evergreen que C07/C09. |
| Conformité (5, éliminatoire) | 4/5 | Besoin d'un cadrage clair « projection, non réalisé » sur les scénarios spéculatifs. |
| **Total** | **71** | |

---

## C09 — Terre profonde / temps géologique

### 1. Promesse et épisodes

Promesse type : « Tu vas voir la Terre telle qu'elle était il y a [N] millions/milliards d'années, minute par minute. »

5 idées d'épisodes :
1. La Terre il y a 4 milliards d'années, avant la vie
2. Le jour où l'astéroïde a tué les dinosaures, heure par heure
3. Pangée : comment un seul continent s'est déchiré
4. La Grande Oxydation : l'événement qui a failli tout tuer
5. La dernière ère glaciaire vue depuis l'espace

2 idées de Shorts : « À quoi ressemblait le ciel il y a 2 milliards d'années » ; « La taille réelle du plus grand supercontinent ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| 4.5 Billion Years of Earth's History in JUST 1 Hour \| Full Documentary | Wild Horizons (68 200 abonnés) | EN | 2026-03-24 | 2 839 655 | 518 795 — médiane de **14 vidéos de 14 chaînes différentes** traitant du même mécanisme exact « X milliards d'années d'histoire de la Terre » (méthode A, recherche « 4.5 billion years earth history ») | **5,5×** | https://www.youtube.com/watch?v=Me4hxOX8ULo |
| 4.5 Billion Years In 20 Minutes | ReYOUniverse (796 000 abonnés) | EN | 2024-10-20 — **hors fenêtre privilégiée (avant 2025-03-28), retenu au titre de la tolérance « au pire 2024 »** ; chaîne elle-même assez grosse, ce qui nuance le caractère « outlier » | 2 069 997 | idem 518 795 (même échantillon niche) | 4,0× | https://www.youtube.com/watch?v=xnCuEwovcFU |

Point méthodologique important : ce mécanisme (« X milliards d'années en Y minutes ») est produit **de façon quasi identique par au moins une dizaine de chaînes différentes** repérées dans un seul résultat de recherche (Wild Horizons, Mr. Deep History, What If, Astrum, Paleora ×2, ReYOUniverse, Flag Geography, TIMELINE RUNNER, ChronoMorph, Big Data Factor, Pug3D, SmallScaleTales…) — cette médiane de niche est donc bien fondée statistiquement (n=14) même si elle ne porte pas sur l'historique d'une seule chaîne.

### 3. Concurrence

- **PBS Eons** (chaîne officielle PBS Digital Studios, 3,17 M abonnés selon une source PBS, production réelle avec présentateurs, très établie, pas IA) — référence qualité du secteur, mais format différent (épisodes courts thématiques, pas de « chronologie complète »).
- **melodysheep** (3,2 M abonnés selon Wikipédia, 432 M vues cumulées ; « Timelapse of the Future », 2019, 112,9 M vues — hors fenêtre mais preuve que le mécanisme peut atteindre une audience colossale) — production semi-artisanale à forte identité visuelle, pas IA générative.
- Le sous-mécanisme précis « 4,5 milliards d'années en 1 heure/20 minutes » est **très saturé et largement dupliqué** par des chaînes de taille moyenne (dizaines de milliers à quelques centaines de milliers d'abonnés), plusieurs visiblement produites à moindre effort (titres quasi identiques, ex. Pug3D « History For Sleep », probablement une variante du filon « sleep content » déjà repéré en C07). Saturation AI slop **probable** sur ce sous-mécanisme précis, non confirmée par une source de presse dédiée cette session (à la différence de C07, où 404 Media documente explicitement le phénomène).

### 4. RPM estimé

Bonne donnée disponible : `docs/research/economics.md` documente une niche « éducation/science » avec **médiane 10,22 $/1000 vues** (panel de 300 chaînes, 3 595 mois-chaîne, mai 2025-mai 2026, confiance moyenne) et une sous-niche « science expliquée / vulgarisation légère » à 5,32 $. Le deep time / temps géologique se classe raisonnablement dans cette fourchette **5-14 $ US**, **2-3 $ FR** (cf. RPM généraliste France de la même note).

### 5. Légitimité d'une production IA/procédurale

- **Blender procédural : part dominante** — paysages, tectonique des plaques, échelle de temps visualisée en mouvement de caméra, exactement le terrain de MISSION §6.6.
- **Modèle vidéo local : part modérée**, réservée aux créatures préhistoriques animées (point faible partiel : l'anatomie animale reste plus simple à contrôler qu'un visage humain, mais demande un contrôle qualité `visual_critic` dédié).
- **Motion design fort** pour les frises chronologiques et cartes de continents en mouvement.
- **Archives : nulles** (pas de sujet filmable).
- Valeur ajoutée vs. slop : échelle de temps réellement respectée et sourcée (`fact_checker`) vs. les nombreuses chaînes quasi identiques repérées, dont plusieurs semblent optimisées pour la durée d'écoute passive plutôt que pour l'exactitude.

### 6. Risque politique

**Faible.** Aucune personne réelle, aucune violence contemporaine. Seul point mineur : l'échelle de temps géologique touche indirectement à l'évolution, sujet occasionnellement sensible dans certains marchés/publics — traitement factuel standard suffisant, pas un point bloquant pour une chaîne en anglais/français destinée à un public généraliste.

### 7. Sérialité

Bonne mais **structurellement finie** à l'échelle du sujet global (l'histoire de la Terre a un début et une fin connus) — nécessite des sous-arcs pour tenir des dizaines d'épisodes distincts : par ère géologique, par extinction, par continent, par « et si » (et si telle extinction n'avait pas eu lieu), par comparaison (Terre vs. Mars vs. Vénus). Avec ces sous-arcs, la sérialité redevient large.

### 8. Coût unitaire qualitatif

**Long (10 min) : moyen** (scènes procédurales complexes mais réutilisables par ère). **Short (40 s) : moyen** — les créatures animées, quand nécessaires, demandent plus de GPU générateur que les scènes purement géologiques de C07/C11.

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 18/20 | 2 outliers confirmés (5,5× récent, 4,0× daté 2024) sur une niche cohérente et large (14 chaînes comparées). |
| Packaging (20, éliminatoire) | 16/20 | Titres forts et intelligibles (« il y a 4 milliards d'années »), miniature = paysage extrême, format déjà validé par le marché. |
| Audience adressable (15) | 12/15 | Universel, mais parfois perçu comme aride sans un bon hook. |
| Angle neuf (15) | 7,5/15 | Sous-mécanisme précis très dupliqué (au moins 10 chaînes quasi identiques identifiées) ; l'angle doit se démarquer nettement du gabarit « X milliards d'années en Y minutes ». |
| Intensité (10) | 8/10 | Extinctions, catastrophes, vertige de l'échelle de temps. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Image de la Terre primitive dès l'ouverture, immédiat. |
| Durée de vie (5) | 5/5 | Evergreen fort. |
| Conformité (5, éliminatoire) | 5/5 | Aucune personne réelle, sujet non sensible. |
| **Total** | **80,5** | |

---

## C10 — Fiction sérielle « analog horror » / found footage fictionnel

### 1. Promesse et épisodes

Promesse type : « Voici un document trouvé — une émission, une cassette, un enregistrement — qui n'aurait jamais dû être regardé. » (Fiction annoncée comme telle dès la description et, si nécessaire, à l'écran.)

5 idées d'épisodes (univers original, pas d'IP protégée) :
1. Bande n°7 : ce que la station a filmé cette nuit-là
2. La diffusion d'urgence de 1987 qui n'a jamais dû sortir
3. Cassette retrouvée : le dernier quart d'heure du bâtiment 4
4. L'émission pour enfants qui a changé au 3e épisode
5. Journal de bord, jour 41 : plus personne ne répond

2 idées de Shorts : « Cette image dure 4 secondes de trop » ; « Le bruit qu'on entend à 0:12 n'est pas dans le script ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| The Cat in the Hat (Analog Horror) | Kris Archives (67 500 abonnés) | EN | 2026-07-25 | 2 223 430 | 145 276 — médiane de **14 vidéos de 14 chaînes différentes** du mécanisme analog horror (méthode A, recherche « analog horror 2026 ») | **15,3×** | https://www.youtube.com/watch?v=MNJhZmC3Bhk |
| SIV-24 Virus Outbreak \| Analog Horror | Rogue Signal (8 510 abonnés) | EN | 2025-07-19 | 951 065 | idem 145 276 (même échantillon niche) | **6,5×** | https://www.youtube.com/watch?v=PeLBMdH2zKs |

Signal complémentaire (non compté comme outlier faute de médiane propre à la chaîne, mais qui confirme la vigueur récente du mécanisme) : Kane Pixels, la chaîne fondatrice du genre (3,66 M abonnés selon Wikipédia), a publié « Backrooms – Everything Must Go » il y a environ un mois (~2026-08), déjà à 4 766 192 vues.

**Point de vigilance sérieux relevé pendant la recherche** : le premier outlier confirmé (« The Cat in the Hat (Analog Horror) ») détourne un personnage jeunesse sous copyright (Dr. Seuss) à des fins d'horreur — ce n'est pas un « univers inventé » au sens strict demandé par le concept, et ce n'est pas un modèle à suivre (risque de droit d'auteur en plus du risque éditorial). Cela confirme cependant que le *mécanisme* (found footage dégradé + IP ou univers familier détourné) fonctionne très fort — à reproduire avec un univers **entièrement original**, condition posée dans le brief du concept.

### 3. Concurrence

- **Kane Pixels** (3,66 M abonnés) — le standard du genre, production semi-artisanale (Unreal Engine/Blender), pas de production IA générative.
- **Mandela Catalogue / Alex Kister** (plus d'1 M abonnés, 55 M vues cumulées selon une synthèse presse) — univers original, référence narrative du genre.
- Selon Tubefilter (article du 2024-10-31, donc antérieur à la fenêtre privilégiée mais retenu comme contexte daté) : le genre a généré **plus de 500 millions de vues en 2024**, et plusieurs chaînes de taille moyenne affichent un rapport vues-mensuelles/abonnés très supérieur à la norme — Spencer Lackey (a/s/l), 108 000 abonnés pour 8 M de vues mensuelles ; Doctor Nowhere, 424 000 abonnés pour 3 M de vues mensuelles — signe d'un genre à forte propension virale, cohérent avec les deux outliers mesurés directement ci-dessus.
- Saturation AI slop : pas de source dédiée trouvée spécifiquement à l'analog horror, mais le genre a explicitement franchi le grand public (film A24 « Backrooms » sorti le 2025-10-31 selon une page vue en résultat de recherche), ce qui a mécaniquement attiré une vague de contenus opportunistes de qualité inégale.

### 4. RPM estimé

`docs/research/economics.md` documente une entrée « Horreur / histoires effrayantes narrées : ~4-13 $ (exemple cité : chaîne Mr Nightmare, 6 M abonnés), confiance **faible** (source non rouverte avec succès) ». Je reprends cette fourchette en confiance faible. La niche « fiction/récits (trahison, revanche) » du même document donne 12,82 $ (confiance moyenne) — plus proche du haut de fourchette si le format est perçu comme narratif plutôt que pur choc horrifique.

### 5. Légitimité d'une production IA/procédurale

- **Argument de légitimité spécifique et fort à ce concept** : le grain VHS, les artefacts de compression, l'éclairage dégradé et le tremblement de caméra caractéristiques du found footage **masquent structurellement** les défauts d'anatomie, de cohérence d'identité et de texture des modèles vidéo locaux — c'est la niche où le point faible documenté du local (visages, incohérence d'une image à l'autre) devient le moins pénalisant, voire un atout esthétique. C'est la seule niche du lot B où le modèle vidéo local peut occuper une part significative sans que ce soit un point faible.
- **Blender procédural : part modérée** pour les décors et environnements abandonnés.
- **Motion design : faible**, générique/interstitiels seulement (écrans de « signal perdu », timestamps).
- **Archives** : textures de bruit VHS et d'interférence du domaine public réutilisables.
- Attention : le principe 6 de MISSION reste « éviter les visages humains en gros plan » — le found footage doit être écrit pour ne montrer des silhouettes/plans larges/caméra de sécurité, jamais un visage net en gros plan, ce qui est un choix d'écriture naturel pour le genre (caméra de survie, signal dégradé) et non une contrainte artificielle.

### 6. Risque politique

**Moyen à élevé — le plus élevé du lot B**, conformément au signal explicite du brief :
- Risque que la fiction passe pour réelle : le format found footage/diffusion d'urgence imite délibérément des formats d'information réels (JT, alerte d'urgence). Précédent réel documenté par la recherche : l'esthétique a historiquement provoqué de la confusion (panique locale autour de simulations d'urgence). Divulgation de fiction obligatoire, dès la description et si besoin à l'écran, en plus de l'étiquette « altered or synthetic content » si le rendu est réaliste (voir `platform-policies.md`).
- Public jeune : une partie du sous-genre cible ou attire explicitement un public jeune (l'exemple « Cat in the Hat (Analog Horror) » trouvé pendant la recherche en est la preuve directe) — interdiction ferme du studio de cibler les enfants (MISSION §12, skill §7 point 10) à faire respecter strictement dans le choix des sujets et des vignettes.
- Contenu potentiellement choc/détresse répétée sans arc narratif = red flag direct du skill §7 point 6 — vigilance éditoriale systématique.
- Pas de personne réelle imitée si l'univers est original (condition posée dans le brief) — réduit une partie du risque par rapport aux found footage qui usurpent des marques/personnes réelles.

### 7. Sérialité

Excellente : univers entièrement inventé, aucune limite structurelle (contrairement à C09) — chaque « cassette » ou « diffusion » est un épisode distinct, avec une continuité de personnages et de lore possible d'un épisode à l'autre (recommandé par le skill pour l'avatar/persona IA : traiter comme un personnage inventé avec continuité).

### 8. Coût unitaire qualitatif

**Long (10 min) : faible-moyen.** **Short (40 s) : faible** — c'est le concept le moins coûteux en rendu par seconde de tous ceux étudiés dans ce lot pour le local vidéo, car le grain/la dégradation volontaire réduisent le besoin de résolution et de cohérence longue durée qu'exigerait un rendu photoréaliste propre.

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 20/20 | 2 outliers confirmés et massifs (15,3× et 6,5×), sur le mécanisme exact, tous deux dans la fenêtre privilégiée. |
| Packaging (20, éliminatoire) | 14/20 | Très fort en genre horreur (mystère, image qui dérange), mais la règle « visage à l'émotion sincère » (repère miniature du skill) est plus dure à tenir sans visages nets. |
| Audience adressable (15) | 9/15 | Niche plus jeune et plus genrée (horreur) que les autres concepts du lot, audience adressable plus étroite. |
| Angle neuf (15) | 9/15 | Univers inventé = fort potentiel d'angle propre, mais le mécanisme « found footage VHS » est déjà copié par des dizaines de chaînes clones (constaté directement dans les données). |
| Intensité (10) | 9/10 | Très forte (mystère + peur), point fort naturel du genre. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Une image qui dérange dès l'ouverture est la structure même du genre. |
| Durée de vie (5) | 3/5 | Tendance cyclique (pic autour du film A24 fin 2025), risque de lassitude du format plus rapide que les concepts evergreen. |
| Conformité (5, éliminatoire) | 2,5/5 | Le critère le plus fragile du lot : risque réel de confusion fiction/réel et d'attraction d'un public jeune, déjà observé dans les données récoltées. |
| **Total** | **75,5** | |

---

## C11 — Géographie et données animées

### 1. Promesse et épisodes

Promesse type : « Voici pourquoi [ce pays/cette frontière/ce réseau] a exactement cette forme, en données et en cartes animées. »

5 idées d'épisodes :
1. Pourquoi le Chili est un pays aussi étroit
2. La frontière la plus absurde du monde, expliquée en cartes
3. Comment un seul conteneur traverse la planète
4. Le pays qui a failli exister et a disparu en un jour
5. La carte qui ment : ce que ta mappemonde te cache

2 idées de Shorts : « Ce pays partage une frontière avec lui-même » ; « La vraie taille de l'Afrique, comparée sur une carte ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| Let's Fix The United States' Awful Borders | Geography By Geoff (1,11 M abonnés) | EN | 2024-11-04 — **hors fenêtre privilégiée (avant 2025-03-28), retenu au titre de la tolérance « au pire 2024 »** ; chaîne assez grosse, ce qui nuance le caractère « outlier » | 2 071 078 | 98 210 — médiane de 4 vidéos de chaînes différentes sur le mécanisme « frontières expliquées » (méthode A, recherche « borders explained map ») | **21,1×** | https://www.youtube.com/watch?v=UjpluyYtOG4 |
| They're Not British. They're Not Independent. So What Are They? | Geography Now | EN | 2026-08-31 | 364 328 | 98 210 (même échantillon niche) | **3,7×** | https://www.youtube.com/watch?v=SnXXIT610eU |

Signal complémentaire non retenu comme outlier (sous le seuil de 3×, mais montre la sensibilité de la niche à l'actualité géopolitique) : Geography Now, « What is going on with Armenia and Azerbaijan?! », 232 963 vues, il y a 6 jours, ratio 2,4×.

### 3. Concurrence

Niche la plus établie et la plus encombrée du lot B :
- **Wendover Productions** (4,9 M abonnés, 833 M vues sur 282 vidéos selon Wikipédia au 2026-09-06) — logistique/géographie/économie, production humaine réelle.
- **Geography Now** (3,92 M abonnés, 729,4 M vues, en ligne depuis octobre 2014 selon Wikipédia au 2026-08-10) — présentateur réel, a terminé son format « un pays par épisode » en octobre 2024 et explore un nouveau chapitre (« Gray Zone », territoires non reconnus, depuis juillet 2025) — signe que même le leader de la niche cherche un nouvel angle, ce qui confirme le diagnostic « angle neuf » ci-dessous.
- **Half as Interesting** (2,9 M abonnés, 805 M vues sur 564 vidéos) — style geo/logistique à ton humoristique.
- **RealLifeLore** — grande chaîne comparable, mécanisme proche.
- Sur l'échantillon récent de Wendover et Geography Now (vidéos produites), la variance est **faible** (aucune vidéo récente au-delà de ~1,6× la médiane de son propre échantillon) : ce sont des chaînes matures à audience stable, pas des viviers d'outliers — l'essentiel de la preuve de demande de cette niche vient donc de chaînes plus petites ou de sujets d'actualité géopolitique ponctuels (Arménie-Azerbaïdjan), pas des mastodontes établis.
- Pas de saturation « AI slop » spécifiquement documentée sur ce mécanisme pendant cette session (à la différence de C07/C09), la production dominante restant humaine et éditorialisée.

### 4. RPM estimé

Aucune donnée de niche dédiée trouvée — `docs/research/economics.md` le signale explicitement (« Ingénierie, géographie : aucune donnée dédiée trouvée »). Par analogie avec la catégorie « éducation/documentaire » : **inférence, confiance faible**, plausiblement 4-10 $ US / 1,5-2,5 $ FR — sans confirmation directe.

### 5. Légitimité d'une production IA/procédurale

- **Motion design (Remotion) : part très dominante** — c'est le concept qui a structurellement **le moins besoin de génération vidéo IA coûteuse** de tout le lot B : cartes animées, graphiques de données, typographie, tout est du code de rendu déterministe.
- **Rendu 3D procédural : part faible**, seulement pour quelques scènes d'échelle (comparaison de superficies en 3D).
- **Modèle vidéo local : très faible**, quasi absent.
- **Archives** : photos de lieux réels sous licence libre pour les inserts.
- Point faible du local (visages, foules) : **non pertinent**, le format n'en a presque jamais besoin.
- Valeur ajoutée vs. slop : c'est aussi le concept avec **le risque de « look IA » le plus bas** (aucune texture générative à défaut, donc aucun artefact visuel possible) — argument de conformité fort en plus de l'argument de coût.

### 6. Risque politique

**Moyen**, spécifique à ce concept : les tracés de frontières sont un sujet légalement et diplomatiquement sensible dans plusieurs pays (le concept touche par nature à des territoires contestés — Cachemire, Sahara occidental, Taïwan, Chypre du Nord, etc.). Un précédent concret a été trouvé pendant la recherche : Real Engineering (chaîne concurrente indirecte) a connu une controverse pour avoir représenté de façon contestée l'étendue territoriale de l'Inde dans une vidéo sur le programme spatial indien. Nécessite une politique éditoriale explicite sur le tracé des frontières contestées (suivre la position de l'ONU par défaut, le signaler à l'écran) plutôt qu'une prise de position implicite. Pas de personne réelle imitée ; pas de violence graphique.

### 7. Sérialité

Illimitée : chaque pays, frontière, réseau logistique ou jeu de données est un épisode distinct ; alimentation continue par l'actualité géopolitique (permet une chaîne evergreen ET réactive) ; structure de saison par continent, par type de mécanisme (frontières / logistique / démographie) ou par question récurrente.

### 8. Coût unitaire qualitatif

**Long (10 min) : faible.** **Short (40 s) : faible.** Le concept le moins coûteux du lot B en heures GPU générative — l'essentiel du budget va au temps de développement Remotion/données plutôt qu'au calcul GPU.

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 20/20 | 2 outliers confirmés (21,1× et 3,7×), bien que le premier soit daté 2024. |
| Packaging (20, éliminatoire) | 18/20 | Une carte animée se comprend en une seconde à 120 px, fort contraste possible, correspond très bien aux règles de miniature du skill. |
| Audience adressable (15) | 13,5/15 | Très large (géopolitique, curiosité générale). |
| Angle neuf (15) | 7,5/15 | Concurrence énorme et déjà mature (Wendover, RealLifeLore, Geography Now, HAI) — même le leader de la niche change de format faute d'angle neuf restant sur son mécanisme historique. |
| Intensité (10) | 8/10 | Frontières et actualité géopolitique = enjeu réel et concret. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Une carte qui bouge dès l'ouverture est immédiat. |
| Durée de vie (5) | 4,5/5 | Bon mélange evergreen + actualité. |
| Conformité (5, éliminatoire) | 3,5/5 | Terrain politiquement sensible (tracés de frontières contestées), nécessite une politique éditoriale explicite mais gérable. |
| **Total** | **84** | |

---

## C12 — Batailles et stratégies historiques reconstituées

### 1. Promesse et épisodes

Promesse type : « Voici comment [bataille/siège] a vraiment été gagné ou perdu, carte par carte, décision par décision. »

5 idées d'épisodes :
1. Cannae, -216 : comment 50 000 Romains ont été encerclés
2. Le siège qui a duré 2 ans et n'a jamais dû réussir
3. La flotte invisible qui a changé la guerre du Pacifique
4. Trafalgar en 3D : la manœuvre qui a tout décidé
5. La bataille perdue d'avance qui a sauvé un empire

2 idées de Shorts : « La formation qui a gagné 300 batailles » ; « Pourquoi cette flotte n'aurait jamais dû gagner ».

### 2. Preuve de demande

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| War of the Spanish Succession: All Battles and Events – FULL DOCUMENTARY | Kings and Generals (4,2 M abonnés) | EN | 2026-09-13 | 841 901 | 208 075 — médiane de 14 vidéos récentes de la chaîne (méthode A, recherche « kings and generals ») | **4,0×** | https://www.youtube.com/watch?v=5ij0tDYhIhg |
| American Revolution: Road to Independence | Epic History (3,18 M abonnés) | EN | 2026-06-12 | 1 716 689 | 542 684 — médiane de 7 vidéos récentes de la chaîne (méthode A, recherche « epic history tv ») | **3,2×** | https://www.youtube.com/watch?v=Wyip07JxiT4 |

Deux chaînes différentes, deux outliers récents (dans la fenêtre privilégiée), même mécanisme (documentaire de bataille/guerre en cartes animées).

### 3. Concurrence

Niche la plus dominée par un très petit nombre d'acteurs établis :
- **Kings and Generals** (4,2 M abonnés, ~2 014 vidéos publiées, ~1 Md de vues cumulées selon un résultat de recherche vidIQ/SPEAKRJ, confiance faible car non rouvert directement) — cadence très élevée, quasi hebdomadaire, couvre aussi bien l'Antiquité que l'actualité (plusieurs vidéos récentes de la chaîne portent sur la guerre en Ukraine, hors du périmètre strictement historique du concept).
- **Epic History** (3,18 M abonnés) — production plus lente, très qualitative, longs formats « All Parts » cumulant plusieurs millions de vues sur les guerres napoléoniennes et mondiales.
- **Invicta** — reconstructions 3D de batailles antiques et médiévales, chaîne plus petite mais avec des outliers ponctuels (« How did the US Navy win the Battle of Midway? », 6,7 M vues, mais ancienne).
- Pas de saturation « AI slop » spécifiquement documentée sur ce mécanisme précis cette session ; la barrière à l'entrée (nécessite une recherche historique et une réalisation cartographique soignées) semble avoir jusqu'ici limité l'arrivée de contenu IA de masse, à la différence de C07/C09.

### 4. RPM estimé

`docs/research/economics.md` documente « Fiction/récits (trahison, revanche) : 12,82 $ » — proche par nature du récit de bataille (montée dramatique, enjeux, trahisons). Mais **point de vigilance spécifique et documenté** : les règles publicitaires YouTube limitent la publicité sur le contenu de guerre/violence/mort selon leur degré de gravité et d'actualité (voir `platform-policies.md` pour le détail des règles « advertiser-friendly ») — plusieurs vidéos récentes de Kings and Generals portent sur des conflits contemporains (Ukraine) qui tombent typiquement dans cette zone de publicité restreinte. Un concept strictement historique (batailles antiques/médiévales/moderne, sans actualité de guerre en cours) limite ce risque. Fourchette retenue : **6-12 $ US pour l'historique pur, potentiellement dégradée sur tout épisode touchant à un conflit contemporain**.

### 5. Légitimité d'une production IA/procédurale

- **Blender procédural : part dominante** — cartes 3D de terrain, formations tactiques, mouvements de troupes et de flottes, exactement l'usage visé par MISSION §6.6 ; c'est d'ailleurs déjà, dans les grandes lignes, l'esthétique dominante de Kings and Generals (animation de carte plutôt que reconstitution d'acteurs).
- **Modèle vidéo local : part modérée**, plans d'ambiance de combat à distance, sans visage en gros plan (cohérent avec l'esthétique déjà standard du genre).
- **Motion design fort** pour les flèches de mouvement, les effectifs chiffrés, les lignes de front.
- **Archives** : peintures et gravures d'époque du domaine public, cartes historiques.
- Valeur ajoutée vs. slop : précision tactique et géographique réelle (terrain, échelle, chronologie sourcée) — le principal risque n'est pas le « look IA » mais la concurrence déjà très qualitative sur le fond historique.

### 6. Risque politique

**Moyen.** Violence, guerre et mort sont les sujets explicitement signalés à risque de publicité limitée par les règles YouTube (voir §4). Deux atténuants : le format est historique et pédagogique (pas de représentation graphique de violence, dans l'esprit des chaînes de référence du secteur) et n'implique aucune personne réelle vivante. Point de vigilance éditoriale supplémentaire : la ligne de démarcation entre histoire et actualité géopolitique doit être tenue strictement (contrairement à Kings and Generals, qui couvre aussi l'actualité) pour éviter à la fois le risque de publicité limitée et le risque de polarisation politique sur des conflits en cours.

### 7. Sérialité

Bonne : des dizaines de guerres et de batailles majeures documentées, structure de saison par guerre, par siècle ou par thème tactique (sièges / batailles navales / guerres méconnues) ; moins « illimité » que C10/C11 (le stock de batailles majeures bien documentées, bien qu'important, est fini), mais largement suffisant pour des dizaines d'épisodes distincts avant tout risque de répétition.

### 8. Coût unitaire qualitatif

**Long (10 min) : moyen** (cartes 3D détaillées, mouvements de troupes animés, réutilisables par théâtre de guerre). **Short (40 s) : moyen** — un mouvement tactique clé peut être extrait d'une scène de carte déjà modélisée pour le long.

### 9. Note /100

| Critère (poids) | Note | Justification |
|---|---|---|
| Demande prouvée (20) | 18/20 | 2 outliers confirmés et récents (4,0× et 3,2×) sur deux chaînes distinctes du même mécanisme. |
| Packaging (20, éliminatoire) | 14/20 | Cartes de bataille animées très lisibles, mais les miniatures à base de personnages/portraits sont plus dures à composer sans visages en gros plan. |
| Audience adressable (15) | 10,5/15 | Large mais plus masculine/passionnés d'histoire militaire que les autres concepts du lot. |
| Angle neuf (15) | 6/15 | Le score le plus bas du lot sur ce critère : Kings and Generals (4,2 M abonnés, 2 014 vidéos) et Epic History dominent déjà le mécanisme presque à saturation, difficile de se différencier sur le fond. |
| Intensité (10) | 9/10 | Enjeu de vie ou de mort, stratégie, fort par nature. |
| Livrable en 30 s (10, éliminatoire) | 9/10 | Une carte de bataille en mouvement dès l'ouverture fonctionne immédiatement. |
| Durée de vie (5) | 5/5 | Evergreen fort pour l'historique pur. |
| Conformité (5, éliminatoire) | 3/5 | Publicité limitée probable sur une partie du catalogue (violence/guerre/mort) ; nécessite de tenir strictement la ligne « historique, pas actualité ». |
| **Total** | **74,5** | |

---

## Limites de la méthode et questions ouvertes

- **Aucun des 6 concepts n'est sans preuve de demande** au sens strict du skill (chacun a au moins 2 outliers avec une URL ouverte et un ratio calculé), mais la **qualité** de la preuve est inégale : C07, C09 (partiellement), C10, C11 (partiellement) et C12 reposent sur des données bien dans la fenêtre privilégiée (post 2025-03-28) ; C08, C09 (2e ligne) et C11 (1re ligne) comportent une donnée datée 2024 ou un échantillon trop petit (n=2), explicitement signalé dans chaque table.
- **C08 est le concept où la preuve de demande spécifique à une production IA reste la plus fragile** : le seul outlier solide (The B1M) est une chaîne à production humaine réelle ; l'échantillon IA (Modern-Life-Studio) n'a que 2 vidéos connues. Une vérification complémentaire (recherche plus large de chaînes « AI future city » avec un historique exploitable) serait utile avant d'investir dans ce concept en priorité.
- **Difficulté de mesure principale rencontrée** : les outils usuels de preuve de demande cités par le skill (page de chaîne, Social Blade, Noxinfluencer, Playboard, vidIQ) se sont révélés en grande partie inaccessibles pendant cette session (pages payantes : codes HTTP 402/403 constatés sur Social Blade, NoxInfluencer, vidIQ ; le budget `WebSearch` de la session a été épuisé après une douzaine de requêtes). La méthode de repli (lecture directe des pages publiques YouTube, calcul manuel de médianes) a permis de tenir l'exigence malgré tout, mais donne une confiance plafonnée à « moyenne » plutôt que « élevée » sur l'ensemble des données chiffrées de cette note, et n'a pas permis de calculer une vraie médiane « par chaîne » pour C09, C10 et C11 (remplacée par une médiane de niche inter-chaînes, méthode explicitée en tête de note).
- **RPM par niche** : seuls C07 et C09 bénéficient d'une donnée de niche déjà publiée et sourcée (`economics.md`, « éducation/histoire » et « éducation/science »). C08 et C11 n'ont aucune donnée dédiée trouvée (signalé explicitement, pas d'extrapolation risquée) ; C10 et C12 reposent sur des fourchettes de confiance faible à moyenne. Une vérification RPM dédiée « géographie », « mégaprojets » et « fiction found footage » resterait utile si le studio retient l'un de ces concepts en priorité.
- **Grille de notation** : la grille /100 du skill est elle-même qualifiée d'« heuristique, non validée statistiquement » par le skill lui-même — les notes ci-dessus classent les 6 concepts entre eux, elles ne sont pas des probabilités de succès.

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | YouTube — Disclosing use of altered or synthetic content | https://support.google.com/youtube/answer/14328491 | s.d. | 2026-09-28 | officiel | élevée |
| S2 | Page vidéo YouTube — Ancient Architects, « Khafre Pyramid SAR Scan ANALYSIS » (609 818 vues, 640 k abonnés) | https://www.youtube.com/watch?v=hh9sDs05s3c | 2025-03-25 | 2026-09-28 | données | moyenne |
| S3 | Résultats de recherche YouTube — « history in 3d » (échantillon de 6-8 vidéos, vues et dates, chaîne History in 3D 110 k abonnés) | https://www.youtube.com/results?search_query=history+in+3d | s.d. | 2026-09-28 | données | moyenne |
| S4 | Page vidéo YouTube — The B1M, « The World's Biggest Airport is About to Land » (3 966 862 vues, 4,07 M abonnés) | https://www.youtube.com/watch?v=ZnBIsRFtbsA | 2026-09-02 | 2026-09-28 | données | moyenne |
| S5 | Page vidéo YouTube — Modern-Life-Studio, « Future City 2125 » et « Future City 2250 » (909 277 et 65 160 vues, 28,3 k abonnés) | https://www.youtube.com/watch?v=V328AMkg5XQ | 2025-10-08 | 2026-09-28 | données | moyenne |
| S6 | Page vidéo YouTube — Wild Horizons, « 4.5 Billion Years of Earth's History in JUST 1 Hour » (2 839 655 vues, 68,2 k abonnés) | https://www.youtube.com/watch?v=Me4hxOX8ULo | 2026-03-24 | 2026-09-28 | données | moyenne |
| S7 | Résultats de recherche YouTube — « 4.5 billion years earth history » (échantillon de 14 chaînes différentes, même mécanisme) | https://www.youtube.com/results?search_query=4.5+billion+years+earth+history | s.d. | 2026-09-28 | données | moyenne |
| S8 | Page vidéo YouTube — ReYOUniverse, « 4.5 Billion Years In 20 Minutes » (2 069 997 vues, 796 k abonnés) | https://www.youtube.com/watch?v=xnCuEwovcFU | 2024-10-20 | 2026-09-28 | données | moyenne |
| S9 | Résultats de recherche YouTube — « analog horror 2026 » (échantillon de 14 chaînes différentes, même mécanisme) | https://www.youtube.com/results?search_query=analog+horror+2026 | s.d. | 2026-09-28 | données | moyenne |
| S10 | Page vidéo YouTube — Kris Archives, « The Cat in the Hat (Analog Horror) » (2 223 430 vues, 67,5 k abonnés) | https://www.youtube.com/watch?v=MNJhZmC3Bhk | 2026-07-25 | 2026-09-28 | données | moyenne |
| S11 | Page vidéo YouTube — Rogue Signal, « SIV-24 Virus Outbreak \| Analog Horror » (951 065 vues, 8,51 k abonnés) | https://www.youtube.com/watch?v=PeLBMdH2zKs | 2025-07-19 | 2026-09-28 | données | moyenne |
| S12 | Page vidéo YouTube — Geography By Geoff, « Let's Fix The United States' Awful Borders » (2 071 078 vues, 1,11 M abonnés) | https://www.youtube.com/watch?v=UjpluyYtOG4 | 2024-11-04 | 2026-09-28 | données | moyenne |
| S13 | Page vidéo YouTube — Geography Now, « They're Not British. They're Not Independent. So What Are They? » (364 328 vues) | https://www.youtube.com/watch?v=SnXXIT610eU | 2026-08-31 | 2026-09-28 | données | moyenne |
| S14 | Résultats de recherche YouTube — « borders explained map » (échantillon de niche « frontières expliquées ») | https://www.youtube.com/results?search_query=borders+explained+map | s.d. | 2026-09-28 | données | moyenne |
| S15 | Page vidéo YouTube — Kings and Generals, « War of the Spanish Succession: All Battles and Events » (841 901 vues, 4,2 M abonnés) + résultats de recherche « kings and generals » (échantillon de 14 vidéos récentes) | https://www.youtube.com/watch?v=5ij0tDYhIhg | 2026-09-13 | 2026-09-28 | données | moyenne |
| S16 | Page vidéo YouTube — Epic History, « American Revolution: Road to Independence » (1 716 689 vues, 3,18 M abonnés) + résultats de recherche « epic history tv » | https://www.youtube.com/watch?v=Wyip07JxiT4 | 2026-06-12 | 2026-09-28 | données | moyenne |
| S17 | Wikipédia — Kane Parsons (Kane Pixels) : abonnés, vues cumulées, filmographie | https://en.wikipedia.org/wiki/Kane_Parsons | s.d. | 2026-09-28 | présentation générale | moyenne |
| S18 | Résultats de recherche YouTube — « kane pixels » (dont « Backrooms – Everything Must Go », 4 766 192 vues, il y a 1 mois ; « The Backrooms (Found Footage) », 95 481 867 vues, hors fenêtre) | https://www.youtube.com/results?search_query=kane+pixels | s.d. | 2026-09-28 | données | moyenne |
| S19 | Tubefilter — It's an analog horror Halloween on YouTube | https://www.tubefilter.com/2024/10/31/its-an-analog-horror-halloween-on-youtube/ | 2024-10-31 | 2026-09-28 | presse | moyenne |
| S20 | 404 Media — AI-Generated 'Boring History' Videos Are Flooding YouTube and Drowning Out Real History | https://www.404media.co/ai-generated-boring-history-videos-are-flooding-youtube-and-drowning-out-real-history/ | 2025-09-03 | 2026-09-28 | presse | élevée |
| S21 | Kapwing — AI Slop Report: The Global Rise of Low-Quality AI Videos | https://www.kapwing.com/blog/ai-slop-report-the-global-rise-of-low-quality-ai-videos/ | 2025-10 | 2026-09-28 | données | moyenne |
| S22 | Medianama — AI Slop Videos Make Up 33% of YouTube Feed, Says Study | https://www.medianama.com/2025/12/223-ai-slop-videos-youtube-algorithmic-recommendations/ | 2025-12 | 2026-09-28 | presse | moyenne |
| S23 | Wikipédia — Real Engineering (chaîne YouTube) : abonnés, vues, historique | https://en.wikipedia.org/wiki/Real_Engineering | 2026-01-20 | 2026-09-28 | présentation générale | moyenne |
| S24 | Wikipédia — Sam Denby (Wendover Productions, Half as Interesting, Jet Lag: The Game) : abonnés, vues | https://en.wikipedia.org/wiki/Sam_Denby | 2026-09-06 | 2026-09-28 | présentation générale | moyenne |
| S25 | Wikipédia — Geography Now (chaîne YouTube) : abonnés, vues, historique éditorial | https://en.wikipedia.org/wiki/Geography_Now | 2026-08-10 | 2026-09-28 | présentation générale | moyenne |
| S26 | Wikipédia — John D. Boswell (melodysheep) : abonnés, vues, filmographie (« Timelapse of the Future », « Timelapse of the Entire Universe ») | https://en.wikipedia.org/wiki/John_D._Boswell | 2026-02-16 | 2026-09-28 | présentation générale | moyenne |
| S27 | Résultat de recherche (synthèse vidIQ/SocialBlade) — Ancient Architects : 628 000 abonnés, 83,1 M vues cumulées | https://vidiq.com/youtube-stats/channel/UCscI4NOggNSN-Si5QgErNCw/ | 2025-12 | 2026-09-28 | données | faible |
| S28 | Résultat de recherche (synthèse vidIQ/SPEAKRJ) — Kings and Generals : ~4,11 M abonnés, 2 014 vidéos, ~1 Md de vues cumulées | https://vidiq.com/youtube-stats/channel/@kingsandgenerals/ | s.d. | 2026-09-28 | données | faible |
| S29 | `docs/research/economics.md` (interne, même session de recherche) — table RPM par niche (éducation/science, fiction/récits, horreur narrée) | — (fichier du dépôt) | 2026-09-28 | 2026-09-28 | données | moyenne |
| S30 | `docs/research/platform-policies.md` (interne, même session de recherche) — mécanique détaillée « inauthentic content » et divulgation synthétique | — (fichier du dépôt) | 2026-09-28 | 2026-09-28 | données | élevée |
