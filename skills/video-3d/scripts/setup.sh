#!/usr/bin/env bash
# Dépendances du skill (à lancer une fois) : three + playwright (Node), edge-tts + imageio-ffmpeg (Python), Chromium.
set -e
cd "$(dirname "$0")"
npm install --no-audit --no-fund --save=false three@0.170.0 playwright@1.56.1
python3 -m pip install -q edge-tts imageio-ffmpeg || pip install -q edge-tts imageio-ffmpeg
# Chromium : réutilise celui de l'environnement s'il existe (PLAYWRIGHT_BROWSERS_PATH), sinon le télécharge
if [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ] || [ ! -d "${PLAYWRIGHT_BROWSERS_PATH}" ]; then npx playwright install chromium; fi
python3 -c "import imageio_ffmpeg;print('ffmpeg :', imageio_ffmpeg.get_ffmpeg_exe())"
echo "prêt"
