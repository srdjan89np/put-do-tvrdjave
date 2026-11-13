#!/usr/bin/env bash
# Pravi engleski promo klip docs/promo-en.mp4 iz prave igre (index.html).
set -euo pipefail
cd "$(dirname "$0")"
rm -rf frames && python3 record_en.py && FRAMES=$(ls frames | wc -l) python3 music.py
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i frames/f%05d.jpg -i music.wav \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 160k -shortest ../../docs/promo-en.mp4
rm -rf frames music.wav
echo "Gotovo: docs/promo-en.mp4"
