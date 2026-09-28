# Recettes avancées (tirées d'un épisode réel)

Ces recettes viennent d'un récit de 56 s : un bronze de Camille Claudel retrouvé dans une remise, puis vendu à Drouot. Elles couvrent ce que les modèles ne font pas : plusieurs décors, un écran qui filme la scène, une sculpture organique, une révélation calée sur un mot.

## Sommaire
1. Plusieurs décors dans une seule scène
2. Caler un événement sur un mot de la voix
3. Écran (TV, téléphone, moniteur) qui montre de la vraie 3D
4. Sculpture, animal ou personnage organique (`K.blob`)
5. Révélation : drap qui s'envole, gravure cachée
6. Cadrer une rangée d'objets en 9:16
7. Coupe franche ou fondu

## 1. Plusieurs décors
Place chaque décor à une abscisse différente, assez loin pour qu'aucun ne soit visible depuis un autre :
```js
const X = { tv: 0, galerie: 16, remise: 32, drouot: 48 };
```
Chaque beat de `story.json` porte un champ libre `"station": "remise"`. Dans `update`, la lumière principale suit la station active, et les intensités sont réglées décor par décor. Un décor sombre (musée) s'éclaire à 10–15, un décor clair à 60–110.

## 2. Caler un événement sur un mot
`b.words` contient l'horodatage réel de chaque mot. Calcule les instants clés une seule fois dans `build` et range-les dans `S` :
```js
const at = (id, word, fallback) => { const b = T.beat(id); const w = b.words.find((x) => x.w.toLowerCase().startsWith(word)); return w ? w.t : b.v0 + fallback; };
S.tCut = at('hook', 'et', 4.2) - 0.05;      // coupe sur « et qui reconnaissent… »
S.tStrike = T.beat('vente').v0 + 2.35;       // coup de marteau
```
Réutilise ensuite ces instants partout : animation, `camera` (secousse, flash via `K.grade.uFlash`), `sfx()` et `textAt`. L'image, le son et le texte tombent alors sur la même image.

## 3. Écran qui montre de la 3D
```js
S.rt = new THREE.WebGLRenderTarget(640, 360, { type: THREE.HalfFloatType });
S.screen = new THREE.Mesh(new THREE.PlaneGeometry(1.28, 0.72), new THREE.MeshBasicMaterial({ map: S.rt.texture }));
S.tvCam = new THREE.PerspectiveCamera(30, 16 / 9, 0.05, 20);
// update() : un « plateau télé » caché loin (x = -20) filmé par tvCam, seulement tant que l'écran est visible
if (v < S.tCut + 0.1) {
  S.tvCam.position.set(-20.35, 0.72, 1.25); S.tvCam.lookAt(-20, 0.55, 0);
  K.renderer.setRenderTarget(S.rt); K.renderer.render(K.scene, S.tvCam); K.renderer.setRenderTarget(null);
}
```
Ajoute par-dessus un plan transparent avec un bandeau en `K.canvasTex` (« DIRECT », prix, titre inventé). Aucun logo réel de chaîne.

## 4. Formes organiques (`K.blob`)
Décris la forme par des « chaînes » de sphères, en mètres réels :
```js
const c = (pts, r0, r1) => K.chain(pts, r0, r1, 2.2);           // densité 2,2 = surface lisse
const balls = [
  ...c([[-0.335, 0.2, 0], [-0.3, 0.29, 0], [-0.255, 0.36, 0]], 0.048, 0.04),   // torse
  { p: [-0.215, 0.435, 0], r: 0.031 },                                          // tête
];
const mesh = K.blob(balls, { size: 1.0, center: [0, 0.3, 0], resolution: 160, subtract: 30 });
```
- Une résolution de 160 avec `subtract` à 30 donne des détails nets. Le calcul prend quelques secondes : **mets la géométrie en cache** au niveau du module et partage-la entre toutes les copies (5 exemplaires = 1 calcul).
- Pour une patine sans texture, écris les couleurs par sommet : reliefs orientés vers le haut plus clairs, creux plus sombres, bruit `K.noise`. Utilise ensuite un matériau avec `vertexColors: true`, `metalness` 0,9 et `roughness` 0,35.
- Pour un socle rocheux, jette 70 sphères aléatoires dans une ellipse avec `K.rng(seed)`.
- Une silhouette en bâtons (cylindres + sphères) fait « cheap » ; `blob` la remplace.

## 5. Révélation
- **Drap** : un `LatheGeometry` avec des plis (rayon modulé par `sin`). À la révélation, il monte, pivote et part hors champ en 0,6 s (`K.easeIn`).
- **Ce qui doit rester secret** (gravure, étiquette, prix) est `visible = false` jusqu'à `S.tReveal`. Un objet caché sous un drap reste visible à travers le drap si on ne le masque pas.
- Découpe le beat pour que la chute tombe **sur le mot fort** : un beat « appel » (« Sa réaction : ») suivi d'un beat `reveal` en `drop: true`.

## 6. Cadrer une rangée en 9:16
Le champ horizontal est étroit. Pour montrer 5 objets, aligne-les en diagonale qui s'éloigne (`x = (i-2)*0.8`, `z = 0.4 - i*1.35`) et filme le long de la diagonale **depuis le haut** : œil à 2,7 m, cible à 0,95 m, fov 38. Vue de trop bas, les objets se superposent ; vue de trop près, le premier écrase les autres.

## 7. Coupe franche ou fondu
```js
const prev = T.beats[b.i - 1];
if (prev && prev.station === b.station && v - b.v0 < 0.7) cam = K.mixCam(view(prev.id, v), cam, (v - b.v0) / 0.7);
```
Utilise un fondu entre deux plans du même décor et une coupe franche entre deux décors. Un fondu qui traverse 16 m de vide montre l'arrière du décor.
