// Réalisateur automatique : transforme un enregistrement de simulation en montage vidéo.
// Pur JS (aucune dépendance au DOM ni à three.js) : même résultat dans Node et dans le navigateur.
//  - courbe de vitesse (ralentis), replay, célébration
//  - plans caméra (fonction pure du temps vidéo)
//  - voix off : candidats → planification avec priorités (durées réelles issues du TTS)
//  - sous-titres mot à mot, événements d'interface, liste d'effets sonores
import { P, PHASE, STATE, sampleAt, effRadius } from './sim.js';
import { COUNTRIES, cap } from './countries.js';

export const FPS = 30;
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const ease = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);

// ---------- textes de la voix off ----------
const ELIM_T = [
  (c) => `Adieu ${c.def} !`,
  (c) => `${cap(c.def)} ${c.plur ? 'tombent' : 'tombe'} !`,
  (c) => `${cap(c.def)}, c'est fini !`,
  (c) => `Bye bye ${c.def} !`,
  (c) => `Et ${c.def} ${c.plur ? 'dégagent' : 'dégage'} !`,
  (c) => `Pas de chance pour ${c.def} !`,
  (c) => `Ciao ${c.def} !`,
  (c) => `${cap(c.def)} ${c.plur ? 'sautent' : 'saute'} !`,
];
const ARM_T = [(c) => `Le bras éjecte ${c.def} !`, (c) => `Le bras balaie ${c.def} !`];

export const VOICE = { host: 'fr-FR-RemyMultilingualNeural' };

function hashN(a, b) { let h = (a * 73856093) ^ (b * 19349663); h = (h ^ (h >>> 13)) * 1274126177; return Math.abs(h ^ (h >>> 16)); }

// Analyse de l'enregistrement : éliminations, manches, événements marquants
export function analyse(rec) {
  const E = rec.elims.slice().sort((a, b) => a.t - b.t);
  const phases = {};
  for (const e of rec.events) if (e.type === 'phase') phases[e.phase] = e.t;
  const armHits = rec.events.filter((e) => e.type === 'arm');
  E.forEach((e, k) => {
    e.k = k;
    e.byArm = armHits.some((h) => h.i === e.i && e.t - h.t < 0.8 && e.t >= h.t && h.v > 0.8);
    const same = E.filter((o) => Math.abs(o.t - e.t) < 0.45);
    e.combo = same.length;
  });
  const tFinal = phases[PHASE.FINAL];
  const tWin = phases[PHASE.WIN];
  const loser = E[E.length - 1].i;
  return { E, phases, tFinal, tWin, finalists: [loser, rec.winner], loser };
}

