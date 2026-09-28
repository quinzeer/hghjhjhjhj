// Accessoires 3D procéduraux photoréalistes : smartphone, liasses de billets, podium, texte 3D.
import * as THREE from 'three';
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry.js';
import { canvas, toTexture, roundRect, fbmField } from './textures.js';
import { mulberry32 } from './util.js';

function roundedRectShape(w, h, r) {
  const s = new THREE.Shape();
  const x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  return s;
}

function normalizeUVs(geo) {
  geo.computeBoundingBox();
  const bb = geo.boundingBox, uv = geo.attributes.uv, p = geo.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, (p.getX(i) - bb.min.x) / (bb.max.x - bb.min.x), (p.getY(i) - bb.min.y) / (bb.max.y - bb.min.y));
  uv.needsUpdate = true;
}

// ---------------- Smartphone (échelle « monolithe » ×10) ----------------
export function makePhone({ frameColor = 0x3a3c41, screenTexture = null } = {}) {
  const W = 0.72, H = 1.47, D = 0.078, R = 0.105, bev = 0.012;
  const g = new THREE.Group();
  const bodyGeo = new THREE.ExtrudeGeometry(roundedRectShape(W - bev * 2, H - bev * 2, R - bev), {
    depth: D - bev * 2, bevelEnabled: true, bevelThickness: bev, bevelSize: bev, bevelSegments: 6, curveSegments: 24,
  });
  bodyGeo.translate(0, 0, -(D - bev * 2) / 2);
  const frameMat = new THREE.MeshPhysicalMaterial({ color: frameColor, metalness: 1, roughness: 0.28, clearcoat: 0.3, clearcoatRoughness: 0.2 });
  const body = new THREE.Mesh(bodyGeo, frameMat);
  body.castShadow = true;
  g.add(body);

  // Verre avant + écran émissif.
  const glassGeo = new THREE.ShapeGeometry(roundedRectShape(W - 0.018, H - 0.018, R - 0.009), 24);
  normalizeUVs(glassGeo);
  const screenMat = new THREE.MeshPhysicalMaterial({
    color: 0x000000, emissive: 0xffffff, emissiveIntensity: 1.9, emissiveMap: screenTexture,
    roughness: 0.08, metalness: 0, clearcoat: 0.45, clearcoatRoughness: 0.05, ior: 1.5, specularIntensity: 0.5,
  });
  const glass = new THREE.Mesh(glassGeo, screenMat);
  glass.position.z = D / 2 + 0.0006;
  g.add(glass);

  // Dos en verre dépoli + bloc photo.
  const backMat = new THREE.MeshPhysicalMaterial({ color: 0x2b2d31, roughness: 0.55, metalness: 0.1, clearcoat: 0.6, clearcoatRoughness: 0.45 });
  const back = new THREE.Mesh(glassGeo.clone(), backMat);
  back.rotation.y = Math.PI; back.position.z = -D / 2 - 0.0006;
  g.add(back);
  const camBlock = new THREE.Mesh(new THREE.ExtrudeGeometry(roundedRectShape(0.3, 0.3, 0.07), { depth: 0.01, bevelEnabled: true, bevelThickness: 0.006, bevelSize: 0.006, bevelSegments: 3 }), backMat);
  camBlock.position.set(W / 2 - 0.2, H / 2 - 0.2, -D / 2 - 0.012); camBlock.rotation.y = Math.PI;
  g.add(camBlock);
  const lensGlass = new THREE.MeshPhysicalMaterial({ color: 0x05070a, roughness: 0.02, metalness: 0.2, clearcoat: 1, clearcoatRoughness: 0 });
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x9a9da3, metalness: 1, roughness: 0.2 });
  [[-0.065, 0.065], [-0.065, -0.065], [0.07, 0]].forEach(([dx, dy]) => {
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.058, 0.058, 0.022, 40), ringMat);
    ring.rotation.x = Math.PI / 2; ring.position.set(W / 2 - 0.2 + dx, H / 2 - 0.2 + dy, -D / 2 - 0.024);
    const lens = new THREE.Mesh(new THREE.CircleGeometry(0.046, 40), lensGlass);
    lens.position.set(W / 2 - 0.2 + dx, H / 2 - 0.2 + dy, -D / 2 - 0.0355); lens.rotation.y = Math.PI;
    g.add(ring, lens);
  });
  // Boutons latéraux.
  const btnGeo = new THREE.BoxGeometry(0.012, 0.13, 0.03);
  [[W / 2 + 0.003, 0.28], [-W / 2 - 0.003, 0.36], [-W / 2 - 0.003, 0.2]].forEach(([x, y]) => { const b = new THREE.Mesh(btnGeo, frameMat); b.position.set(x, y, 0); g.add(b); });
  g.userData.screen = glass;
  g.userData.size = { W, H, D };
  return g;
}

