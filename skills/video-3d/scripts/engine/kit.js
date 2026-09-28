// Kit three.js « qualité tournage » : ambiances de lumière, IBL, post-traitement (DOF, bloom, étalonnage, grain),
// matériaux PBR prêts à l'emploi, cyclorama de studio, textes 3D, particules, caméra avec bougé.
// Une scène (scene.js) reçoit ce kit dans build/update/camera et n'a plus qu'à poser ses objets.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { MarchingCubes } from 'three/addons/objects/MarchingCubes.js';

export { THREE, RoundedBoxGeometry };

// ---------- maths & temps ----------
export const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
export const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
export const easeIn = (t) => Math.pow(clamp(t, 0, 1), 3);
export const easeInOut = (t) => { t = clamp(t, 0, 1); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOutBack = (t) => { t = clamp(t, 0, 1); const c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
export const bounce = (t) => { t = clamp(t, 0, 1); const n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375; return n * (t -= 2.625 / d) * t + 0.984375; };
export function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const h1 = (n) => { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); };
export const noise = (x) => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(h1(i), h1(i + 1), u) * 2 - 1; };

// ---------- ambiances ----------
// Chaque ambiance règle fond, brouillard, IBL, lumières, exposition, bloom et étalonnage.
export const LOOKS = {
  studio: { bg: 0x0b0d14, fog: [0x0b0d14, 0.028], env: 'studio', envI: 0.65, key: [0xfff0dc, 170, [0.8, 7.2, 3.2]], rims: [[0x3d6bff, 90, [-4.5, 3.2, -3.5]], [0xff2d8a, 80, [4.5, 3.0, -3.2]]], hemi: [0x223047, 0x000000, 0.3], exposure: 1.0, bloom: [0.45, 0.5, 1.0], floor: 0x1a1d27, grade: { sat: 1.12, warm: 0 } },
  day: { bg: 0xbfd3ea, fog: [0xbfd3ea, 0.02], env: 'sky', envI: 0.9, sun: [0xfff4e0, 3.2, [6, 10, 5]], hemi: [0xbfd9ff, 0x6b5b45, 0.8], exposure: 1.0, bloom: [0.2, 0.4, 1.2], floor: 0xd9d4cc, grade: { sat: 1.08, warm: 0.02 } },
  sunset: { bg: 0x2a1530, fog: [0x3a1c2a, 0.03], env: 'sunset', envI: 0.8, sun: [0xffa060, 2.6, [-8, 3, -4]], rims: [[0x7a4dff, 60, [5, 3, 4]]], hemi: [0xff9d6b, 0x2a1530, 0.5], exposure: 1.05, bloom: [0.5, 0.6, 0.95], floor: 0x3a2630, grade: { sat: 1.15, warm: 0.06 } },
  night: { bg: 0x05070f, fog: [0x070a16, 0.04], env: 'night', envI: 0.5, key: [0xb8c8ff, 120, [-3, 7, 2]], rims: [[0x00e5ff, 90, [-4, 2.5, -4]], [0xff2d8a, 90, [4, 2.5, -4]]], hemi: [0x1a2240, 0x000000, 0.25], exposure: 1.0, bloom: [0.45, 0.5, 1.0], floor: 0x10131d, grade: { sat: 1.1, warm: -0.04 } },
  space: { bg: 0x000000, fog: null, env: 'space', envI: 0.25, sun: [0xffffff, 3.5, [10, 3, 6]], hemi: [0x10131d, 0x000000, 0.08], exposure: 1.05, bloom: [0.55, 0.6, 0.9], floor: null, grade: { sat: 1.08, warm: 0 }, stars: true },
  dark: { bg: 0x030305, fog: [0x040406, 0.05], env: 'studio', envI: 0.3, key: [0xffe2c0, 140, [1.5, 6.5, 2.5]], rims: [[0x4466aa, 40, [-4, 2, -4]]], hemi: [0x111418, 0x000000, 0.15], exposure: 0.95, bloom: [0.4, 0.5, 1.0], floor: 0x0d0e11, grade: { sat: 0.95, warm: 0.03 } },
};

