# Lancement : calendrier jour par jour (30 jours)

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 (version corrigée après la [revue red team](../docs/revue-red-team.md)) |
| Fenêtre | **J1 = lundi 16/11/2026** (lendemain de la porte 1) → **J30 = mardi 15/12/2026** (date limite de Noël) |
| Condition de départ | Porte 1 franchie le 15/11 (`brand.json` → `lancement.porte_1` : vues ou inscriptions, **taux de clics produit ≥ 1,5 %**, 20 commentaires d'intention hors entourage) et option de trésorerie a ou b signée (`brand.json` → `hypotheses_cles.tresorerie`). Sinon, tout le calendrier glisse (§4) |
| Hypothèse produit | Le rouleau a gagné le duel. Si le tapis de fouille gagne, son micro-stock remplace celui du rouleau, les vidéos R sont remplacées par les TF et 5 scripts de kits sont écrits en S6 |
| Ordre corrigé | **Le micro-stock est commandé et payé le J1, avant toute précommande.** Les dates de précommande sont calculées à partir de cette commande. Les précommandes ne financent pas le stock (05 §5.2) |
| Cadence | **2 vidéos TikTok par jour** (plan de 25 heures par semaine, [07 §3](07-plan-organique-90j.md)), recyclées sur Reels (J+1) et Pinterest (J+1 à J+7) ; LIVE à partir de S12 |
| Entrées | [07 — Plan 90 jours](07-plan-organique-90j.md), [scripts-tiktok.md](scripts-tiktok.md), [emails.md](emails.md), [createurs-affiliation.md](createurs-affiliation.md), [04 §6.2](../strategie/04-strategie.md), [05 §5](../finance/05-analyse-financiere.md) |
| Notation des vidéos | `R02-B` = script R02, accroche B. `P3` = réponse vidéo à un vrai commentaire du jour. `R10 ép. n` = épisode de la série « je lance ma marque » (faits réels du jour). Publication vers 12 h et 19 h |

---

## 0. Jalons et règles de décision

| Jalon | Date nominale | Règle |
|---|---|---|
| Conformité et commande du stock | **J1, lun. 16/11** | Médiateur CM2C, Léko (IDU), dépôt INPI classe 21, assurance RC souscrite, identité légale complète (`generer.py --publication` sans erreur). Puis **commande et paiement du micro-stock** : 40 rouleaux, 45 gants, 12 raclettes, 8 tapis, un seul colis, facture B2B HT, envoi express ou entrepôt UE (≈ 476 € TTC) |
| Calcul des dates de précommande | J2, mar. 17/11 | Expédition à partir du = date de commande du stock + **90e centile du transit mesuré sur les échantillons** + 3 jours ouvrés (dédouanement, contrôle, étiquetage) ; livraison au plus tard le = expédition + 6 jours ouvrés ; plafond 30 jours après l'ouverture. Exemple nominal avec un transit P90 de 12 jours : **expédition à partir du mer. 2/12, livraison au plus tard le jeu. 10/12**. Avec 20 jours : 9/12 et 17/12. Au-delà de 25 jours, la date dépasse le 23/12 : aucun argument Noël (`brand.json` → `livraison.precommande.exemples_calcul_commande_stock_16_11_2026`) |
| Ouverture des précommandes | **J3, mer. 18/11** | Dates saisies dans `brand.json` → `livraison.precommande`, phase `precommande`, site régénéré : bandeau, fiches, panier, page Commande, page Stripe et e-mail de confirmation affichent les mêmes dates ; aucune page ne promet « 1 jour ouvré » (test bloquant de `verifier_site.js`) |
| Contrôle J-10 | **lun. 30/11** (10 jours avant le 10/12) | Colis fournisseur arrivé en France ? Sinon : e-mail individuel à chaque client avec la nouvelle date et le choix d'une annulation remboursée sous 14 jours (CGV art. 5.4) |
| Réception du stock | J15-J16, lun. 30/11-mar. 1/12 | Contrôle à 100 %, étiquette importateur, notice en français ([gabarits](../docs/gabarits/)) ; stock saisi dans `brand.json` |
| Expédition des précommandes | **J17, mer. 2/12** | Toutes les précommandes déposées à partir de la date écrite ; site en phase `vente` |
| Porte stock | J17, mer. 2/12 | **≥ 20 précommandes payées par des acheteurs hors entourage** (noms et adresses vérifiés) **et conversion liste d'attente → précommande ≥ 8 %** → réassort et stock principal autorisés (stock principal fin janvier 2027). Sinon : aucun réassort, le micro-stock est écoulé, retour au test de contenu |
| Ouverture de TikTok Shop | J18, jeu. 3/12 | Fiches actives avec le stock réel − 2 ; expédition par TikTok ou transporteur agréé (livraison sous 4 jours ouvrés exigée en expédition par le vendeur) ; avec l'option b, aucune collaboration d'affiliés avant le premier règlement TikTok Shop (≈ 31 jours après les premières livraisons) |
| Date limite de Noël | **Commande avant le mar. 15/12** pour une livraison au plus tard le mer. 23/12 | 15/12 + 6 jours ouvrés (délai maximal annoncé, préparation comprise, `brand.json` → `livraison.noel_2026`) ; affichée à partir du 1/12, en phase vente |
| Porte 2 | J24-J30 | ≥ 3 commandes par jour pendant 7 jours après l'arrivée du stock. La finance situe ce seuil en mars-avril 2027 dans le scénario réaliste (05 §4.4) : un échec en décembre déclenche une revue, pas un arrêt |

**Trésorerie du mois** (05 §5.2 ; `brand.json` → `hypotheses_cles.tresorerie`) : médiateur 48 €, Léko 114 € TTC, INPI 190 €, RC 25 €, fournitures 12 € et micro-stock ≈ 476 € TTC le J1, soit **≈ 865 €** en plus des 45 € déjà engagés en octobre : **910 €** avant le premier versement Stripe (7 jours après le premier paiement). Les ventes TikTok Shop sont réglées **31 jours après livraison** pour un vendeur débutant (05 §5.1) : les ventes de décembre arrivent fin janvier. Règle : réserve disponible < 300 € → plus aucune commande fournisseur ni échantillon avant le prochain encaissement.

---

## 1. Préparation (J-3 à J0)

| J | Date | Vidéos TikTok | Actions | Décision ou indicateur |
|---|---|---|---|---|
| J-3 | jeu. 12/11 | TF29-C · R05-B | Décompte des commentaires d'intention (hors entourage), des inscrits par produit (attribut `PRODUIT` dans Brevo) et du taux de clics produit des vidéos de démonstration | Tableau du duel à jour |
| J-2 | ven. 13/11 | TF30-C · R07-C | Dossiers CM2C et Léko remplis sans paiement ; devis RC retenu ; panier fournisseur préparé (4 références, un colis, facture HT) ; C1 rédigé dans Brevo | — |
| J-1 | sam. 14/11 | TF26-C · R10 ép. 2 (« demain, je décide ») | Captures d'écran des statistiques du duel | — |
| J0 | dim. 15/11 | R17-C · P3 | **Porte 1** : décision écrite (produit, chiffres, go / no-go) | Go si (≥ 1 vidéo > 50 000 vues avec ≥ 1 % de clics **ou** ≥ 150 inscrits) **et** taux de clics produit ≥ 1,5 % **et** ≥ 20 commentaires d'intention hors entourage |

---

## 2. Calendrier J1 → J30

| J | Date | Phase | TikTok (2 vidéos) | E-mail | Créateurs | Opérations, conformité, trésorerie | Indicateur du jour (nominal / plancher) |
|---|---|---|---|---|---|---|---|
| 1 | lun. 16/11 | Conformité et stock | R10 ép. 3 (« la porte est franchie, voici les chiffres ») · R02-A | Flux de bienvenue actif pour les nouveaux inscrits | Revue de la liste des 50 qualifiés ; tri des 15 meilleurs scores | CM2C (48 €), Léko (114 € TTC), INPI classe 21 (190 €), RC souscrite ; **commande et paiement du micro-stock** (≈ 476 € TTC) ; capture du suivi du colis | Stock commandé |
| 2 | mar. 17/11 | Conformité | R05-C · R14-A | — | — | Dates de précommande calculées (§0) et saisies dans `brand.json` ; IDU et médiateur dans `brand.json` → `identite` ; `generer.py --publication` ; Stripe en mode réel ; commande test payée puis remboursée | Commande test réussie |
| 3 | **mer. 18/11** | **Ouverture des précommandes** | R10 ép. 4 (« c'est ouvert », CTA-P, dates à l'écran) · R02-B | **C1** lot 1 (300 premières adresses, inscrits ayant donné leur consentement) | — | Phase `precommande` publiée ; vérification de la fiche, du bandeau, du panier, de la page Stripe et du bloc GPSR | 3 précommandes / 1 |
| 4 | jeu. 19/11 | Précommande | R04-B · R15-A | C1 lot 2 (reste de la liste) | — | Réponses aux messages sous 48 h ouvrées (cible 24 h) ; suivi des précommandes et des gants de la prime dans [`pilotage.xlsx`](../docs/pilotage.xlsx) | 6 cumulées / 2 |
| 5 | ven. 20/11 | Précommande | R06-A · R03-A | — | — | Compteur de la prime mis à jour dans `brand.json` (gants attribués, date) et site régénéré | 10 cumulées / 4 |
| 6 | sam. 21/11 | Précommande | R12-A · P3 | — | — | Stories : coulisses de la commande fournisseur (vraie capture, prix masqués) | 13 / 5 |
| 7 | dim. 22/11 | Précommande | R16-A · R11-B (« le stock est en route ») | — | — | **Revue hebdomadaire** des KPI ([07 §8](07-plan-organique-90j.md)) | 15 / 6 |
| 8 | lun. 23/11 | Précommande | R09 ép. 2 (nouveau tissu choisi par les commentaires) · R08-B | — | **M1** aux 15 meilleurs scores (échantillon annoncé pour le 3/12, date écrite) | Fiches TikTok Shop préparées en brouillon (8 fiches, photos réelles dès réception) | 17 / 7 |
| 9 | mar. 24/11 | Précommande | R03-B · R05-A | **C2** (inscrits sans commande, consentement enregistré) | — | Suivi du colis fournisseur | 19 / 8 |
| 10 | mer. 25/11 | Précommande | R19-A (pas de Black Friday) · R10 ép. 5 (bilan chiffré des précommandes) | — | — | Impression des étiquettes importateur et des notices | 21 / 9 |
| 11 | jeu. 26/11 | Précommande | R19-B · P3 | — | — | Point colis : en France ? | 22 / 10 |
| 12 | ven. 27/11 | Black Friday | R19-C · R17-A | Aucun envoi | — | **Aucune remise, aucun compte à rebours** (03 §1.7) | 23 / — |
| 13 | sam. 28/11 | Précommande | R12-B · R15-B | — | **M4** (relance unique) aux créateurs sans réponse | Arrivée nominale du colis (transit de 12 jours) | 24 / — |
| 14 | dim. 29/11 | Précommande | R16-B · R07-B | — | — | **Revue hebdomadaire** | 25 / — |
| 15 | lun. 30/11 | **Contrôle J-10** | R11 suite (« le stock est arrivé », suivi réel) · P3 | Si colis absent de France : e-mail individuel à chaque client (nouvelle date + annulation remboursée au choix) | Adresses des créateurs ayant dit oui collectées (M5) | Réception et contrôle à 100 % du stock | Colis en France |
| 16 | mar. 1/12 | Précommande + saison | K25-A (date limite réelle : 15/12) · R03-C | — | — | Étiquetage ; registre GPSR ; colis préparés ; article A9 publié ([seo-contenu.md](seo-contenu.md)) | Défauts ≤ 5 % (04 §6.3) |
| 17 | **mer. 2/12** | **Expédition des précommandes** | R20-B (déballage du stock, étiquetage) · R20-C (« les colis partent ») | **PO2** à tous les clients des précommandes | — | Dépôt de toutes les précommandes ; stock restant saisi dans `brand.json`, phase `vente`, **date limite de Noël affichée** ; **porte stock** évaluée | 100 % expédié ; porte stock : 20 précommandes hors entourage, conversion ≥ 8 % |
| 18 | jeu. 3/12 | TikTok Shop ouvert | K21-A · R08-C | — | **5 échantillons envoyés** aux premiers « oui » (retirés du stock disponible) | Fiches TikTok Shop actives avec le stock réel − 2 ; mission « nouveau vendeur » acceptée (≥ 5 produits en stock, 4 % pendant 60 jours) | Fiches validées |
| 19 | ven. 4/12 | Vente | K22-A · R05-B | — | — | Ancres produit TikTok Shop sur les vidéos de produit encore actives | 1 commande / jour |
| 20 | sam. 5/12 | Vente | R12-C · K21-B | — | — | Stock TikTok mis à jour à 9 h et 18 h | 1 / jour |
| 21 | dim. 6/12 | Vente | K25-B · R16-C | — | — | **Revue hebdomadaire** | 1 / jour |
| 22 | lun. 7/12 | Vente | K21-C · R15-C | — | **Collaboration ouverte à 12 %** avec la charte ([createurs-affiliation.md](createurs-affiliation.md) §8.3) **si option a** ; avec l'option b, attendre le premier règlement TikTok Shop | — | 2 / jour |
| 23 | mar. 8/12 | Vente | R20-A (premier vrai délai mesuré chez un proche) · K22-B | — | Message « bien reçu ? » aux créateurs | Premières livraisons : date réelle notée dans le tableur (90e centile après 30 livraisons) | 2 / jour |
| 24 | mer. 9/12 | Vente | K24-A (si le tapis est en stock, sinon R07-C) · K25-C | — | — | Kit chat d'hiver activé si le tapis est en stock ; **début de la mesure de la porte 2** | 3 / jour / 1 |
| 25 | jeu. 10/12 | Vente | K23-B · R09 ép. 5 | — | — | Date limite des précommandes : toutes livrées ? Sinon, remboursement proposé | 3 / jour / 1 |
| 26 | ven. 11/12 | Vente | K24-B (ou R06-C) · R03-A (version fêtes) | — | Premières vidéos d'affiliés attendues (option a) : vérification de la mention dans les 24 h | Formulaire d'avis (AV1) testé avec une commande interne | 3 / jour / 1 |
| 27 | sam. 12/12 | Vente | R10 ép. 6 (premiers retours clients réels, avec leur accord) · K21-A (nouvelle prise) | — | Republication en story d'une vidéo d'affilié (avec accord) | — | 3 / jour / 1 |
| 28 | dim. 13/12 | Vente | R17-C · K22-C | — | — | **Revue hebdomadaire** | 3 / jour / 1 |
| 29 | lun. 14/12 | Avant-dernier jour pour Noël | K25 (« commande avant demain soir pour une livraison au plus tard le 23/12 », date réelle) · R02 (nouveau tissu) | Campagne « date limite de Noël » aux inscrits consentants et aux clients sans opposition | Contrôle hebdomadaire des vidéos d'affiliés | **Décision de réassort** (seulement si la porte stock est franchie) : stock < 25 jours de ventes → commande fournisseur (≈ 15 jours, 04 §5.5) ; PO3 pour les premières livraisons | 3 / jour / 1 |
| 30 | **mar. 15/12** | **Dernier jour pour Noël** et bilan | R10 ép. 7 (bilan des 30 jours, chiffres réels) · K24-C (ou R03-B) | PO3 aux clients livrés le 8/12 | Bilan des créateurs : publications, ventes, conformité | Date limite de Noël retirée le soir ; tapis thermique : sans stock à cette date, report à octobre 2027 ; **bilan écrit** (§3) | Porte 2 : ≥ 3 / jour sur 7 jours |

---

## 3. Bilan de J30 (à remplir)

| Indicateur | Cible nominale | Plancher | Réel | Décision si sous le plancher |
|---|---|---|---|---|
| Précommandes (J3-J17) | 30 (stock dimensionné pour 30) | 20 hors entourage | | Sous 20 : porte stock non franchie, aucun réassort |
| Conversion liste d'attente → précommande | ≥ 10 % | 8 % | | Sous 8 % : porte stock non franchie ; revoir l'offre et la page de précommande |
| Dates de précommande tenues | 100 % | 100 % | | Toute précommande en retard : remboursement proposé, cause écrite |
| Délai réel moyen et 90e centile | ≤ 6 jours ouvrés | 7 | | Changer de mode d'envoi ; mettre à jour la promesse |
| Commandes par jour (J24-J30) | 3 | 1 | | Revue du contenu (07 §8.3), pas d'arrêt avant les critères de 04 §6.3 |
| Part des kits sur le site | ≥ 45 % | 30 % | | Retravailler le sélecteur d'offre |
| Taux de défaut à réception | ≤ 5 % | — | | Au-delà : second fournisseur (04 §6.3) |
| Créateurs ayant publié | 3 (option a) | 1 | | Réécrire M1, resserrer la grille |
| Vidéos d'affiliés conformes | 100 % | 95 % | | Fin de collaboration pour les récidivistes |
| Réclamations et litiges | < 0,5 % | 1 % | | Revue du SAV et des délais |
| Réserve de trésorerie disponible | ≥ 300 € | 300 € | | Plafonner les ventes TikTok Shop au stock payé ; aucune commande fournisseur |

---

## 4. Règles de décalage

| Événement | Effet sur le calendrier |
|---|---|
| Porte 1 non franchie le 15/11 | Deux semaines de contenu supplémentaires sur le meilleur produit ; J1 devient le 30/11. Le stock commandé le 30/11 avec un transit de 12 jours donne une livraison au plus tard le 24/12 : **aucun argument Noël** ; l'offre devient « livraison début janvier », annoncée comme telle. Le stock principal reste programmé fin janvier |
| Médiateur, IDU, RC ou identité légale manquants à J2 | L'ouverture (J3) attend ; aucune vente sans eux (`generer.py --publication` refuse) |
| Transit des échantillons trop long (P90 > 25 jours) | Envoi express ou vendeur à entrepôt UE pour le lot ; sinon dates calculées au-delà du 23/12 et aucun argument Noël |
| Moins de 10 précommandes à J9 | Contenu recentré sur la démonstration ; le stock déjà commandé sera écoulé en vente normale et sur TikTok Shop |
| Stock en retard sur la date écrite | Contrôle J-10 : e-mail individuel avant la date, nouvelle date + annulation remboursée sous 14 jours si le client le souhaite |
| Vidéo virale (> 20 000 vues en 6 heures) | Procédure de pic (`brand.json` → `livraison.stock.procedure_pic_viral`) : stock TikTok mis à jour toutes les 2 heures, précommande avec dates réelles dès 5 unités, réassort express à 10 unités si la trésorerie le permet, aucune ancre produit si le stock couvre moins de 7 jours |
| Le tapis de fouille gagne le duel | Son micro-stock est commandé à J1 à la place de celui du rouleau ; les scripts R sont remplacés par TF26-TF30 et 5 scripts de kits à écrire ; dates recalculées avec le transit mesuré de son échantillon |
