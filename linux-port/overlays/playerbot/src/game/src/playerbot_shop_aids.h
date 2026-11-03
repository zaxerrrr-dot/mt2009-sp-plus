#ifndef __INC_METIN2_PLAYERBOT_SHOP_AIDS_H__
#define __INC_METIN2_PLAYERBOT_SHOP_AIDS_H__

// MT2009_PLUS_BOT_USE_SHOP_AIDS_V1 - the bots use the ItemShop V3's gear aids and buy them there when a pass of theirs
// wants one now (the owner, 28 October 2026: "Teach the bots to USE all of these, and buy them from ItemShop V3 when
// needed"). How each works on this server (read in the engine, the overlay and the server patches):
//
//   * Seon-Hae's Suplementy 72065 / 72066 / 72067 (V3 5 / 9 / 18 SM; 72064 Maly has no line) - playerbot_seonhae.h
//     (MT2009_PLUS_SEONHAE_V1, NPC 20095 in the first villages, quest seonhae, event flag m2_seonhae_on). A weapon or an
//     armour / jewel / glove with all five ordinary bonuses and fewer than two extra ones, 1-10 shards of the item's
//     level band (MaterialVnum - the Lucent 39078-39080 drop on Yohara; since MT2009_PLUS_BOT_SEONHAE_V2 the ordinary
//     39070-39077 / 39081 drop for bots too, at the players' rules and chances - playerbot_seonhae.h)
//     and 0-5 Suplementy of one kind: chance = 2% a shard + the kind's % x pieces / 5 (Silny 50, Duzy 20, Sredni 10),
//     rolled at hand-in, everything spent whatever the roll; Seon-Hae keeps the item m2_seonhae_wait_min (0 = 24 h),
//     then "collect" remakes it and, on a won roll, adds the bonus (AddRareAttribute; a glove: Bonus67GloveRare).
//     The quest and the chat commands refuse a bot (pc.is_bot(), Eligible). The bot does what the quest does - its
//     seonhae.npc_vid / npc_time flags at the NPC it stands by - and calls the same core functions the command calls
//     (mt2009_seonhae::Add / Collect): every check, the chance, the costs and the wait are the players'.
//   * Blogoslawienstwo Przedmiotu 71052 (V3 100005, 129 SM; a 2% mob drop) - CHARACTER::UseItemEx case 71052:
//     ChangeRareAttribute(2) - on a glove Bonus67GloveRare(change): every 6th/7th line the glove has is rolled again
//     from the pool's glove column, never one it had nor two alike. 71051 (the add) exists in item_proto and in the
//     engine, but nothing gives it (no drop, no shop, no quest - the owner: "ONLY the Seon-Hae version"), so a glove
//     gets its 6th / 7th line from Seon-Hae alone (MT2009_PLUS_SEONHAE_GLOVE_V1); 71052 then re-rolls them.
//   * Ksiega Obrobki Kamienia 71083 (V3 604, 20 SM) - USE_CLEAN_SOCKET, value0 3: up to three Pekniete Kamienie
//     (28960, a failed soul stone or demon stone) out of the item's sockets, the remaining stones shifted forward. It
//     never takes a good stone out. The bots' seating (ManagePlayerBotSoulStones, SocketPlayerBotChiStone) welds a
//     cracked stone 7 times in 10 and treated the socket as lost: the book gives it back when a stone waits for it.
//   * Kamien Kowala 71025 (V3 452, 79 SM) and Magiczny Metal 71026 (V3 451, 59 SM; 710, 350 SZ) - V1 read them as
//     unused: no use case in UseItemEx, no tuning value, no refine_proto material, no cube.txt recipe. They are the
//     Blacksmith's CRAFTING materials (MT2009_PLUS_BOT_SEONHAE_V2): Kowal 20016's "Wytwarzanie" opens crafting window 101
//     (quest crafting_manage, crafting.open(CRAFTING_BLACKSMITH)), whose rows 1-6 (crafting_data.lua, world.crafting_proto)
//     are: 25040 + 71025 -> Podrecznik Kowala 25043 (200 000 yang), 25041 + 71025 -> Podrecznik Kowala 70039 (200 000),
//     25040 + 71026 -> Zwoj Boga Smokow 25045 (100 000), 25041 + 71026 -> Zwoj Boga Smokow 71032 (100 000), 25040/25041
//     + 70035 -> Zwoj Wojny 25044 / 71021 (400 000), all 100%. 70039 / 25043 and 71032 / 25045 are USE_TUNING with
//     value0 0 (NORMAL_REFINE_SCROLL) and value1 15 / 10: DoRefineWithScroll adds value1 to the step's odds and hands a
//     failed piece back a level down, as the Blessing Scroll (value1 0) does.
//
// The bots' logic:
//   * Seon-Hae (PLAYERBOT_SEONHAE): a bot of PLAYERBOT_SEONHAE_MIN_LEVEL with the system on looks every few minutes at
//     its worn pieces the core would take (CheckItem's rules, off the body) whose band's shard it holds. The piece: by
//     need (PLAYERBOT_SEONHAE_SLOTS - the weapon and the armour most, then the glove of a Champion, the helmet, the
//     jewellery) less what its absence costs (Seon-Hae keeps it a day: a weapon or a body armour only with a wearable
//     spare in the bag, a Champion's glove a little less), a piece with no extra line yet first. The recipe: the shards
//     (1-10) and the Suplementy (kind, 0-5) of the lowest yang a won bonus - (pieces x the V3 price a piece x the yang a
//     coin + shards x their price + the day's wait, PLAYERBOT_SEONHAE_WAIT_SM) / chance - from what it holds and its
//     Smocze Monety can buy, at PLAYERBOT_SEONHAE_MIN_PCT at least (1 shard + 5 Silne, 52%, at today's prices). What the
//     recipe lacks is the V3 goal; with it in the bag (or nothing more to buy) the bot goes to the Seon-Hae of its
//     first village (the workshop's road), takes the piece off, hands it in, and comes back to collect it when it is
//     ready. One piece at a time (the core's rule).
//   * Glove 6/7 (PLAYERBOT_GLOVE67): a Sung Ma Champion whose glove has its extra lines: a line is a must (the
//     Will % of the kind its band's map lacks most - GetPlayerBotChiShortKind -, the glove's "base attribute +x%" of
//     that kind, or, lacking nothing, the boss damage line of its fighting - skills for a caster, hits else), wanted
//     (the other boss lines, the other Will %, the base attribute %, the lightning) or other. A glove with a must, or
//     with only wanted lines, is done; else 71052 re-rolls it (the glove off and on again, as the stones go in), at most
//     PLAYERBOT_GLOVE67_GIVE_UP times a glove (quest flags playerbot.g67_glove / playerbot.g67_rolls).
//   * Every other piece's 6/7 (PLAYERBOT_RARE67, MT2009_PLUS_BOT_SEONHAE_V2; the owner: "6/7 bonus re-roll on ALL items").
//     71052 on a non-glove piece is CItem::ChangeRareAttribute2 (ENABLE_ITEM_RARE_ATTR_LEVEL_PCT in char_item.cpp): the
//     piece off the body, its rare lines cleared and as many drawn again from world.item_attr_rare's column of its
//     attribute set (weighted by prob, no line twice, an old one may come back) at the levels 40/50/10 % of lv1/lv2/lv3
//     (never over the column's max); refused for a costume, no attribute set, no rare line, a young heroes' weapon, a
//     Will talisman, a Jade piece. Graded per piece by the bot's needs (GetPlayerBotRare67Role: the hunt element's power
//     % on the weapon and its resistance % on the armour, the Yohara race (devils) or the monsters line, max HP, the
//     class's attack value, the boss damage line of its fighting on the necklace, the boss defence on the shield, the
//     Will % it lacks most on a talisman; wanted: the element's hit buffs, the other boss lines, the map's other
//     elements, the "n-th bonus +x%" where the piece has that line, block ...). The glove's stopping rule (a must, or
//     only wanted lines) and a cap a slot (PLAYERBOT_RARE67_SLOTS: weapon 12, armour 10, necklace 8, helmet / bracelet /
//     shield / talisman 6, boots / earrings 5; quest flags playerbot.r67_id_<wear> / playerbot.r67_n_<wear>).
//   * The Blacksmith's scrolls (PLAYERBOT_SMITHSCROLL, MT2009_PLUS_BOT_SEONHAE_V2): a bot whose worn pieces have refine
//     steps under 100% (the scroll work's slots) makes up to PLAYERBOT_SMITH_SCROLL_TARGET better scrolls (two a step)
//     of the Blessing Scrolls it holds at a Kowal within 10 m - the town's blacksmith errand or the light pass by any
//     Kowal - Kamien Kowala first (+15), then Magiczny Metal (+10). The refining takes them through
//     FindPlayerBotRefineScrollCell (playerbot_economy.h): the smallest bonus that brings the step to 100, else the
//     largest - the better scrolls go to the low-odds steps.
//   * Clean socket (PLAYERBOT_CLEANSOCKET): a worn weapon or body armour with a cracked stone and no open socket while
//     the bag holds a soul stone the seating pass would put there (its own rules: Iwakura's tier, the grade for the
//     piece, no second of a kind), or a Champion's glove with a cracked stone, no free socket and a demon stone of
//     PLAYERBOT_CHI_STONE_MIN_LEVEL: 71083 on the piece (off and on again); the seating passes then go on as before.
//
// The shop goals (CollectPlayerBotShopAidGoals, from CollectPlayerBotIshop3Goals - playerbot_ishop3_goals.h):
// "bonus_67add" the Seon-Hae recipe's Suplementy the bag lacks, "bonus_67change" one 71052 while the glove pass would
// roll and holds none (V2: or any other piece the RARE67 pass would roll), "bonus_socket_clean" one 71083 while a piece
// waits for one and the bag holds none, "smith_scroll" (V2) the stones the craftable Blessing Scrolls lack - Magiczny
// Metal for Smocze Znaki while the bot has them, else Kamien Kowala for Smocze Monety. Logged as the
// other goals (PLAYERBOT_ISHOP3: bought / session / no coins; the hourly census by these categories).
//
// The log: PLAYERBOT_SEONHAE (plan, going, handed in, collected, refused, census), PLAYERBOT_GLOVE67 (roll, done,
// give up), PLAYERBOT_CLEANSOCKET (cleaned) and their census every PLAYERBOT_SHOP_AIDS_CENSUS_MS. Event flag
// m2_bot_shop_aids_off stops the three passes and their goals.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, right after playerbot_ishop3_goals.h; the
// tick calls ManagePlayerBotShopAids beside the workshop's errand.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1) && defined(MT2009_PLUS_BOT_USE_SHOP_AIDS_V1)

namespace
{
	const char* const PLAYERBOT_SHOP_AIDS_OFF_FLAG = "m2_bot_shop_aids_off";
	const DWORD PLAYERBOT_SHOP_AIDS_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SHOP_AIDS_LIGHT_MIN_MS = 60 * 1000;
	const DWORD PLAYERBOT_SHOP_AIDS_LIGHT_MAX_MS = 120 * 1000;

	// ---- Seon-Hae
	const int PLAYERBOT_SEONHAE_MIN_LEVEL = 50;
	const int PLAYERBOT_SEONHAE_MIN_PCT = 20;
	const long long PLAYERBOT_SEONHAE_WAIT_SM = 40;		// a day without the piece, in Smocze Monety
	const long long PLAYERBOT_SEONHAE_SHARD_YANG = 400000;	// a shard the price sheet does not name
	const DWORD PLAYERBOT_SEONHAE_CHECK_MIN_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_SEONHAE_CHECK_MAX_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SEONHAE_VISIT_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_SEONHAE_REFUSED_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_SEONHAE_ADDITIVES[4] = { 72064, 72065, 72066, 72067 };
	// the V3 price a piece where the catalogue has no line (Maly: none) - only for comparing what the bag holds
	const long long PLAYERBOT_SEONHAE_ADDITIVE_FALLBACK_SM[4] = { 3, 5, 9, 18 };

