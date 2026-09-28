// Mixeur audio en JavaScript pur (aucune Web Audio API) : identique dans Node et dans le navigateur.
// Bruitages synthétisés, musique procédurale par préréglage, voix off normalisée, ducking, réverbération, limiteur.
// Entrée : la timeline (voix + beats), une liste d'événements sonores, les PCM des voix. Sortie : [L, R] à 48 kHz.
export const SR = 48000;
const TAU = Math.PI * 2;
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);

// ---------- filtres ----------
function biquad(type, f, q = 0.707, gainDb = 0) {
  const w = (TAU * f) / SR, cs = Math.cos(w), sn = Math.sin(w), al = sn / (2 * q), A = Math.pow(10, gainDb / 40);
  let b0, b1, b2, a0, a1, a2;
  if (type === 'lp') { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = b0; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'hp') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = b0; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'bp') { b0 = al; b1 = 0; b2 = -al; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else { b0 = 1 + al * A; b1 = -2 * cs; b2 = 1 - al * A; a0 = 1 + al / A; a1 = -2 * cs; a2 = 1 - al / A; }
  return { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: a1 / a0, a2: a2 / a0 };
}
function filt(x, c, out = x) {
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let i = 0; i < x.length; i++) { const y = c.b0 * x[i] + c.b1 * x1 + c.b2 * x2 - c.a1 * y1 - c.a2 * y2; x2 = x1; x1 = x[i]; y2 = y1; y1 = y; out[i] = y; }
  return out;
}
// filtre passe-bande à fréquence glissante (recalcul tous les 64 échantillons)
function sweepBP(x, f0, f1, q) {
  const out = new Float32Array(x.length);
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0, c;
  for (let i = 0; i < x.length; i++) {
    if (i % 64 === 0) c = biquad('bp', f0 * Math.pow(f1 / f0, i / x.length), q);
    const y = c.b0 * x[i] + c.b1 * x1 + c.b2 * x2 - c.a1 * y1 - c.a2 * y2; x2 = x1; x1 = x[i]; y2 = y1; y1 = y; out[i] = y;
  }
  return out;
}
function noise(n, seed) { const r = rng(seed), o = new Float32Array(n); for (let i = 0; i < n; i++) o[i] = r() * 2 - 1; return o; }
function norm(b, peak = 0.9) { let m = 0; for (const x of b) m = Math.max(m, Math.abs(x)); if (m > 0) for (let i = 0; i < b.length; i++) b[i] *= peak / m; return b; }

