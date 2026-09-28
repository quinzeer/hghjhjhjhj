# tiktok-studio — l'usine à vidéos « actu influenceurs »

Moteur de rendu vertical (1080×1920, 30 fps) en **Three.js**, piloté par un **JSON de scènes**.
Un épisode = un fichier `episodes/<slug>/episode.json` → une vidéo MP4 prête pour TikTok, Shorts, Reels et Spotlight.

```
episode.json ──► tools/build.py ──► voix off alignée au mot + musique originale + bruitages + timeline.json
                                         │
                 tools/render.mjs ◄──────┘  Chromium headless (WebGL) → images JPEG → ffmpeg → MP4
```

## Ce que fait le pipeline

| Étape | Outil | Détail |
|---|---|---|
| Voix off | `tools/tts.py` | Piper (local), horodatage **mot à mot** par alignement des phonèmes, lexique de prononciation (`Nasdas` → « Nass-dass »), chaîne « voix radio » (coupe-bas, présence, compression) |
| Musique | `tools/music.py` | Instrumental trap original généré (808 saturée audible sur haut-parleur de téléphone), arrangé sur la timeline : `drop`, `build`, `break`, `stop` |
| Bruitages | `tools/sfx.py` | 19 sons synthétisés : whoosh, boom, hit, riser, pop, ding, cash, tick, glitch, shutter… |
| Montage | `tools/build.py` | Coupes calées sur les mots, sous-titres 1-3 mots avec mots-clés colorés, habillage synchronisé sur un mot (`au_mot`), whooshes automatiques, ducking de la musique, mastering −14 LUFS / −1 dBTP |
| Rendu 3D | `src/` | Plateau TV : sol résine à réflexions floues, mur LED à masque RVB, faisceaux volumétriques, poussière, podium LED ; accessoires PBR (téléphone, écrin + diamant à dispersion, pizza, liasses, voiture bâchée CC0, texte 3D or, graphique en barres) |
| Caméra | `src/engine/camera.js` | Keyframes + tremblement « à l'épaule » + secousses synchronisées aux impacts + whip pan / zoom punch |
| Post-prod | `src/engine/post.js` | Profondeur de champ, bloom, tone mapping AgX/ACES, flou de mouvement d'obturateur, SMAA, aberration chromatique, distorsion d'objectif, grain argentique, vignettage, light leaks |
| Habillage | `src/engine/overlay.js` | Sous-titres « pop », titres chocs, compteurs, tampons, bandeaux nom, flèches, cercles, emojis, sources, barre de progression |

## Installation (une fois)

```bash
cd tiktok-studio
npm install                                   # three, postprocessing, esbuild, playwright, opentype.js
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
sudo apt-get install -y ffmpeg                # avec libx264
.venv/bin/python tools/fetch_assets.py        # HDRI + modèles Poly Haven (CC0)
.venv/bin/python tools/fetch_assets.py model:covered_car:1k
mkdir -p .voices && cd .voices && B=https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium \
  && curl -LO $B/fr_FR-siwis-medium.onnx && curl -LO $B/fr_FR-siwis-medium.onnx.json && cd ..
```

Playwright utilise le Chromium déjà installé (`PLAYWRIGHT_BROWSERS_PATH`) ; sinon `npx playwright install chromium`.

## Produire un épisode

```bash
npm run build                                              # compile le moteur (dist/engine.js)
.venv/bin/python tools/build.py episodes/nasdas-01         # voix + musique + timeline + mix
.venv/bin/python tools/script_doc.py episodes/nasdas-01    # script lisible (SCRIPT.md)
node tools/render.mjs episodes/nasdas-01 --scale 0.5 --fps-div 3 --workers 2   # aperçu rapide (10 fps)
node tools/render.mjs episodes/nasdas-01 --mode plate --rs 0.9   # passe lente : plaques 3D sans texte (build/plates)
node tools/render.mjs episodes/nasdas-01 --mode overlay          # passe rapide : habillage + encodage → out/final.mp4
node tools/render.mjs episodes/nasdas-01 --stills 0,90,300       # images fixes de contrôle (3D + habillage)
```

