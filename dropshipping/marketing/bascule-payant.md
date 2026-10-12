# Bascule vers la publicité payante : quand et comment

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Entrées | [`brand.json`](../strategie/brand.json) (prix, coûts, frais de port, Stripe, commissions), [02 §5](../recherche/02-acquisition.md), [04 §6.4](../strategie/04-strategie.md), [05 §3 et §4](../finance/05-analyse-financiere.md) |
| Calculs | Script de la direction marketing qui relit `brand.json` et reproduit les marges de 04 §4.1 (12,57 €, 15,05 €, 17,74 €, 15,34 €, 18,62 €) et de 05 §2.2 après import (13,22 €, 20,04 €). Coûts d'import et de 3PL : estimation de la finance, confiance faible |
| Convention | ROAS = chiffre d'affaires attribué ÷ dépense publicitaire. « TTC » = valeur que remontent les pixels Meta et TikTok (montant payé, port compris). MER = CA total TTC ÷ dépense publicitaire totale |

---

## 0. Verdict

| Question | Réponse |
|---|---|
| Faut-il de la publicité au lancement ? | **Non.** Aucune offre en micro-stock n'est rentable au ROAS médian du marché : le Grand kit exige un ROAS de **2,25** sur le TTC, le rouleau seul **2,29**, contre une médiane de **1,93** sur Meta et **2,21** sur TikTok ([Triple Whale](https://triplewhale.com/blog/facebook-ads-benchmarks), [Triple Whale TikTok](https://www.triplewhale.com/blog/tiktok-benchmarks), données majoritairement américaines, 02 §2.6) |
| Quand ? | Quand les **8 conditions** du §1 sont réunies, dont l'import groupé avec 3PL. Date probable : **juin-juillet 2027** dans le scénario optimiste de la finance, **octobre-novembre 2027** dans le réaliste (05 §4.1) |
| Quelle offre ? | **Grand kit** sur le site après import : marge de **20,04 €** (60,3 % du CA HT), ROAS de rentabilité **1,99** TTC, CPA maximal **20,04 €**, CPA cible **16,70 €** |
| Sur quelle plateforme d'abord ? | **Meta** (campagne Ventes, puis Advantage+ Ventes) avec les vidéos organiques gagnantes. TikTok Spark Ads ensuite. GMV Max (TikTok Shop) en dernier |
| Combien pour tester ? | Vagues de **120 €** (3 ensembles × 10 € par jour × 4 jours), au plus 3 vagues, sans jamais dépasser 50 % de la trésorerie disponible |
| Probabilité que la publicité devienne rentable | Conditionnée à un CPA ≤ 16,70 € : seul le scénario « favorable » de 02 §5.3 (CPA 10,67 €) y parvient ; le scénario central (CPA 30 €) perd de l'argent sur toutes les offres. Le test réaliste de la finance, au CPA de 21 €, perd 0,96 € par commande et s'arrête après 3 mois (05 §4.4). Estimation : 25-35 % de chances qu'un test bien conduit atteigne la cible (confiance faible) |

---

## 1. Conditions de déclenchement (toutes requises)

