"""Rutas, opciones y lista de consolas de TeleVieja OS."""
import glob
import os
import re

HOME = os.path.expanduser("~")
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.environ.get("TELEVIEJA_RAIZ", os.path.join(HOME, "TeleVieja"))
CONFIG_DIR = os.environ.get("TELEVIEJA_CONFIG", os.path.join(HOME, ".config", "televieja"))
CACHE_DIR = os.path.join(HOME, ".cache", "televieja")
CORES_DIR = os.path.join(APP_DIR, "cores")
SISTEMA_DIR = os.path.join(APP_DIR, "sistema")
BIN_DIR = os.path.join(APP_DIR, "bin")

ARCHIVO_OPCIONES = os.path.join(CONFIG_DIR, "opciones.conf")
ARCHIVO_JOYSTICK = os.path.join(CONFIG_DIR, "joystick.json")
ARCHIVO_RA_JOYSTICK = os.path.join(CONFIG_DIR, "retroarch-joystick.cfg")
ARCHIVO_RA = os.path.join(CONFIG_DIR, "retroarch.cfg")
ARCHIVO_HISTORIETAS = os.path.join(CONFIG_DIR, "historietas.json")
AUTOCONFIG_DIR = os.path.join(CONFIG_DIR, "autoconfig")

CARPETA_VIDEOS = os.path.join(RAIZ, "Videos")
CARPETA_PROGRAMAS = os.path.join(RAIZ, "Canal", "Programas")
CARPETA_TANDAS = os.path.join(RAIZ, "Canal", "Tandas")
CARPETA_JUEGOS = os.path.join(RAIZ, "Juegos")
CARPETA_HISTORIETAS = os.path.join(RAIZ, "Historietas")
CARPETA_RADIO = os.path.join(RAIZ, "Radio")

EXT_VIDEO = (".mp4", ".mkv", ".avi", ".mpg", ".mpeg", ".wmv", ".mov", ".m4v",
             ".flv", ".webm", ".vob", ".3gp", ".ogv", ".ts", ".divx", ".rmvb", ".rm")
EXT_AUDIO = (".mp3", ".ogg", ".oga", ".opus", ".wav", ".flac", ".m4a", ".aac",
             ".wma", ".mka")
EXT_IMAGEN = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
EXT_HISTORIETA = (".cbz", ".cbr", ".cb7", ".zip", ".rar", ".7z", ".pdf")

OPCIONES_POR_DEFECTO = {
    "NOMBRE_CANAL": "TELE VIEJA",
    "CANAL_RELOJ": "si",
    "CANAL_EMPEZADO": "si",
    "TANDAS_POR_CORTE": "2",
    "ARRANCAR_EN": "menu",
    "SONIDOS_MENU": "si",
    "RESOLUCION": "640x480",
    "CONTROL_CELULAR": "si",
    "PUERTO_CELULAR": "8080",
}

# Consolas: la primera "core" que esté instalada es la que se usa.
SISTEMAS = [
    {"id": "nes", "nombre": "Family / NES", "carpeta": "Family",
     "ext": (".nes", ".zip"), "cores": ["nestopia", "fceumm"]},
    {"id": "snes", "nombre": "Super Nintendo", "carpeta": "SuperNintendo",
     "ext": (".smc", ".sfc", ".zip"), "cores": ["snes9x2010", "snes9x"]},
    {"id": "sega", "nombre": "Sega (Genesis / Master System)", "carpeta": "Sega",
     "ext": (".md", ".gen", ".smd", ".bin", ".sms", ".gg", ".zip"),
     "cores": ["genesis_plus_gx"]},
    {"id": "gb", "nombre": "Game Boy / Color", "carpeta": "GameBoy",
     "ext": (".gb", ".gbc", ".zip"), "cores": ["gambatte"]},
    {"id": "gba", "nombre": "Game Boy Advance", "carpeta": "GameBoyAdvance",
     "ext": (".gba", ".zip"), "cores": ["gpsp", "mgba"]},
    {"id": "neogeo", "nombre": "Neo Geo", "carpeta": "NeoGeo",
     "ext": (".zip",), "cores": ["fbneo"], "excluir": ("neogeo.zip",)},
]