// ---------- échantillons synthétisés ----------
function marbleClick(variant) {
  // choc bille contre bille : partiels inharmoniques très amortis + transitoire
  const n = Math.round(0.09 * SR), o = new Float32Array(n), r = rng(100 + variant);
  const f0 = 2300 + variant * 170;
  const parts = [[f0, 1, 0.018], [f0 * 2.71, 0.55, 0.011], [f0 * 5.2, 0.3, 0.006], [f0 * 0.52, 0.35, 0.03]];
  for (let i = 0; i < n; i++) {
    const t = i / SR; let s = 0;
    for (const [f, a, tau] of parts) s += a * Math.sin(TAU * f * t + variant) * Math.exp(-t / tau);
    if (i < 60) s += (r() * 2 - 1) * (1 - i / 60) * 0.8;
    o[i] = s;
  }
  return norm(o, 0.8);
}
function thud(f0 = 95, dur = 0.35, seed = 1) {
  const n = Math.round(dur * SR), o = new Float32Array(n), r = rng(seed);
  let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / SR, f = f0 * (0.55 + 0.45 * Math.exp(-t / 0.04)); ph += (TAU * f) / SR; o[i] = Math.sin(ph) * Math.exp(-t / (dur * 0.3)) + (i < 200 ? (r() * 2 - 1) * (1 - i / 200) * 0.5 : 0); }
  return norm(o, 0.9);
}
function knock(seed) {
  const n = Math.round(0.12 * SR), nz = noise(n, seed), o = filt(nz, biquad('bp', 1100, 2.5), new Float32Array(n));
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] = o[i] * Math.exp(-t / 0.018) * 3 + Math.sin(TAU * 420 * t) * Math.exp(-t / 0.03) * 0.6; }
  return norm(o, 0.8);
}
function clang(seed) {
  const n = Math.round(0.9 * SR), o = new Float32Array(n);
  const parts = [[523, 1, 0.35], [1187, 0.6, 0.22], [1873, 0.45, 0.15], [2690, 0.3, 0.1], [3480, 0.2, 0.07]];
  for (let i = 0; i < n; i++) { const t = i / SR; let s = 0; for (const [f, a, tau] of parts) s += a * Math.sin(TAU * f * (1 + seed * 0.004) * t) * Math.exp(-t / tau); o[i] = s + Math.sin(TAU * 70 * t) * Math.exp(-t / 0.06) * 0.8; }
  return norm(o, 0.85);
}
function beeps() {
  const n = Math.round(0.32 * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; const on = (t < 0.08) || (t > 0.13 && t < 0.21); o[i] = on ? Math.sign(Math.sin(TAU * 1480 * t)) * 0.35 + Math.sin(TAU * 2960 * t) * 0.2 : 0; }
  return filt(o, biquad('lp', 5000));
}
function hydraulic(seed) {
  const n = Math.round(0.35 * SR), o = sweepBP(noise(n, seed), 2400, 380, 1.2);
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] = o[i] * Math.exp(-t / 0.12) * 2.2; }
  const k = thud(70, 0.25, seed); for (let i = 0; i < k.length && i < n; i++) o[i] += k[i] * 0.5;
  return norm(o, 0.8);
}
function siren() {
  const n = Math.round(1.1 * SR), o = new Float32Array(n); let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / SR, f = 650 + 300 * (0.5 - 0.5 * Math.cos(TAU * t / 0.55)); ph += (TAU * f) / SR; o[i] = (Math.sin(ph) + 0.3 * Math.sin(2 * ph)) * Math.min(1, t / 0.03, (1.1 - t) / 0.1); }
  return norm(o, 0.6);
}
function crumble(dur, seed) {
  const n = Math.round((dur + 0.8) * SR), r = rng(seed), o = new Float32Array(n);
  for (let g = 0; g < dur * 60; g++) {
    const at = Math.floor(r() * dur * SR), len = Math.floor((0.02 + r() * 0.08) * SR), a = 0.3 + r() * 0.7;
    for (let i = 0; i < len && at + i < n; i++) o[at + i] += (r() * 2 - 1) * a * Math.exp(-i / (len * 0.3));
  }
  filt(o, biquad('lp', 1400));
  const rum = thud(40, dur + 0.8, seed); for (let i = 0; i < n && i < rum.length; i++) o[i] += rum[i] * 0.6;
  return norm(o, 0.85);
}
function whoosh(dur, up, seed) {
  const n = Math.round(dur * SR), o = sweepBP(noise(n, seed), up ? 300 : 3500, up ? 4000 : 250, 1.6);
  for (let i = 0; i < n; i++) { const t = i / n; o[i] *= Math.sin(Math.PI * Math.pow(t, up ? 1.6 : 0.6)) * 3; }
  return norm(o, 0.8);
}
function ding() {
  const n = Math.round(0.6 * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] = (Math.sin(TAU * 1318 * t) + 0.5 * Math.sin(TAU * 1976 * t) + 0.25 * Math.sin(TAU * 2637 * t)) * Math.exp(-t / 0.16); }
  return norm(o, 0.6);
}
function impact(seed) {
  const n = Math.round(2.2 * SR), o = new Float32Array(n), cr = filt(noise(n, seed), biquad('hp', 2500), new Float32Array(n));
  let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / SR, f = 32 + 55 * Math.exp(-t / 0.18); ph += (TAU * f) / SR; o[i] = Math.tanh(1.6 * Math.sin(ph) * Math.exp(-t / 0.7)) + cr[i] * Math.exp(-t / 0.55) * 0.45; }
  return norm(o, 0.95);
}
function riser(dur, seed) {
  const n = Math.round(dur * SR), o = sweepBP(noise(n, seed), 250, 7000, 2.2);
  let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / n; ph += (TAU * (200 + 900 * t * t)) / SR; o[i] = (o[i] * 2.2 + Math.sin(ph) * 0.25) * t * t; }
  return norm(o, 0.7);
}
function rewind() {
  const n = Math.round(0.55 * SR), o = new Float32Array(n), nz = filt(noise(n, 77), biquad('bp', 1800, 0.8), new Float32Array(n)); let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / SR, f = 1600 * Math.exp(-t / 0.15) + 120; ph += (TAU * f) / SR; o[i] = (Math.sin(ph) * 0.6 + nz[i] * 1.5 * (0.5 + 0.5 * Math.sin(TAU * 38 * t))) * Math.min(1, (0.55 - t) / 0.1); }
  return norm(o, 0.8);
}
function heartbeat() {
  const n = Math.round(0.5 * SR), o = new Float32Array(n);
  for (const [at, a] of [[0, 1], [0.17, 0.7]]) for (let i = 0; i < 0.2 * SR; i++) { const t = i / SR, j = Math.round(at * SR) + i; o[j] += a * Math.sin(TAU * (48 + 20 * Math.exp(-t / 0.02)) * t) * Math.exp(-t / 0.06); }
  return norm(o, 0.9);
}
function applause(dur, seed) {
  const n = Math.round(dur * SR), r = rng(seed), o = new Float32Array(n);
  const claps = Math.floor(dur * 420);
  for (let k = 0; k < claps; k++) {
    const at = Math.floor(r() * n), len = Math.floor((0.006 + r() * 0.012) * SR), a = 0.2 + r() * 0.8;
    for (let i = 0; i < len && at + i < n; i++) o[at + i] += (r() * 2 - 1) * a * Math.exp(-i / (len * 0.25));
  }
  filt(o, biquad('bp', 2200, 0.6));
  for (let i = 0; i < n; i++) { const t = i / n; o[i] *= Math.min(1, t / 0.04) * (1 - t * 0.6); }
  return norm(o, 0.8);
}
function whistle(seed) {
  const r = rng(seed), n = Math.round(0.9 * SR), o = new Float32Array(n); let ph = 0; const f0 = 2100 + r() * 700;
  for (let i = 0; i < n; i++) { const t = i / SR, f = f0 * (1 + 0.25 * Math.sin(Math.PI * t / 0.9)) ; ph += (TAU * f) / SR; o[i] = Math.sin(ph) * Math.min(1, t / 0.05, (0.9 - t) / 0.1) * 0.5; }
  return o;
}

