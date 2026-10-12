# Démarrage : les 14 premiers jours, une page par jour

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Pour qui | Le client, débutant, qui exécute seul le plan de [04 §6.2](../strategie/04-strategie.md) |
| Période | **J1 = lundi 12/10/2026 → J14 = dimanche 25/10/2026** (semaines S1 et S2) |
| Budget de la période | **45 €** (domaine + échantillons). Aucune autre dépense avant la porte 1 du 15/11 |
| Temps | ≈ 25 heures par semaine (plan allégé de [07 §4.5](../marketing/07-plan-organique-90j.md)) |
| Outils | [`strategie/brand.json`](../strategie/brand.json) (seul fichier de réglages), [`docs/pilotage.xlsx`](pilotage.xlsx) (suivi), [`docs/gabarits/`](gabarits/) (étiquettes, notices, carte de colis) |
| Règle d'or | Rien n'est publié, vendu ni commandé au fournisseur sans la ligne « Résultat attendu » du jour précédent cochée |

---

## J1 — lundi 12/10 : décider du financement

| Champ | Contenu |
|---|---|
| Action | Lire [05 §5](../finance/05-analyse-financiere.md) (trésorerie, 2 pages). Choisir **par écrit** l'option a (apport de 2 400 € en compte courant), b (TikTok Shop plafonné au stock déjà payé, aucun affilié avant le premier règlement TikTok Shop, 910 € à la porte 1) ou c (arrêt à 45 € si la porte 1 n'est pas franchie). Reporter la lettre et la date dans `brand.json` → `hypotheses_cles.tresorerie.option_retenue` et dans `pilotage.xlsx` → Décisions!B4. Prendre rendez-vous avec l'expert-comptable (J4) |
| Durée | 1 h 30 |
| Coût | 0 € |
| Lien | [`brand.json` → `hypotheses_cles.tresorerie`](../strategie/brand.json) |
| Résultat attendu | Option signée ; rendez-vous comptable fixé |

## J2 — mardi 13/10 : vérifier la marque et le produit (propriété intellectuelle)

| Champ | Contenu |
|---|---|
| Action | 1) [TMview](https://www.tmdn.org/tmview/) et [data.inpi.fr](https://data.inpi.fr/) : rechercher « Canapoil » et « Canapoils » (classes 20, 21, 28). 2) [DesignView](https://www.tmdn.org/tmdsview-web/) : rechercher les dessins et modèles de rouleau anti-poils (classe de Locarno 04-02, brosses) et de tapis de fouille, avec des mots-clés anglais (« lint roller », « pet hair remover », « snuffle mat »). 3) Capture d'écran datée de chaque résultat, rangée dans un dossier « PI » |
| Durée | 2 h |
| Coût | 0 € |
| Lien | 04 §3.1 et §2.5 ; `brand.json` → `propriete_intellectuelle` |
| Résultat attendu | Aucune marque identique, aucun modèle enregistré proche ; sinon, arrêt du produit concerné ou du nom (04 §2.5) |

## J3 — mercredi 14/10 : réserver les noms

| Champ | Contenu |
|---|---|
| Action | Acheter canapoil.fr (≈ 10 €, un registrar qui permet de gérer les DNS chez Cloudflare). Créer l'adresse e-mail du service client sur le domaine. Ouvrir `@canapoil` sur TikTok (compte Business), Instagram (professionnel), Pinterest (professionnel) et YouTube ; double authentification partout, codes de secours imprimés |
| Durée | 2 h |
| Coût | ≈ 10 € |
| Lien | 07 §1 |
| Résultat attendu | Domaine et 4 comptes à votre nom |

## J4 — jeudi 15/10 : identité légale, TVA, objet social

| Champ | Contenu |
|---|---|
| Action | Avec l'expert-comptable : 1) Kbis : l'objet social couvre-t-il la vente en ligne de marchandises ? Sinon, modification (contrôles KYC de Stripe et de TikTok Shop). 2) Régime de TVA (franchise recommandée si la société n'a pas opté, 05 §8.1). 3) Traitement de l'achat B2B du stock (risque de double TVA AliExpress, régime douanier d'un colis de plus de 150 €). Puis remplir **toutes** les valeurs de `brand.json` → `identite` (raison sociale, forme, capital, adresse, SIREN, RCS, TVA, e-mail, téléphone, horaires, directeur de publication, hébergeur, adresses de retour et d'expédition) et `regime_tva` |
| Durée | 2 h (dont 1 h de rendez-vous) |
| Coût | Inclus dans l'abonnement comptable (≈ 90 € par mois dans le modèle) |
| Lien | `brand.json` → `identite`, `regime_tva` |
| Résultat attendu | Il ne reste que les variables liées à la porte 1 (médiateur, IDU Léko) et aux fabricants |

## J5 — vendredi 16/10 : mettre le site en ligne (liste d'attente)

| Champ | Contenu |
|---|---|
| Action | 1) `python3 site/outils/generer.py` puis `NODE_PATH="$(npm root -g)" node site/outils/rendre_images.js`. 2) Déployer sur Cloudflare Pages (Git conseillé : [site/README.md §4](../site/README.md)). 3) DNS de canapoil.fr chez Cloudflare. 4) Variables de l'hébergeur : `SITE_URL`, `BREVO_*`, `EMAIL_*`, `TURNSTILE_SECRET_KEY` ; **pas de `STRIPE_SECRET_KEY` avant la porte 1**. 5) Lier un espace KV nommé `CANAPOIL_KV`. 6) Activer Web Analytics. 7) Turnstile : créer le widget, coller la clé de site dans `config.js` → `turnstile.cle_site`, passer `mode: "production"` |
| Durée | 3 h |
| Coût | 0 € |
| Lien | [site/README.md §4-§5](../site/README.md) |
| Résultat attendu | canapoil.fr affiche la liste d'attente, sans bandeau « Démonstration » ; aucune page de vente |

