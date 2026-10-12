#!/usr/bin/env python3
"""Gabarits imprimables de Canapoil, générés depuis strategie/brand.json.

Produit dans ce dossier :
  - etiquette-importateur.html : planche A4 de 24 étiquettes (63,5 × 33,9 mm) par produit,
    « Importé par » + référence + lot (GPSR art. 11 : coordonnées de l'importateur sur le produit) ;
  - notice-<slug>.html : notice d'utilisation en français par produit (mode d'emploi,
    avertissements, entretien, fabricant, importateur, référence) ;
  - insert-colis.html : carte glissée dans chaque colis (mode d'emploi en vidéo, 30 jours pour
    changer d'avis, lien « renoncer au contrat ici », service client).
Les variables {{...}} non remplies dans brand.json → identite restent visibles : n'imprimez
qu'une fois l'identité et les fabricants saisis. Usage : python3 docs/gabarits/generer_gabarits.py
Impression : navigateur > Imprimer > A4, marges « aucune », échelle 100 %.
"""
import html
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
BRAND = json.loads((ICI.parent.parent / "strategie" / "brand.json").read_text(encoding="utf-8"))
ID = {k: v for k, v in BRAND["identite"].items() if not k.startswith("_")}
e = lambda s: html.escape(str(s))  # noqa: E731


def remplir(t):
    for k, v in ID.items():
        if v:
            t = t.replace("{{" + k + "}}", str(v))
    return t


STYLE = """<style>
@page{size:A4;margin:0}
body{margin:0;font-family:"DM Sans",Arial,sans-serif;color:#2B211B}
h1,h2{font-family:Georgia,serif;color:#B4492A;margin:0 0 6px}
.planche{width:210mm;height:297mm;padding:13mm 7mm;box-sizing:border-box;display:grid;grid-template-columns:repeat(3,63.5mm);grid-auto-rows:33.9mm;column-gap:2.5mm;page-break-after:always}
.etiquette{border:0.2mm dashed #ccc;padding:2mm 3mm;box-sizing:border-box;font-size:7pt;line-height:1.25;overflow:hidden}
.etiquette strong{font-size:8pt}
.page{width:210mm;min-height:297mm;padding:14mm 16mm;box-sizing:border-box;page-break-after:always;font-size:10pt;line-height:1.45}
.encadre{border:1px solid #E3D6C6;border-radius:3mm;padding:3mm 4mm;margin:4mm 0}
.alerte{border-left:2mm solid #B42318;padding-left:3mm}
.insert{width:105mm;height:148mm;padding:9mm;box-sizing:border-box;border:0.2mm dashed #ccc;font-size:9pt;line-height:1.4;display:inline-block;vertical-align:top}
.note{font-size:8pt;color:#6A5B50}
</style>"""


def doc(titre, corps):
    return f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{e(titre)}</title>{STYLE}</head><body>{corps}</body></html>\n'


def etiquettes():
    planches = ""
    for p in BRAND["produits"]:
        txt = (f"<strong>{e(p['nom'])}</strong><br>Réf. {e(p['sku'])} · Lot ________<br>"
               f"Importé par {e('{{RAISON_SOCIALE}}')}<br>{e('{{ADRESSE}}')}<br>{e('{{EMAIL}}')}<br>Fabriqué en Chine")
        planches += '<div class="planche">' + "".join(f'<div class="etiquette">{txt}</div>' for _ in range(24)) + "</div>"
    return doc("Étiquettes importateur Canapoil", planches)


def notice(p):
    g = p["gpsr"]
    c = p.get("caracteristiques", {})
    av = "".join(f"<li>{e(a)}</li>" for a in g["avertissements"])
    lignes = "".join(f"<tr><th align='left'>{lib}</th><td>{e(c[k])}</td></tr>" for k, lib in
                     (("matieres", "Matières"), ("dimensions", "Dimensions"), ("taille", "Taille"), ("poids", "Poids"), ("entretien", "Entretien")) if k in c)
    corps = f"""<div class="page">
<p class="note">canapoil · notice d'utilisation · réf. {e(p['sku'])} · à glisser dans chaque colis</p>
<h1>{e(p['nom'])}</h1>
<p>{e(p['description_courte'])}</p>
<h2>Mode d'emploi</h2><p>{e(g['instructions'])}</p>
<div class="encadre alerte"><h2>Avertissements de sécurité</h2><ul>{av}</ul></div>
<h2>Caractéristiques et entretien</h2><table>{lignes}</table>
<div class="encadre"><h2>Fabricant et importateur</h2>
<p><strong>Fabricant :</strong> {e(g['fabricant'])}<br><strong>Importateur et personne responsable dans l'Union européenne :</strong> {e(g['responsable_ue'])}<br><strong>Identification :</strong> {e(g['identification'])}</p>
<p>Un problème de sécurité avec ce produit ? Écrivez à {e('{{EMAIL}}')} en indiquant la référence et le lot.</p></div>
<p class="note">Fabriqué en Chine. Notice conforme au règlement (UE) 2023/988 (sécurité générale des produits). Avertissements {e(g['avertissements_statut'][0].lower() + g['avertissements_statut'][1:])} : relire la notice du fabricant avant impression.</p>
</div>"""
    return doc(f"Notice {p['nom']}", corps)


def insert():
    carte = f"""<div class="insert"><h1>Merci !</h1>
<p>Votre colis Canapoil a été préparé à la main en France.</p>
<p><strong>Bien démarrer en 30 secondes</strong> : la vidéo de démonstration est sur canapoil.fr/faq/ et sur notre compte TikTok @canapoil.</p>
<p><strong>30 jours pour changer d'avis</strong> après réception (14 jours prévus par la loi + 16 jours offerts). Pour vous rétracter : canapoil.fr/retractation/ (« renoncer au contrat ici »).</p>
<p><strong>Une question, un défaut ?</strong> {e('{{EMAIL}}')} : réponse sous 48 heures ouvrées.</p>
<p class="note">{e('{{RAISON_SOCIALE}}')} · {e('{{ADRESSE}}')} · Produits fabriqués en Chine, contrôlés et expédiés depuis la France. Emballage : consignes de tri sur info-tri.fr.</p></div>"""
    return doc("Carte insérée dans les colis Canapoil", '<div class="page">' + carte * 4 + "</div>")


def main():
    (ICI / "etiquette-importateur.html").write_text(remplir(etiquettes()), encoding="utf-8")
    for p in BRAND["produits"] + BRAND.get("challengers", []):
        (ICI / f"notice-{p['slug']}.html").write_text(remplir(notice(p)), encoding="utf-8")
    (ICI / "insert-colis.html").write_text(remplir(insert()), encoding="utf-8")
    restes = sum(f.read_text(encoding="utf-8").count("{{") for f in ICI.glob("*.html"))
    print(f"Gabarits écrits dans {ICI} ; {restes} variable(s) {{{{...}}}} à remplir dans brand.json → identite avant impression")


if __name__ == "__main__":
    main()
