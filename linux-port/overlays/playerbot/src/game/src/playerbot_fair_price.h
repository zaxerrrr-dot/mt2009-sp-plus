#ifndef __INC_METIN2_PLAYERBOT_FAIR_PRICE_H__
#define __INC_METIN2_PLAYERBOT_FAIR_PRICE_H__

#include <cmath>
#include <deque>
#include <unordered_map>
#include <vector>

// MT2009_PLUS_BOT_FAIR_PRICE_V1 - the "fair price" market (the owner, 10 November 2026: "rynek, ktory sam sie reguluje
// podaza i sprzedaza, jak na prawdziwym serwerze"; the Polish README: docs/RYNEK_UCZCIWA_CENA.md). It replaces, while
// the event flag m2_bot_fairprice_off is not set, the supply clearing (playerbot_market_clearing.h), the lada's glut
// tiers (5 % / 3 % off the cheapest fifth) and the 90 % market floor's repair (playerbot_lada.h) for the goods it
// prices: the stackable goods of the clearing (IsPlayerBotClearingGoods - materials, ores, stones, scrolls...) and the
// owner's roasted fish; never gear, books, soul or dragon stones, Cors, coupons, runes, rank fruit, marbles.
//
// 1. The fair price of a kind (vnum) = its reference x its ratio.
//    * The reference: the owner's own number (the roasted fish table, 'O'), else the sheet through the yang-rate curve
//      and the inflation as every price before ('S' - the asking price's prior, GetPlayerBotShopAskingPriceRaw), else
//      the merchant's / wallet prior ('P'), replaced by what the real sales paid once there are enough of them ('M':
//      the trimmed mean of the accepted sales, moved at most 10 % a day).
//    * The ratio lives in [m2_bot_fair_min_pct, m2_bot_fair_max_pct] (60..200 % of the reference; a pin or the
//      kind's own bounds from the panel win) and is moved every m2_bot_fair_step_min (15) minutes by the market:
//        stock   = units on every stand (bots and players, both channels), rate = units sold an hour over the window
//                  (m2_bot_fair_window_h, 48 h; every sale of every counter - playerbot_offline::fairSales; a sale at
//                  under 35 % or over 300 % of the fair price is an outlier, ignored), rate6 = the same over 6 h;
//        x_cover = log(stock / rate / 24 h / m2_bot_fair_cover_days) / log(8), in [-1, 1] - few days of stock (it
//                  sells out) pushes up, many pushes down, the down side x m2_bot_fair_stock_weight (30 %): the lada
//                  holds everything a bot has by design, so the stock alone never crashes a price; nothing sold in
//                  the window with stock up: +1 (x the weight);
//        x_price = -(share of the units of the last 6 h sold at or above the fair price / 0.5) x m2_bot_fair_price_weight
//                  (50 %): the cheap offers cleared and the buyers pay the fair price or more -> up;
//        x_trend = -log((rate6 + a) / (rate + a)) / log(4) x m2_bot_fair_trend_weight (30 %): sales speeding up -> up;
//        x = x_cover + x_price + x_trend in [-1, 1], a dead band of 0.08;
//        confidence = sale events / (sale events + m2_bot_fair_conf_sales (8)) - a rare kind barely moves; a kind with
//                  stock and no sale at all: 0.3 x min(1, stock / 50);
//        a move an hour = x > 0 ? -m2_bot_fair_down_pct (10) % x x : +m2_bot_fair_up_pct (15) % x |x|, times the
//                  confidence, applied for the time since the last step; no stock and no sales: back to 1.0 by 2 % an
//                  hour.
//    One writer core (the lada's tier writer, IsPlayerBotLadaTierWriter) computes it and writes
//    player.playerbot_market_fair (and the hourly player.playerbot_market_fair_hist); every other core reads the rows
//    every 5 minutes. A core prices with its own sheet reference ('S' / 'O': the same inflation everywhere) and the
//    writer's ratio, or the writer's reference for 'P' / 'M'.
// 2. The sellers (the owner's final rule, 10 November 2026): a bot lists ALL its stock of a kind at once, at ONE unit
//    price - fair x its multiplier. Every bot has, per kind (from its pid and the vnum), its personality and its own
//    band inside [m2_bot_fair_list_min_pct, m2_bot_fair_list_max_pct] (60..200 % of the fair price):
//        handlarze (30 %): floor 60-70 %, ceiling 110-140 %, start 90-100 %;
//        normalni  (50 %): floor 70-85 %, ceiling 120-170 %, start 97-108 %;
//        cierpliwi (20 %): floor 90-110 %, ceiling 140-200 %, start 105-120 %;
//    so the market always shows a ladder of prices, cheap to dear. Every m2_bot_fair_check_min..max (30..60, drawn per
//    bot and kind) minutes the stand's host core looks at that bot's kind: sold since the last look -> the multiplier
//    goes up m2_bot_fair_step_lo..hi (3..5) %, nothing sold -> down as much; never past its own floor or ceiling. Then
//    every line of that kind on the stand is edited to the one price (playerbot_lada.h, PumpPlayerBotFairEdits,
//    m2_bot_fair_edits_s a second). Nothing reacts to the cheapest offer and nothing is withdrawn. A line asking under
//    its bot's floor (the old crashed lines) or off the bot's price is edited by the same sweep - the repair.
// 3. The buyers: unchanged - the cheapest first; every sale feeds the window above.
//
// Log: "PLAYERBOT_FAIR:" - config, census (every 10 minutes, every core), kind (the writer: the 12 kinds of the most
// stock - reference, fair, ratio, bounds, stock, sellers, sales, cover, x, confidence, the spread of the offers min /
// p25 / median / p75 / max). The panel: "Gospodarka -> Rynek - uczciwa cena" (seban-panel rynek.py).
//
// MT2009_PLUS_BOT_FAIR_PRICE_V1 follow-up hook: a "market clearing" module was discussed and dropped by the owner
// (nothing is withdrawn); the per-kind numbers it would have needed are TPlayerBotFairKind / TPlayerBotFairBook.

namespace
{
	bool IsPlayerBotFairPriceOn();	// both branches below: playerbot_market_clearing.h asks it

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
	DWORD GetPlayerBotShopAskingPrice(LPITEM item);	// playerbot_town.h

	// ------------------------------------------------------------------------------------------------ config
	struct TPlayerBotFairCfg
	{
		bool on = true;
		int stepMin = 15, downPct = 10, upPct = 15, minPct = 60, maxPct = 200, coverDays = 7, stockW = 30, priceW = 50,
			trendW = 30, confSales = 8, windowH = 48, checkMin = 30, checkMax = 60, stepLo = 3, stepHi = 5,
			listMinPct = 60, listMaxPct = 200, editsPerS = 20, histDays = 14;
		bool operator!=(const TPlayerBotFairCfg& o) const
		{
			return on != o.on || stepMin != o.stepMin || downPct != o.downPct || upPct != o.upPct || minPct != o.minPct ||
					maxPct != o.maxPct || coverDays != o.coverDays || stockW != o.stockW || priceW != o.priceW ||
					trendW != o.trendW || confSales != o.confSales || windowH != o.windowH || checkMin != o.checkMin ||
					checkMax != o.checkMax || stepLo != o.stepLo || stepHi != o.stepHi || listMinPct != o.listMinPct ||
					listMaxPct != o.listMaxPct || editsPerS != o.editsPerS || histDays != o.histDays;
		}
	};
	TPlayerBotFairCfg s_kPlayerBotFairCfg;
	const int PLAYERBOT_FAIR_HOURS = 96;	// the sales ring: the window can be up to this many hours

