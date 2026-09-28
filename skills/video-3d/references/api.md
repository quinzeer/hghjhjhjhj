# API du moteur

## Sommaire
1. Cycle de vie d'une scène
2. Timeline `T`
3. Kit `K`
4. Caméra
5. Habillage `o` (overlay)
6. Bruitages et musique
7. Voix
8. Exemple minimal complet

## 1. Cycle de vie

`scene.js` est un module ES importé dans Chromium ; `three` est disponible via `K.THREE`.

| Export | Appel | Rôle |
|---|---|---|
| `build(K, T, story)` | une fois (peut être `async`) | crée les objets, charge les modèles, renvoie un état `S` |
| `update(K, v, T, S)` | à chaque image | place tout pour l'instant `v` (secondes) |
| `camera(K, v, T, S)` | à chaque image | renvoie `{ eye, tgt, fov, focus?, aperture?, shake?, roll?, offsetY? }` |
| `overlay(o, v, T, S, K)` | optionnel | dessin 2D supplémentaire (repère 1080×1920) |
| `sfx(T, story, S)` | optionnel, une fois | événements sonores `[{ v, type, gain, pan, rate }]` |

**Règle d'or** : `update` et `camera` ne dépendent que de `v`. Pas de `+=` d'une image à l'autre, pas de `Math.random()` (utiliser `K.rng(seed)` dans `build`). Le rendu découpe la vidéo en segments rendus en parallèle : un état accumulé casserait la continuité.

## 2. Timeline `T`

| Membre | Description |
|---|---|
| `T.duration` | durée totale (s) |
| `T.beats` | beats avec `v0`, `v1`, `dur`, `voiceV`, `voiceDur`, `words`, `energy`, `i`, et tous les champs de `story.json` |
| `T.beat(id)` / `T.at(id)` | beat par identifiant / son instant de début |
| `T.k(id, v, a=0, b=null)` | progression 0→1 dans le beat ; `a` et `b` en secondes depuis le début (b < 0 : depuis la fin) |
| `T.beatAt(v)` | beat en cours |
| `T.lines`, `T.captions` | répliques et sous-titres calculés |

Motif courant : `const k = K.easeOutBack(T.k('reveal', v, 0, 0.6));` → apparition en 0,6 s au début du beat `reveal`.

## 3. Kit `K`

- **Base** : `K.THREE`, `K.scene`, `K.camera`, `K.renderer`, `K.W`, `K.H`, `K.lights` (`key`, `sun`, `rims`, `hemi`), `K.grade` (uniforms : `uFlash`, `uTint` vec4 rgb+force, `uBars` bandes cinéma 0–1, `uSat`, `uWarm`, `uGrain`, `uVig`).
- **Temps** : `clamp`, `lerp`, `ease`, `easeIn`, `easeOut`, `easeInOut`, `easeOutBack`, `bounce`, `noise(x)` (−1..1), `rng(seed)`.
- **Matériaux** `K.mat` :

  | Fonction | Rendu |
  |---|---|
  | `glossy(c)` | laque, vernis |
  | `matte(c)` | peinture mate, plâtre, carton |
  | `plastic(c)` | plastique |
  | `metal(c)` | métal brossé |
  | `gold()` | or |
  | `chrome()` | chrome miroir |
  | `glass(tint)` | verre avec transmission, plus coûteux |
  | `emissive(c, i)` | LED, écran, fenêtre allumée |
  | `textured(tex)` | texture dessinée |

  Chaque fonction accepte des options three.js en 2e argument.
- **Textures dessinées** : `K.canvasTex(w, h, (ctx, w, h) => { … })`. Elles servent pour les écrans, les affiches, les cartes, les étiquettes et les drapeaux.
- **Texte dans la scène** : `K.text('TEXTE', { height: 0.4, color, stroke, bg, lit, glow })` renvoie un plan. Pour une étiquette qui fait toujours face à la caméra, utiliser `mesh.quaternion.copy(K.camera.quaternion)` dans `update`.
- **Décor** :
  - `K.cyclorama({ color })` : studio sans horizon ;
  - `K.floor({ color, size })` : sol simple ;
  - `K.contactShadow(radius, opacity)` : ombre douce sous un objet ;
  - `K.shadows(obj)` : active les ombres portées sur toute la hiérarchie.
- **Effets** :
  - `K.dust({ n, radius, height })` : poussière, à appeler dans `update` via `S.dust.userData.update(v)` ;
  - `K.confetti({ origin })` : confettis, via `S.confetti.userData.update(v - t0)`.
- **Formes organiques** : `K.blob(balls, { size, center, resolution, material })` fusionne des sphères en une surface lisse (sculpture, animal, personnage stylisé sans visage, rocher, nuage, liquide figé). Pour décrire un membre, un tronc ou un drapé, `K.chain([[x, y, z], …], r0, r1)` renvoie une suite de sphères. Le calcul se fait une seule fois dans `build`, en 1 à 3 s pour une résolution de 90 à 110. Pour des détails nets, monte à 160 avec `subtract: 30`, et mets la géométrie en cache si l'objet apparaît plusieurs fois. Recette complète : `references/avance.md`.
- **Modèles externes** :
  - `await K.loadGLB('/project/models/x.glb')` renvoie `gltf` (`gltf.scene`) ;
  - `await K.loadHDRI('/project/hdri/x.hdr', false)` remplace l'éclairage d'environnement.

  Les fichiers se placent dans le dossier du projet et s'adressent en `/project/...`. Sources CC0 : Poly Haven (HDRI, modèles), Kenney, Quaternius.
