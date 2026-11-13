"""Rutas, opciones y lista de consolas de TeleVieja OS."""
import glob
import os
import re
import subprocess

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
    "NOMBRE_CANAL": "FRECUENCIA 99",
    "CANAL_RELOJ": "si",
    "CANAL_EMPEZADO": "si",
    "TANDAS_POR_CORTE": "2",
    "ARRANCAR_EN": "menu",
    "SONIDOS_MENU": "si",
    "RESOLUCION": "640x480",
    "CONTROL_CELULAR": "si",
    "N64": "auto",
    "TEMA": "auto",
    "EFECTO_ENCENDIDO": "si",
    "PROTECTOR_MINUTOS": "5",
    "PC_ESCRITORIO_VIRTUAL": "si",
    "DESCARGAS_PARALELAS": "4",
    "PUERTO_CELULAR": "8080",
}

# Archivos de BIOS de las placas arcade: no son juegos, no se muestran en la lista.
BIOS_ARCADE = tuple(n + ext for n in (
    "neogeo", "pgm", "skns", "decocass", "isgsm", "nmk004", "ym2608", "cchip", "midssio",
    "bubsys", "namcoc69", "namcoc70", "namcoc75", "neocdz", "hiscore", "qsound")
    for ext in (".zip", ".7z"))

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
     "ext": (".zip",), "cores": ["fbneo"], "excluir": ("neogeo.zip",), "nombres": "arcade"},
    {"id": "arcade", "nombre": "Arcade (fichines)", "carpeta": "Arcade",
     "ext": (".zip", ".7z"), "cores": ["fbneo"], "excluir": BIOS_ARCADE, "nombres": "arcade"},
    {"id": "ps1", "nombre": "PlayStation", "carpeta": "PlayStation",
     "ext": (".cue", ".chd", ".pbp", ".m3u", ".iso", ".img", ".bin"),
     "cores": ["pcsx_rearmed"], "discos": True},
    # Experimental: solo aparece si la placa de video puede (ver video_para_n64).
    {"id": "n64", "nombre": "Nintendo 64 (experimental)", "carpeta": "Nintendo64",
     "ext": (".z64", ".n64", ".v64", ".zip"), "cores": ["mupen64plus_next"],
     "experimental": "N64"},
    # Juegos viejos de Windows con Wine: cada juego es una carpeta (ver wine.py).
    {"id": "pc", "nombre": "Juegos de PC", "carpeta": "PC", "ext": (), "cores": [],
     "pc": True},
]

ARCHIVO_NOMBRES_ARCADE = os.path.join(APP_DIR, "datos", "arcade.dat")
_nombres_arcade = None


def nombres_arcade():
    """Nombre completo de cada juego de arcade ("sfa.zip" -> "Street Fighter Alpha ...").

    Sale de la base de datos de FBNeo que baja instalar.sh. Si no está, devuelve {}.
    """
    global _nombres_arcade
    if _nombres_arcade is not None:
        return _nombres_arcade
    _nombres_arcade = {}
    try:
        with open(ARCHIVO_NOMBRES_ARCADE, encoding="utf-8", errors="replace") as f:
            nombre = None
            for linea in f:
                linea = linea.strip()
                if linea.startswith("game ("):
                    nombre = None
                elif linea.startswith('name "') and nombre is None:
                    nombre = linea[6:-1] if linea.endswith('"') else linea[6:]
                elif linea.startswith("rom ( name ") and nombre:
                    archivo = linea[11:].split(" ", 1)[0]
                    clave = os.path.splitext(archivo)[0].lower()
                    _nombres_arcade.setdefault(clave, nombre)
    except OSError:
        pass
    return _nombres_arcade

_video_3d = None


def analizar_glxinfo(texto):
    """Lee la salida de "glxinfo -B". Devuelve (alcanza, motivo)."""
    renderer = re.search(r"OpenGL renderer string:\s*(.*)", texto)
    renderer = renderer.group(1).strip() if renderer else ""
    acelerado = re.search(r"Accelerated:\s*(yes|no)", texto)
    nucleo = re.search(r"Max core profile version:\s*(\d+)\.(\d+)", texto)
    if not renderer:
        return False, "No pude averiguar qué placa de video tiene"
    if any(s in renderer.lower() for s in ("llvmpipe", "softpipe", "swrast")) or \
            (acelerado and acelerado.group(1) == "no"):
        return False, "La placa de video no tiene 3D (%s)" % renderer
    version = (int(nucleo.group(1)), int(nucleo.group(2))) if nucleo else (0, 0)
    if version < (3, 3):
        return False, "La placa de video no alcanza: tiene OpenGL %d.%d y hace falta 3.3" % version
    return True, "%s (OpenGL %d.%d)" % (renderer, version[0], version[1])


def video_para_n64():
    """¿La placa de video puede con la Nintendo 64? Se averigua una vez con glxinfo."""
    global _video_3d
    if _video_3d is None:
        try:
            texto = subprocess.run(["glxinfo", "-B"], capture_output=True, text=True,
                                   timeout=15).stdout
        except (OSError, subprocess.TimeoutExpired):
            texto = ""
        _video_3d = analizar_glxinfo(texto) if texto else (False, "Falta glxinfo (mesa-utils)")
    return _video_3d


def sistema_visible(sistema, opciones):
    """Las consolas experimentales se muestran según la opción (auto / si / no)."""
    clave = sistema.get("experimental")
    if not clave:
        return True
    valor = opciones.get(clave, "auto").lower()
    if valor in ("si", "sí", "yes", "1"):
        return True
    if valor in ("no", "0"):
        return False
    return video_para_n64()[0]