// ---------- instruments de la musique ----------
function kick808() {
  const n = Math.round(0.9 * SR), o = new Float32Array(n); let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / SR, f = 44 + 120 * Math.exp(-t / 0.03); ph += (TAU * f) / SR; o[i] = Math.tanh(2.2 * Math.sin(ph) * Math.exp(-t / 0.42)) + (i < 90 ? (1 - i / 90) * 0.6 : 0); }
  return norm(o, 0.95);
}
function clap() {
  const n = Math.round(0.35 * SR), nz = noise(n, 5), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; let e = Math.exp(-t / 0.09); for (const b of [0, 0.011, 0.022]) if (t >= b && t < b + 0.01) e = Math.max(e, 1 - (t - b) / 0.01); o[i] = nz[i] * e; }
  filt(o, biquad('bp', 1500, 0.9)); filt(o, biquad('hp', 450));
  return norm(o, 0.8);
}
function hat(open) {
  const n = Math.round((open ? 0.25 : 0.06) * SR), o = filt(noise(n, open ? 9 : 8), biquad('hp', 7500), new Float32Array(n));
  for (let i = 0; i < n; i++) o[i] *= Math.exp(-i / SR / (open ? 0.08 : 0.018));
  return norm(o, 0.5);
}
function bellNote(m, dur = 0.9) {
  const f = mtof(m), n = Math.round(dur * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] = Math.sin(TAU * f * t + 1.4 * Math.exp(-t / 0.18) * Math.sin(TAU * 3.5 * f * t)) * Math.exp(-t / 0.32) * Math.min(1, t / 0.003); }
  return norm(o, 0.5);
}
function subNote(m, dur) {
  const f = mtof(m), n = Math.round(dur * SR), o = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] = Math.tanh(1.8 * Math.sin(TAU * f * t)) * Math.min(1, t / 0.01, (dur - t) / 0.05) * 0.6; }
  return o;
}
function padChord(ms, dur, seed) {
  const n = Math.round(dur * SR), o = new Float32Array(n), r = rng(seed);
  for (const m of ms) for (const det of [-0.12, 0, 0.11]) {
    const f = mtof(m + det); let ph = r();
    for (let i = 0; i < n; i++) { ph += f / SR; ph -= Math.floor(ph); o[i] += (2 * ph - 1) * 0.12; }
  }
  filt(o, biquad('lp', 1300, 0.6));
  for (let i = 0; i < n; i++) { const t = i / SR; o[i] *= Math.min(1, t / 0.35, (dur - t) / 0.4); }
  return o;
}

