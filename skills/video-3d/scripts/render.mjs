// Rendu d'un projet vidéo 3D → MP4 vertical prêt pour TikTok/Shorts/Reels.
//   node render.mjs <projet> --preview 8        planche contact de 8 images (contrôle visuel rapide, ~1 min)
//   node render.mjs <projet> --at 0.5,3,12      images précises (secondes)
//   node render.mjs <projet>                    vidéo complète : out/video.mp4 (≤ 9 Mb/s) + out/video_light.mp4 (< 30 Mio)
// Options : --workers 2  --rs 0.75 (échelle du rendu 3D)  --q high|draft  --fps 30  --music tension|epic|chill|playful|mystery|none
//           --audio-only (remixe le son sans refaire les images)  --no-light
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { buildTimeline } from './engine/timeline.js';
import { mixVideo, encodeWav, SR } from './engine/audio.js';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const args = process.argv.slice(2);
const PROJ = path.resolve(args[0] || '.');
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const flag = (k) => args.includes(`--${k}`);
const FPS = +opt('fps', 30), RS = +opt('rs', 0.75), Q = opt('q', 'high'), WORKERS = +opt('workers', 2);
const tmp = path.join(PROJ, 'tmp'), out = path.join(PROJ, 'out');
fs.mkdirSync(tmp, { recursive: true }); fs.mkdirSync(out, { recursive: true });
const log = (...a) => { const s = `[${new Date().toISOString().slice(11, 19)}] ${a.join(' ')}`; console.log(s); fs.appendFileSync(path.join(tmp, 'render.log'), s + '\n'); };

// --- dépendances : Playwright, three (local si possible), ffmpeg ---
function findModule(name) {
  // remonte l'arborescence depuis le projet, le skill et le dossier courant (certains paquets n'exportent pas package.json)
  for (const base of [PROJ, HERE, process.cwd()]) {
    let d = base;
    while (true) { const f = path.join(d, 'node_modules', name, 'package.json'); if (fs.existsSync(f)) return f; const up = path.dirname(d); if (up === d) break; d = up; }
  }
  try { return createRequire(path.join(HERE, 'x.js')).resolve(`${name}/package.json`); } catch { return null; }
}
const pwPkg = findModule('playwright');
if (!pwPkg) { console.error('Playwright introuvable : lancer scripts/setup.sh (npm install three@0.170.0 playwright)'); process.exit(1); }
const { chromium } = await import(path.join(path.dirname(pwPkg), 'index.mjs'));
const threePkg = findModule('three');
const THREE_DIR = threePkg ? path.dirname(threePkg) : null;
function ffmpeg() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  try { return execFileSync('python3', ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim(); } catch { return 'ffmpeg'; }
}
const FF = ffmpeg();

