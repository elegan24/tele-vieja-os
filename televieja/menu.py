"""TeleVieja OS: el menú que aparece al prender la netbook."""
import array
import os
import subprocess
import sys
import time

os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from . import config, reproducir, ui  # noqa: E402
from .mando import Mando  # noqa: E402
from .pantallas import (Calibrar, Confirmar, Espera, Explorador, Item, Lista,  # noqa: E402
                        ListaSistemas, Mensaje)
from .ui import ANCHO, ALTO, MARGEN_X, MARGEN_Y  # noqa: E402

SALIR_A_TERMINAL = 10
FPS = 20


class Sonido:
    """Pitiditos del menú, generados acá mismo (no hacen falta archivos)."""

    def __init__(self, activo):
        self.activo = activo
        self.sonidos = {}
        self.prender()

    def prender(self):
        if not self.activo:
            return
        try:
            pygame.mixer.init(22050, -16, 1, 512)
            frec, _, canales = pygame.mixer.get_init()
            self.sonidos = {
                "mover": self._tono(frec, canales, 880, 25, 0.15),
                "elegir": self._tono(frec, canales, 1320, 60, 0.2),
                "volver": self._tono(frec, canales, 440, 60, 0.2),
            }
        except pygame.error:
            self.sonidos = {}

    def apagar(self):
        self.sonidos = {}
        if pygame.mixer.get_init():
            pygame.mixer.quit()

    @staticmethod
    def _tono(frec, canales, hz, ms, volumen):
        n = int(frec * ms / 1000)
        datos = array.array("h")
        periodo = max(2, int(frec / hz))
        for i in range(n):
            v = int(32767 * volumen * (1 - i / n) * (1 if (i % periodo) < periodo // 2 else -1))
            datos.extend([v] * canales)
        return pygame.mixer.Sound(buffer=datos.tobytes())

    def tocar(self, nombre):
        s = self.sonidos.get(nombre)
        if s:
            s.play()


class App:
    def __init__(self):
        self.opciones = config.leer_opciones()
        self.ventana = bool(os.environ.get("TELEVIEJA_VENTANA"))
        self.iniciar_pantalla()
        self.fuentes = ui.Fuentes()
        self.mando = Mando()
        self.sonido = Sonido(config.opcion_si(self.opciones, "SONIDOS_MENU"))
        self.pila = []
        self.sucio = True
        self.ultimo_minuto = ""
        self.corriendo = True
        self.codigo_salida = 0
        self.poner(menu_principal(self))

    # --- pantalla física ---------------------------------------------------
    def iniciar_pantalla(self):
        if pygame.display.get_init():
            pygame.display.quit()
        pygame.display.init()
        pygame.display.set_caption("TeleVieja")
        if self.ventana:
            self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        else:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
        self.lienzo = pygame.Surface((ANCHO, ALTO))
        self.fondo = ui.fondo()
        self.sucio = True

    def mostrar(self):
        destino = self.pantalla.get_size()
        if destino == (ANCHO, ALTO):
            self.pantalla.blit(self.lienzo, (0, 0))
        else:  # pantalla de la netbook: agrandamos manteniendo 4:3
            escala = min(destino[0] / ANCHO, destino[1] / ALTO)
            tam = (int(ANCHO * escala), int(ALTO * escala))
            self.pantalla.fill((0, 0, 0))
            self.pantalla.blit(pygame.transform.scale(self.lienzo, tam),
                               ((destino[0] - tam[0]) // 2, (destino[1] - tam[1]) // 2))
        pygame.display.flip()

    # --- pila de pantallas ---------------------------------------------------
    @property
    def actual(self):
        return self.pila[-1]

    def poner(self, pantalla):
        self.pila.append(pantalla)
        self.sucio = True

    def sacar(self):
        if len(self.pila) > 1:
            self.pila.pop()
            self.actual.al_volver(self)
        self.sucio = True

    def dibujar_debajo(self, pantalla, sup):
        """Para cajas de aviso: dibuja la pantalla de atrás."""
        i = self.pila.index(pantalla) if pantalla in self.pila else len(self.pila)
        if i > 0:
            self._dibujar(self.pila[i - 1], sup)

    def _dibujar(self, p, sup):
        if p.sin_marco:
            p.dibujar(self, sup)
            return
        if isinstance(p, (Mensaje, Confirmar)):
            p.dibujar(self, sup)
            return
        sup.blit(self.fondo, (0, 0))
        f = self.fuentes
        # franjas de colores, bien de los 80
        for i, color in enumerate(ui.FRANJAS):
            pygame.draw.rect(sup, color, (MARGEN_X, MARGEN_Y + 4 + i * 7, 26, 5))
        titulo = ui.recortar(f.titulo, p.titulo or "", ANCHO - 2 * MARGEN_X - 130, f.puntos)
        ui.escribir(sup, f.titulo, titulo, ui.AMARILLO, (MARGEN_X + 38, MARGEN_Y))
        ui.escribir(sup, f.item, time.strftime("%H:%M"), ui.BLANCO, (ANCHO - MARGEN_X, MARGEN_Y + 4),
                    "topright")
        pygame.draw.line(sup, ui.GRIS_OSCURO, (MARGEN_X, MARGEN_Y + 48), (ANCHO - MARGEN_X, MARGEN_Y + 48), 2)
        pie = ALTO - MARGEN_Y - 22
        ui.escribir(sup, f.chica, ui.recortar(f.chica, p.ayuda, ANCHO - 2 * MARGEN_X - 90, f.puntos),
                    ui.GRIS, (MARGEN_X, pie))
        if p.info():
            ui.escribir(sup, f.chica, p.info(), ui.GRIS, (ANCHO - MARGEN_X, pie), "topright")
        p.dibujar(self, sup)

    # --- programas externos ----------------------------------------------------
    def lanzar(self, orden, control=None, nombre_log="ultimo", combo_salida=False):
        """Corre mpv o RetroArch y espera. Mientras tanto escucha el joystick."""
        self.sonido.apagar()
        inicio = time.monotonic()
        try:
            with open(reproducir.ruta_log(nombre_log), "w") as log:
                proc = subprocess.Popen(orden, stdout=log, stderr=subprocess.STDOUT)
        except OSError as e:
            self.sonido.prender()
            return None, 0.0, str(e)
        combo_desde = None
        pidio_salir = None
        while proc.poll() is None:
            for ev in pygame.event.get():
                for boton in self.mando.traducir(ev):
                    if control and control(boton):
                        pidio_salir = pidio_salir or time.monotonic()
            if combo_salida and self.mando.esta_apretado("select") and self.mando.esta_apretado("start"):
                combo_desde = combo_desde or time.monotonic()
                if time.monotonic() - combo_desde > 2.5:
                    proc.terminate()
            else:
                combo_desde = None
            if pidio_salir and time.monotonic() - pidio_salir > 4:
                proc.terminate()
            time.sleep(0.03)
        duracion = time.monotonic() - inicio
        self.mando.soltar_todo()
        pygame.event.clear()
        self.sonido.prender()
        self.sucio = True
        return proc.returncode, duracion, ""

    def _ultimas_lineas(self, nombre_log, n=3):
        try:
            with open(reproducir.ruta_log(nombre_log), encoding="utf-8", errors="replace") as f:
                lineas = [l.strip() for l in f if l.strip()]
            return "\n".join(lineas[-n:])
        except OSError:
            return ""

    def lanzar_mpv(self, orden, control):
        rc, duracion, error = self.lanzar(orden, control, "video")
        if rc is None:
            self.poner(Mensaje("Falta mpv", "No está instalado el reproductor: " + error))
        elif rc not in (0, 4) and duracion < 4:
            self.poner(Mensaje("No se pudo reproducir", self._ultimas_lineas("video")))

    def jugar(self, core, rom):
        orden = reproducir.orden_juego(core, rom)
        rc, duracion, error = self.lanzar(orden, None, "juego", combo_salida=True)
        if rc is None:
            self.poner(Mensaje("Falta RetroArch", error))
        elif rc != 0 and duracion < 5:
            self.poner(Mensaje("No se pudo abrir el juego", self._ultimas_lineas("juego")))

    def canal(self):
        lista = reproducir.armar_canal(self.opciones)
        if not lista:
            self.poner(Mensaje("El canal está vacío",
                               "Poné videos en TeleVieja/Canal/Programas (y publicidades viejas "
                               "en TeleVieja/Canal/Tandas)."))
            return
        self.lanzar_mpv(reproducir.orden_canal(self.opciones, lista), reproducir.control_canal)

    def cambiar_pantalla(self):
        script = os.path.join(config.BIN_DIR, "pantalla.sh")
        subprocess.run([script, "alternar"], capture_output=True)
        self.iniciar_pantalla()

    def sistema(self, accion):
        r = subprocess.run(["sudo", "-n", "systemctl", accion], capture_output=True, text=True)
        if r.returncode != 0:
            self.poner(Mensaje("No se pudo", r.stderr.strip() or "Error"))

    def salir_a_terminal(self):
        self.codigo_salida = SALIR_A_TERMINAL
        self.corriendo = False

    # --- bucle principal --------------------------------------------------------
    def correr(self):
        reloj = pygame.time.Clock()
        if self.opciones.get("ARRANCAR_EN", "menu").lower() == "canal":
            self.canal()
        while self.corriendo:
            dt = reloj.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.corriendo = False
                if ev.type in (pygame.VIDEOEXPOSE, pygame.WINDOWEXPOSED if hasattr(pygame, "WINDOWEXPOSED") else -1):
                    self.sucio = True
                botones = self.mando.traducir(ev)
                if ev.type == pygame.JOYDEVICEADDED:
                    self._joystick_nuevo(ev.device_index)
                if self.actual.crudo:
                    self.actual.evento(self, ev)
                    continue
                for b in botones:
                    self.actual.accion(self, b)
            if not self.actual.crudo:
                for b in self.mando.repeticiones():
                    self.actual.accion(self, b)
            self.actual.actualizar(self, dt)
            minuto = time.strftime("%H:%M")
            if minuto != self.ultimo_minuto:
                self.ultimo_minuto = minuto
                self.sucio = True
            if self.sucio:
                self.sucio = False
                self._dibujar(self.actual, self.lienzo)
                self.mostrar()
        return self.codigo_salida

    def _joystick_nuevo(self, indice):
        try:
            j = pygame.joystick.Joystick(indice)
        except pygame.error:
            return
        if not self.mando.esta_calibrado(j) and not isinstance(self.actual, Calibrar) \
                and not self.mando.calibraciones:
            self.poner(Calibrar("Encontré un joystick nuevo: vamos a configurarlo."))


def menu_principal(app):
    def ir(pantalla_fabrica):
        return lambda app: app.poner(pantalla_fabrica())

    opciones = Lista("Opciones", [
        Item("Configurar joystick", ir(lambda: Calibrar()), icono="joystick"),
        Item("Cambiar pantalla (tele / netbook)", lambda app: app.cambiar_pantalla(), icono="tele"),
        Item("Reiniciar", lambda app: app.poner(Confirmar("¿Reiniciar?", lambda a: a.sistema("reboot"))),
             icono="flecha"),
        Item("Salir a la terminal", lambda app: app.salir_a_terminal(), icono="engranaje"),
    ])
    nombre = app.opciones.get("NOMBRE_CANAL", "TELE VIEJA")
    return Lista(nombre, [
        Item("Canal Retro", lambda app: app.canal(), icono="tele"),
        Item("Videos", ir(lambda: Explorador("Videos", config.CARPETA_VIDEOS, config.EXT_VIDEO,
                                             "video", "")), icono="play"),
        Item("Juegos", ir(ListaSistemas), icono="joystick"),
        Item("Historietas", ir(lambda: Explorador("Historietas", config.CARPETA_HISTORIETAS,
                                                  config.EXT_HISTORIETA, "historieta", "")),
             icono="libro"),
        Item("Radio", ir(lambda: Explorador("Radio", config.CARPETA_RADIO, config.EXT_AUDIO,
                                            "radio", "")), icono="nota"),
        Item("Copiar desde pendrive", copiar_pendrive, icono="usb"),
        Item("Opciones", lambda app: app.poner(opciones), icono="engranaje"),
        Item("Apagar", lambda app: app.poner(Confirmar("¿Apagar la tele vieja?",
                                                       lambda a: a.sistema("poweroff"))),
             icono="apagar"),
    ], ayuda="A: elegir")


def copiar_pendrive(app):
    script = os.path.join(config.BIN_DIR, "importar-usb.sh")

    def trabajo():
        r = subprocess.run(["sudo", "-n", script], capture_output=True, text=True)
        lineas = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        return r.returncode, "\n".join(lineas[-4:])

    def terminar(app, resultado, error):
        if error:
            app.poner(Mensaje("No se pudo copiar", str(error)))
            return
        rc, texto = resultado
        app.poner(Mensaje("¡Listo!" if rc == 0 else "Ojo", texto or "Terminó."))

    app.poner(Espera("Copiar desde pendrive", "Copiando... no saques el pendrive", trabajo, terminar))


def main():
    pygame.display.init()
    pygame.font.init()
    pygame.joystick.init()
    app = App()
    codigo = app.correr()
    pygame.quit()
    sys.exit(codigo)


if __name__ == "__main__":
    main()
