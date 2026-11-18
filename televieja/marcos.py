"""Marcos (bezels) alrededor del video, estilo Super Game Boy.

El marco llena las franjas negras que deja el video (a los costados de un video 4:3 en una
pantalla ancha, o arriba y abajo de uno 16:9 en la tele): el video no se achica nunca.
Cada marco es una carpeta con PNGs (lo del centro no se ve: ahí va el video):
  - default.png: el mismo todo el día.
  - manana.png (06-12:59), tarde.png (13-19:59), noche.png (20-00:59),
    madrugada.png (01-05:59): cambian solos según la hora.
  - marco.json (opcional): {"pixelArt": true} agranda sin suavizar. Con "modo": "ventana",
    el video se achica para entrar en el hueco del dibujo (estilo Super Game Boy), con
    "anchoPorcentaje", "altoPorcentaje" (y opcional "izquierdaPorcentaje",
    "arribaPorcentaje"); sin eso, el hueco se detecta mirando lo transparente del PNG.

Los marcos vienen de sistema/marcos (los de fábrica) y de TeleVieja/Marcos (los tuyos,
también en discos USB). mpv los dibuja con overlay-add, que pide los píxeles crudos en
BGRA premultiplicado: este módulo los prepara (y los guarda en caché) para marco.lua.
"""
import datetime
import hashlib
import json
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from . import config  # noqa: E402

FRANJAS = (("madrugada", 1, 6), ("manana", 6, 13), ("tarde", 13, 20))  # el resto: noche
NOMBRES_HORARIO = ("manana", "tarde", "noche", "madrugada")
VENTANA_POR_DEFECTO = (12.5, 0.0, 75.0, 100.0)  # izquierda, arriba, ancho, alto (%): 4:3 en 16:9


def carpetas_base():
    return [os.path.join(config.SISTEMA_DIR, "marcos")] + \
        [os.path.join(r, "Marcos") for r in config.raices()]


def _pngs(carpeta):
    try:
        return {os.path.splitext(n)[0].lower(): os.path.join(carpeta, n)
                for n in os.listdir(carpeta) if n.lower().endswith(".png")}
    except OSError:
        return {}


def listar():
    """Marcos disponibles: [{"nombre", "ruta", "modo" ("fijo"/"horario"), "propio"}]."""
    vistos = {}
    for base in carpetas_base():
        propio = not base.startswith(config.SISTEMA_DIR)
        try:
            nombres = sorted(os.listdir(base), key=config.clave_natural)
        except OSError:
            continue
        for n in nombres:
            ruta = os.path.join(base, n)
            pngs = _pngs(ruta)
            if not os.path.isdir(ruta) or not ("default" in pngs or
                                               any(h in pngs for h in NOMBRES_HORARIO)):
                continue
            modo = "horario" if any(h in pngs for h in NOMBRES_HORARIO) else "fijo"
            vistos[n] = {"nombre": n, "ruta": ruta, "modo": modo, "propio": propio}
    return sorted(vistos.values(), key=lambda m: config.clave_natural(m["nombre"]))


def buscar(nombre):
    for m in listar():
        if m["nombre"] == nombre:
            return m["ruta"]
    return None


def franja(cuando=None):
    hora = (cuando or datetime.datetime.now()).hour
    for nombre, desde, hasta in FRANJAS:
        if desde <= hora < hasta:
            return nombre
    return "noche"


def elegir_png(carpeta, cuando=None):
    """El PNG que va ahora: el de la franja horaria, si no default.png, si no cualquiera."""
    pngs = _pngs(carpeta)
    actual = franja(cuando)
    if actual in pngs:
        return pngs[actual]
    if "default" in pngs:
        return pngs["default"]
    for h in NOMBRES_HORARIO:
        if h in pngs:
            return pngs[h]
    return None


