"""Control desde el celular: una página web con botones, servida por la netbook.

Entrás desde el celu (conectado al mismo WiFi) a http://IP-DE-LA-NETBOOK:8080
y cada botón le llega al menú como si fuera el joystick.

En /joystick el celu se convierte en un joystick de verdad (para jugar): los
botones viajan por un WebSocket y joystick_virtual.py los pasa a Linux.
"""
import base64
import hashlib
import json
import re
import socket
import struct
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pygame

EVENTO = pygame.USEREVENT + 7
BOTONES = {"up", "down", "left", "right", "a", "b", "x", "y", "l", "r",
           "select", "start", "inicio", "vol+", "vol-", "mute", "actualizar"}
BOTONES_JOYSTICK = {"up", "down", "left", "right", "a", "b", "x", "y", "l", "r", "l2", "r2",
                    "select", "start"}
GUID_WEBSOCKET = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _crear_joystick():
    from .joystick_virtual import JoystickVirtual
    return JoystickVirtual()


# Se puede reemplazar en las pruebas (acá no siempre hay /dev/uinput).
crear_joystick = _crear_joystick

# El gestor de descargas (descargas.Gestor): lo pone el menú al arrancar.
gestor = None


def direccion_ip():
    """IP de la netbook en la red de la casa (o None si no hay red)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))  # no manda nada: solo elige la placa de red
        ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None
    finally:
        s.close()


class _Manejador(BaseHTTPRequestHandler):
    server_version = "TeleVieja"

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._pagina(PAGINA)
        elif self.path == "/joystick":
            self._pagina(PAGINA_JOYSTICK)
        elif self.path == "/ws":
            self._websocket()
        elif self.path == "/manifest.json":
            self._json(200, MANIFIESTO)
        elif re.match(r"^/icono-(180|192|512)\.png$", self.path):
            datos = ICONOS.get(int(self.path[7:10]))
            if not datos:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(datos)))
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(datos)
        elif self.path == "/descargas":
            self._json(200, {"descargas": gestor.lista() if gestor else [],
                             "disponible": gestor is not None})
        else:
            self.send_error(404)

    def _json(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _pagina(self, html):
        cuerpo = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    # --- WebSocket mínimo (sin librerías) para el joystick ---------------------
    def _websocket(self):
        clave = self.headers.get("Sec-WebSocket-Key")
        if not clave or "websocket" not in self.headers.get("Upgrade", "").lower():
            self.send_error(400)
            return
        acepta = base64.b64encode(hashlib.sha1((clave + GUID_WEBSOCKET).encode()).digest()).decode()
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", acepta)
        self.end_headers()
        self.close_connection = True
        self.connection.settimeout(30)  # la página manda "ping" cada 10 s
        try:
            pad = crear_joystick()
        except Exception as err:  # noqa: BLE001 - se le muestra al usuario en el celu
            self._ws_enviar("error " + str(err))
            self._ws_enviar(b"", 0x8)
            return
        self._ws_enviar("ok")
        try:
            while True:
                op, datos = self._ws_leer()
                if op == 0x8:          # el celu cerró
                    break
                if op == 0x9:          # ping del navegador
                    self._ws_enviar(datos, 0xA)
                    continue
                if op != 0x1:
                    continue
                for linea in datos.decode("utf-8", "replace").splitlines():
                    partes = linea.split()
                    if len(partes) == 2 and partes[0] in ("0", "1") and partes[1] in BOTONES_JOYSTICK:
                        pad.boton(partes[1], partes[0] == "1")
                    elif len(partes) == 3 and partes[0] == "ax":  # palanca: "ax X Y"
                        try:
                            pad.palanca(int(partes[1]), int(partes[2]))
                        except ValueError:
                            pass
        except (OSError, ValueError):
            pass  # se cortó el WiFi, se apagó la pantalla del celu, etc.
        finally:
            pad.cerrar()  # suelta todos los botones

    def _leer(self, n):
        datos = self.rfile.read(n)
        if len(datos) < n:
            raise OSError("conexión cerrada")
        return datos

    def _ws_leer(self):
        b1, b2 = self._leer(2)
        op = b1 & 0x0F
        largo = b2 & 0x7F
        if largo == 126:
            largo = struct.unpack(">H", self._leer(2))[0]
        elif largo == 127:
            largo = struct.unpack(">Q", self._leer(8))[0]
        if largo > 4096:
            raise ValueError("mensaje demasiado largo")
        mascara = self._leer(4) if b2 & 0x80 else b"\0\0\0\0"
        datos = bytearray(self._leer(largo))
        for i in range(largo):
            datos[i] ^= mascara[i % 4]
        return op, bytes(datos)

    def _ws_enviar(self, datos, op=0x1):
        if isinstance(datos, str):
            datos = datos.encode("utf-8")
        if len(datos) < 126:
            cabecera = bytes([0x80 | op, len(datos)])
        else:
            cabecera = bytes([0x80 | op, 126]) + struct.pack(">H", len(datos))
        try:
            self.wfile.write(cabecera + datos)
            self.wfile.flush()
        except OSError:
            pass

    def do_POST(self):
        if self.path == "/descargar":
            self._descargar()
            return
        m = re.match(r"^/descargas/(\d+)/cancelar$", self.path)
        if m:
            ok = bool(gestor) and gestor.cancelar(int(m.group(1)))
            self._json(200 if ok else 404, {"ok": ok})
            return
        boton = self.path[3:] if self.path.startswith("/b/") else ""
        if boton not in BOTONES:
            self.send_error(404)
            return
        try:
            pygame.event.post(pygame.event.Event(EVENTO, boton=boton))
        except pygame.error:
            pass
        self.send_response(204)
        self.end_headers()

    def _descargar(self):
        if gestor is None:
            self._json(503, {"error": "Las descargas no están disponibles."})
            return
        largo = int(self.headers.get("Content-Length") or 0)
        if largo <= 0 or largo > 4096:
            self._json(400, {"error": "Pedido inválido."})
            return
        try:
            url = json.loads(self.rfile.read(largo).decode("utf-8")).get("url", "")
            trabajo = gestor.agregar(url)
        except ValueError as e:
            self._json(400, {"error": str(e)})
            return
        self._json(200, {"ok": True, "id": trabajo.id})

    def log_message(self, *args):
        pass


MANIFIESTO = {
    "name": "TeleVieja", "short_name": "TeleVieja",
    "description": "Control remoto de la TeleVieja",
    "start_url": "/", "scope": "/", "display": "standalone", "orientation": "any",
    "background_color": "#0c1240", "theme_color": "#0c1240",
    "icons": [
        {"src": "/icono-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icono-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
ICONOS = {}


def dibujar_icono(lado):
    """Una tele de tubo con antena y barras de color, sobre el azul de TeleVieja."""
    s = pygame.Surface((lado, lado))
    s.fill((12, 18, 64))
    u = lado / 100.0  # todo en "porcentaje" del ícono

    def r(x, y, w, h):
        return pygame.Rect(int(x * u), int(y * u), max(1, int(w * u)), max(1, int(h * u)))

    pygame.draw.line(s, (236, 236, 236), (int(50 * u), int(30 * u)), (int(34 * u), int(14 * u)), max(2, int(3 * u)))
    pygame.draw.line(s, (236, 236, 236), (int(50 * u), int(30 * u)), (int(66 * u), int(14 * u)), max(2, int(3 * u)))
    pygame.draw.rect(s, (255, 212, 60), r(16, 28, 68, 54), border_radius=int(10 * u))
    pantalla = r(23, 35, 44, 40)
    barras = ((235, 235, 235), (235, 235, 16), (16, 235, 235), (16, 235, 16),
              (235, 16, 235), (235, 16, 16), (16, 16, 235))
    ancho = pantalla.width / len(barras)
    for i, color in enumerate(barras):
        pygame.draw.rect(s, color, (pantalla.x + int(i * ancho), pantalla.y, int(ancho) + 1, pantalla.height))
    pygame.draw.rect(s, (10, 14, 40), pantalla, max(2, int(2 * u)), border_radius=int(5 * u))
    for y in (42, 56):
        pygame.draw.circle(s, (10, 14, 40), (int(75 * u), int(y * u)), max(2, int(4 * u)))
    return s


def _preparar_iconos():
    """Arma los íconos una vez, al arrancar (pygame dibuja; se guardan como PNG)."""
    import os
    import tempfile
    for lado in (180, 192, 512):
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                ruta = f.name
            pygame.image.save(dibujar_icono(lado), ruta)
            with open(ruta, "rb") as f:
                ICONOS[lado] = f.read()
            os.remove(ruta)
        except (pygame.error, OSError):
            pass


def iniciar(puerto):
    """Arranca el servidor en segundo plano. Devuelve el servidor o None si no se pudo."""
    _preparar_iconos()
    try:
        servidor = ThreadingHTTPServer(("0.0.0.0", puerto), _Manejador)
    except OSError:
        return None
    servidor.daemon_threads = True
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<meta name="theme-color" content="#0c1240">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/png" href="/icono-192.png">
<link rel="apple-touch-icon" href="/icono-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="TeleVieja">
<title>TeleVieja</title>
<style>
  :root { --fondo:#0c1240; --boton:#1f2f7a; --borde:#3a4ca8; --amarillo:#ffd43c; --texto:#ececec; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html, body { margin:0; background:var(--fondo); color:var(--texto);
    font-family:system-ui, -apple-system, "DejaVu Sans", sans-serif; user-select:none;
    -webkit-user-select:none; touch-action:manipulation; }
  main { max-width:420px; margin:0 auto; padding:16px 16px 32px; }
  h1 { margin:4px 0 14px; font-size:22px; color:var(--amarillo); display:flex; gap:10px; align-items:center; }
  .franjas { display:grid; gap:3px; }
  .franjas i { display:block; width:24px; height:4px; }
  h2 { font-size:13px; text-transform:uppercase; letter-spacing:.08em; color:#97a3d6; margin:22px 0 8px; }
  button { font:inherit; color:var(--texto); background:var(--boton); border:2px solid var(--borde);
    border-radius:14px; min-height:58px; font-size:18px; font-weight:700; cursor:pointer; }
  button:active, button.apretado { background:var(--amarillo); color:#0c1240; border-color:var(--amarillo); }
  .cruz { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
  .cruz button { min-height:78px; font-size:30px; }
  .cruz .ok { border-radius:50%; aspect-ratio:1; font-size:22px; background:#2c41a0; }
  .fila { display:grid; grid-template-columns:repeat(var(--n,3),1fr); gap:10px; margin-top:10px; }
  .vacio { visibility:hidden; }
  .grande { font-size:28px; }
  a.joystick { display:block; text-align:center; text-decoration:none; color:#0c1240;
    background:var(--amarillo); border-radius:14px; padding:16px; font-weight:800; font-size:18px;
    margin-bottom:18px; }
  #estado { margin-top:20px; font-size:13px; color:#97a3d6; text-align:center; min-height:1em; }
  form.bajar { display:grid; grid-template-columns:1fr auto; gap:10px; }
  form.bajar input { font:inherit; font-size:16px; min-width:0; padding:14px; border-radius:12px;
    border:2px solid var(--borde); background:#0a0f33; color:var(--texto); }
  form.bajar button { min-height:52px; padding:0 18px; }
  .nota { font-size:13px; color:#97a3d6; margin:8px 0 0; line-height:1.4; }
  .descarga { background:#141d55; border:1px solid var(--borde); border-radius:12px; padding:12px;
    margin-top:10px; }
  .descarga .titulo { font-weight:700; overflow-wrap:anywhere; }
  .descarga .detalle { font-size:13px; color:#c7cdee; margin-top:4px; overflow-wrap:anywhere; }
  .descarga .aviso { font-size:12px; color:var(--amarillo); margin-top:4px; }
  .barra { height:8px; background:#0a0f33; border-radius:4px; margin-top:8px; overflow:hidden; }
  .barra i { display:block; height:100%; background:var(--amarillo); width:0; }
  .descarga button { min-height:36px; font-size:14px; padding:0 12px; margin-top:8px; }
</style>
</head>
<body>
<main>
  <h1><span class="franjas"><i style="background:#e6463c"></i><i style="background:#f58c28"></i>
    <i style="background:#ffd43c"></i><i style="background:#5ac86e"></i><i style="background:#5aaaf0"></i></span>
    TeleVieja</h1>

  <a class="joystick" href="/joystick">🎮 Usar el celu como joystick</a>

  <div class="cruz">
    <span class="vacio"></span><button data-b="up" data-repetir aria-label="Arriba">▲</button><span class="vacio"></span>
    <button data-b="left" data-repetir aria-label="Izquierda">◀</button>
    <button data-b="a" class="ok">OK</button>
    <button data-b="right" data-repetir aria-label="Derecha">▶</button>
    <span class="vacio"></span><button data-b="down" data-repetir aria-label="Abajo">▼</button><span class="vacio"></span>
  </div>

  <div class="fila" style="--n:2">
    <button data-b="b">↩ Volver</button>
    <button data-b="inicio">⌂ Inicio</button>
  </div>

  <h2>Videos y radio</h2>
  <div class="fila">
    <button data-b="l" class="grande" aria-label="Anterior">⏮</button>
    <button data-b="start" class="grande" aria-label="Pausa">⏯</button>
    <button data-b="r" class="grande" aria-label="Siguiente">⏭</button>
  </div>
  <div class="fila">
    <button data-b="vol-" data-repetir>🔉 −</button>
    <button data-b="mute">🔇</button>
    <button data-b="vol+" data-repetir>🔊 +</button>
  </div>
  <div class="fila" style="--n:2">
    <button data-b="x">Subtítulos</button>
    <button data-b="y">Idioma</button>
  </div>

  <h2>Juegos</h2>
  <div class="fila">
    <button data-b="l">Cargar</button>
    <button data-b="b">Salir</button>
    <button data-b="r">Guardar</button>
  </div>

  <h2>Descargar de Google Drive</h2>
  <form class="bajar" id="form-bajar">
    <input type="url" id="link" placeholder="Pegá el link acá" autocomplete="off" required>
    <button type="submit">Bajar</button>
  </form>
  <p class="nota">Archivo o carpeta compartidos como "Cualquier persona con el enlace".
    Se baja en la netbook y se acomoda solo: videos, juegos, historietas, radio.</p>
  <p class="nota">También sirven links directos de otros sitios. <b>MediaFire:</b> abrí la página
    del archivo, mantené apretado el botón azul "Download" → "Copiar dirección del enlace" y
    pegá ese link (empieza con https://download...).</p>
  <div id="descargas"></div>

  <h2>Mantenimiento</h2>
  <div class="fila" style="--n:1">
    <button data-b="actualizar">⬇ Actualizar TeleVieja</button>
  </div>
  <p class="nota">La tele te pregunta si querés buscar la última versión; confirmás con el joystick o el control.</p>

  <div id="estado"></div>
</main>
<script>
  const estado = document.getElementById("estado");
  function mandar(boton) {
    fetch("/b/" + boton, { method: "POST" })
      .then(() => { estado.textContent = ""; })
      .catch(() => { estado.textContent = "No llego a la tele. ¿Está prendida y en el mismo WiFi?"; });
    if (navigator.vibrate) navigator.vibrate(12);
  }
  document.querySelectorAll("button[data-b]").forEach((btn) => {
    let espera = null, repetir = null;
    const soltar = () => {
      clearTimeout(espera); clearInterval(repetir); espera = repetir = null;
      btn.classList.remove("apretado");
    };
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      btn.classList.add("apretado");
      mandar(btn.dataset.b);
      if (btn.hasAttribute("data-repetir")) {
        espera = setTimeout(() => { repetir = setInterval(() => mandar(btn.dataset.b), 120); }, 400);
      }
    });
    ["pointerup", "pointerleave", "pointercancel"].forEach((t) => btn.addEventListener(t, soltar));
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
  });

  // --- Descargas ---
  const formBajar = document.getElementById("form-bajar");
  const campoLink = document.getElementById("link");
  const listaDescargas = document.getElementById("descargas");
  const ESTADOS = { esperando: "En espera", bajando: "Bajando", acomodando: "Acomodando",
                    listo: "Listo ✔", error: "Error", cancelado: "Cancelada",
                    reintentar: "Reintenta más tarde" };
  function texto(t) { const s = document.createElement("span"); s.textContent = t; return s.innerHTML; }
  function dibujarDescargas(lista) {
    listaDescargas.innerHTML = lista.map((d) => {
      let detalle = "";
      if (d.estado === "bajando" && d.total) {
        detalle = "Archivo " + d.archivo + " de " + d.total + (d.actual ? " · " + d.actual : "") +
                  (d.porcentaje ? " · " + d.porcentaje + "%" : "");
      } else if (d.estado === "bajando") {
        detalle = d.actual || "Preguntándole a Google qué hay en el link...";
      } else if (d.estado === "reintentar" || d.estado === "esperando") {
        detalle = d.actual || "";
        if (d.total) detalle += (detalle ? " · " : "") + d.archivo + " de " + d.total + " bajados";
      } else if (d.estado === "acomodando") {
        detalle = d.actual || "Repartiendo en las carpetas...";
      } else if (d.estado === "listo") {
        detalle = d.resumen;
      }
      const avance = d.total ? Math.round(((d.archivo - 1) + d.porcentaje / 100) / d.total * 100) : 0;
      return '<div class="descarga"><div class="titulo">' + texto(d.nombre) + " — " +
        texto(ESTADOS[d.estado] || d.estado) + "</div>" +
        (detalle ? '<div class="detalle">' + texto(detalle) + "</div>" : "") +
        (d.mensaje ? '<div class="aviso">' + texto(d.mensaje) + "</div>" : "") +
        d.avisos.map((a) => '<div class="aviso">' + texto(a) + "</div>").join("") +
        (d.estado === "bajando" ? '<div class="barra"><i style="width:' + avance + '%"></i></div>' : "") +
        (d.estado === "esperando" || d.estado === "bajando" || d.estado === "reintentar"
          ? '<button data-cancelar="' + d.id + '">Cancelar</button>' : "") + "</div>";
    }).join("");
  }
  function actualizarDescargas() {
    if (document.hidden) return;
    fetch("/descargas").then((r) => r.json()).then((d) => dibujarDescargas(d.descargas)).catch(() => {});
  }
  formBajar.addEventListener("submit", (e) => {
    e.preventDefault();
    fetch("/descargar", { method: "POST", headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ url: campoLink.value }) })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) { estado.textContent = d.error; return; }
        campoLink.value = ""; estado.textContent = "¡Agregada! Se baja en la netbook.";
        actualizarDescargas();
      })
      .catch(() => { estado.textContent = "No llego a la tele. ¿Está prendida y en el mismo WiFi?"; });
  });
  listaDescargas.addEventListener("click", (e) => {
    const id = e.target.dataset.cancelar;
    if (id) fetch("/descargas/" + id + "/cancelar", { method: "POST" }).then(actualizarDescargas);
  });
  actualizarDescargas();
  setInterval(actualizarDescargas, 2000);
</script>
</body>
</html>
"""


