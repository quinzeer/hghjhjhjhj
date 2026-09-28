// Modèle « comparaison » : objets alignés du plus petit au plus grand, la caméra se recadre sur chacun
// (distance proportionnelle à sa taille), étiquette nom + valeur sous chaque objet.
// Données : story.items [{ name, value, size (m), color, shape: sphere|box|cylinder }] ; chaque beat porte "item": index.

function shape(K, it) {
  const { THREE } = K, s = it.size;
  const geo = it.shape === 'box' ? new K.RoundedBoxGeometry(s, s, s, 3, s * 0.08) : it.shape === 'cylinder' ? new THREE.CylinderGeometry(s / 2, s / 2, s, 48) : new THREE.SphereGeometry(s / 2, 64, 48);
  const m = new THREE.Mesh(geo, K.mat.glossy(new THREE.Color(it.color)));
  m.position.y = s / 2; m.castShadow = true; return m;
}

export function build(K, T, story) {
  const { scene } = K;
  // tailles relatives : le plus grand objet mesure 1,2 m à l'écran, les proportions sont respectées
  const F = 1.2 / Math.max(...story.items.map((i) => i.size));
  story = { ...story, items: story.items.map((i) => ({ ...i, size: i.size * F })) };
  K.cyclorama({ color: 0x2a3150, width: 80 });
  let x = 0;
  const items = story.items.map((it, i) => {
    const g = new K.THREE.Group(); scene.add(g);
    x += (i ? story.items[i - 1].size / 2 : 0) + it.size / 2 + Math.max(0.05, it.size * 0.6);
    g.position.x = x;
    const obj = shape(K, it); g.add(obj);
    const sh = K.contactShadow(it.size * 0.7, 0.7); sh.position.y = 0.001; g.add(sh);
    const label = K.text(`${it.name} · ${it.value}`, { height: Math.max(0.03, it.size * 0.22) });
    label.position.set(0, it.size * 1.25 + 0.03, 0); g.add(label);
    const first = T.beats.find((b) => b.item === i && b.i > 0);
    return { g, obj, label, it, i, t0: first ? first.v0 : 0 };
  });
  return { items };
}

export function update(K, v, T, S) {
  const hook = T.beats[0];
  for (const o of S.items) {
    const inHook = v < T.beats[1].v0 && hook.item === o.i;
    const k = inHook ? 1 : K.easeOutBack((v - o.t0 + 0.1) / 0.5);
    o.g.scale.setScalar(Math.max(1e-4, k));
    o.obj.rotation.y = v * 0.6;
    o.label.quaternion.copy(K.camera.quaternion);
  }
}

export function camera(K, v, T, S) {
  const view = (b) => { const o = S.items[b.item ?? 0]; const s = o.it.size, x = o.g.position.x; return K.orbit([x, s * 0.7, 0], 0.35, 0.22, s * 4.2 + 0.25, 32, [x, s * 0.5, 0]); };
  const b = T.beatAt(v), prev = T.beats[b.i - 1];
  const cam = prev ? K.mixCam(view(prev), view(b), (v - b.v0) / 0.9) : view(b);
  cam.aperture = 0.004;
  return cam;
}
