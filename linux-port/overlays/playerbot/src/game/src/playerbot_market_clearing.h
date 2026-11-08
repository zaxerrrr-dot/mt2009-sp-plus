#ifndef __INC_METIN2_PLAYERBOT_MARKET_CLEARING_H__
#define __INC_METIN2_PLAYERBOT_MARKET_CLEARING_H__

// MT2009_PLUS_BOT_MARKET_CLEARING_V1 - the supply-driven clearing price (the owner, 6 November 2026: "gdy jest duzo
// przedmiotow na rynku, zmniejszaj ceny, nie patrz na inflacje itd. [...] cene przy duzej ilosci przedmiotow
// zmniejszamy do momentu, az przedmioty beda znikac z rynku").
//
// Why: on the supporters' world 77 635 Rybia Osc (27799) stood on the bots' counters at 192-800 thousand a piece
// against buyer wallets of ~1.4 million and real sales at ~124 thousand. The asking price starts from the operator's
// sheet (450 000), goes through the yang curve and the inflation, the market index can lift it to 160 % and
// GetPlayerBotMarketFloor holds every line at half the sheet at least - nothing in that chain looks at how much of the
// thing is unsold. This is that missing piece, per item kind (vnum):
//
//   overstock   S units on the counters (the market ledger) >= MIN_UNITS and more than COVER_HOURS of the units sold
//               (every sale of every counter, a player's included - playerbot_offline::soldUnitsByVnum, a 12 h window)
//               plus PER_BUYER units for every bot short of it (the ledger's demand). Watched WARMUP_MIN first, so a
//               restart (no sales history yet) does not call everything unsold.
//   start       the clearing ask per unit: the counters' own average ask, never over WALLET_PERMILLE of the median buyer
//               wallet (1.5 M -> 75 000 at 50 permille). Not the item_proto value and not the operator's sheet.
//   step        every STEP_MIN while overstocked: if the kind is not disappearing - fewer than SELL_PERMILLE of the stock
//               sold since the last step and the stock not down by that much either - the ask comes down STEP_PCT,
//               to the floor (MIN_UNIT yang, or what the merchant pays for one, whichever is more). Disappearing: hold.
//   release     when the stock falls under half of the overstock line the ask goes back up RELAX_PCT a step; once it
//               reaches what the ordinary pricing asks (sheet, index, sale memory - the step limiter's anchor, and the
//               start ask at least) the kind is let go.
//
// The inflation index plays no part: the clearing ask caps the asking price at its very end
// (GetPlayerBotShopAskingPriceRaw), and the listing floor (GetPlayerBotListingFloor: sheet half, Dropki) never holds a
// line above it. The offline reprice looks at an overpriced line of a clearing kind first (BotOfflineRepriceTarget's
// caller), so the old 400 000 lines come down in hours, not in a counter's whole rotation.
//
// Shop channel's cores only, like the market index (the ledger counts the stands of its own channel). In memory: a
// restart begins again from the counters' asks, which already carry what the last run cleared to.
//
// Switches (environment, read once): PLAYERBOT_MARKET_CLEAR (1/0), PLAYERBOT_MARKET_CLEAR_MIN_UNITS (200),
// PLAYERBOT_MARKET_CLEAR_COVER_HOURS (24), PLAYERBOT_MARKET_CLEAR_PER_BUYER (5), PLAYERBOT_MARKET_CLEAR_WARMUP_MIN (60),
// PLAYERBOT_MARKET_CLEAR_WALLET_PERMILLE (50), PLAYERBOT_MARKET_CLEAR_STEP_MIN (30), PLAYERBOT_MARKET_CLEAR_STEP_PCT (10),
// PLAYERBOT_MARKET_CLEAR_SELL_PERMILLE (10), PLAYERBOT_MARKET_CLEAR_RELAX_PCT (5), PLAYERBOT_MARKET_CLEAR_MIN_UNIT (1000).
// Log prefix: "PLAYERBOT_MARKET_CLEAR:" (start/step/release throttled a minute; census with the market report).

namespace
{
	int ReadPlayerBotYoharaEnvInt(const char* name, int def, int lo, int hi);	// playerbot_yohara_bots.h
	bool IsPlayerBotCorVnum(DWORD vnum);
	bool IsPlayerBotFixedPriceTalismanVnum(DWORD vnum);
	bool IsPlayerBotGuildBuildMaterial(DWORD vnum);
	const std::set<DWORD>& GetPlayerBotRefineMaterialVnums();

