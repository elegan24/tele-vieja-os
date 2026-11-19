"""Prueba sin tele: arma contenido de ejemplo, recorre el menú y guarda capturas.

Uso:  python3 pruebas/prueba_menu.py CARPETA_CAPTURAS
"""
import json
import os
import sys
import tempfile
import time
import zipfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["TELEVIEJA_VENTANA"] = "1"
os.environ["TELEVIEJA_SIN_HORA"] = "1"
TMP = tempfile.mkdtemp(prefix="televieja-prueba-")
os.environ["TELEVIEJA_RAIZ"] = os.path.join(TMP, "TeleVieja")
os.environ["TELEVIEJA_CONFIG"] = os.path.join(TMP, "config")
os.environ["HOME"] = TMP
MONTAJES = os.path.join(TMP, "media")
os.environ["TELEVIEJA_MONTAJES"] = MONTAJES
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from televieja import config, historietas, menu, pantallas  # noqa: E402

SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TMP, "capturas")
os.makedirs(SALIDA, exist_ok=True)


def tocar(ruta, contenido=b""):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(contenido)


def pagina_de_ejemplo(numero, ancho=1000, alto=1500):
    sup = pygame.Surface((ancho, alto))
    sup.fill((250, 245, 230))
    fuente = pygame.font.Font(None, 90)
    colores = [(220, 60, 50), (40, 120, 220), (250, 200, 40), (60, 170, 90)]
    for fila in range(3):
        for col in range(2):
            r = pygame.Rect(40 + col * 470, 40 + fila * 480, 450, 450)
            pygame.draw.rect(sup, colores[(fila + col + numero) % 4], r)
            pygame.draw.rect(sup, (0, 0, 0), r, 8)
            sup.blit(fuente.render("P%d C%d" % (numero, fila * 2 + col + 1), True, (0, 0, 0)),
                     r.move(30, 30))
    return sup


def preparar_contenido():
    R = config.RAIZ
    for nombre in ["Los Simpsons", "El Chavo del 8", "Dragon Ball"]:
        for cap in (1, 2, 10):
            tocar(os.path.join(R, "Videos", nombre, "Capitulo %d.mp4" % cap))
    tocar(os.path.join(R, "Videos", "Volver al futuro.avi"))
    # carpeta que quedó suelta al copiar un disco (fuera de Videos) y otra sin videos
    tocar(os.path.join(R, "Dale Play", "Temporada 1", "Capitulo 1.mkv"))
    for n in ("OPLAT-44-1192.mp4", "OP.LAT-03-720P.mp4", "OPLAT-10-1201.mp4"):
        tocar(os.path.join(R, "Videos", "One Piece", n))
    # fondos de pantalla: uno grande 16:9, un póster vertical y un PNG de 256 colores
    fondos = os.path.join(R, "Videos", "One Piece", "Fondos de Pantalla")
    os.makedirs(fondos, exist_ok=True)
    grande = pygame.Surface((1920, 1080))
    for x in range(0, 1920, 120):
        pygame.draw.rect(grande, (x % 255, 90, 200 - x % 200), (x, 0, 120, 1080))
    pygame.draw.circle(grande, (255, 220, 0), (960, 540), 300)
    pygame.image.save(grande, os.path.join(fondos, "Luffy Gear 5.png"))
    poster = pygame.Surface((600, 900))
    poster.fill((230, 210, 160))
    pygame.draw.rect(poster, (40, 30, 20), (60, 60, 480, 120))
    pygame.image.save(poster, os.path.join(fondos, "Wanted Zoro.jpg"))
    paleta = pygame.Surface((320, 200), depth=8)
    paleta.fill((200, 0, 0))
    pygame.image.save(paleta, os.path.join(fondos, "Bandera.png"))
    tocar(os.path.join(R, "Papeles", "nota.txt"))
    tocar(os.path.join(R, "Canal", "Programas", "El Zorro 01.mp4"))
    tocar(os.path.join(R, "Canal", "Tandas", "Publicidad Coca 1991.mp4"))
    for n in ["Super Mario Bros. (World)", "Contra (U) [!]", "Duck Hunt (World)",
              "Adventure Island (U)", "Battle City (J)", "Bomberman (U)", "Castlevania (U) [!]",
              "Excitebike (JU)", "Ice Climber (U)", "Kung Fu (U)", "Mega Man 2 (U)",
              "Ninja Gaiden (U)", "Pac-Man (U)", "Tetris (U)", "Zelda (U)"]:
        tocar(os.path.join(R, "Juegos", "Family", n + ".nes"))
    tocar(os.path.join(R, "Juegos", "NeoGeo", "mslug.zip"))
    tocar(os.path.join(R, "Juegos", "NeoGeo", "neogeo.zip"))
    # PlayStation: .cue con sus pistas, juego de 3 discos con .m3u, .chd y un .bin suelto
    ps1 = os.path.join(R, "Juegos", "PlayStation")
    tocar(os.path.join(ps1, "Crash Bandicoot (USA).cue"),
          b'FILE "Crash Bandicoot (USA).bin" BINARY\n  TRACK 01 MODE2/2352\n')
    tocar(os.path.join(ps1, "Crash Bandicoot (USA).bin"))
    tocar(os.path.join(ps1, "Tekken 3 (USA).chd"))
    ff7 = os.path.join(ps1, "Final Fantasy VII")
    for d in (1, 2, 3):
        tocar(os.path.join(ff7, "Final Fantasy VII (Disc %d).chd" % d))
    tocar(os.path.join(ff7, "Final Fantasy VII.m3u"),
          "\n".join("Final Fantasy VII (Disc %d).chd" % d for d in (1, 2, 3)).encode())
    tocar(os.path.join(ps1, "Juego Suelto.bin"))
    tocar(os.path.join(R, "Juegos", "Nintendo64", "Super Mario 64 (USA).z64"))
    # Arcade: nombres cortos de FBNeo + archivos de BIOS que no tienen que aparecer
    for n in ("sfa.zip", "mvsc.zip", "pgm.zip", "neogeo.zip", "raro.7z"):
        tocar(os.path.join(R, "Juegos", "Arcade", n))
    # PC: Sonic R con su instalador al lado, un juego con varios .exe y uno con jugar.txt
    pc = os.path.join(R, "Juegos", "PC")
    tocar(os.path.join(pc, "Sonic R", "SONICR.EXE"))
    tocar(os.path.join(pc, "Sonic R", "SETUP.EXE"))
    tocar(os.path.join(pc, "Sonic R", "Uninstal.exe"))
    tocar(os.path.join(pc, "Juego Raro", "uno.exe"))
    tocar(os.path.join(pc, "Juego Raro", "dos.exe"))
    tocar(os.path.join(pc, "Con Archivo", "bin", "game.exe"))
    tocar(os.path.join(pc, "Con Archivo", "otro.exe"))
    tocar(os.path.join(pc, "Con Archivo", "jugar.txt"), b"bin\\game.exe\n")
    tocar(os.path.join(ps1, "Pistas", "Wipeout.cue"), b"FILE Wipeout.bin BINARY\n")
    tocar(os.path.join(ps1, "Pistas", "Wipeout.bin"))
    tocar(os.path.join(R, "Radio", "Kaliman", "Episodio 001.mp3"))
    # disco USB con carpeta TeleVieja y otro sin (se recorre entero)
    disco = os.path.join(MONTAJES, "1234-ABCD", "TeleVieja")
    tocar(os.path.join(disco, "Videos", "Los Tres Chiflados", "Episodio 1.mp4"))
    tocar(os.path.join(disco, "Juegos", "Family", "Super Mario Bros. 3 (U).nes"))
    tocar(os.path.join(disco, "Canal", "Tandas", "Publicidad Topper.mp4"))
    tocar(os.path.join(MONTAJES, "DISCO2", "Pelis", "Esperando la carroza.mkv"))
    # el megapack completo, puesto en el disco fuera de TeleVieja/Historietas
    tocar(os.path.join(MONTAJES, "1234-ABCD", "+MEGAPACK HISTORIETAS RETRO", "Condorito 001.cbz"))
    # historieta CBZ de ejemplo
    os.makedirs(os.path.join(R, "Historietas", "Mafalda"), exist_ok=True)
    cbz = os.path.join(R, "Historietas", "Patoruzito 042.cbz")
    with zipfile.ZipFile(cbz, "w") as z:
        for i in range(1, 4):
            ruta = os.path.join(TMP, "p%d.png" % i)
            pygame.image.save(pagina_de_ejemplo(i), ruta)
            z.write(ruta, "%02d.png" % i)
    carpeta = os.path.join(R, "Historietas", "Mafalda", "Tomo 1")
    os.makedirs(carpeta, exist_ok=True)
    pygame.image.save(pagina_de_ejemplo(7), os.path.join(carpeta, "001.jpg"))
    return cbz


def apretar_tecla(app, tecla):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0, unicode="", scancode=0))
    app.vuelta(0.05)


