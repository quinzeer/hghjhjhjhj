# 07 — Plan marketing organique sur 90 jours : Canapoil

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 (version corrigée après la [revue red team](../docs/revue-red-team.md) : plan ramené à 25 heures par semaine) |
| Rôle | Direction du marketing organique |
| Période | Lundi 12/10/2026 (S1) → dimanche 10/01/2027 (S13), calée sur le palier 0 de [04 §6.2](../strategie/04-strategie.md) |
| Entrées | [`brand.json`](../strategie/brand.json), [04 — Stratégie](../strategie/04-strategie.md), [02 — Acquisition](../recherche/02-acquisition.md), [05 — Finance](../finance/05-analyse-financiere.md), [relevé Google Trends FR du 12/10/2026](../recherche/donnees/google-trends-fr-2026-10-12.csv) |
| Livrables liés | [scripts-tiktok.md](scripts-tiktok.md) · [createurs-affiliation.md](createurs-affiliation.md) · [emails.md](emails.md) · [seo-contenu.md](seo-contenu.md) · [lancement-30-jours.md](lancement-30-jours.md) · [bascule-payant.md](bascule-payant.md) |
| Conventions | Chiffre sourcé = lien. Sinon « estimation » + confiance **élevée / moyenne / faible**. « 02 §4.4 » renvoie à une section d'un dossier du projet. |

---

## 0. L'essentiel en une page

| Sujet | Décision marketing | Justification chiffrée |
|---|---|---|
| Canal moteur | TikTok (compte de marque) jusqu'à la porte 1, puis **TikTok Shop** dès que le stock est en France | TikTok Shop convertit ≈ 0,042 % des vues en commandes contre ≈ 0,0034 % pour le lien en bio, soit 12 fois plus (02 §4.3, estimation, confiance faible) |
| Cadence | **2 vidéos par jour** sur TikTok à partir de S3, recyclées sur Reels et Pinterest seulement ; LIVE à partir de S12 ; 4 articles SEO avant février | Le plan initial (3 vidéos par jour, Shorts, LIVE dès S8, 10 articles) demandait 35 à 43 heures par semaine avec ses propres durées unitaires, pour un budget de 20 à 25 heures (revue red team M5). 02 §1.2 : 15 vidéos par produit avant de conclure, atteintes sur S3-S5 |
| Production | 1 smartphone, 1 échantillon par produit, 2 sessions de tournage de 2 h 30 par semaine | ≈ 14 vidéos par semaine pour **25 heures** de travail total, détail au §4.5 (estimation, confiance moyenne). Si le client dispose réellement de 35-40 heures, le plan à 3 vidéos par jour peut être rétabli (04 §8 décision 6) |
| Piliers | 5 piliers ; 35 % du volume sur le « banc d'essai par tissu » | La promesse de marque repose sur la preuve vidéo (`brand.json` → `marque.promesse`) |
| Saison | Novembre-décembre : angles « invités des fêtes », « cadeau », « chat à la fenêtre » ; le tapis de fouille, challenger, culmine en novembre (indice 1,30). Février-août : angles « mue » et « poils partout » ; si le rouleau gagne, stock principal acheté fin janvier pour la hausse de février | Google Trends FR sur 5 ans : l'intérêt pour « anti poils » tombe à **0,54** de sa moyenne annuelle en décembre et culmine à **1,21** en août ; « poils de chat » au plus bas en novembre (0,74), au plus haut en mai (1,16) (calcul marketing sur les [séries brutes](../recherche/donnees/), confiance moyenne) |
| Portes | Porte 1 le **15/11/2026** ; porte 2 = ≥ 3 commandes par jour sur 7 jours après l'arrivée du stock | `brand.json` → `lancement` |
| Budget marketing cash | **0 € de publicité**. 5 échantillons créateurs prélevés sur le micro-stock ; collaborations d'affiliés seulement avec l'option de trésorerie a (04 §5.3) | 04 §5.3 ; [bascule-payant.md](bascule-payant.md) |
| Objectif J+90 (nominal) | Trajectoire ≥ 5 commandes par jour | 04 §6.2. Le scénario réaliste de la finance place la porte 2 en mars-avril 2027 (05 §9.3) : les cibles hebdomadaires ci-dessous portent une valeur nominale et un plancher d'alerte |

