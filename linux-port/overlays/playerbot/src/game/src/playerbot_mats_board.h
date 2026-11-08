#ifndef __INC_METIN2_PLAYERBOT_MATS_BOARD_H__
#define __INC_METIN2_PLAYERBOT_MATS_BOARD_H__

// MT2009_PLUS_BOT_MATS_BOARD_V1 - the global board of refine materials (the owner, 8 November 2026: "Czy jest szansa
// zrobic taki globalny rynek ulepszaczy? Tzn ze boty wiedza czego im brakuje na ulepszanie i czego nie ma na rynku i
// inne boty - to dropia i wystawiaja?").
//
// The measure that asked for it (the Yohara test world, 8 November 10:54, bots 43-57 - needed / on the market / in the
// bots' bags): Kawalek Klejnotu 30021 1150 / 21 / 1290, Ezoteryczny Przewodnik 30008 792 / 7 / 1346, Ksiega Klatw+ 30080
// 482 / 13 / 809, Nieznane Lekarstwo+ 30083 368 / 37 / 782, Flaga 30052 292 / 3 / 146, Nogi Pajaka 30059 238 / 0 / 333,
// Jezyk Zaby 30060 74 / 8 / 355, Kawalek Zepsutej Zbroi 30005 38 / 3 / 323, Ogon Weza+ 30082 16 / 0 / 254. The surplus sat
// in bags, and why (the test DB, 11:06; the surplus over the holder's own worn next step):
//   * ~48 % of it (2036 of 4251 units of the nine) in the bags of bots of the second channel: shops are the first channel's alone (playerbot_channel_rules.h,
//     "wszystkie sklepy tylko na ch1") - a bot there has no counter, ever, and no pass of it sells a material to anyone but
//     the four-a-quarter-hour meetups (playerbot_meetups.h, three at a time a core);
//   * ~38 % (1595) with bots of the first channel that have no counter: since the route of the extra inventory
//     (MT2009_PLUS_BOT_EKW_ROUTE_V1, 31 October) every material lies in UPGRADE_INVENTORY, and the counter's reasons to
//     open (HasPlayerBotHoardedGoods' hoard, IsPlayerBotBagFull) read the bag's cells only - a bot with 70 Kawalek
//     Klejnotu in its materials' page and a roomy bag has no reason to open a counter;
//   * ~15 % (620) with bots that have a counter: the counter's own rules - a material the ledger calls "plenty" is held back
//     (GetPlayerBotMarketSupplyState, the world's usual count), a line a visit with the best-scored goods first.
//   (The keeps were not it: over the 2x reserve of the anvil sat only some 5 % more than over the worn step's need.)
//
// The board (a pass a core every PLAYERBOT_MATS_BOARD_PASS_MS, 3 minutes; the bots read in a rolling scan of
// PLAYERBOT_MATS_BOARD_SCAN_BOTS a second, each bot's row kept until the next look):
//   * demand: what the next step of each worn piece (weapon, armour, shield, helmet, boots, bracelet, necklace, earrings -
//     below its refine target, not outdated gear) lacks of each refine material, over the bag + the extra inventory less
//     the Biologist's share. A held bot of the progression checklist (IsPlayerBotProgressionHeld) and the gates' pieces
//     (armour, helmet, shield) come first among the buyers.
//   * supply in bags: what a bot holds of a material over its own real need - max(the anvil's reserve
//     GetPlayerBotRefineMaterialReserve (2x the recipes of its pieces within 15 levels, the crafts' keep in it), the worn
//     step's need) + the Biologist's share + the crafts' keep + a pet keeper's next stage; nothing of a kind it is short
//     of (PlayerBotNeedsRefineMaterial), GEAR2 wants (CollectPlayerBotGear2WantedMaterials) or a craft lacks
//     (CollectPlayerBotCraftMissing); never 30378 (the swap's, the Yohara shop's - GetPlayerBotCraftMaterialsWanted /
//     GetPlayerBotYoharaShopMaterialsWanted), a refine scroll, the heaven oil, an energy shard, a herb's brew; only the
//     stacks the swap's "any" path may move (IsPlayerBotMatsSwapAnyGood: not worn, locked, in a trade, under a policy or a
//     companion's).
//   * listed: the units on the shop channel's stands now (every core counts them itself - the ledger counts its own
//     channel only).
//   * unmet = demand - listed. Then, per material:
//       - the counter: a holder with a counter puts the kind up ahead (no "plenty" hold-back, +PLAYERBOT_MARKET_V3_MISSING_SCORE
//         - ScorePlayerBotShopStock), a holder of the first channel with no counter and PLAYERBOT_MATS_BOARD_COUNTER_MIN
//         units of such kinds opens one (GetPlayerBotShopReason: "nadmiar towaru"), at the market's price with the board's
//         premium (GetPlayerBotListingPrice: the shortage markup or the board's, the higher);
//       - the sale: a holder with no counter (the second channel, or none opened yet) sells to a short bot of its core -
//         the pieces from its bag to the buyer's, the yang the other way (the G0 spare's bot-to-bot sale): the market's
//         price (GetPlayerBotDealFairPrice - the sales' memory, the stands' cheapest, the asking price) + the premium,
//         never over an NPC's, the buyer paying out of PLAYERBOT_MATS_BOARD_BUY_PURSE_PCT of its spare purse; up to the
//         unmet demand, PLAYERBOT_MATS_BOARD_SALES_PER_PASS sales a pass;
//       - the buy: a short bot at a market (ManagePlayerBotOfflineShopping, after the scroll rule's pick) looks for its
//         worn steps' lacks on every stand of the map - the gambler's pick (FindPlayerBotGambleMaterialPick), out of
//         PLAYERBOT_MATS_BOARD_BUY_PURSE_PCT of its budget;
//       - the farm: what neither the stands nor the core's bags hold - ceil(lacking / PLAYERBOT_MATS_BOARD_FARM_UNITS)
//         farmers a kind (PLAYERBOT_MATS_BOARD_FARM_KIND_MAX, PLAYERBOT_MATS_BOARD_FARM_MAX a core): a bot whose need pass
//         (playerbot_dropknow.h) chose a field monster for it and that is short of it is sent to that map
//         (GetPlayerBotMatsFarmMap - a frontier map of this core, the drop still paying at its level; no dungeon, no
//         village) while the kind has a free farmer's place.
//     The premium: demand over (listed + bag supply) - (ratio - 1) x 25 %, at most PLAYERBOT_MATS_BOARD_PREMIUM_MAX (30).
// Nothing is made or given: every piece that moves was dropped by somebody and paid for; no Smocze Monety anywhere.
// Companions (IsPlayerBotSidekickPID) and players take no part on either side.
//
// Switches (event flags, looked at once a second): m2_bot_mats_board_off 1 - all of it; m2_bot_mats_board_sale_off,
// m2_bot_mats_board_list_off (the counter's boost, reason and premium), m2_bot_mats_board_buy_off,
// m2_bot_mats_board_farm_off - one part. The numbers (env, read once): PLAYERBOT_MATS_BOARD_PASS_MS (180000),
// _SCAN_BOTS (25), _SALES_PER_PASS (80), _PREMIUM_MAX (30), _COUNTER_MIN (10), _BUY_PURSE_PCT (60), _FARM_UNITS (5),
// _FARM_KIND_MAX (15), _FARM_MAX (60).
// The log: BOT_MATS_BOARD lines - pass (each pass: the kinds, the demand, the supply, the sales; throttled to one a 10
// minutes per core when nothing sold), sale (one a sale, throttled per pair of tags), buy (a buy pick, throttled), farm
// (a farmer's place taken), census every 10 minutes - the totals, then one "item" line for each of the
// PLAYERBOT_MATS_BOARD_CENSUS_ITEMS kinds of the most demand: demand / demand_bots / supply (by the holders: counter,
// first channel without one, no counter possible) / listed / unmet / premium / the held units the board does not count
// as supply by their keep (own step, short, GEAR2 / craft, reserve, locked) / sold units and yang / counter boosts /
// buy picks / farm places and farmers.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_mats_flow.h, in the anonymous namespace;
// its hooks are declared where they are asked (playerbot_town.h, playerbot_offline_market.h, playerbot_mats_flow.h,
// playerbot_dungeon_runs.h).

