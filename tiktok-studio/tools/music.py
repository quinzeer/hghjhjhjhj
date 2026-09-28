"""Instrumental original (trap/drill sombre) généré procéduralement, arrangé sur la timeline.

Pensé pour les haut-parleurs de téléphone : la basse 808 est saturée (harmoniques audibles
même quand le sub ne passe pas). Arrangement piloté par des marqueurs :
  {'t': s, 'type': 'drop'|'build'|'break'|'stop'}
Retourne un stéréo float32 48 kHz + la grille temporelle (pour caler les coupes sur le tempo).
"""
import numpy as np
from audiolib import (SR, secs, white, filt, saturate, reverb, delay, mono_to_stereo, db, sine_sweep)

NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(name):
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + (o - 4) * 12 - 9) / 12)


# ---------------- Instruments ----------------
def kick(vel=1.0):
    d = 0.35
    t = np.arange(secs(d)) / SR
    x = sine_sweep(150, 50, d, tau=0.03) * np.exp(-t / 0.12)
    x += filt(white(len(t), 3), 'hp', 3000) * np.exp(-t / 0.003) * 0.3
    return saturate(x * 1.5, 1.8) * vel


def b808(freq, dur, vel=1.0, glide_from=None):
    t = np.arange(secs(dur)) / SR
    f = np.full(len(t), freq)
    if glide_from:
        f = freq + (glide_from - freq) * np.exp(-t / 0.06)
    f = f * (1 + 0.9 * np.exp(-t / 0.012))  # « punch » d'attaque
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.minimum(1, t / 0.003) * np.exp(-t / max(0.25, dur * 0.8))
    x = saturate(x * 2.8, 2.6)          # harmoniques → audible sur téléphone
    x = filt(x, 'lp', 1800)
    rel = min(len(x), secs(0.03))
    x[-rel:] *= np.linspace(1, 0, rel)
    return x * vel


def clap(vel=1.0, seed=21):
    d = 0.45
    n = secs(d)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float32)
    for k, o in enumerate([0.0, 0.011, 0.022, 0.034]):
        i = secs(o)
        nz = filt(white(n - i, seed + k), 'bp', (900, 5000), 2)
        x[i:] += nz * np.exp(-np.arange(n - i) / SR / (0.012 if k < 3 else 0.09))
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.4
    return (x + body) * vel


def hat(vel=1.0, open_=False, seed=31):
    d = 0.35 if open_ else 0.06
    n = secs(d)
    t = np.arange(n) / SR
    x = filt(white(n, seed), 'hp', 7500, 4) * np.exp(-t / (0.09 if open_ else 0.014))
    # métal : quelques partiels carrés inharmoniques
    for f in (5270, 7040, 8450):
        x += np.sign(np.sin(2 * np.pi * f * t)) * 0.05 * np.exp(-t / (0.06 if open_ else 0.01))
    return filt(x, 'hp', 6000) * vel


def bell(freq, dur, vel=1.0):
    """Cloche FM sombre (porteuse + modulante 3.5×, indice décroissant)."""
    t = np.arange(secs(dur)) / SR
    idx = 2.4 * np.exp(-t / 0.35)
    mod = np.sin(2 * np.pi * freq * 3.5 * t) * idx
    x = np.sin(2 * np.pi * freq * t + mod) * np.exp(-t / 0.7)
    x += 0.25 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / 0.3)
    x *= np.minimum(1, t / 0.002)
    return x * vel


def pad_chord(freqs, dur, cutoff=1400):
    t = np.arange(secs(dur)) / SR
    x = np.zeros(len(t))
    for i, f in enumerate(freqs):
        for det in (-0.08, 0.0, 0.08):
            ff = f * 2 ** (det / 12)
            ph = (ff * t + i * 0.13 + det) % 1.0
            x += (2 * ph - 1)  # dent de scie
    env = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.3)
    x = filt(x * env / (len(freqs) * 3), 'lp', cutoff, 2)
    return x


# ---------------- Arrangement ----------------
CHORDS = [  # Fa mineur : i – VI – III – VII
    (['F3', 'Ab3', 'C4'], 'F2'),
    (['Db3', 'F3', 'Ab3'], 'Db2'),
    (['Ab2', 'C3', 'Eb3'], 'Ab1'),
    (['Eb3', 'G3', 'Bb3'], 'Eb2'),
]
MOTIF = [('F5', 0, 2), ('Ab5', 3, 1), ('C6', 6, 2), ('Eb6', 8, 2), ('C6', 11, 1), ('Ab5', 12, 2), ('G5', 14, 2)]


