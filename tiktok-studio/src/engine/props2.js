// Accessoires « héros » supplémentaires : écrin + bague diamant (dispersion), pizza, confettis,
// graphique en barres 3D, étiquettes texte. Matériaux PBR, textures procédurales.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { canvas, toTexture, fbmField, normalFromField } from './textures.js';
import { mulberry32, clamp, ease, lerp } from './util.js';

// ---------------- Écrin + bague ----------------
export function makeRingBox() {
  const g = new THREE.Group();
  const velvet = new THREE.MeshPhysicalMaterial({ color: 0x3a0616, roughness: 0.95, sheen: 1, sheenRoughness: 0.4, sheenColor: new THREE.Color(0xff5a7a) });
  const satin = new THREE.MeshPhysicalMaterial({ color: 0xf2e9e4, roughness: 0.45, sheen: 0.6, sheenColor: new THREE.Color(0xffffff) });
  const base = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.34, 0.62, 5, 0.06), velvet);
  base.position.y = 0.17; base.castShadow = true; base.receiveShadow = true;
  const cushion = new THREE.Mesh(new RoundedBoxGeometry(0.54, 0.06, 0.54, 4, 0.03), new THREE.MeshPhysicalMaterial({ color: 0x1a0209, roughness: 0.9, sheen: 1, sheenColor: new THREE.Color(0xc03050) }));
  cushion.position.y = 0.345;
  const lidPivot = new THREE.Group(); lidPivot.position.set(0, 0.34, -0.31);
  const lid = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.16, 0.62, 5, 0.06), velvet);
  lid.position.set(0, 0.08, 0.31); lid.castShadow = true;
  const lining = new THREE.Mesh(new THREE.PlaneGeometry(0.54, 0.54), satin);
  lining.rotation.x = Math.PI / 2; lining.position.set(0, -0.001, 0.31);
  lidPivot.add(lid, lining);
  lidPivot.rotation.x = -1.9;
  g.add(base, cushion, lidPivot);

  const gold = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(1.0, 0.76, 0.33), metalness: 1, roughness: 0.1, clearcoat: 0.5 });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.105, 0.017, 32, 160), gold);
  ring.position.set(0, 0.47, 0.02); ring.castShadow = true;
  // Diamant taille brillant (couronne + pavillon), réfraction + dispersion.
  const prof = [new THREE.Vector2(0.0001, -0.07), new THREE.Vector2(0.055, 0.0), new THREE.Vector2(0.052, 0.012), new THREE.Vector2(0.03, 0.03), new THREE.Vector2(0.0001, 0.03)];
  const dgeo = new THREE.LatheGeometry(prof, 16);
  dgeo.computeVertexNormals();
  const diamond = new THREE.Mesh(dgeo, new THREE.MeshPhysicalMaterial({
    color: 0xdfe8ff, metalness: 0.15, roughness: 0.0, ior: 2.42, specularIntensity: 1, specularColor: new THREE.Color(1, 1, 1),
    iridescence: 1, iridescenceIOR: 1.9, iridescenceThicknessRange: [180, 820], envMapIntensity: 3.2, flatShading: true,
    emissive: 0x223044, emissiveIntensity: 0.4,
  }));
  diamond.position.set(0, 0.47 + 0.105 + 0.055, 0.02);
  const prongMat = gold;
  for (let i = 0; i < 4; i++) {
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.006, 0.05, 8), prongMat);
    const a = i * Math.PI / 2 + Math.PI / 4;
    p.position.set(Math.cos(a) * 0.045, 0.47 + 0.105 + 0.045, 0.02 + Math.sin(a) * 0.045);
    g.add(p);
  }
  const setting = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.02, 0.035, 16), gold);
  setting.position.set(0, 0.47 + 0.105 + 0.012, 0.02);
  g.add(ring, setting, diamond);
  const sc = canvas(128, 128), sctx = sc.getContext('2d');
  const grd = sctx.createRadialGradient(64, 64, 0, 64, 64, 64); grd.addColorStop(0, 'rgba(255,255,255,1)'); grd.addColorStop(0.15, 'rgba(255,255,255,0.6)'); grd.addColorStop(1, 'rgba(255,255,255,0)');
  sctx.fillStyle = grd; sctx.fillRect(0, 0, 128, 128);
  sctx.globalCompositeOperation = 'lighter'; sctx.fillStyle = 'rgba(255,255,255,0.9)';
  sctx.beginPath(); sctx.moveTo(64, 0); sctx.lineTo(68, 60); sctx.lineTo(128, 64); sctx.lineTo(68, 68); sctx.lineTo(64, 128); sctx.lineTo(60, 68); sctx.lineTo(0, 64); sctx.lineTo(60, 60); sctx.closePath(); sctx.fill();
  const glintMat = new THREE.SpriteMaterial({ map: toTexture(sc), color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  const glints = [[0.02, 0.03, 0.05], [-0.03, 0.0, 0.05], [0.0, -0.02, 0.055]].map(([dx, dy, dz], i) => {
    const sp = new THREE.Sprite(glintMat.clone()); sp.position.set(dx, 0.47 + 0.105 + 0.055 + dy, 0.02 + dz); sp.scale.setScalar(0.12); sp.userData.phase = i * 2.1; g.add(sp); return sp;
  });
  g.userData.lid = lidPivot;
  g.userData.diamond = diamond;
  g.userData.glints = glints;
  return g;
}

// ---------------- Pizza ----------------
function pizzaTexture(seed = 3) {
  const S = 1024, c = canvas(S, S), ctx = c.getContext('2d');
  const rnd = mulberry32(seed);
  const cx = S / 2;
  // Pâte / croûte
  const crust = ctx.createRadialGradient(cx, cx, S * 0.38, cx, cx, S * 0.5);
  crust.addColorStop(0, '#d9a45a'); crust.addColorStop(0.6, '#c9863d'); crust.addColorStop(1, '#8a4f1e');
  ctx.fillStyle = crust; ctx.beginPath(); ctx.arc(cx, cx, S * 0.5, 0, Math.PI * 2); ctx.fill();
  // Sauce tomate
  ctx.fillStyle = '#a3261a'; ctx.beginPath(); ctx.arc(cx, cx, S * 0.42, 0, Math.PI * 2); ctx.fill();
  for (let i = 0; i < 900; i++) { const a = rnd() * 6.283, r = Math.sqrt(rnd()) * S * 0.42; ctx.fillStyle = `rgba(${120 + rnd() * 60},${20 + rnd() * 20},${10},${0.25})`; ctx.beginPath(); ctx.arc(cx + Math.cos(a) * r, cx + Math.sin(a) * r, 4 + rnd() * 14, 0, 6.283); ctx.fill(); }
  // Fromage fondu (taches irrégulières)
  for (let i = 0; i < 70; i++) {
    const a = rnd() * 6.283, r = Math.sqrt(rnd()) * S * 0.38;
    const x = cx + Math.cos(a) * r, y = cx + Math.sin(a) * r, rr = 30 + rnd() * 60;
    const gg = ctx.createRadialGradient(x, y, 0, x, y, rr);
    gg.addColorStop(0, '#fff3c4'); gg.addColorStop(0.7, '#f4d27c'); gg.addColorStop(1, 'rgba(240,200,110,0)');
    ctx.fillStyle = gg; ctx.beginPath(); ctx.ellipse(x, y, rr, rr * (0.6 + rnd() * 0.4), rnd() * 3, 0, 6.283); ctx.fill();
  }
  // Pepperoni
  for (let i = 0; i < 16; i++) {
    const a = rnd() * 6.283, r = Math.sqrt(rnd()) * S * 0.34;
    const x = cx + Math.cos(a) * r, y = cx + Math.sin(a) * r, rr = 34 + rnd() * 8;
    const pg = ctx.createRadialGradient(x, y, 0, x, y, rr);
    pg.addColorStop(0, '#b7321f'); pg.addColorStop(0.8, '#8e2012'); pg.addColorStop(1, '#5e150b');
    ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(x, y, rr, 0, 6.283); ctx.fill();
    for (let k = 0; k < 8; k++) { ctx.fillStyle = 'rgba(60,10,5,0.4)'; ctx.beginPath(); ctx.arc(x + (rnd() - 0.5) * rr, y + (rnd() - 0.5) * rr, 3, 0, 6.283); ctx.fill(); }
  }
  // Basilic + origan
  for (let i = 0; i < 10; i++) { const a = rnd() * 6.283, r = Math.sqrt(rnd()) * S * 0.33; ctx.fillStyle = '#2f6b1f'; ctx.beginPath(); ctx.ellipse(cx + Math.cos(a) * r, cx + Math.sin(a) * r, 22, 11, rnd() * 3, 0, 6.283); ctx.fill(); }
  for (let i = 0; i < 400; i++) { const a = rnd() * 6.283, r = Math.sqrt(rnd()) * S * 0.4; ctx.fillStyle = 'rgba(40,60,20,0.7)'; ctx.fillRect(cx + Math.cos(a) * r, cx + Math.sin(a) * r, 2, 2); }
  // Brûlures du four sur la croûte
  for (let i = 0; i < 60; i++) { const a = rnd() * 6.283, r = S * (0.43 + rnd() * 0.06); ctx.fillStyle = `rgba(40,20,5,${0.3 + rnd() * 0.4})`; ctx.beginPath(); ctx.ellipse(cx + Math.cos(a) * r, cx + Math.sin(a) * r, 6 + rnd() * 16, 4 + rnd() * 8, a, 0, 6.283); ctx.fill(); }
  // Découpe en 8 parts
  ctx.strokeStyle = 'rgba(60,15,5,0.55)'; ctx.lineWidth = 3;
  for (let i = 0; i < 4; i++) { const a = i * Math.PI / 4 + 0.2; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * S * 0.5, cx + Math.sin(a) * S * 0.5); ctx.lineTo(cx - Math.cos(a) * S * 0.5, cx - Math.sin(a) * S * 0.5); ctx.stroke(); }
  return c;
}