// ---------- candidats de voix off (identiques dans Node et le navigateur) ----------
export function voiceCandidates(rec, A) {
  const C = COUNTRIES, out = [];
  const add = (o) => out.push({ voice: VOICE.host, rate: '+10%', pitch: '+0Hz', ...o });
  add({ id: 'hook', text: 'Trente-deux pays. Un seul survivant.', rate: '+6%', at: { v: 0.25 }, pr: 100, fixed: true });
  add({ id: 'choose', text: 'Choisis ton pays. Maintenant.', rate: '+8%', at: { after: 'hook', gap: 0.25 }, pr: 99, fixed: true });
  const E = A.E;
  let prevT = -1;
  E.forEach((e, k) => {
    if (k >= 29) return; // la finale a ses propres lignes
    const c = C[e.i];
    let text, pr = 40 + c.aud * 1.5 + (31 - e.rank) * 0.3;
    if (k === 0) { text = `Premier éliminé : ${c.def} !`; pr = 96; }
    else if (e.combo >= 2 && e.t - prevT < 0.45) return; // déjà couvert par l'annonce de combo
    else if (e.combo >= 3) { text = e.combo >= 4 ? 'Quadruple élimination !' : 'Triple élimination !'; pr = 88; }
    else if (e.combo === 2) {
      const o = C[E[k + 1] && Math.abs(E[k + 1].t - e.t) < 0.45 ? E[k + 1].i : E[k - 1].i];
      text = hashN(e.i, 11) % 3 === 0 ? 'Double élimination !' : `${cap(c.def)} et ${o.def} tombent ensemble !`;
      pr = 74 + (c.aud + o.aud) * 0.6;
    }
    else if (e.byArm && hashN(e.i, 3) % 2 === 0) { text = ARM_T[hashN(e.i, rec.seed) % ARM_T.length](c); pr += 10; }
    else text = ELIM_T[hashN(e.i + 7 * k, rec.seed) % ELIM_T.length](c);
    prevT = e.t;
    add({ id: `e${k}`, text, rate: '+14%', at: { sim: e.t + 0.12 }, pr, maxDelay: k === 0 ? 1.2 : 0.8, elim: k });
  });
  if (A.phases[PHASE.R2] !== undefined) add({ id: 'r2', text: 'Manche deux : le bras de la mort !', at: { sim: A.phases[PHASE.R2] + 0.1 }, pr: 95, maxDelay: 1.0, rate: '+6%' });
  if (A.phases[PHASE.R3] !== undefined) add({ id: 'r3', text: 'Manche trois : plus aucune barrière !', at: { sim: A.phases[PHASE.R3] + 0.1 }, pr: 95, maxDelay: 1.0, rate: '+6%' });
  const at = (rank) => { const e = E.find((x) => x.rank === rank); return e ? e.t : null; };
  const t10 = at(11); if (t10) add({ id: 'ten', text: 'Plus que dix !', at: { sim: t10 + 0.1 }, pr: 84, maxDelay: 1.0 });
  const t3 = at(4); if (t3) add({ id: 'three', text: 'Il en reste trois.', at: { sim: t3 + 0.1 }, pr: 86, maxDelay: 1.0, rate: '+2%' });
  const [a, b] = [COUNTRIES[A.loser], COUNTRIES[rec.winner]];
  const [f1, f2] = hashN(rec.seed, 5) % 2 ? [a, b] : [b, a];
  add({ id: 'final', text: `C'est la finale. ${cap(f1.def)} contre ${f2.def}.`, at: { sim: A.tFinal + 0.25 }, pr: 98, fixed: true, rate: '-4%' });
  add({ id: 'crack', text: 'Qui va craquer ?', at: { sim: A.tFinal + P.finalSetup + 1.6 }, pr: 70, maxDelay: 1.5, rate: '+0%' });
  const w = COUNTRIES[rec.winner];
  add({ id: 'win', text: `${cap(w.def)} ${w.plur ? 'gagnent' : 'gagne'} !`, at: { sim: A.tWin + 0.2 }, pr: 100, fixed: true, rate: '+4%', pitch: '+2Hz' });
  add({ id: 'replay', text: 'Regarde bien. Tout s\'est joué ici.', at: { seg: 'replay', off: 0.35 }, pr: 90, fixed: true, rate: '-2%' });
  add({ id: 'end', text: 'Et ton pays, il a fini où ?', at: { seg: 'board', off: 0.25 }, pr: 97, fixed: true, rate: '+4%' });
  return out;
}

// Voix de foule (fichiers génériques, communs à tous les épisodes)
export const CROWD_VOICES = ['fr-FR-DeniseNeural', 'fr-FR-HenriNeural', 'fr-FR-EloiseNeural', 'fr-FR-VivienneMultilingualNeural', 'fr-CA-SylvieNeural', 'fr-CA-JeanNeural', 'fr-CA-AntoineNeural', 'fr-CA-ThierryNeural', 'fr-BE-CharlineNeural', 'fr-BE-GerardNeural', 'fr-CH-ArianeNeural', 'fr-CH-FabriceNeural'];
export const CROWD_LINES = {
  oh: 'Ooooh !', non: 'Nooon !', ouais: 'Ouaiiis !',
  b1: 'Allez, allez !', b2: 'Oh là là, regarde !', b3: 'Il va tomber !', b4: 'Vas-y, vas-y !', b5: "C'est chaud !", b6: 'Mais non !',
};

