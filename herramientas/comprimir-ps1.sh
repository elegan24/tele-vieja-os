#!/bin/bash
# Comprime juegos de PS1 (.cue + .bin) a .chd: ocupan bastante menos y se juegan igual.
# Necesita chdman (en Debian/Ubuntu: sudo apt install mame-tools). Conviene correrlo en la compu.
#
# Uso: ./comprimir-ps1.sh CARPETA_CON_JUEGOS [CARPETA_SALIDA]
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 CARPETA_CON_JUEGOS [CARPETA_SALIDA]"
    exit 1
fi
if ! command -v chdman >/dev/null; then
    echo "Falta chdman. Instalalo con:  sudo apt install mame-tools"
    exit 1
fi
ORIGEN="$(cd "$1" && pwd)"
SALIDA="${2:-$ORIGEN}"
mkdir -p "$SALIDA"
SALIDA="$(cd "$SALIDA" && pwd)"

find "$ORIGEN" -type f -iname '*.cue' -print0 | while IFS= read -r -d '' cue; do
    relativo="${cue#"$ORIGEN"/}"
    destino="$SALIDA/${relativo%.*}.chd"
    if [ -f "$destino" ]; then
        echo "Ya está: $relativo"
        continue
    fi
    mkdir -p "$(dirname "$destino")"
    echo "Comprimiendo: $relativo"
    chdman createcd -i "$cue" -o "$destino.tmp" >/dev/null
    mv "$destino.tmp" "$destino"
done
echo "Listo. Revisá que los .chd anden y después podés borrar los .cue/.bin originales."
