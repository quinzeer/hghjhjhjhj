"""Banque de bruitages synthétisés (originaux, libres de droits) pour le montage « MrBeast ».

Chaque fonction renvoie un clip stéréo float32 à 48 kHz, normalisé autour de -3 dBFS crête.
"""
import numpy as np
from audiolib import (SR, secs, white, pink, filt, sweep_filter, env_ad, exp_env, sine_sweep,
                      saturate, fade, reverb, mono_to_stereo, pan_sweep, db, delay)


def _norm(x, peak_db=-3.0):
    m = np.abs(x).max() + 1e-9
    return (x / m * db(peak_db)).astype(np.float32)


def whoosh(dur=0.5, direction=1, bright=1.0, seed=1):
    n = secs(dur)
    x = pink(n, seed) * 0.6 + white(n, seed + 1) * 0.4
    peak = 0.62
    centers = np.concatenate([np.geomspace(220, 3200 * bright, int(60 * peak)), np.geomspace(3200 * bright, 700, int(60 * (1 - peak)))])
    y = sweep_filter(x, centers, width_oct=1.3)
    t = np.linspace(0, 1, n)
    env = np.where(t < peak, (t / peak) ** 2.2, np.exp(-(t - peak) / (1 - peak) * 4.0))
    y *= env
    st = pan_sweep(y, -0.7 * direction, 0.7 * direction)
    return _norm(fade(reverb(st, 0.6, 0.18), 0.001, 0.05))


def whoosh_big(dur=0.9, direction=1, seed=3):
    w = whoosh(dur, direction, 0.8, seed)
    n = len(w)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (45 + 30 * t / dur) * t) * np.clip(t / (dur * 0.6), 0, 1) ** 2 * np.exp(-np.maximum(0, t - dur * 0.6) * 8)
    return _norm(w + mono_to_stereo(sub.astype(np.float32) * 0.8))


def boom(dur=2.2, seed=5):
    """Impact cinéma : sub qui plonge + transitoire + queue réverbérée."""
    n = secs(dur)
    t = np.arange(n) / SR
    sub = sine_sweep(95, 32, dur, tau=0.18) * np.exp(-t / 0.55)
    body = sine_sweep(160, 55, dur, tau=0.05) * np.exp(-t / 0.12)
    nz = filt(white(n, seed), 'lp', 900, 2) * np.exp(-t / 0.09)
    crack = filt(white(n, seed + 1), 'hp', 2500, 2) * np.exp(-t / 0.012) * 0.5
    x = saturate(sub * 1.0 + body * 0.6 + nz * 0.5 + crack, 1.8)
    return _norm(fade(reverb(mono_to_stereo(x), 2.2, 0.28, damp=3000), 0.0005, 0.3), -1.5)


def hit(dur=0.6, seed=6):
    n = secs(dur)
    t = np.arange(n) / SR
    k = sine_sweep(170, 48, dur, tau=0.035) * np.exp(-t / 0.16)
    click = filt(white(n, seed), 'hp', 3000, 2) * np.exp(-t / 0.004)
    snap = filt(white(n, seed + 2), 'bp', (900, 4000), 2) * np.exp(-t / 0.03) * 0.35
    x = saturate(k + click * 0.6 + snap, 2.2)
    return _norm(fade(reverb(mono_to_stereo(x), 0.9, 0.15), 0.0003, 0.1), -2)


def riser(dur=1.6, seed=7):
    n = secs(dur)
    t = np.linspace(0, 1, n)
    nz = sweep_filter(white(n, seed), np.geomspace(350, 7500, 80), width_oct=1.6)
    tone = sine_sweep(160, 980, dur, 'exp') * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t * dur))
    tone2 = sine_sweep(161.5, 990, dur, 'exp')
    env = t ** 2.6
    x = (nz * 0.9 + (tone + tone2) * 0.18) * env
    st = np.stack([x * (1 - 0.3 * t), x * (0.7 + 0.3 * t)], axis=1).astype(np.float32)
    return _norm(fade(reverb(st, 1.0, 0.25), 0.02, 0.004)[:n])


def pop(freq=880, seed=8):
    dur = 0.12
    n = secs(dur)
    t = np.arange(n) / SR
    x = sine_sweep(freq * 1.7, freq, dur, tau=0.012) * np.exp(-t / 0.028)
    x += filt(white(n, seed), 'hp', 4000, 2) * np.exp(-t / 0.002) * 0.25
    return _norm(fade(reverb(mono_to_stereo(x), 0.4, 0.1), 0.0002, 0.02), -6)


def ding(freq=1318.5, dur=1.6):
    n = secs(dur)
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 0.9), (2.0, 0.45, 0.6), (2.99, 0.28, 0.45), (4.18, 0.16, 0.3), (5.43, 0.09, 0.2)]
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / d) for r, a, d in parts)
    x *= np.minimum(1, t / 0.002)
    return _norm(reverb(mono_to_stereo(x.astype(np.float32)), 1.2, 0.2)[:n], -5)


