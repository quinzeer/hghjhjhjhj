// Caméra virtuelle « opérateur humain » : keyframes + tremblement organique + secousses d'impact
// + transitions (whip pan, zoom punch). Fonction pure du temps → rendu reproductible.
import * as THREE from 'three';
import { keyframes, fbm1D, impulse, ease, clamp, lerp } from './util.js';

export function makeCameraPath(spec = {}, seed = 7) {
  const nx = fbm1D(seed), ny = fbm1D(seed + 11), nz = fbm1D(seed + 23), nr = fbm1D(seed + 37), ny2 = fbm1D(seed + 51);
  const shake = spec.shake ?? 0.35;        // amplitude du tremblement « à l'épaule »
  const freq = spec.shakeFreq ?? 0.55;     // Hz approximatif
  return function at(lt, ctx = {}) {
    const pos = keyframes(spec.pos, lt) || [0, 1.6, 6];
    const target = keyframes(spec.target, lt) || [0, 1.2, 0];
    let fov = keyframes(spec.fov, lt) ?? 32;
    let roll = keyframes(spec.roll, lt) ?? 0;
    const s = shake * 0.018;
    const p = [pos[0] + nx(lt * freq) * s, pos[1] + ny(lt * freq * 1.1) * s, pos[2] + nz(lt * freq * 0.8) * s * 0.6];
    const tg = [target[0] + ny2(lt * freq * 0.9) * s * 0.7, target[1] + nx(lt * freq * 0.7 + 3) * s * 0.7, target[2]];
    roll += nr(lt * freq * 0.6) * shake * 0.35 * Math.PI / 180;

    // Secousses d'impact (synchronisées aux « booms » de la bande son).
    let kick = 0;
    for (const imp of ctx.impacts || []) kick += impulse(lt, imp.t, imp.decay ?? 9, 0.7) * (imp.amp ?? 1);
    if (kick > 0) {
      const hf = Math.sin(lt * 78.0) * 0.6 + Math.sin(lt * 51.0 + 1.3) * 0.4;
      p[1] += hf * kick * 0.025;
      p[0] += Math.sin(lt * 63.0 + 0.7) * kick * 0.02;
      roll += hf * kick * 0.9 * Math.PI / 180;
      fov *= 1 - kick * 0.02;
    }
    return { pos: p, target: tg, fov, roll };
  };
}

const _v = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _axisY = new THREE.Vector3(0, 1, 0);

// Applique un état caméra + décalages de transition (yaw rapide, zoom).
export function applyCamera(cam, st, trans = {}) {
  cam.position.fromArray(st.pos);
  cam.up.set(0, 1, 0);
  cam.lookAt(_v.fromArray(st.target));
  if (trans.yaw) { _q.setFromAxisAngle(_axisY, trans.yaw); cam.quaternion.premultiply(_q); }
  if (trans.pitch) cam.rotateX(trans.pitch);
  cam.rotateZ(st.roll || 0);
  cam.fov = st.fov * (trans.zoom || 1);
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld();
}

// Décalages de transition autour d'une coupe : `k` ∈ [0,1] = intensité (1 au moment de la coupe).
export function transitionOffsets(kind, side, k) {
  // side = -1 : fin du plan sortant, +1 : début du plan entrant.
  if (k <= 0) return {};
  switch (kind) {
    case 'whip': {
      const dir = side < 0 ? 1 : -1;
      return { yaw: dir * ease.inCubic(k) * 0.55 };
    }
    case 'whipUp': return { pitch: (side < 0 ? 1 : -1) * ease.inCubic(k) * 0.45 };
    case 'zoom': return { zoom: side < 0 ? 1 - 0.45 * ease.inCubic(k) : 1 + 0.5 * ease.inCubic(k) };
    default: return {};
  }
}

// Projette un point monde en coordonnées UV écran (pour flou de mouvement et annotations).
export function projectUV(cam, p) {
  _v.fromArray(p).project(cam);
  return [(_v.x + 1) / 2, (_v.y + 1) / 2, _v.z];
}
