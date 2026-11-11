"""Cómo está conectada la netbook: por cable, por WiFi (con su señal) o sin conexión."""
import os

BASE = "/sys/class/net"
WIRELESS = "/proc/net/wireless"
IGNORAR = ("lo", "veth", "docker", "virbr", "br-", "tun", "tap")


def _leer(*partes):
    try:
        with open(os.path.join(*partes)) as f:
            return f.read().strip()
    except OSError:
        return ""


def senal_wifi(placa, wireless=None):
    """Calidad de la señal en % (de /proc/net/wireless), o None."""
    try:
        with open(wireless or WIRELESS) as f:
            for linea in f:
                if linea.strip().startswith(placa + ":"):
                    calidad = float(linea.split()[2].rstrip("."))
                    return max(0, min(100, int(calidad * 100 / 70)))
    except (OSError, ValueError, IndexError):
        pass
    return None


def estado(base=None, wireless=None):
    """{"tipo": "cable" | "wifi" | None, "placa": "enp5s0", "senal": 80}"""
    base = base or BASE
    try:
        placas = sorted(os.listdir(base))
    except OSError:
        return {"tipo": None, "placa": None, "senal": None}
    cable = wifi = None
    for placa in placas:
        if placa.startswith(IGNORAR):
            continue
        operstate = _leer(base, placa, "operstate")
        conectada = operstate == "up" or (operstate == "unknown" and _leer(base, placa, "carrier") == "1")
        if not conectada:
            continue
        if placa.startswith("wl") or os.path.isdir(os.path.join(base, placa, "wireless")):
            wifi = wifi or placa
        else:
            cable = cable or placa   # enp5s0 (cable) o usb0 (anclaje USB del celu)
    if cable:  # si hay cable, se usa el cable
        return {"tipo": "cable", "placa": cable, "senal": None}
    if wifi:
        return {"tipo": "wifi", "placa": wifi, "senal": senal_wifi(wifi, wireless)}
    return {"tipo": None, "placa": None, "senal": None}
