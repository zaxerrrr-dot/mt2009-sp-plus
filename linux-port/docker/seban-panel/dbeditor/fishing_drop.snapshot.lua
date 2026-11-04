-- MT2009_PLUS_FISHING_GLOBAL_V1: what a rod brings up - fishing as on the global server (the owner, 4 November 2026:
-- cache/yohara/decyzje-lowienie-mikstury.md "Lowienie" 3-7, cache/yohara/lowienie-analiza.md D2). Replaces the
-- package's quest/libs/fishing/fishing_drop.lua (game/Dockerfile); the Seban panel's "Lowienie ryb" page edits the
-- table's lines (bin/m2-fishing, spool fishing/fishing_drop.v2.custom.txt).
--
-- One line a catch: itemVnum ("farba" - a random hair dye 70202-70206), itemCount, rodFrom, rodTo, tier, weight.
--   * the rod's level 1-20 (Wedka+1 ... Wedka+20: value0 / 10), Wedka Weglowa 22; a line from rodFrom to rodTo;
--     rodFrom is the wiki's minimum rod of a fish (+1 / +2 / +3 / +4);
--   * tier 0 - a common fish or an item: its weight as it is ("this does not count for regular items");
--     tier 1 - a better fish (minimum rod +2 ... +4): weight x (1 + 0.10 x (level - 1));
--     tier 2 - a rare fish: ONLY with Rybie Wnetrznosci (71008 / 72013-72015 worn, or the premium) or the golden tuna's
--              bonus (decision 4), weight x (1 + 0.25 x (level - 4)) x 2 (the book; the tuna's 60 minutes x2, its 5
--              minutes of the bait x2.5 - the best one counts);
--     tier 3 - Zloty Tunczyk: once a day a character (from midnight, Polish time), never while its bonus runs, never
--              for a bot (decision 12);
--   * weights: Owsap v6.2.6 fishing.txt (PROB0 - the village column - for the fish and the wiki's items, PROB2 for
--     the four rare fish of the wiki; Slodka Ryba ... Zloty Karas 150/90/60/30/20 - Owsap gave them 0, the old
--     Korean table x10); our own catches (decision 7) at their old share of the wiki's items; Bryla Zlota back.
fishing_drop = {}
local fishing_drop_table = {
    -- itemVnum, itemCount, rodFrom, rodTo, tier, weight
    27802, 1, 1, 22, 0, 2000, -- Drobne Ryby
    27803, 1, 1, 22, 0, 1950, -- Karas
    27804, 1, 1, 22, 0, 900, -- Ryba Mandaryna
    27806, 1, 1, 22, 0, 200, -- Karp
    27808, 1, 1, 22, 0, 100, -- Amur
    27809, 1, 1, 22, 0, 100, -- Pstrag
    27812, 1, 1, 22, 0, 100, -- Rzeczny Pstrag
    27814, 1, 1, 22, 0, 100, -- Okon
    27818, 1, 1, 22, 0, 50, -- Ryba Lotosu
    27805, 1, 2, 22, 1, 700, -- Duzy Karas
    27807, 1, 2, 22, 1, 200, -- Losos
    27810, 1, 2, 22, 1, 100, -- Wegorz
    27813, 1, 2, 22, 1, 100, -- Krasnopiorka
    27816, 1, 2, 22, 1, 50, -- Sum
    27815, 1, 3, 22, 1, 50, -- Tenchi
    27811, 1, 4, 22, 1, 100, -- Teczowy Pstrag
    27819, 1, 4, 22, 2, 150, -- Slodka Ryba
    27820, 1, 4, 22, 2, 90, -- Gromadnik
    27821, 1, 4, 22, 2, 60, -- Shiri
    27822, 1, 4, 22, 2, 30, -- Lustrzany Karp
    27823, 1, 4, 22, 2, 20, -- Zloty Karas
    27824, 1, 4, 22, 2, 100, -- Wezoglow
    27825, 1, 4, 22, 2, 100, -- Skaber
    27826, 1, 4, 22, 2, 250, -- Krab Krolewski
    27827, 1, 4, 22, 2, 200, -- Rak Niebieski
    27797, 1, 1, 22, 3, 1300, -- Zloty Tunczyk
    70201, 1, 1, 22, 0, 100, -- Wybielacz
    "farba", 1, 1, 22, 0, 425, -- farba do wlosow (70202-70206)
    70048, 1, 1, 22, 0, 25, -- Peleryna Maskujaca
    70049, 1, 1, 22, 0, 25, -- Pierscien Lucy
    70050, 1, 1, 22, 0, 25, -- Symbol Krola Przepowiedni
    70051, 1, 1, 22, 0, 25, -- Rekawica Krola Przepowiedni
    50002, 1, 1, 22, 0, 50, -- Zloty Pierscien
    50009, 1, 1, 22, 0, 25, -- Srebrny Klucz
    50008, 1, 1, 22, 0, 25, -- Zloty Klucz
    50043, 1, 1, 22, 0, 25, -- Klucz Nimfy Wodnej
    80008, 1, 1, 22, 0, 25, -- Bryla Zlota
    70007, 1, 3, 22, 0, 20, -- Pierscien Niejawnosci
    70006, 1, 3, 22, 0, 12, -- Pierscien Jezyka
    70102, 1, 5, 22, 0, 12, -- Fasolka Zen
    27798, 1, 6, 22, 0, 7, -- Skamieniala Krewetka
    25040, 1, 6, 22, 0, 2, -- Zwoj Blogoslawienstwa
    30370, 1, 7, 22, 0, 1,
    30373, 1, 7, 22, 0, 1,
    30374, 1, 7, 22, 0, 1,
    39015, 1, 7, 22, 0, 1, -- Kamien Kowala
    39016, 1, 7, 22, 0, 1, -- Magiczny Metal
}

