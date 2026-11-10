#!/usr/bin/env python3
"""Baja un link público de Google Drive (un archivo o una carpeta entera).

Lo corre descargas.py con el Python que tiene gdown (/opt/televieja/pyenv).
Uso: bajar_drive.py URL CARPETA_DESTINO

Escribe renglones "@@ {json}" para contar cómo va. El resto de lo que imprime
(la barrita de gdown) también sirve: de ahí se saca el porcentaje.
"""
import importlib
import json
import os
import re
import shutil
import sys

import gdown

ESPACIO_MINIMO = 500 * 1024 * 1024  # dejamos siempre medio GB libre


def evento(**datos):
    print("@@ " + json.dumps(datos, ensure_ascii=False), flush=True)


def limpio(nombre):
    """Nombre seguro para una carpeta o archivo (sin barras ni cosas raras)."""
    nombre = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", nombre or "").strip(" .")
    return nombre[:150] or "sin nombre"


def traducir(mensaje):
    if "Too many users" in mensaje or "many accesses" in mensaje:
        return ("Google frenó la descarga: este archivo se bajó demasiadas veces hoy "
                "(cuota). Probá de nuevo mañana.")
    if "permission" in mensaje or "public link" in mensaje or "Cannot retrieve" in mensaje:
        return ("No se puede bajar: el link tiene que estar compartido como "
                "\"Cualquier persona con el enlace\".")
    if "No space left" in mensaje:
        return "Se llenó el disco."
    return mensaje.strip().splitlines()[-1][:200] if mensaje.strip() else "Error desconocido"


def hay_lugar(carpeta):
    return shutil.disk_usage(carpeta).free > ESPACIO_MINIMO


def es_carpeta(url):
    return "/folders/" in url or "folderview" in url


def bajar_archivo(url, destino):
    evento(total=1, incompletas=0)
    evento(archivo=1, de=1, ruta="")
    if not hay_lugar(destino):
        raise RuntimeError("No space left: el disco está casi lleno")
    ruta = gdown.download(url, output=destino + os.sep, quiet=False, fuzzy=True,
                          use_cookies=False)
    if not ruta:
        raise RuntimeError("No se pudo bajar el archivo")
    evento(nombre=os.path.basename(ruta), listo=1, fallados=0)


def bajar_carpeta(url, destino):
    modulo = importlib.import_module("gdown.download_folder")
    import requests
    sesion = requests.session()
    evento(leyendo=True)
    # quiet=False: gdown va escribiendo "Retrieving folder..." y "Processing file..."
    # mientras recorre las subcarpetas; descargas.py lo usa para mostrar el avance.
    ok, raiz = modulo._download_and_parse_google_drive_link(
        sesion, url, quiet=False, remaining_ok=True, verify=True)
    if not ok or raiz is None:
        raise RuntimeError("Cannot retrieve the folder")
    nombre = limpio(raiz.name)
    evento(nombre=nombre)

    archivos = []
    incompletas = 0

    def recorrer(nodo, ruta):
        nonlocal incompletas
        # Sin cuenta, Google muestra como mucho 50 cosas por carpeta.
        if len(nodo.children) >= modulo.MAX_NUMBER_FILES:
            incompletas += 1
        for hijo in nodo.children:
            if hijo.is_folder():
                recorrer(hijo, os.path.join(ruta, limpio(hijo.name)))
            else:
                archivos.append((hijo.id, os.path.join(ruta, limpio(hijo.name))))

    recorrer(raiz, "")
    evento(total=len(archivos), incompletas=incompletas)
    fallados = 0
    for i, (ident, relativa) in enumerate(archivos, 1):
        evento(archivo=i, de=len(archivos), ruta=relativa)
        local = os.path.join(destino, nombre, relativa)
        if os.path.exists(local):
            continue  # ya estaba (se puede reanudar una descarga cortada)
        if not hay_lugar(destino):
            evento(aviso="Se llenó el disco: corto acá.", ruta=relativa)
            fallados += len(archivos) - i + 1
            break
        os.makedirs(os.path.dirname(local), exist_ok=True)
        try:
            listo = gdown.download(id=ident, output=local, quiet=False, resume=True,
                                   use_cookies=False)
        except Exception as e:  # noqa: BLE001 - un archivo que falla no corta el resto
            listo = None
            evento(aviso=traducir(str(e)), ruta=relativa)
        if not listo:
            fallados += 1
    evento(listo=len(archivos) - fallados, fallados=fallados)


def main():
    if len(sys.argv) != 3:
        print("Uso: bajar_drive.py URL CARPETA_DESTINO", file=sys.stderr)
        sys.exit(2)
    url, destino = sys.argv[1], sys.argv[2]
    os.makedirs(destino, exist_ok=True)
    try:
        if es_carpeta(url):
            bajar_carpeta(url, destino)
        else:
            bajar_archivo(url, destino)
    except Exception as e:  # noqa: BLE001 - se le muestra al usuario
        evento(error=traducir(str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
