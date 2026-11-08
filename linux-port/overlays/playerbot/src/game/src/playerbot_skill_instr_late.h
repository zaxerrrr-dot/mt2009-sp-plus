#ifndef __INC_METIN2_PLAYERBOT_SKILL_INSTR_LATE_H__
#define __INC_METIN2_PLAYERBOT_SKILL_INSTR_LATE_H__

// MT2009_PLUS_BOT_SKILL_INSTR_V1 (the late part; the items, the keep rule and the switches are playerbot_skill_instr.h).
// The owner, 8 November 2026: "a bot that lacks skill books (KU) to develop its skills buys the ItemShop chests of skill
// instructions; a Rada Pustelnika goes to the dearest skill among those it can develop, a Zwoj Egzorcyzmu to the dearest
// skill it is developing; the rest is read in the bot's programmed order; the next skill gets the Rada / Zwoj only once
// the previous is G1 or out of books; the spare instructions go on the counter at their KU's price".
//
// The chests. An "instruction chest" is any ItemShop line the bots can buy whose contents hold an instruction
// (50401-50511), found at runtime - nothing is hard-coded, so a chest the owner adds is known within ten minutes:
//   * a giftbox line (an item of ITEM_GIFTBOX sold in common.itemshop_items / itemshop3.v3_lines with its vnum): its
//     special_item_group, sub-groups (sNNNNN) followed three deep - e.g. the groups InstrukcjeBody 50401 / InstrukcjeMental
//     50402 / InstrukcjeDagger 50403 / InstrukcjeArcher 50404 / InstrukcjeWP 50405 / InstrukcjeBM 50406 / InstrukcjeSmok
//     50407 / InstrukcjeHealer 50408 and the class groups 50411-50414 (s5040x) that special_item_group.txt carries; bought
//     through the V3 goal path ("skill_instr", CollectPlayerBotIshop3Goals -> BuyPlayerBotIshop3Pieces: the daily SM pool,
//     never urgent, the session's purchase cap) and opened by the chest pass (ManagePlayerBotChests);
//   * a V3 roll chest (itemshop3.chests / chest_drops / chest_items) whose results hold an instruction: bought one roll at
//     a time by BuyPlayerBotIshop3Chest from the goal session (the daily pool asked first, as the set chest's), and never
//     taken by the set-chest look (ManagePlayerBotIshop3Chest skips it).
// Which chest: the one whose instructions cover the most of the bot's short skills (its own skills at M1-M9 with no book
// - KU or instruction - in the bag), then the cheapest. One chest at a time: none while the bot holds an unopened one of
// them, and at most one every PLAYERBOT_SKILL_INSTR_CHEST_GAP_H hours (quest flag playerbot.instr_chest). A Zwoj / Rada in
// the chest is spent by the reading below; the bots' wish (playerbot_itemshop.h) still buys them when none is held.
// On 8 November no such line was found (the census said chests=0): the ItemShop's instruction chests are the eight class
// chests (D) of MT2009_PLUS_CLASS_CHESTS_V1 (V3 lines 100183-100190, 999 SM), ITEM_QUEST items opened by the quest
// skrzynie_klas - no special_item_group, and the encyclopedia inside is a second item. MT2009_PLUS_BOT_CLASS_CHESTS_V1
// (the owner, 8 November 2026): the scan knows them (PLAYERBOT_CLASS_CHESTS below - the quest's table, keep the two
// equal), a giftbox's content that is itself a giftbox is followed into its group (a nested chest), and a bot opens a
// class chest and its encyclopedia here (OpenPlayerBotClassChests) as the quest does for a player - a bot runs no quest.
//
// The dearest skill ("most expensive", the definition): the price-list value of its book - GetPlayerBotBookAskingBase(skill),
// the KU's sheet price for the skill (PLAYERBOT_BOOK_PRICES: the owner's / Iwakura's prices, the ladder of
// MT2009_PLUS_BOOK_PRICE_LADDER_V1; one yang-rate factor for every skill, so the order is the sheet's), the build's earlier
// skill on a tie. The market's live index is left out on purpose: it moves by the hour and would move the Rada with it.
// E.g. a warrior (Body): Aura Miecza 1 550 568 > Berserk 781 000 > Wir Miecza 394 000 > Szarza 198 000 > Trzystronne 100 000.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, after playerbot_shop_aids.h.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1) && defined(MT2009_PLUS_BOT_SKILL_INSTR_V1)
#define PLAYERBOT_SKILL_INSTR_LATE 1	// the reading (playerbot_manager.cpp) and the census call ask this