def _referencias(archivo):
    """Archivos que nombra un .cue (sus pistas .bin) o un .m3u (los discos de un juego)."""
    carpeta = os.path.dirname(archivo)
    try:
        with open(archivo, encoding="utf-8", errors="replace") as f:
            texto = f.read(65536)
    except OSError:
        return []
    if archivo.lower().endswith(".cue"):
        nombres = re.findall(r'^\s*FILE\s+"([^"]+)"', texto, re.I | re.M)
        nombres += re.findall(r'^\s*FILE\s+([^"\s]+)\s', texto, re.I | re.M)
    else:
        nombres = [l.strip() for l in texto.splitlines() if l.strip() and not l.startswith("#")]
    return [os.path.normcase(os.path.normpath(os.path.join(carpeta, n))).lower() for n in nombres]


def filtrar_discos(archivos):
    """Juegos de CD: muestra cada juego una vez.

    Saca los .bin que ya nombra un .cue y los discos sueltos que ya nombra un .m3u
    (así "Final Fantasy VII" aparece una vez y no tres).
    """
    usados = set()
    for a in archivos:
        if a.lower().endswith((".cue", ".m3u")):
            usados.update(_referencias(a))
    return [a for a in archivos if os.path.normcase(os.path.normpath(a)).lower() not in usados]


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


# Las carpetas que el sistema usa adentro de TeleVieja (todo lo demás está "suelto").
CARPETAS_PROPIAS = {"videos", "canal", "juegos", "historietas", "radio", "partidas",
                    "bios", "descargas"}


def tiene_archivos(carpeta, extensiones, limite=4000):
    """¿Hay algún archivo con esas extensiones adentro (en cualquier subcarpeta)?"""
    vistos = 0
    for _, _, archivos in os.walk(carpeta):
        for a in archivos:
            if a.lower().endswith(extensiones):
                return True
        vistos += len(archivos)
        if vistos > limite:   # carpeta enorme sin videos al principio: no seguimos buscando
            return False
    return False


def carpetas_sueltas(extensiones):
    """Carpetas puestas directo en TeleVieja (fuera de Videos, Juegos...) que tienen
    archivos de ese tipo. Pasa al copiar un disco que no tenía todo en Videos.
    Devuelve [(nombre, ruta, es_de_disco)]."""
    salida = []
    for r in raices():
        try:
            nombres = sorted(os.listdir(r), key=clave_natural)
        except OSError:
            continue
        for n in nombres:
            ruta = os.path.join(r, n)
            if (n.startswith(".") or n.lower() in CARPETAS_PROPIAS
                    or not os.path.isdir(ruta) or not tiene_archivos(ruta, extensiones)):
                continue
            salida.append((n, ruta, r != RAIZ))
    return salida


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


def guardar_opcion(clave, valor):
    """Cambia (o agrega) una opción en opciones.conf sin tocar el resto del archivo."""
    try:
        with open(ARCHIVO_OPCIONES, encoding="utf-8") as f:
            lineas = f.read().splitlines()
    except OSError:
        lineas = []
    nueva = "%s=%s" % (clave, valor)
    for i, linea in enumerate(lineas):
        if linea.strip().split("=", 1)[0].strip() == clave and not linea.lstrip().startswith("#"):
            lineas[i] = nueva
            break
    else:
        lineas.append(nueva)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = ARCHIVO_OPCIONES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    os.replace(tmp, ARCHIVO_OPCIONES)


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


# Para ordenar por número de episodio aunque los nombres vengan de distintos lados.
_ENTRE_CORCHETES = re.compile(r"\[[^\]]*\]|\([^)]*\)|\{[^}]*\}")
_TEMPORADA_EP = re.compile(r"\bs(\d{1,2})\s*[ex](\d{1,4})\b|\b(\d{1,2})x(\d{2,4})\b", re.I)
_MARCA_EP = re.compile(r"(?:\bep(?:isodio|isode|is)?|\bcap(?:[ií]tulo)?|\bchapter|#)"
                       r"[\s._-]*(\d{1,4})\b", re.I)
_NO_EPISODIO = re.compile(r"\b\d{3,4}p\b|\b[xh]\.?26[45]\b|\b\d{1,2}bit\b|\b(?:19|20)\d\d\b"
                          r"|\bmp4\b|\b5\.1\b|\b2\.0\b", re.I)


def numero_episodio(nombre_archivo):
    """El número de episodio de un nombre como "[Grupo] One Piece - 045 [720p].mkv"
    (45), "Serie S02E05" (2005) o "Capítulo 7" (7). None si no tiene."""
    base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    base = _ENTRE_CORCHETES.sub(" ", base).replace("_", " ")
    m = _TEMPORADA_EP.search(base)
    if m:
        temporada, ep = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        return int(temporada) * 10000 + int(ep)
    m = _MARCA_EP.search(base)
    if m:
        return int(m.group(1))
    base = _NO_EPISODIO.sub(" ", base.replace(".", " "))
    m = re.search(r"\d+", base)
    return int(m.group()) if m else None


def ordenar_episodios(rutas):
    """Ordena por número de episodio si casi todos tienen uno; si no, por nombre."""
    numeros = [numero_episodio(r) for r in rutas]
    con_numero = sum(n is not None for n in numeros)
    if len(rutas) < 2 or con_numero < 0.8 * len(rutas):
        return sorted(rutas, key=lambda r: clave_natural(os.path.basename(r)))
    infinito = float("inf")
    pares = sorted(zip(numeros, rutas),
                   key=lambda p: (infinito if p[0] is None else p[0],
                                  clave_natural(os.path.basename(p[1]))))
    return [r for _, r in pares]


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