	struct TPlayerBotClearingConfig
	{
		bool on;
		DWORD minUnits, coverHours, perBuyer, warmupMs, walletPermille, stepMs, stepPct, sellPermille, relaxPct, minUnit;
	};

	const TPlayerBotClearingConfig& GetPlayerBotClearingConfig()
	{
		static bool s_bRead = false;
		static TPlayerBotClearingConfig c;
		if (!s_bRead)
		{
			s_bRead = true;
			c.on = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR", 1, 0, 1) != 0;
			c.minUnits = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_MIN_UNITS", 200, 1, 10000000);
			c.coverHours = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_COVER_HOURS", 24, 1, 24 * 30);
			c.perBuyer = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_PER_BUYER", 5, 0, 1000);
			c.warmupMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_WARMUP_MIN", 60, 0, 24 * 60) * 60000U;
			c.walletPermille = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_WALLET_PERMILLE", 50, 1, 1000);
			c.stepMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_STEP_MIN", 30, 1, 24 * 60) * 60000U;
			c.stepPct = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_STEP_PCT", 10, 1, 50);
			c.sellPermille = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_SELL_PERMILLE", 10, 1, 1000);
			c.relaxPct = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_RELAX_PCT", 5, 1, 50);
			c.minUnit = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_MARKET_CLEAR_MIN_UNIT", 1000, 1, 100000000);
			sys_log(0, "PLAYERBOT_MARKET_CLEAR: config on=%d min_units=%u cover_h=%u per_buyer=%u warmup_min=%u wallet_permille=%u step_min=%u step_pct=%u sell_permille=%u relax_pct=%u min_unit=%u",
					c.on ? 1 : 0, c.minUnits, c.coverHours, c.perBuyer, c.warmupMs / 60000U, c.walletPermille,
					c.stepMs / 60000U, c.stepPct, c.sellPermille, c.relaxPct, c.minUnit);
		}
		return c;
	}

