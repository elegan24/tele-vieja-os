#!/bin/bash
# Pone la netbook en hora. Lo llama el menú con sudo (sin contraseña), al arrancar y
# cuando una descarga falla por la fecha. Con la fecha mal no anda internet "seguro"
# (https): los certificados parecen vencidos o del futuro.
set -u

# 1) El servicio de hora por internet (NTP)
timedatectl set-ntp true >/dev/null 2>&1 || true
systemctl restart systemd-timesyncd >/dev/null 2>&1 || true
for _ in $(seq 1 20); do
    if [ "$(timedatectl show -p NTPSynchronized --value 2>/dev/null)" = yes ]; then
        hwclock --systohc >/dev/null 2>&1 || true
        echo "En hora: $(date '+%d/%m/%Y %H:%M')"
        exit 0
    fi
    sleep 1
done

# 2) Si no anduvo, la hora que dice un servidor web (por http, que no depende de la fecha)
for sitio in http://www.google.com http://deb.debian.org; do
    fecha=$(curl -sI --max-time 10 "$sitio" | awk -F': ' 'tolower($1) == "date" {print $2}' | tr -d '\r')
    if [ -n "$fecha" ] && date -s "$fecha" >/dev/null 2>&1; then
        hwclock --systohc >/dev/null 2>&1 || true
        echo "En hora: $(date '+%d/%m/%Y %H:%M')"
        exit 0
    fi
done
echo "No pude poner la hora (¿hay internet?)"
exit 1
