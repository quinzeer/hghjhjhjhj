// Assemblage navigateur : story.json + voix → timeline → scène 3D (scene.js du projet) → habillage → image.
import { createKit } from './kit.js';
import { buildTimeline, autoEvents } from './timeline.js';
import { Overlay } from './overlay.js';

const json = async (u) => { const r = await fetch(u); if (!r.ok) throw new Error(`${u} : ${r.status}`); return r.json(); };

export async function setup({ project = '/project', glCanvas, outCanvas, quality = 'high', renderScale = 0.75 }) {
  const story = await json(`${project}/story.json`);
  let manifest = null;
  try { manifest = await json(`${project}/voices/manifest.json`); } catch { manifest = null; }
  const T = buildTimeline(story, manifest);
  if (document.fonts) await Promise.all(['400 100px Anton', '900 80px Montserrat', '700 30px Montserrat'].map((f) => document.fonts.load(f).catch(() => {})));
  const mod = await import(`${project}/scene.js`);
  const W = Math.round(1080 * renderScale), H = Math.round(1920 * renderScale);
  const K = createKit(glCanvas, { width: W, height: H, look: story.look || 'studio', quality });
  K.story = story; K.T = T;
  const state = (await mod.build(K, T, story)) || {};
  outCanvas.width = 1080; outCanvas.height = 1920;
  const overlay = new Overlay(outCanvas, T, story);
  const ctx = outCanvas.getContext('2d');
  const events = autoEvents(T).concat(mod.sfx ? mod.sfx(T, story, state) : []);
  const frame = (v) => {
    if (mod.update) mod.update(K, v, T, state);
    const cam = mod.camera(K, v, T, state);
    K.render(v, cam);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(glCanvas, 0, 0, 1080, 1920);
    overlay.draw(v, mod.overlay ? (o) => mod.overlay(o, v, T, state, K) : null);
  };
  return { story, T, K, state, frame, events, manifest };
}
