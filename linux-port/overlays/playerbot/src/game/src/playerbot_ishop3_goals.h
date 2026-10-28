#ifndef __INC_METIN2_PLAYERBOT_ISHOP3_GOALS_H__
#define __INC_METIN2_PLAYERBOT_ISHOP3_GOALS_H__

// MT2009_PLUS_BOT_ISHOP_V3_V1 - what a bot buys in the ItemShop V3 for its gear (the owner, 28 October 2026).
//
// No category cap (the daily pool below is the only one): a purchase is made because a pass of the bot's own would use it now, a batch at a time,
// and the goal is asked again a few minutes later (PLAYERBOT_ISHOP3_GOAL_STEP_MS) - after the pass has spent what was
// bought - until it is reached or the Smocze Monety run out. "Reached" is the pass's own answer, never a count here:
//   * bonus_add / bonus_change / bonus_marble - the ordinary bonus pass (playerbot_bonus.h): its own choice
//     (PlayerBotWouldSpendDustStone: StepFor over the bot's own pieces with one more stone of the kind) would spend an
//     ordinary Wzmocnienie (71085) / Zaczarowanie (71084) now and the bag holds none; the marble (70024) while a worn
//     piece of four lines waits for its fifth (PlayerBotWantsBlessingMarble). Not while the bot's Magiczny Pyl already
//     makes that stone (ManagePlayerBotDustBonusStones / ManagePlayerBotDustMarble - that source comes first).
//     A Yohara bot (playerbot_yohara_bonus.h - its musts, the hunt element's resistance): the adds its pieces' open
//     lines take, the marble for a piece of four, and changes while its own Pick, given a bag over the reserve, would
//     still change a piece - topped up to the reserve plus PLAYERBOT_ISHOP3_YOHARA_CHANGE_BATCH; never for a piece that
//     has already taken PLAYERBOT_ISHOP3_YOHARA_PIECE_GIVE_UP changes (a target its slot cannot reach).
//   * cor - the Alchemist's flow (playerbot_alchemy.h): an alchemy user with a dragon stone kind under the grade / step
//     its level wants (GetPlayerBotDsTarget), nothing the Alchemist could still refine there with what it holds, fewer
//     than PLAYERBOT_ISHOP3_COR_LOW Cors left and room on the pages a Cor fills: up to PLAYERBOT_ISHOP3_COR_BATCH raw
//     Cor Draconis (51501, the only Cor bought) - opened and refined by the existing flow.
//   * bean - Zielona Smocza Fasola (100300) from V3 when its price in Smocze Monety, at the price sheet's yang a coin
//     (the Kupon SM (100) line), is under the Alchemist's yang price, while a strength refine waits and the bag holds
//     fewer than PLAYERBOT_ISHOP3_BEAN_LOW beans (the Alchemist's own sale stays the fallback).
//   * sash - Szarfa Wladcy +0 (85001) for a sash keeper (playerbot_sash.h) not done, short of a combine partner (a lone
//     grade-1 sash: one; an empty bag or a lone higher grade: a pair), within the keeper's three and its yang for the
//     combine.
//   * refine - Zwoj Blogoslawienstwa (25041, Smocze Znaki) while a worn piece is under scroll work and no safe scroll
//     is held: three (the 2+1 line when it is cheaper a piece).
// The lines: the cheapest a piece first (a pack when the batch takes it - up to a quarter more pieces than asked).
// Looks: from the coins over the open goals' next batches only (GetPlayerBotIshop3GoalReserve, read by the look's
// reserve in playerbot_itemshop.h). A set chest ("Sety Bonusowe", phase 2): a quarter of the dressed bots, at most
// once a week, ten rolls from a surplus over PLAYERBOT_ISHOP3_CHEST_MIN_SURPLUS.
// MT2009_PLUS_BOT_USE_SHOP_AIDS_V1 (playerbot_shop_aids.h, CollectPlayerBotShopAidGoals): the Seon-Hae additives
// (72065-72067) a bot's Seon-Hae recipe lacks, Blogoslawienstwo Przedmiotu (71052) while a Champion's glove would be
// rolled again, Ksiega Obrobki Kamienia (71083) while a cracked stone blocks a stone that waits. MT2009_PLUS_BOT_SEONHAE_V2:
// 71052 for any worn piece with 6th/7th lines, and Kamien Kowala (71025) / Magiczny Metal (71026) for the Blacksmith's
// better scrolls (crafting window 101 at Kowal 20016).
//
// The log: PLAYERBOT_ISHOP3 (bought / chest / bag full / not given, playerbot_itemshop.h) and the hourly census.
//
// MT2009_PLUS_BOT_SM_DAILY_POOL_V1 (the owner, 28 October 2026): the coins of a week no longer go in hours - every
// Smocze Monety purchase here (and the wishes', the element stone's and pet's, the Sung Ma premium's, the Loch
// ticket's) stays within the account's daily pool (playerbot_itemshop.h: a seventh of the weekly grant a day,
// cumulative). "Really needs it" - IsPlayerBotSmPoolUrgent, below - may take the next day's seventh too; these are the
// goals that block the bot's progression now:
//   * the Yohara bonus musts for the move to the next map: bonus_add / bonus_change / bonus_marble of a Yohara bot
//     while its hunt element's resistance - the must the Sung Ma move waits for (playerbot_element_resist.h, the
//     move's preparation, IsPlayerBotElementGearReady) - is not on its armour / helmet / bracelet / talisman yet, or a
//     move's preparation is open;
//   * the Sung Ma premium buff (72803) when the Will alone stands between the bot and the next map ("next_map",
//     bought as sungma_buff_next; never the renewal or a struggle's day);
//   * the element stone (element_stone) and the element pet (element_pet) - bought only when missing;
//   * the refine scrolls for a gear gate of the progression checklist: smith_scroll (Kamien Kowala, the Blacksmith's
//     better scroll), refine / blessing_scroll, while the checklist holds the bot for its gear
//     (GetPlayerBotProgressionNeeds & NEED_GEAR; the Blessing Scroll and Magiczny Metal are Smocze Znaki - outside the
//     pool anyway).
// Never urgent: the looks (costumes, hairstyles, skins, pets, mounts, the counter's hairstyle), the set chests, the Cors
// for the future grades, the beans, the sash, the ordinary bonus stones and the Seon-Hae aids, the boosters and
// elixirs, the Loch ticket, the wishes of the old needs list.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, after playerbot_element_pet.h (the
// itemshop's purchase, the bonus, alchemy and sash passes are all above).

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)