**Si cette journée bloque** (Python, Node, Git, DNS) : option Shopify pour la phase de précommande, 1 $ par mois pendant 3 mois (≈ 3 €), avec le kit d'import [`shopify-kit/`](../shopify-kit/) (04 §5.2). La liste d'attente peut alors passer par un formulaire Brevo hébergé.

## J6 — samedi 17/10 : Brevo et premier test réel

| Champ | Contenu |
|---|---|
| Action | Brevo : authentifier le domaine (SPF, DKIM, DMARC), créer la liste « Liste d'attente », le modèle de double opt-in (texte BV0 de [emails.md](../marketing/emails.md)), et les attributs `PRODUIT`, `SOURCE`, `CONSENTEMENT_DATE`, `CONSENTEMENT_TEXTE`, `UTM_SOURCE`, `UTM_CAMPAIGN`, `UTM_CONTENT`. S'inscrire soi-même depuis la fiche du rouleau et depuis la page du tapis de fouille ; vérifier l'e-mail de confirmation et les attributs |
| Durée | 2 h |
| Coût | 0 € |
| Lien | emails.md §1 |
| Résultat attendu | 2 inscriptions de test visibles dans Brevo avec le produit et la date du consentement |

## J7 — dimanche 18/10 : choisir les fournisseurs et commander les échantillons

| Champ | Contenu |
|---|---|
| Action | Écrire aux vendeurs repérés (liens dans `brand.json`) : nom, adresse et e-mail du **fabricant**, notice et avertissements, photo de l'étiquette d'origine, facture B2B hors taxes possible ? Éliminer ceux qui ne répondent pas par écrit (`brand.json` → `approvisionnement`). Commander les échantillons : 2 rouleaux (2 vendeurs), 1 gant, 1 raclette, 1 tapis thermique, 1 tapis de fouille. **Noter la date de commande** : le transit mesuré servira à calculer les dates de précommande |
| Durée | 2 h |
| Coût | ≈ 35 € |
| Lien | 04 §5.4 |
| Résultat attendu | Échantillons commandés chez des vendeurs qui identifient le fabricant ; sinon, CJ Dropshipping ou un agent |

## J8 — lundi 19/10 : assurance et TikTok Shop

