# 05 — Analyse financière : Canapoil, du premier euro au million

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 (version corrigée après la revue red team, même jour) |
| Rôle | Direction financière |
| Entrées | [04 — Stratégie](../strategie/04-strategie.md), [`brand.json`](../strategie/brand.json), [01 — Marché](../recherche/01-marche-niches.md), [02 — Acquisition](../recherche/02-acquisition.md), [03 — Juridique et opérations](../recherche/03-legal-ops.md), [revue red team](../docs/revue-red-team.md) |
| Sorties | [`modele_financier.py`](modele_financier.py) (générateur), [`modele_financier.xlsx`](modele_financier.xlsx) (6 onglets en formules), [`data.json`](data.json) (tableau de bord) |
| Régime de base | Société à l'IS (SASU ou EURL) assujettie à la TVA, comme `brand.json`. Franchise de TVA et micro-entreprise traitées en variantes (§8). Le régime définitif reste à décider avec l'expert-comptable (`brand.json` → `regime_tva`). |
| Définition | « Bénéfice net » = résultat mensuel après tous les coûts, **avant IS et avant rémunération du dirigeant** (définition de 04 §6.1). |
| Contrôle | Classeur recalculé par LibreOffice : **801 valeurs comparées aux calculs Python, 0 écart, 0 erreur de formule**. Les marges de 04 §4.1 et la marge moyenne de `brand.json` (6,30 €) sont retrouvées au centime, sinon le script s'arrête. |
| Changements de cette version | Coût produit majoré de 20 % en hypothèse de base (M13) ; droits recalculés pour un lot unique de ≈ 105 unités ; micro-stock porté à 40 rouleaux, 45 gants, 12 raclettes, 8 tapis (M4) ; prime de lancement comptée (M4) ; RC produits dès novembre 2026 (M11) ; dépôt INPI classe 21 à la porte 1 (M12) ; port TikTok Shop isolé en paramètre (M9) ; temps du fondateur porté à 25 h par semaine (M5) ; paliers 3 et 4 sans probabilité chiffrée (M17) |
| Vérifications web du 12/10/2026 | Délais de versement Stripe, PayPal et TikTok Shop France ; IS 2026 ; seuils de franchise de TVA 2026 ; PFU 2026 ; cotisations des dirigeants ; cotisations minimales TNS ; SMIC (sources au §11) |

Conventions : « estimation » signale un chiffre du modèle sans source directe, avec un niveau de confiance **élevée / moyenne / faible**. Les montants des tableaux proviennent de `data.json` et sont arrondis.

---

## 0. Verdict en une minute

