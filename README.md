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
2. Bajá el instalador "netinst" de **Debian 12** (ojo: la página principal de debian.org te
   ofrece la 13; TeleVieja está hecha y probada para la 12, que tiene soporte hasta 2028):
   - 64 bits: <https://cdimage.debian.org/cdimage/archive/12.15.0/amd64/iso-cd/debian-12.15.0-amd64-netinst.iso>
   - 32 bits: <https://cdimage.debian.org/cdimage/archive/12.15.0/i386/iso-cd/debian-12.15.0-i386-netinst.iso>
   (si hay una 12.x más nueva en <https://cdimage.debian.org/cdimage/archive/>, sirve igual)
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

### Pasar el disco a una netbook más potente

TeleVieja está pensada para que, si conseguís una netbook mejor (por ejemplo una Juana
Manso), le pases el disco y siga andando. Ya viene preparada para eso:

- Trae el **firmware** de las placas WiFi, de sonido y de video más comunes (Intel, Realtek,
  Atheros, Broadcom).
- El **WiFi** queda guardado para cualquier placa, no solo la de esta netbook.
- La **salida a la tele** sirve por VGA (netbooks viejas) o por **HDMI** (las nuevas). Por
  HDMI usa 720x480, que es lo que suelen pedir los conversores HDMI → AV.
- La **Nintendo 64** y lo demás se activan solos si la netbook nueva puede.

Falta un solo paso, porque las netbooks viejas y las nuevas **arrancan distinto** (BIOS y
UEFI). **Antes de sacar el disco**, en la netbook vieja y con internet:

```bash
cd tele-vieja-os
sudo ./herramientas/preparar-cambio-de-netbook.sh
```

Le agrega al disco el arranque para netbooks nuevas, sin sacar el de las viejas: después
arranca en las dos. Para hacer lugar cambia la partición de intercambio (swap) por un
archivo; **tus cosas no se tocan**. Te pide que escribas `SI` para confirmar, guarda una copia
de cómo estaba el disco y, si el disco no tiene la forma de siempre, no cambia nada.

En la netbook nueva:
1. Poné el disco y prendela. Si no arranca sola, entrá al menú de arranque (F12, F11, F10 o
   Esc) y elegí el disco. Si dice algo de *Secure Boot*, desactivalo en el BIOS.
2. Corré `sudo ./instalar.sh` de nuevo, con internet, para que se termine de adaptar.

> Ojo: muchas netbooks nuevas traen la memoria **soldada** (eMMC) en lugar de un disco que se
> pueda sacar. Antes de comprar, fijate que tenga lugar para un disco SATA de 2,5" o M.2.
> Si no tiene, instalá TeleVieja en ella con `instalar.sh` y enchufale tu disco externo USB
> con tus cosas: queda igual.

**Mejora barata:** si le ponés un disco **SSD** en vez del disco común, la netbook prende y
carga todo mucho más rápido. No hace que los juegos vayan más rápido (eso depende del
procesador), pero se nota un montón en el uso.

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
│   ├── PlayStation/        .cue+.bin, .chd, .pbp (ver "Juegos de PlayStation")
│   ├── Nintendo64/         .z64 .n64 .v64 .zip (experimental, ver "Nintendo 64")
│   ├── Arcade/             .zip/.7z de FBNeo (fichines: Capcom, Konami, Data East...)
│   └── PC/                 juegos viejos de Windows, uno por carpeta (ver "Juegos de PC")
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

### Nintendo 64 (experimental)

La N64 pide mucho más que la PS1: necesita una placa de video con 3D moderno (OpenGL 3.3).
Por eso **aparece en Juegos solo si la netbook puede**. TeleVieja se fija sola qué placa tiene:

| Netbook | N64 |
|---|---|
| Atom N450 / N455 / N570 (GMA 3150) | ❌ no aparece: la placa no alcanza |
| Atom N2600 / N2800 | ❌ no aparece: sin 3D |
| Celeron (últimos años del plan) | 🟡 aparece; algunos juegos andan |
| Juana Manso (Celeron N4020) | ✅ aparece; muchos juegos andan bien |

(Es lo que se espera por el hardware de cada una; no está probado en ninguna todavía.)

- Usa **Mupen64Plus-Next** a la resolución original (320x240), que es lo más liviano.
- Muchos juegos de N64 (Mario 64, Zelda) se juegan con **palanca analógica**:
  - Con un joystick con palancas: al configurarlo te pide moverlas (si no tiene, esperá y lo saltea).
  - Con el **celu**: en el joystick tocá **"Usar palanca"** y la cruz se convierte en palanca.
  - La palanca derecha hace de botones C (la cámara en Mario 64).
- Botones: A y B de la N64 = B e Y del joystick, Z = L2, L y R = L y R.
- Si querés que aparezca igual (o esconderla), poné `N64=si` o `N64=no` en las opciones.

### Arcade (fichines)

Los juegos de las placas arcade: Street Fighter, Marvel vs. Capcom, X-Men, Final Fight,
Cadillacs and Dinosaurs, Metal Slug, Tortugas Ninja... Usa **FBNeo**, el mismo emulador que la Neo Geo.

- Poné los `.zip` (o `.7z`) **tal cual vienen**, sin descomprimir ni cambiarles el nombre:
  FBNeo los reconoce por el nombre (`sfa.zip`, `mvsc.zip`...). En el menú aparecen con el
  nombre completo ("Street Fighter Alpha: Warriors' Dreams").
- Tienen que ser *romsets* para FBNeo. Los de otras versiones de MAME a veces no andan.
- Algunas placas necesitan además su BIOS en la misma carpeta (por ejemplo `neogeo.zip` o `pgm.zip`).
  TeleVieja no las muestra en la lista porque no son juegos.
- En un Atom andan bien casi todos los de los 80 y 90 (Capcom CPS1/CPS2, Neo Geo, Konami).
  Los más modernos (CPS3, Cave) pueden ir lentos.

### Juegos de PC (Windows viejos)

Para juegos de Windows de los 90 y principios de los 2000, como **Sonic R de PC**. Se abren
con **Wine**, un programa que hace andar juegos de Windows en Linux.

- Cada juego va en **su propia carpeta** adentro de `TeleVieja/Juegos/PC`, ya instalado:
  ```
  Juegos/PC/
  └── Sonic R/
      ├── SONICR.EXE
      └── (el resto de los archivos del juego)
  ```
  Lo más fácil: instalalo en una compu con Windows y copiá la carpeta que quedó
  (por ejemplo `C:\Program Files\Sonic R`).
- TeleVieja busca solo el `.exe` del juego (saltea instaladores y desinstaladores). Si hay
  varios y no sabe cuál, te avisa: creá en la carpeta un archivo **`jugar.txt`** con el nombre
  del que abre el juego (por ejemplo `SONICR.EXE`).
- La primera vez tarda un par de minutos en **preparar Wine**. Después abre enseguida.
- El juego se ve en una ventana del tamaño de la pantalla (así la tele y el conversor no
  tienen que cambiar de resolución). Si un juego se ve mal, probá `PC_ESCRITORIO_VIRTUAL=no`.
- **SELECT + START** (mantenidos) cierra el juego, igual que en las consolas. Los controles
  de adentro del juego se configuran en el propio juego (Sonic R tiene su menú de opciones).
- Copiá los juegos de PC a la netbook: desde un disco USB (que es de solo lectura) muchos no
  pueden guardar su configuración.
- **Ojo con los juegos que piden el CD:** algunos, Sonic R incluido, tocan la música directo
  del CD. Sin el CD, puede que no tengan música o que no arranquen. Hay arreglos de la
  comunidad para esos casos.
- Wine no anda con todos los juegos. Para ver cuáles andan, buscá el juego en
  **appdb.winehq.org**.
- Wine ocupa bastante. Para no instalarlo: `sudo SIN_WINE=1 ./instalar.sh`.

### Descargar desde Google Drive (con el celu)

En la página del control del celu (*Opciones → Control desde el celular*) hay una sección
**"Descargar de Google Drive"**: pegás el link de un archivo o de una carpeta, tocás **Bajar**,
y la netbook lo baja sola. Ves cómo va en el celu y en la tele (*Opciones → Descargas*), y
cuando termina aparece un aviso.

Al terminar, **lo acomoda solo**:

| Qué es | A dónde va |
|---|---|
| Videos | `Videos/` (respetando las carpetas: cada serie con sus capítulos) |
| Música y radionovelas | `Radio/` |
| Historietas (.cbr, .cbz, .pdf, o carpetas con páginas) | `Historietas/` |
| Juegos (.nes, .sfc, .md, .gb, .gba, .z64, .cue/.chd...) | `Juegos/<consola>/` según la extensión |
| Juegos de arcade (.zip de FBNeo) | `Juegos/Arcade/` |
| Packs comprimidos (.zip/.rar/.7z con muchas cosas) | se descomprimen y se reparten |
| Juegos de PC (carpetas con .exe) y lo que no reconoce | `Descargas/`, para acomodarlo a mano |

Límites (los pone Google, no TeleVieja):
- El link tiene que estar compartido como **"Cualquier persona con el enlace"**.
- Sin una cuenta, Google muestra **como mucho 50 archivos por carpeta**. Si una carpeta tiene
  más, te avisa: pegá el link de cada subcarpeta para bajar el resto.
- Si un archivo se bajó demasiadas veces ese día, Google lo bloquea por un rato
  (**"cuota de descarga"**): probá de nuevo al otro día.
- Baja de a una descarga por vez y deja siempre medio GB libre en el disco.
- Cualquiera conectado a tu WiFi puede usar la página, igual que el control.

Usá la herramienta con cosas que tengas derecho a bajar: tus propios archivos, lo que te
compartan, contenido libre o copias de juegos y discos que tengas.

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
| X | F2 o Insert | En una lista de juegos: agregar o sacar de **Favoritos** ★ |
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
(guardar, cargar y salir).

**Tenerlo como una app:** con la página abierta en Chrome, tocá los 3 puntitos →
**"Agregar a la pantalla principal"** (en iPhone: Compartir → "Agregar a inicio"). Queda un
ícono de una tele retro llamado "TeleVieja". Si reiniciás el router y deja de andar, volvé a
escanear el QR (a veces la netbook cambia de dirección).

**El celular como joystick.** En esa misma página tocá **"🎮 Usar el celu como joystick"**,
girá el celu y aparece un joystick tipo Super Nintendo: cruz, A, B, X, Y, L, R, SELECT y START
(y L2/R2 arriba, para los juegos de PS1). El botón **"Usar palanca"** cambia la cruz por una
palanca analógica, para los juegos de N64.
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

## Actualizar TeleVieja (con un botón)

*Opciones → **Actualizar TeleVieja*** (o el botón **"Actualizar TeleVieja"** al final de la página
del celu). La tele pregunta si buscar la última versión; al confirmar, la netbook la baja de
GitHub, la instala y reinicia el menú sola. Tarda unos minutos y necesita internet. Si ya tenés
la última versión, te lo dice. El registro queda en `/var/log/televieja-actualizar.log`.

(La primera vez, para tener el botón, hay que actualizar a mano una vez:
`sudo -i`, `cd tele-vieja-os`, `git pull`, `./instalar.sh TU_USUARIO`.)

## Temas, efectos y otras chucherías

- **Temas** (*Opciones → Tema*): Clásico, Fichín (arcade, con grilla de neón), Game Boy (los
  4 verdes), Cine (con telón), Canal 7 años 80 (la carta de ajuste), Navidad y Halloween. Al
  moverte por la lista ya se ve cómo queda; A lo elige y B vuelve al de antes. Cada tema cambia
  también los pitiditos del menú y el color del logo del Canal Retro. En **Automático** usa el
  Clásico, salvo en Navidad (diciembre hasta Reyes) y Halloween (fines de octubre), que se ponen solos.
- **Encendido y apagado de tele de tubo:** al prender, la imagen se abre desde una rayita de
  luz; al apagar, se cierra en un puntito.
- **Protector de pantalla:** si no tocás nada por 5 minutos aparece la **carta de ajuste** y
  después el **logo rebotando** (cambia de color en cada choque y cuenta las veces que pega justo
  en la esquina). Van alternando para que no se marque el tubo. Cualquier botón vuelve.
- **Favoritos y Últimos jugados:** en una lista de juegos apretá **X** para marcar un favorito
  (★). Arriba de todo en *Juegos* aparecen **Favoritos** y **Últimos jugados**, con juegos de
  todas las consolas juntos.
- **WiFi sin cortes:** el instalador apaga el "ahorro de energía" de la placa WiFi, que en
  algunas (como la Realtek RTL8191SE de las Conectar Igualdad) hace que se corte sola.

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
| `RESOLUCION_HDMI` | `720x480` para conversores HDMI → AV (o `720x576`, o `640x480`) |
| `CONTROL_CELULAR` | `si`/`no`: la página para manejar la tele desde el celu |
| `PUERTO_CELULAR` | El puerto de esa página (`8080`) |
| `N64` | `auto` (aparece si la placa de video puede), `si` o `no` |
| `PC_ESCRITORIO_VIRTUAL` | `si`: los juegos de PC en una ventana del tamaño de la pantalla; `no`: que cambien la resolución |
| `DESCARGAS_PARALELAS` | Cuántos archivos se bajan a la vez de una carpeta de Drive (`4`; de 1 a 8) |
| `TEMA` | `auto`, `clasico`, `fichin`, `gameboy`, `cine`, `canal7`, `navidad` o `halloween` |
| `EFECTO_ENCENDIDO` | `si`/`no`: efecto de tele de tubo al prender y apagar |
| `PROTECTOR_MINUTOS` | Minutos sin tocar nada hasta el protector de pantalla (`0` = nunca) |

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
| El WiFi se corta cada tanto | Volvé a correr `sudo ./instalar.sh` (apaga el ahorro de energía del WiFi) y reiniciá |
| El celu no abre la página del control | Que esté en el mismo WiFi que la netbook (no en datos móviles) y que la dirección sea la que muestra *Opciones → Control desde el celular* |
| Un juego no abre | Revisá que la ROM sea de esa consola. Los errores quedan en `~/.cache/televieja/juego.log` |
| Un juego de PC no abre | Mirá `~/.cache/televieja/pc.log` y buscá el juego en appdb.winehq.org |

---

## Cómo está hecho

- `instalar.sh`: instala los paquetes, copia todo a `/opt/televieja` y configura el arranque automático.
- `televieja/`: el menú (Python + pygame), dibujado para 640x480 con márgenes para la tele de tubo.
- `sistema/`: configuración de mpv, RetroArch, el script del Canal Retro (`canal.lua`) y el arranque de X.
- `bin/pantalla.sh`: elige la salida (tele o netbook). `bin/importar-usb.sh`: copia desde el pendrive.
- `herramientas/preparar-cambio-de-netbook.sh`: agrega el arranque UEFI (con Secure Boot) al
  disco sin sacar el de BIOS. `bin/wifi-portatil.sh`: guarda el WiFi en NetworkManager.
- `bin/disco-usb.sh` + `sistema/99-televieja-usb.rules` + `sistema/televieja-disco@.service`:
  montan solos los discos USB (solo lectura) en `/media/televieja/`.
- `televieja/descargas.py` (cola), `televieja/bajar_drive.py` (baja con gdown, en
  `/opt/televieja/pyenv`) y `televieja/acomodar.py` (reparte por tipo de archivo).
- `televieja/remoto.py`: la página del control para el celu (un servidor web chiquito, puerto 8080)
  y el WebSocket del joystick. `televieja/joystick_virtual.py` crea el joystick virtual con
  `/dev/uinput`, y `mando.py` le arma a RetroArch un perfil de botones por cada joystick.
- `pruebas/prueba_menu.py`: recorre el menú sin pantalla (también con el celu) y guarda capturas.

Emuladores: nestopia (Family), snes9x2010 (Super Nintendo), Genesis Plus GX (Sega),
Gambatte (Game Boy), gpsp/mGBA (GBA), FBNeo (Neo Geo), PCSX ReARMed (PlayStation)
y Mupen64Plus-Next (Nintendo 64, experimental). Juegos de PC: Wine (`televieja/wine.py`).
