#!/usr/bin/env bash
# Preuzima fontove (Rubik i Nunito, ćirilica + latinica) sa npm-a u folder fonts/
# da igrica izgleda isto i bez interneta (APK, GitHub Pages).
# Pokretanje:  bash scripts/fetch-fonts.sh [izlazni_folder]
set -euo pipefail

OUT="${1:-fonts}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$OUT"
( cd "$TMP" && npm pack @fontsource/rubik@5 @fontsource/nunito@5 >/dev/null \
  && mkdir rubik nunito \
  && tar xzf fontsource-rubik-*.tgz -C rubik --strip-components=1 \
  && tar xzf fontsource-nunito-*.tgz -C nunito --strip-components=1 )

CYR='U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116'
LAT='U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
LATEXT='U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF'

CSS="$OUT/fonts.css"
: > "$CSS"

add() { # family pkg weight
  local fam="$1" pkg="$2" w="$3" sub range file
  for sub in cyrillic latin-ext latin; do
    case "$sub" in
      cyrillic) range="$CYR" ;;
      latin-ext) range="$LATEXT" ;;
      latin) range="$LAT" ;;
    esac
    file="$pkg-$sub-$w-normal.woff2"
    cp "$TMP/$pkg/files/$file" "$OUT/$file"
    cat >> "$CSS" <<CSSEOF
@font-face{font-family:'$fam';font-style:normal;font-weight:$w;font-display:swap;src:url($file) format('woff2');unicode-range:$range}
CSSEOF
  done
}

for w in 700 800 900; do add Rubik rubik "$w"; done
for w in 600 800 900; do add Nunito nunito "$w"; done

echo "Fontovi su u: $OUT ($(ls "$OUT" | wc -l) fajlova)"
