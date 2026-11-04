-- MT2009_PLUS_FISHING_GLOBAL_V1: fishing as on the global server (the owner, 4 November 2026:
-- cache/yohara/decyzje-lowienie-mikstury.md "£owienie" 1-13, cache/yohara/lowienie-analiza.md). Replaces the package's
-- quest/libs/fishing/fishing.lua (game/Dockerfile; CP1250). The catch table: fishing_drop.lua.
--   * the rod's level 1-20 = value0 / 10 (Wêdka+1 ... Wêdka+20, yohara_lowienie.sql), Wêdka Wêglowa 22;
--   * the rare fish only with Rybie Wnêtrznoœci (the premium, or 71008 / 72013-72015 worn) or the golden tuna's bonus
--     (affect 742: value 200 - the 60 minutes of a release, 250 - the 5 minutes of the bait);
--   * Z³oty Tuñczyk once a day a character (from midnight, Polish time), not while its bonus runs, never for a bot;
--   * the Rybak's dialog (quest rybak_wedki): the free upgrade (value3 %: +1 100 %, then 39 %; a failure takes 10 % of
--     the points - fishing.cpp RealRefineRod, server-patches/fishglobal), Wêdka Wêglowa's recipe (his crafting window,
--     cube.lowienie.txt);
--   * the golden tuna (quest zloty_tunczyk, Owsap's golden_tuna ported): release / cut / bait.
fishing_manage = {}

FISHING_ROD_VALUE_BONUS = 0
FISHING_ROD_CHANCE_NEXT_POINT = 1
FISHING_ROD_NEEDED_POINTS = 2
FISHING_ROD_CHANGE_TO_REFINE = 3
FISHING_ROD_REDUCE_VNUM = 4
FISHING_ROD_BONUS_FISH_CHANCE = 5

FISHING_ROD_SOCKET_CURRENT_POINTS = 0
-- FISHING_ROD_SOCKET_UNUSED = 1
FISHING_ROD_SOCKET_BAIT = 2

fishing_manage.CARBON_ROD = 27591
fishing_manage.GOLDEN_TUNA = 27797
fishing_manage.KELPIE_CHEST = 27625
fishing_manage.AFFECT_GOLD_TUNA = 742       -- fish_global.cpp FISHGLOBAL_AFFECT_GOLD_TUNA
fishing_manage.AFFECT_WET_CLOTHES = 743     -- Mokre Szaty
fishing_manage.TUNA_LONG = 200              -- the rare fish x2 (60 minutes)
fishing_manage.TUNA_SHORT = 250             -- the rare fish x2.5 (5 minutes)
fishing_manage.MIND = 200                   -- Rybie Wnêtrznoœci: the rare fish x2
fishing_manage.MIND_VNUMS = {[71008] = true, [72013] = true, [72014] = true, [72015] = true}
local POINT_NONE_ = 0
local POINT_MOV_SPEED_ = 19

local function rod_level()
    if item.select_wear(WEAR_WEAPON) then
        if item.get_type() != ITEM_ROD then
            return 0
        end
        local level = math.floor(item.get_value(FISHING_ROD_VALUE_BONUS) / 10)
        if level < 1 then
            level = 1
        end
        return level
    end
    return 0
end

local function has_mind()
    if pc.get_premium_remain_sec(PREMIUM_FISH_MIND) > 0 then
        return true
    end
    if item.select_wear(WEAR_UNIQUE1) and fishing_manage.MIND_VNUMS[item.get_vnum()] then
        return true
    end
    if item.select_wear(WEAR_UNIQUE2) and fishing_manage.MIND_VNUMS[item.get_vnum()] then
        return true
    end
    return false
end

local function tuna_bonus()
    local v = pc.get_affect_value(fishing_manage.AFFECT_GOLD_TUNA)
    if v == nil then
        return 0
    end
    return v
end

-- the rare fish's multiplier x100: 0 - no rare fish at all
local function rare_mult()
    local m = 0
    if has_mind() then
        m = fishing_manage.MIND
    end
    local t = tuna_bonus()
    if t > m then
        m = t
    end
    return m
end

-- the day number in Poland (CET, CEST from the last Sunday of March to the last Sunday of October, 01:00 UTC)
local function last_sunday(year, month, days)
    local t = os.time({year = year, month = month, day = days, hour = 12})
    local w = os.date("!*t", t).wday     -- 1 = Sunday
    return days - (w - 1)
end

local function poland_day()
    local t = get_time()
    local u = os.date("!*t", t)
    local cest = false
    if u.month > 3 and u.month < 10 then
        cest = true
    elseif u.month == 3 then
        local s = last_sunday(u.year, 3, 31)
        cest = u.day > s or (u.day == s and u.hour >= 1)
    elseif u.month == 10 then
        local s = last_sunday(u.year, 10, 31)
        cest = u.day < s or (u.day == s and u.hour < 1)
    end
    local off = 3600
    if cest then
        off = 7200
    end
    return math.floor((t + off) / 86400)
end

local function tuna_ok()
    if pc.is_playerbot() then
        return false
    end
    if pc.has_affect(fishing_manage.AFFECT_GOLD_TUNA) then
        return false
    end
    return pc.getf("fishing", "tuna_day") != poland_day()
end

local function context()
    return {level = rod_level(), rare = rare_mult(), tuna = tuna_ok()}
end

local function can_predict()
    return pc.has_affect(AFFECT_FISH_MIND_PILL) or has_mind() or tuna_bonus() > 0
end

local function get_fishing_chance()
    local chance = 20
    if pc.has_affect(AFFECT_FISH_MIND_PILL) then
        chance = chance + 2
    end

    if has_mind() or tuna_bonus() > 0 then
        chance = chance + 10
    end

    if item.select_wear(WEAR_WEAPON) then
        if item.get_type() != ITEM_ROD then
            return 0
        end
        chance = chance + item.get_value(FISHING_ROD_BONUS_FISH_CHANCE)
    end

    return chance
end

local function simulate_fishing(count, chanceToFailGame, fish_chance)
    chanceToFailGame = chanceToFailGame or 1
    fish_chance = fish_chance or get_fishing_chance()

    local fail = 0
    local failed_games = 0
    local chance_bonus = 0
    local ctx = context()
    for i=1, count do
        if number(1,100) <= fish_chance + chance_bonus then
            if number(1,1000) > chanceToFailGame then
                local drop = fishing_drop.get_random_drop(ctx)
                if drop != nil then
                    pc.give_item2(drop.itemVnum, drop.itemCount)
                end
                chance_bonus = 0
            else
                failed_games = failed_games + 1
            end
        else
            chance_bonus = math.min(chance_bonus+2, math.max(25 - math.floor(fish_chance / 2)))
            fail = fail + 1
        end
        pc.practice_fishing()
    end
    local total_fails = fail + failed_games
    local total_success = count - total_fails
    debug("### FISHING SIMULATION RESULTS ###")
    debug("Rod level %d, rare x%d, tuna %s", ctx.level, ctx.rare, tostring(ctx.tuna))
    debug("Attempts: %d (fishing chance %d%%) (game fail chance %.1f%%)", count, fish_chance, chanceToFailGame/10)
    debug("Fails in total: %d (normal fails %d) (game fails %d)", total_fails, fail, failed_games)
    debug("Success %d", total_success)
    debug("#########")
end

local function simulate_calm()
    local r = number(1,100)
    if r <= 50 then
        syschat(get_lctext("You find a simple Piece of Stone in the Clam."))
        pc.give_item2(27990)
    else
        local prob_table = {95, 97, 99}

        if r <= prob_table[1] then
            syschat(get_lctext("The Clam has vanished."))
        elseif r <= prob_table[2] then
            syschat(get_lctext("There is a White Pearl inside the Clam."))
            pc.give_item2(27992);
        elseif r <= prob_table[3] then
            syschat(get_lctext("There is a Blue Pearl inside the Clam."))
            pc.give_item2(27993);
        else
            syschat(get_lctext("There is a Blood-Red Pearl inside the Clam."))
            pc.give_item2(27994);
        end
    end
end

local function success()
    local dropIndex = pc.getf("fishing", "drop_index")
    local drop = fishing_drop.get_drop_by_index(dropIndex)
    if drop == nil then
        debug("FISHING DROP ERROR")
        syschat("Wystapil blad (fishing_drop_success).")
        return
    end

    if drop.itemVnum == fishing_manage.GOLDEN_TUNA then
        if not tuna_ok() then
            syschat("Z³oty Tuñczyk zerwa³ siê z haczyka.")
            return
        end
        pc.setf("fishing", "tuna_day", poland_day())
        syschat("Z³owi³eœ Z³otego Tuñczyka! Kliknij go prawym przyciskiem myszy: wypuœæ go, pokrój albo u¿yj jako przynêty.")
        pc.fishing_log(drop.itemVnum, 1)
        pc.give_item2(drop.itemVnum, 1, -1, true)
        return
    end

    local localeText = ""
    if item.proto_get_type(drop.itemVnum) == ITEM_FISH then
        localeText = get_lctext("FISHING_SUCCESS2")
    else
        localeText = get_lctext("FISHING_SUCCESS1")
    end

    local dropItem = drop.itemVnum
    syschat(string.format(localeText, item.proto_get_name(drop.itemVnum)))
    pc.fishing_log(dropItem, drop.itemCount)
    pc.give_item2(dropItem, drop.itemCount, -1, true)
end

local function predict_fish()
    local drop = fishing_drop.get_random_drop(context())
    if drop == nil then
        debug("FISHING DROP ERROR")
        syschat("Wystapil blad (kod: fishing_predict).")
        return
    end
    debug("predict vnum: %s, itemCount: %d", tostring(drop.itemVnum), drop.itemCount)
    pc.setf("fishing", "drop_index", drop.index, true)

    if can_predict() then
        local localeText = ""
        if item.proto_get_type(drop.itemVnum) == ITEM_FISH or drop.itemVnum == fishing_manage.GOLDEN_TUNA then
            localeText = get_lctext("FISHING_NOTIFY2")
        else
            localeText = get_lctext("FISHING_NOTIFY1")
        end
        syschat(string.format(localeText, drop.name))
    else
        syschat(get_lctext("FISHING_UNKNOWN"))
    end
end

-- the Rybak takes a rod (quest rybak_wedki, "when 9009.take"): the free upgrade as on the global server
local function take_rod()
    say_title(mob_name(9009)..":")
    if item.get_type() != ITEM_ROD then
        say("Przynieœ mi wêdkê, a zobaczê, czy da siê j¹ ulepszyæ.")
        return
    end
    local vnum = item.get_vnum()
    if vnum == fishing_manage.CARBON_ROD then
        say("Wêdki Wêglowej nie da siê ulepszyæ - lepszej wêdki nie znam.")
        return
    end
    local next_vnum = item.get_refine_vnum()
    if next_vnum == 0 then
        say("To Wêdka+20 - lepszej zwyk³ej wêdki nie zrobiê.")
        say("Lepsza jest tylko Wêdka Wêglowa: zrobiê ci j¹ z Wêdziska, Przelotki, Rêkojeœci i 3 W³ókien Wêglowych.")
        return
    end
    local points = item.get_socket(FISHING_ROD_SOCKET_CURRENT_POINTS)
    local need = item.get_value(FISHING_ROD_NEEDED_POINTS)
    if points < need then
        say(string.format("Twoja %s ma %d z %d punktów.", item.get_name(), points, need))
        say("£ów dalej - gdy zbierzesz wszystkie punkty, ulepszê j¹ za darmo.")
        return
    end
    local chance = item.get_value(FISHING_ROD_CHANGE_TO_REFINE)
    local cell = item.get_cell()
    say(string.format("Twoja %s ma wszystkie punkty (%d/%d). Ulepszê j¹ za darmo na %s.", item.get_name(), points,
        need, item.proto_get_name(next_vnum)))
    say(string.format("Szansa powodzenia: %d%%. Jeœli siê nie uda, wêdka zostanie, ale straci 10%% punktów.", chance))
    say("Wêdka musi byæ w ekwipunku (nie w rêku).")
    if select("Ulepsz wêdkê za darmo", "Nie teraz") != 1 then
        return
    end
    local r = __fish_real_refine_rod(cell)
    say_title(mob_name(9009)..":")
    if r == 1 then
        say(string.format("Uda³o siê! Masz teraz %s.", item.proto_get_name(next_vnum)))
    elseif r == 0 then
        say("Niestety, tym razem siê nie uda³o. Wêdka straci³a 10% punktów - ³ów dalej i spróbuj ponownie.")
    else
        say("Nie mogê teraz ulepszyæ tej wêdki. Zdejmij j¹ z rêki i przynieœ jeszcze raz.")
    end
end

-- Wêdka Wêglowa at the Rybak (quest rybak_wedki): the recipe and his crafting window (cube.lowienie.txt)
local function carbon_rod_talk()
    say_title(mob_name(9009)..":")
    say("Wêdka Wêglowa to najlepsza wêdka, jak¹ znam - ³owi jak wêdka +22 i daje 12% wiêcej brañ.")
    say("Zrobiê ci j¹ z: Wêdziska, Przelotki, Rêkojeœci i 3 W³ókien Wêglowych (szansa 100%, bez Yang).")
    say("Materia³y znajdziesz w Skrzyni Nimfy Wodnej (otwiera j¹ Klucz Nimfy Wodnej). Wêdka dzia³a 30 dni")
    say("- czas p³ynie tak¿e poza gr¹ - potem znika. Nie da siê jej ulepszyæ ani przekazaæ.")
    say("")
    if select("Otwórz okno wytwarzania", "Anuluj") == 1 then
        setskin(NOWINDOW)
        command("cube open")
    end
end

-- Z³oty Tuñczyk used (quest zloty_tunczyk, "when 27797.use"): Owsap's golden_tuna - release / cut / bait
local function golden_tuna()
    say_title("Z³oty Tuñczyk")
    say("Jego ³uski b³yszcz¹ niczym p³ynne z³oto! Co z nim zrobisz?")
    say("- Wypuœæ: zwykle zmokniesz (Mokre Szaty: -50 szybkoœci ruchu na 5 minut), czasem dostaniesz Bonus Z³otego")
    say("  Tuñczyka na 60 minut (rzadkie ryby jak z Rybimi Wnêtrznoœciami).")
    say("- Pokrój: mo¿e coœ w nim znajdziesz (bardzo rzadko nawet Wêdkê Wêglow¹).")
    say("- U¿yj jako przynêty: Bonus Z³otego Tuñczyka na 5 minut - silniejszy.")
    local s = select("Wypuœæ", "Pokrój", "U¿yj jako przynêty", "Anuluj")
    if s < 1 or s > 3 then
        return
    end
    if pc.count_item(fishing_manage.GOLDEN_TUNA) < 1 then
        return
    end
    pc.remove_item(fishing_manage.GOLDEN_TUNA, 1)
    say_title("Z³oty Tuñczyk")
    if s == 1 then
        if number(1, 100) <= 30 then
            affect.remove(fishing_manage.AFFECT_GOLD_TUNA)
            affect.add_new(fishing_manage.AFFECT_GOLD_TUNA, POINT_NONE_, fishing_manage.TUNA_LONG, 3600)
            say("Tuñczyk odp³yn¹³, a na po¿egnanie obdarzy³ ciê swoim blaskiem.")
            say_reward("Bonus Z³otego Tuñczyka: 60 minut.")
        else
            affect.remove(fishing_manage.AFFECT_WET_CLOTHES)
            affect.add_new(fishing_manage.AFFECT_WET_CLOTHES, POINT_MOV_SPEED_, -50, 300)
            say("Tuñczyk szarpn¹³ siê i ochlapa³ ciê od stóp do g³ów.")
            say_reward("Mokre Szaty: -50 szybkoœci ruchu na 5 minut.")
        end
    elseif s == 2 then
        local r = number(1, 100)
        local give = 0
        if r <= 1 then
            give = fishing_manage.CARBON_ROD
        elseif r <= 17 then
            give = 27993        -- Niebieska Per³a
        elseif r <= 29 then
            give = 27992        -- Bia³a Per³a
        elseif r <= 44 then
            give = fishing_manage.KELPIE_CHEST
        elseif r <= 64 then
            give = 27987        -- Ma³¿
        end
        if give == 0 then
            say("W œrodku nie by³o nic ciekawego.")
        else
            pc.give_item2(give, 1)
            say("W œrodku znalaz³eœ:")
            say_reward(item.proto_get_name(give))
        end
    else
        affect.remove(fishing_manage.AFFECT_GOLD_TUNA)
        affect.add_new(fishing_manage.AFFECT_GOLD_TUNA, POINT_NONE_, fishing_manage.TUNA_SHORT, 300)
        say("Z³oty Tuñczyk na haczyku przyci¹gnie rzadkie ryby.")
        say_reward("Bonus Z³otego Tuñczyka: 5 minut.")
    end
end

-- GM: what the angler's rod would bring up now (the shares of the table for his rod, book and tuna bonus)
local function show_odds()
    local ctx = context()
    local odds, total = fishing_drop.get_odds(ctx)
    syschat(string.format("Wêdka %d, rzadkie x%d, tuñczyk %s, suma wag %d", ctx.level, ctx.rare, tostring(ctx.tuna), total))
    for i = 1, table.getn(odds) do
        local v = odds[i][1]
        local name = v
        if type(v) == "number" then
            name = item.proto_get_name(v)
        end
        syschat(string.format("%s: %.2f%%", tostring(name), odds[i][2]))
    end
end

fishing_manage.success = success
fishing_manage.predict_fish = predict_fish
fishing_manage.simulate_fishing = simulate_fishing
fishing_manage.simulate_calm = simulate_calm
fishing_manage.take_rod = take_rod
fishing_manage.carbon_rod_talk = carbon_rod_talk
fishing_manage.golden_tuna = golden_tuna
fishing_manage.show_odds = show_odds
fishing_manage.rod_level = rod_level
fishing_manage.rare_mult = rare_mult
