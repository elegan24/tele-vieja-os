"""Juegos viejos de Windows (por ejemplo Sonic R de PC) con Wine.

Cada juego es una carpeta en TeleVieja/Juegos/PC. Wine usa una "botella"
propia de TeleVieja (32 bits, como los juegos de esa época) que se prepara
sola la primera vez.
"""
import glob
import os
import re
import shutil
import subprocess

from . import config

PREFIJO = os.path.join(config.HOME, ".local", "share", "televieja", "wine")

# Programas que casi nunca son el juego en sí.
NO_ES_EL_JUEGO = re.compile(
    r"setup|instal|unins|uninst|config|dxsetup|directx|dxwebsetup|vcredist|autorun|"
    r"readme|update|patch|register|crash|helper|redist", re.I)


def hay_wine():
    return shutil.which("wine") is not None


def entorno():
    env = dict(os.environ)
    env.update({
        "WINEPREFIX": PREFIJO,
        "WINEARCH": "win32",
        "WINEDEBUG": "-all",
        # Sin estos, Wine abre ventanas preguntando si bajar Mono y Gecko.
        "WINEDLLOVERRIDES": "mscoree,mshtml=",
    })
    return env


def prefijo_listo():
    return os.path.isfile(os.path.join(PREFIJO, "system.reg"))


def preparar():
    """Crea la botella de Wine (solo la primera vez; tarda un par de minutos)."""
    os.makedirs(os.path.dirname(PREFIJO), exist_ok=True)
    subprocess.run(["wine", "wineboot", "-i"], env=entorno(), capture_output=True, timeout=900)
    _wineserver("-w", espera=300)
    if not prefijo_listo():
        raise RuntimeError("No se pudo preparar Wine. Revisá que esté instalado (instalar.sh).")
    return True


def _wineserver(*args, espera=10):
    ruta = shutil.which("wineserver") or next(iter(sorted(
        glob.glob("/usr/lib/wine/wineserver*") + glob.glob("/usr/lib/*/wine/wineserver*"))), None)
    try:
        if ruta:
            subprocess.run([ruta] + list(args), env=entorno(), capture_output=True, timeout=espera)
        elif args == ("-k",):
            subprocess.run(["wine", "wineboot", "-k"], env=entorno(), capture_output=True,
                           timeout=espera)
    except (OSError, subprocess.TimeoutExpired):
        pass


def cortar():
    """Cierra el juego (y todo lo de Wine) de golpe: SELECT + START o "Salir" en el celu."""
    _wineserver("-k")


def orden(exe, ancho, alto, escritorio=True):
    """Con "escritorio virtual" el juego queda en una ventana del tamaño de la pantalla,
    sin cambiar la resolución (la tele y el conversor no se enteran)."""
    if escritorio:
        return ["wine", "explorer", "/desktop=TeleVieja,%dx%d" % (ancho, alto), exe]
    return ["wine", exe]


def juegos_pc():
    """Carpetas de juegos de PC en la netbook y en los discos USB."""
    juegos = []
    for raiz in config.raices():
        carpeta = os.path.join(raiz, "Juegos", "PC")
        try:
            nombres = os.listdir(carpeta)
        except OSError:
            continue
        for n in nombres:
            ruta = os.path.join(carpeta, n)
            if not n.startswith(".") and os.path.isdir(ruta):
                juegos.append(ruta)
    juegos.sort(key=lambda p: config.clave_natural(os.path.basename(p)))
    return juegos


def _simple(texto):
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def exe_de_juego(carpeta):
    """Qué .exe abrir. Devuelve (exe o None, lista de candidatos).

    1) Si hay un archivo jugar.txt, el nombre que diga adentro.
    2) Si hay un solo .exe que no sea instalador/configuración, ese.
    3) Si alguno se llama parecido a la carpeta, ese.
    """
    txt = os.path.join(carpeta, "jugar.txt")
    if os.path.isfile(txt):
        try:
            with open(txt, encoding="utf-8", errors="replace") as f:
                pedido = next((l.strip() for l in f if l.strip()), "")
        except OSError:
            pedido = ""
        ruta = os.path.normpath(os.path.join(carpeta, pedido.replace("\\", "/")))
        if pedido and ruta.startswith(os.path.normpath(carpeta) + os.sep) and os.path.isfile(ruta):
            return ruta, [ruta]
    exes = []
    for raiz, subdirs, archivos in os.walk(carpeta):
        if raiz.count(os.sep) - carpeta.count(os.sep) >= 2:
            subdirs[:] = []  # no buscar muy adentro
        for a in archivos:
            if a.lower().endswith(".exe"):
                exes.append(os.path.join(raiz, a))
    candidatos = sorted((e for e in exes if not NO_ES_EL_JUEGO.search(os.path.basename(e))),
                        key=lambda p: (p.count(os.sep), p.lower()))
    if len(candidatos) == 1:
        return candidatos[0], candidatos
    nombre = _simple(os.path.basename(carpeta))
    for e in candidatos:
        base = _simple(os.path.splitext(os.path.basename(e))[0])
        if base and (base in nombre or nombre in base):
            return e, candidatos
    return None, candidatos
