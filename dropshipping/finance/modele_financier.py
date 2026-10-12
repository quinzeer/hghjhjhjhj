#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle financier Canapoil — direction financière (dossier 05).

Produit, dans le dossier du script :
  - modele_financier.xlsx : onglets Hypothèses, Unit economics, Scénarios 18 mois,
    Trésorerie, Paliers, Sensibilité. Les onglets de calcul sont en formules Excel
    qui pointent vers des noms définis (h_... = hypothèse, ue_... = unit economics).
  - data.json : données du tableau de bord graphique.

Usage : python3 modele_financier.py
Dépendances : Python 3.10+, openpyxl (aucune autre).

Conventions
  - Montants en euros. Prix de vente TTC. Coûts HT pour une société assujettie à la TVA,
    sauf dans les blocs « franchise en base » et « micro-entreprise ».
  - « Bénéfice net » = résultat mensuel après tous les coûts, avant impôt sur les sociétés
    et avant rémunération du dirigeant (définition de 04-strategie.md §6.1).
  - Les prix et coûts des produits sont repris de ../strategie/brand.json : le script
    s'arrête si une valeur diverge.
  - Les calculs Python ci-dessous reproduisent exactement les formules Excel ; la
    cohérence est vérifiée en recalculant le classeur avec LibreOffice (voir
    verifier_avec_libreoffice()).
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

ICI = Path(__file__).resolve().parent
BRAND_JSON = ICI.parent / "strategie" / "brand.json"
SORTIE_XLSX = ICI / "modele_financier.xlsx"
SORTIE_JSON = ICI / "data.json"

# =============================================================================
# 1. HYPOTHÈSES (source unique du modèle)
# =============================================================================
# Chaque hypothèse : (nom, libellé, valeur, unité, source ou niveau de confiance).
# Le nom devient un nom défini Excel préfixé « h_ ».

SRC = {
    "brand": "strategie/brand.json (12/10/2026)",
    "04": "strategie/04-strategie.md",
    "sp_tva": "https://entreprendre.service-public.gouv.fr/vosdroits/F21746 (vérifié le 01/01/2026)",
    "sp_is": "https://entreprendre.service-public.gouv.fr/vosdroits/F23575 ; LF 2026 inchangée : https://hayot-expertise.fr/blog/is-2026-taux-normal-taux-reduit-15-seuils",
    "sp_micro": "https://entreprendre.service-public.gouv.fr/vosdroits/F32353 (03 §3.6)",
    "pfu": "https://www.lafinancepourtous.com/2025/12/17/csg-un-taux-a-double-vitesse-pour-2026/",
    "charges": "https://hayot-expertise.fr/blog/charges-sociales-sasu ; https://www.keobiz.fr/le-mag/sasu-charge-sociale/",
    "tns_min": "https://www.lecoindesentrepreneurs.fr/cotisations-tns-minimales/",
    "smic": "https://www.info.gouv.fr/public/index.php/actualite/le-smic-revalorise-le-1er-juin-2026",
    "stripe": "https://stripe.com/fr/pricing",
    "stripe_payouts": "https://docs.stripe.com/payouts (France : 7 jours calendaires au premier versement, 3 jours ouvrés ensuite)",
    "paypal": "https://www.paypal.com/fr/brc/article/funds-availability",
    "tts_regl": "https://seller-fr.tiktok.com/university/essay?knowledge_id=747695670282004 (page du 09/10/2026)",
    "tts_comm": "https://www.ecommerce-nation.fr/tiktok-shop-les-commissions-doublent-janvier-2026/",
    "leko": "https://www.leko-organisme.fr/wp-content/uploads/Bareme-Leko-Emballage-et-Papiers-2026-14.11.2025.pdf",
    "cm2c": "https://www.cm2c.net/tarifs.php",
    "inpi": "https://www.inpi.fr/inpi-block/download-document?id=20516",
    "euipo": "https://www.euipo.europa.eu/en/trade-marks/before-applying/fees-payable-direct-filing",
    "shopify": "https://speed-ecom.eu/blog/combien-coute-reellement-shopify/",
}

HYPOTHESES = [
    ("Fiscalité", [
        ("TVA", "Taux normal de TVA", 0.20, "%", "03 §3.1 ; " + SRC["sp_tva"]),
        ("IS_TAUX_REDUIT", "IS, taux réduit PME", 0.15, "%", SRC["sp_is"]),
        ("IS_SEUIL", "IS, plafond du bénéfice au taux réduit", 42500, "€ / exercice", SRC["sp_is"]),
        ("IS_TAUX_NORMAL", "IS, taux normal", 0.25, "%", SRC["sp_is"]),
        ("FRANCHISE_SEUIL", "Franchise en base de TVA : seuil (CA N-1, ventes)", 85000, "€ / an", SRC["sp_tva"]),
        ("FRANCHISE_SEUIL_MAJORE", "Franchise en base de TVA : seuil majoré (année en cours)", 93500, "€ / an", SRC["sp_tva"]),
        ("MICRO_COTIS", "Micro-entreprise : cotisations sociales (ventes)", 0.123, "% du CA", SRC["sp_micro"]),
        ("MICRO_VL", "Micro-entreprise : versement libératoire (ventes)", 0.01, "% du CA", SRC["sp_micro"]),
        ("MICRO_PLAFOND", "Micro-entreprise : plafond de CA (ventes)", 203100, "€ / an", SRC["sp_micro"]),
        ("PFU", "Prélèvement forfaitaire unique sur dividendes 2026 (12,8 % + 18,6 %)", 0.314, "%", SRC["pfu"]),
        ("CHARGES_SASU", "Président de SASU : cotisations / salaire net", 0.80, "ratio", "Fourchette 75-82 % : " + SRC["charges"]),
        ("CHARGES_TNS", "Gérant majoritaire d'EURL (TNS) : cotisations / rémunération nette", 0.45, "ratio", "Fourchette 33-45 % : " + SRC["charges"]),
        ("TNS_MINIMUM", "TNS : cotisations minimales dues sans rémunération", 1423, "€ / an", SRC["tns_min"] + " (montants 2026 divergents selon les sources : 1 058 à 1 423 €)"),
        ("SMIC_NET_H", "SMIC horaire net (depuis le 1/06/2026)", 9.74, "€ / h", SRC["smic"]),
        ("HEURES_FONDATEUR", "Temps du fondateur", 25, "h / semaine", "Plan marketing ramené à 25 h par semaine (07 §3.3, correction M5) ; à remplacer par la valeur décidée par le client"),
    ]),
    ("Livraison, paiement, plateformes", [
        ("PORT_CLIENT_TTC", "Frais de port facturés au client sous le seuil", 3.90, "€ TTC", SRC["brand"] + " livraison.frais_ttc"),
        ("SEUIL_GRATUIT", "Seuil de livraison offerte", 35.0, "€ TTC", SRC["brand"] + " livraison.seuil_gratuite_ttc"),
        ("PORT_500", "Port point relais HT, jusqu'à 500 g", 4.50, "€ HT", SRC["brand"] + " hypotheses_cles.port_ht"),
        ("PORT_1KG", "Port point relais HT, 500 g à 1 kg", 5.50, "€ HT", SRC["brand"] + " hypotheses_cles.port_ht"),
        ("PORT_2KG", "Port point relais HT, 1 à 2 kg", 7.00, "€ HT", SRC["brand"] + " hypotheses_cles.port_ht"),
        ("PORT_TTS_500", "TikTok Shop : étiquette d'expédition HT, jusqu'à 500 g", 4.50, "€ HT", SRC["brand"] + " livraison.tiktok_shop.port_ht_modele ; tarif « Expédition par TikTok » à relever dans le Seller Center (non publié), hypothèse non vérifiée"),
        ("PORT_TTS_1KG", "TikTok Shop : étiquette d'expédition HT, 500 g à 1 kg", 5.50, "€ HT", "Idem"),
        ("EMB_PETIT", "Emballage, colis jusqu'à 500 g", 0.30, "€ HT", SRC["brand"] + " cout_emballage_ht"),
        ("EMB_GRAND", "Emballage, colis de plus de 500 g", 0.40, "€ HT", "04 §4.1 (0,30-0,40 €), estimation, confiance moyenne"),
        ("STRIPE_PCT", "Stripe / Shopify Payments : part variable (carte standard EEE)", 0.015, "%", SRC["stripe"]),
        ("STRIPE_FIXE", "Stripe / Shopify Payments : part fixe", 0.25, "€", SRC["stripe"]),
        ("STRIPE_LITIGE", "Frais de litige Stripe", 20.0, "€ / litige", SRC["stripe"]),
        ("PAYPAL_PCT", "PayPal : part variable", 0.029, "%", "03 §4.1 [S26]"),
        ("PAYPAL_FIXE", "PayPal : part fixe", 0.35, "€", "03 §4.1 [S26]"),
        ("TTS_COMM", "Commission TikTok Shop (assiette TTC, port payé inclus)", 0.09, "% TTC", SRC["tts_comm"]),
        ("TTS_COMM_LANCEMENT", "Commission TikTok Shop, 60 premiers jours (nouvelle boutique UE)", 0.04, "% TTC", SRC["tts_comm"]),
        ("CREA_COMM", "Commission des créateurs affiliés", 0.15, "% TTC", SRC["brand"] + " hypotheses_cles.commission_createurs"),
        ("PROV_RETOURS", "Provision retours, SAV et litiges", 0.05, "% du CA HT", SRC["brand"] + " hypotheses_cles.taux_retour ; 02 §4.1"),
    ]),
    ("Mix de ventes", [
        ("MIX_AFF", "Part des commandes TikTok Shop par affiliés", 0.58, "%", SRC["brand"] + " canaux.repartition_commandes_hypothese"),
        ("MIX_PROPRE", "Part des commandes TikTok Shop en contenu propre", 0.22, "%", SRC["brand"]),
        ("MIX_SITE", "Part des commandes du site", 0.20, "%", SRC["brand"]),
        ("SITE_ROU", "Site : part Rouleau seul", 0.35, "%", SRC["brand"] + " panier_moyen_ttc_note"),
        ("SITE_KAP", "Site : part Kit anti-poils", 0.20, "%", SRC["brand"]),
        ("SITE_GK", "Site : part Grand kit", 0.30, "%", SRC["brand"]),
        ("SITE_DUO", "Site : part Duo", 0.15, "%", SRC["brand"]),
        ("TTS_ROU", "TikTok Shop : part Rouleau seul", 0.70, "%", "Estimation finance, confiance faible, à remplacer par la répartition observée après 30 commandes TikTok Shop (revue red team m16)"),
        ("TTS_KAP", "TikTok Shop : part Kit anti-poils", 0.30, "%", "Idem"),
    ]),
    ("Phase import groupé + 3PL (palier 2)", [
        ("IMP_ROU", "Rouleau : coût rendu entrepôt, droits inclus", 2.00, "€ HT", "Estimation finance, confiance faible, calée sur 04 §6.4 (Grand kit ≈ 3,80 €)"),
        ("IMP_GAN", "Gant : coût rendu entrepôt, droits inclus", 0.65, "€ HT", "Idem"),
        ("IMP_RAC", "Raclette : coût rendu entrepôt, droits inclus", 1.15, "€ HT", "Idem"),
        ("IMP_TAP", "Tapis thermique : coût rendu entrepôt, droits inclus", 2.60, "€ HT", "Idem"),
        ("TPL_PREP", "3PL : préparation par colis (emballage inclus)", 2.40, "€ HT", "03 §5.1 [S52], source faible"),
        ("IMP_FRAIS_MOIS", "Import : transitaire, inspection AQL, agent (lissés)", 160, "€ / mois", "03 §3.5 et §5.2 : ≈ 400 € par lot tous les 2,5 mois, estimation"),
        ("TPL_STOCKAGE", "3PL : stockage", 50, "€ / mois", "03 §5.1 : 10-25 € par palette, estimation"),
    ]),
    ("Publicité", [
        ("CPA_REALISTE", "CPA scénario réaliste (Grand kit, Meta)", 21.0, "€", "Entre favorable (10,67 €) et central (30 €) de 02 §5.3 D ; estimation, confiance faible"),
        ("CPA_OPTIMISTE", "CPA scénario optimiste", 14.0, "€", "Idem, créatives du premier quartile"),
        ("MER_MARGE", "Marge de sécurité exigée sur le MER de rentabilité", 1.2, "×", "02 §5.2"),
    ]),
    ("Frais fixes et ponctuels", [
        ("COMPTABLE", "Expert-comptable en ligne, société à l'IS (lancement)", 90, "€ / mois", "03 §0.4 : 1 000-2 500 € par an ; bas de fourchette"),
        ("COMPTABLE_P2", "Expert-comptable, phase import et publicité", 200, "€ / mois", "Estimation, confiance moyenne"),
        ("BANQUE", "Compte bancaire professionnel", 10, "€ / mois", "Estimation"),
        ("OUTILS", "Plateforme de facturation électronique, outils", 10, "€ / mois", "03 §0.5 : 0-15 € par mois"),
        ("RC", "Assurance RC professionnelle et produits (souscrite avant la commande du stock, dès novembre 2026)", 25, "€ / mois", "03 §0.5 : 150-500 € par an ; 3 devis en S1 (correction M11)"),
        ("DOMICILIATION", "Domiciliation avec réception de colis (dès 150 commandes / mois)", 25, "€ / mois", "03 §5.5 : 15-40 € par mois"),
        ("SHOPIFY_ESSAI", "Shopify, 3 premiers mois (1 $)", 0.86, "€ / mois", SRC["shopify"]),
        ("SHOPIFY_BASIC", "Shopify Basic", 36, "€ / mois", SRC["shopify"]),
        ("SHOPIFY_GROW", "Shopify Grow", 105, "€ / mois", "04 §5.2"),
        ("SHOPIFY_GROW_SEUIL", "CA HT mensuel à partir duquel Grow est retenu", 34500, "€", "04 §5.2"),
        ("APPS", "Applications Shopify (avis, e-mail)", 50, "€ / mois", "Estimation"),
        ("ASSISTANT", "Assistant SAV à mi-temps, coût employeur (dès 1 000 commandes / mois)", 1300, "€ / mois", "Estimation, confiance moyenne"),
        ("MEDIA_BUYER", "Media buyer indépendant (dès 3 000 € de publicité / mois)", 1000, "€ / mois", "Estimation, confiance faible"),
        ("DOMAINE", "Domaine canapoil.fr", 10, "€ / an", "04 §5.3"),
        ("ECHANT_FOURN", "Échantillons fournisseurs (mois 1)", 35, "€", "04 §5.3"),
        ("MEDIATEUR", "Médiateur CM2C (3 ans)", 48, "€", SRC["cm2c"]),
        ("LEKO", "Adhésion Léko, minimum annuel", 95, "€ HT / an", SRC["leko"]),
        ("FOURNITURES", "Fournitures de lancement", 12, "€", "04 §5.3"),
        ("INPI_P1", "Dépôt INPI « Canapoil », classe 21 (porte 1, novembre 2026)", 190, "€", SRC["inpi"] + " (correction M12)"),
        ("INPI", "Dépôt INPI classes 20 et 28 (porte 2, ≥ 90 commandes / mois) : 190 € + 40 €", 230, "€", SRC["inpi"]),
        ("PRIME_QTE", "Prime de lancement : gants offerts aux premières précommandes", 30, "unités", SRC["brand"] + " livraison.precommande.prime (correction M4)"),
        ("EUIPO", "Marque de l'Union européenne, 2 classes (import groupé)", 900, "€", SRC["euipo"]),
        ("ECH_UNIT", "Coût d'un échantillon envoyé à un créateur", 12, "€", "02 §3.6, central"),
    ]),
    ("Trésorerie", [
        ("TRESO_INITIALE", "Trésorerie de départ affectée au projet", 0, "€", "Hypothèse « 0 € » du client"),
        ("STRIPE_DELAI_INITIAL", "Stripe : délai du premier versement", 7, "jours", SRC["stripe_payouts"]),
        ("STRIPE_DELAI", "Stripe / Shopify Payments : délai courant (3 jours ouvrés)", 5, "jours calendaires", SRC["stripe_payouts"]),
        ("PAYPAL_RETENUE", "PayPal : retenue possible des premiers paiements", 21, "jours", SRC["paypal"]),
        ("TTS_LIVRAISON", "TikTok Shop : délai commande → livraison", 4, "jours", "02 §1.3 (livraison sous 4 jours ouvrés)"),
        ("TTS_DEBUTANT", "TikTok Shop : règlement d'un vendeur débutant", 31, "jours après livraison", SRC["tts_regl"]),
        ("TTS_STANDARD", "TikTok Shop : règlement standard", 8, "jours après livraison", SRC["tts_regl"]),
        ("TTS_ACCELERE", "TikTok Shop : règlement accéléré (SPS ≥ 2,5 et > 4 500 $ de GMV)", 3, "jours après livraison", SRC["tts_regl"]),
        ("TTS_VIREMENT", "TikTok Shop : virement vers la banque", 3, "jours", "Page UK de TikTok Shop ; hypothèse pour la France"),
        ("TTS_DEBUTANT_MOIS", "Durée du statut débutant (mois de ventes)", 3, "mois", "Estimation, confiance faible"),
        ("COUV_MICRO", "Stock détenu, phase micro-stock", 1.2, "mois de ventes", "04 §6.7 : 25-45 jours"),
        ("COUV_IMPORT", "Stock détenu, phase import groupé", 2.5, "mois de ventes", "04 §6.5"),
    ]),
    ("Paliers", [
        ("P1_ECH", "Palier 1 : échantillons créateurs", 100, "€ / mois", "02 §3.6, estimation"),
        ("P2_PART_PUB", "Palier 2 : part des commandes issues de la publicité", 0.25, "%", "Estimation, confiance faible"),
        ("P2_FIXES_AUTRES", "Palier 2 : frais fixes hors personnel", 750, "€ / mois", "Comptable 200, banque 20, RC 40, Shopify Grow 105, applications 100, import 160, stockage 100, conformité 25 : estimation"),
        ("P2_PERSONNEL", "Palier 2 : assistant SAV + media buyer", 2300, "€ / mois", "Estimation, confiance moyenne"),
        ("P2_ECH", "Palier 2 : échantillons créateurs", 300, "€ / mois", "Estimation"),
        ("P3_MARGE", "Palier 3 : marge nette sur CA HT", 0.14, "%", "04 §6.1 : 12-16 %"),
        ("P3_PANIER", "Palier 3 : panier moyen", 40, "€ TTC", "04 §6.1"),
        ("P3_PUB", "Palier 3 : publicité en % du CA HT", 0.25, "%", "02 §5.2 : 20-35 %"),
        ("P3_COGS", "Palier 3 : coût des produits en % du CA HT", 0.18, "%", "Estimation, confiance faible"),
        ("P4_MARGE", "Palier 4 : marge nette sur CA HT", 0.12, "%", "04 §6.1 : 10-14 %"),
        ("P4_PANIER", "Palier 4 : panier moyen", 45, "€ TTC", "04 §6.1"),
        ("P4_PUB", "Palier 4 : publicité en % du CA HT", 0.22, "%", "Estimation"),
        ("P4_COGS", "Palier 4 : coût des produits en % du CA HT (distribution physique incluse)", 0.22, "%", "Estimation, confiance faible"),
        ("PART_MARKETPLACE", "Paliers 3-4 : part du CA encaissée par des places de marché", 0.40, "%", "Estimation"),
        ("CREANCES_JOURS", "Paliers 3-4 : délai d'encaissement des places de marché", 15, "jours", "TikTok Shop standard ; Amazon ≈ 14 jours"),
        ("DETTES_FOURN_PART", "Paliers 3-4 : part des achats payée à 30 jours", 0.50, "%", "Estimation"),
        ("TVA_NETTE_RATIO", "Paliers 3-4 : TVA nette due / TVA collectée", 0.85, "ratio", "Estimation : TVA d'import autoliquidée"),
    ]),
]

