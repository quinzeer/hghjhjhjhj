// 32 pays : 20 à forte audience francophone sur TikTok + 12 grandes nations de football (rivalités = commentaires).
// def : forme avec article pour la voix off ; plur : accord pluriel ; aud : poids d'audience (priorité des annonces vocales).
export const COUNTRIES = [
  { code: 'FRA', name: 'France', def: 'la France', aud: 10 },
  { code: 'DZA', name: 'Algérie', def: "l'Algérie", aud: 10 },
  { code: 'MAR', name: 'Maroc', def: 'le Maroc', aud: 10 },
  { code: 'TUN', name: 'Tunisie', def: 'la Tunisie', aud: 8 },
  { code: 'SEN', name: 'Sénégal', def: 'le Sénégal', aud: 8 },
  { code: 'CIV', name: "Côte d'Ivoire", def: "la Côte d'Ivoire", aud: 9 },
  { code: 'CMR', name: 'Cameroun', def: 'le Cameroun', aud: 9 },
  { code: 'BEL', name: 'Belgique', def: 'la Belgique', aud: 7 },
  { code: 'SUI', name: 'Suisse', def: 'la Suisse', aud: 6 },
  { code: 'CAN', name: 'Canada', def: 'le Canada', aud: 7 },
  { code: 'COD', name: 'RD Congo', def: 'la RDC', aud: 9 },
  { code: 'MLI', name: 'Mali', def: 'le Mali', aud: 7 },
  { code: 'GIN', name: 'Guinée', def: 'la Guinée', aud: 7 },
  { code: 'HAI', name: 'Haïti', def: 'Haïti', aud: 6 },
  { code: 'MAD', name: 'Madagascar', def: 'Madagascar', aud: 6 },
  { code: 'BFA', name: 'Burkina Faso', def: 'le Burkina', aud: 6 },
  { code: 'GAB', name: 'Gabon', def: 'le Gabon', aud: 6 },
  { code: 'BEN', name: 'Bénin', def: 'le Bénin', aud: 6 },
  { code: 'TOG', name: 'Togo', def: 'le Togo', aud: 6 },
  { code: 'NER', name: 'Niger', def: 'le Niger', aud: 5 },
  { code: 'BRA', name: 'Brésil', def: 'le Brésil', aud: 8 },
  { code: 'ARG', name: 'Argentine', def: "l'Argentine", aud: 7 },
  { code: 'POR', name: 'Portugal', def: 'le Portugal', aud: 8 },
  { code: 'ESP', name: 'Espagne', def: "l'Espagne", aud: 7 },
  { code: 'ITA', name: 'Italie', def: "l'Italie", aud: 7 },
  { code: 'GER', name: 'Allemagne', def: "l'Allemagne", aud: 6 },
  { code: 'ENG', name: 'Angleterre', def: "l'Angleterre", aud: 6 },
  { code: 'USA', name: 'États-Unis', def: 'les États-Unis', plur: true, aud: 7 },
  { code: 'JPN', name: 'Japon', def: 'le Japon', aud: 6 },
  { code: 'TUR', name: 'Turquie', def: 'la Turquie', aud: 7 },
  { code: 'MEX', name: 'Mexique', def: 'le Mexique', aud: 5 },
  { code: 'NED', name: 'Pays-Bas', def: 'les Pays-Bas', plur: true, aud: 5 },
];

export const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

// ---------- dessin des drapeaux (Canvas 2D, aucune image externe) ----------
function vb(c, w, h, cols, ratios) {
  const tot = (ratios || cols.map(() => 1)).reduce((a, b) => a + b, 0);
  let x = 0;
  cols.forEach((col, i) => { const bw = (w * (ratios ? ratios[i] : 1)) / tot; c.fillStyle = col; c.fillRect(x - 0.5, 0, bw + 1, h); x += bw; });
}
function hb(c, w, h, cols, ratios) {
  const tot = (ratios || cols.map(() => 1)).reduce((a, b) => a + b, 0);
  let y = 0;
  cols.forEach((col, i) => { const bh = (h * (ratios ? ratios[i] : 1)) / tot; c.fillStyle = col; c.fillRect(0, y - 0.5, w, bh + 1); y += bh; });
}
function star(c, x, y, R, col, rot = -Math.PI / 2, inner = 0.382) {
  c.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = rot + (i * Math.PI) / 5, rr = i % 2 ? R * inner : R;
    c.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  c.closePath(); c.fillStyle = col; c.fill();
}
function disc(c, x, y, r, col) { c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fillStyle = col; c.fill(); }
// croissant : disque R moins disque r décalé de dx (vers +x si dx>0), sur un calque pour préserver le fond
function crescent(c, x, y, R, r, dx, col) {
  const cv = mk(c.canvas.width, c.canvas.height), k = cv.getContext('2d');
  k.setTransform(c.getTransform());
  disc(k, x, y, R, col);
  k.globalCompositeOperation = 'destination-out';
  disc(k, x + dx, y, r, '#000');
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(cv, 0, 0); c.restore();
}
function mk(w, h) {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; return cv;
}
const LEAF = 'm-90 2030 45-863a95 95 0 0 0-111-98l-859 151 116-320a65 65 0 0 0-20-73l-941-762 212-99a65 65 0 0 0 34-79l-186-572 542 115a65 65 0 0 0 73-38l105-247 423 454a65 65 0 0 0 111-57l-204-1052 327 189a65 65 0 0 0 91-27l332-652 332 652a65 65 0 0 0 91 27l327-189-204 1052a65 65 0 0 0 111 57l423-454 105 247a65 65 0 0 0 73 38l542-115-186 572a65 65 0 0 0 34 79l212 99-941 762a65 65 0 0 0-20 73l116 320-859-151a95 95 0 0 0-111 98l45 863z';

