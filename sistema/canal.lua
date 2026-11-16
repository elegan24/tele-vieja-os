-- Canal Retro: un canal de aire con grilla horaria.
-- El menú prepara la programación (canal.json: series, bloques de la grilla, tandas y
-- cortinas) y este script decide en vivo qué va: según el bloque al aire (mañana,
-- tarde, maratón del domingo...) elige la serie y pasa su capítulo siguiente. Entre
-- programa y programa: tandas y una cortina "A continuación".

local utils = require("mp.utils")

local opts = { nombre = "FRECUENCIA 99", reloj = "si", empezado = "si", color = "&HFFFFFF&",
               presentacion = "si", catalogo = "" }
require("mp.options").read_options(opts, "canal")

-- Capas, de abajo hacia arriba: video (con su marco, si hay) → HUD (logo y reloj) →
-- zócalo "AHORA" → cortina.
local hud = mp.create_osd_overlay("ass-events")
local cartel = mp.create_osd_overlay("ass-events")
local carta = mp.create_osd_overlay("ass-events")
hud.z, cartel.z, carta.z = 10, 11, 20
local ALTO_TELA = 480
local tela = { w = 640, h = ALTO_TELA }  -- la pantalla, en unidades virtuales
local ventana = { 0, 0, 0, 0 }            -- márgenes del video (marco): izq, arriba, der, abajo

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
-- Todo lo del canal (logo, reloj, zócalo, cortina) es una capa aparte del video: se
-- dibuja en una "tela" virtual de 480 de alto y el ancho que dé la pantalla, y se mide
-- en porcentajes de la "tele" (el video, o el hueco del marco): como vh/vmin y clamp()
-- en una página web. No cambia con la resolución de cada archivo.
local function caja()  -- x, y, ancho, alto de la tele, en la tela
    return ventana[1] * tela.w, ventana[2] * tela.h,
           tela.w * (1 - ventana[1] - ventana[3]), tela.h * (1 - ventana[2] - ventana[4])
end

local function entre(minimo, valor, maximo)  -- clamp()
    return math.max(minimo, math.min(maximo, valor))
end

local function medidas()
    local x, y, w, h = caja()
    local u = h / 100                       -- 1% del alto de la tele
    -- la tele de tubo corta los bordes: margen seguro
    -- (la tele de tubo corta un 5-7% de cada lado: el margen depende del ancho también)
    return x, y, w, h, u, entre(10, math.max(7 * u, 0.07 * w), 70), entre(8, 6 * u, 50)
end

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

local function letras(texto)  -- cantidad de letras (no de bytes)
    local _, n = texto:gsub("[^\128-\191]", "")
    return n
end

