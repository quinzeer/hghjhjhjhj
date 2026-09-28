// Mixeur audio en JavaScript pur (aucune Web Audio API) : identique dans Node et dans le navigateur.
//  - bruitages synthétisés à partir des événements physiques (chocs, portes, bras, chutes)
//  - musique procédurale « trap tension » 140 BPM qui suit les manches
//  - foule : babillage multi-voix + réactions + applaudissements de synthèse
//  - voix off (PCM décodé en amont), ducking de la musique, réverbération algorithmique, limiteur
import { P, PHASE, sampleAt } from './sim.js';

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
export function mixEpisode(D, pcm, opts = {}) {
  const dur = D.duration;
  const N = Math.ceil((dur + 0.05) * SR);
  const bus = () => [new Float32Array(N), new Float32Array(N)];
  const sfx = bus(), mus = bus(), vox = bus(), crowd = bus(), send = bus();
  const H = D.hud;

  // --- bruitages ---
  const clicks = Array.from({ length: 8 }, (_, k) => marbleClick(k));
  const S = {
    land: thud(95, 0.35, 3), knocks: [knock(1), knock(2), knock(3)], clangs: [clang(0), clang(3), clang(6)], alarm: beeps(),
    gate: hydraulic(4), siren: siren(), boom: thud(52, 0.9, 7), ding: ding(), whooshD: whoosh(0.45, false, 8), whooshU: whoosh(0.3, true, 9),
    impact: impact(10), riser: riser(1.3, 11), rewind: rewind(), heart: heartbeat(),
  };
  let window0 = -1, inWin = 0;
  for (const e of D.sfx) {
    const slow = (e.rate ?? 1) < 0.85;
    const rate = slow ? Math.max(0.45, Math.sqrt(e.rate)) : 1;
    const pan = clamp((e.x ?? 0) / 2.2, -0.8, 0.8);
    switch (e.type) {
      case 'click': {
        if (e.gain < 0.07) break;
        const w = Math.floor(e.v * 12);
        if (w !== window0) { window0 = w; inWin = 0; }
        if (++inWin > 6) break;
        add(sfx, clicks[e.key % 8], e.v, 0.42 * Math.pow(e.gain, 1.2), pan, rate * (0.93 + (e.key % 13) * 0.011));
        break;
      }
      case 'land': add(sfx, S.land, e.v, 0.35 * e.gain, pan); add(sfx, clicks[e.key % 8], e.v, 0.25 * e.gain, pan, 0.8); break;
      case 'wall': add(sfx, S.knocks[e.key % 3], e.v, 0.3 * e.gain, pan, rate); break;
      case 'arm': add(sfx, S.clangs[e.key % 3], e.v, 0.42 * e.gain, pan, rate); add(send, S.clangs[e.key % 3], e.v, 0.12 * e.gain, pan, rate); break;
      case 'alarm': add(sfx, S.alarm, e.v, 0.16, 0); break;
      case 'gate': add(sfx, S.gate, e.v, 0.3, 0); break;
      case 'siren': add(sfx, S.siren, e.v, 0.22, 0); break;
      case 'crumble': add(sfx, crumble(e.dur || 1, Math.floor(e.v * 100)), e.v, 0.55, 0); add(send, S.boom, e.v, 0.2, 0); break;
      case 'elim':
        add(sfx, S.whooshD, e.v - 0.05, 0.4, pan, rate);
        add(sfx, S.boom, e.v + 0.1, 0.5, 0, rate); add(send, S.boom, e.v + 0.1, 0.18, 0, rate);
        if (e.seg === 'live' && e.rank > 2) add(sfx, S.ding, e.v + 0.06, 0.2, 0.2);
        break;
      case 'phase':
        if (e.phase === PHASE.R2 || e.phase === PHASE.R3 || e.phase === PHASE.FINAL) {
          add(sfx, S.riser, e.v - 1.3, 0.35, 0); add(sfx, S.impact, e.v, 0.8, 0); add(send, S.impact, e.v, 0.3, 0);
        }
        if (e.phase === PHASE.WIN) { add(sfx, S.impact, e.v, 0.9, 0); add(send, S.impact, e.v, 0.35, 0); }
        break;
      case 'whoosh': add(sfx, S.whooshU, e.v, 0.3 * e.gain, 0); break;
      case 'rewind': add(sfx, S.rewind, e.v, 0.55, 0); break;
      case 'impact': add(sfx, S.impact, e.v, 0.7, 0); add(send, S.impact, e.v, 0.25, 0); break;
      case 'boardIn': add(sfx, S.whooshU, e.v, 0.35, 0); add(sfx, S.ding, e.v + 0.1, 0.25, 0); break;
    }
  }
  add(sfx, S.impact, 0.02, 0.55, 0);                        // coup d'ouverture sur la 1re image
  // grondement de roulement et moteur du bras (enveloppes image par image)
  {
    const rum = filt(filt(noise(N, 12), biquad('lp', 300, 0.7), new Float32Array(N)), biquad('hp', 70, 0.7));
    const hum = new Float32Array(N); let ph = 0;
    const step = Math.round(SR / 60);
    let eg = 0, ag = 0, af = 40;
    for (let i = 0; i < N; i += step) {
      const v = i / SR, { s, g } = D.simAt(v);
      const { A } = sampleAt(D.rec, s);
      const tgE = g.kind === 'celebrate' ? 0 : clamp(A.energy / 14, 0, 1) * (g.kind === 'replay' ? 0.5 : 1);
      const tgA = A.phase >= PHASE.R2 && A.phase < PHASE.WIN ? A.armExt * (0.35 + 0.25 * Math.abs(A.armW)) : 0;
      const tgF = 38 + 22 * Math.abs(A.armW);
      for (let j = i; j < Math.min(N, i + step); j++) {
        eg += (tgE - eg) * 0.002; ag += (tgA - ag) * 0.002; af += (tgF - af) * 0.002;
        ph += (af / SR); ph -= Math.floor(ph);
        hum[j] = ((2 * ph - 1) * 0.5 + Math.sin(TAU * ph * 2) * 0.3) * ag;
        rum[j] *= eg * 0.55;
      }
    }
    filt(hum, biquad('lp', 380, 0.8));
    for (let i = 0; i < N; i++) { sfx[0][i] += rum[i] * 0.5 + hum[i] * 0.12; sfx[1][i] += rum[i] * 0.5 + hum[i] * 0.12; }
  }
  // battements de cœur pendant la finale
  {
    const tF = D.A.tFinal, tW = D.A.tWin;
    let s = tF + 0.3;
    while (s < tW) {
      const k = clamp((s - tF) / (tW - tF), 0, 1);
      add(sfx, S.heart, D.vOfSim(s), 0.55, 0);
      s += 0.72 - 0.3 * k;
    }
  }

  // --- musique ---
  if (opts.music !== false) composeMusic(D, mus);

  // --- voix off ---
  for (const L of D.lines) {
    const b = pcm.voices[L.id];
    if (!b) continue;
    const g = rmsGain(b, 0.2);            // ≈ −14 dBFS RMS pendant la parole
    add(vox, b, L.v, g, 0);
    add(send, b, L.v, g * 0.05, 0);
  }
  for (const ch of vox) { filt(ch, biquad('hp', 85, 0.7)); filt(ch, biquad('pk', 3200, 1.0, 2.5)); }

  // --- foule ---
  if (pcm.crowd) composeCrowd(D, pcm.crowd, crowd);

  // --- ducking de la musique sous la voix ---
  const duck = new Float32Array(N).fill(1);
  for (const L of D.lines) {
    const a = Math.round((L.v - 0.08) * SR), b = Math.round((L.v + L.dur + 0.25) * SR);
    for (let i = Math.max(0, a); i < Math.min(N, b); i++) duck[i] = 0.22;
  }
  let dv = 1;
  for (let i = 0; i < N; i++) { const tg = duck[i]; dv += (tg - dv) * (tg < dv ? 0.0009 : 0.00012); duck[i] = dv; }

  // --- somme, réverbération, limiteur ---
  for (let i = 0; i < N; i++) { send[0][i] += crowd[0][i] * 0.7 + mus[0][i] * 0.05; send[1][i] += crowd[1][i] * 0.7 + mus[1][i] * 0.05; }
  const [rvL, rvR] = reverb(send[0], send[1], 0.42);
  const gM = opts.music === false ? 0 : 0.45;
  const out = [new Float32Array(N), new Float32Array(N)];
  for (let c = 0; c < 2; c++) {
    const rv = c ? rvR : rvL;
    for (let i = 0; i < N; i++) { const dn = (duck[i] - 0.22) / 0.78; out[c][i] = vox[c][i] + sfx[c][i] * 0.62 * (0.4 + 0.6 * dn) + mus[c][i] * gM * duck[i] + crowd[c][i] * 0.7 + rv[i]; }
  }
  if (opts.stems) { const dn = (i) => 0.4 + 0.6 * (duck[i] - 0.22) / 0.78; return { vox, sfx: sfx.map((ch) => ch.map((x, i) => x * dn(i))), mus: [mus[0].map((x, i) => x * gM * duck[i]), mus[1].map((x, i) => x * gM * duck[i])], crowd, rv: [rvL, rvR] }; }
  limiter(out, 0.891);
  // micro-fondus aux extrémités (boucle propre)
  for (let c = 0; c < 2; c++) for (let i = 0; i < 480; i++) { out[c][i] *= i / 480; out[c][N - 1 - i] *= i / 480; }
  return out;
}

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

