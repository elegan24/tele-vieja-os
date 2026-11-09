"""Joysticks y teclado: todo se traduce a nombres de botón tipo Super Nintendo.

Nombres: up, down, left, right, a, b, x, y, l, r, select, start.
"""
import json
import os
import re
import time

import pygame

from . import config

DIRECCIONES = ("up", "down", "left", "right")
HAT_DIR = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
UMBRAL_EJE = 0.55

# Si el joystick no está configurado, probamos con lo más común.
POR_DEFECTO = {
    "up": ["hat", 0, "up"], "down": ["hat", 0, "down"],
    "left": ["hat", 0, "left"], "right": ["hat", 0, "right"],
    "a": ["btn", 1], "b": ["btn", 2], "x": ["btn", 0], "y": ["btn", 3],
    "l": ["btn", 4], "r": ["btn", 5], "select": ["btn", 8], "start": ["btn", 9],
}

TECLAS = {
    pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    pygame.K_RETURN: "a", pygame.K_KP_ENTER: "a", pygame.K_SPACE: "a",
    pygame.K_ESCAPE: "b", pygame.K_BACKSPACE: "b",
    pygame.K_PAGEUP: "l", pygame.K_PAGEDOWN: "r",
    pygame.K_TAB: "select", pygame.K_F1: "start",
}
# Controles remotos USB ("air mouse" de los TV Box): mandan estas teclas especiales.
for _nombre, _boton in {
    "K_AC_BACK": "b", "K_AC_HOME": "inicio", "K_HOME": "inicio", "K_MENU": "select",
    "K_AUDIOPLAY": "start", "K_AUDIOSTOP": "b", "K_AUDIONEXT": "r", "K_AUDIOPREV": "l",
    "K_VOLUMEUP": "vol+", "K_VOLUMEDOWN": "vol-", "K_MUTE": "mute", "K_AUDIOMUTE": "mute",
}.items():
    if hasattr(pygame, _nombre):
        TECLAS[getattr(pygame, _nombre)] = _boton

REPETIR_DESPUES = 0.35
REPETIR_CADA = 0.08


