"""Illustrations SVG de la marque Canapoil.

Aucune photo réelle n'existe encore : ces dessins vectoriels aux couleurs de
brand.json servent de visuels provisoires. Ils n'utilisent aucun attribut
« style » (compatibles avec la Content-Security-Policy stricte du site).
Chaque fonction renvoie un fragment <g> ; `document()` l'enveloppe dans un SVG.
"""

C = {
    "primaire": "#B4492A",
    "primaire_fonce": "#8E3820",
    "primaire_clair": "#D9785A",
    "primaire_pale": "#F3D9CE",
    "secondaire": "#2F4A3C",
    "sauge": "#4F6E5D",
    "sauge_moyen": "#6F8E7C",
    "sauge_clair": "#A9BFB1",
    "sauge_pale": "#DDE7E0",
    "fond": "#FAF5EE",
    "creme": "#F1E6D8",
    "sable": "#E7D5BF",
    "kraft": "#CDA77E",
    "kraft_fonce": "#A9824F",
    "texte": "#2B211B",
    "brun": "#6A5B50",
    "accent": "#E3A93B",
    "accent_fonce": "#C4882A",
    "accent_pale": "#F6DDAA",
    "blanc": "#FFFFFF",
    "bois": "#8A5A3B",
}


def document(contenu, largeur=800, hauteur=600, titre="", fond=True, couleur_fond=None):
    """Enveloppe un fragment dans un document SVG autonome et accessible."""
    t = f"<title>{titre}</title>" if titre else ""
    f = (
        f'<rect width="{largeur}" height="{hauteur}" fill="{couleur_fond or C["blanc"]}"/>'
        if fond
        else ""
    )
    role = 'role="img" ' if titre else 'aria-hidden="true" '
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur} {hauteur}" '
        f'width="{largeur}" height="{hauteur}" {role}>{t}{f}{contenu}</svg>\n'
    )


def ombre(cx, cy, rx, ry=None, opacite=0.12):
    ry = ry or rx * 0.16
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{C["texte"]}" opacity="{opacite}"/>'


def tache(cx, cy, r, couleur):
    """Forme organique douce servant de fond aux objets."""
    p = (
        f"M{cx - r},{cy} "
        f"C{cx - r},{cy - r * 0.62} {cx - r * 0.55},{cy - r * 1.02} {cx + r * 0.05},{cy - r * 0.98} "
        f"C{cx + r * 0.7},{cy - r * 0.94} {cx + r * 1.04},{cy - r * 0.5} {cx + r},{cy + r * 0.05} "
        f"C{cx + r * 0.96},{cy + r * 0.66} {cx + r * 0.5},{cy + r * 0.98} {cx - r * 0.06},{cy + r * 0.96} "
        f"C{cx - r * 0.66},{cy + r * 0.94} {cx - r},{cy + r * 0.6} {cx - r},{cy} Z"
    )
    return f'<path d="{p}" fill="{couleur}"/>'


def poils(points, couleur=None, epaisseur=3):
    """Petits poils incurvés : liste de (x, y, angle)."""
    couleur = couleur or C["accent"]
    out = []
    for x, y, a in points:
        out.append(
            f'<path d="M0,0 q6,-5 13,-2" transform="translate({x},{y}) rotate({a})" '
            f'fill="none" stroke="{couleur}" stroke-width="{epaisseur}" stroke-linecap="round"/>'
        )
    return "".join(out)


# ---------------------------------------------------------------- objets


