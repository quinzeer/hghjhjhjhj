#!/usr/bin/env python3
"""Télécharge les assets CC0 de Poly Haven (HDRI + modèles glTF) utilisés par le moteur.

Usage : python tools/fetch_assets.py            # set par défaut
        python tools/fetch_assets.py hdri:neon_photostudio:2k model:Megaphone_01:1k
Les fichiers vont dans assets/polyhaven/ (ignoré par git : ils se re-téléchargent).
Licence Poly Haven : CC0 (aucune attribution requise).
"""
import json, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'polyhaven')
DEFAULT = [
    'hdri:studio_small_09:2k', 'hdri:neon_photostudio:2k', 'hdri:modern_buildings_night:2k',
    'hdri:ferndale_studio_03:1k',
    'model:Megaphone_01:1k', 'model:vintage_suitcase:1k', 'model:magnifying_glass_01:1k',
    'model:security_camera_01:1k', 'model:marble_bust_01:1k',
]

def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'tiktok-studio/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest + '.part', 'wb') as f:
        f.write(r.read())
    os.replace(dest + '.part', dest)

def files(asset_id):
    req = urllib.request.Request(f'https://api.polyhaven.com/files/{asset_id}', headers={'User-Agent': 'tiktok-studio/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def fetch(spec):
    kind, asset_id, res = spec.split(':')
    info = files(asset_id)
    if kind == 'hdri':
        url = info['hdri'][res]['hdr']['url']
        get(url, os.path.join(ROOT, 'hdri', f'{asset_id}_{res}.hdr'))
    elif kind == 'model':
        g = info['gltf'][res]['gltf']
        base = os.path.join(ROOT, 'models', asset_id)
        get(g['url'], os.path.join(base, f'{asset_id}.gltf'))
        for rel, inc in g.get('include', {}).items():
            get(inc['url'], os.path.join(base, rel))
    print('ok', spec)

if __name__ == '__main__':
    for s in (sys.argv[1:] or DEFAULT):
        try:
            fetch(s)
        except Exception as e:
            print('FAIL', s, e)