def celular(app, boton):
    """Aprieta un botón en la página del celular (pedido HTTP de verdad)."""
    import urllib.request
    pedido = urllib.request.Request("http://127.0.0.1:18080/b/" + boton, method="POST")
    with urllib.request.urlopen(pedido, timeout=5) as r:
        assert r.status == 204
    time.sleep(0.05)
    app.vuelta(0.05)


class PadFalso:
    """Joystick virtual de mentira (en la prueba no hay /dev/uinput)."""
    creados = []

    def __init__(self):
        self.eventos = []
        self.cerrado = False
        PadFalso.creados.append(self)

    def boton(self, nombre, apretado):
        self.eventos.append((nombre, apretado))

    def palanca(self, x, y):
        self.eventos.append(("palanca", x, y))

    def cerrar(self):
        self.cerrado = True


def websocket(mensajes, puerto=18080):
    """Cliente WebSocket mínimo: se conecta a /ws, manda mensajes y devuelve lo que contestó."""
    import base64
    import socket
    import struct
    s = socket.create_connection(("127.0.0.1", puerto), timeout=5)
    clave = base64.b64encode(os.urandom(16)).decode()
    s.sendall(("GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % clave).encode())
    respuesta = b""
    while b"\r\n\r\n" not in respuesta:
        respuesta += s.recv(1)
    assert b" 101 " in respuesta, respuesta

    def leer_mensaje():
        b1, b2 = s.recv(1)[0], s.recv(1)[0]
        largo = b2 & 0x7F
        if largo == 126:
            largo = struct.unpack(">H", s.recv(2))[0]
        datos = b""
        while len(datos) < largo:
            datos += s.recv(largo - len(datos))
        return b1 & 0x0F, datos.decode()

    recibidos = [leer_mensaje()[1]]
    if recibidos[0] == "ok":
        for m in mensajes:
            datos = m.encode()
            mascara = os.urandom(4)
            enmascarado = bytes(c ^ mascara[i % 4] for i, c in enumerate(datos))
            s.sendall(bytes([0x81, 0x80 | len(datos)]) + mascara + enmascarado)
        s.sendall(bytes([0x88, 0x80]) + os.urandom(4))  # cerrar
        time.sleep(0.2)
    s.close()
    return recibidos


def probar_joystick_celular():
    from televieja import joystick_virtual, mando, remoto
    pagina = __import__("urllib.request").request.urlopen("http://127.0.0.1:18080/joystick").read().decode()
    assert "SELECT" in pagina and "/ws" in pagina
    # 1) sin /dev/uinput (como acá): el celu recibe un mensaje claro
    remoto.crear_joystick = remoto._crear_joystick
    respuesta = websocket([])
    assert respuesta[0].startswith("error"), respuesta
    print("sin uinput, el celu muestra:", respuesta[0])
    # 2) con un joystick: los botones llegan apretados y soltados, y al cortar se suelta todo
    remoto.crear_joystick = PadFalso
    assert websocket(["1 a", "1 right", "ping", "0 right", "0 a", "1 rm -rf", "1 start",
                      "ax 50 -100", "ax x y", "0 start"]) == ["ok"]
    pad = PadFalso.creados[-1]
    assert pad.eventos == [("a", True), ("right", True), ("right", False), ("a", False),
                           ("start", True), ("palanca", 50, -100), ("start", False)], pad.eventos
    assert pad.cerrado
    # 3) el perfil de RetroArch del celu coincide con el orden de botones del joystick virtual
    texto = mando.perfil_retroarch(joystick_virtual.NOMBRE, joystick_virtual.VENDOR,
                                   joystick_virtual.PRODUCTO, joystick_virtual.MAPA_MENU)
    assert 'input_a_btn = "1"' in texto and 'input_b_btn = "0"' in texto
    assert 'input_up_btn = "h0up"' in texto and 'input_exit_emulator_btn = "9"' in texto
    assert 'input_l2_btn = "6"' in texto and 'input_r2_btn = "7"' in texto
    assert 'input_vendor_id = "%d"' % 0x1209 in texto
    for i, nombre in enumerate(joystick_virtual.BOTONES):
        assert joystick_virtual.MAPA_MENU[nombre] == ["btn", i]
    assert 'input_l_x_plus_axis = "+0"' in texto and 'input_l_x_minus_axis = "-0"' in texto
    assert 'input_l_y_plus_axis = "+1"' in texto and 'input_l_y_minus_axis = "-1"' in texto


def probar_perfiles_retroarch():
    from televieja import mando
    # GUID de SDL: bus, crc, fabricante, 0, modelo, 0, versión, datos (2 bytes c/u)
    guid = "0300" + "0000" + "6d04" + "0000" + "16c2" + "0000" + "1101" + "0000"
    assert mando.vid_pid(guid) == (0x046D, 0xC216), mando.vid_pid(guid)
    mando.guardar_calibracion(guid, "Logitech Dual Action",
                              {"up": ["hat", 0, "up"], "a": ["btn", 2], "b": ["btn", 1],
                               "left": ["axis", 0, -1], "select": ["btn", 8], "start": ["btn", 9],
                               # palanca derecha "al revés": al mover a la derecha el eje 3 baja
                               "cstick_x": ["axis", 3, -1]})
    carpeta = os.path.join(config.AUTOCONFIG_DIR, "udev")
    archivos = sorted(os.listdir(carpeta))
    assert "televieja-celular.cfg" in archivos and len(archivos) == 2, archivos
    perfil = open(os.path.join(carpeta, [a for a in archivos if "celular" not in a][0])).read()
    assert 'input_vendor_id = "1133"' in perfil and 'input_left_axis = "-0"' in perfil, perfil
    assert 'input_enable_hotkey_btn = "8"' in perfil
    assert 'input_r_x_plus_axis = "-3"' in perfil and 'input_r_x_minus_axis = "+3"' in perfil, perfil
    base = open(config.ARCHIVO_RA_JOYSTICK).read()
    assert 'input_autodetect_enable = "true"' in base and config.AUTOCONFIG_DIR in base
    assert "input_player1" not in base  # nada global: cada joystick usa su perfil


def probar_controles(app, paso, foto):
    import urllib.request
    from televieja import remoto
    assert app.servidor_celular, "no arrancó el servidor del celular"
    pagina = urllib.request.urlopen("http://127.0.0.1:18080/", timeout=5).read().decode()
    assert "Frecuencia 99" in pagina and 'data-b="inicio"' in pagina
    assert 'src="/logo.png"' in pagina
    logo = urllib.request.urlopen("http://127.0.0.1:18080/logo.png", timeout=5).read()
    assert logo[:8] == b"\x89PNG\r\n\x1a\n" and len(logo) > 1000
    # botón inválido -> 404
    try:
        urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:18080/b/rm", method="POST"))
        raise AssertionError("tenía que dar 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404
    principal = app.pila[0]
    principal.sel = 0
    celular(app, "down")
    celular(app, "down")
    assert principal.sel == 2, principal.sel           # Juegos
    celular(app, "a")
    assert app.actual.titulo == "Juegos", app.actual.titulo
    app.actual.sel = [it.texto for it in app.actual.items].index("Family / NES")
    celular(app, "a")                                   # Family
    assert app.actual.titulo.startswith("Family")
    celular(app, "inicio")                              # vuelve al menú de una
    assert app.actual is principal and len(app.pila) == 1
    # control remoto USB: tecla "Atrás" y "Inicio"
    assert principal.sel == 2                           # se quedó en Juegos
    principal.sel = 0
    celular(app, "up")
    celular(app, "up")                                  # va a "Opciones" (vuelve por abajo)
    assert principal.items[principal.sel].texto == "Opciones", principal.items[principal.sel].texto
    celular(app, "a")
    apretar_tecla(app, pygame.K_AC_BACK)
    assert app.actual is principal
    # volumen desde el celu (sin amixer en la prueba: igual muestra el aviso)
    celular(app, "vol+")
    assert app.aviso.startswith("Volumen") or app.aviso == "Sin sonido", app.aviso
    # pantalla con el código QR
    app.poner(pantallas.ControlCelular())
    pantalla = app.actual
    if pantalla.ip is None:
        pantalla.ip = "192.168.0.23"  # la prueba corre sin red de casa
    app.aviso = ""
    foto("15-control-celular")
    assert pantalla.url and pantalla.url.endswith(":18080"), pantalla.url
    assert pantalla.qr, "falta el QR (pip install qrcode)"
    paso("b")
    assert remoto.EVENTO > pygame.USEREVENT
    probar_joystick_celular()
    probar_perfiles_retroarch()


def probar_glxinfo():
    gma3150 = """OpenGL vendor string: Intel Open Source Technology Center
OpenGL renderer string: Mesa DRI Intel(R) IGD
    Accelerated: yes
Max core profile version: 0.0
Max compat profile version: 2.1
"""
    software = """OpenGL renderer string: llvmpipe (LLVM 15.0.6, 128 bits)
    Accelerated: no
Max core profile version: 4.5
"""
    juana_manso = """OpenGL renderer string: Mesa Intel(R) UHD Graphics 600 (GLK 2)
    Accelerated: yes
Max core profile version: 4.6
"""
    assert config.analizar_glxinfo(gma3150) == (False, "La placa de video no alcanza: tiene OpenGL 0.0 y hace falta 3.3")
    assert config.analizar_glxinfo(software)[0] is False
    assert config.analizar_glxinfo(juana_manso)[0] is True
    assert config.analizar_glxinfo("")[0] is False


def probar_episodios():
    casos = {"[Fansub B] One Piece 10 [720p].mp4": 10,
             "[Fansub A] One Piece - 002 [1080p][ABC12345].mkv": 2,
             "One Piece Episodio 1.mp4": 1, "One.Piece.003.HD.1080p.x264.mp4": 3,
             "One Piece 045 - El hombre de 2 caras.mp4": 45, "One Piece Cap 1000.mkv": 1000,
             "Los Simpsons S02E05.mkv": 20005, "One_Piece_Ep_12_720p.mp4": 12,
             "One Piece (1999) 004.mp4": 4, "Pelicula.mp4": None}
    for nombre, esperado in casos.items():
        assert config.numero_episodio(nombre) == esperado, (nombre, config.numero_episodio(nombre))
    orden = config.ordenar_episodios(["[B] One Piece 10.mp4", "One Piece Episodio 1.mp4",
                                      "[A] One Piece 2 [720p].mkv", "One Piece 100.mp4"])
    assert orden == ["One Piece Episodio 1.mp4", "[A] One Piece 2 [720p].mkv",
                     "[B] One Piece 10.mp4", "One Piece 100.mp4"], orden
    # el pack de One Piece mezcla "OP.LAT-03-720P" con "OPLAT-44-1192"
    orden = config.ordenar_episodios(["OPLAT-44-1192.mp4", "OP.LAT-03-720P.mp4",
                                      "OPLAT-4-1201.mp4", "OP.LAT-100-720P.mp4"])
    assert orden == ["OP.LAT-03-720P.mp4", "OPLAT-4-1201.mp4", "OPLAT-44-1192.mp4",
                     "OP.LAT-100-720P.mp4"], orden
    assert config.etiqueta_episodio("OPLAT-44-1192.mp4") == "Episodio 44"
    assert config.etiqueta_episodio("Volver al futuro.avi") is None
    assert config.etiqueta_episodio("Los Simpsons S02E05.mkv") is None
    # nombres "sucios" de descargas (como los del prototipo del motor de continuidad)
    sucio = "Copia de Steven.Spielberg.Presents.Animaniacs.S01E05.Taming.Of.The.Screwy.1080p.HMAX.WEB-DL.DD2.0.mp4"
    assert config.nombre_lindo(sucio) == "Steven Spielberg Presents Animaniacs S01E05 Taming Of The Screwy"
    assert config.titulo_episodio(sucio) == "T1 E5 · Taming Of The Screwy"
    assert config.titulo_episodio("Get Smart S01E01 (Mr. Big).ia.mp4") == "T1 E1 · Mr. Big"
    assert config.titulo_episodio("Los Simpsons 3x07 - Lisa la vegetariana.mkv") == "T3 E7 · Lisa la vegetariana"
    assert config.nombre_lindo("Dr. No (1962).mkv") == "Dr. No (1962)"
    assert config.nombre_lindo("Copia de Copia de El Chavo 001.mp4") == "El Chavo 001"
    # películas sin número: por nombre
    assert config.ordenar_episodios(["Volver al futuro.avi", "Titanic.mp4", "Rocky 2.mp4"]) == \
        ["Rocky 2.mp4", "Titanic.mp4", "Volver al futuro.avi"]


def probar_canal():
    """Canal Retro con grilla: series, orden de capítulos, bloques por día y hora."""
    import datetime
    from televieja import grilla, reproducir
    raiz = os.path.join(TMP, "canal-raiz")
    # un pack con varias series adentro, una serie con arcos y un video suelto
    tocar(os.path.join(raiz, "Videos", "SERI3S ANIMAD4S RETRO", "Los Picapiedras", "Cap 2.mp4"))
    tocar(os.path.join(raiz, "Videos", "SERI3S ANIMAD4S RETRO", "Los Picapiedras", "Cap 1.mp4"))
    tocar(os.path.join(raiz, "Videos", "SERI3S ANIMAD4S RETRO", "Scooby-Doo", "Episodio 1.mp4"))
    tocar(os.path.join(raiz, "Videos", "+One Piece", "1. Sagas", "2. Arco B", "OPLAT-10-1.mp4"))
    tocar(os.path.join(raiz, "Videos", "+One Piece", "1. Sagas", "1. Arco A", "OPLAT-2-1.mp4"))
    tocar(os.path.join(raiz, "Videos", "+One Piece", "1. Sagas", "1. Arco A", "OP.LAT-1-720P.mp4"))
    tocar(os.path.join(raiz, "Canal", "Tandas", "Coca 1991.mp4"))
    viejo = config.raices
    config.raices = lambda: [raiz]
    try:
        series = grilla.carpetas_de_series()
        assert sorted(series) == ["Los Picapiedras", "One Piece", "Scooby-Doo"], sorted(series)
        eps = [t for _, t in grilla.episodios(series["One Piece"])]
        assert eps == ["Episodio 1", "Episodio 2", "Episodio 10"], eps
        # bloques: el domingo a las 15 manda la maratón; el lunes a las 15, la tarde
        g = {"bloques": [
            {"nombre": "Tarde", "dias": "todos", "hora": "13:00", "tipo": "mezcla", "series": []},
            {"nombre": "Noche", "dias": "todos", "hora": "20:00", "tipo": "mezcla", "series": []},
            {"nombre": "Maratón", "dias": "dom", "hora": "13:00", "tipo": "maraton",
             "series": ["Scooby-Doo"]}]}
        domingo = datetime.datetime(2026, 11, 15, 15, 0)
        assert grilla.bloque_en(g, domingo) == 2
        assert grilla.bloque_en(g, domingo + datetime.timedelta(days=1)) == 0
        assert grilla.bloque_en(g, datetime.datetime(2026, 11, 16, 3, 0)) == 1  # sigue la noche
        assert [h for h, _ in grilla.guia_del_dia(g, 6)] == ["13:00", "20:00"]
        listos = grilla.resolver(g, {s: [] for s in series})
        assert listos[2]["series"] == ["Scooby-Doo"] and len(listos[0]["series"]) == 3, listos
        # maratón sin serie elegida: una serie entera (cambia cada semana)
        g["bloques"][2]["series"] = []
        assert len(grilla.resolver(g, {s: [] for s in series})[2]["series"]) == 1
        # el catálogo para canal.lua
        opciones = dict(config.OPCIONES_POR_DEFECTO, TANDAS_POR_CORTE="1")
        ruta = reproducir.armar_canal(opciones)
        cat = json.load(open(ruta, encoding="utf-8"))
        assert cat["series"]["One Piece"][0]["titulo"] == "Episodio 1", cat["series"]["One Piece"]
        assert len(cat["tandas"]) == 1 and cat["por_corte"] == 1 and cat["semana"]
        orden = reproducir.orden_canal(opciones, ruta)
        assert "--idle=yes" in orden and any("canal-catalogo=" + ruta in o for o in orden), orden
    finally:
        config.raices = viejo


def probar_grilla_menu(app, paso, foto):
    """Opciones > Grilla del canal: ver bloques, cambiar hora/tipo y elegir la serie."""
    from televieja import grilla
    while len(app.pila) > 1:
        app.sacar()
    viejo = grilla.carpetas_de_series
    grilla.carpetas_de_series = lambda: {"One Piece": [], "Scooby-Doo": [], "Los Picapiedras": []}
    try:
        if os.path.exists(grilla.ARCHIVO):
            os.remove(grilla.ARCHIVO)
        app.poner(pantallas.GrillaCanal())
        textos = [it.texto for it in app.actual.items]
        assert "Domingos 10:00  Maratón del domingo" in textos, textos
        assert sum(it.extra == "AL AIRE" for it in app.actual.items) == 1
        foto("28-grilla")
        app.actual.sel = textos.index("Domingos 10:00  Maratón del domingo")
        paso("a")
        editor = app.actual
        assert isinstance(editor, pantallas.EditarBloque)
        editor.sel = 2                       # Empieza: 10:00
        paso("right", "right")
        assert editor.bloque["hora"] == "11:00", editor.bloque
        editor.sel = 4                       # Serie: ...
        paso("a")
        fin = time.time() + 5
        while time.time() < fin and not isinstance(app.actual, pantallas.ElegirSeries):
            app.vuelta(0.05)
            time.sleep(0.02)
        assert isinstance(app.actual, pantallas.ElegirSeries)
        app.actual.sel = [it.texto for it in app.actual.items].index("One Piece")
        paso("a")                            # maratón: elige una y vuelve
        assert app.actual is editor and editor.bloque["series"] == ["One Piece"]
        foto("29-grilla-bloque")
        guardada = grilla.cargar()
        bloque = [b for b in guardada["bloques"] if b["nombre"] == "Maratón del domingo"][0]
        assert bloque["hora"] == "11:00" and bloque["series"] == ["One Piece"], bloque
        paso("b")
        assert isinstance(app.actual, pantallas.GrillaCanal)
        assert any(it.texto == "Domingos 11:00  Maratón del domingo" for it in app.actual.items)
    finally:
        grilla.carpetas_de_series = viejo
        while len(app.pila) > 1:
            app.sacar()


def probar_marcos():
    """Marcos (bezels): franja horaria, PNG que va, marco.json, hueco y píxeles para mpv."""
    import datetime
    from televieja import marcos, reproducir
    hora = lambda h, m=0: datetime.datetime(2026, 11, 16, h, m)  # noqa: E731
    franjas = [marcos.franja(hora(h, m)) for h, m in ((3, 0), (6, 0), (12, 59), (13, 0), (19, 59),
                                                       (20, 0), (0, 30), (1, 0))]
    assert franjas == ["madrugada", "manana", "manana", "tarde", "tarde", "noche", "noche",
                       "madrugada"], franjas
    nombres = [m["nombre"] for m in marcos.listar()]
    assert "Super_Frecuencia" in nombres and "TV_Clasica" in nombres, nombres
    sgb = marcos.buscar("Super_Frecuencia")
    assert marcos.elegir_png(sgb, hora(14)).endswith("tarde.png")
    assert marcos.elegir_png(sgb, hora(3)).endswith("madrugada.png")
    # uno propio en TeleVieja/Marcos: solo manana.png (sin default) y otro con default.png
    propios = os.path.join(config.RAIZ, "Marcos")
    pygame.init()
    for nombre, archivo, hueco, cfg in (
            ("Solo_Manana", "manana.png", (20, 0, 120, 90), None),
            ("Con_Json", "default.png", (0, 0, 160, 90), {"modo": "ventana", "anchoPorcentaje": "50%",
                                                           "altoPorcentaje": 50, "pixelArt": True})):
        carpeta = os.path.join(propios, nombre)
        os.makedirs(carpeta, exist_ok=True)
        sup = pygame.Surface((160, 90), pygame.SRCALPHA)
        sup.fill((200, 50, 50, 255))
        sup.fill((0, 0, 0, 0), hueco)
        pygame.image.save(sup, os.path.join(carpeta, archivo))
        if cfg:
            json.dump(cfg, open(os.path.join(carpeta, "marco.json"), "w"))
    listados = {m["nombre"]: m for m in marcos.listar()}
    assert listados["Solo_Manana"]["modo"] == "horario" and listados["Solo_Manana"]["propio"]
    assert listados["Con_Json"]["modo"] == "fijo"
    solo = marcos.buscar("Solo_Manana")
    assert marcos.elegir_png(solo, hora(22)).endswith("manana.png")  # no hay noche ni default
    cache = os.path.join(TMP, "cache-marcos")
    d = marcos.preparar(solo, 160, 90, cache)          # video 4:3 en pantalla ancha: franjas a los costados
    assert d["modo"] == "relleno" and [round(v, 3) for v in d["ventana"]] == [0.125, 0.0, 0.125, 0.0], d
    crudo = open(d["archivo"], "rb").read()
    assert len(crudo) == 160 * 90 * 4
    assert crudo[(45 * 160 + 80) * 4:(45 * 160 + 80) * 4 + 4] == b"\0\0\0\0"   # centro transparente
    assert crudo[0:4] == bytes((50, 50, 200, 255))                               # BGRA, opaco
    d = marcos.preparar(marcos.buscar("Con_Json"), 160, 90, cache)
    assert d["modo"] == "ventana" and [round(v, 3) for v in d["ventana"]] == [0.25] * 4, d  # marco.json
    # en la tele (4:3) con un video 16:9: el marco llena las franjas de arriba y abajo
    d = marcos.preparar(sgb, 640, 480, cache, hora(21), aspecto=16 / 9)
    assert d["png"].endswith("noche.png") and [round(v, 3) for v in d["ventana"]] == [0, 0.125, 0, 0.125], d
    crudo = open(d["archivo"], "rb").read()
    assert crudo[(10 * 640 + 320) * 4 + 3] == 255                                 # franja de arriba: marco
    assert crudo[(240 * 640 + 320) * 4:(240 * 640 + 320) * 4 + 4] == b"\0\0\0\0"  # el video, entero
    # video 4:3 en la tele 4:3: no hay franjas (marco.lua no lo muestra)
    d = marcos.preparar(sgb, 640, 480, cache, hora(21), aspecto=4 / 3)
    assert [round(v, 3) for v in d["ventana"]] == [0, 0, 0, 0], d
    # mpv: con marco elegido se carga marco.lua; sin marco, nada
    config.guardar_opcion("MARCO", "Super_Frecuencia")
    extra = reproducir.opciones_marco()
    assert any(o.endswith("marco.lua") for o in extra) and \
        any(o == "--script-opts-append=marco-carpeta=" + sgb for o in extra), extra
    config.guardar_opcion("MARCO", "ninguno")
    assert reproducir.opciones_marco() == []
    orden = reproducir.orden_canal(dict(config.OPCIONES_POR_DEFECTO, NOMBRE_CANAL="TELE, VIEJA"), "c.json")
    assert "--script-opts-append=canal-nombre=TELE, VIEJA" in orden, orden


def probar_wine():
    from televieja import wine
    pc = os.path.join(config.RAIZ, "Juegos", "PC")
    exe, _ = wine.exe_de_juego(os.path.join(pc, "Sonic R"))
    assert exe and exe.endswith("SONICR.EXE"), exe            # ignora SETUP y Uninstal
    exe, candidatos = wine.exe_de_juego(os.path.join(pc, "Juego Raro"))
    assert exe is None and len(candidatos) == 2                # hay que elegir con jugar.txt
    exe, _ = wine.exe_de_juego(os.path.join(pc, "Con Archivo"))
    assert exe and exe.endswith(os.path.join("bin", "game.exe")), exe
    assert wine.orden("/x/a.exe", 640, 480) == ["wine", "explorer", "/desktop=TeleVieja,640x480", "/x/a.exe"]
    env = wine.entorno()
    assert env["WINEARCH"] == "win32" and env["WINEPREFIX"] == wine.PREFIJO


def probar_mega(app, paso, foto):
    """Mega actualización: temas, protector, encendido/apagado, favoritos e ícono del celu."""
    import urllib.request
    from televieja import efectos, favoritos, temas, ui
    while len(app.pila) > 1:
        app.sacar()
    principal = app.pila[0]
    # --- temas: vista previa al moverse, B vuelve, A guarda ---
    assert temas.elegir("auto", __import__("datetime").date(2026, 12, 24)) == "navidad"
    assert temas.elegir("auto", __import__("datetime").date(2026, 10, 31)) == "halloween"
    assert temas.elegir("auto", __import__("datetime").date(2026, 7, 9)) == "clasico"
    assert temas.elegir("gameboy") == "gameboy"
    antes = app.tema
    app.poner(pantallas.ElegirTema())
    elegir = app.actual
    elegir.sel = 0
    paso("down", "down")                      # Automático -> Clásico -> Fichín
    assert app.tema == "fichin" and ui.TEMA == "fichin"
    foto("16-tema-fichin")
    paso("b")
    assert app.tema == antes, "B tenía que volver al tema de antes"
    app.poner(pantallas.ElegirTema())
    app.actual.sel = temas.ORDEN.index("gameboy") + 1
    paso("a")
    assert app.tema == "gameboy" and config.leer_opciones()["TEMA"] == "gameboy"
    assert "PUERTO_CELULAR=18080" in open(config.ARCHIVO_OPCIONES).read()  # no borra lo demás
    foto("17-tema-gameboy")
    # --- encendido y apagado: cuadros de la animación ---
    app._dibujar(app.actual, app.lienzo)
    imagen = app.lienzo.copy()
    hoja = pygame.Surface((4 * 330, 2 * 250))
    hoja.fill((40, 40, 40))
    for i, t in enumerate((0.08, 0.3, 0.55, 0.85)):
        hoja.blit(pygame.transform.scale(efectos.cuadro_encendido(imagen, t), (320, 240)), (i * 330 + 5, 5))
        hoja.blit(pygame.transform.scale(efectos.cuadro_apagado(imagen, (0.2, 0.5, 0.75, 0.9)[i]),
                                         (320, 240)), (i * 330 + 5, 255))
    pygame.image.save(hoja, os.path.join(SALIDA, "18-encendido-apagado.png"))
    # --- protector: aparece solo si no se toca nada, y un botón lo saca ---
    app.opciones["PROTECTOR_MINUTOS"] = "1"
    app.ultima_actividad = time.monotonic() - 30
    app.vuelta(0.05)
    assert not isinstance(app.actual, pantallas.Protector)
    app.ultima_actividad = time.monotonic() - 61
    app.vuelta(0.05)
    assert isinstance(app.actual, pantallas.Protector), app.actual
    foto("19-protector-carta")
    app.actual.inicio -= 50                     # pasar a la parte del logo
    for _ in range(40):
        app.actual.actualizar(app, 0.1)
    foto("20-protector-logo")
    app.actual.accion(app, "a")
    assert not isinstance(app.actual, pantallas.Protector)
    app.opciones["PROTECTOR_MINUTOS"] = "0"
    app.aplicar_tema("clasico")
    # --- favoritos y últimos jugados ---
    principal.sel = [it.texto for it in principal.items].index("Juegos")
    paso("a")
    sistemas = app.actual
    sistemas.sel = [it.texto for it in sistemas.items].index("Family / NES")
    paso("a")
    juegos = app.actual
    juegos.sel = [it.texto for it in juegos.items].index("Contra")
    paso("x")
    assert juegos.items[juegos.sel].extra == "★"
    assert favoritos.es_favorito(juegos.items[juegos.sel].dato)
    paso("a")                                   # jugar: queda en "Últimos jugados"
    paso("b")
    textos = [it.texto for it in app.actual.items]
    assert textos[:2] == ["Favoritos", "Últimos jugados"], textos
    foto("21-juegos-favoritos")
    app.actual.sel = 0
    paso("a")
    assert [it.texto for it in app.actual.items] == ["Contra"], [it.texto for it in app.actual.items]
    assert app.actual.items[0].extra == "Family"
    paso("x")                                   # sacarlo de favoritos desde la lista
    assert app.actual.items[0].texto == "(vacío)"
    paso("b", "b")
    # --- el control del celu como app ---
    manifiesto = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/manifest.json").read())
    assert manifiesto["name"] == "Frecuencia 99" and manifiesto["display"] == "standalone"
    icono = urllib.request.urlopen("http://127.0.0.1:18080/icono-512.png").read()
    assert icono[:8] == b"\x89PNG\r\n\x1a\n", icono[:8]
    with open(os.path.join(SALIDA, "22-icono-celu.png"), "wb") as f:
        f.write(icono)
    pagina = urllib.request.urlopen("http://127.0.0.1:18080/").read().decode()
    assert 'rel="manifest"' in pagina


def probar_bluetooth(app, paso, foto):
    """Opciones > Auriculares Bluetooth con equipos de mentira, y el sonido por el auricular."""
    from televieja import reproducir
    estado = {"adaptador": True, "conectado": False}

    def bt_falso(app_, *args):
        if args[0] == "buscar":
            return {"adaptador": estado["adaptador"], "dispositivos": [
                {"mac": "AA:BB:CC:DD:EE:01", "nombre": "Auricular i12", "audio": True,
                 "emparejado": estado["conectado"], "conectado": estado["conectado"]},
                {"mac": "AA:BB:CC:DD:EE:02", "nombre": "Celular", "audio": False,
                 "emparejado": False, "conectado": False}]}
        if args[0] == "conectar":
            estado["conectado"] = True
            return {"ok": True}
        estado["conectado"] = False
        return {"ok": True}

    pantallas._bt = bt_falso
    while len(app.pila) > 1:
        app.sacar()

    def esperar_pantalla(clase):
        fin = time.time() + 5
        while time.time() < fin and not isinstance(app.actual, clase):
            app.vuelta(0.05)
            time.sleep(0.02)
        assert isinstance(app.actual, clase), app.actual

    pantallas.abrir_bluetooth(app)
    esperar_pantalla(pantallas.Auriculares)
    textos = [it.texto for it in app.actual.items]
    assert textos == ["Buscar de nuevo", "Auricular i12", "Celular"], textos
    foto("26-bluetooth")
    app.actual.sel = 1
    paso("a")
    esperar_pantalla(pantallas.Mensaje)
    assert app.actual.titulo_caja == "¡Conectado!", (app.actual.titulo_caja, app.actual.texto)
    foto("27-bluetooth-conectado")
    while len(app.pila) > 1:
        app.sacar()
    # conectado: muestra "conectado" y ofrece desconectar
    pantallas.abrir_bluetooth(app)
    esperar_pantalla(pantallas.Auriculares)
    assert app.actual.items[1].extra == "conectado"
    app.actual.sel = 1
    paso("a")
    assert isinstance(app.actual, pantallas.Confirmar)
    while len(app.pila) > 1:
        app.sacar()
    # sin adaptador: explica qué hacer
    estado["adaptador"] = False
    pantallas.abrir_bluetooth(app)
    esperar_pantalla(pantallas.Mensaje)
    assert "adaptador Bluetooth USB" in app.actual.texto, app.actual.texto
    while len(app.pila) > 1:
        app.sacar()
    # el sonido va al auricular si bluealsa tiene uno conectado
    falso = os.path.join(TMP, "bin-bt")
    os.makedirs(falso, exist_ok=True)
    with open(os.path.join(falso, "bluealsa-aplay"), "w") as f:
        f.write("#!/bin/sh\necho 'bluealsa:DEV=AA:BB:CC:DD:EE:01,PROFILE=a2dp,SRV=org.bluealsa'\n"
                "echo '    Auricular i12, trusted audio-headset, audio playback'\n")
    os.chmod(os.path.join(falso, "bluealsa-aplay"), 0o755)
    viejo = os.environ["PATH"]
    os.environ["PATH"] = falso + os.pathsep + viejo
    try:
        orden = reproducir.mpv_base()
        assert "--audio-device=alsa/bluealsa:DEV=AA:BB:CC:DD:EE:01,PROFILE=a2dp" in orden, orden
        juego = reproducir.orden_juego("/x/core.so", "/x/rom.nes")
        extra = juego[juego.index("--appendconfig") + 1].split("|")
        auricular = open(extra[-1]).read()
        assert 'audio_device = "bluealsa:DEV=AA:BB:CC:DD:EE:01,PROFILE=a2dp"' in auricular, auricular
    finally:
        os.environ["PATH"] = viejo
    assert not any(a.startswith("--audio-device") for a in reproducir.mpv_base())


def probar_archivo(app, paso, foto):
    """Internet Archive con respuestas de mentira (la prueba no usa internet)."""
    from televieja import archivo
    # la elección de versiones con archivos como los de archive.org
    elegidos = archivo.elegir_videos([
        {"name": "Show S01E02.mp4", "format": "MPEG4", "source": "original", "size": "900"},
        {"name": "Show S01E02.ia.mp4", "format": "h.264 IA", "source": "derivative",
         "original": "Show S01E02.mp4", "size": "500"},
        {"name": "Show S01E01.mpg", "format": "MPEG2", "source": "original", "size": "3000"},
        {"name": "Show S01E01_512kb.mp4", "format": "512Kb MPEG4", "source": "derivative",
         "original": "Show S01E01.mpg", "size": "300"},
        {"name": "Show S01E01.ogv", "format": "Ogg Video", "source": "derivative",
         "original": "Show S01E01.mpg", "size": "280"},
        {"name": "Show.thumbs/1.jpg", "format": "Thumbnail", "source": "derivative"}])
    assert [v["nombre"] for v in elegidos] == ["Show S01E01_512kb.mp4", "Show S01E02.ia.mp4"], elegidos
    assert elegidos[0]["titulo"] == "Show S01E01", elegidos
    assert archivo.consulta_de_texto('Popeye "el" (marino) AND') == \
        "title:(Popeye el marino) OR subject:(Popeye el marino) OR description:(Popeye el marino)"

    viejos = archivo.buscar, archivo.videos
    archivo.buscar = lambda consulta, pagina=1: (2, [
        {"id": "betty", "titulo": "Betty Boop Cartoons", "anio": "1936"},
        {"id": "smart", "titulo": "Get Smart", "anio": ""}])
    archivo.videos = lambda ident: ("Get Smart", [
        {"titulo": "Get Smart S01E01 (Mr. Big)", "url": "https://archive.org/download/smart/1.mp4"},
        {"titulo": "Get Smart S01E02", "url": "https://archive.org/download/smart/2.mp4"}])
    lanzados = []
    viejo_lanzar = app.lanzar
    app.lanzar = lambda orden, *a, **k: (lanzados.append(orden), (0, 10.0, ""))[1]
    try:
        while len(app.pila) > 1:
            app.sacar()
        principal = app.pila[0]
        principal.sel = [it.texto for it in principal.items].index("Internet")
        paso("a")
        assert [it.texto for it in app.actual.items] == ["Favoritos", "Internet Archive", "YouTube",
                                                         "Streaming"]
        foto("33-internet")
        app.actual.sel = 1
        paso("a")
        assert isinstance(app.actual, pantallas.ArchivoInicio)
        foto("30-archivo")
        app.actual.sel = [it.texto for it in app.actual.items].index("Series de TV clásicas")
        paso("a")

        def esperar(clase):
            fin = time.time() + 5
            while time.time() < fin and not isinstance(app.actual, clase):
                app.vuelta(0.05)
                time.sleep(0.02)
            assert isinstance(app.actual, clase), app.actual
        esperar(pantallas.ArchivoResultados)
        assert [it.texto for it in app.actual.items] == ["Betty Boop Cartoons", "Get Smart"]
        app.actual.sel = 1
        paso("x")                            # Get Smart a Favoritos
        assert app.actual.items[1].extra == "★", app.actual.items[1].extra
        foto("31-archivo-resultados")
        app.actual.sel = 1
        paso("a")
        esperar(pantallas.ArchivoVideos)
        app.actual.sel = 1
        paso("a")                            # ve desde el capítulo 2
        orden = lanzados[-1]
        assert orden[0] == "mpv" and any(o.startswith("--playlist=") for o in orden), orden
        m3u = open([o for o in orden if o.startswith("--playlist=")][0].split("=", 1)[1]).read()
        assert "smart/2.mp4" in m3u and "smart/1.mp4" not in m3u and "#EXTINF:-1,Get Smart S01E02" in m3u
    finally:
        archivo.buscar, archivo.videos = viejos
        app.lanzar = viejo_lanzar
        while len(app.pila) > 1:
            app.sacar()


def probar_youtube(app, paso, foto):
    """YouTube con respuestas de mentira (la prueba no usa internet) y Kodi sin Kodi."""
    import shutil
    from televieja import reproducir, youtube
    datos = {"entries": [
        {"id": "aaa", "title": "TELEFE 1991 - Tandas", "duration": 3281, "channel": "Canal"},
        {"id": "bbb", "title": "Un short", "duration": 40},
        {"id": "ccc", "title": "En vivo", "duration": None, "live_status": "is_live"},
        {"id": "ddd", "title": "Dibujos clásicos", "duration": 600}]}
    videos = youtube.interpretar(datos)
    assert [v["id"] for v in videos] == ["aaa", "ddd"], videos
    assert videos[0]["duracion"] == "54:41" and videos[1]["duracion"] == "10:00"
    assert videos[0]["url"] == "https://www.youtube.com/watch?v=aaa"
    orden = reproducir.orden_youtube(youtube.lista_m3u(videos))
    assert "--ytdl=yes" in orden and any(o.startswith("--ytdl-format=") and "360" in o for o in orden)
    assert any("ytdl_hook-ytdl_path=" in o for o in orden) and \
        any(o == "--ytdl-raw-options-append=cookies=" + youtube.ARCHIVO_COOKIES for o in orden), orden
    assert "PREF\tf2=8000000" in open(youtube.ARCHIVO_COOKIES).read()

    viejo_buscar, viejo_lanzar = youtube.buscar, app.lanzar
    youtube.buscar = lambda texto, cantidad=30: videos
    lanzados = []
    app.lanzar = lambda orden, *a, **k: (lanzados.append((orden, a, k)), (0, 10.0, ""))[1]
    try:
        while len(app.pila) > 1:
            app.sacar()
        app.poner(pantallas.YoutubeInicio())
        assert app.actual.items[0].texto == "Buscar..."
        app.actual.sel = [it.texto for it in app.actual.items].index(youtube.SUGERENCIAS[1])
        paso("a")
        fin = time.time() + 5
        while time.time() < fin and not isinstance(app.actual, pantallas.YoutubeResultados):
            app.vuelta(0.05)
            time.sleep(0.02)
        assert isinstance(app.actual, pantallas.YoutubeResultados)
        assert [it.extra for it in app.actual.items] == ["54:41", "10:00"]
        app.actual.sel = 0
        paso("x")                            # a Favoritos
        assert app.actual.items[0].extra == "★ 54:41", app.actual.items[0].extra
        app.actual.sel = 1
        paso("letra:F")                      # con la tecla F del teclado, también
        assert app.actual.items[1].extra == "★ 10:00", app.actual.items[1].extra
        paso("letra:F")                      # y otra vez lo saca
        assert app.actual.items[1].extra == "10:00"
        foto("34-youtube")
        app.actual.sel = 1
        paso("a")
        m3u = open([o for o in lanzados[-1][0] if o.startswith("--playlist=")][0][11:]).read()
        assert "watch?v=ddd" in m3u and "watch?v=aaa" not in m3u
        app.sacar()
        assert app.actual.items[1].texto == youtube.SUGERENCIAS[1] and app.actual.items[1].extra == "reciente"
        # Internet > Favoritos: lo marcado con X en YouTube y en Internet Archive
        app.poner(pantallas.InternetFavoritos())
        favs = app.actual
        assert [(it.texto, it.extra) for it in favs.items] == [
            ("TELEFE 1991 - Tandas", "YouTube"), ("Get Smart", "Archive")], [(it.texto, it.extra) for it in favs.items]
        foto("37-favoritos-internet")
        favs.sel = 0
        paso("a")
        m3u = open([o for o in lanzados[-1][0] if o.startswith("--playlist=")][0][11:]).read()
        assert "watch?v=aaa" in m3u
        paso("x")                            # sacar
        assert [it.texto for it in favs.items] == ["Get Smart"]
        favs.sel = 0
        paso("x")
        assert favs.items[0].apagado
        # Kodi: si no está, avisa; si está, la primera vez explica y después abre
        while len(app.pila) > 1:
            app.sacar()
        viejo_which = shutil.which
        shutil.which = lambda nombre: None
        app.kodi()
        assert isinstance(app.actual, pantallas.Mensaje) and app.actual.titulo_caja == "Falta Kodi"
        app.sacar()
        shutil.which = lambda nombre: "/usr/bin/" + nombre
        app.kodi()
        assert isinstance(app.actual, pantallas.Mensaje) and "Netflix" in app.actual.texto
        foto("35-streaming")
        paso("a")                                  # cierra la guía y abre Kodi
        assert lanzados[-1][0] == ["kodi", "-fs"] and lanzados[-1][2].get("combo_salida")
        app.kodi()                                 # la segunda vez, directo
        assert len(app.pila) == 1 and lanzados[-1][0] == ["kodi", "-fs"]
        # si Kodi se cae enseguida (placa sin 3D), reintenta en modo compatible y lo recuerda
        respuestas = [(-11, 3.0, ""), (0, 120.0, "")]
        app.lanzar = lambda orden, *a, **k: (lanzados.append((orden, a, k)), respuestas.pop(0))[1]
        app.kodi()
        assert (lanzados[-2][2].get("env") or {}).get("LIBGL_ALWAYS_SOFTWARE") is None
        assert lanzados[-1][2]["env"]["LIBGL_ALWAYS_SOFTWARE"] == "1"
        assert config.leer_opciones().get("KODI_COMPATIBLE") == "si"
        # ya en modo compatible, si igual se cae: muestra el error del registro de Kodi
        registro = os.path.expanduser("~/.kodi/temp/kodi.log")
        os.makedirs(os.path.dirname(registro), exist_ok=True)
        with open(registro, "w") as f:
            f.write("2026-11-17 02:33:00.1 T:1   info <general>: Arrancando\n"
                    "2026-11-17 02:33:01.2 T:1  error <general>: GLX: Failed to create context\n"
                    "2026-11-17 02:33:01.3 T:1  error <general>: DBus error: UPower not provided\n")
        with open(reproducir.ruta_log("kodi"), "w") as f:
            f.write("/usr/bin/kodi: linea 190: 1234 Illegal instruction\n")
        respuestas[:] = [(-6, 2.0, "")]
        app.kodi()
        assert lanzados[-1][2]["env"]["LIBGL_ALWAYS_SOFTWARE"] == "1"
        assert isinstance(app.actual, pantallas.Mensaje) and app.actual.titulo_caja == "Kodi se cerró solo"
        assert "GLX: Failed to create context" in app.actual.texto, app.actual.texto
        assert "Illegal instruction" in app.actual.texto and "UPower" not in app.actual.texto
        app.sacar()
        config.guardar_opcion("KODI_COMPATIBLE", "no")
        shutil.which = viejo_which
    finally:
        youtube.buscar, app.lanzar = viejo_buscar, viejo_lanzar
        while len(app.pila) > 1:
            app.sacar()


def probar_marco_menu(app, paso, foto):
    """Opciones > Marco de la tele: elegir uno lo guarda en las opciones."""
    while len(app.pila) > 1:
        app.sacar()
    app.poner(pantallas.ElegirMarco())
    textos = [it.texto for it in app.actual.items]
    assert textos[0] == "Sin marco" and "Super Frecuencia" in textos and "TV Clasica" in textos, textos
    app.actual.sel = textos.index("Super Frecuencia")
    paso("a")
    assert config.leer_opciones()["MARCO"] == "Super_Frecuencia"
    assert app.actual.items[app.actual.sel].extra == "actual"
    foto("32-marcos")
    app.actual.sel = 0
    paso("a")
    assert config.leer_opciones()["MARCO"] == "ninguno"
    while len(app.pila) > 1:
        app.sacar()


def probar_espacio(app, paso, foto):
    """Espacio en el disco: tamaños, qué se puede borrar y borrar con X (en Espacio y en Videos)."""
    from televieja import espacio
    assert espacio.legible(1234567890) == "1,1 GB" and espacio.legible(5 * 1024 ** 3) == "5 GB"
    assert espacio.legible(350 * 1024 ** 2) == "350 MB"
    R = config.RAIZ
    assert not espacio.se_puede_borrar(R)
    for protegida in ("Videos", "Juegos", "Juegos/Family", "Canal/Tandas", "Historietas", "Marcos"):
        assert not espacio.se_puede_borrar(os.path.join(R, protegida)), protegida
    assert espacio.se_puede_borrar(os.path.join(R, "Videos", "Los Simpsons"))
    assert espacio.se_puede_borrar(os.path.join(R, "Dale Play"))                  # suelta
    assert not espacio.se_puede_borrar(os.path.join(MONTAJES, "1234-ABCD", "TeleVieja", "Videos"))
    grande = os.path.join(R, "Videos", "Serie Para Borrar")
    os.makedirs(grande, exist_ok=True)
    with open(os.path.join(grande, "Capitulo 1.mp4"), "wb") as f:
        f.write(b"\0" * 3 * 1024 * 1024)
    with open(os.path.join(grande, "Capitulo 2.mp4"), "wb") as f:
        f.write(b"\0" * 1024 * 1024)

    def esperar(condicion):
        fin = time.time() + 8
        while time.time() < fin and not condicion():
            app.vuelta(0.05)
            time.sleep(0.02)
        assert condicion(), app.actual

    while len(app.pila) > 1:
        app.sacar()
    # Opciones > Espacio en el disco: lo más grande primero
    pantallas.abrir_espacio(app)
    esperar(lambda: isinstance(app.actual, pantallas.EspacioDisco))
    espacio_pantalla = app.actual
    assert app.actual.items[0].texto == "Videos", [it.texto for it in app.actual.items]
    assert app.actual.titulo.startswith("Libre: ")
    paso("a")                                            # entra a Videos
    textos = [it.texto for it in app.actual.items]
    assert textos[0] == "Serie Para Borrar" and app.actual.items[0].extra == "4 MB", textos
    foto("36-espacio")
    antes = espacio_pantalla.tamanos[os.path.join(R, "Videos")]
    paso("x")                                            # borrar la serie entera
    esperar(lambda: isinstance(app.actual, pantallas.Confirmar))
    assert "Libera 4 MB" in app.actual.pregunta, app.actual.pregunta
    app.actual.opcion = 0
    paso("a")
    esperar(lambda: app.actual is espacio_pantalla and not os.path.exists(grande))
    assert espacio_pantalla.tamanos[os.path.join(R, "Videos")] == antes - 4 * 1024 * 1024
    assert "Serie Para Borrar" not in [it.texto for it in app.actual.items]
    assert app.aviso == "Liberaste 4 MB", app.aviso
    paso("b")
    # las carpetas principales no se borran
    app.actual.sel = [it.texto for it in app.actual.items].index("Videos")
    paso("x")
    assert isinstance(app.actual, pantallas.EspacioDisco) and "sistema" in app.aviso, app.aviso
    while len(app.pila) > 1:
        app.sacar()
    # En Videos, X sobre un capítulo lo borra
    otro = os.path.join(R, "Videos", "Para Borrar 2")
    tocar(os.path.join(otro, "Capitulo 1.mp4"))
    tocar(os.path.join(otro, "Capitulo 2.mp4"))
    explorador = pantallas.Explorador("video", "Videos", config.EXT_VIDEO)
    app.poner(explorador)
    explorador.sel = [it.texto for it in explorador.items].index("Para Borrar 2")
    paso("a")
    explorador.sel = [it.texto for it in explorador.items].index("Capitulo 2")
    paso("x")
    assert isinstance(app.actual, pantallas.Confirmar)
    app.actual.opcion = 0
    paso("a")
    esperar(lambda: app.actual is explorador and not os.path.exists(os.path.join(otro, "Capitulo 2.mp4")))
    assert [it.texto for it in explorador.items] == ["Capitulo 1"], [it.texto for it in explorador.items]
    # en un disco USB, X no borra
    explorador.historial.clear()
    explorador.carpeta = explorador.raiz
    explorador.cargar()
    explorador.sel = [it.texto for it in explorador.items].index("Disco: 1234-ABCD")
    paso("a")
    explorador.sel = 0
    paso("x")
    assert app.actual is explorador and "USB" in app.aviso, app.aviso
    while len(app.pila) > 1:
        app.sacar()


def probar_wifi(app, paso, foto):
    """Opciones > WiFi con redes de mentira (acá no hay NetworkManager)."""
    llamadas = []
    vacio = {"si": False}

    def wifi_falso(app_, *args, entrada=None):
        llamadas.append((args, entrada))
        if args[0] == "listar":
            if vacio["si"]:
                return {"redes": [], "detalle": "Placa wlp7s0: unavailable"}
            return {"redes": [
                {"nombre": "Casa de Roman", "senal": 30, "segura": True, "conectada": False},
                {"nombre": "Bar El Tubo", "senal": 80, "segura": True, "conectada": False},
                {"nombre": "Plaza Libre", "senal": 45, "segura": False, "conectada": False}],
                "detalle": ""}
        return {"ok": entrada == "Mate&Facturas 2\n", "mensaje": "La contraseña no es correcta."}

    pantallas._wifi = wifi_falso
    while len(app.pila) > 1:
        app.sacar()

    def esperar_pantalla(clase):
        fin = time.time() + 5
        while time.time() < fin and not isinstance(app.actual, clase):
            app.vuelta(0.05)
            time.sleep(0.02)
        assert isinstance(app.actual, clase), app.actual

    pantallas.abrir_wifi(app)
    esperar_pantalla(pantallas.RedesWifi)
    textos = [it.texto for it in app.actual.items]
    assert textos == ["Buscar de nuevo", "Casa de Roman", "Bar El Tubo", "Plaza Libre"], textos
    foto("23-wifi-redes")
    app.actual.sel = 2
    paso("a")                                  # Bar El Tubo: pide contraseña
    assert isinstance(app.actual, pantallas.Teclado)
    teclado = app.actual
    # con el teclado de la netbook (mayúsculas, símbolos, espacios)
    for letra in "Mate&Facturas":
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=letra))
    app.vuelta(0.05)
    assert teclado.texto == "Mate&Facturas", teclado.texto
    # y con el joystick: Espacio y el "2" del teclado en pantalla
    teclado.fila, teclado.col = 4, 1           # Espacio
    paso("a")
    teclado.fila, teclado.col = 0, 1           # el "2"
    paso("a")
    assert teclado.texto == "Mate&Facturas 2", teclado.texto
    paso("b", "a")                             # B borra; vuelve a poner el 2
    assert teclado.texto == "Mate&Facturas 2", teclado.texto
    foto("24-wifi-teclado")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="\r",
                                         scancode=0))
    app.vuelta(0.05)
    esperar_pantalla(pantallas.Mensaje)
    assert app.actual.titulo_caja == "¡Conectado!", app.actual.titulo_caja
    assert llamadas[-1] == (("conectar", "Bar El Tubo"), "Mate&Facturas 2\n"), llamadas[-1]
    paso("a")
    # contraseña mal: avisa
    pantallas.conectar_red(app, {"nombre": "Casa de Roman", "segura": True}, "mal")
    esperar_pantalla(pantallas.Mensaje)
    assert "contraseña" in app.actual.texto, app.actual.texto
    paso("a")
    while len(app.pila) > 1:
        app.sacar()
    # sin redes: explica lo de 2,4 GHz y muestra qué le pasa a la placa
    vacio["si"] = True
    pantallas.abrir_wifi(app)
    esperar_pantalla(pantallas.RedesWifi)
    assert [it.texto for it in app.actual.items] == ["Buscar de nuevo", "No encontré redes cerca",
                                                     "¿Por qué?"]
    app.actual.sel = 2
    paso("a")
    assert "2,4 GHz" in app.actual.texto and "unavailable" in app.actual.texto, app.actual.texto
    foto("25-wifi-por-que")
    while len(app.pila) > 1:
        app.sacar()


