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
    # películas sin número: por nombre
    assert config.ordenar_episodios(["Volver al futuro.avi", "Titanic.mp4", "Rocky 2.mp4"]) == \
        ["Rocky 2.mp4", "Titanic.mp4", "Volver al futuro.avi"]


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
