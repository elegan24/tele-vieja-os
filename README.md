# 📺 TeleVieja OS

Convierte una netbook vieja (la del plan Conectar Igualdad, "la Cristina") en una
**consola para la tele de tubo**: la prendés y aparece un menú grande para ver
videos, poner un canal retro con tandas, jugar juegos viejos, leer historietas
y escuchar radionovelas. Todo se maneja con un joystick USB.

```
 ┌───────────────────────────────┐
 │ ≡ TELE VIEJA            21:45 │
 │ ───────────────────────────── │
 │ [▶] Canal Retro               │
 │  ▶  Videos                    │
 │  🎮 Juegos                    │
 │  📖 Historietas               │
 │  ♪  Radio                     │
 │  ⬆  Copiar desde pendrive     │
 │  ⚙  Opciones                  │
 │  ⏻  Apagar                    │
 └───────────────────────────────┘
```

Por debajo es un **Debian 12** mínimo (sin escritorio) que arranca directo en el menú.

---

## 1. Qué necesitás

| Cosa | Para qué |
|---|---|
| Netbook Conectar Igualdad (ver abajo cuál conviene) | El "cerebro" |
| Conversor **VGA → AV (RCA)** | La netbook tiene salida VGA y la tele entrada RCA |
| Cable **3,5 mm → RCA** | Sonido: de la salida de auriculares a la tele |
| Joystick USB (tipo Super Nintendo) | Para manejar todo |
| Pendrive de 2 GB o más | Para instalar Debian (y después para cargar cosas) |

### ¿Qué netbook conviene?

Mirá la etiqueta de abajo o, al prenderla, entrá al BIOS para ver el procesador:

- ✅ **Intel Atom N450 / N455 / N570**: las más comunes. Andan bien.
- ✅✅ **Intel Celeron**: las de los últimos años. Mejores todavía.
- ❌ **Intel Atom N2600 / N2800**: evitalas. Su placa de video (GMA 3600) casi no anda en Linux.
- ⚠️ Antes de comprarla, que la prendan delante tuyo: muchas quedaron **bloqueadas**
  por el sistema antirrobo del plan.
- Tiene que tener puerto **VGA** (el azul de 15 pines).

### Cómo se conecta

```
 NETBOOK                         CONVERSOR VGA→AV            TELE
 [VGA azul] ──── cable VGA ────▶ [VGA IN]
                                 [AV OUT amarillo] ────────▶ VIDEO
 [auriculares] ── cable 3,5mm→RCA (blanco o rojo) ─────────▶ AUDIO
 [USB] ───────── alimentación del conversor (si la pide)
```

- La tele **Ansai ACP-1393R** es *multisistema*: acepta PAL y NTSC. Si se ve en
  **blanco y negro**, cambiá la norma en el conversor (botón o llave NTSC/PAL).
- Tiene una sola entrada de audio (mono): usá **una** de las dos fichas del cable (blanca o roja).

---

## 2. Instalar Debian en la netbook

1. **¿32 o 64 bits?** Atom N450/N455/N570 y Celeron → **64 bits (amd64)**.
   Si es un Atom N270/N280 → 32 bits (i386). Ante la duda, usá i386, que anda en todas.
2. Bajá el instalador "netinst" de Debian 12 desde **debian.org**:
   - 64 bits: `debian-12.x.x-amd64-netinst.iso`
   - 32 bits: `debian-12.x.x-i386-netinst.iso`
3. Grabalo en el pendrive con **Rufus** (Windows) o **balenaEtcher**.
4. Enchufá el pendrive y prendé la netbook apretando **F12** (en algunas es F11, F10 o Esc)
   para elegir arrancar desde USB.
5. En el instalador:
   - Idioma: Español, país: Argentina, teclado: Latinoamericano.
   - Conectala por cable o WiFi (necesita internet).
   - **Contraseña de root: dejala vacía.** Así tu usuario puede usar `sudo`.
   - Usuario: el nombre que quieras (por ejemplo `tele`).
   - Particionado: "Guiado - utilizar todo el disco".
   - En **"Selección de programas"**, destildá TODO menos
     **"utilidades estándar del sistema"**. (Nada de escritorio: TeleVieja ya trae su menú.)