	struct TPlayerBotSeonHaeSlot
	{
		BYTE bWear;
		int iNeed;		// what a 6th/7th line on the piece is worth
		int iAbsence;	// what a day without it costs
		bool bSpare;	// handed in only with a wearable spare in the bag
	};
	const TPlayerBotSeonHaeSlot PLAYERBOT_SEONHAE_SLOTS[] = {
		{ WEAR_WEAPON, 10, 6, true },
		{ WEAR_BODY, 9, 5, true },
		{ WEAR_GLOVE, 9, 3, false },
		{ WEAR_HEAD, 7, 0, false },
		{ WEAR_PENDANT, 6, 0, false },
		{ WEAR_WRIST, 6, 0, false },
		{ WEAR_NECK, 6, 0, false },
		{ WEAR_SHIELD, 6, 0, false },
		{ WEAR_FOOTS, 5, 0, false },
		{ WEAR_EAR, 5, 0, false },
	};

	// Seon-Hae in the first villages (npc.txt of metin2_map_a1/b1/c1: (698,652), (677,585), (471,576) on the bases
	// (409600,896000), (0,102400), (921600,204800)).
	bool GetPlayerBotSeonHaePoint(long mapIndex, long& x, long& y)
	{
		switch (mapIndex)
		{
			case 1:  x = 479400; y = 961200; return true;
			case 21: x = 67700;  y = 160900; return true;
			case 41: x = 968700; y = 262400; return true;
			default: return false;
		}
	}

	// ---- the glove's 6th / 7th lines
	const DWORD PLAYERBOT_GLOVE67_CHANGE_VNUM = 71052;
	const int PLAYERBOT_GLOVE67_GIVE_UP = 12;
	const char* const PLAYERBOT_GLOVE67_FLAG_ID = "playerbot.g67_glove";
	const char* const PLAYERBOT_GLOVE67_FLAG_ROLLS = "playerbot.g67_rolls";
	enum { GLOVE67_OTHER = 1, GLOVE67_WANTED = 2, GLOVE67_MUST = 3 };

#ifdef MT2009_PLUS_BOT_SEONHAE_V2
	// ---- MT2009_PLUS_BOT_SEONHAE_V2: every other worn piece's 6th / 7th lines (PLAYERBOT_RARE67), in this order, with
	// the 71052s (129 SM each) a piece may take before the bot settles for what it has
	struct TPlayerBotRare67Slot
	{
		BYTE bWear;
		int iGiveUp;
	};
	const TPlayerBotRare67Slot PLAYERBOT_RARE67_SLOTS[] = {
		{ WEAR_WEAPON, 12 },
		{ WEAR_BODY, 10 },
		{ WEAR_NECK, 8 },
		{ WEAR_HEAD, 6 },
		{ WEAR_WRIST, 6 },
		{ WEAR_SHIELD, 6 },
		{ WEAR_PENDANT, 6 },
		{ WEAR_FOOTS, 5 },
		{ WEAR_EAR, 5 },
	};

	// ---- MT2009_PLUS_BOT_SEONHAE_V2: the Blacksmith's scrolls (Kowal 20016, crafting window 101)
	const DWORD PLAYERBOT_SMITH_NPC = 20016;
	const int PLAYERBOT_SMITH_CRAFT_RANGE = 1000;	// crafting.create: npc.is_near(10), 10 m
	const DWORD PLAYERBOT_SMITH_ROWS[] = { 1, 2, 3, 4, 5, 6 };	// crafting_data.lua [CRAFTING_BLACKSMITH]
	const DWORD PLAYERBOT_SMITH_STONE_BOOK = 71025;		// Kamien Kowala -> Podrecznik Kowala (+15)
	const DWORD PLAYERBOT_SMITH_STONE_METAL = 71026;	// Magiczny Metal -> Zwoj Boga Smokow (+10)
	const DWORD PLAYERBOT_SMITH_BASE_UNTRADEABLE = 25041;	// Zwoj Blogoslawienstwa (V3, SZ) -> 70039 / 71032
	const DWORD PLAYERBOT_SMITH_BASE_TRADEABLE = 25040;	// Zwoj Blogoslawienstwa -> 25043 / 25045
	const DWORD PLAYERBOT_SMITH_BETTER_SCROLLS[] = { 70039, 25043, 71032, 25045 };
	const int PLAYERBOT_SMITH_SCROLL_TARGET = 4;
	const int PLAYERBOT_SMITH_CRAFTS_A_VISIT = 4;
	const int PLAYERBOT_SMITH_STONE_BATCH = 3;
	const long long PLAYERBOT_SMITH_GOLD_RESERVE = 2000000;
	const long long PLAYERBOT_SMITH_PRICE_MAX = 200000;	// the dearer row (crafting_proto 3 / 6)
	const DWORD PLAYERBOT_SMITH_PAUSE_MS = 30 * 60 * 1000;
#endif

	// ---- the socket book
	const DWORD PLAYERBOT_CLEAN_SOCKET_VNUM = 71083;
	const DWORD PLAYERBOT_CRACKED_STONE_VNUM = 28960;

	struct TPlayerBotSeonHae
	{
		BYTE bPhase;	// 0 none, 1 the visit (hand in or collect)
		DWORD dwNextCheck, dwVisitStart, dwNextAction, dwRefusedUntil;
		TPlayerBotSeonHae() : bPhase(0), dwNextCheck(0), dwVisitStart(0), dwNextAction(0), dwRefusedUntil(0) {}
	};
	std::map<DWORD, TPlayerBotSeonHae> s_mapPlayerBotSeonHae;
	std::map<DWORD, DWORD> s_mapPlayerBotShopAidsLight;
	DWORD s_dwPlayerBotShopAidsCensusAt = 0;

	struct TPlayerBotShopAidsStats
	{
		unsigned int looks, plans, noPiece, noShard, lowChance, waitBuy, trips, handed, handedWon, refused, collected,
				added, notAdded, far;
		unsigned int gloveLooks, gloveDone, gloveRolls, gloveBetter, gloveGiveUp, gloveNoStone;
		unsigned int cleanWanted, cleaned, cleanNoBook;
		unsigned int rareLooks, rareDone, rareRolls, rareBetter, rareGiveUp, rareNoStone;	// MT2009_PLUS_BOT_SEONHAE_V2
		unsigned int smithCrafted, smithFar, smithNoGold;	// MT2009_PLUS_BOT_SEONHAE_V2
		TPlayerBotShopAidsStats() { memset(this, 0, sizeof(*this)); }
	};
	TPlayerBotShopAidsStats s_kPlayerBotShopAidsStats;
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
	std::map<DWORD, DWORD> s_mapPlayerBotSmithCraftPause;	// pid -> no town errand for the craft before
#endif

	bool ArePlayerBotShopAidsOff()
	{
		return quest::CQuestManager::instance().GetEventFlag(PLAYERBOT_SHOP_AIDS_OFF_FLAG) != 0;
	}