# --- Produits et kits : copie de brand.json (vérifiée au lancement) ----------
PRODUITS = {
    "ROU": {"id": "rouleau-anti-poils", "sku": "CNP-ROU-01", "nom": "Rouleau anti-poils", "prix": 24.9,
            "prod": 5.4, "droits": 0.40, "port": 4.5, "emb": 0.3, "poids": 280},
    "GAN": {"id": "gant-toilettage", "sku": "CNP-GAN-01", "nom": "Gant de toilettage", "prix": 9.9,
            "prod": 1.56, "droits": 0.25, "port": 4.5, "emb": 0.3, "poids": 70},
    "RAC": {"id": "raclette-anti-poils", "sku": "CNP-RAC-01", "nom": "Raclette anti-poils", "prix": 12.9,
            "prod": 2.28, "droits": 0.30, "port": 4.5, "emb": 0.3, "poids": 150},
    "TAP": {"id": "tapis-fenetre-thermique", "sku": "CNP-TAP-01", "nom": "Tapis de fenêtre thermique", "prix": 24.9,
            "prod": 6.0, "droits": 0.50, "port": 4.5, "emb": 0.3, "poids": 400},
}
KITS = {
    "KAP": {"id": "kit-anti-poils", "nom": "Kit anti-poils", "prix": 29.9, "compo": ["ROU", "GAN"], "separes": 34.8, "eco": 4.9, "offerte": False},
    "GK": {"id": "grand-kit", "nom": "Grand kit", "prix": 39.9, "compo": ["ROU", "RAC", "GAN"], "separes": 47.7, "eco": 7.8, "offerte": True},
    "DUO": {"id": "duo-rouleaux", "nom": "Duo maison + voiture", "prix": 39.9, "compo": ["ROU", "ROU"], "separes": 49.8, "eco": 9.9, "offerte": True},
    "HIV": {"id": "kit-chat-hiver", "nom": "Kit chat d'hiver", "prix": 44.9, "compo": ["ROU", "TAP"], "separes": 49.8, "eco": 4.9, "offerte": True},
}
for code, p in PRODUITS.items():
    HYPOTHESES.insert(1, (f"Produit {p['sku']} — {p['nom']} (brand.json)", [
        (f"{code}_PRIX", "Prix de vente", p["prix"], "€ TTC", SRC["brand"]),
        (f"{code}_PROD", "Coût produit rendu France, base prudente (produit + fret entrant) × 1,20", p["prod"], "€ HT", SRC["brand"] + " cout_produit_ht (correction M13 : +20 % tant que la TVA et la douane ne sont pas validées)"),
        (f"{code}_DROITS", "Droits et redevance répartis sur le lot", p["droits"], "€ HT", SRC["brand"] + " droits_douane_estimes"),
        (f"{code}_POIDS", "Poids", p["poids"], "g", SRC["brand"] + " poids_g"),
    ]))
HYPOTHESES.insert(5, ("Kits (brand.json)", [
    (f"{k}_PRIX", f"{v['nom']} : prix", v["prix"], "€ TTC", SRC["brand"] + " bundles") for k, v in KITS.items()
]))

V = {nom: val for _, lignes in HYPOTHESES for (nom, _l, val, _u, _s) in lignes}

# --- Scénarios : saisies mensuelles ------------------------------------------
MOIS = ["oct. 2026", "nov. 2026", "déc. 2026", "janv. 2027", "févr. 2027", "mars 2027", "avr. 2027",
        "mai 2027", "juin 2027", "juil. 2027", "août 2027", "sept. 2027", "oct. 2027", "nov. 2027",
        "déc. 2027", "janv. 2028", "févr. 2028", "mars 2028"]
EXERCICE = [2026] * 3 + [2027] * 12 + [2028] * 3
N = len(MOIS)


def mix_canaux(mature_site, mature_propre, mature_aff):
    """Part site / TikTok propre / affiliés par mois. M2 : précommandes sur le site uniquement."""
    site, propre, aff = [], [], []
    for m in range(N):
        if m <= 1:
            s, p, a = 1.0, 0.0, 0.0
        elif m == 2:
            s, p, a = 0.30, 0.50, 0.20
        elif m == 3:
            s, p, a = 0.25, 0.35, 0.40
        else:
            s, p, a = mature_site, mature_propre, mature_aff
        site.append(s); propre.append(p); aff.append(a)
    return site, propre, aff


SCENARIOS = {
    "pessimiste": {
        "libelle": "Pessimiste",
        "description": "Porte 1 franchie de justesse ; moins d'une commande par jour hors Noël ; peu d'affiliés actifs ; ni import groupé ni publicité.",
        "proba": "Au moins aussi bien dans 60-75 % des cas où la porte 1 est franchie (estimation, confiance faible)",
        "cmd_org": [0, 8, 30, 18, 20, 22, 24, 25, 25, 25, 26, 28, 32, 45, 55, 26, 26, 28],
        "mix": mix_canaux(0.25, 0.35, 0.40),
        "import_debut": None,
        "pub": [0] * N,
        "cpa": None,
        "ech": [0, 0, 60, 60, 60, 40, 40, 40, 40, 40, 40, 40, 40, 60, 60, 40, 40, 40],
        "accelere_debut": None,
    },
    "realiste": {
        "libelle": "Réaliste",
        "description": "Croissance organique régulière ; palier 1 en novembre 2027 ; import groupé en octobre 2027 ; test publicitaire de 3 mois arrêté faute de rentabilité.",
        "proba": "Au moins aussi bien dans 30-40 % des cas où la porte 1 est franchie (estimation, confiance faible)",
        "cmd_org": [0, 12, 45, 50, 65, 85, 105, 125, 145, 160, 170, 185, 205, 250, 320, 240, 260, 290],
        "mix": mix_canaux(0.20, 0.22, 0.58),
        "import_debut": 12,  # index : oct. 2027
        "pub": [0] * 13 + [300, 450, 600, 0, 0],
        "cpa": "CPA_REALISTE",
        "ech": [0, 0, 60, 150, 150, 100, 100, 100, 100, 100, 100, 100, 100, 120, 120, 100, 100, 100],
        "accelere_debut": None,
    },
    "optimiste": {
        "libelle": "Optimiste",
        "description": "Vidéo virale en décembre avec du stock ; affiliés nombreux ; import groupé en juin 2027 ; publicité rentable à 14 € de CPA dès juillet 2027.",
        "proba": "Au moins aussi bien dans 5-10 % des cas où la porte 1 est franchie (estimation, confiance faible)",
        "cmd_org": [0, 30, 200, 230, 280, 360, 430, 500, 560, 600, 640, 720, 850, 1050, 1300, 1050, 1150, 1300],
        "mix": mix_canaux(0.20, 0.22, 0.58),
        "import_debut": 8,  # index : juin 2027
        "pub": [0] * 9 + [500, 1000, 2000, 3000, 4500, 6000, 5000, 6000, 7000],
        "cpa": "CPA_OPTIMISTE",
        "ech": [0, 0, 100, 250, 250, 200, 200, 200, 200, 200, 250, 250, 300, 300, 300, 300, 300, 300],
        "accelere_debut": 8,
    },
}

# =============================================================================
# 2. VÉRIFICATION DE COHÉRENCE AVEC brand.json
# =============================================================================


def verifier_brand_json():
    brand = json.loads(BRAND_JSON.read_text(encoding="utf-8"))
    erreurs = []

    def eq(a, b, quoi):
        if abs(float(a) - float(b)) > 1e-9:
            erreurs.append(f"{quoi} : modèle {a} ≠ brand.json {b}")

    par_id = {p["id"]: p for p in brand["produits"]}
    for code, p in PRODUITS.items():
        b = par_id[p["id"]]
        eq(p["prix"], b["prix_ttc"], f"{code} prix_ttc")
        eq(p["prod"], b["cout_produit_ht"], f"{code} cout_produit_ht")
        eq(p["droits"], b["droits_douane_estimes"], f"{code} droits")
        eq(p["port"], b["cout_livraison_ht"], f"{code} cout_livraison_ht")
        eq(p["emb"], b["cout_emballage_ht"], f"{code} cout_emballage_ht")
        eq(p["poids"], b["poids_g"], f"{code} poids_g")
        eq(p["port"], V["PORT_500"], f"{code} port = tranche ≤ 500 g")
        eq(p["emb"], V["EMB_PETIT"], f"{code} emballage = colis ≤ 500 g")
    kits_b = {k["id"]: k for k in brand["bundles"]}
    code_par_id = {p["id"]: c for c, p in PRODUITS.items()}
    for code, k in KITS.items():
        b = kits_b[k["id"]]
        eq(k["prix"], b["prix_ttc"], f"{code} prix")
        eq(k["separes"], b["prix_separes_ttc"], f"{code} prix séparés")
        eq(k["eco"], b["economie_affichee_ttc"], f"{code} économie")
        if sorted(code_par_id[i] for i in b["produits"]) != sorted(k["compo"]):
            erreurs.append(f"{code} composition différente")
        if bool(b["livraison_offerte"]) != (k["prix"] >= V["SEUIL_GRATUIT"]):
            erreurs.append(f"{code} livraison offerte incohérente avec le seuil")
        eq(round(sum(PRODUITS[c]["prix"] for c in k["compo"]), 2), k["separes"], f"{code} somme des prix")
    liv = brand["livraison"]
    eq(V["PORT_CLIENT_TTC"], liv["frais_ttc"], "frais de port")
    eq(V["PORT_TTS_500"], liv["tiktok_shop"]["port_ht_modele"]["jusqu_a_500g"], "port TikTok ≤ 500 g")
    eq(V["PORT_TTS_1KG"], liv["tiktok_shop"]["port_ht_modele"]["de_500g_a_1kg"], "port TikTok 500 g-1 kg")
    eq(V["SEUIL_GRATUIT"], liv["seuil_gratuite_ttc"], "seuil de livraison offerte")
    hc = brand["hypotheses_cles"]
    eq(V["PORT_500"], hc["port_ht"]["jusqu_a_500g"], "port ≤ 500 g")
    eq(V["PORT_1KG"], hc["port_ht"]["de_500g_a_1kg"], "port 500 g-1 kg")
    eq(V["PORT_2KG"], hc["port_ht"]["de_1_a_2kg"], "port 1-2 kg")
    eq(V["PROV_RETOURS"], hc["taux_retour"], "taux de retour")
    eq(V["CREA_COMM"], hc["commission_createurs"], "commission créateurs")
    eq(V["TTS_COMM"], hc["commission_tiktok_shop"], "commission TikTok Shop")
    eq(V["TTS_COMM_LANCEMENT"], hc["commission_tiktok_shop_60_premiers_jours"], "commission TikTok Shop lancement")
    eq(V["STRIPE_PCT"], hc["frais_paiement_stripe"]["pourcentage"], "Stripe %")
    eq(V["STRIPE_FIXE"], hc["frais_paiement_stripe"]["fixe_eur"], "Stripe fixe")
    rep = brand["canaux"]["repartition_commandes_hypothese"]
    eq(V["MIX_AFF"], rep["tiktok_shop_affilies"], "mix affiliés")
    eq(V["MIX_PROPRE"], rep["tiktok_shop_contenu_propre"], "mix contenu propre")
    eq(V["MIX_SITE"], rep["site"], "mix site")
    if erreurs:
        sys.exit("Incohérence avec brand.json :\n  - " + "\n  - ".join(erreurs))
    return brand


# =============================================================================
# 3. UNIT ECONOMICS (calcul Python, miroir des formules Excel)
# =============================================================================
# Cas : (id, libellé, canal, composition, nom du prix, affilié ?, nom du taux TikTok, nom du CPA)
CAS_MS = [
    ("site-rou", "Site — Rouleau seul (+3,90 € de port)", "site", ["ROU"], "ROU_PRIX", False, None, None),
    ("site-gan", "Site — Gant seul (+3,90 € de port)", "site", ["GAN"], "GAN_PRIX", False, None, None),
    ("site-rac", "Site — Raclette seule (+3,90 € de port)", "site", ["RAC"], "RAC_PRIX", False, None, None),
    ("site-tap", "Site — Tapis thermique seul (+3,90 € de port)", "site", ["TAP"], "TAP_PRIX", False, None, None),
    ("site-kap", "Site — Kit anti-poils (+3,90 € de port)", "site", ["ROU", "GAN"], "KAP_PRIX", False, None, None),
    ("site-gk", "Site — Grand kit (port offert)", "site", ["ROU", "RAC", "GAN"], "GK_PRIX", False, None, None),
    ("site-duo", "Site — Duo 2 rouleaux (port offert)", "site", ["ROU", "ROU"], "DUO_PRIX", False, None, None),
    ("site-hiv", "Site — Kit chat d'hiver (port offert)", "site", ["ROU", "TAP"], "HIV_PRIX", False, None, None),
    ("tts-propre-rou", "TikTok Shop, contenu propre — Rouleau", "tts", ["ROU"], "ROU_PRIX", False, "TTS_COMM", None),
    ("tts-propre-kap", "TikTok Shop, contenu propre — Kit anti-poils", "tts", ["ROU", "GAN"], "KAP_PRIX", False, "TTS_COMM", None),
    ("tts-propre4-rou", "TikTok Shop, contenu propre, commission 4 % — Rouleau", "tts", ["ROU"], "ROU_PRIX", False, "TTS_COMM_LANCEMENT", None),
    ("tts-aff-rou", "TikTok Shop, affilié 15 % — Rouleau", "tts", ["ROU"], "ROU_PRIX", True, "TTS_COMM", None),
    ("tts-aff-kap", "TikTok Shop, affilié 15 % — Kit anti-poils", "tts", ["ROU", "GAN"], "KAP_PRIX", True, "TTS_COMM", None),
]
CAS_RISQUE_GK = ("site-gk-lourd", "Site — Grand kit si le colis dépasse 500 g emballage compris", "site",
                 ["ROU", "RAC", "GAN"], "GK_PRIX", False, None, None)
CAS_IMP = [
    ("imp-site-rou", "Site — Rouleau seul", "site", ["ROU"], "ROU_PRIX", False, None, None),
    ("imp-site-kap", "Site — Kit anti-poils", "site", ["ROU", "GAN"], "KAP_PRIX", False, None, None),
    ("imp-site-gk", "Site — Grand kit", "site", ["ROU", "RAC", "GAN"], "GK_PRIX", False, None, None),
    ("imp-site-duo", "Site — Duo 2 rouleaux", "site", ["ROU", "ROU"], "DUO_PRIX", False, None, None),
    ("imp-tts-propre-rou", "TikTok Shop, contenu propre — Rouleau", "tts", ["ROU"], "ROU_PRIX", False, "TTS_COMM", None),
    ("imp-tts-propre-kap", "TikTok Shop, contenu propre — Kit anti-poils", "tts", ["ROU", "GAN"], "KAP_PRIX", False, "TTS_COMM", None),
    ("imp-tts-aff-rou", "TikTok Shop, affilié — Rouleau", "tts", ["ROU"], "ROU_PRIX", True, "TTS_COMM", None),
    ("imp-tts-aff-kap", "TikTok Shop, affilié — Kit anti-poils", "tts", ["ROU", "GAN"], "KAP_PRIX", True, "TTS_COMM", None),
    ("imp-pub-gk-real", "Site, publicité au CPA réaliste — Grand kit", "pub", ["ROU", "RAC", "GAN"], "GK_PRIX", False, None, "CPA_REALISTE"),
    ("imp-pub-gk-opt", "Site, publicité au CPA optimiste — Grand kit", "pub", ["ROU", "RAC", "GAN"], "GK_PRIX", False, None, "CPA_OPTIMISTE"),
]
CAS_REGIME = [c for c in CAS_MS if c[0] in ("site-rou", "site-kap", "site-gk", "site-duo", "tts-propre-rou",
                                              "tts-propre-kap", "tts-aff-rou", "tts-aff-kap")]
COLS_UE = ["prix_ttc", "tva", "ca_ht", "cout_produit", "droits", "livraison", "paiement",
           "commission_tts", "createur_ou_pub", "provision", "cotis_micro", "marge"]


def tranche_port(poids, canal="site"):
    tts = canal == "tts"
    if poids <= 500:
        return (V["PORT_TTS_500"] if tts else V["PORT_500"]), V["EMB_PETIT"]
    if poids <= 1000:
        return (V["PORT_TTS_1KG"] if tts else V["PORT_1KG"]), V["EMB_GRAND"]
    return V["PORT_2KG"], V["EMB_GRAND"]


def calc_cas(cas, phase="MS", regime="ASS", lourd=False):
    _id, _lib, canal, compo, prix_nom, aff, taux_nom, cpa_nom = cas
    K = 1.0 if regime == "ASS" else 1.0 + V["TVA"]
    prix = V[prix_nom]
    poids = sum(PRODUITS[c]["poids"] for c in compo)
    ttc = prix + (V["PORT_CLIENT_TTC"] if canal in ("site", "pub") and prix < V["SEUIL_GRATUIT"] else 0.0)
    tva = ttc - ttc / (1 + V["TVA"]) if regime == "ASS" else 0.0
    ht = ttc - tva
    if phase == "MS":
        prod = sum(PRODUITS[c]["prod"] for c in compo) * K
        droits = sum(PRODUITS[c]["droits"] for c in compo) * K
        port, emb = (V["PORT_1KG"], V["EMB_GRAND"]) if lourd else tranche_port(poids, canal)
        livraison = (port + emb) * K
    else:
        prod = sum(V["IMP_" + c] for c in compo)
        droits = 0.0
        livraison = tranche_port(poids, canal)[0] + V["TPL_PREP"]
    paiement = V["STRIPE_PCT"] * ttc + V["STRIPE_FIXE"] if canal in ("site", "pub") else 0.0
    comm = V[taux_nom] * ttc * K if canal == "tts" else 0.0
    if aff:
        crea = V["CREA_COMM"] * ttc * K
    elif canal == "pub":
        crea = V[cpa_nom] * K
    else:
        crea = 0.0
    prov = V["PROV_RETOURS"] * ht
    micro = V["MICRO_COTIS"] * ttc if regime == "MICRO" else 0.0
    marge = ht - (prod + droits + livraison + paiement + comm + crea + prov + micro)
    d = dict(prix_ttc=ttc, tva=tva, ca_ht=ht, cout_produit=prod, droits=droits, livraison=livraison,
             paiement=paiement, commission_tts=comm, createur_ou_pub=crea, provision=prov,
             cotis_micro=micro, marge=marge, poids=poids)
    avant_pub = marge + (crea if canal == "pub" else 0.0)
    d["marge_avant_pub"] = avant_pub
    d["marge_pct"] = marge / ht
    d["roas_ht"] = ht / avant_pub if canal != "tts" or not aff else None
    d["roas_ttc"] = ttc / avant_pub if canal != "tts" or not aff else None
    d["cpa_max"] = avant_pub if canal != "tts" or not aff else None
    return d


