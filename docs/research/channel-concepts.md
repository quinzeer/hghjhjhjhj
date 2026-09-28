# Concepts de chaînes : 6 concepts classés

> Consulté le : 2026-09-28 · Auteur : fusion des lots A (C01-C06) et B (C07-C12) par l'ingénieur en chef · Version : 1 · Portée : MISSION §9 phase 0, concepts des chaînes A et B (§0 = « propose »). Détail par concept (épisodes, grilles complètes) : `docs/research/_work/concepts-a.md` et `docs/research/_work/concepts-b.md`.

## Synthèse

- **La preuve de demande n'est pas encore mesurée.** Aucun des 12 candidats n'a d'outlier mesuré par une méthode conforme. Le lot A n'a pu obtenir aucun ratio. Le lot B a calculé des ratios en lisant par script des pages YouTube, dont des pages de résultats de recherche que le `robots.txt` de YouTube interdit ; pour 3 concepts, il les a comparés à une médiane « de niche » au lieu de la médiane de la chaîne. Ces ratios sont gardés comme **indices** et ne comptent pas comme preuve (ADR-004). La mesure conforme passe par `tools/outliers.py` (API YouTube Data), dès que la clé `YOUTUBE_API_KEY` sera disponible (NEEDS_HUMAN H0).
- **Classement provisoire** sur les 80 points de la grille du skill hors « demande prouvée » (20 points ajoutés à la mesure). Deux évaluateurs différents ont noté les lots A et B : un écart de ±3 points est du bruit.
- **Top 6** : C03 Échelles impossibles (64), C11 Géographie et données animées (64), C02 Comment on a construit (63), C09 Terre profonde (62,5), C07 Mondes disparus (61,5), C04 Scénarios « et si » (61).
- **Recommandation** : une chaîne « Civilisations reconstruites » (fusion de C02 et C07) et une chaîne « Échelles de l'espace et du temps » (fusion de C03 et C09). Alternative à coût minimal pour B : C11.
- **Contexte économique** : à partir du 01/02/2027, une nouvelle chaîne devra réunir 8 000 h de visionnage pour entrer au YPP, et le partage des revenus Shorts exigera 10 M de vues Shorts sur 90 jours [S3]. Le long format porte l'économie ; les Shorts servent à la découverte.

## Constats

