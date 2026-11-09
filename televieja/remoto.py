"""Control desde el celular: una página web con botones, servida por la netbook.

Entrás desde el celu (conectado al mismo WiFi) a http://IP-DE-LA-NETBOOK:8080
y cada botón le llega al menú como si fuera el joystick.
"""
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pygame

EVENTO = pygame.USEREVENT + 7
BOTONES = {"up", "down", "left", "right", "a", "b", "x", "y", "l", "r",
           "select", "start", "inicio", "vol+", "vol-", "mute"}


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
            cuerpo = PAGINA.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(cuerpo)
        else:
            self.send_error(404)

    def do_POST(self):
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

    def log_message(self, *args):
        pass


def iniciar(puerto):
    """Arranca el servidor en segundo plano. Devuelve el servidor o None si no se pudo."""
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
  #estado { margin-top:20px; font-size:13px; color:#97a3d6; text-align:center; min-height:1em; }
</style>
</head>
<body>
<main>
  <h1><span class="franjas"><i style="background:#e6463c"></i><i style="background:#f58c28"></i>
    <i style="background:#ffd43c"></i><i style="background:#5ac86e"></i><i style="background:#5aaaf0"></i></span>
    TeleVieja</h1>

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
</script>
</body>
</html>
"""