export function makePizza() {
  const g = new THREE.Group();
  // Planche en bois
  const woodC = canvas(512, 512), wctx = woodC.getContext('2d');
  const rnd = mulberry32(8);
  wctx.fillStyle = '#6b4424'; wctx.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 120; i++) { wctx.strokeStyle = `rgba(${40 + rnd() * 40},${22 + rnd() * 20},10,0.35)`; wctx.lineWidth = 1 + rnd() * 3; wctx.beginPath(); const y = rnd() * 512; wctx.moveTo(0, y); wctx.bezierCurveTo(170, y + (rnd() - 0.5) * 30, 340, y + (rnd() - 0.5) * 30, 512, y + (rnd() - 0.5) * 20); wctx.stroke(); }
  const board = new THREE.Mesh(new THREE.CylinderGeometry(0.68, 0.68, 0.045, 96), new THREE.MeshStandardMaterial({ map: toTexture(woodC), roughness: 0.6 }));
  board.position.y = 0.0225; board.castShadow = true; board.receiveShadow = true;
  const tex = toTexture(pizzaTexture());
  const hf = fbmField(256, { seed: 21, octaves: 5, base: 16 });
  const nrm = toTexture(normalFromField(hf, 256, 6), { srgb: false });
  const top = new THREE.Mesh(new THREE.CircleGeometry(0.56, 128), new THREE.MeshPhysicalMaterial({ map: tex, normalMap: nrm, normalScale: new THREE.Vector2(0.6, 0.6), roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.5 }));
  top.rotation.x = -Math.PI / 2; top.position.y = 0.075; top.receiveShadow = true;
  const crustMat = new THREE.MeshStandardMaterial({ color: 0xc98a45, roughness: 0.75, normalMap: nrm, normalScale: new THREE.Vector2(1.2, 1.2) });
  const crust = new THREE.Mesh(new THREE.TorusGeometry(0.56, 0.042, 24, 160), crustMat);
  crust.rotation.x = Math.PI / 2; crust.position.y = 0.07; crust.castShadow = true;
  const dough = new THREE.Mesh(new THREE.CylinderGeometry(0.57, 0.57, 0.03, 96), crustMat);
  dough.position.y = 0.055;
  g.add(board, dough, top, crust);
  return g;
}

