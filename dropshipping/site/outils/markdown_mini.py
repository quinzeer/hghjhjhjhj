"""Convertisseur Markdown minimal pour les pages légales (aucune dépendance).

Gère : titres, paragraphes, listes à puces et numérotées, tableaux, citations,
gras, code en ligne, liens, règles horizontales, lignes HTML brutes et blocs
de variante « ::: site » / « ::: shopify » terminés par « ::: ».
Les liens « lien:cle » sont résolus selon la cible (site statique ou Shopify).
Les variables {{...}} sont conservées telles quelles (visibles à remplir).
"""

import html
import re

LIENS = {
    "site": {
        "cgv": "/cgv/",
        "livraison": "/livraison/",
        "retours": "/retours-retractation/",
        "retractation": "/retractation/",
        "confidentialite": "/confidentialite/",
        "cookies": "/cookies/",
        "contact": "/contact/",
        "mentions": "/mentions-legales/",
        "faq": "/faq/",
    },
    "shopify": {
        "cgv": "/policies/terms-of-service",
        "livraison": "/policies/shipping-policy",
        "retours": "/policies/refund-policy",
        "retractation": "/pages/retractation",
        "confidentialite": "/policies/privacy-policy",
        "cookies": "/pages/cookies",
        "contact": "/pages/contact",
        "mentions": "/policies/legal-notice",
        "faq": "/pages/faq",
    },
}


def lire_entete(texte):
    """Sépare l'en-tête « --- clé: valeur --- » du corps."""
    meta = {}
    if texte.startswith("---"):
        fin = texte.index("\n---", 3)
        for ligne in texte[3:fin].strip().splitlines():
            if ":" in ligne:
                k, v = ligne.split(":", 1)
                meta[k.strip()] = v.strip()
        texte = texte[fin + 4 :]
    return meta, texte.lstrip("\n")


def filtrer_variantes(texte, cible):
    sortie, garder = [], True
    for ligne in texte.splitlines():
        s = ligne.strip()
        if s.startswith("::: ") and s[4:].strip() in ("site", "shopify"):
            garder = s[4:].strip() == cible
            continue
        if s == ":::":
            garder = True
            continue
        if garder:
            sortie.append(ligne)
    return "\n".join(sortie)


def en_ligne(t, cible):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r'<code class="code">\1</code>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)

    def lien(m):
        texte, url = m.group(1), m.group(2)
        if url.startswith("lien:"):
            url = LIENS[cible][url[5:]]
        attrs = ' rel="noopener"' if url.startswith("http") else ""
        return f'<a href="{url}"{attrs}>{texte}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lien, t)
    return t


def convertir(texte, cible="site", decalage_titres=0):
    texte = filtrer_variantes(texte, cible)
    lignes = texte.splitlines()
    out, i, n = [], 0, len(lignes)

    def titre(niv, contenu):
        niv = min(6, niv + decalage_titres)
        ident = re.sub(r"[^a-z0-9]+", "-", contenu.lower()).strip("-")[:60]
        return f'<h{niv} id="{ident}">{en_ligne(contenu, cible)}</h{niv}>'

    while i < n:
        l = lignes[i]
        s = l.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            out.append(titre(len(m.group(1)), m.group(2)))
            i += 1
            continue
        if s == "---":
            out.append("<hr>")
            i += 1
            continue
        if s.startswith("<") and s.endswith(">"):
            out.append(s)
            i += 1
            continue
        if s.startswith("|"):
            bloc = []
            while i < n and lignes[i].strip().startswith("|"):
                bloc.append(lignes[i].strip())
                i += 1
            cellules = [[c.strip() for c in r.strip("|").split("|")] for r in bloc]
            entete, corps = cellules[0], [r for r in cellules[2:]]
            h = '<div class="tableau-wrap"><table><thead><tr>'
            h += "".join(f'<th scope="col">{en_ligne(c, cible)}</th>' for c in entete)
            h += "</tr></thead><tbody>"
            for r in corps:
                h += "<tr>" + "".join(f"<td>{en_ligne(c, cible)}</td>" for c in r) + "</tr>"
            h += "</tbody></table></div>"
            out.append(h)
            continue
        if s.startswith(">"):
            bloc = []
            while i < n and lignes[i].strip().startswith(">"):
                bloc.append(lignes[i].strip()[1:].strip())
                i += 1
            paras, cur = [], []
            for b in bloc:
                if not b:
                    if cur:
                        paras.append(" ".join(cur))
                        cur = []
                else:
                    cur.append(b)
            if cur:
                paras.append(" ".join(cur))
            out.append("<blockquote>" + "".join(f"<p>{en_ligne(p, cible)}</p>" for p in paras) + "</blockquote>")
            continue
        if re.match(r"^[-*]\s+", s):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lignes[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lignes[i]).strip())
                i += 1
                while i < n and lignes[i].startswith("  ") and lignes[i].strip() and not re.match(r"^\s*[-*]\s+", lignes[i]):
                    items[-1] += " " + lignes[i].strip()
                    i += 1
            out.append("<ul>" + "".join(f"<li>{en_ligne(x, cible)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lignes[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lignes[i]).strip())
                i += 1
            out.append("<ol>" + "".join(f"<li>{en_ligne(x, cible)}</li>" for x in items) + "</ol>")
            continue
        para = [s]
        i += 1
        while i < n:
            t = lignes[i].strip()
            if not t or re.match(r"^(#{1,6}\s|[-*]\s|\d+\.\s|\||>|<|---$|:::)", t):
                break
            para.append(t)
            i += 1
        out.append(f"<p>{en_ligne(' '.join(para), cible)}</p>")
    return "\n".join(out)