def cargar_calibraciones():
    try:
        with open(config.ARCHIVO_JOYSTICK, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_calibracion(guid, nombre, mapa):
    datos = cargar_calibraciones()
    datos[guid] = {"nombre": nombre, "mapa": mapa}
    datos["_ultimo"] = guid
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    with open(config.ARCHIVO_JOYSTICK, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)
    escribir_config_retroarch()


def _valor_ra(enlace):
    """Convierte un enlace a la sintaxis de RetroArch: ("btn"|"axis", valor)."""
    tipo = enlace[0]
    if tipo == "btn":
        return "btn", str(enlace[1])
    if tipo == "hat":
        return "btn", "h%d%s" % (enlace[1], enlace[2])
    if tipo == "axis":
        return "axis", ("+" if enlace[2] > 0 else "-") + str(enlace[1])
    return None, None


def vid_pid(guid):
    """Saca el fabricante y modelo USB del GUID de SDL (para que RetroArch reconozca el joystick)."""
    if not isinstance(guid, str) or len(guid) != 32:
        return None, None
    try:
        vid = int(guid[10:12] + guid[8:10], 16)
        pid = int(guid[18:20] + guid[16:18], 16)
    except ValueError:
        return None, None
    return (vid, pid) if vid else (None, None)


# Palancas analógicas: "stick" = izquierda, "cstick" = derecha (cámara / botones C de la N64).
ANALOGICOS = {"stick_x", "stick_y", "cstick_x", "cstick_y"}
PALANCAS_RA = {"stick_x": "l_x", "stick_y": "l_y", "cstick_x": "r_x", "cstick_y": "r_y"}

NOMBRES_RA = ("up", "down", "left", "right", "a", "b", "x", "y", "l", "r", "l2", "r2",
              "select", "start")
ATAJOS_RA = {"select": "enable_hotkey", "start": "exit_emulator",
             "r": "save_state", "l": "load_state", "x": "menu_toggle"}


def perfil_retroarch(nombre, vid, pid, mapa):
    """Un perfil de "autoconfig": RetroArch lo usa solo para ESE joystick.

    Así cada joystick (el de verdad, el del celu, otro de un amigo) tiene sus
    propios números de botón y se pueden usar varios a la vez.
    """
    lineas = ['input_driver = "udev"', 'input_device = "%s"' % nombre.replace('"', "'")]
    if vid:
        lineas += ['input_vendor_id = "%d"' % vid, 'input_product_id = "%d"' % pid]
    for n in NOMBRES_RA:
        enlace = mapa.get(n)
        if enlace:
            tipo, valor = _valor_ra(enlace)
            lineas.append('input_%s_%s = "%s"' % (n, tipo, valor))
    for n, atajo in ATAJOS_RA.items():
        enlace = mapa.get(n)
        if enlace:
            tipo, valor = _valor_ra(enlace)
            lineas.append('input_%s_%s = "%s"' % (atajo, tipo, valor))
    for n, ra in PALANCAS_RA.items():
        enlace = mapa.get(n)
        if enlace and enlace[0] == "axis":
            eje, signo = enlace[1], enlace[2]
            mas, menos = ("+", "-") if signo > 0 else ("-", "+")
            lineas.append('input_%s_plus_axis = "%s%d"' % (ra, mas, eje))
            lineas.append('input_%s_minus_axis = "%s%d"' % (ra, menos, eje))
    return "\n".join(lineas) + "\n"


def escribir_config_retroarch():
    """Escribe un perfil por joystick configurado (más el del celu) y la config base."""
    from .joystick_virtual import MAPA_MENU, NOMBRE, PRODUCTO, VENDOR
    carpeta = os.path.join(config.AUTOCONFIG_DIR, "udev")
    os.makedirs(carpeta, exist_ok=True)
    for viejo in os.listdir(carpeta):
        if viejo.startswith("televieja-"):
            os.remove(os.path.join(carpeta, viejo))
    perfiles = {"televieja-celular.cfg": perfil_retroarch(NOMBRE, VENDOR, PRODUCTO, MAPA_MENU)}
    for guid, datos in cargar_calibraciones().items():
        if guid.startswith("_") or not isinstance(datos, dict) or "mapa" not in datos:
            continue
        vid, pid = vid_pid(guid)
        archivo = "televieja-%s.cfg" % (re.sub(r"[^A-Za-z0-9]", "", guid)[:32] or "joystick")
        perfiles[archivo] = perfil_retroarch(datos.get("nombre", "Joystick"), vid, pid, datos["mapa"])
    for archivo, texto in perfiles.items():
        with open(os.path.join(carpeta, archivo), "w", encoding="utf-8") as f:
            f.write(texto)
    with open(config.ARCHIVO_RA_JOYSTICK, "w", encoding="utf-8") as f:
        f.write("# Generado por TeleVieja OS: los botones de cada joystick están en %s\n"
                % config.AUTOCONFIG_DIR)
        f.write('input_joypad_driver = "udev"\n')
        f.write('input_autodetect_enable = "true"\n')
        f.write('joypad_autoconfig_dir = "%s"\n' % config.AUTOCONFIG_DIR)


class Mando:
    def __init__(self):
        self.joysticks = {}          # instance_id -> Joystick
        self.calibraciones = cargar_calibraciones()
        self.apretados = {}          # nombre -> momento en que se apretó (para repetir)
        self.proxima_repeticion = {}
        self.estado_ejes = {}        # (instance_id, eje) -> -1/0/1
        self.estado_hats = {}        # (instance_id, hat) -> (x, y)

    # --- conexión ---------------------------------------------------------
    def recargar(self):
        self.calibraciones = cargar_calibraciones()

    def conectar(self, indice):
        try:
            j = pygame.joystick.Joystick(indice)
            j.init()
            self.joysticks[j.get_instance_id()] = j
            return j
        except pygame.error:
            return None

    def desconectar(self, instance_id):
        self.joysticks.pop(instance_id, None)

    def hay_joystick(self):
        return bool(self.joysticks)

    @staticmethod
    def es_celular(j):
        from .joystick_virtual import NOMBRE
        try:
            return j.get_name() == NOMBRE
        except pygame.error:
            return False

    def esta_calibrado(self, j):
        return self.es_celular(j) or self._guid(j) in self.calibraciones

    @staticmethod
    def _guid(j):
        try:
            return j.get_guid()
        except AttributeError:
            return j.get_name()

    def mapa(self, j):
        if self.es_celular(j):
            from .joystick_virtual import MAPA_MENU
            return MAPA_MENU
        datos = self.calibraciones.get(self._guid(j))
        if datos:
            return datos["mapa"]
        ultimo = self.calibraciones.get("_ultimo")
        if ultimo and ultimo in self.calibraciones:
            return self.calibraciones[ultimo]["mapa"]
        return POR_DEFECTO

    # --- traducción de eventos ---------------------------------------------
    def traducir(self, ev):
        """Devuelve la lista de botones que se acaban de apretar con este evento."""
        if ev.type == pygame.KEYDOWN:
            if ev.key in TECLAS:
                return [TECLAS[ev.key]]
            if ev.unicode and ev.unicode.isalnum():
                return ["letra:" + ev.unicode.upper()]
            return []
        if ev.type == pygame.JOYDEVICEADDED:
            self.conectar(ev.device_index)
            return []
        if ev.type == pygame.JOYDEVICEREMOVED:
            self.desconectar(ev.instance_id)
            return []
        j = self.joysticks.get(getattr(ev, "instance_id", None))
        if j is None:
            return []
        mapa = self.mapa(j)
        nuevos = []
        if ev.type == pygame.JOYBUTTONDOWN:
            for nombre, enlace in mapa.items():
                if enlace and enlace[0] == "btn" and enlace[1] == ev.button:
                    nuevos.append(nombre)
        elif ev.type == pygame.JOYHATMOTION:
            clave = (ev.instance_id, ev.hat)
            antes = self.estado_hats.get(clave, (0, 0))
            self.estado_hats[clave] = ev.value
            for d in DIRECCIONES:
                if self._hat_tiene(ev.value, d) and not self._hat_tiene(antes, d):
                    enlace = mapa.get(d)
                    if (enlace and enlace[0] == "hat" and enlace[1] == ev.hat) or \
                            (ev.hat == 0 and not self._dir_es_eje(mapa, d)):
                        nuevos.append(d)
        elif ev.type == pygame.JOYAXISMOTION:
            clave = (ev.instance_id, ev.axis)
            antes = self.estado_ejes.get(clave, 0)
            ahora = 1 if ev.value > UMBRAL_EJE else (-1 if ev.value < -UMBRAL_EJE else 0)
            self.estado_ejes[clave] = ahora
            if ahora != 0 and ahora != antes:
                for nombre, enlace in mapa.items():
                    if nombre in ANALOGICOS:
                        continue  # las palancas son para los juegos, no botones
                    if enlace and enlace[0] == "axis" and enlace[1] == ev.axis and enlace[2] == ahora:
                        nuevos.append(nombre)
                # Palanca analógica: ejes 0 y 1 siempre mueven el menú.
                if not nuevos and ev.axis in (0, 1):
                    nuevos.append({(0, -1): "left", (0, 1): "right",
                                   (1, -1): "up", (1, 1): "down"}[(ev.axis, ahora)])
        ahora_t = time.monotonic()
        for n in nuevos:
            if n in DIRECCIONES:
                self.apretados[n] = ahora_t
                self.proxima_repeticion[n] = ahora_t + REPETIR_DESPUES
        return nuevos

    @staticmethod
    def _hat_tiene(valor, direccion):
        dx, dy = HAT_DIR[direccion]
        return (dx and valor[0] == dx) or (dy and valor[1] == dy)

    @staticmethod
    def _dir_es_eje(mapa, d):
        enlace = mapa.get(d)
        return bool(enlace) and enlace[0] == "axis"

    # --- estado actual -----------------------------------------------------
    def esta_apretado(self, nombre):
        for j in self.joysticks.values():
            enlace = self.mapa(j).get(nombre)
            try:
                if self._enlace_activo(j, enlace):
                    return True
                if nombre in DIRECCIONES:
                    if j.get_numhats() > 0 and self._hat_tiene(j.get_hat(0), nombre):
                        return True
                    if j.get_numaxes() >= 2:
                        eje, signo = {"left": (0, -1), "right": (0, 1),
                                      "up": (1, -1), "down": (1, 1)}[nombre]
                        if j.get_axis(eje) * signo > UMBRAL_EJE:
                            return True
            except pygame.error:
                continue
        return False

    @staticmethod
    def _enlace_activo(j, enlace):
        if not enlace:
            return False
        if enlace[0] == "btn":
            return enlace[1] < j.get_numbuttons() and j.get_button(enlace[1])
        if enlace[0] == "hat":
            return enlace[1] < j.get_numhats() and Mando._hat_tiene(j.get_hat(enlace[1]), enlace[2])
        if enlace[0] == "axis":
            return enlace[1] < j.get_numaxes() and j.get_axis(enlace[1]) * enlace[2] > UMBRAL_EJE
        return False

    def repeticiones(self):
        """Direcciones mantenidas que tienen que repetirse (para bajar rápido por las listas)."""
        ahora = time.monotonic()
        salida = []
        for d in list(self.apretados):
            if not self.esta_apretado(d):
                del self.apretados[d]
                continue
            if ahora >= self.proxima_repeticion[d]:
                salida.append(d)
                self.proxima_repeticion[d] = ahora + REPETIR_CADA
        return salida

    def soltar_todo(self):
        self.apretados.clear()
        self.estado_ejes.clear()
        self.estado_hats.clear()
