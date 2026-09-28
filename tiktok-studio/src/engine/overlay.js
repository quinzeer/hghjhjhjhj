// Couche 2D « montage MrBeast » : sous-titres mot à mot, titres chocs, compteurs, tampons,
// flèches, cercles, emojis, sources. Unité de conception : 1080 × 1920 (mise à l'échelle auto).
import { clamp, ease, lerp, popScale, invLerp, mulberry32 } from './util.js';
import { roundRect, wrapLines } from './textures.js';

const Y = '#FFD60A', RED = '#FF2D2D', GREEN = '#2BE06A', WHITE = '#FFFFFF', BLACK = '#000000';
const CAP_FONT = (s) => `900 ${s}px Montserrat`;

function strokeFill(ctx, text, x, y, fill, stroke, lw, shadow = true) {
  ctx.lineJoin = 'round'; ctx.miterLimit = 2;
  if (shadow) {
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.strokeStyle = 'rgba(0,0,0,0.55)'; ctx.lineWidth = lw;
    ctx.strokeText(text, x + lw * 0.18, y + lw * 0.45);
    ctx.fillText(text, x + lw * 0.18, y + lw * 0.45);
    ctx.restore();
  }
  ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.strokeText(text, x, y);
  ctx.fillStyle = fill; ctx.fillText(text, x, y);
}

function fmtNumber(v, o = {}) {
  const d = o.decimals ?? 0;
  const s = v.toFixed(d).replace('.', ',');
  const [i, f] = s.split(',');
  const ii = i.replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0');
  return (o.prefix || '') + ii + (f ? ',' + f : '') + (o.suffix || '');
}

export class Overlay {
  constructor(tl, W, H, assets) {
    this.tl = tl; this.W = W; this.H = H; this.s = W / 1080; this.assets = assets;
    this.images = new Map();
  }

  async preload() {
    for (const o of this.tl.overlays || []) {
      if (o.image) { const img = await this.assets.optionalHTMLImage(o.image); if (img) this.images.set(o.image, img); }
    }
  }

  draw(ctx, t) {
    const s = this.s;
    ctx.save();
    ctx.scale(s, s);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const list = (this.tl.overlays || []).filter((o) => t >= o.start && t < o.end);
    list.sort((a, b) => (a.z || 0) - (b.z || 0));
    for (const o of list) {
      const lt = t - o.start, dur = o.end - o.start;
      const fn = this['o_' + o.type];
      if (fn) { ctx.save(); fn.call(this, ctx, o, lt, dur, t); ctx.restore(); }
    }
    this.captions(ctx, t);
    ctx.restore();
  }

