// Habillage « MrBeast / TikTok » dessiné en Canvas 2D par-dessus le rendu 3D.
// Zones sûres TikTok (1080×1920) : haut < 160 px (onglets), bas > 1560 px (légende), droite > 950 px entre 880 et 1560 px (boutons).
import { COUNTRIES, flagCanvas } from './countries.js';
import { P, STATE, sampleAt } from './sim.js';

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const easeOutBack = (t) => { t = clamp(t, 0, 1); const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
const F_DISPLAY = '"Anton", "Impact", "Arial Narrow Bold", sans-serif';
const F_CAPTION = '"Montserrat", "Arial Black", "Helvetica Neue", sans-serif';
const YELLOW = '#FFE11A', RED = '#FF2D3D', GOLD = '#FFC83D';

function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function rr(c, x, y, w, h, r) { c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); }
function grey(cv) {
  const g = mk(cv.width, cv.height), c = g.getContext('2d');
  c.drawImage(cv, 0, 0);
  const im = c.getImageData(0, 0, g.width, g.height), d = im.data;
  for (let i = 0; i < d.length; i += 4) { const l = (d[i] * 0.3 + d[i + 1] * 0.59 + d[i + 2] * 0.11) * 0.45; d[i] = d[i + 1] = d[i + 2] = l; }
  c.putImageData(im, 0, 0);
  return g;
}
// texte « sticker » : contour noir épais + ombre portée
function stroked(c, text, x, y, size, fill, font = F_DISPLAY, stroke = 0.16, align = 'center') {
  c.font = `${font === F_CAPTION ? '900 ' : ''}${size}px ${font}`;
  c.textAlign = align; c.textBaseline = 'middle';
  c.lineJoin = 'round'; c.miterLimit = 2;
  c.shadowColor = 'rgba(0,0,0,0.55)'; c.shadowOffsetY = size * 0.06; c.shadowBlur = size * 0.08;
  c.lineWidth = size * stroke; c.strokeStyle = '#000'; c.strokeText(text, x, y);
  c.shadowColor = 'transparent';
  c.fillStyle = fill; c.fillText(text, x, y);
}

export class Hud {
  constructor(canvas, D, arena, opts = {}) {
    this.c = canvas.getContext('2d');
    this.W = canvas.width; this.H = canvas.height;
    this.D = D; this.arena = arena; this.rec = D.rec;
    this.episode = opts.episode || 1;
    this.flags = COUNTRIES.map((c) => flagCanvas(c.code, 240, 160));
    this.greys = this.flags.map(grey);
    this.elimV = new Array(this.rec.N).fill(Infinity);
    this.rankOf = new Array(this.rec.N).fill(1);
    for (const e of D.A.E) { this.elimV[e.i] = D.vOfSim(e.t); this.rankOf[e.i] = e.rank; }
    this.ranking = [...Array(this.rec.N).keys()].sort((a, b) => this.rankOf[a] - this.rankOf[b]);
  }

  draw(v) {
    const c = this.c, D = this.D, H = D.hud;
    const { g } = D.simAt(v);
    this.labels(v, g);
    if (v >= 2.35 && v < H.vFin + 0.3) this.grid(v, g);
    if (v >= H.vFin - 0.05 && v < H.vWin + 0.5) this.vsCard(v);
    this.toasts(v, g);
    this.banners(v);
    if (g.kind === 'replay') this.replayBadge(v);
    if (v >= H.vWin + 0.15 && v < H.vBoard && g.kind !== 'replay') this.winnerCard(v);
    if (v >= H.vBoard) this.board(v);
    this.captions(v);
    this.watermark(v);
  }

