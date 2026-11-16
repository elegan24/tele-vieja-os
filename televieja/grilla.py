"""La grilla del Canal Retro: bloques de programación por día y horario.

Cada bloque tiene días, hora de inicio, nombre y qué pasa:
  - "mezcla": series al azar (de las elegidas, o todas), cada una sigue en su capítulo.
  - "maraton": una sola serie, capítulo tras capítulo (si no se elige, cambia cada semana).
Un bloque dura hasta que empieza el siguiente.

Las series salen de las carpetas de Canal/Programas (o de Videos si está vacía).
Cada serie recuerda por qué capítulo va (lo guarda canal.lua en canal-estado.json).
"""
import datetime
import json
import os
import re

from . import config

ARCHIVO = os.path.join(config.CONFIG_DIR, "grilla.json")
ARCHIVO_ESTADO = os.path.join(config.CONFIG_DIR, "canal-estado.json")

DIAS = {  # clave -> (texto, días de la semana: 0 = lunes ... 6 = domingo)
    "todos": ("Todos los días", (0, 1, 2, 3, 4, 5, 6)),
    "lun-vie": ("Lunes a viernes", (0, 1, 2, 3, 4)),
    "finde": ("Sábado y domingo", (5, 6)),
    "sab": ("Sábados", (5,)),
    "dom": ("Domingos", (6,)),
}
ORDEN_DIAS = ("todos", "lun-vie", "finde", "sab", "dom")
TIPOS = {"mezcla": "Series mezcladas", "maraton": "Maratón (una serie en orden)"}

POR_DEFECTO = {"bloques": [
    {"nombre": "Mañana de dibujos", "dias": "todos", "hora": "07:00", "tipo": "mezcla", "series": []},
    {"nombre": "La tarde", "dias": "todos", "hora": "13:00", "tipo": "mezcla", "series": []},
    {"nombre": "Noche de series", "dias": "todos", "hora": "20:00", "tipo": "mezcla", "series": []},
    {"nombre": "Trasnoche", "dias": "todos", "hora": "00:00", "tipo": "mezcla", "series": []},
    {"nombre": "Maratón del domingo", "dias": "dom", "hora": "10:00", "tipo": "maraton", "series": []},
    {"nombre": "Domingo a la noche", "dias": "dom", "hora": "21:00", "tipo": "mezcla", "series": []},
]}


# --- guardar y leer -------------------------------------------------------------
def _hora_ok(hora):
    m = re.match(r"^(\d{1,2}):(\d{2})$", str(hora))
    return bool(m) and int(m.group(1)) < 24 and int(m.group(2)) < 60


def cargar():
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
        bloques = [b for b in datos.get("bloques", [])
                   if b.get("dias") in DIAS and _hora_ok(b.get("hora")) and b.get("tipo") in TIPOS]
        if bloques:
            for b in bloques:
                b.setdefault("nombre", "Bloque")
                b["series"] = [s for s in b.get("series", []) if isinstance(s, str)]
            return {"bloques": bloques}
    except (OSError, ValueError, AttributeError):
        pass
    return json.loads(json.dumps(POR_DEFECTO))  # copia


def guardar(grilla):
    os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
    temporal = ARCHIVO + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(grilla, f, ensure_ascii=False, indent=1)
    os.replace(temporal, ARCHIVO)