**Deux passes** : la 3D (lente) est rendue une fois en « plaques » ; sous-titres, titres et compteurs sont posés ensuite en quelques minutes.
Pour corriger un texte, modifie `episode.json` puis relance `build.py` et seulement `--mode overlay`.
La voix off est mise en cache par scène (`build/tts_cache/`) : tant que le texte lu ne change pas, les timings restent identiques et les plaques restent synchrones. Si tu changes une `voix_off`, relance aussi `--mode plate`.

Temps mesurés sur 4 cœurs CPU sans GPU (WebGL logiciel) : aperçu ≈ 12 min, rendu final ≈ 1 h 30 à 2 h pour 62 s.
Avec une vraie carte graphique (Chrome lancé avec `--use-angle=vulkan` ou sans les options SwiftShader), le rendu tombe à quelques minutes.

## Remplacer la voix de synthèse par ta voix (recommandé)

1. `build/mix_sans_voix.wav` contient musique + bruitages calés sur la timeline.
2. Enregistre-toi en lisant `SCRIPT.md` sur ce fond (casque sur les oreilles), exporte `ma_voix.wav`.
3. Mixe : `ffmpeg -i build/mix_sans_voix.wav -i ma_voix.wav -filter_complex "[1]volume=1.0[v];[0][v]amix=inputs=2:normalize=0" mix_perso.wav`
4. Remplace la piste audio : `ffmpeg -i out/final.mp4 -i mix_perso.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k out/final_ma_voix.mp4`

Pour un calage parfait des sous-titres sur ta voix, garde le même texte et un débit proche (≈ 2,8 mots/s).

## Ajouter de vraies images (optionnel)

Chaque écran accepte une image : `"image": "episodes/nasdas-01/assets/photo.jpg"` dans un `wall` de type `photo`, un item de `grid`, ou le `phone` (`"image"` ou `"avatar"`).
Si le fichier n'existe pas, une silhouette neutre s'affiche. **N'utilise que des images dont tu as les droits** (photo fournie par l'intéressé, licence, capture de ta propre publication) : en France, reproduire une photo entière n'est pas une « courte citation » (Cass. 1re civ., 07/11/2006).

## Écrire un nouvel épisode

Copie `episodes/nasdas-01/episode.json` et modifie les `scenes`. Champs utiles :

| Champ | Rôle |
|---|---|
| `voix_off` | Texte lu. `446_773` s'affiche « 446 773 » et se prononce comme un seul nombre |
| `mots_cles` / `mots_rouges` / `mots_verts` | Mots colorés dans les sous-titres |
| `plans[]` | Plans 3D : `cam` (préréglage ou keyframes), `params.prop`, `params.wall`, `params.phone`, `coupe_sur` (mot où couper), `trans` (`whip`, `whipUp`, `zoom`, `cut`) |
| `habillage[]` | `headline`, `counter`, `chip`, `stamp`, `lowerthird`, `quote`, `emoji`, `arrow`, `circle`, `source`, `progress`, `photo` ; `au_mot` pour la synchro |
| `bruitages[]` | `sfx` + `at`, `au_mot` ou `avant_fin` |
| `musique` | `drop` / `build` / `break` / `stop` au début de scène (ou `musique_au_mot`) |

Préréglages caméra du plateau : `wide`, `hero`, `heroLeft`, `low`, `orbit`, `wall`, `crane`, `push`, `macro`, `top`, `car`, `carSide`.
Accessoires : `phone` (écrans `live`, `lock`, `video`, `profile`), `ringbox`, `pizza`, `cash`, `car`, `chart`, `text3d`, `vintage_suitcase`, `Megaphone_01`, `magnifying_glass_01`, `marble_bust_01`.

## Licences et crédits

- Modèles et HDRI : [Poly Haven](https://polyhaven.com) (CC0).
- Polices : Montserrat, Anton, Inter, Bebas Neue, Archivo Black (SIL OFL), Luckiest Guy (Apache 2.0).
- Voix : [Piper](https://github.com/rhasspy/piper), modèle `fr_FR-siwis-medium` entraîné sur le corpus SIWIS (**CC BY 4.0** : créditer « Voix de synthèse : Piper / SIWIS »).
- Musique et bruitages : générés par le code de ce dépôt (aucun échantillon tiers).
