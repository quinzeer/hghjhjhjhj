# Applications Shopify : le minimum utile, avec les coûts réels

Principe : au palier 1 (≈ 155 commandes par mois, `brand.json` > `hypotheses_cles`), aucune application payante n'est nécessaire. Chaque application ajoutée ralentit la boutique et peut déposer des traceurs : n'installez que celles de ce tableau. Prix relevés sur l'App Store Shopify le 12/10/2026 ; Shopify facture les applications en dollars.

## 1. Tableau de décision

| Besoin | Application retenue | Coût réel | Alternative gratuite | Réglages indispensables |
|---|---|---|---|---|
| Avis clients vérifiés | **Judge.me** ([fiche](https://apps.shopify.com/judgeme)) | Offre Free « Forever Free » : avis illimités, photos et vidéos, extraits enrichis Google. Offre Awesome : 15 $ par mois, essai de 15 jours | — (l'offre Free suffit) | Invitation par e-mail après livraison ; avis négatifs publiés ; tri chronologique par défaut ; **ne jamais utiliser l'importeur d'avis ni la synchronisation AliExpress** proposés par l'application (faux avis, L121-4 C. conso) ; texte d'information sous le widget (CGV art. 13) |
| E-mails transactionnels et lettre d'information | **Shopify Messaging** ([fiche](https://apps.shopify.com/shopify-email)) | 10 000 e-mails gratuits par mois, puis à partir de 1 $ les 1 000 | Brevo gratuit, déjà utilisé par le site statique | Inscription avec consentement explicite ; lien de désinscription dans chaque e-mail ; e-mail J+7 de vente additionnelle (raclette) au prix normal |
| Bannière de consentement aux cookies | **Bannière native de Shopify** (Paramètres > Confidentialité des clients) ([aide Shopify](https://help.shopify.com/en/manual/privacy-and-security/privacy/customer-privacy-settings/privacy-settings)) | Incluse dans l'abonnement | **Complianz Consent** ([fiche](https://apps.shopify.com/gdpr-legal-cookie)) : offre Free (scanner de cookies, blocage automatique, une législation) ; Premium 5,99 $ par mois ou 59 $ par an, nécessaire pour le mode Consentement Google v2 | Régions UE/EEE ; refus aussi visible que l'acceptation ; test en navigation privée : aucun pixel avant le choix. Passer à Complianz Premium seulement si Google Ads est lancé (mode Consentement v2) |
| Informations GPSR sur la fiche | **Aucune application** : métachamps natifs (`theme.md` §6) + bloc déjà présent dans les descriptions du CSV | 0 € | — | Fabricant, personne responsable dans l'UE, identification, avertissements sur chaque fiche ; une fiche incomplète n'est pas publiée |
| Rétractation en ligne (« renoncer au contrat ici ») | **Section Liquid du kit** (`theme/sections/canapoil-retractation.liquid`) + fonction serveur du site statique, gardée en ligne gratuitement (Netlify ou Cloudflare) | 0 € | Shopify Forms ([fiche](https://apps.shopify.com/shopify-forms)), gratuit : la fiche ne confirme pas l'envoi automatique d'un accusé au client ; à tester, et à écarter si l'accusé horodaté n'est pas automatique | Variable `ORIGINES_AUTORISEES` de la fonction = adresse de la boutique ; test d'une rétractation avant l'ouverture |
| Kits (stock des composants) | **Shopify Bundles** ([fiche](https://apps.shopify.com/shopify-bundles)) | Gratuit | Kits importés comme produits simples (CSV du kit), stock suivi à la main | L'application a une note de 2,9 sur 5 (568 avis) : tester la synchronisation du stock sur un kit avant de supprimer les kits du CSV |
| Fournisseur (réassort du micro-stock) | **Aucune application au palier 1** : commande groupée passée à la main sur AliExpress ou CJ, livrée en France | 0 € | **DSers** ([fiche](https://apps.shopify.com/dsers)) : Basic gratuit ; Advanced 19,90 $ par mois ; Pro 49,90 $ par mois | DSers sert à passer des commandes fournisseur depuis Shopify. Le dropshipping colis par colis depuis la Chine est exclu par la stratégie (TikTok Shop, statut d'importateur GPSR, ≈ 5 € de taxes par colis) : ne l'utiliser que pour des commandes de stock |
| Automatisations (alerte de stock bas, étiquetage des commandes) | **Shopify Flow** ([fiche](https://apps.shopify.com/flow)) | Gratuit (la fiche ne précise pas les forfaits compatibles : à vérifier à l'installation) | Rappels manuels dans le tableur | Alerte quand le stock du rouleau descend sous 25 jours de ventes (§5.5 de la stratégie) |
| Transport en point relais | Application Mondial Relay ou agrégateur d'étiquettes | **Non vérifié** : aucune fiche officielle n'a pu être consultée le 12/10/2026 | Étiquettes créées sur le site du transporteur, comme au palier 0 | Critères de choix : sélection du point relais au paiement, étiquettes en lot, aucun abonnement fixe |
| Ventes sur TikTok Shop, Google, Meta | Applications officielles des plateformes | Installation gratuite selon les plateformes (non revérifié ici) | — | À connecter au palier 2 seulement, avec le consentement aux cookies déjà en place |

## 2. Budget mensuel des applications

| Palier | Applications | Coût mensuel |
|---|---|---|
| Bascule et palier 1 | Judge.me Free, Shopify Messaging (< 10 000 e-mails), bannière native, Bundles, Flow | **0 €** |
| Palier 2 (publicité) | + Complianz Premium si Google Ads (5,99 $) ; + Judge.me Awesome si les intégrations Google Shopping ou TikTok des avis deviennent utiles (15 $) | ≈ 21 $ par mois au plus |

## 3. À ne jamais installer

| Type d'application | Pourquoi |
|---|---|
| Comptes à rebours, « offre valable 2 h » sans date de fin réelle | Pratique réputée trompeuse (03 §1.7) |
| Fenêtres « Marie vient d'acheter… », « 27 personnes regardent » | Fausse popularité si les données ne sont pas réelles |
| Compteurs de stock non reliés au stock réel | Fausse rareté |
| Importeurs d'avis (AliExpress, Amazon, autres boutiques) | Faux avis : L121-4 C. conso, contrôlé par la DGCCRF |
| Options payantes pré-cochées (assurance colis, « protection d'achat ») | Interdit (L121-17 C. conso) |
| Applications qui chargent un pixel sans passer par l'API de consentement | Dépôt de traceurs sans consentement (sanctions CNIL) |