def leer_config(carpeta):
    try:
        with open(os.path.join(carpeta, "marco.json"), encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def _porcentaje(valor):
    try:
        return max(0.0, min(100.0, float(str(valor).strip().rstrip("%"))))
    except ValueError:
        return None


def ventana_del_diseno(imagen, cfg):
    """Dónde va el video, en píxeles del PNG original: (x, y, ancho, alto)."""
    pw, ph = imagen.get_size()
    ancho, alto = _porcentaje(cfg.get("anchoPorcentaje")), _porcentaje(cfg.get("altoPorcentaje"))
    if ancho and alto:
        izq = _porcentaje(cfg.get("izquierdaPorcentaje"))
        arriba = _porcentaje(cfg.get("arribaPorcentaje"))
        izq = (100 - ancho) / 2 if izq is None else izq
        arriba = (100 - alto) / 2 if arriba is None else arriba
        return (pw * izq / 100, ph * arriba / 100, pw * ancho / 100, ph * alto / 100)
    hueco = detectar_hueco(imagen)
    if hueco:
        return hueco
    izq, arriba, ancho, alto = VENTANA_POR_DEFECTO
    return (pw * izq / 100, ph * arriba / 100, pw * ancho / 100, ph * alto / 100)


def detectar_hueco(imagen):
    """El hueco transparente del centro: se mide desde el centro hacia los cuatro lados."""
    pw, ph = imagen.get_size()
    cx, cy = pw // 2, ph // 2

    def transparente(x, y):
        return imagen.get_at((x, y)).a < 128

    if not transparente(cx, cy):
        return None
    x0 = cx
    while x0 > 0 and transparente(x0 - 1, cy):
        x0 -= 1
    x1 = cx
    while x1 < pw - 1 and transparente(x1 + 1, cy):
        x1 += 1
    y0 = cy
    while y0 > 0 and transparente(cx, y0 - 1):
        y0 -= 1
    y1 = cy
    while y1 < ph - 1 and transparente(cx, y1 + 1):
        y1 += 1
    return (x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def _bgra_premultiplicado(sup):
    """Los píxeles como los pide mpv: B, G, R, A con el color ya multiplicado por el alfa."""
    import pygame
    ancho, alto = sup.get_size()
    rgba = pygame.image.tostring(sup, "RGBA")
    sobre_negro = pygame.Surface((ancho, alto))       # pintar sobre negro = color × alfa
    sobre_negro.fill((0, 0, 0))
    sobre_negro.blit(sup, (0, 0))
    rgb = pygame.image.tostring(sobre_negro, "RGB")
    salida = bytearray(ancho * alto * 4)
    salida[0::4] = rgb[2::3]
    salida[1::4] = rgb[1::3]
    salida[2::4] = rgb[0::3]
    salida[3::4] = rgba[3::4]
    return bytes(salida)


def color_de_fondo(imagen):
    """El color promedio de lo que no es transparente (para rellenar los agujeros)."""
    import pygame
    chica = pygame.transform.scale(imagen, (32, 32))
    r = g = b = n = 0
    for x in range(32):
        for y in range(32):
            c = chica.get_at((x, y))
            if c.a >= 128:
                r, g, b, n = r + c.r, g + c.g, b + c.b, n + 1
    return (r // n, g // n, b // n, 255) if n else (0, 0, 0, 255)


def rectangulo_del_video(ancho, alto, aspecto):
    """Dónde queda el video en la pantalla (sin achicarlo): (x0, y0, x1, y1)."""
    vw = min(ancho, alto * aspecto)
    vh = vw / aspecto
    x0, y0 = (ancho - vw) / 2, (alto - vh) / 2
    return x0, y0, x0 + vw, y0 + vh


def preparar(carpeta, ancho, alto, cache, cuando=None, aspecto=None):
    """Deja el marco listo para una pantalla de ancho×alto.

    Normal ("relleno"): el video queda en su tamaño de siempre y el marco tapa solo las
    franjas negras que deja (a los costados o arriba y abajo): se le hace un hueco del
    tamaño del video. Con {"modo": "ventana"} en marco.json, en cambio, el video se
    achica para entrar en el hueco del dibujo (estilo Super Game Boy).

    Devuelve {"archivo": .bgra, "ancho", "alto", "ventana": [izq, arriba, der, abajo]
    (márgenes del video, en fracciones), "modo", "png"} o None si no hay marco."""
    import pygame
    png = elegir_png(carpeta, cuando)
    if not png:
        return None
    cfg = leer_config(carpeta)
    pixel_art = bool(cfg.get("pixelArt"))
    modo = "ventana" if str(cfg.get("modo", "")).lower() == "ventana" else "relleno"
    original = pygame.image.load(png)
    if original.get_bitsize() not in (24, 32) or original.get_alpha() is None:
        original = original.convert(32, pygame.SRCALPHA)
    # "cover": llena la pantalla sin deformar (si la pantalla es 4:3 y el marco 16:9,
    # se recortan los costados)
    pw, ph = original.get_size()
    escala = max(ancho / pw, alto / ph)
    tam = (max(1, round(pw * escala)), max(1, round(ph * escala)))
    ox, oy = (ancho - tam[0]) / 2, (alto - tam[1]) / 2
    if modo == "ventana":
        vx, vy, vw, vh = ventana_del_diseno(original, cfg)
        x0, y0 = max(0.0, vx * escala + ox), max(0.0, vy * escala + oy)
        x1, y1 = min(ancho, (vx + vw) * escala + ox), min(alto, (vy + vh) * escala + oy)
        hueco = None
    else:
        x0, y0, x1, y1 = rectangulo_del_video(ancho, alto, aspecto or 4 / 3)
        # un píxel para adentro: que el marco pise el borde del video y no quede una raya negra
        hueco = pygame.Rect(int(x0) + 1, int(y0) + 1, max(0, int(x1) - int(x0) - 2),
                            max(0, int(y1) - int(y0) - 2))
    ventana = [x0 / ancho, y0 / alto, (ancho - x1) / ancho, (alto - y1) / alto]

    clave = "%s|%s|%dx%d|%s|%s|%s" % (png, os.path.getmtime(png), ancho, alto, pixel_art, modo,
                                      tuple(hueco) if hueco else "")
    archivo = os.path.join(cache, hashlib.sha1(clave.encode()).hexdigest()[:16] + ".bgra")
    if not os.path.exists(archivo):
        if pixel_art:
            grande = pygame.transform.scale(original, tam)        # sin suavizar: píxeles nítidos
        else:
            grande = pygame.transform.smoothscale(original, tam)
        lienzo = pygame.Surface((ancho, alto), pygame.SRCALPHA, 32)
        lienzo.fill((0, 0, 0, 0))
        if hueco:
            # si el dibujo tiene partes transparentes (un PNG hecho con el centro vacío),
            # que en las franjas se vea el color del marco y no negro
            lienzo.fill(color_de_fondo(original))
        lienzo.blit(grande, (round(ox), round(oy)))
        if hueco:
            lienzo.fill((0, 0, 0, 0), hueco)   # ahí se ve el video, entero
        os.makedirs(cache, exist_ok=True)
        temporal = archivo + ".tmp"
        with open(temporal, "wb") as f:
            f.write(_bgra_premultiplicado(lienzo))
        os.replace(temporal, archivo)
        _limpiar_cache(cache)
    return {"archivo": archivo, "ancho": ancho, "alto": alto, "ventana": ventana, "modo": modo,
            "png": png}


def _limpiar_cache(cache, guardar=8):
    try:
        viejos = sorted((os.path.join(cache, n) for n in os.listdir(cache) if n.endswith(".bgra")),
                        key=os.path.getmtime, reverse=True)
    except OSError:
        return
    for ruta in viejos[guardar:]:
        try:
            os.remove(ruta)
        except OSError:
            pass


def main(args):
    """marco.py preparar CARPETA ANCHO ALTO CACHE [ASPECTO_DEL_VIDEO]  -> JSON para marco.lua"""
    if len(args) in (5, 6) and args[0] == "preparar":
        try:
            aspecto = float(args[5]) if len(args) == 6 else None
            datos = preparar(args[1], int(args[2]), int(args[3]), args[4], aspecto=aspecto)
        except Exception as e:  # noqa: BLE001 - marco.lua solo necesita saber que no hay marco
            datos = {"error": str(e)}
        print(json.dumps(datos))
        return 0
    print(json.dumps({"error": "uso: marco.py preparar CARPETA ANCHO ALTO CACHE"}))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