namespace
{
	const DWORD PLAYERBOT_ISHOP3_GOAL_STEP_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_ISHOP3_GOAL_IDLE_MS = 10 * 60 * 1000;
	const int PLAYERBOT_ISHOP3_MAX_GOALS = 8;
	const int PLAYERBOT_ISHOP3_ADD_BATCH_MAX = 8;
	const int PLAYERBOT_ISHOP3_CHANGE_BATCH = 8;
	const int PLAYERBOT_ISHOP3_YOHARA_ADD_BATCH_MAX = 16;
	const int PLAYERBOT_ISHOP3_YOHARA_CHANGE_BATCH = 40;
	const int PLAYERBOT_ISHOP3_YOHARA_CHANGE_LOW = 10;
	const int PLAYERBOT_ISHOP3_YOHARA_PIECE_GIVE_UP = 300;
	const DWORD PLAYERBOT_ISHOP3_COR_VNUM = 51501;
	const int PLAYERBOT_ISHOP3_COR_BATCH = 200;
	const int PLAYERBOT_ISHOP3_COR_LOW = 20;
	const int PLAYERBOT_ISHOP3_BEAN_BATCH = 20;
	const int PLAYERBOT_ISHOP3_BEAN_LOW = 3;
	const DWORD PLAYERBOT_ISHOP3_SASH_VNUM = 85001;
	const int PLAYERBOT_ISHOP3_REFINE_BATCH = 3;
	const DWORD PLAYERBOT_ISHOP3_YANG_PER_COIN_DEFAULT = 20000;
	// a session's purchases at most (a 200-Cor batch is twenty purchases of ten)
	const int PLAYERBOT_ISHOP3_SESSION_PURCHASES = 40;
	const int PLAYERBOT_ISHOP3_CHEST_SHARE = 25;
	const int PLAYERBOT_ISHOP3_CHEST_ROLLS = 10;
	const int PLAYERBOT_ISHOP3_CHEST_WEEK = 7 * 24 * 60 * 60;
	const long long PLAYERBOT_ISHOP3_CHEST_MIN_SURPLUS = 1000;
	const char* PLAYERBOT_ISHOP3_CHEST_FLAG = "playerbot.ishop3_chest";