	// A bag item of the vnum (the first cell of a stack, never locked or in a trade); NULL none.
	LPITEM FindPlayerBotShopAidBagItem(LPCHARACTER ch, DWORD vnum)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && item->GetVnum() == vnum && !item->isLocked() && !item->IsExchanging())
				return item;
		}
		return NULL;
	}

	// The same, brought out of the extra inventory's storages when the bag has none.
	LPITEM FetchPlayerBotShopAidBagItem(LPCHARACTER ch, DWORD vnum)
	{
		LPITEM item = FindPlayerBotShopAidBagItem(ch, vnum);
		if (!item && ch->CountSpecifyItem(vnum) > 0 && PlayerBotEkwFetchVnum(ch, vnum))
			item = FindPlayerBotShopAidBagItem(ch, vnum);
		return item;
	}

	// The cheapest V3 price a piece in Smocze Monety (0: no line the bot's level may buy).
	long long GetPlayerBotShopAidUnitCoins(LPCHARACTER ch, DWORD vnum)
	{
		std::vector<const TPlayerBotItemShopEntry*> lines;
		SortPlayerBotIshop3Lines(ch, vnum, false, lines);
		if (lines.empty())
			return 0;
		return std::max<long long>(1, ((long long)lines[0]->dwPrice + lines[0]->dwCount - 1) / std::max<DWORD>(1, lines[0]->dwCount));
	}

	// A shard's yang, from the bots' price sheet.
	long long GetPlayerBotSeonHaeShardYang(DWORD vnum)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_MATERIAL_PRICES) / sizeof(PLAYERBOT_MATERIAL_PRICES[0]); ++i)
			if (PLAYERBOT_MATERIAL_PRICES[i].dwVnum == vnum && PLAYERBOT_MATERIAL_PRICES[i].dwPrice > 0)
				return (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_MATERIAL_PRICES[i].dwPrice);
		for (size_t i = 0; i < sizeof(PLAYERBOT_EXTRA_MATERIAL_PRICES) / sizeof(PLAYERBOT_EXTRA_MATERIAL_PRICES[0]); ++i)
			if (PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwVnum == vnum && PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwPrice > 0)
				return (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwPrice);
		return (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_SEONHAE_SHARD_YANG);
	}

	// ======================================================================== Seon-Hae

	// The core's CheckItem (playerbot_seonhae.h) for a piece still worn: what it would refuse whatever the moment.
	bool IsPlayerBotSeonHaePiece(LPCHARACTER ch, LPITEM item)
	{
		if (!item || (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR) || MlodziIsWeaponVnum(item->GetVnum()))
			return false;
		if (item->GetAttributeSetIndex() < 0 || item->GetCount() != 1 || IS_SET(item->GetFlag(), ITEM_FLAG_UNIQUE) ||
				item->isLocked() || item->IsExchanging() || IsPlayerBotSidekickPinned(ch, item))
			return false;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE t = item->GetLimitType(i);
			if (t == LIMIT_REAL_TIME || t == LIMIT_REAL_TIME_START_FIRST_USE || t == LIMIT_TIMER_BASED_ON_WEAR)
				return false;
		}
		if (item->GetAttributeCount() < ITEM_ATTRIBUTE_NORM_NUM || item->GetRareAttrCount() >= ITEM_ATTRIBUTE_RARE_NUM ||
				!mt2009_seonhae::RarePoolHasRoom(item))
			return false;
		// MT2009_PLUS_JADE_BASE_V1: the jade jewellery's two lines are its base attribute (no bonus slot) - it takes the
		// 6th and 7th bonus as any other jewellery; a Talizman Woli's slots stay its own lines
		BYTE bReserved;
		if (Mt2009WillTalismanType(item->GetVnum(), bReserved))
			return false;
		return true;
	}

	// A piece of the same kind in the bag the bot could wear while Seon-Hae keeps its own.
	bool HasPlayerBotSeonHaeSpare(LPCHARACTER ch, LPITEM worn)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item == worn || item->GetType() != worn->GetType() ||
					item->GetSubType() != worn->GetSubType() || item->isLocked() || !IsPlayerBotWearableAtLevel(ch, item->GetVnum()))
				continue;
			static const DWORD s_aJobAnti[4] = { ITEM_ANTIFLAG_WARRIOR, ITEM_ANTIFLAG_ASSASSIN, ITEM_ANTIFLAG_SURA,
				ITEM_ANTIFLAG_SHAMAN };
			const int job = (int)ch->GetJob();
			if (job >= 0 && job < 4 && IS_SET(item->GetAntiFlag(), s_aJobAnti[job]))
				continue;
			if (IS_SET(item->GetAntiFlag(), GET_SEX(ch) == SEX_MALE ? ITEM_ANTIFLAG_MALE : ITEM_ANTIFLAG_FEMALE))
				continue;
			return true;
		}
		return false;
	}

	struct TPlayerBotSeonHaePlan
	{
		LPITEM item;
		BYTE bWear;
		DWORD dwShard;
		int iShards;
		int iGrade;			// PLAYERBOT_SEONHAE_ADDITIVES index, -1 none
		int iAdditives;
		int iHeld;			// of the grade in the bag (and the storages)
		int iPct;
		long long llYangPerWin;
		const char* szWhy;	// no plan: why
		TPlayerBotSeonHaePlan() : item(NULL), bWear(0), dwShard(0), iShards(0), iGrade(-1), iAdditives(0), iHeld(0), iPct(0),
			llYangPerWin(0), szWhy("") {}
	};

	// The recipe of the lowest yang a won bonus for one piece: heldOnly - from the bag; else what the coins add.
	bool PlanPlayerBotSeonHaeRecipe(LPCHARACTER ch, const TPlayerBotAIState& state, int shardsHeld, DWORD shard,
			bool heldOnly, TPlayerBotSeonHaePlan& plan)
	{
		const long long yangPerCoin = GetPlayerBotIshop3YangPerCoin();
		const long long shardYang = GetPlayerBotSeonHaeShardYang(shard);
		const int maxShards = std::min(shardsHeld, (int)mt2009_seonhae::MATERIAL_MAX);
		const long long coinsLeft = std::max(0, state.iDragonCoins);
		bool found = false;
		for (int g = -1; g < 4; ++g)
		{
			const DWORD vnum = g >= 0 ? PLAYERBOT_SEONHAE_ADDITIVES[g] : 0;
			const int held = g >= 0 ? (int)ch->CountSpecifyItem(vnum) : 0;
			const long long unitV3 = g >= 0 ? GetPlayerBotShopAidUnitCoins(ch, vnum) : 0;
			const long long unit = unitV3 > 0 ? unitV3 : (g >= 0 ? PLAYERBOT_SEONHAE_ADDITIVE_FALLBACK_SM[g] : 0);
			int maxN = 0;
			if (g >= 0)
			{
				maxN = std::min(held, (int)mt2009_seonhae::SUPPORT_MAX);
				if (!heldOnly && unitV3 > 0)
					maxN = (int)std::min<long long>(mt2009_seonhae::SUPPORT_MAX, held + coinsLeft / unitV3);
			}
			for (int n = g >= 0 ? 1 : 0; n <= maxN; ++n)
				for (int s = 1; s <= maxShards; ++s)
				{
					const int pct = mt2009_seonhae::ChancePct(s, g >= 0 ? mt2009_seonhae::SupportPct(vnum) : 0, n);
					if (pct < PLAYERBOT_SEONHAE_MIN_PCT)
						continue;
					const long long cost = (long long)n * unit * yangPerCoin + (long long)s * shardYang +
							PLAYERBOT_SEONHAE_WAIT_SM * yangPerCoin;
					const long long perWin = cost * 100 / pct;
					if (!found || perWin < plan.llYangPerWin)
					{
						found = true;
						plan.dwShard = shard;
						plan.iShards = s;
						plan.iGrade = g;
						plan.iAdditives = n;
						plan.iHeld = held;
						plan.iPct = pct;
						plan.llYangPerWin = perWin;
					}
				}
		}
		return found;
	}

	// The piece and its recipe (heldOnly: what the bag holds now - the visit's; else with what the coins buy - the goal's).
	bool PlanPlayerBotSeonHae(LPCHARACTER ch, const TPlayerBotAIState& state, bool heldOnly, TPlayerBotSeonHaePlan& out)
	{
		out = TPlayerBotSeonHaePlan();
		if (!ch || !ch->IsItemLoaded() || ch->GetLevel() < PLAYERBOT_SEONHAE_MIN_LEVEL || !mt2009_seonhae::IsOn() ||
				mt2009_seonhae::Holding(ch) || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				ArePlayerBotShopAidsOff())
		{
			out.szWhy = "off";
			return false;
		}
		bool anyPiece = false, anyShard = false;
		int bestScore = INT_MIN;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SEONHAE_SLOTS) / sizeof(PLAYERBOT_SEONHAE_SLOTS[0]); ++i)
		{
			const TPlayerBotSeonHaeSlot& slot = PLAYERBOT_SEONHAE_SLOTS[i];
			LPITEM item = ch->GetWear(slot.bWear);
			if (!IsPlayerBotSeonHaePiece(ch, item))
				continue;
			if (slot.bSpare && !HasPlayerBotSeonHaeSpare(ch, item))
				continue;
			int absence = slot.iAbsence;
			if (slot.bWear == WEAR_GLOVE && !IsPlayerBotSungmaWillUser(ch))
				absence = 0;
			anyPiece = true;
			const DWORD shard = mt2009_seonhae::MaterialVnum(item);
			const int shards = (int)ch->CountSpecifyItem(shard);
			if (shards <= 0)
				continue;
			anyShard = true;
			// the first extra line before the second; then the need less the absence
			const int score = (item->GetRareAttrCount() == 0 ? 100 : 0) + (slot.iNeed - absence) * 10;
			if (score <= bestScore)
				continue;
			TPlayerBotSeonHaePlan p;
			if (!PlanPlayerBotSeonHaeRecipe(ch, state, shards, shard, heldOnly, p))
				continue;
			bestScore = score;
			p.item = item;
			p.bWear = slot.bWear;
			out = p;
		}
		if (out.item)
			return true;
		out.szWhy = !anyPiece ? "no_piece" : (!anyShard ? "no_shard" : "low_chance");
		return false;
	}

	// The goal: the recipe's Suplementy the bag lacks.
	int GetPlayerBotSeonHaeAdditiveNeed(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD& vnum)
	{
		TPlayerBotSeonHaePlan plan;
		if (!PlanPlayerBotSeonHae(ch, state, false, plan) || plan.iGrade < 0)
			return 0;
		vnum = PLAYERBOT_SEONHAE_ADDITIVES[plan.iGrade];
		return std::max(0, plan.iAdditives - plan.iHeld);
	}

	void EndPlayerBotSeonHaeVisit(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotSeonHae& s, DWORD dwNow, const char* why)
	{
		if (s.bPhase != 0)
			sys_log(0, "PLAYERBOT_SEONHAE: visit over pid=%u name=%s why=%s holding=%d", ch->GetPlayerID(), ch->GetName(), why,
					mt2009_seonhae::Holding(ch) ? 1 : 0);
		s.bPhase = 0;
		s.dwNextAction = 0;
		s.dwNextCheck = dwNow + number(PLAYERBOT_SEONHAE_CHECK_MIN_MS, PLAYERBOT_SEONHAE_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
	}

	LPCHARACTER FindPlayerBotSeonHaeNpc(LPCHARACTER ch)
	{
		CharacterVectorInteractor found;
		if (!CHARACTER_MANAGER::instance().GetCharactersByRaceNum(mt2009_seonhae::NPC_VNUM, found))
			return NULL;
		LPCHARACTER best = NULL;
		int bestDist = mt2009_seonhae::NPC_RANGE + 1;
		for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end(); ++it)
		{
			LPCHARACTER npc = *it;
			if (!npc || !npc->IsNPC() || npc->GetMapIndex() != ch->GetMapIndex())
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY());
			if (dist < bestDist)
			{
				bestDist = dist;
				best = npc;
			}
		}
		return best;
	}

	// Collect what Seon-Hae keeps (ready, a free cell): the core's Collect.
	bool CollectPlayerBotSeonHae(LPCHARACTER ch)
	{
		const DWORD vnum = (DWORD)ch->GetQuestFlag(mt2009_seonhae::F_VNUM);
		const int result = ch->GetQuestFlag(mt2009_seonhae::F_RESULT);
		const int pct = ch->GetQuestFlag(mt2009_seonhae::F_PCT);
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto || ch->GetEmptyInventory(proto->bSize) < 0)
		{
			PlayerBotLogThrottled("seonhae_no_room", get_dword_time(),
					"PLAYERBOT_SEONHAE: no room to collect pid=%u name=%s vnum=%u", ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		mt2009_seonhae::Collect(ch);
		if (mt2009_seonhae::Holding(ch))
		{
			++s_kPlayerBotShopAidsStats.refused;
			sys_log(0, "PLAYERBOT_SEONHAE: collect refused pid=%u name=%s vnum=%u", ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		++s_kPlayerBotShopAidsStats.collected;
		// the remade piece: the newest of its vnum in the bag
		LPITEM got = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && item->GetVnum() == vnum && (!got || item->GetID() > got->GetID()))
				got = item;
		}
		const bool won = result == mt2009_seonhae::RESULT_SUCCESS;
		if (won)
			++s_kPlayerBotShopAidsStats.added;
		else
			++s_kPlayerBotShopAidsStats.notAdded;
		char lines[96] = "";
		if (got)
		{
			int len = 0;
			for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END && len < (int)sizeof(lines) - 16; ++i)
				len += snprintf(lines + len, sizeof(lines) - len, "%s%u:%d", i == ITEM_ATTRIBUTE_RARE_START ? "" : ",",
						(unsigned int)got->GetAttributeType(i), (int)got->GetAttributeValue(i));
		}
		sys_log(0, "PLAYERBOT_SEONHAE: collected pid=%u name=%s vnum=%u pct=%d result=%s extra=[%s]", ch->GetPlayerID(),
				ch->GetName(), vnum, pct, won ? "ADDED" : "NONE", lines);
		return true;
	}

	// Hand the plan's piece in: off the body, the Suplement into the bag, the core's Add.
	bool HandPlayerBotSeonHae(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotSeonHae& s, DWORD dwNow)
	{
		TPlayerBotSeonHaePlan plan;
		if (!PlanPlayerBotSeonHae(ch, state, true, plan))
		{
			sys_log(0, "PLAYERBOT_SEONHAE: nothing to hand in pid=%u name=%s why=%s", ch->GetPlayerID(), ch->GetName(), plan.szWhy);
			return false;
		}
		LPITEM item = plan.item;
		const DWORD vnum = item->GetVnum();
		LPITEM additive = NULL;
		if (plan.iGrade >= 0)
		{
			additive = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_SEONHAE_ADDITIVES[plan.iGrade]);
			if (!additive)
				return false;
		}
		if (item->IsEquipped() && (ch->GetEmptyInventory(item->GetSize()) < 0 || !ch->UnequipItem(item) || item->IsEquipped()))
		{
			PlayerBotLogThrottled("seonhae_unequip", dwNow, "PLAYERBOT_SEONHAE: cannot take off pid=%u name=%s vnum=%u",
					ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		if (plan.iGrade >= 0 && additive->GetCell() == item->GetCell())
			return false;
		const int rareBefore = item->GetRareAttrCount();
		char args[64];
		snprintf(args, sizeof(args), "%d %d %d %d", (int)item->GetCell(), plan.iShards,
				additive ? (int)additive->GetCell() : -1, plan.iAdditives);
		mt2009_seonhae::Add(ch, args);
		if (!mt2009_seonhae::Holding(ch))
		{
			// the core's own answer for the piece (the rest - the NPC, the shards, the additive - logs its args)
			const int check = mt2009_seonhae::CheckItem(ch, item);
			++s_kPlayerBotShopAidsStats.refused;
			s.dwRefusedUntil = dwNow + PLAYERBOT_SEONHAE_REFUSED_MS;
			PlayerBotEquipItem(ch, item);
			sys_log(0, "PLAYERBOT_SEONHAE: refused pid=%u name=%s vnum=%u args=%s check=%d", ch->GetPlayerID(), ch->GetName(),
					vnum, args, check);
			return false;
		}
		++s_kPlayerBotShopAidsStats.handed;
		if (ch->GetQuestFlag(mt2009_seonhae::F_RESULT) == mt2009_seonhae::RESULT_SUCCESS)
			++s_kPlayerBotShopAidsStats.handedWon;
		sys_log(0, "PLAYERBOT_SEONHAE: handed in pid=%u name=%s lv=%d vnum=%u wear=%d extra=%d shard=%u x%d additive=%u x%d "
				"pct=%d yang_per_win=%lld ready_in_min=%d coins=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), vnum,
				(int)plan.bWear, rareBefore, plan.dwShard, plan.iShards,
				plan.iGrade >= 0 ? PLAYERBOT_SEONHAE_ADDITIVES[plan.iGrade] : 0, plan.iAdditives, plan.iPct,
				plan.llYangPerWin, (ch->GetQuestFlag(mt2009_seonhae::F_READY) - (int)get_global_time()) / 60, state.iDragonCoins);
		return true;
	}

	// What brings the bot to Seon-Hae now: 1 collect, 2 hand in, 0 nothing.
	int GetPlayerBotSeonHaeWork(LPCHARACTER ch, const TPlayerBotAIState& state, const TPlayerBotSeonHae& s, DWORD dwNow)
	{
		if (mt2009_seonhae::Holding(ch))
			return ch->GetQuestFlag(mt2009_seonhae::F_READY) <= (int)get_global_time() ? 1 : 0;
		if (s.dwRefusedUntil != 0 && (int)(dwNow - s.dwRefusedUntil) < 0)
			return 0;
		++s_kPlayerBotShopAidsStats.looks;
		TPlayerBotSeonHaePlan held, full;
		const bool okHeld = PlanPlayerBotSeonHae(ch, state, true, held);
		const bool okFull = PlanPlayerBotSeonHae(ch, state, false, full);
		if (!okHeld && !okFull)
		{
			const char* why = held.szWhy;
			if (!strcmp(why, "no_piece"))
				++s_kPlayerBotShopAidsStats.noPiece;
			else if (!strcmp(why, "no_shard"))
				++s_kPlayerBotShopAidsStats.noShard;
			else if (!strcmp(why, "low_chance"))
				++s_kPlayerBotShopAidsStats.lowChance;
			return 0;
		}
		++s_kPlayerBotShopAidsStats.plans;
		// the goal still buys what the full recipe adds: wait for it (the coins' answer is the full plan's)
		if (!okHeld || (okFull && full.iAdditives > full.iHeld && (full.item != held.item || full.iPct > held.iPct)))
		{
			++s_kPlayerBotShopAidsStats.waitBuy;
			return 0;
		}
		return 2;
	}

	// The errand: to the Seon-Hae of the first village, hand in or collect; true while it has the bot.
	bool ManagePlayerBotSeonHae(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		TPlayerBotSeonHae& s = s_mapPlayerBotSeonHae[ch->GetPlayerID()];
		const bool otherErrand = state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bVisitingUriel || state.bFishingSession ||
				state.bMarketTrip || state.bVisitingYonah;
		if (otherErrand || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch) ||
				ch->GetMyShop() != NULL || ch->GetExchange() || IsPlayerBotArezzoHeldHere(ch) || IsPlayerBotGearFrozen(ch))
		{
			if (s.bPhase != 0)
				EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "interrupted");
			return false;
		}
		if (s.bPhase == 0)
		{
			if ((int)(dwNow - s.dwNextCheck) < 0)
				return false;
			s.dwNextCheck = dwNow + number(PLAYERBOT_SEONHAE_CHECK_MIN_MS, PLAYERBOT_SEONHAE_CHECK_MAX_MS);
			const int work = GetPlayerBotSeonHaeWork(ch, state, s, dwNow);
			if (work == 0)
				return false;
			long x = 0, y = 0;
			if (!GetPlayerBotSeonHaePoint(ch->GetMapIndex(), x, y))
			{
				long homeMap = 0, homeX = 0, homeY = 0;
				if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, homeMap, homeX, homeY) ||
						!IsPlayerBotMapHostedHere(homeMap) || !GetPlayerBotSeonHaePoint(homeMap, x, y))
				{
					++s_kPlayerBotShopAidsStats.far;
					return false;
				}
				if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
				{
					s.dwNextCheck = dwNow + number(20000, 60000);
					return false;
				}
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "seonhae"))
					return false;
				s.dwNextCheck = 0;	// straight to Seon-Hae once in the village
				return true;
			}
			s.bPhase = 1;
			s.dwVisitStart = dwNow;
			s.dwNextAction = 0;
			++s_kPlayerBotShopAidsStats.trips;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_SEONHAE: going pid=%u name=%s lv=%d work=%s map=%ld coins=%d", ch->GetPlayerID(), ch->GetName(),
					ch->GetLevel(), work == 1 ? "collect" : "hand_in", ch->GetMapIndex(), state.iDragonCoins);
		}

		long x = 0, y = 0;
		if (!GetPlayerBotSeonHaePoint(ch->GetMapIndex(), x, y))
		{
			EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "left_village");
			return false;
		}
		if (dwNow - s.dwVisitStart > PLAYERBOT_SEONHAE_VISIT_MS)
		{
			EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "timeout");
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		long ax = 0, ay = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), x, y, 0x53454f4eU, ax, ay);
		if (DISTANCE_APPROX(ch->GetX() - ax, ch->GetY() - ay) > 650)
		{
			if (!MovePlayerBot(ch, ax, ay, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
			{
				sys_err("PLAYERBOT_SEONHAE: route failed pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld)", ch->GetPlayerID(),
						ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), ax, ay);
				EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "route_failed");
				return false;
			}
			return true;
		}
		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (s.dwNextAction == 0)
		{
			s.dwNextAction = dwNow + number(2000, 5000);
			return true;
		}
		if ((int)(dwNow - s.dwNextAction) < 0)
			return true;

		LPCHARACTER npc = FindPlayerBotSeonHaeNpc(ch);
		if (!npc || DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY()) > mt2009_seonhae::NPC_RANGE)
		{
			EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "no_npc");
			return false;
		}
		// what the quest writes when a player talks to him (quest seonhae: pc.setqf("npc_vid") / ("npc_time"))
		ch->SetQuestFlag(mt2009_seonhae::F_NPC_VID, (int)(DWORD)npc->GetVID());
		ch->SetQuestFlag(mt2009_seonhae::F_NPC_TIME, (int)get_global_time());
		if (mt2009_seonhae::Holding(ch))
		{
			if (ch->GetQuestFlag(mt2009_seonhae::F_READY) <= (int)get_global_time())
				CollectPlayerBotSeonHae(ch);
			EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "collect");
			return false;
		}
		HandPlayerBotSeonHae(ch, state, s, dwNow);
		EndPlayerBotSeonHaeVisit(ch, state, s, dwNow, "hand_in");
		return false;
	}

	// ======================================================================== the glove's 6th / 7th lines

	int GetPlayerBotGlove67Role(LPCHARACTER ch, LPITEM glove, BYTE type, int shortKind)
	{
		BYTE bWill = 0;
		Mt2009GloveType(glove->GetVnum(), bWill);
		const BYTE classBoss = IsPlayerBotCaster(ch) ? POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE : POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE;
		if (shortKind >= 0)
		{
			if (type == POINT_SUNGMA_PER_STR + shortKind ||
					(type == POINT_GLOVE_BASE_ATTR_PCT && bWill == POINT_SUNGMA_STR + shortKind))
				return GLOVE67_MUST;
		}
		else if (type == classBoss)
			return GLOVE67_MUST;
		if (type == POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE ||
				type == POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE ||
				type == POINT_GLOVE_BASE_ATTR_PCT || type == POINT_GLOVE_LIGHTNING ||
				(type >= POINT_SUNGMA_PER_STR && type < POINT_SUNGMA_PER_STR + 3))
			return GLOVE67_WANTED;
		return GLOVE67_OTHER;
	}

	// The stopping rule: a must line, or only wanted ones.
	bool IsPlayerBotGlove67Good(LPCHARACTER ch, LPITEM glove)
	{
		const int shortKind = GetPlayerBotChiShortKind(ch);
		bool must = false, allWanted = true;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		{
			const BYTE type = glove->GetAttributeType(i);
			if (!type)
				continue;
			const int role = GetPlayerBotGlove67Role(ch, glove, type, shortKind);
			must = must || role == GLOVE67_MUST;
			allWanted = allWanted && role >= GLOVE67_WANTED;
		}
		return must || allWanted;
	}

	// The worn glove of a Champion whose extra lines the pass would roll again (none: done, gave up, no lines).
	LPITEM GetPlayerBotGlove67Target(LPCHARACTER ch, bool count)
	{
		if (!ch || !IsPlayerBotSungmaWillUser(ch) || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				ArePlayerBotShopAidsOff())
			return NULL;
		LPITEM glove = ch->GetWear(WEAR_GLOVE);
		BYTE bWill = 0;
		if (!glove || !Mt2009GloveType(glove->GetVnum(), bWill) || glove->GetRareAttrCount() == 0 || glove->isLocked() ||
				IsPlayerBotSidekickPinned(ch, glove))
			return NULL;
		if (count)
			++s_kPlayerBotShopAidsStats.gloveLooks;
		if (IsPlayerBotGlove67Good(ch, glove))
		{
			if (count)
				++s_kPlayerBotShopAidsStats.gloveDone;
			return NULL;
		}
		if ((DWORD)ch->GetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ID) == glove->GetID() &&
				ch->GetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ROLLS) >= PLAYERBOT_GLOVE67_GIVE_UP)
		{
			if (count)
				++s_kPlayerBotShopAidsStats.gloveGiveUp;
			return NULL;
		}
		return glove;
	}

	void FormatPlayerBotGlove67Lines(LPITEM glove, char* buf, size_t size)
	{
		int len = 0;
		buf[0] = 0;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END && len >= 0 && len < (int)size - 16; ++i)
			len += snprintf(buf + len, size - len, "%s%u:%d", i == ITEM_ATTRIBUTE_RARE_START ? "" : ",",
					(unsigned int)glove->GetAttributeType(i), (int)glove->GetAttributeValue(i));
	}

	// One 71052 on the glove (off and on again, as its stones go in).
	bool ManagePlayerBotGlove67(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LPITEM glove = GetPlayerBotGlove67Target(ch, true);
		if (!glove)
			return false;
		LPITEM blessing = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_GLOVE67_CHANGE_VNUM);
		if (!blessing)
		{
			++s_kPlayerBotShopAidsStats.gloveNoStone;
			return false;
		}
		if (ch->GetEmptyInventory(glove->GetSize()) < 0 || !ch->UnequipItem(glove) || glove->IsEquipped())
			return false;
		char before[64], after[64];
		FormatPlayerBotGlove67Lines(glove, before, sizeof(before));
		const int shortKind = GetPlayerBotChiShortKind(ch);
		const DWORD gloveId = glove->GetID();
		ch->UseItemEx(blessing, TItemPos(INVENTORY, glove->GetCell()));
		FormatPlayerBotGlove67Lines(glove, after, sizeof(after));
		PlayerBotEquipItem(ch, glove);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		const bool rolled = strcmp(before, after) != 0;
		if (!rolled)
		{
			PlayerBotLogThrottled("glove67_refused", dwNow, "PLAYERBOT_GLOVE67: refused pid=%u name=%s glove=%u lines=[%s]",
					ch->GetPlayerID(), ch->GetName(), glove->GetVnum(), before);
			return false;
		}
		if ((DWORD)ch->GetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ID) != gloveId)
		{
			ch->SetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ID, (int)gloveId);
			ch->SetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ROLLS, 0);
		}
		const int rolls = ch->GetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ROLLS) + 1;
		ch->SetQuestFlag(PLAYERBOT_GLOVE67_FLAG_ROLLS, rolls);
		++s_kPlayerBotShopAidsStats.gloveRolls;
		const bool good = IsPlayerBotGlove67Good(ch, glove);
		if (good)
			++s_kPlayerBotShopAidsStats.gloveBetter;
		sys_log(0, "PLAYERBOT_GLOVE67: roll pid=%u name=%s champion=%d glove=%u short=%d lines=[%s]->[%s] rolls=%d %s",
				ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), glove->GetVnum(), shortKind, before, after, rolls,
				good ? "DONE" : (rolls >= PLAYERBOT_GLOVE67_GIVE_UP ? "GIVE_UP" : "AGAIN"));
		return true;
	}