	// The event flags (player.quest rows of pid 0, the panel's "Rynek" page; 0 = the default), read once a second.
	const TPlayerBotFairCfg& GetPlayerBotFairCfg()
	{
		static DWORD s_dwAt = 0;
		static bool s_bLogged = false;
		const DWORD now = get_dword_time();
		if (s_dwAt != 0 && now - s_dwAt < 1000)
			return s_kPlayerBotFairCfg;
		s_dwAt = now ? now : 1;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		TPlayerBotFairCfg& c = s_kPlayerBotFairCfg;
		const TPlayerBotFairCfg was = c;
		auto value = [&q](const char* flag, int def, int lo, int hi) {
			const int v = q.GetEventFlag(flag);
			return v == 0 ? def : std::max(lo, std::min(hi, v));
		};
		auto weight = [&q](const char* flag, int def) {	// a weight: 0 the default, under 0 none
			const int v = q.GetEventFlag(flag);
			return v == 0 ? def : (v < 0 ? 0 : std::min(100, v));
		};
		c.on = q.GetEventFlag("m2_bot_fairprice_off") == 0;
		c.stepMin = value("m2_bot_fair_step_min", 15, 5, 120);
		c.downPct = value("m2_bot_fair_down_pct", 10, 1, 50);
		c.upPct = value("m2_bot_fair_up_pct", 15, 1, 50);
		c.minPct = value("m2_bot_fair_min_pct", 60, 10, 100);
		c.maxPct = std::max(c.minPct, value("m2_bot_fair_max_pct", 200, 100, 1000));
		c.coverDays = value("m2_bot_fair_cover_days", 7, 1, 90);
		c.stockW = weight("m2_bot_fair_stock_weight", 30);
		c.priceW = weight("m2_bot_fair_price_weight", 50);
		c.trendW = weight("m2_bot_fair_trend_weight", 30);
		c.confSales = value("m2_bot_fair_conf_sales", 8, 1, 1000);
		c.windowH = value("m2_bot_fair_window_h", 48, 6, PLAYERBOT_FAIR_HOURS);
		c.checkMin = value("m2_bot_fair_check_min", 30, 5, 1440);
		c.checkMax = std::max(c.checkMin, value("m2_bot_fair_check_max", 60, 5, 1440));
		c.stepLo = value("m2_bot_fair_step_lo", 3, 1, 50);
		c.stepHi = std::max(c.stepLo, value("m2_bot_fair_step_hi", 5, 1, 50));
		c.listMinPct = value("m2_bot_fair_list_min_pct", 60, 10, 100);
		c.listMaxPct = std::max(c.listMinPct, value("m2_bot_fair_list_max_pct", 200, 100, 1000));
		c.editsPerS = value("m2_bot_fair_edits_s", 20, 1, 200);
		c.histDays = value("m2_bot_fair_hist_days", 14, 1, 90);
		if (!s_bLogged || was != c)
		{
			s_bLogged = true;
			sys_log(0, "PLAYERBOT_FAIR: config on=%d step_min=%d down_pct=%d up_pct=%d bounds_pct=%d..%d cover_days=%d "
					"stock_w=%d price_w=%d trend_w=%d conf_sales=%d window_h=%d check_min=%d..%d step_pct=%d..%d "
					"list_pct=%d..%d edits_s=%d hist_days=%d",
					c.on ? 1 : 0, c.stepMin, c.downPct, c.upPct, c.minPct, c.maxPct, c.coverDays, c.stockW, c.priceW,
					c.trendW, c.confSales, c.windowH, c.checkMin, c.checkMax, c.stepLo, c.stepHi, c.listMinPct,
					c.listMaxPct, c.editsPerS, c.histDays);
		}
		return c;
	}

	bool IsPlayerBotFairPriceOn()
	{
		return GetPlayerBotFairCfg().on;
	}

	// ------------------------------------------------------------------------------------------------ the goods
	std::unordered_map<DWORD, bool> s_mapPlayerBotFairGoodsCache;

	bool IsPlayerBotFairGoodsStatic(DWORD vnum)
	{
		// The goods of the clearing (stackable goods and refine materials, no gear, costume, book, Dragon Stone, Cor,
		// coupon, belt, sash, talisman, guild material), less the kinds the asking price prices on their own curve
		// before the sheet's prior: runes, rank fruit, Delikatne Sukno, the Forgetting Scroll (by its skill), the pet
		// transporter (55002), soul stones and marbles.
		if (!IsPlayerBotClearingGoods(vnum) || IsPlayerBotRuneVnum(vnum) || IsPlayerBotRankFruit(vnum) ||
				vnum == PLAYERBOT_SASH_CLOTH_VNUM || vnum == PLAYERBOT_SKILL_FORGET_SCROLL_VNUM || vnum == 55002)
			return false;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto && proto->bType != ITEM_METIN && proto->bType != ITEM_POLYMORPH;
	}

	bool IsPlayerBotFairGoods(DWORD vnum)
	{
		if (vnum == 0)
			return false;
		if (GetPlayerBotRoastedFishOwnerPrice(vnum) != 0)
			return true;
		std::unordered_map<DWORD, bool>::const_iterator it = s_mapPlayerBotFairGoodsCache.find(vnum);
		if (it != s_mapPlayerBotFairGoodsCache.end())
			return it->second;
		if (s_mapPlayerBotFairGoodsCache.size() > 65536)
			s_mapPlayerBotFairGoodsCache.clear();
		const bool goods = IsPlayerBotFairGoodsStatic(vnum);
		s_mapPlayerBotFairGoodsCache.emplace(vnum, goods);
		return goods;
	}

	// ------------------------------------------------------------------------------------------------ the shared rows
	struct TPlayerBotFairRow
	{
		DWORD ref = 0, ratioPm = 1000, minPm = 0, maxPm = 0, pin = 0;
		char src = 'S';
	};
	std::unordered_map<DWORD, TPlayerBotFairRow> s_mapPlayerBotFairShared;	// vnum -> the writer's row

	// The reference a unit this core's asking price worked out (its prior), and where it came from.
	struct TPlayerBotFairRef
	{
		DWORD unit = 0, at = 0;	// at: global seconds
		char src = 'S';
	};
	std::unordered_map<DWORD, TPlayerBotFairRef> s_mapPlayerBotFairLocalRef;

	struct TPlayerBotFairCensus
	{
		unsigned int salesIn = 0, salesOwner = 0, outliers = 0, probes = 0, checks = 0, raised = 0, lowered = 0,
				atFloor = 0, atCeil = 0, editsQueued = 0, editsDone = 0, editsSkipped = 0, repaired = 0, steps = 0,
				rowsRead = 0, readFailed = 0, asked = 0, listed = 0;
		unsigned long long repairedYang = 0;
	};
	TPlayerBotFairCensus s_kPlayerBotFairCensus;

	// The reference of a kind on this core: the local sheet / owner reference, the writer's for a merchant-priced or a
	// sales-priced kind (a wallet prior differs between cores).
	DWORD GetPlayerBotFairRefFor(DWORD vnum, DWORD localRef, char localSrc, const TPlayerBotFairRow* row)
	{
		DWORD ref = localRef;
		if (row && row->ref && (ref == 0 || (localSrc != 'S' && localSrc != 'O') || row->src == 'M'))
			ref = row->ref;
		return ref;
	}

	// The fair price a unit, 0 when unknown.
	DWORD GetPlayerBotFairUnitFrom(DWORD vnum, DWORD localRef, char localSrc)
	{
		std::unordered_map<DWORD, TPlayerBotFairRow>::const_iterator it = s_mapPlayerBotFairShared.find(vnum);
		const TPlayerBotFairRow* row = it == s_mapPlayerBotFairShared.end() ? NULL : &it->second;
		if (row && row->pin)
			return row->pin;
		const DWORD ref = GetPlayerBotFairRefFor(vnum, localRef, localSrc, row);
		if (ref == 0)
			return 0;
		const TPlayerBotFairCfg& c = GetPlayerBotFairCfg();
		const DWORD lo = row && row->minPm ? row->minPm : (DWORD)c.minPct * 10U;
		const DWORD hi = row && row->maxPm ? std::max(lo, row->maxPm) : std::max(lo, (DWORD)c.maxPct * 10U);
		const DWORD pm = std::max(lo, std::min(hi, row ? row->ratioPm : 1000U));
		return (DWORD)std::max<unsigned long long>(1ULL, std::min<unsigned long long>(0xFFFFFFFEULL,
				(unsigned long long)ref * pm / 1000ULL));
	}

