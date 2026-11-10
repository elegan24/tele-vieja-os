"""Reparte lo que se bajó en las carpetas de TeleVieja según el tipo de archivo.

- Videos -> Videos, música y radionovelas -> Radio, historietas -> Historietas.
- Juegos -> Juegos/<consola> según la extensión (.nes -> Family, .sfc -> SuperNintendo...).
- Un .zip con un solo juego adentro va entero a su consola (RetroArch lo abre así).
- Un .zip/.rar/.7z con muchas cosas (un "pack") se descomprime y se reparte.
- Lo que no se sabe dónde va queda en Descargas/, para acomodarlo a mano.
Se respetan las carpetas (una serie sigue con sus capítulos juntos).
"""
import os
import shutil
import subprocess
import zipfile

from . import config

ROMS = {
    ".nes": "Juegos/Family", ".fds": "Juegos/Family",
    ".smc": "Juegos/SuperNintendo", ".sfc": "Juegos/SuperNintendo",
    ".md": "Juegos/Sega", ".gen": "Juegos/Sega", ".smd": "Juegos/Sega",
    ".sms": "Juegos/Sega", ".gg": "Juegos/Sega",
    ".gb": "Juegos/GameBoy", ".gbc": "Juegos/GameBoy",
    ".gba": "Juegos/GameBoyAdvance",
    ".z64": "Juegos/Nintendo64", ".n64": "Juegos/Nintendo64", ".v64": "Juegos/Nintendo64",
    ".chd": "Juegos/PlayStation", ".pbp": "Juegos/PlayStation",
    ".cue": "Juegos/PlayStation", ".m3u": "Juegos/PlayStation",
}
HISTORIETAS = (".cbz", ".cbr", ".cb7", ".pdf")
COMPRIMIDOS = (".zip", ".rar", ".7z")
OTROS = "Descargas"


def categoria(nombre):
    """Carpeta (relativa a TeleVieja) para un archivo, o None si no se sabe."""
    ext = os.path.splitext(nombre)[1].lower()
    if ext in config.EXT_VIDEO:
        return "Videos"
    if ext in config.EXT_AUDIO:
        return "Radio"
    if ext in HISTORIETAS:
        return "Historietas"
    return ROMS.get(ext)


def _categoria_zip(ruta):
    """Si un .zip es un juego (o una historieta) entero, a dónde va. Si es un pack, None."""
    base = os.path.splitext(os.path.basename(ruta))[0].lower()
    if base in config.nombres_arcade():
        return "Juegos/Arcade"  # romset de arcade: va tal cual, sin descomprimir
    try:
        with zipfile.ZipFile(ruta) as z:
            nombres = [n for n in z.namelist() if not n.endswith("/")]
    except (zipfile.BadZipFile, OSError):
        return None
    if not nombres:
        return None
    if all(n.lower().endswith(config.EXT_IMAGEN) for n in nombres):
        return "Historietas"  # páginas sueltas: es una historieta
    cats = {categoria(n) for n in nombres}
    if len(nombres) <= 3 and len(cats) == 1:
        cat = cats.pop()
        if cat and cat.startswith("Juegos/") and cat != "Juegos/PlayStation":
            return cat  # un juego comprimido: RetroArch lo abre así
    return None


def _destino_libre(destino):
    if not os.path.exists(destino):
        return destino
    base, ext = os.path.splitext(destino)
    n = 2
    while os.path.exists("%s (%d)%s" % (base, n, ext)):
        n += 1
    return "%s (%d)%s" % (base, n, ext)


def _mover(origen, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino) and os.path.getsize(destino) == os.path.getsize(origen):
        os.remove(origen)  # ya lo teníamos
        return destino
    destino = _destino_libre(destino)
    shutil.move(origen, destino)
    return destino


def _descomprimir(ruta):
    """Descomprime un pack al lado (en una carpeta con su nombre). Devuelve la carpeta o None."""
    carpeta = os.path.splitext(ruta)[0]
    os.makedirs(carpeta, exist_ok=True)
    try:
        r = subprocess.run(["bsdtar", "-xf", ruta, "-C", carpeta], capture_output=True,
                           timeout=3600)
        ok = r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        ok = False
    if not ok and ruta.lower().endswith(".zip"):
        try:  # sin bsdtar, al menos los .zip
            with zipfile.ZipFile(ruta) as z:
                for miembro in z.namelist():
                    final = os.path.realpath(os.path.join(carpeta, miembro))
                    if not final.startswith(os.path.realpath(carpeta) + os.sep):
                        continue  # nada de escaparse de la carpeta
                    z.extract(miembro, carpeta)
            ok = True
        except (zipfile.BadZipFile, OSError):
            ok = False
    if not ok:
        shutil.rmtree(carpeta, ignore_errors=True)
        return None
    os.remove(ruta)
    return carpeta


