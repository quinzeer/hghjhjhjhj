// Contenus des écrans (mur LED, totems, téléphone) dessinés en Canvas2D.
// Règle éditoriale : aucun faux « screenshot » attribué à une personne réelle.
// Les écrans affichent notre habillage (titres, chiffres sourcés) ou des images fournies.
import { roundRect, wrapLines, drawSilhouette, fitText } from '../engine/textures.js';
import { clamp, ease, lerp } from '../engine/util.js';

const Y = '#FFD60A', RED = '#FF2D2D';

function bgGradient(ctx, w, h, a = '#0b1030', b = '#1a0830') {
  const g = ctx.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, a); g.addColorStop(1, b);
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
}

function scan(ctx, w, h, lt) {
  ctx.globalAlpha = 0.07; ctx.fillStyle = '#fff';
  for (let y = 0; y < h; y += 8) ctx.fillRect(0, y, w, 2);
  ctx.globalAlpha = 1;
}

const WALL_BG = {
  breaking: ['#2a0000', '#090000'], photo: ['#0a0d1a', '#140a1f'], grid: ['#07101f', '#150a22'], number: ['#0d0a00', '#000000'],
  map: ['#03101c', '#07061a'], date: ['#12020a', '#030005'], logo: ['#0a0a0a', '#1d1600'],
};

export function drawWall(ctx, w, h, spec = {}, lt = 0, images = new Map()) {
  if (!spec.portrait) return drawWallInner(ctx, w, h, spec, lt, images);
  // Plan « mur » en 9:16 : seul le tiers central est visible → contenu composé dans cette colonne.
  const [a, b] = WALL_BG[spec.kind] || [spec.bgA || '#0c0f2a', spec.bgB || '#23061f'];
  bgGradient(ctx, w, h, a, b);
  scan(ctx, w, h, 0);
  const cw = Math.round(w * 0.29), x0 = Math.round((w - cw) / 2);
  ctx.save();
  ctx.beginPath(); ctx.rect(x0, 0, cw, h); ctx.clip();
  ctx.translate(x0, 0);
  drawWallInner(ctx, cw, h, { ...spec, portrait: false }, lt, images);
  ctx.restore();
}

