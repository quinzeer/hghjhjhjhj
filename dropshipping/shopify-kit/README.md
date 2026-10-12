# Kit d'import Shopify Canapoil

Tout ce qu'il faut pour passer du site statique (`site/`) à Shopify en une journée, le jour où une condition de bascule de la stratégie est remplie. Les fichiers sont **générés** depuis `strategie/brand.json` par `python3 site/outils/generer.py` : ne les modifiez pas à la main, modifiez la source puis régénérez.

| Fichier | Contenu | Utilisation |
|---|---|---|
| `products.csv` | 4 produits + 4 kits, au format d'import Shopify actuel : en-têtes identiques au modèle officiel [`product_template.csv`](https://help.shopify.com/csv/product_template.csv) téléchargé le 12/10/2026 (61 colonnes). Prix TTC, aucun prix barré, coût de revient, poids, stock initial du micro-stock, catégories de la taxonomie Shopify et Google, SEO, bloc GPSR dans la description | Produits > Importer |
| `redirections.csv` | Redirections 301 des URL du site statique vers les URL Shopify | Navigation > Redirections d'URL > Importer |
| `pages/politique-*.html` | CGV, retours et rétractation (avec formulaire type), livraison, confidentialité, mentions légales, adaptées à Shopify (Shopify Payments, PayPal, Judge.me, Shopify Messaging) | Paramètres > Politiques |
| `pages/page-*.html` | Cookies, FAQ, À propos, Contact, Rétractation en ligne | Boutique en ligne > Pages |
| `theme/sections/canapoil-retractation.liquid` | Fonctionnalité « renoncer au contrat ici » → « confirmer la rétractation » → accusé horodaté par e-mail (via la fonction serveur gratuite du site statique) | Modifier le code du thème |
| `theme/snippets/canapoil-case-cgv.liquid` | Case d'acceptation des CGV, non pré-cochée, qui bloque le passage au paiement tant qu'elle n'est pas cochée | Modifier le code du thème (panier) |
| `theme.md` | Thème gratuit Horizon : couleurs, polices, réglages, structure de la page produit et de l'accueil, métachamps GPSR | Personnaliser le thème |
| `apps.md` | Applications nécessaires, coûts réels relevés le 12/10/2026, alternatives gratuites, applications interdites | App Store |
| `checklist-mise-en-ligne.md` | Procédure pas à pas, coût de chaque étape, tests avant ouverture | Le jour de la bascule |

## Choix structurants

| Choix | Raison |
|---|---|
| Kits importés comme produits distincts | Fonctionne sans application ; l'application gratuite Shopify Bundles peut ensuite synchroniser le stock des composants |
| Images en PNG depuis `https://canapoil.fr/images/...` | Shopify n'accepte pas les SVG comme images produit ; le site statique doit rester en ligne pendant l'import |
| Bloc GPSR dans la description | Information affichée dès l'import, sans réglage du thème ; métachamps décrits dans `theme.md` §6 pour une présentation en onglet |
| `Compare-at price` vide partout | Aucun prix barré pendant les 30 premiers jours, puis seulement avec le prix le plus bas réellement pratiqué sur 30 jours (L112-1-1) |
| `Google Shopping / Custom product` = TRUE | Produits sans code GTIN |

## Variables à remplacer

Mêmes variables que le site (liste et pages concernées dans `site/README.md` §7), plus trois propres à Shopify :

| Variable | Fichier | À remplacer par |
|---|---|---|
| `{{HEBERGEUR}}` | `pages/politique-mentions-legales.html` | Shopify International Limited, adresse et téléphone recopiés depuis les conditions Shopify en vigueur |
| `{{LOCALISATION_JUDGEME}}` | `pages/politique-confidentialite.html` | Pays d'établissement de Judge.me et garanties de transfert, d'après sa politique de confidentialité |
| `{{DUREE_A_VERIFIER}}` | `pages/page-cookies.html` | Durées réelles des cookies Shopify, relevées avec le scanner de l'application de consentement |

Occurrences dans le kit au 12/10/2026 : `{{EMAIL}}` 36, `{{RAISON_SOCIALE}}` 32, `{{ADRESSE}}` 25, `{{TELEPHONE}}` 8, `{{MEDIATEUR}}` 5, `{{HORAIRES_SERVICE_CLIENT}}` 5, `{{FABRICANT_ROULEAU}}` 5, `{{ADRESSE_RETOUR}}` 5, `{{RCS}}`, `{{FORME_JURIDIQUE}}`, `{{CAPITAL}}`, `{{FABRICANT_GANT}}`, `{{DUREE_A_VERIFIER}}` 3 chacune, `{{TVA_INTRACOM}}`, `{{SIREN}}`, `{{IDU_EMBALLAGES}}`, `{{FABRICANT_TAPIS}}`, `{{FABRICANT_RACLETTE}}` 2 chacune, `{{LOCALISATION_JUDGEME}}`, `{{HEBERGEUR}}`, `{{DIRECTEUR_PUBLICATION}}` 1 chacune. Avant publication, une recherche de « {{ » dans chaque page et politique doit revenir vide (checklist, test 8.9).
