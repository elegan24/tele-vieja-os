#!/usr/bin/env python3
"""Dibuja la plantilla para hacer marcos propios (plantillas/marco/).

    python3 herramientas/plantilla_marco.py

Las medidas salen de cómo Frecuencia 99 pone el marco (televieja/marcos.py): el dibujo
(1280x720) llena la pantalla sin deformarse y el video tapa el centro.
  - Costados (x 0-160 y 1120-1280): se ven en pantallas anchas (la de la netbook) con
    videos 4:3. La netbook corta 26 px de cada borde.
  - Arriba y abajo (y 0-90 y 630-720, entre x 160 y 1120): se ven en la tele / monitor
    4:3 con videos 16:9. La tele de tubo corta más o menos un 5% de cada borde.
  - El centro (x 160-1120) lo tapa siempre el video.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(AQUI, "plantillas", "marco")

COSTADO = (178, 60, 60)      # se ve en la netbook
FRANJA = (45, 95, 175)       # se ve en la tele
CENTRO = (70, 70, 70)        # lo tapa el video
BLANCO = (255, 255, 255)
AMARILLO = (255, 214, 60)


def punteado(sup, color, a, b, paso=12):
    (x0, y0), (x1, y1) = a, b
    largo = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(0, int(largo), paso * 2):
        t0, t1 = i / largo, min(1, (i + paso) / largo)
        pygame.draw.line(sup, color, (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                         (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1), 3)


def rect_punteado(sup, color, r):
    punteado(sup, color, r.topleft, r.topright)
    punteado(sup, color, r.topright, r.bottomright)
    punteado(sup, color, r.bottomright, r.bottomleft)
    punteado(sup, color, r.bottomleft, r.topleft)


def texto(sup, fuente, linea, color, centro, girar=0):
    t = fuente.render(linea, True, color)
    if girar:
        t = pygame.transform.rotate(t, girar)
    sup.blit(t, t.get_rect(center=centro))


def guia_grande():
    """1280x720 con las zonas, los cortes de cada pantalla y carteles."""
    W, H = 1280, 720
    s = pygame.Surface((W, H))
    s.fill(COSTADO)
    pygame.draw.rect(s, FRANJA, (160, 0, 960, 720))
    pygame.draw.rect(s, CENTRO, (160, 90, 960, 540))
    # cuadrícula suave para ayudar a ubicar
    for x in range(0, W, 40):
        pygame.draw.line(s, (0, 0, 0), (x, 0), (x, H), 1)
    for y in range(0, H, 40):
        pygame.draw.line(s, (0, 0, 0), (0, y), (W, y), 1)
    pygame.draw.rect(s, BLANCO, (160, 0, 960, 720), 3)
    pygame.draw.rect(s, BLANCO, (160, 90, 960, 540), 3)
    # lo que corta cada pantalla
    punteado(s, AMARILLO, (26, 0), (26, H))
    punteado(s, AMARILLO, (1254, 0), (1254, H))
    rect_punteado(s, AMARILLO, pygame.Rect(208, 36, 864, 648))

    grande = pygame.font.Font(None, 54)
    media = pygame.font.Font(None, 34)
    chica = pygame.font.Font(None, 26)
    texto(s, grande, "ACÁ VA EL VIDEO", BLANCO, (640, 300))
    texto(s, media, "Esta parte no se ve: la tapa el video.", BLANCO, (640, 350))
    texto(s, chica, "Plantilla de marco · Frecuencia 99 · 1280 x 720", (200, 200, 200), (640, 600))
    texto(s, media, "SE VE EN LA TELE con videos 16:9", BLANCO, (640, 62))
    texto(s, media, "SE VE EN LA TELE con videos 16:9", BLANCO, (640, 660))
    texto(s, media, "SE VE EN LA NETBOOK con videos 4:3", BLANCO, (93, 360), girar=90)
    texto(s, media, "SE VE EN LA NETBOOK con videos 4:3", BLANCO, (1187, 360), girar=-90)
    texto(s, chica, "- - -  lo que queda afuera de la línea amarilla", AMARILLO, (640, 22))
    texto(s, chica, "puede no verse (la pantalla corta los bordes)  - - -", AMARILLO, (640, 700))
    return s


def guia_chica():
    """320x180 (pixel art, con "pixelArt": true): las mismas zonas, a 1/4."""
    W, H = 320, 180
    s = pygame.Surface((W, H))
    s.fill(COSTADO)
    pygame.draw.rect(s, FRANJA, (40, 0, 240, 180))
    pygame.draw.rect(s, CENTRO, (40, 22, 240, 136))
    pygame.draw.rect(s, BLANCO, (40, 0, 240, 180), 1)
    pygame.draw.rect(s, BLANCO, (40, 22, 240, 136), 1)
    for x in range(0, 180, 4):          # cortes, punteados
        s.set_at((6, x), AMARILLO)
        s.set_at((313, x), AMARILLO)
    r = pygame.Rect(52, 9, 216, 162)
    for x in range(r.left, r.right, 4):
        s.set_at((x, r.top), AMARILLO)
        s.set_at((x, r.bottom), AMARILLO)
    for y in range(r.top, r.bottom, 4):
        s.set_at((r.left, y), AMARILLO)
        s.set_at((r.right, y), AMARILLO)
    chica = pygame.font.Font(None, 16)
    texto(s, chica, "VIDEO (no se ve)", BLANCO, (160, 90))
    texto(s, chica, "TELE 16:9", BLANCO, (160, 14))
    texto(s, chica, "TELE 16:9", BLANCO, (160, 168))
    texto(s, chica, "NETBOOK 4:3", BLANCO, (22, 90), girar=90)
    texto(s, chica, "NETBOOK 4:3", BLANCO, (298, 90), girar=-90)
    return s


def ejemplo():
    """Un marco simple hecho sobre la guía: degradé, nombre a los costados y abajo."""
    W, H = 1280, 720
    s = pygame.Surface((W, H))
    for y in range(H):  # degradé violeta a naranja
        t = y / H
        s.fill((int(60 + 160 * t), int(30 + 60 * t), int(110 - 60 * t)), (0, y, W, 1))
    for x in range(-H, W, 48):  # rayas finas
        pygame.draw.line(s, (255, 255, 255), (x, H), (x + H, 0), 1)
    fuente = pygame.font.Font(None, 64)
    for x, angulo in ((93, 90), (1187, -90)):          # costados: se ve en la netbook
        texto(s, fuente, "MI TELE", BLANCO, (x, 360), girar=angulo)
    texto(s, pygame.font.Font(None, 48), "MI CANAL", BLANCO, (640, 62))    # arriba: tele
    texto(s, pygame.font.Font(None, 48), "MI CANAL", BLANCO, (640, 660))   # abajo: tele
    return s


def armar_zip():
    import zipfile
    raiz = os.path.dirname(DESTINO)
    with zipfile.ZipFile(os.path.join(raiz, "plantilla-marco.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for carpeta, _, archivos in os.walk(DESTINO):
            for a in sorted(archivos):
                ruta = os.path.join(carpeta, a)
                z.write(ruta, os.path.relpath(ruta, raiz))


def main():
    pygame.init()
    os.makedirs(DESTINO, exist_ok=True)
    pygame.image.save(guia_grande(), os.path.join(DESTINO, "guia-1280x720.png"))
    pygame.image.save(guia_chica(), os.path.join(DESTINO, "guia-pixelart-320x180.png"))
    carpeta_ejemplo = os.path.join(DESTINO, "ejemplo", "Mi_Marco")
    os.makedirs(carpeta_ejemplo, exist_ok=True)
    pygame.image.save(ejemplo(), os.path.join(carpeta_ejemplo, "default.png"))
    with open(os.path.join(DESTINO, "ejemplo", "marco.json"), "w") as f:
        f.write('{"pixelArt": false}\n')
    armar_zip()
    print("Plantilla en", DESTINO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
