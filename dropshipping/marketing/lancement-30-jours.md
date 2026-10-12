# Lancement : calendrier jour par jour (30 jours)

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Fenêtre | **J1 = lundi 16/11/2026** (lendemain de la porte 1) → **J30 = mardi 15/12/2026** |
| Condition de départ | Porte 1 franchie le 15/11 (`brand.json` → `lancement.porte_1`). Si elle ne l'est pas, tout le calendrier glisse (§4) |
| Hypothèse produit | Le rouleau a gagné le duel. Si le tapis de fouille gagne, les vidéos R sont remplacées par les TF et par des scripts de kits à écrire en S6 |
| Entrées | [07 — Plan 90 jours](07-plan-organique-90j.md), [scripts-tiktok.md](scripts-tiktok.md), [emails.md](emails.md), [createurs-affiliation.md](createurs-affiliation.md), [04 §6.2](../strategie/04-strategie.md), [05 §5](../finance/05-analyse-financiere.md) |
| Notation des vidéos | `R02-B` = script R02, accroche B. `P3` = réponse vidéo à un vrai commentaire du jour. `R10 ép. n` = épisode de la série « je lance ma marque » (faits réels du jour). Les vidéos sont publiées vers 8 h, 13 h et 19 h ; recyclage Reels J+1, Shorts J+2, Pinterest J+1 à J+7 |

---

## 0. Jalons et règles de décision

| Jalon | Date nominale | Règle |
|---|---|---|
| Médiateur et éco-organisme en place | J1-J2 | Aucune précommande payée avant l'adhésion au médiateur CM2C et l'obtention de l'identifiant unique (IDU) Léko (04 §4.5) |
| Ouverture des précommandes | **J3, mer. 18/11** | Site en phase `precommande` ; dates écrites sur chaque fiche et dans PO1 |
| Commande du micro-stock | J5, ven. 20/11, **dès 10 précommandes** | ≈ 197 € TTC à avancer : le fournisseur est payé le jour de la commande, Stripe verse 7 jours après le premier encaissement (05 §5.2) |
| Fin de la fenêtre annoncée | J9, mar. 24/11, 23 h 59 | **< 5 précommandes** → aucun stock, remboursement intégral, retour au test de contenu (04 §6.2) |
| Dates écrites sur les précommandes | Expédition à partir du **ven. 4/12**, livraison au plus tard le **lun. 14/12** | Règle : date de commande du stock (20/11) + 90e centile du transit observé sur les échantillons + 2 jours ouvrés ; nominal ici avec un transit de 12 jours (estimation, confiance faible). Limite légale : 30 jours après la commande. **Mettre à jour `site/assets/js/config.js`** (actuellement 23/11 et 04/12) |
| Réception du stock | J17, mer. 2/12 | Contrôle à 100 %, étiquette importateur, notice en français (04 §5.4) |
| Expédition des précommandes et ouverture de TikTok Shop | **J19, ven. 4/12** | Toutes les précommandes déposées le même jour ; fiches TikTok Shop activées avec le stock réel |
| Date limite de Noël | **Commande avant le lun. 14/12** pour une livraison au plus tard le mer. 23/12 | Calcul sur le délai maximal annoncé : 1 jour ouvré de préparation + 6 jours ouvrés de livraison. `brand.json` estime le 17/12 : cette date ne tient qu'avec un 90e centile mesuré plus court ; à défaut, une commande du 17/12 peut arriver le 28/12 |
| Porte 2 | J24-J30 | ≥ 3 commandes par jour pendant 7 jours après l'arrivée du stock (`brand.json` → `lancement.porte_2`). La finance situe ce seuil en mars-avril 2027 dans le scénario réaliste (05 §4.4) : un échec en décembre déclenche une revue, pas un arrêt |

**Trésorerie du mois** (04 §5.3 ; 05 §5.2) : médiateur 48 € et Léko 114 € TTC à J1 ; fournitures ≈ 12 € à J2 ; stock ≈ 197 € TTC à J5 ; échantillons créateurs ≈ 60 € à J19-J20. Total ≈ 430 € avant le premier versement Stripe. Les ventes TikTok Shop sont réglées **31 jours après livraison** pour un vendeur débutant (05 §5.1) : les ventes de décembre arrivent en janvier. Règle : ne mettre en vente sur TikTok Shop que le stock déjà payé (05 §9.4).

