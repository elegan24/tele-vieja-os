"""Arma las órdenes para mpv (videos, canal, radio) y RetroArch (juegos)."""
import json
import os
import random
import socket
import subprocess

from . import config

SOCKET_MPV = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "televieja-mpv.sock")
LOG_DIR = config.CACHE_DIR


def ruta_log(nombre):
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, nombre + ".log")


# En 720x480 / 720x576 (HDMI a la tele) cada pixel no es cuadrado: la tele lo muestra en 4:3.
ASPECTO_PIXEL = {"720x480": "0.8889", "720x576": "1.0667"}


def salida_bluetooth():
    """Si hay un auricular Bluetooth conectado, su salida de sonido ALSA (o None)."""
    try:
        r = subprocess.run(["bluealsa-aplay", "-L"], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return None
    for linea in r.stdout.splitlines():
        if linea.startswith("bluealsa:") and "PROFILE=a2dp" in linea:
            # sin ",SRV=..." (es el servicio por defecto)
            return ",".join(p for p in linea.strip().split(",") if not p.startswith("SRV="))
    return None


def mpv_base():
    orden = ["mpv", "--fullscreen", "--input-ipc-server=" + SOCKET_MPV]
    auricular = salida_bluetooth()
    if auricular:
        orden.append("--audio-device=alsa/" + auricular)
    try:
        with open("/tmp/televieja-resolucion") as f:
            res = f.read().strip()
    except OSError:
        res = ""
    if res in ASPECTO_PIXEL:
        orden.append("--monitorpixelaspect=" + ASPECTO_PIXEL[res])
    return orden


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


def orden_canal(opciones, lista, color="&HFFFFFF&"):
    nombre = opciones.get("NOMBRE_CANAL", "FRECUENCIA 99").replace(",", " ")
    opts = "canal-nombre=%s,canal-reloj=%s,canal-empezado=%s,canal-color=%s" % (
        nombre,
        "si" if config.opcion_si(opciones, "CANAL_RELOJ") else "no",
        "si" if config.opcion_si(opciones, "CANAL_EMPEZADO") else "no",
        color,
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
    extras = []
    if os.path.isfile(config.ARCHIVO_RA_JOYSTICK):
        extras.append(config.ARCHIVO_RA_JOYSTICK)
    auricular = salida_bluetooth()
    if auricular:
        # el Bluetooth tarda un poco más: más margen para que no se entrecorte
        ruta = os.path.join(config.CONFIG_DIR, "retroarch-auricular.cfg")
        with open(ruta, "w") as f:
            f.write('audio_device = "%s"\naudio_latency = "200"\n' % auricular)
        extras.append(ruta)
    if extras:
        orden += ["--appendconfig", "|".join(extras)]
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
        "inicio": ("quit",),
    }
    if boton in acciones:
        mpv_comando(*acciones[boton])
        if boton in ("up", "down"):
            mpv_comando("show-text", "Volumen: ${volume}%")
    return boton in ("b", "inicio")


def control_canal(boton):
    acciones = {
        "b": ("quit",),
        "right": ("playlist-next",), "r": ("playlist-next",),
        "up": ("add", "volume", "5"), "down": ("add", "volume", "-5"),
        "a": ("show-text", "${media-title}", "3000"),
        "start": ("cycle", "pause"),
        "l": ("show-text", "${media-title}", "3000"),
        "inicio": ("quit",),
    }
    if boton in acciones:
        mpv_comando(*acciones[boton])
        if boton in ("up", "down"):
            mpv_comando("show-text", "Volumen: ${volume}%")
    return boton in ("b", "inicio")


def control_juego_remoto(boton):
    """Botones del celular mientras se juega: le hablan a RetroArch por la red local."""
    ordenes = {"b": "QUIT", "inicio": "QUIT", "start": "PAUSE_TOGGLE",
               "r": "SAVE_STATE", "l": "LOAD_STATE", "select": "MENU_TOGGLE"}
    orden = ordenes.get(boton)
    if orden:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(orden.encode("ascii"), ("127.0.0.1", 55355))
            s.close()
        except OSError:
            pass
    return orden == "QUIT"