def rouleau(x=0, y=0, echelle=1.0, rotation=0, clapet_ouvert=False):
    """Rouleau anti-poils réutilisable : poignée en arc, coque terracotta,
    bande textile visible dessous. Origine au centre de la coque."""
    hach = "".join(
        f'<path d="M{-104 + i * 16},96 l10,-44" stroke="{C["sauge_moyen"]}" stroke-width="5" stroke-linecap="round"/>'
        for i in range(14)
    )
    if clapet_ouvert:
        clapet = (
            f'<g transform="translate(118,8) rotate(38)">'
            f'<rect x="-6" y="-6" width="96" height="62" rx="18" fill="{C["primaire_fonce"]}"/>'
            f'<rect x="4" y="2" width="76" height="12" rx="6" fill="{C["primaire"]}"/></g>'
            # boule de poils qui tombe
            f'<g transform="translate(205,105)">'
            f'<circle r="30" fill="{C["accent"]}"/>'
            f'<circle cx="-12" cy="-8" r="16" fill="{C["accent_pale"]}" opacity=".7"/>'
            f'{poils([(-34, -6, -30), (18, -30, 20), (24, 14, 70), (-20, 24, 150), (-4, -34, -60)], C["accent_fonce"], 3.5)}'
            f"</g>"
        )
    else:
        clapet = (
            f'<rect x="-22" y="-6" width="44" height="16" rx="8" fill="{C["fond"]}"/>'
        )
    return (
        f'<g transform="translate({x},{y}) rotate({rotation}) scale({echelle})">'
        # poignée
        f'<path d="M-72,-40 C-74,-160 74,-160 72,-40" fill="none" stroke="{C["texte"]}" stroke-width="32" stroke-linecap="round"/>'
        f'<path d="M-40,-121 C-16,-136 16,-136 40,-121" fill="none" stroke="{C["brun"]}" stroke-width="7" stroke-linecap="round"/>'
        # bande textile
        f'<rect x="-122" y="40" width="244" height="64" rx="32" fill="{C["secondaire"]}"/>'
        f"{hach}"
        # coque
        f'<rect x="-134" y="-58" width="268" height="122" rx="48" fill="{C["primaire"]}"/>'
        f'<rect x="-112" y="-46" width="224" height="22" rx="11" fill="{C["primaire_clair"]}" opacity=".55"/>'
        f'<path d="M-130,24 H130" stroke="{C["primaire_fonce"]}" stroke-width="5"/>'
        f"{clapet}"
        # embouts
        f'<circle cx="-134" cy="64" r="15" fill="{C["texte"]}"/>'
        f'<circle cx="134" cy="64" r="15" fill="{C["texte"]}"/>'
        f"</g>"
    )


def chat_assis(x=0, y=0, echelle=1.0, miroir=False, couleur=None, rayures=None):
    """Chat roux assis, yeux mi-clos. Origine au bas du corps."""
    couleur = couleur or C["accent"]
    rayures = rayures or C["accent_fonce"]
    sx = -echelle if miroir else echelle
    return (
        f'<g transform="translate({x},{y}) scale({sx},{echelle})">'
        # queue
        f'<path d="M58,-18 C120,-10 132,-70 104,-96" fill="none" stroke="{couleur}" stroke-width="22" stroke-linecap="round"/>'
        f'<path d="M110,-62 l14,-6 M116,-80 l14,-2" stroke="{rayures}" stroke-width="6" stroke-linecap="round"/>'
        # corps
        f'<path d="M-70,0 C-82,-70 -58,-140 0,-142 C58,-140 82,-70 70,0 Z" fill="{couleur}"/>'
        f'<path d="M-30,-4 C-34,-50 -20,-92 0,-96 C20,-92 34,-50 30,-4 Z" fill="{C["accent_pale"]}"/>'
        f'<path d="M-62,-62 q14,4 22,14 M-66,-36 q14,2 22,12 M62,-62 q-14,4 -22,14 M66,-36 q-14,2 -22,12" fill="none" stroke="{rayures}" stroke-width="6" stroke-linecap="round"/>'
        # pattes
        f'<ellipse cx="-30" cy="-4" rx="22" ry="12" fill="{C["accent_pale"]}"/>'
        f'<ellipse cx="30" cy="-4" rx="22" ry="12" fill="{C["accent_pale"]}"/>'
        # tête
        f'<path d="M-62,-206 L-50,-262 L-14,-232 Z" fill="{couleur}"/>'
        f'<path d="M62,-206 L50,-262 L14,-232 Z" fill="{couleur}"/>'
        f'<path d="M-52,-214 L-47,-246 L-26,-230 Z" fill="{C["primaire_pale"]}"/>'
        f'<path d="M52,-214 L47,-246 L26,-230 Z" fill="{C["primaire_pale"]}"/>'
        f'<ellipse cx="0" cy="-190" rx="66" ry="56" fill="{couleur}"/>'
        f'<path d="M-14,-242 l4,18 M0,-246 v20 M14,-242 l-4,18" stroke="{rayures}" stroke-width="6" stroke-linecap="round"/>'
        # visage
        f'<path d="M-36,-192 q12,10 24,0 M12,-192 q12,10 24,0" fill="none" stroke="{C["texte"]}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M-8,-172 h16 l-8,9 Z" fill="{C["primaire"]}"/>'
        f'<path d="M0,-163 q-6,10 -14,8 M0,-163 q6,10 14,8" fill="none" stroke="{C["texte"]}" stroke-width="3.5" stroke-linecap="round"/>'
        f'<path d="M-24,-170 l-46,-8 M-24,-164 l-46,4 M24,-170 l46,-8 M24,-164 l46,4" stroke="{C["texte"]}" stroke-width="2.5" stroke-linecap="round" opacity=".55"/>'
        f'<ellipse cx="-40" cy="-174" rx="10" ry="6" fill="{C["primaire_clair"]}" opacity=".45"/>'
        f'<ellipse cx="40" cy="-174" rx="10" ry="6" fill="{C["primaire_clair"]}" opacity=".45"/>'
        f"</g>"
    )


