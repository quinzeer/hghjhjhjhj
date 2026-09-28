// « Le Camille Claudel de la remise » — 4 décors alignés sur l'axe x, la caméra voyage de l'un à l'autre.
// tv (salon) · galerie (les 5 exemplaires) · remise (le drap) · drouot (la vente). Aucune personne représentée.
import { sticker, COLORS } from '/engine/overlay.js';

const X = { tv: 0, galerie: 16, remise: 32, socle: 32, drouot: 48 };

// ---------- textures ----------
function woodTex(K, base = [92, 62, 38], seed = 1, planks = 6) {
  const R = K.rng(seed);
  return K.canvasTex(1024, 1024, (c, w, h) => {
    const ph = h / planks;
    for (let p = 0; p < planks; p++) {
      const t = 0.75 + R() * 0.35;
      c.fillStyle = `rgb(${base[0] * t | 0},${base[1] * t | 0},${base[2] * t | 0})`; c.fillRect(0, p * ph, w, ph);
      for (let k = 0; k < 40; k++) { c.strokeStyle = `rgba(0,0,0,${0.05 + R() * 0.12})`; c.lineWidth = 1 + R() * 2; c.beginPath(); const y = p * ph + R() * ph; c.moveTo(0, y); c.bezierCurveTo(w * 0.3, y + (R() - 0.5) * 20, w * 0.7, y + (R() - 0.5) * 20, w, y + (R() - 0.5) * 10); c.stroke(); }
      c.fillStyle = 'rgba(0,0,0,0.55)'; c.fillRect(0, p * ph, w, 3);
    }
  });
}
function patinaTex(K) {
  const R = K.rng(7);
  return K.canvasTex(512, 512, (c, w, h) => {
    c.fillStyle = '#7a5332'; c.fillRect(0, 0, w, h);
    for (let i = 0; i < 260; i++) { const x = R() * w, y = R() * h, r = 4 + R() * 40; const g = c.createRadialGradient(x, y, 0, x, y, r); const green = R() < 0.25; g.addColorStop(0, green ? 'rgba(70,95,70,0.45)' : R() < 0.5 ? 'rgba(40,24,12,0.5)' : 'rgba(170,120,70,0.35)'); g.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); }
  });
}

import { bronze } from '/project/bronze.js';

// gravure du socle : « C. CLAUDEL · 5 · EUG. BLOT PARIS »
function engraving(K) {
  const tex = K.canvasTex(2048, 170, (c, w, h) => {
    c.clearRect(0, 0, w, h); c.font = '600 100px "Montserrat", serif'; c.textBaseline = 'middle';
    const draw = (t, x) => { c.fillStyle = 'rgba(20,12,6,0.85)'; c.fillText(t, x, h / 2); c.fillStyle = 'rgba(230,190,140,0.35)'; c.fillText(t, x + 2, h / 2 + 3); };
    draw('C. CLAUDEL', 60); draw('5', 980); draw('EUG. BLOT PARIS', 1230);
  });
  const m = new K.THREE.Mesh(new K.THREE.PlaneGeometry(0.8, 0.066), new K.THREE.MeshStandardMaterial({ map: tex, transparent: true, metalness: 0.6, roughness: 0.5 }));
  return m;
}

// écran de télévision : le bronze vu dans un reportage
function tvScreen(K) {
  return K.canvasTex(1280, 720, (c, w, h) => {
    c.clearRect(0, 0, w, h);
    c.fillStyle = '#d6182c'; c.fillRect(0, h - 170, w, 110);
    c.font = '400 76px "Anton", sans-serif'; c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.fillText('ADJUGÉ 3,1 M€', 50, h - 115);
    c.font = '700 34px "Montserrat", sans-serif'; c.fillStyle = '#111'; c.fillRect(0, h - 60, w, 60); c.fillStyle = '#fff'; c.fillText('BRONZE DE CAMILLE CLAUDEL · VENTE AUX ENCHÈRES', 50, h - 30);
    c.fillStyle = '#d6182c'; c.beginPath(); c.arc(w - 70, 60, 16, 0, 7); c.fill(); c.font = '700 30px "Montserrat"'; c.fillStyle = '#fff'; c.fillText('DIRECT', w - 210, 62);
  });
}