const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.mp3': 'audio/mpeg', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.hdr': 'application/octet-stream', '.bin': 'application/octet-stream', '.ktx2': 'application/octet-stream' };
async function openPage() {
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-background-timer-throttling'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  page.on('pageerror', (e) => log('erreur page :', e.message));
  page.on('console', (m) => { if (m.type() === 'error') log('console :', m.text().slice(0, 300)); });
  await page.route('**/*', async (route) => {
    const url = route.request().url();
    let file = null;
    if (url.startsWith('http://local/')) {
      const p = decodeURIComponent(url.slice(13).split('?')[0]);
      if (p.startsWith('project/')) file = path.join(PROJ, p.slice(8));
      else if (p.startsWith('engine/') || p.startsWith('fonts/') || p === 'render.html') file = path.join(HERE, p);
    } else if (THREE_DIR && url.includes('cdn.jsdelivr.net/npm/three@0.170.0/')) file = path.join(THREE_DIR, url.split('three@0.170.0/')[1]);
    if (file) {
      if (!fs.existsSync(file)) return route.fulfill({ status: 404, body: 'introuvable' });
      return route.fulfill({ status: 200, body: fs.readFileSync(file), headers: { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' } });
    }
    return route.continue();
  });
  await page.goto(`http://local/render.html?q=${Q}&rs=${RS}&fps=${FPS}`);
  try { await page.waitForFunction(() => window.__ready === true || window.__error, null, { timeout: 180000 }); }
  catch { await browser.close(); throw new Error("la page de rendu ne s'est pas initialisée en 3 min (voir les erreurs « console » ci-dessus : module introuvable, erreur de syntaxe dans scene.js, three non chargé…)"); }
  const err = await page.evaluate(() => window.__error);
  if (err) { await browser.close(); throw new Error(`la scène n'a pas pu être construite :\n${err}`); }
  return { browser, page };
}

function decodeMono(file) {
  const raw = execFileSync(FF, ['-v', 'error', '-i', file, '-f', 'f32le', '-ac', '1', '-ar', String(SR), '-'], { maxBuffer: 1 << 28 });
  return new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4).slice();
}
function normalize(inWav, outWav) {
  const r = spawnSync(FF, ['-hide_banner', '-nostats', '-i', inWav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const js = JSON.parse(r.slice(r.lastIndexOf('{'), r.lastIndexOf('}') + 1));
  execFileSync(FF, ['-y', '-v', 'error', '-i', inWav, '-af', `loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=${js.input_i}:measured_TP=${js.input_tp}:measured_LRA=${js.input_lra}:measured_thresh=${js.input_thresh}:offset=${js.target_offset}:linear=true`, '-ar', '48000', outWav]);
  return js;
}

async function stills(times, name) {
  const { browser, page } = await openPage();
  const meta = await page.evaluate(() => window.__meta);
  const files = [];
  for (let k = 0; k < times.length; k++) {
    const i = Math.min(meta.frames - 1, Math.round(times[k] * FPS));
    const url = await page.evaluate((i) => window.__frame(i, 0.9), i);
    const f = path.join(out, `still_${String(k).padStart(2, '0')}.jpg`);
    fs.writeFileSync(f, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
    files.push(f);
  }
  await browser.close();
  const cols = Math.min(6, files.length), rows = Math.ceil(files.length / cols);
  const sheet = path.join(out, name);
  execFileSync(FF, ['-y', '-v', 'error', '-framerate', '1', '-i', path.join(out, 'still_%02d.jpg'), '-vf', `scale=270:480,tile=${cols}x${rows}:padding=6:color=0x141414`, '-frames:v', '1', sheet]);
  log(`planche contact : ${sheet} (${times.map((t) => t.toFixed(1)).join(', ')} s) · durée ${meta.duration.toFixed(2)} s`);
  return meta;
}

async function renderChunk(w, a, b) {
  const seg = path.join(tmp, `seg_${String(w).padStart(2, '0')}.mp4`);
  if (fs.existsSync(seg + '.done')) return seg;
  const { browser, page } = await openPage();
  const ff = spawn(FF, ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M', '-tune', 'film', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2', '-r', String(FPS), '-g', String(FPS * 2), '-movflags', '+faststart', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = a; i < b; i++) {
    const url = await page.evaluate((i) => window.__frame(i), i);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
    if ((i - a + 1) % 30 === 0) fs.writeFileSync(path.join(tmp, `progress_${w}.json`), JSON.stringify({ w, done: i - a + 1, total: b - a, sPerFrame: (Date.now() - t0) / 1000 / (i - a + 1) }));
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error(`ffmpeg ${c}`)))));
  await browser.close();
  fs.writeFileSync(seg + '.done', 'ok');
  log(`segment ${w} : ${b - a} images, ${((Date.now() - t0) / 1000 / (b - a)).toFixed(2)} s/image`);
  return seg;
}

(async () => {
  const story = JSON.parse(fs.readFileSync(path.join(PROJ, 'story.json')));
  let manifest = null;
  try { manifest = JSON.parse(fs.readFileSync(path.join(PROJ, 'voices/manifest.json'))); } catch { log('⚠ pas de voix (voices/manifest.json) : lancer tts.py ; timings estimés'); }
  const T = buildTimeline(story, manifest);

  if (opt('preview') || opt('at')) {
    const times = opt('at') ? opt('at').split(',').map(Number) : Array.from({ length: +opt('preview') }, (_, k) => (T.duration * (k + 0.5)) / +opt('preview'));
    await stills(times, 'preview.jpg');
    return;
  }

  const total = Math.floor(T.duration * FPS);
  log(`projet ${path.basename(PROJ)} · ${T.duration.toFixed(2)} s · ${total} images · ${WORKERS} rendus parallèles`);
  // images
  let segs;
  if (flag('audio-only')) segs = fs.readdirSync(tmp).filter((f) => /^seg_\d+\.mp4$/.test(f)).sort().map((f) => path.join(tmp, f));
  else {
    const per = Math.ceil(total / WORKERS), chunks = [];
    for (let w = 0; w < WORKERS; w++) { const a = w * per, b = Math.min(total, a + per); if (b > a) chunks.push([w, a, b]); }
    segs = await Promise.all(chunks.map(([w, a, b]) => renderChunk(w, a, b)));
  }
  // événements sonores de la scène (calculés dans la page)
  const { browser, page } = await openPage();
  const meta = await page.evaluate(() => window.__meta);
  await browser.close();
  // audio
  const voices = {};
  if (manifest) for (const [id, m] of Object.entries(manifest.lines)) voices[id] = decodeMono(path.join(PROJ, 'voices', m.file));
  const music = opt('music', story.music || 'tension');
  const wav = path.join(tmp, 'mix.wav');
  fs.writeFileSync(wav, encodeWav(mixVideo(T, meta.events, voices, { music })));
  const L = normalize(wav, path.join(tmp, 'mix_norm.wav'));
  // assemblage
  fs.writeFileSync(path.join(tmp, 'list.txt'), segs.map((s) => `file '${path.resolve(s)}'`).join('\n'));
  execFileSync(FF, ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'), '-c', 'copy', path.join(tmp, 'video.mp4')]);
  const master = path.join(out, 'video.mp4');
  execFileSync(FF, ['-y', '-v', 'error', '-i', path.join(tmp, 'video.mp4'), '-i', path.join(tmp, 'mix_norm.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', master]);
  // version légère < 30 Mio (envoi par messagerie / outils limités), encodage 2 passes
  if (!flag('no-light')) {
    const kbps = Math.max(1500, Math.floor((28 * 8 * 1024 * 1024) / T.duration / 1000) - 180);
    for (const pass of [1, 2]) execFileSync(FF, ['-y', '-v', 'error', '-i', path.join(tmp, 'video.mp4'), '-c:v', 'libx264', '-preset', 'slow', '-tune', 'film', '-b:v', `${kbps}k`, '-maxrate', `${Math.round(kbps * 1.5)}k`, '-bufsize', `${kbps * 2}k`, '-pix_fmt', 'yuv420p', '-pass', String(pass), '-passlogfile', path.join(tmp, 'x264'), '-an', '-f', 'mp4', pass === 1 ? '/dev/null' : path.join(tmp, 'light.mp4')]);
    execFileSync(FF, ['-y', '-v', 'error', '-i', path.join(tmp, 'light.mp4'), '-i', path.join(tmp, 'mix_norm.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', path.join(out, 'video_light.mp4')]);
  }
  // couverture + contrôle
  execFileSync(FF, ['-y', '-v', 'error', '-ss', String(Math.min(1, T.duration / 2)), '-i', master, '-frames:v', '1', '-q:v', '2', path.join(out, 'cover.jpg')]);
  const eb = spawnSync(FF, ['-hide_banner', '-nostats', '-i', master, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const I = (eb.match(/I:\s+(-?[\d.]+) LUFS/g) || []).pop(), TP = (eb.match(/Peak:\s+(-?[\d.]+) dBFS/g) || []).pop();
  log(`terminé : ${master} · ${(fs.statSync(master).size / 1048576).toFixed(1)} Mio · son ${L.input_i} → ${I} · crête ${TP}`);
})().catch((e) => { log('ERREUR', e.stack || e); process.exit(1); });
