"""Arma las órdenes para mpv (videos, canal, radio) y RetroArch (juegos)."""
import json
import os
import random
import socket

from . import config

SOCKET_MPV = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "televieja-mpv.sock")
LOG_DIR = config.CACHE_DIR


def ruta_log(nombre):
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, nombre + ".log")


def mpv_base():
    return ["mpv", "--fullscreen", "--input-ipc-server=" + SOCKET_MPV]


def orden_videos(archivos):
    return mpv_base() + ["--save-position-on-quit", "--"] + list(archivos)


def orden_radio(archivos):
    return mpv_base() + [
        "--save-position-on-quit", "--force-window=immediate", "--osd-level=3",
        "--osd-status-msg=${media-title}\n${time-pos} / ${duration}",
        "--image-display-duration=inf", "--",
    ] + list(archivos)


def armar_canal(opciones):
    """Mezcla programas y tandas como un canal de aire. Devuelve la ruta de la lista."""
    programas = config.listar_en_todas(("Canal", "Programas"), config.EXT_VIDEO)
    if not programas:
        programas = config.listar_en_todas(("Videos",), config.EXT_VIDEO)
    if not programas:
        return None
    tandas = config.listar_en_todas(("Canal", "Tandas"), config.EXT_VIDEO)
    try:
        por_corte = max(0, int(opciones.get("TANDAS_POR_CORTE", "2")))
    except ValueError:
        por_corte = 2
    random.shuffle(programas)
    lista = []
    for p in programas:
        lista.append(p)
        if tandas and por_corte:
            lista.extend(random.sample(tandas, min(por_corte, len(tandas))))
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    ruta = os.path.join(config.CACHE_DIR, "canal.m3u")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in lista:
            f.write(item + "\n")
    return ruta


def orden_canal(opciones, lista):
    nombre = opciones.get("NOMBRE_CANAL", "TELE VIEJA").replace(",", " ")
    opts = "canal-nombre=%s,canal-reloj=%s,canal-empezado=%s" % (
        nombre,
        "si" if config.opcion_si(opciones, "CANAL_RELOJ") else "no",
        "si" if config.opcion_si(opciones, "CANAL_EMPEZADO") else "no",
    )
    return mpv_base() + [
        "--script=" + os.path.join(config.SISTEMA_DIR, "canal.lua"),
        "--script-opts=" + opts,
        "--loop-playlist=inf",
        "--playlist=" + lista,
    ]


def orden_juego(core, rom):
    orden = ["retroarch", "--fullscreen"]
    if os.path.isfile(config.ARCHIVO_RA):
        orden += ["--config", config.ARCHIVO_RA]
    if os.path.isfile(config.ARCHIVO_RA_JOYSTICK):
        orden += ["--appendconfig", config.ARCHIVO_RA_JOYSTICK]
    return orden + ["-L", core, rom]


def mpv_comando(*args):
    """Le manda una orden a mpv mientras está reproduciendo (por el socket)."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(SOCKET_MPV)
        s.sendall((json.dumps({"command": list(args)}) + "\n").encode("utf-8"))
        s.close()
    except OSError:
        pass


# Qué hace cada botón del joystick mientras mpv está reproduciendo.
def control_videos(boton):
    acciones = {
        "a": ("cycle", "pause"), "start": ("cycle", "pause"),
        "b": ("quit",),
        "left": ("seek", "-10"), "right": ("seek", "10"),
        "up": ("add", "volume", "5"), "down": ("add", "volume", "-5"),
        "l": ("playlist-prev",), "r": ("playlist-next",),
        "x": ("cycle", "sub"), "y": ("cycle", "audio"),
    }
    if boton in acciones:
        mpv_comando(*acciones[boton])
        if boton in ("up", "down"):
            mpv_comando("show-text", "Volumen: ${volume}%")
    return boton == "b"


def control_canal(boton):
    acciones = {
        "b": ("quit",),
        "right": ("playlist-next",), "r": ("playlist-next",),
        "up": ("add", "volume", "5"), "down": ("add", "volume", "-5"),
        "a": ("show-text", "${media-title}", "3000"),
        "start": ("cycle", "pause"),
    }
    if boton in acciones:
        mpv_comando(*acciones[boton])
        if boton in ("up", "down"):
            mpv_comando("show-text", "Volumen: ${volume}%")
    return boton == "b"
