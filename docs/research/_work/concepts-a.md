# Concepts de chaîne — lot A (C01-C06)

> Consulté le : 2026-09-28 · Auteur : researcher · Version : 1 · Portée : 6 concepts candidats du lot A pour `docs/research/channel-concepts.md` (à fusionner avec le lot B). Note de travail, `docs/research/_work/`.

**Note méthodologique (à lire avant les tableaux « Preuve de demande »).** YouTube bloque l'accès direct non authentifié à ses pages (captcha anti-bot rencontré via `curl` et `WebFetch` sur `youtube.com/watch`) : impossible d'ouvrir une fiche vidéo et d'y lire vues/date à la volée. Les outils tiers habituels (Social Blade, Playboard, Wikitubia) ont renvoyé des erreurs 402/403/429 à l'ouverture directe. Le budget de recherche web de la session (partagé avec les autres sous-agents de la phase 0) s'est épuisé en cours de rédaction, avant d'avoir pu vérifier tous les concepts avec la même profondeur. Conséquence : **aucun des 6 concepts ne dispose d'un outlier vidéo isolé avec ratio vues/médiane ≥ 3× entièrement vérifié et chiffré** au sens strict demandé. Ce qui suit est donc la meilleure preuve *indirecte* rassemblée (existence du format, taille de chaîne, vues cumulées, confirmées par au moins une page ouverte ou un résultat de recherche vu), avec une confiance explicitement dégradée en conséquence. C'est un résultat en soi, à traiter comme tel plutôt qu'à masquer.

## Récapitulatif et recommandation

| # | Concept | Note /100 | RPM (repère, inférence) | Risque politique | Sérialité (épisodes plausibles) | Coût unitaire (long 10 min / short 40 s) |
|---|---|---|---|---|---|---|
| C01 | Une journée dans la vie de… | 67 | FR ~1,6-2,3 $ / US ~5,4 $ pour 1 000 vues en long ; Shorts ~0,03-0,20 $ (base skill §12) ; pas d'ajustement niche établi | Moyen | ~40-60 | Élevé / Moyen |
| C02 | Comment on a construit… | 71 | idem base ; inférence légèrement positive (éducatif/ingénierie = brand-safe) | Faible-moyen | ~30-50 | Faible-moyen / Faible |
| C03 | Échelles impossibles | 76 | idem base ; neutre | Faible | 100+ | Faible / Faible |
| C04 | Et si… (scénarios) | 69 | idem base ; neutre à légèrement positif | Faible-moyen | ~30-50 | Faible-moyen / Faible |
| C05 | Cosmos visualisé | 72 | idem base ; neutre à légèrement positif (sponsoring science observé chez les gros acteurs, non chiffré) | Faible | ~40-60 | Faible / Faible |
| C06 | Catastrophes minute par minute | 71 | idem base, mais probablement réduit sur une partie des épisodes (politique « sensitive events », S16) | Élevé | ~40-60, rythme de publication plus lent | Moyen / Faible-moyen |