// ---------- construction du montage ----------
export function buildDirector(rec, manifest = null, opts = {}) {
  const A = analyse(rec);
  const { E, tFinal, tWin } = A;
  const S0 = 0.28;

  // Courbe de vitesse de la partie « live » (ralentis en creux gaussiens)
  const dips = [];
  let lastDip = -99;
  for (const e of E) {
    if (e.k >= 29) break;
    const strong = e.byArm || e.combo >= 3;
    if (strong && e.t - lastDip > 6 && e.t > 6) { dips.push({ c: e.t + 0.05, depth: 0.5, w: 0.22 }); lastDip = e.t; }
  }
  dips.push({ c: tWin + 0.02, depth: 0.8, w: 0.42 });              // la chute décisive au ralenti
  const liveEnd = tWin + 1.25;
  const speed = (s) => {
    let v = s > tFinal + P.finalSetup && s < tWin + 0.3 ? 0.9 : 1;
    for (const d of dips) v *= 1 - d.depth * Math.exp(-0.5 * ((s - d.c) / d.w) ** 2);
    return Math.max(v, 0.12);
  };
  const ds = 1 / 960, tabS = [S0], tabV = [0];
  for (let s = S0; s < liveEnd; s += ds) { tabS.push(s + ds); tabV.push(tabV[tabV.length - 1] + ds / speed(s + ds / 2)); }
  const vLive = tabV[tabV.length - 1];
  const vOfSimLive = (s) => {
    if (s <= S0) return 0; if (s >= liveEnd) return vLive;
    const f = (s - S0) / ds, i = Math.floor(f), a = f - i;
    return lerp(tabV[i], tabV[Math.min(i + 1, tabV.length - 1)], a);
  };
  const simOfVLive = (v) => {
    let lo = 0, hi = tabV.length - 1;
    if (v <= 0) return S0; if (v >= vLive) return liveEnd;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (tabV[m] <= v) lo = m; else hi = m; }
    const a = (v - tabV[lo]) / (tabV[hi] - tabV[lo] || 1);
    return lerp(tabS[lo], tabS[hi], a);
  };

  const RP = { s0: tWin - 1.35, s1: tWin + 0.3, rate: 0.4 };
  const vReplay0 = vLive, vReplay1 = vReplay0 + (RP.s1 - RP.s0) / RP.rate;
  const CEL = 5.6;
  const vCel0 = vReplay1, vEnd = vCel0 + CEL;
  const vBoard = vEnd - 3.9;
  const segs = [
    { kind: 'live', v0: 0, v1: vLive, s0: S0, s1: liveEnd },
    { kind: 'replay', v0: vReplay0, v1: vReplay1, s0: RP.s0, s1: RP.s1 },
    { kind: 'celebrate', v0: vCel0, v1: vEnd, s0: liveEnd, s1: liveEnd + CEL },
  ];
  const segAt = (v) => segs.find((g) => v < g.v1) || segs[segs.length - 1];
  function simAt(v) {
    const g = segAt(v);
    if (g.kind === 'live') return { s: simOfVLive(v), g };
    const s = g.s0 + (v - g.v0) * ((g.s1 - g.s0) / (g.v1 - g.v0));
    return { s, g };
  }
  const vOfSim = (s) => vOfSimLive(s);
  const vPhase = (ph) => (A.phases[ph] !== undefined ? vOfSim(A.phases[ph]) : null);

  // ---------- voix off : planification ----------
  const cands = voiceCandidates(rec, A);
  const segStart = { replay: vReplay0, board: vBoard };
  const lines = [];
  const dur = (c) => (manifest && manifest.lines[c.id] ? manifest.lines[c.id].dur : estDur(c.text));
  const placed = [];
  const free = (a, b) => placed.every((p) => b + 0.12 <= p.v || a >= p.v + p.dur + 0.12);
  const want = (c) => (c.at.v !== undefined ? c.at.v : c.at.sim !== undefined ? vOfSim(c.at.sim) : c.at.seg ? segStart[c.at.seg] + c.at.off : null);
  const key = (c) => (c.at.after ? want(cands.find((q) => q.id === c.at.after)) + 0.001 : want(c));
  const fixed = cands.filter((c) => c.fixed).sort((x, y) => key(x) - key(y));
  for (const c of fixed) {
    let v = c.at.after ? (() => { const p = placed.find((q) => q.id === c.at.after); return p.v + p.dur + c.at.gap; })() : want(c);
    for (const p of placed) if (v < p.v + p.dur + 0.1 && v + dur(c) > p.v) v = p.v + p.dur + 0.1;
    placed.push({ ...c, v, dur: dur(c) });
  }
  const rest = cands.filter((c) => !c.fixed).sort((x, y) => y.pr - x.pr);
  for (const c of rest) {
    const w0 = want(c), d = dur(c);
    for (let dv = 0; dv <= (c.maxDelay || 0.6); dv += 0.05) {
      const v = w0 + dv;
      if (v + d > vReplay0 - 0.05 && !(c.id === 'crack')) break;
      if (free(v, v + d)) { placed.push({ ...c, v, dur: d }); break; }
    }
  }
  placed.sort((a, b) => a.v - b.v);
  for (const p of placed) {
    const m = manifest && manifest.lines[p.id];
    const words = m ? m.words.map((w) => ({ w: w.w, t: p.v + w.t, d: w.d })) : fakeWords(p.text, p.v, p.dur);
    lines.push({ id: p.id, text: p.text, v: p.v, dur: p.dur, file: m ? m.file : null, words, elim: p.elim });
  }

  // ---------- sous-titres (groupes de 1 à 3 mots, style TikTok) ----------
  const captions = [];
  for (const L of lines) {
    let chunk = [];
    const flush = () => {
      if (!chunk.length) return;
      captions.push({ v0: chunk[0].t, v1: chunk[chunk.length - 1].t + chunk[chunk.length - 1].d, words: chunk.map((w) => ({ ...w })), line: L.id });
      chunk = [];
    };
    for (const w of L.words) {
      chunk.push(w);
      const len = chunk.map((x) => x.w).join(' ').length;
      if (chunk.length >= 3 || len > 13 || /[.!?:,]$/.test(w.w)) flush();
    }
    flush();
  }
  for (let i = 0; i < captions.length - 1; i++) captions[i].v1 = Math.min(Math.max(captions[i].v1 + 0.25, captions[i].v1), captions[i + 1].v0);

  // ---------- centroïde lissé des billes en jeu (cadrage « opérateur ») ----------
  const track = [];
  const tr = 30;
  for (let s = 0; s <= rec.frames[rec.frames.length - 1].t; s += 1 / tr) {
    const f = rec.frames[Math.min(rec.frames.length - 1, Math.round(s * P.recHz))];
    let x = 0, z = 0, n = 0;
    for (let i = 0; i < rec.N; i++) if (f.st[i] !== STATE.FALL) { x += f.pos[i * 3]; z += f.pos[i * 3 + 2]; n++; }
    x /= n || 1; z /= n || 1;
    let sp = 0;
    for (let i = 0; i < rec.N; i++) if (f.st[i] !== STATE.FALL) sp = Math.max(sp, Math.hypot(f.pos[i * 3] - x, f.pos[i * 3 + 2] - z));
    track.push([x, z, sp]);
  }
  for (const pass of [0, 1]) {
    const a = 1 - Math.exp(-1 / (tr * 0.7));
    const idx = pass ? [...track.keys()].reverse() : [...track.keys()];
    let cur = track[idx[0]].slice();
    for (const i of idx) { for (let c = 0; c < 3; c++) cur[c] += (track[i][c] - cur[c]) * a; track[i] = cur.slice(); }
  }
  const trackAt = (s) => {
    const f = clamp(s * tr, 0, track.length - 1.001), i = Math.floor(f), a = f - i;
    return [0, 1, 2].map((c) => lerp(track[i][c], track[i + 1][c], a));
  };

  // position d'une bille (monde) à un instant de simulation
  const ballPos = (i, s) => {
    const { A: fa, B: fb, a } = sampleAt(rec, s);
    return [0, 1, 2].map((c) => lerp(fa.pos[i * 3 + c], fb.pos[i * 3 + c], a));
  };

  // ---------- élévation du vainqueur pendant la célébration ----------
  const W = rec.winner;
  const liftK = (v) => ease((v - vCel0 - 0.25) / 1.4);
  const LIFT = [0, 0.95, 0];
  function winnerOverride(v) {
    if (v < vCel0) return null;
    const k = liftK(v);
    const base = ballPos(W, liveEnd);
    const bob = Math.sin((v - vCel0) * 2.2) * 0.03 * k;
    return { pos: [lerp(base[0], LIFT[0], k), lerp(base[1], LIFT[1], k) + bob, lerp(base[2], LIFT[2], k)], spin: (v - vCel0) * 1.6 * k, k };
  }

  // ---------- plan de tournage ----------
  const shots = [];
  const vR2 = vPhase(PHASE.R2), vR3 = vPhase(PHASE.R3), vFin = vOfSim(tFinal), vWin = vOfSim(tWin);
  shots.push({ v: 0, type: 'intro' });
  shots.push({ v: 2.9, type: 'broadcast', blend: 0.9 });
  // zooms « coup de poing » sur certaines éliminations (pas plus d'un toutes les 3,2 s)
  let lastPunch = 3;
  const bans = [vR2, vR3].filter((x) => x !== null);
  for (const e of E) {
    if (e.k >= 29) break;
    const v = vOfSim(e.t);
    const important = e.k === 0 || e.byArm || e.combo >= 2 || COUNTRIES[e.i].aud >= 9 || e.rank <= 12;
    if (!important || v - lastPunch < 3.2 || bans.some((b) => v > b - 0.8 && v < b + 2.4) || v > vFin - 1.5) continue;
    shots.push({ v: v - 0.18, type: 'punch', ball: e.i, s: e.t, blend: 0.22 });
    shots.push({ v: v + 1.15, type: 'broadcast', blend: 0.45 });
    lastPunch = v;
  }
  if (vR2 !== null) { shots.push({ v: vR2 - 0.05, type: 'sweep', dir: 1, blend: 0.35 }); shots.push({ v: vR2 + 2.3, type: 'broadcast', blend: 0.7 }); }
  if (vR3 !== null) { shots.push({ v: vR3 - 0.05, type: 'sweep', dir: -1, blend: 0.35 }); shots.push({ v: vR3 + 2.5, type: 'broadcast', blend: 0.7 }); }
  shots.push({ v: vFin - 0.1, type: 'duel', blend: 0.5 });
  shots.push({ v: vOfSim(tWin - 0.7), type: 'kill', ball: A.loser, blend: 0.5 });
  shots.push({ v: vReplay0, type: 'replay', ball: A.loser, blend: 0 });
  shots.push({ v: vCel0, type: 'winner', blend: 0 });
  shots.sort((a, b) => a.v - b.v);
  // on retire les plans écrasés par un plan de priorité supérieure
  const clean = [];
  for (const sh of shots) { if (clean.length && Math.abs(clean[clean.length - 1].v - sh.v) < 0.01) clean.pop(); clean.push(sh); }

  const elimPoint = (i) => { const e = E.find((x) => x.i === i); return e ? [e.x, 0.15, e.z] : [0, 0, 0]; };

  function rig(sh, v) {
    const { s } = simAt(v);
    const [cx, cz, spread] = trackAt(Math.min(s, liveEnd));
    const yawBase = 0.62 + v * 0.085;
    const R = (yaw, pitch, dist, tgt, fov) => {
      const cp = Math.cos(pitch);
      return { eye: [tgt[0] + Math.sin(yaw) * cp * dist, tgt[1] + Math.sin(pitch) * dist, tgt[2] + Math.cos(yaw) * cp * dist], tgt, fov };
    };
    switch (sh.type) {
      case 'intro': {
        const k = easeOut(v / 3.0);
        return { ...R(yawBase - 0.5 * (1 - k), lerp(0.34, 1.06, k), lerp(4.8, 6.9, k), [0, lerp(0.55, 0.05, k), 0], lerp(46, 46, k)), focus: null };
      }
      case 'broadcast': {
        const tgt = [lerp(0, cx, 0.5), 0.05, lerp(0, cz, 0.5)];
        const dist = clamp(3.3 + spread * 2.1, 3.7, 6.9);
        return { ...R(yawBase, 1.1, dist, tgt, 46), focus: null };
      }
      case 'punch': {
        const p = elimPoint(sh.ball);
        const k = easeOut((v - sh.v) / 0.3);
        const tgt = [lerp(cx * 0.4, p[0] * 0.8, k), 0.1, lerp(cz * 0.4, p[2] * 0.8, k)];
        return { ...R(yawBase, lerp(1.1, 0.74, k), lerp(5.6, 2.8, k), tgt, lerp(46, 42, k)), focus: p };
      }
      case 'sweep': {
        const k = (v - sh.v) / 2.4;
        return { ...R(yawBase + sh.dir * (0.2 + k * 0.9), lerp(0.36, 0.62, k), lerp(3.6, 4.6, k), [0, 0.1, 0], 50), focus: [0, 0.2, 0] };
      }
      case 'duel': {
        const a = ballPos(A.loser, Math.min(s, tWin)), b = ballPos(W, Math.min(s, tWin));
        const mid = [(a[0] + b[0]) / 2 * 0.8, 0.12, (a[2] + b[2]) / 2 * 0.8];
        const sep = Math.hypot(a[0] - b[0], a[2] - b[2]);
        return { ...R(yawBase * 0.8 + 0.3, 0.84, clamp(2.5 + sep * 1.2, 3.0, 5.0), mid, 46), focus: mid };
      }
      case 'kill': {
        const p = ballPos(sh.ball, Math.min(s, tWin + 0.4));
        const tgt = [p[0] * 0.85, Math.max(p[1], -0.4) * 0.5 + 0.08, p[2] * 0.85];
        const phi = Math.atan2(p[0], p[2]);
        return { ...R(phi + 0.9, 0.42, 2.1, tgt, 40), focus: p };
      }
      case 'replay': {
        const p = ballPos(sh.ball, s);
        const e = elimPoint(sh.ball);
        const phi = Math.atan2(e[0], e[2]);
        const k = (v - sh.v) / (vReplay1 - vReplay0);
        const eye = [Math.sin(phi + 0.55 - k * 0.25) * 2.9, 0.42 - k * 0.2, Math.cos(phi + 0.55 - k * 0.25) * 2.9];
        return { eye, tgt: [p[0], Math.max(p[1], -1.2), p[2]], fov: 34, focus: p };
      }
      case 'winner': {
        const o = winnerOverride(v);
        const tgt = o ? [o.pos[0], o.pos[1], o.pos[2]] : [0, 0.5, 0];
        const k = ease((v - vCel0) / 1.6);
        return { ...R(1.2 + (v - vCel0) * 0.42, lerp(0.35, 0.12, k), lerp(2.6, 1.35, k), tgt, lerp(40, 34, k)), focus: tgt };
      }
    }
  }

  function camAt(v) {
    let i = 0;
    while (i + 1 < clean.length && clean[i + 1].v <= v) i++;
    const cur = clean[i];
    let c = rig(cur, v);
    const prev = clean[i - 1];
    if (prev && cur.blend > 0 && v - cur.v < cur.blend) {
      const k = ease((v - cur.v) / cur.blend);
      const p = rig(prev, v);
      c = { eye: c.eye.map((x, j) => lerp(p.eye[j], x, k)), tgt: c.tgt.map((x, j) => lerp(p.tgt[j], x, k)), fov: lerp(p.fov, c.fov, k), focus: k > 0.5 ? c.focus : p.focus };
    }
    // bougé « caméra à l'épaule » + secousses d'impact
    let shake = 0.0025;
    for (const e of E) { const ve = vOfSim(e.t); if (v >= ve && v < ve + 0.6) shake += 0.012 * Math.exp(-(v - ve) * 7); }
    for (const ph of [vR2, vR3, vWin]) if (ph !== null && v >= ph && v < ph + 0.8) shake += 0.03 * Math.exp(-(v - ph) * 5);
    c.shake = shake;
    c.type = cur.type;
    return c;
  }

  // ---------- interface ----------
  const toasts = E.slice(0, 30).map((e) => ({ v: vOfSim(e.t), i: e.i, rank: e.rank, byArm: e.byArm, combo: e.combo }));
  const banners = [];
  banners.push({ v: 0.05, dur: 2.5, kind: 'hook', title: '32 PAYS', sub: '1 SEUL SURVIVANT' });
  if (vR2 !== null) banners.push({ v: vR2, dur: 2.0, kind: 'round', title: 'MANCHE 2', sub: 'LE BRAS DE LA MORT' });
  if (vR3 !== null) banners.push({ v: vR3, dur: 2.0, kind: 'round', title: 'MANCHE 3', sub: 'PLUS DE BARRIÈRES' });
  banners.push({ v: vFin, dur: 2.2, kind: 'final', title: 'FINALE' });
  const hud = {
    chooseV: [2.55, 4.6],
    vFin, vWin, vReplay0, vReplay1, vCel0, vBoard, vEnd, vR2, vR3,
    toasts, banners,
  };

  // ---------- effets sonores (temps vidéo) ----------
  const sfx = [];
  const mapEvent = (s) => {
    const out = [];
    if (s >= S0 && s <= liveEnd) out.push({ v: vOfSimLive(s), rate: speed(s), seg: 'live' });
    if (s >= RP.s0 && s <= RP.s1) out.push({ v: vReplay0 + (s - RP.s0) / RP.rate, rate: RP.rate, seg: 'replay' });
    return out;
  };
  for (const ev of rec.events) {
    for (const m of mapEvent(ev.t)) {
      const base = { v: m.v, rate: m.rate, seg: m.seg };
      if (ev.type === 'bb') sfx.push({ ...base, type: 'click', gain: clamp(ev.v / 2.5, 0.05, 1), key: hashN(ev.i, ev.j) % 1000, x: ballPos(ev.i, ev.t)[0] });
      else if (ev.type === 'land') sfx.push({ ...base, type: 'land', gain: clamp(ev.v / 5, 0.1, 1), key: ev.i, x: ballPos(ev.i, ev.t)[0] });
      else if (ev.type === 'wall') sfx.push({ ...base, type: 'wall', gain: clamp(ev.v / 2, 0.08, 1), key: ev.i, x: ballPos(ev.i, ev.t)[0] });
      else if (ev.type === 'arm') sfx.push({ ...base, type: 'arm', gain: clamp(ev.v / 2.5, 0.15, 1), key: ev.i, x: ballPos(ev.i, ev.t)[0] });
      else if (ev.type === 'gateWarn') { sfx.push({ ...base, type: 'alarm', gain: 0.5, key: ev.k }); const m2 = mapEvent(ev.at)[0]; if (m2 && m2.seg === m.seg) sfx.push({ v: m2.v, rate: m2.rate, seg: m.seg, type: 'gate', gain: 0.7, key: ev.k }); }
      else if (ev.type === 'wallsDown') sfx.push({ ...base, type: 'wallsDown', gain: 1 });
      else if (ev.type === 'ringWarn') { sfx.push({ ...base, type: 'siren', gain: 0.8 }); const m2 = mapEvent(ev.at)[0]; if (m2) sfx.push({ v: m2.v, rate: m2.rate, seg: m.seg, type: 'crumble', gain: 1, dur: ev.dur / m2.rate }); }
      else if (ev.type === 'elim') sfx.push({ ...base, type: 'elim', gain: 1, key: ev.i, rank: ev.rank, x: ballPos(ev.i, ev.t)[0] });
      else if (ev.type === 'phase') sfx.push({ ...base, type: 'phase', phase: ev.phase, gain: 1 });
    }
  }
  // Transitions de montage
  for (const sh of clean) if (sh.type === 'punch') sfx.push({ v: sh.v, type: 'whoosh', gain: 0.55 });
  sfx.push({ v: vReplay0, type: 'rewind', gain: 1 });
  sfx.push({ v: vCel0, type: 'impact', gain: 1 });
  sfx.push({ v: vBoard, type: 'boardIn', gain: 0.9 });
  sfx.sort((a, b) => a.v - b.v);

  // Réactions de la foule
  const crowd = [];
  for (const e of E) {
    const v = vOfSim(e.t);
    if (e.byArm || e.combo >= 2 || e.rank <= 6) crowd.push({ v: v + 0.1, kind: e.rank <= 3 ? 'non' : 'oh', gain: e.rank <= 6 ? 0.9 : 0.6 });
  }
  crowd.push({ v: vWin + 0.05, kind: 'cheer', gain: 1 });
  crowd.push({ v: vCel0 + 0.1, kind: 'cheer', gain: 0.8 });

  // Intensité d'ambiance (0-1) pour la musique et la rumeur de foule
  const intensity = (v) => {
    const { s, g } = simAt(v);
    if (g.kind === 'replay') return 0.35;
    if (g.kind === 'celebrate') return 1;
    if (s < 2.2) return 0.35;
    if (s < (A.phases[PHASE.R2] ?? 99)) return 0.55;
    if (s < (A.phases[PHASE.R3] ?? 99)) return 0.7;
    if (s < tFinal) return 0.85;
    return 0.95;
  };

  // ---------- découpage en scènes (JSON de production) ----------
  const scenes = buildScenes({ lines, banners, shots: clean, vEnd, vReplay0, vCel0, vBoard, E, vOfSim });

  return {
    rec, A, fps: FPS, duration: vEnd, segs, simAt, vOfSim, speed,
    lines, captions, camAt, shots: clean, hud, sfx, crowd, intensity,
    winnerOverride, ballPos, liveEnd, S0, RP, scenes, candidates: cands,
  };
}