function composeMusic(D, mus) {
  const H = D.hud, bpm = 140, beat = 60 / bpm, dur = D.duration;
  const K = kick808(), C = clap(), HH = hat(false), OH = hat(true);
  const bellCache = new Map(), bell = (m) => { if (!bellCache.has(m)) bellCache.set(m, bellNote(m)); return bellCache.get(m); };
  const tF = D.vOfSim(D.A.tFinal), tDuel = D.vOfSim(D.A.tFinal + P.finalSetup), tW = H.vWin;
  const r2 = H.vR2 ?? 1e9, r3 = H.vR3 ?? 1e9;
  // progression i – VI – III – VII (do mineur), 2 mesures par accord
  const prog = [[48, 51, 55], [44, 48, 51], [51, 55, 58], [46, 50, 53]];
  const roots = [36, 32, 39, 34];
  const arp = [0, 1, 2, 1, 2, 0, 2, 1];
  const nBeats = Math.ceil(dur / beat);
  const inDrums = (v) => (v < tF - 0.1 || (v >= tDuel && v < tW - 0.3) || v >= H.vCel0) && !(v >= H.vReplay0 && v < H.vReplay1);
  for (let b = 0; b < nBeats; b++) {
    const v = b * beat;
    const bar = Math.floor(b / 4), chord = Math.floor(bar / 2) % 4, inBar = b % 4;
    const celebrate = v >= H.vCel0;
    const ch = celebrate ? [[44, 48, 51], [46, 50, 53], [48, 52, 55], [48, 52, 55]][chord] : prog[chord];
    const root = celebrate ? [32, 34, 36, 36][chord] : roots[chord];
    if (inBar === 0 && bar % 2 === 0 && v < dur - 0.3) {
      const len = Math.min(8 * beat, dur - v);
      if (len > 0.5) { const pd = padChord(ch.map((m) => m + 12), len, b); add(mus, pd, v, v >= tF && v < tW ? 0.9 : 0.55, 0); }
    }
    if (!inDrums(v)) continue;
    const r3on = v >= r3 || v >= tDuel;
    // kick trap : 1, « et » du 2, 3 (+ variations)
    if (inBar === 0 || inBar === 2) add(mus, K, v, 0.85, 0);
    if (inBar === 1 && (bar % 2 === 1 || r3on)) add(mus, K, v + beat * 0.5, 0.7, 0);
    if (inBar === 1 || inBar === 3) add(mus, C, v, 0.55, 0.05);
    // hi-hats : croches, doubles-croches puis roulements en manche 3
    const div = r3on ? 4 : v >= r2 ? 2 : 2;
    for (let k = 0; k < div; k++) add(mus, HH, v + (k * beat) / div, k === 0 ? 0.3 : 0.2, 0.3);
    if (r3on && inBar === 3 && bar % 2 === 1) for (let k = 0; k < 6; k++) add(mus, HH, v + beat * 0.5 + (k * beat) / 12, 0.18, 0.3);
    if (inBar === 2 && bar % 2 === 1) add(mus, OH, v + beat * 0.5, 0.2, -0.3);
    // basse 808
    if (v >= 2.3 && (inBar === 0 || inBar === 2)) add(mus, subNote(root, beat * 1.8), v, 0.5, 0);
    // cloches arpégées à partir de la manche 2
    if (v >= r2 || celebrate) for (let k = 0; k < 2; k++) { const m = ch[arp[(b * 2 + k) % 8] % 3] + 24; add(mus, bell(m), v + (k * beat) / 2, 0.22, k ? 0.35 : -0.35); }
  }
  // finale : bourdon + montée
  const drone = new Float32Array(Math.round((tW - tF + 0.5) * SR));
  for (let i = 0; i < drone.length; i++) { const t = i / SR; drone[i] = (Math.sin(TAU * 32.7 * t) + 0.5 * Math.sin(TAU * 49 * t)) * Math.min(1, t / 0.8) * 0.35 * (1 + t / (tW - tF)); }
  add(mus, drone, tF, 0.8, 0);
  add(mus, riser(Math.max(0.5, tW - tDuel), 21), tDuel, 0.4, 0);
  // accord de victoire (tierce picarde)
  add(mus, padChord([60, 64, 67, 72], 2.5, 99), tW, 1.1, 0);
  // replay : musique étouffée
  const a = Math.round(H.vReplay0 * SR), b = Math.round(H.vReplay1 * SR);
  for (const chn of mus) {
    const seg = chn.slice(a, b); filt(seg, biquad('lp', 500, 0.7));
    for (let i = a; i < b; i++) chn[i] = seg[i - a] * 0.8;
  }
  // fondu de fin
  const n = mus[0].length, f = Math.round(0.35 * SR);
  for (const chn of mus) for (let i = 0; i < f; i++) chn[n - 1 - i] *= i / f;
}

