"""Temas: colores, decoración de fondo y sonidos del menú.

Cada tema define:
  fondo_arriba / fondo_abajo  degradé del fondo
  acento     color de lo elegido y los títulos
  elegido    color del texto sobre lo elegido
  texto, gris, gris_oscuro, sombra, caja
  franjas    las rayitas de colores del título
  sombras    si el texto lleva sombra
  sonido     (forma de onda, multiplicador de tono)
  decorar    función que dibuja adornos sobre el fondo
"""
import datetime
import math
import random

import pygame

ANCHO, ALTO = 640, 480


# --- adornos ------------------------------------------------------------------
def _nada(sup, t):
    pass


def _fichin(sup, t):
    """Estrellitas arriba y una grilla de neón que se pierde en el horizonte."""
    r = random.Random(7)
    for _ in range(70):
        x, y = r.randrange(ANCHO), r.randrange(ALTO // 2)
        brillo = r.randrange(80, 200)
        sup.set_at((x, y), (brillo, brillo, min(255, brillo + 40)))
    horizonte = ALTO - 120
    color = (110, 20, 110)
    for i in range(1, 12):
        y = horizonte + int((i / 11) ** 2 * 120)
        pygame.draw.line(sup, color, (0, y), (ANCHO, y))
    for i in range(-12, 13):
        x_abajo = ANCHO // 2 + i * 70
        pygame.draw.line(sup, color, (ANCHO // 2 + i * 8, horizonte), (x_abajo, ALTO))
    pygame.draw.line(sup, (255, 60, 200), (0, horizonte), (ANCHO, horizonte), 2)


def _gameboy(sup, t):
    """La grilla de puntitos de la pantalla de la Game Boy."""
    color = [max(0, c - 8) for c in t["fondo_abajo"]]
    for x in range(0, ANCHO, 4):
        pygame.draw.line(sup, color, (x, 0), (x, ALTO))
    for y in range(0, ALTO, 4):
        pygame.draw.line(sup, color, (0, y), (ANCHO, y))


def _cine(sup, t):
    """Telón de terciopelo a los costados y arriba."""
    for lado in (0, 1):
        for i in range(8):
            ancho = 38 - i * 4
            x = i * 4 if lado == 0 else ANCHO - i * 4 - ancho
            tono = 70 + (i % 2) * 30
            pygame.draw.rect(sup, (tono, 6, 12), (x, 0, ancho, ALTO))
    for i in range(16):
        pygame.draw.ellipse(sup, (120, 12, 24), (i * 42 - 10, -14, 60, 34))
    pygame.draw.line(sup, (230, 185, 90), (0, 16), (ANCHO, 16), 2)


def _canal7(sup, t):
    """La carta de ajuste, bien tenue de fondo, y las barras de color abajo."""
    centro = (ANCHO // 2, ALTO // 2 + 20)
    for radio in (150, 110):
        pygame.draw.circle(sup, (58, 58, 58), centro, radio, 2)
    for x in range(40, ANCHO, 40):
        pygame.draw.line(sup, (50, 50, 50), (x, 0), (x, ALTO))
    for y in range(40, ALTO, 40):
        pygame.draw.line(sup, (50, 50, 50), (0, y), (ANCHO, y))
    barras = BARRAS_CARTA
    ancho = ANCHO / len(barras)
    for i, color in enumerate(barras):
        pygame.draw.rect(sup, color, (int(i * ancho), ALTO - 14, int(ancho) + 1, 14))


def _navidad(sup, t):
    """Nieve y una guirnalda de lucecitas arriba."""
    r = random.Random(25)
    for _ in range(55):
        x, y = r.randrange(ANCHO), r.randrange(ALTO)
        radio = r.choice((1, 1, 1, 2))
        pygame.draw.circle(sup, (170, 200, 185), (x, y), radio)
    colores = ((230, 50, 50), (250, 210, 60), (70, 170, 255), (90, 220, 110))
    for i, x in enumerate(range(10, ANCHO, 32)):
        y = 8 + int(6 * math.sin(x / 40))
        pygame.draw.line(sup, (30, 70, 40), (x, y), (x + 32, 8 + int(6 * math.sin((x + 32) / 40))), 2)
        pygame.draw.circle(sup, colores[i % 4], (x, y + 6), 4)


def _halloween(sup, t):
    """Luna llena y murciélagos."""
    # luna tenue, entre el título y la hora (el texto se lee encima)
    pygame.draw.circle(sup, (120, 105, 80), (ANCHO - 170, 48), 26)
    pygame.draw.circle(sup, (105, 92, 70), (ANCHO - 178, 42), 5)
    pygame.draw.circle(sup, (105, 92, 70), (ANCHO - 162, 58), 4)
    r = random.Random(31)
    for _ in range(7):
        x, y = r.randrange(40, ANCHO - 120), r.randrange(60, ALTO - 80)
        e = r.choice((0.6, 0.8, 1.0))
        ala = [(x, y), (x - 14 * e, y - 8 * e), (x - 22 * e, y + 2 * e), (x - 10 * e, y),
               (x, y + 6 * e), (x + 10 * e, y), (x + 22 * e, y + 2 * e), (x + 14 * e, y - 8 * e)]
        pygame.draw.polygon(sup, (25, 8, 30), ala)


BARRAS_CARTA = ((235, 235, 235), (235, 235, 16), (16, 235, 235), (16, 235, 16),
                (235, 16, 235), (235, 16, 16), (16, 16, 235))

TEMAS = {
    "clasico": {
        "nombre": "Clásico",
        "fondo_arriba": (12, 18, 64), "fondo_abajo": (28, 48, 132),
        "acento": (255, 212, 60), "elegido": (10, 14, 40),
        "texto": (236, 236, 236), "gris": (150, 162, 205), "gris_oscuro": (90, 100, 140),
        "sombra": (10, 14, 40), "caja": (16, 24, 72), "sombras": True,
        "franjas": ((230, 70, 60), (245, 140, 40), (255, 212, 60), (90, 200, 110), (90, 170, 240)),
        "sonido": ("cuadrada", 1.0), "decorar": _nada,
    },
    "fichin": {
        "nombre": "Fichín (arcade)",
        "fondo_arriba": (4, 2, 14), "fondo_abajo": (26, 6, 40),
        "acento": (255, 60, 200), "elegido": (10, 0, 20),
        "texto": (245, 245, 255), "gris": (90, 230, 255), "gris_oscuro": (110, 60, 140),
        "sombra": (0, 0, 0), "caja": (20, 4, 34), "sombras": True,
        "franjas": ((255, 60, 200), (255, 230, 0), (0, 255, 200), (0, 180, 255), (180, 80, 255)),
        "sonido": ("cuadrada", 1.5), "decorar": _fichin,
    },
    "gameboy": {
        "nombre": "Game Boy",
        "fondo_arriba": (155, 188, 15), "fondo_abajo": (139, 172, 15),
        "acento": (48, 98, 48), "elegido": (155, 188, 15),
        "texto": (15, 56, 15), "gris": (48, 98, 48), "gris_oscuro": (100, 140, 30),
        "sombra": (139, 172, 15), "caja": (139, 172, 15), "sombras": False,
        "franjas": ((15, 56, 15), (48, 98, 48), (100, 140, 30), (48, 98, 48), (15, 56, 15)),
        "sonido": ("cuadrada", 2.0), "decorar": _gameboy, "logo": (155, 188, 15),
    },
    "cine": {
        "nombre": "Cine",
        "fondo_arriba": (34, 4, 8), "fondo_abajo": (80, 10, 18),
        "acento": (230, 185, 90), "elegido": (40, 6, 10),
        "texto": (245, 232, 200), "gris": (205, 165, 120), "gris_oscuro": (130, 80, 70),
        "sombra": (20, 2, 4), "caja": (50, 6, 12), "sombras": True,
        "franjas": ((230, 185, 90), (200, 150, 60), (160, 20, 30), (200, 150, 60), (230, 185, 90)),
        "sonido": ("triangulo", 0.7), "decorar": _cine,
    },
    "canal7": {
        "nombre": "Canal 7 años 80",
        "fondo_arriba": (30, 30, 30), "fondo_abajo": (44, 44, 44),
        "acento": (240, 240, 240), "elegido": (10, 10, 10),
        "texto": (235, 235, 235), "gris": (175, 175, 175), "gris_oscuro": (100, 100, 100),
        "sombra": (0, 0, 0), "caja": (20, 20, 20), "sombras": True,
        "franjas": BARRAS_CARTA,
        "sonido": ("seno", 1.13), "decorar": _canal7,  # 1000 Hz: el pitido de la carta
    },
    "navidad": {
        "nombre": "Navidad",
        "fondo_arriba": (6, 40, 24), "fondo_abajo": (14, 78, 40),
        "acento": (215, 40, 50), "elegido": (255, 255, 255),
        "texto": (250, 250, 245), "gris": (200, 230, 200), "gris_oscuro": (90, 140, 100),
        "sombra": (2, 20, 10), "caja": (10, 50, 28), "sombras": True,
        "franjas": ((215, 40, 50), (250, 250, 245), (90, 200, 110), (250, 210, 60), (215, 40, 50)),
        "sonido": ("campana", 1.6), "decorar": _navidad,
    },
    "halloween": {
        "nombre": "Halloween",
        "fondo_arriba": (8, 3, 16), "fondo_abajo": (44, 14, 44),
        "acento": (255, 130, 20), "elegido": (20, 5, 20),
        "texto": (240, 230, 210), "gris": (200, 150, 220), "gris_oscuro": (110, 70, 120),
        "sombra": (0, 0, 0), "caja": (30, 8, 34), "sombras": True,
        "franjas": ((255, 130, 20), (120, 200, 60), (160, 60, 200), (255, 130, 20), (120, 200, 60)),
        "sonido": ("triangulo", 0.5), "decorar": _halloween,
    },
}
ORDEN = ["clasico", "fichin", "gameboy", "cine", "canal7", "navidad", "halloween"]


def de_temporada(hoy=None):
    """El tema que corresponde por la fecha (para TEMA=auto)."""
    hoy = hoy or datetime.date.today()
    if (hoy.month == 12) or (hoy.month == 1 and hoy.day <= 6):
        return "navidad"
    if (hoy.month == 10 and hoy.day >= 20) or (hoy.month == 11 and hoy.day <= 2):
        return "halloween"
    return "clasico"


def elegir(opcion, hoy=None):
    opcion = (opcion or "auto").lower()
    if opcion in TEMAS:
        return opcion
    return de_temporada(hoy)


def color_ass(rgb):
    """(r, g, b) -> "&HBBGGRR&" (el formato de colores de los subtítulos de mpv)."""
    return "&H%02X%02X%02X&" % (rgb[2], rgb[1], rgb[0])