local fishing_drop_data_length = 6

fishing_drop.TIER_COMMON = 0
fishing_drop.TIER_BETTER = 1
fishing_drop.TIER_RARE = 2
fishing_drop.TIER_TUNA = 3
fishing_drop.TUNA_VNUM = 27797

local function get_drop_by_index(i)
    local indexInDropTable = (i-1) * fishing_drop_data_length + 1

    local itemVnum = fishing_drop_table[indexInDropTable]
    if itemVnum == nil then
        return nil
    end
    local name = ""
    if itemVnum == "farba" then
        itemVnum = number(70202, 70206)
        name = locale.fishing.hair_dye
    else
        name = item.proto_get_name(itemVnum)
    end

    return {
        index = i,
        name = name,
        itemVnum = itemVnum,
        itemCount = fishing_drop_table[indexInDropTable+1],
        rodFrom = fishing_drop_table[indexInDropTable+2],
        rodTo = fishing_drop_table[indexInDropTable+3],
        tier = fishing_drop_table[indexInDropTable+4],
        poolValue = fishing_drop_table[indexInDropTable+5],
    }
end

-- the weight of the line at i for a context {level, rare (the rare fish's x100 multiplier: 0 none, 200, 250), tuna (true
-- when Zloty Tunczyk may bite)}
local function row_weight(i, ctx)
    local level = ctx.level
    if level < fishing_drop_table[i + 2] or level > fishing_drop_table[i + 3] then
        return 0
    end
    local tier = fishing_drop_table[i + 4]
    local weight = fishing_drop_table[i + 5]
    if tier == fishing_drop.TIER_BETTER then
        return math.floor(weight * (10 + (level - 1)) / 10)
    elseif tier == fishing_drop.TIER_RARE then
        if ctx.rare <= 0 then
            return 0
        end
        local plus = level - 4
        if plus < 0 then
            plus = 0
        end
        return math.floor(weight * (4 + plus) * ctx.rare / 400)
    elseif tier == fishing_drop.TIER_TUNA then
        if ctx.tuna then
            return weight
        end
        return 0
    end
    return weight
