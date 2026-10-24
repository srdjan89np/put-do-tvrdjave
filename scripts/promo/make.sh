#!/usr/bin/env bash
# Pravi promo klip docs/promo.mp4 iz prave igre (index.html).
# Potrebno: python3 + playwright (chromium), numpy, ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf frames && python3 record.py && python3 music.py
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i frames/f%05d.jpg -i music.wav \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 160k -shortest ../../docs/promo.mp4
rm -rf frames music.wav
echo "Gotovo: docs/promo.mp4"