namespace
{
	const DWORD PLAYERBOT_MATS_BOARD_ROW_MS = 10 * 60 * 1000;	// a bot's row older than this counts no more
	const DWORD PLAYERBOT_MATS_BOARD_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_MATS_BOARD_FARM_CLAIM_MS = 2 * 60 * 1000;
	const size_t PLAYERBOT_MATS_BOARD_CENSUS_ITEMS = 16;

	struct TPlayerBotMatsBoardCfg
	{
		bool read;
		int passMs, scanBots, salesPerPass, premiumMax, counterMin, buyPursePct, farmUnits, farmKindMax, farmMax;
		TPlayerBotMatsBoardCfg() : read(false), passMs(180000), scanBots(25), salesPerPass(80), premiumMax(30), counterMin(10),
				buyPursePct(60), farmUnits(5), farmKindMax(15), farmMax(60) {}
	};
	TPlayerBotMatsBoardCfg s_kPlayerBotMatsBoardCfg;

	const TPlayerBotMatsBoardCfg& GetPlayerBotMatsBoardCfg()
	{
		TPlayerBotMatsBoardCfg& c = s_kPlayerBotMatsBoardCfg;
		if (!c.read)
		{
			c.read = true;
			c.passMs = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_PASS_MS", 180000, 30000, 3600000);
			c.scanBots = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_SCAN_BOTS", 25, 1, 500);
			c.salesPerPass = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_SALES_PER_PASS", 80, 0, 2000);
			c.premiumMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_PREMIUM_MAX", 30, 0, 200);
			c.counterMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_COUNTER_MIN", 10, 1, 1000);
			c.buyPursePct = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_BUY_PURSE_PCT", 60, 1, 100);
			c.farmUnits = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_FARM_UNITS", 5, 1, 200);
			c.farmKindMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_FARM_KIND_MAX", 15, 0, 500);
			c.farmMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOARD_FARM_MAX", 60, 0, 2000);
			sys_log(0, "BOT_MATS_BOARD: config pass_ms=%d scan_bots=%d sales_per_pass=%d premium_max=%d counter_min=%d "
					"buy_purse_pct=%d farm_units=%d farm_kind_max=%d farm_max=%d", c.passMs, c.scanBots, c.salesPerPass,
					c.premiumMax, c.counterMin, c.buyPursePct, c.farmUnits, c.farmKindMax, c.farmMax);
		}
		return c;
	}

	enum EPlayerBotMatsBoardPart
	{
		MATS_BOARD_ALL = 0,
		MATS_BOARD_SALE,
		MATS_BOARD_LIST,
		MATS_BOARD_BUY,
		MATS_BOARD_FARM,
		MATS_BOARD_PART_COUNT
	};

	bool IsPlayerBotMatsBoardOff(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[MATS_BOARD_PART_COUNT] = { false, false, false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_mats_board_off") != 0;
			s_abOff[MATS_BOARD_ALL] = all;
			s_abOff[MATS_BOARD_SALE] = all || q.GetEventFlag("m2_bot_mats_board_sale_off") != 0;
			s_abOff[MATS_BOARD_LIST] = all || q.GetEventFlag("m2_bot_mats_board_list_off") != 0;
			s_abOff[MATS_BOARD_BUY] = all || q.GetEventFlag("m2_bot_mats_board_buy_off") != 0;
			s_abOff[MATS_BOARD_FARM] = all || q.GetEventFlag("m2_bot_mats_board_farm_off") != 0;
		}
		return part < 0 || part >= MATS_BOARD_PART_COUNT || s_abOff[part];
	}

	// The held units the board does not count as supply, by the keep that holds them.
	enum EPlayerBotMatsBoardHeld
	{
		BOARD_HELD_OWN = 0,	// the worn step's own need
		BOARD_HELD_SHORT,	// a kind the bot is short of (PlayerBotNeedsRefineMaterial)
		BOARD_HELD_PLAN,	// GEAR2's or a craft's
		BOARD_HELD_KEEP,	// the reserve: the anvil's 2x, the Biologist's, the crafts', a pet's stage
		BOARD_HELD_LOCKED,	// stacks no pass may move (worn, locked, a policy, a companion's)
		BOARD_HELD_COUNT
	};
	const char* const PLAYERBOT_MATS_BOARD_HELD_NAMES[BOARD_HELD_COUNT] = { "own", "short", "plan", "keep", "locked" };

	enum EPlayerBotMatsBoardHolder
	{
		BOARD_HOLDER_COUNTER = 0,	// a counter of its own stands
		BOARD_HOLDER_CAN,		// the first channel, no counter opened
		BOARD_HOLDER_NONE,		// no counter possible (the second channel)
		BOARD_HOLDER_COUNT
	};

	// A bot's row: its lacks and its supply, by vnum.
	struct TPlayerBotMatsBoardRow
	{
		DWORD at;
		int priority;
		BYTE holder;
		std::map<DWORD, int> lack, surplus;
		std::map<DWORD, int> held[BOARD_HELD_COUNT];
		TPlayerBotMatsBoardRow() : at(0), priority(0), holder(BOARD_HOLDER_NONE) {}
	};
	std::map<DWORD, TPlayerBotMatsBoardRow> s_mapPlayerBotMatsBoardRows;

