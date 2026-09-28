// « Le Plateau » : décor signature de la chaîne. Sol résine miroir, mur LED 16:9, totems,
// barres lumineuses, faisceaux volumétriques dans la brume, poussière en suspension, podium.
import * as THREE from 'three';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';
import { ReflectiveFloor } from '../engine/floor.js';
import { makeSoftboxEnv } from '../engine/envstudio.js';
import { canvas, toTexture, floorRoughness, fbmField, normalFromField } from '../engine/textures.js';
import { makePhone, makeCashPile, makePodium, makeText3D } from '../engine/props.js';
import { makeRingBox, makePizza, makeConfetti, makeBarChart } from '../engine/props2.js';
import { drawWall, drawPhone } from './screens.js';
import { mulberry32, clamp, ease, lerp } from '../engine/util.js';

RectAreaLightUniformsLib.init();

const beamVert = /* glsl */ `
varying vec3 vN; varying vec3 vV; varying float vH;
void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); vH = uv.y; gl_Position = projectionMatrix*mv; }`;
const beamFrag = /* glsl */ `
uniform vec3 uColor; uniform float uIntensity; varying vec3 vN; varying vec3 vV; varying float vH;
void main(){ float edge = pow(abs(dot(vN, vV)), 2.5); float fall = pow(vH, 2.2); gl_FragColor = vec4(uColor * uIntensity * edge * fall, 1.0); }`;

function makeBeam(color, length = 8, r0 = 0.06, r1 = 0.9) {
  const geo = new THREE.CylinderGeometry(r0, r1, length, 40, 1, true);
  geo.translate(0, -length / 2, 0);
  const mat = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uIntensity: { value: 0.1 } },
    vertexShader: beamVert, fragmentShader: beamFrag,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.FrontSide,
  });
  const m = new THREE.Mesh(geo, mat);
  m.renderOrder = 10;
  return m;
}

function dustSprite() {
  const c = canvas(64, 64), ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.35, 'rgba(255,255,255,0.35)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64);
  return toTexture(c);
}

// Couleur dominante d'un écran (éclaire la scène comme un vrai mur LED).
const WALL_TINT = { breaking: 0xff2a2a, number: 0xffc400, photo: 0x6a7bff, grid: 0x6a7bff, logo: 0xffd60a, title: 0xb44dff };

export class StudioSet {
  constructor(ctx) {
    this.ctx = ctx;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(32, ctx.W / ctx.H, 0.05, 120);
    this.images = ctx.images;
  }

