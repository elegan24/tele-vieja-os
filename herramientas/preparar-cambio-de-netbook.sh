#!/bin/bash
# Deja el disco listo para pasarlo a una netbook más nueva.
#
# Las netbooks viejas (como la Atom N455) arrancan "a la antigua" (BIOS) y las nuevas
# arrancan con UEFI. Este script le agrega al disco lo que necesita UEFI SIN sacar lo
# de BIOS: después de correrlo, el disco arranca en las dos.
#
# Para hacer lugar, cambia la partición de intercambio ("swap") por un archivo de
# intercambio y usa ese espacio para la partición de arranque UEFI.
# Solo toca el disco si tiene exactamente la forma que deja el instalador de Debian
# ("Guiado - utilizar todo el disco"). Si no, no cambia nada.
#
# Uso: sudo ./herramientas/preparar-cambio-de-netbook.sh
set -euo pipefail

verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
amarillo() { printf '\033[1;33m%s\033[0m\n' "$*"; }
rojo() { printf '\033[1;31m%s\033[0m\n' "$*"; }

# Para las pruebas: trabajar sobre un disco de mentira y solo tocar particiones.
PRUEBA_DISCO="${TELEVIEJA_PRUEBA_DISCO:-}"
PRUEBA_RAIZ="${TELEVIEJA_PRUEBA_RAIZ:-}"

if [ "$(id -u)" != 0 ]; then
    rojo "Corré esto con sudo:  sudo $0"
    exit 1
fi
if [ -z "$PRUEBA_DISCO" ] && [ "$(dpkg --print-architecture)" != amd64 ]; then
    rojo "Esto sirve solo con Debian de 64 bits (amd64): las netbooks nuevas no arrancan 32 bits."
    exit 1
fi

instalar_arranque_uefi() {
    verde "==> Instalando el arranque UEFI (con Secure Boot)..."
    apt-get install -y --no-install-recommends grub-efi-amd64-bin grub-efi-amd64-signed \
        shim-signed dosfstools
    # "--removable": se instala en EFI/BOOT/BOOTX64.EFI, el lugar que busca cualquier
    # netbook UEFI sin configurar nada (no depende de la memoria de la netbook vieja).
    grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot \
        --removable --uefi-secure-boot --no-nvram
    local uuid prefijo
    if findmnt -n /boot >/dev/null; then
        uuid=$(findmnt -no UUID /boot)
        prefijo=/grub
    else
        uuid=$(findmnt -no UUID /)
        prefijo=/boot/grub
    fi
    # El GRUB firmado busca su configuración en EFI/debian; el otro, al lado suyo.
    for carpeta in /boot/efi/EFI/BOOT /boot/efi/EFI/debian; do
        mkdir -p "$carpeta"
        printf 'search.fs_uuid %s root\nset prefix=($root)%s\nconfigfile $prefix/grub.cfg\n' \
            "$uuid" "$prefijo" > "$carpeta/grub.cfg"
    done
    update-grub
}

terminar() {
    echo
    verde "¡Listo! El disco ahora arranca en netbooks viejas (BIOS) y nuevas (UEFI)."
    echo "Cuando lo pases a la otra netbook:"
    echo " - Si no arranca solo, entrá al menú de arranque (F12, F11, F10 o Esc) y elegí el disco."
    echo " - Si dice algo de 'Secure Boot', desactivalo en el BIOS de la netbook nueva."
    echo " - Corré de nuevo  sudo ./instalar.sh  con internet, para que se adapte a esa netbook."
}

# --- Caso 1: ya está todo o la netbook ya arranca con UEFI ------------------
if [ -z "$PRUEBA_DISCO" ] && findmnt -n /boot/efi >/dev/null; then
    instalar_arranque_uefi
    terminar
    exit 0
fi

# --- Caso 2: BIOS sin partición UEFI: hay que hacerle lugar -----------------
if [ -n "$PRUEBA_DISCO" ]; then
    disco="$PRUEBA_DISCO"
    raiz="$PRUEBA_RAIZ"
else
    raiz=$(findmnt -no SOURCE /)
    disco="/dev/$(lsblk -no PKNAME "$raiz" | head -n1)"
fi

buscar_esp() {  # la partición UEFI (tipo "ef"), si ya existe
    sfdisk --json "$disco" | python3 -c '
import json, sys
for p in json.load(sys.stdin)["partitiontable"].get("partitions", []):
    if p["type"].lower() == "ef":
        print(p["node"])'
}

esp=$(buscar_esp)
if [ -n "$esp" ]; then
    verde "==> Ya hay una partición UEFI ($esp): sigo desde ahí."
else