def chat_couche(x=0, y=0, echelle=1.0, couleur=None, rayures=None):
    """Chat couché en boule (pour le tapis de fenêtre). Origine au bas."""
    couleur = couleur or C["accent"]
    rayures = rayures or C["accent_fonce"]
    return (
        f'<g transform="translate({x},{y}) scale({echelle})">'
        f'<path d="M-150,0 C-160,-70 -90,-112 -10,-112 C80,-112 150,-80 150,-26 C150,-6 140,0 130,0 Z" fill="{couleur}"/>'
        f'<path d="M-40,-108 q8,26 0,52 M10,-112 q8,28 0,56 M60,-104 q8,26 0,48" fill="none" stroke="{rayures}" stroke-width="7" stroke-linecap="round"/>'
        # queue enroulée devant
        f'<path d="M140,-10 C120,16 -40,22 -96,6" fill="none" stroke="{couleur}" stroke-width="26" stroke-linecap="round"/>'
        f'<path d="M-60,12 l-4,12 M-30,14 l-2,12" stroke="{rayures}" stroke-width="6" stroke-linecap="round"/>'
        # tête posée
        f'<path d="M-200,-70 L-196,-122 L-160,-94 Z" fill="{couleur}"/>'
        f'<path d="M-118,-82 L-112,-130 L-82,-96 Z" fill="{couleur}"/>'
        f'<path d="M-192,-80 L-190,-108 L-170,-92 Z" fill="{C["primaire_pale"]}"/>'
        f'<path d="M-114,-90 L-110,-116 L-94,-98 Z" fill="{C["primaire_pale"]}"/>'
        f'<ellipse cx="-150" cy="-58" rx="62" ry="50" fill="{couleur}"/>'
        f'<path d="M-182,-60 q10,8 20,0 M-140,-60 q10,8 20,0" fill="none" stroke="{C["texte"]}" stroke-width="4.5" stroke-linecap="round"/>'
        f'<path d="M-158,-44 h14 l-7,8 Z" fill="{C["primaire"]}"/>'
        f'<path d="M-172,-40 l-40,-4 M-172,-36 l-40,6 M-130,-40 l40,-6 M-130,-36 l40,4" stroke="{C["texte"]}" stroke-width="2.2" stroke-linecap="round" opacity=".5"/>'
        f'<ellipse cx="-104" cy="-6" rx="26" ry="11" fill="{C["accent_pale"]}"/>'
        f"</g>"
    )