end

local function get_total_pool_value(ctx)
    local drop_table_length = table.getn(fishing_drop_table)
    local pool = 0
    for i in range(1, drop_table_length, fishing_drop_data_length) do
        pool = pool + row_weight(i, ctx)
    end
    return pool
end

local function get_random_drop(ctx)
    local drop_table_length = table.getn(fishing_drop_table)

    local maxPool = get_total_pool_value(ctx)
    if maxPool <= 0 then
        return nil
    end
    local poolCheck = 0
    local luckyNumber = number(1, maxPool)
    debug("fishing drop rod level: %d, rare x%d, tuna %s, maxPool: %d, luckyNumber: %d", ctx.level, ctx.rare,
        tostring(ctx.tuna), maxPool, luckyNumber)
    for i in range(1, drop_table_length, fishing_drop_data_length) do
        local w = row_weight(i, ctx)
        if w > 0 then
            local nextPoolCheck = poolCheck + w
            if luckyNumber > poolCheck and luckyNumber <= nextPoolCheck then
                local index = math.floor(i / fishing_drop_data_length + 1)
                debug("fishing drop index: %d", index)
                return get_drop_by_index(index)
            end
            poolCheck = nextPoolCheck
        end
    end
    return nil
end

-- the shares (per cent) of every line for a context - the GM's /fishing_odds talk and the panel's check
local function get_odds(ctx)
    local out = {}
    local total = get_total_pool_value(ctx)
    local drop_table_length = table.getn(fishing_drop_table)
    for i in range(1, drop_table_length, fishing_drop_data_length) do
        local w = row_weight(i, ctx)
        if w > 0 and total > 0 then
            table.insert(out, {fishing_drop_table[i], w * 100 / total})
        end
    end
    return out, total
end

-- killing a fish (right click): a dead fish, a bone, a clam, a worm or nothing; a rarer fish holds a clam a bit more
-- often (its line's weight against the table's: 2000 the commonest, 20 the rarest)
local function open_fish(fishVnum)
    local fishPool = 0
    local length = table.getn(fishing_drop_table)
    for i in range(1, length, fishing_drop_data_length) do
        if fishing_drop_table[i] == fishVnum then
            fishPool = fishing_drop_table[i + fishing_drop_data_length - 1]
        end
    end
    if fishPool == 0 then
        syschat("Wystapil blad (kod bledu: fish_no_pool_found)")
        return false
    end

    local drop_from_fish_table = {
        27987, 1, 8,
        27799, 1, 28,
        "water", 1, 47,
        "dead", 1, 150,
        27801, 1, 20,
    }

    local maxPool = 2000
    local minPool = 20
    local checkPool = fishPool - minPool
    local deltaPool = maxPool - minPool
    local progress = minmax(0, 1-(checkPool / deltaPool), 1)
    local addCalmChance = math.floor(10 * progress)
    drop_from_fish_table[3] = drop_from_fish_table[3] + addCalmChance
    debug("additional calm chance (%d%%)", addCalmChance)

    local i = get_random_element_from_pool_table(drop_from_fish_table, 3)
    local itemVnum = drop_from_fish_table[i]
    local itemCount = drop_from_fish_table[i+1]
    if itemVnum == "water" then
        syschat(get_lctext("The fish vanished in the depths of the water."))
    elseif itemVnum == "dead" then
        pc.give_item2(fishVnum+30)
    elseif itemVnum == 27801 then
        syschat(get_lctext("There is a Worm inside the Fish."))
    elseif itemVnum == 27987 then
        syschat(get_lctext("There is a Clam inside the Fish."))
    end

    if type(itemVnum) == "number" then
        pc.give_item2(itemVnum, itemCount)
    end
    return true
end

fishing_drop.get_random_drop = get_random_drop
fishing_drop.get_drop_by_index = get_drop_by_index
fishing_drop.get_odds = get_odds
fishing_drop.open_fish = open_fish
