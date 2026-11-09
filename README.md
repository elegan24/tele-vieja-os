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
| Joystick USB (tipo Super Nintendo) | Para jugar (y manejar todo) |
| *Opcional:* control remoto USB "air mouse" | Para videos, canal e historietas desde el sillón |
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
git clone https://github.com/elegan24/tele-vieja-os.git
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
│   ├── NeoGeo/             .zip  (+ neogeo.zip, el BIOS, en la misma carpeta)
│   └── PlayStation/        .cue+.bin, .chd, .pbp (ver "Juegos de PlayStation")
├── Historietas/            .cbz .cbr .pdf o carpetas con imágenes
├── Radio/                  radionovelas y música (.mp3, .ogg, ...)
├── Partidas/               (las partidas guardadas de los juegos)
└── BIOS/                   (BIOS de consolas, si algún juego las pide)
```

**Con pendrive (lo más fácil):** en tu compu creá en el pendrive una carpeta
`TeleVieja` con la misma forma (solo las carpetas que uses), enchufalo en la netbook y
en el menú elegí **Copiar desde pendrive**. Copia solo lo nuevo; no borra nada.

### Disco externo USB (para tener mucho más)

Si el disco de la netbook te queda chico, enchufá un **disco externo USB** (o un pendrive):
TeleVieja lo monta solo y su contenido aparece en el menú, **sin copiar nada**.

- Armá en el disco la misma carpeta `TeleVieja` (con `Videos`, `Juegos`, `Historietas`, ...).
- En **Videos**, **Historietas** y **Radio** aparece como **"Disco: NOMBRE"** arriba de todo.
  Si el disco no tiene carpeta `TeleVieja`, igual podés recorrerlo entero desde ahí.
- Los **juegos** del disco se suman a la lista de cada consola, y el **Canal Retro** también
  usa sus programas y tandas.
- Se monta en **solo lectura**: lo podés desenchufar cuando quieras sin romper nada.
  (Las partidas guardadas y "dónde quedaste" se guardan en la netbook.)
- Sirve con discos formateados en NTFS, exFAT o FAT32 (los de Windows) y ext4 (Linux).
- El nombre que aparece es la **etiqueta** del disco: ponele uno lindo desde Windows
  (clic derecho → Cambiar nombre).
- Discos de 2,5" sin fuente propia: si la netbook no les da suficiente corriente, usá un hub USB con fuente.

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
| Juegos de PS1 | `Juegos/PlayStation` | 🟡 muchos sí (ver "Juegos de PlayStation") |
| OPL | — | ❌ no es un emulador: es un programa para cargar juegos en una PlayStation 2 de verdad |

### Juegos de PlayStation

Usa **PCSX ReARMed**, el emulador de PS1 más liviano que hay (el mismo que se usa en
consolitas portátiles). Lo esperable en un Atom: los juegos 2D y muchos 3D andan bien;
los 3D más pesados pueden ir un poco a los saltos (el emulador saltea cuadros para que el
juego no se ponga lento). No está probado en la netbook todavía: probalo con tus juegos.

- **Formatos:** `.cue` + `.bin` (poné los dos juntos en la carpeta), `.chd`, `.pbp` o `.iso`.
  En la lista aparece solo el `.cue`, no sus `.bin`.
  Si vienen en `.rar` o `.zip`, descomprimilos primero.
- **Juegos de varios discos:** poné los discos en una carpeta con un archivo `.m3u` (un archivo
  de texto con el nombre de cada disco, uno por renglón). En la lista aparece una sola vez,
  y cuando el juego pide el disco siguiente: SELECT + X (menú de RetroArch) → *Disc Control*.
  ```
  Final Fantasy VII/
  ├── Final Fantasy VII.m3u      ← adentro: los 3 nombres de abajo
  ├── Final Fantasy VII (Disc 1).chd
  ├── Final Fantasy VII (Disc 2).chd
  └── Final Fantasy VII (Disc 3).chd
  ```
- **Ocupan mucho** (300 a 700 MB cada uno). Pasalos a `.chd` y ocupan bastante menos:
  `./herramientas/comprimir-ps1.sh carpeta_juegos` (en una compu con Linux o WSL;
  necesita `sudo apt install mame-tools`). En Windows hay programas como *namDHC* que hacen lo mismo.
- **BIOS:** el emulador trae una de reemplazo y casi todos los juegos andan con ella.
  Si tenés el archivo de BIOS de tu consola (por ejemplo `scph1001.bin`), ponelo en
  `TeleVieja/BIOS` y mejora la compatibilidad.
- **L2 y R2:** muchos juegos de PS1 los usan. Al configurar el joystick te los pide
  (si tu joystick no los tiene, esperá y los saltea). El joystick del celu ya los trae.
- La tarjeta de memoria se guarda sola en `TeleVieja/Partidas`.

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

Cada vez que enchufás un **modelo nuevo** de joystick, TeleVieja te pide que **apretes cada botón**
para aprenderlo (una sola vez por modelo; el celu no hace falta configurarlo). Se puede repetir en *Opciones → Configurar joystick*.

### Control remoto

Hay dos opciones y se pueden usar las dos a la vez, junto con el joystick:

**Control remoto USB** (los de los TV Box: buscalos como *"air mouse"* o *"control remoto
inalámbrico 2.4G"*, por ejemplo el G10). Enchufás el receptor USB en la netbook y listo:

| Botón del control | Hace |
|---|---|
| Flechas y OK | Moverse y elegir |
| Atrás | Volver (en un video: salir) |
| Inicio (casita) | Vuelve al menú principal desde cualquier lado |
| Play/Pausa | Pausa el video |
| Siguiente / Anterior | Próximo capítulo o programa |
| Volumen + / − / mute | Volumen |

En el Canal Retro, **derecha** (o canal +) cambia de programa, como hacer zapping.
Para los **juegos** sigue haciendo falta el joystick (el control tiene muy pocos botones).
El "mouse" del control no hace nada (así no se sale de pantalla completa sin querer).

**El celular como control** (gratis). La netbook tiene que estar en el mismo WiFi que el
celu (configurá el WiFi al instalar Debian). En el menú andá a
*Opciones → Control desde el celular*: aparece una dirección (por ejemplo
`http://192.168.0.23:8080`) y un **código QR**. Escanealo con la cámara del celu y tenés
un control con cruz, OK, volver, inicio, pausa, volumen y botones para los juegos
(guardar, cargar y salir). Guardala en favoritos o agregala a la pantalla de inicio.

