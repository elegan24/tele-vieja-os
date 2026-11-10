"""Prueba de las descargas: el reparto de archivos, la cola y la página del celu.

Uso:  python3 pruebas/prueba_descargas.py
      TELEVIEJA_PRUEBA_RED=/ruta/al/python/con/gdown python3 pruebas/prueba_descargas.py
      (lo segundo además baja de verdad la carpeta de prueba pública de gdown)
"""
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
TMP = tempfile.mkdtemp(prefix="televieja-descargas-")
os.environ["TELEVIEJA_RAIZ"] = os.path.join(TMP, "TeleVieja")
os.environ["TELEVIEJA_CONFIG"] = os.path.join(TMP, "config")
os.environ["HOME"] = TMP
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AQUI)

import pygame  # noqa: E402

pygame.display.init()

from televieja import acomodar, config, descargas, remoto  # noqa: E402

R = config.RAIZ


def tocar(ruta, contenido=b"x"):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(contenido)


def existe(*partes):
    return os.path.isfile(os.path.join(R, *partes))


def probar_acomodar():
    dat = os.path.join(TMP, "arcade.dat")
    with open(dat, "w") as f:
        f.write('game (\n\tname "Street Fighter Alpha"\n\trom ( name sfa.zip size 1 )\n)\n')
    config.ARCHIVO_NOMBRES_ARCADE = dat
    config._nombres_arcade = None

    o = os.path.join(TMP, "bajado")
    pack = os.path.join(o, "Mega Pack")
    tocar(os.path.join(pack, "Los Simpsons", "T01", "01 - Bart el genio.mkv"))
    tocar(os.path.join(pack, "Los Simpsons", "T01", "02.avi"))
    tocar(os.path.join(pack, "Juegos", "Contra (U).nes"))
    tocar(os.path.join(pack, "Juegos", "Super Mario World.sfc"))
    tocar(os.path.join(pack, "Juegos", "sfa.zip"))                       # arcade: tal cual
    tocar(os.path.join(pack, "Comics", "Kaliman 001.cbr"))
    tocar(os.path.join(pack, "Radionovelas", "Kaliman 001.mp3"))
    tocar(os.path.join(pack, "PS1", "Crash.cue"), b'FILE "Crash.bin" BINARY\n')
    tocar(os.path.join(pack, "PS1", "Crash.bin"))
    tocar(os.path.join(pack, "Sonic R", "SONICR.EXE"))                   # juego de PC: entero
    tocar(os.path.join(pack, "Sonic R", "MUSIC", "track02.ogg"))
    tocar(os.path.join(pack, "leeme.txt"))
    tocar(os.path.join(pack, "suelto.bin"))                              # ambiguo: a Descargas
    for i in range(1, 5):                                                # páginas sueltas
        tocar(os.path.join(pack, "Mafalda Tomo 1", "%03d.jpg" % i))
    # un .zip con un solo juego (va entero) y un pack .zip (se descomprime)
    with zipfile.ZipFile(os.path.join(pack, "Juegos", "Tetris.zip"), "w") as z:
        z.writestr("Tetris (W).gb", b"rom")
    with zipfile.ZipFile(os.path.join(pack, "Family pack.zip"), "w") as z:
        for n in ("Duck Hunt.nes", "Pac-Man.nes", "Excitebike.nes", "Tetris.nes"):
            z.writestr("Family pack/" + n, b"rom")
        z.writestr("Family pack/leeme.txt", b"hola")
        z.writestr("../../escape.nes", b"malo")                         # intento de escaparse

    resumen = acomodar.acomodar(o, R)
    print("resumen:", acomodar.describir(resumen))
    assert existe("Videos", "Mega Pack", "Los Simpsons", "T01", "01 - Bart el genio.mkv")
    assert existe("Juegos", "Family", "Mega Pack", "Juegos", "Contra (U).nes")
    assert existe("Juegos", "SuperNintendo", "Mega Pack", "Juegos", "Super Mario World.sfc")
    assert existe("Juegos", "Arcade", "sfa.zip")
    assert existe("Juegos", "GameBoy", "Mega Pack", "Juegos", "Tetris.zip")
    assert existe("Historietas", "Mega Pack", "Comics", "Kaliman 001.cbr")
    assert existe("Historietas", "Mega Pack", "Mafalda Tomo 1", "001.jpg")
    assert existe("Radio", "Mega Pack", "Radionovelas", "Kaliman 001.mp3")
    assert existe("Juegos", "PlayStation", "Mega Pack", "PS1", "Crash.cue")
    assert existe("Juegos", "PlayStation", "Mega Pack", "PS1", "Crash.bin")
    assert existe("Descargas", "Mega Pack", "Sonic R", "SONICR.EXE")
    assert existe("Descargas", "Mega Pack", "Sonic R", "MUSIC", "track02.ogg")  # no se pierde
    assert existe("Descargas", "Mega Pack", "leeme.txt")
    assert existe("Descargas", "Mega Pack", "suelto.bin")
    assert existe("Juegos", "Family", "Mega Pack", "Family pack", "Family pack", "Duck Hunt.nes")
    assert not os.path.exists(os.path.join(TMP, "escape.nes"))
    assert not os.path.exists(os.path.join(R, "escape.nes"))
    assert not os.path.exists(o), "la carpeta temporal tenía que borrarse"
    total = sum(resumen.values())
    assert total == 23, (total, resumen)


