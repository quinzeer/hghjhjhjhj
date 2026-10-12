# Site Canapoil : prototype de production

Site e-commerce statique (HTML, CSS et JavaScript natifs, aucun framework, aucune étape de build) pour la marque Canapoil, conforme à la stratégie `strategie/04-strategie.md` et alimenté par `strategie/brand.json`. Paiement sur la page hébergée par Stripe, fonctions serveur gratuites (Netlify ou Cloudflare Pages).

| Élément | Valeur |
|---|---|
| Pages | 25 : accueil, boutique, 4 fiches produit, 4 fiches kit, page de liste d'attente du tapis de fouille, panier, commande, `merci.html`, FAQ, à propos, contact, rétractation en ligne, 6 pages légales, 404 |
| JavaScript livré | `assets/js/app.js` + `assets/js/config.js`, ≈ 43 Ko au total (plafond fixé : 60 Ko) |
| Dépendances | Aucune côté navigateur ; aucune dépendance npm côté serveur (appels `fetch` directs aux API Stripe et Brevo) |
| Polices | Fraunces et DM Sans auto-hébergées (`assets/fonts/`, licence OFL) : aucun appel à Google Fonts, donc aucune adresse IP transmise à un tiers à l'ouverture d'une page |
| Source des prix, de la phase et du stock | `data/products.json`, généré depuis `brand.json`, relu par le navigateur **et** par le serveur au moment du paiement : le navigateur ne choisit ni le prix, ni la phase, ni la quantité disponible |
| Vérification | 417 contrôles Playwright réussis (`outils/verifier_site.js`, phases liste d'attente, précommande et vente, CSP appliquée) et 19 tests des fonctions serveur (`outils/tester_fonctions.js`) au 12/10/2026 |

## 1. Arborescence

| Chemin | Rôle |
|---|---|
| `index.html`, `boutique/`, `produits/<slug>/`, `kits/<slug>/`, `faq/`, `a-propos/`, `contact/` | Pages publiques (URL propres : un dossier par page) |
| `panier/`, `commande/`, `merci.html`, `retractation/` | Tunnel et rétractation (non indexés) |
| `mentions-legales/`, `cgv/`, `retours-retractation/`, `livraison/`, `confidentialite/`, `cookies/` | Pages légales adaptées de `recherche/pages-legales/` |
| `assets/css/style.css` | Feuille de style unique, mobile d'abord, jetons de couleur de `brand.json` |
| `assets/js/config.js` | Mode (`demo` ou `production`), clé de site Turnstile, traceurs, réseaux. La phase, les dates et le stock sont dans `strategie/brand.json` |
| `assets/js/app.js` | Panier (localStorage), tiroir, sélecteur d'offres, barre d'achat collante, dates de livraison, consentement, commande, rétractation, inscriptions |
| `data/products.json` | Catalogue public (prix TTC, contenus, GPSR). Ne contient ni coûts ni fournisseurs |
| `netlify/functions/*.js` | Fonctions Netlify : `create-checkout`, `retractation`, `inscription`, `stripe-webhook` |
| `liste-attente/tapis-de-fouille/` | Page de liste d'attente du challenger (duel de la porte 1), non indexée |
| `functions/api/*.js`, `functions/_middleware.js`, `_routes.json` | Mêmes fonctions pour Cloudflare Pages (code partagé : `netlify/lib/coeur.js`) |
| `netlify.toml`, `_headers` | Configuration Netlify ; en-têtes de sécurité (CSP stricte) et de cache, lus par les deux hébergeurs |
| `sitemap.xml`, `robots.txt`, `flux/google-merchant.xml` | SEO et fiches gratuites Google |
| `documents/cgv-canapoil.pdf` | CGV imprimables jointes à l'e-mail de confirmation (support durable) |
| `images/` | Illustrations SVG provisoires et PNG dérivés ; voir `images/README.md` |
| `outils/` | Générateur, rendu des images, tests. Bloqués en ligne (404) sur les deux hébergeurs |

## 2. Travailler en local

Depuis le dossier `dropshipping/` :

```bash
python3 site/outils/generer.py                               # brand.json → products.json, pages, sitemap, flux, kit Shopify
python3 site/outils/generer.py --publication                 # idem, mais refuse s'il reste une variable {{...}} (avant tout déploiement)
NODE_PATH="$(npm root -g)" node site/outils/rendre_images.js  # PNG produits, images de partage, CGV en PDF
cd site && python3 -m http.server 8765 --bind 127.0.0.1       # puis ouvrir http://127.0.0.1:8765
```

Dans un second terminal :

```bash
NODE_PATH="$(npm root -g)" node site/outils/verifier_site.js   # sert lui-même le site (CSP appliquée), génère les variantes de phase, captures dans docs/captures
node site/outils/tester_fonctions.js                                                # fonctions serveur, sans réseau
```

Pour changer un prix, un texte produit, une phase, des dates ou un stock : modifier `strategie/brand.json`, relancer les deux premières commandes, redéployer. Ne modifiez jamais un prix ou un délai directement dans une page HTML.

## 3. Modes et phases

| Réglage | Où | Valeur | Effet |
|---|---|---|---|
| `mode` | `assets/js/config.js` | `"demo"` (par défaut) | Aucun appel serveur ; bandeau « Démonstration » en haut de chaque page ; paiement, rétractation et inscriptions simulés à l'écran |
| | | `"production"` | Appelle `/api/create-checkout`, `/api/retractation` et `/api/inscription` ; charge Turnstile si une clé de site est saisie |
| `livraison.phase` | `strategie/brand.json` | `"liste_attente"` (par défaut) | **Avant la porte 1** : aucune vente, formulaire d'inscription avec consentement et produit d'intérêt, panier masqué ; le serveur refuse tout paiement (503) |
| | | `"precommande"` | Après la commande du stock : exige `livraison.precommande.expedition_a_partir_du` et `livraison_au_plus_tard_le` (≤ 30 jours après la génération, sinon `generer.py` s'arrête). Toutes les pages, la page Stripe et l'e-mail de confirmation affichent ces dates ; « 1 jour ouvré » n'apparaît nulle part (contrôlé par le vérificateur) |
| | | `"vente"` | Stock en France : « expédié sous 1 jour ouvré, livré 3 à 6 jours ouvrés après la commande ». Exige un stock > 0 |
| `produits[].stock_disponible` | `strategie/brand.json` | Entier, mis à jour chaque matin | Plafond par commande contrôlé par le serveur (kits compris). En phase vente, sous `livraison.stock.seuil_bascule_precommande` (5), le produit passe en précommande avec les dates de `livraison.stock.reassort`, ou devient indisponible (formulaire « prévenez-moi ») |
| `regime_tva.affichage_site` | `strategie/brand.json` | `"assujetti"` ou `"franchise"` | Mention sous les totaux (« dont TVA 20 % » ou « TVA non applicable, art. 293 B du CGI ») ; en franchise, adapter aussi l'article 4.1 des CGV |
| `identite` | `strategie/brand.json` | Une valeur par variable | Remplace les `{{...}}` partout (pages, `products.json`, PDF des CGV, flux, kit Shopify) |
| `traceurs` | `assets/js/config.js` | listes vides | Scripts chargés **uniquement après consentement**. Ajouter aussi leurs domaines dans `_headers` (CSP) et dans la page cookies |

## 4. Déploiement gratuit

### Option A : Cloudflare Pages (retenue par la stratégie)

L'offre gratuite autorise l'usage commercial mais interdit de collecter des données de carte sur le site (article 2.2.1 h du [contrat Cloudflare](https://www.cloudflare.com/terms/)) : c'est le cas ici, la carte est saisie sur la page Stripe. Les Pages Functions offrent 100 000 requêtes par jour gratuites ([Cloudflare](https://developers.cloudflare.com/workers/platform/pricing/)) ; `_routes.json` limite leur exécution à `/api/*`.

Le glisser-déposer du tableau de bord **ne compile pas** le dossier `functions` ([documentation Cloudflare](https://developers.cloudflare.com/pages/get-started/direct-upload/)). Deux méthodes fonctionnent :

1. **Wrangler** (ligne de commande) : `cd site && npx wrangler pages deploy . --project-name canapoil` (le dossier `functions` doit se trouver là où la commande est lancée).
2. **Git** : pousser le dossier dans un dépôt GitHub privé, puis Workers & Pages > Create > Pages > Connect to Git ; *Root directory* `site` (ou `dropshipping/site`), *Build command* vide, *Build output directory* `.`.

Puis : Settings > Variables and Secrets (tableau du §5), Custom domains > `canapoil.fr`. Coût : 0 € ; domaine ≈ 10 € par an (estimation, confiance moyenne).

### Option B : Netlify

1. Add new site > Import from Git (ou `npx netlify-cli deploy --prod` depuis `site/`). *Base directory* `site` ; `netlify.toml` fixe `publish = "."` et `functions = "netlify/functions"`.
2. Site configuration > Environment variables (tableau du §5). Les fonctions utilisent `fetch` et Web Crypto natifs : Node 20 ou plus (vérifier Site configuration > Functions > Runtime).
3. Domain management > ajouter `canapoil.fr`.

Point d'attention : l'offre gratuite fonctionne avec des crédits mensuels, et une source secondaire indique que le site est suspendu jusqu'au mois suivant s'ils sont épuisés ([netli.fyi](https://netli.fyi/blog/netlify-free-plan-limits-2026), confiance faible). C'est un risque en cas de vidéo virale ; Cloudflare n'a pas cette limite sur les fichiers statiques.

## 5. Clés et variables d'environnement

| Variable | Obligatoire pour | Valeur |
|---|---|---|
| `SITE_URL` | Toutes les fonctions | `https://canapoil.fr` (sans barre finale). Sert aux URL de retour Stripe et à la vérification de l'origine |
| `STRIPE_SECRET_KEY` | Paiement, vérification des commandes avant un accusé de rétractation | **À saisir seulement à la porte 1.** Clé restreinte `rk_live_…` avec « Checkout Sessions : écriture » (la lecture est incluse) |
| `STRIPE_WEBHOOK_SECRET` | E-mail de confirmation | `whsec_…` affiché à la création du webhook |
| `STRIPE_CASE_CGV` | Facultatif | `oui` ajoute une seconde case CGV sur la page Stripe (exige l'URL des CGV dans Paramètres > Informations publiques) |
| `BREVO_API_KEY` | Rétractation, inscriptions, confirmation | Clé API Brevo (offre gratuite) |
| `EMAIL_EXPEDITEUR` | Idem | Adresse expéditrice validée dans Brevo (domaine authentifié SPF/DKIM) |
| `EMAIL_SERVICE_CLIENT` | Idem | Adresse qui reçoit la copie de chaque accusé et confirmation |
| `NOM_EXPEDITEUR` | Facultatif | « Canapoil » par défaut |
| `BREVO_LISTE_ID`, `BREVO_TEMPLATE_DOI` | Inscriptions | Identifiant de la liste « Liste d'attente » et du modèle de confirmation double opt-in |
| `ORIGINES_AUTORISEES` | Facultatif | Autres origines autorisées, séparées par des virgules (par exemple la boutique Shopify qui réutilise la fonction de rétractation). Toute requête sans en-tête `Origin`, ou d'une autre origine, reçoit 403 (sauf le webhook Stripe, vérifié par signature) |
| `TURNSTILE_SECRET_KEY` | Inscription, rétractation | Clé secrète du widget Cloudflare Turnstile (gratuit) ; la clé de site va dans `config.js` → `turnstile.cle_site`. **Obligatoire avant la mise en production** |
| `CANAPOIL_KV` (liaison, pas une variable) | Limite de 3 requêtes par heure et par adresse IP ; webhooks déjà traités | Cloudflare Pages > Settings > Bindings > KV namespace, nom `CANAPOIL_KV` (offre gratuite : 1 000 écritures par jour). La règle de limitation de l'offre gratuite de Cloudflare ne compte que sur 10 secondes : le compteur horaire est donc dans le code. Sur Netlify, compteur en mémoire seulement (moins fiable) |

### Configurer Stripe (≈ 30 minutes, 0 € d'abonnement)

1. Créer le compte sur stripe.com, renseigner la société (SIREN, IBAN, pièce d'identité du dirigeant).
2. Paramètres > Moyens de paiement : cartes activées ; Apple Pay et Google Pay au choix (aucun surcoût pour le client).
3. Paramètres > Informations publiques : nom « Canapoil », descripteur bancaire `CANAPOIL`, e-mail et téléphone du service client, URL des CGV (`https://canapoil.fr/cgv/`) et de la politique de retours.
4. Paramètres > E-mails clients : activer les reçus pour les paiements réussis.
5. Développeurs > Clés API : créer une clé restreinte « Checkout Sessions : écriture » et la coller dans `STRIPE_SECRET_KEY`.
6. Développeurs > Webhooks : endpoint `https://canapoil.fr/api/stripe-webhook`, événement `checkout.session.completed` ; copier le secret dans `STRIPE_WEBHOOK_SECRET`.
7. En mode test, passer `mode: "production"` dans `config.js` et la phase à `precommande` ou `vente` dans `brand.json`, payer avec la carte `4242 4242 4242 4242`, vérifier la commande dans Stripe (métadonnées : panier, point relais, date d'acceptation des CGV, phase, dates de précommande, `utm_*`) et la réception de l'e-mail de confirmation. Puis remplacer la clé de test par la clé live.

Frais : 1,5 % + 0,25 € par carte standard de l'EEE, 2,8 % + 0,25 € par carte premium ([Stripe](https://stripe.com/fr/pricing)).

Les commandes se traitent depuis le tableau de bord Stripe (Paiements) : adresse, téléphone, articles, point relais demandé (métadonnées). Le prix envoyé à Stripe est recalculé par la fonction à partir de `data/products.json` ; un panier modifié dans le navigateur ne peut pas changer le montant.

### Configurer Brevo (offre gratuite)

1. Créer le compte, authentifier le domaine `canapoil.fr` (Expéditeurs, domaines et IP dédiées > Domaines).
2. Contacts > Listes : créer « Liste d'attente » et noter son identifiant (`BREVO_LISTE_ID`).
3. Modèles : créer le modèle de confirmation double opt-in et noter son identifiant (`BREVO_TEMPLATE_DOI`).
3 bis. Contacts > Paramètres > Attributs : créer `PRODUIT`, `SOURCE`, `CONSENTEMENT_DATE`, `CONSENTEMENT_TEXTE`, `UTM_SOURCE`, `UTM_CAMPAIGN`, `UTM_CONTENT` (texte). Sans eux, Brevo refuse l'inscription (erreur journalisée par la fonction).
4. Paramètres SMTP et API > Clés API : créer la clé (`BREVO_API_KEY`).

## 6. Conformité : ce que fait le site

| Exigence | Où |
|---|---|
| Prix TTC, frais de port avant le panier, aucun frais à la livraison | Fiches, panier, récapitulatif, CGV art. 4 |
| Délai de livraison réel avec dates en jours ouvrés (jours fériés français exclus) ; en précommande, dates d'expédition et de livraison identiques sur toutes les pages, sur la page Stripe et dans l'e-mail de confirmation | Fiches, bandeau, panier, commande, page Stripe, e-mail, page Livraison, CGV art. 7.1 |
| Aucun prix barré, aucun compte à rebours, aucun stock fictif, aucune allégation santé | Tout le site ; économie des kits écrite en texte et vérifiée par le générateur |
| Avis : état vide « Les premiers avis vérifiés arrivent », aucun `aggregateRating` | Fiches, accueil |
| Bloc GPSR (fabricant, personne responsable dans l'UE, identification, avertissements, mode d'emploi) | Chaque fiche produit et kit |
| Case CGV non pré-cochée, bouton final « Payer » sur Stripe avec la mention « commande avec obligation de paiement » | `/commande/`, page Stripe |
| Confirmation sur support durable avec CGV en PDF, lien de rétractation et formulaire type | Webhook `stripe-webhook` |
| Fonctionnalité « renoncer au contrat ici » → bouton « confirmer la rétractation » → accusé horodaté par e-mail (commande vérifiée dans Stripe ; sinon transmis au service client, qui répond sous 48 heures ouvrées) ; formulaire protégé contre les abus | Pied de page de toutes les pages, `/retractation/`, fonction `retractation` |
| Consentement à la prospection : case non pré-cochée obligatoire, texte de `marketing/emails.md` §1.2, date et version enregistrées dans Brevo | Formulaires de liste d'attente, accueil |
| Formulaire type de rétractation | `/retours-retractation/` et annexe des CGV |
| Médiateur de la consommation | Pied de page, mentions légales, CGV art. 14, contact |
| Bandeau cookies : aucun traceur avant consentement, « Tout refuser » de même taille et même style que « Tout accepter », choix conservé 6 mois, « Gérer mes cookies » permanent | Toutes les pages |
| Accessibilité : contrastes AA (palette vérifiée), focus visible, lien d'évitement, tiroir piégeant le focus et fermé par Échap, textes alternatifs, champs étiquetés | Tout le site |

## 7. Variables `{{...}}` à remplacer avant la mise en ligne

Les variables d'identité légale restent visibles sous la forme `{{...}}` tant qu'elles ne sont pas saisies. **Un seul endroit** : `strategie/brand.json` → `identite`. Puis `python3 site/outils/generer.py --publication` : la commande refuse de générer le site publiable tant qu'il reste une variable (la LCEN s'applique dès la liste d'attente). Le tableau ci-dessous est recalculé à chaque génération.

En phase liste d'attente, les variables qui ne servent qu'à la vente (`MEDIATEUR`, `IDU_EMBALLAGES`, `ADRESSE_RETOUR`, `ADRESSE_EXPEDITION`, `FABRICANT_*`) sont remplacées par une mention neutre (« désigné avant l'ouverture des ventes ») ; en précommande et en vente, `--publication` exige qu'elles soient remplies. Les fabricants sont un critère éliminatoire du choix du fournisseur (`brand.json` → `approvisionnement`) : sans raison sociale, adresse et e-mail écrits, aucune fiche n'est publiable, et TikTok Shop refuse les fiches sans informations GPSR.

<!-- PLACEHOLDERS:DEBUT -->
| Variable (`brand.json` → `identite`) | À saisir | Pages concernées |
|---|---|---|
| `{{RAISON_SOCIALE}}` | Dénomination sociale de la société (ou « NOM Prénom EI » en micro-entreprise) | `/`, `/boutique/`, `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/` et 19 autres |
| `{{FORME_JURIDIQUE}}` | SASU, EURL, SARL… (supprimer la mention du capital en micro-entreprise) | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{CAPITAL}}` | Montant du capital social, par exemple « 1 000 € » | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{ADRESSE}}` | Adresse postale du siège | `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/`, `/kits/grand-kit/`, `/kits/kit-anti-poils/` et 10 autres |
| `{{SIREN}}` | Numéro SIREN (9 chiffres) | `/mentions-legales/`, `/cgv/` |
| `{{RCS}}` | « RCS Ville 123 456 789 » (ou RNE pour un entrepreneur individuel) | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{TVA_INTRACOM}}` | Numéro de TVA intracommunautaire ; en franchise sans numéro, supprimer la ligne et ajouter « TVA non applicable, art. 293 B du CGI » | `/mentions-legales/`, `/cgv/` |
| `{{EMAIL}}` | Adresse e-mail du service client | `/`, `/boutique/`, `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/` et 19 autres |
| `{{TELEPHONE}}` | Numéro non surtaxé | `/contact/`, `/mentions-legales/`, `/cgv/`, `/retours-retractation/`, `/livraison/` |
| `{{HORAIRES_SERVICE_CLIENT}}` | Jours et horaires, par exemple « du lundi au vendredi, de 9 h à 18 h » | `/contact/`, `/mentions-legales/`, `/cgv/`, `/retours-retractation/`, `/livraison/` |
| `{{DIRECTEUR_PUBLICATION}}` | Nom du représentant légal | `/mentions-legales/` |
| `{{HEBERGEUR}}` | Raison sociale, adresse postale et téléphone de l'hébergeur (Netlify ou Cloudflare), recopiés depuis ses conditions en vigueur | `/mentions-legales/`, `/confidentialite/` |
<!-- PLACEHOLDERS:FIN -->

Autres points à compléter avant la première vente :

| Point | Où | Pourquoi |
|---|---|---|
| Avertissements GPSR « à valider sur l'échantillon » | `brand.json` > `produits[].gpsr` | Ils doivent reprendre la notice réelle du fabricant |
| Dimensions, matières et poids « à confirmer » | `brand.json` > `caracteristiques` | Caractéristiques essentielles (L111-1) |
| Présence de latex dans la raclette | `brand.json` > raclette | Avertissement allergie à confirmer |
| Micro-entreprise : variante des mentions | `outils/contenus/mentions-legales.md`, `cgv.md` art. 2 | Remplacer la dénomination par « NOM Prénom EI », supprimer forme et capital ; en franchise de TVA, ajouter « TVA non applicable, art. 293 B du CGI » et passer `tva: "franchise"` |
| Couverture Corse par le transporteur | `outils/contenus/livraison.md`, `cgv.md` art. 1.2 | Retirer « Corse comprise » si le contrat Mondial Relay ne la couvre pas |
| Photos réelles | `images/README.md` | Remplacer les illustrations ; indispensable avant de soumettre le flux Google |
| Phase | `strategie/brand.json` → `livraison.phase` | `liste_attente` jusqu'à la porte 1, puis `precommande` avec les dates calculées (`docs/pilotage.xlsx` → Dates précommande) |

## 8. Limites connues

| Limite | Contournement actuel | Évolution |
|---|---|---|
| Pas de sélecteur cartographique de point relais | Champ facultatif « numéro du point relais » + lien vers le moteur de recherche Mondial Relay ; sinon le plus proche de l'adresse, annoncé par e-mail | Widget Mondial Relay ou bascule Shopify avec une application de transport |
| Pas de relance des paniers abandonnés | Aucune relance (PA1-PA3 suspendus dans `marketing/emails.md`) | Native sur Shopify, ou case de consentement du panier + webhook `checkout.session.expired` |
| Journal des consentements stocké dans le navigateur seulement | Aucun traceur n'est actif : rien à prouver pour l'instant | Outil de consentement avec journal serveur avant d'activer un pixel |
| Stock non décrémenté en temps réel | Stock saisi chaque matin dans `brand.json` (plafond par commande contrôlé par le serveur, bascule automatique en précommande sous 5 unités) ; TikTok Shop au stock réel − 2 | Shopify (stock multicanal) ou 3PL |
| Prime « gant offert aux 30 premières précommandes » | Mention affichée en phase précommande avec la limite des 30 gants réservés ; compteur daté mis à jour dans `brand.json` → `livraison.precommande.prime` ; gant ajouté à la main au colisage | Compteur serveur si l'opération est reconduite |
| Variante Cloudflare des fonctions | Logique testée sous Node (`tester_fonctions.js`), non déployée depuis cet environnement ; liaison KV et Turnstile non testées contre les vrais services | Premier déploiement à vérifier avec la carte de test Stripe, une inscription et une rétractation réelles |
| Formulaire de rétractation | Fonctionne avec JavaScript seulement | Ajouter `action` et `method` au formulaire et accepter `application/x-www-form-urlencoded` côté serveur |