# Revisa que el disco sea exactamente: 1 partición Linux (la del sistema) +
# 1 extendida + 1 swap adentro. Imprime "extendida swap" o el problema.
analisis=$(sfdisk --json "$disco" | python3 -c '
import json, sys
raiz = sys.argv[1]
t = json.load(sys.stdin)["partitiontable"]
if t.get("label") != "dos":
    print("ERROR: el disco no usa la tabla de particiones de siempre (MBR)"); sys.exit()
partes = t.get("partitions", [])
tipos = {p["node"]: p["type"].lower() for p in partes}
linux = [n for n, ty in tipos.items() if ty == "83"]
extendidas = [n for n, ty in tipos.items() if ty in ("5", "f", "85")]
swaps = [n for n, ty in tipos.items() if ty == "82"]
if len(partes) != 3 or linux != [raiz] or len(extendidas) != 1 or len(swaps) != 1:
    print("ERROR: el disco no tiene la forma que deja el instalador de Debian")
    for p in partes:
        print("  ", p["node"], "tipo", p["type"])
    sys.exit()
print(extendidas[0], swaps[0])
' "$raiz")
if [[ "$analisis" == ERROR* ]]; then
    rojo "${analisis%%$'\n'*}"
    echo "${analisis#*$'\n'}"
    amarillo "No toqué nada. Así el disco arranca solo en netbooks con BIOS (o UEFI con 'modo Legacy/CSM')."
    exit 1
fi
read -r extendida swap <<< "$analisis"
num_extendida="${extendida##*[!0-9]}"
num_swap="${swap##*[!0-9]}"

echo
amarillo "Voy a cambiar las particiones de $disco:"
echo "  - $swap (swap, memoria de intercambio) pasa a ser un archivo: /swapfile"
echo "  - en su lugar creo la partición de arranque UEFI"
echo "  - $raiz (tu sistema y tus cosas) NO se toca"
if [ -z "$PRUEBA_DISCO" ]; then
    echo
    read -r -p "Escribí SI (en mayúsculas) para seguir: " respuesta
    if [ "$respuesta" != SI ]; then
        echo "Cancelado. No toqué nada."
        exit 1
    fi
fi

copia="/root/particiones-antes-de-uefi-$(date +%Y%m%d-%H%M%S).txt"
[ -n "$PRUEBA_DISCO" ] && copia="${TMPDIR:-/tmp}/particiones-prueba.txt"
sfdisk --dump "$disco" > "$copia"
verde "==> Copia de la tabla de particiones en $copia"

if [ -z "$PRUEBA_DISCO" ]; then
    verde "==> Pasando la swap a un archivo..."
    if [ ! -f /swapfile ]; then
        fallocate -l 1G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=1024 status=none
        chmod 600 /swapfile
        mkswap /swapfile >/dev/null
    fi
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    swapon /swapfile 2>/dev/null || true
    uuid_swap=$(blkid -o value -s UUID "$swap" || true)
    swapoff "$swap" 2>/dev/null || true
    [ -n "$uuid_swap" ] && sed -i "/^UUID=${uuid_swap}[[:space:]]/s/^/# (TeleVieja: ahora es \/swapfile) /" /etc/fstab
    sed -i "\#^${swap}[[:space:]]#s/^/# (TeleVieja: ahora es \/swapfile) /" /etc/fstab
    if [ -f /etc/initramfs-tools/conf.d/resume ]; then
        echo "RESUME=none" > /etc/initramfs-tools/conf.d/resume
        update-initramfs -u
    fi
fi

verde "==> Cambiando las particiones..."
sfdisk --no-reread --delete "$disco" "$num_swap" >/dev/null
sfdisk --no-reread --delete "$disco" "$num_extendida" >/dev/null
echo "type=ef" | sfdisk --no-reread --append "$disco" >/dev/null
partx -u "$disco" 2>/dev/null || partx -a "$disco" 2>/dev/null || true
udevadm settle 2>/dev/null || true
esp=$(buscar_esp)
fi  # fin de "hacerle lugar"

if [ -z "$esp" ] || [ ! -b "$esp" ]; then
    rojo "Las particiones cambiaron pero Linux todavía no ve la nueva."
    echo "Reiniciá la netbook y corré este script de nuevo: va a seguir desde acá."
    exit 1
fi
if [ "$(blkid -o value -s TYPE "$esp" 2>/dev/null)" != vfat ]; then
    mkfs.vfat -F 32 -n EFI "$esp" >/dev/null
fi
verde "==> Partición UEFI lista: $esp"

if [ -n "$PRUEBA_DISCO" ]; then
    echo "PRUEBA OK $esp"
    exit 0
fi

mkdir -p /boot/efi
uuid_esp=$(blkid -o value -s UUID "$esp")
grep -q '/boot/efi' /etc/fstab || echo "UUID=$uuid_esp /boot/efi vfat umask=0077,nofail 0 1" >> /etc/fstab
systemctl daemon-reload
mount /boot/efi
instalar_arranque_uefi
terminar
