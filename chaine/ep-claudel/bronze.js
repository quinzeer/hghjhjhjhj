const RES = 160, SUB = 30, SCALE = 0.85;
// Sculpture stylisée « L'Âge mûr » (bronze), géométrie organique partagée par toutes les copies.
// ---------- le bronze : surface organique continue (proportions réelles 85 × 61,5 × 37,5 cm) ----------
let BRONZE_GEO = null;
export function bronzeGeometry(K) {
  if (BRONZE_GEO) return BRONZE_GEO;
  const c = (pts, r0, r1) => K.chain(pts, r0 * SCALE, r1 * SCALE, 2.2);
  const balls = [
    // socle rocheux irrégulier (bosses aléatoires dans une ellipse)
    ...(() => { const R = K.rng(11), out = []; for (let i = 0; i < 70; i++) { const a = R() * Math.PI * 2, d = Math.sqrt(R()); const x = Math.cos(a) * d * 0.4, z = Math.sin(a) * d * 0.15; out.push({ p: [x, 0.015 + R() * 0.03 * (1 - d * 0.6), z], r: (0.035 + R() * 0.035) * (1.1 - d * 0.35) }); } return out; })(),
    // la jeune femme agenouillée, bras tendus vers l'homme
    ...c([[-0.45, 0.06, 0.035], [-0.34, 0.07, 0.035], [-0.335, 0.2, 0.012]], 0.026, 0.034),
    ...c([[-0.45, 0.06, -0.035], [-0.34, 0.07, -0.035], [-0.335, 0.2, -0.012]], 0.026, 0.034),
    ...c([[-0.335, 0.2, 0], [-0.3, 0.29, 0], [-0.255, 0.36, 0]], 0.048, 0.04),
    ...c([[-0.25, 0.38, 0], [-0.225, 0.41, 0]], 0.019, 0.019),
    { p: [-0.215, 0.435, 0], r: 0.037 * SCALE }, { p: [-0.245, 0.45, 0], r: 0.024 * SCALE },
    ...c([[-0.265, 0.36, 0.04], [-0.19, 0.4, 0.035], [-0.115, 0.43, 0.015]], 0.02, 0.013),
    ...c([[-0.265, 0.36, -0.04], [-0.19, 0.395, -0.03], [-0.12, 0.425, -0.012]], 0.02, 0.013),
    // l'homme qui s'éloigne, une main tendue en arrière
    ...c([[-0.01, 0.05, 0.04], [0.03, 0.18, 0.03], [0.06, 0.3, 0.02]], 0.026, 0.036),
    ...c([[0.15, 0.05, -0.04], [0.11, 0.18, -0.03], [0.08, 0.3, -0.02]], 0.026, 0.036),
    ...c([[0.07, 0.3, 0], [0.1, 0.42, 0], [0.125, 0.5, 0]], 0.052, 0.05),
    ...c([[0.135, 0.52, 0], [0.145, 0.545, 0]], 0.022, 0.022),
    { p: [0.155, 0.575, 0], r: 0.039 * SCALE },
    ...c([[0.1, 0.49, 0.055], [0.03, 0.45, 0.06], [-0.07, 0.425, 0.05]], 0.02, 0.013),
    ...c([[0.15, 0.49, -0.05], [0.2, 0.47, -0.055], [0.235, 0.455, -0.05]], 0.02, 0.015),
    // la vieille femme drapée qui l'entraîne
    ...c([[0.37, 0.05, 0], [0.34, 0.2, 0], [0.29, 0.37, 0], [0.23, 0.46, -0.01]], 0.1, 0.055),
    ...c([[0.39, 0.05, 0.06], [0.36, 0.2, 0.05], [0.3, 0.36, 0.03], [0.24, 0.45, 0.0]], 0.08, 0.045),
    ...c([[0.39, 0.05, -0.06], [0.36, 0.2, -0.05], [0.3, 0.36, -0.03], [0.24, 0.45, -0.02]], 0.08, 0.045),
    ...c([[0.42, 0.05, 0.0], [0.4, 0.18, 0.0], [0.35, 0.33, 0.0]], 0.075, 0.05),
    { p: [0.37, 0.06, 0.06], r: 0.065 * SCALE }, { p: [0.37, 0.06, -0.06], r: 0.065 * SCALE }, { p: [0.4, 0.07, 0], r: 0.06 * SCALE },
    { p: [0.205, 0.505, -0.01], r: 0.034 * SCALE },
    ...c([[0.22, 0.46, -0.045], [0.17, 0.5, -0.06], [0.125, 0.51, -0.035]], 0.019, 0.014),
    ...c([[0.43, 0.08, 0.07], [0.41, 0.25, 0.09], [0.35, 0.42, 0.07], [0.27, 0.5, 0.035]], 0.03, 0.018),
  ];
  const mesh = K.blob(balls, { size: 1.0, center: [0, 0.3, 0], resolution: RES, subtract: SUB });
  // patine : couleurs par sommet (reliefs usés plus clairs, creux sombres, touches de vert-de-gris)
  const g = mesh.geometry, pos = g.attributes.position, nor = g.attributes.normal, col = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i), up = nor.getY(i);
    const n = K.noise(x * 23 + z * 17) * 0.5 + K.noise(y * 31 - x * 7) * 0.5;
    let r = 0.42, gg = 0.27, b = 0.15;
    const wear = Math.max(0, up) * 0.35 + n * 0.12;
    r += wear * 0.45; gg += wear * 0.3; b += wear * 0.15;
    if (n < -0.35) { r *= 0.75; gg *= 0.9; b *= 0.85; }
    col.set([r, gg, b], i * 3);
  }
  g.setAttribute('color', new K.THREE.BufferAttribute(col, 3));
  BRONZE_GEO = g;
  return g;
}
export function bronze(K, M) {
  const m = new K.THREE.Mesh(bronzeGeometry(K), M);
  m.castShadow = m.receiveShadow = true;
  const g = new K.THREE.Group(); g.add(m); return g;
}