  // ---------- Sous-titres (mot à mot, mots-clés colorés) ----------
  captions(ctx, t) {
    const chunk = (this.tl.captions || []).find((c) => t >= c.start && t < c.end);
    if (!chunk) return;
    const cx = 500, cy = chunk.y ?? 1235;
    const words = chunk.words.filter((w) => t >= w.start - 0.02);
    if (!words.length) return;
    let size = chunk.size ?? 96;
    ctx.font = CAP_FONT(size);
    ctx.letterSpacing = '-1px';
    // Mise en page : 1 ou 2 lignes, largeur max 880.
    const all = chunk.words.map((w) => w.text.toUpperCase());
    const measure = (arr) => arr.reduce((a, w) => a + ctx.measureText(w).width * 1.1, 0) + (arr.length - 1) * size * 0.3;
    while (measure(all) > 1700 && size > 60) { size -= 4; ctx.font = CAP_FONT(size); }
    let lines = [chunk.words];
    if (measure(all) > 860) {
      let best = 1, bestDiff = 1e9;
      for (let k = 1; k < chunk.words.length; k++) {
        const d = Math.abs(measure(all.slice(0, k)) - measure(all.slice(k)));
        if (d < bestDiff) { bestDiff = d; best = k; }
      }
      lines = [chunk.words.slice(0, best), chunk.words.slice(best)];
    }
    const lh = size * 1.08;
    lines.forEach((line, li) => {
      const texts = line.map((w) => w.text.toUpperCase());
      const widths = texts.map((x, i) => ctx.measureText(x).width * (line[i].hl ? 1.1 * 1.04 : 1.04));
      const gap = size * 0.3;
      const total = widths.reduce((a, b) => a + b, 0) + gap * (line.length - 1);
      let x = cx - total / 2;
      const y = cy + (li - (lines.length - 1) / 2) * lh;
      line.forEach((w, wi) => {
        const width = widths[wi];
        const wx = x + width / 2;
        x += width + gap;
        if (t < w.start - 0.02) return;
        const k = popScale(t - w.start + 0.02, 0.14, 1.16);
        const active = t >= w.start && t < w.end + 0.08;
        const hl = w.hl;
        const color = hl === 'red' ? RED : hl === 'green' ? GREEN : hl ? Y : WHITE;
        const sc = k * (hl ? 1.1 : 1) * (active ? 1.04 : 1);
        ctx.save();
        ctx.translate(wx, y);
        ctx.rotate(hl ? -0.035 : 0);
        ctx.scale(sc, sc);
        ctx.font = CAP_FONT(size);
        if (hl && chunk.box) {
          ctx.fillStyle = hl === 'red' ? RED : GREEN;
          roundRect(ctx, -width / 2 - 14, -size * 0.52, width + 28, size * 1.04, 14); ctx.fill();
          strokeFill(ctx, texts[wi], 0, 4, WHITE, BLACK, size * 0.16);
        } else {
          strokeFill(ctx, texts[wi], 0, 4, color, BLACK, size * 0.17);
        }
        ctx.restore();
      });
    });
    ctx.letterSpacing = '0px';
  }

  // ---------- Titre choc ----------
  o_headline(ctx, o, lt, dur) {
    const inK = popScale(lt, 0.18, 1.14);
    const outK = o.exit === false ? 1 : 1 - ease.inCubic(clamp((lt - (dur - 0.12)) / 0.12));
    const sc = inK * outK;
    if (sc <= 0.001) return;
    const style = o.style || 'impact';
    const y = o.y ?? 520, x = o.x ?? 520;
    const rot = (o.rotate ?? (style === 'impact' ? -3 : 0)) * Math.PI / 180;
    ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
    const lines = Array.isArray(o.text) ? o.text : [o.text];
    const size = o.size ?? 130;
    if (style === 'alert' || style === 'box') {
      ctx.font = `900 ${size}px Montserrat`;
      const w = Math.max(...lines.map((l) => ctx.measureText(l.toUpperCase()).width)) + 70;
      const h = lines.length * size * 1.05 + 40;
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; roundRect(ctx, -w / 2 + 10, -h / 2 + 14, w, h, 22); ctx.fill();
      ctx.fillStyle = o.bg || RED; roundRect(ctx, -w / 2, -h / 2, w, h, 22); ctx.fill();
      ctx.fillStyle = o.color || WHITE;
      lines.forEach((l, i) => ctx.fillText(l.toUpperCase(), 0, (i - (lines.length - 1) / 2) * size * 1.05 + 6));
      return;
    }
    const font = style === 'news' ? `${size}px Anton` : `900 ${size}px Montserrat`;
    ctx.font = font;
    ctx.letterSpacing = style === 'news' ? '1px' : '-2px';
    // Ajustement automatique : aucune ligne ne dépasse 960 px (zone sûre TikTok).
    const widest = Math.max(...lines.map((l) => ctx.measureText(l.toUpperCase()).width));
    if (widest > 960) { const f = 960 / widest; ctx.scale(f, f); }
    lines.forEach((l, i) => {
      const yy = (i - (lines.length - 1) / 2) * size * 1.02;
      const colors = o.colors || [];
      strokeFill(ctx, l.toUpperCase(), 0, yy, colors[i] || o.color || (i === lines.length - 1 && style === 'impact' ? Y : WHITE), BLACK, size * 0.16);
    });
    ctx.letterSpacing = '0px';
  }

