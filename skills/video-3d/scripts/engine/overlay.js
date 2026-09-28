// Habillage 2D par-dessus la 3D (repère 1080×1920) : sous-titres mot à mot, textes-chocs, outils de dessin.
// Zones sûres TikTok : haut < 160 px, bas > 1560 px, droite > 950 px entre 880 et 1560 px.
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
export const easeOutBack = (t) => { t = clamp(t, 0, 1); const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
export const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
export const FONT = { display: '"Anton", Impact, sans-serif', caption: '"Montserrat", "Arial Black", sans-serif' };
export const COLORS = { yellow: '#FFE11A', red: '#FF2D3D', green: '#7CFF4F', cyan: '#39D5FF', white: '#FFFFFF' };
export const SAFE = { top: 170, bottom: 1540, right: 950 };

export function rr(c, x, y, w, h, r) { c.beginPath(); c.roundRect(x, y, w, h, r); }
// texte « sticker » : contour noir épais + ombre
export function sticker(c, text, x, y, size, fill = '#fff', { font = FONT.display, weight = '', stroke = 0.15, align = 'center', maxW = 0 } = {}) {
  c.save();
  c.font = `${weight} ${size}px ${font}`;
  if (maxW) { const w = c.measureText(text).width; if (w > maxW) { size *= maxW / w; c.font = `${weight} ${size}px ${font}`; } }
  c.textAlign = align; c.textBaseline = 'middle'; c.lineJoin = 'round';
  c.shadowColor = 'rgba(0,0,0,0.55)'; c.shadowOffsetY = size * 0.06; c.shadowBlur = size * 0.08;
  c.lineWidth = size * stroke; c.strokeStyle = '#000'; c.strokeText(text, x, y);
  c.shadowColor = 'transparent'; c.fillStyle = fill; c.fillText(text, x, y);
  c.restore();
  return size;
}

export class Overlay {
  constructor(canvas, T, story) {
    this.c = canvas.getContext('2d'); this.T = T; this.story = story;
    this.style = story.captions || {};
    this.highlight = new Set((story.highlight || []).map((w) => w.toUpperCase()));
  }
  draw(v, extra) {
    this.punch(v);
    if (extra) extra(this, v);
    if (this.style.show !== false) this.captions(v);
  }
  // texte-choc d'un beat (champ "text") : claque à l'écran au début du beat
  punch(v) {
    const b = this.T.beatAt(v);
    if (!b || !b.text) return;
    const t = v - b.v0 - (b.textAt ?? 0), dur = Math.min(b.dur - (b.textAt ?? 0), b.textDur ?? 2.4);
    if (t < 0 || t > dur) return;
    const k = easeOutBack(t / 0.28), out = clamp((dur - t) / 0.25, 0, 1);
    const y = { top: 330, center: 820, bottom: 1180 }[b.textPos || 'top'];
    const c = this.c;
    c.save(); c.globalAlpha = out; c.translate(540, y); c.scale(1.8 - 0.8 * k, 1.8 - 0.8 * k); c.rotate(-0.03);
    const lines = String(b.text).split('\n');
    lines.forEach((ln, i) => sticker(c, ln, 0, (i - (lines.length - 1) / 2) * 150, i === 0 ? 150 : 110, i === 0 ? '#fff' : COLORS.yellow, { maxW: 940 }));
    c.restore();
  }
  // sous-titres mot à mot (le mot prononcé apparaît, les mots-clés en jaune)
  captions(v) {
    const cap = this.T.captions.find((k) => v >= k.v0 && v < k.v1 + 0.05);
    if (!cap) return;
    const c = this.c, size = this.style.size || 80, y = this.style.y || 1320, x = 488;
    const k = easeOutBack((v - cap.v0) / 0.12);
    c.save(); c.translate(x, y); c.scale(k, k);
    c.font = `900 ${size}px ${FONT.caption}`;
    const words = cap.words.map((w) => w.w.toUpperCase());
    const widths = words.map((w) => c.measureText(w).width), space = size * 0.28;
    const total = widths.reduce((a, b) => a + b, 0) + space * (words.length - 1);
    if (total > 820) c.scale(820 / total, 820 / total);
    let xx = -total / 2;
    words.forEach((w, j) => {
      if (v >= cap.words[j].t - 0.02) {
        const clean = w.replace(/[.,!?:;«»"]/g, '');
        const fill = this.highlight.has(clean) || /\d/.test(clean) ? COLORS.yellow : j === words.length - 1 && /!$/.test(w) ? COLORS.green : '#fff';
        sticker(c, w, xx + widths[j] / 2, 0, size, fill, { font: FONT.caption, weight: 900, stroke: 0.2 });
      }
      xx += widths[j] + space;
    });
    c.restore();
  }
}
