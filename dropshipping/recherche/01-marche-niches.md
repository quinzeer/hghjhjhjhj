# 01 — Marché e-commerce France et sélection de niches

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Rôle | Analyste marché et sélection de niches |
| Périmètre | France uniquement, budget cash ≤ 150 € sur 3 mois, acquisition organique |
| Données brutes | [`donnees/google-trends-fr-2026-10-12.csv`](donnees/google-trends-fr-2026-10-12.csv) (57 mots-clés, 5 ans, France), [`donnees/releve-prix-amazon-zooplus-2026-10-12.csv`](donnees/releve-prix-amazon-zooplus-2026-10-12.csv) (382 prix relevés le 12/10/2026), séries brutes `donnees/google-trends-brut-lot1..5.json` |
| Convention | « Estimation » = calcul ou jugement de l'analyste, avec confiance élevée / moyenne / faible. Prix fournisseurs en $ convertis à 1 $ ≈ 0,86 € (estimation). |

---

## Synthèse

1. **Marché** : 196,4 Md€ dépensés en ligne en France en 2025 (+7 %), dont 76,1 Md€ de produits (+4 %). Panier moyen 62 € (−3 %). La moitié des transactions fait moins de 30 € ([FEVAD][s-fevad-bilan], [Sellermania/FEVAD][s-sellermania]). Le T1 2026 progresse de +5 % ([FEVAD T1 2026][s-fevad-q1]).
2. **Concentration extrême** : 158 200 sites marchands actifs ; 1 % d'entre eux réalisent 78 % du chiffre d'affaires ([Sellermania/FEVAD][s-sellermania]). L'objectif « 1 M€ de bénéfice net par mois » suppose 7 à 10 M€ de CA mensuel, soit 0,11 à 0,16 % de toutes les ventes de produits en ligne en France (estimation, confiance moyenne).
3. **Réseaux sociaux** : chez les 15-25 ans, 83 % ont déjà acheté un produit découvert par hasard sur les réseaux sociaux et TikTok est la première source d'information produit (66 %) ([OpinionWay pour Orisha, avril 2026][s-opinionway]). TikTok touche 23,4 M d'adultes en France ([DataReportal][s-datareportal]).
4. **Deux ruptures 2026 changent l'économie du dropshipping depuis la Chine** :
   - droit de douane de 3 € par catégorie d'articles sur chaque colis ≤ 150 € depuis le 1er juillet 2026, puis redevance de gestion UE de 2 € à partir du 1er novembre 2026 ([gouvernement][s-douane-gouv], [Commission européenne][s-ec-reform]). Soit ≈ +5 € fixes par colis ;
   - TikTok Shop France exige une expédition depuis la France, une remise au transporteur sous 2 jours ouvrés et une livraison sous 4 jours ouvrés en « Expédition par le vendeur » ([politique officielle TikTok Shop][s-tts-shipping]). Le dropshipping depuis la Chine y est donc inutilisable.
