# Images du site : convention de nommage et remplacement par de vraies photos

Aucune photo réelle n'existe au 12/10/2026. Toutes les images du site sont des **illustrations SVG provisoires**, dessinées aux couleurs de la marque par `outils/illustrations.py`. Chaque fiche produit l'indique (pastille « Illustration » et phrase sous la galerie). Ces mentions disparaissent automatiquement dès qu'une vraie photo remplace toutes les illustrations d'une fiche.

## Arborescence

| Dossier | Contenu | Format affiché |
|---|---|---|
| `produits/<slug-produit>/` | Galerie de la fiche produit, dans l'ordre des numéros | 4:3 (800 × 600 minimum, 1600 × 1200 conseillé) |
| `kits/<slug-kit>/` | Image du kit | 4:3 |
| `illustrations/` | Accueil (`accueil-canape.svg`, 960 × 720) et étapes « Comment ça marche » (`etape-1.svg` à `etape-3.svg`, 400 × 300) | 4:3 |
| `og/` | Images de partage (Open Graph), 1200 × 630, PNG | 1,91:1 |
| `produits/<slug>/principale.png`, `kits/<slug>/principale.png` | Image produit en PNG 1200 × 900, utilisée par Stripe (page de paiement), le JSON-LD Product, le flux Google Merchant et le CSV Shopify | 4:3 |

Slugs actuels : `rouleau-anti-poils-reutilisable`, `gant-toilettage-silicone`, `raclette-anti-poils-tapis-voiture`, `tapis-fenetre-thermique-chat` ; kits : `grand-kit`, `kit-anti-poils`, `duo-maison-voiture`, `kit-chat-hiver`.

## Emplacements de la galerie

| Fichier | Rouleau | Gant | Raclette | Tapis de fenêtre |
|---|---|---|---|---|
| `01-principale` | Produit seul, fond clair | Produit seul | Produit seul | Tapis sur un rebord, chat dessus |
| `02-…` | `02-usage` : sur un canapé en tissu | `02-usage` : brossage d'un chat | `02-usage` : sur un tapis ras | `02-couches` : coupe des 3 couches |
| `03-reservoir` | Réservoir ouvert au-dessus de la poubelle | — | — | — |
| `04-colis` | Contenu du colis (rouleau + notice) | — | — | — |
| `05-dimensions` | Produit avec cotes mesurées | — | — | — |

Vous pouvez ajouter des emplacements (par exemple `06-velours`, `07-siege-auto`) : il suffit de les déclarer dans `PLANCHES_PRODUITS` de `outils/illustrations.py` ou de déposer le fichier et d'ajouter l'emplacement au même endroit.

## Remplacer une illustration par une photo

1. Prenez la photo avec le **produit réel reçu** (jamais une photo du fournisseur ou d'un tiers sans licence écrite, règle de `brand.json`).
2. Recadrez en **4:3**, 1600 × 1200 px, exportez en **WebP** (qualité 80) ou JPEG ; visez moins de 200 Ko.
3. Nommez le fichier exactement comme l'emplacement, avec la nouvelle extension, dans le même dossier : par exemple `produits/rouleau-anti-poils-reutilisable/01-principale.webp`. Gardez le SVG à côté : le générateur choisit automatiquement, dans cet ordre, `.webp`, `.jpg`, `.jpeg`, `.png`, puis `.svg`.
4. Relancez la génération depuis le dossier `dropshipping/` :
   ```
   python3 site/outils/generer.py
   ```
   Les pages, `data/products.json`, le flux Google et le CSV Shopify pointent alors vers la photo.
5. Pour la photo principale, remplacez aussi `principale.png` (1200 × 900) par la photo convertie en PNG, ou relancez `node site/outils/rendre_images.js` après avoir adapté le script. C'est cette image que voient Stripe, Google et Shopify.
6. Vérifiez le texte alternatif : il est repris du titre de l'illustration (`<title>` du SVG). Si la photo montre autre chose, modifiez le titre dans `outils/illustrations.py` (fonction de la planche correspondante) puis relancez la génération.

## Règles

- Le **Google Merchant Center** refuse les illustrations comme image produit : ne soumettez `flux/google-merchant.xml` qu'après avoir remplacé toutes les `principale.png` par de vraies photos.
- Aucune image retouchée pour exagérer le résultat (avant/après truqué) : pratique commerciale trompeuse.
- Les vidéos de démonstration (velours, microfibre, lin, plaid, siège auto, cuir) sont publiées sur les réseaux ; pour les intégrer au site, hébergez-les vous-même (MP4 court, sans son par défaut) afin de ne charger aucun traceur tiers sans consentement.
