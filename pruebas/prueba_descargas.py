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
ev(leyendo=True)
print("Retrieving folder AAA Temporada", flush=True)
print("Processing file BBB Cap 1.mp4", flush=True)
time.sleep(0.3)
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
    g = descargas.Gestor(R, archivo=os.path.join(TMP, "fila1.json"), internet=lambda: True)
    for mf in ("https://www.mediafire.com/file/abc123/juego.zip/file",
               "https://www.mediafire.com/folder/abc123/Pack"):
        try:
            g.agregar(mf)
            raise AssertionError("tenía que explicar qué link de MediaFire pegar")
        except ValueError as e:
            assert "MediaFire" in str(e), e
    # el link directo de MediaFire sí se acepta (lo baja la descarga directa)
    assert not descargas.es_drive("https://download1234.mediafire.com/abc/juego.zip")
    descargas.validar("https://download1234.mediafire.com/abc/juego.zip")
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
    vio_lectura = False
    fin = time.time() + 10
    while time.time() < fin and not vio_lectura:
        d = [x for x in g.lista() if x["id"] == t.id][0]
        vio_lectura = d["carpetas_leidas"] == 1 and d["archivos_vistos"] == 1
        time.sleep(0.05)
    assert vio_lectura, "no mostró el avance de la lectura de carpetas"
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
    assert d2["estado"] == "error" and "compartido" in d2["mensaje"], d2   # sin reintentos
    assert d2["intentos"] == 0, d2
    return g


FALSO_CORTES = r'''
import json, os, sys
url, destino = sys.argv[1], sys.argv[2]
def ev(**d): print("@@ " + json.dumps(d), flush=True)
contador = os.path.join(os.path.dirname(destino), "veces-" + os.path.basename(destino))
veces = int(open(contador).read()) if os.path.exists(contador) else 0
open(contador, "w").write(str(veces + 1))
if "nollamar" in url:
    ev(error="no tenía que bajar de nuevo"); sys.exit(1)
ev(nombre="Serie")
ev(total=3, incompletas=0)
carpeta = os.path.join(destino, "Serie")
os.makedirs(carpeta, exist_ok=True)
hechos = 0
fallados = 0
for i in (1, 2, 3):
    ruta = os.path.join(carpeta, "Cap %d.mp4" % i)
    if os.path.exists(ruta):
        hechos += 1; ev(archivo=hechos, de=3, ruta=os.path.basename(ruta)); continue
    if i == 3 and veces == 0:   # la primera vez el tercero falla
        motivo = "Google frenó la descarga: cuota" if "cuota" in url else "Connection reset by peer"
        open(ruta + ".part", "w").write("medio")
        fallados += 1; ev(aviso=motivo, ruta="Cap 3.mp4"); continue
    open(ruta, "w").write("v%d" % veces)
    hechos += 1; ev(archivo=hechos, de=3, ruta=os.path.basename(ruta))
ev(listo=3 - fallados, fallados=fallados)
'''


