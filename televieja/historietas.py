"""Abrir historietas: CBZ/ZIP, CBR/RAR/7Z, PDF o carpetas con imágenes.

Cada "libro" sabe cuántas páginas tiene y cómo cargar una como imagen de pygame.
Las páginas se achican a ANCHO_MAX para no llenar la memoria de la netbook.
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import zipfile

import pygame

from . import config

ANCHO_MAX = 1280
CACHE = os.path.join(config.CACHE_DIR, "historietas")
GUARDAR_EXTRAIDOS = 3     # cuántos CBR descomprimidos se guardan en el disco


class ErrorHistorieta(Exception):
    pass


def _a_color(superficie):
    """smoothscale solo trabaja con 24/32 bits; las GIF y PNG con paleta se pasan a color."""
    if superficie.get_bitsize() in (24, 32):
        return superficie
    nueva = pygame.Surface(superficie.get_size(), 0, 24)
    nueva.fill((255, 255, 255))
    nueva.blit(superficie, (0, 0))
    return nueva


def _achicar(superficie):
    superficie = _a_color(superficie)
    ancho, alto = superficie.get_size()
    if ancho <= ANCHO_MAX:
        return superficie
    nuevo_alto = max(1, int(alto * ANCHO_MAX / ancho))
    return pygame.transform.smoothscale(superficie, (ANCHO_MAX, nuevo_alto))


def es_imagen(nombre):
    return nombre.lower().endswith(config.EXT_IMAGEN)


class LibroCarpeta:
    def __init__(self, carpeta):
        self.paginas = config.listar_archivos(carpeta, config.EXT_IMAGEN)
        if not self.paginas:
            raise ErrorHistorieta("No tiene imágenes")

    def cantidad(self):
        return len(self.paginas)

    def cargar(self, i):
        return _achicar(pygame.image.load(self.paginas[i]))


class LibroZip:
    def __init__(self, ruta):
        self.ruta = ruta
        with zipfile.ZipFile(ruta) as z:
            nombres = [n for n in z.namelist()
                       if es_imagen(n) and not os.path.basename(n).startswith(".")
                       and "__MACOSX" not in n]
        if not nombres:
            raise ErrorHistorieta("No tiene imágenes")
        self.paginas = sorted(nombres, key=config.clave_natural)

    def cantidad(self):
        return len(self.paginas)

    def cargar(self, i):
        nombre = self.paginas[i]
        with zipfile.ZipFile(self.ruta) as z:
            datos = z.read(nombre)
        return _achicar(pygame.image.load(io.BytesIO(datos), os.path.basename(nombre)))


class LibroPdf:
    def __init__(self, ruta):
        self.ruta = ruta
        try:
            salida = subprocess.run(["pdfinfo", ruta], capture_output=True, text=True,
                                    timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ErrorHistorieta("Falta pdfinfo (poppler-utils)") from e
        m = re.search(r"^Pages:\s+(\d+)", salida, re.M)
        if not m or int(m.group(1)) == 0:
            raise ErrorHistorieta("No pude leer el PDF")
        self.total = int(m.group(1))
        self.carpeta = os.path.join(CACHE, "pdf-" + _huella(ruta))
        os.makedirs(self.carpeta, exist_ok=True)

    def cantidad(self):
        return self.total

    def cargar(self, i):
        destino = os.path.join(self.carpeta, "p%05d" % (i + 1))
        if not os.path.isfile(destino + ".jpg"):
            subprocess.run(["pdftoppm", "-f", str(i + 1), "-l", str(i + 1), "-singlefile",
                            "-scale-to-x", str(ANCHO_MAX), "-scale-to-y", "-1",
                            "-jpeg", "-jpegopt", "quality=85", self.ruta, destino],
                           capture_output=True, timeout=120)
        if not os.path.isfile(destino + ".jpg"):
            raise ErrorHistorieta("No pude dibujar la página %d" % (i + 1))
        return _achicar(pygame.image.load(destino + ".jpg"))


def _huella(ruta):
    try:
        st = os.stat(ruta)
        clave = "%s|%d|%d" % (ruta, st.st_size, int(st.st_mtime))
    except OSError:
        clave = ruta
    return hashlib.sha1(clave.encode("utf-8", "replace")).hexdigest()[:16]


def _limpiar_cache():
    try:
        extraidos = [os.path.join(CACHE, d) for d in os.listdir(CACHE) if d.startswith("arc-")]
    except OSError:
        return
    extraidos.sort(key=os.path.getmtime, reverse=True)
    for viejo in extraidos[GUARDAR_EXTRAIDOS:]:
        shutil.rmtree(viejo, ignore_errors=True)


def _extraer(ruta):
    """Descomprime RAR/7Z con bsdtar (libarchive) en la cache."""
    destino = os.path.join(CACHE, "arc-" + _huella(ruta))
    listo = os.path.join(destino, ".listo")
    if not os.path.isfile(listo):
        shutil.rmtree(destino, ignore_errors=True)
        os.makedirs(destino, exist_ok=True)
        try:
            r = subprocess.run(["bsdtar", "-xf", ruta, "-C", destino],
                               capture_output=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ErrorHistorieta("No pude descomprimir (falta libarchive-tools)") from e
        if r.returncode != 0 and not config.listar_archivos(destino, config.EXT_IMAGEN):
            raise ErrorHistorieta("No pude descomprimir el archivo")
        open(listo, "w").close()
    os.utime(destino)
    _limpiar_cache()
    return destino


def abrir(ruta):
    if os.path.isdir(ruta):
        return LibroCarpeta(ruta)
    minus = ruta.lower()
    if minus.endswith(".pdf"):
        return LibroPdf(ruta)
    if zipfile.is_zipfile(ruta):
        return LibroZip(ruta)
    return LibroCarpeta(_extraer(ruta))


def es_carpeta_historieta(carpeta):
    """Una carpeta con imágenes y sin subcarpetas se lee como una historieta."""
    try:
        hay_imagen = False
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isdir(ruta) and not nombre.startswith("."):
                return False
            if es_imagen(nombre):
                hay_imagen = True
        return hay_imagen
    except OSError:
        return False


# --- dónde quedó cada historieta -------------------------------------------
def leer_progreso():
    try:
        with open(config.ARCHIVO_HISTORIETAS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_progreso(ruta, pagina, modo_manga=None):
    datos = leer_progreso()
    entrada = datos.get(ruta, {})
    entrada["pagina"] = pagina
    if modo_manga is not None:
        entrada["manga"] = modo_manga
    datos[ruta] = entrada
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    tmp = config.ARCHIVO_HISTORIETAS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f)
    os.replace(tmp, config.ARCHIVO_HISTORIETAS)