const DRAW = {
  FRA: (c, w, h) => vb(c, w, h, ['#0055A4', '#FFFFFF', '#EF4135']),
  DZA: (c, w, h) => { vb(c, w, h, ['#006233', '#FFFFFF']); crescent(c, w / 2, h / 2, h * 0.25, h * 0.2, h * 0.07, '#D21034'); star(c, w / 2 + h * 0.085, h / 2, h * 0.1, '#D21034', Math.PI); },
  MAR: (c, w, h) => {
    c.fillStyle = '#C1272D'; c.fillRect(0, 0, w, h);
    const R = h * 0.2, pts = [];
    for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5; pts.push([w / 2 + Math.cos(a) * R, h / 2 + Math.sin(a) * R]); }
    c.beginPath(); [0, 2, 4, 1, 3, 0].forEach((k, i) => (i ? c.lineTo(...pts[k]) : c.moveTo(...pts[k])));
    c.strokeStyle = '#006233'; c.lineWidth = h * 0.035; c.lineJoin = 'miter'; c.stroke();
  },
  TUN: (c, w, h) => { c.fillStyle = '#E70013'; c.fillRect(0, 0, w, h); disc(c, w / 2, h / 2, h * 0.25, '#FFFFFF'); crescent(c, w / 2 - h * 0.02, h / 2, h * 0.19, h * 0.155, h * 0.05, '#E70013'); star(c, w / 2 + h * 0.06, h / 2, h * 0.09, '#E70013', Math.PI); },
  SEN: (c, w, h) => { vb(c, w, h, ['#00853F', '#FDEF42', '#E31B23']); star(c, w / 2, h / 2 + h * 0.01, h * 0.14, '#00853F'); },
  CIV: (c, w, h) => vb(c, w, h, ['#F77F00', '#FFFFFF', '#009E60']),
  CMR: (c, w, h) => { vb(c, w, h, ['#007A5E', '#CE1126', '#FCD116']); star(c, w / 2, h / 2 + h * 0.01, h * 0.14, '#FCD116'); },
  BEL: (c, w, h) => vb(c, w, h, ['#111111', '#FDDA24', '#EF3340']),
  SUI: (c, w, h) => { c.fillStyle = '#DA291C'; c.fillRect(0, 0, w, h); c.fillStyle = '#FFFFFF'; const a = h * 0.19, l = h * 0.62; c.fillRect(w / 2 - a / 2, h / 2 - l / 2, a, l); c.fillRect(w / 2 - l / 2, h / 2 - a / 2, l, a); },
  CAN: (c, w, h) => {
    vb(c, w, h, ['#D52B1E', '#FFFFFF', '#D52B1E'], [1, 2, 1]);
    c.save(); c.translate(w / 2, h / 2 + h * 0.01); const s = (h * 0.62) / 4030; c.scale(s, s);
    c.fillStyle = '#D52B1E'; c.fill(new Path2D(LEAF)); c.restore();
  },
  COD: (c, w, h) => {
    c.fillStyle = '#007FFF'; c.fillRect(0, 0, w, h);
    c.lineCap = 'butt';
    c.beginPath(); c.moveTo(-w * 0.1, h * 1.1); c.lineTo(w * 1.1, -h * 0.1); c.strokeStyle = '#F7D618'; c.lineWidth = h * 0.36; c.stroke();
    c.beginPath(); c.moveTo(-w * 0.1, h * 1.1); c.lineTo(w * 1.1, -h * 0.1); c.strokeStyle = '#CE1021'; c.lineWidth = h * 0.24; c.stroke();
    star(c, w * 0.17, h * 0.24, h * 0.15, '#F7D618');
  },
  MLI: (c, w, h) => vb(c, w, h, ['#14B53A', '#FCD116', '#CE1126']),
  GIN: (c, w, h) => vb(c, w, h, ['#CE1126', '#FCD116', '#009460']),
  HAI: (c, w, h) => {
    hb(c, w, h, ['#00209F', '#D21034']);
    c.fillStyle = '#FFFFFF'; c.fillRect(w / 2 - h * 0.24, h / 2 - h * 0.2, h * 0.48, h * 0.4);
    c.fillStyle = '#016A16'; c.beginPath(); c.moveTo(w / 2, h / 2 - h * 0.15); c.lineTo(w / 2 + h * 0.1, h / 2 + h * 0.08); c.lineTo(w / 2 - h * 0.1, h / 2 + h * 0.08); c.fill();
    c.fillStyle = '#016A16'; c.fillRect(w / 2 - h * 0.18, h / 2 + h * 0.1, h * 0.36, h * 0.05);
  },
  MAD: (c, w, h) => { c.fillStyle = '#FFFFFF'; c.fillRect(0, 0, w / 3, h); c.fillStyle = '#FC3D32'; c.fillRect(w / 3, 0, w, h / 2); c.fillStyle = '#007E3A'; c.fillRect(w / 3, h / 2, w, h / 2); },
  BFA: (c, w, h) => { hb(c, w, h, ['#EF2B2D', '#009E49']); star(c, w / 2, h / 2, h * 0.16, '#FCD116'); },
  GAB: (c, w, h) => hb(c, w, h, ['#009E60', '#FCD116', '#3A75C4']),
  BEN: (c, w, h) => { c.fillStyle = '#FCD116'; c.fillRect(0, 0, w, h / 2); c.fillStyle = '#E8112D'; c.fillRect(0, h / 2, w, h / 2); c.fillStyle = '#008751'; c.fillRect(0, 0, w * 0.4, h); },
  TOG: (c, w, h) => { hb(c, w, h, ['#006A4E', '#FFCE00', '#006A4E', '#FFCE00', '#006A4E']); c.fillStyle = '#D21034'; c.fillRect(0, 0, h * 0.6, h * 0.6); star(c, h * 0.3, h * 0.31, h * 0.2, '#FFFFFF'); },
  NER: (c, w, h) => { hb(c, w, h, ['#E05206', '#FFFFFF', '#0DB02B']); disc(c, w / 2, h / 2, h * 0.13, '#E05206'); },
  BRA: (c, w, h) => {
    c.fillStyle = '#009C3B'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#FFDF00'; c.beginPath(); c.moveTo(w / 2, h * 0.08); c.lineTo(w - w * 0.07, h / 2); c.lineTo(w / 2, h * 0.92); c.lineTo(w * 0.07, h / 2); c.fill();
    disc(c, w / 2, h / 2, h * 0.24, '#002776');
    c.save(); c.beginPath(); c.arc(w / 2, h / 2, h * 0.24, 0, Math.PI * 2); c.clip();
    c.beginPath(); c.arc(w / 2 - h * 0.1, h * 1.05, h * 0.62, -Math.PI * 0.62, -Math.PI * 0.2); c.strokeStyle = '#FFFFFF'; c.lineWidth = h * 0.045; c.stroke();
    for (let i = 0; i < 9; i++) disc(c, w / 2 + (((i * 37) % 17) / 17 - 0.5) * h * 0.3, h / 2 + h * 0.06 + ((i * 53) % 11) / 11 * h * 0.13, h * 0.009, '#FFFFFF');
    c.restore();
  },
  ARG: (c, w, h) => {
    hb(c, w, h, ['#74ACDF', '#FFFFFF', '#74ACDF']);
    c.save(); c.translate(w / 2, h / 2);
    for (let i = 0; i < 16; i++) { c.rotate(Math.PI / 8); c.beginPath(); c.moveTo(-h * 0.025, 0); c.lineTo(0, -h * (i % 2 ? 0.14 : 0.16)); c.lineTo(h * 0.025, 0); c.fillStyle = '#F6B40E'; c.fill(); }
    c.restore(); disc(c, w / 2, h / 2, h * 0.075, '#F6B40E');
  },
  POR: (c, w, h) => {
    c.fillStyle = '#006600'; c.fillRect(0, 0, w * 0.4, h); c.fillStyle = '#FF0000'; c.fillRect(w * 0.4, 0, w * 0.6, h);
    c.beginPath(); c.arc(w * 0.4, h / 2, h * 0.2, 0, Math.PI * 2); c.strokeStyle = '#FFE000'; c.lineWidth = h * 0.05; c.stroke();
    c.fillStyle = '#FFFFFF'; c.fillRect(w * 0.4 - h * 0.1, h / 2 - h * 0.12, h * 0.2, h * 0.22);
    c.strokeStyle = '#FF0000'; c.lineWidth = h * 0.035; c.strokeRect(w * 0.4 - h * 0.1, h / 2 - h * 0.12, h * 0.2, h * 0.22);
    disc(c, w * 0.4, h / 2 - h * 0.01, h * 0.035, '#003399');
  },
  ESP: (c, w, h) => hb(c, w, h, ['#AA151B', '#F1BF00', '#AA151B'], [1, 2, 1]),
  ITA: (c, w, h) => vb(c, w, h, ['#009246', '#FFFFFF', '#CE2B37']),
  GER: (c, w, h) => hb(c, w, h, ['#111111', '#DD0000', '#FFCE00']),
  ENG: (c, w, h) => { c.fillStyle = '#FFFFFF'; c.fillRect(0, 0, w, h); c.fillStyle = '#CE1124'; const a = h * 0.2; c.fillRect(w / 2 - a / 2, 0, a, h); c.fillRect(0, h / 2 - a / 2, w, a); },
  USA: (c, w, h) => {
    for (let i = 0; i < 13; i++) { c.fillStyle = i % 2 ? '#FFFFFF' : '#B22234'; c.fillRect(0, (i * h) / 13 - 0.5, w, h / 13 + 1); }
    const cw = w * 0.42, ch = (h * 7) / 13; c.fillStyle = '#3C3B6E'; c.fillRect(0, 0, cw, ch);
    for (let r = 0; r < 9; r++) for (let k = 0; k < (r % 2 ? 5 : 6); k++) star(c, (cw / 12) * (1 + 2 * k + (r % 2)), (ch / 10) * (r + 1), Math.min(cw, ch) * 0.045, '#FFFFFF');
  },
  JPN: (c, w, h) => { c.fillStyle = '#FFFFFF'; c.fillRect(0, 0, w, h); disc(c, w / 2, h / 2, h * 0.3, '#BC002D'); },
  TUR: (c, w, h) => { c.fillStyle = '#E30A17'; c.fillRect(0, 0, w, h); const x = w / 2 - h * 0.17; crescent(c, x, h / 2, h * 0.25, h * 0.2, h * 0.0625, '#FFFFFF'); star(c, x + h * 0.23, h / 2, h * 0.11, '#FFFFFF', Math.PI); },
  MEX: (c, w, h) => { vb(c, w, h, ['#006847', '#FFFFFF', '#CE1126']); disc(c, w / 2, h / 2, h * 0.12, '#6F4E1E'); c.beginPath(); c.arc(w / 2, h / 2 + h * 0.02, h * 0.13, 0.15 * Math.PI, 0.85 * Math.PI); c.strokeStyle = '#2E7D32'; c.lineWidth = h * 0.03; c.stroke(); disc(c, w / 2 + h * 0.03, h / 2 - h * 0.04, h * 0.045, '#C8A04A'); },
  NED: (c, w, h) => hb(c, w, h, ['#AE1C28', '#FFFFFF', '#21468B']),
};

