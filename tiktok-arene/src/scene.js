// Rendu three.js « plateau de jeu télé » : PBR, éclairage de studio, ombres, faisceaux volumétriques,
// profondeur de champ, bloom, grain argentique. Le rendu est une fonction pure du temps vidéo v.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { P, PHASE, STATE, sampleAt, tileFallTime, effRadius } from './sim.js';
import { COUNTRIES, ballTexture } from './countries.js';
import { floorTextures, scratchTexture, hazardTexture, blobTexture, dotTexture } from './textures.js';

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
function hash(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function vnoise(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; }

// Solide en secteur d'anneau : surface haute yTop(ρ), basse yBot(ρ). Groupes : 0 = dessus, 1 = côtés/dessous.
function sectorSolid(r0, r1, a0, a1, yTop, yBot, segR = 2, segA = 8, uvPlanar = true) {
  const pos = [], uv = [], idx = [], groups = [];
  let base = 0;
  const face = (fn, nu, nv, group, flip) => {
    const start = idx.length;
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) { const p = fn(i / nu, j / nv); pos.push(p[0], p[1], p[2]); uv.push(p[3], p[4]); }
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) {
      const a = base + j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1;
      if (flip) idx.push(a, b, c, b, d, c); else idx.push(a, c, b, b, c, d);
    }
    groups.push([start, idx.length - start, group]);
    base += (nu + 1) * (nv + 1);
  };
  const P2 = (rho, a, y) => [rho * Math.cos(a), y, rho * Math.sin(a)];
  const U = (x, z) => (uvPlanar ? [x / (2 * P.R0) + 0.5, 1 - (z / (2 * P.R0) + 0.5)] : [0, 0]);
  // orientation : (i = angle, j = rayon) → dessus « flip », normales vers l'extérieur du solide
  face((u, w) => { const rho = lerp(r0, r1, w), a = lerp(a0, a1, u), p = P2(rho, a, yTop(rho)); return [...p, ...U(p[0], p[2])]; }, segA, segR, 0, true);
  face((u, w) => { const rho = lerp(r0, r1, w), a = lerp(a0, a1, u), p = P2(rho, a, yBot(rho)); return [...p, u, w]; }, segA, segR, 1, false);
  face((u, w) => { const a = lerp(a0, a1, u), p = P2(r1, a, lerp(yBot(r1), yTop(r1), w)); return [...p, u, w]; }, segA, 1, 1, false);
  if (r0 > 0.001) face((u, w) => { const a = lerp(a0, a1, u), p = P2(r0, a, lerp(yBot(r0), yTop(r0), w)); return [...p, u, w]; }, segA, 1, 1, true);
  if (a1 - a0 < Math.PI * 1.99) {
    face((u, w) => { const rho = lerp(r0, r1, u), p = P2(rho, a0, lerp(yBot(rho), yTop(rho), w)); return [...p, u, w]; }, segR, 1, 1, false);
    face((u, w) => { const rho = lerp(r0, r1, u), p = P2(rho, a1, lerp(yBot(rho), yTop(rho), w)); return [...p, u, w]; }, segR, 1, 1, true);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  for (const [s, c, m] of groups) g.addGroup(s, c, m);
  g.computeVertexNormals();
  return g;
}

