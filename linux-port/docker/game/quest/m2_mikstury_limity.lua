-- MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026; cache/yohara/decyzje-lowienie-mikstury.md M1, M2, M6 and the
-- fishing decision 9): the herbal potions and the grilled fish (item type 36, quest potion_use) with no group limit.
--
-- dofile'd by _otherModuleLoader.lua after potion_system.lua and before m2_mikstury.lua (game/Dockerfile), which wraps
-- what this file puts in potion_system.use_potion (the withdrawn potions). The file is cp1250 like the quests: its
-- texts go to the client as they are. The engine side of the same rule is server-patches/mikstury (README.md).
--
-- What changes against the package's potion_system.use_potion:
--   * no group caps - BOOST 5, OFFENSIVE 3, DEFENSIVE 2, FOOD 2 (the "2 fish" limit) are gone, for Baek-Go's recipe
--     potions too (M6; their crafting is untouched);
--   * no block by an ItemShop speed / attack-speed potion (AFFECT_MALL) - another affect type, both run;
--   * the same bonus (this group's affect + the point): a stronger one running refuses the potion, the same value
--     running at least as long as the new one would refuses it (nothing to refresh), otherwise the new one replaces it
--     (override + per point) - a refresh or an upgrade. The package refused a re-drink to refresh;
--   * a cooldown starts only when the potion was really used (the package started it before its own refusals);
--   * the fish exceptions (decision 9), the only potions that still exclude one another:
--       - the EXP fish never run together: S³odka Ryba 27879 < Z³oty Karaœ 27883 < Rak Niebieski 27887 - eating a
--         better one switches the running one off, a weaker one is refused while a better one runs;
--       - Z³oty Karaœ 27883 and Krab Królewski 27886 exclude each other (refused while the other runs).
--     A fish "runs" when every apply of its proto row (item.get_apply(vnum)) is on as this group's affect with the
--     same value - no other food gives those points (mikstury-analiza.md §5.4).
--   Kept: the level limit, the custom affect (value4: Mikstura Stagnacji's 310 - refused while it runs), the
--   duration extension of socket 0 (+50 / +100%), the drink effects.
m2_mikstury_limity = {}

local DURATION_VALUE_INDEX = 0
local GROUP_VALUE_INDEX = 1
local COOLDOWN_VALUE_INDEX = 2
local SHARED_COOLDOWN_VALUE_INDEX = 3
local CUSTOM_AFFECT_VALUE_INDEX = 4
local GROUP_TYPE_FOOD = 4

-- the EXP fish, weakest first
m2_mikstury_limity.EXP_FISH = {
	[27879] = 1,	-- Pieczona S³odka Ryba
	[27883] = 2,	-- Pieczony Z³oty Karaœ
	[27887] = 3,	-- Pieczony Rak Niebieski
}

-- fish that exclude each other
m2_mikstury_limity.EXCLUSIVE = {
	[27883] = {27886},	-- Z³oty Karaœ - Krab Królewski
	[27886] = {27883},
}

m2_mikstury_limity.MSG_STRONGER = "Silniejszy efekt tego rodzaju ju¿ dzia³a."
m2_mikstury_limity.MSG_LONGER = "Ten efekt ju¿ dzia³a i potrwa d³u¿ej ni¿ nowy."
m2_mikstury_limity.MSG_BETTER_FISH = "Dzia³a ju¿ lepsza ryba na doœwiadczenie - s³absza nie zadzia³a razem z ni¹."
m2_mikstury_limity.MSG_SWITCHED = "Poprzednia ryba na doœwiadczenie przesta³a dzia³aæ - zast¹pi³a j¹ lepsza."
m2_mikstury_limity.MSG_EXCLUSIVE = "Nie mo¿esz jednoczeœnie u¿ywaæ Z³otego Karasia i Krabu Królewskiego."

-- {point, value, point, value, ...} of a vnum's proto row
m2_mikstury_limity.applies = function(vnum)
	return {item.get_apply(vnum)}
end

-- does the fish vnum run now (every apply of it on as the food affect, the same value)?
m2_mikstury_limity.fish_runs = function(vnum)
	local a = m2_mikstury_limity.applies(vnum)
	local n = table.getn(a)
	if n == 0 then
		return false
	end
	local affect_type = AFFECT_POTION_START + GROUP_TYPE_FOOD
	for i = 1, n, 2 do
		if pc.get_affect_value(affect_type, a[i]) ~= a[i + 1] then
			return false
		end
	end
	return true
end

-- the fish rules for vnum: false (refused, told why) or true and the list of EXP fish to switch off once it is eaten
m2_mikstury_limity.fish_check = function(vnum)
	local off = {}
	local others = m2_mikstury_limity.EXCLUSIVE[vnum]
	if others ~= nil then
		for _, o in ipairs(others) do
			if m2_mikstury_limity.fish_runs(o) then
				syschat(m2_mikstury_limity.MSG_EXCLUSIVE)
				return false, off
			end
		end
	end
	local rank = m2_mikstury_limity.EXP_FISH[vnum]
	if rank ~= nil then
		for o, r in pairs(m2_mikstury_limity.EXP_FISH) do
			if o ~= vnum and m2_mikstury_limity.fish_runs(o) then
				if r > rank then
					syschat(m2_mikstury_limity.MSG_BETTER_FISH)
					return false, off
				end
				table.insert(off, o)
			end
		end
	end
	return true, off
end

-- switches the listed fish off (their food affects)
m2_mikstury_limity.fish_off = function(list)
	local affect_type = AFFECT_POTION_START + GROUP_TYPE_FOOD
	for _, o in ipairs(list) do
		local a = m2_mikstury_limity.applies(o)
		for i = 1, table.getn(a), 2 do
			affect.remove_new(affect_type, a[i])
		end
	end
	if table.getn(list) > 0 then
		syschat(m2_mikstury_limity.MSG_SWITCHED)
	end
end

-- the same-bonus rule for the applies of the item: true when it may be used
m2_mikstury_limity.may_refresh = function(affect_type, applies, duration)
	local n = table.getn(applies)
	if n == 0 then
		return true
	end
	local all_longer = true
	for i = 1, n, 2 do
		local point = applies[i]
		local value = applies[i + 1]
		if pc.has_affect(affect_type, point) then
			local current = pc.get_affect_value(affect_type, point)
			if current > value then
				syschat(m2_mikstury_limity.MSG_STRONGER)
				return false
			end
			if current < value or pc.get_affect_duration(affect_type, point) < duration then
				all_longer = false
			end
		else
			all_longer = false
		end
	end
	if all_longer then
		syschat(m2_mikstury_limity.MSG_LONGER)
		return false
	end
	return true
end

potion_system.use_potion = function()
	local level_limit = item.get_level_limit()
	if pc.get_level() < level_limit then
		syschat(string.format(translate.general.low_lvl, level_limit))
		return
	end

	local applies = {item.get_apply()}
	local item_vnum = item.get_vnum()
	local group = item.get_value(GROUP_VALUE_INDEX)
	local affect_type = AFFECT_POTION_START + group
	local duration = item.get_value(DURATION_VALUE_INDEX)
	local cooldown = item.get_value(COOLDOWN_VALUE_INDEX)
	local shared_cooldown_index = item.get_value(SHARED_COOLDOWN_VALUE_INDEX)
	local custom_affect = item.get_value(CUSTOM_AFFECT_VALUE_INDEX)
	if duration == 0 then
		duration = INFINITE_AFFECT_DURATION
	end

	local extend_duration = item.get_socket(0)
	if extend_duration == 50 or extend_duration == 100 then
		duration = math.floor(duration * (100 + extend_duration) / 100)
	end

	if cooldown > 0 then
		local current_cooldown = pc.getf("potion", "cooldown"..shared_cooldown_index) - get_time()
		if current_cooldown > 0 then
			local minutes = math.floor(current_cooldown / 60)
			if minutes > 0 then
				syschat(string.format(get_lctext("POTION_COOLDOWN_MINUTE%d"), minutes + 1))
			else
				local seconds = current_cooldown - minutes * 60
				syschat(string.format(get_lctext("POTION_COOLDOWN_SECOND%d"), seconds))
			end
			return
		end
	end

	if custom_affect > 0 then
		if pc.has_affect(custom_affect) then
			syschat(translate.potions.already_used)
			return
		end
		affect_type = custom_affect
	end

	local fish_ok, fish_off = m2_mikstury_limity.fish_check(item_vnum)
	if not fish_ok then
		return
	end

	if not m2_mikstury_limity.may_refresh(affect_type, applies, duration) then
		return
	end

	if not affect.is_loaded() then
		return
	end

	if item.remove(1) then
		if cooldown > 0 then
			pc.setf("potion", "cooldown"..shared_cooldown_index, get_time() + cooldown)
		end

		m2_mikstury_limity.fish_off(fish_off)

		local potion_effect_type = SE_DRINK_POTION
		local point_len = table.getn(applies)
		if point_len > 0 then
			for i = 1, point_len, 2 do
				local point = applies[i]
				local value = applies[i + 1]
				affect.add_new(affect_type, point, value, duration, AFF_NONE, true, true, item_vnum)

				if point == POINT_MOV_SPEED then
					potion_effect_type = SE_DXUP_PURPLE
				elseif point == POINT_ATT_SPEED then
					potion_effect_type = SE_SPEEDUP_GREEN
				end
			end
		else
			affect.add_new(affect_type, POINT_NONE, 0, duration, AFF_NONE, true, true, item_vnum)
		end

		pc.show_effect(potion_effect_type)
	end
end

-- Z³ote Zio³o (50741, decision M3): a rare find while gathering herbs. The package's compiled herb_pick timer of quest
-- herbalism calls this after a successful pick (game/Dockerfile, MT2009_PLUS_MIKSTURY_V1 (herb)).
m2_mikstury_limity.GOLDEN_HERB = 50741
m2_mikstury_limity.GOLDEN_HERB_PERMILLE = 10	-- 1% a successful pick

m2_mikstury_limity.herb_picked = function()
	if number(1, 1000) <= m2_mikstury_limity.GOLDEN_HERB_PERMILLE then
		pc.give_item2(m2_mikstury_limity.GOLDEN_HERB, 1)
		syschat("Wœród zió³ znaleziono Z³ote Zio³o!")
	end
end