#ifdef MT2009_PLUS_BOT_SEONHAE_V2
	// ======================================================================== every piece's 6th / 7th lines (V2)

	// MT2009_PLUS_BOT_SEONHAE_V2: the bot's needs a 6th/7th line is graded against (read once a look).
	struct TPlayerBotRare67Need
	{
		int iElement;		// the hunt element (0 lightning, 1 fire, 2 ice, 3 wind, 4 earth, 5 dark), -1 none
		bool bYohara;		// a Yohara bot (the cohorts, a Champion level)
		bool bCaster;
		int iWillShort;		// the Will kind the bot lacks most (GetPlayerBotChiShortKind), -1 none / no Will user
		int aiShare[PLAYERBOT_YOHARA_ELEMENTS];	// its Sung Ma map's element shares (all 0 elsewhere)
	};

	void ReadPlayerBotRare67Need(LPCHARACTER ch, TPlayerBotRare67Need& n)
	{
		n.iElement = GetPlayerBotHuntElementIndex(ch);
		n.bYohara = IsPlayerBotYoharaBonusMember(ch) || GetPlayerBotChampionLevel(ch) > 0;
		n.bCaster = IsPlayerBotCaster(ch);
		n.iWillShort = IsPlayerBotSungmaWillUser(ch) ? GetPlayerBotChiShortKind(ch) : -1;
		const long map = GetPlayerBotYoharaElementMap(ch);
		if (!map || !GetPlayerBotYoharaMapShares(map, n.aiShare))
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				n.aiShare[e] = 0;
	}

	// The 6th/7th "+x%" and hit-buff lines of an element, in the hunt element's order (lightning, fire, ice, wind,
	// earth, dark - playerbot_yohara_elements.h).
	const BYTE PLAYERBOT_RARE67_ENCHANT_PER[PLAYERBOT_YOHARA_ELEMENTS] = { POINT_ENCHANT_PER_ELECT, POINT_ENCHANT_PER_FIRE,
		POINT_ENCHANT_PER_ICE, POINT_ENCHANT_PER_WIND, POINT_ENCHANT_PER_EARTH, POINT_ENCHANT_PER_DARK };
	const BYTE PLAYERBOT_RARE67_RESIST_PER[PLAYERBOT_YOHARA_ELEMENTS] = { POINT_RESIST_PER_ELEC, POINT_RESIST_PER_FIRE,
		POINT_RESIST_PER_ICE, POINT_RESIST_PER_WIND, POINT_RESIST_PER_EARTH, POINT_RESIST_PER_DARK };
	const BYTE PLAYERBOT_RARE67_HIT_ENCHANT[PLAYERBOT_YOHARA_ELEMENTS] = { POINT_HIT_BUFF_ENCHANT_ELEC,
		POINT_HIT_BUFF_ENCHANT_FIRE, POINT_HIT_BUFF_ENCHANT_ICE, POINT_HIT_BUFF_ENCHANT_WIND, POINT_HIT_BUFF_ENCHANT_EARTH,
		POINT_HIT_BUFF_ENCHANT_DARK };
	const BYTE PLAYERBOT_RARE67_HIT_RESIST[PLAYERBOT_YOHARA_ELEMENTS] = { POINT_HIT_BUFF_RESIST_ELEC,
		POINT_HIT_BUFF_RESIST_FIRE, POINT_HIT_BUFF_RESIST_ICE, POINT_HIT_BUFF_RESIST_WIND, POINT_HIT_BUFF_RESIST_EARTH,
		POINT_HIT_BUFF_RESIST_DARK };

	// The element index of a line of one of the tables above (-1 none).
	int GetPlayerBotRare67LineElement(const BYTE* table, BYTE type)
	{
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (table[e] == type)
				return e;
		return -1;
	}

	// One line of a piece's 6th/7th slots: GLOVE67_MUST / GLOVE67_WANTED / GLOVE67_OTHER, by the piece's attribute set
	// (the pool's columns, world.item_attr_rare) and the bot's needs.
	int GetPlayerBotRare67Role(LPITEM item, int set, BYTE type, const TPlayerBotRare67Need& n)
	{
		const BYTE classAtt = n.bCaster ? POINT_MAGIC_ATT_GRADE_BONUS : POINT_ATT_GRADE_BONUS;
		const BYTE classBoss = n.bCaster ? POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE : POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE;
		const int e = n.iElement;
		const bool hitOwn = e >= 0 && (type == PLAYERBOT_RARE67_HIT_ENCHANT[e] || type == PLAYERBOT_RARE67_HIT_RESIST[e]);
		// "the item's own n-th bonus x% more" is worth something only where that line exists
		const bool nthOwn = type >= POINT_FIRST_ATTRIBUTE_BONUS && type <= POINT_FIFTH_ATTRIBUTE_BONUS &&
				item->GetAttributeType(type - POINT_FIRST_ATTRIBUTE_BONUS) != 0;
		switch (set)
		{
			case ATTRIBUTE_SET_WEAPON:
			{
				// the hunt element's power % and the race of the Yohara maps (devils) - else the monsters line
				if ((e >= 0 && type == PLAYERBOT_RARE67_ENCHANT_PER[e]) || (n.bYohara && type == POINT_ATTBONUS_PER_DEVIL) ||
						(!n.bYohara && type == POINT_ATTBONUS_PER_MONSTER))
					return GLOVE67_MUST;
				const int pe = GetPlayerBotRare67LineElement(PLAYERBOT_RARE67_ENCHANT_PER, type);
				if (type == POINT_ATTBONUS_PER_MONSTER || type == POINT_ATTBONUS_PER_DEVIL || type == POINT_ATTBONUS_PER_STONE ||
						type == POINT_ATTBONUS_STONE || type == classAtt || type == POINT_MAX_HP || hitOwn ||
						(pe >= 0 && n.aiShare[pe] > 0))
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
			}
			case ATTRIBUTE_SET_BODY:
			{
				if (type == POINT_MAX_HP || (e >= 0 && type == PLAYERBOT_RARE67_RESIST_PER[e]))
					return GLOVE67_MUST;
				const int re = GetPlayerBotRare67LineElement(PLAYERBOT_RARE67_RESIST_PER, type);
				if (type == POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE ||
						type == POINT_RESIST_PER_MAGIC || type == POINT_RESIST_PER_HUMAN || type == classAtt || hitOwn ||
						(re >= 0 && n.aiShare[re] > 0))
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
			}
			case ATTRIBUTE_SET_NECK:
				// the boss damage line of the bot's fighting (skills for a caster, hits else)
				if (type == classBoss || type == POINT_MAX_HP)
					return GLOVE67_MUST;
				if (type == POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE ||
						type == classAtt || type == POINT_ATTBONUS_STONE || hitOwn)
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
			case ATTRIBUTE_SET_SHIELD:
				if (type == POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE ||
						type == POINT_MAX_HP)
					return GLOVE67_MUST;
				if (type == POINT_BLOCK || type == classAtt || nthOwn || hitOwn)
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
#ifdef ENABLE_PENDANT_SYSTEM
			case ATTRIBUTE_SET_PENDANT:
				// a Will user's talisman: the Will % it lacks most
				if ((n.iWillShort >= 0 && type == POINT_SUNGMA_PER_STR + n.iWillShort) || type == POINT_MAX_HP)
					return GLOVE67_MUST;
				if ((n.iWillShort >= 0 && type >= POINT_SUNGMA_PER_STR && type <= POINT_SUNGMA_PER_IMMUNE) || type == classAtt ||
						hitOwn)
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
#endif
			case ATTRIBUTE_SET_HEAD:
			case ATTRIBUTE_SET_WRIST:
			case ATTRIBUTE_SET_FOOTS:
			case ATTRIBUTE_SET_EAR:
				if (type == POINT_MAX_HP || type == classAtt)
					return GLOVE67_MUST;
				if (nthOwn || hitOwn || type == POINT_POISON_REDUCE)
					return GLOVE67_WANTED;
				return GLOVE67_OTHER;
			default:
				return GLOVE67_OTHER;
		}
	}

	// The stopping rule, the glove's: a must line, or only wanted ones.
	bool IsPlayerBotRare67Good(LPITEM item, const TPlayerBotRare67Need& n)
	{
		const int set = item->GetAttributeSetIndex();
		bool must = false, allWanted = true;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			if (!type)
				continue;
			const int role = GetPlayerBotRare67Role(item, set, type, n);
			must = must || role == GLOVE67_MUST;
			allWanted = allWanted && role >= GLOVE67_WANTED;
		}
		return must || allWanted;
	}

	// The 71052s a piece may take before the bot settles for its lines.
	int GetPlayerBotRare67GiveUp(BYTE wear)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_RARE67_SLOTS) / sizeof(PLAYERBOT_RARE67_SLOTS[0]); ++i)
			if (PLAYERBOT_RARE67_SLOTS[i].bWear == wear)
				return PLAYERBOT_RARE67_SLOTS[i].iGiveUp;
		return 0;
	}

	void GetPlayerBotRare67Flags(BYTE wear, char* idFlag, char* rollFlag, size_t size)
	{
		snprintf(idFlag, size, "playerbot.r67_id_%u", (unsigned int)wear);
		snprintf(rollFlag, size, "playerbot.r67_n_%u", (unsigned int)wear);
	}

	// Whether CItem::ChangeRareAttribute2 would take the piece at all (char_item.cpp case 71052, item_attribute.cpp):
	// lines to change, an attribute set, not a costume; never a young heroes' weapon, a Will talisman - and the glove
	// has its own pass (PLAYERBOT_GLOVE67). MT2009_PLUS_JADE_BASE_V1: a Jade piece's 6th/7th are real bonuses now.
	bool IsPlayerBotRare67Piece(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->GetRareAttrCount() == 0 || item->GetAttributeSetIndex() < 0 || item->GetType() == ITEM_COSTUME ||
				item->isLocked() || item->IsExchanging() || IsPlayerBotSidekickPinned(ch, item) ||
				MlodziIsWeaponVnum(item->GetVnum()))
			return false;
		BYTE bReserved = 0;
		return !Mt2009WillTalismanType(item->GetVnum(), bReserved) && !Mt2009GloveType(item->GetVnum(), bReserved);
	}

	// The worn piece the pass would roll again now (the slots' order), NULL none: done, gave up, nothing to roll.
	LPITEM GetPlayerBotRare67Target(LPCHARACTER ch, bool count, BYTE* wearOut = NULL)
	{
		if (!ch || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()) || ArePlayerBotShopAidsOff())
			return NULL;
		TPlayerBotRare67Need need;
		bool needRead = false;
		for (size_t i = 0; i < sizeof(PLAYERBOT_RARE67_SLOTS) / sizeof(PLAYERBOT_RARE67_SLOTS[0]); ++i)
		{
			const BYTE wear = PLAYERBOT_RARE67_SLOTS[i].bWear;
			LPITEM item = ch->GetWear(wear);
			if (!IsPlayerBotRare67Piece(ch, item))
				continue;
			if (!needRead)
			{
				ReadPlayerBotRare67Need(ch, need);
				needRead = true;
			}
			if (count)
				++s_kPlayerBotShopAidsStats.rareLooks;
			if (IsPlayerBotRare67Good(item, need))
			{
				if (count)
					++s_kPlayerBotShopAidsStats.rareDone;
				continue;
			}
			char idFlag[48], rollFlag[48];
			GetPlayerBotRare67Flags(wear, idFlag, rollFlag, sizeof(idFlag));
			if ((DWORD)ch->GetQuestFlag(idFlag) == item->GetID() && ch->GetQuestFlag(rollFlag) >= PLAYERBOT_RARE67_SLOTS[i].iGiveUp)
			{
				if (count)
					++s_kPlayerBotShopAidsStats.rareGiveUp;
				continue;
			}
			if (wearOut)
				*wearOut = wear;
			return item;
		}
		return NULL;
	}

	// One 71052 on the piece (off and on again: the engine refuses an equipped item).
	bool ManagePlayerBotRare67(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		BYTE wear = 0;
		LPITEM item = GetPlayerBotRare67Target(ch, true, &wear);
		if (!item)
			return false;
		LPITEM blessing = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_GLOVE67_CHANGE_VNUM);
		if (!blessing)
		{
			++s_kPlayerBotShopAidsStats.rareNoStone;
			return false;
		}
		if (ch->GetEmptyInventory(item->GetSize()) < 0 || !ch->UnequipItem(item) || item->IsEquipped())
			return false;
		char before[64], after[64];
		FormatPlayerBotGlove67Lines(item, before, sizeof(before));
		const DWORD itemId = item->GetID();
		char idFlag[48], rollFlag[48];
		GetPlayerBotRare67Flags(wear, idFlag, rollFlag, sizeof(idFlag));
		ch->UseItemEx(blessing, TItemPos(INVENTORY, item->GetCell()));
		FormatPlayerBotGlove67Lines(item, after, sizeof(after));
		PlayerBotEquipItem(ch, item);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if ((DWORD)ch->GetQuestFlag(idFlag) != itemId)
		{
			ch->SetQuestFlag(idFlag, (int)itemId);
			ch->SetQuestFlag(rollFlag, 0);
		}
		if (strcmp(before, after) == 0)
		{
			// the engine refused it (a reserved piece the rules above missed): no second try on this piece
			ch->SetQuestFlag(rollFlag, GetPlayerBotRare67GiveUp(wear));
			PlayerBotLogThrottled("rare67_refused", dwNow, "PLAYERBOT_RARE67: refused pid=%u name=%s wear=%u item=%u lines=[%s]",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)wear, item->GetVnum(), before);
			return false;
		}
		const int rolls = ch->GetQuestFlag(rollFlag) + 1;
		ch->SetQuestFlag(rollFlag, rolls);
		++s_kPlayerBotShopAidsStats.rareRolls;
		TPlayerBotRare67Need need;
		ReadPlayerBotRare67Need(ch, need);
		const bool good = IsPlayerBotRare67Good(item, need);
		if (good)
			++s_kPlayerBotShopAidsStats.rareBetter;
		sys_log(0, "PLAYERBOT_RARE67: roll pid=%u name=%s wear=%u item=%u element=%d yohara=%d caster=%d will=%d lines=[%s]->[%s] "
				"rolls=%d/%d %s", ch->GetPlayerID(), ch->GetName(), (unsigned int)wear, item->GetVnum(), need.iElement,
				need.bYohara ? 1 : 0, need.bCaster ? 1 : 0, need.iWillShort, before, after, rolls, GetPlayerBotRare67GiveUp(wear),
				good ? "DONE" : (rolls >= GetPlayerBotRare67GiveUp(wear) ? "GIVE_UP" : "AGAIN"));
		return true;
	}
