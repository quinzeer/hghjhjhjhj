"""Outils DSP (numpy/scipy) : synthèse, filtres, réverbération, spatialisation, mastering.

Tout est déterministe (graines fixes) : un même épisode produit toujours le même son.
Format interne : float32 stéréo, shape (n, 2), 48 kHz.
"""
import numpy as np
from scipy import signal

SR = 48000


def secs(n):
    return int(round(n * SR))


def rng(seed):
    return np.random.default_rng(seed)


def silence(dur):
    return np.zeros((secs(dur), 2), dtype=np.float32)


def mono_to_stereo(x, pan=0.0):
    """Pan à puissance constante, pan ∈ [-1, 1]."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1).astype(np.float32)


def pan_sweep(x, p0, p1):
    p = np.linspace(p0, p1, len(x))
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1).astype(np.float32)


def white(n, seed=0):
    return rng(seed).standard_normal(n).astype(np.float32)


def pink(n, seed=0):
    w = rng(seed).standard_normal(n)
    f = np.fft.rfft(w)
    k = np.arange(len(f))
    k[0] = 1
    f /= np.sqrt(k)
    x = np.fft.irfft(f, n)
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def sos(kind, freq, order=2, q=None):
    nyq = SR / 2
    if kind == 'lp':
        return signal.butter(order, min(freq / nyq, 0.999), 'low', output='sos')
    if kind == 'hp':
        return signal.butter(order, max(freq / nyq, 1e-4), 'high', output='sos')
    if kind == 'bp':
        lo, hi = freq
        return signal.butter(order, [max(lo / nyq, 1e-4), min(hi / nyq, 0.999)], 'band', output='sos')
    raise ValueError(kind)


def filt(x, kind, freq, order=2):
    return signal.sosfilt(sos(kind, freq, order), x, axis=0).astype(np.float32)


def sweep_filter(x, centers, width_oct=1.0):
    """Filtre passe-bande à fréquence centrale variable dans le temps (masque STFT gaussien)."""
    nper = 1024
    f, t, Z = signal.stft(x, SR, nperseg=nper, noverlap=nper * 3 // 4)
    c = np.interp(t, np.linspace(0, len(x) / SR, len(centers)), centers)
    lf = np.log2(np.maximum(f, 1.0))[:, None]
    lc = np.log2(np.maximum(c, 1.0))[None, :]
    mask = np.exp(-0.5 * ((lf - lc) / (width_oct / 2)) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=nper, noverlap=nper * 3 // 4)
    y = y[: len(x)]
    if len(y) < len(x):
        y = np.pad(y, (0, len(x) - len(y)))
    return y.astype(np.float32)


def env_ad(n, attack, decay_curve=4.0):
    """Enveloppe attaque linéaire (fraction) puis décroissance exponentielle."""
    a = max(1, int(n * attack))
    e = np.ones(n, dtype=np.float32)
    e[:a] = np.linspace(0, 1, a) ** 1.5
    d = n - a
    if d > 0:
        e[a:] = np.exp(-decay_curve * np.linspace(0, 1, d))
    return e


def exp_env(dur, tau):
    t = np.arange(secs(dur)) / SR
    return np.exp(-t / tau).astype(np.float32)


def sine_sweep(f0, f1, dur, curve='exp', tau=None, phase=0.0):
    n = secs(dur)
    t = np.arange(n) / SR
    if tau is not None:
        f = f1 + (f0 - f1) * np.exp(-t / tau)
    elif curve == 'exp':
        f = f0 * (f1 / f0) ** (t / max(dur, 1e-6))
    else:
        f = f0 + (f1 - f0) * t / max(dur, 1e-6)
    ph = phase + 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph).astype(np.float32)


def saturate(x, drive=2.0):
    return (np.tanh(x * drive) / np.tanh(drive)).astype(np.float32)


def fade(x, fin=0.002, fout=0.01):
    n = len(x)
    a, b = min(n, secs(fin)), min(n, secs(fout))
    y = x.copy()
    if a > 0:
        y[:a] *= np.linspace(0, 1, a)[:, None] if y.ndim == 2 else np.linspace(0, 1, a)
    if b > 0:
        y[-b:] *= np.linspace(1, 0, b)[:, None] if y.ndim == 2 else np.linspace(1, 0, b)
    return y


def _ir(dur, decay, seed, damp=6000):
    n = secs(dur)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        nz = white(n, seed + ch)
        nz *= np.exp(-t * (6.9 / decay))
        # amortissement des aigus au fil du temps
        lo = filt(nz, 'lp', damp)
        mix = np.clip(t / decay, 0, 1)
        out.append(nz * (1 - mix) + lo * mix)
    ir = np.stack(out, axis=1)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    return ir.astype(np.float32)


def reverb(x, decay=1.2, mix=0.2, predelay=0.012, seed=7, damp=6000):
    """Réverbération par convolution (réponse impulsionnelle synthétique stéréo décorrélée)."""
    if x.ndim == 1:
        x = mono_to_stereo(x)
    ir = _ir(decay * 1.3, decay, seed, damp)
    pd = secs(predelay)
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x) + len(ir)] for c in range(2)], axis=1)
    wet = np.pad(wet, ((pd, 0), (0, 0)))
    dry = np.pad(x, ((0, len(wet) - len(x)), (0, 0)))
    return (dry * (1 - mix) + wet * mix * 0.9).astype(np.float32)


def delay(x, time=0.25, fb=0.35, mix=0.25, pingpong=True):
    if x.ndim == 1:
        x = mono_to_stereo(x)
    d = secs(time)
    n = len(x) + d * 8
    out = np.zeros((n, 2), dtype=np.float32)
    out[: len(x)] += x
    tap = x.copy()
    for k in range(1, 8):
        tap = tap * fb
        if pingpong:
            tap = tap[:, ::-1]
        out[k * d: k * d + len(tap)] += tap * mix
    return out


def place(buf, clip, t, gain=1.0):
    """Ajoute un clip stéréo dans le buffer à l'instant t (secondes)."""
    if clip.ndim == 1:
        clip = mono_to_stereo(clip)
    i = secs(t)
    if i >= len(buf):
        return
    if i < 0:
        clip = clip[-i:]
        i = 0
    n = min(len(clip), len(buf) - i)
    buf[i: i + n] += clip[:n] * gain