**Recommandation argumentée (top 3 du lot A) : C03 > C05 > C02.**
- **C03 (Échelles impossibles)** cumule le meilleur score, le risque le plus faible et le coût le plus faible : presque 100 % rendu 3D procédural Blender, aucun visage, aucun évènement réel à altérer — exactement le point fort de la stack décrite en MISSION §6 principe 6. Le genre a une preuve de demande forte au niveau chaîne (MetaBallStudios, source S11, faible confiance faute d'accès direct mais cohérente avec la notoriété publique du format).
- **C05 (Cosmos visualisé)** partage les mêmes atouts (peu de visages, données NASA/ESA du domaine public disponibles, rendu procédural dominant) et bénéficie de la preuve de genre la plus solide obtenue dans cette note : Kurzgesagt (S2, 25,5 M abonnés, 3,84 Md vues, mise à jour datée du 10/09/2026) et melodysheep (S1, une vidéo à 88 054 235 vues au 29/12/2022) montrent qu'un contenu cosmos/science bien exécuté peut devenir massif — même si aucune de ces preuves n'est un outlier récent au sens strict.
- **C02 (Comment on a construit…)** complète le trio : audience la plus universellement adressable (15/15 sur ce critère), sujets peu porteurs de visages en gros plan (grues, structures, foules lointaines), et un risque de conformité limité si les faits d'ingénierie sont sourcés.
- **C04** talonne de près (69) et reste une bonne 4ᵉ chaîne possible. **C01** est pénalisé par son besoin de personnages et de visages animés en gros plan (point faible confirmé du local, MISSION §4/§6), donc un coût et un risque « AI look » plus élevés. **C06** a la demande de genre la plus tangible mesurée ici (Fascinating Horror, S9/S10, ~1,46 M abonnés et ~3,98 M vues/30 j sur exactement ce mécanisme) mais porte le risque politique le plus élevé (évènements sensibles, morts réelles, publicité potentiellement limitée — S16) : à garder en réserve pour une chaîne ultérieure, une fois les portes de conformité éprouvées sur des sujets moins sensibles.

Aucun concept n'a de critère éliminatoire noté à 0 ; C06 mérite néanmoins une vigilance particulière sur la conformité (poids 5, note 2/5 ici).

---

### C01 — Une journée dans la vie de…

**1. Promesse et épisodes.** Promesse type : « Tu vas vivre une journée complète dans la peau de [personnage historique], heure par heure. »
Longs (≤ 50 car.) :
1. Légionnaire romain : une journée complète
2. Paysan médiéval : du lever au couvre-feu
3. Bâtisseur de pyramide : un jour à Gizeh
4. Mineur de sel à Wieliczka, XVIIIe siècle
5. Gladiateur : les heures avant l'arène

Shorts :
- 3 minutes dans la vie d'un légionnaire romain
- Le repas d'un paysan médiéval en 40 secondes

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| AI-Generated: A Day in the Life of a Roman Legionary | non identifiée (nom de chaîne non extrait) | EN | 2025-04-18 | ND — page YouTube non accessible (captcha) | ND | ND | https://www.youtube.com/watch?v=lhukeuglV-g |
| A Day in the Roman Legion - AI Historical Recreation | non identifiée | EN | 2025-10-14 | ND | ND | ND | https://www.youtube.com/watch?v=nos4MbNPx-Q |

Verdict : **outlier chiffré non établi.** Seule preuve indirecte : le format « journée dans la vie, IA » existe et se publie activement depuis avril 2025 (2 occurrences distinctes trouvées en une recherche), et la chaîne d'histoire IA « Chloe vs. History » (259 000 abonnés, « plusieurs vidéos à plusieurs millions de vues » sans détail chiffré, source S5, confiance faible) confirme qu'une chaîne d'histoire tournée vers l'IA peut atteindre une audience significative — mais ce n'est pas le même sous-format (jours-dans-la-vie vs vulgarisation) et aucun ratio n'a pu être calculé. Confiance globale : **faible**.

**3. Concurrence.** « Chloe vs. History » (IA, EN, 259 000 abonnés, S5) — chaîne IA généraliste histoire, pas uniquement « jour dans la vie ». TED-Ed « A day in the life of a Roman soldier » (non-IA, animation classique, éducatif, très ancien format scolaire). Plusieurs canaux de très petite taille identifiés dans les recherches (les deux vidéos ci-dessus), sans abonnés vérifiés — signe d'un **créneau naissant, pas encore saturé par de grosses chaînes IA identifiées**, à la différence de l'anime ou du religieux (S6, S7 : les chaînes « slop » sanctionnées en 2026 sont sur Dragon Ball, contenu biblique, animaux — aucune sur l'histoire immersive).

**4. RPM estimé.** Pas de donnée niche spécifique trouvée. Base skill §12 : FR ~1,6-2,3 $, US ~5,4 $ / 1 000 vues en long ; Shorts ~0,03-0,20 $ / 1 000 (panels, sept. 2026, confiance moyenne selon le skill). Aucun ajustement fiable identifiable pour ce sous-format : neutre.

**5. Légitimité IA/procédurale.** Grammaire de plans réaliste dès lors que : archives et reconstitutions Blender pour les décors (camp romain, champs, forge), plans larges et silhouettes pour les foules/scènes d'action, motion design pour les cartes et repères temporels (« 6h », « midi »), et un nombre **limité** de plans de personnage animé (le point faible identifié en MISSION §6 : visages en gros plan). Valeur ajoutée vs slop : narration à hauteur d'un personnage précis avec un enjeu par heure (faim, discipline, danger), pas un diaporama de « faits historiques ». Risque : si le budget GPU dérape vers trop de plans de personnage en gros plan pour tenir l'immersion, le point faible du local (visages) devient visible.

**6. Risque politique.** **Moyen.** Reconstitution réaliste d'un individu générique (pas une personne réelle nommée) mais d'un évènement historique plausible → scène réaliste pouvant passer pour un document d'époque : `containsSyntheticMedia` quasi systématique (S17, officiel). Risque de désinformation historique si des détails du quotidien sont inventés et présentés comme des faits sans le signaler (checklist skill §9). Pas de sujet santé/finance/droit, donc pas de restriction avatar (skill §7.5).

**7. Sérialité.** Large : dizaines de métiers et statuts par époque (légionnaire, paysan, moine copiste, marin viking, artisan verrier, mineur, chevalier, ouvrier d'usine industrielle…). Structure de saison plausible : une saison = une époque (Antiquité, Moyen Âge, Renaissance, Révolution industrielle), chaque épisode = un métier/statut. Estimation : ~40-60 épisodes distincts avant d'épuiser le filon évident.

**8. Coût unitaire qualitatif.** Long 10 min : **élevé** — nécessite le plus de plans avec mouvement de personnage identifiable dans la durée (marche, gestes, visage) parmi les 6 concepts, donc la part de génération vidéo locale (point faible) est la plus grande. Short 40 s : **moyen** — un seul décor/action suffit, réduit la charge.

**9. Note /100 (grille skill §2 étape 2).**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 2 | Format confirmé actif (2 vidéos 2025) mais aucun chiffre de vues ni ratio obtenu |
| Packaging (élim.) | 20 | 4 | Titre court possible, miniature = personnage + objet d'époque, lisible ; risque « AI look » sur le visage en vignette |
| Audience adressable | 15 | 4 | Curiosité large pour le quotidien historique, compréhensible en une phrase |
| Angle neuf | 15 | 3 | Mécanisme déjà repris par plusieurs petites chaînes IA depuis 2025 |
| Intensité | 10 | 3 | Contraintes concrètes mais pas d'enjeu extrême par défaut |
| Livrable en 30 s (élim.) | 10 | 4 | Une scène immersive peut ouvrir la vidéo dès la 1re seconde |
| Durée de vie | 5 | 5 | Sujet evergreen |
| Conformité (élim.) | 5 | 3 | Divulgation quasi systématique, vigilance désinformation, gros plans à limiter |
| **Total** | | | **67/100** |

---

### C02 — Comment on a construit…

**1. Promesse et épisodes.** Promesse type : « Tu vas comprendre, étape par étape, comment [structure] a été construite sans les outils modernes. »
Longs :
1. Comment on a construit la Grande Pyramide
2. Comment on a construit Notre-Dame de Paris
3. Comment on a construit le Colisée
4. Comment on a construit les aqueducs romains
5. Comment on a construit le canal de Panama

Shorts :
- La Grande Pyramide construite en 40 secondes
- Comment tenaient les aqueducs romains ?

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| What The Pyramids Of Egypt REALLY Looked Like When They Were New (AI Reconstruction) | non identifiée | EN | s.d. (2026, vu en résultat de recherche) | ND | ND | ND | https://www.youtube.com/watch?v=Em39pDl719g |
| AI Just Found a New Answer to How the Egyptian Pyramids Were Built | non identifiée | EN | s.d. (~3 semaines avant consultation, 2026) | ND | ND | ND | (URL vue en résultat de recherche, non ouverte : titre seul) |

Verdict : **outlier chiffré non établi.** Plusieurs vidéos IA sur « comment les pyramides ont été construites » publiées courant 2026 confirment un intérêt actif pour le sujet côté créateurs, mais aucune vue ni comparaison à une médiane de chaîne n'a pu être vérifiée. Le mécanisme « comment c'est construit » est en revanche un genre documentaire très établi en format non-IA (voir concurrence) : preuve de demande générale forte, preuve d'un outlier IA récent chiffré absente. Confiance : **faible** sur le chiffrage, **moyenne** sur l'existence du marché.

**3. Concurrence.** Format « comment c'est construit » très occupé en anglais par des chaînes de vulgarisation d'ingénierie non-IA (voix réelle + schémas/stock), et en français par des chaînes d'histoire classiques (présentateur face caméra, pas IA). Sur le créneau spécifiquement IA/3D, seules de petites chaînes isolées identifiées ci-dessus (aucun abonné vérifié). Pas de signe de saturation par de l'« AI slop » sur ce mécanisme précis dans les sources consultées (S6, S7 : les chaînes sanctionnées sont sur d'autres niches).

**4. RPM estimé.** Base skill §12 (FR ~1,6-2,3 $ / US ~5,4 $ / 1 000 vues long ; Shorts ~0,03-0,20 $). Inférence : contenu éducatif/ingénierie généralement classé « brand-safe » par les annonceurs → RPM probablement à la borne haute de la fourchette générale, sans donnée chiffrée propre trouvée (confiance faible, inférence).

**5. Légitimité IA/procédurale.** C'est le concept le plus naturellement « Blender procédural » du lot A après C03 : structures, échafaudages, leviers, rampes, physique de simulation (blocs qui glissent, poulies) — exactement l'usage visé par MISSION §6 principe 6. Les humains n'apparaissent qu'en silhouettes/plans larges (ouvriers de chantier), sans nécessité de gros plan sur un visage récurrent. Valeur ajoutée vs slop : démonstration physique crédible (simulation) plutôt qu'un montage d'images IA statiques avec voix off générique.

**6. Risque politique.** **Faible à moyen.** Peu de personnes réelles nommées à représenter ; le risque principal est la **désinformation historique** si une hypothèse de construction contestée (ex. théories alternatives sur les pyramides) est présentée comme un fait établi sans nuance — point de vigilance explicite du skill (§7.4, « vrai = vrai ») et de la checklist. Divulgation `containsSyntheticMedia` nécessaire pour les reconstitutions réalistes de lieux réels (S17).

**7. Sérialité.** Large : pyramides (Gizeh, Chichén Itzá, Teotihuacán), cathédrales (Notre-Dame, Cologne, Sagrada Família historique), Colisée, aqueducs, Grande Muraille, canal de Panama/Suez, tour Eiffel, barrage Hoover, Cité interdite, Angkor Wat, Machu Picchu… Estimation : ~30-50 épisodes distincts. Saison plausible = un ensemble de structures par civilisation ou par période.

**8. Coût unitaire qualitatif.** Long 10 min : **faible à moyen** — dominante Blender/motion design, peu de génération vidéo humaine. Short 40 s : **faible**.

**9. Note /100.**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 2 | Sujet actif côté créateurs IA en 2026 mais aucun chiffre vérifié |
| Packaging (élim.) | 20 | 4 | Titre « Comment on a construit X » très lisible, miniature = structure emblématique |
| Audience adressable | 15 | 5 | Sujets universellement identifiables (pyramides, cathédrales) |
| Angle neuf | 15 | 3 | Mécanisme saturé en format classique ; le rendu 3D procédural différencie |
| Intensité | 10 | 3 | Enjeu technique réel, peu d'urgence dramatique par défaut |
| Livrable en 30 s (élim.) | 10 | 4 | La structure finie peut être montrée dès l'ouverture |
| Durée de vie | 5 | 5 | Evergreen |
| Conformité (élim.) | 5 | 4 | Peu de visages, vigilance sur les faits d'ingénierie contestés |
| **Total** | | | **71/100** |

---

### C03 — Échelles impossibles / comparaisons de taille

**1. Promesse et épisodes.** Promesse type : « Tu vas voir à quel point [chose] est petite ou immense face à [chose] — à l'échelle. »
Longs :
1. L'univers, du plus petit au plus grand
2. Fosse des Mariannes contre l'Everest
3. Tous les plus hauts bâtiments du monde
4. Les créatures les plus énormes de l'histoire
5. 1 million contre 1 milliard : ce que ça change

Shorts :
- La Terre à côté du plus gros trou noir connu
- Combien de fois la Terre tient dans le Soleil ?

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| (ensemble de la chaîne — pas de vidéo isolée vérifiée) | MetaBallStudios | ES/EN (visuel, quasi muet) | s.d. (~2M abonnés, 554M vues cumulées, 239 vidéos ; page consultée via résultat de recherche) | 554 M vues cumulées / 239 vidéos ≈ 2,3 M vues/vidéo en moyenne (calcul dérivé) | moyenne de chaîne = ≈2,3 M (méthode : total vues ÷ nb vidéos, Wikitubia) | ND (pas de vidéo isolée comparée) | https://youtube.fandom.com/wiki/MetaBallStudios |

Verdict : **outlier chiffré non établi au sens strict** (pas de vidéo isolée ≥ 3× une médiane connue), mais **preuve de genre la plus solide obtenue dans cette note à l'échelle d'une chaîne** : un canal consacré presque exclusivement aux comparaisons de taille en 3D cumule ~2 millions d'abonnés et une moyenne de ~2,3 M vues par vidéo sur 239 vidéos (donnée dérivée d'un calcul simple à partir de deux chiffres publiés, pas inventée). Publication de la source non datée précisément (page wiki, consultée aujourd'hui) : confiance **faible à moyenne**, et hors fenêtre de fraîcheur stricte demandée (aucune date de vidéo récente confirmée).

**3. Concurrence.** MetaBallStudios (non-IA au sens strict — modélisation 3D manuelle, ES, ~2 M abonnés, S11) domine ce créneau depuis 2016. Format très repris en Shorts de bas de gamme : le rapport Kapwing (S6) chiffre à 21-33 % la part de Shorts IA/« brainrot » dans les recommandations faites à un compte neuf fin 2025, sans isoler la comparaison de taille — indice de saturation générale du format court plutôt qu'une preuve spécifique à ce mécanisme.

**4. RPM estimé.** Base skill §12, neutre : rien dans les sources consultées n'indique un écart pour ce format par rapport à la moyenne générale.

**5. Légitimité IA/procédurale.** Le concept le mieux aligné avec MISSION §6 principe 6 : quasi 100 % rendu 3D procédural Blender (échelles, empilements, caméra qui recule), aucun visage humain nécessaire, aucun évènement réel à reconstituer. Valeur ajoutée vs slop : narration et choix de comparaisons pertinents (mise en contexte, pas juste un défilé d'objets), musique et rythme travaillés — le rendu brut est déjà « legitimate » techniquement, la différenciation se joue sur l'écriture.

**6. Risque politique.** **Faible.** Pas de personne réelle représentée, pas d'évènement réel altéré : peu ou pas de cas de divulgation synthétique au sens de S17 (scènes non réalistes/abstraites). Risque principal : exactitude scientifique des chiffres utilisés (à sourcer systématiquement, cf. `fact_checker`).

**7. Sérialité.** Très large, quasi illimitée : échelles d'univers, de profondeurs, de bâtiments, de créatures, de vitesses, de durées, de forces, de nombres. Structure de saison par « famille » de comparaison (espace, biologie, ingénierie, temps). Estimation : 100+ épisodes plausibles sans redite flagrante si le sous-angle change à chaque fois.

**8. Coût unitaire qualitatif.** Long 10 min : **faible**. Short 40 s : **faible**. Le concept le moins coûteux en GPU générative du lot A.

**9. Note /100.**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 3 | Preuve de genre forte au niveau chaîne (S11) mais pas d'outlier vidéo chiffré et récent |
| Packaging (élim.) | 20 | 4 | Archétype « A contre B » très lisible en miniature |
| Audience adressable | 15 | 5 | Compréhensible sans aucun prérequis culturel ou linguistique |
| Angle neuf | 15 | 2 | Mécanisme très copié, y compris en Shorts IA bas de gamme (S6) |
| Intensité | 10 | 4 | Effet « wow » fort, chiffres extrêmes |
| Livrable en 30 s (élim.) | 10 | 5 | La comparaison spectaculaire s'affiche dès l'ouverture |
| Durée de vie | 5 | 4 | Tendance installée depuis 2016, pas de signe d'essoufflement mais très copiée |
| Conformité (élim.) | 5 | 5 | Aucune personne réelle, aucun évènement réel à altérer |
| **Total** | | | **76/100** |

---

### C04 — Scénarios scientifiques « et si »

**1. Promesse et épisodes.** Promesse type : « Tu vas voir, minute par minute, ce qui se passerait vraiment si [évènement impossible] arrivait. »
Longs :
1. Et si la Lune disparaissait cette nuit ?
2. Et si la Terre arrêtait de tourner d'un coup ?
3. Et si tous les glaciers fondaient d'un coup ?
4. Et si le Soleil s'éteignait une heure ?
5. Et si on creusait jusqu'au centre de la Terre ?

Shorts :
- Et si la gravité doublait pendant 10 secondes ?
- Et si l'air disparaissait pendant 5 secondes ?

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| What would happen to life as we know it if the moon disappeared? | Insider Tech (via UniladTech) | EN | s.d., article daté 2023-12-07 | « plus de 1,5 million » (chiffre arrondi de l'article, pas de nombre exact) | ND — médiane de la chaîne non vérifiée | ND | https://www.uniladtech.com/science/space/frightening-video-shows-fate-of-life-on-earth-without-moon-664427-20231207 |

Verdict : **outlier chiffré non établi.** Le seul point de donnée trouvé (1,5 M de vues, arrondi, via un article tiers de 2023) est trop ancien pour la fenêtre demandée (publié avant 2024) et ne permet aucun calcul de ratio faute de médiane de chaîne. Le format « What If » est confirmé comme un genre installé (Underknown, prix Webby 2020 pour sa série *What If*, S4) mais sans chiffre exploitable aujourd'hui. C'est le concept où la preuve de demande rassemblée est **la plus faible des six**. Confiance : **faible**.

**3. Concurrence.** Underknown / *What If* (non-IA priori, format documentaire scientifique, EN, reconnu par un prix Webby 2020 — S4, aucun chiffre d'audience trouvé aujourd'hui). RealLifeLore (grande chaîne anglophone connue pour ce mécanisme, cartes animées + voix off — taille non revérifiée aujourd'hui, page Wikipédia dédiée introuvable au moment de la recherche). Aucune chaîne francophone identifiée sur ce mécanisme précis dans les sources consultées : indice (faible confiance, faute de recherche exhaustive) d'un possible **arbitrage linguistique** favorable côté FR, comme le suggère le skill §2 étape 2.

**4. RPM estimé.** Base skill §12, neutre à légèrement positif : sujet scientifique généralement considéré brand-safe, sans donnée chiffrée propre trouvée (inférence, confiance faible).

**5. Légitimité IA/procédurale.** Mix Blender procédural (simulations physiques : eau, glace, gravité, rotation) + motion design/dataviz pour les mécanismes abstraits + quelques plans d'ambiance humaine évitables (villes, foules en plan large, jamais de visage récurrent en gros plan). Valeur ajoutée vs slop : rigueur des simulations physiques plutôt qu'un simple montage d'images spectaculaires sans base scientifique.

**6. Risque politique.** **Faible à moyen.** Le cadre est explicitement hypothétique/fictionnel (« et si »), ce qui réduit le risque de confusion avec un fait réel (le skill distingue fiction annoncée et évènement réel altéré, §7.4/§7.8). Risque principal : désinformation scientifique si les conséquences physiques présentées ne sont pas sourcées (fact_checker obligatoire).

**7. Sérialité.** Large : Lune, rotation terrestre, champ magnétique, gravité, atmosphère, océans, Soleil, espèces disparues, etc. Estimation : ~30-50 épisodes distincts avant redite.

**8. Coût unitaire qualitatif.** Long 10 min : **faible à moyen** (simulations physiques Blender dominantes, quelques plans d'ambiance). Short 40 s : **faible**.

**9. Note /100.**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 2 | Genre reconnu (prix Webby) mais aucun chiffre récent vérifié, seul point de donnée trouvé daté 2023 |
| Packaging (élim.) | 20 | 4 | Formule « Et si… » très lisible, miniature = scène spectaculaire ou avant/après |
| Audience adressable | 15 | 4 | Large mais légèrement plus « curiosité scientifique » que grand public pur |
| Angle neuf | 15 | 3 | Mécanisme repris par de grosses chaînes anglophones établies |
| Intensité | 10 | 4 | Scénarios catastrophiques par construction |
| Livrable en 30 s (élim.) | 10 | 4 | La conséquence choc peut ouvrir la vidéo |
| Durée de vie | 5 | 4 | Evergreen, quelques sujets liés à l'actualité scientifique |
| Conformité (élim.) | 5 | 4 | Cadre hypothétique assumé, vigilance sur la rigueur scientifique |
| **Total** | | | **69/100** |

---

### C05 — Cosmos visualisé

**1. Promesse et épisodes.** Promesse type : « Tu vas voir, à l'échelle, [objet ou phénomène cosmique] comme jamais montré. »
Longs :
1. Voyage jusqu'aux confins du système solaire
2. À l'intérieur d'un trou noir
3. La mort du Soleil, dans 5 milliards d'années
4. Combien de temps pour atteindre Mars ?
5. La Voie lactée, de la Terre à sa périphérie

Shorts :
- La taille réelle de la Voie lactée
- Ce que verrait un astronaute près d'un trou noir

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| Timelapse of the Future: A Journey to the End of Time | melodysheep | EN | 2019-03-20 (hors fenêtre de fraîcheur demandée) | 88 054 235 vues au 2022-12-29 (Wikipédia) | Chaîne : ~3,2 M abonnés / ~432 M vues cumulées (résultat de recherche, non daté précisément) ⇒ moyenne dérivée ≈ hors calcul fiable (nb de vidéos non connu) | ND — médiane de chaîne non calculable avec les données obtenues | https://en.wikipedia.org/wiki/Timelapse_of_the_Future |
| The Coronavirus Explained & What You Should Do | Kurzgesagt | EN | 2020-03 | 89 M+ vues (Wikipédia, page consultée 2026-09-28) | Chaîne : 25,5 M abonnés / 3,84 Md vues cumulées, mise à jour datée 2026-09-10 (Wikipédia) | ND — médiane de chaîne non calculable (nb de vidéos non connu) | https://en.wikipedia.org/wiki/Kurzgesagt_%E2%80%93_In_a_Nutshell |

Verdict : **outlier chiffré au sens strict non établi** — les deux vidéos ci-dessus ont des vues exactes et sourcées, mais (a) elles sont anciennes (2019 et 2020, bien avant la fenêtre du 2025-03-28 voire 2024), et (b) la médiane de vues de chaque chaîne n'a pas pu être calculée (nombre de vidéos par chaîne non obtenu). Ce sont en revanche des **preuves de genre exceptionnellement solides** : deux chaînes de vulgarisation cosmos/science, sur ce mécanisme précis, cumulent plusieurs dizaines de millions d'abonnés et des vidéos individuelles à ~90 M de vues chacune. Confiance sur les chiffres cités : **moyenne** (sources ouvertes directement, chiffres précis) ; confiance sur la validité en tant qu'« outlier » au sens de la définition demandée : **faible** (pas récent, pas de ratio calculé).

**3. Concurrence.** Kurzgesagt (non-IA, animation 2D soignée, EN doublé en plusieurs langues, 25,5 M abonnés / 3,84 Md vues — S2, confiance moyenne) ; melodysheep (non-IA, montage/2,5D + musique, EN, ~3,2 M abonnés / ~432 M vues — S1, confiance faible sur les chiffres de chaîne non datés) ; the Infographics Show (non-IA, animation 2D, EN, 8 M abonnés selon une référence datée 2020 — S3, confiance faible, chiffre ancien) couvre occasionnellement l'espace parmi d'autres sujets. Aucune grosse chaîne IA identifiée sur ce créneau précis dans les recherches faites : **créneau dominé par des productions non-IA de très haute qualité**, ce qui relève la barre de packaging/écriture plutôt que la barre technique.

**4. RPM estimé.** Base skill §12, neutre à légèrement positif (inférence, confiance faible) : la présence de sponsors récurrents chez les grosses chaînes science observée de notoriété publique n'a pas été chiffrée dans les sources ouvertes aujourd'hui.

**5. Légitimité IA/procédurale.** Très bon alignement MISSION §6 : rendu procédural Blender pour les orbites, échelles et simulations physiques, plus des données/images du domaine public NASA/ESA (mentionnées dans le brief), quasi aucun visage humain nécessaire. Valeur ajoutée vs slop : précision scientifique des échelles et trajectoires (calculs réels plutôt qu'esthétique générique), sourçage systématique des données.

**6. Risque politique.** **Faible.** Pas de personne réelle, pas d'évènement réel à altérer dans l'immense majorité des sujets (sauf reconstitution d'une mission spatiale réelle précise, auquel cas divulgation `containsSyntheticMedia` recommandée par prudence). Risque principal : exactitude scientifique, mais catégorie considérée par la plateforme comme standard/non sensible.

**7. Sérialité.** Large : système solaire (planètes, lunes, astéroïdes), trous noirs, étoiles (naines, géantes, supernovae), galaxies, exoplanètes, missions spatiales réelles. Estimation : ~40-60 épisodes distincts.

**8. Coût unitaire qualitatif.** Long 10 min : **faible** (procédural + archives NASA/ESA dominants). Short 40 s : **faible**.

**9. Note /100.**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 3 | Preuve de genre exceptionnelle (Kurzgesagt, melodysheep) mais ancienne et non ramenée à un ratio |
| Packaging (élim.) | 20 | 4 | Image céleste spectaculaire en miniature, titre clair |
| Audience adressable | 15 | 4 | Curiosité universelle pour l'espace |
| Angle neuf | 15 | 2 | Créneau très occupé par des chaînes non-IA de très haute qualité |
| Intensité | 10 | 4 | Échelles de temps et d'espace extrêmes |
| Livrable en 30 s (élim.) | 10 | 4 | Image spectaculaire dès l'ouverture |
| Durée de vie | 5 | 5 | Totalement evergreen |
| Conformité (élim.) | 5 | 5 | Données du domaine public, pas de personnes réelles |
| **Total** | | | **72/100** |

---

### C06 — Catastrophes reconstituées minute par minute

**1. Promesse et épisodes.** Promesse type : « Tu vas revivre, minute par minute, les heures qui ont précédé [catastrophe]. »
Longs :
1. Titanic : les 160 dernières minutes
2. Pompéi : les 18 heures de l'éruption
3. Hindenburg : les 37 secondes du crash
4. Tchernobyl : la nuit du 26 avril 1986
5. Notre-Dame : les heures de l'incendie

Shorts :
- Les 37 secondes du crash du Hindenburg
- Pompéi : la dernière heure avant l'éruption

**2. Preuve de demande.**

| Vidéo | Chaîne | Langue | Publiée | Vues | Médiane ou moyenne de la chaîne (méthode) | Ratio | URL |
|---|---|---|---|---|---|---|---|
| (ensemble récent de la chaîne — pas de vidéo isolée vérifiée) | Fascinating Horror | EN | Chaîne active depuis 2019-01-17 ; volume mesuré sur les 30 derniers jours au 2026-09-28 | 3,98 M vues cumulées sur les 30 derniers jours (vidIQ, résultat de recherche) | ~1,46 M abonnés (NoxInfluencer, compteur temps réel consulté le 2026-09-28) ; ~1 vidéo/semaine (le mardi, selon la page Wikitubia) ⇒ moyenne dérivée ≈ 1 M vues/vidéo récente (calcul : 3,98 M ÷ ~4 vidéos/mois) | ND — pas de vidéo isolée identifiée au-dessus de cette moyenne dérivée | https://www.noxinfluencer.com/youtube/realtime-subs-count/UCFXad0mx4WxY1fXdbvtg0CQ |

Verdict : **outlier chiffré au sens strict non établi**, mais c'est la **preuve de demande la plus directement pertinente obtenue dans cette note** : une chaîne consacrée exactement à ce mécanisme (catastrophes/accidents racontés en détail, ton posé, sans sensationnalisme — description explicite trouvée) cumule ~1,46 M d'abonnés et ~4 M de vues sur 30 jours récents (chiffres consultés aujourd'hui). La moyenne de ~1 M vues/vidéo est un **calcul dérivé** de deux chiffres publiés (vues/30j ÷ fréquence hebdomadaire), pas une donnée publiée directement : à traiter comme un ordre de grandeur, confiance **faible**, pas comme un outlier vérifié.

**3. Concurrence.** Fascinating Horror (non-IA, voix off + photos d'archives + quelques animations, EN, ~1,46 M abonnés — S9/S10) ; the Infographics Show (non-IA, format liste/explainer couvrant aussi les catastrophes parmi d'autres sujets, EN, 8 M abonnés selon une référence 2020 — S3, confiance faible car ancienne) ; format proche des émissions « Mayday / Air Crash Investigation » réutilisées en clips (non vérifié aujourd'hui). **Aucune** des chaînes « AI slop » citées dans les rapports consultés (S6, S7 : Dragon Ball, contenu biblique, animaux) n'opère sur ce créneau — pas de signe de saturation par de l'IA bas de gamme sur les catastrophes dans les sources ouvertes, mais le créneau non-IA est déjà très occupé par des acteurs établis et respectés pour leur sobriété.

**4. RPM estimé.** Base skill §12, mais **probablement réduit sur une partie des épisodes** : la politique officielle YouTube sur les « sensitive events » (S16, source officielle, confiance élevée) prévoit que le contenu qui « profite d'un évènement sensible » ou l'exploite n'est pas monétisable, et que les discussions non exploitatives de pertes de vie/tragédie restent monétisables mais peuvent recevoir des publicités limitées selon le contexte. Sans chiffre RPM spécifique publié pour cette catégorie : inférence, confiance **moyenne** (fondée sur une source officielle, mais sans chiffre).

**5. Légitimité IA/procédurale.** Le mix le plus favorable aux archives du domaine public du lot A : photos et documents d'époque réels (Titanic, Pompéi, Hindenburg, Tchernobyl ont une abondante iconographie libre de droits ou tombée dans le domaine public), complétés par du rendu Blender procédural pour les reconstitutions physiques (naufrage, effondrement, explosion — simulations, pas de visages), et du motion design pour les cartes/chronologies minute par minute. Les visages de victimes réelles doivent être évités ou remplacés par des silhouettes/plans larges (point faible du local + exigence éthique). Valeur ajoutée vs slop : rigueur factuelle et sobriété (à l'inverse d'un montage sensationnaliste), exactement le positionnement de la chaîne concurrente la plus citée dans les sources consultées.

**6. Risque politique.** **Élevé — le plus élevé des six concepts.** Cumul de plusieurs facteurs identifiés dans les sources : (a) évènements réels avec morts réelles → politique « sensitive events », publicité potentiellement limitée voire nulle si le contenu est jugé exploitant la tragédie sans bénéfice éducatif discernable (S16, officiel) ; (b) reconstitution réaliste d'un évènement réel → divulgation `containsSyntheticMedia` quasi systématique (S17, officiel) ; (c) risque de désinformation historique sur le déroulé minute par minute si les sources ne sont pas fiables ; (d) sujet requérant une vigilance éditoriale particulière sur le ton (skill §7.6, « pas de formule émotionnelle manipulatrice » — détresse répétée sans arc narratif cohérent).

**7. Sérialité.** Large : Titanic, Pompéi, Hindenburg, Tchernobyl, Costa Concordia, tour de Grenfell, Bhopal, Deepwater Horizon, Fukushima, grand incendie de Londres, effondrement du World Trade Center, explosion de Beyrouth, crash du Concorde, incendie de Notre-Dame, tempête de Galveston (1900)… Estimation : ~40-60 épisodes distincts, mais rythme de publication vraisemblablement plus lent que les autres concepts (chaque sujet exige une validation conformité individuelle, jamais automatisable selon MISSION §11).

**8. Coût unitaire qualitatif.** Long 10 min : **moyen** (archives gratuites en partie, mais reconstitutions physiques Blender + quelques plans de génération vidéo pour l'ambiance/les foules). Short 40 s : **faible à moyen**.

**9. Note /100.**
| Critère | Poids | Note /5 | Justification |
|---|---|---|---|
| Demande prouvée | 20 | 3 | Chaîne de référence vérifiée sur exactement ce mécanisme (~1,46 M abonnés, ~4 M vues/30j) mais pas d'outlier vidéo isolé chiffré |
| Packaging (élim.) | 20 | 4 | Titre « minute par minute » très lisible, miniature = image d'archive forte |
| Audience adressable | 15 | 4 | Fascination large et universelle pour les catastrophes historiques |
| Angle neuf | 15 | 2 | Mécanisme très repris par des chaînes non-IA établies et respectées |
| Intensité | 10 | 5 | Enjeu maximal : vies humaines réelles, compte à rebours |
| Livrable en 30 s (élim.) | 10 | 4 | Image de l'évènement dès l'ouverture |
| Durée de vie | 5 | 5 | Evergreen |
| Conformité (élim.) | 5 | 2 | Sujets sensibles, publicité potentiellement limitée, divulgation systématique, vigilance ton |
| **Total** | | | **71/100** |

---

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | Wikipédia — Timelapse of the Future | https://en.wikipedia.org/wiki/Timelapse_of_the_Future | 2022-12-29 | 2026-09-28 | données | moyenne |
| S2 | Wikipédia — Kurzgesagt – In a Nutshell | https://en.wikipedia.org/wiki/Kurzgesagt_%E2%80%93_In_a_Nutshell | 2026-09-10 | 2026-09-28 | données | moyenne |
| S3 | Wikipédia — The Infographics Show (article Andrej Preston) | https://en.wikipedia.org/wiki/The_Infographics_Show | 2020 | 2026-09-28 | données | faible |
| S4 | Wikipédia — Underknown | https://en.wikipedia.org/wiki/Underknown | s.d. | 2026-09-28 | données | faible |
| S5 | Knowledge Lust (Samuel Rinko) — « The AI YouTube channel that "teaches" history » | https://samuelrinko.substack.com/p/the-ai-youtube-channel-that-teaches | s.d. | 2026-09-28 | praticien | faible |
| S6 | Kapwing — AI Slop Report: The Global Rise of Low-Quality AI Videos | https://www.kapwing.com/blog/ai-slop-report-the-global-rise-of-low-quality-ai-videos/ | 2025-12-29 | 2026-09-28 | données | moyenne |
| S7 | OutlierKit — YouTube's AI Slop Crackdown: 4.7 Billion Views Wiped, What Creators Must Know (2026) | https://outlierkit.com/resources/youtube-ai-slop-crackdown-2026/ | 2026 | 2026-09-28 | praticien | moyenne |
| S8 | Dexerto — Over 20% of YouTube is now "AI slop" and they're making millions: Report | https://www.dexerto.com/youtube/over-20-of-youtube-is-now-ai-slop-and-theyre-making-millions-report-3298592/ | s.d. | 2026-09-28 | presse | faible |
| S9 | NoxInfluencer — Fascinating Horror, compteur d'abonnés en temps réel | https://www.noxinfluencer.com/youtube/realtime-subs-count/UCFXad0mx4WxY1fXdbvtg0CQ | s.d. (temps réel) | 2026-09-28 | données | moyenne |
| S10 | vidIQ — Fascinating Horror's YouTube Stats (vu via résultat de recherche) | https://vidiq.com/youtube-stats/channel/UCFXad0mx4WxY1fXdbvtg0CQ/ | s.d. | 2026-09-28 | données | faible |
| S11 | Wikitubia (Fandom) — MetaBallStudios (vu via résultat de recherche) | https://youtube.fandom.com/wiki/MetaBallStudios | s.d. | 2026-09-28 | données | faible |
| S12 | YouTube — « AI-Generated: A Day in the Life of a Roman Legionary » | https://www.youtube.com/watch?v=lhukeuglV-g | 2025-04-18 | 2026-09-28 | données | faible |
| S13 | YouTube — « A Day in the Roman Legion - AI Historical Recreation » | https://www.youtube.com/watch?v=nos4MbNPx-Q | 2025-10-14 | 2026-09-28 | données | faible |
| S14 | YouTube — « What The Pyramids Of Egypt REALLY Looked Like When They Were New (AI Reconstruction) » | https://www.youtube.com/watch?v=Em39pDl719g | s.d. (2026) | 2026-09-28 | données | faible |
| S15 | UniladTech — « Frightening video shows what would happen to life on Earth if the moon disappeared » | https://www.uniladtech.com/science/space/frightening-video-shows-fate-of-life-on-earth-without-moon-664427-20231207 | 2023-12-07 | 2026-09-28 | presse | moyenne |
| S16 | Aide YouTube — Règles relatives au contenu adapté aux annonceurs (évènements sensibles) | https://support.google.com/youtube/answer/6162278 | 2022-03-23 | 2026-09-28 | officiel | élevée |
| S17 | Aide YouTube — Signaler du contenu généré ou modifié par IA | https://support.google.com/youtube/answer/14328491 | s.d. | 2026-09-28 | officiel | élevée |
| S18 | Variety — « More Than 1 Million YouTube Channels Are Using AI Tools Daily... » (titre vu en résultat de recherche) | https://variety.com/2026/digital/news/youtube-channels-using-ai-tools-reduce-slop-neal-mohan-letter-1236636548/ | 2026 | 2026-09-28 | presse | faible |