#endif

	// ======================================================================== the socket book

	bool HasPlayerBotCrackedSocket(LPITEM item, bool& open)
	{
		bool cracked = false;
		open = false;
		for (int i = 0; item && i < ITEM_SOCKET_MAX_NUM; ++i)
		{
			const long socket = item->GetSocket(i);
			if (socket == (long)PLAYERBOT_CRACKED_STONE_VNUM)
				cracked = true;
			else if (socket == 1)
				open = true;
		}
		return cracked;
	}

	// A soul stone in the bag the seating pass would put into this worn piece once a socket is open
	// (ManagePlayerBotSoulStones / FindPlayerBotSoulStoneSocket's rules with the cracked socket counted open).
	bool HasPlayerBotStoneWaitingFor(LPCHARACTER ch, LPITEM gear, bool weapon)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM stone = ch->GetInventoryItem(cell);
			if (!stone || stone->GetCell() != cell || stone->GetType() != ITEM_METIN || stone->GetSubType() == METIN_SUNGMA ||
					IsPlayerBotSidekickKeptForOwner(ch, stone))
				continue;
			const DWORD vnum = stone->GetVnum();
			const int kind = GetPlayerBotSoulStoneKind(vnum);
			if ((weapon ? !IsPlayerBotWeaponSoulStoneKind(kind) : !IsPlayerBotArmorSoulStoneKind(kind)) ||
					GetPlayerBotSoulStoneSeatTier(vnum) <= 0 || !ShouldPlayerBotSeatSoulStone(gear, GetPlayerBotSoulStoneGrade(vnum)))
				continue;
			bool same = false;
			for (int i = 0; i < ITEM_SOCKET_MAX_NUM && !same; ++i)
			{
				const DWORD inSocket = (DWORD)gear->GetSocket(i);
				if (inSocket <= 2 || inSocket == PLAYERBOT_CRACKED_STONE_VNUM)
					continue;
				const TItemTable* seated = ITEM_MANAGER::instance().GetTable(inSocket);
				same = seated && seated->alValues[5] == stone->GetValue(5);
			}
			if (!same)
				return true;
		}
		return false;
	}

	// The worn piece the book should clean now (NULL none).
	LPITEM GetPlayerBotCleanSocketTarget(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()) || ArePlayerBotShopAidsOff())
			return NULL;
		static const BYTE s_aWear[2] = { WEAR_WEAPON, WEAR_BODY };
		for (int w = 0; w < 2; ++w)
		{
			LPITEM gear = ch->GetWear(s_aWear[w]);
			bool open = false;
			if (!gear || IsPlayerBotSidekickPinned(ch, gear) || gear->isLocked() || !HasPlayerBotCrackedSocket(gear, open) || open)
				continue;
			if (HasPlayerBotStoneWaitingFor(ch, gear, w == 0))
				return gear;
		}
		LPITEM glove = ch->GetWear(WEAR_GLOVE);
		bool open = false;
		if (glove && IsPlayerBotSungmaWillUser(ch) && IsPlayerBotChiGloveVnum(glove->GetVnum()) && !glove->isLocked() &&
				!IsPlayerBotSidekickPinned(ch, glove) && HasPlayerBotCrackedSocket(glove, open) &&
				CountPlayerBotChiFreeSockets(glove) == 0 && CountPlayerBotChiStones(ch, false) > 0)
			return glove;
		return NULL;
	}

	bool ManagePlayerBotCleanSocket(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LPITEM gear = GetPlayerBotCleanSocketTarget(ch);
		if (!gear)
			return false;
		++s_kPlayerBotShopAidsStats.cleanWanted;
		LPITEM book = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_CLEAN_SOCKET_VNUM);
		if (!book)
		{
			++s_kPlayerBotShopAidsStats.cleanNoBook;
			return false;
		}
		if (ch->GetEmptyInventory(gear->GetSize()) < 0 || !ch->UnequipItem(gear) || gear->IsEquipped())
			return false;
		long before[3] = { 0, 0, 0 }, after[3] = { 0, 0, 0 };
		for (int i = 0; i < 3 && i < ITEM_SOCKET_MAX_NUM; ++i)
			before[i] = gear->GetSocket(i);
		ch->UseItemEx(book, TItemPos(INVENTORY, gear->GetCell()));
		for (int i = 0; i < 3 && i < ITEM_SOCKET_MAX_NUM; ++i)
			after[i] = gear->GetSocket(i);
		PlayerBotEquipItem(ch, gear);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		state.dwNextSoulStoneTime = 0;	// the stone that waited goes in at the seating pass's next look
		bool open = false;
		const bool still = HasPlayerBotCrackedSocket(gear, open);
		if (!still)
			++s_kPlayerBotShopAidsStats.cleaned;
		sys_log(0, "PLAYERBOT_CLEANSOCKET: %s pid=%u name=%s gear=%u sockets=%ld,%ld,%ld->%ld,%ld,%ld", still ? "refused" : "cleaned",
				ch->GetPlayerID(), ch->GetName(), gear->GetVnum(), before[0], before[1], before[2], after[0], after[1], after[2]);
		return !still;
	}