	DWORD GetPlayerBotFairUnitByVnum(DWORD vnum)
	{
		std::unordered_map<DWORD, TPlayerBotFairRef>::const_iterator it = s_mapPlayerBotFairLocalRef.find(vnum);
		return it == s_mapPlayerBotFairLocalRef.end() ? GetPlayerBotFairUnitFrom(vnum, 0, 'P')
				: GetPlayerBotFairUnitFrom(vnum, it->second.unit, it->second.src);
	}

	// The asking price's hook (GetPlayerBotShopAskingPriceRaw, at its prior): the reference noted, the fair price a
	// unit back - 0 when the kind is not the fair market's (the old way then).
	DWORD PlayerBotFairAskUnit(DWORD vnum, DWORD prior, char src)
	{
		if (prior == 0 || !IsPlayerBotFairPriceOn() || !IsPlayerBotFairGoods(vnum))
			return 0;
		TPlayerBotFairRef& r = s_mapPlayerBotFairLocalRef[vnum];
		r.unit = prior;
		r.src = src;
		r.at = (DWORD)get_global_time();
		++s_kPlayerBotFairCensus.asked;
		return GetPlayerBotFairUnitFrom(vnum, prior, src);
	}

	// ------------------------------------------------------------------------------------------------ the books
	// Every core, every minute, from its full copy of every shop (any channel, a person's too).
	struct TPlayerBotFairBook
	{
		unsigned long long units = 0, yang = 0;
		DWORD lines = 0, sellers = 0;
		DWORD pMin = 0, p25 = 0, p50 = 0, p75 = 0, pMax = 0;	// the writer's spread of the unit prices
	};
	struct TPlayerBotFairOwnerBook
	{
		unsigned long long units = 0, yang = 0;
		DWORD lines = 0;
	};
	std::unordered_map<DWORD, TPlayerBotFairBook> s_mapPlayerBotFairBooks;
	std::unordered_map<unsigned long long, TPlayerBotFairOwnerBook> s_mapPlayerBotFairOwnerBooks;
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotFairLineOwner;	// line id -> owner (a sale's owner where the engine gives none)

	inline unsigned long long PlayerBotFairKey(DWORD owner, DWORD vnum)
	{
		return ((unsigned long long)owner << 32) | (unsigned long long)vnum;
	}

	DWORD GetPlayerBotFairStockUnits(DWORD vnum)
	{
		std::unordered_map<DWORD, TPlayerBotFairBook>::const_iterator it = s_mapPlayerBotFairBooks.find(vnum);
		return it == s_mapPlayerBotFairBooks.end() ? 0U : (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, it->second.units);
	}

