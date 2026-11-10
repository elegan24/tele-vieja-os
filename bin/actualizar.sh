#!/bin/bash
# Actualiza TeleVieja desde GitHub: baja lo nuevo, corre el instalador y listo.
# Lo llama el menú ("Actualizar TeleVieja") con sudo, sin contraseña. No recibe argumentos.
set -u
USUARIO="@USUARIO@"
REPO="https://github.com/elegan24/tele-vieja-os.git"
FUENTE=/var/lib/televieja/fuente
LOG=/var/log/televieja-actualizar.log

mkdir -p "$(dirname "$FUENTE")"
exec > >(tee "$LOG") 2>&1

echo "Buscando la versión nueva..."
if [ -d "$FUENTE/.git" ]; then
    git -C "$FUENTE" fetch --quiet origin main || { echo "No pude conectarme a GitHub (¿hay internet?)."; exit 1; }
    git -C "$FUENTE" reset --quiet --hard origin/main
else
    rm -rf "$FUENTE"
    git clone --quiet --depth 1 "$REPO" "$FUENTE" || { echo "No pude bajar TeleVieja (¿hay internet?)."; exit 1; }
fi

nueva=$(git -C "$FUENTE" rev-parse --short HEAD)
actual=$(cat /opt/televieja/VERSION 2>/dev/null || echo "ninguna")
if [ "$nueva" = "$actual" ] && [ "${1:-}" != "--forzar" ]; then
    echo "Ya tenés la última versión ($nueva)."
    exit 0
fi

echo "Instalando la versión $nueva (antes: $actual)..."
cd "$FUENTE" || exit 1
if ./instalar.sh "$USUARIO"; then
    echo "$nueva" > /opt/televieja/VERSION
    echo "LISTO"
else
    echo "Falló la actualización. Mirá $LOG"
    exit 1
fi