export function build(K, T) {
  const { THREE, scene } = K;
  const M = new THREE.MeshPhysicalMaterial({ vertexColors: true, metalness: 0.85, roughness: 0.36, clearcoat: 0.3, clearcoatRoughness: 0.25 });
  const ghostM = new THREE.MeshStandardMaterial({ color: 0x39d5ff, emissive: 0x1a6b88, emissiveIntensity: 1.2, transparent: true, opacity: 0.22, depthWrite: false });
  const S = {};
  const wallM = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.9 });
  const box = (w, h, d, m, p, parent = scene) => { const b = new THREE.Mesh(new K.RoundedBoxGeometry(w, h, d, 2, Math.min(w, h, d) * 0.08), m); b.position.set(...p); b.castShadow = b.receiveShadow = true; parent.add(b); return b; };
  const plane = (w, h, m, p, ry = 0, rx = 0) => { const q = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); q.position.set(...p); q.rotation.set(rx, ry, 0); q.receiveShadow = true; scene.add(q); return q; };

  // ===== salon (tv) =====
  const parquet = woodTex(K, [120, 80, 48], 2, 10); parquet.wrapS = parquet.wrapT = THREE.RepeatWrapping; parquet.repeat.set(3, 3);
  plane(9, 9, new THREE.MeshStandardMaterial({ map: parquet, roughness: 0.55 }), [X.tv, 0, 0], 0, -Math.PI / 2);
  plane(9, 5, wallM(0x1f3b33), [X.tv, 2.5, -2.2]);
  box(1.7, 0.5, 0.45, K.mat.glossy(0x3b2414, { roughness: 0.4 }), [X.tv, 0.25, -1.85]);
  box(1.36, 0.8, 0.06, K.mat.glossy(0x07080b, { roughness: 0.2 }), [X.tv, 0.98, -1.85]);
  S.rt = new THREE.WebGLRenderTarget(640, 360, { type: THREE.HalfFloatType });
  S.screen = plane(1.28, 0.72, new THREE.MeshBasicMaterial({ map: S.rt.texture }), [X.tv, 0.98, -1.815]);
  const banner = plane(1.28, 0.72, new THREE.MeshBasicMaterial({ map: tvScreen(K), transparent: true, toneMapped: false }), [X.tv, 0.98, -1.812]);
  // plateau télé caché (x = −20) : le bronze sous projecteur, filmé par une caméra dédiée
  const tvStatue = bronze(K, M); tvStatue.position.set(-20, 0.3, 0); scene.add(tvStatue); S.tvStatue = tvStatue;
  const tvSpot = new THREE.SpotLight(0xffe2b8, 80, 0, 0.5, 0.6, 2); tvSpot.position.set(-19.2, 2.4, 1.5); tvSpot.target.position.set(-20, 0.5, 0); scene.add(tvSpot, tvSpot.target);
  const tvBack = plane(6, 4, new THREE.MeshStandardMaterial({ color: 0x12151f, roughness: 0.9 }), [-20, 1.5, -1.2]);
  S.tvCam = new THREE.PerspectiveCamera(30, 16 / 9, 0.05, 20);
  const tvGlow = new THREE.PointLight(0x9fb8ff, 2.5, 4, 2); tvGlow.position.set(X.tv, 1.0, -1.3); scene.add(tvGlow);
  const lamp = new THREE.PointLight(0xffb566, 6, 6, 2); lamp.position.set(X.tv - 1.9, 1.4, -1.2); scene.add(lamp);
  box(0.45, 0.3, 0.45, K.mat.matte(0xe8d2a8, { emissive: 0xffb566, emissiveIntensity: 0.6 }), [X.tv - 1.9, 1.45, -1.2]);
  box(1.2, 0.4, 0.6, K.mat.glossy(0x2a1a10), [X.tv, 0.2, 0.2]); // table basse
  for (const dx of [-0.2, 0.22]) { const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.04, 0.1, 24), K.mat.glossy(dx < 0 ? 0xc0392b : 0xf2f2f2)); mug.position.set(X.tv + dx, 0.45, 0.25); mug.castShadow = true; scene.add(mug); }

  // ===== galerie (les 5 exemplaires) =====
  plane(14, 16, new THREE.MeshStandardMaterial({ color: 0x1b1c20, roughness: 0.28, metalness: 0.1 }), [X.galerie, 0, -2], 0, -Math.PI / 2);
  plane(14, 7, wallM(0x14323b), [X.galerie, 3.5, -7]);
  plane(16, 7, wallM(0x14323b), [X.galerie - 3.2, 3.5, -2], Math.PI / 2);
  S.plinths = [];
  for (let i = 0; i < 5; i++) {
    const x = X.galerie + (i - 2) * 0.8, z = 0.4 - i * 1.35;
    box(0.62, 1.0, 0.5, K.mat.matte(0x8f8b84, { roughness: 0.7 }), [x, 0.5, z]);
    const num = K.text(`N°${i + 1}`, { height: 0.09, color: '#b98a3c', stroke: null, lit: true }); num.position.set(x, 0.85, z + 0.255); scene.add(num);
    const real = bronze(K, M); real.scale.setScalar(0.62); real.position.set(x, 1.0, z); scene.add(real);
    const ghost = bronze(K, ghostM); ghost.scale.setScalar(0.62); ghost.position.set(x, 1.0, z); ghost.traverse((o) => (o.castShadow = false)); scene.add(ghost);
    const q = K.text('?', { height: 0.5, color: '#ff2d3d', glow: 0.5 }); q.position.set(x, 1.3, z); scene.add(q);
    const spot = new THREE.SpotLight(0xfff1dc, 0, 0, 0.3, 0.6, 2); spot.position.set(x + 0.4, 3.6, z + 1.2); spot.target.position.set(x, 1.1, z); scene.add(spot, spot.target);
    S.plinths.push({ x, z, real, ghost, q, spot });
  }
  S.priceTag = K.text('3,1 M€', { height: 0.2, color: '#ffe11a', glow: 0.6 }); S.priceTag.position.set(S.plinths[0].x, 1.72, S.plinths[0].z); scene.add(S.priceTag);
  for (const wx of [-2.5, 0, 2.5]) { const ws = new THREE.SpotLight(0x8fc6d6, 25, 0, 0.6, 0.8, 2); ws.position.set(X.galerie + wx, 5.5, -4.5); ws.target.position.set(X.galerie + wx, 2.5, -7); scene.add(ws, ws.target); }
  const galFill = new THREE.PointLight(0x9fc4d0, 3, 12, 2); galFill.position.set(X.galerie + 1, 3, 1.5); scene.add(galFill);

  // ===== remise =====
  const planks = woodTex(K, [96, 70, 48], 5, 8);
  const floorW = woodTex(K, [70, 50, 34], 9, 12); floorW.wrapS = floorW.wrapT = THREE.RepeatWrapping; floorW.repeat.set(2, 2);
  plane(8, 8, new THREE.MeshStandardMaterial({ map: floorW, roughness: 0.85 }), [X.remise, 0, 0], 0, -Math.PI / 2);
  plane(8, 4, new THREE.MeshStandardMaterial({ map: planks, roughness: 0.9 }), [X.remise, 2, -1.8]);
  plane(4, 4, new THREE.MeshStandardMaterial({ map: planks, roughness: 0.9 }), [X.remise - 2.2, 2, 0], Math.PI / 2);
  plane(4, 4, new THREE.MeshStandardMaterial({ map: planks, roughness: 0.9 }), [X.remise + 2.2, 2, 0], -Math.PI / 2);
  const win = plane(0.7, 0.5, new THREE.MeshBasicMaterial({ color: new THREE.Color(0.85, 0.92, 1).multiplyScalar(2.2), toneMapped: false }), [X.remise + 1.2, 2.2, -1.79]);
  const crateTex = woodTex(K, [140, 104, 62], 4, 5);
  const crateM = new THREE.MeshStandardMaterial({ map: crateTex, roughness: 0.8 });
  box(1.0, 0.55, 0.6, crateM, [X.remise, 0.275, -0.6]);
  box(0.6, 0.45, 0.5, crateM, [X.remise - 1.3, 0.225, -1.2]); box(0.5, 0.4, 0.45, crateM, [X.remise - 1.3, 0.65, -1.2]);
  box(0.7, 0.35, 0.5, crateM, [X.remise + 1.35, 0.175, -1.1]);
  const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.018, 10, 48), K.mat.matte(0x222222)); wheel.position.set(X.remise + 1.75, 0.34, -1.55); wheel.rotation.y = 0.3; wheel.castShadow = true; scene.add(wheel);
  for (let k = 0; k < 3; k++) { const tool = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 1.3, 8), K.mat.matte(0x6b4a2b)); tool.position.set(X.remise - 1.9 + k * 0.12, 0.65, -1.65); tool.rotation.z = 0.12; tool.castShadow = true; scene.add(tool); }
  S.statue = bronze(K, M); S.statue.position.set(X.remise, 0.55, -0.6); scene.add(S.statue);
  const plaque = box(0.56, 0.07, 0.03, M, [X.remise, 0.6, -0.6 + 0.2]); S.plaque = plaque;
  const eng = engraving(K); eng.scale.setScalar(0.66); eng.position.set(X.remise, 0.6, -0.6 + 0.2165); scene.add(eng); S.eng = eng;
  // le drap : forme de fantôme bosselée
  const dp = [[0.001, 0.72], [0.18, 0.7], [0.36, 0.6], [0.47, 0.35], [0.52, 0.05], [0.55, 0.0]].map(([r, y]) => new THREE.Vector2(r, y));
  const dg = new THREE.LatheGeometry(dp, 64, 0, Math.PI * 2), dpos = dg.attributes.position;
  for (let i = 0; i < dpos.count; i++) { const x = dpos.getX(i), z = dpos.getZ(i), a = Math.atan2(z, x); const f = Math.sin(a * 7) * 0.02 * (1 - dpos.getY(i) / 0.8); dpos.setX(i, x * (1 + f) * 0.95); dpos.setZ(i, z * (1 + f) * 0.42); }
  dg.computeVertexNormals();
  S.drape = new THREE.Mesh(dg, new THREE.MeshPhysicalMaterial({ color: 0xd8cdb8, roughness: 0.95, sheen: 1, sheenColor: new THREE.Color(0xffffff), sheenRoughness: 0.6, transparent: true, side: THREE.DoubleSide }));
  S.drape.position.set(X.remise, 0.55, -0.6); S.drape.castShadow = true; scene.add(S.drape);
  // faisceau de la fenêtre + poussière
  const beamM = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 0.95, 1).multiplyScalar(0.07), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.9, 2.9, 32, 1, true), beamM);
  beam.position.set(X.remise + 0.6, 1.3, -1.1); beam.rotation.set(0.5, 0, 0.4); scene.add(beam);
  S.dustR = K.dust({ n: 700, radius: 1.3, height: 2.4, size: 0.01, opacity: 0.7 }); S.dustR.position.set(X.remise + 0.4, 0.2, -0.8);
  S.winSpot = new THREE.SpotLight(0xdfe9ff, 60, 0, 0.45, 0.7, 2); S.winSpot.position.set(X.remise + 1.2, 2.3, -1.6); S.winSpot.target.position.set(X.remise, 0.6, -0.6); S.winSpot.castShadow = true; scene.add(S.winSpot, S.winSpot.target);
  S.revealSpot = new THREE.SpotLight(0xffc98a, 0, 0, 0.35, 0.5, 2); S.revealSpot.position.set(X.remise - 0.4, 2.8, 1.0); S.revealSpot.target.position.set(X.remise, 0.8, -0.6); scene.add(S.revealSpot, S.revealSpot.target);

  // ===== Drouot =====
  const velvet = K.canvasTex(512, 512, (c, w, h) => { for (let x = 0; x < w; x++) { const t = 0.55 + 0.45 * Math.pow(Math.sin(x / 18) * 0.5 + 0.5, 1.5); c.fillStyle = `rgb(${120 * t | 0},${10 * t | 0},${22 * t | 0})`; c.fillRect(x, 0, 1, h); } });
  plane(12, 7, new THREE.MeshStandardMaterial({ map: velvet, roughness: 0.95 }), [X.drouot, 3.5, -2.2]);
  plane(12, 12, new THREE.MeshStandardMaterial({ color: 0x2a1a14, roughness: 0.6 }), [X.drouot, 0, 0], 0, -Math.PI / 2);
  box(0.7, 1.0, 0.7, K.mat.glossy(0x0b0b0d), [X.drouot, 0.5, -1.0]);
  S.statueD = bronze(K, M); S.statueD.position.set(X.drouot, 1.0, -1.0); scene.add(S.statueD);
  box(1.1, 1.05, 0.55, K.mat.glossy(0x4a2b16, { roughness: 0.35 }), [X.drouot + 1.4, 0.525, 0.1]); // pupitre
  box(0.16, 0.05, 0.16, K.mat.glossy(0x2d1a0e), [X.drouot + 1.4, 1.075, 0.2]); // tablette de frappe
  S.gavel = new THREE.Group();
  const gw = woodTex(K, [110, 62, 30], 13, 3); const head = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.14, 24), new THREE.MeshPhysicalMaterial({ map: gw, roughness: 0.35, clearcoat: 0.8 })); head.rotation.z = Math.PI / 2; S.gavel.add(head);
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.014, 0.26, 12), new THREE.MeshPhysicalMaterial({ map: gw, roughness: 0.4, clearcoat: 0.6 })); handle.position.set(0, 0, 0.13); handle.rotation.x = Math.PI / 2; S.gavel.add(handle);
  K.shadows(S.gavel); scene.add(S.gavel);
  for (let r = 0; r < 2; r++) for (let k = 0; k < 5; k++) box(0.42, 0.9, 0.42, K.mat.matte(0x151515), [X.drouot - 1.6 + k * 0.8, 0.45, 1.6 + r * 0.9]); // chaises
  const deskSpot = new THREE.SpotLight(0xffd9a8, 45, 0, 0.35, 0.6, 2); deskSpot.position.set(X.drouot + 0.8, 2.6, 1.6); deskSpot.target.position.set(X.drouot + 1.4, 1.1, 0.2); scene.add(deskSpot, deskSpot.target);
  S.drouotSpot = new THREE.SpotLight(0xfff0d8, 0, 0, 0.3, 0.5, 2); S.drouotSpot.position.set(X.drouot, 4, 0.8); S.drouotSpot.target.position.set(X.drouot, 1.2, -1.0); scene.add(S.drouotSpot, S.drouotSpot.target);
  const dFill = new THREE.PointLight(0xff9a7a, 12, 9, 2); dFill.position.set(X.drouot - 2, 2.5, 1.5); scene.add(dFill);
  S.confetti = K.confetti({ origin: [X.drouot, 2.8, -0.5], colors: [0xffd24a, 0xffffff, 0xffc657] });

  // instants clés (pris sur les mots de la voix)
  const at = (id, word, fallback) => { const b = T.beat(id); const w = b.words.find((x) => x.w.toLowerCase().startsWith(word)); return w ? w.t : b.v0 + fallback; };
  S.tCut = at('hook', 'et', 4.2) - 0.05;
  S.tReveal = T.beat('reveal').v0 + 0.1;
  S.tStrike = T.beat('vente').v0 + 2.35;
  return S;
}

