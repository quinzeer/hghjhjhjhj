// Environnement « studio photo produit » procédural : fond noir + boîtes à lumière HDR.
// Donne des reflets nets et contrastés sur le métal, le verre et l'or (look keynote / pub).
import * as THREE from 'three';

export function makeSoftboxEnv(renderer, { warm = 1.0, accentA = 0xff2d7a, accentB = 0x19c8ff } = {}) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x020203);
  const add = (w, h, pos, look, color, power) => {
    const c = new THREE.Color(color).multiplyScalar(power);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: c, side: THREE.DoubleSide }));
    m.position.set(...pos);
    m.lookAt(...look);
    scene.add(m);
  };
  // Grande boîte à lumière zénithale (légèrement chaude).
  add(6, 3, [0, 6, 1], [0, 0, 0], new THREE.Color(1, 0.96 * warm, 0.9 * warm), 9);
  // Strip lights latéraux (hauts et étroits : reflets verticaux élégants).
  add(0.7, 5, [-5, 2.5, 1.5], [0, 1.5, 0], 0xffffff, 7);
  add(0.7, 5, [5, 2.5, 1.5], [0, 1.5, 0], 0xffffff, 6);
  // Contre-jour arrière + accents néon colorés (bords des objets).
  add(4, 1.2, [0, 3, -6], [0, 1, 0], 0xfff3e0, 4);
  add(0.5, 4, [-4, 2, -4], [0, 1, 0], accentA, 3.5);
  add(0.5, 4, [4, 2, -4], [0, 1, 0], accentB, 3.5);
  // Grande source frontale derrière la caméra (faces avant du métal et de l'or lumineuses).
  add(9, 6, [0, 0.6, 7.5], [0, 0.6, 0], new THREE.Color(1, 0.93 * warm, 0.84 * warm), 2.4);
  add(1.2, 3, [2.6, 1.6, 6], [0, 1, 0], 0xffffff, 5);
  // Rebond de sol très faible.
  add(10, 10, [0, -2, 0], [0, 0, 0], 0x202028, 0.4);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(scene, 0.0, 0.1, 100);
  pmrem.dispose();
  return rt.texture;
}