	struct TPlayerBotIshop3Goal
	{
		DWORD dwVnum;
		bool bMarks;
		int iPieces;
		const char* szReason;
	};

	std::map<DWORD, DWORD> s_mapPlayerBotIshop3NextGoal;

	// The Magiczny Pyl the dust pass may still turn into stones (what the G0 package and the elixirs keep is not).
	int GetPlayerBotIshop3SpareDust(LPCHARACTER ch)
	{
		if (GetPlayerBotG0DustReserve(ch) > 0)
			return 0;
		return std::max(0, (int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM) - GetPlayerBotYoharaShopDustKeep(ch));
	}

#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
	// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: a Yohara bot whose move up the Sung Ma maps waits for its gear's must - the hunt
	// element's resistance not yet at its target on a piece that can still take it, or a move's preparation open.
	bool IsPlayerBotYoharaMoveWaitingOnBonus(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotYoharaBonusMember(ch))
			return false;
		std::map<DWORD, TPlayerBotHuntElement>::const_iterator h = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		if (h != s_mapPlayerBotHuntElement.end() && h->second.bPrepOpen && h->second.bPrepWait)
			return true;
		const int e = GetPlayerBotHuntElementIndex(ch);
		if (e < 0)
			return false;
		bool noStones = false;
		const bool ready = IsPlayerBotElementGearReady(ch, e, &noStones);
		return !ready || noStones;	// noStones: the line is missing and the bag has no stones for it
	}

	// The goals that may borrow the next day's seventh (the list: this file's header).
	bool IsPlayerBotSmPoolUrgent(LPCHARACTER ch, const char* reason)
	{
		if (!ch || !reason)
			return false;
		if (strcmp(reason, "element_stone") == 0 || strcmp(reason, "element_pet") == 0 ||
				strcmp(reason, "sungma_buff_next") == 0)
			return true;
		if (strcmp(reason, "bonus_add") == 0 || strcmp(reason, "bonus_change") == 0 || strcmp(reason, "bonus_marble") == 0)
			return IsPlayerBotYoharaMoveWaitingOnBonus(ch);
		if (strcmp(reason, "smith_scroll") == 0 || strcmp(reason, "refine") == 0 || strcmp(reason, "blessing_scroll") == 0)
			return (GetPlayerBotProgressionNeeds(ch->GetPlayerID()) & playerbot_progression::NEED_GEAR) != 0;
		return false;
	}