#ifdef MT2009_PLUS_BOT_SEONHAE_V2
	// ======================================================================== the Blacksmith's scrolls (V2)

	// The Blacksmith's recipe of this stone and this base scroll (Kowal's crafting window 101, world.crafting_proto rows
	// 1-6: 25040/25041 + 71025 -> 25043/70039, + 71026 -> 25045/71032): one of each, a refine scroll out; NULL none.
	const TCraftingItem* FindPlayerBotSmithRow(DWORD base, DWORD stone)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_SMITH_ROWS) / sizeof(PLAYERBOT_SMITH_ROWS[0]); ++i)
		{
			const TCraftingItem* row = CCraftingManager::instance().GetCraftingRecipe(PLAYERBOT_SMITH_ROWS[i]);
			if (!row || row->itemVnum == 0 || row->count <= 0)
				continue;
			bool hasBase = false, hasStone = false, other = false;
			for (int m = 0; m < CRAFTING_MATERIAL_MAX_NUM; ++m)
			{
				const DWORD v = row->materials[m].vnum;
				if (v == 0 || row->materials[m].count <= 0)
					continue;
				if (v == base && row->materials[m].count == 1)
					hasBase = true;
				else if (v == stone && row->materials[m].count == 1)
					hasStone = true;
				else
					other = true;
			}
			const TItemTable* out = ITEM_MANAGER::instance().GetTable(row->itemVnum);
			if (hasBase && hasStone && !other && out && out->bType == ITEM_USE && out->bSubType == USE_TUNING &&
					out->alValues[0] == NORMAL_REFINE_SCROLL)
				return row;
		}
		return NULL;
	}

	bool IsPlayerBotSmithScrollStone(DWORD vnum)
	{
		return vnum == PLAYERBOT_SMITH_STONE_BOOK || vnum == PLAYERBOT_SMITH_STONE_METAL;
	}

	// The worn pieces whose next step a better scroll lifts: under the scroll work (PlayerBotWearsScrollWork's slots and
	// rules) and at the refine table's odds under 100.
	int CountPlayerBotSmithScrollSteps(LPCHARACTER ch)
	{
		static const BYTE s_aWear[] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR };
		int steps = 0;
		for (size_t i = 0; i < sizeof(s_aWear) / sizeof(s_aWear[0]); ++i)
		{
			LPITEM worn = ch->GetWear(s_aWear[i]);
			if (!worn || worn->GetRefinedVnum() == 0 || IsPlayerBotScrollFreeGear(worn) ||
					worn->GetRefineLevel() >= PLAYERBOT_SCROLL_REFINE_MAX_PLUS)
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(worn->GetRefineSet());
			if (recipe && recipe->prob < 100)
				++steps;
		}
		return steps;
	}

	int CountPlayerBotSmithBetterScrolls(LPCHARACTER ch)
	{
		int n = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SMITH_BETTER_SCROLLS) / sizeof(PLAYERBOT_SMITH_BETTER_SCROLLS[0]); ++i)
			n += (int)ch->CountSpecifyItem(PLAYERBOT_SMITH_BETTER_SCROLLS[i]);
		return n;
	}

	int CountPlayerBotSmithBaseScrolls(LPCHARACTER ch)
	{
		return (int)ch->CountSpecifyItem(PLAYERBOT_SMITH_BASE_UNTRADEABLE) + (int)ch->CountSpecifyItem(PLAYERBOT_SMITH_BASE_TRADEABLE);
	}

	int CountPlayerBotSmithStones(LPCHARACTER ch)
	{
		return (int)ch->CountSpecifyItem(PLAYERBOT_SMITH_STONE_BOOK) + (int)ch->CountSpecifyItem(PLAYERBOT_SMITH_STONE_METAL);
	}

	// How many better scrolls the bot would make now: its low-odds steps want two each (up to
	// PLAYERBOT_SMITH_SCROLL_TARGET held), and each takes one Blessing Scroll it holds (a Blessing Scroll becomes a better
	// one - the count of safe scrolls stays).
	int GetPlayerBotSmithCraftable(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(ch->GetPlayerID()) || ArePlayerBotShopAidsOff() ||
				quest::CQuestManager::instance().GetEventFlag("block_crafting") > 0)
			return 0;
		const int steps = CountPlayerBotSmithScrollSteps(ch);
		if (steps <= 0)
			return 0;
		const int want = std::min(PLAYERBOT_SMITH_SCROLL_TARGET, 2 * steps) - CountPlayerBotSmithBetterScrolls(ch);
		return std::max(0, std::min(want, CountPlayerBotSmithBaseScrolls(ch)));
	}

	// ---- MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: the Zwoj Wojny of the owner's ladder (playerbot_high_gear_refine.h) - Kowal's
	// rows 1 / 4 (world.crafting_proto): a Blessing Scroll 25040 / 25041 + Magiczna Ruda Miedzi 70035 (ItemShop V3, 420
	// Smocze Znaki) + 400 000 Yang -> Zwoj Wojny 25044 / 71021, 100%: a level-100+ piece's step under +4 at 100%.
	const DWORD PLAYERBOT_WAR_ORE_VNUM = 70035;
	const int PLAYERBOT_WAR_SCROLL_HOLD_MAX = 6;
	const int PLAYERBOT_WAR_ORE_BATCH = 2;
	const int PLAYERBOT_HIGH_GEAR_BLESSING_WANT = 3;

	int CountPlayerBotWarScrolls(LPCHARACTER ch)
	{
		int n = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && GetPlayerBotScrollKind(item) == playerbot_high_gear::KIND_WAR)
				n += (int)item->GetCount();
		}
		return n;
	}

	// The War scrolls the worn level-100+ pieces' steps under +4 still want: (4 - plus) a piece, at most
	// PLAYERBOT_WAR_SCROLL_HOLD_MAX held, less what the bag holds.
	int GetPlayerBotWarScrollWant(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(ch->GetPlayerID()) || IsPlayerBotHighGearOff())
			return 0;
		int steps = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_HIGH_GEAR_WEAR) / sizeof(PLAYERBOT_HIGH_GEAR_WEAR[0]); ++i)
		{
			LPITEM worn = ch->GetWear(PLAYERBOT_HIGH_GEAR_WEAR[i]);
			if (!worn || worn->GetRefinedVnum() == 0 || !IsPlayerBotHighGear(worn) ||
					(int)worn->GetRefineLevel() >= playerbot_high_gear::WAR_BELOW)
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(worn->GetRefineSet());
			if (recipe && playerbot_high_gear::StepNeedsScroll((int)recipe->prob))
				steps += playerbot_high_gear::WAR_BELOW - (int)worn->GetRefineLevel();
		}
		return std::max(0, std::min(steps, PLAYERBOT_WAR_SCROLL_HOLD_MAX) - CountPlayerBotWarScrolls(ch));
	}

	// Kowal's row of the base scroll with the ore: one of each, a UP_TO_3TH_LEVEL scroll out.
	const TCraftingItem* FindPlayerBotWarScrollRow(DWORD base)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_SMITH_ROWS) / sizeof(PLAYERBOT_SMITH_ROWS[0]); ++i)
		{
			const TCraftingItem* row = CCraftingManager::instance().GetCraftingRecipe(PLAYERBOT_SMITH_ROWS[i]);
			if (!row || row->itemVnum == 0 || row->count <= 0)
				continue;
			bool hasBase = false, hasOre = false, other = false;
			for (int m = 0; m < CRAFTING_MATERIAL_MAX_NUM; ++m)
			{
				const DWORD v = row->materials[m].vnum;
				if (v == 0 || row->materials[m].count <= 0)
					continue;
				if (v == base && row->materials[m].count == 1)
					hasBase = true;
				else if (v == PLAYERBOT_WAR_ORE_VNUM && row->materials[m].count == 1)
					hasOre = true;
				else
					other = true;
			}
			const TItemTable* out = ITEM_MANAGER::instance().GetTable(row->itemVnum);
			if (hasBase && hasOre && !other && out && out->bType == ITEM_USE && out->bSubType == USE_TUNING &&
					out->alValues[0] == UP_TO_3TH_LEVEL_SCROLL)
				return row;
		}
		return NULL;
	}

	bool PlayerBotWantsWarScrollCraft(LPCHARACTER ch)
	{
		return ch && ch->CountSpecifyItem(PLAYERBOT_WAR_ORE_VNUM) > 0 && CountPlayerBotSmithBaseScrolls(ch) > 0 &&
				GetPlayerBotWarScrollWant(ch) > 0 && (long long)ch->GetGold() >= PLAYERBOT_SMITH_GOLD_RESERVE + 400000LL &&
				quest::CQuestManager::instance().GetEventFlag("block_crafting") <= 0;
	}

	// The War scrolls made at a Kowal within reach (the caller found him): as crafting.create makes them.
	int CraftPlayerBotWarScrolls(LPCHARACTER ch, const char* where)
	{
		int made = 0;
		static const DWORD s_aBases[2] = { PLAYERBOT_SMITH_BASE_UNTRADEABLE, PLAYERBOT_SMITH_BASE_TRADEABLE };
		for (int tries = 0; tries < PLAYERBOT_SMITH_CRAFTS_A_VISIT && PlayerBotWantsWarScrollCraft(ch); ++tries)
		{
			const TCraftingItem* row = NULL;
			LPITEM ore = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_WAR_ORE_VNUM), base = NULL;
			for (int b = 0; b < 2 && !row && ore; ++b)
			{
				if (ch->CountSpecifyItem(s_aBases[b]) <= 0)
					continue;
				const TCraftingItem* r = FindPlayerBotWarScrollRow(s_aBases[b]);
				base = r ? FetchPlayerBotShopAidBagItem(ch, s_aBases[b]) : NULL;
				if (r && base && base != ore)
					row = r;
			}
			if (!row)
			{
				++s_kPlayerBotHighGearStats.warCraftNoOre;
				break;
			}
			if ((long long)ch->GetGold() < (long long)row->price + PLAYERBOT_SMITH_GOLD_RESERVE || CountPlayerBotFreeInventoryCells(ch) < 1)
				break;
			const DWORD baseVnum = base->GetVnum();
			ore->SetCount(ore->GetCount() - 1);
			base->SetCount(base->GetCount() - 1);
			if (row->price > 0)
				PlayerBotChangeGold(ch, -(long long)row->price);
			const bool ok = number(1, 100) <= row->chance;
			if (ok)
				ch->AutoGiveItem(row->itemVnum, row->count);
			++s_kPlayerBotHighGearStats.warCrafted;
			++made;
			sys_log(0, "PLAYERBOT_HIGHGEAR: war scroll craft pid=%u name=%s where=%s row=%u %u+%u->%u x%d price=%d %s want_now=%d",
					ch->GetPlayerID(), ch->GetName(), where ? where : "-", row->vnum, baseVnum, PLAYERBOT_WAR_ORE_VNUM, row->itemVnum,
					ok ? (int)row->count : 0, row->price, ok ? "OK" : "FAILED", GetPlayerBotWarScrollWant(ch));
		}
		return made;
	}

	// The ItemShop V3 goals of the ladder: the ore for the War scrolls the bag cannot make yet (Smocze Znaki), and the
	// Blessing Scrolls (25041, Smocze Znaki) for the ore's base and the +4..+6 steps while the bag holds fewer than
	// PLAYERBOT_HIGH_GEAR_BLESSING_WANT.
	bool GetPlayerBotHighGearOreGoal(LPCHARACTER ch, TPlayerBotIshop3Goal& g)
	{
		const int want = GetPlayerBotWarScrollWant(ch) - (int)ch->CountSpecifyItem(PLAYERBOT_WAR_ORE_VNUM);
		if (want <= 0)
			return false;
		const TPlayerBotIshop3Goal o = { PLAYERBOT_WAR_ORE_VNUM, true, std::min(want, PLAYERBOT_WAR_ORE_BATCH), "hg_war_ore" };
		g = o;
		++s_kPlayerBotHighGearStats.oreGoals;
		return true;
	}

	bool GetPlayerBotHighGearBlessingGoal(LPCHARACTER ch, TPlayerBotIshop3Goal& g)
	{
		int below = 0;
		const int work = CountPlayerBotHighGearWork(ch, &below);
		if (work <= 0)
			return false;
		const int have = CountPlayerBotBlessingScrolls(ch);
		const int want = std::min(PLAYERBOT_HIGH_GEAR_BLESSING_WANT, work + (below > 0 ? 1 : 0));
		if (have >= want)
			return false;
		const TPlayerBotIshop3Goal b = { PLAYERBOT_SMITH_BASE_UNTRADEABLE, true, want - have, "hg_blessing" };
		g = b;
		++s_kPlayerBotHighGearStats.blessingGoals;
		return true;
	}

	// The town's errand (playerbot_town.h): a craft is ready - stones, Blessing Scrolls, the price - and the last try did
	// not fail on the distance a while ago.
	bool PlayerBotWantsSmithScrollCraft(LPCHARACTER ch)
	{
		if (PlayerBotWantsWarScrollCraft(ch))	// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1
			return true;
		if (!ch || CountPlayerBotSmithStones(ch) <= 0 || GetPlayerBotSmithCraftable(ch) <= 0 ||
				(long long)ch->GetGold() < PLAYERBOT_SMITH_GOLD_RESERVE + PLAYERBOT_SMITH_PRICE_MAX)
			return false;
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotSmithCraftPause.find(ch->GetPlayerID());
		return it == s_mapPlayerBotSmithCraftPause.end() || (int)(get_dword_time() - it->second) >= 0;
	}

	// The Kowal (20016) of the bot's map within the crafting window's reach (crafting.create: npc.is_near(10)).
	LPCHARACTER FindPlayerBotSmithNpc(LPCHARACTER ch)
	{
		CharacterVectorInteractor found;
		if (!CHARACTER_MANAGER::instance().GetCharactersByRaceNum(PLAYERBOT_SMITH_NPC, found))
			return NULL;
		for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end(); ++it)
		{
			LPCHARACTER npc = *it;
			if (npc && npc->IsNPC() && npc->GetMapIndex() == ch->GetMapIndex() &&
					DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY()) < PLAYERBOT_SMITH_CRAFT_RANGE)
				return npc;
		}
		return NULL;
	}

	// The crafts, as crafting.create makes them (crafting.lua: the materials out, the yang out, the row's chance, the
	// product in) - the bot has no client window to press "Wytworz" in, so the row is worked here against the same
	// CCraftingManager rows (the herbalist's way, playerbot_herbalism.h). Kamien Kowala first (+15), then Magiczny Metal
	// (+10); the untradeable Blessing Scroll (25041) before the tradeable one (25040, a counter's goods). Where: "town"
	// (the blacksmith's phase - a failure on the distance pauses the errand) or "near" (the light pass, quiet when no Kowal
	// stands by). The crafts made.
	int CraftPlayerBotSmithScrolls(LPCHARACTER ch, const char* where)
	{
		if (!ch || !ch->IsPC() || ch->IsDead() || ch->GetExchange() || ch->GetMyShop())
			return 0;
		// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: the War scrolls of the ladder first, by any Kowal within reach
		int warMade = 0;
		if (PlayerBotWantsWarScrollCraft(ch) && FindPlayerBotSmithNpc(ch))
			warMade = CraftPlayerBotWarScrolls(ch, where);
		int craftable = GetPlayerBotSmithCraftable(ch);
		if (craftable <= 0 || CountPlayerBotSmithStones(ch) <= 0)
			return warMade;
		const bool town = where && strcmp(where, "town") == 0;
		if (!FindPlayerBotSmithNpc(ch))
		{
			if (town)
			{
				++s_kPlayerBotShopAidsStats.smithFar;
				s_mapPlayerBotSmithCraftPause[ch->GetPlayerID()] = get_dword_time() + PLAYERBOT_SMITH_PAUSE_MS;
			}
			return warMade;
		}
		static const DWORD s_aStones[2] = { PLAYERBOT_SMITH_STONE_BOOK, PLAYERBOT_SMITH_STONE_METAL };
		static const DWORD s_aBases[2] = { PLAYERBOT_SMITH_BASE_UNTRADEABLE, PLAYERBOT_SMITH_BASE_TRADEABLE };
		int made = 0;
		for (int tries = 0; tries < PLAYERBOT_SMITH_CRAFTS_A_VISIT && craftable > 0; ++tries)
		{
			const TCraftingItem* row = NULL;
			LPITEM stone = NULL, base = NULL;
			for (int s = 0; s < 2 && !row; ++s)
			{
				if (ch->CountSpecifyItem(s_aStones[s]) <= 0)
					continue;
				for (int b = 0; b < 2 && !row; ++b)
				{
					if (ch->CountSpecifyItem(s_aBases[b]) <= 0)
						continue;
					const TCraftingItem* r = FindPlayerBotSmithRow(s_aBases[b], s_aStones[s]);
					if (!r)
						continue;
					stone = FetchPlayerBotShopAidBagItem(ch, s_aStones[s]);
					base = FetchPlayerBotShopAidBagItem(ch, s_aBases[b]);
					if (stone && base && stone != base)
						row = r;
				}
			}
			if (!row)
				break;
			if ((long long)ch->GetGold() < (long long)row->price + PLAYERBOT_SMITH_GOLD_RESERVE)
			{
				++s_kPlayerBotShopAidsStats.smithNoGold;
				break;
			}
			if (CountPlayerBotFreeInventoryCells(ch) < 1)
				break;
			const DWORD stoneVnum = stone->GetVnum(), baseVnum = base->GetVnum();
			stone->SetCount(stone->GetCount() - 1);
			base->SetCount(base->GetCount() - 1);
			if (row->price > 0)
				PlayerBotChangeGold(ch, -(long long)row->price);
			const bool ok = number(1, 100) <= row->chance;
			if (ok)
				ch->AutoGiveItem(row->itemVnum, row->count);
			++s_kPlayerBotShopAidsStats.smithCrafted;
			++made;
			--craftable;
			sys_log(0, "PLAYERBOT_SMITHSCROLL: craft pid=%u name=%s where=%s row=%u %u+%u->%u x%d price=%d chance=%d %s "
					"steps=%d better_now=%d", ch->GetPlayerID(), ch->GetName(), where ? where : "-", row->vnum, baseVnum, stoneVnum,
					row->itemVnum, ok ? (int)row->count : 0, row->price, row->chance, ok ? "OK" : "FAILED",
					CountPlayerBotSmithScrollSteps(ch), CountPlayerBotSmithBetterScrolls(ch));
		}
		return made + warMade;
	}

	// The goal: the stones the craftable Blessing Scrolls lack - Magiczny Metal for Smocze Znaki when the bot has them
	// (V3 line 710, 350 SZ), else Kamien Kowala for Smocze Monety (452, 79 SM; the better scroll).
	bool GetPlayerBotSmithStoneGoal(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotIshop3Goal& g)
	{
		const int need = std::min(GetPlayerBotSmithCraftable(ch) - CountPlayerBotSmithStones(ch), PLAYERBOT_SMITH_STONE_BATCH);
		if (need <= 0)
			return false;
		std::vector<const TPlayerBotItemShopEntry*> marks;
		SortPlayerBotIshop3Lines(ch, PLAYERBOT_SMITH_STONE_METAL, true, marks);
		if (!marks.empty() && state.iDragonMarks >= (int)marks[0]->dwPrice)
		{
			const TPlayerBotIshop3Goal m = { PLAYERBOT_SMITH_STONE_METAL, true, need, "smith_scroll" };
			g = m;
			return true;
		}
		const TPlayerBotIshop3Goal c = { PLAYERBOT_SMITH_STONE_BOOK, false, need, "smith_scroll" };
		g = c;
		return true;
	}

	// ======================================================================== Seon-Hae's shards on the counters (V2)

	// What a bag keeps of a shard (GetPlayerBotStallBaseKeep): a hand-in's worth (MATERIAL_MAX) while a worn piece of
	// the shard's band is one Seon-Hae would take, none else - the rest goes on the counters.
	int GetPlayerBotSeonHaeShardKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_SEONHAE_MIN_LEVEL || !mt2009_seonhae::IsOn())
			return 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SEONHAE_SLOTS) / sizeof(PLAYERBOT_SEONHAE_SLOTS[0]); ++i)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_SEONHAE_SLOTS[i].bWear);
			if (IsPlayerBotSeonHaePiece(ch, item) && mt2009_seonhae::MaterialVnum(item) == vnum)
				return mt2009_seonhae::MATERIAL_MAX;
		}
		return 0;
	}
