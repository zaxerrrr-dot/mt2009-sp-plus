#ifndef __INC_METIN2_PLAYERBOT_RANK_FRUIT_MARKET_H__
#define __INC_METIN2_PLAYERBOT_RANK_FRUIT_MARKET_H__

// MT2009_PLUS_RANK_FRUIT_MARKET_V1 - the bots buy the rank fruit they can eat
// (the owner, 8 October: "dlaczego boty wystawiaja tyle jablek, a ich nie
// uzywaja ani nie kupuja? Niech wiedza, ze ranga daje bonusy ... ci, ktorzy maja
// range juz poza zakresem jablek, niech wystawiaja jablka i kupuja gruszki").
//
// The fruits 80050-80054 (playerbot_rank_points.h) work in one range of the
// total each: Jablko under 20 000, Gruszka 20 000-40 000, and so on. A bot ate
// the fitting ones its own kills dropped and listed the rest - and nobody
// bought: no buying rule knew the fruits. So the counters filled with the
// fruits of the bands their keepers were past (test world, 8 October: 919
// Gruszki on 484 lines, kept by bots under 20 000 that can not eat them, and 79
// Jablka on 34 lines, all kept by bots at the alignment's cap), while 4 414 bot
// characters stood under 20 000, hungry for Jablka that their level's Metins
// no longer drop (Jablko is the fruit of monsters up to 53).
//
// Now an eater (IsPlayerBotRankFruitEater, three bots in four, never a
// trader) buys the fruit of its total off the counters - on every stand of its
// map, the gambler's way (FindPlayerBotGambleMaterialPick) - up to
// PLAYERBOT_RANK_FRUIT_BUY_AHEAD pieces ahead and no more than its range still
// takes, at most PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT of the price table
// (GetPlayerBotRankFruitPrice) a piece and out of
// PLAYERBOT_RANK_FRUIT_PURSE_PERCENT of what it can spare. It eats them at its
// next look (ManagePlayerBotRankPoints). The other bots list every fruit they
// hold, and every bot lists a fruit out of its range.
//
// MT2009_PLUS_RANK_FRUIT_GOAL_V1 (6 November 2026): every bot but a trader eats and buys only up to its rank goal
// (GetPlayerBotRankGoal, playerbot_rank_points.h), keeps a reserve and lists the rest; the price follows supply and
// demand (GetPlayerBotRankFruitListUnit) and the census is "PLAYERBOT_RANK_FRUIT:" (both at the end of this file).
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, from playerbot_manager.cpp, before playerbot_market.h.

namespace
{
	int GetPlayerBotReservedGold(LPCHARACTER ch);

	const int PLAYERBOT_RANK_FRUIT_BUY_AHEAD = 10;
	const int PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT = 130;
	const int PLAYERBOT_RANK_FRUIT_PURSE_PERCENT = 30;

	// The fruit this bot eats now, or NULL: an eater, its total read, in a range.
	const mt2009_rankp::SFruit* GetPlayerBotRankFruitToEat(LPCHARACTER ch)
	{
		using namespace mt2009_rankp;
		if (!ch || !Enabled() || !IsPlayerBotRankFruitEater(ch) || !Known(ch))
			return NULL;
		return GetPlayerBotRankFruitDue(ch);	// MT2009_PLUS_RANK_FRUIT_GOAL_V1: under the goal only (V1: the total's fruit)
	}

	// How many more pieces of its fruit the bot buys: what its range still
	// takes, PLAYERBOT_RANK_FRUIT_BUY_AHEAD at most, less what it holds.
	int GetPlayerBotRankFruitWant(LPCHARACTER ch, DWORD* vnumOut = NULL)
	{
		const mt2009_rankp::SFruit* fruit = GetPlayerBotRankFruitToEat(ch);
		if (vnumOut)
			*vnumOut = fruit ? fruit->vnum : 0;
		if (!fruit || !ch->IsItemLoaded() || fruit->gain <= 0)
			return 0;
		// MT2009_PLUS_RANK_FRUIT_GOAL_V1: up to the goal, not the range's top.
		const int top = IsPlayerBotRankFruitGoalOn() ? std::min(fruit->to, GetPlayerBotRankGoal(ch)) : fruit->to;
		const int left = top - mt2009_rankp::KnownPoints(ch);
		const int range = std::max(1, (left + fruit->gain - 1) / fruit->gain);
		return std::max(0, std::min(range, PLAYERBOT_RANK_FRUIT_BUY_AHEAD) - (int)ch->CountSpecifyItem(fruit->vnum));
	}

	// A counter's line the bot would eat: its fruit, no more than it wants.
	bool WantsPlayerBotRankFruitOffer(LPCHARACTER ch, LPITEM offer)
	{
		DWORD vnum = 0;
		const int want = GetPlayerBotRankFruitWant(ch, &vnum);
		return offer && want > 0 && offer->GetVnum() == vnum && (int)offer->GetCount() <= want;
	}

	// What an eater spends on fruit: a share of what it can spare.
	long long GetPlayerBotRankFruitBudget(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return spare > 0 ? spare * PLAYERBOT_RANK_FRUIT_PURSE_PERCENT / 100 : 0;
	}

