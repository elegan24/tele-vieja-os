"""YouTube liviano: buscar con yt-dlp y ver en mpv en 360p (H.264, lo más fácil de
decodificar para la netbook).

yt-dlp y deno (el motor de JavaScript que hoy YouTube le exige a yt-dlp) van en el Python
aparte de Frecuencia 99 (pyenv) y se actualizan con "Actualizar".
Se busca en "modo restringido" de YouTube: es una tele para toda la familia.
"""
import json
import os
import subprocess

from . import config

YTDLP = os.path.join(config.APP_DIR, "pyenv", "bin", "yt-dlp")
DENO = os.path.join(config.APP_DIR, "pyenv", "bin", "deno")
ARCHIVO_COOKIES = os.path.join(config.CONFIG_DIR, "youtube-cookies.txt")
# 360p H.264 + audio m4a; si no hay, lo más chico que haya hasta 480p
FORMATO = ("bv*[height<=360][vcodec^=avc1]+ba[ext=m4a]/b[height<=360]/"
           "bv*[height<=480][vcodec^=avc1]+ba/b[height<=480]/b")
CANTIDAD = 30
ARCHIVO_RECIENTES = os.path.join(config.CONFIG_DIR, "youtube-recientes.json")

SUGERENCIAS = [
    "Dibujos animados clásicos en español",
    "Publicidades argentinas de los 90",
    "Tandas publicitarias de los 80",
    "Música de los 80 en vivo",
    "Presentaciones de canales de TV viejos",
    "Documentales de historia",
]


class SinYoutube(RuntimeError):
    pass


def instalado():
    return os.path.isfile(YTDLP)


def archivo_cookies():
    """La cookie del "modo restringido" de YouTube (PREF=f2=8000000), en el formato de
    archivo que lee yt-dlp."""
    os.makedirs(os.path.dirname(ARCHIVO_COOKIES), exist_ok=True)
    with open(ARCHIVO_COOKIES, "w") as f:
        f.write("# Netscape HTTP Cookie File\n"
                ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tPREF\tf2=8000000\n")
    return ARCHIVO_COOKIES


def _base():
    orden = [YTDLP, "--no-warnings", "--cookies", archivo_cookies(),
             "--extractor-args", "youtube:lang=es"]
    if os.path.isfile(DENO):
        orden += ["--js-runtimes", "deno:" + DENO]
    return orden


def _duracion(segundos):
    s = int(segundos or 0)
    if s >= 3600:
        return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)
    return "%d:%02d" % (s // 60, s % 60)


def interpretar(datos):
    """Resultados de "yt-dlp -J --flat-playlist ytsearchN:...": solo videos de verdad
    (ni en vivo ni shorts de menos de un minuto)."""
    salida = []
    for e in datos.get("entries") or []:
        if not e or not e.get("id") or e.get("live_status") in ("is_live", "is_upcoming"):
            continue
        duracion = e.get("duration")
        if not duracion or duracion < 60:
            continue
        salida.append({"id": e["id"], "titulo": (e.get("title") or e["id"]).strip(),
                       "duracion": _duracion(duracion), "canal": e.get("channel") or "",
                       "url": "https://www.youtube.com/watch?v=" + e["id"]})
    return salida


def buscar(texto, cantidad=CANTIDAD):
    if not instalado():
        raise SinYoutube("Falta el programa para YouTube. Entrá a Opciones → Actualizar "
                         "(con internet) y probá de nuevo.")
    try:
        r = subprocess.run(_base() + ["-J", "--flat-playlist", "ytsearch%d:%s" % (cantidad, texto)],
                           capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        raise SinYoutube("YouTube tardó demasiado en contestar. Probá de nuevo.")
    if r.returncode != 0:
        error = (r.stderr or "").strip().splitlines()
        motivo = error[-1] if error else ""
        if "CERTIFICATE" in motivo.upper():
            raise SinYoutube("La netbook tiene mal la fecha y la hora. Conectate a internet y "
                             "reiniciá para que se ponga en hora.")
        if any(p in motivo for p in ("resolve", "Network", "network", "timed out", "urlopen")):
            raise SinYoutube("No hay internet (o YouTube no responde).")
        raise SinYoutube("YouTube no respondió bien. Probá de nuevo; si sigue, entrá a "
                         "Opciones → Actualizar.\n\n" + motivo[-200:])
    try:
        return interpretar(json.loads(r.stdout))
    except ValueError:
        raise SinYoutube("YouTube mandó una respuesta rara. Probá de nuevo.")


def recientes():
    try:
        with open(ARCHIVO_RECIENTES, encoding="utf-8") as f:
            lista = json.load(f)
        return [t for t in lista if isinstance(t, str)][:5]
    except (OSError, ValueError):
        return []


def anotar_busqueda(texto):
    lista = [texto] + [t for t in recientes() if t.lower() != texto.lower()]
    os.makedirs(os.path.dirname(ARCHIVO_RECIENTES), exist_ok=True)
    with open(ARCHIVO_RECIENTES, "w", encoding="utf-8") as f:
        json.dump(lista[:5], f, ensure_ascii=False)


def lista_m3u(videos):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    ruta = os.path.join(config.CACHE_DIR, "youtube.m3u")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            f.write("#EXTINF:-1,%s\n%s\n" % (v["titulo"].replace("\n", " "), v["url"]))
    return ruta


def opciones_mpv():
    """Para que mpv abra los links de YouTube con nuestro yt-dlp y en 360p."""
    opciones = ["--ytdl=yes", "--script-opts-append=ytdl_hook-ytdl_path=" + YTDLP,
                "--ytdl-format=" + FORMATO,
                "--ytdl-raw-options-append=cookies=" + archivo_cookies(),
                "--ytdl-raw-options-append=extractor-args=youtube:lang=es"]
    if os.path.isfile(DENO):
        opciones.append("--ytdl-raw-options-append=js-runtimes=deno:" + DENO)
    return opciones