  // ---------- Compteur (argent, abonnés, vues) ----------
  o_counter(ctx, o, lt, dur) {
    const k = ease.outExpo(clamp(lt / (o.countDur ?? Math.min(1.4, dur * 0.7))));
    const v = lerp(o.from ?? 0, o.to, k);
    const sc = popScale(lt, 0.2, 1.15) * (1 + (k < 1 ? 0.02 * Math.sin(lt * 60) : 0));
    ctx.translate(o.x ?? 520, o.y ?? 560); ctx.scale(sc, sc); ctx.rotate((o.rotate ?? -2) * Math.PI / 180);
    const size = o.size ?? 170;
    ctx.font = `${size}px Anton`;
    const txt = fmtNumber(v, o);
    ctx.shadowColor = o.glow || 'rgba(255,214,10,0.65)'; ctx.shadowBlur = 40;
    strokeFill(ctx, txt, 0, 0, o.color || Y, BLACK, size * 0.12, false);
    ctx.shadowBlur = 0;
    if (o.label) { ctx.font = `900 ${Math.round(size * 0.3)}px Montserrat`; strokeFill(ctx, o.label.toUpperCase(), 0, size * 0.72, WHITE, BLACK, size * 0.07); }
  }

  // ---------- Pastille (ACTU 1/4, CONFIRMÉ, RUMEUR…) ----------
  o_chip(ctx, o, lt, dur) {
    const sc = popScale(lt, 0.16, 1.1);
    const outK = o.exit === false ? 1 : 1 - ease.inCubic(clamp((lt - (dur - 0.1)) / 0.1));
    ctx.translate(o.x ?? 540, o.y ?? 360); ctx.scale(sc * outK, sc * outK); ctx.rotate((o.rotate ?? 0) * Math.PI / 180);
    const size = o.size ?? 46;
    ctx.font = `900 ${size}px Montserrat`;
    const text = o.text.toUpperCase();
    const w = ctx.measureText(text).width + size * 1.1, h = size * 1.6;
    ctx.fillStyle = 'rgba(0,0,0,0.4)'; roundRect(ctx, -w / 2 + 5, -h / 2 + 7, w, h, h / 2); ctx.fill();
    ctx.fillStyle = o.bg || Y; roundRect(ctx, -w / 2, -h / 2, w, h, h / 2); ctx.fill();
    if (o.border) { ctx.strokeStyle = o.border; ctx.lineWidth = 5; ctx.stroke(); }
    ctx.fillStyle = o.color || BLACK; ctx.fillText(text, 0, size * 0.06);
  }

  // ---------- Tampon (CONFIRMÉ / FAUX / EXCLU) ----------
  o_stamp(ctx, o, lt) {
    const k = clamp(lt / 0.16);
    const sc = lerp(2.6, 1, ease.outCubic(k));
    const a = clamp(lt / 0.06);
    const shake = lt < 0.3 ? Math.sin(lt * 90) * 6 * (1 - lt / 0.3) : 0;
    ctx.globalAlpha = a;
    ctx.translate((o.x ?? 540) + shake, o.y ?? 700); ctx.rotate((o.rotate ?? -12) * Math.PI / 180); ctx.scale(sc, sc);
    const size = o.size ?? 110;
    ctx.font = `900 ${size}px Montserrat`;
    const text = o.text.toUpperCase();
    const w = ctx.measureText(text).width + 70, h = size * 1.35;
    const col = o.color || RED;
    ctx.strokeStyle = col; ctx.lineWidth = 12; roundRect(ctx, -w / 2, -h / 2, w, h, 18); ctx.stroke();
    ctx.lineWidth = 4; roundRect(ctx, -w / 2 + 16, -h / 2 + 16, w - 32, h - 32, 10); ctx.stroke();
    ctx.fillStyle = col; ctx.fillText(text, 0, 8);
  }

  // ---------- Emoji qui rebondit ----------
  o_emoji(ctx, o, lt) {
    const sc = popScale(lt, 0.22, 1.25);
    const bob = Math.sin(lt * 6) * 8;
    ctx.translate(o.x ?? 860, (o.y ?? 420) + bob); ctx.rotate(((o.rotate ?? 10) + Math.sin(lt * 5) * 4) * Math.PI / 180); ctx.scale(sc, sc);
    ctx.font = `${o.size ?? 150}px "Noto Color Emoji"`;
    ctx.fillText(o.text, 0, 0);
  }

