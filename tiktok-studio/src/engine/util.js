// Outils mathématiques déterministes (aucun Math.random : chaque image doit être reproductible).

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => clamp((x - a) / (b - a));
export const smoothstep = (a, b, x) => { const t = invLerp(a, b, x); return t * t * (3 - 2 * t); };
export const fract = (x) => x - Math.floor(x);

export const ease = {
  linear: (t) => t,
  inQuad: (t) => t * t,
  outQuad: (t) => 1 - (1 - t) * (1 - t),
  inOutQuad: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  inCubic: (t) => t * t * t,
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outQuart: (t) => 1 - Math.pow(1 - t, 4),
  inOutQuart: (t) => (t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2),
  inExpo: (t) => (t === 0 ? 0 : Math.pow(2, 10 * t - 10)),
  outExpo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutExpo: (t) => (t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  outElastic: (t) => (t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1),
};

// Animation « pop » : 0 → dépassement → 1 (sous-titres, badges).
export function popScale(t, dur = 0.16, overshoot = 1.12) {
  if (t <= 0) return 0;
  if (t >= dur) return 1;
  const k = t / dur;
  if (k < 0.6) return lerp(0.55, overshoot, ease.outCubic(k / 0.6));
  return lerp(overshoot, 1, ease.inOutQuad((k - 0.6) / 0.4));
}

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hashStr(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

// Bruit de gradient 1D lissé (tremblement caméra à la main).
export function noise1D(seed = 1) {
  const rnd = mulberry32(seed);
  const g = new Float32Array(512);
  for (let i = 0; i < 512; i++) g[i] = rnd() * 2 - 1;
  return (x) => {
    const i = Math.floor(x); const f = x - i;
    const a = g[i & 511] * f; const b = g[(i + 1) & 511] * (f - 1);
    const u = f * f * (3 - 2 * f);
    return lerp(a, b, u) * 2;
  };
}

// Somme d'octaves : mouvement organique type « opérateur caméra ».
export function fbm1D(seed = 1, octaves = 3) {
  const ns = Array.from({ length: octaves }, (_, i) => noise1D(seed * 31 + i * 7));
  return (x) => { let s = 0, amp = 1, fr = 1, norm = 0; for (const n of ns) { s += n(x * fr) * amp; norm += amp; amp *= 0.5; fr *= 2.03; } return s / norm; };
}

// Interpolation de keyframes [{t, v}] avec easing par segment (v : nombre ou tableau).
export function keyframes(frames, t, defaultEase = ease.inOutCubic) {
  if (!frames || !frames.length) return undefined;
  if (t <= frames[0].t) return frames[0].v;
  const last = frames[frames.length - 1];
  if (t >= last.t) return last.v;
  let i = 0;
  while (i < frames.length - 1 && t > frames[i + 1].t) i++;
  const a = frames[i], b = frames[i + 1];
  const e = typeof b.ease === 'string' ? ease[b.ease] : (b.ease || defaultEase);
  const k = e(invLerp(a.t, b.t, t));
  if (Array.isArray(a.v)) return a.v.map((x, j) => lerp(x, b.v[j], k));
  return lerp(a.v, b.v, k);
}

// Décroissance d'impact : secousse brève après un « boom ».
export function impulse(t, t0, decay = 7, dur = 0.6) {
  const d = t - t0;
  if (d < 0 || d > dur) return 0;
  return Math.exp(-decay * d);
}