**El celular como joystick.** En esa misma página tocá **"🎮 Usar el celu como joystick"**,
girá el celu y aparece un joystick tipo Super Nintendo: cruz, A, B, X, Y, L, R, SELECT y START
(y L2/R2 arriba, para los juegos de PS1).
Para la netbook es un joystick USB más, así que sirve para **jugar** y también para el menú.

- **Dos jugadores:** cada celu que abre el joystick es un joystick distinto. Podés jugar
  con el joystick de verdad y un celu, o con dos celus.
- En la cruz podés deslizar el dedo y hacer diagonales, y se pueden apretar varios botones a la vez.
- SELECT + START sale del juego, igual que con el joystick de verdad.
- Si el celu se bloquea o se corta el WiFi, se sueltan todos los botones solos
  (no queda Mario corriendo para siempre).
- Hay un poquito de demora (lo que tarda el WiFi): para los juegos de plataformas más
  exigentes conviene el joystick USB.

> Cualquiera conectado a tu WiFi puede abrir esa página. Si no la querés, poné
> `CONTROL_CELULAR=no` en las opciones.

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
| `CONTROL_CELULAR` | `si`/`no`: la página para manejar la tele desde el celu |
| `PUERTO_CELULAR` | El puerto de esa página (`8080`) |

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
| El joystick del celu dice "No se pudo crear el joystick" | Reiniciá la netbook (carga el módulo `uinput`). Si sigue, volvé a correr `sudo ./instalar.sh` |
| El celu no abre la página del control | Que esté en el mismo WiFi que la netbook (no en datos móviles) y que la dirección sea la que muestra *Opciones → Control desde el celular* |
| Un juego no abre | Revisá que la ROM sea de esa consola. Los errores quedan en `~/.cache/televieja/juego.log` |

---

## Cómo está hecho

- `instalar.sh`: instala los paquetes, copia todo a `/opt/televieja` y configura el arranque automático.
- `televieja/`: el menú (Python + pygame), dibujado para 640x480 con márgenes para la tele de tubo.
- `sistema/`: configuración de mpv, RetroArch, el script del Canal Retro (`canal.lua`) y el arranque de X.
- `bin/pantalla.sh`: elige la salida (tele o netbook). `bin/importar-usb.sh`: copia desde el pendrive.
- `bin/disco-usb.sh` + `sistema/99-televieja-usb.rules` + `sistema/televieja-disco@.service`:
  montan solos los discos USB (solo lectura) en `/media/televieja/`.
- `televieja/remoto.py`: la página del control para el celu (un servidor web chiquito, puerto 8080)
  y el WebSocket del joystick. `televieja/joystick_virtual.py` crea el joystick virtual con
  `/dev/uinput`, y `mando.py` le arma a RetroArch un perfil de botones por cada joystick.
- `pruebas/prueba_menu.py`: recorre el menú sin pantalla (también con el celu) y guarda capturas.

Emuladores: nestopia (Family), snes9x2010 (Super Nintendo), Genesis Plus GX (Sega),
Gambatte (Game Boy), gpsp/mGBA (GBA), FBNeo (Neo Geo) y PCSX ReARMed (PlayStation).