function estDur(text) { return 0.35 + text.split(/\s+/).length * 0.3; }
function fakeWords(text, v, d) {
  const ws = text.split(/\s+/);
  const each = d / ws.length;
  return ws.map((w, k) => ({ w, t: v + k * each, d: each * 0.9 }));
}

function buildScenes({ lines, banners, shots, vEnd, vReplay0, vCel0, vBoard, E, vOfSim }) {
  // Scènes de ≤ 5 s pour un Short : on coupe aux plans caméra et aux lignes de voix
  const cuts = new Set([0, vEnd, vReplay0, vCel0, vBoard, ...shots.map((s) => s.v)]);
  const sorted = [...cuts].filter((x) => x >= 0 && x <= vEnd).sort((a, b) => a - b);
  const bounds = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    const a = sorted[i], b = sorted[i + 1];
    if (b - a < 0.4) { if (bounds.length && b - bounds[bounds.length - 1][0] <= 5) bounds[bounds.length - 1][1] = b; else bounds.push([a, b]); continue; }
    const n = Math.ceil((b - a) / 5);                 // découpe en parts égales de 5 s max
    for (let k = 0; k < n; k++) bounds.push([a + ((b - a) * k) / n, a + ((b - a) * (k + 1)) / n]);
  }
  return bounds.map(([a, b], k) => {
    const ls = lines.filter((l) => l.v >= a && l.v < b);
    const sh = [...shots].reverse().find((s) => s.v <= a + 0.01) || shots[0];
    const bn = banners.find((x) => x.v >= a && x.v < b);
    const el = E.filter((e) => { const v = vOfSim(e.t); return v >= a && v < b; });
    const role = a < 0.1 ? 'hook' : a >= vBoard ? 'boucle' : a >= vCel0 ? 'payoff' : ls.some((l) => l.id === 'win') ? 'payoff' : bn ? 'relance' : 'contenu';
    return {
      id: `S${String(k + 1).padStart(2, '0')}`, role, debut_s: +a.toFixed(2), duree_s: +(b - a).toFixed(2),
      voix_off: ls.map((l) => l.text).join(' '),
      ton: role === 'hook' ? 'posé, tranchant' : role === 'payoff' ? 'explosif' : 'énergique, rapide',
      avatar: 'hors_champ',
      visuel: shotLabel(sh.type) + (el.length ? ` — élimination(s) : ${el.map((e) => COUNTRIES[e.i].name).join(', ')}` : ''),
      texte_ecran: bn ? `${bn.title}${bn.sub ? ' · ' + bn.sub : ''}` : el.length ? `${COUNTRIES[el[0].i].name.toUpperCase()} OUT` : '',
      son: role === 'payoff' ? 'impact + foule en liesse' : 'clics de billes, musique tendue',
      boucles: { ouvre: role === 'hook' ? ['Q1'] : [], ferme: role === 'payoff' ? ['Q1'] : [] },
      note_traduction: '',
    };
  });
}
function shotLabel(t) {
  return {
    intro: 'Plan grue : pluie de 32 billes-drapeaux sur le plateau', broadcast: 'Plan large 3/4 type retransmission, légère orbite',
    punch: 'Zoom coup de poing sur la chute', sweep: 'Plan bas en travelling circulaire', duel: 'Plan serré en orbite sur les deux finalistes',
    kill: 'Plan rapproché, ralenti 0,2×', replay: 'Replay latéral au ralenti 0,4×', winner: 'Orbite autour du vainqueur en lévitation, confettis',
  }[t] || t;
}
