# Économie du studio — revenus plateformes et coûts unitaires

> Consulté le : 2026-09-28 · Auteur : researcher · Version : 1 · Portée : paramètres chiffrés sourcés (RPM, seuils d'éligibilité, coûts unitaires de production) destinés à alimenter `docs/COST_MODEL.md`. Ce n'est pas un modèle de coût complet ni un calcul de rentabilité par chaîne.

## Synthèse

- YouTube reverse 55 % net aux créateurs en long format, 45 % du Creator Pool en Shorts (page officielle) [S1][S6]. Éligibilité YPP actuelle : 1 000 abonnés + 4 000 h de visionnage/12 mois OU 10 M de vues Shorts/90 j ; ces seuils **doublent au 1er février 2027** (8 000 h / 20 M de vues Shorts) pour les nouveaux entrants, les partenaires déjà actifs sont conservés [S2][S5][S16].
- Depuis le 24/08/2026, le compteur de vues démarre dès la lecture, mais monétisation et éligibilité YPP restent basées sur les « engaged views » : aucun changement de revenu annoncé [S3].
- Les pistes audio multilingues génèrent en moyenne > 25 % du watch time hors langue principale (chiffre officiel YouTube) [S4].
- RPM long format très dépendant du pays et de la niche : France ~2,3 $/1000 vues en moyenne généraliste, États-Unis ~5,9 $ [S15] ; la niche éducation/science a une médiane de ~10,22 $ sur un panel de 300 chaînes **sans pays précisé**, 9-18 $ selon les études [S17][S18]. Aucune source ne donne un RPM éducation/science propre à la France.
- RPM Shorts : 0,01 à 0,25 $/1000 vues selon niche et pays, repère généraliste 0,07-0,20 $ [S15][S17][S18].
- TikTok Creator Rewards : officiellement ouvert en France, seuils 10 000 abonnés + 100 000 vues/30 j, vidéo > 1 min, ≥ 1 000 vues qualifiées/vidéo [S7]. RPM France observé ~0,60-0,80 €/1000 vues (source non officielle) [S25]. L'exclusion du contenu « entièrement IA » n'est confirmée par aucun texte officiel trouvé — seulement des sources secondaires, comme le note déjà MISSION §4 [S26].
- Distribution des vues : loi de puissance confirmée par échantillonnage aléatoire (McGrady/Zuckerman, UMass) — 86,9 % des vidéos YouTube ont moins de 1 000 vues, médiane à 35 vues, 3,7 % des vidéos concentrent 93,6 % des vues [S21][S22][S23].
- Électricité France (tarif réglementé EDF, option Base, 6 kVA) : 0,2001 €/kWh depuis le 1er août 2026, hausse confirmée officiellement par la CRE (+2,5 % TTC) [S8][S14].
- RTX 4070 Ti Super : TGP officiel NVIDIA 285 W, alimentation système recommandée 700 W [S9]. Carte retirée des catalogues neufs constatés (gamme RTX 50 uniquement) → marché occasion ~430-950 € [S27][S28].
- Claude Max : 100 $ (5x) et 200 $ (20x)/mois, prix affichés hors taxe, aucun tarif EUR officiel [S10]. Taux BCE du 2026-09-25 : 1 €  = 1,1403 $ [S13].
- Coûts non vérifiés faute de budget de recherche disponible en fin de session : €/To stockage, délai moyen avant premier revenu de sponsoring, probabilité statistique qu'une nouvelle chaîne atteigne l'éligibilité YPP (voir « Questions ouvertes »).

## Constats

| # | Constat | Sources | Confiance | Conséquence pour le studio |
|---|---|---|---|---|
| 1 | Partage de revenus YouTube long format : 55 % des revenus nets publicitaires versés au créateur sur la Watch Page. | [S1] | élevée | Base de calcul du registre des coûts §6 principe 4 de MISSION. |
| 2 | Partage de revenus Shorts : 45 % du montant alloué au créateur via le Creator Pool, après déduction d'un coût de licence musicale (~50 % si 1 piste, ~67 % si 2 pistes), calculé sur la part de vues engagées du créateur parmi les créateurs monétisés du même pays. | [S1][S6] | élevée | Le RPM Shorts réel dépend fortement de l'usage de musique sous licence ; éviter la musique commerciale sur les Shorts maximise la part réellement perçue. |
| 3 | Éligibilité YPP actuelle (2026) : 1 000 abonnés + (4 000 h de visionnage qualifié sur 12 mois OU 10 M de vues Shorts qualifiées sur 90 j) ; les deux voies ne se cumulent pas ; les heures de visionnage Shorts ne comptent pas dans les 4 000 h. Palier « Fan Funding » à 500 abonnés + 3 000 h ou 3 M de vues Shorts (pas de partage publicitaire). | [S2][S16] | élevée | Le plan de lancement doit prévoir un chemin explicite « Shorts d'abord » ou « long d'abord » selon la chaîne, jamais un mélange des deux compteurs. |
| 4 | Changement programmé au 1er février 2027 : nouveaux seuils YPP doublés (8 000 h ou 20 M de vues Shorts/90 j) pour tout nouvel entrant ; les partenaires déjà acceptés sont conservés sans nouvelle condition. Le seuil Shorts (10 M vues/90 j, glissant) devient aussi une condition de maintien du partage Shorts, pas seulement d'entrée. | [S5][S16] | élevée | Lancer les 2 chaînes avant le 01/02/2027 réduit le seuil d'entrée de moitié ; à documenter dans `docs/PLAN.md` comme contrainte de calendrier. |
| 5 | Depuis le 24/08/2026, le compteur de « vue » public démarre dès la première image ; c'est la notion d'« engaged view » (clic + visionnage au-delà des premières secondes) qui a pris l'ancienne définition. Monétisation et éligibilité YPP restent basées sur les engaged views / watch hours qualifiées : YouTube affirme explicitement l'absence d'impact sur les revenus. | [S3] | élevée | Confirme MISSION §4 « Mesure des vues » : jamais piloter sur le compteur brut, toujours sur watch time et engaged views. |
| 6 | Pistes audio multilingues : en moyenne plus de 25 % du watch time d'une vidéo dotée de pistes multilingues provient de la langue non principale (donnée officielle YouTube, juillet 2025). Fonctionnalité de doublage auto disponible pour tous les créateurs depuis septembre 2025, 27 langues, > 6 M de spectateurs quotidiens regardant > 10 min de contenu doublé (déc. 2025). | [S4] | élevée | Argument fort pour prioriser tôt une piste anglaise (ou doublage auto) sur les chaînes françaises : gain de watch time significatif et quasi gratuit à produire (TTS déjà dans le pipeline). |
| 7 | RPM long format France (contenu généraliste) : ~2,29 $/1000 vues (données août 2026, panel « 87 marchés »), fourchette réaliste 1,20-3,50 $. RPM long format États-Unis : ~5,90 $/1000 vues, soit ~2,6× la France. | [S15] | moyenne | Cohérent avec le repère du skill `scenariste-youtube` (non reproduits) — voir « Écarts avec MISSION §4 ». |
| 8 | RPM niche Éducation/Science : le plus élevé de toutes les niches YouTube étudiées, médiane ~10,22 $/1000 vues (panel de 300 chaînes, 3 595 mois-chaîne, mai 2025-mai 2026), avec des sous-études donnant 9-14 $ (Education & Learning) et 14,97-18,23 $ pour une étude AIR spécifique à l'éducation. | [S17][S18] | moyenne | Le panel ne précise pas les pays : l'écart éducation/généraliste est un indice favorable aux concepts retenus, pas un RPM France. |
| 9 | RPM Shorts généraliste : 0,01-0,07 $/1000 vues le plus souvent citées, jusqu'à 0,15-0,25 $ dans les niches à forte valeur publicitaire (finance, tech B2B) ; étude AIR (via Digitiz) donne 0,07-0,20 $ selon niche. | [S15][S17] | moyenne | Les Shorts restent un canal de distribution/entonnoir plutôt qu'une source de revenu directe, cohérent avec MISSION §4 « TikTok = distribution » appliqué aussi aux Shorts YouTube. |
| 10 | TikTok Creator Rewards Program — conditions officielles (Conditions EEA, couvrant la France) : compte personnel (pas Business), en règle avec les CGU, ≥ 10 000 abonnés authentiques, ≥ 100 000 vues vidéo authentiques sur 30 jours, vidéo ≥ 1 minute, ≥ 1 000 « vues qualifiées » (regardées ≥ 5 s, non marquées « pas intéressé ») par vidéo, contenu original (pas de Duet/Stitch/Photo Mode), pas de contenu publicitaire/sponsorisé, seuil de paiement 50 $. | [S7] | élevée | Confirme et précise MISSION §4 : la France est bien un pays éligible ; le seuil d'entrée (10 000 abonnés) est significativement plus dur à atteindre que YPP Fan Funding YouTube (500 abonnés). |
| 11 | Aucune mention, dans les conditions officielles TikTok consultées, d'une exclusion générale du contenu « entièrement généré par IA » pour le Creator Rewards Program. Cette exclusion n'existe que dans des sources secondaires non sourcées officiellement, qui reconnaissent elles-mêmes l'absence de seuil publié par TikTok pour le contenu hybride IA/humain. | [S7][S26] | faible (pour l'exclusion IA) / élevée (pour l'absence de mention officielle) | Ne pas bâtir d'architecture sur une exclusion IA non confirmée, mais garder la divulgation AIGC (déjà prévue MISSION §4) et revérifier avant chaque campagne TikTok. |
| 12 | RPM TikTok Creator Rewards observé par pays (sources praticiennes, non officielles, TikTok ne publie aucun chiffre) : Royaume-Uni 1,00-1,30 £, Allemagne 0,70-0,90 €, **France 0,60-0,80 €**, Italie 0,45-0,65 €, Espagne 0,40-0,60 € pour 1000 vues qualifiées ; moyenne UE ~0,50 €. Autre source (illustrative) : exemple de calcul à 0,72 $ RPM. | [S25][S24] | faible | RPM TikTok France ≈ 4-8× inférieur au RPM YouTube long format France ; confirme MISSION §4 « TikTok = distribution, entonnoir vers YouTube » plutôt que source de revenu. |
| 13 | TikTok Shop Affiliate existe comme flux de revenu séparé (commission fixée par le vendeur sur les ventes attribuées) mais aucune source consultée ne quantifie sa pertinence spécifique pour les niches histoire/science/éducation/fiction de ce studio. | [S24] | faible | Ne pas compter sur TikTok Shop dans le modèle de coût initial ; affiliation classique (livres, cours en ligne) reste une piste plus alignée avec ces niches mais non chiffrée par les sources trouvées. |
| 14 | CPM de sponsoring direct pour la niche Éducation : 20-40 $ (repère central utilisé comme base de calcul par plusieurs praticiens pour les niches adjacentes), à comparer aux 5-18 $ d'AdSense pour la même niche — donc 2-4× le revenu publicitaire pur. Niches adjacentes IA/productivité 28-55 $, Tech 25-45 $. | [S19][S20] | moyenne | Le sponsoring reste hors-cadre du studio (§5 MISSION : aucune API externe de génération, mais le sponsoring n'est pas une génération) — à considérer comme revenu complémentaire possible, non un prérequis. |
| 15 | Distribution des vues YouTube — loi de puissance confirmée par échantillonnage aléatoire véritable (méthode « dialing », pas un panel de chaînes populaires) : 86,93 % des vidéos ont < 1 000 vues, 65,44 % ont < 100 vues, médiane 35 vues, moyenne 5 868 vues (écart énorme dû à la queue) ; seules 3,67 % des vidéos dépassent 10 000 vues mais concentrent 93,61 % des vues totales. Étude publiée dans une revue à comité de lecture (Journal of Quantitative Description), équipe UMass Amherst (Zuckerman et al.), échantillon construit sur les identifiants YouTube 11 caractères de 2023, ~9,9 milliards de vidéos estimées fin 2022. | [S21][S22][S23] | élevée (existence et ordre de grandeur de la loi de puissance) / moyenne (chiffres précis, lus via un résumé secondaire, PDF source non accessible cette session) | Confirme directement MISSION §2 : « la distribution des vues suit une loi de puissance ; aucun logiciel ne garantit un volume de vues ». Le studio doit mesurer son succès en probabilité d'outlier, pas en vues moyennes attendues. |
| 16 | Aucune statistique agrégée trouvée sur le délai ou la probabilité qu'une nouvelle chaîne atteigne l'éligibilité YPP (1 000 abonnés + 4 000 h). Les seuls repères trouvés sont anecdotiques et très dispersés (de 3-4 mois dans un scénario optimiste à plusieurs années), sans méthodologie statistique publiée. | [S16] | faible | Ne pas fixer d'objectif calendaire de monétisation dans `docs/PLAN.md` sans le marquer comme hypothèse ; NEEDS_HUMAN si un objectif chiffré est requis par ailleurs. |
| 17 | Tarif réglementé de vente d'électricité (TRVE) « Tarif Bleu », option Base, 6 kVA : 0,2001 €/kWh, abonnement annuel 190,32 €, en vigueur depuis le 1er août 2026. Hausse officielle confirmée par la CRE : +2,5 % TTC en moyenne au 1er août 2026 (TURPE +3,04 % distribution, nouveau mécanisme de capacité, baisse partielle de l'accise). | [S8][S14] | élevée (existence et sens de la hausse, source CRE officielle) / moyenne (valeur exacte 0,2001 €/kWh, lue sur des comparateurs et non sur une page EDF/CRE ouverte avec succès cette session) | Base de calcul kWh pour `docs/COST_MODEL.md` §6 principe 4 (registre des coûts, kWh estimés). |
| 18 | RTX 4070 Ti Super : Total Graphics Power (TGP) officiel NVIDIA 285 W, alimentation système recommandée 700 W minimum. | [S9] | élevée | Base de calcul conso/heure pour un GPU seul : 285 W × heures d'usage × 0,2001 €/kWh. |
| 19 | Consommation d'un système à 4 GPU en pleine charge : aucune mesure publiée tierce trouvée cette session (budget de recherche épuisé). Inférence à partir du TGP officiel : 4 × 285 W = 1 140 W pour les seules cartes, plus 150-350 W typiques pour CPU/carte mère/RAM/stockage/pertes d'alimentation sur une station 4 GPU — soit un ordre de grandeur de 1 300-1 500 W en pleine charge simultanée des 4 cartes. | inférence à partir de [S9] | faible (inférence, pas une mesure publiée) | À remplacer par une mesure réelle (wattmètre) dès que la machine GPU est disponible ; ne pas utiliser cette estimation au-delà d'un ordre de grandeur initial dans `docs/COST_MODEL.md`. |
| 20 | RTX 4070 Ti Super absente des catalogues « neuf » constatés en septembre 2026 (LDLC ne référence plus que la gamme RTX 50 dans sa catégorie cartes graphiques), confirmant une fin de production/commercialisation neuve. Sur le marché de l'occasion (annonces individuelles, France), les prix observés vont d'environ 430 € à 950 € selon état/marque, la majorité des annonces se situant autour de 500-680 €. | [S28][S27] | moyenne (absence du neuf, source ouverte avec succès) / faible (fourchette occasion, page marketplace non ouverte avec succès — 403 — donnée lue uniquement dans un résumé de résultat de recherche) | Le studio devra budgéter la carte en occasion (~500-700 € par carte en valeur centrale) pour tout calcul d'amortissement, avec une marge d'incertitude large. |
| 21 | Claude Max : 5x affiché à 100 $/mois, 20x à 200 $/mois, taxes non incluses, aucune tarification EUR publiée officiellement par Anthropic au 28/09/2026. | [S10] | élevée | Le §0 MISSION doit choisir entre 5x/20x sur la base du prix USD, converti et incertain côté TVA — voir table des paramètres. |
| 22 | Taux de change EUR/USD (Banque centrale européenne, taux de référence quotidien) : 1 € = 1,1403 $ au 25/09/2026. | [S13] | élevée | Sert de base de conversion unique et datée pour tout montant $→€ de cette note, conformément à l'exigence de traçabilité. |
| 23 | L'API YouTube Data v3 est gratuite dans la limite du quota par défaut (100 `videos.insert`, 100 `search.list`, 10 000 unités/jour pour le reste) ; au-delà, une extension de quota peut être demandée, sans que la documentation officielle ne mentionne de coût monétaire à ce stade. | [S11] | élevée | Confirme MISSION §4 « API YouTube » : le coût direct de l'API est nul, la contrainte est le quota, pas le budget. |
| 24 | La documentation officielle TikTok Developers (Content Posting API) ne mentionne aucun tarif ni coût d'usage ; l'absence de section pricing suggère un accès gratuit sous conditions d'audit du client, sans confirmation explicite. | [S12] | moyenne (inférence d'absence, pas une confirmation positive) | Traiter comme gratuit par défaut dans `docs/COST_MODEL.md`, avec note NEEDS_HUMAN si un coût apparaissait lors de l'audit TikTok réel. |
| 25 | Non trouvé : aucune valeur monétaire officielle ou sourcée du temps humain cette session ; aucune source ne chiffre un coût d'opportunité pour les 15 min/vidéo de portes humaines du §11 MISSION. | — | — | Ne pas inventer de chiffre ; le coût d'opportunité du temps humain reste hors modèle tant qu'aucune source n'est trouvée (voir « Questions ouvertes »). |