#endif

	// ======================================================================== the goals, the tick, the census

	// MT2009_PLUS_BOT_USE_SHOP_AIDS_V1 (goals): asked by CollectPlayerBotIshop3Goals (playerbot_ishop3_goals.h).
	void CollectPlayerBotShopAidGoals(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (!ch || ArePlayerBotShopAidsOff())
			return;
		TPlayerBotAIStateMap::const_iterator state = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (state == s_mapPlayerBotAIStates.end())
			return;
		DWORD vnum = 0;
		const int additives = n < PLAYERBOT_ISHOP3_MAX_GOALS ? GetPlayerBotSeonHaeAdditiveNeed(ch, state->second, vnum) : 0;
		if (additives > 0)
		{
			const TPlayerBotIshop3Goal g = { vnum, false, additives, "bonus_67add" };
			goals[n++] = g;
		}
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && ch->CountSpecifyItem(PLAYERBOT_GLOVE67_CHANGE_VNUM) == 0 &&
				(GetPlayerBotGlove67Target(ch, false)
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
				|| GetPlayerBotRare67Target(ch, false)	// MT2009_PLUS_BOT_SEONHAE_V2: every piece with 6th/7th lines
#endif
				))
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_GLOVE67_CHANGE_VNUM, false, 1, "bonus_67change" };
			goals[n++] = g;
		}
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && ch->CountSpecifyItem(PLAYERBOT_CLEAN_SOCKET_VNUM) == 0 &&
				GetPlayerBotCleanSocketTarget(ch))
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_CLEAN_SOCKET_VNUM, false, 1, "bonus_socket_clean" };
			goals[n++] = g;
		}
		// MT2009_PLUS_RELIC_V1: the soul the bot's relic waits for (a bonus to add or a charge) - one piece, never
		// urgent (playerbot_relikty.cpp Mt2009RelicBotSoulNeed; the dailies of Dongan give them too)
		DWORD relicSoul = 0;
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && ::Mt2009RelicBotSoulNeed(ch, relicSoul) > 0 && relicSoul)
		{
			const TPlayerBotIshop3Goal g = { relicSoul, false, 1, "relic_soul" };
			goals[n++] = g;
		}
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
		// MT2009_PLUS_BOT_SEONHAE_V2: Kamien Kowala / Magiczny Metal for the Blacksmith's better scrolls.
		TPlayerBotIshop3Goal smith;
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && GetPlayerBotSmithStoneGoal(ch, state->second, smith))
			goals[n++] = smith;
		// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: the ladder's ore and Blessing Scrolls
		TPlayerBotIshop3Goal hg;
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && GetPlayerBotHighGearOreGoal(ch, hg))
			goals[n++] = hg;
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && GetPlayerBotHighGearBlessingGoal(ch, hg))
			goals[n++] = hg;