def _referencias_cd(carpeta):
    """Los .bin/.chd que nombra algún .cue o .m3u: van con su juego de PlayStation."""
    usados = set()
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            if a.lower().endswith((".cue", ".m3u")):
                usados.update(config._referencias(os.path.join(raiz, a)))
    return usados


def acomodar(origen, raiz=None, avisar=None):
    """Reparte todo lo que hay en `origen` dentro de `raiz` (la carpeta TeleVieja).

    Devuelve {carpeta destino: cantidad de archivos}.
    """
    raiz = raiz or config.RAIZ
    resumen = {}
    origen = os.path.realpath(origen)

    # 1) Los packs comprimidos se abren (los juegos e historietas comprimidos, no).
    pendientes = True
    while pendientes:
        pendientes = False
        for carpeta, _, archivos in os.walk(origen):
            for a in archivos:
                ruta = os.path.join(carpeta, a)
                ext = os.path.splitext(a)[1].lower()
                if ext not in COMPRIMIDOS:
                    continue
                if ext == ".zip" and _categoria_zip(ruta):
                    continue
                if ext == ".7z" and os.path.splitext(a)[0].lower() in config.nombres_arcade():
                    continue
                if avisar:
                    avisar("Descomprimiendo " + a)
                if _descomprimir(ruta):
                    pendientes = True  # puede haber packs adentro de packs
        # (se vuelve a recorrer si se descomprimió algo)

    # 2) Las carpetas con un juego de PC (.exe) se dejan enteras en Descargas.
    con_exe = set()
    for carpeta, _, archivos in os.walk(origen):
        if any(a.lower().endswith(".exe") for a in archivos):
            con_exe.add(carpeta)
    cd = _referencias_cd(origen)

    # 3) Cada archivo a su lugar, respetando las carpetas.
    for carpeta, subdirs, archivos in os.walk(origen, topdown=True):
        relativa_dir = os.path.relpath(carpeta, origen)
        if carpeta in con_exe and relativa_dir != ".":
            # Juego de PC: la carpeta entera (con sus subcarpetas) a Descargas.
            subdirs[:] = []
            cantidad = sum(len(f) for _, _, f in os.walk(carpeta))
            destino = _destino_libre(os.path.join(raiz, OTROS, relativa_dir))
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.move(carpeta, destino)
            resumen[OTROS] = resumen.get(OTROS, 0) + cantidad
            continue
        solo_imagenes = archivos and all(a.lower().endswith(config.EXT_IMAGEN) for a in archivos)
        for a in archivos:
            ruta = os.path.join(carpeta, a)
            relativa = os.path.normpath(os.path.join(relativa_dir, a))
            if carpeta in con_exe:
                cat = OTROS
            elif os.path.normcase(os.path.normpath(ruta)).lower() in cd:
                cat = "Juegos/PlayStation"
            elif a.lower().endswith(".zip"):
                cat = _categoria_zip(ruta) or OTROS
            elif a.lower().endswith(".7z") and os.path.splitext(a)[0].lower() in config.nombres_arcade():
                cat = "Juegos/Arcade"
            elif solo_imagenes and len(archivos) >= 3:
                cat = "Historietas"  # una carpeta con páginas sueltas
            else:
                cat = categoria(a) or OTROS
            if cat == "Juegos/Arcade":
                relativa = a  # FBNeo los reconoce por el nombre: sin subcarpetas
            destino = os.path.join(raiz, *cat.split("/"), relativa)
            _mover(ruta, destino)
            resumen[cat] = resumen.get(cat, 0) + 1
    # 4) Por las dudas: si quedó algún archivo sin mover, a Descargas (nunca se borra nada).
    for carpeta, _, archivos in os.walk(origen):
        for a in archivos:
            relativa = os.path.relpath(os.path.join(carpeta, a), origen)
            _mover(os.path.join(carpeta, a), os.path.join(raiz, OTROS, relativa))
            resumen[OTROS] = resumen.get(OTROS, 0) + 1
    shutil.rmtree(origen, ignore_errors=True)
    return resumen


NOMBRES_LINDOS = {
    "Videos": "videos", "Radio": "audios", "Historietas": "historietas",
    "Descargas": "otros (en Descargas)",
}


def describir(resumen):
    """{"Videos": 3, "Juegos/Family": 10} -> "3 videos, 10 de Family"."""
    partes = []
    for cat, n in sorted(resumen.items(), key=lambda kv: -kv[1]):
        if cat in NOMBRES_LINDOS:
            partes.append("%d %s" % (n, NOMBRES_LINDOS[cat]))
        else:
            partes.append("%d de %s" % (n, cat.split("/")[-1]))
    return ", ".join(partes) if partes else "nada"
