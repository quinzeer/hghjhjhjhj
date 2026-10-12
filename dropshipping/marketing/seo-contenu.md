# SEO et contenu éditorial : 15 clusters, 10 articles

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Domaine | `canapoil.fr` (neuf) ; section `/guides/` à créer par l'agent site ([07 §1.3](07-plan-organique-90j.md)) |
| Données | [Google Trends France, 57 mots-clés, 5 ans, relevé du 12/10/2026](../recherche/donnees/google-trends-fr-2026-10-12.csv) et [séries brutes](../recherche/donnees/) ; mots-clés de `brand.json` → `seo` |
| Rôle du SEO | Canal de rendement lent : 4 à 12 mois avant un trafic significatif sur un domaine neuf (02 §1.7, estimation, confiance moyenne). Les articles servent aussi tout de suite de support aux épingles Pinterest, aux e-mails et aux réponses en commentaire |

---

## 0. Constats qui orientent le plan

| # | Constat | Chiffre | Conséquence |
|---|---|---|---|
| 1 | Le nom du produit est peu cherché ; le problème l'est beaucoup | « rouleau anti poils » ≈ 0,04 fois le volume de « tapis de fouille » (Trends : volume trop faible) ; « poils de chat » ≈ 6,2 fois ; « anti poils » ≈ 1,8 fois ([CSV Trends](../recherche/donnees/google-trends-fr-2026-10-12.csv)) | Les articles ciblent le problème (« poils de chat canapé », « poils de chien voiture ») et renvoient vers les fiches produit |
| 2 | Saisonnalité inversée par rapport au lancement | Indice mensuel « anti poils » : décembre 0,54, août 1,21 ; « poils de chat » : novembre 0,74, mai 1,16 ; « brosse chat » : octobre 0,75, mai 1,23 (calcul marketing sur 5 ans de séries hebdomadaires, confiance moyenne) | Les articles « poils » doivent être indexés **avant février 2027** ; le lancement de novembre s'appuie sur TikTok, pas sur la recherche |
| 3 | Les requêtes « cadeau » et « couchage » culminent en fin d'année | « jouet chat » : novembre 1,88, décembre 1,71 ; « lit chat » : octobre 1,24, novembre 1,20 (même calcul) | Les articles cadeau et fenêtre visent surtout la saison 2027 ; publiés en décembre 2026, ils servent d'abord Pinterest et l'e-mail |
| 4 | Les résumés IA de Google réduisent les clics sur les requêtes informationnelles | CTR de la position 1 −58 % (Ahrefs, déc. 2025) ; clic sur un résultat dans 8 % des visites avec résumé IA contre 15 % sans (Pew) (02 §1.7) | Chaque article apporte une information introuvable ailleurs : tests filmés, comptages d'allers-retours, échecs montrés. Les fiches produit (requêtes transactionnelles, moins touchées) restent la priorité |
| 5 | Les têtes de requête sont tenues par des acteurs installés | Amazon, zooplus et les médias animaliers occupent les premières positions (observation, non mesurée) | Priorité à la longue traîne : surface + animal + tissu (« poils chien siège voiture tissu ») |

### 0.1 Méthode d'estimation des volumes

Google Trends donne des indices relatifs, pas des volumes. Les volumes mensuels ci-dessous sont obtenus ainsi :