	// The price: no more than the table's a piece and the tolerance, out of the
	// fruit's share of the purse.
	bool CanPlayerBotPayForRankFruit(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long unit = price / std::max<long long>(1, (long long)item->GetCount());
		const long long table = (long long)GetPlayerBotRankFruitPrice(item->GetVnum());
		return table > 0 && unit <= table * PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT / 100 &&
				price <= GetPlayerBotRankFruitBudget(ch);
	}

	// Worth a walk to the market: it wants its fruit, a counter has some (the
	// ledger) and the purse pays one at the table's price.
	bool PlayerBotWantsRankFruitFromMarket(LPCHARACTER ch)
	{
		DWORD vnum = 0;
		if (GetPlayerBotRankFruitWant(ch, &vnum) <= 0 || vnum == 0)
			return false;
		const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
		return entry && entry->dwSupplyUnits > 0 &&
				GetPlayerBotRankFruitBudget(ch) >= (long long)std::min(GetPlayerBotRankFruitPrice(vnum),
						std::max<DWORD>(1, GetPlayerBotRankFruitListUnit(vnum)));
	}

	// For the stands' scan (FindPlayerBotGambleMaterialPick): the fruit and how
	// many, and the most one line may cost. 0 - nothing wanted.
	long long CollectPlayerBotRankFruitMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		DWORD vnum = 0;
		const int want = GetPlayerBotRankFruitWant(ch, &vnum);
		if (want <= 0 || vnum == 0)
			return 0;
		const long long budget = GetPlayerBotRankFruitBudget(ch);
		if (budget < (long long)std::min(GetPlayerBotRankFruitPrice(vnum), std::max<DWORD>(1, GetPlayerBotRankFruitListUnit(vnum))))
			return 0;
		missing[vnum] = want;
		return budget;
	}

	// ---------------------------------------------------------------- MT2009_PLUS_RANK_FRUIT_GOAL_V1

	// The list price by supply and demand ("supply-driven", the owner, 6 November). The table price
	// (GetPlayerBotRankFruitPrice) is where it starts; the item_proto value is no price of anybody's.
	//   overstock - the clearing ask (playerbot_market_clearing.h: the counters hold more than a day's sales, the
	//               ask steps down until the fruit moves) - the Jablka: 10 000 and more on the counters of vps3
	//               and 83.168.69.144 against 1 100-1 600 sold a day;
	//   scarce    - sold faster than it stands (the units sold in the clearing's 12-hour window over twice the
	//               units on the counters): PLAYERBOT_RANK_FRUIT_SCARCE_LIFT percent over the table - under the
	//               eaters' tolerance (PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT), so they still buy.
	// m2_bot_rank_fruit_price_off 1: the table, as before.
	const int PLAYERBOT_RANK_FRUIT_SCARCE_LIFT = 20;

	DWORD GetPlayerBotRankFruitSold12h(DWORD vnum)
	{
		std::map<DWORD, TPlayerBotClearKind>::const_iterator it = s_mapPlayerBotClear.find(vnum);
		if (it == s_mapPlayerBotClear.end())
			return 0;
		unsigned long long sold = 0;
		for (int i = 0; i < PLAYERBOT_CLEAR_SALE_BUCKETS; ++i)
			sold += it->second.sales[i];
		return (DWORD)std::min<unsigned long long>(sold, 0xFFFFFFFFULL);
	}

	DWORD GetPlayerBotRankFruitListUnit(DWORD vnum)
	{
		const DWORD table = GetPlayerBotRankFruitPrice(vnum);
		if (table == 0 || !mt2009_rankp::BotFruitOn(mt2009_rankp::BOT_FRUIT_PRICE))
			return table;
		const DWORD clearUnit = GetPlayerBotClearingUnit(vnum);
		if (clearUnit > 0)
			return std::max<DWORD>(100, std::min(table, clearUnit));
		const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
		const DWORD supply = entry ? entry->dwSupplyUnits : 0;
		const DWORD sold = GetPlayerBotRankFruitSold12h(vnum);
		if (sold > 0 && (unsigned long long)sold > 2ULL * supply)
			return (DWORD)std::min<unsigned long long>(0xFFFFFFF0ULL,
					(unsigned long long)table * (100 + PLAYERBOT_RANK_FRUIT_SCARCE_LIFT) / 100 / 100 * 100);
		return table;
	}

	// The census - "PLAYERBOT_RANK_FRUIT:" every PLAYERBOT_RANK_FRUIT_CENSUS_MS: per fruit what the bots looked at in
	// the last PLAYERBOT_RANK_FRUIT_LOOK_TTL_MS hold in their bags (owned), keep (kept) and may list (surplus), what
	// they ate since the last census (used) and in all (used_total), what stands on this core's counters (listed:
	// the ledger, shop channel), what sold in 12 h (sold_12h, every buyer) and the ask.
	const DWORD PLAYERBOT_RANK_FRUIT_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_RANK_FRUIT_LOOK_TTL_MS = 15 * 60 * 1000;

	struct TPlayerBotRankFruitLook
	{
		DWORD at;
		DWORD held[mt2009_rankp::FRUIT_COUNT];
		DWORD kept[mt2009_rankp::FRUIT_COUNT];
		BYTE state;	// 0 no goal (a trader), 1 under the goal, 2 at it
	};
	std::map<DWORD, TPlayerBotRankFruitLook> s_mapPlayerBotRankFruitLooks;
	unsigned long long s_aPlayerBotRankFruitUsed[mt2009_rankp::FRUIT_COUNT];
	unsigned long long s_aPlayerBotRankFruitUsedTotal[mt2009_rankp::FRUIT_COUNT];
	DWORD s_dwPlayerBotRankFruitCensusAt = 0;

	void NotePlayerBotRankFruitEaten(DWORD vnum)
	{
		for (int i = 0; i < mt2009_rankp::FRUIT_COUNT; ++i)
			if (mt2009_rankp::FRUITS[i].vnum == vnum)
			{
				++s_aPlayerBotRankFruitUsed[i];
				++s_aPlayerBotRankFruitUsedTotal[i];
			}
	}

	void ReportPlayerBotRankFruits(DWORD dwNow)
	{
		using namespace mt2009_rankp;
		unsigned long long held[FRUIT_COUNT] = { 0 }, kept[FRUIT_COUNT] = { 0 };
		unsigned int bots = 0, traders = 0, under = 0, at = 0;
		for (std::map<DWORD, TPlayerBotRankFruitLook>::iterator it = s_mapPlayerBotRankFruitLooks.begin();
				it != s_mapPlayerBotRankFruitLooks.end();)
		{
			if (dwNow - it->second.at > PLAYERBOT_RANK_FRUIT_LOOK_TTL_MS)
			{
				s_mapPlayerBotRankFruitLooks.erase(it++);
				continue;
			}
			++bots;
			if (it->second.state == 0)
				++traders;
			else if (it->second.state == 1)
				++under;
			else
				++at;
			for (int i = 0; i < FRUIT_COUNT; ++i)
			{
				held[i] += it->second.held[i];
				kept[i] += it->second.kept[i];
			}
			++it;
		}
		sys_log(0, "PLAYERBOT_RANK_FRUIT: census bots=%u traders=%u under_goal=%u at_goal=%u goal_on=%d price_on=%d stack_on=%d",
				bots, traders, under, at, IsPlayerBotRankFruitGoalOn() ? 1 : 0, BotFruitOn(BOT_FRUIT_PRICE) ? 1 : 0,
				BotFruitOn(BOT_FRUIT_STACK) ? 1 : 0);
		for (int i = 0; i < FRUIT_COUNT; ++i)
		{
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(FRUITS[i].vnum);
			sys_log(0, "PLAYERBOT_RANK_FRUIT: census vnum=%u owned=%llu kept=%llu surplus=%llu used=%llu used_total=%llu "
					"listed=%u stalls=%u sold_12h=%u ask=%u table=%u",
					FRUITS[i].vnum, held[i], kept[i], held[i] - std::min(held[i], kept[i]), s_aPlayerBotRankFruitUsed[i],
					s_aPlayerBotRankFruitUsedTotal[i], entry ? entry->dwSupplyUnits : 0, entry ? entry->dwSupplyStalls : 0,
					GetPlayerBotRankFruitSold12h(FRUITS[i].vnum), GetPlayerBotRankFruitListUnit(FRUITS[i].vnum),
					GetPlayerBotRankFruitPrice(FRUITS[i].vnum));
			s_aPlayerBotRankFruitUsed[i] = 0;
		}
	}

	// At every look of a bot (ManagePlayerBotRankPoints): its bag noted, the census when due.
	void NotePlayerBotRankFruitLook(LPCHARACTER ch, DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (!ch)
			return;
		TPlayerBotRankFruitLook& look = s_mapPlayerBotRankFruitLooks[ch->GetPlayerID()];
		look.at = dwNow;
		const int goal = GetPlayerBotRankGoal(ch);
		look.state = goal <= 0 ? 0 : (KnownPoints(ch) < goal ? 1 : 2);
		for (int i = 0; i < FRUIT_COUNT; ++i)
		{
			look.held[i] = (DWORD)std::max(0, (int)ch->CountSpecifyItem(FRUITS[i].vnum));
			look.kept[i] = (DWORD)std::min<long long>(look.held[i],
					std::max(0, IsPlayerBotRankFruitEater(ch) ? GetPlayerBotRankFruitKeep(ch, FRUITS[i].vnum) : 0));
		}
		if (s_dwPlayerBotRankFruitCensusAt == 0)
			s_dwPlayerBotRankFruitCensusAt = dwNow;
		else if (dwNow - s_dwPlayerBotRankFruitCensusAt >= PLAYERBOT_RANK_FRUIT_CENSUS_MS)
		{
			s_dwPlayerBotRankFruitCensusAt = dwNow;
			ReportPlayerBotRankFruits(dwNow);
		}
	}
}

#endif