#endif

	// The ordinary pass's own pieces (worn, held for a slot - never goods) a line can still be added to: the open lines.
	int CountPlayerBotIshop3OpenLines(LPCHARACTER ch)
	{
		std::vector<TPlayerBotBonusTarget> targets;
		CollectPlayerBotBonusTargets(ch, targets);
		int open = 0;
		for (size_t i = 0; i < targets.size(); ++i)
		{
			const TPlayerBotBonusTarget& t = targets[i];
			if (!t.item || t.kind == PLAYERBOT_BONUS_TARGET_GOODS || IsPlayerBotGreenOnlyFor(ch, t) ||
					!CanPlayerBotItemRollNewLine(t.item))
				continue;
			const int lines = t.item->GetAttributeCount();
			if (lines < PLAYERBOT_BONUS_MAX_LINES)
				open += PLAYERBOT_BONUS_MAX_LINES - lines;
		}
		return open;
	}

	// The ordinary bonus pass's needs (not a Yohara bot's).
	void CollectPlayerBotIshop3OrdinaryBonus(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (ch->GetLevel() < PLAYERBOT_BONUS_MIN_LEVEL || IsPlayerBotGearFrozen(ch))
			return;
		const int dust = GetPlayerBotIshop3SpareDust(ch);
		const bool add = PlayerBotWouldSpendDustStone(ch, true);
		if (add && dust < PLAYERBOT_DUST_PER_ADD && n < PLAYERBOT_ISHOP3_MAX_GOALS)
		{
			const int open = std::max(1, std::min(CountPlayerBotIshop3OpenLines(ch), PLAYERBOT_ISHOP3_ADD_BATCH_MAX));
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS_ADD_VNUM, false, open, "bonus_add" };
			goals[n++] = g;
		}
		if (PlayerBotWantsBlessingMarble(ch) && dust < PLAYERBOT_DUST_PER_MARBLE && n < PLAYERBOT_ISHOP3_MAX_GOALS)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BLESSING_MARBLE_VNUM, false, 1, "bonus_marble" };
			goals[n++] = g;
		}
		// the dust goes to the add first (ManagePlayerBotDustBonusStones), so a change is the shop's unless more is left
		if (PlayerBotWouldSpendDustStone(ch, false) && n < PLAYERBOT_ISHOP3_MAX_GOALS &&
				dust < PLAYERBOT_DUST_PER_CHANGE + (add ? PLAYERBOT_DUST_PER_ADD : 0))
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS_CHANGE_VNUM, false, PLAYERBOT_ISHOP3_CHANGE_BATCH, "bonus_change" };
			goals[n++] = g;
		}
	}

	// A Yohara bot's needs, by its pass's own rules (playerbot_yohara_bonus_rules.h).
	void CollectPlayerBotIshop3YoharaBonus(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (IsPlayerBotGearFrozen(ch))
			return;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		if (IsPlayerBotSecondSetSwapPending(ch))
			return;
#endif
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		std::vector<TPlayerBotYoharaBonusPiece> pieces;
		CollectPlayerBotYoharaBonusPieces(ch, pieces);
		if (pieces.empty())
			return;
		static const std::map<DWORD, int> s_none;
		std::map<DWORD, std::map<DWORD, int> >::const_iterator memory = s_mapPlayerBotYoharaBonusSpent.find(ch->GetPlayerID());
		const std::map<DWORD, int>& spent = memory != s_mapPlayerBotYoharaBonusSpent.end() ? memory->second : s_none;
		int open = 0;
		bool fourLines = false;
		for (size_t i = 0; i < pieces.size(); ++i)
		{
			const playerbot_yohara_bonus_rules::TPiece p = BuildPlayerBotYoharaBonusPiece(ch, pieces[i], spent);
			if (!p.lineRolls)
				continue;
			if (p.lines < p.maxStoneLines)
				open += p.maxStoneLines - p.lines;
			else if (p.lines == p.maxStoneLines)
				fourLines = true;
		}
		const int addNeed = std::min(open - bag.addUnits, PLAYERBOT_ISHOP3_YOHARA_ADD_BATCH_MAX);
		if (addNeed > 0 && n < PLAYERBOT_ISHOP3_MAX_GOALS)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS_ADD_VNUM, false, addNeed, "bonus_add" };
			goals[n++] = g;
		}
		if (fourLines && bag.marbleCell < 0 && n < PLAYERBOT_ISHOP3_MAX_GOALS)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BLESSING_MARBLE_VNUM, false, 1, "bonus_marble" };
			goals[n++] = g;
		}
		// the changes: the pass's Pick with the bag topped up - would it still change a piece?
		if (bag.changeUnits >= PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE + PLAYERBOT_ISHOP3_YOHARA_CHANGE_LOW ||
				n >= PLAYERBOT_ISHOP3_MAX_GOALS)
			return;
		TPlayerBotYoharaBonusBag topped = bag;
		topped.addCell = -1;
		topped.addUnits = 0;
		topped.marbleCell = -1;
		topped.changeCell = 0;
		topped.changeUnits = PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE + PLAYERBOT_ISHOP3_YOHARA_CHANGE_BATCH;
		std::vector<playerbot_yohara_bonus_rules::TPiece> built;
		const playerbot_yohara_bonus_rules::TChoice c = PickPlayerBotYoharaBonus(ch, pieces, spent, topped, built);
		if (c.piece < 0 || c.step != playerbot_yohara_bonus_rules::STEP_CHANGE ||
				built[c.piece].spent >= PLAYERBOT_ISHOP3_YOHARA_PIECE_GIVE_UP)
			return;
		const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS_CHANGE_VNUM, false,
				PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE + PLAYERBOT_ISHOP3_YOHARA_CHANGE_BATCH - bag.changeUnits, "bonus_change" };
		goals[n++] = g;
	}

	// Raw Cors for a dragon stone kind under its target with nothing left to refine there.
	int GetPlayerBotIshop3CorNeed(LPCHARACTER ch)
	{
		if (!IsPlayerBotAlchemyUser(ch) || !ch->DragonSoul_IsQualified() ||
				CountPlayerBotOpenableCors(ch) >= PLAYERBOT_ISHOP3_COR_LOW || !PlayerBotHasRoomForCor(ch, PLAYERBOT_ISHOP3_COR_VNUM))
			return 0;
		const TPlayerBotDsTarget t = GetPlayerBotDsTarget(ch);
		if (t.grade == 0)
			return 0;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM worn = GetPlayerBotWornDs(ch, kind);
			const bool short_ = !worn || GetPlayerBotDsGrade(worn) < t.grade ||
					(GetPlayerBotDsGrade(worn) == t.grade && GetPlayerBotDsStep(worn) < t.step);
			if (!short_)
				continue;
			LPITEM a = NULL, b = NULL;
			if (FindPlayerBotDsRefine(ch, kind, a, b) == PLAYERBOT_DS_WORK_NONE)
				return PLAYERBOT_ISHOP3_COR_BATCH;
		}
		return 0;
	}

	// The yang a Smocze Moneta is worth: the price sheet's Kupon SM (100), the market's rate.
	long long GetPlayerBotIshop3YangPerCoin()
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_EXTRA_MATERIAL_PRICES) / sizeof(PLAYERBOT_EXTRA_MATERIAL_PRICES[0]); ++i)
			if (PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwVnum == 80014 && PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwPrice > 0)
				return std::max<long long>(1, (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_EXTRA_MATERIAL_PRICES[i].dwPrice) / 100);
		for (size_t i = 0; i < sizeof(PLAYERBOT_MATERIAL_PRICES) / sizeof(PLAYERBOT_MATERIAL_PRICES[0]); ++i)
			if (PLAYERBOT_MATERIAL_PRICES[i].dwVnum == 80014 && PLAYERBOT_MATERIAL_PRICES[i].dwPrice > 0)
				return std::max<long long>(1, (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_MATERIAL_PRICES[i].dwPrice) / 100);
		return (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_ISHOP3_YANG_PER_COIN_DEFAULT);
	}

	// Green beans from V3 when a strength refine waits and V3's bean is the cheaper in yang.
	int GetPlayerBotIshop3BeanNeed(LPCHARACTER ch)
	{
		if (!IsPlayerBotAlchemyUser(ch) || CountPlayerBotDsBeans(ch) >= PLAYERBOT_ISHOP3_BEAN_LOW)
			return 0;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(PLAYERBOT_DS_GREEN_BEAN_VNUM);
		TPlayerBotItemShopTable::const_iterator it = s_mapPlayerBotItemShopCoins.find(PLAYERBOT_DS_GREEN_BEAN_VNUM);
		if (!proto || it == s_mapPlayerBotItemShopCoins.end())
			return 0;
		long long best = 0;
		for (size_t i = 0; i < it->second.size(); ++i)
		{
			const long long unit = (long long)it->second[i].dwPrice * GetPlayerBotIshop3YangPerCoin() /
					std::max<DWORD>(1, it->second[i].dwCount);
			if (best == 0 || unit < best)
				best = unit;
		}
		if (best == 0 || best >= (long long)proto->dwGold)
			return 0;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM a = NULL, b = NULL;
			if (FindPlayerBotDsRefine(ch, kind, a, b) == PLAYERBOT_DS_WORK_STRENGTH)
				return PLAYERBOT_ISHOP3_BEAN_BATCH;
		}
		return 0;
	}

	// Szarfa Wladcy +0 for a keeper short of a combine partner.
	int GetPlayerBotIshop3SashNeed(LPCHARACTER ch)
	{
#if defined(ENABLE_ACCE_COSTUME_SYSTEM)
		if (!IsPlayerBotSashKeeper(ch))
			return 0;
		const TPlayerBotSashTarget t = GetPlayerBotSashTarget(ch);
		if (t.grade <= 0 || IsPlayerBotSashDone(ch, t) || FindPlayerBotSashToFill(ch, t) ||
				GetPlayerBotSashSpareGold(ch) < (long long)ch->GetAcceCombinePrice(1))
			return 0;
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		const int room = PLAYERBOT_SASH_KEEP - (int)bag.size();
		if (room <= 0)
			return 0;
		int open = 0, loneOne = 0, loneHigher = 0;
		for (size_t i = 0; i < bag.size(); ++i)
		{
			if (IsPlayerBotSashAbsorbed(bag[i]) || GetPlayerBotSashGrade(bag[i]) >= t.grade)
				continue;
			++open;
			if (IsPlayerBotSashLone(ch, bag[i], t))
				++(GetPlayerBotSashGrade(bag[i]) == 1 ? loneOne : loneHigher);
		}
		int need = 0;
		if (loneOne > 0)
			need = 1;
		else if (loneHigher > 0 || open == 0)
			need = 2;
		return std::min(need, room);
#else
		(void)ch;
		return 0;
#endif
	}

