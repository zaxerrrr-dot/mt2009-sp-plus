#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_SHOP_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_SHOP_H__

// MT2009_PLUS_BOT_ELEMENT_SHOP_V1 - the element gate built from the ItemShop the way a player builds it (the owner, 8
// November 2026: "Wez to ogarnij, bo z ItemShopem wbicie 40% odpornosci na ogien to 10 minut gry prawdziwego gracza").
//
// The measure that asked for it (the test world, 2000 bots of 100 000 SM each after the 23:07 reset of 7 November):
// not one of 2438 bots of 30+ held 40% fire, lightning or wind, the averages under 3% - the progression's gates
// (MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1, playerbot_element_maps.h) refused them and the build-ahead goal only steered
// the ordinary bonus pass: three stones a visit, a visit every five minutes, eight pieces in its turn and a day cap of
// 60 Zaczarowanie.
//
// What the ItemShop V3 sells for it (itemshop3.shop of the test world, 8 November; the prices are the lines'):
//   Zaczarowanie Przedmiotu 71084   59 SM (1), 207 SM (4)   - the change: every line again, level 2-5 (10/40/35/15%)
//   Wzmocnienie Przedmiotu  71085   99 SM (1), 299 SM (4)   - an add: one line, level 1-3, 100/80/60/50% by the count
//   Kamien Ochrony Zywiolow 39120   65 SM, 7 days            - +10 to all six resistances (a unique slot)
//   Maly Zywiolak (53290-53295)    299 SM, a 30-day seal     - +10 its element's resistance (+5 its power) while out
// and nothing else with an element resistance: no costume or hairstyle line comes with a V3 costume (their lines are
// the Handlarka's 70063 / 70064 for yang - the costume pass's), no talisman, necklace or boots is sold (the element
// necklaces and boots are the equipment pass's: market / NPC, scored by GetPlayerBotElementMapApplyScore).
// The lines (world.item_attr, global mode): fire / lightning / wind on the armour, helmet and bracelet 2/4/6/10/15, on
// the talisman 5-25 (5 a level, BonusModeSetAttrValue), on the costume and hairstyle 2-15. With 4 lines a change gives
// the element at level 4+ (10, the talisman's 20) about one time in 10 on the armour (its set's weights 18/357), one
// in 12 on the helmet and the bracelet, one in 7 on the talisman (simulated, 3000 pieces of two lines: armour 9.6
// changes and 3.7 adds on average, median 7, 90% within 22; helmet 12.3; bracelet 11.6; talisman to 20: 7.1). So 42
// (the gate + the margin) is, at the shop's prices: the stone (10, 65 SM) + the pet (10, 299 SM) + two or three of
// armour / helmet / bracelet at 10+ (~52 SM a change in fours, ~75 an add) = ~26 changes and ~9 adds, ~2 400 SM on
// average, 3 700 for nine bots in ten; less with a talisman. A player does it in minutes; so does this pass.
//
// Who: a bot of the maps 1-120 (no Yohara hunt element, not a Yohara bonus member - their own pass, not a companion)
// whose element goal (GetPlayerBotElementMapGoal) is gated - the progression's build-ahead window of the next step
// (the prebuild) or a gated map it wants and is refused - fire, lightning or wind, its resistance under the target
// (the gate + PLAYERBOT_ESHOP_MARGIN; once reached, it is urgent again only under the gate itself - an expiry).
// What, every PLAYERBOT_ESHOP_STEP_MS while urgent (the plan made again each time - the rolls are random):
//   * the plan (BuildPlayerBotElementShopPlan): the resistance now per source and what each source still gives -
//     the stone (+10), the pet (+10), each piece's line to its level 4 ("floor": 10, the talisman 20) and then to its
//     top (15 / 25) - with its expected SM (the changes a hit takes by the set's weights, the adds that fill the piece
//     to four lines first, the cheapest line a piece); the cheapest SM a point first until the gap is closed. A piece
//     carrying the element the bot still hunts with (the prebuild's kept element) is not touched;
//   * the pet: bought (V3, "element_shop_pet") and called out (the seal's use; another pet out is called back);
//   * the stone: the stone pass's (playerbot_element_stones.h - bought in V3, never given, put on); this pass makes the
//     bot its member (IsPlayerBotElementShopStoneWanted) while the plan holds the stone;
//   * the piece: one at a time (the plan's cheapest, kept while it is in the plan), out of a fight's swing window -
//     off, filled to four lines with adds, changed until the element's line reaches the piece's level of the plan,
//     on again; up to PLAYERBOT_ESHOP_STONES_PER_SESSION stones a session, bought in batches as they run out
//     ("element_shop_change" / "element_shop_add"), never over the hold cap; a piece that has taken
//     PLAYERBOT_ESHOP_PIECE_GIVE_UP changes for the step is left. The ordinary pass leaves a piece alone that carries
//     the goal's (or the kept) element at its floor or is being worked (IsPlayerBotElementShopPinnedPiece) - its
//     rerolls for Max HP would throw the line away again.
//   Reached: the target is met - logged, the record kept (its SM, minutes); the travel pass's gate now lets the bot
//   pick the map (GetPlayerBotFrontierMapForLevel asks it live) and it goes at its next look.
// The coins (no SM added): every purchase stays in the bot's balance and in the daily pool, as urgent (tomorrow's
// seventh too, IsPlayerBotSmPoolUrgent) - and, for this need only, a step may spend up to PLAYERBOT_ESHOP_BUDGET of the
// balance whatever the day's seventh says (GetPlayerBotElementShopPoolRoom, event flag m2_bot_element_shop_budget N,
// 100-200000). The day caps of 71084 / 71085 (60 / 32) do not apply to these purchases (the hold caps do). The look's
// reserve keeps the plan's remaining SM back (GetPlayerBotElementShopReserve).
// Switches (event flags): m2_bot_element_shop_off 1 - the pass off (the pins, the stone membership, the pool's room,
// the reserve with it); m2_bot_element_shop_margin N (1-20, 99 none; default 2); m2_bot_element_shop_budget N.
// MT2009_PLUS_BOT_WIND_BUILD_V1 (the owner, 10 November 2026: the bots of 90+ build wind with the ItemShop; see
// playerbot_element_maps.h): the lightning goal of the wind window built without its pet, the wind step's budget
// PLAYERBOT_ESHOP_WIND_BUDGET (m2_bot_wind_shop_budget N) and PLAYERBOT_WIND_CENSUS (the bots of 90+ by band: wind spread,
// lightning without the pet, goals, pet, stone; the period's wind starts, reached, median minutes, SM, changes, adds,
// pets). MT2009_PLUS_BOT_WIND_SET_V1 (the owner rejected the rest): no lightning line is rolled away (the "fewest pieces"
// rule and the both option are gone); while a bot builds its wind set (playerbot_element_wind_set.h) this pass leaves
// its wind goal to that set - the worn lightning set is not touched - and the wind budget is the set's SM cap.
// The log: PLAYERBOT_EPROG_SHOP: start / plan / pet / work / piece_done / piece_give_up / reached / arrived / again /
// left / short, and a census every PLAYERBOT_ESHOP_CENSUS_MS (the bots in the window - urgent now, reached - their
// resistance at the start and now, the SM spent, the minutes from the start to the gate, the stones used, the
// equip-window waits, the purchases refused).
//
// An implementation fragment: included once from playerbot_manager.cpp after playerbot_ishop3_goals.h (the purchase)
// and playerbot_element_pet.h / playerbot_element_stones.h; the tick from the per-bot pass beside the element stone.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)

long BonusModeSetAttrValue(int iSet, WORD apply, BYTE level, long value); // playerbot_bonus_mode.cpp

namespace
{
	const DWORD PLAYERBOT_ESHOP_STEP_MS = 10 * 1000;
	const DWORD PLAYERBOT_ESHOP_IDLE_MS = 30 * 1000;
	const DWORD PLAYERBOT_ESHOP_WINDOW_RETRY_MS = 2000;
	const DWORD PLAYERBOT_ESHOP_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ESHOP_STONE_WAIT_MS = 3 * 60 * 1000;	// the stone pass's buy and wear, or the stone is left out
	const int PLAYERBOT_ESHOP_MARGIN = 2;
	const int PLAYERBOT_ESHOP_STONES_PER_SESSION = 12;
	const int PLAYERBOT_ESHOP_CHANGE_BATCH = 20;
	const int PLAYERBOT_ESHOP_ADD_BATCH = 8;
	const int PLAYERBOT_ESHOP_PIECE_GIVE_UP = 120;
	const long long PLAYERBOT_ESHOP_BUDGET = 6000;
	const int PLAYERBOT_ESHOP_SOURCE_GAIN = 10;	// the stone's and the pet's
	// the change's level odds (CItem::ChangeAttribute's tmpChangeProb, levels 1-5)
	const int PLAYERBOT_ESHOP_CHANGE_LEVEL_PCT[5] = { 0, 10, 40, 35, 15 };

	enum { PLAYERBOT_ESHOP_OPT_STONE = 0, PLAYERBOT_ESHOP_OPT_PET, PLAYERBOT_ESHOP_OPT_FLOOR, PLAYERBOT_ESHOP_OPT_TOP };