def section_at(t, markers):
    cur = 'drop'
    for m in markers:
        if m['t'] <= t:
            cur = m['type']
    return cur


def generate(duration, markers, bpm=140, seed=1):
    beat = 60.0 / bpm
    step = beat / 4
    n = secs(duration + 2)
    drums = np.zeros((n, 2), dtype=np.float32)
    bass = np.zeros((n, 2), dtype=np.float32)
    mel = np.zeros((n, 2), dtype=np.float32)
    pad = np.zeros((n, 2), dtype=np.float32)
    rng = np.random.default_rng(seed)
    K = kick(); C = clap(); H = hat(); HO = hat(open_=True)

    def put(buf, clip, t, gain=1.0, pan=0.0):
        if clip.ndim == 1:
            clip = mono_to_stereo(clip.astype(np.float32), pan)
        i = secs(t)
        if i >= len(buf):
            return
        m = min(len(clip), len(buf) - i)
        buf[i:i + m] += clip[:m] * gain

    bars = int(np.ceil(duration / (beat * 4))) + 1
    for b in range(bars):
        t0 = b * beat * 4
        chord, root = CHORDS[b % 4]
        sec = section_at(t0 + 0.01, markers)
        # Pad (toujours présent sauf « stop »).
        put(pad, pad_chord([hz(x) for x in chord], beat * 4, 1100 if sec == 'break' else 1600), t0, 0.5)
        for s in range(16):
            ts = t0 + s * step
            sec = section_at(ts + 0.001, markers)
            if any(m['type'] == 'stop' and m['t'] <= ts < m['t'] + m.get('len', 0.4) for m in markers):
                continue
            full = sec == 'drop'
            # Kick / 808
            if full and s in ((0, 7, 10) if b % 2 == 0 else (0, 3, 10, 13)):
                put(drums, K, ts, 0.55)
                nxt = 3 if s in (0, 7) else 2
                glide = hz(root) * 2 if (s == 10 and b % 4 == 3) else None
                put(bass, b808(hz(root), step * nxt * 1.6, 1.0, glide), ts, 0.62)
            # Clap
            if (full or sec == 'break') and s == 8:
                put(drums, C, ts, 0.5 if full else 0.3)
            # Roulement de caisse claire en montée
            if sec == 'build':
                mt = [m for m in markers if m['type'] == 'build' and m['t'] <= ts]
                start = mt[-1]['t'] if mt else ts
                prog = min(1.0, (ts - start) / 2.0)
                div = 1 if prog < 0.34 else 2 if prog < 0.67 else 4
                for k in range(div):
                    put(drums, C, ts + k * step / div, 0.12 + 0.3 * prog)
            # Charleston + roulements « trap »
            if sec != 'stop':
                if s % 2 == 0:
                    put(drums, H, ts, 0.16 + 0.06 * (s % 4 == 0), 0.25)
                if full and b % 4 == 3 and s >= 12:
                    for k in range(3):
                        put(drums, H, ts + k * step / 3, 0.1 + 0.03 * k, 0.25)
                if full and s == 14 and b % 2 == 1:
                    put(drums, HO, ts, 0.12, -0.3)
        # Mélodie (2 mesures sur 4, pour respirer sous la voix).
        if section_at(t0 + 0.01, markers) in ('drop', 'break') and b % 4 in (0, 2):
            for note, st, ln in MOTIF:
                put(mel, bell(hz(note) / 2, step * ln * 3, 0.9), t0 + st * step, 0.2, (st % 3 - 1) * 0.35)

    mel = reverb(mel, 1.6, 0.3)[:n]
    mel = mel + delay(mel, beat * 0.75, 0.3, 0.18)[:n]
    pad = reverb(pad, 2.4, 0.4)[:n]
    drums = drums + reverb(drums, 0.8, 0.12)[:n] * 0.3
    bass = filt(bass, 'hp', 28)
    mix = drums * 1.0 + bass * 0.95 + mel * 1.0 + pad * 0.55
    mix = saturate(mix * 0.9, 1.1)
    mix = mix[:secs(duration)]
    mix /= np.abs(mix).max() + 1e-9
    grid = {'bpm': bpm, 'beat': beat, 'step': step}
    return mix.astype(np.float32) * db(-3), grid
