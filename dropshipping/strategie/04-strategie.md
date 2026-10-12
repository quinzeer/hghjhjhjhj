# 04 — Stratégie : Canapoil, du test à 150 € au chemin vers le million

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 (version corrigée après la [revue red team](../docs/revue-red-team.md), même jour) |
| Rôle | Direction de la stratégie |
| Entrées | [01 — Marché et niches](../recherche/01-marche-niches.md), [02 — Acquisition](../recherche/02-acquisition.md), [03 — Juridique et opérations](../recherche/03-legal-ops.md), pages légales de `recherche/pages-legales/` |
| Sortie machine | [`brand.json`](brand.json), lu par les agents site, finance et marketing |
| Conventions | Chaque chiffre porte une source (lien) ou la mention « estimation » avec une confiance **élevée / moyenne / faible**. « 01 §3.5 » renvoie à une section d'un dossier de recherche. Montants HT pour une société assujettie à la TVA, sauf mention contraire. Coûts produit majorés de 20 % tant que la TVA et la douane de l'achat ne sont pas validées par l'expert-comptable (`brand.json`). |
| Source unique | `brand.json` fait foi pour les prix, coûts, délais, phase de vente, dates, stock, identité légale, régime de TVA et délai de réponse du service client. Ce document cite ses champs. |
| Vérifications web du 12/10/2026 | Tarifs Shopify, Stripe, Cloudflare, Netlify, GitHub Pages, Vercel ; barème Léko 2026 ; barème INPI ; antériorités des noms de marque ; enregistrement des domaines (RDAP AFNIC et Verisign). |

---

## 0. Les décisions en une minute