def probar_reintentos_y_fila():
    falso = os.path.join(TMP, "falso_cortes.py")
    with open(falso, "w") as f:
        f.write(FALSO_CORTES)
    descargas.BAJAR_DRIVE = falso
    rapido = {"red": [0.002, 0.002], "cuota": [0.004]}   # en minutos: para la prueba, casi ya
    fila = os.path.join(TMP, "fila2.json")
    g = descargas.Gestor(R, archivo=fila, esperas=rapido, internet=lambda: True)
    # 1) se corta el WiFi en el tercer capítulo: reintenta solo y no vuelve a bajar los dos primeros
    t = g.agregar("https://drive.google.com/drive/folders/CORTE")
    d = esperar(g, t.id, estados=("reintentar",), limite=10)
    assert "reintenta sola" in d["mensaje"], d
    d = esperar(g, t.id)
    assert d["estado"] == "listo" and d["intentos"] == 1, d
    for i in (1, 2):   # los primeros dos son de la primera vez (no se bajaron de nuevo)
        assert open(os.path.join(R, "Videos", "Serie", "Cap %d.mp4" % i)).read() == "v0"
    assert existe("Videos", "Serie", "Cap 3.mp4")
    assert not existe("Videos", "Serie", "Cap 3.mp4.part"), "el .part tenía que descartarse"
    # 2) cuota de Google: también reintenta (y queda guardado en el archivo de la fila)
    t = g.agregar("https://drive.google.com/drive/folders/cuota")
    d = esperar(g, t.id, estados=("reintentar",), limite=10)
    assert "cuota" in d["mensaje"], d
    guardado = json.load(open(fila))
    assert any(x["id"] == t.id and x["estado"] == "reintentar" for x in guardado), guardado
    d = esperar(g, t.id)
    assert d["estado"] == "listo", d

    # 3) "apagón": la fila guardada se retoma al volver a prender
    fila3 = os.path.join(TMP, "fila3.json")
    temporal = os.path.join(R, "Descargas", ".bajando")
    os.makedirs(os.path.join(temporal, "901", "Peli"), exist_ok=True)
    open(os.path.join(temporal, "901", "Peli", "Peli.mkv"), "w").write("v")
    json.dump([
        {"id": 900, "url": "https://drive.google.com/drive/folders/APAGON", "estado": "bajando",
         "nombre": "Serie", "archivo": 1, "total": 3},
        {"id": 901, "url": "https://drive.google.com/drive/folders/nollamar", "estado": "acomodando",
         "nombre": "Peli"},
        {"id": 902, "url": "https://drive.google.com/drive/folders/VIEJA", "estado": "listo",
         "nombre": "Vieja"},
    ], open(fila3, "w"))
    sin_red = {"hay": False}
    g2 = descargas.Gestor(R, archivo=fila3, esperas=rapido, internet=lambda: sin_red["hay"])
    time.sleep(0.5)
    lista = {d["id"]: d for d in g2.lista()}
    assert lista[900]["estado"] == "esperando", lista[900]
    assert "internet" in lista[900]["actual"], lista[900]     # espera la red, sin gastar intentos
    assert lista[901]["estado"] in ("listo", "acomodando"), lista[901]  # acomodar no necesita red
    sin_red["hay"] = True
    g2.hay_trabajo.set()
    d = esperar(g2, 900, limite=60)
    assert d["estado"] == "listo", d
    assert esperar(g2, 901)["estado"] == "listo"
    assert existe("Videos", "Peli", "Peli.mkv")
    nuevo = g2.agregar("https://drive.google.com/drive/folders/OTRA")
    assert nuevo.id > 902, nuevo.id   # los números siguen después de los guardados
    esperar(g2, nuevo.id, limite=60)


FALSO_TEMPRANO = r'''
import json, os, sys, time
url, destino = sys.argv[1], sys.argv[2]
def ev(**d): print("@@ " + json.dumps(d), flush=True)
lista = ["T1/Cap 1.mp4", "T1/Cap 2.mp4", "Pack.zip", "Juego PC/juego.exe", "Juego PC/intro.avi"]
hechos = set()
p = os.path.join(destino, ".televieja-hechos")
if os.path.exists(p):
    hechos = {l.strip() for l in open(p) if l.strip()}
open(os.path.join(os.path.dirname(destino), "bajados-" + os.path.basename(destino)), "a").write(
    ",".join(r for r in lista if r not in hechos) + "\n")
ev(nombre="Mezcla")
ev(total=len(lista), incompletas=0)
ev(lista=lista)
for i, rel in enumerate(lista, 1):
    if rel not in hechos:
        ruta = os.path.join(destino, "Mezcla", rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        open(ruta, "w").write("x")
    ev(archivo=i, de=len(lista), ruta=rel, ok=True, nuevo=rel not in hechos)
    time.sleep(0.4)
    if "cortar" in url and i == 2 and not hechos:
        ev(error="Se cortó la conexión a internet."); sys.exit(1)
ev(listo=len(lista), fallados=0)
'''