// ---------------- Billets (design générique, aucune reproduction de billet réel) ----------------
export function banknoteTexture({ value = '500', hue = '#6d3fa0', seed = 5 } = {}) {
  const c = canvas(1024, 540), ctx = c.getContext('2d');
  const rnd = mulberry32(seed);
  const g = ctx.createLinearGradient(0, 0, 1024, 540);
  g.addColorStop(0, hue); g.addColorStop(0.5, '#c7a9e8'); g.addColorStop(1, hue);
  ctx.fillStyle = g; ctx.fillRect(0, 0, 1024, 540);
  ctx.globalAlpha = 0.18; ctx.strokeStyle = '#2a1840'; ctx.lineWidth = 1.2;
  for (let k = 0; k < 90; k++) { ctx.beginPath(); for (let x = 0; x <= 1024; x += 8) { const y = 270 + Math.sin(x * 0.012 + k * 0.21) * (60 + k * 2.2) * Math.cos(k * 0.13); x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); } ctx.stroke(); }
  ctx.globalAlpha = 1;
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(250, 270, 150, 180, 0, 0, Math.PI * 2); ctx.fill();
  ctx.font = '900 190px Montserrat'; ctx.textAlign = 'right'; ctx.fillStyle = 'rgba(40,20,60,0.85)'; ctx.fillText(value, 990, 250);
  ctx.font = '900 70px Montserrat'; ctx.textAlign = 'left'; ctx.fillText(value, 40, 90); ctx.fillText(value, 40, 510);
  ctx.strokeStyle = 'rgba(40,20,60,0.5)'; ctx.lineWidth = 10; ctx.strokeRect(14, 14, 996, 512);
  for (let i = 0; i < 1400; i++) { ctx.fillStyle = `rgba(0,0,0,${rnd() * 0.05})`; ctx.fillRect(rnd() * 1024, rnd() * 540, 2, 2); }
  return toTexture(c);
}

function stackEdgeTexture(hue = '#7d4fc0') {
  const c = canvas(512, 128), ctx = c.getContext('2d');
  ctx.fillStyle = '#8e6fb8'; ctx.fillRect(0, 0, 512, 128);
  const rnd = mulberry32(3);
  for (let y = 0; y < 128; y += 2) { ctx.fillStyle = rnd() > 0.45 ? hue : '#c9b8e0'; ctx.globalAlpha = 0.5 + rnd() * 0.5; ctx.fillRect(0, y, 512, 1 + (rnd() > 0.8 ? 1 : 0)); }
  ctx.globalAlpha = 1;
  return toTexture(c);
}

function bandTexture(label = '10 000 €') {
  const c = canvas(512, 256), ctx = c.getContext('2d');
  ctx.fillStyle = '#f2efe6'; ctx.fillRect(0, 0, 512, 256);
  ctx.fillStyle = '#c0392b'; ctx.fillRect(0, 20, 512, 18); ctx.fillRect(0, 218, 512, 18);
  ctx.font = '900 64px Montserrat'; ctx.fillStyle = '#222'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, 256, 128);
  return toTexture(c);
}

export function makeCashBundle({ value = '500', hue = '#7a4bb0', seed = 1 } = {}) {
  const w = 0.62, d = 0.33, h = 0.1;
  const top = banknoteTexture({ value, hue, seed });
  const edge = stackEdgeTexture();
  const topMat = new THREE.MeshStandardMaterial({ map: top, roughness: 0.78 });
  const edgeMat = new THREE.MeshStandardMaterial({ map: edge, roughness: 0.9 });
  const bundle = new THREE.Group();
  const box = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), [edgeMat, edgeMat, topMat, topMat, edgeMat, edgeMat]);
  box.castShadow = true; box.receiveShadow = true;
  bundle.add(box);
  const bandMat = new THREE.MeshStandardMaterial({ map: bandTexture(), roughness: 0.6 });
  const band = new THREE.Mesh(new THREE.BoxGeometry(0.1, h + 0.006, d + 0.006), bandMat);
  band.castShadow = true;
  bundle.add(band);
  bundle.userData.size = { w, h, d };
  return bundle;
}

