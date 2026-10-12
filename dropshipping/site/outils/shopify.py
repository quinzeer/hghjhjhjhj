"""Kit d'import Shopify généré depuis brand.json (appelé par generer.py).

- shopify-kit/products.csv : en-têtes du modèle officiel Shopify
  (https://help.shopify.com/csv/product_template.csv, téléchargé le 12/10/2026) ;
- shopify-kit/pages/*.html : contenus prêts à coller (politiques et pages).
"""

import csv
import html
import io
import re
from pathlib import Path

import markdown_mini as MD

EN_TETES = (
    "Title,URL handle,Description,Vendor,Product category,Type,Tags,Published on online store,Status,SKU,"
    "Variant Barcodes,Option1 name,Option1 value,Option1 Linked To,Option2 name,Option2 value,Option2 Linked To,"
    "Option3 name,Option3 value,Option3 Linked To,Price,Compare-at price,Cost per item,Charge tax,Tax code,"
    "Unit price total measure,Unit price total measure unit,Unit price base measure,Unit price base measure unit,"
    "Inventory tracker,Inventory quantity,Continue selling when out of stock,Weight value (grams),Weight unit for display,"
    "Requires shipping,Fulfillment service,Product image URL,Image position,Image alt text,Variant image URL,Gift card,"
    "SEO title,SEO description,Color (product.metafields.shopify.color-pattern),Google Shopping / Google product category,"
    "Google Shopping / Gender,Google Shopping / Age group,Google Shopping / Manufacturer part number (MPN),"
    "Google Shopping / Ad group name,Google Shopping / Ads labels,Google Shopping / Condition,Google Shopping / Custom product,"
    "Google Shopping / Custom label 0,Google Shopping / Custom label 1,Google Shopping / Custom label 2,"
    "Google Shopping / Custom label 3,Google Shopping / Custom label 4,Packed product length,Packed product width,"
    "Packed product height,Packed product dimension unit"
).split(",")

TAXONOMIE_SHOPIFY = {
    "rouleau-anti-poils": "Home & Garden > Household Supplies > Laundry Supplies > Lint Rollers",
    "gant-toilettage": "Animals & Pet Supplies > Pet Supplies > Pet Grooming Supplies > Pet Combs & Brushes > Gloves",
    "raclette-anti-poils": "Home & Garden > Household Supplies > Household Cleaning Supplies > Squeegees",
    "tapis-fenetre-thermique": "Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Furniture > Cat Window Beds & Perches",
}
TAXONOMIE_GOOGLE = {
    "rouleau-anti-poils": "Home & Garden > Household Supplies > Laundry Supplies > Lint Rollers",
    "gant-toilettage": "Animals & Pet Supplies > Pet Supplies > Pet Grooming Supplies > Pet Combs & Brushes",
    "raclette-anti-poils": "Home & Garden > Household Supplies > Household Cleaning Supplies > Squeegees",
    "tapis-fenetre-thermique": "Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Beds",
}
TYPES = {
    "rouleau-anti-poils": "Rouleau anti-poils",
    "gant-toilettage": "Gant de toilettage",
    "raclette-anti-poils": "Raclette anti-poils",
    "tapis-fenetre-thermique": "Couchage pour chat",
}
TAGS = {
    "rouleau-anti-poils": "anti-poils, rouleau, chat, chien, canape, heros",
    "gant-toilettage": "anti-poils, gant, toilettage, chat, chien",
    "raclette-anti-poils": "anti-poils, raclette, tapis, voiture, chien, chat",
    "tapis-fenetre-thermique": "chat, hiver, fenetre, couchage, saisonnier",
}
SEO = {
    "rouleau-anti-poils": ("Rouleau anti-poils réutilisable chat et chien | Canapoil",
                           "Rouleau anti-poils réutilisable : sans adhésif ni recharge, se vide en un geste. Expédié depuis la France, livré en 3 à 6 jours ouvrés."),
    "gant-toilettage": ("Gant de toilettage silicone chat et chien | Canapoil",
                        "Gant de toilettage en silicone : récupère une partie des poils morts au brossage. Expédié depuis la France en 3 à 6 jours ouvrés."),
    "raclette-anti-poils": ("Raclette anti-poils tapis et voiture | Canapoil",
                            "Raclette anti-poils : décolle les poils incrustés dans les tapis ras, la moquette et la voiture. Expédiée depuis la France."),
    "tapis-fenetre-thermique": ("Tapis de fenêtre thermique pour chat | Canapoil",
                                "Couchage sherpa pour rebord de fenêtre, couche réfléchissante, sans fil ni prise. Vendu d'octobre à février."),
}

