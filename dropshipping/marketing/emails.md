# E-mails : flux automatiques de Canapoil

| Champ | Valeur |
|---|---|
| Date | 12 octobre 2026 (version corrigée après la [revue red team](../docs/revue-red-team.md) : consentement codé sur le site, relances de panier suspendues) |
| Outil | Brevo gratuit au lancement (`brand.json` → `stack.lancement.email`) ; Shopify Messaging après la bascule (`stack.croissance`) |
| Expéditeur | « Canapoil » `<{{EMAIL}}>`, adresse de réponse lue chaque jour |
| Ton | Vouvoiement (`brand.json` → `marque.ton`) ; phrases courtes ; chiffres réels |
| Variables | `{{ contact.PRENOM }}` et `{{ params.X }}` = variables Brevo (attributs de contact et paramètres transactionnels). `{{EMAIL}}`, `{{RAISON_SOCIALE}}`, `{{ADRESSE}}` = champs de `brand.json` à remplacer une fois pour toutes |

---

## 0. Vue d'ensemble

| ID | Flux | Déclencheur | Délai | Destinataires | Base légale | Mise en œuvre au lancement |
|---|---|---|---|---|---|---|
| BV0 | Confirmation d'inscription (double opt-in) | Formulaire de liste d'attente | Immédiat | Inscrits | Consentement | Modèle Brevo appelé par `/api/inscription` avec les attributs `PRODUIT`, `CONSENTEMENT_DATE`, `CONSENTEMENT_TEXTE`, `SOURCE` et `UTM_*` |
| BV1-BV3 | **Bienvenue** | Inscription confirmée | J0, J+3, J+7 | Inscrits confirmés **dont l'attribut `CONSENTEMENT_DATE` est renseigné** (case du §1.2 cochée) | Consentement | Automatisation Brevo filtrée sur cet attribut ; les inscrits antérieurs au formulaire du 12/10/2026 ne reçoivent que BV0 et C1 |
| PA1-PA3 | **Panier abandonné — SUSPENDU** | Session Stripe expirée sans paiement | H+1, H+24, H+72 | **Aucun envoi** tant que la case de rappel du panier et le webhook `checkout.session.expired` n'existent pas sur le site | Consentement préalable | Non développé : textes conservés au §3 pour la bascule Shopify ou un développement ultérieur |
| PO1-PO3 | **Post-achat** | Paiement, expédition, livraison | J0, expédition, J+7 après livraison | Clients du site | Exécution du contrat (PO1, PO2) ; exception « client » pour le bloc produit de PO3 | Brevo transactionnel + automatisation |
| AV1 | **Demande d'avis** | Livraison | J+10 après livraison | Clients du site | Intérêt légitime (service), sans contrepartie | Automatisation Brevo |
| RE1 | **Réactivation** | 75 jours sans commande | J+75 | Clients ayant accepté les offres analogues | Exception « client » (L34-5 CPCE) | Automatisation Brevo |
| C1-C2 | Annexe : campagnes d'ouverture des précommandes | Stock commandé, dates de précommande publiées | Ouverture et J+6 | Liste d'attente (tout inscrit confirmé : l'annonce de l'ouverture est couverte par l'ancien et le nouveau texte) | Consentement | Campagnes manuelles |

Les clients TikTok Shop ne reçoivent aucun de ces e-mails : la relation passe par la messagerie du Seller Center.

---

## 1. Conformité et paramétrage (à faire avant le premier envoi)

### 1.1 Règles qui s'appliquent

| Sujet | Règle | Conséquence pour Canapoil | Source |
|---|---|---|---|
| Prospection par e-mail | Consentement préalable, sauf client existant pour des produits analogues du même vendeur, informé et en mesure de s'opposer à la collecte puis dans chaque message | Liste d'attente en double opt-in ; case d'opposition à la collecte de l'adresse client ; lien de désinscription dans chaque e-mail | Art. L34-5 CPCE ([CNIL](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique)) |
| **Relance de panier** | La CNIL la qualifie de courriel promotionnel relevant de l'article L34-5 : **consentement préalable du destinataire** | PA1-PA3 partent seulement vers les personnes qui ont coché la case de rappel sur `/panier/` | [FAQ CNIL, question 16](https://www.cnil.fr/fr/faq-recommandation-pixels-courriers-electroniques) |
| Pixels de suivi | Recommandation CNIL adoptée le 12/03/2026, publiée le 14/04/2026, période de transition close le 14/07/2026 : un pixel d'ouverture exige le consentement, sauf l'usage limité à la « date de dernière ouverture » pour espacer ou arrêter les envois aux inactifs ; une statistique globale anonymisée du taux d'ouverture reste possible avec un pixel exempté | Suivi des ouvertures désactivé dans Brevo, ou case de consentement distincte à l'inscription (à vérifier selon les options du compte gratuit) ; KPI e-mail mesurés par les visites suivies (`utm_source=email`) dans la mesure d'audience sans cookie du site | [FAQ CNIL, questions 6, 7, 16](https://www.cnil.fr/fr/faq-recommandation-pixels-courriers-electroniques) ; [synthèse De Gaulle Fleurance](https://www.degaullefleurance.com/actualites/pixels-de-suivi-dans-les-courriels-ce-que-changent-la-recommandation-de-la-cnil-et-la-faq-du-22-juillet-2026/) |
| Liens traçants | Le suivi individuel des clics par redirection n'est pas couvert explicitement par les extraits consultés | Suivi des clics de Brevo désactivé par prudence tant qu'un juriste ne l'a pas validé ; mesure agrégée par UTM | Point à valider (confiance faible) |
| Avis clients | Information sur le contrôle des avis ; avis négatifs publiés ; date affichée ; tri chronologique ; contrepartie signalée | AV1 sans contrepartie ; formulaire relié au numéro de commande | Art. L111-7-2 et D111-17 à D111-19 du Code de la consommation (03 §1.8) |
| Prix et urgence | Aucune réduction pendant les 30 premiers jours ; aucun compte à rebours sans date de fin réelle | Aucune remise dans les relances ; seules des dates réelles (fin des précommandes, date limite de Noël) | `brand.json` → `regles_commerciales` ; 03 §1.7 |
| Confirmation de commande | Confirmation sur support durable avec les informations du contrat | PO1 contient le récapitulatif, le lien des CGV, la date d'expédition et le lien « renoncer au contrat ici » | 03 §1.3 ; `brand.json` → `retours.fonction_retractation.emplacements` |
| Délivrabilité | Domaine authentifié (SPF, DKIM, DMARC) et désinscription en un clic, exigés par Gmail et Yahoo pour les expéditeurs en volume | Authentification du domaine `canapoil.fr` dans Brevo en S1 | [Google, consignes aux expéditeurs](https://support.google.com/a/answer/81126) |

### 1.2 Textes de consentement

| Emplacement | Texte exact | Type |
|---|---|---|
| Formulaire de liste d'attente | « Je souhaite recevoir par e-mail l'annonce du lancement, les tests et les nouveautés de Canapoil (2 e-mails par semaine au plus, hors e-mails liés à mes commandes). Désinscription en un clic dans chaque e-mail. » | Case non pré-cochée, obligatoire pour s'inscrire. **Codée sur le site le 12/10/2026** (fiches, page du tapis de fouille, accueil) ; refus serveur sans case ; date et version du texte enregistrées dans Brevo (`CONSENTEMENT_DATE`, `CONSENTEMENT_TEXTE`) |
| Formulaire de liste d'attente (facultatif) | « J'accepte que Canapoil mesure l'ouverture de ses e-mails. » | Case distincte, non pré-cochée (seulement si le suivi des ouvertures est conservé) |
| Page `/panier/` | « Envoyez-moi un rappel par e-mail si je ne termine pas ma commande (3 e-mails au plus, sur 3 jours). » | Case non pré-cochée ; champ e-mail affiché seulement si la case est cochée. **Non codée : PA1-PA3 suspendus** |
| Page `/panier/`, sous le bouton de paiement | « Après votre commande, Canapoil peut vous écrire au sujet de produits similaires. Vous pouvez vous y opposer en cochant cette case, puis à tout moment dans chaque e-mail. » | Case d'opposition non pré-cochée (exception « client ») |

### 1.3 Développements à demander à l'agent site (état au 12/10/2026 : 1 à 3 non réalisés, relances de panier suspendues ; consentement de la liste d'attente réalisé)

| # | Développement | Raison |
|---|---|---|
| 1 | Sur `/panier/` : les deux cases ci-dessus, e-mail transmis à Stripe (`customer_email`) et consentement stocké en métadonnées de session | La collecte du consentement promotionnel par Stripe Checkout est réservée aux entreprises et clients situés aux États-Unis ([Stripe](https://docs.stripe.com/payments/checkout/promotional-emails-consent)) ; Stripe indique qu'on peut s'en passer quand l'e-mail et le consentement sont recueillis avant la redirection ([Stripe, paniers abandonnés](https://docs.stripe.com/payments/checkout/abandoned-carts)) |
| 2 | Création de session avec `after_expiration.recovery.enabled = true` et `expires_at` = création + 1 h | Stripe génère alors une URL de reprise valable 30 jours ; l'expiration minimale est de 30 minutes ([Stripe](https://docs.stripe.com/payments/checkout/abandoned-carts)) |
| 3 | Fonction `/api/stripe-webhook` : `checkout.session.expired` → si consentement, appel de l'API Brevo (contact + attributs `URL_REPRISE`, `ARTICLES`, `MONTANT`) qui déclenche PA1-PA3 ; `checkout.session.completed` → PO1 transactionnel, attribut `DERNIERE_COMMANDE`, retrait du flux panier ; un seul flux panier par adresse et par 7 jours | Éviter les relances multiples, que Stripe signale explicitement |
| 4 | Attribut `DATE_EXPEDITION` saisi depuis le tableur (ou bouton dans un back-office minimal) qui déclenche PO2 ; date de livraison estimée = expédition + 5 jours ouvrés pour PO3, AV1 et RE1 | Pas d'intégration transporteur au lancement |

Après la bascule sur Shopify : flux natifs de Shopify Messaging, avec l'envoi des relances de panier limité aux abonnés marketing.

### 1.4 Limites de l'offre gratuite de Brevo

| Élément | Valeur | Source | Effet |
|---|---|---|---|
| Envois | 300 e-mails par jour | [La Fabrique du Net](https://www.lafabriquedunet.fr/email-marketing/articles/tarifs-brevo/) (02 §6.4) ; [independant.io](https://independant.io/avis/brevo/) | Une campagne à 450 inscrits part en 2 jours : prévoir l'envoi de C1 sur J1 et J2 ou passer à Starter (dès 7 € par mois) le mois du lancement |
| Automatisation | Scénarios limités à 2 000 contacts selon deux sources tierces | [independant.io](https://independant.io/avis/brevo/), [Joinsecret](https://www.joinsecret.com/fr/sendinblue/pricing) (fiabilité faible) | Sans effet avant le palier 1 ; à vérifier dans le compte |
| Transactionnel | Inclus dans l'offre gratuite (API et SMTP), dans la limite quotidienne | [Hackceleration](https://hackceleration.com/fr/labs/combien-coute-brevo) | PO1 et PO2 consomment le quota : surveiller les jours de pic |
| Logo Brevo | Présent dans le pied de page en offre gratuite | Idem | Acceptable au palier 0 |

### 1.5 Pied de page commun

> Canapoil · {{RAISON_SOCIALE}} · {{ADRESSE}}
> Vous recevez cet e-mail parce que {raison : vous vous êtes inscrit à la liste d'attente le {date} / vous avez commandé sur canapoil.fr / vous avez demandé un rappel de panier}.
> [Se désinscrire en un clic] · [Nous écrire : {{EMAIL}}] · [Conditions générales de vente] · [Renoncer au contrat ici]

Le lien « Renoncer au contrat ici » figure dans PO1, PO2 et PO3 ; il pointe vers `https://canapoil.fr/retractation/`.

---

## 2. Flux de bienvenue (liste d'attente)

### BV0 — Confirmation d'inscription (double opt-in, technique)

| Champ | Contenu |
|---|---|
| Objet | Confirmez votre inscription au lancement Canapoil |
| Pré-en-tête | Un clic et vous serez prévenu le jour de l'ouverture. |
| Déclencheur | Envoi du formulaire (modèle `BREVO_TEMPLATE_DOI`) |

> Bonjour,
>
> Vous venez de demander à être prévenu du lancement de Canapoil. Pour confirmer, cliquez sur le bouton ci-dessous.
>
> **[Je confirme mon inscription]**
>
> Sans clic de votre part, nous ne vous écrirons pas. Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.
>
> L'équipe Canapoil

### BV1 — J0 après confirmation

| Champ | Contenu |
|---|---|
| Objet | Bienvenue sur le canapé |
| Pré-en-tête | Ce que nous lançons, quand, et pourquoi nous filmons tout. |
| Lien suivi | `?utm_source=email&utm_medium=email&utm_campaign=liste-attente-2026&utm_content=BV1` |

> Bonjour {{ contact.PRENOM | default: "" }},
>
> Merci de votre inscription. Vous serez parmi les premiers prévenus quand les commandes ouvriront, avec les dates d'expédition et de livraison écrites.
>
> Canapoil part d'un constat simple : chez nous, le chat dort sur le canapé, et le canapé garde ses poils. Nous avons donc cherché des outils simples pour partager le canapé avec un chat ou un chien et garder un intérieur présentable.
>
> Notre premier produit est un **rouleau anti-poils réutilisable** : quelques allers-retours sur le tissu, les poils finissent dans un réservoir que l'on vide au-dessus de la poubelle. Sans feuille adhésive, sans recharge, sans pile.
>
> Trois engagements, dès le premier jour :
> - **Tout est filmé** sur de vrais tissus, y compris là où le rouleau marche mal (cuir, soie, tapis à poils longs).
> - **Expédition depuis la France**, avec un délai écrit avant le paiement : en précommande, une date d'expédition et une date limite de livraison ; ensuite, livraison en point relais 3 à 6 jours ouvrés après la commande.
> - **30 jours pour changer d'avis** après réception : les 14 jours prévus par la loi, plus 16 jours que nous ajoutons.
>
> Une question pour mieux vous servir : **en quoi est votre canapé ?** Velours, microfibre, lin, cuir ? Répondez simplement à cet e-mail : nous lisons toutes les réponses, et les tissus les plus cités seront testés en vidéo en premier.
>
> À très vite,
> {prénom du fondateur}, fondateur de Canapoil
>
> P.-S. Nos produits sont fabriqués en Chine. Nous les choisissons sur échantillon, nous les contrôlons et nous les expédions depuis la France.

### BV2 — J+3

| Champ | Contenu |
|---|---|
| Objet | 5 tissus, 1 rouleau, aucune coupe |
| Pré-en-tête | Le test complet, y compris là où il échoue. |
| Lien suivi | `utm_content=BV2` |

> Bonjour {{ contact.PRENOM | default: "" }},
>
> Avant de vous proposer quoi que ce soit, voici ce que le rouleau donne sur cinq tissus courants : velours, microfibre, lin, plaid polaire et siège auto en tissu.
>
> **[Voir le test sur 5 tissus]** (vidéo de 60 secondes)
>
> Ce que la vidéo montre :
> - le même geste sur chaque tissu, filmé en un seul plan ;
> - le nombre d'allers-retours nécessaires, tissu par tissu ;
> - les trois cas où nous déconseillons le rouleau : **cuir et simili-cuir, soie et tissus délicats, tapis à poils longs**. Pour les tapis ras et la voiture, nous avons une raclette en caoutchouc, présentée au lancement.
>
> Votre tissu n'est pas dans la liste ? Envoyez-nous une photo en réponse à cet e-mail. Nous vous dirons honnêtement si le rouleau convient.
>
> {prénom du fondateur}

### BV3 — J+7

| Champ | Contenu |
|---|---|
| Objet | Comment se passera le lancement |
| Pré-en-tête | Dates, prix, livraison : tout est écrit ici. |
| Lien suivi | `utm_content=BV3` |
| Condition | Si l'inscription a lieu après l'ouverture des précommandes, BV3 est remplacé par C1 |

> Bonjour {{ contact.PRENOM | default: "" }},
>
> Voici comment se déroulera l'ouverture, pour que rien ne vous surprenne.
>
> **1. Le jour J, vous recevez un e-mail.** Les commandes ouvrent d'abord en précommande : la date d'expédition et la date de livraison au plus tard sont écrites sur la page produit avant le paiement.
>
> **2. Les prix sont fixés dès maintenant et ne changeront pas pendant le lancement.**
> - Rouleau anti-poils réutilisable : 24,90 €
> - Kit anti-poils (rouleau + gant de toilettage) : 29,90 €
> - **Grand kit** (rouleau + raclette tapis et voiture + gant) : 39,90 €, livraison offerte, soit 7,80 € de moins que les trois produits achetés séparément
> - Duo maison + voiture (2 rouleaux) : 39,90 €, livraison offerte
>
> **3. Les 30 premières précommandes reçoivent le gant de toilettage en silicone offert.** Il n'y a pas d'autre offre : nos prix sont trop récents pour annoncer une réduction honnête.
>
> **4. Livraison et retours.** Point relais à 3,90 €, offert dès 35 € d'achat. Expédition depuis la France. 30 jours après réception pour changer d'avis.
>
> Si vous avez une question avant l'ouverture, répondez à cet e-mail.
>
> {prénom du fondateur}

**Variante « phase de vente »** (inscription à la lettre d'information après le lancement) : même structure ; BV3 devient « Quel kit pour votre intérieur ? », avec un tableau des kits par surface (canapé seul → rouleau ou Kit anti-poils ; canapé + tapis + voiture → Grand kit ; deux pièces ou maison + voiture → Duo ; chat d'appartement en hiver → Kit chat d'hiver jusqu'au 28/02/2027) et aucune mention de prime.

---

## 3. Flux panier abandonné (avec consentement uniquement) — SUSPENDU

**Aucun de ces e-mails ne part au lancement** : la case de consentement du panier et le webhook `checkout.session.expired` ne sont pas développés sur le site statique (revue red team M10). Les textes sont conservés pour la bascule Shopify (relances natives réservées aux abonnés marketing) ou pour un développement ultérieur.

Arrêt du flux dès qu'un paiement est enregistré pour la même adresse. Aucune remise, aucun code promotionnel (`allow_promotion_codes` laissé à `false`).

### PA1 — H+1 (expiration de la session)

| Champ | Contenu |
|---|---|
| Objet | Votre panier Canapoil est resté ouvert |
| Pré-en-tête | Le lien ci-dessous le reprend exactement là où vous l'avez laissé. |
| Lien | `{{ params.URL_REPRISE }}` (URL de reprise Stripe, valable 30 jours) |

> Bonjour,
>
> Vous avez demandé un rappel si votre commande n'était pas terminée. La voici :
>
> {{ params.ARTICLES }} — {{ params.MONTANT }} € TTC
>
> **[Reprendre ma commande]**
>
> Pour mémoire :
> - {% if precommande %}expédition à partir du {{ params.DATE_EXPEDITION }}, livraison au plus tard le {{ params.DATE_LIVRAISON_MAX }} ;{% else %}livraison en point relais 3 à 6 jours ouvrés après la commande ;{% endif %}
> - livraison offerte dès 35 € d'achat ;
> - 30 jours après réception pour changer d'avis.
>
> Un souci pendant le paiement ? Répondez à cet e-mail, nous vous aidons.
>
> L'équipe Canapoil

### PA2 — H+24

| Champ | Contenu |
|---|---|
| Objet | Est-ce que ça marchera sur votre tissu ? |
| Pré-en-tête | La réponse en vidéo, et une photo suffit si vous hésitez. |
| Lien | Vidéo du test sur 5 tissus + `{{ params.URL_REPRISE }}` |

> Bonjour,
>
> La question qu'on nous pose le plus avant d'acheter : « Est-ce que ça marchera sur mon canapé ? »
>
> - **Velours, microfibre, plaid, lin, couette, arbre à chat, siège auto en tissu** : oui, la vidéo montre le résultat sur chacun. **[Voir le test]**
> - **Cuir, soie, tissus très lisses, tapis à poils longs** : le rouleau est peu efficace. Pour les tapis ras et la moquette de voiture, la raclette du Grand kit prend le relais.
>
> En cas de doute, envoyez une photo de votre tissu en réponse à cet e-mail. Si le rouleau ne convient pas, nous vous le dirons.
>
> **[Reprendre ma commande]**
>
> L'équipe Canapoil

### PA3 — H+72 (dernier message)

| Champ | Contenu |
|---|---|
| Objet | Dernier rappel pour votre panier |
| Pré-en-tête | Ensuite, nous ne vous écrirons plus à ce sujet. |
| Lien | `{{ params.URL_REPRISE }}` |

> Bonjour,
>
> C'est notre dernier message au sujet de votre panier : {{ params.ARTICLES }}.
>
> {% if saison_noel %}Pour une livraison avant le 24 décembre, la dernière date de commande est le **{{ params.DATE_LIMITE_NOEL }}**.{% endif %}
>
> Si vous changez d'avis après réception, vous avez 30 jours pour nous retourner le produit. Si le produit est défectueux, nous le remplaçons ou le remboursons sur simple photo.
>
> **[Reprendre ma commande]** (lien valable jusqu'au {{ params.DATE_FIN_REPRISE }})
>
> Merci d'avoir regardé Canapoil.
> L'équipe Canapoil

---

## 4. Flux post-achat

### PO1 — Confirmation de commande (J0, transactionnel)

| Champ | Contenu |
|---|---|
| Objet | Commande {{ params.NUMERO_COMMANDE }} confirmée |
| Pré-en-tête | Récapitulatif, date d'expédition et vos droits. |
| Déclencheur | `checkout.session.completed` |
| Remarque | Le reçu Stripe part aussi ; PO1 porte les informations contractuelles. **Au lancement, PO1 est envoyé par la fonction `stripe-webhook` du site** (texte codé dans `site/netlify/lib/coeur.js`, dates de précommande lues dans les métadonnées de la session) ; ce modèle sert après la bascule Shopify |

> Bonjour {{ params.PRENOM }},
>
> Merci pour votre commande. Voici le récapitulatif.
>
> **Commande** {{ params.NUMERO_COMMANDE }} du {{ params.DATE_COMMANDE }}
> {{ params.LIGNES }} (article, quantité, prix TTC)
> Livraison : {{ params.FRAIS_PORT }}
> **Total payé : {{ params.TOTAL }} € TTC**
>
> **Livraison** : point relais {{ params.POINT_RELAIS }}.
> {% if precommande %}Précommande : **expédition à partir du {{ params.DATE_EXPEDITION }}, livraison au plus tard le {{ params.DATE_LIVRAISON_MAX }}**. Si cette date ne peut pas être tenue, nous vous écrivons avant et vous pourrez annuler avec remboursement intégral.{% else %}Expédition sous 1 jour ouvré depuis la France, livraison en 3 à 6 jours ouvrés.{% endif %}
>
> **Vos droits**
> - 30 jours après réception pour changer d'avis (14 jours prévus par la loi + 16 jours ajoutés par Canapoil). Frais de retour à votre charge, sauf produit défectueux ou erroné.
> - Pour renoncer à votre commande : **[Renoncer au contrat ici]**.
> - Garantie légale de conformité de 2 ans et garantie des vices cachés : détails dans nos **[conditions générales de vente]** (version du {{ params.VERSION_CGV }}, jointe en PDF).
>
> Une question ? Répondez à cet e-mail.
>
> L'équipe Canapoil

### PO2 — Votre colis est parti (à l'expédition)

| Champ | Contenu |
|---|---|
| Objet | Votre colis Canapoil est en route |
| Pré-en-tête | Suivi, et 30 secondes de mode d'emploi pour bien démarrer. |
| Déclencheur | Attribut `DATE_EXPEDITION` renseigné |
| Lien suivi | `utm_content=PO2` |

> Bonjour {{ params.PRENOM }},
>
> Votre colis a été déposé aujourd'hui en point relais. Suivi : **[{{ params.NUMERO_SUIVI }}]**. Livraison prévue entre le {{ params.DATE_MIN }} et le {{ params.DATE_MAX }}.
>
> **En attendant, le mode d'emploi en 30 secondes** : **[Voir la vidéo]**
> 1. Posez le rouleau sur le tissu.
> 2. Faites des allers-retours courts en appuyant légèrement.
> 3. Ouvrez le réservoir au-dessus de la poubelle.
> 4. Essuyez la bande avec un chiffon sec et rangez le rouleau à l'abri de la chaleur.
>
> Deux précautions : ne l'utilisez pas directement sur votre animal, et testez d'abord une zone cachée sur les tissus fragiles.
>
> Pour renoncer à votre commande : **[Renoncer au contrat ici]**.
>
> L'équipe Canapoil

### PO3 — Une semaine sur le canapé (J+7 après livraison)

| Champ | Contenu |
|---|---|
| Objet | Une semaine avec votre rouleau : tout va bien ? |
| Pré-en-tête | Trois réglages qui changent le résultat, et notre réponse si ce n'est pas le cas. |
| Déclencheur | Livraison estimée + 7 jours |
| Segments | A : a acheté le rouleau sans la raclette et ne s'est pas opposé aux offres → bloc raclette. B : a acheté le Grand kit → bloc « tapis thermique » d'octobre à février, sinon aucun bloc produit. C : s'est opposé → aucun bloc produit |
| Lien suivi | `utm_content=PO3` |

> Bonjour {{ params.PRENOM }},
>
> Votre rouleau est arrivé il y a une semaine environ. Trois réglages font la différence :
>
> - **Des allers-retours courts** donnent un meilleur résultat qu'un long passage.
> - **Videz le réservoir après chaque usage** : la bande attrape mieux quand il n'est pas plein.
> - **Passez-le souvent** : deux minutes deux fois par semaine demandent moins d'effort qu'une séance par mois.
>
> **Le résultat ne vous convient pas ?** Répondez à cet e-mail avec une photo de votre tissu. Nous vous donnons un conseil d'usage ; si le rouleau ne convient vraiment pas, vous avez jusqu'au {{ params.DATE_FIN_RETOUR }} pour le retourner.
>
> {% if segment_A %}**Pour les tapis et la voiture.** Le rouleau glisse sur les tapis et la moquette. Notre raclette en caoutchouc décolle les poils incrustés dans les tapis ras, la moquette du coffre et les sièges en tissu : on la tire vers soi, les poils se regroupent en boule. 12,90 €. **[Voir la raclette]**{% endif %}
> {% if segment_B_hiver %}**Pour le rebord de fenêtre.** Si votre chat passe l'hiver près de la fenêtre, notre tapis de fenêtre (24,90 €, sans fil ni prise) lui fait un couchage moelleux. Vendu jusqu'à fin février. **[Voir le tapis]**{% endif %}
>
> Pour renoncer à votre commande : **[Renoncer au contrat ici]**.
>
> {prénom du fondateur}

---

## 5. Demande d'avis

### AV1 — J+10 après livraison

| Champ | Contenu |
|---|---|
| Objet | Votre avis sur le rouleau, en 2 minutes |
| Pré-en-tête | Bon ou mauvais, il sera publié. |
| Déclencheur | Livraison estimée + 10 jours ; pas d'envoi si une réclamation est ouverte |
| Formulaire | Formulaire hébergé dans l'UE (par exemple Tally), pré-rempli avec le numéro de commande ; champs : note sur 5, titre, texte, tissu ou surface, animal, date d'utilisation, photo facultative, accord de publication |
| Lien suivi | `utm_content=AV1` |

> Bonjour {{ params.PRENOM }},
>
> Vous utilisez votre rouleau Canapoil depuis une dizaine de jours. Pourriez-vous nous dire ce que vous en pensez ? Cela prend deux minutes.
>
> **[Donner mon avis]**
>
> Ce que nous faisons de votre avis :
> - **il est publié, qu'il soit positif ou négatif**, avec sa date et le type de tissu, sur la page du produit ;
> - il n'est ni modifié ni trié : les avis s'affichent du plus récent au plus ancien ;
> - nous ne donnons aucune contrepartie pour un avis.
>
> Les avis sont réservés aux clients ayant passé commande : nous vérifions chaque avis grâce au numéro de commande.
>
> Merci,
> {prénom du fondateur}

**Texte à afficher sous le bloc d'avis du site** (03 §1.8) : « Avis collectés auprès de clients ayant passé commande, vérifiés par rapprochement avec le numéro de commande. Tous les avis sont publiés, positifs comme négatifs, du plus récent au plus ancien. Un avis est refusé uniquement s'il est injurieux, s'il contient des données personnelles ou s'il ne porte pas sur le produit. Aucune contrepartie n'est accordée. »

---

## 6. Réactivation

### RE1 — 75 jours sans nouvelle commande (clients)

| Champ | Contenu |
|---|---|
| Objet | Votre rouleau tient le coup ? |
| Pré-en-tête | Une question, et ce qui est nouveau chez Canapoil cette saison. |
| Destinataires | Clients du site sans opposition, dernière commande il y a 75 jours, aucune commande depuis |
| Base | Exception « client » pour des produits analogues (L34-5 CPCE) |
| Lien suivi | `utm_content=RE1` |

> Bonjour {{ contact.PRENOM }},
>
> Votre commande Canapoil date de deux mois et demi. Une question rapide : **votre rouleau fonctionne-t-il toujours comme au premier jour ?** Si la bande attrape moins bien, répondez à cet e-mail : nous vous expliquons comment la nettoyer, et si le produit est défectueux, il est couvert par la garantie légale de conformité de 2 ans.
>
> **Ce qui est nouveau cette saison**
> {% if mois in [10,11,12,1,2] %}- **Kit chat d'hiver** : un rouleau + un tapis de fenêtre sans fil ni prise, 44,90 €, livraison offerte, disponible jusqu'au 28/02/2027.{% endif %}
> {% if mois in [2,3,4,5] %}- **Période de mue** : notre vidéo « brosser son chat au gant en 2 minutes » et le gant de toilettage à 9,90 €.{% endif %}
> - **Duo maison + voiture** : un second rouleau pour la chambre ou la voiture, 39,90 € les deux, livraison offerte.
>
> **[Voir les nouveautés]**
>
> Si vous ne souhaitez plus recevoir nos e-mails, un clic suffit en bas de ce message.
>
> {prénom du fondateur}

**Variante RE2 — inscrits sans achat, 6 mois sans clic** (gestion des inactifs, CNIL question 7) : objet « On continue ensemble ? » ; corps de 3 lignes : « Vous êtes inscrit à la lettre Canapoil depuis le {date}. Si vous souhaitez continuer à recevoir nos tests et nouveautés, cliquez ici : [Je reste inscrit]. Sans clic de votre part d'ici 15 jours, nous retirerons votre adresse de notre liste. » Les adresses sans clic sont supprimées.

---

## 7. Annexe : campagnes d'ouverture des précommandes

### C1 — Jour d'ouverture (envoyé sur 2 jours si la liste dépasse 300 adresses)

| Champ | Contenu |
|---|---|
| Objet | C'est ouvert : les précommandes Canapoil commencent |
| Pré-en-tête | Dates d'expédition écrites, gant offert aux 30 premières précommandes (30 gants réservés). |
| Lien suivi | `utm_campaign=precommande-2026&utm_content=C1` |

> Bonjour {{ contact.PRENOM | default: "" }},
>
> Vous avez demandé à être prévenu : les précommandes sont ouvertes.
>
> - **Expédition à partir du {{ params.DATE_EXPEDITION }}**, depuis la France ; **livraison au plus tard le {{ params.DATE_LIVRAISON_MAX }}**.
> - **Le gant de toilettage est offert aux 30 premières précommandes**, dans la limite des 30 gants réservés à cette offre.
> - Rouleau 24,90 € · Kit anti-poils 29,90 € · **Grand kit 39,90 €, livraison offerte** · Duo 39,90 €, livraison offerte.
> - 30 jours après réception pour changer d'avis.
>
> **[Précommander]**
>
> Merci d'avoir suivi le projet depuis le début.
> {prénom du fondateur}

### C2 — Rappel des dates (J+6 de l'ouverture)

| Champ | Contenu |
|---|---|
| Objet | Précommandes : les dates, et ce qu'il reste du stock commandé |
| Pré-en-tête | Expédition à partir du {{ params.DATE_EXPEDITION }}, livraison au plus tard le {{ params.DATE_LIVRAISON_MAX }}. |
| Destinataires | Inscrits n'ayant pas commandé (consentement enregistré) |
| Règle | Aucune fausse urgence : la précommande reste ouverte aux mêmes dates tant que le stock commandé le permet ; l'e-mail ne parle de fin que si une date de fin réelle est fixée |

> Bonjour {{ contact.PRENOM | default: "" }},
>
> Les précommandes sont ouvertes depuis 6 jours : expédition depuis la France à partir du {{ params.DATE_EXPEDITION }}, livraison au plus tard le {{ params.DATE_LIVRAISON_MAX }}. Le stock est commandé et en route ; quand il sera épuisé, la fiche affichera la date du réassort suivant.
>
> {% if primes_restantes > 0 %}Le gant offert aux 30 premières précommandes est encore disponible : il en reste {{ params.PRIMES_RESTANTES }} (décompte réel).{% else %}Les 30 gants offerts ont tous été attribués.{% endif %}
>
> **[Précommander]**
>
> {prénom du fondateur}

---

## 8. Indicateurs

| Indicateur | Mesure (sans pixel individuel) | Cible palier 0 | Source de la cible |
|---|---|---|---|
| Confirmation du double opt-in | Confirmés ÷ formulaires envoyés | ≥ 60 % | Estimation, confiance faible |
| Visites issues des e-mails | Visites `utm_source=email` ÷ e-mails délivrés | ≥ 4 % | Estimation, confiance faible |
| Conversion liste d'attente → précommande | Précommandes d'inscrits ÷ inscrits confirmés | ≥ 10 % | Estimation, confiance faible |
| Récupération des paniers | Commandes avec `recovered_from` ÷ sessions expirées avec consentement | ≥ 5 % | Estimation, confiance faible |
| Taux d'avis | Avis reçus ÷ AV1 envoyés | ≥ 10 % | Estimation, confiance faible |
| Désinscriptions | Désinscrits ÷ e-mails délivrés, par envoi | < 0,5 % | Estimation, confiance moyenne |
| Part de l'e-mail dans le CA du site | CA attribué par UTM ÷ CA du site | 5-12 % les 90 premiers jours | 02 §6.2, estimation, confiance faible |