  // ---------- Flèche animée (dessin progressif) ----------
  o_arrow(ctx, o, lt) {
    const k = ease.outCubic(clamp(lt / 0.25));
    const [x0, y0] = o.from, [x1, y1] = o.to;
    const mx = (x0 + x1) / 2 + (o.bend ?? 80), my = (y0 + y1) / 2 - (o.bend ?? 80) * 0.5;
    ctx.strokeStyle = o.color || RED; ctx.lineWidth = 16; ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 12;
    ctx.beginPath();
    const N = 30; let px = x0, py = y0;
    ctx.moveTo(x0, y0);
    for (let i = 1; i <= N * k; i++) {
      const u = i / N;
      px = (1 - u) * (1 - u) * x0 + 2 * (1 - u) * u * mx + u * u * x1;
      py = (1 - u) * (1 - u) * y0 + 2 * (1 - u) * u * my + u * u * y1;
      ctx.lineTo(px, py);
    }
    ctx.stroke();
    if (k > 0.95) {
      const ang = Math.atan2(y1 - my, x1 - mx);
      ctx.fillStyle = o.color || RED; ctx.beginPath();
      ctx.moveTo(x1 + Math.cos(ang) * 22, y1 + Math.sin(ang) * 22);
      ctx.lineTo(x1 + Math.cos(ang + 2.5) * 50, y1 + Math.sin(ang + 2.5) * 50);
      ctx.lineTo(x1 + Math.cos(ang - 2.5) * 50, y1 + Math.sin(ang - 2.5) * 50);
      ctx.closePath(); ctx.fill();
    }
  }