def canape(x=0, y=0, echelle=1.0, avec_poils=True, bande_propre=(-40, 120)):
    """Canapé vert sauge vu de face, coussin terracotta. Origine au sol, centre."""
    poils_assise = []
    if avec_poils:
        import random

        rnd = random.Random(7)
        for _ in range(46):
            px = rnd.uniform(-250, 250)
            py = rnd.uniform(-150, -100)
            if bande_propre and bande_propre[0] < px < bande_propre[1]:
                continue
            poils_assise.append((px, py, rnd.uniform(-60, 60)))
        for _ in range(22):
            px = rnd.uniform(-240, 240)
            py = rnd.uniform(-300, -190)
            poils_assise.append((px, py, rnd.uniform(-60, 60)))
    p = poils(poils_assise, C["accent_pale"], 3)
    return (
        f'<g transform="translate({x},{y}) scale({echelle})">'
        # pieds
        f'<rect x="-262" y="-14" width="18" height="30" rx="4" fill="{C["bois"]}"/>'
        f'<rect x="244" y="-14" width="18" height="30" rx="4" fill="{C["bois"]}"/>'
        # dossier
        f'<rect x="-270" y="-330" width="540" height="230" rx="56" fill="{C["sauge"]}"/>'
        # assise
        f'<rect x="-290" y="-162" width="580" height="150" rx="40" fill="{C["sauge_moyen"]}"/>'
        f'<path d="M0,-158 V-20" stroke="{C["sauge"]}" stroke-width="5"/>'
        f'<rect x="-290" y="-162" width="580" height="30" rx="15" fill="{C["sauge_clair"]}" opacity=".35"/>'
        # accoudoirs
        f'<rect x="-340" y="-230" width="100" height="220" rx="44" fill="{C["secondaire"]}"/>'
        f'<rect x="240" y="-230" width="100" height="220" rx="44" fill="{C["secondaire"]}"/>'
        f'<rect x="-326" y="-218" width="72" height="22" rx="11" fill="{C["sauge"]}" opacity=".7"/>'
        f'<rect x="254" y="-218" width="72" height="22" rx="11" fill="{C["sauge"]}" opacity=".7"/>'
        # coussin
        f'<g transform="translate(-170,-200) rotate(-8)">'
        f'<rect x="-62" y="-62" width="124" height="118" rx="30" fill="{C["primaire"]}"/>'
        f'<path d="M-40,-2 H40" stroke="{C["primaire_fonce"]}" stroke-width="4" stroke-linecap="round" opacity=".6"/>'
        f"</g>"
        f"{p}"
        f"</g>"
    )


def gant(x=0, y=0, echelle=1.0, rotation=0):
    """Gant de toilettage en silicone, picots en relief."""
    picots = []
    for row in range(5):
        for col in range(5):
            cx = -64 + col * 32 + (16 if row % 2 else 0)
            cy = -150 + row * 34
            if cx > 70:
                continue
            picots.append(
                f'<circle cx="{cx}" cy="{cy}" r="8" fill="{C["sauge_clair"]}"/>'
            )
    return (
        f'<g transform="translate({x},{y}) rotate({rotation}) scale({echelle})">'
        # pouce
        f'<path d="M-92,-70 C-150,-90 -170,-150 -130,-170 C-100,-184 -80,-150 -70,-118 Z" fill="{C["sauge"]}"/>'
        # main
        f'<path d="M-96,40 L-100,-150 C-100,-210 -60,-232 0,-232 C60,-232 100,-210 100,-150 L96,40 Z" fill="{C["sauge"]}"/>'
        f'<path d="M-70,-200 C-40,-222 40,-222 70,-200" fill="none" stroke="{C["sauge_moyen"]}" stroke-width="8" stroke-linecap="round" opacity=".7"/>'
        f'{"".join(picots)}'
        # poignet + sangle
        f'<rect x="-104" y="24" width="208" height="66" rx="18" fill="{C["secondaire"]}"/>'
        f'<rect x="-120" y="38" width="240" height="38" rx="12" fill="{C["primaire"]}"/>'
        f'<rect x="64" y="42" width="48" height="30" rx="8" fill="{C["primaire_fonce"]}"/>'
        f"</g>"
    )


def raclette(x=0, y=0, echelle=1.0, rotation=0):
    """Raclette anti-poils : manche terracotta, tête et lame dentelée."""
    dents = "".join(
        f'<path d="M{-118 + i * 16},64 l8,18 l8,-18 Z" fill="{C["sauge"]}"/>' for i in range(15)
    )
    return (
        f'<g transform="translate({x},{y}) rotate({rotation}) scale({echelle})">'
        # manche
        f'<rect x="-28" y="-260" width="56" height="230" rx="28" fill="{C["primaire"]}"/>'
        f'<rect x="-14" y="-240" width="12" height="150" rx="6" fill="{C["primaire_clair"]}" opacity=".6"/>'
        f'<circle cx="0" cy="-232" r="9" fill="{C["fond"]}"/>'
        # tête
        f'<path d="M-130,-40 C-130,-56 -116,-64 -100,-64 H100 C116,-64 130,-56 130,-40 V20 H-130 Z" fill="{C["secondaire"]}"/>'
        f'<rect x="-130" y="16" width="260" height="50" rx="10" fill="{C["sauge"]}"/>'
        f"{dents}"
        f'<path d="M-112,-30 H112" stroke="{C["sauge"]}" stroke-width="5" stroke-linecap="round" opacity=".8"/>'
        f"</g>"
    )