| # | Condition | Seuil chiffré | Mesure | Origine |
|---|---|---|---|---|
| 1 | Demande prouvée en organique | ≥ 30 commandes organiques sur 14 jours glissants | Stripe + Seller Center | 02 §5.1 |
| 2 | Conversion du site | ≥ 2 % sur ≥ 1 000 sessions | Commandes ÷ sessions | 02 §5.1 ; en dessous, le CPC maximal rentable tombe sous 0,40 € (§2.3) |
| 3 | Marge de l'offre promue | ≥ 20 € par commande **et** ≥ 55 % du CA HT | Calcul du §2 avec les factures réelles | 02 §5.1. Seuls le Grand kit importé (20,04 €, 60,3 %) et le Kit chat d'hiver importé (22,12 €, 59,1 %) passent |
| 4 | Créatives éprouvées | ≥ 3 vidéos organiques avec rétention à 3 s ≥ 60 % et clics mesurables ; droits publicitaires signés pour les vidéos de créateurs | TikTok Studio ; avenant de droits ([createurs-affiliation.md](createurs-affiliation.md) §7.2, clause 4) | 02 §5.1 |
| 5 | Trésorerie | ≥ 600 € disponibles hors provisions d'IS et de TVA ; budget de test ≤ 50 % de ce montant | Relevé bancaire + tableur | 02 §5.1 ; 05 §9.4 |
| 6 | Mesure | Site sur Shopify ; pixel Meta + API Conversions et pixel TikTok + Events API installés par les applications officielles ; bannière de consentement conforme (refus aussi simple que l'acceptation) ; une commande test remontée | Gestionnaires d'événements | 02 §5.1 ; `brand.json` → `stack.conditions_bascule_shopify` ; 03 §1.9 |
| 7 | Logistique | Délai ≤ 7 jours ouvrés ; litiges < 0,5 % ; remboursements < 5 % | Tableur, Stripe | 02 §5.1 ; seuils de litige de 04 §6.3 |
| 8 | Coût de revient | Import groupé reçu et 3PL connecté ; coût livré ≤ 30 % du prix TTC | Factures | 04 §6.4 ; 05 §3 |

---

## 2. Seuils de rentabilité calculés depuis `brand.json`

### 2.1 Site, par offre

Hypothèses : société assujettie à la TVA ; port client 3,90 € TTC sous 35 € d'achat ; Stripe 1,5 % + 0,25 € ; provision retours et SAV 5 % du CA HT ; port 4,50 € HT jusqu'à 500 g, 5,50 € au-delà ; emballage 0,30-0,40 € (micro-stock) ou préparation 3PL 2,40 € (import).

**Micro-stock (situation de lancement)**

| Offre | Panier TTC | CA HT | Marge avant pub | % CA HT | ROAS de rentabilité HT | **ROAS de rentabilité TTC** | CPA maximal | CPA cible (MER ≥ 1,2 × rentabilité) | ROAS TTC cible | CPA pour 15 % de marge nette |
|---|---|---|---|---|---|---|---|---|---|---|
| Rouleau seul (+ port) | 28,80 € | 24,00 € | 12,57 € | 52,4 % | 1,91 | **2,29** | 12,57 € | 10,47 € | 2,75 | 8,97 € |
| Kit anti-poils (+ port) | 33,80 € | 28,17 € | 15,05 € | 53,4 % | 1,87 | **2,25** | 15,05 € | 12,54 € | 2,69 | 10,83 € |
| Grand kit | 39,90 € | 33,25 € | 17,74 € | 53,4 % | 1,87 | **2,25** | 17,74 € | 14,78 € | 2,70 | 12,75 € |
| Duo | 39,90 € | 33,25 € | 15,34 € | 46,1 % | 2,17 | **2,60** | 15,34 € | 12,78 € | 3,12 | 10,35 € |
| Kit chat d'hiver | 44,90 € | 37,42 € | 18,62 € | 49,8 % | 2,01 | **2,41** | 18,62 € | 15,52 € | 2,89 | 13,01 € |
| Grand kit si le colis emballé dépasse 500 g (05 §2.3) | 39,90 € | 33,25 € | 16,64 € | 50,0 % | 2,00 | **2,40** | 16,64 € | 13,87 € | 2,88 | 11,65 € |

**Après import groupé + 3PL (condition 8)**

| Offre | Panier TTC | Marge avant pub | % CA HT | ROAS de rentabilité HT | **ROAS de rentabilité TTC** | CPA maximal | CPA cible | ROAS TTC cible | CPA pour 15 % de marge nette |
|---|---|---|---|---|---|---|---|---|---|
| Rouleau seul | 28,80 € | 13,22 € | 55,1 % | 1,82 | **2,18** | 13,22 € | 11,02 € | 2,61 | 9,62 € |
| Kit anti-poils | 33,80 € | 16,45 € | 58,4 % | 1,71 | **2,05** | 16,45 € | 13,71 € | 2,47 | 12,22 € |
| **Grand kit** | 39,90 € | **20,04 €** | 60,3 % | 1,66 | **1,99** | **20,04 €** | **16,70 €** | **2,39** | 15,05 € |
| Duo | 39,90 € | 18,84 € | 56,7 % | 1,76 | **2,12** | 18,84 € | 15,70 € | 2,54 | 13,85 € |
| Kit chat d'hiver | 44,90 € | 22,12 € | 59,1 % | 1,69 | **2,03** | 22,12 € | 18,44 € | 2,44 | 16,51 € |

Formules (02 §5.3) : ROAS de rentabilité = panier ÷ marge avant publicité ; CPA maximal = marge avant publicité ; CPA cible = marge ÷ 1,2 (règle MER ≥ 1,2 × rentabilité de 02 §5.2) ; CPA pour 15 % de marge nette = marge − 0,15 × CA HT.

**Lecture** : même après l'import, aucune offre ne passe sous le ROAS médian de Meta (1,93). Le Grand kit s'en approche (1,99) et constitue la seule offre de test. Le rouleau seul reste exclu de l'acquisition froide.

### 2.2 TikTok Shop (GMV Max), contenu propre sans affilié

ROI calculé sur le GMV (montant payé TTC), commission TikTok de 9 %.

| Offre | Marge avant pub, micro-stock | ROI de rentabilité | ROI cible | Marge après import | ROI de rentabilité | ROI cible |
|---|---|---|---|---|---|---|
| Rouleau 24,90 € | 7,92 € | 3,14 | 3,77 | 8,57 € | 2,90 | 3,49 |
| Kit anti-poils 29,90 € | 10,03 € | 2,98 | 3,58 | 11,43 € | 2,62 | 3,14 |
| Grand kit 39,90 € | 15,00 € | 2,66 | 3,19 | 17,30 € | **2,31** | **2,77** |

GMV Max est le seul type de campagne pris en charge pour les publicités TikTok Shop depuis juillet 2025 ; TikTok recommande un budget total d'environ **40 fois le CPA moyen** pour sortir de la phase d'apprentissage, soit ≈ 40 conversions par boutique ([aide TikTok Ads](https://ads.tiktok.com/help/article/best-practices-for-setting-a-live-shopping-ads-budget)). Pour le Grand kit importé (CPA cible 14,42 €) : **≈ 577 €**. Si la vidéo promue est celle d'un affilié, sa commission s'ajoute et le ROI de rentabilité augmente d'autant.

### 2.3 CPC maximal rentable (Grand kit après import)

| Conversion du site | CPC maximal (CPA 20,04 €) | CPC cible (CPA 16,70 €) |
|---|---|---|
| 1,0 % | 0,20 € | 0,17 € |
| 1,5 % | 0,30 € | 0,25 € |
| 2,0 % | 0,40 € | 0,33 € |
| 3,0 % | 0,60 € | 0,50 € |

Hypothèse de CPC lien en France, achat optimisé : 0,40-1,00 € (02 §2.5, estimation, confiance moyenne). Il faut donc **≥ 2 % de conversion et un CPC ≤ 0,40 €**, ou ≥ 3 % et ≤ 0,60 €.

### 2.4 CPA prévisionnel

| Scénario (02 §5.3 D) | CPM | CTR lien | Conversion | CPC | CPA | Grand kit importé (CPA cible 16,70 €) |
|---|---|---|---|---|---|---|
| Favorable | 4 € | 1,5 % | 2,5 % | 0,27 € | 10,67 € | Rentable |
| Central | 6 € | 1,0 % | 2,0 % | 0,60 € | 30,00 € | Perte de 9,96 € par commande |
| Défavorable | 8 € | 0,8 % | 1,5 % | 1,00 € | 66,67 € | Perte de 46,63 € par commande |

La créative (CTR) et la page (conversion) décident de la rentabilité ; le budget n'y change rien.

---

## 3. Plan de test sur Meta

### 3.1 Structure et budgets

| Phase | Structure | Budget | Durée | Sortie |
|---|---|---|---|---|
| **Vague de test** | 1 campagne Ventes (événement Achat), budget au niveau des ensembles ; 3 ensembles, 1 angle par ensemble (preuve par tissu, voiture et tapis, cadeau ou hiver selon la saison), 2-3 accroches par ensemble ; ciblage large France 18-65 ans et plus ; placements Advantage+ ; exclusion des clients | **10 € par jour et par ensemble = 30 € par jour** | 4 jours ou 2 × CPA maximal dépensés par ensemble (≈ 40 €) | 1 ou 2 créatives gagnantes, ou arrêt |
| Vagues suivantes | Nouvelles créatives seulement (les angles perdants sont abandonnés) | 120 € par vague | 4 jours | **3 vagues au plus** ; à la troisième perte, retour à l'organique (04 §6.4) |
| **Consolidation** | Gagnants regroupés dans une campagne Advantage+ Ventes (qui remplace Advantage+ Shopping depuis le T1 2026, 02 §5.4), un seul ensemble ; 2-3 nouvelles créatives par semaine | Somme des budgets gagnants | Continu | Statut « apprentissage limité » accepté : sortir de l'apprentissage demande ≈ 50 achats par semaine et par ensemble (02 §5.4), soit ≈ 835 € par semaine au CPA cible |
| **Montée en budget** | Voir §3.3 | Plafond : dépense quotidienne ≤ 15 % de la trésorerie disponible (02 §5.2) | Continu | Volume |

Le montant minimal imposé par Meta est affiché dans le gestionnaire de publicités ; il n'a pas été revérifié pour cette note (recherche web épuisée le 12/10/2026).

### 3.2 Critères d'arrêt (par ensemble de publicités, Grand kit après import)

| Signal | Seuil d'arrêt | Mesuré après |
|---|---|---|
| CTR lien | < 0,8 % | 1 500-2 000 impressions |
| CPC lien | > 0,60 € (CPC maximal à 2 % de conversion × 1,5) | 50 clics |
| Ajout au panier | Aucun | 20 € dépensés (1 × CPA maximal) |
| Achat | Aucun | 40 € dépensés (2 × CPA maximal) |
| ROAS | < 1,99 TTC | 3 jours et ≥ 3 achats |
| Fatigue | Fréquence > 2,5 et CTR en baisse de 30 % par rapport aux 3 premiers jours | Hebdomadaire |
| CPA | > 16,70 € sur 7 jours glissants | Réduction de 30 % ; > 20,04 € → arrêt ([05 §9.4](../finance/05-analyse-financiere.md), décision 6) |

Seuils adaptés de 02 §5.4 (pratiques courantes de media buying), à recalibrer après 30 jours de données réelles.

### 3.3 Règles de montée et de baisse

| Situation (fenêtre glissante) | Action |
|---|---|
| ROAS TTC sur 3 jours ≥ **2,39** **et** MER sur 7 jours ≥ 1,2 × MER de rentabilité **et** ≥ 10 achats sur l'ensemble | **+20 %** de budget, au plus toutes les 72 heures |
| La hausse dégrade le CPA de plus de 20 % | Retour au budget précédent ; duplication de l'ensemble à budget égal |
| ROAS TTC sur 3 jours entre 1,99 et 2,39 | Budget maintenu ; 2 nouvelles créatives |
| ROAS TTC sur 3 jours < 1,99 | **−30 %** ; si 2 baisses successives, pause |
| MER sur 7 jours < MER de rentabilité | **Arrêt global** de la publicité (02 §5.2) |
| Contribution totale après publicité < contribution moyenne des 4 semaines précédant la publicité | Arrêt : la publicité remplace des ventes organiques au lieu d'en ajouter |

**MER de rentabilité** (calcul à refaire chaque semaine) = CA TTC total de la semaine ÷ (marge totale avant publicité de la semaine). Exemple avec le mix du palier 1 (panier moyen de 28,10 € TTC et marge moyenne de 7,55 €, `brand.json`) : MER de rentabilité ≈ 3,72 ; avec un mix porté par le Grand kit importé : ≈ 1,99.

---

## 4. TikTok

| Usage | Format | Budget | Règles |
|---|---|---|---|
| Trafic vers le site | **Spark Ads** sur les meilleures vidéos organiques (propres, ou de créateurs avec code d'autorisation et avenant de droits) | Minimums cités : plus de 50 $ par jour par campagne et 20 $ par jour par groupe d'annonces, d'après des guides qui reprennent l'aide TikTok de juillet 2026 ([Relevant Audience](https://www.relevantaudience.com/tiktok-ads/tiktok-ads-cost/), [Tlinky](https://tlinky.com/tiktok-ads-minimum-budget/)) ; montants en euros à vérifier dans le gestionnaire | Démarrage après une vague Meta gagnante (le site a prouvé sa conversion) ; mêmes critères d'arrêt qu'au §3.2 |
| Ventes TikTok Shop | **GMV Max** | ≈ 577 € de budget total pour sortir de l'apprentissage (Grand kit importé, §2.2) | Seulement sur le Grand kit importé, ROI cible ≥ **2,77** ; jamais sur le rouleau seul (ROI de rentabilité ≥ 2,90) |
| LIVE | Publicités LIVE | Hors périmètre du palier 2 | — |

---

## 5. Réinvestissement par palier

| Palier de bénéfice net mensuel | Part de la marge réinvestie en publicité | Échantillons, stock, créateurs | Réserve (impôts, imprévus) | Garde-fous |
|---|---|---|---|---|
| 0 → 1 k€ | **0 %** | 70 % | 30 % | Aucune publicité tant que le §1 n'est pas rempli |
| 1 → 10 k€ | 40 % | 30 % | 30 % | Dépense quotidienne ≤ 15 % de la trésorerie ; arrêt si MER sur 7 jours < MER de rentabilité |
| 10 → 100 k€ | 50-60 % | 20 % (marque propre, stock 3PL) | 20-30 % | Retour sur dépense en moins de 30 jours ; MER ≥ 1,2 × rentabilité |
| > 100 k€ | Pilotage par la contribution marginale | — | — | Media buyer recruté ; tests multi-pays |

Source : 02 §5.2 (proportions estimées, confiance moyenne). Au palier 2 de la finance, il faut ≈ 7 653 € de publicité par mois au CPA ≤ 16,70 € (05 §9.1).

---

## 6. Créatives, conformité et mesure

| Sujet | Règle |
|---|---|
| Source des créatives | Vidéos organiques qui ont rempli la condition 4 ; ordre de priorité : R09 (banc d'essai), K21 (Grand kit), R15 (voiture), R07 (comparatif), vidéos d'affiliés avec avenant |
| Allégations | Mêmes interdits que l'organique (`brand.json` → `allegations_interdites`) ; économie du Grand kit en texte, jamais en prix barré ; aucun compte à rebours sans date de fin réelle |
| Vidéos de créateurs | Mention « Publicité » ou « Collaboration commerciale » conservée ; diffusion en Spark Ads ou en publicité Meta en partenariat seulement après accord écrit et rémunération convenue (loi n° 2023-451, art. 5 et 8) |
| Consentement | Pixels et API de conversion alimentés uniquement pour les visiteurs qui ont accepté les traceurs publicitaires (position prudente, 03 §1.9) ; les données incomplètes qui en résultent sont compensées par le MER |
| Attribution | UTM sur chaque publicité ; question « Comment avez-vous connu Canapoil ? » dans PO1 ([emails.md](emails.md)) ; décisions prises sur le MER et la contribution, le ROAS plateforme servant à départager les créatives |

---

## 7. Liste de contrôle avant le premier euro dépensé

| # | Vérification | Fait |
|---|---|---|
| 1 | Les 8 conditions du §1 sont remplies et datées dans le tableur | |
| 2 | Les marges du §2 sont recalculées avec les factures réelles d'import et de 3PL | |
| 3 | Le Grand kit emballé est pesé (≤ 500 g ou port de 5,50 € intégré) | |
| 4 | Les seuils d'arrêt du §3.2 sont saisis comme règles automatiques dans le gestionnaire Meta | |
| 5 | La trésorerie du test (≤ 50 % du disponible) est isolée | |
| 6 | Les avenants de droits des vidéos de créateurs sont signés | |
| 7 | La bannière de consentement est testée (refus en un clic, aucun pixel avant consentement) | |
| 8 | Une commande test remonte dans Meta et TikTok avec la bonne valeur | |
| 9 | Le tableau de bord quotidien (dépense, CA, MER, contribution, CPA, CTR, fréquence) est prêt | |