## RPM YouTube long format — détail par pays et niche

| Segment | RPM (pour 1000 vues) | Période / méthode | Source | Confiance |
|---|---|---|---|---|
| France, généraliste | ~2,29 $ (fourchette réaliste 1,20-3,50 $) | Panel « 87 marchés », données août 2026 | [S15] | moyenne |
| États-Unis, généraliste | ~5,90 $ | Idem, comparaison directe France/US | [S15] | moyenne |
| Éducation/Science, panel large | médiane 10,22 $ | 300 chaînes, 3 595 mois-chaîne, mai 2025-mai 2026 | [S17] | moyenne |
| Éducation & Learning (sous-niches : langues, certifications) | 9-14 $ | Panel de niches 2026 | [S18] | moyenne |
| Éducation, étude spécialisée AIR | 14,97-18,23 $ | Étude AIR Media-Tech, juin 2026, citée par [S15] | [S15] | faible (donnée de seconde main, étude source non ouverte intégralement) |
| Science expliquée (format « vulgarisation légère ») | 5,32 $ | Panel niches 2026 | [S18] | moyenne |
| Fiction/récits (trahison, revanche) | 12,82 $ | Panel niches 2026 | [S18] | moyenne |
| Analyse littéraire / critique | 9,15 $ | Panel niches 2026 | [S18] | moyenne |
| Horreur / histoires effrayantes narrées | ~4-13 $ (exemple cité : chaîne « Mr Nightmare », 6 M abonnés) | Source non rouverte avec succès (404 lors de la vérification), donnée issue d'un résumé de recherche uniquement | — | faible |
| Ingénierie, géographie | aucune donnée dédiée trouvée | — | — | — (absence de donnée, ne pas extrapoler sans le signaler) |
| Shorts, généraliste | 0,01-0,07 $, jusqu'à 0,15-0,25 $ (niches fortes) | Multiples sources praticiennes 2026 | [S15][S17] | moyenne |
| Shorts, repère central utilisé par plusieurs praticiens | 0,07-0,20 $ | Étude AIR Media-Tech, juin 2026, citée par [S15] | [S15] | moyenne |

