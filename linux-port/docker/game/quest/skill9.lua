-- MT2009_PLUS_SKILL9_V1: the 9th skills of Yohara and the Soul Stones (server-patches/skill9/README.md).
--
-- The package's training_grandmaster_skill (Kamien Duchowy 50513, G1 -> P) lists the skills of
-- special.active_skill_list for the character's class and specialisation. That list stays as it is
-- (reset_scroll's BuildSkillList reads it too and gives skill points back - a 9th skill has none in
-- it); the Dockerfile step "share: 9th skills and the Soul Stones" makes the quest's compiled
-- object ask mt2009_skill9.grandmaster_list instead: the same skills plus the 9th one of the class
-- and specialisation (playerbot_skill9.cpp SkillFor). Its name goes into locale.GM_SKILL_NAME_DICT
-- when first asked (locale.lua is loaded by then; it replaces the whole table when it loads).
-- This file is CP1250 like the quests.
mt2009_skill9 = {}

mt2009_skill9.by_job = {
	[0] = { 176, 176 },	-- Wojownik: Trzesienie
	[1] = { 177, 178 },	-- Ninja: Swiatlo Gwiazd / Strzal Wichury
	[2] = { 179, 180 },	-- Sura: Piekielny Cios / Fala Smierci
	[3] = { 181, 182 },	-- Szaman: Meteor / Tarcza Eteru
}

mt2009_skill9.names = {
	[176] = "Trzêsienie",
	[177] = "Œwiat³o Gwiazd",
	[178] = "Strza³ Wichury",
	[179] = "Piekielny Cios",
	[180] = "Fala Œmierci",
	[181] = "Meteor",
	[182] = "Tarcza Eteru",
}

mt2009_skill9.grandmaster_list = function(job, group)
	local list = {}
	local base = special.active_skill_list[job + 1]
	if base ~= nil and base[group] ~= nil then
		table.foreachi(base[group], function(i, v) table.insert(list, v) end)
	end
	local row = mt2009_skill9.by_job[job]
	if row ~= nil and row[group] ~= nil then
		local vnum = row[group]
		table.insert(list, vnum)
		if locale ~= nil and locale.GM_SKILL_NAME_DICT ~= nil and locale.GM_SKILL_NAME_DICT[vnum] == nil then
			locale.GM_SKILL_NAME_DICT[vnum] = mt2009_skill9.names[vnum]
		end
	end
	return list
end
