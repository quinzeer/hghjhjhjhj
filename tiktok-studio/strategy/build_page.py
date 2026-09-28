#!/usr/bin/env python3
"""Remplit la page de stratégie avec les données réelles de l'épisode (timeline construite).

Usage : python strategy/build_page.py episodes/nasdas-01 strategy/out
Copie aussi la vidéo web (out/web.mp4 → nasdas-01-web.mp4) et l'affiche (poster.jpg).
"""
import html
import json
import os
import shutil
import sys

ROLE_VAR = {'hook': 'hook', 'relance': 'relance', 'cadre': 'cadre', 'contenu': 'contenu', 'payoff': 'payoff', 'boucle': 'boucle'}


def main(ep_dir, out_dir):
    here = os.path.dirname(os.path.abspath(__file__))
    tpl = open(os.path.join(here, 'page.template.html'), encoding='utf-8').read()
    ep = json.load(open(os.path.join(ep_dir, 'episode.json'), encoding='utf-8'))
    tl = json.load(open(os.path.join(ep_dir, 'build', 'timeline.json'), encoding='utf-8'))
    recap = json.load(open(os.path.join(ep_dir, 'build', 'scenes_recap.json'), encoding='utf-8'))
    roles = {sc['id']: sc.get('role', 'contenu') for sc in ep['scenes']}
    labels = {sc['id']: sc.get('texte_ecran', '') for sc in ep['scenes']}
    total = tl['duration']
    words = sum(r['mots'] for r in recap)
    segs = []
    for r in recap:
        role = ROLE_VAR.get(roles[r['id']], 'contenu')
        tip = html.escape(f"{r['id']} · {r['debut_s']:.1f}–{r['debut_s'] + r['duree_s']:.1f} s · {labels[r['id']]}")
        segs.append(f'<div class="seg" style="flex:{r["duree_s"]:.2f} 1 0;background:var(--{role})" title="{tip}"><span>{r["id"][1:]}</span></div>')
    rows = []
    for s in ep.get('sources', []):
        rows.append(f"<tr><td>{html.escape(s['fait'])}</td><td><a href=\"{html.escape(s['url'])}\">{html.escape(s['source'])}</a></td><td><span class=\"conf {s['confiance']}\">{s['confiance']}</span></td></tr>")
    m = ep.get('metadonnees', {})
    rep = {
        '{{DURATION}}': f'{total:.1f}'.replace('.', ','),
        '{{SHOTS}}': str(len(tl['shots'])),
        '{{AVGSHOT}}': f"{total / len(tl['shots']):.1f}".replace('.', ','),
        '{{WPS}}': f'{words / total:.2f}'.replace('.', ','),
        '{{CAPTIONS}}': str(len(tl['captions'])),
        '{{RUNDOWN}}': ''.join(segs),
        '{{SOURCES}}': ''.join(rows),
        '{{CAPTION}}': html.escape(m.get('description', '')),
        '{{HASHTAGS}}': html.escape(' '.join(m.get('hashtags', []))),
        '{{PINNED}}': html.escape(m.get('commentaire_epingle', '')),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(tpl)
    for src, dst in [('out/web.mp4', 'nasdas-01-web.mp4'), ('out/poster.jpg', 'poster.jpg')]:
        p = os.path.join(ep_dir, src)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(out_dir, dst))
    print('page :', os.path.join(out_dir, 'index.html'))


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