| Champ | Contenu |
|---|---|
| Action | 1) Demander 3 devis d'assurance RC professionnelle + RC produits (activité : import et vente en ligne d'accessoires pour animaux ; volume prévisionnel : 5 000 € de CA la première année). 2) Déposer le dossier du Seller Center TikTok Shop (SIRET, TVA, pièce d'identité, IBAN) ; ne rien mettre en vente. 3) Dès l'accès au Seller Center : relever le tarif de l'étiquette « Expédition par TikTok » pour 300 g, 500 g et 1 kg, le saisir dans `brand.json` → `livraison.tiktok_shop.port_ht` et `port_ht_modele`, puis dans `finance/modele_financier.py` (`PORT_TTS_500`, `PORT_TTS_1KG`, contrôlés contre `brand.json`), puis relancer `python3 finance/modele_financier.py` (revue red team M9) |
| Durée | 2 h |
| Coût | 0 € (souscription à la porte 1) |
| Lien | 04 §8 décision 10 |
| Résultat attendu | 3 devis demandés ; dossier TikTok Shop déposé |

## J9 — mardi 20/10 : premier tournage

| Champ | Contenu |
|---|---|
| Action | Session de 2 h 30 : vidéos « problème » sans produit (pull noir, canapé, voiture), 3 accroches par thème ([scripts-tiktok.md](../marketing/scripts-tiktok.md)) ; nommage des fichiers `AAAAMMJJ_ID_accroche_prise.mp4` |
| Durée | 2 h 30 |
| Coût | 0 € |
| Lien | 07 §4.3 |
| Résultat attendu | 7 vidéos tournées |

## J10 — mercredi 21/10 : montage, publication, relevé des prix

| Champ | Contenu |
|---|---|
| Action | 1) Monter et publier 2 vidéos (lien de la bio vers la fiche du rouleau avec `?utm_source=tiktok&utm_medium=bio`). 2) Dans l'application TikTok, onglet Boutique : relever les 20 premiers rouleaux anti-poils réutilisables (prix, ventes affichées, délai) dans `pilotage.xlsx` → Prix TikTok Shop, avec captures datées |
| Durée | 2 h 30 |
| Coût | 0 € |
| Lien | 04 §3.2 |
| Résultat attendu | Médiane calculée : rouleau à 24,90 € (médiane ≥ 16 €) ou à 19,90 € (sinon) ; si le prix change, le modifier dans `brand.json` et relancer le modèle financier |

## J11 — jeudi 22/10 : deuxième tournage et Pinterest

| Champ | Contenu |
|---|---|
| Action | Session de 2 h 30 ; compte Pinterest : revendication du site, 6 tableaux (07 §1.2) ; 2 vidéos publiées |
| Durée | 3 h |
| Coût | 0 € |
| Lien | 07 §1.2 |
| Résultat attendu | 7 vidéos de plus en banque ; site revendiqué |

## J12 — vendredi 23/10 : Stripe sans clé, pilotage

