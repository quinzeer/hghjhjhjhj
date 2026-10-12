# Thème Shopify : Horizon, réglé pour Canapoil

À appliquer le jour de la bascule vers Shopify (première condition remplie parmi celles de `brand.json` > `stack.conditions_bascule_shopify`). Objectif : reproduire en moins d'une journée le site statique (`site/`), mêmes couleurs, mêmes textes, mêmes règles de conversion loyale.

## 1. Choix du thème

| Option | Prix | Éditeur | Points utiles pour Canapoil | Verdict |
|---|---|---|---|---|
| **Horizon** | Gratuit ([Shopify Theme Store](https://themes.shopify.com/themes/horizon/presets/horizon)) | Shopify | Zoom sur image, galeries, vidéos produit, produits recommandés, achat rapide, en-tête collant ([fiche du thème](https://themes.shopify.com/themes/horizon/presets/horizon)) | **Retenu** |
| Dawn | Gratuit | Shopify | Ancien thème par défaut, remplacé par Horizon à la création des nouvelles boutiques ([Pulsev, 24/07/2025](https://www.pulsev.com/en/blogs/our-blog/new-free-themes-created-by-shopify), source secondaire) | Écarté : partir du thème installé par défaut évite une migration |
| Thèmes payants | Payants (prix non relevés) | Tiers | Aucun besoin au palier 1 | Écarté |

**Statut de thème par défaut.** « The default theme has changed from Dawn to Horizon » : Horizon est installé par défaut à la création d'une nouvelle boutique depuis l'été 2025 ([Pulsev, 24/07/2025](https://www.pulsev.com/en/blogs/our-blog/new-free-themes-created-by-shopify)). Source secondaire : confiance moyenne. La fiche officielle confirme le prix (gratuit) et l'éditeur (Shopify), sans mention du statut par défaut. À la création de la boutique, vérifiez dans Boutique en ligne > Thèmes quel thème est installé ; s'il s'agit d'Horizon, rien à ajouter.

Après installation, mesurez la page produit avec PageSpeed Insights (mobile) : le trafic TikTok est mobile à plus de 80 %.

## 2. Couleurs (Paramètres du thème > Couleurs > Schémas)

Les valeurs viennent de `strategie/brand.json` > `marque.palette` ; les contrastes ont été calculés dans la stratégie (§3.5) selon WCAG 2.1.

| Schéma | Usage | Arrière-plan | Texte | Bouton principal (fond / texte) | Bouton secondaire | Bordures |
|---|---|---|---|---|---|---|
| Schéma 1 | Fond général, en-tête | `#FAF5EE` | `#2B211B` (14,49 : 1) | `#B4492A` / `#FFFFFF` (5,35 : 1) | Contour `#2B211B` | `#E3D6C6` |
| Schéma 2 | Sections blanches, cartes produit | `#FFFFFF` | `#2B211B` | `#B4492A` / `#FFFFFF` | Contour `#2B211B` | `#E3D6C6` |
| Schéma 3 | Bandeau d'annonce, section « engagements », pied de page | `#2F4A3C` | `#FAF5EE` (9,7 : 1 en blanc) | `#FAF5EE` / `#2F4A3C` | Contour `#FAF5EE` | `#4F6E5D` |
| Schéma 4 | Sections crème (FAQ) | `#F1E6D8` | `#2B211B` | `#B4492A` / `#FFFFFF` | Contour `#2B211B` | `#E3D6C6` |

Règles : texte secondaire `#6A5B50` (6,0 : 1 sur le fond) ; liens `#B4492A` soulignés ; l'accent moutarde `#E3A93B` sert uniquement aux pastilles et étoiles, **toujours avec un texte `#2B211B`, jamais blanc** ; erreurs `#B42318`.

## 3. Typographie (Paramètres du thème > Typographie)

| Usage | Police | Graisse | Remarque |
|---|---|---|---|
| Titres | Fraunces | 600-700 | Chercher « Fraunces » dans le sélecteur de polices de Shopify. Si elle n'y figure pas, choisir une serif douce de la bibliothèque (Lora, par exemple) : à vérifier dans le sélecteur |
| Texte, boutons, prix | DM Sans | 400, 500, 700 | Idem ; alternative sans empattement de la bibliothèque si absente |
| Logo provisoire | Texte « canapoil » en Fraunces 700, couleur `#B4492A` | — | Ou téléverser `site/images/og/logo.png` (512 × 512) |

Taille de base : 16 px minimum sur mobile ; titres à l'échelle 110-120 %.

## 4. Réglages généraux du thème

| Réglage | Valeur | Raison |
|---|---|---|
| Barre d'annonce | « Livraison offerte dès 35 € · Expédié depuis la France sous 1 jour ouvré » | Information vraie et vérifiable, sans urgence |
| En-tête | Collant ; menu : Boutique, Le rouleau, Grand kit, Questions fréquentes, À propos | Identique au site statique |
| Panier | Type **tiroir** ; boutons de paiement accéléré **désactivés dans le panier** ; note de commande désactivée | La case CGV du panier ne doit pas pouvoir être contournée (`theme/snippets/canapoil-case-cgv.liquid`) |
| Cartes produit | Image 4:3, deuxième image au survol désactivée tant qu'il n'y a pas de vraies photos ; achat rapide activé | Ajout en un geste depuis les collections |
| Favicon | `site/images/og/logo.png` | — |
| Réseaux sociaux | TikTok, Instagram, Pinterest, YouTube une fois les comptes créés | — |
| Applications interdites | Comptes à rebours, fenêtres « X vient d'acheter », compteurs de stock inventés, importeurs d'avis | Pratiques commerciales trompeuses (03 §1.7 et §1.8) |

## 5. Page produit (modèle « produit par défaut »)

Ordre des blocs de la section « Informations produit », du haut vers le bas :

| # | Bloc | Contenu |
|---|---|---|
| 1 | Galerie | 4:3, zoom activé, vignettes sous l'image principale ; vidéo de démonstration par tissu dès qu'elle existe |
| 2 | Texte (petit, majuscules) | « Notre produit phare » sur le rouleau uniquement |
| 3 | Titre | Nom du produit |
| 4 | Prix | Prix TTC ; ne jamais renseigner « Prix barré » (colonne `Compare-at price` vide dans le CSV) |
| 5 | Texte | « Livraison 3,90 €, offerte dès 35 € » (ou « Livraison offerte » sur les kits concernés) |
| 6 | Texte enrichi | Les 5 bénéfices de `brand.json` en liste à puces |
| 7 | Sélecteur de variante | Aucun : les kits sont des produits distincts, liés par le bloc 9 |
| 8 | Quantité + boutons d'achat | Boutons de paiement accéléré désactivés |
| 9 | Texte enrichi « Choisissez votre formule » | Liens vers Grand kit (en premier, « Le plus complet, livraison offerte »), Kit anti-poils, Duo, Kit chat d'hiver, avec l'économie écrite en texte |
| 10 | Texte | « Expédié sous 1 jour ouvré depuis la France, livré en point relais en 3 à 6 jours ouvrés. 30 jours pour changer d'avis. Paiement sécurisé. » |
| 11 | Lignes repliables | « Où il marche, et où il marche moins bien » ; « Caractéristiques » ; « Livraison et retours » ; « Sécurité du produit » (voir §6) |

Sections suivantes du modèle :

| # | Section | Contenu |
|---|---|---|
| 1 | Colonnes avec image | « Comment ça marche » : 3 étapes (`site/images/illustrations/etape-1.svg` à `etape-3.svg`, converties en PNG, ou photos) |
| 2 | Bloc d'application Judge.me | Avis vérifiés ; tant qu'il n'y en a aucun, texte « Les premiers avis vérifiés arrivent » et explication de la collecte (CGV art. 13) |
| 3 | Contenu repliable | FAQ du produit (`brand.json` > `produits[].faq`) |
| 4 | Produits recommandés | Titre « Complétez la maison » |

## 6. Informations de sécurité (GPSR)

Le CSV place déjà le bloc GPSR complet dans la description de chaque produit et de chaque kit : l'information est affichée dès l'import, sans réglage. Pour l'afficher plutôt dans une ligne repliable dédiée :

1. Paramètres > Données personnalisées > Produits > Ajouter une définition, quatre fois : `custom.gpsr_fabricant` (texte multiligne), `custom.gpsr_responsable_ue` (texte multiligne), `custom.gpsr_identification` (texte sur une ligne), `custom.gpsr_avertissements` (texte multiligne).
2. Remplir ces champs sur chaque produit à partir de `brand.json` > `produits[].gpsr` (en remplaçant `{{FABRICANT_…}}` par les coordonnées du dossier fournisseur).
3. Dans la ligne repliable « Sécurité du produit », insérer ces métachamps comme sources dynamiques.
4. Retirer alors le bloc GPSR de la description pour éviter le doublon.

Une fiche sans ces quatre informations ne doit pas être publiée (03 §2.3).

## 7. Page d'accueil

| # | Section | Contenu (repris de `site/index.html`) |
|---|---|---|
| 1 | Image avec texte (bannière) | Titre « Les câlins sur le canapé, les poils à la poubelle. » ; bouton « Découvrir le rouleau » ; 3 puces : réutilisable, expédié depuis la France en 3 à 6 jours ouvrés, 30 jours pour changer d'avis |
| 2 | Colonnes | « Comment marche le rouleau », 3 étapes, avec la phrase sur les tissus où il marche moins bien |
| 3 | Collection en vedette | Collection « Kits », Grand kit en premier |
| 4 | Texte enrichi (schéma 3) | « Une boutique honnête, vérifiable » : les 6 engagements |
| 5 | Collection en vedette | « À l'unité » |
| 6 | Bloc Judge.me | Avis vérifiés |
| 7 | Contenu repliable | 4 questions fréquentes |
| 8 | Inscription à la newsletter | « Des astuces anti-poils, une fois par mois », consentement explicite |

## 8. Pied de page et pages obligatoires

| Élément | Réglage |
|---|---|
| Menu « Informations légales » | Mentions légales, CGV, Confidentialité, Cookies, Retours et rétractation, Livraison |
| Lien « renoncer au contrat ici » | Élément de menu vers `/pages/retractation`, libellé exact, présent dans le pied de page de toutes les pages |
| Texte du pied de page | « Prix en euros TTC. Médiateur de la consommation : {{MEDIATEUR}}. Marque française. Produits fabriqués en Chine, contrôlés et expédiés depuis la France. » |
| Bannière de cookies | Paramètres > Confidentialité des clients > Bannière de cookies : régions UE/EEE au minimum ; vérifier en navigation privée qu'aucun pixel ne part avant le choix et que le refus est aussi accessible que l'acceptation |
| Rétractation en ligne | Section `theme/sections/canapoil-retractation.liquid` dans un modèle `page.retractation` |
| Case CGV | Extrait `theme/snippets/canapoil-case-cgv.liquid` dans le panier (page et tiroir) |
