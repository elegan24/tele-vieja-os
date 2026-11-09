#!/bin/bash
# Copia el WiFi que configuró el instalador de Debian a NetworkManager.
#
# El instalador de Debian ata el WiFi al nombre de la placa (por ejemplo "wlp2s0").
# Si el disco pasa a otra netbook, la placa se llama distinto y se queda sin WiFi.
# NetworkManager guarda la red sin atarla a ninguna placa: anda en cualquier netbook.
# (En esta netbook sigue mandando la configuración de Debian; NetworkManager solo
# se ocupa de las placas que Debian no conoce.)
set -u
ARCHIVO=/etc/NetworkManager/system-connections/televieja-wifi.nmconnection

[ -d /etc/NetworkManager/system-connections ] || exit 0
[ -f "$ARCHIVO" ] && exit 0

leer() {  # leer CLAVE -> primer valor encontrado en la config de red de Debian
    grep -hE "^[[:space:]]*$1[[:space:]]" /etc/network/interfaces /etc/network/interfaces.d/* 2>/dev/null |
        head -n1 | sed -E "s/^[[:space:]]*$1[[:space:]]+//; s/^\"(.*)\"$/\1/"
}
ssid=$(leer wpa-ssid)
clave=$(leer wpa-psk)
if [ -z "$ssid" ] || [ -z "$clave" ]; then
    echo "   No hay WiFi configurado por el instalador de Debian (¿instalaste por cable?)."
    exit 0
fi

umask 077
cat > "$ARCHIVO" <<EOF
[connection]
id=TeleVieja WiFi
uuid=$(cat /proc/sys/kernel/random/uuid)
type=wifi
autoconnect=true

[wifi]
mode=infrastructure
ssid=$ssid

[wifi-security]
key-mgmt=wpa-psk
psk=$clave

[ipv4]
method=auto

[ipv6]
method=auto
EOF
chmod 600 "$ARCHIVO"
nmcli connection reload >/dev/null 2>&1 || true
echo "   WiFi \"$ssid\" guardado para cualquier netbook."