function composeCrowd(D, C, crowd) {
  const r = rng(4242), dur = D.duration;
  const voices = 12;
  const clip = (key, vi) => C[`${key}_${vi}`];
  // rumeur de fond : 5 à 9 bribes de phrases par seconde selon l'intensité du jeu
  let v = 0;
  while (v < dur) {
    const inten = D.intensity(v);
    const key = ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'][Math.floor(r() * 6)], vi = Math.floor(r() * voices);
    add(crowd, clip(key, vi), v, 0.05 + 0.07 * inten, r() * 1.6 - 0.8, 0.9 + r() * 0.2);
    v += 1 / (4 + 6 * inten) * (0.5 + r());
  }
  // réactions
  for (const e of D.crowd) {
    if (e.kind === 'oh' || e.kind === 'non') {
      for (let k = 0; k < 9; k++) add(crowd, clip(e.kind, Math.floor(r() * voices)), e.v + r() * 0.12, 0.2 * e.gain, r() * 1.6 - 0.8, 0.9 + r() * 0.2);
    } else if (e.kind === 'cheer') {
      for (let k = 0; k < 14; k++) add(crowd, clip('ouais', Math.floor(r() * voices)), e.v + r() * 0.35, 0.22 * e.gain, r() * 1.8 - 0.9, 0.92 + r() * 0.16);
      add(crowd, applause(4.5, Math.floor(e.v * 10)), e.v, 0.5 * e.gain, -0.2);
      add(crowd, applause(4.5, Math.floor(e.v * 10) + 1), e.v + 0.05, 0.5 * e.gain, 0.2);
      for (let k = 0; k < 3; k++) add(crowd, whistle(Math.floor(e.v * 7) + k), e.v + 0.3 + r() * 1.2, 0.18, r() * 1.4 - 0.7);
    }
  }
  for (const ch of crowd) filt(ch, biquad('lp', 3800, 0.6));
}

// WAV 16 bits stéréo
export function encodeWav(ch) {
  const n = ch[0].length, buf = new ArrayBuffer(44 + n * 4), dv = new DataView(buf);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); dv.setUint32(4, 36 + n * 4, true); w(8, 'WAVE'); w(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 2, true);
  dv.setUint32(24, SR, true); dv.setUint32(28, SR * 4, true); dv.setUint16(32, 4, true); dv.setUint16(34, 16, true); w(36, 'data'); dv.setUint32(40, n * 4, true);
  let o = 44;
  for (let i = 0; i < n; i++) for (let c = 0; c < 2; c++) { const s = clamp(ch[c][i], -1, 1); dv.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true); o += 2; }
  return new Uint8Array(buf);
}
