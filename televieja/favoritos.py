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