def probar_temprano():
    """Lo que ya llegó se puede usar mientras baja el resto (y no se vuelve a bajar)."""
    from televieja import acomodar as ac
    el = ac.elegibles_temprano(["T1/Cap 1.mp4", "Pack.zip", "Juego PC/juego.exe",
                                "Juego PC/intro.avi", "PS1/Crash.cue", "Comics/K.cbr", "a.nes"])
    assert el == {"T1/Cap 1.mp4", "Comics/K.cbr", "a.nes"}, el
    falso = os.path.join(TMP, "falso_temprano.py")
    with open(falso, "w") as f:
        f.write(FALSO_TEMPRANO)
    descargas.BAJAR_DRIVE = falso
    g = descargas.Gestor(R, archivo=os.path.join(TMP, "fila5.json"), internet=lambda: True,
                         esperas={"red": [0.003]})
    t = g.agregar("https://drive.google.com/drive/folders/cortar")
    # antes de que termine, el primer capítulo ya está en Videos
    fin = time.time() + 10
    while time.time() < fin and not existe("Videos", "Mezcla", "T1", "Cap 1.mp4"):
        time.sleep(0.05)
    assert existe("Videos", "Mezcla", "T1", "Cap 1.mp4"), "el capítulo 1 tenía que poder verse ya"
    d = [x for x in g.lista() if x["id"] == t.id][0]
    assert d["estado"] == "bajando", d
    assert not existe("Descargas", "Mezcla", "Juego PC", "intro.avi")   # el juego de PC espera
    d = esperar(g, t.id, limite=30)
    assert d["estado"] == "listo" and d["intentos"] == 1, d             # se cortó y se reanudó
    bajados = open(os.path.join(R, "Descargas", ".bajando", "bajados-%d" % t.id)).read().splitlines()
    assert "T1/Cap 1.mp4" not in bajados[1] and "T1/Cap 2.mp4" not in bajados[1], bajados
    assert existe("Videos", "Mezcla", "T1", "Cap 2.mp4")
    assert existe("Descargas", "Mezcla", "Juego PC", "intro.avi")        # el juego de PC, entero
    assert existe("Descargas", "Mezcla", "Juego PC", "juego.exe")
    assert not existe("Descargas", ".televieja-hechos")
    assert "2 videos" in d["resumen"], d["resumen"]
    assert any("Ya podés usar" in n for n in g.tomar_novedades())


def probar_directo_cortado():
    """Un link directo que se corta a la mitad: tiene que seguir desde donde quedó."""
    import http.server
    import threading
    contenido = bytes(range(256)) * 4000          # ~1 MB
    pedidos = []

    class Servidor(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            rango = self.headers.get("Range")
            pedidos.append(rango)
            inicio = int(rango.split("=")[1].split("-")[0]) if rango else 0
            self.send_response(206 if rango else 200)
            self.send_header("Content-Disposition", 'attachment; filename="Pelicula.mp4"')
            self.send_header("Content-Length", str(len(contenido) - inicio))
            self.end_headers()
            if not rango:   # la primera vez se corta a la mitad
                self.wfile.write(contenido[:len(contenido) // 2])
                self.wfile.flush()
                self.connection.shutdown(2)
                return
            self.wfile.write(contenido[inicio:])

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 18484), Servidor)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    g = descargas.Gestor(R, archivo=os.path.join(TMP, "fila4.json"), internet=lambda: True)
    t = g.agregar("http://127.0.0.1:18484/descargar?id=123")
    d = esperar(g, t.id, limite=60)
    srv.shutdown()
    assert d["estado"] == "listo", d
    assert pedidos[0] is None and pedidos[-1] == "bytes=%d-" % (len(contenido) // 2), pedidos
    with open(os.path.join(R, "Videos", "Pelicula.mp4"), "rb") as f:
        assert f.read() == contenido, "el archivo armado en dos partes no es igual al original"


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
    g = descargas.Gestor(R, archivo=os.path.join(TMP, "fila-red.json"))
    t = g.agregar("https://drive.google.com/drive/folders/1KpLl_1tcK0eeehzN980zbG-3M2nhbVks")
    d = esperar(g, t.id, limite=180)
    print("red:", d["estado"], d["nombre"], d["resumen"], d["mensaje"])
    assert d["estado"] == "listo", d
    assert existe("Descargas", "gdown_folder_test", "this is a file.txt")


def main():
    probar_acomodar()
    g = probar_gestor()
    probar_web(g)
    probar_reintentos_y_fila()
    probar_directo_cortado()
    probar_temprano()
    red = os.environ.get("TELEVIEJA_PRUEBA_RED")
    if red:
        probar_red(red)
    print("OK - descargas")


if __name__ == "__main__":
    main()
