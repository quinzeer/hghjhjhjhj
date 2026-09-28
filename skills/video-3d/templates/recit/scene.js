// Modèle « récit » : l'histoire avance de tableau en tableau (stations alignées), la caméra voyage de l'un à l'autre.
// Pour une nouvelle histoire : garder la mécanique, remplacer les fabriques d'objets PROPS et story.json.
// Chaque beat de story.json porte "station": n (index dans PROPS).

const GAP = 7; // distance entre deux stations (m)

// ---------- fabriques d'objets (procédurales : aucun fichier externe) ----------
const PROPS = [
  // 0 · trombone rouge
  (K) => {
    const { THREE } = K;
    const pts = [[-0.35, 0.5], [0.35, 0.5], [0.35, -0.55], [-0.25, -0.55], [-0.25, 0.35], [0.2, 0.35], [0.2, -0.35]].map(([x, y]) => new THREE.Vector3(x, y, 0));
    const path = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.05);
    const m = new THREE.Mesh(new THREE.TubeGeometry(path, 200, 0.035, 16), K.mat.glossy(0xd81e2c, { roughness: 0.2 }));
    m.scale.setScalar(0.9); m.rotation.z = 0.2; return m;
  },
  // 1 · stylo-poisson
  (K) => {
    const { THREE } = K, g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.12, 0.7, 8, 24), K.mat.glossy(0x2f8fdd));
    body.rotation.z = Math.PI / 2; g.add(body);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.3, 3), K.mat.glossy(0xffb400)); tail.position.x = -0.6; tail.rotation.z = -Math.PI / 2; g.add(tail);
    const tip = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.18, 16), K.mat.metal()); tip.position.x = 0.58; tip.rotation.z = -Math.PI / 2; g.add(tip);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 8), K.mat.glossy(0x111111)); eye.position.set(0.3, 0.05, 0.11); g.add(eye);
    return g;
  },
  // 2 · poignée de porte en laiton
  (K) => {
    const { THREE } = K, g = new THREE.Group();
    const knob = new THREE.Mesh(new THREE.SphereGeometry(0.28, 48, 32), K.mat.gold({ roughness: 0.3 })); knob.scale.y = 0.8; knob.position.y = 0.2; g.add(knob);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 0.35, 32), K.mat.gold({ roughness: 0.35 })); stem.position.y = -0.15; g.add(stem);
    const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.05, 48), K.mat.gold({ roughness: 0.4 })); plate.position.y = -0.33; g.add(plate);
    return g;
  },
  // 3 · boule à neige
  (K) => {
    const { THREE } = K, g = new THREE.Group();
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.4, 0.22, 48), K.mat.glossy(0x3a1d12, { roughness: 0.35 })); base.position.y = -0.3; g.add(base);
    const glass = new THREE.Mesh(new THREE.SphereGeometry(0.42, 64, 48), K.mat.glass(0xeef6ff, { thickness: 0.2, roughness: 0.03 })); glass.position.y = 0.12; g.add(glass);
    const inner = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.34, 6), K.mat.matte(0x1f6b3a)); inner.position.y = 0.02; g.add(inner);
    return g;
  },
  // 4 · la maison
  (K) => {
    const { THREE } = K, g = new THREE.Group();
    const walls = new THREE.Mesh(new K.RoundedBoxGeometry(1.1, 0.7, 0.8, 3, 0.03), K.mat.matte(0xf1e6d3)); walls.position.y = 0.35; g.add(walls);
    const roof = new THREE.Mesh(new THREE.CylinderGeometry(0, 0.8, 0.45, 4, 1), K.mat.matte(0x8e2f25, { roughness: 0.7 })); roof.position.y = 0.93; roof.rotation.y = Math.PI / 4; roof.scale.set(1, 1, 0.75); g.add(roof);
    const door = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.32, 0.02), K.mat.glossy(0x3b2a20)); door.position.set(0, 0.16, 0.41); g.add(door);
    for (const x of [-0.33, 0.33]) { const w = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.16, 0.02), K.mat.emissive(0xffc26b, 1.6)); w.position.set(x, 0.42, 0.41); g.add(w); }
    g.position.y = -0.35; const outer = new THREE.Group(); outer.add(g); return outer;
  },
];

export function build(K, T, story) {
  const { THREE, scene } = K;
  K.cyclorama({ color: 0x2a3150, width: 90, depth: 30 });
  const dust = K.dust({ n: 1200, radius: 20, height: 5 });
  const stations = PROPS.map((make, i) => {
    const g = new THREE.Group(); g.position.set(i * GAP, 0, 0); scene.add(g);
    const ped = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.95, 0.3, 64), K.mat.glossy(0x0e1018, { roughness: 0.3 }));
    ped.position.y = 0.15; ped.castShadow = ped.receiveShadow = true; g.add(ped);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.92, 0.012, 8, 96), K.mat.emissive(0x39d5ff, 4)); ring.rotation.x = Math.PI / 2; ring.position.y = 0.3; g.add(ring);
    const sh = K.contactShadow(0.7, 0.6); sh.position.y = 0.302; g.add(sh);
    const prop = K.shadows(make(K)); prop.position.y = 1.0; g.add(prop);
    const first = T.beats.find((b) => b.station === i);
    return { g, prop, sh, ring, t0: first ? first.v0 : Infinity };
  });
  const confetti = K.confetti({ origin: [(PROPS.length - 1) * GAP, 2.6, 0] });
  return { stations, dust, confetti };
}

export function update(K, v, T, S) {
  S.dust.userData.update(v);
  for (const st of S.stations) {
    const k = K.easeOutBack((v - st.t0 + 0.2) / 0.6);
    const s = Math.max(0.0001, k);
    st.prop.scale.setScalar(s);
    st.prop.position.y = 1.0 + (1 - K.easeOut((v - st.t0 + 0.2) / 0.6)) * 1.5 + Math.sin(v * 1.3) * 0.03;
    st.prop.rotation.y = v * 0.45;
    st.sh.material.opacity = 0.6 * K.clamp(k, 0, 1);
  }
  const last = T.beats[T.beats.length - 1];
  S.confetti.userData.update(v - last.v0 - 0.3);
}

export function camera(K, v, T) {
  const view = (b, vv) => {
    const x = (b.station ?? 0) * GAP, k = K.clamp((vv - b.v0) / b.dur, 0, 1);
    return K.orbit([x, 0.85, 0], -0.35 + k * 0.35, 0.26 - k * 0.06, 5.6 - k * 1.0, 34, [x, 1.0, 0]);
  };
  const b = T.beatAt(v), prev = T.beats[b.i - 1];
  let cam = view(b, v);
  if (prev && prev.station !== b.station) cam = K.mixCam(view(prev, v), cam, (v - b.v0) / 0.8);
  cam.aperture = 0.004;
  if (b.drop && v - b.v0 < 0.5) cam.shake = 0.03 * (1 - (v - b.v0) / 0.5);
  return cam;
}