namespace
{
	const DWORD PLAYERBOT_SKILL_INSTR_SCAN_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_SKILL_INSTR_CHEST_FLAG = "playerbot.instr_chest";
	const int PLAYERBOT_SKILL_INSTR_GROUP_DEPTH = 3;

	// The hours between two chests of one bot (env PLAYERBOT_SKILL_INSTR_CHEST_GAP_H, read once; 0..168, default 12).
	int GetPlayerBotSkillInstrChestGapSeconds()
	{
		static int s_iGap = -1;
		if (s_iGap < 0)
		{
			s_iGap = 12;
			if (const char* v = getenv("PLAYERBOT_SKILL_INSTR_CHEST_GAP_H"))
				if (*v)
					s_iGap = std::max(0, std::min(168, atoi(v)));
			sys_log(0, "PLAYERBOT_SKILL_INSTR: config chest_gap_h=%d", s_iGap);
		}
		return s_iGap * 3600;
	}

	// MT2009_PLUS_BOT_CLASS_CHESTS_V1: the class chests (D) and what the quest skrzynie_klas gives (keep equal to
	// linux-port/docker/game/quest/skrzynie_klas.quest): a chest -> 10x Mikstura Madrosci (3h) 71155, 20x Zwoj Egzorcyzmu
	// 71001, 10x Rada Pustelnika 71094, 5x Pierscien Teleportacji 70058 (one a cell) and its path's encyclopedia; the
	// encyclopedia -> 25 random instructions (50400 + skill) of the path, each draw on its own.
	struct TPlayerBotClassChest
	{
		DWORD dwChest, dwBook;
		BYTE bJob, bGroup;
		BYTE bSkills;
		DWORD adwSkills[6];
	};
	const TPlayerBotClassChest PLAYERBOT_CLASS_CHESTS[] = {
		{ 39048, 71204, JOB_WARRIOR, 1, 5, { 1, 2, 3, 4, 5, 0 } },	// Skrz. Woj. M. Ciala (D) / Encyklopedia Saturna (D)
		{ 39050, 71206, JOB_WARRIOR, 2, 5, { 16, 17, 18, 19, 20, 0 } },	// Skrz. Woj.M. Ducho. (D) / Encyklopedia Ziemi (D)
		{ 39052, 71208, JOB_ASSASSIN, 1, 5, { 31, 32, 33, 34, 35, 0 } },	// Skrz. Ninja M.Ostrza (D) / Encyklopedia Marsa (D)
		{ 39054, 71210, JOB_ASSASSIN, 2, 6, { 46, 47, 48, 49, 50, 51 } },	// Skrz. Ninja M. Luku (D) / Encyklop. Jupitera (D)
		{ 39056, 71212, JOB_SURA, 1, 6, { 61, 62, 63, 64, 65, 66 } },	// Skrzynia Sura Broni (D) / Encyklopedia Urana (D)
		{ 39058, 71214, JOB_SURA, 2, 6, { 76, 77, 78, 79, 80, 81 } },	// Skrzynia Sura Magii (D) / Encyklopedia Neptuna (D)
		{ 39060, 71216, JOB_SHAMAN, 1, 6, { 91, 92, 93, 94, 95, 96 } },	// Skrz. Szam. M. Smoka (D) / Encyklop. Merkurego (D)
		{ 39062, 71218, JOB_SHAMAN, 2, 6, { 106, 107, 108, 109, 110, 111 } },	// Skrz. Szam. M. Lecz. (D) / Encyklopedia Wenus (D)
	};
	const size_t PLAYERBOT_CLASS_CHEST_COUNT = sizeof(PLAYERBOT_CLASS_CHESTS) / sizeof(PLAYERBOT_CLASS_CHESTS[0]);
	const int PLAYERBOT_CLASS_CHEST_DRAWS = 25;
	const int PLAYERBOT_CLASS_CHEST_CELLS = 9;	// the quest's room: 3 stacks + 5 rings + the encyclopedia
	const DWORD PLAYERBOT_CLASS_CHEST_LOOK_MS = 30 * 1000;

	// The class chest of a chest's or an encyclopedia's vnum (NULL: neither).
	const TPlayerBotClassChest* FindPlayerBotClassChest(DWORD vnum, bool* isBook)
	{
		for (size_t i = 0; i < PLAYERBOT_CLASS_CHEST_COUNT; ++i)
			if (PLAYERBOT_CLASS_CHESTS[i].dwChest == vnum || PLAYERBOT_CLASS_CHESTS[i].dwBook == vnum)
			{
				if (isBook)
					*isBook = PLAYERBOT_CLASS_CHESTS[i].dwBook == vnum;
				return &PLAYERBOT_CLASS_CHESTS[i];
			}
		return NULL;
	}

