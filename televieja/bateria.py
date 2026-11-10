"""La batería de la netbook (lo que dice Linux en /sys/class/power_supply)."""
import os

BASE = "/sys/class/power_supply"


def _leer(ruta, archivo):
    try:
        with open(os.path.join(ruta, archivo)) as f:
            return f.read().strip()
    except OSError:
        return ""


def leer(base=None):
    """{"porcentaje": 85, "cargando": False, "enchufada": False} o None si no hay batería."""
    base = base or BASE
    try:
        nombres = sorted(os.listdir(base))
    except OSError:
        return None
    enchufada = any(_leer(os.path.join(base, n), "type") == "Mains" and
                    _leer(os.path.join(base, n), "online") == "1" for n in nombres)
    for nombre in nombres:
        ruta = os.path.join(base, nombre)
        if _leer(ruta, "type") != "Battery" or _leer(ruta, "present") == "0":
            continue
        porcentaje = _leer(ruta, "capacity")
        if not porcentaje.isdigit():  # algunas baterías solo dicen cuánto tienen y cuánto entra
            for ahora, lleno in (("energy_now", "energy_full"), ("charge_now", "charge_full")):
                a, l = _leer(ruta, ahora), _leer(ruta, lleno)
                if a.isdigit() and l.isdigit() and int(l) > 0:
                    porcentaje = str(int(a) * 100 // int(l))
                    break
        if not porcentaje.isdigit():
            continue
        estado = _leer(ruta, "status")
        return {"porcentaje": max(0, min(100, int(porcentaje))),
                "cargando": estado == "Charging",
                "enchufada": enchufada or estado in ("Charging", "Full", "Not charging")}
    return None
