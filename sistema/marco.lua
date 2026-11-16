-- Marco (bezel) alrededor del video, estilo Super Game Boy.
-- Lo carga Frecuencia 99 en mpv cuando hay un marco elegido (Opciones → Marco de la tele).
-- bin/marco.py prepara el PNG del marco para el tamaño de esta pantalla (y para la franja
-- horaria, si el marco cambia con la hora) y dice dónde va el video (el hueco del centro).
-- Si el video es 4:3 (o más angosto que la pantalla), se muestra el marco y el video va en
-- el hueco; si es 16:9, el marco se esconde y el video va a pantalla completa.
-- Avisa a canal.lua dónde quedó el video (script-message marco-ventana) para que el logo,
-- el reloj, el zócalo y las cortinas vayan adentro de la "tele".

local utils = require("mp.utils")
local opts = { carpeta = "", ayudante = "", cache = "" }
require("mp.options").read_options(opts, "marco")

local ID = 7            -- número de overlay de mpv (cualquiera libre)
local datos = nil       -- lo que devolvió marco.py para esta pantalla y franja
local clave = nil       -- pantalla y franja de "datos"
local mostrando = nil   -- true/false: el estado aplicado

local function franja()
    local h = tonumber(os.date("%H"))
    if h >= 1 and h < 6 then return "madrugada" end
    if h >= 6 and h < 13 then return "manana" end
    if h >= 13 and h < 20 then return "tarde" end
    return "noche"
end

local function preparar(w, h)
    local r = mp.command_native({
        name = "subprocess", playback_only = false, capture_stdout = true,
        args = { "python3", opts.ayudante, "preparar", opts.carpeta, tostring(w), tostring(h),
                 opts.cache },
    })
    local salida = (r and r.stdout or ""):match("([^\n]*)\n*$") or ""
    local d = utils.parse_json(salida)
    if not d or not d.archivo then
        mp.msg.warn("sin marco: " .. ((d and d.error) or salida))
        return nil
    end
    return d
end

local function margenes(izq, arriba, der, abajo)
    mp.set_property_number("video-margin-ratio-left", izq)
    mp.set_property_number("video-margin-ratio-top", arriba)
    mp.set_property_number("video-margin-ratio-right", der)
    mp.set_property_number("video-margin-ratio-bottom", abajo)
    mp.commandv("script-message", "marco-ventana", tostring(izq), tostring(arriba),
                tostring(der), tostring(abajo))
end

local function aplicar()
    local dim = mp.get_property_native("osd-dimensions")
    local vp = mp.get_property_native("video-params")
    if not dim or not dim.w or dim.w <= 0 or not vp or not vp.aspect then
        return  -- entre un archivo y otro: se deja como está (sin parpadeos)
    end
    local k = dim.w .. "x" .. dim.h .. " " .. franja()
    if k ~= clave then
        clave = k
        datos = preparar(dim.w, dim.h)
        mostrando = nil  -- hay que volver a dibujarlo
    end
    local pantalla = dim.aspect or (dim.w / dim.h)
    local usar = datos ~= nil and (vp.aspect <= 1.45 or vp.aspect < pantalla - 0.05)
    if usar == mostrando then return end
    mostrando = usar
    if usar then
        mp.commandv("overlay-add", tostring(ID), "0", "0", datos.archivo, "0", "bgra",
                    tostring(datos.ancho), tostring(datos.alto), tostring(datos.ancho * 4))
        margenes(datos.ventana[1], datos.ventana[2], datos.ventana[3], datos.ventana[4])
    else
        mp.commandv("overlay-remove", tostring(ID))
        margenes(0, 0, 0, 0)
    end
end

if opts.carpeta ~= "" and opts.ayudante ~= "" then
    mp.observe_property("video-params", "native", aplicar)
    mp.observe_property("osd-dimensions", "native", aplicar)
    mp.add_periodic_timer(60, aplicar)  -- por si cambia la franja horaria
end
