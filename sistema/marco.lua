-- Marco (bezel) alrededor del video, estilo Super Game Boy.
-- Lo carga Frecuencia 99 en mpv cuando hay un marco elegido (Opciones → Marco de la tele).
-- bin/marco.py prepara el PNG del marco para el tamaño de esta pantalla (y para la franja
-- horaria, si el marco cambia con la hora) y dice dónde va el video (el hueco del centro).
-- El marco tapa las franjas negras que deja el video (a los costados o arriba y abajo); el
-- video queda en su tamaño de siempre. Si el video llena la pantalla, no hay marco.
-- (Con "modo": "ventana" en marco.json, el video se achica para entrar en el dibujo.)
-- Avisa a canal.lua dónde quedó el video (script-message marco-ventana) para que el logo,
-- el reloj, el zócalo y las cortinas vayan adentro de la "tele".

local utils = require("mp.utils")
local opts = { carpeta = "", ayudante = "", cache = "", pantalla = "" }  -- pantalla: "1024x600" para forzar
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

local function preparar(w, h, aspecto)
    local r = mp.command_native({
        name = "subprocess", playback_only = false, capture_stdout = true, capture_stderr = true,
        args = { "python3", opts.ayudante, "preparar", opts.carpeta, tostring(w), tostring(h),
                 opts.cache, string.format("%.4f", aspecto) },
    })
    local salida = (r and r.stdout or ""):match("([^\n]*)\n*$") or ""
    local d = utils.parse_json(salida)
    if not d or not d.archivo then
        local errores = (r and r.stderr or ""):match("([^\n]+)\n*$")  -- la última línea
        local motivo = (d and d.error) or errores or salida
        if motivo == "" then motivo = "el ayudante no contestó (estado " .. tostring(r and r.status) .. ")" end
        mp.msg.warn("sin marco: " .. motivo)
        -- que se vea en la tele por qué no aparece (así se puede mandar una foto)
        mp.osd_message("No se pudo poner el marco: " .. motivo:sub(1, 120), 8)
        return nil
    end
    return d
end

local function margenes(izq, arriba, der, abajo)
    mp.set_property_number("video-margin-ratio-left", izq)
    mp.set_property_number("video-margin-ratio-top", arriba)
    mp.set_property_number("video-margin-ratio-right", der)
    mp.set_property_number("video-margin-ratio-bottom", abajo)
end

local function avisar_ventana(v)  -- a canal.lua: dónde quedó el video
    mp.commandv("script-message", "marco-ventana", tostring(v[1]), tostring(v[2]),
                tostring(v[3]), tostring(v[4]))
end

local function modo_ventana()  -- ¿marco.json pide achicar el video (estilo Super Game Boy)?
    local f = io.open(opts.carpeta .. "/marco.json", "r")
    if not f then return false end
    local texto = f:read("*a")
    f:close()
    return texto:find('"modo"%s*:%s*"ventana"') ~= nil
end

local relleno_puesto = nil   -- a qué forma se agrandó la imagen del video (filtro @marco)

local function aspecto_pantalla()
    local fw, fh = opts.pantalla:match("^(%d+)x(%d+)$")
    if fw then return tonumber(fw) / tonumber(fh) end
    local w = mp.get_property_number("display-width")
    local h = mp.get_property_number("display-height")
    if w and h and h > 0 then
        return w / h * (mp.get_property_number("monitorpixelaspect", 1) or 1)
    end
    local dim = mp.get_property_native("osd-dimensions")
    if dim and dim.h and dim.h > 0 then return dim.aspect or (dim.w / dim.h) end
    return nil
end

-- Con la salida "xv" (la liviana de la netbook), mpv dibuja todo SOBRE la imagen del video,
-- nunca en las franjas negras. Por eso la imagen se agranda hasta la forma de la pantalla
-- (las franjas pasan a ser parte de la imagen; casi no gasta) y ahí el marco va encima.
local function agrandar(aspecto_video, pantalla)
    local quiere = nil
    if pantalla and math.abs(aspecto_video - pantalla) > 0.02 then
        quiere = string.format("%.4f", pantalla)
    end
    if quiere == relleno_puesto then return end
    if relleno_puesto then mp.commandv("vf", "remove", "@marco") end
    if quiere then
        mp.commandv("vf", "add", "@marco:lavfi=[pad=aspect=" .. quiere ..
                    ":x=(ow-iw)/2:y=(oh-ih)/2:color=black]")
    end
    relleno_puesto = quiere
end

local function aplicar()
    local dim = mp.get_property_native("osd-dimensions")
    if dim and (not dim.w or dim.w <= 0) then
        -- algunas salidas no dicen el tamaño: se dibuja sobre la imagen (como en "xv")
        local vp = mp.get_property_native("video-out-params")   -- la imagen ya agrandada
        if vp and vp.w and vp.w > 0 then dim = { w = vp.w, h = vp.h } end
    end
    -- la forma del video tal como viene (antes de agrandarlo)
    local dp = mp.get_property_native("video-dec-params")
    if not dim or not dim.w or dim.w <= 0 or not dp or not dp.aspect then
        return  -- entre un archivo y otro: se deja como está (sin parpadeos)
    end
    local aspecto = dp.aspect
    local k = string.format("%dx%d %s %.3f", dim.w, dim.h, franja(), aspecto)
    if k == clave then return end
    if not modo_ventana() then
        local pantalla = aspecto_pantalla()
        if pantalla and math.abs(aspecto - pantalla) > 0.02 and
           math.abs(dim.w / dim.h - pantalla) > 0.02 then
            -- primero agrandar la imagen; cuando cambie el tamaño se vuelve a llamar y
            -- recién ahí se prepara el dibujo (para no hacerlo dos veces)
            agrandar(aspecto, pantalla)
            return
        end
    end
    clave = k
    datos = preparar(dim.w, dim.h, aspecto)
    local usar
    if datos and datos.modo == "ventana" then
        -- estilo Super Game Boy: el video se achica para entrar en el hueco del dibujo
        agrandar(aspecto, nil)
        local pantalla = dim.aspect or (dim.w / dim.h)
        usar = aspecto <= 1.45 or aspecto < pantalla - 0.05
    else
        -- normal: el marco tapa las franjas negras (si las hay); el video no se achica.
        -- Hay franjas si la forma del video no es la de la pantalla.
        local pantalla = aspecto_pantalla()
        local hay_franjas = pantalla ~= nil and math.abs(aspecto - pantalla) > 0.02
        agrandar(aspecto, hay_franjas and pantalla or nil)
        usar = datos ~= nil and hay_franjas
    end
    if usar then
        mp.commandv("overlay-add", tostring(ID), "0", "0", datos.archivo, "0", "bgra",
                    tostring(datos.ancho), tostring(datos.alto), tostring(datos.ancho * 4))
        if datos.modo == "ventana" then
            margenes(datos.ventana[1], datos.ventana[2], datos.ventana[3], datos.ventana[4])
        else
            margenes(0, 0, 0, 0)
        end
        avisar_ventana(datos.ventana)
    else
        mp.commandv("overlay-remove", tostring(ID))
        margenes(0, 0, 0, 0)
        avisar_ventana({ 0, 0, 0, 0 })
    end
    mostrando = usar
end

if opts.carpeta ~= "" and opts.ayudante ~= "" then
    mp.observe_property("video-dec-params", "native", aplicar)
    mp.observe_property("video-out-params", "native", aplicar)
    mp.observe_property("osd-dimensions", "native", aplicar)
    mp.add_periodic_timer(60, aplicar)  -- por si cambia la franja horaria
end
