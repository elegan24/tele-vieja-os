"""Descargas desde un link (Google Drive o un link directo), de a una por vez.

Se agregan desde la página del celu. Cada descarga se baja a una carpeta
temporal y, al terminar, acomodar.py la reparte en las carpetas de TeleVieja.
"""
import itertools
import json
import os
import re
import shutil
import socket
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
    host = partes.netloc.lower()
    if host in ("mediafire.com", "www.mediafire.com"):
        # La página de MediaFire no se puede bajar sola (tiene un control anti-robots).
        # El link directo (download####.mediafire.com/...) sí, y lo saca uno desde el celu.
        if "/folder/" in partes.path:
            raise ValueError("Las carpetas de MediaFire no se pueden bajar desde acá. "
                             "Entrá a la carpeta en el celu y pegá el link directo de cada "
                             "archivo (ver abajo).")
        raise ValueError("Ese es el link de la página de MediaFire. Abrilo en el celu, "
                         "mantené apretado el botón azul \"Download\" y elegí "
                         "\"Copiar dirección del enlace\". Pegá ese link acá.")
    return url


ESTADOS_ACTIVOS = ("esperando", "bajando", "acomodando", "reintentar")
# Cuándo reintentar (minutos), según qué pasó. Lo ya bajado no se vuelve a bajar.
ESPERAS = {
    "red": [2, 5, 15, 30, 60, 120],          # se cortó internet, se colgó algo
    "cuota": [180, 180, 240, 360, 480, 720],  # Google frenó por "cuota": esperar horas
}


def hay_internet():
    for host in ("drive.google.com", "www.google.com"):
        try:
            socket.create_connection((host, 443), timeout=8).close()
            return True
        except OSError:
            continue
    return False


def legible(mensaje):
    """Los errores técnicos de conexión, en criollo."""
    if any(x in mensaje for x in ("HTTPSConnectionPool", "ConnectionError", "Connection reset",
                                  "Connection aborted", "timed out", "Max retries",
                                  "Name or service", "Temporary failure", "urlopen error",
                                  "NameResolution", "Network is unreachable")):
        return "Se cortó la conexión a internet."
    return mensaje


def clasificar(textos):
    """Qué tipo de problema hubo: cuota, permiso, disco o red (lo demás se trata como red)."""
    junto = " ".join(textos).lower()
    if "compartido" in junto or "permission" in junto or "público" in junto:
        return "permiso"
    if "disco" in junto or "no space" in junto:
        return "disco"
    if "cuota" in junto or "too many users" in junto or "demasiadas veces" in junto:
        return "cuota"
    return "red"


class Trabajo:
    CAMPOS = ("id", "url", "estado", "nombre", "archivo", "total", "porcentaje", "mensaje",
              "avisos", "resumen", "creado", "intentos", "proximo", "solo_acomodar",
              "aviso_temprano")

    def __init__(self, url, ident=None):
        self.id = ident if ident is not None else next(_numeros)
        self.url = url
        # esperando, bajando, acomodando, reintentar, listo, error, cancelado
        self.estado = "esperando"
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
        self.intentos = 0           # cuántas veces se reintentó
        self.proximo = 0.0          # cuándo reintentar (hora en segundos)
        self.solo_acomodar = False  # se cortó mientras acomodaba: no hace falta bajar de nuevo
        self.aviso_temprano = False  # ya se avisó que hay cosas para usar

    def a_guardar(self):
        return {c: getattr(self, c) for c in self.CAMPOS}

    @classmethod
    def desde(cls, datos):
        t = cls(datos["url"], datos["id"])
        for c in cls.CAMPOS:
            if c in datos:
                setattr(t, c, datos[c])
        return t

    def como_dict(self):
        actual = self.actual
        if self.estado == "reintentar":
            actual = "Reintenta a las %s" % time.strftime("%H:%M", time.localtime(self.proximo))
        return {
            "id": self.id, "url": self.url, "estado": self.estado, "nombre": self.nombre,
            "archivo": self.archivo, "total": self.total, "porcentaje": self.porcentaje,
            "actual": actual, "mensaje": self.mensaje, "avisos": self.avisos[-3:],
            "carpetas_leidas": self.carpetas_leidas, "archivos_vistos": self.archivos_vistos,
            "resumen": acomodar.describir(self.resumen) if self.resumen else "",
            "intentos": self.intentos,
        }