// ---------- mixage ----------
function add(bus, buf, t, gain, pan = 0, rate = 1) {
  if (!buf || gain <= 0) return;
  const L = bus[0], R = bus[1];
  const start = Math.round(t * SR);
  const gl = gain * Math.cos(((clamp(pan, -1, 1) + 1) * Math.PI) / 4), gr = gain * Math.sin(((clamp(pan, -1, 1) + 1) * Math.PI) / 4);
  const n = Math.floor((buf.length - 1) / rate);
  for (let i = 0; i < n; i++) {
    const j = start + i;
    if (j < 0) continue;
    if (j >= L.length) break;
    const x = i * rate, k = x | 0, f = x - k;
    const s = buf[k] + (buf[k + 1] - buf[k]) * f;
    L[j] += s * gl; R[j] += s * gr;
  }
}
function reverb(inL, inR, wet = 0.3, room = 0.84, damp = 0.35) {
  // Freeverb simplifié : 8 filtres en peigne + 4 passe-tout par canal
  const combs = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617].map((d) => Math.round((d * SR) / 44100));
  const alls = [556, 441, 341, 225].map((d) => Math.round((d * SR) / 44100));
  const run = (x, spread) => {
    const out = new Float32Array(x.length);
    const cb = combs.map((d) => ({ b: new Float32Array(d + spread), i: 0, s: 0 }));
    const ab = alls.map((d) => ({ b: new Float32Array(d + spread), i: 0 }));
    for (let n = 0; n < x.length; n++) {
      const inp = x[n] * 0.015; let acc = 0;
      for (const c of cb) { const y = c.b[c.i]; c.s = y * (1 - damp) + c.s * damp; c.b[c.i] = inp + c.s * room; c.i = (c.i + 1) % c.b.length; acc += y; }
      for (const a of ab) { const y = a.b[a.i]; const o = -acc + y; a.b[a.i] = acc + y * 0.5; a.i = (a.i + 1) % a.b.length; acc = o; }
      out[n] = acc * wet;
    }
    return out;
  };
  return [run(inL, 0), run(inR, 23)];
}

// ---------- composition ----------
function rmsGain(b, target) {
  let e = 0, n = 0;
  for (let i = 0; i < b.length; i++) if (Math.abs(b[i]) > 0.01) { e += b[i] * b[i]; n++; }
  const r = Math.sqrt(e / Math.max(1, n));
  return r > 0 ? Math.min(8, target / r) : 1;
}

function limiter(ch, ceil) {
  const N = ch[0].length;
  const peak = new Float32Array(N);
  for (let i = 0; i < N; i++) peak[i] = Math.max(Math.abs(ch[0][i]), Math.abs(ch[1][i]));
  // maximum glissant sur la fenêtre d'anticipation
  const need = new Float32Array(N);
  for (let i = N - 1; i >= 0; i--) { let m = peak[i]; if (i + 1 < N) m = Math.max(m, need[i + 1] * 0.9995); need[i] = m; }
  let g = 1;
  for (let i = 0; i < N; i++) {
    const p = need[i];
    const tg = p > ceil ? ceil / p : 1;
    g = tg < g ? tg : g + (tg - g) * 0.0004;
    ch[0][i] = Math.tanh((ch[0][i] * g) / ceil * 1.05) * ceil;
    ch[1][i] = Math.tanh((ch[1][i] * g) / ceil * 1.05) * ceil;
  }
}

export function encodeWav(ch) {
  const n = ch[0].length, buf = new ArrayBuffer(44 + n * 4), dv = new DataView(buf);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); dv.setUint32(4, 36 + n * 4, true); w(8, 'WAVE'); w(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 2, true);
  dv.setUint32(24, SR, true); dv.setUint32(28, SR * 4, true); dv.setUint16(32, 4, true); dv.setUint16(34, 16, true); w(36, 'data'); dv.setUint32(40, n * 4, true);
  let o = 44;
  for (let i = 0; i < n; i++) for (let c = 0; c < 2; c++) { const s = clamp(ch[c][i], -1, 1); dv.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true); o += 2; }
  return new Uint8Array(buf);
}

