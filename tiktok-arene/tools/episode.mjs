// Prépare un épisode : simulation + montage « brouillon » → liste des répliques à synthétiser.
// Usage : node tools/episode.mjs <seed> <dossier>   ex. node tools/episode.mjs 370 episodes/ep01
import fs from 'node:fs';
import path from 'node:path';
import { simulate } from '../src/sim.js';
import { buildDirector, CROWD_VOICES, CROWD_LINES } from '../src/director.js';
import { COUNTRIES } from '../src/countries.js';

const seed = +process.argv[2];
const dir = process.argv[3];
if (!seed || !dir) { console.error('usage: node tools/episode.mjs <seed> <dossier>'); process.exit(1); }
fs.mkdirSync(path.join(dir, 'voices'), { recursive: true });

const rec = simulate(seed);
const D = buildDirector(rec, null);
const ep = {
  seed,
  episode: path.basename(dir),
  winner: COUNTRIES[rec.winner].name,
  ranking: [...rec.elims].sort((a, b) => a.rank - b.rank).map((e) => ({ rank: e.rank, country: COUNTRIES[e.i].name })).concat([{ rank: 1, country: COUNTRIES[rec.winner].name }]).sort((a, b) => a.rank - b.rank),
  estimatedDuration: +D.duration.toFixed(2),
  lines: D.candidates.map((c) => ({ id: c.id, text: c.text, voice: c.voice, rate: c.rate, pitch: c.pitch })),
  crowd: { voices: CROWD_VOICES, lines: CROWD_LINES },
};
fs.writeFileSync(path.join(dir, 'episode.json'), JSON.stringify(ep, null, 2));
console.log(`seed ${seed} → vainqueur ${ep.winner}, ~${ep.estimatedDuration}s, ${ep.lines.length} répliques`);