e = lambda s: html.escape(str(s), quote=True).replace("&#x27;", "'")  # noqa: E731  (attributs entre guillemets doubles)


def prix(v):
    return f"{v:.2f}"


def gpsr_html(p):
    av = "".join(f"<li>{e(a)}</li>" for a in p["gpsr"]["avertissements"])
    return (
        f"<h3>Informations de sécurité du produit : {e(p['nom'])}</h3>"
        "<p>Règlement (UE) 2023/988 relatif à la sécurité générale des produits.</p>"
        f"<p><strong>Fabricant :</strong> {e(p['gpsr']['fabricant'])}<br>"
        f"<strong>Personne responsable dans l'UE :</strong> {e(p['gpsr']['responsable_ue'])}<br>"
        f"<strong>Identification :</strong> {e(p['gpsr']['identification'])}</p>"
        f"<p><strong>Avertissements :</strong></p><ul>{av}</ul>"
        f"<p><strong>Mode d'emploi :</strong> {e(p['gpsr']['instructions'])}</p>"
    )


def bloc_livraison(livraison_offerte):
    frais = "Livraison offerte." if livraison_offerte else "Livraison 3,90 € en point relais, offerte dès 35 € d'achat."
    return (
        "<h3>Livraison et retours</h3>"
        f"<p>Expédié sous 1 jour ouvré depuis la France, livré en point relais Mondial Relay 3 à 6 jours ouvrés après la commande (produits en stock). {frais} "
        "30 jours après réception pour changer d'avis (14 jours prévus par la loi + 16 jours offerts) ; retour à vos frais, sauf produit défectueux.</p>"
    )


def description_produit(p):
    c = p["caracteristiques"]
    lignes = ""
    for k, lib in [("matieres", "Matières"), ("dimensions", "Dimensions"), ("taille", "Taille"), ("poids", "Poids"),
                   ("alimentation", "Alimentation"), ("entretien", "Entretien"), ("origine", "Origine")]:
        if k in c:
            lignes += f"<tr><th>{lib}</th><td>{e(c[k])}</td></tr>"
    surfaces = ""
    if c.get("surfaces_conseillees"):
        surfaces = (
            "<h3>Où il marche, et où il marche moins bien</h3>"
            f"<p><strong>Meilleurs résultats :</strong> {e(', '.join(c['surfaces_conseillees']))}.</p>"
            f"<p><strong>Moins efficace :</strong> {e(', '.join(c['surfaces_deconseillees']))}.</p>"
        )
    return (
        f"<p>{e(p['description_longue'])}</p>"
        "<h3>Points forts</h3><ul>" + "".join(f"<li>{e(b)}</li>" for b in p["benefices"]) + "</ul>"
        + surfaces
        + f"<h3>Caractéristiques</h3><table><tbody>{lignes}<tr><th>Référence</th><td>{e(p['sku'])}</td></tr></tbody></table>"
        + "<h3>Contenu du colis</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in p["contenu_du_colis"]) + "</ul>"
        + bloc_livraison(False)
        + gpsr_html(p)
    )


def description_kit(k, idx):
    compo = "".join(
        f"<li>{e(idx[c['id']]['nom'])}{' × ' + str(c['quantite']) if c['quantite'] > 1 else ''} ({prix(idx[c['id']]['prix_ttc']).replace('.', ',')} € à l'unité)</li>"
        for c in k["composition"]
    )
    uniques = list(dict((c["id"], idx[c["id"]]) for c in k["composition"]).values())
    return (
        f"<p>{e(k['description'])}</p>"
        f"<h3>Contenu du kit</h3><ul>{compo}</ul>"
        f"<p><strong>{prix(k['economie_ttc']).replace('.', ',')} € de moins que les produits achetés séparément "
        f"({prix(k['prix_separes_ttc']).replace('.', ',')} €).</strong></p>"
        + bloc_livraison(k["livraison_offerte"])
        + "".join(gpsr_html(p) for p in uniques)
    )


def ligne_vide():
    return {h: "" for h in EN_TETES}


