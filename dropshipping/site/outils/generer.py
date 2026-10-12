#!/usr/bin/env python3
"""Générateur du site Canapoil et du kit Shopify.

Source unique : strategie/brand.json. Le script produit :
- site/data/products.json (prix et contenus publics, sans coûts ni fournisseurs) ;
- les illustrations SVG provisoires (site/images/...) ;
- toutes les pages HTML statiques du site, sitemap.xml, robots.txt ;
- le flux Google Merchant (site/flux/google-merchant.xml) ;
- shopify-kit/products.csv et shopify-kit/pages/*.html ;
- le tableau des variables {{...}} dans site/README.md.

Usage : python3 site/outils/generer.py   (depuis n'importe quel dossier)
Le site déployé reste du HTML/CSS/JS statique : ce script n'est pas une étape
de build, il ne sert qu'à régénérer les fichiers quand brand.json change.
"""

import csv
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
SITE = ICI.parent
RACINE = SITE.parent
sys.path.insert(0, str(ICI))

import illustrations as ILL  # noqa: E402
import markdown_mini as MD  # noqa: E402
import shopify as SHOP  # noqa: E402

BRAND = json.loads((RACINE / "strategie" / "brand.json").read_text(encoding="utf-8"))
M = BRAND["marque"]
BASE = "https://" + M["domaine_vise"]
AUJOURDHUI = dt.date(2026, 10, 12)
ANNEE = AUJOURDHUI.year

e = lambda s: html.escape(str(s), quote=True).replace("&#x27;", "'")  # noqa: E731  (attributs entre guillemets doubles)


def euros(v):
    s = f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", "\u202f")
    if s.endswith(",00"):
        s = s[:-3]
    return s + "\u00a0€"


def ecrire(chemin, contenu, binaire=False):
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if binaire:
        chemin.write_bytes(contenu)
    else:
        chemin.write_text(contenu, encoding="utf-8")


def empreinte(chemin):
    try:
        return hashlib.sha1(Path(chemin).read_bytes()).hexdigest()[:8]
    except FileNotFoundError:
        return "0"


# ===================================================================== catalogue

NOMS_COURTS = {
    "rouleau-anti-poils": "Le rouleau",
    "gant-toilettage": "Le gant",
    "raclette-anti-poils": "La raclette",
    "tapis-fenetre-thermique": "Le tapis de fenêtre",
}
ACCROCHES = {
    "rouleau-anti-poils": "Notre produit phare",
    "gant-toilettage": "Avant le canapé",
    "raclette-anti-poils": "Tapis et voiture",
    "tapis-fenetre-thermique": "Saison d'hiver",
}
SLUG_KITS = {
    "kit-anti-poils": "kit-anti-poils",
    "grand-kit": "grand-kit",
    "duo-rouleaux": "duo-maison-voiture",
    "kit-chat-hiver": "kit-chat-hiver",
}
ORDRE_IMAGES = (".webp", ".jpg", ".jpeg", ".png", ".svg")


def resoudre_images(dossier_rel, emplacements):
    """Pour chaque emplacement (01-principale, 02-usage…), retient la vraie photo
    si elle existe (webp > jpg > png), sinon l'illustration SVG."""
    images = []
    for slot, alt in emplacements:
        trouve = None
        for ext in ORDRE_IMAGES:
            p = SITE / dossier_rel / f"{slot}{ext}"
            if p.exists():
                trouve = p
                break
        if trouve:
            images.append(
                {
                    "src": "/" + str(trouve.relative_to(SITE)).replace(os.sep, "/"),
                    "alt": alt,
                    "illustration": trouve.suffix == ".svg",
                }
            )
    return images


def titre_svg(svg):
    m = re.search(r"<title>(.*?)</title>", svg)
    return m.group(1) if m else ""


def generer_illustrations():
    """Écrit les SVG (jamais par-dessus une photo) et renvoie les alt par emplacement."""
    alts = {}
    for pid, planches in ILL.PLANCHES_PRODUITS.items():
        slug = next(p["slug"] for p in BRAND["produits"] if p["id"] == pid)
        alts[pid] = []
        for slot, fonction in planches:
            svg = fonction()
            ecrire(SITE / "images" / "produits" / slug / f"{slot}.svg", svg)
            alts[pid].append((slot, titre_svg(svg)))
    for k in BRAND["bundles"]:
        noms = " + ".join(NOMS_COURTS[p].split(" ", 1)[1] for p in k["produits"])
        t = f"{k['nom']} Canapoil : {noms}"
        svg = ILL.planche_kit(k["produits"], t)
        ecrire(SITE / "images" / "kits" / SLUG_KITS[k["id"]] / "01-principale.svg", svg)
        alts[k["id"]] = [("01-principale", t)]
    hero = ILL.planche_hero()
    ecrire(SITE / "images" / "illustrations" / "accueil-canape.svg", hero)
    alts["hero"] = titre_svg(hero)
    alts["etapes"] = []
    for n in (1, 2, 3):
        svg = ILL.etape(n)
        ecrire(SITE / "images" / "illustrations" / f"etape-{n}.svg", svg)
        alts["etapes"].append(titre_svg(svg))
    ecrire(SITE / "favicon.svg", ILL.favicon())
    return alts


def construire_catalogue(alts):
    liv = BRAND["livraison"]
    produits, kits = [], []
    for p in BRAND["produits"]:
        images = resoudre_images(f"images/produits/{p['slug']}", alts[p["id"]])
        item = {
            "id": p["id"],
            "type": "produit",
            "sku": p["sku"],
            "nom": p["nom"],
            "nom_court": NOMS_COURTS[p["id"]],
            "slug": p["slug"],
            "url": f"/produits/{p['slug']}/",
            "role": p["role"],
            "statut": p["statut"],
            "prix_ttc": p["prix_ttc"],
            "description_courte": p["description_courte"],
            "description_longue": p["description_longue"],
            "benefices": p["benefices"],
            "caracteristiques": p["caracteristiques"],
            "contenu_du_colis": p["contenu_du_colis"],
            "poids_g": p["poids_g"],
            "delai_livraison_jours": p["delai_livraison_jours"],
            "images": images,
            "image_partage": f"/images/og/{p['slug']}.png",
            "image_produit_png": f"/images/produits/{p['slug']}/principale.png",
            "gpsr": p["gpsr"],
            "faq": p["faq"],
        }
        if p.get("saison"):
            item["saison"] = {"debut_mois": 10, "fin_mois": 2, "libelle": "d'octobre à février"}
        produits.append(item)
    index = {p["id"]: p for p in produits}
    for k in BRAND["bundles"]:
        slug = SLUG_KITS[k["id"]]
        somme = round(sum(index[x]["prix_ttc"] for x in k["produits"]), 2)
        assert abs(somme - k["prix_separes_ttc"]) < 0.001, k["id"]
        assert abs(round(somme - k["prix_ttc"], 2) - k["economie_affichee_ttc"]) < 0.001, k["id"]
        composition = []
        for x in k["produits"]:
            if composition and composition[-1]["id"] == x:
                composition[-1]["quantite"] += 1
            else:
                composition.append({"id": x, "quantite": 1})
        item = {
            "id": k["id"],
            "type": "kit",
            "sku": k["sku"],
            "nom": k["nom"],
            "slug": slug,
            "url": f"/kits/{slug}/",
            "statut": k["statut"],
            "prix_ttc": k["prix_ttc"],
            "prix_separes_ttc": k["prix_separes_ttc"],
            "economie_ttc": k["economie_affichee_ttc"],
            "livraison_offerte": k["livraison_offerte"],
            "mise_en_avant": k["mise_en_avant"],
            "description": k["description"],
            "composition": composition,
            "poids_g": sum(index[x]["poids_g"] for x in k["produits"]),
            "images": resoudre_images(f"images/kits/{slug}", alts[k["id"]]),
            "image_partage": f"/images/og/{slug}.png",
            "image_produit_png": f"/images/kits/{slug}/principale.png",
        }
        if k.get("disponible_jusqu_au"):
            item["disponible_jusqu_au"] = k["disponible_jusqu_au"]
            item["saison"] = {"debut_mois": 10, "fin_mois": 2, "libelle": "d'octobre à février"}
        kits.append(item)
    # ordre d'affichage des kits : mis en avant d'abord
    kits.sort(key=lambda k: (not k["mise_en_avant"], k["statut"] == "saisonnier"))
    return {
        "version": BRAND["meta"]["version"],
        "source": "strategie/brand.json",
        "genere_le": AUJOURDHUI.isoformat(),
        "devise": "EUR",
        "prix": "TTC, en euros",
        "marque": {"nom": M["nom"], "slogan": M["slogan"], "site": BASE},
        "livraison": {
            "transporteur": liv["transporteur"],
            "zone": liv["zone"],
            "pays_autorises": ["FR"],
            "frais_ttc": liv["frais_ttc"],
            "seuil_gratuite_ttc": liv["seuil_gratuite_ttc"],
            "delai_min_jours_ouvres": liv["delai_jours"]["min"],
            "delai_max_jours_ouvres": liv["delai_jours"]["max"],
            "expedition_jours_ouvres": 1,
            "texte": liv["delai_annonce"],
        },
        "retours": {
            "delai_jours": BRAND["retours"]["delai_jours"],
            "delai_legal_jours": BRAND["retours"]["delai_legal_jours"],
            "extension_commerciale_jours": BRAND["retours"]["extension_commerciale_jours"],
        },
        "quantite_max_par_ligne": 10,
        "produits": produits,
        "kits": kits,
    }


# ===================================================================== gabarit

ICONES = {
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "camion": '<path d="M1 4h14v12H1z"/><path d="M15 8h4l4 4v4h-8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "retour": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    "cadenas": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "sac": '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "fermer": '<path d="M18 6 6 18M6 6l12 12"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "repere": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "colis": '<path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z"/><path d="M3.3 7 12 12l8.7-5M12 22V12"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
    "telephone": '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
    "courrier": '<path d="M3 21h18M5 21V8l7-5 7 5v13"/><path d="M9 21v-6h6v6"/>',
    "video": '<rect x="2" y="5" width="15" height="14" rx="2"/><path d="m17 10 5-3v10l-5-3"/>',
    "non": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
    "oui": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "etoile": '<path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "bouclier": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "oeil": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "etiquette": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><path d="M7 7h.01"/>',
    "horloge": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "bulle": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
}


def ic(nom, classe="icone"):
    return f'<svg class="{classe}" aria-hidden="true" focusable="false"><use href="#i-{nom}"/></svg>'


SPRITE = (
    '<svg class="sprite" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">'
    + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONES.items())
    + "</svg>"
)

NAV = [
    ("/boutique/", "Boutique"),
    ("/produits/rouleau-anti-poils-reutilisable/", "Le rouleau"),
    ("/kits/grand-kit/", "Grand kit"),
    ("/faq/", "Questions fréquentes"),
    ("/a-propos/", "À propos"),
]


def badges_paiement():
    return (
        '<span class="paiements" aria-label="Moyens de paiement : CB, Visa, Mastercard">'
        '<span class="paiement" aria-hidden="true">CB</span>'
        '<span class="paiement" aria-hidden="true">VISA</span>'
        '<span class="paiement" aria-hidden="true">Mastercard</span></span>'
    )


