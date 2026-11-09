#!/bin/bash
# Achica videos para la netbook: 480 líneas como máximo y H.264 fácil de decodificar.
# Conviene correrlo en una compu más potente (Linux o WSL con ffmpeg).
#
# Uso: ./convertir-videos.sh CARPETA_ORIGEN CARPETA_DESTINO
set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Uso: $0 CARPETA_ORIGEN CARPETA_DESTINO"
    exit 1
fi
ORIGEN="$(cd "$1" && pwd)"
DESTINO="$2"
mkdir -p "$DESTINO"
DESTINO="$(cd "$DESTINO" && pwd)"

find "$ORIGEN" -type f \( -iname '*.mp4' -o -iname '*.mkv' -o -iname '*.avi' -o -iname '*.mov' \
    -o -iname '*.wmv' -o -iname '*.flv' -o -iname '*.webm' -o -iname '*.mpg' -o -iname '*.mpeg' \
    -o -iname '*.m4v' -o -iname '*.vob' -o -iname '*.ts' \) -print0 |
while IFS= read -r -d '' video; do
    relativo="${video#"$ORIGEN"/}"
    salida="$DESTINO/${relativo%.*}.mp4"
    if [ -f "$salida" ]; then
        echo "Ya está: $relativo"
        continue
    fi
    mkdir -p "$(dirname "$salida")"
    echo "Convirtiendo: $relativo"
    ffmpeg -nostdin -loglevel error -stats -i "$video" \
        -map 0:v:0 -map 0:a:0? \
        -vf "scale='min(640,iw)':'min(480,ih)':force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
        -c:v libx264 -preset medium -tune fastdecode -profile:v main -crf 22 \
        -c:a aac -ac 2 -b:a 128k -movflags +faststart \
        "$salida.tmp.mp4"
    mv "$salida.tmp.mp4" "$salida"
done
echo "Terminado. Los videos están en: $DESTINO"