function envScene(kind) {
  const env = new THREE.Scene();
  const col = (c, i) => new THREE.Color(c).multiplyScalar(i);
  const room = (c) => env.add(new THREE.Mesh(new THREE.BoxGeometry(30, 14, 30), new THREE.MeshBasicMaterial({ color: c, side: THREE.BackSide })));
  const panel = (w, h, c, i, p, look = [0, 0, 0]) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: col(c, i), side: THREE.DoubleSide })); m.position.set(...p); m.lookAt(...look); env.add(m); };
  if (kind === 'sky' || kind === 'sunset') {
    const top = kind === 'sky' ? 0x8fb8ff : 0x5b3a8a, mid = kind === 'sky' ? 0xe8f1ff : 0xff9a5a, bot = kind === 'sky' ? 0x6b6358 : 0x2a1a24;
    const g = new THREE.SphereGeometry(20, 32, 16), c = [];
    for (let i = 0; i < g.attributes.position.count; i++) { const y = g.attributes.position.getY(i) / 20; const cc = new THREE.Color(y > 0 ? mid : bot).lerp(new THREE.Color(y > 0 ? top : bot), Math.abs(y)); c.push(cc.r, cc.g, cc.b); }
    g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
    env.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
    panel(4, 4, kind === 'sky' ? 0xffffff : 0xffb070, kind === 'sky' ? 12 : 8, kind === 'sky' ? [8, 12, 6] : [-14, 3, -6]);
    return env;
  }
  room(kind === 'space' ? 0x000000 : 0x040509);
  if (kind === 'space') { panel(3, 3, 0xffffff, 10, [12, 4, 8]); return env; }
  panel(6, 6, 0xfff4e6, kind === 'night' ? 1.2 : 3.2, [0, 6.8, 0], [0, 0, 0]);
  for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; panel(0.5, 4, i % 2 ? 0x2f6bff : 0xff2d8a, kind === 'night' ? 5 : 3.5, [Math.cos(a) * 12, 3, Math.sin(a) * 12], [0, 3, 0]); }
  for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; const m = new THREE.Mesh(new THREE.SphereGeometry(0.25, 12, 8), new THREE.MeshBasicMaterial({ color: col(0xffffff, 8) })); m.position.set(Math.cos(a) * 9, 6 + (i % 2), Math.sin(a) * 9); env.add(m); }
  return env;
}

