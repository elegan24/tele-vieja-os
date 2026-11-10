#!/usr/bin/python3
"""Redes WiFi para TeleVieja (lo llama el menú con sudo, sin contraseña).

Uso:
  wifi.py listar            redes cercanas, en JSON
  wifi.py conectar NOMBRE   la contraseña llega por la entrada estándar (no a la vista)
  wifi.py estado            a qué red está conectada

Las redes quedan guardadas en NetworkManager: la próxima vez se conecta sola.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

INTERFACES = "/etc/network/interfaces"


def nmcli(*args, entrada=None, tiempo=60):
    try:
        return subprocess.run(["nmcli"] + list(args), capture_output=True, text=True,
                              input=entrada, timeout=tiempo)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(args, 1, "", str(e))


def placas():
    return sorted(os.path.basename(p) for p in glob.glob("/sys/class/net/wl*"))


def partir_terse(linea):
    """nmcli -t separa con ":" y escribe "\\:" cuando el ":" es parte del texto."""
    campos, actual, i = [], "", 0
    while i < len(linea):
        c = linea[i]
        if c == "\\" and i + 1 < len(linea):
            actual += linea[i + 1]
            i += 2
            continue
        if c == ":":
            campos.append(actual)
            actual = ""
        else:
            actual += c
        i += 1
    campos.append(actual)
    return campos


def sacar_de_interfaces(texto, placa):
    """Comenta en /etc/network/interfaces todo lo de `placa` (para que la maneje NetworkManager)."""
    salida, dentro = [], False
    for linea in texto.splitlines():
        tokens = linea.split()
        es_cabecera = bool(tokens) and tokens[0] in ("auto", "allow-hotplug", "iface", "mapping")
        if es_cabecera:
            dentro = tokens[0] in ("iface", "mapping") and len(tokens) > 1 and tokens[1] == placa
            if placa in tokens[1:] and tokens[0] in ("auto", "allow-hotplug"):
                restantes = [t for t in tokens[1:] if t != placa]
                salida.append("# (TeleVieja: ahora lo maneja NetworkManager) " + linea)
                if restantes:
                    salida.append(tokens[0] + " " + " ".join(restantes))
                continue
        if dentro and (es_cabecera or linea[:1] in (" ", "\t")):
            salida.append("# (TeleVieja: ahora lo maneja NetworkManager) " + linea)
            continue
        if not linea.strip():
            dentro = False
        salida.append(linea)
    return "\n".join(salida) + "\n"


def liberar():
    """Si el WiFi lo maneja la configuración vieja de Debian, se lo pasa a NetworkManager."""
    estados = {}
    for linea in nmcli("-t", "-f", "DEVICE,STATE", "device").stdout.splitlines():
        campos = partir_terse(linea)
        if len(campos) >= 2:
            estados[campos[0]] = campos[1]
    for placa in placas():
        if estados.get(placa) != "unmanaged":
            continue
        try:
            with open(INTERFACES, encoding="utf-8") as f:
                texto = f.read()
            nuevo = sacar_de_interfaces(texto, placa)
            if nuevo != texto:
                if not os.path.exists(INTERFACES + ".televieja-antes"):
                    shutil.copy(INTERFACES, INTERFACES + ".televieja-antes")
                with open(INTERFACES, "w", encoding="utf-8") as f:
                    f.write(nuevo)
        except OSError:
            pass
        subprocess.run(["ifdown", "--force", placa], capture_output=True, timeout=30)
        nmcli("device", "set", placa, "managed", "yes")
        time.sleep(3)


def listar():
    liberar()
    nmcli("device", "wifi", "rescan", tiempo=20)
    time.sleep(2)
    salida = nmcli("-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list").stdout
    redes = {}
    for linea in salida.splitlines():
        campos = partir_terse(linea)
        if len(campos) < 4 or not campos[1]:
            continue  # redes ocultas (sin nombre): no se muestran
        en_uso, nombre, senal, seguridad = campos[0] == "*", campos[1], campos[2], campos[3]
        try:
            senal = int(senal)
        except ValueError:
            senal = 0
        vieja = redes.get(nombre)
        if not vieja or senal > vieja["senal"] or en_uso:
            redes[nombre] = {"nombre": nombre, "senal": max(senal, vieja["senal"] if vieja else 0),
                             "segura": seguridad not in ("", "--"),
                             "conectada": en_uso or bool(vieja and vieja["conectada"])}
    lista = sorted(redes.values(), key=lambda r: (not r["conectada"], -r["senal"]))
    print(json.dumps(lista, ensure_ascii=False))


def conectar(nombre):
    clave = sys.stdin.readline().rstrip("\n")
    liberar()
    guardada = nmcli("-t", "-f", "NAME", "connection", "show").stdout.splitlines()
    if not clave and nombre in [partir_terse(l)[0] for l in guardada]:
        r = nmcli("connection", "up", "id", nombre, tiempo=90)   # una red que ya conocía
    else:
        args = ["device", "wifi", "connect", nombre]
        if clave:
            args += ["password", clave]
        r = nmcli(*args, tiempo=90)
    ok = r.returncode == 0
    mensaje = (r.stdout + r.stderr).strip().splitlines()
    mensaje = mensaje[-1] if mensaje else ""
    if not ok and re.search(r"secrets|password|802-11-wireless-security|Secrets", mensaje):
        mensaje = "La contraseña no es correcta."
    print(json.dumps({"ok": ok, "mensaje": mensaje}, ensure_ascii=False))


def estado():
    for linea in nmcli("-t", "-f", "ACTIVE,SSID", "device", "wifi").stdout.splitlines():
        campos = partir_terse(linea)
        if len(campos) >= 2 and campos[0] == "yes":
            print(json.dumps({"conectada": campos[1]}, ensure_ascii=False))
            return
    print(json.dumps({"conectada": None}))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    orden = sys.argv[1]
    if orden == "listar":
        listar()
    elif orden == "conectar" and len(sys.argv) == 3:
        conectar(sys.argv[2])
    elif orden == "estado":
        estado()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