def leer_estado():
    try:
        with open(ARCHIVO_ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


# --- horarios ---------------------------------------------------------------------
def minutos(hora):
    h, m = hora.split(":")
    return int(h) * 60 + int(m)


def semana(grilla):
    """Todos los arranques de bloque de la semana: [(minuto de la semana, índice)], en orden.
    Si dos bloques empiezan a la misma hora, gana el de días más específicos."""
    especificidad = {"todos": 0, "lun-vie": 1, "finde": 2, "sab": 3, "dom": 3}
    por_minuto = {}
    for i, b in enumerate(grilla["bloques"]):
        for d in DIAS[b["dias"]][1]:
            m = d * 1440 + minutos(b["hora"])
            if m not in por_minuto or especificidad[b["dias"]] >= especificidad[
                    grilla["bloques"][por_minuto[m]]["dias"]]:
                por_minuto[m] = i
    return sorted(por_minuto.items())


def bloque_en(grilla, cuando=None):
    """Índice del bloque que está al aire en ese momento (por defecto, ahora)."""
    cuando = cuando or datetime.datetime.now()
    m = cuando.weekday() * 1440 + cuando.hour * 60 + cuando.minute
    tabla = semana(grilla)
    if not tabla:
        return None
    actual = tabla[-1][1]  # antes del primero del lunes sigue el último del domingo
    for inicio, i in tabla:
        if inicio <= m:
            actual = i
        else:
            break
    return actual


def guia_del_dia(grilla, dia=None):
    """[(hora, índice)] de los bloques que arrancan ese día (0 = lunes), en orden."""
    dia = datetime.date.today().weekday() if dia is None else dia
    return [("%02d:%02d" % divmod(m - dia * 1440, 60), i)
            for m, i in semana(grilla) if dia * 1440 <= m < (dia + 1) * 1440]


# --- series ---------------------------------------------------------------------
# Carpetas que son partes de una serie (temporadas, arcos...) y no series distintas
_PARTE = re.compile(r"^(\d+[\s._-]|temporada|season|saga|arco|arc\b|parte|part\b|vol|disco|dvd|"
                    r"cd\s*\d|[ts]\s*\d|cap|episod|ova|especial|pel[ií]cula|movie|serie\s*\d)", re.I)


def _con_videos(carpeta):
    return config.tiene_archivos(carpeta, config.EXT_VIDEO)


def _subcarpetas(carpeta):
    try:
        nombres = sorted(os.listdir(carpeta), key=config.clave_natural)
    except OSError:
        return []
    return [os.path.join(carpeta, n) for n in nombres
            if not n.startswith(".") and os.path.isdir(os.path.join(carpeta, n))]


def _limpiar_nombre(nombre):
    """El nombre de la carpeta sin "Copia de", "1080p.WEB-DL"... ni signos sueltos."""
    return config.nombre_lindo(nombre + ".carpeta").strip("+-_ ").strip() or nombre


def _es_pack(carpeta):
    """¿Es un pack de varias series (y no una serie con temporadas)?"""
    hijas = [c for c in _subcarpetas(carpeta) if _con_videos(c)]
    if len(hijas) < 2:
        return False
    distintas = sum(1 for c in hijas if not _PARTE.match(os.path.basename(c)))
    return distintas * 2 > len(hijas)


def carpetas_de_series():
    """{nombre de la serie: [(carpeta, recursivo)]} de la netbook y los discos."""
    bases = [os.path.join(r, "Canal", "Programas") for r in config.raices()]
    if not any(os.path.isdir(b) and _con_videos(b) for b in bases):
        bases = [os.path.join(r, "Videos") for r in config.raices()]
        sueltas = [ruta for _, ruta, _ in config.carpetas_sueltas(config.EXT_VIDEO)]
    else:
        sueltas = []
    series = {}
    candidatas = []
    for b in bases:
        candidatas += [c for c in _subcarpetas(b) if _con_videos(c)]
    candidatas += sueltas
    for c in candidatas:
        partes = [h for h in _subcarpetas(c) if _con_videos(h)] if _es_pack(c) else [c]
        for p in partes:
            series.setdefault(_limpiar_nombre(os.path.basename(p)), []).append((p, True))
    # videos sueltos directo en Programas: "Varios"
    for b in bases:
        if config.listar_archivos(b, config.EXT_VIDEO, recursivo=False):
            series.setdefault("Varios", []).append((b, False))
    return series


def _clave_episodio(rel):
    partes = rel.split(os.sep)
    archivo = partes[-1]
    n = config.numero_episodio(archivo)
    return ([config.clave_natural(p) for p in partes[:-1]],
            float("inf") if n is None else n, config.clave_natural(archivo))


def episodios(carpetas):
    """[(ruta, título)] de una serie, en orden (carpetas por nombre, capítulos por número)."""
    salida = []
    for c, recursivo in carpetas:
        archivos = config.listar_archivos(c, config.EXT_VIDEO, recursivo=recursivo)
        archivos.sort(key=lambda r: _clave_episodio(os.path.relpath(r, c)))
        for r in archivos:
            nombre = os.path.basename(r)
            salida.append((r, config.titulo_episodio(nombre)))
    return salida


def resolver(grilla, series, cuando=None):
    """Bloques listos para el canal: "todas" -> la lista entera; maratón sin serie -> una
    distinta cada semana. Las series que no están (disco desenchufado) se sacan."""
    nombres = sorted(series, key=config.clave_natural)
    semana_num = (cuando or datetime.date.today()).isocalendar()[1]
    listos = []
    for b in grilla["bloques"]:
        propias = [s for s in b["series"] if s in series]
        if b["tipo"] == "maraton":
            if propias:
                elegidas = propias[:1]
            else:  # sin elegir: una serie distinta cada semana
                elegidas = [nombres[semana_num % len(nombres)]] if nombres else []
        else:
            elegidas = propias or nombres
        listos.append({"nombre": b["nombre"], "tipo": b["tipo"], "series": elegidas})
    return listos


def armar_catalogo(opciones, ruta_salida):
    """Escribe el JSON que usa canal.lua. Devuelve la ruta, o None si no hay programas."""
    carpetas = carpetas_de_series()
    series = {}
    for nombre, cs in carpetas.items():
        eps = episodios(cs)
        if eps:
            series[nombre] = [{"ruta": r, "titulo": t} for r, t in eps]
    if not series:
        return None
    grilla = cargar()
    try:
        por_corte = max(0, int(opciones.get("TANDAS_POR_CORTE", "2")))
    except ValueError:
        por_corte = 2
    catalogo = {
        "series": series,
        "bloques": resolver(grilla, series),
        "semana": [[m, i] for m, i in semana(grilla)],
        "tandas": config.listar_en_todas(("Canal", "Tandas"), config.EXT_VIDEO),
        "cortinas": config.listar_en_todas(("Canal", "Cortinas"), config.EXT_VIDEO),
        "por_corte": por_corte,
        "estado": ARCHIVO_ESTADO,
    }
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False)
    return ruta_salida
