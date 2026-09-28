// Chargement et cache des assets : HDRI (éclairage basé image), modèles glTF PBR,
// textures, polices (Canvas2D + géométrie 3D extrudée).
import * as THREE from 'three';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { loadFont3D } from './ttf.js';

export const FONTS = [
  { family: 'Montserrat', file: 'Montserrat-VF.ttf', weight: '100 900' },
  { family: 'Inter', file: 'Inter-VF.ttf', weight: '100 900' },
  { family: 'Anton', file: 'Anton-Regular.ttf' },
  { family: 'Bebas Neue', file: 'BebasNeue-Regular.ttf' },
  { family: 'Luckiest Guy', file: 'LuckiestGuy-Regular.ttf' },
  { family: 'Archivo Black', file: 'ArchivoBlack-Regular.ttf' },
];

export class Assets {
  constructor(renderer, base = '/') {
    this.renderer = renderer;
    this.base = base;
    this.pmrem = null;
    this.cache = new Map();
    this.gltf = new GLTFLoader();
    this.hdr = new HDRLoader();
    this.tex = new THREE.TextureLoader();
  }

  url(p) { return this.base + p; }

  async loadFonts() {
    await Promise.all(FONTS.map(async (f) => {
      const face = new FontFace(f.family, `url(${this.url('assets/fonts/' + f.file)})`, f.weight ? { weight: f.weight } : {});
      await face.load();
      document.fonts.add(face);
    }));
    await document.fonts.ready;
  }

  async once(key, fn) {
    if (!this.cache.has(key)) this.cache.set(key, fn());
    return this.cache.get(key);
  }

  // HDRI → environnement PMREM (réflexions et éclairage physiquement plausibles).
  envMap(name) {
    return this.once('env:' + name, async () => {
      const t = await this.hdr.loadAsync(this.url(`assets/polyhaven/hdri/${name}.hdr`));
      t.mapping = THREE.EquirectangularReflectionMapping;
      this.pmrem = this.pmrem || new THREE.PMREMGenerator(this.renderer);
      const env = this.pmrem.fromEquirectangular(t).texture;
      return { env, raw: t };
    });
  }

  model(name) {
    return this.once('model:' + name, async () => {
      const g = await this.gltf.loadAsync(this.url(`assets/polyhaven/models/${name}/${name}.gltf`));
      g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
      return g.scene;
    });
  }

  // Image optionnelle fournie par l'utilisateur (ex. assets/photos/nasdas.jpg). null si absente.
  async optionalImage(path) {
    if (!path) return null;
    return this.once('img:' + path, async () => {
      try {
        const res = await fetch(this.url(path), { method: 'HEAD' });
        if (!res.ok) return null;
        const t = await this.tex.loadAsync(this.url(path));
        t.colorSpace = THREE.SRGBColorSpace;
        t.anisotropy = 8;
        return t;
      } catch { return null; }
    });
  }

  async optionalHTMLImage(path) {
    if (!path) return null;
    return this.once('himg:' + path, async () => {
      try {
        const res = await fetch(this.url(path), { method: 'HEAD' });
        if (!res.ok) return null;
        const img = new Image();
        img.src = this.url(path);
        await img.decode();
        return img;
      } catch { return null; }
    });
  }

  font3D(file) {
    return this.once('font3d:' + file, () => loadFont3D(this.url('assets/fonts/' + file)));
  }
}
