// Simulation physique déterministe de l'arène.
// Aucune dépendance : tourne à l'identique dans Node (recherche de seeds) et dans le navigateur (rendu).
// Unités SI : mètres, secondes, m/s². Le plateau est centré sur l'origine, surface à y = 0 quand il est à plat.

export const P = {
  R0: 1.6,            // rayon initial du plateau
  r: 0.14,            // rayon d'une bille (≈ boule de bowling)
  g: 9.81,
  hz: 480,            // pas physique
  recHz: 120,         // échantillonnage enregistré pour le rendu
  nGates: 12,         // barrières périphériques (portes de 30° ≈ 3 billes ; se referment après un passage)
  k: 0.02,            // cuvette : hauteur de surface y = k·ρ² (≈ 5 cm au bord)
  wallT: 0.05,
  wallH: 0.17,
  rings: 6,           // anneaux extérieurs qui s'effondrent en manche 3
  ringW: 0.1,
  tilesPerRing: 12,
  hubR: 0.17,
  hubH: 0.42,
  armW: 0.05,         // demi-épaisseur du bras rotatif
  eBall: 0.86, eWall: 0.55, eArm: 0.72, eFloor: 0.36,
  crr: 0.012,         // résistance au roulement
  lin: 0.06,          // amortissement linéaire
  // Rythme visé : la k-ième élimination (k ≤ 30) à Ts + D·(k/30)^p, puis un duel final de ~duel s
  Ts: 3.3, D: 36, p: 1.25, duel: 7, finalSetup: 3.2,
};

export const PHASE = { DROP: 0, R1: 1, R2: 2, R3: 3, FINAL: 4, WIN: 5 };
export const STATE = { AIR: 0, ROLL: 1, FALL: 2, WIN: 3 };

// ---------- utilitaires ----------
export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function noise1D(rng, n = 256) {
  const k = new Float64Array(n);
  for (let i = 0; i < n; i++) k[i] = rng() * 2 - 1;
  return (x) => {
    const i = Math.floor(x), f = x - i;
    const a = k[((i % n) + n) % n], b = k[(((i + 1) % n) + n) % n];
    const s = f * f * f * (f * (f * 6 - 15) + 10);
    return a + (b - a) * s;
  };
}


// ---------- maths déterministes ----------
// Math.sin/atan2/pow/hypot peuvent différer d'un ULP d'un moteur JS à l'autre ; la simulation étant chaotique,
// on n'utilise ici que + − × ÷ et sqrt (arrondis IEEE exacts) : même seed ⇒ même partie dans Node, Chrome, Safari, Firefox.
const PI_ = 3.141592653589793, HALF_PI = 1.5707963267948966, TWO_PI = 6.283185307179586, LN2 = 0.6931471805599453;
export function dsin(x) {
  x = x - TWO_PI * Math.floor((x + PI_) / TWO_PI);
  if (x > HALF_PI) x = PI_ - x; else if (x < -HALF_PI) x = -PI_ - x;
  const x2 = x * x;
  return x * (1 - (x2 / 6) * (1 - (x2 / 20) * (1 - (x2 / 42) * (1 - (x2 / 72) * (1 - (x2 / 110) * (1 - (x2 / 156) * (1 - (x2 / 210) * (1 - x2 / 272))))))));
}
export const dcos = (x) => dsin(x + HALF_PI);
function datan01(x) { // x ≥ 0
  let off = 0;
  if (x > 1) return HALF_PI - datan01(1 / x);
  if (x > 0.41421356237309503) { x = (x - 1) / (x + 1); off = PI_ / 4; }
  const x2 = x * x;
  let term = x, sum = x;
  for (let k = 3; k <= 29; k += 2) { term *= -x2; sum += term / k; }
  return off + sum;
}
export function datan2(y, x) {
  if (x === 0 && y === 0) return 0;
  const ax = Math.abs(x), ay = Math.abs(y);
  let a = ay <= ax ? datan01(ay / ax) : HALF_PI - datan01(ax / ay);
  if (x < 0) a = PI_ - a;
  return y < 0 ? -a : a;
}
export function dexp(x) {
  const n = Math.round(x / LN2), r = x - n * LN2;
  let term = 1, sum = 1;
  for (let k = 1; k <= 18; k++) { term *= r / k; sum += term; }
  let m = n;
  while (m > 0) { sum *= 2; m--; }
  while (m < 0) { sum /= 2; m++; }
  return sum;
}
export function dlog(x) {
  let k = 0;
  while (x >= 2) { x /= 2; k++; }
  while (x < 1) { x *= 2; k--; }
  if (x > 1.4142135623730951) { x /= 2; k++; }
  const z = (x - 1) / (x + 1), z2 = z * z;
  let term = z, sum = z;
  for (let j = 3; j <= 25; j += 2) { term *= z2; sum += term / j; }
  return 2 * sum + k * LN2;
}
export const dpow = (a, b) => (a > 0 ? dexp(b * dlog(a)) : a === 0 ? 0 : NaN);
export const dhyp = (x, y) => Math.sqrt(x * x + y * y);
const dhyp3 = (x, y, z) => Math.sqrt(x * x + y * y + z * z);

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const smooth = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };

// quaternions [x, y, z, w]
export function qmul(a, b) {
  return [
    a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
    a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
    a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
    a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
  ];
}
export function qrot(q, v) {
  const [x, y, z, w] = q;
  const ix = w * v[0] + y * v[2] - z * v[1];
  const iy = w * v[1] + z * v[0] - x * v[2];
  const iz = w * v[2] + x * v[1] - y * v[0];
  const iw = -x * v[0] - y * v[1] - z * v[2];
  return [
    ix * w + iw * -x + iy * -z - iz * -y,
    iy * w + iw * -y + iz * -x - ix * -z,
    iz * w + iw * -z + ix * -y - iy * -x,
  ];
}
export const qconj = (q) => [-q[0], -q[1], -q[2], q[3]];
function qnorm(q) { const l = Math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]) || 1; return [q[0] / l, q[1] / l, q[2] / l, q[3] / l]; }
function qintegrate(q, w, dt) {
  const h = 0.5 * dt;
  const d = qmul([w[0] * h, w[1] * h, w[2] * h, 0], q);
  return qnorm([q[0] + d[0], q[1] + d[1], q[2] + d[2], q[3] + d[3]]);
}
// Inclinaison : le côté (dx, dz) du plateau descend d'un angle |(dx, dz)|
export function tiltQuat(dx, dz) {
  const a = dhyp(dx, dz);
  if (a < 1e-9) return [0, 0, 0, 1];
  const s = dsin(a / 2) / a;
  return [dz * s, 0, -dx * s, dcos(a / 2)];
}

// Anneaux effondrés : rayon utile du plateau à l'angle phi et à l'instant t
export function effRadius(rings, phi, t) {
  let R = P.R0;
  for (let k = 0; k < rings.length; k++) {
    const rg = rings[k];
    let rel = (rg.dir * (phi - rg.phi0)) / (2 * Math.PI);
    rel -= Math.floor(rel);
    if (t >= rg.t + rel * rg.dur) R = P.R0 - (k + 1) * P.ringW; else break;
  }
  return R;
}
export function tileFallTime(rings, k, phiMid) {
  const rg = rings[k];
  if (!rg) return Infinity;
  let rel = (rg.dir * (phiMid - rg.phi0)) / (2 * Math.PI);
  rel -= Math.floor(rel);
  return rg.t + rel * rg.dur;
}

export function targetElims(t) {
  if (t <= P.Ts) return 0;
  return 30 * Math.min(1, dpow((t - P.Ts) / P.D, 1 / P.p));
}
export function targetTime(k) {
  return k <= 30 ? P.Ts + P.D * dpow(k / 30, P.p) : P.Ts + P.D + P.duel;
}