def pied_de_page():
    liens_boutique = "".join(
        f'<li><a href="{p["url"]}">{e(p["nom_court"])}</a></li>' for p in CAT["produits"]
    ) + '<li><a href="/boutique/#kits">Les kits</a></li>'
    return f"""
<footer class="pied sur-fonce">
  <div class="conteneur">
    <div class="pied__grille">
      <div>
        <a class="logo" href="/">canapoil</a>
        <p>{e(M["slogan"])}</p>
        <p>Marque française. Produits fabriqués en Chine, contrôlés et expédiés depuis la France.</p>
        <p><a class="pied__retractation" href="/retractation/">{ic("retour")}renoncer au contrat ici</a></p>
      </div>
      <nav aria-label="Boutique"><h2>Boutique</h2><ul>{liens_boutique}</ul></nav>
      <nav aria-label="Aide"><h2>Aide</h2><ul>
        <li><a href="/faq/">Questions fréquentes</a></li>
        <li><a href="/livraison/">Livraison</a></li>
        <li><a href="/retours-retractation/">Retours et rétractation</a></li>
        <li><a href="/contact/">Contact</a></li>
        <li><a href="/a-propos/">À propos</a></li>
      </ul></nav>
      <nav aria-label="Informations légales"><h2>Informations légales</h2><ul>
        <li><a href="/mentions-legales/">Mentions légales</a></li>
        <li><a href="/cgv/">Conditions générales de vente</a></li>
        <li><a href="/confidentialite/">Confidentialité</a></li>
        <li><a href="/cookies/">Cookies</a></li>
        <li><button type="button" class="btn-lien js-gerer-cookies">Gérer mes cookies</button></li>
      </ul></nav>
    </div>
    <div class="pied__bas">
      <p>Prix en euros TTC. Livraison en France métropolitaine. {badges_paiement()}</p>
      <p>Médiateur de la consommation : {{{{MEDIATEUR}}}}. Service client : {{{{EMAIL}}}}.</p>
      <p class="reseaux js-reseaux"></p>
      <p>© {ANNEE} {{{{RAISON_SOCIALE}}}} · Canapoil</p>
    </div>
  </div>
</footer>"""


TIROIR = f"""
<div class="tiroir-fond" data-fermer-panier hidden></div>
<div class="tiroir" id="tiroir-panier" role="dialog" aria-modal="true" aria-labelledby="tiroir-titre" hidden>
  <div class="tiroir__entete">
    <h2 id="tiroir-titre">Votre panier</h2>
    <button type="button" class="bouton-icone" data-fermer-panier aria-label="Fermer le panier">{ic("fermer")}</button>
  </div>
  <div class="tiroir__corps">
    <div class="progression js-progression"></div>
    <ul class="lignes js-lignes"></ul>
    <div class="js-suggestion"></div>
  </div>
  <div class="tiroir__pied">
    <div class="recap js-recap"></div>
    <a class="btn btn--primaire btn--plein btn--grand js-vers-commande" href="/commande/">Commander</a>
    <p class="centre"><a href="/panier/">Voir le panier détaillé</a></p>
  </div>
</div>
<div class="notification js-notification" role="status" aria-live="polite" hidden></div>"""

COOKIES = """
<div class="cookies" id="bandeau-cookies" role="dialog" aria-modal="false" aria-labelledby="cookies-titre" aria-describedby="cookies-texte" hidden>
  <h2 id="cookies-titre">Cookies et traceurs</h2>
  <p id="cookies-texte">Avec votre accord, nous utiliserions des traceurs de mesure d'audience et de publicité (aucun n'est actif pour l'instant). Le panier et la commande fonctionnent sans. Votre choix est conservé 6 mois et modifiable à tout moment via « Gérer mes cookies ». <a href="/cookies/">En savoir plus</a></p>
  <div class="cookies__choix js-cookies-choix" hidden>
    <label class="case"><input type="checkbox" name="mesure"> <span><strong>Mesure d'audience</strong> : statistiques de fréquentation.</span></label>
    <label class="case"><input type="checkbox" name="publicite"> <span><strong>Publicité</strong> : mesure de nos publicités sur TikTok, Meta, Pinterest, Google.</span></label>
  </div>
  <div class="cookies__boutons">
    <button type="button" class="btn btn--secondaire js-cookies-refuser">Tout refuser</button>
    <button type="button" class="btn btn--secondaire js-cookies-accepter">Tout accepter</button>
  </div>
  <p class="cookies__perso"><button type="button" class="btn-lien js-cookies-personnaliser">Personnaliser</button><button type="button" class="btn-lien js-cookies-enregistrer" hidden>Enregistrer mes choix</button></p>
</div>"""


def page(chemin_fichier, url, titre, description, corps, page_id, jsonld=None, robots="index,follow",
         og_type="website", og_image="/images/og/accueil.png", classes=""):
    canon = BASE + url
    nav = "".join(
        f'<li><a href="{h}"{" aria-current=\"page\"" if h == url else ""}>{e(t)}</a></li>' for h, t in NAV
    )
    ld = ""
    for bloc in jsonld or []:
        ld += '<script type="application/ld+json">' + json.dumps(bloc, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    v_css, v_js, v_cfg = empreinte(SITE / "assets/css/style.css"), empreinte(SITE / "assets/js/app.js"), empreinte(SITE / "assets/js/config.js")
    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titre)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Canapoil">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{e(titre)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FAF5EE">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/dm-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css?v={v_css}">
<script src="/assets/js/config.js?v={v_cfg}" defer></script>
<script src="/assets/js/app.js?v={v_js}" defer></script>
{ld}</head>
<body data-page="{page_id}"{f' class="{classes}"' if classes else ""}>
<a class="lien-evitement" href="#contenu">Aller au contenu</a>
{SPRITE}
<p class="bandeau-info"><strong>Livraison offerte dès 35 €</strong> · Expédié depuis la France<span class="large-seulement"> sous 1 jour ouvré</span></p>
<header class="entete">
  <div class="conteneur entete__barre">
    <button type="button" class="bouton-icone entete__menu js-menu" aria-expanded="false" aria-controls="nav-principale" aria-label="Ouvrir le menu">{ic("menu")}</button>
    <a class="logo" href="/" aria-label="Canapoil, retour à l'accueil">canapoil</a>
    <nav id="nav-principale" class="nav" aria-label="Navigation principale"><ul>{nav}</ul></nav>
    <a class="bouton-icone js-ouvrir-panier" href="/panier/" aria-label="Panier">{ic("sac")}<span class="pastille js-compteur" data-vide="true">0</span></a>
  </div>
</header>
<main id="contenu">
{corps}
</main>
{pied_de_page()}
{TIROIR}
{COOKIES}
</body>
</html>
"""
    ecrire(SITE / chemin_fichier, doc)
    PAGES.append({"url": url, "fichier": chemin_fichier, "robots": robots, "titre": titre, "description": description})


PAGES = []
CAT = None
IDX = {}

# ===================================================================== JSON-LD


def ld_organisation():
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Canapoil",
        "legalName": "{{RAISON_SOCIALE}}",
        "url": BASE + "/",
        "logo": BASE + "/images/og/logo.png",
        "slogan": M["slogan"],
        "email": "{{EMAIL}}",
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "email": "{{EMAIL}}",
            "availableLanguage": "French",
            "areaServed": "FR",
        },
    }


def ld_fil(elements):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(elements)
        ],
    }


def ld_offre(item):
    liv = CAT["livraison"]
    gratuite = item.get("livraison_offerte") or item["prix_ttc"] >= liv["seuil_gratuite_ttc"]
    return {
        "@type": "Offer",
        "url": BASE + item["url"],
        "priceCurrency": "EUR",
        "price": f"{item['prix_ttc']:.2f}",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "seller": {"@type": "Organization", "name": "Canapoil"},
        "shippingDetails": {
            "@type": "OfferShippingDetails",
            "shippingRate": {"@type": "MonetaryAmount", "value": "0.00" if gratuite else f"{liv['frais_ttc']:.2f}", "currency": "EUR"},
            "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "FR"},
            "deliveryTime": {
                "@type": "ShippingDeliveryTime",
                "handlingTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY"},
                "transitTime": {"@type": "QuantitativeValue", "minValue": 2, "maxValue": 5, "unitCode": "DAY"},
            },
        },
        "hasMerchantReturnPolicy": {
            "@type": "MerchantReturnPolicy",
            "applicableCountry": "FR",
            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
            "merchantReturnDays": CAT["retours"]["delai_jours"],
            "returnMethod": "https://schema.org/ReturnByMail",
            "returnFees": "https://schema.org/ReturnFeesCustomerResponsibility",
        },
    }


def ld_produit(item, description):
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": item["nom"],
        "sku": item["sku"],
        "description": description,
        "image": [BASE + item["image_produit_png"]],
        "brand": {"@type": "Brand", "name": "Canapoil"},
        "url": BASE + item["url"],
        "offers": ld_offre(item),
    }


def ld_faq(questions):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in questions
        ],
    }


# ===================================================================== blocs communs


def img(src, alt, largeur=800, hauteur=600, prioritaire=False, classe=""):
    charge = 'fetchpriority="high"' if prioritaire else 'loading="lazy"'
    c = f' class="{classe}"' if classe else ""
    return f'<img src="{src}" alt="{e(alt)}" width="{largeur}" height="{hauteur}" {charge} decoding="async"{c}>'


def bloc_prix(item, grand=False):
    cls = "prix prix--grand" if grand else "prix"
    return f'<span class="{cls}" data-prix="{item["id"]}">{euros(item["prix_ttc"])}</span>'


def ligne_livraison_item(item):
    if item.get("livraison_offerte"):
        return "Livraison offerte"
    return f"Livraison {euros(CAT['livraison']['frais_ttc'])}, offerte dès {euros(CAT['livraison']['seuil_gratuite_ttc'])}"


def carte_item(item, vedette=False):
    image = item["images"][0]
    if item["type"] == "kit":
        badge = '<span class="badge">Le plus complet</span>' if item["mise_en_avant"] else (
            '<span class="badge badge--sauge">Saison d\'hiver</span>' if item.get("saison") else ""
        )
        desc = f'{e(item["description"])}'
        eco = f'<p class="economie">{euros(item["economie_ttc"])} de moins que séparément</p>'
    else:
        badge = f'<span class="badge badge--creme">{e(ACCROCHES[item["id"]])}</span>' if item["role"] == "heros" or item.get("saison") else ""
        desc = e(item["description_courte"])
        eco = ""
    verbe = "Ajouter"
    return f"""<article class="carte{' carte--vedette' if vedette else ''}" data-item="{item['id']}">
  {badge}
  <a class="carte__visuel" href="{item['url']}" tabindex="-1" aria-hidden="true">{img(image['src'], '', 800, 600)}</a>
  <div class="carte__corps">
    <h3 class="carte__titre"><a href="{item['url']}">{e(item['nom'])}</a></h3>
    <p class="carte__desc">{desc}</p>
    {eco}
    <div class="carte__bas">
      <span>{bloc_prix(item)} <span class="mention-ttc">TTC</span></span>
      <button type="button" class="btn btn--primaire js-ajout-rapide" data-ajouter="{item['id']}" aria-label="{verbe} {e(item['nom'])} au panier">{verbe}</button>
    </div>
  </div>
