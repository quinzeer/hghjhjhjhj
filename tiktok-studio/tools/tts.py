"""Voix off TTS (Piper, local) avec horodatage mot à mot via l'alignement des phonèmes.

- Le texte affiché (sous-titres) et le texte prononcé peuvent différer par un lexique
  (ex. « Nasdas » prononcé « Nasdasse ») sans casser l'alignement : 1 mot affiché = 1 mot dit.
- Retourne l'audio 48 kHz mono + la liste des mots {text, start, end} en secondes.
"""
import re
import numpy as np
from scipy import signal

from audiolib import SR, filt, saturate, db

_VOICES = {}
PUNCT = set(',.;:!?…-–—«»"\'()')
SPECIAL = {'^', '$', '_'}


def load_voice(model_path):
    from piper import PiperVoice
    if model_path not in _VOICES:
        _VOICES[model_path] = PiperVoice.load(model_path, include_alignments=True)
    return _VOICES[model_path]


def _strip(tok):
    m = re.match(r'^([«"\'(]*)(.*?)([»"\')\.,;:!?…]*)$', tok)
    return m.group(1), m.group(2), m.group(3)


def apply_lexicon(tokens, lexicon):
    out = []
    for tok in tokens:
        pre, core, post = _strip(tok)
        rep = lexicon.get(core) or lexicon.get(core.lower())
        out.append(pre + (rep if rep else core) + post)
    return out


def _phoneme_words(voice, text):
    ph = voice.phonemize(text)
    s = ' '.join(''.join(p) for p in ph)
    return [w for w in s.split(' ') if any(c not in PUNCT for c in w)]


def synth(model_path, text, length_scale=0.88, noise_scale=0.62, noise_w=0.75, speaker=None, lexicon=None,
          sentence_gap=0.07):
    from piper import SynthesisConfig
    voice = load_voice(model_path)
    lexicon = lexicon or {}
    tokens = []
    # « 446_773 » : affiché « 446 773 » (espace fine), prononcé « 446773 » (un seul nombre).
    for tok in text.split():
        # « ? », « ! », « : » isolés (typographie française) → collés au mot précédent.
        if tokens and all(c in PUNCT for c in tok):
            tokens[-1] = tokens[-1] + ' ' + tok
        else:
            tokens.append(tok)
    tts_tokens = apply_lexicon([t.replace('_', '') for t in tokens], lexicon)
    tokens = [t.replace('_', '\u00a0') for t in tokens]
    cfg = SynthesisConfig(length_scale=length_scale, noise_scale=noise_scale, noise_w_scale=noise_w,
                          speaker_id=speaker, normalize_audio=True)
    audio, pw = [], []   # pw : mots phonétiques (start, end) en échantillons @ sr natif
    offset = 0
    sr_in = voice.config.sample_rate
    gap = int(sentence_gap * sr_in)
    for ch in voice.synthesize(' '.join(tts_tokens), cfg, include_alignments=True):
        a = ch.audio_float_array.astype(np.float32)
        cur = offset
        wstart = None
        for al in ch.phoneme_alignments or []:
            p = al.phoneme
            n = int(al.num_samples)
            if p == ' ' or p in SPECIAL or p in PUNCT:
                if wstart is not None:
                    pw.append((wstart, cur))
                    wstart = None
            else:
                if wstart is None:
                    wstart = cur
            cur += n
        if wstart is not None:
            pw.append((wstart, cur))
        audio.append(a)
        audio.append(np.zeros(gap, dtype=np.float32))
        offset += len(a) + gap
    y = np.concatenate(audio) if audio else np.zeros(1, dtype=np.float32)

    # Association mots affichés ↔ mots phonétiques.
    counts = [max(1, len(_phoneme_words(voice, t))) for t in tts_tokens]
    words = []
    if sum(counts) == len(pw):
        k = 0
        for tok, c in zip(tokens, counts):
            s, e = pw[k][0], pw[k + c - 1][1]
            words.append({'text': tok, 'start': s / sr_in, 'end': e / sr_in})
            k += c
    else:
        # Repli : répartition proportionnelle au nombre de phonèmes, sur l'étendue parlée.
        lens = [max(1, sum(len(w) for w in _phoneme_words(voice, t))) for t in tts_tokens]
        t0 = pw[0][0] if pw else 0
        t1 = pw[-1][1] if pw else len(y)
        tot = sum(lens)
        acc = t0
        for tok, l in zip(tokens, lens):
            d = (t1 - t0) * l / tot
            words.append({'text': tok, 'start': acc / sr_in, 'end': (acc + d) / sr_in})
            acc += d
        print(f'  [tts] alignement approché ({sum(counts)} vs {len(pw)} mots) : {text[:60]}…')

    y48 = signal.resample_poly(y, SR, sr_in).astype(np.float32)
    return y48, words


def voice_chain(x):
    """Traitement « voix radio » : coupe-bas, présence, compression, légère saturation."""
    y = filt(x, 'hp', 85, 2)
    # bosse de présence 2,5–6 kHz (+3 dB environ)
    pres = filt(y, 'bp', (2500, 6000), 2)
    y = y + pres * 0.45
    # atténuation légère des bas-médiums boueux
    mud = filt(y, 'bp', (220, 450), 2)
    y = y - mud * 0.25
    # compresseur simple (enveloppe RMS 10 ms, ratio 3.5:1 au-dessus de -20 dBFS)
    env = np.sqrt(np.convolve(y ** 2, np.ones(480) / 480, mode='same')) + 1e-9
    thr = db(-20)
    gain = np.where(env > thr, (thr / env) ** (1 - 1 / 3.5), 1.0)
    gain = np.convolve(gain, np.ones(240) / 240, mode='same')
    y = y * gain
    y = saturate(y * 1.3, 1.2)
    y = y / (np.abs(y).max() + 1e-9) * db(-2)
    return y.astype(np.float32)
