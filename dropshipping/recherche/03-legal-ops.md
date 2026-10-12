# 03 — Juridique, conformité et opérations (France, octobre 2026)

> Rédigé le 12 octobre 2026. Périmètre : vente B2C en France depuis une société française déjà immatriculée (forme exacte inconnue : SASU, EURL ou micro-entreprise), boutique Shopify, 150 € de dépenses cash maximum sur 3 mois, aucun budget publicitaire au départ.
>
> Ce dossier fournit une analyse documentée et des modèles prêts à adapter. Les points marqués **« à valider »** demandent la confirmation d'un avocat ou d'un expert-comptable avant engagement financier.
>
> **Conventions de fiabilité**
> - **[Sn]** : chiffre ou règle sourcé, URL dans la section 8.
> - **Fiabilité élevée** : texte officiel, administration, page tarifaire de l'opérateur.
> - **Fiabilité moyenne** : cabinet d'avocats, expert-comptable, média spécialisé.
> - **Fiabilité faible** : blog commercial, comparatif d'outils, témoignage.
> - **[E-é] / [E-m] / [E-f]** : estimation de l'auteur, confiance élevée / moyenne / faible. Les hypothèses sont écrites à côté.
> - Les articles de code cités sans [Sn] (« L221-18 C. conso », « 1245-5 C. civ. ») renvoient au texte consolidé sur Légifrance ; confiance élevée sauf mention contraire.
>
> **Modèles de pages légales** livrés avec ce dossier : `recherche/pages-legales/` → `mentions-legales.md`, `cgv.md`, `retours-retractation.md` (avec formulaire type), `livraison.md`, `confidentialite.md`, `cookies.md`.

---

## Sommaire