// ---------- bibliothèque de bruitages (clé → fabrique d'échantillon mono) ----------
function pop() { const n = Math.round(0.12 * SR), o = new Float32Array(n); for (let i = 0; i < n; i++) { const t = i / SR; o[i] = Math.sin(TAU * (900 - 500 * t / 0.12) * t) * Math.exp(-t / 0.03); } return norm(o, 0.6); }
function tick() { const n = Math.round(0.05 * SR), o = new Float32Array(n); for (let i = 0; i < n; i++) { const t = i / SR; o[i] = (Math.sin(TAU * 3200 * t) + 0.5 * Math.sin(TAU * 5100 * t)) * Math.exp(-t / 0.006); } return norm(o, 0.5); }
function coin() { const n = Math.round(0.5 * SR), o = new Float32Array(n); for (let i = 0; i < n; i++) { const t = i / SR, f = t < 0.08 ? 1976 : 2637; o[i] = (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2 * f * t)) * Math.exp(-(t < 0.08 ? t : t - 0.08) / 0.12); } return norm(o, 0.5); }
function swell(dur, seed) { const n = Math.round(dur * SR), o = filt(noise(n, seed), biquad('lp', 900, 0.7), new Float32Array(n)); let ph = 0; for (let i = 0; i < n; i++) { const t = i / n; ph += (TAU * 55) / SR; o[i] = (o[i] * 1.5 + Math.sin(ph) * 0.6) * Math.sin(Math.PI * t); } return norm(o, 0.7); }
const LIB = {};
const make = {
  whoosh: () => whoosh(0.32, true, 9), whooshDown: () => whoosh(0.45, false, 8), impact: () => impact(10), boom: () => thud(52, 0.9, 7),
  ding: () => ding(), click: () => marbleClick(3), knock: () => knock(2), clang: () => clang(3), riser: () => riser(1.3, 11),
  alarm: () => beeps(), siren: () => siren(), heartbeat: () => heartbeat(), applause: () => applause(3.5, 5), rewind: () => rewind(),
  pop: () => pop(), tick: () => tick(), coin: () => coin(), swell: () => swell(2.2, 4), land: () => thud(95, 0.35, 3), whistle: () => whistle(7),
};
export const SFX_TYPES = Object.keys(make);
const sample = (k) => { if (!make[k]) return null; if (!LIB[k]) LIB[k] = make[k](); return LIB[k]; };

// ---------- musique procédurale ----------
export const MUSIC = {
  tension: { bpm: 140, prog: [[48, 51, 55], [44, 48, 51], [51, 55, 58], [46, 50, 53]], roots: [36, 32, 39, 34], kick: 'trap', bells: true },
  epic: { bpm: 90, prog: [[45, 48, 52], [41, 45, 48], [48, 52, 55], [43, 47, 50]], roots: [33, 29, 36, 31], kick: 'four', bells: false },
  chill: { bpm: 84, prog: [[53, 57, 60, 64], [50, 53, 57, 60], [55, 58, 62, 65], [48, 52, 55, 59]], roots: [41, 38, 43, 36], kick: 'soft', bells: true },
  playful: { bpm: 118, prog: [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]], roots: [48, 45, 41, 43], kick: 'four', bells: true },
  mystery: { bpm: 76, prog: [[50, 53, 57], [46, 50, 53], [48, 51, 55], [45, 49, 52]], roots: [38, 34, 36, 33], kick: 'soft', bells: true },
};

