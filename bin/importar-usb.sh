#!/bin/bash
# Copia la carpeta "TeleVieja" de un pendrive a la netbook.
# Corre como root (sudo, sin contraseña) desde el menú. No recibe argumentos.
set -u
USUARIO="@USUARIO@"
CASA=$(getent passwd "$USUARIO" | cut -d: -f6)
DESTINO="$CASA/TeleVieja"
PUNTO=/mnt/televieja-usb

if [ -z "$CASA" ] || [ ! -d "$DESTINO" ]; then
    echo "No encuentro la carpeta $DESTINO"
    exit 1
fi

encontrado=0
copiados=0

copiar_desde() {  # copiar_desde CARPETA_TELEVIEJA_DEL_PENDRIVE
    local antes despues
    encontrado=1
    antes=$(find "$DESTINO" -type f | wc -l)
    rsync -r --size-only --no-perms --chmod=ugo=rwX \
          --chown="$USUARIO:$USUARIO" "$1"/ "$DESTINO"/
    despues=$(find "$DESTINO" -type f | wc -l)
    copiados=$((copiados + despues - antes))
}

# 1) Discos que ya montó solo TeleVieja (bin/disco-usb.sh)
hay_montados=0
for montado in /media/televieja/*; do
    mountpoint -q "$montado" 2>/dev/null || continue
    hay_montados=1
    origen=$(find "$montado" -maxdepth 1 -type d -iname televieja | head -n1)
    [ -n "$origen" ] && copiar_desde "$origen"
done

# 2) Si no hay ninguno montado, los montamos a mano un momento
if [ "$hay_montados" = 0 ]; then
    discos=$(lsblk -dpnro NAME,TRAN | awk '$2 == "usb" {print $1}')
    if [ -z "$discos" ]; then
        echo "No encontré ningún pendrive. Enchufalo y probá de nuevo."
        exit 1
    fi
    mkdir -p "$PUNTO"
    mountpoint -q "$PUNTO" && umount "$PUNTO"
    for disco in $discos; do
        for part in $(lsblk -pnro NAME,FSTYPE "$disco" | awk '$2 != "" {print $1}'); do
            mount -o ro "$part" "$PUNTO" 2>/dev/null || continue
            origen=$(find "$PUNTO" -maxdepth 1 -type d -iname televieja | head -n1)
            [ -n "$origen" ] && copiar_desde "$origen"
            umount "$PUNTO"
        done
    done
fi
sync

if [ "$encontrado" = 0 ]; then
    echo "El pendrive no tiene una carpeta llamada TeleVieja."
    echo "Creala y poné adentro Videos, Juegos, Historietas, etc."
    exit 1
fi
echo "Se copiaron $copiados archivos nuevos."
echo "Ya podés sacar el pendrive."