Note méthodologique : aucune de ces valeurs n'est une donnée officielle YouTube (YouTube ne publie pas de RPM). Toutes proviennent de panels tiers (vidIQ, TubeBuddy, AIR Media-Tech, comparateurs) ou de créateurs individuels ; elles varient avec la composition géographique de l'audience, la saison (Q4 plus élevé) et le format d'annonce activé.

## TikTok Creator Rewards — détail

| Critère | Valeur officielle | Source |
|---|---|---|
| Pays couverts (constatés) | États-Unis, Royaume-Uni, Allemagne, Japon, Corée du Sud, **France**, Mexique, Brésil | [S7], recoupé par [S24] |
| Type de compte | Personnel uniquement (Business exclu) | [S7] |
| Seuil compte | ≥ 10 000 abonnés authentiques ; ≥ 100 000 vues vidéo sur 30 jours | [S7] |
| Seuil vidéo | ≥ 1 minute ; ≥ 1 000 vues qualifiées (≥ 5 s de visionnage, pas de « pas intéressé ») ; contenu original, pas de Duet/Stitch/Photo Mode, pas de contenu sponsorisé | [S7] |
| Paiement minimum | 50 $ US ou équivalent, versement mensuel le 15 | [S7] |
| Exclusion IA totale | Non trouvée dans le texte officiel ; affirmée uniquement par des sources secondaires non sourcées officiellement, qui reconnaissent l'absence de seuil publié | [S26] (confiance faible) |
| RPM France observé | ~0,60-0,80 €/1000 vues qualifiées | [S25] (confiance faible, TikTok ne publie aucun chiffre) |