// ---------------- Confettis (instanciés, chute déterministe) ----------------
export function makeConfetti({ count = 420, colors = [0xffd60a, 0xff5fa2, 0xffffff, 0xffb3d1], area = 3.2, height = 4.5, seed = 5 } = {}) {
  const geo = new THREE.PlaneGeometry(0.035, 0.06);
  const mat = new THREE.MeshStandardMaterial({ metalness: 0.6, roughness: 0.3, side: THREE.DoubleSide });
  const mesh = new THREE.InstancedMesh(geo, mat, count);
  const rnd = mulberry32(seed);
  const data = [];
  const col = new THREE.Color();
  for (let i = 0; i < count; i++) {
    data.push({ x: (rnd() - 0.5) * area, z: (rnd() - 0.5) * area * 0.7, y0: height + rnd() * 2.5, v: 0.55 + rnd() * 0.5, f: 1.5 + rnd() * 3, a: rnd() * 6.28, s: (rnd() - 0.5) * 12, w: 0.08 + rnd() * 0.12 });
    mesh.setColorAt(i, col.set(colors[i % colors.length]));
  }
  mesh.instanceColor.needsUpdate = true;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), p = new THREE.Vector3(), sc = new THREE.Vector3(1, 1, 1);
  mesh.userData.update = (lt) => {
    for (let i = 0; i < count; i++) {
      const d = data[i];
      const y = d.y0 - d.v * lt;
      p.set(d.x + Math.sin(lt * d.f + d.a) * d.w, y, d.z + Math.cos(lt * d.f * 0.7 + d.a) * d.w);
      e.set(lt * d.s + d.a, lt * d.s * 0.7, lt * d.s * 0.4);
      q.setFromEuler(e);
      sc.setScalar(y < -0.1 ? 0 : 1);
      m4.compose(p, q, sc);
      mesh.setMatrixAt(i, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
  mesh.frustumCulled = false;
  return mesh;
}

// ---------------- Étiquette texte (sprite plan face caméra) ----------------
export function makeLabel(lines, { w = 512, h = 192, color = '#ffffff', accent = '#FFD60A', scale = 0.5 } = {}) {
  const c = canvas(w, h), ctx = c.getContext('2d');
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = `900 ${Math.round(h * 0.34)}px Montserrat`; ctx.fillStyle = accent; ctx.fillText(lines[0], w / 2, h * 0.32);
  if (lines[1]) { ctx.font = `800 ${Math.round(h * 0.26)}px Montserrat`; ctx.fillStyle = color; ctx.fillText(lines[1], w / 2, h * 0.72); }
  const tex = toTexture(c);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(scale, scale * h / w), new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, depthWrite: false }));
  return m;
}