def cash(seed=9):
    dur = 1.6
    n = secs(dur)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    for i, (t0, band) in enumerate([(0.0, (1500, 5000)), (0.055, (2200, 7000))]):
        k = secs(t0)
        nz = filt(white(n - k, seed + i), 'bp', band, 2) * np.exp(-np.arange(n - k) / SR / 0.018)
        out[k:] += nz * 0.9
    bell_t = t - 0.09
    bell = np.where(bell_t > 0, 1.0, 0.0) * (
        np.sin(2 * np.pi * 2093 * bell_t) * np.exp(-np.maximum(bell_t, 0) / 0.6) +
        0.7 * np.sin(2 * np.pi * 2637 * bell_t) * np.exp(-np.maximum(bell_t, 0) / 0.5) +
        0.3 * np.sin(2 * np.pi * 4186 * bell_t) * np.exp(-np.maximum(bell_t, 0) / 0.3))
    out += bell.astype(np.float32) * 0.6
    r = np.random.default_rng(seed)
    for _ in range(16):
        t0 = 0.12 + r.random() * 0.45
        f = 3500 + r.random() * 4500
        k = secs(t0)
        m = secs(0.06)
        if k + m < n:
            tt = np.arange(m) / SR
            out[k:k + m] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.012) * (0.15 + r.random() * 0.2)).astype(np.float32)
    return _norm(reverb(mono_to_stereo(out), 0.8, 0.15)[:n], -3)


def tick(seed=10):
    n = secs(0.03)
    t = np.arange(n) / SR
    x = filt(white(n, seed), 'bp', (2500, 6000), 2) * np.exp(-t / 0.003)
    x += np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.004) * 0.4
    return _norm(mono_to_stereo(x), -10)


def glitch(dur=0.35, seed=11):
    r = np.random.default_rng(seed)
    n = secs(dur)
    out = np.zeros(n, dtype=np.float32)
    i = 0
    while i < n:
        seg = secs(0.01 + r.random() * 0.04)
        kind = r.integers(0, 3)
        tt = np.arange(min(seg, n - i)) / SR
        if kind == 0:
            f = 100 + r.random() * 1200
            s = np.sign(np.sin(2 * np.pi * f * tt))
        elif kind == 1:
            s = np.round(white(len(tt), seed + i) * 3) / 3
        else:
            s = np.zeros(len(tt))
        out[i:i + len(tt)] = s * (0.4 + r.random() * 0.6)
        i += seg
    out = filt(out, 'lp', 9000)
    return _norm(np.stack([out, np.roll(out, 90)], axis=1), -6)


def shutter(seed=12):
    n = secs(0.25)
    out = np.zeros(n, dtype=np.float32)
    for k, t0 in enumerate([0.0, 0.07]):
        i = secs(t0)
        m = secs(0.03)
        tt = np.arange(m) / SR
        out[i:i + m] += filt(white(m, seed + k), 'bp', (1800, 9000), 2) * np.exp(-tt / 0.006)
    return _norm(reverb(mono_to_stereo(out), 0.3, 0.1)[:n], -5)


def heartbeat():
    n = secs(0.8)
    out = np.zeros(n, dtype=np.float32)
    for t0, a in [(0.0, 1.0), (0.22, 0.7)]:
        i = secs(t0)
        m = secs(0.18)
        tt = np.arange(m) / SR
        out[i:i + m] += sine_sweep(75, 42, 0.18, tau=0.04) * np.exp(-tt / 0.05) * a
    return _norm(mono_to_stereo(saturate(out, 1.5)), -3)


def notif():
    n = secs(0.7)
    out = np.zeros(n, dtype=np.float32)
    for t0, f in [(0.0, 1318.5), (0.11, 1760.0)]:
        i = secs(t0)
        m = n - i
        tt = np.arange(m) / SR
        out[i:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt / 0.18) * np.minimum(1, tt / 0.003)
    return _norm(reverb(mono_to_stereo(out), 0.6, 0.15)[:n], -6)


def swish(seed=13):
    return whoosh(0.28, 1, 1.3, seed) * db(-4)


def stamp(seed=14):
    h = hit(0.5, seed)
    n = len(h)
    t = np.arange(n) / SR
    slap = filt(white(n, seed + 3), 'bp', (400, 2500), 2) * np.exp(-t / 0.05)
    return _norm(h + mono_to_stereo(slap * 0.5), -2)


def bass_drop(dur=2.5):
    n = secs(dur)
    t = np.arange(n) / SR
    x = sine_sweep(110, 36, dur, tau=0.6) * np.exp(-t / 1.2)
    x = saturate(x * 1.4, 2.5)
    return _norm(fade(mono_to_stereo(filt(x, 'lp', 400)), 0.002, 0.4), -2)


BANK = {
    'whoosh': lambda: whoosh(0.5, 1, 1.0, 1),
    'whoosh_l': lambda: whoosh(0.5, -1, 1.0, 2),
    'whoosh_big': lambda: whoosh_big(),
    'boom': lambda: boom(),
    'hit': lambda: hit(),
    'riser': lambda: riser(1.6),
    'riser_long': lambda: riser(3.0, 17),
    'pop': lambda: pop(880),
    'pop_hi': lambda: pop(1320, 18),
    'ding': lambda: ding(),
    'cash': lambda: cash(),
    'tick': lambda: tick(),
    'glitch': lambda: glitch(),
    'shutter': lambda: shutter(),
    'heartbeat': lambda: heartbeat(),
    'notif': lambda: notif(),
    'swish': lambda: swish(),
    'stamp': lambda: stamp(),
    'bass_drop': lambda: bass_drop(),
}

_cache = {}


def get(name):
    if name not in _cache:
        _cache[name] = BANK[name]()
    return _cache[name]


if __name__ == '__main__':
    import os
    import sys
    from audiolib import write_wav
    out = sys.argv[1] if len(sys.argv) > 1 else 'sfx_preview'
    os.makedirs(out, exist_ok=True)
    for k in BANK:
        x = get(k)
        write_wav(os.path.join(out, k + '.wav'), x)
        print(f'{k:12s} {len(x) / SR:5.2f}s  crête {20 * np.log10(np.abs(x).max() + 1e-9):6.1f} dBFS')