</article>"""


def encart_livraison():
    return f"""<div class="encart encart--livraison js-encart-livraison">
  <p class="encart__ligne">{ic("camion")}<span><strong>Expédié sous 1 jour ouvré depuis la France.</strong> Livré en point relais en 3 à 6 jours ouvrés<span class="js-dates-livraison"></span>.</span></p>
  <p class="encart__ligne js-precommande-texte" hidden>{ic("horloge")}<span></span></p>
  <p class="encart__ligne">{ic("retour")}<span><strong>30 jours pour changer d'avis</strong> : 14 jours prévus par la loi + 16 jours offerts. Retour à vos frais, sauf produit défectueux.</span></p>
  <p class="encart__ligne">{ic("cadenas")}<span>Paiement sécurisé sur la page Stripe, nous ne voyons jamais votre carte. {badges_paiement()}</span></p>
</div>"""


def bloc_gpsr(p, titre_h="h3"):
    av = "".join(f"<li>{e(a)}</li>" for a in p["gpsr"]["avertissements"])
    return f"""<div class="gpsr" id="securite-{p['id']}">
  <{titre_h}>Informations de sécurité du produit{' : ' + e(p['nom']) if titre_h == 'h3' else ''}</{titre_h}>
  <p class="texte-2">Règlement (UE) 2023/988 relatif à la sécurité générale des produits.</p>
  <dl>
    <div><dt>Fabricant</dt><dd>{e(p['gpsr']['fabricant'])}</dd></div>
    <div><dt>Personne responsable dans l'Union européenne</dt><dd>{e(p['gpsr']['responsable_ue'])}</dd></div>
    <div><dt>Identification du produit</dt><dd>{e(p['nom'])}. {e(p['gpsr']['identification'])}</dd></div>
    <div><dt>Avertissements et consignes de sécurité</dt><dd><ul>{av}</ul></dd></div>
    <div><dt>Mode d'emploi</dt><dd>{e(p['gpsr']['instructions'])}</dd></div>
  </dl>
  <p class="gpsr__statut">Avertissements {e(p['gpsr']['avertissements_statut'][0].lower() + p['gpsr']['avertissements_statut'][1:])} ; ils figurent aussi sur l'étiquette et la notice en français.</p>
</div>"""


def bloc_avis(nom):
    return f"""<div class="avis-vide">
  <svg class="icone avis-vide__icone" aria-hidden="true" focusable="false"><use href="#i-etoile"/></svg>
  <h3>Les premiers avis vérifiés arrivent</h3>
  <p>{e(nom)} est en lancement : aucun avis n'a encore été déposé. Nous publierons ici uniquement les avis de clients ayant commandé, positifs comme négatifs, par ordre chronologique, avec leur date. Aucun avis n'est importé d'un autre site ni rémunéré.</p>
</div>"""


def accordeon(questions):
    return '<div class="accordeon">' + "".join(
        f"<details><summary>{e(q)}</summary><div><p>{e(r)}</p></div></details>" for q, r in questions
    ) + "</div>"


def galerie(item, nom):
    figs, vign = "", ""
    for i, im in enumerate(item["images"]):
        figs += f'<figure>{img(im["src"], im["alt"], 800, 600, prioritaire=(i == 0))}</figure>'
        vign += (
            f'<button type="button" data-cible="{i}" aria-label="Afficher l\'image {i + 1} sur {len(item["images"])}"'
            f'{" aria-current=\"true\"" if i == 0 else ""}><img src="{im["src"]}" alt="" width="84" height="63" loading="lazy"></button>'
        )
    note, badge = "", ""
    if all(im["illustration"] for im in item["images"]):
        badge = '<span class="galerie__badge galerie__badge--image" aria-hidden="true">Illustration</span>'
        note = '<p class="galerie__note">Illustrations : les photos du produit réel seront publiées à réception du stock contrôlé.</p>'
    vignettes = f'<div class="galerie__vignettes" role="group" aria-label="Choisir une image">{vign}</div>' if len(item["images"]) > 1 else ""
    return f"""<div class="galerie js-galerie">
  <div class="galerie__cadre">{badge}<div class="galerie__principale" tabindex="0" role="region" aria-label="Images : {e(nom)}">{figs}</div></div>
  {vignettes}
  {note}
</div>"""


def barre_achat(item):
    return f"""<div class="barre-achat js-barre-achat" aria-hidden="true">
  <div class="barre-achat__info"><div class="barre-achat__nom js-barre-nom">{e(item['nom'])}</div><div class="barre-achat__prix"><span class="js-barre-prix">{euros(item['prix_ttc'])}</span> TTC</div></div>
  <button type="button" class="btn btn--primaire js-barre-ajouter" tabindex="-1">Ajouter au panier</button>
</div>"""


def quantite():
    return """<div class="quantite js-quantite"><button type="button" data-pas="-1" aria-label="Diminuer la quantité">−</button><label class="visuellement-cache" for="qte">Quantité</label><input id="qte" type="number" inputmode="numeric" min="1" max="10" value="1"><button type="button" data-pas="1" aria-label="Augmenter la quantité">+</button></div>"""


TPL_ATTENTE = """<template id="tpl-attente">
  <form class="formulaire js-form-inscription" data-source="liste-attente" novalidate>
    <p class="message message--info">Lancement en novembre : recevez un e-mail le jour de l'ouverture des ventes.</p>
    <div class="champ"><label for="attente-email">Votre adresse e-mail</label>
      <div class="form-ligne"><input id="attente-email" name="email" type="email" autocomplete="email" required><button class="btn btn--primaire" type="submit">Me prévenir</button></div>
      <p class="aide">Un e-mail de confirmation vous sera envoyé. Désinscription en un clic. <a href="/confidentialite/">Confidentialité</a></p>
      <p class="erreur js-erreur" role="alert"></p>
    </div>
  </form>
</template>"""


# ===================================================================== pages produit


def page_produit(p):
    heros = p["role"] == "heros"
    autres = [x for x in CAT["produits"] if x["id"] != p["id"]]
    kits_avec = [k for k in CAT["kits"] if any(c["id"] == p["id"] for c in k["composition"])]
    fil = [("Accueil", "/"), ("Boutique", "/boutique/"), (p["nom"], p["url"])]
    benefs = "".join(f"<li>{ic('check')}<span>{e(b)}</span></li>" for b in p["benefices"])

    if heros:
        options = []
        ordre = ["grand-kit", p["id"], "kit-anti-poils", "duo-rouleaux", "kit-chat-hiver"]
        for oid in ordre:
            it = IDX[oid]
            if it["type"] == "kit":
                compo = " + ".join(
                    (f"{c['quantite']} " if c["quantite"] > 1 else "") + NOMS_COURTS[c["id"]].split(" ", 1)[1] + ("s" if c["quantite"] > 1 else "")
                    for c in it["composition"]
                )
                detail = f"{compo.capitalize()} · {euros(it['economie_ttc'])} de moins que séparément"
                if it["livraison_offerte"]:
                    detail += " · livraison offerte"
                badge = ' <span class="badge">Le plus complet</span>' if it["mise_en_avant"] else (
                    ' <span class="badge badge--sauge">Hiver</span>' if it.get("saison") else ""
                )
                nom = it["nom"]
            else:
                detail = "Le rouleau seul · livraison 3,90 €, offerte dès 35 €"
                badge, nom = "", "Rouleau seul"
            options.append(
                f'<label class="offre" data-offre="{oid}"><input type="radio" name="offre" value="{oid}"{" checked" if oid == p["id"] else ""}>'
                f'<span class="offre__nom">{e(nom)}{badge}</span><span class="offre__prix" data-prix="{oid}">{euros(it["prix_ttc"])}</span>'
                f'<span class="offre__detail">{e(detail)}</span></label>'
            )
        selecteur = f'<fieldset class="offres"><legend>Choisissez votre formule</legend>{"".join(options)}</fieldset>'
        gant = IDX["gant-toilettage"]
        kap = IDX["kit-anti-poils"]
        diff = round(kap["prix_ttc"] - p["prix_ttc"], 2)
        upsell = f"""<label class="case js-upsell"><input type="checkbox" value="kit-anti-poils"><span><strong>Ajouter le gant de toilettage (+{euros(diff)})</strong><br><span class="texte-2">Rouleau + gant = Kit anti-poils à {euros(kap['prix_ttc'])} au lieu de {euros(p['prix_ttc'] + gant['prix_ttc'])} séparément. Le gant récupère une partie des poils au brossage.</span></span></label>"""
    else:
        selecteur, upsell = f'<input type="hidden" name="offre" value="{p["id"]}">', ""

    saison = ""
    if p.get("saison"):
        saison = f'<p class="message message--info js-saison" data-saison="{p["id"]}">Produit de saison, vendu {p["saison"]["libelle"]}.</p>'

    bouton_txt = "Ajouter au panier"
    achat = f"""<div class="js-achat" data-produit="{p['id']}">
  {selecteur}
  {upsell}
  {saison}
  <div class="achat">{quantite()}<button type="button" class="btn btn--primaire btn--grand js-ajouter"><span class="js-libelle-ajout">{bouton_txt}</span><span class="achat__prix">&nbsp;·&nbsp;<span class="js-prix-bouton">{euros(p['prix_ttc'])}</span></span></button></div>
</div>"""

    kit_suggere = ""
    if not heros and kits_avec:
        k = next((x for x in kits_avec if x["mise_en_avant"]), kits_avec[0])
        kit_suggere = f"""<div class="suggestion"><img src="{k['images'][0]['src']}" alt="" width="56" height="42" loading="lazy"><p class="suggestion__texte">Aussi dans le <strong>{e(k['nom'])}</strong> à {euros(k['prix_ttc'])}{', livraison offerte' if k['livraison_offerte'] else ''} : {euros(k['economie_ttc'])} de moins que séparément.</p><a class="btn btn--secondaire" href="{k['url']}">Voir</a></div>"""

    # sections de détail
    caract = p["caracteristiques"]
    lignes_c = ""
    libelles = {
        "matieres": "Matières", "dimensions": "Dimensions", "taille": "Taille", "poids": "Poids",
        "alimentation": "Alimentation", "entretien": "Entretien", "origine": "Origine",
    }
    for k_, lib in libelles.items():
        if k_ in caract:
            lignes_c += f'<tr><th scope="row">{lib}</th><td>{e(caract[k_])}</td></tr>'
    lignes_c += f'<tr><th scope="row">Référence</th><td>{e(p["sku"])}</td></tr>'
    lignes_c += f'<tr><th scope="row">Contenu du colis</th><td>{e(", ".join(p["contenu_du_colis"]))}</td></tr>'

    surfaces = ""
    if caract.get("surfaces_conseillees"):
        oui = "".join(f"<li>{e(s)}</li>" for s in caract["surfaces_conseillees"])
        non = "".join(f"<li>{e(s)}</li>" for s in caract["surfaces_deconseillees"])
        surfaces = f"""<section class="section" aria-labelledby="t-surfaces"><div class="conteneur">
  <span class="surtitre">Sans trucage</span>
  <h2 id="t-surfaces">Où il marche, et où il marche moins bien</h2>
  <p class="chapo">Nous préférons le dire avant votre achat. En cas de doute sur votre tissu, envoyez-nous une photo : nous vous répondons sous 24 heures ouvrées.</p>
  <div class="surfaces">
    <div class="surfaces__oui"><h3>{ic("oui")}Donne ses meilleurs résultats sur</h3><ul>{oui}</ul></div>
    <div class="surfaces__non"><h3>{ic("non")}Moins efficace sur</h3><ul>{non}</ul><p class="texte-2">Pour les tapis et la moquette, la <a href="{IDX['raclette-anti-poils']['url']}">raclette anti-poils</a> prend le relais.</p></div>
  </div>
