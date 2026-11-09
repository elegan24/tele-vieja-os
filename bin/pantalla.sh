#!/bin/bash
# Elige dónde se ve la imagen: la tele (salida VGA) o la pantalla de la netbook.
# Uso: pantalla.sh [auto|tele|netbook|alternar]
modo="${1:-auto}"
ESTADO=/tmp/televieja-pantalla
OPCIONES="$HOME/.config/televieja/opciones.conf"

RESOLUCION=640x480
if [ -f "$OPCIONES" ]; then
    valor=$(grep -E '^RESOLUCION=' "$OPCIONES" | tail -n1 | cut -d= -f2 | tr -d '"'"'"' ')
    [ -n "$valor" ] && RESOLUCION="$valor"
fi

consulta=$(xrandr --query 2>/dev/null) || exit 1
internas=$(echo "$consulta" | awk '$2 == "connected" && $1 ~ /^(LVDS|eDP|DSI)/ {print $1}')
externas=$(echo "$consulta" | awk '$2 == "connected" && $1 !~ /^(LVDS|eDP|DSI)/ {print $1}')
interna=$(echo "$internas" | head -n1)
externa=$(echo "$externas" | head -n1)

poner_modo() {  # agrega la resolución si la salida no la ofrece (pasa con algunos conversores)
    local salida="$1" res="$2"
    if xrandr --output "$salida" --mode "$res" 2>/dev/null; then
        return 0
    fi
    local ancho="${res%x*}" alto="${res#*x}"
    local linea nombre resto
    linea=$(cvt "$ancho" "$alto" 60 | grep Modeline | sed 's/Modeline //')
    nombre=$(echo "$linea" | awk '{print $1}' | tr -d '"')
    resto=$(echo "$linea" | cut -d' ' -f2-)
    # shellcheck disable=SC2086
    xrandr --newmode "$nombre" $resto 2>/dev/null
    xrandr --addmode "$salida" "$nombre" 2>/dev/null
    xrandr --output "$salida" --mode "$nombre"
}

usar_tele() {
    [ -n "$externa" ] || return 1
    poner_modo "$externa" "$RESOLUCION" || return 1
    xrandr --output "$externa" --primary
    for i in $internas; do xrandr --output "$i" --off; done
    echo tele > "$ESTADO"
}

usar_netbook() {
    [ -n "$interna" ] || return 1
    xrandr --output "$interna" --auto --primary
    for e in $externas; do xrandr --output "$e" --off; done
    echo netbook > "$ESTADO"
}

case "$modo" in
    tele) usar_tele || usar_netbook ;;
    netbook) usar_netbook || usar_tele ;;
    alternar)
        if [ "$(cat "$ESTADO" 2>/dev/null)" = tele ]; then
            usar_netbook || usar_tele
        else
            usar_tele || usar_netbook
        fi ;;
    *) usar_tele || usar_netbook ;;
esac
