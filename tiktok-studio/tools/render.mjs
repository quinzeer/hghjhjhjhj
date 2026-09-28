#!/usr/bin/env node
// Rendu hors-ligne : Chromium headless (WebGL SwiftShader) → images JPEG → ffmpeg (H.264 + audio).
// Usage :
//   node tools/render.mjs episodes/<ep> [--scale 1] [--q final|draft] [--workers 2]
//        [--from 0] [--to N] [--stills 0,30,60] [--no-video] [--fps-div 1]
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const ep = args[0];
if (!ep) { console.error('usage: node tools/render.mjs episodes/<ep> [options]'); process.exit(1); }
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const flag = (k) => args.includes('--' + k);
const epDir = path.resolve(ROOT, ep);
const tlPath = path.join(epDir, 'build', 'timeline.json');
const tl = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const scale = parseFloat(opt('scale', '1'));
const quality = opt('q', 'final');
const workers = parseInt(opt('workers', '2'), 10);
const total = Math.round(tl.duration * tl.fps);
const from = parseInt(opt('from', '0'), 10);
const to = Math.min(parseInt(opt('to', String(total)), 10), total);
const div = parseInt(opt('fps-div', '1'), 10);
const stills = opt('stills', null);
const framesDir = path.join(epDir, 'build', stills ? 'stills' : 'frames');
fs.mkdirSync(framesDir, { recursive: true });

const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.ttf': 'font/ttf', '.hdr': 'application/octet-stream', '.gltf': 'model/gltf+json', '.bin': 'application/octet-stream', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const p = path.join(ROOT, u === '/' ? '/src/index.html' : u);
  if (!p.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  fs.stat(p, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size });
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(p).pipe(res);
  });
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const rel = path.relative(ROOT, tlPath).split(path.sep).join('/');
const url = `http://127.0.0.1:${port}/src/index.html?timeline=/${rel}&scale=${scale}&q=${quality}&rs=${opt('rs', '1')}`;

let list;
if (stills) list = stills.split(',').map((x) => parseInt(x, 10));
else { list = []; for (let i = from; i < to; i += div) list.push(i); }

async function worker(idx, frames) {
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--use-gl=angle', '--disable-gpu-driver-bug-workarounds'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) console.log(`[w${idx}] ${m.type()}: ${m.text().slice(0, 300)}`); });
  page.on('pageerror', (e) => console.log(`[w${idx}] pageerror: ${e.message}`));
  await page.goto(url);
  await page.waitForFunction('window.ready === true || window.bootError', null, { timeout: 300000 });
  const err = await page.evaluate(() => window.bootError);
  if (err) { console.error(err); process.exit(2); }
  let n = 0; const t0 = Date.now();
  for (const f of frames) {
    const b64 = await page.evaluate(async (i) => { window.renderFrame(i); return await window.grabFrame(0.95); }, f);
    fs.writeFileSync(path.join(framesDir, `f_${String(f).padStart(5, '0')}.jpg`), Buffer.from(b64, 'base64'));
    n++;
    if (n % 20 === 0 || n === frames.length) {
      const el = (Date.now() - t0) / 1000;
      console.log(`[w${idx}] ${n}/${frames.length} images · ${(el / n).toFixed(2)} s/image · reste ~${Math.round((frames.length - n) * el / n / 60)} min`);
    }
  }
  await browser.close();
}

const W = flag('encode-only') ? 0 : Math.max(1, Math.min(workers, list.length));
const chunk = Math.ceil(list.length / W);
const t0 = Date.now();
if (W > 0) await Promise.all(Array.from({ length: W }, (_, i) => worker(i, list.slice(i * chunk, (i + 1) * chunk))));
server.close();
console.log(`rendu terminé : ${list.length} images en ${((Date.now() - t0) / 60000).toFixed(1)} min`);

if (!stills && !flag('no-video')) {
  const outDir = path.join(epDir, 'out'); fs.mkdirSync(outDir, { recursive: true });
  const mix = path.join(epDir, 'build', 'mix.wav');
  const isPreview = quality === 'draft' || scale < 1 || div > 1;
  const outFile = path.join(outDir, opt('out', isPreview ? 'preview.mp4' : 'final.mp4'));
  const fps = tl.fps / div;
  // Liste explicite des images de CE rendu (robuste aux trous de numérotation).
  const listFile = path.join(framesDir, `list_${isPreview ? 'preview' : 'final'}.txt`);
  const dur = (1 / fps).toFixed(6);
  fs.writeFileSync(listFile, list.map((f) => `file 'f_${String(f).padStart(5, '0')}.jpg'\nduration ${dur}`).join('\n') + `\nfile 'f_${String(list[list.length - 1]).padStart(5, '0')}.jpg'\n`);
  const W2 = Math.round(tl.width * scale / 2) * 2, H2 = Math.round(tl.height * scale / 2) * 2;
  const a = ['-y', '-f', 'concat', '-safe', '0', '-i', listFile];
  if (fs.existsSync(mix)) a.push('-ss', String(list[0] / tl.fps), '-i', mix);
  a.push('-map', '0:v');
  if (fs.existsSync(mix)) a.push('-map', '1:a');
  a.push('-vf', `scale=${W2}:${H2}:flags=lanczos,fps=${fps}`, '-c:v', 'libx264', '-preset', isPreview ? 'veryfast' : 'slow',
    '-crf', isPreview ? '23' : opt('crf', '17'), '-maxrate', isPreview ? '4M' : opt('maxrate', '16M'), '-bufsize', isPreview ? '8M' : '32M',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2', '-r', String(fps), '-movflags', '+faststart');
  if (fs.existsSync(mix)) a.push('-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest');
  a.push(outFile);
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', ...a], { stdio: 'inherit' });
  if (r.status === 0) console.log('vidéo :', outFile);
}
