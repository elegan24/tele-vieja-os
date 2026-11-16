-- Canal Retro: un canal de aire con grilla horaria.
-- El menú prepara la programación (canal.json: series, bloques de la grilla, tandas y
-- cortinas) y este script decide en vivo qué va: según el bloque al aire (mañana,
-- tarde, maratón del domingo...) elige la serie y pasa su capítulo siguiente. Entre
-- programa y programa: tandas y una cortina "A continuación".

local utils = require("mp.utils")

local opts = { nombre = "FRECUENCIA 99", reloj = "si", empezado = "si", color = "&HFFFFFF&",
               presentacion = "si", catalogo = "" }
require("mp.options").read_options(opts, "canal")

local logo = mp.create_osd_overlay("ass-events")
local cartel = mp.create_osd_overlay("ass-events")
local carta = mp.create_osd_overlay("ass-events")
carta.z = 20  -- arriba de todo

-- La tele de tubo corta los bordes: dejamos un margen.
local W, H = 640, 480
local MX, MY = 46, 30

local cat = nil           -- la programación
local estado = { punteros = {} }  -- por qué capítulo va cada serie
local info = {}           -- ruta -> { tipo, serie, episodio, indice, bloque }
local primero = true
local actual = nil        -- info del archivo que se está viendo
local ultima_serie = nil
local ultimo_bloque = nil
local cola = {}           -- lo que viene después de lo que se está viendo, en orden
local carta_activa = false
local timer_cartel, timer_carta = nil, nil

math.randomseed(os.time())

-- --- programación --------------------------------------------------------------
local function leer_json(ruta)
    local f = ruta ~= "" and io.open(ruta, "r")
    if not f then return nil end
    local texto = f:read("*a")
    f:close()
    return utils.parse_json(texto)
end

local function guardar_estado()
    if not cat or not cat.estado then return end
    local f = io.open(cat.estado .. ".tmp", "w")
    if not f then return end
    local texto = utils.format_json(estado)  -- (devuelve también un error vacío)
    f:write(texto or "{}")
    f:close()
    os.rename(cat.estado .. ".tmp", cat.estado)
end

