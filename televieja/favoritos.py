"""Favoritos y últimos jugados (se guardan en ~/.config/televieja/juegos.json)."""
import json
import os
import time

from . import config

ARCHIVO = os.path.join(config.CONFIG_DIR, "juegos.json")
MAX_ULTIMOS = 12


def cargar():
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = {}
    datos.setdefault("favoritos", [])
    datos.setdefault("ultimos", [])
    return datos


def _guardar(datos):
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    tmp = ARCHIVO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)
    os.replace(tmp, ARCHIVO)


def es_favorito(rom, datos=None):
    datos = datos or cargar()
    return any(f["rom"] == rom for f in datos["favoritos"])


def alternar_favorito(rom, sistema):
    """Agrega o saca de favoritos. Devuelve True si quedó como favorito."""
    datos = cargar()
    if es_favorito(rom, datos):
        datos["favoritos"] = [f for f in datos["favoritos"] if f["rom"] != rom]
        queda = False
    else:
        datos["favoritos"].append({"rom": rom, "sistema": sistema})
        queda = True
    _guardar(datos)
    return queda


def registrar_jugado(rom, sistema):
    datos = cargar()
    datos["ultimos"] = [u for u in datos["ultimos"] if u["rom"] != rom]
    datos["ultimos"].insert(0, {"rom": rom, "sistema": sistema, "cuando": int(time.time())})
    datos["ultimos"] = datos["ultimos"][:MAX_ULTIMOS]
    _guardar(datos)


def disponibles(lista):
    """Solo los que están (un disco USB puede no estar enchufado)."""
    return [e for e in lista if os.path.exists(e["rom"])]


# --- Internet (YouTube e Internet Archive) ------------------------------------
ARCHIVO_INTERNET = os.path.join(config.CONFIG_DIR, "internet-favoritos.json")


def internet():
    """[{"tipo": "youtube"/"archivo", "id", "titulo", "detalle", "url"?}], el último primero."""
    try:
        with open(ARCHIVO_INTERNET, encoding="utf-8") as f:
            lista = json.load(f)
        return [e for e in lista if isinstance(e, dict) and e.get("tipo") and e.get("id")]
    except (OSError, ValueError):
        return []


def es_favorito_internet(tipo, ident, lista=None):
    return any(e["tipo"] == tipo and e["id"] == ident for e in (lista if lista is not None else internet()))


def alternar_internet(entrada):
    """Agrega o saca de Favoritos de Internet. Devuelve True si quedó como favorito."""
    lista = internet()
    if es_favorito_internet(entrada["tipo"], entrada["id"], lista):
        lista = [e for e in lista if not (e["tipo"] == entrada["tipo"] and e["id"] == entrada["id"])]
        queda = False
    else:
        lista.insert(0, entrada)
        queda = True
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    tmp = ARCHIVO_INTERNET + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=1, ensure_ascii=False)
    os.replace(tmp, ARCHIVO_INTERNET)
    return queda