- **Géométries utiles** de three : `RoundedBoxGeometry` (`K.RoundedBoxGeometry`), `TubeGeometry` sur une `CatmullRomCurve3` (câbles, fils, trajectoires), `LatheGeometry` (vases, verres, bouteilles), `ExtrudeGeometry` sur une `Shape` (silhouettes, cartes de pays, logos inventés), `InstancedMesh` (foules, forêts, briques : des milliers d'objets pour le prix d'un).

## 4. Caméra

- `K.orbit(cible, yaw, pitch, distance, fov, focus)` : orbite autour d'une cible ; `focus` = point net (profondeur de champ activée).
- `K.mixCam(a, b, k)` : fondu lissé entre deux plans (transition de 0,6 à 1 s).
- Champs utiles : `aperture` (0,002 léger, 0,006 très flou), `shake` (0,003 = caméra à l'épaule, 0,03 = impact), `roll` (radians), `offsetY` (décale le sujet vers le bas pour libérer le haut ; 0,03 par défaut).
- En 9:16, le champ horizontal est étroit : un objet de 1 m de large tient dans l'image à environ 3,5 m avec `fov` 34.
- `K.project([x, y, z])` renvoie la position à l'écran (1080×1920) pour accrocher une étiquette 2D à un objet.

## 5. Habillage `o`

Automatique : sous-titres mot à mot (mots de `highlight` et nombres en jaune, dernier mot suivi de « ! » en vert) et texte-choc du champ `text`.

Dans `overlay(o, v, T, S, K)`, `o.c` est le contexte 2D. Fonctions importables depuis `/engine/overlay.js` :
- `sticker(ctx, texte, x, y, taille, couleur, { font, maxW })` : texte à contour noir, façon MrBeast ;
- `rr(ctx, x, y, w, h, r)` : rectangle arrondi ;
- `easeOutBack` et `easeOut` ;
- les constantes `FONT`, `COLORS` et `SAFE`.

Polices disponibles : Anton (titres) et Montserrat (sous-titres).

Réglages dans `story.json` : `"captions": { "show": true, "y": 1320, "size": 80 }`.

## 6. Bruitages et musique

Types de bruitages : `whoosh`, `whooshDown`, `impact`, `boom`, `ding`, `click`, `knock`, `clang`, `riser` (monte pendant 1,3 s et culmine à l'instant donné), `swell`, `alarm`, `siren`, `heartbeat`, `applause`, `rewind`, `pop`, `tick`, `coin`, `land`, `whistle`.

Automatiques :
- un impact à 0 s ;
- un whoosh et un pop sur chaque `text` ;
- un impact sur chaque `drop`.

À ajouter :
- `beat.sfx` : `["land@0.3", "riser@1.0"]` ;
- l'export `sfx()` de la scène, pour caler un son sur une animation précise.

Musique (`story.music`) : la densité suit `energy`. Au-dessus de 0,3 arrivent le kick et la basse, au-dessus de 0,45 les claps, au-dessus de 0,55 les charlestons, au-dessus de 0,6 les cloches. `"music": "off"` sur un beat le rend silencieux. Le mixage est automatique :
- voix normalisée ;
- musique à −13 dB et bruitages à −8 dB pendant la voix ;
- réverbération et limiteur ;
- normalisation finale à −14 LUFS.

## 7. Voix (edge-tts, gratuites)

| Langue | Voix |
|---|---|
| FR | `fr-FR-RemyMultilingualNeural` (narrateur), `fr-FR-VivienneMultilingualNeural`, `fr-FR-HenriNeural`, `fr-FR-DeniseNeural`, `fr-CA-ThierryNeural`, `fr-BE-GerardNeural`, `fr-CH-FabriceNeural` |
| EN | `en-US-AndrewMultilingualNeural`, `en-US-AvaMultilingualNeural`, `en-US-BrianMultilingualNeural` |
| AR | `ar-DZ-IsmaelNeural`, `ar-EG-ShakirNeural`… |

Réglages par beat : `voice`, `rate` (`"+10%"`), `pitch` (`"-2Hz"`). Pour un usage monétisé, préférer Azure AI Speech (mêmes voix, sous licence) ou ElevenLabs.

## 8. Exemple minimal complet

```js
export function build(K) {
  K.cyclorama({ color: 0x2a3150 });
  const box = K.shadows(new K.THREE.Mesh(new K.RoundedBoxGeometry(1, 1, 1, 4, 0.08), K.mat.glossy(0xff2d3d)));
  box.position.y = 0.5; K.scene.add(box);
  const sh = K.contactShadow(0.8); sh.position.y = 0.002; K.scene.add(sh);
  return { box };
}
export function update(K, v, T, S) {
  const k = K.easeOutBack(T.k('hook', v, 0, 0.6));
  S.box.scale.setScalar(Math.max(1e-4, k));
  S.box.rotation.y = v * 0.5;
}
export function camera(K, v, T) {
  return K.orbit([0, 0.5, 0], 0.4 + v * 0.05, 0.25, 4.2, 34, [0, 0.5, 0]);
}
```