def calc_unit_economics():
    ue = {"MS": {}, "IMP": {}, "FR": {}, "MICRO": {}}
    for c in CAS_MS:
        ue["MS"][c[0]] = calc_cas(c)
    ue["MS"][CAS_RISQUE_GK[0]] = calc_cas(CAS_RISQUE_GK, lourd=True)
    for c in CAS_IMP:
        ue["IMP"][c[0]] = calc_cas(c, phase="IMP")
    for c in CAS_REGIME:
        ue["FR"][c[0]] = calc_cas(c, regime="FR")
        ue["MICRO"][c[0]] = calc_cas(c, regime="MICRO")
    return ue


def moyennes(ue):
    """Composantes moyennes par commande et par canal (noms ue_... dans Excel)."""
    S = {"rou": V["SITE_ROU"], "kap": V["SITE_KAP"], "gk": V["SITE_GK"], "duo": V["SITE_DUO"]}
    T = {"rou": V["TTS_ROU"], "kap": V["TTS_KAP"]}
    out = {}

    def pond(bloc, prefix, poids, champ):
        return sum(w * bloc[f"{prefix}{k}"][champ] for k, w in poids.items())

    for ph, pre in (("MS", ""), ("IMP", "imp-")):
        b = ue[ph]
        out[f"SITE_TTC"] = pond(b, pre + "site-", S, "prix_ttc")
        out[f"SITE_HT"] = pond(b, pre + "site-", S, "ca_ht")
        out[f"SITE_PAY"] = pond(b, pre + "site-", S, "paiement")
        out[f"SITE_PROD_{ph}"] = pond(b, pre + "site-", S, "cout_produit") + pond(b, pre + "site-", S, "droits")
        out[f"SITE_LOG_{ph}"] = pond(b, pre + "site-", S, "livraison")
        out[f"SITE_MARGE_{ph}"] = pond(b, pre + "site-", S, "marge")
        out[f"TTS_TTC"] = pond(b, pre + "tts-propre-", T, "prix_ttc")
        out[f"TTS_HT"] = pond(b, pre + "tts-propre-", T, "ca_ht")
        out[f"TTS_PROD_{ph}"] = pond(b, pre + "tts-propre-", T, "cout_produit") + pond(b, pre + "tts-propre-", T, "droits")
        out[f"TTS_LOG_{ph}"] = pond(b, pre + "tts-propre-", T, "livraison")
        out[f"PROPRE_MARGE_{ph}"] = pond(b, pre + "tts-propre-", T, "marge")
        out[f"AFF_MARGE_{ph}"] = pond(b, pre + "tts-aff-", T, "marge")
        gk = b[pre + "site-gk"]
        out["PUB_TTC"] = gk["prix_ttc"]
        out["PUB_HT"] = gk["ca_ht"]
        out["PUB_PAY"] = gk["paiement"]
        out[f"PUB_PROD_{ph}"] = gk["cout_produit"] + gk["droits"]
        out[f"PUB_LOG_{ph}"] = gk["livraison"]
        out[f"PUB_MARGE_AVANT_PUB_{ph}"] = gk["marge"]
        out[f"MIX_MARGE_{ph}"] = (V["MIX_SITE"] * out[f"SITE_MARGE_{ph}"] + V["MIX_PROPRE"] * out[f"PROPRE_MARGE_{ph}"]
                                  + V["MIX_AFF"] * out[f"AFF_MARGE_{ph}"])
        out[f"MIX_PROD_{ph}"] = V["MIX_SITE"] * out[f"SITE_PROD_{ph}"] + (1 - V["MIX_SITE"]) * out[f"TTS_PROD_{ph}"]
        out[f"MIX_LOG_{ph}"] = V["MIX_SITE"] * out[f"SITE_LOG_{ph}"] + (1 - V["MIX_SITE"]) * out[f"TTS_LOG_{ph}"]
    out["MIX_TTC"] = V["MIX_SITE"] * out["SITE_TTC"] + (1 - V["MIX_SITE"]) * out["TTS_TTC"]
    out["MIX_HT"] = V["MIX_SITE"] * out["SITE_HT"] + (1 - V["MIX_SITE"]) * out["TTS_HT"]
    for reg in ("FR", "MICRO"):
        b = ue[reg]
        site = pond(b, "site-", S, "marge")
        propre = pond(b, "tts-propre-", T, "marge")
        aff = pond(b, "tts-aff-", T, "marge")
        out[f"SITE_MARGE_{reg}"], out[f"PROPRE_MARGE_{reg}"], out[f"AFF_MARGE_{reg}"] = site, propre, aff
        out[f"MIX_MARGE_{reg}"] = V["MIX_SITE"] * site + V["MIX_PROPRE"] * propre + V["MIX_AFF"] * aff
    return out


# =============================================================================
# 4. SCÉNARIOS 18 MOIS ET TRÉSORERIE (miroir des formules Excel)
# =============================================================================


def entrees_scenario(sc):
    """Saisies mensuelles d'un scénario : valeurs Python + formules Excel des lignes dérivées."""
    e = {}
    e["cmd_org"] = list(sc["cmd_org"])
    e["part_site"], e["part_propre"], e["part_aff"] = [list(x) for x in sc["mix"]]
    imp0 = sc["import_debut"]
    e["import"] = [1 if imp0 is not None and m >= imp0 else 0 for m in range(N)]
    e["pub"] = list(sc["pub"])
    e["ech"] = list(sc["ech"])
    e["exercice"] = list(EXERCICE)
    # Lignes dérivées des noms définis (formules dans Excel)
    e["taux_tts"] = ["h_TTS_COMM_LANCEMENT" if m in (2, 3) else "h_TTS_COMM" for m in range(N)]
    e["cpa"] = [("h_" + sc["cpa"]) if sc["cpa"] else "0" for m in range(N)]
    couv = []
    for m in range(N):
        if m == 0:
            couv.append("0")
        elif imp0 is not None and m >= imp0 - 1:
            couv.append("h_COUV_IMPORT")
        else:
            couv.append("h_COUV_MICRO")
    e["couverture"] = couv
    e["delai_site"] = ["h_STRIPE_DELAI_INITIAL" if m == 1 else "h_STRIPE_DELAI" for m in range(N)]
    dts = []
    for m in range(N):
        if m < 2:
            dts.append("0")
        elif m < 2 + V["TTS_DEBUTANT_MOIS"]:
            dts.append("h_TTS_LIVRAISON+h_TTS_DEBUTANT+h_TTS_VIREMENT")
        elif sc["accelere_debut"] is not None and m >= sc["accelere_debut"]:
            dts.append("h_TTS_LIVRAISON+h_TTS_ACCELERE+h_TTS_VIREMENT")
        else:
            dts.append("h_TTS_LIVRAISON+h_TTS_STANDARD+h_TTS_VIREMENT")
    e["delai_tts"] = dts
    return e


def eval_nom(expr):
    """Évalue une expression simple de noms h_... additionnés (ou un nombre)."""
    tot = 0.0
    for t in expr.split("+"):
        t = t.strip()
        tot += V[t[2:]] if t.startswith("h_") else float(t)
    return tot


def calc_scenario(cle, sc, mo):
    e = entrees_scenario(sc)
    r = {k: e[k] for k in ("cmd_org", "part_site", "part_propre", "part_aff", "import", "pub", "ech", "exercice")}
    for k in ("taux_tts", "cpa", "couverture", "delai_site", "delai_tts"):
        r[k] = [eval_nom(x) for x in e[k]]
    rng = range(N)
    r["cmd_site"] = [e["cmd_org"][m] * e["part_site"][m] for m in rng]
    r["cmd_propre"] = [e["cmd_org"][m] * e["part_propre"][m] for m in rng]
    r["cmd_aff"] = [e["cmd_org"][m] * e["part_aff"][m] for m in rng]
    r["cmd_pub"] = [r["pub"][m] / r["cpa"][m] if r["cpa"][m] > 0 else 0.0 for m in rng]
    r["cmd_total"] = [r["cmd_site"][m] + r["cmd_propre"][m] + r["cmd_aff"][m] + r["cmd_pub"][m] for m in rng]
    r["cmd_jour"] = [x / 30 for x in r["cmd_total"]]
    tts = [r["cmd_propre"][m] + r["cmd_aff"][m] for m in rng]
    r["ca_ttc"] = [r["cmd_site"][m] * mo["SITE_TTC"] + tts[m] * mo["TTS_TTC"] + r["cmd_pub"][m] * mo["PUB_TTC"] for m in rng]
    r["ca_ht"] = [x / (1 + V["TVA"]) for x in r["ca_ttc"]]
    r["tva_collectee"] = [r["ca_ttc"][m] - r["ca_ht"][m] for m in rng]

    def ph(m, base):
        return mo[f"{base}_IMP"] if r["import"][m] == 1 else mo[f"{base}_MS"]

    r["c_produits"] = [r["cmd_site"][m] * ph(m, "SITE_PROD") + tts[m] * ph(m, "TTS_PROD") + r["cmd_pub"][m] * ph(m, "PUB_PROD") for m in rng]
    r["c_logistique"] = [r["cmd_site"][m] * ph(m, "SITE_LOG") + tts[m] * ph(m, "TTS_LOG") + r["cmd_pub"][m] * ph(m, "PUB_LOG") for m in rng]
    r["c_paiement"] = [r["cmd_site"][m] * mo["SITE_PAY"] + r["cmd_pub"][m] * mo["PUB_PAY"] for m in rng]
    r["c_tts"] = [tts[m] * mo["TTS_TTC"] * r["taux_tts"][m] for m in rng]
    r["c_crea"] = [r["cmd_aff"][m] * mo["TTS_TTC"] * V["CREA_COMM"] for m in rng]
    r["c_prov"] = [V["PROV_RETOURS"] * r["ca_ht"][m] for m in rng]
    r["marge_contrib"] = [r["ca_ht"][m] - (r["c_produits"][m] + r["c_logistique"][m] + r["c_paiement"][m] + r["c_tts"][m]
                                           + r["c_crea"][m] + r["c_prov"][m]) for m in rng]

    # Frais fixes : règles d'activation (valeurs écrites dans l'onglet Hypothèses)
    ff = {k: [0.0] * N for k in ("ff_structure", "ff_conformite", "ff_outils", "ff_import", "ff_personnel")}
    imp = r["import"]

    def premier(cond):
        for m in rng:
            if cond(m):
                return m
        return None

    m_shop = premier(lambda m: r["cmd_site"][m] >= 150 or r["pub"][m] > 0 or imp[m] == 1)
    m_dom = premier(lambda m: r["cmd_total"][m] >= 150)
    m_inpi = premier(lambda m: r["cmd_total"][m] >= 90)
    for m in rng:
        ff["ff_structure"][m] = (V["COMPTABLE_P2"] if imp[m] else V["COMPTABLE"]) + V["BANQUE"]
        c = 0.0
        if m == 0:
            c += V["DOMAINE"] + V["ECHANT_FOURN"]
        if m == 1:
            c += V["MEDIATEUR"] + V["LEKO"] + V["FOURNITURES"] + V["INPI_P1"]
            c += V["PRIME_QTE"] * (PRODUITS["GAN"]["prod"] + PRODUITS["GAN"]["droits"])
        if m == 12:
            c += V["DOMAINE"]
        if m == 13:
            c += V["LEKO"]
        if m >= 1:
            c += V["RC"]
        if m_inpi is not None and m == m_inpi:
            c += V["INPI"]
        if imp[m] == 1 and (m == 0 or imp[m - 1] == 0):
            c += V["EUIPO"]
        ff["ff_conformite"][m] = c
        o = V["OUTILS"] if m >= 2 else 0.0
        if m_dom is not None and m >= m_dom:
            o += V["DOMICILIATION"]
        if m_shop is not None and m >= m_shop:
            if m - m_shop < 3:
                o += V["SHOPIFY_ESSAI"]
            elif r["ca_ht"][m] > V["SHOPIFY_GROW_SEUIL"]:
                o += V["SHOPIFY_GROW"]
            else:
                o += V["SHOPIFY_BASIC"]
            o += V["APPS"]
        ff["ff_outils"][m] = o
        ff["ff_import"][m] = (V["IMP_FRAIS_MOIS"] + V["TPL_STOCKAGE"]) if imp[m] else 0.0
        p = 0.0
        if r["cmd_total"][m] >= 1000:
            p += V["ASSISTANT"]
        if r["pub"][m] >= 3000:
            p += V["MEDIA_BUYER"]
        ff["ff_personnel"][m] = p
    r.update(ff)
    r["evenements"] = {"bascule_shopify": MOIS[m_shop] if m_shop is not None else None,
                       "domiciliation": MOIS[m_dom] if m_dom is not None else None,
                       "depot_inpi": MOIS[m_inpi] if m_inpi is not None else None,
                       "import_groupe": MOIS[sc["import_debut"]] if sc["import_debut"] is not None else None}
    r["frais_fixes"] = [sum(ff[k][m] for k in ff) for m in rng]
    r["benefice"] = [r["marge_contrib"][m] - r["pub"][m] - r["ech"][m] - r["frais_fixes"][m] for m in rng]
    cum = 0.0
    r["benefice_cumul"] = []
    for x in r["benefice"]:
        cum += x
        r["benefice_cumul"].append(cum)
    r["couts_totaux"] = [r["ca_ht"][m] - r["benefice"][m] for m in rng]
    # IS par exercice civil, avec report du déficit de l'exercice précédent
    r["nouvel_ex"], r["base_is"], r["is_cumul"], r["is_mois"] = [], [], [], []
    for m in rng:
        nouv = 1 if m == 0 or r["exercice"][m] != r["exercice"][m - 1] else 0
        if m == 0:
            base = r["benefice"][m]
        elif nouv:
            base = min(0.0, r["base_is"][m - 1]) + r["benefice"][m]
        else:
            base = r["base_is"][m - 1] + r["benefice"][m]
        isc = V["IS_TAUX_REDUIT"] * min(max(base, 0.0), V["IS_SEUIL"]) + V["IS_TAUX_NORMAL"] * max(base - V["IS_SEUIL"], 0.0)
        ism = isc if nouv else isc - r["is_cumul"][m - 1]
        r["nouvel_ex"].append(nouv); r["base_is"].append(base); r["is_cumul"].append(isc); r["is_mois"].append(ism)
    r["resultat_apres_is"] = [r["benefice"][m] - r["is_mois"][m] for m in rng]

    # ---- Trésorerie ----
    t = {}
    t["site_du"] = [r["cmd_site"][m] * (mo["SITE_TTC"] - mo["SITE_PAY"]) + r["cmd_pub"][m] * (mo["PUB_TTC"] - mo["PUB_PAY"]) for m in rng]
    t["enc_site"] = []
    for m in rng:
        L = r["delai_site"][m]
        v = t["site_du"][m] * (1 - L / 30)
        if m > 0:
            v += t["site_du"][m - 1] * r["delai_site"][m - 1] / 30
        t["enc_site"].append(v)
    t["tts_du"] = [tts[m] * mo["TTS_TTC"] * (1 - r["taux_tts"][m]) - r["cmd_aff"][m] * mo["TTS_TTC"] * V["CREA_COMM"] for m in rng]
    t["w0"], t["w1"], t["w2"] = [], [], []
    for m in rng:
        L = r["delai_tts"][m]
        t["w0"].append(max(0.0, 1 - L / 30))
        t["w1"].append(L / 30 if L <= 30 else (60 - L) / 30)
        t["w2"].append(max(0.0, (L - 30) / 30))
    t["enc_tts"] = []
    for m in rng:
        v = t["tts_du"][m] * t["w0"][m]
        if m >= 1:
            v += t["tts_du"][m - 1] * t["w1"][m - 1]
        if m >= 2:
            v += t["tts_du"][m - 2] * t["w2"][m - 2]
        t["enc_tts"].append(v)
    t["enc_total"] = [t["enc_site"][m] + t["enc_tts"][m] for m in rng]
    t["stock_fin"] = [r["couverture"][m] * r["c_produits"][min(m + 1, N - 1)] for m in rng]
    t["achats_stock"] = [r["c_produits"][m] + t["stock_fin"][m] - (t["stock_fin"][m - 1] if m > 0 else 0.0) for m in rng]
    t["achat_import"] = [r["import"][min(m + 1, N - 1)] for m in rng]
    t["tva_achats"] = [V["TVA"] * t["achats_stock"][m] * (1 - t["achat_import"][m]) for m in rng]
    t["logistique_ttc"] = [r["c_logistique"][m] * (1 + V["TVA"]) for m in rng]
    t["remboursements"] = list(r["c_prov"])
    t["tva_deductible"] = [t["tva_achats"][m] + V["TVA"] * r["c_logistique"][m] for m in rng]
    t["tva_payee"] = [0.0] + [r["tva_collectee"][m - 1] - t["tva_deductible"][m - 1] for m in range(1, N)]
    t["is_paye"] = [0.0] * N
    t["dec_total"] = [t["achats_stock"][m] + t["tva_achats"][m] + t["logistique_ttc"][m] + r["pub"][m] + r["ech"][m]
                      + r["frais_fixes"][m] + t["remboursements"][m] + t["tva_payee"][m] + t["is_paye"][m] for m in rng]
    t["flux"] = [t["enc_total"][m] - t["dec_total"][m] for m in rng]
    t["treso"] = []
    s = V["TRESO_INITIALE"]
    for x in t["flux"]:
        s += x
        t["treso"].append(s)
    t["besoin"] = -min(0.0, min(t["treso"]))
    t["mois_creux"] = MOIS[t["treso"].index(min(t["treso"]))]
    r["treso"] = t
    # Règle d'arrêt (04 §6.3) : bénéfice net négatif 3 mois de suite après le mois 4
    r["arret"] = None
    for m in range(5, N):
        if all(r["benefice"][k] < 0 for k in (m - 2, m - 1, m)):
            r["arret"] = m
            break
    return r, e


# =============================================================================
# 5. PALIERS
# =============================================================================


