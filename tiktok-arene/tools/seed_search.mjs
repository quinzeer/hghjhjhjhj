// Cherche les seeds les plus dramatiques (rythme, finale serrée, remontée du vainqueur).
// Le critère porte sur la dramaturgie, jamais sur l'identité du vainqueur.
// Usage : node tools/seed_search.mjs [debut] [fin]   → JSON trié sur la sortie standard
import { simulate } from '../src/sim.js';

export function dramaScore(rec) {
  const s = rec.stats, et = rec.elims.map((e) => e.t);
  if (!Number.isFinite(s.duration) || rec.elims.length < 31) return { score: -999 };
  const first = et[0];
  let burst = 0; // pire rafale : éliminations dans une fenêtre d'1 s
  for (let i = 0; i < et.length; i++) { let n = 0; for (let j = i; j < et.length && et[j] - et[i] < 1; j++) n++; burst = Math.max(burst, n); }
  let score = 100;
  score -= Math.max(0, first - 4.6) * 14;                       // le hook doit payer vite
  score -= Math.abs(s.duration - 46) * 1.6;                      // ~46 s de jeu → ~60 s de vidéo
  score -= Math.max(0, s.maxGap - 3.5) * 9;                      // pas de temps mort
  score -= Math.max(0, 5.5 - s.finalDuel) * 8 + Math.max(0, s.finalDuel - 9) * 5;
  score -= Math.max(0, burst - 4) * 7;                           // rafales lisibles
  score += Math.min(s.winnerNearMiss, 3) * 4;                    // le vainqueur a frôlé la chute
  score += s.winnerMinEdge < 0.12 ? 6 : 0;
  score += Math.min(s.armKills, 6) * 1.2;                        // éjections spectaculaires
  score += Math.min(s.combos, 10) * 0.6;
  return { score: +score.toFixed(2), first: +first.toFixed(2), burst };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const a = +process.argv[2] || 1, b = +process.argv[3] || 50;
  const out = [];
  for (let seed = a; seed <= b; seed++) {
    const rec = simulate(seed);
    const d = dramaScore(rec);
    out.push({ seed, ...d, winner: rec.winner, duration: +rec.stats.duration.toFixed(1), duel: +rec.stats.finalDuel.toFixed(1), maxGap: +rec.stats.maxGap.toFixed(1), nearMiss: rec.stats.winnerNearMiss, armKills: rec.stats.armKills, combos: rec.stats.combos });
  }
  out.sort((x, y) => y.score - x.score);
  console.log(JSON.stringify(out));
}
