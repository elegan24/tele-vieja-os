#!/bin/bash
# Monta (o desmonta) un disco USB para TeleVieja. Lo llama systemd cuando
# enchufás o sacás un disco (ver sistema/99-televieja-usb.rules).
#
# Se monta en SOLO LECTURA: así se puede desenchufar sin romper nada.
# Uso: disco-usb.sh montar|desmontar sdb1
set -u
accion="${1:-}"
dispositivo="${2:-}"
USUARIO="@USUARIO@"
MONTAJES=/media/televieja
ESTADO=/run/televieja

# Solo nombres del kernel tipo "sdb1" (nada de rutas raras).
if ! [[ "$dispositivo" =~ ^[a-z]+[0-9]*$ ]]; then
    echo "Dispositivo inválido: $dispositivo" >&2
    exit 1
fi
mkdir -p "$MONTAJES" "$ESTADO"

montar() {
    local dev="/dev/$dispositivo" tipo uuid punto opciones uid gid
    tipo=$(blkid -o value -s TYPE "$dev" 2>/dev/null) || exit 0
    uuid=$(blkid -o value -s UUID "$dev" 2>/dev/null)
    # Carpeta con el UUID: siempre la misma para el mismo disco (así se acuerda
    # en qué capítulo o página quedaste aunque lo enchufes en otro puerto).
    if [[ "$uuid" =~ ^[A-Za-z0-9-]+$ ]]; then
        punto="$MONTAJES/$uuid"
    else
        punto="$MONTAJES/$dispositivo"
    fi
    if mountpoint -q "$punto"; then
        exit 0
    fi
    uid=$(id -u "$USUARIO")
    gid=$(id -g "$USUARIO")
    opciones="ro,nosuid,nodev,noexec"
    case "$tipo" in
        vfat) opciones+=",uid=$uid,gid=$gid,utf8" ;;
        exfat) opciones+=",uid=$uid,gid=$gid,iocharset=utf8" ;;
        ntfs)
            opciones+=",uid=$uid,gid=$gid"
            command -v ntfs-3g >/dev/null && tipo=ntfs-3g ;;
        ext2|ext3|ext4|btrfs|xfs|f2fs) ;;
        *) exit 0 ;;   # swap, discos cifrados, etc.: no se tocan
    esac
    mkdir -p "$punto"
    if mount -t "$tipo" -o "$opciones" "$dev" "$punto"; then
        echo "$punto" > "$ESTADO/$dispositivo"
    else
        rmdir "$punto" 2>/dev/null
        exit 1
    fi
}

desmontar() {
    local punto
    punto=$(cat "$ESTADO/$dispositivo" 2>/dev/null) || exit 0
    case "$punto" in
        "$MONTAJES"/*) ;;
        *) exit 0 ;;
    esac
    umount -l "$punto" 2>/dev/null
    rmdir "$punto" 2>/dev/null
    rm -f "$ESTADO/$dispositivo"
}

case "$accion" in
    montar) montar ;;
    desmontar) desmontar ;;
    *) echo "Uso: $0 montar|desmontar DISPOSITIVO" >&2; exit 1 ;;
esac