#ifdef MT2009_PLUS_BOT_USE_SHOP_AIDS_V1
	// MT2009_PLUS_BOT_USE_SHOP_AIDS_V1 (goals): the Seon-Hae additives, 71052 and 71083 (playerbot_shop_aids.h, below).
	void CollectPlayerBotShopAidGoals(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n);
#endif

	// Every open goal, in the order the coins go: the bonus stones, the marble, the Cors, the beans, the sash, the
	// scrolls (Smocze Znaki - no coins taken from the rest).
	int CollectPlayerBotIshop3Goals(LPCHARACTER ch, TPlayerBotIshop3Goal* goals)
	{
		int n = 0;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		if (IsPlayerBotYoharaBonusMember(ch))
			CollectPlayerBotIshop3YoharaBonus(ch, goals, n);
		else
			CollectPlayerBotIshop3OrdinaryBonus(ch, goals, n);
		const int cors = n < PLAYERBOT_ISHOP3_MAX_GOALS ? GetPlayerBotIshop3CorNeed(ch) : 0;
		if (cors > 0)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_ISHOP3_COR_VNUM, false, cors, "cor" };
			goals[n++] = g;
		}
		const int beans = n < PLAYERBOT_ISHOP3_MAX_GOALS ? GetPlayerBotIshop3BeanNeed(ch) : 0;
		if (beans > 0)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_DS_GREEN_BEAN_VNUM, false, beans, "bean" };
			goals[n++] = g;
		}
		const int sashes = n < PLAYERBOT_ISHOP3_MAX_GOALS ? GetPlayerBotIshop3SashNeed(ch) : 0;
		if (sashes > 0)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_ISHOP3_SASH_VNUM, false, sashes, "sash" };
			goals[n++] = g;
		}
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && PlayerBotWearsScrollWork(ch) && CountPlayerBotSafeRefineScrolls(ch) == 0)
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM, true, PLAYERBOT_ISHOP3_REFINE_BATCH, "refine" };
			goals[n++] = g;
		}