	// The goods the clearing prices: a stack of one kind - refine materials, ores, stones, scrolls, the rest of the
	// stackable goods. Never gear, a costume, a Dragon Stone, a skill book (every book is one vnum on the ledger,
	// priced by its skill), nor a good the operator prices on his own curve.
	bool IsPlayerBotClearingGoods(DWORD vnum)
	{
		if (vnum == 0 || IsPlayerBotCorVnum(vnum) || vnum == PLAYERBOT_CRAFT_MATERIAL_VNUM_PRICED ||
				vnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM || IsPlayerBotGuildBuildMaterial(vnum) ||
				IsPlayerBotFixedPriceTalismanVnum(vnum) || IsPlayerBotSmCouponVnum(vnum) ||
				IsPlayerBotBeltVnum(vnum) || IsPlayerBotSashVnum(vnum))
			return false;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto)
			return false;
		if (proto->bType == ITEM_WEAPON || proto->bType == ITEM_ARMOR || proto->bType == ITEM_COSTUME ||
				proto->bType == ITEM_SKILLBOOK || proto->bType == ITEM_DS || proto->bType == ITEM_BELT)
			return false;
		return IS_SET(proto->dwFlags, ITEM_FLAG_STACKABLE) || GetPlayerBotRefineMaterialVnums().count(vnum) != 0;
	}

	const int PLAYERBOT_CLEAR_SALE_BUCKETS = 12;	// one an hour: the sales window
	const size_t PLAYERBOT_CLEAR_MAX_KINDS = 4096;

	struct TPlayerBotClearKind
	{
		DWORD firstSeen;
		DWORD sales[PLAYERBOT_CLEAR_SALE_BUCKETS];
		DWORD bucketHour;	// the hour (since firstSeen) sales[bucketHour % N] counts
		DWORD clearUnit;	// 0: not clearing
		DWORD startUnit;
		DWORD stepAt;
		DWORD supplyAtStep;
		DWORD soldSinceStep;
		int steps;
		TPlayerBotClearKind() : firstSeen(0), bucketHour(0), clearUnit(0), startUnit(0), stepAt(0), supplyAtStep(0),
				soldSinceStep(0), steps(0)
		{
			memset(sales, 0, sizeof(sales));
		}
	};
	std::map<DWORD, TPlayerBotClearKind> s_mapPlayerBotClear;

	// The counters' asks of this ledger pass (AddPlayerBotOfflineLedger): units and their summed price, the cheapest.
	struct TPlayerBotClearAsk
	{
		unsigned long long units, yang;
		DWORD minUnit;
		TPlayerBotClearAsk() : units(0), yang(0), minUnit(0) {}
	};
	std::map<DWORD, TPlayerBotClearAsk> s_mapPlayerBotClearAsks;

	struct TPlayerBotClearCounters
	{
		unsigned int started, stepped, held, relaxed, released, capped;
		TPlayerBotClearCounters() : started(0), stepped(0), held(0), relaxed(0), released(0), capped(0) {}
	};
	TPlayerBotClearCounters s_kPlayerBotClearCounters;

	void ResetPlayerBotClearingAsks()
	{
		s_mapPlayerBotClearAsks.clear();
	}

	void NotePlayerBotClearingAsk(DWORD vnum, DWORD count, long long totalYang)
	{
		if (!GetPlayerBotClearingConfig().on || count == 0 || totalYang <= 0)
			return;
		if (s_mapPlayerBotClearAsks.size() >= PLAYERBOT_CLEAR_MAX_KINDS &&
				s_mapPlayerBotClearAsks.find(vnum) == s_mapPlayerBotClearAsks.end())
			return;
		TPlayerBotClearAsk& a = s_mapPlayerBotClearAsks[vnum];
		a.units += count;
		a.yang += (unsigned long long)totalYang;
		const DWORD unit = (DWORD)std::min<long long>(0xFFFFFFFFLL, totalYang / (long long)count);
		if (a.minUnit == 0 || unit < a.minUnit)
			a.minUnit = unit;
	}

	DWORD GetPlayerBotClearingFloorUnit(DWORD vnum)
	{
		// What the merchant pays for one (the engine's sell arithmetic, GetPlayerBotNpcSellUnitPrice): a floor, never an
		// anchor - nobody sells to a counter for less than the merchant gives.
		DWORD npc = 0;
		if (const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum))
			if (!IS_SET(proto->dwAntiFlags, ITEM_ANTIFLAG_SELL) && !IS_SET(proto->dwFlags, ITEM_FLAG_COUNT_PER_1GOLD))
			{
				npc = proto->dwShopBuyPrice / 5;
				npc -= npc * 3 / 100;
			}
		return std::max(GetPlayerBotClearingConfig().minUnit, npc);
	}

	// The clearing ask of a kind per unit, or 0 when the kind is not being cleared.
	DWORD GetPlayerBotClearingUnit(DWORD vnum)
	{
		if (!GetPlayerBotClearingConfig().on)
			return 0;
		std::map<DWORD, TPlayerBotClearKind>::const_iterator it = s_mapPlayerBotClear.find(vnum);
		return it == s_mapPlayerBotClear.end() ? 0 : it->second.clearUnit;
	}

	// MT2009_PLUS_BOT_LADA_V1 (tiers; the owner, 8 November 2026: "tylko gdy jest duzo przedmiotu i slabo sie sprzedaje,
	// cena spada - i nie calego rynku: najtansze 10% o 5%, kolejne 10% o 3%, reszta zostaje"): while the bots' counters
	// are "lady" (playerbot_lada.h, event flag m2_bot_lada_price_off not set) the clearing above no longer caps every ask
	// of a glutted kind. Its detection (overstock and not disappearing) and its ask, stepping down while nothing sells and
	// relaxing as the stock falls, stay; they price only the cheap tail of the kind's listings - the line ids of
	// s_mapPlayerBotLadaTier (950 permille: the cheapest 10% of the kind's units on the stands, 970: the next 10%; ranked
	// by the unit price, every stand of the shop channel, a person's lines counted, only bots' edited), which the lada's
	// tier pass recomputes every few minutes. A tier line asks min(ordinary, clearing ask) x its permille, never under
	// what the merchant pays (BotOfflineRepriceTarget); every other line asks what it would without the glut. When the
	// cheap lines sell, the next ones are the tail and the stock that is left asks the ordinary price.
	bool s_bPlayerBotLadaTiers = false;			// refreshed each second by ManagePlayerBotLadaCore
	bool s_bPlayerBotLadaScan = false;			// the lada's bag scan: no "plenty" hold-back (ScorePlayerBotShopStock)
	std::unordered_map<DWORD, WORD> s_mapPlayerBotLadaTier;	// line id -> permille (950 / 970)
	unsigned int s_uPlayerBotLadaTierPriced = 0;	// lines priced by their tier since the last census

	int GetPlayerBotLadaTierPermille(DWORD lineId)
	{
		if (!s_bPlayerBotLadaTiers || !lineId)
			return 0;
		std::unordered_map<DWORD, WORD>::const_iterator it = s_mapPlayerBotLadaTier.find(lineId);
		return it == s_mapPlayerBotLadaTier.end() ? 0 : (int)it->second;
	}

	// MT2009_PLUS_BOT_LADA_TIER_XCH_V1 (the owner, 8 November 2026: why do the new lines listed from channel 2 start at
	// the ordinary price?): the glut's kinds and their clearing ask, the same on every core of every channel - the
	// clearing's state (sales windows, steps) lives on the shop channel's cores and differs between them, so one of them
	// (the writer, playerbot_lada.h IsPlayerBotLadaTierWriter: the core hosting the map of the shop channel's bot stand of
	// the lowest owner pid) publishes vnum -> clearing ask to player.playerbot_lada_tier at its tier pass and every other
	// core reads it at its own. Every core then ranks the same lines (its full copy of every shop) into the same
	// s_mapPlayerBotLadaTier, prices a new line of a glutted kind by where it falls in that ranking
	// (GetPlayerBotLadaNewLineTier), and edits only the lines of the stands it hosts, as before.
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotLadaTierClear;	// vnum -> clearing ask per unit (the tiers' input)

	DWORD GetPlayerBotLadaTierClearUnit(DWORD vnum)
	{
		std::unordered_map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotLadaTierClear.find(vnum);
		return it == s_mapPlayerBotLadaTierClear.end() ? 0 : it->second;
	}

	// A tier's price of a line of `count` units that asks `asking` in all: min(ordinary, the clearing ask) x its
	// permille, never under what the merchant pays, never over the ordinary ask (BotOfflineRepriceTarget and the lada's
	// new line alike).
	long long GetPlayerBotLadaTierPrice(DWORD vnum, long long count, long long asking, int tier)
	{
		count = std::max<long long>(1, count);
		long long anchor = asking;
		const DWORD clearUnit = GetPlayerBotLadaTierClearUnit(vnum);
		if (clearUnit > 0)
			anchor = std::min(anchor, (long long)clearUnit * count);
		const long long merchant = (long long)GetPlayerBotClearingFloorUnit(vnum) * count;
		return std::min(std::max(1LL, asking), std::max(std::max(1LL, merchant), anchor * tier / 1000));
	}

	// The ranking's curve of a glutted kind (built by the tier pass): the unit prices (milli-yang) of its lines in order
	// and the units up to and including each, so a new line finds its place without a walk.
	struct TPlayerBotLadaTierCurve
	{
		std::vector<unsigned long long> unitMilli;
		std::vector<unsigned long long> unitsTo;
		unsigned long long units = 0;
		unsigned long long added = 0;	// units of new lines listed into a tier since the pass
	};
	std::unordered_map<DWORD, TPlayerBotLadaTierCurve> s_mapPlayerBotLadaTierCurve;
	unsigned int s_uPlayerBotLadaNewLooked = 0;	// new lines of a glutted kind looked at since the last census

	// The tier a new line of a glutted kind would rank into: the units of the kind's lines that ask no more a unit
	// (ties go before it, the ranking's id order), and the tier lines listed since the pass, against every unit with it.
	int GetPlayerBotLadaNewLineTier(DWORD vnum, unsigned long long unitMilli, DWORD count)
	{
		if (!s_bPlayerBotLadaTiers || GetPlayerBotLadaTierClearUnit(vnum) == 0 || count == 0)
			return 0;
		++s_uPlayerBotLadaNewLooked;
		std::unordered_map<DWORD, TPlayerBotLadaTierCurve>::const_iterator it = s_mapPlayerBotLadaTierCurve.find(vnum);
		unsigned long long before = 0, units = 0;
		if (it != s_mapPlayerBotLadaTierCurve.end())
		{
			const TPlayerBotLadaTierCurve& c = it->second;
			const size_t at = std::upper_bound(c.unitMilli.begin(), c.unitMilli.end(), unitMilli) - c.unitMilli.begin();
			before = (at > 0 ? c.unitsTo[at - 1] : 0ULL) + c.added;
			units = c.units + c.added;
		}
		const unsigned long long share = before * 1000ULL / std::max<unsigned long long>(1ULL, units + count);
		if (share >= 200)
			return 0;
		return share < 100 ? 950 : 970;
	}

	// A new line went up into a tier: the next new lines of the kind rank behind it until the next pass.
	void NotePlayerBotLadaNewTierUnits(DWORD vnum, DWORD count)
	{
		s_mapPlayerBotLadaTierCurve[vnum].added += count;
	}

	// The clearing ask that caps every ask and floor of a kind (GetPlayerBotShopAskingPriceRaw, GetPlayerBotListingFloor):
	// none while the tiers price the glut instead.
	DWORD GetPlayerBotClearingCapUnit(DWORD vnum)
	{
		return s_bPlayerBotLadaTiers ? 0 : GetPlayerBotClearingUnit(vnum);
	}

	// An offline line of a clearing kind that asks more than the clearing ask and a margin: what the reprice looks at
	// first.
	bool IsPlayerBotClearingOverpriced(DWORD vnum, DWORD count, long long totalYang)
	{
		if (s_bPlayerBotLadaTiers)	// MT2009_PLUS_BOT_LADA_V1: the tier pass edits the tail itself
			return false;
		const DWORD unit = GetPlayerBotClearingUnit(vnum);
		if (unit == 0 || count == 0)
			return false;
		return totalYang > 0 && (unsigned long long)totalYang * 100ULL >
				(unsigned long long)unit * (unsigned long long)count * 115ULL;
	}

	// The sales window rolled on to the hour `dwNow` falls in: the buckets of the hours passed since are emptied.
	void RollPlayerBotClearSales(TPlayerBotClearKind& k, DWORD dwNow)
	{
		const DWORD hour = (dwNow - k.firstSeen) / 3600000U;
		if (hour <= k.bucketHour)
			return;
		if (hour - k.bucketHour >= (DWORD)PLAYERBOT_CLEAR_SALE_BUCKETS)
			memset(k.sales, 0, sizeof(k.sales));
		else
			while (k.bucketHour < hour)
				k.sales[++k.bucketHour % PLAYERBOT_CLEAR_SALE_BUCKETS] = 0;
		k.bucketHour = hour;
	}

	DWORD SumPlayerBotClearSales(const TPlayerBotClearKind& k)
	{
		DWORD sum = 0;
		for (int i = 0; i < PLAYERBOT_CLEAR_SALE_BUCKETS; ++i)
			sum += k.sales[i];
		return sum;
	}

	// The window's sales hours: what has been watched of it, one at least.
	DWORD GetPlayerBotClearSaleHours(const TPlayerBotClearKind& k, DWORD dwNow)
	{
		const DWORD hours = (dwNow - k.firstSeen) / 3600000U + 1U;
		return std::min<DWORD>(hours, PLAYERBOT_CLEAR_SALE_BUCKETS);
	}

	// Once a ledger pass, after the counts (RefreshPlayerBotMarketLedger).
	void UpdatePlayerBotMarketClearing(DWORD dwNow, bool report)
	{
		const TPlayerBotClearingConfig& c = GetPlayerBotClearingConfig();
		std::map<uint32_t, uint64_t> sold;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		sold.swap(playerbot_offline::soldUnitsByVnum);
#endif
		if (!c.on || g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
		{
			s_mapPlayerBotClear.clear();
			return;
		}
		// Watch every clearing kind on the counters or sold.
		for (TPlayerBotMarketLedger::const_iterator e = s_mapMarketLedger.begin(); e != s_mapMarketLedger.end(); ++e)
			if (e->second.dwSupplyUnits > 0 && s_mapPlayerBotClear.find(e->first) == s_mapPlayerBotClear.end() &&
					s_mapPlayerBotClear.size() < PLAYERBOT_CLEAR_MAX_KINDS && IsPlayerBotClearingGoods(e->first))
				s_mapPlayerBotClear[e->first].firstSeen = dwNow;
		for (std::map<uint32_t, uint64_t>::const_iterator s = sold.begin(); s != sold.end(); ++s)
		{
			std::map<DWORD, TPlayerBotClearKind>::iterator it = s_mapPlayerBotClear.find(s->first);
			if (it == s_mapPlayerBotClear.end())
			{
				if (s_mapPlayerBotClear.size() >= PLAYERBOT_CLEAR_MAX_KINDS || !IsPlayerBotClearingGoods(s->first))
					continue;
				it = s_mapPlayerBotClear.insert(std::make_pair((DWORD)s->first, TPlayerBotClearKind())).first;
				it->second.firstSeen = dwNow;
			}
			const DWORD units = (DWORD)std::min<uint64_t>(s->second, 0x7FFFFFFFULL);
			TPlayerBotClearKind& k = it->second;
			RollPlayerBotClearSales(k, dwNow);
			k.sales[k.bucketHour % PLAYERBOT_CLEAR_SALE_BUCKETS] += units;
			k.soldSinceStep += units;
		}

		const DWORD wallet = GetPlayerBotMarketMedianWallet();
		for (std::map<DWORD, TPlayerBotClearKind>::iterator it = s_mapPlayerBotClear.begin(); it != s_mapPlayerBotClear.end(); )
		{
			TPlayerBotClearKind& k = it->second;
			const DWORD vnum = it->first;
			// The sales window rolls on with the clock, sold or not.
			RollPlayerBotClearSales(k, dwNow);
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
			const DWORD supply = entry ? entry->dwSupplyUnits : 0;
			const DWORD demand = entry ? entry->dwDemandBots : 0;
			const DWORD soldWindow = SumPlayerBotClearSales(k);
			const DWORD hours = GetPlayerBotClearSaleHours(k, dwNow);
			// Units the market takes in COVER_HOURS: the sales rate over the window, and the bots short of it.
			const unsigned long long takes = (unsigned long long)soldWindow * c.coverHours / hours +
					(unsigned long long)demand * c.perBuyer;
			const bool overstock = supply >= c.minUnits && (unsigned long long)supply > takes;
			const bool released = supply < c.minUnits / 2 || (unsigned long long)supply * 2ULL <= takes;
			if (k.clearUnit == 0)
			{
				// A kind nobody lists nor buys any more is forgotten (a day of nothing).
				if (supply == 0 && soldWindow == 0 && dwNow - k.firstSeen > 24U * 3600000U)
				{
					s_mapPlayerBotClear.erase(it++);
					continue;
				}
				if (overstock && dwNow - k.firstSeen >= c.warmupMs)
				{
					std::map<DWORD, TPlayerBotClearAsk>::const_iterator a = s_mapPlayerBotClearAsks.find(vnum);
					const DWORD mean = a != s_mapPlayerBotClearAsks.end() && a->second.units > 0
							? (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, a->second.yang / a->second.units) : 0;
					const DWORD walletCap = wallet > 0
							? (DWORD)std::max<unsigned long long>(1ULL, (unsigned long long)wallet * c.walletPermille / 1000ULL) : 0;
					DWORD start = mean;
					if (walletCap > 0 && (start == 0 || walletCap < start))
						start = walletCap;
					const DWORD floor = GetPlayerBotClearingFloorUnit(vnum);
					if (start > floor)
					{
						k.clearUnit = k.startUnit = start;
						k.stepAt = dwNow;
						k.supplyAtStep = supply;
						k.soldSinceStep = 0;
						k.steps = 0;
						++s_kPlayerBotClearCounters.started;
						PlayerBotLogThrottled("market_clear_start", dwNow,
								"PLAYERBOT_MARKET_CLEAR: start vnum=%u supply=%u sold_%uh=%u bots_short=%u mean_ask=%u min_ask=%u wallet=%u unit=%u floor=%u",
								vnum, supply, hours, soldWindow, demand, mean,
								a != s_mapPlayerBotClearAsks.end() ? a->second.minUnit : 0U, wallet, start, floor);
					}
				}
				++it;
				continue;
			}
			if (dwNow - k.stepAt < c.stepMs)
			{
				++it;
				continue;
			}
			const DWORD was = k.clearUnit;
			const DWORD fell = k.supplyAtStep > supply ? k.supplyAtStep - supply : 0;
			const unsigned long long base = std::max<DWORD>(1, std::max(supply, k.supplyAtStep));
			const bool disappearing = (unsigned long long)k.soldSinceStep * 1000ULL >= base * c.sellPermille ||
					(unsigned long long)fell * 1000ULL >= base * c.sellPermille;
			const DWORD floor = GetPlayerBotClearingFloorUnit(vnum);
			if (released)
			{
				k.clearUnit = (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL,
						(unsigned long long)k.clearUnit * (100ULL + c.relaxPct) / 100ULL + 1ULL);
				++s_kPlayerBotClearCounters.relaxed;
				// Let go only where the ordinary pricing asks (the step limiter's anchor, which the clearing never
				// moves), so the release is the same slow climb and not a jump back to the sheet.
				const DWORD ordinary = std::max(k.startUnit, GetPlayerBotLastAsk(vnum, 0, dwNow));
				if (k.clearUnit >= ordinary)
				{
					++s_kPlayerBotClearCounters.released;
					PlayerBotLogThrottled("market_clear_release", dwNow,
							"PLAYERBOT_MARKET_CLEAR: release vnum=%u supply=%u sold_%uh=%u bots_short=%u unit=%u start=%u steps=%d",
							vnum, supply, hours, soldWindow, demand, was, k.startUnit, k.steps);
					k.clearUnit = k.startUnit = 0;
					k.steps = 0;
				}
			}
			else if (overstock && !disappearing && k.clearUnit > floor)
			{
				k.clearUnit = std::max<DWORD>(floor, (DWORD)((unsigned long long)k.clearUnit * (100ULL - c.stepPct) / 100ULL));
				++k.steps;
				++s_kPlayerBotClearCounters.stepped;
				PlayerBotLogThrottled("market_clear_step", dwNow,
						"PLAYERBOT_MARKET_CLEAR: step vnum=%u supply=%u was_supply=%u sold_since=%u sold_%uh=%u bots_short=%u unit=%u was=%u floor=%u steps=%d",
						vnum, supply, k.supplyAtStep, k.soldSinceStep, hours, soldWindow, demand, k.clearUnit, was, floor, k.steps);
			}
			else
				++s_kPlayerBotClearCounters.held;
			k.stepAt = dwNow;
			k.supplyAtStep = supply;
			k.soldSinceStep = 0;
			++it;
		}

		if (!report)
			return;
		// The census: the clearing kinds with the most stock, and what the pass did since the last report.
		std::vector<std::pair<DWORD, DWORD> > ranked;	// supply, vnum
		unsigned int active = 0;
		for (std::map<DWORD, TPlayerBotClearKind>::const_iterator it = s_mapPlayerBotClear.begin(); it != s_mapPlayerBotClear.end(); ++it)
			if (it->second.clearUnit != 0)
			{
				++active;
				const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(it->first);
				ranked.push_back(std::make_pair(entry ? entry->dwSupplyUnits : 0U, it->first));
			}
		std::sort(ranked.rbegin(), ranked.rend());
		std::string top;
		for (size_t i = 0; i < ranked.size() && i < 8; ++i)
		{
			const TPlayerBotClearKind& k = s_mapPlayerBotClear[ranked[i].second];
			std::map<DWORD, TPlayerBotClearAsk>::const_iterator a = s_mapPlayerBotClearAsks.find(ranked[i].second);
			const DWORD mean = a != s_mapPlayerBotClearAsks.end() && a->second.units > 0
					? (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, a->second.yang / a->second.units) : 0;
			char buf[160];
			snprintf(buf, sizeof(buf), " %u(S=%u sold%uh=%u unit=%u start=%u steps=%d ask=%u/%u)", ranked[i].second,
					ranked[i].first, GetPlayerBotClearSaleHours(k, dwNow), SumPlayerBotClearSales(k), k.clearUnit,
					k.startUnit, k.steps, mean, a != s_mapPlayerBotClearAsks.end() ? a->second.minUnit : 0U);
			top += buf;
		}
		sys_log(0, "PLAYERBOT_MARKET_CLEAR: census watched=%u active=%u started=%u stepped=%u held=%u relaxed=%u released=%u capped_prices=%u wallet=%u top:%s",
				(unsigned int)s_mapPlayerBotClear.size(), active, s_kPlayerBotClearCounters.started,
				s_kPlayerBotClearCounters.stepped, s_kPlayerBotClearCounters.held, s_kPlayerBotClearCounters.relaxed,
				s_kPlayerBotClearCounters.released, s_kPlayerBotClearCounters.capped, wallet, top.c_str());
		s_kPlayerBotClearCounters = TPlayerBotClearCounters();
	}
}

#endif