| Sujet | Décision | Justification courte |
|---|---|---|
| Niche | Foyers avec chat ou chien, angle « cohabitation sur le canapé » | 60 % des Français ont un animal, dont 16,6 M de chats ([FACCO-Odoxa 2026][facco]) ; meilleurs scores de la grille 01 |
| Produit héros | **Rouleau anti-poils réutilisable**, 24,90 € TTC, prix confirmé ou ramené à 19,90 € après le relevé de 20 rouleaux concurrents sur TikTok Shop (§3.2) | Score 89/100 dans la matrice du §2.1 ; démonstration en 3 secondes ; micro-stock finançable |
| Challenger | Tapis de fouille lavable (score 87/100), testé en duel pendant la validation, avec sa fiche dans `brand.json` → `challengers` et sa page de liste d'attente (`/liste-attente/tapis-de-fouille/`) | Écart de 2 points : les inscriptions attribuées par produit et le taux de clics trancheront |
| Complémentaires | Gant de toilettage en silicone (9,90 €), raclette anti-poils tapis et voiture (12,90 €), tapis de fenêtre thermique (24,90 €, d'octobre à février) | Même acheteur, poids faible, aucune réglementation sectorielle |
| Offre phare | **Grand kit** rouleau + raclette + gant à 39,90 € : marge de 15,75 € par commande, la plus élevée des offres vendues toute l'année (§4.1) | Fait passer le panier au-dessus du seuil de livraison offerte |
| Marque | **Canapoil**, slogan « Les câlins sur le canapé, les poils à la poubelle. » | Aucune marque identique trouvée ; canapoil.fr et canapoil.com non enregistrés au 12/10/2026 (dépôt INPI et achat à confirmer) |
| Stack de lancement | Site statique codé sur Cloudflare Pages (gratuit) + paiement sur la page hébergée Stripe (liens de paiement) + TikTok Shop | 0 € de coût fixe, aucun abonnement qui court pendant les semaines sans vente |
| Stack de croissance | Shopify Basic (offre d'essai activée au moment de la bascule), puis Grow au-delà d'environ 34 500 € de CA mensuel | Intégrations publicitaires, 3PL et gestion de stock multicanal |
| Approvisionnement | Pas de vente avant le signal de demande ; à la porte 1, micro-stock de ≈ 105 unités commandé et payé **avant** d'ouvrir les précommandes, auprès d'un fournisseur qui identifie le fabricant par écrit et facture HT, importé en un seul colis et étiqueté par le client (importateur GPSR) | Seul schéma qui concilie TikTok Shop, le droit et des dates de précommande tenables (§5.4) |
| Budget | 45 € engagés avant le signal ; **910 €** à avancer à la porte 1 avant le premier euro encaissé ; **réserve de 2 000 €** dans le scénario réaliste (05 §5) | L'enveloppe de 150 € est intenable dès qu'on vend son propre stock. Le client signe avant S1 l'option a (apport de 2 400 €), b (TikTok Shop plafonné au stock payé, sans affiliés avant le premier règlement) ou c (arrêt à 45 €) (§5.3) |
| Objectif « millions par mois » | Traité comme un repère d'échelle, sans probabilité chiffrée : aucun modèle produit ne le porte au-delà du palier 2 | 1 M€ net suppose 7 à 10 M€ de CA HT par mois, plusieurs gammes dont au moins une à réachat, et une présence dans plusieurs pays (§6) |

---

## 1. Synthèse des recherches

### 1.1 Les faits qui conditionnent la stratégie

| # | Fait | Chiffre | Source | Conséquence retenue |
|---|---|---|---|---|
| 1 | Taille et panier du e-commerce français | 196,4 Md€ en 2025 (+7 %), dont 76,1 Md€ de produits ; panier moyen 62 € (−3 %) ; 50 % des transactions sous 30 € | [FEVAD][fevad], [Sellermania/FEVAD][sellermania] | Prix d'entrée entre 20 et 40 € : zone d'achat d'impulsion |
| 2 | Concentration | 158 200 sites ; 1 % font 78 % du CA | [Sellermania/FEVAD][sellermania] | 1 M€ net par mois suppose d'entrer dans ce 1 % et de sortir de France |
| 3 | Découverte des produits | TikTok est la 1re source d'information produit chez les 15-25 ans (66 %) ; 83 % ont acheté un produit découvert sur les réseaux | [OpinionWay pour Orisha][opinionway] | TikTok est le canal principal |
| 4 | Règles TikTok Shop France | Expédition depuis la France, remise au transporteur sous 2 jours ouvrés, livraison sous 4 jours ouvrés | [Politique TikTok Shop][tts-shipping] | Dropshipping depuis la Chine exclu de ce canal ; stock en France obligatoire |
| 5 | Rendement de l'organique | TikTok Shop convertit ≈ 0,042 % des vues en commandes ; la vidéo vers le site par le lien en bio ≈ 0,0034 %, soit 12 fois moins | 02 §4, estimation, confiance faible | TikTok Shop porte les ventes ; le site sert de vitrine, de capture d'e-mails et de canal à marge élevée |
| 6 | Commission TikTok Shop | 9 % (4 % pendant 60 jours pour une première boutique UE) | [Ecommerce Nation][tts-commission] | Avec un affilié à 15 %, il reste 4 à 6 € par commande (§4.1) |
| 7 | Douane sur les petits colis venus de Chine | 3 € par article depuis le 1/07/2026, puis redevance UE de 2 € par article distinct à partir du 1/11/2026 | [Ministère de l'Économie][douane-gouv], [Revenue.ie][revenue] | Chaque colis Chine-direct perd ≈ 5 € ; un lot importé en une fois répartit ce coût sur 20 unités |
| 8 | Effet sur les plateformes asiatiques | Commandes juin → juillet 2026 : Temu −50 %, AliExpress −37 %, Shein −15 % | [MacGeneration, panel Joko][macg] | Un stock en Europe devient un avantage de prix et de délai |
| 9 | Sécurité des produits (GPSR) | Le vendeur français qui fait venir un produit de Chine est, selon la lecture la plus probable, importateur : coordonnées sur le produit, documentation conservée 10 ans | [Règlement (UE) 2023/988][gpsr] ; 03 §2.1, estimation, confiance moyenne | Étiquetage possible à la main sur un micro-stock ; impossible en dropshipping AliExpress |
| 10 | Emballages (REP) | Adhésion Léko : minimum de 95 € HT facturé dès la signature ; IDU obligatoire, amende jusqu'à 30 000 € | [Barème Léko 2026][leko], [ADEME][ademe-idu] | Coût d'entrée fixe avant toute vente de stock propre |
| 11 | Médiateur de la consommation | CM2C : 48 € pour 3 ans | [CM2C][cm2c] | Obligatoire avant la première vente |
| 12 | Contrôles | DGCCRF : 141 sites de dropshipping en anomalie sur 251 contrôlés en 2023 | [DGCCRF][dgccrf] | Conformité intégrale dès la première vente |
| 13 | Animaux | 60 % des Français ont un animal ; 16,6 M de chats ; 9,6 M de chiens (−300 000) | [FACCO-Odoxa 2026][facco] | Chat en priorité, chien en second |
| 14 | Prix de référence du héros | Rouleaux réutilisables sur Amazon.fr de 14,95 à 25,99 € (n° 1 : ACE2ACE à 25,99 €) ; gants anti-poils de 5 à 13 € ; rouleau en silicone à 7,19 € chez Zoomalia | [Amazon.fr chiens][a-rouleaux-chien], [Amazon.fr chats][a-rouleaux-chat], [Zoomalia][zoomalia-rouleau] | 24,90 € se situe en haut de la fourchette, 56 à 67 % au-dessus des génériques livrés en 1-3 jours. Prix sous condition : relevé TikTok Shop avant la porte 1 (§3.2) ; si la médiane est sous 16 €, rouleau à 19,90 € et Grand kit seul mis en avant |
| 15 | Rentabilité de la publicité | ROAS médian 1,93 sur Meta et 2,21 sur TikTok ; rentable à partir d'environ 25-30 € de marge par commande et d'un panier de 45-55 € | [Triple Whale Meta][tw-meta], [Triple Whale TikTok][tw-tiktok] ; 02 §5.3, estimation, confiance moyenne | Aucune publicité avant les kits et l'import groupé |
| 16 | Fiscalité | Franchise de TVA jusqu'à 85 000 € ; micro-entreprise : 12,3 % du CA, plafond 203 100 € ; IS à 15 % jusqu'à 42 500 € | [Service-public TVA][sp-tva], [Service-public micro][sp-micro], [Service-public IS][sp-is] | La forme juridique change la marge de 1 à 4 € par commande (§4.1) |

### 1.2 Verdict sur la thèse de départ

| Élément de la thèse | Verdict | Données |
|---|---|---|
| Dropshipping comme phase de validation | **Amendé** | La validation se fait d'abord **sans vente** (contenu + liste d'attente), puis par précommandes sur un micro-stock importé par lot. Le dropshipping colis par colis depuis la Chine cumule +5 € de taxes par colis, un statut d'importateur intenable et l'exclusion de TikTok Shop (faits 4, 7, 9). |
| Acquisition 100 % organique au départ | **Confirmé** | TikTok Shop avec créateurs affiliés rapporte 12 fois plus de commandes par vue que le lien en bio (fait 5). Il impose un stock en France. |
| Créateurs rémunérés à la commission | **Confirmé, avec un coût d'échantillons** | 8 à 17 € par échantillon ; environ 450 € pour obtenir 15 affiliés actifs (02 §3.3, estimation, confiance moyenne). À financer par les marges. |
| Réinvestir les profits en publicité | **Confirmé sous condition** | Le rouleau seul (24,90 €) laisse 11,52 € de marge sur le site (48 % du CA HT) : le seuil de rentabilité publicitaire est un ROAS de 2,08 sur le HT, soit 2,50 sur le TTC affiché par les plateformes, au-dessus du ROAS médian de Meta (1,93). La publicité attend le Grand kit, l'import groupé, les 7 conditions de 02 §5.1 et, au-delà de 1 000 € par mois, un produit à ≥ 15 % de réachat à 180 jours. |
| Marque propre et stock en entrepôt UE dès validation | **Confirmé et avancé** | Le micro-stock en France est la première étape (palier 0). Le 3PL arrive vers 5 commandes par jour sur 14 jours (03 §5.6, estimation, confiance moyenne). |
| Extension multi-pays UE | **Confirmé, indispensable au-delà de 100 k€ net** | 1 M€ net par mois représenterait 0,11 à 0,16 % de tout le e-commerce de produits en France (01 §1.8, estimation, confiance moyenne). |

### 1.3 Contradictions entre les dossiers et arbitrages

| Sujet | 01 Marché | 02 Acquisition | 03 Juridique | Arbitrage retenu |
|---|---|---|---|---|
| Approvisionnement de départ | Micro-stock acheté sur AliExpress ou CJ | Dropshipping depuis un entrepôt UE pour le site, micro-stock dès le signal | Grossiste établi en France (le client reste distributeur, sans REP) | Aucun grossiste français proposant le rouleau n'a été trouvé (recherche web du 12/10/2026). Retenu : **pas de vente avant le signal**, puis micro-stock importé par lot, étiqueté au nom du client (importateur), avec adhésion Léko. |
| Plateforme du site | Shopify implicite | Shopify (applications d'e-mail et d'affiliation) | Shopify | Site statique + Stripe au lancement (0 € fixe), Shopify à la bascule (§5.3). Le kit d'import Shopify est préparé dès maintenant pour que la migration prenne une journée. |
| Prix du produit type | 24,90 € (rouleau) | 34,90 € (produit théorique) | 34,90 € (exemple fiscal) | 24,90 € pour le rouleau et 39,90 € pour le Grand kit. Le panier moyen visé sur le site (34,80 €) rejoint l'hypothèse de 02. |
| Budget de 150 € | Finance un micro-stock | ≈ 120 € pour l'acquisition | 48 € à 160 € de conformité | Les trois ne tiennent pas ensemble. 45 € avant la porte 1, 910 € à la porte 1, réserve de 2 000 € (05 §5) : options a, b ou c à signer par le client avant S1 (§5.3, §8). |
| Garantie | « Garantie de 2 ans clairement affichée » comme argument | — | Garantie légale de conformité obligatoire | La garantie légale est affichée comme une information. La présenter comme un avantage propre à l'offre est une pratique trompeuse ([directive 2005/29/CE, annexe I, point 10][dir-2005-29]). L'argument commercial devient le délai de 30 jours pour changer d'avis, qui va au-delà du minimum légal. |

---

## 2. Décision : niche, produit héros et produits complémentaires

### 2.1 Matrice de décision du produit héros

Notes de 1 (défavorable) à 5 (favorable). Score = Σ (poids × note) / 5, sur 100. Le critère C1 reprend le score de la grille 01 (≥ 75 → 5 ; 70-74 → 4 ; 67-69 → 3 ; 63-66 → 2 ; < 63 → 1). Les autres notes sont des jugements de la direction de la stratégie fondés sur les chiffres cités (estimation, confiance moyenne).

| Critère | Poids | P1 Rouleau anti-poils | P2 Tapis de fouille | P3 Hamac de fenêtre | P4 Tapis thermique | P5 Kit câbles | N6 Pilates |
|---|---|---|---|---|---|---|---|
| C1 Score marché 01 | 20 | 5 (77) | 5 (76) | 3 (69) | 3 (69) | 2 (66) | 1 (60, filtre F3) |
| C2 Démonstration en 3 s | 15 | 5 | 4 | 5 | 3 | 4 | 3 |
| C3 Micro-stock finançable (TikTok Shop) | 15 | 5 (≈ 95 € pour 20 u.) | 4 (≈ 102 € pour 12 u.) | 1 (> 150 €) | 5 (≈ 83 €) | 4 (≈ 103 €) | 1 |
| C4 Marge par commande sur le site | 10 | 4 (11,52 €) | 5 (11,75 €) | 3 (10,42 € en micro-stock) | 4 (10,82 €) | 4 (≈ 10 €) | 1 |
| C5 Potentiel de panier (kits, lots) | 10 | 4 (Grand kit 39,90 €) | 4 (lot 54,90 €) | 5 (44,90-59,90 €) | 2 | 2 | 4 |
| C6 Risque juridique et sécurité (5 = faible) | 15 | 3 (design à vérifier) | 4 (avertissement d'ingestion) | 2 (chute du chat) | 4 (aucune allégation) | 5 | 3 (REP sport, blessure) |
| C7 Calendrier oct.-déc. 2026 | 5 | 4 (mue d'automne, cadeaux) | 5 (pic en novembre) | 4 (pic en décembre) | 5 (saison d'octobre à février) | 3 | 3 |
| C8 Extension de gamme vers le même acheteur | 10 | 5 | 4 | 5 | 4 | 1 | 1 |
| **Score /100** | **100** | **89** | **87** | **66** | **73** | **64** | **40** |

**Décision : le rouleau anti-poils est le produit héros.** Il gagne sur la démonstration (avant/après sur un canapé en 3 secondes), le coût du stock et l'extension de gamme (gant, raclette, kits). Son point faible est juridique : des clones du ChomChom circulent partout et un dessin ou modèle enregistré dans l'UE reste possible (01 §3 bis). La vérification sur [DesignView][designview] est un critère d'arrêt (§2.5).

**Duel de validation.** Le tapis de fouille n'est qu'à 2 points. Sa fiche complète (prix envisagé 29,90 €, coût, avertissement d'ingestion, GPSR) est dans `brand.json` → `challengers`, et sa page de liste d'attente est en ligne dès S2. Les deux produits sont filmés pendant les semaines 4 et 5 (§6.2). Chaque inscription porte le produit qui intéresse le visiteur (champ caché transmis à Brevo). Si le tapis de fouille fait au moins 50 % de mieux sur les inscriptions qualifiées et le taux de clics produit, il devient le héros : son micro-stock est commandé à la porte 1 à la place de celui du rouleau. Saisonnalité : le tapis de fouille culmine en novembre (indice 1,30) quand la recherche « anti poils » est au creux de décembre (0,59) ; si le rouleau gagne, l'achat du stock principal est décalé à fin janvier 2027, avant la hausse de février.

### 2.2 Candidats écartés

| Candidat | Score 01 | Raison de l'écart | Statut |
|---|---|---|---|
| Bigoudis sans chaleur | 74 | Filtre F2 : prix courant de 6 à 14 € sur Amazon.fr | Écarté |
| Outils de nettoyage manuels | 70 | Filtre F2 : moins de 10 € chez Action et en grande surface | Écarté |
| Hamac de fenêtre | 69 (66 ici) | Stock de 10 unités supérieur à 150 € ; risque de chute du chat (GPSR) ; marge de 10,42 € seulement en micro-stock | Reporté au palier 1, après un test de charge filmé (20 kg pendant 72 h) |
| Bijoux en acier | 68 | Ni démonstration ni problème résolu ; demande en baisse de 3 % | Écarté |
| Kit câbles | 66 (64 ici) | Hors de la cible animaux ; demande faible ; achat unique | Écarté |
| Maquettes 3D en bois | 66 | Filtre F4 : designs protégés (ROKR, Robotime) | Écarté |
| Portraits d'animaux personnalisés | 65 | Demande faible hors période de fêtes ; concurrence d'applications d'IA | Réserve pour un T4 ultérieur |
| Fontaines à eau | 61 | Filtre F1 : appareil électrique (DEEE, basse tension) | Palier 2, avec fournisseur certifié |
| Pilates à domicile | 60 (40 ici) | Filtre F3 : coût livré supérieur à 60 % du prix ; REP sport | Première candidate d'une seconde marque après l'import groupé (01 §5.3) |
| Cuisine | 59 | Contact alimentaire (règlement (CE) 1935/2004) | Écarté |
| Rangement sans perçage, voyage, voiture | 53-62 | Demande en baisse (−14 à −31 %) ; prix de référence bas | Écarté |

### 2.3 Matrice des produits complémentaires

Critères : affinité avec l'acheteur du rouleau (30), hausse du panier ou de la marge (25), coût logistique marginal (15), conformité (15), stock finançable (15). Notes de 1 à 5, estimations de la stratégie, confiance moyenne.

| Candidat | Affinité (30) | Panier (25) | Logistique (15) | Conformité (15) | Stock (15) | **Score** | Décision |
|---|---|---|---|---|---|---|---|
| Gant de toilettage en silicone (70 g) | 5 | 3 | 5 | 5 | 5 | **90** | **Retenu** : vente additionnelle en un clic, prime de lancement |
| Raclette anti-poils en caoutchouc (150 g) | 4 | 3 | 4 | 5 | 5 | **81** | **Retenu** : couvre les surfaces où le rouleau est faible (tapis ras, sièges auto) |
| Tapis de fenêtre thermique (400 g) | 4 | 4 | 4 | 4 | 4 | **80** | **Retenu** : vente croisée saisonnière pour les chats, d'octobre à février |
| Plaid imperméable protège-canapé | 5 | 5 | 2 | 3 | 2 | 76 | Palier 2 (REP textile, poids) |
| Boules anti-poils pour lave-linge | 4 | 2 | 5 | 3 | 5 | 73 | Écarté : efficacité contestée (un lot noté 1,6/5 dans le relevé Amazon.fr du 12/10/2026) |
| Tapis de fouille (pour un acheteur de rouleau) | 2 | 4 | 3 | 4 | 3 | 62 | Challenger du héros, hors kits |
| Hamac de fenêtre | 4 | 5 | 1 | 2 | 1 | 61 | Palier 1, après test de charge |
| Recharges adhésives | 1 | 2 | 5 | 5 | 5 | 61 | Écarté : contredit la promesse « sans recharge » |

**Consommables.** Aucun consommable crédible n'existe à ce stade : le rouleau est réutilisable et les produits d'entretien chimiques relèvent d'autres réglementations. Le réachat viendra des kits « maison + voiture », du tapis thermique saisonnier et de l'extension de gamme au palier 2 (plaid, griffoir, protections de canapé).

### 2.4 Catalogue de lancement

| SKU | Produit | Rôle | Prix TTC | Disponibilité |
|---|---|---|---|---|
| CNP-ROU-01 | Rouleau anti-poils réutilisable | Héros | 24,90 € | Lancement |
| CNP-GAN-01 | Gant de toilettage en silicone | Complémentaire (vente additionnelle) | 9,90 € | Lancement |
| CNP-RAC-01 | Raclette anti-poils tapis et voiture | Complémentaire (kit) | 12,90 € | Lancement |
| CNP-TAP-01 | Tapis de fenêtre thermique, sans électricité | Complémentaire (saison) | 24,90 € | Lancement si le stock arrive avant le 15/12, vendu jusqu'à fin février ; étiquette de composition textile en français |
| CNP-FOU-01 | Tapis de fouille lavable (challenger) | Liste d'attente seulement | 29,90 € envisagé | Vendu seulement s'il gagne le duel de la porte 1 |

### 2.5 Ce qui ferait changer la décision

| Événement | Effet |
|---|---|
| Dessin ou modèle UE enregistré couvrant le rouleau ([DesignView][designview], [INPI][inpi-data]) | Le rouleau sort. Le tapis de fouille devient le héros ; la raclette et le gant restent en complémentaires. |
| Le tapis de fouille gagne le duel de la porte 1 avec ≥ 50 % d'écart | Il devient le héros ; les kits sont recomposés (tapis M + L, guide de jeux de flair). |
| L'échantillon de rouleau ne ramasse pas les poils sur 3 tissus courants (velours, microfibre, plaid) | Test du second fournisseur ; si l'échec se répète, le tapis de fouille passe en héros. |
| Fulfilled by TikTok ouvre en France, ou budget de stock ≥ 300 € | Le hamac remonte au rang 2 (panier élevé, contenu viral). |
| La redevance de 2 € s'applique par article et non par colis | Sans effet sur le micro-stock importé par lot ; pénalise les tests en Chine-direct, déjà exclus. |

---

## 3. Marque

### 3.1 Nom : trois options

Vérifications du 12/10/2026 : recherche web des marques et commerces identiques ou proches ; enregistrement des domaines interrogé par RDAP ([AFNIC][rdap-afnic] pour le .fr, [Verisign][rdap-verisign] pour le .com : réponse 404 = non enregistré). **Le dépôt INPI, la recherche d'antériorité sur [data.inpi.fr][inpi-data] et [TMview][tmview], et l'achat effectif des domaines restent à faire.**

| Option | Sens | Antériorités trouvées | Domaines .fr / .com | Forces | Faiblesses | Verdict |
|---|---|---|---|---|---|---|
| **Canapoil** | canapé + poil | Aucune marque, boutique ou site trouvé | Non enregistrés | Mot inventé, donc marque forte ; mémorable ; territoire clair (la vie avec un animal sur le canapé) | Prononciation difficile hors des pays francophones ; moins adapté à des produits loin de la maison | **Retenu** |
| Toutpoil | « de tout poil » | Salons de toilettage « A Tout Poils » à Colmar ([PagesJaunes][atoutpoils-colmar]) et « Atout Poils » à Saint-Malo ([chien.com][atoutpoils-stmalo]) ; atoutpoil.fr et .com enregistrés | Non enregistrés | Large : couvre tous les animaux et toute la gamme | Proximité phonétique avec des toiletteurs existants : risque d'opposition | Second choix |
| Poilette | diminutif de « poil » | Aucune | Non enregistrés | Doux, féminin | Confusion avec « toilette » ; image peu premium | Troisième choix |

Noms examinés puis écartés : **Maison Poilue** (concept store pour chiens et chats en activité sur [maisonpoilue.com][maisonpoilue], domaine .fr enregistré le 07/11/2025), **DeBonPoil** (marque de soins pour animaux distribuée par [Zoomalia][debonpoil]), **Moumoute** (domaines .fr et .com enregistrés ; marque de linge pour enfants [Moumout][moumout] très proche).

**Vérifications en S1**, avant la commande des échantillons : [TMview][tmview] et [data.inpi.fr][inpi-data] pour « Canapoil », [DesignView][designview] (classes de Locarno 04-02 brosses et 08-05 outils) pour le rouleau et le tapis de fouille, avec captures d'écran datées dans le dossier produit. **Dépôt INPI « Canapoil » en classe 21 (brosses, ustensiles de nettoyage) à la porte 1 : 190 €** ([barème INPI][inpi-bareme]), avant la première vente ; classes 20 (couchages pour animaux) et 28 (jouets pour animaux) à la porte 2, par un second dépôt (190 € + 40 €). Marque de l'Union européenne au palier 2 : 850 € pour une classe en ligne, 50 € pour la deuxième ([EUIPO][euipo-fees], montant confirmé par une source secondaire, confiance moyenne).

### 3.2 Promesse, slogan, positionnement

| Élément | Contenu |
|---|---|
| Slogan | **Les câlins sur le canapé, les poils à la poubelle.** |
| Promesse | Des outils simples pour partager le canapé avec son chat ou son chien et garder un intérieur présentable. Chaque produit est montré en vidéo, sans trucage, sur de vrais tissus. Expédition depuis la France. |
| Preuves | Vidéo par type de tissu (velours, microfibre, lin, plaid, siège auto), y compris les surfaces où le produit marche mal ; délai réel publié ; avis vérifiés uniquement ; coordonnées complètes de la société |
| Transparence d'origine | « Marque française. Produits fabriqués en Chine, contrôlés et expédiés depuis la France. » Aucun drapeau ni « made in France » (03 §1.7) |
| Prix | Milieu-haut de marché : au-dessus des génériques Amazon (14,95-15,99 €), au niveau du n° 1 (25,99 €) ([relevé Amazon.fr][a-rouleaux-chien]) |

**Carte de positionnement (prix × niveau de preuve)**

| Acteur | Prix du rouleau | Délai | Preuve et service | Position |
|---|---|---|---|---|
| Génériques Amazon.fr (PAKEWAY, Wouble, Veddelholzer) | 14,95-15,99 € | 1-3 jours (Prime) | Fiche standard, avis mélangés | Prix bas, sans marque |
| ACE2ACE (n° 1 Amazon.fr) | 25,99 € | 1-3 jours | Avis nombreux | Leader de catégorie |
| Partenaires zooplus | 17,59-25,99 € | 8-11 jours ouvrés | Faible | Catalogue |
| Vendeurs TikTok Shop France | **À relever avant la porte 1** : 20 premiers rouleaux réutilisables de l'onglet Boutique de l'application (prix, ventes affichées, délai), sans compte vendeur | Livraison sous 4 jours ouvrés exigée | Variable | Si la médiane est sous 16 € : rouleau testé à 19,90 € et Grand kit seul mis en avant ; marges recalculées dans `brand.json` |
| **Canapoil** | **24,90 € ; 39,90 € le Grand kit** | **3-6 jours ouvrés depuis la France** | **Démonstration par tissu, kits pensés par surface, 30 jours pour changer d'avis** | Spécialiste de la cohabitation canapé-animaux |

### 3.3 Personas

| | Camille, 29 ans — « chat d'appartement » | Julien et Sarah, 38 ans — « maison, chien, voiture » | Offreur de cadeau (secondaire) |
|---|---|---|---|
| Foyer | Locataire en ville, 1 ou 2 chats d'intérieur, canapé en velours ou en tissu | Maison, chien à poil mi-long, enfants, voiture familiale | Ami ou parent d'un propriétaire d'animal |
| Poids dans la population | 16,6 M de chats en France ([FACCO][facco]) | 9,6 M de chiens ([FACCO][facco]) | Saisonnier (novembre-décembre) |
| Canal | TikTok tous les jours, achat dans l'application (TikTok 1re source d'information produit des 15-25 ans, [OpinionWay][opinionway]) | Instagram, Facebook, Pinterest (67 % de femmes, 02 §1.6), recherche Google | TikTok, Instagram, Google |
| Déclencheur | Pull noir couvert de poils avant de sortir ; invités à la maison | Poils dans la voiture et sur le tapis du salon | Idée cadeau à moins de 40 € |
| Objections | « Encore un gadget qui ne marche pas » ; prix comparé à Amazon | Efficacité sur tapis et sièges auto ; délai | Délai avant Noël ; retour possible |
| Réponse de l'offre | Démonstration sur son type de tissu ; Kit anti-poils à 29,90 € | Grand kit à 39,90 € avec raclette ; livraison offerte | Date limite d'expédition affichée ; 30 jours pour changer d'avis |
| Panier visé | 24,90-29,90 € | 39,90 € | 39,90-44,90 € |

### 3.4 Ton

| À faire | À éviter |
|---|---|
| Phrases courtes, humour bienveillant envers les animaux et les maîtres | Moquerie, culpabilisation (« votre maison est sale ») |
| Montrer avant d'affirmer : chaque promesse a sa vidéo | Superlatifs invérifiables (« le meilleur », « 100 % des poils ») |
| Dire où le produit marche mal (cuir, soie, poils très courts incrustés) | Allégations de santé (« réduit les allergies », « stimule la circulation ») |
| Vouvoiement sur le site et au service client ; tutoiement possible sur TikTok et Instagram | Faux avis, fausse rareté, faux compte à rebours, prix barré sans référence réelle |
| Chiffres concrets : délai, poids, dimensions | Jargon technique non expliqué |
| Mention « Collaboration commerciale » sur toute vidéo de créateur | Vidéos de fournisseurs ou de tiers sans licence écrite |

### 3.5 Identité visuelle

| Jeton | Couleur | Usage | Contraste vérifié (WCAG 2.1) |
|---|---|---|---|
| primaire | `#B4492A` terracotta (velours de canapé) | Boutons d'achat, liens | Blanc sur primaire 5,35 : 1 ; primaire sur fond 4,93 : 1 |
| secondaire | `#2F4A3C` vert sauge foncé | Bandeaux, pied de page | Blanc sur secondaire 9,70 : 1 |
| fond | `#FAF5EE` crème | Fond de page | Texte sur fond 14,49 : 1 |
| surface | `#FFFFFF` | Cartes, formulaires | Texte sur surface 15,72 : 1 |
| texte | `#2B211B` brun très foncé | Texte courant | — |
| texte_secondaire | `#6A5B50` | Légendes, mentions | 6,00 : 1 sur fond |
| accent | `#E3A93B` moutarde (pelage) | Pastilles, étoiles d'avis, surlignage | Texte sur accent 7,49 : 1 (ne jamais écrire en blanc sur l'accent) |
| succes | `#2E6B47` | Confirmations, stock disponible | Blanc sur succès 6,34 : 1 |
| alerte | `#B42318` | Erreurs de formulaire | Blanc sur alerte 6,57 : 1 |

Polices Google Fonts : **Fraunces** pour les titres (empattements doux, chaleureux), **DM Sans** pour le texte (lisible sur mobile). Logo provisoire : le mot « canapoil » en Fraunces, terracotta sur fond crème, en attendant un logo dessiné au palier 2.

---

## 4. Offre

### 4.1 Prix et économie unitaire

**Hypothèses communes (modèle de lancement : micro-stock en France importé en un seul lot de ≈ 105 unités)** — estimation, confiance moyenne, à remplacer par les factures réelles :

| Paramètre | Valeur | Source |
|---|---|---|
| Coût produit rendu France, hors droits, **base prudente × 1,20** | Rouleau 5,40 € (3,50 € fournisseur + 1,00 € de fret entrant, × 1,20) ; gant 1,56 € ; raclette 2,28 € ; tapis thermique 6,00 € | 01 §3.5 et 01 §3 bis (prix d'index AliExpress à revérifier) ; majoration de 20 % pour la TVA d'AliExpress peut-être non récupérable, les droits d'un petit lot et l'absence de devis, jusqu'à la validation de l'expert-comptable (`brand.json`) |
| Droits, redevance et frais de dossier répartis sur le lot | 0,25 à 0,50 € par unité (lot de plus de 150 € : droits du tarif commun, ≈ 20 € de frais du transporteur) | [Ministère de l'Économie][douane-gouv] ; répartition : estimation, confiance faible |
| Port vers le client en point relais | 4,50 € HT (< 500 g) ; 5,50 € (500 g-1 kg) ; emballage 0,30-0,40 € ; TikTok Shop : tarif « Expédition par TikTok » à relever, 4,50 € supposé | 01 §3.3, hypothèse prudente. Tarif public Mondial Relay depuis le 15/06/2026 : 4,15 € TTC jusqu'à 500 g, 5,99 € TTC jusqu'à 1 kg ([Margeo][margeo-mr], source secondaire à revérifier) ; au tarif public, la marge gagne ≈ 1 € par colis léger |
| Paiement sur le site | Stripe 1,5 % + 0,25 € (carte standard EEE) | [Stripe][stripe-pricing] |
| TikTok Shop | Commission 9 % ; affilié 15 % du prix | [Ecommerce Nation][tts-commission] ; 02 §3.2 |
| Retours et SAV | Provision de 5 % du CA | 02 §4.1, estimation, confiance moyenne |
| Frais de port facturés | 3,90 € TTC sous 35 € d'achat, offerts au-delà | Décision §4.3 |

**Marge par commande, société assujettie à la TVA** (calcul de la stratégie, estimation, confiance moyenne)

| Cas | Poids | CA HT | Produit + droits | Port + emballage | Paiement | Commission TikTok | Affilié | Retours/SAV | **Marge** | % du CA |
|---|---|---|---|---|---|---|---|---|---|---|
| Site — Rouleau seul 24,90 € (+3,90 € de port) | 280 g | 24,00 | 5,80 | 4,80 | 0,68 | — | — | 1,20 | **11,52** | 48 % |
| Site — Kit anti-poils (rouleau + gant) 29,90 € (+3,90 €) | 350 g | 28,17 | 7,61 | 4,80 | 0,76 | — | — | 1,41 | **13,59** | 48 % |
| Site — **Grand kit** (rouleau + raclette + gant) 39,90 € | 500 g | 33,25 | 10,19 | 4,80 | 0,85 | — | — | 1,66 | **15,75** | 47 % |
| Site — Duo 2 rouleaux 39,90 € | 560 g | 33,25 | 11,60 | 5,90 | 0,85 | — | — | 1,66 | **13,24** | 40 % |
| Site — Kit chat d'hiver (rouleau + tapis) 44,90 € | 680 g | 37,42 | 12,30 | 5,90 | 0,92 | — | — | 1,87 | **16,42** | 44 % |
| Site — Tapis thermique seul 24,90 € (+3,90 €) | 400 g | 24,00 | 6,50 | 4,80 | 0,68 | — | — | 1,20 | **10,82** | 45 % |
| TikTok Shop, contenu propre — Rouleau | 280 g | 20,75 | 5,80 | 4,80 | — | 2,24 | — | 1,04 | **6,87** | 33 % |
| TikTok Shop, contenu propre, commission à 4 % (60 jours) | 280 g | 20,75 | 5,80 | 4,80 | — | 1,00 | — | 1,04 | **8,12** | 39 % |
| TikTok Shop, affilié 15 % — Rouleau | 280 g | 20,75 | 5,80 | 4,80 | — | 2,24 | 3,73 | 1,04 | **3,14** | 15 % |
| TikTok Shop, affilié 15 % — Kit anti-poils | 350 g | 24,92 | 7,61 | 4,80 | — | 2,69 | 4,48 | 1,25 | **4,08** | 16 % |

**Effet de la forme juridique** (même calcul, estimation, confiance moyenne) :

| Régime | Rouleau seul, site | Grand kit, site | Rouleau, affilié TikTok | Marge moyenne du mix de lancement* |
|---|---|---|---|---|
| Société assujettie à la TVA (SASU, EURL) | 11,52 € | 15,75 € | 3,14 € | 6,30 € |
| Société en franchise de TVA (TVA d'achat non récupérée) | 13,96 € | 19,07 € | 3,76 € | 7,59 € |
| Micro-entreprise en franchise (après 12,3 % de cotisations sur le CA) | 10,42 € | 14,16 € | 0,70 € | 4,14 € |

\* Mix de lancement : 58 % de commandes TikTok Shop via affiliés, 22 % TikTok Shop en contenu propre, 20 % site (répartition du scénario 02 §4.5). Panier moyen du mix : 28,10 € TTC ; panier moyen du site : 34,80 € TTC.

**Lecture.** Le rouleau vendu par un affilié laisse 3 à 4 € : l'affiliation sert à gagner de la visibilité et des vidéos réutilisables, la marge se fait sur le site et sur les kits. Le mix de lancement donne environ 2 170 € de marge par mois à 11,5 commandes par jour, contre 3 900 € dans le scénario de 02 §4.5, calculé sur un produit à 34,90 €. La majoration de prudence coûte 1,25 € par commande : une facture B2B HT validée par l'expert-comptable la supprime. La micro-entreprise réduit la marge affiliée à 0,70 € : la société à l'IS est recommandée (§8).

### 4.2 Kits et ventes additionnelles

| Kit | Contenu | Prix TTC | Prix séparés | Économie affichée | Marge (assujetti) | Rôle |
|---|---|---|---|---|---|---|
| Kit anti-poils | Rouleau + gant | 29,90 € | 34,80 € | 4,90 € | 13,59 € | Entrée de gamme, TikTok Shop |
| **Grand kit** | Rouleau + raclette + gant | **39,90 €** | 47,70 € | 7,80 € | **15,75 €** | Offre mise en avant sur le site, livraison offerte |
| Duo maison + voiture | 2 rouleaux | 39,90 € | 49,80 € | 9,90 € | 13,24 € | Foyers à plusieurs pièces ou avec voiture |
| Kit chat d'hiver | Rouleau + tapis thermique | 44,90 € | 49,80 € | 4,90 € | 16,42 € | Saisonnier, jusqu'au 28/02/2027 |

Règles d'affichage : l'économie s'écrit en texte (« 7,80 € de moins que les trois produits achetés séparément : 24,90 € + 12,90 € + 9,90 € »), sans prix barré. Elle n'est licite que si les prix unitaires sont réellement pratiqués au même moment (03 §1.7).

| Vente additionnelle | Où | Mécanique | Effet attendu |
|---|---|---|---|
| Gant +9,90 € | Fiche du rouleau ; page de paiement Stripe (« articles optionnels », 10 au maximum par lien, [API Stripe][stripe-plink-api]) | Case non pré-cochée | Panier +9,90 € ; incite à passer au Kit |
| Passage au Grand kit | Sélecteur d'offre sur la fiche produit, Grand kit présenté en premier | « Le plus complet : livraison offerte » | Panier site visé : 34,80 € (estimation, confiance faible) |
| Raclette « pour la voiture » | E-mail J+7 après livraison | Prix normal, aucune remise fictive | Second achat ; taux visé 3-5 % des clients (estimation, confiance faible) |
| Tapis thermique | Fiche rouleau pour les acheteurs « chat » ; e-mail de bienvenue en saison | Kit chat d'hiver | Panier 44,90 € |

### 4.3 Livraison

| Élément | Décision |
|---|---|
| Transporteur | Mondial Relay en point relais (compte pro ou agrégateur sans abonnement). Domicile (Colissimo) ajouté au palier 1. |
| Frais | 3,90 € TTC ; **offerts dès 35 € d'achat** (le seuil est permanent, sans limite de durée) |
| Pourquoi 35 € | 40 % au-dessus du prix du rouleau : le Grand kit, le Duo et le Kit chat d'hiver passent le seuil, le rouleau seul et le Kit anti-poils paient le port. Seuil à revoir à J+60 avec les données réelles. |
| Délai annoncé (stock en France, phase vente) | « Expédié sous 1 jour ouvré depuis la France, livré en point relais 3 à 6 jours ouvrés après la commande. » (`brand.json` → `livraison.delai_annonce`, identique aux CGV art. 7.1) |
| Recalcul du délai | Après 30 livraisons : 90e centile des délais constatés + 2 jours ouvrés (03 §1.5). Le site affiche ensuite la fourchette de dates « livré entre le … et le … ». |
| Précommande (lancement) | Ouverte seulement après la commande du stock. Dates calculées ainsi : date de commande du stock + 90e centile du transit mesuré sur les échantillons + 3 jours ouvrés (dédouanement, étiquetage) = expédition à partir du ; + 6 jours ouvrés = livraison au plus tard le ; plafond de 30 jours ([L216-1][l216-1]). Saisies dans `brand.json` → `livraison.precommande`, elles s'affichent partout (bandeau, fiche, panier, commande, page Stripe, e-mail) et aucune page ne promet alors « 1 jour ouvré » (test bloquant du vérificateur). Contrôle à J-10 : colis fournisseur absent de France → e-mail individuel, nouvelle date ou annulation remboursée |
| Noël 2026 | **Commande avant le mardi 15/12** pour une livraison au plus tard le mercredi 23/12 (15/12 + 6 jours ouvrés), affichée à partir du 1/12, en phase vente avec stock en France (`brand.json` → `livraison.noel_2026`). En précommande, argument Noël seulement si la date limite de livraison tombe au plus tard le 23/12 |
| TikTok Shop | Expédition par TikTok (mode par défaut en France) ou par le vendeur avec un transporteur agréé remis à J+2 au plus tard ; en expédition par le vendeur, **livraison sous 4 jours ouvrés** exigée ([politique][tts-shipping]) : Mondial Relay exclu tant que son 90e centile mesuré dépasse 4 jours ouvrés. Tarif de l'étiquette TikTok à relever à l'ouverture du Seller Center (300 g, 500 g, 1 kg) et à saisir dans le modèle financier |
| Zone | France métropolitaine. Belgique et Luxembourg au palier 1 (même langue). |

### 4.4 Retours et garanties

| Élément | Décision |
|---|---|
| Délai pour changer d'avis | **30 jours** après réception : 14 jours légaux + 16 jours d'extension commerciale, décrite comme telle dans les CGV |
| Frais de retour | À la charge du client en cas de changement d'avis (≈ 5-7 € en point relais, 03 §5.5) ; offerts pour un produit défectueux ou erroné |
| Petits montants | Remboursement sans renvoi quand le retour coûte plus que le produit (gant, raclette) |
| Produit défectueux | Remplacement ou remboursement sur photo ou vidéo, sans renvoi si la valeur est inférieure à 15 € (garantie légale de conformité, 2 ans) |
| Remboursement | Sous 14 jours au plus, par le même moyen de paiement ([L221-24][l221-24]) |
| Fonctionnalité « renoncer au contrat ici » | Obligatoire depuis le 19/06/2026 : lien en pied de page, formulaire, bouton « confirmer la rétractation », accusé de réception horodaté (03 §1.3) |
| Adresse de retour | `{{ADRESSE_RETOUR}}`, en France |

### 4.5 Lancement : liste d'attente, précommande, prime

| Étape | Mécanique | Conformité |
|---|---|---|
| Liste d'attente (semaines 1 à 5) | « Lancement en préparation : recevez un e-mail le jour de l'ouverture des ventes. » Formulaire e-mail avec case de consentement non pré-cochée (lancement, tests et nouveautés, 2 e-mails par semaine au plus), produit d'intérêt et date du consentement enregistrés dans Brevo (Brevo gratuit, 300 e-mails par jour, 02 §6.4) | Consentement préalable ([L34-5 CPCE][cnil-prospection]) ; aucune vente, donc ni médiateur ni REP à ce stade ; le serveur refuse tout paiement |
| Précommande (dès que le stock est commandé, après la porte 1) | Paiement à la commande, dates d'expédition et de livraison écrites partout | Médiateur, adhésion Léko, RC produits et identité légale en place avant le premier paiement (`generer.py --publication`) |
| Prime de lancement | **Gant offert aux 30 premières précommandes, dans la limite des 30 gants réservés** (45 gants commandés au total ; coût 54 €, compté dans le modèle financier) ; compteur réel et daté sur le site | Vente avec prime, licite tant qu'elle reste loyale et que la limite est réelle ; plus simple qu'une remise, qui exigerait un prix de référence pratiqué depuis 30 jours |
| Black Friday (27/11/2026) | Aucune remise : le prix n'a pas 30 jours d'historique | [L112-1-1][l112-1-1] ; fiche DGCCRF du 25/08/2026 (03 §1.7) |

### 4.6 Lignes rouges

Aucun prix barré pendant les 30 premiers jours, ni ensuite sans prix de référence réellement pratiqué. Aucun compte à rebours sans date de fin réelle. Aucun « plus que 3 en stock » non issu du stock réel. Aucun avis importé. Aucune allégation de santé ni allégation environnementale. Aucune vidéo de fournisseur ou de tiers sans licence écrite. Ces règles sont reprises dans `brand.json` (clé `regles_commerciales`).

---

## 5. Modèle opérationnel à 0 €

### 5.1 Comparatif des deux modèles

| Critère | Site statique codé + Stripe Checkout sur Cloudflare Pages | Shopify Basic (offre d'essai) |
|---|---|---|
| Coût fixe, mois 1 à 3 | 0 € d'hébergement ; domaine ≈ 10 € par an (estimation, confiance moyenne) | 3 jours gratuits, puis 1 $ par mois pendant 3 mois, montant affiché en dollars par la [page officielle][shopify-tarifs] (conversion en euros à confirmer à l'inscription) ; domaine en plus |
| Coût fixe, à partir du mois 4 | 0 € | 36 € par mois, ou 27 € par mois en paiement annuel d'avance ([Speed Ecom, relevé du 26/08/2026][speedecom-shopify]) |
| Coût fixe sur 12 mois | ≈ 10 € | ≈ 327 € (3 € + 9 × 36 €) |
| Frais par paiement | Stripe : 1,5 % + 0,25 € (carte standard EEE) ; 2,8 % + 0,25 € (carte premium EEE) ; 3,15 % + 0,25 € (hors EEE) ; aucun frais mensuel ([Stripe][stripe-pricing]) | Shopify Payments Basic : 1,5 % + 0,25 € ([Kanal][kanal], source secondaire, confiance moyenne) ; passerelle tierce : +2 % ([Speed Ecom][speedecom-shopify]) |
| Litige | 20 € + 20 € si contesté, remboursés en cas de gain ([Stripe][stripe-pricing]) | 15 € ([Kanal][kanal]) |
| Mise en ligne | 1 jour : le site est livré par l'agent site ; validation d'identité Stripe | 2 à 4 jours : thème, import du kit CSV, réglages (estimation, confiance moyenne) |
| Panier et vente additionnelle | Liens de paiement par offre, jusqu'à 20 lignes et 10 articles optionnels ; case CGV (`consent_collection`), adresse limitée à la France, tarifs de port ([API Stripe][stripe-plink-api]) ; un panier multi-produits demande une fonction serveur (Pages Functions : 100 000 requêtes par jour gratuites, [Cloudflare][cf-workers-pricing]) | Panier natif, applications de vente additionnelle |
| Relance des paniers abandonnés | Non codée : aucune relance tant que la case de consentement du panier et le webhook d'expiration n'existent pas | Native ; Shopify Messaging, 10 000 e-mails gratuits par mois (02 §6.4) |
| Pages et fonctions légales | Pages statiques fournies (03) ; rétractation = formulaire + fonction + e-mail Brevo, protégée par l'origine, Turnstile, 3 envois par heure et par IP et la vérification de la commande ; mesure d'audience Cloudflare sans cookie autorisée par la CSP | Pages et formulaires natifs ; bannière de consentement Shopify |
| Restriction de l'hébergeur | Usage commercial non interdit, mais **interdiction de collecter des données de carte sur une propriété en offre gratuite** (art. 2.2.1 h du [contrat Cloudflare][cf-terms]) : le paiement se fait uniquement sur la page hébergée par Stripe | Aucune |
| Pic de trafic après une vidéo virale | Requêtes vers les fichiers statiques gratuites et illimitées ([Cloudflare][cf-workers-pricing]) | Inclus |
| Intégrations | Manuelles : flux XML pour Google Merchant Center, TikTok Shop géré à part, aucune publicité avant la bascule | Applications officielles : Google, TikTok, Meta avec API de conversion, DSers, 3PL |
| Gestion des commandes | Tableau de bord Stripe + tableur ; étiquettes créées à la main | Back-office complet, stock multicanal |
| Compétence requise | Remplir `brand.json`, lancer `generer.py` et redéployer avec Wrangler ou Git ; configurer DNS, Stripe, Brevo et Turnstile (pas à pas dans [`docs/demarrage-J1-J14.md`](../docs/demarrage-J1-J14.md)) | Aucune ligne de code |
| Risques principaux | Bug sans support ; temps de maintenance ; aucune automatisation | Abonnement qui court sans vente ; empilement d'applications payantes |

**Hébergeurs gratuits examinés**

| Hébergeur | Usage commercial sur l'offre gratuite | Limite qui compte pour une boutique | Verdict |
|---|---|---|---|
| **Cloudflare Pages** | Non interdit par le [contrat][cf-terms] ; aucune donnée de carte sur le site | Fichiers statiques illimités ; 100 000 requêtes de fonctions par jour ([Cloudflare][cf-workers-pricing]) ; 500 déploiements par mois | **Retenu** |
| Netlify Free | Non établi par les sources consultées | 300 crédits par mois ; au-delà, les sites sont suspendus jusqu'au mois suivant ([netli.fyi][netlify-free], source secondaire, confiance faible) : risque lors d'un pic viral | Écarté |
| GitHub Pages | Interdit pour les sites destinés aux transactions commerciales ([GitHub Docs][gh-pages]) | — | Exclu |
| Vercel Hobby | Réservé à un usage personnel non commercial ([Vercel][vercel-hobby]) | — | Exclu |

### 5.2 Stacks retenues

| Phase | Stack | Coût fixe mensuel |
|---|---|---|
| **Lancement** (validation, précommandes, palier 1) | Site statique (agent site) sur Cloudflare Pages ; liens de paiement Stripe ; TikTok Shop Seller Center ; Brevo gratuit (liste d'attente, accusés de rétractation) ; Google Merchant Center (fiches gratuites, flux XML) ; mesure d'audience Cloudflare sans cookie ; tableur Google Sheets ; CapCut et Canva gratuits | ≈ 1 € (domaine) |
| **Croissance** (dès la première condition de bascule) | Shopify Basic avec le kit d'import (`shopify-kit/`), Shopify Payments + PayPal, Shopify Messaging, Judge.me (avis vérifiés), application TikTok, application Google, pixel Meta + API de conversion, connecteur 3PL | 36 € puis 105 € (Grow) |

**Conditions de bascule vers Shopify** (une seule suffit) : ≥ 5 commandes par jour sur le site pendant 14 jours ; démarrage de la publicité payante (02 §5.1 exige pixel + API de conversion) ; connexion d'un 3PL ; plus de 6 références à synchroniser entre le site et TikTok Shop. La migration prend une journée grâce au kit CSV préparé en amont (produits importés en brouillon, kits suivis en stock ; installer Shopify Bundles le jour de l'import).

**Option pour la précommande.** Si le déploiement du site statique bloque le client (Python, Node, Wrangler, DNS), Shopify Basic à 1 $ par mois pendant 3 mois couvre novembre à janvier pour ≈ 3 €, avec stock, précommandes et e-mails de commande natifs. Le kit d'import sert alors dès la porte 1.

**Passage de Basic à Grow** : Grow coûte 69 € de plus par mois et réduit la commission carte de 1,5 % à 1,3 % (03 §4.1). Il devient rentable au-delà de 69 € ÷ 0,2 % ≈ **34 500 € de CA mensuel** (calcul).

### 5.3 Budget de lancement et portes de décision

Chiffres repris de la finance (05 §5, `finance/data.json` → `tresorerie_demarrage`) et de `brand.json` → `hypotheses_cles.tresorerie`.

| Poste | Quand | Montant cash TTC | Cumul | Condition |
|---|---|---|---|---|
| Domaine canapoil.fr, 1 an | Semaine 1 | ≈ 10 € (estimation) | 10 € | Après recherche TMview et INPI |
| Échantillons : 2 rouleaux de 2 vendeurs, 1 gant, 1 raclette, 1 tapis thermique, 1 tapis de fouille, commandés avant le 1/11 | Semaine 1 | ≈ 35 € (estimation, confiance moyenne) | 45 € | Fournisseur qui identifie le fabricant par écrit (§5.4) |
| Hébergement, Stripe, Brevo, comptes sociaux, TikTok Shop, 3 devis d'assurance RC | Semaines 1-2 | 0 € | 45 € | — |
| **Porte 1 franchie** : médiateur CM2C (3 ans) | 15-16/11 | 48 € ([CM2C][cm2c]) | 93 € | Signal de demande atteint (§6.2) |
| Adhésion Léko, minimum annuel | 15-16/11 | 114 € TTC (95 € HT, TVA récupérable si assujetti) ([Léko][leko]) | 207 € | Idem |
| Fournitures : pochettes, étiquettes importateur et Info-tri, notices imprimées ([gabarits](../docs/gabarits/)) | 15-16/11 | ≈ 12 € (estimation) | 219 € | Idem |
| Dépôt INPI « Canapoil », classe 21 | 15-16/11 | 190 € ([INPI][inpi-bareme]) | 409 € | Idem |
| Assurance RC professionnelle et produits | Avant la commande du stock | 25 € par mois (300 € par an, 150-500 € selon les devis, 03 §0.5) | 434 € | Obligatoire avant d'importer : l'importateur répond comme le producteur (art. 1245-5 du Code civil) |
| **Micro-stock : 40 rouleaux, 45 gants, 12 raclettes, 8 tapis thermiques**, un seul colis, facture B2B HT | 16/11, payé à la commande | ≈ 476 € TTC (396 € HT, coûts unitaires +20 % de prudence, droits compris ; 403 € TTC sans la majoration) | **910 €** | Payé **avant** l'ouverture des précommandes : elles ne le financent pas (le premier versement Stripe arrive 7 jours après le premier paiement) |
| 5 échantillons pour créateurs | Semaine 8 | Prélevés sur le micro-stock | — | Retirés du stock disponible le jour de l'envoi |
| Réserve de trésorerie (règlement TikTok Shop à 31 jours, réassort, étiquettes) | Novembre 2026 à juillet 2027 | **2 000 €** au creux de février 2027 (réaliste) ; 4 539 € (optimiste) | — | Voir options ci-dessous |

**Lecture honnête.** L'enveloppe de 150 € couvre la phase 0 (45 €) et rien d'autre. Vendre légalement son propre stock demande **910 € avant le premier euro encaissé** (1 185 € si l'assurance est payée à l'année), puis une réserve de **2 000 €** dans le scénario réaliste à cause du règlement TikTok Shop 31 jours après livraison. Le client choisit **par écrit, avant S1**, une des trois options de `brand.json` → `hypotheses_cles.tresorerie.options_a_signer_avant_S1` :

| Option | Engagement | Conséquence |
|---|---|---|
| a. Apport en compte courant d'associé | **2 400 €** (besoin réaliste + seuil d'alerte de 300 €) | Plan complet ; remboursable sans impôt dès que la trésorerie le permet |
| b. TikTok Shop plafonné au stock déjà payé, aucune collaboration d'affiliés avant le premier règlement TikTok Shop | 910 € à la porte 1 | Croissance plus lente, palier 1 plus tardif ; pas de creux de février |
| c. Arrêt | 45 € | Si la porte 1 n'est pas franchie, ou si a et b sont refusées |

### 5.4 Approvisionnement et conformité opérationnelle

| Étape | Action | Référence |
|---|---|---|
| 1 | Comparer 2 fournisseurs par produit sur échantillon : finition, efficacité sur 3 tissus, notice, odeur, absence de marque tierce. **Critères éliminatoires** (`brand.json` → `approvisionnement`) : fabricant identifié par écrit (raison sociale, adresse postale, e-mail), notice et avertissements fournis, photos de l'étiquette d'origine, facture B2B HT. Si aucun vendeur AliExpress ne les remplit : CJ Dropshipping ou un agent de sourcing (03 §5.1) | 03 §5.2, GPSR art. 9 et 11 |
| 2 | En S1, avant la commande des échantillons : DesignView, TMview et data.inpi.fr pour le rouleau, le tapis de fouille et le nom, captures datées | 01 §6, §3.1 |
| 3 | À la porte 1, commander le micro-stock des 4 références en un seul colis (≈ 330 € de marchandises : dédouanement de droit commun), depuis un entrepôt UE ou en envoi express, livraison au siège ou à `{{ADRESSE_EXPEDITION}}` ; traitement TVA et douane validé par l'expert-comptable | 01 §3.5, 03 §3.3 |
| 4 | À réception : contrôle à 100 %, étiquette « Importé par `{{RAISON_SOCIALE}}`, `{{ADRESSE}}`, `{{EMAIL}}` — réf. CNP-ROU-01 — lot AAMM » sur chaque produit, notice et avertissements en français dans chaque colis ([gabarits imprimables](../docs/gabarits/)) ; saisie du stock dans `brand.json` et régénération du site | [GPSR, art. 11][gpsr] |
| 5 | Dossier produit conservé 10 ans : factures, photos, coordonnées du fabricant, avertissements | 03 §2.2 |
| 6 | IDU Léko dans les CGV et les mentions légales ; Info-tri sur les emballages | [ADEME][ademe-idu] |
| 7 | Bloc GPSR sur chaque fiche (fabricant, personne responsable dans l'UE, identification, avertissements), alimenté par `brand.json` | 03 §2.3 |

### 5.5 Traitement des commandes

| Étape | Site (Stripe) | TikTok Shop | Délai cible |
|---|---|---|---|
| 1. Réception | E-mail Stripe + reçu automatique au client | Notification du Seller Center | — |
| 2. Contrôle | Adresse en France, paiement validé, détection de fraude Stripe | Statut « à expédier » | Chaque jour à 9 h |
| 3. Préparation | Prélèvement dans le micro-stock, notice, insert « merci + mode d'emploi en vidéo » | Idem | Avant 12 h |
| 4. Étiquette | Mondial Relay (compte pro ou agrégateur) | Étiquette TikTok | Le jour même |
| 5. Dépôt | Point relais de proximité | Transporteur agréé | J+1 ouvré au plus tard |
| 6. Suivi | E-mail de suivi (modèle Brevo) ; ligne dans le tableur : date de commande, d'expédition, de livraison | Automatique | Moins de 24 h |
| 7. Mesure | Délai réel → 90e centile chaque semaine | Taux de livraison à l'heure > 90 % | Hebdomadaire |
| 8. Stock | `brand.json` → `produits[].stock_disponible` mis à jour chaque matin, site régénéré ; sous 5 unités, passage automatique en précommande (dates de réassort) ou indisponible ; le serveur refuse toute commande qui dépasse le stock | Stock Seller Center = stock réel − 2, mis à jour à 9 h et 18 h | Quotidien |
| 9. Réassort | Seuil de commande : 10 jours de ventes + délai fournisseur (≈ 15 jours) ; réassort express à 10 unités en cas de pic viral (`brand.json` → `livraison.stock.procedure_pic_viral`) | Idem | Quand le stock < 25 jours de ventes |

### 5.6 Service client

| Situation | Réponse | Délai | Coût estimé |
|---|---|---|---|
| Question avant achat | Réponse type + vidéo du tissu concerné | Engagement affiché : 48 h ouvrées (`brand.json` → `service_client`) ; cible interne 24 h | 0 € |
| Colis en retard | Localisation, renvoi ou remboursement sans attendre de mise en demeure | < 24 h | Port + produit si perdu |
| Produit défectueux | Photo ou vidéo → remplacement ou remboursement | < 48 h | ≈ 10 € par cas |
| « Ne marche pas sur mon tissu » | Conseil d'usage ; sinon retour sous 30 jours | < 24 h | Remboursement |
| Rétractation | Accusé automatique, remboursement à réception ou sur preuve d'envoi | Sous 14 jours | Prix + port aller standard |
| Litige bancaire | Dossier de preuve (03 §4.3) ; remboursement spontané si le dossier est faible | Avant l'échéance | 20 € par litige |
| Incident de sécurité | Registre des réclamations, information du fabricant, Safety Business Gateway si accident grave | Sans retard | — |

Canaux : e-mail `{{EMAIL}}`, messagerie TikTok Shop, formulaire du site. Pas de téléphone surtaxé. Délai de réponse écrit partout (site, CGV, mentions) : **48 heures ouvrées**.

### 5.7 Outils

| Besoin | Outil | Coût |
|---|---|---|
| Site | Cloudflare Pages | 0 € |
| Paiement | Stripe (liens de paiement) | Commission seule |
| E-mail (liste d'attente, suivi, rétractation) | Brevo gratuit | 0 € |
| Ventes dans l'application | TikTok Shop Seller Center | Commission seule |
| Fiches gratuites Google | Google Merchant Center | 0 € |
| Mesure d'audience | Cloudflare Web Analytics (domaines autorisés dans la CSP) + UTM transmis aux métadonnées Stripe et aux attributs Brevo | 0 € |
| Vidéo et visuels | CapCut, Canva (offres gratuites) | 0 € |
| Pilotage | [`docs/pilotage.xlsx`](../docs/pilotage.xlsx) (importable dans Google Sheets) : commandes, stock, délais, réclamations GPSR, registre RGPD, créateurs, KPI | 0 € |
| Étiquettes | Mondial Relay pro ou agrégateur | Au colis ; caution de 50 € signalée pour le compte pro par une source non vérifiée ([Artisans 2.0][mr-pro]) |

---

## 6. Roadmap par paliers

### 6.1 Vue d'ensemble

« Bénéfice net » désigne ici le résultat mensuel après tous les coûts (produits, logistique, plateformes, publicité, outils, comptable), avant impôt sur les sociétés et avant rémunération du dirigeant. Toutes les lignes sont des estimations de la stratégie ; leur confiance baisse à chaque palier.

| Palier | Bénéfice net / mois | CA TTC / mois | Commandes / mois | Marge nette / CA HT | Canaux | Organisation | Durée estimée | Probabilité cumulée depuis aujourd'hui |
|---|---|---|---|---|---|---|---|---|
| 0 — Validation | 0 € | 0-1 k€ | 0-30 | — | Contenu organique, liste d'attente, précommandes | Fondateur seul | 6-10 semaines | 35-50 % de franchir la porte 1 sur l'un des 3 produits testés |
| 1 | **1 k€** | 5,7 k€ | ≈ 202 (6,7 par jour) | ≈ 21 % | TikTok Shop (propre + affiliés), site, Google gratuit | Seul, micro-stock | 3-12 mois | **10-20 % à 12 mois** (05 §6 ; la red team l'estime à 5-12 %) |
| 2 | **10 k€** | 45-60 k€ | 1 300-1 900 | 20-27 % | + publicité Meta et TikTok, Amazon.fr, Belgique | Seul + assistant SAV à temps partiel + media buyer indépendant ; 3PL | 9-18 mois de plus | **3-5 % à 24 mois** (05 §6) |
| 3 | **100 k€** | 750 k€-1 M€ | 19 000-25 000 | 12-16 % | France < 50 % du CA ; Allemagne, Italie, Espagne ; Amazon UE ; TikTok Shop multi-pays | 8-15 personnes ; 20-40 références | 18-36 mois de plus | **Non chiffrée** : repère d'échelle |
| 4 | **1 M€** | 8,5-12 M€ | 190 000-270 000 | 10-14 % | 10 pays et plus, distribution physique, plusieurs gammes | 50-100 personnes ; stock de 4-6 M€ à financer | 3-5 ans de plus | **Non chiffrée** : repère d'échelle |

Calculs : palier 1 = (1 000 € + 170 € de frais fixes + 100 € d'échantillons créateurs) ÷ 6,30 € de marge moyenne par commande (§4.1, 05 §6). Palier 2 = (10 000 € + ≈ 3 350 € de frais fixes, personnel et échantillons) ÷ 7,28 € de marge après publicité (05 §6). Paliers 3 et 4 = bénéfice visé ÷ marge nette type d'une marque e-commerce rentable (10-16 %, estimation, confiance faible) : ce sont des repères d'échelle obtenus par ratios. Le catalogue ne contient aucun consommable, la valeur vie client n'est pas modélisée et le CPA central de 02 (30 €) dépasse le CPA maximal (20,04 €) : aucune probabilité défendable ne peut leur être attachée. Pour le palier 4, la France seule représenterait 0,11 à 0,16 % de toutes les ventes de produits en ligne du pays (01 §1.8).

### 6.2 Palier 0 : validation (12 octobre 2026 → 10 janvier 2027)

| Semaine | Dates | Actions | Dépense cash | Indicateur de sortie |
|---|---|---|---|---|
| S1 | 12-18/10 | **Décision écrite de trésorerie (option a, b ou c)** ; Kbis (objet social couvrant la vente en ligne) ; régime de TVA et traitement de l'achat B2B avec le comptable ; recherches TMview, data.inpi.fr et DesignView avec captures datées ; 3 devis d'assurance RC ; identité légale saisie dans `brand.json` → `identite` ; domaine ; comptes TikTok Business, Instagram, YouTube, Pinterest ; site en phase liste d'attente ; Brevo (attributs PRODUIT et CONSENTEMENT_DATE) ; Turnstile ; dossier TikTok Shop ; échantillons commandés chez des vendeurs qui identifient le fabricant (`docs/demarrage-J1-J14.md`) | ≈ 45 € | Site en ligne, publiable (`generer.py --publication` sans erreur) ; échantillons commandés |
| S2-S3 | 19/10-1/11 | Page de liste d'attente du tapis de fouille en ligne (S2) ; vidéos « problème » sans produit (poils sur pull noir, canapé, voiture) pour tester les accroches ; relevé des prix de 20 rouleaux sur TikTok Shop ; réception des échantillons ; **mesure du transit de chaque échantillon** (base du calcul des dates de précommande) ; 7 jours d'usage réel ; dossier GPSR | 0 € | ≥ 1 vidéo > 10 000 vues ; échantillon conforme ; prix du rouleau décidé |
| S4-S5 | 2/11-15/11 | **Duel** rouleau / tapis de fouille : 2 vidéos par jour, une par produit, soit ≈ 15 vidéos de démonstration par produit en comptant celles de S3 (5 angles × 3 accroches), recyclées sur Reels et Pinterest ; chaque lien porte `utm_content` et chaque inscription le produit | 0 € | Porte 1 |
| **Porte 1** | 15/11 | Décision écrite | — | **Go** si, sur 14 jours, les trois conditions sont réunies : (1) ≥ 1 vidéo > 50 000 vues avec ≥ 1 % de clics, **ou** ≥ 150 inscrits qualifiés ; (2) **taux de clics produit ≥ 1,5 %** en moyenne sur toutes les vidéos de démonstration du produit (clics vers le profil ou le site ÷ vues), pour mesurer l'intention et pas seulement l'attention ; (3) ≥ 20 commentaires d'intention d'achat de comptes uniques hors entourage |
| S6 | 16-22/11 | Lundi 16/11 : médiateur, Léko, INPI classe 21, RC souscrite, **commande et paiement du micro-stock** (envoi express ou entrepôt UE). Dates de précommande calculées (exemple : transit P90 de 12 jours → expédition à partir du 2/12, livraison au plus tard le 10/12) et saisies dans `brand.json` ; site régénéré en phase précommande ; précommandes ouvertes (gant offert aux 30 premières, dans la limite des 30 gants réservés) | 910 € (option a ou b) | Précommandes ouvertes après la commande du stock |
| S7-S8 | 23/11-6/12 | Contrôle J-10 : colis fournisseur en France 10 jours avant la date limite, sinon e-mail individuel (nouvelle date ou annulation remboursée) ; réception, étiquetage, expédition des précommandes ; site en phase vente avec le stock saisi ; ouverture de TikTok Shop avec le stock réel − 2 (commission à 4 % pendant 60 jours si éligible) ; 5 premiers créateurs ciblés à 18-25 % (sauf option b : pas d'affiliés avant le premier règlement TikTok Shop) | Réserve | **Porte stock** : ≥ 20 précommandes hors entourage et conversion liste → précommande ≥ 8 % |
| S9-S10 | 7/12-20/12 | Date limite de Noël : commande avant le 15/12 ; collaboration ouverte à 12-15 % si l'option de trésorerie le permet ; réassort seulement si la porte stock est franchie | Réserve | ≥ 3 commandes par jour sur 7 jours (porte 2 nominale ; mars-avril 2027 dans le scénario réaliste) |
| S11-S13 | 21/12-10/01 | Revue J+90 ; Kit chat d'hiver ; bilan des délais réels ; **stock principal programmé fin janvier 2027** (avant la hausse saisonnière de février) si la porte stock est franchie ; lives à partir de S12 | Réserve | Trajectoire ≥ 5 commandes par jour |

**Critères d'arrêt du palier 0**

| Signal | Seuil | Décision |
|---|---|---|
| Contenu sans traction | 15-20 vidéos publiées pour un produit, aucune > 5 000 vues, < 10 clics cumulés (02 §1.2) | Abandon du produit, passage au suivant |
| Échantillon non conforme | Inefficace sur 2 tissus sur 3, ou notice absente et impossible à obtenir | Second fournisseur, sinon produit suivant |
| Propriété intellectuelle | Dessin ou modèle enregistré trouvé | Abandon immédiat du produit |
| Précommandes | Porte stock non franchie (< 20 précommandes hors entourage ou conversion < 8 %) | Aucun réassort ; le micro-stock est écoulé (site, TikTok Shop, échantillons créateurs) ; retour au test de contenu |
| Économie | Bénéfice net < 500 € par mois en mai 2027, ou négatif 3 mois de suite | Changer de produit héros ou arrêter (05 §4.4 : le scénario pessimiste déclenche ce critère en mars 2027) |
| Projet entier | 3 produits testés sans franchir la porte 1 (≈ 6 mois) | Arrêt du projet ; perte limitée à ≈ 45-90 € (option c) |

### 6.3 Palier 1 : 1 k€ de bénéfice net par mois

| Rubrique | Contenu |
|---|---|
| Actions | Ouverture de TikTok Shop et affiliation (300 créateurs contactés, environ 15 actifs, 02 §3.3) ; 2 vidéos par jour (plan de 25 h par semaine, 07 §3) ; lives à partir de S12 ; Grand kit mis en avant sur le site ; e-mails automatiques (bienvenue, post-achat J+7) ; fiches Google gratuites ; Pinterest ; avis vérifiés ; hamac après test de charge (stock de 10 unités financé par les marges) ; livraison en Belgique et au Luxembourg |
| Porte 2 (début du palier) | ≥ 3 commandes par jour sur 7 jours (01 §5.2) |
| KPI de passage au palier 2 | 3 mois consécutifs ≥ 1 k€ net ; ≥ 202 commandes par mois ; ≥ 5 commandes par jour sur un même produit pendant 14 jours (seuil 3PL, 03 §5.6) ; retours ≤ 6 % ; litiges ≤ 0,5 % ; note moyenne des avis vérifiés ≥ 4,3/5 ; stock écoulé en moins de 45 jours |
| Critères d'arrêt | < 20 commandes sur les 30 jours suivant l'arrivée du stock (01 §5.2) ; taux de défaut > 5 % (03 §5.2) ; litiges > 1 % ; marge mensuelle inférieure aux frais fixes pendant 3 mois |
| Durée estimée | 3 à 12 mois après le début des ventes (novembre 2027 dans le scénario réaliste de 05) |
| Probabilité | **10-20 % en 12 mois** (estimation, confiance faible, alignée sur 05 §6 : 35-50 % de franchir la porte 1 × 30-40 % de suivre ensuite la trajectoire réaliste ou mieux). La red team l'estime plus bas, à 5-12 %, en raison du temps exigé, du creux saisonnier de décembre et du prix |
| Ce qui la ferait monter | Une vidéo à plus de 1 M de vues avec du stock disponible (≈ 420 commandes, 02 §4.4) ; un créateur au-dessus de 100 000 abonnés ; un budget de stock de 300 € ou plus ; un associé à l'aise devant la caméra |
| Ce qui la ferait baisser | Moins de 15 heures par semaine consacrées au contenu ; médiane des prix TikTok Shop sous 16 € ; nouvelle hausse de la commission TikTok Shop ; saturation du rouleau sur TikTok Shop à moins de 15 € ; découverte d'un dessin protégé |

### 6.4 Palier 2 : 10 k€ par mois — marque propre, import groupé, 3PL, publicité

| Rubrique | Contenu |
|---|---|
| Passage en marque propre | Dépôt INPI des classes 20 et 28 (230 €, la classe 21 étant déposée à la porte 1) puis marque UE (850 € + 50 €) ; emballage à la marque avec informations GPSR et Info-tri ; logo dessiné. Avec sa marque, le client devient « fabricant » au sens du GPSR (art. 13) : documentation technique complète (03 §0.2) |
| Import groupé | 300-1 000 unités par référence via un agent de sourcing (commission 5-10 %), fret maritime ou ferroviaire, numéro EORI, transitaire (50-150 € par déclaration), droits selon TARIC, inspection AQL 2,5 (250-350 € par jour) (03 §3.5 et §5.2). Objectif : coût livré ≤ 30 % du prix TTC (01 §5.2) |
| 3PL France | Bascule à ≥ 5 commandes par jour pendant 14 jours ; préparation ≈ 2,40 € par colis + stockage (03 §5.1, source faible) ; assurance RC produits déjà souscrite depuis la porte 1, plafonds revus à la hausse avant le premier lot importé |
| Publicité | Seulement quand les 7 conditions de 02 §5.1 sont réunies (≥ 30 commandes organiques sur 14 jours, conversion ≥ 2 %, marge ≥ 20 € par commande, créatives prouvées, trésorerie ≥ 600 €, mesure installée, délai ≤ 7 jours) ; **au-delà de 1 000 € par mois, uniquement avec un produit dont le taux de réachat à 180 jours mesuré atteint 15 %** (consommable ou accessoire d'usure, à trouver dans la gamme du palier 2) ; test sur Meta puis Advantage+ Ventes ; GMV Max sur TikTok Shop ; MER comme indicateur principal |
| Exemple d'économie unitaire (Grand kit, import groupé + 3PL) | CA HT 33,25 € ; produits ≈ 3,80 € ; 3PL + port ≈ 6,90 € ; paiement 0,85 € ; retours 1,66 € → **≈ 20 € de marge avant publicité (60 %)**, ROAS de rentabilité ≈ 1,66 sur le HT (estimation, confiance faible) |
| Gamme | 5 à 8 références : plaid imperméable, protège-canapé anti-griffes, griffoir, hamac, tapis de fouille ; Amazon.fr (FBA) ouvert ; e-mail ≥ 10 % du CA |
| Fiscalité | Sortie de la micro-entreprise avant 203 100 € de CA annuel ; fin de la franchise de TVA au-delà de 85 000 € ; IS à 15 % jusqu'à 42 500 € de bénéfice (fait 16) |
| KPI de passage au palier 3 | 3 mois consécutifs ≥ 10 k€ net ; MER ≥ 1,2 × MER de rentabilité (02 §5.2) ; récupération du coût d'acquisition en < 30 jours ; ≥ 15 % des clients rachètent dans les 180 jours ; coût livré ≤ 30 % ; Belgique rentable |
| Critères d'arrêt | Publicité : MER sur 30 jours inférieur au MER de rentabilité après 3 vagues de créatives → retour à l'organique ; stock écoulé en plus de 120 jours → pas de nouvelle commande ; marge brute après import < 55 % → révision des prix ou retrait |
| Durée estimée | 9 à 18 mois après le palier 1 |
| Probabilité | 20-30 % une fois le palier 1 atteint ; **3-5 % à 24 mois** depuis aujourd'hui (estimation, confiance faible, alignée sur 05 §6) |
| Ce qui la ferait changer | **À la hausse** : un produit qui devient best-seller sur Amazon.fr ; des CPM français 2 à 3 fois inférieurs aux CPM américains, confirmés ([Talyco][talyco]) ; un financement de stock (BPI, prêt d'honneur). **À la baisse** : CPM en hausse, concurrence d'une grande marque d'animalerie, rupture d'un fournisseur unique |

### 6.5 Palier 3 : 100 k€ par mois — multi-pays UE

| Rubrique | Contenu |
|---|---|
| Ordre d'entrée | 1. Belgique et Luxembourg (même langue, dès le palier 1) ; 2. Allemagne (TikTok Shop ouvert le même jour que la France, 02 §1.3 ; Amazon.de) ; 3. Italie ; 4. Espagne |
| Prérequis par pays | Guichet OSS au-delà de 10 000 € de ventes intra-UE (03 §3.1) ; REP propre à chaque pays (emballages, et filière du produit) ; avertissements GPSR dans la langue du pays ; stock local pour TikTok Shop (3PL dans le pays ou FBT là où il existe, 01 §1.6) ; service client dans la langue |
| Organisation | 8-15 personnes : contenu, créateurs, publicité, opérations, SAV multilingue, finance ; 20-40 références ; 2e gamme possible (Pilates, sous une marque distincte, 01 §5.3) |
| Financement | Stock ≈ 2,5 mois de coût des ventes, soit 300-400 k€ à financer (estimation, confiance faible) : prêt bancaire, BPI, financement adossé au CA |
| KPI de passage au palier 4 | ≥ 3 pays rentables après publicité ; France < 50 % du CA ; Amazon ≥ 20 % du CA ; marge après publicité ≥ 25 % ; une 2e gamme > 25 % du CA |
| Critères d'arrêt (par pays) | Retour sur coût d'acquisition > 90 jours après 3 mois → sortie du pays ; besoin de trésorerie supérieur au financement disponible → croissance ralentie volontairement |
| Durée estimée | 18 à 36 mois après le palier 2 |
| Probabilité | Non chiffrée : le palier 3 est un repère d'échelle calculé par ratios, sans base produit (aucun consommable, valeur vie client non modélisée). Il suppose une autre entreprise : plusieurs gammes, plusieurs pays |

### 6.6 Palier 4 : 1 M€ par mois

| Rubrique | Contenu |
|---|---|
| Réalité économique | 1 M€ net = 7 à 10 M€ de CA HT par mois, soit 84 à 120 M€ par an : l'entreprise ferait partie du 1 % de sites qui réalisent 78 % du CA en France ([Sellermania/FEVAD][sellermania]) |
| Ce qu'il faut | 10 pays ou plus ; distribution en magasin et chez les grossistes ; plusieurs gammes ou marques ; équipe de 50 à 100 personnes ; 4-6 M€ de stock financés ; probablement une levée de fonds ou un rachat de marques |
| KPI | Marge nette 10-14 % sur 7-10 M€ de CA HT mensuel ; aucun pays > 30 % du CA ; aucun canal > 40 % du CA |
| Probabilité | Non chiffrée : repère d'échelle sans base produit. À ce stade, ce palier est hors de portée du projet tel qu'il est financé |
| Ce qui la ferait changer | Une catégorie entière créée par la marque (effet de réseau, brevet propre) ; une acquisition par un groupe ; une baisse durable des coûts d'acquisition. À l'inverse : régulation accrue des plateformes, droits de douane plus élevés, fin des fortes croissances du social commerce |

### 6.7 Tableau de bord hebdomadaire

| Indicateur | Cible palier 0-1 | Seuil d'alerte | Source |
|---|---|---|---|
| Vidéos publiées | 14 par semaine (2 par jour, plan de 25 h) | < 10 | Comptes sociaux |
| Vues médianes par vidéo | ≥ 2 000 à J+60 (02 §4.4) | < 500 après 30 jours | TikTok Analytics |
| Clics produit / vues (vidéos de démonstration avant la porte 1, puis ancres TikTok Shop) | ≥ 1,5 % (porte 1) ; ≥ 1,2 % ensuite | < 0,5 % | TikTok Studio, Seller Center |
| Conversion du site | ≥ 1,5 % (02 §2.2) | < 0,8 % | Cloudflare + Stripe |
| Commandes par jour | 5 (palier 1) | < 3 sur 14 jours | Stripe + Seller Center |
| Marge moyenne par commande | ≥ 6,30 € | < 5 € | Tableur |
| **Réserve de trésorerie disponible** | ≥ 300 € | **< 300 € : plus aucune commande fournisseur ni échantillon avant le prochain encaissement** | Banque + tableur (`docs/pilotage.xlsx`) |
| Stock par produit (site + TikTok Shop) | ≥ 5 unités | < 5 : précommande ou indisponible ; < 10 en pic viral : réassort express | `brand.json`, Seller Center |
| Délai de livraison, 90e centile | ≤ 6 jours ouvrés | > 7 | Tableur |
| Taux de retour | ≤ 5 % | > 8 % | Tableur |
| Taux de litige | < 0,5 % | > 1 % | Stripe |
| Stock en jours de ventes | 25-45 jours | < 15 ou > 60 | Tableur |
| Affiliés actifs | 15 à J+90 | < 5 à J+60 | Seller Center |

---

## 7. Les 10 risques principaux

Probabilité (P) et impact (I) notés de 1 à 5 ; score = P × I (estimation de la stratégie, confiance moyenne).

| # | Risque | P | I | Score | Parade | Signal d'alerte |
|---|---|---|---|---|---|---|
| 1 | Aucune traction organique | 4 | 4 | 16 | Duel de 2 produits ; 3 produits au maximum ; 45 € engagés avant la porte 1 ; critères d'arrêt écrits | < 5 000 vues de moyenne après 10 vidéos |
| 2 | Concurrence par les prix sur le rouleau (génériques à 15 €, vendeurs TikTok Shop) | 4 | 3 | 12 | Kits ; démonstration par tissu ; délai depuis la France ; marque ; plancher de 8 € de marge par commande sur le site | Prix médian concurrent sur TikTok Shop < 15 € |
| 3 | Non-conformité (GPSR, REP, mentions, prix, avis) | 3 | 4 | 12 | Checklist 03 §6 (79 exigences P0) ; étiquette importateur ; Léko ; médiateur ; lignes rouges du §4.6 | Contrôle DGCCRF, réclamation client, retrait par la plateforme |
| 4 | Trésorerie insuffisante (stock payé à la commande, règlement TikTok Shop à 31 jours, REP, RC) | 4 | 4 | 16 | Option a, b ou c signée avant S1 ; réserve de 2 000 € (réaliste) ; portes de décision ; alerte à 300 € | Réserve < 300 € |
| 5 | Dépendance à TikTok (commission, algorithme, suspension) | 3 | 4 | 12 | Liste e-mail dès le 1er jour ; Pinterest et Google gratuits ; site à marge élevée ; contenus conformes | > 70 % du CA sur TikTok après 6 mois |
| 6 | Dessin ou modèle protégé sur le rouleau | 2 | 5 | 10 | DesignView et INPI avant le stock ; fournisseur à design générique ; jamais le nom « ChomChom » | Mise en demeure, signalement sur la plateforme |
| 7 | Qualité et délais du fournisseur (pics du 11.11 et du Black Friday) | 3 | 4 | 12 | 2 fournisseurs échantillonnés ; transit mesuré sur les échantillons ; stock commandé le 16/11, avant toute précommande, en express ou depuis un entrepôt UE ; dates calculées sur le 90e centile + 3 jours ouvrés ; contrôle à J-10 | Colis fournisseur absent de France 10 jours avant la date limite |
| 8 | Capacité du fondateur (le plan initial demandait 35-43 h par semaine pour 20-25 h disponibles) | 3 | 3 | 9 | Plan ramené à 25 h : 2 vidéos par jour, lives à partir de S12, 4 articles SEO avant février, recyclage limité à Reels et Pinterest (07 §3) ; ou 35-40 h décidées par le client | Cadence < 10 vidéos par semaine pendant 2 semaines |
| 9 | Litiges et blocage des fonds Stripe après un pic viral | 2 | 4 | 8 | Délais réels ; suivi transmis ; descripteur bancaire = « CANAPOIL » ; prévenir Stripe d'un pic ; 20-30 % du CA du pic gardés en trésorerie (03 §4.2) | Litiges > 0,5 % |
| 10 | Hausse des coûts d'import (redevance UE, droits) | 4 | 2 | 8 | Import par lot ; lots de produits identiques ; import groupé au palier 2 | Coût livré > 40 % du prix TTC |

| 11 | Vidéo virale sans stock (l'objectif même du plan : ≈ 420 commandes pour 1 M de vues, 02 §4.4) | 3 | 3 | 9 | Procédure de pic (`brand.json` → `livraison.stock.procedure_pic_viral`) : stock TikTok mis à jour toutes les 2 heures, précommande dès 5 unités, réassort express à 10 unités, aucune ancre produit si le stock couvre moins de 7 jours | Vidéo > 20 000 vues en 6 heures |

Risque spécifique hors classement : la sécurité du hamac (chute du chat si une ventouse lâche). Parade : test de charge filmé, limites de compatibilité affichées, vente uniquement après validation (§2.2).

---

## 8. Décisions restant au client

| # | Décision | Options | Recommandation | Échéance | Impact |
|---|---|---|---|---|---|
| 1 | Forme juridique et régime de TVA | Micro-entreprise ; SASU ou EURL à l'IS ; franchise de TVA ou assujettissement | Société à l'IS ; franchise de TVA tant que le CA reste sous 85 000 € et que la publicité est nulle (à valider avec un expert-comptable) | Semaine 1 | Marge moyenne de 4,14 € à 7,59 € par commande (§4.1) |
| 2 | Financement | a. Apport de 2 400 € en compte courant ; b. TikTok Shop plafonné au stock payé, sans affiliés avant le premier règlement (910 € à la porte 1) ; c. arrêt à 45 € | a si le client peut immobiliser 2 400 € ; sinon b | **Avant S1, par écrit** | Sans a ou b, pas de vente légale de stock propre ni de réserve pour TikTok Shop |
| 3 | Nom de marque | Canapoil ; Toutpoil ; Poilette | Canapoil, après recherche d'antériorité INPI et TMview | Semaine 1 | Domaine, contenus, dépôt |
| 4 | Adresse d'expédition et de retour | Domicile du dirigeant ; domiciliation avec réception de colis (15-40 € par mois, 03 §5.5) | Domicile au palier 0 si le dirigeant accepte que l'adresse figure sur les étiquettes ; domiciliation au palier 1 | Semaine 1 | Vie privée, coût |
| 5 | Présence à l'écran | Visage ; mains seulement ; animal seul | Mains + animal au départ, visage dès que possible (les lives l'exigent) | Semaine 2 | Portée, confiance |
| 6 | Temps disponible | 25 heures par semaine (plan allégé de 07) ; 35-40 heures (plan initial complet) | 25 h avec le plan allégé ; 35-40 h seulement si le client les a réellement | Semaine 1 | Probabilité du palier 1 (§6.3) ; taux horaire de 3,77 € à 25 h (05 §4.3) |
| 7 | Éco-organisme | Léko (minimum 95 € HT, barème public) ; Citeo (forfait à confirmer) | Comparer les devis ; Léko par défaut | Porte 1 | 80-110 € par an |
| 8 | Taux de commission des créateurs | Ouvert 10-15 % ; ciblé 18-25 % | 12 % en ouvert, 20 % en ciblé | S7 | 4-6 € de marge par commande affiliée |
| 9 | Frais de retour | À la charge du client ; offerts | À la charge du client, sauf défaut ; remboursement sans retour pour les petits montants | Avant les précommandes | Coût de 0,25 € par commande si offerts (estimation) |
| 10 | Assurance RC professionnelle et produits | 3 devis en S1 | Souscrire avant la commande du micro-stock : en important, la société répond comme le producteur (art. 1245-5 du Code civil) | Avant la porte 1 | 150-500 € par an ; 25 € par mois dans le modèle dès novembre 2026 |
| 11 | Prix du rouleau | 24,90 € ; 19,90 € | 24,90 € si la médiane des 20 rouleaux relevés sur TikTok Shop est ≥ 16 € ; sinon 19,90 € et Grand kit seul mis en avant | Avant la porte 1 | Marges à recalculer dans `brand.json` et le modèle |
| 12 | Identité légale et objet social | Valeurs de `brand.json` → `identite` ; Kbis | Tout remplir en S1 : le site ne peut pas être publié avec une variable `{{…}}` (LCEN) | Semaine 1 | Blocage de la mise en ligne |

---

## Sources

Sources vérifiées le 12/10/2026 pour ce document, en complément des dossiers 01, 02 et 03.

| Clé | Source |
|---|---|
| shopify-tarifs | Shopify, page tarifs (affichage en dollars depuis l'outil de lecture) : https://www.shopify.com/fr/tarifs |
| speedecom-shopify | Speed Ecom, tarifs Shopify vérifiés le 26/08/2026 : https://speed-ecom.eu/blog/combien-coute-reellement-shopify/ |
| kanal | Kanal, frais Shopify Payments en France : https://getkanal.com/fr/blog/shopify-payments-frais |
| stripe-pricing | Stripe, tarifs France : https://stripe.com/fr/pricing |
| stripe-plink-api | Stripe, API de création d'un lien de paiement : https://docs.stripe.com/api/payment-link/create |
| cf-terms | Cloudflare, Self-Serve Subscription Agreement (art. 2.2.1 h) : https://www.cloudflare.com/terms/ |
| cf-workers-pricing | Cloudflare, tarifs Workers et Pages Functions : https://developers.cloudflare.com/workers/platform/pricing/ |
| netlify-free | netli.fyi, limites de l'offre gratuite Netlify 2026 : https://netli.fyi/blog/netlify-free-plan-limits-2026 |
| gh-pages | GitHub Docs, limites de GitHub Pages : https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits |
| vercel-hobby | Vercel, offre Hobby : https://vercel.com/docs/plans/hobby |
| leko | Léko, barème emballages et papiers 2026 : https://www.leko-organisme.fr/wp-content/uploads/Bareme-Leko-Emballage-et-Papiers-2026-14.11.2025.pdf |
| inpi-bareme | INPI, barème des redevances : https://www.inpi.fr/inpi-block/download-document?id=20516 |
| euipo-fees | EUIPO, taxes de dépôt : https://www.euipo.europa.eu/en/trade-marks/before-applying/fees-payable-direct-filing ; reprise secondaire : https://thaonco.com/?p=58608 |
| rdap-afnic | AFNIC, RDAP (ex. https://rdap.nic.fr/domain/canapoil.fr) |
| rdap-verisign | Verisign, RDAP (ex. https://rdap.verisign.com/com/v1/domain/canapoil.com) |
| maisonpoilue | Maison Poilue, concept store : https://www.maisonpoilue.com |
| debonpoil | Zoomalia, marque DeBonPoil : https://www.zoomalia.com/marques/debonpoil-m-3090-1.html |
| moumout | Smallable, marque My Moumout : https://www.smallable.com/fr/marques/my-moumout |
| atoutpoils-colmar | PagesJaunes, A Tout Poils (Colmar) : https://www.pagesjaunes.fr/pros/62225140 |
| atoutpoils-stmalo | chien.com, Atout Poils (Saint-Malo) : https://www.chien.com/adresse/toiletteur-canin/atout-poils-99518.php |
| zoomalia-rouleau | Zoomalia, rouleau anti-poils en silicone : https://www.zoomalia.com/animalerie/rouleau-anti-poils-reutilisable-en-silicone-clio-plusieurs-coloris-possibles-coloris-selon-arrivage-p-115026.html |
| margeo-mr | Margeo, tarifs Mondial Relay 2026 : https://margeoapp.com/blog/tarifs-mondial-relay-2026 |
| mr-pro | Artisans 2.0, Mondial Relay pro : https://artisansdeuxpointzero.fr/mondial-relay-tarif-pro-artisan |
| dir-2005-29 | Directive 2005/29/CE sur les pratiques commerciales déloyales : https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32005L0029 |

[fevad]: https://www.fevad.com/bilan-du-e-commerce-en-france-les-francais-ont-depense-pres-de-200-milliards-deuros-sur-internet-en-2025/
[sellermania]: https://www.sellermania.com/fr/blog/marketplaces/rapport-fevad-2026-chiffres-e-commerce-vendeurs-marketplace/
[opinionway]: https://fr.themedialeader.com/ia-et-reseaux-sociaux-simposent-dans-les-parcours-dachat-de-la-gen-z/
[tts-shipping]: https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897
[tts-commission]: https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/
[douane-gouv]: https://presse.economie.gouv.fr/?p=180373
[revenue]: https://www.revenue.ie/en/corporate/press-office/press-releases/2026/pr-092926-handling-fee.aspx
[macg]: https://www.macg.co/ailleurs/2026/08/la-taxe-de-3-eu-fait-chuter-les-ventes-de-temu-shein-et-aliexpress-mais-des-contournements-restent-possibles-310523
[gpsr]: https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32023R0988
[leko]: https://www.leko-organisme.fr/wp-content/uploads/Bareme-Leko-Emballage-et-Papiers-2026-14.11.2025.pdf
[ademe-idu]: https://filieres-rep.ademe.fr/en/identifiant-unique
[cm2c]: https://www.cm2c.net/tarifs.php
[dgccrf]: https://www.economie.gouv.fr/dgccrf/laction-de-la-dgccrf/les-enquetes/dropshipping-des-manquements-dans-la-moitie-des-sites
[facco]: https://www.lepointveterinaire.fr/veterinaire/planete-vet/animal-societe/possession-suivi-veterinaire-alimentation-dit-barometre-faccoodoxa-2026-15hngc3
[a-rouleaux-chien]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036748031
[a-rouleaux-chat]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036607031
[zoomalia-rouleau]: https://www.zoomalia.com/animalerie/rouleau-anti-poils-reutilisable-en-silicone-clio-plusieurs-coloris-possibles-coloris-selon-arrivage-p-115026.html
[tw-meta]: https://triplewhale.com/blog/facebook-ads-benchmarks
[tw-tiktok]: https://www.triplewhale.com/blog/tiktok-benchmarks
[sp-tva]: https://entreprendre.service-public.gouv.fr/vosdroits/F21746
[sp-micro]: https://entreprendre.service-public.gouv.fr/vosdroits/F32353
[sp-is]: https://entreprendre.service-public.gouv.fr/vosdroits/F23575
[dir-2005-29]: https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32005L0029
[designview]: https://www.tmdn.org/tmdsview-web/
[inpi-data]: https://data.inpi.fr/
[tmview]: https://www.tmdn.org/tmview/
[rdap-afnic]: https://rdap.nic.fr/domain/canapoil.fr
[rdap-verisign]: https://rdap.verisign.com/com/v1/domain/canapoil.com
[atoutpoils-colmar]: https://www.pagesjaunes.fr/pros/62225140
[atoutpoils-stmalo]: https://www.chien.com/adresse/toiletteur-canin/atout-poils-99518.php
[maisonpoilue]: https://www.maisonpoilue.com
[debonpoil]: https://www.zoomalia.com/marques/debonpoil-m-3090-1.html
[moumout]: https://www.smallable.com/fr/marques/my-moumout
[inpi-bareme]: https://www.inpi.fr/inpi-block/download-document?id=20516
[euipo-fees]: https://www.euipo.europa.eu/en/trade-marks/before-applying/fees-payable-direct-filing
[margeo-mr]: https://margeoapp.com/blog/tarifs-mondial-relay-2026
[mr-pro]: https://artisansdeuxpointzero.fr/mondial-relay-tarif-pro-artisan
[stripe-pricing]: https://stripe.com/fr/pricing
[stripe-plink-api]: https://docs.stripe.com/api/payment-link/create
[l216-1]: https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006069565
[l221-24]: https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006069565
[l112-1-1]: https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006069565
[cnil-prospection]: https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique
[shopify-tarifs]: https://www.shopify.com/fr/tarifs
[speedecom-shopify]: https://speed-ecom.eu/blog/combien-coute-reellement-shopify/
[kanal]: https://getkanal.com/fr/blog/shopify-payments-frais
[cf-terms]: https://www.cloudflare.com/terms/
[cf-workers-pricing]: https://developers.cloudflare.com/workers/platform/pricing/
[netlify-free]: https://netli.fyi/blog/netlify-free-plan-limits-2026
[gh-pages]: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
[vercel-hobby]: https://vercel.com/docs/plans/hobby
[talyco]: https://www.talyco.io/blog/media/observatoire-prix-publicite-en-ligne-france-2026/
