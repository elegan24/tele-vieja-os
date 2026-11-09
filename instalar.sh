#!/bin/bash
# Instalador de TeleVieja OS.
# Se corre UNA vez sobre un Debian 12 recién instalado (sin escritorio):
#     sudo ./instalar.sh
# Se puede volver a correr sin problema (por ejemplo, para actualizar).
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
APP=/opt/televieja

verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
amarillo() { printf '\033[1;33m%s\033[0m\n' "$*"; }
rojo() { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" != 0 ]; then
    rojo "Corré esto con sudo:  sudo ./instalar.sh"
    exit 1
fi

USUARIO="${1:-${SUDO_USER:-}}"
if [ -z "$USUARIO" ] || [ "$USUARIO" = root ]; then
    rojo "No sé para qué usuario instalar. Usá:  sudo ./instalar.sh TU_USUARIO"
    exit 1
fi
CASA=$(getent passwd "$USUARIO" | cut -d: -f6)
if [ -z "$CASA" ]; then
    rojo "El usuario $USUARIO no existe."
    exit 1
fi

if ! grep -q 'VERSION_ID="12"' /etc/os-release 2>/dev/null; then
    amarillo "Ojo: esto está pensado para Debian 12. Sigo igual..."
fi

ARQ=$(dpkg --print-architecture)
case "$ARQ" in
    amd64) ARQ_LIBRETRO=x86_64 ;;
    i386) ARQ_LIBRETRO=x86 ;;
    *) amarillo "Arquitectura $ARQ: no bajo los emuladores extra."; ARQ_LIBRETRO="" ;;
esac