def calc_paliers(mo):
    P = []
    # Palier 1 : micro-stock, organique, mix de lancement
    f1 = (V["COMPTABLE"] + V["BANQUE"] + V["OUTILS"] + V["RC"] + V["DOMICILIATION"]
          + V["LEKO"] / 12 + V["MEDIATEUR"] / 36 + V["DOMAINE"] / 12)
    m1 = mo["MIX_MARGE_MS"]
    n1 = (1000 + f1 + V["P1_ECH"]) / m1
    ca_ht1 = n1 * mo["MIX_HT"]
    stock1 = V["COUV_MICRO"] * n1 * mo["MIX_PROD_MS"]
    tts_net = mo["TTS_TTC"] * (1 - V["TTS_COMM"]) - V["MIX_AFF"] / (1 - V["MIX_SITE"]) * mo["TTS_TTC"] * V["CREA_COMM"]
    cre1 = n1 * (1 - V["MIX_SITE"]) * tts_net * (V["TTS_LIVRAISON"] + V["TTS_STANDARD"] + V["TTS_VIREMENT"]) / 30 \
        + n1 * V["MIX_SITE"] * (mo["SITE_TTC"] - mo["SITE_PAY"]) * V["STRIPE_DELAI"] / 30
    tva1 = n1 * (mo["MIX_TTC"] - mo["MIX_HT"]) - V["TVA"] * n1 * (mo["MIX_PROD_MS"] + mo["MIX_LOG_MS"])
    P.append(dict(cle="1k", benefice=1000, marge_cmd=m1, frais_fixes=f1 + V["P1_ECH"], commandes=n1, ca_ht=ca_ht1,
                  ca_ttc=n1 * mo["MIX_TTC"], pub=0.0, stock=stock1, creances=cre1, dettes=tva1,
                  bfr=stock1 + cre1 - tva1))
    # Palier 2 : import groupé + 3PL + publicité au CPA cible (MER ≥ 1,2 × rentabilité)
    s = V["P2_PART_PUB"]
    cpa2 = mo["PUB_MARGE_AVANT_PUB_IMP"] / V["MER_MARGE"]
    m_org = mo["MIX_MARGE_IMP"]
    m_pub = mo["PUB_MARGE_AVANT_PUB_IMP"] - cpa2
    f2 = V["P2_FIXES_AUTRES"] + V["P2_PERSONNEL"] + V["P2_ECH"]
    blend = (1 - s) * m_org + s * m_pub
    n2 = (10000 + f2) / blend
    ca_ht2 = n2 * ((1 - s) * mo["MIX_HT"] + s * mo["PUB_HT"])
    ca_ttc2 = n2 * ((1 - s) * mo["MIX_TTC"] + s * mo["PUB_TTC"])
    prod2 = n2 * ((1 - s) * mo["MIX_PROD_IMP"] + s * mo["PUB_PROD_IMP"])
    log2 = n2 * ((1 - s) * mo["MIX_LOG_IMP"] + s * mo["PUB_LOG_IMP"])
    stock2 = V["COUV_IMPORT"] * prod2
    cre2 = n2 * (1 - s) * (1 - V["MIX_SITE"]) * tts_net * (V["TTS_LIVRAISON"] + V["TTS_STANDARD"] + V["TTS_VIREMENT"]) / 30 \
        + n2 * ((1 - s) * V["MIX_SITE"] * (mo["SITE_TTC"] - mo["SITE_PAY"]) + s * (mo["PUB_TTC"] - mo["PUB_PAY"])) * V["STRIPE_DELAI"] / 30
    tva2 = (ca_ttc2 - ca_ht2) - V["TVA"] * log2
    P.append(dict(cle="10k", benefice=10000, marge_cmd=blend, frais_fixes=f2, commandes=n2, ca_ht=ca_ht2, ca_ttc=ca_ttc2,
                  pub=n2 * s * cpa2, cpa=cpa2, stock=stock2, creances=cre2, dettes=tva2, bfr=stock2 + cre2 - tva2))
    # Paliers 3 et 4 : approche descendante
    for cle, ben, pre in (("100k", 100000, "P3"), ("1M", 1000000, "P4")):
        ca_ht = ben / V[f"{pre}_MARGE"]
        ca_ttc = ca_ht * (1 + V["TVA"])
        n = ca_ttc / V[f"{pre}_PANIER"]
        stock = V["COUV_IMPORT"] * V[f"{pre}_COGS"] * ca_ht
        cre = V["PART_MARKETPLACE"] * ca_ttc * V["CREANCES_JOURS"] / 30
        dettes = V["DETTES_FOURN_PART"] * V[f"{pre}_COGS"] * ca_ht + V["TVA"] * ca_ht * V["TVA_NETTE_RATIO"]
        P.append(dict(cle=cle, benefice=ben, marge_cmd=ben / n, frais_fixes=None, commandes=n, ca_ht=ca_ht, ca_ttc=ca_ttc,
                      pub=V[f"{pre}_PUB"] * ca_ht, stock=stock, creances=cre, dettes=dettes, bfr=stock + cre - dettes))
    QUAL = {
        "1k": dict(effectif="Fondateur seul, 25 h par semaine", effectif_n=1,
                   probabilite_strategie="10-20 % à 12 mois (alignée sur la finance, correction M6)",
                   probabilite_finance="10-20 % à 12 mois : P(porte 1) 35-50 % × P(trajectoire réaliste ou mieux, porte 1 franchie) 30-40 % ; la red team l'estime à 5-12 %",
                   delai="3 à 12 mois après les premières ventes (novembre 2027 dans le scénario réaliste)",
                   conditions="Porte 1, porte stock et porte 2 franchies ; ≈ 15 affiliés actifs ; 2 vidéos par jour ; marge moyenne ≥ marge du mix de lancement"),
        "10k": dict(effectif="2 à 3 personnes : fondateur, assistant SAV à mi-temps, media buyer indépendant ; 3PL", effectif_n=2.5,
                    probabilite_strategie="3-5 % à 24 mois (alignée sur la finance)",
                    probabilite_finance="3-5 % à 24 mois : P(porte 1) 35-50 % × P(trajectoire optimiste, porte 1 franchie) 8-10 % ; le CPA cible ≤ 16,70 € est le verrou",
                    delai="9 à 18 mois après le palier 1",
                    conditions="Import groupé, 3PL, marque déposée, publicité rentable avec MER ≥ 1,2 × rentabilité ; aucune publicité au-delà de 1 000 € par mois sans un produit à ≥ 15 % de réachat à 180 jours (M17) ; sortie de la franchise de TVA et de la micro-entreprise"),
        "100k": dict(effectif="8 à 15 personnes ; 20-40 références", effectif_n=12,
                     probabilite_strategie="Non chiffrée : repère d'échelle sans base produit (correction M17)", probabilite_finance="Non chiffrée : repère d'échelle obtenu par ratios, sans consommable ni valeur vie client modélisés",
                     delai="18 à 36 mois après le palier 2",
                     conditions="France < 50 % du CA ; Allemagne, Italie, Espagne ; Amazon UE ; financement de stock bancaire ou BPI"),
        "1M": dict(effectif="50 à 100 personnes ; plusieurs gammes", effectif_n=75,
                   probabilite_strategie="Non chiffrée : repère d'échelle sans base produit (correction M17)", probabilite_finance="Non chiffrée : hors de portée du projet tel qu'il est financé",
                   delai="3 à 5 ans après le palier 3",
                   conditions="10 pays et plus, distribution physique, levée de fonds ou rachat de marques ; place l'entreprise dans le 1 % des sites qui font 78 % du CA"),
    }
    for p in P:
        p.update(QUAL[p["cle"]])
        p["commandes_jour"] = p["commandes"] / 30
    return P


# =============================================================================
# 6. SENSIBILITÉ (modèle réduit, identique dans Excel)
# =============================================================================
VARS_SENS = [
    ("kVol", "Volume de commandes organiques"),
    ("kPrix", "Prix de vente (tous produits)"),
    ("kProd", "Coût produit et droits"),
    ("kLog", "Livraison et emballage"),
    ("kPay", "Frais de paiement"),
    ("kTTS", "Commission TikTok Shop"),
    ("kCrea", "Commission des créateurs"),
    ("kRet", "Retours, SAV et litiges"),
    ("kAff", "Part des ventes par affiliés"),
    ("kFix", "Frais fixes"),
    ("kEch", "Échantillons créateurs"),
    ("kCPA", "CPA publicitaire"),
    ("kPubVol", "Budget publicitaire"),
]
CANAUX_SENS = ["site", "propre", "aff", "pub"]


def base_sens_palier1(mo, real):
    m = 11  # sept. 2027 dans le scénario réaliste
    comp = {}
    for c, n in (("site", real["cmd_site"][m]), ("propre", real["cmd_propre"][m]), ("aff", real["cmd_aff"][m]), ("pub", 0.0)):
        comp[c] = composantes_canal(mo, c, "MS", real["taux_tts"][m], n)
    return dict(libelle=f"Palier 1 — scénario réaliste, {MOIS[m]}", comp=comp, F=real["frais_fixes"][m], E=real["ech"][m],
                budget=0.0, cpa=0.0)


def base_sens_palier2(mo, pal2):
    n, s = pal2["commandes"], V["P2_PART_PUB"]
    comp = {
        "site": composantes_canal(mo, "site", "IMP", V["TTS_COMM"], n * (1 - s) * V["MIX_SITE"]),
        "propre": composantes_canal(mo, "propre", "IMP", V["TTS_COMM"], n * (1 - s) * V["MIX_PROPRE"]),
        "aff": composantes_canal(mo, "aff", "IMP", V["TTS_COMM"], n * (1 - s) * V["MIX_AFF"]),
        "pub": composantes_canal(mo, "pub", "IMP", V["TTS_COMM"], n * s),
    }
    return dict(libelle="Palier 2 — 10 000 € de bénéfice (import groupé, 3PL, publicité)", comp=comp,
                F=V["P2_FIXES_AUTRES"] + V["P2_PERSONNEL"], E=V["P2_ECH"], budget=n * s * pal2["cpa"], cpa=pal2["cpa"])


def composantes_canal(mo, c, ph, taux, n):
    if c == "site":
        ttc, ht, prod, log = mo["SITE_TTC"], mo["SITE_HT"], mo[f"SITE_PROD_{ph}"], mo[f"SITE_LOG_{ph}"]
    elif c == "pub":
        ttc, ht, prod, log = mo["PUB_TTC"], mo["PUB_HT"], mo[f"PUB_PROD_{ph}"], mo[f"PUB_LOG_{ph}"]
    else:
        ttc, ht, prod, log = mo["TTS_TTC"], mo["TTS_HT"], mo[f"TTS_PROD_{ph}"], mo[f"TTS_LOG_{ph}"]
    web = c in ("site", "pub")
    return dict(n=n, ht=ht, prod=prod, log=log, paypct=V["STRIPE_PCT"] * ttc if web else 0.0,
                payfix=V["STRIPE_FIXE"] if web else 0.0, tts=taux * ttc if c in ("propre", "aff") else 0.0,
                crea=V["CREA_COMM"] * ttc if c == "aff" else 0.0, prov=V["PROV_RETOURS"] * ht)


def benef_sens(b, k):
    comp = b["comp"]
    kk = {v: k.get(v, 1.0) for v, _ in VARS_SENS}

    def marge(c):
        x = comp[c]
        return (kk["kPrix"] * x["ht"] - kk["kProd"] * x["prod"] - kk["kLog"] * x["log"]
                - kk["kPay"] * (x["paypct"] * kk["kPrix"] + x["payfix"]) - kk["kTTS"] * x["tts"] * kk["kPrix"]
                - kk["kCrea"] * x["crea"] * kk["kPrix"] - kk["kRet"] * x["prov"] * kk["kPrix"])
    n_site = comp["site"]["n"] * kk["kVol"]
    n_aff = comp["aff"]["n"] * kk["kVol"] * kk["kAff"]
    n_propre = (comp["propre"]["n"] + comp["aff"]["n"] * (1 - kk["kAff"])) * kk["kVol"]
    budget = b["budget"] * kk["kPubVol"]
    n_pub = budget / (b["cpa"] * kk["kCPA"]) if b["cpa"] > 0 else 0.0
    return (n_site * marge("site") + n_propre * marge("propre") + n_aff * marge("aff") + n_pub * marge("pub")
            - budget - kk["kFix"] * b["F"] - kk["kEch"] * b["E"])


def calc_sensibilite(b, variables):
    base = benef_sens(b, {})
    lignes = []
    for v, lib in variables:
        bas = benef_sens(b, {v: 0.8})
        haut = benef_sens(b, {v: 1.2})
        lignes.append(dict(variable=lib, code=v, moins_20=bas, plus_20=haut, impact_moins_20=bas - base,
                           impact_plus_20=haut - base, amplitude=abs(haut - bas)))
    lignes.sort(key=lambda d: -d["amplitude"])
    return base, lignes


# =============================================================================
# 7. CLASSEUR EXCEL
# =============================================================================
F_TITRE = Font(bold=True, size=14, color="2F4A3C")
F_GRAS = Font(bold=True)
F_ENTETE = Font(bold=True, color="FFFFFF")
F_SAISIE = Font(color="0000FF")
F_NOTE = Font(italic=True, color="6A5B50", size=9)
FILL_ENTETE = PatternFill("solid", fgColor="2F4A3C")
FILL_SECTION = PatternFill("solid", fgColor="F3E7D8")
FILL_TOTAL = PatternFill("solid", fgColor="FAF5EE")
FILL_CLE = PatternFill("solid", fgColor="FBE3D6")
BORD = Border(bottom=Side(style="thin", color="D9CFC4"))
EUR = '#,##0.00 "€";[Red]-#,##0.00 "€"'
EUR0 = '#,##0 "€";[Red]-#,##0 "€"'
PCT = "0.0%"
NB = "#,##0.0"
NB0 = "#,##0"
X2 = "0.00"

S_HYP, S_UE, S_SCEN, S_TRESO, S_PAL, S_SENS = ("Hypothèses", "Unit economics", "Scénarios 18 mois", "Trésorerie",
                                                "Paliers", "Sensibilité")


def q(feuille):
    return "'" + feuille + "'"


def nommer(wb, nom, feuille, cell):
    col = "".join(ch for ch in cell if ch.isalpha())
    row = "".join(ch for ch in cell if ch.isdigit())
    wb.defined_names[nom] = DefinedName(nom, attr_text=f"{q(feuille)}!${col}${row}")


def entete(ws, row, valeurs, col0=1):
    for i, v in enumerate(valeurs):
        c = ws.cell(row=row, column=col0 + i, value=v)
        c.font = F_ENTETE
        c.fill = FILL_ENTETE
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")


def fmt_unite(u):
    if u.startswith("%") or u.startswith("% "):
        return PCT
    if "€" in u:
        return '#,##0.00 "€"'
    return "General"


def feuille_hypotheses(wb, saisies):
    ws = wb.active
    ws.title = S_HYP
    ws["A1"] = "Canapoil — hypothèses du modèle financier"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Toutes les valeurs en bleu sont des saisies ; chaque cellule de la colonne C porte un nom défini "
                "« h_NOM » utilisé par les autres onglets. Prix et coûts produits = brand.json.")
    ws["A2"].font = F_NOTE
    row = 4
    entete(ws, row, ["Nom Excel", "Hypothèse", "Valeur", "Unité", "Source / confiance"])
    row += 1
    for titre, lignes in HYPOTHESES:
        ws.cell(row=row, column=1, value=titre).font = F_GRAS
        for col in range(1, 6):
            ws.cell(row=row, column=col).fill = FILL_SECTION
        row += 1
        for nom, lib, val, unite, src in lignes:
            ws.cell(row=row, column=1, value="h_" + nom)
            ws.cell(row=row, column=2, value=lib)
            c = ws.cell(row=row, column=3, value=val)
            c.font = F_SAISIE
            c.number_format = fmt_unite(unite)
            ws.cell(row=row, column=4, value=unite)
            ws.cell(row=row, column=5, value=src).alignment = Alignment(wrap_text=False)
            nommer(wb, "h_" + nom, S_HYP, f"C{row}")
            row += 1
    # Saisies mensuelles des scénarios
    row += 1
    ws.cell(row=row, column=1, value="Scénarios — saisies mensuelles (volumes, budgets, phases)").font = F_TITRE
    row += 1
    ws.cell(row=row, column=1, value=("Commandes organiques et parts de canal : saisies. Taux TikTok, CPA, couverture de stock "
                                      "et délais : formules liées aux hypothèses ci-dessus. Frais fixes : calculés par le script "
                                      "selon les règles d'activation (Shopify dès 5 commandes/jour sur le site, la publicité ou le 3PL ; "
                                      "domiciliation dès 150 commandes/mois ; INPI dès 90 ; assistant SAV dès 1 000 ; media buyer dès 3 000 € de publicité).")).font = F_NOTE
    row += 2
    refs = {}
    libelles = [
        ("exercice", "Exercice fiscal", "General"), ("cmd_org", "Commandes organiques (tous canaux)", NB0),
        ("part_site", "Part du site", PCT), ("part_propre", "Part TikTok Shop, contenu propre", PCT),
        ("part_aff", "Part TikTok Shop, affiliés", PCT), ("taux_tts", "Commission TikTok Shop", PCT),
        ("import", "Phase import groupé + 3PL (1 = oui)", "0"), ("pub", "Budget publicitaire", EUR0),
        ("cpa", "CPA", EUR), ("ech", "Échantillons créateurs", EUR0), ("couverture", "Stock détenu en fin de mois (mois de ventes suivantes)", X2),
        ("delai_site", "Délai d'encaissement du site (jours)", NB0), ("delai_tts", "Délai d'encaissement TikTok Shop depuis la commande (jours)", NB0),
        ("ff_structure", "Frais fixes : structure (comptable, banque)", EUR0),
        ("ff_conformite", "Frais fixes : conformité et ponctuels (médiateur, Léko, RC, INPI, EUIPO, domaine, prime de lancement)", EUR0),
        ("ff_outils", "Frais fixes : outils, Shopify, domiciliation", EUR0),
        ("ff_import", "Frais fixes : import et stockage 3PL", EUR0), ("ff_personnel", "Frais fixes : personnel", EUR0),
    ]
    formules = {"taux_tts", "cpa", "couverture", "delai_site", "delai_tts"}
    for cle, (sc, e, r) in saisies.items():
        ws.cell(row=row, column=1, value=f"Scénario {SCENARIOS[cle]['libelle'].lower()}").font = F_GRAS
        for col in range(1, 21):
            ws.cell(row=row, column=col).fill = FILL_SECTION
        row += 1
        entete(ws, row, ["Ligne", "Libellé"] + MOIS)
        row += 1
        for k, lib, nf in libelles:
            ws.cell(row=row, column=1, value=k)
            ws.cell(row=row, column=2, value=lib)
            for m in range(N):
                cell = ws.cell(row=row, column=3 + m)
                if k in formules:
                    cell.value = "=" + e[k][m]
                elif k.startswith("ff_"):
                    cell.value = round(r[k][m], 2)
                    cell.font = Font(color="7F6000")
                else:
                    cell.value = e[k][m]
                    cell.font = F_SAISIE
                cell.number_format = nf
            refs[(cle, k)] = row
            row += 1
        row += 1
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 58
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 70
    for col in range(6, 21):
        ws.column_dimensions[get_column_letter(col)].width = 11
    ws.freeze_panes = "C5"
    return refs


UE_COLS = ["Cas", "Canal", "Poids (g)", "Prix payé TTC", "TVA collectée", "CA HT (base)", "Coût produit",
           "Droits de douane", "Livraison + emballage", "Frais de paiement", "Commission TikTok Shop",
           "Commission créateur ou pub", "Provision retours / litiges", "Cotisations micro", "Marge de contribution",
           "% du CA HT", "ROAS de rentabilité HT", "ROAS de rentabilité TTC", "CPA maximal"]


