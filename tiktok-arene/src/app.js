// Assemblage navigateur : simulation → montage → rendu 3D → habillage → audio.
// Deux modes : studio (aperçu interactif, enregistrement temps réel) et rendu (image par image, piloté par Playwright).
import { simulate } from './sim.js';
import { buildDirector } from './director.js';
import { Arena } from './scene.js';
import { Hud } from './hud.js';
import { mixEpisode, SR } from './audio.js';
import { COUNTRIES } from './countries.js';

export async function loadJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(url); return r.json(); }

export async function loadFonts() {
  if (!document.fonts) return;
  await Promise.all(['400 100px Anton', '900 80px Montserrat', '700 20px Montserrat', '600 20px Montserrat'].map((f) => document.fonts.load(f).catch(() => {})));
}

// renderScale : la 3D est rendue plus petite puis agrandie (grain + profondeur de champ masquent la différence),
// l'habillage reste dessiné à pleine résolution.
export async function setup({ seed, epDir, glCanvas, outCanvas, quality = 'high', width = 1080, height = 1920, episode = 1, renderScale = 0.75 }) {
  let manifest = null;
  if (epDir) { try { manifest = await loadJSON(`${epDir}/voices/manifest.json`); } catch { manifest = null; } }
  const rec = simulate(seed);
  const D = buildDirector(rec, manifest);
  await loadFonts();
  const arena = new Arena(glCanvas, D, { width: Math.round(width * renderScale), height: Math.round(height * renderScale), projW: 1080, projH: 1920, quality });
  outCanvas.width = width; outCanvas.height = height;
  const hud = new Hud(outCanvas, D, arena, { episode });
  const ctx = outCanvas.getContext('2d');
  const sx = width / 1080;
  const frame = (v) => {
    arena.renderAt(v);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(glCanvas, 0, 0, width, height);
    ctx.setTransform(sx, 0, 0, sx, 0, 0);
    hud.draw(v);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  };
  return { rec, D, arena, hud, frame, manifest };
}

// Décodage des voix et de la foule puis mixage complet (même code que le rendu Node)
export async function buildMix(D, epDir, crowdDir, { music = true, onProgress } = {}) {
  const ac = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 1, SR);
  const dec = async (url) => { const b = await (await fetch(url)).arrayBuffer(); const a = await ac.decodeAudioData(b); return a.getChannelData(0).slice(); };
  const voices = {};
  if (epDir) for (const L of D.lines) if (L.file) { try { voices[L.id] = await dec(`${epDir}/voices/${L.file}`); } catch {} }
  onProgress && onProgress('voix décodées');
  let crowd = null;
  try {
    const cm = await loadJSON(`${crowdDir}/manifest.json`);
    crowd = {};
    await Promise.all(Object.entries(cm.lines).map(async ([id, m]) => { crowd[id] = await dec(`${crowdDir}/${m.file}`); }));
  } catch { crowd = null; }
  onProgress && onProgress('mixage…');
  await new Promise((r) => setTimeout(r, 30));
  return mixEpisode(D, { voices, crowd }, { music });
}

export function countryList() { return COUNTRIES; }
