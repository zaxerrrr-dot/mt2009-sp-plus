-- MT2009_PLUS_LANGUAGE_V1: the quests' texts in the language each player reads (server-patches/language/README.md).
--
-- The engine loads this file after quest/locale.lua (questlua.cpp, "lua load"), when every library function is
-- defined and before the quests. Every quest - the stock ones (gameforge.*, translate.*, locale.*) and ours (Polish
-- literals) - keeps building its texts in Polish; what goes to the quest window is handed to mt2009_tr() first,
-- which looks the Polish up in the reader's dictionary (lang/<code>/*.tsv, mt2009_language.cpp): the exact text, or
-- a format the text was made of ("Masz %d sztuk" finds "Masz 5 sztuk" and gives "You have 5 pieces"). A Polish reader,
-- a quest running for nobody and a text no dictionary has get the text as it is. So no quest is compiled differently,
-- and nothing a quest compares or stores changes language.
--
-- Chat lines (syschat, chat, notice, notice_all, d.notice, ...) are not wrapped here: the engine translates every
-- INFO / NOTICE / TALKING line for its own reader in CHARACTER::ChatPacket, so a broadcast reaches each player in his
-- own language.
--
-- ASCII only (the engine's Lua reads a byte over 0x7F in a string as a double-byte lead byte).

if type(mt2009_tr) ~= "function" then
	return
end

local tr = mt2009_tr

-- f(a, b, ...) with the string arguments at the given positions (nil: all of them) translated.
local function wrap(tbl, name, positions)
	local raw = tbl[name]
	if type(raw) ~= "function" then
		return
	end
	tbl[name] = function(...)
		if positions == nil then
			for i = 1, arg.n do
				if type(arg[i]) == "string" then
					arg[i] = tr(arg[i])
				end
			end
		else
			for _, i in ipairs(positions) do
				if type(arg[i]) == "string" then
					arg[i] = tr(arg[i])
				end
			end
		end
		return raw(unpack(arg))
	end
end

local G = getfenv(0)

-- The quest window.
wrap(G, "say")
wrap(G, "say_title", { 1 })
wrap(G, "say_reward", { 1 })
wrap(G, "say_orange", { 1 })
wrap(G, "say_quiz", { 1 })
wrap(G, "say_split", { 1 })
wrap(G, "say_item", { 1, 3 })
-- The options: select("A", "B", ...) - also the NPC's menu (NPC::OnChat runs select(...) with the options' texts).
wrap(G, "select")
do
	local raw = G.select_table
	if type(raw) == "function" then
		G.select_table = function(t)
			if type(t) ~= "table" then
				return raw(t)
			end
			local copy = {}
			for k, v in pairs(t) do
				if type(v) == "string" then
					copy[k] = tr(v)
				else
					copy[k] = v
				end
			end
			return raw(copy)
		end
	end
end
-- The letters (quest buttons) and the quest's title, clock and counter in the quest list.
wrap(G, "makequestbutton", { 1 })
wrap(G, "make_quest_button_ex", { 1 })
if type(q) == "table" then
	wrap(q, "set_title", { 1 })
	wrap(q, "set_clock_name", { 1 })
	wrap(q, "set_counter_name", { 1 })
end

-- Item and monster names: the reader's language's (lang/<code>/item_names.tsv, mob_names.tsv), else the proto's.
do
	local function names(tbl, name, lookup)
		local raw = tbl[name]
		if type(raw) ~= "function" then
			return
		end
		tbl[name] = function(vnum, ...)
			local n = lookup(vnum)
			if n ~= nil then
				return n
			end
			return raw(vnum, unpack(arg))
		end
	end
	if type(mt2009_item_name) == "function" then
		names(G, "item_name", mt2009_item_name)
		names(G, "get_item_name", mt2009_item_name)
	end
	if type(mt2009_mob_name) == "function" then
		names(G, "mob_name", mt2009_mob_name)
	end
end

mt2009_language_loaded = true