</div></section>"""

    comment = ""
    if heros:
        etapes = ""
        textes = [
            ("Allers-retours courts", "Posez le rouleau sur le tissu et faites des allers-retours en appuyant légèrement."),
            ("Les poils vont au réservoir", "La bande textile attrape les poils et les dépose dans un réservoir fermé."),
            ("Videz, recommencez", "Ouvrez le clapet au-dessus de la poubelle. Aucune feuille adhésive ni recharge à racheter."),
        ]
        for i, (t, d) in enumerate(textes):
            etapes += f"""<div class="etape">{img(f'/images/illustrations/etape-{i + 1}.svg', ALTS['etapes'][i], 400, 300)}<h3><span class="etape__num" aria-hidden="true">{i + 1}</span>{e(t)}</h3><p>{e(d)}</p></div>"""
        comment = f"""<section class="section section--blanche" aria-labelledby="t-comment"><div class="conteneur">
  <span class="surtitre">Mode d'emploi</span>
  <h2 id="t-comment">Comment ça marche</h2>
  <div class="grille-3">{etapes}</div>
</div></section>"""

    croise = [x for x in autres if heros or x["id"] != "tapis-fenetre-thermique"][:3]
    if len(croise) < 3:
        croise.append(IDX["grand-kit"])
    cartes = "".join(carte_item(x) for x in croise)
    faq_q = [(q["q"], q["r"]) for q in p["faq"]]

    corps = f"""
<nav class="fil-ariane conteneur" aria-label="Fil d'Ariane"><ol><li><a href="/">Accueil</a></li><li><a href="/boutique/">Boutique</a></li><li aria-current="page">{e(p['nom'])}</li></ol></nav>
<section class="produit"><div class="conteneur produit__grille">
  {galerie(p, p['nom'])}
  <div class="produit__infos">
    <div class="produit__entete">
      <span class="badge badge--creme">{e(ACCROCHES[p['id']])}</span>
      <h1>{e(p['nom'])}</h1>
      <p class="produit__accroche">{e(p['description_courte'])}</p>
      <div class="produit__prix"><span class="prix prix--grand js-prix-offre">{euros(p['prix_ttc'])}</span><span class="mention-ttc">TTC</span><span class="ligne-livraison">{ligne_livraison_item(p)}</span></div>
    </div>
    <ul class="benefices">{benefs}</ul>
    {achat}
    {encart_livraison()}
    {kit_suggere}
  </div>
</div></section>
{comment}
<section class="section" aria-labelledby="t-desc"><div class="conteneur grille-2">
  <div><span class="surtitre">En détail</span><h2 id="t-desc">{e(p['nom'])}</h2><p>{e(p['description_longue'])}</p></div>
  <div><h3>Caractéristiques</h3><div class="tableau-wrap"><table><tbody>{lignes_c}</tbody></table></div><p class="texte-2">Les valeurs précédées de « ≈ » ou marquées « à confirmer » seront mesurées sur le stock contrôlé avant expédition.</p></div>
</div></section>
{surfaces}
<section class="section section--blanche" aria-labelledby="t-avis"><div class="conteneur">
  <h2 id="t-avis">Avis clients</h2>
  {bloc_avis(p['nom'])}
</div></section>
<section class="section" aria-labelledby="t-faq"><div class="conteneur grille-2">
  <div><span class="surtitre">Questions fréquentes</span><h2 id="t-faq">Vos questions sur {e(NOMS_COURTS[p['id']][0].lower() + NOMS_COURTS[p['id']][1:])}</h2>{accordeon(faq_q)}</div>
  <div>{bloc_gpsr(p, 'h2')}</div>
</div></section>
<section class="section section--blanche" aria-labelledby="t-croise"><div class="conteneur">
  <div class="titre-section"><h2 id="t-croise">{'Complétez la maison' if heros else 'Avec ce produit'}</h2><a class="lien-fleche" href="/boutique/">Toute la boutique</a></div>
  <div class="grille-produits grille-produits--3">{cartes}</div>
</div></section>
{TPL_ATTENTE}
{barre_achat(p)}
"""
    desc_meta = {
        "rouleau-anti-poils": "Rouleau anti-poils réutilisable pour chat et chien : sans adhésif ni recharge, se vide en un geste. 24,90 € TTC, expédié depuis la France, livré en 3 à 6 jours ouvrés.",
        "gant-toilettage": "Gant de toilettage en silicone pour chat et chien : récupère une partie des poils morts au brossage. 9,90 € TTC, expédié depuis la France en 3 à 6 jours ouvrés.",
        "raclette-anti-poils": "Raclette anti-poils pour tapis, moquette et voiture : décolle les poils de chien et de chat incrustés. 12,90 € TTC, expédiée depuis la France.",
        "tapis-fenetre-thermique": "Tapis de fenêtre thermique pour chat : couchage sherpa avec couche réfléchissante, sans fil ni prise. 24,90 € TTC, vendu d'octobre à février.",
    }[p["id"]]
    titres = {
        "rouleau-anti-poils": "Rouleau anti-poils réutilisable chat et chien | Canapoil",
        "gant-toilettage": "Gant de toilettage en silicone chat et chien | Canapoil",
        "raclette-anti-poils": "Raclette anti-poils tapis et voiture | Canapoil",
        "tapis-fenetre-thermique": "Tapis de fenêtre thermique pour chat | Canapoil",
    }
    page(
        f"produits/{p['slug']}/index.html", p["url"], titres[p["id"]], desc_meta, corps, "produit",
        jsonld=[ld_produit(p, p["description_courte"]), ld_fil(fil), ld_faq(faq_q)],
        og_type="product", og_image=p["image_partage"], classes="avec-barre",
    )


def page_kit(k):
    compo_items = [IDX[c["id"]] for c in k["composition"]]
    lignes = "".join(
        f'<li>{ic("check")}<span><a href="{IDX[c["id"]]["url"]}">{e(IDX[c["id"]]["nom"])}</a>'
        f'{" × " + str(c["quantite"]) if c["quantite"] > 1 else ""} · {euros(IDX[c["id"]]["prix_ttc"])} à l\'unité</span></li>'
        for c in k["composition"]
    )
    somme = " + ".join(
        euros(IDX[c["id"]]["prix_ttc"]) for c in k["composition"] for _ in range(c["quantite"])
    )
    eco = f'<p class="economie">{euros(k["economie_ttc"])} de moins que les produits achetés séparément ({somme} = {euros(k["prix_separes_ttc"])}).</p>'
    saison = ""
    if k.get("saison"):
        fin = dt.date.fromisoformat(k["disponible_jusqu_au"])
        saison = f'<p class="message message--info js-saison" data-saison="{k["id"]}">Kit de saison, disponible jusqu\'au {fin.day} février {fin.year}.</p>'
    gpsr = "".join(bloc_gpsr(x) for x in dict((x["id"], x) for x in compo_items).values())
    fil = [("Accueil", "/"), ("Boutique", "/boutique/"), (k["nom"], k["url"])]
    autres = [x for x in CAT["kits"] if x["id"] != k["id"]][:3]
    corps = f"""
<nav class="fil-ariane conteneur" aria-label="Fil d'Ariane"><ol><li><a href="/">Accueil</a></li><li><a href="/boutique/#kits">Kits</a></li><li aria-current="page">{e(k['nom'])}</li></ol></nav>
<section class="produit"><div class="conteneur produit__grille">
  {galerie(k, k['nom'])}
  <div class="produit__infos">
    <div class="produit__entete">
      {'<span class="badge">Le plus complet</span>' if k['mise_en_avant'] else '<span class="badge badge--creme">Kit</span>'}
      <h1>{e(k['nom'])}</h1>
      <p class="produit__accroche">{e(k['description'])}</p>
      <div class="produit__prix">{bloc_prix(k, True)}<span class="mention-ttc">TTC</span><span class="ligne-livraison">{ligne_livraison_item(k)}</span></div>
      {eco}
    </div>
    <h2 class="visuellement-cache">Contenu du kit</h2>
    <ul class="benefices">{lignes}</ul>
    <div class="js-achat" data-produit="{k['id']}">
      <input type="hidden" name="offre" value="{k['id']}">
      {saison}
      <div class="achat">{quantite()}<button type="button" class="btn btn--primaire btn--grand js-ajouter"><span class="js-libelle-ajout">Ajouter au panier</span><span class="achat__prix">&nbsp;·&nbsp;<span class="js-prix-bouton">{euros(k['prix_ttc'])}</span></span></button></div>
    </div>
    {encart_livraison()}
  </div>
</div></section>
<section class="section section--blanche" aria-labelledby="t-compo"><div class="conteneur">
  <h2 id="t-compo">Ce que contient le kit</h2>
  <div class="grille-produits grille-produits--3">{''.join(carte_item(x) for x in dict((x['id'], x) for x in compo_items).values())}</div>
</div></section>
<section class="section" aria-labelledby="t-secu"><div class="conteneur">
  <h2 id="t-secu">Informations de sécurité des produits du kit</h2>
  <div class="grille-2">{gpsr}</div>
</div></section>
<section class="section section--blanche" aria-labelledby="t-avis"><div class="conteneur"><h2 id="t-avis">Avis clients</h2>{bloc_avis(k['nom'])}</div></section>
<section class="section" aria-labelledby="t-autres"><div class="conteneur">
  <div class="titre-section"><h2 id="t-autres">Les autres kits</h2><a class="lien-fleche" href="/boutique/">Toute la boutique</a></div>
  <div class="grille-produits grille-produits--3">{''.join(carte_item(x, vedette=x['mise_en_avant']) for x in autres)}</div>
