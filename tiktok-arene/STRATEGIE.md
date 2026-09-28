# Arène des Nations — stratégie pour maximiser les vues

> Épisode 1 livré : `arene-ep01_tiktok.mp4` (61 s, 1080×1920, H.264/AAC, −14 LUFS, 28 Mio) et sa variante `…_sans-musique.mp4`. Master 8,5 Mb/s régénérable à l'identique (`tools/render.mjs`), aperçu versionné dans `episodes/ep01/preview/`.
> Tout est généré par le code de ce dossier : un **seed** = une partie de physique rejouable à l'identique, dans n'importe quel navigateur.

---

## 0. Prémisses corrigées

| Demande | Ce qui est faux ou risqué | Ce qui a été fait |
|---|---|---|
| « Ultra réaliste avec three.js » | three.js ne produit pas d'humains photoréalistes crédibles. Un faux « tournage » avec de faux humains serait raté visuellement **et** trompeur. | Réalisme là où three.js excelle : matériaux PBR, lumière de studio, ombres, profondeur de champ, physique simulée, sons déclenchés par les chocs réels de la simulation. |
| « Type MrBeast » | Reprendre son visage, sa voix ou son nom = usurpation (interdit par TikTok, risque juridique). | Reprise de sa **mécanique** : enjeu extrême, élimination, manches qui montent en intensité, ralenti + replay, payoff à la toute fin, texte géant, bruitage sur chaque graphisme. |
| « Voix ultra réalistes » | Cloner une voix réelle = interdit. Une voix synthétique réaliste doit être signalée. | Voix neuronale Microsoft (Rémy) + 12 voix pour la foule, horodatées mot à mot pour les sous-titres. Option ElevenLabs pour plus d'émotion. Label « contenu généré par IA » à activer. |
| « Le plus de millions de vues possible » | Personne ne peut promettre un nombre de vues. Une vidéo isolée est un tirage au sort à queue lourde. | La stratégie maximise **le nombre de tirages × la probabilité de chaque tirage**. Le générateur rend chaque épisode quasi gratuit en temps humain. |

---

## 1. Décomposition en premiers principes

```
Vues totales  =  Σ épisodes  [ impressions testées × P(passer chaque palier de diffusion) ]
                                         │
          ┌──────────────────────────────┼───────────────────────────────┐
     1re seconde                  visionnage complet                engagement
  (arrêt du scroll)          (rétention, re-visionnage)     (commentaires, partages)
```

TikTok indique lui-même que ses recommandations reposent sur les **interactions** (likes, partages, commentaires, visionnage), les **informations de la vidéo** (légende, sons, hashtags) et les réglages du compte, et qu'un **visionnage jusqu'au bout** est un fort indicateur d'intérêt (TikTok Newsroom, « How TikTok recommends videos #ForYou », 2020 — confiance élevée sur les facteurs, pondérations inconnues).
La diffusion par paliers (petit échantillon, puis élargissement si les métriques battent la moyenne) est un modèle de praticiens, non documenté officiellement (confiance moyenne).

**Conséquence : chaque levier du montage vise un de ces trois termes.**

