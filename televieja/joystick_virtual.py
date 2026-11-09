"""Joystick virtual: el celular se convierte en un joystick USB "de mentira".

Usa /dev/uinput (módulo del kernel) a través de python3-evdev. Para Linux,
RetroArch y el menú es igual que enchufar un joystick de verdad.
"""
import threading

NOMBRE = "TeleVieja Celular"
VENDOR = 0x1209     # id libre para proyectos abiertos (pid.codes)
PRODUCTO = 0x7656

# Orden de los botones = orden de los códigos de Linux, así el número de cada
# botón es siempre el mismo (lo usan sistema/autoconfig y mando.py).
#   0 BTN_SOUTH (B)  1 BTN_EAST (A)  2 BTN_NORTH (X)  3 BTN_WEST (Y)
#   4 BTN_TL (L)     5 BTN_TR (R)    6 BTN_SELECT     7 BTN_START
BOTONES = ("b", "a", "x", "y", "l", "r", "select", "start")
MAPA_MENU = {
    "up": ["hat", 0, "up"], "down": ["hat", 0, "down"],
    "left": ["hat", 0, "left"], "right": ["hat", 0, "right"],
    "b": ["btn", 0], "a": ["btn", 1], "x": ["btn", 2], "y": ["btn", 3],
    "l": ["btn", 4], "r": ["btn", 5], "select": ["btn", 6], "start": ["btn", 7],
}


class ErrorJoystick(Exception):
    pass


class JoystickVirtual:
    def __init__(self):
        try:
            from evdev import AbsInfo, UInput
            from evdev import ecodes as e
        except ImportError as err:
            raise ErrorJoystick("Falta python3-evdev") from err
        self.e = e
        self.codigos = {
            "b": e.BTN_SOUTH, "a": e.BTN_EAST, "x": e.BTN_NORTH, "y": e.BTN_WEST,
            "l": e.BTN_TL, "r": e.BTN_TR, "select": e.BTN_SELECT, "start": e.BTN_START,
        }
        hat = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)
        eje = AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)
        capacidades = {
            e.EV_KEY: sorted(self.codigos.values()),
            # Ejes X/Y quietos en el centro: ayudan a que todos lo reconozcan como joystick.
            e.EV_ABS: [(e.ABS_X, eje), (e.ABS_Y, eje), (e.ABS_HAT0X, hat), (e.ABS_HAT0Y, hat)],
        }
        try:
            self.ui = UInput(capacidades, name=NOMBRE, vendor=VENDOR, product=PRODUCTO,
                             version=1, bustype=e.BUS_USB)
        except (OSError, Exception) as err:  # noqa: BLE001 - uinput puede fallar de muchas formas
            raise ErrorJoystick("No se pudo crear el joystick (¿falta /dev/uinput?)") from err
        self.apretados = set()
        self.lock = threading.Lock()

    def _hat(self):
        x = (1 if "right" in self.apretados else 0) - (1 if "left" in self.apretados else 0)
        y = (1 if "down" in self.apretados else 0) - (1 if "up" in self.apretados else 0)
        self.ui.write(self.e.EV_ABS, self.e.ABS_HAT0X, x)
        self.ui.write(self.e.EV_ABS, self.e.ABS_HAT0Y, y)

    def boton(self, nombre, apretado):
        with self.lock:
            if apretado:
                self.apretados.add(nombre)
            else:
                self.apretados.discard(nombre)
            if nombre in ("up", "down", "left", "right"):
                self._hat()
            elif nombre in self.codigos:
                self.ui.write(self.e.EV_KEY, self.codigos[nombre], 1 if apretado else 0)
            else:
                return
            self.ui.syn()

    def cerrar(self):
        with self.lock:
            try:
                for nombre in list(self.apretados):
                    if nombre in self.codigos:
                        self.ui.write(self.e.EV_KEY, self.codigos[nombre], 0)
                self.apretados.clear()
                self._hat()
                self.ui.syn()
            finally:
                self.ui.close()
