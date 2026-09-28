// Textures procédurales (Canvas 2D) : sol imprimé du plateau, rayures d'usure, bandes de danger, ombres de contact.
import { P } from './sim.js';

function mk(w, h) {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  const c = document.createElement('canvas'); c.width = w; c.height = h; return c;
}
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// Sol du plateau vu de dessus (2048 px = 3,2 m) : couleur, rugosité, émission (LED)
export function floorTextures(size = 2048) {
  const R = rng(7);
  const col = mk(size, size), c = col.getContext('2d');
  const rough = mk(size, size), r = rough.getContext('2d');
  const emi = mk(size, size), e = emi.getContext('2d');
  const S = size / (2 * P.R0); // px par mètre
  const cx = size / 2, cy = size / 2;
  const ring = (ctx, rad, w, style) => { ctx.beginPath(); ctx.arc(cx, cy, rad * S, 0, Math.PI * 2); ctx.lineWidth = w * S; ctx.strokeStyle = style; ctx.stroke(); };

  // base : époxy anthracite légèrement bleuté + variations basse fréquence
  c.fillStyle = '#16264d'; c.fillRect(0, 0, size, size);
  for (let i = 0; i < 90; i++) {
    const x = R() * size, y = R() * size, rr = (0.2 + R() * 0.9) * S;
    const g = c.createRadialGradient(x, y, 0, x, y, rr);
    const l = R() < 0.5 ? '255,255,255' : '0,0,0';
    g.addColorStop(0, `rgba(${l},0.035)`); g.addColorStop(1, `rgba(${l},0)`);
    c.fillStyle = g; c.fillRect(x - rr, y - rr, rr * 2, rr * 2);
  }
  // rugosité : base satinée
  r.fillStyle = 'rgb(120,120,120)'; r.fillRect(0, 0, size, size);

  // disque central : cible concentrique façon plateau de jeu télé
  for (let k = 0; k < 5; k++) ring(c, 0.3 + k * 0.14, 0.012, 'rgba(255,255,255,0.16)');
  const grd = c.createRadialGradient(cx, cy, 0.18 * S, cx, cy, 1.0 * S);
  grd.addColorStop(0, 'rgba(60,140,255,0.35)'); grd.addColorStop(0.7, 'rgba(60,140,255,0.10)'); grd.addColorStop(1, 'rgba(60,140,255,0.02)');
  c.fillStyle = grd; c.beginPath(); c.arc(cx, cy, 1.0 * S, 0, Math.PI * 2); c.fill();

  // texte circulaire autour du moyeu
  const text = 'ARÈNE DES NATIONS  ·  32 PAYS  ·  1 SURVIVANT  ·  ';
  c.save(); c.translate(cx, cy);
  c.font = `900 ${0.075 * S}px "Anton", "Impact", "Arial Black", sans-serif`;
  c.fillStyle = 'rgba(255,255,255,0.55)'; c.textAlign = 'center'; c.textBaseline = 'middle';
  const full = text + text;
  const rad = 0.5 * S;
  let ang = -Math.PI / 2;
  for (const ch of full) {
    const w = c.measureText(ch).width;
    if (ang + w / rad > Math.PI * 1.5 - 0.12) break;
    ang += (w / 2) / rad;
    c.save(); c.rotate(ang); c.translate(0, -rad); c.fillText(ch, 0, 0); c.restore();
    ang += (w / 2) / rad + 0.004;
  }
  c.restore();

  // anneaux extérieurs (zone effondrable) : bandes rouges de danger + graduations
  for (let k = 0; k < P.rings; k++) {
    const r0 = P.R0 - (k + 1) * P.ringW, r1 = P.R0 - k * P.ringW;
    c.beginPath(); c.arc(cx, cy, r1 * S, 0, Math.PI * 2); c.arc(cx, cy, r0 * S, 0, Math.PI * 2, true);
    c.fillStyle = k % 2 ? '#b3182b' : '#c81f32'; c.fill();
    ring(c, r0 + 0.002, 0.004, 'rgba(255,255,255,0.45)');
  }
  // bande hachurée jaune/noir sur l'anneau extérieur
  c.save(); c.beginPath(); c.arc(cx, cy, (P.R0 - 0.005) * S, 0, Math.PI * 2); c.arc(cx, cy, (P.R0 - 0.085) * S, 0, Math.PI * 2, true); c.clip();
  c.translate(cx, cy);
  for (let a = 0; a < Math.PI * 2; a += Math.PI / 90) {
    c.save(); c.rotate(a);
    c.beginPath(); c.moveTo(P.R0 * 0.94 * S, -8); c.lineTo(P.R0 * 1.01 * S, 8); c.lineTo(P.R0 * 1.01 * S, 22); c.lineTo(P.R0 * 0.94 * S, 6);
    c.fillStyle = '#f2c200'; c.fill(); c.restore();
  }
  c.restore();
  // numéros de portes
  c.save(); c.translate(cx, cy);
  c.font = `900 ${0.07 * S}px "Anton", "Impact", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle';
  for (let g = 0; g < P.nGates; g++) {
    const a = ((g + 0.5) * 2 * Math.PI) / P.nGates;
    c.save(); c.rotate(a + Math.PI / 2); c.translate(0, -(P.R0 - 0.21) * S);
    c.fillStyle = 'rgba(255,255,255,0.35)'; c.fillText(String(g + 1).padStart(2, '0'), 0, 0); c.restore();
  }
  c.restore();

  // traces d'usure : arcs clairs laissés par les billes + poussière
  c.lineCap = 'round';
  for (let i = 0; i < 260; i++) {
    const rr = (0.25 + R() * 1.3) * S, a0 = R() * Math.PI * 2, da = (0.05 + R() * 0.5) * (R() < 0.5 ? 1 : -1);
    c.beginPath(); c.arc(cx + (R() - 0.5) * 0.3 * S, cy + (R() - 0.5) * 0.3 * S, rr, a0, a0 + da, da < 0);
    c.strokeStyle = `rgba(255,255,255,${0.012 + R() * 0.02})`; c.lineWidth = 1 + R() * 3; c.stroke();
    r.beginPath(); r.arc(cx, cy, rr, a0, a0 + da, da < 0); r.strokeStyle = `rgba(70,70,70,${0.2 + R() * 0.2})`; r.lineWidth = 2 + R() * 4; r.stroke();
  }
  const img = c.getImageData(0, 0, size, size), d = img.data;
  for (let i = 0; i < d.length; i += 4) { const n = (R() - 0.5) * 10; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  c.putImageData(img, 0, 0);

  // émission : LED de séparation zone sûre / zone effondrable + fin liseré extérieur
  e.fillStyle = '#000'; e.fillRect(0, 0, size, size);
  ring(e, P.R0 - P.rings * P.ringW, 0.012, '#39d5ff');
  ring(e, P.R0 - 0.1, 0.006, '#ff2a3a');
  ring(e, 0.2, 0.01, '#39d5ff');

  return { col, rough, emi };
}

// micro-rayures (rugosité) partagées par toutes les billes
export function scratchTexture(size = 512) {
  const R = rng(3), cv = mk(size, size), c = cv.getContext('2d');
  c.fillStyle = 'rgb(46,46,46)'; c.fillRect(0, 0, size, size);
  for (let i = 0; i < 700; i++) {
    const x = R() * size, y = R() * size, l = 4 + R() * 30, a = R() * Math.PI;
    c.strokeStyle = `rgba(${140 + R() * 80},${140 + R() * 80},${140 + R() * 80},${0.15 + R() * 0.35})`;
    c.lineWidth = 0.6 + R() * 0.8; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); c.stroke();
  }
  for (let i = 0; i < 60; i++) { const x = R() * size, y = R() * size; c.fillStyle = `rgba(160,160,160,${0.2 + R() * 0.3})`; c.beginPath(); c.arc(x, y, 1 + R() * 3, 0, Math.PI * 2); c.fill(); }
  return cv;
}

export function hazardTexture(w = 512, h = 64) {
  const cv = mk(w, h), c = cv.getContext('2d');
  c.fillStyle = '#f2c200'; c.fillRect(0, 0, w, h);
  c.fillStyle = '#111';
  for (let x = -h; x < w + h; x += h) { c.beginPath(); c.moveTo(x, h); c.lineTo(x + h / 2, 0); c.lineTo(x + h, 0); c.lineTo(x + h / 2, h); c.fill(); }
  const img = c.getImageData(0, 0, w, h), d = img.data, R = rng(11);
  for (let i = 0; i < d.length; i += 4) { const n = (R() - 0.5) * 22; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  c.putImageData(img, 0, 0);
  return cv;
}

export function blobTexture(size = 128) {
  const cv = mk(size, size), c = cv.getContext('2d');
  const g = c.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(0.35, 'rgba(0,0,0,0.45)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = g; c.fillRect(0, 0, size, size);
  return cv;
}

export function dotTexture(size = 64) {
  const cv = mk(size, size), c = cv.getContext('2d');
  const g = c.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,0.8)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  c.fillStyle = g; c.fillRect(0, 0, size, size);
  return cv;
}