	// The board, per material, as the last pass left it.
	struct TPlayerBotMatsBoardEntry
	{
		int demand, demandBots, supply, holders, listed, unmet, premium, farmSlots;
		int supplyBy[BOARD_HOLDER_COUNT];
		int held[BOARD_HELD_COUNT];
		// since the last census
		unsigned soldUnits, sales, boosts, buyPicks, farmTaken;
		unsigned long long soldYang;
		TPlayerBotMatsBoardEntry() : demand(0), demandBots(0), supply(0), holders(0), listed(0), unmet(0), premium(0),
				farmSlots(0), soldUnits(0), sales(0), boosts(0), buyPicks(0), farmTaken(0), soldYang(0)
		{
			for (int i = 0; i < BOARD_HOLDER_COUNT; ++i)
				supplyBy[i] = 0;
			for (int i = 0; i < BOARD_HELD_COUNT; ++i)
				held[i] = 0;
		}
	};
	std::map<DWORD, TPlayerBotMatsBoardEntry> s_mapPlayerBotMatsBoard;

	struct TPlayerBotMatsBoardStats
	{
		unsigned passes, scanned, sales, saleRefused, boosts, buyPicks, farmTaken;
		unsigned long long soldUnits, soldYang;
	};
	TPlayerBotMatsBoardStats s_kPlayerBotMatsBoardStats = { 0, 0, 0, 0, 0, 0, 0, 0, 0 };

	struct TPlayerBotMatsBoardFarmClaim
	{
		DWORD vnum;
		DWORD at;
	};
	std::map<DWORD, TPlayerBotMatsBoardFarmClaim> s_mapPlayerBotMatsBoardFarm;	// pid -> its farmer's place
	std::set<DWORD> s_setPlayerBotMatsBoardCounterBots;	// the bots the board gave a counter's reason, since the census

	// ------------------------------------------------------------ the kinds

	bool IsPlayerBotMatsBoardKind(DWORD vnum)
	{
		if (vnum == 0 || vnum == PLAYERBOT_MATS_CRAFT_VNUM || vnum == PLAYERBOT_HEAVEN_OIL_VNUM || IsPlayerBotRefineScroll(vnum) ||
				IsPlayerBotSafeRefineScroll(vnum) || IsPlayerBotEnergyShardVnum(vnum) || IsPlayerBotNonGearMaterial(vnum))
			return false;
		return GetPlayerBotRefineMaterialVnums().count(vnum) != 0;
	}

	bool IsPlayerBotMatsBoardBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && ch->IsItemLoaded() &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID()) && !IsPlayerBotSidekickServing(ch);
	}

	// ------------------------------------------------------------ one bot

	// What the next steps of the worn pieces take of the board's kinds; whether a gate's piece (armour, helmet, shield)
	// is among them.
	void CollectPlayerBotMatsBoardNeed(LPCHARACTER ch, std::map<DWORD, int>& need, bool& gatePiece)
	{
		need.clear();
		gatePiece = false;
		const BYTE wears[] = { WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR };
		for (size_t i = 0; i < sizeof(wears) / sizeof(wears[0]); ++i)
		{
			LPITEM piece = ch->GetWear(wears[i]);
			if (!piece || piece->GetRefinedVnum() == 0 || piece->GetRefineSet() == 0 ||
					piece->GetRefineLevel() >= GetPlayerBotRefineTarget(ch, piece) || IsPlayerBotOutdatedGear(ch, piece))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(piece->GetRefineSet());
			for (int m = 0; recipe && m < recipe->material_count; ++m)
			{
				const DWORD vnum = recipe->materials[m].vnum;
				if (vnum == 0 || recipe->materials[m].count <= 0 || !IsPlayerBotMatsBoardKind(vnum))
					continue;
				need[vnum] += (int)recipe->materials[m].count;
				if (wears[i] == WEAR_BODY || wears[i] == WEAR_HEAD || wears[i] == WEAR_SHIELD)
					gatePiece = true;
			}
		}
	}

	int GetPlayerBotMatsBoardLackOf(LPCHARACTER ch, DWORD vnum, int need)
	{
		if (need <= 0)
			return 0;
		const int have = (int)ch->CountSpecifyItem(vnum) - GetPlayerBotBiologistReserve(ch, vnum);
		return std::max(0, need - std::max(0, have));
	}

	// The worn steps' lacks (the buy's question, live).
	void CollectPlayerBotMatsBoardLack(LPCHARACTER ch, std::map<DWORD, int>& out)
	{
		out.clear();
		if (!IsPlayerBotMatsBoardBot(ch) || IsPlayerBotMatsBoardOff(MATS_BOARD_BUY))
			return;
		std::map<DWORD, int> need;
		bool gate = false;
		CollectPlayerBotMatsBoardNeed(ch, need, gate);
		for (std::map<DWORD, int>::const_iterator it = need.begin(); it != need.end(); ++it)
		{
			const int lack = GetPlayerBotMatsBoardLackOf(ch, it->first, it->second);
			if (lack > 0)
				out[it->first] = lack;
		}
	}

	// The bot's movable stacks of the board's kinds (the bag's cells, then the materials' storage), by vnum.
	void CollectPlayerBotMatsBoardStacks(LPCHARACTER ch, std::map<DWORD, std::vector<LPITEM> >& stacks, DWORD only)
	{
		stacks.clear();
		std::vector<LPITEM> owned;
		CollectPlayerBotOwnedItems(ch, owned);
		for (size_t i = 0; i < owned.size(); ++i)
		{
			LPITEM item = owned[i];
			if (!item || (only && item->GetVnum() != only) || !IsPlayerBotMatsBoardKind(item->GetVnum()) ||
					!IsPlayerBotMatsSwapAnyGood(ch, item))
				continue;
			stacks[item->GetVnum()].push_back(item);
		}
	}

	// The keep a holder's supply of a kind is over: its real need (the anvil's reserve or the worn step's, the larger) and
	// the shares others hold it for.
	int GetPlayerBotMatsBoardKeep(LPCHARACTER ch, DWORD vnum, int need)
	{
		return std::max(GetPlayerBotRefineMaterialReserve(ch, vnum), need) + GetPlayerBotBiologistReserve(ch, vnum) +
				GetPlayerBotCraftMaterialKeep(ch, vnum) + GetPlayerBotNewPetStageKeep(ch, vnum);
	}

	// What the bot can spare of a kind, with the held units by their keep (heldOut may be NULL).
	int GetPlayerBotMatsBoardSpare(LPCHARACTER ch, DWORD vnum, int need, int movable, const std::set<DWORD>& plans,
			int* heldOut)
	{
		const int count = (int)ch->CountSpecifyItem(vnum);
		if (heldOut)
		{
			for (int i = 0; i < BOARD_HELD_COUNT; ++i)
				heldOut[i] = 0;
			heldOut[BOARD_HELD_LOCKED] = std::max(0, count - movable);
		}
		int left = std::min(count, movable);
		if (left <= 0)
			return 0;
		const int own = std::min(left, std::max(0, need));
		left -= own;
		if (heldOut)
			heldOut[BOARD_HELD_OWN] = own;
		if (left <= 0)
			return 0;
		const int why = plans.count(vnum) ? BOARD_HELD_PLAN : (PlayerBotNeedsRefineMaterial(ch, vnum) ? BOARD_HELD_SHORT : -1);
		if (why >= 0)
		{
			if (heldOut)
				heldOut[why] = left;
			return 0;
		}
		const int spare = std::min(left, count - GetPlayerBotMatsBoardKeep(ch, vnum, need));
		if (heldOut)
			heldOut[BOARD_HELD_KEEP] = left - std::max(0, spare);
		return std::max(0, spare);
	}

	// The kinds GEAR2's recipes and the crafts still want: never supply.
	void CollectPlayerBotMatsBoardPlans(LPCHARACTER ch, std::set<DWORD>& plans)
	{
		plans.clear();
		CollectPlayerBotGear2WantedMaterials(ch, plans);
		std::map<DWORD, int> craft;
		CollectPlayerBotCraftMissing(ch, craft, 1);
		for (std::map<DWORD, int>::const_iterator it = craft.begin(); it != craft.end(); ++it)
			plans.insert(it->first);
	}

	BYTE GetPlayerBotMatsBoardHolder(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (HasPlayerBotOfflineShop(ch))
			return BOARD_HOLDER_COUNTER;
#endif
		return PlayerBotHasCounter(ch) ? BOARD_HOLDER_CAN : BOARD_HOLDER_NONE;
	}

	void ScanPlayerBotMatsBoardBot(LPCHARACTER ch, DWORD dwNow)
	{
		TPlayerBotMatsBoardRow& row = s_mapPlayerBotMatsBoardRows[ch->GetPlayerID()];
		row = TPlayerBotMatsBoardRow();
		row.at = dwNow ? dwNow : 1;
		row.holder = GetPlayerBotMatsBoardHolder(ch);
		std::map<DWORD, int> need;
		bool gate = false;
		CollectPlayerBotMatsBoardNeed(ch, need, gate);
		for (std::map<DWORD, int>::const_iterator it = need.begin(); it != need.end(); ++it)
		{
			const int lack = GetPlayerBotMatsBoardLackOf(ch, it->first, it->second);
			if (lack > 0)
				row.lack[it->first] = lack;
		}
		row.priority = (IsPlayerBotProgressionHeld(ch->GetPlayerID()) ? 1000 : 0) + (gate ? 100 : 0);
		std::map<DWORD, std::vector<LPITEM> > stacks;
		CollectPlayerBotMatsBoardStacks(ch, stacks, 0);
		if (stacks.empty())
			return;
		std::set<DWORD> plans;
		CollectPlayerBotMatsBoardPlans(ch, plans);
		for (std::map<DWORD, std::vector<LPITEM> >::const_iterator it = stacks.begin(); it != stacks.end(); ++it)
		{
			int movable = 0;
			for (size_t i = 0; i < it->second.size(); ++i)
				movable += std::max<int>(1, (int)it->second[i]->GetCount());
			std::map<DWORD, int>::const_iterator n = need.find(it->first);
			int held[BOARD_HELD_COUNT];
			const int spare = GetPlayerBotMatsBoardSpare(ch, it->first, n != need.end() ? n->second : 0, movable, plans, held);
			if (spare > 0)
				row.surplus[it->first] = spare;
			for (int h = 0; h < BOARD_HELD_COUNT; ++h)
				if (held[h] > 0)
					row.held[h][it->first] = held[h];
		}
	}

	const TPlayerBotMatsBoardRow* GetPlayerBotMatsBoardRow(DWORD pid)
	{
		std::map<DWORD, TPlayerBotMatsBoardRow>::const_iterator it = s_mapPlayerBotMatsBoardRows.find(pid);
		if (it == s_mapPlayerBotMatsBoardRows.end() || get_dword_time() - it->second.at >= PLAYERBOT_MATS_BOARD_ROW_MS)
			return NULL;
		return &it->second;
	}

	// ------------------------------------------------------------ the hooks

	const TPlayerBotMatsBoardEntry* GetPlayerBotMatsBoardEntry(DWORD vnum)
	{
		std::map<DWORD, TPlayerBotMatsBoardEntry>::const_iterator it = s_mapPlayerBotMatsBoard.find(vnum);
		return it == s_mapPlayerBotMatsBoard.end() ? NULL : &it->second;
	}

	// GetPlayerBotListingPrice's markup (playerbot_town.h): the board's premium of a kind short on the market.
	int GetPlayerBotMatsBoardPremiumPercent(DWORD vnum)
	{
		if (IsPlayerBotMatsBoardOff(MATS_BOARD_LIST))
			return 0;
		const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(vnum);
		return e && e->unmet > 0 ? e->premium : 0;
	}

	// ScorePlayerBotShopStock's question (playerbot_town.h): a counter's line of a kind the board lacks, out of this
	// bot's supply - put up ahead, never held back as "plenty".
	bool IsPlayerBotMatsBoardListing(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || IsPlayerBotMatsBoardOff(MATS_BOARD_LIST) || !IsPlayerBotMatsBoardKind(vnum))
			return false;
		const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(vnum);
		if (!e || e->unmet <= 0)
			return false;
		const TPlayerBotMatsBoardRow* row = GetPlayerBotMatsBoardRow(ch->GetPlayerID());
		if (!row || !row->surplus.count(vnum))
			return false;
		++s_mapPlayerBotMatsBoard[vnum].boosts;
		++s_kPlayerBotMatsBoardStats.boosts;
		return true;
	}

	// GetPlayerBotShopReason's question (playerbot_town.h): a bot of the first channel with no counter that holds
	// PLAYERBOT_MATS_BOARD_COUNTER_MIN units of kinds the board lacks opens one.
	bool IsPlayerBotMatsBoardCounterDue(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotMatsBoardOff(MATS_BOARD_LIST) || !PlayerBotHasCounter(ch))
			return false;
		const TPlayerBotMatsBoardRow* row = GetPlayerBotMatsBoardRow(ch->GetPlayerID());
		if (!row || row->surplus.empty())
			return false;
		int units = 0;
		for (std::map<DWORD, int>::const_iterator it = row->surplus.begin(); it != row->surplus.end(); ++it)
		{
			const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(it->first);
			if (e && e->unmet > 0)
				units += std::min(it->second, e->unmet);
		}
		if (units < GetPlayerBotMatsBoardCfg().counterMin)
			return false;
		if (s_setPlayerBotMatsBoardCounterBots.size() < 50000)
			s_setPlayerBotMatsBoardCounterBots.insert(ch->GetPlayerID());
		return true;
	}

	int GetPlayerBotMatsBoardBuyPursePct()
	{
		return GetPlayerBotMatsBoardCfg().buyPursePct;
	}

	// ManagePlayerBotOfflineShopping's note of a board pick (playerbot_offline_market.h).
	void NotePlayerBotMatsBoardBuyPick(LPCHARACTER ch, const std::map<DWORD, int>& missing, DWORD owner, DWORD itemId)
	{
		++s_kPlayerBotMatsBoardStats.buyPicks;
		for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end(); ++it)
			++s_mapPlayerBotMatsBoard[it->first].buyPicks;
		PlayerBotLogThrottledEvery("mats_board_buy", get_dword_time(), 60000,
				"BOT_MATS_BOARD: buy pick pid=%u name=%s level=%d owner=%u item=%u lacking=%u first=%u(%s):%d gold=%lld picks=%u",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), owner, itemId, (unsigned int)missing.size(),
				missing.empty() ? 0u : missing.begin()->first, missing.empty() ? "-" : PlayerBotDkItemName(missing.begin()->first),
				missing.empty() ? 0 : missing.begin()->second, (long long)ch->GetGold(), s_kPlayerBotMatsBoardStats.buyPicks);
	}

	bool IsPlayerBotMatsBoardFarmKind(DWORD vnum)
	{
		if (IsPlayerBotMatsBoardOff(MATS_BOARD_FARM))
			return false;
		const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(vnum);
		return e && e->farmSlots > 0;
	}

	// DecidePlayerBotMatsFarmMap's (playerbot_mats_flow.h): a farmer's place of the kind - kept while asked again, a
	// free one taken while the kind has one. True: the bot farms it.
	bool ClaimPlayerBotMatsBoardFarm(LPCHARACTER ch, DWORD vnum, long map)
	{
		if (!ch || !IsPlayerBotMatsBoardFarmKind(vnum))
			return false;
		const DWORD pid = ch->GetPlayerID(), now = get_dword_time();
		std::map<DWORD, TPlayerBotMatsBoardFarmClaim>::iterator own = s_mapPlayerBotMatsBoardFarm.find(pid);
		if (own != s_mapPlayerBotMatsBoardFarm.end() && own->second.vnum == vnum &&
				now - own->second.at < PLAYERBOT_MATS_BOARD_FARM_CLAIM_MS)
		{
			own->second.at = now ? now : 1;
			return true;
		}
		int ofKind = 0, all = 0;
		for (std::map<DWORD, TPlayerBotMatsBoardFarmClaim>::iterator it = s_mapPlayerBotMatsBoardFarm.begin();
				it != s_mapPlayerBotMatsBoardFarm.end();)
		{
			if (now - it->second.at >= PLAYERBOT_MATS_BOARD_FARM_CLAIM_MS || it->first == pid)
			{
				s_mapPlayerBotMatsBoardFarm.erase(it++);
				continue;
			}
			++all;
			if (it->second.vnum == vnum)
				++ofKind;
			++it;
		}
		const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(vnum);
		if (!e || ofKind >= e->farmSlots || all >= GetPlayerBotMatsBoardCfg().farmMax)
			return false;
		TPlayerBotMatsBoardFarmClaim& c = s_mapPlayerBotMatsBoardFarm[pid];
		c.vnum = vnum;
		c.at = now ? now : 1;
		++s_mapPlayerBotMatsBoard[vnum].farmTaken;
		++s_kPlayerBotMatsBoardStats.farmTaken;
		sys_log(0, "BOT_MATS_BOARD: farm pid=%u name=%s level=%d item=%u(%s) map=%ld from=%ld places=%d farmers=%d demand=%d listed=%d supply=%d",
				pid, ch->GetName(), (int)ch->GetLevel(), vnum, PlayerBotDkItemName(vnum), map, ch->GetMapIndex(), e->farmSlots,
				ofKind + 1, e->demand, e->listed, e->supply);
		return true;
	}

	// ------------------------------------------------------------ the sale

	// The board's price of a unit: the market's, the premium on top, under an NPC's.
	long long GetPlayerBotMatsBoardUnitPrice(DWORD vnum, int premium)
	{
		const long long fair = GetPlayerBotDealFairPrice(vnum);
		if (fair <= 0)
			return 0;
		long long unit = fair * (100 + std::max(0, premium)) / 100;
		unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(unit, 2000000000LL), false);
		const long long npcUnit = GetPlayerBotNpcShopUnitPrice(vnum);
		if (npcUnit > 0 && unit >= npcUnit)
			unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(npcUnit * 90 / 100, 2000000000LL), false);
		return std::max(0LL, unit);
	}

	bool IsPlayerBotMatsBoardTrader(LPCHARACTER ch)
	{
		return IsPlayerBotMatsBoardBot(ch) && !ch->IsDead() && !ch->GetExchange() && !ch->GetMyShop() && !ch->IsOpenSafebox() &&
				!ch->IsCubeOpen() && !IsPlayerBotInMeetup(ch->GetPlayerID());
	}

	// One sale: `units` of the seller's spare to the buyer, the pieces from its stacks (the last first), the yang back.
	// The units sold (0: refused).
	int SellPlayerBotMatsBoardUnits(LPCHARACTER seller, LPCHARACTER buyer, DWORD vnum, int units, long long unit)
	{
		if (units <= 0 || unit <= 0 || !IsPlayerBotMatsBoardTrader(seller) || !IsPlayerBotMatsBoardTrader(buyer))
			return 0;
		// the seller's spare now
		std::map<DWORD, int> need;
		bool gate = false;
		CollectPlayerBotMatsBoardNeed(seller, need, gate);
		std::map<DWORD, std::vector<LPITEM> > stacks;
		CollectPlayerBotMatsBoardStacks(seller, stacks, vnum);
		std::vector<LPITEM>& own = stacks[vnum];
		int movable = 0;
		for (size_t i = 0; i < own.size(); ++i)
			movable += std::max<int>(1, (int)own[i]->GetCount());
		std::set<DWORD> plans;
		CollectPlayerBotMatsBoardPlans(seller, plans);
		std::map<DWORD, int>::const_iterator n = need.find(vnum);
		units = std::min(units, GetPlayerBotMatsBoardSpare(seller, vnum, n != need.end() ? n->second : 0, movable, plans, NULL));
		// the buyer's purse and room
		const long long spare = (long long)buyer->GetGold() - GetPlayerBotReservedGold(buyer) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		const long long purse = std::max(0LL, spare) * GetPlayerBotMatsBoardCfg().buyPursePct / 100;
		if ((long long)units * unit > purse)
			units = (int)(purse / unit);
		if ((long long)seller->GetGold() + (long long)units * unit >= (long long)PLAYERBOT_GOLD_MAX)
			units = 0;
		if (units <= 0 || !PlayerBotEkwHasRoomForVnum(buyer, vnum, 1))
		{
			++s_kPlayerBotMatsBoardStats.saleRefused;
			return 0;
		}
		LPITEM got = buyer->AutoGiveItem(vnum, (ITEM_COUNT)units, -1, false);
		if (!got)
		{
			++s_kPlayerBotMatsBoardStats.saleRefused;
			return 0;
		}
		// the seller's pieces, the last stacks first (the first ones hold the keep)
		int left = units;
		for (size_t i = own.size(); i > 0 && left > 0; --i)
		{
			LPITEM item = own[i - 1];
			if (!item)
				continue;
			const int count = std::max<int>(1, (int)item->GetCount());
			LogManager::instance().ItemLog(seller, item, "PLAYERBOT_MATS_BOARD_SOLD", buyer->GetName());
			if (count > left)
			{
				item->SetCount(count - left);
				left = 0;
			}
			else
			{
				left -= count;
				own[i - 1] = NULL;
				ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_MATS_BOARD_SOLD");
			}
		}
		const long long total = (long long)units * unit;
		PlayerBotChangeGold(buyer, -total);
		PlayerBotChangeGold(seller, total);
		LogManager::instance().ItemLog(buyer, got, "PLAYERBOT_MATS_BOARD_BOUGHT", seller->GetName());
		return units;
	}

	struct TPlayerBotMatsBoardBuyer
	{
		int priority;
		int lack;
		DWORD pid;
		bool operator<(const TPlayerBotMatsBoardBuyer& o) const
		{
			if (priority != o.priority)
				return priority > o.priority;
			if (lack != o.lack)
				return lack > o.lack;
			return pid < o.pid;
		}
	};

	// ------------------------------------------------------------ the pass

	// The units on the shop channel's stands, by kind (every core counts them for itself).
	void CountPlayerBotMatsBoardListed(std::map<DWORD, int>& out)
	{
		out.clear();
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
				? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			(void)pid;
			if (!shop || shop->GetDuration() == 0 || (int)shop->GetSpawn().channel != shopChannel)
				continue;
			for (const auto& [id, line] : shop->GetItems())
			{
				(void)id;
				if (line && IsPlayerBotMatsBoardKind(line->GetInfo().vnum))
					out[line->GetInfo().vnum] += (int)std::max<DWORD>(1, line->GetInfo().count);
			}
		}