export function update(K, v, T, S) {
  const b = T.beatAt(v);
  const st = b.id === 'hook' ? (v < S.tCut ? 'tv' : 'remise') : b.station;
  // la lumière principale suit le décor actif
  const kx = X[st] ?? 0;
  K.lights.key.position.set(kx + 1.5, 6.5, 2.5); K.lights.key.target.position.set(kx, 0.8, -0.8);
  K.lights.key.intensity = st === 'remise' || st === 'socle' ? 35 : st === 'drouot' ? 60 : st === 'galerie' ? 12 : 110;
  // galerie
  const kO = T.k('oeuvre', v), inFin = v >= T.at('fin');
  S.plinths.forEach((p, i) => {
    const appear = K.easeOutBack((v - T.at('oeuvre') - 0.8 - i * 0.55) / 0.4);
    const found = (i === 0 && v >= T.at('n1') + 0.3) || (inFin && (i === 2 || i === 4));
    p.ghost.visible = !found && !(inFin && (i === 1 || i === 3)) && appear > 0.01;
    p.ghost.scale.setScalar(0.62 * Math.max(1e-4, appear));
    p.ghost.rotation.y = v * 0.3;
    p.real.visible = found; p.real.rotation.y = 0.4 + Math.sin(v * 0.4) * 0.2;
    p.q.visible = inFin && (i === 1 || i === 3); p.q.position.y = 1.3 + Math.sin(v * 3 + i) * 0.04;
    p.spot.intensity = found ? 75 : inFin && (i === 1 || i === 3) ? 30 : kO > 0 ? 22 : 0;
  });
  S.priceTag.visible = v >= T.at('n1') + 4.0 && v < T.beat('n1').v1;
  S.priceTag.scale.setScalar(K.easeOutBack((v - T.at('n1') - 4.0) / 0.35) || 1e-4);
  // remise : le drap s'envole
  const r = K.clamp((v - S.tReveal) / 1.1, 0, 1);
  S.drape.visible = r < 1;
  S.eng.visible = S.plaque.visible = v >= S.tReveal;
  S.drape.position.set(X.remise + r * 0.6, 0.55 + K.easeIn(r) * 2.2, -0.6 + r * 0.4);
  S.drape.rotation.set(r * 0.9, r * 1.4, r * 0.5);
  S.drape.material.opacity = 1 - K.easeIn(r);
  S.revealSpot.intensity = 140 * K.ease((v - S.tReveal) / 0.8);
  S.statue.rotation.y = -0.15;
  S.dustR.userData.update(v);
  // Drouot : le marteau et la sculpture qui tourne
  const ts = v - S.tStrike;
  const lift = ts < -0.35 ? K.ease((ts + 1.2) / 0.6) : ts < 0 ? 1 - K.easeIn((ts + 0.35) / 0.35) : K.bounce(Math.min(1, ts / 0.3)) * 0;
  S.gavel.position.set(X.drouot + 1.4, 1.14 + lift * 0.28, 0.2);
  S.gavel.rotation.set(0, 0.3, -lift * 0.9);
  S.statueD.rotation.y = v * 0.35;
  // rendu de l'écran de télévision pendant le hook
  if (v < S.tCut + 0.1) {
    S.tvStatue.rotation.y = 0.5 + v * 0.25;
    S.tvCam.position.set(-20 + 0.35, 0.72, 1.25); S.tvCam.lookAt(-20, 0.55, 0);
    K.renderer.setRenderTarget(S.rt); K.renderer.render(K.scene, S.tvCam); K.renderer.setRenderTarget(null);
  }
  S.drouotSpot.intensity = v >= T.at('vente') ? 260 : 0;
  S.confetti.userData.update(ts - 0.05);
}

