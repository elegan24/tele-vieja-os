# Plantilla para hacer tu propio marco · Frecuencia 99

El marco es un dibujo que **llena las franjas negras** que quedan al costado (o arriba y
abajo) del video. El video no se achica: el marco solo se ve donde el video no llega.

## Qué hay acá

| Archivo | Para qué |
|---|---|
| `guia-1280x720.png` | La guía: muestra qué parte del dibujo se ve en cada pantalla |
| `guia-pixelart-320x180.png` | La misma guía, chiquita, para dibujar en pixel art |
| `ejemplo/Mi_Marco/` | Un marco de ejemplo, listo para copiar y probar |
| `ejemplo/marco.json` | Ejemplo de configuración (opcional) |

Para bajar todo junto: **`plantilla-marco.zip`** (en la carpeta `plantillas` del GitHub).

## Qué parte se ve

- **Rojo (costados):** se ve en pantallas anchas, como la de la netbook, cuando el
  video es 4:3 (los dibujos animados y series viejas).
- **Azul (arriba y abajo):** se ve en la tele o el monitor de tubo cuando el video es
  16:9 (lo más nuevo).
- **Gris (centro):** no se ve nunca, lo tapa el video. Podés dejarlo como quieras.
- **Línea amarilla punteada:** lo que queda afuera puede cortarse (la tele de tubo come
  un poquito los bordes y la netbook corta 26 píxeles de cada costado). No pongas texto
  importante afuera de esa línea.

## Cómo hacerlo, paso a paso

1. Abrí `guia-1280x720.png` en un programa o app de dibujo: Ibis Paint o Medibang en el
   celu, o Photopea (photopea.com, gratis en el navegador), Krita o GIMP en una compu.
2. Dejá la guía como **capa de abajo** y dibujá en una **capa nueva** arriba.
3. Pintá **todo** el dibujo, de borde a borde: si queda algo transparente, se rellena
   solo con el color promedio de tu marco.
4. Escondé la capa de la guía y guardá como **PNG de 1280 × 720** con el nombre:
   - `default.png` si querés el mismo marco todo el día, o
   - `manana.png` (6 a 12:59), `tarde.png` (13 a 19:59), `noche.png` (20 a 0:59) y
     `madrugada.png` (1 a 5:59) para que cambie solo con la hora. Podés hacer solo
     algunas: las que falten usan `default.png` (o la que haya).
5. Poné tu dibujo en una carpeta con el nombre del marco (sin espacios raros), por
   ejemplo `Mi_Marco/default.png`, adentro de **`TeleVieja/Marcos`**:
   - en un pendrive: `TeleVieja/Marcos/Mi_Marco/default.png` y en la netbook
     *Opciones → Copiar desde pendrive*, o
   - en el disco USB: `TeleVieja/Marcos/Mi_Marco/default.png` (se usa directo, sin copiar).
6. En la netbook: *Opciones → Marco de la tele → Mi Marco*. ¡Listo!

## Pixel art (opcional)

Si dibujás en chiquito, usá `guia-pixelart-320x180.png` (320 × 180) y poné al lado de tu
PNG un archivo `marco.json` con:

```json
{"pixelArt": true}
```

Así se agranda sin suavizar y los píxeles quedan nítidos.

## Otro estilo: el video adentro del dibujo (Super Game Boy)

Si preferís que el video se achique para entrar en un hueco de tu dibujo (en vez de
llenar las franjas), dejá ese hueco **transparente** y poné en `marco.json`:

```json
{"modo": "ventana"}
```

El hueco se detecta solo. Si querés indicarlo a mano (en % del dibujo):
`{"modo": "ventana", "anchoPorcentaje": 60, "altoPorcentaje": 80}`.