def generer_csv(brand, cat, idx, base):
    couts = {p["id"]: p["cout_produit_ht"] + p["droits_douane_estimes"] for p in brand["produits"]}
    # Stock vendable du micro-stock : les gants réservés à la prime de lancement ne sont pas en vente.
    stock = {k: v for k, v in brand["hypotheses_cles"]["micro_stock_initial"].items() if isinstance(v, int)}
    prime = brand["livraison"]["precommande"].get("prime") or {}
    if "gant-toilettage" in stock and prime.get("quantite"):
        stock["gant-toilettage"] = max(0, stock["gant-toilettage"] - int(prime["quantite"]))
    lignes = []
    for p in cat["produits"]:
        r = ligne_vide()
        titre_seo, desc_seo = SEO[p["id"]]
        r.update({
            "Title": p["nom"], "URL handle": p["slug"], "Description": description_produit(p), "Vendor": "Canapoil",
            "Product category": TAXONOMIE_SHOPIFY[p["id"]], "Type": TYPES[p["id"]], "Tags": TAGS[p["id"]],
            "Published on online store": "FALSE", "Status": "Draft", "SKU": p["sku"],
            "Option1 name": "Title", "Option1 value": "Default Title",
            "Price": prix(p["prix_ttc"]), "Cost per item": prix(couts[p["id"]]), "Charge tax": "TRUE",
            "Inventory tracker": "shopify", "Inventory quantity": str(stock.get(p["id"], 0)),
            "Continue selling when out of stock": "DENY", "Weight value (grams)": str(p["poids_g"]),
            "Weight unit for display": "g", "Requires shipping": "TRUE", "Fulfillment service": "manual",
            "Product image URL": base + p["image_produit_png"], "Image position": "1",
            "Image alt text": p["images"][0]["alt"][:125], "Gift card": "FALSE",
            "SEO title": titre_seo, "SEO description": desc_seo,
            "Google Shopping / Google product category": TAXONOMIE_GOOGLE[p["id"]],
            "Google Shopping / Manufacturer part number (MPN)": p["sku"],
            "Google Shopping / Condition": "New", "Google Shopping / Custom product": "TRUE",
            "Google Shopping / Custom label 0": "heros" if p["role"] == "heros" else "complementaire",
        })
        lignes.append(r)
        for pos, im in enumerate(p["images"][1:], start=2):
            if im["src"].endswith(".svg"):
                continue  # Shopify n'accepte pas le SVG comme image produit
            r2 = ligne_vide()
            r2.update({"URL handle": p["slug"], "Product image URL": base + im["src"], "Image position": str(pos), "Image alt text": im["alt"][:125]})
            lignes.append(r2)
    for k in cat["kits"]:
        r = ligne_vide()
        premier = k["composition"][0]["id"]
        r.update({
            "Title": k["nom"], "URL handle": k["slug"], "Description": description_kit(k, idx), "Vendor": "Canapoil",
            "Product category": TAXONOMIE_SHOPIFY[premier], "Type": "Kit", "Tags": "kit, anti-poils, chat, chien" + (", saisonnier" if k.get("saison") else ""),
            "Published on online store": "FALSE", "Status": "Draft", "SKU": k["sku"],
            "Option1 name": "Title", "Option1 value": "Default Title",
            "Price": prix(k["prix_ttc"]),
            "Cost per item": prix(sum(couts[c["id"]] * c["quantite"] for c in k["composition"])),
            "Charge tax": "TRUE", "Inventory tracker": "shopify",
            "Inventory quantity": str(min(int(stock.get(c["id"], 0)) // c["quantite"] for c in k["composition"])),
            "Continue selling when out of stock": "DENY", "Weight value (grams)": str(k["poids_g"]),
            "Weight unit for display": "g", "Requires shipping": "TRUE", "Fulfillment service": "manual",
            "Product image URL": base + k["image_produit_png"], "Image position": "1",
            "Image alt text": k["images"][0]["alt"][:125], "Gift card": "FALSE",
            "SEO title": f"{k['nom']} anti-poils | Canapoil",
            "SEO description": f"{k['description']} {prix(k['economie_ttc']).replace('.', ',')} € de moins que séparément. Expédié depuis la France."[:320],
            "Google Shopping / Google product category": TAXONOMIE_GOOGLE[premier],
            "Google Shopping / Manufacturer part number (MPN)": k["sku"],
            "Google Shopping / Condition": "New", "Google Shopping / Custom product": "TRUE",
            "Google Shopping / Custom label 0": "kit",
        })
        lignes.append(r)
    sortie = io.StringIO()
    w = csv.DictWriter(sortie, fieldnames=EN_TETES, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    w.writerows(lignes)
    return sortie.getvalue()


PAGES_SHOPIFY = [
    # (fichier source, fichier de sortie, emplacement dans Shopify)
    ("cgv", "politique-conditions-de-vente.html", "Paramètres > Politiques > Conditions d'utilisation (URL /policies/terms-of-service)"),
    ("retours-retractation", "politique-retours-retractation.html", "Paramètres > Politiques > Politique de remboursement (URL /policies/refund-policy)"),
    ("livraison", "politique-livraison.html", "Paramètres > Politiques > Politique d'expédition (URL /policies/shipping-policy)"),
    ("confidentialite", "politique-confidentialite.html", "Paramètres > Politiques > Politique de confidentialité (URL /policies/privacy-policy)"),
    ("mentions-legales", "politique-mentions-legales.html", "Paramètres > Politiques > Mentions légales (URL /policies/legal-notice)"),
    ("cookies", "page-cookies.html", "Boutique en ligne > Pages > Ajouter une page, titre « Politique cookies », adresse /pages/cookies"),
]


def generer_pages(contenus, dossier, transformer=lambda t: t):
    dossier.mkdir(parents=True, exist_ok=True)
    for src, out, ou in PAGES_SHOPIFY:
        meta, corps = MD.lire_entete(transformer((contenus / f"{src}.md").read_text(encoding="utf-8")))
        h = MD.convertir(corps, "shopify", decalage_titres=0)
        h = h.replace('<div class="tableau-wrap">', "<div>").replace(' class="code"', "").replace('<div class="formulaire-type">', "<div>")
        entete = (
            f"<!--\n  {meta['titre']} — contenu prêt à coller dans Shopify.\n  Où : {ou}.\n"
            "  Comment : ouvrir l'éditeur, cliquer sur le bouton « < > » (afficher le HTML), coller tout ce qui suit ce commentaire.\n"
            "  Avant publication : remplacer chaque variable {{...}} (liste dans shopify-kit/README.md).\n-->\n"
        )
        (dossier / out).write_text(entete + h + "\n", encoding="utf-8")


def generer_redirections(cat):
    """Redirections 301 des anciennes URL du site statique vers Shopify
    (Boutique en ligne > Navigation > Redirections d'URL > Importer)."""
    lignes = [("Redirect from", "Redirect to")]
    for it in cat["produits"] + cat["kits"]:
        lignes.append((it["url"], f"/products/{it['slug']}"))
    lignes += [
        ("/boutique/", "/collections/all"), ("/panier/", "/cart"), ("/faq/", "/pages/faq"), ("/a-propos/", "/pages/a-propos"),
        ("/contact/", "/pages/contact"), ("/retractation/", "/pages/retractation"), ("/cookies/", "/pages/cookies"),
        ("/cgv/", "/policies/terms-of-service"), ("/retours-retractation/", "/policies/refund-policy"),
        ("/livraison/", "/policies/shipping-policy"), ("/confidentialite/", "/policies/privacy-policy"),
        ("/mentions-legales/", "/policies/legal-notice"),
    ]
    sortie = io.StringIO()
    csv.writer(sortie, lineterminator="\n").writerows(lignes)
    return sortie.getvalue()


def generer(brand, cat, idx, dossier_kit, contenus, base, transformer=lambda t: t):
    """Kit Shopify. Produits et kits importés en brouillon (Status Draft, non publiés) : la boutique
    n'est publiée qu'après le remplissage de l'identité. Les kits sont suivis en stock avec la quantité
    du composant le plus rare ; installer Shopify Bundles le jour de l'import pour lier leur stock
    à celui des composants (correction M3)."""
    dossier_kit = Path(dossier_kit)
    (dossier_kit / "products.csv").write_text(transformer(generer_csv(brand, cat, idx, base)), encoding="utf-8")
    (dossier_kit / "redirections.csv").write_text(generer_redirections(cat), encoding="utf-8")
    generer_pages(contenus, dossier_kit / "pages", transformer)
    infos = contenus / "shopify"
    if infos.exists():
        for f in sorted(infos.glob("*.html")):
            (dossier_kit / "pages" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