class Gestor:
    """Fila de descargas. Se guarda en disco: si se reinicia la netbook, sigue sola."""

    def __init__(self, raiz=None, archivo=None, esperas=None, internet=None):
        self.raiz = raiz or config.RAIZ
        self.temporal = os.path.join(self.raiz, "Descargas", ".bajando")
        self.archivo = archivo or os.path.join(config.CONFIG_DIR, "descargas.json")
        self.esperas = esperas or ESPERAS
        self.internet = internet or hay_internet
        self.trabajos = []
        self.lock = threading.Lock()
        self.hay_trabajo = threading.Event()
        self.novedades = []         # avisos para mostrar en la tele
        self.sin_internet = False
        self._ultimo_guardado = 0.0
        self._cargar()
        threading.Thread(target=self._trabajar, daemon=True).start()

    # --- guardar y cargar la fila ------------------------------------------------
    def _cargar(self):
        global _numeros
        try:
            with open(self.archivo, encoding="utf-8") as f:
                guardados = json.load(f)
        except (OSError, ValueError):
            guardados = []
        for datos in guardados:
            try:
                t = Trabajo.desde(datos)
            except (KeyError, TypeError):
                continue
            if t.estado == "bajando":
                t.estado = "esperando"           # se cortó a la mitad: sigue desde donde quedó
            elif t.estado == "acomodando":
                t.estado = "esperando"
                t.solo_acomodar = True           # ya estaba todo bajado
            self.trabajos.append(t)
        if self.trabajos:
            _numeros = itertools.count(max(t.id for t in self.trabajos) + 1)

    def _guardar(self, forzar=True):
        ahora = time.time()
        if not forzar and ahora - self._ultimo_guardado < 15:
            return
        self._ultimo_guardado = ahora
        with self.lock:
            # las activas siempre; de las terminadas, solo las últimas 30
            activas = [t for t in self.trabajos if t.estado in ESTADOS_ACTIVOS]
            terminadas = [t for t in self.trabajos if t.estado not in ESTADOS_ACTIVOS][-30:]
            self.trabajos = [t for t in self.trabajos if t in activas or t in terminadas]
            datos = [t.a_guardar() for t in self.trabajos]
        try:
            os.makedirs(os.path.dirname(self.archivo), exist_ok=True)
            tmp = self.archivo + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
            os.replace(tmp, self.archivo)
        except OSError:
            pass

    # --- lo que usan la página del celu y el menú ------------------------------
    def agregar(self, url):
        url = validar(url)
        with self.lock:
            for t in self.trabajos:
                if t.url == url and t.estado in ESTADOS_ACTIVOS:
                    raise ValueError("Ese link ya está en la lista.")
            trabajo = Trabajo(url)
            self.trabajos.append(trabajo)
        self._guardar()
        self.hay_trabajo.set()
        return trabajo

    def cancelar(self, ident):
        with self.lock:
            for t in self.trabajos:
                if t.id == ident and t.estado in ("esperando", "bajando", "reintentar"):
                    t.estado = "cancelado"
                    t.mensaje = "Cancelada."
                    if t.proceso:
                        t.proceso.terminate()
                    else:
                        shutil.rmtree(os.path.join(self.temporal, str(t.id)), ignore_errors=True)
                    break
            else:
                return False
        self._guardar()
        return True

    def lista(self):
        with self.lock:
            lista = [t.como_dict() for t in reversed(self.trabajos)]
        if self.sin_internet:
            for d in lista:
                if d["estado"] in ("esperando", "reintentar"):
                    d["actual"] = "Esperando que vuelva internet..."
        return lista

    def activos(self):
        with self.lock:
            return sum(1 for t in self.trabajos if t.estado in ESTADOS_ACTIVOS)

    def tomar_novedades(self):
        with self.lock:
            novedades, self.novedades = self.novedades, []
            return novedades

    # --- el trabajo en sí (en segundo plano) -----------------------------------
    def _siguiente(self):
        ahora = time.time()
        with self.lock:
            listas = [t for t in self.trabajos
                      if t.estado == "esperando" or (t.estado == "reintentar" and t.proximo <= ahora)]
        # Primero lo que ya está bajado y solo falta acomodar (no necesita internet).
        for t in listas:
            if t.solo_acomodar:
                return t
        return listas[0] if listas else None

    def _hasta_el_proximo(self):
        """Cuánto dormir: hasta el próximo reintento (como mucho 20 segundos)."""
        with self.lock:
            proximos = [t.proximo for t in self.trabajos if t.estado == "reintentar"]
        if not proximos:
            return 20
        return max(0.05, min(20, min(proximos) - time.time()))

    def _trabajar(self):
        while True:
            trabajo = self._siguiente()
            if trabajo is None:
                self.hay_trabajo.wait(timeout=self._hasta_el_proximo())
                self.hay_trabajo.clear()
                continue
            if not trabajo.solo_acomodar and not self.internet():
                self.sin_internet = True   # no se gasta un intento: espera y vuelve a probar
                self.hay_trabajo.wait(timeout=30)
                self.hay_trabajo.clear()
                continue
            self.sin_internet = False
            with self.lock:
                if trabajo.estado == "cancelado":
                    continue
                trabajo.estado = "bajando"
            self._guardar()
            try:
                self._hacer(trabajo)
            except Exception as e:  # noqa: BLE001 - que una descarga rota no frene las demás
                trabajo.mensaje = str(e)[:200]
                self._fallo(trabajo, os.path.join(self.temporal, str(trabajo.id)))
            self._guardar()

    def _hacer(self, trabajo):
        carpeta = os.path.join(self.temporal, str(trabajo.id))
        os.makedirs(carpeta, exist_ok=True)
        ok = True
        if not trabajo.solo_acomodar:
            trabajo.mensaje = ""
            trabajo.avisos = []
            if es_drive(trabajo.url):
                ok = self._bajar_drive(trabajo, carpeta)
            else:
                ok = self._bajar_directo(trabajo, carpeta)
        if trabajo.estado == "cancelado":
            shutil.rmtree(carpeta, ignore_errors=True)
            return
        if ok:
            self._acomodar(trabajo, carpeta)
        else:
            self._fallo(trabajo, carpeta)

    def _acomodar_ya(self, trabajo, carpeta, relativa):
        """Un video (o juego, historieta...) que ya llegó: a su lugar, para usarlo ya."""
        try:
            cat = acomodar.acomodar_archivo(carpeta, os.path.join(trabajo.nombre, relativa),
                                            self.raiz)
        except OSError:
            return
        if not cat:
            return
        # anotado: si la descarga se reanuda, no se vuelve a bajar
        with open(os.path.join(carpeta, ".televieja-hechos"), "a", encoding="utf-8") as f:
            f.write(relativa + "\n")
        trabajo.resumen[cat] = trabajo.resumen.get(cat, 0) + 1
        if not trabajo.aviso_temprano:
            trabajo.aviso_temprano = True
            self._novedad("Ya podés usar lo primero que llegó de %s" % trabajo.nombre)

    def _acomodar(self, trabajo, carpeta, faltaron=False):
        trabajo.estado = "acomodando"
        trabajo.solo_acomodar = True
        trabajo.actual = ""
        self._guardar()

        def avisar(texto):
            trabajo.actual = texto
        for cat, n in acomodar.acomodar(carpeta, self.raiz, avisar).items():
            trabajo.resumen[cat] = trabajo.resumen.get(cat, 0) + n
        trabajo.estado = "listo"
        trabajo.solo_acomodar = False
        if faltaron:
            self._novedad("Descarga terminada con faltantes: %s" % trabajo.nombre)
        else:
            trabajo.mensaje = ""
            self._novedad("Descarga lista: %s (%s)" % (trabajo.nombre,
                                                      acomodar.describir(trabajo.resumen)))

    def _fallo(self, trabajo, carpeta):
        """Algo no se bajó: según qué pasó, se reintenta más tarde o se da por terminada."""
        trabajo.mensaje = legible(trabajo.mensaje or "")
        tipo = clasificar([trabajo.mensaje] + trabajo.avisos)
        esperas = self.esperas.get(tipo)
        if esperas and trabajo.intentos < len(esperas):
            minutos = esperas[trabajo.intentos]
            trabajo.intentos += 1
            trabajo.estado = "reintentar"
            trabajo.proximo = time.time() + minutos * 60
            trabajo.mensaje = ("Google frenó la descarga (cuota). " if tipo == "cuota" else
                               "Se cortó la descarga. ") + \
                "Lo ya bajado se guarda; reintenta sola (intento %d de %d)." % (
                    trabajo.intentos, len(esperas))
            return
        # sin más reintentos (o no tiene sentido reintentar): se acomoda lo que llegó
        if _hay_archivos(carpeta):
            trabajo.mensaje = (trabajo.mensaje or "Algunos archivos no se pudieron bajar.")
            self._acomodar(trabajo, carpeta, faltaron=True)
        else:
            trabajo.estado = "error"
            trabajo.mensaje = trabajo.mensaje or "No se pudo bajar."
            shutil.rmtree(carpeta, ignore_errors=True)
            self._novedad("No se pudo bajar %s: %s" % (trabajo.nombre, trabajo.mensaje))

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
        elegibles = set()
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
                if "lista" in datos:
                    elegibles = acomodar.elegibles_temprano(datos["lista"])
                if "archivo" in datos and datos.get("ok") and datos.get("nuevo") \
                        and datos.get("ruta") in elegibles:
                    self._acomodar_ya(trabajo, carpeta, datos["ruta"])
                if "archivo" in datos:
                    self._guardar(forzar=False)
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
        """Links que no son de Drive. Si se corta, sigue desde donde quedó (si el sitio deja)."""
        for intento in range(3):
            try:
                return self._bajar_directo_una_vez(trabajo, carpeta)
            except Exception as e:  # noqa: BLE001
                trabajo.mensaje = legible(str(e)[:200])
                if trabajo.estado == "cancelado" or clasificar([trabajo.mensaje]) == "disco":
                    return False
                time.sleep(5 * (intento + 1))
        return False

    def _bajar_directo_una_vez(self, trabajo, carpeta):
        partes = [a for a in os.listdir(carpeta) if a.endswith(".part")]
        ya = os.path.getsize(os.path.join(carpeta, partes[0])) if partes else 0
        cabeceras = {"User-Agent": "TeleVieja"}
        if ya:
            cabeceras["Range"] = "bytes=%d-" % ya
        pedido = urllib.request.Request(trabajo.url, headers=cabeceras)
        with urllib.request.urlopen(pedido, timeout=60) as r:
            nombre = partes[0][:-5] if partes else _nombre_de_respuesta(r, trabajo.url)
            parcial = os.path.join(carpeta, nombre + ".part")
            continuar = ya and r.status == 206
            trabajo.nombre = nombre
            trabajo.total = 1
            trabajo.archivo = 1
            trabajo.actual = nombre
            largo = int(r.headers.get("Content-Length") or 0) + (ya if continuar else 0)
            bajado = ya if continuar else 0
            with open(parcial, "ab" if continuar else "wb") as f:
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
        if trabajo.estado == "cancelado":
            return False
        if largo and bajado < largo:
            raise OSError("Se cortó la descarga (llegó %d de %d bytes)." % (bajado, largo))
        os.replace(parcial, os.path.join(carpeta, nombre))
        return True


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