const GradeShader = {
  uniforms: {
    tDiffuse: { value: null }, uTime: { value: 0 }, uFlash: { value: 0 }, uRed: { value: 0 }, uBars: { value: 0 },
    uReplay: { value: 0 }, uRes: { value: new THREE.Vector2(1080, 1920) }, uGrain: { value: 0.03 },
  },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uTime, uFlash, uRed, uBars, uReplay, uGrain; uniform vec2 uRes; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    void main(){
      vec2 c = vUv - 0.5; float r2 = dot(c,c);
      vec2 off = c * r2 * 0.012;
      vec3 col = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
      float l = dot(col, vec3(0.299,0.587,0.114));
      col = mix(vec3(l), col, 1.12 - 0.45*uReplay);                 // saturation (désaturé en replay)
      col = (col - 0.5) * 1.05 + 0.5;                                // contraste
      col *= mix(vec3(1.0), vec3(1.04,0.98,0.9), uReplay);           // teinte chaude du replay
      col *= 1.0 - smoothstep(0.18, 0.72, r2) * 0.55;                // vignettage
      col = mix(col, vec3(1.0,0.08,0.05), uRed * smoothstep(0.08, 0.5, r2) * 0.55);
      float g = h(floor(vUv*uRes) + fract(uTime*7.13)*97.0) - 0.5;
      col += g * uGrain * (0.6 + 0.8*l*(1.0-l));                      // grain argentique
      col = mix(col, vec3(1.0), uFlash);
      float bar = 0.085 * uBars;
      if (vUv.y < bar || vUv.y > 1.0 - bar) col = vec3(0.0);
      gl_FragColor = vec4(clamp(col,0.0,1.0), 1.0);
    }`,
};

const beamVS = `varying vec3 vN; varying vec3 vV; varying float vH; varying vec3 vW;
  uniform float uH;
  void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vW = wp.xyz; vN = normalize(mat3(modelMatrix)*normal); vV = normalize(cameraPosition - wp.xyz); vH = position.y/uH + 0.5; gl_Position = projectionMatrix*viewMatrix*wp; }`;
const beamFS = `uniform vec3 uColor; uniform float uInt; uniform float uTime; varying vec3 vN; varying vec3 vV; varying float vH; varying vec3 vW;
  void main(){ float f = abs(dot(normalize(vN), normalize(vV))); float edge = pow(f, 2.2);
    float along = pow(clamp(vH,0.0,1.0), 1.4);
    float n = 0.72 + 0.28*sin(vW.x*2.7+uTime*0.6)*sin(vW.z*2.1-uTime*0.45)*sin(vW.y*1.7+uTime*0.3);
    gl_FragColor = vec4(uColor * uInt * edge * along * n, 1.0); }`;

export class Arena {
  constructor(canvas, D, opts = {}) {
    this.D = D; this.rec = D.rec;
    this.W = opts.width || 1080; this.H = opts.height || 1920;
    this.PW = opts.projW || this.W; this.PH = opts.projH || this.H; // repère de l'habillage
    this.q = opts.quality || 'high';
    const hi = this.q === 'high';
    const r = (this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: true, alpha: false }));
    r.setPixelRatio(1);
    r.setSize(this.W, this.H, false);
    r.outputColorSpace = THREE.SRGBColorSpace;
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = 1.0;
    r.shadowMap.enabled = true;
    r.shadowMap.type = THREE.PCFSoftShadowMap;

    const scene = (this.scene = new THREE.Scene());
    scene.background = new THREE.Color(0x05060a);
    scene.fog = new THREE.FogExp2(0x070912, 0.04);
    this.camera = new THREE.PerspectiveCamera(48, this.W / this.H, 0.05, 80);

    this.buildEnvironment();
    this.buildLights(hi);
    this.buildPlatform();
    this.buildBalls();
    this.buildStage();
    this.buildConfetti();
    this.buildPost(hi);
  }

  // ---------- environnement (réflexions) : studio sombre avec softbox et bandes LED ----------
  buildEnvironment() {
    const env = new THREE.Scene();
    env.background = new THREE.Color(0x020203);
    const box = new THREE.Mesh(new THREE.BoxGeometry(30, 14, 30), new THREE.MeshBasicMaterial({ color: 0x050608, side: THREE.BackSide }));
    env.add(box);
    const panel = (w, h, col, int, p, rx) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).multiplyScalar(int), side: THREE.DoubleSide })); m.position.set(...p); m.rotation.x = rx; env.add(m); };
    panel(6, 6, 0xfff4e6, 3.2, [0, 6.8, 0], Math.PI / 2);        // softbox au-dessus
    for (let i = 0; i < 8; i++) {                                   // bandes LED colorées tout autour
      const a = (i / 8) * Math.PI * 2, col = i % 2 ? 0x2f6bff : 0xff2d8a;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).multiplyScalar(4), side: THREE.DoubleSide }));
      m.position.set(Math.cos(a) * 12, 3, Math.sin(a) * 12); m.lookAt(0, 3, 0); env.add(m);
    }
    for (let i = 0; i < 16; i++) {                                  // projecteurs ponctuels (reflets nets)
      const a = (i / 16) * Math.PI * 2;
      const m = new THREE.Mesh(new THREE.SphereGeometry(0.25, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffffff).multiplyScalar(8) }));
      m.position.set(Math.cos(a) * 9, 6 + (i % 2), Math.sin(a) * 9); env.add(m);
    }
    const pm = new THREE.PMREMGenerator(this.renderer);
    this.envTex = pm.fromScene(env, 0.03).texture;
    this.scene.environment = this.envTex;
    this.scene.environmentIntensity = 0.6;
    pm.dispose();
  }

  buildLights(hi) {
    const s = this.scene;
    const key = (this.key = new THREE.SpotLight(0xfff0dc, 170, 0, 0.46, 0.55, 2));
    key.position.set(0.8, 7.2, 1.6); key.target.position.set(0, 0, 0);
    key.castShadow = true;
    key.shadow.mapSize.set(hi ? 2048 : 1024, hi ? 2048 : 1024);
    key.shadow.bias = -0.0002; key.shadow.normalBias = 0.015;
    key.shadow.camera.near = 4; key.shadow.camera.far = 11;
    s.add(key, key.target);
    const rim1 = new THREE.SpotLight(0x3d6bff, 110, 0, 0.55, 0.8, 2); rim1.position.set(-4.5, 3.2, -3.5); rim1.target.position.set(0, 0, 0); s.add(rim1, rim1.target);
    const rim2 = new THREE.SpotLight(0xff2d8a, 95, 0, 0.55, 0.8, 2); rim2.position.set(4.5, 3.0, -3.2); rim2.target.position.set(0, 0, 0); s.add(rim2, rim2.target);
    const front = new THREE.SpotLight(0xdfe8ff, 28, 0, 0.6, 0.9, 2); front.position.set(0, 2.5, 6); front.target.position.set(0, 0, 0); s.add(front, front.target);
    s.add(new THREE.HemisphereLight(0x223047, 0x000000, 0.25));
    this.under = new THREE.PointLight(0xff2a14, 9, 9, 2); this.under.position.set(0, -2.4, 0); s.add(this.under);
    this.beacon = new THREE.PointLight(0xff1a1a, 0, 3.5, 2); this.beacon.position.set(0, 0.62, 0); s.add(this.beacon);
  }

  // ---------- plateau : disque central, 6 anneaux de 24 dalles, barrières, moyeu, bras ----------
  buildPlatform() {
    const plat = (this.plat = new THREE.Group());
    this.scene.add(plat);
    const ft = floorTextures(2048);
    const tex = (cv, srgb) => { const t = new THREE.CanvasTexture(cv); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; return t; };
    this.floorMat = new THREE.MeshPhysicalMaterial({
      map: tex(ft.col, true), roughnessMap: tex(ft.rough, false), roughness: 0.72, metalness: 0.02,
      clearcoat: 0.22, clearcoatRoughness: 0.45, envMapIntensity: 0.55, emissiveMap: tex(ft.emi, true), emissive: new THREE.Color(1, 1, 1), emissiveIntensity: 1.6,
    });
    this.warnMat = this.floorMat.clone(); this.warnMat.emissive = new THREE.Color(1, 0.1, 0.05); this.warnMat.emissiveMap = null; this.warnMat.emissiveIntensity = 0;
    const metal = (this.metalMat = new THREE.MeshStandardMaterial({ color: 0x2a2e36, metalness: 0.85, roughness: 0.38 }));
    const yTop = (rho) => P.k * rho * rho, yBot = (rho) => P.k * rho * rho - 0.11;
    const inner = P.R0 - P.rings * P.ringW;
    const disc = new THREE.Mesh(sectorSolid(0.0, inner, 0, Math.PI * 2, yTop, yBot, 16, 128), [this.floorMat, metal]);
    disc.castShadow = false; disc.receiveShadow = true; plat.add(disc);
    this.tiles = [];
    const gap = 0.002;
    for (let k = 0; k < P.rings; k++) {
      const r1 = P.R0 - k * P.ringW, r0 = r1 - P.ringW;
      for (let j = 0; j < P.tilesPerRing; j++) {
        const a0 = (j / P.tilesPerRing) * Math.PI * 2, a1 = ((j + 1) / P.tilesPerRing) * Math.PI * 2;
        const g = sectorSolid(r0 + gap, r1 - gap, a0 + gap / r1, a1 - gap / r1, yTop, yBot, 2, 6);
        const m = new THREE.Mesh(g, [this.floorMat, metal]);
        m.receiveShadow = true;
        const mid = (a0 + a1) / 2;
        const tFall = tileFallTime(this.rec.rings, k, mid);
        const rr = hash(k * 31 + j);
        m.userData = { k, j, mid, rc: (r0 + r1) / 2, tFall, spin: (0.8 + rr * 1.6) * (rr > 0.5 ? 1 : -1), mats: [this.floorMat, metal], warnMats: [this.warnMat, metal] };
        plat.add(m); this.tiles.push(m);
      }
    }
    // barrières (polycarbonate + liseré LED)
    this.walls = [];
    const wallMat = new THREE.MeshPhysicalMaterial({ color: 0xbfe3ff, metalness: 0, roughness: 0.08, transparent: true, opacity: 0.32, clearcoat: 1, clearcoatRoughness: 0.05, depthWrite: false });
    const base = P.k * (P.R0 - P.wallT / 2) ** 2;
    for (let g = 0; g < P.nGates; g++) {
      const w = (2 * Math.PI) / P.nGates, a0 = g * w + 0.012, a1 = (g + 1) * w - 0.012;
      const grp = new THREE.Group();
      const wall = new THREE.Mesh(sectorSolid(P.R0 - P.wallT, P.R0 - 0.004, a0, a1, () => base + P.wallH, () => base - 0.02, 1, 10, false), wallMat);
      wall.renderOrder = 2;
      const ledMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.6, 0.9, 1).multiplyScalar(3) });
      const led = new THREE.Mesh(sectorSolid(P.R0 - P.wallT - 0.004, P.R0, a0, a1, () => base + P.wallH + 0.012, () => base + P.wallH, 1, 10, false), ledMat);
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, P.wallH + 0.05, 12), metal);
      post.position.set(Math.cos(a0 - 0.006) * (P.R0 - P.wallT / 2), base + (P.wallH + 0.05) / 2 - 0.02, Math.sin(a0 - 0.006) * (P.R0 - P.wallT / 2));
      post.castShadow = true;
      grp.add(wall, led, post);
      plat.add(grp);
      this.walls.push({ grp, led, ledMat, post });
    }
    // moyeu central + gyrophare
    const hz = hazardTexture(512, 64); const hzT = new THREE.CanvasTexture(hz); hzT.colorSpace = THREE.SRGBColorSpace; hzT.wrapS = THREE.RepeatWrapping; hzT.repeat.set(2, 1);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(P.hubR, P.hubR * 1.08, P.hubH, 48), [new THREE.MeshPhysicalMaterial({ map: hzT, metalness: 0.2, roughness: 0.45, clearcoat: 0.8 }), metal, metal]);
    hub.position.y = P.hubH / 2 - 0.01; hub.castShadow = true; hub.receiveShadow = true; plat.add(hub);
    this.beaconMat = new THREE.MeshStandardMaterial({ color: 0x551111, emissive: new THREE.Color(1, 0.05, 0.03), emissiveIntensity: 0.3, roughness: 0.2, transparent: true, opacity: 0.92 });
    const dome = new THREE.Mesh(new THREE.SphereGeometry(0.075, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), this.beaconMat);
    dome.position.y = P.hubH; plat.add(dome);
    // bras rotatif télescopique (deux côtés)
    const armT = new THREE.CanvasTexture(hazardTexture(1024, 64)); armT.colorSpace = THREE.SRGBColorSpace; armT.wrapS = THREE.RepeatWrapping; armT.repeat.set(3, 1);
    this.armMat = new THREE.MeshPhysicalMaterial({ map: armT, metalness: 0.35, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.12 });
    this.arm = new THREE.Mesh(new RoundedBoxGeometry(2 * (P.R0 - 0.06), 0.11, 2 * P.armW, 3, 0.03), this.armMat);
    this.arm.position.y = P.r + 0.02; this.arm.castShadow = true; plat.add(this.arm);
    // clôture lumineuse de la finale
    this.fenceMat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uA: { value: 0 }, uT: { value: 0 } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
      fragmentShader: 'uniform float uA,uT; varying vec2 vUv; void main(){ float s = 0.55+0.45*sin(vUv.y*80.0-uT*6.0); float f=(1.0-vUv.y); gl_FragColor=vec4(vec3(0.25,0.8,1.0)*uA*f*f*s*1.6,1.0); }',
    });
    this.fence = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.3, 96, 1, true), this.fenceMat);
    this.fence.visible = false; plat.add(this.fence);
    // pied central qui plonge dans le vide
    const ped = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.55, 14, 48, 1, true), metal);
    ped.position.y = -7.1; plat.add(ped);
    // ombres de contact
    this.blobTex = new THREE.CanvasTexture(blobTexture(128));
  }

  buildBalls() {
    const geo = new THREE.SphereGeometry(P.r, 64, 40);
    const scr = new THREE.CanvasTexture(scratchTexture(512)); scr.colorSpace = THREE.NoColorSpace; scr.wrapS = scr.wrapT = THREE.RepeatWrapping; scr.repeat.set(2, 1);
    this.balls = [];
    this.blobs = [];
    const blobMat = new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: this.blobTex, transparent: true, depthWrite: false, opacity: 0.8 });
    for (let i = 0; i < this.rec.N; i++) {
      const t = new THREE.CanvasTexture(ballTexture(COUNTRIES[i].code, 1024, i + 1));
      t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
      const m = new THREE.MeshPhysicalMaterial({ map: t, roughness: 0.2, roughnessMap: scr, metalness: 0.0, clearcoat: 1, clearcoatRoughness: 0.045, specularIntensity: 0.6 });
      const b = new THREE.Mesh(geo, m);
      b.castShadow = true; b.receiveShadow = true;
      this.scene.add(b); this.balls.push(b);
      const blob = new THREE.Mesh(new THREE.PlaneGeometry(P.r * 4.2, P.r * 4.2), blobMat.clone());
      blob.rotation.x = -Math.PI / 2; blob.renderOrder = 1;
      this.plat.add(blob); this.blobs.push(blob);
    }
  }

  // ---------- décor : portique, projecteurs, faisceaux, public, lumières lointaines ----------
  buildStage() {
    const s = this.scene;
    const truss = new THREE.MeshStandardMaterial({ color: 0x1b1d22, metalness: 0.9, roughness: 0.45 });
    const Y = 6.3, L = 5.4;
    for (let i = 0; i < 4; i++) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(L + 0.3, 0.28, 0.28), truss);
      const a = (i * Math.PI) / 2;
      b.position.set(Math.cos(a) * L / 2, Y, Math.sin(a) * L / 2); b.rotation.y = a + Math.PI / 2; s.add(b);
      const led = new THREE.Mesh(new THREE.BoxGeometry(L, 0.03, 0.03), new THREE.MeshBasicMaterial({ color: new THREE.Color(i % 2 ? 0x3d6bff : 0xff2d8a).multiplyScalar(3) }));
      led.position.set(Math.cos(a) * (L / 2 - 0.16), Y - 0.16, Math.sin(a) * (L / 2 - 0.16)); led.rotation.y = a + Math.PI / 2; s.add(led);
    }
    this.beams = [];
    const cols = [0xfff1d8, 0x9fb8ff, 0xfff1d8, 0xff7ab8, 0xfff1d8, 0x9fb8ff, 0xfff1d8, 0xff7ab8];
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2 + Math.PI / 8;
      const lp = new THREE.Vector3(Math.cos(a) * 2.5, Y - 0.2, Math.sin(a) * 2.5);
      const tp = new THREE.Vector3(Math.cos(a + 2.2) * 0.7, 0, Math.sin(a + 2.2) * 0.7);
      const can = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.1, 0.3, 16), truss);
      can.position.copy(lp); can.lookAt(tp); can.rotateX(Math.PI / 2); s.add(can);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.1, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(cols[i]).multiplyScalar(6) }));
      lens.position.copy(lp).add(tp.clone().sub(lp).normalize().multiplyScalar(0.16)); lens.lookAt(tp); s.add(lens);
      const len = lp.distanceTo(tp) + 0.3;
      const mat = new THREE.ShaderMaterial({ vertexShader: beamVS, fragmentShader: beamFS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
        uniforms: { uColor: { value: new THREE.Color(cols[i]) }, uInt: { value: 0.085 }, uTime: { value: 0 }, uH: { value: len } } });
      const cone = new THREE.Mesh(new THREE.ConeGeometry(0.85, len, 40, 1, true), mat);
      cone.position.copy(lp.clone().add(tp).multiplyScalar(0.5));
      cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), lp.clone().sub(tp).normalize());
      s.add(cone); this.beams.push(cone);
    }
    // public : milliers de téléphones allumés dans les gradins sombres
    const n = 2600, pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const a = hash(i * 3.1) * Math.PI * 2, rr = 13 + hash(i * 7.7) * 8, y = -1.5 + (rr - 13) * 0.75 + hash(i * 1.3) * 1.2;
      pos.set([Math.cos(a) * rr, y, Math.sin(a) * rr], i * 3);
      const w = hash(i * 9.1); col.set(w < 0.7 ? [0.9, 0.95, 1] : w < 0.85 ? [1, 0.8, 0.55] : [0.6, 0.75, 1], i * 3);
    }
    const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pos, 3)); pg.setAttribute('color', new THREE.BufferAttribute(col, 3));
    this.crowdCol = col; this.crowdBase = col.slice();
    this.crowd = new THREE.Points(pg, new THREE.PointsMaterial({ size: 0.11, map: new THREE.CanvasTexture(dotTexture(64)), vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true, fog: false }));
    s.add(this.crowd);
    // rampes de projecteurs lointaines (bokeh en profondeur de champ)
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * Math.PI * 2;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.5), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffffff).multiplyScalar(2.5), fog: false }));
      m.position.set(Math.cos(a) * 24, 9, Math.sin(a) * 24); m.lookAt(0, 0, 0); s.add(m);
    }
    // lueur rouge du vide sous le plateau
    const glow = new THREE.Mesh(new THREE.CircleGeometry(7, 48), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(dotTexture(128)), color: new THREE.Color(1, 0.12, 0.05).multiplyScalar(0.16), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    glow.rotation.x = -Math.PI / 2; glow.position.y = -9; s.add(glow);
    // poussière dans les faisceaux
    const dn = 1400, dp = new Float32Array(dn * 3);
    for (let i = 0; i < dn; i++) { const a = hash(i * 2.3) * Math.PI * 2, rr = Math.sqrt(hash(i * 5.9)) * 3.2; dp.set([Math.cos(a) * rr, 0.3 + hash(i * 4.1) * 5.5, Math.sin(a) * rr], i * 3); }
    const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dp, 3));
    this.dustBase = dp.slice();
    this.dust = new THREE.Points(dg, new THREE.PointsMaterial({ size: 0.012, color: 0xfff3e0, map: new THREE.CanvasTexture(dotTexture(32)), transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending }));
    s.add(this.dust);
  }

  buildConfetti() {
    const n = 520;
    const g = new THREE.PlaneGeometry(0.034, 0.02);
    const m = new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, metalness: 0.6, roughness: 0.3, emissive: 0x111111 });
    this.confetti = new THREE.InstancedMesh(g, m, n);
    const W = COUNTRIES[this.rec.winner];
    const palette = [0xffd24a, 0xffffff, 0xffc21a, 0xff3355, 0x39d5ff];
    const c = new THREE.Color();
    this.cf = [];
    for (let i = 0; i < n; i++) {
      c.set(palette[i % palette.length]); this.confetti.setColorAt(i, c);
      const burst = i < n * 0.45 ? 0 : 1;
      const a = hash(i * 1.7) * Math.PI * 2, cannon = Math.floor(hash(i * 3.3) * 4);
      const ca = (cannon / 4) * Math.PI * 2 + Math.PI / 4;
      this.cf.push({
        burst, p0: burst ? [Math.cos(ca) * 1.9, 0.1, Math.sin(ca) * 1.9] : [(hash(i) - 0.5) * 3, 3.2 + hash(i * 2) * 1.5, (hash(i * 3) - 0.5) * 3],
        v0: burst ? [-Math.cos(ca) * (1.2 + hash(i * 4) * 1.5) + Math.cos(a) * 0.6, 4.5 + hash(i * 5) * 2.5, -Math.sin(ca) * (1.2 + hash(i * 4) * 1.5) + Math.sin(a) * 0.6] : [Math.cos(a) * 0.3, -0.2, Math.sin(a) * 0.3],
        spin: [hash(i * 6) * 12, hash(i * 7) * 12, hash(i * 8) * 12], ph: hash(i * 9) * 6.28,
      });
    }
    this.confetti.instanceColor.needsUpdate = true;
    this.confetti.visible = false;
    this.confetti.frustumCulled = false;
    this.scene.add(this.confetti);
    this._m4 = new THREE.Matrix4(); this._q = new THREE.Quaternion(); this._e = new THREE.Euler(); this._s = new THREE.Vector3(1, 1, 1); this._p = new THREE.Vector3();
  }

  buildPost(hi) {
    const rt = new THREE.WebGLRenderTarget(this.W, this.H, { type: THREE.HalfFloatType, samples: hi ? 2 : 0 });
    const comp = (this.composer = new EffectComposer(this.renderer, rt));
    comp.setPixelRatio(1); comp.setSize(this.W, this.H);
    comp.addPass(new RenderPass(this.scene, this.camera));
    this.bokeh = new BokehPass(this.scene, this.camera, { focus: 4, aperture: 0.002, maxblur: 0.006 });
    this.bokeh.enabled = hi;
    comp.addPass(this.bokeh);
    this.bloom = new UnrealBloomPass(new THREE.Vector2(this.W / 2, this.H / 2), 0.45, 0.5, 1.0);
    comp.addPass(this.bloom);
    comp.addPass(new OutputPass());
    this.grade = new ShaderPass(GradeShader);
    this.grade.uniforms.uRes.value.set(this.W, this.H);
    comp.addPass(this.grade);
  }

  // ---------- état à l'instant v ----------
  renderAt(v) {
    const D = this.D, rec = this.rec;
    const { s, g } = D.simAt(v);
    const { A: fa, B: fb, a } = sampleAt(rec, s);
    // plateau
    const qa = new THREE.Quaternion(...fa.Qp), qb = new THREE.Quaternion(...fb.Qp);
    const Qp = qa.slerp(qb, a);
    this.plat.quaternion.copy(Qp);
    const Qinv = Qp.clone().invert();
    const armA = lerp(fa.armA, fb.armA, a), armExt = lerp(fa.armExt, fb.armExt, a);
    this.arm.visible = armExt > 0.01;
    this.arm.rotation.y = -armA;
    this.arm.scale.x = 0.12 + 0.88 * armExt;
    const phase = fa.phase;
    const armOn = phase >= PHASE.R2 && phase < PHASE.WIN;
    this.beaconMat.emissiveIntensity = armOn ? 1.5 + 1.3 * Math.max(0, Math.sin(v * 9)) : 0.25;
    this.beacon.intensity = armOn ? 2.5 * Math.max(0, Math.sin(v * 9)) : 0;
    // barrières
    for (let k = 0; k < P.nGates; k++) {
      const gv = fa.gates[k];
      const w = this.walls[k];
      const open = gv > 0 ? gv : 0;
      w.grp.position.y = -open * (P.wallH + 0.04);
      w.grp.visible = open < 0.999 || gv === -1;
      const warn = gv === -1 || (open > 0 && open < 1);
      const blink = Math.sin(v * 40) > 0 ? 1 : 0.15;
      if (warn) w.ledMat.color.setRGB(4 * blink, 0.15 * blink, 0.1 * blink);
      else if (open >= 1) w.ledMat.color.setRGB(3.5, 0.1, 0.05);
      else w.ledMat.color.setRGB(1.3, 2.4, 3.2);
    }
    // dalles qui tombent
    for (const t of this.tiles) {
      const u = t.userData;
      const dt = s - u.tFall;
      const warnStart = rec.events.find((e) => e.type === 'ringWarn' && e.k === u.k);
      if (dt > 0) {
        const fall = 0.5 * 9.81 * dt * dt;
        t.visible = fall < 9;
        const ang = dt * u.spin;
        t.position.set(Math.cos(u.mid) * dt * 0.25, -fall, Math.sin(u.mid) * dt * 0.25);
        t.setRotationFromAxisAngle(new THREE.Vector3(-Math.sin(u.mid), 0, Math.cos(u.mid)), ang * 0.6);
        t.material = u.mats;
      } else {
        t.visible = true; t.position.set(0, 0, 0); t.rotation.set(0, 0, 0);
        const w = warnStart && s >= warnStart.t;
        if (w) { t.material = u.warnMats; } else t.material = u.mats;
      }
    }
    if (rec.events.some((e) => e.type === 'ringWarn' && s >= e.t && s < e.at + e.dur)) this.warnMat.emissiveIntensity = Math.sin(v * 30) > 0 ? 2.2 : 0.3;
    // clôture lumineuse (mise en place de la finale)
    const tF = D.A.tFinal;
    const fenceA = s >= tF && s < tF + P.finalSetup ? Math.min(1, (s - tF) / 0.3, (tF + P.finalSetup - s) / 0.3) : 0;
    this.fence.visible = fenceA > 0.01 && g.kind === 'live';
    if (this.fence.visible) {
      let Re = P.R0; for (let q = 0; q < 8; q++) Re = Math.min(Re, effRadius(rec.rings, (q / 8) * Math.PI * 2, s));
      this.fence.scale.set(Re, 1, Re); this.fence.position.y = P.k * Re * Re + 0.15;
      this.fenceMat.uniforms.uA.value = fenceA; this.fenceMat.uniforms.uT.value = v;
    }
    // billes
    const qA = new THREE.Quaternion(), qB = new THREE.Quaternion();
    const over = D.winnerOverride(v);
    for (let i = 0; i < rec.N; i++) {
      const b = this.balls[i], blob = this.blobs[i];
      const px = lerp(fa.pos[i * 3], fb.pos[i * 3], a), py = lerp(fa.pos[i * 3 + 1], fb.pos[i * 3 + 1], a), pz = lerp(fa.pos[i * 3 + 2], fb.pos[i * 3 + 2], a);
      qA.fromArray(fa.rot, i * 4); qB.fromArray(fb.rot, i * 4);
      b.quaternion.copy(qA).slerp(qB, a);
      b.position.set(px, py, pz);
      if (over && i === rec.winner) {
        b.position.set(...over.pos);
        b.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), over.spin));
      }
      b.visible = py > -9;
      const st = fa.st[i];
      // ombre de contact dans le repère du plateau
      const lp = b.position.clone().applyQuaternion(Qinv);
      const rho2 = lp.x * lp.x + lp.z * lp.z;
      const ys = P.k * rho2;
      const hgt = lp.y - P.r - ys;
      const onDisc = Math.sqrt(rho2) < P.R0 + 0.1 && st !== STATE.FALL && hgt > -0.05;
      blob.visible = onDisc && hgt < 1.2;
      if (blob.visible) {
        blob.position.set(lp.x, ys + 0.004, lp.z);
        const sc = 1 + hgt * 1.2;
        blob.scale.set(sc, sc, sc);
        blob.material.opacity = clamp(0.85 - hgt * 1.1, 0, 0.85);
      }
    }
    // faisceaux, public, poussière
    for (const c of this.beams) c.material.uniforms.uTime.value = v;
    for (let i = 0; i < this.crowdCol.length / 3; i++) {
      const tw = 0.55 + 0.45 * Math.max(0, Math.sin(v * (1.5 + hash(i) * 3) + hash(i * 2) * 20));
      this.crowdCol[i * 3] = this.crowdBase[i * 3] * tw; this.crowdCol[i * 3 + 1] = this.crowdBase[i * 3 + 1] * tw; this.crowdCol[i * 3 + 2] = this.crowdBase[i * 3 + 2] * tw;
    }
    this.crowd.geometry.attributes.color.needsUpdate = true;
    const dp = this.dust.geometry.attributes.position;
    for (let i = 0; i < dp.count; i++) {
      dp.array[i * 3] = this.dustBase[i * 3] + Math.sin(v * 0.21 + i) * 0.12;
      dp.array[i * 3 + 1] = this.dustBase[i * 3 + 1] + ((v * 0.05 + hash(i)) % 1) * 0.3;
      dp.array[i * 3 + 2] = this.dustBase[i * 3 + 2] + Math.cos(v * 0.17 + i * 1.3) * 0.12;
    }
    dp.needsUpdate = true;
    // confettis
    const tc0 = D.hud.vWin + 0.05, tc1 = D.hud.vCel0;
    this.confetti.visible = v >= tc0 && g.kind !== 'replay';
    if (this.confetti.visible) {
      for (let i = 0; i < this.cf.length; i++) {
        const c = this.cf[i];
        const t0 = c.burst ? tc0 : tc1;
        const tau = v - t0;
        if (tau < 0) { this._m4.makeScale(0, 0, 0); this.confetti.setMatrixAt(i, this._m4); continue; }
        const k = 1.6, dr = (1 - Math.exp(-k * tau)) / k;
        this._p.set(c.p0[0] + c.v0[0] * dr + Math.sin(tau * 3 + c.ph) * 0.08, c.p0[1] + c.v0[1] * dr - 0.75 * tau, c.p0[2] + c.v0[2] * dr + Math.cos(tau * 2.6 + c.ph) * 0.08);
        this._e.set(c.spin[0] * tau, c.spin[1] * tau, c.spin[2] * tau);
        this._q.setFromEuler(this._e);
        this._m4.compose(this._p, this._q, this._s);
        this.confetti.setMatrixAt(i, this._m4);
      }
      this.confetti.instanceMatrix.needsUpdate = true;
    }
    // caméra
    const cam = D.camAt(v);
    const sh = cam.shake;
    const n1 = (o) => vnoise(v * 1.7 + o) * 0.6 + vnoise(v * 6.3 + o * 2) * 0.4;
    this.camera.position.set(cam.eye[0] + n1(1) * sh * 4, cam.eye[1] + n1(2) * sh * 4, cam.eye[2] + n1(3) * sh * 4);
    this.camera.lookAt(cam.tgt[0] + n1(4) * sh, cam.tgt[1] + n1(5) * sh, cam.tgt[2] + n1(6) * sh);
    this.camera.rotateZ(n1(7) * sh * 0.8);
    this.camera.fov = cam.fov;
    // l'arène est décalée vers le bas de l'image : le haut reste libre pour la grille des drapeaux
    this.camera.setViewOffset(this.W, this.H, 0, -0.05 * this.H, this.W, this.H);
    this.camera.updateProjectionMatrix();
    // profondeur de champ
    if (this.q === 'high') {
      const f = cam.focus;
      const u = this.bokeh.uniforms;
      this.bokeh.enabled = !!f;
      if (f) {
        const d = this.camera.position.distanceTo(new THREE.Vector3(...f));
        u.focus.value = d; u.aperture.value = cam.type === 'winner' ? 0.006 : cam.type === 'kill' || cam.type === 'replay' ? 0.0045 : 0.003; u.maxblur.value = 0.009;
      } else {
        u.focus.value = this.camera.position.length(); u.aperture.value = 0.0011; u.maxblur.value = 0.005;
      }
    }
    // étalonnage & effets d'écran
    const G = this.grade.uniforms;
    G.uTime.value = v;
    let flash = 0;
    for (const t of [D.hud.vR2, D.hud.vR3, D.hud.vFin, D.hud.vWin]) if (t !== null && v >= t && v < t + 0.35) flash = Math.max(flash, 0.32 * (1 - (v - t) / 0.35));
    if (v >= D.hud.vReplay0 && v < D.hud.vReplay0 + 0.2) flash = Math.max(flash, 0.8 * (1 - (v - D.hud.vReplay0) / 0.2));
    if (v >= D.hud.vCel0 && v < D.hud.vCel0 + 0.3) flash = Math.max(flash, 0.7 * (1 - (v - D.hud.vCel0) / 0.3));
    G.uFlash.value = flash;
    const inReplay = g.kind === 'replay';
    G.uReplay.value = inReplay ? 1 : 0;
    G.uBars.value = inReplay ? 1 : 0;
    let red = 0;
    for (const e of D.hud.toasts) if (v >= e.v && v < e.v + 0.5) red = Math.max(red, 0.5 * (1 - (v - e.v) / 0.5));
    if (s > tF + P.finalSetup && s < D.A.tWin && g.kind === 'live') red = Math.max(red, 0.18 + 0.12 * Math.sin(v * 7.5));
    G.uRed.value = red;
    this.under.intensity = 9 + 14 * red;
    this.composer.render();
  }

  // projection écran (pixels) d'un point monde, pour l'interface
  project(p) {
    const vec = new THREE.Vector3(p[0], p[1], p[2]).project(this.camera);
    return { x: (vec.x * 0.5 + 0.5) * this.PW, y: (-vec.y * 0.5 + 0.5) * this.PH, z: vec.z };
  }
  ballScreen(i) { const b = this.balls[i]; return this.project([b.position.x, b.position.y, b.position.z]); }
}