verde "==> 1/7 Instalando programas (puede tardar bastante)..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
PAQUETES=(
    xserver-xorg-core xserver-xorg-input-libinput xinit x11-xserver-utils mesa-utils
    matchbox-window-manager libgl1-mesa-dri
    python3 python3-pygame python3-qrcode python3-evdev fonts-dejavu-core
    mpv ffmpeg alsa-utils
    retroarch libretro-core-info
    libretro-nestopia libretro-snes9x libretro-genesisplusgx
    libretro-gambatte libretro-mgba
    poppler-utils libarchive-tools
    rsync ntfs-3g exfatprogs curl unzip sudo
)
# Placa de video Intel vieja (GMA 3150 y similares): su driver trae Xv, que es lo más liviano.
for d in /sys/bus/pci/devices/*; do
    if grep -q '^0x03' "$d/class" 2>/dev/null && grep -q '0x8086' "$d/vendor" 2>/dev/null; then
        PAQUETES+=(xserver-xorg-video-intel)
        break
    fi
done
apt-get install -y --no-install-recommends "${PAQUETES[@]}"

verde "==> 2/7 Copiando TeleVieja a $APP..."
rm -rf "${APP:?}/televieja" "${APP:?}/sistema" "${APP:?}/bin"
mkdir -p "$APP/cores"
cp -r "$AQUI/televieja" "$AQUI/sistema" "$AQUI/bin" "$APP/"
sed -i "s/@USUARIO@/$USUARIO/" "$APP/bin/importar-usb.sh" "$APP/bin/disco-usb.sh"
chown -R root:root "$APP"
chmod 755 "$APP/bin/"*.sh
find "$APP" -name '__pycache__' -prune -exec rm -rf {} +

verde "==> 3/7 Bajando emuladores que no vienen en Debian (Neo Geo, PlayStation, Super Nintendo liviano, GBA)..."
if [ -n "$ARQ_LIBRETRO" ]; then
    for core in fbneo snes9x2010 gpsp pcsx_rearmed mupen64plus_next; do
        if [ -f "$APP/cores/${core}_libretro.so" ]; then
            echo "   $core ya estaba."
            continue
        fi
        url="https://buildbot.libretro.com/nightly/linux/$ARQ_LIBRETRO/latest/${core}_libretro.so.zip"
        tmp=$(mktemp -d)
        if curl -fsSL --retry 3 -o "$tmp/core.zip" "$url" && unzip -oq "$tmp/core.zip" -d "$tmp"; then
            install -m 644 "$tmp/${core}_libretro.so" "$APP/cores/"
            echo "   $core listo."
        else
            amarillo "   No pude bajar $core (¿hay internet?). Se usa el de Debian si existe."
        fi
        rm -rf "$tmp"
    done
fi

# Nombres completos de los juegos de arcade ("sfa.zip" -> "Street Fighter Alpha")
mkdir -p "$APP/datos"
if curl -fsSL --retry 3 -o "$APP/datos/arcade.dat.tmp" \
    "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat/fbneo-split/FBNeo%20-%20Arcade%20Games.dat"; then
    mv "$APP/datos/arcade.dat.tmp" "$APP/datos/arcade.dat"
    echo "   Nombres de los juegos de arcade listos."
else
    rm -f "$APP/datos/arcade.dat.tmp"
    amarillo "   No pude bajar los nombres de arcade: se van a ver los nombres cortos (sfa, mslug...)."
fi

# Wine, para juegos viejos de Windows (Sonic R de PC, etc.). Ocupa bastante:
# para no instalarlo, corré el instalador así:  sudo SIN_WINE=1 ./instalar.sh
if [ "${SIN_WINE:-0}" != 1 ]; then
    verde "   Instalando Wine (juegos de PC)..."
    if [ "$ARQ" = amd64 ]; then
        dpkg --add-architecture i386
        apt-get update
        apt-get install -y --no-install-recommends wine wine64 wine32:i386 libwine:i386 \
            fonts-wine libgl1-mesa-dri:i386 libasound2-plugins:i386 libsdl2-2.0-0:i386 \
            || amarillo "   No se pudo instalar Wine: los juegos de PC no van a andar."
    else
        apt-get install -y --no-install-recommends wine wine32 fonts-wine libasound2-plugins \
            || amarillo "   No se pudo instalar Wine: los juegos de PC no van a andar."
    fi
fi

verde "==> 4/7 Creando carpetas en $CASA/TeleVieja..."
R="$CASA/TeleVieja"
sudo -u "$USUARIO" mkdir -p \
    "$R/Videos" "$R/Canal/Programas" "$R/Canal/Tandas" \
    "$R/Juegos/Family" "$R/Juegos/SuperNintendo" "$R/Juegos/Sega" \
    "$R/Juegos/GameBoy" "$R/Juegos/GameBoyAdvance" "$R/Juegos/NeoGeo" "$R/Juegos/PlayStation" \
    "$R/Juegos/Nintendo64" "$R/Juegos/Arcade" "$R/Juegos/PC" \
    "$R/Historietas" "$R/Radio" "$R/Partidas" "$R/BIOS" \
    "$CASA/.config/televieja" "$CASA/.config/mpv"

instalar_archivo() {  # instalar_archivo ORIGEN DESTINO [no-pisar]
    if [ "${3:-}" = no-pisar ] && [ -f "$2" ]; then return; fi
    install -o "$USUARIO" -g "$USUARIO" -m 644 "$1" "$2"
}

if [ ! -f "$CASA/.config/televieja/opciones.conf" ]; then
    cat > "$CASA/.config/televieja/opciones.conf" <<'EOF'
# Opciones de TeleVieja OS. Después de cambiar algo, reiniciá.
NOMBRE_CANAL=TELE VIEJA
# Mostrar la hora en el Canal Retro (si/no)
CANAL_RELOJ=si
# Al entrar al canal, agarrar el programa empezado (si/no)
CANAL_EMPEZADO=si
# Cuántas publicidades pasar entre programa y programa
TANDAS_POR_CORTE=2
# Qué aparece al prender: menu o canal
ARRANCAR_EN=menu
SONIDOS_MENU=si
# Resolución para la tele. Si el conversor no la toma, probá 800x600
RESOLUCION=640x480
# Manejar la tele desde el celular (mismo WiFi): si/no y puerto
CONTROL_CELULAR=si
PUERTO_CELULAR=8080
# Nintendo 64 (experimental): auto = solo si la placa de video puede; si / no para forzar
N64=auto
# Juegos de PC: mostrarlos en una ventana del tamaño de la pantalla (si) o dejar que
# cambien la resolución (no). Con "si" la tele y el conversor no se enteran.
PC_ESCRITORIO_VIRTUAL=si
EOF
    chown "$USUARIO:$USUARIO" "$CASA/.config/televieja/opciones.conf"
fi
sed -e "s#@RAIZ@#$R#g" -e "s#@CONFIG@#$CASA/.config/televieja#g" \
    "$APP/sistema/retroarch.cfg" > "$CASA/.config/televieja/retroarch.cfg"
chown "$USUARIO:$USUARIO" "$CASA/.config/televieja/retroarch.cfg"
# Opciones de los emuladores (PS1 afinado para el Atom). No pisa cambios tuyos.
instalar_archivo "$APP/sistema/retroarch-core-options.cfg" \
    "$CASA/.config/televieja/retroarch-core-options.cfg" no-pisar
instalar_archivo "$APP/sistema/mpv/mpv.conf" "$CASA/.config/mpv/mpv.conf"
instalar_archivo "$APP/sistema/mpv/input.conf" "$CASA/.config/mpv/input.conf"
install -o "$USUARIO" -g "$USUARIO" -m 755 "$APP/sistema/xinitrc" "$CASA/.xinitrc"

verde "==> 5/7 Arranque automático (sin pedir contraseña)..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USUARIO --noclear %I \$TERM
EOF
PERFIL="$CASA/.bash_profile"
touch "$PERFIL"
chown "$USUARIO:$USUARIO" "$PERFIL"
if ! grep -q 'TELEVIEJA' "$PERFIL"; then
    cat >> "$PERFIL" <<'EOF'

# --- TELEVIEJA: arrancar el menú en la pantalla 1 ---
[ -f ~/.profile ] && . ~/.profile
if [ -z "${DISPLAY:-}" ] && [ "$(tty)" = /dev/tty1 ]; then
    rm -f /tmp/televieja-terminal
    startx -- -nocursor >/dev/null 2>&1
    if [ ! -e /tmp/televieja-terminal ]; then
        logout
    fi
    echo "Saliste a la terminal. Para volver al menú escribí:  startx"
fi
# --- fin TELEVIEJA ---
EOF
fi

verde "==> 6/7 Permisos (joystick, sonido, apagar, discos USB)..."
usermod -aG input,audio,video "$USUARIO"
cat > /etc/sudoers.d/televieja <<EOF
$USUARIO ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff, /usr/bin/systemctl reboot, $APP/bin/importar-usb.sh
EOF
chmod 440 /etc/sudoers.d/televieja
visudo -cf /etc/sudoers.d/televieja >/dev/null
# Volumen al máximo y sin silencio (se ajusta con la perilla de la tele)
amixer -q sset Master 90% unmute 2>/dev/null || true
amixer -q sset PCM 90% unmute 2>/dev/null || true
alsactl store 2>/dev/null || true

# Celular como joystick: necesita el módulo uinput y permiso para el grupo "input".
echo uinput > /etc/modules-load.d/televieja.conf
cat > /etc/udev/rules.d/99-televieja-uinput.rules <<'EOF'
KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"
EOF
modprobe uinput 2>/dev/null || true

# Discos USB: se montan solos (solo lectura) y aparecen en el menú.
install -m 644 "$APP/sistema/99-televieja-usb.rules" /etc/udev/rules.d/
install -m 644 "$APP/sistema/televieja-disco@.service" /etc/systemd/system/
systemctl daemon-reload
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger --subsystem-match=block --action=add 2>/dev/null || true
udevadm trigger --subsystem-match=misc --sysname-match=uinput --action=add 2>/dev/null || true

verde "==> 7/7 Arranque silencioso..."
if [ -f /etc/default/grub ]; then
    sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' /etc/default/grub
    sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 vt.global_cursor_default=0"/' /etc/default/grub
    update-grub 2>/dev/null || true
fi

echo
verde "¡Listo! Reiniciá con:  sudo reboot"
echo "Cargá tus cosas en $R (o con un pendrive desde el menú)."
