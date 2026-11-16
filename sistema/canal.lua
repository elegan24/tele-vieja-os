-- Canal Retro: logo del canal y hora en la esquina, como la tele de antes.
-- Lo carga TeleVieja solo cuando se mira el canal.

local opts = { nombre = "FRECUENCIA 99", reloj = "si", empezado = "si", color = "&HFFFFFF&",
               presentacion = "si" }
require("mp.options").read_options(opts, "canal")

local logo = mp.create_osd_overlay("ass-events")
local cartel = mp.create_osd_overlay("ass-events")
local carta = mp.create_osd_overlay("ass-events")
carta.z = 20  -- arriba de todo
local primero = true
local timer_cartel = nil
local timer_carta = nil
local termino_programa = false  -- el archivo anterior era un programa y llegó al final
local tipo_actual = nil

-- La tele de tubo corta los bordes: dejamos un margen.
local W, H = 640, 480
local MX, MY = 46, 30

-- "tanda" (publicidad), "cortina" (presentación del canal, Canal/Cortinas) o "programa"
local function tipo_de(ruta)
    ruta = ruta or ""
    if ruta:find("/Tandas/", 1, true) then return "tanda" end
    if ruta:find("/Cortinas/", 1, true) then return "cortina" end
    return "programa"
end

local function es_tanda()  -- tanda o cortina: sin logo ni cartel
    return tipo_de(mp.get_property("path", "")) ~= "programa"
end

local function limpiar(texto)
    return ((texto or ""):gsub("[{}\\]", ""))
end

-- El próximo programa de la lista (desde el que se está por ver): "Serie", "Episodio"
local function proximo_programa()
    local pos = mp.get_property_number("playlist-pos", 0)
    local total = mp.get_property_number("playlist-count", 0)
    for i = pos, total - 1 do
        local archivo = mp.get_property("playlist/" .. i .. "/filename", "")
        if tipo_de(archivo) == "programa" then
            local titulo = mp.get_property("playlist/" .. i .. "/title", "")
            if titulo == "" then
                titulo = archivo:match("([^/]+)$"):gsub("%.[%w]+$", "")
            end
            local serie, episodio = titulo:match("^(.-) — (.+)$")
            return limpiar(serie or titulo), limpiar(episodio or "")
        end
    end
    return nil
end

-- Presentación entre programas, como las de Cartoon Network: tablero de damas que
-- se mueve y una franja con lo que viene. Los overlays de mpv no se animan solos,
-- así que se redibuja varias veces por segundo.
local DURACION = 4

local function tablero(color, inicio, corrimiento)
    local trazos = {}
    for fila = 0, 5 do
        for col = -1, 10 do
            if (fila + col) % 2 == inicio then
                local x, y = col * 80, fila * 80
                trazos[#trazos + 1] = string.format("m %d %d l %d %d %d %d %d %d ",
                    x, y, x + 80, y, x + 80, y + 80, x, y + 80)
            end
        end
    end
    return string.format("{\\an7\\pos(%d,0)\\bord0\\shad0\\1c%s\\p1}", corrimiento, color) ..
           table.concat(trazos) .. "{\\p0}"
end

local function avance(t, desde, hasta)  -- 0..1 con frenado suave al final
    local x = math.max(0, math.min(1, (t - desde) / (hasta - desde)))
    return 1 - (1 - x) * (1 - x)
end

local function dibujar_carta(t, serie, episodio)
    local tam = 46
    if #serie > 26 then tam = 28 elseif #serie > 18 then tam = 36 end
    local corrimiento = -(math.floor(t / DURACION * 160) % 160)  -- el tablero camina
    local franja = math.floor(-640 + 640 * avance(t, 0, 0.35))
    local etiqueta = math.floor(-300 + (MX + 10 + 300) * avance(t, 0.15, 0.5))
    local escala = math.floor(30 + 70 * avance(t, 0.3, 0.6))
    local opaco = math.floor(255 * (1 - avance(t, 0.55, 0.9)))
    carta.data = table.concat({
        tablero("&H101010&", 0, corrimiento),
        tablero("&HF0F0F0&", 1, corrimiento),
        string.format("{\\an7\\pos(%d,165)\\bord0\\shad0\\1c%s\\p1}m 0 0 l 640 0 640 150 0 150{\\p0}",
                      franja, opts.color),
        string.format("{\\an4\\pos(%d,190)\\fs24\\b1\\bord0\\shad0\\1c&H101010&}A CONTINUACIÓN",
                      etiqueta),
        string.format("{\\an5\\pos(320,245)\\q2\\fs%d\\b1\\bord3\\shad0\\1c&HFFFFFF&\\3c&H101010&" ..
                      "\\fscx%d\\fscy%d}%s", tam, escala, escala, serie),
        string.format("{\\an5\\pos(320,295)\\fs22\\b1\\bord0\\shad0\\1c&H101010&\\alpha&H%02X&}%s",
                      opaco, episodio),
        string.format("{\\an3\\pos(%d,%d)\\fs20\\b1\\bord2\\shad0\\1c&HFFFFFF&\\3c&H101010&}%s",
                      W - MX, H - MY, limpiar(opts.nombre)),
    }, "\n")
    carta:update()
end

local function presentar()
    local serie, episodio = proximo_programa()
    if not serie then return end
    carta.res_x, carta.res_y = W, H
    mp.set_property_bool("pause", true)
    if timer_carta then timer_carta:kill() end
    local inicio = mp.get_time()
    dibujar_carta(0, serie, episodio)
    timer_carta = mp.add_periodic_timer(1 / 15, function()
        local t = mp.get_time() - inicio
        if t >= DURACION then
            timer_carta:kill()
            timer_carta = nil
            carta:remove()
            mp.set_property_bool("pause", false)
        else
            dibujar_carta(t, serie, episodio)
        end
    end)
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

mp.register_event("end-file", function(evento)
    -- Solo si el programa terminó solo (no si hiciste zapping)
    termino_programa = evento.reason == "eof" and tipo_actual == "programa"
end)

mp.register_event("file-loaded", function()
    -- La primera vez agarrás el programa empezado, como al prender la tele.
    if primero and opts.empezado == "si" and not es_tanda() then
        math.randomseed(os.time())
        local dur = mp.get_property_number("duration", 0)
        if dur > 120 then
            mp.commandv("seek", tostring(math.random(5, 60)), "absolute-percent")
        end
    end
    local tipo = tipo_de(mp.get_property("path", ""))
    tipo_actual = tipo
    -- Terminó un programa: presentación de lo que viene (si después no hay una cortina propia)
    if not primero and termino_programa and opts.presentacion == "si" and tipo ~= "cortina" then
        presentar()
    end
    termino_programa = false
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
