# Site Canapoil : prototype de production

Site e-commerce statique (HTML, CSS et JavaScript natifs, aucun framework, aucune étape de build) pour la marque Canapoil, conforme à la stratégie `strategie/04-strategie.md` et alimenté par `strategie/brand.json`. Paiement sur la page hébergée par Stripe, fonctions serveur gratuites (Netlify ou Cloudflare Pages).

| Élément | Valeur |
|---|---|
| Pages | 24 : accueil, boutique, 4 fiches produit, 4 fiches kit, panier, commande, `merci.html`, FAQ, à propos, contact, rétractation en ligne, 6 pages légales, 404 |
| JavaScript livré | `assets/js/app.js` + `assets/js/config.js`, ≈ 37 Ko au total (plafond fixé : 60 Ko) |
| Dépendances | Aucune côté navigateur ; aucune dépendance npm côté serveur (appels `fetch` directs aux API Stripe et Brevo) |
| Polices | Fraunces et DM Sans auto-hébergées (`assets/fonts/`, licence OFL) : aucun appel à Google Fonts, donc aucune adresse IP transmise à un tiers à l'ouverture d'une page |
| Source des prix | `data/products.json`, généré depuis `brand.json`, relu par le navigateur **et** par le serveur au moment du paiement |
| Vérification | 348 contrôles Playwright réussis (`outils/verifier_site.js`) et 17 tests des fonctions serveur (`outils/tester_fonctions.js`) au 12/10/2026 |

## 1. Arborescence

