-- Canal Retro: logo del canal y hora en la esquina, como la tele de antes.
-- Lo carga TeleVieja solo cuando se mira el canal.

local opts = { nombre = "TELE VIEJA", reloj = "si", empezado = "si", color = "&HFFFFFF&" }
require("mp.options").read_options(opts, "canal")

local logo = mp.create_osd_overlay("ass-events")
local cartel = mp.create_osd_overlay("ass-events")
local primero = true
local timer_cartel = nil

-- La tele de tubo corta los bordes: dejamos un margen.
local W, H = 640, 480
local MX, MY = 46, 30

local function es_tanda()
    local p = mp.get_property("path", "") or ""
    return p:find("/Tandas/", 1, true) ~= nil
end

local function dibujar_logo()
    if es_tanda() then
        logo:remove()
        return
    end
    logo.res_x, logo.res_y = W, H
    -- el color del logo lo pone el tema del menú
    local estilo = "{\\an9\\pos(%d,%d)\\fs%d\\b1\\bord2\\shad1\\1c" .. opts.color ..
                   "\\3c&H202020&\\alpha&H60&}"
    local texto = string.format(estilo, W - MX, MY, 22) .. opts.nombre
    if opts.reloj == "si" then
        texto = texto .. "\n" .. string.format(estilo, W - MX, MY + 26, 20) .. os.date("%H:%M")
    end
    logo.data = texto
    logo:update()
end

local function mostrar_titulo()
    if es_tanda() then return end
    local titulo = mp.get_property("media-title", "") or ""
    titulo = titulo:gsub("%.[%w]+$", ""):gsub("[{}\\]", "")
    cartel.res_x, cartel.res_y = W, H
    cartel.data = string.format(
        "{\\an1\\pos(%d,%d)\\fs22\\b1\\bord2\\1c&H40D4FF&\\3c&H101010&}AHORA: {\\1c&HFFFFFF&}%s",
        MX, H - MY, titulo)
    cartel:update()
    if timer_cartel then timer_cartel:kill() end
    timer_cartel = mp.add_timeout(5, function() cartel:remove() end)
end

mp.register_event("file-loaded", function()
    -- La primera vez agarrás el programa empezado, como al prender la tele.
    if primero and opts.empezado == "si" and not es_tanda() then
        math.randomseed(os.time())
        local dur = mp.get_property_number("duration", 0)
        if dur > 120 then
            mp.commandv("seek", tostring(math.random(5, 60)), "absolute-percent")
        end
    end
    primero = false
    dibujar_logo()
    mostrar_titulo()
end)

mp.add_periodic_timer(10, dibujar_logo)

-- En el canal las flechas hacen "zapping" en vez de adelantar el video.
local function siguiente() mp.command("playlist-next") end
local function que_dan() mp.commandv("show-text", "${media-title}", "3000") end
mp.add_forced_key_binding("RIGHT", "canal-siguiente", siguiente)
mp.add_forced_key_binding("CHANNEL_UP", "canal-siguiente-ch", siguiente)
mp.add_forced_key_binding("NEXT", "canal-siguiente-next", siguiente)
mp.add_forced_key_binding("LEFT", "canal-que-dan", que_dan)
mp.add_forced_key_binding("ENTER", "canal-que-dan-ok", que_dan)