  // étiquettes pays au-dessus des billes (plans larges)
  labels(v, g) {
    const c = this.c, D = this.D;
    if (v < 3 || v >= D.hud.vBoard) return;
    const cam = D.camAt(v);
    if (cam.type === 'winner' || cam.type === 'replay') return;
    const { s } = D.simAt(v);
    const { A } = sampleAt(this.rec, s);
    c.font = `700 21px ${F_CAPTION}`; c.textAlign = 'center'; c.textBaseline = 'middle';
    for (let i = 0; i < this.rec.N; i++) {
      const out = A.st[i] === STATE.FALL;
      const since = v - this.elimV[i];
      if (out && since > 0.9) continue;
      const b = this.arena.balls[i];
      if (!b.visible) continue;
      const p = this.arena.project([b.position.x, b.position.y + P.r * 1.05, b.position.z]);
      if (p.z > 1 || p.x < -40 || p.x > this.W + 40 || p.y < 0 || p.y > this.H) continue;
      const code = COUNTRIES[i].code;
      const w = 62, h = 30, y = p.y - 22;
      c.globalAlpha = out ? clamp(1 - since / 0.9, 0, 1) : 0.9;
      rr(c, p.x - w / 2, y - h / 2, w, h, 9);
      c.fillStyle = out ? 'rgba(220,20,40,0.92)' : 'rgba(8,10,18,0.72)'; c.fill();
      c.fillStyle = '#fff'; c.fillText(code, p.x, y + 1);
    }
    c.globalAlpha = 1;
  }

