// Point d'entrée du moteur (navigateur headless). Expose window.renderFrame(i) et window.grabFrame().
import * as THREE from 'three';
import { createRenderer } from './engine/renderer.js';
import { Overlay } from './engine/overlay.js';
import { Assets } from './engine/assets.js';
import { makeCameraPath, applyCamera, transitionOffsets, projectUV } from './engine/camera.js';
import { hashStr, clamp, impulse } from './engine/util.js';
import { SETS } from './sets/index.js';

const qs = new URLSearchParams(location.search);
const TL_URL = qs.get('timeline');
const SCALE = parseFloat(qs.get('scale') || '1');
const QUALITY = qs.get('q') || 'final';
const RS = parseFloat(qs.get('rs') || '1'); // échelle du rendu 3D interne (l'habillage reste en pleine définition)
// full : 3D + habillage ; plate : 3D seule (passe lente) ; overlay : habillage sur plaques déjà rendues (passe rapide)
const MODE = qs.get('mode') || 'full';
const PLATES = qs.get('plates') || '';
const pad5 = (i) => String(i).padStart(5, '0');

async function boot() {
  const tl = await (await fetch(TL_URL)).json();
  const W = Math.round(tl.width * SCALE / 2) * 2, H = Math.round(tl.height * SCALE / 2) * 2;
  const out = document.createElement('canvas'); out.width = W; out.height = H;
  document.body.appendChild(out);
  const octx = out.getContext('2d');
  window.grabFrame = async (q = 0.95) => {
    const blob = await new Promise((r) => out.toBlob(r, 'image/jpeg', q));
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  window.TL = { frames: Math.round(tl.duration * tl.fps), fps: tl.fps, W, H };

  if (MODE === 'overlay') {
    // Passe rapide : aucune 3D, on pose l'habillage sur les plaques rendues.
    const assets = new Assets(null, '/');
    await assets.loadFonts();
    const overlay = new Overlay(tl, W, H, assets);
    await overlay.preload();
    window.renderFrame = async (i) => {
      const img = new Image();
      img.src = `${PLATES}/f_${pad5(i)}.jpg`;
      await img.decode();
      octx.imageSmoothingQuality = 'high';
      octx.drawImage(img, 0, 0, W, H);
      overlay.draw(octx, i / tl.fps);
      return true;
    };
    window.ready = true;
    return;
  }

  const R = createRenderer(Math.round(W * RS / 2) * 2, Math.round(H * RS / 2) * 2, { quality: QUALITY });
  const assets = new Assets(R.renderer, '/');
  await assets.loadFonts();

  // Images optionnelles fournies par l'utilisateur (photos, captures) : chargées si présentes.
  const images = new Map();
  const wanted = new Set(tl.images || []);
  for (const p of wanted) { const img = await assets.optionalHTMLImage(p); if (img) images.set(p, img); }

  const ctx = { W, H, images, tl };
  const sets = {};
  for (const shot of tl.shots) {
    if (!sets[shot.set]) {
      const Set = SETS[shot.set];
      if (!Set) throw new Error('Décor inconnu : ' + shot.set);
      sets[shot.set] = new Set(ctx);
      await sets[shot.set].load(assets);
    }
  }
  const overlay = new Overlay(tl, W, H, assets);
  await overlay.preload();

  // Pré-compilation des shaders de chaque décor (évite les à-coups au premier plan).
  for (const s of Object.values(sets)) R.renderer.compile(s.scene, s.camera);

  const scratch = new THREE.PerspectiveCamera();
  const paths = new Map();
  const TW = 0.17; // demi-durée des transitions (s)

  function camState(shot, set, lt) {
    if (!paths.has(shot.id)) paths.set(shot.id, makeCameraPath(set.camSpec(shot), hashStr(shot.id) % 1000));
    const impacts = (tl.beats || []).filter((b) => b.shake && b.t >= shot.start - 0.05 && b.t < shot.end).map((b) => ({ t: b.t - shot.start, amp: b.shake }));
    const st = paths.get(shot.id)(lt, { impacts });
    const dur = shot.end - shot.start;
    let tr = {};
    if (shot.transOut && dur - lt < TW) tr = { ...tr, ...transitionOffsets(shot.transOut, -1, 1 - (dur - lt) / TW) };
    if (shot.transIn && lt < TW) tr = { ...tr, ...transitionOffsets(shot.transIn, +1, 1 - lt / TW) };
    return { st, tr };
  }

  window.renderFrame = (i) => {
    const t = i / tl.fps;
    let shot = tl.shots.find((s) => t >= s.start && t < s.end) || tl.shots[tl.shots.length - 1];
    const set = sets[shot.set];
    const lt = t - shot.start;
    set.update(shot, lt, t);
    const { st, tr } = camState(shot, set, lt);
    applyCamera(set.camera, st, tr);

    // Flou de mouvement : déplacement apparent du point de mise au point pendant l'obturation (180°).
    const focus = { ...set.focus(shot), ...(shot.dof || {}) };
    const shutter = 0.5 / tl.fps;
    const prev = camState(shot, set, Math.max(0, lt - shutter));
    scratch.copy(set.camera);
    applyCamera(scratch, prev.st, prev.tr);
    const a = projectUV(set.camera, focus.target), b = projectUV(scratch, focus.target);
    let dir = [a[0] - b[0], a[1] - b[1]];
    if (lt < shutter) dir = [0, 0];
    const zoom = (prev.st.fov * (prev.tr.zoom || 1)) / (st.fov * (tr.zoom || 1)) - 1;

    // Flashs et pics d'exposition synchronisés aux temps forts.
    let flash = 0, ca = 0.004;
    for (const bt of tl.beats || []) {
      if (bt.flash) flash = Math.max(flash, impulse(t, bt.t, 14, 0.35) * bt.flash);
      if (bt.shake) ca += impulse(t, bt.t, 10, 0.5) * 0.02 * bt.shake;
    }
    const fx = {
      dof: shot.noDof ? null : focus,
      motionBlur: { dir: [dir[0] * 1.0, dir[1] * 1.0], zoom: clamp(zoom * 1.2, -0.2, 0.2) },
      bloom: shot.bloom, tone: shot.tone,
      grade: { uFlash: flash, uCA: ca, ...(shot.grade || {}) },
    };
    // Ombres calculées une seule fois par image (réutilisées par le reflet et le rendu principal).
    R.renderer.shadowMap.autoUpdate = false;
    R.renderer.shadowMap.needsUpdate = true;
    if (set.beforeRender) set.beforeRender(R.renderer, t);
    R.render(set.scene, set.camera, fx, i);
    octx.imageSmoothingQuality = 'high';
    octx.drawImage(R.canvas, 0, 0, W, H);
    if (MODE !== 'plate') overlay.draw(octx, t);
    return true;
  };
  window.ready = true;
}

boot().catch((e) => { console.error('BOOT ERROR', e && e.stack || e); window.bootError = String(e && e.stack || e); });
