-- MT2009_PLUS_BIOLOG_ELIKSIR_V1 / MT2009_PLUS_MIKSTURY_WYCOFANE_V1 (the owner, 3 November 2026, the Yohara list):
-- the Biologist's and the skill books' helpers as the pl-wiki has them.
--
-- dofile'd by _otherModuleLoader.lua after m2_difficulty.lua (game/Dockerfile), so after collect_data.lua and
-- potion_system.lua, whose functions it wraps. The file is cp1250 like the quests: its texts go to the client as they are.
--
-- 1. Withdrawn: three of Baek-Go's herbalism potions that are not on the wiki and did the work of the wiki's own helpers
--    (crafting_proto rows 71 / 72 / 74 of the package, their recipes 50932 / 50933 / 50935 from the "super receptury"
--    drop group s50902):
--      51782 Mikstura Geniuszu          +75% POINT_LEARN_CHANCE for the next skill book / soul stone / recipe read
--      51783 Mikstura Determinacji      AFFECT_LEARN_NO_FAIL_TIME - a failed book read set no wait
--      51785 Mikstura Szybkiej Analizy  AFFECT_COLLECT_NO_FAIL_TIME - a spoiled Biologist specimen set no wait
--    The wiki's helpers are Rada Pustelnika (71094, the next book read), Zwoj Egzorcyzmu (71001, the book wait), Spirala
--    Czasu (72347-72349, the Biologist's wait) and Eliksir Poszukiwacza (below). A withdrawn potion is refused when used
--    and stays in the bag - it sells to an NPC as before. The Dockerfile takes the three rows off Baek-Go's board and the
--    three recipes out of s50902, apply.sh takes the rows out of world.crafting_proto (the bots brew from it), and quest
--    eliksir_poszukiwacza takes an effect still running off a character at login.
--
-- 2. Eliksir Poszukiwacza (71035; 76020 the starter chests' bound copy, 39023 the tradeable one; pl-wiki "Eliksir
--    Poszukiwacza": "Poprawia jakosc przedmiotow do badan od Biologa Chaegiraba oraz Seona-Pyeonga ... Nie dotyczy misji
--    na Yohara"): quest eliksir_poszukiwacza sets collect_quest.eliksir when one is drunk and the next research hand-in
--    (collect_data.take_chance - collect_quest_lv30 ... lv90 at Chaegirab, lv92 / lv94 at Seon-Pyeong) is rolled at half
--    as much again: the package's 60% becomes 90% - the original quest's "pass_percent = 90" with the elixir (Owsap's
--    collect_quest_lv30, AFFECT_RESEARCHER_ELIXIR). The elixir is spent on that hand-in whatever the roll; a hand-in that
--    cannot fail (lv94's 100%) leaves it for the next. The Yohara rows (collect_quest_cz*) pass no_elixir.
m2_mikstury = {}

m2_mikstury.WITHDRAWN = {
	[51782] = true,
	[51783] = true,
	[51785] = true,
}

m2_mikstury.ELIXIR_BONUS = 50	-- percent of the row's own chance: 60 -> 90

m2_mikstury.is_withdrawn = function(vnum)
	return m2_mikstury.WITHDRAWN[vnum] == true
end

local m2_mikstury_stock_use_potion = potion_system.use_potion
potion_system.use_potion = function()
	if m2_mikstury.is_withdrawn(item.get_vnum()) then
		syschat("Ta mikstura zosta³a wycofana i nie dzia³a. Mo¿esz j¹ sprzedaæ w sklepie NPC.")
		return
	end
	return m2_mikstury_stock_use_potion()
end

-- A spoiled specimen always starts the wait now (Mikstura Szybkiej Analizy is withdrawn); the hand-in's "wait info"
-- line reads this too.
collect_data.is_no_time_on_fail = function()
	return false
end

m2_mikstury.has_elixir = function()
	return pc.getf("collect_quest", "eliksir") > 0
end

local m2_mikstury_stock_take_chance = collect_data.take_chance
collect_data.take_chance = function(chance, no_elixir)
	if not no_elixir and chance < 100 and m2_mikstury.has_elixir() then
		pc.setf("collect_quest", "eliksir", 0)
		chance = math.floor(chance * (100 + m2_mikstury.ELIXIR_BONUS) / 100)
		if chance > 100 then
			chance = 100
		end
		syschat(string.format("Eliksir Poszukiwacza poprawi³ jakoœæ przedmiotu: szansa na przyjêcie %d%%.", chance))
	end
	return m2_mikstury_stock_take_chance(chance)
end