def formules_cas(cas, row, phase, regime, lourd=False):
    _id, _lib, canal, compo, prix_nom, aff, taux_nom, cpa_nom = cas
    K = "" if regime == "ASS" else "*(1+h_TVA)"
    poids = "+".join(f"h_{c}_POIDS" for c in compo)
    f = {}
    f["C"] = "=" + poids
    if canal in ("site", "pub"):
        f["D"] = f"=h_{prix_nom}+IF(h_{prix_nom}<h_SEUIL_GRATUIT,h_PORT_CLIENT_TTC,0)"
    else:
        f["D"] = f"=h_{prix_nom}"
    f["E"] = f"=D{row}-D{row}/(1+h_TVA)" if regime == "ASS" else "=0"
    f["F"] = f"=D{row}-E{row}"
    if phase == "MS":
        f["G"] = "=(" + "+".join(f"h_{c}_PROD" for c in compo) + ")" + K
        f["H"] = "=(" + "+".join(f"h_{c}_DROITS" for c in compo) + ")" + K
        if lourd:
            f["I"] = "=(h_PORT_1KG+h_EMB_GRAND)" + K
        else:
            p5, p1 = ("h_PORT_TTS_500", "h_PORT_TTS_1KG") if canal == "tts" else ("h_PORT_500", "h_PORT_1KG")
            f["I"] = (f"=IF(C{row}<=500,{p5}+h_EMB_PETIT,IF(C{row}<=1000,{p1}+h_EMB_GRAND,"
                      f"h_PORT_2KG+h_EMB_GRAND))" + K)
    else:
        f["G"] = "=" + "+".join(f"h_IMP_{c}" for c in compo)
        f["H"] = "=0"
        p5, p1 = ("h_PORT_TTS_500", "h_PORT_TTS_1KG") if canal == "tts" else ("h_PORT_500", "h_PORT_1KG")
        f["I"] = f"=IF(C{row}<=500,{p5},IF(C{row}<=1000,{p1},h_PORT_2KG))+h_TPL_PREP"
    f["J"] = f"=h_STRIPE_PCT*D{row}+h_STRIPE_FIXE" if canal in ("site", "pub") else "=0"
    f["K"] = f"=h_{taux_nom}*D{row}" + K if canal == "tts" else "=0"
    if aff:
        f["L"] = f"=h_CREA_COMM*D{row}" + K
    elif canal == "pub":
        f["L"] = f"=h_{cpa_nom}" + K
    else:
        f["L"] = "=0"
    f["M"] = f"=h_PROV_RETOURS*F{row}"
    f["N"] = f"=h_MICRO_COTIS*D{row}" if regime == "MICRO" else "=0"
    f["O"] = f"=F{row}-SUM(G{row}:N{row})"
    f["P"] = f"=O{row}/F{row}"
    avant = f"(O{row}+L{row})" if canal == "pub" else f"O{row}"
    if canal == "tts" and aff:
        f["Q"] = f["R"] = f["S"] = None
    else:
        f["Q"] = f"=F{row}/{avant}"
        f["R"] = f"=D{row}/{avant}"
        f["S"] = f"={avant}"
    return f


def feuille_unit_economics(wb, ue, mo):
    ws = wb.create_sheet(S_UE)
    ws["A1"] = "Unit economics par commande (€)"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Marge de contribution = CA HT − coûts variables (produit, droits, livraison, paiement, commissions, "
                "provision 5 % du CA HT). En franchise et en micro-entreprise, le CA est le prix payé et les coûts portent "
                "la TVA non récupérable (×1,2), sauf les frais de paiement.")
    ws["A2"].font = F_NOTE
    pos = {}
    row = 4
    blocs = [
        ("Société assujettie à la TVA (SASU ou EURL à l'IS) — micro-stock en France (lancement)", "MS", "ASS",
         CAS_MS + [CAS_RISQUE_GK]),
        ("Société assujettie — import groupé + 3PL (palier 2)", "IMP", "ASS", CAS_IMP),
        ("Société en franchise en base de TVA — micro-stock", "MS", "FR", CAS_REGIME),
        ("Micro-entreprise en franchise de TVA — micro-stock (après cotisations de 12,3 %)", "MS", "MICRO", CAS_REGIME),
    ]
    for titre, phase, regime, cas_liste in blocs:
        ws.cell(row=row, column=1, value=titre).font = F_GRAS
        for col in range(1, 20):
            ws.cell(row=row, column=col).fill = FILL_SECTION
        row += 1
        entete(ws, row, UE_COLS)
        row += 1
        for cas in cas_liste:
            lourd = cas[0] == "site-gk-lourd"
            ws.cell(row=row, column=1, value=cas[1])
            ws.cell(row=row, column=2, value={"site": "Site", "tts": "TikTok Shop", "pub": "Site + publicité"}[cas[2]])
            f = formules_cas(cas, row, phase, regime, lourd)
            for col_l, formule in f.items():
                if formule is None:
                    continue
                c = ws[f"{col_l}{row}"]
                c.value = formule
                c.number_format = {"C": NB0, "P": PCT, "Q": X2, "R": X2}.get(col_l, EUR)
            ws[f"O{row}"].font = F_GRAS
            bloc = {"ASS": phase, "FR": "FR", "MICRO": "MICRO"}[regime]
            pos[(bloc, cas[0])] = row
            row += 1
        row += 1
    # Moyennes pondérées
    ws.cell(row=row, column=1, value="Composantes moyennes par commande et par canal (utilisées par les scénarios)").font = F_GRAS
    for col in range(1, 20):
        ws.cell(row=row, column=col).fill = FILL_SECTION
    row += 1
    entete(ws, row, ["Nom Excel", "Définition", "Valeur"])
    row += 1
    S = [("SITE_ROU", "rou"), ("SITE_KAP", "kap"), ("SITE_GK", "gk"), ("SITE_DUO", "duo")]
    T = [("TTS_ROU", "rou"), ("TTS_KAP", "kap")]

    def pond(bloc, prefix, poids, cols):
        termes = []
        for nom, k in poids:
            r_ = pos[(bloc, f"{prefix}{k}")]
            termes.append(f"h_{nom}*(" + "+".join(f"{c}{r_}" for c in cols) + ")")
        return "=" + "+".join(termes)

    defs = []
    for ph, pre in (("MS", ""), ("IMP", "imp-")):
        if ph == "MS":
            defs += [("SITE_TTC", "Site organique : panier TTC", pond(ph, pre + "site-", S, ["D"])),
                     ("SITE_HT", "Site organique : CA HT", pond(ph, pre + "site-", S, ["F"])),
                     ("SITE_PAY", "Site organique : frais de paiement", pond(ph, pre + "site-", S, ["J"])),
                     ("TTS_TTC", "TikTok Shop : panier TTC", pond(ph, pre + "tts-propre-", T, ["D"])),
                     ("TTS_HT", "TikTok Shop : CA HT", pond(ph, pre + "tts-propre-", T, ["F"])),
                     ("PUB_TTC", "Commande payante (Grand kit) : prix TTC", f"=D{pos[(ph, 'site-gk')]}"),
                     ("PUB_HT", "Commande payante : CA HT", f"=F{pos[(ph, 'site-gk')]}"),
                     ("PUB_PAY", "Commande payante : frais de paiement", f"=J{pos[(ph, 'site-gk')]}")]
        lib = "micro-stock" if ph == "MS" else "import + 3PL"
        defs += [(f"SITE_PROD_{ph}", f"Site : produit + droits, {lib}", pond(ph, pre + "site-", S, ["G", "H"])),
                 (f"SITE_LOG_{ph}", f"Site : livraison, {lib}", pond(ph, pre + "site-", S, ["I"])),
                 (f"SITE_MARGE_{ph}", f"Site : marge de contribution, {lib}", pond(ph, pre + "site-", S, ["O"])),
                 (f"TTS_PROD_{ph}", f"TikTok Shop : produit + droits, {lib}", pond(ph, pre + "tts-propre-", T, ["G", "H"])),
                 (f"TTS_LOG_{ph}", f"TikTok Shop : livraison, {lib}", pond(ph, pre + "tts-propre-", T, ["I"])),
                 (f"PROPRE_MARGE_{ph}", f"TikTok Shop contenu propre (9 %) : marge, {lib}", pond(ph, pre + "tts-propre-", T, ["O"])),
                 (f"AFF_MARGE_{ph}", f"TikTok Shop affilié (9 % + 15 %) : marge, {lib}", pond(ph, pre + "tts-aff-", T, ["O"])),
                 (f"PUB_PROD_{ph}", f"Commande payante : produit + droits, {lib}", f"=G{pos[(ph, pre + 'site-gk')]}+H{pos[(ph, pre + 'site-gk')]}"),
                 (f"PUB_LOG_{ph}", f"Commande payante : livraison, {lib}", f"=I{pos[(ph, pre + 'site-gk')]}"),
                 (f"PUB_MARGE_AVANT_PUB_{ph}", f"Commande payante : marge avant publicité, {lib}", f"=O{pos[(ph, pre + 'site-gk')]}"),
                 (f"MIX_MARGE_{ph}", f"Mix de lancement (20/22/58) : marge moyenne, {lib}",
                  f"=h_MIX_SITE*ue_SITE_MARGE_{ph}+h_MIX_PROPRE*ue_PROPRE_MARGE_{ph}+h_MIX_AFF*ue_AFF_MARGE_{ph}"),
                 (f"MIX_PROD_{ph}", f"Mix : produit + droits, {lib}", f"=h_MIX_SITE*ue_SITE_PROD_{ph}+(1-h_MIX_SITE)*ue_TTS_PROD_{ph}"),
                 (f"MIX_LOG_{ph}", f"Mix : livraison, {lib}", f"=h_MIX_SITE*ue_SITE_LOG_{ph}+(1-h_MIX_SITE)*ue_TTS_LOG_{ph}")]
    defs += [("MIX_TTC", "Mix : panier moyen TTC", "=h_MIX_SITE*ue_SITE_TTC+(1-h_MIX_SITE)*ue_TTS_TTC"),
             ("MIX_HT", "Mix : CA HT moyen", "=h_MIX_SITE*ue_SITE_HT+(1-h_MIX_SITE)*ue_TTS_HT")]
    for reg, lib in (("FR", "franchise de TVA"), ("MICRO", "micro-entreprise")):
        defs += [(f"SITE_MARGE_{reg}", f"Site : marge, {lib}", pond(reg, "site-", S, ["O"])),
                 (f"PROPRE_MARGE_{reg}", f"TikTok Shop contenu propre : marge, {lib}", pond(reg, "tts-propre-", T, ["O"])),
                 (f"AFF_MARGE_{reg}", f"TikTok Shop affilié : marge, {lib}", pond(reg, "tts-aff-", T, ["O"])),
                 (f"MIX_MARGE_{reg}", f"Mix de lancement : marge moyenne, {lib}",
                  f"=h_MIX_SITE*ue_SITE_MARGE_{reg}+h_MIX_PROPRE*ue_PROPRE_MARGE_{reg}+h_MIX_AFF*ue_AFF_MARGE_{reg}")]
    for nom, lib, formule in defs:
        ws.cell(row=row, column=1, value="ue_" + nom)
        ws.cell(row=row, column=2, value=lib)
        c = ws.cell(row=row, column=3, value=formule)
        c.number_format = EUR
        if "MARGE" in nom:
            c.font = F_GRAS
        nommer(wb, "ue_" + nom, S_UE, f"C{row}")
        row += 1
    # Seuils
    row += 1
    ws.cell(row=row, column=1, value="Seuils de rentabilité publicitaire et point mort").font = F_GRAS
    for col in range(1, 20):
        ws.cell(row=row, column=col).fill = FILL_SECTION
    row += 1
    entete(ws, row, ["Offre", "Marge avant pub (€)", "% du CA HT", "ROAS rentabilité HT", "ROAS rentabilité TTC",
                     "CPA maximal (€)", "CPA cible MER ×1,2 (€)", "ROAS cible TTC"])
    row += 1
    seuils_rows = {}
    for bloc, cid, lib in (("MS", "site-rou", "Site — Rouleau seul (micro-stock)"), ("MS", "site-kap", "Site — Kit anti-poils (micro-stock)"),
                           ("MS", "site-gk", "Site — Grand kit (micro-stock)"), ("MS", "site-hiv", "Site — Kit chat d'hiver (micro-stock)"),
                           ("IMP", "imp-site-gk", "Site — Grand kit (import + 3PL)"), ("IMP", "imp-site-rou", "Site — Rouleau seul (import + 3PL)")):
        r_ = pos[(bloc, cid)]
        ws.cell(row=row, column=1, value=lib)
        ws.cell(row=row, column=2, value=f"=O{r_}").number_format = EUR
        ws.cell(row=row, column=3, value=f"=O{r_}/F{r_}").number_format = PCT
        ws.cell(row=row, column=4, value=f"=F{r_}/O{r_}").number_format = X2
        ws.cell(row=row, column=5, value=f"=D{r_}/O{r_}").number_format = X2
        ws.cell(row=row, column=6, value=f"=O{r_}").number_format = EUR
        ws.cell(row=row, column=7, value=f"=O{r_}/h_MER_MARGE").number_format = EUR
        ws.cell(row=row, column=8, value=f"=D{r_}/(O{r_}/h_MER_MARGE)").number_format = X2
        seuils_rows[cid] = row
        row += 1
    row += 1
    ws.cell(row=row, column=1, value="Point mort du palier 1 (commandes / mois)")
    ws.cell(row=row, column=2, value=("=(h_COMPTABLE+h_BANQUE+h_OUTILS+h_RC+h_DOMICILIATION+h_LEKO/12+h_MEDIATEUR/36"
                                      "+h_DOMAINE/12+h_P1_ECH)/ue_MIX_MARGE_MS")).number_format = NB
    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 44
    for col in range(3, 20):
        ws.column_dimensions[get_column_letter(col)].width = 13
    ws.freeze_panes = "C4"
    return pos


SCEN_LIGNES = [
    # (clé, libellé, format, gras)
    ("mois", "Mois", None, True),
    ("exercice", "Exercice", "General", False),
    ("cmd_site", "Commandes site (organique)", NB, False),
    ("cmd_propre", "Commandes TikTok Shop, contenu propre", NB, False),
    ("cmd_aff", "Commandes TikTok Shop, affiliés", NB, False),
    ("cmd_pub", "Commandes issues de la publicité", NB, False),
    ("cmd_total", "Commandes totales", NB0, True),
    ("cmd_jour", "Commandes par jour", NB, False),
    ("ca_ttc", "CA TTC", EUR0, False),
    ("ca_ht", "CA HT", EUR0, True),
    ("tva_collectee", "TVA collectée", EUR0, False),
    ("c_produits", "Coût des produits et droits", EUR0, False),
    ("c_logistique", "Livraison, emballage, 3PL", EUR0, False),
    ("c_paiement", "Frais de paiement", EUR0, False),
    ("c_tts", "Commission TikTok Shop", EUR0, False),
    ("c_crea", "Commission des créateurs", EUR0, False),
    ("c_prov", "Provision retours, SAV, litiges", EUR0, False),
    ("marge_contrib", "Marge de contribution", EUR0, True),
    ("pub", "Publicité", EUR0, False),
    ("ech", "Échantillons créateurs", EUR0, False),
    ("frais_fixes", "Frais fixes et ponctuels", EUR0, False),
    ("benefice", "Bénéfice net (avant IS et rémunération du dirigeant)", EUR0, True),
    ("benefice_cumul", "Bénéfice net cumulé", EUR0, False),
    ("couts_totaux", "Coûts totaux (CA HT − bénéfice net)", EUR0, False),
    ("nouvel_ex", "Nouvel exercice (1 = oui)", "0", False),
    ("base_is", "Base IS cumulée de l'exercice (déficit antérieur reporté)", EUR0, False),
    ("is_cumul", "IS cumulé de l'exercice", EUR0, False),
    ("is_mois", "IS du mois (provision)", EUR0, False),
    ("resultat_apres_is", "Résultat après IS", EUR0, True),
]


def col(m):
    return get_column_letter(3 + m)


def feuille_scenarios(wb, refs):
    ws = wb.create_sheet(S_SCEN)
    ws["A1"] = "Scénarios sur 18 mois (octobre 2026 → mars 2028) — société assujettie à la TVA"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Tous les calculs sont des formules. Les saisies (volumes, parts de canal, budgets, frais fixes) sont "
                "dans l'onglet Hypothèses. Bénéfice net = avant IS et avant rémunération du dirigeant.")
    ws["A2"].font = F_NOTE
    pos = {}
    row = 4
    H = q(S_HYP)
    for cle, sc in SCENARIOS.items():
        ws.cell(row=row, column=1, value=f"Scénario {sc['libelle'].lower()} — {sc['description']}").font = F_GRAS
        for c_ in range(1, 22):
            ws.cell(row=row, column=c_).fill = FILL_SECTION
        row += 1
        lr = {}
        for i, (k, *_r) in enumerate(SCEN_LIGNES):
            lr[k] = row + i
        for k, lib, nf, gras in SCEN_LIGNES:
            r = lr[k]
            ws.cell(row=r, column=1, value=lib).font = F_GRAS if gras else Font()
            if k == "mois":
                entete(ws, r, ["Ligne", ""] + MOIS + ["Total 18 mois"])
                continue
            for m in range(N):
                C, P_ = col(m), (col(m - 1) if m > 0 else None)

                def h(key):
                    return f"{H}!{C}{refs[(cle, key)]}"
                L = {kk: f"{C}{lr[kk]}" for kk in lr}
                Lp = {kk: f"{P_}{lr[kk]}" for kk in lr} if P_ else None
                f = None
                if k == "exercice":
                    f = "=" + h("exercice")
                elif k == "cmd_site":
                    f = f"={h('cmd_org')}*{h('part_site')}"
                elif k == "cmd_propre":
                    f = f"={h('cmd_org')}*{h('part_propre')}"
                elif k == "cmd_aff":
                    f = f"={h('cmd_org')}*{h('part_aff')}"
                elif k == "cmd_pub":
                    f = f"=IF({h('cpa')}>0,{h('pub')}/{h('cpa')},0)"
                elif k == "cmd_total":
                    f = f"={L['cmd_site']}+{L['cmd_propre']}+{L['cmd_aff']}+{L['cmd_pub']}"
                elif k == "cmd_jour":
                    f = f"={L['cmd_total']}/30"
                elif k == "ca_ttc":
                    f = f"={L['cmd_site']}*ue_SITE_TTC+({L['cmd_propre']}+{L['cmd_aff']})*ue_TTS_TTC+{L['cmd_pub']}*ue_PUB_TTC"
                elif k == "ca_ht":
                    f = f"={L['ca_ttc']}/(1+h_TVA)"
                elif k == "tva_collectee":
                    f = f"={L['ca_ttc']}-{L['ca_ht']}"
                elif k in ("c_produits", "c_logistique"):
                    b = "PROD" if k == "c_produits" else "LOG"
                    imp = h("import")
                    f = (f"={L['cmd_site']}*IF({imp}=1,ue_SITE_{b}_IMP,ue_SITE_{b}_MS)"
                         f"+({L['cmd_propre']}+{L['cmd_aff']})*IF({imp}=1,ue_TTS_{b}_IMP,ue_TTS_{b}_MS)"
                         f"+{L['cmd_pub']}*IF({imp}=1,ue_PUB_{b}_IMP,ue_PUB_{b}_MS)")
                elif k == "c_paiement":
                    f = f"={L['cmd_site']}*ue_SITE_PAY+{L['cmd_pub']}*ue_PUB_PAY"
                elif k == "c_tts":
                    f = f"=({L['cmd_propre']}+{L['cmd_aff']})*ue_TTS_TTC*{h('taux_tts')}"
                elif k == "c_crea":
                    f = f"={L['cmd_aff']}*ue_TTS_TTC*h_CREA_COMM"
                elif k == "c_prov":
                    f = f"=h_PROV_RETOURS*{L['ca_ht']}"
                elif k == "marge_contrib":
                    f = f"={L['ca_ht']}-SUM({C}{lr['c_produits']}:{C}{lr['c_prov']})"
                elif k == "pub":
                    f = "=" + h("pub")
                elif k == "ech":
                    f = "=" + h("ech")
                elif k == "frais_fixes":
                    f = "=" + "+".join(h(x) for x in ("ff_structure", "ff_conformite", "ff_outils", "ff_import", "ff_personnel"))
                elif k == "benefice":
                    f = f"={L['marge_contrib']}-{L['pub']}-{L['ech']}-{L['frais_fixes']}"
                elif k == "benefice_cumul":
                    f = f"={L['benefice']}" + (f"+{Lp['benefice_cumul']}" if Lp else "")
                elif k == "couts_totaux":
                    f = f"={L['ca_ht']}-{L['benefice']}"
                elif k == "nouvel_ex":
                    f = "=1" if m == 0 else f"=IF({L['exercice']}<>{Lp['exercice']},1,0)"
                elif k == "base_is":
                    f = (f"={L['benefice']}" if m == 0 else
                         f"=IF({L['nouvel_ex']}=1,MIN(0,{Lp['base_is']})+{L['benefice']},{Lp['base_is']}+{L['benefice']})")
                elif k == "is_cumul":
                    f = f"=h_IS_TAUX_REDUIT*MIN(MAX({L['base_is']},0),h_IS_SEUIL)+h_IS_TAUX_NORMAL*MAX({L['base_is']}-h_IS_SEUIL,0)"
                elif k == "is_mois":
                    f = f"={L['is_cumul']}" if m == 0 else f"=IF({L['nouvel_ex']}=1,{L['is_cumul']},{L['is_cumul']}-{Lp['is_cumul']})"
                elif k == "resultat_apres_is":
                    f = f"={L['benefice']}-{L['is_mois']}"
                c = ws.cell(row=r, column=3 + m, value=f)
                c.number_format = nf
                if gras:
                    c.font = F_GRAS
                if k == "benefice":
                    c.fill = FILL_CLE
            if k not in ("exercice", "cmd_jour", "benefice_cumul", "nouvel_ex", "base_is", "is_cumul"):
                t = ws.cell(row=r, column=3 + N, value=f"=SUM({col(0)}{r}:{col(N - 1)}{r})")
                t.number_format = nf
                t.font = F_GRAS
        pos[cle] = lr
        row += len(SCEN_LIGNES) + 2
    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 2
    for c_ in range(3, 22):
        ws.column_dimensions[get_column_letter(c_)].width = 11
    ws.freeze_panes = "C4"
    return pos


