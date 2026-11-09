"""Dibujo: colores, letras e íconos pensados para una tele de tubo de 640x480."""
import os

import pygame

ANCHO, ALTO = 640, 480
# Las teles de tubo "comen" los bordes de la imagen (overscan): dejamos margen.
MARGEN_X, MARGEN_Y = 44, 28

FONDO_ARRIBA = (12, 18, 64)
FONDO_ABAJO = (28, 48, 132)
AMARILLO = (255, 212, 60)
BLANCO = (236, 236, 236)
GRIS = (150, 162, 205)
GRIS_OSCURO = (90, 100, 140)
OSCURO = (10, 14, 40)
ROJO = (230, 70, 60)
VERDE = (90, 200, 110)
NARANJA = (245, 140, 40)
CELESTE = (90, 170, 240)
FRANJAS = (ROJO, NARANJA, AMARILLO, VERDE, CELESTE)

RUTAS_FUENTE = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


class Fuentes:
    def __init__(self):
        ruta = next((r for r in RUTAS_FUENTE if os.path.isfile(r)), None)
        self.titulo = pygame.font.Font(ruta, 32)
        self.item = pygame.font.Font(ruta, 26)
        self.chica = pygame.font.Font(ruta, 18)
        self.grande = pygame.font.Font(ruta, 64)
        self.puntos = "…" if ruta else "..."


def fondo():
    sup = pygame.Surface((ANCHO, ALTO))
    for y in range(ALTO):
        t = y / (ALTO - 1)
        color = [int(a + (b - a) * t) for a, b in zip(FONDO_ARRIBA, FONDO_ABAJO)]
        pygame.draw.line(sup, color, (0, y), (ANCHO, y))
    return sup


def recortar(fuente, texto, ancho, puntos="..."):
    if fuente.size(texto)[0] <= ancho:
        return texto
    while texto and fuente.size(texto + puntos)[0] > ancho:
        texto = texto[:-1]
    return texto.rstrip() + puntos


def escribir(sup, fuente, texto, color, pos, ancla="topleft", sombra=True):
    img = fuente.render(texto, True, color)
    rect = img.get_rect(**{ancla: pos})
    if sombra:
        sup.blit(fuente.render(texto, True, OSCURO), rect.move(2, 2))
    sup.blit(img, rect)
    return rect


def caja(sup, rect, color=(16, 24, 72), borde=AMARILLO):
    pygame.draw.rect(sup, color, rect, border_radius=10)
    pygame.draw.rect(sup, borde, rect, width=3, border_radius=10)


def partir_lineas(fuente, texto, ancho):
    lineas = []
    for parrafo in texto.split("\n"):
        palabras = parrafo.split(" ")
        actual = ""
        for p in palabras:
            prueba = (actual + " " + p).strip()
            if fuente.size(prueba)[0] <= ancho or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = p
        lineas.append(actual)
    return lineas


# --- íconos simples dibujados a mano (22x22) --------------------------------
def icono(sup, nombre, x, y, color):
    """Dibuja un ícono con su esquina superior izquierda en (x, y)."""
    if nombre == "carpeta":
        pygame.draw.rect(sup, color, (x, y + 5, 22, 15), border_radius=2)
        pygame.draw.rect(sup, color, (x, y + 2, 10, 5), border_radius=2)
    elif nombre == "play":
        pygame.draw.polygon(sup, color, [(x + 4, y + 2), (x + 20, y + 11), (x + 4, y + 20)])
    elif nombre == "mezclar":
        pygame.draw.line(sup, color, (x + 2, y + 5), (x + 20, y + 17), 3)
        pygame.draw.line(sup, color, (x + 2, y + 17), (x + 20, y + 5), 3)
    elif nombre == "libro":
        pygame.draw.rect(sup, color, (x + 3, y + 1, 16, 20), border_radius=2)
        for i in range(3):
            pygame.draw.line(sup, OSCURO, (x + 6, y + 6 + i * 4), (x + 15, y + 6 + i * 4), 2)
    elif nombre == "nota":
        pygame.draw.circle(sup, color, (x + 7, y + 17), 5)
        pygame.draw.line(sup, color, (x + 11, y + 17), (x + 11, y + 2), 3)
        pygame.draw.line(sup, color, (x + 11, y + 3), (x + 19, y + 7), 3)
    elif nombre == "tele":
        pygame.draw.rect(sup, color, (x, y + 6, 22, 16), border_radius=4)
        pygame.draw.line(sup, color, (x + 11, y + 6), (x + 5, y), 2)
        pygame.draw.line(sup, color, (x + 11, y + 6), (x + 17, y), 2)
        pygame.draw.rect(sup, OSCURO, (x + 3, y + 9, 13, 10), border_radius=2)
    elif nombre == "joystick":
        pygame.draw.rect(sup, color, (x, y + 6, 22, 12), border_radius=6)
        pygame.draw.line(sup, OSCURO, (x + 4, y + 12), (x + 9, y + 12), 2)
        pygame.draw.line(sup, OSCURO, (x + 6, y + 9), (x + 6, y + 15), 2)
        pygame.draw.circle(sup, OSCURO, (x + 15, y + 11), 2)
        pygame.draw.circle(sup, OSCURO, (x + 18, y + 14), 2)
    elif nombre == "usb":
        pygame.draw.rect(sup, color, (x + 6, y + 7, 10, 15), border_radius=2)
        pygame.draw.rect(sup, color, (x + 8, y + 1, 6, 7), width=2)
    elif nombre == "engranaje":
        pygame.draw.circle(sup, color, (x + 11, y + 11), 9)
        for dx, dy in ((0, -10), (0, 10), (-10, 0), (10, 0), (7, 7), (-7, -7), (7, -7), (-7, 7)):
            pygame.draw.circle(sup, color, (x + 11 + dx * 0.9, y + 11 + dy * 0.9), 3)
        pygame.draw.circle(sup, OSCURO, (x + 11, y + 11), 4)
    elif nombre == "apagar":
        pygame.draw.arc(sup, color, (x + 2, y + 3, 18, 18), 2.2, 7.2, 3)
        pygame.draw.line(sup, color, (x + 11, y), (x + 11, y + 10), 3)
    elif nombre == "flecha":
        pygame.draw.polygon(sup, color, [(x + 2, y + 11), (x + 12, y + 2), (x + 12, y + 20)])
        pygame.draw.rect(sup, color, (x + 11, y + 8, 10, 6))
