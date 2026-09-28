#!/usr/bin/env python3
"""Construit un épisode : JSON de scènes → voix off alignée → timeline.json + mixage audio.

Usage : .venv/bin/python tools/build.py episodes/<slug>
Sorties (episodes/<slug>/build/) :
  timeline.json   données de rendu (plans, sous-titres, habillage, temps forts)
  vo.wav          voix off seule        music.wav   musique seule      sfx.wav  bruitages seuls
  mix.wav         mixage final (-14 LUFS, crête -1 dBTP)
  mix_sans_voix.wav  musique + bruitages (pour enregistrer sa propre voix par-dessus)
  sous-titres.srt    sous-titres horodatés
"""
import hashlib
import json
import os
import re
import sys
import unicodedata

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audiolib import SR, secs, place, write_wav, duck_gain, limiter, loudness_normalize, db  # noqa: E402
import sfx  # noqa: E402
import music  # noqa: E402
from tts import synth, voice_chain  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r"[^a-z0-9€%]", '', w)


def match_keywords(words, phrases):
    """Marque les mots appartenant à une expression-clé (séquence de mots consécutifs)."""
    hits = set()
    nw = [norm(w['text']) for w in words]
    for ph in phrases:
        toks = [norm(x) for x in ph.split() if norm(x)]
        if not toks:
            continue
        for i in range(len(nw) - len(toks) + 1):
            if all(nw[i + k] == toks[k] or (len(toks[k]) > 4 and nw[i + k].startswith(toks[k][:-1])) for k in range(len(toks))):
                hits.update(range(i, i + len(toks)))
    return hits


def chunk_words(words, max_words=3, max_chars=17):
    chunks, cur = [], []
    for w in words:
        test = cur + [w]
        chars = sum(len(x['text']) for x in test) + len(test) - 1
        if cur and (len(test) > max_words or chars > max_chars):
            chunks.append(cur)
            cur = [w]
        else:
            cur = test
        if re.search(r'[.,!?;:…]$', w['text'].replace(' ', '')) and cur:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def snap(t, step):
    return np.ceil(t / step - 1e-6) * step


def fmt_srt(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}'.replace(',1000', ',999')


