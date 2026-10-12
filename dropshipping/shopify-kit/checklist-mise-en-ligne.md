# Checklist de mise en ligne sur Shopify (bascule depuis le site statique)

Quand : dès que la **première** condition de bascule est remplie (`brand.json` > `stack.conditions_bascule_shopify`) : 5 commandes par jour sur le site pendant 14 jours, démarrage de la publicité payante, connexion d'un 3PL, ou plus de 6 références à synchroniser avec TikTok Shop. Durée visée : une journée de travail, plus les délais de validation des comptes.

Les coûts suivis de « (stratégie) » viennent de `strategie/04-strategie.md`, qui cite ses sources ; les autres sont sourcés dans `apps.md` ou marqués « estimation ».

## Récapitulatif des coûts

| Poste | Coût | Fréquence |
|---|---|---|
| Shopify Basic | Essai de 3 jours, puis 1 $ par mois pendant 3 mois, puis **36 € par mois** (27 € par mois en paiement annuel) (stratégie, [Shopify](https://www.shopify.com/fr/tarifs), [Speed Ecom](https://speed-ecom.eu/blog/combien-coute-reellement-shopify/)) | Mensuel |
| Shopify Payments | 1,5 % + 0,25 € par carte de l'EEE sur Basic (stratégie, [Kanal](https://getkanal.com/fr/blog/shopify-payments-frais), confiance moyenne) ; une passerelle tierce ajoute 2 % de frais Shopify | Par commande |
| Applications | 0 € au palier 1 (`apps.md`) | — |
| Domaine canapoil.fr | Déjà acheté au palier 0 (≈ 10 € par an, estimation) | Annuel |
| Médiateur CM2C, adhésion Léko | Déjà payés à la porte 1 : 48 € pour 3 ans, 95 € HT minimum par an (stratégie) | — |
| **Total de la bascule** | **≈ 1 $ par mois pendant 3 mois, puis 36 € par mois + commissions** | — |

## Étape 0 — Préalables (avant d'ouvrir la boutique)

| # | Action | Coût | Fait |
|---|---|---|---|
| 0.1 | Vérifier qu'une condition de bascule est remplie et la noter dans le tableau de bord hebdomadaire | 0 € | ☐ |
| 0.2 | Médiateur adhéré, IDU Léko reçu, coordonnées GPSR des fabricants reçues, avertissements validés sur échantillon | Déjà engagé | ☐ |
| 0.3 | Remplacer toutes les variables `{{...}}` dans `site/outils/contenus/*.md` et `strategie/brand.json`, puis `python3 site/outils/generer.py` : le CSV et les pages de ce kit sont régénérés | 0 € | ☐ |
| 0.4 | Vraies photos déposées (`site/images/README.md`) et `principale.png` mises à jour : le CSV les référence par URL publique `https://canapoil.fr/images/...` | 0 € | ☐ |
| 0.5 | Le site statique reste en ligne pendant l'import (Shopify télécharge les images depuis ces URL) | 0 € | ☐ |

## Étape 1 — Compte et réglages de base

| # | Action | Où | Coût | Fait |
|---|---|---|---|---|
| 1.1 | Créer la boutique, pays France, devise EUR, langue français | shopify.com | Essai 3 jours | ☐ |
| 1.2 | Choisir l'offre Basic (pas Grow avant ≈ 34 500 € de CA mensuel, stratégie §5.2) | Paramètres > Forfait | 1 $ par mois × 3, puis 36 € | ☐ |
| 1.3 | Coordonnées de la société (raison sociale, adresse, SIREN, TVA) | Paramètres > Détails de la boutique | 0 € | ☐ |
| 1.4 | Double authentification du compte propriétaire | Compte | 0 € | ☐ |
| 1.5 | Taxes : prix **TTC** (« Inclure les taxes dans les prix »), TVA France 20 %. En franchise de TVA : ne pas facturer de TVA et ajouter la mention 293 B dans les CGV et les factures | Paramètres > Taxes et droits | 0 € | ☐ |

## Étape 2 — Paiements, expédition, commande

| # | Action | Où | Coût | Fait |
|---|---|---|---|---|
| 2.1 | Activer Shopify Payments (cartes, Apple Pay, Google Pay) et PayPal ; authentification 3-D Secure ; aucun frais selon le moyen de paiement | Paramètres > Paiements | Commissions seules | ☐ |
| 2.2 | Descripteur bancaire `CANAPOIL` | Paramètres > Paiements | 0 € | ☐ |
| 2.3 | Zone d'expédition « France » : tarif « Point relais Mondial Relay » à **3,90 €** pour une commande de moins de 35 € ; tarif « Point relais — livraison offerte » à **0 €** dès 35 € (les kits à livraison offerte coûtent tous 39,90 € ou plus, la règle les couvre) ; délai affiché 3 à 6 jours ouvrés | Paramètres > Expédition et livraison | 0 € | ☐ |
| 2.4 | Application de transport avec choix du point relais (`apps.md`) | App Store | Non vérifié | ☐ |
| 2.5 | Commande : compte client facultatif ; aucune case marketing pré-cochée ; numéro de téléphone demandé (avis de passage du transporteur) | Paramètres > Paiement | 0 € | ☐ |
| 2.6 | Libellé du bouton final en français (« Payer maintenant ») vérifié sur un téléphone | Aperçu de la commande | 0 € | ☐ |

## Étape 3 — Produits

| # | Action | Où | Coût | Fait |
|---|---|---|---|---|
| 3.1 | (Facultatif) Créer les 4 définitions de métachamps GPSR (`theme.md` §6) | Paramètres > Données personnalisées | 0 € | ☐ |
| 3.2 | Importer `products.csv` (en-têtes identiques au [modèle officiel Shopify](https://help.shopify.com/csv/product_template.csv) téléchargé le 12/10/2026 ; 8 produits dont 4 kits ; prix TTC ; aucun prix barré ; coûts de revient renseignés pour le suivi de marge ; stock initial du micro-stock) | Produits > Importer | 0 € | ☐ |
| 3.3 | Contrôler chaque fiche : prix, poids, images, bloc GPSR, catégorie, aucune mention « à confirmer » restante | Produits | 0 € | ☐ |
| 3.4 | Si Shopify Bundles est utilisé : recréer les 4 kits dans l'application, vérifier la synchronisation du stock, puis supprimer les kits importés en doublon | Applications > Bundles | 0 € | ☐ |
| 3.5 | Collections : « Kits » (Grand kit en premier) et « À l'unité » | Produits > Collections | 0 € | ☐ |

## Étape 4 — Thème

| # | Action | Où | Coût | Fait |
|---|---|---|---|---|
| 4.1 | Vérifier que le thème installé est Horizon (sinon l'ajouter depuis le Theme Store, gratuit) | Boutique en ligne > Thèmes | 0 € | ☐ |
| 4.2 | Couleurs, polices, panier en tiroir, boutons de paiement accéléré désactivés dans le panier (`theme.md` §2 à §4) | Personnaliser | 0 € | ☐ |
| 4.3 | Modèle produit et page d'accueil (`theme.md` §5 et §7) | Personnaliser | 0 € | ☐ |
| 4.4 | Ajouter l'extrait `theme/snippets/canapoil-case-cgv.liquid` au panier (page et tiroir) et tester : impossible de passer au paiement sans cocher | Modifier le code | 0 € | ☐ |
| 4.5 | Ajouter la section `theme/sections/canapoil-retractation.liquid`, créer le modèle `page.retractation` | Modifier le code | 0 € | ☐ |

## Étape 5 — Politiques et pages

| # | Action | Fichier du kit | Où | Fait |
|---|---|---|---|---|
| 5.1 | Conditions générales de vente | `pages/politique-conditions-de-vente.html` | Paramètres > Politiques > Conditions d'utilisation | ☐ |
| 5.2 | Retours et rétractation (avec formulaire type) | `pages/politique-retours-retractation.html` | Paramètres > Politiques > Politique de remboursement | ☐ |
| 5.3 | Livraison | `pages/politique-livraison.html` | Paramètres > Politiques > Politique d'expédition | ☐ |
| 5.4 | Confidentialité | `pages/politique-confidentialite.html` | Paramètres > Politiques > Politique de confidentialité | ☐ |
| 5.5 | Mentions légales | `pages/politique-mentions-legales.html` | Paramètres > Politiques > Mentions légales (si le champ n'existe pas : page `/pages/mentions-legales` et lien dans le pied de page) | ☐ |
| 5.6 | Cookies (liste réelle à établir avec le scanner de l'application de consentement) | `pages/page-cookies.html` | Pages, adresse `/pages/cookies` | ☐ |
| 5.7 | FAQ, À propos, Contact | `pages/page-faq.html`, `page-a-propos.html`, `page-contact.html` | Pages | ☐ |
| 5.8 | Rétractation en ligne | `pages/page-retractation.html` + section du thème | Pages, adresse `/pages/retractation`, modèle `page.retractation` | ☐ |
| 5.9 | Menus : principal (Boutique, Le rouleau, Grand kit, FAQ, À propos) ; pied de page (légal + « renoncer au contrat ici ») | — | Boutique en ligne > Navigation | ☐ |
| 5.10 | E-mail « Confirmation de commande » : ajouter le lien « renoncer au contrat ici » (`/pages/retractation`), le lien des CGV et le formulaire type de rétractation (texte de `pages/politique-retours-retractation.html`, section « Formulaire type ») | — | Paramètres > Notifications | ☐ |

Coût de l'étape : 0 €.

## Étape 6 — Applications (`apps.md`)

| # | Action | Coût | Fait |
|---|---|---|---|
| 6.1 | Judge.me Free : invitations après livraison, publication des avis négatifs, tri chronologique, importeur désactivé | 0 € | ☐ |
| 6.2 | Bannière de cookies native (régions UE/EEE) ; test en navigation privée | 0 € | ☐ |
| 6.3 | Shopify Messaging : modèles de bienvenue et de suivi J+7 | 0 € jusqu'à 10 000 e-mails par mois | ☐ |
| 6.4 | Shopify Flow : alerte de stock bas | 0 € | ☐ |
| 6.5 | Fonction de rétractation : garder le projet Netlify ou Cloudflare du site statique sur un sous-domaine (par exemple `outils.canapoil.fr`), avec `SITE_URL` sur ce sous-domaine et `ORIGINES_AUTORISEES=https://canapoil.fr` | 0 € | ☐ |

## Étape 7 — Domaine et redirections

| # | Action | Où | Coût | Fait |
|---|---|---|---|---|
| 7.1 | Importer `redirections.csv` (redirections 301 des anciennes URL du site statique vers Shopify : fiches, kits, pages, politiques) | Boutique en ligne > Navigation > Redirections d'URL > Importer | 0 € | ☐ |
| 7.2 | Connecter `canapoil.fr` à Shopify (enregistrements DNS indiqués par Shopify) ; déplacer le site statique sur le sous-domaine de l'étape 6.5 | Paramètres > Domaines | 0 € | ☐ |
| 7.3 | Mettre à jour l'URL du site dans Stripe (si le compte Stripe reste utilisé pour TikTok ou des liens de paiement), Google Merchant Center et les profils sociaux | — | 0 € | ☐ |

## Étape 8 — Tests avant ouverture

| # | Test | Résultat attendu | Fait |
|---|---|---|---|
| 8.1 | Commande test (mode test de Shopify Payments) : rouleau seul | Port 3,90 €, total 28,80 € | ☐ |
| 8.2 | Commande test : Grand kit | Port offert, total 39,90 € | ☐ |
| 8.3 | Panier sans cocher la case CGV | Passage au paiement bloqué, message d'erreur | ☐ |
| 8.4 | E-mail de confirmation reçu | Récapitulatif, lien CGV, formulaire type, lien « renoncer au contrat ici » | ☐ |
| 8.5 | Rétractation en ligne | Accusé de réception horodaté reçu par e-mail en moins d'une minute | ☐ |
| 8.6 | Navigation privée, refus des cookies | Aucun pixel chargé (onglet Réseau du navigateur) | ☐ |
| 8.7 | Remboursement de la commande test | Remboursement visible côté client | ☐ |
| 8.8 | Parcours complet sur un téléphone (TikTok ouvre le site dans son navigateur intégré) | Aucun blocage, pages lisibles sans zoom | ☐ |
| 8.9 | Toutes les variables `{{...}}` remplacées : rechercher « {{ » dans l'aperçu de chaque page et politique | Aucune occurrence | ☐ |

## Étape 9 — Ouverture et suivi

| # | Action | Coût | Fait |
|---|---|---|---|
| 9.1 | Retirer le mot de passe de la boutique | 0 € | ☐ |
| 9.2 | Annoncer la nouvelle adresse aux créateurs affiliés et dans les bios | 0 € | ☐ |
| 9.3 | Suivre chaque semaine : conversion, panier moyen, délai réel de livraison (90e centile), retours, litiges | 0 € | ☐ |
| 9.4 | Après 30 livraisons : recalculer le délai affiché (90e centile + 2 jours ouvrés) et mettre à jour fiches, politique d'expédition et tarifs d'expédition | 0 € | ☐ |
| 9.5 | Résilier l'ancien site seulement après 30 jours sans erreur de redirection | 0 € | ☐ |