## Sponsoring / affiliation — détail

| Constat | Valeur | Source | Confiance |
|---|---|---|---|
| CPM sponsoring, niche Éducation (repère central 2026) | 20-40 $ | [S19] | moyenne |
| CPM sponsoring, niches adjacentes IA/productivité | 28-55 $ | [S19] | moyenne |
| CPM sponsoring vs AdSense, même niche Éducation | 2-4× le revenu AdSense pur (5-18 $ AdSense vs 20-40 $ sponsoring) | [S20] | moyenne |
| Délai avant premier revenu de sponsoring | non trouvé (aucune source consultée ne le quantifie) | — | — |
| Délai d'approbation de la demande de monétisation YouTube (validation administrative, pas croissance de chaîne) | ~30 jours en moyenne | [S29] | moyenne |

## Distribution des résultats — loi de puissance (détail)

Étude de référence : McGrady, Zheng, Curran, Baumgartner (dir. Ethan Zuckerman, UMass Amherst), « Dialing for Videos: A Random Sample of YouTube », *Journal of Quantitative Description: Digital Media*, décembre 2023 [S22]. Méthode : génération d'identifiants YouTube aléatoires à 11 caractères (« composition téléphonique » de l'espace d'adressage), donnant un échantillon représentatif de l'ensemble des vidéos publiées (pas seulement les vidéos recommandées ou populaires) — contrairement aux panels de chaînes utilisés pour les RPM ci-dessus.

