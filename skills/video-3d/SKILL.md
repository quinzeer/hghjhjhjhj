---
name: video-3d
description: Produire des vidéos verticales 3D de qualité « tournage » (three.js) sur n'importe quel sujet, de l'idée au MP4 prêt à publier sur TikTok, YouTube Shorts ou Reels ; scène 3D, voix off neuronale, sous-titres mot à mot, bruitages, musique et rendu image par image. Utiliser ce skill dès qu'on demande une vidéo, un Short, un TikTok, un Reel, une animation 3D, une vidéo explicative, un récit animé, une vidéo « C'est l'histoire de… », un top ou une comparaison animée, même si three.js ou la 3D ne sont pas cités, et dès qu'on veut refaire « une vidéo comme la précédente » sur un autre sujet.
---

# Vidéo 3D verticale (three.js)

Ce skill fournit un moteur complet : la timeline suit la voix off, le kit three.js apporte l'éclairage, les matériaux et le post-traitement, l'habillage ajoute sous-titres et textes-chocs, puis le rendu produit un MP4 1080×1920 à −14 LUFS. **Pour chaque vidéo, tu écris seulement deux fichiers : `story.json` (le récit) et `scene.js` (la mise en scène 3D).**

Chemin du skill : le dossier de ce fichier, noté `$S` ci-dessous.

## 0. Installation (une fois par machine)

```bash
bash $S/scripts/setup.sh        # three, playwright, edge-tts, imageio-ffmpeg, Chromium
```
Si le réseau passe par un proxy TLS, exporte `TTS_CA_BUNDLE=/chemin/ca.pem` pour la voix. Les pièges d'environnement sont dans `references/pieges.md`.

## 1. Cadrer le sujet

Avant tout code, réponds à trois questions :
1. **La promesse en 15 mots** : « Tu vas voir / comprendre ___ ».
2. **Le format** (voir `references/sujets.md`) : récit, explication, comparaison, classement, simulation, portrait d'objet ou de lieu.
3. **Faisabilité 3D** : tout sujet se raconte en 3D, à condition de passer par des objets, des lieux, des maquettes, des symboles, des données ou des personnages stylisés. Quatre choses sont exclues :
   - des humains photoréalistes ;
   - le visage ou la voix d'une personne réelle ;
   - des logos de marque ;
   - une fausse image d'un événement réel présentée comme vraie.

   `references/sujets.md` donne l'équivalent visuel de chaque type de sujet.

Si le sujet touche l'actualité ou un fait réel : chaque chiffre, date ou nom doit venir d'au moins **deux sources fiables**. Ne jamais inventer un fait pour « faire plus fort ». Un fait non vérifié se retire ou se formule prudemment. Si un skill de scénarisation est disponible (par ex. `scenariste-youtube`), utilise-le pour le hook et la structure.

## 2. Créer le projet