</div></section>
{TPL_ATTENTE}
{barre_achat(k)}
"""
    desc = f"{k['nom']} Canapoil à {euros(k['prix_ttc']).replace(chr(160), ' ')} TTC : {k['description']} {euros(k['economie_ttc']).replace(chr(160), ' ')} de moins que séparément. Expédié depuis la France."
    desc = desc.replace("  ", " ")
    page(
        f"kits/{k['slug']}/index.html", k["url"], f"{k['nom']} anti-poils chat et chien | Canapoil" if k["id"] != "kit-chat-hiver" else "Kit chat d'hiver : rouleau et tapis de fenêtre | Canapoil",
        desc[:300], corps, "produit",
        jsonld=[ld_produit(k, k["description"]), ld_fil(fil)], og_type="product", og_image=k["image_partage"], classes="avec-barre",
    )


# ===================================================================== autres pages


ENGAGEMENTS = [
    ("etoile", "Aucun faux avis", "Seuls les clients qui ont commandé peuvent laisser un avis. Les avis négatifs sont publiés."),
    ("etiquette", "Aucune fausse promotion", "Pas de prix barré inventé, pas de compte à rebours, pas de stock fictif. L'économie des kits est écrite en clair."),
    ("camion", "Des délais réels", "Expédié depuis la France sous 1 jour ouvré. Le délai affiché sera recalculé sur nos livraisons réelles."),
    ("repere", "L'origine dite clairement", "Produits fabriqués en Chine, importés, contrôlés, étiquetés et expédiés depuis la France par Canapoil."),
    ("oeil", "Les limites aussi", "Nous disons où nos produits marchent moins bien : cuir, soie, tapis à poils longs."),
    ("retour", "30 jours pour changer d'avis", "14 jours prévus par la loi, plus 16 jours que nous ajoutons. Rétractation en ligne en deux clics."),
]


def bloc_engagements():
    lis = "".join(f"<li>{ic(i)}<div><strong>{e(t)}</strong><span>{e(d)}</span></div></li>" for i, t, d in ENGAGEMENTS)
    return f'<ul class="engagements">{lis}</ul>'


FAQ_GENERALE = [
    ("Livraison", [
        ("Sous quel délai vais-je recevoir ma commande ?", "Elle est expédiée depuis notre stock en France sous 1 jour ouvré et livrée en point relais Mondial Relay en 3 à 6 jours ouvrés. La fourchette de dates est affichée sur chaque fiche produit."),
        ("Combien coûte la livraison ?", "3,90 € en point relais. Elle est offerte dès 35 € d'achat, ainsi que pour le Grand kit, le Duo maison + voiture et le Kit chat d'hiver."),
        ("Livrez-vous à domicile ou hors de France ?", "Pas encore : uniquement en point relais, en France métropolitaine (Corse comprise). La livraison à domicile, la Belgique et le Luxembourg viendront ensuite."),
        ("Y a-t-il des frais de douane à la livraison ?", "Non. Le prix payé sur le site est le seul montant dû : nos produits sont déjà en France quand vous commandez."),
    ]),
    ("Retours et rétractation", [
        ("Puis-je changer d'avis ?", "Oui, pendant 30 jours après la réception : 14 jours prévus par la loi, plus 16 jours que nous ajoutons. Aucun motif n'est demandé."),
        ("Comment me rétracter ?", "Cliquez sur « renoncer au contrat ici » en bas de chaque page, remplissez le formulaire (nom, prénom, numéro de commande, e-mail) et cliquez sur « confirmer la rétractation ». Vous recevez un accusé de réception par e-mail."),
        ("Qui paie le retour ?", "Vous, en cas de changement d'avis (environ 5 à 7 € en point relais). Nous le prenons en charge si le produit est défectueux ou si nous nous sommes trompés."),
        ("Quand suis-je remboursé ?", "Au plus tard 14 jours après votre demande, frais de livraison initiaux inclus, par le même moyen de paiement."),
    ]),
    ("Paiement et commande", [
        ("Quels moyens de paiement acceptez-vous ?", "Les cartes bancaires (CB, Visa, Mastercard) et les autres moyens affichés sur la page de paiement Stripe. Aucun frais n'est ajouté selon le moyen choisi."),
        ("Le paiement est-il sécurisé ?", "Oui. Vous payez sur la page sécurisée de Stripe, avec authentification forte (3-D Secure). Nous ne voyons jamais les numéros de votre carte."),
        ("Que veut dire « précommande » ?", "Pendant le lancement, certains produits peuvent être proposés en précommande : la date d'expédition et la date limite de livraison sont écrites sur la fiche et dans l'e-mail de confirmation. Elles ne dépassent jamais 30 jours après votre commande."),
    ]),
    ("Nos produits", [
        ("Où sont fabriqués vos produits ?", "En Chine. Nous les importons par lot, les contrôlons, les étiquetons à notre nom et les expédions depuis la France. Canapoil est une marque française ; nos produits ne sont pas fabriqués en France."),
        ("Les produits sont-ils testés ?", "Chaque référence est testée sur échantillon avant la mise en vente : efficacité sur plusieurs tissus, finition, notice en français. Nous publions les résultats en vidéo, y compris là où le produit marche moins bien."),
        ("Pourquoi n'y a-t-il pas encore d'avis ?", "Canapoil est en lancement. Nous n'importons aucun avis d'un autre site et n'en rédigeons aucun : les premiers avis vérifiés de clients arriveront après les premières livraisons."),
        ("Puis-je vous montrer mon tissu avant d'acheter ?", "Oui, envoyez-nous une photo par e-mail : nous vous disons franchement si le rouleau ou la raclette conviennent."),
    ]),
]


def page_accueil():
    rouleau = IDX["rouleau-anti-poils"]
    kits = "".join(carte_item(k, vedette=k["mise_en_avant"]) for k in CAT["kits"])
    produits = "".join(carte_item(p) for p in CAT["produits"])
    etapes = ""
    textes = [
        ("Allers-retours courts", "Posez le rouleau sur le canapé, le plaid ou le siège auto et faites des allers-retours."),
        ("Les poils au réservoir", "La bande textile attrape les poils et les range dans un réservoir fermé."),
        ("Un geste pour vider", "Ouvrez le clapet au-dessus de la poubelle. Sans adhésif, sans recharge, sans pile."),
    ]
    for i, (t, d) in enumerate(textes):
        etapes += f"""<div class="etape">{img(f'/images/illustrations/etape-{i + 1}.svg', ALTS['etapes'][i], 400, 300)}<h3><span class="etape__num" aria-hidden="true">{i + 1}</span>{e(t)}</h3><p>{e(d)}</p></div>"""
    faq_extrait = [q for _, qs in FAQ_GENERALE for q in qs][:1] + [FAQ_GENERALE[1][1][0], FAQ_GENERALE[3][1][0], FAQ_GENERALE[3][1][2]]
    corps = f"""
<section class="hero"><div class="conteneur hero__grille">
  <div>
    <span class="surtitre">Rouleau anti-poils réutilisable</span>
    <h1>Les câlins sur le canapé, <em>les poils à la poubelle.</em></h1>
    <p class="chapo">Des outils simples pour partager le canapé avec votre chat ou votre chien et garder un intérieur présentable. Montrés en vidéo sur de vrais tissus, expédiés depuis la France.</p>
    <div class="hero__actions">
      <a class="btn btn--primaire btn--grand" href="{rouleau['url']}">Découvrir le rouleau · <span data-prix="{rouleau['id']}">{euros(rouleau['prix_ttc'])}</span></a>
      <a class="btn btn--secondaire btn--grand" href="/boutique/#kits">Voir les kits</a>
    </div>
    <ul class="puces">
      <li>{ic("check")}<span><strong>Réutilisable</strong> : aucune feuille adhésive ni recharge à racheter</span></li>
      <li>{ic("check")}<span><strong>Expédié depuis la France</strong> sous 1 jour ouvré, livré en 3 à 6 jours ouvrés</span></li>
      <li>{ic("check")}<span><strong>30 jours pour changer d'avis</strong>, rétractation en ligne en deux clics</span></li>
    </ul>
  </div>
  <div class="hero__visuel">{img('/images/illustrations/accueil-canape.svg', ALTS['hero'], 960, 720, prioritaire=True)}</div>
</div></section>

<section class="section section--blanche" aria-labelledby="t-comment"><div class="conteneur">
  <div class="centre"><span class="surtitre">Démonstration en 3 secondes</span><h2 id="t-comment">Comment marche le rouleau</h2>
  <p class="chapo">Il donne ses meilleurs résultats sur les canapés en tissu ou en velours, les plaids, les lits et les sièges auto. Sur le cuir, la soie et les tapis à poils longs, il est moins efficace : nous le disons avant votre achat.</p></div>
  <div class="grille-3">{etapes}</div>
  <p class="centre"><a class="btn btn--primaire btn--grand" href="{rouleau['url']}">Voir le rouleau</a></p>
</div></section>

<section class="section" id="kits" aria-labelledby="t-kits"><div class="conteneur">
  <div class="titre-section"><div><span class="surtitre">Pensés par surface</span><h2 id="t-kits">Les kits</h2></div><a class="lien-fleche" href="/boutique/">Toute la boutique</a></div>
  <div class="grille-produits grille-produits--4">{kits}</div>
  <p class="texte-2">L'économie affichée est la différence avec les produits achetés séparément au prix pratiqué aujourd'hui. Aucun prix barré.</p>
</div></section>

<section class="section section--sauge" aria-labelledby="t-engagements"><div class="conteneur">
  <span class="surtitre">Ce que nous nous interdisons</span>
  <h2 id="t-engagements">Une boutique honnête, vérifiable</h2>
  <p class="chapo">Le dropshipping a mauvaise réputation, souvent à raison. Voici nos règles, et elles sont écrites dans nos conditions de vente.</p>
  {bloc_engagements()}
</div></section>

<section class="section section--blanche" aria-labelledby="t-produits"><div class="conteneur">
  <div class="titre-section"><h2 id="t-produits">À l'unité</h2></div>
  <div class="grille-produits grille-produits--4">{produits}</div>
</div></section>

<section class="section" aria-labelledby="t-avis"><div class="conteneur"><h2 id="t-avis" class="centre">Avis clients</h2>{bloc_avis("Canapoil")}</div></section>

<section class="section section--creme" aria-labelledby="t-faq"><div class="conteneur grille-2">
  <div><span class="surtitre">Questions fréquentes</span><h2 id="t-faq">Avant de commander</h2><p>Toutes les réponses sur la livraison, les retours et nos produits.</p><p><a class="lien-fleche" href="/faq/">Toutes les questions</a></p></div>
  {accordeon(faq_extrait)}
</div></section>

<section class="section section--blanche" aria-labelledby="t-lettre"><div class="conteneur grille-2">
  <div><h2 id="t-lettre">Des astuces anti-poils, une fois par mois</h2><p class="texte-2">Les nouveautés et nos tests sur de vrais tissus. Pas de fausse promotion, désinscription en un clic.</p></div>
  <form class="formulaire js-form-inscription" data-source="lettre" novalidate>
    <div class="champ"><label for="lettre-email">Votre adresse e-mail</label>
      <div class="form-ligne"><input id="lettre-email" name="email" type="email" autocomplete="email" required><button class="btn btn--primaire" type="submit">S'inscrire</button></div>
      <p class="aide">Un e-mail de confirmation vous sera envoyé avant toute inscription. <a href="/confidentialite/">Confidentialité</a></p>
      <p class="erreur js-erreur" role="alert"></p>
    </div>
  </form>
</div></section>
"""
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Canapoil", "url": BASE + "/", "inLanguage": "fr-FR"}
    page("index.html", "/", BRAND["seo"]["titre_accueil"],
         BRAND["seo"]["meta_description_accueil"], corps, "accueil", jsonld=[ld_organisation(), site_ld])


def page_boutique():
    kits = "".join(carte_item(k, vedette=k["mise_en_avant"]) for k in CAT["kits"])
    produits = "".join(carte_item(p) for p in CAT["produits"])
    corps = f"""
<section class="page-entete"><div class="conteneur">
  <h1>La boutique</h1>
  <p class="chapo">Un rouleau pour le canapé, une raclette pour les tapis et la voiture, un gant pour brosser l'animal. Les kits regroupent les outils par surface et coûtent moins cher que les produits achetés séparément.</p>
</div></section>
<section class="section" id="kits" aria-labelledby="t-kits"><div class="conteneur">
  <h2 id="t-kits">Les kits</h2>
  <div class="grille-produits grille-produits--4">{kits}</div>
  <p class="texte-2">Livraison offerte pour le Grand kit, le Duo et le Kit chat d'hiver, et dès 35 € d'achat. L'économie est calculée sur les prix unitaires pratiqués aujourd'hui sur ce site.</p>
</div></section>
<section class="section section--blanche" id="produits" aria-labelledby="t-unite"><div class="conteneur">
  <h2 id="t-unite">À l'unité</h2>
  <div class="grille-produits grille-produits--4">{produits}</div>
