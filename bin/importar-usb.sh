#!/bin/bash
# Copia la carpeta "TeleVieja" de un pendrive (o disco USB) a la netbook.
# Corre como root (sudo, sin contraseña) desde el menú. No recibe argumentos.
# Le cuenta al menú cómo va con líneas "@@estado ...", "@@total BYTES" y el
# progreso de rsync (porcentaje, velocidad).
set -u
export LC_ALL=C   # números de rsync siempre con el mismo formato
USUARIO="@USUARIO@"
CASA=$(getent passwd "$USUARIO" | cut -d: -f6)
DESTINO="$CASA/TeleVieja"
PUNTO=/mnt/televieja-usb
MARGEN=$((1024 * 1024 * 1024))   # dejamos 1 GB libre para que la netbook ande bien

if [ -z "$CASA" ] || [ ! -d "$DESTINO" ]; then
    echo "No encuentro la carpeta $DESTINO"
    exit 1
fi

origenes=()
montados_a_mano=()

desmontar() {
    for m in "${montados_a_mano[@]}"; do
        umount "$m" 2>/dev/null && rmdir "$m" 2>/dev/null
    done
}
trap desmontar EXIT

buscar_en() {  # buscar_en PUNTO_DE_MONTAJE
    local origen
    origen=$(find "$1" -maxdepth 1 -type d -iname televieja | head -n1)
    [ -n "$origen" ] && origenes+=("$origen")
}

# 1) Discos que ya montó solo el sistema (bin/disco-usb.sh)
hay_montados=0
for montado in /media/televieja/*; do
    mountpoint -q "$montado" 2>/dev/null || continue
    hay_montados=1
    buscar_en "$montado"
done

# 2) Si no hay ninguno montado, los montamos a mano mientras dura la copia
if [ "$hay_montados" = 0 ]; then
    discos=$(lsblk -dpnro NAME,TRAN | awk '$2 == "usb" {print $1}')
    if [ -z "$discos" ]; then
        echo "No encontré ningún pendrive. Enchufalo y probá de nuevo."
        exit 1
    fi
    n=0
    for disco in $discos; do
        for part in $(lsblk -pnro NAME,FSTYPE "$disco" | awk '$2 != "" {print $1}'); do
            n=$((n + 1))
            mkdir -p "$PUNTO/$n"
            mountpoint -q "$PUNTO/$n" && umount "$PUNTO/$n"
            mount -o ro "$part" "$PUNTO/$n" 2>/dev/null || continue
            montados_a_mano+=("$PUNTO/$n")
            buscar_en "$PUNTO/$n"
        done
    done
fi

if [ "${#origenes[@]}" = 0 ]; then
    echo "El pendrive no tiene una carpeta llamada TeleVieja."
    echo "Creala y poné adentro Videos, Juegos, Historietas, etc."
    exit 1
fi

RSYNC=(rsync -r --size-only --no-perms --chmod=ugo=rwX --chown="$USUARIO:$USUARIO")

# Primero vemos cuánto hay que copiar (lo que ya está en la netbook se saltea)
echo "@@estado Revisando qué hay para copiar..."
falta=0
archivos=0
for origen in "${origenes[@]}"; do
    stats=$("${RSYNC[@]}" -n --stats "$origen"/ "$DESTINO"/ 2>/dev/null)
    b=$(echo "$stats" | awk -F: '/Total transferred file size/ {gsub(/[^0-9]/, "", $2); print $2}')
    a=$(echo "$stats" | awk -F: '/Number of regular files transferred/ {gsub(/[^0-9]/, "", $2); print $2}')
    falta=$((falta + ${b:-0}))
    archivos=$((archivos + ${a:-0}))
done

if [ "$archivos" = 0 ]; then
    echo "No hay nada nuevo: todo lo del pendrive ya está en la netbook."
    echo "Ya podés sacar el pendrive."
    exit 0
fi

libre=$(df -B1 --output=avail "$DESTINO" | tail -n1 | tr -d ' ')
gb() {  # bytes -> "12,3 GB" o "350 MB"
    awk -v b="$1" 'BEGIN { if (b >= 1073741824) printf "%.1f GB", b / 1073741824;
                           else printf "%d MB", b / 1048576 }' | tr . ,
}
if [ "$((falta + MARGEN))" -gt "$libre" ]; then
    echo "No entra: hay que copiar $(gb "$falta") y en la netbook quedan $(gb "$libre") libres."
    echo "No hace falta copiar: con el disco enchufado, lo que tiene ya aparece en el menú."
    exit 2
fi

echo "@@total $falta"
for origen in "${origenes[@]}"; do
    "${RSYNC[@]}" --info=progress2 --no-inc-recursive "$origen"/ "$DESTINO"/ \
        || { echo "Se cortó la copia (¿sacaste el pendrive?). Probá de nuevo: sigue donde quedó."; exit 1; }
done
echo "@@estado Terminando de guardar..."
sync

echo "Se copiaron $archivos archivos nuevos ($(gb "$falta"))."
echo "Ya podés sacar el pendrive."