| Terme | Levier intégré dans la vidéo | Où |
|---|---|---|
| Arrêt du scroll | Action dès l'image 1 (pluie de 32 billes), texte « 32 PAYS · 1 SEUL SURVIVANT », coup sonore à 0,02 s | 0–2,5 s |
| Enjeu personnel | Chaque spectateur cherche **son** pays dans la grille des 32 drapeaux | 2,4 s → finale |
| Engagement précoce | « Choisis ton pays. Maintenant. » = prédiction = investissement | 3,0 s |
| Aucun temps mort | 1re élimination à 4,4 s ; écart maximal entre deux éliminations : 3,1 s | tout le jeu |
| Escalade | Manche 2 (bras rotatif), manche 3 (barrières retirées, anneaux qui s'effondrent), finale 1 contre 1 | 20 s, 35 s, 40 s |
| Boucle ouverte unique | « Qui survit ? » fermée seulement à 48,6 s | toute la vidéo |
| Re-visionnage | Ralenti ×0,2 de la chute décisive + replay ×0,4 + classement final complet (on met pause pour trouver son pays) | 47–61 s |
| Commentaires | Rivalités réelles (Algérie/Maroc/Tunisie, Brésil/Argentine, France/Algérie), question finale « Et ton pays, il a fini où ? » | 57 s |
| Sérialisation | « ÉP. 1 », seed affiché → épisode 2 = revanche | filigrane |

---

## 2. Fiche

- **Promesse** : tu vas voir lequel des 32 pays survit seul sur la plateforme.
- **Public** : francophones 13–34 ans (France, Maghreb, Afrique de l'Ouest et centrale, Belgique, Suisse, Québec) + fans de foot.
- **Format** : Short vertical 61 s (au-dessus du seuil d'une minute du programme de rémunération TikTok).
- **Hypothèse posée** : compte neuf, publication manuelle, aucun budget publicitaire.

### Demande prouvée
- Page TikTok « Marble Race Country Elimination » : **661 500 publications** ; une vidéo de la chaîne Cactus Canyon Marble Race : **181 000 likes, 3 662 commentaires** ([TikTok](https://www.tiktok.com/discover/marble-race-country-elimination), [vidéo](https://www.tiktok.com/@cactus.canyon.marblerace/video/7486577241976098090)).
- Des outils dédiés existent pour produire ces vidéos à la chaîne ([ViralBalls](https://viralballs.com/en), [BallSimulator](https://ballsimulator.com/en/), [country-ball-physics](https://github.com/jlrinconj-mcp/country-ball-physics)) : la demande est réelle **et** l'offre en 2D est déjà abondante.

### Note de l'idée

| Critère | Poids | Note /5 | Points |
|---|---:|---:|---:|
| Demande prouvée | 20 | 4 | 16 |
| Packaging (éliminatoire) | 20 | 5 | 20 |
| Audience adressable | 15 | 5 | 15 |
| Angle neuf | 15 | 3 | 9 |
| Intensité | 10 | 4 | 8 |
| Livrable en 30 s (éliminatoire) | 10 | 5 | 10 |
| Durée de vie | 5 | 4 | 4 |
| Conformité (éliminatoire) | 5 | 4 | 4 |
| **Total** | | | **86 / 100** |

L'angle neuf est le point faible : le genre est saturé en 2D. La différenciation repose sur le rendu 3D « plateau télé », la voix off de commentateur, le montage façon MrBeast et le ciblage francophone.

### Potentiel (confiance faible)

| Scénario sur 30 jours, 30 à 45 épisodes | Probabilité estimée | Vues cumulées |
|---|---:|---|
| Le format ne décolle pas (complétion < 25 %) | ~45 % | 5 k – 50 k |
| 1 ou 2 épisodes percent | ~40 % | 100 k – 1 M |
| Un épisode dépasse 1 M | ~15 % | 1 M – 10 M |

Ce qui ferait monter l'estimation : sur les 5 premiers épisodes, taux de visionnage complet ≥ 35 % et ≥ 1 partage pour 100 vues. Ce qui la ferait baisser : chute > 50 % avant 3 s.
Plafond structurel : le français limite l'audience. Le levier le plus fort pour viser plusieurs millions est la **version anglaise et arabe** du même épisode (§ 7).

---

## 3. Packaging

**1re image + texte à l'écran** : pluie de billes-drapeaux + « 32 PAYS » / « 1 SEUL SURVIVANT ».

| Légende TikTok | Caractères | Logique |
|---|---:|---|
| A. 32 pays, 1 seul survivant. Ton pays tient combien de temps ? | 60 | enjeu + question personnelle |
| B. Le dernier pays sur la plateforme gagne. Commente le tien 👇 | 60 | règle + appel au commentaire |
| C. J'ai lancé 32 pays dans une arène. Un seul en sort vivant | 58 | 1re personne (vraie : c'est ta simulation) |

Hashtags (3 à 5, rôle de classification seulement) : `#simulation #pays #marblerace` + les 2 finalistes (`#algerie #bresil`).

Couvertures exportées : `cover_hook.jpg` (grille du profil, sans spoiler), `cover_vs.jpg` (révèle la finale : à réserver aux reposts), `cover_victoire.jpg`.

Son : piste originale (voix + bruitages + musique générée). Variante `_sans-musique.mp4` pour poser un son tendance de la bibliothèque TikTok à faible volume.

---

## 4. Script minuté de l'épisode 1 (seed 356)

| # | Temps | Voix off | Visuel | Texte écran | Son |
|---|---|---|---|---|---|
| 1 | 0,0–2,9 | [HOOK] Trente-deux pays. Un seul survivant. | Plan grue bas → plongée : 32 billes tombent et rebondissent | 32 PAYS · 1 SEUL SURVIVANT | impact d'ouverture, cliquetis de chute |
| 2 | 3,0–5,1 | [Q1 ouverte] Choisis ton pays. Maintenant. | Grille des 32 drapeaux qui apparaît case par case | 32 RESTANTS | foule, première alarme de porte |
| 3 | 4,4–8,0 | Premier éliminé : le Cameroun ! | La porte 1 s'ouvre, le plateau penche, zoom coup de poing | CAMEROUN OUT · 32e | whoosh, boom, « ding » |
| 4 | 8–20 | Pays-Bas et Guinée… Mexique… Bénin et États-Unis… Côte d'Ivoire… Turquie | Plan large 3/4, orbite lente, étiquettes pays | toasts d'élimination | clics de billes, grondement |
| 5 | 20,4–22,7 | [RELANCE] Manche deux : le bras de la mort ! | Travelling bas, le bras télescopique sort du moyeu | MANCHE 2 · LE BRAS DE LA MORT | montée + impact, gyrophare |
| 6 | 23–34 | Mali et Haïti… Burkina… Belgique… Plus que dix ! | Le bras balaie, éjections, zooms | 10 RESTANTS | clangs métalliques |
| 7 | 34,8–37,3 | [RELANCE] Manche trois : plus aucune barrière ! | Plateau stabilisé, barrières qui tombent en cascade, anneaux rouges qui s'effondrent | MANCHE 3 · PLUS DE BARRIÈRES | sirène, effondrement |
| 8 | 38,6–40,4 | Allemagne et Suisse tombent ensemble ! | Descente à 2 finalistes | — | foule « oooh » |
| 9 | 40,4–48,6 | C'est la finale. L'Algérie contre le Brésil. · Qui va craquer ? | Clôture lumineuse, plateau à plat puis escalade ; orbite serrée, profondeur de champ | FINALE · carte VS | battements de cœur, bourdon, montée |
| 10 | 47–49,6 | [PAYOFF] [Q1 fermée] L'Algérie gagne ! | Chute du Brésil au ralenti ×0,2 | VICTOIRE · ALGÉRIE | impact, accord majeur, foule |
| 11 | 51,3–55,4 | Regarde bien. Tout s'est joué ici. | Replay latéral ×0,4, bandes cinéma | REPLAY ×0,4 | rembobinage, sons ralentis |
| 12 | 55,4–57,1 | — | La bille vainqueur lévite, confettis, orbite | VICTOIRE · ALGÉRIE | ovation, applaudissements, sifflets |
| 13 | 57,1–61,0 | [CTA] Et ton pays, il a fini où ? | Classement final complet des 32 | CLASSEMENT FINAL | whoosh, musique |

115 mots en 61 s (1,9 mot/s) : l'image porte le récit, la voix ponctue.
Le JSON de production (scènes ≤ 5 s) est écrit par le rendu dans `episodes/ep01/ep01.scenes.json`.

### Ouvertures alternatives (test A/B)
- **B — question** : « Un seul de ces 32 pays va survivre. Lequel ? » (même image).
- **C — in medias res** : démarrer sur la quadruple élimination par le bras (flash-forward 1,5 s), puis « 32 pays au départ. Plus que 4 en une seconde. »

Pour produire B : remplacer le texte de la réplique `hook` dans `src/director.js`, relancer `tools/episode.mjs`, `tools/tts.py` puis `tools/render.mjs`.

---

## 5. Réalisme : ce qui est en place, ce qui reste à ajouter

| Couche | En place | Amélioration suivante (impact / coût) |
|---|---|---|
| Physique | Roulement sans glissement (a = 5/7·g), cuvette, chocs élastiques, bras rotatif, portes, effondrement, chute libre avec rotation ; déterministe bit à bit | Flou de mouvement par accumulation de sous-images (fort / ×3 temps de rendu) |
| Matériaux | Billes vernies (clearcoat), micro-rayures, drapeaux imprimés avec grain ; sol époxy texturé, usure ; polycarbonate ; métal | Textures scannées CC0 (Poly Haven) pour le métal et le sol (moyen / faible) |
| Lumière | Éclairage de studio (clé + contres colorées), IBL du décor, ombres douces, lumière rouge du vide, gyrophare | HDRI réelle d'arène CC0 (moyen / faible) ; rendu path-tracé pour la couverture (fort / moyen) |
| Caméra | Grue, orbite type retransmission, zooms coup de poing, bougé à l'épaule, profondeur de champ, aberration chromatique, grain, vignettage | Rendu 60 i/s sur GPU (moyen / nul avec GPU) |
| Son | Clics de billes synthétisés à chaque choc réel, grondement de roulement, moteur du bras, portes, sirène, effondrement, battements de cœur, musique générée, réverbération | **Enregistrer 20 min de vraies billes** au téléphone et remplacer les clics synthétiques (fort / faible) |
| Voix | Voix neuronale, sous-titres mot à mot, foule multi-voix, ducking | ElevenLabs v3 avec balises d'émotion [excited] [whispers] (fort / ~5–22 $/mois) |

---

## 6. Audit (Short)

| Point | Statut | Détail |
|---|---|---|
| Hook ≤ 3 s, image et texte alignés | ✓ | texte et voix identiques dès 0,05 s |
| Texte à l'écran ≤ 5 mots | ✓ | « 32 PAYS », « 1 SEUL SURVIVANT » |
| Payoff à la fin | ✓ | vainqueur à 48,6 s, classement à 57 s |
| Une seule boucle ouverte, refermée | ✓ | « qui survit ? » |
| Ni outro ni demande d'abonnement | ✓ | fin sur une question |
| Boucle visuelle fin → début | ✗ | la dernière image (classement) ne raccorde pas avec la première ; test à faire : finir sur la pluie de billes de l'épisode suivant |
| Tics d'écriture IA | ✓ | aucun |
| Divulgation | à faire | activer « contenu généré par IA » (voix synthétique réaliste) |
| Aucune personne réelle imitée | ✓ | ni visage, ni voix, ni nom de créateur |

---

## 7. Plan 30 jours

**Règle d'or : 1 épisode par jour minimum, jamais deux fois le même modèle mot pour mot.** TikTok peut écarter du fil Pour Toi les contenus répétitifs ou peu originaux (règles d'éligibilité, confiance moyenne) : chaque épisode change au moins deux éléments parmi pays, mécanique, hook, musique.

| Semaine | Contenu | But |
|---|---|---|
| 1 | Ép. 1–7 : 32 pays mixtes, seeds différents ; 3 hooks testés (A, B, C) | trouver le hook qui garde > 70 % des spectateurs après 3 s |
| 2 | Thèmes : Afrique (32 pays), Maghreb vs Europe, « revanche » demandée en commentaire | mesurer l'effet des rivalités sur les commentaires |
| 3 | Duels 1 contre 1 demandés par les commentaires (réponse vidéo au commentaire), épisodes « Coupe du monde 2026 » | boucle communauté → contenu |
| 4 | Doublage anglais (voix `en-US`) et arabe (`ar-*`) des meilleurs épisodes, repost sur YouTube Shorts et Reels (fichier sans filigrane) | multiplier le vivier d'audience |

**Rituel après chaque publication** : épingler « Ton pays a fini où ? 👇 », répondre aux 20 premiers commentaires dans l'heure, transformer la meilleure demande en épisode.

---

## 8. Indicateurs et règles de décision

| Symptôme (TikTok Analytics) | Cause probable | Action |
|---|---|---|
| > 50 % partent avant 3 s | 1re image ou hook | tester l'ouverture C, couverture plus lisible |
| Chute nette vers 20 s | lassitude en milieu de manche 1 | raccourcir la manche 1 (paramètre `P.D` dans `src/sim.js`) |
| Bonne rétention, peu de commentaires | enjeu personnel faible | liste de pays plus rivale, question finale plus clivante |
| Commentaires « truqué » | doute sur l'aléa | afficher « seed n°… », publier le studio pour rejouer |
| Vues plafonnées à ~200–500 | le premier palier ne passe pas | changer 2 éléments sur les 3 épisodes suivants, pas le format entier |

Repères de praticiens (confiance moyenne) : sur un format de 60 s, un visionnage complet > 35 % et un taux de partage > 1 % sont de bons signaux. Juger au bout de 5 épisodes, pas d'un seul.

---

## 9. Risques

| Risque | Parade |
|---|---|
| Commentaires haineux entre supporters | filtres de mots-clés, commentaire épinglé « on joue, on ne se déteste pas », jamais de moquerie d'un pays dans les textes |
| « C'est truqué » | l'épisode affiché est choisi parmi 400 simulations sur un **score de suspense** (rythme, finale serrée), jamais sur l'identité du vainqueur ; le dire en réponse et montrer le seed |
| Droits de la voix Edge TTS pour un usage monétisé | pour monétiser : Azure AI Speech (mêmes voix, licence commerciale) ou forfait payant ElevenLabs |
| Saturation du genre | 3D, voix, montage, thèmes d'actualité foot |
| Monétisation | le programme de rémunération TikTok exige des vidéos > 1 min ; l'épisode fait 61 s — garder P.D ≥ 36 s (confiance moyenne sur les seuils, qui changent) |

---

## 10. Actions dans l'ordre

1. **Aujourd'hui** — Créer un compte dédié « Arène des Nations ». Publier `arene-ep01.mp4` avec la légende A, la couverture `cover_hook.jpg`, le label IA activé. Épingler le commentaire. *Vérification : la vidéo apparaît avec la mention « Généré par IA ».*
2. **J+1 et J+2** — Produire les épisodes 2 et 3 :
   ```bash
   node tools/seed_search.mjs 401 800 | head -c 600      # meilleurs seeds (JSON trié)
   node tools/episode.mjs <seed> episodes/ep02
   python3 tools/tts.py episodes/ep02
   node tools/render.mjs episodes/ep02 --workers 2       # ~70 min sur 4 cœurs sans GPU
   ```
   *Vérification : `episodes/ep02/out/arene-ep02.mp4` dure > 60 s et `tmp/render.log` affiche « terminé ».*
3. **J+5** — Relever pour les 5 épisodes : % de visionnage complet, spectateurs restés après 3 s, partages, commentaires. Appliquer le tableau du § 8.
4. **J+7** — Garder le hook gagnant, lancer les thèmes de la semaine 2.
5. **J+21** — Doubler les 3 meilleurs épisodes en anglais (voix `en-US-AndrewMultilingualNeural`, textes traduits dans `src/director.js`) et les publier aussi sur Shorts et Reels.
6. **Chaque semaine** — Un épisode issu d'une demande de commentaire, publié en réponse vidéo au commentaire.

*Critère de succès à J+30 : au moins un épisode à 10× la médiane du compte. Sinon, changer l'angle (arène, mécanique), garder le moteur.*
