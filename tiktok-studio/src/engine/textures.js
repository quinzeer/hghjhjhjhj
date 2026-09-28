// Textures procédurales (Canvas2D) : bruit, cartes de rugosité/normales, écrans.
import * as THREE from 'three';
import { mulberry32 } from './util.js';

export function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return c;
}

export function toTexture(c, { srgb = true, repeat = null, aniso = 8 } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = aniso;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  t.needsUpdate = true;
  return t;
}

// Bruit fractal « valeur » tuilable (sans raccord visible).
export function fbmField(size, { seed = 1, octaves = 5, base = 4 } = {}) {
  const rnd = mulberry32(seed);
  const out = new Float32Array(size * size);
  let amp = 1, norm = 0;
  for (let o = 0; o < octaves; o++) {
    const g = base << o;
    const grid = new Float32Array(g * g);
    for (let i = 0; i < grid.length; i++) grid[i] = rnd();
    for (let y = 0; y < size; y++) {
      const fy = (y / size) * g, y0 = Math.floor(fy), ty = fy - y0, sy = ty * ty * (3 - 2 * ty);
      for (let x = 0; x < size; x++) {
        const fx = (x / size) * g, x0 = Math.floor(fx), tx = fx - x0, sx = tx * tx * (3 - 2 * tx);
        const a = grid[(y0 % g) * g + (x0 % g)], b = grid[(y0 % g) * g + ((x0 + 1) % g)];
        const c = grid[((y0 + 1) % g) * g + (x0 % g)], d = grid[((y0 + 1) % g) * g + ((x0 + 1) % g)];
        out[y * size + x] += ((a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy) * amp;
      }
    }
    norm += amp; amp *= 0.5;
  }
  for (let i = 0; i < out.length; i++) out[i] /= norm;
  return out;
}

export function fieldToCanvas(field, size, map = (v) => [v * 255, v * 255, v * 255]) {
  const c = canvas(size, size);
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(size, size);
  for (let i = 0; i < field.length; i++) {
    const [r, g, b] = map(field[i]);
    img.data[i * 4] = r; img.data[i * 4 + 1] = g; img.data[i * 4 + 2] = b; img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

export function normalFromField(field, size, strength = 2) {
  const c = canvas(size, size);
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(size, size);
  const h = (x, y) => field[((y + size) % size) * size + ((x + size) % size)];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const dx = (h(x + 1, y) - h(x - 1, y)) * strength;
    const dy = (h(x, y + 1) - h(x, y - 1)) * strength;
    const n = new THREE.Vector3(-dx, -dy, 1).normalize();
    const i = (y * size + x) * 4;
    img.data[i] = (n.x * 0.5 + 0.5) * 255; img.data[i + 1] = (n.y * 0.5 + 0.5) * 255; img.data[i + 2] = (n.z * 0.5 + 0.5) * 255; img.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

// Rugosité de sol de plateau : zones lustrées, traces de passage, micro-rayures.
export function floorRoughness(size = 512, seed = 3) {
  const f = fbmField(size, { seed, octaves: 6, base: 3 });
  const c = fieldToCanvas(f, size, (v) => { const r = 0.18 + Math.pow(v, 1.6) * 0.75; return [r * 255, r * 255, r * 255]; });
  const ctx = c.getContext('2d');
  const rnd = mulberry32(seed + 9);
  ctx.globalAlpha = 0.08; ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.7;
  for (let i = 0; i < 260; i++) {
    const x = rnd() * size, y = rnd() * size, a = rnd() * Math.PI, l = 8 + rnd() * 50;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); ctx.stroke();
  }
  return c;
}

export function roundRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

// Texte ajusté à une largeur max (réduit la taille si besoin).
export function fitText(ctx, text, maxW, size, font) {
  let s = size;
  ctx.font = font.replace('{s}', s);
  while (ctx.measureText(text).width > maxW && s > 8) { s -= 2; ctx.font = font.replace('{s}', s); }
  return s;
}

export function wrapLines(ctx, text, maxW) {
  const words = text.split(/\s+/);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

// Silhouette neutre (aucun visage réel) pour les emplacements photo non fournis.
export function drawSilhouette(ctx, x, y, w, h, { bg = '#1c1f2b', fg = '#3a4054', accent = '#ffd60a' } = {}) {
  const g = ctx.createLinearGradient(x, y, x, y + h);
  g.addColorStop(0, bg); g.addColorStop(1, '#0d0f16');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = fg;
  const cx = x + w / 2;
  ctx.beginPath(); ctx.ellipse(cx, y + h * 0.36, w * 0.17, w * 0.2, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(cx, y + h * 0.98, w * 0.42, h * 0.36, 0, Math.PI, 0); ctx.fill();
  ctx.strokeStyle = accent; ctx.globalAlpha = 0.35; ctx.lineWidth = Math.max(2, w * 0.01);
  ctx.strokeRect(x + w * 0.04, y + h * 0.04, w * 0.92, h * 0.92);
  ctx.globalAlpha = 1;
}
