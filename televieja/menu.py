"""TeleVieja OS: el menú que aparece al prender la netbook."""
import array
import os
import subprocess
import sys
import time

os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from . import config, remoto, reproducir, ui  # noqa: E402
from . import mando as mando_mod  # noqa: E402
from .mando import Mando  # noqa: E402
from .pantallas import (Calibrar, Confirmar, ControlCelular, Descargas, Espera, Explorador,  # noqa: E402
                        Item, Lista,
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
        try:  # perfiles de joystick para RetroArch (también actualiza instalaciones viejas)
            mando_mod.escribir_config_retroarch()
        except OSError:
            pass
        self.sonido = Sonido(config.opcion_si(self.opciones, "SONIDOS_MENU"))
        self.pila = []
        self.sucio = True
        self.ultimo_minuto = ""
        self.corriendo = True
        self.codigo_salida = 0
        self.aviso = ""
        self.aviso_hasta = 0.0
        self.discos = self._ids_discos()
        self.proximo_chequeo = 0.0
        self.servidor_celular = None
        if config.opcion_si(self.opciones, "CONTROL_CELULAR"):
            try:
                puerto = int(self.opciones.get("PUERTO_CELULAR", "8080"))
            except ValueError:
                puerto = 8080
            self.servidor_celular = remoto.iniciar(puerto)
            if self.servidor_celular:
                from . import descargas
                remoto.gestor = descargas.Gestor()
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
        elif destino in ((720, 480), (720, 576)):
            # Resoluciones de tele (por HDMI): la tele las muestra en 4:3, así que se estira todo.
            self.pantalla.blit(pygame.transform.scale(self.lienzo, destino), (0, 0))
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

    # --- discos USB ------------------------------------------------------------
    @staticmethod
    def _ids_discos():
        return {d["id"]: d["nombre"] for d in config.discos_externos()}

    def revisar_discos(self):
        """Cada 2 segundos se fija si enchufaron o sacaron un disco USB."""
        ahora = time.monotonic()
        if ahora < self.proximo_chequeo:
            return
        self.proximo_chequeo = ahora + 2
        discos = self._ids_discos()
        if discos == self.discos:
            return
        nuevos = [n for i, n in discos.items() if i not in self.discos]
        if nuevos:
            self.avisar("Disco conectado: " + ", ".join(nuevos))
        else:
            self.avisar("Se desconectó un disco")
        self.discos = discos
        self.actual.al_volver(self)
        self.sucio = True

    def avisar(self, texto, segundos=3.0):
        self.aviso = texto
        self.aviso_hasta = time.monotonic() + segundos
        self.sucio = True

    def _dibujar_aviso(self, sup):
        f = self.fuentes
        texto = ui.recortar(f.chica, self.aviso, ANCHO - 2 * MARGEN_X - 40, f.puntos)
        img = f.chica.render(texto, True, ui.BLANCO)
        r = img.get_rect(midbottom=(ANCHO // 2, ALTO - MARGEN_Y - 36)).inflate(28, 14)
        ui.caja(sup, r, borde=ui.VERDE)
        sup.blit(img, img.get_rect(center=r.center))

    # --- programas externos ----------------------------------------------------
    def lanzar(self, orden, control=None, nombre_log="ultimo", combo_salida=False,
               control_remoto=None, cwd=None, env=None, cortar=None):
        """Corre mpv, RetroArch o Wine y espera. Mientras tanto escucha el joystick y el celular.

        control: qué hacer con cada botón. control_remoto: lo mismo pero solo para los
        botones del celular (en los juegos el joystick ya lo maneja el juego).
        cortar: cómo cerrarlo de golpe (por defecto, terminar el proceso).
        """
        self.sonido.apagar()
        inicio = time.monotonic()
        try:
            with open(reproducir.ruta_log(nombre_log), "w") as log:
                proc = subprocess.Popen(orden, stdout=log, stderr=subprocess.STDOUT,
                                        cwd=cwd, env=env)
        except OSError as e:
            self.sonido.prender()
            return None, 0.0, str(e)
        combo_desde = None
        pidio_salir = None
        intentos = 0
        while proc.poll() is None:
            for ev in pygame.event.get():
                if ev.type == remoto.EVENTO:
                    botones, manejar = [ev.boton], control_remoto or control
                else:
                    botones, manejar = self.mando.traducir(ev), control
                for boton in botones:
                    if boton in ("vol+", "vol-", "mute"):
                        reproducir.mpv_comando("show-text", self.volumen(boton))
                    elif manejar and manejar(boton):
                        pidio_salir = pidio_salir or time.monotonic()
            if combo_salida and self.mando.esta_apretado("select") and self.mando.esta_apretado("start"):
                combo_desde = combo_desde or time.monotonic()
                if time.monotonic() - combo_desde > 2.5:
                    (cortar or proc.terminate)()
                    combo_desde = time.monotonic() + 5  # no repetir enseguida
            else:
                combo_desde = None
            if pidio_salir and time.monotonic() - pidio_salir > 4:
                intentos += 1
                if intentos > 1:
                    proc.kill()  # no hubo caso: a la fuerza
                else:
                    (cortar or proc.terminate)()
                pidio_salir = time.monotonic()
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
        rc, duracion, error = self.lanzar(orden, None, "juego", combo_salida=True,
                                          control_remoto=reproducir.control_juego_remoto)
        if rc is None:
            self.poner(Mensaje("Falta RetroArch", error))
        elif rc != 0 and duracion < 5:
            self.poner(Mensaje("No se pudo abrir el juego", self._ultimas_lineas("juego")))

    def jugar_pc(self, carpeta):
        """Juego viejo de Windows con Wine (la primera vez prepara Wine)."""
        from . import wine
        exe, candidatos = wine.exe_de_juego(carpeta)
        nombre = os.path.basename(carpeta)
        if not exe:
            if candidatos:
                lista = ", ".join(os.path.basename(c) for c in candidatos[:6])
                texto = ("Hay varios programas: %s. Creá en la carpeta del juego un archivo "
                         "jugar.txt con el nombre del que abre el juego." % lista)
            else:
                texto = "No encontré ningún .exe en la carpeta de %s." % nombre
            self.poner(Mensaje("¿Qué programa abro?", texto))
            return
        if not wine.prefijo_listo():
            def listo(app, resultado, error):
                if error:
                    app.poner(Mensaje("No se pudo preparar Wine", str(error)))
                else:
                    app._abrir_pc(exe)
            self.poner(Espera("Juegos de PC", "Preparando Wine (solo la primera vez)...",
                              wine.preparar, listo))
            return
        self._abrir_pc(exe)

    def _abrir_pc(self, exe):
        from . import wine
        ancho, alto = self.pantalla.get_size()
        escritorio = config.opcion_si(self.opciones, "PC_ESCRITORIO_VIRTUAL")
        orden = wine.orden(exe, ancho, alto, escritorio)

        def control_pc(boton):  # "Salir" o "Inicio" en el celu cierran el juego
            if boton in ("b", "inicio"):
                wine.cortar()
                return True
            return False

        rc, duracion, error = self.lanzar(orden, None, "pc", combo_salida=True,
                                          control_remoto=control_pc, cwd=os.path.dirname(exe),
                                          env=wine.entorno(), cortar=wine.cortar)
        if rc is None:
            self.poner(Mensaje("Falta Wine", error))
        elif rc != 0 and duracion < 5:
            self.poner(Mensaje("No se pudo abrir el juego", self._ultimas_lineas("pc")))

    def canal(self):
        lista = reproducir.armar_canal(self.opciones)
        if not lista:
            self.poner(Mensaje("El canal está vacío",
                               "Poné videos en TeleVieja/Canal/Programas (y publicidades viejas "
                               "en TeleVieja/Canal/Tandas)."))
            return
        self.lanzar_mpv(reproducir.orden_canal(self.opciones, lista), reproducir.control_canal)

    def volumen(self, boton):
        """Volumen de la netbook (sirve para todo: menú, videos y juegos)."""
        cambio = {"vol+": "5%+", "vol-": "5%-", "mute": "toggle"}[boton]
        try:
            subprocess.run(["amixer", "-q", "sset", "Master", cambio], timeout=3)
            salida = subprocess.run(["amixer", "get", "Master"], capture_output=True,
                                    text=True, timeout=3).stdout
        except (OSError, subprocess.TimeoutExpired):
            return "Volumen"
        if "[off]" in salida:
            return "Sin sonido"
        import re
        m = re.search(r"\[(\d+)%\]", salida)
        return "Volumen: %s%%" % m.group(1) if m else "Volumen"

    def ir_al_inicio(self):
        while len(self.pila) > 1:
            self.pila.pop().cerrar(self)
        self.actual.al_volver(self)
        self.sonido.tocar("volver")
        self.sucio = True

    def boton_global(self, boton):
        """Botones que hacen lo mismo en cualquier pantalla. Devuelve True si lo usó."""
        if boton in ("vol+", "vol-", "mute"):
            self.avisar(self.volumen(boton), 1.5)
            return True
        if boton == "inicio":
            self.ir_al_inicio()
            return True
        return False

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
            self.vuelta(reloj.tick(FPS) / 1000.0)
        return self.codigo_salida

    def vuelta(self, dt):
        """Una vuelta del bucle: leer botones, actualizar y dibujar."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.corriendo = False
            if ev.type in (pygame.VIDEOEXPOSE, pygame.WINDOWEXPOSED if hasattr(pygame, "WINDOWEXPOSED") else -1):
                self.sucio = True
            if ev.type == remoto.EVENTO:
                botones = [ev.boton]
                if self.actual.crudo:
                    continue
            else:
                botones = self.mando.traducir(ev)
            if ev.type == pygame.JOYDEVICEADDED:
                self._joystick_nuevo(ev.device_index)
            if self.actual.crudo:
                self.actual.evento(self, ev)
                continue
            for b in botones:
                if not self.boton_global(b):
                    self.actual.accion(self, b)
        if not self.actual.crudo:
            for b in self.mando.repeticiones():
                self.actual.accion(self, b)
        self.actual.actualizar(self, dt)
        self.revisar_discos()
        if remoto.gestor:
            novedades = remoto.gestor.tomar_novedades()
            if novedades:
                self.avisar(novedades[-1], 5.0)
                self.actual.al_volver(self)  # que aparezca lo nuevo en la lista
        if self.aviso and time.monotonic() > self.aviso_hasta:
            self.aviso = ""
            self.sucio = True
        minuto = time.strftime("%H:%M")
        if minuto != self.ultimo_minuto:
            self.ultimo_minuto = minuto
            self.sucio = True
        if self.sucio:
            self.sucio = False
            self._dibujar(self.actual, self.lienzo)
            if self.aviso:
                self._dibujar_aviso(self.lienzo)
            self.mostrar()

    def _joystick_nuevo(self, indice):
        try:
            j = pygame.joystick.Joystick(indice)
        except pygame.error:
            return
        # Cada modelo de joystick nuevo se configura una vez (RetroArch necesita sus botones).
        if not self.mando.esta_calibrado(j) and not isinstance(self.actual, Calibrar):
            self.poner(Calibrar("Encontré un joystick nuevo: vamos a configurarlo."))


def menu_principal(app):
    def ir(pantalla_fabrica):
        return lambda app: app.poner(pantalla_fabrica())

    opciones = Lista("Opciones", [
        Item("Configurar joystick", ir(lambda: Calibrar()), icono="joystick"),
        Item("Control desde el celular", ir(ControlCelular), icono="celular"),
        Item("Descargas", ir(Descargas), icono="bajar"),
        Item("Cambiar pantalla (tele / netbook)", lambda app: app.cambiar_pantalla(), icono="tele"),
        Item("Reiniciar", lambda app: app.poner(Confirmar("¿Reiniciar?", lambda a: a.sistema("reboot"))),
             icono="flecha"),
        Item("Salir a la terminal", lambda app: app.salir_a_terminal(), icono="engranaje"),
    ])
    nombre = app.opciones.get("NOMBRE_CANAL", "TELE VIEJA")
    return Lista(nombre, [
        Item("Canal Retro", lambda app: app.canal(), icono="tele"),
        Item("Videos", ir(lambda: Explorador("video", "Videos", config.EXT_VIDEO)), icono="play"),
        Item("Juegos", ir(ListaSistemas), icono="joystick"),
        Item("Historietas", ir(lambda: Explorador("historieta", "Historietas", config.EXT_HISTORIETA)),
             icono="libro"),
        Item("Radio", ir(lambda: Explorador("radio", "Radio", config.EXT_AUDIO)), icono="nota"),
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