#endif
	}

	void LogPlayerBotShopAidsCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotShopAidsCensusAt != 0 && (int)(dwNow - s_dwPlayerBotShopAidsCensusAt) < 0)
			return;
		const bool first = s_dwPlayerBotShopAidsCensusAt == 0;
		s_dwPlayerBotShopAidsCensusAt = dwNow + PLAYERBOT_SHOP_AIDS_CENSUS_MS;
		if (first)
			return;
		const TPlayerBotShopAidsStats& t = s_kPlayerBotShopAidsStats;
		int holding = 0;
		for (std::map<DWORD, TPlayerBotSeonHae>::const_iterator it = s_mapPlayerBotSeonHae.begin(); it != s_mapPlayerBotSeonHae.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (ch && mt2009_seonhae::Holding(ch))
				++holding;
		}
		sys_log(0, "PLAYERBOT_SEONHAE: census on=%d looks=%u plans=%u no_piece=%u no_shard=%u low_chance=%u wait_buy=%u far=%u "
				"trips=%u handed=%u rolled_won=%u refused=%u collected=%u added=%u not_added=%u holding_now=%d",
				mt2009_seonhae::IsOn() ? 1 : 0, t.looks, t.plans, t.noPiece, t.noShard, t.lowChance, t.waitBuy, t.far, t.trips,
				t.handed, t.handedWon, t.refused, t.collected, t.added, t.notAdded, holding);
		sys_log(0, "PLAYERBOT_GLOVE67: census looks=%u done=%u rolls=%u better=%u give_up=%u no_blessing=%u",
				t.gloveLooks, t.gloveDone, t.gloveRolls, t.gloveBetter, t.gloveGiveUp, t.gloveNoStone);
		sys_log(0, "PLAYERBOT_CLEANSOCKET: census wanted=%u cleaned=%u no_book=%u", t.cleanWanted, t.cleaned, t.cleanNoBook);
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
		sys_log(0, "PLAYERBOT_RARE67: census looks=%u done=%u rolls=%u better=%u give_up=%u no_blessing=%u",
				t.rareLooks, t.rareDone, t.rareRolls, t.rareBetter, t.rareGiveUp, t.rareNoStone);
		sys_log(0, "PLAYERBOT_SMITHSCROLL: census crafted=%u far=%u no_gold=%u", t.smithCrafted, t.smithFar, t.smithNoGold);
#endif
	}

	// The tick (playerbot_manager.cpp, beside the workshop's errand): the glove and the book where the bot stands on a
	// clock of their own, then Seon-Hae's errand - true while it has the bot.
	bool ManagePlayerBotShopAids(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		LogPlayerBotShopAidsCensus(dwNow);
		LogPlayerBotHighGearCensus(dwNow);	// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1
		if (ArePlayerBotShopAidsOff())
			return false;
		DWORD& light = s_mapPlayerBotShopAidsLight[ch->GetPlayerID()];
		if ((light == 0 || (int)(dwNow - light) >= 0) && ch->GetVictim() == NULL && state.dwTargetVID == 0 &&
				!ch->GetExchange() && !ch->GetMyShop() && ch->CanHandleItem())
		{
			light = dwNow + number(PLAYERBOT_SHOP_AIDS_LIGHT_MIN_MS, PLAYERBOT_SHOP_AIDS_LIGHT_MAX_MS);
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
			// MT2009_PLUS_BOT_SEONHAE_V2: then 71052 on the other pieces, and the Blacksmith's craft while one stands by.
			CraftPlayerBotSmithScrolls(ch, "near");
			if (!ManagePlayerBotCleanSocket(ch, state, dwNow) && !ManagePlayerBotGlove67(ch, state, dwNow))
				ManagePlayerBotRare67(ch, state, dwNow);
#else
			if (!ManagePlayerBotCleanSocket(ch, state, dwNow))
				ManagePlayerBotGlove67(ch, state, dwNow);
#endif
		}
		return ManagePlayerBotSeonHae(ch, state, dwNow);
	}
}

#endif

#endif