TRESO_LIGNES = [
    ("mois", "Mois", None, True),
    ("site_du", "Ventes du site nettes de frais de paiement (dues)", EUR0, False),
    ("enc_site", "Encaissement Stripe / Shopify Payments", EUR0, False),
    ("tts_du", "Ventes TikTok Shop nettes de commissions (dues)", EUR0, False),
    ("delai_tts", "Délai d'encaissement TikTok Shop (jours)", NB0, False),
    ("w0", "Part encaissée le mois même", PCT, False),
    ("w1", "Part encaissée le mois suivant", PCT, False),
    ("w2", "Part encaissée à M+2", PCT, False),
    ("enc_tts", "Encaissement TikTok Shop", EUR0, False),
    ("enc_total", "Total des encaissements", EUR0, True),
    ("stock_fin", "Stock en fin de mois (coût HT)", EUR0, False),
    ("achats_stock", "Achats de stock HT (payés à la commande)", EUR0, False),
    ("achat_import", "Achat en import groupé (TVA autoliquidée, 1 = oui)", "0", False),
    ("tva_achats", "TVA payée sur achats de micro-stock", EUR0, False),
    ("logistique_ttc", "Étiquettes, emballage, 3PL (TTC)", EUR0, False),
    ("pub", "Publicité", EUR0, False),
    ("ech", "Échantillons créateurs", EUR0, False),
    ("frais_fixes", "Frais fixes et ponctuels", EUR0, False),
    ("remboursements", "Remboursements clients et SAV", EUR0, False),
    ("tva_deductible", "TVA déductible du mois", EUR0, False),
    ("tva_payee", "TVA nette reversée (mois suivant)", EUR0, False),
    ("is_paye", "IS payé (solde 2027 dû en mai 2028, hors horizon)", EUR0, False),
    ("dec_total", "Total des décaissements", EUR0, True),
    ("flux", "Flux de trésorerie du mois", EUR0, True),
    ("treso", "Trésorerie en fin de mois (départ : h_TRESO_INITIALE)", EUR0, True),
]


def feuille_tresorerie(wb, refs, spos):
    ws = wb.create_sheet(S_TRESO)
    ws["A1"] = "Trésorerie mensuelle — départ à 0 €, fournisseurs payés à la commande"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Stripe : 7 jours au premier versement puis 3 jours ouvrés ; TikTok Shop : 31 jours après livraison "
                "pour un vendeur débutant, puis 8 jours ; TVA reversée le mois suivant ; stock détenu = couverture × "
                "coût des produits du mois suivant.")
    ws["A2"].font = F_NOTE
    S, H = q(S_SCEN), q(S_HYP)
    pos = {}
    row = 4
    for cle, sc in SCENARIOS.items():
        ws.cell(row=row, column=1, value=f"Scénario {sc['libelle'].lower()}").font = F_GRAS
        for c_ in range(1, 22):
            ws.cell(row=row, column=c_).fill = FILL_SECTION
        row += 1
        lr = {k: row + i for i, (k, *_r) in enumerate(TRESO_LIGNES)}
        sl = spos[cle]
        for k, lib, nf, gras in TRESO_LIGNES:
            r = lr[k]
            ws.cell(row=r, column=1, value=lib).font = F_GRAS if gras else Font()
            if k == "mois":
                entete(ws, r, ["Ligne", ""] + MOIS + ["Total"])
                continue
            for m in range(N):
                C = col(m)
                P_ = col(m - 1) if m > 0 else None
                P2 = col(m - 2) if m > 1 else None
                Cn = col(min(m + 1, N - 1))

                def s(key, cc=C):
                    return f"{S}!{cc}{sl[key]}"

                def h(key, cc=C):
                    return f"{H}!{cc}{refs[(cle, key)]}"
                L = {kk: f"{C}{lr[kk]}" for kk in lr}
                f = None
                if k == "site_du":
                    f = f"={s('cmd_site')}*(ue_SITE_TTC-ue_SITE_PAY)+{s('cmd_pub')}*(ue_PUB_TTC-ue_PUB_PAY)"
                elif k == "enc_site":
                    f = f"={L['site_du']}*(1-{h('delai_site')}/30)"
                    if P_:
                        f += f"+{P_}{lr['site_du']}*{h('delai_site', P_)}/30"
                elif k == "tts_du":
                    f = (f"=({s('cmd_propre')}+{s('cmd_aff')})*ue_TTS_TTC*(1-{h('taux_tts')})"
                         f"-{s('cmd_aff')}*ue_TTS_TTC*h_CREA_COMM")
                elif k == "delai_tts":
                    f = "=" + h("delai_tts")
                elif k == "w0":
                    f = f"=MAX(0,1-{L['delai_tts']}/30)"
                elif k == "w1":
                    f = f"=IF({L['delai_tts']}<=30,{L['delai_tts']}/30,(60-{L['delai_tts']})/30)"
                elif k == "w2":
                    f = f"=MAX(0,({L['delai_tts']}-30)/30)"
                elif k == "enc_tts":
                    f = f"={L['tts_du']}*{L['w0']}"
                    if P_:
                        f += f"+{P_}{lr['tts_du']}*{P_}{lr['w1']}"
                    if P2:
                        f += f"+{P2}{lr['tts_du']}*{P2}{lr['w2']}"
                elif k == "enc_total":
                    f = f"={L['enc_site']}+{L['enc_tts']}"
                elif k == "stock_fin":
                    f = f"={h('couverture')}*{s('c_produits', Cn)}"
                elif k == "achats_stock":
                    f = f"={s('c_produits')}+{L['stock_fin']}" + (f"-{P_}{lr['stock_fin']}" if P_ else "")
                elif k == "achat_import":
                    f = "=" + h("import", Cn)
                elif k == "tva_achats":
                    f = f"=h_TVA*{L['achats_stock']}*(1-{L['achat_import']})"
                elif k == "logistique_ttc":
                    f = f"={s('c_logistique')}*(1+h_TVA)"
                elif k in ("pub", "ech", "frais_fixes"):
                    f = "=" + s(k)
                elif k == "remboursements":
                    f = "=" + s("c_prov")
                elif k == "tva_deductible":
                    f = f"={L['tva_achats']}+h_TVA*{s('c_logistique')}"
                elif k == "tva_payee":
                    f = "=0" if m == 0 else f"={s('tva_collectee', P_)}-{P_}{lr['tva_deductible']}"
                elif k == "is_paye":
                    f = "=0"
                elif k == "dec_total":
                    f = "=" + "+".join(L[x] for x in ("achats_stock", "tva_achats", "logistique_ttc", "pub", "ech",
                                                      "frais_fixes", "remboursements", "tva_payee", "is_paye"))
                elif k == "flux":
                    f = f"={L['enc_total']}-{L['dec_total']}"
                elif k == "treso":
                    f = f"=h_TRESO_INITIALE+{L['flux']}" if m == 0 else f"={P_}{lr['treso']}+{L['flux']}"
                c = ws.cell(row=r, column=3 + m, value=f)
                c.number_format = nf
                if gras:
                    c.font = F_GRAS
                if k == "treso":
                    c.fill = FILL_CLE
            if k in ("enc_site", "enc_tts", "enc_total", "achats_stock", "tva_achats", "logistique_ttc", "pub", "ech",
                     "frais_fixes", "remboursements", "tva_payee", "dec_total", "flux"):
                t = ws.cell(row=r, column=3 + N, value=f"=SUM({col(0)}{r}:{col(N - 1)}{r})")
                t.number_format = nf
                t.font = F_GRAS
        r = lr["treso"] + 1
        ws.cell(row=r, column=1, value="Besoin de trésorerie (creux le plus bas, signe inversé)").font = F_GRAS
        c = ws.cell(row=r, column=3, value=f"=-MIN(0,MIN({col(0)}{lr['treso']}:{col(N - 1)}{lr['treso']}))")
        c.number_format = EUR0
        c.font = F_GRAS
        c.fill = FILL_CLE
        lr["besoin"] = r
        pos[cle] = lr
        row = r + 3
    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 2
    for c_ in range(3, 22):
        ws.column_dimensions[get_column_letter(c_)].width = 11
    ws.freeze_panes = "C4"
    return pos


def feuille_paliers(wb, paliers):
    ws = wb.create_sheet(S_PAL)
    ws["A1"] = "Paliers de bénéfice net mensuel : ce qu'il faut réunir"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Paliers 1 et 2 : calcul ascendant à partir des unit economics. Paliers 3 et 4 : calcul descendant à "
                "partir d'une marge nette type. Bénéfice net = avant IS et rémunération du dirigeant.")
    ws["A2"].font = F_NOTE
    row = 4
    entete(ws, row, ["Indicateur", "Palier 1 — 1 k€", "Palier 2 — 10 k€", "Palier 3 — 100 k€", "Palier 4 — 1 M€"])
    lignes = {}
    noms = ["benefice", "marge_cmd", "frais_fixes", "cpa", "commandes", "commandes_jour", "ca_ht", "ca_ttc", "pub",
            "stock", "creances", "dettes", "bfr"]
    libs = {"benefice": "Bénéfice net visé (€ / mois)", "marge_cmd": "Marge par commande après publicité (paliers 1-2) ; bénéfice net par commande (paliers 3-4) (€)",
            "frais_fixes": "Frais fixes, personnel et échantillons (€ / mois)", "cpa": "CPA cible (€)",
            "commandes": "Commandes par mois", "commandes_jour": "Commandes par jour", "ca_ht": "CA HT nécessaire (€ / mois)",
            "ca_ttc": "CA TTC (€ / mois)", "pub": "Budget publicitaire (€ / mois)", "stock": "Stock immobilisé (€)",
            "creances": "Créances clients et plateformes (€)", "dettes": "Dettes TVA et fournisseurs (€)",
            "bfr": "Besoin en fonds de roulement (€)"}
    for i, k in enumerate(noms):
        lignes[k] = row + 1 + i
        ws.cell(row=lignes[k], column=1, value=libs[k]).font = F_GRAS if k in ("ca_ht", "commandes_jour", "bfr") else Font()
    B, Cc, D, E = "B", "C", "D", "E"
    L = lignes
    f1 = "(h_COMPTABLE+h_BANQUE+h_OUTILS+h_RC+h_DOMICILIATION+h_LEKO/12+h_MEDIATEUR/36+h_DOMAINE/12)"
    tts_net = "(ue_TTS_TTC*(1-h_TTS_COMM)-h_MIX_AFF/(1-h_MIX_SITE)*ue_TTS_TTC*h_CREA_COMM)"
    d_tts = "(h_TTS_LIVRAISON+h_TTS_STANDARD+h_TTS_VIREMENT)/30"
    # Palier 1
    p1 = {
        "benefice": "=1000", "marge_cmd": "=ue_MIX_MARGE_MS", "frais_fixes": f"={f1}+h_P1_ECH", "cpa": None,
        "commandes": f"=({B}{L['benefice']}+{B}{L['frais_fixes']})/{B}{L['marge_cmd']}",
        "commandes_jour": f"={B}{L['commandes']}/30", "ca_ht": f"={B}{L['commandes']}*ue_MIX_HT",
        "ca_ttc": f"={B}{L['commandes']}*ue_MIX_TTC", "pub": "=0",
        "stock": f"=h_COUV_MICRO*{B}{L['commandes']}*ue_MIX_PROD_MS",
        "creances": (f"={B}{L['commandes']}*(1-h_MIX_SITE)*{tts_net}*{d_tts}"
                     f"+{B}{L['commandes']}*h_MIX_SITE*(ue_SITE_TTC-ue_SITE_PAY)*h_STRIPE_DELAI/30"),
        "dettes": f"={B}{L['commandes']}*(ue_MIX_TTC-ue_MIX_HT)-h_TVA*{B}{L['commandes']}*(ue_MIX_PROD_MS+ue_MIX_LOG_MS)",
        "bfr": f"={B}{L['stock']}+{B}{L['creances']}-{B}{L['dettes']}",
    }
    s_ = "h_P2_PART_PUB"
    p2 = {
        "benefice": "=10000", "cpa": "=ue_PUB_MARGE_AVANT_PUB_IMP/h_MER_MARGE",
        "marge_cmd": f"=(1-{s_})*ue_MIX_MARGE_IMP+{s_}*(ue_PUB_MARGE_AVANT_PUB_IMP-{Cc}{L['cpa']})",
        "frais_fixes": "=h_P2_FIXES_AUTRES+h_P2_PERSONNEL+h_P2_ECH",
        "commandes": f"=({Cc}{L['benefice']}+{Cc}{L['frais_fixes']})/{Cc}{L['marge_cmd']}",
        "commandes_jour": f"={Cc}{L['commandes']}/30",
        "ca_ht": f"={Cc}{L['commandes']}*((1-{s_})*ue_MIX_HT+{s_}*ue_PUB_HT)",
        "ca_ttc": f"={Cc}{L['commandes']}*((1-{s_})*ue_MIX_TTC+{s_}*ue_PUB_TTC)",
        "pub": f"={Cc}{L['commandes']}*{s_}*{Cc}{L['cpa']}",
        "stock": f"=h_COUV_IMPORT*{Cc}{L['commandes']}*((1-{s_})*ue_MIX_PROD_IMP+{s_}*ue_PUB_PROD_IMP)",
        "creances": (f"={Cc}{L['commandes']}*(1-{s_})*(1-h_MIX_SITE)*{tts_net}*{d_tts}"
                     f"+{Cc}{L['commandes']}*((1-{s_})*h_MIX_SITE*(ue_SITE_TTC-ue_SITE_PAY)+{s_}*(ue_PUB_TTC-ue_PUB_PAY))*h_STRIPE_DELAI/30"),
        "dettes": f"=({Cc}{L['ca_ttc']}-{Cc}{L['ca_ht']})-h_TVA*{Cc}{L['commandes']}*((1-{s_})*ue_MIX_LOG_IMP+{s_}*ue_PUB_LOG_IMP)",
        "bfr": f"={Cc}{L['stock']}+{Cc}{L['creances']}-{Cc}{L['dettes']}",
    }

    def haut(colL, pre, ben):
        return {
            "benefice": f"={ben}", "marge_cmd": f"={colL}{L['benefice']}/{colL}{L['commandes']}", "frais_fixes": None, "cpa": None,
            "ca_ht": f"={colL}{L['benefice']}/h_{pre}_MARGE", "ca_ttc": f"={colL}{L['ca_ht']}*(1+h_TVA)",
            "commandes": f"={colL}{L['ca_ttc']}/h_{pre}_PANIER", "commandes_jour": f"={colL}{L['commandes']}/30",
            "pub": f"=h_{pre}_PUB*{colL}{L['ca_ht']}", "stock": f"=h_COUV_IMPORT*h_{pre}_COGS*{colL}{L['ca_ht']}",
            "creances": f"=h_PART_MARKETPLACE*{colL}{L['ca_ttc']}*h_CREANCES_JOURS/30",
            "dettes": f"=h_DETTES_FOURN_PART*h_{pre}_COGS*{colL}{L['ca_ht']}+h_TVA*{colL}{L['ca_ht']}*h_TVA_NETTE_RATIO",
            "bfr": f"={colL}{L['stock']}+{colL}{L['creances']}-{colL}{L['dettes']}",
        }
    for colL, dico in ((B, p1), (Cc, p2), (D, haut(D, "P3", 100000)), (E, haut(E, "P4", 1000000))):
        for k, f in dico.items():
            if f is None:
                continue
            c = ws[f"{colL}{L[k]}"]
            c.value = f
            c.number_format = {"commandes": NB0, "commandes_jour": NB, "marge_cmd": EUR, "cpa": EUR}.get(k, EUR0)
    row = L["bfr"] + 1
    for k, lib in (("effectif", "Effectif"), ("probabilite_strategie", "Probabilité (stratégie 04)"),
                   ("probabilite_finance", "Probabilité (lecture finance)"), ("delai", "Délai estimé"),
                   ("conditions", "Conditions de passage")):
        ws.cell(row=row, column=1, value=lib).font = F_GRAS
        for i, p in enumerate(paliers):
            c = ws.cell(row=row, column=2 + i, value=p[k])
            c.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1
    ws.column_dimensions["A"].width = 46
    for c_ in "BCDE":
        ws.column_dimensions[c_].width = 34
    return L


