# Revue red team : Canapoil

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Rôle | Red team : investisseur sceptique, avocat en droit de la consommation, QA |
| Périmètre lu | `recherche/` (01, 02, 03, pages légales, données Google Trends), `strategie/` (04, `brand.json`), `finance/` (05, `modele_financier.py`, `data.json`), `marketing/` (7 fichiers), `site/` (code, contenus, fonctions serveur, flux, PDF), `shopify-kit/` (CSV, pages, Liquid, guides) |
| Tests exécutés | Vérificateur du site (`site/outils/verifier_site.js`) relancé : 348/348 ; tests des fonctions (`site/outils/tester_fonctions.js`) : 17/17 ; crawl Playwright indépendant (21 pages × 390 px et 1 440 px) ; 46 contrôles de parcours en 4 configurations (vente démo, précommande, liste d'attente, production simulée) ; 8 scénarios d'attaque et de régression sur les fonctions serveur avec Stripe et Brevo simulés |
| Vérifications web | 10 pages consultées directement le 12/10/2026 (liste au §9). Le quota de recherche web de la session était épuisé : aucune requête de moteur de recherche n'a pu être lancée, seules des pages sources déjà citées ou officielles ont été lues |
| Règle de gravité | **Critique** : bloque le lancement ou crée un risque juridique ou financier sérieux. **Majeur** : dégrade fortement les résultats. **Mineur** : le reste |
| Modifications | Aucune. Ce document est le seul fichier écrit |
| Suivi des corrections | §12, ajouté le 12/10/2026 après correction des fichiers : 5 critiques et 18 majeurs traités, 9 sous-points laissés « non corrigé » faute de décision ou de donnée du client |

---

## 0. Verdict

| Question | Réponse | Confiance |
|---|---|---|
| Le dossier est-il sérieux ? | Oui. Points solides : objectif « millions » traité comme horizon chiffré, lignes rouges commerciales respectées sur tout le site, conformité intégrée dès la conception, économie unitaire recalculée au centime dans 3 documents, site sans erreur console ni appel tiers | Élevée |
| Peut-on lancer demain avec ce dossier ? | **Non.** 5 problèmes critiques bloquent le lancement ou exposent le client : précommande annoncée avec des délais contradictoires et faux dans l'e-mail de confirmation (C1), calendrier de précommande intenable (C2), budget réel 10 fois supérieur à l'enveloppe (C3), identité légale et fabricants impossibles à renseigner en l'état (C4), deux fonctions serveur ouvertes à l'abus (C5) | Élevée |
| La phase 0 (contenu + liste d'attente) peut-elle démarrer ? | Oui, après C4 (identité légale publiée), la correction de `config.js` (M14) et la sécurisation de `/api/inscription` (C5). Coût : 45 € | Élevée |
| L'économie unitaire tient-elle ? | Sur le site, oui (12,57 à 18,62 € par commande, 05 §2.1). Sur TikTok Shop via affiliés, elle tient à peine (4,19 €) et repose sur un coût de livraison TikTok non vérifié (M9) et une TVA d'achat supposée récupérable (M13) | Moyenne |
| Le palier 1 (1 k€ net par mois) est-il crédible ? | Possible, peu probable. La red team l'estime à **5-12 % à 12 mois** (estimation, confiance faible), sous les 10-20 % de la finance et les 30-40 % de la stratégie : le plan exige 35 à 43 heures par semaine pour un budget-temps de 20-25 heures (M5), le lancement tombe au creux saisonnier (M7) et le prix est 56 à 67 % au-dessus des génériques Amazon (M8) | Faible |
| « Des millions d'euros de bénéfice par mois » | Hors de portée de ce projet. Le dossier le dit correctement (≤ 0,1 %, 04 §6.6 et 05 §6). La red team ajoute qu'aucun produit consommable, aucune valeur vie client modélisée et un CPA central (30 €) supérieur au CPA maximal (20,04 €) rendent le chemin au-delà du palier 2 non démontré (M17) | Moyenne |

**Décision recommandée** : GO pour la phase 0 seulement, après 4 corrections rapides (C4, C5, M14, M1). NO-GO pour les précommandes tant que C1, C2 et C3 ne sont pas levés par écrit.

### Synthèse par gravité

| Gravité | Nombre | Domaines principaux |
|---|---|---|
| Critique | 5 | Droit de la consommation (délais), trésorerie, identité légale et GPSR, sécurité des fonctions serveur |
| Majeur | 18 | Mesure, stock, temps du fondateur, saisonnalité, prix, TikTok Shop, consentement e-mail, assurance, propriété intellectuelle, cohérence entre documents, exécutabilité |
| Mineur | 16 | Code, données structurées, sources, rédaction des CGV |

---

## 1. Tableau des problèmes par gravité

Les références « fichier:ligne » renvoient à `dropshipping/`. Les corrections sont écrites pour être exécutées telles quelles.

### 1.1 Critiques

| ID | Domaine | Problème | Preuve | Correction précise |
|---|---|---|---|---|
| **C1** | Droit de la consommation, site | En phase « précommande », le client reçoit des informations de délai contradictoires et, dans l'e-mail de confirmation, fausses. La fiche affiche à la fois « Expédié sous 1 jour ouvré… livré en 3 à 6 jours ouvrés » et « Précommande : expédition à partir du 23 novembre ». Le panier et la page Commande n'affichent que « 3 à 6 jours ouvrés ». L'e-mail de confirmation (support durable, L221-13) dit toujours « Expédition depuis la France sous 1 jour ouvré, livraison… en 3 à 6 jours ouvrés », alors que la FAQ et les CGV art. 5.4 promettent que cet e-mail porte la date de précommande | `site/netlify/lib/coeur.js:318` (texte en dur, `metadata.phase` ignoré) ; `coeur.js:168` ; `site/outils/generer.py:418` et `:964` (bandeau et bénéfices statiques) ; test Playwright « précommande » ; test serveur n° 7 (§5.3) | 1) Ajouter `phase` et `precommande.{expedition, livraison_max}` dans `brand.json` → `livraison`, propagés par `generer.py` dans `data/products.json`, et supprimer ces réglages de `config.js`. 2) Dans `coeur.js`, lire la phase depuis `products.json` (jamais depuis le navigateur) et, si `precommande`, remplacer la phrase de la ligne 318 par « Précommande : expédition à partir du JJ/MM/AAAA, livraison au plus tard le JJ/MM/AAAA » ; ajouter ces dates dans `custom_text.submit` et dans `metadata`. 3) Dans `generer.py`, générer le bandeau, les bénéfices, la FAQ, la page Livraison, les CGV art. 7.1 et la page Commande selon la phase. 4) Ajouter au vérificateur un test qui échoue si « 1 jour ouvré » apparaît en phase précommande |
| **C2** | Opérations, droit de la consommation | Le calendrier de précommande ne tient pas. Le stock est commandé vers le 20/11 sur AliExpress, en pleine période 11.11 et Black Friday. Le plan suppose 12 jours de transit (confiance faible) pour promettre une livraison au plus tard le 14/12, alors que 03 §5.4 donne 10-20 jours pour AliExpress standard. Un transit de 20 jours fait manquer la date écrite pour toutes les précommandes et la date de Noël. `config.js` contient encore 23/11 et 04/12, impossibles | `marketing/lancement-30-jours.md:22` ; `site/assets/js/config.js:15-16` ; `recherche/03-legal-ops.md:651-653` ; `strategie/04-strategie.md:469` | Inverser la séquence : commander le micro-stock **à la porte 1** (15/11), avec la réserve de C3, puis ouvrir les précommandes. Date affichée = date de commande + 90e centile du transit mesuré sur les échantillons + 3 jours ouvrés (dédouanement, étiquetage) + 6 jours ouvrés de livraison, plafonnée à 30 jours. Si le résultat dépasse le 23/12, ne pas utiliser l'argument Noël. Prévoir dans l'e-mail de précommande l'option « annulation et remboursement intégral sous 14 jours » si le colis fournisseur n'est pas arrivé en France 10 jours avant la date limite. Préférer un vendeur expédiant depuis un entrepôt UE ou en livraison express pour ce lot |
| **C3** | Trésorerie | Le budget de 150 € est incompatible avec le plan, et le dossier donne trois chiffres différents au client. 04 et `brand.json` annoncent 219 € et un stock « financé par les précommandes ». La finance démontre 416 € à avancer avant le premier euro et un creux de 1 309 € (réaliste) à 3 088 € (optimiste), dû au règlement TikTok Shop à 31 jours. Sans réserve, une vidéo virale produit des ruptures et des annulations sanctionnées par TikTok | `strategie/04-strategie.md:27`, `:385` ; `strategie/brand.json:679-680` ; `finance/05-analyse-financiere.md:221-232`, `:234-240` ; règlement TikTok Shop vérifié (§3.2) | 1) Remplacer dans 04 §0, §5.3 et `brand.json` → `hypotheses_cles` les montants par ceux de 05 : 416 € avant le premier encaissement, 1 300-1 500 € de réserve. 2) Faire signer au client, avant S1, un choix écrit entre trois options : (a) apport en compte courant de 1 500 € ; (b) plafond strict des ventes TikTok Shop au stock payé, sans affiliés avant le premier règlement ; (c) arrêt à 45 € si la porte 1 n'est pas franchie. 3) Ajouter une ligne « réserve de trésorerie disponible » au tableau de bord hebdomadaire de 04 §6.7, avec alerte sous 300 € |
| **C4** | Mentions légales, GPSR | Le site ne peut pas être mis en ligne en S1, même en liste d'attente : 19 variables d'identité restent visibles (`{{RAISON_SOCIALE}}`, `{{SIREN}}`, `{{HEBERGEUR}}`…), alors que la LCEN s'applique à tout site professionnel, avec ou sans vente (1 an et 75 000 €, 375 000 € pour une personne morale, 03 §1.1). Les champs `{{FABRICANT_*}}` exigent le nom, l'adresse postale et l'e-mail du fabricant réel : un vendeur AliExpress grand public les fournit rarement, et l'importateur doit aussi vérifier la documentation technique (art. 11 GPSR). Sans eux, aucune fiche n'est publiable et TikTok Shop UE refuse les fiches sans informations GPSR | `site/README.md` §7 (tableau des 19 variables) ; crawl : 3 à 32 variables visibles par page ; `strategie/brand.json` → `produits[].gpsr.fabricant` ; 03 §2.2, §6.5 L1-L6 | 1) Remplir les 19 variables avant tout déploiement, régénérer (`generer.py` puis `rendre_images.js`) et ajouter au vérificateur un échec bloquant si `{{` apparaît dans une page publique. 2) Ajouter aux critères éliminatoires du choix fournisseur (04 §5.4, étape 1) : « fabricant identifié par écrit (raison sociale, adresse postale, e-mail), notice et avertissements fournis, photos de l'étiquette d'origine ». 3) Si aucun vendeur AliExpress ne remplit ce critère, passer par CJ Dropshipping ou un agent qui fournit ces documents (03 §5.1) |
| **C5** | Sécurité, droit | Les fonctions `/api/retractation` et `/api/inscription` acceptent toute requête sans en-tête `Origin` (curl, script), sans limite de débit, sans captcha et sans vérification que la commande existe. Un tiers peut faire envoyer, depuis le domaine authentifié de Canapoil, un e-mail au contenu libre (nom, prénom, commande, produits : 760 caractères) à n'importe quelle adresse. Test : objet « Accusé de réception de votre rétractation (commande VOTRE COMPTE EST BLOQUE) » avec une URL d'hameçonnage dans le corps. Conséquences : hameçonnage au nom de la marque, plaintes pour spam, suspension du compte Brevo, et épuisement du quota gratuit de 300 e-mails par jour, qui bloque les confirmations de commande et les accusés de rétractation imposés par la loi | `site/netlify/lib/coeur.js:105-110` (`if (!o) return true`), `:201-239`, `:242-261` ; test serveur n° 4 et n° 6 (§5.3) | 1) Exiger un en-tête `Origin` égal à `SITE_URL` pour `retractation` et `inscription` (garder l'exception pour `webhook`). 2) Ajouter Cloudflare Turnstile (gratuit) sur les deux formulaires et vérifier le jeton côté serveur. 3) Limiter à 3 requêtes par adresse IP et par heure (règle de limitation de débit Cloudflare, offre gratuite). 4) Rétractation : vérifier que le numéro de commande correspond à une session Stripe payée dont l'e-mail est identique (`GET /v1/checkout/sessions` filtré) ; sinon, envoyer l'accusé uniquement au service client avec mention « commande non retrouvée » et répondre au client par un message neutre. 5) N'insérer dans l'e-mail que des champs filtrés (lettres, chiffres, tirets ; aucune URL) |

### 1.2 Majeurs

| ID | Domaine | Problème | Preuve | Correction précise |
|---|---|---|---|---|
| **M1** | Mesure | Les portes de décision ne sont pas mesurables. 1) La CSP `script-src 'self'` bloque Cloudflare Web Analytics, seule mesure d'audience prévue : la documentation Cloudflare exige `https://static.cloudflareinsights.com` dans `script-src`. 2) Les UTM ne sont pas transmis à Stripe (aucun code dans `app.js` ni `coeur.js`), alors que le plan marketing attribue chaque commande à un script (`utm_content`). 3) Le formulaire de liste d'attente n'a pas le champ « produit qui m'intéresse », et le tapis de fouille n'a aucune page : les inscriptions du duel de la porte 1 ne sont pas attribuables | `site/_headers:10` ; [doc Cloudflare](https://developers.cloudflare.com/web-analytics/faq/) ; `marketing/07-plan-organique-90j.md:61-65` (demandes 3 et 7 non réalisées) | 1) `_headers` : ajouter `https://static.cloudflareinsights.com` à `script-src` et `https://cloudflareinsights.com` à `connect-src`, puis vérifier dans le tableau de bord Cloudflare qu'une visite remonte. 2) `app.js` : lire `utm_*` à l'arrivée, les garder en `sessionStorage` et les envoyer dans `create-checkout` ; `coeur.js` : les copier dans `metadata`. 3) Créer une page `/liste-attente/tapis-de-fouille/` et ajouter au formulaire un champ caché `produit` transmis à Brevo comme attribut |
| **M2** | Sécurité, droit | Le serveur ne connaît ni la phase de vente ni le stock. N'importe qui peut créer une session Stripe payable pendant la liste d'attente (avant médiateur, adhésion Léko et stock) ou après épuisement du stock ; le navigateur choisit lui-même la phase envoyée | `coeur.js:118-137` (`phase` lue dans le corps de la requête) ; test serveur n° 1 | Dans `coeur.js`, refuser `checkout` (503) si `products.json` → `livraison.phase` vaut `liste_attente` ; ajouter un champ `stock_disponible` par produit dans `brand.json` (mis à jour à chaque réassort) et refuser une ligne dont la quantité dépasse ce stock ; ne pas saisir `STRIPE_SECRET_KEY` dans l'hébergeur avant la porte 1 |
| **M3** | Stock, opérations | Aucune gestion de stock réelle : le site, TikTok Shop et les échantillons créateurs puisent dans 20 rouleaux, et le site continue d'afficher « expédié sous 1 jour ouvré » quand le stock est vide. Dans le kit Shopify, les 4 kits ont `Inventory tracker` vide : ils se vendent sans limite pendant que les composants sont suivis | `site/README.md` §8 (« Pas de gestion de stock en ligne ») ; `shopify-kit/products.csv` (kits : tracker vide, quantité vide) | Site : stock par produit dans `brand.json` (M2) et passage automatique en « précommande, expédition le JJ/MM » sous 5 unités. TikTok Shop : saisir le stock réel moins 2 unités de sécurité. Shopify : installer Shopify Bundles le jour de l'import pour lier le stock des kits aux composants, ou mettre `Inventory tracker` = `shopify` avec la quantité calculée sur le composant le plus rare |
| **M4** | Stock, finance | Le dimensionnement du micro-stock contredit l'offre de lancement. La prime « gant offert aux 30 premières précommandes » demande 30 gants, plus ceux du Kit anti-poils et du Grand kit, pour 10 gants en stock. Le Grand kit mis en avant est limité à 6 unités (6 raclettes). L'objectif de 30 précommandes consomme ≈ 35 rouleaux (Duo compris) pour 20 en stock, avant les 5 échantillons créateurs. Le coût de la prime (30 × 1,40 € + poids) est absent du modèle financier | `strategie/brand.json:555`, `:672-678` ; `finance/modele_financier.py` (aucune occurrence de la prime) ; `marketing/07-plan-organique-90j.md:206` | Recalculer le lot à partir de l'objectif : pour 30 précommandes au mix du site (35 % rouleau, 20 % Kit anti-poils, 30 % Grand kit, 15 % Duo) + 30 gants offerts + 5 échantillons : ≈ 40 rouleaux, ≈ 45 gants, ≈ 12 raclettes. Limiter la prime aux 30 premières commandes **dans la limite du stock de gants commandé**, afficher un compteur réel ou réduire la prime à 10. Ajouter la ligne « prime de lancement » au modèle financier (≈ 50 € TTC) |
| **M5** | Organisation | Le plan exige ≈ 35-43 heures par semaine (estimation, confiance moyenne, calculée avec les durées unitaires du plan) : tournage 6 h, montage 21 × 25-35 min = 9-12 h, recyclage 5 h, LIVE 3 h, réponses aux commentaires dans l'heure ≈ 3,5 h, créateurs 2-3 h, 10 articles SEO ≈ 3,5 h, colisage et SAV 3-4 h, administration 1 h. Le budget retenu est de 20-25 h. Le taux horaire de la finance (4,77 € réaliste) tombe vers 2,5-3 € à ce volume | `marketing/07-plan-organique-90j.md:20`, `:153`, `:182`, `:223` ; `finance/05-analyse-financiere.md:179` | Réduire le plan à 25 h : 2 vidéos par jour au lieu de 3, LIVE à partir de S12 seulement, articles SEO ramenés à 4 avant février, recyclage limité à Reels et Pinterest. Ou faire décider par le client un budget de 35-40 h. Recalculer `HEURES_FONDATEUR` dans le modèle financier avec la valeur retenue |
| **M6** | Stratégie, cohérence | Les probabilités et les portes de décision divergent entre documents et la porte 1 mesure l'attention ; l'intention d'achat reste à prouver. Palier 1 à 12 mois : 30-40 % (04) contre 10-20 % (05). Une seule vidéo à 50 000 vues ouvre la porte ; avec 1-3 % de chances par vidéo (02 §4.4) et ≈ 42 vidéos de duel, la probabilité d'en obtenir une dépasse 50 % sans preuve d'achat. Le second filtre (≥ 10 précommandes, ≈ 300 €) peut être franchi par l'entourage | `strategie/04-strategie.md:454`, `:468` ; `finance/05-analyse-financiere.md:310`, `:321` ; `recherche/02-acquisition.md:494` | Aligner 04 et `brand.json` sur la lecture finance (10-20 %). Porte 1 : exiger en plus ≥ 1,5 % de clics produit sur les vidéos de démonstration. Porte « stock » : ≥ 20 précommandes payées par des acheteurs hors entourage (vérifié sur les adresses) et un taux de conversion liste → précommande ≥ 8 % |
| **M7** | Marché, calendrier | Le lancement tombe au creux saisonnier : l'intérêt pour « anti poils » descend à 0,54-0,59 de sa moyenne en décembre (calcul marketing ; CSV : creux en décembre à 0,59) ; les requêtes « rouleau anti poils », « rouleau poils », « brosse anti poils » et « chomchom » ont un volume « trop faible » pour Google Trends. Le challenger (tapis de fouille) culmine en novembre (indice 1,30). Le duel ne peut pas changer de héros : la décision tombe le 15/11, les précommandes ouvrent le 16/11, et `brand.json` ne contient aucune donnée sur le tapis de fouille (prix, coût, GPSR, page, kits) | `recherche/donnees/google-trends-fr-2026-10-12.csv` ; `marketing/07-plan-organique-90j.md:22`, `:27` ; `strategie/04-strategie.md:98` | Préparer dès S2 une fiche complète du tapis de fouille dans `brand.json` (prix, coût sur échantillon, GPSR, avertissement d'ingestion) et une page générée, pour que le duel soit réellement ouvert. Si le rouleau gagne, décaler l'achat du stock principal à fin janvier (hausse de février) et garder novembre-décembre pour la liste d'attente et le Kit chat d'hiver |
| **M8** | Prix, concurrence | Le prix du héros est fragile : rouleau livré 28,80 € sur le site contre 14,95-15,99 € pour les génériques Amazon livrés en 1-3 jours, 7,19 € chez Zoomalia et 2,99 € pour le Trixie (01 §3 bis). Les prix concurrents sur TikTok Shop, canal de 80 % des commandes prévues, n'ont pas été relevés. La conversion clic → commande de 3,5 % sur TikTok Shop vient d'un agrégateur non sourcé | `strategie/04-strategie.md:51`, `:178-188` ; `recherche/01-marche-niches.md:394` ; `recherche/02-acquisition.md:295` | Avant la porte 1 : relever dans l'application TikTok (onglet Boutique, sans compte vendeur) les 20 premiers rouleaux réutilisables, avec prix, nombre de ventes affiché et délai. Si la médiane est sous 16 €, tester le rouleau à 19,90 € et faire du Grand kit l'offre unique mise en avant ; recalculer les marges dans `brand.json` |
| **M9** | TikTok Shop, logistique | 1) La politique TikTok Shop France impose, en expédition par le vendeur, une livraison sous 4 jours ouvrés ; le dossier annonce 3 à 6 jours ouvrés en point relais : le taux de livraison à l'heure risque de passer sous 90 %, avec frais hebdomadaires et plafond de commandes. 2) En expédition par TikTok (mode par défaut en France), le prix de l'étiquette est fixé par TikTok et n'a pas été relevé, alors que le modèle applique 4,50 € HT à 80 % des commandes | [Politique d'expédition TikTok Shop France](https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897), lue le 12/10/2026 ; `finance/modele_financier.py:93` | À l'ouverture du Seller Center, relever le tarif d'étiquette « Expédition par TikTok » pour 300 g, 500 g et 1 kg et le saisir dans le modèle (ligne `PORT_500` séparée pour TikTok). Utiliser l'expédition par TikTok, ou un transporteur agréé à J+2 (Colissimo point retrait) si l'expédition par le vendeur est choisie. Ne jamais utiliser Mondial Relay pour TikTok Shop sans avoir mesuré un 90e centile ≤ 4 jours ouvrés |
| **M10** | E-mail, RGPD | Le consentement recueilli ne couvre pas les envois prévus. Le formulaire du site promet « un e-mail le jour de l'ouverture des ventes ». Le plan e-mail envoie BV1, BV2, BV3, deux campagnes, puis « tests et nouveautés ». Les cases de consentement de `emails.md` §1.2 (liste d'attente, relance de panier, opposition client) ne sont pas codées. Les relances de panier PA1-PA3 n'ont aucun support technique sur le site | Gabarit `#tpl-attente` dans les fiches produit ; `marketing/emails.md:44-63` ; `site/README.md` §8 (« Pas de relance des paniers abandonnés ») | Remplacer le texte du formulaire par celui de `emails.md` §1.2 (case non pré-cochée, obligatoire) et l'enregistrer comme attribut Brevo avec la date. Jusqu'à ce développement, n'envoyer à la liste que BV0 et l'e-mail d'ouverture. Supprimer PA1-PA3 du plan tant que la case de consentement du panier et le webhook `checkout.session.expired` n'existent pas |
| **M11** | Assurance, responsabilité | En important le micro-stock, le client devient importateur, donc assimilé au producteur pour la responsabilité du fait des produits (1245-5 C. civ.). 03 classe l'assurance RC produits en P0 « avant tout stock » ; 04 la repousse au palier 1 ; le modèle financier ne la compte qu'à partir du 4e mois (février 2027), soit 3 mois de ventes sans couverture sur des produits utilisés près d'enfants et d'animaux (ingestion, chaleur) | `recherche/03-legal-ops.md:820` ; `strategie/04-strategie.md:589` ; `finance/modele_financier.py:592-593` | Demander 3 devis RC professionnelle + RC produits en S1, souscrire avant la commande du micro-stock, et déplacer la ligne `RC` du modèle au mois 2 (novembre 2026). Coût : 150-500 € par an (03 §0.5, estimation, confiance faible), à ajouter à C3 |
| **M12** | Propriété intellectuelle | Le héros est un modèle de type ChomChom, largement copié ; les vérifications DesignView et data.inpi.fr ne sont pas faites. La recherche sur le nom « Canapoil » s'est limitée au web et au RDAP : aucune recherche INPI ni TMview. Le dépôt de marque est reporté à la porte 2, alors que l'exposition commence avec la première vidéo diffusée | `strategie/04-strategie.md:96`, `:158`, `:168` ; 03 §6.6 S2 (P0) | En S1, avant la commande des échantillons : recherche DesignView (classe Locarno 04-02 brosses et 08-05 outils), TMview et data.inpi.fr pour « rouleau anti-poils » et « Canapoil », capture d'écran datée dans le dossier produit. Déposer « Canapoil » en classe 21 à la porte 1 (190 €, [barème INPI](https://www.inpi.fr/inpi-block/download-document?id=20516)), les classes 20 et 28 à la porte 2 |
| **M13** | Coût d'achat, fiscalité | Trois hypothèses d'achat sont optimistes. 1) La TVA facturée par AliExpress (IOSS de la plateforme) est supposée récupérable dans le modèle de base, alors que 03 §3.3 signale une double TVA probable (jusqu'à 20 % du coût d'achat). 2) Droit de 3 € par catégorie et redevance de 2 € par article distinct : réparti sur 20 rouleaux cela fait 0,25 €, mais un colis de 10 gants coûte 0,50 € par gant, un colis de 6 raclettes 0,83 € par raclette (contre 0,10 € et 0,15 € dans `brand.json`). 3) Le statut du droit forfaitaire de 3 € pour un achat B2B destiné à la revente n'est pas tranché ; un dédouanement de droit commun ajoute des frais de dossier du transporteur | `strategie/brand.json` (`droits_douane_estimes`) ; `finance/05-analyse-financiere.md:109` ; [Revenue.ie](https://www.revenue.ie/en/corporate/press-office/press-releases/2026/pr-092926-handling-fee.aspx) | Acheter le micro-stock via un compte AliExpress Business avec numéro de TVA, ou via CJ / un agent qui émet une facture B2B HT. Regrouper les 4 références chez un seul vendeur ou un agent (un seul colis). Faire valider par l'expert-comptable, avant la porte 1, le traitement TVA et douane de ce lot. Passer la variante « coût produit + 20 % » en hypothèse de base tant que ce point n'est pas validé |
| **M14** | Configuration du site | `config.js` est livré avec `phase: "vente"` et `mode: "demo"`, alors que la stratégie impose la liste d'attente avant la porte 1. Déployé tel quel, le site vend (ou simule des ventes) avant la porte 1, avec des dates de précommande impossibles | `site/assets/js/config.js:8`, `:12`, `:15-16` | Valeurs par défaut : `phase: "liste_attente"`, dates de précommande vides ; faire échouer `generer.py` si `phase` vaut `vente` ou `precommande` sans dates renseignées ; afficher en haut de toutes les pages un bandeau « site de démonstration » quand `mode` vaut `demo` |
| **M15** | Cohérence documentaire | Le client reçoit des consignes contradictoires : date limite de Noël 17/12 (`brand.json`) contre 14/12 (marketing) ; délai « 3 à 6 jours ouvrés à compter de la commande » (CGV art. 7.1, page Livraison) contre « 1 jour de préparation + 6 jours » (marketing) ; régime de TVA assujetti (`brand.json`, `config.js`) contre franchise recommandée (04 §8, 05 §8.1) ; assurance RC au palier 1 (04) contre P0 (03) ; délai de réponse 24 h, 48 h ou 5 jours ouvrés selon les pages | `strategie/brand.json:557` ; `marketing/lancement-30-jours.md:25` ; `site/outils/contenus/cgv.md` art. 7.1, 10.2, 12 | Désigner `brand.json` comme seule source et y ajouter : `noel_2026.date_limite_commande` = 15/12 (calcul : 15/12 + 6 jours ouvrés = 23/12), `regime_tva` décidé avec l'expert-comptable, `delai_reponse_sav` = 48 h ouvrées. Corriger 04, marketing et CGV pour citer ces champs |
| **M16** | Exécutabilité | Un débutant ne peut pas exécuter le dossier dès demain. Les ≈ 100 000 mots se répartissent sur 15 documents qui se contredisent (M15). Il manque les modèles physiques obligatoires (étiquette « Importé par », notice en français par produit, insert), les tableurs promis (commandes, stock, délais, registre des réclamations GPSR, registre RGPD, suivi créateurs) et une procédure Mondial Relay. Le déploiement demande Python, Node, Wrangler, la configuration DNS (SPF, DKIM, DMARC) et des webhooks Stripe | `site/README.md` §2, §4, §5 ; `strategie/04-strategie.md:352` (« Modifier un fichier JSON et redéployer ») | Livrer un fichier `docs/demarrage-J1-J14.md` d'une page par jour (action, durée, coût, lien), un classeur `docs/pilotage.xlsx` (onglets Commandes, Stock, Délais, Réclamations GPSR, Registre RGPD, Créateurs, KPI) et les gabarits imprimables d'étiquette et de notice. Envisager Shopify pour la phase de précommande : l'offre à 1 $ par mois pendant 3 mois (04 §5.1) couvre novembre à février pour ≈ 3 €, avec stock, e-mails de commande et précommandes natifs |
| **M17** | Stratégie long terme | Les paliers 3 et 4 sont calculés par ratios descendants, sans base produit. Le catalogue ne contient aucun consommable (04 §2.3), la valeur vie client n'est pas modélisée (05 §10), et le CPA central de 02 (30 €) dépasse le CPA maximal du meilleur cas (20,04 €). La croissance au-delà du palier 2 suppose donc une autre activité (plusieurs gammes ou marques) qui n'est pas décrite | `finance/05-analyse-financiere.md:298`, `:131` ; `marketing/bascule-payant.md` §2.4 | Présenter les paliers 3 et 4 comme des repères d'échelle, sans probabilité chiffrée. Ajouter au palier 2 un critère d'entrée « un produit à réachat (consommable ou accessoire d'usure) avec ≥ 15 % de réachat à 180 jours mesuré » avant toute dépense publicitaire supérieure à 1 000 € par mois |
| **M18** | Risque de pic | Le plan marketing classe « vidéo virale sans stock » en probabilité faible, alors que l'objectif même du plan est la viralité : 02 §4.4 estime à ≈ 420 commandes TikTok Shop l'effet d'une vidéo à 1 M de vues, pour 20 rouleaux en stock et un réassort de ≈ 15 jours depuis la Chine | `marketing/07-plan-organique-90j.md:317` ; `recherche/02-acquisition.md:513` | Requalifier le risque en « moyenne » ; écrire la procédure : stock TikTok Shop à jour 2 fois par jour, passage du site en précommande avec date réelle dès 5 unités, réassort express déclenché à 10 unités, aucun lien produit dans une vidéo qui dépasse 20 000 vues en 6 heures sans stock pour 7 jours |

### 1.3 Mineurs

| ID | Domaine | Problème | Preuve | Correction précise |
|---|---|---|---|---|
| m1 | Site | Faute affichée « 2 rouleaus » sur la fiche du héros (pluriel fabriqué en ajoutant « s ») | `site/outils/generer.py:680` | Ajouter `nom_court_pluriel` dans `brand.json` et l'utiliser quand `quantite > 1` |
| m2 | Serveur | Le webhook n'est pas idempotent : un événement rejoué par Stripe renvoie un second e-mail de confirmation (test n° 8) | `coeur.js:290-331` | Mémoriser l'identifiant d'événement dans Cloudflare KV (offre gratuite) et ignorer les doublons |
| m3 | Serveur | L'e-mail recalcule les lignes avec les prix du catalogue au moment du webhook, et le PDF des CGV est joint par URL (dernière version) au lieu de la version acceptée | `coeur.js:302-306`, `:329` | Lire les lignes via `GET /v1/checkout/sessions/{id}/line_items` ; publier les CGV sous `documents/cgv-AAAA-MM-JJ.pdf` et joindre la version notée dans `metadata.cgv_version` |
| m4 | Site | `merci.html` n'affiche pas le numéro de commande après un vrai paiement, alors que le formulaire de rétractation le demande | `assets/js/app.js` (`initMerci`) | Afficher les 10 derniers caractères de `session_id` en majuscules, identiques à l'e-mail |
| m5 | SEO, Merchant | JSON-LD et flux Google indiquent `InStock` quelle que soit la phase ; aucune `availability_date` en précommande | Crawl (JSON-LD de la fiche rouleau) ; `site/flux/google-merchant.xml` | Générer `PreOrder` / `preorder` avec date en précommande et `OutOfStock` en liste d'attente |
| m6 | Conversion | Le bandeau cookies s'affiche alors qu'aucun traceur n'est actif ; il couvre ≈ 35 % de l'écran à 390 px (capture) et masque le prix | `app.js` (`initCookies`) | Ne pas afficher le bandeau quand `traceurs.mesure` et `traceurs.publicite` sont vides ; garder le lien « Gérer mes cookies » |
| m7 | Mentions | Pendant la liste d'attente, le pied de page affiche « Médiateur de la consommation : `{{MEDIATEUR}}` » ; l'adhésion n'intervient qu'à la porte 1 | `generer.py` (pied de page) | Masquer la ligne tant que `contact.mediateur` est vide, ou adhérer à CM2C dès S1 (48 € pour 3 ans, [tarif vérifié](https://www.cm2c.net/tarifs.php)) |
| m8 | Sources | Le tarif Mondial Relay de 4,15 € TTC vient d'une source secondaire qui se contredit (« jusqu'à 250 g » en introduction, « jusqu'à 0,5 kg » dans le tableau). L'accès d'une société au tarif grand public et la desserte de la Corse (CGV art. 1.2) ne sont pas vérifiés | [Margeo](https://margeoapp.com/blog/tarifs-mondial-relay-2026) ; `cgv.md` art. 1.2 | Relever la grille sur mondialrelay.fr et la page de l'offre professionnelle, puis corriger `brand.json` → `port_ht` et les CGV |
| m9 | Sources | 03 cite le communiqué du ministère (S1) pour la redevance de 2 € ; ce communiqué ne donne aucun montant (« modalités précises… définies dans les prochains mois ») | `recherche/03-legal-ops.md:40`, `:482` | Citer [Revenue.ie](https://www.revenue.ie/en/corporate/press-office/press-releases/2026/pr-092926-handling-fee.aspx) seul pour le montant |
| m10 | CGV | Délais de réponse incohérents : 48 h ouvrées (art. 12), 5 jours ouvrés (art. 10.2), 24 h (mentions, contact, FAQ) | `site/outils/contenus/cgv.md` | Aligner sur la valeur de M15 |
| m11 | Information précontractuelle | Le modèle d'information du décret n° 2026-3 contient une phrase commençant par « Vous pouvez également exercer votre droit de rétractation en ligne sur » ; elle est absente de la page Retours et des CGV (point à vérifier sur le texte du décret) | [La Cité des entreprises](https://www.lacitedesentreprises.com/droit-des-affaires/obligation-daffichage-du-bouton-de-retractation-en-ligne-les-precisions-apportees-par-le-decret-n-2026-3-du-5-janvier-2026/) ; `outils/contenus/retours-retractation.md` | Lire le décret sur Légifrance et reprendre la phrase à l'identique avec l'URL `https://canapoil.fr/retractation/` dans la page Retours et l'article 8.3 |
| m12 | Accessibilité légale | La fonctionnalité de rétractation ne marche qu'avec JavaScript (formulaire sans `action`) | `retractation/index.html` | Ajouter `action="/api/retractation" method="post"` et accepter `application/x-www-form-urlencoded` côté serveur |
| m13 | Produit | Le tapis de fenêtre (textile ≥ 80 %) exige une étiquette de composition en français (règl. (UE) 1007/2011, 03 M2) ; son rattachement à une filière REP textile ou ameublement n'est pas analysé | `strategie/brand.json` (tapis) | Ajouter la composition à `caracteristiques` et poser la question REP à Léko avant l'achat |
| m14 | Juridique | L'objet social et le code d'activité de la société existante doivent couvrir la vente en ligne de marchandises (contrôles KYC de Stripe et TikTok Shop) | Absent du dossier | Vérifier le Kbis en S1 ; modifier l'objet social si besoin (coût à demander à l'expert-comptable) |
| m15 | Shopify | `products.csv` importe les produits en `Active` et publiés, avec les variables `{{…}}` dans les descriptions | `shopify-kit/products.csv` | Passer `Status` à `Draft` et `Published on online store` à `FALSE` |
| m16 | Finance | La répartition TikTok Shop 70 % rouleau / 30 % kit a été choisie pour retrouver la marge de 7,55 € de `brand.json` : l'hypothèse est calibrée sur le résultat attendu | `finance/modele_financier.py` (`TTS_ROU`) | La remplacer après 30 commandes TikTok Shop par la répartition observée |

---

## 2. Cohérence chiffrée entre documents

### 2.1 Ce qui est cohérent (contrôlé par script)

| Donnée | `brand.json` | `data/products.json` | `products.csv` | Modèle financier | Marketing |
|---|---|---|---|---|---|
| Prix des 4 produits et 4 kits | 24,90 / 9,90 / 12,90 / 24,90 ; 29,90 / 39,90 / 39,90 / 44,90 | Identiques | Identiques | Identiques (arrêt du script si écart) | Identiques |
| Port client et seuil | 3,90 € ; 35 € | Identiques | — | Identiques | Identiques |
| Coût de revient rouleau | 4,50 + 0,25 € | — (non publié) | 4,75 € | 4,50 + 0,25 € | — |
| Marges site (rouleau, Grand kit) | 12,57 € ; 17,74 € | — | — | 12,57 € ; 17,74 € | 12,57 € ; 17,74 € |
| ROAS de rentabilité TTC (Grand kit micro-stock / importé) | — | — | — | 2,25 / 1,99 | 2,25 / 1,99 |
| CPA maximal et cible (Grand kit importé) | — | — | — | 20,04 € / 16,70 € | 20,04 € / 16,70 € |

Le recalcul indépendant de la red team confirme : rouleau sur le site 28,80 € TTC → 24,00 € HT − 4,75 − 4,80 − 0,68 − 1,20 = 12,57 € ; ROAS TTC du Grand kit = 39,90 ÷ 17,74 = 2,25.

### 2.2 Ce qui diverge

| Sujet | Document A | Document B | Écart | Valeur à retenir |
|---|---|---|---|---|
| Cash avant le premier encaissement | 04 : 219 € + stock « financé par les précommandes » | 05 : 416 € | × 1,9 | 05 (C3) |
| Besoin de trésorerie | 04 : non chiffré | 05 : 1 309 € (réaliste), 3 088 € (optimiste) | — | 05 (C3) |
| Commandes pour le palier 1 | 04 : 155 par mois | 05 : 168 par mois | +8 % | 05 |
| Probabilité du palier 1 à 12 mois | 04 : 30-40 % | 05 : 10-20 % | × 2 à 3 | Red team : 5-12 % (§8) |
| Porte 2 (≥ 3 commandes par jour) | 04 : mi-décembre 2026 | 05 : mars-avril 2027 | 3 mois | 05 |
| Date limite de Noël | `brand.json` : 17/12 | Marketing : 14/12 | 3 jours | 15/12 (M15) |
| Délai total annoncé | CGV : 3-6 jours ouvrés depuis la commande | Marketing : 1 + 6 jours ouvrés | 1 jour | CGV (texte contractuel) |
| Dates de précommande | `config.js` : 23/11 → 04/12 | Marketing : 04/12 → 14/12 | 11 jours | Recalcul de C2 |
| Régime de TVA | `brand.json`, `config.js` : assujetti | 04 §8 et 05 §8.1 : franchise recommandée | +1,54 € par commande | Décision de l'expert-comptable, inscrite dans `brand.json` |
| Gants nécessaires au lancement | Prime : 30 + kits | Micro-stock : 10 | −35 environ | M4 |
| Assurance RC produits | 03 : P0 avant tout stock | 04 : palier 1 ; 05 : à partir de février 2027 | 3 mois sans couverture | 03 (M11) |
| Droits et redevance par unité | `brand.json` : gant 0,10 €, raclette 0,15 € | Calcul par colis : 0,50 € et 0,83 € | × 5 | M13 |

---

## 3. Hypothèses irréalistes et vérification des chiffres structurants

### 3.1 Hypothèses jugées irréalistes ou fragiles

| Hypothèse | Valeur du dossier | Pourquoi elle est fragile | Effet si elle est fausse |
|---|---|---|---|
| Conversion vues → clic produit TikTok Shop | 1,2 % (02 §2.3) | « Pas de benchmark public fiable » selon 02 lui-même ; estimation de confiance faible | Le volume TikTok Shop, qui porte 80 % des commandes, varie d'un facteur 5 entre les bornes basse et haute (0,5-2,5 %) |
| Conversion clic → commande TikTok Shop | 3,5 % (02 §2.2) | Agrégateur non sourcé (4,7 %) et estimation d'agence (5-12 %) ; prix 56-67 % au-dessus des génériques (M8) | À 2 %, le palier 1 recule de plusieurs mois |
| Vues médianes d'un compte neuf | 2 000 à J+60 (02 §4.4) | Portée des comptes de marque −23 % sur un an (02 §1.2) ; saison basse (M7) | Volume organique −20 % = −279 € par mois au palier 1 (05 §7.1) |
| Transit Chine → France du lot de stock | 12 jours (marketing) | 10-20 jours en standard (03 §5.4), pic 11.11 et Black Friday | Précommandes livrées en retard (C2) |
| Temps du fondateur | 20-25 h par semaine | Le plan détaillé en demande 35-43 (M5) | Cadence réduite ou épuisement ; taux horaire divisé par ≈ 1,7 |
| Statut « débutant » TikTok Shop | 3 mois (05, confiance faible) | La page officielle ne donne aucune durée (vérifié) | À 6 mois, besoin de trésorerie de 1 646 € (05 §5.4) |
| Taux de retour et SAV | 5 % du CA HT | Gadget à 24,90 € comparé à des produits à 15 € ; 30 jours pour changer d'avis | À 8 %, −0,72 € par commande sur le site |
| Porte 1 = demande | Une vidéo > 50 000 vues | La viralité d'une vidéo d'animal mesure l'attention (M6) | Stock acheté sur un faux signal |

### 3.2 Vérification web des chiffres les plus structurants (12/10/2026)

| # | Chiffre du dossier | Résultat | Source lue | Verdict |
|---|---|---|---|---|
| 1 | Droit de douane forfaitaire de 3 € par catégorie d'article sur les colis ≤ 150 € depuis le 1/07/2026 | Confirmé : « un droit de douane forfaitaire de 3 euros par catégorie d'article » ; suspension de la taxe française au 1/07 | [Ministère de l'Économie, communiqué n° 850](https://presse.economie.gouv.fr/?p=180373) | Exact |
| 2 | Redevance de gestion de l'Union de 2 € à partir du 1/11/2026 | Confirmé : « €2 per distinct item in a package », à partir du 1/11/2026, payée par le déclarant et répercutable. Le communiqué français ne donne pas le montant | [Revenue.ie, 29/09/2026](https://www.revenue.ie/en/corporate/press-office/press-releases/2026/pr-092926-handling-fee.aspx) | Exact, citation de 03 à corriger (m9) |
| 3 | Commission TikTok Shop France de 9 % depuis le 8/01/2026, 4 % pendant 60 jours pour une première boutique UE, assiette frais de port inclus | Confirmé : 9 % dès le 8/01/2026 ; 4 % jusqu'à 60 jours avec mission de 5 produits en 15 jours ; « montant total de la commande, expédition incluse » | [E-Commerce Nation, 9/12/2025](https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/) (source secondaire reprenant l'annonce TikTok) | Exact, confiance moyenne |
| 4 | Règlement TikTok Shop à 31 jours après livraison pour un vendeur débutant | Confirmé : 31 jours (« Débutant »), 8 jours standard, 3 jours accéléré (SPS ≥ 2,5 et > 4 500 $), 1 jour express (SPS ≥ 3 et > 30 000 $). Durée du statut débutant non indiquée | [TikTok Shop Seller University France](https://seller-fr.tiktok.com/university/essay?knowledge_id=747695670282004&default_language=en-GB) | Exact ; durée de 3 mois non sourcée |
| 5 | Expédition TikTok Shop sous 2 jours ouvrés depuis la France, livraison sous 4 jours ouvrés | Confirmé pour l'expédition par le vendeur ; l'expédition par TikTok est le mode par défaut en France, avec la date du transporteur ; annulation automatique au-delà de 7 jours ouvrés | [Politique d'expédition TikTok Shop France](https://seller-fr.tiktok.com/university/essay?default_language=fr&knowledge_id=6711589562500897) | Exact ; incompatible avec « 3 à 6 jours ouvrés » en expédition par le vendeur (M9) |
| 6 | Mondial Relay 4,15 € TTC jusqu'à 500 g | Le tableau de la source indique 4,15 € jusqu'à 0,5 kg et 5,99 € jusqu'à 1 kg depuis le 15/06/2026, mais l'introduction associe 4,15 € à 250 g ; grille grand public seulement | [Margeo](https://margeoapp.com/blog/tarifs-mondial-relay-2026) | Incertain (m8) |
| 7 | Médiateur CM2C : 48 € pour 3 ans, 36 € par médiation | Confirmé | [CM2C](https://www.cm2c.net/tarifs.php) | Exact |
| 8 | Fonctionnalité « renoncer au contrat ici » obligatoire depuis le 19/06/2026 | Confirmé, libellés « renoncer au contrat ici » et « confirmer la rétractation » (art. D. 222-2), accusé sur support durable avec date et heure | [La Cité des entreprises](https://www.lacitedesentreprises.com/droit-des-affaires/obligation-daffichage-du-bouton-de-retractation-en-ligne-les-precisions-apportees-par-le-decret-n-2026-3-du-5-janvier-2026/) | Exact |
| 9 | Cloudflare Web Analytics comme mesure d'audience | La CSP doit autoriser `static.cloudflareinsights.com` | [Cloudflare, FAQ Web Analytics](https://developers.cloudflare.com/web-analytics/faq/) | Incompatible avec la CSP livrée (M1) |
| 10 | Stripe et les précommandes | La liste des activités restreintes de Stripe ne mentionne ni précommande ni dropshipping hors Japon | [Stripe, activités restreintes](https://stripe.com/legal/restricted-businesses) | Pas d'interdiction ; risque de réserve non exclu |

Non vérifiés faute de quota de recherche : ROAS médian Meta 1,93 (la page Triple Whale renvoie une erreur 403), conversions TikTok Shop, durée du statut débutant, tarif « Expédition par TikTok », prix concurrents sur TikTok Shop. Ces points sont repris dans les corrections M8 et M9.

---

## 4. Conformité du site au regard de la checklist 03 §6

| Exigence (ID 03) | État constaté | Gravité |
|---|---|---|
| A1-A4 Identité, directeur de publication, hébergeur, contact | Pages présentes, 19 variables non remplies | Critique (C4) |
| A6 / N1 IDU emballages | Variable `{{IDU_EMBALLAGES}}` ; adhésion Léko prévue à la porte 1 | Bloquant avant la première vente |
| B1 CGV accessibles et téléchargeables | Oui (page + PDF) ; PDF à régénérer après remplissage | Conforme après C4 |
| B3 Encadré de garantie légale | Reproduit (art. 10.1) | Conforme |
| B5 / G2 Médiateur | Variable ; adhésion à la porte 1 | Conforme après adhésion (m7) |
| B6 Aucun lien RLL | Aucun lien trouvé | Conforme |
| C1 Récapitulatif et correction | Panier, tiroir et page Commande | Conforme |
| C2 Case CGV non pré-cochée | Oui ; refus testé sans case cochée | Conforme |
| C4 « Commande avec obligation de paiement » | Texte Stripe `custom_text.submit` | Conforme |
| C5 Confirmation sur support durable | E-mail avec CGV en PDF et formulaire type ; délai faux en précommande | Critique (C1) |
| D1 Prix TTC et port avant le panier | Oui sur chaque fiche | Conforme |
| D2-D3 Prix barrés, urgence, rareté | Aucun prix barré, compte à rebours ni stock fictif (crawl) | Conforme |
| D4 Origine | « Fabriqués en Chine, contrôlés et expédiés depuis la France » dans le pied de page | Conforme |
| D5 Allégations | Aucune allégation santé ; « renvoie la chaleur du corps » à justifier sur l'échantillon (tapis) | Conforme sous réserve |
| D6 Photos et vidéos | Illustrations signalées comme telles | Conforme ; photos réelles obligatoires avant vente |
| E1-E2 Rétractation et fonctionnalité en ligne | Libellés exacts, champs exigés, accusé horodaté ; fonction abusable (C5), JavaScript obligatoire (m12) | Conforme sur le fond |
| E6 Formulaire type | Présent (page Retours, annexe des CGV, PDF) | Conforme |
| F1-F2 Délai affiché | Dates calculées en jours ouvrés hors fériés ; contradictoires en précommande | Critique (C1) |
| F5 Aucun frais à la livraison | Mention présente | Conforme |
| H1-H3 Avis | État vide, aucun `aggregateRating`, règles écrites | Conforme |
| I1 Confidentialité | Complète pour le site ; TikTok Shop et les créateurs absents | Mineur |
| J1-J3 Cookies | Aucun traceur, aucun appel tiers (crawl : 0 requête externe), refus de même taille, lien permanent | Conforme |
| K1 Consentement e-mail | Portée du consentement plus étroite que les envois prévus | Majeur (M10) |
| L2 Bloc GPSR | Présent sur chaque fiche ; fabricant et avertissements « à valider » | Critique (C4) |
| L4 Coordonnées de l'importateur sur le produit | Prévu (étiquette) ; aucun gabarit livré | Majeur (M16) |
| M2 Étiquette textile | Non traité pour le tapis | Mineur (m13) |
| S1 RC produits | Reportée | Majeur (M11) |
| S2 Antériorité de marque | Recherche web seulement | Majeur (M12) |
| T1 Délai réel mesuré avant affichage | 3-6 jours affichés sans mesure | Acceptable si la règle des 30 livraisons est appliquée |

---

## 5. Bugs du site et tests

### 5.1 Ce qui fonctionne (tests de la red team)

| Contrôle | 390 px | 1 440 px |
|---|---|---|
| 21 pages crawlées, HTTP 200, un seul `h1`, aucun défilement horizontal | Oui | Oui |
| Liens internes et ressources (images, PDF, flux) | 0 lien cassé | 0 lien cassé |
| Erreurs console et erreurs JavaScript | 0 | 0 |
| Requêtes vers un domaine tiers | 0 | 0 |
| Ajout au panier, tiroir, total rouleau 28,80 €, suggestion Grand kit avec écart réel de 11,10 € | Oui | Oui |
| Rouleau + gant séparés : total 38,70 € et proposition du Kit anti-poils | Oui | Oui |
| Case CGV non pré-cochée, refus sans case, simulation jusqu'à `merci.html` | Oui | Oui |
| Champ point relais avec `<img onerror>` : texte échappé, aucune injection | Oui | Oui |
| Production simulée : le navigateur n'envoie aucun prix ; erreur serveur affichée, bouton réactivé | Oui | Oui |
| Liste d'attente : aucun bouton d'achat, paiement bloqué côté navigateur | Oui | Oui |

### 5.2 Défauts trouvés dans le parcours

| Défaut | Configuration | Référence |
|---|---|---|
| « Expédié sous 1 jour ouvré » et « livré en 3 à 6 jours ouvrés » affichés à côté des dates de précommande (bandeau en 1 440 px, bénéfices, FAQ, page Livraison) | Précommande | C1 |
| Page Commande et panier : aucune date de précommande, seulement « 3 à 6 jours ouvrés » | Précommande | C1 |
| Fiches en liste d'attente : « Expédié sous 1 jour ouvré » et « Lancement en novembre » restent affichés après novembre | Liste d'attente | C1, M14 |
| Faute « 2 rouleaus » | Toutes | m1 |
| Bandeau cookies sans traceur, 35 % de l'écran | 390 px | m6 |

### 5.3 Fonctions serveur (Stripe et Brevo simulés)

| # | Scénario | Résultat | Gravité |
|---|---|---|---|
| 1 | `create-checkout` sans en-tête `Origin`, phase forcée à « vente » par le client | 200 : session créée avec « Expédié depuis la France sous 1 jour ouvré » et estimation de livraison | M2 |
| 2 | Doublons de lignes (10 + 10 rouleaux) | Fusionnés et plafonnés à 10 ; total recalculé 249,00 € | Conforme |
| 3 | Quantité en texte, décimale, `__proto__`, `constructor`, 21 lignes | 400 pour chacun | Conforme |
| 4 | `retractation` sans `Origin`, adresse et contenu arbitraires | 200 : e-mail envoyé à la victime avec URL et texte de l'attaquant dans le corps et l'objet | C5 |
| 5 | `retractation` avec une origine étrangère | 403 | Conforme |
| 6 | `inscription` sans `Origin`, adresse arbitraire | 200 : e-mail de double opt-in envoyé | C5 |
| 7 | Webhook signé pour une commande `phase = precommande` | E-mail « Expédition… sous 1 jour ouvré, livraison… en 3 à 6 jours ouvrés », aucune date de précommande | C1 |
| 8 | Même webhook rejoué | Second e-mail envoyé | m2 |

---

## 6. Faisabilité de la contrainte « 0 € » et besoin de trésorerie

| Poste | Montant | Moment | Source | Inclus dans les 150 € ? |
|---|---|---|---|---|
| Domaine + échantillons | 45 € | S1 | 04 §5.3 | Oui |
| Médiateur CM2C (3 ans) | 48 € | Porte 1 | [CM2C](https://www.cm2c.net/tarifs.php) | Oui |
| Léko, minimum annuel | 114 € TTC | Porte 1 | 04 §1.1 | Dépassement |
| Fournitures | 12 € | Porte 1 | 04 §5.3 | Dépassement |
| Micro-stock initial | 197 € TTC | Porte 1, payé à la commande | 05 §5.2 | Non |
| Micro-stock recalculé pour 30 précommandes, la prime et 5 échantillons (M4) : ≈ 40 rouleaux, 45 gants, 12 raclettes, 8 tapis | ≈ 320 € HT, ≈ 385 € TTC (estimation, confiance faible) | Porte 1 | Calcul red team avec les coûts unitaires de `brand.json`, droits compris | Non |
| RC professionnelle et produits | 150-500 € par an | Avant le stock | 03 §0.5 | Non |
| Dépôt INPI classe 21 | 190 € | Porte 1 (M12) | [INPI](https://www.inpi.fr/inpi-block/download-document?id=20516) | Non |
| Réserve de trésorerie (TikTok à 31 jours, réassort, échantillons créateurs) | 1 309 € réaliste ; 3 088 € optimiste | Novembre 2026 à février 2027 | 05 §5.3 | Non |
| Expert-comptable et banque, si non déjà payés par la société | ≈ 100 € par mois | Continu | 05 §5.5 | Non |

**Conclusion.** La contrainte de 150 € permet la phase 0 (45 €) et l'adhésion au médiateur. Un lancement légal de stock propre demande **≈ 750 à 1 100 € engagés** (219 € de conformité et d'échantillons, ≈ 385 € de stock dimensionné, 150-500 € d'assurance), **≈ 950 à 1 300 €** avec le dépôt de marque (estimation, confiance moyenne), plus **≈ 1 300 € de réserve** dans le scénario réaliste, soit **≈ 2 050 à 2 600 €** au total. La seule voie compatible avec 150 € décrite dans le dossier (grossiste établi en France, schéma C de 03) a été écartée faute de grossiste trouvé pour le rouleau ; elle reste à chercher pour les complémentaires (gant, raclette).

---

## 7. Risques plateforme

| Plateforme | Risque | Déclencheur probable dans ce projet | Probabilité (estimation, confiance faible) | Parade |
|---|---|---|---|---|
| TikTok Shop | Pénalités de retard, plafond de commandes | Livraison > 4 jours ouvrés en expédition par le vendeur ; rupture après une vidéo virale | Moyenne | M9, M18 |
| TikTok Shop | Refus ou retrait de fiches | Informations GPSR incomplètes ; photos d'illustration ; plainte de propriété intellectuelle sur un clone ChomChom | Moyenne | C4, M12 ; photos réelles avant la création des fiches |
| TikTok Shop | Trésorerie bloquée | Règlement à 31 jours pendant le statut débutant (vérifié) | Certaine | C3 |
| TikTok (compte) | Portée réduite ou suspension | Contenu jugé non original, musique hors bibliothèque commerciale, défaut de mention « Collaboration commerciale » chez un affilié (responsabilité solidaire, loi n° 2023-451 art. 8 III) | Faible à moyenne | Règles du plan marketing ; contrôle hebdomadaire des vidéos d'affiliés |
| Stripe | Vérification renforcée, réserve, premier versement à 7-14 jours | Site avec variables `{{…}}`, précommandes à 3 semaines, pic soudain | Moyenne | C4 ; prévenir Stripe avant l'ouverture des précommandes ; politique de livraison claire |
| Stripe | Litiges « non reçu » | Retard sur la date de précommande (C2) | Moyenne | C2 ; remboursement proactif |
| Brevo | Suspension du compte, quota épuisé | Abus des fonctions ouvertes (C5) ; campagne > 300 e-mails par jour | Moyenne | C5 ; envoi étalé ; offre Starter le mois du lancement |
| Google Merchant Center | Suspension pour « déclarations trompeuses » | Illustrations, adresse manquante, `in_stock` sans stock | Élevée si soumis en l'état | Soumettre le flux seulement après C4, photos réelles et m5 |
| Cloudflare Pages | Faible | Fonctions au-delà de 100 000 requêtes par jour | Faible | `_routes.json` déjà limité à `/api/*` |
| PayPal | Retenue jusqu'à 21 jours | Après la bascule Shopify | Moyenne | Synchroniser les numéros de suivi |

---

## 8. Probabilités révisées par la red team

| Jalon | 04 Stratégie | 05 Finance | Red team | Raisons de l'écart |
|---|---|---|---|---|
| Porte 1 franchie (15/11) | 35-50 % | — | 50-65 % | Critère facile à atteindre avec une vidéo d'animal (M6) |
| ≥ 3 commandes par jour sur 7 jours avant le 31/03/2027 | — | Mars-avril 2027 (réaliste) | 15-25 % | Saison basse, prix, stock, temps (M5, M7, M8) |
| Palier 1 (1 k€ net par mois) à 12 mois | 30-40 % | 10-20 % | **5-12 %** | Idem, plus TikTok à 31 jours et coût d'étiquette TikTok inconnu |
| Palier 2 (10 k€ net par mois) à 24 mois | 5-10 % | 3-5 % | **1-3 %** | CPA cible ≤ 16,70 € contre 30 € au centre ; aucun réachat (M17) |
| 1 M€ net par mois | ≤ 0,1 % | ≤ 0,1 % | ≤ 0,01 % | Aucun modèle produit au-delà du palier 2 |

Toutes ces valeurs sont des estimations, confiance faible.

---

## 9. Sources manquantes, douteuses ou périmées

| Source | Utilisée pour | Problème | Action |
|---|---|---|---|
| Triple Whale (ROAS Meta 1,93, TikTok 2,21) | Toute la décision publicitaire | Données majoritairement américaines, 2025 ; page inaccessible (403) le 12/10/2026 | Remplacer au palier 2 par les données de tests réels ; signaler « US » à chaque citation |
| Agrégateurs de conversion (SimpleURL, TT Calculator, JoinBrands) | Entonnoirs 02 §2.2-2.3 | Blogs non vérifiés ; aucune méthode publiée | Remplacer par les chiffres du Seller Center après 1 000 vues produit |
| Kanal (frais Shopify Payments) | Comparatif des stacks | Source secondaire | Vérifier dans l'interface Shopify (03 alerte 11) |
| Speed Ecom (prix Shopify en euros) | Stack de croissance | La page officielle s'affiche en dollars | Relever le prix à l'inscription |
| netli.fyi (Netlify) | Choix de l'hébergeur | Source secondaire, confiance faible | Sans effet : Cloudflare retenu |
| Margeo (Mondial Relay) | Premier poste de coût (25,6 % du CA HT) | Contradiction interne (m8) | Grille officielle |
| Artisans 2.0 (seuil LIVE de 1 000 abonnés) | Plan marketing S8 | Non confirmé par TikTok | Vérifier dans l'application |
| Kohen Avocats (500 abonnés pour l'affiliation) | Recrutement des créateurs | Contredit d'autres guides | Vérifier dans le Seller Center |
| Sources tierces sur les limites Brevo | Capacité d'envoi | Page officielle non lue | Lire la page tarifs Brevo |
| URL Google « consignes aux expéditeurs » | Délivrabilité | Citée de mémoire (marketing) | Vérifier l'URL |
| Ministère de l'Économie (S1) pour la redevance de 2 € | 03 §0.1 et §3.4 | Le communiqué ne donne pas le montant | m9 |
| Prix fournisseurs AliExpress (3,50 € le rouleau) | Toutes les marges | « Prix d'index à revérifier » ; aucun devis | Devis écrit du vendeur retenu, frais de port du lot compris |
| Aucune source | Tarif « Expédition par TikTok », prix concurrents TikTok Shop, durée du statut débutant | Absents | M8, M9 |

---

## 10. Ce qui manque pour exécuter dès demain

| Manque | Pourquoi c'est bloquant | Livrable à produire | Délai |
|---|---|---|---|
| Décision budgétaire signée (C3) | Sans réserve, le plan casse en décembre | Une page de décision : option (a), (b) ou (c) | S1, jour 1 |
| Identité légale complète et décision de régime de TVA | Le site ne peut pas être publié ; `tva` de `config.js` et TikTok Shop en dépendent | Les 19 valeurs + avis de l'expert-comptable | S1 |
| Vérifications PI (DesignView, TMview, INPI) | Achat d'échantillons et vidéos d'un produit peut-être protégé | Captures datées dans le dossier produit | S1 |
| Fournisseur avec fabricant identifié | Bloc GPSR impossible sinon (C4) | Fiche fournisseur : lien, prix, port du lot, fabricant, notice | S1-S3 |
| Gabarits physiques | Étiquette importateur, notice en français, insert, Info-tri exigés à réception du stock | Fichiers imprimables par produit | S5 |
| Classeur de pilotage | Commandes, stock, délais (90e centile), réclamations GPSR, registre RGPD, créateurs, KPI | `docs/pilotage.xlsx` | S1 |
| Procédure Mondial Relay ou transporteur TikTok | Compte, caution, impression, dépôt | Fiche pas à pas | S5 |
| Plan d'exécution court | 15 documents et 100 000 mots, contradictoires (M15) | `docs/demarrage-J1-J14.md` | S1 |
| Test réel Stripe en mode test, déploiement Cloudflare réel | Rien n'a été déployé ni testé contre les vraies API (`site/README.md` §8) | Compte rendu de test avec la carte 4242 | Avant la porte 1 |
| Devis RC produits | Exposition d'importateur dès le premier colis | 3 devis | S1-S5 |

---

## 11. Ordre de correction recommandé

| Rang | Action | IDs | Coût | Échéance |
|---|---|---|---|---|
| 1 | Décision budgétaire écrite du client | C3 | 0 € | 13/10/2026 |
| 2 | Identité légale, régime de TVA, objet social | C4, M15, m14 | 0 € (expert-comptable déjà payé ou à chiffrer) | 16/10 |
| 3 | `config.js` en liste d'attente, sécurisation de `inscription` et `retractation`, CSP de la mesure, UTM | M14, C5, M1 | 0 € | 18/10 |
| 4 | Recherches PI produit et marque | M12 | 0 € | 18/10 |
| 5 | Critère « fabricant identifié » pour les échantillons ; achat B2B avec facture HT | C4, M13 | Inclus dans les 45 € | 18/10 |
| 6 | Fiche complète du tapis de fouille dans `brand.json` | M7 | 0 € | 1/11 |
| 7 | Phase et stock côté serveur, e-mail de précommande correct, textes générés par phase | C1, M2, M3 | 0 € | Avant le 15/11 |
| 8 | Recalcul du micro-stock et de la prime ; commande du stock à la porte 1 avant toute précommande | M4, C2 | ≈ 385 € TTC | 15/11 |
| 9 | RC produits souscrite | M11 | 150-500 € par an | Avant la commande du stock |
| 10 | Relevés TikTok Shop : prix concurrents, tarif d'étiquette, mode d'expédition | M8, M9 | 0 € | Avant l'ouverture de la boutique |

---

## Annexe : méthode des tests

| Test | Commande ou script | Résultat |
|---|---|---|
| Vérificateur fourni | `node site/outils/verifier_site.js http://127.0.0.1:8765 <scratchpad>` | 348/348 |
| Fonctions fournies | `node site/outils/tester_fonctions.js` | 17/17 |
| Crawl indépendant | Script Playwright (Chromium de `/opt/pw-browsers`), 2 tailles d'écran, collecte des liens, ressources, erreurs console, requêtes tierces, variables `{{…}}`, JSON-LD | 21 pages, 0 erreur, 0 lien cassé, 0 requête tierce |
| Parcours | Script Playwright avec `config.js` intercepté (`**/assets/js/config.js*`) en vente démo, précommande, liste d'attente et production simulée | 46 contrôles ; défauts du §5.2 |
| Fonctions serveur | Appel direct de `coeur.traiter()` avec `fetch` simulé et signature HMAC calculée | 8 scénarios ; défauts du §5.3 |
| Données | Contrôle croisé des prix entre `brand.json`, `data/products.json`, `products.csv`, `data.json` ; lecture du CSV Google Trends | §2 |

Les scripts et captures de la red team sont restés dans le dossier temporaire de la session ; aucun fichier du projet n'a été modifié.

---

## 12. Suivi des corrections

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 |
| Rôle | Ingénieur de correction : chaque problème critique et majeur a été traité directement dans les fichiers ; les points qui demandent une décision, un compte ou un document du client restent « non corrigé » avec la raison |
| Source unique | `strategie/brand.json` (v1.1). Toute valeur modifiée a été propagée par script : `site/outils/generer.py` → `site/data/products.json`, pages, flux, CGV HTML et PDF, `shopify-kit/products.csv` et pages ; `finance/modele_financier.py` → `modele_financier.xlsx` et `data.json` ; puis `finance/05-analyse-financiere.md`, `strategie/04-strategie.md` et les documents de `marketing/` réécrits avec les nouveaux chiffres |
| Hypothèse de coût | Coût produit **+20 %** en hypothèse de base (M13) : rouleau 5,40 € HT, gant 1,56 €, raclette 2,28 €, tapis thermique 6,00 € (valeurs d'origine conservées dans `*_hors_majoration`). Marge moyenne du mix de lancement : **6,30 €** par commande (7,55 € avant majoration) ; marge TikTok Shop via affilié sur le rouleau : 3,14 € (4,19 € dans la version revue) |
| Vérifications | `verifier_site.js` : **417/417** contrôles (390 px et 1 440 px, CSP appliquée, phases liste d'attente, précommande et vente, zéro erreur console) ; `tester_fonctions.js` : **19/19** ; `modele_financier.py` exécuté, recalcul LibreOffice **801 valeurs, 0 écart, 0 erreur** ; `docs/pilotage.xlsx` recalculé par LibreOffice sans erreur ; captures de `docs/captures/` régénérées (4 nouvelles : liste d'attente, tapis de fouille, fiche et commande en précommande) |
| Vérifications web | Le quota de recherche web de la session était épuisé : aucune requête de moteur de recherche. Pages lues directement le 12/10/2026 : [validation serveur Turnstile](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/) (POST `siteverify`, jeton valable 300 s, usage unique) et [FAQ Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/faq/) (`static.cloudflareinsights.com` dans `script-src`, `cloudflareinsights.com` dans `connect-src` en installation manuelle). La grille d'étiquettes TikTok Shop est rendue en JavaScript et n'a pas pu être lue (M9) |

### 12.1 Critiques et majeurs

| Problème | Statut | Détail |
|---|---|---|
| **C1** Délais de précommande contradictoires, e-mail de confirmation faux | **Corrigé** | `brand.json` → `livraison.phase` et `livraison.precommande` portent la phase et les dates ; `generer.py` produit le bandeau, l'encart de la fiche, la FAQ, le panier, la page Commande, la page Livraison et l'art. 7.1 des CGV selon la phase. `coeur.js` relit la phase et les dates dans `data/products.json` (jamais dans le navigateur), les écrit sur la page Stripe (`custom_text`), dans `metadata` et dans l'e-mail (`phraseLivraison`). Contrôles : « 1 jour ouvré » absent des 30 fichiers publics en précommande (Playwright) ; tests serveur « précommande » et « webhook précommande » |
| **C2** Calendrier de précommande intenable | **Corrigé** | Ordre imposé (`livraison.precommande.ordre_des_operations`) : porte 1, micro-stock commandé et payé le 16/11, calcul des dates, puis ouverture. Règle : date de commande + 90e centile du transit mesuré sur les échantillons + 3 jours ouvrés, livraison = expédition + 6 jours ouvrés, plafond 30 jours (`generer.py` refuse au-delà, et refuse la phase précommande sans dates). Exemples pour une commande du 16/11 : transit 8 j → livraison au plus tard le 07/12 ; 12 j → 10/12 ; 20 j → 17/12 ; 25 j → 24/12, sans argument Noël. Contrôle J-10 avec annulation remboursée sous 14 jours ; vendeur en entrepôt UE ou envoi express conseillé. Dates de `config.js` supprimées. Les dates réelles dépendent du transit mesuré par le client sur ses échantillons |
| **C3** Trésorerie : montants unifiés | **Corrigé** | Mêmes chiffres dans `brand.json` → `hypotheses_cles.tresorerie`, 04 §0 et §5.3, 05, `data.json` et `docs/demarrage-J1-J14.md` : 45 € avant la porte 1 ; 389 € de conformité à la porte 1 (CM2C 48 €, Léko 114 €, fournitures 12 €, INPI 190 €, 1er mois de RC 25 €) ; 476 € de micro-stock ; **910 € avant le premier encaissement** (1 185 € si la RC est payée à l'année) ; creux **2 000 €** (réaliste, février 2027), 4 539 € (optimiste), 1 220 € (pessimiste, novembre 2027). Ces montants dépassent ceux de la revue (416 €, 1 300-1 500 €) parce que le modèle inclut désormais la majoration de 20 %, le lot de 105 articles, la prime, la RC dès novembre et l'INPI à la porte 1. Ligne « réserve de trésorerie disponible » avec alerte sous 300 € dans 04 §6.7 et `pilotage.xlsx` (Trésorerie, KPI hebdo) |
| **C3** Choix écrit de l'option de financement | **Non corrigé** | Décision du client. Options rédigées dans `brand.json` (a : apport de 2 400 € ; b : ventes TikTok Shop plafonnées au stock payé, sans affiliés avant le premier règlement, apport minimal de 910 € ; c : arrêt à 45 €), `option_retenue` = `null`, à signer en J1 de `docs/demarrage-J1-J14.md` |
| **C4** Garde-fou de publication et critère fournisseur | **Corrigé** | `generer.py --publication` sort en erreur (code 1) et liste les variables tant qu'un `{{…}}` reste visible ; contrôle Playwright dédié. Identité saisie en un seul endroit (`brand.json` → `identite`, 21 champs). En liste d'attente, les champs propres à la vente (médiateur, IDU, adresses de retour et d'expédition, fabricants) affichent « désigné avant l'ouverture des ventes » ; ils redeviennent bloquants en précommande et en vente. Critères éliminatoires du fournisseur (fabricant identifié par écrit, notice, photos d'étiquette, facture B2B HT, un colis) dans `brand.json` → `approvisionnement` et 04 §5.4, repli CJ ou agent. Gabarits imprimables : étiquette importateur, 5 notices, carte de colis (`docs/gabarits/`) |
| **C4** Remplissage des variables d'identité et des fabricants | **Non corrigé** | Données que seul le client détient (raison sociale, SIREN, RCS, TVA, adresse, hébergeur, directeur de publication, fabricants réels). État actuel : 12 variables visibles en phase liste d'attente, site non publiable ; `generer.py --publication` le refuse |
| **C5** Fonctions `/api/retractation` et `/api/inscription` détournables | **Corrigé** | `coeur.js` : en-tête `Origin` égal à `SITE_URL` exigé pour checkout, rétractation et inscription (403 sinon ; le webhook reste protégé par la signature HMAC) ; jeton Turnstile vérifié côté serveur quand `TURNSTILE_SECRET_KEY` est défini (widget autorisé par la CSP) ; 3 requêtes par heure et par IP (stockage KV `CANAPOIL_KV`, mémoire à défaut, 429 au-delà) ; rétractation : recherche de la session Stripe payée avec le même e-mail, sinon rien n'est envoyé à l'adresse saisie et seul le service client est alerté ; champs filtrés, URL refusées. 7 tests serveur couvrent ces cas. Les clés Turnstile (gratuites) sont à créer par le client dans Cloudflare (`site/README.md` §5) |
| **M1** Mesure impossible | **Corrigé** | `_headers` : `static.cloudflareinsights.com` dans `script-src`, `cloudflareinsights.com` dans `connect-src` (conforme à la FAQ Cloudflare lue le 12/10/2026). UTM conservés en `sessionStorage`, envoyés au checkout, copiés dans les métadonnées Stripe et en attributs Brevo (`UTM_SOURCE`, `UTM_CAMPAIGN`, `UTM_CONTENT`). Page `/liste-attente/tapis-de-fouille/` et champ caché `produit` (attribut `PRODUIT`). Reste au client : vérifier après déploiement qu'une visite remonte dans le tableau de bord Cloudflare |
| **M2** Phase et stock inconnus du serveur | **Corrigé** | `coeur.js` refuse le paiement (503) si `products.json` est en liste d'attente, quelle que soit la phase envoyée par le navigateur, et refuse (409) une quantité supérieure au stock affiché, kits compris. `produits[].stock_disponible` dans `brand.json` (0 aujourd'hui). `STRIPE_SECRET_KEY` saisie à la porte 1 seulement (`site/README.md` §5, démarrage J12) |
| **M3** Aucune gestion de stock | **Corrigé** | Sous 5 unités, passage automatique en précommande avec les dates de réassort, ou en « épuisé » sans date ; stock TikTok Shop = stock réel − 2, mis à jour à 9 h et 18 h ; `products.csv` : kits suivis (`Inventory tracker` = `shopify`, quantité du composant le plus rare, gants de la prime exclus du stock vendable), consigne Shopify Bundles ; onglets Mouvements stock et Stock dans `pilotage.xlsx` |
| **M4** Micro-stock incompatible avec l'offre | **Corrigé** | Lot recalculé : 40 rouleaux, 45 gants, 12 raclettes, 8 tapis thermiques (476 € TTC). Prime limitée aux 30 gants réservés, avec compteur daté (`livraison.precommande.prime`) ; coût 54,30 € HT inscrit dans le modèle financier (ligne « prime de lancement ») |
| **M5** Plan de 35-43 h pour 20-25 h disponibles | **Corrigé** | Plan ramené à 25 h (07 §4.5) : 2 vidéos par jour, recyclage limité à Reels et Pinterest, LIVE à partir de S12, 4 articles SEO avant février. `HEURES_FONDATEUR` = 25 : 3,77 € net de l'heure dans le scénario réaliste |
| **M5** Option 35-40 h | **Non corrigé** | Décision du client (04 §8, décision 6) : le plan à 3 vidéos par jour n'est rétabli que s'il dispose réellement de 35-40 h |
| **M6** Probabilités et portes divergentes | **Corrigé** | Palier 1 à 12 mois : 10-20 % partout (04, `brand.json`, 05), avec la lecture red team (5-12 %) citée. Porte 1 : trois conditions, dont ≥ 1,5 % de clics produit et ≥ 20 commentaires d'intention hors entourage (probabilité 35-50 %). Porte « stock » : ≥ 20 précommandes hors entourage et conversion liste → précommande ≥ 8 %, condition du réassort |
| **M7** Creux saisonnier, duel non ouvert | **Corrigé** | Tapis de fouille dans `brand.json` → `challengers` : 29,90 €, coût 9,00 € HT (+20 %), droits 0,45 €, avertissement d'ingestion GPSR, page générée et notice. Si le rouleau gagne, stock principal décalé à fin janvier 2027 (04, `brand.json` → `lancement`, lancement-30-jours). Le coût du tapis reste une estimation à confirmer sur l'échantillon |
| **M8** Prix du héros : règle de décision | **Corrigé** | 04 §0 et §3.2 : prix conditionnel (si la médiane TikTok Shop est sous 16 €, rouleau à 19,90 € et Grand kit seul mis en avant, marges recalculées) ; onglet « Prix TikTok Shop » de `pilotage.xlsx` ; relevé planifié en J10. Conversion TikTok Shop de 3,5 % marquée « agrégateur non sourcé, confiance faible » |
| **M8** Relevé des 20 rouleaux concurrents sur TikTok Shop | **Non corrigé** | Exige l'application TikTok sur téléphone (onglet Boutique) ; inaccessible depuis cette session, sans moteur de recherche (quota épuisé). Action client en J10 |
| **M9** Exigences d'expédition TikTok Shop | **Corrigé** | `brand.json` → `livraison.tiktok_shop` : expédition par TikTok ou transporteur agréé remis à J+2, livraison sous 4 jours ouvrés ; Mondial Relay interdit pour TikTok Shop tant que le 90e centile mesuré dépasse 4 jours ouvrés. Paramètres séparés `PORT_TTS_500` et `PORT_TTS_1KG` dans le modèle |
| **M9** Tarif de l'étiquette « Expédition par TikTok » | **Non corrigé** | Non publié hors Seller Center (page rendue en JavaScript, illisible le 12/10/2026). Le modèle garde 4,50 € et 5,50 € HT, signalés « hypothèse non vérifiée » ; relevé à faire à l'ouverture du compte vendeur (démarrage J8) |
| **M10** Consentement e-mail insuffisant | **Corrigé** | Case non pré-cochée et obligatoire (« annonce du lancement, tests et nouveautés, 2 e-mails par semaine au plus »), refusée sans consentement côté navigateur et côté serveur ; attributs Brevo `CONSENTEMENT_DATE` et `CONSENTEMENT_TEXTE` ; double opt-in. `emails.md` : PA1-PA3 suspendus tant que la case du panier et le webhook `checkout.session.expired` n'existent pas |
| **M11** RC produits : place dans le calendrier et le modèle | **Corrigé** | RC obligatoire avant la commande du micro-stock dans 04, `brand.json` → `assurance`, lancement-30-jours et démarrage (devis en J8) ; ligne `RC` du modèle à partir de novembre 2026 (25 € par mois) |
| **M11** Devis et souscription | **Non corrigé** | Action du client : 3 devis RC professionnelle + RC produits (150-500 € par an, estimation, confiance faible) |
| **M12** Propriété intellectuelle : procédure | **Corrigé** | Recherches DesignView (Locarno 04-02 et 08-05), TMview et data.inpi.fr en J2, avec captures datées et critère d'arrêt ; dépôt « Canapoil » classe 21 à la porte 1 (190 €) dans le budget de 389 € et dans le modèle (mois de novembre 2026) ; classes 20 et 28 à la porte 2 |
| **M12** Recherches et dépôt | **Non corrigé** | Bases interactives et dépôt au nom de la société : action du client (J2 et porte 1) |
| **M13** Coût d'achat : hypothèses | **Corrigé** | Majoration de 20 % en base (voir en-tête) ; droits par article recalculés pour un colis unique : 0,40 € (rouleau), 0,25 € (gant), 0,30 € (raclette), 0,50 € (tapis thermique) ; achat B2B HT en un colis dans les critères éliminatoires ; 05 et `data.json` recalculés |
| **M13** Traitement TVA et douane du lot | **Non corrigé** | Validation par l'expert-comptable avant la porte 1 (démarrage J4) |
| **M14** `config.js` livré en vente | **Corrigé** | `config.js` ne contient plus ni phase ni dates : la phase vient de `brand.json` (liste d'attente par défaut) ; `mode` = `demo` par défaut avec bandeau « Démonstration » sur toutes les pages (contrôle Playwright) ; `generer.py` refuse la précommande sans dates ou au-delà de 30 jours |
| **M15** Consignes contradictoires | **Corrigé** | `brand.json` seule source : Noël = commande avant le 15/12 pour une livraison au plus tard le 23/12 ; service client 48 h ouvrées (CGV art. 10.2 et 12, mentions, contact, FAQ alignés ; 24 h reste une cible interne) ; délai « expédié sous 1 jour ouvré, livré 3 à 6 jours ouvrés après la commande » identique partout en phase vente ; RC avant le stock dans 03, 04 et le modèle |
| **M15** Régime de TVA | **Non corrigé** | `regime_tva.decision` = `a_decider` : le site affiche le régime assujetti (prudent) ; la franchise rapporterait 1,29 € de plus par commande (05 §8.1). Décision du client avec l'expert-comptable (démarrage J4) |
| **M16** Dossier non exécutable par un débutant | **Corrigé** | `docs/demarrage-J1-J14.md` (une page par jour : action, durée, coût, lien, résultat attendu ; annexe Mondial Relay ; option Shopify à 1 $ par mois si le déploiement bloque) ; `docs/pilotage.xlsx` (14 onglets dont Commandes, Stock, Délais, Trésorerie, KPI hebdo, Réclamations GPSR, Registre RGPD, Créateurs, Prix TikTok Shop) ; gabarits d'étiquette, de notice et de carte de colis |
| **M17** Paliers 3 et 4 sans base produit | **Corrigé** | Paliers 3 et 4 présentés comme repères d'échelle, sans probabilité chiffrée (04, `brand.json`, 05) ; critère « produit à ≥ 15 % de réachat à 180 jours » avant toute publicité au-delà de 1 000 € par mois (04, 05, bascule-payant) |
| **M18** Risque de pic viral sous-estimé | **Corrigé** | Risque requalifié « moyen » (07) ; procédure dans `brand.json` → `livraison.stock.procedure_pic_viral` : stock TikTok Shop mis à jour toutes les 2 heures, précommande avec dates réelles dès 5 unités, réassort express à 10 unités si la réserve le permet, aucune ancre produit au-delà de 20 000 vues en 6 heures si le stock couvre moins de 7 jours |

### 12.2 Mineurs

| Problème | Statut | Détail |
|---|---|---|
| m1 « 2 rouleaus » | Corrigé | `nom_court_pluriel` ; contrôle Playwright « 2 rouleaux » |
| m2 Webhook non idempotent | Corrigé | Identifiant d'événement mémorisé dans KV ; test « webhook rejoué » |
| m3 Lignes recalculées, CGV jointes en dernière version | Non corrigé | Seule la version des CGV acceptée est enregistrée dans `metadata.cgv_version` et citée dans l'e-mail ; lecture de `line_items` et PDF daté non faits (hors périmètre des critiques et majeurs) |
| m4 Numéro de commande absent de `merci.html` | Corrigé | 10 derniers caractères de la session, contrôle Playwright |
| m5 `InStock` quelle que soit la phase | Corrigé | JSON-LD `InStock`, `PreOrder` ou `OutOfStock` ; flux `in_stock`, `preorder` avec `availability_date`, `out_of_stock` |
| m6 Bandeau cookies sans traceur actif | Non corrigé | Le bandeau gouverne le chargement de Cloudflare Web Analytics (catégorie « mesure ») ; le supprimer suppose une analyse d'exemption de consentement non faite ici |
| m7 Médiateur `{{MEDIATEUR}}` en liste d'attente | Corrigé | Mention neutre en liste d'attente, variable bloquante en vente |
| m8 Tarif Mondial Relay de source secondaire | Non corrigé | Relevé sur mondialrelay.fr à faire par le client (annexe du démarrage, étape 1) ; quota de recherche épuisé |
| m9 Citation de la redevance de 2 € | Non corrigé | Correction dans `recherche/03-legal-ops.md`, dossier hors du périmètre d'écriture de cette mission |
| m10 Délais de réponse incohérents | Corrigé | 48 h ouvrées partout (M15) |
| m11 Phrase du décret n° 2026-3 | Non corrigé | Texte du décret à lire sur Légifrance avant reprise mot pour mot |
| m12 Rétractation sans JavaScript | Non corrigé | Formulaire toujours sans `action` ; à traiter avec l'acceptation de `application/x-www-form-urlencoded` côté serveur |
| m13 Composition et REP du tapis thermique | Corrigé en partie | Obligation d'étiquette de composition et question REP à Léko inscrites dans `caracteristiques` ; composition exacte à reporter depuis l'échantillon |
| m14 Objet social | Corrigé en partie | Vérification du Kbis inscrite en J4 du démarrage ; vérification elle-même à faire par le client |
| m15 Produits Shopify actifs et publiés | Corrigé | `Status` = `Draft`, `Published on online store` = `FALSE` |
| m16 Répartition TikTok Shop calibrée | Corrigé en partie | Hypothèse marquée « confiance faible, à remplacer après 30 commandes TikTok Shop » dans le modèle ; remplacement possible seulement avec des données réelles |

### 12.3 Ce que le client doit encore trancher ou fournir avant les précommandes

| Ordre | Décision ou donnée | Où la saisir | Bloque |
|---|---|---|---|
| 1 | Option de financement a, b ou c, signée | `brand.json` → `hypotheses_cles.tresorerie.option_retenue` | Porte 1 (C3) |
| 2 | 21 champs d'identité, dont fabricants | `brand.json` → `identite` | Toute publication (C4) |
| 3 | Régime de TVA, traitement TVA et douane du lot | `brand.json` → `regime_tva` | Porte 1 (M13, M15) |
| 4 | RC souscrite | `brand.json` → `assurance` | Commande du stock (M11) |
| 5 | Recherches DesignView, TMview, INPI | Dossier produit | Échantillons (M12) |
| 6 | Relevés TikTok Shop : 20 prix concurrents, tarif d'étiquette | `pilotage.xlsx` → Prix TikTok Shop ; `brand.json` → `livraison.tiktok_shop.port_ht` | Prix du héros, modèle (M8, M9) |
| 7 | Clés Turnstile, Stripe (à la porte 1), Brevo ; stockage KV | Hébergeur (`site/README.md` §5) | Mise en ligne sécurisée (C5) |

## 13. Contrôle complémentaire : brevet ChomChom (orchestrateur, 12/10/2026)

| Point | Constat | Source | Confiance |
|---|---|---|---|
| Brevet de base du ChomChom Roller | US 8 117 706 B2, « Manual cleaning instrument », inventeur Tsutomu Sato, titulaire Nippon Seal Co. ; priorité JP 04/03/2008 ; expiration estimée 09/01/2030 aux États-Unis. ChomChom (Word Ape, puis Cheddar Creations) en est licencié exclusif et l'a fait valoir aux États-Unis | [Google Patents US8117706B2](https://patents.google.com/patent/US8117706B2/en) ; [Cheddar Creations v. Pawico](https://case-law.vlex.com/vid/cheddar-creations-inc-v-1028687036) | Élevée |
| Extension en Europe | La famille ne contient que des dépôts US, JP, CN (modèle d'utilité expiré) et HK (éteint). Aucun dépôt EP, FR, DE ou WO n'apparaît | [Google Patents US8117706B2](https://patents.google.com/patent/US8117706B2/en) | Moyenne (un autre brevet ou un dessin et modèle UE hors de cette famille reste possible) |
| Marque | « CHOMCHOM ROLLER » est déposée aux États-Unis | [Justia Trademarks 87395211](https://trademarks.justia.com/873/95/chomchom-87395211.html) | Élevée |
| Droit d'auteur | Un tribunal américain a interdit à un concurrent toute œuvre dérivée de la publicité vidéo ChomChom | [Cheddar Creations v. Pawico](https://www.casemine.com/judgement/us/6610d0ec98c8641582fe77dc) | Élevée |

**Conclusion.** Le risque brevet en France est faible à moyen sur la base de cette famille. Trois risques demeurent, et ils justifient de garder M12 ouvert :

1. **Dessins et modèles UE.** Ils restent non vérifiés. La recherche DesignView de J2 reste obligatoire.
2. **Copie servile.** Copier la forme et les couleurs exactes du ChomChom peut constituer de la concurrence déloyale ou du parasitisme en droit français. Choisir un modèle fournisseur visuellement distinct.
3. **Usage du nom et des contenus.** Ne jamais utiliser le nom « ChomChom », dans les annonces comme dans les mots-clés (règle déjà prévue dans marketing/seo-contenu.md). Ne jamais reprendre ses vidéos ni ses visuels.
