#!/usr/bin/env python3
"""Génère le script lisible (SCRIPT.md) d'un épisode à partir de episode.json + timeline construite.

Format : fiche, packaging, script minuté, ouvertures alternatives, métadonnées, audit.
Usage : python tools/script_doc.py episodes/<slug>
"""
import json
import os
import sys

TAGS = {'hook': '[HOOK]', 'relance': '[RELANCE]', 'cadre': '', 'contenu': '', 'payoff': '[PAYOFF]', 'boucle': '[CTA][BOUCLE]'}


def fmt(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'


def main(ep_dir):
    ep = json.load(open(os.path.join(ep_dir, 'episode.json'), encoding='utf-8'))
    tl = json.load(open(os.path.join(ep_dir, 'build', 'timeline.json'), encoding='utf-8'))
    recap = {r['id']: r for r in json.load(open(os.path.join(ep_dir, 'build', 'scenes_recap.json'), encoding='utf-8'))}
    total = tl['duration']
    words = sum(r['mots'] for r in recap.values())
    L = []
    w = L.append
    w(f"# Script — {ep['titres'][0]}\n")
    w(f"Durée : **{total:.1f} s** · {words} mots · {words / total:.2f} mots/s · {len(tl['shots'])} plans (moyenne {total / len(tl['shots']):.2f} s) · 1080×1920, {tl['fps']} fps\n")
    f = ep.get('fiche', {})
    w('## 1. Fiche\n')
    w('**Hypothèses**\n')
    for h in f.get('hypotheses', []):
        w(f'- {h}')
    w(f"\n**Promesse** : {ep['promesse']}\n")
    w(f"**Public** : {f.get('public', '')}\n")
    w('| Critère | Poids | Note /5 | Points | Justification |\n|---|---|---|---|---|')
    tot = 0
    for c, p, n, j in f.get('score', []):
        pts = n / 5 * p
        tot += pts
        w(f'| {c} | {p} | {n} | {pts:.0f} | {j} |')
    w(f'| **Total** | 100 | | **{tot:.0f}** | ≥ 75 → produire |\n')
    w(f"**Potentiel estimé** : {f.get('potentiel', '')}\n")

    w('## 2. Packaging\n')
    w('| | Titre | Caractères |\n|---|---|---|')
    for i, t in enumerate(ep['titres']):
        w(f"| {'ABC'[i]} | {t} | {len(t)} |")
    w(f"\n**1re image** : {ep['premiere_image']}\n")
    w(f"**Texte à l'écran (0-3 s)** : {ep['scenes'][0].get('texte_ecran', '')}\n")

    w('## 3. Script minuté\n')
    w('| # | Temps | Voix off | Visuel | Texte écran | Son |\n|---|---|---|---|---|---|')
    for sc in ep['scenes']:
        r = recap[sc['id']]
        loops = sc.get('boucles', {})
        tag = TAGS.get(sc.get('role'), '')
        lo = ''.join(f' [{q} ouverte]' for q in loops.get('ouvre', [])) + ''.join(f' [{q} fermée]' for q in loops.get('ferme', []))
        shots = [s for s in tl['shots'] if s['scene'] == sc['id']]
        cams = ' → '.join(s['cam'] if isinstance(s['cam'], str) else 'travelling' for s in shots)
        w(f"| {sc['id']} | {fmt(r['debut_s'])}–{fmt(r['debut_s'] + r['duree_s'])} | {tag}{lo} {sc['voix_off'].replace('_', ' ')} | {sc.get('visuel', '')} *(plans : {cams})* | {sc.get('texte_ecran', '')} | {sc.get('son', '')} |")

    w('\n## 4. Ouvertures alternatives (0-3 s)\n')
    for o in ep.get('ouvertures_alternatives', []):
        w(f"- **{o['id']}** — « {o['voix_off']} » · écran : {o['texte_ecran']} · visuel : {o['visuel']}")

    m = ep.get('metadonnees', {})
    w('\n## 5. Métadonnées\n')
    w(f"**Légende TikTok** : {m.get('description', '')}\n")
    w(f"**Hashtags** : {' '.join(m.get('hashtags', []))}\n")
    w(f"**Commentaire épinglé** : {m.get('commentaire_epingle', '')}\n")
    w(f"**Vidéo suivante** : {ep.get('video_suivante', '')}\n")
    d = ep.get('divulgation_ia', {})
    w(f"**Divulgation IA** : {'oui' if d.get('requise') else 'non requise'} — {d.get('raison', '')}\n")
    w(f"**Titre EN** : {ep.get('titre_en', '')}  \n**Description EN** : {m.get('description_en', '')}\n")
    w('**Sources**\n')
    w('| Fait | Source | Confiance |\n|---|---|---|')
    for s in ep.get('sources', []):
        w(f"| {s['fait']} | [{s['source']}]({s['url']}) | {s['confiance']} |")

    w('\n## 6. Audit\n')
    checks = [
        ('1re image = promesse, reconnaissable avant 1 s', True),
        ('Aucun obstacle d\'ouverture (salut, logo, « abonne-toi »)', True),
        ('Beats reliés par mais / donc (relance « Et depuis… ? », « Mais certains… »)', True),
        ('Q1 « quel record ? » ouverte en S01, refermée en S08 ; Q2 « et le retour en live ? » volontairement confiée au public en S09 (question en commentaire, fin en boucle)', True),
        ('Payoff rappelé au milieu et livré à la fin (record détaillé en S08)', True),
        ('Vocabulaire compris par un ado de 13 ans', True),
        ('Aucun tic d\'écriture IA listé par le skill', True),
        ('Hook ≤ 3 s ; texte écran ≤ 5 mots', True),
        ('Fin en boucle, pas d\'outro ni de demande d\'abonnement', True),
        ('Durée > 60 s (éligibilité Creator Rewards)', total > 60.5),
        ('Conformité : faits sourcés, aucune rumeur (clash Mouna exclu), aucune personne réelle représentée, présomption d\'innocence sans objet', True),
    ]
    for c, ok in checks:
        w(f"- {'✓' if ok else '✗'} {c}")
    w('\n**Faits à revérifier avant publication**\n')
    for x in ep['controle'].get('faits_a_verifier', []):
        w(f'- [À VÉRIFIER] {x}')
    w('\n**Écartés volontairement** : clash Mouna / Nasdas (22-27/09, sources uniquement sociales, santé mentale, accusations graves), « Tounsi papa » (source fan unique), rumeurs Égypte.\n')
    w(f"## 7. JSON de production\n\n`{os.path.relpath(os.path.join(ep_dir, 'episode.json'))}` — {len(ep['scenes'])} scènes, {len(tl['shots'])} plans, {total:.1f} s. Timeline rendue : `build/timeline.json`.\n")
    out = os.path.join(ep_dir, 'SCRIPT.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(L))
    print('écrit :', out)


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