function drawWallInner(ctx, w, h, spec = {}, lt = 0, images = new Map()) {
  const kind = spec.kind || 'title';
  ctx.save();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  if (kind === 'breaking') {
    bgGradient(ctx, w, h, '#2a0000', '#090000');
    const pulse = 0.6 + 0.4 * Math.sin(lt * 8);
    ctx.fillStyle = `rgba(255,45,45,${0.25 * pulse})`; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = RED; ctx.fillRect(0, h * 0.72, w, h * 0.16);
    ctx.font = `900 ${h * 0.1}px Montserrat`; ctx.fillStyle = '#fff';
    const tick = (spec.ticker || 'ACTU INFLUENCEURS • ').repeat(6);
    ctx.textAlign = 'left'; ctx.fillText(tick, -((lt * 260) % (ctx.measureText(spec.ticker || 'ACTU INFLUENCEURS • ').width)), h * 0.8);
    ctx.textAlign = 'center';
    {
      fitText(ctx, (spec.title || 'ALERTE').toUpperCase(), w * 0.92, Math.round(h * 0.22), '900 {s}px Montserrat'); ctx.fillStyle = '#fff';
      ctx.fillText((spec.title || 'ALERTE').toUpperCase(), w / 2, h * 0.36);
      if (spec.subtitle) { fitText(ctx, spec.subtitle.toUpperCase(), w * 0.92, Math.round(h * 0.085), '800 {s}px Montserrat'); ctx.fillStyle = Y; ctx.fillText(spec.subtitle.toUpperCase(), w / 2, h * 0.58); }
    }
  } else if (kind === 'photo') {
    const img = images.get(spec.image);
    bgGradient(ctx, w, h, '#0a0d1a', '#140a1f');
    const pw = h * 0.72, ph = h * 0.86;
    if (img) {
      const s = Math.max(pw / img.width, ph / img.height);
      ctx.save(); roundRect(ctx, w * 0.08, h * 0.07, pw, ph, 18); ctx.clip();
      ctx.drawImage(img, w * 0.08 + (pw - img.width * s) / 2, h * 0.07 + (ph - img.height * s) / 2, img.width * s, img.height * s); ctx.restore();
    } else drawSilhouette(ctx, w * 0.08, h * 0.07, pw, ph, { accent: spec.accent || Y });
    ctx.textAlign = 'left';
    const tx = w * 0.08 + pw + w * 0.05, tw = w - tx - w * 0.06;
    ctx.font = `900 ${h * 0.14}px Montserrat`; ctx.fillStyle = '#fff';
    const s1 = fitText(ctx, (spec.name || '').toUpperCase(), tw, Math.round(h * 0.14), '900 {s}px Montserrat');
    ctx.fillText((spec.name || '').toUpperCase(), tx, h * 0.3);
    ctx.font = `800 ${h * 0.065}px Montserrat`; ctx.fillStyle = spec.accent || Y;
    wrapLines(ctx, (spec.line || '').toUpperCase(), tw).forEach((l, i) => ctx.fillText(l, tx, h * 0.3 + s1 * 0.9 + i * h * 0.08));
  } else if (kind === 'grid') {
    bgGradient(ctx, w, h, '#07101f', '#150a22');
    const items = spec.items || [];
    const cols = Math.min(items.length, spec.cols || 4), rows = Math.ceil(items.length / cols);
    const cw = w / (cols + 0.4), ch = h / (rows + 0.35);
    items.forEach((it, i) => {
      const cx = (i % cols + 0.7) * cw, cy = (Math.floor(i / cols) + 0.62) * ch;
      const appear = clamp((lt - i * 0.08) / 0.25);
      if (appear <= 0) return;
      ctx.save(); ctx.globalAlpha = appear; ctx.translate(cx, cy); ctx.scale(lerp(0.8, 1, ease.outBack(appear)), lerp(0.8, 1, ease.outBack(appear)));
      const img = images.get(it.image);
      const pw = cw * 0.82, ph = ch * 0.72;
      if (img) { const s = Math.max(pw / img.width, ph / img.height); ctx.save(); roundRect(ctx, -pw / 2, -ph / 2 - ch * 0.08, pw, ph, 14); ctx.clip(); ctx.drawImage(img, -img.width * s / 2, -ph / 2 - ch * 0.08 + (ph - img.height * s) / 2, img.width * s, img.height * s); ctx.restore(); }
      else drawSilhouette(ctx, -pw / 2, -ph / 2 - ch * 0.08, pw, ph, { accent: it.status === 'out' ? RED : Y });
      ctx.font = `900 ${ch * 0.11}px Montserrat`; ctx.fillStyle = '#fff';
      fitText(ctx, it.name.toUpperCase(), pw, Math.round(ch * 0.11), '900 {s}px Montserrat');
      ctx.fillText(it.name.toUpperCase(), 0, ph / 2 + ch * 0.02);
      if (it.status === 'out') { ctx.strokeStyle = RED; ctx.lineWidth = ch * 0.03; ctx.beginPath(); ctx.moveTo(-pw / 2, -ph / 2 - ch * 0.08); ctx.lineTo(pw / 2, ph / 2 - ch * 0.08); ctx.moveTo(pw / 2, -ph / 2 - ch * 0.08); ctx.lineTo(-pw / 2, ph / 2 - ch * 0.08); ctx.stroke(); }
      ctx.restore();
    });
  } else if (kind === 'number') {
    bgGradient(ctx, w, h, '#0d0a00', '#000000');
    const rg = ctx.createRadialGradient(w / 2, h * 0.45, 0, w / 2, h * 0.45, w * 0.45);
    rg.addColorStop(0, 'rgba(255,190,0,0.28)'); rg.addColorStop(1, 'rgba(255,190,0,0)');
    ctx.fillStyle = rg; ctx.fillRect(0, 0, w, h);
    const k = ease.outExpo(clamp(lt / 1.2));
    const v = lerp(spec.from || 0, spec.to || 0, k);
    const txt = (spec.prefix || '') + v.toFixed(spec.decimals || 0).replace('.', ',') + (spec.suffix || '');
    fitText(ctx, txt, w * 0.92, Math.round(h * 0.42), '{s}px Anton'); ctx.fillStyle = Y; ctx.shadowColor = 'rgba(255,200,0,0.8)'; ctx.shadowBlur = 40;
    ctx.fillText(txt, w / 2, h * 0.45); ctx.shadowBlur = 0;
    if (spec.label) { ctx.fillStyle = '#fff'; wrapLines(ctx, spec.label.toUpperCase(), w * 0.9).length; fitText(ctx, spec.label.toUpperCase(), w * 0.92, Math.round(h * 0.08), '900 {s}px Montserrat'); ctx.fillText(spec.label.toUpperCase(), w / 2, h * 0.78); }
  } else if (kind === 'map') {
    bgGradient(ctx, w, h, '#03101c', '#07061a');
    ctx.strokeStyle = 'rgba(80,160,255,0.12)'; ctx.lineWidth = 1;
    for (let x = 0; x < w; x += w / 24) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (let y = 0; y < h; y += h / 14) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    const T = spec.target;
    const tx = T.x * w, ty = T.y * h;
    (spec.cities || []).forEach((c, i) => {
      const x = c.x * w, y = c.y * h;
      const k = ease.outCubic(clamp((lt - 0.2 - i * 0.25) / 0.7));
      const mx = (x + tx) / 2, my = Math.min(y, ty) - h * 0.18;
      ctx.strokeStyle = spec.accent || Y; ctx.lineWidth = h * 0.008; ctx.setLineDash([]);
      ctx.beginPath();
      for (let s2 = 0; s2 <= 40 * k; s2++) { const u = s2 / 40; const px = (1 - u) * (1 - u) * x + 2 * (1 - u) * u * mx + u * u * tx; const py = (1 - u) * (1 - u) * y + 2 * (1 - u) * u * my + u * u * ty; s2 === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py); }
      ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y, h * 0.014, 0, Math.PI * 2); ctx.fill();
      ctx.font = `800 ${h * 0.05}px Montserrat`; ctx.fillText(c.name.toUpperCase(), x, y + h * 0.06);
    });
    const pulse = 1 + 0.25 * Math.sin(lt * 6);
    ctx.fillStyle = RED; ctx.beginPath(); ctx.arc(tx, ty, h * 0.022 * pulse, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = RED; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(tx, ty, h * 0.05 * pulse, 0, Math.PI * 2); ctx.stroke();
    ctx.font = `900 ${h * 0.075}px Montserrat`; ctx.fillStyle = '#fff'; ctx.fillText(T.name.toUpperCase(), tx, ty - h * 0.09);
    if (spec.title) { fitText(ctx, spec.title.toUpperCase(), w * 0.9, Math.round(h * 0.09), '900 {s}px Montserrat'); ctx.fillStyle = spec.accent || Y; ctx.fillText(spec.title.toUpperCase(), w / 2, h * 0.1); }
  } else if (kind === 'date') {
    bgGradient(ctx, w, h, '#12020a', '#030005');
    fitText(ctx, (spec.title || '').toUpperCase(), w * 0.9, Math.round(h * 0.3), '{s}px Anton'); ctx.fillStyle = '#fff';
    ctx.fillText((spec.title || '').toUpperCase(), w / 2, h * 0.43);
    if (spec.strike) { const tw = ctx.measureText((spec.title || '').toUpperCase()).width; ctx.strokeStyle = RED; ctx.lineWidth = h * 0.03; ctx.beginPath(); ctx.moveTo(w / 2 - tw / 2 - 20, h * 0.47); ctx.lineTo(w / 2 + tw / 2 + 20, h * 0.39); ctx.stroke(); }
    if (spec.subtitle) { fitText(ctx, spec.subtitle.toUpperCase(), w * 0.92, Math.round(h * 0.085), '900 {s}px Montserrat'); ctx.fillStyle = spec.accent || Y; ctx.fillText(spec.subtitle.toUpperCase(), w / 2, h * 0.73); }
  } else if (kind === 'logo') {
    bgGradient(ctx, w, h, '#0a0a0a', '#1d1600');
    ctx.font = `900 ${h * 0.16}px Montserrat`; ctx.fillStyle = '#fff'; ctx.fillText((spec.title || 'ACTU').toUpperCase(), w / 2, h * 0.42);
    ctx.font = `900 ${h * 0.09}px Montserrat`; ctx.fillStyle = Y; ctx.fillText((spec.subtitle || '').toUpperCase(), w / 2, h * 0.6);
  } else {
    bgGradient(ctx, w, h, spec.bgA || '#0c0f2a', spec.bgB || '#23061f');
    const lines = Array.isArray(spec.title) ? spec.title : [spec.title || ''];
    const size = h * (spec.size || 0.2);
    lines.forEach((l, i) => {
      ctx.font = `900 ${size}px Montserrat`;
      fitText(ctx, l.toUpperCase(), w * 0.9, Math.round(size), '900 {s}px Montserrat');
      ctx.fillStyle = i === lines.length - 1 ? (spec.accent || Y) : '#fff';
      ctx.fillText(l.toUpperCase(), w / 2, h * 0.5 + (i - (lines.length - 1) / 2) * size * 1.05);
    });
  }
  scan(ctx, w, h, lt);
  ctx.restore();
}

