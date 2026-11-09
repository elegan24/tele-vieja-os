"""Prueba sin tele: arma contenido de ejemplo, recorre el menú y guarda capturas.

Uso:  python3 pruebas/prueba_menu.py CARPETA_CAPTURAS
"""
import os
import sys
import tempfile
import time
import zipfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["TELEVIEJA_VENTANA"] = "1"
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
    tocar(os.path.join(R, "Canal", "Programas", "El Zorro 01.mp4"))
    tocar(os.path.join(R, "Canal", "Tandas", "Publicidad Coca 1991.mp4"))
    for n in ["Super Mario Bros. (World)", "Contra (U) [!]", "Duck Hunt (World)",
              "Adventure Island (U)", "Battle City (J)", "Bomberman (U)", "Castlevania (U) [!]",
              "Excitebike (JU)", "Ice Climber (U)", "Kung Fu (U)", "Mega Man 2 (U)",
              "Ninja Gaiden (U)", "Pac-Man (U)", "Tetris (U)", "Zelda (U)"]:
        tocar(os.path.join(R, "Juegos", "Family", n + ".nes"))
    tocar(os.path.join(R, "Juegos", "NeoGeo", "mslug.zip"))
    tocar(os.path.join(R, "Juegos", "NeoGeo", "neogeo.zip"))
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


def main():
    pygame.display.init()
    pygame.font.init()
    pygame.joystick.init()
    cbz = preparar_contenido()
    # En esta prueba no hay emuladores instalados: hacemos de cuenta que sí.
    config.buscar_core = lambda nombres: "/falso/%s_libretro.so" % nombres[0]
    lanzados = []
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