def tapis_fenetre(x=0, y=0, echelle=1.0, avec_chat=True):
    """Fenêtre d'hiver avec tapis thermique sur le rebord et chat couché."""
    flocons = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{C["blanc"]}"/>'
        for cx, cy, r in [
            (-230, -380, 6), (-150, -330, 4), (-60, -400, 5), (40, -350, 6), (150, -390, 4),
            (220, -320, 5), (-200, -250, 5), (-90, -220, 4), (90, -260, 5), (200, -210, 4),
            (-10, -300, 4), (120, -160, 4), (-240, -150, 4),
        ]
    )
    chat = chat_couche(40, -58, 0.86) if avec_chat else ""
    return (
        f'<g transform="translate({x},{y}) scale({echelle})">'
        # mur et cadre
        f'<rect x="-300" y="-460" width="600" height="420" rx="18" fill="{C["blanc"]}"/>'
        f'<rect x="-274" y="-436" width="548" height="372" rx="10" fill="{C["sauge_clair"]}"/>'
        f'<path d="M-274,-150 C-150,-190 -40,-140 60,-170 C150,-196 220,-160 274,-176 V-64 H-274 Z" fill="{C["sauge_pale"]}"/>'
        f"{flocons}"
        f'<rect x="-8" y="-436" width="16" height="372" fill="{C["blanc"]}"/>'
        f'<rect x="-274" y="-258" width="548" height="14" fill="{C["blanc"]}"/>'
        # rebord
        f'<rect x="-330" y="-64" width="660" height="40" rx="10" fill="{C["sable"]}"/>'
        f'<rect x="-330" y="-30" width="660" height="10" rx="5" fill="{C["kraft"]}" opacity=".5"/>'
        # tapis : couche réfléchissante + sherpa
        f'<rect x="-262" y="-82" width="524" height="26" rx="13" fill="{C["brun"]}" opacity=".35"/>'
        f'<path d="M-262,-70 C-262,-96 -240,-104 -220,-104 H220 C240,-104 262,-96 262,-70 V-62 H-262 Z" fill="{C["creme"]}"/>'
        f'<path d="M-240,-92 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0" fill="none" stroke="{C["sable"]}" stroke-width="4" stroke-linecap="round"/>'
        f"{chat}"
        f"</g>"
    )


def colis(x=0, y=0, echelle=1.0):
    """Carton kraft ouvert avec notice."""
    return (
        f'<g transform="translate({x},{y}) scale({echelle})">'
        f'<path d="M-200,-120 L-250,-190 L-20,-200 L0,-120 Z" fill="{C["kraft"]}"/>'
        f'<path d="M200,-120 L250,-190 L20,-200 L0,-120 Z" fill="{C["kraft_fonce"]}" opacity=".85"/>'
        f'<rect x="-200" y="-120" width="400" height="200" rx="8" fill="{C["kraft"]}"/>'
        f'<rect x="-200" y="-120" width="400" height="26" fill="{C["kraft_fonce"]}" opacity=".45"/>'
        f'<rect x="-60" y="-30" width="120" height="70" rx="6" fill="{C["fond"]}"/>'
        f'<text x="0" y="12" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-weight="700" font-size="30" fill="{C["primaire"]}">canapoil</text>'
        f"</g>"
    )


def notice(x=0, y=0, echelle=1.0, rotation=0):
    lignes = "".join(
        f'<rect x="-58" y="{-40 + i * 18}" width="{116 - (i % 3) * 22}" height="7" rx="3.5" fill="{C["sable"]}"/>'
        for i in range(5)
    )
    return (
        f'<g transform="translate({x},{y}) rotate({rotation}) scale({echelle})">'
        f'<rect x="-80" y="-100" width="160" height="210" rx="8" fill="{C["blanc"]}"/>'
        f'<text x="0" y="-62" text-anchor="middle" font-family="DM Sans, Arial, sans-serif" font-weight="700" font-size="20" fill="{C["texte"]}">Notice</text>'
        f'<text x="0" y="-48" text-anchor="middle" font-family="DM Sans, Arial, sans-serif" font-size="11" fill="{C["brun"]}">en français</text>'
        f'<g transform="translate(0,40)">{lignes}</g>'
        f"</g>"
    )


def fleches_va_et_vient(x, y, longueur=180, couleur=None):
    couleur = couleur or C["texte"]
    d = longueur / 2
    return (
        f'<g transform="translate({x},{y})" fill="none" stroke="{couleur}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M{-d},0 H{d}"/>'
        f'<path d="M{-d + 22},-16 L{-d},0 L{-d + 22},16"/>'
        f'<path d="M{d - 22},-16 L{d},0 L{d - 22},16"/>'
        f"</g>"
    )