```bash
node $S/scripts/new_project.mjs recit ./projets/mon-sujet   # modèles : recit, comparaison, classement
```
Choisis le modèle le plus proche du format. Tu peux ensuite réécrire `scene.js` librement : le modèle donne la mécanique (caméra qui voyage, entrées d'objets, confettis).

## 3. Écrire `story.json`

La vidéo suit la narration : chaque **beat** dure le temps de sa réplique, plus une petite marge.

```json
{
  "title": "…", "look": "studio", "music": "tension",
  "voice": "fr-FR-RemyMultilingualNeural", "rate": "+8%",
  "highlight": ["MOTS", "EN JAUNE"],
  "beats": [
    { "id": "hook", "say": "Phrase dite par la voix off.", "text": "3 À 5 MOTS\nÀ L'ÉCRAN", "energy": 0.6 },
    { "id": "twist", "say": "…", "drop": true, "sfx": ["impact@0.2"], "energy": 0.9 }
  ]
}
```

| Champ | Rôle |
|---|---|
| `look` | ambiance : `studio`, `day`, `sunset`, `night`, `space`, `dark` |
| `music` | `tension`, `epic`, `chill`, `playful`, `mystery`, `none` |
| `say` | réplique (≈ 2,6 mots/s) ; sans `say`, donner `dur` en secondes |
| `text` | texte-choc à l'écran (`\n` = 2e ligne en jaune), position `textPos` : `top`, `center`, `bottom` ; `textAt` = décalage en s depuis le début du beat |
| `energy` | 0–1 : densité de la musique sur ce beat |
| `drop` | coupe la musique 0,45 s avant le beat puis impact (révélation) |
| `sfx` | bruitages au début du beat, `type@décalage` ; types dans `references/api.md` |
| `delay`, `pad`, `min`, `dur` | réglages de durée du beat |
| n'importe quel autre champ | libre : lu par `scene.js` (ex. `"station": 2`) |

Règles d'écriture qui font la rétention :
- **Hook en moins de 2 s** : l'image, la voix et le texte disent la même chose, et l'action est déjà en cours.
- Un seul mystère ouvert, refermé à la fin.
- Les beats s'enchaînent par « mais » ou « donc », jamais par « et puis ».
- Une relance vers le tiers et vers les deux tiers de la vidéo.
- La fin est sèche, sans outro.
- Durée : 35–60 s (TikTok ne rémunère qu'au-delà d'1 min ; la complétion baisse avec la longueur).

## 4. Voix off

```bash
python3 $S/scripts/tts.py ./projets/mon-sujet     # → voices/*.mp3 + manifest.json (horodatage mot à mot)
```
Réécouter n'est pas possible pour toi : vérifie au moins la durée totale affichée. La voix par défaut est `fr-FR-RemyMultilingualNeural` ; il y a d'autres voix FR, EN et AR (liste dans `references/api.md`). `--engine elevenlabs` utilise `ELEVENLABS_API_KEY` et `ELEVENLABS_VOICE_ID` pour plus d'émotion.

## 5. Écrire `scene.js`

Quatre exports, tous des **fonctions du temps vidéo `v`** (aucun état accumulé d'une image à l'autre : c'est ce qui rend le rendu déterministe et parallélisable) :

```js
export function build(K, T, story) { /* crée les objets une fois ; renvoie un état */ }
export function update(K, v, T, S) { /* positionne tout pour l'instant v */ }
export function camera(K, v, T, S) { return K.orbit([0, 1, 0], yaw, pitch, dist, fov, focus); }
export function overlay(o, v, T, S, K) { /* optionnel : habillage 2D en plus (compteurs, cartes) */ }
export function sfx(T, story, S) { return [{ v: 3.2, type: 'land', gain: 0.6 }]; } // optionnel
```
`K` est le kit (matériaux, textes 3D, cyclorama, particules, confettis, glTF…), `T` la timeline (`T.beat(id)`, `T.k(id, v)` = progression 0→1 d'un beat, `T.beatAt(v)`). API complète et exemples : `references/api.md`. Recette du rendu réaliste : `references/realisme.md`. **Lis les deux avant d'écrire la scène.**

## 6. Contrôler, puis rendre

```bash
node $S/scripts/render.mjs ./projets/mon-sujet --preview 8        # planche contact (≈ 1–2 min) → out/preview.jpg
node $S/scripts/render.mjs ./projets/mon-sujet --at 0.5,4,12       # images précises
node $S/scripts/render.mjs ./projets/mon-sujet --workers 2         # vidéo complète
```
**Regarde toujours la planche contact avant le rendu complet.** Sans GPU, le rendu complet coûte 2 à 4 s par image, soit environ 40 à 70 min pour 60 s. Lance-le en arrière-plan.

La planche contact doit passer ces contrôles :
- le sujet principal occupe 30 à 60 % de la hauteur ;
- rien d'important dans les zones de l'interface TikTok (haut < 170 px, bas > 1540 px, bande de droite) ;
- aucun objet coupé par le cadre sans intention ;
- aucun écran vide ou noir, ni face invisible (normales inversées) ;
- les textes restent lisibles en miniature.

Sorties dans `out/` :
- `video.mp4` : H.264 ≤ 9 Mb/s, AAC, −14 LUFS, crête −1,5 dBTP ;
- `video_light.mp4` : moins de 30 Mio, à envoyer par des outils limités ;
- `cover.jpg`.

Pour remixer le son sans refaire les images : `--audio-only`.

## 7. Livrer

Donne la vidéo (version légère si l'outil d'envoi est limité à 30 Mio), la liste des faits et de leurs sources si le sujet est réel, et le rappel d'activer le label « contenu généré par IA » (voix synthétique). Signale ce que tu n'as pas pu vérifier : l'audio écouté, un fait à source unique.

## Références

| Fichier | Quand le lire |
|---|---|
| `references/api.md` | avant d'écrire `scene.js` : kit, timeline, habillage, bruitages, voix |
| `references/realisme.md` | pour tout rendu : lumière, matériaux, caméra, son qui font « vrai » |
| `references/sujets.md` | au cadrage : format et traduction visuelle de n'importe quel sujet |
| `references/pieges.md` | quand quelque chose casse : écran noir, polices, proxy, lenteur, son |
| `references/avance.md` | scène à plusieurs décors, écran qui filme la 3D, sculpture ou personnage organique, révélation calée sur un mot, rangée d'objets en 9:16 |