-- Bloque al aire en ese momento (os.time()): el último que arrancó en la semana.
local function bloque_en(cuando)
    local t = os.date("*t", cuando)
    local dia = (t.wday + 5) % 7  -- 0 = lunes ... 6 = domingo
    local minuto = dia * 1440 + t.hour * 60 + t.min
    local semana = cat.semana
    local elegido = semana[#semana][2]  -- antes del primero del lunes: el último del domingo
    for _, e in ipairs(semana) do
        if e[1] <= minuto then elegido = e[2] else break end
    end
    return cat.bloques[elegido + 1]
end

local function al_azar(lista)
    return lista[math.random(#lista)]
end

-- El programa que va en ese momento: serie según el bloque, y su capítulo siguiente.
local function elegir_programa(cuando)
    local b = bloque_en(cuando)
    local opciones = {}
    for _, s in ipairs(b.series) do
        if cat.series[s] then opciones[#opciones + 1] = s end
    end
    if #opciones == 0 then
        for s, _ in pairs(cat.series) do opciones[#opciones + 1] = s end
    end
    local serie
    if b.tipo == "maraton" then
        serie = opciones[1]
    else
        local otras = {}  -- que no se repita la misma serie dos veces seguidas
        for _, s in ipairs(opciones) do
            if s ~= ultima_serie then otras[#otras + 1] = s end
        end
        serie = al_azar(#otras > 0 and otras or opciones)
    end
    local eps = cat.series[serie]
    local i = (estado.punteros[serie] or 0) % #eps  -- terminada la serie, vuelve a empezar
    local ep = eps[i + 1]
    info[ep.ruta] = { tipo = "programa", serie = serie, episodio = ep.titulo, indice = i,
                      bloque = b.nombre }
    return ep.ruta
end

local function tipo_de(ruta)
    local i = info[ruta or ""]
    if i then return i.tipo end
    ruta = ruta or ""
    if ruta:find("/Tandas/", 1, true) then return "tanda" end
    if ruta:find("/Cortinas/", 1, true) then return "cortina" end
    return "programa"
end

-- Después del programa que empieza: tandas, cortina y el programa que sigue (elegido
-- para la hora en que va a empezar, por si cambia el bloque).
local function encolar_lo_que_sigue()
    mp.commandv("playlist-clear")  -- deja solo lo que se está viendo
    cola = {}
    local dur = mp.get_property_number("duration", 1800)
    local pos = mp.get_property_number("time-pos", 0)
    local cuando = os.time() + math.max(0, dur - pos) + 30 * cat.por_corte
    if #cat.tandas > 0 then
        for _ = 1, cat.por_corte do
            local t = al_azar(cat.tandas)
            info[t] = { tipo = "tanda" }
            cola[#cola + 1] = info[t]
            mp.commandv("loadfile", t, "append")
        end
    end
    if #cat.cortinas > 0 then
        local c = al_azar(cat.cortinas)
        info[c] = { tipo = "cortina" }
        cola[#cola + 1] = info[c]
        mp.commandv("loadfile", c, "append")
    end
    local prog = elegir_programa(cuando)
    cola[#cola + 1] = info[prog]
    mp.commandv("loadfile", prog, "append")
end

-- --- en pantalla ------------------------------------------------------------------
local function limpiar(texto)
    return ((texto or ""):gsub("[{}\\]", ""))
end

-- upper() de Lua no sabe de tildes ni eñes
local MAYUSCULAS = { ["á"] = "Á", ["é"] = "É", ["í"] = "Í", ["ó"] = "Ó", ["ú"] = "Ú",
                     ["ñ"] = "Ñ", ["ü"] = "Ü" }
local function mayusculas(texto)
    texto = texto:upper()
    for chica, grande in pairs(MAYUSCULAS) do
        texto = texto:gsub(chica, grande)
    end
    return texto
end

local function dibujar_logo()
    if not actual or actual.tipo ~= "programa" then
        logo:remove()
        return
    end
    logo.res_x, logo.res_y = W, H
    -- el color del logo lo pone el tema del menú
    local estilo = "{\\an9\\pos(%d,%d)\\fs%d\\b1\\bord2\\shad1\\1c" .. opts.color ..
                   "\\3c&H202020&\\alpha&H60&}"
    local texto = string.format(estilo, W - MX, MY, 22) .. limpiar(opts.nombre)
    if opts.reloj == "si" then
        texto = texto .. "\n" .. string.format(estilo, W - MX, MY + 26, 20) .. os.date("%H:%M")
    end
    logo.data = texto
    logo:update()
end

-- Recorta sin partir una letra con tilde (UTF-8)
local function recortar(texto, n)
    if #texto <= n then return texto end
    local corte = n
    while corte > 0 and (texto:byte(corte + 1) or 0) >= 128 and (texto:byte(corte + 1) or 0) < 192 do
        corte = corte - 1
    end
    return texto:sub(1, corte) .. "…"
end

local function avance(t, desde, hasta)  -- 0..1 con frenado suave al final
    local x = math.max(0, math.min(1, (t - desde) / (hasta - desde)))
    return 1 - (1 - x) * (1 - x)
end

-- Zócalo "AHORA": recuadro del color del canal + título, entra deslizando y dura 6 segundos
local function dibujar_zocalo(t, texto)
    local entra = avance(t, 0, 0.35)
    local y = H - MY - 26 + math.floor(18 * (1 - entra))
    local alfa = string.format("\\alpha&H%02X&", math.floor(255 * (1 - entra)))
    cartel.data = table.concat({
        string.format("{\\an7\\pos(%d,%d)\\bord0\\shad0\\1c%s%s\\p1}m 0 0 l 86 0 86 26 0 26{\\p0}",
                      MX, y, opts.color, alfa),
        string.format("{\\an5\\pos(%d,%d)\\fs18\\b1\\bord0\\shad0\\1c&H141414&%s}AHORA",
                      MX + 43, y + 13, alfa),
        string.format("{\\an4\\pos(%d,%d)\\fs21\\b1\\bord2\\shad1\\1c&HFFFFFF&\\3c&H000000&%s}%s",
                      MX + 96, y + 13, alfa, texto),
    }, "\n")
    cartel:update()
end

local function mostrar_titulo()
    if not actual or actual.tipo ~= "programa" or not actual.serie then return end
    local texto = recortar(limpiar(actual.serie .. " — " .. actual.episodio), 48)
    cartel.res_x, cartel.res_y = W, H
    if timer_cartel then timer_cartel:kill() end
    local inicio = mp.get_time()
    dibujar_zocalo(0, texto)
    timer_cartel = mp.add_periodic_timer(1 / 15, function()
        local t = mp.get_time() - inicio
        if t >= 6 then
            timer_cartel:kill()
            timer_cartel = nil
            cartel:remove()
        elseif t <= 0.4 then
            dibujar_zocalo(t, texto)
        end
    end)
end

-- Cortina "A continuación", como las de Cartoon Network: tablero de damas que camina y
-- una franja con lo que viene. Si empieza otro bloque, lo anuncia ("MARATÓN DEL DOMINGO").
-- Los overlays de mpv no se animan solos: se redibuja varias veces por segundo.
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

local function dibujar_carta(t, encabezado, serie, episodio)
    local tam = 44
    if #serie > 24 then tam = 26 elseif #serie > 16 then tam = 34 end
    local corrimiento = -(math.floor(t / DURACION * 160) % 160)
    local franja = math.floor(-640 + 640 * avance(t, 0, 0.35))
    local etiqueta = math.floor(-400 + (MX + 10 + 400) * avance(t, 0.15, 0.5))
    local escala = math.floor(30 + 70 * avance(t, 0.3, 0.6))
    local opaco = math.floor(255 * (1 - avance(t, 0.55, 0.9)))
    carta.data = table.concat({
        tablero("&H101010&", 0, corrimiento),
        tablero("&HF0F0F0&", 1, corrimiento),
        string.format("{\\an7\\pos(%d,165)\\bord0\\shad0\\1c%s\\p1}m 0 0 l 640 0 640 150 0 150{\\p0}",
                      franja, opts.color),
        string.format("{\\an4\\pos(%d,190)\\fs24\\b1\\bord0\\shad0\\1c&H101010&}%s",
                      etiqueta, encabezado),
        string.format("{\\an5\\pos(320,245)\\q2\\fs%d\\b1\\bord3\\shad0\\1c&HFFFFFF&\\3c&H101010&" ..
                      "\\fscx%d\\fscy%d}%s", tam, escala, escala, serie),
        string.format("{\\an5\\pos(320,295)\\fs22\\b1\\bord0\\shad0\\1c&H101010&\\alpha&H%02X&}%s",
                      opaco, episodio),
        string.format("{\\an3\\pos(%d,%d)\\fs20\\b1\\bord2\\shad0\\1c&HFFFFFF&\\3c&H101010&}%s",
                      W - MX, H - MY, limpiar(opts.nombre)),
    }, "\n")
    carta:update()
end

-- El bumper arranca apenas termina lo anterior y tapa la carga del capítulo, que
-- espera en pausa abajo: nunca queda la pantalla en negro. Al irse, el zócalo "AHORA".
local function presentar(prox)
    local encabezado = "A CONTINUACIÓN"
    if ultimo_bloque and prox.bloque ~= ultimo_bloque then
        encabezado = "COMIENZA: " .. mayusculas(limpiar(prox.bloque))
    end
    local serie, episodio = mayusculas(limpiar(prox.serie)), limpiar(prox.episodio)
    carta.res_x, carta.res_y = W, H
    carta_activa = true
    if timer_carta then timer_carta:kill() end
    local inicio = mp.get_time()
    dibujar_carta(0, encabezado, serie, episodio)
    timer_carta = mp.add_periodic_timer(1 / 15, function()
        local t = mp.get_time() - inicio
        if t >= DURACION then
            timer_carta:kill()
            timer_carta = nil
            carta_activa = false
            carta:remove()
            mp.set_property_bool("pause", false)
            mostrar_titulo()
        else
            dibujar_carta(t, encabezado, serie, episodio)
        end
    end)
end

-- --- eventos ----------------------------------------------------------------------
mp.register_event("end-file", function(evento)
    -- Terminó solo (no zapping) y lo que sigue es un programa: bumper, salvo que lo que
    -- terminó haya sido una cortina propia (ya hizo de presentación).
    local prox = cola[1]
    if evento.reason == "eof" and not primero and opts.presentacion == "si" and prox
       and prox.tipo == "programa" and actual and actual.tipo ~= "cortina" then
        presentar(prox)
    end
end)

mp.register_event("file-loaded", function()
    local ruta = mp.get_property("path", "")
    if #cola > 0 then table.remove(cola, 1) end
    actual = info[ruta] or { tipo = tipo_de(ruta) }
    if carta_activa then
        mp.set_property_bool("pause", true)  -- espera abajo del bumper
    end
    if actual.tipo == "programa" and actual.serie then
        -- La primera vez agarrás el programa empezado, como al prender la tele.
        if primero and opts.empezado == "si" then
            local dur = mp.get_property_number("duration", 0)
            if dur > 120 then
                mp.commandv("seek", tostring(math.random(5, 60)), "absolute-percent")
            end
        end
        estado.punteros[actual.serie] = actual.indice + 1
        ultima_serie = actual.serie
        ultimo_bloque = actual.bloque
        guardar_estado()
        encolar_lo_que_sigue()
        if not carta_activa then mostrar_titulo() end
    end
    primero = false
    dibujar_logo()
end)

mp.add_periodic_timer(10, dibujar_logo)

-- Zapping: otro programa del bloque, sin cortina ni tandas
local function zapping()
    if not cat then return end
    if timer_carta then
        timer_carta:kill()
        timer_carta = nil
        carta:remove()
        mp.set_property_bool("pause", false)
    end
    carta_activa = false
    cola = {}
    mp.commandv("loadfile", elegir_programa(os.time()), "replace")
end
local function que_dan()
    if actual and actual.serie then
        mp.osd_message(limpiar(actual.bloque .. ": " .. actual.serie .. " — " .. actual.episodio), 3)
    end
end
mp.register_script_message("canal-zapping", zapping)
mp.add_forced_key_binding("RIGHT", "canal-siguiente", zapping)
mp.add_forced_key_binding("CHANNEL_UP", "canal-siguiente-ch", zapping)
mp.add_forced_key_binding("NEXT", "canal-siguiente-next", zapping)
mp.add_forced_key_binding("LEFT", "canal-que-dan", que_dan)
mp.add_forced_key_binding("ENTER", "canal-que-dan-ok", que_dan)
mp.register_script_message("canal-que-dan", que_dan)

-- --- arranque ----------------------------------------------------------------------
cat = leer_json(opts.catalogo)
if not cat or not cat.series or not cat.semana or #cat.semana == 0 then
    mp.osd_message("No encontré la programación del canal", 5)
    cat = nil
else
    estado = leer_json(cat.estado) or {}
    estado.punteros = estado.punteros or {}
    mp.commandv("loadfile", elegir_programa(os.time()), "replace")
end
