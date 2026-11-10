"""Descargas desde un link (Google Drive o un link directo), de a una por vez.

Se agregan desde la página del celu. Cada descarga se baja a una carpeta
temporal y, al terminar, acomodar.py la reparte en las carpetas de TeleVieja.
"""
import itertools
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request

from . import acomodar, config

def paralelas():
    try:
        return max(1, min(8, int(config.leer_opciones().get("DESCARGAS_PARALELAS", "4"))))
    except ValueError:
        return 4


PYTHON_DRIVE = os.path.join(config.APP_DIR, "pyenv", "bin", "python")
BAJAR_DRIVE = os.path.join(config.APP_DIR, "televieja", "bajar_drive.py")
_numeros = itertools.count(1)


def es_drive(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    return host.endswith("drive.google.com") or host.endswith("docs.google.com") or \
        host.endswith("drive.usercontent.google.com")


def validar(url):
    """Devuelve el link limpio o tira ValueError con un mensaje para el usuario."""
    url = (url or "").strip()
    partes = urllib.parse.urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError("Eso no parece un link. Tiene que empezar con https://")
    if len(url) > 2000:
        raise ValueError("El link es demasiado largo.")
    return url


class Trabajo:
    def __init__(self, url):
        self.id = next(_numeros)
        self.url = url
        self.estado = "esperando"   # esperando, bajando, acomodando, listo, error, cancelado
        self.nombre = "Drive" if es_drive(url) else os.path.basename(urllib.parse.urlparse(url).path) or url
        self.archivo = 0
        self.total = 0
        self.porcentaje = 0
        self.actual = ""
        self.mensaje = ""
        self.avisos = []
        self.resumen = {}
        self.proceso = None
        self.creado = time.time()
        self.carpetas_leidas = 0    # mientras Google da la lista de una carpeta grande
        self.archivos_vistos = 0

    def como_dict(self):
        return {
            "id": self.id, "url": self.url, "estado": self.estado, "nombre": self.nombre,
            "archivo": self.archivo, "total": self.total, "porcentaje": self.porcentaje,
            "actual": self.actual, "mensaje": self.mensaje, "avisos": self.avisos[-3:],
            "carpetas_leidas": self.carpetas_leidas, "archivos_vistos": self.archivos_vistos,
            "resumen": acomodar.describir(self.resumen) if self.resumen else "",
        }


class Gestor:
    def __init__(self, raiz=None):
        self.raiz = raiz or config.RAIZ
        self.temporal = os.path.join(self.raiz, "Descargas", ".bajando")
        self.trabajos = []
        self.lock = threading.Lock()
        self.hay_trabajo = threading.Event()
        self.novedades = []         # avisos para mostrar en la tele
        threading.Thread(target=self._trabajar, daemon=True).start()

    # --- lo que usan la página del celu y el menú ------------------------------
    def agregar(self, url):
        url = validar(url)
        with self.lock:
            for t in self.trabajos:
                if t.url == url and t.estado in ("esperando", "bajando", "acomodando"):
                    raise ValueError("Ese link ya se está bajando.")
            trabajo = Trabajo(url)
            self.trabajos.append(trabajo)
            self.trabajos = self.trabajos[-30:]  # no acumular para siempre
        self.hay_trabajo.set()
        return trabajo

    def cancelar(self, ident):
        with self.lock:
            for t in self.trabajos:
                if t.id == ident and t.estado in ("esperando", "bajando"):
                    t.estado = "cancelado"
                    t.mensaje = "Cancelada."
                    if t.proceso:
                        t.proceso.terminate()
                    return True
        return False

    def lista(self):
        with self.lock:
            return [t.como_dict() for t in reversed(self.trabajos)]

    def activos(self):
        with self.lock:
            return sum(1 for t in self.trabajos if t.estado in ("esperando", "bajando", "acomodando"))

    def tomar_novedades(self):
        with self.lock:
            novedades, self.novedades = self.novedades, []
            return novedades

    # --- el trabajo en sí (en segundo plano) -----------------------------------
    def _siguiente(self):
        with self.lock:
            for t in self.trabajos:
                if t.estado == "esperando":
                    t.estado = "bajando"
                    return t
        return None

    def _trabajar(self):
        while True:
            trabajo = self._siguiente()
            if trabajo is None:
                self.hay_trabajo.wait(timeout=5)
                self.hay_trabajo.clear()
                continue
            carpeta = os.path.join(self.temporal, str(trabajo.id))
            try:
                os.makedirs(carpeta, exist_ok=True)
                if es_drive(trabajo.url):
                    ok = self._bajar_drive(trabajo, carpeta)
                else:
                    ok = self._bajar_directo(trabajo, carpeta)
                if trabajo.estado == "cancelado":
                    shutil.rmtree(carpeta, ignore_errors=True)
                    continue
                if not ok and not _hay_archivos(carpeta):
                    trabajo.estado = "error"
                    trabajo.mensaje = trabajo.mensaje or "No se pudo bajar."
                    shutil.rmtree(carpeta, ignore_errors=True)
                    self._novedad("No se pudo bajar %s: %s" % (trabajo.nombre, trabajo.mensaje))
                    continue
                trabajo.estado = "acomodando"
                trabajo.actual = ""

                def avisar(texto):
                    trabajo.actual = texto
                trabajo.resumen = acomodar.acomodar(carpeta, self.raiz, avisar)
                trabajo.estado = "listo"
                if not ok:  # se bajó una parte: igual se acomoda lo que llegó
                    trabajo.mensaje = trabajo.mensaje or "Algunos archivos no se pudieron bajar."
                self._novedad("Descarga lista: %s (%s)" % (trabajo.nombre,
                                                          acomodar.describir(trabajo.resumen)))
            except Exception as e:  # noqa: BLE001 - que una descarga rota no frene las demás
                trabajo.estado = "error"
                trabajo.mensaje = str(e)[:200]
                self._novedad("Falló la descarga de %s" % trabajo.nombre)

    def _novedad(self, texto):
        with self.lock:
            self.novedades.append(texto)

    def _bajar_drive(self, trabajo, carpeta):
        if not os.path.isfile(PYTHON_DRIVE):
            trabajo.mensaje = "Falta gdown: volvé a correr instalar.sh con internet."
            return False
        try:
            entorno = dict(os.environ, TELEVIEJA_PARALELAS=str(paralelas()))
            proceso = subprocess.Popen([PYTHON_DRIVE, BAJAR_DRIVE, trabajo.url, carpeta],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=entorno)
        except OSError as e:
            trabajo.mensaje = str(e)
            return False
        trabajo.proceso = proceso
        error = None
        for renglon in _renglones(proceso.stdout):
            if renglon.startswith("@@ "):
                try:
                    datos = json.loads(renglon[3:])
                except ValueError:
                    continue
                if datos.get("leyendo"):
                    trabajo.actual = "Leyendo la lista de archivos de Google Drive..."
                if "nombre" in datos:
                    trabajo.nombre = datos["nombre"]
                if "total" in datos:
                    trabajo.total = datos["total"]
                    if datos.get("incompletas"):
                        trabajo.avisos.append(
                            "Google muestra solo 50 archivos por carpeta: puede que falten "
                            "algunos. Pegá el link de cada subcarpeta para bajar el resto.")
                if "archivo" in datos:
                    trabajo.archivo = datos["archivo"]       # cuántos van hechos
                    trabajo.actual = os.path.basename(datos.get("ruta", ""))
                    if trabajo.total > 1:  # porcentaje de TODA la descarga
                        trabajo.porcentaje = min(100, trabajo.archivo * 100 // trabajo.total)
                if "aviso" in datos:
                    trabajo.avisos.append("%s: %s" % (os.path.basename(datos.get("ruta", "")),
                                                      datos["aviso"]))
                if "error" in datos:
                    error = datos["error"]
                if datos.get("fallados"):
                    trabajo.mensaje = "%d archivos no se pudieron bajar." % datos["fallados"]
            elif renglon.startswith("Retrieving folder ") and not trabajo.total:
                trabajo.carpetas_leidas += 1
                trabajo.actual = "Leyendo la lista: %d carpetas, %d archivos" % (
                    trabajo.carpetas_leidas, trabajo.archivos_vistos)
            elif renglon.startswith("Processing file ") and not trabajo.total:
                trabajo.archivos_vistos += 1
                trabajo.actual = "Leyendo la lista: %d carpetas, %d archivos" % (
                    trabajo.carpetas_leidas, trabajo.archivos_vistos)
            else:
                m = re.search(r"(\d{1,3})%\|", renglon)
                if m and trabajo.total <= 1:  # un archivo solo: sí sirve el porcentaje de gdown
                    trabajo.porcentaje = int(m.group(1))
        proceso.wait()
        trabajo.proceso = None
        if error:
            trabajo.mensaje = error
        return proceso.returncode == 0 and not trabajo.mensaje

    def _bajar_directo(self, trabajo, carpeta):
        """Links que no son de Drive: se bajan tal cual (por ejemplo un .zip de una página)."""
        try:
            pedido = urllib.request.Request(trabajo.url, headers={"User-Agent": "TeleVieja"})
            with urllib.request.urlopen(pedido, timeout=60) as r:
                nombre = _nombre_de_respuesta(r, trabajo.url)
                trabajo.nombre = nombre
                trabajo.total = 1
                trabajo.archivo = 1
                trabajo.actual = nombre
                largo = int(r.headers.get("Content-Length") or 0)
                bajado = 0
                destino = os.path.join(carpeta, nombre)
                with open(destino, "wb") as f:
                    while trabajo.estado != "cancelado":
                        bloque = r.read(256 * 1024)
                        if not bloque:
                            break
                        f.write(bloque)
                        bajado += len(bloque)
                        if largo:
                            trabajo.porcentaje = min(100, bajado * 100 // largo)
                        if shutil.disk_usage(carpeta).free < 500 * 1024 * 1024:
                            raise OSError("Se llenó el disco.")
            return trabajo.estado != "cancelado"
        except Exception as e:  # noqa: BLE001
            trabajo.mensaje = str(e)[:200]
            return False


def _nombre_de_respuesta(respuesta, url):
    disposicion = respuesta.headers.get("Content-Disposition") or ""
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", disposicion)
    nombre = urllib.parse.unquote(m.group(1)) if m else \
        urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(url).path))
    nombre = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", nombre).strip(" .")
    return nombre[:150] or "descarga"


def _renglones(flujo):
    """Lee la salida del proceso partiendo en \\n y \\r (la barrita de avance usa \\r)."""
    resto = b""
    while True:
        bloque = flujo.read1(4096) if hasattr(flujo, "read1") else flujo.read(4096)
        if not bloque:
            break
        resto += bloque
        partes = re.split(rb"[\r\n]", resto)
        resto = partes.pop()
        for p in partes:
            yield p.decode("utf-8", "replace")
    if resto:
        yield resto.decode("utf-8", "replace")


def _hay_archivos(carpeta):
    return any(archivos for _, _, archivos in os.walk(carpeta))