| Indicateur | Valeur | Source | Confiance |
|---|---|---|---|
| Vidéos avec < 100 vues | 65,44 % | [S21][S23] | moyenne (lu via résumé secondaire) |
| Vidéos avec < 1 000 vues | 86,93 % | [S23] | moyenne |
| Vidéos avec ≥ 10 000 vues | 3,67 % | [S21][S23] | moyenne |
| Part des vues totales captée par ces ≥ 10 000 vues | 93,61 % | [S23] | moyenne |
| Vidéos avec 0 vue | ~4,68-4,88 % | [S21][S23] | moyenne |
| Médiane de vues par vidéo | 35 | [S21][S23] | moyenne |
| Moyenne de vues par vidéo | 5 868 | [S23] | moyenne |
| Total de vidéos estimé sur YouTube (fin 2022) | ~9,9 milliards | [S23] | moyenne |

Inférence : ces chiffres portent sur l'ensemble de YouTube (tous formats, tous niveaux de production, y compris le contenu quasi vide). Ils ne mesurent pas spécifiquement la distribution des vues *à l'intérieur* d'une niche éducative bien packagée ; la vraie référence pour ce studio serait la distribution des vues des chaînes comparables (§8 MISSION), non celle de l'ensemble de la plateforme. Confiance moyenne sur cette inférence.

## Coûts unitaires de production France — détail

| Poste | Valeur | Date / condition | Source | Confiance |
|---|---|---|---|---|
| Électricité, Tarif Bleu option Base, 6 kVA | 0,2001 €/kWh ; abonnement annuel 190,32 € | En vigueur depuis le 01/08/2026 | [S14], hausse confirmée par [S8] | moyenne (valeur exacte) / élevée (existence et sens de la hausse) |
| RTX 4070 Ti Super — TGP | 285 W | Fiche produit NVIDIA | [S9] | élevée |
| RTX 4070 Ti Super — alimentation système recommandée | 700 W | Fiche produit NVIDIA | [S9] | élevée |
| Système 4× RTX 4070 Ti Super en pleine charge | ~1 300-1 500 W (inférence, cartes seules 1 140 W) | Aucune mesure publiée trouvée | inférence à partir de [S9] | faible |
| RTX 4070 Ti Super, prix neuf | non disponible — carte retirée des catalogues neufs constatés | Sept. 2026 | [S28] | moyenne |
| RTX 4070 Ti Super, prix occasion France | ~430-950 €, majorité ~500-680 € | Annonces individuelles, sept. 2026 | [S27] (page non ouverte avec succès, donnée via résumé de recherche) | faible |
| Claude Max 5x | 100 $/mois hors taxe (≈ 87,70 € au taux du 25/09/2026, hors TVA éventuelle) | [S10][S13] | élevée (prix $) / moyenne (conversion €, TVA non confirmée) |
| Claude Max 20x | 200 $/mois hors taxe (≈ 175,40 € au taux du 25/09/2026, hors TVA éventuelle) | [S10][S13] | élevée (prix $) / moyenne (conversion €, TVA non confirmée) |
| Stockage HDD (€/To) | non trouvé cette session | budget de recherche épuisé | — | — |
| Stockage SSD (€/To) | non trouvé cette session | budget de recherche épuisé | — | — |
| API YouTube Data v3 | gratuite dans le quota (100 `videos.insert`/j, 100 `search.list`/j, 10 000 unités/j pour le reste) | [S11] | élevée |
| API TikTok (Content Posting) | aucun tarif mentionné dans la documentation officielle ; gratuit par défaut supposé, non confirmé positivement | [S12] | moyenne |