def feuille_sensibilite(wb, bases, spos):
    ws = wb.create_sheet(S_SENS)
    ws["A1"] = "Sensibilité du bénéfice mensuel à ±20 % de chaque variable (tornado)"
    ws["A1"].font = F_TITRE
    ws["A2"] = ("Modèle réduit : bénéfice = Σ commandes × marge par canal − budget publicitaire − frais fixes − échantillons. "
                "Chaque ligne multiplie une seule variable par 0,8 ou 1,2. Prix ±20 % : les commandes restent constantes "
                "(effet sur la demande non modélisé). CPA ±20 % : budget constant, donc moins de commandes payantes.")
    ws["A2"].font = F_NOTE
    row = 4
    S = q(S_SCEN)
    pos = {}
    for cle, b, variables, src in bases:
        ws.cell(row=row, column=1, value=b["libelle"]).font = F_GRAS
        for c_ in range(1, 18):
            ws.cell(row=row, column=c_).fill = FILL_SECTION
        row += 1
        entete(ws, row, ["Canal", "Commandes", "CA HT", "Produit", "Livraison", "Paiement %", "Paiement fixe",
                         "Comm. TikTok", "Comm. créateur", "Provision"])
        row += 1
        crow = {}
        ph = "MS" if cle == "p1" else "IMP"
        for c in CANAUX_SENS:
            crow[c] = row
            ws.cell(row=row, column=1, value={"site": "Site organique", "propre": "TikTok Shop contenu propre",
                                              "aff": "TikTok Shop affiliés", "pub": "Site, publicité"}[c])
            if cle == "p1":
                m = 11
                nref = {"site": f"={S}!{col(m)}{spos['realiste']['cmd_site']}",
                        "propre": f"={S}!{col(m)}{spos['realiste']['cmd_propre']}",
                        "aff": f"={S}!{col(m)}{spos['realiste']['cmd_aff']}", "pub": "=0"}[c]
                taux = f"{q(S_HYP)}!{col(m)}{src[('realiste', 'taux_tts')]}"
            else:
                pc = f"{q(S_PAL)}!C{src['commandes']}"
                nref = {"site": f"={pc}*(1-h_P2_PART_PUB)*h_MIX_SITE", "propre": f"={pc}*(1-h_P2_PART_PUB)*h_MIX_PROPRE",
                        "aff": f"={pc}*(1-h_P2_PART_PUB)*h_MIX_AFF", "pub": f"={pc}*h_P2_PART_PUB"}[c]
                taux = "h_TTS_COMM"
            base = {"site": "SITE", "pub": "PUB"}.get(c, "TTS")
            ttc = f"ue_{base}_TTC"
            web = c in ("site", "pub")
            vals = [nref, f"=ue_{base}_HT", f"=ue_{base}_PROD_{ph}", f"=ue_{base}_LOG_{ph}",
                    f"=h_STRIPE_PCT*{ttc}" if web else "=0", "=h_STRIPE_FIXE" if web else "=0",
                    f"={taux}*{ttc}" if c in ("propre", "aff") else "=0",
                    f"=h_CREA_COMM*{ttc}" if c == "aff" else "=0", f"=h_PROV_RETOURS*C{row}"]
            for i, v in enumerate(vals):
                ws.cell(row=row, column=2 + i, value=v).number_format = NB if i == 0 else EUR
            row += 1
        ws.cell(row=row, column=1, value="Frais fixes (€ / mois)")
        if cle == "p1":
            ws.cell(row=row, column=2, value=f"={S}!{col(11)}{spos['realiste']['frais_fixes']}")
        else:
            ws.cell(row=row, column=2, value="=h_P2_FIXES_AUTRES+h_P2_PERSONNEL")
        rF = row
        row += 1
        ws.cell(row=row, column=1, value="Échantillons créateurs (€ / mois)")
        ws.cell(row=row, column=2, value=(f"={S}!{col(11)}{spos['realiste']['ech']}" if cle == "p1" else "=h_P2_ECH"))
        rE = row
        row += 1
        ws.cell(row=row, column=1, value="CPA (€)")
        ws.cell(row=row, column=2, value=("=0" if cle == "p1" else f"={q(S_PAL)}!C{src['cpa']}"))
        rC = row
        row += 1
        ws.cell(row=row, column=1, value="Budget publicitaire (€ / mois)")
        ws.cell(row=row, column=2, value=f"=B{rC}*B{crow['pub']}")
        rB = row
        for r_ in (rF, rE, rC, rB):
            ws.cell(row=r_, column=2).number_format = EUR0
        row += 2
        kcols = [v for v, _ in VARS_SENS]
        entete(ws, row, ["Variable", "Variation"] + kcols + ["Bénéfice mensuel", "Écart vs base"])
        row += 1
        first_var_row = row

        def formule_benef(r):
            k = {v: f"{get_column_letter(3 + i)}{r}" for i, v in enumerate(kcols)}

            def marge(c):
                x = crow[c]
                return (f"({k['kPrix']}*C{x}-{k['kProd']}*D{x}-{k['kLog']}*E{x}-{k['kPay']}*(F{x}*{k['kPrix']}+G{x})"
                        f"-{k['kTTS']}*H{x}*{k['kPrix']}-{k['kCrea']}*I{x}*{k['kPrix']}-{k['kRet']}*J{x}*{k['kPrix']})")
            n_site = f"B{crow['site']}*{k['kVol']}"
            n_aff = f"B{crow['aff']}*{k['kVol']}*{k['kAff']}"
            n_propre = f"(B{crow['propre']}+B{crow['aff']}*(1-{k['kAff']}))*{k['kVol']}"
            budget = f"$B${rB}*{k['kPubVol']}"
            n_pub = f"IF($B${rC}>0,{budget}/($B${rC}*{k['kCPA']}),0)"
            return (f"={n_site}*{marge('site')}+{n_propre}*{marge('propre')}+{n_aff}*{marge('aff')}"
                    f"+{n_pub}*{marge('pub')}-{budget}-{k['kFix']}*$B${rF}-{k['kEch']}*$B${rE}")
        # Ligne de base
        ws.cell(row=row, column=1, value="Base").font = F_GRAS
        ws.cell(row=row, column=2, value="—")
        for i in range(len(kcols)):
            ws.cell(row=row, column=3 + i, value=1)
        base_row = row
        ws.cell(row=row, column=3 + len(kcols), value=formule_benef(row)).number_format = EUR0
        ws.cell(row=row, column=3 + len(kcols)).font = F_GRAS
        row += 1
        var_rows = {}
        for v, lib in variables:
            for sens, mult in (("−20 %", 0.8), ("+20 %", 1.2)):
                ws.cell(row=row, column=1, value=lib)
                ws.cell(row=row, column=2, value=sens)
                for i, kv in enumerate(kcols):
                    c = ws.cell(row=row, column=3 + i, value=mult if kv == v else 1)
                    if kv == v:
                        c.font = F_SAISIE
                bc = get_column_letter(3 + len(kcols))
                ws.cell(row=row, column=3 + len(kcols), value=formule_benef(row)).number_format = EUR0
                ws.cell(row=row, column=4 + len(kcols), value=f"={bc}{row}-{bc}${base_row}").number_format = EUR0
                var_rows[(v, mult)] = row
                row += 1
        pos[cle] = dict(base=base_row, rows=var_rows, colB=get_column_letter(3 + len(kcols)))
        row += 2
    ws.column_dimensions["A"].width = 40
    for c_ in range(2, 18):
        ws.column_dimensions[get_column_letter(c_)].width = 11
    return pos


# =============================================================================
# 8. VÉRIFICATION PAR RECALCUL LIBREOFFICE
# =============================================================================


