// Rendu complet d'un épisode → MP4 prêt pour TikTok (1080×1920, 30 i/s, H.264 ≤ 9 Mb/s + AAC, −14 LUFS, crête −1,5 dBTP).
// Images : Chromium headless (WebGL via GPU ou SwiftShader), rendu image par image, déterministe.
// Usage : node tools/render.mjs episodes/ep01 [--workers 2] [--scale 1] [--fps 30] [--q high|draft] [--from 0] [--to N]
//         node tools/render.mjs episodes/ep01 --audio-only   (remixe l'audio et remultiplexe sans re-rendre les images)
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync, execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { simulate } from '../src/sim.js';
import { buildDirector } from '../src/director.js';
import { encodeWav } from '../src/audio.js';
import { ffmpegPath, buildAudio, loadEpisode } from './mix.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const epDir = args[0];
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const AUDIO_ONLY = args.includes('--audio-only');
const WORKERS = +opt('workers', 2), SCALE = +opt('scale', 1), FPS = +opt('fps', 30), Q = opt('q', 'high');
const FF = ffmpegPath();
const epName = path.basename(epDir);
const tmp = path.join(epDir, 'tmp'); fs.mkdirSync(tmp, { recursive: true });
const outDir = path.join(epDir, 'out'); fs.mkdirSync(outDir, { recursive: true });
const log = (...a) => { const s = `[${new Date().toISOString().slice(11, 19)}] ${a.join(' ')}`; console.log(s); fs.appendFileSync(path.join(tmp, 'render.log'), s + '\n'); };