FALSO = r'''
import json, os, sys, time
url, destino = sys.argv[1], sys.argv[2]
def ev(**d): print("@@ " + json.dumps(d), flush=True)
if "roto" in url:
    ev(error="No se puede bajar: el link tiene que estar compartido"); sys.exit(1)
ev(nombre="Dibujitos")
ev(total=2, incompletas=1)
for i, n in enumerate(["Cap 1.mp4", "Cap 2.mp4"], 1):
    ev(archivo=i, de=2, ruta="Temporada/" + n)
    print("  50%|#####     | 1/2", end="\r", flush=True)
    os.makedirs(os.path.join(destino, "Dibujitos", "Temporada"), exist_ok=True)
    open(os.path.join(destino, "Dibujitos", "Temporada", n), "w").write("v")
    time.sleep(0.2)
ev(listo=2, fallados=0)
'''


def esperar(gestor, ident, estados=("listo", "error", "cancelado"), limite=20):
    fin = time.time() + limite
    while time.time() < fin:
        d = [t for t in gestor.lista() if t["id"] == ident][0]
        if d["estado"] in estados:
            return d
        time.sleep(0.1)
    raise AssertionError("no terminó: %r" % d)


def probar_gestor():
    falso = os.path.join(TMP, "falso.py")
    with open(falso, "w") as f:
        f.write(FALSO)
    descargas.PYTHON_DRIVE = sys.executable
    descargas.BAJAR_DRIVE = falso
    g = descargas.Gestor(R)
    for malo in ("", "hola", "ftp://x/y", "javascript:alert(1)"):
        try:
            g.agregar(malo)
            raise AssertionError("tenía que rechazar %r" % malo)
        except ValueError:
            pass
    t = g.agregar("https://drive.google.com/drive/folders/ABC?usp=sharing")
    try:
        g.agregar("https://drive.google.com/drive/folders/ABC?usp=sharing")
        raise AssertionError("tenía que rechazar el repetido")
    except ValueError:
        pass
    d = esperar(g, t.id)
    assert d["estado"] == "listo", d
    assert d["nombre"] == "Dibujitos" and d["total"] == 2, d
    assert any("50 archivos" in a for a in d["avisos"]), d["avisos"]
    assert existe("Videos", "Dibujitos", "Temporada", "Cap 2.mp4")
    assert "2 videos" in d["resumen"], d["resumen"]
    novedades = g.tomar_novedades()
    assert novedades and "Descarga lista: Dibujitos" in novedades[0], novedades
    t2 = g.agregar("https://drive.google.com/file/d/roto/view")
    d2 = esperar(g, t2.id)
    assert d2["estado"] == "error" and "compartido" in d2["mensaje"], d2
    return g


def probar_web(g):
    remoto.gestor = g
    servidor = remoto.iniciar(18282)
    assert servidor

    def pedir(ruta, datos=None):
        cuerpo = json.dumps(datos).encode() if datos is not None else None
        req = urllib.request.Request("http://127.0.0.1:18282" + ruta, data=cuerpo,
                                     method="POST" if cuerpo is not None else "GET",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    codigo, d = pedir("/descargar", {"url": "no es un link"})
    assert codigo == 400 and "link" in d["error"], d
    codigo, d = pedir("/descargar", {"url": "https://drive.google.com/drive/folders/XYZ"})
    assert codigo == 200 and d["ok"], d
    codigo, d = pedir("/descargas")
    assert codigo == 200 and d["descargas"][0]["url"].endswith("XYZ"), d
    pagina = urllib.request.urlopen("http://127.0.0.1:18282/").read().decode()
    assert 'id="form-bajar"' in pagina
    esperar(g, d["descargas"][0]["id"])


def probar_red(python_con_gdown):
    """Baja de verdad la carpeta pública de prueba del proyecto gdown."""
    descargas.PYTHON_DRIVE = python_con_gdown
    descargas.BAJAR_DRIVE = os.path.join(AQUI, "televieja", "bajar_drive.py")
    g = descargas.Gestor(R)
    t = g.agregar("https://drive.google.com/drive/folders/1KpLl_1tcK0eeehzN980zbG-3M2nhbVks")
    d = esperar(g, t.id, limite=180)
    print("red:", d["estado"], d["nombre"], d["resumen"], d["mensaje"])
    assert d["estado"] == "listo", d
    assert existe("Descargas", "gdown_folder_test", "this is a file.txt")


def main():
    probar_acomodar()
    g = probar_gestor()
    probar_web(g)
    red = os.environ.get("TELEVIEJA_PRUEBA_RED")
    if red:
        probar_red(red)
    print("OK - descargas")


if __name__ == "__main__":
    main()