def poubelle(x, y, echelle=1.0):
    return (
        f'<g transform="translate({x},{y}) scale({echelle})">'
        f'<path d="M-70,-120 H70 L58,40 C57,52 48,60 36,60 H-36 C-48,60 -57,52 -58,40 Z" fill="{C["sauge"]}"/>'
        f'<rect x="-84" y="-140" width="168" height="26" rx="13" fill="{C["secondaire"]}"/>'
        f'<rect x="-24" y="-156" width="48" height="20" rx="8" fill="{C["secondaire"]}"/>'
        f'<path d="M-30,-90 V30 M0,-90 V30 M30,-90 V30" stroke="{C["sauge_moyen"]}" stroke-width="7" stroke-linecap="round"/>'
        f"</g>"
    )


def cote(x1, y1, x2, y2, texte, decal=0, couleur=None):
    couleur = couleur or C["brun"]
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    return (
        f'<g stroke="{couleur}" stroke-width="3" stroke-linecap="round">'
        f'<path d="M{x1},{y1} L{x2},{y2}"/>'
        f'<path d="M{x1},{y1 - 12} v24 M{x2},{y2 - 12} v24"/>'
        f"</g>"
        f'<text x="{mx}" y="{my - 16 + decal}" text-anchor="middle" font-family="DM Sans, Arial, sans-serif" font-size="26" font-weight="700" fill="{C["texte"]}">{texte}</text>'
    )


# ---------------------------------------------------------------- planches


def planche_rouleau_principale():
    return document(
        tache(400, 300, 250, C["creme"])
        + ombre(400, 470, 190)
        + rouleau(400, 330, 1.25, -12),
        titre="Le rouleau anti-poils réutilisable Canapoil, coque terracotta et poignée en arc",
    )


def planche_rouleau_usage():
    return document(
        f'<rect x="0" y="470" width="800" height="130" fill="{C["sable"]}"/>'
        + canape(400, 500, 0.92, bande_propre=(-250, 60))
        + chat_assis(650, 352, 0.6, miroir=True)
        + rouleau(255, 306, 0.62, -6)
        + fleches_va_et_vient(300, 420, 230, C["texte"]),
        titre="Le rouleau passé en allers-retours sur l'assise d'un canapé en tissu, une bande propre apparaît, le chat regarde",
    )


def planche_rouleau_reservoir():
    return document(
        tache(380, 300, 240, C["creme"])
        + ombre(380, 470, 220)
        + rouleau(330, 320, 1.05, 0, clapet_ouvert=True)
        + poubelle(640, 470, 0.85),
        titre="Le réservoir du rouleau s'ouvre au-dessus de la poubelle : les poils tombent en boule",
    )


def planche_rouleau_colis():
    return document(
        tache(400, 310, 250, C["creme"])
        + ombre(380, 500, 230)
        + colis(380, 420, 1.0)
        + rouleau(330, 250, 0.72, -18)
        + notice(590, 300, 0.9, 10),
        titre="Contenu du colis : un rouleau anti-poils avec réservoir et une notice en français",
    )


def planche_rouleau_dimensions():
    return document(
        rouleau(400, 330, 1.0, 0)
        + cote(266, 470, 534, 470, "≈ 27 cm")
        + f'<g transform="translate(600,330)">'
        + f'<path d="M0,-120 V104" stroke="{C["brun"]}" stroke-width="3" stroke-linecap="round"/>'
        + f'<path d="M-12,-120 h24 M-12,104 h24" stroke="{C["brun"]}" stroke-width="3" stroke-linecap="round"/>'
        + f'<text x="18" y="0" font-family="DM Sans, Arial, sans-serif" font-size="26" font-weight="700" fill="{C["texte"]}">≈ 9 cm</text></g>'
        + f'<text x="400" y="560" text-anchor="middle" font-family="DM Sans, Arial, sans-serif" font-size="22" fill="{C["brun"]}">≈ 27 × 9 × 7 cm · ≈ 280 g · dimensions à confirmer sur l\'échantillon</text>',
        titre="Dimensions approximatives du rouleau : environ 27 par 9 par 7 centimètres, 280 grammes",
    )