| # | Constat | Sources | Confiance | Conséquence pour le studio |
|---|---|---|---|---|
| 1 | Les chaînes IA sanctionnées ou désignées comme « slop » en 2025-2026 visent surtout des niches de volume (anime, contenu religieux, animaux, « boring history » générique) ; aucune source consultée ne cite l'ingénierie historique, la géographie ou le temps géologique. | [S4] [S5] [S16] | moyenne | Privilégier des niches où la valeur vient de l'explication et de la reconstitution, pas du volume |
| 2 | Le contenu « histoire » générique produit par IA est déjà signalé comme une nuisance qui noie l'histoire sérieuse. | [S5] | moyenne | Pour C02 et C07 : faits sourcés, niveau de certitude affiché, reconstitution annoncée ; jamais de « boring history » en série |
| 3 | Les leaders non IA de ces niches ont une audience massive et durable (Kurzgesagt 25,5 M d'abonnés ; melodysheep ; Wendover et Half as Interesting ; Geography Now ; Real Engineering). | [S6] [S7] [S9] [S10] [S11] | moyenne | La demande de genre existe ; la barre de qualité est haute, donc le packaging et l'écriture comptent plus que le volume |
| 4 | Une reconstitution réaliste d'un événement ou d'un lieu réel doit être divulguée comme contenu synthétique ; une scène manifestement irréaliste ne l'exige pas. | [S1] | élevée | C02, C07, C09 : divulgation quasi systématique ; C03 et C04 : souvent non requise (rendus manifestement irréalistes) |
| 5 | Les événements sensibles (catastrophes, guerres, tragédies) limitent la publicité. | [S2] | élevée | Écarte C06 et C12 du lancement |
| 6 | Seuils YPP 2027 et partage des revenus Shorts réservé aux chaînes à ≥ 10 M de vues Shorts sur 90 jours. | [S3] | élevée | Chaînes de long format d'abord |
| 7 | Les comparaisons de taille sont un format très copié, y compris en Shorts IA de bas de gamme. | [S4] [S8] | moyenne | C03 n'est viable qu'avec une question narrative par épisode ; une suite d'objets alignés tomberait sous « contenu répétitif » (`platform-policies.md`, règle dérivée 1) |

## Classement

Score = somme (note / 5 × poids) de la grille du skill `scenariste-youtube` hors « demande prouvée », sur 80. Notes par critère : fichiers `_work/`.

| Rang | Concept | Hors demande /80 | Indice de demande (non compté) | RPM (`economics.md`) | Risque politique | Sérialité | Coût unitaire (long / Short) |
|---|---|---|---|---|---|---|---|
| 1 | C03 Échelles impossibles | 64 | preuve de genre au niveau chaîne seulement | généraliste ; niche science plus haute (confiance moyenne) | faible, mais risque de gabarit | 100+ | faible / faible |
| 1 ex æquo | C11 Géographie et données animées | 64 | indices 21,1× (2024) et 3,7× sur médiane de niche | généraliste à éducation | moyen (frontières contestées) | illimitée | faible / faible |
| 3 | C02 Comment on a construit | 63 | aucun ratio obtenu | éducation / ingénierie | faible | 30-50 | faible-moyen / faible |
| 4 | C09 Terre profonde | 62,5 | indices 5,5× et 4,0× sur médiane de niche | éducation / science | faible | dizaines, avec sous-arcs | moyen / moyen |
| 5 | C07 Mondes disparus | 61,5 | indices 7,9× et 3,6× sur médiane de chaîne (méthode non conforme) | éducation / histoire | faible-moyen | dizaines à centaines | moyen / moyen |
| 6 | C04 Scénarios « et si » | 61 | un point de données de 2023 | généraliste à science | faible-moyen | 30-50 | faible-moyen / faible |
| — | C05 Cosmos visualisé | 60 | preuve de genre ancienne | science | faible | 40-60 | faible / faible |
| — | C01 Une journée dans la vie de… | 59 | aucun ratio | généraliste | moyen | 40-60 | élevé / moyen |
| — | C06 Catastrophes minute par minute | 59 | preuve de genre (Fascinating Horror) | réduit (événements sensibles) | élevé | 40-60 | moyen / faible-moyen |
| — | C12 Batailles historiques | 56,5 | indices 4,0× et 3,2× | réduit (guerre, violence) | moyen | dizaines | moyen / moyen |
| — | C10 Fiction analog horror | 55,5 | indices 15,3× et 6,5× sur médiane de niche | faible confiance | moyen-élevé | illimitée | faible-moyen / faible |
| — | C08 Futurs et mégaprojets | 55 | 3,3× (chaîne non IA) ; 14× sur n = 2 | pas de donnée dédiée | faible | dizaines | moyen / faible-moyen |

### C03 — Échelles impossibles

- **Promesse** : « Tu vas sentir la vraie taille de X », avec une question par épisode (ex. « Pourquoi aucun animal terrestre ne dépasse 20 tonnes ? »).
- **Preuve de demande** : preuve de genre au niveau chaîne (MetaBallStudios, non IA, ≈ 2 M d'abonnés) [S8] ; aucun outlier récent mesuré.

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| à mesurer | MetaBallStudios | es/en | — | — | `tools/outliers.py channel @MetaBallStudios` | non mesuré | — |

- **RPM** : généraliste (France ≈ 2,29 $, `economics.md`, S15) ; niche science plus haute selon des panels (confiance moyenne).
- **Légitimité IA** : maximale. ≈ 90 % de rendu 3D procédural Blender (objets, bâtiments, planètes, sans humains), motion design pour les chiffres ; la valeur vient de l'explication, pas du modèle.
- **Risque politique** : faible sur le fond, mais **risque de gabarit** : une suite d'objets alignés d'une vidéo à l'autre ressemble à du contenu répétitif (constat 7). Chaque épisode doit porter une question, un arc et une structure propres.
- **Sérialité** : 100+ épisodes distincts (espace, vivant, ingénierie, nombres).
- **Coût unitaire** : faible (Blender EEVEE majoritaire, peu de génératif).

### C11 — Géographie et données animées

- **Promesse** : « Tu vas comprendre pourquoi cette frontière ou cette route existe », avec une carte qui bouge dès la 1re seconde.
- **Preuve de demande** : indices obtenus par une méthode non conforme (médiane de niche) ; leaders établis (Wendover, Half as Interesting, Geography Now) [S9] [S10].

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| They're Not British. They're Not Independent. So What Are They? | Geography Now | en | 2026-08-31 | 364 328 | médiane de niche de 4 vidéos (méthode non conforme, ADR-004) | indice 3,7 (non compté) | https://www.youtube.com/watch?v=SnXXIT610eU |
| à mesurer | Geography Now, Wendover Productions, Half as Interesting, RealLifeLore | en | — | — | `tools/outliers.py channel …` | non mesuré | — |

- **RPM** : entre généraliste et éducation ; pas de donnée dédiée (`economics.md`, questions ouvertes).
- **Légitimité IA** : élevée. La production est surtout du motion design et de la cartographie (Remotion, données ouvertes), sans visage et sans look IA ; la valeur est l'analyse.
- **Risque politique** : moyen. Frontières contestées et sujets géopolitiques : il faut une politique éditoriale explicite (sources, cartes officielles, neutralité).
- **Sérialité** : illimitée (pays, frontières, logistique, données).
- **Coût unitaire** : le plus faible des 12 (peu de GPU génératif).

### C02 — Comment on a construit…

- **Promesse** : « Tu vas voir, étape par étape, comment on a construit X avec les moyens de l'époque. »
- **Preuve de demande** : aucun ratio obtenu ; genre établi chez des chaînes non IA d'ingénierie (Real Engineering) [S11].

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| à mesurer | Real Engineering, History in 3D, Ancient Architects | en | — | — | `tools/outliers.py channel …` | non mesuré | — |

- **RPM** : éducation / ingénierie, supérieur au généraliste (confiance moyenne).
- **Légitimité IA** : très élevée. Chantiers, machines et structures en Blender procédural (plans larges, sans visages en gros plan), animations de principes mécaniques ; le génératif sert aux ambiances vivantes.
- **Risque politique** : faible. Il faut sourcer les hypothèses de construction et afficher le degré de certitude ; la reconstitution réaliste est divulguée [S1].
- **Sérialité** : 30-50 grands chantiers ; bien plus avec C07.
- **Coût unitaire** : faible-moyen.

### C09 — Terre profonde et temps géologique

- **Promesse** : « Tu vas voir à quoi ressemblait la Terre il y a X millions d'années, et pourquoi elle a changé. »
- **Preuve de demande** : indices obtenus par une méthode non conforme (médiane de 14 chaînes) ; plus de 10 chaînes quasi identiques sur le mécanisme « 4,5 milliards d'années ».

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| 4.5 Billion Years of Earth's History in JUST 1 Hour | Wild Horizons | en | 2026-03-24 | 2 839 655 | médiane de niche, 14 chaînes (méthode non conforme, ADR-004) | indice 5,5 (non compté) | https://www.youtube.com/watch?v=Me4hxOX8ULo |
| à mesurer | Wild Horizons, ReYOUniverse | en | — | — | `tools/outliers.py channel …` | non mesuré | — |

- **RPM** : éducation / science (`economics.md`).
- **Légitimité IA** : élevée. Paysages, volcans, océans et continents en Blender ; le génératif sert à la faune ancienne (point faible : créatures en gros plan).
- **Risque politique** : faible. Aucune personne réelle ; il faut suivre le consensus scientifique et afficher le degré de certitude.
- **Sérialité** : des dizaines d'épisodes, à condition de structurer des sous-arcs (ères, extinctions, climats) pour éviter la répétition.
- **Coût unitaire** : moyen.

### C07 — Mondes disparus (archéologie reconstituée)

- **Promesse** : « Tu vas marcher dans X tel qu'il était, et comprendre pourquoi il a disparu. »
- **Preuve de demande** : indices obtenus par une méthode non conforme, sur médiane de chaîne.

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| Khafre Pyramid SAR Scan ANALYSIS: LOST CITY or FAKE NEWS? | Ancient Architects | en | 2025-03-25 | 609 818 | médiane de 15 vidéos (méthode non conforme, ADR-004) | indice 7,9 (non compté) | https://www.youtube.com/watch?v=hh9sDs05s3c |
| à mesurer | Ancient Architects, History in 3D | en | — | — | `tools/outliers.py channel …` | non mesuré | — |

- **RPM** : éducation / histoire.
- **Légitimité IA** : très élevée. Villes et monuments en Blender (Poly Haven, reconstitution à partir de plans publiés), foules en plans larges ; divulgation systématique [S1].
- **Risque politique** : faible-moyen. La niche « histoire IA » est polluée par du contenu générique [S5] : sources et degré de certitude affichés, aucune pseudo-archéologie.
- **Sérialité** : des dizaines à des centaines d'épisodes (1 site = 1 à N épisodes).
- **Coût unitaire** : moyen.

### C04 — Scénarios scientifiques « et si »

- **Promesse** : « Tu vas voir ce qui se passerait vraiment si X, minute par minute. »
- **Preuve de demande** : un seul point de données (2023) ; genre reconnu (Underknown / *What If*) ; possible arbitrage linguistique en français (aucune chaîne FR identifiée, confiance faible).

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| à mesurer | What If (Underknown), RealLifeLore | en | — | — | `tools/outliers.py channel …` | non mesuré | — |

- **RPM** : généraliste à science.
- **Légitimité IA** : élevée. Scénarios manifestement hypothétiques en Blender (simulations physiques, destructions) ; la divulgation est souvent non requise pour une scène manifestement irréaliste [S1].
- **Risque politique** : faible-moyen. Il faut une rigueur scientifique sourcée et éviter le catastrophisme gratuit (garde-fous de MISSION §7).
- **Sérialité** : 30-50 épisodes.
- **Coût unitaire** : faible-moyen.

## Concepts écartés et pourquoi

| Concept | Raison principale |
|---|---|
| C05 Cosmos visualisé | Créneau dominé par des productions non IA de très haute qualité (Kurzgesagt, melodysheep) [S6] [S7] ; angle neuf 2/5. Peut entrer dans la chaîne « Échelles » comme saison. |
| C01 Une journée dans la vie de… | Exige des personnages et des visages récurrents : c'est le point faible du local, avec un risque de look IA. |
| C06 Catastrophes minute par minute | Publicité limitée sur les événements sensibles [S2], divulgation systématique, risque de ton. À reconsidérer quand les portes de conformité auront fait leurs preuves. |
| C12 Batailles historiques | Niche saturée (Kings and Generals, Epic History) et publicité limitée sur la guerre [S2] [S17]. |
| C10 Fiction analog horror | Fiction qui peut passer pour réelle, public jeune ; un indice repose sur un personnage jeunesse protégé [S18] [S12]. |
| C08 Futurs et mégaprojets | Niche la plus saturée de villes futuristes générées sans récit ; seule preuve solide sur une chaîne non IA. |

## Recommandation pour les chaînes A et B

| Option | Chaîne A | Chaîne B | Pour | Contre |
|---|---|---|---|---|
| **1 (recommandée)** | « Civilisations reconstruites » = C02 + C07 | « Échelles de l'espace et du temps » = C03 + C09 (+ C05 en saison) | les deux concepts les mieux adaptés au rendu Blender procédural ; audiences distinctes (histoire / science) ; séries longues | même famille de production : les bibles visuelles doivent être nettement différentes pour passer le contrôle de diversité inter-chaînes |
| 2 | « Civilisations reconstruites » = C02 + C07 | C11 Géographie et données | coût minimal ; grammaire de plans différente (motion design), ce qui diversifie le risque de production | concurrence installée ; sujets géopolitiques sensibles |

**Langue** : décision humaine (NEEDS_HUMAN H3). D'un côté, l'anglais : audience plus large et RPM des États-Unis ≈ 2,5 fois celui de la France (`economics.md`). De l'autre, le français : arbitrage linguistique possible sur C04 (confiance faible). Option médiane : master anglais + piste audio française (la fonction se gère dans Studio, sans API connue : `apis.md`).

## Écarts avec MISSION §4

| Affirmation de la mission | Verdict | Sources | Correction proposée |
|---|---|---|---|
| §9 : « 6 concepts classés avec preuve de demande (≥ 2 outliers récents) » | non vérifiable dans cette session : aucune méthode conforme sans clé d'API | [S13] [S14] [S15] | ADR-004 : mesure par l'API YouTube Data ; la phase 0 reste ouverte sur ce seul critère |
| §2 : l'IA surclasse la caméra sur les reconstitutions historiques et les échelles impossibles | confirmé comme positionnement : les niches retenues sont celles où la caméra ne peut rien filmer | [S4] [S5] | aucune |
| §4 : les fermetures massives de chaînes IA en 2026 visent le contenu générique | nuancé : les niches citées sont des niches de volume ; l'histoire générique est déjà signalée | [S5] [S16] | ajouter au contrôle anti-gabarit une vigilance « histoire générique » |

## Questions ouvertes

- Ratios mesurés (API) pour les listes de chaînes ci-dessus : `python3 tools/outliers.py channel <handles> --months 18 --min-ratio 3` dès que `YOUTUBE_API_KEY` est disponible. Le classement peut s'inverser.
- RPM réels des niches ingénierie et géographie : non trouvés (`economics.md`).
- Existence de concurrents francophones sur C02, C04, C07 et C09 : non mesurée (recherche web épuisée pendant la session).

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | Aide YouTube — Disclosing use of altered or synthetic content | https://support.google.com/youtube/answer/14328491 | s.d. | 2026-09-28 | officiel | élevée |
| S2 | Aide YouTube — Advertiser-friendly content guidelines (événements sensibles) | https://support.google.com/youtube/answer/6162278 | 2022-03-23 | 2026-09-28 | officiel | élevée |
| S3 | Blog YouTube — YouTube Partner Program updates (2027) | https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/ | 2026-08-10 | 2026-09-28 | officiel | élevée |
| S4 | Kapwing — AI Slop Report: The Global Rise of Low-Quality AI Videos | https://www.kapwing.com/blog/ai-slop-report-the-global-rise-of-low-quality-ai-videos/ | 2025 | 2026-09-28 | données | moyenne |
| S5 | 404 Media — AI-Generated 'Boring History' Videos Are Flooding YouTube | https://www.404media.co/ai-generated-boring-history-videos-are-flooding-youtube-and-drowning-out-real-history/ | 2025-09-03 | 2026-09-28 | presse | moyenne |
| S6 | Wikipédia — Kurzgesagt – In a Nutshell | https://en.wikipedia.org/wiki/Kurzgesagt_%E2%80%93_In_a_Nutshell | 2026-09-10 | 2026-09-28 | données | moyenne |
| S7 | Wikipédia — John D. Boswell (melodysheep) | https://en.wikipedia.org/wiki/John_D._Boswell | 2026-02-16 | 2026-09-28 | données | moyenne |
| S8 | Wikitubia — MetaBallStudios | https://youtube.fandom.com/wiki/MetaBallStudios | s.d. | 2026-09-28 | données | faible |
| S9 | Wikipédia — Sam Denby (Wendover Productions, Half as Interesting) | https://en.wikipedia.org/wiki/Sam_Denby | 2026-09-06 | 2026-09-28 | données | moyenne |
| S10 | Wikipédia — Geography Now | https://en.wikipedia.org/wiki/Geography_Now | 2026-08-10 | 2026-09-28 | données | moyenne |
| S11 | Wikipédia — Real Engineering | https://en.wikipedia.org/wiki/Real_Engineering | 2026-01-20 | 2026-09-28 | données | moyenne |
| S12 | Tubefilter — It's an analog horror Halloween on YouTube | https://www.tubefilter.com/2024/10/31/its-an-analog-horror-halloween-on-youtube/ | 2024-10-31 | 2026-09-28 | presse | moyenne |
| S13 | YouTube — Ancient Architects, « Khafre Pyramid SAR Scan ANALYSIS » (indice, méthode non conforme) | https://www.youtube.com/watch?v=hh9sDs05s3c | 2025-03-25 | 2026-09-28 | données | faible |
| S14 | YouTube — Wild Horizons, « 4.5 Billion Years of Earth's History in JUST 1 Hour » (indice) | https://www.youtube.com/watch?v=Me4hxOX8ULo | 2026-03-24 | 2026-09-28 | données | faible |
| S15 | YouTube — Geography Now, « They're Not British. They're Not Independent… » (indice) | https://www.youtube.com/watch?v=SnXXIT610eU | 2026-08-31 | 2026-09-28 | données | faible |
| S16 | OutlierKit — YouTube's AI Slop Crackdown (2026) | https://outlierkit.com/resources/youtube-ai-slop-crackdown-2026/ | 2026 | 2026-09-28 | praticien | moyenne |
| S17 | YouTube — Kings and Generals, « War of the Spanish Succession: All Battles and Events » (indice) | https://www.youtube.com/watch?v=5ij0tDYhIhg | 2026-09-13 | 2026-09-28 | données | faible |
| S18 | YouTube — Kris Archives, « The Cat in the Hat (Analog Horror) » (indice) | https://www.youtube.com/watch?v=MNJhZmC3Bhk | 2026-07-25 | 2026-09-28 | données | faible |