---

## 1. Préparation (J-3 à J0)

| J | Date | Vidéos TikTok | Actions | Décision ou indicateur |
|---|---|---|---|---|
| J-3 | jeu. 12/11 | TF29-C · R05-B · R09-C | Décompte des commentaires d'intention et des inscrits par produit ; page de précommande préparée en mode démonstration | Tableau du duel à jour |
| J-2 | ven. 13/11 | TF30-C · R07-C · R03-C | Dossiers CM2C et Léko remplis sans paiement ; C1 rédigé dans Brevo ; dates de précommande calculées selon la règle du §0 | — |
| J-1 | sam. 14/11 | TF26-C · R04-C · R10 ép. 2 (« demain, je décide ») | Captures d'écran des statistiques du duel | — |
| J0 | dim. 15/11 | R17-C · P3 · P3 | **Porte 1** : décision écrite (produit, chiffres, go / no-go) | Go si ≥ 1 vidéo > 50 000 vues avec ≥ 1 % de clics, **ou** ≥ 150 inscrits ; **et** ≥ 20 commentaires d'intention |

---

## 2. Calendrier J1 → J30

| J | Date | Phase | TikTok (3 vidéos) | E-mail | Créateurs | Opérations, conformité, trésorerie | Indicateur du jour (nominal / plancher) |
|---|---|---|---|---|---|---|---|
| 1 | lun. 16/11 | Mise en conformité | R10 ép. 3 (« la porte est franchie, voici les chiffres ») · R02-A · R08-A | Flux de bienvenue actif pour les nouveaux inscrits | Revue de la liste des 50 qualifiés ; tri des 15 meilleurs scores | Adhésion CM2C (48 €) et Léko (114 € TTC) ; demande d'IDU ; décision du client sur la réserve de trésorerie (1 300-1 500 € recommandés par 05 §9.4) | Médiateur signé |
| 2 | mar. 17/11 | Mise en conformité | R05-C · R14-A · P3 | — | — | IDU et médiateur reportés dans les CGV et les mentions légales ; Stripe en mode réel ; commande test payée puis remboursée ; fournitures (≈ 12 €) | Commande test réussie |
| 3 | **mer. 18/11** | **Ouverture des précommandes** | R10 ép. 4 (« c'est ouvert », CTA-P) · R02-B · R09-A | **C1** lot 1 (300 premières adresses) | — | `config.js` : `phase: "precommande"`, dates du §0 ; vérification de la fiche, du bloc GPSR, du lien « renoncer au contrat ici » | 3 précommandes / 1 |
| 4 | jeu. 19/11 | Précommande | R04-B · R15-A · P3 | C1 lot 2 (reste de la liste) | — | Réponses aux messages sous 24 h ; suivi des précommandes dans le tableur | 6 cumulées / 2 |
| 5 | ven. 20/11 | Précommande | R06-A · R03-A · R17-B | — | — | **Si ≥ 10 précommandes : commande du micro-stock** (≈ 197 € TTC) ; sinon attente jusqu'à J9 | 10 cumulées / 5 |
| 6 | sam. 21/11 | Précommande | R12-A · R07-A · P3 | — | — | Stories : coulisses de la commande fournisseur (vraie capture, prix masqués) | 13 / 6 |
| 7 | dim. 22/11 | Précommande | R16-A · R01-A · R11-B (« le stock est commandé ») | — | — | **Revue hebdomadaire** des KPI ([07 §8](07-plan-organique-90j.md)) | 15 / 7 |
| 8 | lun. 23/11 | Précommande | R09 ép. 2 (nouveau tissu choisi par les commentaires) · R08-B · P3 | — | **M1** aux 15 meilleurs scores (échantillon annoncé pour le 4/12, date écrite) | Fiches TikTok Shop préparées en brouillon (8 fiches, photos réelles) | 17 / 8 |
| 9 | mar. 24/11 | Fin de la fenêtre annoncée | R03-B · R05-A · R02-C | **C2** (inscrits sans commande) | — | Fenêtre fermée à 23 h 59 ; **< 5 précommandes → remboursement intégral et arrêt du stock** | 20 / 5 |
| 10 | mer. 25/11 | Précommande continue (réassort suivant) | R19-A (pas de Black Friday) · R14-B · R10 ép. 5 (bilan chiffré des précommandes) | — | — | Site : dates des commandes suivantes mises à jour (même lot si le stock commandé le couvre) | 21 / — |
| 11 | jeu. 26/11 | Précommande | R19-B · R04-C · P3 | — | — | Suivi du colis fournisseur ; impression des étiquettes importateur et des notices | 22 / — |
| 12 | ven. 27/11 | Black Friday | R19-C · R17-A · R06-B | Aucun envoi | — | **Aucune remise, aucun compte à rebours** (03 §1.7) | 23 / — |
| 13 | sam. 28/11 | Précommande | R12-B · R15-B · P3 | — | **M4** (relance unique) aux créateurs sans réponse | — | 24 / — |
| 14 | dim. 29/11 | Précommande | R16-B · R07-B · R01-B | — | — | **Revue hebdomadaire** | 25 / — |
| 15 | lun. 30/11 | Précommande | R11 suite (« le stock arrive », suivi réel) · R09 ép. 3 · P3 | — | Adresses des créateurs ayant dit oui collectées (M5 envoyé) | Retard du stock > 3 jours sur le suivi → e-mail individuel aux clients avec la nouvelle date et l'offre d'annulation remboursée | Colis en France / — |
| 16 | mar. 1/12 | Précommande + saison | K25-A (date limite réelle : 14/12) · R03-C · P3 | — | — | **Date limite de Noël affichée** sur le site (`brand.json` → `livraison.noel_2026`) ; article A9 publié ([seo-contenu.md](seo-contenu.md)) | 27 / — |
| 17 | mer. 2/12 | **Réception du stock** | R20-B (déballage du stock, étiquetage) · K21-A · R08-C | — | — | Contrôle à 100 % ; étiquette importateur sur chaque produit ; registre GPSR ; colis préparés | Défauts ≤ 5 % (04 §6.3) |
| 18 | jeu. 3/12 | Préparation des envois | K22-A · R05-B · R14-C | — | — | Étiquettes Mondial Relay ; tapis thermique : stock reçu ? (limite le 15/12) | 100 % des colis prêts |
| 19 | **ven. 4/12** | **Expédition + TikTok Shop ouvert** | R20-C (« les colis partent ») · K23-A · R02-A (version CTA-V, nouvelle prise) | **PO2** à tous les clients des précommandes | **5 échantillons envoyés** aux premiers « oui » | Dépôt de toutes les précommandes ; site en phase `vente` ; fiches TikTok Shop actives avec le stock payé seulement ; mission « nouveau vendeur » acceptée (≥ 5 produits en stock, 4 % pendant 60 jours) ; expédition TikTok Shop selon le modèle imposé par la plateforme (livraison sous 4 jours ouvrés) | 100 % expédié |
| 20 | sam. 5/12 | Vente | R12-C · K21-B · R09 ép. 4 | — | — | Ancres produit TikTok Shop ajoutées sur les vidéos de produit encore actives | 1 commande / jour |
| 21 | dim. 6/12 | Vente | K25-B · R16-C · P3 | — | — | **Revue hebdomadaire** ; premier LIVE si le compte y est éligible (seuil de 1 000 abonnés non confirmé par TikTok) | 1 / jour |
| 22 | lun. 7/12 | Vente | K21-C · R15-C · R18-A | — | **Collaboration ouverte à 12 %** publiée avec la charte ([createurs-affiliation.md](createurs-affiliation.md) §8.3) ; contrôle hebdomadaire des vidéos d'affiliés | — | 2 / jour |
| 23 | mar. 8/12 | Vente | R20-A (premier vrai délai mesuré chez un proche) · K22-B · P3 | — | Message « bien reçu ? » aux créateurs | Premières livraisons : date réelle notée dans le tableur (90e centile après 30 livraisons) | 2 / jour |
| 24 | mer. 9/12 | Vente | K24-A (si le tapis est en stock, sinon R07-C) · K25-C · R01-C | — | — | Kit chat d'hiver activé si le tapis est en stock ; **début de la mesure de la porte 2** | 3 / jour / 1 |
| 25 | jeu. 10/12 | Vente | K23-B · R09 ép. 5 · P3 | — | — | Formulaire d'avis (AV1) testé avec une commande interne | 3 / jour / 1 |
| 26 | ven. 11/12 | Vente | K24-B (ou R06-C) · R03-A (version fêtes) · P3 | — | Premières vidéos d'affiliés attendues : vérification de la mention dans les 24 h | LIVE du vendredi soir (si éligible) | 3 / jour / 1 |
| 27 | sam. 12/12 | Vente | R10 ép. 6 (premiers retours clients réels, avec leur accord) · K21-A (nouvelle prise) · P3 | — | Republication en story d'une vidéo d'affilié (avec accord) | — | 3 / jour / 1 |
| 28 | dim. 13/12 | Vente | R17-C · K22-C · R18-B | — | — | **Revue hebdomadaire** | 3 / jour / 1 |
| 29 | **lun. 14/12** | **Dernier jour pour Noël** | K25 (« dernier jour pour une livraison au plus tard le 23/12 », date réelle) · R02 (nouveau tissu) · P3 | Campagne « date limite de Noël » aux inscrits et aux clients sans opposition | Contrôle hebdomadaire des vidéos d'affiliés | **Décision de réassort** : stock < 25 jours de ventes → commande fournisseur (≈ 15 jours, 04 §5.5) ; PO3 pour les premières livraisons du 8/12 à partir du 15/12 | 3 / jour / 1 |
| 30 | mar. 15/12 | Bilan | R10 ép. 7 (bilan des 30 jours, chiffres réels) · K24-C (ou R03-B) · P3 | PO3 aux clients livrés le 8/12 | Bilan des créateurs : publications, ventes, conformité | Date limite de Noël retirée ou remplacée par « livraison après Noël » ; tapis thermique : sans stock à cette date, report à octobre 2027 (`brand.json`) ; **bilan écrit** (§3) | Porte 2 : ≥ 3 / jour sur 7 jours |

---

## 3. Bilan de J30 (à remplir)

| Indicateur | Cible nominale | Plancher | Réel | Décision si sous le plancher |
|---|---|---|---|---|
| Précommandes (J3-J9) | 20 | 5 | | Sous 5 : remboursement et retour au test (déjà appliqué à J9) |
| Conversion liste d'attente → précommande | ≥ 10 % | 3 % | | Revoir l'offre et la page de précommande |
| Délai réel moyen et 90e centile | ≤ 6 jours ouvrés | 7 | | Changer de mode d'envoi ; mettre à jour la promesse |
| Commandes par jour (J24-J30) | 3 | 1 | | Revue du contenu (07 §8.3), pas d'arrêt avant les critères de 04 §6.3 |
| Part des kits sur le site | ≥ 45 % | 30 % | | Retravailler le sélecteur d'offre |
| Taux de défaut à réception | ≤ 5 % | — | | Au-delà : second fournisseur (04 §6.3) |
| Créateurs ayant publié | 3 | 1 | | Réécrire M1, resserrer la grille |
| Vidéos d'affiliés conformes | 100 % | 95 % | | Fin de collaboration pour les récidivistes |
| Réclamations et litiges | < 0,5 % | 1 % | | Revue du SAV et des délais |
| Trésorerie disponible | ≥ 0 € sans découvert | — | | Plafonner les ventes TikTok Shop au stock payé |

---

## 4. Règles de décalage

| Événement | Effet sur le calendrier |
|---|---|
| Porte 1 non franchie le 15/11 | Deux semaines de contenu supplémentaires sur le meilleur produit ; J1 devient le 30/11. La date limite de Noël n'est plus tenable pour une précommande : l'offre de lancement devient « livraison début janvier », annoncée comme telle |
| Médiateur ou IDU non obtenus à J2 | L'ouverture (J3) attend leur obtention ; aucune vente sans eux |
| Moins de 10 précommandes à J5 | La commande du stock attend J9 ; les dates écrites sont décalées d'autant pour les nouvelles commandes, et celles déjà payées restent dans la limite de 30 jours |
| Stock en retard sur la date écrite | E-mail individuel avant la date : nouvelle date + annulation remboursée sous 14 jours si le client le souhaite |
| Vidéo virale (> 50 000 vues en 24 h) pendant la précommande | Pas de promesse au-delà du stock commandé : dates du lot suivant affichées ; commande fournisseur complémentaire seulement si la trésorerie le permet |
| Le tapis de fouille gagne le duel | Les scripts R sont remplacés par TF26-TF30 et 5 scripts de kits à écrire ; la date limite de Noël et les dates de stock sont recalculées avec le délai du fournisseur du tapis |