#ifdef MT2009_PLUS_BOT_USE_SHOP_AIDS_V1
		CollectPlayerBotShopAidGoals(ch, goals, n);
#endif
		return n;
	}

	// The lines of a vnum the bot's level may buy, cheapest a piece first.
	void SortPlayerBotIshop3Lines(LPCHARACTER ch, DWORD vnum, bool marks, std::vector<const TPlayerBotItemShopEntry*>& out)
	{
		out.clear();
		const TPlayerBotItemShopTable& table = marks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
		TPlayerBotItemShopTable::const_iterator it = table.find(vnum);
		if (it == table.end())
			return;
		for (size_t i = 0; i < it->second.size(); ++i)
			if (it->second[i].dwCount > 0 && ch->GetLevel() >= it->second[i].bMinLevel)
				out.push_back(&it->second[i]);
		for (size_t i = 1; i < out.size(); ++i)
			for (size_t j = i; j > 0 && (unsigned long long)out[j]->dwPrice * out[j - 1]->dwCount <
					(unsigned long long)out[j - 1]->dwPrice * out[j]->dwCount; --j)
				std::swap(out[j], out[j - 1]);
	}

	// The coins the goal's batch costs (its cheapest piece times the pieces), for the look's reserve.
	long long GetPlayerBotIshop3GoalCost(LPCHARACTER ch, const TPlayerBotIshop3Goal& g)
	{
		std::vector<const TPlayerBotItemShopEntry*> lines;
		SortPlayerBotIshop3Lines(ch, g.dwVnum, g.bMarks, lines);
		if (lines.empty())
			return 0;
		return (long long)lines[0]->dwPrice * g.iPieces / std::max<DWORD>(1, lines[0]->dwCount);
	}

	long long GetPlayerBotIshop3GoalReserve(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		(void)state;
		if (!ch || GetPlayerBotItemShopSource() != 2 || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		TPlayerBotIshop3Goal goals[PLAYERBOT_ISHOP3_MAX_GOALS];
		const int n = CollectPlayerBotIshop3Goals(ch, goals);
		long long reserve = 0;
		for (int i = 0; i < n; ++i)
			if (!goals[i].bMarks)
				reserve += GetPlayerBotIshop3GoalCost(ch, goals[i]);
		return reserve;
	}

	// One goal's batch: the cheapest line a piece that the remaining pieces take (a pack with up to a quarter more
	// pieces than asked), as many as the balance pays, again until the batch is bought or nothing more can be.
	// The pieces bought; *purchases counts the session's purchases.
	int BuyPlayerBotIshop3Pieces(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotIshop3Goal& goal, DWORD dwNow,
			int* purchases)
	{
		std::vector<const TPlayerBotItemShopEntry*> lines;
		SortPlayerBotIshop3Lines(ch, goal.dwVnum, goal.bMarks, lines);
		if (lines.empty())
		{
			++GetPlayerBotIshop3Census(goal.szReason).uNotListed;
			return 0;
		}
		int bought = 0;
		bool noCoins = false;
		bool poolBlock = false;
		while (bought < goal.iPieces && *purchases < PLAYERBOT_ISHOP3_SESSION_PURCHASES)
		{
			const int left = goal.iPieces - bought;
			const int balance = goal.bMarks ? state.iDragonMarks : state.iDragonCoins;
			int have = balance;
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
			// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: Smocze Monety only up to what the daily pool leaves the goal
			if (!goal.bMarks)
				have = (int)std::max(0LL, std::min((long long)balance, GetPlayerBotSmPoolRoom(ch, state, goal.szReason).Room()));
#endif
			const TPlayerBotItemShopEntry* pick = NULL;
			int qty = 0;
			bool balanceWould = false;
			for (size_t i = 0; i < lines.size() && !pick; ++i)
			{
				const int count = (int)lines[i]->dwCount;
				if (count > left + left / 4 && i + 1 < lines.size())
					continue;
				const int want = std::max(1, std::min(left / std::max(1, count), PLAYERBOT_ISHOP3_MAX_QTY));
				const int afford = have / (int)std::max<DWORD>(1, lines[i]->dwPrice);
				const int q = std::min(lines[i]->bStackable ? want : 1, afford);
				if (balance >= (int)lines[i]->dwPrice)
					balanceWould = true;
				if (q >= 1)
				{
					pick = lines[i];
					qty = q;
				}
			}
			if (!pick)
			{
				(balanceWould ? poolBlock : noCoins) = true;
				break;
			}
			++*purchases;
			if (!BuyPlayerBotIshop3Line(ch, state, *pick, goal.dwVnum, goal.bMarks, qty, goal.szReason, dwNow))
				break;
			bought += (int)pick->dwCount * qty;
		}
		if (poolBlock)
		{
			++GetPlayerBotIshop3Census(goal.szReason).uPoolBlock;
			PlayerBotLogThrottled("ishop3_pool_goal", dwNow,
					"PLAYERBOT_ISHOP3: pool block pid=%u name=%s goal=%s vnum=%u wanted=%d bought=%d coins=%d",
					ch->GetPlayerID(), ch->GetName(), goal.szReason, goal.dwVnum, goal.iPieces, bought, state.iDragonCoins);
		}
		if (noCoins)
		{
			++GetPlayerBotIshop3Census(goal.szReason).uNoCoins;
			PlayerBotLogThrottled("ishop3_no_coins", dwNow,
					"PLAYERBOT_ISHOP3: no coins pid=%u name=%s goal=%s vnum=%u wanted=%d bought=%d coins=%d marks=%d",
					ch->GetPlayerID(), ch->GetName(), goal.szReason, goal.dwVnum, goal.iPieces, bought, state.iDragonCoins,
					state.iDragonMarks);
		}
		return bought;
	}

	// A set chest's rolls, from what the open goals leave, for a quarter of the dressed bots once a week.
	bool ManagePlayerBotIshop3Chest(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_vecPlayerBotIshop3Chests.empty() || ch->GetLevel() < PLAYERBOT_ISHOP_LOOK_MIN_LEVEL ||
				(int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x43485354U) % 100U) >= PLAYERBOT_ISHOP3_CHEST_SHARE)
			return false;
		const int last = ch->GetQuestFlag(PLAYERBOT_ISHOP3_CHEST_FLAG);
		if (last != 0 && get_global_time() - last < PLAYERBOT_ISHOP3_CHEST_WEEK)
			return false;
		int look = 0;
		if (PickPlayerBotLook(ch, &look) != 0)
			return false;	// a missing piece of the look is bought outright first
		std::vector<const TPlayerBotIshop3Chest*> mine;
		for (size_t i = 0; i < s_vecPlayerBotIshop3Chests.size(); ++i)
			if (ch->GetLevel() >= s_vecPlayerBotIshop3Chests[i].bMinLevel)
				mine.push_back(&s_vecPlayerBotIshop3Chests[i]);
		if (mine.empty())
			return false;
		const TPlayerBotIshop3Chest& chest = *mine[number(0, (int)mine.size() - 1)];
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		const long long cost = (long long)chest.dwPrice * PLAYERBOT_ISHOP3_CHEST_ROLLS;
		if ((long long)state.iDragonCoins - cost < PLAYERBOT_ISHOP3_CHEST_MIN_SURPLUS)
			return false;
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: the week's chest waits for a day whose allowance covers it (the flag unset)
		if (cost > GetPlayerBotSmPoolRoom(ch, state, "chest").Room())
		{
			++GetPlayerBotIshop3Census("chest").uPoolBlock;
			return false;
		}