# Discos USB: los monta solos bin/disco-usb.sh (solo lectura) en esta carpeta.
MONTAJES = os.environ.get("TELEVIEJA_MONTAJES", "/media/televieja")


def _decodificar_etiqueta(texto):
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), texto)


def _etiquetas():
    """Nombre de cada disco (la "etiqueta" que le pusiste) según su UUID."""
    por_dispositivo = {}
    try:
        for e in os.listdir("/dev/disk/by-label"):
            real = os.path.realpath(os.path.join("/dev/disk/by-label", e))
            por_dispositivo[real] = _decodificar_etiqueta(e)
    except OSError:
        return {}
    por_uuid = {}
    try:
        for u in os.listdir("/dev/disk/by-uuid"):
            real = os.path.realpath(os.path.join("/dev/disk/by-uuid", u))
            if real in por_dispositivo:
                por_uuid[u] = por_dispositivo[real]
    except OSError:
        pass
    return por_uuid


def discos_externos():
    """Discos USB conectados. Cada uno: {"id", "nombre", "punto", "raiz"}.

    "raiz" es su carpeta TeleVieja (o None si el disco no tiene una).
    """
    try:
        ids = sorted(os.listdir(MONTAJES))
    except OSError:
        return []
    etiquetas = None
    discos = []
    for ident in ids:
        punto = os.path.join(MONTAJES, ident)
        try:
            contenido = os.listdir(punto)
        except OSError:
            continue
        if not contenido:  # carpeta vacía: no hay nada montado
            continue
        raiz = next((os.path.join(punto, n) for n in contenido
                     if n.lower() == "televieja" and os.path.isdir(os.path.join(punto, n))), None)
        if etiquetas is None:
            etiquetas = _etiquetas()
        discos.append({"id": ident, "nombre": etiquetas.get(ident, ident), "punto": punto, "raiz": raiz})
    return discos


def raices():
    """La carpeta TeleVieja de la netbook más las de los discos USB."""
    return [RAIZ] + [d["raiz"] for d in discos_externos() if d["raiz"]]


def listar_en_todas(partes, extensiones):
    """Busca archivos en la misma subcarpeta de todas las raíces (netbook + discos)."""
    archivos = []
    for r in raices():
        archivos += listar_archivos(os.path.join(r, *partes), extensiones)
    return archivos


def leer_opciones():
    opciones = dict(OPCIONES_POR_DEFECTO)
    try:
        with open(ARCHIVO_OPCIONES, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave, valor = linea.split("=", 1)
                opciones[clave.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return opciones


def opcion_si(opciones, clave):
    return opciones.get(clave, "").lower() in ("si", "sí", "1", "yes", "true")


def carpetas_de_cores():
    dirs = [CORES_DIR]
    dirs += sorted(glob.glob("/usr/lib/*/libretro"))
    dirs += ["/usr/lib/libretro", "/usr/local/lib/libretro"]
    return dirs


def buscar_core(nombres):
    for nombre in nombres:
        for d in carpetas_de_cores():
            ruta = os.path.join(d, nombre + "_libretro.so")
            if os.path.isfile(ruta):
                return ruta
    return None


def clave_natural(texto):
    """Ordena "Capitulo 2" antes que "Capitulo 10"."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", texto)]


def nombre_lindo(nombre_archivo):
    base = os.path.splitext(nombre_archivo)[0]
    if " " not in base:
        base = base.replace("_", " ").replace(".", " ")
    return base.strip() or nombre_archivo


def listar_archivos(carpeta, extensiones, recursivo=True):
    encontrados = []
    if not os.path.isdir(carpeta):
        return encontrados
    if recursivo:
        for raiz, subdirs, archivos in os.walk(carpeta):
            subdirs[:] = [d for d in subdirs if not d.startswith(".")]
            for a in archivos:
                if a.lower().endswith(extensiones) and not a.startswith("."):
                    encontrados.append(os.path.join(raiz, a))
    else:
        for a in os.listdir(carpeta):
            ruta = os.path.join(carpeta, a)
            if os.path.isfile(ruta) and a.lower().endswith(extensiones) and not a.startswith("."):
                encontrados.append(ruta)
    encontrados.sort(key=lambda p: clave_natural(os.path.relpath(p, carpeta)))
    return encontrados