PAGINA_JOYSTICK = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#0c1240">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/png" href="/icono-192.png">
<link rel="apple-touch-icon" href="/icono-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="TeleVieja">
<meta name="mobile-web-app-capable" content="yes">
<title>TeleVieja · Joystick</title>
<style>
  :root { --fondo:#0c1240; --boton:#1f2f7a; --borde:#3a4ca8; --amarillo:#ffd43c; --texto:#ececec;
    --rojo:#e6463c; --azul:#5aaaf0; --verde:#5ac86e; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html, body { margin:0; height:100%; overflow:hidden; background:var(--fondo); color:var(--texto);
    font-family:system-ui, -apple-system, "DejaVu Sans", sans-serif; user-select:none;
    -webkit-user-select:none; touch-action:none; overscroll-behavior:none; }
  #pad { position:fixed; inset:0; display:grid; grid-template-rows:auto 1fr;
    padding:max(10px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right))
            max(10px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left)); }
  .arriba { display:flex; justify-content:space-between; align-items:center; gap:10px; }
  .hombro { width:15vw; max-width:130px; height:13vh; min-height:44px; border-radius:14px 14px 22px 22px; }
  .hombro[data-b$="2"] { opacity:.8; font-size:14px; }
  #estado { font-size:14px; color:#97a3d6; text-align:center; flex:1; }
  #estado a { color:var(--amarillo); }
  .cuerpo { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; }
  button { font:inherit; color:var(--texto); background:var(--boton); border:2px solid var(--borde);
    font-weight:800; padding:0; touch-action:none; }
  button.on, .flecha.on { background:var(--amarillo); color:var(--fondo); border-color:var(--amarillo); }
  #cruz { position:relative; width:min(58vh, 42vw); aspect-ratio:1; justify-self:start; touch-action:none; }
  .flecha { position:absolute; background:var(--boton); border:2px solid var(--borde); border-radius:10px; }
  .f-up { left:33%; top:0; width:34%; height:38%; }
  .f-down { left:33%; bottom:0; width:34%; height:38%; }
  .f-left { top:33%; left:0; width:38%; height:34%; }
  .f-right { top:33%; right:0; width:38%; height:34%; }
  .f-centro { left:31%; top:31%; width:38%; height:38%; border-radius:4px; border-color:var(--boton); }
  #base, #perilla { display:none; position:absolute; border-radius:50%; }
  #base { inset:3%; background:var(--boton); border:2px solid var(--borde); }
  #perilla { width:38%; height:38%; left:31%; top:31%; background:#2c41a0; border:3px solid var(--amarillo); }
  #cruz.palanca .flecha { display:none; }
  #cruz.palanca #base, #cruz.palanca #perilla { display:block; }
  #modo { background:transparent; border-style:dashed; color:#97a3d6; }
  .medio { display:flex; flex-direction:column; align-items:center; gap:14px; }
  .chico { width:22vw; max-width:150px; height:11vh; min-height:38px; border-radius:30px; font-size:13px;
    letter-spacing:.06em; }
  #botones { position:relative; width:min(62vh, 44vw); aspect-ratio:1; justify-self:end; }
  .redondo { position:absolute; width:36%; aspect-ratio:1; border-radius:50%; font-size:min(7vh, 30px); }
  .b-x { left:32%; top:0; border-color:var(--azul); }
  .b-y { left:0; top:32%; border-color:var(--verde); }
  .b-a { right:0; top:32%; border-color:var(--rojo); }
  .b-b { left:32%; bottom:0; border-color:var(--amarillo); }
  #girar { display:none; position:fixed; inset:0; background:var(--fondo); z-index:5;
    align-items:center; justify-content:center; text-align:center; font-size:22px; padding:24px; }
  @media (orientation: portrait) { #girar { display:flex; } }
</style>
</head>
<body>
<div id="girar">Girá el celu para jugar<br>📱 ↻</div>
<div id="pad">
  <div class="arriba">
    <button class="hombro" data-b="l2">L2</button>
    <button class="hombro" data-b="l">L</button>
    <div id="estado">Conectando…</div>
    <button class="hombro" data-b="r">R</button>
    <button class="hombro" data-b="r2">R2</button>
  </div>
  <div class="cuerpo">
    <div id="cruz" aria-label="Cruz de direcciones">
      <div class="flecha f-up" data-d="up"></div><div class="flecha f-down" data-d="down"></div>
      <div class="flecha f-left" data-d="left"></div><div class="flecha f-right" data-d="right"></div>
      <div class="flecha f-centro"></div>
      <div id="base"></div><div id="perilla"></div>
    </div>
    <div class="medio">
      <button class="chico" data-b="select">SELECT</button>
      <button class="chico" data-b="start">START</button>
      <button class="chico" id="modo">Usar palanca</button>
    </div>
    <div id="botones">
      <button class="redondo b-x" data-b="x">X</button>
      <button class="redondo b-y" data-b="y">Y</button>
      <button class="redondo b-a" data-b="a">A</button>
      <button class="redondo b-b" data-b="b">B</button>
    </div>
  </div>
</div>
<script>
  const estado = document.getElementById("estado");
  let ws = null, sinArreglo = false;

  function conectar() {
    ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
    ws.onmessage = (ev) => {
      if (ev.data === "ok") {
        estado.innerHTML = "🎮 Listo · <a href='/'>Control</a>";
      } else if (ev.data.startsWith("error")) {
        sinArreglo = true;
        estado.textContent = ev.data.slice(6);
      }
    };
    ws.onclose = () => {
      soltarTodo();
      if (!sinArreglo) {
        estado.textContent = "Reconectando…";
        setTimeout(conectar, 1500);
      }
    };
  }
  function enviar(apretado, boton) {
    if (ws && ws.readyState === 1) ws.send((apretado ? "1 " : "0 ") + boton);
    if (apretado && navigator.vibrate) navigator.vibrate(10);
  }
  setInterval(() => { if (ws && ws.readyState === 1) ws.send("ping"); }, 10000);

  // Botones (varios dedos a la vez)
  document.querySelectorAll("button[data-b]").forEach((btn) => {
    const b = btn.dataset.b;
    const soltar = (e) => {
      if (!btn._dedos.has(e.pointerId)) return;
      btn._dedos.delete(e.pointerId);
      if (btn._dedos.size === 0) { btn.classList.remove("on"); enviar(false, b); }
    };
    btn._dedos = new Set();
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      if (btn._dedos.size === 0) { btn.classList.add("on"); enviar(true, b); }
      btn._dedos.add(e.pointerId);
    });
    btn.addEventListener("pointerup", soltar);
    btn.addEventListener("pointercancel", soltar);
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
  });

  // Cruz: se puede deslizar el dedo y hacer diagonales
  const cruz = document.getElementById("cruz");
  const flechas = {};
  cruz.querySelectorAll("[data-d]").forEach((f) => { flechas[f.dataset.d] = f; });
  let direcciones = new Set();
  function ponerDirecciones(nuevas) {
    for (const d of direcciones) if (!nuevas.has(d)) { enviar(false, d); flechas[d].classList.remove("on"); }
    for (const d of nuevas) if (!direcciones.has(d)) { enviar(true, d); flechas[d].classList.add("on"); }
    direcciones = nuevas;
  }
  // Modo palanca (analógica, para la N64): manda "ax X Y" con valores de -100 a 100
  const perilla = document.getElementById("perilla");
  const botonModo = document.getElementById("modo");
  let modoPalanca = false, palanca = [0, 0], palancaEnviada = [0, 0];
  try { modoPalanca = localStorage.getItem("televieja-palanca") === "si"; } catch (e) {}
  function mostrarModo() {
    cruz.classList.toggle("palanca", modoPalanca);
    botonModo.textContent = modoPalanca ? "Usar cruz" : "Usar palanca";
  }
  botonModo.addEventListener("click", () => {
    ponerDirecciones(new Set()); moverPalanca(0, 0);
    modoPalanca = !modoPalanca;
    try { localStorage.setItem("televieja-palanca", modoPalanca ? "si" : "no"); } catch (e) {}
    mostrarModo();
  });
  function moverPalanca(x, y) {
    const largo = Math.hypot(x, y);
    if (largo > 1) { x /= largo; y /= largo; }
    palanca = [Math.round(x * 100), Math.round(y * 100)];
    const r = cruz.getBoundingClientRect();
    perilla.style.transform = "translate(" + (x * r.width * 0.31) + "px," + (y * r.height * 0.31) + "px)";
  }
  setInterval(() => {  // como mucho ~30 mensajes por segundo
    if (palanca[0] === palancaEnviada[0] && palanca[1] === palancaEnviada[1]) return;
    if (ws && ws.readyState === 1) ws.send("ax " + palanca[0] + " " + palanca[1]);
    palancaEnviada = palanca.slice();
  }, 33);
  mostrarModo();

  function leerCruz(e) {
    const r = cruz.getBoundingClientRect();
    const dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
    const dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
    if (modoPalanca) { moverPalanca(dx / 0.75, dy / 0.75); return; }
    const zona = 0.18, d = new Set();
    if (Math.abs(dx) > zona && Math.abs(dx) >= 0.41 * Math.abs(dy)) d.add(dx < 0 ? "left" : "right");
    if (Math.abs(dy) > zona && Math.abs(dy) >= 0.41 * Math.abs(dx)) d.add(dy < 0 ? "up" : "down");
    ponerDirecciones(d);
  }
  let dedoCruz = null;
  cruz.addEventListener("pointerdown", (e) => {
    e.preventDefault(); dedoCruz = e.pointerId; cruz.setPointerCapture(e.pointerId); leerCruz(e);
  });
  cruz.addEventListener("pointermove", (e) => { if (e.pointerId === dedoCruz) leerCruz(e); });
  const soltarCruz = (e) => {
    if (e.pointerId === dedoCruz) { dedoCruz = null; ponerDirecciones(new Set()); moverPalanca(0, 0); }
  };
  cruz.addEventListener("pointerup", soltarCruz);
  cruz.addEventListener("pointercancel", soltarCruz);

  function soltarTodo() {
    ponerDirecciones(new Set());
    moverPalanca(0, 0);
    document.querySelectorAll("button.on").forEach((b) => {
      b.classList.remove("on"); b._dedos.clear(); enviar(false, b.dataset.b);
    });
  }

  // Pantalla completa, horizontal y sin que se apague la pantalla
  let pantallaLista = false;
  document.addEventListener("pointerdown", async () => {
    if (pantallaLista) return;
    pantallaLista = true;
    try { await document.documentElement.requestFullscreen(); } catch (e) {}
    try { await screen.orientation.lock("landscape"); } catch (e) {}
    try { if (navigator.wakeLock) await navigator.wakeLock.request("screen"); } catch (e) {}
  }, { capture: true });
  document.addEventListener("visibilitychange", () => { if (document.hidden) soltarTodo(); });

  conectar();
</script>
</body>
</html>
"""