// ---------------- Graphique en barres 3D ----------------
export function makeBarChart(items, { width = 1.15, maxH = 1.1 } = {}) {
  const g = new THREE.Group();
  const max = Math.max(...items.map((i) => i.value));
  const n = items.length, bw = width / n * 0.72;
  const bars = [];
  items.forEach((it, i) => {
    const hero = i === 0;
    const mat = hero
      ? new THREE.MeshPhysicalMaterial({ color: new THREE.Color(1.0, 0.68, 0.24), metalness: 1, roughness: 0.2, clearcoat: 0.4 })
      : new THREE.MeshPhysicalMaterial({ color: 0x2a2d36, metalness: 0.4, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.1 });
    const b = new THREE.Mesh(new RoundedBoxGeometry(bw, 1, bw, 4, 0.02), mat);
    b.castShadow = true; b.receiveShadow = true;
    const x = (i - (n - 1) / 2) * (width / n);
    b.position.x = x;
    const label = makeLabel([it.name.toUpperCase(), it.valueLabel || ''], { scale: width / n * 1.05, accent: hero ? '#FFD60A' : '#ffffff' });
    label.position.set(x, 0, bw / 2 + 0.06);
    g.add(b, label);
    bars.push({ mesh: b, label, h: Math.max(0.03, it.value / max * maxH), delay: hero ? 0.35 : i * 0.06 });
  });
  g.userData.update = (lt) => {
    for (const b of bars) {
      const k = ease.outExpo(clamp((lt - b.delay) / 1.1));
      const h = Math.max(0.001, b.h * k);
      b.mesh.scale.y = h; b.mesh.position.y = h / 2;
      b.label.position.y = h + 0.13;
    }
  };
  return g;
}