const GradeShader = {
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uFlash: { value: 0 }, uTint: { value: new THREE.Vector4(0, 0, 0, 0) }, uBars: { value: 0 }, uSat: { value: 1.1 }, uWarm: { value: 0 }, uRes: { value: new THREE.Vector2(1080, 1920) }, uGrain: { value: 0.03 }, uVig: { value: 0.55 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime,uFlash,uBars,uSat,uWarm,uGrain,uVig; uniform vec4 uTint; uniform vec2 uRes; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    void main(){ vec2 c = vUv - 0.5; float r2 = dot(c,c); vec2 off = c * r2 * 0.012;
      vec3 col = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
      float l = dot(col, vec3(0.299,0.587,0.114));
      col = mix(vec3(l), col, uSat); col = (col - 0.5) * 1.05 + 0.5; col *= vec3(1.0 + uWarm, 1.0, 1.0 - uWarm);
      col *= 1.0 - smoothstep(0.18, 0.72, r2) * uVig;
      col = mix(col, uTint.rgb, uTint.a * smoothstep(0.05, 0.5, r2));
      col += (h(floor(vUv*uRes) + fract(uTime*7.13)*97.0) - 0.5) * uGrain * (0.6 + 0.8*l*(1.0-l));
      col = mix(col, vec3(1.0), uFlash);
      float bar = 0.085 * uBars; if (vUv.y < bar || vUv.y > 1.0 - bar) col = vec3(0.0);
      gl_FragColor = vec4(clamp(col,0.0,1.0), 1.0); }`,
};

// ---------- création du kit ----------
export function createKit(canvas, { width = 1080, height = 1920, look = 'studio', quality = 'high', projW = 1080, projH = 1920 } = {}) {
  const L = LOOKS[look] || LOOKS.studio;
  const hi = quality === 'high';
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(width, height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = L.exposure;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(L.bg);
  if (L.fog) scene.fog = new THREE.FogExp2(L.fog[0], L.fog[1]);
  const camera = new THREE.PerspectiveCamera(40, width / height, 0.05, 400);

  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(envScene(L.env), 0.03).texture;
  scene.environmentIntensity = L.envI;

  const lights = {};
  if (L.key) { const k = new THREE.SpotLight(L.key[0], L.key[1], 0, 0.5, 0.55, 2); k.position.set(...L.key[2]); k.castShadow = true; k.shadow.mapSize.set(hi ? 2048 : 1024, hi ? 2048 : 1024); k.shadow.bias = -0.0002; k.shadow.normalBias = 0.015; scene.add(k, k.target); lights.key = k; }
  if (L.sun) { const s = new THREE.DirectionalLight(L.sun[0], L.sun[1]); s.position.set(...L.sun[2]); s.castShadow = true; s.shadow.mapSize.set(hi ? 2048 : 1024, hi ? 2048 : 1024); const sc = s.shadow.camera; sc.left = sc.bottom = -8; sc.right = sc.top = 8; sc.near = 0.5; sc.far = 40; s.shadow.bias = -0.0003; s.shadow.normalBias = 0.02; scene.add(s, s.target); lights.sun = s; }
  lights.rims = (L.rims || []).map(([c, i, p]) => { const r = new THREE.SpotLight(c, i, 0, 0.6, 0.8, 2); r.position.set(...p); scene.add(r, r.target); return r; });
  if (L.hemi) scene.add((lights.hemi = new THREE.HemisphereLight(...L.hemi)));
  if (L.stars) {
    const n = 4000, p = new Float32Array(n * 3), R = rng(9);
    for (let i = 0; i < n; i++) { const u = R() * 2 - 1, a = R() * Math.PI * 2, s = Math.sqrt(1 - u * u); p.set([s * Math.cos(a) * 180, u * 180, s * Math.sin(a) * 180], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 0.6, sizeAttenuation: true, fog: false })));
  }

  // post-traitement
  const rt = new THREE.WebGLRenderTarget(width, height, { type: THREE.HalfFloatType, samples: hi ? 2 : 0 });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1); composer.setSize(width, height);
  composer.addPass(new RenderPass(scene, camera));
  const bokeh = new BokehPass(scene, camera, { focus: 5, aperture: 0.002, maxblur: 0.008 });
  bokeh.enabled = false; composer.addPass(bokeh);
  const bloom = new UnrealBloomPass(new THREE.Vector2(width / 2, height / 2), ...L.bloom);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const grade = new ShaderPass(GradeShader);
  grade.uniforms.uRes.value.set(width, height); grade.uniforms.uSat.value = L.grade.sat; grade.uniforms.uWarm.value = L.grade.warm;
  composer.addPass(grade);

  const K = {
    THREE, renderer, scene, camera, composer, bloom, bokeh, grade: grade.uniforms, lights, look: L, W: width, H: height, hi,
    clamp, lerp, ease, easeOut, easeIn, easeInOut, easeOutBack, bounce, rng, noise, RoundedBoxGeometry,
    // --- matériaux PBR ---
    mat: {
      glossy: (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.06, ...o }),
      matte: (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0, ...o }),
      metal: (color = 0xb8bcc6, o = {}) => new THREE.MeshStandardMaterial({ color, metalness: 1, roughness: 0.28, ...o }),
      gold: (o = {}) => new THREE.MeshPhysicalMaterial({ color: 0xffc657, metalness: 1, roughness: 0.2, clearcoat: 0.5, ...o }),
      chrome: (o = {}) => new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 1, roughness: 0.05, ...o }),
      glass: (tint = 0xffffff, o = {}) => new THREE.MeshPhysicalMaterial({ color: tint, metalness: 0, roughness: 0.02, transmission: 1, thickness: 0.4, ior: 1.5, ...o }),
      plastic: (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.4, clearcoat: 0.3, ...o }),
      emissive: (color, intensity = 3, o = {}) => new THREE.MeshStandardMaterial({ color: 0x000000, emissive: color, emissiveIntensity: intensity, ...o }),
      textured: (tex, o = {}) => new THREE.MeshPhysicalMaterial({ map: tex, roughness: 0.35, clearcoat: 0.4, ...o }),
    },
    // texture dessinée en Canvas 2D (étiquettes, écrans, affiches, cartes, drapeaux…)
    canvasTex(w, h, draw, srgb = true) {
      const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
      const t = new THREE.CanvasTexture(c); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; return t;
    },
    // texte posé dans la scène (plan texturé) ; height = hauteur en mètres ; lit = éclairé par la scène
    text(str, { height = 0.4, font = 'Anton', weight = '', color = '#ffffff', stroke = '#000000', strokeW = 0.12, bg = null, pad = 0.25, lit = false, glow = 0 } = {}) {
      const px = 256, c0 = document.createElement('canvas').getContext('2d');
      c0.font = `${weight} ${px}px "${font}", sans-serif`;
      const tw = Math.ceil(c0.measureText(str).width + px * (pad * 2 + strokeW)), th = Math.ceil(px * 1.35);
      const tex = K.canvasTex(tw, th, (c) => {
        c.font = `${weight} ${px}px "${font}", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle';
        if (bg) { c.fillStyle = bg; const r = th * 0.2; c.beginPath(); c.roundRect(0, 0, tw, th, r); c.fill(); }
        if (stroke && strokeW) { c.lineJoin = 'round'; c.lineWidth = px * strokeW; c.strokeStyle = stroke; c.strokeText(str, tw / 2, th / 2); }
        c.fillStyle = color; c.fillText(str, tw / 2, th / 2);
      });
      const m = lit ? new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.6 }) : new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, color: new THREE.Color(1, 1, 1).multiplyScalar(glow ? 1 + glow : 0.84) });
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry((height * tw) / th, height), m);
      mesh.userData.aspect = tw / th;
      return mesh;
    },
    // cyclorama de studio : sol qui se courbe en mur, sans horizon visible (look « shooting produit »)
    cyclorama({ color = L.floor ?? 0x1a1d27, width = 60, depth = 30, radius = 6, height = 20, roughness = 0.6 } = {}) {
      const segX = 2, segS = 64, pos = [], idx = [];
      const prof = []; const fl = depth - radius, arc = (Math.PI / 2) * radius, total = fl + arc + (height - radius);
      for (let j = 0; j <= segS; j++) {
        const s = (j / segS) * total; let z, y;
        if (s < fl) { z = depth / 2 - s; y = 0; } else if (s < fl + arc) { const a = (s - fl) / radius; z = depth / 2 - fl - Math.sin(a) * radius; y = radius - Math.cos(a) * radius; } else { z = depth / 2 - fl - radius; y = radius + (s - fl - arc); }
        prof.push([z, y]);
      }
      for (let j = 0; j <= segS; j++) for (let i = 0; i <= segX; i++) pos.push(-width / 2 + (i / segX) * width, prof[j][1], prof[j][0]);
      for (let j = 0; j < segS; j++) for (let i = 0; i < segX; i++) { const a = j * (segX + 1) + i, b = a + 1, c = a + segX + 1, d = c + 1; idx.push(a, b, c, b, d, c); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
      const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 }));
      m.receiveShadow = true; scene.add(m); return m;
    },
    // sol simple (disque) qui reçoit les ombres
    floor({ color = L.floor ?? 0x1a1d27, size = 40, roughness = 0.55, y = 0 } = {}) {
      const m = new THREE.Mesh(new THREE.CircleGeometry(size, 96), new THREE.MeshStandardMaterial({ color, roughness }));
      m.rotation.x = -Math.PI / 2; m.position.y = y; m.receiveShadow = true; scene.add(m); return m;
    },
    // ombre de contact douce sous un objet
    contactShadow(radius = 0.5, opacity = 0.7) {
      const t = K.canvasTex(128, 128, (c, w) => { const g = c.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = g; c.fillRect(0, 0, w, w); }, false);
      const m = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2, radius * 2), new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: t, transparent: true, opacity, depthWrite: false }));
      m.rotation.x = -Math.PI / 2; m.renderOrder = 1; return m;
    },
    // poussière en suspension (fonction du temps : déterministe)
    dust({ n = 900, radius = 4, height = 4, size = 0.012, color = 0xfff3e0, opacity = 0.5 } = {}) {
      const p = new Float32Array(n * 3), base = new Float32Array(n * 3), R = rng(5);
      for (let i = 0; i < n; i++) { const a = R() * Math.PI * 2, r = Math.sqrt(R()) * radius; base.set([Math.cos(a) * r, R() * height, Math.sin(a) * r], i * 3); }
      p.set(base);
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
      const pts = new THREE.Points(g, new THREE.PointsMaterial({ size, color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending }));
      scene.add(pts);
      pts.userData.update = (v) => { for (let i = 0; i < n; i++) { p[i * 3] = base[i * 3] + Math.sin(v * 0.21 + i) * 0.12; p[i * 3 + 1] = base[i * 3 + 1] + ((v * 0.05 + h1(i)) % 1) * 0.3; p[i * 3 + 2] = base[i * 3 + 2] + Math.cos(v * 0.17 + i * 1.3) * 0.12; } g.attributes.position.needsUpdate = true; };
      return pts;
    },
    // confettis analytiques (position = fonction du temps depuis t0)
    confetti({ n = 400, origin = [0, 2.5, 0], spread = 2.5, colors = [0xffd24a, 0xffffff, 0xff3355, 0x39d5ff] } = {}) {
      const im = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.035, 0.02), new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, metalness: 0.6, roughness: 0.3, emissive: 0x111111 }), n);
      const R = rng(3), P = [], c = new THREE.Color();
      for (let i = 0; i < n; i++) { c.set(colors[i % colors.length]); im.setColorAt(i, c); P.push({ p: [origin[0] + (R() - 0.5) * spread, origin[1] + R(), origin[2] + (R() - 0.5) * spread], v: [(R() - 0.5) * 1.2, 1 + R() * 2, (R() - 0.5) * 1.2], s: [R() * 12, R() * 12, R() * 12], ph: R() * 6.28 }); }
      im.frustumCulled = false; im.visible = false; scene.add(im);
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s1 = new THREE.Vector3(1, 1, 1), pv = new THREE.Vector3();
      im.userData.update = (tau) => {
        im.visible = tau >= 0; if (tau < 0) return;
        for (let i = 0; i < n; i++) { const o = P[i], dr = (1 - Math.exp(-1.6 * tau)) / 1.6; pv.set(o.p[0] + o.v[0] * dr + Math.sin(tau * 3 + o.ph) * 0.08, o.p[1] + o.v[1] * dr - 0.7 * tau, o.p[2] + o.v[2] * dr + Math.cos(tau * 2.6 + o.ph) * 0.08); e.set(o.s[0] * tau, o.s[1] * tau, o.s[2] * tau); q.setFromEuler(e); m4.compose(pv, q, s1); im.setMatrixAt(i, m4); }
        im.instanceMatrix.needsUpdate = true;
      };
      return im;
    },
    // formes organiques (sculpture, animal, personnage stylisé, rocher, nuage) : surface lisse qui fusionne des sphères.
    // balls : [{ p: [x, y, z] en m, r: rayon en m }] ; size : côté du cube de calcul (m) ; center : centre de ce cube.
    blob(balls, { size = 1, center = [0, size / 2, 0], resolution = 90, material = null, subtract = 12 } = {}) {
      const mc = new MarchingCubes(resolution, material || K.mat.glossy(0xcccccc), false, false, 400000);
      mc.isolation = 80; mc.reset();
      for (const b of balls) {
        const u = (b.p[0] - center[0]) / size + 0.5, w = (b.p[1] - center[1]) / size + 0.5, z = (b.p[2] - center[2]) / size + 0.5, rn = b.r / size;
        mc.addBall(u, w, z, rn * rn * (80 + subtract), subtract);
      }
      mc.update();
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(mc.positionArray.slice(0, mc.count * 3), 3));
      g.setAttribute('normal', new THREE.BufferAttribute(mc.normalArray.slice(0, mc.count * 3), 3));
      g.scale(size / 2, size / 2, size / 2); g.translate(...center);
      g.computeBoundingSphere(); g.computeBoundingBox();
      const m = new THREE.Mesh(g, mc.material); m.castShadow = m.receiveShadow = true;
      return m;
    },
    // chaîne de sphères le long d'une courbe (membres, tiges, drapés) ; r0 → r1 du début à la fin
    chain(points, r0, r1 = r0, density = 3) {
      const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
      const L = curve.getLength(), out = [];
      const n = Math.max(2, Math.ceil((L * density) / Math.min(r0, r1)));
      for (let i = 0; i <= n; i++) { const t = i / n, q = curve.getPointAt(t); out.push({ p: [q.x, q.y, q.z], r: lerp(r0, r1, t) }); }
      return out;
    },
    // modèles glTF/GLB (CC0 : Poly Haven, Kenney, Quaternius…) et HDRI d'environnement
    loadGLB: (url) => new Promise((res, rej) => new GLTFLoader().load(url, (g) => { g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); res(g); }, undefined, rej)),
    loadHDRI: (url, asBackground = false) => new Promise((res, rej) => new RGBELoader().load(url, (t) => { t.mapping = THREE.EquirectangularReflectionMapping; scene.environment = t; if (asBackground) scene.background = t; res(t); }, undefined, rej)),
    // ombres portées automatiques sur une hiérarchie
    shadows(obj, cast = true, receive = true) { obj.traverse((o) => { if (o.isMesh) { o.castShadow = cast; o.receiveShadow = receive; } }); return obj; },
    // caméra en orbite autour d'une cible
    orbit(tgt, yaw, pitch, dist, fov = 40, focus = null) {
      const cp = Math.cos(pitch);
      return { eye: [tgt[0] + Math.sin(yaw) * cp * dist, tgt[1] + Math.sin(pitch) * dist, tgt[2] + Math.cos(yaw) * cp * dist], tgt, fov, focus };
    },
    mixCam(a, b, k) { k = ease(k); return { eye: a.eye.map((x, i) => lerp(x, b.eye[i], k)), tgt: a.tgt.map((x, i) => lerp(x, b.tgt[i], k)), fov: lerp(a.fov, b.fov, k), focus: k < 0.5 ? a.focus : b.focus, aperture: lerp(a.aperture ?? 0.002, b.aperture ?? 0.002, k) }; },
  };

  // rendu d'une image à l'instant v avec la caméra c = { eye, tgt, fov, focus, aperture, shake, roll, offsetY }
  K.render = (v, c) => {
    const sh = c.shake ?? 0.003;
    const n = (o) => noise(v * 1.7 + o) * 0.6 + noise(v * 6.3 + o * 2) * 0.4;
    camera.position.set(c.eye[0] + n(1) * sh * 4, c.eye[1] + n(2) * sh * 4, c.eye[2] + n(3) * sh * 4);
    camera.lookAt(c.tgt[0] + n(4) * sh, c.tgt[1] + n(5) * sh, c.tgt[2] + n(6) * sh);
    camera.rotateZ(n(7) * sh * 0.8 + (c.roll || 0));
    camera.fov = c.fov || 40;
    camera.setViewOffset(width, height, 0, -(c.offsetY ?? 0.03) * height, width, height);
    camera.updateProjectionMatrix();
    if (hi && c.focus) {
      bokeh.enabled = true;
      bokeh.uniforms.focus.value = camera.position.distanceTo(new THREE.Vector3(...c.focus));
      bokeh.uniforms.aperture.value = c.aperture ?? 0.003; bokeh.uniforms.maxblur.value = 0.009;
    } else bokeh.enabled = false;
    grade.uniforms.uTime.value = v;
    composer.render();
  };
  // projection d'un point 3D en pixels de l'habillage (1080×1920)
  K.project = (p) => { const q = new THREE.Vector3(...p).project(camera); return { x: (q.x * 0.5 + 0.5) * projW, y: (-q.y * 0.5 + 0.5) * projH, z: q.z }; };
  return K;
}