	struct TPlayerBotSkillInstrChest
	{
		DWORD dwVnum;	// the giftbox's vnum (0 for a V3 roll chest)
		DWORD dwBook;	// MT2009_PLUS_BOT_CLASS_CHESTS_V1: a class chest's encyclopedia (0 for any other)
		DWORD dwChestId;	// the V3 chest's id (0 for a giftbox)
		bool bMarks;	// the giftbox's line is Smocze Znaki only
		std::set<DWORD> skills;
		int iRada, iZwoj;
	};
	std::vector<TPlayerBotSkillInstrChest> s_vecPlayerBotSkillInstrChests;
	std::set<DWORD> s_setPlayerBotSkillInstrV3Ids;
	DWORD s_dwPlayerBotSkillInstrScanAt = 0;
	size_t s_uPlayerBotSkillInstrScanLines = (size_t)-1;

	void CollectPlayerBotSkillInstrGroup(DWORD groupVnum, TPlayerBotSkillInstrChest& c, int depth);

	void NotePlayerBotSkillInstrContent(TPlayerBotSkillInstrChest& c, DWORD vnum, int depth)
	{
		if (IsPlayerBotSkillInstructionVnum(vnum))
		{
			c.skills.insert((DWORD)ITEM_MANAGER::instance().GetTable(vnum)->alValues[0]);
			return;
		}
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto)
			return;
		// MT2009_PLUS_BOT_CLASS_CHESTS_V1: a content that is a chest itself (a giftbox with its own group, or a class
		// chest's encyclopedia) - what it gives counts as the outer chest's
		if (depth < PLAYERBOT_SKILL_INSTR_GROUP_DEPTH)
		{
			bool isBook = false;
			const TPlayerBotClassChest* k = FindPlayerBotClassChest(vnum, &isBook);
			if (k && isBook)
			{
				for (BYTE s = 0; s < k->bSkills; ++s)
					c.skills.insert(k->adwSkills[s]);
				return;
			}
			if (proto->bType == ITEM_GIFTBOX && ITEM_MANAGER::instance().GetSpecialItemGroup(vnum))
			{
				CollectPlayerBotSkillInstrGroup(vnum, c, depth + 1);
				return;
			}
		}
		if (proto->bType != ITEM_USE || proto->bSubType != USE_AFFECT)
			return;
		if ((DWORD)proto->alValues[0] == AFFECT_SKILL_BOOK_BONUS)
			++c.iRada;
		else if ((DWORD)proto->alValues[0] == AFFECT_SKILL_NO_BOOK_DELAY)
			++c.iZwoj;
	}

	void CollectPlayerBotSkillInstrGroup(DWORD groupVnum, TPlayerBotSkillInstrChest& c, int depth)
	{
		const CSpecialItemGroup* g = ITEM_MANAGER::instance().GetSpecialItemGroup(groupVnum);
		if (!g)
			return;
		const std::vector<CSpecialItemGroup::CSpecialItemInfo> items = g->GetItems();
		for (size_t i = 0; i < items.size(); ++i)
		{
			if (items[i].isSpecial)
			{
				if (depth < PLAYERBOT_SKILL_INSTR_GROUP_DEPTH && items[i].vnum != groupVnum)
					CollectPlayerBotSkillInstrGroup(items[i].vnum, c, depth + 1);
				continue;
			}
			NotePlayerBotSkillInstrContent(c, items[i].vnum, depth);
		}
	}

	// The chests, from the catalogue as the bots last read it (every PLAYERBOT_SKILL_INSTR_SCAN_MS, or when its size moved).
	void RefreshPlayerBotSkillInstrChests(DWORD dwNow)
	{
		const size_t lines = s_mapPlayerBotItemShopCoins.size() + s_mapPlayerBotItemShopMarks.size() +
				s_vecPlayerBotIshop3Chests.size();
		if (s_dwPlayerBotSkillInstrScanAt != 0 && (int)(dwNow - s_dwPlayerBotSkillInstrScanAt) < (int)PLAYERBOT_SKILL_INSTR_SCAN_MS &&
				lines == s_uPlayerBotSkillInstrScanLines)
			return;
		s_dwPlayerBotSkillInstrScanAt = dwNow ? dwNow : 1;
		s_uPlayerBotSkillInstrScanLines = lines;
		s_vecPlayerBotSkillInstrChests.clear();
		s_setPlayerBotSkillInstrV3Ids.clear();
		for (int pass = 0; pass < 2; ++pass)
		{
			const TPlayerBotItemShopTable& table = pass == 0 ? s_mapPlayerBotItemShopCoins : s_mapPlayerBotItemShopMarks;
			for (TPlayerBotItemShopTable::const_iterator it = table.begin(); it != table.end(); ++it)
			{
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(it->first);
				bool isBook = false;
				const TPlayerBotClassChest* klass = FindPlayerBotClassChest(it->first, &isBook);
				if (!proto || it->second.empty() || (proto->bType != ITEM_GIFTBOX && !klass))
					continue;
				if (pass == 1 && s_mapPlayerBotItemShopCoins.find(it->first) != s_mapPlayerBotItemShopCoins.end())
					continue;	// a coins line of it was taken already
				TPlayerBotSkillInstrChest c;
				c.dwVnum = it->first;
				c.dwBook = 0;
				c.dwChestId = 0;
				c.bMarks = pass == 1;
				c.iRada = c.iZwoj = 0;
				if (proto->bType == ITEM_GIFTBOX && ITEM_MANAGER::instance().GetSpecialItemGroup(it->first))
					CollectPlayerBotSkillInstrGroup(it->first, c, 0);
				else if (klass)
				{
					// MT2009_PLUS_BOT_CLASS_CHESTS_V1: a quest-opened class chest (or its encyclopedia sold alone)
					for (BYTE s = 0; s < klass->bSkills; ++s)
						c.skills.insert(klass->adwSkills[s]);
					if (!isBook)
					{
						c.dwBook = klass->dwBook;
						c.iRada = 10;
						c.iZwoj = 20;
					}
				}
				if (!c.skills.empty())
					s_vecPlayerBotSkillInstrChests.push_back(c);
			}
		}
		for (size_t i = 0; i < s_vecPlayerBotIshop3Chests.size(); ++i)
		{
			const TPlayerBotIshop3Chest& v = s_vecPlayerBotIshop3Chests[i];
			TPlayerBotSkillInstrChest c;
			c.dwVnum = 0;
			c.dwBook = 0;
			c.dwChestId = v.dwChestId;
			c.bMarks = false;
			c.iRada = c.iZwoj = 0;
			for (size_t d = 0; d < v.drops.size(); ++d)
				for (size_t k = 0; k < v.drops[d].items.size(); ++k)
					for (size_t a = 0; a < v.drops[d].items[k].size(); ++a)
						NotePlayerBotSkillInstrContent(c, v.drops[d].items[k][a].dwVnum, 0);
			if (c.skills.empty())
				continue;
			s_vecPlayerBotSkillInstrChests.push_back(c);
			s_setPlayerBotSkillInstrV3Ids.insert(c.dwChestId);
		}
		std::string list;
		for (size_t i = 0; i < s_vecPlayerBotSkillInstrChests.size() && list.size() < 900; ++i)
		{
			const TPlayerBotSkillInstrChest& c = s_vecPlayerBotSkillInstrChests[i];
			char one[96];
			snprintf(one, sizeof(one), "%s%s%u:skills=%u,rada=%d,zwoj=%d", list.empty() ? "" : " ", c.dwVnum ? "box" : "v3",
					c.dwVnum ? c.dwVnum : c.dwChestId, (unsigned int)c.skills.size(), c.iRada, c.iZwoj);
			list += one;
		}
		sys_log(0, "PLAYERBOT_SKILL_INSTR: chests scanned lines=%u found=%u [%s]", (unsigned int)lines,
				(unsigned int)s_vecPlayerBotSkillInstrChests.size(), list.c_str());
	}

	bool IsPlayerBotSkillInstrV3Chest(DWORD chestId)
	{
		return s_setPlayerBotSkillInstrV3Ids.find(chestId) != s_setPlayerBotSkillInstrV3Ids.end();
	}

	// The bot's own skills at M1-M9 (readable) with no book of them in the bag - KU or instruction.
	void CollectPlayerBotSkillInstrShort(LPCHARACTER ch, std::vector<DWORD>& out)
	{
		out.clear();
		if (!ch || ch->GetSkillGroup() == 0)
			return;
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
		for (BYTE i = 0; i < build.bSkillCount; ++i)
		{
			const DWORD skill = build.dwSkills[i];
			const BYTE level = skill ? ch->GetSkillLevel(skill) : 0;
			if (skill && ch->GetSkillMasterType(skill) == SKILL_MASTER && level >= 20 && level < 30 &&
					CountPlayerBotOwnedSkillBooks(ch, skill) == 0)
				out.push_back(skill);
		}
	}

	// The chest for this bot: the most of its short skills, then the cheapest (V3 chests when v3, giftboxes else). NULL: none.
	const TPlayerBotSkillInstrChest* PickPlayerBotSkillInstrChest(LPCHARACTER ch, const std::vector<DWORD>& shortSkills, bool v3,
			long long* price)
	{
		const TPlayerBotSkillInstrChest* best = NULL;
		int bestCover = 0;
		long long bestPrice = 0;
		for (size_t i = 0; i < s_vecPlayerBotSkillInstrChests.size(); ++i)
		{
			const TPlayerBotSkillInstrChest& c = s_vecPlayerBotSkillInstrChests[i];
			if ((c.dwChestId != 0) != v3)
				continue;
			int cover = 0;
			for (size_t s = 0; s < shortSkills.size(); ++s)
				if (c.skills.find(shortSkills[s]) != c.skills.end())
					++cover;
			if (cover == 0)
				continue;
			long long p = 0;
			if (v3)
			{
				const TPlayerBotIshop3Chest* v = NULL;
				for (size_t k = 0; k < s_vecPlayerBotIshop3Chests.size() && !v; ++k)
					if (s_vecPlayerBotIshop3Chests[k].dwChestId == c.dwChestId)
						v = &s_vecPlayerBotIshop3Chests[k];
				if (!v || ch->GetLevel() < v->bMinLevel)
					continue;
				p = v->dwPrice;
			}
			else
			{
				std::vector<const TPlayerBotItemShopEntry*> lines;
				SortPlayerBotIshop3Lines(ch, c.dwVnum, c.bMarks, lines);
				if (lines.empty())
					continue;
				p = (long long)lines[0]->dwPrice / std::max<DWORD>(1, lines[0]->dwCount);
			}
			if (!best || cover > bestCover || (cover == bestCover && p < bestPrice))
			{
				best = &c;
				bestCover = cover;
				bestPrice = p;
			}
		}
		if (price)
			*price = bestPrice;
		return best;
	}

	std::string FormatPlayerBotSkillList(const std::vector<DWORD>& skills)
	{
		std::string s;
		for (size_t i = 0; i < skills.size(); ++i)
		{
			char one[16];
			snprintf(one, sizeof(one), "%s%u", i ? "," : "", skills[i]);
			s += one;
		}
		return s;
	}

	// Whether the bot may buy an instruction chest now: buying on, the V3 shop the source, a short skill, no unopened
	// instruction chest in hand, the gap since its last one over. shortSkills is filled.
	bool PlayerBotMayBuySkillInstrChest(LPCHARACTER ch, std::vector<DWORD>& shortSkills)
	{
		shortSkills.clear();
		if (!ch || !ch->IsItemLoaded() || !IsPlayerBotSkillInstrOn(SKILLINSTR_BUY) || GetPlayerBotItemShopSource() != 2 ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		CollectPlayerBotSkillInstrShort(ch, shortSkills);
		if (shortSkills.empty())
			return false;
		s_kPlayerBotSkillInstrCensus.shortBots.insert(ch->GetPlayerID());
		RefreshPlayerBotSkillInstrChests(get_dword_time());
		if (s_vecPlayerBotSkillInstrChests.empty())
		{
			s_kPlayerBotSkillInstrCensus.shortNoChest.insert(ch->GetPlayerID());
			return false;
		}
		const int last = ch->GetQuestFlag(PLAYERBOT_SKILL_INSTR_CHEST_FLAG);
		if (last != 0 && get_global_time() - last < GetPlayerBotSkillInstrChestGapSeconds())
			return false;
		for (size_t i = 0; i < s_vecPlayerBotSkillInstrChests.size(); ++i)
			if ((s_vecPlayerBotSkillInstrChests[i].dwVnum && ch->CountSpecifyItem(s_vecPlayerBotSkillInstrChests[i].dwVnum) > 0) ||
					(s_vecPlayerBotSkillInstrChests[i].dwBook && ch->CountSpecifyItem(s_vecPlayerBotSkillInstrChests[i].dwBook) > 0))
				return false;	// an unopened one (or its encyclopedia): the chest pass opens it first
		return true;
	}

	// The V3 goal (CollectPlayerBotIshop3Goals): one giftbox chest of the bot's short skills.
	void CollectPlayerBotSkillInstrGoals(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (n >= PLAYERBOT_ISHOP3_MAX_GOALS)
			return;
		std::vector<DWORD> shortSkills;
		if (!PlayerBotMayBuySkillInstrChest(ch, shortSkills))
			return;
		const TPlayerBotSkillInstrChest* c = PickPlayerBotSkillInstrChest(ch, shortSkills, false, NULL);
		if (!c)
		{
			bool v3 = false;
			for (size_t i = 0; i < s_vecPlayerBotSkillInstrChests.size() && !v3; ++i)
				v3 = s_vecPlayerBotSkillInstrChests[i].dwChestId != 0;
			if (!v3)
				s_kPlayerBotSkillInstrCensus.shortNoChest.insert(ch->GetPlayerID());
			return;
		}
		TPlayerBotIshop3Goal g = { c->dwVnum, c->bMarks, 1, "skill_instr", 0 };
		goals[n++] = g;
	}

	// The goal session's answer (ManagePlayerBotIshop3Goals): the chest bought - the gap starts, the census, the line.
	void NotePlayerBotSkillInstrGoalResult(LPCHARACTER ch, const TPlayerBotIshop3Goal& goal, int got)
	{
		if (!ch || !goal.szReason || strcmp(goal.szReason, "skill_instr") != 0)
			return;
		++s_kPlayerBotSkillInstrCensus.uGoals;
		if (got <= 0)
			return;
		ch->SetQuestFlag(PLAYERBOT_SKILL_INSTR_CHEST_FLAG, get_global_time());
		++s_kPlayerBotSkillInstrCensus.uChestsBought;
		s_kPlayerBotSkillInstrCensus.uChestPieces += (unsigned int)got;
		++s_kPlayerBotSkillInstrCensus.chestsByVnum[goal.dwVnum];
		std::vector<DWORD> shortSkills;
		CollectPlayerBotSkillInstrShort(ch, shortSkills);
		PlayerBotLogThrottled("skill_instr_chest", get_dword_time(),
				"PLAYERBOT_SKILL_INSTR: chest bought pid=%u name=%s lv=%d job=%u group=%u vnum=%u pieces=%d short=[%s] marks=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)ch->GetJob(), (unsigned int)ch->GetSkillGroup(),
				goal.dwVnum, got, FormatPlayerBotSkillList(shortSkills).c_str(), goal.bMarks ? 1 : 0);
	}

	// A V3 roll chest of the bot's short skills, one roll, from the goal session (the daily pool asked first).
	bool ManagePlayerBotSkillInstrV3Chest(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		std::vector<DWORD> shortSkills;
		if (s_setPlayerBotSkillInstrV3Ids.empty() || !PlayerBotMayBuySkillInstrChest(ch, shortSkills))
			return false;
		long long price = 0;
		const TPlayerBotSkillInstrChest* c = PickPlayerBotSkillInstrChest(ch, shortSkills, true, &price);
		if (!c)
			return false;
		const TPlayerBotIshop3Chest* v = NULL;
		for (size_t k = 0; k < s_vecPlayerBotIshop3Chests.size() && !v; ++k)
			if (s_vecPlayerBotIshop3Chests[k].dwChestId == c->dwChestId)
				v = &s_vecPlayerBotIshop3Chests[k];
		if (!v)
			return false;
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		if (state.iDragonCoins < (int)v->dwPrice)
			return false;
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		if ((long long)v->dwPrice > GetPlayerBotSmPoolRoom(ch, state, "skill_instr").Room())
		{
			++s_kPlayerBotSkillInstrCensus.uPoolBlock;
			++GetPlayerBotIshop3Census("skill_instr").uPoolBlock;
			return false;
		}
#endif
		const TPlayerBotIshop3Chest chest = *v;	// the purchase may re-read the catalogue
		if (!BuyPlayerBotIshop3Chest(ch, state, chest, 1, dwNow))
			return false;
		ch->SetQuestFlag(PLAYERBOT_SKILL_INSTR_CHEST_FLAG, get_global_time());
		++s_kPlayerBotSkillInstrCensus.uV3Chests;
		++s_kPlayerBotSkillInstrCensus.uChestsBought;
		PlayerBotLogThrottled("skill_instr_v3", dwNow,
				"PLAYERBOT_SKILL_INSTR: v3 chest bought pid=%u name=%s lv=%d chest=%u line=%u price=%u short=[%s]",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), chest.dwChestId, chest.dwLine, chest.dwPrice,
				FormatPlayerBotSkillList(shortSkills).c_str());
		return true;
	}

	// MT2009_PLUS_BOT_CLASS_CHESTS_V1: a class chest or its encyclopedia in the bag is opened the way the quest
	// skrzynie_klas opens it for a player (a bot runs no quest): the room first (9 cells for a chest, one a skill of the
	// path for an encyclopedia - the quest's tests), one piece taken, the contents given. Only the bot's own class's (the
	// chests carry the other classes' antiflags, MT2009_PLUS_CLASS_CHESTS_V2), out of a fight and with no window open;
	// one opening a look, a look every PLAYERBOT_CLASS_CHEST_LOOK_MS a bot. The chest's Zwoje / Rady go to the focused
	// reading, the Mikstury Madrosci to the booster pass (USE_AFFECT 510), the rings past one to
	// TrimPlayerBotTeleportRings (MT2009_PLUS_BOT_TELEPORT_RING_KEEP_V1). Off with m2_bot_skill_instr_off.
	std::map<DWORD, DWORD> s_mapPlayerBotClassChestNext;

	bool OpenPlayerBotClassChests(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !IsPlayerBotSkillInstrOn(SKILLINSTR_ALL) ||
				state.bCurrentAction == BOT_ACTION_FIGHT || ch->GetExchange() || ch->GetMyShop() || !ch->CanHandleItem())
			return false;
		if (s_mapPlayerBotClassChestNext.size() > 20000)
			s_mapPlayerBotClassChestNext.clear();
		DWORD& next = s_mapPlayerBotClassChestNext[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return false;
		next = dwNow + PLAYERBOT_CLASS_CHEST_LOOK_MS;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->isLocked() || item->IsExchanging() || IsPlayerBotSidekickHeld(ch, item))
				continue;
			bool isBook = false;
			const TPlayerBotClassChest* k = FindPlayerBotClassChest(item->GetVnum(), &isBook);
			if (!k || k->bJob != ch->GetJob() || !item->CanUsedBy(ch))
				continue;
			const DWORD vnum = item->GetVnum();
			const int need = isBook ? (int)k->bSkills : PLAYERBOT_CLASS_CHEST_CELLS;
			const int empty = ch->CountEmptyInventory();
			if (empty < need)
			{
				++s_kPlayerBotSkillInstrCensus.uClassNoRoom;
				PlayerBotLogThrottled("class_chest_room", dwNow,
						"PLAYERBOT_SKILL_INSTR: class chest waits for room pid=%u name=%s vnum=%u empty=%d need=%d",
						ch->GetPlayerID(), ch->GetName(), vnum, empty, need);
				continue;
			}
			item->SetCount(item->GetCount() - 1);
			if (!isBook)
			{
				ch->AutoGiveItem(71155, 10, -1, false);
				ch->AutoGiveItem(71001, 20, -1, false);
				ch->AutoGiveItem(71094, 10, -1, false);
				for (int r = 0; r < 5; ++r)
					ch->AutoGiveItem(70058, 1, -1, false);
				ch->AutoGiveItem(k->dwBook, 1, -1, false);
				++s_kPlayerBotSkillInstrCensus.uClassChestsOpened;
				PlayerBotLogThrottled("class_chest_open", dwNow,
						"PLAYERBOT_SKILL_INSTR: class chest opened pid=%u name=%s lv=%d job=%u group=%u vnum=%u book=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)ch->GetJob(),
						(unsigned int)ch->GetSkillGroup(), vnum, k->dwBook);
				return true;
			}
			int got[6] = { 0, 0, 0, 0, 0, 0 };
			for (int d = 0; d < PLAYERBOT_CLASS_CHEST_DRAWS; ++d)
				++got[number(0, (int)k->bSkills - 1)];
			std::string list;
			for (BYTE s = 0; s < k->bSkills; ++s)
			{
				if (got[s] <= 0)
					continue;
				ch->AutoGiveItem(50400 + k->adwSkills[s], got[s], -1, false);
				char one[24];
				snprintf(one, sizeof(one), "%s%u:%d", list.empty() ? "" : ",", 50400 + k->adwSkills[s], got[s]);
				list += one;
			}
			++s_kPlayerBotSkillInstrCensus.uClassBooksOpened;
			s_kPlayerBotSkillInstrCensus.uClassBookInstr += PLAYERBOT_CLASS_CHEST_DRAWS;
			PlayerBotLogThrottled("class_book_open", dwNow,
					"PLAYERBOT_SKILL_INSTR: encyclopedia opened pid=%u name=%s lv=%d job=%u group=%u vnum=%u instr=[%s]",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)ch->GetJob(),
					(unsigned int)ch->GetSkillGroup(), vnum, list.c_str());
			return true;
		}
		return false;
	}

	// The dearest skill's worth (the header's definition).
	DWORD GetPlayerBotSkillInstrWorth(DWORD skill)
	{
		return GetPlayerBotBookAskingBase(skill);
	}

	void NotePlayerBotSkillInstrRead(DWORD skill, bool instruction, bool landed)
	{
		std::pair<unsigned int, unsigned int>& p = instruction ? s_kPlayerBotSkillInstrCensus.readBySkill[skill]
				: s_kPlayerBotSkillInstrCensus.kuBySkill[skill];
		++p.first;
		if (landed)
			++p.second;
	}

	std::string FormatPlayerBotSkillInstrPairs(const std::map<DWORD, std::pair<unsigned int, unsigned int> >& m,
			unsigned int* reads, unsigned int* landed)
	{
		std::string s;
		for (std::map<DWORD, std::pair<unsigned int, unsigned int> >::const_iterator it = m.begin(); it != m.end(); ++it)
		{
			*reads += it->second.first;
			*landed += it->second.second;
			if (s.size() > 700)
				continue;
			char one[40];
			snprintf(one, sizeof(one), "%s%u:%u/%u", s.empty() ? "" : ",", it->first, it->second.first, it->second.second);
			s += one;
		}
		return s;
	}

	std::string FormatPlayerBotSkillInstrCounts(const std::map<DWORD, unsigned int>& m, unsigned int* total)
	{
		std::string s;
		for (std::map<DWORD, unsigned int>::const_iterator it = m.begin(); it != m.end(); ++it)
		{
			*total += it->second;
			if (s.size() > 500)
				continue;
			char one[32];
			snprintf(one, sizeof(one), "%s%u:%u", s.empty() ? "" : ",", it->first, it->second);
			s += one;
		}
		return s;
	}

	// The census, every ten minutes (from the manager's world pass).
	void WritePlayerBotSkillInstrCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotSkillInstrCensusAt == 0)
		{
			s_dwPlayerBotSkillInstrCensusAt = dwNow + PLAYERBOT_SKILL_INSTR_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwPlayerBotSkillInstrCensusAt) < 0)
			return;
		s_dwPlayerBotSkillInstrCensusAt = dwNow + PLAYERBOT_SKILL_INSTR_CENSUS_MS;
		TPlayerBotSkillInstrCensus& c = s_kPlayerBotSkillInstrCensus;
		if (!IsPlayerBotSkillInstrOn(SKILLINSTR_ALL))
		{
			sys_log(0, "PLAYERBOT_SKILL_INSTR: census off (m2_bot_skill_instr_off)");
			c = TPlayerBotSkillInstrCensus();
			return;
		}
		RefreshPlayerBotSkillInstrChests(dwNow);
		unsigned int boxes = 0;
		for (size_t i = 0; i < s_vecPlayerBotSkillInstrChests.size(); ++i)
			if (s_vecPlayerBotSkillInstrChests[i].dwVnum)
				++boxes;
		unsigned int iReads = 0, iLanded = 0, kReads = 0, kLanded = 0, rada = 0, zwoj = 0, bought = 0;
		const std::string instr = FormatPlayerBotSkillInstrPairs(c.readBySkill, &iReads, &iLanded);
		const std::string ku = FormatPlayerBotSkillInstrPairs(c.kuBySkill, &kReads, &kLanded);
		const std::string radaBy = FormatPlayerBotSkillInstrCounts(c.radaBySkill, &rada);
		const std::string zwojBy = FormatPlayerBotSkillInstrCounts(c.zwojBySkill, &zwoj);
		const std::string chestBy = FormatPlayerBotSkillInstrCounts(c.chestsByVnum, &bought);
		sys_log(0, "PLAYERBOT_SKILL_INSTR: census short_bots=%u short_no_chest=%u chests=%u (box=%u v3=%u) goals=%u "
				"chests_bought=%u by_vnum=[%s] v3_bought=%u pool_block=%u instr_read=%u/%u by_skill=[%s] ku_read=%u/%u "
				"rada=%u by_skill=[%s] zwoj=%u by_skill=[%s] rada_spill=%u listed=%u units=%u book_wait_s=%d "
				"class_chests=%u class_books=%u class_instr=%u class_no_room=%u buy=%d focus=%d keep=%d",
				(unsigned int)c.shortBots.size(), (unsigned int)c.shortNoChest.size(),
				(unsigned int)s_vecPlayerBotSkillInstrChests.size(), boxes,
				(unsigned int)s_vecPlayerBotSkillInstrChests.size() - boxes, c.uGoals, c.uChestsBought, chestBy.c_str(),
				c.uV3Chests, c.uPoolBlock, iReads, iLanded, instr.c_str(), kReads, kLanded, rada, radaBy.c_str(), zwoj,
				zwojBy.c_str(), c.uRadaSpill, c.uListed, c.uListedUnits, GetPlayerBotBookWaitSeconds(),
				c.uClassChestsOpened, c.uClassBooksOpened, c.uClassBookInstr, c.uClassNoRoom,
				IsPlayerBotSkillInstrOn(SKILLINSTR_BUY) ? 1 : 0, IsPlayerBotSkillInstrOn(SKILLINSTR_FOCUS) ? 1 : 0,
				IsPlayerBotSkillInstrOn(SKILLINSTR_KEEP) ? 1 : 0);
		c = TPlayerBotSkillInstrCensus();
	}
}

#endif

#endif
