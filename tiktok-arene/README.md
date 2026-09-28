# Arène des Nations — générateur de TikTok 3D (three.js)

32 billes-drapeaux sur un plateau de jeu télé. Le plateau penche, un bras rotatif balaie, les barrières tombent, les anneaux s'effondrent. **Le dernier pays sur la plateforme gagne.** Montage automatique façon MrBeast, voix off neuronale, foule, musique générée, export MP4 vertical prêt à publier.

Stratégie de diffusion : [`STRATEGIE.md`](STRATEGIE.md).

## Livrables de l'épisode 1 (seed 356)

| Fichier | Contenu |
|---|---|
| `episodes/ep01/out/arene-ep01.mp4` | vidéo finale 1080×1920, 30 i/s, H.264 + AAC 48 kHz, −14 LUFS |
| `episodes/ep01/out/arene-ep01_sans-musique.mp4` | même vidéo sans musique (pour un son tendance TikTok) |
| `episodes/ep01/out/cover_*.jpg` | couvertures candidates |
| `episodes/ep01/ep01.scenes.json` | découpage en scènes (JSON de production) |
| `episodes/ep01/voices/` | répliques TTS + horodatage mot à mot |

## Chaîne de production

```
seed ─► sim.js (physique déterministe) ─► director.js (ralentis, replay, caméras, voix, sous-titres, SFX)
                                              │
            tts.py (voix neuronales) ◄────────┤ répliques
                                              ▼
  render.html + scene.js (three.js) + hud.js (habillage) ─► images ─► ffmpeg H.264
  audio.js (bruitages, musique, foule, voix, ducking, limiteur) ─► loudnorm −14 LUFS ─► MP4
```

| Module | Rôle |
|---|---|
| `src/sim.js` | physique à 480 Hz : roulement dans une cuvette, chocs, portes, bras, effondrement, chute libre. Maths maison (sin, atan2, pow…) : **même seed ⇒ même partie** dans Node, Chrome, Firefox, Safari. Difficulté adaptative pour tenir le rythme visé. |
| `src/director.js` | courbe de vitesse (ralentis), replay, célébration, plans caméra, planification des répliques par priorité, sous-titres, événements sonores, JSON de scènes |
| `src/scene.js` | rendu three.js : PBR, IBL, ombres douces, faisceaux volumétriques, public, profondeur de champ, bloom, étalonnage, grain, confettis |
| `src/hud.js` | grille des 32 drapeaux, compteur, toasts d'élimination, bannières de manche, carte VS, sous-titres mot à mot, classement final |
| `src/audio.js` | mixeur en JS pur : clics de billes, grondement, moteur du bras, portes, sirène, battements de cœur, musique trap 140 BPM, foule multi-voix, réverbération, ducking, limiteur |
| `tools/seed_search.mjs` | classe les seeds par score de suspense (jamais par vainqueur) |
| `tools/episode.mjs` | prépare un épisode (liste des répliques) |
| `tools/tts.py` | voix Microsoft Neural (edge-tts) ou ElevenLabs (`--engine elevenlabs`, non testé faute de clé) |
| `tools/render.mjs` | rendu image par image (Chromium headless) + mixage + multiplexage |
| `index.html` | studio : aperçu temps réel, seed libre, zones sûres TikTok, enregistrement navigateur |

## Utilisation

```bash
npm install                      # three + playwright (navigateur Chromium requis)
pip install edge-tts imageio-ffmpeg

node tools/seed_search.mjs 1 400 > seeds.json          # 1. choisir un seed dramatique
node tools/episode.mjs 356 episodes/ep01               # 2. préparer l'épisode
python3 tools/tts.py episodes/ep01 --crowd             # 3. voix off + foule
node tools/render.mjs episodes/ep01 --workers 2        # 4. rendu MP4 (~70 min sur 4 cœurs CPU, quelques minutes avec GPU)
node tools/render.mjs episodes/ep01 --audio-only       #    remixer le son sans refaire les images
npx http-server -c-1 .                                 # studio : http://localhost:8080
```

Derrière un proxy TLS : `TTS_CA_BUNDLE=/chemin/ca.pem python3 tools/tts.py …`.

## Réglages utiles

- Durée de jeu : `P.D` (secondes jusqu'à la 30e élimination) et `P.duel` dans `src/sim.js`.
- Pays : `src/countries.js` (drapeaux dessinés en Canvas, aucune image externe).
- Répliques : `voiceCandidates()` dans `src/director.js`.
- Qualité / vitesse : `?rs=` (échelle du rendu 3D, défaut 0,75) et `?q=draft|high` dans `render.html`.

## Licences

Polices Anton et Montserrat : SIL Open Font License 1.1. Drapeaux redessinés en code. Musique et bruitages générés par le code. Voix : service Microsoft Edge TTS — pour un usage commercial, utiliser Azure AI Speech (mêmes voix) ou une offre payante ElevenLabs.