	// MT2009_PLUS_BOT_WIND_BUILD_V1: the wind step's budget (a step may spend this much of the balance) - event flag
	// m2_bot_wind_shop_budget N (100-200000); MT2009_PLUS_BOT_WIND_SET_V1: the wind set's SM cap too
	const long long PLAYERBOT_ESHOP_WIND_BUDGET = 15000;

	struct TPlayerBotEShopRecord
	{
		int iElement;		// the goal's element (PLAYERBOT_EM_*), -1 none
		int iGate;
		int iTarget;
		long lMap;			// the goal row's map
		DWORD dwStart;		// the urgency's start (0: not urgent)
		DWORD dwReached;	// the target reached (0: not yet)
		bool bArrivedLogged;
		int iResistStart;
		long long llSpent;	// SM spent on this step by this pass (and the stone when it went on)
		int iChanges, iAdds;
		bool bPetBought, bStoneCounted, bStoneWanted, bStoneOut, bPetOut;
		DWORD dwStoneWantedSince;
		int iFocusWear;		// the piece being worked (-1 none) and its item
		DWORD dwFocusItem;
		std::map<DWORD, int> pieceChanges;	// item id -> changes this step
		long long llPlanCost;	// the plan's SM still to go (the look's reserve)
		bool bPlanShort;
		DWORD dwNext;
		DWORD dwSeen;
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: a retreat's boost - the HP lines wanted after the element, the pieces given
		// an HP line by this pass (kept from the ordinary rerolls while the boost lasts)
		bool bHpWanted;
		int iBoosts;
		std::set<DWORD> hpPieces;
		TPlayerBotEShopRecord() : iElement(-1), iGate(0), iTarget(0), lMap(0), dwStart(0), dwReached(0), bArrivedLogged(false),
			iResistStart(0), llSpent(0), iChanges(0), iAdds(0), bPetBought(false), bStoneCounted(false), bStoneWanted(false),
			bStoneOut(false), bPetOut(false), dwStoneWantedSince(0), iFocusWear(-1), dwFocusItem(0), llPlanCost(0),
			bPlanShort(false), dwNext(0), dwSeen(0), bHpWanted(false), iBoosts(0) {}
	};
	std::map<DWORD, TPlayerBotEShopRecord> s_mapPlayerBotEShop;

	struct TPlayerBotEShopStats
	{
		unsigned int starts, reached, again, left, sessions, windowWaits, noStones, petsBought, petsOut, pieceDone, pieceGiveUp;
		unsigned int changes, adds;
		unsigned int boosts, hpPieceDone, hpDone;	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1
		// MT2009_PLUS_BOT_WIND_BUILD_V1: the wind step's work this period
		unsigned int windStarts, windReached, windChanges, windAdds, windPets, windSessions, windShort, holderSessions;
		long long windSm;
		std::vector<int> windMinutes;
		long long smReached;		// the SM of the bots reached in the period
		long long minutesReached;	// their minutes
		long resistStartReached;
		std::vector<int> minutes;	// each reached bot's minutes (the median)
		TPlayerBotEShopStats() : starts(0), reached(0), again(0), left(0), sessions(0), windowWaits(0), noStones(0), petsBought(0),
			petsOut(0), pieceDone(0), pieceGiveUp(0), changes(0), adds(0), boosts(0), hpPieceDone(0), hpDone(0), windStarts(0),
			windReached(0), windChanges(0), windAdds(0), windPets(0), windSessions(0), windShort(0), holderSessions(0), windSm(0), smReached(0), minutesReached(0), resistStartReached(0) {}
	};
	TPlayerBotEShopStats s_kPlayerBotEShop;

	bool IsPlayerBotElementShopOn()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			s_bOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_shop_off") == 0;
		}
		return s_bOn;
	}

	// m2_bot_element_shop_margin N: 1-20 that margin, 99 none (stop at the gate itself), else PLAYERBOT_ESHOP_MARGIN
	int GetPlayerBotElementShopMargin()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_shop_margin");
		return flag == 99 ? 0 : (flag > 0 && flag <= 20 ? flag : PLAYERBOT_ESHOP_MARGIN);
	}

	long long GetPlayerBotElementShopBudget()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_shop_budget");
		return flag >= 100 && flag <= 200000 ? (long long)flag : PLAYERBOT_ESHOP_BUDGET;
	}

	// MT2009_PLUS_BOT_WIND_BUILD_V1: the step's budget for the bot's goal now - the wind step's own (never under the
	// common one)
	long long GetPlayerBotElementShopBudgetFor(int element)
	{
		const long long common = GetPlayerBotElementShopBudget();
		if (element != PLAYERBOT_EM_WIND)
			return common;
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_wind_shop_budget");
		return std::max(common, flag >= 100 && flag <= 200000 ? (long long)flag : PLAYERBOT_ESHOP_WIND_BUDGET);
	}

	// The element goal this pass builds: a gated goal (the prebuild window or a gated map wanted) of fire, lightning or
	// wind, for a bot of the maps 1-120 that may buy in V3. false: none.
	bool GetPlayerBotElementShopView(LPCHARACTER ch, TPlayerBotElementMapView& v)
	{
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || !IsPlayerBotElementShopOn() ||
				!IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_ALL) || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				GetPlayerBotHuntElement(ch) != 0 || IsPlayerBotYoharaBonusMember(ch))
			return false;
		if (!GetPlayerBotElementMapGoal(ch, v) || v.iGate <= 0)
			return false;
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		// MT2009_PLUS_BOT_WIND_SET_V1: the wind of a bot building its wind set is that set's (in the bag) - the worn
		// lightning set is not rerolled, the wind pet is not called over the lightning one
		if (v.iElement == PLAYERBOT_EM_WIND && IsPlayerBotWindSetBuilding(ch))
			return false;