</div></section>
<section class="section"><div class="conteneur">{encart_livraison()}</div></section>
"""
    items = CAT["kits"] + CAT["produits"]
    liste = {
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + x["url"], "name": x["nom"]} for i, x in enumerate(items)],
    }
    page("boutique/index.html", "/boutique/", "Boutique anti-poils chat et chien : rouleau, kits, raclette | Canapoil",
         "Rouleau anti-poils réutilisable, gant de toilettage, raclette tapis et voiture, tapis de fenêtre et kits jusqu'à 9,90 € moins chers. Expédié depuis la France.",
         corps, "boutique", jsonld=[liste, ld_fil([("Accueil", "/"), ("Boutique", "/boutique/")])])


def page_panier():
    corps = """
<section class="page-entete"><div class="conteneur"><h1>Votre panier</h1></div></section>
<section class="section"><div class="conteneur page-panier__grille">
  <div class="panneau">
    <div class="progression js-progression"></div>
    <ul class="lignes js-lignes"><li class="vide">Chargement du panier…</li></ul>
    <div class="js-suggestion"></div>
    <noscript><p class="message message--alerte">Le panier nécessite JavaScript. Vous pouvez aussi commander par e-mail : {{EMAIL}}.</p></noscript>
  </div>
  <aside class="panneau colonne-collante" aria-labelledby="t-recap">
    <h2 id="t-recap">Récapitulatif</h2>
    <div class="recap js-recap"></div>
    <a class="btn btn--primaire btn--plein btn--grand js-vers-commande" href="/commande/">Commander</a>
    <p class="recap__note">Livraison en point relais Mondial Relay en 3 à 6 jours ouvrés, depuis la France. Prix TTC.</p>
  </aside>
</div></section>
"""
    page("panier/index.html", "/panier/", "Votre panier | Canapoil", "Votre panier Canapoil : récapitulatif, frais de livraison et accès à la commande.",
         corps, "panier", robots="noindex,follow")


def page_commande():
    corps = f"""
<section class="page-entete"><div class="conteneur">
  <ol class="etapes-commande"><li>1. Panier</li><li aria-current="step">2. Livraison et acceptation</li><li>3. Paiement sécurisé Stripe</li></ol>
  <h1>Commande</h1>
  <div class="message message--demo js-avertissement-demo" hidden><strong>Site en mode démonstration.</strong> Aucun paiement ne sera demandé : le bouton simule la commande et mène à la page de confirmation.</div>