export function drawFlag(ctx, code, x, y, w, h) {
  ctx.save(); ctx.translate(x, y);
  ctx.beginPath(); ctx.rect(0, 0, w, h); ctx.clip();
  DRAW[code](ctx, w, h);
  ctx.restore();
}

// Canvas d'un drapeau au format 3:2 (interface)
export function flagCanvas(code, w = 240, h = 160) {
  const cv = mk(w, h); drawFlag(cv.getContext('2d'), code, 0, 0, w, h); return cv;
}

// Texture équirectangulaire d'une bille : deux copies carrées du drapeau (une par hémisphère),
// grain d'impression et fines rayures pour que la surface ne soit pas « parfaite ».
export function ballTexture(code, size = 1024, seed = 1) {
  const cv = mk(size, size / 2), c = cv.getContext('2d');
  const s = size / 2;
  drawFlag(c, code, 0, 0, s, s);
  drawFlag(c, code, s, 0, s, s);
  let a = seed * 9301 + 49297;
  const rnd = () => ((a = (a * 9301 + 49297) % 233280) / 233280);
  c.globalAlpha = 0.05;
  for (let i = 0; i < 1400; i++) { c.fillStyle = rnd() < 0.5 ? '#000' : '#fff'; c.fillRect(rnd() * size, rnd() * s, 2, 2); }
  c.globalAlpha = 1;
  return cv;
}