#endif
	}

	void RunPlayerBotMatsBoardPass(DWORD dwNow)
	{
		const TPlayerBotMatsBoardCfg& c = GetPlayerBotMatsBoardCfg();
		++s_kPlayerBotMatsBoardStats.passes;
		// the rows of the bots still here, fresh
		std::map<DWORD, TPlayerBotMatsBoardEntry> fresh;
		for (std::map<DWORD, TPlayerBotMatsBoardRow>::iterator it = s_mapPlayerBotMatsBoardRows.begin();
				it != s_mapPlayerBotMatsBoardRows.end();)
		{
			if (!s_mapPlayerBotAIStates.count(it->first) || dwNow - it->second.at >= PLAYERBOT_MATS_BOARD_ROW_MS)
			{
				s_mapPlayerBotMatsBoardRows.erase(it++);
				continue;
			}
			const TPlayerBotMatsBoardRow& row = it->second;
			for (std::map<DWORD, int>::const_iterator l = row.lack.begin(); l != row.lack.end(); ++l)
			{
				TPlayerBotMatsBoardEntry& e = fresh[l->first];
				e.demand += l->second;
				++e.demandBots;
			}
			for (std::map<DWORD, int>::const_iterator s = row.surplus.begin(); s != row.surplus.end(); ++s)
			{
				TPlayerBotMatsBoardEntry& e = fresh[s->first];
				e.supply += s->second;
				e.supplyBy[row.holder] += s->second;
				++e.holders;
			}
			for (int h = 0; h < BOARD_HELD_COUNT; ++h)
				for (std::map<DWORD, int>::const_iterator k = row.held[h].begin(); k != row.held[h].end(); ++k)
					fresh[k->first].held[h] += k->second;
			++it;
		}
		std::map<DWORD, int> listed;
		CountPlayerBotMatsBoardListed(listed);
		// the census' counts since the last census go on
		for (std::map<DWORD, TPlayerBotMatsBoardEntry>::iterator it = fresh.begin(); it != fresh.end(); ++it)
		{
			TPlayerBotMatsBoardEntry& e = it->second;
			std::map<DWORD, TPlayerBotMatsBoardEntry>::const_iterator old = s_mapPlayerBotMatsBoard.find(it->first);
			if (old != s_mapPlayerBotMatsBoard.end())
			{
				e.soldUnits = old->second.soldUnits;
				e.sales = old->second.sales;
				e.boosts = old->second.boosts;
				e.buyPicks = old->second.buyPicks;
				e.farmTaken = old->second.farmTaken;
				e.soldYang = old->second.soldYang;
			}
			std::map<DWORD, int>::const_iterator l = listed.find(it->first);
			e.listed = l != listed.end() ? l->second : 0;
			e.unmet = std::max(0, e.demand - e.listed);
			e.premium = 0;
			if (e.demand > 0 && c.premiumMax > 0)
			{
				const long long ratio = (long long)e.demand * 100 / std::max(1, e.listed + e.supply);
				if (ratio > 100)
					e.premium = (int)std::min<long long>(c.premiumMax, (ratio - 100) / 4);
			}
		}
		s_mapPlayerBotMatsBoard.swap(fresh);

		// the sales: a holder with no counter to a short bot of the core, up to the unmet demand
		unsigned sales = 0;
		unsigned long long units = 0, yang = 0;
		std::map<DWORD, int> soldNow;
		if (!IsPlayerBotMatsBoardOff(MATS_BOARD_SALE) && c.salesPerPass > 0)
		{
			for (std::map<DWORD, TPlayerBotMatsBoardEntry>::iterator it = s_mapPlayerBotMatsBoard.begin();
					it != s_mapPlayerBotMatsBoard.end() && (int)sales < c.salesPerPass; ++it)
			{
				const DWORD vnum = it->first;
				TPlayerBotMatsBoardEntry& e = it->second;
				const int noCounter = e.supplyBy[BOARD_HOLDER_CAN] + e.supplyBy[BOARD_HOLDER_NONE];
				if (e.unmet <= 0 || noCounter <= 0)
					continue;
				const long long unit = GetPlayerBotMatsBoardUnitPrice(vnum, e.premium);
				if (unit <= 0)
					continue;
				std::vector<TPlayerBotMatsBoardBuyer> buyers;
				std::vector<std::pair<int, DWORD> > sellers;	// (spare, pid), the most first
				for (std::map<DWORD, TPlayerBotMatsBoardRow>::const_iterator r = s_mapPlayerBotMatsBoardRows.begin();
						r != s_mapPlayerBotMatsBoardRows.end(); ++r)
				{
					std::map<DWORD, int>::const_iterator l = r->second.lack.find(vnum);
					if (l != r->second.lack.end())
					{
						TPlayerBotMatsBoardBuyer b = { r->second.priority, l->second, r->first };
						buyers.push_back(b);
					}
					std::map<DWORD, int>::const_iterator s = r->second.surplus.find(vnum);
					if (s != r->second.surplus.end() && r->second.holder != BOARD_HOLDER_COUNTER)
						sellers.push_back(std::make_pair(s->second, r->first));
				}
				if (buyers.empty() || sellers.empty())
					continue;
				std::sort(buyers.begin(), buyers.end());
				std::sort(sellers.begin(), sellers.end(), std::greater<std::pair<int, DWORD> >());
				int room = e.unmet;
				size_t si = 0;
				for (size_t bi = 0; bi < buyers.size() && room > 0 && si < sellers.size() && (int)sales < c.salesPerPass; ++bi)
				{
					LPCHARACTER buyer = CHARACTER_MANAGER::instance().FindByPID(buyers[bi].pid);
					if (!buyer || !IsPlayerBotMatsBoardTrader(buyer) || !PlayerBotEkwHasRoomForVnum(buyer, vnum, 1))
						continue;
					// the buyer's lack and purse now
					int want = 0;
					{
						std::map<DWORD, int> need;
						bool gate = false;
						CollectPlayerBotMatsBoardNeed(buyer, need, gate);
						std::map<DWORD, int>::const_iterator n = need.find(vnum);
						want = std::min(room, GetPlayerBotMatsBoardLackOf(buyer, vnum, n != need.end() ? n->second : 0));
						const long long spare = (long long)buyer->GetGold() - GetPlayerBotReservedGold(buyer) -
								(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
						const long long purse = std::max(0LL, spare) * c.buyPursePct / 100;
						want = (int)std::min<long long>(want, purse / unit);
					}
					while (want > 0 && si < sellers.size() && (int)sales < c.salesPerPass)
					{
						if (sellers[si].first <= 0 || sellers[si].second == buyers[bi].pid)
						{
							++si;
							continue;
						}
						LPCHARACTER seller = CHARACTER_MANAGER::instance().FindByPID(sellers[si].second);
						const int ask = std::min(want, sellers[si].first);
						const int sold = seller ? SellPlayerBotMatsBoardUnits(seller, buyer, vnum, ask, unit) : 0;
						if (sold <= 0)
						{
							++si;	// this seller has none of it to spare now
							continue;
						}
						want -= sold;
						room -= sold;
						++sales;
						units += (unsigned long long)sold;
						yang += (unsigned long long)sold * (unsigned long long)unit;
						soldNow[vnum] += sold;
						++e.sales;
						e.soldUnits += (unsigned)sold;
						e.soldYang += (unsigned long long)sold * (unsigned long long)unit;
						// the rows move with the sale
						TPlayerBotMatsBoardRow& sr = s_mapPlayerBotMatsBoardRows[sellers[si].second];
						if ((sr.surplus[vnum] -= sold) <= 0)
							sr.surplus.erase(vnum);
						TPlayerBotMatsBoardRow& br = s_mapPlayerBotMatsBoardRows[buyers[bi].pid];
						if ((br.lack[vnum] -= sold) <= 0)
							br.lack.erase(vnum);
						sellers[si].first = sold < ask ? 0 : sellers[si].first - sold;	// less than asked: the seller's spare is out
						PlayerBotLogThrottledEvery("mats_board_sale", get_dword_time(), 2000,
								"BOT_MATS_BOARD: sale seller=%u(%s) ch=%u buyer=%u(%s) level=%d item=%u(%s) units=%d unit=%lld "
								"premium=%d demand=%d listed=%d unmet_left=%d", seller->GetPlayerID(), seller->GetName(),
								(unsigned int)g_bChannel, buyer->GetPlayerID(), buyer->GetName(), (int)buyer->GetLevel(), vnum,
								PlayerBotDkItemName(vnum), sold, unit, e.premium, e.demand, e.listed, room);
					}
				}
			}
		}
		s_kPlayerBotMatsBoardStats.sales += sales;
		s_kPlayerBotMatsBoardStats.soldUnits += units;
		s_kPlayerBotMatsBoardStats.soldYang += yang;

		// the farm: what neither the stands nor the core's bags hold, a farmer for each PLAYERBOT_MATS_BOARD_FARM_UNITS
		int kinds = 0, farmKinds = 0, farmPlaces = 0;
		long long demand = 0, supply = 0, listedAll = 0;
		for (std::map<DWORD, TPlayerBotMatsBoardEntry>::iterator it = s_mapPlayerBotMatsBoard.begin();
				it != s_mapPlayerBotMatsBoard.end(); ++it)
		{
			TPlayerBotMatsBoardEntry& e = it->second;
			std::map<DWORD, int>::const_iterator sold = soldNow.find(it->first);
			const int left = e.unmet - (sold != soldNow.end() ? sold->second : 0) -
					std::max(0, e.supply - (sold != soldNow.end() ? sold->second : 0));
			e.farmSlots = left > 0 && c.farmKindMax > 0 && !IsPlayerBotMatsBoardOff(MATS_BOARD_FARM)
					? std::min(c.farmKindMax, (left + c.farmUnits - 1) / c.farmUnits) : 0;
			if (e.demand > 0)
				++kinds;
			if (e.farmSlots > 0)
			{
				++farmKinds;
				farmPlaces += e.farmSlots;
			}
			demand += e.demand;
			supply += e.supply;
			listedAll += e.listed;
		}
		if (sales > 0)
			sys_log(0, "BOT_MATS_BOARD: pass rows=%u kinds=%d demand=%lld supply=%lld listed=%lld sales=%u units=%llu yang=%llu "
					"farm_kinds=%d farm_places=%d ch=%u", (unsigned int)s_mapPlayerBotMatsBoardRows.size(), kinds, demand, supply,
					listedAll, sales, units, yang, farmKinds, farmPlaces, (unsigned int)g_bChannel);
		else
			PlayerBotLogThrottledEvery("mats_board_pass", get_dword_time(), PLAYERBOT_MATS_BOARD_CENSUS_MS,
					"BOT_MATS_BOARD: pass rows=%u kinds=%d demand=%lld supply=%lld listed=%lld sales=0 farm_kinds=%d farm_places=%d ch=%u",
					(unsigned int)s_mapPlayerBotMatsBoardRows.size(), kinds, demand, supply, listedAll, farmKinds, farmPlaces,
					(unsigned int)g_bChannel);
	}

	void LogPlayerBotMatsBoardCensus()
	{
		const TPlayerBotMatsBoardStats& s = s_kPlayerBotMatsBoardStats;
		std::vector<std::pair<int, DWORD> > ranked;
		for (std::map<DWORD, TPlayerBotMatsBoardEntry>::const_iterator it = s_mapPlayerBotMatsBoard.begin();
				it != s_mapPlayerBotMatsBoard.end(); ++it)
			if (it->second.demand > 0 || it->second.soldUnits > 0)
				ranked.push_back(std::make_pair(it->second.demand, it->first));
		std::sort(ranked.begin(), ranked.end(), std::greater<std::pair<int, DWORD> >());
		int farmers = 0;
		const DWORD now = get_dword_time();
		for (std::map<DWORD, TPlayerBotMatsBoardFarmClaim>::const_iterator it = s_mapPlayerBotMatsBoardFarm.begin();
				it != s_mapPlayerBotMatsBoardFarm.end(); ++it)
			if (now - it->second.at < PLAYERBOT_MATS_BOARD_FARM_CLAIM_MS)
				++farmers;
		sys_log(0, "BOT_MATS_BOARD: census ch=%u rows=%u kinds=%u passes=%u scanned=%u sales=%u sold_units=%llu sold_yang=%llu "
				"refused=%u counter_boosts=%u counter_reason_bots=%u buy_picks=%u farm_taken=%u farmers=%d "
				"off(all/sale/list/buy/farm)=%d/%d/%d/%d/%d", (unsigned int)g_bChannel,
				(unsigned int)s_mapPlayerBotMatsBoardRows.size(), (unsigned int)ranked.size(), s.passes, s.scanned, s.sales,
				s.soldUnits, s.soldYang, s.saleRefused, s.boosts, (unsigned int)s_setPlayerBotMatsBoardCounterBots.size(), s.buyPicks, s.farmTaken, farmers,
				IsPlayerBotMatsBoardOff(MATS_BOARD_ALL) ? 1 : 0, IsPlayerBotMatsBoardOff(MATS_BOARD_SALE) ? 1 : 0,
				IsPlayerBotMatsBoardOff(MATS_BOARD_LIST) ? 1 : 0, IsPlayerBotMatsBoardOff(MATS_BOARD_BUY) ? 1 : 0,
				IsPlayerBotMatsBoardOff(MATS_BOARD_FARM) ? 1 : 0);
		for (size_t i = 0; i < ranked.size() && i < PLAYERBOT_MATS_BOARD_CENSUS_ITEMS; ++i)
		{
			const DWORD vnum = ranked[i].second;
			TPlayerBotMatsBoardEntry& e = s_mapPlayerBotMatsBoard[vnum];
			int itemFarmers = 0;
			for (std::map<DWORD, TPlayerBotMatsBoardFarmClaim>::const_iterator it = s_mapPlayerBotMatsBoardFarm.begin();
					it != s_mapPlayerBotMatsBoardFarm.end(); ++it)
				if (it->second.vnum == vnum && now - it->second.at < PLAYERBOT_MATS_BOARD_FARM_CLAIM_MS)
					++itemFarmers;
			sys_log(0, "BOT_MATS_BOARD: item ch=%u vnum=%u name=%s demand=%d demand_bots=%d supply=%d holders=%d "
					"supply_by(counter/can/none)=%d/%d/%d listed=%d unmet=%d premium=%d held(%s/%s/%s/%s/%s)=%d/%d/%d/%d/%d "
					"sold_units=%u sales=%u sold_yang=%llu counter_boosts=%u buy_picks=%u farm_places=%d farm_taken=%u farmers=%d",
					(unsigned int)g_bChannel, vnum, PlayerBotDkItemName(vnum), e.demand, e.demandBots, e.supply, e.holders,
					e.supplyBy[BOARD_HOLDER_COUNTER], e.supplyBy[BOARD_HOLDER_CAN], e.supplyBy[BOARD_HOLDER_NONE], e.listed,
					e.unmet, e.premium, PLAYERBOT_MATS_BOARD_HELD_NAMES[0], PLAYERBOT_MATS_BOARD_HELD_NAMES[1],
					PLAYERBOT_MATS_BOARD_HELD_NAMES[2], PLAYERBOT_MATS_BOARD_HELD_NAMES[3], PLAYERBOT_MATS_BOARD_HELD_NAMES[4],
					e.held[0], e.held[1], e.held[2], e.held[3], e.held[4], e.soldUnits, e.sales, e.soldYang, e.boosts,
					e.buyPicks, e.farmSlots, e.farmTaken, itemFarmers);
		}
		// the counts since the last census start again
		s_setPlayerBotMatsBoardCounterBots.clear();
		for (std::map<DWORD, TPlayerBotMatsBoardEntry>::iterator it = s_mapPlayerBotMatsBoard.begin();
				it != s_mapPlayerBotMatsBoard.end(); ++it)
		{
			it->second.soldUnits = it->second.sales = it->second.boosts = it->second.buyPicks = it->second.farmTaken = 0;
			it->second.soldYang = 0;
		}
	}

	// The core's tick (playerbot_dungeon_runs.h, beside the drop knowledge): the rolling scan, the pass, the census.
	void ManagePlayerBotMatsBoard(DWORD dwNow)
	{
		static DWORD s_dwNextScan = 0, s_dwNextPass = 0, s_dwNextCensus = 0, s_dwCursor = 0;
		if (s_dwNextCensus == 0)
		{
			s_dwNextCensus = dwNow + PLAYERBOT_MATS_BOARD_CENSUS_MS;
			s_dwNextPass = dwNow + 60000;	// a minute of rows before the first pass
		}
		if ((int)(dwNow - s_dwNextCensus) >= 0)
		{
			s_dwNextCensus = dwNow + PLAYERBOT_MATS_BOARD_CENSUS_MS;
			LogPlayerBotMatsBoardCensus();
		}
		if (IsPlayerBotMatsBoardOff(MATS_BOARD_ALL))
		{
			if (!s_mapPlayerBotMatsBoard.empty())
			{
				s_mapPlayerBotMatsBoard.clear();
				s_mapPlayerBotMatsBoardRows.clear();
				s_mapPlayerBotMatsBoardFarm.clear();
			}
			return;
		}
		const TPlayerBotMatsBoardCfg& c = GetPlayerBotMatsBoardCfg();
		if (s_dwNextScan == 0 || (int)(dwNow - s_dwNextScan) >= 0)
		{
			s_dwNextScan = dwNow + 1000;
			int done = 0, walked = 0;
			const int total = (int)s_mapPlayerBotAIStates.size();
			TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.upper_bound(s_dwCursor);
			while (done < c.scanBots && walked < total)
			{
				if (it == s_mapPlayerBotAIStates.end())
					it = s_mapPlayerBotAIStates.begin();
				if (it == s_mapPlayerBotAIStates.end())
					break;
				++walked;
				const DWORD pid = it->first;
				s_dwCursor = pid;
				++it;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
				if (!IsPlayerBotMatsBoardBot(ch))
				{
					s_mapPlayerBotMatsBoardRows.erase(pid);
					continue;
				}
				ScanPlayerBotMatsBoardBot(ch, dwNow);
				++done;
				++s_kPlayerBotMatsBoardStats.scanned;
			}
		}
		if ((int)(dwNow - s_dwNextPass) >= 0)
		{
			s_dwNextPass = dwNow + (DWORD)c.passMs;
			RunPlayerBotMatsBoardPass(dwNow);
		}
	}
}

#endif
