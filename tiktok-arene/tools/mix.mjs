// Mixage audio d'un épisode dans Node (voix + foule décodées par ffmpeg) → WAV.
// Usage : node tools/mix.mjs episodes/ep01 [--no-music] [sortie.wav]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { simulate } from '../src/sim.js';
import { buildDirector } from '../src/director.js';
import { mixEpisode, encodeWav, SR } from '../src/audio.js';

export function ffmpegPath() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  try { return execFileSync('python3', ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim(); } catch { return 'ffmpeg'; }
}
export function decodeMono(file, ff = ffmpegPath()) {
  const raw = execFileSync(ff, ['-v', 'error', '-i', file, '-f', 'f32le', '-ac', '1', '-ar', String(SR), '-'], { maxBuffer: 1 << 28 });
  return new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4).slice();
}
export function loadEpisode(dir) {
  const ep = JSON.parse(fs.readFileSync(path.join(dir, 'episode.json')));
  const man = JSON.parse(fs.readFileSync(path.join(dir, 'voices/manifest.json')));
  return { ep, man };
}
export function buildAudio(dir, D, man, music = true) {
  const ff = ffmpegPath();
  const voices = {};
  for (const [id, m] of Object.entries(man.lines)) voices[id] = decodeMono(path.join(dir, 'voices', m.file), ff);
  const cdir = path.join(path.dirname(path.dirname(path.resolve(dir))), 'assets/crowd');
  const cman = JSON.parse(fs.readFileSync(path.join(cdir, 'manifest.json')));
  const crowd = {};
  for (const [id, m] of Object.entries(cman.lines)) crowd[id] = decodeMono(path.join(cdir, m.file), ff);
  return mixEpisode(D, { voices, crowd }, { music });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const dir = process.argv[2];
  const music = !process.argv.includes('--no-music');
  const out = process.argv.find((a) => a.endsWith('.wav')) || path.join(dir, music ? 'mix.wav' : 'mix_nomusic.wav');
  const { ep, man } = loadEpisode(dir);
  const t0 = Date.now();
  const D = buildDirector(simulate(ep.seed), man);
  const ch = buildAudio(dir, D, man, music);
  fs.writeFileSync(out, encodeWav(ch));
  let pk = 0, rms = 0; for (const c of ch) for (const x of c) { pk = Math.max(pk, Math.abs(x)); rms += x * x; }
  console.log(`${out} : ${D.duration.toFixed(2)} s, crête ${(20 * Math.log10(pk)).toFixed(1)} dBFS, RMS ${(10 * Math.log10(rms / (ch[0].length * 2))).toFixed(1)} dBFS, ${(Date.now() - t0) / 1000}s`);
}