## Temps humain — repères non chiffrés

Aucune source datée trouvée cette session ne chiffre un coût d'opportunité du temps humain pour ce type de studio (les 15 min/vidéo de portes humaines du §11 MISSION). Conformément à MISSION principe 2 (« aucun chiffre inventé »), cette note n'invente pas de valeur horaire. Si un chiffrage est nécessaire pour `docs/COST_MODEL.md`, il doit venir d'une décision explicite de l'opérateur humain (entrée `docs/NEEDS_HUMAN.md`), pas d'une estimation de marché générique.

## Paramètres pour COST_MODEL.md

| Paramètre | Valeur basse | Valeur centrale | Valeur haute | Unité | Sources | Confiance |
|---|---|---|---|---|---|---|
| RPM long format, France (généraliste) | 1,20 | 2,29 | 3,50 | $ / 1000 vues | [S15] | moyenne |
| RPM long format, niche éducation/science, panel sans pays précisé (AIR, 300 chaînes) | 9,00 | 10,22 | 18,23 | $ / 1000 vues | [S17][S18] | moyenne |
| RPM long format, France, niche éducation/science | — | non sourcé | — | $ / 1000 vues | Inférence : entre le généraliste France (2,29 $) et le panel ci-dessus | faible |
| RPM long format, États-Unis (généraliste) | 3,00 | 5,90 | 11,00 | $ / 1000 vues | [S15][S17] | moyenne |
| RPM Shorts, généraliste, monde | 0,01 | 0,07 | 0,25 | $ / 1000 vues | [S15][S17] | moyenne |
| Part créateur, revenus pub long format YouTube | — | 55 | — | % net | [S1] | élevée |
| Part créateur, Creator Pool Shorts YouTube | — | 45 | — | % du pool alloué | [S1][S6] | élevée |
| RPM TikTok Creator Rewards, France | 0,60 | 0,70 | 0,80 | € / 1000 vues qualifiées | [S25] | faible |
| Seuil YPP full monetization (jusqu'au 31/01/2027) | — | 1000 abonnés + 4000 h/12 mois OU 10 M vues Shorts/90 j | — | seuil binaire | [S2] | élevée |
| Seuil YPP full monetization (à partir du 01/02/2027) | — | 1000 abonnés + 8000 h/365 j OU 20 M vues Shorts/90 j | — | seuil binaire | [S5][S16] | élevée |
| Seuil TikTok Creator Rewards | — | 10 000 abonnés + 100 000 vues/30 j | — | seuil binaire | [S7] | élevée |
| CPM sponsoring, niche éducation | 20 | 30 | 40 | $ / 1000 vues | [S19] | moyenne |
| Prix électricité France, option Base | — | 0,2001 | — | € / kWh | [S14][S8] | moyenne |
| TGP RTX 4070 Ti Super | — | 285 | — | W | [S9] | élevée |
| Consommation système 4× RTX 4070 Ti Super, pleine charge | 1140 | 1400 | 1500 | W | inférence [S9] | faible |
| RTX 4070 Ti Super, prix occasion France | 430 | 600 | 950 | € | [S27] | faible |
| Abonnement Claude Max 5x | 87,70 | 90 | 105,30 | € TTC estimé / mois | [S10][S13] | moyenne |
| Abonnement Claude Max 20x | 175,40 | 180 | 210,50 | € TTC estimé / mois | [S10][S13] | moyenne |
| Taux de change utilisé | — | 1 € = 1,1403 $ | — | taux, daté 2026-09-25 | [S13] | élevée |
| Part de vidéos YouTube < 1000 vues (référence loi de puissance, toute la plateforme) | — | 86,93 | — | % | [S23] | moyenne |
| Coût API YouTube / TikTok | — | 0 (dans le quota) | — | € | [S11][S12] | élevée / moyenne |
| Coût stockage €/To (HDD, SSD) | non déterminé — absent du modèle tant que non sourcé | | | € / To | — | — |

## Écarts avec MISSION §4

| Affirmation de la mission | Verdict (confirmé / infirmé / nuancé / non vérifiable) | Sources | Correction proposée |
|---|---|---|---|
| « Monétisation TikTok : Creator Rewards, contenu original de plus d'une minute ; contenu entièrement généré par IA exclu selon des sources secondaires (confiance moyenne). » | **confirmé** — le texte officiel des conditions EEA de TikTok [S7] confirme exactement le seuil « > 1 minute » et « contenu original » ; en revanche, aucun texte officiel trouvé ne mentionne une exclusion générale du contenu « entièrement IA » — l'estimation de MISSION (confiance moyenne, source secondaire) est donc la bonne façon de le formuler, rien à corriger sur le fond. À ajouter : le seuil d'entrée réel est nettement plus exigeant que celui d'YPP Fan Funding (10 000 abonnés + 100 000 vues/30 j vs 500 abonnés), un point absent de MISSION §4. | [S7][S26] | Ajouter dans MISSION §4 (ou dans une future révision) le seuil précis (10 000 abonnés, 100 000 vues/30 j, 1 000 vues qualifiées/vidéo) et le pays de disponibilité confirmé (France incluse). Continuer à traiter TikTok comme un canal de distribution plutôt qu'une source de revenu fiable, comme déjà prévu. |
| Repères RPM du skill `scenariste-youtube` (§12, non reproduits : dépôt public) | **nuancé** : ordres de grandeur France et États-Unis cohérents avec [S15] ; la fourchette Shorts des sources 2026 va de 0,01 à 0,25 $ selon la niche [S15][S17] ; la niche éducation/science est nettement au-dessus du généraliste sur un panel sans pays précisé [S17]. | [S15][S17] | Distinguer dans le skill un RPM « généraliste » et un RPM « niche forte », en précisant le pays. |
| « Mesure des vues : YouTube compte une vue dès le démarrage (tous formats) ; les revenus suivent les vues engagées. » | **confirmé** — vérifié sur la page officielle YouTube dédiée au changement du 24/08/2026 : le compteur public démarre dès la première image, mais la monétisation et l'éligibilité YPP restent basées sur les engaged views / watch hours qualifiées, sans impact annoncé sur les revenus. | [S3] | Aucune, l'affirmation de MISSION est exacte et à jour. |

## Questions ouvertes

- Coût du stockage (€/To, HDD et SSD, neuf) en France en septembre 2026 : budget de recherche de session épuisé avant d'avoir pu vérifier une source ouverte avec succès ; à revérifier en priorité dans une session de recherche ultérieure (aucune page marchande n'a pu être ouverte : LDLC, Amazon.fr ont renvoyé des erreurs 403/503/410 lors des tentatives).
- Délai moyen ou médian avant qu'une chaîne nouvellement lancée dans les niches histoire/science/éducation obtienne son premier revenu de sponsoring : aucune source praticienne consultée ne le chiffre.
- Probabilité statistique et délai moyen pour qu'une nouvelle chaîne atteigne l'éligibilité YPP (1 000 abonnés + 4 000 h, ou la version 2027) : aucune étude agrégée trouvée, seulement des anecdotes individuelles très dispersées.
- RPM spécifique aux niches « ingénierie » et « géographie » : aucune source dédiée trouvée ; à rapprocher provisoirement de la fourchette éducation/documentaire par analogie, en le signalant comme hypothèse non vérifiée dans `COST_MODEL.md`.
- Mesure publiée (wattmètre réel) de la consommation d'un système à 4 GPU RTX 4070 Ti Super en pleine charge : non trouvée ; la valeur de cette note est une inférence à partir du TGP officiel par carte, à remplacer dès que possible par une mesure sur la machine GPU réelle (`make gpu-smoke`).
- Confirmation d'une TVA française applicable (ou non) aux abonnements Claude Max facturés par Anthropic (société hors UE) : non trouvée sur `claude.com/pricing`, qui affiche des prix hors taxe sans préciser le régime applicable aux clients français.
- Table complète (13+ niches) de l'étude AIR Media-Tech RPM 2026 : la page n'a pu être ouverte que partiellement (contenu tronqué par l'outil de récupération) ; seules les figures déjà relayées par une source secondaire (Digitiz) ou par le résumé de recherche ont pu être vérifiées.

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | YouTube Help — YouTube partner earnings overview | https://support.google.com/youtube/answer/72902?hl=en | s.d. | 2026-09-28 | officiel | élevée |
| S2 | YouTube Help — YouTube Partner Program overview & eligibility | https://support.google.com/youtube/answer/72851?hl=en | s.d. | 2026-09-28 | officiel | élevée |
| S3 | YouTube Blog — What are "Engaged" Views on YouTube? | https://blog.youtube/inside-youtube/engaged-views-youtube-explained/ | 2026-08 | 2026-09-28 | officiel | élevée |
| S4 | YouTube Blog — Unlock a world of viewers with multi-language audio | https://blog.youtube/news-and-events/multi-language-audio/ | 2025-09-10 | 2026-09-28 | officiel | élevée |
| S5 | YouTube Blog — New opportunities to earn and changes to the YouTube Partner Program | https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/ | 2026-08-10 | 2026-09-28 | officiel | élevée |
| S6 | YouTube Help — YouTube Shorts monetization policies | https://support.google.com/youtube/answer/12504220?hl=en | s.d. | 2026-09-28 | officiel | élevée |
| S7 | TikTok — Creator Rewards Program Terms (EEA) | https://www.tiktok.com/legal/page/global/tiktok-creator-rewards-program-eea/en | s.d. | 2026-09-28 | officiel | élevée |
| S8 | CRE — La CRE propose une évolution du niveau moyen des TRVE de +2,5 % TTC au 1er août 2026 | https://www.cre.fr/actualites/toute-lactualite/la-cre-propose-une-evolution-du-niveau-moyen-des-tarifs-reglementes-de-vente-de-lelectricite-de-25-ttc-au-1er-aout-2026.html | 2026-07 | 2026-09-28 | officiel | élevée |
| S9 | NVIDIA — GeForce RTX 4070 Family Graphics Cards | https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4070-family/ | s.d. | 2026-09-28 | officiel | élevée |
| S10 | Anthropic — Plans & Pricing | https://claude.com/pricing | s.d. | 2026-09-28 | officiel | élevée |
| S11 | Google Developers — YouTube Data API v3, Getting Started | https://developers.google.com/youtube/v3/getting-started | s.d. | 2026-09-28 | officiel | élevée |
| S12 | TikTok for Developers — Content Posting API, Get Started | https://developers.tiktok.com/doc/content-posting-api-get-started/ | s.d. | 2026-09-28 | officiel | élevée |
| S13 | Banque centrale européenne — Euro reference exchange rate, USD | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html | 2026-09-25 | 2026-09-28 | officiel | élevée |
| S14 | Fournisseurs-électricité.com — Option Base EDF : prix du kWh et abonnement au tarif réglementé (2026) | https://www.fournisseurs-electricite.com/fournisseurs/edf/tarifs/base | 2026-09 | 2026-09-28 | données | moyenne |
| S15 | Digitiz — Rémunération YouTube 2026 : mes revenus avec 10 000 abonnés | https://digitiz.fr/monetisation-youtube/ | 2026-08-24 | 2026-09-28 | praticien | moyenne |
| S16 | AIR Media-Tech — YouTube Partner Program Requirements 2026: The Complete Guide | https://air.io/en/monetization/youtube-partner-program-requirements-2026-the-complete-guide | 2026-09-18 | 2026-09-28 | données | moyenne |
| S17 | AIR Media-Tech — Which YouTube Niche Makes the Most Money in 2026? Ranked by Real RPM and CPM | https://air.io/en/air-data-findings/which-youtube-niche-makes-the-most-money-in-2026-ranked-by-real-rpm-and-cpm | 2026-07 | 2026-09-28 | données | moyenne |
| S18 | OutlierKit — 19 Most Profitable YouTube Niches 2026 (Real RPM Data) | https://outlierkit.com/blog/most-profitable-youtube-niches | 2026-06 | 2026-09-28 | données | moyenne |
| S19 | OutlierKit — YouTube Sponsorship Rates 2026: What to Charge by Niche, Subs, and CPM | https://outlierkit.com/resources/youtube-sponsorship-rates/ | 2026-09-13 | 2026-09-28 | praticien | moyenne |
| S20 | Kingy.ai — The AI Niche and YouTube Sponsorship Rates | https://kingy.ai/news/the-ai-niche-and-youtube-sponsorship-rates-how-it-compares-to-finance-gaming-and-everything-in-between/ | 2026-08-22 | 2026-09-28 | praticien | moyenne |
| S21 | Ethan Zuckerman — How Big is YouTube? | https://ethanzuckerman.com/2023/12/22/how-big-is-youtube/ | 2023-12-22 | 2026-09-28 | publication | élevée |
| S22 | McGrady et al. — Dialing for Videos: A Random Sample of YouTube, Journal of Quantitative Description: Digital Media | https://journalqd.org/article/view/4066 | 2023-12-20 | 2026-09-28 | publication | élevée |
| S23 | Into the Minds — Research reveals YouTube's most secret stats | https://www.intotheminds.com/blog/en/research-youtube-stats/ | 2024-01-12 | 2026-09-28 | données | moyenne |
| S24 | Creators Agency — TikTok Creator Rewards Program: Requirements, RPM, Pay, and Disqualifications | https://creatorsagency.co/blog/tiktok-creator-rewards-program-2026 | 2026-07-28 | 2026-09-28 | praticien | moyenne |
| S25 | Linkdash — TikTok Creator Rewards Europe 2026: Realistic Earnings by Country | https://linkdash.eu/en/blog/tiktok-creator-rewards-europe-2026-realistic-earnings-by-country-uk-13 | 2026-05-17 | 2026-09-28 | données | moyenne |
| S26 | Storrito — What TikTok's AI Monetization Restrictions Signal for Creator Income | https://storrito.com/resources/what-tiktoks-ai-monetization-restrictions-signal-for-creator-income/ | s.d. | 2026-09-28 | praticien | faible |
| S27 | leboncoin — Rtx 4070 ti super d'occasion (accessoires informatique) | https://www.leboncoin.fr/ck/accessoires_informatique/rtx-4070-ti-super | s.d. | 2026-09-28 | données | faible |
| S28 | LDLC — Catalogue cartes graphiques internes | https://www.ldlc.com/informatique/pieces-informatique/carte-graphique-interne/c4684/ | s.d. | 2026-09-28 | données | moyenne |
| S29 | TubeBuddy — YouTube Monetization Requirements | https://www.tubebuddy.com/blog/youtube-monetization-requirements/ | 2026 | 2026-09-28 | praticien | moyenne |