  // grille des 32 drapeaux (on y cherche son pays)
  grid(v, g) {
    const c = this.c, D = this.D;
    const cw = 96, ch = 64, gap = 9, cols = 8;
    const x0 = (this.W - (cols * cw + (cols - 1) * gap)) / 2, y0 = 186;
    const fadeOut = clamp((D.hud.vFin + 0.3 - v) / 0.3, 0, 1);
    const inK = easeOut((v - 2.35) / 0.35);
    c.save();
    c.globalAlpha = fadeOut;
    rr(c, x0 - 18, y0 - 16, cols * cw + (cols - 1) * gap + 36, 4 * ch + 3 * gap + 32, 22);
    c.fillStyle = `rgba(6,8,16,${0.62 * inK})`; c.fill();
    c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 2; c.stroke();
    const final = g.kind !== 'live';
    for (let i = 0; i < 32; i++) {
      const col = i % cols, row = Math.floor(i / cols);
      const appear = 2.35 + i * 0.028;
      const k = easeOutBack((v - appear) / 0.28);
      if (k <= 0) continue;
      const x = x0 + col * (cw + gap), y = y0 + row * (ch + gap);
      const ev = this.elimV[i];
      const out = final ? this.rankOf[i] > 1 : v >= ev;
      const since = v - ev;
      let sc = k;
      if (out && since < 0.45) sc *= 1 + 0.35 * Math.sin((since / 0.45) * Math.PI);
      c.save();
      c.translate(x + cw / 2, y + ch / 2); c.scale(sc, sc);
      rr(c, -cw / 2, -ch / 2, cw, ch, 9); c.save(); c.clip();
      c.drawImage(out ? this.greys[i] : this.flags[i], -cw / 2, -ch / 2, cw, ch);
      c.restore();
      rr(c, -cw / 2, -ch / 2, cw, ch, 9);
      c.lineWidth = 3; c.strokeStyle = out ? 'rgba(255,45,61,0.9)' : 'rgba(255,255,255,0.85)'; c.stroke();
      if (out) {
        c.strokeStyle = RED; c.lineWidth = 7; c.lineCap = 'round';
        c.beginPath(); c.moveTo(-cw * 0.28, -ch * 0.28); c.lineTo(cw * 0.28, ch * 0.28); c.moveTo(cw * 0.28, -ch * 0.28); c.lineTo(-cw * 0.28, ch * 0.28); c.stroke();
        if (since < 0.35) { rr(c, -cw / 2, -ch / 2, cw, ch, 9); c.fillStyle = `rgba(255,40,40,${0.7 * (1 - since / 0.35)})`; c.fill(); }
      }
      c.restore();
    }
    // compteur « restants »
    const alive = this.aliveAt(v);
    const bx = this.W / 2, by = y0 + 4 * ch + 3 * gap + 40;
    const pop = this.popAt(v);
    c.save(); c.translate(bx, by); c.scale(1 + pop * 0.25, 1 + pop * 0.25);
    rr(c, -150, -34, 300, 68, 34); c.fillStyle = pop > 0.05 ? RED : '#111'; c.fill();
    c.lineWidth = 4; c.strokeStyle = '#fff'; c.stroke();
    c.font = `52px ${F_DISPLAY}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fff';
    c.fillText(`${alive} RESTANTS`, 0, 3);
    c.restore();
    c.restore();
  }
  aliveAt(v) { let n = 32; for (const x of this.elimV) if (v >= x) n--; return n; }
  popAt(v) { let p = 0; for (const x of this.elimV) if (v >= x && v < x + 0.35) p = Math.max(p, 1 - (v - x) / 0.35); return p; }

  // carte « VS » de la finale
  vsCard(v) {
    const c = this.c, D = this.D;
    const k = easeOutBack((v - D.hud.vFin) / 0.45);
    const [a, b] = [D.A.loser, this.rec.winner];
    const lostV = this.elimV[a];
    const out = clamp((v - D.hud.vWin - 0.15) / 0.35, 0, 1);
    const y = 250 - 420 * out * out;
    c.save();
    c.globalAlpha = 1 - out;
    for (const [i, side] of [[b, -1], [a, 1]]) {
      const x = this.W / 2 + side * 250 * k;
      const out = v >= lostV && i === a;
      c.save(); c.translate(x, y); c.rotate(side * 0.04);
      rr(c, -150, -100, 300, 200, 18); c.save(); c.clip();
      c.drawImage(out ? this.greys[i] : this.flags[i], -150, -100, 300, 200); c.restore();
      rr(c, -150, -100, 300, 200, 18); c.lineWidth = 7; c.strokeStyle = out ? RED : '#fff'; c.stroke();
      stroked(c, COUNTRIES[i].name.toUpperCase(), 0, 145, COUNTRIES[i].name.length > 9 ? 50 : 62, out ? '#888' : '#fff');
      c.restore();
    }
    const p = 1 + 0.08 * Math.sin(v * 8);
    c.translate(this.W / 2, y); c.scale(k * p, k * p);
    stroked(c, 'VS', 0, 0, 130, YELLOW, F_DISPLAY, 0.2);
    c.restore();
  }

  toasts(v, g) {
    const c = this.c, D = this.D;
    if (g.kind !== 'live' || v >= D.hud.vFin) return;
    const act = D.hud.toasts.filter((t) => v >= t.v && v < t.v + 1.7).slice(-2);
    act.forEach((t, j) => {
      const since = v - t.v;
      const kin = easeOutBack(since / 0.32), kout = clamp((1.7 - since) / 0.25, 0, 1);
      const y = 600 + j * 112;
      const x = lerp(-520, 40, kin);
      c.save(); c.globalAlpha = kout; c.translate(x, y);
      rr(c, 0, -46, 560, 92, 16); c.fillStyle = 'rgba(8,10,18,0.86)'; c.fill();
      rr(c, 0, -46, 12, 92, 6); c.fillStyle = RED; c.fill();
      rr(c, 26, -32, 96, 64, 8); c.save(); c.clip(); c.drawImage(this.flags[t.i], 26, -32, 96, 64); c.restore();
      c.font = `54px ${F_DISPLAY}`; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillStyle = '#fff';
      const name = COUNTRIES[t.i].name.toUpperCase();
      c.fillText(name, 140, 2);
      const w = c.measureText(name).width;
      c.font = `40px ${F_DISPLAY}`; c.fillStyle = RED;
      c.fillText(`OUT · ${t.rank}e`, 140 + w + 18, 4);
      c.restore();
    });
  }

  banners(v) {
    const c = this.c;
    for (const b of this.D.hud.banners) {
      const t = v - b.v;
      if (t < 0 || t > b.dur) continue;
      const kin = easeOutBack(t / 0.3), kout = clamp((b.dur - t) / 0.3, 0, 1);
      c.save(); c.globalAlpha = kout;
      if (b.kind === 'hook') {
        const y = 640;
        c.translate(this.W / 2, y); c.scale(lerp(1.8, 1, kin), lerp(1.8, 1, kin)); c.rotate(-0.035);
        stroked(c, b.title, 0, 0, 210, '#fff', F_DISPLAY, 0.14);
        const k2 = easeOutBack((t - 0.35) / 0.3);
        if (k2 > 0) {
          c.save(); c.translate(0, 170); c.scale(k2, k2); c.rotate(0.02);
          rr(c, -330, -58, 660, 116, 14); c.fillStyle = RED; c.fill(); c.lineWidth = 8; c.strokeStyle = '#000'; c.stroke();
          c.font = `92px ${F_DISPLAY}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fff'; c.fillText(b.sub, 0, 6);
          c.restore();
        }
      } else if (b.kind === 'round') {
        c.translate(this.W / 2, 860); c.scale(lerp(2.4, 1, kin), lerp(2.4, 1, kin)); c.rotate(-0.04);
        stroked(c, b.title, 0, -40, 190, YELLOW, F_DISPLAY, 0.14);
        rr(c, -380, 60, 760, 104, 12); c.fillStyle = RED; c.fill(); c.lineWidth = 8; c.strokeStyle = '#000'; c.stroke();
        c.font = `78px ${F_DISPLAY}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fff'; c.fillText(b.sub, 0, 116);
      } else if (b.kind === 'final') {
        c.translate(this.W / 2, 900); c.scale(lerp(3, 1, kin), lerp(3, 1, kin)); c.rotate(-0.04);
        stroked(c, b.title, 0, 0, 250, YELLOW, F_DISPLAY, 0.13);
      }
      c.restore();
    }
  }

  replayBadge(v) {
    const c = this.c, y = 250;
    c.save();
    rr(c, 60, y - 40, 330, 80, 14); c.fillStyle = 'rgba(0,0,0,0.75)'; c.fill();
    if (Math.floor(v * 3) % 2 === 0) { c.beginPath(); c.arc(100, y, 16, 0, Math.PI * 2); c.fillStyle = RED; c.fill(); }
    c.font = `58px ${F_DISPLAY}`; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillStyle = '#fff'; c.fillText('REPLAY', 132, y + 3);
    c.font = `40px ${F_DISPLAY}`; c.fillStyle = YELLOW; c.fillText('×0,4', 305, y + 5);
    c.restore();
  }

  winnerCard(v) {
    const c = this.c, D = this.D, H = D.hud;
    const i = this.rec.winner;
    const t = v - (H.vWin + 0.15);
    const t2 = v >= H.vCel0 ? v - H.vCel0 : t;
    const k = easeOutBack(t2 / 0.4);
    const y = 470;
    const sc = 1;
    c.save(); c.translate(this.W / 2, y); c.scale(k * sc, k * sc);
    // couronne
    c.save(); c.translate(0, -175);
    c.beginPath(); c.moveTo(-90, 40); c.lineTo(-100, -40); c.lineTo(-45, 5); c.lineTo(0, -60); c.lineTo(45, 5); c.lineTo(100, -40); c.lineTo(90, 40); c.closePath();
    const gr = c.createLinearGradient(0, -60, 0, 40); gr.addColorStop(0, '#FFF3A0'); gr.addColorStop(0.5, GOLD); gr.addColorStop(1, '#C27A00');
    c.fillStyle = gr; c.fill(); c.lineWidth = 8; c.strokeStyle = '#000'; c.stroke();
    c.restore();
    stroked(c, 'VICTOIRE', 0, -60, 120, YELLOW, F_DISPLAY, 0.14);
    const name = COUNTRIES[i].name.toUpperCase();
    stroked(c, name, 0, 70, name.length > 9 ? 120 : 150, '#fff', F_DISPLAY, 0.13);
    c.restore();
  }

  board(v) {
    const c = this.c, D = this.D;
    const t = v - D.hud.vBoard;
    c.save();
    c.fillStyle = `rgba(4,5,10,${0.8 * easeOut(t / 0.35)})`; c.fillRect(0, 0, this.W, this.H);
    const k = easeOutBack(t / 0.35);
    c.save(); c.translate(this.W / 2, 245); c.scale(k, k);
    stroked(c, 'CLASSEMENT FINAL', 0, 0, 104, YELLOW, F_DISPLAY, 0.14);
    c.restore();
    const rowH = 70, top = 350;
    for (let n = 0; n < 32; n++) {
      const i = this.ranking[n];
      const col = n < 16 ? 0 : 1, row = n % 16;
      const x = col ? 548 : 62, y = top + row * rowH;
      const kk = easeOutBack((t - 0.15 - n * 0.035) / 0.25);
      if (kk <= 0) continue;
      c.save(); c.translate(x, y); c.scale(kk, 1);
      const podium = n < 3 ? [GOLD, '#D9DEE6', '#E09A5A'][n] : null;
      rr(c, 0, -28, col ? 396 : 460, 56, 12); c.fillStyle = podium ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.06)'; c.fill();
      if (podium) { c.lineWidth = 3; c.strokeStyle = podium; c.stroke(); }
      c.font = `38px ${F_DISPLAY}`; c.textAlign = 'right'; c.textBaseline = 'middle'; c.fillStyle = podium || '#9aa3b5';
      c.fillText(`${n + 1}`, 52, 3);
      rr(c, 64, -20, 60, 40, 5); c.save(); c.clip(); c.drawImage(this.flags[i], 64, -20, 60, 40); c.restore();
      c.textAlign = 'left'; c.fillStyle = '#fff'; c.font = `36px ${F_DISPLAY}`;
      c.fillText(COUNTRIES[i].name.toUpperCase(), 138, 3);
      c.restore();
    }
    c.restore();
  }

  captions(v) {
    const c = this.c;
    const cap = this.D.captions.find((k) => v >= k.v0 && v < k.v1 + 0.05);
    if (!cap) return;
    const t = v - cap.v0;
    const k = easeOutBack(t / 0.12);
    const onBoard = v >= this.D.hud.vBoard;
    const y = onBoard ? 1500 : 1330, x = 488;
    const size = 82;
    c.save(); c.translate(x, y); c.scale(k, k);
    c.font = `900 ${size}px ${F_CAPTION}`;
    const words = cap.words.map((w) => w.w.toUpperCase());
    const widths = words.map((w) => c.measureText(w).width);
    const space = size * 0.28;
    let total = widths.reduce((a, b) => a + b, 0) + space * (words.length - 1);
    const maxW = 820;
    const scale = total > maxW ? maxW / total : 1;
    c.scale(scale, scale);
    let xx = -total / 2;
    words.forEach((w, j) => {
      const wd = cap.words[j];
      const active = v >= wd.t - 0.02;
      const isName = /^[A-ZÀ-Ý'’-]{3,}/.test(w) && COUNTRIES.some((cc) => cc.name.toUpperCase().includes(w.replace(/[.,!?:]/g, '')));
      const fill = !active ? 'rgba(255,255,255,0.0)' : isName ? YELLOW : j === words.length - 1 && /[!]/.test(w) ? '#7CFF4F' : '#fff';
      if (active) stroked(c, w, xx + widths[j] / 2, 0, size, fill, F_CAPTION, 0.2);
      xx += widths[j] + space;
    });
    c.restore();
  }

  watermark(v) {
    const c = this.c;
    if (v < 2.4 || v >= this.D.hud.vBoard) return;
    c.save(); c.globalAlpha = 0.55;
    c.font = `600 22px ${F_CAPTION}`; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillStyle = '#fff';
    c.fillText(`ARÈNE DES NATIONS · ÉP. ${this.episode} · SIMULATION PHYSIQUE · SEED ${this.rec.seed}`, 40, 1535);
    c.restore();
  }
}