#endif
		ch->SetQuestFlag(PLAYERBOT_ISHOP3_CHEST_FLAG, get_global_time());
		const bool ok = BuyPlayerBotIshop3Chest(ch, state, chest, PLAYERBOT_ISHOP3_CHEST_ROLLS, dwNow);
		if (ok)
			WearPlayerBotBoughtLook(ch, state);
		return ok;
	}

	// The session: every open goal a batch, in order, while the coins last; then the next look in a few minutes (a goal
	// was open) or at the idle pace. Nothing for a companion (its bag is its owner's) or with the source not V3.
	bool ManagePlayerBotIshop3Goals(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc() || GetPlayerBotItemShopSource() != 2 ||
				!IsPlayerBotItemShopEnabled() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		std::map<DWORD, DWORD>::iterator next = s_mapPlayerBotIshop3NextGoal.find(ch->GetPlayerID());
		if (next != s_mapPlayerBotIshop3NextGoal.end() && (int)(dwNow - next->second) < 0)
			return false;
		if (ch->IsBusy() || ch->GetMyShop() || ch->GetExchange() || !ch->CanHandleItem())
			return false;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		TPlayerBotIshop3Goal goals[PLAYERBOT_ISHOP3_MAX_GOALS];
		const int n = CollectPlayerBotIshop3Goals(ch, goals);
		const DWORD spread = PlayerBotNavHash(ch->GetPlayerID() ^ 0x49533347U) % 30000U;
		if (n == 0)
		{
			s_mapPlayerBotIshop3NextGoal[ch->GetPlayerID()] = dwNow + PLAYERBOT_ISHOP3_GOAL_IDLE_MS + spread;
			return ManagePlayerBotIshop3Chest(ch, state, dwNow);
		}
		s_mapPlayerBotIshop3NextGoal[ch->GetPlayerID()] = dwNow + PLAYERBOT_ISHOP3_GOAL_STEP_MS + spread;
		// the balance read fresh once, at the session's start (the grants come from outside the core)
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		int purchases = 0;
		bool any = false;
		std::string done;
		for (int i = 0; i < n && purchases < PLAYERBOT_ISHOP3_SESSION_PURCHASES; ++i)
		{
			const int got = BuyPlayerBotIshop3Pieces(ch, state, goals[i], dwNow, &purchases);
			if (got <= 0)
				continue;
			any = true;
			char buf[48];
			snprintf(buf, sizeof(buf), "%s%s:%d/%d", done.empty() ? "" : ",", goals[i].szReason, got, goals[i].iPieces);
			done += buf;
		}
		if (any)
			sys_log(0, "PLAYERBOT_ISHOP3: session pid=%u name=%s lv=%d goals=%d bought=[%s] coins=%d marks=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), n, done.c_str(), state.iDragonCoins, state.iDragonMarks);
		return any;
	}
}

#endif

#endif