  async load(assets) {
    const S = this.scene;
    S.environment = makeSoftboxEnv(assets.renderer);
    S.environmentIntensity = 0.9;
    S.background = new THREE.Color(0x010102);
    S.fog = new THREE.FogExp2(0x020206, 0.028);

    // Sol : résine sombre, rugosité variable, micro-relief.
    const rough = toTexture(floorRoughness(512, 7), { srgb: false });
    const hf = fbmField(256, { seed: 12, octaves: 5, base: 8 });
    const nrm = toTexture(normalFromField(hf, 256, 3), { srgb: false });
    this.floor = new ReflectiveFloor({ size: 70, resolution: Math.round(this.ctx.W / 3), aspect: this.ctx.W / this.ctx.H, color: 0x050506, roughness: 1, roughnessMap: rough, normalMap: nrm, normalScale: 0.1, repeat: 10, strength: 0.55 });
    S.add(this.floor);

    // Mur LED principal (16:9) + masque de pixels RVB.
    this.wallCanvas = canvas(1920, 1080);
    this.wallTex = toTexture(this.wallCanvas);
    const pix = canvas(8, 8); const pctx = pix.getContext('2d');
    pctx.fillStyle = '#000'; pctx.fillRect(0, 0, 8, 8);
    pctx.fillStyle = '#ff5050'; pctx.fillRect(1, 1, 2, 6); pctx.fillStyle = '#50ff50'; pctx.fillRect(3, 1, 2, 6); pctx.fillStyle = '#5050ff'; pctx.fillRect(5, 1, 2, 6);
    const pixTex = toTexture(pix, { srgb: false, repeat: [480, 270] });
    const wallMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: this.wallTex, emissiveIntensity: 1.25, roughness: 0.35, metalness: 0 });
    wallMat.onBeforeCompile = (sh) => {
      sh.uniforms.tPix = { value: pixTex };
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D tPix;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance *= mix(vec3(1.0), texture2D(tPix, vEmissiveMapUv * 480.0).rgb * 1.6, 0.18);');
    };
    const wallW = 13.5, wallH = wallW * 9 / 16;
    this.wall = new THREE.Mesh(new THREE.PlaneGeometry(wallW, wallH), wallMat);
    this.wall.position.set(0, wallH / 2 + 0.25, -7.5);
    S.add(this.wall);
    const frame = new THREE.Mesh(new THREE.BoxGeometry(wallW + 0.3, wallH + 0.3, 0.2), new THREE.MeshStandardMaterial({ color: 0x0a0a0a, roughness: 0.6, metalness: 0.8 }));
    frame.position.set(0, wallH / 2 + 0.25, -7.62); S.add(frame);
    this.wallLight = new THREE.RectAreaLight(0xffffff, 0.9, wallW, wallH);
    this.wallLight.position.set(0, wallH / 2 + 0.25, -7.3); this.wallLight.lookAt(0, 1.5, 0);
    S.add(this.wallLight);

    // Totems LED portrait.
    this.totems = [-1, 1].map((side) => {
      const c = canvas(540, 960); const tex = toTexture(c);
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 3.02), new THREE.MeshStandardMaterial({ color: 0, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 1.15, roughness: 0.4 }));
      m.position.set(side * 3.4, 1.62, -3.0); m.rotation.y = -side * 0.45;
      const back = new THREE.Mesh(new THREE.BoxGeometry(1.82, 3.14, 0.12), new THREE.MeshStandardMaterial({ color: 0x0b0b0d, metalness: 0.7, roughness: 0.4 }));
      back.position.copy(m.position); back.rotation.copy(m.rotation); back.translateZ(-0.07);
      S.add(m, back);
      return { mesh: m, canvas: c, tex };
    });

    // Barres lumineuses verticales (se reflètent dans le sol).
    this.bars = [];
    const barGeo = new THREE.CylinderGeometry(0.03, 0.03, 4.2, 16);
    for (let i = 0; i < 6; i++) {
      const side = i < 3 ? -1 : 1, k = i % 3;
      const mat = new THREE.MeshStandardMaterial({ color: 0, emissive: 0xffd60a, emissiveIntensity: 4 });
      const b = new THREE.Mesh(barGeo, mat);
      b.position.set(side * (5.0 + k * 1.3), 2.1, -4.2 - k * 1.4);
      S.add(b); this.bars.push(b);
    }

    // Éclairage : clé douce (ombres), boîte à lumière zénithale, contre-jours colorés.
    this.key = new THREE.SpotLight(0xfff1e0, 70, 30, 0.38, 0.7, 1.8);
    this.key.position.set(3.2, 6.5, 4.2); this.key.target.position.set(0, 0.8, 0);
    this.key.castShadow = true; this.key.shadow.mapSize.set(2048, 2048); this.key.shadow.bias = -0.0002; this.key.shadow.radius = 5;
    S.add(this.key, this.key.target);
    this.top = new THREE.RectAreaLight(0xfff6ea, 5.5, 2.4, 1.2);
    this.top.position.set(0, 3.4, 0.9); this.top.lookAt(0, 0.6, 0);
    // (lumière d'appoint zénithale fournie par l'environnement softbox)
    this.rimL = new THREE.PointLight(0x4d7bff, 16, 9, 1.8); this.rimL.position.set(-2.6, 2.4, -1.6);
    this.rimR = new THREE.PointLight(0xff3d7f, 16, 9, 1.8); this.rimR.position.set(2.6, 2.4, -1.6);
    S.add(this.rimL, this.rimR);

    // Faisceaux volumétriques derrière le podium.
    this.beams = [];
    [[-2.8, 7.5, -3.2, 0.28], [2.8, 7.5, -3.2, -0.28], [0, 7.8, -5.2, 0]].forEach(([x, y, z, rz], i) => {
      const beam = makeBeam(i === 2 ? 0xdfe8ff : 0xffe2a8);
      beam.position.set(x, y, z); beam.rotation.z = rz; beam.rotation.x = 0.08;
      const can = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.22, 0.45, 24), new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8, roughness: 0.35 }));
      can.position.set(x, y + 0.1, z); can.rotation.copy(beam.rotation);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.15, 24), new THREE.MeshStandardMaterial({ color: 0, emissive: 0xfff4d6, emissiveIntensity: 10 }));
      lens.position.set(x, y - 0.13, z); lens.rotation.x = Math.PI / 2;
      S.add(beam, can, lens); this.beams.push(beam);
    });

    // Poussière en suspension.
    const rnd = mulberry32(99), N = 700;
    const pos = new Float32Array(N * 3); this.dustSeed = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) { pos[i * 3] = (rnd() - 0.5) * 10; pos[i * 3 + 1] = rnd() * 6; pos[i * 3 + 2] = -6 + rnd() * 10; this.dustSeed[i * 3] = rnd(); this.dustSeed[i * 3 + 1] = rnd(); this.dustSeed[i * 3 + 2] = rnd(); }
    this.dustBase = pos.slice();
    const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    this.dust = new THREE.Points(dg, new THREE.PointsMaterial({ size: 0.016, map: dustSprite(), transparent: true, opacity: 0.45, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xfff0d0 }));
    S.add(this.dust);

    // Podium + accessoires.
    this.podium = makePodium({});
    S.add(this.podium);
    const top = this.podium.userData.topY;
    this.props = {};
    this.phoneCanvas = canvas(720, 1470);
    this.phoneTex = toTexture(this.phoneCanvas);
    const phone = makePhone({ screenTexture: this.phoneTex });
    phone.position.set(0, top + 0.78, 0);
    this.props.phone = phone;
    const cash = makeCashPile({ rows: 4 }); cash.position.y = top; cash.scale.setScalar(0.85);
    this.props.cash = cash;
    this.font = await assets.font3D('Anton-Regular.ttf');
    this.textCache = new Map();
    const ringbox = makeRingBox(); ringbox.position.y = top; ringbox.scale.setScalar(1.25); this.props.ringbox = ringbox;
    const pizza = makePizza(); pizza.position.y = top; this.props.pizza = pizza;
    this.confetti = makeConfetti({}); this.confetti.visible = false; S.add(this.confetti);
    this.charts = new Map();
    try {
      const car = (await assets.model('covered_car')).clone();
      const bb = new THREE.Box3().setFromObject(car); const sz = bb.getSize(new THREE.Vector3());
      const s = 4.4 / Math.max(sz.x, sz.y, sz.z); car.scale.setScalar(s);
      const bb2 = new THREE.Box3().setFromObject(car);
      car.position.set(-(bb2.min.x + bb2.max.x) / 2, -bb2.min.y, -(bb2.min.z + bb2.max.z) / 2);
      const holder = new THREE.Group(); holder.add(car); holder.position.set(0, 0, 0.3); this.props.car = holder;
    } catch (e) { console.warn('car', e); }
    for (const name of ['vintage_suitcase', 'Megaphone_01', 'magnifying_glass_01', 'marble_bust_01']) {
      try {
        const m = (await assets.model(name)).clone();
        const box = new THREE.Box3().setFromObject(m); const size = box.getSize(new THREE.Vector3());
        const s = 1.2 / Math.max(size.x, size.y, size.z); m.scale.setScalar(s);
        const box2 = new THREE.Box3().setFromObject(m); m.position.y = top - box2.min.y; m.position.x -= (box2.min.x + box2.max.x) / 2; m.position.z -= (box2.min.z + box2.max.z) / 2;
        const holder = new THREE.Group(); holder.add(m); this.props[name] = holder;
      } catch (e) { console.warn('model', name, e); }
    }
    for (const p of Object.values(this.props)) { p.visible = false; S.add(p); }
  }

  text3D(text, material) {
    const key = text + '|' + material;
    if (!this.textCache.has(key)) {
      const m = makeText3D(this.font, text, { size: 0.55, depth: 0.16, material });
      m.position.y = this.podium.userData.topY + 0.01;
      m.visible = false; this.scene.add(m);
      this.textCache.set(key, m);
    }
    return this.textCache.get(key);
  }

  chart(items) {
    const key = JSON.stringify(items);
    if (!this.charts.has(key)) {
      const c = makeBarChart(items);
      c.position.y = this.podium.userData.topY + 0.01;
      c.visible = false; this.scene.add(c);
      this.charts.set(key, c);
    }
    return this.charts.get(key);
  }

  // Redessine un écran uniquement si son contenu change (économise le téléversement GPU).
  paint(slot, draw, spec, lt, animFor = 1.8) {
    const animated = lt < animFor || spec.kind === 'breaking' || spec.kind === 'live' || spec.kind === 'map';
    const key = JSON.stringify(spec) + (animated ? '@' + lt.toFixed(3) : '');
    if (slot.key === key) return;
    slot.key = key;
    draw();
    slot.tex.needsUpdate = true;
  }

  // Préréglages caméra pensés pour le 9:16 (sujet dans le tiers central, sous les titres).
  camSpec(shot) {
    const c = shot.cam || 'hero';
    if (typeof c === 'object') return c;
    const d = shot.end - shot.start;
    const top = this.podium.userData.topY;
    const cy = top + 0.7; // centre du sujet
    const P = {
      wide: { pos: [{ t: 0, v: [0, 2.3, 10.5] }, { t: d, v: [0, 2.0, 9.0] }], target: [{ t: 0, v: [0, 2.0, -1.5] }], fov: [{ t: 0, v: 40 }], shake: 0.3 },
      hero: { pos: [{ t: 0, v: [0.9, cy + 0.35, 4.3] }, { t: d, v: [0.45, cy + 0.3, 3.6] }], target: [{ t: 0, v: [0, cy - 0.2, 0] }], fov: [{ t: 0, v: 34 }], shake: 0.45 },
      heroLeft: { pos: [{ t: 0, v: [-1.1, cy + 0.2, 4.1] }, { t: d, v: [-0.6, cy + 0.35, 3.5] }], target: [{ t: 0, v: [0, cy - 0.2, 0] }], fov: [{ t: 0, v: 34 }], shake: 0.45 },
      low: { pos: [{ t: 0, v: [0.5, 0.45, 3.7] }, { t: d, v: [0.2, 0.4, 3.2] }], target: [{ t: 0, v: [0, cy + 0.05, 0] }], fov: [{ t: 0, v: 38 }], shake: 0.4 },
      orbit: { pos: [{ t: 0, v: [2.8, cy + 0.5, 3.0] }, { t: d / 2, v: [0, cy + 0.55, 4.1], ease: 'linear' }, { t: d, v: [-2.8, cy + 0.5, 3.0], ease: 'linear' }], target: [{ t: 0, v: [0, cy - 0.15, 0] }], fov: [{ t: 0, v: 34 }], shake: 0.3 },
      wall: { pos: [{ t: 0, v: [0, 3.9, 3.0] }, { t: d, v: [0, 3.9, 1.6] }], target: [{ t: 0, v: [0, 3.9, -7.5] }], fov: [{ t: 0, v: 50 }], shake: 0.3 },
      crane: { pos: [{ t: 0, v: [0, 6.2, 5.2] }, { t: d, v: [0.35, cy + 0.4, 3.8], ease: 'inOutQuart' }], target: [{ t: 0, v: [0, top, 0] }, { t: d, v: [0, cy - 0.2, 0] }], fov: [{ t: 0, v: 36 }], shake: 0.25 },
      push: { pos: [{ t: 0, v: [0, cy + 0.25, 5.4] }, { t: d, v: [0, cy + 0.2, 3.4], ease: 'inOutQuad' }], target: [{ t: 0, v: [0, cy - 0.15, 0] }], fov: [{ t: 0, v: 34 }], shake: 0.35 },
      car: { pos: [{ t: 0, v: [3.6, 0.55, 4.6] }, { t: d, v: [2.9, 0.7, 4.0] }], target: [{ t: 0, v: [0, 0.65, 0.3] }], fov: [{ t: 0, v: 36 }], shake: 0.4 },
      carSide: { pos: [{ t: 0, v: [-4.2, 1.3, 3.4] }, { t: d, v: [-3.4, 1.1, 2.8] }], target: [{ t: 0, v: [0, 0.6, 0.3] }], fov: [{ t: 0, v: 36 }], shake: 0.4 },
      chart: { pos: [{ t: 0, v: [0.25, 1.5, 3.9] }, { t: d, v: [0.1, 1.45, 3.4] }], target: [{ t: 0, v: [0, 1.22, 0] }], fov: [{ t: 0, v: 36 }], shake: 0.35 },
      food: { pos: [{ t: 0, v: [0.55, 2.55, 2.5] }, { t: d, v: [0.25, 2.3, 2.1] }], target: [{ t: 0, v: [0, top + 0.15, 0.05] }], fov: [{ t: 0, v: 34 }], shake: 0.35 },
      phone: { pos: [{ t: 0, v: [0.35, 1.72, 3.3] }, { t: d, v: [0.15, 1.68, 2.9] }], target: [{ t: 0, v: [0, 1.55, 0] }], fov: [{ t: 0, v: 34 }], shake: 0.4 },
      macro: { pos: [{ t: 0, v: [0.55, top + 0.9, 1.9] }, { t: d, v: [0.25, top + 0.8, 1.45] }], target: [{ t: 0, v: [0, top + 0.62, 0] }], fov: [{ t: 0, v: 30 }], shake: 0.35 },
      top: { pos: [{ t: 0, v: [0.01, 7.5, 0.6] }, { t: d, v: [0.01, 6.0, 0.5] }], target: [{ t: 0, v: [0, top, 0] }], fov: [{ t: 0, v: 40 }], roll: [{ t: 0, v: 0 }, { t: d, v: 0.25 }], shake: 0.2 },
    };
    return P[c] || P.hero;
  }

  focus(shot) {
    const c = shot.cam || 'hero';
    if (c === 'wall') return { target: [0, 3.9, -7.5], range: 6, bokeh: 1.2 };
    if (c === 'wide') return { target: [0, 1.2, 0], range: 5, bokeh: 1.2 };
    if (c === 'top') return { target: [0, this.podium.userData.topY, 0], range: 2, bokeh: 1.5 };
    if (c === 'car' || c === 'carSide') return { target: [0, 0.7, 0.3], range: 3, bokeh: 1.6 };
    if (c === 'chart') return { target: [0, 1.1, 0], range: 1.6, bokeh: 2.2 };
    if (c === 'food') return { target: [0, this.podium.userData.topY + 0.15, 0.05], range: 0.9, bokeh: 2.6 };
    if (c === 'phone') return { target: [0, 1.35, 0.04], range: 1.2, bokeh: 2.6 };
    if (c === 'macro') return { target: [0, this.podium.userData.topY + 0.62, 0], range: 0.5, bokeh: 3.2 };
    return { target: [0, this.podium.userData.topY + 0.55, 0], range: 1.6, bokeh: 2.6 };
  }

  update(shot, lt, t) {
    const p = shot.params || {};
    for (const v of Object.values(this.props)) v.visible = false;
    for (const m of this.textCache.values()) m.visible = false;
    for (const c of this.charts.values()) c.visible = false;
    let prop = null;
    const top = this.podium.userData.topY;
    this.podium.visible = p.prop !== 'car';
    if (p.prop === 'chart') { prop = this.chart(p.chart); prop.userData.update(lt); }
    else if (p.prop === 'text3d') prop = this.text3D(p.text || '#1', p.material || 'gold');
    else if (p.prop && this.props[p.prop]) prop = this.props[p.prop];
    if (prop) {
      prop.visible = true;
      const intro = ease.outBack(clamp(lt / 0.45));
      prop.rotation.y = (p.spin ?? 0.3) * lt + (p.yaw ?? 0);
      if (p.prop === 'phone') { prop.rotation.x = -0.06 + Math.sin(lt * 1.3) * 0.02; prop.position.y = top + 0.78 + Math.sin(lt * 1.7) * 0.02; }
      if (p.prop === 'text3d') { prop.position.y = top + 0.01; prop.rotation.y = Math.sin(lt * 0.8) * 0.25 + (p.yaw ?? 0); prop.rotation.x = -0.14; }
      if (p.prop === 'pizza') { prop.rotation.x = 0.32; prop.position.y = top + 0.18; prop.position.z = 0.05; }
      if (p.prop === 'chart' || p.prop === 'car') prop.rotation.y = (p.yaw ?? 0) + (p.prop === 'car' ? 0.6 : 0);
      if (p.prop === 'ringbox') for (const gl of prop.userData.glints) { const k = Math.max(0, Math.sin(t * 5.3 + gl.userData.phase)); gl.material.opacity = k * k; gl.scale.setScalar(0.05 + 0.12 * k); gl.material.rotation = t * 0.8 + gl.userData.phase; }
      if (p.prop === 'ringbox') { prop.userData.lid.rotation.x = lerp(-0.05, -1.9, ease.outBack(clamp((lt - 0.1) / 0.6))); prop.rotation.y = (p.yaw ?? -0.25) + lt * 0.12; }
      const base = p.prop === 'ringbox' ? 1.25 : 1;
      const s = p.prop === 'text3d' ? lerp(0.5, 1, intro) : 1;
      prop.scale.setScalar(base * s * (p.scale ?? 1));
    }
    this.confetti.visible = !!p.confetti;
    if (p.confetti) this.confetti.userData.update(lt + (p.confettiOffset ?? 1.2));
    if (p.prop === 'phone') {
      this.phoneSlot = this.phoneSlot || { tex: this.phoneTex };
      this.paint(this.phoneSlot, () => drawPhone(this.phoneCanvas.getContext('2d'), 720, 1470, p.phone || {}, lt, this.images), p.phone || {}, lt, 2.2);
    }

    // Mur LED + totems.
    const wallSpec = { ...(p.wall || { kind: 'logo', title: 'ACTU', subtitle: 'INFLUENCEURS' }), portrait: true };
    this.wallSlot = this.wallSlot || { tex: this.wallTex };
    this.paint(this.wallSlot, () => drawWall(this.wallCanvas.getContext('2d'), 1920, 1080, wallSpec, lt, this.images), wallSpec, lt);
    this.wallLight.color.set(WALL_TINT[wallSpec.kind] || 0xffffff);
    this.totems.forEach((tm, i) => {
      const spec = (p.totems && p.totems[i]) || { kind: 'logo', title: 'ACTU', subtitle: '' };
      this.paint(tm, () => drawWall(tm.canvas.getContext('2d'), 540, 960, spec, lt, this.images), spec, lt);
    });

    // Ambiance lumineuse.
    const accent = new THREE.Color(p.accent || '#ffd60a');
    for (const b of this.bars) b.material.emissive.copy(accent);
    this.podium.userData.ledMat.emissive.copy(accent);
    const mood = p.mood || 'gold';
    if (mood === 'alert') { this.rimL.color.set(0xff2020); this.rimR.color.set(0xff6a1f); }
    else if (mood === 'cool') { this.rimL.color.set(0x3d7bff); this.rimR.color.set(0x19e3ff); }
    else { this.rimL.color.set(0x4d7bff); this.rimR.color.set(0xff3d7f); }
    const flick = 0.92 + 0.08 * Math.sin(t * 3.1) * Math.sin(t * 1.7);
    this.beams.forEach((b, i) => { b.material.uniforms.uIntensity.value = (i === 2 ? 0.06 : 0.09) * flick; });

    const arr = this.dust.geometry.attributes.position.array;
    for (let i = 0; i < arr.length / 3; i++) {
      const s0 = this.dustSeed[i * 3], s1 = this.dustSeed[i * 3 + 1], s2 = this.dustSeed[i * 3 + 2];
      arr[i * 3] = this.dustBase[i * 3] + Math.sin(t * (0.15 + s0 * 0.2) + s1 * 6.28) * 0.25;
      arr[i * 3 + 1] = ((this.dustBase[i * 3 + 1] + t * (0.03 + s2 * 0.05)) % 6);
      arr[i * 3 + 2] = this.dustBase[i * 3 + 2] + Math.cos(t * (0.12 + s1 * 0.2) + s0 * 6.28) * 0.25;
    }
    this.dust.geometry.attributes.position.needsUpdate = true;
  }

  beforeRender(renderer) {
    this.floor.update(renderer, this.scene, this.camera);
  }
}