0. [Synthèse décisionnelle](#0-synthèse-décisionnelle)
1. [Droit de la vente en ligne en France en 2026](#1-droit-de-la-vente-en-ligne-en-france-en-2026)
2. [Sécurité des produits et environnement](#2-sécurité-des-produits-et-environnement)
3. [Fiscalité et douane](#3-fiscalité-et-douane)
4. [Paiements](#4-paiements)
5. [Fournisseurs et logistique](#5-fournisseurs-et-logistique)
6. [Checklist de conformité avant lancement](#6-checklist-de-conformité-avant-lancement)
7. [Alertes et points à vérifier](#7-alertes-et-points-à-vérifier)
8. [Sources](#8-sources)

---

## 0. Synthèse décisionnelle

### 0.1 Les sept constats qui modifient la stratégie

| # | Constat (octobre 2026) | Conséquence pour le projet | Source |
|---|---|---|---|
| 1 | **Fin de la franchise de droits de douane sous 150 €.** Depuis le 1er juillet 2026, chaque envoi B2C d'une valeur ≤ 150 € importé d'un pays tiers paie un droit forfaitaire de **3 € par « article »** (marchandises d'un même classement tarifaire), quel que soit le régime de TVA (IOSS ou non), jusqu'au 1er juillet 2028. | Le dropshipping depuis la Chine perd 3 € par catégorie de produit et par colis. | [S1][S2] |
| 2 | **Redevance UE de gestion de 2 € par article distinct à partir du 1er novembre 2026**, sans seuil de valeur, non remboursable, à la charge du déclarant (vendeur ou plateforme), qui la répercute. | Un produit acheté 8 € en Chine coûte environ **14 € rendu** (+75 %) à partir de novembre 2026 [E-m]. | [S3][S1] |
| 3 | **Le vendeur établi en France qui fait livrer un produit depuis la Chine a, selon la lecture la plus probable du règlement GPSR, la qualité d'importateur** : nom et adresse sur le produit ou l'emballage, vérification de la documentation du fabricant, conservation 10 ans, gestion des accidents et rappels. | Obligations impossibles à tenir colis par colis via AliExpress. Le **choix du fournisseur détermine le statut juridique** du client (importateur ou distributeur). | [S32] [E-m] |
| 4 | **Responsabilité élargie du producteur (REP)** : celui qui met en premier un produit emballé sur le marché français doit adhérer aux éco-organismes (emballages, plus la filière du produit), obtenir un identifiant unique (IDU) et l'afficher dans ses CGV et sur son site. Amende jusqu'à 30 000 €. | Coût fixe de 80-110 € HT/an pour les seuls emballages [E-f], évitable en achetant auprès d'un grossiste établi en France qui a déjà déclaré les produits. | [S33][S35] |
| 5 | **Le vendeur répond de plein droit des retards et défauts de son fournisseur** (L221-15 C. conso). Délai maximum de 30 jours sans date annoncée (L216-1). La DGCCRF a relevé des manquements sur **116 sites de dropshipping sur 215 contrôlés (2022)** et **141 sur 251 (2023)**. | Les délais affichés doivent être les délais réels. Les clauses « délais indicatifs » sont illicites. | [S14] |
| 6 | **Trois obligations nouvelles en 2026** : fonctionnalité de rétractation en ligne « renoncer au contrat ici » depuis le **19 juin 2026** ; avis harmonisé UE sur la garantie légale (application prévue le **27 septembre 2026**, non transposé en France à mi-septembre) ; réception des factures électroniques par toute entreprise assujettie depuis le **1er septembre 2026**. Le lien vers la plateforme européenne RLL est à **retirer** (plateforme fermée le 20 juillet 2025). | Les modèles de CGV et la page retours livrés intègrent ces évolutions. | [S19][S20][S37][S12][S22] |
| 7 | **Paiements** : Shopify Payments, forfait Basic, 1,5 % + 0,25 € par carte standard ; litige facturé 15 € ; Visa sanctionne les marchands au-delà de **1,5 %** (fraude + litiges) depuis avril 2026. | Les délais longs du dropshipping Chine génèrent des litiges « non reçu » qui menacent le compte de paiement. | [S28][S30] |

### 0.2 Verdict sur la thèse de départ (angle juridique et opérationnel)

| Élément de la thèse | Verdict | Raison chiffrée |
|---|---|---|
| Dropshipping comme phase de validation produit | **Confirmé avec amendement** | Valider en dropshipping **depuis un stock situé en France ou dans l'UE** (grossiste français, BigBuy, entrepôt UE de CJ). Le Chine-direct se limite aux échantillons et à des tests de moins de 20 commandes : +5 € de droits et redevance par article à partir de novembre 2026 [S1][S3], statut d'importateur GPSR, emballages sans Triman, délais de 7-15 jours [E-m]. |
| Acquisition 100 % organique (TikTok, créateurs à la commission) | **Confirmé, encadré** | Loi n° 2023-451 : mention « Publicité » ou « Collaboration commerciale », contrat écrit au-delà de 1 000 € HT par an et par créateur (décret n° 2025-1137, depuis le 1/01/2026), **responsabilité solidaire de l'annonceur** (art. 8 III) [S41][S59]. |
| Réinvestir les profits en publicité payante | **Confirmé, sous contrainte cookies** | Les pixels Meta, TikTok et Google ne se déclenchent qu'après consentement (art. 82 loi Informatique et Libertés). La CNIL a sanctionné Shein de 150 M€ pour cookies déposés sans consentement (1/09/2025) [S17]. Le bandeau conforme réduit le signal publicitaire : à intégrer dans le calcul du ROAS. |
| Marque propre + stock en entrepôt UE (3PL) dès validation | **Confirmé et avancé** | Le stock importé en gros paie les droits normaux une fois par lot (au lieu de 3 € + 2 € par colis), permet l'Info-tri, le marquage du nom de l'importateur et un contrôle qualité par lot. Seuil de bascule : ≈ 5 commandes/jour sur un même produit [E-m]. Avec la marque propre, le client devient **« fabricant »** au sens du GPSR (art. 13) : obligations complètes. |
| Extension multi-pays UE | **Confirmé, à préparer tôt** | Ventes à distance intra-UE : TVA du pays de destination via le guichet OSS au-delà de 10 000 € de ventes intra-UE annuelles ; REP propres à chaque pays (Allemagne, Espagne…) ; langue du pays ; GPSR : avertissements dans la langue de chaque État. |

### 0.3 Les douze décisions juridiques et opérationnelles

1. **Liste blanche de catégories** pour la phase 1 : produits non électriques, pour adultes, sans contact alimentaire, sans cosmétique, sans batterie, sans allégation santé, sans marque de tiers. Tout produit soumis au marquage CE est exclu tant qu'il n'y a pas de stock contrôlé (section 2.4).
2. **Fournisseur prioritaire établi en France** (grossiste avec stock en France et IDU) : le client reste **distributeur** au sens du GPSR et n'est pas producteur REP pour ces produits. Second choix : stock UE (BigBuy, entrepôt UE de CJ). Chine-direct : échantillons et tests seulement.
3. **Médiateur de la consommation avant la première vente** : CM2C, 48 € pour 3 ans (≤ 10 personnes) + 36 € par médiation à distance [S23].
4. **Publication des six pages légales** fournies, avec la fonctionnalité de rétractation « renoncer au contrat ici » et l'encadré réglementaire de garantie légale (section 1.4).
5. **Délai affiché = délai réellement constaté** (90e centile des 30 dernières livraisons + 2 jours ouvrés). Jamais de clause « délais indicatifs ».
6. **Aucun prix barré pendant les 30 premiers jours de vente d'un produit**, aucun compte à rebours, aucune mention de stock limité non réelle, aucun avis importé d'AliExpress.
7. **Bandeau cookies conforme CNIL** (bouton « Tout refuser » au premier niveau) **avant tout pixel publicitaire**.
8. **Dossier produit GPSR par référence** avant mise en ligne : identité du fabricant, personne responsable dans l'UE, photos de l'échantillon reçu, avertissements en français, preuves de conformité.
9. **Paiement** : Shopify Payments + PayPal, 3-D Secure activé, numéros de suivi synchronisés, descripteur bancaire = nom de marque, taux de litige cible < 0,5 %.
10. **Retours vers une adresse en France** ({{ADRESSE_RETOUR}}), jamais vers la Chine.
11. **Fiscalité** : rester en franchise en base de TVA tant que le CA reste sous 85 000 € et que les achats portent peu de TVA récupérable ; anticiper la sortie (section 3.2). Choisir dès maintenant une plateforme agréée de facturation électronique (réception obligatoire depuis le 1/09/2026).
12. **Micro-entreprise : sortie à anticiper** dès que la marge brute passe sous ~40 % du CA ou que le CA dépasse ~5 000 €/mois [E-m] : les cotisations de 12,3 % du CA absorbent jusqu'à la moitié de la marge brute d'un produit de dropshipping (section 3.6).

### 0.4 Ce qui change selon la forme juridique

| Sujet | Micro-entreprise (entrepreneur individuel) | EURL / SASU à l'impôt sur les sociétés | Conclusion modifiée ? |
|---|---|---|---|
| Plafond de chiffre d'affaires | **203 100 € HT** de ventes de marchandises en 2026 [S10] | Aucun | Oui : la micro plafonne à ≈ 17 000 €/mois de CA, incompatible avec le palier 10 k€ de bénéfice net/mois. |
| Prélèvements sociaux | **12,3 % du CA** (ventes de marchandises) [S10b] | Sur la rémunération versée ; rien si aucune rémunération | Oui : en dropshipping (marge brute 25-40 %), 12,3 % du CA = 31-49 % de la marge brute. |
| Impôt sur le bénéfice | Impôt sur le revenu (abattement 71 %) ou versement libératoire 1 % du CA | IS **15 % jusqu'à 42 500 €** de bénéfice, 25 % au-delà (CA < 10 M€, capital libéré, détenu à 75 % par des personnes physiques) [S9] | Oui à partir de ≈ 2 000 €/mois de bénéfice [E-m]. |
| Franchise en base de TVA | Possible (seuil 85 000 €) | Possible aussi (la franchise vise tout assujetti) | Non. |
| Comptabilité | Livre des recettes + registre des achats | Comptabilité complète, bilan, liasse, approbation et dépôt des comptes | Coût expert-comptable 1 000-2 500 €/an [E-m], hors budget initial. |
| Mentions légales | Nom, prénom, mention « EI », SIREN, RCS | Raison sociale, forme, capital, RCS, siège | Les modèles fournis couvrent les deux cas. |
| Achat de stock (phase 3PL) | Possible, mais cotisations sur CA et pas de déduction du stock pour les cotisations | Stock déductible du résultat, TVA d'import autoliquidée | Oui : passer en société avant la phase stock. |

### 0.5 Coût minimum de conformité sur les 3 premiers mois

| Poste | Statut | Coût | Commentaire |
|---|---|---|---|
| Médiateur (CM2C, ≤ 10 personnes) | **Obligatoire** (L612-1 C. conso) | **48 €** pour 3 ans [S23] | Plus 36 € par médiation effectivement déclenchée. |
| REP emballages (Citeo ou Léko, forfait < 10 000 UVC) | Obligatoire si le client est le premier metteur sur le marché français (schémas A, B, D de la section 2.1) | **80-110 € HT/an** [S35] [E-f] | 0 € si le fournisseur établi en France a déclaré les produits et leurs emballages (schéma C). |
| Bandeau cookies | Obligatoire dès qu'un traceur non exempté est utilisé | 0 € (bannière native Shopify ou offre gratuite d'un outil de consentement) | Configuration « Tout refuser » au premier niveau. |
| Pages légales, bouton de rétractation | Obligatoire | 0 € (modèles fournis, formulaire Shopify) | Voir `pages-legales/`. |
| Réception des factures électroniques | Obligatoire depuis le 1/09/2026 pour les assujettis | 0-15 €/mois selon plateforme agréée [E-f] | À choisir avec l'expert-comptable ou la banque. |
| Assurance RC professionnelle + RC produits | Recommandée (forte exposition : responsabilité du fait des produits) | 150-500 €/an [E-f] | Hors budget initial ; à souscrire dès les premiers profits et **avant** tout stock. |
| Dépôt de marque INPI (1 classe) | Recommandé avant la marque propre | 190 € [S53] | À reporter à la validation d'un produit. |
| **Total obligatoire** | | **48 € (schéma C) à ≈ 160 € (schémas A/B)** | Le budget de 150 € ne couvre pas à la fois la REP, l'abonnement Shopify et les échantillons. Le schéma C (fournisseur établi en France) est le seul compatible avec le budget. |

---

## 1. Droit de la vente en ligne en France en 2026

### 1.1 Informations obligatoires et emplacement sur le site

| Information | Base légale | Emplacement | Point d'attention dropshipping |
|---|---|---|---|
| Dénomination ou raison sociale, forme, capital, adresse du siège, téléphone, e-mail | LCEN art. 1-1 (ex-art. 6 III, réécrit par la loi SREN du 21/05/2024) et art. 19 ; R111-1 C. conso [S43] | Mentions légales + CGV | Adresse géographique réelle obligatoire ; un simple formulaire de contact ne suffit pas. |
| SIREN et numéro RCS | LCEN art. 19 | Mentions légales, CGV, factures | En micro : mention « EI » à côté du nom. |
| Numéro de TVA intracommunautaire | LCEN art. 19 | Mentions légales, factures | En franchise : mention « TVA non applicable, art. 293 B du CGI » sur les factures [S6]. |
| Directeur de la publication | LCEN art. 1-1 | Mentions légales | Le représentant légal par défaut. |
| Hébergeur : nom, adresse, téléphone | LCEN art. 1-1 | Mentions légales | Shopify : entité et adresse à recopier depuis les conditions Shopify en vigueur. |
| Caractéristiques essentielles du produit | L111-1 1° C. conso | Fiche produit | Dimensions, matières, compatibilités, contenu du colis. Photos du produit réellement livré. |
| Prix TTC et frais de livraison | L112-1, L221-5 C. conso | Fiche produit, panier | Aucun frais à payer à la livraison (droits, TVA, frais de dédouanement) : envoi rendu droits acquittés. |
| Date ou délai de livraison | L111-1 3°, L216-1 C. conso | Fiche produit, tunnel, confirmation | Délai réel, jamais « indicatif ». |
| Garanties légales (conformité, vices cachés) | L111-1, L217-1 et s. C. conso ; encadré du décret n° 2022-946 | CGV + page dédiée | Encadré à reproduire à l'identique (modèle dans `cgv.md`). |
| Droit de rétractation : conditions, délai, modalités, formulaire type, **existence et emplacement de la fonctionnalité de rétractation en ligne** | L221-5 2° (modifié par l'ordonnance n° 2026-2), L221-21, R221-1 C. conso [S19][S20] | CGV, page retours, e-mail de confirmation | Bouton « renoncer au contrat ici » accessible pendant 14 jours. |
| Frais de retour à la charge du consommateur | L221-5 3° C. conso | Page retours, CGV | À défaut d'information, ils restent à la charge du vendeur. |
| Coordonnées du médiateur | L616-1 C. conso | CGV, mentions légales, page contact | Lien vers la plateforme européenne RLL à supprimer (fermée le 20/07/2025) [S22]. |
| Moyens de paiement acceptés | L221-5 C. conso | Tunnel de paiement | Aucun surcoût selon le moyen de paiement (L112-12). |
| Modalités de collecte et de vérification des avis | L111-7-2, D111-16 à D111-19 C. conso | À proximité des avis | Voir section 1.8. |
| Identifiant unique REP (IDU) | L541-10-13 C. env. [S33] | CGV + mentions légales | Un IDU par filière. |
| Informations de sécurité GPSR (fabricant, personne responsable UE, identification, avertissements) | Règl. (UE) 2023/988, art. 19 [S32] | Fiche produit | Modèle de bloc en section 2.3. |
| Langue française | Loi n° 94-665 du 4/08/1994 | Tout le site, notices, emballages | Notice uniquement en anglais ou en chinois : non conforme. |
| Archivage du contrat ≥ 120 € et accès du client | L213-1 et D213-1 C. conso | CGV | Conserver 10 ans (Shopify conserve les commandes ; prévoir un export). |
| Information sur les données personnelles et les cookies | RGPD art. 13 ; art. 82 loi n° 78-17 | Politique de confidentialité, page cookies, bandeau | Voir section 1.9. |

**Sanctions** : absence de mentions LCEN : 1 an d'emprisonnement et 75 000 € d'amende (personne physique), quintuple pour une personne morale (LCEN art. 1-2) [S43] ; manquement aux informations précontractuelles : amende administrative jusqu'à 3 000 € (personne physique) et 15 000 € (personne morale) (L242-10 C. conso).

### 1.2 Tunnel de commande

| Étape | Exigence | Base légale |
|---|---|---|
| Panier | Récapitulatif des articles, prix TTC, frais de livraison, délai, possibilité de corriger la commande avant validation | 1127-2 C. civ. ; L221-14 C. conso |
| Options payantes | Aucune case pré-cochée (assurance colis, livraison express, « protection d'achat ») | L121-17 III C. conso |
| Acceptation des CGV | Case à cocher non pré-cochée + lien vers les CGV accessibles et téléchargeables | 1127-1 C. civ. |
| Bouton final | Libellé « Commande avec obligation de paiement » ou formule analogue dénuée d'ambiguïté (« Payer maintenant ») | L221-14 C. conso |
| Paiement | Authentification forte (3-D Secure) ; aucun surcoût par carte | L133-44 C. monét. fin. ; L112-12 C. conso |
| Accusé de réception | E-mail de confirmation sans délai | 1127-2 C. civ. |
| Confirmation du contrat | Sur support durable au plus tard à la livraison : récapitulatif, CGV, formulaire de rétractation, lien vers la fonctionnalité de rétractation | L221-13 C. conso |

### 1.3 Droit de rétractation (14 jours) et fonctionnalité de rétractation en ligne

| Règle | Contenu | Base légale |
|---|---|---|
| Délai | 14 jours à compter de la réception du bien ; commande en plusieurs livraisons : à compter de la réception du dernier bien | L221-18 C. conso [S21] |
| Défaut d'information | Délai prolongé de 12 mois | L221-20 C. conso |
| Formes de rétractation | Formulaire type, toute déclaration dénuée d'ambiguïté, **fonctionnalité en ligne obligatoire depuis le 19/06/2026** | L221-21 C. conso (ordonnance n° 2026-2 du 5/01/2026 ; décret n° 2026-3 du 5/01/2026) [S19][S20] |
| Fonctionnalité en ligne : libellés | Accès : « renoncer au contrat ici » ou formule équivalente non ambiguë ; validation : « confirmer la rétractation » | Décret n° 2026-3 [S19][S20] |
| Fonctionnalité en ligne : champs | Nom et prénom ; identification du contrat (numéro de commande) ; moyen électronique de réception de l'accusé | Décret n° 2026-3 [S20] |
| Accusé de réception | Envoyé dans un délai raisonnable sur support durable : contenu de la déclaration, date et heure d'envoi | Décret n° 2026-3 [S19][S20] |
| Disponibilité | Visible, directement accessible pendant toute la durée du délai, gratuite | Ordonnance n° 2026-2 [S19] |
| Renvoi du bien | Par le client, au plus tard 14 jours après sa déclaration | L221-23 C. conso |
| Frais de retour | À la charge du client s'il en a été informé ; sinon à la charge du vendeur | L221-23, L221-5 C. conso |
| Remboursement | Sous 14 jours après la déclaration, frais de livraison standard inclus, même moyen de paiement ; report possible jusqu'à récupération du bien ou preuve d'expédition | L221-24 C. conso |
| Retard de remboursement | Majoration de plein droit : taux légal jusqu'à 10 jours de retard, puis 5 %, 10 %, 20 %, 50 %, puis 5 points par mois supplémentaire | L242-4 C. conso |
| Dépréciation | Le client répond de la dépréciation due à des manipulations excédant l'essai nécessaire | L221-23 C. conso |

**Exceptions (L221-28 C. conso) appliquées aux produits de dropshipping**

| Exception | Exemples | Applicable au catalogue ? |
|---|---|---|
| Biens confectionnés selon les spécifications du consommateur ou nettement personnalisés (3°) | Gravure du prénom, impression photo | Oui, si la personnalisation est réelle. Un choix de couleur ne suffit pas. |
| Biens susceptibles de se détériorer ou de se périmer rapidement (4°) | Denrées fraîches | Hors liste blanche. |
| Biens descellés après livraison et non renvoyables pour des raisons d'hygiène ou de protection de la santé (5°) | Écouteurs intra-auriculaires, brosses, sous-vêtements | Seulement si le produit est **scellé** à l'expédition et que le client a rompu le scellé. Un produit livré en sachet ouvert reste retournable. |
| Biens mélangés de manière indissociable (6°) | Carburant | Non concerné. |
| Enregistrements audio, vidéo, logiciels descellés (9°) | DVD | Non concerné. |

**Implémentation Shopify** (coût 0 €) : page `/pages/retractation` avec formulaire (nom, prénom, numéro de commande, e-mail), bouton « renoncer au contrat ici » dans le pied de page, dans l'espace client et dans l'e-mail de confirmation ; e-mail automatique d'accusé de réception contenant la déclaration, la date et l'heure. Le modèle de page est dans `retours-retractation.md`.

### 1.4 Garantie légale de conformité et vices cachés

| Garantie | Durée | Preuve | Remèdes | Base |
|---|---|---|---|---|
| Conformité (biens neufs) | 2 ans à compter de la délivrance | Défaut présumé exister à la délivrance pendant 24 mois : le client prouve seulement le défaut | Réparation ou remplacement sous 30 jours, sans frais ; à défaut, réduction du prix ou résolution ; +6 mois de garantie après réparation ; nouvelle garantie de 2 ans si le vendeur impose le remplacement | L217-3 à L217-32 C. conso |
| Vices cachés | 2 ans à compter de la découverte | Le client prouve le vice antérieur à la vente | Réduction du prix ou remboursement contre restitution | 1641 à 1649 C. civ. |
| Garantie commerciale | Facultative | Contrat écrit, mention des garanties légales | Selon contrat | L217-21 et s. C. conso |

- **Responsabilité du vendeur** : le client s'adresse au vendeur, jamais au fournisseur. Le recours contre un fournisseur chinois est théorique. Provision recommandée : 3-8 % du CA pour retours, remplacements et litiges en phase dropshipping Chine, 1-3 % avec stock contrôlé [E-f].
- **Obstacle de mauvaise foi** : amende civile jusqu'à 300 000 € ou 10 % du CA moyen annuel (L241-5 C. conso).
- **Encadré réglementaire** obligatoire dans les CGV (décret n° 2022-946 du 29/06/2022) : reproduit dans `cgv.md`, article 10.
- **Avis harmonisé UE** sur la garantie légale (règlement d'exécution (UE) 2025/1960, en application de la directive (UE) 2024/825, application prévue le 27/09/2026) [S37]. La France n'avait pas transposé la directive à mi-septembre 2026 [S36]. Recommandation : afficher l'avis harmonisé (visuel officiel, non modifiable) en pied de page dès sa transposition ; coût nul.
- **Directive « droit à la réparation » (UE) 2024/1799** : transposition due au 31/07/2026, non réalisée par la France à cette date [S38]. À la transposition, l'extension de garantie après réparation passera à 12 mois. Les CGV devront être mises à jour.

### 1.5 Livraison

| Règle | Contenu | Base légale |
|---|---|---|
| Délai | Livraison à la date ou dans le délai indiqué ; sans indication : **30 jours maximum** après la conclusion du contrat | L216-1 C. conso |
| Retard | Le client met en demeure de livrer dans un délai supplémentaire raisonnable, puis peut résoudre le contrat ; résolution immédiate si le délai était essentiel ou si le vendeur refuse de livrer | L216-6 C. conso |
| Remboursement après résolution | Sous 14 jours | L216-3 C. conso |
| Risque de perte ou d'avarie | Supporté par le vendeur jusqu'à la prise de possession physique par le client | L216-4 C. conso |
| Responsabilité | Le vendeur répond de plein droit de la bonne exécution, y compris par ses fournisseurs et transporteurs | L221-15 C. conso |
| Clauses interdites | « Délais donnés à titre indicatif », exclusion de responsabilité pour retard, délai de réserve imposé au client | L216-1 ; R212-1 C. conso (clauses noires) |

**Pratique recommandée** : afficher une fourchette « livré entre le JJ/MM et le JJ/MM » calculée sur le 90e centile des délais constatés + 2 jours ouvrés ; e-mail proactif dès qu'un colis dépasse la date haute ; remboursement ou renvoi sans attendre la mise en demeure.

### 1.6 Médiateur de la consommation

| Option | Coût | Conditions | Source |
|---|---|---|---|
| **CM2C** | **48 € pour 3 ans** (≤ 10 personnes) ; 36 € par médiation à distance | Paiement unique | [S23] |
| CNPM Médiation Consommation | ≈ 35 € (via partenariat FNAE) à 150 € pour 3 ans selon le canal | À vérifier sur le site du médiateur | [S24b] (fiabilité faible) |
| Médiateur du e-commerce (FEVAD) | Adhésion FEVAD nécessaire | Coût d'adhésion supérieur au budget [E-m] | — |
| Medicys | Ne plus retenir : retiré de la liste des médiateurs référencés selon plusieurs sources | À vérifier sur la liste officielle CECMC | [S24b] |

- **Obligation** : garantir au consommateur le recours effectif et gratuit à un médiateur (L612-1) et l'en informer (L616-1). Le médiateur choisi doit figurer sur la **liste officielle de la CECMC**.
- **Sanction** : amende administrative jusqu'à 3 000 € (personne physique) et 15 000 € (personne morale) (L641-1 C. conso).
- **Plateforme RLL (ODR)** : supprimée par le règlement (UE) 2024/3228 avec effet au 20/07/2025 ; le lien ne doit plus figurer sur le site ni dans les CGV [S22].

### 1.7 Prix, promotions et urgence

| Pratique | Règle | Sanction encourue | Consigne pour le site |
|---|---|---|---|
| Prix barré, « -50 % » | Prix de référence = **prix le plus bas pratiqué pendant les 30 jours précédant la réduction** ; en cas de réductions successives, prix d'avant la première réduction | Pratique commerciale trompeuse : 2 ans d'emprisonnement et 300 000 € (personne physique), montant porté à 10 % du CA moyen annuel ou 50 % des dépenses engagées (L132-2) | Aucun prix barré pendant les 30 premiers jours de vente d'un produit. Historique des prix conservé (export Shopify). |
| « Prix conseillé », « valeur 79 € » | Un prix de comparaison fictif est trompeur | Idem | Ne jamais citer un prix de comparaison non pratiqué. |
| Compte à rebours, « offre valable 2 h » | Déclarer faussement qu'un produit n'est disponible que pendant une période très limitée : pratique **réputée** trompeuse | Idem, sans débat sur l'effet | Compte à rebours autorisé seulement pour une date de fin réelle et respectée. |
| « Plus que 3 en stock », « 27 personnes regardent ce produit » | Fausse rareté, fausse popularité | Idem | Seulement des données réelles issues du stock ou du trafic. |
| Origine (« marque française », drapeau français) pour un produit fabriqué et expédié de Chine | Tromperie sur l'origine et les qualités substantielles | Idem + tromperie (L441-1, L454-1 : 2 ans, 300 000 €) | Indiquer le pays d'expédition sur la page livraison. |
| « Livraison gratuite » avec prix gonflé | Licite si le prix est réel ; trompeur si un prix de référence fictif est affiché | — | Les frais de port inclus dans le prix sont licites. |

**Cas récent** : Shein a accepté en juillet 2025 une amende transactionnelle de **40 M€** proposée par la DGCCRF pour fausses réductions : sur les annonces vérifiées, 57 % n'offraient aucune baisse réelle et 11 % masquaient une hausse [S16]. Fiche DGCCRF sur les annonces de réduction mise à jour le 25/08/2026 [S18].

### 1.8 Avis clients

| Obligation | Base légale | Mise en œuvre |
|---|---|---|
| Indiquer si les avis font l'objet d'un contrôle et, si oui, ses modalités | L111-7-2 ; D111-17 C. conso | Texte sous le bloc d'avis : « Avis collectés auprès de clients ayant passé commande, vérifiés par [outil] » |
| Date de l'avis et de l'expérience ; critères de classement (chronologique par défaut) | D111-17 | Paramétrage de l'application d'avis |
| Motifs de rejet d'un avis ; publication des avis négatifs | D111-18, D111-19 | Ne pas filtrer les avis 1-2 étoiles |
| Contrepartie éventuelle à l'avis | D111-17 | Mention « avis rémunéré par un bon d'achat » si incitation |
| Interdiction des faux avis, des avis achetés et de l'affirmation non vérifiée que les avis émanent de clients | L121-4 C. conso (ajouts de la directive Omnibus) | **Aucun import d'avis AliExpress ou d'avis d'autres boutiques** |

La DGCCRF a constaté des faux avis lors de son enquête dropshipping, pratique présentée comme « courante » et même recommandée dans certaines formations [S14].

### 1.9 RGPD, prospection et cookies

**Données personnelles (RGPD)**

| Obligation | Base | Action |
|---|---|---|
| Information des personnes | Art. 13 RGPD | Politique de confidentialité (modèle `confidentialite.md`) |
| Registre des traitements | Art. 30 RGPD (traitement non occasionnel : pas d'exemption) | Tableur : finalité, données, destinataires, durées, transferts |
| Contrats de sous-traitance | Art. 28 RGPD | Accepter les DPA de Shopify, Stripe/Shopify Payments, outil e-mail, application d'avis |
| **Transferts vers la Chine** (nom, adresse, téléphone transmis au fournisseur pour l'expédition) | Art. 44-46 RGPD ; pas de décision d'adéquation pour la Chine | Clauses contractuelles types (décision 2021/914) avec le fournisseur ou l'agent + information explicite des clients. Argument supplémentaire pour un fournisseur établi dans l'UE. |
| Transferts vers les États-Unis | Décision d'adéquation « Data Privacy Framework » | Vérifier la certification DPF des prestataires américains |
| Sécurité et violations | Art. 32-34 RGPD | Double authentification sur Shopify ; notification à la CNIL sous 72 h en cas de violation |
| Durées de conservation | Recommandations CNIL ; L123-22 C. com. | Clients : relation + 3 ans (prospection) ; prospects : 3 ans après le dernier contact ; pièces comptables : 10 ans |
| Sanctions | Art. 83 RGPD | Jusqu'à 20 M€ ou 4 % du CA mondial ; procédure simplifiée CNIL : jusqu'à 20 000 € |

**Prospection** : e-mail et SMS vers des particuliers : consentement préalable, sauf client existant pour des produits analogues avec possibilité d'opposition à la collecte et dans chaque message (L34-5 CPCE).

**Cookies et traceurs (règles CNIL)**

| Règle | Contenu |
|---|---|
| Consentement préalable | Aucun traceur publicitaire ou de mesure non exemptée avant le choix de l'internaute (art. 82 loi n° 78-17) |
| Refus aussi simple que l'acceptation | Bouton « Tout refuser » au premier niveau, même visibilité que « Tout accepter » (lignes directrices CNIL du 17/09/2020) [S57] |
| Durée du choix | Conservation du choix (accord ou refus) pendant 6 mois, puis nouvelle sollicitation (pratique recommandée) [S57] |
| Mesure d'audience exemptée | Statistiques anonymes, cookies ≤ 13 mois, données ≤ 25 mois, aucun recoupement ; Google Analytics en configuration standard n'est pas exempté [S57] |
| Retrait du consentement | Lien « Gérer mes cookies » permanent en pied de page |
| Preuve | Journal des consentements (outil de consentement) |

Sanctions récentes : Shein 150 M€ et Google 325 M€ (CNIL, 1/09/2025), pour dépôt de cookies sans consentement et mécanismes de refus défaillants [S17].

### 1.10 Influence commerciale (loi n° 2023-451 du 9 juin 2023)

| Obligation | Détail | Base |
|---|---|---|
| Transparence | Mention « Publicité » ou « Collaboration commerciale », claire et visible pendant toute la durée du contenu | Art. 5 [S59] |
| Images | « Image retouchée » ou « Image virtuelle » selon le cas | Art. 5 [S59] |
| Produits interdits à la promotion | Chirurgie et médecine esthétiques, abstention thérapeutique, produits contenant de la nicotine, certains produits financiers et crypto-actifs non autorisés, animaux sauvages, notamment | Art. 3 et 4 [S59] |
| Contrat écrit | Obligatoire au-delà de **1 000 € HT** par an, par annonceur et par objectif promotionnel, avantages en nature (produits offerts) compris ; applicable depuis le **1/01/2026** | Art. 8 ; décret n° 2025-1137 [S41] |
| Responsabilité solidaire | L'annonceur répond solidairement des dommages causés aux tiers par l'influenceur | Art. 8 III [S59] |
| Influenceur qui vend lui-même en dropshipping | Informations précontractuelles + identité du fournisseur ; vérification de la disponibilité et de la licéité des produits ; responsabilité de plein droit envers l'acheteur | Art. 7 [S59] [E-m sur la numérotation] |
| Sanctions | 2 ans d'emprisonnement et 300 000 € pour pratique commerciale trompeuse ; « name and shame » DGCCRF | L132-2 C. conso |

Contrôles : plus de 300 influenceurs contrôlés en 2022-2023, environ la moitié en anomalie sur l'affichage de l'intention commerciale [S42].

### 1.11 Allégations environnementales et textile

| Règle | Contenu | Statut octobre 2026 |
|---|---|---|
| Mentions interdites sur produits et emballages | « Biodégradable », « respectueux de l'environnement » ou équivalent | En vigueur (L541-9-1 C. env.) |
| « Neutre en carbone » | Encadré (justification, rapport public) | En vigueur (loi Climat et résilience) |
| Directive (UE) 2024/825 [S58] (allégations génériques « éco », « vert », labels non certifiés) | Interdiction des allégations génériques sans performance reconnue | Application prévue au 27/09/2026 ; non transposée en France (projet de loi DDADUE en navette) ; mise en demeure de la Commission le 28/05/2026 [S36] |
| Loi « mode ultra-express » (loi n° 2026-602, publiée le 9/07/2026 selon une source) | Pénalité par vêtement dans l'éco-contribution, interdiction de publicité (y compris par influenceurs) au 1/01/2027, affichage de l'origine | Seuils fixés par décret, non publiés au 28/09/2026 [S40] |

Consigne : aucune allégation environnementale. Le textile à petit prix et à renouvellement rapide est à éviter en phase 1.

### 1.12 Accessibilité numérique

La directive (UE) 2019/882, transposée en France, s'applique aux services de commerce électronique depuis le **28/06/2025**. Les **microentreprises** (moins de 10 personnes **et** CA ou total de bilan ≤ 2 M€) prestataires de services en sont exemptées [S44]. Le client est exempté au démarrage. Recommandation : thème Shopify accessible (contrastes, textes alternatifs, navigation clavier) dès le départ, car la mise en conformité devient obligatoire en sortant de la catégorie microentreprise.

### 1.13 Contrôles et sanctions DGCCRF visant le dropshipping

| Année | Sites contrôlés | Sites en anomalie | Suites | Manquements principaux | Source |
|---|---|---|---|---|---|
| 2019 | 12 professionnels | — | 8 procédures pénales ; amendes de 15 000 € à 80 000 € | Pratiques commerciales trompeuses | [S14] (via synthèse) |
| 2022 | 215 | 116 (54 %) | 26 avertissements, 67 injonctions, 22 procès-verbaux pénaux, 9 procès-verbaux administratifs | Fausse origine, identité du vendeur absente, informations sur la rétractation manquantes, faux avis | [S14] |
| 2023 | 251 | 141 (56 %) | 22 avertissements, 92 injonctions, 29 procès-verbaux pénaux ; **réquisitions numériques** pour bloquer des sites | Idem | [S14] |

**Barème des sanctions applicables au site**

| Manquement | Sanction | Base |
|---|---|---|
| Pratique commerciale trompeuse (faux prix barrés, fausse urgence, faux avis, fausse origine, délais mensongers) | 2 ans, 300 000 € (personne physique) ; 1,5 M€ (personne morale) ; jusqu'à 10 % du CA moyen annuel | L132-2 C. conso |
| Tromperie sur les qualités substantielles | 2 ans, 300 000 € ; 7 ans et 750 000 € si le produit est dangereux pour la santé | L441-1, L454-1, L454-3 C. conso |
| Informations précontractuelles manquantes | Amende administrative 3 000 € / 15 000 € | L242-10 C. conso |
| Absence de médiateur | Amende administrative 3 000 € / 15 000 € | L641-1 C. conso |
| Mentions légales absentes | 1 an, 75 000 € / 375 000 € | LCEN art. 1-2 |
| Non-respect d'une mesure de retrait ou de rappel | Jusqu'à 5 ans et 600 000 € (personne physique), 3 M€ (personne morale) selon une source secondaire, à vérifier | L452-5-1 C. conso [E-f] |
| Blocage du site | Injonction, déréférencement, restriction d'accès (réquisitions numériques) | L521-3-1 C. conso |
| Cookies | Jusqu'à 2 % ou 4 % du CA mondial ; procédure simplifiée jusqu'à 20 000 € | Loi n° 78-17 ; RGPD |
| IDU REP absent | Jusqu'à 30 000 € + astreinte jusqu'à 20 000 €/jour | L541-9-5 C. env. [S33] |

### 1.14 Ventes sur places de marché (TikTok Shop, Amazon)

Le règlement sur les services numériques (DSA, art. 30) impose aux places de marché de collecter l'identité du vendeur (raison sociale, adresse, RCS, moyen de paiement, auto-certification de conformité des produits). Le vendeur reste soumis aux règles des sections 1.1 à 1.13. Pour la REP, la place de marché paie l'éco-contribution des vendeurs qui ne lui transmettent pas d'IDU [S34].

---

## 2. Sécurité des produits et environnement

### 2.1 Qui est responsable de quoi : cinq schémas d'approvisionnement

Le règlement (UE) 2023/988 sur la sécurité générale des produits (GPSR), applicable depuis le **13/12/2024**, définit l'importateur comme la personne établie dans l'UE qui met sur le marché de l'Union un produit provenant d'un pays tiers [S32]. Quand un vendeur établi en France vend à un consommateur français un produit expédié depuis la Chine, le fabricant chinois est hors UE et le fournisseur chinois vend au vendeur. La lecture la plus probable, et la plus prudente, est que **le vendeur français est l'importateur** [E-m]. Aucune source officielle consultée ne tranche explicitement le cas du dropshipping (la fiche DGCCRF dédiée [S15] n'a pas pu être lue, accès bloqué).

| Schéma | Rôle GPSR du client | Producteur REP en France ? | Douane et TVA à l'import | Faisabilité de la conformité |
|---|---|---|---|---|
| **A. Chine-direct** (AliExpress, CJ depuis la Chine, agent) → client final en France | **Importateur** [E-m] | Oui (emballages + filière du produit) | Colis ≤ 150 € : 3 €/article depuis le 1/07/2026 ; +2 €/article à partir du 1/11/2026 ; TVA via IOSS (de la plateforme ou du vendeur) [S1][S2][S3] | **Très faible** : nom et adresse de l'importateur à faire apposer par le fournisseur sur chaque produit, Triman absent, notice rarement en français |
| **B. Fournisseur établi dans un autre pays de l'UE** (BigBuy en Espagne, entrepôt UE de CJ) | **Distributeur** si le fournisseur ou son entité UE a importé le produit ; importateur sinon | Probablement oui pour le marché français (premier metteur sur le marché national), sauf attestation écrite du fournisseur couvrant la France [E-m] | Aucune formalité douanière | **Moyenne** |
| **C. Grossiste établi en France avec stock en France** | **Distributeur** | **Non** pour les produits et emballages déjà déclarés par le grossiste (obtenir ses IDU par écrit) | Aucune | **Élevée** ; seul schéma compatible avec 150 € |
| **D. Stock propre importé en gros → 3PL en France** | **Importateur** (assumé, une fois par lot) | Oui | Dédouanement normal : droits du tarif douanier, TVA d'import autoliquidée ; plus de forfait 3 €/2 € par colis | **Élevée** (contrôle par lot) |
| **E. Marque propre fabriquée hors UE** | **Fabricant** (art. 13 : celui qui met le produit sur le marché sous son nom ou sa marque) + importateur | Oui | Idem D | Élevée, avec coûts de tests et de documentation |

### 2.2 Obligations GPSR selon le rôle

| Obligation | Fabricant (marque propre) | Importateur | Distributeur | Article |
|---|---|---|---|---|
| Analyse de risques interne et documentation technique | Établir, mettre à jour, conserver 10 ans | Vérifier que le fabricant l'a établie ; la tenir à disposition des autorités 10 ans | — | Art. 9, 11 |
| Identification du produit (type, lot, numéro de série) | Apposer | Vérifier | Vérifier | Art. 9, 11, 12 |
| Nom, marque, adresse postale et électronique | Du fabricant, sur le produit (ou emballage, document joint) | **Ajouter les siens** sur le produit, à défaut sur l'emballage ou un document joint | Vérifier leur présence | Art. 9, 11, 12 |
| Instructions et avertissements en français | Fournir | Vérifier | Vérifier | Art. 9, 11, 12 |
| Personne responsable établie dans l'UE | — | Peut être elle | Vérifier son existence | Art. 16 ; règl. (UE) 2019/1020 art. 4 |
| Informations sur la page de vente à distance | — | — | **Tout vendeur à distance** : voir 2.3 | Art. 19 |
| Produit dangereux | Mesures correctives, alerte via le portail Safety Business Gateway | Ne pas mettre sur le marché, informer, alerter | Ne pas vendre, informer, alerter | Art. 9, 11, 12 |
| Accident grave | Notifier sans retard via Safety Business Gateway | Informer le fabricant | Informer le fabricant | Art. 20 |
| Rappel | Avis de rappel, remède (réparation, remplacement ou remboursement au moins égal au prix payé) | Contribuer | Contribuer | Art. 35-37 |

**Conséquence pratique** : en schéma A, l'importateur doit faire figurer **ses propres coordonnées sur chaque produit ou son emballage**. Un fournisseur AliExpress ne le fait pas. La parade minimale consiste à exiger du fournisseur ou de l'agent une étiquette ou un insert imprimé avec {{RAISON_SOCIALE}}, {{ADRESSE}}, {{EMAIL}}, la référence du produit et les avertissements en français. Coût : 0,05-0,30 € par unité chez un agent [E-f] ; impossible sur AliExpress grand public.

### 2.3 Bloc d'informations GPSR à afficher sur chaque fiche produit (art. 19)

```
Informations de sécurité du produit (règlement (UE) 2023/988)
Fabricant : [nom ou marque déposée du fabricant], [adresse postale], [adresse e-mail ou site]
Personne responsable dans l'Union européenne : [nom], [adresse postale], [adresse e-mail]
  (schémas A, D, E : {{RAISON_SOCIALE}}, {{ADRESSE}}, {{EMAIL}} ; schémas B, C : coordonnées du fournisseur importateur)
Identification du produit : [type / modèle], [référence, lot ou EAN], photo du produit
Avertissements et consignes de sécurité : [texte intégral en français, identique à celui de l'emballage]
```

Implémentation Shopify : métachamps produit (`gpsr.fabricant`, `gpsr.personne_responsable`, `gpsr.identifiant`, `gpsr.avertissements`) affichés dans un onglet « Sécurité du produit ». Une fiche sans ces quatre éléments ne doit pas être publiée.

### 2.4 Marquage CE et réglementations sectorielles : liste noire et liste blanche

| Catégorie | Textes | Exigences clés | Verdict phase dropshipping |
|---|---|---|---|
| Jouets (enfants < 14 ans) | Directive 2009/48/CE (remplacée à terme par le règlement (UE) 2025/2509) | Marquage CE, essais EN 71, avertissements en français, nom de l'importateur, REP jouets | **Exclure** |
| Appareils électriques et électroniques | Directives 2014/35/UE (basse tension), 2014/30/UE (CEM), 2011/65/UE (RoHS) | CE, déclaration UE de conformité, REP DEEE, Triman | **Exclure** |
| Produits radio (Bluetooth, Wi-Fi) | Directive 2014/53/UE (+ exigences de cybersécurité depuis le 1/08/2025) | CE, déclaration de conformité | **Exclure** |
| Petits appareils rechargeables | Directive (UE) 2022/2380 (chargeur universel) : USB-C depuis le 28/12/2024 ; ordinateurs portables depuis le 28/04/2026 | Port USB-C, pictogramme « chargeur inclus ou non » | **Exclure** |
| Piles et batteries, produits à batterie lithium | Règlement (UE) 2023/1542 | Marquage, REP piles, restrictions de transport aérien | **Exclure** |
| Cosmétiques | Règlement (CE) 1223/2009 | Personne responsable UE, dossier d'information produit, notification CPNP, étiquetage | **Exclure** |
| Compléments alimentaires | Directive 2002/46/CE ; décret n° 2006-352 | Déclaration préalable à la DGCCRF | **Exclure** |
| Matériaux au contact des aliments (gourdes, ustensiles, boîtes) | Règlements (CE) 1935/2004 et (UE) 10/2011 | Déclaration de conformité du fabricant | **Exclure** sauf grossiste français fournissant la déclaration |
| Équipements de protection individuelle (lunettes de soleil, gants, genouillères) | Règlement (UE) 2016/425 | CE, notice, catégorie | **Exclure** |
| Dispositifs médicaux (correcteurs de posture, appareils « antidouleur ») | Règlement (UE) 2017/745 | Marquage CE MDR ; allégations santé interdites hors dispositif | **Exclure** |
| Puériculture | Normes et décrets nationaux | Essais | **Exclure** |
| Bijoux fantaisie | REACH, annexe XVII (nickel, cadmium, plomb) | Rapports d'essais | Risqué ; seulement avec rapport d'essai du fournisseur |
| Textile et chaussures | Règlement (UE) 1007/2011 (composition) ; REP textile | Étiquette de composition en français | Possible avec fournisseur conforme |
| Décoration non électrique, rangement, accessoires pour adultes, animalerie non électrique, papeterie | GPSR seul (+ REP éventuelle : ameublement, sport et loisirs, bricolage et jardin) | Dossier GPSR (section 2.3) | **Liste blanche** |

### 2.5 Responsabilité élargie du producteur (REP), IDU, Triman, emballages

| Filière | Éco-organismes agréés | Produits typiques du catalogue | Coût indicatif |
|---|---|---|---|
| Emballages ménagers (dont colis d'expédition e-commerce) | Citeo, Léko, Adelphe | Tous les produits vendus emballés | Forfait 80-110 € HT/an sous 10 000 unités de vente consommateur [S35] [E-f] |
| Équipements électriques et électroniques | ecosystem, Ecologic | Hors liste blanche | Barème à l'unité [E-f] |
| Piles et accumulateurs | Corepile, Screlec | Hors liste blanche | Barème à l'unité |
| Textiles, linge de maison, chaussures | Refashion | Accessoires textiles | Barème à l'unité + pénalité « mode ultra-express » le cas échéant [S40] |
| Éléments d'ameublement (dont décoration de type meuble) | Ecomaison | Étagères, rangements | Barème à l'unité |
| Jouets | Ecomaison | Hors liste blanche | — |
| Articles de sport et de loisirs | Ecologic | Accessoires de sport | Barème à l'unité |
| Articles de bricolage et de jardin | Ecomaison, Ecologic | Outils manuels, accessoires de jardin | Barème à l'unité |
| Papiers graphiques | Citeo | Flyers glissés dans les colis | Forfait |

- **Qui est producteur ?** Celui qui met en premier le produit sur le marché français, y compris par vente à distance. Citeo vise expressément les e-commerçants pour les emballages d'expédition destinés aux consommateurs lorsqu'ils agissent comme importateurs [S34].
- **IDU** : un identifiant par filière, délivré par l'ADEME (registre SYDEREP) ou transmis par l'éco-organisme ; à indiquer **dans les CGV et sur le site** dans les mêmes conditions que les mentions LCEN ; à communiquer à tout acheteur qui le demande. Sanction : jusqu'à 30 000 € d'amende et 20 000 € d'astreinte par jour [S33].
- **Distributeur (schéma C)** : il doit pouvoir fournir l'IDU de son fournisseur sur demande [S33]. Action : obtenir du grossiste une attestation écrite de ses IDU et de la déclaration des emballages.
- **Triman et Info-tri** : signalétique obligatoire sur les produits et emballages ménagers soumis à une REP (L541-9-3 C. env.). Les emballages des fournisseurs chinois n'en portent pas : non-conformité structurelle du schéma A.
- **Règlement (UE) 2025/40 sur les emballages (PPWR)** : applicable depuis le 12/08/2026 ; obligations progressives (taux de vide des emballages e-commerce, étiquetage harmonisé) d'ici 2028-2030. Impact à planifier pour la phase marque propre.
- **Destruction des invendus non alimentaires interdite** (L541-15-8 C. env.) : produits invendus ou retournés à donner ou recycler (phase stock).
- **Affichage des qualités et caractéristiques environnementales** (L541-9-1 C. env.) : réservé aux metteurs sur le marché au-delà de 10 M€ de CA et 10 000 unités (seuils du décret n° 2022-748) [E-m] : non applicable au démarrage.

### 2.6 Responsabilité du fait des produits défectueux

| Règle | Contenu | Base |
|---|---|---|
| Responsabilité sans faute du producteur | Dommage causé par un défaut de sécurité | 1245 et s. C. civ. |
| Importateur assimilé au producteur | Toute personne qui importe un produit dans l'UE en vue de sa vente | 1245-5 C. civ. |
| Vendeur | Responsable comme le producteur si celui-ci reste non identifié, sauf s'il désigne son propre fournisseur ou le producteur dans les 3 mois de la demande | 1245-6 C. civ. |
| Nouvelle directive (UE) 2024/2853 | Transposition au plus tard le **9/12/2026**, pour les produits mis sur le marché après cette date ; élargit les opérateurs responsables (importateur, mandataire, prestataire de services d'exécution des commandes) et la notion de produit (logiciels) | [S39] |

Conséquence : en schéma A, le client répond seul d'un dommage corporel causé par un produit chinois (brûlure, coupure, ingestion). **Assurance RC produits indispensable dès qu'un produit dépasse le stade de test** (150-500 €/an [E-f]).

### 2.7 Propriété intellectuelle et contrefaçon

| Risque | Règle | Sanction |
|---|---|---|
| Produit copiant une marque, un design ou un brevet (« dupe ») | Contrefaçon de marque, de dessin et modèle, de brevet | Jusqu'à 3 à 4 ans d'emprisonnement et 300 000 à 400 000 € (L716-9, L716-10 CPI) ; saisie douanière des colis |
| Photos et vidéos du fournisseur ou de concurrents | Droit d'auteur : autorisation nécessaire | 3 ans et 300 000 € (L335-2 CPI) |
| Nom de marque du site | Antériorités | Recherche gratuite INPI, EUIPO (TMview) avant d'acheter le domaine |
| Protection de la marque propre | Dépôt INPI 190 € (1 classe) ; protection 10 ans [S53] | — |

Consigne : photos et vidéos produites par le client à partir de l'échantillon reçu ; aucun produit portant un logo, un personnage ou un design de tiers.

---

## 3. Fiscalité et douane

### 3.1 TVA d'un vendeur établi en France vendant à des consommateurs en France

| Situation | Régime | Mention / formalité |
|---|---|---|
| Vente d'un bien situé en France (stock français, grossiste français) | TVA française, taux normal 20 % (taux réduits pour quelques catégories) | Déclaration CA3 ou régime simplifié |
| Vente d'un bien expédié depuis un autre État de l'UE à un consommateur français, par un vendeur français | TVA française (lieu d'arrivée) | Achat intracommunautaire chez le fournisseur UE : facture HT avec autoliquidation si le client est identifié à la TVA |
| Vente d'un bien expédié depuis un pays tiers, envoi ≤ 150 € | Vente à distance de biens importés : voir 3.3 | IOSS ou TVA à l'importation |
| Ventes à distance vers d'autres pays de l'UE | TVA française jusqu'à 10 000 € de ventes intra-UE par an (tous pays confondus), puis TVA du pays de destination via le guichet OSS | Immatriculation OSS en France |
| Franchise en base | Pas de TVA facturée, pas de TVA déduite | « TVA non applicable, art. 293 B du CGI » sur chaque facture [S6] |

### 3.2 Franchise en base de TVA en 2026 : seuils et arbitrage

| Activité | Seuil de base (CA N-1) | Seuil majoré (CA de l'année en cours) | Source |
|---|---|---|---|
| Ventes de marchandises, hébergement | **85 000 €** | **93 500 €** | [S6] (vérifié le 01/01/2026) |
| Prestations de services | 37 500 € | 41 250 € | [S6] |

- **Historique** : le seuil unique de 25 000 € voté en loi de finances 2025 a été suspendu, puis abandonné (loi de novembre 2025) ; le PLF 2026 proposait un seuil unique de 37 500 € (25 000 € pour le bâtiment) [S7] ; le Parlement a supprimé cette mesure et maintenu les seuils différenciés [S7b]. Fiabilité : élevée pour les montants, moyenne pour le déroulé parlementaire.
- **Dépassement du seuil majoré** : TVA due dès l'opération qui fait franchir le seuil (régime en vigueur depuis 2025).
- **Recodification** : les règles de TVA sont transférées dans le code des impositions sur les biens et services (CIBS) au 1/09/2026 (ordonnance n° 2025-1247). Les factures peuvent continuer à citer le CGI **jusqu'au 31/12/2027** [S8].
- **Piège de la franchise** : les services achetés à des prestataires établis dans un autre pays de l'UE (Shopify, Meta, TikTok, Google : entités irlandaises) restent soumis à l'autoliquidation de la TVA française par le client, **non déductible** en franchise. Sur 500 € de publicité mensuelle : 100 € de TVA payée sans récupération [E-m, à valider].

**Arbitrage chiffré (un produit vendu 34,90 € TTC, acheté 10 € HT + 2 € de TVA à un grossiste français)** [E-m]

| Poste | Assujetti à la TVA | Franchise en base |
|---|---|---|
| Chiffre d'affaires retenu | 29,08 € HT | 34,90 € |
| Coût d'achat | 10,00 € (TVA récupérée) | 12,00 € (TVA non récupérable) |
| Frais de paiement (1,5 % + 0,25 €) [S28] | 0,77 € | 0,77 € |
| **Marge après achat et paiement** | **18,31 €** | **22,13 € (+21 %)** |

Conclusion : la franchise est favorable tant que le CA reste sous 85 000 € et que les dépenses publicitaires (TVA autoliquidée non récupérable) restent faibles. Au-delà de ≈ 1 500 € de dépenses mensuelles soumises à autoliquidation, l'avantage diminue fortement [E-m]. Décision à revoir avec l'expert-comptable avant le passage à la publicité payante.

### 3.3 Ventes de biens importés en colis ≤ 150 € : qui est redevable

| Schéma | TVA facturée au consommateur | TVA sur l'achat du vendeur | Droits 3 € et redevance 2 € | Risque principal |
|---|---|---|---|---|
| **A1. Achat sur AliExpress** (la plateforme agit comme fournisseur présumé et applique son IOSS) | Le vendeur facture 20 % de TVA française sur sa vente (sauf franchise) | AliExpress facture 20 % de TVA française ; déductibilité incertaine (facture au nom de la société avec numéro de TVA requise) [S55] | Facturés par la plateforme et répercutés au vendeur | **Double TVA** : jusqu'à 20 % du coût d'achat non récupérable [E-m, à valider] |
| **A2. Agent ou fournisseur qui déclare l'import avec l'IOSS du vendeur** | Le vendeur, via sa déclaration IOSS mensuelle | Aucune (achat à l'export) | Payés par le déclarant (transporteur), refacturés | Immatriculation IOSS, déclaration mensuelle, numéro IOSS obligatoire dans la déclaration en douane [S55] |
| **A3. Sans IOSS** : le consommateur paie la TVA d'importation et des frais de dédouanement à la livraison | Aucune à la vente, sous conditions strictes [S54] | — | Payés par le consommateur à la livraison | Prix affiché incomplet, colis refusés, litiges : **à exclure** |

Le seuil de 150 € s'apprécie sur la valeur intrinsèque de chaque envoi, au niveau de la vente au client final [S54]. Au-delà de 150 €, droits du tarif douanier et TVA d'importation de droit commun.

### 3.4 Fin de l'exonération de droits sous 150 € : calendrier et impact

| Date | Mesure | Montant | Source |
|---|---|---|---|
| 1/07/2021 → 30/06/2026 | Franchise de droits de douane sous 150 € (TVA due depuis 2021) | 0 € de droits | [S2] |
| 1/03/2026 → 30/06/2026 | Taxe française sur les petits colis (art. 82 loi n° 2026-103 de finances pour 2026) | 2 € par catégorie d'article | [S5] |
| **1/07/2026** | **Suspension de la taxe française** au profit du droit européen | — | [S1] (communiqué du 30/06/2026) ; [S4] |
| **1/07/2026 → 1/07/2028** (ou mise en service de la plateforme douanière de données de l'UE) | **Droit de douane forfaitaire** (règlement (UE) 2026/382 ; règlement d'exécution (UE) 2026/1200) sur les ventes à distance B2C ≤ 150 €, quel que soit le régime de TVA | **3 € par « article »** : marchandises d'un même envoi partageant le même classement tarifaire ; en pratique 3 € par ligne de déclaration | [S1][S2] |
| **1/11/2026** | Identifiants produits (code marchand, référence fabricant, EAN) obligatoires dans les déclarations de ventes à distance | — | [S2] |
| **1/11/2026** (prévu) | **Redevance de gestion de l'Union** sur les envois e-commerce venant de pays tiers, sans seuil de valeur, non remboursable, payée par le déclarant | **2 € par article distinct** (articles identiques = 1 article) | [S3][S1] ; statut juridique final et traitement TVA à confirmer [S56] |
| 2028 | Droits normaux selon le classement tarifaire de chaque produit | Taux du tarif douanier | [S2] |

**Impact sur un produit acheté 8,00 € livré en Chine-direct (hypothèse : coûts répercutés au vendeur, TVA de 20 % sur les montants refacturés)** [E-m]

| Période / panier | Coût d'achat | Droit forfaitaire (+ TVA) | Redevance (+ TVA) | Coût rendu | Variation | Coût rendu / prix de vente 29,90 € TTC |
|---|---|---|---|---|---|---|
| Avant le 1/07/2026, 1 produit | 8,00 € | — | — | 8,00 € | — | 27 % |
| Du 1/07 au 31/10/2026, 1 produit | 8,00 € | 3,60 € | — | 11,60 € | +45 % | 39 % |
| À partir du 1/11/2026, 1 produit | 8,00 € | 3,60 € | 2,40 € | **14,00 €** | **+75 %** | **47 %** |
| À partir du 1/11/2026, 2 produits identiques | 16,00 € | 3,60 € | 2,40 € | 22,00 € | +38 % | 37 % (sur 59,80 €) |
| À partir du 1/11/2026, 2 produits de classements différents | 16,00 € | 7,20 € | 4,80 € | 28,00 € | +75 % | 47 % (sur 59,80 €) |

Lecture : à partir de novembre 2026, le Chine-direct n'est viable que pour des paniers élevés ou des lots de produits identiques. Un fournisseur avec stock UE paie les droits normaux une seule fois sur l'import en gros et n'acquitte pas la redevance par colis.

### 3.5 Import en gros pour un stock en 3PL (phase 3)

| Étape | Exigence | Coût |
|---|---|---|
| Numéro EORI | Demande en ligne auprès de la douane | 0 € |
| Commissionnaire en douane / transitaire | Déclaration d'import, classement tarifaire | 50-150 € par déclaration [E-f] |
| Droits de douane | Taux du tarif intégré de l'UE (TARIC) selon la nomenclature ; droits antidumping sur certaines catégories | Variable : à vérifier dans TARIC avant toute commande |
| TVA à l'importation | Autoliquidée sur la déclaration de TVA (CGI art. 1695 II, obligatoire depuis le 1/01/2022 pour les assujettis) : aucun décaissement | 0 € de trésorerie (assujetti) ; payée et non récupérable en franchise |
| Conformité | Importateur : nom et adresse sur les produits, documentation 10 ans, Triman, REP | Voir section 2 |

### 3.6 Impôt sur les bénéfices et prélèvements sociaux

| Régime | Taux | Conditions | Source |
|---|---|---|---|
| IS taux réduit | 15 % jusqu'à 42 500 € de bénéfice | CA ≤ 10 M€ ; capital entièrement libéré ; détenu à 75 % au moins par des personnes physiques | [S9] (vérifié le 17/02/2026) |
| IS taux normal | 25 % au-delà | — | [S9] |
| Micro-entreprise : cotisations sociales | 12,3 % du CA (ventes de marchandises) ; 13,3 % avec versement libératoire | Plafond de CA 2026 : 203 100 € HT | [S10][S10b] |
| Micro-entreprise : impôt | Barème de l'impôt sur le revenu après abattement de 71 %, ou versement libératoire de 1 % du CA (sous condition de revenu fiscal) | — | [S10b] |

Un amendement PLF 2026 visant à porter le plafond du taux réduit d'IS à 100 000 € a circulé ; les sources consultées indiquent un plafond inchangé à 42 500 € [E-m, à valider].

**Comparaison chiffrée (hypothèse annuelle : CA 60 000 € en franchise de TVA, marge brute 35 % = 21 000 €, frais fixes 6 000 €, comptable 1 500 € en société)** [E-m]

| Poste | Micro-entreprise | SASU/EURL à l'IS sans rémunération |
|---|---|---|
| Résultat avant prélèvements | 15 000 € | 13 500 € |
| Cotisations sociales | 7 380 € (12,3 % × 60 000 €) | 0 € |
| Impôt | IR sur 17 400 € (29 % du CA) au taux marginal du foyer, ou 600 € de versement libératoire | IS 15 % : 2 025 € |
| **Trésorerie disponible pour réinvestir** | **≈ 7 000 €** (avec versement libératoire) | **11 475 €** (+63 %) |

Lecture : en phase de réinvestissement (stock, publicité), la société à l'IS conserve nettement plus de trésorerie ; la micro-entreprise reste acceptable tant que le CA est faible et la marge brute élevée. La distribution de dividendes subit ensuite le prélèvement forfaitaire unique (taux 2026 à confirmer avec l'expert-comptable).

### 3.7 Obligations comptables et déclaratives

| Obligation | Micro-entreprise | EURL / SASU à l'IS | Fréquence |
|---|---|---|---|
| Livre des recettes, registre des achats | Oui | — | Continu |
| Comptabilité complète, bilan, compte de résultat | — | Oui | Annuelle |
| Liasse fiscale | Déclaration 2042-C-PRO | 2065 + 2033 | Annuelle (mai) |
| Déclaration du CA à l'URSSAF | Oui | — | Mensuelle ou trimestrielle |
| Approbation et dépôt des comptes au greffe | — | Oui (option de confidentialité pour les micro-entreprises au sens comptable) | Annuelle |
| TVA (si assujetti) | CA3 mensuelle, ou régime simplifié (acomptes de juillet et décembre + CA12) ; **nouveau régime simplifié trimestriel au 1/01/2027** (seuil unique 1 M€) [S11] | Idem | Mensuelle à annuelle |
| IOSS (si immatriculé) | Déclaration et paiement mensuels | Idem | Mensuelle |
| Facturation électronique | **Réception obligatoire depuis le 1/09/2026** pour tout assujetti ; émission et transmission des données de ventes aux particuliers (e-reporting) au 1/09/2027 pour les PME et micro-entreprises [S12] | Idem | Continu |
| Factures B2C | À émettre sur demande du client ; conserver les données de transaction | Idem | — |
| Logiciel de caisse sécurisé | Non concerné en franchise de TVA [S13] ; pour un site e-commerce assujetti : champ d'application à valider | Idem | — |
| CFE | Exonération l'année de création, puis cotisation minimale communale | Idem | Annuelle (décembre) |
| Conservation | Pièces comptables 10 ans (L123-22 C. com.) ; droit de reprise fiscal 6 ans (L102 B LPF) | Idem | — |

---

## 4. Paiements

### 4.1 Frais en France (octobre 2026)

| Prestataire | Cartes standard FR/UE | Cartes internationales, Amex | Frais Shopify en plus | Litige (rétrofacturation) | Versements | Source |
|---|---|---|---|---|---|---|
| **Shopify Payments, Basic** | **1,5 % + 0,25 €** | 2,7 % + 0,25 € | 0 % | **15 €**, remboursés si gain | Délai de 3 jours ; aucun versement le week-end ; minimum 10 € | [S28] (relevé de la page tarifaire française le 7/10/2026, fiabilité moyenne) |
| Shopify Payments, Grow / Advanced | 1,3 % / 1,1 % + 0,25 € | 2,6 % / 2,4 % + 0,25 € | 0 % | 15 € | Idem | [S28] |
| **Stripe** (prototype codé hors Shopify) | 1,5 % + 0,25 € (EEE standard) ; 2,8 % + 0,25 € (EEE premium) | 3,15 % + 0,25 € + 2 % de conversion ; Royaume-Uni 2,5 % + 0,25 € | Sans objet (sur Shopify, Shopify Payments repose déjà sur Stripe) | 20 € reçu + 20 € de réponse, remboursés si gain | Premier versement : 7 jours (France) ; ensuite 3 jours ouvrés | [S24][S25] |
| **PayPal** | 2,90 % + 0,35 € (transaction commerciale) ; paiement par carte sans compte PayPal : 1,20 % + 0,35 € | +1,29 % Royaume-Uni ; +1,99 % autres pays hors EEE | 0 % si Shopify Payments est actif [E-m] | 14 € (litige standard) ; 16 € (opposition bancaire) ; 28 € (vendeurs à fort volume de litiges) | Disponibles immédiatement ; suspension possible jusqu'à 21 jours, levée environ 24 h après la livraison confirmée par le transporteur | [S26] (MAJ 15/07/2026) ; [S27] |
| Passerelle tierce sur Shopify (Mollie, etc.) | Frais du prestataire | — | **+2 % (Basic)**, +1 % (Grow), +0,6 % (Advanced) | Selon prestataire | Selon prestataire | [S29] |

**Coût par commande** [E-é, calcul]

| Panier TTC | Shopify Payments Basic | PayPal | Passerelle tierce à 1,5 % + 0,25 € sur Shopify Basic |
|---|---|---|---|
| 25 € | 0,63 € (2,5 %) | 1,08 € (4,3 %) | 1,13 € (4,5 %) |
| 35 € | 0,78 € (2,2 %) | 1,37 € (3,9 %) | 1,48 € (4,2 %) |
| 50 € | 1,00 € (2,0 %) | 1,80 € (3,6 %) | 2,00 € (4,0 %) |

Recommandation : Shopify Payments en moyen principal, PayPal en option (≈ 15-30 % des paiements en France selon la clientèle [E-f]), aucune passerelle tierce.

### 4.2 Réserves, délais et gels de fonds : déclencheurs propres au dropshipping

| Déclencheur | Pourquoi il alerte le prestataire | Prévention |
|---|---|---|
| Délais de livraison longs (≥ 10 jours) | Multiplication des litiges « article non reçu » ; exposition prolongée du prestataire | Fournisseur avec stock UE/France ; fourchette de livraison réaliste ; suivi transmis sous 72 h |
| Pic soudain de ventes (vidéo virale) | Profil de risque modifié ; réserve glissante possible | Prévenir le support du prestataire ; garder 20-30 % du CA du pic en trésorerie [E-m] |
| Taux de remboursement ou de litige élevé | Signal de fraude ou de produit défectueux | SAV en moins de 24 h ; remboursement proactif avant litige |
| Produits à risque (répliques, santé, contrefaçons) | Interdits par les conditions des prestataires | Liste blanche (section 2.4) |
| Précommandes, ruptures non affichées | Livraison différée de plusieurs semaines | Synchronisation du stock ; aucune vente sans stock |
| Site incomplet (mentions, CGV, retours, contact) | Contrôle de conformité du prestataire à l'activation | Publier les six pages avant d'activer les paiements |
| Descripteur bancaire inconnu du client | Le client ne reconnaît pas l'achat et conteste | Descripteur = nom de marque + domaine |
| Informations d'identification (KYC) incohérentes | Blocage du compte | Kbis/RNE, pièce d'identité, IBAN professionnel au même nom |

PayPal indique lever la suspension des fonds environ 24 h après confirmation de livraison, avec une suspension pouvant aller jusqu'à 21 jours, par exemple en cas de changement d'habitudes de vente [S27]. Stripe fixe le premier versement à 7-14 jours selon le secteur, le pays et le niveau de risque [S25].

### 4.3 Rétrofacturations (chargebacks)

**Seuils des réseaux**

| Réseau | Programme | Seuil marchand | Source |
|---|---|---|---|
| Visa | VAMP (Visa Acquirer Monitoring Program) : (fraudes déclarées + litiges) / transactions réglées | **1,5 %** depuis le 1/04/2026 (2,2 % pendant la période initiale), avec un nombre minimal d'incidents par mois | [S30] (sources concordantes, règle Visa non consultée directement) |
| Mastercard | Excessive Chargeback Merchant | ≥ 1,5 % et ≥ 100 litiges par mois ; niveau élevé ≥ 3 % et ≥ 300 | [S31] (fiabilité faible) |

Ces seuils ne visent un petit site qu'au-delà de volumes minimaux. Shopify, Stripe et PayPal appliquent leurs propres seuils de risque, plus bas et non publiés. **Cible interne : taux de litige < 0,5 % des commandes** [E-m].

**Motifs et preuves**

| Motif du litige | Fréquence en dropshipping | Preuve à fournir | Prévention |
|---|---|---|---|
| Article non reçu | Élevée en Chine-direct | Suivi avec preuve de livraison à l'adresse de la commande | Transporteur avec preuve de remise ; délai réaliste |
| Article non conforme à la description | Élevée | Photos et description de la fiche, échanges avec le client, politique de retour acceptée | Photos réelles, caractéristiques précises |
| Fraude (carte volée) | Moyenne | Authentification 3-D Secure (transfert de responsabilité à la banque émettrice), adresse IP, historique | 3-D Secure activé ; analyse de risque Shopify |
| Achat non reconnu | Moyenne | Descripteur, e-mail de confirmation | Descripteur = nom de marque |
| Remboursement non reçu après retour | Faible | Preuve du remboursement | Remboursement sous 14 jours (L221-24) |

**Procédure** : répondre avant l'échéance affichée dans l'interface ; dossier type : confirmation de commande, CGV acceptées (horodatage), suivi de livraison, échanges, photos ; rembourser spontanément quand le dossier est faible (le litige coûte 15-20 € de frais en plus du montant [S28][S24]).

---

## 5. Fournisseurs et logistique

### 5.1 Comparatif des sources d'approvisionnement

| Source | Stock / expédition | Délai réel vers la France | Coût d'accès | Qualité et contrôle | Automatisation Shopify | Retours | Statut GPSR du client | Droits 3 € + redevance 2 € | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **AliExpress + DSers** | Chine ; quelques entrepôts « Local+ » (Royaume-Uni, Allemagne, Espagne) [S50] | Choice : 7-15 jours [S50b] (fiabilité faible) ; standard : 10-20 jours [E-m] | DSers Basic gratuit (3 boutiques, 3 000 produits) ; Advanced 19,90 $/mois ; Pro 49,90 $/mois [S45] | Hétérogène (vendeurs multiples) ; contrôle seulement par échantillon | Commandes groupées (DSers) ; synchronisation du suivi | Retour vers la Chine irréaliste : adresse France nécessaire | **Importateur** | **Oui**, par colis | **Échantillons et tests uniquement** |
| **CJ Dropshipping** | Chine + entrepôts hors Chine, dont Allemagne (Francfort) [S48] | Chine : 7-14 jours (CJPacket) [S49] ; entrepôt UE : 3-6 jours ouvrés [E-m] | Inscription gratuite ; prix produit + port ; sourcing sur demande | Photos de contrôle, emballage personnalisé, inserts possibles | Application Shopify, commande automatique | Via l'entrepôt UE à vérifier au cas par cas | Chine : importateur ; stock UE : à vérifier (importateur de l'entité UE de CJ ou client) | Chine : oui ; stock UE : non | **Bon compromis en phase 1 si le produit est en stock UE** |
| **BigBuy** (grossiste espagnol) | Espagne | 48-72 h annoncées [S47] (fiabilité faible) ; 2-5 jours ouvrés [E-m] | Abonnement 69-120 €/mois + frais d'inscription ≈ 90 € selon des sources tierces [S47] (fiabilité faible, page officielle inaccessible) | Catalogue de produits de marque déjà importés dans l'UE | Connecteur Shopify | Retour vers l'Espagne | Distributeur probable | Non | Hors budget de la phase 0 ; pertinent après les premiers profits |
| **Spocket** | Fournisseurs UE et US (+ catalogue AliExpress) | Fournisseurs UE : 2-7 jours [E-f] | Starter 39,99 $/mois (25 produits) ; Pro 59,99 $/mois ; essai 7 jours [S46] | Variable selon le fournisseur | Application | Selon le fournisseur | Dépend du fournisseur | Non si fournisseur UE | Hors budget de la phase 0 |
| **Agent de sourcing privé** (Chine) | Chine ; envoi en ligne directe ou en gros vers un 3PL | 7-12 jours en ligne directe [E-m] ; transport maritime 30-45 jours pour le stock [E-m] | Commission 5-10 % du coût produit [E-m] | Contrôle physique, emballage, insert importateur, étiquette Triman | Application ou fichier | Selon accord | Importateur | Oui en direct ; non en import en gros (droits normaux) | **Phase 2** (≥ 10 commandes/jour) |
| **Grossiste établi en France pratiquant le dropshipping** | France | 1-3 jours ouvrés [E-m] | Souvent sans abonnement ; marges plus faibles | Conformité CE, REP, notice FR assurées par le grossiste (à vérifier : IDU, déclaration de conformité) | Fichier, API ou application | Retour en France | **Distributeur** | Non | **Premier choix légal en phase 1** |
| **3PL en France** | Stock propre en France | J+1 à J+3 | Préparation ≈ 2,40 € par colis + transport ; rentabilité vers 100 colis/mois [S52] (fiabilité faible) ; stockage 10-25 €/palette/mois [E-f] | Contrôle à réception | Intégration Shopify native | Gérés par le 3PL | Importateur (ou fabricant en marque propre) | Non (droits normaux une fois) | **Phase 3** |

### 5.2 Protocole de contrôle qualité

| Étape | Action | Critère d'acceptation | Coût |
|---|---|---|---|
| 1. Sélection du fournisseur | Plateformes : note ≥ 4,7, ≥ 1 000 ventes, ≥ 1 an d'ancienneté ; grossiste : extrait Kbis, IDU, déclarations de conformité | Tous critères remplis | 0 € |
| 2. Échantillon | 1-2 unités livrées à l'adresse du client, par le circuit réel | Conforme aux photos, finition, mesures, notice en français, marquages, odeur, absence de marque tierce | 8-17 € par produit [E-m] |
| 3. Test d'usage | 7 jours d'utilisation réelle ; essais simples (chute, lavage, charge) | Aucun défaut | 0 € |
| 4. Dossier produit | Factures, photos de l'échantillon, coordonnées du fabricant, personne responsable UE, avertissements, preuves de conformité | Dossier complet (section 2.3) | 0 € |
| 5. Mesure du délai réel | Date de commande → date de livraison sur les premières commandes ; calcul du 90e centile | Délai affiché ≥ 90e centile + 2 jours ouvrés | 0 € |
| 6. Suivi après vente | Taux de défaut et de retour par produit, chaque semaine | Retrait du produit si défaut > 5 % [E-m] | 0 € |
| 7. Inspection avant expédition (stock) | Inspection tierce selon AQL 2,5 | Rapport sans défaut critique | 250-350 € par jour d'inspection [E-f] |

### 5.3 Commande manuelle ou automatisée

| Mode | Outil | Temps par commande | Coût | Risque principal | Seuil d'usage |
|---|---|---|---|---|---|
| Manuel | Saisie sur le site du fournisseur | 3-5 min [E-m] | 0 € | Erreur d'adresse, oubli | < 5 commandes/jour |
| Semi-automatique | DSers (commandes groupées), import du suivi | ≈ 1 min [E-m] | 0-19,90 $/mois [S45] | Rupture fournisseur non détectée | 5-30 commandes/jour |
| Automatique | Application CJ, connecteur BigBuy, Spocket, API grossiste | 0 | Abonnement éventuel | Stock non synchronisé | Dès le départ avec un stock UE/France |
| 3PL | Intégration Shopify native | 0 ; expédition le jour même ou J+1 | Préparation ≈ 2,40 €/colis + stockage [S52] | Volume minimal | ≥ 100 colis/mois |

**Niveaux de service internes** : commande transmise au fournisseur en moins de 24 h ; numéro de suivi transmis au client et à PayPal en moins de 72 h ; e-mail proactif dès qu'un colis dépasse la date haute annoncée ; réponse SAV en moins de 24 h ouvrées.

### 5.4 Délais réels et promesse affichée

| Origine | Délai indicatif vers la France | Fiabilité |
|---|---|---|
| AliExpress Choice | 7-15 jours | Faible [S50b] |
| AliExpress standard (vendeur en Chine) | 10-20 jours | [E-m] |
| CJ Dropshipping depuis la Chine | 7-14 jours (lignes Europe) ; 5-12 jours selon un comparatif d'avril 2026 | Faible [S49] |
| Entrepôt UE (Allemagne) | 3-6 jours ouvrés | [E-m] |
| BigBuy (Espagne) | 48-72 h annoncées | Faible [S47] |
| Grossiste ou 3PL en France (Colissimo) | 1-3 jours ouvrés | [E-m] |

Règle d'affichage : la fourchette affichée couvre au moins 90 % des livraisons constatées. Un délai de 7-15 jours affiché honnêtement reste licite ; il dégrade la conversion et augmente les litiges, d'où la priorité donnée au stock UE.

### 5.5 Retours

| Situation | Frais de retour | Destination | Délai | Consigne |
|---|---|---|---|---|
| Rétractation | Client, s'il en a été informé (sinon vendeur) | {{ADRESSE_RETOUR}} en France | Remboursement sous 14 jours après la déclaration, report possible jusqu'à réception ou preuve d'envoi | Si le retour coûte plus que le produit : remboursement sans retour (choix commercial licite) |
| Défaut de conformité | Vendeur | {{ADRESSE_RETOUR}} ou aucun retour (photo, vidéo) | Réparation ou remplacement sous 30 jours | Photo et vidéo transmises au fournisseur pour avoir |
| Colis perdu | Vendeur | — | Renvoi ou remboursement rapide | Réclamation au fournisseur ou au transporteur |
| Colis endommagé | Vendeur | — | Idem | Photos du colis demandées, sans délai de réserve imposé |

**Adresse de retour** : siège social (0 €, expose l'adresse personnelle en cas de domiciliation au domicile) ; domiciliation commerciale avec réception de colis (15-40 €/mois [E-f]) ; 3PL en phase 3. **Coût d'un retour** : Colissimo 500 g en point de retrait 6,89 € TTC (tarif public 2026) [S51] ; Mondial Relay 4-8 € [E-f]. **Produits retournés** : remise en vente si neufs et complets ; sinon don ou recyclage (destruction interdite).

### 5.6 Passage au stock et au 3PL

| Condition de bascule | Seuil | Source |
|---|---|---|
| Ventes d'un même produit | ≥ 5 commandes/jour pendant 14 jours | [E-m] |
| Taux de défaut | < 5 % | [E-m] |
| Marge contributive après droits 3 € + 2 € | Positive et ≥ 8 € par commande | [E-m] |
| Trésorerie | Commande de stock (1-2 mois de ventes) + droits + transport financés sans découvert | [E-m] |
| Canal TikTok Shop | Exige une expédition depuis la France en 2 jours ouvrés (dossier 02) | [02-acquisition S4] |

---

## 6. Checklist de conformité avant lancement

**Priorités** : **P0** = bloquant, à satisfaire avant la mise en ligne ou l'activation des paiements ; **P1** = dans les 30 jours suivant la première vente ; **P2** = à planifier (phase suivante ou échéance réglementaire). « Schéma » renvoie à la section 2.1.

### 6.1 Identité, mentions et contrat

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| A1 | Identification de l'éditeur : raison sociale, forme, capital, siège, SIREN, RCS, TVA, téléphone, e-mail | LCEN art. 1-1 et 19 ; R111-1 C. conso | Compléter et publier `mentions-legales.md` ; lien dans le pied de page de toutes les pages | 0 € | P0 |
| A2 | Directeur de la publication | LCEN art. 1-1 | Renseigner {{DIRECTEUR_PUBLICATION}} | 0 € | P0 |
| A3 | Hébergeur : nom, adresse, téléphone | LCEN art. 1-1 | Renseigner {{HEBERGEUR}} avec l'entité Shopify contractante | 0 € | P0 |
| A4 | Coordonnées de contact effectives (adresse géographique, e-mail, téléphone non surtaxé) | L221-5, R111-1, L113-5 C. conso | Page Contact + pied de page | 0 € | P0 |
| A5 | Mention « EI » si micro-entreprise | Statut de l'entrepreneur individuel (loi n° 2022-172) | Variante B de `mentions-legales.md` | 0 € | P0 |
| A6 | IDU REP affiché (si producteur) | L541-10-13 C. env. | CGV art. 15 + mentions légales | 0 € | P0 |
| A7 | Site, fiches, notices et e-mails en français | Loi n° 94-665 | Relecture complète | 0 € | P0 |
| B1 | CGV B2C complètes, accessibles et téléchargeables avant la commande | L221-5 C. conso ; 1127-1 C. civ. | Publier `cgv.md` ; lien dans le pied de page et le tunnel | 0 € | P0 |
| B2 | Absence de clauses abusives (délais indicatifs, exclusion de garantie, réserves imposées, frais en cas de défaut) | L212-1, R212-1, R212-2 C. conso | Relecture avec la liste des clauses noires et grises | 0 € | P0 |
| B3 | Encadré réglementaire de garantie légale reproduit à l'identique | Décret n° 2022-946 | Article 10 de `cgv.md` | 0 € | P0 |
| B4 | Archivage des contrats ≥ 120 € pendant 10 ans et accès du client | L213-1, D213-1 C. conso | Export trimestriel des commandes ; mention CGV art. 19 | 0 € | P1 |
| B5 | Coordonnées du médiateur dans les CGV et sur le site | L616-1 C. conso | CGV art. 14 + mentions + page contact | 0 € | P0 |
| B6 | Aucun lien vers la plateforme RLL de l'UE | Règl. (UE) 2024/3228 | Vérifier le thème et les modèles de pages | 0 € | P0 |
| B7 | Avis harmonisé UE sur la garantie légale | Règl. d'exécution (UE) 2025/1960 ; dir. (UE) 2024/825 | Ajouter en pied de page dès la transposition française | 0 € | P2 |

### 6.2 Tunnel de commande et prix

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| C1 | Récapitulatif et correction de la commande avant validation | 1127-2 C. civ. ; L221-14 C. conso | Panier Shopify natif ; tester sur mobile | 0 € | P0 |
| C2 | Acceptation expresse des CGV | 1127-1 C. civ. | Case non pré-cochée sur la page panier (thème) + mention et lien sous le bouton de paiement | 0 € | P0 |
| C3 | Aucune option payante pré-cochée (assurance colis, protection d'achat, express) | L121-17 C. conso | Désactiver les applications d'options pré-cochées | 0 € | P0 |
| C4 | Bouton « Payer maintenant » ou « Commande avec obligation de paiement » | L221-14 C. conso | Vérifier le libellé du checkout en français | 0 € | P0 |
| C5 | Confirmation sur support durable avec CGV, formulaire de rétractation et lien vers la fonctionnalité de rétractation | L221-13 C. conso | Modifier le modèle d'e-mail « Confirmation de commande » | 0 € | P0 |
| C6 | Aucun surcoût selon le moyen de paiement | L112-12 C. conso | Pas de frais PayPal ajoutés | 0 € | P0 |
| C7 | Authentification forte (3-D Secure) | L133-44 C. monét. fin. | Vérifier l'activation dans Shopify Payments | 0 € | P0 |
| D1 | Prix TTC et frais de livraison affichés avant le panier | L112-1 C. conso | Fiche produit + page livraison | 0 € | P0 |
| D2 | Prix barrés calculés sur le prix le plus bas des 30 jours précédents | L112-1-1 C. conso | Aucun « prix avant réduction » pendant les 30 premiers jours ; historique des prix exporté | 0 € | P0 |
| D3 | Aucune fausse urgence, fausse rareté ou fausse popularité | L121-2, L121-4 C. conso | Désactiver comptes à rebours, pop-ups « X vient d'acheter », compteurs de stock fictifs | 0 € | P0 |
| D4 | Aucune origine trompeuse ; pays d'expédition indiqué | L121-2, L441-1 C. conso | Page livraison : « expédié depuis [pays] » | 0 € | P0 |
| D5 | Aucune allégation santé ou environnementale | L541-9-1 C. env. ; règl. (UE) 2017/745 ; L121-2 C. conso | Relecture des fiches et des vidéos | 0 € | P0 |
| D6 | Photos et vidéos détenues ou autorisées | L122-4, L335-2 CPI | Photos et vidéos propres à partir de l'échantillon | 0 € | P0 |
| D7 | Aucun produit contrefaisant, aucune marque de tiers | L716-9, L716-10 CPI | Contrôle visuel + recherche TMview | 0 € | P0 |

### 6.3 Rétractation, garanties, livraison, médiation

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| E1 | Information complète sur la rétractation (délai, modalités, frais de retour, formulaire) | L221-5 C. conso | Publier `retours-retractation.md` | 0 € | P0 |
| E2 | Fonctionnalité « renoncer au contrat ici » → formulaire → « confirmer la rétractation » → accusé de réception horodaté | L221-21 C. conso (ord. n° 2026-2) ; décret n° 2026-3 | Formulaire Shopify + e-mail automatique (Shopify Flow ou application) ; lien en pied de page, espace client, e-mail de confirmation | 0 € | P0 |
| E3 | Remboursement sous 14 jours, frais de livraison standard inclus | L221-24, L242-4 C. conso | Procédure SAV écrite ; rappel dans l'outil de support | 0 € | P0 |
| E4 | Exceptions au droit de rétractation limitées aux cas légaux | L221-28 C. conso | Ne mentionner que les exceptions réellement applicables | 0 € | P0 |
| E5 | Mise en œuvre de la garantie légale (réparation ou remplacement sous 30 jours) | L217-8 et s. C. conso | Procédure SAV + budget de remplacement | Provision 3-8 % du CA [E-f] | P0 |
| E6 | Formulaire type de rétractation | R221-1 C. conso (annexe) | Inclus dans `retours-retractation.md` et dans l'e-mail de confirmation | 0 € | P0 |
| F1 | Date ou fourchette de livraison affichée | L111-1 3°, L216-1 C. conso | Fiche produit + checkout, sur la base du 90e centile constaté | 0 € | P0 |
| F2 | Délai maximal ≤ 30 jours ou date annoncée respectée | L216-1 C. conso | Fournisseur avec délai < 15 jours | 0 € | P0 |
| F3 | Suivi des colis et notifications | L221-15 C. conso | Application de suivi ou notifications Shopify | 0-10 €/mois | P1 |
| F4 | Procédure retard, perte, avarie | L216-4, L216-6, L221-15 C. conso | `livraison.md` + procédure SAV | 0 € | P0 |
| F5 | Aucun frais réclamé au client à la livraison (droits, TVA, dédouanement) | L112-1 C. conso | Fournisseur en stock UE/France ou IOSS ; vérifier les conditions du fournisseur | 0 € | P0 |
| F6 | Adresse de retour en France opérationnelle | L221-23 C. conso (pratique) | Renseigner {{ADRESSE_RETOUR}} ; tester un retour | 0-40 €/mois [E-f] | P0 |
| G1 | Adhésion à un médiateur référencé par la CECMC | L612-1 C. conso | Adhésion CM2C | 48 € / 3 ans [S23] | P0 |
| G2 | Coordonnées du médiateur communiquées | L616-1 C. conso | Renseigner {{MEDIATEUR}} | 0 € | P0 |
| G3 | Service client joignable, réponse rapide, numéro non surtaxé | L113-5 C. conso | E-mail + formulaire ; délai cible 24 h ouvrées | 0 € | P1 |
| G4 | Registre des réclamations et accidents liés aux produits | Règl. (UE) 2023/988, art. 11, 12, 20 | Tableur partagé | 0 € | P1 |

### 6.4 Avis, données personnelles, cookies, marketing

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| H1 | Information sur le contrôle des avis | L111-7-2, D111-17 C. conso | Texte sous le bloc d'avis | 0 € | P0 (si avis) |
| H2 | Aucun avis importé, acheté ou rédigé par le vendeur | L121-4 C. conso | Désactiver l'import d'avis AliExpress | 0 € | P0 |
| H3 | Avis négatifs publiés ; tri chronologique par défaut ; date affichée | D111-17, D111-18 C. conso | Paramétrage de l'application d'avis | 0 € | P1 |
| I1 | Politique de confidentialité | Art. 13 RGPD | Publier `confidentialite.md` | 0 € | P0 |
| I2 | Registre des traitements | Art. 30 RGPD | Tableur (modèle CNIL) | 0 € | P1 |
| I3 | Contrats de sous-traitance (Shopify, paiement, e-mail, avis) | Art. 28 RGPD | Accepter les DPA ; lister les sous-traitants | 0 € | P1 |
| I4 | Transferts vers la Chine encadrés | Art. 44-46 RGPD | Clauses contractuelles types avec agent ou fournisseur, ou fournisseur UE | 0 € | P0 (schéma A) |
| I5 | Sécurité des comptes | Art. 32 RGPD | Double authentification ; comptes collaborateurs à droits limités | 0 € | P0 |
| I6 | Procédure en cas de violation de données (72 h) | Art. 33-34 RGPD | Fiche réflexe | 0 € | P2 |
| I7 | Durées de conservation appliquées | Art. 5 RGPD | Purge annuelle des prospects inactifs depuis 3 ans | 0 € | P2 |
| I8 | Exercice des droits sous 1 mois | Art. 12-22 RGPD | Adresse {{EMAIL}} + procédure | 0 € | P1 |
| J1 | Aucun traceur non exempté avant consentement | Art. 82 loi n° 78-17 | Bannière de consentement + API de confidentialité Shopify + mode consentement Google | 0 € | P0 |
| J2 | Bouton « Tout refuser » au premier niveau | Lignes directrices CNIL du 17/09/2020 | Configuration de la bannière | 0 € | P0 |
| J3 | Page cookies + lien permanent « Gérer mes cookies » | Art. 82 loi n° 78-17 | Publier `cookies.md` | 0 € | P0 |
| J4 | Cookies ≤ 13 mois ; choix conservé 6 mois | Recommandations CNIL | Paramétrage des outils de mesure | 0 € | P1 |
| J5 | Preuve des consentements | Art. 7 RGPD | Journal de l'outil de consentement | 0 € | P1 |
| K1 | E-mail et SMS : consentement ou client existant ; désinscription | L34-5 CPCE | Case non pré-cochée ; lien de désinscription | 0 € | P0 |
| K2 | Mention « Publicité » ou « Collaboration commerciale » sur tout contenu de créateur | Loi n° 2023-451, art. 5 | Clause contractuelle + vérification avant publication | 0 € | P0 |
| K3 | Contrat écrit au-delà de 1 000 € HT par an et par créateur, produits offerts compris | Loi n° 2023-451, art. 8 ; décret n° 2025-1137 | Modèle de contrat d'affiliation | 0 € | P1 |
| K4 | Contrôle des contenus des créateurs (responsabilité solidaire) | Loi n° 2023-451, art. 8 III | Validation et archivage de chaque vidéo | 0 € | P0 |
| K5 | Aucun produit ou promotion interdits aux influenceurs | Loi n° 2023-451, art. 3 et 4 | Liste blanche (section 2.4) | 0 € | P0 |
| K6 | Contenus vidéo originaux | CPI | Aucune vidéo de tiers ou de fournisseur sans licence écrite | 0 € | P0 |

### 6.5 Produits, environnement

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| L1 | Rôle déterminé pour chaque produit (importateur, distributeur, fabricant) | Règl. (UE) 2023/988, art. 3, 11-13 | Colonne « schéma » dans le tableau des fournisseurs | 0 € | P0 |
| L2 | Bloc d'informations GPSR sur chaque fiche | Règl. (UE) 2023/988, art. 19 | Métachamps produit (section 2.3) | 0 € | P0 |
| L3 | Personne responsable établie dans l'UE identifiée | Règl. (UE) 2023/988, art. 16 ; règl. (UE) 2019/1020, art. 4 | Attestation du fournisseur ou client lui-même | 0 € | P0 |
| L4 | Coordonnées de l'importateur sur le produit ou l'emballage (schémas A, D, E) | Règl. (UE) 2023/988, art. 11 | Étiquette ou insert imprimé par l'agent | 0,05-0,30 €/unité [E-f] | P0 |
| L5 | Avertissements et notice en français | Règl. (UE) 2023/988, art. 9-12 ; loi n° 94-665 | Vérification sur l'échantillon | 0 € | P0 |
| L6 | Dossier produit conservé 10 ans | Règl. (UE) 2023/988, art. 9, 11 | Dossier partagé par référence | 0 € | P0 |
| L7 | Compte Safety Business Gateway et procédure accident / rappel | Règl. (UE) 2023/988, art. 20, 35-37 | Création du compte ; modèle d'avis de rappel | 0 € | P1 |
| L8 | Échantillon reçu et testé avant publication | Diligence de l'importateur et du distributeur (art. 11-12) ; L217-3 C. conso | Commande test par le circuit réel | 8-17 € par produit [E-m] | P0 |
| M1 | Aucune catégorie soumise au marquage CE ou à une réglementation sectorielle en phase 1 | Directives et règlements sectoriels (section 2.4) | Application de la liste noire | 0 € | P0 |
| M2 | Étiquette de composition textile en français | Règl. (UE) 1007/2011 | Vérification sur l'échantillon | 0 € | P0 (si textile) |
| M3 | Substances restreintes (bijoux, plastiques) | Règl. (CE) 1907/2006, annexe XVII | Rapport d'essai du fournisseur | Variable | P0 (si concerné) |
| N1 | Adhésion à un éco-organisme emballages | L541-10 C. env. | Citeo ou Léko, forfait petits metteurs sur le marché | 80-110 € HT/an [E-f] | P0 (schémas A, B, D) |
| N2 | Adhésion à la filière du produit (EEE, textile, ameublement, sport et loisirs, bricolage et jardin, jouets) | L541-10-1 C. env. | Éco-organisme concerné | Barème à l'unité | P0 (si producteur) |
| N3 | Attestation écrite des IDU du grossiste | L541-10-13 C. env. | Demande par e-mail au grossiste | 0 € | P0 (schéma C) |
| N4 | Triman et Info-tri sur produits et emballages | L541-9-3 C. env. | Vérification ; insert ou étiquette en phase stock | 0-0,10 €/unité [E-f] | P1 |
| N5 | Aucune mention « biodégradable » ou « respectueux de l'environnement » | L541-9-1 C. env. | Relecture | 0 € | P0 |
| N6 | Aucune destruction d'invendus | L541-15-8 C. env. | Procédure de don ou de recyclage | 0 € | P2 |

### 6.6 Fiscalité, douane, paiements, comptabilité, assurance, opérations

| ID | Exigence | Base légale | Action concrète | Coût | Priorité |
|---|---|---|---|---|---|
| O1 | Régime de TVA choisi et suivi du seuil (85 000 € / 93 500 €) | CGI art. 293 B (CIBS au 1/09/2026) | Décision écrite avec l'expert-comptable ; suivi mensuel du CA | 0 € | P0 |
| O2 | Mention « TVA non applicable, art. 293 B du CGI » (franchise) | CGI art. 293 B et 293 E | Factures + CGV art. 4 | 0 € | P0 |
| O3 | Autoliquidation de la TVA sur les services achetés dans l'UE (Shopify, Meta, TikTok, Google) | CGI art. 283-2 | Déclaration selon le régime ; numéro de TVA intracommunautaire | 0 € | P1 |
| O4 | Immatriculation IOSS si import ≤ 150 € avec son propre numéro | Dir. 2006/112/CE, art. 369 L et s. | Inscription au guichet unique | 0 € | P2 (schéma A2) |
| O5 | Guichet OSS au-delà de 10 000 € de ventes intra-UE | Dir. 2006/112/CE | Inscription avant le dépassement | 0 € | P2 |
| O6 | Réception des factures électroniques | Réforme de la facturation électronique (obligation au 1/09/2026) | Choisir une plateforme agréée | 0-15 €/mois [E-f] | P0 |
| O7 | Émission électronique et e-reporting des ventes aux particuliers | Idem (échéance 1/09/2027 pour PME et micro) | Préparer avec la plateforme agréée | 0 € | P2 |
| P1 | Aucun colis ne génère de frais pour le client | L112-1 C. conso | Clause DDP ou stock UE | 0 € | P0 |
| P2 | Droit forfaitaire de 3 € et redevance de 2 € intégrés au prix de revient | Règl. (UE) 2026/382 ; redevance de gestion de l'Union | Tableur de marge par produit | 0 € | P0 |
| P3 | Numéro EORI avant tout import en gros | Code des douanes de l'Union | Demande en ligne | 0 € | P2 |
| P4 | Classement tarifaire et droits vérifiés avant commande de stock | Tarif intégré (TARIC) | Vérification avec le transitaire | 0 € | P2 |
| Q1 | Compte de paiement vérifié (identité, Kbis/RNE, IBAN professionnel) | LCB-FT ; conditions des prestataires | Vérification avant lancement | 0 € | P0 |
| Q2 | Descripteur bancaire = nom de marque + domaine | Règles des réseaux de cartes | Paramètres Shopify Payments | 0 € | P0 |
| Q3 | Politiques publiées avant activation des paiements | Conditions Shopify, Stripe, PayPal | Six pages en ligne | 0 € | P0 |
| Q4 | Suivi transmis à PayPal | Conditions PayPal | Synchronisation automatique | 0 € | P1 |
| Q5 | Procédure de réponse aux rétrofacturations | Règles Visa et Mastercard | Dossier de preuve type (section 4.3) | 0 € | P1 |
| Q6 | Taux de litige < 0,5 % suivi chaque semaine | Seuils VAMP et ECM [S30][S31] | Tableau de bord | 0 € | P1 |
| R1 | Compte bancaire professionnel dédié | Obligatoire pour une société ; micro : au-delà de 10 000 € de CA deux années de suite | Ouverture | 0-10 €/mois | P0 |
| R2 | Outil comptable et rapprochement des versements Shopify | L123-12 C. com. | Export mensuel des versements | 0-30 €/mois [E-f] | P1 |
| R3 | Conservation des pièces 10 ans | L123-22 C. com. | Archivage numérique | 0 € | P1 |
| R4 | Calendrier URSSAF, TVA, IS, CFE | CGI ; CSS | Agenda partagé | 0 € | P1 |
| S1 | Assurance RC professionnelle et RC produits | 1245 et s. C. civ. (exposition) | Trois devis | 150-500 €/an [E-f] | P1 (P0 avant tout stock) |
| S2 | Recherche d'antériorité du nom de marque | L711-3 CPI | INPI, TMview | 0 € | P0 |
| S3 | Dépôt de la marque | CPI | INPI, 1 classe | 190 € [S53] | P2 |
| S4 | Accessibilité de base du thème | Dir. (UE) 2019/882 (exemption microentreprise) | Thème accessible, textes alternatifs | 0 € | P2 |
| T1 | Délai réel mesuré avant affichage | L216-1, L121-2 C. conso | Mesure sur les premières commandes et l'échantillon | 0 € | P0 |
| T2 | Niveaux de service : transmission < 24 h, suivi < 72 h | L221-15 C. conso | Routine quotidienne | 0 € | P0 |
| T3 | Procédure SAV écrite (retard, défaut, rétractation, litige bancaire) | L216-6, L217-8, L221-24 C. conso | Document interne + réponses types | 0 € | P0 |

**Synthèse de la checklist** : 111 exigences, dont 79 de priorité P0 (certaines conditionnelles : « si textile », « schéma A ») ; coût obligatoire minimal de 48 € (schéma C) à ≈ 160 € (schémas A et B) hors abonnements techniques.

---

## 7. Alertes et points à vérifier

| # | Alerte | Impact | Action |
|---|---|---|---|
| 1 | La redevance UE de 2 € (1/11/2026) est annoncée par la Commission et les administrations ; l'acte peut encore faire l'objet d'une objection et son traitement TVA diverge selon les sources [S3][S56] | Coût rendu Chine-direct incertain à ±0,40 € | Vérifier sur le site de la douane française fin octobre 2026 |
| 2 | Qualification d'importateur GPSR du dropshipper Chine-direct déduite des définitions du règlement ; la fiche DGCCRF dédiée n'a pas pu être consultée (accès bloqué) [S15] | Risque de sous-estimation des obligations | Retenir la qualification d'importateur ; consulter la fiche DGCCRF |
| 3 | Double TVA possible en achetant sur AliExpress avec IOSS de la plateforme [S55] | Jusqu'à 20 % du coût d'achat perdu | Faire valider par l'expert-comptable avant toute vente en schéma A |
| 4 | Le budget de 150 € ne finance pas à la fois la REP (schémas A, B), l'abonnement Shopify et les échantillons | Lancement non conforme ou sous-financé | Schéma C (grossiste français) en phase 1 |
| 5 | Directives non transposées à la date : 2024/825 (allégations, avis harmonisé), 2024/1799 (réparation) ; directive 2024/2853 (produits défectueux) à transposer au 9/12/2026 [S36][S38][S39] | CGV à mettre à jour à chaque transposition | Veille trimestrielle ; date de mise à jour dans les CGV |
| 6 | Numérotation réglementaire de la fonctionnalité de rétractation divergente selon les sources (D221-5 ou D222-2) [S19][S20] | Référence d'article dans les CGV | Les modèles citent L221-21 et le décret n° 2026-3 sans numéro D |
| 7 | Champ d'application du logiciel de caisse sécurisé pour un site e-commerce assujetti à la TVA [S13] | Amende en cas de contrôle | Question à poser à l'expert-comptable |
| 8 | Plafond du taux réduit d'IS : 42 500 € selon les sources officielles consultées ; relèvement à 100 000 € discuté au PLF 2026 [S9] | Économie d'IS sous-estimée ou surestimée | Vérifier la loi de finances 2026 promulguée |
| 9 | Montant du forfait Citeo ou Léko pour petits metteurs sur le marché non confirmé par une source officielle [S35] | ±30 € | Simulateur de l'éco-organisme |
| 10 | Tarifs BigBuy issus de sources tierces (page officielle inaccessible) [S47] | Choix fournisseur | Vérifier sur bigbuy.eu |
| 11 | Taux Shopify Payments France relevés par une source secondaire (la page tarifaire française s'affiche en dollars depuis l'outil de recherche) [S28][S29] | ±0,2 point sur les frais | Vérifier dans l'interface Shopify lors de l'activation |
| 12 | Absence de frais Shopify sur PayPal quand Shopify Payments est actif : hypothèse [E-m] | +2 % sur les paiements PayPal si inexacte | Vérifier dans les paramètres de paiement |
| 13 | Loi « mode ultra-express » : décrets de seuils non publiés au 28/09/2026 [S40] | Pénalités et interdiction de publicité pour certains textiles | Éviter le textile à petit prix en phase 1 |
| 14 | Medicys cité par d'anciens guides comme médiateur | Adhésion sans valeur légale | Vérifier la liste CECMC avant adhésion |

---

## 8. Sources

Consultées entre le 11 et le 12 octobre 2026. Plusieurs sites officiels français (economie.gouv.fr, Légifrance, EUR-Lex) bloquent les accès automatisés : leur contenu a alors été lu via les résultats du moteur de recherche ou une source secondaire concordante ; la colonne « Fiabilité » le signale.

| # | Source | URL | Fiabilité |
|---|---|---|---|
| S1 | Ministère de l'Économie, communiqué n° 850 du 30/06/2026 : droit de 3 € par catégorie d'article au 1/07/2026, suspension de la taxe française, redevance UE au 1/11/2026 | https://presse.economie.gouv.fr/?p=180373 | Élevée |
| S2 | Commission européenne, Access2Markets : droit de 3 € par article (règl. (UE) 2026/382 et 2026/1200), définition de l'article, identifiants produits au 1/11/2026 | https://trade.ec.europa.eu/access-to-markets/fr/news/lue-applique-un-droit-de-douane-de-3-eur-par-article-sur-les-envois-de-faible-valeur-faisant-lobjet | Élevée |
| S3 | Revenue (administration irlandaise), communiqué du 29/09/2026 : redevance de gestion de l'Union de 2 € par article | https://www.revenue.ie/en/corporate/press-office/press-releases/2026/pr-092926-handling-fee.aspx | Élevée |
| S4 | Legifiscal : suspension de la taxe française de 2 € au 1/07/2026 | https://www.legifiscal.fr/actualites-fiscales/4550-taxe-petits-colis-france-suspend-prelevement-2-profit-nouveau-droit-douane-europeen.html | Moyenne |
| S5 | CCI Lyon Métropole : taxe de 2 € sur les petits colis au 1/03/2026 (art. 82 loi n° 2026-103) | https://www.lyon-metropole.cci.fr/actualite/taxe-2-euros-sur-les-petits-colis-entree-en-vigueur-mars-2026 | Moyenne |
| S6 | Service-public.fr, franchise en base de TVA (vérifié le 01/01/2026) | https://entreprendre.service-public.gouv.fr/vosdroits/F21746 | Élevée |
| S7 | Bpifrance Création, PLF 2026 : seuil unique de franchise proposé à 37 500 € (15/10/2025) | https://bpifrance-creation.fr/entrepreneur/actualites/plf-2026-franchise-base-tva-annoncee-a-37-500-eu | Élevée (pour le projet) |
| S7b | Synthèses : maintien des seuils de franchise par le Parlement | https://www.maformationimmo.fr/budget-2026-tva-le-parlement-maintient-les-seuils-de-franchise-pour-les-micro-entrepreneurs/ ; https://comptabook.fr/tva/seuil-franchise-tva-2026/ | Faible |
| S8 | BOFiP, BOI-RES-TVA-000253-20260218 : recodification de la TVA dans le CIBS, références CGI admises sur factures jusqu'au 31/12/2027 | https://bofip.impots.gouv.fr/bofip/14901-PGP.html/identifiant=BOI-RES-TVA-000253-20260218 | Élevée |
| S9 | Service-public.fr, taux de l'impôt sur les sociétés (vérifié le 17/02/2026) | https://entreprendre.service-public.gouv.fr/vosdroits/F23575 | Élevée |
| S10 | Service-public.fr, plafonds de la micro-entreprise 2026 (vérifié le 21/02/2026) | https://entreprendre.service-public.gouv.fr/vosdroits/F32353 | Élevée |
| S10b | Service-public.fr, cotisations du micro-entrepreneur (vérifié le 01/01/2026) | https://entreprendre.service-public.gouv.fr/vosdroits/F36232 | Élevée |
| S11 | Legifiscal : réforme du régime simplifié de TVA au 1/01/2027 | https://www.legifiscal.fr/actualites-fiscales/4052-loi-finances-2025-reforme-regime-simplifie-tva-compter-2027.html | Moyenne |
| S12 | LegalPlace : calendrier de la facturation électronique | https://www.legalplace.fr/guides/facturation-electronique/ | Moyenne |
| S13 | impots.gouv.fr : champ d'application du logiciel de caisse sécurisé (modifié le 21/05/2026) | https://www.impots.gouv.fr/professionnel/questions/quel-est-le-champ-dapplication-de-lobligation-de-detenir-un-logiciel-de | Élevée |
| S14 | DGCCRF, « Dropshipping : des manquements dans la moitié des sites contrôlés » (enquêtes 2022 et 2023) | https://www.economie.gouv.fr/dgccrf/laction-de-la-dgccrf/les-enquetes/dropshipping-des-manquements-dans-la-moitie-des-sites | Élevée (lue via synthèse ; page bloquée) |
| S15 | DGCCRF, fiche pratique « Dropshipping : comment respecter la réglementation ? » | https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/dropshipping-comment-respecter-la-reglementation | Élevée (non lue : accès bloqué) |
| S16 | La Libre / AFP, amende transactionnelle de 40 M€ contre Shein (3/07/2025) | https://www.lalibre.be/economie/entreprises-startup/2025/07/03/une-amende-record-de-40-millions-pour-shein-en-france-pour-pratiques-commerciales-trompeuses-GQLCSQ7DTBG65NAFW6XCKRTWKU/ | Moyenne |
| S17 | CNIL, sanction de 150 M€ contre Shein (cookies) | https://www.cnil.fr/fr/cookies-deposes-sans-consentement-la-cnil-sanctionne-shein-dune-amende-de-150-millions-deuros | Élevée |
| S18 | DGCCRF, fiche « Annonces de réduction de prix » (mise à jour du 25/08/2026) | https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/annonces-de-reduction-de-prix-ce-que-vous-devez-savoir | Élevée |
| S19 | Village de la Justice (K. Sammier, avocat) : fonctionnalité de rétractation en ligne, ordonnance n° 2026-2 | https://www.village-justice.com/articles/commerce-droit-retractation-ajout-obligatoire-une-fonctionnalite-retractation,55675.html | Moyenne |
| S20 | La Cité des entreprises : décret n° 2026-3 du 5/01/2026 | https://www.lacitedesentreprises.com/droit-des-affaires/obligation-daffichage-du-bouton-de-retractation-en-ligne-les-precisions-apportees-par-le-decret-n-2026-3-du-5-janvier-2026/ | Moyenne |
| S21 | Légifrance, article L221-18 du code de la consommation | https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032226842 | Élevée |
| S22 | Règlement (UE) 2024/3228 (fin de la plateforme RLL) ; CMS | https://eur-lex.europa.eu/eli/reg/2024/3228/oj/fra ; https://cms.law/en/deu/legal-updates/the-odr-platform-is-closing-what-businesses-need-to-know | Élevée |
| S23 | CM2C, tarifs | https://www.cm2c.net/tarifs.php | Élevée |
| S24 | Stripe, tarifs France | https://stripe.com/fr/pricing | Élevée |
| S24b | Comparatifs de médiateurs (CNPM, Medicys) | https://margeoapp.com/blog/mediateur-consommation-revendeur-obligatoire ; https://lamicrobyflo.fr/la-mediation-de-la-consommation/ | Faible |
| S25 | Stripe, documentation des versements | https://docs.stripe.com/payouts | Élevée |
| S26 | PayPal, frais professionnels France (mis à jour le 15/07/2026) | https://www.paypal.com/fr/business/paypal-business-fees | Élevée |
| S27 | PayPal, aide « Comment débloquer mes paiements suspendus ? » | https://www.paypal.com/fr/smarthelp/article/faq3743 | Élevée |
| S28 | Kanal : frais Shopify Payments France (page Shopify relevée le 7/10/2026) | https://getkanal.com/fr/blog/shopify-payments-frais | Moyenne |
| S29 | Shopify, page tarifs (frais des passerelles tierces) | https://www.shopify.com/fr/tarifs | Élevée |
| S30 | Visa VAMP : Fraudio ; PayPal, Spring 2026 Release Guide | https://fraudio.com/blog/visa-vamp-guide ; https://paypal.com/us/brc/article/spring-2026-release-guide | Moyenne |
| S31 | Chargebacks911, seuils Mastercard | https://chargebacks911.com/mastercard-chargeback-threshold/ | Faible |
| S32 | Règlement (UE) 2023/988 (GPSR), EUR-Lex | https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32023R0988 | Élevée |
| S33 | ADEME, identifiant unique des filières REP | https://filieres-rep.ademe.fr/en/identifiant-unique | Élevée |
| S34 | Citeo, adhésion et obligations des metteurs sur le marché | https://www.citeo.com/en/why-join-citeo/ | Élevée |
| S35 | La Micro by Flo : REP emballages en micro-entreprise (forfaits) | https://lamicrobyflo.fr/rep-emballages-micro-entreprise/ | Faible |
| S36 | Village de la Justice (G. Leclerc, avocat) : directive 2024/825 non transposée au 27/09/2026 | https://www.village-justice.com/articles/allegations-environnementales-septembre-2026-directive-applique-france-pas,59252.html | Moyenne |
| S37 | Noerr : règlement d'exécution (UE) 2025/1960, avis et label harmonisés | https://www.noerr.com/en/insights/new-labelling-obligations-for-commercial-guarantees-offered-by-producers-and-legal-guarantee-of-conformity-under-the-empco-directive-action-needed-by-september-2026 | Moyenne |
| S38 | HOP : directive « droit à la réparation » non transposée au 31/07/2026 | https://www.halteobsolescence.org/directive-reparation-europe-retard-france/ | Moyenne |
| S39 | Linklaters : directive (UE) 2024/2853 sur les produits défectueux | https://www.linklaters.com/knowledge/articles/alerts-newsletters-and-guides/2025/september/19/the-product-liability-directive | Moyenne |
| S40 | Euronews : adoption de la loi contre la mode ultra-express (29/06/2026) | https://fr.euronews.com/my-europe/2026/06/29/france-le-parlement-adopte-definitivement-la-loi-qui-sattaque-a-la-mode-jetable | Moyenne |
| S41 | Kolsquare : décret n° 2025-1137, contrat écrit au-delà de 1 000 € HT | https://www.kolsquare.com/fr/blog/la-france-publie-un-nouveau-decret-definissant-les-contrats-obligatoires-pour-les-partenariats-avec-les-influenceurs | Moyenne |
| S42 | Next : contrôles DGCCRF de 310 influenceurs | https://next.ink/brief-article/la-dgccrf-controle-310-influenceurs-et-delivre-151-avertissements-injonctions-et-suites-penales/ | Moyenne |
| S43 | Simonnet Avocat : mentions légales après la loi SREN (LCEN art. 1-1 et 1-2) | https://www.simonnetavocat.fr/mentions-legales-dun-site-internet-obligations-sanctions-et-modele/ | Moyenne |
| S44 | iubenda : acte européen sur l'accessibilité, exemption des microentreprises | https://www.iubenda.com/fr/help/181749-eaa-compliance-7/ | Moyenne |
| S45 | DSers, tarifs | https://www.dsers.com/pricing | Élevée |
| S46 | Spocket, tarifs | https://www.spocket.co/pricing | Élevée |
| S47 | Avis BigBuy (Trendtrack, Copyfy) | https://www.trendtrack.io/fr/blog-post/avis-bigbuy-est-ce-une-option-fiable-pour-votre-site-de-dropshipping ; https://www.copyfy.io/blog/avis-bigbuy | Faible |
| S48 | CJ Dropshipping : entrepôt en Allemagne | https://cjdropshipping.com/blogs/cj-news/CJdropshipping-for-Germany-Dropshipping-Sellers | Moyenne |
| S49 | Délais CJPacket (Parcelsapp, Earnifyhub) | https://parcelsapp.com/en/carriers/cjpacket ; https://www.earnifyhub.com/blog/dropshipping/cj-dropshipping-vs-aliexpress | Faible |
| S50 | FashionUnited : entrepôts locaux d'AliExpress en Europe (2025) | https://fashionunited.fr/actualite/business/aliexpress-renforce-sa-presence-en-europe-avec-des-entrepots-locaux/2025061638436 | Moyenne |
| S50b | Vitepromo : délais AliExpress Choice | https://www.vitepromo.com/shopping-ecommerce/code-promo-aliexpress | Faible |
| S51 | La Poste, tarifs colis 2026 | https://www.laposte.fr/tarifs-postaux-colis | Élevée |
| S52 | Margeo : externaliser ses expéditions avec un 3PL (juillet 2026) | https://margeoapp.com/blog/externaliser-expedition-3pl-france | Faible |
| S53 | INPI, barème au 2/07/2026 | https://www.inpi.fr/inpi-block/download-document?id=20516 | Élevée |
| S54 | Socic (expert-comptable) : TVA du dropshipping sans IOSS (mis à jour le 19/05/2026) | https://www.socic.fr/ressources-comptabilite/articles/dropshipping-tva-sans-ioss-guichet-unique-regles-bofip-2026-seuil-150-e-importation-et-facturation | Moyenne |
| S55 | Calculer-TVA : TVA à l'import depuis la Chine, IOSS, AliExpress | https://www.calculer-tva.com/guides/tva-import-export-chine/ | Faible |
| S56 | VATupdate : TVA due sur la redevance de gestion de 2 € (8/10/2026) | https://www.vatupdate.com/2026/10/08/vat-is-due-on-the-eus-e2-union-handling-fee-for-e-commerce-imports/ | Moyenne |
| S57 | CNIL, « Cookies et traceurs : que dit la loi ? » ; Legiscope (durées, mesure d'audience) | https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies/que-dit-la-loi ; https://www.legiscope.com/blog/cookies-traceurs-rgpd-conformite.html | Élevée / moyenne |
| S58 | Directive (UE) 2024/825, EUR-Lex | https://eur-lex.europa.eu/legal-content/FR/TXT/PDF/?uri=OJ:L_202400825 | Élevée |
| S59 | Légifrance, loi n° 2023-451 du 9 juin 2023 (influence commerciale) | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000047663185 | Élevée |
| 02-acquisition S4 | Dossier `recherche/02-acquisition.md`, conditions logistiques TikTok Shop France | `recherche/02-acquisition.md` | Voir ce dossier |
