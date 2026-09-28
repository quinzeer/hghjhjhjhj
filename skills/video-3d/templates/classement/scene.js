// Modèle « classement » : podiums numérotés, chaque élément tombe sur le sien quand son rang est annoncé,
// le n°1 au centre sous un projecteur avec confettis. Données : story.items rangés du dernier au premier ; beats "rank".

export function build(K, T, story) {
  const { THREE, scene } = K;
  K.cyclorama({ color: 0x151a2c });
  const n = story.items.length, order = story.items.map((_, i) => n - i); // rang de chaque item
  const xs = order.map((r) => (r === 1 ? 0 : (r % 2 ? 1 : -1) * Math.ceil((r - 1) / 2) * 1.6));
  const items = story.items.map((it, i) => {
    const r = order[i], h = 0.25 + (n - r + 1) * 0.18;
    const g = new THREE.Group(); g.position.x = xs[i]; scene.add(g);
    const ped = new THREE.Mesh(new K.RoundedBoxGeometry(1.2, h, 1.2, 3, 0.04), K.mat.glossy(0x10131d)); ped.position.y = h / 2; ped.castShadow = ped.receiveShadow = true; g.add(ped);
    const num = K.text(String(r), { height: h * 0.7, color: '#ffe11a', lit: false }); num.position.set(0, h / 2, 0.61); g.add(num);
    const geo = it.shape === 'box' ? new K.RoundedBoxGeometry(0.6, 0.6, 0.6, 3, 0.05) : it.shape === 'cylinder' ? new THREE.CylinderGeometry(0.3, 0.3, 0.6, 48) : new THREE.SphereGeometry(0.33, 64, 48);
    const obj = new THREE.Mesh(geo, r === 1 ? K.mat.gold() : K.mat.glossy(new THREE.Color(it.color))); obj.castShadow = true; g.add(obj);
    const label = K.text(`${it.name}${it.value && it.value !== '…' ? ' · ' + it.value : ''}`, { height: 0.16 }); label.position.set(0, h + 0.7, 0); g.add(label);
    const beats = T.beats.filter((b) => b.rank === r && b.id !== 'hook');
    return { g, obj, label, h, r, t0: beats.length ? beats[0].v0 : Infinity };
  });
  const spot = new THREE.SpotLight(0xfff2cc, 0, 0, 0.35, 0.5, 2); spot.position.set(0, 6, 1.5); spot.target.position.set(0, 0.6, 0); scene.add(spot, spot.target);
  const confetti = K.confetti({ origin: [0, 3, 0] });
  return { items, spot, confetti };
}

export function update(K, v, T, S) {
  for (const o of S.items) {
    const t = v - o.t0, k = K.clamp(t / 0.6, 0, 1);
    const hookShow = o.r === 1 && v < T.beats[1].v0;
    const drop = hookShow ? 0 : (1 - K.bounce(k)) * 3;
    o.obj.visible = hookShow || t > -0.05;
    o.obj.position.y = o.h + 0.33 + drop;
    o.obj.rotation.y = v * 0.7;
    o.label.visible = o.obj.visible && (hookShow || t > 0.4);
    o.label.quaternion.copy(K.camera.quaternion);
  }
  const one = S.items.find((o) => o.r === 1);
  S.spot.intensity = v >= one.t0 ? 220 : 0;
  S.confetti.userData.update(v - one.t0 - 0.2);
}

export function camera(K, v, T, S) {
  const b = T.beatAt(v), o = S.items.find((x) => x.r === b.rank) || S.items[0];
  const view = (bb) => { const oo = S.items.find((x) => x.r === bb.rank) || S.items[0]; const p = oo.g.position; return K.orbit([p.x, oo.h * 0.6 + 0.35, 0], 0.25, 0.3, 4.4, 34, [p.x, oo.h + 0.4, 0]); };
  const prev = T.beats[b.i - 1];
  const cam = prev ? K.mixCam(view(prev), view(b), (v - b.v0) / 0.7) : view(b);
  if (b.drop && v - b.v0 < 0.5) cam.shake = 0.03;
  return cam;
}