</div></section>
<section class="section"><div class="conteneur commande__grille">
  <form class="panneau formulaire js-form-commande" novalidate>
    <h2>Livraison</h2>
    <p class="encart__ligne">{ic("repere")}<span><strong>Point relais Mondial Relay</strong>, en France métropolitaine. Expédié sous 1 jour ouvré depuis la France, livré en 3 à 6 jours ouvrés<span class="js-dates-livraison"></span>.</span></p>
    <div class="champ">
      <label for="point-relais">Numéro du point relais choisi <span class="texte-2">(facultatif)</span></label>
      <input id="point-relais" name="point_relais" type="text" maxlength="80" autocomplete="off" aria-describedby="aide-relais">
      <p class="aide" id="aide-relais">Trouvez un point relais sur <a href="https://www.mondialrelay.fr/trouver-le-point-relais-le-plus-proche-de-chez-moi/" rel="noopener" target="_blank">le site de Mondial Relay (nouvel onglet)</a> et copiez son numéro ou son nom. Sans indication, nous retenons le point relais le plus proche de l'adresse de livraison saisie à l'étape suivante et nous vous l'indiquons par e-mail avant l'expédition.</p>
    </div>
    <p class="encart__ligne">{ic("info")}<span>Votre adresse e-mail, votre adresse de livraison et votre téléphone (pour l'avis de passage du transporteur) sont demandés à l'étape suivante, sur la page de paiement sécurisée Stripe.</span></p>
    <h2>Conditions</h2>
    <label class="case case--simple" for="cgv"><input id="cgv" name="cgv" type="checkbox" required aria-describedby="erreur-cgv"><span>J'ai lu et j'accepte les <a href="/cgv/" target="_blank" rel="noopener">conditions générales de vente (nouvel onglet)</a>, dont la <a href="/retours-retractation/" target="_blank" rel="noopener">politique de retours (nouvel onglet)</a>.</span></label>
    <p class="erreur" id="erreur-cgv" role="alert"></p>
    <div class="message message--alerte js-erreur-commande" role="alert" hidden></div>
    <button type="submit" class="btn btn--primaire btn--plein btn--grand js-payer">Continuer vers le paiement sécurisé</button>
    <p class="recap__note">{ic("cadenas")} Vous serez redirigé vers la page de paiement Stripe. La commande est passée, avec obligation de paiement, au clic sur « Payer » sur cette page. {badges_paiement()}</p>
  </form>
  <aside class="panneau colonne-collante" aria-labelledby="t-recap">
    <h2 id="t-recap">Votre commande</h2>
    <ul class="lignes js-lignes js-lignes-lecture"></ul>
    <div class="recap js-recap"></div>
    <p><a href="/panier/">Modifier le panier</a></p>
  </aside>
</div></section>
"""
    page("commande/index.html", "/commande/", "Commande | Canapoil", "Finalisez votre commande Canapoil : point relais, acceptation des CGV et paiement sécurisé.",
         corps, "commande", robots="noindex,nofollow")


def page_merci():
    corps = """
<section class="section"><div class="conteneur prose">
  <div class="message message--demo js-merci-demo" hidden><strong>Simulation.</strong> Aucun paiement n'a été effectué et aucune commande n'a été transmise : le site est en mode démonstration.</div>
  <h1 class="js-merci-titre">Merci pour votre commande</h1>
  <p class="chapo js-merci-chapo">Un e-mail de confirmation vous est envoyé avec le récapitulatif, nos conditions générales de vente et le formulaire de rétractation.</p>
  <div class="panneau js-merci-recap" hidden><h2>Récapitulatif</h2><p class="js-merci-numero"></p><ul class="lignes js-merci-lignes"></ul><div class="recap js-merci-totaux"></div></div>
  <h2>Et maintenant ?</h2>
  <ol>
    <li>Nous préparons votre colis et l'expédions depuis la France sous 1 jour ouvré.</li>
    <li>Vous recevez un e-mail avec le numéro de suivi et le point relais Mondial Relay retenu.</li>
    <li>Mondial Relay vous prévient quand le colis est disponible : 3 à 6 jours ouvrés après la commande.</li>
  </ol>
  <p>Vous changez d'avis ? Vous avez 30 jours après réception. <a href="/retractation/">renoncer au contrat ici</a>.</p>
  <p><a class="btn btn--secondaire" href="/boutique/">Retour à la boutique</a></p>
</div></section>
"""
    page("merci.html", "/merci.html", "Merci pour votre commande | Canapoil", "Confirmation de commande Canapoil.",
         corps, "merci", robots="noindex,nofollow")


def page_faq():
    blocs, tout = "", []
    for titre, qs in FAQ_GENERALE:
        ident = re.sub(r"[^a-z]+", "-", titre.lower()).strip("-")
        blocs += f'<section class="bloc" aria-labelledby="f-{ident}"><h2 id="f-{ident}">{e(titre)}</h2>{accordeon(qs)}</section>'
        tout += qs
    for p in CAT["produits"]:
        qs = [(q["q"], q["r"]) for q in p["faq"]]
        blocs += f'<section class="bloc" aria-labelledby="f-{p["id"]}"><h2 id="f-{p["id"]}">{e(p["nom"])}</h2>{accordeon(qs)}<p><a href="{p["url"]}">Voir la fiche produit</a></p></section>'
        tout += [(f"{q} ({NOMS_COURTS[p['id']].split(' ', 1)[1]})", r) for q, r in qs]
    corps = f"""
<section class="page-entete"><div class="conteneur"><h1>Questions fréquentes</h1><p class="chapo">Livraison, retours, paiement, origine des produits : les réponses courtes. Une autre question ? Écrivez-nous, nous répondons sous 24 heures ouvrées.</p></div></section>
<section class="section"><div class="conteneur prose">{blocs}<p><a class="btn btn--secondaire" href="/contact/">Nous contacter</a></p></div></section>
"""
    page("faq/index.html", "/faq/", "Questions fréquentes : livraison, retours, produits | Canapoil",
         "Délais de livraison depuis la France, 30 jours pour changer d'avis, paiement sécurisé, origine des produits, efficacité selon les tissus : les réponses de Canapoil.",
         corps, "faq", jsonld=[ld_faq(tout)])


def page_a_propos():
    corps = f"""
<section class="page-entete"><div class="conteneur"><span class="surtitre">À propos</span><h1>Canapoil, la cohabitation canapé-animaux</h1><p class="chapo">{e(M['promesse'])}</p></div></section>
<section class="section"><div class="conteneur grille-2">
  <div class="prose">
    <h2>Pourquoi nous existons</h2>
    <p>En France, 16,6 millions de chats et 9,6 millions de chiens partagent la vie de leurs maîtres, et souvent leur canapé (baromètre FACCO-Odoxa 2026). Le pull noir couvert de poils avant de sortir, le plaid à secouer avant l'arrivée des invités, les sièges de la voiture après la balade : Canapoil sélectionne des outils simples pour ces moments-là.</p>
    <h2>Comment nous travaillons</h2>
    <p>Nous comparons plusieurs fournisseurs sur échantillon, nous testons chaque produit sur de vrais tissus et nous filmons le résultat, y compris là où il marche moins bien. Les produits retenus sont fabriqués en Chine, importés par lot, contrôlés, étiquetés à notre nom avec une notice en français, puis expédiés depuis la France.</p>
    <p>Canapoil est une jeune marque française. Nous avons choisi de le dire, comme le reste : nos délais sont mesurés, nos avis seront vérifiés, nos prix n'ont pas de faux prix barré.</p>
  </div>
  <div>{img('/images/illustrations/accueil-canape.svg', ALTS['hero'], 960, 720)}</div>
</div></section>
<section class="section section--sauge" aria-labelledby="t-engagements"><div class="conteneur">
  <h2 id="t-engagements">Nos engagements</h2>
  {bloc_engagements()}
</div></section>
<section class="section"><div class="conteneur prose">
  <h2>Qui sommes-nous ?</h2>
  <p>Canapoil est une marque de {{{{RAISON_SOCIALE}}}}, {{{{ADRESSE}}}}. Toutes nos coordonnées figurent dans les <a href="/mentions-legales/">mentions légales</a>.</p>
  <p><a class="btn btn--primaire" href="/boutique/">Découvrir la boutique</a></p>
</div></section>
"""
    page("a-propos/index.html", "/a-propos/", "À propos de Canapoil : marque française, produits testés | Canapoil",
         "Canapoil sélectionne et teste des outils anti-poils pour chat et chien. Produits fabriqués en Chine, contrôlés et expédiés depuis la France. Nos engagements.",
         corps, "a-propos")


def page_contact():
    corps = f"""
<section class="page-entete"><div class="conteneur"><h1>Contact</h1><p class="chapo">Une question avant d'acheter, un colis en retard, un produit qui ne convient pas : nous répondons sous 24 heures ouvrées en moyenne, 48 heures au plus.</p></div></section>
<section class="section"><div class="conteneur">
  <div class="contact-cartes">
    <div class="panneau"><h2>{ic("mail")} Par e-mail</h2><p><a href="mailto:{{{{EMAIL}}}}">{{{{EMAIL}}}}</a></p><p class="texte-2">Le plus rapide. Joignez une photo de votre tissu ou du produit si besoin.</p></div>
    <div class="panneau"><h2>{ic("telephone")} Par téléphone</h2><p>{{{{TELEPHONE}}}}</p><p class="texte-2">Appel non surtaxé, {{{{HORAIRES_SERVICE_CLIENT}}}}.</p></div>
    <div class="panneau"><h2>{ic("courrier")} Par courrier</h2><p>{{{{RAISON_SOCIALE}}}}<br>{{{{ADRESSE}}}}</p><p class="texte-2">Retours : utilisez l'adresse indiquée sur la page <a href="/retours-retractation/">Retours</a>.</p></div>
  </div>
</div></section>
<section class="section section--blanche"><div class="conteneur grille-2">
  <div class="prose"><h2>Avant d'acheter</h2><p>Vous ne savez pas si le rouleau convient à votre canapé ? Envoyez-nous une photo du tissu de près : nous vous disons franchement s'il marche, et sinon ce que nous conseillons.</p><p><a href="/faq/">Consulter les questions fréquentes</a></p></div>
  <div class="prose"><h2>Après votre commande</h2><p>Pour vous rétracter : <a href="/retractation/">renoncer au contrat ici</a>. Pour un produit défectueux : écrivez-nous avec votre numéro de commande et une photo.</p><p>En cas de litige non résolu, vous pouvez saisir gratuitement le médiateur de la consommation : {{{{MEDIATEUR}}}}.</p></div>
</div></section>
"""
    page("contact/index.html", "/contact/", "Contact et service client | Canapoil",
         "Contacter le service client Canapoil par e-mail, téléphone ou courrier. Réponse sous 24 heures ouvrées en moyenne. Médiateur de la consommation.",
         corps, "contact")


def page_retractation():
    corps = """
<section class="page-entete"><div class="conteneur prose">
  <h1>Renoncer au contrat</h1>
  <p class="chapo">Vous disposez de 30 jours après la réception de votre commande pour vous rétracter : 14 jours prévus par la loi, plus 16 jours que nous ajoutons. Aucun motif n'est demandé.</p>
</div></section>
<section class="section"><div class="conteneur grille-2">
  <form class="panneau formulaire js-form-retractation" novalidate>
    <div class="message message--demo js-avertissement-demo" hidden><strong>Mode démonstration.</strong> La déclaration n'est pas transmise : l'accusé de réception est simulé à l'écran.</div>
    <div class="champ"><label for="r-nom">Nom</label><input id="r-nom" name="nom" type="text" autocomplete="family-name" required><p class="erreur" role="alert"></p></div>
    <div class="champ"><label for="r-prenom">Prénom</label><input id="r-prenom" name="prenom" type="text" autocomplete="given-name" required><p class="erreur" role="alert"></p></div>
    <div class="champ"><label for="r-commande">Numéro de commande</label><input id="r-commande" name="commande" type="text" required aria-describedby="r-commande-aide"><p class="aide" id="r-commande-aide">Il figure dans l'e-mail de confirmation de commande.</p><p class="erreur" role="alert"></p></div>
    <div class="champ"><label for="r-email">Adresse e-mail pour recevoir l'accusé de réception</label><input id="r-email" name="email" type="email" autocomplete="email" required><p class="erreur" role="alert"></p></div>
    <div class="champ"><label for="r-produits">Produits concernés <span class="texte-2">(facultatif, si vous ne renoncez qu'à une partie de la commande)</span></label><textarea id="r-produits" name="produits" maxlength="500"></textarea></div>
    <div class="message message--alerte js-erreur-retractation" role="alert" hidden></div>
    <button type="submit" class="btn btn--primaire btn--plein btn--grand">confirmer la rétractation</button>
    <p class="recap__note">Un accusé de réception reprenant votre déclaration, avec sa date et son heure, vous est envoyé par e-mail. Vous pouvez aussi utiliser le <a href="/retours-retractation/#formulaire-type-de-rétractation">formulaire type</a> ou nous écrire à {{EMAIL}}.</p>
  </form>
  <div>
    <div class="accuse js-accuse" tabindex="-1" hidden></div>
    <div class="prose js-retractation-info">
      <h2>Ensuite</h2>
      <ol>
        <li>Renvoyez le produit au plus tard 14 jours après votre déclaration, à l'adresse : {{ADRESSE_RETOUR}}.</li>
        <li>Les frais de renvoi sont à votre charge, sauf produit défectueux ou erroné (environ 5 à 7 € en point relais).</li>
        <li>Nous vous remboursons au plus tard 14 jours après votre déclaration, frais de livraison initiaux inclus. Nous pouvons attendre la réception du produit ou votre preuve d'envoi.</li>
      </ol>
      <p><a href="/retours-retractation/">Toutes les conditions de retour</a></p>
    </div>
  </div>
</div></section>
"""
    page("retractation/index.html", "/retractation/", "Renoncer au contrat : rétractation en ligne | Canapoil",
         "Fonctionnalité de rétractation en ligne Canapoil : renoncez à votre commande en deux clics et recevez un accusé de réception horodaté par e-mail.",
         corps, "retractation", robots="noindex,follow")


def page_404():
    corps = """
<section class="erreur-404"><div class="conteneur">
  <h1>Cette page n'existe pas</h1>
  <p class="chapo">Le lien est peut-être ancien, ou une coquille s'est glissée dans l'adresse.</p>
  <p><a class="btn btn--primaire" href="/">Retour à l'accueil</a> <a class="btn btn--secondaire" href="/boutique/">Voir la boutique</a></p>
</div></section>
"""
    page("404.html", "/404.html", "Page introuvable | Canapoil", "Cette page n'existe pas.", corps, "404", robots="noindex,follow")


def pages_legales():
    infos = [
        ("mentions-legales", "/mentions-legales/"),
        ("cgv", "/cgv/"),
        ("retours-retractation", "/retours-retractation/"),
        ("livraison", "/livraison/"),
        ("confidentialite", "/confidentialite/"),
        ("cookies", "/cookies/"),
    ]
    for nom, url in infos:
        meta, corps_md = MD.lire_entete((ICI / "contenus" / f"{nom}.md").read_text(encoding="utf-8"))
        html_corps = MD.convertir(corps_md, "site")
        html_corps = html_corps.replace("<p>Dernière mise à jour", '<p class="mise-a-jour">Dernière mise à jour', 1).replace(
            "<p>Version en vigueur", '<p class="mise-a-jour">Version en vigueur', 1
        )
        if nom == "retours-retractation":
            html_corps = html_corps.replace(
                '<h2 id="en-bref">', f'<p><a class="btn btn--primaire" href="/retractation/">{ic("retour")}renoncer au contrat ici</a></p><h2 id="en-bref">', 1
            )
        corps = f"""
<section class="page-entete"><div class="conteneur prose"><h1>{e(meta['titre'])}</h1><p class="chapo">{e(meta.get('chapo', ''))}</p></div></section>
<section class="section"><div class="conteneur prose">{html_corps}</div></section>
"""
        robots = "index,follow"
        page(f"{nom}/index.html", url, f"{meta['titre']} | Canapoil", meta["description"], corps, "legal", robots=robots)


# ===================================================================== fichiers techniques


def sitemap_robots():
    urls = [p for p in PAGES if p["robots"].startswith("index")]
    prio = lambda u: "1.0" if u == "/" else ("0.9" if u.startswith("/produits/") or u.startswith("/kits/") else ("0.8" if u == "/boutique/" else "0.5"))  # noqa: E731
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in sorted(urls, key=lambda x: (-float(prio(x["url"])), x["url"])):
        xml += f"  <url><loc>{BASE}{p['url']}</loc><lastmod>{AUJOURDHUI.isoformat()}</lastmod><priority>{prio(p['url'])}</priority></url>\n"
    xml += "</urlset>\n"
    ecrire(SITE / "sitemap.xml", xml)
    robots = f"""# Canapoil
User-agent: *
Allow: /
Disallow: /panier/
Disallow: /commande/
Disallow: /merci.html
Disallow: /retractation/
Disallow: /documents/
Disallow: /api/
Disallow: /outils/
Disallow: /netlify/
Disallow: /functions/

Sitemap: {BASE}/sitemap.xml
"""
    ecrire(SITE / "robots.txt", robots)


CATEGORIES_GOOGLE = {
    "rouleau-anti-poils": "3080",
    "gant-toilettage": "6385",
    "raclette-anti-poils": "2610",
    "tapis-fenetre-thermique": "4433",
}


def flux_merchant():
    """Flux RSS 2.0 Google Merchant Center (fiches gratuites). À ne soumettre
    qu'avec de vraies photos : les illustrations ne respectent pas les règles
    d'images de Google."""
    liv = CAT["livraison"]
    items = ""
    for it in CAT["produits"] + CAT["kits"]:
        desc = it.get("description_longue") or (it["description"] + " Contenu : " + ", ".join(IDX[c["id"]]["nom"] + (f" × {c['quantite']}" if c["quantite"] > 1 else "") for c in it["composition"]) + ".")
        gratuit = it.get("livraison_offerte") or it["prix_ttc"] >= liv["seuil_gratuite_ttc"]
        cat = CATEGORIES_GOOGLE.get(it["id"], "3080")
        items += f"""  <item>
    <g:id>{e(it['sku'])}</g:id>
    <g:title>{e(it['nom'])}</g:title>
    <g:description>{e(desc[:4900])}</g:description>
    <g:link>{BASE}{it['url']}</g:link>
    <g:image_link>{BASE}{it['image_produit_png']}</g:image_link>
    <g:availability>in_stock</g:availability>
    <g:price>{it['prix_ttc']:.2f} EUR</g:price>
    <g:brand>Canapoil</g:brand>
    <g:condition>new</g:condition>
    <g:identifier_exists>no</g:identifier_exists>
    <g:google_product_category>{cat}</g:google_product_category>
    <g:shipping_weight>{it['poids_g']} g</g:shipping_weight>
    <g:shipping><g:country>FR</g:country><g:service>Point relais</g:service><g:price>{'0.00' if gratuit else f"{liv['frais_ttc']:.2f}"} EUR</g:price><g:min_handling_time>0</g:min_handling_time><g:max_handling_time>1</g:max_handling_time><g:min_transit_time>2</g:min_transit_time><g:max_transit_time>5</g:max_transit_time></g:shipping>
{'    <g:is_bundle>yes</g:is_bundle>' + chr(10) if it['type'] == 'kit' else ''}  </item>
"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
<channel>
  <title>Canapoil</title>
  <link>{BASE}/</link>
  <description>Catalogue Canapoil, généré depuis strategie/brand.json le {AUJOURDHUI.isoformat()}</description>
{items}</channel>
</rss>
"""
    ecrire(SITE / "flux" / "google-merchant.xml", xml)


def placeholders_readme():
    trouve = {}
    for p in PAGES:
        txt = (SITE / p["fichier"]).read_text(encoding="utf-8")
        for m in sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", txt))):
            trouve.setdefault(m, []).append(p["url"])
    descriptions = {
        "{{RAISON_SOCIALE}}": "Dénomination sociale de la société (ou « NOM Prénom EI » en micro-entreprise)",
        "{{FORME_JURIDIQUE}}": "SASU, EURL, SARL… (supprimer la mention du capital en micro-entreprise)",
        "{{CAPITAL}}": "Montant du capital social, par exemple « 1 000 € »",
        "{{ADRESSE}}": "Adresse postale du siège",
        "{{SIREN}}": "Numéro SIREN (9 chiffres)",
        "{{RCS}}": "« RCS Ville 123 456 789 » (ou RNE pour un entrepreneur individuel)",
        "{{TVA_INTRACOM}}": "Numéro de TVA intracommunautaire ; en franchise sans numéro, supprimer la ligne et ajouter « TVA non applicable, art. 293 B du CGI »",
        "{{EMAIL}}": "Adresse e-mail du service client",
        "{{TELEPHONE}}": "Numéro non surtaxé",
        "{{HORAIRES_SERVICE_CLIENT}}": "Jours et horaires, par exemple « du lundi au vendredi, de 9 h à 18 h »",
        "{{DIRECTEUR_PUBLICATION}}": "Nom du représentant légal",
        "{{HEBERGEUR}}": "Raison sociale, adresse postale et téléphone de l'hébergeur (Netlify ou Cloudflare), recopiés depuis ses conditions en vigueur",
        "{{MEDIATEUR}}": "Nom, adresse et site du médiateur après adhésion (par exemple CM2C)",
        "{{IDU_EMBALLAGES}}": "Identifiant unique REP emballages (FR…) attribué après adhésion à Léko ou Citeo",
        "{{ADRESSE_RETOUR}}": "Adresse en France où les clients renvoient les produits",
        "{{FABRICANT_ROULEAU}}": "Nom, adresse postale et e-mail du fabricant du rouleau (dossier fournisseur)",
        "{{FABRICANT_GANT}}": "Idem pour le gant",
        "{{FABRICANT_RACLETTE}}": "Idem pour la raclette",
        "{{FABRICANT_TAPIS}}": "Idem pour le tapis de fenêtre",
    }
    lignes = ["| Variable | À remplacer par | Pages concernées |", "|---|---|---|"]
    for k in sorted(trouve, key=lambda x: list(descriptions).index(x) if x in descriptions else 99):
        urls = trouve[k]
        u = ", ".join(f"`{x}`" for x in urls[:6]) + (f" et {len(urls) - 6} autres" if len(urls) > 6 else "")
        lignes.append(f"| `{k}` | {descriptions.get(k, 'À compléter')} | {u} |")
    tableau = "\n".join(lignes)
    readme = SITE / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        t = re.sub(r"<!-- PLACEHOLDERS:DEBUT -->.*<!-- PLACEHOLDERS:FIN -->",
                   "<!-- PLACEHOLDERS:DEBUT -->\n" + tableau + "\n<!-- PLACEHOLDERS:FIN -->", t, flags=re.S)
        readme.write_text(t, encoding="utf-8")
    return trouve


def document_cgv():
    """Version imprimable des CGV (jointe en PDF à l'e-mail de confirmation : support durable)."""
    meta, corps_md = MD.lire_entete((ICI / "contenus" / "cgv.md").read_text(encoding="utf-8"))
    corps = MD.convertir(corps_md, "site").replace('href="/', f'href="{BASE}/')
    doc = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>Conditions générales de vente Canapoil</title>
<style>
@font-face{{font-family:"Fraunces";src:url("../assets/fonts/fraunces-latin.woff2") format("woff2");font-weight:100 900}}
@font-face{{font-family:"DM Sans";src:url("../assets/fonts/dm-sans-latin.woff2") format("woff2");font-weight:100 1000}}
@page{{size:A4;margin:18mm 16mm}}
body{{font-family:"DM Sans",Arial,sans-serif;font-size:10.5pt;line-height:1.45;color:#2B211B}}
h1,h2,h3{{font-family:"Fraunces",Georgia,serif;line-height:1.2;break-after:avoid}}
h1{{font-size:22pt;color:#B4492A;margin:0 0 4pt}}h2{{font-size:13pt;margin:16pt 0 6pt}}h3{{font-size:11pt}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #E3D6C6;padding:4pt 6pt;text-align:left;vertical-align:top}}
blockquote{{margin:0;padding:6pt 10pt;border-left:3pt solid #E7D5BF;font-size:9.5pt}}a{{color:#8E3820}}
.formulaire-type{{border:1px solid #E3D6C6;padding:8pt 12pt}}
</style></head><body>
<p><strong>canapoil</strong> · {e(meta['titre'])} · document remis avec la confirmation de commande</p>
<h1>{e(meta['titre'])}</h1>
{corps}
</body></html>
"""
    ecrire(SITE / "documents" / "cgv.html", doc)


def pages_info_shopify():
    """Pages informatives prêtes à coller dans Shopify (Boutique en ligne > Pages)."""
    dossier = RACINE / "shopify-kit" / "pages"
    dossier.mkdir(parents=True, exist_ok=True)
    def entete(titre, ou):
        return (f"<!--\n  {titre} — contenu prêt à coller dans Shopify.\n  Où : {ou}.\n"
                "  Comment : ouvrir l'éditeur de la page, cliquer sur « < > » (afficher le HTML), coller ce qui suit.\n"
                "  Avant publication : remplacer chaque variable {{...}}.\n-->\n")
    faq = ""
    for titre, qs in FAQ_GENERALE:
        faq += f"<h2>{e(titre)}</h2>" + "".join(f"<h3>{e(q)}</h3><p>{e(r)}</p>" for q, r in qs)
    for p in CAT["produits"]:
        faq += f"<h2>{e(p['nom'])}</h2>" + "".join(f"<h3>{e(q['q'])}</h3><p>{e(q['r'])}</p>" for q in p["faq"])
    faq = faq.replace("en bas de chaque page", "en bas de chaque page (lien vers /pages/retractation)")
    (dossier / "page-faq.html").write_text(entete("Questions fréquentes", "Boutique en ligne > Pages > Ajouter, titre « Questions fréquentes », adresse /pages/faq") + faq + "\n", encoding="utf-8")
    engag = "".join(f"<li><strong>{e(t)}</strong> : {e(d)}</li>" for _, t, d in ENGAGEMENTS)
    apropos = (
        f"<p>{e(M['promesse'])}</p>"
        "<h2>Pourquoi nous existons</h2><p>En France, 16,6 millions de chats et 9,6 millions de chiens partagent la vie de leurs maîtres, et souvent leur canapé (baromètre FACCO-Odoxa 2026). Le pull noir couvert de poils avant de sortir, le plaid à secouer avant l'arrivée des invités, les sièges de la voiture après la balade : Canapoil sélectionne des outils simples pour ces moments-là.</p>"
        "<h2>Comment nous travaillons</h2><p>Nous comparons plusieurs fournisseurs sur échantillon, nous testons chaque produit sur de vrais tissus et nous filmons le résultat, y compris là où il marche moins bien. Les produits retenus sont fabriqués en Chine, importés par lot, contrôlés, étiquetés à notre nom avec une notice en français, puis expédiés depuis la France.</p>"
        f"<h2>Nos engagements</h2><ul>{engag}</ul>"
        "<p>Canapoil est une marque de {{RAISON_SOCIALE}}, {{ADRESSE}}. Toutes nos coordonnées figurent dans les <a href=\"/policies/legal-notice\">mentions légales</a>.</p>"
    )
    (dossier / "page-a-propos.html").write_text(entete("À propos", "Boutique en ligne > Pages > Ajouter, titre « À propos », adresse /pages/a-propos") + apropos + "\n", encoding="utf-8")
    contact = (
        "<p>Une question avant d'acheter, un colis en retard, un produit qui ne convient pas : nous répondons sous 24 heures ouvrées en moyenne, 48 heures au plus.</p>"
        "<ul><li><strong>E-mail</strong> : {{EMAIL}}</li><li><strong>Téléphone</strong> : {{TELEPHONE}} (appel non surtaxé), {{HORAIRES_SERVICE_CLIENT}}</li>"
        "<li><strong>Courrier</strong> : {{RAISON_SOCIALE}}, {{ADRESSE}}</li></ul>"
        "<p><strong>Avant d'acheter</strong> : envoyez-nous une photo de votre tissu, nous vous disons franchement si le rouleau convient.</p>"
        "<p><strong>Rétractation</strong> : <a href=\"/pages/retractation\">renoncer au contrat ici</a>.</p>"
        "<p>En cas de litige non résolu, vous pouvez saisir gratuitement le médiateur de la consommation : {{MEDIATEUR}}.</p>"
    )
    (dossier / "page-contact.html").write_text(entete("Contact", "Boutique en ligne > Pages > Contact (modèle « page.contact » qui affiche le formulaire de contact du thème)") + contact + "\n", encoding="utf-8")
    retract = (
        "<p>Vous disposez de 30 jours après la réception de votre commande pour vous rétracter : 14 jours prévus par la loi, plus 16 jours que nous ajoutons. Aucun motif n'est demandé.</p>"
        "<p>Remplissez le formulaire ci-dessous (nom, prénom, numéro de commande, adresse e-mail) et cliquez sur « confirmer la rétractation ». Vous recevez par e-mail un accusé de réception reprenant votre déclaration, avec sa date et son heure.</p>"
        "<p>Ensuite : renvoyez le produit au plus tard 14 jours après votre déclaration à {{ADRESSE_RETOUR}}. Les frais de renvoi sont à votre charge, sauf produit défectueux ou erroné (environ 5 à 7 € en point relais). Nous vous remboursons au plus tard 14 jours après votre déclaration, frais de livraison initiaux inclus.</p>"
        "<p>Vous pouvez aussi utiliser le formulaire type figurant dans notre <a href=\"/policies/refund-policy\">politique de retours</a> ou nous écrire à {{EMAIL}}.</p>"
    )
    (dossier / "page-retractation.html").write_text(entete("Renoncer au contrat (rétractation en ligne)", "Boutique en ligne > Pages > Ajouter, titre « Renoncer au contrat », adresse /pages/retractation, modèle « page.retractation » qui contient la section shopify-kit/theme/sections/canapoil-retractation.liquid") + retract + "\n", encoding="utf-8")


# ===================================================================== principal


def main():
    global CAT, IDX, ALTS
    ALTS = generer_illustrations()
    CAT = construire_catalogue(ALTS)
    IDX = {x["id"]: x for x in CAT["produits"] + CAT["kits"]}
    ecrire(SITE / "data" / "products.json", json.dumps(CAT, ensure_ascii=False, indent=2) + "\n")
    page_accueil()
    page_boutique()
    for p in CAT["produits"]:
        page_produit(p)
    for k in CAT["kits"]:
        page_kit(k)
    page_panier()
    page_commande()
    page_merci()
    page_faq()
    page_a_propos()
    page_contact()
    page_retractation()
    pages_legales()
    page_404()
    sitemap_robots()
    flux_merchant()
    document_cgv()
    trouve = placeholders_readme()
    SHOP.generer(BRAND, CAT, IDX, RACINE / "shopify-kit", ICI / "contenus", BASE)
    pages_info_shopify()
    print(f"{len(PAGES)} pages, {len(CAT['produits'])} produits, {len(CAT['kits'])} kits, {len(trouve)} variables {{...}}")


ALTS = {}

if __name__ == "__main__":
    main()