const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.mp3': 'audio/mpeg', '.css': 'text/css', '.woff2': 'font/woff2' };
async function openPage() {
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-background-timer-throttling'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  page.on('pageerror', (e) => log('pageerror', e.message));
  await page.route('**/*', async (route) => {
    const url = route.request().url();
    let file = null;
    if (url.startsWith('http://local/')) file = path.join(ROOT, decodeURIComponent(url.slice(13).split('?')[0]));
    else if (url.includes('cdn.jsdelivr.net/npm/three@0.170.0/')) file = path.join(ROOT, 'node_modules/three', url.split('three@0.170.0/')[1]);
    if (file) {
      if (!fs.existsSync(file)) return route.fulfill({ status: 404, body: 'introuvable' });
      return route.fulfill({ status: 200, body: fs.readFileSync(file), headers: { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' } });
    }
    return route.continue();
  });
  await page.goto(`http://local/render.html?ep=${encodeURI(epDir)}&scale=${SCALE}&q=${Q}&fps=${FPS}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 600000 });
  return { browser, page };
}

async function renderChunk(w, a, b) {
  const seg = path.join(tmp, `seg_${String(w).padStart(2, '0')}.mp4`);
  if (fs.existsSync(seg + '.done')) { log(`segment ${w} déjà rendu`); return seg; }
  const { browser, page } = await openPage();
  const ff = spawn(FF, ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M', '-tune', 'film', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
    '-r', String(FPS), '-g', String(FPS * 2), '-bf', '2', '-movflags', '+faststart', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = a; i < b; i++) {
    const url = await page.evaluate((i) => window.__frame(i, 'image/jpeg', 0.95), i);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    const done = i - a + 1;
    if (done % 25 === 0 || i === b - 1) {
      const el = (Date.now() - t0) / 1000;
      fs.writeFileSync(path.join(tmp, `progress_${w}.json`), JSON.stringify({ w, a, b, done, total: b - a, perFrame: el / done }));
    }
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error(`ffmpeg ${c}`)))));
  await browser.close();
  fs.writeFileSync(seg + '.done', 'ok');
  log(`segment ${w} terminé (${b - a} images, ${((Date.now() - t0) / 1000 / (b - a)).toFixed(2)} s/image)`);
  return seg;
}

function normalize(inWav, outWav) {
  // passe 1 : mesure (le JSON sort sur stderr)
  const r = spawnSyncStderr([FF, '-hide_banner', '-nostats', '-i', inWav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-']);
  const js = JSON.parse(r.slice(r.lastIndexOf('{'), r.lastIndexOf('}') + 1));
  const f = `loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=${js.input_i}:measured_TP=${js.input_tp}:measured_LRA=${js.input_lra}:measured_thresh=${js.input_thresh}:offset=${js.target_offset}:linear=true`;
  execFileSync(FF, ['-y', '-v', 'error', '-i', inWav, '-af', f, '-ar', '48000', outWav]);
  return js;
}
function spawnSyncStderr(cmd) {
  return spawnSync(cmd[0], cmd.slice(1), { encoding: 'utf8', maxBuffer: 1 << 26 }).stderr || '';
}

(async () => {
  const { ep, man } = loadEpisode(epDir);
  const D = buildDirector(simulate(ep.seed), man);
  const total = Math.floor(D.duration * FPS);
  const from = +opt('from', 0), to = Math.min(+opt('to', total), total);
  log(`épisode ${epName} · seed ${ep.seed} · ${D.duration.toFixed(2)} s · images ${from}→${to} · ${WORKERS} rendus parallèles · échelle ${SCALE}`);
  fs.writeFileSync(path.join(epDir, `${epName}.scenes.json`), JSON.stringify(sceneJson(ep, D), null, 2));

  // 1) audio (Node) : avec et sans musique, normalisés à −14 LUFS
  const wav = path.join(tmp, 'mix.wav'), wavN = path.join(tmp, 'mix_nomusic.wav');
  if (AUDIO_ONLY || !fs.existsSync(wav)) fs.writeFileSync(wav, encodeWav(buildAudio(epDir, D, man, true)));
  if (AUDIO_ONLY || !fs.existsSync(wavN)) fs.writeFileSync(wavN, encodeWav(buildAudio(epDir, D, man, false)));
  const L1 = normalize(wav, path.join(tmp, 'mix_norm.wav'));
  normalize(wavN, path.join(tmp, 'mix_nomusic_norm.wav'));
  log(`audio : ${L1.input_i} LUFS → −14 LUFS`);

  // 2) images en parallèle, un segment par processus
  const chunks = [];
  const n = to - from, per = Math.ceil(n / WORKERS);
  for (let w = 0; w < WORKERS; w++) { const a = from + w * per, b = Math.min(to, a + per); if (b > a) chunks.push([w, a, b]); }
  const segs = AUDIO_ONLY
    ? fs.readdirSync(tmp).filter((f) => /^seg_\d+\.mp4$/.test(f)).sort().map((f) => path.join(tmp, f))
    : await Promise.all(chunks.map(([w, a, b]) => renderChunk(w, a, b)));

  // 3) concaténation + multiplexage
  const list = path.join(tmp, 'list.txt');
  fs.writeFileSync(list, segs.map((s) => `file '${path.resolve(s)}'`).join('\n'));
  const video = path.join(tmp, 'video.mp4');
  execFileSync(FF, ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', video]);
  const tag = from === 0 && to === total ? '' : `_${from}-${to}`;
  const mux = (audio, name) => {
    const out = path.join(outDir, name);
    const ss = (from / FPS).toFixed(3);
    execFileSync(FF, ['-y', '-v', 'error', '-i', video, '-ss', ss, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out]);
    return out;
  };
  const o1 = mux(path.join(tmp, 'mix_norm.wav'), `arene-${epName}${tag}.mp4`);
  const o2 = mux(path.join(tmp, 'mix_nomusic_norm.wav'), `arene-${epName}${tag}_sans-musique.mp4`);
  // 4) couvertures candidates (TikTok laisse choisir l'image de couverture)
  for (const [nm, v] of [['cover_hook', 0.9], ['cover_vs', D.hud.vFin + 0.8], ['cover_victoire', D.hud.vCel0 + 1.2]]) {
    const t = v - from / FPS;
    if (t >= 0 && t < (to - from) / FPS) execFileSync(FF, ['-y', '-v', 'error', '-ss', t.toFixed(2), '-i', o1, '-frames:v', '1', '-q:v', '2', path.join(outDir, `${nm}.jpg`)]);
  }
  log(`terminé : ${o1} · ${o2}`);
})().catch((e) => { log('ERREUR', e.stack || e); process.exit(1); });

function sceneJson(ep, D) {
  return {
    version: '1.0', format: 'short', plateforme: 'tiktok', langue: 'fr', duree_totale_s: +D.duration.toFixed(2),
    promesse: 'Tu vas voir lequel des 32 pays survit seul sur la plateforme.',
    titres: ['32 pays, 1 seul survivant', 'Ton pays tient combien de temps ?', 'Le dernier pays debout gagne'],
    titre_en: '32 countries, only 1 survives',
    premiere_image: 'Pluie de 32 billes-drapeaux sur un plateau de jeu télé, titre « 32 PAYS · 1 SEUL SURVIVANT »',
    video_suivante: 'Épisode 2 : revanche avec un nouveau seed',
    divulgation_ia: { requise: true, raison: 'voix off synthétique réaliste (TTS neuronal) ; images de synthèse 3D' },
    controle: { publiable: true, raisons_blocage: [], faits_a_verifier: [], seed: ep.seed },
    scenes: D.scenes,
  };
}
