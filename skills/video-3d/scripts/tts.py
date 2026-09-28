#!/usr/bin/env python3
"""Voix off d'un projet vidéo 3D (voix neuronales) + horodatage mot à mot pour les sous-titres.

Moteurs :
  edge        (défaut, gratuit)  voix Microsoft Neural via le paquet edge-tts
  elevenlabs  (option, payant)   plus expressif ; ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID requis
              (non testé ici faute de clé : vérifier la sortie sur une réplique avant un rendu complet)

Usage :
  python3 tts.py <projet> [--engine edge|elevenlabs]
Lit <projet>/story.json (champ "say" de chaque beat) → <projet>/voices/<id>.mp3 + voices/manifest.json
Voix : story.voice (défaut fr-FR-RemyMultilingualNeural), story.rate ; surchargeables par beat (voice, rate, pitch).
Réseau derrière un proxy TLS : définir TTS_CA_BUNDLE=/chemin/vers/ca.pem
"""
import argparse, asyncio, base64, hashlib, json, os, re, ssl, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'

def media_duration(path):
    r = subprocess.run([ffmpeg_exe(), '-hide_banner', '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', r.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0

def align(text, tokens):
    """Rattache la ponctuation du texte original aux mots renvoyés par le moteur."""
    pos, cur = [], 0
    for tok, _, _ in tokens:
        i = text.find(tok, cur)
        if i < 0:
            i = cur
        pos.append(i)
        cur = i + len(tok)
    out = []
    for k, (tok, t, d) in enumerate(tokens):
        end = pos[k + 1] if k + 1 < len(pos) else len(text)
        w = text[pos[k]:end].strip() or tok
        out.append({'w': w, 't': round(t, 3), 'd': round(d, 3)})
    return out

# ---------- edge-tts ----------
async def edge_line(text, voice, rate, pitch, path):
    import edge_tts, edge_tts.communicate as C
    ca = os.environ.get('TTS_CA_BUNDLE')
    if ca:
        C._SSL_CTX = ssl.create_default_context(cafile=ca)
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary='WordBoundary')
    audio, toks = b'', []
    async for ch in com.stream():
        if ch['type'] == 'audio':
            audio += ch['data']
        elif ch['type'] == 'WordBoundary':
            toks.append((ch['text'], ch['offset'] / 1e7, ch['duration'] / 1e7))
    with open(path, 'wb') as f:
        f.write(audio)
    return toks

# ---------- ElevenLabs ----------
def eleven_line(text, path, style=0.55):
    key, vid = os.environ['ELEVENLABS_API_KEY'], os.environ['ELEVENLABS_VOICE_ID']
    model = os.environ.get('ELEVENLABS_MODEL', 'eleven_multilingual_v2')
    body = json.dumps({'text': text, 'model_id': model,
                       'voice_settings': {'stability': 0.35, 'similarity_boost': 0.8, 'style': style, 'use_speaker_boost': True}}).encode()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128',
                                 data=body, headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    ctx = ssl.create_default_context(cafile=os.environ.get('TTS_CA_BUNDLE')) if os.environ.get('TTS_CA_BUNDLE') else None
    with urllib.request.urlopen(req, context=ctx, timeout=120) as r:
        js = json.loads(r.read())
    with open(path, 'wb') as f:
        f.write(base64.b64decode(js['audio_base64']))
    al = js.get('alignment') or js.get('normalized_alignment')
    toks, cur, t0, t1 = [], '', None, None
    for ch, a, b in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if ch.isspace():
            if cur:
                toks.append((cur, t0, t1 - t0)); cur = ''
            continue
        if not cur:
            t0 = a
        cur += ch; t1 = b
    if cur:
        toks.append((cur, t0, t1 - t0))
    # le texte affiché garde la ponctuation : on retire celle collée au mot pour l'alignement
    return [(re.sub(r'[^\w\-\'’]+$', '', w) or w, a, d) for w, a, d in toks]

def h(*parts):
    return hashlib.sha1('|'.join(parts).encode()).hexdigest()[:12]

async def run_lines(items, engine, outdir, old):
    """items : liste de dict(id, text, voice, rate, pitch). Renvoie le manifeste {id: {...}}."""
    man, sem = {}, asyncio.Semaphore(4)
    async def one(it):
        fid = it['id']
        path = os.path.join(outdir, f'{fid}.mp3')
        sig = h(engine, it['text'], it['voice'], it.get('rate', ''), it.get('pitch', ''))
        if fid in old and old[fid].get('sig') == sig and os.path.exists(path):
            man[fid] = old[fid]; return
        async with sem:
            for attempt in range(4):
                try:
                    if engine == 'edge':
                        toks = await edge_line(it['text'], it['voice'], it.get('rate', '+0%'), it.get('pitch', '+0Hz'), path)
                    else:
                        toks = await asyncio.to_thread(eleven_line, it['text'], path)
                    break
                except Exception as e:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(2 ** attempt)
        words = align(it['text'], toks)
        speech_end = (words[-1]['t'] + words[-1]['d']) if words else 0
        man[fid] = {'file': os.path.basename(path), 'text': it['text'], 'dur': round(speech_end + 0.08, 3),
                    'fileDur': round(media_duration(path), 3), 'words': words, 'sig': sig}
    await asyncio.gather(*(one(it) for it in items))
    return man

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--engine', default='edge', choices=['edge', 'elevenlabs'])
    a = ap.parse_args()
    story = json.load(open(os.path.join(a.project, 'story.json')))
    items = []
    for b in story['beats']:
        if not b.get('say'):
            continue
        items.append({'id': b['id'], 'text': b['say'], 'voice': b.get('voice', story.get('voice', 'fr-FR-RemyMultilingualNeural')),
                      'rate': b.get('rate', story.get('rate', '+8%')), 'pitch': b.get('pitch', story.get('pitch', '+0Hz'))})
    vdir = os.path.join(a.project, 'voices'); os.makedirs(vdir, exist_ok=True)
    mpath = os.path.join(vdir, 'manifest.json')
    old = json.load(open(mpath))['lines'] if os.path.exists(mpath) else {}
    man = asyncio.run(run_lines(items, a.engine, vdir, old))
    keep = {m['file'] for m in man.values()}
    for f in os.listdir(vdir):
        if f.endswith('.mp3') and f not in keep:
            os.remove(os.path.join(vdir, f))
    json.dump({'engine': a.engine, 'lines': man}, open(mpath, 'w'), ensure_ascii=False, indent=1)
    tot = sum(m['dur'] for m in man.values())
    print(f"{len(man)} répliques · {tot:.1f} s de voix → {mpath}")

if __name__ == '__main__':
    main()