6. Reiniciá, sacá el pendrive y entrá con tu usuario y contraseña.

## 3. Instalar TeleVieja

En la netbook, con internet:

```bash
sudo apt install -y git
git clone https://github.com/USUARIO/tele-vieja-os.git
cd tele-vieja-os
sudo ./instalar.sh
sudo reboot
```

> Si el repositorio es privado, bajá el ZIP desde GitHub en otra compu, pasalo por
> pendrive y descomprimilo en la netbook (`unzip tele-vieja-os-main.zip`).

El instalador tarda un rato (baja unos 300 MB). Cuando reinicia, **arranca solo en el menú**.
Si hay algo conectado en la salida VGA, la imagen sale por la tele; si no, por la pantalla de la netbook.

---

## 4. Cargar tus cosas

Todo va en la carpeta **`TeleVieja`** de la netbook:

```
TeleVieja/
├── Videos/                 películas y series (podés hacer subcarpetas por serie)
├── Canal/
│   ├── Programas/          lo que pasa el Canal Retro (si está vacía, usa Videos/)
│   └── Tandas/             publicidades viejas que van entre programa y programa
├── Juegos/
│   ├── Family/             .nes
│   ├── SuperNintendo/      .smc .sfc
│   ├── Sega/               .md .gen .bin .sms .gg
│   ├── GameBoy/            .gb .gbc
│   ├── GameBoyAdvance/     .gba
│   └── NeoGeo/             .zip  (+ neogeo.zip, el BIOS, en la misma carpeta)
├── Historietas/            .cbz .cbr .pdf o carpetas con imágenes
├── Radio/                  radionovelas y música (.mp3, .ogg, ...)
├── Partidas/               (las partidas guardadas de los juegos)
└── BIOS/                   (BIOS de consolas, si algún juego las pide)
```

**Con pendrive (lo más fácil):** en tu compu creá en el pendrive una carpeta
`TeleVieja` con la misma forma (solo las carpetas que uses), enchufalo en la netbook y
en el menú elegí **Copiar desde pendrive**. Copia solo lo nuevo; no borra nada.

Las ROMs se pueden dejar en `.zip`. Lo que no puede ser es `.rar` o `.7z` (para juegos):
descomprimilos primero.

### Tus emuladores de Windows

No hacen falta: TeleVieja trae **RetroArch**, que emula todas esas consolas.
Usá solamente las ROMs que venían adentro:

| Lo que tenés | Dónde va | ¿Anda en la netbook? |
|---|---|---|
| E.M.U.L.4.D.O.R.N.3.S (ROMs de Family) | `Juegos/Family` | ✅ perfecto |
| Super Nintendo | `Juegos/SuperNintendo` | ✅ bien (usa snes9x2010, el liviano) |
| NeoRAGEx | `Juegos/NeoGeo` | ✅ bien. Ojo: las ROMs de NeoRAGEx son versiones muy viejas y algunas no las reconoce el emulador moderno |
| Visual Boy Advance | `Juegos/GameBoyAdvance` | 🟡 la mayoría sí |
| MARIO DS | — | ❌ Nintendo DS es demasiado pesada para un Atom |
| OPL | — | ❌ no es un emulador: es un programa para cargar juegos en una PlayStation 2 de verdad |

### Videos más livianos

La netbook no tiene aceleración de video. En una tele de tubo no se nota la diferencia,
así que conviene pasar los videos a 480 líneas. En una compu más potente con Linux o WSL:

```bash
./herramientas/convertir-videos.sh carpeta_con_videos carpeta_salida
```

En Windows se puede hacer lo mismo con **HandBrake**: preset *"Fast 480p30"* y en
*Video* activá **Fast Decode**.

---

## 5. Controles

### Menú

| Joystick | Teclado | Hace |
|---|---|---|
| Cruz | Flechas | Moverse (izquierda/derecha = página entera) |
| A | Enter | Elegir |
| B | Esc | Volver |
| L / R | RePág / AvPág | Saltar a la letra anterior / siguiente (para listas con miles de juegos) |
| — | una letra | Ir a los juegos que empiezan con esa letra |