	void ScanPlayerBotFairMarket(bool writer)
	{
		std::unordered_map<DWORD, TPlayerBotFairBook> books;
		std::unordered_map<unsigned long long, TPlayerBotFairOwnerBook> owners;
		std::unordered_map<DWORD, DWORD> lineOwner;
		std::unordered_map<DWORD, std::vector<std::pair<unsigned long long, DWORD> > > offers;	// writer: unit milli, units
		lineOwner.reserve(s_mapPlayerBotFairLineOwner.size() + 64);
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || shop->GetDuration() == 0)
				continue;
			const DWORD owner = shop->GetOwnerPID();
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || line->GetInfo().count == 0 || !IsPlayerBotFairGoods(line->GetInfo().vnum))
					continue;
				const long long yang = (long long)line->GetPrice().GetTotalYangAmount();
				if (yang <= 0)
					continue;
				const DWORD vnum = line->GetInfo().vnum;
				const DWORD count = (DWORD)line->GetInfo().count;
				TPlayerBotFairBook& b = books[vnum];
				b.units += count;
				b.yang += (unsigned long long)yang;
				++b.lines;
				TPlayerBotFairOwnerBook& o = owners[PlayerBotFairKey(owner, vnum)];
				if (o.lines == 0)
					++b.sellers;
				o.units += count;
				o.yang += (unsigned long long)yang;
				++o.lines;
				lineOwner[id] = owner;
				if (writer)
					offers[vnum].push_back(std::make_pair((unsigned long long)yang * 1000ULL / count, count));
			}
		}
		if (writer)
			for (auto& [vnum, list] : offers)
			{
				std::sort(list.begin(), list.end());
				TPlayerBotFairBook& b = books[vnum];
				const unsigned long long total = b.units;
				auto at = [&list, total](unsigned long long q) -> DWORD {
					const unsigned long long want = total * q / 100ULL;
					unsigned long long before = 0;
					for (const auto& e : list)
					{
						before += e.second;
						if (before > want)
							return (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, e.first / 1000ULL);
					}
					return list.empty() ? 0U : (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, list.back().first / 1000ULL);
				};
				b.pMin = list.empty() ? 0 : (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, list.front().first / 1000ULL);
				b.p25 = at(25);
				b.p50 = at(50);
				b.p75 = at(75);
				b.pMax = list.empty() ? 0 : (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, list.back().first / 1000ULL);
			}
		s_mapPlayerBotFairBooks.swap(books);
		s_mapPlayerBotFairOwnerBooks.swap(owners);
		s_mapPlayerBotFairLineOwner.swap(lineOwner);
	}

	// ------------------------------------------------------------------------------------------------ the sellers
	enum { PLAYERBOT_FAIR_TRADER = 0, PLAYERBOT_FAIR_NORMAL = 1, PLAYERBOT_FAIR_PATIENT = 2 };

	struct TPlayerBotFairBand
	{
		int kind = PLAYERBOT_FAIR_NORMAL;
		int floorPm = 800, ceilPm = 1200, startPm = 1000;	// per mille of the fair price
	};

	int GetPlayerBotFairPersonality(DWORD owner)
	{
		if (owner == 0)
			return PLAYERBOT_FAIR_NORMAL;
		const DWORD h = PlayerBotNavHash(owner ^ 0x46414952U) % 100U;
		return h < 30 ? PLAYERBOT_FAIR_TRADER : (h < 80 ? PLAYERBOT_FAIR_NORMAL : PLAYERBOT_FAIR_PATIENT);
	}

	// A bot's own floor, ceiling and start for a kind (deterministic from its pid and the vnum), inside the global
	// listing bounds: the market's ladder of prices.
	TPlayerBotFairBand GetPlayerBotFairBand(DWORD owner, DWORD vnum)
	{
		const TPlayerBotFairCfg& c = GetPlayerBotFairCfg();
		TPlayerBotFairBand b;
		b.kind = GetPlayerBotFairPersonality(owner);
		if (owner != 0)
		{
			const DWORD h1 = PlayerBotNavHash(owner * 2654435761U ^ vnum);
			const DWORD h2 = PlayerBotNavHash(h1 ^ 0x9E3779B9U);
			const DWORD h3 = PlayerBotNavHash(h2 ^ 0x7F4A7C15U);
			switch (b.kind)
			{
				case PLAYERBOT_FAIR_TRADER:
					b.floorPm = 600 + (int)(h1 % 101U);
					b.ceilPm = 1100 + (int)(h2 % 301U);
					b.startPm = 900 + (int)(h3 % 101U);
					break;
				case PLAYERBOT_FAIR_PATIENT:
					b.floorPm = 900 + (int)(h1 % 201U);
					b.ceilPm = 1400 + (int)(h2 % 601U);
					b.startPm = 1050 + (int)(h3 % 151U);
					break;
				default:
					b.floorPm = 700 + (int)(h1 % 151U);
					b.ceilPm = 1200 + (int)(h2 % 501U);
					b.startPm = 970 + (int)(h3 % 111U);
					break;
			}
		}
		const int lo = c.listMinPct * 10, hi = c.listMaxPct * 10;
		b.floorPm = std::max(lo, std::min(hi, b.floorPm));
		b.ceilPm = std::max(b.floorPm, std::min(hi, b.ceilPm));
		b.startPm = std::max(b.floorPm, std::min(b.ceilPm, b.startPm));
		return b;
	}

	// A bot's state for a kind. The multiplier is the stand's host core's (CheckPlayerBotFairSellers, playerbot_lada.h);
	// any other core reads it off the bot's lines (their mean unit / the fair price). The last sale is every core's.
	struct TPlayerBotFairSeller
	{
		double multPm = 0.0;	// 0: not set yet
		DWORD lastSale = 0, lastCheck = 0, nextCheck = 0, seq = 0, lastSeen = 0, soldSinceCheck = 0;	// global seconds
		bool hosted = false;
	};
	std::unordered_map<unsigned long long, TPlayerBotFairSeller> s_mapPlayerBotFairSellers;

	// The multiplier (per mille of the fair price) a bot asks for a kind now.
	double GetPlayerBotFairSellerMult(DWORD owner, DWORD vnum, DWORD fairUnit, const TPlayerBotFairBand& band)
	{
		if (owner != 0)
		{
			const unsigned long long key = PlayerBotFairKey(owner, vnum);
			std::unordered_map<unsigned long long, TPlayerBotFairSeller>::const_iterator s = s_mapPlayerBotFairSellers.find(key);
			if (s != s_mapPlayerBotFairSellers.end() && s->second.hosted && s->second.multPm > 0.0)
				return s->second.multPm;
			std::unordered_map<unsigned long long, TPlayerBotFairOwnerBook>::const_iterator o = s_mapPlayerBotFairOwnerBooks.find(key);
			if (o != s_mapPlayerBotFairOwnerBooks.end() && o->second.units > 0 && fairUnit > 0)
			{
				const double mean = (double)o->second.yang / (double)o->second.units;
				return std::max((double)band.floorPm, std::min((double)band.ceilPm, mean * 1000.0 / (double)fairUnit));
			}
		}
		return (double)band.startPm;
	}

	// What the merchant pays for one (the engine's sell arithmetic): nobody lists a unit for less.
	DWORD GetPlayerBotFairMerchantUnit(DWORD vnum)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto || IS_SET(proto->dwAntiFlags, ITEM_ANTIFLAG_SELL) || IS_SET(proto->dwFlags, ITEM_FLAG_COUNT_PER_1GOLD))
			return 0;
		DWORD npc = proto->dwShopBuyPrice / 5;
		npc -= npc * 3 / 100;
		return npc;
	}

	// What a bot asks a unit of a kind, 0 when the kind is not the fair market's here.
	DWORD GetPlayerBotFairSellerUnit(DWORD owner, DWORD vnum)
	{
		if (!IsPlayerBotFairPriceOn() || !IsPlayerBotFairGoods(vnum))
			return 0;
		const DWORD fair = GetPlayerBotFairUnitByVnum(vnum);
		if (fair == 0)
			return 0;
		const TPlayerBotFairBand band = GetPlayerBotFairBand(owner, vnum);
		const double mult = GetPlayerBotFairSellerMult(owner, vnum, fair, band);
		const unsigned long long unit = (unsigned long long)((double)fair * mult / 1000.0 + 0.5);
		return (DWORD)std::max<unsigned long long>(std::max<unsigned long long>(1ULL, GetPlayerBotFairMerchantUnit(vnum)),
				std::min<unsigned long long>(0xFFFFFFFEULL, unit));
	}

	// The least a bot's line of the kind asks a unit: its floor (and what the merchant pays).
	DWORD GetPlayerBotFairFloorUnit(DWORD owner, DWORD vnum)
	{
		if (!IsPlayerBotFairPriceOn() || !IsPlayerBotFairGoods(vnum))
			return 0;
		const DWORD fair = GetPlayerBotFairUnitByVnum(vnum);
		if (fair == 0)
			return 0;
		const TPlayerBotFairBand band = GetPlayerBotFairBand(owner, vnum);
		const unsigned long long unit = (unsigned long long)fair * (unsigned long long)band.floorPm / 1000ULL;
		return (DWORD)std::max<unsigned long long>(std::max<unsigned long long>(1ULL, GetPlayerBotFairMerchantUnit(vnum)),
				std::min<unsigned long long>(0xFFFFFFFEULL, unit));
	}

	// ------------------------------------------------------------------------------------------------ the sales
	// The writer's kind: the reference, the ratio, the sales by the hour and the last accepted sale prices.
	struct TPlayerBotFairSale
	{
		DWORD unit = 0, count = 0, hour = 0;
	};
	struct TPlayerBotFairKind
	{
		DWORD ref = 0, refM = 0, refMAt = 0, firstHour = 0, lastStepAt = 0, outliers = 0;
		char src = 'S';
		double ratio = 1.0, x = 0.0, conf = 0.0, rate = 0.0;
		DWORD hourStamp[PLAYERBOT_FAIR_HOURS];
		DWORD sold[PLAYERBOT_FAIR_HOURS];
		DWORD soldHi[PLAYERBOT_FAIR_HOURS];	// sold at or above the fair price
		WORD events[PLAYERBOT_FAIR_HOURS];
		std::deque<TPlayerBotFairSale> sales;	// the last PLAYERBOT_FAIR_SALES_KEPT accepted
		// the last step's numbers (the table, the census)
		DWORD soldW = 0, eventsW = 0, sold6 = 0, soldHi6 = 0, saleMean = 0, fairUnit = 0;
		double coverH = 0.0;
		TPlayerBotFairKind()
		{
			memset(hourStamp, 0, sizeof(hourStamp));
			memset(sold, 0, sizeof(sold));
			memset(soldHi, 0, sizeof(soldHi));
			memset(events, 0, sizeof(events));
		}
	};
	const size_t PLAYERBOT_FAIR_SALES_KEPT = 64;
	std::unordered_map<DWORD, TPlayerBotFairKind> s_mapPlayerBotFairKinds;
	bool s_bPlayerBotFairWriter = false, s_bPlayerBotFairSeeded = false;

	DWORD GetPlayerBotFairKindRef(const TPlayerBotFairKind& k)
	{
		return k.src == 'P' && k.refM ? k.refM : k.ref;
	}

	void AddPlayerBotFairKindSale(TPlayerBotFairKind& k, DWORD hour, DWORD count, DWORD unit, bool hi)
	{
		const int i = (int)(hour % PLAYERBOT_FAIR_HOURS);
		if (k.hourStamp[i] != hour)
		{
			k.hourStamp[i] = hour;
			k.sold[i] = k.soldHi[i] = 0;
			k.events[i] = 0;
		}
		k.sold[i] += count;
		if (hi)
			k.soldHi[i] += count;
		if (k.events[i] < 0xFFFF)
			++k.events[i];
		if (unit)
		{
			TPlayerBotFairSale s;
			s.unit = unit;
			s.count = count;
			s.hour = hour;
			k.sales.push_back(s);
			while (k.sales.size() > PLAYERBOT_FAIR_SALES_KEPT)
				k.sales.pop_front();
		}
	}

	// The trimmed mean of the kept sales of the window (a fifth off each end, by units), 0 under three sales.
	DWORD GetPlayerBotFairTrimmedMean(const TPlayerBotFairKind& k, DWORD fromHour)
	{
		std::vector<std::pair<DWORD, DWORD> > v;
		unsigned long long units = 0;
		for (const TPlayerBotFairSale& s : k.sales)
			if (s.hour >= fromHour)
			{
				v.push_back(std::make_pair(s.unit, s.count));
				units += s.count;
			}
		if (v.size() < 3 || units == 0)
			return 0;
		std::sort(v.begin(), v.end());
		const unsigned long long cut = units / 5ULL;
		unsigned long long at = 0, keptUnits = 0;
		long double sum = 0;
		for (const auto& e : v)
		{
			const unsigned long long from = at, to = at + e.second;
			at = to;
			const unsigned long long lo = std::max(from, cut), hi = std::min(to, units - cut);
			if (hi <= lo)
				continue;
			keptUnits += hi - lo;
			sum += (long double)e.first * (long double)(hi - lo);
		}
		return keptUnits ? (DWORD)std::min<long double>(4294967294.0L, sum / (long double)keptUnits) : 0U;
	}

	// The sales since the last call (playerbot_offline::fairSales, every core sees every sale): every core notes a
	// bot's last sale of a kind (its seller state), the writer counts them for the kinds.
	void DrainPlayerBotFairSales(DWORD nowS)
	{
		std::vector<playerbot_offline::FairSale> sales;
		sales.swap(playerbot_offline::fairSales);
		if (sales.empty() || !IsPlayerBotFairPriceOn())
			return;
		TPlayerBotFairCensus& k = s_kPlayerBotFairCensus;
		const DWORD hour = nowS / 3600U;
		for (const playerbot_offline::FairSale& s : sales)
		{
			if (!s.vnum || !s.count || s.price <= 0 || !IsPlayerBotFairGoods(s.vnum))
				continue;
			++k.salesIn;
			DWORD owner = s.owner;
			if (!owner)
			{
				std::unordered_map<DWORD, DWORD>::const_iterator o = s_mapPlayerBotFairLineOwner.find(s.item);
				if (o != s_mapPlayerBotFairLineOwner.end())
					owner = o->second;
			}
			if (owner)
			{
				++k.salesOwner;
				TPlayerBotFairSeller& st = s_mapPlayerBotFairSellers[PlayerBotFairKey(owner, s.vnum)];
				st.lastSale = nowS;
				st.soldSinceCheck += s.count;
				st.lastSeen = nowS;
			}
			if (!s_bPlayerBotFairWriter)
				continue;
			const DWORD unit = (DWORD)std::min<long long>(0xFFFFFFFELL, std::max(1LL, s.price / (long long)s.count));
			TPlayerBotFairKind& kind = s_mapPlayerBotFairKinds[s.vnum];
			if (kind.firstHour == 0)
				kind.firstHour = hour;
			const DWORD fair = kind.fairUnit;
			// A giveaway (a person's line at 1 yang) or a slip is no market price, and not the market's demand either.
			if (fair > 0 && ((unsigned long long)unit * 100ULL < (unsigned long long)fair * 35ULL ||
					(unsigned long long)unit > (unsigned long long)fair * 3ULL))
			{
				++kind.outliers;
				++k.outliers;
				continue;
			}
			AddPlayerBotFairKindSale(kind, hour, s.count, unit, fair > 0 && (unsigned long long)unit * 1000ULL >=
					(unsigned long long)fair * 995ULL);
		}
	}

	// ------------------------------------------------------------------------------------------------ the tables
	bool s_bPlayerBotFairTables = false;

	bool EnsurePlayerBotFairTables()
	{
		if (s_bPlayerBotFairTables)
			return true;
		// The same as linux-port/docker/mariadb/playerbot/rynek_fair.sql (apply.sh) - here for a world without it.
		std::unique_ptr<SQLMsg> a(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_market_fair ("
				"vnum INT UNSIGNED NOT NULL PRIMARY KEY, ref_unit INT UNSIGNED NOT NULL DEFAULT 0, "
				"ref_src CHAR(1) NOT NULL DEFAULT 'S', ratio_pm INT UNSIGNED NOT NULL DEFAULT 1000, "
				"fair_unit INT UNSIGNED NOT NULL DEFAULT 0, min_pm INT UNSIGNED NOT NULL DEFAULT 0, "
				"max_pm INT UNSIGNED NOT NULL DEFAULT 0, pin_unit INT UNSIGNED NOT NULL DEFAULT 0, "
				"stock BIGINT UNSIGNED NOT NULL DEFAULT 0, offer_lines INT UNSIGNED NOT NULL DEFAULT 0, "
				"sellers INT UNSIGNED NOT NULL DEFAULT 0, sold_w INT UNSIGNED NOT NULL DEFAULT 0, "
				"events_w INT UNSIGNED NOT NULL DEFAULT 0, sold_6h INT UNSIGNED NOT NULL DEFAULT 0, "
				"sold_hi_6h INT UNSIGNED NOT NULL DEFAULT 0, window_h SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
				"cover_h INT UNSIGNED NOT NULL DEFAULT 0, sale_mean INT UNSIGNED NOT NULL DEFAULT 0, "
				"p_min INT UNSIGNED NOT NULL DEFAULT 0, p25 INT UNSIGNED NOT NULL DEFAULT 0, "
				"p50 INT UNSIGNED NOT NULL DEFAULT 0, p75 INT UNSIGNED NOT NULL DEFAULT 0, "
				"p_max INT UNSIGNED NOT NULL DEFAULT 0, conf_pm SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
				"x_pm SMALLINT NOT NULL DEFAULT 0, move_bp SMALLINT NOT NULL DEFAULT 0, "
				"port SMALLINT UNSIGNED NOT NULL DEFAULT 0, updated INT UNSIGNED NOT NULL DEFAULT 0, "
				"KEY updated (updated)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> b(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_market_fair_hist ("
				"vnum INT UNSIGNED NOT NULL, hour INT UNSIGNED NOT NULL, ref_unit INT UNSIGNED NOT NULL DEFAULT 0, "
				"fair_unit INT UNSIGNED NOT NULL DEFAULT 0, stock BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"sold INT UNSIGNED NOT NULL DEFAULT 0, events INT UNSIGNED NOT NULL DEFAULT 0, "
				"sold_hi INT UNSIGNED NOT NULL DEFAULT 0, sale_mean INT UNSIGNED NOT NULL DEFAULT 0, "
				"p50 INT UNSIGNED NOT NULL DEFAULT 0, sellers INT UNSIGNED NOT NULL DEFAULT 0, "
				"PRIMARY KEY (vnum, hour), KEY hour (hour)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> c(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_market_fair_pin ("
				"vnum INT UNSIGNED NOT NULL PRIMARY KEY, pin_unit INT UNSIGNED NOT NULL DEFAULT 0, "
				"min_pct SMALLINT UNSIGNED NOT NULL DEFAULT 0, max_pct SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
				"note VARCHAR(80) NOT NULL DEFAULT '', updated_at DATETIME NULL) ENGINE=InnoDB"));
		s_bPlayerBotFairTables = a && a->Get() && b && b->Get() && c && c->Get();
		return s_bPlayerBotFairTables;
	}

	// The panel's pins and bounds: vnum -> (pin a unit, min %, max %).
	struct TPlayerBotFairPin
	{
		DWORD pin = 0, minPct = 0, maxPct = 0;
	};
	std::unordered_map<DWORD, TPlayerBotFairPin> s_mapPlayerBotFairPins;

	void ReadPlayerBotFairPins()
	{
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT vnum, pin_unit, min_pct, max_pct FROM player.playerbot_market_fair_pin"));
		if (!msg || !msg->Get())
			return;
		std::unordered_map<DWORD, TPlayerBotFairPin> pins;
		if (msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				DWORD vnum = 0;
				TPlayerBotFairPin p;
				str_to_number(vnum, row[0]);
				str_to_number(p.pin, row[1]);
				str_to_number(p.minPct, row[2]);
				str_to_number(p.maxPct, row[3]);
				if (vnum && (p.pin || p.minPct || p.maxPct))
					pins[vnum] = p;
			}
		}
		s_mapPlayerBotFairPins.swap(pins);
	}

	// A writer's first pass (a start, or the writer moved here): the ratios and the sales by the hour from the tables.
	void SeedPlayerBotFairWriter(DWORD nowS)
	{
		const TPlayerBotFairCfg& c = GetPlayerBotFairCfg();
		s_bPlayerBotFairSeeded = true;
		s_mapPlayerBotFairKinds.clear();
		unsigned int rows = 0, hours = 0;
		{
			std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
					"SELECT vnum, ref_unit, ref_src, ratio_pm FROM player.playerbot_market_fair"));
			if (msg && msg->Get() && msg->Get()->uiNumRows > 0)
			{
				MYSQL_ROW row;
				while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
				{
					DWORD vnum = 0, ref = 0, ratio = 0;
					str_to_number(vnum, row[0]);
					str_to_number(ref, row[1]);
					str_to_number(ratio, row[3]);
					if (!vnum || !ratio)
						continue;
					TPlayerBotFairKind& k = s_mapPlayerBotFairKinds[vnum];
					k.ratio = (double)ratio / 1000.0;
					const char src = row[2] && row[2][0] ? row[2][0] : 'S';
					if (src == 'M' && ref)
					{
						k.src = 'P';
						k.refM = ref;
						k.refMAt = nowS;
					}
					++rows;
				}
			}
		}
		{
			const DWORD nowH = nowS / 3600U;
			std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
					"SELECT vnum, hour, sold, events, sold_hi FROM player.playerbot_market_fair_hist WHERE hour >= %u",
					nowH - (DWORD)c.windowH + 1U));
			if (msg && msg->Get() && msg->Get()->uiNumRows > 0)
			{
				MYSQL_ROW row;
				while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
				{
					DWORD vnum = 0, hour = 0, sold = 0, events = 0, soldHi = 0;
					str_to_number(vnum, row[0]);
					str_to_number(hour, row[1]);
					str_to_number(sold, row[2]);
					str_to_number(events, row[3]);
					str_to_number(soldHi, row[4]);
					if (!vnum || hour > nowH)
						continue;
					TPlayerBotFairKind& k = s_mapPlayerBotFairKinds[vnum];
					const int i = (int)(hour % PLAYERBOT_FAIR_HOURS);
					k.hourStamp[i] = hour;
					k.sold[i] = sold;
					k.soldHi[i] = soldHi;
					k.events[i] = (WORD)std::min<DWORD>(0xFFFF, events);
					if (k.firstHour == 0 || hour < k.firstHour)
						k.firstHour = hour;
					++hours;
				}
			}
		}
		sys_log(0, "PLAYERBOT_FAIR: writer seeded port=%u kinds=%u rows=%u hours=%u",
				(unsigned int)mother_port, (unsigned int)s_mapPlayerBotFairKinds.size(), rows, hours);
	}

	// Every other core: the writer's rows (an hour old at most - a writer gone leaves the references, ratio 1).
	void ReadPlayerBotFairRows(DWORD nowS)
	{
		if (!EnsurePlayerBotFairTables())
			return;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT vnum, ref_unit, ref_src, ratio_pm, min_pm, max_pm, pin_unit FROM player.playerbot_market_fair "
				"WHERE updated >= %u", nowS - 3600U));
		if (!msg || !msg->Get())
		{
			++s_kPlayerBotFairCensus.readFailed;
			return;
		}
		std::unordered_map<DWORD, TPlayerBotFairRow> rows;
		if (msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				DWORD vnum = 0;
				TPlayerBotFairRow r;
				str_to_number(vnum, row[0]);
				str_to_number(r.ref, row[1]);
				r.src = row[2] && row[2][0] ? row[2][0] : 'S';
				str_to_number(r.ratioPm, row[3]);
				str_to_number(r.minPm, row[4]);
				str_to_number(r.maxPm, row[5]);
				str_to_number(r.pin, row[6]);
				if (vnum)
					rows[vnum] = r;
			}
		}
		s_mapPlayerBotFairShared.swap(rows);
		++s_kPlayerBotFairCensus.rowsRead;
	}

	// ------------------------------------------------------------------------------------------------ the writer
	const unsigned int PLAYERBOT_FAIR_PROBES_A_STEP = 250;
	const DWORD PLAYERBOT_FAIR_REF_STALE_S = 6 * 3600;

	// The kind's reference: the owner's fish price, this core's own (fresh), or a probe of one piece (the chat deals'
	// way: a piece made, priced, destroyed - the hook notes the prior).
	void RefreshPlayerBotFairKindRef(DWORD vnum, TPlayerBotFairKind& k, DWORD nowS, unsigned int& probes)
	{
		const DWORD fish = GetPlayerBotRoastedFishOwnerPrice(vnum);
		if (fish)
		{
			k.ref = fish;
			k.src = 'O';
			return;
		}
		std::unordered_map<DWORD, TPlayerBotFairRef>::const_iterator it = s_mapPlayerBotFairLocalRef.find(vnum);
		const bool fresh = it != s_mapPlayerBotFairLocalRef.end() && nowS - it->second.at < PLAYERBOT_FAIR_REF_STALE_S;
		if (!fresh && probes < PLAYERBOT_FAIR_PROBES_A_STEP)
		{
			++probes;
			++s_kPlayerBotFairCensus.probes;
			if (LPITEM probe = ITEM_MANAGER::instance().CreateItem(vnum, 1, 0, false))
			{
				(void)GetPlayerBotShopAskingPrice(probe);
				M2_DESTROY_ITEM(probe);
			}
			it = s_mapPlayerBotFairLocalRef.find(vnum);
		}
		if (it != s_mapPlayerBotFairLocalRef.end() && it->second.unit)
		{
			k.ref = it->second.unit;
			k.src = it->second.src == 'O' ? 'O' : (it->second.src == 'S' ? 'S' : 'P');
		}
	}

	struct TPlayerBotFairWriterState
	{
		DWORD histHour = 0, pruneHour = 0;
	};
	TPlayerBotFairWriterState s_kPlayerBotFairWriterState;

	void StepPlayerBotFairWriter(DWORD nowS)
	{
		const TPlayerBotFairCfg& c = GetPlayerBotFairCfg();
		if (!EnsurePlayerBotFairTables())
			return;
		if (!s_bPlayerBotFairSeeded)
			SeedPlayerBotFairWriter(nowS);
		ReadPlayerBotFairPins();
		++s_kPlayerBotFairCensus.steps;
		const DWORD nowH = nowS / 3600U;
		for (const auto& [vnum, book] : s_mapPlayerBotFairBooks)
			if (book.units > 0)
			{
				TPlayerBotFairKind& k = s_mapPlayerBotFairKinds[vnum];
				if (k.firstHour == 0)
					k.firstHour = nowH;
			}
		const double lnExtreme = log(8.0);
		const int deadPm = 80;
		unsigned int probes = 0;
		std::unordered_map<DWORD, TPlayerBotFairRow> shared;
		std::string rows, hist;
		auto flush = [](std::string& s, const char* head) {
			if (s.empty())
				return;
			DBManager::instance().Query("%s%s", head, s.c_str());
			s.clear();
		};
		static const char* s_szRowHead = "REPLACE INTO player.playerbot_market_fair (vnum, ref_unit, ref_src, ratio_pm, "
				"fair_unit, min_pm, max_pm, pin_unit, stock, offer_lines, sellers, sold_w, events_w, sold_6h, sold_hi_6h, "
				"window_h, cover_h, sale_mean, p_min, p25, p50, p75, p_max, conf_pm, x_pm, move_bp, port, updated) VALUES ";
		static const char* s_szHistHead = "REPLACE INTO player.playerbot_market_fair_hist (vnum, hour, ref_unit, fair_unit, "
				"stock, sold, events, sold_hi, sale_mean, p50, sellers) VALUES ";
		for (auto it = s_mapPlayerBotFairKinds.begin(); it != s_mapPlayerBotFairKinds.end(); )
		{
			const DWORD vnum = it->first;
			TPlayerBotFairKind& k = it->second;
			std::unordered_map<DWORD, TPlayerBotFairBook>::const_iterator bk = s_mapPlayerBotFairBooks.find(vnum);
			const TPlayerBotFairBook book = bk == s_mapPlayerBotFairBooks.end() ? TPlayerBotFairBook() : bk->second;
			// the window's sales
			const DWORD watchedH = std::max<DWORD>(1U, std::min<DWORD>((DWORD)c.windowH, nowH - std::min(nowH, k.firstHour) + 1U));
			DWORD soldW = 0, eventsW = 0, sold6 = 0, soldHi6 = 0, soldNow = 0;
			for (DWORD h = nowH + 1U - watchedH; h <= nowH; ++h)
			{
				const int i = (int)(h % PLAYERBOT_FAIR_HOURS);
				if (k.hourStamp[i] != h)
					continue;
				soldW += k.sold[i];
				eventsW += k.events[i];
				if (h + 6U > nowH)
				{
					sold6 += k.sold[i];
					soldHi6 += k.soldHi[i];
				}
				if (h == nowH)
					soldNow = k.sold[i];
			}
			// A kind nobody lists nor buys any more is let go after a day (its row ages out of the readers' hour).
			if (book.units == 0 && soldW == 0 && nowH > k.firstHour + 24U && !s_mapPlayerBotFairPins.count(vnum))
			{
				it = s_mapPlayerBotFairKinds.erase(it);
				continue;
			}
			RefreshPlayerBotFairKindRef(vnum, k, nowS, probes);
			// the sales' reference of a merchant-priced kind: the trimmed mean of the accepted sales, set once there are
			// eight of them, then moved at most 10 % a day
			const DWORD mean = GetPlayerBotFairTrimmedMean(k, nowH + 1U - watchedH);
			if (k.src == 'P' && mean > 0 && k.sales.size() >= 8)
			{
				if (k.refM == 0)
				{
					k.refM = mean;
					k.refMAt = nowS;
				}
				else if (nowS - k.refMAt >= 86400U)
				{
					k.refM = (DWORD)std::max<double>(1.0, std::min<double>((double)k.refM * 1.1,
							std::max<double>((double)k.refM * 0.9, (double)mean)));
					k.refMAt = nowS;
				}
			}
			const DWORD ref = GetPlayerBotFairKindRef(k);
			if (ref == 0)
			{
				++it;
				continue;
			}
			std::unordered_map<DWORD, TPlayerBotFairPin>::const_iterator pin = s_mapPlayerBotFairPins.find(vnum);
			const DWORD minPm = pin != s_mapPlayerBotFairPins.end() && pin->second.minPct ? pin->second.minPct * 10U
					: (DWORD)c.minPct * 10U;
			const DWORD maxPm = std::max(minPm, pin != s_mapPlayerBotFairPins.end() && pin->second.maxPct
					? pin->second.maxPct * 10U : (DWORD)c.maxPct * 10U);
			const DWORD pinUnit = pin != s_mapPlayerBotFairPins.end() ? pin->second.pin : 0U;
			// the market's imbalance
			// units an hour - the current hour counted for the part of it gone, so a fresh hour reads no slowdown
			const double partial = std::max(1.0 / 60.0, (double)(nowS % 3600U) / 3600.0);
			const double rate = (double)soldW / ((double)watchedH - 1.0 + partial);
			const double rate6 = (double)sold6 / ((double)std::min<DWORD>(6U, watchedH) - 1.0 + partial);
			const double stock = (double)book.units;
			double xc = 0.0;
			if (stock <= 0.0)
				xc = rate > 0.0 ? -1.0 : 0.0;
			else if (rate <= 0.0)
				xc = 1.0;
			else
				xc = std::max(-1.0, std::min(1.0, log(stock / rate / 24.0 / (double)c.coverDays) / lnExtreme));
			if (xc > 0.0)
				xc *= (double)c.stockW / 100.0;
			double xp = 0.0;
			if (sold6 > 0)
				xp = -std::min(1.0, ((double)soldHi6 / (double)sold6) / 0.5) * (double)c.priceW / 100.0;
			double xt = 0.0;
			if (watchedH >= 12U && soldW > 0)
			{
				const double a = std::max(rate * 0.25, 1.0 / 48.0);
				xt = std::max(-1.0, std::min(1.0, -log((rate6 + a) / (rate + a)) / log(4.0))) * (double)c.trendW / 100.0;
			}
			double x = std::max(-1.0, std::min(1.0, xc + xp + xt));
			const double dead = (double)deadPm / 1000.0;
			x = fabs(x) < dead ? 0.0 : (x > 0 ? (x - dead) : (x + dead)) / (1.0 - dead);
			double conf = (double)eventsW / (double)(eventsW + (DWORD)c.confSales);
			if (eventsW == 0)
				conf = x > 0.0 ? 0.3 * std::min(1.0, stock / 50.0) : 0.0;
			double move = x > 0.0 ? -(double)c.downPct / 100.0 * x : (double)c.upPct / 100.0 * -x;
			move *= conf;
			const double dtH = k.lastStepAt ? std::min(1.0, (double)(nowS - k.lastStepAt) / 3600.0) : 0.0;
			k.lastStepAt = nowS;
			if (dtH > 0.0)
			{
				if (stock <= 0.0 && soldW == 0)
					k.ratio += (1.0 - k.ratio) * std::min(1.0, 0.02 * dtH);
				else
					k.ratio *= pow(1.0 + move, dtH);
			}
			if (pinUnit)
				k.ratio = (double)pinUnit / (double)ref;
			else
				k.ratio = std::max((double)minPm / 1000.0, std::min((double)maxPm / 1000.0, k.ratio));
			k.x = x;
			k.conf = conf;
			k.rate = move;
			k.soldW = soldW;
			k.eventsW = eventsW;
			k.sold6 = sold6;
			k.soldHi6 = soldHi6;
			k.saleMean = mean;
			k.coverH = rate > 0.0 ? stock / rate : (stock > 0.0 ? 999999.0 : 0.0);
			k.fairUnit = pinUnit ? pinUnit : (DWORD)std::max(1.0, std::min(4294967294.0, (double)ref * k.ratio + 0.5));
			TPlayerBotFairRow& r = shared[vnum];
			r.ref = ref;
			r.src = k.src == 'P' && k.refM ? 'M' : k.src;
			r.ratioPm = (DWORD)std::max(1.0, k.ratio * 1000.0 + 0.5);
			r.minPm = minPm;
			r.maxPm = maxPm;
			r.pin = pinUnit;
			char row[320];
			snprintf(row, sizeof(row), "%s(%u,%u,'%c',%u,%u,%u,%u,%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d,%d,%u,%u)",
					rows.empty() ? "" : ",", vnum, ref, r.src, r.ratioPm, k.fairUnit, minPm, maxPm, pinUnit, book.units,
					book.lines, book.sellers, soldW, eventsW, sold6, soldHi6, watchedH,
					(unsigned int)std::min(999999.0, k.coverH), mean, book.pMin, book.p25, book.p50, book.p75, book.pMax,
					(unsigned int)(conf * 1000.0 + 0.5), (int)(x * 1000.0), (int)std::max(-32000.0, std::min(32000.0, move * 10000.0)),
					(unsigned int)mother_port, nowS);
			rows += row;
			if (rows.size() > 3300)
				flush(rows, s_szRowHead);
			if (book.units > 0 || soldNow > 0)
			{
				const int i = (int)(nowH % PLAYERBOT_FAIR_HOURS);
				const bool cur = k.hourStamp[i] == nowH;
				char h[200];
				snprintf(h, sizeof(h), "%s(%u,%u,%u,%u,%llu,%u,%u,%u,%u,%u,%u)", hist.empty() ? "" : ",", vnum, nowH, ref,
						k.fairUnit, book.units, cur ? k.sold[i] : 0U, cur ? (unsigned int)k.events[i] : 0U,
						cur ? k.soldHi[i] : 0U, mean, book.p50, book.sellers);
				hist += h;
				if (hist.size() > 3500)
					flush(hist, s_szHistHead);
			}
			++it;
		}
		flush(rows, s_szRowHead);
		flush(hist, s_szHistHead);
		s_mapPlayerBotFairShared.swap(shared);
		// the rows of the kinds let go, and the old history (once an hour)
		DBManager::instance().Query("DELETE FROM player.playerbot_market_fair WHERE updated < %u", nowS - 2U * 86400U);
		if (s_kPlayerBotFairWriterState.pruneHour != nowH)
		{
			s_kPlayerBotFairWriterState.pruneHour = nowH;
			DBManager::instance().Query("DELETE FROM player.playerbot_market_fair_hist WHERE hour < %u",
					nowH - (DWORD)c.histDays * 24U);
		}
	}

	// ------------------------------------------------------------------------------------------------ the census
	void LogPlayerBotFairCensus(DWORD nowS)
	{
		TPlayerBotFairCensus& k = s_kPlayerBotFairCensus;
		unsigned long long units = 0;
		unsigned int lines = 0;
		for (const auto& [vnum, b] : s_mapPlayerBotFairBooks)
		{
			units += b.units;
			lines += b.lines;
		}
		unsigned int hosted = 0, kinds[3] = { 0, 0, 0 };
		for (const auto& [key, s] : s_mapPlayerBotFairSellers)
			if (s.hosted)
			{
				++hosted;
				++kinds[GetPlayerBotFairPersonality((DWORD)(key >> 32))];
			}
		sys_log(0, "PLAYERBOT_FAIR: census ch=%u port=%u on=%d writer=%d kinds=%u shared_rows=%u local_refs=%u offer_kinds=%u "
				"offer_units=%llu offer_lines=%u asked=%u sales_in=%u sales_owner=%u outliers=%u probes=%u steps=%u rows_read=%u "
				"read_failed=%u sellers=%u hosted=%u hosted_traders=%u hosted_normal=%u hosted_patient=%u checks=%u raised=%u "
				"lowered=%u at_floor=%u at_ceiling=%u edits_queued=%u edits_done=%u edits_skipped=%u repaired=%u repaired_yang=%llu",
				(unsigned int)g_bChannel, (unsigned int)mother_port, IsPlayerBotFairPriceOn() ? 1 : 0, s_bPlayerBotFairWriter ? 1 : 0,
				(unsigned int)s_mapPlayerBotFairKinds.size(), (unsigned int)s_mapPlayerBotFairShared.size(),
				(unsigned int)s_mapPlayerBotFairLocalRef.size(), (unsigned int)s_mapPlayerBotFairBooks.size(), units, lines,
				k.asked, k.salesIn, k.salesOwner, k.outliers, k.probes, k.steps, k.rowsRead, k.readFailed,
				(unsigned int)s_mapPlayerBotFairSellers.size(), hosted, kinds[0], kinds[1], kinds[2], k.checks, k.raised,
				k.lowered, k.atFloor, k.atCeil, k.editsQueued, k.editsDone, k.editsSkipped, k.repaired, k.repairedYang);
		if (s_bPlayerBotFairWriter)
		{
			std::vector<std::pair<unsigned long long, DWORD> > ranked;
			for (const auto& [vnum, b] : s_mapPlayerBotFairBooks)
				if (s_mapPlayerBotFairKinds.count(vnum))
					ranked.push_back(std::make_pair(b.units, vnum));
			std::sort(ranked.rbegin(), ranked.rend());
			for (size_t i = 0; i < ranked.size() && i < 12; ++i)
			{
				const DWORD vnum = ranked[i].second;
				std::unordered_map<DWORD, TPlayerBotFairRow>::const_iterator ri = s_mapPlayerBotFairShared.find(vnum);
				if (ri == s_mapPlayerBotFairShared.end())
					continue;
				const TPlayerBotFairRow& r = ri->second;
				const TPlayerBotFairKind& f = s_mapPlayerBotFairKinds[vnum];
				const TPlayerBotFairBook& b = s_mapPlayerBotFairBooks[vnum];
				sys_log(0, "PLAYERBOT_FAIR: kind vnum=%u ref=%u src=%c fair=%u ratio_pm=%u bounds_pm=%u..%u pin=%u stock=%llu "
						"lines=%u sellers=%u sold_w=%u events_w=%u sold_6h=%u sold_hi_6h=%u cover_d=%.1f sale_mean=%u x=%.2f "
						"conf=%.2f move_h=%.2f%% outliers=%u spread min=%u p25=%u med=%u p75=%u max=%u",
						vnum, r.ref, r.src, f.fairUnit, r.ratioPm, r.minPm, r.maxPm, r.pin, b.units, b.lines, b.sellers, f.soldW,
						f.eventsW, f.sold6, f.soldHi6, f.coverH / 24.0, f.saleMean, f.x, f.conf, f.rate * 100.0, f.outliers,
						b.pMin, b.p25, b.p50, b.p75, b.pMax);
			}
		}
		s_kPlayerBotFairCensus = TPlayerBotFairCensus();
		(void)nowS;
	}

	// ------------------------------------------------------------------------------------------------ the core's clock
	// From the lada's core tick (ManagePlayerBotLadaCore, once a second), with the lada's tier writer.
	void ManagePlayerBotFairCore(DWORD now, bool writer)
	{
		static DWORD s_dwScan = 0, s_dwStep = 0, s_dwRead = 0, s_dwCensus = 0;
		const TPlayerBotFairCfg& c = GetPlayerBotFairCfg();
		const DWORD nowS = (DWORD)get_global_time();
		if (!c.on)
		{
			playerbot_offline::fairSales.clear();
			if (!s_mapPlayerBotFairSellers.empty() || !s_mapPlayerBotFairKinds.empty())
			{
				s_mapPlayerBotFairSellers.clear();
				s_mapPlayerBotFairKinds.clear();
				s_mapPlayerBotFairShared.clear();
				s_bPlayerBotFairSeeded = false;
			}
			return;
		}
		if (writer != s_bPlayerBotFairWriter)
		{
			s_bPlayerBotFairWriter = writer;
			s_bPlayerBotFairSeeded = false;	// a new writer begins from the tables
			if (!writer)
				s_mapPlayerBotFairKinds.clear();
			sys_log(0, "PLAYERBOT_FAIR: writer=%d port=%u ch=%u", writer ? 1 : 0, (unsigned int)mother_port, (unsigned int)g_bChannel);
		}
		if (s_dwScan == 0 || now - s_dwScan >= 60000)
		{
			s_dwScan = now ? now : 1;
			ScanPlayerBotFairMarket(writer);
		}
		DrainPlayerBotFairSales(nowS);
		if (writer)
		{
			if (s_dwStep == 0 || now - s_dwStep >= (DWORD)c.stepMin * 60000U)
			{
				s_dwStep = now ? now : 1;
				StepPlayerBotFairWriter(nowS);
			}
		}
		else if (s_dwRead == 0 || now - s_dwRead >= 5U * 60000U)
		{
			s_dwRead = now ? now : 1;
			ReadPlayerBotFairRows(nowS);
		}
		if (s_dwCensus == 0)
			s_dwCensus = now ? now : 1;
		else if (now - s_dwCensus >= 10U * 60000U)
		{
			s_dwCensus = now ? now : 1;
			LogPlayerBotFairCensus(nowS);
		}
	}
#else
	bool IsPlayerBotFairPriceOn()
	{
		return false;
	}
	bool IsPlayerBotFairGoods(DWORD vnum)
	{
		(void)vnum;
		return false;
	}
	DWORD PlayerBotFairAskUnit(DWORD vnum, DWORD prior, char src)
	{
		(void)vnum; (void)prior; (void)src;
		return 0;
	}
	DWORD GetPlayerBotFairSellerUnit(DWORD owner, DWORD vnum)
	{
		(void)owner; (void)vnum;
		return 0;
	}
	DWORD GetPlayerBotFairFloorUnit(DWORD owner, DWORD vnum)
	{
		(void)owner; (void)vnum;
		return 0;
	}
	DWORD GetPlayerBotFairStockUnits(DWORD vnum)
	{
		(void)vnum;
		return 0;
	}
#endif
}

#endif