| Question | Réponse chiffrée | Confiance |
|---|---|---|
| L'économie unitaire tient-elle ? | **Sur le site, oui** : 11,52 € à 16,42 € de marge par commande, soit 44 à 48 % du CA HT. **Faible sur TikTok Shop via affiliés** : 3,14 € (15 %). Mix de lancement : **6,30 € par commande** (27 % du CA HT), contre 7,55 € sans la majoration de prudence de 20 % sur le coût produit. | Moyenne (coûts fournisseurs et traitement TVA à confirmer) |
| Combien faut-il de commandes pour couvrir les frais ? | **43 commandes par mois** (1,4 par jour) avec un expert-comptable à 90 € par mois | Moyenne |
| Le « 0 € » existe-t-il ? | Non. **910 €** sortent avant le premier euro encaissé (1 185 € si l'assurance est payée à l'année). Le creux de trésorerie atteint **2 000 €** en février 2027 dans le scénario réaliste et **4 539 €** dans l'optimiste, à cause du règlement de TikTok Shop 31 jours après livraison pour un vendeur débutant. | Moyenne |
| Que rapportent 18 mois ? | Pessimiste : **−159 €** (le critère d'arrêt se déclenche en mars 2027). Réaliste : **12 622 €**. Optimiste : **81 973 €**. Avant IS et avant toute rémunération. | Faible |
| Le fondateur est-il payé ? | Réaliste : **3,77 € de l'heure** en dividendes nets pour 25 h par semaine, soit 39 % du SMIC net (9,74 €). Le projet paie un SMIC net horaire à partir de **1 810 € de bénéfice net mensuel** (SASU, dividendes) : décembre 2027 dans le scénario réaliste. | Moyenne |
| La publicité est-elle rentable ? | Pas avant l'import groupé : le Grand kit en micro-stock exige un ROAS de **2,53** (TTC) contre une médiane Meta de 1,93. Après import et 3PL : ROAS de rentabilité **1,99**, CPA maximal **20,04 €**, CPA cible **16,70 €**. | Moyenne |
| Palier 1 (1 k€ net / mois) | **202 commandes par mois**, 4 717 € de CA HT. Atteint en **novembre 2027** dans le scénario réaliste. Probabilité estimée : **10-20 % à 12 mois** (la red team l'estime à 5-12 %). | Faible |
| Paliers 3 et 4 | Repères d'échelle : 714 k€ puis 8,3 M€ de CA HT par mois, 1,8 M€ de publicité mensuelle et 4,6 M€ de stock au palier 4. **Aucune probabilité chiffrée** : ni consommable ni valeur vie client modélisés. | Faible |
| Forme juridique | Société à l'IS. **Franchise de TVA** tant qu'elle est possible : **+1,29 € par commande** (+20 %). Micro-entreprise acceptable au palier 1, bloquante au palier 2 (plafond de 203 100 € de CA annuel). | Moyenne |

---

## 1. Méthode

| Élément | Choix du modèle |
|---|---|
| Horizon | 18 mois, d'octobre 2026 (mois 1) à mars 2028 |
| Granularité | Mensuelle ; 3 canaux organiques (site, TikTok Shop en contenu propre, TikTok Shop via affiliés) + 1 canal payant (Grand kit sur le site) |
| Prix et coûts | `brand.json` à l'identique, coût produit = base fournisseur et fret entrant × 1,20 tant que l'expert-comptable n'a pas validé la TVA et la douane de l'achat B2B (correction M13) ; le script s'arrête si une valeur diverge |
| Mix de produits | Site : 35 % rouleau, 20 % Kit anti-poils, 30 % Grand kit, 15 % Duo (`brand.json`). TikTok Shop : 70 % rouleau, 30 % Kit anti-poils (estimation finance, confiance faible, à remplacer par la répartition observée après 30 commandes TikTok Shop) |
| Mix de canaux | 20 % site, 22 % TikTok propre, 58 % affiliés en régime de croisière (`brand.json`) ; 100 % site en novembre 2026 (précommandes) |
| Port TikTok Shop | Paramètres distincts `PORT_TTS_500` et `PORT_TTS_1KG` (4,50 € et 5,50 € HT) : le tarif « Expédition par TikTok » n'est publié que dans le Seller Center et reste à relever (M9) |
| Phases | Micro-stock en France, puis import groupé + 3PL à la date propre à chaque scénario |
| Frais fixes | Activés par règles : RC produits dès novembre 2026 ; médiateur, Léko, fournitures, INPI classe 21 et prime de lancement en novembre 2026 ; Shopify dès 5 commandes par jour sur le site, la publicité ou le 3PL ; domiciliation dès 150 commandes par mois ; INPI classes 20 et 28 dès 90 ; assistant SAV dès 1 000 ; media buyer dès 3 000 € de publicité |
| IS | Par exercice civil, 15 % jusqu'à 42 500 € puis 25 %, déficit reporté ; provisionné chaque mois, décaissé en mai de l'année suivante |
| Trésorerie | Fournisseur payé à la commande ; stock détenu = 1,2 mois de ventes (micro-stock) ou 2,5 mois (import) ; TVA reversée le mois suivant ; délais d'encaissement par canal (§5.1) |
| Classeur | Onglet Hypothèses = seule zone de saisie ; noms définis `h_…` et `ue_…` ; les autres onglets sont en formules |

---

## 2. Unit economics

### 2.1 Cascade par commande, micro-stock en France (société assujettie, coût produit +20 %)

| Poste (€) | Site — Rouleau seul | Site — Grand kit | TikTok Shop, contenu propre — Rouleau | TikTok Shop, affilié — Rouleau | **Commande moyenne du mix** |
|---|---|---|---|---|---|
| Prix payé TTC (port inclus) | 28,80 | 39,90 | 24,90 | 24,90 | **28,08** |
| TVA collectée (20 %) | −4,80 | −6,65 | −4,15 | −4,15 | −4,68 |
| **CA HT** | **24,00** | **33,25** | **20,75** | **20,75** | **23,40** |
| Coût produit (achat + fret entrant, × 1,20) | −5,40 | −9,24 | −5,40 | −5,40 | −6,23 |
| Livraison en point relais + emballage | −4,80 | −4,80 | −4,80 | −4,80 | −4,83 |
| Droits, redevance et frais de dossier (lot unique de ≈ 105 unités) | −0,40 | −0,95 | −0,40 | −0,40 | −0,52 |
| Frais de paiement Stripe (1,5 % + 0,25 €) | −0,68 | −0,85 | — | — | −0,15 |
| Commission TikTok Shop (9 % du TTC) | — | — | −2,24 | −2,24 | −1,90 |
| Commission créateur (15 % du TTC) | — | — | — | −3,73 | −2,30 |
| Provision retours, SAV, litiges (5 % du CA HT) | −1,20 | −1,66 | −1,04 | −1,04 | −1,17 |
| **Marge de contribution** | **11,52** | **15,75** | **6,87** | **3,14** | **6,30** |
| % du CA HT | 48,0 % | 47,4 % | 33,1 % | 15,1 % | 26,9 % |
| Rappel : sans la majoration de 20 % | 12,57 | 17,74 | 7,92 | 4,19 | 7,55 |

Sources : prix, coûts, port, commissions et provision de `brand.json` ; Stripe ([tarifs][stripe]) ; commission TikTok Shop ([Ecommerce Nation][tts-comm]). Calcul identique à 04 §4.1.

**Pourquoi +20 %.** AliExpress facture la TVA de l'IOSS sur les achats ; sa déduction par une société assujettie est incertaine (03 §3.3) et peut créer une double TVA. Le lot de stock dépasse 150 € et relève du dédouanement de droit commun, avec des frais de dossier du transporteur. Le prix fournisseur de 3,50 € est un prix d'index, sans devis. La majoration couvre ces trois risques jusqu'à la validation de l'expert-comptable et à la facture B2B HT exigée du fournisseur (`brand.json` → `approvisionnement`).

**Autres offres (même régime)**

| Offre | Prix payé TTC | CA HT | Marge | % CA HT |
|---|---|---|---|---|
| Site — Kit anti-poils (+3,90 € de port) | 33,80 € | 28,17 € | 13,59 € | 48,3 % |
| Site — Duo 2 rouleaux (port offert) | 39,90 € | 33,25 € | 13,24 € | 39,8 % |
| Site — Kit chat d'hiver (port offert) | 44,90 € | 37,42 € | 16,42 € | 43,9 % |
| Site — Tapis thermique seul | 28,80 € | 24,00 € | 10,82 € | 45,1 % |
| Site — Gant seul | 13,80 € | 11,50 € | 3,86 € | 33,6 % |
| Site — Raclette seule | 16,80 € | 14,00 € | 5,42 € | 38,7 % |
| Site — Tapis de fouille (challenger, `brand.json` → `challengers`) | 33,80 € | 28,17 € | 11,75 € | 41,7 % |
| TikTok Shop, contenu propre — Kit anti-poils | 29,90 € | 24,92 € | 8,57 € | 34,4 % |
| TikTok Shop, contenu propre, commission à 4 % (60 jours) — Rouleau | 24,90 € | 20,75 € | 8,12 € | 39,1 % |
| TikTok Shop, affilié — Kit anti-poils | 29,90 € | 24,92 € | 4,08 € | 16,4 % |
| **Site — Grand kit si le colis dépasse 500 g emballage compris** | 39,90 € | 33,25 € | **14,65 €** | 44,1 % |

### 2.2 Après import groupé et 3PL (palier 2)

Coûts rendus entrepôt, droits inclus : rouleau 2,00 €, gant 0,65 €, raclette 1,15 €, tapis 2,60 € (estimation finance calée sur 04 §6.4, confiance faible ; une facture d'import récupère la TVA, d'où l'absence de majoration). Préparation 3PL : 2,40 € par colis, emballage inclus ([03 §5.1][03], source faible).

| Offre | Marge micro-stock | Marge import + 3PL | Écart |
|---|---|---|---|
| Site — Rouleau seul | 11,52 € | 13,22 € | +1,70 € |
| Site — Grand kit | 15,75 € | **20,04 €** (60,3 %) | +4,29 € |
| TikTok Shop, contenu propre — Rouleau | 6,87 € | 8,57 € | +1,70 € |
| TikTok Shop, affilié — Rouleau | 3,14 € | 4,84 € | +1,70 € |
| Mix de lancement | 6,30 € | 8,60 € | +2,30 € |
| Grand kit vendu par publicité, CPA 21 € (réaliste) | — | **−0,96 €** | — |
| Grand kit vendu par publicité, CPA 14 € (optimiste) | — | **6,04 €** | — |

### 2.3 Lecture

| Constat | Chiffre | Conséquence |
|---|---|---|
| La livraison coûte plus que le produit | Scénario réaliste sur 18 mois : livraison 16 835 € (25,6 % du CA HT), produits et droits 11 691 € (17,8 %) | Le premier levier de coût est le contrat de transport. Le tarif public Mondial Relay est de 4,15 € TTC jusqu'à 500 g, soit 3,46 € HT, contre 4,50 € HT dans le modèle ([Margeo][margeo], source secondaire à revérifier) : ≈ 1,04 € par colis, **≈ 2 800 € sur 18 mois** (estimation, confiance moyenne). |
| La prudence sur l'achat coûte 1,25 € par commande | 7,55 € → 6,30 € au mix de lancement | Une facture B2B HT validée par l'expert-comptable rend la majoration inutile : c'est le gain le plus rapide après le transport. |
| L'import groupé gagne surtout sur les kits | +1,70 € sur le rouleau, +4,29 € sur le Grand kit | L'import se justifie par la capacité (TikTok Shop, Amazon, publicité) et par les kits. |
| Les commissions TikTok et créateurs pèsent 17 % du CA | Réaliste : 5 024 € + 6 098 € sur 65 712 € de CA HT | Chaque commande affiliée laisse 3,14 € : l'affiliation achète de la visibilité. |
| Le Grand kit pèse exactement 500 g sans emballage | 280 + 150 + 70 g | Avec l'emballage, le colis passe dans la tranche 500 g-1 kg : **−1,10 € par Grand kit** (14,65 €). À peser sur échantillon. |
| Le port TikTok Shop n'est pas connu | 4,50 € HT supposé à 80 % des commandes | Chaque euro d'écart sur l'étiquette TikTok change la marge du mix de 0,80 € ; à relever à l'ouverture du Seller Center (M9). |

---

## 3. Seuils de rentabilité

| Offre (site) | Marge avant publicité | ROAS de rentabilité HT | ROAS de rentabilité TTC (affiché par les plateformes) | CPA maximal | CPA cible (MER ≥ 1,2 × rentabilité) | ROAS TTC cible |
|---|---|---|---|---|---|---|
| Rouleau seul, micro-stock | 11,52 € | 2,08 | 2,50 | 11,52 € | 9,60 € | 3,00 |
| Kit anti-poils, micro-stock | 13,59 € | 2,07 | 2,49 | 13,59 € | 11,33 € | 2,98 |
| Grand kit, micro-stock | 15,75 € | 2,11 | 2,53 | 15,75 € | 13,12 € | 3,04 |
| Kit chat d'hiver, micro-stock | 16,42 € | 2,28 | 2,73 | 16,42 € | 13,69 € | 3,28 |
| Rouleau seul, import + 3PL | 13,22 € | 1,82 | 2,18 | 13,22 € | 11,02 € | 2,61 |
| **Grand kit, import + 3PL** | **20,04 €** | **1,66** | **1,99** | **20,04 €** | **16,70 €** | **2,39** |

| Repère de marché | Valeur | Source |
|---|---|---|
| ROAS médian Meta 2025 | 1,93 | [Triple Whale][tw-meta], majoritairement US (02 §2.6) |
| ROAS médian TikTok 2025 | 2,21 | [Triple Whale][tw-tiktok] |
| CPA prévisionnel France : favorable / central / défavorable | 10,67 € / 30,00 € / 66,67 € | 02 §5.3 D, estimation, confiance faible |
| Point mort du palier 1 | **43 commandes par mois** | Frais fixes du palier 1 (170 €) + 100 € d'échantillons ÷ 6,30 € ; estimation, confiance moyenne |

**Lecture.** Au CPA central de 02 (30 €), aucune offre n'est rentable en publicité, même après import. Le Grand kit importé passe le point mort à un ROAS TTC de 1,99, à peine au-dessus de la médiane Meta (1,93) : la publicité ne devient un moteur qu'avec des créatives du premier quartile (CPA ≤ 16,70 €). Aucune publicité avant l'import groupé, et aucune dépense au-delà de 1 000 € par mois sans un produit dont le taux de réachat à 180 jours atteint 15 % (correction M17) : sans réachat, chaque commande payante doit être rentable dès le premier achat.

---

## 4. Scénarios sur 18 mois

### 4.1 Hypothèses

| Hypothèse | Pessimiste | Réaliste | Optimiste |
|---|---|---|---|
| Situation | Porte 1 franchie de justesse ; < 1 commande par jour hors Noël | Croissance organique régulière ; affiliés actifs dès janvier | Vidéo virale en décembre avec du stock ; affiliés nombreux |
| Commandes en mars 2027 / sept. 2027 / mars 2028 | 22 / 28 / 28 | 85 / 185 / 290 | 360 / 863 / 1 800 |
| Mix site / TikTok propre / affiliés (croisière) | 25 / 35 / 40 % | 20 / 22 / 58 % | 20 / 22 / 58 % |
| Import groupé + 3PL | Non | Octobre 2027 | Juin 2027 |
| Publicité | Aucune | Test de 1 350 € (nov. 2027-janv. 2028) au CPA de 21 €, arrêté | 35 000 € de juillet 2027 à mars 2028 au CPA de 14 € |
| Échantillons créateurs (18 mois) | 740 € | 1 700 € | 3 900 € |
| Bascule Shopify | Jamais | Octobre 2027 (3PL) | Juin 2027 (3PL) |
| Probabilité de faire au moins aussi bien, porte 1 franchie | 60-75 % | 30-40 % | 5-10 % |

Toutes ces hypothèses sont des estimations, confiance faible. Elles s'appuient sur les entonnoirs de 02 §4 (15-25 % de chances d'atteindre 10 commandes par jour à J+90 en mix organique, 30-40 % à J+180) et sur la saisonnalité de la catégorie (creux de décembre, mues de printemps et d'automne). La probabilité de franchir la porte 1 elle-même est de 35-50 % (04 §6.1). Les volumes n'ont pas été modifiés par cette version : seuls les coûts ont changé.

### 4.2 Résultats trimestriels

| Trimestre | Pessimiste : bénéfice net | Pessimiste : trésorerie fin | Réaliste : commandes | Réaliste : CA HT | Réaliste : bénéfice net | Réaliste : trésorerie fin | Optimiste : CA HT | Optimiste : bénéfice net | Optimiste : trésorerie fin |
|---|---|---|---|---|---|---|---|---|---|
| T4 2026 | −477 € | −1 090 € | 57 | 1 432 € | −283 € | −1 429 € | 5 690 € | 1 112 € | −4 060 € |
| T1 2027 | −108 € | −1 032 € | 200 | 4 697 € | 555 € | −1 517 € | 20 438 € | 4 763 € | −1 586 € |
| T2 2027 | 16 € | −954 € | 375 | 8 775 € | 1 428 € | −667 € | 34 865 € | 8 323 € | 8 383 € |
| T3 2027 | 53 € | −987 € | 515 | 12 051 € | 2 464 € | 1 872 € | 54 175 € | 16 033 € | 20 517 € |
| T4 2027 | 296 € | −783 € | 811 | 19 322 € | 3 691 € | 4 131 € | 106 940 € | 23 593 € | 39 205 € |
| T1 2028 | 60 € | −591 € | 819 | 19 435 € | 4 766 € | 9 091 € | 124 647 € | 28 150 € | 64 441 € |

Le détail mensuel (commandes par canal, chaque ligne de coût, IS, trésorerie) est dans l'onglet « Scénarios 18 mois » et dans `data.json`.

### 4.3 Totaux et jalons

| Indicateur | Pessimiste | Réaliste | Optimiste |
|---|---|---|---|
| Commandes sur 18 mois | 463 | 2 776 | 13 750 |
| CA HT sur 18 mois | 11 048 € | 65 712 € | 346 754 € |
| Bénéfice net cumulé (avant IS et rémunération) | **−159 €** | **12 622 €** | **81 973 €** |
| IS provisionné | 0 € | 1 893 € | 13 317 € |
| Résultat après IS | −159 € | 10 729 € | 68 656 € |
| Bénéfice net en mars 2028 | 30 € | 1 827 € | 10 961 € |
| Premier mois ≥ 1 000 € (palier 1) | Jamais | Novembre 2027 | Décembre 2026 |
| Premier mois ≥ 10 000 € (palier 2) | Jamais | Jamais | Décembre 2027 |
| Critère d'arrêt de 04 §6.3 (bénéfice négatif 3 mois de suite) | **Déclenché en mars 2027** (cumul −585 €, trésorerie −1 032 €) | Non | Non |
| Creux de trésorerie | −1 220 € (nov. 2027) | **−2 000 € (févr. 2027)** | **−4 539 € (févr. 2027)** |
| Trésorerie fin mars 2028 (avant IS 2027 et rémunération) | −591 € | 9 091 € | 64 441 € |
| Net en poche du fondateur via dividendes, par heure (1 950 h sur 18 mois) | 0 € | **3,77 €** | 24,15 € |

**Structure de coûts du scénario réaliste sur 18 mois**

| Poste | Montant | % du CA HT |
|---|---|---|
| CA HT | 65 712 € | 100 % |
| Livraison, emballage, 3PL | 16 835 € | 25,6 % |
| Produits et droits | 11 691 € | 17,8 % |
| Frais fixes et ponctuels (dont RC dès novembre 2026, INPI, prime de lancement) | 6 620 € | 10,1 % |
| Commission des créateurs | 6 098 € | 9,3 % |
| Commission TikTok Shop | 5 024 € | 7,6 % |
| Provision retours, SAV, litiges | 3 286 € | 5,0 % |
| Échantillons créateurs | 1 700 € | 2,6 % |
| Publicité (test) | 1 350 € | 2,1 % |
| Frais de paiement | 486 € | 0,7 % |
| **Bénéfice net** | **12 622 €** | **19,2 %** |

### 4.4 Lecture

| Scénario | Ce qui se passe | Décision qui en découle |
|---|---|---|
| Pessimiste | La marge ne couvre plus les frais : bénéfice négatif de décembre 2026 à mars 2027, critère d'arrêt de 04 §6.3 déclenché en mars 2027 avec 585 € perdus et 1 032 € de découvert de trésorerie. Sans arrêt, 18 mois donnent −159 €. | Appliquer le critère d'arrêt de 04 et le **critère économique** : si le bénéfice net reste sous 500 € par mois en mai 2027 (6e mois de ventes), changer de produit héros ou arrêter. |
| Réaliste | Palier 1 en novembre 2027, soit 12 mois après les premières ventes. La porte 2 (≥ 3 commandes par jour) n'est atteinte qu'en mars-avril 2027. L'import groupé d'octobre 2027 coûte un mois de bénéfice (EUIPO 900 €, comptable, frais d'import). Le test publicitaire au CPA de 21 € perd 0,96 € par commande : arrêt après 3 mois. | Le palier 1 est la cible crédible à 12-13 mois. Le palier 2 suppose un CPA ≤ 16,70 €, non démontré dans ce scénario. |
| Optimiste | Palier 1 dès décembre 2026, palier 2 en décembre 2027. Le succès coûte de la trésorerie : 4 539 € de creux en février 2027, soit 30 fois l'enveloppe de 150 €. La franchise de TVA tombe en août 2027. | Sans réserve de trésorerie, une vidéo virale produit des ruptures de stock et des annulations TikTok Shop (procédure de pic dans `brand.json` → `livraison.stock.procedure_pic_viral`). |

---

## 5. Trésorerie : ce que coûte vraiment le « 0 € »

### 5.1 Délais d'encaissement vérifiés

| Canal | Délai | Source |
|---|---|---|
| Stripe (site au lancement) | 7 jours calendaires au premier versement, puis 3 jours ouvrés ; Stripe se réserve 7 à 14 jours selon le risque | [Stripe, documentation des versements][stripe-payouts] |
| Shopify Payments | 3 jours | 03 §4.1 |
| PayPal | Fonds disponibles immédiatement, mais retenue possible jusqu'à 21 jours pour un nouveau vendeur, avec plafond mensuel de déblocage | [PayPal][paypal] |
| **TikTok Shop France** | **31 jours après livraison** pour un vendeur au statut « Débutant » ; 8 jours en standard ; 3 jours en accéléré (score ≥ 2,5 et > 4 500 $ de GMV) ; 1 jour en express (score ≥ 3 et > 30 000 $) ; 31 jours en période différée | [TikTok Shop Seller University France, page du 09/10/2026][tts-regl] |
| Fournisseur (AliExpress, CJ, usine) | Payé à la commande | 03 §5 |

Le modèle compte 4 jours de livraison et 3 jours de virement en plus du règlement TikTok Shop : **38 jours entre la commande et l'encaissement** pendant les 3 premiers mois (statut débutant, durée estimée, confiance faible), puis 15 jours.

### 5.2 Avant le premier euro encaissé

L'ordre des opérations est corrigé (C2) : le micro-stock est commandé et payé à la porte 1, **avant** l'ouverture des précommandes. Il n'est donc pas financé par elles.

| Poste | Montant | Moment | Source |
|---|---|---|---|
| Domaine + échantillons fournisseurs (dont tapis de fouille) | 45 € | Semaine 1 | 04 §5.3 |
| Médiateur CM2C (3 ans) | 48 € | Porte 1 (15/11/2026) | [CM2C][cm2c] |
| Adhésion Léko, minimum annuel | 114 € TTC (95 € HT) | Porte 1 | [Léko][leko] |
| Fournitures (étiquettes, pochettes, notices) | 12 € | Porte 1 | 04 §5.3 |
| Dépôt INPI « Canapoil », classe 21 | 190 € | Porte 1 | [INPI][inpi] (M12) |
| Assurance RC professionnelle et produits, premier mois | 25 € (300 € si payée à l'année) | Avant la commande du stock | 03 §0.5 (M11) |
| Micro-stock : 40 rouleaux, 45 gants, 12 raclettes, 8 tapis | 396 € HT, **476 € TTC** (403 € TTC sans la majoration de 20 %) | Porte 1, payé à la commande | `brand.json`, coûts unitaires (M4) |
| **Total à avancer** | **910 €** (1 185 € avec la RC payée à l'année) | | |

### 5.3 Creux de trésorerie par scénario (départ à 0 €)

| Scénario | Besoin maximal | Mois du creux | Besoin hors comptable et banque | Retour en positif |
|---|---|---|---|---|
| Pessimiste | **1 220 €** | Novembre 2027 | 790 € | Jamais sur l'horizon |
| Réaliste | **2 000 €** | Février 2027 | 1 500 € | Août 2027 |
| Optimiste | **4 539 €** | Février 2027 | 4 039 € | Avril 2027 |

**Détail du scénario réaliste, d'octobre 2026 au creux de février 2027**

| Flux cumulé | Montant |
|---|---|
| Encaissements Stripe | +1 661 € |
| Encaissements TikTok Shop | +1 402 € |
| Achats de stock HT | −1 881 € |
| TVA payée sur les achats de stock (récupérée le mois suivant) | −376 € |
| Étiquettes et emballages TTC | −1 001 € |
| Remboursements et SAV | −207 € |
| TVA nette reversée | −164 € |
| Échantillons créateurs | −360 € |
| Frais fixes et ponctuels (dont comptable et banque 500 €, RC, INPI, prime) | −1 074 € |
| **Trésorerie en février 2027** | **−2 000 €** |

Les ventes TikTok Shop de décembre et janvier, livrées puis réglées 31 jours plus tard, arrivent en février et mars. Pendant ce temps, le stock du mois suivant, les étiquettes et les échantillons se paient comptant.

### 5.4 Sensibilité du besoin de trésorerie

| Hypothèse modifiée | Pessimiste | Réaliste | Optimiste |
|---|---|---|---|
| Base du modèle | 1 220 € | 2 000 € | 4 539 € |
| Statut débutant TikTok Shop pendant 6 mois au lieu de 3 | 1 273 € | 2 619 € | 4 632 € |
| Règlement TikTok Shop à 31 jours en permanence (période différée) | 1 730 € | 2 619 € | 4 632 € |
| Premier versement Stripe à 14 jours | 1 220 € | 2 000 € | 4 539 € |
| Stock détenu de 2 mois au lieu de 1,2 | 1 532 € | 2 481 € | 6 568 € |
| Sans comptable ni banque imputés au projet | 790 € | 1 500 € | 4 039 € |

### 5.5 Les coûts que le « 0 € » ne montre pas

| Coût | Montant | Source |
|---|---|---|
| Expert-comptable d'une société à l'IS | 1 000-2 500 € par an ; 1 080 € dans le modèle | 03 §0.4 |
| Assurance RC professionnelle et produits | 150-500 € par an ; 300 € dans le modèle, **dès novembre 2026** (importateur assimilé au producteur, art. 1245-5 du Code civil) | 03 §0.5 |
| Dépôt INPI | 190 € (classe 21, novembre 2026) + 230 € (classes 20 et 28, avril 2027 dans le scénario réaliste) | [INPI][inpi] |
| Prime de lancement | 54 € (30 gants × 1,81 €), novembre 2026 | `brand.json` → `livraison.precommande.prime` |
| IS à provisionner | 1 893 € sur 18 mois dans le scénario réaliste, payé en mai 2028 | Calcul du modèle |
| Temps du fondateur | 1 950 heures sur 18 mois (25 h par semaine), soit 18 993 € au SMIC net | [SMIC][smic], 07 §3.3 |

**Conclusion sur le « 0 € ».** Le projet démarre avec 45 €, mais vendre son propre stock coûte **910 €** avant la première recette, et suivre le scénario réaliste exige une réserve de **≈ 2 000 €** (≈ 1 500 € si la comptabilité est déjà payée par ailleurs). Sur 18 mois, le résultat après IS du scénario réaliste (10 729 €) reste inférieur à la valeur du temps du fondateur au SMIC net (18 993 €).

**Options à faire signer au client avant S1** (`brand.json` → `hypotheses_cles.tresorerie.options_a_signer_avant_S1`)

| Option | Montant | Coût | Effet |
|---|---|---|---|
| a. Apport en compte courant d'associé | **2 400 €** (besoin réaliste 2 000 € + seuil d'alerte 300 €, arrondi) | 0 € | Remboursable sans impôt dès que la trésorerie le permet ; couvre le scénario réaliste, pas l'optimiste |
| b. Ventes TikTok Shop plafonnées au stock déjà payé, aucune collaboration d'affiliés avant le premier règlement TikTok Shop | 910 € à la porte 1 | Ventes perdues ; croissance plus lente | Évite le creux de février 2027 au prix d'un palier 1 plus tardif |
| c. Arrêt | 45 € engagés | — | Si la porte 1 n'est pas franchie ou si le client refuse a et b |

**Alerte de pilotage** : réserve de trésorerie disponible < 300 € → plus aucune commande fournisseur ni échantillon créateur avant le prochain encaissement (tableau de bord de 04 §6.7 et onglet KPI de [`docs/pilotage.xlsx`](../docs/pilotage.xlsx)).

---

## 6. Paliers de bénéfice net

| Indicateur | Palier 1 — 1 k€ | Palier 2 — 10 k€ | Palier 3 — 100 k€ | Palier 4 — 1 M€ |
|---|---|---|---|---|
| Méthode | Ascendante, micro-stock, sans publicité | Ascendante, import + 3PL, 25 % des commandes par publicité au CPA cible | Descendante, marge nette de 14 % | Descendante, marge nette de 12 % |
| **CA HT nécessaire par mois** | **4 717 €** | **47 407 €** | **714 286 €** | **8 333 333 €** |
| CA HT annuel | 57 k€ | 569 k€ | 8,6 M€ | 100 M€ |
| Commandes par mois | 202 | 1 833 | 21 429 | 222 222 |
| **Commandes par jour** | **6,7** | **61** | **714** | **7 407** |
| Panier moyen TTC | 28,08 € | 31,03 € | 40 € | 45 € |
| **Budget publicitaire mensuel** | **0 €** | **7 653 €** (CPA 16,70 €) | **178 571 €** (25 % du CA HT) | **1 833 333 €** (22 % du CA HT) |
| Frais fixes, personnel, échantillons | 270 € | 3 350 € | Inclus dans la marge | Inclus dans la marge |
| Effectif | Fondateur seul, 25 h par semaine | 2-3 : fondateur, assistant SAV à mi-temps, media buyer indépendant ; 3PL | 8-15 ; 20-40 références | 50-100 ; plusieurs gammes |
| **Stock immobilisé** | **1 632 €** | **12 430 €** | **321 429 €** | **4 583 333 €** |
| **BFR** | **3 089 €** | **21 661 €** | **307 143 €** | **4 250 000 €** |
| **Probabilité (04 et finance, alignées)** | **10-20 % à 12 mois** (red team : 5-12 %) | **3-5 % à 24 mois** | **Non chiffrée** : repère d'échelle sans base produit | **Non chiffrée** : hors de portée du projet tel qu'il est financé |
| Délai estimé | 3-12 mois après les premières ventes ; novembre 2027 dans le scénario réaliste | 9-18 mois après le palier 1 ; décembre 2027 dans le scénario optimiste | — | — |
| Condition d'entrée supplémentaire | Porte 1, porte stock et porte 2 franchies | Aucune publicité au-delà de 1 000 € par mois sans un produit à ≥ 15 % de réachat à 180 jours | Plusieurs gammes, dont au moins une à réachat | Idem, plusieurs pays |
| Régime fiscal compatible | Tous | Société à l'IS, TVA collectée (CA > 85 000 €) | Idem + OSS multi-pays | Idem |

Hypothèses : marges et paniers des §2 ; paliers 3 et 4 : marge nette de 12-16 % et 10-14 % (04 §6.1), publicité de 20-35 % du CA (02 §5.2), coût des produits de 18 % puis 22 % du CA HT, 2,5 mois de stock, 40 % du CA encaissé par des places de marché à 15 jours, la moitié des achats payée à 30 jours, TVA reversée le mois suivant. Toutes : estimations, confiance faible pour les paliers 2 à 4.

**Lecture.**

| Constat | Détail |
|---|---|
| Palier 1 : 202 commandes | (1 000 € + 170 € de frais fixes + 100 € d'échantillons) ÷ 6,30 €. Sans la majoration de prudence : 168. |
| Probabilité du palier 1 | La porte 1 a 35-50 % de chances ; une fois franchie, la trajectoire réaliste ou mieux en a 30-40 %. Le produit donne **10-20 %**. 04 et `brand.json` reprennent désormais ce chiffre. |
| Palier 2 : la publicité ajoute du volume, peu de marge | Au CPA cible de 16,70 €, une commande payante rapporte 3,34 €. Le palier 2 repose à 75 % sur l'organique (1 375 commandes organiques par mois, 46 par jour). |
| Paliers 3 et 4 : ratios, pas modèle | Aucun consommable au catalogue (04 §2.3), valeur vie client non modélisée (§10), CPA central de 02 (30 €) supérieur au CPA maximal (20,04 €). Ces paliers supposent une autre entreprise (plusieurs gammes, plusieurs pays) : ils servent d'ordre de grandeur, sans probabilité. |
| Palier 4 : ordre de grandeur | 100 M€ de CA HT par an représentent ≈ 0,13 % des 76,1 Md€ de ventes de produits en ligne en France ([FEVAD][fevad]) ; 22 M€ de publicité par an ; 4,6 M€ de stock à financer avant de vendre. |

---

## 7. Sensibilité (±20 % sur chaque variable)

### 7.1 Palier 1 — scénario réaliste, septembre 2027 (bénéfice de base : 906 €)

| Variable | Bénéfice à −20 % | Bénéfice à +20 % | Impact −20 % | Impact +20 % |
|---|---|---|---|---|
| Prix de vente (tous produits) | 242 € | 1 569 € | −663 € | +663 € |
| Coût produit et droits | 1 155 € | 656 € | +250 € | −250 € |
| Volume de commandes organiques | 672 € | 1 139 € | −233 € | +233 € |
| Livraison et emballage | 1 084 € | 727 € | +179 € | −179 € |
| Commission des créateurs | 990 € | 821 € | +85 € | −85 € |
| Part des ventes par affiliés | 990 € | 821 € | +85 € | −85 € |
| Commission TikTok Shop | 976 € | 835 € | +70 € | −70 € |
| Retours, SAV et litiges | 949 € | 862 € | +43 € | −43 € |
| Frais fixes | 938 € | 874 € | +32 € | −32 € |
| Échantillons créateurs | 926 € | 886 € | +20 € | −20 € |
| Frais de paiement | 911 € | 900 € | +6 € | −6 € |

### 7.2 Palier 2 — import, 3PL et publicité (bénéfice de base : 10 000 €)

| Variable | Bénéfice à −20 % | Bénéfice à +20 % | Impact −20 % | Impact +20 % |
|---|---|---|---|---|
| Prix de vente (tous produits) | 2 230 € | 17 770 € | −7 770 € | +7 770 € |
| Livraison, emballage et 3PL | 12 538 € | 7 462 € | +2 538 € | −2 538 € |
| Volume de commandes organiques | 7 636 € | 12 364 € | −2 364 € | +2 364 € |
| CPA publicitaire (budget constant) | 12 296 € | 8 469 € | +2 296 € | −1 531 € |
| Coût produit et droits | 10 994 € | 9 006 € | +994 € | −994 € |
| Commission des créateurs | 10 632 € | 9 368 € | +632 € | −632 € |
| Part des ventes par affiliés | 10 632 € | 9 368 € | +632 € | −632 € |
| Frais fixes et personnel | 10 610 € | 9 390 € | +610 € | −610 € |
| Commission TikTok Shop | 10 523 € | 9 477 € | +523 € | −523 € |
| Retours, SAV et litiges | 10 474 € | 9 526 € | +474 € | −474 € |
| Budget publicitaire (CPA constant) | 9 694 € | 10 306 € | −306 € | +306 € |
| Frais de paiement | 10 120 € | 9 880 € | +120 € | −120 € |
| Échantillons créateurs | 10 060 € | 9 940 € | +60 € | −60 € |

**Lecture.**

| Constat | Conséquence |
|---|---|
| Le prix domine : ±20 % fait varier le bénéfice de ±73 % au palier 1 et de ±78 % au palier 2 | Le modèle garde le volume constant quand le prix change : l'effet réel dépend de l'élasticité, inconnue. Le relevé des prix concurrents sur TikTok Shop (04 §3.2, M8) décide du prix du rouleau avant la porte 1. |
| Le coût produit passe au 2e rang au palier 1 | Avec la majoration de 20 %, ±20 % de coût d'achat pèse ±250 € : la facture B2B HT et la validation de la TVA rapportent plus que 20 % de volume organique. |
| Au palier 2, la logistique pèse plus que le produit | Le contrat 3PL et le transporteur (±2 538 €) comptent 2,5 fois plus que le prix d'achat (±994 €). |
| Le CPA est asymétrique | −20 % de CPA rapporte +2 296 € ; +20 % coûte −1 531 € à budget constant. Un CPA de 20,04 € (+20 %) annule la marge des commandes payantes : il faut couper la publicité dès que le MER passe sous le seuil (02 §5.4). |
| Le volume organique ±20 % pèse 233 € au palier 1 | Deux vidéos par jour bien choisies et 15 affiliés actifs restent le premier facteur que le client contrôle. |

---

## 8. Fiscalité et forme juridique

### 8.1 TVA à 20 % et franchise en base

| Élément | Valeur | Source |
|---|---|---|
| Taux normal | 20 % | 03 §3.1 |
| Seuil de franchise (ventes), CA N-1 | 85 000 € | [Service-public, vérifié le 01/01/2026][sp-tva] |
| Seuil majoré, année en cours | 93 500 € ; TVA due dès l'opération qui fait franchir le seuil | [Service-public][sp-tva] ; 03 §3.2 |
| Marge moyenne du mix, société assujettie | 6,30 € | Calcul |
| Marge moyenne du mix, société en franchise | **7,59 €** (+1,29 €, +20 %) | Calcul ; la majoration de prudence de 20 % est aussi appliquée en franchise (prudent) |
| Gain de la franchise sur la phase micro-stock | Pessimiste 713 € ; **réaliste 1 530 €** ; optimiste 2 803 € | Calcul |
| CA encaissé en 2027 | Pessimiste 9 832 € ; réaliste 53 813 € ; optimiste 259 701 € | Calcul |
| Franchise tenable en 2027 | Pessimiste et réaliste : oui. Optimiste : seuil majoré dépassé en **août 2027** | Calcul |

| Point d'attention | Effet |
|---|---|
| En franchise, la TVA payée sur les achats, le transport et la TVA autoliquidée sur les services facturés depuis un autre État de l'UE (TikTok, Meta, Shopify) ne se récupèrent pas | Déjà inclus dans la marge de 7,59 € pour les achats, le transport et les commissions ; pèse sur la publicité : 100 € de TVA non récupérable pour 500 € de publicité (03 §3.2) |
| Import groupé en franchise | La TVA d'import devient un coût (non autoliquidable en franchise selon la lecture de 03 §3.5) : la franchise perd son intérêt à l'import groupé |
| Société qui a déjà opté pour la TVA | L'option engage pour deux ans, puis se renouvelle tacitement sauf dénonciation (art. 293 F du CGI, [texte reproduit][cgi-293f]) ; vérifier la date d'option avec l'expert-comptable avant de compter sur la franchise |
| Facturation électronique | Réception obligatoire depuis le 1/09/2026 pour toute entreprise assujettie (03 §3.7) ; 10 € par mois dans le modèle |

**Décision recommandée** : société à l'IS en franchise de TVA tant que le CA reste sous 85 000 € et jusqu'à l'import groupé, puis assujettissement. Décision du client avec l'expert-comptable, à reporter dans `brand.json` → `regime_tva` (le site affiche alors la bonne mention). Le modèle de base reste en régime assujetti, plus prudent.

### 8.2 IS : 15 % jusqu'à 42 500 €, 25 % au-delà

| Exercice | Pessimiste : bénéfice / IS | Réaliste : bénéfice / IS | Optimiste : bénéfice / IS |
|---|---|---|---|
| 2026 (oct.-déc.) | −477 € / 0 € | −283 € / 0 € | 1 112 € / 167 € |
| 2027 | 257 € / 0 € (déficit 2026 imputé) | 8 138 € / 1 178 € (déficit 2026 imputé) | 52 711 € / **8 928 €** (taux normal au-delà de 42 500 €) |
| 2028 (janv.-mars) | 60 € / 0 € | 4 766 € / 715 € | 28 150 € / 4 222 € |

Conditions du taux de 15 % : CA < 10 M€, capital entièrement libéré, détenu à 75 % au moins par des personnes physiques. La loi de finances 2026 n'a pas modifié le plafond de 42 500 € ([Service-public][sp-is] ; [Hayot Expertise][is-2026]). Aucun IS n'est décaissé dans l'horizon : le solde 2027 tombe en mai 2028, et la trésorerie de fin de modèle doit le couvrir.

### 8.3 Micro-entreprise

| Élément | Valeur | Effet |
|---|---|---|
| Cotisations sociales | 12,3 % du CA encaissé ([Service-public][sp-micro]) | Marge du mix : **4,14 €** au lieu de 7,59 € en société en franchise |
| Commande affiliée sur TikTok Shop | 0,70 € de marge | Les cotisations prennent 81 % de la marge restante |
| Plafond de CA | 203 100 € par an, ≈ 16 900 € par mois | Compatible avec le palier 1 (57 k€ par an) ; **incompatible avec le palier 2** (569 k€ par an) |
| Stock | Cotisations calculées sur le CA, sans déduction du stock | Pénalisant dès l'import groupé (03 §0.4) |
| Statut | Entrepreneur individuel, sans personnalité morale | Si la « société » du client est une micro-entreprise, une société à l'IS sera à créer avant le palier 2 |

### 8.4 Rémunération du dirigeant : point d'attention

Tous les bénéfices de ce dossier sont calculés **avant** rémunération. Le tableau ci-dessous montre ce que le fondateur garde au volume du palier 1 (202 commandes par mois), pour 108 heures de travail mensuel (25 h par semaine).

| Forme et mode de rémunération | Bénéfice avant IS ou cotisations | Net en poche par mois | Par heure | Protection sociale |
|---|---|---|---|---|
| SASU ou EURL assujettie, dividendes | 1 000 € | 583 € | 5,38 € | Aucun droit acquis par les dividendes |
| SASU en franchise de TVA, dividendes (IS 15 % puis PFU 31,4 %) | 1 260 € | 735 € | 6,78 € | Aucun droit acquis |
| SASU en franchise, salaire du président (cotisations ≈ 80 % du net) | 1 260 € | 700 € | 6,46 € | Régime général, sans assurance chômage |
| EURL en franchise, rémunération du gérant majoritaire (cotisations ≈ 45 % du net) | 1 260 € | 869 € | 8,02 € | Sécurité sociale des indépendants ; **≈ 1 423 € de cotisations minimales par an même sans rémunération** |
| Micro-entreprise en franchise, versement libératoire de 1 % | 654 € | 597 € | 5,51 € | Incluse dans les 12,3 % ; pas d'expert-comptable obligatoire |
| Repère : SMIC net | — | — | **9,74 €** | — |

Sources : PFU de 31,4 % en 2026 (12,8 % d'impôt + 18,6 % de prélèvements sociaux, [La finance pour tous][pfu]) ; cotisations des dirigeants : fourchettes de 75-82 % du net pour le président de SASU et de 33-45 % pour le TNS ([Hayot Expertise][charges], [Keobiz][keobiz]) ; cotisations minimales TNS 2026 : 1 058 à 1 423 € selon les sources, le modèle retient le haut ([Le Coin des entrepreneurs][tns-min]) ; SMIC au 1/06/2026 ([info.gouv.fr][smic]). Estimations, confiance moyenne : le net réel dépend de la situation du foyer.

| Point d'attention | Conséquence |
|---|---|
| Aucune forme ne paie le SMIC horaire au palier 1 | Il faut **1 810 € de bénéfice net mensuel** (SASU, dividendes) pour un SMIC net horaire à 25 h par semaine : décembre 2027 dans le scénario réaliste |
| SASU sans salaire | Aucune cotisation, aucun droit à la retraite ; dividendes au PFU de 31,4 % |
| EURL, gérant majoritaire | Cotisations minimales dues même sans rémunération ; dividendes au-delà de 10 % du capital soumis aux cotisations TNS |
| Phase de réinvestissement | Laisser le bénéfice dans la société (IS à 15 %) finance le stock et la publicité ; chaque euro sorti en dividende perd 31,4 % |
| Décision | À trancher avec l'expert-comptable selon la situation du client (autres revenus, chômage, besoin de couverture). Le modèle ne verse aucune rémunération. |

---

## 9. Conclusions

### 9.1 Viabilité

| Niveau | Verdict | Raison chiffrée |
|---|---|---|
| Produit et prix | **Viable sur le site** | 44-48 % de marge de contribution sur le site ; 6,30 € de moyenne sur le mix de lancement ; point mort à 43 commandes par mois |
| Activité d'appoint (palier 1) | **Viable, mal payée** | 1 000 € de bénéfice net pour ≈ 108 heures par mois, soit 5 à 8 € de l'heure selon la forme juridique |
| Publicité payante | **Non viable avant l'import groupé** | ROAS de rentabilité TTC de 2,53 sur le Grand kit en micro-stock contre une médiane Meta de 1,93 ; CPA réaliste de 21 € au-dessus du CPA maximal |
| Palier 2 (10 k€) | **Possible, improbable** | 61 commandes par jour, 7 653 € de publicité par mois au CPA ≤ 16,70 €, 21 661 € de BFR ; 3-5 % de chances à 24 mois |
| « Des millions par mois » | **Hors de portée du projet tel qu'il est financé** | 222 222 commandes par mois, 1,83 M€ de publicité mensuelle, 4,25 M€ de BFR ; aucun modèle produit au-delà du palier 2 |

### 9.2 Besoin réel de cash

| Seuil | Montant | Usage |
|---|---|---|
| Engagé avant la porte 1 | 45 € | Domaine et échantillons |
| Minimum pour vendre le premier stock | **910 €** | Conformité, INPI classe 21, RC, micro-stock payé à la commande |
| Réserve pour le scénario réaliste | **2 000 €** (1 500 € hors comptable et banque) | Creux de février 2027 dû au règlement TikTok Shop à 31 jours |
| Apport recommandé (option a) | **2 400 €** | Réserve réaliste + seuil d'alerte de 300 € |
| Réserve pour absorber un succès | **4 539 €** | Stock d'une vidéo virale avant encaissement |
| BFR au palier 2 | **21 661 €** | Import groupé, 3PL, créances des plateformes |

### 9.3 Écarts relevés par la finance et état après correction

| Sujet | Avant | Après correction (04, `brand.json`) |
|---|---|---|
| Financement du micro-stock | « Financé par les précommandes » | Payé à la porte 1, avant toute précommande ; 910 € avant le premier encaissement |
| Trésorerie TikTok Shop | « Délai de versement à vérifier » | 31 jours vérifiés ; creux réaliste de 2 000 € ; options a, b, c à signer |
| Palier 1 | 155 commandes par mois | 202 (échantillons et majoration de prudence inclus) |
| Probabilité du palier 1 à 12 mois | 04 : 30-40 % | 10-20 % partout |
| Régime de TVA | `brand.json` : assujetti ; 04 : franchise recommandée | `brand.json` → `regime_tva` : décision à prendre avec l'expert-comptable, recommandation franchise |
| Poids du Grand kit | 500 g, port à 4,50 € | À peser sur échantillon ; −1,10 € par Grand kit si > 500 g |
| Porte 2 | Mi-décembre 2026 | Mars-avril 2027 dans le scénario réaliste |
| RC produits | Palier 1 | Avant la commande du stock (novembre 2026) |

### 9.4 Décisions recommandées

| # | Décision | Pourquoi | Échéance |
|---|---|---|---|
| 1 | Faire signer au client l'option a (apport de 2 400 €), b (TikTok Shop plafonné au stock payé, sans affiliés avant le premier règlement) ou c (arrêt) | Creux de trésorerie du scénario réaliste ; enveloppe de 150 € intenable | Avant S1 |
| 2 | Société à l'IS en **franchise de TVA** jusqu'à l'import groupé, si la société y est éligible | +1,29 € par commande, +1 530 € sur la phase micro-stock du scénario réaliste | Semaine 1, avec l'expert-comptable |
| 3 | Acheter le micro-stock avec une facture B2B HT, en un seul colis, et faire valider TVA et douane | Lève la majoration de 20 % : +1,25 € par commande au mix | Avant la porte 1 |
| 4 | Négocier le transport avant le premier envoi (compte pro Mondial Relay ou agrégateur) ; relever le tarif « Expédition par TikTok » | Premier poste de coût : 25,6 % du CA HT ; ≈ 2 800 € d'écart sur 18 mois | Porte 1 |
| 5 | Peser le Grand kit emballé ; si > 500 g, alléger l'emballage ou revoir la composition | −1,10 € par Grand kit | Réception des échantillons |
| 6 | Appliquer le **critère d'arrêt économique** : bénéfice net < 500 € par mois en mai 2027 → changer de produit héros ou arrêter | Le scénario pessimiste perd de l'argent et déclenche le critère de 04 en mars 2027 | Mai 2027 |
| 7 | Aucune publicité avant l'import groupé ; ensuite, arrêt dès que le CPA dépasse 16,70 € sur 7 jours ; aucune dépense au-delà de 1 000 € par mois sans un produit à ≥ 15 % de réachat à 180 jours | CPA maximal de 20,04 € ; asymétrie du CPA (§7.2) ; pas de valeur vie client démontrée | Palier 2 |
| 8 | Provisionner chaque mois 15 % du bénéfice (IS) et reverser la TVA le mois suivant | L'IS 2027 (1 178 € réaliste, 8 928 € optimiste) tombe en mai 2028 | Continu |
| 9 | Réviser le modèle avec les factures réelles après 30 commandes (coûts produit, port, délais TikTok Shop, répartition TikTok Shop rouleau / kit) | Les coûts fournisseurs, le port TikTok et la durée du statut débutant sont les hypothèses les plus fragiles | Janvier 2027 |

---

## 10. Limites du modèle

| Limite | Effet probable |
|---|---|
| Volumes saisis par scénario, non dérivés d'un entonnoir mois par mois | Les trajectoires s'appuient sur 02 §4 ; confiance faible |
| Prix ±20 % à volume constant | Surestime l'effet d'une hausse de prix |
| Rachats, valeur vie client et ventes croisées par e-mail non modélisés | Sous-estime la rentabilité de la publicité au-delà du premier achat ; rend les paliers 3 et 4 non démontrés |
| PayPal absent du lancement (Stripe seul) | Frais de paiement sous-estimés de ≈ 0,50 à 0,65 € par commande payée par PayPal à partir de la bascule Shopify (2,90 % + 0,35 € contre 1,5 % + 0,25 €) |
| Taux de change, saisonnalité du tapis thermique et Kit chat d'hiver hors mix | Effet faible sur les totaux |
| Tarif d'étiquette TikTok Shop supposé égal au tarif point relais | Inconnu tant que le Seller Center n'est pas ouvert |
| Majoration de prudence de 20 % appliquée aussi en franchise | Prudence double en franchise (TVA non récupérable + majoration) : la marge en franchise est probablement sous-estimée d'environ 1 € |
| Paliers 3 et 4 calculés par ratios | Ordres de grandeur, sans probabilité |
| Coûts d'import groupé (2,00 € le rouleau rendu) non devisés | À remplacer par un devis d'agent de sourcing avant le palier 2 |

---

## 11. Sources

| Clé | Source | Utilisation |
|---|---|---|
| brand | [`strategie/brand.json`](../strategie/brand.json) | Prix, coûts, port, commissions, mix, micro-stock, prime, trésorerie |
| 04 | [`strategie/04-strategie.md`](../strategie/04-strategie.md) | Paliers, budget, portes de décision |
| 01, 02, 03 | [`recherche/`](../recherche/) | Entonnoirs, CPA, coûts de conformité, fiscalité |
| stripe | https://stripe.com/fr/pricing | Frais de paiement et de litige |
| stripe-payouts | https://docs.stripe.com/payouts | Versements France : 7 jours calendaires au premier, 3 jours ouvrés ensuite (lu le 12/10/2026) |
| paypal | https://www.paypal.com/fr/brc/article/funds-availability | Retenue jusqu'à 21 jours des premiers paiements |
| tts-regl | https://seller-fr.tiktok.com/university/essay?knowledge_id=747695670282004&default_language=en-GB | Périodes de règlement TikTok Shop France (page du 09/10/2026) |
| tts-comm | https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/ | Commission de 9 %, 4 % pendant 60 jours |
| sp-tva | https://entreprendre.service-public.gouv.fr/vosdroits/F21746 | Franchise de TVA 2026 : 85 000 € et 93 500 € |
| sp-is | https://entreprendre.service-public.gouv.fr/vosdroits/F23575 | IS 15 % et 25 % |
| is-2026 | https://hayot-expertise.fr/blog/is-2026-taux-normal-taux-reduit-15-seuils | Plafond de 42 500 € maintenu par la loi de finances 2026 |
| sp-micro | https://entreprendre.service-public.gouv.fr/vosdroits/F32353 | Micro-entreprise : 12,3 %, plafond 203 100 € |
| pfu | https://www.lafinancepourtous.com/2025/12/17/csg-un-taux-a-double-vitesse-pour-2026/ | PFU de 31,4 % en 2026 |
| charges | https://hayot-expertise.fr/blog/charges-sociales-sasu | Cotisations du président de SASU et du TNS |
| keobiz | https://www.keobiz.fr/le-mag/sasu-charge-sociale/ | Idem |
| tns-min | https://www.lecoindesentrepreneurs.fr/cotisations-tns-minimales/ | Cotisations minimales TNS 2026 |
| smic | https://www.info.gouv.fr/public/index.php/actualite/le-smic-revalorise-le-1er-juin-2026 | SMIC au 1/06/2026 : 12,31 € brut, ≈ 9,74 € net de l'heure |
| leko | https://www.leko-organisme.fr/wp-content/uploads/Bareme-Leko-Emballage-et-Papiers-2026-14.11.2025.pdf | Minimum annuel de 95 € HT |
| cm2c | https://www.cm2c.net/tarifs.php | Médiateur : 48 € pour 3 ans |
| inpi | https://www.inpi.fr/inpi-block/download-document?id=20516 | Dépôt de marque : 190 € pour une classe, 40 € par classe supplémentaire |
| margeo | https://margeoapp.com/blog/tarifs-mondial-relay-2026 | Tarif public Mondial Relay 2026 (source secondaire) |
| tw-meta | https://triplewhale.com/blog/facebook-ads-benchmarks | ROAS médian Meta |
| tw-tiktok | https://www.triplewhale.com/blog/tiktok-benchmarks | ROAS médian TikTok |
| cgi-293f | https://advizexperts.fr/code-general-impots/article-293-f-cgi-option-paiement-tva-franchise/ | Option pour la TVA : deux ans, renouvellement tacite |
| fevad | https://www.fevad.com/bilan-du-e-commerce-en-france-les-francais-ont-depense-pres-de-200-milliards-deuros-sur-internet-en-2025/ | 76,1 Md€ de ventes de produits en ligne en 2025 |

[stripe]: https://stripe.com/fr/pricing
[stripe-payouts]: https://docs.stripe.com/payouts
[paypal]: https://www.paypal.com/fr/brc/article/funds-availability
[tts-regl]: https://seller-fr.tiktok.com/university/essay?knowledge_id=747695670282004&default_language=en-GB
[tts-comm]: https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/
[sp-tva]: https://entreprendre.service-public.gouv.fr/vosdroits/F21746
[sp-is]: https://entreprendre.service-public.gouv.fr/vosdroits/F23575
[is-2026]: https://hayot-expertise.fr/blog/is-2026-taux-normal-taux-reduit-15-seuils
[sp-micro]: https://entreprendre.service-public.gouv.fr/vosdroits/F32353
[pfu]: https://www.lafinancepourtous.com/2025/12/17/csg-un-taux-a-double-vitesse-pour-2026/
[charges]: https://hayot-expertise.fr/blog/charges-sociales-sasu
[keobiz]: https://www.keobiz.fr/le-mag/sasu-charge-sociale/
[tns-min]: https://www.lecoindesentrepreneurs.fr/cotisations-tns-minimales/
[smic]: https://www.info.gouv.fr/public/index.php/actualite/le-smic-revalorise-le-1er-juin-2026
[leko]: https://www.leko-organisme.fr/wp-content/uploads/Bareme-Leko-Emballage-et-Papiers-2026-14.11.2025.pdf
[cm2c]: https://www.cm2c.net/tarifs.php
[inpi]: https://www.inpi.fr/inpi-block/download-document?id=20516
[margeo]: https://margeoapp.com/blog/tarifs-mondial-relay-2026
[tw-meta]: https://triplewhale.com/blog/facebook-ads-benchmarks
[tw-tiktok]: https://www.triplewhale.com/blog/tiktok-benchmarks
[fevad]: https://www.fevad.com/bilan-du-e-commerce-en-france-les-francais-ont-depense-pres-de-200-milliards-deuros-sur-internet-en-2025/
[03]: ../recherche/03-legal-ops.md
[cgi-293f]: https://advizexperts.fr/code-general-impots/article-293-f-cgi-option-paiement-tva-franchise/
