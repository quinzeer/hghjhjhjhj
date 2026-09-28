// Timeline pilotée par la voix : chaque beat dure le temps de sa réplique (+ marge), la vidéo se cale sur la narration.
// Pur JS (Node et navigateur). Toute l'animation d'une scène s'exprime en fonction du temps vidéo v et de ces beats.
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const estDur = (text) => 0.35 + text.split(/\s+/).length * 0.33;

export function buildTimeline(story, manifest = null) {
  const beats = [];
  let v = story.start ?? 0.1;
  story.beats.forEach((b, i) => {
    const m = manifest && manifest.lines && manifest.lines[b.id];
    const delay = b.delay ?? 0;
    const vd = b.say ? (m ? m.dur : estDur(b.say)) : 0;
    const dur = b.dur ?? Math.max(b.min ?? 1.0, delay + vd + (b.pad ?? 0.3));
    const words = b.say
      ? m ? m.words.map((w) => ({ w: w.w, t: v + delay + w.t, d: w.d }))
        : b.say.split(/\s+/).map((w, k, a) => ({ w, t: v + delay + (k * vd) / a.length, d: (vd / a.length) * 0.9 }))
      : [];
    const energy = b.energy ?? 0.5 + 0.4 * (i / Math.max(1, story.beats.length - 1));
    beats.push({ ...b, i, v0: v, v1: v + dur, dur, voiceV: v + delay, voiceDur: vd, words, energy, file: m ? m.file : null });
    v += dur;
  });
  const duration = v + (story.tail ?? 0.3);
  const byId = Object.fromEntries(beats.map((b) => [b.id, b]));
  const lines = beats.filter((b) => b.say).map((b) => ({ id: b.id, v: b.voiceV, dur: b.voiceDur, text: b.say, file: b.file }));

  // sous-titres : groupes de 1 à 3 mots, coupés à la ponctuation
  const captions = [];
  for (const b of beats) {
    let chunk = [];
    const flush = () => { if (chunk.length) captions.push({ v0: chunk[0].t, v1: chunk[chunk.length - 1].t + chunk[chunk.length - 1].d, words: chunk, beat: b.id }); chunk = []; };
    for (const w of b.words) { chunk.push(w); if (chunk.length >= 3 || chunk.map((x) => x.w).join(' ').length > 14 || /[.!?:,]$/.test(w.w)) flush(); }
    flush();
  }
  for (let i = 0; i < captions.length - 1; i++) captions[i].v1 = Math.min(captions[i].v1 + 0.25, captions[i + 1].v0);

  const T = {
    duration, beats, lines, captions,
    beat: (id) => byId[id],
    at: (id) => byId[id].v0,
    // progression locale 0→1 d'un beat (a, b : fenêtre en secondes depuis le début du beat, b négatif = depuis la fin)
    k: (id, v, a = 0, b = null) => { const B = byId[id]; const s = B.v0 + a, e = b === null ? B.v1 : b < 0 ? B.v1 + b : B.v0 + b; return clamp((v - s) / Math.max(1e-6, e - s), 0, 1); },
    beatAt: (v) => beats.find((b) => v >= b.v0 && v < b.v1) || beats[beats.length - 1],
    index: (v) => T.beatAt(v).i,
    energyAt: (v) => T.beatAt(v).energy,
    musicMutedAt: (v) => beats.some((b) => (b.music === 'off' && v >= b.v0 && v < b.v1) || (b.drop && v >= b.v0 - 0.45 && v < b.v0)),
  };
  return T;
}

// Événements sonores automatiques : coup d'ouverture, whoosh + pop sur chaque texte-choc, sfx déclarés dans les beats
export function autoEvents(T) {
  const ev = [{ v: 0.02, type: 'impact', gain: 0.5 }];
  for (const b of T.beats) {
    if (b.text) { const tv = b.v0 + (b.textAt ?? 0); ev.push({ v: tv - 0.04, type: 'whoosh', gain: 0.35 }); ev.push({ v: tv + 0.05, type: 'pop', gain: 0.3 }); }
    if (b.drop) ev.push({ v: b.v0, type: 'impact', gain: 0.8 });
    for (const s of b.sfx || []) {
      const [type, off] = String(s).split('@');
      ev.push({ v: b.v0 + (+off || 0), type, gain: 0.6 });
    }
  }
  return ev;
}