| Champ | Contenu |
|---|---|
| Action | Créer le compte Stripe et le vérifier (SIREN, IBAN, pièce d'identité), descripteur `CANAPOIL`, URL des CGV ; **ne pas saisir la clé chez l'hébergeur** (le serveur refuse de toute façon les paiements en liste d'attente). Remplir la première semaine de `pilotage.xlsx` → KPI hebdo |
| Durée | 1 h 30 |
| Coût | 0 € |
| Lien | site/README.md §5 |
| Résultat attendu | Compte Stripe vérifié, inactif sur le site |

## J13 — samedi 24/10 : gabarits physiques

| Champ | Contenu |
|---|---|
| Action | `python3 docs/gabarits/generer_gabarits.py` ; imprimer une planche d'étiquettes « Importé par » et une notice en français sur papier ordinaire pour vérifier la lisibilité ; dresser la liste des fournitures de la porte 1 (pochettes, planches d'étiquettes 63,5 × 33,9 mm, papier) |
| Durée | 1 h |
| Coût | 0 € (fournitures achetées à la porte 1, ≈ 12 €) |
| Lien | [docs/gabarits/](gabarits/) |
| Résultat attendu | Gabarits vérifiés ; il ne leur manque que le nom des fabricants |

## J14 — dimanche 25/10 : revue de la semaine 2

| Champ | Contenu |
|---|---|
| Action | Revue des KPI (vidéos, vues médianes, inscrits par produit) ; suivi des colis d'échantillons ; réponses des assureurs ; si une vidéo dépasse 2 000 vues, décliner l'accroche (07 §8.3) |
| Durée | 1 h |
| Coût | 0 € |
| Lien | 07 §6 (S2) |
| Résultat attendu | Médiane ≥ 300 vues ; ≥ 1 vidéo > 2 000 vues ; 15 inscrits. Sinon, revoir les 2 premières secondes des vidéos |

---

## Ensuite : la porte 1 (15/11) en 6 lignes

| Ordre | Action | Où |
|---|---|---|
| 1 | Décision porte 1 (vues ou inscrits, taux de clics produit ≥ 1,5 %, 20 commentaires hors entourage) | `pilotage.xlsx` → Décisions |
| 2 | Médiateur CM2C, Léko (IDU), INPI classe 21, RC souscrite ; valeurs saisies dans `brand.json` → `identite` | 04 §5.3 |
| 3 | Commande et paiement du micro-stock (40 rouleaux, 45 gants, 12 raclettes, 8 tapis), un colis, facture HT | 04 §5.4 |
| 4 | Dates de précommande calculées | `pilotage.xlsx` → Dates précommande |
| 5 | `brand.json` : `livraison.phase` = `precommande`, dates saisies ; `python3 site/outils/generer.py --publication` (refuse s'il manque quelque chose) ; redéploiement ; clé Stripe saisie | site/README.md §3 |
| 6 | Calendrier jour par jour | [lancement-30-jours.md](../marketing/lancement-30-jours.md) |

---

## Annexe : première expédition Mondial Relay (avant la première commande payée)

Procédure pas à pas qui complète 04 §5.5 (traitement des commandes). Mondial Relay sert au site uniquement : pour TikTok Shop, utiliser l'expédition par TikTok ou un transporteur agréé (`brand.json` → `livraison.tiktok_shop`).

| Ordre | Action | Durée | Coût | Où noter |
|---|---|---|---|---|
| 1 | Ouvrir l'espace professionnel sur mondialrelay.fr (ou un agrégateur d'étiquettes) au nom de la société ; relever la grille réelle pour ≤ 500 g, ≤ 1 kg et ≤ 2 kg, et vérifier la desserte de la Corse (revue red team m8 : le tarif de 4,15 € TTC vient d'une source secondaire) | 45 min | 0 € | `brand.json` → `hypotheses_cles.port_ht`, puis `python3 finance/modele_financier.py` |
| 2 | Envoi à blanc vers sa propre adresse : un rouleau emballé (pochette, notice, carte de colis), pesé sur une balance de cuisine | 30 min + dépôt | Prix d'une étiquette ≤ 500 g | `pilotage.xlsx` → Commandes (une ligne, canal « test » : expédition réelle, livraison réelle) |
| 3 | Pour chaque commande du site : lire l'e-mail Stripe (point relais demandé dans les métadonnées), peser, créer l'étiquette, glisser notice et carte, coller l'étiquette « Importé par » si absente | 10 min par colis | Étiquette | `pilotage.xlsx` → Commandes (n° de commande = 10 derniers caractères de la session Stripe) |
| 4 | Déposer au point relais avant la fin du jour ouvré suivant la commande ; saisir le numéro de suivi ; envoyer l'e-mail de suivi (modèle Brevo) | 15 min par tournée | 0 € | `pilotage.xlsx` → Commandes (colonnes « Expédition réelle » puis « Livraison réelle » et « Statut », numéro de suivi noté dans « Statut ») ; `brand.json` → `produits[].stock_disponible` diminué, site régénéré |
| 5 | Chaque lundi : 90e centile des délais réels (commande → livraison, calculé par l'onglet Délais). S'il dépasse 6 jours ouvrés, corriger le délai annoncé dans `brand.json` → `livraison.delai_annonce` avant toute nouvelle vente ; après 30 livraisons, appliquer `livraison.regle_recalcul` | 10 min | 0 € | `pilotage.xlsx` → Délais et KPI hebdo |
| 6 | Colis en retard ou perdu : réclamation dans l'espace professionnel, renvoi ou remboursement sans attendre de mise en demeure (04 §5.6) | Selon le cas | Port + produit | `pilotage.xlsx` → Commandes (« Statut ») ; défaut de sécurité : onglet Réclamations GPSR |