function composeMusic(T, preset, mus) {
  const P = MUSIC[preset];
  if (!P) return;
  const beat = 60 / P.bpm, dur = T.duration;
  const K = kick808(), C = clap(), HH = hat(false), OH = hat(true);
  const bells = new Map(), bell = (m) => { if (!bells.has(m)) bells.set(m, bellNote(m)); return bells.get(m); };
  const arp = [0, 1, 2, 1, 2, 0, 2, 1];
  const energy = (v) => T.energyAt(v);
  for (let b = 0; b * beat < dur; b++) {
    const v = b * beat, e = energy(v);
    if (T.musicMutedAt(v)) continue;
    const bar = Math.floor(b / 4), inBar = b % 4, chord = Math.floor(bar / 2) % 4;
    const ch = P.prog[chord], root = P.roots[chord];
    if (inBar === 0 && bar % 2 === 0) { const len = Math.min(8 * beat, dur - v); if (len > 0.5) add(mus, padChord(ch.map((m) => m + 12), len, b), v, 0.35 + 0.35 * e, 0); }
    if (e >= 0.3) {
      if (P.kick === 'trap') { if (inBar === 0 || inBar === 2) add(mus, K, v, 0.8, 0); if (inBar === 1 && (bar % 2 || e > 0.8)) add(mus, K, v + beat / 2, 0.65, 0); }
      else if (P.kick === 'four') add(mus, K, v, inBar === 0 ? 0.85 : 0.65, 0);
      else if (inBar === 0 || (inBar === 2 && bar % 2)) add(mus, K, v, 0.5, 0);
      if (inBar % 2 === 0) add(mus, subNote(root, beat * 1.8), v, 0.38, 0);
    }
    if (e >= 0.45 && (inBar === 1 || inBar === 3)) add(mus, C, v, P.kick === 'soft' ? 0.3 : 0.5, 0.05);
    if (e >= 0.55) { const div = e > 0.85 ? 4 : 2; for (let k = 0; k < div; k++) add(mus, HH, v + (k * beat) / div, k ? 0.16 : 0.25, 0.3); if (inBar === 2 && bar % 2) add(mus, OH, v + beat / 2, 0.18, -0.3); }
    if (P.bells && e >= 0.6) for (let k = 0; k < 2; k++) add(mus, bell(ch[arp[(b * 2 + k) % 8] % ch.length] + 24), v + (k * beat) / 2, 0.2, k ? 0.35 : -0.35);
  }
  const n = mus[0].length, f = Math.round(0.35 * SR);
  for (const c of mus) for (let i = 0; i < f; i++) c[n - 1 - i] *= i / f;
}

// ---------- mixage ----------
// events : [{ v, type, gain, pan, rate }] ; voices : { lineId: Float32Array mono 48 kHz }
export function mixVideo(T, events, voices, { music = 'tension', musicGain = 0.45 } = {}) {
  const N = Math.ceil((T.duration + 0.05) * SR);
  const bus = () => [new Float32Array(N), new Float32Array(N)];
  const sfx = bus(), mus = bus(), vox = bus(), send = bus();
  for (const e of events) {
    const b = sample(e.type);
    if (!b) continue;
    const at = e.type === 'riser' ? e.v - 1.3 : e.type === 'swell' ? e.v - 1.1 : e.v;
    add(sfx, b, at, e.gain ?? 0.6, e.pan ?? 0, e.rate ?? 1);
    if (['impact', 'boom', 'clang', 'applause'].includes(e.type)) add(send, b, at, (e.gain ?? 0.6) * 0.3, e.pan ?? 0, e.rate ?? 1);
  }
  if (music && music !== 'none') composeMusic(T, music, mus);
  for (const L of T.lines) {
    const b = voices[L.id];
    if (!b) continue;
    const g = rmsGain(b, 0.2);
    add(vox, b, L.v, g, 0); add(send, b, L.v, g * 0.04, 0);
  }
  for (const ch of vox) { filt(ch, biquad('hp', 85, 0.7)); filt(ch, biquad('pk', 3200, 1.0, 2.5)); }
  // ducking : musique −13 dB et bruitages −8 dB pendant la voix
  const duck = new Float32Array(N).fill(1);
  for (const L of T.lines) for (let i = Math.max(0, Math.round((L.v - 0.08) * SR)); i < Math.min(N, Math.round((L.v + L.dur + 0.25) * SR)); i++) duck[i] = 0.22;
  let dv = 1;
  for (let i = 0; i < N; i++) { const tg = duck[i]; dv += (tg - dv) * (tg < dv ? 0.0009 : 0.00012); duck[i] = dv; }
  for (let i = 0; i < N; i++) { send[0][i] += mus[0][i] * 0.05; send[1][i] += mus[1][i] * 0.05; }
  const [rvL, rvR] = reverb(send[0], send[1], 0.4);
  const out = bus();
  for (let c = 0; c < 2; c++) {
    const rv = c ? rvR : rvL;
    for (let i = 0; i < N; i++) { const dn = (duck[i] - 0.22) / 0.78; out[c][i] = vox[c][i] + sfx[c][i] * 0.62 * (0.4 + 0.6 * dn) + mus[c][i] * musicGain * duck[i] + rv[i]; }
  }
  limiter(out, 0.891);
  for (let c = 0; c < 2; c++) for (let i = 0; i < 480; i++) { out[c][i] *= i / 480; out[c][N - 1 - i] *= i / 480; }
  return out;
}
