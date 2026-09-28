# Pièges connus et remèdes

| Symptôme | Cause | Remède |
|---|---|---|
| Écran noir / objet invisible vu du dessus | normales inversées (faces tournées vers l'intérieur) sur une géométrie maison | inverser l'ordre des indices des triangles, ou `side: THREE.DoubleSide` pour tester |
| « la page de rendu ne s'est pas initialisée » | erreur JS dans `scene.js`, module introuvable, three non chargé | lire les lignes `console :` / `erreur page :` du journal ; `render.mjs` sert `three` depuis `node_modules` (lancer `setup.sh`) |
| Polices de secours (texte trop large, débordements) | Google Fonts bloqué en headless | le skill embarque Anton et Montserrat en local (`scripts/fonts`) ; ne pas dépendre d'une police web |
| `ERR_CERT_AUTHORITY_INVALID` / TLS | proxy qui intercepte le HTTPS | voix : `TTS_CA_BUNDLE=/chemin/ca.pem` ; navigateur : servir les fichiers en local (déjà fait pour three) |
| Rendu très lent (> 5 s/image) | pas de GPU (SwiftShader), MSAA, profondeur de champ, verre à transmission | `--rs 0.6`, `--q draft` pour les essais, limiter `mat.glass`, `--workers 2` (au-delà, les rendus se gênent) |
| Les images changent d'un rendu à l'autre | état accumulé ou `Math.random()` dans `update` | tout calculer depuis `v` ; `K.rng(seed)` dans `build` |
| Simulation différente entre Node et Chrome | `Math.sin/pow/atan2` diffèrent d'un ULP selon le moteur ; le chaos amplifie | maths maison à base de + − × ÷ et `sqrt` (voir `sim.js` de l'Arène) |
| Voix noyée | musique et bruitages trop forts | le mixeur normalise la voix (≈ −14 dBFS RMS) et baisse le reste ; éviter des `gain` > 0,8 sur des sons longs |
| Fichier trop lourd pour l'envoi | limite de 30 Mio de certains outils | envoyer `out/video_light.mp4` (2 passes, < 30 Mio) |
| Texte coupé à gauche/droite | texte-choc trop long | ≤ 14 caractères par ligne, `\n` pour couper ; `sticker(..., { maxW })` réduit automatiquement |
| Sujet collé au haut de l'image | la grille/le titre de TikTok le recouvrent | `offsetY` de la caméra (0,03–0,08) pousse le sujet vers le bas |