export function camera(K, v, T, S) {
  const b = T.beatAt(v);
  const view = (id, vv) => {
    const B = T.beat(id), k = K.clamp((vv - B.v0) / B.dur, 0, 1);
    switch (id) {
      case 'hook': {
        if (vv < S.tCut) { const kk = K.easeInOut((vv - B.v0) / (S.tCut - B.v0)); return { eye: [X.tv + 0.2 * kk, 1.0 + 0.3 * kk, 0.2 + 2.2 * kk], tgt: [X.tv, 0.9 - 0.1 * kk, -1.85], fov: 34, focus: [X.tv, 0.98, -1.82], aperture: 0.003 }; }
        const kk = K.clamp((vv - S.tCut) / (B.v1 - S.tCut), 0, 1);
        return K.orbit([X.remise, 0.85, -0.6], 0.5 - kk * 0.15, 0.14, 3.2 - kk * 0.5, 36, [X.remise, 0.85, -0.6]);
      }
      case 'oeuvre': return { eye: [X.galerie - 4.6 + k * 0.4, 2.7, 2.6 - k * 0.3], tgt: [X.galerie + 0.3, 0.95, -2.2], fov: 38, focus: [X.galerie - 0.8, 1.2, -0.95], aperture: 0.0012, offsetY: -0.04 };
      case 'n1': { const p = S.plinths[0]; return K.orbit([p.x + 0.05, 1.3, p.z], -0.6 + k * 0.55, 0.16, 1.9 - k * 0.35, 32, [p.x, 1.2, p.z]); }
      case 'freres': return { eye: [X.remise - 1.1 + k * 0.5, 1.35 - k * 0.2, 3.6 - k * 0.9], tgt: [X.remise, 0.8, -0.6], fov: 38, focus: [X.remise, 0.85, -0.6], aperture: 0.0025 };
      case 'appel': return { eye: [X.remise - 0.7, 1.1, 2.4 - k * 0.3], tgt: [X.remise, 0.85, -0.6], fov: 36, focus: [X.remise, 0.85, -0.6], aperture: 0.003 };
      case 'reveal': return K.orbit([X.remise, 0.84, -0.6], 0.25 + k * 0.5, 0.16, 2.2 - k * 0.35, 32, [X.remise, 0.86, -0.6]);
      case 'preuve': return { eye: [X.remise - 0.2 + k * 0.4, 0.66, -0.05], tgt: [X.remise - 0.16 + k * 0.32, 0.6, -0.39], fov: 30, focus: [X.remise - 0.16 + k * 0.32, 0.6, -0.39], aperture: 0.006 };
      case 'vente': {
        const ts = vv - S.tStrike;
        if (ts < 0.25) return { eye: [X.drouot + 1.05, 1.35, 0.95], tgt: [X.drouot + 1.4, 1.1, 0.2], fov: 32, focus: [X.drouot + 1.4, 1.12, 0.2], aperture: 0.005 };
        return K.orbit([X.drouot, 1.3, -1.0], 0.2 + ts * 0.08, 0.2, 2.6 + ts * 0.25, 36, [X.drouot, 1.3, -1.0]);
      }
      case 'fin': return { eye: [X.galerie - 3.0 + k * 0.3, 1.5 + k * 0.15, 1.8 + k * 0.5], tgt: [X.galerie + 0.6, 1.1, -2.7], fov: 36, focus: [X.galerie - 0.8, 1.3, -0.95], aperture: 0.001, offsetY: -0.04 };
    }
  };
  let cam = view(b.id, v);
  const prev = T.beats[b.i - 1];
  // fondu entre plans d'un même décor, coupe franche entre décors (sauf galerie → galerie)
  if (prev && prev.station === b.station && v - b.v0 < 0.7) cam = K.mixCam(view(prev.id, v), cam, (v - b.v0) / 0.7);
  if (cam.offsetY === undefined) cam.offsetY = 0.05;
  if (b.id === 'vente' && v >= S.tStrike && v < S.tStrike + 0.5) cam.shake = 0.035 * (1 - (v - S.tStrike) / 0.5);
  if (b.id === 'reveal' && v - b.v0 < 0.4) cam.shake = 0.02;
  // effets d'image : flash à la révélation et au coup de marteau, bandes cinéma dans la remise
  const g = K.grade;
  g.uFlash.value = Math.max(v >= S.tReveal && v < S.tReveal + 0.25 ? 0.35 * (1 - (v - S.tReveal) / 0.25) : 0, v >= S.tStrike && v < S.tStrike + 0.2 ? 0.5 * (1 - (v - S.tStrike) / 0.2) : 0);
  g.uWarm.value = b.station === 'remise' || b.station === 'socle' ? 0.05 : 0.02;
  return cam;
}