-- Recorta para que entre en "ancho" (estimado por el tamaño de letra), sin partir tildes
local function recortar(texto, ancho, tam, factor)
    local caben = math.floor(ancho / (tam * (factor or 0.56)))
    if letras(texto) <= caben then return texto end
    local salida, n = {}, 0
    for letra in texto:gmatch("[\1-\127\192-\255][\128-\191]*") do
        n = n + 1
        if n > caben - 1 then break end
        salida[#salida + 1] = letra
    end
    return table.concat(salida) .. "…"
end

local function avance(t, desde, hasta)  -- 0..1 con frenado suave al final
    local x = math.max(0, math.min(1, (t - desde) / (hasta - desde)))
    return 1 - (1 - x) * (1 - x)
end

local function recorte()  -- \clip para que nada se salga de la tele
    local x, y, w, h = caja()
    return string.format("\\clip(%.0f,%.0f,%.0f,%.0f)", math.floor(x), math.floor(y),
                         math.ceil(x + w), math.ceil(y + h))
end

-- Mosca del canal y reloj, arriba a la derecha de la tele
local function dibujar_logo()
    if not actual or actual.tipo ~= "programa" then
        hud:remove()
        return
    end
    local x, y, w, _, u, mx, my = medidas()
    local tam_logo, tam_hora = entre(14, 4.6 * u, 30), entre(12, 4.2 * u, 26)
    local estilo = "{\\an9\\pos(%.0f,%.0f)\\fs%.0f\\b1\\bord2\\shad1\\1c" .. opts.color ..
                   "\\3c&H202020&\\alpha&H60&}"
    local texto = string.format(estilo, x + w - mx, y + my, tam_logo) .. limpiar(opts.nombre)
    if opts.reloj == "si" then
        texto = texto .. "\n" .. string.format(estilo, x + w - mx, y + my + tam_logo * 1.15,
                                               tam_hora) .. os.date("%H:%M")
    end
    hud.res_x, hud.res_y = tela.w, tela.h
    hud.data = texto
    hud:update()
end

-- Zócalo "AHORA": recuadro del color del canal + título; entra deslizando y dura 6 s
local function dibujar_zocalo(t, serie_episodio)
    local x, y, w, h, u, mx, my = medidas()
    local alto = entre(18, 5.6 * u, 36)
    local ancho = alto * 3.3
    local entra = avance(t, 0, 0.35)
    local by = y + h - my - alto + math.floor(3.5 * u * (1 - entra))
    local tx = x + mx + ancho + 1.8 * u
    local tam = entre(14, 4.4 * u, 30)
    local alfa = string.format("\\alpha&H%02X&", math.floor(255 * (1 - entra)))
    local titulo = recortar(serie_episodio, x + w - mx - tx, tam)
    cartel.res_x, cartel.res_y = tela.w, tela.h
    cartel.data = table.concat({
        string.format("{\\an7\\pos(%.0f,%.0f)\\bord0\\shad0\\1c%s%s\\p1}m 0 0 l %.0f 0 %.0f %.0f 0 %.0f{\\p0}",
                      x + mx, by, opts.color, alfa, ancho, ancho, alto, alto),
        string.format("{\\an5\\pos(%.0f,%.0f)\\fs%.0f\\b1\\bord0\\shad0\\1c&H141414&%s}AHORA",
                      x + mx + ancho / 2, by + alto / 2, alto * 0.68, alfa),
        string.format("{\\an4\\pos(%.0f,%.0f)\\fs%.0f\\b1\\bord2\\shad1\\1c&HFFFFFF&\\3c&H000000&%s}%s",
                      tx, by + alto / 2, tam, alfa, titulo),
    }, "\n")
    cartel:update()
end

local function mostrar_titulo()
    if not actual or actual.tipo ~= "programa" or not actual.serie then return end
    local texto = limpiar(actual.serie .. " — " .. actual.episodio)
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

-- Cortina "A continuación" (bumper), estilo Cartoon Network: ~3 segundos. Tablero de damas
-- que camina y una franja del color del canal con la serie que viene. Si empieza otro
-- bloque, lo anuncia ("COMIENZA: MARATÓN DEL DOMINGO"). Los overlays de mpv no se animan
-- solos: se redibuja varias veces por segundo.
local DURACION = 3.2

local function tablero(color, inicio, corrimiento)
    local x, y, w, h = caja()
    local lado = h / 6
    local trazos = {}
    for fila = 0, 5 do
        for col = -1, math.ceil(w / lado) + 2 do
            if (fila + col) % 2 == inicio then
                local px, py = math.floor(col * lado), math.floor(fila * lado)
                local q = math.ceil(lado)
                trazos[#trazos + 1] = string.format("m %.0f %.0f l %.0f %.0f %.0f %.0f %.0f %.0f ",
                    px, py, px + q, py, px + q, py + q, px, py + q)
            end
        end
    end
    return string.format("{\\an7\\pos(%.0f,%.0f)%s\\bord0\\shad0\\1c%s\\p1}", x + corrimiento, y,
                         recorte(), color) .. table.concat(trazos) .. "{\\p0}"
end

local function dibujar_carta(t, encabezado, serie, episodio)
    local x, y, w, h, u, mx, my = medidas()
    local lado = h / 6
    local corrimiento = -((t / DURACION * 2 * lado) % (2 * lado))   -- el tablero camina
    local fy, falto = y + 0.344 * h, 0.3125 * h                       -- la franja
    local franja = math.floor(x - w + w * avance(t, 0, 0.3))
    local etiqueta = math.floor(x - w * 0.6 + (mx + w * 0.6) * avance(t, 0.12, 0.42))
    local escala = math.floor(30 + 70 * avance(t, 0.25, 0.5))
    local opaco = math.floor(255 * (1 - avance(t, 0.45, 0.75)))
    local tam_etiqueta = entre(12, 5 * u, 30)
    local tam_serie = math.min(entre(16, 9.2 * u, 60), (w - 2 * mx) / (letras(serie) * 0.68))
    tam_serie = math.max(entre(12, 3.6 * u, 24), tam_serie)
    local tam_ep = entre(12, 4.6 * u, 28)
    local clip = recorte()
    carta.res_x, carta.res_y = tela.w, tela.h
    carta.data = table.concat({
        tablero("&H101010&", 0, corrimiento),
        tablero("&HF0F0F0&", 1, corrimiento),
        string.format("{\\an7\\pos(%.0f,%.0f)%s\\bord0\\shad0\\1c%s\\p1}m 0 0 l %.0f 0 %.0f %.0f 0 %.0f{\\p0}",
                      franja, fy, clip, opts.color, w, w, falto, falto),
        string.format("{\\an4\\pos(%.0f,%.0f)%s\\fs%.0f\\b1\\bord0\\shad0\\1c&H101010&}%s",
                      etiqueta, fy + 0.17 * falto, clip, tam_etiqueta, encabezado),
        string.format("{\\an5\\pos(%.0f,%.0f)%s\\q2\\fs%.0f\\b1\\bord3\\shad0\\1c&HFFFFFF&\\3c&H101010&" ..
                      "\\fscx%.0f\\fscy%.0f}%s", x + w / 2, fy + 0.53 * falto, clip, tam_serie,
                      escala, escala, serie),
        string.format("{\\an5\\pos(%.0f,%.0f)%s\\fs%.0f\\b1\\bord0\\shad0\\1c&H101010&\\alpha&H%02X&}%s",
                      x + w / 2, fy + 0.87 * falto, clip, tam_ep, opaco,
                      recortar(episodio, w - 2 * mx, tam_ep)),
        string.format("{\\an3\\pos(%.0f,%.0f)%s\\fs%.0f\\b1\\bord2\\shad0\\1c&HFFFFFF&\\3c&H101010&}%s",
                      x + w - mx, y + h - my, clip, entre(12, 4.2 * u, 26), limpiar(opts.nombre)),
    }, "\n")
    carta:update()
end

-- La cortina arranca un instante ANTES de que termine lo anterior (cero cuadros negros) y
-- tapa la carga del capítulo, que espera en pausa abajo. Se va recién cuando el capítulo
-- ya tiene imagen; ahí arranca el capítulo y aparece el zócalo "AHORA".
local listo_abajo = false
local cargado_abajo = nil   -- cuándo se cargó el capítulo que espera abajo
local ya_presentado = false

local function terminar_carta()
    timer_carta:kill()
    timer_carta = nil
    carta_activa = false
    carta:remove()
    mp.set_property_bool("pause", false)
    mostrar_titulo()
end

local function presentar(prox)
    local encabezado = "A CONTINUACIÓN"
    if ultimo_bloque and prox.bloque ~= ultimo_bloque then
        encabezado = "COMIENZA: " .. mayusculas(limpiar(prox.bloque))
    end
    local serie, episodio = mayusculas(limpiar(prox.serie)), limpiar(prox.episodio)
    carta_activa, listo_abajo, ya_presentado, cargado_abajo = true, false, true, nil
    if timer_carta then timer_carta:kill() end
    local inicio = mp.get_time()
    dibujar_carta(0, encabezado, serie, episodio)
    timer_carta = mp.add_periodic_timer(1 / 15, function()
        local t = mp.get_time() - inicio
        -- listo: mpv avisó que hay imagen, o ya pasó un ratito desde que cargó
        local listo = listo_abajo or (cargado_abajo and mp.get_time() - cargado_abajo > 0.6)
        if t >= DURACION and (listo or t >= DURACION + 8) then
            terminar_carta()
        else
            dibujar_carta(math.min(t, DURACION), encabezado, serie, episodio)
        end
    end)
end

local function intentar_cortina()
    -- Lo que sigue es un programa y lo que termina no es una cortina propia (esa ya hizo
    -- de presentación): va el bumper.
    local prox = cola[1]
    if not carta_activa and not ya_presentado and not primero and opts.presentacion == "si"
       and prox and prox.tipo == "programa" and actual and actual.tipo ~= "cortina" then
        presentar(prox)
    end
end

-- --- eventos ----------------------------------------------------------------------
local zocalo_pendiente = false

mp.observe_property("time-remaining", "number", function(_, quedan)
    if quedan and quedan <= 0.3 and not mp.get_property_bool("pause", false) then
        intentar_cortina()
    end
end)

mp.register_event("end-file", function(evento)
    if evento.reason == "eof" then intentar_cortina() end  -- por si no llegó a avisar antes
end)

mp.register_event("file-loaded", function()
    local ruta = mp.get_property("path", "")
    if #cola > 0 then table.remove(cola, 1) end
    actual = info[ruta] or { tipo = tipo_de(ruta) }
    ya_presentado = false
    if carta_activa then
        mp.set_property_bool("pause", true)  -- espera abajo de la cortina
        cargado_abajo = mp.get_time()
    end
    zocalo_pendiente = false
    if actual.tipo ~= "programa" and timer_cartel then  -- en las tandas, sin zócalo
        timer_cartel:kill()
        timer_cartel = nil
        cartel:remove()
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
        zocalo_pendiente = not carta_activa  -- sin cortina: el zócalo cuando haya imagen
    end
    primero = false
    dibujar_logo()
end)

mp.register_event("video-reconfig", function()
    if carta_activa and cargado_abajo then listo_abajo = true end
end)

mp.register_event("playback-restart", function()
    -- ya hay imagen del archivo nuevo
    if carta_activa then listo_abajo = true end
    if zocalo_pendiente then
        zocalo_pendiente = false
        mostrar_titulo()
    end
end)

mp.add_periodic_timer(10, dibujar_logo)

local function redibujar()
    dibujar_logo()
end

mp.observe_property("osd-dimensions", "native", function(_, dim)
    if dim and dim.w and dim.w > 0 and dim.h > 0 then
        tela.w = math.floor(ALTO_TELA * dim.w / dim.h)
        redibujar()
    end
end)

-- marco.lua avisa dónde quedó el video (márgenes: izquierda, arriba, derecha, abajo)
mp.register_script_message("marco-ventana", function(izq, arriba, der, abajo)
    ventana = { tonumber(izq) or 0, tonumber(arriba) or 0, tonumber(der) or 0,
                tonumber(abajo) or 0 }
    redibujar()
end)

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
