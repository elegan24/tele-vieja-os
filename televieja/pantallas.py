"""Las pantallas del menú. Cada una recibe botones ("up", "a", "b"...) y se dibuja."""
import math
import os
import queue
import re
import threading
import time

import pygame

from . import config, historietas, reproducir, ui
from .ui import ANCHO, ALTO, MARGEN_X, MARGEN_Y


class Pantalla:
    titulo = ""
    ayuda = "A: elegir    B: volver"
    crudo = False            # True: recibe los eventos del joystick sin traducir
    sin_marco = False        # True: dibuja toda la pantalla ella sola

    def accion(self, app, boton):
        pass

    def evento(self, app, ev):
        pass

    def actualizar(self, app, dt):
        pass

    def dibujar(self, app, sup):
        pass

    def al_volver(self, app):
        pass

    def cerrar(self, app):
        """Se llama cuando la pantalla se saca de golpe (botón Inicio)."""
        pass

    def info(self):
        return ""


class Item:
    def __init__(self, texto, accion=None, icono=None, extra="", apagado=False, dato=None):
        self.texto = texto
        self.accion = accion
        self.icono = icono
        self.extra = extra
        self.apagado = apagado
        self.dato = dato


# --- lista con cursor --------------------------------------------------------
class Lista(Pantalla):
    ALTO_FILA = 40
    ARRIBA = MARGEN_Y + 58
    ABAJO = ALTO - MARGEN_Y - 34

    def __init__(self, titulo, items=None, ayuda=None):
        self.titulo = titulo
        self.items = items or []
        self.sel = 0
        self.primero = 0
        self.letra = None
        self.letra_hasta = 0
        if ayuda:
            self.ayuda = ayuda

    @property
    def visibles(self):
        return max(1, (self.ABAJO - self.ARRIBA) // self.ALTO_FILA)

    def info(self):
        if len(self.items) > self.visibles:
            return "%d/%d" % (self.sel + 1, len(self.items))
        return ""

    def ajustar(self):
        self.sel = max(0, min(self.sel, len(self.items) - 1))
        if self.sel < self.primero:
            self.primero = self.sel
        elif self.sel >= self.primero + self.visibles:
            self.primero = self.sel - self.visibles + 1

    def mover(self, app, a):
        if not self.items:
            return
        nuevo = max(0, min(len(self.items) - 1, a))
        if nuevo != self.sel:
            self.sel = nuevo
            app.sonido.tocar("mover")
        if self.sel < self.primero:
            self.primero = self.sel
        elif self.sel >= self.primero + self.visibles:
            self.primero = self.sel - self.visibles + 1
        app.sucio = True

    def _inicial(self, item):
        t = item.texto.lstrip("¡¿\"'([ ").upper()
        return t[:1] if t else ""

    def saltar_letra(self, app, sentido):
        """L/R: saltan a la letra anterior/siguiente (para listas con miles de juegos)."""
        if not self.items:
            return
        actual = self._inicial(self.items[self.sel])
        i = self.sel
        while 0 <= i + sentido < len(self.items):
            i += sentido
            if self._inicial(self.items[i]) != actual:
                break
        if sentido < 0:  # ir al primero de esa letra
            letra = self._inicial(self.items[i])
            while i > 0 and self._inicial(self.items[i - 1]) == letra:
                i -= 1
        self.mover(app, i)
        self._mostrar_letra()

    def ir_a_letra(self, app, letra):
        n = len(self.items)
        for k in range(1, n + 1):
            i = (self.sel + k) % n
            if self._inicial(self.items[i]) == letra:
                self.mover(app, i)
                self._mostrar_letra()
                return

    def _mostrar_letra(self):
        if self.items:
            self.letra = self._inicial(self.items[self.sel])
            self.letra_hasta = time.monotonic() + 0.8

    def accion(self, app, boton):
        if boton == "up":
            self.mover(app, self.sel - 1 if self.sel > 0 else len(self.items) - 1)
        elif boton == "down":
            self.mover(app, self.sel + 1 if self.sel < len(self.items) - 1 else 0)
        elif boton == "left":
            self.mover(app, self.sel - self.visibles)
        elif boton == "right":
            self.mover(app, self.sel + self.visibles)
        elif boton == "l":
            self.saltar_letra(app, -1)
        elif boton == "r":
            self.saltar_letra(app, 1)
        elif boton.startswith("letra:"):
            self.ir_a_letra(app, boton[6:])
        elif boton in ("a", "start"):
            if self.items:
                item = self.items[self.sel]
                if item.accion:
                    app.sonido.tocar("elegir")
                    item.accion(app)
        elif boton == "b":
            self.volver(app)

    def volver(self, app):
        app.sonido.tocar("volver")
        app.sacar()

    def actualizar(self, app, dt):
        if self.letra and time.monotonic() > self.letra_hasta:
            self.letra = None
            app.sucio = True

    def dibujar(self, app, sup):
        f = app.fuentes
        for fila in range(self.visibles):
            i = self.primero + fila
            if i >= len(self.items):
                break
            item = self.items[i]
            y = self.ARRIBA + fila * self.ALTO_FILA
            elegido = i == self.sel
            if elegido:
                pygame.draw.rect(sup, ui.AMARILLO, (MARGEN_X - 6, y, ANCHO - 2 * MARGEN_X + 12,
                                                    self.ALTO_FILA - 4), border_radius=8)
            color = ui.OSCURO if elegido else (ui.GRIS_OSCURO if item.apagado else ui.BLANCO)
            x = MARGEN_X + 4
            if item.icono:
                ui.icono(sup, item.icono, x, y + 7, ui.OSCURO if elegido else
                         (ui.GRIS_OSCURO if item.apagado else ui.AMARILLO))
                x += 34
            ancho_extra = 0
            if item.extra:
                img = f.chica.render(item.extra, True, ui.OSCURO if elegido else ui.GRIS)
                ancho_extra = img.get_width() + 12
                sup.blit(img, img.get_rect(midright=(ANCHO - MARGEN_X, y + self.ALTO_FILA // 2 - 2)))
            disponible = (ANCHO - MARGEN_X) - x - ancho_extra - 6
            texto = ui.recortar(f.item, item.texto, disponible, f.puntos)
            ui.escribir(sup, f.item, texto, color, (x, y + 4), sombra=not elegido)
        # barrita de desplazamiento
        if len(self.items) > self.visibles:
            alto_total = self.ABAJO - self.ARRIBA
            alto_barra = max(16, alto_total * self.visibles // len(self.items))
            y = self.ARRIBA + (alto_total - alto_barra) * self.primero // max(1, len(self.items) - self.visibles)
            pygame.draw.rect(sup, ui.GRIS_OSCURO, (ANCHO - MARGEN_X + 14, self.ARRIBA, 5, alto_total),
                             border_radius=2)
            pygame.draw.rect(sup, ui.AMARILLO, (ANCHO - MARGEN_X + 14, y, 5, alto_barra), border_radius=2)
        if self.letra:
            r = pygame.Rect(0, 0, 120, 120)
            r.center = (ANCHO // 2, ALTO // 2)
            ui.caja(sup, r)
            ui.escribir(sup, f.grande, self.letra, ui.AMARILLO, r.center, "center")


# --- avisos ------------------------------------------------------------------
class Mensaje(Pantalla):
    ayuda = "A: aceptar"

    def __init__(self, titulo, texto, al_cerrar=None):
        self.titulo_caja = titulo
        self.texto = texto
        self.al_cerrar = al_cerrar

    def accion(self, app, boton):
        if boton in ("a", "b", "start"):
            app.sacar()
            if self.al_cerrar:
                self.al_cerrar(app)

    def dibujar(self, app, sup):
        app.dibujar_debajo(self, sup)
        f = app.fuentes
        lineas = ui.partir_lineas(f.chica, self.texto, ANCHO - 2 * MARGEN_X - 50)
        alto = 70 + len(lineas) * 24
        r = pygame.Rect(MARGEN_X, 0, ANCHO - 2 * MARGEN_X, alto)
        r.centery = ALTO // 2
        ui.caja(sup, r)
        ui.escribir(sup, f.item, self.titulo_caja, ui.AMARILLO, (r.centerx, r.y + 14), "midtop")
        for i, linea in enumerate(lineas):
            ui.escribir(sup, f.chica, linea, ui.BLANCO, (r.centerx, r.y + 54 + i * 24), "midtop")


class Confirmar(Pantalla):
    ayuda = "Izq/Der: elegir    A: aceptar"

    def __init__(self, pregunta, si):
        self.pregunta = pregunta
        self.si = si
        self.opcion = 1  # empieza en "No"

    def accion(self, app, boton):
        if boton in ("left", "right", "up", "down"):
            self.opcion = 1 - self.opcion
            app.sonido.tocar("mover")
            app.sucio = True
        elif boton in ("a", "start"):
            app.sacar()
            if self.opcion == 0:
                self.si(app)
        elif boton == "b":
            app.sacar()

    def dibujar(self, app, sup):
        app.dibujar_debajo(self, sup)
        f = app.fuentes
        r = pygame.Rect(0, 0, 420, 150)
        r.center = (ANCHO // 2, ALTO // 2)
        ui.caja(sup, r)
        ui.escribir(sup, f.item, self.pregunta, ui.BLANCO, (r.centerx, r.y + 22), "midtop")
        for i, texto in enumerate(("Sí", "No")):
            b = pygame.Rect(0, 0, 120, 44)
            b.center = (r.centerx + (-80 if i == 0 else 80), r.y + 105)
            if i == self.opcion:
                pygame.draw.rect(sup, ui.AMARILLO, b, border_radius=8)
            ui.escribir(sup, f.item, texto, ui.OSCURO if i == self.opcion else ui.BLANCO,
                        b.center, "center", sombra=i != self.opcion)


class Espera(Pantalla):
    """Hace un trabajo lento en otro hilo mostrando una ruedita."""
    ayuda = ""

    def __init__(self, titulo, texto, trabajo, al_terminar):
        self.titulo = titulo
        self.texto = texto
        self.trabajo = trabajo
        self.al_terminar = al_terminar
        self.resultado = None
        self.error = None
        self.listo = False
        self.t0 = time.monotonic()
        threading.Thread(target=self._correr, daemon=True).start()

    def _correr(self):
        try:
            self.resultado = self.trabajo()
        except Exception as e:  # noqa: BLE001 - se muestra en pantalla
            self.error = e
        self.listo = True

    def actualizar(self, app, dt):
        app.sucio = True
        if self.listo:
            app.sacar()
            self.al_terminar(app, self.resultado, self.error)

    def dibujar(self, app, sup):
        f = app.fuentes
        ui.escribir(sup, f.item, self.texto, ui.BLANCO, (ANCHO // 2, ALTO // 2 - 50), "center")
        t = time.monotonic() - self.t0
        for i in range(8):
            ang = i / 8 * 6.283 + t * 4
            x = ANCHO // 2 + int(26 * math.cos(ang))
            y = ALTO // 2 + 20 + int(26 * math.sin(ang))
            brillo = 80 + int(175 * (i / 7))
            pygame.draw.circle(sup, (brillo, brillo * 212 // 255, 60 * brillo // 255), (x, y), 5)


# --- explorador de carpetas (videos, radio, historietas) ---------------------
class Explorador(Lista):
    """Recorre carpetas. En la primera pantalla suma los discos USB conectados."""
    TITULOS = {"video": "Videos", "radio": "Radio", "historieta": "Historietas"}

    def __init__(self, tipo, subcarpeta, extensiones):
        super().__init__(self.TITULOS[tipo])
        self.tipo = tipo          # "video", "radio" o "historieta"
        self.subcarpeta = subcarpeta
        self.raiz = os.path.join(config.RAIZ, subcarpeta)
        self.carpeta = self.raiz
        self.ext = extensiones
        self.historial = []       # (carpeta, título, elegido) de donde venimos
        self.recuerdo = {}
        self.cargar()

    def _carpetas_de_discos(self):
        """Por cada disco USB: su TeleVieja/<subcarpeta> o, si no tiene, el disco entero."""
        salida = []
        for d in config.discos_externos():
            if d["raiz"]:
                carpeta = os.path.join(d["raiz"], self.subcarpeta)
                if not os.path.isdir(carpeta):
                    continue
            else:
                carpeta = d["punto"]
            salida.append((d["nombre"], carpeta))
        return salida

    def cargar(self):
        self.items = []
        carpetas, archivos = [], []
        try:
            nombres = sorted(os.listdir(self.carpeta), key=config.clave_natural)
        except OSError:
            nombres = []
        for n in nombres:
            if n.startswith("."):
                continue
            ruta = os.path.join(self.carpeta, n)
            if os.path.isdir(ruta):
                carpetas.append(ruta)
            elif n.lower().endswith(self.ext):
                archivos.append(ruta)
        self.archivos = archivos
        icono_archivo = {"video": "play", "radio": "nota", "historieta": "libro"}[self.tipo]
        if self.tipo in ("video", "radio") and len(archivos) > 1:
            self.items.append(Item("Mezclar todo", lambda app: self.reproducir(app, None),
                                   icono="mezclar"))
        if not self.historial:
            for nombre, c in self._carpetas_de_discos():
                self.items.append(Item("Disco: " + nombre,
                                       lambda app, c=c, n=nombre: self.entrar(app, c, n),
                                       icono="disco"))
        for c in carpetas:
            nombre = os.path.basename(c)
            if self.tipo == "historieta" and historietas.es_carpeta_historieta(c):
                self.items.append(Item(nombre, lambda app, c=c: abrir_historieta(app, c),
                                       icono="libro"))
            else:
                self.items.append(Item(nombre, lambda app, c=c: self.entrar(app, c), icono="carpeta"))
        progreso = historietas.leer_progreso() if self.tipo == "historieta" else {}
        for i, a in enumerate(archivos):
            extra = ""
            if a in progreso:
                extra = "pág. %d" % (progreso[a].get("pagina", 0) + 1)
            if self.tipo == "historieta":
                accion = (lambda app, a=a: abrir_historieta(app, a))
            else:
                accion = (lambda app, i=i: self.reproducir(app, i))
            self.items.append(Item(config.nombre_lindo(os.path.basename(a)), accion,
                                   icono=icono_archivo, extra=extra))
        if not self.items:
            self.items.append(Item("(vacío)", apagado=True))
            if self.historial:
                self.ayuda = "B: volver"
            else:
                self.ayuda = "Cargá cosas en TeleVieja/" + self.subcarpeta
        else:
            self.ayuda = "A: elegir    B: volver    L/R: letra"
        self.sel = min(self.recuerdo.get(self.carpeta, 0), len(self.items) - 1)
        self.primero = 0
        self.ajustar()

    def entrar(self, app, carpeta, titulo=None):
        self.historial.append((self.carpeta, self.titulo, self.sel))
        self.carpeta = carpeta
        self.titulo = titulo or os.path.basename(carpeta)
        self.cargar()
        app.sucio = True

    def volver(self, app):
        if not self.historial:
            return super().volver(app)
        app.sonido.tocar("volver")
        self.recuerdo[self.carpeta] = self.sel
        self.carpeta, self.titulo, sel = self.historial.pop()
        self.recuerdo[self.carpeta] = sel
        self.cargar()
        app.sucio = True

    def al_volver(self, app):
        if not os.path.isdir(self.carpeta):  # desenchufaron el disco
            self.carpeta, self.titulo = self.raiz, self.TITULOS[self.tipo]
            self.historial.clear()
        anterior = self.sel
        self.cargar()  # por si cambió algo (página guardada, disco nuevo)
        self.sel = anterior
        self.ajustar()

    def reproducir(self, app, indice):
        import random
        if indice is None:
            lista = list(self.archivos)
            random.shuffle(lista)
        else:
            lista = self.archivos[indice:]  # sigue con los capítulos siguientes
        if self.tipo == "radio":
            app.lanzar_mpv(reproducir.orden_radio(lista), reproducir.control_videos)
        else:
            app.lanzar_mpv(reproducir.orden_videos(lista), reproducir.control_videos)


# --- juegos -----------------------------------------------------------------
def limpiar_nombre_rom(nombre):
    base = os.path.splitext(nombre)[0]
    sin_corchetes = re.sub(r"\s*\[[^\]]*\]", "", base).strip()
    sin_tags = re.sub(r"\s*\([^)]*\)", "", sin_corchetes).strip()
    return sin_tags or sin_corchetes or base, sin_corchetes or base


class ListaSistemas(Lista):
    def __init__(self):
        super().__init__("Juegos")
        self.cargar()

    def cargar(self):
        self.items = []
        opciones = config.leer_opciones()
        for s in config.SISTEMAS:
            if not config.sistema_visible(s, opciones):
                continue
            if s.get("pc"):
                from . import wine
                roms = wine.juegos_pc()
                core = "wine" if wine.hay_wine() else None
            else:
                roms = [r for r in config.listar_en_todas(("Juegos", s["carpeta"]), s["ext"])
                        if os.path.basename(r).lower() not in s.get("excluir", ())]
                if s.get("discos"):
                    roms = config.filtrar_discos(roms)
                core = config.buscar_core(s["cores"])
            if not core:
                extra = "falta Wine" if s.get("pc") else "falta emulador"
            elif roms:
                extra = str(len(roms))
            else:
                extra = "vacío"
            self.items.append(Item(s["nombre"], lambda app, s=s, roms=roms, core=core:
                                   self.elegir(app, s, roms, core),
                                   icono="joystick", extra=extra, apagado=not (roms and core)))

    def al_volver(self, app):
        anterior = self.sel
        self.cargar()  # por si enchufaron o sacaron un disco
        self.sel = anterior
        self.ajustar()

    def elegir(self, app, sistema, roms, core):
        if not core:
            app.poner(Mensaje("Falta el emulador",
                              "No encontré el emulador para %s. Volvé a correr instalar.sh "
                              "con internet." % sistema["nombre"]))
        elif not roms and sistema.get("pc"):
            app.poner(Mensaje("No hay juegos de PC",
                              "Poné cada juego (ya instalado) en su propia carpeta adentro de "
                              "TeleVieja/Juegos/PC. Por ejemplo: TeleVieja/Juegos/PC/Sonic R"))
        elif not roms:
            app.poner(Mensaje("No hay juegos",
                              "Poné los juegos de %s en la carpeta TeleVieja/Juegos/%s"
                              % (sistema["nombre"], sistema["carpeta"])))
        else:
            app.poner(ListaJuegos(sistema, roms, core))


class ListaJuegos(Lista):
    def __init__(self, sistema, roms, core):
        super().__init__(sistema["nombre"], ayuda="A: jugar  B: volver  L/R: letra")
        self.core = core
        if sistema.get("nombres") == "arcade":
            tabla = config.nombres_arcade()
            nombres = []
            for r in roms:
                corto = os.path.splitext(os.path.basename(r))[0]
                # ".x" para que no se coma lo que viene después de un punto ("Vs. Capcom")
                nombres.append(limpiar_nombre_rom(tabla.get(corto.lower(), corto) + ".x"))
        elif sistema.get("pc"):
            nombres = [(os.path.basename(r), os.path.basename(r)) for r in roms]
        else:
            nombres = [limpiar_nombre_rom(os.path.basename(r)) for r in roms]
        cuenta = {}
        for corto, _ in nombres:
            cuenta[corto] = cuenta.get(corto, 0) + 1
        pares = []
        for rom, (corto, medio) in zip(roms, nombres):
            pares.append((corto if cuenta[corto] == 1 else medio, rom))
        pares.sort(key=lambda p: config.clave_natural(p[0]))
        if sistema.get("pc"):
            self.items = [Item(n, lambda app, rom=rom: app.jugar_pc(rom)) for n, rom in pares]
        else:
            self.items = [Item(n, lambda app, rom=rom: app.jugar(self.core, rom)) for n, rom in pares]


# --- lector de historietas ----------------------------------------------------
def abrir_historieta(app, ruta):
    nombre = config.nombre_lindo(os.path.basename(ruta))

    def terminar(app, libro, error):
        if error or libro is None:
            app.poner(Mensaje("No se pudo abrir", "%s\n%s" % (nombre, error or "")))
        else:
            app.poner(Lector(ruta, libro))

    app.poner(Espera(nombre, "Abriendo historieta...", lambda: historietas.abrir(ruta), terminar))


class Lector(Pantalla):
    sin_marco = True
    MODOS = (("pagina", "Página entera"), ("ancho", "Ancho"), ("lupa", "Lupa"))

    def __init__(self, ruta, libro):
        self.ruta = ruta
        self.libro = libro
        self.total = libro.cantidad()
        guardado = historietas.leer_progreso().get(ruta, {})
        self.pagina = max(0, min(guardado.get("pagina", 0), self.total - 1))
        self.manga = bool(guardado.get("manga", False))
        self.modo = 1
        self.originales = {}
        self.errores = {}
        self.pedidos = set()
        self.cola = queue.Queue()
        self.escalada = None
        self.clave_escalada = None
        self.x = self.y = 0.0
        self.x_obj = self.y_obj = 0.0
        self.ir_abajo = False
        self.aviso = ""
        self.aviso_hasta = 0
        self.vivo = True
        threading.Thread(target=self._trabajador, daemon=True).start()
        self._avisar(app=None)
        self._pedir_cercanas()

    # carga de páginas en segundo plano
    def _trabajador(self):
        while self.vivo:
            try:
                i = self.cola.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self.originales[i] = self.libro.cargar(i)
            except Exception as e:  # noqa: BLE001
                self.errores[i] = str(e) or "Error"

    def _pedir(self, i):
        if 0 <= i < self.total and i not in self.pedidos:
            self.pedidos.add(i)
            self.cola.put(i)

    def _pedir_cercanas(self):
        for i in (self.pagina, self.pagina + 1, self.pagina - 1, self.pagina + 2):
            self._pedir(i)
        for i in list(self.originales):
            if abs(i - self.pagina) > 2:
                self.originales.pop(i, None)
                self.pedidos.discard(i)

    def _avisar(self, app, texto=None):
        self.aviso = texto or "Página %d de %d  -  %s%s" % (
            self.pagina + 1, self.total, self.MODOS[self.modo][1], "  -  Manga" if self.manga else "")
        self.aviso_hasta = time.monotonic() + 2.2
        if app:
            app.sucio = True

    # tamaño de la página según el modo
    def _superficie(self):
        original = self.originales.get(self.pagina)
        if original is None:
            return None
        clave = (self.pagina, self.modo, id(original))
        if clave != self.clave_escalada:
            w, h = original.get_size()
            nombre = self.MODOS[self.modo][0]
            if nombre == "pagina":
                escala = min(ANCHO / w, ALTO / h)
            elif nombre == "ancho":
                escala = ANCHO / w
            else:
                escala = ANCHO * 1.6 / w
            tam = (max(1, int(w * escala)), max(1, int(h * escala)))
            self.escalada = pygame.transform.smoothscale(original, tam)
            self.clave_escalada = clave
            if self.ir_abajo:
                self.y = self.y_obj = max(0, tam[1] - ALTO)
                self.ir_abajo = False
            self._limitar()
            self.x = self.x_obj
        return self.escalada

    def _limites(self):
        if self.escalada is None or self.clave_escalada[0] != self.pagina:
            return 0, 0
        w, h = self.escalada.get_size()
        return max(0, w - ANCHO), max(0, h - ALTO)

    def _limitar(self):
        if self.escalada is None or self.clave_escalada[0] != self.pagina:
            return  # la página nueva todavía no cargó
        mx, my = self._limites()
        self.x_obj = max(0, min(mx, self.x_obj))
        self.y_obj = max(0, min(my, self.y_obj))

    def cambiar_pagina(self, app, delta, al_final=False):
        nueva = self.pagina + delta
        if nueva < 0:
            self._avisar(app, "Es la primera página")
            return
        if nueva >= self.total:
            self._avisar(app, "Fin de la historieta")
            return
        self.pagina = nueva
        self.x = self.x_obj = (self._limite_x_manga() if self.manga else 0)
        self.y = self.y_obj = 0
        self.ir_abajo = al_final
        self._pedir_cercanas()
        historietas.guardar_progreso(self.ruta, self.pagina)
        app.sonido.tocar("mover")
        self._avisar(app)

    def _limite_x_manga(self):
        return 10 ** 6  # se ajusta al tamaño real cuando la página está cargada

    def accion(self, app, boton):
        paso_y = ALTO * 0.45
        paso_x = ANCHO * 0.5
        mx, my = self._limites()
        adelante, atras = ("left", "right") if self.manga else ("right", "left")
        if boton == "down":
            if self.y_obj < my - 1:
                self.y_obj = min(my, self.y_obj + paso_y)
            else:
                self.cambiar_pagina(app, 1)
        elif boton == "up":
            if self.y_obj > 1:
                self.y_obj = max(0, self.y_obj - paso_y)
            else:
                self.cambiar_pagina(app, -1, al_final=True)
        elif boton == adelante:
            puede = self.x_obj > 1 if self.manga else self.x_obj < mx - 1
            if mx and puede:
                self.x_obj += -paso_x if self.manga else paso_x
                self._limitar()
            else:
                self.cambiar_pagina(app, 1)
        elif boton == atras:
            puede = self.x_obj < mx - 1 if self.manga else self.x_obj > 1
            if mx and puede:
                self.x_obj += paso_x if self.manga else -paso_x
                self._limitar()
            else:
                self.cambiar_pagina(app, -1)
        elif boton == "r":
            self.cambiar_pagina(app, 1)
        elif boton == "l":
            self.cambiar_pagina(app, -1)
        elif boton == "a":
            proporcion = (self.y_obj / my) if my else 0
            self.modo = (self.modo + 1) % len(self.MODOS)
            self._superficie()
            _, my2 = self._limites()
            self.y = self.y_obj = proporcion * my2
            self.x = self.x_obj = 0
            self._limitar()
            self._avisar(app)
        elif boton in ("x", "select"):
            self.manga = not self.manga
            historietas.guardar_progreso(self.ruta, self.pagina, self.manga)
            self._avisar(app, "Modo manga (de derecha a izquierda)" if self.manga
                         else "Modo normal (de izquierda a derecha)")
        elif boton == "start":
            self._avisar(app)
        elif boton == "b":
            self.cerrar(app)
            app.sonido.tocar("volver")
            app.sacar()
        app.sucio = True

    def cerrar(self, app):
        self.vivo = False
        historietas.guardar_progreso(self.ruta, self.pagina)

    def actualizar(self, app, dt):
        if self.pagina in self.errores:
            self.errores.pop(self.pagina)
            self.pedidos.discard(self.pagina)
            self._avisar(app, "No pude cargar la página %d" % (self.pagina + 1))
        self._limitar()
        k = min(1.0, dt * 12)
        nx = self.x + (self.x_obj - self.x) * k
        ny = self.y + (self.y_obj - self.y) * k
        if abs(nx - self.x_obj) < 0.5:
            nx = self.x_obj
        if abs(ny - self.y_obj) < 0.5:
            ny = self.y_obj
        if (nx, ny) != (self.x, self.y):
            self.x, self.y = nx, ny
            app.sucio = True
        if self.aviso and time.monotonic() > self.aviso_hasta:
            self.aviso = ""
            app.sucio = True
        if self.escalada is None or self.clave_escalada[0] != self.pagina:
            app.sucio = True  # esperando que cargue

    def dibujar(self, app, sup):
        sup.fill((24, 24, 28))
        f = app.fuentes
        pag = self._superficie()
        if pag is None:
            ui.escribir(sup, f.item, "Cargando página %d..." % (self.pagina + 1), ui.BLANCO,
                        (ANCHO // 2, ALTO // 2), "center")
        else:
            w, h = pag.get_size()
            ox = (ANCHO - w) // 2 if w < ANCHO else -int(self.x)
            oy = (ALTO - h) // 2 if h < ALTO else -int(self.y)
            sup.blit(pag, (ox, oy))
            _, my = self._limites()
            if my:  # indicador de dónde estás en la página
                alto = max(20, ALTO * ALTO // h)
                y = int((ALTO - alto) * self.y / my)
                pygame.draw.rect(sup, (0, 0, 0), (ANCHO - 12, 0, 8, ALTO))
                pygame.draw.rect(sup, ui.AMARILLO, (ANCHO - 11, y, 6, alto), border_radius=3)
        if self.aviso:
            img = f.chica.render(self.aviso, True, ui.BLANCO)
            r = img.get_rect(midbottom=(ANCHO // 2, ALTO - MARGEN_Y - 4)).inflate(24, 12)
            ui.caja(sup, r, borde=ui.AMARILLO)
            sup.blit(img, img.get_rect(center=r.center))


# --- configurar joystick ------------------------------------------------------
PASOS_JOYSTICK = [
    ("up", "ARRIBA en la cruz", True),
    ("down", "ABAJO en la cruz", True),
    ("left", "IZQUIERDA en la cruz", True),
    ("right", "DERECHA en la cruz", True),
    ("a", "el botón A (derecha)", True),
    ("b", "el botón B (abajo)", True),
    ("x", "el botón X (arriba)", False),
    ("y", "el botón Y (izquierda)", False),
    ("l", "el gatillo L", False),
    ("r", "el gatillo R", False),
    ("l2", "el gatillo L2 (para PS1)", False),
    ("r2", "el gatillo R2 (para PS1)", False),
    ("select", "SELECT", True),
    ("start", "START", True),
    # Palancas analógicas (para la N64): solo si el joystick las tiene.
    ("stick_x", "la PALANCA izquierda a la DERECHA", False),
    ("stick_y", "la PALANCA izquierda para ABAJO", False),
    ("cstick_x", "la PALANCA derecha a la DERECHA", False),
    ("cstick_y", "la PALANCA derecha para ABAJO", False),
]
ESPERA_OPCIONAL = 6.0
SOLO_EJES = {"stick_x", "stick_y", "cstick_x", "cstick_y"}


class Calibrar(Pantalla):
    crudo = True
    titulo = "Configurar joystick"
    ayuda = "ESC en el teclado: cancelar"

    def __init__(self, intro=""):
        self.intro = intro
        self.paso = 0
        self.mapa = {}
        self.joystick = None     # instance_id del joystick que se está configurando
        self.neutro = False
        self.t_paso = time.monotonic()
        self.reposo = {}
        self.queja = ""
        self.queja_hasta = 0

    def _registrar_reposo(self, app):
        for iid, j in app.mando.joysticks.items():
            for e in range(j.get_numaxes()):
                self.reposo[(iid, e)] = j.get_axis(e)

    def _todo_suelto(self, app):
        for iid, j in app.mando.joysticks.items():
            if self.joystick is not None and iid != self.joystick:
                continue
            try:
                if any(j.get_button(b) for b in range(j.get_numbuttons())):
                    return False
                if any(j.get_hat(h) != (0, 0) for h in range(j.get_numhats())):
                    return False
                for e in range(j.get_numaxes()):
                    if abs(j.get_axis(e) - self.reposo.get((iid, e), 0.0)) > 0.4:
                        return False
            except pygame.error:
                continue
        return True

    def evento(self, app, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            app.sacar()
            return
        if not self.neutro or self.paso >= len(PASOS_JOYSTICK):
            return
        iid = getattr(ev, "instance_id", None)
        if self.joystick is not None and iid != self.joystick:
            return
        enlace = None
        if ev.type == pygame.JOYBUTTONDOWN:
            enlace = ["btn", ev.button]
        elif ev.type == pygame.JOYHATMOTION and ev.value != (0, 0):
            x, y = ev.value
            d = "up" if y == 1 else "down" if y == -1 else "left" if x == -1 else "right"
            enlace = ["hat", ev.hat, d]
        elif ev.type == pygame.JOYAXISMOTION:
            reposo = self.reposo.get((iid, ev.axis), 0.0)
            if abs(ev.value - reposo) > 0.6 and abs(ev.value) > 0.5:
                enlace = ["axis", ev.axis, 1 if ev.value > 0 else -1]
        if enlace is None:
            return
        if PASOS_JOYSTICK[self.paso][0] in SOLO_EJES and enlace[0] != "axis":
            return  # para las palancas solo vale mover una palanca
        if enlace in self.mapa.values():
            self.queja = "Ese ya lo usaste, probá con otro"
            self.queja_hasta = time.monotonic() + 1.5
            app.sucio = True
            return
        if self.joystick is None:
            self.joystick = iid
        self.mapa[PASOS_JOYSTICK[self.paso][0]] = enlace
        app.sonido.tocar("elegir")
        self._siguiente(app)

    def _siguiente(self, app):
        self.paso += 1
        self.neutro = False
        self.t_paso = time.monotonic()
        app.sucio = True
        if self.paso >= len(PASOS_JOYSTICK):
            j = app.mando.joysticks.get(self.joystick)
            if j is not None:
                from .mando import guardar_calibracion
                guid = j.get_guid() if hasattr(j, "get_guid") else j.get_name()
                guardar_calibracion(guid, j.get_name(), self.mapa)
                app.mando.recargar()
            app.sacar()
            app.poner(Mensaje("¡Listo!", "Joystick configurado.\nEn los juegos: SELECT + START "
                                         "para salir, SELECT + R guarda, SELECT + L carga."))

    def actualizar(self, app, dt):
        if not self.reposo:
            self._registrar_reposo(app)
        if not self.neutro and self._todo_suelto(app):
            self.neutro = True
            self.t_paso = time.monotonic()
            app.sucio = True
        if self.paso < len(PASOS_JOYSTICK) and not PASOS_JOYSTICK[self.paso][2] and self.neutro:
            if time.monotonic() - self.t_paso > ESPERA_OPCIONAL:
                self._siguiente(app)
            app.sucio = True
        if self.queja and time.monotonic() > self.queja_hasta:
            self.queja = ""
            app.sucio = True

    def dibujar(self, app, sup):
        f = app.fuentes
        y = MARGEN_Y + 70
        if not app.mando.hay_joystick():
            for linea in ui.partir_lineas(f.item, "Enchufá un joystick USB...", ANCHO - 2 * MARGEN_X):
                ui.escribir(sup, f.item, linea, ui.BLANCO, (ANCHO // 2, y), "midtop")
                y += 34
            return
        if self.intro:
            ui.escribir(sup, f.chica, self.intro, ui.GRIS, (ANCHO // 2, y), "midtop")
        y += 40
        if self.paso < len(PASOS_JOYSTICK):
            nombre, texto, obligatorio = PASOS_JOYSTICK[self.paso]
            ui.escribir(sup, f.item, "Apretá", ui.BLANCO, (ANCHO // 2, y), "midtop")
            ui.escribir(sup, f.titulo, texto, ui.AMARILLO, (ANCHO // 2, y + 40), "midtop")
            if not obligatorio and self.neutro:
                resta = max(0, int(ESPERA_OPCIONAL - (time.monotonic() - self.t_paso)) + 1)
                ui.escribir(sup, f.chica, "Si no lo tenés, esperá %d..." % resta, ui.GRIS,
                            (ANCHO // 2, y + 96), "midtop")
            # puntitos de progreso
            total = len(PASOS_JOYSTICK)
            x0 = ANCHO // 2 - total * 9
            for i in range(total):
                color = ui.AMARILLO if i < self.paso else (ui.BLANCO if i == self.paso else ui.GRIS_OSCURO)
                pygame.draw.circle(sup, color, (x0 + i * 18 + 9, y + 150), 6)
        if self.queja:
            ui.escribir(sup, f.chica, self.queja, ui.ROJO, (ANCHO // 2, y + 180), "midtop")


# --- control desde el celular -------------------------------------------------
class ControlCelular(Pantalla):
    titulo = "Control con el celu"
    ayuda = "B: volver"

    def __init__(self):
        from . import remoto
        self.ip = remoto.direccion_ip()
        self.qr = None
        self.url = None

    def _armar(self, app):
        puerto = app.opciones.get("PUERTO_CELULAR", "8080")
        if self.ip:
            self.url = "http://%s:%s" % (self.ip, puerto)
            try:
                import qrcode
                q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_L)
                q.add_data(self.url)
                q.make(fit=True)
                self.qr = q.get_matrix()
            except ImportError:
                self.qr = None

    def accion(self, app, boton):
        if boton in ("b", "a"):
            app.sonido.tocar("volver")
            app.sacar()

    def dibujar(self, app, sup):
        f = app.fuentes
        if self.url is None:
            self._armar(app)
        y = MARGEN_Y + 64
        if not app.servidor_celular:
            texto = ("El control por celular está apagado o no pudo arrancar. "
                     "Revisá CONTROL_CELULAR en las opciones.")
        elif not self.url:
            texto = ("La netbook no está conectada a ninguna red. "
                     "Conectala al WiFi de tu casa para usar el celu como control.")
        else:
            texto = None
        if texto:
            for linea in ui.partir_lineas(f.chica, texto, ANCHO - 2 * MARGEN_X):
                ui.escribir(sup, f.chica, linea, ui.BLANCO, (ANCHO // 2, y), "midtop")
                y += 26
            return
        ui.escribir(sup, f.chica, "Con el celu en el mismo WiFi, escaneá el código", ui.BLANCO,
                    (ANCHO // 2, y), "midtop")
        ui.escribir(sup, f.chica, "o entrá a esta dirección:", ui.BLANCO, (ANCHO // 2, y + 24), "midtop")
        ui.escribir(sup, f.item, self.url, ui.AMARILLO, (ANCHO // 2, y + 52), "midtop")
        if self.qr:
            n = len(self.qr)
            modulo = max(2, 176 // n)
            lado = n * modulo
            x0 = (ANCHO - lado) // 2
            y0 = y + 96
            pygame.draw.rect(sup, (255, 255, 255), (x0 - 6, y0 - 6, lado + 12, lado + 12))
            for fila, valores in enumerate(self.qr):
                for col, negro in enumerate(valores):
                    if negro:
                        pygame.draw.rect(sup, (0, 0, 0),
                                         (x0 + col * modulo, y0 + fila * modulo, modulo, modulo))
            ui.escribir(sup, f.chica, "Ahí también lo podés usar como joystick", ui.GRIS,
                        (ANCHO // 2, y0 + lado + 14), "midtop")


# --- descargas (se agregan desde el celu) ---------------------------------------
class Descargas(Lista):
    """Muestra cómo van las descargas que se pidieron desde el celu."""
    ESTADOS = {"esperando": "en espera", "bajando": "bajando", "acomodando": "acomodando",
               "listo": "lista", "error": "error", "cancelado": "cancelada"}

    def __init__(self):
        super().__init__("Descargas", ayuda="B: volver   (se agregan desde el celu)")
        self.proxima = 0
        self.cargar()

    def cargar(self):
        from . import remoto
        anterior = self.sel
        self.items = []
        lista = remoto.gestor.lista() if remoto.gestor else []
        for d in lista:
            if d["estado"] == "bajando" and d["total"]:
                extra = "%d/%d %d%%" % (d["archivo"], d["total"], d["porcentaje"])
            elif d["estado"] == "bajando":
                extra = "leyendo lista (%d)" % (d["carpetas_leidas"] + d["archivos_vistos"])
            else:
                extra = self.ESTADOS.get(d["estado"], d["estado"])
            self.items.append(Item(d["nombre"], icono="bajar", extra=extra,
                                   apagado=d["estado"] in ("error", "cancelado")))
        if not self.items:
            self.items.append(Item("No hay descargas. Pegá un link de Drive en la página "
                                   "del celu (Opciones > Control desde el celular).", apagado=True))
        self.sel = anterior
        self.ajustar()

    def actualizar(self, app, dt):
        super().actualizar(app, dt)
        if time.monotonic() > self.proxima:
            self.proxima = time.monotonic() + 1
            self.cargar()
            app.sucio = True

    def al_volver(self, app):
        self.cargar()