La primera vez que enchufás un joystick, TeleVieja te pide que **apretes cada botón**
para aprenderlo. Se puede repetir en *Opciones → Configurar joystick*.

### Videos y Radio

A o START pausa · izquierda/derecha adelanta o atrasa 10 s · arriba/abajo cambia el volumen ·
L/R capítulo anterior/siguiente · X subtítulos · Y idioma · **B sale**.
Al elegir un capítulo, sigue solo con los siguientes. Si salís a la mitad, la próxima vez sigue desde ahí.

### Canal Retro

Mezcla tus programas con las tandas y los pasa sin parar, con el nombre del canal y la
hora en la esquina. Al entrar agarrás un programa empezado, como cuando prendías la tele.
Derecha o R cambia de programa · A muestra qué estás viendo · **B sale**.

### Juegos

**SELECT + START: salir** · SELECT + R: guardar partida · SELECT + L: cargar partida ·
SELECT + X: menú de RetroArch. Si un juego se cuelga, mantené SELECT + START 3 segundos.

### Historietas

| Botón | Hace |
|---|---|
| Arriba / abajo | Bajar por la página; al llegar al final, pasa a la siguiente |
| Izquierda / derecha | Página anterior / siguiente (o moverse a los costados en modo lupa) |
| L / R | Página anterior / siguiente |
| A | Cambiar zoom: **Ancho** → **Lupa** → **Página entera** |
| X o SELECT | Modo manga (se lee de derecha a izquierda) |
| B | Salir (se acuerda en qué página quedaste) |

En una tele de 13" lo más cómodo es **Ancho**: la página ocupa todo el ancho y vas bajando.

---

## 6. Opciones

En `~/.config/televieja/opciones.conf` (desde *Opciones → Salir a la terminal*, con `nano`):

| Opción | Qué hace |
|---|---|
| `NOMBRE_CANAL` | El nombre que aparece arriba y en la esquina del canal |
| `CANAL_RELOJ` | `si`/`no`: hora en el Canal Retro |
| `CANAL_EMPEZADO` | `si`/`no`: agarrar el primer programa empezado |
| `TANDAS_POR_CORTE` | Cuántas publicidades entre programas |
| `ARRANCAR_EN` | `menu` o `canal` (¡prendés y ya está pasando algo!) |
| `RESOLUCION` | `640x480` (si el conversor no la toma: `800x600`) |

Para volver al menú desde la terminal: `startx`.

---

## 7. Si algo no anda

| Problema | Solución |
|---|---|
| La tele se ve en blanco y negro | Cambiá NTSC/PAL en el conversor |
| No sale nada en la tele | Encendé la netbook con el conversor ya enchufado, o *Opciones → Cambiar pantalla* |
| La imagen se corta en los bordes | Es normal en las teles de tubo (overscan); el menú ya deja margen |
| El conversor dice "fuera de rango" | Poné `RESOLUCION=800x600` en las opciones |
| No hay sonido | Revisá el cable de auriculares y el volumen de la tele. Desde la terminal: `alsamixer` |
| El joystick no responde en los juegos | *Opciones → Configurar joystick* |
| Un video anda trabado | Pasalo a 480p (ver arriba) |
| Un juego no abre | Revisá que la ROM sea de esa consola. Los errores quedan en `~/.cache/televieja/juego.log` |

---

## Cómo está hecho

- `instalar.sh`: instala los paquetes, copia todo a `/opt/televieja` y configura el arranque automático.
- `televieja/`: el menú (Python + pygame), dibujado para 640x480 con márgenes para la tele de tubo.
- `sistema/`: configuración de mpv, RetroArch, el script del Canal Retro (`canal.lua`) y el arranque de X.
- `bin/pantalla.sh`: elige la salida (tele o netbook). `bin/importar-usb.sh`: copia desde el pendrive.
- `pruebas/prueba_menu.py`: recorre el menú sin pantalla y guarda capturas.

Emuladores: nestopia (Family), snes9x2010 (Super Nintendo), Genesis Plus GX (Sega),
Gambatte (Game Boy), gpsp/mGBA (GBA) y FBNeo (Neo Geo).