// ---------- simulation ----------
export function simulate(seed, opts = {}) {
  const N = opts.n || 32;
  const rng = mulberry32(seed * 2654435761 >>> 0);
  const nA = noise1D(rng), nB = noise1D(rng), nC = noise1D(rng), nD = noise1D(rng);
  const r = P.r, dt = 1 / P.hz, g = P.g;
  const recEvery = P.hz / P.recHz;

  // Placement initial : grille hexagonale bruitée, hauteurs étagées (pluie de billes)
  const spots = [];
  const sp = 0.33;
  for (let iz = -6; iz <= 6; iz++) for (let ix = -6; ix <= 6; ix++) {
    const x = (ix + (iz & 1) * 0.5) * sp, z = iz * sp * 0.866;
    const rho = dhyp(x, z);
    if (rho < 1.25 && rho > 0.42) spots.push([x, z]);
  }
  for (let i = spots.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [spots[i], spots[j]] = [spots[j], spots[i]]; }
  const order = [...Array(N).keys()];
  for (let i = N - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }

  const balls = [];
  for (let k = 0; k < N; k++) {
    const i = order[k];
    const [x, z] = spots[k];
    const a0 = rng() * Math.PI * 2, a1 = rng() * Math.PI * 2;
    balls[i] = {
      i, s: STATE.AIR,
      p: [x + (rng() - 0.5) * 0.04, 0.55 + rng() * 1.2, z + (rng() - 0.5) * 0.04],
      v: [(rng() - 0.5) * 0.3, -rng() * 0.5, (rng() - 0.5) * 0.3],
      q: qnorm([dsin(a0) * 0.7, dcos(a1) * 0.7, dsin(a1) * 0.7, dcos(a0)]),
      w: [(rng() - 0.5) * 6, (rng() - 0.5) * 6, (rng() - 0.5) * 6],
      elimT: -1, rank: 0,
      pw: null, vw: null, qw: null, ww: null, // repère monde après chute
      minEdge: 9, nearMiss: 0, lastNear: -9,
    };
  }

  // État de l'arène
  const gates = Array.from({ length: P.nGates }, () => ({ open: 0, warn: -9, start: Infinity, until: -9, perm: false }));
  const rings = [];
  let phase = PHASE.DROP, alive = N;
  let d = 0.35, dS = 0.35, I = 0;
  let armExt = 0, armT = Infinity, armA = rng() * Math.PI * 2, armW = 0, armDir = rng() < 0.5 ? 1 : -1;
  let nextArmFlip = Infinity;
  let allDown = false, calmUntil = -9;
  let nextGate = 2.3, nextRing = Infinity, winT = Infinity, winner = -1, finalT = Infinity;
  let tiltAmp = 0, huntDir = 0, huntUntil = -9, huntW = 0, nextHunt = 2.6;
  const events = [];
  const elims = [];
  const lastPair = new Map();

  // Enregistrement
  const maxT = opts.maxT || 110;
  const frames = [];
  let t = 0, step = 0;

  // Portes « pulsées » : alerte rouge, la barrière s'abaisse quelques instants, puis remonte.
  // Débit limité par porte : c'est ce qui donne un rythme d'éliminations régulier.
  function openGateAt(k, dur, hunt) {
    const gt = gates[k];
    gt.warn = t; gt.start = t + 0.5; gt.until = t + 0.5 + dur; gt.perm = false;
    events.push({ t, type: 'gateWarn', k, at: gt.start, until: gt.until, hunt });
  }
  // L'arène « chasse » : ouvre la porte devant la bille la plus exposée et penche le plateau vers elle
  function hunt(dur) {
    let best = null, bestS = -1;
    for (const b of balls) {
      if (b.s !== STATE.ROLL) continue;
      const px = b.p[0] + b.v[0] * 0.5, pz = b.p[2] + b.v[2] * 0.5;
      const rp = dhyp(px, pz);
      const sc = rp + rng() * 0.25;
      if (sc > bestS) { bestS = sc; best = datan2(pz, px); }
    }
    if (best === null) return;
    huntDir = best; huntUntil = t + 0.5 + dur;
    if (!rings.length) {
      const ph = best < 0 ? best + 2 * Math.PI : best;
      const k = Math.floor(ph / ((2 * Math.PI) / P.nGates)) % P.nGates;
      if (t >= gates[k].until + 0.3 && gates[k].warn < t - 0.01) openGateAt(k, dur, true);
    }
  }
  function pulseGate(dur, permanent = false) {
    const w = (2 * Math.PI) / P.nGates;
    const cand = [];
    for (let k = 0; k < P.nGates; k++) {
      const gt = gates[k];
      if (gt.perm || t < gt.until + 0.6 || gt.warn > t - 0.01) continue;
      let near = 0;
      const mid = (k + 0.5) * w;
      for (const b of balls) {
        if (b.s !== STATE.ROLL) continue;
        const rho = dhyp(b.p[0], b.p[2]);
        let dphi = Math.abs(datan2(b.p[2], b.p[0]) - mid); dphi = Math.min(dphi, 2 * Math.PI - dphi);
        if (rho > P.R0 - 0.5 && dphi < w * 1.2) near++;
      }
      cand.push([k, 1 + near * 1.6 + rng() * 1.2]);
    }
    if (!cand.length) return;
    let tot = cand.reduce((a, c) => a + c[1], 0), x = rng() * tot, k = cand[0][0];
    for (const c of cand) { x -= c[1]; if (x <= 0) { k = c[0]; break; } }
    const gt = gates[k];
    gt.warn = t; gt.start = t + 0.55; gt.until = permanent ? Infinity : t + 0.55 + dur; gt.perm = permanent;
    events.push({ t, type: 'gateWarn', k, at: gt.start, until: gt.until });
  }
  function gateBlocks(k) { return gates[k].open < 0.6; }
  function gateAngles(k) { const w = (2 * Math.PI) / P.nGates; return [k * w + 0.012, (k + 1) * w - 0.012]; }

  function setPhase(ph) {
    if (ph <= phase) return;
    phase = ph;
    events.push({ t, type: 'phase', phase: ph, alive });
    if (ph === PHASE.R2) { armT = t; nextArmFlip = t + 7 + rng() * 4; }
    if (ph === PHASE.R3) { calmUntil = t + 2.2; nextRing = t + 2.2 + 1.5; }
    if (ph === PHASE.R2 || ph === PHASE.R3) { I = Math.min(I, 0); dS = Math.min(dS, 0.6); }
    if (ph === PHASE.FINAL) { dS = 0; for (const gt of gates) if (!gt.perm) gt.until = Math.min(gt.until, t); }
    if (ph === PHASE.WIN) winT = t;
    if (ph === PHASE.FINAL) finalT = t;
  }

  while (t < maxT) {
    // ----- pilotage (difficulté adaptative + manches) -----
    if (phase === PHASE.FINAL) {
      // duel : mise en place (plateau stabilisé, barrière lumineuse), puis escalade continue
      d = t < finalT + P.finalSetup ? 0 : clamp(0.15 + (t - finalT - P.finalSetup) / 3.6, 0.15, 2.6);
    } else {
      const err = targetElims(t) - (N - alive);
      if (t > P.Ts) { I += err * dt * (err < 0 ? 3 : 1); I = clamp(I, -4, 6); }
      d = clamp(0.45 + 0.25 * err + 0.08 * I, 0, 2.0);
      if (phase === PHASE.R1 && alive === N) d = Math.max(d, 1.25); // première élimination rapide (paiement du hook)
    }
    if (t > P.Ts + P.D + P.duel + 12) d = 3;
    dS += (d - dS) * (dt / 1.1);

    if (phase === PHASE.DROP && t > 2.2) setPhase(PHASE.R1);
    if (phase < PHASE.R2 && alive <= 20) setPhase(PHASE.R2);
    if (phase < PHASE.R3 && alive <= 8) setPhase(PHASE.R3);
    if (phase < PHASE.FINAL && alive <= 2) setPhase(PHASE.FINAL);
    if (phase < PHASE.WIN && alive <= 1) setPhase(PHASE.WIN);

    // barrières
    const errNow = phase === PHASE.FINAL ? (t > finalT + P.finalSetup + 2.8 ? 1 : -1) : targetElims(t + 0.6) - (N - alive);
    if (phase === PHASE.R3 && !allDown && t >= calmUntil) {
      // manche 3 : toutes les barrières tombent pour de bon (en cascade autour du plateau)
      allDown = true;
      const k0 = Math.floor(rng() * P.nGates);
      for (let j = 0; j < P.nGates; j++) { const gt = gates[(k0 + j) % P.nGates]; gt.perm = true; gt.warn = t; gt.start = t + 0.1 + j * 0.05; gt.until = Infinity; }
      events.push({ t, type: 'wallsDown', k0 });
    }
    if (phase >= PHASE.R1 && phase < PHASE.WIN && t >= nextHunt && errNow > 0.35 && t > huntUntil && t > calmUntil) {
      hunt(alive === N ? 2.2 : 1.1 + 0.4 * Math.min(dS, 1.5));
      nextHunt = t + (phase === PHASE.FINAL ? 1.2 : 0.9);
    }
    // portes « leurres » : suspense sans forcément d'élimination
    if ((phase === PHASE.R1 || phase === PHASE.R2) && t >= nextGate && !allDown) {
      const openNow = gates.filter((gt) => t >= gt.warn && t < gt.until).length;
      if (openNow < 2 && errNow > -0.8) pulseGate(0.55 + 0.3 * rng());
      nextGate = t + 2.4 + rng() * 1.8;
    }
    for (const gt of gates) {
      const up = t >= gt.start ? clamp((t - gt.start) / 0.22, 0, 1) : 0;
      const down = gt.until !== Infinity && t > gt.until ? clamp((t - gt.until) / 0.2, 0, 1) : 0;
      gt.open = up * (1 - down);
    }

    // anneaux qui s'effondrent
    if ((phase === PHASE.R3 || phase === PHASE.FINAL) && t >= nextRing && rings.length < P.rings) {
      const rg = { t: t + 1.1, phi0: rng() * Math.PI * 2, dir: rng() < 0.5 ? 1 : -1, dur: 1.0 };
      rings.push(rg);
      events.push({ t, type: 'ringWarn', k: rings.length - 1, at: rg.t, phi0: rg.phi0, dir: rg.dir, dur: rg.dur });
      nextRing = t + 1.1 + 3.0 / (0.25 + dS);
    }

    // bras rotatif
    if (phase >= PHASE.R2 && phase < PHASE.WIN) {
      armExt = clamp((t - armT) / 1.3, 0, 1);
      // Sans barrière, une bille poussée par le bras s'échappe dès que ω² > (5/7)·g·2k (≈ 0,53 rad/s) :
      // en manche 3 et en finale, la vitesse du bras est donc le levier principal.
      let target = phase === PHASE.R2 ? 1.5 * (0.2 + 0.8 * Math.min(dS, 1.6))
        : phase === PHASE.R3 ? 0.3 + 0.38 * Math.min(dS, 2)
        : 0.3 + 0.45 * Math.min(dS, 2.2);
      if (phase === PHASE.FINAL && t < finalT + P.finalSetup) target = 0;
      if (t < calmUntil) target = 0;
      if (armExt < 1) target *= armExt;
      if (t >= nextArmFlip && phase >= PHASE.R3) { armDir = -armDir; nextArmFlip = t + 5 + rng() * 5; events.push({ t, type: 'armFlip' }); }
      const tw = target * armDir;
      armW += clamp(tw - armW, -2.2 * dt, 2.2 * dt);
    } else if (phase === PHASE.WIN) {
      armW += clamp(-armW, -2.5 * dt, 2.5 * dt);
    }
    armA += armW * dt;
    const L = (P.R0 - 0.06) * (0.12 + 0.88 * armExt);
    const armOn = phase >= PHASE.R2 && armExt > 0.05;

    // inclinaison
    let ampDeg = 0;
    if (phase === PHASE.DROP) ampDeg = 0;
    else if (phase === PHASE.FINAL && t < finalT + P.finalSetup) ampDeg = 0;
    else if (t < calmUntil) ampDeg = 1.5;
    else if (phase === PHASE.R1) ampDeg = (3.2 + 2.6 * dS) * smooth((t - 1.6) / 1.4);
    else if (phase === PHASE.R2) ampDeg = 3.0 + 2.4 * dS;
    else if (phase === PHASE.R3) ampDeg = 3.0 + 2.4 * dS;
    else if (phase === PHASE.FINAL) ampDeg = 3.2 + 2.4 * dS;
    ampDeg = Math.min(ampDeg, 7.2);
    if (phase === PHASE.WIN) tiltAmp += (0 - tiltAmp) * (dt / 0.45);
    else tiltAmp += (ampDeg - tiltAmp) * (dt / 0.6);
    const amp = (tiltAmp * Math.PI) / 180;
    const f = 0.3 + 0.05 * dS;
    huntW += ((t < huntUntil ? 0.75 : 0) - huntW) * (dt / 0.35);
    const nx0 = clamp(nA(t * f) * 1.25 + 0.35 * nC(t * f * 2.7), -1, 1);
    const nz0 = clamp(nB(t * f) * 1.25 + 0.35 * nD(t * f * 2.7), -1, 1);
    const tx = amp * ((1 - huntW) * nx0 + huntW * dcos(huntDir));
    const tz = amp * ((1 - huntW) * nz0 + huntW * dsin(huntDir));
    const Qp = tiltQuat(tx, tz);
    const gl = qrot(qconj(Qp), [0, -g, 0]);

    // ----- intégration -----
    for (const b of balls) {
      if (b.s === STATE.FALL) {
        if (b.pw[1] > -14) {
          b.vw[1] -= g * dt;
          for (let c = 0; c < 3; c++) b.pw[c] += b.vw[c] * dt;
          b.qw = qintegrate(b.qw, b.ww, dt);
        }
        continue;
      }
      if (b.s === STATE.AIR) {
        for (let c = 0; c < 3; c++) { b.v[c] += gl[c] * dt; b.p[c] += b.v[c] * dt; }
        b.q = qintegrate(b.q, b.w, dt);
        const rho = dhyp(b.p[0], b.p[2]);
        const ys = P.k * rho * rho + r;
        if (b.p[1] <= ys && rho <= effRadius(rings, datan2(b.p[2], b.p[0]), t)) {
          b.p[1] = ys;
          if (b.v[1] < 0) {
            const vi = -b.v[1];
            if (vi > 0.25) events.push({ t, type: 'land', i: b.i, v: vi });
            b.v[1] = vi * P.eFloor;
            b.v[0] *= 0.93; b.v[2] *= 0.93;
            if (b.v[1] < 0.3) { b.v[1] = 0; b.s = STATE.ROLL; }
          }
        }
        continue;
      }
      // roulement sur la cuvette (bille pleine : a = 5/7 · g tangentiel)
      const x0 = b.p[0], z0 = b.p[2];
      let nx = -2 * P.k * x0, ny = 1, nz = -2 * P.k * z0;
      const nl = dhyp3(nx, ny, nz); nx /= nl; ny /= nl; nz /= nl;
      const gn = gl[0] * nx + gl[1] * ny + gl[2] * nz;
      let ax = (5 / 7) * (gl[0] - gn * nx), az = (5 / 7) * (gl[2] - gn * nz);
      const vx = b.v[0], vz = b.v[2];
      const sp = dhyp(vx, vz);
      const lin = (phase === PHASE.WIN && b.i === winner) || (phase === PHASE.FINAL && t < finalT + P.finalSetup - 0.6) ? 1.8 : P.lin;
      if (sp > 1e-4) { ax -= (P.crr * g * vx) / sp + lin * vx; az -= (P.crr * g * vz) / sp + lin * vz; }
      b.v[0] += ax * dt; b.v[2] += az * dt;
      b.p[0] += b.v[0] * dt; b.p[2] += b.v[2] * dt;
      b.p[1] = P.k * (b.p[0] * b.p[0] + b.p[2] * b.p[2]) + r;
      b.v[1] = 2 * P.k * (b.p[0] * b.v[0] + b.p[2] * b.v[2]);
      b.w = [(ny * b.v[2] - nz * b.v[1]) / r, (nz * b.v[0] - nx * b.v[2]) / r, (nx * b.v[1] - ny * b.v[0]) / r];
      b.q = qintegrate(b.q, b.w, dt);
    }

    // collisions bille/bille
    for (let i = 0; i < N; i++) {
      const A = balls[i];
      if (A.s === STATE.FALL) continue;
      for (let j = i + 1; j < N; j++) {
        const B = balls[j];
        if (B.s === STATE.FALL) continue;
        const dx = B.p[0] - A.p[0], dy = B.p[1] - A.p[1], dz = B.p[2] - A.p[2];
        const d2 = dx * dx + dy * dy + dz * dz;
        if (d2 >= 4 * r * r || d2 < 1e-12) continue;
        const dist = Math.sqrt(d2);
        let nx = dx / dist, ny = dy / dist, nz = dz / dist;
        const bothRoll = A.s === STATE.ROLL && B.s === STATE.ROLL;
        if (bothRoll) { const l = dhyp(nx, nz) || 1; nx /= l; nz /= l; ny = 0; }
        const pen = 2 * r - dist;
        const ca = A.s === STATE.ROLL ? [1, 0, 1] : [1, 1, 1];
        const cb = B.s === STATE.ROLL ? [1, 0, 1] : [1, 1, 1];
        A.p[0] -= nx * pen * 0.5 * ca[0]; A.p[1] -= ny * pen * 0.5 * ca[1]; A.p[2] -= nz * pen * 0.5 * ca[2];
        B.p[0] += nx * pen * 0.5 * cb[0]; B.p[1] += ny * pen * 0.5 * cb[1]; B.p[2] += nz * pen * 0.5 * cb[2];
        const vn = (B.v[0] - A.v[0]) * nx + (B.v[1] - A.v[1]) * ny + (B.v[2] - A.v[2]) * nz;
        if (vn < 0) {
          const J = (-(1 + P.eBall) * vn) / 2;
          A.v[0] -= J * nx * ca[0]; A.v[1] -= J * ny * ca[1]; A.v[2] -= J * nz * ca[2];
          B.v[0] += J * nx * cb[0]; B.v[1] += J * ny * cb[1]; B.v[2] += J * nz * cb[2];
          if (-vn > 0.12) {
            const key = i * 64 + j, lt = lastPair.get(key) || -1;
            if (t - lt > 0.03) {
              events.push({ t, type: 'bb', i, j, v: -vn });
              lastPair.set(key, t);
            }
          }
        }
      }
    }

    // barrières, moyeu, bras, bord
    for (const b of balls) {
      if (b.s === STATE.FALL || (b.s === STATE.AIR && phase !== PHASE.DROP && b.p[1] > P.wallH + r * 0.6)) continue;
      const x = b.p[0], z = b.p[2];
      const rho = dhyp(x, z);
      const phi = datan2(z, x);
      // moyeu central
      if (rho < P.hubR + r) {
        const nx = x / (rho || 1), nz = z / (rho || 1);
        b.p[0] = nx * (P.hubR + r); b.p[2] = nz * (P.hubR + r);
        const vn = b.v[0] * nx + b.v[2] * nz;
        if (vn < 0) { b.v[0] -= (1 + P.eWall) * vn * nx; b.v[2] -= (1 + P.eWall) * vn * nz; if (-vn > 0.2) events.push({ t, type: 'wall', i: b.i, v: -vn }); }
      }
      // barrières (arcs + extrémités), uniquement tant que l'anneau extérieur existe
      if (rho > P.R0 - P.wallT - r - 0.02 && !(allDown && gates.every((gt) => gt.open >= 0.6))) {
        const Rc = P.R0 - P.wallT / 2;
        for (let k = 0; k < P.nGates; k++) {
          if (!gateBlocks(k)) continue;
          const [a0, a1] = gateAngles(k);
          let ph = phi < 0 ? phi + 2 * Math.PI : phi;
          let cx, cz;
          if (ph >= a0 && ph <= a1) { cx = Rc * dcos(ph); cz = Rc * dsin(ph); }
          else {
            const d0 = Math.min(Math.abs(ph - a0), 2 * Math.PI - Math.abs(ph - a0));
            const d1 = Math.min(Math.abs(ph - a1), 2 * Math.PI - Math.abs(ph - a1));
            const a = d0 < d1 ? a0 : a1;
            cx = Rc * dcos(a); cz = Rc * dsin(a);
          }
          const ex = b.p[0] - cx, ez = b.p[2] - cz;
          const dd = dhyp(ex, ez);
          const lim = r + P.wallT / 2;
          if (dd < lim && dd > 1e-9) {
            const nx = ex / dd, nz = ez / dd;
            b.p[0] = cx + nx * lim; b.p[2] = cz + nz * lim;
            const vn = b.v[0] * nx + b.v[2] * nz;
            if (vn < 0) {
              b.v[0] -= (1 + P.eWall) * vn * nx; b.v[2] -= (1 + P.eWall) * vn * nz;
              if (-vn > 0.2) events.push({ t, type: 'wall', i: b.i, v: -vn });
            }
          }
        }
      }
      // bras rotatif (deux côtés)
      if (armOn) {
        const ux = dcos(armA), uz = dsin(armA);
        const s = clamp(b.p[0] * ux + b.p[2] * uz, -L, L);
        const cx = s * ux, cz = s * uz;
        const ex = b.p[0] - cx, ez = b.p[2] - cz;
        const dd = dhyp(ex, ez);
        const lim = r + P.armW;
        if (dd < lim && dd > 1e-9) {
          const nx = ex / dd, nz = ez / dd;
          b.p[0] = cx + nx * lim; b.p[2] = cz + nz * lim;
          const vax = armW * s * -dsin(armA), vaz = armW * s * dcos(armA);
          const vn = (b.v[0] - vax) * nx + (b.v[2] - vaz) * nz;
          if (vn < 0) {
            b.v[0] -= (1 + P.eArm) * vn * nx; b.v[2] -= (1 + P.eArm) * vn * nz;
            if (-vn > 0.25) events.push({ t, type: 'arm', i: b.i, v: -vn });
          }
        }
      }
      // bord du plateau
      const rho2 = dhyp(b.p[0], b.p[2]);
      const phi2 = datan2(b.p[2], b.p[0]);
      const Re = effRadius(rings, phi2, t);
      const edge = Re - rho2;
      if (alive > 1) {
        // quasi-sortie : bille à moins de 12 cm d'un bord ouvert
        let open = allDown;
        if (!open) { let ph = phi2 < 0 ? phi2 + 2 * Math.PI : phi2; const k = Math.floor(ph / ((2 * Math.PI) / P.nGates)) % P.nGates; open = !gateBlocks(k); }
        if (open) {
          b.minEdge = Math.min(b.minEdge, edge);
          if (edge < 0.1 && edge > 0 && t - b.lastNear > 1.2) { b.nearMiss++; b.lastNear = t; }
        }
      }
      const fence = phase === PHASE.FINAL && t < finalT + P.finalSetup;
      if (rho2 > Re) {
        if ((alive <= 1 && b.i === winner) || fence) {
          // le vainqueur ne peut plus tomber
          const nx = b.p[0] / rho2, nz = b.p[2] / rho2;
          b.p[0] = nx * (Re - 0.001); b.p[2] = nz * (Re - 0.001);
          const vn = b.v[0] * nx + b.v[2] * nz;
          if (vn > 0) { b.v[0] -= 1.2 * vn * nx; b.v[2] -= 1.2 * vn * nz; }
          continue;
        }
        // chute : passage dans le repère monde
        b.s = STATE.FALL;
        b.pw = qrot(Qp, b.p);
        const vw = qrot(Qp, b.v);
        b.vw = [vw[0] * 1.02, vw[1] - 0.05, vw[2] * 1.02];
        b.qw = qmul(Qp, b.q);
        b.ww = qrot(Qp, b.w);
        b.elimT = t; b.rank = alive;
        elims.push({ t, i: b.i, rank: alive, x: b.pw[0], y: b.pw[1], z: b.pw[2] });
        events.push({ t, type: 'elim', i: b.i, rank: alive });
        alive--;
        // la porte franchie se referme aussitôt : une porte = une élimination
        if (!rings.length) {
          const ph = phi2 < 0 ? phi2 + 2 * Math.PI : phi2;
          const gt = gates[Math.floor(ph / ((2 * Math.PI) / P.nGates)) % P.nGates];
          if (!gt.perm && gt.until > t + 0.06) gt.until = t + 0.06;
        }
        if (alive === 1) {
          winner = balls.find((o) => o.s !== STATE.FALL).i;
          events.push({ t, type: 'win', i: winner });
        }
      }
    }
    // balles en l'air hors plateau (rebond au départ) : chute
    for (const b of balls) {
      if (b.s === STATE.AIR && b.p[1] < P.k * (b.p[0] ** 2 + b.p[2] ** 2) + r - 0.02) {
        const rho = dhyp(b.p[0], b.p[2]);
        if (rho > effRadius(rings, datan2(b.p[2], b.p[0]), t)) {
          b.s = STATE.FALL; b.pw = qrot(Qp, b.p); b.vw = qrot(Qp, b.v); b.qw = qmul(Qp, b.q); b.ww = qrot(Qp, b.w);
          b.elimT = t; b.rank = alive;
          elims.push({ t, i: b.i, rank: alive, x: b.pw[0], y: b.pw[1], z: b.pw[2] });
          events.push({ t, type: 'elim', i: b.i, rank: alive });
          alive--;
        }
      }
    }

    // ----- enregistrement -----
    if (step % recEvery === 0) {
      const pos = new Float32Array(N * 3), rot = new Float32Array(N * 4), st = new Uint8Array(N);
      let energy = 0;
      for (const b of balls) {
        let pw, qw;
        if (b.s === STATE.FALL) { pw = b.pw; qw = b.qw; }
        else { pw = qrot(Qp, b.p); qw = qmul(Qp, b.q); energy += dhyp(b.v[0], b.v[2]) * (b.s === STATE.ROLL ? 1 : 0); }
        pos[b.i * 3] = pw[0]; pos[b.i * 3 + 1] = pw[1]; pos[b.i * 3 + 2] = pw[2];
        rot[b.i * 4] = qw[0]; rot[b.i * 4 + 1] = qw[1]; rot[b.i * 4 + 2] = qw[2]; rot[b.i * 4 + 3] = qw[3];
        st[b.i] = b.s === STATE.FALL ? 2 : b.i === winner && phase === PHASE.WIN ? 3 : b.s;
      }
      frames.push({
        t, pos, rot, st, Qp, armA, armExt, armW,
        gates: gates.map((gt) => (gt.open > 0 ? gt.open : t >= gt.warn && t < gt.start ? -1 : 0)), phase, d: dS, alive, energy, tilt: tiltAmp,
      });
    }

    t += dt; step++;
    if (winT !== Infinity && t > winT + 7) break;
  }

  // statistiques de dramaturgie (utilisées pour choisir les seeds)
  const et = elims.map((e) => e.t);
  const w = winner >= 0 ? balls[winner] : null;
  const stats = {
    duration: winT,
    finalDuel: et.length >= 31 ? et[30] - et[29] : 0,
    winner,
    winnerNearMiss: w ? w.nearMiss : 0,
    winnerMinEdge: w ? w.minEdge : 9,
    combos: et.filter((x, k) => k > 0 && x - et[k - 1] < 0.45).length,
    armKills: elims.filter((e) => events.some((ev) => ev.type === 'arm' && ev.i === e.i && e.t - ev.t < 0.8 && e.t >= ev.t)).length,
    pacingRms: Math.sqrt(elims.reduce((s, e, k) => s + (e.t - targetTime(k + 1)) ** 2, 0) / Math.max(1, elims.length)),
    maxGap: et.reduce((m, x, k) => (k > 0 && k < 29 ? Math.max(m, x - et[k - 1]) : m), 0),
  };

  return { seed, N, frames, events, elims, rings, winner, winT, stats, P };
}

// Interpolation d'un échantillon à un temps de simulation arbitraire
export function sampleAt(rec, t) {
  const f = clamp(t * P.recHz, 0, rec.frames.length - 1.001);
  const i = Math.floor(f), a = f - i;
  return { A: rec.frames[i], B: rec.frames[Math.min(i + 1, rec.frames.length - 1)], a };
}