// Écran du téléphone : notifications de NOTRE média, ou profil public (chiffres sourcés).
export function drawPhone(ctx, w, h, spec = {}, lt = 0, images = new Map()) {
  ctx.save();
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
  const r = w * 0.13;
  ctx.save(); roundRect(ctx, w * 0.018, h * 0.009, w * 0.964, h * 0.982, r); ctx.clip();
  const img = images.get(spec.image);
  if (img) {
    const s = Math.max(w / img.width, h / img.height);
    ctx.drawImage(img, (w - img.width * s) / 2, (h - img.height * s) / 2, img.width * s, img.height * s);
    ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(0, 0, w, h);
  } else {
    const g = ctx.createLinearGradient(0, 0, w * 0.6, h);
    g.addColorStop(0, spec.bgA || '#3a1c71'); g.addColorStop(0.55, spec.bgB || '#d76d77'); g.addColorStop(1, spec.bgC || '#ffaf7b');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    ctx.globalAlpha = 0.25; ctx.fillStyle = '#fff';
    ctx.beginPath(); ctx.arc(w * 0.2, h * 0.3, w * 0.5, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1;
  }
  ctx.textBaseline = 'middle';
  // Barre d'état + Dynamic Island.
  ctx.fillStyle = '#fff'; ctx.font = `600 ${w * 0.045}px Inter`; ctx.textAlign = 'left'; ctx.fillText(spec.clock || '21:47', w * 0.09, h * 0.028);
  ctx.textAlign = 'right'; ctx.fillText('5G ▮▮▮', w * 0.91, h * 0.028);
  ctx.fillStyle = '#000'; roundRect(ctx, w * 0.35, h * 0.012, w * 0.3, h * 0.036, h * 0.018); ctx.fill();
  ctx.textAlign = 'center';
  if ((spec.kind || 'lock') === 'lock') {
    ctx.fillStyle = '#fff'; ctx.font = `300 ${w * 0.27}px Inter`; ctx.fillText(spec.clock || '21:47', w / 2, h * 0.16);
    ctx.font = `500 ${w * 0.05}px Inter`; ctx.fillText(spec.date || 'dimanche 28 septembre', w / 2, h * 0.075);
    const notes = spec.notifications || [];
    notes.forEach((n, i) => {
      const t0 = (n.at ?? i * 0.35);
      const k = ease.outBack(clamp((lt - t0) / 0.3));
      if (k <= 0) return;
      const y = h * 0.3 + i * h * 0.13;
      ctx.save(); ctx.translate(w / 2, y + (1 - k) * -h * 0.05); ctx.globalAlpha = clamp((lt - t0) / 0.15);
      ctx.fillStyle = 'rgba(245,245,250,0.82)'; roundRect(ctx, -w * 0.44, -h * 0.055, w * 0.88, h * 0.11, w * 0.06); ctx.fill();
      ctx.fillStyle = n.color || Y; roundRect(ctx, -w * 0.4, -h * 0.03, w * 0.11, w * 0.11, w * 0.025); ctx.fill();
      ctx.fillStyle = '#000'; ctx.font = `900 ${w * 0.05}px Montserrat`; ctx.fillText(n.icon || '!', -w * 0.345, -h * 0.03 + w * 0.057);
      ctx.textAlign = 'left'; ctx.fillStyle = '#111';
      ctx.font = `800 ${w * 0.042}px Inter`; ctx.fillText(n.app || 'ACTU INFLUENCEURS', -w * 0.25, -h * 0.028);
      ctx.font = `600 ${w * 0.043}px Inter`;
      wrapLines(ctx, n.text, w * 0.62).slice(0, 2).forEach((l, j) => ctx.fillText(l, -w * 0.25, -h * 0.003 + j * h * 0.024));
      ctx.textAlign = 'right'; ctx.fillStyle = '#666'; ctx.font = `500 ${w * 0.036}px Inter`; ctx.fillText(n.time || 'maintenant', w * 0.4, -h * 0.028);
      ctx.restore(); ctx.textAlign = 'center';
    });
  } else if (spec.kind === 'live') {
    const g2 = ctx.createLinearGradient(0, 0, 0, h); g2.addColorStop(0, '#1a0b2e'); g2.addColorStop(1, '#05030a');
    ctx.fillStyle = g2; ctx.fillRect(0, 0, w, h);
    const spot = ctx.createRadialGradient(w / 2, h * 0.42, 0, w / 2, h * 0.42, w * 0.7); spot.addColorStop(0, 'rgba(255,80,160,0.35)'); spot.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = spot; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = RED; roundRect(ctx, w * 0.07, h * 0.065, w * 0.36, h * 0.042, h * 0.012); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.font = `900 ${w * 0.05}px Montserrat`; ctx.textAlign = 'left';
    ctx.fillText('● EN DIRECT', w * 0.1, h * 0.087);
    const kv = ease.outExpo(clamp(lt / (spec.countDur || 1.3)));
    const v = Math.round((spec.viewers || 0) * kv).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0');
    ctx.fillStyle = 'rgba(0,0,0,0.45)'; roundRect(ctx, w * 0.46, h * 0.065, w * 0.47, h * 0.042, h * 0.012); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.fillText('👁 ' + v, w * 0.49, h * 0.087);
    ctx.textAlign = 'center';
    ctx.font = `900 ${w * 0.11}px Montserrat`; ctx.fillStyle = '#fff';
    wrapLines(ctx, (spec.title || '').toUpperCase(), w * 0.8).forEach((l, i) => ctx.fillText(l, w / 2, h * 0.36 + i * w * 0.12));
    for (let i = 0; i < 14; i++) {
      const tt = (lt * 0.8 + i * 0.37) % 2.2;
      const x = w * (0.72 + 0.12 * Math.sin(i * 2.1 + tt * 2)), y = h * (0.9 - tt * 0.3);
      ctx.globalAlpha = clamp(1 - tt / 2.2); ctx.font = `${w * (0.06 + (i % 3) * 0.015)}px "Noto Color Emoji"`; ctx.fillText(i % 4 === 0 ? '🔥' : '❤️', x, y);
    }
    ctx.globalAlpha = 1; ctx.textAlign = 'left';
    (spec.chat || []).forEach((m, i) => {
      const k = clamp((lt - 0.3 - i * 0.28) / 0.2); if (k <= 0) return;
      ctx.globalAlpha = k; ctx.fillStyle = 'rgba(0,0,0,0.4)'; roundRect(ctx, w * 0.06, h * (0.66 + i * 0.055), w * 0.55, h * 0.045, h * 0.02); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.font = `700 ${w * 0.042}px Inter`; ctx.fillText(m, w * 0.09, h * (0.683 + i * 0.055));
    });
    ctx.globalAlpha = 1; ctx.textAlign = 'center';
  } else if (spec.kind === 'video') {
    ctx.fillStyle = '#0b0b0f'; ctx.fillRect(0, 0, w, h);
    const th = w * 0.5625, ty0 = h * 0.2;
    const tg = ctx.createLinearGradient(0, ty0, w, ty0 + th); tg.addColorStop(0, '#2b1d0e'); tg.addColorStop(1, '#0e1a2b');
    ctx.fillStyle = tg; ctx.fillRect(0, ty0, w, th);
    ctx.font = `900 ${w * 0.1}px Montserrat`; ctx.fillStyle = Y;
    wrapLines(ctx, (spec.thumb || '').toUpperCase(), w * 0.85).forEach((l, i) => ctx.fillText(l, w / 2, ty0 + th * 0.4 + i * w * 0.11));
    ctx.textAlign = 'left'; ctx.fillStyle = '#fff'; ctx.font = `800 ${w * 0.055}px Inter`;
    wrapLines(ctx, spec.title || '', w * 0.86).slice(0, 2).forEach((l, i) => ctx.fillText(l, w * 0.07, ty0 + th + h * 0.045 + i * w * 0.07));
    ctx.fillStyle = 'rgba(255,255,255,0.65)'; ctx.font = `600 ${w * 0.045}px Inter`;
    ctx.fillText(spec.channel || '', w * 0.07, ty0 + th + h * 0.14);
    const kv = ease.outExpo(clamp((lt - 0.2) / 1.3));
    const vv = Math.round((spec.views || 0) * kv).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0');
    ctx.fillStyle = Y; ctx.font = `900 ${w * 0.1}px Montserrat`; ctx.textAlign = 'center';
    ctx.fillText(vv + (spec.suffix || ' vues'), w / 2, h * 0.78);
  } else if (spec.kind === 'profile') {
    const cx = w / 2, cy = h * 0.28;
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, w * 0.2, 0, Math.PI * 2); ctx.clip();
    const pimg = images.get(spec.avatar);
    if (pimg) { const s = Math.max(w * 0.4 / pimg.width, w * 0.4 / pimg.height); ctx.drawImage(pimg, cx - pimg.width * s / 2, cy - pimg.height * s / 2, pimg.width * s, pimg.height * s); }
    else drawSilhouette(ctx, cx - w * 0.2, cy - w * 0.2, w * 0.4, w * 0.4, { accent: 'rgba(0,0,0,0)' });
    ctx.restore();
    ctx.strokeStyle = Y; ctx.lineWidth = w * 0.015; ctx.beginPath(); ctx.arc(cx, cy, w * 0.21, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = `900 ${w * 0.085}px Montserrat`; ctx.fillText((spec.name || '').toUpperCase(), cx, h * 0.41);
    ctx.font = `600 ${w * 0.045}px Inter`; ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fillText(spec.handle || '', cx, h * 0.45);
    (spec.stats || []).forEach((st, i) => {
      const k = ease.outExpo(clamp((lt - 0.2 - i * 0.2) / 1.2));
      const y = h * 0.55 + i * h * 0.11;
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; roundRect(ctx, w * 0.08, y - h * 0.045, w * 0.84, h * 0.09, w * 0.04); ctx.fill();
      ctx.textAlign = 'left'; ctx.fillStyle = '#fff'; ctx.font = `700 ${w * 0.045}px Inter`; ctx.fillText(st.label, w * 0.13, y);
      ctx.textAlign = 'right'; ctx.fillStyle = Y; ctx.font = `900 ${w * 0.07}px Montserrat`;
      ctx.fillText((st.prefix || '') + (st.to * k).toFixed(st.decimals || 0).replace('.', ',') + (st.suffix || ''), w * 0.87, y + w * 0.005);
      ctx.textAlign = 'center';
    });
  }
  ctx.restore();
  ctx.restore();
}