1. **Ratio Trends** de chaque mot-clé par rapport au repère « tapis de fouille », mesuré sur 12 mois en France ([CSV](../recherche/donnees/google-trends-fr-2026-10-12.csv), confiance moyenne sur l'ordre de grandeur).
2. **Volume du repère** « tapis de fouille » fixé entre **3 000 et 12 000 recherches par mois** (estimation, confiance faible).
3. Volume estimé = ratio × fourchette du repère.

Pour les requêtes absentes du relevé Trends, la classe de volume est une estimation de confiance faible : **faible** (< 1 000 par mois), **moyen** (1 000 à 10 000), **élevé** (> 10 000).

**Action S1** : remplacer toutes ces estimations par les volumes du Google Keyword Planner (compte Google Ads sans dépense, 01 §6) et, après 3 mois, par les impressions réelles de la Search Console.

---

## 1. Les 15 clusters de mots-clés

| # | Cluster | Requête principale | Requêtes secondaires | Intention | Volume mensuel France (requête principale) | Page cible | Priorité |
|---|---|---|---|---|---|---|---|
| 1 | Poils de chat dans la maison | poils de chat | poils de chat partout, se débarrasser des poils de chat, poils de chat vêtements | Informationnelle | ≈ 19 000-74 000 (Trends × 6,2) ; la requête inclut des intentions hors sujet (allergies) | A1 (pilier) | 2 |
| 2 | Poils de chat sur le canapé | enlever poils chat canapé | poils de chat canapé velours, poils chat canapé tissu, canapé plein de poils | Informationnelle → commerciale | Moyen (estimation, confiance faible) | **A1** | **1** |
| 3 | Poils de chien sur le canapé et les textiles | enlever poils chien canapé | poils de chien partout, poils chien plaid, poils courts de chien canapé | Informationnelle | Moyen (estimation, confiance faible) | A1 (section chien), A7 | 1 |
| 4 | Produits anti-poils | anti poils | brosse anti poils animaux, anti poil chat canapé, accessoire anti poils | Commerciale | ≈ 5 400-21 700 (Trends × 1,81) | `/boutique/`, fiche rouleau | 1 |
| 5 | Rouleau réutilisable | rouleau anti poils | rouleau anti poils réutilisable, rouleau poils animaux, brosse anti poils réutilisable | Transactionnelle | Faible : ≈ 100-500 (Trends × 0,04, signal trop faible) | **Fiche rouleau** `/produits/rouleau-anti-poils-reutilisable/` | **1** |
| 6 | Rouleau adhésif et recharges | rouleau adhésif poils | recharge rouleau adhésif, rouleau collant poils chat, rouleau adhésif ou réutilisable | Commerciale | Moyen (estimation, confiance faible) | **A4** | 1 |
| 7 | Poils de chien dans la voiture | poils de chien voiture | enlever poils chien siège voiture, poils chien coffre, poils chien moquette voiture | Informationnelle → commerciale | Moyen (estimation, confiance faible) ; mot-clé principal de `brand.json` | **A2** ; fiche raclette | **1** |
| 8 | Poils sur tapis et moquette | enlever poils tapis | poils de chat tapis, poils chien moquette, raclette poils tapis | Informationnelle | Moyen (estimation, confiance faible) | **A7** ; fiche raclette | 1 |
| 9 | Tissu de canapé et animaux | quel tissu canapé chat | canapé et chat, canapé résistant chien, canapé velours chat | Commerciale (recherche avant achat d'un canapé) | Moyen (estimation, confiance faible) | **A3** | 2 |
| 10 | Mue | mue chat | période de mue chat, mue chien, chat perd ses poils (redirigé vers le vétérinaire) | Informationnelle, saisonnière (février-mai) | Moyen à élevé (estimation, confiance faible) | **A5** | 1 (publication avant février) |
| 11 | Brossage | brosse chat | gant toilettage chat, brosser son chat, gant poil chat | Commerciale | ≈ 12 800-51 000 (Trends × 4,25) ; pic mars-août | **A6** ; fiche gant | 2 |
| 12 | Lit, couette, linge | poils de chat lit | poils chat couette, enlever poils linge, poils de chat draps | Informationnelle | Moyen (estimation, confiance faible) | **A8** | 2 |
| 13 | Arbre à chat et couchages | nettoyer arbre à chat | poils arbre à chat, nettoyer panier chat | Informationnelle | Faible à moyen (estimation, confiance faible) ; « arbre à chat » seul ≈ 27 800-111 400 (Trends × 9,28) mais d'intention d'achat de meuble | A1 (section), A8 | 3 |
| 14 | Cadeaux | idée cadeau propriétaire chat | cadeau amoureux des chats, cadeau propriétaire chien, cadeau chat moins de 40 € | Commerciale, saisonnière (novembre-décembre) | Moyen (estimation, confiance faible) ; « jouet chat » ≈ 30 700-122 900 (Trends × 10,24), pic en novembre | **A9** | 2 (saison 2027) |
| 15 | Chat à la fenêtre en hiver | couchage chat fenêtre | lit chat fenêtre, tapis chauffant chat sans électricité, tapis fenêtre chat, hamac fenêtre chat | Commerciale, saisonnière (octobre-février) | « lit chat » ≈ 27 800-111 400 (Trends × 9,28) ; « tapis chauffant chat » et « hamac fenêtre chat » < 500 (Trends : volume trop faible) | **A10** ; fiche tapis thermique | 2 |

Cluster de réserve : **tapis de fouille** (≈ 3 000-12 000, repère du calcul ; pic de novembre à février). Article « Tapis de fouille : comment l'utiliser et le laver » à écrire seulement si le challenger gagne la porte 1 (04 §2.1).

**Mots-clés à exclure** : « chomchom » (marque tierce, 04 §7 risque 6), « allergie poils de chat » et toute requête de santé (allégations interdites), « made in France ».

---

## 2. Optimisation des pages existantes (avant les articles)

| Page | Balise title (≤ 60 caractères) | Meta description | Points à ajouter |
|---|---|---|---|
| Accueil | « Canapoil — Rouleau anti-poils réutilisable pour chat et chien » (`brand.json`) | `brand.json` → `seo.meta_description_accueil` | Lien vers A1 et la vidéo de test sur 5 tissus |
| Fiche rouleau | « Rouleau anti-poils réutilisable chat et chien · Canapoil » | « Rouleau anti-poils réutilisable sans recharge ni pile, testé en vidéo sur velours, microfibre, plaid et siège auto. Expédié depuis la France. » | Vidéo R09 intégrée ; tableau « tissus conseillés / déconseillés » ; FAQ de `brand.json` ; données structurées Product avec `offers`, `shippingDetails` et `hasMerchantReturnPolicy` |
| Fiche raclette | « Raclette anti-poils pour tapis et voiture · Canapoil » | « Raclette en caoutchouc pour décoller les poils de chien et de chat incrustés dans les tapis ras, la moquette et les sièges auto. » | Vidéo K22 ; lien vers A2 et A7 |
| Fiche gant | « Gant de toilettage en silicone chat et chien · Canapoil » | « Gant en silicone pour brosser votre chat ou votre chien : une partie des poils morts reste sur le gant. Se rince à l'eau claire. » | Vidéo K23 ; lien vers A6 ; aucune allégation de bien-être |
| Fiche tapis thermique | « Tapis de fenêtre pour chat, sans électricité · Canapoil » | « Couchage pour rebord de fenêtre : dessus sherpa, couche réfléchissante, dessous antidérapant. Sans fil ni prise. Vendu d'octobre à février. » | Vidéo K24 ; consigne « jamais sur un radiateur » ; lien vers A10 |
| Grand kit | « Grand kit anti-poils : canapé, tapis, voiture · Canapoil » | « Rouleau, raclette et gant : les trois outils anti-poils pour toute la maison. 39,90 €, livraison offerte, expédié depuis la France. » | Vidéo K21 ; économie affichée en texte |

**Règles techniques** : une seule balise H1 par page ; textes rédigés de zéro, aucune description fournisseur (02 §1.7) ; images au format WebP avec texte alternatif descriptif (« rouleau anti-poils sur un coussin en velours vert ») ; vidéos hébergées sur YouTube et intégrées avec des données structurées VideoObject ; pages `/guides/` ajoutées au `sitemap.xml` ; maillage : chaque article renvoie vers 1 fiche produit et 2 articles.

---

## 3. Plans détaillés des 10 articles

Règles communes : 1 vidéo de test filmée par Canapoil dans chaque article ; résultats chiffrés seulement s'ils sont mesurés (allers-retours, chrono) ; limites du produit écrites ; aucun conseil de santé (renvoi au vétérinaire) ; date de mise à jour visible ; auteur nommé (le fondateur) avec une courte biographie réelle ; appel à l'action vers une fiche, jamais plus de deux par article.

### A1 — Article pilier

| Champ | Contenu |
|---|---|
| H1 | Enlever les poils de chat d'un canapé : test sur 5 tissus |
| URL | `/guides/enlever-poils-chat-canape/` |
| Title | Enlever les poils de chat d'un canapé : test sur 5 tissus (57) |
| Meta description | Velours, microfibre, lin, cuir, plaid : quelle méthode marche sur quel tissu ? Tests filmés, nombre de passages mesuré, et ce qui ne marche pas. |
| Clusters | 2 (principal), 1, 3, 13 |
| Longueur | 1 800-2 200 mots |
| Publication | S10 (14-20/12/2026), mise à jour en février 2027 |

| Section | Contenu |
|---|---|
| Introduction (100 mots) | Le problème ; 16,6 M de chats en France ([FACCO-Odoxa 2026](https://www.lepointveterinaire.fr/veterinaire/planete-vet/animal-societe/possession-suivi-veterinaire-alimentation-dit-barometre-faccoodoxa-2026-15hngc3)) ; ce que l'article a testé |
| H2 Notre protocole de test | Même poignée de poils, 5 tissus, plan fixe, comptage des allers-retours ; vidéo R09 intégrée |
| H2 Les méthodes comparées | H3 Gant en caoutchouc humide · H3 Rouleau adhésif · H3 Rouleau réutilisable · H3 Aspirateur avec brosse · H3 Chiffon microfibre humide. Pour chacune : geste, coût, tissus où elle marche, limites |
| H2 Résultats par tissu | Tableau tissu × méthode (allers-retours ou « peu efficace »), rempli avec les mesures réelles |
| H2 Cas particuliers | H3 Cuir et simili-cuir · H3 Velours côtelé · H3 Poils courts incrustés · H3 Arbre à chat |
| H2 Prévenir plutôt que nettoyer | Plaid lavable, brossage hebdomadaire, passages courts et fréquents (script R17) |
| H2 Et pour les chiens ? | Différences observées sur les poils courts et longs ; lien vers A2 et A7 |
| FAQ (4 questions) | « Comment enlever les poils de chat d'un canapé en velours ? » · « Quelle méthode sur un canapé en cuir ? » · « À quelle fréquence nettoyer ? » · « Un rouleau réutilisable abîme-t-il le tissu ? » |
| Appel à l'action | Fiche rouleau ; Grand kit pour canapé + tapis |
| Liens internes | A3, A4, A7, A8 |

### A2 — Voiture

| Champ | Contenu |
|---|---|
| H1 | Poils de chien dans la voiture : sièges, coffre, moquette |
| URL | `/guides/poils-chien-voiture/` |
| Title | Poils de chien dans la voiture : sièges, coffre, moquette (57) |
| Meta description | Sièges en tissu, moquette du coffre, tapis de sol : les gestes qui décollent les poils de chien incrustés, testés en vidéo, et comment limiter le problème. |
| Clusters | 7 (principal), 8 |
| Longueur | 1 300-1 600 mots |
| Publication | S11 (21-27/12/2026) |

| Section | Contenu |
|---|---|
| Introduction | Persona Julien et Sarah : balade, banquette, coffre ; 9,6 M de chiens en France ([FACCO-Odoxa 2026](https://www.lepointveterinaire.fr/veterinaire/planete-vet/animal-societe/possession-suivi-veterinaire-alimentation-dit-barometre-faccoodoxa-2026-15hngc3)) |
| H2 Pourquoi les poils s'incrustent dans la moquette | Fibres de moquette, poils courts ; description factuelle sans chiffre inventé |
| H2 Les sièges en tissu | Rouleau réutilisable (vidéo R15), aspirateur, gant humide |
| H2 Le coffre et les tapis de sol | Raclette en caoutchouc (vidéo K22), gestes par petites zones, zone cachée d'abord |
| H2 Sièges en cuir | Chiffon microfibre humide ; rouleau déconseillé |
| H2 Limiter les poils pendant le trajet | Housse ou plaid de coffre lavable, brossage avant le départ (gant) |
| H2 Routine en 5 minutes après la balade | Liste numérotée |
| FAQ (3) | « Comment enlever les poils de chien incrustés dans la moquette de voiture ? » · « Un rouleau marche-t-il sur les sièges auto ? » · « Quelle housse choisir ? » |
| Appel à l'action | Duo maison + voiture ; raclette |
| Liens internes | A1, A7 |

### A3 — Tissu de canapé

| Champ | Contenu |
|---|---|
| H1 | Quel tissu de canapé avec un chat ou un chien ? |
| URL | `/guides/tissu-canape-chat-chien/` |
| Title | Quel tissu de canapé avec un chat ou un chien ? (47) |
| Meta description | Velours, microfibre, lin, cuir, bouclette : comment chaque tissu retient les poils, d'après nos tests filmés, et les questions à poser avant d'acheter. |
| Clusters | 9 |
| Longueur | 1 500-1 800 mots |
| Publication | Janvier 2027 |

| Section | Contenu |
|---|---|
| Introduction | Le canapé est le premier lieu de cohabitation ; ce que l'article mesure (poils) et ce qu'il ne mesure pas (résistance aux griffes, non testée) |
| H2 Tableau des tissus | Tissu × facilité de nettoyage des poils (nombre d'allers-retours mesuré par Canapoil) × méthode recommandée |
| H2 Velours | Résultats du test ; poils visibles en lumière rasante |
| H2 Microfibre | Résultats |
| H2 Lin et coton | Résultats |
| H2 Cuir et simili-cuir | Poils faciles à essuyer, rouleau inutile ; griffes : se renseigner auprès du fabricant |
| H2 Bouclette et tissus à relief | Résultats ou « non testé » |
| H2 Questions à poser au vendeur du canapé | Housses déhoussables et lavables, garantie du fabricant, échantillon de tissu |
| Appel à l'action | Envoyer une photo de son tissu au service client ; fiche rouleau |
| Liens internes | A1, A8 |

### A4 — Comparatif adhésif / réutilisable

| Champ | Contenu |
|---|---|
| H1 | Rouleau adhésif ou rouleau réutilisable : le comparatif |
| URL | `/guides/rouleau-adhesif-ou-reutilisable/` |
| Title | Rouleau adhésif ou réutilisable : le comparatif (47) |
| Meta description | Coût sur un an, efficacité sur plaid et canapé, usage sur les vêtements : nos mesures pour choisir entre rouleau collant et rouleau réutilisable. |
| Clusters | 6 (principal), 5 |
| Longueur | 1 200-1 500 mots |
| Publication | S12 (28/12/2026-3/01/2027) |

| Section | Contenu |
|---|---|
| Introduction | Deux outils, deux usages |
| H2 Le test | Même plaid partagé en deux (vidéo R07) : feuilles utilisées, allers-retours, temps |
| H2 Le coût sur un an | Prix des recharges relevés sur Amazon.fr le 12/10/2026 : 1,8 à 2,6 centimes la feuille ([relevé](../recherche/donnees/releve-prix-amazon-zooplus-2026-10-12.csv)) ; calcul pour 2, 5 et 10 feuilles par séance et 2 séances par semaine, hypothèses écrites |
| H2 Où l'adhésif reste meilleur | Vêtements, petites surfaces, déplacements |
| H2 Où le réutilisable est plus pratique | Canapé, plaid, couette, arbre à chat |
| H2 Les limites des deux | Cuir, poils courts incrustés, tapis épais |
| Tableau récapitulatif | Critère × outil |
| FAQ (3) | « Un rouleau réutilisable marche-t-il sur les vêtements ? » · « Combien de temps dure un rouleau réutilisable ? » (réponse : durée réelle observée, sinon « mesure en cours ») · « Comment le nettoyer ? » |
| Appel à l'action | Fiche rouleau |
| Liens internes | A1, A8 |

### A5 — Mue

| Champ | Contenu |
|---|---|
| H1 | Mue du chat : gérer les poils à la maison |
| URL | `/guides/mue-chat-poils-maison/` |
| Title | Mue du chat : gérer les poils à la maison (41) |
| Meta description | Pendant la mue, les poils envahissent canapé, lit et vêtements. Routine de brossage et de nettoyage, et quand demander conseil au vétérinaire. |
| Clusters | 10 (principal), 11 |
| Longueur | 1 200-1 500 mots |
| Publication | **Au plus tard le 25/01/2027** (avant la hausse de février) |

| Section | Contenu |
|---|---|
| Encadré en tête | « Une perte de poils inhabituelle, des plaques ou des démangeaisons relèvent du vétérinaire. Cet article traite seulement des poils dans la maison. » |
| H2 Quand les poils se multiplient à la maison | Saisons observées dans les recherches françaises (Trends : pic de février à août) ; sources vétérinaires à citer pour les périodes de mue, sans affirmation non sourcée |
| H2 La routine de la semaine | Brossage (gant ou brosse), plaid lavé, passages courts sur le canapé, lit |
| H2 Brosser un chat qui n'aime pas la brosse | Séances courtes, arrêt dès l'inconfort (vidéo K23) |
| H2 Les endroits à traiter en priorité | Canapé, lit, arbre à chat, voiture |
| FAQ (3) | « Quand mon chat mue-t-il ? » (réponse sourcée) · « Faut-il brosser tous les jours ? » (renvoi vétérinaire si doute) · « Comment éviter les poils sur les vêtements ? » |
| Appel à l'action | Gant ; Kit anti-poils |
| Liens internes | A1, A6, A8 |

### A6 — Brossage

| Champ | Contenu |
|---|---|
| H1 | Brosser son chat : gant, brosse ou peigne ? |
| URL | `/guides/brosser-son-chat-gant-brosse-peigne/` |
| Title | Brosser son chat : gant, brosse ou peigne ? (43) |
| Meta description | Poil court, mi-long ou long : quel outil de brossage choisir, comment s'y prendre avec un chat réticent et comment entretenir l'outil. |
| Clusters | 11 |
| Longueur | 1 300-1 600 mots |
| Publication | Février 2027 |

| Section | Contenu |
|---|---|
| H2 Les trois familles d'outils | Gant en silicone, brosse, peigne : usage, type de poil, limites |
| H2 Selon le poil | Court, mi-long, long ; renvoi vers un toiletteur ou un vétérinaire pour les nœuds |
| H2 Habituer son chat au brossage | Séances courtes, moments calmes, arrêt dès l'inconfort |
| H2 Entretien de l'outil | Rinçage, séchage |
| Tableau | Outil × poil × prix indicatif (relevé daté) |
| FAQ (3) | « Le gant convient-il aux poils longs ? » (réponse de `brand.json` : un peigne reste nécessaire) · « À quelle fréquence ? » · « Mon chat refuse, que faire ? » |
| Appel à l'action | Fiche gant |
| Liens internes | A5, A1 |

### A7 — Tapis et moquette

| Champ | Contenu |
|---|---|
| H1 | Poils d'animaux sur le tapis : 4 méthodes testées |
| URL | `/guides/poils-animaux-tapis-moquette/` |
| Title | Poils d'animaux sur le tapis : 4 méthodes testées (49) |
| Meta description | Raclette en caoutchouc, aspirateur, gant humide, rouleau : ce qui décolle vraiment les poils de chat et de chien des tapis ras et de la moquette. |
| Clusters | 8 (principal), 3 |
| Longueur | 1 200-1 500 mots |
| Publication | Janvier 2027 |

| Section | Contenu |
|---|---|
| H2 Le test | Même tapis ras, 4 méthodes, plan fixe, temps mesuré |
| H2 Raclette en caoutchouc | Geste, résultat, zone cachée d'abord, tapis à poils longs exclus |
| H2 Aspirateur | Brosse adaptée, passages croisés |
| H2 Gant en caoutchouc humide | Geste, limites |
| H2 Rouleau | Peu efficace sur tapis (transparence, vidéo R08) |
| H2 Tapis à poils longs | Méthodes possibles, sans produit Canapoil |
| Appel à l'action | Raclette ; Grand kit |
| Liens internes | A1, A2 |

### A8 — Lit et couette

| Champ | Contenu |
|---|---|
| H1 | Poils de chat sur le lit et la couette : la routine |
| URL | `/guides/poils-chat-lit-couette/` |
| Title | Poils de chat sur le lit et la couette : la routine (51) |
| Meta description | Couette, draps, plaid : la routine pour garder un lit présentable quand le chat dort avec vous, et l'entretien du linge en machine. |
| Clusters | 12 (principal), 13 |
| Longueur | 1 000-1 300 mots |
| Publication | Février 2027 |

| Section | Contenu |
|---|---|
| H2 Avant de se coucher | Passage court du rouleau sur la couette (vidéo R16) |
| H2 Le plaid de lit | Plaid dédié, lavable |
| H2 Le linge en machine | Secouer avant lavage, nettoyer le filtre ; aucune allégation sur les produits de lavage tiers |
| H2 Arbre à chat et panier | Nettoyage (vidéo R14) |
| FAQ (2) | « Peut-on utiliser le rouleau sur les draps ? » · « Comment enlever les poils d'une couette en plumes ? » (prudence : zone cachée) |
| Appel à l'action | Fiche rouleau |
| Liens internes | A1, A5 |

### A9 — Cadeaux

| Champ | Contenu |
|---|---|
| H1 | Cadeau pour un propriétaire de chat : 12 idées à moins de 40 € |
| URL | `/guides/cadeau-proprietaire-chat/` |
| Title | Cadeau propriétaire de chat : 12 idées à moins de 40 € (54) |
| Meta description | Pour un ami qui vit avec un chat : 12 idées utiles à moins de 40 €, du couchage de fenêtre aux outils anti-poils, avec les délais de livraison réels. |
| Clusters | 14 |
| Longueur | 1 200-1 500 mots |
| Publication | Première version le 1/12/2026 (support Pinterest et e-mail) ; version enrichie en octobre 2027 pour la saison suivante |

| Section | Contenu |
|---|---|
| Introduction | À qui s'adresse la liste ; comment les idées ont été choisies |
| H2 Pour le canapé | Rouleau, Grand kit (produits Canapoil, signalés comme tels) |
| H2 Pour le chat | Couchage de fenêtre, griffoir, jouets (produits d'autres marques, sans lien d'affiliation, cités par catégorie) |
| H2 Pour la voiture | Housse, raclette |
| H2 Délais et retours | Date limite réelle pour Noël ; 30 jours pour changer d'avis chez Canapoil |
| Appel à l'action | Grand kit ; Kit chat d'hiver |
| Liens internes | A10, A1 |

### A10 — Chat à la fenêtre

| Champ | Contenu |
|---|---|
| H1 | Chat à la fenêtre en hiver : installer un couchage sûr |
| URL | `/guides/chat-fenetre-hiver-couchage/` |
| Title | Chat à la fenêtre en hiver : installer un couchage sûr (54) |
| Meta description | Rebord, hamac, tapis : comment offrir à votre chat une place à la fenêtre en hiver, sans source de chaleur dangereuse, et quoi mesurer avant d'acheter. |
| Clusters | 15 |
| Longueur | 1 000-1 300 mots |
| Publication | S12 (fin décembre 2026) |

| Section | Contenu |
|---|---|
| H2 Pourquoi la fenêtre | Observation, sans allégation de comportement non sourcée |
| H2 Mesurer son rebord | Profondeur, matériau, stabilité (vidéo K24) |
| H2 Tapis, coussin ou hamac : comparatif | Tableau ; hamac à ventouses : test de charge et risque de chute (04 §2.2) |
| H2 Sécurité | Jamais sur ou contre un radiateur, un poêle ou une source de chaleur ; fenêtre fermée ou protégée ; avertissements de `brand.json` |
| H2 Entretien | Lavage à 30 °C, séchage à l'air libre |
| Appel à l'action | Tapis de fenêtre ; Kit chat d'hiver (jusqu'au 28/02/2027) |
| Liens internes | A9, A5 |

---

## 4. Calendrier éditorial

| Mois | Articles | Raison |
|---|---|---|
| Décembre 2026 | A1 (S10), A9 (1/12), A2 (S11), A4 et A10 (S12) | A1 sert de page de preuve pour TikTok et l'e-mail ; A9 et A10 servent Pinterest pendant la saison |
| Janvier 2027 | A3, A7, A5 (au plus tard le 25/01) | Indexation avant la hausse de février |
| Février 2027 | A6, A8 ; mise à jour de A1 avec les nouveaux tests | Pic de recherche de février à août |
| Octobre 2027 | Mise à jour de A9 et A10 | Saison cadeaux et hiver suivante |

Rythme : 1 article par semaine au plus (02 §1.7), rédigé par le fondateur à partir des tests filmés ; ≈ 3 h par article (estimation, confiance moyenne).

---

## 5. KPI SEO

| KPI | Source | Cible à 3 mois (janvier 2027) | Cible à 6 mois (avril 2027) |
|---|---|---|---|
| Pages indexées | Search Console | 100 % des fiches et articles publiés | 100 % |
| Impressions mensuelles | Search Console | ≥ 2 000 | ≥ 15 000 |
| Clics mensuels | Search Console | ≥ 50 | ≥ 400 |
| Requêtes en positions 1-10 | Search Console | ≥ 10 | ≥ 50 |
| Visites organiques Google | Cloudflare Web Analytics | ≥ 2 % des sessions | ≥ 10 % des sessions |
| Commandes depuis Google (fiches gratuites + recherche) | Métadonnée UTM Stripe | ≥ 1 par semaine | ≥ 1 par jour |

Cibles : estimations de la direction marketing, confiance faible (domaine neuf, saison basse).