5. **Effet sur la concurrence low-cost** : après le 1er juillet 2026, les volumes de commandes ont baissé de 50 % chez Temu, 37 % chez AliExpress et 15 % chez Shein (panel Joko, 1,5 M de consommateurs, relayé par [MacGeneration][s-macg-joko]). La concurrence ultra-bon marché recule, au profit des vendeurs stockés en Europe.
6. **Niche dominante : les animaux de compagnie.** 60 % des Français possèdent un animal ; la France compte 16,6 M de chats et 9,6 M de chiens, ce dernier chiffre en baisse de 300 000 ([baromètre FACCO-Odoxa 2026][s-facco]). Quatre des cinq produits retenus visent les propriétaires d'animaux, dont trois les propriétaires de chats.
7. **Top 5 produits** (score de la niche, sur 100) :
   - rouleau anti-poils réutilisable (77) ;
   - tapis de fouille lavable (76) ;
   - hamac de fenêtre pliable pour chat (69) ;
   - tapis de rebord de fenêtre auto-chauffant pour chat (69, produit saisonnier d'hiver) ;
   - kit de gestion des câbles de bureau (66, diversification hors animaux).
8. **Économie unitaire** : aux volumes de départ, le coût livré représente 38 à 49 % du prix TTC pour les cinq produits. La cible de 25-30 % n'est atteignable qu'en phase 2, avec un import groupé, un fret maritime et un stock en entrepôt. La marge par commande se situe entre 9 et 14 € sur Shopify (société assujettie à la TVA). Ce niveau suffit en acquisition organique. Une campagne payante n'est rentable que si elle coûte moins de 9 à 14 € par commande (estimation, confiance moyenne).
9. **Thèse de départ** : confirmée sur trois points, amendée sur deux, partiellement vérifiable sur un :
   - la validation par dropshipping fonctionne sur le site Shopify uniquement ;
   - TikTok Shop et l'affiliation de créateurs demandent un micro-stock en France (15-25 unités, ≈ 80-100 €). Ce micro-stock favorise les produits légers et bon marché.
   - Le détail figure au §5.4.

---

## 1. Marché e-commerce France 2025-2026

### 1.1 Taille et croissance

| Indicateur | Valeur | Évolution | Source | Confiance |
|---|---|---|---|---|
| Ventes en ligne totales 2025 (produits + services) | 196,4 Md€ | +7 % (après +9,6 % en 2024) | [FEVAD, 11/02/2026][s-fevad-bilan] | Élevée |
| dont produits | 76,1 Md€ | +4 % | [FEVAD][s-fevad-bilan] | Élevée |
| dont services (voyage, billetterie…) | 120,3 Md€ | +9 % | [FEVAD][s-fevad-bilan] | Élevée |
| Part du e-commerce dans le commerce de détail de produits | ≈ 12 % | — | [FEVAD][s-fevad-bilan] | Moyenne (estimation FEVAD) |
| Ventes T1 2026 | 50,1 Md€ | +5 % | [FEVAD/Médiamétrie T1 2026][s-fevad-q1] | Élevée |
| Ventes 2026 (projection) | > 200 Md€ | ≈ +3 à +6 % | Estimation à partir du T1 2026 et de l'anticipation FEVAD | Moyenne |
| Ventes mensuelles moyennes de produits | ≈ 6,3 Md€ | — | Calcul : 76,1 Md€ / 12 | Élevée |

### 1.2 Panier, fréquence, concentration

| Indicateur | Valeur | Source | Lecture pour le client |
|---|---|---|---|
| Panier moyen 2025 | 62 € (−3 % ; produits −4 %) | [FEVAD][s-fevad-bilan] | Une fourchette de prix de 25-45 € se situe sous le panier moyen et facilite l'achat d'impulsion. |
| Transactions 2025 | 3,2 milliards (+10 à +11 %) | [FEVAD][s-fevad-bilan], [Sellermania][s-sellermania] | Les Français achètent plus souvent, pour des montants plus faibles. |
| Part des transactions < 30 € | 50 % | [Sellermania/FEVAD 2026][s-sellermania] | Au-delà de 30 €, l'acheteur demande plus de preuves (avis, démonstration, délai). |
| Achats par acheteur et par an | 75 (4 657 € dépensés) | [Sellermania/FEVAD 2026][s-sellermania] | — |
| Cyberacheteurs | 42,2 M (80 % des 16-74 ans) | [FEVAD Chiffres clés 2026][s-fevad-cc2026] via [recherche][s-sellermania] | Marché mûr : pour gagner un client, il faut le prendre à un concurrent. |
| Sites marchands actifs | 158 200 | [Sellermania/FEVAD 2026][s-sellermania] | — |
| Concentration | 1 % des sites = 78 % du CA | [Sellermania/FEVAD 2026][s-sellermania] | Un CA de 7-10 M€/mois place un site dans ce 1 %. |
| Part des marketplaces dans les ventes de produits | 32 % | [Sellermania/FEVAD 2026][s-sellermania] | Amazon et TikTok Shop sont des canaux à intégrer dès que le stock le permet. |
| Clients actifs d'Amazon | 24 M (57,5 % des cyberacheteurs) | [Sellermania/FEVAD 2026][s-sellermania] | Le prix affiché par Amazon sert de référence au client : il faut le relever pour chaque produit (§4). |
| Achat de seconde main (12 mois) | 41,4 % des cyberacheteurs | [Sellermania/FEVAD 2026][s-sellermania] | — |

### 1.3 Mobile

| Indicateur | Valeur | Source | Confiance |
|---|---|---|---|
| Part des e-acheteurs ayant acheté sur smartphone (2023) | 62 % | FEVAD/Odoxa, repris par [LearnThings][s-learnthings] | Moyenne (donnée 2023) |
| Part mobile des visiteurs uniques, T2 2026 | Shein 95,2 % ; Lidl 92,7 % ; Temu 91,9 % ; Vinted 91,8 % | [FEVAD/Médiamétrie T2 2026][s-fevad-q2] | Élevée |
| Site le plus consulté sur ordinateur | Amazon (36 % de ses visiteurs), Leroy Merlin (33,9 %) | [FEVAD/Médiamétrie T2 2026][s-fevad-q2] | Élevée |
| Part du mobile dans les commandes d'un site vendu via TikTok, Instagram et Pinterest | 85-95 % | Estimation (profil proche de Shein et Temu) | Moyenne |

La FEVAD ne publie pas de part mobile du chiffre d'affaires 2025 en accès libre. Pour ce projet, la page produit doit être pensée pour un écran de téléphone. La vidéo doit être lisible sans le son. Le paiement doit se faire en un geste (Apple Pay, Google Pay, Shop Pay).

### 1.4 Catégories en croissance

Panel iCE100 de la FEVAD, ventes 2025 aux particuliers (+5,6 % au total) ([FEVAD][s-fevad-bilan]) :

| Catégorie | Croissance 2025 | Lecture |
|---|---|---|
| Voyage et loisirs (sites) | +10 % | Hors périmètre |
| High-tech et électroménager | +5,2 % | Appareils sur secteur exclus par le cahier des charges |
| Sport | +5,1 % | Porté par le Pilates (§3) |
| Meuble et décoration | +3,0 % | — |
| Linge de maison | +2,9 % | — |
| Produits de grande consommation | +2,7 % | — |
| Beauté | +2,0 % | Cosmétiques exclus (CPNP) |
| Habillement et chaussures | −0,5 % | Tailles = retours ; à éviter |

Signaux complémentaires issus de Google Trends France (moyenne des 12 derniers mois comparée aux 12 mois précédents, calcul de l'analyste à partir de [Google Trends][s-gt-animaux], données dans le CSV) :

| Mot-clé | Variation sur 1 an | Variation sur 4-5 ans | Volume relatif (« tapis de fouille » = 1) |
|---|---|---|---|
| reformer pilates | +48 % | +2 215 % | ≈ 14 |
| pilates | +18 % | +150 % | ≈ 80 (ordre de grandeur) |
| pilates maison | +60 % | n.s. | ≈ 1,5 |
| boucles sans chaleur | +38 % | +924 % | ≈ 0,9 |
| fontaine chat | +29 % | +48 % | ≈ 13,5 |
| jouet chien | +19 % | +9 % | ≈ 13 |
| griffoir | +12 % | +18 % | ≈ 5,7 |
| anti poils | +11 % | +42 % | ≈ 1,8 |
| tapis de fouille | +11 % | +6 % | 1 |
| lit chat | +7 % | +31 % | ≈ 9,3 |
| hamac chat | −5 % | −17 % | ≈ 2,0 |
| bijoux acier inoxydable | −3 % | +56 % | ≈ 8,3 |
| collier personnalisé | −7 % | −32 % | ≈ 5,4 |
| organisateur valise | −31 % | +50 % | ≈ 0,4 |

Les volumes relatifs sont issus de comparaisons par lots de 5 mots-clés avec « tapis de fouille » comme repère commun. Ce sont des ordres de grandeur (confiance moyenne). Les mots-clés de moins de 2,5 points d'indice sont marqués « volume trop faible » dans le CSV.

### 1.5 Audience des principaux acteurs (T2 2026)

| Site | Visiteurs uniques mensuels | Évolution | Source |
|---|---|---|---|
| Amazon | 41,2 M | +0,5 M sur le trimestre | [FEVAD/Médiamétrie T2 2026][s-fevad-q2] |
| Leboncoin | 32,1 M | — | idem |
| Booking.com | 22,5 M | +11,6 % sur le trimestre | idem |
| Temu | 21,3 M | −12,7 % sur le trimestre, −5,2 % sur un an | idem |
| Vinted | 20,1 M | entre dans le top 5 | idem |
| Shein | 15,5 M | −7,1 % sur un an | idem |
| AliExpress | 15,1 M | 15,9 M au T1 | idem |

Temu et AliExpress reculent au trimestre où entre en vigueur le droit de 3 €. Ce recul est cohérent avec la baisse des volumes mesurée par Joko (§1.7).

### 1.6 Achats via les réseaux sociaux

| Indicateur | Valeur | Source | Confiance |
|---|---|---|---|
| Identités sur les réseaux sociaux en France | 51,5 M (77,2 % de la population), oct. 2025 | [DataReportal Digital 2026 France][s-datareportal] | Moyenne (données des régies) |
| Audience publicitaire TikTok, 18 ans et plus | 23,4 M (43,9 % des adultes) | [DataReportal][s-datareportal] | Moyenne |
| Audience publicitaire Instagram / Facebook / Pinterest / YouTube | 28,2 M / 31,5 M / 18,3 M / 51,5 M | [DataReportal][s-datareportal] | Moyenne |
| Utilisateurs mensuels TikTok en France | 27,8 M (premier pays européen) | Déclaration TikTok, [The Media Leader, sept. 2025][s-medialeader-tiktok] | Moyenne (non audité) |
| 15-25 ans ayant déjà acheté un produit découvert par hasard sur les réseaux sociaux | 83 % (42 % souvent) | [OpinionWay pour Orisha Commerce, 804 jeunes, avril 2026][s-opinionway] | Moyenne (déclaratif) |
| Première plateforme d'information produit chez les 15-25 ans | TikTok 66 %, Instagram 44 %, YouTube 38 % | [OpinionWay/Orisha][s-opinionway] | Moyenne |
| 15-25 ans consultant une IA générative avant un achat | 35 % | [OpinionWay/Orisha][s-opinionway] | Moyenne |
| Lancement de TikTok Shop France | 31 mars 2025 | [LSA][s-lsa-tts] | Élevée |
| Vendeurs TikTok Shop France | 33 000 en mars 2026 (16 500 en oct. 2025) | Déclaration TikTok, [Les Gens d'Internet][s-tts-33k] | Moyenne (non audité) |
| Croissance des ventes TikTok Shop France | +113 % sur 6 mois | Déclaration TikTok, [Les Gens d'Internet][s-tts-33k] | Faible à moyenne |
| Part du live shopping dans les ventes TikTok Shop France | ≈ 20 % | idem | Moyenne |
| Commission TikTok Shop | 9 % depuis le 8 janvier 2026 (5 % avant) ; 7 % électronique ; 4 % pendant 60 jours pour une première boutique UE | [Ecommerce Nation][s-tts-commission] | Moyenne (à vérifier dans le Seller Center) |
| Fulfilled by TikTok (FBT) en France | Sur invitation ; entrepôts en Espagne, Allemagne et Pays-Bas selon une source, sans entrepôt français | [Eurofiscalis][s-fbt] | Faible (sources contradictoires) |

**Lecture** : TikTok est le premier canal de découverte de produits chez les moins de 25 ans. TikTok Shop permet l'achat sans quitter l'application, et les créateurs affiliés y sont payés à la commission. Ces deux leviers sont les plus puissants pour un budget nul. Les deux exigent un stock en France (§1.7).

### 1.7 Changements réglementaires et logistiques 2026

| Mesure | Contenu | Date | Effet chiffré pour le client | Source | Confiance |
|---|---|---|---|---|---|
| Fin de la franchise de droits ≤ 150 € | Droit forfaitaire de 3 € par catégorie tarifaire d'articles dans chaque colis ≤ 150 € venant d'un pays tiers ; prévu jusqu'au 1er juillet 2028 | 1er juillet 2026 | +3 € par colis mono-produit expédié de Chine ; +6 € pour un lot de deux catégories | [Gouvernement][s-douane-gouv], [Commission européenne][s-ec-reform] | Élevée |
| Redevance de gestion UE (« Union handling fee ») | 2 € ; base par colis ou par article encore discutée selon les sources | 1er novembre 2026 | +2 € par colis (hypothèse retenue) | [Commission européenne, actualité du 07/10/2026][s-ec-reform] | Moyenne sur l'assiette |
| Taxe nationale française sur les petits colis | 2 € par article, en vigueur du 1er mars au 30 juin 2026, suspendue depuis | Suspendue le 1er juillet 2026 | Aucun effet aujourd'hui | [Gouvernement][s-douane-gouv], [economie.gouv.fr][s-eco-gouv-colis] | Élevée |
| TVA à l'import | Due quelle que soit la valeur du colis | En vigueur | Pour une société assujettie, la TVA payée à AliExpress n'est pas récupérable en pratique (hypothèse prudente) | [economie.gouv.fr][s-eco-gouv-colis] | Moyenne |
| Règlement (UE) 2023/988 (GPSR) | Opérateur responsable établi dans l'UE, identification du produit, avertissements en français, informations obligatoires sur la fiche en ligne | 13 décembre 2024 | La société française qui importe ou vend sous sa marque peut endosser les obligations d'importateur ou de fabricant. Un fournisseur chinois sans représentant UE expose le vendeur. | [EUR-Lex][s-gpsr], [Journal du Net][s-gpsr-jdn] | Élevée |
| REP françaises (filières pollueur-payeur) | Emballages pour tous ; articles de sport et de loisirs (Ecologic), jouets, équipements électriques, ameublement selon le produit ; le dropshipping n'exonère pas le premier metteur sur le marché | En vigueur | Inscription et éco-contribution par filière ; pénalise le fitness et les appareils électriques | [Guide Ecologic ASL][s-rep-asl], [LeFreelance][s-rep-idu] | Moyenne |
| Politique d'expédition TikTok Shop UE | Expédition depuis le pays d'enregistrement de la boutique. Remise au transporteur sous 2 jours ouvrés. Livraison sous 4 jours ouvrés en « Expédition par le vendeur ». Annulation automatique à 7 jours ouvrés. | En vigueur | Dropshipping Chine incompatible ; micro-stock en France obligatoire | [TikTok Shop, politique officielle][s-tts-shipping] | Élevée |
| Exception au droit de rétractation | Biens « nettement personnalisés » (art. L221-28 3° du Code de la consommation) | En vigueur | Avantage des produits personnalisés (portraits, gravure) | [Légifrance][s-l221-28] | Élevée |
| Franchise en base de TVA (micro-entreprise) | 85 000 € de CA (seuil majoré 93 500 €) pour la vente de marchandises | 2025-2026 | En franchise, la marge par commande gagne 3,5 à 7,5 € sur les produits du top 5 (§3.5) | [Sparkreceipt][s-tva] | Moyenne (source secondaire) |

**Effet mesuré sur les plateformes asiatiques** (panel Joko, juin → juillet 2026, [MacGeneration][s-macg-joko]) :

| Plateforme | Volume de commandes | Panier moyen |
|---|---|---|
| Temu | −50 % (CA ≈ −38 %) | +30 % |
| DHGate | −43 % | — |
| AliExpress | −37 % | +27 % |
| Shein (entrepôt en Pologne) | −15 % | — |

Le recul plus faible de Shein s'explique par son stock en Europe. La même logique vaut pour le client : un stock en France ou dans l'UE devient un avantage de coût et de délai.

### 1.8 Ce que le marché implique pour l'objectif de rentabilité

| Palier de bénéfice net mensuel | Commandes mensuelles nécessaires à 10-14 € de marge par commande | Conditions de marché | Estimation de confiance |
|---|---|---|---|
| 1 k€ | 80-120 | Atteignable en organique avec un produit validé | Moyenne |
| 10 k€ | 800-1 200 (30-40 par jour) | TikTok Shop, créateurs affiliés et micro-stock ; un seul produit peut suffire | Moyenne |
| 100 k€ | 7 000-10 000, avec une marge relevée à 15-25 € par import groupé | Marque, gamme de 5 à 15 produits, publicité payante rentable, 3PL | Faible |
| 1 M€ | ≈ 7-10 M€ de CA par mois = 0,11-0,16 % des ventes de produits en ligne en France | Multi-pays UE, marketplaces, marque reconnue ; place le site dans le 1 % qui réalise 78 % du CA | Faible |

Le détail des paliers, des conditions de passage et des probabilités relève du dossier stratégie. Ce tableau montre seulement l'ordre de grandeur imposé par le marché.

---

## 2. Grille de scoring

### 2.1 Filtres éliminatoires (appliqués avant le score)

| Filtre | Catégories exclues ou pénalisées | Raison | Source |
|---|---|---|---|
| F1 Réglementation sectorielle lourde | Cosmétiques (notification CPNP, personne responsable), compléments alimentaires, dispositifs médicaux (correcteurs de posture, appareils de massage à allégation), jouets pour moins de 14 ans (EN 71, REP jouets), puériculture, appareils sur secteur (DEEE, basse tension, CEM) | Coût de conformité et responsabilité incompatibles avec 150 € | Cahier des charges client ; [GPSR][s-gpsr] |
| F2 Ancrage de prix | Produit vendu couramment < 15 € sur Amazon.fr ou chez Action (note « Prix 25-60 € » = 1) | Impossible de le vendre seul entre 25 et 60 € ; il peut servir d'article complémentaire | Relevé Amazon.fr du 12/10/2026 (CSV) |
| F3 Coût livré | Coût livré > 55 % du prix de marché (note « Coût » = 1) | Marge négative ou nulle à petite échelle ; produit renvoyé en phase 2 | Calcul §3.5 |
| F4 Propriété intellectuelle | Copie d'un design, d'une marque ou d'une vidéo protégés | Contrefaçon (saisie, responsabilité civile et pénale) | Vérification EUIPO/INPI obligatoire avant tout lancement |

### 2.2 Critères et pondérations

Chaque critère est noté de 1 (défavorable) à 5 (favorable). Score = Σ (poids × note) / 5, sur 100.

| # | Critère | Poids | Note 5 | Note 1 | Donnée utilisée |
|---|---|---|---|---|---|
| 1 | Démontrabilité vidéo (effet visible en 3 s) | 14 | Avant/après immédiat, réaction d'un animal | Bénéfice invisible ou abstrait | Jugement sur formats TikTok observés |
| 2 | Problème réel résolu | 8 | Gêne quotidienne partagée par des millions de foyers | Achat purement décoratif | FACCO, usages |
| 3 | Demande et tendance en France | 10 | Volume élevé et croissance > +15 % sur 1 an | Volume quasi nul ou baisse > 15 % | Google Trends FR (CSV) |
| 4 | Prix de vente 25-60 € TTC tenable | 8 | Concurrents français vendent à 35 € et plus | Ancrage < 15 € | Amazon.fr, zooplus, boutiques françaises |
| 5 | Coût livré ≤ 30 % du TTC atteignable | 10 | ≤ 30 % dès le départ | > 55 % | Calcul §3.5 |
| 6 | Logistique (poids, volume, fragilité) | 7 | < 300 g, souple, incassable | > 1,5 kg ou fragile | Fiches fournisseurs |
| 7 | Risque réglementaire faible | 10 | Aucune réglementation sectorielle, risque d'usage faible | Réglementation sectorielle ou risque de blessure | §1.7, §2.1 |
| 8 | Taux de retour faible | 4 | Taille unique, peu de cas d'incompatibilité | Tailles, compatibilité incertaine | Jugement |
| 9 | Différenciation face à Action, Amazon, Temu, Shein | 10 | Peu d'équivalents bon marché, marques absentes | Équivalent identique < 10 € partout | Relevés de prix |
| 10 | Potentiel de marque et de récurrence | 9 | Gamme naturelle, consommables, communauté | Achat unique sans suite | Jugement |
| 11 | Saisonnalité | 3 | Demande stable ou pic imminent (T4 2026) | Pic unique éloigné | Google Trends (mois de pic et de creux) |
| 12 | Éligibilité TikTok Shop France et micro-stock | 7 | Catégorie autorisée, 15-25 unités finançables pour moins de 100 € | Stock inabordable ou catégorie restreinte | §1.7, §3.5 |

Les poids favorisent ce qui fait vendre sans budget : la vidéo (critères 1 et 3) et la marge (critères 4, 5 et 9). La saisonnalité pèse peu, car le calendrier de lancement s'adapte au produit.

---

## 3. Niches candidates

### 3.1 Tableau de scores (15 niches)

| Rang | Niche | Démo 3 s (14) | Problème (8) | Demande (10) | Prix 25-60 € (8) | Coût ≤ 30 % (10) | Logistique (7) | Réglementaire (10) | Retours (4) | Différenciation (10) | Marque/récurrence (9) | Saisonnalité (3) | TikTok Shop (7) | **Score /100** | Filtre |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | N2 Poils d'animaux dans la maison | 5 | 5 | 3 | 3 | 3 | 5 | 4 | 5 | 2 | 3 | 5 | 5 | **77** | — |
| 2 | N3 Enrichissement et alimentation lente (chien, chat) | 4 | 4 | 3 | 4 | 3 | 4 | 5 | 5 | 3 | 4 | 3 | 4 | **76** | — |
| 3 | N7 Coiffure sans chaleur (bigoudis satin) | 5 | 3 | 4 | 1 | 4 | 5 | 5 | 5 | 1 | 3 | 4 | 5 | **74** | **F2** |
| 4 | N11 Outils de nettoyage manuels | 5 | 4 | 4 | 1 | 3 | 4 | 4 | 5 | 1 | 3 | 5 | 4 | **70** | **F2** |
| 5 | N1 Chat d'intérieur : hamacs et couchages de fenêtre | 5 | 3 | 4 | 5 | 2 | 2 | 3 | 4 | 3 | 4 | 4 | 2 | **69** | — |
| 6 | N14 Bijoux en acier inoxydable | 2 | 1 | 4 | 4 | 5 | 5 | 4 | 4 | 1 | 4 | 4 | 5 | **68** | — |
| 7 | N9 Bureau et gestion des câbles | 4 | 4 | 2 | 2 | 3 | 4 | 5 | 5 | 2 | 2 | 4 | 4 | **66** | — |
| 8 | N8 Maquettes 3D mécaniques en bois (adultes) | 4 | 2 | 4 | 5 | 3 | 3 | 2 | 4 | 3 | 4 | 1 | 3 | **66** | F4 (risque) |
| 9 | N5 Portraits d'animaux personnalisés (impression à la demande) | 4 | 2 | 2 | 3 | 3 | 5 | 4 | 5 | 3 | 3 | 2 | 3 | **65** | — |
| 10 | N12 Organisation de voyage (cubes de compression) | 4 | 4 | 1 | 3 | 3 | 4 | 5 | 4 | 2 | 2 | 2 | 3 | **62** | — |
| 11 | N4 Fontaines à eau pour chat | 3 | 4 | 5 | 3 | 2 | 2 | 2 | 3 | 2 | 5 | 4 | 2 | **61** | F1 (électrique) |
| 12 | N6 Pilates et fitness à domicile | 3 | 3 | 5 | 4 | 1 | 2 | 3 | 4 | 2 | 4 | 4 | 2 | **60** | **F3** |
| 13 | N15 Ustensiles de cuisine (contact alimentaire) | 4 | 3 | 4 | 2 | 3 | 3 | 2 | 4 | 1 | 3 | 4 | 3 | **59** | — |
| 14 | N10 Rangement sans perçage (locataires) | 4 | 4 | 1 | 2 | 3 | 3 | 4 | 4 | 1 | 2 | 5 | 4 | **58** | — |
| 15 | N13 Accessoires voiture | 3 | 3 | 2 | 2 | 3 | 3 | 4 | 4 | 1 | 2 | 3 | 3 | **53** | — |

Après filtres, l'ordre des niches éligibles est le suivant : N2 (77), N3 (76), N1 (69), N14 (68), N9 (66), N8 (66, sous condition), N5 (65).

### 3.2 Justification des notes

| Niche | Signal de demande (Google Trends FR) | Ancrage de prix observé | Point fort | Point faible | Verdict |
|---|---|---|---|---|---|
| N1 Chat d'intérieur | « hamac chat » ≈ 2× le repère (−5 %) ; « lit chat » ≈ 9× (+7 %) | Amazon « Tapis de fenêtre » : 12-70 € ; boutiques françaises : 34,90-79,90 € | 16,6 M de chats ; la vidéo d'un chat sur une vitre se partage seule ; prix de 35-45 € validé par des boutiques françaises | 1-1,7 kg, coût livré ≈ 49 %, ventouses à tester | Top 5 (Shopify) |
| N2 Poils d'animaux | « anti poils » ≈ 1,8× (+11 % ; +42 % en 4-5 ans) ; « poils de chat » ≈ 6× (−8 %) | Rouleaux Amazon : 8-26 €, n° 1 de la sous-catégorie à 25,99 € ; zooplus : 17,59-25,99 € | Avant/après en 3 secondes ; 39 % des Français ont un chat, 28 % un chien | Clones partout, risque de design protégé | Top 5, n° 1 |
| N3 Enrichissement | « tapis de fouille » +11 % ; « jouet chien » ≈ 13× (+19 %) ; « gamelle anti glouton » ≈ 2,9× (+10 %) | zooplus : 2-35 € ; inooko : 16,99-39,99 € ; artisans français : 30-57 € | Léger, souple, peu présent dans les meilleures ventes Amazon | Population canine en baisse (−300 000) ; pic en novembre, creux en juin | Top 5 |
| N4 Fontaines chat | « fontaine chat » ≈ 13,5× (+29 %) | Amazon n° 1 à 22,21 € ; filtres à 10-20 € | Demande forte et filtres récurrents | Pompe électrique, adaptateur secteur (F1), DEEE, 1-1,5 kg | Phase 2, avec marque et fournisseur certifié |
| N5 Portraits personnalisés | « portrait chien » volume faible ; « cadeau personnalisé » ≈ 22× (−4 %) | Affiches : 19-39 € ([Mon Chouchou][c-monchouchou], [Petprinted][c-petprinted], [ThinkArt][c-thinkart], [VotrePortrait][c-votreportrait]) | Pas de douane avec une impression locale ([Gelato France][s-gelato]) ; pas de droit de rétractation ([L221-28][s-l221-28]) | Applications IA déjà installées à 19 € ; ventes concentrées au T4 | Réserve pour le T4 |
| N6 Pilates | « reformer pilates » ≈ 14× (+48 %) ; « pilates maison » +60 % | Amazon : kits barre 29,99-45,99 €, planches 39,99-49,99 € | Plus forte croissance mesurée | Prix AliExpress : barre avec élastiques ≈ 22-24 $ ([exemple de fiche][f-pilates-bar]), planche 51-71 $ ([exemple de fiche][f-pilates-board]). Le coût livré dépasse 60 % (F3). REP ASL. | Phase 2 (import groupé), candidat n° 1 de cette phase |
| N7 Coiffure sans chaleur | « boucles sans chaleur » ≈ 0,9× (+38 % ; ×10 en 5 ans) ; #heatlesscurls ≈ 8,9 milliards de vues ([TimesLive, 2024][s-heatless]) | Amazon : 6,29-13,99 € pour l'essentiel du top 30 ; Kitsch 25,90 € ([Kitsch][s-kitsch]) | Démonstration parfaite, 50 g | Ancrage < 15 € (F2), Shein et Temu | Article complémentaire pour TikTok Shop |
| N8 Maquettes 3D bois | « maquette bois » ≈ 4,7× (−3 %) ; « rokr » +51 % | Amazon : ROKR 59,95 €, Rolife 44,95-48,95 € | Prix de 40-60 €, collection | Designs copiés = contrefaçon (F4). Pic en décembre ×3,6, creux en été. Frontière avec les jouets. | Uniquement avec un fournisseur autorisé, au T4 |
| N9 Bureau et câbles | « cache câble » ≈ 0,37× (+55 %) | Galaxus : 18,39 € ([lien][c-galaxus]) ; Leroy Merlin : 40,89 € ([lien][c-lm-cable]) | Aucun risque réglementaire, avant/après visuel | Volume faible, différenciation faible | Top 5 (diversification) |
| N10 Sans perçage | « étagère sans perçage » volume trop faible | Action, IKEA, Command < 10 € | — | Ancrage bas, demande faible | Écartée |
| N11 Nettoyage manuel | « brosse nettoyage » ≈ 7× (−5 %) | Action et grandes surfaces < 10 € | Format vidéo de nettoyage très viral | F2 | Écartée |
| N12 Voyage | « organisateur valise » ≈ 0,4× (−31 %) | Decathlon, Amazon, Action | — | Saison courte (juillet ×2,8) | Écartée |
| N13 Voiture | « organisateur voiture » −14 % ; « support téléphone voiture » −10 % | Norauto, Amazon, Action | — | Demande en baisse | Écartée |
| N14 Bijoux acier | « bijoux acier inoxydable » ≈ 8× (−3 %) ; « collier personnalisé » −7 % (−32 % en 5 ans) | Shein, Temu, Etsy | Coût de 1 à 5 $ ([AliExpress][f-bijou]), 20 g | Aucune démonstration ni problème résolu ; demande personnalisée en baisse | Réserve (marque esthétique) |
| N15 Cuisine | « ustensiles cuisine » ≈ 10× (+2 %) | Action, Amazon | — | Règlement (CE) 1935/2004 : déclaration de conformité et tests de migration | Écartée |

### 3.3 Hypothèses économiques communes

| Paramètre | Valeur retenue | Source | Confiance |
|---|---|---|---|
| Droit de douane colis ≤ 150 € | 3 € par catégorie d'articles et par colis | [Gouvernement][s-douane-gouv] | Élevée |
| Redevance UE à partir du 01/11/2026 | 2 € par colis | [Commission][s-ec-reform] | Moyenne |
| Taux de change | 1 $ ≈ 0,86 € | Estimation | Moyenne |
| Frais de paiement (Shopify Payments ou équivalent) | ≈ 2 % + 0,25 € | Estimation | Moyenne |
| Port France en point relais (contrat pro via agrégateur) | 4,50 € (< 500 g) ; 5,50 € (500 g-1 kg) ; 7,00 € (1-2 kg) | Estimation. Tarif public Colissimo 2026 à domicile : 5,49 € (250 g), 7,59 € (500 g), 9,59 € (1 kg) ([La Poste][s-colissimo]) ; Mondial Relay pro dès 3,89 € ([source][s-mondialrelay]) | Moyenne |
| Emballage | 0,30 € par colis | Estimation | Moyenne |
| Commission TikTok Shop | 9 % (4 % pendant les 60 premiers jours) | [Ecommerce Nation][s-tts-commission] | Moyenne |
| Commission des créateurs affiliés | 15 % (fourchette usuelle 10-20 %) | Estimation, cohérente avec [02-acquisition](02-acquisition.md) | Moyenne |
| TVA payée à AliExpress | Non récupérée (hypothèse prudente) | — | Moyenne |

### 3.4 Délais et entrepôts fournisseurs (valables pour tout le top 5)

| Mode | Délai vers la France | Compatible TikTok Shop FR | Source | Confiance |
|---|---|---|---|---|
| AliExpress Choice, expédition de Chine | 7-15 jours | Non | [Vitepromo][s-ali-choice] | Faible |
| AliExpress, annonces « expédié depuis la France ou l'UE » | 2-5 jours | Non (l'expédition ne part pas de l'adresse du vendeur) | [Vitepromo][s-ali-choice] | Faible |
| CJ Dropshipping, Chine (CJPacket) | 7-14 jours | Non | [Speed-ecom][s-speedecom-cj] | Faible |
| CJ Dropshipping, entrepôts UE (Allemagne, France, Espagne, Italie annoncés) | 3-7 jours | Non pour l'Allemagne, l'Espagne et l'Italie. Pour la France, uniquement si l'expédition respecte 2 + 4 jours ouvrés avec l'étiquette TikTok. | [CJ, nov. 2025][s-cj-warehouses], [Speed-ecom][s-speedecom-cj] | Faible (stock par référence à vérifier) |
| Micro-stock chez le client, envoi en point relais | 2-4 jours | Oui | [Politique TikTok Shop][s-tts-shipping] | Élevée |

Le dropshipping depuis un entrepôt UE de CJ évite les 5 € par colis, puisque le stock a déjà été dédouané. En contrepartie, CJ facture un prix de vente supérieur. L'effet net est à vérifier produit par produit dans le tableau de bord CJ.

### 3.5 Économie unitaire du top 5 (aux volumes de départ)

Modèle A : dropshipping depuis la Chine. Coût livré = prix fournisseur + port Chine-France + 3 € + 2 €.
Modèle B : micro-stock en France. N unités achetées en un colis ≤ 150 €, réexpédiées en point relais.

| Produit | Prix TTC cible | Coût livré A | % du TTC | Marge par commande A (assujetti TVA) | Marge par commande A (franchise TVA) | Coût livré B | % du TTC | Marge par commande B sur TikTok Shop (9 % + affilié 15 %), assujetti | Mise de départ du micro-stock |
|---|---|---|---|---|---|---|---|---|---|
| Rouleau anti-poils réutilisable | 24,90 € | 10,00 € | 40 % | 10,00 € | 14,15 € | 9,55 € (20 u.) | 38 % | 5,22 € | ≈ 95 € |
| Tapis de fouille M/L lavable | 32,90 € | 13,50 € | 41 % | 13,01 € | 18,49 € | 14,30 € (12 u.) | 43 % | 5,22 € | ≈ 102 € |
| Hamac de fenêtre pliable pour chat | 44,90 € | 22,00 € | 49 % | 14,27 € | 21,75 € | Non finançable dans le budget | — | — | > 150 € |
| Tapis de fenêtre auto-chauffant pour chat | 24,90 € | 11,00 € | 44 % | 9,00 € | 13,15 € | 10,30 € (15 u.) | 41 % | 4,47 € | ≈ 83 € |
| Kit de gestion des câbles | 29,90 € | 14,00 € | 47 % | 10,07 € | 15,05 € | 14,38 € (12 u.) | 48 % | 3,36 € | ≈ 103 € |

Toutes les valeurs sont des estimations de l'analyste (confiance moyenne). Prix fournisseurs retenus : rouleau 3,50 €, tapis de fouille 6 €, hamac 12 €, tapis auto-chauffant 3,50 €, kit câbles 6,50 €. Port Chine-France : 1,50 à 5 € selon le poids.

**Conclusions chiffrées :**

| Constat | Conséquence |
|---|---|
| Aucun produit n'atteint 30 % de coût livré à petite échelle. Les 5 € fixes par colis représentent 11 à 20 % du prix de vente. | La règle de 25-30 % ne s'applique qu'en phase 2. À ce stade, l'achat passe par 1688 ou Alibaba (300-1 000 unités), en fret maritime ou ferroviaire, avec un dédouanement normal : droits ad valorem de 0 à 6,5 % selon le code SH, à vérifier sur [TARIC][s-taric] (estimation), et TVA d'import récupérable. |
| À petite échelle, le micro-stock coûte presque autant que le dropshipping. Le port en France remplace le port depuis la Chine. | Le micro-stock sert à accéder à TikTok Shop et à livrer en 2-4 jours ; le coût unitaire reste quasi inchangé. |
| Sur TikTok Shop, commission de 9 % et affiliation de 15 % comprises, il reste 3 à 5 € par commande. | Pendant les 60 jours à 4 % de commission, et avec une affiliation à 10 %, la marge du rouleau monte à ≈ 7,70 €. Il faut ensuite augmenter le panier avec des lots de même catégorie : un seul droit de 3 € par colis. |
| Un lot de deux catégories tarifaires différentes envoyé de Chine paie 6 € de droit au lieu de 3 €. | Les lots se composent d'articles de même catégorie (deux rouleaux, deux tapis), ou se constituent à partir du stock en France. |
| Le budget de 150 € ne finance qu'un seul micro-stock à la fois (80-103 €). | Les tests sont séquentiels : un seul produit est stocké pour TikTok Shop, les autres restent en dropshipping sur le site. |

---

## 3 bis. Top 5 : produits concrets

### P1 — Rouleau anti-poils réutilisable autonettoyant (niche N2, score 77)

| Rubrique | Contenu |
|---|---|
| Spécification à exiger | Rouleau à brosse en nylon et réservoir à clapet, sans adhésif ni pile ; poignée ABS ; ≈ 250-300 g ; notice et avertissements en français (GPSR) ; nom et adresse du fabricant |
| Fournisseurs de référence | [AliExpress 1005008948630642][f-roul-1] ; [AliExpress 1005010323493766][f-roul-2] ; [recherche AliExpress « pet hair remover reusable »][f-roul-3] ; référence haut de gamme [Youpin POPO 1005011845470631][f-roul-4] |
| Prix fournisseur observé | 1,33 à 6,23 $ (≈ 1,15-5,35 €). Une annonce affiche plus de 10 000 ventes. Modèle haut de gamme à 22,09 $. Index de recherche du 12/10/2026, à revérifier en direct. |
| Délai vers la France | 7-15 jours (Choice). Expédition depuis l'UE possible selon l'annonce, non vérifiée par référence (§3.4). |
| Entrepôt UE | Non confirmé pour ce SKU. Le micro-stock en France est la voie fiable. |
| Signaux de demande | Google Trends FR : « anti poils » +11 % sur un an, +42 % sur 4-5 ans. Amazon.fr, catégorie « Gants et rouleaux de toilettage » chiens : n° 1 = rouleau ACE2ACE à 25,99 € ([meilleures ventes][a-rouleaux-chien]). Aux États-Unis, le ChomChom cumule plus de 98 000 avis 5 étoiles et s'est fait connaître sur TikTok ([Mental Floss][s-chomchom]). Hashtags TikTok : chiffres non vérifiables sans connexion (§6). |
| Prix de vente cible | 24,90 € à l'unité ; 39,90 € les deux (même catégorie, un seul droit) |
| Accroche vidéo (3 s) | Un aller-retour sur un canapé en velours couvert de poils de chat, puis ouverture du réservoir plein |
| Risques | (1) Design potentiellement protégé : vérifier [EUIPO DesignView][s-designview] et [INPI][s-inpi], ne jamais utiliser le nom « ChomChom ». (2) Efficacité faible sur tissus lisses : le dire dans la vidéo. (3) Clones à 1-5 $ : la différence se fait sur la livraison en 48 h depuis la France, la garantie et la démonstration par type de tissu. |

### P2 — Tapis de fouille lavable, formats M et L (niche N3, score 76)

| Rubrique | Contenu |
|---|---|
| Spécification à exiger | Polaire ou feutre teint sans azoïques, base antidérapante, lavable en machine, deux tailles (≈ 45×30 cm et 70×50 cm), 300-700 g ; avertissement d'utilisation sous surveillance (risque d'ingestion) |
| Fournisseurs de référence | [AliExpress 1005002611412566][f-fouille-1] ; [recherche AliExpress « dog snuffle mat »][f-fouille-2] ; [CJ, jouet de fouille serpent][f-fouille-cj1] ; [CJ, tapis et carotte][f-fouille-cj2] |
| Prix fournisseur observé | AliExpress : 3,33 $ (plus de 4 000 ventes) à 17,78 $ ; référence ci-dessus de 5,28 à 17,78 $ (plus de 1 000 ventes). CJ : jouet serpent à 3,84 $. Index de recherche du 12/10/2026. |
| Délai vers la France | 7-15 jours (AliExpress), 7-14 jours (CJ Chine) |
| Entrepôt UE | Non confirmé. Les entrepôts UE de CJ sont à filtrer dans le catalogue. |
| Signaux de demande | « tapis de fouille » +11 % sur un an, pic en novembre (indice 1,3) ; « jouet chien » +19 % ; « gamelle anti glouton » +10 %. zooplus.fr référence 48 produits (tapis de fouille, tapis de léchage, gamelles anti-glouton) entre 1,99 et 62,49 € ([catégorie][z-fouille]). Aucun tapis de fouille dans le top 30 Amazon.fr des jouets pour chien ([meilleures ventes][a-jouets-chien]), signe d'une niche peu verrouillée par Amazon. |
| Prix de vente cible | 29,90 € (M) ; 39,90 € (L) ; 54,90 € le lot « 2 tapis + guide de 15 jeux de flair » |
| Accroche vidéo (3 s) | Croquettes cachées, puis un chien qui fouille 10 minutes sans rien détruire. Variante : « mon chien seul à la maison ». |
| Risques | Population canine en baisse. Imitation de designs d'artisans : créer ses propres motifs. Creux en juin (indice 0,49). |

### P3 — Hamac de fenêtre pliable pour chat, ventouses et câbles acier (niche N1, score 69)

| Rubrique | Contenu |
|---|---|
| Spécification à exiger | Cadre acier, 4 ventouses de 8-9 cm de diamètre avec câbles, charge annoncée ≥ 18 kg, housse amovible et lavable, pliable ; poids 1,2-1,7 kg ; certificat de test de charge ; notice illustrée en français (vitre lisse, dégraissage, contrôle mensuel) |
| Fournisseurs de référence | [AliExpress 1005003142833115][f-hamac-1] ; [AliExpress 1005009054696873][f-hamac-2] ; [recherche AliExpress « cat window perch with suction cups »][f-hamac-3] |
| Prix fournisseur observé | 9 à 27 $. Un modèle pliable à 17,97 $ affiche plus de 5 000 ventes ; un modèle en velours est à 24,54 $. Index de recherche du 12/10/2026. |
| Délai vers la France | 7-15 jours |
| Entrepôt UE | Probable chez les vendeurs Amazon.fr. Les partenaires zooplus annoncent 8-11 jours ouvrés, donc probablement une expédition depuis l'Asie ([zooplus][z-hamac]). |
| Signaux de demande | « hamac chat » ≈ 2× le repère (−5 % sur un an), pic en décembre (1,25) ; « lit chat » ≈ 9× (+7 %). Amazon.fr, « Tapis de fenêtre » : 30 références de 12,36 à 69,99 €, dont EDAGNY à 37,99 € noté 4,7 ([meilleures ventes][a-fenetre]). Les boutiques françaises spécialisées ajoutent de nouveaux modèles entre août et décembre 2025 (§4). |
| Prix de vente cible | 44,90 € ; 54,90 € avec le tapis auto-chauffant (P4) |
| Accroche vidéo (3 s) | Le chat qui saute sur le hamac collé à la vitre, vu depuis l'extérieur |
| Risques | Chute du chat si une ventouse lâche : responsabilité produit (GPSR). Il faut un vrai test de charge filmé (sac de 20 kg, 72 h) et des limites de compatibilité affichées (vitre d'au moins 74 × 64 cm pour un modèle comparable chez [zooplus/HausPets][z-hamac]). Retours pour cause d'incompatibilité. Micro-stock hors budget : vente sur Shopify uniquement en phase 0. |

### P4 — Tapis de rebord de fenêtre auto-chauffant pour chat, sans électricité (niche N1, score 69, saisonnier)

| Rubrique | Contenu |
|---|---|
| Spécification à exiger | Sherpa, couche réfléchissante interne (sans câble, sans pile), base antidérapante, ≈ 90 × 28 cm pour les rebords français, lavable, 300-500 g |
| Fournisseurs de référence | [AliExpress 1005011691079831][f-chauff-1] ; [AliExpress 1005012462046397][f-chauff-2] ; [recherche AliExpress « cat thermal mat »][f-chauff-3] |
| Prix fournisseur observé | 0,99 à 1,09 $ en promotion de bienvenue (prix barré de 6,72 à 21,31 $), avec très peu de ventes. Prix réaliste hors promotion : 3-6 € (estimation, confiance faible). |
| Délai vers la France | 7-15 jours |
| Entrepôt UE | Non confirmé |
| Signaux de demande | Amazon.fr, « Tapis de fenêtre » : Knupis auto-chauffant à 19,99 € classé n° 7 et n° 29, PiuPet à 19,98 € classé n° 23 ([meilleures ventes][a-fenetre]) ; zooplus : 4,49 à 29,49 € ([catégorie][z-hamac]). Google Trends « tapis chauffant chat » : volume faible, pic en janvier. Saison : octobre à février. |
| Prix de vente cible | 24,90 € ; vendu aussi en lot avec P3 |
| Accroche vidéo (3 s) | Vue en caméra thermique : le tapis est chaud là où le chat est couché, sans aucun fil |
| Risques | Aucune allégation de santé (« soulage l'arthrose » est interdit). Vente saisonnière : arrêt du produit en mars. Ancrage à 20 € sur Amazon : la qualité, la taille adaptée aux rebords français et le lot avec P3 justifient l'écart. |

### P5 — Kit de gestion des câbles « bureau net » (niche N9, score 66, diversification)

| Rubrique | Contenu |
|---|---|
| Spécification à exiger | Gaine refermable de 2 m, 20 clips adhésifs, une goulotte sous bureau de 40 cm, attaches velcro ; adhésif 3M ou équivalent testé ; 400-500 g ; aucune pièce électrique |
| Fournisseurs de référence | [Recherche AliExpress « cable management kit »][f-cable-1] ; [recherche AliExpress « under desk wire management »][f-cable-2] |
| Prix fournisseur observé | Kit de 173 pièces de 7,65 à 13,98 $. Goulotte seule à 3,79 $ (plus de 5 000 ventes). Clips de 1,09 à 1,78 $. Index de recherche du 12/10/2026. |
| Délai vers la France | 7-15 jours |
| Entrepôt UE | Probable chez CJ pour des accessoires génériques, non vérifié |
| Signaux de demande | « cache câble » +55 % sur un an, sur un volume faible (≈ 0,37× le repère), pic en mars. Références de prix : goulotte Digitus n° 1 chez Galaxus à 18,39 € ([lien][c-galaxus]) ; kit rétractable chez Leroy Merlin à 40,89 € ([lien][c-lm-cable]). |
| Prix de vente cible | 29,90 € |
| Accroche vidéo (3 s) | Avant/après sous un bureau de télétravail, en un seul plan |
| Risques | Différenciation faible face à Amazon ; volume de recherche faible ; achat unique sans suite. Ce produit ne sert que de second test si l'audience « animaux » ne répond pas. |

---

## 4. Concurrence du top 5

| Produit | Concurrents en France (prix TTC relevés) | Livraison concurrente | Angle de différenciation possible |
|---|---|---|---|
| P1 Rouleau anti-poils | Amazon.fr : ACE2ACE 25,99 € (n° 1), Wouble 15,99 €, PAKEWAY 14,99 €, Veddelholzer 14,95 €, gants de 5 à 13 € ([meilleures ventes][a-rouleaux-chien], [chats][a-rouleaux-chat]). zooplus : 17,59-25,99 €, 8-11 jours ouvrés pour les partenaires ([zooplus][z-poils]). [La Maison des Housses][c-maisonhousses] : 12,90 €. Trixie : 2,99 € ([La Compagnie des Animaux][c-trixie]). | 2-11 jours | Livraison en 48 h depuis la France. Démonstration honnête par tissu (velours, lin, tapis, siège auto), y compris là où le rouleau fonctionne mal. Lot de deux à 39,90 €. Garantie de 2 ans clairement affichée. Ligne de marque « maison avec animaux ». |
| P2 Tapis de fouille | [inooko][c-inooko] : 16,99-39,99 € (Duvo+, Pet PLAY, HugSmart). zooplus : 9,59-35,35 € (Trixie 19,54 €, IntiMeg 35,35 €) ([catégorie][z-fouille]). Artisans français : [Gueule d'Amour][c-gueuledamour] 56,90 €, [Lucienne la Parisienne][c-lucienne] 30 €, [Canigourmand][c-canigourmand] 39,99 €. [Oria & Co][c-oria] (format XXL). | 2-7 jours | Niveaux de difficulté (débutant, confirmé), guide en français de 15 jeux de flair rédigé avec un éducateur canin, tailles par poids de chien, lavable. Contenu pédagogique sur l'ennui du chien seul. |
| P3 Hamac de fenêtre | Boutiques françaises spécialisées (relevé de leurs catalogues publics le 12/10/2026) : [Chat Joueur][c-chatjoueur] 34,90-54,90 € (8 modèles créés d'août à décembre 2025) ; [Chat Mellow][c-chatmellow] 34,99-69,99 € ; [Amaccas][c-amaccas] 39,90-79,90 € ; [Satisfaction Félin][c-satisfelin] 29,50 €. zooplus : Karlie 49,99 € (238 avis), Trixie 41,99 €, lionto 41,95 € ([catégorie][z-hamac]). Amazon.fr : EDAGNY 37,99 €, GUUSII 38,19 €, Pecute 29,99-42,99 € ([meilleures ventes][a-fenetre]). | 2-11 jours | Test de charge filmé et publié. Compatibilité garantie (gabarit de vitre téléchargeable). Câble de sécurité anti-chute. Housse réversible. Lot avec P4 pour l'hiver. Positionnement « sécurité » face à des boutiques qui vendent le même produit sous dix noms différents. |
| P4 Tapis auto-chauffant | Amazon.fr : Knupis 19,99 €, PiuPet 19,98 €, Pet Prime 17,84 € ([meilleures ventes][a-fenetre]). zooplus : Aumüller 29,49 €, Modern Living 16,09 €, Trixie 10,49-10,99 €, zooplus Exclusive 4,49-12,29 € ([catégorie][z-hamac]). | 2-4 jours | Format adapté aux rebords français, démonstration en caméra thermique, lot avec P3, livraison en 48 h pendant la saison froide. |
| P5 Kit câbles | Galaxus : Digitus 18,39 € ([lien][c-galaxus]). Leroy Merlin : kit rétractable 40,89 € ([lien][c-lm-cable]). ManoMano : goulotte de 2 m ([lien][c-manomano-cable]). Amazon.fr : prix non relevés (recherche bloquée). | 2-5 jours | Kit composé par type de bureau (droit, d'angle, assis-debout) avec un tutoriel vidéo de 3 minutes. Ciblage télétravail et joueurs. |

Temu : présence probable sur les cinq produits, non vérifiée (site inaccessible aux outils d'analyse ; confiance faible). Action : aucun des cinq produits trouvé sur action.com lors des recherches du 12/10/2026 (confiance faible).

---

## 5. Recommandation classée

### 5.1 Classement

| Ordre | Produit | Canal de départ | Pourquoi à ce rang |
|---|---|---|---|
| 1 | **P1 Rouleau anti-poils** | Micro-stock de 20 unités (≈ 95 €) : TikTok Shop avec créateurs affiliés, et site Shopify | Meilleur score (77). Démonstration en 3 secondes. Problème quotidien dans une grande partie des foyers avec animal (60 % des Français possèdent un animal). Assez léger et bon marché pour ouvrir TikTok Shop dans le budget. Marge de 10 € par commande sur le site, 5 à 8 € sur TikTok Shop. |
| 2 | **P2 Tapis de fouille** | Shopify en dropshipping ; micro-stock si le signal de validation est atteint | Score 76. Faible présence d'Amazon. Pic de recherche en novembre, donc un lancement en octobre tombe bien. Marge de 13 € par commande. |
| 3 | **P3 Hamac de fenêtre** | Shopify en dropshipping uniquement | Panier le plus élevé (44,90-54,90 €) et marge de 14 € par commande. Contenu félin très partageable. Prix validé par quatre boutiques françaises. Stock hors budget, donc pas de TikTok Shop en phase 0. |
| 4 | **P4 Tapis auto-chauffant** | Shopify, en lot avec P3 ; micro-stock possible (≈ 83 €) | Fenêtre de vente d'octobre à février, donc à lancer maintenant ou à attendre l'automne 2027. Fait monter le panier de P3. |
| 5 | **P5 Kit câbles** | Shopify en dropshipping | Second test sur une audience différente (télétravail), seulement si les produits pour animaux échouent. Risque faible, potentiel faible. |

**Raisonnement d'ensemble :**

- **Cohérence de marque.** P1 à P4 s'adressent à la même cible : les foyers avec chat ou chien (60 % des Français, [FACCO][s-facco]). Une seule marque « maison et animaux » permet de réutiliser l'audience TikTok et Instagram, de vendre des lots et d'ajouter des produits sans repartir de zéro.
- **Le chat d'abord.** La France compte 16,6 M de chats contre 9,6 M de chiens, et la population canine recule ([FACCO][s-facco]). Le contenu félin se partage le mieux sur les réseaux.
- **Ordre de lancement.** Le budget ne finance qu'un micro-stock à la fois. Le premier va au produit le plus léger, le moins cher et le plus démontrable (P1). Les produits plus lourds (P3) passent par le site, ce qui convient à leur panier plus élevé.

### 5.2 Protocole de test et seuils de décision

Le seuil de validation est aligné sur [02-acquisition](02-acquisition.md) : au moins 10 commandes organiques en 14 jours, ou une vidéo à plus de 50 000 vues qui génère des clics.

| Étape | Durée | Action | Seuil « on continue » | Seuil « on arrête » |
|---|---|---|---|---|
| Pré-validation | 3 jours | Commande d'un échantillon par produit (P1, P2, P3). Vérification EUIPO/INPI. Test réel du produit filmé. | Le produit fonctionne comme annoncé, aucun design protégé identifié | Défaut constaté ou design protégé : on passe au produit suivant |
| Test de contenu | 14 jours par produit | 10 à 15 vidéos par produit (3 accroches × 3-5 variantes), publiées sur TikTok, Reels et Shorts | ≥ 1 vidéo > 50 000 vues avec ≥ 1 % de clics vers la boutique, ou ≥ 10 commandes | < 5 000 vues de moyenne après 10 vidéos et 0 commande |
| Micro-stock et TikTok Shop | 30 jours | 15-25 unités, ouverture TikTok Shop, 10-20 créateurs invités à 10-15 % | ≥ 3 commandes par jour pendant 7 jours | < 20 commandes sur 30 jours |
| Phase 2 | Après plus de 300 commandes cumulées | Import groupé (300-1 000 unités), 3PL, marque déposée à l'INPI | Coût livré ≤ 30 % | — |

Les seuils chiffrés sont des estimations (confiance moyenne). Ils servent de règle d'arrêt pour éviter de s'acharner sur un produit sans traction.

### 5.3 Ce qui ferait changer l'ordre

| Événement ou résultat | Effet sur le classement |
|---|---|
| TikTok Shop autorise les expéditions depuis un autre pays de l'UE pour une boutique française, ou FBT ouvre en France | P3 monte au rang 1 : stock chez FBT, panier le plus élevé, contenu le plus viral. |
| Budget de stock porté à 300 € ou plus | P3 en micro-stock (10 unités) ; P3 rejoint P1 au premier rang. |
| Un design ou un brevet UE protège le rouleau (EUIPO) | P1 sort du classement. P2 passe au rang 1. La niche N2 se recentre sur le gant et la raclette en caoutchouc. |
| La redevance de 2 € s'applique par article (et non par colis) | Les lots expédiés de Chine coûtent plus cher. Les produits à l'unité au prix le plus élevé (P3) gagnent un rang. |
| La société est en franchise de TVA | Les marges gagnent 3,5 à 7,5 € par commande. L'ordre reste identique ; sur TikTok Shop, la marge de P5 passe de 3,36 € à ≈ 8,30 € (estimation). |
| Le test de contenu de P1 échoue (seuils du §5.2) | P2 passe au rang 1 ; P4 prend le micro-stock en hiver. |
| Novembre-décembre 2026 (cadeaux) | P3 + P4 en lot cadeau et N5 (portraits personnalisés, sans stock) passent devant P2 pour la période. |
| Profits disponibles pour la phase 2 | N6 Pilates (« reformer pilates » +48 %, « pilates maison » +60 %) devient la première niche à importer en volume, sous une marque fitness distincte. Il faudra adhérer à la REP ASL. |
| Fournisseur autorisé ROKR/Robotime trouvé avec un stock UE | N8 (maquettes 3D, 40-60 €) devient un produit opportuniste pour le T4. |
| Temu, AliExpress ou Shein stockent massivement en Europe (comme Shein en Pologne) | Le critère de différenciation baisse pour tous les produits. La marque, le contenu et le service prennent plus de poids que le délai de livraison. |

### 5.4 Confrontation avec la thèse de départ

| Hypothèse de la thèse | Verdict | Données |
|---|---|---|
| Le dropshipping sert de phase de validation | **Confirmée sur le site, infirmée sur TikTok Shop** | TikTok Shop impose une expédition depuis la France en 2 + 4 jours ouvrés ([politique][s-tts-shipping]). Le site accepte 7-15 jours. |
| Acquisition 100 % organique au départ | **Confirmée, à condition d'un micro-stock** | Le canal organique le plus rentable (TikTok Shop avec affiliés) n'existe qu'avec un stock en France. |
| Réinvestir les profits en publicité | **Confirmée, sous condition de marge** | À 10-14 € de marge par commande, une acquisition payante n'est rentable qu'en dessous de ce coût par commande. La phase 2 (coût ≤ 30 %) doit précéder une publicité à grande échelle (estimation). |
| Marque propre et stock UE dès qu'un produit est validé | **Confirmée et renforcée** | Le droit de 3 € et la redevance de 2 € pénalisent chaque colis venu de Chine. Le stock UE de Shein a limité sa baisse à 15 %, contre 50 % pour Temu ([Joko via MacGeneration][s-macg-joko]). |
| Absence d'équivalent bon marché chez Temu ou Shein | **Partiellement vérifiable** | Les clones existent pour les cinq produits. La taxe réduit leur avantage, sans le supprimer. La différenciation repose sur le délai, la preuve et la marque. |
| Extension multi-pays UE | **Confirmée pour la phase 3** | Le marché français seul rend l'objectif de 7-10 M€ de CA mensuel très improbable (0,11-0,16 % de tout le e-commerce de produits français). |

---

## 6. Limites et vérifications à faire

| Point non vérifié | Pourquoi | Comment vérifier | Coût |
|---|---|---|---|
| Prix fournisseurs exacts, frais de port et stock UE par référence | AliExpress et CJ bloquent la lecture automatique (vérification humaine demandée) ; les prix viennent de l'index de recherche | Ouvrir chaque lien, choisir la France comme pays de livraison, filtrer par lieu d'expédition, commander un échantillon | 15-40 € d'échantillons |
| Vues des hashtags TikTok et Creative Center | Le Creative Center exige une connexion depuis 2025 (constaté le 12/10/2026) | Compte gratuit, puis [Creative Center][s-tcc] : #catsoftiktok, #chat, #snufflemat, #tapisdefouille, #pethair, #cablemanagement | 0 € |
| Pinterest Trends | Accès réservé aux comptes professionnels | Compte Pinterest professionnel gratuit, puis [Pinterest Trends][s-pintrends] : « hamac chat », « lit chat fenêtre », « jouet chien occupation » | 0 € |
| Prix et présence sur Temu | Site protégé contre l'analyse automatique | Recherche manuelle sur l'application Temu | 0 € |
| Assiette exacte de la redevance de 2 € (par colis ou par article) | Acte délégué en attente de publication au Journal officiel de l'UE | Surveiller la [page Réforme douanière de la Commission][s-ec-reform] | 0 € |
| Commission TikTok Shop par catégorie (animaux, maison) | Sources secondaires uniquement | Seller Center TikTok Shop France après inscription | 0 € |
| Designs protégés (rouleau, hamac) | Non recherché dans les registres | [EUIPO DesignView][s-designview], [INPI][s-inpi] | 0 € |
| Volumes Google Trends | Indices relatifs, sans volumes absolus | Google Keyword Planner (compte Google Ads sans dépense) | 0 € |

---

## Sources

Marché et comportements
- `s-fevad-bilan` : <https://www.fevad.com/bilan-du-e-commerce-en-france-les-francais-ont-depense-pres-de-200-milliards-deuros-sur-internet-en-2025/>
- `s-sellermania` : <https://www.sellermania.com/fr/blog/marketplaces/rapport-fevad-2026-chiffres-e-commerce-vendeurs-marketplace/>
- `s-fevad-cc2026` : <https://www.fevad.com/chiffres-cles-ecommerce-2026/>
- `s-fevad-q1` : <https://www.fevad.com/barometre-de-laudience-du-e-commerce-au-1er-trimestre-2026/>
- `s-fevad-q2` : <https://www.fevad.com/barometre-de-laudience-du-e-commerce-au-2eme-trimestre-2026/>
- `s-learnthings` : <https://www.learnthings.fr/chiffres-cles-de-le-commerce-en-france-donnees-fevad/>
- `s-datareportal` : <https://datareportal.com/reports/digital-2026-france>
- `s-medialeader-tiktok` : <https://fr.themedialeader.com/?p=112254>
- `s-opinionway` : <https://fr.themedialeader.com/ia-et-reseaux-sociaux-simposent-dans-les-parcours-dachat-de-la-gen-z/>
- `s-facco` : <https://www.lepointveterinaire.fr/veterinaire/planete-vet/animal-societe/possession-suivi-veterinaire-alimentation-dit-barometre-faccoodoxa-2026-15hngc3>
- `s-gt-animaux` : <https://trends.google.com/trends/explore?date=today%205-y&geo=FR&q=tapis%20de%20fouille,hamac%20chat,lit%20chat,anti%20poils,fontaine%20chat>
- Google Trends, comparaison Pilates et autres : https://trends.google.com/trends/explore?date=today%205-y&geo=FR&q=tapis%20de%20fouille,reformer%20pilates,pilates%20maison,boucles%20sans%20chaleur,cache%20c%C3%A2ble
- Google Trends, comparaison cadeaux T4 : https://trends.google.com/trends/explore?date=today%205-y&geo=FR&q=tapis%20de%20fouille,maquette%20bois,rokr,bijoux%20acier%20inoxydable,cadeau%20personnalis%C3%A9
- `s-heatless` : <https://www.timeslive.co.za/lifestyle/2024-05-20-hair-raising-trends-to-avoid-on-tiktok/>
- `s-chomchom` : <https://www.mentalfloss.com/posts/chomchom-pet-hair-remover>

TikTok Shop
- `s-lsa-tts` : <https://www.lsa-conso.fr/tiktok-shop-ouvre-aujourd-hui-en-france-carrefour-nous-devoile-sa-strategie,460007>
- `s-tts-33k` : <https://gensdinternet.fr/2026/03/13/plus-de-33-000-vendeurs-sont-presents-sur-tiktok-shop-en-france/>
- `s-tts-commission` : <https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/>
- `s-tts-shipping` : <https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897>
- `s-fbt` : <https://www.eurofiscalis.com/fbt-tiktok-shop-tva/>
- `s-tcc` : <https://ads.tiktok.com/business/creativecenter/>

Réglementation, fiscalité, logistique
- `s-douane-gouv` : <https://presse.economie.gouv.fr/?p=180373>
- `s-ec-reform` : <https://taxation-customs.ec.europa.eu/customs/eu-customs-reform_en>
- `s-eco-gouv-colis` : <https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-la-taxe-sur-les-petits-colis>
- `s-macg-joko` : <https://www.macg.co/ailleurs/2026/08/la-taxe-de-3-eu-fait-chuter-les-ventes-de-temu-shein-et-aliexpress-mais-des-contournements-restent-possibles-310523>
- `s-gpsr` : <https://eur-lex.europa.eu/eli/reg/2023/988/oj>
- `s-gpsr-jdn` : <https://www.journaldunet.com/retail/1547583-gpsr-quand-le-commerce-en-ligne-entre-dans-l-ere-de-la-responsabilite-produit/>
- `s-rep-asl` : <https://www.ecologic-france.com/storage/uploads/6a467c29b6de8/Guide-de-ladhrent-ASL.pdf>
- `s-rep-idu` : <https://lefreelance.fr/articles/rep-freelance-idu-eco-organisme-produits/>
- `s-l221-28` : <https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032226820>
- `s-tva` : <https://sparkreceipt.com/fr-fr/blog/franchise-en-base-de-tva/>
- `s-colissimo` : <https://www.laposte.fr/professionnel/tarif-colissimo>
- `s-mondialrelay` : <https://artisansdeuxpointzero.fr/mondial-relay-tarif-pro-artisan>
- `s-taric` : <https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp?Lang=fr>
- `s-designview` : <https://www.tmdn.org/tmdsview-web/>
- `s-inpi` : <https://data.inpi.fr/>
- `s-pintrends` : <https://trends.pinterest.com/>

Fournisseurs
- `s-cj-warehouses` : <https://cjdropshipping.com/blogs/cj-news/CJ-s-Global-Warehouses>
- `s-speedecom-cj` : <https://speed-ecom.eu/blog/cj-dropshipping-le-nouvel-aliexpress/>
- `s-ali-choice` : <https://www.vitepromo.com/shopping-ecommerce/code-promo-aliexpress>
- `s-gelato` : <https://www.gelato.com/fr/print-on-demand/france>
- `s-kitsch` : <https://www.mykitsch.com/fr/products/kit-coiffure-sans-chaleur>
- `f-roul-1` : <https://www.aliexpress.com/item/1005008948630642.html>
- `f-roul-2` : <https://www.aliexpress.com/item/1005010323493766.html>
- `f-roul-3` : <https://www.aliexpress.com/w/wholesale-pet-hair-remover-reusable.html>
- `f-roul-4` : <https://www.aliexpress.com/item/1005011845470631.html>
- `f-fouille-1` : <https://www.aliexpress.com/item/1005002611412566.html>
- `f-fouille-2` : <https://www.aliexpress.com/w/wholesale-dog-snuffle-mat.html>
- `f-fouille-cj1` : <https://cjdropshipping.com/product/snake-snuffle-toy-for-dogs-pet-slow-feeder-feeder-puzzle-nosework-toys-dog-enrichment-puzzle-p-1509073837051760640.html>
- `f-fouille-cj2` : <https://cjdropshipping.com/product/pet-dog-toys-carrot-plush-toy-vegetable-chew-toy-for-dogs-snuffle-mat-for-dogs-cats-durable-chew-puppy-toy-dogs-accessories-p-1455000172097572864.html>
- `f-hamac-1` : <https://www.aliexpress.com/item/1005003142833115.html>
- `f-hamac-2` : <https://he.aliexpress.com/item/1005009054696873.html>
- `f-hamac-3` : <https://www.aliexpress.com/w/wholesale-cat-window-perch-with-suction-cups.html>
- `f-chauff-1` : <https://www.aliexpress.com/item/1005011691079831.html>
- `f-chauff-2` : <https://vi.aliexpress.com/item/1005012462046397.html>
- `f-chauff-3` : <https://pt.aliexpress.com/w/wholesale-cat-thermal-mat.html>
- `f-cable-1` : <https://www.aliexpress.com/w/wholesale-cable-management-kit.html>
- `f-cable-2` : <https://www.aliexpress.com/w/wholesale-under-desk-wire-management.html>
- `f-pilates-bar` : <https://www.aliexpress.com/item/1005009960252597.html>
- `f-pilates-board` : <https://www.aliexpress.com/item/1005012058587880.html>
- `f-bijou` : <https://fr.aliexpress.com/categories/collier-personnalis%C3%A9-pr%C3%A9nom-chien.html>

Concurrence et relevés de prix (12/10/2026)
- `a-rouleaux-chien` : <https://www.amazon.fr/gp/bestsellers/pet-supplies/2036748031>
- `a-rouleaux-chat` : <https://www.amazon.fr/gp/bestsellers/pet-supplies/2036607031>
- `a-fenetre` : <https://www.amazon.fr/gp/bestsellers/pet-supplies/2036572031>
- `a-jouets-chien` : <https://www.amazon.fr/gp/bestsellers/pet-supplies/2036807031>
- Amazon.fr Pilates : https://www.amazon.fr/gp/bestsellers/sports/493336031 ; Bigoudis : https://www.amazon.fr/gp/bestsellers/beauty/2984902031 ; Puzzles 3D : https://www.amazon.fr/gp/bestsellers/toys/363690031
- `z-hamac` : <https://www.zooplus.fr/shop/chats/paniers_lits_couvertures_chat/hamacs_fenetre_chat>
- `z-fouille` : <https://www.zooplus.fr/shop/chiens/bols_gamelles_fontaines/tapis_lechage_fouille>
- `z-poils` : <https://www.zooplus.fr/shop/chiens/desodorisants/elimination_poils/9980052936>
- `c-chatjoueur` : <https://chatjoueur.com/collections/hamac-chat-fenetre>
- `c-chatmellow` : <https://chatmellow.com/collections/hamac-pour-chat>
- `c-amaccas` : <https://amaccas.com/collections/hamac-chat-fenetre>
- `c-satisfelin` : <https://www.satisfactionfelin.com/products/hamac-chat-fenetre>
- `c-inooko` : <https://inooko.com/collections/tapis-fouille-chien>
- `c-gueuledamour` : <https://www.gueule-damour.com/fr/391-tapis-de-fouille-pour-chien>
- `c-lucienne` : <https://luciennelaparisienne.fr/en/product/tapis-de-fouille/>
- `c-canigourmand` : <https://www.canigourmand.com/jouets-d-intelligence/980-tapis-de-fouille-3760361284200.html>
- `c-oria` : <https://www.oria-co.com/products/tapis-de-fouille>
- `c-maisonhousses` : <https://www.lamaisondeshousses.fr/products/rouleau-anti-poils-danimaux>
- `c-trixie` : <https://www.lacompagniedesanimaux.com/trixie-brosse-roller-rouleau-adhesif-anti-poils.html>
- `c-galaxus` : <https://www.galaxus.fr/en/s4/producttype/toplist/relevance/cable-trunking-2899>
- `c-lm-cable` : <https://www.leroymerlin.fr/produits/cable-management-gestion-cable-bureau-sans-percage-retractable-de-30-5cm-a-55cm-kit-cable-management-organisateur-de-cable-pour-bureau-a-domicile-97075625.html>
- `c-manomano-cable` : <https://www.manomano.fr/p/kit-de-gestion-de-cables-2-metres-organisateur-de-cables-goulotte-de-cables-chemin-de-cables-mural-auto-adhesif-gaine-de-cable-auto-fermante-noir-240277648>
- `c-monchouchou` : <https://monchouchou.app/>
- `c-petprinted` : <https://petprinted.fr/collections/poster>
- `c-thinkart` : <https://thinkart.store/>
- `c-votreportrait` : <https://www.votreportrait.fr/fr/217-portrait-animal-personnalise>

[s-fevad-bilan]: https://www.fevad.com/bilan-du-e-commerce-en-france-les-francais-ont-depense-pres-de-200-milliards-deuros-sur-internet-en-2025/
[s-sellermania]: https://www.sellermania.com/fr/blog/marketplaces/rapport-fevad-2026-chiffres-e-commerce-vendeurs-marketplace/
[s-fevad-cc2026]: https://www.fevad.com/chiffres-cles-ecommerce-2026/
[s-fevad-q1]: https://www.fevad.com/barometre-de-laudience-du-e-commerce-au-1er-trimestre-2026/
[s-fevad-q2]: https://www.fevad.com/barometre-de-laudience-du-e-commerce-au-2eme-trimestre-2026/
[s-learnthings]: https://www.learnthings.fr/chiffres-cles-de-le-commerce-en-france-donnees-fevad/
[s-datareportal]: https://datareportal.com/reports/digital-2026-france
[s-medialeader-tiktok]: https://fr.themedialeader.com/?p=112254
[s-opinionway]: https://fr.themedialeader.com/ia-et-reseaux-sociaux-simposent-dans-les-parcours-dachat-de-la-gen-z/
[s-facco]: https://www.lepointveterinaire.fr/veterinaire/planete-vet/animal-societe/possession-suivi-veterinaire-alimentation-dit-barometre-faccoodoxa-2026-15hngc3
[s-gt-animaux]: https://trends.google.com/trends/explore?date=today%205-y&geo=FR&q=tapis%20de%20fouille,hamac%20chat,lit%20chat,anti%20poils,fontaine%20chat
[s-heatless]: https://www.timeslive.co.za/lifestyle/2024-05-20-hair-raising-trends-to-avoid-on-tiktok/
[s-chomchom]: https://www.mentalfloss.com/posts/chomchom-pet-hair-remover
[s-lsa-tts]: https://www.lsa-conso.fr/tiktok-shop-ouvre-aujourd-hui-en-france-carrefour-nous-devoile-sa-strategie,460007
[s-tts-33k]: https://gensdinternet.fr/2026/03/13/plus-de-33-000-vendeurs-sont-presents-sur-tiktok-shop-en-france/
[s-tts-commission]: https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/
[s-tts-shipping]: https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897
[s-fbt]: https://www.eurofiscalis.com/fbt-tiktok-shop-tva/
[s-tcc]: https://ads.tiktok.com/business/creativecenter/
[s-douane-gouv]: https://presse.economie.gouv.fr/?p=180373
[s-ec-reform]: https://taxation-customs.ec.europa.eu/customs/eu-customs-reform_en
[s-eco-gouv-colis]: https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-la-taxe-sur-les-petits-colis
[s-macg-joko]: https://www.macg.co/ailleurs/2026/08/la-taxe-de-3-eu-fait-chuter-les-ventes-de-temu-shein-et-aliexpress-mais-des-contournements-restent-possibles-310523
[s-gpsr]: https://eur-lex.europa.eu/eli/reg/2023/988/oj
[s-gpsr-jdn]: https://www.journaldunet.com/retail/1547583-gpsr-quand-le-commerce-en-ligne-entre-dans-l-ere-de-la-responsabilite-produit/
[s-rep-asl]: https://www.ecologic-france.com/storage/uploads/6a467c29b6de8/Guide-de-ladhrent-ASL.pdf
[s-rep-idu]: https://lefreelance.fr/articles/rep-freelance-idu-eco-organisme-produits/
[s-l221-28]: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032226820
[s-tva]: https://sparkreceipt.com/fr-fr/blog/franchise-en-base-de-tva/
[s-colissimo]: https://www.laposte.fr/professionnel/tarif-colissimo
[s-mondialrelay]: https://artisansdeuxpointzero.fr/mondial-relay-tarif-pro-artisan
[s-taric]: https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp?Lang=fr
[s-designview]: https://www.tmdn.org/tmdsview-web/
[s-inpi]: https://data.inpi.fr/
[s-pintrends]: https://trends.pinterest.com/
[s-cj-warehouses]: https://cjdropshipping.com/blogs/cj-news/CJ-s-Global-Warehouses
[s-speedecom-cj]: https://speed-ecom.eu/blog/cj-dropshipping-le-nouvel-aliexpress/
[s-ali-choice]: https://www.vitepromo.com/shopping-ecommerce/code-promo-aliexpress
[s-gelato]: https://www.gelato.com/fr/print-on-demand/france
[s-kitsch]: https://www.mykitsch.com/fr/products/kit-coiffure-sans-chaleur
[f-roul-1]: https://www.aliexpress.com/item/1005008948630642.html
[f-roul-2]: https://www.aliexpress.com/item/1005010323493766.html
[f-roul-3]: https://www.aliexpress.com/w/wholesale-pet-hair-remover-reusable.html
[f-roul-4]: https://www.aliexpress.com/item/1005011845470631.html
[f-fouille-1]: https://www.aliexpress.com/item/1005002611412566.html
[f-fouille-2]: https://www.aliexpress.com/w/wholesale-dog-snuffle-mat.html
[f-fouille-cj1]: https://cjdropshipping.com/product/snake-snuffle-toy-for-dogs-pet-slow-feeder-feeder-puzzle-nosework-toys-dog-enrichment-puzzle-p-1509073837051760640.html
[f-fouille-cj2]: https://cjdropshipping.com/product/pet-dog-toys-carrot-plush-toy-vegetable-chew-toy-for-dogs-snuffle-mat-for-dogs-cats-durable-chew-puppy-toy-dogs-accessories-p-1455000172097572864.html
[f-hamac-1]: https://www.aliexpress.com/item/1005003142833115.html
[f-hamac-2]: https://he.aliexpress.com/item/1005009054696873.html
[f-hamac-3]: https://www.aliexpress.com/w/wholesale-cat-window-perch-with-suction-cups.html
[f-chauff-1]: https://www.aliexpress.com/item/1005011691079831.html
[f-chauff-2]: https://vi.aliexpress.com/item/1005012462046397.html
[f-chauff-3]: https://pt.aliexpress.com/w/wholesale-cat-thermal-mat.html
[f-cable-1]: https://www.aliexpress.com/w/wholesale-cable-management-kit.html
[f-cable-2]: https://www.aliexpress.com/w/wholesale-under-desk-wire-management.html
[f-pilates-bar]: https://www.aliexpress.com/item/1005009960252597.html
[f-pilates-board]: https://www.aliexpress.com/item/1005012058587880.html
[f-bijou]: https://fr.aliexpress.com/categories/collier-personnalis%C3%A9-pr%C3%A9nom-chien.html
[a-rouleaux-chien]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036748031
[a-rouleaux-chat]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036607031
[a-fenetre]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036572031
[a-jouets-chien]: https://www.amazon.fr/gp/bestsellers/pet-supplies/2036807031
[z-hamac]: https://www.zooplus.fr/shop/chats/paniers_lits_couvertures_chat/hamacs_fenetre_chat
[z-fouille]: https://www.zooplus.fr/shop/chiens/bols_gamelles_fontaines/tapis_lechage_fouille
[z-poils]: https://www.zooplus.fr/shop/chiens/desodorisants/elimination_poils/9980052936
[c-chatjoueur]: https://chatjoueur.com/collections/hamac-chat-fenetre
[c-chatmellow]: https://chatmellow.com/collections/hamac-pour-chat
[c-amaccas]: https://amaccas.com/collections/hamac-chat-fenetre
[c-satisfelin]: https://www.satisfactionfelin.com/products/hamac-chat-fenetre
[c-inooko]: https://inooko.com/collections/tapis-fouille-chien
[c-gueuledamour]: https://www.gueule-damour.com/fr/391-tapis-de-fouille-pour-chien
[c-lucienne]: https://luciennelaparisienne.fr/en/product/tapis-de-fouille/
[c-canigourmand]: https://www.canigourmand.com/jouets-d-intelligence/980-tapis-de-fouille-3760361284200.html
[c-oria]: https://www.oria-co.com/products/tapis-de-fouille
[c-maisonhousses]: https://www.lamaisondeshousses.fr/products/rouleau-anti-poils-danimaux
[c-trixie]: https://www.lacompagniedesanimaux.com/trixie-brosse-roller-rouleau-adhesif-anti-poils.html
[c-galaxus]: https://www.galaxus.fr/en/s4/producttype/toplist/relevance/cable-trunking-2899
[c-lm-cable]: https://www.leroymerlin.fr/produits/cable-management-gestion-cable-bureau-sans-percage-retractable-de-30-5cm-a-55cm-kit-cable-management-organisateur-de-cable-pour-bureau-a-domicile-97075625.html
[c-manomano-cable]: https://www.manomano.fr/p/kit-de-gestion-de-cables-2-metres-organisateur-de-cables-goulotte-de-cables-chemin-de-cables-mural-auto-adhesif-gaine-de-cable-auto-fermante-noir-240277648
[c-monchouchou]: https://monchouchou.app/
[c-petprinted]: https://petprinted.fr/collections/poster
[c-thinkart]: https://thinkart.store/
[c-votreportrait]: https://www.votreportrait.fr/fr/217-portrait-animal-personnalise
