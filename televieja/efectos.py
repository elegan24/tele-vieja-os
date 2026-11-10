"""Efectos de tele de tubo: encendido, apagado y protector de pantalla."""
import time

import pygame

from . import temas, ui
from .ui import ANCHO, ALTO


def _blanco_encima(sup, alfa):
    if alfa <= 0:
        return
    capa = pygame.Surface((ANCHO, ALTO))
    capa.fill((255, 255, 255))
    capa.set_alpha(int(max(0, min(255, alfa))))
    sup.blit(capa, (0, 0))


def cuadro_encendido(imagen, t):
    """Un cuadro del encendido, con t de 0 a 1: rayita -> se abre la imagen -> brillo que baja."""
    sup = pygame.Surface((ANCHO, ALTO))
    sup.fill((0, 0, 0))
    if t < 0.18:  # la rayita horizontal se estira desde el centro
        largo = max(2, int(ANCHO * (t / 0.18)))
        pygame.draw.rect(sup, (255, 255, 255), ((ANCHO - largo) // 2, ALTO // 2 - 1, largo, 3))
    elif t < 0.7:  # la imagen se abre para arriba y para abajo
        k = (t - 0.18) / 0.52
        alto = max(3, int(ALTO * (1 - (1 - k) ** 3)))
        sup.blit(pygame.transform.scale(imagen, (ANCHO, alto)), (0, (ALTO - alto) // 2))
        _blanco_encima(sup, 200 * (1 - k))
    else:  # brillo que se va apagando
        sup.blit(imagen, (0, 0))
        _blanco_encima(sup, 90 * (1 - (t - 0.7) / 0.3))
    return sup


def cuadro_apagado(imagen, t):
    """Al revés: la imagen se aplasta en una rayita, la rayita en un punto y el punto se apaga."""
    sup = pygame.Surface((ANCHO, ALTO))
    sup.fill((0, 0, 0))
    if t < 0.4:
        k = t / 0.4
        alto = max(3, int(ALTO * (1 - k) ** 2))
        sup.blit(pygame.transform.scale(imagen, (ANCHO, alto)), (0, (ALTO - alto) // 2))
        _blanco_encima(sup, 220 * k)
    elif t < 0.7:
        k = (t - 0.4) / 0.3
        largo = max(4, int(ANCHO * (1 - k)))
        pygame.draw.rect(sup, (255, 255, 255), ((ANCHO - largo) // 2, ALTO // 2 - 1, largo, 3))
    else:
        k = (t - 0.7) / 0.3
        brillo = int(255 * (1 - k))
        pygame.draw.circle(sup, (brillo, brillo, brillo), (ANCHO // 2, ALTO // 2), 4)
    return sup


def animar(app, cuadro, imagen, segundos):
    """Muestra la animación en la pantalla (bloquea un ratito)."""
    inicio = time.monotonic()
    reloj = pygame.time.Clock()
    while True:
        t = (time.monotonic() - inicio) / segundos
        if t >= 1:
            break
        app.mostrar(cuadro(imagen, t))
        pygame.event.pump()
        reloj.tick(30)


# --- protector de pantalla ---------------------------------------------------------
def dibujar_carta(sup, fuentes, nombre):
    """La carta de ajuste, como cuando terminaba la programación."""
    sup.fill((110, 110, 110))
    for x in range(0, ANCHO + 1, 40):
        pygame.draw.line(sup, (230, 230, 230), (x, 0), (x, ALTO), 2)
    for y in range(0, ALTO + 1, 40):
        pygame.draw.line(sup, (230, 230, 230), (0, y), (ANCHO, y), 2)
    centro = (ANCHO // 2, ALTO // 2)
    pygame.draw.circle(sup, (25, 25, 25), centro, 200)
    pygame.draw.circle(sup, (235, 235, 235), centro, 200, 3)
    # barras de color en la franja de arriba del círculo
    barras = temas.BARRAS_CARTA
    ancho = 300 / len(barras)
    for i, color in enumerate(barras):
        pygame.draw.rect(sup, color, (int(centro[0] - 150 + i * ancho), centro[1] - 140,
                                      int(ancho) + 1, 90))
    # escala de grises
    for i in range(6):
        g = int(i * 255 / 5)
        pygame.draw.rect(sup, (g, g, g), (centro[0] - 150 + i * 50, centro[1] + 60, 50, 50))
    # cartel con el nombre y la hora
    cartel = pygame.Rect(0, 0, 300, 70)
    cartel.center = (centro[0], centro[1] + 5)
    pygame.draw.rect(sup, (0, 0, 0), cartel)
    pygame.draw.rect(sup, (235, 235, 235), cartel, 2)
    ui.escribir(sup, fuentes.item, nombre, (240, 240, 240), (cartel.centerx, cartel.y + 8), "midtop",
                sombra=False)
    ui.escribir(sup, fuentes.chica, time.strftime("%H:%M"), (240, 240, 240),
                (cartel.centerx, cartel.bottom - 8), "midbottom", sombra=False)
    pygame.draw.line(sup, (235, 235, 235), (centro[0], centro[1] - 200), (centro[0], centro[1] - 145), 2)
    pygame.draw.line(sup, (235, 235, 235), (centro[0], centro[1] + 115), (centro[0], centro[1] + 200), 2)


class LogoRebotando:
    """El logo que rebota por la pantalla y cambia de color en cada choque."""

    def __init__(self, fuente, texto):
        self.fuente = fuente
        self.texto = texto
        self.x, self.y = 80.0, 120.0
        self.vx, self.vy = 70.0, 52.0      # pixeles por segundo
        self.color = 0
        self.esquinas = 0

    def mover(self, dt):
        img = self.fuente.render(self.texto, True, (255, 255, 255))
        w, h = img.get_size()
        self.x += self.vx * dt
        self.y += self.vy * dt
        choques = 0
        if self.x <= 0 or self.x + w >= ANCHO:
            self.vx = -self.vx
            self.x = max(0, min(ANCHO - w, self.x))
            choques += 1
        if self.y <= 0 or self.y + h >= ALTO:
            self.vy = -self.vy
            self.y = max(0, min(ALTO - h, self.y))
            choques += 1
        if choques:
            self.color += 1
        if choques == 2:
            self.esquinas += 1  # ¡justo en la esquina!

    def dibujar(self, sup):
        sup.fill((0, 0, 0))
        # colores vivos de la carta de ajuste (sin el azul, que sobre negro casi no se ve)
        colores = temas.BARRAS_CARTA[:-1]
        color = colores[self.color % len(colores)]
        img = self.fuente.render(self.texto, True, color)
        sup.blit(img, (int(self.x), int(self.y)))
        if self.esquinas:
            ui.escribir(sup, pygame.font.Font(None, 22), "esquinas: %d" % self.esquinas,
                        (90, 90, 90), (ANCHO - 10, ALTO - 8), "bottomright", sombra=False)


def fase_protector(segundos):
    """Alterna: 45 s de carta de ajuste y 3 minutos de logo (así no se marca el tubo)."""
    ciclo = segundos % (45 + 180)
    return "carta" if ciclo < 45 else "logo"
