"""Marcos (bezels) alrededor del video, estilo Super Game Boy.

Cada marco es una carpeta con PNGs que tienen el centro transparente (ahí va el video):
  - default.png: el mismo todo el día.
  - manana.png (06-12:59), tarde.png (13-19:59), noche.png (20-00:59),
    madrugada.png (01-05:59): cambian solos según la hora.
  - marco.json (opcional): {"pixelArt": true, "anchoPorcentaje": 75, "altoPorcentaje": 100,
    "izquierdaPorcentaje": 12.5, "arribaPorcentaje": 0}. Sin él, la ventana del video se
    detecta sola mirando el hueco transparente del PNG.

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


def preparar(carpeta, ancho, alto, cache, cuando=None):
    """Deja el marco listo para una pantalla de ancho×alto. Devuelve:
    {"archivo": .bgra, "ancho", "alto", "ventana": [izq, arriba, der, abajo] (fracciones de
    margen, como video-margin-ratio de mpv), "png"} o None si no hay marco."""
    import pygame
    png = elegir_png(carpeta, cuando)
    if not png:
        return None
    cfg = leer_config(carpeta)
    pixel_art = bool(cfg.get("pixelArt"))
    original = pygame.image.load(png)
    if original.get_bitsize() not in (24, 32) or original.get_alpha() is None:
        original = original.convert(32, pygame.SRCALPHA)
    # "cover": llena la pantalla sin deformar (si la pantalla es 4:3 y el marco 16:9,
    # se recortan los costados)
    pw, ph = original.get_size()
    escala = max(ancho / pw, alto / ph)
    tam = (max(1, round(pw * escala)), max(1, round(ph * escala)))
    ox, oy = (ancho - tam[0]) / 2, (alto - tam[1]) / 2
    vx, vy, vw, vh = ventana_del_diseno(original, cfg)
    x0, y0 = max(0.0, vx * escala + ox), max(0.0, vy * escala + oy)
    x1, y1 = min(ancho, (vx + vw) * escala + ox), min(alto, (vy + vh) * escala + oy)
    ventana = [x0 / ancho, y0 / alto, (ancho - x1) / ancho, (alto - y1) / alto]

    clave = "%s|%s|%dx%d|%s" % (png, os.path.getmtime(png), ancho, alto, pixel_art)
    archivo = os.path.join(cache, hashlib.sha1(clave.encode()).hexdigest()[:16] + ".bgra")
    if not os.path.exists(archivo):
        if pixel_art:
            grande = pygame.transform.scale(original, tam)        # sin suavizar: píxeles nítidos
        else:
            grande = pygame.transform.smoothscale(original, tam)
        lienzo = pygame.Surface((ancho, alto), pygame.SRCALPHA, 32)
        lienzo.fill((0, 0, 0, 0))
        lienzo.blit(grande, (round(ox), round(oy)))
        os.makedirs(cache, exist_ok=True)
        temporal = archivo + ".tmp"
        with open(temporal, "wb") as f:
            f.write(_bgra_premultiplicado(lienzo))
        os.replace(temporal, archivo)
        _limpiar_cache(cache)
    return {"archivo": archivo, "ancho": ancho, "alto": alto, "ventana": ventana, "png": png}


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
    """marco.py preparar CARPETA ANCHO ALTO CACHE  -> una línea JSON para marco.lua"""
    if len(args) == 5 and args[0] == "preparar":
        try:
            datos = preparar(args[1], int(args[2]), int(args[3]), args[4])
        except Exception as e:  # noqa: BLE001 - marco.lua solo necesita saber que no hay marco
            datos = {"error": str(e)}
        print(json.dumps(datos))
        return 0
    print(json.dumps({"error": "uso: marco.py preparar CARPETA ANCHO ALTO CACHE"}))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