  // ---------- Cercle « feutre » ----------
  o_circle(ctx, o, lt) {
    const k = ease.outCubic(clamp(lt / 0.35));
    const rnd = mulberry32(7);
    ctx.strokeStyle = o.color || RED; ctx.lineWidth = 12; ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 10;
    ctx.beginPath();
    const N = 60, turns = 1.12;
    for (let i = 0; i <= N * k; i++) {
      const a = -Math.PI / 2 + (i / N) * Math.PI * 2 * turns;
      const wob = 1 + (rnd() - 0.5) * 0.03;
      const x = o.x + Math.cos(a) * o.rx * wob, y = o.y + Math.sin(a) * o.ry * wob;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  // ---------- Source / crédit (petit, lisible, zone sûre) ----------
  o_source(ctx, o, lt, dur) {
    const a = clamp(lt / 0.2) * (1 - clamp((lt - (dur - 0.15)) / 0.15));
    ctx.globalAlpha = a;
    ctx.textAlign = 'left';
    ctx.font = '700 30px Inter';
    const text = o.text;
    const w = ctx.measureText(text).width + 36;
    const x = o.x ?? 48, y = o.y ?? 1440;
    ctx.fillStyle = 'rgba(0,0,0,0.55)'; roundRect(ctx, x, y - 26, w, 52, 12); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.fillText(text, x + 18, y + 2);
  }

  // ---------- Bandeau nom (lower third) ----------
  o_lowerthird(ctx, o, lt, dur) {
    const k = ease.outExpo(clamp(lt / 0.35));
    const out = 1 - ease.inCubic(clamp((lt - (dur - 0.2)) / 0.2));
    const x = lerp(-700, o.x ?? 48, k) - (1 - out) * 800;
    const y = o.y ?? 1020;
    ctx.textAlign = 'left';
    ctx.font = '900 66px Montserrat';
    const w1 = ctx.measureText(o.name.toUpperCase()).width + 50;
    ctx.fillStyle = Y; ctx.fillRect(x, y - 46, w1, 92);
    ctx.fillStyle = BLACK; ctx.fillText(o.name.toUpperCase(), x + 25, y + 4);
    if (o.role) {
      ctx.font = '700 38px Inter';
      const w2 = ctx.measureText(o.role).width + 40;
      ctx.fillStyle = 'rgba(10,10,14,0.92)'; ctx.fillRect(x, y + 46, w2, 64);
      ctx.fillStyle = WHITE; ctx.fillText(o.role, x + 20, y + 80);
    }
  }

  // ---------- Barre de progression des actus (haut d'écran) ----------
  o_progress(ctx, o, lt, dur, t) {
    const n = o.total, cur = o.index;
    const x0 = 120, x1 = 900, y = o.y ?? 250, gap = 14;
    const w = (x1 - x0 - gap * (n - 1)) / n;
    const a = clamp(lt / 0.2);
    ctx.globalAlpha = a;
    for (let i = 0; i < n; i++) {
      const x = x0 + i * (w + gap);
      ctx.fillStyle = 'rgba(255,255,255,0.28)'; roundRect(ctx, x, y - 7, w, 14, 7); ctx.fill();
      let f = i < cur - 1 ? 1 : i === cur - 1 ? clamp((t - o.segStart) / (o.segEnd - o.segStart)) : 0;
      if (f > 0) { ctx.fillStyle = Y; roundRect(ctx, x, y - 7, w * f, 14, 7); ctx.fill(); }
    }
    ctx.font = '900 40px Montserrat';
    strokeFill(ctx, `ACTU ${cur}/${n}`, 540, y + 46, WHITE, BLACK, 8, false);
  }

  // ---------- Citation (machine à écrire) ----------
  o_quote(ctx, o, lt) {
    const sc = popScale(lt, 0.18, 1.06);
    ctx.translate(o.x ?? 520, o.y ?? 640); ctx.scale(sc, sc);
    const maxW = 820;
    ctx.font = '800 58px Inter';
    const shown = o.text.slice(0, Math.floor(clamp((lt - 0.1) / (o.typeDur ?? 1.0)) * o.text.length));
    const lines = wrapLines(ctx, '« ' + o.text + ' »', maxW);
    const h = lines.length * 72 + 110;
    ctx.fillStyle = 'rgba(255,255,255,0.96)'; roundRect(ctx, -maxW / 2 - 40, -h / 2, maxW + 80, h, 28); ctx.fill();
    ctx.fillStyle = BLACK; ctx.textAlign = 'left';
    let rem = ('« ' + shown).length;
    lines.forEach((l, i) => {
      const part = l.slice(0, Math.max(0, rem)); rem -= l.length + 1;
      ctx.fillText(part, -maxW / 2, -h / 2 + 70 + i * 72);
    });
    if (o.author) { ctx.font = '700 40px Inter'; ctx.fillStyle = '#555'; ctx.fillText('— ' + o.author, -maxW / 2, h / 2 - 34); }
  }

  // ---------- Marque discrète ----------
  o_brand(ctx, o, lt) {
    ctx.globalAlpha = 0.85 * clamp(lt / 0.3);
    ctx.textAlign = 'left';
    ctx.font = '800 34px Montserrat';
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; roundRect(ctx, 44, 142, ctx.measureText(o.text).width + 40, 56, 28); ctx.fill();
    ctx.fillStyle = WHITE; ctx.fillText(o.text, 64, 172);
  }

  // ---------- Image plein cadre fournie par l'utilisateur (optionnelle) ----------
  o_photo(ctx, o, lt) {
    const img = this.images.get(o.image);
    if (!img) return;
    const sc = popScale(lt, 0.2, 1.05);
    ctx.translate(o.x ?? 540, o.y ?? 700); ctx.rotate((o.rotate ?? -2) * Math.PI / 180); ctx.scale(sc, sc);
    const w = o.w ?? 760, h = o.h ?? (w * img.height / img.width);
    ctx.fillStyle = WHITE; ctx.fillRect(-w / 2 - 14, -h / 2 - 14, w + 28, h + 70);
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
    if (o.caption) { ctx.font = '700 34px Inter'; ctx.fillStyle = '#111'; ctx.fillText(o.caption, 0, h / 2 + 30); }
  }
}