export function overlay(o, v, T, S) {
  // compteur d'enchères qui s'emballe jusqu'à 1 500 000 € au coup de marteau
  const t = v - (S.tStrike - 1.6);
  if (t < 0 || v > T.beat('vente').v1) return;
  const k = Math.min(1, t / 1.6), val = Math.round((k < 1 ? K3(k) : 1) * 1500000 / 10000) * 10000;
  const txt = val.toLocaleString('fr-FR').replace(/ | /g, ' ') + ' €';
  sticker(o.c, txt, 540, 1120, k < 1 ? 96 : 118, k < 1 ? '#ffffff' : COLORS.yellow);
}
const K3 = (k) => 1 - Math.pow(1 - k, 3);

export function sfx(T, story, S) {
  const ev = [{ v: S.tStrike, type: 'knock', gain: 0.9 }, { v: S.tStrike, type: 'impact', gain: 0.7 }, { v: S.tStrike + 0.05, type: 'coin', gain: 0.5 }, { v: S.tCut, type: 'whooshDown', gain: 0.45 }];
  for (let i = 0; i < 12; i++) ev.push({ v: S.tStrike - 1.6 + i * 0.13, type: 'tick', gain: 0.25 });
  for (let i = 0; i < 5; i++) ev.push({ v: T.at('oeuvre') + 0.8 + i * 0.55, type: 'pop', gain: 0.3 });
  ev.push({ v: T.at('fin') + 0.2, type: 'heartbeat', gain: 0.5 });
  return ev;
}