def main():
    pygame.display.init()
    pygame.font.init()
    pygame.joystick.init()
    cbz = preparar_contenido()
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    with open(config.ARCHIVO_OPCIONES, "w") as f:
        f.write("PUERTO_CELULAR=18080\n")
    # En esta prueba no hay emuladores instalados: hacemos de cuenta que sí.
    config.buscar_core = lambda nombres: "/falso/%s_libretro.so" % nombres[0]
    lanzados = []
    config._video_3d = (False, "prueba: placa sin 3D")  # no correr glxinfo acá
    dat = os.path.join(TMP, "arcade.dat")
    with open(dat, "w") as f:
        f.write('''clrmamepro (\n\tname "FBNeo"\n)\n
game (\n\tname "Street Fighter Alpha: Warriors' Dreams (Europe 950727)"\n\trom ( name sfa.zip size 1 crc 0 )\n)\n
game (\n\tname "Marvel Vs. Capcom: Clash of Super Heroes (Europe 980123)"\n\trom ( name mvsc.zip size 1 crc 0 )\n)\n
game (\n\tname "Metal Slug - Super Vehicle-001"\n\trom ( name mslug.zip size 1 crc 0 )\n)\n''')
    config.ARCHIVO_NOMBRES_ARCADE = dat
    probar_episodios()
    probar_canal()
    probar_marcos()
    probar_wine()
    probar_glxinfo()
    app = menu.App()
    app.lanzar = lambda orden, *a, **k: (lanzados.append(orden), (0, 10.0, ""))[1]

    def paso(*botones, pausa=0.0):
        for b in botones:
            app.actual.accion(app, b)
        fin = time.monotonic() + pausa
        while True:
            app.actual.actualizar(app, 0.1)
            if time.monotonic() >= fin:
                break
            time.sleep(0.05)
        app._dibujar(app.actual, app.lienzo)

    def foto(nombre):
        app._dibujar(app.actual, app.lienzo)
        if app.aviso:
            app._dibujar_aviso(app.lienzo)
        pygame.image.save(app.lienzo, os.path.join(SALIDA, nombre + ".png"))
        print("captura:", nombre)

    foto("01-menu")
    paso("down")                      # Videos
    paso("a")
    foto("02-videos")
    textos = [it.texto for it in app.actual.items]
    assert "Disco: 1234-ABCD" in textos and "Disco: DISCO2" in textos, textos
    assert "Dale Play" in textos and "Papeles" not in textos and "Juegos" not in textos, textos
    app.actual.sel = textos.index("Disco: 1234-ABCD")
    paso("a")
    assert app.actual.titulo == "1234-ABCD", app.actual.titulo
    foto("02b-videos-disco")
    paso("b")
    assert app.actual.titulo == "Videos"
    app.actual.sel = [it.texto for it in app.actual.items].index("One Piece")
    paso("a")
    textos = [it.texto for it in app.actual.items]
    assert textos == ["Mezclar todo", "Fondos de Pantalla", "Episodio 3", "Episodio 10",
                      "Episodio 44"], textos
    foto("03b-videos-episodios")
    app.actual.sel = [it.texto for it in app.actual.items].index("Fondos de Pantalla")
    paso("a")
    textos = [it.texto for it in app.actual.items]
    assert textos == ["Bandera", "Luffy Gear 5", "Wanted Zoro"], textos
    assert all(it.icono == "foto" for it in app.actual.items)
    app.actual.sel = 1
    paso("a")
    assert isinstance(app.actual, pantallas.Fotos), app.actual
    visor = app.actual
    for paso_visor in range(3):          # las tres se pueden abrir (también la de 256 colores)
        fin = time.time() + 5
        while time.time() < fin and visor.i not in visor.cache and visor.i not in visor.errores:
            time.sleep(0.02)
        assert visor.i in visor.cache, (visor.i, visor.errores)
        if paso_visor == 0:
            assert visor.cache[1].get_size() == (640, 360), visor.cache[1].get_size()
            foto("03c-fondo-pantalla")
        paso("right")
    assert visor.i == 1                  # dio la vuelta
    paso("b")
    assert app.actual.titulo == "Fondos de Pantalla", app.actual.titulo
    paso("b")
    paso("b")
    app.actual.sel = [it.texto for it in app.actual.items].index("El Chavo del 8")
    paso("a")                         # entrar a la carpeta
    foto("03-videos-carpeta")
    paso("down", "a")                 # reproducir
    assert lanzados and lanzados[-1][0] == "mpv", lanzados
    paso("b", "b")
    paso("down", "a")                 # Juegos
    foto("04-juegos")
    assert app.actual.items[0].extra == "16", app.actual.items[0].extra  # 15 + 1 del disco
    # N64 experimental: con la placa de esta prueba "sin 3D" no aparece...
    assert not any("Nintendo 64" in it.texto for it in app.actual.items)
    # ...y con N64=si en las opciones, sí
    with open(config.ARCHIVO_OPCIONES, "a") as f:
        f.write("N64=si\n")
    app.actual.cargar()
    n64 = [it for it in app.actual.items if "Nintendo 64" in it.texto]
    assert n64 and n64[0].extra == "1", [(it.texto, it.extra) for it in app.actual.items]
    arcade = [it for it in app.actual.items if it.texto.startswith("Arcade")][0]
    assert arcade.extra == "3", arcade.extra   # sfa, mvsc, raro (sin pgm ni neogeo)
    app.actual.sel = app.actual.items.index(arcade)
    paso("a")
    nombres = [it.texto for it in app.actual.items]
    assert nombres == ["Marvel Vs. Capcom: Clash of Super Heroes", "raro",
                       "Street Fighter Alpha: Warriors' Dreams"], nombres
    foto("05b-arcade")
    paso("b")
    pcs = [it for it in app.actual.items if it.texto == "Juegos de PC"][0]
    assert pcs.extra in ("3", "falta Wine"), pcs.extra
    from televieja import wine
    wine.hay_wine = lambda: True
    wine.prefijo_listo = lambda: True
    app.actual.cargar()
    pcs = [it for it in app.actual.items if it.texto == "Juegos de PC"][0]
    assert pcs.extra == "3", pcs.extra
    app.actual.sel = app.actual.items.index(pcs)
    paso("a")
    assert [it.texto for it in app.actual.items] == ["Con Archivo", "Juego Raro", "Sonic R"]
    foto("05c-pc")
    app.actual.sel = 2
    lanzados_pc = []
    lanzar_original = app.lanzar
    app.lanzar = lambda orden, *a, **k: (lanzados_pc.append((orden, k)), (0, 30.0, ""))[1]
    paso("a")
    orden, k = lanzados_pc[-1]
    assert orden[:3] == ["wine", "explorer", "/desktop=TeleVieja,640x480"], orden
    assert orden[3].endswith("SONICR.EXE") and k["cwd"].endswith("Sonic R"), (orden, k)
    assert k["env"]["WINEPREFIX"] == wine.PREFIJO and k["cortar"] == wine.cortar
    app.actual.sel = 1
    paso("a")                         # "Juego Raro": hay que decirle qué .exe
    assert isinstance(app.actual, pantallas.Mensaje) and "jugar.txt" in app.actual.texto
    foto("05d-pc-que-exe")
    paso("a", "b")
    app.lanzar = lanzar_original
    app.actual.cargar()   # ahora aparece "Últimos jugados" (se jugó Sonic R)
    assert app.actual.items[0].texto == "Últimos jugados", app.actual.items[0].texto
    app.actual.sel = [it.texto for it in app.actual.items].index("Family / NES")
    ps1 = [it for it in app.actual.items if it.texto == "PlayStation"][0]
    assert ps1.extra == "5", ps1.extra    # Crash, Tekken, FF7 (una vez), Juego Suelto, Wipeout
    paso("a")                         # Family
    foto("05-family")
    paso("r", "r")                    # saltar de letra
    foto("06-family-letra")
    paso("a")
    assert lanzados[-1][0] == "retroarch", lanzados[-1]
    paso("b", "b")
    paso("down", "a")                 # Historietas
    foto("07-historietas")
    # el disco 1234-ABCD tiene TeleVieja pero sin Historietas: igual aparece (se recorre entero)
    textos = [it.texto for it in app.actual.items]
    assert "Disco: 1234-ABCD" in textos, textos
    # abrir la CBZ
    indice = [i for i, it in enumerate(app.actual.items) if "Patoruzito" in it.texto][0]
    app.actual.sel = indice
    paso("a", pausa=1.5)
    assert isinstance(app.actual, pantallas.Lector), app.actual
    paso(pausa=1.0)
    foto("08-lector-ancho")
    paso("down", "down", pausa=1.0)
    foto("09-lector-bajando")
    paso("a", pausa=0.5)              # ancho -> lupa
    paso("a", pausa=0.5)              # lupa -> página entera
    foto("10-lector-pagina")
    paso("r", pausa=1.0)
    paso("b")
    assert historietas.leer_progreso()[cbz]["pagina"] == 1
    foto("11-historietas-progreso")
    paso("b", "down", "a")            # Radio
    foto("12-radio")
    # enchufar un disco con el menú abierto
    tocar(os.path.join(MONTAJES, "5678-EFGH", "TeleVieja", "Radio", "Tango.mp3"))
    app.proximo_chequeo = 0
    app.revisar_discos()
    assert "Disco conectado" in app.aviso, app.aviso
    assert any("5678-EFGH" in it.texto for it in app.actual.items)
    foto("12b-radio-disco-nuevo")
    paso("b")
    probar_controles(app, paso, foto)
    probar_mega(app, paso, foto)
    probar_wifi(app, paso, foto)
    probar_bluetooth(app, paso, foto)
    probar_grilla_menu(app, paso, foto)
    probar_archivo(app, paso, foto)
    probar_marco_menu(app, paso, foto)
    probar_youtube(app, paso, foto)
    probar_espacio(app, paso, foto)
    app.poner(pantallas.Calibrar("Encontré un joystick nuevo: vamos a configurarlo."))
    foto("13-calibrar")
    paso("b")  # (Calibrar ignora botones traducidos; sacamos a mano)
    app.sacar()
    while app.actual.titulo != app.opciones["NOMBRE_CANAL"]:
        app.sacar()
    app.actual.sel = len(app.actual.items) - 1
    paso("a")
    foto("14-apagar")
    print("OK - capturas en", SALIDA)


if __name__ == "__main__":
    main()