def planche_gant_principale():
    return document(
        tache(400, 300, 240, C["creme"]) + ombre(400, 480, 170) + gant(400, 390, 1.05, -8),
        titre="Le gant de toilettage en silicone vert sauge, picots souples et sangle terracotta",
    )


def planche_gant_usage():
    return document(
        tache(400, 320, 260, C["creme"])
        + ombre(400, 520, 220)
        + chat_assis(330, 520, 1.0)
        + gant(560, 340, 0.62, 28),
        titre="Le gant caresse le dos d'un chat roux dans le sens du poil",
    )


def planche_raclette_principale():
    return document(
        tache(400, 300, 240, C["creme"]) + ombre(400, 500, 170) + raclette(400, 420, 1.05, 12),
        titre="La raclette anti-poils : manche terracotta et lame en caoutchouc dentelée",
    )


def planche_raclette_usage():
    import random

    rnd = random.Random(3)
    pts = [(rnd.uniform(80, 420), rnd.uniform(430, 560), rnd.uniform(-70, 70)) for _ in range(40)]
    return document(
        f'<rect x="0" y="380" width="800" height="220" fill="{C["sable"]}"/>'
        + f'<rect x="60" y="410" width="680" height="170" rx="16" fill="{C["primaire_pale"]}"/>'
        + "".join(
            f'<path d="M{80 + i * 22},420 v150" stroke="{C["creme"]}" stroke-width="5" opacity=".7"/>'
            for i in range(30)
        )
        + poils(pts, C["brun"], 3.5)
        + f'<g transform="translate(440,500)"><circle r="34" fill="{C["accent"]}"/><circle cx="-10" cy="-10" r="14" fill="{C["accent_pale"]}" opacity=".7"/></g>'
        + raclette(560, 470, 0.8, 70)
        + fleches_va_et_vient(560, 330, 200, C["texte"]),
        titre="La raclette tirée sur un tapis ras regroupe les poils incrustés en boule",
    )


def planche_tapis_principale():
    return document(
        f'<rect x="0" y="0" width="800" height="600" fill="{C["sable"]}"/>'
        + tapis_fenetre(400, 560, 0.98),
        titre="Le tapis de fenêtre thermique posé sur un rebord, un chat roux couché dessus, la neige tombe dehors",
    )


def planche_tapis_detail():
    couches = (
        f'<g transform="translate(400,300)">'
        f'<rect x="-280" y="40" width="560" height="40" rx="14" fill="{C["brun"]}"/>'
        f'<rect x="-270" y="0" width="540" height="34" rx="12" fill="#C9C2B8"/>'
        f'<path d="M-270,-6 C-270,-52 -240,-64 -200,-64 H200 C240,-64 270,-52 270,-6 Z" fill="{C["creme"]}"/>'
        f'<path d="M-250,-48 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0 q12,-10 24,0" fill="none" stroke="{C["sable"]}" stroke-width="5" stroke-linecap="round"/>'
        f"</g>"
    )
    legendes = (
        f'<g font-family="DM Sans, Arial, sans-serif" font-size="26" font-weight="700" fill="{C["texte"]}">'
        f'<text x="130" y="200">1. Dessus doux en sherpa</text>'
        f'<text x="130" y="460">2. Couche réfléchissante</text>'
        f'<text x="130" y="500">3. Dessous antidérapant</text>'
        f"</g>"
        f'<path d="M200,210 L230,248" stroke="{C["brun"]}" stroke-width="3" stroke-linecap="round"/>'
        f'<path d="M420,436 L420,322" stroke="{C["brun"]}" stroke-width="3" stroke-linecap="round"/>'
        f'<path d="M420,492 H560 V368" fill="none" stroke="{C["brun"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<text x="400" y="565" text-anchor="middle" font-family="DM Sans, Arial, sans-serif" font-size="21" fill="{C["brun"]}">Sans fil, sans pile, sans prise · ≈ 90 × 28 cm (à confirmer)</text>'
    )
    return document(
        couches + legendes,
        titre="Coupe du tapis : dessus en sherpa, couche réfléchissante intérieure, dessous antidérapant",
    )