**Ce que la saisonnalité change.** Le lancement tombe au creux annuel de la recherche « poils » (indices 0,54 à 0,84 d'octobre à décembre). Le produit reste démontrable en 3 secondes, mais l'urgence ressentie est plus faible qu'au printemps. Le plan compense par trois déclencheurs propres à la saison : les invités des fêtes (canapé présentable), le cadeau à moins de 40 € et le chat qui cherche la chaleur près de la fenêtre (tapis thermique). Le stock de contenus « mue » et les articles SEO sont préparés en décembre-janvier pour la hausse de février.

---

## 1. Configuration des comptes (semaine 1)

### 1.1 Règles communes

| Règle | Détail |
|---|---|
| Identifiant | `@canapoil` réservé le même jour sur toutes les plateformes. Repli dans cet ordre : `@canapoil.fr`, `@canapoil_fr`. Même photo de profil partout : mot « canapoil » en Fraunces 700, terracotta `#B4492A` sur crème `#FAF5EE` (`brand.json` → `logo_provisoire`) |
| Sécurité | Adresse de connexion sur le domaine (`{{EMAIL}}`), double authentification sur chaque compte, gestionnaire de mots de passe, codes de secours stockés hors ligne. Une perte de compte TikTok en phase 0 coûte tout l'historique de portée |
| Lien | Un seul lien par profil vers `https://canapoil.fr/?utm_source=<plateforme>&utm_medium=bio`. Aucune page de liens intermédiaire : elle perd 50 à 80 % des clics selon UniLink, cité en 02 §2.3 (fiabilité faible) |
| Mentions | Aucun drapeau, aucune mention « made in France ». Formule autorisée : « Expédié depuis la France » (`brand.json` → `origine_transparence`) |
| Musique | Bibliothèque de musique commerciale de TikTok uniquement sur le compte Business ; sons originaux et voix off ailleurs. Aucune musique sous droits dans une vidéo réutilisée en publicité |

### 1.2 Paramétrage par plateforme

| Plateforme | Type de compte | Bio (limite de l'application) | Réglages à faire en S1 | Rôle dans le plan |
|---|---|---|---|---|
| **TikTok** | Compte Business, catégorie « Animaux » ou « Maison » | « Les câlins sur le canapé, les poils à la poubelle. Testé tissu par tissu. » (73 caractères ; limite de 80) | Lien site dans la bio : vérifier dans l'application que le champ est disponible sans seuil d'abonnés (sources contradictoires, 02 §1.2) ; réglage de divulgation « Votre marque » sur chaque vidéo de produit ; légendes automatiques activées ; téléchargement des vidéos par les tiers désactivé | Canal moteur ; test des accroches ; vente via TikTok Shop dès S8 |
| **TikTok Shop** (à partir de S8) | Seller Center France, compte officiel = le compte TikTok ci-dessus | — | Dossier déposé en S1 (SIRET, n° de TVA intracommunautaire, pièce d'identité du représentant, IBAN) ; boutique activée seulement quand le stock est en France ; 8 fiches (4 produits + 4 kits) ; modèle d'expédition conforme (étiquette sous 2 jours ouvrés, livraison sous 4 jours ouvrés, [politique TikTok Shop](https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897)) ; mission « nouveau vendeur » à 4 % pendant 60 jours, à accepter dans les 15 jours avec au moins 5 produits en stock ([Speed Ecom, mis à jour le 14/09/2026](https://speed-ecom.eu/blog/tiktok-shop-france-2026-guide-complet-vendre/)) | Achat dans l'application ; affiliation des créateurs ; LIVE |
| **Instagram** | Compte professionnel « Entreprise », relié à une Page Facebook minimale (nécessaire pour Meta Business Suite et la future publicité) | « Les câlins sur le canapé, les poils à la poubelle. Outils anti-poils testés en vidéo sur vrais tissus. Expédiés depuis la France. » (≤ 150) | 5 stories à la une : Tests par tissu · Où ça ne marche pas · Livraison · Retours 30 jours · Coulisses ; durée des Reels à vérifier dans le sélecteur de l'application (90 s ou 3 min selon les comptes, [Kontentino](https://www.kontentino.com/fr/questions-et-reponses/quelle-est-la-duree-des-reels-instagram/)) | Recyclage des vidéos TikTok ; preuve sociale ; vivier de créatives pour la phase payante |
| **YouTube** | Chaîne de marque (compte Google de la société), identifiant `@canapoil` | Description de chaîne : promesse + liste des tissus testés + lien du site | Lien du site dans l'en-tête de la chaîne ; liste de lecture « Tests par tissu » ; les liens des descriptions de Shorts ne sont pas cliquables depuis le 31/08/2023 (02 §1.5) | Chaîne réservée en S1 ; Shorts et vidéo longue mensuelle (« test complet 5 tissus ») à partir du palier 1, faute de temps dans le plan de 25 heures |
| **Pinterest** | Compte professionnel | « Canapoil : outils simples pour vivre avec un chat ou un chien sur le canapé. Tests vidéo par tissu, astuces anti-poils, idées d'aménagement. Expédié depuis la France. » | Revendication du site `canapoil.fr` (balise méta ou fichier à déposer par l'agent site) ; 6 tableaux : Poils de chat sur le canapé · Poils de chien dans la voiture · Chat à la fenêtre en hiver · Canapé et animaux : tissus · Idées cadeaux propriétaires de chat · Tests Canapoil ; catalogue produits à partir du flux XML du site (format à valider dans Pinterest) | Trafic cliquable direct vers les fiches ; épingles à durée de vie de plusieurs mois ; 2 à 6 mois avant un trafic régulier (02 §1.6, estimation, confiance moyenne) |
| **Google** | Merchant Center | — | Fiches gratuites activées avec le flux `site/flux/google-merchant.xml` (02 §1.7) ; Search Console sur `canapoil.fr` ; compte Google Ads sans dépense pour accéder au Keyword Planner (volumes réels de [seo-contenu.md](seo-contenu.md)) | Trafic gratuit d'intention d'achat |
| **E-mail** | Brevo gratuit | — | Liste « Liste d'attente » + modèle de double opt-in déjà branchés sur `/api/inscription` (fonction du site) ; domaine d'envoi authentifié (SPF, DKIM, DMARC) ; suivi des ouvertures désactivé sauf consentement spécifique (voir [emails.md](emails.md) §1) | Liste d'attente avant la porte 1 ; flux automatiques ensuite |

### 1.3 Points de configuration du site demandés à l'agent site

| # | Demande | Raison | Échéance |
|---|---|---|---|
| 1 | Phase de vente dans `brand.json` → `livraison.phase` (`liste_attente` par défaut, le serveur refuse tout paiement) | Aucune vente avant le signal | **Fait** (12/10/2026) |
| 2 | Renseigner `reseaux` (TikTok, Instagram, Pinterest, YouTube) dans `config.js` | Liens de profil en pied de page | S1 |
| 3 | Conserver les `utm_*` en `sessionStorage` et les transmettre en métadonnées de la session Stripe et en attributs Brevo ; autoriser Cloudflare Web Analytics dans la CSP | Attribuer chaque commande et chaque inscription à une plateforme et à un script (`utm_content=R02`) | **Fait** (12/10/2026) |
| 4 | Section `/guides/` générée par `site/outils/generer.py` | Accueil des 10 articles de [seo-contenu.md](seo-contenu.md) | S10 |
| 5 | **Non réalisé** : case de consentement non pré-cochée pour les rappels de panier sur `/panier/`, e-mail transmis à Stripe, `after_expiration.recovery` et fonction webhook. Tant qu'elle n'existe pas, aucune relance de panier (PA1-PA3 suspendus, [emails.md](emails.md)) | La CNIL qualifie la relance de panier de message promotionnel soumis au consentement préalable ([FAQ CNIL, question 16](https://www.cnil.fr/fr/faq-recommandation-pixels-courriers-electroniques)) ; la collecte du consentement par Stripe Checkout est réservée aux entreprises et clients situés aux États-Unis ([Stripe](https://docs.stripe.com/payments/checkout/promotional-emails-consent)) | Avant l'ouverture des précommandes |
| 6 | Dates de précommande dans `brand.json` → `livraison.precommande`, calculées après la commande du stock : date de commande + 90e centile du transit mesuré sur les échantillons + 3 jours ouvrés, puis + 6 jours ouvrés, plafond 30 jours ; `generer.py` refuse des dates absentes ou au-delà du plafond | Exemple nominal (transit de 12 jours) : expédition à partir du 2/12, livraison au plus tard le 10/12 ([lancement-30-jours.md](lancement-30-jours.md)) | **Fait** ; dates à saisir à la porte 1 |
| 7 | Champ caché `produit` sur chaque formulaire de liste d'attente, transmis à Brevo (attribut `PRODUIT`) ; page `/liste-attente/tapis-de-fouille/` pour le challenger | Mesurer les inscriptions de chaque produit pendant le duel de la porte 1 ([scripts-tiktok.md](scripts-tiktok.md) §2.1) : lien de la bio vers la fiche du rouleau ou la page du tapis selon la vidéo | **Fait** (12/10/2026) |

---

## 2. Piliers de contenu

| # | Pilier | Part du volume | Objectif | Formats | Exemples de scripts |
|---|---|---|---|---|---|
| P1 | **Le banc d'essai** : un tissu, un geste, un résultat filmé sans coupe | 35 % | Prouver ; traiter l'objection « gadget » ; nourrir la recherche TikTok (« enlever poils chat canapé velours ») | Démonstration, avant/après en plan-séquence, comparaison, test sur 5 tissus, « là où ça ne marche pas » | R02, R05, R07, R08, R09, K22 |
| P2 | **La vie sur le canapé** : humour bienveillant, situations reconnaissables | 25 % | Portée, partages, abonnés | POV, sketch, réaction, « les types de chats sur un canapé » | R01, R03, R12, R16 |
| P3 | **Réponses aux commentaires** : prix, délai, tissu, entretien | 15 % | Conversion ; FAQ vivante | Réponse vidéo à un commentaire, objection | R06, R13, R18, TF29 |
| P4 | **Coulisses de la marque** : lancement, choix du fournisseur, contrôle, emballage, délais réels | 15 % | Confiance (origine, délai, sérieux) ; attachement au fondateur | Storytelling, « je lance ma marque », déballage du vrai colis | R10, R11, R19, R20 |
| P5 | **Astuces sans produit** : habitudes, entretien des tissus, organisation | 10 % | Enregistrements et partages ; crédibilité ; recherche | Liste « 3 habitudes », tutoriel | R17, articles SEO recyclés |

**Règles de preuve applicables à tous les piliers**

| Règle | Application |
|---|---|
| Plan-séquence pendant toute démonstration | Aucune coupe ni accélération entre l'avant et l'après ; nombre d'allers-retours affiché à l'écran |
| Mêmes conditions | Même lumière, même angle, même distance pour l'avant et l'après ; aucun filtre qui change le contraste du tissu |
| Échec montré | Une vidéo « là où ça ne marche pas » toutes les 2 semaines (cuir, soie, tapis à poils longs) |
| Allégations exclues | Santé ou bien-être médical de l'animal, allergies, « 100 % des poils », « écologique », « made in France », « le meilleur » (`brand.json` → `regles_commerciales.allegations_interdites`) |
| Bien-être animal | Le rouleau ne touche jamais l'animal ; aucune scène où l'animal est contraint ; tournage arrêté si l'animal montre de l'inconfort |
| Poils déposés volontairement | Autorisé seulement si la vidéo le dit (« j'ai récupéré les poils du brossage de la semaine et je les ai déposés sur ce plaid ») |

---

## 3. Cadence de publication

### 3.1 Volume par plateforme

| Plateforme | S1 | S2 | S3-S13 | Décalage avec TikTok | Sélection |
|---|---|---|---|---|---|
| TikTok | 1 par jour | 2 par jour | **2 par jour** (≈ 12 h et 19 h ; ajuster après 3 semaines selon l'onglet « Abonnés » des statistiques) | — | Toutes les vidéos |
| TikTok LIVE | — | — | 1 par semaine à partir de S12 (si le compte y est éligible) | — | Format : démonstration sur les tissus envoyés par les spectateurs en photo, questions-réponses, délai réel |
| Instagram Reels | — | 1 par jour | 1 à 2 par jour | J+1 à J+2 | Les vidéos TikTok dont la rétention à 3 s est dans la moitié haute de la semaine |
| Instagram Stories | — | 2 par semaine | 3 par semaine | Libre | Sondages (« quel tissu tester demain ? »), coulisses, colis du jour |
| YouTube Shorts | — | — | Suspendu jusqu'au palier 1 (temps) | — | — |
| YouTube long | — | — | Aucun avant février | — | « Test complet sur 5 tissus » ; intégré à l'article pilier |
| Pinterest | — | — | 2 épingles par jour (1 vidéo + 1 image extraite) | J+1 à J+7 | Démonstrations et avant/après ; lien vers la fiche produit concernée |

### 3.2 Répartition hebdomadaire des 14 vidéos TikTok

| Période | P1 Banc d'essai | P2 Canapé | P3 Réponses | P4 Coulisses | P5 Astuces | Produits concernés |
|---|---|---|---|---|---|---|
| S1-S2 (avant échantillon) | 0 | 5 | 0 | 2 | 3 | Aucun produit visible : problème, situations, fondateur (7 puis 14 vidéos) |
| S3 (échantillons reçus) | 6 | 3 | 2 | 2 | 1 | Rouleau, tapis de fouille (premières démonstrations), gant, raclette |
| **S4-S5 (duel)** | 7 | 2 | 2 | 2 | 1 | **7 rouleau + 7 tapis de fouille par semaine** : ≈ 15 démonstrations par produit avec S3 (5 angles × 3 accroches) |
| S6-S13 | 5 | 3 | 3 | 2 | 1 | Héros retenu à la porte 1 ; kits ; tapis thermique (si stock) |

---

## 4. Production avec un smartphone et un seul échantillon

### 4.1 Matériel

| Élément | Solution à 0 € | Option si les marges le permettent | Note |
|---|---|---|---|
| Caméra | Smartphone, caméra arrière, 1080p ou 4K à 30 images/s, format vertical 9:16 | — | Nettoyer l'objectif avant chaque session |
| Stabilité | Pile de livres ou étagère ; téléphone calé contre un verre | Pince-trépied (≈ 10-15 €, estimation) | Plan fixe obligatoire pour les avant/après |
| Lumière | Fenêtre de côté, entre 10 h et 15 h ; lampe éteinte pour éviter les dominantes | Petit panneau LED | Lumière identique avant/après |
| Son | Micro du téléphone à moins de 50 cm ; pièce avec rideaux et coussins | Micro-cravate filaire | Le bruit du rouleau (ASMR) sert de son original |
| Montage | CapCut gratuit (sous-titres automatiques à corriger), export sans filigrane | — | Toujours exporter le fichier maître depuis CapCut, jamais télécharger depuis TikTok |
| Visuels fixes | Canva gratuit, gabarits aux couleurs de `brand.json` | — | Polices Fraunces (titres) et DM Sans (texte) |
| Tissus de test | Canapé, plaid polaire, couette, siège auto, arbre à chat de la maison ou de proches ; coupons de velours et de lin achetés au mètre si absents (≈ 5-10 €, estimation) | — | Liste fixe de 5 tissus pour la série « banc d'essai » |
| Animal | L'animal du fondateur ou de proches, avec leur accord écrit pour la diffusion | — | Le visage d'un proche ne figure qu'avec son accord écrit |

### 4.2 Gestion de l'échantillon unique

| Règle | Pourquoi |
|---|---|
| Filmer le **déballage et la première utilisation dès réception**, en 3 angles, avant tout autre usage | Une première utilisation ne se rejoue pas ; ces images servent à R11, R20 et aux épingles |
| Vider le réservoir et essuyer la bande après chaque prise | Résultat comparable d'une prise à l'autre ; image propre |
| Noter la date de mise en service sur l'étiquette du tableur | Permet un contenu honnête « après 1 mois », « après 3 mois » d'usage réel |
| Tester d'abord le second échantillon (fournisseur B) hors caméra sur 3 tissus | 04 §2.5 : échec sur 2 tissus sur 3 = critère d'arrêt du fournisseur |
| Ne pas filmer de vidéo qui demande deux unités (Duo) avant l'arrivée du stock | Le Duo n'apparaît qu'en S8 |
| Ne jamais présenter l'échantillon comme le produit « Canapoil » emballé | Avant le stock, la vidéo dit « échantillon » ; l'emballage Canapoil n'apparaît qu'avec le stock étiqueté |

### 4.3 Session de tournage type (3 heures, 10 à 11 vidéos)

| Créneau | Durée | Contenu | Sortie |
|---|---|---|---|
| Préparation | 20 min | Lire les 5 scripts du jour ; installer le plan fixe ; vérifier la lumière ; préparer les tissus | Liste de plans cochable |
| Bloc 1 — démonstrations | 60 min | Plans-séquences avant/après sur 3 tissus, plans serrés du réservoir, vidage | 4 vidéos + 15 plans de coupe |
| Bloc 2 — face caméra et voix | 45 min | Accroches A, B et C de chaque script (3 prises par accroche), réponses aux commentaires de la semaine | 3 vidéos + 15 accroches |
| Bloc 3 — situations | 40 min | POV, animal sur le canapé, plans d'ambiance | 3 vidéos + plans de coupe |
| Rangement | 15 min | Nommage `AAAAMMJJ_IDscript_accroche_prise.mp4` ; sauvegarde sur un drive | Banque de plans réutilisable |

Montage : 25 à 35 minutes par vidéo (estimation, confiance moyenne). Deux sessions de 2 h 30 produisent les 14 vidéos de la semaine.

### 4.5 Budget-temps hebdomadaire : 25 heures (correction M5)

| Poste | Plan initial (durées unitaires de ce document) | Plan retenu | Heures retenues |
|---|---|---|---|
| Tournage | 2 × 3 h | 2 × 2 h 30 | 5,0 |
| Montage | 21 vidéos × 25-35 min = 9-12 h | 14 vidéos × 25 min (gabarits CapCut) | 5,8 |
| Recyclage | 10 vidéos × 30 min = 5 h | Reels (5 min) et Pinterest (5 min) pour 10 vidéos | 1,7 |
| LIVE | 1-2 × 1 h 30 dès S8 | Aucun avant S12, puis 1 × 1 h | 0 (1 dès S12) |
| Communauté (réponses dans l'heure, messages) | ≈ 3,5 h | Deux créneaux de 15 min par jour | 3,5 |
| Créateurs (recherche, messages, suivi) | 2-3 h | 2 h (option a) | 2,0 |
| SEO | 10 articles ≈ 3,5 h par semaine | 4 articles avant février (A1, A2, A9, A3) | 1,5 |
| Colisage et SAV | 3-4 h | 3 h | 3,0 |
| Administration, pilotage, revue hebdomadaire | 1 h | 1,5 h (tableur `docs/pilotage.xlsx`) | 1,5 |
| **Total** | **≈ 35-43 h** | | **≈ 24 h** (25 h dès S12 avec le LIVE) |

Le modèle financier compte désormais 25 heures par semaine (`HEURES_FONDATEUR`) : 3,77 € de l'heure en dividendes nets dans le scénario réaliste sur 18 mois (05 §4.3).

### 4.4 Banque de plans à constituer en S3

| Code | Plan | Usage |
|---|---|---|
| B01 | Chat qui saute sur le canapé, ralenti naturel du téléphone désactivé | Accroches P2 |
| B02 | Poils en lumière rasante sur velours sombre | Accroches « problème » |
| B03 | Main qui fait 5 allers-retours, plan fixe, compteur | Démonstrations |
| B04 | Ouverture du réservoir au-dessus de la poubelle, plan serré | Fin de vidéo, ASMR |
| B05 | Siège auto en tissu avant et après | Persona Julien et Sarah |
| B06 | Rouleau sur cuir : aucun effet visible | « Là où ça ne marche pas » |
| B07 | Colis préparé, étiquette importateur visible (dès le stock) | Coulisses, délais |
| B08 | Chat sur le rebord de fenêtre, lumière d'hiver | Tapis thermique |

---

## 5. Recyclage multi-plateformes

### 5.1 Chaîne de publication d'une vidéo

| Étape | Plateforme | Adaptation | Temps |
|---|---|---|---|
| 1 | TikTok | Légende avec le mot-clé principal (ex. « enlever poils chat canapé velours ») prononcé dans les 3 premières secondes et écrit à l'écran ; 3 à 5 hashtags ; ancre produit TikTok Shop dès S8 ; divulgation « Votre marque » | 5 min |
| 2 | Instagram Reels (J+1 à J+2) | Même fichier maître sans filigrane ; légende réécrite en vouvoiement ou tutoiement selon le ton du compte ; appel à l'action « lien dans la bio » ; couverture lisible dans la grille | 8 min |
| 3 | YouTube Shorts (J+2), à partir du palier 1 | Titre = question recherchée (« Comment enlever les poils de chat d'un canapé en velours ? ») ; vidéo longue associée liée au Short | 5 min |
| 4 | Pinterest (J+1 à J+7) | 1 épingle vidéo + 2 images extraites (avant, après) avec texte superposé ; titre et description avec le mot-clé ; lien vers la fiche produit avec `utm_source=pinterest&utm_medium=pin&utm_content=<ID>` | 10 min |
| 5 | Site et SEO | Intégration de la vidéo dans l'article ou la fiche produit concernée (`utm_content` identique) | 5 min |

Coût marginal du recyclage limité à Reels et Pinterest : ≈ 10 minutes par vidéo, soit ≈ 1 h 40 par semaine pour les 10 meilleures vidéos (estimation, confiance moyenne). YouTube Shorts et l'intégration au site reprennent au palier 1.

### 5.2 Convention de liens suivis

| Paramètre | Valeurs |
|---|---|
| `utm_source` | `tiktok`, `instagram`, `youtube`, `pinterest`, `email`, `createur-<pseudo>`, `google` |
| `utm_medium` | `bio`, `story`, `pin`, `email`, `affilie`, `fiche-gratuite` |
| `utm_campaign` | `liste-attente-2026`, `precommande-2026`, `noel-2026`, `hiver-2027` |
| `utm_content` | Identifiant du script (`R02`, `K21`, `TF26`) ou de l'e-mail (`BV1`, `PA2`) |

---

## 6. Plan semaine par semaine

Valeurs « nominales » : trajectoire de 04 §6.2. Valeurs « plancher » : seuil sous lequel la règle d'action de la dernière colonne s'applique. Toutes les cibles de vues et de conversion sont des estimations de confiance faible, à recalibrer à J+30 avec les données réelles (02 §9).

| Sem. | Dates | Objectif de la semaine | Actions clés | Vidéos TikTok | KPI nominal | Plancher → action |
|---|---|---|---|---|---|---|
| **S1** | 12-18/10 | Comptes ouverts, site en liste d'attente | §1 ; domaine ; échantillons commandés (2 rouleaux de 2 vendeurs, gant, raclette, tapis thermique, tapis de fouille) ; dossier TikTok Shop déposé ; tableur de suivi (§8) ; Keyword Planner | 7 | 5/5 comptes ; site en ligne ; 7 vidéos | Compte bloqué → contacter le support, publier sur Instagram en attendant |
| **S2** | 19-25/10 | Trouver les accroches qui retiennent | Vidéos « problème » sans produit (P2, P4, P5) ; 3 accroches par thème ; recyclage Reels ; page de liste d'attente du tapis de fouille en ligne ; relevé des prix de 20 rouleaux sur TikTok Shop | 14 | Médiane ≥ 300 vues ; ≥ 1 vidéo > 2 000 vues ; 15 inscrits | Médiane < 150 → revoir les 2 premières secondes (image du problème plus nette, texte plus gros) |
| **S3** | 26/10-1/11 | Échantillons reçus, preuve tournée | Déballage et première utilisation filmés ; transit de chaque échantillon noté ; test sur 3 tissus ; second fournisseur testé hors caméra ; banque de plans B01-B08 | 14 | ≥ 1 vidéo > 10 000 vues ; 40 inscrits ; 5 commentaires d'intention | Échantillon inefficace sur 2 tissus sur 3 → fournisseur B ; sinon le tapis de fouille passe devant (04 §2.5) |
| **S4** | 2-8/11 | Duel, semaine 1 | 7 vidéos rouleau (R02, R05, R08, R09, R03) et 7 vidéos tapis de fouille (TF26-TF30) ; Pinterest lancé ; liste des 50 créateurs commencée ([createurs-affiliation.md](createurs-affiliation.md)) | 14 | 90 inscrits ; médiane ≥ 500 vues ; 10 commentaires d'intention | Aucune vidéo > 5 000 vues sur 10 vidéos d'un produit → changer d'angle, pas de produit |
| **S5** | 9-15/11 | Duel, semaine 2 ; **porte 1 le dim. 15/11** | ≈ 15 vidéos par produit atteintes ; décompte des commentaires d'intention et des inscrits par produit ; taux de clics produit par vidéo ; décision écrite | 14 | **Porte 1** : (≥ 1 vidéo > 50 000 vues avec ≥ 1 % de clics, **ou** ≥ 150 inscrits) **et** taux de clics produit ≥ 1,5 % en moyenne sur les vidéos de démonstration **et** ≥ 20 commentaires d'intention hors entourage | Porte non franchie → 2 semaines de plus sur le meilleur produit ; 3 produits sans porte = arrêt (04 §6.2) |
| **S6** | 16-22/11 | Stock commandé, puis précommandes ouvertes | Lundi : médiateur, Léko, INPI, RC, **commande du micro-stock** ; mercredi : précommandes ouvertes avec les dates calculées ; e-mail d'ouverture à la liste (consentement enregistré) ; vidéos avec appel « lien en bio » ; gant offert aux 30 premières, dans la limite des 30 gants réservés ([lancement-30-jours.md](lancement-30-jours.md)) | 14 | Cible 30 précommandes ; conversion liste → précommande ≥ 10 % | < 10 précommandes à J9 → contenu recentré sur la démonstration ; le stock déjà payé sera écoulé |
| **S7** | 23-29/11 | Tenir l'attention pendant le transit du stock | Black Friday sans remise (R19) ; coulisses du contrôle qualité ; 5 créateurs ciblés contactés ; fiches TikTok Shop prêtes | 14 | 20 précommandes cumulées ; 5 créateurs d'accord | 0 créateur d'accord sur 15 contactés → revoir le message et la grille |
| **S8** | 30/11-6/12 | Stock reçu, précommandes expédiées, TikTok Shop ouvert | Contrôle J-10 le 30/11 ; étiquetage ; expédition des précommandes à partir de la date écrite ; déballage du vrai colis (R20) ; ancres produit ; date limite de Noël affichée dès le passage en vente ; 5 échantillons envoyés aux créateurs | 14 | 100 % des précommandes expédiées à temps ; **porte stock** (≥ 20 précommandes hors entourage, conversion ≥ 8 %) ; ≥ 1 commande par jour | Colis fournisseur absent de France 10 jours avant la date limite → e-mail individuel avec nouvelle date et proposition de remboursement |
| **S9** | 7-13/12 | Premières ventes TikTok Shop régulières | Collaboration ouverte à 12 % (option a) ; angle cadeau (K25) ; Kit chat d'hiver si le tapis est en stock | 14 | ≥ 2 commandes par jour ; ≥ 2 vidéos d'affiliés publiées | Taux clic produit / vues < 0,5 % → retravailler l'ancre et l'appel à l'action |
| **S10** | 14-20/12 | Dernière semaine de Noël | Date limite : **commande avant le mar. 15/12** pour une livraison au plus tard le mer. 23/12 (15/12 + 6 jours ouvrés, `brand.json` → `livraison.noel_2026`) ; aucun compte à rebours fictif ; réassort décidé seulement si la porte stock est franchie | 14 | ≥ 3 commandes par jour sur 7 jours (porte 2 nominale) | < 1 commande par jour → conserver le stock, aucune nouvelle commande fournisseur |
| **S11** | 21-27/12 | Fêtes : angle « invités » | R03 et variantes ; contenu « après les fêtes » préparé ; réponses SAV prioritaires | 14 | Stock ≥ 15 jours de ventes | Stock < 15 jours → mention « réassort le JJ/MM » réelle |
| **S12** | 28/12-3/1 | Recalcul du délai annoncé | 30 livraisons atteintes : 90e centile + 2 jours ouvrés (`brand.json` → `livraison.regle_recalcul`) ; tournage du stock « mue » de février ; premier LIVE si le compte y est éligible | 14 | 5 affiliés actifs ; note moyenne ≥ 4,3/5 | Taux de retour > 8 % → analyse des motifs ; vidéo « bien l'utiliser » |
| **S13** | 4-10/1 | **Revue J+90** | Bilan chiffré ; décision : continuer, changer de héros ou arrêter (critères de 04 §6.2-§6.3 et 05 §9.4) ; stock principal commandé fin janvier si la porte stock est franchie ; plan T1 2027 orienté recherche (février-août) | 14 | Trajectoire ≥ 5 commandes par jour | < 20 commandes sur les 30 jours suivant l'arrivée du stock → critère d'arrêt de 04 §6.3 |

**Volume cumulé** : 175 vidéos TikTok sur 13 semaines (7 + 14 + 11 × 14), soit ≈ 60 vidéos par mois en régime de croisière, sous la cible de 02 §0.2 (90) : c'est le prix d'un plan tenable à 25 heures par semaine.

---

## 7. Animation de la communauté

| Règle | Détail | Indicateur |
|---|---|---|
| Première heure | Répondre aux commentaires dans deux créneaux de 15 minutes, juste après chaque publication | Taux de réponse ≥ 90 % |
| Objections | Chaque objection posée 2 fois devient une réponse vidéo dans la semaine (pilier P3) | ≥ 3 réponses vidéo par semaine |
| Commentaire épinglé | FAQ courte : délai, tissus conseillés, retours 30 jours | Présent sur 100 % des vidéos de produit |
| Commentaires d'intention | Compter chaque compte unique qui écrit « je veux », « où l'acheter », « c'est combien », « lien ? » ; exclure les proches | Critère de la porte 1 |
| Messages privés | Réponse type + vidéo du tissu concerné ; engagement 48 h ouvrées, cible interne 24 h (`brand.json` → `service_client`) | Délai médian de réponse |
| Modération | Masquer insultes et spams ; ne jamais supprimer une critique de fond, y répondre | Registre des critiques dans le tableur |
| Créateurs repérés | Tout abonné qui publie spontanément sur le produit passe dans la liste de [createurs-affiliation.md](createurs-affiliation.md) | Nombre de créateurs issus de la communauté |

---

## 8. Tableau de suivi des KPI

À recopier dans Google Sheets (onglet « KPI hebdo »), rempli chaque lundi matin. Les cibles proviennent de 02 §4.4 (vues), 02 §2.2-2.3 (conversions) et 04 §6.7 (opérations) ; ce sont des estimations de confiance faible.

### 8.1 Définitions et cibles

| # | KPI | Définition | Source | Cible S4 | Cible S8 | Cible S13 | Alerte |
|---|---|---|---|---|---|---|---|
| 1 | Vidéos publiées | Nombre de vidéos TikTok publiées dans la semaine | TikTok | 14 | 14 | 14 | < 10 |
| 2 | Vues médianes par vidéo | Médiane des vues à J+7 des vidéos de la semaine | TikTok Studio | 500 | 1 200 | 2 000 | < 500 après S6 |
| 3 | Rétention à 3 s | Part des spectateurs encore présents à 3 s (courbe de rétention) | TikTok Studio | ≥ 50 % | ≥ 55 % | ≥ 60 % | < 40 % |
| 4 | Taux de complétion | Part des spectateurs qui voient la vidéo en entier | TikTok Studio | ≥ 20 % | ≥ 25 % | ≥ 30 % | < 15 % |
| 5 | Vidéos > 10 000 vues | Nombre cumulé | TikTok | 2 | 6 | 15 | 0 à S5 |
| 6 | Abonnés TikTok | Total en fin de semaine | TikTok | 300 | 1 000 | 3 000 | Croissance < 50 par semaine |
| 7 | Commentaires d'intention | Comptes uniques, cumul sur 14 jours | Décompte manuel | 10 | 30 | 60 | < 20 à la porte 1 |
| 8 | Inscrits liste d'attente | Inscriptions confirmées (double opt-in) | Brevo | 90 | — | — | < 150 à la porte 1 sans vidéo virale |
| 9 | Sessions du site | Visites par semaine | Cloudflare Web Analytics | 400 | 800 | 1 000 | < 200 |
| 10 | Conversion du site | Commandes ÷ sessions | Stripe ÷ Cloudflare | — | 1,0 % | 1,5 % | < 0,8 % |
| 11 | Clics produit | Avant la porte 1 : clics vers le profil ou le site ÷ vues, moyenne des vidéos de démonstration (TikTok Studio). Ensuite : clics sur l'ancre TikTok Shop ÷ vues | TikTok Studio, Seller Center | ≥ 1,5 % | 0,8 % | 1,2 % | < 1,5 % à la porte 1 ; < 0,5 % ensuite |
| 12 | Conversion TikTok Shop | Commandes ÷ clics produit | Seller Center | — | 2,5 % | 3,5 % | < 1,5 % |
| 13 | Commandes par jour | Moyenne sur 7 jours, tous canaux | Stripe + Seller Center | — | 1 | 5 | < 3 sur 14 jours après S10 |
| 14 | Panier moyen site | CA TTC ÷ commandes, port compris | Stripe | — | 34,80 € | 34,80 € | < 30 € |
| 15 | Part des kits | Commandes de kits ÷ commandes site | Stripe | — | ≥ 45 % | ≥ 50 % | < 30 % |
| 16 | Marge moyenne par commande | Selon 04 §4.1 | Tableur | — | ≥ 6,30 € | ≥ 6,30 € | < 5 € |
| 23 | Réserve de trésorerie disponible | Solde bancaire − dettes à 30 jours (fournisseur, TVA) | Banque + tableur | ≥ 300 € | ≥ 300 € | ≥ 300 € | **< 300 € : aucune commande fournisseur ni échantillon** |
| 24 | Stock disponible par produit | Unités vendables (site + TikTok Shop) | `brand.json`, Seller Center | — | ≥ 5 | ≥ 5 | < 5 : précommande ou indisponible |
| 17 | Affiliés actifs | Créateurs avec ≥ 1 vidéo par semaine sur 4 semaines | Seller Center | — | 0 | 5 | < 2 à S13 |
| 18 | Vidéos d'affiliés publiées | Cumul | Seller Center | — | 0 | 15 | — |
| 19 | E-mails : visites suivies | Visites `utm_source=email` ÷ e-mails délivrés (aucun pixel individuel, voir [emails.md](emails.md) §1.1) | Cloudflare + Brevo | ≥ 5 % | ≥ 4 % | ≥ 3 % | < 2 % |
| 20 | Avis vérifiés | Nombre et note moyenne | Formulaire d'avis + TikTok Shop | — | 0 | ≥ 15 ; ≥ 4,3/5 | Note < 4,0 |
| 21 | Délai de livraison P90 | 90e centile en jours ouvrés | Tableur | — | ≤ 6 | ≤ 6 | > 7 |
| 22 | Taux de retour | Retours ÷ commandes livrées | Tableur | — | — | ≤ 5 % | > 8 % |

### 8.2 Grille hebdomadaire à remplir

| KPI | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Vidéos publiées | | | | | | | | | | | | | |
| 2 Vues médianes | | | | | | | | | | | | | |
| 3 Rétention à 3 s | | | | | | | | | | | | | |
| 4 Complétion | | | | | | | | | | | | | |
| 5 Vidéos > 10 k (cumul) | | | | | | | | | | | | | |
| 6 Abonnés TikTok | | | | | | | | | | | | | |
| 7 Commentaires d'intention (14 j) | | | | | | | | | | | | | |
| 8 Inscrits liste d'attente | | | | | | | | | | | | | |
| 9 Sessions site | | | | | | | | | | | | | |
| 10 Conversion site | | | | | | | | | | | | | |
| 11 Clics produit TikTok Shop | | | | | | | | | | | | | |
| 12 Conversion TikTok Shop | | | | | | | | | | | | | |
| 13 Commandes par jour | | | | | | | | | | | | | |
| 14 Panier moyen site | | | | | | | | | | | | | |
| 15 Part des kits | | | | | | | | | | | | | |
| 16 Marge moyenne | | | | | | | | | | | | | |
| 17 Affiliés actifs | | | | | | | | | | | | | |
| 18 Vidéos d'affiliés (cumul) | | | | | | | | | | | | | |
| 19 Visites e-mail | | | | | | | | | | | | | |
| 20 Avis (nombre ; note) | | | | | | | | | | | | | |
| 21 Délai P90 | | | | | | | | | | | | | |
| 22 Taux de retour | | | | | | | | | | | | | |
| 23 Réserve de trésorerie | | | | | | | | | | | | | |
| 24 Stock le plus bas | | | | | | | | | | | | | |

### 8.3 Suivi par vidéo (onglet « Vidéos »)

| Colonne | Contenu |
|---|---|
| ID | Identifiant du script + accroche (ex. `R02-B`) |
| Date, heure, plateforme | — |
| Pilier, produit | P1-P5 ; rouleau, tapis de fouille, kit… |
| Vues J+1, J+7 | — |
| Rétention à 3 s, durée moyenne de visionnage, complétion | TikTok Studio |
| J'aime, commentaires, partages, enregistrements | — |
| Commentaires d'intention | Décompte manuel |
| Visites de profil, clics site (référent), clics produit | TikTok Studio, Cloudflare, Seller Center |
| Commandes attribuées | Métadonnée `utm_content` de Stripe ; Seller Center pour TikTok Shop |
| Décision | Décliner (nouvelle accroche), recycler en publicité plus tard, abandonner l'angle |

**Règle de décision par vidéo** (estimation, confiance moyenne) : une vidéo dont la rétention à 3 s dépasse de 10 points la médiane de la semaine est re-tournée avec 2 nouvelles accroches dans les 7 jours ; un angle sans aucune vidéo au-dessus de la médiane après 3 accroches est abandonné.

---

## 9. Risques propres au marketing organique

| Risque | Probabilité | Parade | Signal |
|---|---|---|---|
| Portée des comptes de marque en baisse (−23 % sur un an selon Socialinsider, 02 §1.2) | Élevée | Ton de créateur plus que de marque ; visage du fondateur dès que possible (04 §8 décision 5) ; affiliés | Médiane < 500 vues après S6 |
| Saison basse de la recherche « poils » (octobre-décembre) | Certaine | Angles invités, cadeau, hiver ; préparation du pic de février | Taux de clic produit < 0,5 % |
| Vidéo jugée « non originale » par TikTok | Faible si les règles du §4 sont suivies | Contenu filmé soi-même ; aucune vidéo de fournisseur ; export sans filigrane | Portée nulle soudaine sur plusieurs vidéos |
| Vidéo virale sans stock | **Moyenne** : la viralité est l'objectif du plan, et 1 M de vues représente ≈ 420 commandes TikTok Shop (02 §4.4) pour 40 rouleaux en stock et ≈ 15 jours de réassort | Procédure de pic (`brand.json` → `livraison.stock.procedure_pic_viral`) : stock TikTok Shop mis à jour toutes les 2 heures (2 fois par jour hors pic) ; site en précommande avec dates réelles dès 5 unités ; réassort express déclenché à 10 unités si la réserve le permet ; aucune ancre produit sur une vidéo qui dépasse 20 000 vues en 6 heures quand le stock couvre moins de 7 jours | > 20 000 vues en 6 heures |
| Commentaire négatif sur l'efficacité | Moyenne | Réponse vidéo avec démonstration sur le tissu cité ; reconnaître les limites (cuir, poils longs) | Plus de 3 critiques identiques |
| Dépendance à TikTok | Élevée | Liste e-mail dès S1 ; Pinterest et Google en parallèle | > 70 % du CA sur TikTok après 6 mois (04 §7) |
| Épuisement du fondateur | Moyenne | Plan ramené à 25 heures (§4.5) ; tournage groupé ; banque de plans | < 10 vidéos par semaine pendant 2 semaines |

---

## Sources

| Réf. | Source | URL |
|---|---|---|
| 02 | Dossier acquisition du projet (entonnoirs, benchmarks, cadence) | [../recherche/02-acquisition.md](../recherche/02-acquisition.md) |
| 04 | Stratégie (portes, paliers, catalogue, lignes rouges) | [../strategie/04-strategie.md](../strategie/04-strategie.md) |
| 05 | Analyse financière (trésorerie, calendrier réaliste) | [../finance/05-analyse-financiere.md](../finance/05-analyse-financiere.md) |
| GT | Google Trends France, 5 ans, relevé du 12/10/2026 ; indices mensuels calculés par la direction marketing | [../recherche/donnees/google-trends-fr-2026-10-12.csv](../recherche/donnees/google-trends-fr-2026-10-12.csv) |
| TTS-exp | TikTok Shop, politique d'expédition France | https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897 |
| TTS-com | Speed Ecom, guide TikTok Shop France (commission 9 %, programme nouveau vendeur à 4 % depuis le 15/06/2026), mis à jour le 14/09/2026 | https://speed-ecom.eu/blog/tiktok-shop-france-2026-guide-complet-vendre/ |
| CNIL-16 | CNIL, FAQ de la recommandation sur les pixels dans les courriels (question 16 : relance de panier) | https://www.cnil.fr/fr/faq-recommandation-pixels-courriers-electroniques |
| Stripe-c | Stripe, consentement aux e-mails promotionnels dans Checkout (réservé aux États-Unis) | https://docs.stripe.com/payments/checkout/promotional-emails-consent |
| IG-durée | Kontentino, durée des Reels Instagram en 2026 | https://www.kontentino.com/fr/questions-et-reponses/quelle-est-la-duree-des-reels-instagram/ |
| LIVE | Artisans 2.0, TikTok Shop France (seuil LIVE de 1 000 abonnés, non confirmé par TikTok) | https://artisansdeuxpointzero.fr/vendre-sur-tiktok-shop-france-guide |