#endif
		return v.iElement == PLAYERBOT_EM_FIRE || v.iElement == PLAYERBOT_EM_ELEC || v.iElement == PLAYERBOT_EM_WIND;
	}

	// ---------------------------------------------------------------- the plan

	struct TPlayerBotEShopPiece
	{
		BYTE bWear;
		LPITEM item;
		int iSet;
		int iCur;		// the element's line value on it now
		int iFloor;		// its value at level 4 (or the set's top under 4)
		int iTop;		// at the set's top level
		int iLines;
		double dFloorP;	// a change's chance of the line at the floor or over, with four lines
		double dTopP;	// ... at the top
		double dAdds;	// the add stones expected to fill it to four lines
		int iSpent;		// changes this step
		TPlayerBotEShopPiece() : bWear(0), item(NULL), iSet(-1), iCur(0), iFloor(0), iTop(0), iLines(0), dFloorP(0), dTopP(0),
			dAdds(0), iSpent(0) {}
	};

	struct TPlayerBotEShopOption
	{
		int iKind;
		int iPiece;		// the piece's index (FLOOR / TOP)
		int iGain;
		double dCost;	// SM expected
	};

	struct TPlayerBotEShopPlan
	{
		int iResist, iTarget, iGap;
		int iGain;	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the chosen options' points (a short plan's reach)
		std::vector<TPlayerBotEShopPiece> pieces;
		std::vector<TPlayerBotEShopOption> chosen;	// cheapest a point first
		double dCost;
		bool bShort;	// every source taken and the target still not met
		bool bStone, bPet;
		int iStonePrice, iPetPrice;
		double dUnitChange, dUnitAdd;
		TPlayerBotEShopPlan() : iResist(0), iTarget(0), iGap(0), iGain(0), dCost(0), bShort(false), bStone(false), bPet(false), iStonePrice(0),
			iPetPrice(0), dUnitChange(0), dUnitAdd(0) {}
	};

	// The cheapest V3 line a piece of a vnum, in SM (0: not sold for SM to this bot).
	double GetPlayerBotElementShopUnitPrice(LPCHARACTER ch, DWORD vnum)
	{
		std::vector<const TPlayerBotItemShopEntry*> lines;
		SortPlayerBotIshop3Lines(ch, vnum, false, lines);
		if (lines.empty())
			return 0;
		return (double)lines[0]->dwPrice / (double)std::max<DWORD>(1, lines[0]->dwCount);
	}

	long GetPlayerBotElementShopLevelValue(int set, BYTE point, const TItemAttrTable& t, int level)
	{
		level = std::max(1, std::min(level, 5));
		return BonusModeSetAttrValue(set, point, (BYTE)level, t.lValues[level - 1]);
	}

	int GetPlayerBotElementShopLine(LPITEM item, BYTE point)
	{
		int value = 0;
		for (int i = 0; item && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point)
				value += (int)item->GetAttributeValue(i);
		return value;
	}

	// A worn piece the element's line can be rolled on, and what it may still give.
	bool ReadPlayerBotElementShopPiece(LPCHARACTER ch, BYTE wear, BYTE point, int keep, TPlayerBotEShopPiece& out,
			const TPlayerBotEShopRecord& rec)
	{
		LPITEM item = ch->GetWear(wear);
		if (!item || !CanPlayerBotTakeBonusStone(item) || IsPlayerBotSidekickLockedItem(ch, item))
			return false;
		const int set = item->GetAttributeSetIndex();
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM || !IsPlayerBotApplyOnAttrSet(point, set) ||
				IsPlayerBotElementProgressKeptPiece(ch, item, keep))
			return false;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (it == g_map_itemAttr.end())
			return false;
		const int maxLevel = std::max(1, std::min((int)it->second.bMaxLevelBySet[set], 5));
		const int floorLevel = std::min(4, maxLevel);
		long total = 0;
		int kinds = 0;
		for (TItemAttrMap::const_iterator a = g_map_itemAttr.begin(); a != g_map_itemAttr.end(); ++a)
			if (a->second.bMaxLevelBySet[set] != 0 && a->second.dwProb != 0)
			{
				total += (long)a->second.dwProb;
				++kinds;
			}
		if (total <= 0 || it->second.dwProb == 0)
			return false;
		out.bWear = wear;
		out.item = item;
		out.iSet = set;
		out.iCur = GetPlayerBotElementShopLine(item, point);
		out.iFloor = (int)GetPlayerBotElementShopLevelValue(set, point, it->second, floorLevel);
		out.iTop = (int)GetPlayerBotElementShopLevelValue(set, point, it->second, maxLevel);
		out.iLines = item->GetAttributeCount();
		// four lines after the adds (fewer when the set has no more to give)
		const bool canAdd = CanPlayerBotItemRollNewLine(item);
		const int lines = std::max(out.iLines, canAdd ? PLAYERBOT_BONUS_MAX_LINES : out.iLines);
		out.dAdds = 0;
		for (int c = out.iLines; canAdd && c < PLAYERBOT_BONUS_MAX_LINES; ++c)
			out.dAdds += 100.0 / std::max(1, aiItemAttributeAddPercent[c]);
		// the line among the piece's lines: each line drawn by weight from the kinds not on it yet (PutAttributeWithLevel),
		// the others' weight taken as the set's average
		const double w = (double)it->second.dwProb;
		const double avg = (double)total / (double)std::max(1, kinds);
		double miss = 1.0;
		for (int i = 0; i < std::max(1, lines); ++i)
		{
			const double left = std::max(w, (double)total - i * avg);
			miss *= std::max(0.0, 1.0 - w / left);
		}
		const double present = std::max(0.01, 1.0 - miss);
		int atFloor = 0, atTop = 0;
		for (int l = 1; l <= 5; ++l)
		{
			const int capped = std::min(l, maxLevel);
			if (capped >= floorLevel)
				atFloor += PLAYERBOT_ESHOP_CHANGE_LEVEL_PCT[l - 1];
			if (capped >= maxLevel)
				atTop += PLAYERBOT_ESHOP_CHANGE_LEVEL_PCT[l - 1];
		}
		out.dFloorP = present * std::max(1, atFloor) / 100.0;
		out.dTopP = present * std::max(1, atTop) / 100.0;
		std::map<DWORD, int>::const_iterator s = rec.pieceChanges.find(item->GetID());
		out.iSpent = s != rec.pieceChanges.end() ? s->second : 0;
		return true;
	}

	bool IsPlayerBotElementShopPetOut(LPCHARACTER ch, int e)
	{
#if defined(__PET_SYSTEM__)
		LPITEM out = FindPlayerBotSummonedPetSeal(ch);
		return out && e >= 0 && e < PLAYERBOT_YOHARA_ELEMENTS && out->GetVnum() == PLAYERBOT_ELEMPET_VNUMS[e];
#else
		(void)ch; (void)e;
		return false;
#endif
	}

	// The plan: every source's gain and expected SM, the cheapest a point first until the gap is closed.
	void BuildPlayerBotElementShopPlan(LPCHARACTER ch, const TPlayerBotElementMapView& v, const TPlayerBotEShopRecord& rec,
			int target, TPlayerBotEShopPlan& plan)
	{
		plan = TPlayerBotEShopPlan();
		plan.iResist = v.iResist;
		plan.iTarget = target;
		plan.iGap = std::max(0, target - v.iResist);
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
		plan.dUnitChange = GetPlayerBotElementShopUnitPrice(ch, PLAYERBOT_BONUS_CHANGE_VNUM);
		plan.dUnitAdd = GetPlayerBotElementShopUnitPrice(ch, PLAYERBOT_BONUS_ADD_VNUM);
		const bool changes = plan.dUnitChange > 0 || ch->CountSpecifyItem(PLAYERBOT_BONUS_CHANGE_VNUM) > 0;
		std::vector<TPlayerBotEShopOption> options;
		// the stone: none of the two element stones worn (one at a time), the stone pass not given up on it
		WORD cell = 0;
		const bool stoneHeld = FindPlayerBotBagElementStone(ch, cell) != NULL;
		plan.iStonePrice = (int)GetPlayerBotItemShopCheapest(ch, PLAYERBOT_ELEMSTONE_PROTECT_VNUM, false);
		const bool stoneLate = rec.dwStoneWantedSince != 0 && get_dword_time() - rec.dwStoneWantedSince > PLAYERBOT_ESHOP_STONE_WAIT_MS;
		if (!FindPlayerBotWornElementStone(ch) && (stoneHeld || plan.iStonePrice > 0) && !stoneLate)
		{
			const TPlayerBotEShopOption o = { PLAYERBOT_ESHOP_OPT_STONE, -1, PLAYERBOT_ESHOP_SOURCE_GAIN,
					stoneHeld ? 0.0 : (double)plan.iStonePrice };
			options.push_back(o);
		}
		// the pet: its element's seal out (held: no cost)
		plan.iPetPrice = (int)GetPlayerBotItemShopCheapest(ch, PLAYERBOT_ELEMPET_VNUMS[v.iElement], false);
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
		// MT2009_PLUS_BOT_WIND_BUILD_V1: not for a bot of the wind window on lightning - its pet is wind's next
		if (!IsPlayerBotWindBuildHolder(ch, v.iElement) && !IsPlayerBotElementShopPetOut(ch, v.iElement))
		{
			const bool petHeld = FindPlayerBotBagElementPet(ch, PLAYERBOT_ELEMPET_VNUMS[v.iElement]) != NULL;
			// one purchase a step: a seal bought and not found (another window) is not bought again
			if (petHeld || (plan.iPetPrice > 0 && !rec.bPetBought))
			{
				const TPlayerBotEShopOption o = { PLAYERBOT_ESHOP_OPT_PET, -1, PLAYERBOT_ESHOP_SOURCE_GAIN,
						petHeld ? 0.0 : (double)plan.iPetPrice };
				options.push_back(o);
			}
		}
#endif
		// the pieces: the armour, the helmet, the bracelet and the talisman
		static const BYTE s_wears[] = { WEAR_BODY, WEAR_HEAD, WEAR_WRIST,
#ifdef ENABLE_PENDANT_SYSTEM
			WEAR_PENDANT,
#endif
		};
		for (size_t i = 0; changes && i < sizeof(s_wears) / sizeof(s_wears[0]); ++i)
		{
			TPlayerBotEShopPiece p;
			if (!ReadPlayerBotElementShopPiece(ch, s_wears[i], point, v.iKeep, p, rec) || p.iSpent >= PLAYERBOT_ESHOP_PIECE_GIVE_UP)
				continue;
			const int idx = (int)plan.pieces.size();
			plan.pieces.push_back(p);
			const double unit = std::max(1.0, plan.dUnitChange);
			const double adds = p.dAdds * std::max(1.0, plan.dUnitAdd);
			if (p.iCur < p.iFloor)
			{
				const TPlayerBotEShopOption o = { PLAYERBOT_ESHOP_OPT_FLOOR, idx, p.iFloor - p.iCur, adds + unit / p.dFloorP };
				options.push_back(o);
			}
			if (p.iTop > std::max(p.iCur, p.iFloor))
			{
				const TPlayerBotEShopOption o = { PLAYERBOT_ESHOP_OPT_TOP, idx, p.iTop - std::max(p.iCur, p.iFloor),
						(p.iCur < p.iFloor ? 0.0 : adds) + unit / p.dTopP };
				options.push_back(o);
			}
		}
		// the cheapest a point first (a piece's top only after its floor)
		for (size_t i = 1; i < options.size(); ++i)
			for (size_t j = i; j > 0 && options[j].dCost * options[j - 1].iGain < options[j - 1].dCost * options[j].iGain; --j)
				std::swap(options[j], options[j - 1]);
		int gap = plan.iGap;
		std::vector<bool> taken(options.size(), false);
		for (int pass = 0; pass < 2 && gap > 0; ++pass)
			for (size_t i = 0; i < options.size() && gap > 0; ++i)
			{
				if (taken[i])
					continue;
				const TPlayerBotEShopOption& o = options[i];
				if (o.iKind == PLAYERBOT_ESHOP_OPT_TOP && plan.pieces[o.iPiece].iCur < plan.pieces[o.iPiece].iFloor)
				{
					bool floorTaken = false;
					for (size_t k = 0; k < options.size(); ++k)
						if (taken[k] && options[k].iKind == PLAYERBOT_ESHOP_OPT_FLOOR && options[k].iPiece == o.iPiece)
							floorTaken = true;
					if (!floorTaken)
						continue;	// the second pass takes it once its floor is in
				}
				taken[i] = true;
				gap -= o.iGain;
				plan.iGain += o.iGain;
				plan.dCost += o.dCost;
				plan.chosen.push_back(o);
				if (o.iKind == PLAYERBOT_ESHOP_OPT_STONE)
					plan.bStone = true;
				else if (o.iKind == PLAYERBOT_ESHOP_OPT_PET)
					plan.bPet = true;
			}
		plan.bShort = gap > 0;
	}

	// ---------------------------------------------------------------- the actions

	// One V3 batch for this need (the day cap off for it, the hold cap kept). The SM paid.
	long long BuyPlayerBotElementShopBatch(LPCHARACTER ch, TPlayerBotAIState& state, DWORD vnum, int pieces, const char* reason,
			DWORD dwNow, int* purchases)
	{
		if (pieces <= 0)
			return 0;
		const int before = state.iDragonCoins;
		TPlayerBotIshop3Goal g = { vnum, false, pieces, reason };
		s_bPlayerBotIshop3NoDayCap = true;
		const int got = BuyPlayerBotIshop3Pieces(ch, state, g, dwNow, purchases);
		s_bPlayerBotIshop3NoDayCap = false;
		if (got <= 0)
		{
			++s_kPlayerBotEShop.noStones;
			PlayerBotLogThrottled("eshop_no_buy", dwNow,
					"PLAYERBOT_EPROG_SHOP: no_buy pid=%u name=%s vnum=%u wanted=%d reason=%s coins=%d", ch->GetPlayerID(),
					ch->GetName(), vnum, pieces, reason, state.iDragonCoins);
		}
		return std::max(0LL, (long long)before - (long long)state.iDragonCoins);
	}

	// The element's pet out: called from the bag, bought first when there is none.
	void ManagePlayerBotElementShopPet(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec, int e,
			DWORD dwNow, int* purchases)
	{
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
		const DWORD vnum = PLAYERBOT_ELEMPET_VNUMS[e];
		LPITEM seal = FindPlayerBotBagElementPet(ch, vnum);
		if (!seal)
		{
			if (rec.bPetBought)
				return;
			const long long paid = BuyPlayerBotElementShopBatch(ch, state, vnum, 1, "element_shop_pet", dwNow, purchases);
			rec.llSpent += paid;
			if (paid > 0)
			{
				rec.bPetBought = true;
				++s_kPlayerBotEShop.petsBought;
			}
			seal = FindPlayerBotBagElementPet(ch, vnum);
			if (!seal)
				return;
		}
		if (!ch->GetPetSystem())
			return;
		LPITEM out = FindPlayerBotSummonedPetSeal(ch);
		const DWORD oldVnum = out ? out->GetVnum() : 0;
		if (out)
			ch->SummonPetFromItem(out);	// the seal's use is a toggle: the other pet back first
		if (ch->SummonPetFromItem(seal) && FindPlayerBotSummonedPetSeal(ch) == seal)
		{
			++s_kPlayerBotEShop.petsOut;
			sys_log(0, "PLAYERBOT_EPROG_SHOP: pet pid=%u name=%s lv=%d vnum=%u element=%s replaced=%u bought=%d resist=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), vnum, GetPlayerBotElementMapElementName(e), oldVnum,
					rec.bPetBought ? 1 : 0, GetPlayerBotElementMapResist(ch, e));
		}
		else
			PlayerBotLogThrottled("eshop_pet_call", dwNow, "PLAYERBOT_EPROG_SHOP: pet_not_out pid=%u name=%s vnum=%u old=%u",
					ch->GetPlayerID(), ch->GetName(), vnum, oldVnum);
#else
		(void)ch; (void)state; (void)rec; (void)e; (void)dwNow; (void)purchases;
#endif
	}

	// The stones in the bag, the storages' brought back when the bag has none (the ekwipunek pass's working stock).
	int FindPlayerBotElementShopStone(LPCHARACTER ch, DWORD vnum, LPITEM target)
	{
		int cell = FindPlayerBotBonusStoneCellLike(ch, vnum, target);
		if (cell < 0 && ch->CountSpecifyItem(vnum) > 0 && PlayerBotEkwFetchVnum(ch, vnum))
			cell = FindPlayerBotBonusStoneCellLike(ch, vnum, target);
		return cell;
	}

	// The piece's work of a session: off, filled to four lines, changed until its element line reaches the level, on.
	// The stones spent.
	int WorkPlayerBotElementShopPiece(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec,
			const TPlayerBotEShopPiece& p, BYTE point, int want, DWORD dwNow, int* purchases)
	{
		LPITEM item = p.item;
		// the stock first, so the piece comes off once
		const int before = GetPlayerBotElementShopLine(item, point);
		if (before >= want)
			return 0;
		const bool fill = p.iLines < PLAYERBOT_BONUS_MAX_LINES && CanPlayerBotItemRollNewLine(item);
		// (BuyPlayerBotIshop3Pieces clamps a batch to the hold cap; the day cap is off for this need)
		if (fill && (int)ch->CountSpecifyItem(PLAYERBOT_BONUS_ADD_VNUM) < PLAYERBOT_BONUS_MAX_LINES - p.iLines + 1)
			rec.llSpent += BuyPlayerBotElementShopBatch(ch, state, PLAYERBOT_BONUS_ADD_VNUM, PLAYERBOT_ESHOP_ADD_BATCH,
					"element_shop_add", dwNow, purchases);
		if ((int)ch->CountSpecifyItem(PLAYERBOT_BONUS_CHANGE_VNUM) < PLAYERBOT_ESHOP_STONES_PER_SESSION)
			rec.llSpent += BuyPlayerBotElementShopBatch(ch, state, PLAYERBOT_BONUS_CHANGE_VNUM, PLAYERBOT_ESHOP_CHANGE_BATCH,
					"element_shop_change", dwNow, purchases);
		const int linesBefore = item->GetAttributeCount();
		if (FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_CHANGE_VNUM, item) < 0 &&
				(!fill || FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_ADD_VNUM, item) < 0))
		{
			++s_kPlayerBotEShop.noStones;
			return 0;
		}
		if (!ch->UnequipItem(item))
			return 0;
		int used = 0, changes = 0, adds = 0;
		while (used < PLAYERBOT_ESHOP_STONES_PER_SESSION && GetPlayerBotElementShopLine(item, point) < want)
		{
			const int count = item->GetAttributeCount();
			int cell = -1;
			if (count < PLAYERBOT_BONUS_MAX_LINES && CanPlayerBotItemRollNewLine(item) &&
					(cell = FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_ADD_VNUM, item)) >= 0)
			{
				// the engine's odds for a line by the count (the stone is spent either way, as at the counter)
				if (number(1, 100) <= aiItemAttributeAddPercent[count])
					item->AddAttribute();
				ConsumePlayerBotBonusStoneAt(ch, cell);
				LogManager::instance().ItemLog(ch, item, "PLAYERBOT_ESHOP_ADD", item->GetName());
				++adds;
			}
			else if (count > 0 && (cell = FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_CHANGE_VNUM, item)) >= 0)
			{
				item->ChangeAttribute();
				ConsumePlayerBotBonusStoneAt(ch, cell);
				LogManager::instance().ItemLog(ch, item, "PLAYERBOT_ESHOP_CHANGE", item->GetName());
				++changes;
			}
			else
				break;
			++used;
		}
		if (!PlayerBotEquipItem(ch, item))
			sys_err("PLAYERBOT_EPROG_SHOP: could not re-equip pid=%u name=%s vnum=%u slot=%u stones=%d", ch->GetPlayerID(),
					ch->GetName(), item->GetVnum(), (unsigned int)p.bWear, used);
		rec.iChanges += changes;
		rec.iAdds += adds;
		rec.pieceChanges[item->GetID()] += changes;
		s_kPlayerBotEShop.changes += (unsigned int)changes;
		s_kPlayerBotEShop.adds += (unsigned int)adds;
		const int after = GetPlayerBotElementShopLine(item, point);
		sys_log(0, "PLAYERBOT_EPROG_SHOP: work pid=%u name=%s lv=%d slot=%u vnum=%u lines=%d->%d line=%d->%d want=%d adds=%d "
				"changes=%d piece_changes=%d coins=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)p.bWear, item->GetVnum(), linesBefore,
				item->GetAttributeCount(), before, after, want, adds, changes, rec.pieceChanges[item->GetID()], state.iDragonCoins);
		if (after >= want)
		{
			++s_kPlayerBotEShop.pieceDone;
			sys_log(0, "PLAYERBOT_EPROG_SHOP: piece_done pid=%u name=%s slot=%u vnum=%u line=%d piece_changes=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)p.bWear, item->GetVnum(), after, rec.pieceChanges[item->GetID()]);
		}
		else if (rec.pieceChanges[item->GetID()] >= PLAYERBOT_ESHOP_PIECE_GIVE_UP)
		{
			++s_kPlayerBotEShop.pieceGiveUp;
			sys_log(0, "PLAYERBOT_EPROG_SHOP: piece_give_up pid=%u name=%s slot=%u vnum=%u line=%d piece_changes=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)p.bWear, item->GetVnum(), after, rec.pieceChanges[item->GetID()]);
		}
		return used;
	}

	// ---------------------------------------------------------------- the hooks of the other passes

	TPlayerBotEShopRecord* FindPlayerBotElementShopRecord(LPCHARACTER ch)
	{
		if (!ch || s_mapPlayerBotEShop.empty())
			return NULL;
		std::map<DWORD, TPlayerBotEShopRecord>::iterator it = s_mapPlayerBotEShop.find(ch->GetPlayerID());
		return it != s_mapPlayerBotEShop.end() ? &it->second : NULL;
	}

	bool IsPlayerBotElementShopActive(const TPlayerBotEShopRecord* rec)
	{
		return rec && rec->dwStart != 0 && rec->dwReached == 0;
	}

	// playerbot_element_stones.h (IsPlayerBotElementMapStoneWanted): the plan holds the stone.
	bool IsPlayerBotElementShopStoneWanted(LPCHARACTER ch)
	{
		const TPlayerBotEShopRecord* rec = FindPlayerBotElementShopRecord(ch);
		return IsPlayerBotElementShopOn() && IsPlayerBotElementShopActive(rec) && rec->bStoneWanted;
	}

	// playerbot_bonus.h (PlayerBotWantsBonusChange): the ordinary pass changes no worn piece that carries the goal's
	// element at its floor (or the kept element), nor the piece this pass works on.
	bool IsPlayerBotElementShopPinnedPiece(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotElementShopOn())
			return false;
		const TPlayerBotEShopRecord* rec = FindPlayerBotElementShopRecord(ch);
		if (rec && rec->dwFocusItem == item->GetID() && (IsPlayerBotElementShopActive(rec) || rec->bHpWanted))
			return true;
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: a piece this pass gave its HP line while the boost lasts
		if (rec && !rec->hpPieces.empty() && rec->hpPieces.count(item->GetID()) &&
				GetPlayerBotElementProgressBoostTarget(ch, rec->iElement) > 0)
			return true;
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementShopView(ch, v))
			return false;
		if (IsPlayerBotElementProgressKeptPiece(ch, item, v.iKeep))
			return true;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
		const int set = item->GetAttributeSetIndex();
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM || it == g_map_itemAttr.end() || !IsPlayerBotApplyOnAttrSet(point, set))
			return false;
		const int floorLevel = std::min(4, std::max(1, (int)it->second.bMaxLevelBySet[set]));
		return GetPlayerBotElementShopLine(item, point) >= GetPlayerBotElementShopLevelValue(set, point, it->second, floorLevel);
	}

	// playerbot_itemshop.h (GetPlayerBotSmPoolRoom): this need's room in SM - the step's budget less what it spent; -1
	// for any other reason or a bot not on it.
	long long GetPlayerBotElementShopPoolRoom(LPCHARACTER ch, const char* reason)
	{
		if (!reason || strncmp(reason, "element_shop", 12) != 0 || !IsPlayerBotElementShopOn())
			return -1;
		const TPlayerBotEShopRecord* rec = FindPlayerBotElementShopRecord(ch);
		if (!IsPlayerBotElementShopActive(rec))
			return -1;
		return std::max(0LL, GetPlayerBotElementShopBudgetFor(rec->iElement) - rec->llSpent);
	}

	// playerbot_ishop3_goals.h (GetPlayerBotIshop3GoalReserve): the plan's SM still to go, kept back from the look.
	long long GetPlayerBotElementShopReserve(LPCHARACTER ch)
	{
		const TPlayerBotEShopRecord* rec = FindPlayerBotElementShopRecord(ch);
		if (!IsPlayerBotElementShopOn() || !IsPlayerBotElementShopActive(rec))
			return 0;
		return std::min(rec->llPlanCost, std::max(0LL, GetPlayerBotElementShopBudgetFor(rec->iElement) - rec->llSpent));
	}

	// ---------------------------------------------------------------- MT2009_PLUS_BOT_EPROG_BUY_MORE_V1

	// The HP after a retreat's boost: the shield, the necklace, the boots and the earrings (no element line on them in
	// global mode) each to a Max HP line at the set's level-4 value, one piece a session, within the step's budget.
	// false: nothing left to do (every piece has it, cannot take it, or was given up).
	bool WorkPlayerBotElementShopHp(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec,
			const TPlayerBotElementMapView& v, DWORD dwNow, int* purchases)
	{
		static const BYTE s_wears[] = { WEAR_SHIELD, WEAR_NECK, WEAR_FOOTS, WEAR_EAR };
		const BYTE point = (BYTE)APPLY_MAX_HP;
		for (size_t i = 0; i < sizeof(s_wears) / sizeof(s_wears[0]); ++i)
		{
			TPlayerBotEShopPiece p;
			if (!ReadPlayerBotElementShopPiece(ch, s_wears[i], point, v.iKeep, p, rec) || p.iSpent >= PLAYERBOT_ESHOP_PIECE_GIVE_UP ||
					HasPlayerBotElementProgressKeptLine(p.item, v.iElement))
				continue;
			if (p.iCur >= p.iFloor)
			{
				rec.hpPieces.insert(p.item->GetID());
				continue;
			}
			if (std::max(0LL, GetPlayerBotElementShopBudgetFor(rec.iElement) - rec.llSpent) <= 0)
				return false;
			rec.dwFocusItem = p.item->GetID();
			rec.iFocusWear = p.bWear;
			if (IsPlayerBotEquipWindowShut(ch, state))
			{
				++s_kPlayerBotEShop.windowWaits;
				rec.dwNext = dwNow + PLAYERBOT_ESHOP_WINDOW_RETRY_MS;
				return true;
			}
			WorkPlayerBotElementShopPiece(ch, state, rec, p, point, p.iFloor, dwNow, purchases);
			if (GetPlayerBotElementShopLine(p.item, point) >= p.iFloor)
			{
				rec.hpPieces.insert(p.item->GetID());
				++s_kPlayerBotEShop.hpPieceDone;
				sys_log(0, "PLAYERBOT_EPROG_SHOP: hp_piece pid=%u name=%s lv=%d slot=%u vnum=%u hp_line=%d max_hp=%d spent=%lld",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)p.bWear, p.item->GetVnum(),
						GetPlayerBotElementShopLine(p.item, point), (int)ch->GetMaxHP(), rec.llSpent);
			}
			return true;
		}
		rec.dwFocusItem = 0;
		rec.iFocusWear = -1;
		return false;
	}

	// The worn costume / hairstyle's room for the element's line (to its set's top) - the Handlarka's 70063 / 70064 for
	// yang (the costume pass, which reads the raised want).
	int GetPlayerBotElementShopCostumeRoom(LPCHARACTER ch, int e)
	{
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[e];
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (it == g_map_itemAttr.end())
			return 0;
		static const BYTE s_wears[] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR };
		int room = 0;
		for (size_t i = 0; i < sizeof(s_wears) / sizeof(s_wears[0]); ++i)
		{
			LPITEM item = ch->GetWear(s_wears[i]);
			if (!item || item->GetType() != ITEM_COSTUME)
				continue;
			const int set = item->GetAttributeSetIndex();
			if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM || !IsPlayerBotApplyOnAttrSet(point, set))
				continue;
			const int top = std::max(1, std::min((int)it->second.bMaxLevelBySet[set], 5));
			room += std::max(0, (int)it->second.lValues[top - 1] - GetPlayerBotElementShopLine(item, point));
		}
		return room;
	}

	bool TryPlayerBotElementShopBoost(LPCHARACTER ch, int element, int* pTarget, const char** how, const char** why,
			long long* pCost)
	{
		*how = "-";
		*why = "no_view";
		*pCost = 0;
		if (!ch || !pTarget)
			return false;
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementShopView(ch, v) || v.iElement != element)
			return false;
		TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (st == s_mapPlayerBotAIStates.end())
			return false;
		TPlayerBotAIState& state = st->second;
		TPlayerBotEShopRecord& rec = s_mapPlayerBotEShop[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		int target = *pTarget;
		// SM: the plan to the target (or what it reaches, +5 at least) within a fresh step's budget and the balance
		bool sm = false;
		int smReach = 0;
		long long cost = 0;
		const char* smWhy = "no_shop";
		if (GetPlayerBotItemShopSource() == 2 && IsPlayerBotItemShopEnabled())
		{
			if (!state.bDragonBalanceKnown)
				RefreshPlayerBotDragonBalance(ch, state, now);
			TPlayerBotEShopRecord fresh = rec;
			fresh.pieceChanges.clear();
			fresh.dwStoneWantedSince = 0;
			fresh.bPetBought = false;
			TPlayerBotEShopPlan plan;
			BuildPlayerBotElementShopPlan(ch, v, fresh, target, plan);
			smReach = plan.bShort ? v.iResist + plan.iGain : target;
			cost = (long long)plan.dCost;
			if (smReach < v.iResist + 5)
				smWhy = "plan_short";
			else if (cost > GetPlayerBotElementShopBudgetFor(element) || cost > (long long)state.iDragonCoins)
				smWhy = "no_sm";
			else
				sm = true;
		}
		// yang: the costume and hairstyle's line for the Handlarka's reagents (the costume pass's own gold rule)
		const int costumeRoom = ch->GetGold() >= PLAYERBOT_COSTUME_BONUS_START_GOLD ? GetPlayerBotElementShopCostumeRoom(ch, element) : 0;
		const bool yang = costumeRoom >= 5;
		if (!sm && !yang)
		{
			*why = smWhy;
			return false;
		}
		if (sm && !yang)
			target = smReach;
		else if (!sm)
			target = std::min(target, v.iResist + costumeRoom);
		else
			target = std::min(target, smReach + costumeRoom);
		*how = sm && yang ? "sm+yang" : sm ? "sm" : "yang";
		*why = "-";
		*pTarget = target;
		*pCost = cost;
		// the record: a new step at the raised target, urgent at once, the HP after it
		rec.iElement = v.iElement;
		rec.iGate = v.iGate;
		rec.dwReached = 0;
		rec.dwStart = 0;
		rec.bArrivedLogged = false;
		rec.llSpent = 0;
		rec.iChanges = 0;
		rec.iAdds = 0;
		rec.pieceChanges.clear();
		rec.bStoneWanted = false;
		rec.dwStoneWantedSince = 0;
		rec.bStoneCounted = false;
		rec.bHpWanted = true;
		++rec.iBoosts;
		rec.dwNext = 0;
		rec.dwSeen = now ? now : 1;
		++s_kPlayerBotEShop.boosts;
		return true;
	}

	// ---------------------------------------------------------------- the census

	void TickPlayerBotElementShopCensus(DWORD now)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = now + PLAYERBOT_ESHOP_CENSUS_MS;
			return;
		}
		if ((int)(now - s_dwAt) < 0)
			return;
		s_dwAt = now + PLAYERBOT_ESHOP_CENSUS_MS;
		static const char* const s_aszElements[3] = { "fire", "lightning", "wind" };
		int active[3] = { 0, 0, 0 }, reached[3] = { 0, 0, 0 }, shortPlan = 0, petOut = 0, stoneOut = 0;
		long startSum[3] = { 0, 0, 0 }, nowSum[3] = { 0, 0, 0 };
		long long spentActive = 0, planLeft = 0;
		for (std::map<DWORD, TPlayerBotEShopRecord>::iterator it = s_mapPlayerBotEShop.begin(); it != s_mapPlayerBotEShop.end();)
		{
			if (now - it->second.dwSeen > 60U * 60U * 1000U)
			{
				s_mapPlayerBotEShop.erase(it++);
				continue;
			}
			const TPlayerBotEShopRecord& r = it->second;
			const int k = r.iElement == PLAYERBOT_EM_FIRE ? 0 : r.iElement == PLAYERBOT_EM_ELEC ? 1 : r.iElement == PLAYERBOT_EM_WIND ? 2 : -1;
			LPCHARACTER ch = k >= 0 && r.dwStart != 0 ? CHARACTER_MANAGER::instance().FindByPID(it->first) : NULL;
			if (ch && ch->IsItemLoaded())
			{
				const int resist = GetPlayerBotElementMapResist(ch, r.iElement);
				(r.dwReached ? reached : active)[k] += 1;
				startSum[k] += r.iResistStart;
				nowSum[k] += resist;
				if (!r.dwReached)
				{
					spentActive += r.llSpent;
					planLeft += r.llPlanCost;
					shortPlan += r.bPlanShort ? 1 : 0;
				}
				petOut += IsPlayerBotElementShopPetOut(ch, r.iElement) ? 1 : 0;
				stoneOut += FindPlayerBotWornElementStone(ch) ? 1 : 0;
			}
			++it;
		}
		std::string line;
		for (int k = 0; k < 3; ++k)
		{
			const int n = active[k] + reached[k];
			if (!n)
				continue;
			char buf[160];
			snprintf(buf, sizeof(buf), " %s=[window=%d urgent=%d reached=%d resist_start_avg=%ld resist_now_avg=%ld]", s_aszElements[k],
					n, active[k], reached[k], startSum[k] / n, nowSum[k] / n);
			line += buf;
		}
		std::vector<int>& m = s_kPlayerBotEShop.minutes;
		std::sort(m.begin(), m.end());
		const int median = m.empty() ? -1 : m[m.size() / 2];
		const unsigned int urgentAll = (unsigned int)(active[0] + active[1] + active[2]);
		sys_log(0, "PLAYERBOT_EPROG_SHOP: census%s pet_out=%d stone_out=%d urgent_sm_spent_avg=%lld urgent_plan_left_avg=%lld "
				"plan_short=%d period=[starts=%u reached=%u again=%u left=%u sm_avg=%lld min_avg=%lld min_median=%d "
				"resist_start_avg=%ld sessions=%u window_waits=%u no_stones=%u changes=%u adds=%u pets_bought=%u pets_out=%u "
				"pieces_done=%u pieces_given_up=%u boosts=%u hp_pieces=%u hp_done=%u] budget=%lld margin=%d",
				line.empty() ? " none" : line.c_str(), petOut, stoneOut, urgentAll ? spentActive / urgentAll : 0LL,
				urgentAll ? planLeft / urgentAll : 0LL, shortPlan, s_kPlayerBotEShop.starts, s_kPlayerBotEShop.reached,
				s_kPlayerBotEShop.again, s_kPlayerBotEShop.left,
				s_kPlayerBotEShop.reached ? s_kPlayerBotEShop.smReached / s_kPlayerBotEShop.reached : 0LL,
				s_kPlayerBotEShop.reached ? s_kPlayerBotEShop.minutesReached / s_kPlayerBotEShop.reached : 0LL, median,
				s_kPlayerBotEShop.reached ? s_kPlayerBotEShop.resistStartReached / (long)s_kPlayerBotEShop.reached : 0L,
				s_kPlayerBotEShop.sessions, s_kPlayerBotEShop.windowWaits, s_kPlayerBotEShop.noStones, s_kPlayerBotEShop.changes,
				s_kPlayerBotEShop.adds, s_kPlayerBotEShop.petsBought, s_kPlayerBotEShop.petsOut, s_kPlayerBotEShop.pieceDone,
				s_kPlayerBotEShop.pieceGiveUp, s_kPlayerBotEShop.boosts, s_kPlayerBotEShop.hpPieceDone, s_kPlayerBotEShop.hpDone,
				GetPlayerBotElementShopBudget(), GetPlayerBotElementShopMargin());
		// MT2009_PLUS_BOT_WIND_BUILD_V1: the wind of the bots of 90+ (no Yohara hunt element) by band - its spread, the
		// lightning held without the pet, the goal (wind / lightning first / other), the wind pet and stone out, the worn
		// pieces carrying lightning (all kept - MT2009_PLUS_BOT_WIND_SET_V1) - and the period's wind work in the shop
		{
			const int BANDS = 3;	// 90-94, 95-99, 100-119
			static const char* const s_aszBands[BANDS] = { "90-94", "95-99", "100+" };
			int bots[BANDS] = { 0 }, spread[BANDS][5] = { { 0 } }, elecOk[BANDS] = { 0 }, goalWind[BANDS] = { 0 };
			int goalElec[BANDS] = { 0 }, goalOther[BANDS] = { 0 }, windPet[BANDS] = { 0 }, stone[BANDS] = { 0 };
			int kept[BANDS] = { 0 }, inZaklety[BANDS] = { 0 };
			long windSum[BANDS] = { 0 }, elecSum[BANDS] = { 0 };
			const int elecGate = GetPlayerBotElementProgressGate();
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (!ch || !ch->IsItemLoaded() || ch->GetLevel() < 90 || ch->GetLevel() >= 120 || GetPlayerBotHuntElement(ch) != 0 ||
						IsPlayerBotYoharaBonusMember(ch))
					continue;
				const int b = ch->GetLevel() < 95 ? 0 : ch->GetLevel() < 100 ? 1 : 2;
				++bots[b];
				const int wind = GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_WIND);
				const int elecOwn = GetPlayerBotElementMapResistOwn(ch, PLAYERBOT_EM_ELEC);
				windSum[b] += wind;
				elecSum[b] += elecOwn;
				++spread[b][wind < 20 ? 0 : wind < 30 ? 1 : wind < 40 ? 2 : wind < 45 ? 3 : 4];
				elecOk[b] += elecOwn >= elecGate ? 1 : 0;
				windPet[b] += IsPlayerBotElementShopPetOut(ch, PLAYERBOT_EM_WIND) ? 1 : 0;
				stone[b] += FindPlayerBotWornElementStone(ch) ? 1 : 0;
				inZaklety[b] += GetPlayerBotElementMapBase(ch->GetMapIndex()) == PLAYERBOT_MAP_ZAKLETY ? 1 : 0;
				TPlayerBotElementMapView v;
				if (!GetPlayerBotElementMapGoal(ch, v))
					++goalOther[b];
				else if (v.iElement == PLAYERBOT_EM_WIND)
				{
					++goalWind[b];
					static const BYTE s_wears[] = { WEAR_BODY, WEAR_HEAD, WEAR_WRIST,
#ifdef ENABLE_PENDANT_SYSTEM
						WEAR_PENDANT,
#endif
					};
					for (size_t w = 0; v.iKeep >= 0 && w < sizeof(s_wears) / sizeof(s_wears[0]); ++w)
					{
						LPITEM piece = ch->GetWear(s_wears[w]);
						if (piece && HasPlayerBotElementProgressKeptLine(piece, v.iKeep))
							++kept[b];
					}
				}
				else if (IsPlayerBotWindBuildHolder(ch, v.iElement))
					++goalElec[b];
				else
					++goalOther[b];
			}
			std::string bands;
			for (int b = 0; b < BANDS; ++b)
			{
				if (!bots[b])
					continue;
				char buf[384];
				snprintf(buf, sizeof(buf), " %s=[bots=%d wind_avg=%ld lt20=%d 20-29=%d 30-39=%d 40-44=%d 45+=%d lightning_own_avg=%ld "
						"lightning_own_ok=%d goal_wind=%d goal_lightning_first=%d goal_other=%d wind_pet=%d stone=%d "
						"lightning_pieces_kept=%d in_zaklety=%d]",
						s_aszBands[b], bots[b], windSum[b] / bots[b], spread[b][0], spread[b][1], spread[b][2], spread[b][3],
						spread[b][4], elecSum[b] / bots[b], elecOk[b], goalWind[b], goalElec[b], goalOther[b], windPet[b], stone[b],
						kept[b], inZaklety[b]);
				bands += buf;
			}
			std::vector<int>& wm = s_kPlayerBotEShop.windMinutes;
			std::sort(wm.begin(), wm.end());
			sys_log(0, "PLAYERBOT_WIND_CENSUS:%s period=[starts=%u reached=%u min_median=%d sessions=%u short=%u sm=%lld "
					"changes=%u adds=%u pets_bought=%u lightning_first_sessions=%u] wind_from=%d budget=%lld",
					bands.empty() ? " none" : bands.c_str(), s_kPlayerBotEShop.windStarts, s_kPlayerBotEShop.windReached,
					wm.empty() ? -1 : wm[wm.size() / 2], s_kPlayerBotEShop.windSessions, s_kPlayerBotEShop.windShort,
					s_kPlayerBotEShop.windSm, s_kPlayerBotEShop.windChanges, s_kPlayerBotEShop.windAdds, s_kPlayerBotEShop.windPets,
					s_kPlayerBotEShop.holderSessions, GetPlayerBotElementProgressWindFrom(),
					GetPlayerBotElementShopBudgetFor(PLAYERBOT_EM_WIND));
		}
		s_kPlayerBotEShop = TPlayerBotEShopStats();
	}

	// ---------------------------------------------------------------- the pass

	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: one HP session of a reached boost (out of a fight, every step), the end logged.
	void WorkPlayerBotElementShopBoostHp(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec,
			const TPlayerBotElementMapView& v, DWORD dwNow)
	{
		rec.dwNext = dwNow + PLAYERBOT_ESHOP_STEP_MS;
		if (IsPlayerBotGearFrozen(ch) || ch->IsBusy() || ch->GetMyShop() || ch->GetExchange() || !ch->CanHandleItem())
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		if (!state.bDragonBalanceKnown)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		int purchases = 0;
		if (WorkPlayerBotElementShopHp(ch, state, rec, v, dwNow, &purchases))
			return;
		rec.bHpWanted = false;
		++s_kPlayerBotEShop.hpDone;
		sys_log(0, "PLAYERBOT_EPROG_SHOP: hp_done pid=%u name=%s lv=%d element=%s resist=%d target=%d max_hp=%d hp_pieces=%u "
				"sm=%lld boosts=%d coins=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
				GetPlayerBotElementMapElementName(v.iElement), v.iResist, rec.iTarget, (int)ch->GetMaxHP(),
				(unsigned int)rec.hpPieces.size(), rec.llSpent, rec.iBoosts, state.iDragonCoins);
	}

	void WorkPlayerBotElementShopStep(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec,
			const TPlayerBotElementMapView& v, const TPlayerBotEShopPlan& plan, DWORD dwNow, int* purchases);	// below

	void ManagePlayerBotElementShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		TickPlayerBotElementShopCensus(dwNow);
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc() || !IsPlayerBotElementShopOn() ||
				GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled())
			return;
		// every bot has a record (its clock - the goal is asked every PLAYERBOT_ESHOP_IDLE_MS, not every tick)
		TPlayerBotEShopRecord& rec = s_mapPlayerBotEShop[ch->GetPlayerID()];
		if (rec.dwNext != 0 && (int)(dwNow - rec.dwNext) < 0)
			return;
		rec.dwSeen = dwNow ? dwNow : 1;
		rec.dwNext = dwNow + PLAYERBOT_ESHOP_IDLE_MS + PlayerBotNavHash(ch->GetPlayerID() ^ 0x45534850U) % 5000U;
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementShopView(ch, v))
		{
			if (IsPlayerBotElementShopActive(&rec))
			{
				++s_kPlayerBotEShop.left;
				sys_log(0, "PLAYERBOT_EPROG_SHOP: left pid=%u name=%s lv=%d element=%s resist_start=%d sm=%lld minutes=%u "
						"(the goal is gone - the window passed, a gated map no longer wanted, a Yohara cohort, a hunt element)",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotElementMapElementName(rec.iElement),
						rec.iResistStart, rec.llSpent, (unsigned int)((dwNow - rec.dwStart) / 60000U));
				rec.dwStart = 0;
				rec.dwFocusItem = 0;
				rec.iFocusWear = -1;
				rec.llPlanCost = 0;
			}
			return;
		}
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: or a retreat's raised target
		const int target = std::min(PLAYERBOT_ELEMENT_MAP_RESIST_CAP, std::max(v.iGate + GetPlayerBotElementShopMargin(),
				GetPlayerBotElementProgressBoostTarget(ch, v.iElement)));
		const long map = PLAYERBOT_ELEMENT_MAP_ROWS[v.iRow].lMap;
		// a new step (another element or gate): a new record
		if (rec.iElement != v.iElement || rec.iGate != v.iGate)
		{
			const DWORD next = rec.dwNext;
			rec = TPlayerBotEShopRecord();
			rec.iElement = v.iElement;
			rec.iGate = v.iGate;
			rec.dwSeen = dwNow ? dwNow : 1;
			rec.dwNext = next;
		}
		rec.iTarget = target;
		rec.lMap = map;
		// a reached step: the arrival on the map logged; urgent again only under the gate
		if (rec.dwReached != 0)
		{
			if (!rec.bArrivedLogged && GetPlayerBotElementMapBase(ch->GetMapIndex()) == map)
			{
				rec.bArrivedLogged = true;
				sys_log(0, "PLAYERBOT_EPROG_SHOP: arrived pid=%u name=%s lv=%d map=%ld(%s) resist=%d minutes_after_reached=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), map, PLAYERBOT_ELEMENT_MAP_ROWS[v.iRow].szName,
						v.iResist, (unsigned int)((dwNow - rec.dwReached) / 60000U));
			}
			if (v.iResist >= v.iGate)
			{
				// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the boost's HP lines after the element
				if (rec.bHpWanted)
					WorkPlayerBotElementShopBoostHp(ch, state, rec, v, dwNow);
				return;
			}
			// under the gate again (an expiry): urgent again
			++s_kPlayerBotEShop.again;
			sys_log(0, "PLAYERBOT_EPROG_SHOP: again pid=%u name=%s lv=%d element=%s resist=%d gate=%d", ch->GetPlayerID(),
					ch->GetName(), ch->GetLevel(), GetPlayerBotElementMapElementName(v.iElement), v.iResist, v.iGate);
			rec.dwReached = 0;
			rec.dwStart = 0;
			rec.bArrivedLogged = false;
			rec.bStoneCounted = false;
			rec.bStoneWanted = false;
			rec.dwStoneWantedSince = 0;
			rec.bPetBought = false;	// a seal past its days is bought again
		}
		if (v.iResist >= target)
		{
			if (rec.dwStart != 0)
			{
				const unsigned int minutes = (unsigned int)((dwNow - rec.dwStart) / 60000U);
				rec.dwReached = dwNow ? dwNow : 1;
				rec.dwFocusItem = 0;
				rec.iFocusWear = -1;
				rec.llPlanCost = 0;
				++s_kPlayerBotEShop.reached;
				s_kPlayerBotEShop.smReached += rec.llSpent;
				s_kPlayerBotEShop.minutesReached += minutes;
				s_kPlayerBotEShop.resistStartReached += rec.iResistStart;
				s_kPlayerBotEShop.minutes.push_back((int)minutes);
				if (v.iElement == PLAYERBOT_EM_WIND)	// MT2009_PLUS_BOT_WIND_BUILD_V1
				{
					++s_kPlayerBotEShop.windReached;
					s_kPlayerBotEShop.windMinutes.push_back((int)minutes);
				}
				sys_log(0, "PLAYERBOT_EPROG_SHOP: reached pid=%u name=%s lv=%d element=%s gate=%d target=%d resist=%d->%d sm=%lld "
						"minutes=%u changes=%d adds=%d pet=%d stone=%d map=%ld(%s) prebuild=%d coins=%d",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotElementMapElementName(v.iElement), v.iGate,
						target, rec.iResistStart, v.iResist, rec.llSpent, minutes, rec.iChanges, rec.iAdds,
						IsPlayerBotElementShopPetOut(ch, v.iElement) ? 1 : 0, FindPlayerBotWornElementStone(ch) ? 1 : 0, map,
						PLAYERBOT_ELEMENT_MAP_ROWS[v.iRow].szName, v.bPrebuild ? 1 : 0, state.iDragonCoins);
			}
			return;
		}
		// urgent
		if (rec.dwStart == 0)
		{
			rec.dwStart = dwNow ? dwNow : 1;
			rec.iResistStart = v.iResist;
			++s_kPlayerBotEShop.starts;
			if (v.iElement == PLAYERBOT_EM_WIND)	// MT2009_PLUS_BOT_WIND_BUILD_V1
				++s_kPlayerBotEShop.windStarts;
			sys_log(0, "PLAYERBOT_EPROG_SHOP: start pid=%u name=%s lv=%d element=%s resist=%d gate=%d target=%d map=%ld(%s) "
					"prebuild=%d keep=%d coins=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
					GetPlayerBotElementMapElementName(v.iElement), v.iResist, v.iGate, target, map,
					PLAYERBOT_ELEMENT_MAP_ROWS[v.iRow].szName, v.bPrebuild ? 1 : 0, v.iKeep, state.iDragonCoins);
		}
		rec.dwNext = dwNow + PLAYERBOT_ESHOP_STEP_MS;
		// the stone the stone pass bought and put on: its price counted once
		LPITEM wornStone = FindPlayerBotWornElementStone(ch);
		if (wornStone && rec.bStoneWanted && !rec.bStoneCounted)
		{
			rec.bStoneCounted = true;
			rec.llSpent += (long long)GetPlayerBotItemShopCheapest(ch, PLAYERBOT_ELEMSTONE_PROTECT_VNUM, false);
		}
		if (IsPlayerBotGearFrozen(ch) || ch->IsBusy() || ch->GetMyShop() || ch->GetExchange() || !ch->CanHandleItem())
			return;
		++s_kPlayerBotEShop.sessions;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		// the balance once when never read (a purchase reads it fresh itself, BuyPlayerBotIshop3Line)
		if (!state.bDragonBalanceKnown)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		TPlayerBotEShopPlan plan;
		BuildPlayerBotElementShopPlan(ch, v, rec, target, plan);
		rec.llPlanCost = (long long)plan.dCost;
		const bool wasShort = rec.bPlanShort;
		rec.bPlanShort = plan.bShort;
		if (plan.bStone && rec.dwStoneWantedSince == 0)
			rec.dwStoneWantedSince = dwNow ? dwNow : 1;
		rec.bStoneWanted = plan.bStone || (rec.bStoneWanted && !wornStone && rec.dwStoneWantedSince != 0 &&
				dwNow - rec.dwStoneWantedSince <= PLAYERBOT_ESHOP_STONE_WAIT_MS);
		{
			std::string what;
			for (size_t i = 0; i < plan.chosen.size(); ++i)
			{
				const TPlayerBotEShopOption& o = plan.chosen[i];
				char buf[64];
				if (o.iKind == PLAYERBOT_ESHOP_OPT_STONE || o.iKind == PLAYERBOT_ESHOP_OPT_PET)
					snprintf(buf, sizeof(buf), "%s%s+%d:%.0f", what.empty() ? "" : ",", o.iKind == PLAYERBOT_ESHOP_OPT_STONE ? "stone" : "pet",
							o.iGain, o.dCost);
				else
					snprintf(buf, sizeof(buf), "%sslot%u_%s+%d:%.0f", what.empty() ? "" : ",", (unsigned int)plan.pieces[o.iPiece].bWear,
							o.iKind == PLAYERBOT_ESHOP_OPT_FLOOR ? "floor" : "top",
							o.iGain, o.dCost);
				what += buf;
			}
			PlayerBotLogThrottled("eshop_plan", dwNow,
					"PLAYERBOT_EPROG_SHOP: plan pid=%u name=%s lv=%d element=%s resist=%d target=%d gap=%d sm_expected=%.0f "
					"short=%d change_sm=%.1f add_sm=%.1f pieces=%u [%s] spent=%lld coins=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotElementMapElementName(v.iElement), plan.iResist,
					target, plan.iGap, plan.dCost, plan.bShort ? 1 : 0, plan.dUnitChange, plan.dUnitAdd,
					(unsigned int)plan.pieces.size(), what.c_str(), rec.llSpent, state.iDragonCoins);
			if (plan.bShort && !wasShort)
				sys_log(0, "PLAYERBOT_EPROG_SHOP: short pid=%u name=%s lv=%d element=%s resist=%d target=%d pieces=%u [%s] "
						"(every source taken; the pieces go on to their top)",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotElementMapElementName(v.iElement),
						plan.iResist, target, (unsigned int)plan.pieces.size(), what.c_str());
		}
		int purchases = 0;
		// MT2009_PLUS_BOT_WIND_BUILD_V1: a bot of the wind window building lightning keeps its lightning pet out while it
		// does (the plan counts it not - the pieces must hold the gate without it)
		const bool holder = IsPlayerBotWindBuildHolder(ch, v.iElement);
		if (holder)
			++s_kPlayerBotEShop.holderSessions;
		if (v.iElement == PLAYERBOT_EM_WIND)
		{
			++s_kPlayerBotEShop.windSessions;
			if (plan.bShort && !wasShort)
				++s_kPlayerBotEShop.windShort;
		}
		const long long spentBefore = rec.llSpent;
		const int changesBefore = rec.iChanges, addsBefore = rec.iAdds;
		const bool petBoughtBefore = rec.bPetBought;
		if (plan.bPet || (holder && !IsPlayerBotElementShopPetOut(ch, v.iElement)))
			ManagePlayerBotElementShopPet(ch, state, rec, v.iElement, dwNow, &purchases);
		WorkPlayerBotElementShopStep(ch, state, rec, v, plan, dwNow, &purchases);
		if (v.iElement == PLAYERBOT_EM_WIND)
		{
			s_kPlayerBotEShop.windSm += rec.llSpent - spentBefore;
			s_kPlayerBotEShop.windChanges += (unsigned int)std::max(0, rec.iChanges - changesBefore);
			s_kPlayerBotEShop.windAdds += (unsigned int)std::max(0, rec.iAdds - addsBefore);
			s_kPlayerBotEShop.windPets += rec.bPetBought && !petBoughtBefore ? 1 : 0;
		}
	}

	// The step's piece: the one being worked while the plan keeps it, else the plan's cheapest.
	void WorkPlayerBotElementShopStep(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotEShopRecord& rec,
			const TPlayerBotElementMapView& v, const TPlayerBotEShopPlan& plan, DWORD dwNow, int* purchases)
	{
		// the piece: the one being worked while the plan keeps it, else the plan's cheapest
		int pick = -1;
		int want = 0;
		for (size_t i = 0; i < plan.chosen.size(); ++i)
		{
			const TPlayerBotEShopOption& o = plan.chosen[i];
			if (o.iKind != PLAYERBOT_ESHOP_OPT_FLOOR && o.iKind != PLAYERBOT_ESHOP_OPT_TOP)
				continue;
			const TPlayerBotEShopPiece& p = plan.pieces[o.iPiece];
			const int w = o.iKind == PLAYERBOT_ESHOP_OPT_FLOOR ? p.iFloor : p.iTop;
			if (pick < 0 || (p.item->GetID() == rec.dwFocusItem && plan.pieces[pick].item->GetID() != rec.dwFocusItem))
			{
				pick = o.iPiece;
				want = w;
			}
			else if (o.iPiece == pick)
				want = std::max(want, w);
		}
		if (pick < 0)
		{
			rec.dwFocusItem = 0;
			rec.iFocusWear = -1;
			return;	// the stone and the pet close the gap (the stone pass puts it on)
		}
		const TPlayerBotEShopPiece& p = plan.pieces[pick];
		rec.dwFocusItem = p.item->GetID();
		rec.iFocusWear = p.bWear;
		if (IsPlayerBotEquipWindowShut(ch, state))
		{
			++s_kPlayerBotEShop.windowWaits;
			rec.dwNext = dwNow + PLAYERBOT_ESHOP_WINDOW_RETRY_MS;
			return;
		}
		WorkPlayerBotElementShopPiece(ch, state, rec, p, PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement], want, dwNow, purchases);
	}
}

#else

namespace
{
	// the hooks of the other passes without the ItemShop V3: nothing pinned, wanted or kept back
	bool IsPlayerBotElementShopStoneWanted(LPCHARACTER) { return false; }
	bool IsPlayerBotElementShopPinnedPiece(LPCHARACTER, LPITEM) { return false; }
	long long GetPlayerBotElementShopPoolRoom(LPCHARACTER, const char*) { return -1; }
	long long GetPlayerBotElementShopReserve(LPCHARACTER) { return 0; }
	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: no shop - every retreat leaves
	bool TryPlayerBotElementShopBoost(LPCHARACTER, int, int*, const char** how, const char** why, long long* pCost)
	{
		*how = "-";
		*why = "no_shop";
		*pCost = 0;
		return false;
	}
}

#endif

#endif