def planche_kit(produits, titre):
    """Composition de plusieurs produits pour un kit."""
    pieces = ""
    n = len(produits)
    positions = {
        1: [(400, 330)],
        2: [(280, 330), (540, 340)],
        3: [(250, 300), (470, 360), (640, 300)],
    }[n]
    for (px, py), pid in zip(positions, produits):
        if pid == "rouleau-anti-poils":
            pieces += rouleau(px, py, 0.8 if n > 1 else 1.1, -12)
        elif pid == "gant-toilettage":
            pieces += gant(px, py + 60, 0.62, 10)
        elif pid == "raclette-anti-poils":
            pieces += raclette(px, py + 90, 0.6, 18)
        elif pid == "tapis-fenetre-thermique":
            pieces += (
                f'<g transform="translate({px},{py + 40})">'
                f'<rect x="-150" y="-10" width="300" height="34" rx="12" fill="{C["brun"]}" opacity=".35"/>'
                f'<path d="M-160,10 C-160,-30 -140,-44 -110,-44 H110 C140,-44 160,-30 160,10 Z" fill="{C["creme"]}"/>'
                f'<path d="M-146,-28 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0 q10,-8 20,0" fill="none" stroke="{C["sable"]}" stroke-width="4" stroke-linecap="round"/>'
                f"{chat_couche(30, -40, 0.5)}"
                f"</g>"
            )
    return document(
        tache(400, 310, 270, C["creme"]) + ombre(430, 500, 260) + pieces,
        titre=titre,
    )


def planche_hero():
    """Illustration principale de l'accueil (format 960 × 720)."""
    return document(
        tache(500, 380, 330, C["creme"])
        + f'<rect x="0" y="600" width="960" height="120" fill="{C["sable"]}"/>'
        + ombre(480, 628, 330, 18, 0.1)
        + canape(480, 620, 1.05, bande_propre=(-250, 70))
        + chat_assis(742, 434, 0.74, miroir=True)
        + rouleau(318, 392, 0.72, -6)
        + fleches_va_et_vient(380, 530, 260, C["texte"]),
        largeur=960,
        hauteur=720,
        titre="Un chat roux assis sur un canapé vert, un rouleau anti-poils laisse une bande propre sur l'assise",
        couleur_fond=C["fond"],
    )


def etape(numero):
    if numero == 1:
        corps = (
            f'<rect x="20" y="210" width="360" height="70" rx="22" fill="{C["sauge_moyen"]}"/>'
            + poils([(60, 236, 10), (100, 250, -30), (300, 240, 40), (330, 256, -10), (280, 262, 20)], C["accent_pale"], 3.5)
            + rouleau(190, 150, 0.5, -10)
            + fleches_va_et_vient(190, 60, 150)
        )
        titre = "Étape 1 : faites des allers-retours courts sur le tissu"
    elif numero == 2:
        corps = rouleau(170, 170, 0.62, 0, clapet_ouvert=True)
        titre = "Étape 2 : les poils s'accumulent dans le réservoir"
    else:
        corps = poubelle(200, 230, 0.75) + rouleau(185, 70, 0.4, 175)
        titre = "Étape 3 : videz le réservoir au-dessus de la poubelle"
    return document(tache(200, 160, 140, C["creme"]) + corps, 400, 300, titre)


def favicon():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{C["primaire"]}"/>'
        f'<path d="M20,22 L23,10 L31,17 Z M44,22 L41,10 L33,17 Z" fill="{C["fond"]}"/>'
        f'<ellipse cx="32" cy="30" rx="15" ry="13" fill="{C["fond"]}"/>'
        f'<path d="M23,28 q3,3 6,0 M35,28 q3,3 6,0" fill="none" stroke="{C["primaire"]}" stroke-width="2.6" stroke-linecap="round"/>'
        f'<path d="M29.5,33 h5 l-2.5,3 Z" fill="{C["primaire"]}"/>'
        f'<rect x="12" y="44" width="40" height="10" rx="5" fill="{C["fond"]}"/>'
        "</svg>\n"
    )


PLANCHES_PRODUITS = {
    "rouleau-anti-poils": [
        ("01-principale", planche_rouleau_principale),
        ("02-usage", planche_rouleau_usage),
        ("03-reservoir", planche_rouleau_reservoir),
        ("04-colis", planche_rouleau_colis),
        ("05-dimensions", planche_rouleau_dimensions),
    ],
    "gant-toilettage": [
        ("01-principale", planche_gant_principale),
        ("02-usage", planche_gant_usage),
    ],
    "raclette-anti-poils": [
        ("01-principale", planche_raclette_principale),
        ("02-usage", planche_raclette_usage),
    ],
    "tapis-fenetre-thermique": [
        ("01-principale", planche_tapis_principale),
        ("02-couches", planche_tapis_detail),
    ],
}