def verifier_avec_libreoffice(controles):
    """Recalcule le classeur avec LibreOffice (si présent) et compare aux valeurs Python."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice absent : vérification des formules ignorée.")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.xlsx"
        shutil.copy(SORTIE_XLSX, src)
        out = Path(tmp) / "out"
        out.mkdir()
        subprocess.run([soffice, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(out), str(src)],
                       check=True, capture_output=True, timeout=180,
                       env={"HOME": tmp, "PATH": "/usr/bin:/bin"})
        wb = load_workbook(out / "in.xlsx", data_only=True)
        ecarts, n = [], 0
        for feuille, cell, attendu, quoi in controles:
            v = wb[feuille][cell].value
            n += 1
            if v is None or isinstance(v, str) or abs(float(v) - attendu) > 0.005 + 1e-6 * abs(attendu):
                ecarts.append(f"{quoi} ({feuille}!{cell}) : Excel {v} / Python {attendu:.4f}")
        erreurs = [f"{ws.title}!{c.coordinate}" for ws in wb.worksheets for r in ws.iter_rows() for c in r
                   if isinstance(c.value, str) and c.value.startswith(("#", "Err:"))]
        return n, ecarts, erreurs


# =============================================================================
# 9. PROGRAMME PRINCIPAL
# =============================================================================


def r2(x):
    return None if x is None else round(float(x), 2)


def main():
    brand = verifier_brand_json()
    ue = calc_unit_economics()
    mo = moyennes(ue)

    # Contrôles de cohérence avec 04-strategie.md §4.1 et brand.json (marges à 1 centime près, coûts produit +20 %)
    attendus = {("MS", "site-rou"): 11.52, ("MS", "site-kap"): 13.59, ("MS", "site-gk"): 15.75, ("MS", "site-duo"): 13.24,
                ("MS", "site-hiv"): 16.42, ("MS", "site-tap"): 10.82, ("MS", "tts-propre-rou"): 6.87,
                ("MS", "tts-propre4-rou"): 8.12, ("MS", "tts-aff-rou"): 3.14, ("MS", "tts-aff-kap"): 4.08,
                ("FR", "site-rou"): 13.96, ("FR", "site-gk"): 19.07, ("FR", "tts-aff-rou"): 3.76,
                ("MICRO", "site-rou"): 10.42, ("MICRO", "site-gk"): 14.16, ("MICRO", "tts-aff-rou"): 0.70}
    for (b, cid), v in attendus.items():
        assert abs(ue[b][cid]["marge"] - v) < 0.006, f"{b} {cid} : {ue[b][cid]['marge']:.4f} ≠ {v}"
    assert abs(mo["MIX_MARGE_MS"] - brand["hypotheses_cles"]["marge_moyenne_par_commande_ht"]) < 0.006, mo["MIX_MARGE_MS"]
    assert abs(mo["MIX_MARGE_FR"] - 7.59) < 0.006, mo["MIX_MARGE_FR"]
    assert abs(mo["MIX_MARGE_MICRO"] - 4.14) < 0.006, mo["MIX_MARGE_MICRO"]
    assert abs(mo["SITE_TTC"] - brand["hypotheses_cles"]["panier_moyen_ttc"]) < 0.006

    res, saisies = {}, {}
    for cle, sc in SCENARIOS.items():
        r, e = calc_scenario(cle, sc, mo)
        res[cle] = r
        saisies[cle] = (sc, e, r)
    paliers = calc_paliers(mo)
    b1 = base_sens_palier1(mo, res["realiste"])
    b2 = base_sens_palier2(mo, paliers[1])
    vars1 = [x for x in VARS_SENS if x[0] not in ("kCPA", "kPubVol")]
    base1, sens1 = calc_sensibilite(b1, vars1)
    base2, sens2 = calc_sensibilite(b2, VARS_SENS)
    assert abs(base1 - res["realiste"]["benefice"][11]) < 0.01, (base1, res["realiste"]["benefice"][11])
    assert abs(base2 - 10000) < 0.01, base2

    # ----------------------------- Classeur -----------------------------
    wb = Workbook()
    refs = feuille_hypotheses(wb, saisies)
    pos_ue = feuille_unit_economics(wb, ue, mo)
    spos = feuille_scenarios(wb, refs)
    tpos = feuille_tresorerie(wb, refs, spos)
    ppos = feuille_paliers(wb, paliers)
    src = dict(refs)
    src.update({"commandes": ppos["commandes"], "cpa": ppos["cpa"]})
    sens_pos = feuille_sensibilite(wb, [("p1", b1, vars1, src), ("p2", b2, VARS_SENS, src)], spos)
    wb.calculation.fullCalcOnLoad = True
    wb.save(SORTIE_XLSX)

    # ----------------------------- Contrôles Excel ↔ Python -----------------------------
    ctrl = []
    for (b, cid), rr in pos_ue.items():
        d = ue[b][cid]
        ctrl += [(S_UE, f"O{rr}", d["marge"], f"marge {b} {cid}"), (S_UE, f"D{rr}", d["prix_ttc"], f"prix {cid}")]
    for cle, lr in spos.items():
        for k in ("cmd_total", "ca_ht", "marge_contrib", "frais_fixes", "benefice", "is_mois", "resultat_apres_is"):
            for m in range(N):
                ctrl.append((S_SCEN, f"{col(m)}{lr[k]}", res[cle][k][m], f"{cle} {k} {MOIS[m]}"))
    for cle, lr in tpos.items():
        for k in ("enc_site", "enc_tts", "achats_stock", "tva_payee", "treso"):
            for m in range(N):
                ctrl.append((S_TRESO, f"{col(m)}{lr[k]}", res[cle]["treso"][k][m], f"{cle} tréso {k} {MOIS[m]}"))
        ctrl.append((S_TRESO, f"C{lr['besoin']}", res[cle]["treso"]["besoin"], f"{cle} besoin"))
    for i, p in enumerate(paliers):
        cl = "BCDE"[i]
        for k in ("commandes", "ca_ht", "pub", "stock", "bfr"):
            ctrl.append((S_PAL, f"{cl}{ppos[k]}", p[k], f"palier {p['cle']} {k}"))
    for cle, sens, base in (("p1", sens1, base1), ("p2", sens2, base2)):
        sp = sens_pos[cle]
        ctrl.append((S_SENS, f"{sp['colB']}{sp['base']}", base, f"sensibilité {cle} base"))
        for d in sens:
            ctrl.append((S_SENS, f"{sp['colB']}{sp['rows'][(d['code'], 0.8)]}", d["moins_20"], f"sens {cle} {d['code']} -20"))
            ctrl.append((S_SENS, f"{sp['colB']}{sp['rows'][(d['code'], 1.2)]}", d["plus_20"], f"sens {cle} {d['code']} +20"))
    verif = verifier_avec_libreoffice(ctrl)

    # ----------------------------- data.json -----------------------------
    data = construire_json(ue, mo, res, paliers, (b1, base1, sens1), (b2, base2, sens2), verif)
    SORTIE_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Écrit : {SORTIE_XLSX.name}, {SORTIE_JSON.name}")
    if verif:
        n, ecarts, erreurs = verif
        print(f"Recalcul LibreOffice : {n} valeurs comparées, {len(ecarts)} écart(s), {len(erreurs)} erreur(s) de formule.")
        for x in ecarts[:20] + erreurs[:20]:
            print("  ", x)
        if ecarts or erreurs:
            sys.exit(1)
    for cle in SCENARIOS:
        r = res[cle]
        print(f"{cle:11s} commandes 18 m = {sum(r['cmd_total']):7.0f} ; CA HT = {sum(r['ca_ht']):9.0f} ; "
              f"bénéfice cumulé = {r['benefice_cumul'][-1]:8.0f} ; bénéfice mars 2028 = {r['benefice'][-1]:7.0f} ; "
              f"besoin de trésorerie = {r['treso']['besoin']:7.0f} ({r['treso']['mois_creux']})")


CASCADE_ETAPES = [("prix_ttc", "Prix payé TTC"), ("tva", "TVA collectée"), ("cout_produit", "Coût produit"),
                  ("livraison", "Livraison et emballage"), ("droits", "Droits de douane et redevance"),
                  ("paiement", "Frais de paiement"), ("commission_tts", "Commission TikTok Shop"),
                  ("createur_ou_pub", "Commission créateur ou publicité (CPA)"),
                  ("provision", "Provision retours, SAV et litiges"), ("cotis_micro", "Cotisations sociales micro"),
                  ("marge", "Marge nette de contribution")]


def cascade(d, cid, lib, canal, regime):
    etapes = []
    for k, l in CASCADE_ETAPES:
        if k == "cotis_micro" and regime != "micro-entreprise":
            continue
        v = d[k]
        etapes.append({"poste": l, "cle": k, "montant": r2(v if k in ("prix_ttc", "marge") else -v),
                       "type": "total" if k in ("prix_ttc", "marge") else "deduction"})
    return {"id": cid, "libelle": lib, "canal": canal, "regime": regime, "etapes": etapes,
            "ca_ht": r2(d["ca_ht"]), "marge": r2(d["marge"]), "marge_pct_ca_ht": round(d["marge_pct"], 4)}


def construire_json(ue, mo, res, paliers, s1, s2, verif):
    lib = {c[0]: c[1] for c in CAS_MS + [CAS_RISQUE_GK] + CAS_IMP}
    canal = {c[0]: c[2] for c in CAS_MS + [CAS_RISQUE_GK] + CAS_IMP}
    reg_lib = {"MS": "société assujettie, micro-stock", "IMP": "société assujettie, import + 3PL",
               "FR": "franchise en base de TVA", "MICRO": "micro-entreprise"}
    cascades = [cascade(ue["MS"][c], c, lib[c], canal[c], "société assujettie") for c in
                ("site-gk", "site-rou", "site-kap", "tts-propre-rou", "tts-aff-rou", "tts-aff-kap")]
    cascades.append(cascade(ue["IMP"]["imp-site-gk"], "imp-site-gk", "Site — Grand kit, import + 3PL", "site", "société assujettie"))
    cascades.append(cascade(ue["IMP"]["imp-pub-gk-real"], "imp-pub-gk-real", lib["imp-pub-gk-real"], "pub", "société assujettie"))
    cascades.append(cascade(ue["IMP"]["imp-pub-gk-opt"], "imp-pub-gk-opt", lib["imp-pub-gk-opt"], "pub", "société assujettie"))
    cascades.append(cascade(ue["MICRO"]["tts-aff-rou"], "micro-tts-aff-rou", "Micro-entreprise — TikTok Shop affilié, Rouleau", "tts", "micro-entreprise"))
    # Cascade moyenne du mix de lancement
    S = {"rou": V["SITE_ROU"], "kap": V["SITE_KAP"], "gk": V["SITE_GK"], "duo": V["SITE_DUO"]}
    T = {"rou": V["TTS_ROU"], "kap": V["TTS_KAP"]}
    mix = {k: 0.0 for k, _ in CASCADE_ETAPES}
    for pre, poids, w in (("site-", S, V["MIX_SITE"]), ("tts-propre-", T, V["MIX_PROPRE"]), ("tts-aff-", T, V["MIX_AFF"])):
        for kk, ww in poids.items():
            for k, _ in CASCADE_ETAPES:
                mix[k] += w * ww * ue["MS"][pre + kk][k]
    mix_d = dict(mix)
    mix_d["ca_ht"] = mix["prix_ttc"] - mix["tva"]
    mix_d["marge_pct"] = mix_d["marge"] / mix_d["ca_ht"]
    cascades.insert(0, cascade(mix_d, "mix-lancement", "Commande moyenne du mix de lancement (20 % site, 22 % TikTok propre, 58 % affiliés)", "mix", "société assujettie"))

    par_offre = []
    for b in ("MS", "IMP", "FR", "MICRO"):
        for cid, d in ue[b].items():
            par_offre.append({"bloc": reg_lib[b], "id": cid, "libelle": lib.get(cid, cid), "prix_ttc": r2(d["prix_ttc"]),
                              "ca_ht": r2(d["ca_ht"]), "marge": r2(d["marge"]), "marge_pct": round(d["marge_pct"], 4),
                              "roas_rentabilite_ht": r2(d["roas_ht"]), "roas_rentabilite_ttc": r2(d["roas_ttc"]),
                              "cpa_max": r2(d["cpa_max"])})
    seuils = []
    for b, cid, l in (("MS", "site-rou", "Site — Rouleau seul, micro-stock"), ("MS", "site-kap", "Site — Kit anti-poils, micro-stock"),
                      ("MS", "site-gk", "Site — Grand kit, micro-stock"), ("MS", "site-hiv", "Site — Kit chat d'hiver, micro-stock"),
                      ("IMP", "imp-site-rou", "Site — Rouleau seul, import + 3PL"), ("IMP", "imp-site-gk", "Site — Grand kit, import + 3PL")):
        d = ue[b][cid]
        seuils.append({"offre": l, "marge_contribution": r2(d["marge"]), "marge_contribution_pct": round(d["marge_pct"], 4),
                       "roas_rentabilite_ht": r2(d["roas_ht"]), "roas_rentabilite_ttc": r2(d["roas_ttc"]),
                       "cpa_maximal": r2(d["cpa_max"]), "cpa_cible_mer_1_2": r2(d["cpa_max"] / V["MER_MARGE"]),
                       "roas_cible_ttc": r2(d["prix_ttc"] / (d["cpa_max"] / V["MER_MARGE"]))})
    f1 = paliers[0]["frais_fixes"]
    seuils_d = {
        "par_offre": seuils,
        "roas_median_marche": {"meta": 1.93, "tiktok": 2.21, "source": "Triple Whale 2025 (02 §2.6), majoritairement US"},
        "marge_contribution_mix_lancement": r2(mo["MIX_MARGE_MS"]),
        "marge_contribution_mix_import": r2(mo["MIX_MARGE_IMP"]),
        "point_mort_commandes_mois": r2(f1 / mo["MIX_MARGE_MS"]),
        "point_mort_note": "Frais fixes du palier 1 (structure, outils, RC, domiciliation, Léko, médiateur, domaine) + 100 € d'échantillons, divisés par la marge moyenne du mix de lancement",
        "cpa_cible_palier_2": r2(paliers[1]["cpa"]),
        "synthese": {
            "offre_reference": "Grand kit sur le site",
            "marge_contribution_micro_stock": r2(ue["MS"]["site-gk"]["marge"]),
            "roas_rentabilite_ttc_micro_stock": r2(ue["MS"]["site-gk"]["roas_ttc"]),
            "cpa_maximal_micro_stock": r2(ue["MS"]["site-gk"]["cpa_max"]),
            "marge_contribution_import": r2(ue["IMP"]["imp-site-gk"]["marge"]),
            "roas_rentabilite_ttc_import": r2(ue["IMP"]["imp-site-gk"]["roas_ttc"]),
            "roas_rentabilite_ht_import": r2(ue["IMP"]["imp-site-gk"]["roas_ht"]),
            "cpa_maximal_import": r2(ue["IMP"]["imp-site-gk"]["cpa_max"]),
            "cpa_cible_import": r2(ue["IMP"]["imp-site-gk"]["cpa_max"] / V["MER_MARGE"]),
            "lecture": "Publicité non rentable avant l'import groupé : ROAS de rentabilité TTC de " + f"{ue['MS']['site-gk']['roas_ttc']:.2f}".replace(".", ",") + " contre une médiane Meta de 1,93",
        },
    }

    def serie(r, k):
        return [r2(x) for x in r[k]]
    scen = {"mois": MOIS}
    for cle, sc in SCENARIOS.items():
        r = res[cle]
        t = r["treso"]
        arret = r["arret"]
        scen[cle] = {
            "libelle": sc["libelle"], "description": sc["description"], "probabilite": sc["proba"],
            "commandes": serie(r, "cmd_total"), "commandes_par_jour": serie(r, "cmd_jour"), "commandes_par_canal": {
                "site": serie(r, "cmd_site"), "tiktok_contenu_propre": serie(r, "cmd_propre"),
                "tiktok_affilies": serie(r, "cmd_aff"), "publicite": serie(r, "cmd_pub")},
            "ca_ttc": serie(r, "ca_ttc"), "ca_ht": serie(r, "ca_ht"), "couts": serie(r, "couts_totaux"),
            "couts_detail": {"produits_droits": serie(r, "c_produits"), "logistique": serie(r, "c_logistique"),
                             "paiement": serie(r, "c_paiement"), "commission_tiktok": serie(r, "c_tts"),
                             "commission_createurs": serie(r, "c_crea"), "provision_retours": serie(r, "c_prov"),
                             "publicite": serie(r, "pub"), "echantillons": serie(r, "ech"), "frais_fixes": serie(r, "frais_fixes")},
            "marge_contribution": serie(r, "marge_contrib"), "benefice_net": serie(r, "benefice"),
            "benefice_net_cumule": serie(r, "benefice_cumul"), "is_provisionne": serie(r, "is_mois"),
            "resultat_apres_is": serie(r, "resultat_apres_is"),
            "tresorerie": [r2(x) for x in t["treso"]], "flux_tresorerie": [r2(x) for x in t["flux"]],
            "stock_fin_de_mois": [r2(x) for x in t["stock_fin"]],
            "totaux_18_mois": {"commandes": r2(sum(r["cmd_total"])), "ca_ht": r2(sum(r["ca_ht"])),
                               "benefice_net": r2(sum(r["benefice"])), "is_provisionne": r2(sum(r["is_mois"])),
                               "resultat_apres_is": r2(sum(r["resultat_apres_is"])), "publicite": r2(sum(r["pub"]))},
            "evenements": r["evenements"],
            "regle_arret": ({"mois": MOIS[arret], "benefice_cumule_a_l_arret": r2(r["benefice_cumul"][arret]),
                             "tresorerie_a_l_arret": r2(t["treso"][arret]),
                             "critere": "Bénéfice net négatif 3 mois de suite (04 §6.3)"} if arret is not None else None),
            "besoin_tresorerie": r2(t["besoin"]), "mois_creux": t["mois_creux"],
        }
    pal = []
    for p in paliers:
        pal.append({
            "palier": p["cle"], "benefice_net_mensuel": p["benefice"], "ca_ht_mensuel": r2(p["ca_ht"]), "ca_ttc_mensuel": r2(p["ca_ttc"]),
            "commandes_mois": r2(p["commandes"]), "commandes_jour": r2(p["commandes_jour"]), "budget_pub_mensuel": r2(p["pub"]),
            "cpa_cible": r2(p.get("cpa")), "effectif": p["effectif"], "effectif_etp_indicatif": p["effectif_n"],
            "stock_immobilise": r2(p["stock"]), "bfr": r2(p["bfr"]), "creances": r2(p["creances"]), "dettes_court_terme": r2(p["dettes"]),
            "probabilite_estimee": p["probabilite_finance"],
            "probabilite_strategie": p["probabilite_strategie"], "probabilite_finance": p["probabilite_finance"],
            "delai_estime": p["delai"], "conditions": p["conditions"]})

    def sens_json(b, base, lignes):
        return {"base_libelle": b["libelle"], "benefice_base": r2(base),
                "variables": [{"variable": d["variable"], "code": d["code"], "benefice_moins_20": r2(d["moins_20"]),
                               "benefice_plus_20": r2(d["plus_20"]), "impact_moins_20": r2(d["impact_moins_20"]),
                               "impact_plus_20": r2(d["impact_plus_20"])} for d in lignes]}
    # Trésorerie de démarrage
    r = res["realiste"]
    t = r["treso"]
    creux_idx = t["treso"].index(min(t["treso"]))
    detail = {k: r2(sum(t[k][: creux_idx + 1])) for k in ("enc_site", "enc_tts", "achats_stock", "tva_achats",
                                                          "logistique_ttc", "remboursements", "tva_payee")}
    detail.update({k: r2(sum(r[k][: creux_idx + 1])) for k in ("pub", "ech", "frais_fixes")})
    brand = json.loads(BRAND_JSON.read_text(encoding="utf-8"))
    lot = brand["hypotheses_cles"]["micro_stock_initial"]
    code_id = {p["id"]: c for c, p in PRODUITS.items()}
    stock_ini = sum(lot[i] * (PRODUITS[code_id[i]]["prod"] + PRODUITS[code_id[i]]["droits"]) for i in code_id)
    stock_ini_sans_majoration = sum(lot[i] * (PRODUITS[code_id[i]]["prod"] / 1.2 + PRODUITS[code_id[i]]["droits"]) for i in code_id)
    conformite_p1 = V["MEDIATEUR"] + V["LEKO"] * (1 + V["TVA"]) + V["FOURNITURES"] + V["INPI_P1"] + V["RC"]
    total_avant = 45 + conformite_p1 + stock_ini * (1 + V["TVA"])
    besoins = {}
    for cle in SCENARIOS:
        rr = res[cle]
        tt = rr["treso"]
        structure = rr["ff_structure"]
        cum, mini = 0.0, 0.0
        for m in range(N):
            cum += tt["flux"][m] + structure[m]
            mini = min(mini, cum)
        besoins[cle] = {"besoin_tresorerie": r2(tt["besoin"]), "mois_creux": tt["mois_creux"],
                        "besoin_hors_comptable_et_banque": r2(-mini),
                        "tresorerie_fin_mars_2028": r2(tt["treso"][-1])}
    sens_besoin = []
    for lib_, modifs in (("Base du modèle", {}),
                         ("Statut débutant TikTok Shop pendant 6 mois au lieu de 3", {"TTS_DEBUTANT_MOIS": 6}),
                         ("Règlement TikTok Shop standard à 31 jours (période différée)", {"TTS_STANDARD": 31}),
                         ("Premier versement Stripe à 14 jours", {"STRIPE_DELAI_INITIAL": 14}),
                         ("Stock détenu de 2 mois en phase micro-stock", {"COUV_MICRO": 2.0}),
                         ("Sans comptable ni banque facturés au projet", {"COMPTABLE": 0, "BANQUE": 0})):
        sauv = {k: V[k] for k in modifs}
        V.update(modifs)
        ligne = {"hypothese": lib_}
        for cle_ in SCENARIOS:
            rr_, _e = calc_scenario(cle_, SCENARIOS[cle_], mo)
            ligne[cle_] = r2(rr_["treso"]["besoin"])
        V.update(sauv)
        sens_besoin.append(ligne)
    treso_dem = {
        "hypothese": "Départ à 0 € ; fournisseur payé à la commande ; TVA reversée le mois suivant ; IS non décaissé avant mai 2028",
        "delais_encaissement": {
            "stripe": "7 jours calendaires au premier versement, puis 3 jours ouvrés (" + SRC["stripe_payouts"] + ")",
            "shopify_payments": "3 jours (03 §4.1)",
            "paypal": "Disponible immédiatement, mais retenue possible jusqu'à 21 jours pour un nouveau vendeur (" + SRC["paypal"] + ")",
            "tiktok_shop": "31 jours après livraison pour un vendeur débutant, 8 jours en standard, 3 jours en accéléré, 1 jour en express (" + SRC["tts_regl"] + ")",
            "fournisseur": "Payé à la commande (AliExpress, CJ, usine en import groupé)"},
        "cash_avant_premier_encaissement": {
            "avant_porte_1": 45.0,
            "porte_1_conformite_ttc": r2(conformite_p1),
            "porte_1_detail": {"mediateur_cm2c": V["MEDIATEUR"], "leko_ttc": r2(V["LEKO"] * (1 + V["TVA"])), "fournitures": V["FOURNITURES"],
                               "inpi_classe_21": V["INPI_P1"], "rc_premier_mois": V["RC"]},
            "micro_stock_initial_unites": {k: v for k, v in lot.items() if k in code_id},
            "micro_stock_initial_ht": r2(stock_ini), "micro_stock_initial_ttc": r2(stock_ini * (1 + V["TVA"])),
            "micro_stock_initial_ttc_sans_majoration_20": r2(stock_ini_sans_majoration * (1 + V["TVA"])),
            "total": r2(total_avant),
            "total_si_rc_payee_a_l_annee": r2(total_avant - V["RC"] + 12 * V["RC"]),
            "note": "Ordre corrigé (C2) : le micro-stock est commandé et payé à la porte 1, avant l'ouverture des précommandes. Aucune recette n'arrive avant le premier versement Stripe, 7 jours après le premier paiement."},
        "par_scenario": besoins,
        "detail_realiste_jusqu_au_creux": {"mois_creux": MOIS[creux_idx], "cumuls": detail},
        "budget_client": 150.0,
        "sensibilite_du_besoin": sens_besoin,
        "recommandation": {"minimum_pour_vendre_le_premier_stock": r2(total_avant),
                           "reserve_pour_le_scenario_realiste": r2(res["realiste"]["treso"]["besoin"]),
                           "reserve_pour_absorber_un_succes": r2(res["optimiste"]["treso"]["besoin"]),
                           "seuil_alerte_reserve": 300.0,
                           "options_a_signer_par_le_client": {
                               "a_apport_compte_courant": r2(-(-(res["realiste"]["treso"]["besoin"] + 300) // 100) * 100),
                               "b_plafond_tiktok_shop": "Ventes TikTok Shop plafonnées au stock déjà payé, aucune collaboration d'affiliés avant le premier règlement TikTok Shop ; apport limité au minimum pour vendre le premier stock",
                               "c_arret": "Arrêt avec 45 € engagés si la porte 1 n'est pas franchie"}},
    }
    # Variante franchise de TVA (même volume, marge par commande en franchise, phase micro-stock)
    var_fr = {}
    for cle in SCENARIOS:
        rr = res[cle]
        delta = 0.0
        for m in range(N):
            if rr["import"][m] == 0:
                delta += (rr["cmd_site"][m] * (mo["SITE_MARGE_FR"] - mo["SITE_MARGE_MS"])
                          + rr["cmd_propre"][m] * (mo["PROPRE_MARGE_FR"] - mo["PROPRE_MARGE_MS"])
                          + rr["cmd_aff"][m] * (mo["AFF_MARGE_FR"] - mo["AFF_MARGE_MS"]))
        ca_2027 = sum(rr["ca_ttc"][m] for m in range(N) if EXERCICE[m] == 2027)
        var_fr[cle] = {"gain_marge_phase_micro_stock": r2(delta), "ca_encaisse_2027": r2(ca_2027),
                       "franchise_tenable_2027": ca_2027 <= V["FRANCHISE_SEUIL_MAJORE"]}
    # Rémunération du dirigeant : net en poche pour 1 000 € de bénéfice net mensuel
    b_ = 1000.0
    remu = {
        "base": "1 000 € de bénéfice net mensuel (avant IS et rémunération), entièrement versé au dirigeant",
        "sasu_dividendes": r2(b_ * (1 - V["IS_TAUX_REDUIT"]) * (1 - V["PFU"])),
        "sasu_salaire": r2(b_ / (1 + V["CHARGES_SASU"])),
        "eurl_tns_remuneration": r2(b_ / (1 + V["CHARGES_TNS"])),
        "eurl_cotisations_minimales_annuelles": V["TNS_MINIMUM"],
        "heures_par_mois": r2(V["HEURES_FONDATEUR"] * 52 / 12),
        "smic_net_horaire": V["SMIC_NET_H"],
    }
    remu["taux_horaire_sasu_dividendes"] = r2(remu["sasu_dividendes"] / remu["heures_par_mois"])
    remu["taux_horaire_sasu_salaire"] = r2(remu["sasu_salaire"] / remu["heures_par_mois"])
    remu["taux_horaire_eurl_tns"] = r2(remu["eurl_tns_remuneration"] / remu["heures_par_mois"])
    # Net en poche au volume du palier 1 selon la forme juridique (même nombre de commandes)
    n1 = paliers[0]["commandes"]
    f1 = paliers[0]["frais_fixes"]
    ca1 = n1 * mo["MIX_TTC"]
    ben_ass = n1 * mo["MIX_MARGE_MS"] - f1
    ben_fr = n1 * mo["MIX_MARGE_FR"] - f1
    micro_avant_ir = n1 * mo["MIX_MARGE_MICRO"] - (f1 - V["COMPTABLE"])
    remu["comparaison_palier_1"] = {
        "commandes_mois": r2(n1), "ca_encaisse_mois": r2(ca1),
        "lignes": [
            {"forme": "SASU ou EURL assujettie à la TVA, dividendes", "benefice_avant_is": r2(ben_ass),
             "net_en_poche": r2(ben_ass * (1 - V["IS_TAUX_REDUIT"]) * (1 - V["PFU"])), "protection_sociale": "Aucune (dividendes)"},
            {"forme": "SASU en franchise de TVA, dividendes", "benefice_avant_is": r2(ben_fr),
             "net_en_poche": r2(ben_fr * (1 - V["IS_TAUX_REDUIT"]) * (1 - V["PFU"])), "protection_sociale": "Aucune (dividendes)"},
            {"forme": "SASU en franchise de TVA, salaire du président", "benefice_avant_is": r2(ben_fr),
             "net_en_poche": r2(ben_fr / (1 + V["CHARGES_SASU"])), "protection_sociale": "Régime général sans chômage"},
            {"forme": "EURL en franchise de TVA, rémunération du gérant (TNS)", "benefice_avant_is": r2(ben_fr),
             "net_en_poche": r2(ben_fr / (1 + V["CHARGES_TNS"])), "protection_sociale": "Sécurité sociale des indépendants ; cotisations minimales ≈ 1 423 € par an même sans rémunération"},
            {"forme": "Micro-entreprise en franchise, versement libératoire", "benefice_avant_is": r2(micro_avant_ir),
             "net_en_poche": r2(micro_avant_ir - V["MICRO_VL"] * ca1), "protection_sociale": "Incluse dans les 12,3 % ; pas d'expert-comptable obligatoire"},
        ]}
    remu["benefice_net_pour_un_smic_net_horaire_sasu_dividendes"] = r2(V["SMIC_NET_H"] * remu["heures_par_mois"] / ((1 - V["IS_TAUX_REDUIT"]) * (1 - V["PFU"])))

    return {
        "meta": {"marque": "Canapoil", "date": "2026-10-12", "version": "1.0", "devise": "EUR",
                 "genere_par": "finance/modele_financier.py", "source_prix": "strategie/brand.json",
                 "regime_de_base": "Société à l'IS assujettie à la TVA (SASU ou EURL) ; variantes franchise et micro-entreprise dans unit_economics",
                 "definition_benefice_net": "Résultat mensuel après tous les coûts, avant IS et avant rémunération du dirigeant",
                 "verification": ({"valeurs_comparees_excel_python": verif[0], "ecarts": len(verif[1]), "erreurs_formules": len(verif[2])}
                                  if verif else "non effectuée")},
        "unit_economics": {"cascades": cascades, "par_offre": par_offre,
                           "moyennes_par_canal": {k: r2(v) for k, v in mo.items()},
                           "comparaison_regimes": {
                               "societe_assujettie": {"site_rouleau": r2(ue["MS"]["site-rou"]["marge"]), "site_grand_kit": r2(ue["MS"]["site-gk"]["marge"]),
                                                      "tiktok_affilie_rouleau": r2(ue["MS"]["tts-aff-rou"]["marge"]), "mix": r2(mo["MIX_MARGE_MS"])},
                               "societe_franchise_tva": {"site_rouleau": r2(ue["FR"]["site-rou"]["marge"]), "site_grand_kit": r2(ue["FR"]["site-gk"]["marge"]),
                                                         "tiktok_affilie_rouleau": r2(ue["FR"]["tts-aff-rou"]["marge"]), "mix": r2(mo["MIX_MARGE_FR"])},
                               "micro_entreprise": {"site_rouleau": r2(ue["MICRO"]["site-rou"]["marge"]), "site_grand_kit": r2(ue["MICRO"]["site-gk"]["marge"]),
                                                    "tiktok_affilie_rouleau": r2(ue["MICRO"]["tts-aff-rou"]["marge"]), "mix": r2(mo["MIX_MARGE_MICRO"])}}},
        "seuils": seuils_d,
        "scenarios": scen,
        "paliers": pal,
        "sensibilite": sens_json(*s1),
        "sensibilite_phase_payante": sens_json(*s2),
        "tresorerie_demarrage": treso_dem,
        "variante_franchise_tva": var_fr,
        "remuneration_dirigeant": remu,
    }


if __name__ == "__main__":
    main()
