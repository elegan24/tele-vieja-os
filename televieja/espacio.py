"""Espacio en el disco: cuánto ocupa cada cosa y borrar para hacer lugar.

Solo se borra lo que está en la carpeta TeleVieja de la netbook (nunca en los discos USB,
que además se montan de solo lectura), y nunca las carpetas principales (Videos, Juegos,
Juegos/Family, Canal/Tandas...): lo de adentro, sí.
"""
import os
import shutil

from . import config

# Carpetas que arma el instalador: no se borran (lo que tienen adentro, sí)
PRINCIPALES = config.CARPETAS_PROPIAS | {"marcos"}
CON_SUBCARPETAS_FIJAS = {"canal", "juegos"}   # Canal/Tandas, Juegos/Family...


def legible(bytes_):
    """1234567890 -> "1,1 GB" (como lo muestra la netbook)."""
    for unidad, tam in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if bytes_ >= tam:
            valor = bytes_ / tam
            texto = ("%.1f" % valor) if valor < 100 else ("%d" % round(valor))
            if texto.endswith(".0"):
                texto = texto[:-2]
            return "%s %s" % (texto.replace(".", ","), unidad)
    return "%d bytes" % bytes_


def libre():
    """(libre, total) en bytes del disco donde está TeleVieja."""
    try:
        uso = shutil.disk_usage(config.RAIZ)
        return uso.free, uso.total
    except OSError:
        return 0, 0


def _relativa(ruta):
    raiz = os.path.realpath(config.RAIZ)
    real = os.path.realpath(ruta)
    if real == raiz or not real.startswith(raiz + os.sep):
        return None
    return os.path.relpath(real, raiz).split(os.sep)


def se_puede_borrar(ruta):
    partes = _relativa(ruta)
    if not partes:
        return False   # afuera de TeleVieja (discos USB) o TeleVieja misma
    if len(partes) == 1 and partes[0].lower() in PRINCIPALES:
        return False
    if len(partes) == 2 and partes[0].lower() in CON_SUBCARPETAS_FIJAS and \
            os.path.isdir(os.path.join(config.RAIZ, *partes)):
        return False
    return True


def tamano(ruta):
    if os.path.isfile(ruta) or os.path.islink(ruta):
        try:
            return os.lstat(ruta).st_size
        except OSError:
            return 0
    total = 0
    for raiz, _, archivos in os.walk(ruta):
        for a in archivos:
            try:
                total += os.lstat(os.path.join(raiz, a)).st_size
            except OSError:
                pass
    return total


def tamanos_de_carpetas(raiz=None):
    """{carpeta: bytes} de todas las carpetas adentro de raiz (una sola recorrida)."""
    raiz = raiz or config.RAIZ
    tamanos = {}
    for actual, carpetas, archivos in os.walk(raiz, topdown=False):
        total = 0
        for a in archivos:
            try:
                total += os.lstat(os.path.join(actual, a)).st_size
            except OSError:
                pass
        for c in carpetas:
            total += tamanos.get(os.path.join(actual, c), 0)
        tamanos[actual] = total
    return tamanos


def contenido(carpeta, tamanos):
    """[(nombre, ruta, es_carpeta, bytes)] de lo que hay en carpeta, lo más grande primero."""
    salida = []
    try:
        entradas = list(os.scandir(carpeta))
    except OSError:
        return salida
    for e in entradas:
        if e.name.startswith("."):
            continue
        try:
            es_carpeta = e.is_dir(follow_symlinks=False)
            bytes_ = tamanos.get(e.path, 0) if es_carpeta else e.stat(follow_symlinks=False).st_size
        except OSError:
            continue
        salida.append((e.name, e.path, es_carpeta, bytes_))
    salida.sort(key=lambda x: -x[3])
    return salida


def borrar(ruta):
    """Borra el archivo o la carpeta entera. Devuelve cuánto se liberó (bytes)."""
    if not se_puede_borrar(ruta):
        raise PermissionError("Eso no se puede borrar (es una carpeta del sistema).")
    liberado = tamano(ruta)
    if os.path.isdir(ruta) and not os.path.islink(ruta):
        shutil.rmtree(ruta)
    else:
        os.remove(ruta)
    return liberado