// Pyramide de liasses (disposition déterministe, légères irrégularités).
export function makeCashPile({ rows = 4, seed = 11 } = {}) {
  const g = new THREE.Group();
  const rnd = mulberry32(seed);
  const proto = makeCashBundle({});
  const { w, h, d } = proto.userData.size;
  let level = 0;
  for (let r = rows; r >= 1; r--) {
    for (let i = 0; i < r; i++) for (let j = 0; j < Math.max(1, r - 1); j++) {
      const b = proto.clone();
      b.position.set((i - (r - 1) / 2) * (w + 0.02) + (rnd() - 0.5) * 0.03, level * h + h / 2, (j - (r - 2) / 2) * (d + 0.02) + (rnd() - 0.5) * 0.03);
      b.rotation.y = (rnd() - 0.5) * 0.08;
      g.add(b);
    }
    level++;
  }
  return g;
}

// ---------------- Podium avec liseré LED ----------------
export function makePodium({ radius = 1.1, height = 0.55, led = 0xffd60a } = {}) {
  const g = new THREE.Group();
  const f = fbmField(256, { seed: 4, octaves: 5, base: 8 });
  const c = canvas(256, 256), ctx = c.getContext('2d'); const img = ctx.createImageData(256, 256);
  for (let i = 0; i < f.length; i++) { const v = 90 + f[i] * 90; img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255; }
  ctx.putImageData(img, 0, 0);
  const rough = toTexture(c, { srgb: false, repeat: [3, 1] });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 1.02, height, 96, 1), new THREE.MeshStandardMaterial({ color: 0x111216, roughness: 0.5, roughnessMap: rough, metalness: 0.6 }));
  body.position.y = height / 2; body.castShadow = true; body.receiveShadow = true;
  const top = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.98, radius * 0.98, 0.02, 96), new THREE.MeshPhysicalMaterial({ color: 0x0c0c0f, roughness: 0.32, metalness: 0.1, clearcoat: 0.6, clearcoatRoughness: 0.25 }));
  top.position.y = height + 0.01; top.receiveShadow = true;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.005, 0.012, 12, 160), new THREE.MeshStandardMaterial({ color: 0x000000, emissive: led, emissiveIntensity: 6 }));
  ring.rotation.x = Math.PI / 2; ring.position.y = height - 0.04;
  const ring2 = ring.clone(); ring2.position.y = 0.05;
  g.add(body, top, ring, ring2);
  g.userData.topY = height + 0.02;
  g.userData.ledMat = ring.material;
  return g;
}

// ---------------- Texte 3D extrudé (or / chrome) ----------------
export function makeText3D(font, text, { size = 0.6, depth = 0.16, material = 'gold' } = {}) {
  const geo = new TextGeometry(text, { font, size, depth, curveSegments: 10, bevelEnabled: true, bevelThickness: 0.025, bevelSize: 0.015, bevelSegments: 5 });
  geo.computeBoundingBox();
  const bb = geo.boundingBox;
  geo.translate(-(bb.max.x + bb.min.x) / 2, -bb.min.y, -(bb.max.z + bb.min.z) / 2);
  geo.computeVertexNormals();
  const mats = {
    gold: new THREE.MeshPhysicalMaterial({ color: new THREE.Color(1.0, 0.68, 0.24), metalness: 1, roughness: 0.22, clearcoat: 0.3, clearcoatRoughness: 0.12 }),
    chrome: new THREE.MeshPhysicalMaterial({ color: 0xffffff, metalness: 1, roughness: 0.06 }),
    red: new THREE.MeshPhysicalMaterial({ color: 0xe0201c, metalness: 0.3, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.05 }),
  };
  const m = new THREE.Mesh(geo, mats[material] || mats.gold);
  m.castShadow = true;
  return m;
}
