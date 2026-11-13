#!/usr/bin/env python3
"""Auriculares Bluetooth para Frecuencia 99 (lo llama el menú con sudo, sin contraseña).

Uso:
  bluetooth.py buscar          busca equipos cerca (unos 12 segundos)
  bluetooth.py conectar MAC    empareja, confía y conecta
  bluetooth.py desconectar MAC
  bluetooth.py olvidar MAC

Siempre termina con una línea JSON para el menú.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

MAC = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x01|\x02")
SEGUNDOS_BUSQUEDA = 12


def responder(datos):
    print(json.dumps(datos, ensure_ascii=False))
    sys.exit(0)


def correr(*args, timeout=10):
    try:
        r = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def preparar():
    """Prende el Bluetooth. Devuelve False si la netbook no tiene (ni adaptador USB)."""
    correr("rfkill", "unblock", "bluetooth")
    correr("systemctl", "start", "bluetooth", timeout=20)
    correr("systemctl", "start", "bluealsa", timeout=20)
    for _ in range(5):
        if "Controller" in correr("bluetoothctl", "list"):
            correr("bluetoothctl", "power", "on")
            return True
        time.sleep(1)
    return False


class Sesion:
    """bluetoothctl abierto, para mandarle órdenes y esperar respuestas."""

    def __init__(self):
        self.p = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, errors="replace")
        self.lineas = queue.Queue()
        threading.Thread(target=self._leer, daemon=True).start()
        self.enviar("agent NoInputNoOutput")
        self.enviar("default-agent")
        self.enviar("power on")

    def _leer(self):
        for linea in self.p.stdout:
            self.lineas.put(ANSI.sub("", linea).strip())

    def enviar(self, orden):
        try:
            self.p.stdin.write(orden + "\n")
            self.p.stdin.flush()
        except OSError:
            pass

    def esperar(self, buenas, malas, segundos):
        """Espera una línea con alguna de las frases. Devuelve True, False o None (tiempo)."""
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            try:
                linea = self.lineas.get(timeout=0.5)
            except queue.Empty:
                continue
            if any(b in linea for b in buenas):
                return True
            if any(m in linea for m in malas):
                return False
        return None

    def cerrar(self):
        self.enviar("quit")
        try:
            self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.p.kill()


def info(mac):
    datos = {"mac": mac, "nombre": mac, "audio": False, "emparejado": False, "conectado": False}
    for linea in correr("bluetoothctl", "info", mac).splitlines():
        clave, _, valor = linea.strip().partition(": ")
        if clave == "Alias" or (clave == "Name" and datos["nombre"] == mac):
            datos["nombre"] = valor
        elif clave == "Icon":
            datos["audio"] = valor.startswith("audio")
        elif clave == "Paired":
            datos["emparejado"] = valor == "yes"
        elif clave == "Connected":
            datos["conectado"] = valor == "yes"
        elif clave == "UUID" and "Audio Sink" in valor:
            datos["audio"] = True
    return datos


def dispositivos():
    macs = re.findall(r"Device (([0-9A-F]{2}:){5}[0-9A-F]{2})", correr("bluetoothctl", "devices"))
    lista = [info(m[0]) for m in macs]
    # sin nombre (solo la dirección) no sirve para elegir; los de audio primero
    lista = [d for d in lista if not re.match(r"^([0-9A-F]{2}[-:]){5}[0-9A-F]{2}$", d["nombre"])]
    lista.sort(key=lambda d: (not d["conectado"], not d["audio"], d["nombre"].lower()))
    return lista


def buscar():
    if not preparar():
        responder({"adaptador": False, "dispositivos": []})
    s = Sesion()
    s.enviar("scan on")
    time.sleep(SEGUNDOS_BUSQUEDA)
    s.enviar("scan off")
    s.cerrar()
    responder({"adaptador": True, "dispositivos": dispositivos()})


def conectar(mac):
    if not preparar():
        responder({"ok": False, "mensaje": "No hay Bluetooth en la netbook."})
    s = Sesion()
    try:
        if not info(mac)["emparejado"]:
            s.enviar("scan on")  # tiene que estar "a la vista" para emparejar
            s.esperar([mac], [], 8)
            s.enviar("scan off")
            s.enviar("pair " + mac)
            r = s.esperar(["Pairing successful", "AlreadyExists"],
                          ["Failed to pair", "not available"], 30)
            if not r:
                responder({"ok": False, "mensaje": "No se pudo emparejar. Poné el auricular en modo "
                                                   "emparejar (luz titilando) y probá de nuevo."})
        s.enviar("trust " + mac)
        s.esperar(["trust succeeded"], ["Failed"], 5)
        s.enviar("connect " + mac)
        r = s.esperar(["Connection successful"], ["Failed to connect", "not available"], 25)
        if r is None:
            r = info(mac)["conectado"]
        if not r:
            responder({"ok": False, "mensaje": "Se emparejó pero no se pudo conectar. Apagá y prendé "
                                               "el auricular y probá de nuevo."})
        responder({"ok": True, "dispositivo": info(mac)})
    finally:
        s.cerrar()


def main():
    if len(sys.argv) < 2:
        responder({"error": "falta la orden"})
    orden = sys.argv[1]
    if orden == "buscar":
        buscar()
    mac = sys.argv[2].upper() if len(sys.argv) > 2 else ""
    if not MAC.match(mac):
        responder({"ok": False, "mensaje": "Dirección inválida."})
    if orden == "conectar":
        conectar(mac)
    elif orden == "desconectar":
        correr("bluetoothctl", "disconnect", mac, timeout=15)
        responder({"ok": True})
    elif orden == "olvidar":
        correr("bluetoothctl", "remove", mac, timeout=15)
        responder({"ok": True})
    responder({"error": "orden desconocida"})


if __name__ == "__main__":
    main()