| Chemin | Rôle |
|---|---|
| `index.html`, `boutique/`, `produits/<slug>/`, `kits/<slug>/`, `faq/`, `a-propos/`, `contact/` | Pages publiques (URL propres : un dossier par page) |
| `panier/`, `commande/`, `merci.html`, `retractation/` | Tunnel et rétractation (non indexés) |
| `mentions-legales/`, `cgv/`, `retours-retractation/`, `livraison/`, `confidentialite/`, `cookies/` | Pages légales adaptées de `recherche/pages-legales/` |
| `assets/css/style.css` | Feuille de style unique, mobile d'abord, jetons de couleur de `brand.json` |
| `assets/js/config.js` | **Seul fichier à modifier pour passer en production** (mode, phase, dates de précommande, traceurs) |
| `assets/js/app.js` | Panier (localStorage), tiroir, sélecteur d'offres, barre d'achat collante, dates de livraison, consentement, commande, rétractation, inscriptions |
| `data/products.json` | Catalogue public (prix TTC, contenus, GPSR). Ne contient ni coûts ni fournisseurs |
| `netlify/functions/*.js` | Fonctions Netlify : `create-checkout`, `retractation`, `inscription`, `stripe-webhook` |
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
NODE_PATH="$(npm root -g)" node site/outils/rendre_images.js  # PNG produits, images de partage, CGV en PDF
cd site && python3 -m http.server 8765 --bind 127.0.0.1       # puis ouvrir http://127.0.0.1:8765
```

Dans un second terminal :

```bash
NODE_PATH="$(npm root -g)" node site/outils/verifier_site.js http://127.0.0.1:8765   # parcours complet, captures dans docs/captures
node site/outils/tester_fonctions.js                                                # fonctions serveur, sans réseau
```

Pour changer un prix, un texte produit ou un délai : modifier `strategie/brand.json`, relancer les deux premières commandes, redéployer. Ne modifiez jamais un prix directement dans une page HTML.

## 3. Modes et phases (`assets/js/config.js`)

| Réglage | Valeur | Effet |
|---|---|---|
| `mode` | `"demo"` (par défaut) | Aucun appel serveur. Le bouton de paiement simule la commande et mène à `merci.html` avec l'avertissement « Simulation ». La rétractation et les inscriptions sont simulées à l'écran |
| | `"production"` | Appelle `/api/create-checkout` (session Stripe), `/api/retractation` et `/api/inscription` |
| `phase` | `"liste_attente"` | **À utiliser avant la porte 1 (15/11/2026)** : aucune vente, les boutons d'achat sont remplacés par l'inscription au lancement (double opt-in Brevo) |
| | `"precommande"` | Boutons « Précommander », date d'expédition et date limite de livraison affichées (`precommande.*`, 30 jours au plus) |
| | `"vente"` | Vente normale |
| `tva` | `"assujetti"` ou `"franchise"` | Mention sous les totaux (« dont TVA 20 % » ou « TVA non applicable, art. 293 B du CGI »). En franchise, adaptez aussi l'article 4.1 des CGV (`outils/contenus/cgv.md`) |
| `traceurs` | listes vides | Scripts chargés **uniquement après consentement**. Ajouter aussi leurs domaines dans `_headers` (CSP) et dans la page cookies |
| `livraison.delai_min/max` | `null` | Après 30 livraisons : 90e centile constaté + 2 jours ouvrés |

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
| `STRIPE_SECRET_KEY` | Paiement | Clé secrète `sk_test_…` puis `sk_live_…`, ou mieux une **clé restreinte** `rk_live_…` limitée à « Checkout Sessions : écriture » |
| `STRIPE_WEBHOOK_SECRET` | E-mail de confirmation | `whsec_…` affiché à la création du webhook |
| `STRIPE_CASE_CGV` | Facultatif | `oui` ajoute une seconde case CGV sur la page Stripe (exige l'URL des CGV dans Paramètres > Informations publiques) |
| `BREVO_API_KEY` | Rétractation, inscriptions, confirmation | Clé API Brevo (offre gratuite) |
| `EMAIL_EXPEDITEUR` | Idem | Adresse expéditrice validée dans Brevo (domaine authentifié SPF/DKIM) |
| `EMAIL_SERVICE_CLIENT` | Idem | Adresse qui reçoit la copie de chaque accusé et confirmation |
| `NOM_EXPEDITEUR` | Facultatif | « Canapoil » par défaut |
| `BREVO_LISTE_ID`, `BREVO_TEMPLATE_DOI` | Inscriptions | Identifiant de la liste « Liste d'attente » et du modèle de confirmation double opt-in |
| `ORIGINES_AUTORISEES` | Facultatif | Autres origines autorisées, séparées par des virgules (par exemple la boutique Shopify qui réutilise la fonction de rétractation) |

### Configurer Stripe (≈ 30 minutes, 0 € d'abonnement)

1. Créer le compte sur stripe.com, renseigner la société (SIREN, IBAN, pièce d'identité du dirigeant).
2. Paramètres > Moyens de paiement : cartes activées ; Apple Pay et Google Pay au choix (aucun surcoût pour le client).
3. Paramètres > Informations publiques : nom « Canapoil », descripteur bancaire `CANAPOIL`, e-mail et téléphone du service client, URL des CGV (`https://canapoil.fr/cgv/`) et de la politique de retours.
4. Paramètres > E-mails clients : activer les reçus pour les paiements réussis.
5. Développeurs > Clés API : créer une clé restreinte « Checkout Sessions : écriture » et la coller dans `STRIPE_SECRET_KEY`.
6. Développeurs > Webhooks : endpoint `https://canapoil.fr/api/stripe-webhook`, événement `checkout.session.completed` ; copier le secret dans `STRIPE_WEBHOOK_SECRET`.
7. En mode test, passer `mode: "production"` dans `config.js`, payer avec la carte `4242 4242 4242 4242`, vérifier la commande dans Stripe (métadonnées : panier, point relais, date d'acceptation des CGV) et la réception de l'e-mail de confirmation. Puis remplacer la clé de test par la clé live.

Frais : 1,5 % + 0,25 € par carte standard de l'EEE, 2,8 % + 0,25 € par carte premium ([Stripe](https://stripe.com/fr/pricing)).

Les commandes se traitent depuis le tableau de bord Stripe (Paiements) : adresse, téléphone, articles, point relais demandé (métadonnées). Le prix envoyé à Stripe est recalculé par la fonction à partir de `data/products.json` ; un panier modifié dans le navigateur ne peut pas changer le montant.

### Configurer Brevo (offre gratuite)

1. Créer le compte, authentifier le domaine `canapoil.fr` (Expéditeurs, domaines et IP dédiées > Domaines).
2. Contacts > Listes : créer « Liste d'attente » et noter son identifiant (`BREVO_LISTE_ID`).
3. Modèles : créer le modèle de confirmation double opt-in et noter son identifiant (`BREVO_TEMPLATE_DOI`).
4. Paramètres SMTP et API > Clés API : créer la clé (`BREVO_API_KEY`).

## 6. Conformité : ce que fait le site

| Exigence | Où |
|---|---|
| Prix TTC, frais de port avant le panier, aucun frais à la livraison | Fiches, panier, récapitulatif, CGV art. 4 |
| Délai de livraison réel avec dates en jours ouvrés (jours fériés français exclus) | Fiches, panier, commande |
| Aucun prix barré, aucun compte à rebours, aucun stock fictif, aucune allégation santé | Tout le site ; économie des kits écrite en texte et vérifiée par le générateur |
| Avis : état vide « Les premiers avis vérifiés arrivent », aucun `aggregateRating` | Fiches, accueil |
| Bloc GPSR (fabricant, personne responsable dans l'UE, identification, avertissements, mode d'emploi) | Chaque fiche produit et kit |
| Case CGV non pré-cochée, bouton final « Payer » sur Stripe avec la mention « commande avec obligation de paiement » | `/commande/`, page Stripe |
| Confirmation sur support durable avec CGV en PDF, lien de rétractation et formulaire type | Webhook `stripe-webhook` |
| Fonctionnalité « renoncer au contrat ici » → bouton « confirmer la rétractation » → accusé horodaté par e-mail | Pied de page de toutes les pages, `/retractation/`, fonction `retractation` |
| Formulaire type de rétractation | `/retours-retractation/` et annexe des CGV |
| Médiateur de la consommation | Pied de page, mentions légales, CGV art. 14, contact |
| Bandeau cookies : aucun traceur avant consentement, « Tout refuser » de même taille et même style que « Tout accepter », choix conservé 6 mois, « Gérer mes cookies » permanent | Toutes les pages |
| Accessibilité : contrastes AA (palette vérifiée), focus visible, lien d'évitement, tiroir piégeant le focus et fermé par Échap, textes alternatifs, champs étiquetés | Tout le site |

## 7. Variables `{{...}}` à remplacer avant la mise en ligne

Les variables d'identité légale restent volontairement visibles sous la forme `{{...}}`. Remplacez-les dans `outils/contenus/*.md` (pages légales), dans `strategie/brand.json` (fabricants GPSR, contact) et dans `outils/generer.py` (pied de page, contact, à propos), puis relancez `generer.py`. Le tableau ci-dessous est recalculé à chaque génération.

<!-- PLACEHOLDERS:DEBUT -->
| Variable | À remplacer par | Pages concernées |
|---|---|---|
| `{{RAISON_SOCIALE}}` | Dénomination sociale de la société (ou « NOM Prénom EI » en micro-entreprise) | `/`, `/boutique/`, `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/` et 18 autres |
| `{{FORME_JURIDIQUE}}` | SASU, EURL, SARL… (supprimer la mention du capital en micro-entreprise) | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{CAPITAL}}` | Montant du capital social, par exemple « 1 000 € » | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{ADRESSE}}` | Adresse postale du siège | `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/`, `/kits/grand-kit/`, `/kits/kit-anti-poils/` et 9 autres |
| `{{SIREN}}` | Numéro SIREN (9 chiffres) | `/mentions-legales/`, `/cgv/` |
| `{{RCS}}` | « RCS Ville 123 456 789 » (ou RNE pour un entrepreneur individuel) | `/mentions-legales/`, `/cgv/`, `/confidentialite/` |
| `{{TVA_INTRACOM}}` | Numéro de TVA intracommunautaire ; en franchise sans numéro, supprimer la ligne et ajouter « TVA non applicable, art. 293 B du CGI » | `/mentions-legales/`, `/cgv/` |
| `{{EMAIL}}` | Adresse e-mail du service client | `/`, `/boutique/`, `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/` et 18 autres |
| `{{TELEPHONE}}` | Numéro non surtaxé | `/contact/`, `/mentions-legales/`, `/cgv/`, `/retours-retractation/`, `/livraison/` |
| `{{HORAIRES_SERVICE_CLIENT}}` | Jours et horaires, par exemple « du lundi au vendredi, de 9 h à 18 h » | `/contact/`, `/mentions-legales/`, `/cgv/`, `/retours-retractation/`, `/livraison/` |
| `{{DIRECTEUR_PUBLICATION}}` | Nom du représentant légal | `/mentions-legales/` |
| `{{HEBERGEUR}}` | Raison sociale, adresse postale et téléphone de l'hébergeur (Netlify ou Cloudflare), recopiés depuis ses conditions en vigueur | `/mentions-legales/`, `/confidentialite/` |
| `{{MEDIATEUR}}` | Nom, adresse et site du médiateur après adhésion (par exemple CM2C) | `/`, `/boutique/`, `/produits/rouleau-anti-poils-reutilisable/`, `/produits/gant-toilettage-silicone/`, `/produits/raclette-anti-poils-tapis-voiture/`, `/produits/tapis-fenetre-thermique-chat/` et 18 autres |
| `{{IDU_EMBALLAGES}}` | Identifiant unique REP emballages (FR…) attribué après adhésion à Léko ou Citeo | `/mentions-legales/`, `/cgv/` |
| `{{ADRESSE_RETOUR}}` | Adresse en France où les clients renvoient les produits | `/retractation/`, `/cgv/`, `/retours-retractation/` |
| `{{FABRICANT_ROULEAU}}` | Nom, adresse postale et e-mail du fabricant du rouleau (dossier fournisseur) | `/produits/rouleau-anti-poils-reutilisable/`, `/kits/grand-kit/`, `/kits/kit-anti-poils/`, `/kits/duo-maison-voiture/`, `/kits/kit-chat-hiver/` |
| `{{FABRICANT_GANT}}` | Idem pour le gant | `/produits/gant-toilettage-silicone/`, `/kits/grand-kit/`, `/kits/kit-anti-poils/` |
| `{{FABRICANT_RACLETTE}}` | Idem pour la raclette | `/produits/raclette-anti-poils-tapis-voiture/`, `/kits/grand-kit/` |
| `{{FABRICANT_TAPIS}}` | Idem pour le tapis de fenêtre | `/produits/tapis-fenetre-thermique-chat/`, `/kits/kit-chat-hiver/` |
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
| Phase | `assets/js/config.js` | `liste_attente` jusqu'à la porte 1, puis `precommande` avec des dates réelles |

## 8. Limites connues

| Limite | Contournement actuel | Évolution |
|---|---|---|
| Pas de sélecteur cartographique de point relais | Champ facultatif « numéro du point relais » + lien vers le moteur de recherche Mondial Relay ; sinon le plus proche de l'adresse, annoncé par e-mail | Widget Mondial Relay ou bascule Shopify avec une application de transport |
| Pas de relance des paniers abandonnés | — | Native sur Shopify (conditions de bascule de la stratégie) |
| Journal des consentements stocké dans le navigateur seulement | Aucun traceur n'est actif : rien à prouver pour l'instant | Outil de consentement avec journal serveur avant d'activer un pixel |
| Pas de gestion de stock en ligne | Stock suivi dans le tableur ; passer un produit en rupture en le retirant de `brand.json` ou en mode `liste_attente` | Shopify ou 3PL |
| Prime « gant offert aux 30 premières précommandes » | Mention affichée en phase précommande ; ajout du gant fait à la main au colisage | Compteur serveur si l'opération est reconduite |
| Variante Cloudflare des fonctions | Testée localement après empaquetage esbuild (même moteur que Wrangler), non déployée depuis cet environnement | Premier déploiement à vérifier avec la carte de test Stripe |
