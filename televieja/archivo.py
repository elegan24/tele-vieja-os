"""Internet Archive (archive.org): dibujos, series y películas viejas, gratis y legales.

Busca con la API pública de archive.org y elige, de cada video, la versión más liviana
(los MP4 de 512 kb o los h.264 chicos): en la tele de tubo se ve igual y la netbook
los reproduce sin trabarse. mpv los mira directo por internet, sin bajarlos.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from . import config

BASE = "https://archive.org"
AGENTE = {"User-Agent": "Frecuencia99/1.0 (reproductor para tele de tubo)"}
FILAS = 40

# (nombre en el menú, búsqueda)
CATEGORIAS = [
    ("Dibujos animados clásicos", "collection:(classic_cartoons OR animationandcartoons)"),
    ("Series de TV clásicas", "collection:classic_tv"),
    ("En español", "collection:(feature_films OR classic_tv OR animationandcartoons) "
                   "AND language:(spa OR Spanish OR Español)"),
    ("Películas clásicas", "collection:feature_films"),
    ("Comedias", "collection:Comedy_Films"),
    ("Ciencia ficción y terror", "collection:SciFi_Horror"),
    ("Cine negro y policiales", "collection:Film_Noir"),
    ("Cine mudo", "collection:silent_films"),
    ("Publicidades viejas", "collection:classic_tv_commercials"),
]

# Es una tele para toda la familia: afuera lo que es para adultos
FILTRO = ("NOT subject:(sex* OR erotic* OR adult OR nudity OR porn* OR exploitation OR "
          "sexploitation) AND NOT title:(sex* OR erotic* OR porn* OR nude* OR molester OR "
          "desnud* OR xxx)")

# De las versiones de un mismo video, cuál conviene (primero la más liviana)
PREFERENCIA = ["512Kb MPEG4", "h.264 IA", "h.264", "MPEG4", "Ogg Video", "WebM", "Matroska",
               "MPEG1", "Cinepack", "QuickTime", "AVI", "DivX", "Windows Media", "MPEG2"]


class SinConexion(RuntimeError):
    pass


def _pedir(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=AGENTE)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise SinConexion("archive.org respondió con un error (%d). Probá más tarde." % e.code)
    except (urllib.error.URLError, OSError) as e:
        motivo = str(getattr(e, "reason", e))
        if "CERTIFICATE" in motivo.upper():
            raise SinConexion("La netbook tiene mal la fecha y la hora: sin eso no anda "
                              "internet seguro. Conectate y reiniciá para que se ponga en hora.")
        raise SinConexion("No hay internet (o archive.org no responde).")
    except ValueError:
        raise SinConexion("archive.org mandó una respuesta rara. Probá de nuevo.")


def _limpiar_busqueda(texto):
    """Lo que escribió la persona, sin los signos que la búsqueda usa para otra cosa."""
    texto = re.sub(r'[():"\[\]{}^~*?\\/!]', " ", texto)
    palabras = [p for p in texto.split() if p.upper() not in ("AND", "OR", "NOT")]
    return " ".join(palabras)


def consulta_de_texto(texto):
    """Busca las palabras en el título (todas) o, si no, en la descripción y los temas."""
    limpio = _limpiar_busqueda(texto)
    if not limpio:
        return ""
    return "title:(%s) OR subject:(%s) OR description:(%s)" % (limpio, limpio, limpio)


def buscar(consulta, pagina=1):
    """Resultados de una búsqueda: (total, [{"id", "titulo", "anio"}])."""
    if not consulta:
        return 0, []
    params = [("q", "(%s) AND mediatype:movies AND %s" % (consulta, FILTRO)),
              ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "year"),
              ("sort[]", "downloads desc"), ("rows", str(FILAS)), ("page", str(pagina)),
              ("output", "json")]
    datos = _pedir(BASE + "/advancedsearch.php?" + urllib.parse.urlencode(params))
    respuesta = datos.get("response", {})
    resultados = []
    for d in respuesta.get("docs", []):
        titulo = d.get("title") or d.get("identifier")
        if isinstance(titulo, list):
            titulo = titulo[0]
        anio = d.get("year")
        if isinstance(anio, list):
            anio = anio[0]
        resultados.append({"id": d["identifier"], "titulo": str(titulo).strip(),
                           "anio": str(anio)[:4] if anio else ""})
    return int(respuesta.get("numFound", 0)), resultados


def _nombre_sin_version(nombre):
    base = os.path.splitext(os.path.basename(nombre))[0]
    return re.sub(r"([._]512kb|\.ia)$", "", base, flags=re.I)


def elegir_videos(archivos):
    """De la lista de archivos de un ítem, un video por capítulo (la versión más liviana),
    en orden. Cada uno: {"nombre", "titulo", "tamano"}."""
    grupos = {}
    for f in archivos:
        formato = f.get("format", "")
        if formato not in PREFERENCIA:
            continue
        clave = f.get("original") if f.get("source") == "derivative" and f.get("original") \
            else f.get("name")
        if isinstance(clave, list):
            clave = clave[0]
        grupos.setdefault(clave, []).append(f)
    videos = []
    for clave, opciones in grupos.items():
        def costo(f):
            try:
                tamano = int(f.get("size", 0))
            except ValueError:
                tamano = 0
            return PREFERENCIA.index(f["format"]), tamano
        mejor = min(opciones, key=costo)
        titulo = mejor.get("title") or next((o.get("title") for o in opciones if o.get("title")), "")
        if isinstance(titulo, list):
            titulo = titulo[0]
        nombre_base = _nombre_sin_version(clave)
        try:
            tamano = int(mejor.get("size", 0))
        except ValueError:
            tamano = 0
        videos.append({"nombre": mejor["name"],
                       "titulo": str(titulo).strip() or config.nombre_lindo(nombre_base + ".x"),
                       "tamano": tamano, "orden": clave})
    videos.sort(key=lambda v: (
        [config.clave_natural(p) for p in os.path.dirname(v["orden"]).split("/")],
        config.numero_episodio(os.path.basename(v["orden"])) or float("inf"),
        config.clave_natural(os.path.basename(v["orden"]))))
    for v in videos:
        del v["orden"]
    return videos


def url_de(identificador, nombre):
    return "%s/download/%s/%s" % (BASE, urllib.parse.quote(identificador),
                                  urllib.parse.quote(nombre))


def videos(identificador):
    """(título del ítem, [{"titulo", "url"}]) con los videos que se pueden ver."""
    datos = _pedir(BASE + "/metadata/" + urllib.parse.quote(identificador))
    titulo = datos.get("metadata", {}).get("title") or identificador
    if isinstance(titulo, list):
        titulo = titulo[0]
    lista = [{"titulo": v["titulo"], "url": url_de(identificador, v["nombre"]),
              "tamano": v["tamano"]}
             for v in elegir_videos(datos.get("files", []))]
    return str(titulo), lista


def lista_m3u(titulo, elegidos):
    """Arma una lista para mpv con los títulos lindos (si no, muestra la dirección)."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    ruta = os.path.join(config.CACHE_DIR, "archivo.m3u")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in elegidos:
            f.write("#EXTINF:-1,%s\n%s\n" % (v["titulo"].replace("\n", " "), v["url"]))
    return ruta