def db(x):
    return 10 ** (x / 20)


def rms_env(x, win=0.05):
    m = x if x.ndim == 1 else np.abs(x).mean(axis=1)
    w = secs(win)
    k = np.ones(w) / w
    return np.sqrt(np.convolve(m ** 2, k, mode='same'))


def duck_gain(voice, depth_db=-10, thresh=0.01, attack=0.03, release=0.3):
    """Courbe de gain « sidechain » : baisse la musique quand la voix parle."""
    e = rms_env(voice, 0.04)
    target = np.where(e > thresh, db(depth_db), 1.0).astype(np.float32)
    g = np.empty_like(target)
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    cur = 1.0
    # lissage asymétrique (boucle vectorisée par blocs pour rester rapide)
    blk = 64
    for i in range(0, len(target), blk):
        tv = target[i: i + blk].min()
        coef = a if tv < cur else r
        cur = tv + (cur - tv) * coef ** blk
        g[i: i + blk] = cur
    return g


def limiter(x, ceiling_db=-1.0, lookahead=0.005, release=0.08):
    """Limiteur à anticipation (évite l'écrêtage inter-échantillons grossier)."""
    ceil = db(ceiling_db)
    peak = np.abs(x).max(axis=1)
    la = secs(lookahead)
    padded = np.pad(peak, (0, la))
    # maximum glissant sur la fenêtre d'anticipation
    from scipy.ndimage import maximum_filter1d
    mx = maximum_filter1d(padded, size=la * 2 + 1)[: len(peak)]
    need = np.minimum(1.0, ceil / np.maximum(mx, 1e-9))
    g = np.empty_like(need)
    cur = 1.0
    r = np.exp(-1 / (release * SR))
    blk = 32
    for i in range(0, len(need), blk):
        nv = need[i: i + blk].min()
        cur = nv if nv < cur else nv + (cur - nv) * r ** blk
        g[i: i + blk] = cur
    return (x * g[:, None]).astype(np.float32)


def loudness_normalize(x, target_lufs=-14.0):
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    l = meter.integrated_loudness(x.astype(np.float64))
    return (x * db(target_lufs - l)).astype(np.float32), l


def write_wav(path, x):
    from scipy.io import wavfile
    y = np.clip(x, -1, 1)
    wavfile.write(path, SR, (y * 32767).astype(np.int16))


def read_wav(path):
    from scipy.io import wavfile
    sr, y = wavfile.read(path)
    y = y.astype(np.float32) / (32768.0 if y.dtype == np.int16 else 1.0)
    if y.ndim == 1:
        y = mono_to_stereo(y)
    if sr != SR:
        y = signal.resample_poly(y, SR, sr, axis=0).astype(np.float32)
    return y