def build(ep_dir):
    ep = json.load(open(os.path.join(ep_dir, 'episode.json'), encoding='utf-8'))
    out = os.path.join(ep_dir, 'build')
    os.makedirs(out, exist_ok=True)
    fps = ep.get('fps', 30)
    vcfg = ep.get('voix', {})
    model = os.path.join(ROOT, '.voices', vcfg.get('modele', 'fr_FR-siwis-medium') + '.onnx')
    lex = vcfg.get('lexique', {})
    bpm = ep.get('musique', {}).get('bpm', 140)
    step = 60.0 / bpm / 4

    # 1) Voix off par scène.
    t = 0.0
    scenes = []
    for sc in ep['scenes']:
        start = snap(t, step) if scenes else 0.0
        vo, words = None, []
        if sc.get('voix_off'):
            # Cache : même texte + mêmes réglages → même prise (le TTS est aléatoire ; les plaques 3D restent synchrones).
            key = hashlib.sha1(json.dumps([model, sc['voix_off'], vcfg.get('length_scale', 0.86), lex], ensure_ascii=False).encode()).hexdigest()[:16]
            cdir = os.path.join(out, 'tts_cache')
            os.makedirs(cdir, exist_ok=True)
            cwav, cjson = os.path.join(cdir, key + '.npy'), os.path.join(cdir, key + '.json')
            if os.path.exists(cwav) and os.path.exists(cjson):
                vo, words = np.load(cwav), json.load(open(cjson, encoding='utf-8'))
            else:
                vo, words = synth(model, sc['voix_off'], length_scale=vcfg.get('length_scale', 0.86), lexicon=lex)
                vo = voice_chain(vo)
                np.save(cwav, vo)
                json.dump(words, open(cjson, 'w', encoding='utf-8'), ensure_ascii=False)
            words = [dict(w) for w in words]
        lead = sc.get('lead', 0.08 if scenes else 0.12)
        vo_dur = (len(vo) / SR) if vo is not None else 0.0
        spoken_end = (words[-1]['end'] if words else 0.0)
        dur = max(sc.get('duree_min', 0.0), lead + spoken_end + sc.get('pad', 0.12), sc.get('duree', 0.0))
        for w in words:
            w['start'] += start + lead
            w['end'] += start + lead
        scenes.append({'sc': sc, 'start': start, 'end': start + dur, 'vo': vo, 'vo_at': start + lead, 'words': words, 'vo_dur': vo_dur})
        t = start + dur
    total = scenes[-1]['end'] + ep.get('queue', 0.0)
    # Durée plancher (ex. 61,5 s pour rester au-dessus du seuil « > 1 min » malgré la variabilité du TTS).
    if ep.get('duree_min_totale') and total < ep['duree_min_totale']:
        total = ep['duree_min_totale']
    print(f'durée totale : {total:.2f} s — {sum(len(s["words"]) for s in scenes)} mots')

    def word_time(s, key, default):
        """Instant où commence l'expression `key` (séquence de mots, préfixes tolérés)."""
        if key is None:
            return default
        toks = [norm(k) for k in key.split() if norm(k)]
        nw = [norm(w['text']) for w in s['words']]
        for i in range(len(nw) - len(toks) + 1):
            if all(nw[i + k].startswith(toks[k]) for k in range(len(toks))):
                return s['words'][i]['start']
        print(f'  ! mot introuvable pour synchro : « {key} » ({s["sc"]["id"]})')
        return default

    # 2) Plans (coupes calées sur les fins de mots).
    shots, overlays, beats, cues, captions, markers, images = [], [], [], [], [], [], set()
    for si, s in enumerate(scenes):
        sc = s['sc']
        plans = sc.get('plans', [{'set': 'studio'}])
        weights = [p.get('poids', 1.0) for p in plans]
        dur = s['end'] - s['start']
        bounds = [s['start']]
        acc = s['start']
        for k in range(1, len(plans)):
            p = plans[k]
            target = acc + dur * weights[k - 1] / sum(weights)
            if p.get('coupe_sur'):
                target = word_time(s, p['coupe_sur'], target) - 0.04
            elif s['words']:
                ends = [w['end'] + 0.04 for w in s['words'] if acc + 0.6 < w['end'] + 0.04 < s['end'] - 0.6]
                if ends:
                    target = min(ends, key=lambda e: abs(e - target))
            bounds.append(min(s['end'] - 0.3, max(acc + 0.45, target)))
            acc = bounds[-1]
        bounds.append(s['end'])
        for k, p in enumerate(plans):
            shot = {
                'id': f"{sc['id']}_{k + 1}", 'scene': sc['id'], 'set': p.get('set', 'studio'),
                'start': round(bounds[k], 4), 'end': round(bounds[k + 1], 4),
                'cam': p.get('cam', 'hero'), 'params': p.get('params', {}),
            }
            for key in ('dof', 'noDof', 'grade', 'bloom', 'tone'):
                if key in p:
                    shot[key] = p[key]
            trans_in = p.get('trans', 'whip' if (k == 0 and si > 0) else 'cut')
            if trans_in != 'cut' and shots:
                shot['transIn'] = trans_in
                shots[-1]['transOut'] = trans_in
            shots.append(shot)
            for key in ('image', 'avatar'):
                for obj in [p.get('params', {}).get('wall', {}), p.get('params', {}).get('phone', {})] + p.get('params', {}).get('totems', []):
                    if isinstance(obj, dict) and obj.get(key):
                        images.add(obj[key])
                    for it in (obj.get('items', []) if isinstance(obj, dict) else []):
                        if it.get('image'):
                            images.add(it['image'])

        # 3) Sous-titres.
        if s['words'] and not sc.get('sans_sous_titres'):
            hl = match_keywords(s['words'], sc.get('mots_cles', []))
            red = match_keywords(s['words'], sc.get('mots_rouges', []))
            green = match_keywords(s['words'], sc.get('mots_verts', []))
            idx = {id(w): i for i, w in enumerate(s['words'])}
            chunks = chunk_words(s['words'])
            for ci, ch in enumerate(chunks):
                c_start = ch[0]['start'] - 0.03
                c_end = chunks[ci + 1][0]['start'] - 0.03 if ci + 1 < len(chunks) else min(s['end'], ch[-1]['end'] + 0.35)
                ws = []
                for w in ch:
                    i = idx[id(w)]
                    h = 'red' if i in red else 'green' if i in green else (True if i in hl else False)
                    ws.append({'text': w['text'].replace(' ', ' '), 'start': round(w['start'], 3), 'end': round(w['end'], 3), 'hl': h})
                cap = {'start': round(c_start, 3), 'end': round(c_end, 3), 'words': ws}
                if sc.get('sous_titres_y'):
                    cap['y'] = sc['sous_titres_y']
                if sc.get('sous_titres_boite'):
                    cap['box'] = True
                captions.append(cap)

        # 4) Habillage (temps relatifs à la scène ou synchronisés sur un mot).
        for o in sc.get('habillage', []):
            o = dict(o)
            st = word_time(s, o.pop('au_mot', None), s['start'] + o.pop('at', 0.0))
            d = o.pop('dur', 'scene')
            en = s['end'] if d == 'scene' else st + d
            if o.get('type') == 'progress':
                o['segStart'], o['segEnd'] = s['start'], s['end']
            o['start'], o['end'] = round(st, 3), round(en, 3)
            if o.get('image'):
                images.add(o['image'])
            overlays.append(o)
            auto = {'headline': 'swish', 'chip': 'pop', 'stamp': 'stamp', 'emoji': 'pop_hi', 'counter': None, 'arrow': 'swish', 'circle': 'swish', 'lowerthird': 'whoosh', 'quote': 'notif', 'photo': 'shutter'}
            if auto.get(o['type']) and not o.get('muet'):
                cues.append({'t': st, 'sfx': auto[o['type']], 'gain': 0.7})
            if o['type'] == 'counter' and not o.get('muet'):
                cd = o.get('countDur', min(1.4, (en - st) * 0.7))
                n_ticks = 14
                for k in range(n_ticks):
                    cues.append({'t': st + cd * (1 - (1 - k / n_ticks) ** 2), 'sfx': 'tick', 'gain': 0.8})
                cues.append({'t': st + cd, 'sfx': 'cash' if '€' in o.get('suffix', '') + o.get('prefix', '') else 'ding', 'gain': 0.8})

        # 5) Bruitages et temps forts.
        for b in sc.get('bruitages', []):
            bt = word_time(s, b.get('au_mot'), (s['end'] - b['avant_fin']) if 'avant_fin' in b else s['start'] + b.get('at', 0.0))
            cues.append({'t': bt, 'sfx': b['sfx'], 'gain': b.get('gain', 1.0)})
            if b['sfx'] in ('boom', 'bass_drop'):
                beats.append({'t': round(bt, 3), 'shake': b.get('shake', 1.0), 'flash': b.get('flash', 0.35)})
            elif b['sfx'] in ('hit', 'stamp'):
                beats.append({'t': round(bt, 3), 'shake': b.get('shake', 0.55)})
            elif b['sfx'] in ('riser', 'riser_long'):
                pass
        for b in sc.get('temps_forts', []):
            bt = word_time(s, b.get('au_mot'), s['start'] + b.get('at', 0.0))
            beats.append({'t': round(bt, 3), 'shake': b.get('shake', 0.0), 'flash': b.get('flash', 0.0)})
        if sc.get('musique'):
            mt = word_time(s, sc.get('musique_au_mot'), s['start'] + sc.get('musique_decalage', 0.0))
            m = {'t': mt, 'type': sc['musique']}
            if sc['musique'] == 'stop':
                m['len'] = sc.get('musique_duree', 0.45)
            markers.append(m)
        if sc.get('musique_fin'):
            markers.append({'t': s['end'] - sc.get('musique_fin_avance', 1.8), 'type': sc['musique_fin']})

    # Whooshes automatiques sur les transitions.
    for sh in shots:
        if sh.get('transIn') in ('whip', 'whipUp'):
            cues.append({'t': sh['start'] - 0.26, 'sfx': 'whoosh' if len(cues) % 2 else 'whoosh_l', 'gain': 0.75})
        elif sh.get('transIn') == 'zoom':
            cues.append({'t': sh['start'] - 0.3, 'sfx': 'whoosh_big', 'gain': 0.6})

    # 6) Audio : voix, bruitages, musique, mixage.
    n = secs(total + 0.5)
    vo_track = np.zeros((n, 2), dtype=np.float32)
    for s in scenes:
        if s['vo'] is not None:
            place(vo_track, s['vo'], s['vo_at'], 1.0)
    sfx_track = np.zeros((n, 2), dtype=np.float32)
    for c in cues:
        place(sfx_track, sfx.get(c['sfx']), c['t'], c.get('gain', 1.0))
    markers.sort(key=lambda m: m['t'])
    if not markers or markers[0]['t'] > 0:
        markers.insert(0, {'t': 0.0, 'type': 'drop'})
    mus, grid = music.generate(total + 0.5, markers, bpm=bpm)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    g = duck_gain(vo_track, depth_db=-9, thresh=0.02)
    mus_ducked = mus * g[:, None]

    vo_level, sfx_level, mus_level = db(0), db(-7), db(-13)
    mix = vo_track * vo_level + sfx_track * sfx_level + mus_ducked * mus_level
    mix, lufs_in = loudness_normalize(mix, -14.0)
    mix = limiter(mix, -1.0)
    nov = sfx_track * sfx_level + mus * mus_level
    nov, _ = loudness_normalize(nov, -16.0)
    nov = limiter(nov, -1.0)
    write_wav(os.path.join(out, 'mix.wav'), mix[:secs(total)])
    write_wav(os.path.join(out, 'mix_sans_voix.wav'), nov[:secs(total)])
    write_wav(os.path.join(out, 'vo.wav'), vo_track[:secs(total)])
    write_wav(os.path.join(out, 'music.wav'), (mus * db(-3))[:secs(total)])
    write_wav(os.path.join(out, 'sfx.wav'), (sfx_track * db(-3))[:secs(total)])

    # 7) Timeline + sous-titres SRT.
    tl = {
        'fps': fps, 'width': ep.get('width', 1080), 'height': ep.get('height', 1920), 'duration': round(total, 3),
        'shots': shots, 'captions': captions, 'overlays': overlays,
        'beats': sorted(beats, key=lambda b: b['t']), 'images': sorted(images), 'music': grid,
    }
    json.dump(tl, open(os.path.join(out, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'sous-titres.srt'), 'w', encoding='utf-8') as f:
        for i, c in enumerate(captions, 1):
            f.write(f"{i}\n{fmt_srt(c['start'])} --> {fmt_srt(c['end'])}\n{' '.join(w['text'] for w in c['words'])}\n\n")
    # Récapitulatif des scènes (pour le JSON de production et l'audit).
    recap = [{'id': s['sc']['id'], 'role': s['sc'].get('role'), 'debut_s': round(s['start'], 2), 'duree_s': round(s['end'] - s['start'], 2),
              'mots': len(s['words'])} for s in scenes]
    json.dump(recap, open(os.path.join(out, 'scenes_recap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    words_total = sum(len(s['words']) for s in scenes)
    print(f'plans : {len(shots)} (durée moyenne {total / len(shots):.2f} s) · sous-titres : {len(captions)} · habillages : {len(overlays)} · bruitages : {len(cues)}')
    print(f'débit : {words_total / total:.2f} mots/s · loudness avant normalisation : {lufs_in:.1f} LUFS')
    return tl


if __name__ == '__main__':
    build(os.path.abspath(sys.argv[1]))
