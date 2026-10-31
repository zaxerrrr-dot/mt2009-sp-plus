#ifndef __INC_METIN2_PLAYERBOT_YOHARA_SHOP_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_SHOP_H__

// MT2009_PLUS_BOT_YOHARA_SHOP_V1 - the bots' exchange in Dongan and their world set (the owner, 22 October 2026: list
// item 24 of boty-yohara-lista.md, and "Ekstra: sklep specjalny dla botow w Dongan").
//
// The exchange (bots only - no NPC, no shop window, nothing a person ever sees): at Handlarka Roznosci (9003, Dongan
// 373, the merchant Dongan's errand calls on - playerbot_yohara_sungma.h) a Champion bot changes
//   * 10 Materialy Rzemieslnicze (30378) for 1 elixir of RESISTANCE to an element of its map (50836-50841), and
//   * 10 Magiczny Pyl (30360) for 1 elixir of POWER of an element of its map (50830-50835) - the dust only above its
//     G0 reserve (GetPlayerBotG0DustReserve: a saver's 400 are never touched; banked dust is in the box anyway).
// "Its map" is the map its elements are taken for (GetPlayerBotYoharaElementMap - its Sung Ma stay's map, never Dongan
// on an errand) and an element of it one of PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT or more (the table of
// playerbot_yohara_elements.h - both of the two-element maps, Namgan's wind and dark). The elixir is made as the
// cube makes it, then set to the cube's best: 20% for 10 minutes (MT2009_PLUS_BOT_YOHARA_SHOP_V2).
//
// The stock: up to PLAYERBOT_YSHOP_TARGET of each kind the map needs; Dongan's errand is called for it when a kind is
// under PLAYERBOT_YSHOP_LOW and the bot holds the input for one (at most every PLAYERBOT_YSHOP_ERRAND_GAP_MS). The
// inputs it keeps and buys towards: ten for each elixir short of the target, at most PLAYERBOT_YSHOP_INPUT_MAX of
// each - the materials through the craft want (GetPlayerBotCraftMaterialsWanted: kept off the counters, bought
// off them at the material's caps, refine goods changed at the Dozorca), the dust through the counters' dust keep
// (over the G0 reserve) and its own market line (PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT of the bots' dust price, out of
// PLAYERBOT_YSHOP_DUST_PURSE_PCT of the spare purse). A trade trip home (reason "buy") also goes for them, when a kind
// is low and the market holds what is short. The elixirs - up to PLAYERBOT_YSHOP_KEEP_MAX of each of the twelve - are
// never sold by a Champion; they are drunk on the map (ManagePlayerBotYoharaElements: resistance and power).
//
// The world set (item 24): a Champion that owns jade jewellery (Obrecz / Kolia / Klipsy Jadeitu) keeps, for each of
// those slots, its best piece of other jewellery (the Emerald or whatever is best off Yohara) and its best jade -
// never the merchant's, a counter's or another bot's. Off the Sung Ma maps (Zaklety Las, the Rift, the Hydra, the
// dungeons, home) the Will of its lines counts nothing (GetPlayerBotSungmaWillWeight -> 0), so the gear's score puts
// the world piece on; on a Sung Ma map the Will counts and the jade goes back on. The swap is made at once, out of a
// fight, on the bot's own clock (ManagePlayerBotYoharaShop), the same score as the equipment pass. While dressed for the
// world the Will a Sung Ma map is checked against is the Will the jade in the bag would give
// (GetPlayerBotYoharaWorldSetWillDelta, in GetPlayerBotSungmaWill) - a bot does not step down for its world set.
//
// The log: PLAYERBOT_SHOP2 (exchange, errand wanted, dust/material bought, worldset swap, census every ten minutes).
//
// MT2009_PLUS_BOT_ELEMENT_RESIST_V2 (the census of 28 October: elixir stock_avg 0 for every element, resist_made 0,
// materials_bought 0 - 721 of the 900 cohort bots held no Materialy Rzemieslnicze at all, no NPC sells them, the
// counters had none for them, and a bot that held some had them taken by its horse's keep first):
//   * a bot with a hunt element keeps PLAYERBOT_YSHOP_HUNT_MATERIAL_KEEP materials as its own (never the merchant's, a
//     counter's or the Dozorca's - IsPlayerBotKeptCraftMaterial asks here too) - a grant of them is spent on elixirs,
//     not sold;
//   * its elixir comes before its horse: the exchange takes every material it holds;
//   * an exchange at Handlarka that makes nothing while the hunt element's elixirs are low says why ("exchange none",
//     throttled): no materials, no room, no map.
//
// MT2009_PLUS_BOT_G0_DUST_RULE_V1 (the census of 28 October: power_made=0, dust_paid=0, dust_bought=0, every errand's
// dust_free=0 - 144 second-set bots kept 400 for a second G0 and sought nothing else, the rest held almost no dust):
// a bot with its G0 holds no reserve unless it struggles with its set in the second-set mode (playerbot_yohara_g0.h,
// playerbot_g0_dust_rule.h), so its dust is free for the hunt element's power elixir at the targets above; the power
// elixir's dust on the market is bought at most PLAYERBOT_G0_DUST_PRICE_CAP_PCT of the bots' dust price, out of
// PLAYERBOT_YSHOP_DUST_PURSE_PCT of the spare purse, at most PLAYERBOT_G0DR_POWER_DUST_DAY units a bot in a day, and
// only while the core's counters hold more than PLAYERBOT_G0DR_POWER_DUST_FLOOR (AllowsPlayerBotPowerDustMarket) - the
// elixir burns 60 dust an hour on the map, and 900 Champions on an unbounded line would empty the counters the lower
// bots' marbles and the players buy from.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_elements_late.h.

namespace
{
	const DWORD PLAYERBOT_YSHOP_MATERIAL_VNUM = 30378;	// Materialy Rzemieslnicze
	const int PLAYERBOT_YSHOP_RATE = 10;	// inputs a elixir
	const DWORD PLAYERBOT_YSHOP_NPC = 9003;	// Handlarka Roznosci, Dongan
	const int PLAYERBOT_YSHOP_TARGET = 8;	// elixirs of a needed kind the exchange fills to
	const int PLAYERBOT_YSHOP_LOW = 4;	// under this the errand is called for it
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the resistance elixir drunk every 10 minutes all the hunt long (the elixir tick
	// of playerbot_element_resist.h) - 6 an hour: filled to 16 (some 2.5 hours), the errand under 6; the power elixir's
	// stock as before. Never sold up to 20 of a vnum.
	const int PLAYERBOT_YSHOP_KEEP_MAX = 20;	// elixirs of a vnum never sold
	const int PLAYERBOT_YSHOP_RESIST_TARGET = 16;
	const int PLAYERBOT_YSHOP_RESIST_LOW = 6;
#else
	const int PLAYERBOT_YSHOP_KEEP_MAX = 10;	// elixirs of a vnum never sold
#endif
	const int PLAYERBOT_YSHOP_INPUT_MAX = 100;	// materials / dust over the reserves wanted at most
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the materials a bot with a hunt element keeps (300 elixirs, 50 hours of its map)
	const int PLAYERBOT_YSHOP_HUNT_MATERIAL_KEEP = 3000;
	const int PLAYERBOT_YSHOP_FREE_CELLS = 4;	// free cells left in the bag after an elixir
	const DWORD PLAYERBOT_YSHOP_ERRAND_GAP_MS = 30 * 60 * 1000;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
	const DWORD PLAYERBOT_YSHOP_WANTED_LOG_MS = 5 * 60 * 1000;	// the "errand wanted" line at most this often a bot
#endif
	const DWORD PLAYERBOT_YSHOP_NEED_MS = 30 * 1000;
	const DWORD PLAYERBOT_YSHOP_TICK_MS = 5 * 1000;
	const DWORD PLAYERBOT_YSHOP_DRESS_LOOK_MS = 60 * 1000;	// the dress looked at again without a change of map
	const DWORD PLAYERBOT_YSHOP_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT = 150;
	const int PLAYERBOT_YSHOP_DUST_PURSE_PCT = 25;
	const int PLAYERBOT_YSHOP_LINE_SLACK = 20;	// a market line at most this much over what is short
	const BYTE PLAYERBOT_YSHOP_JEWEL_WEARS[3] = { WEAR_WRIST, WEAR_NECK, WEAR_EAR };

	// The stock a kind is filled to, and the mark under which the errand is called for it.
	int GetPlayerBotYshopTarget(bool power)
	{
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		if (!power)
			return PLAYERBOT_YSHOP_RESIST_TARGET;
#endif
		return power ? PLAYERBOT_YSHOP_TARGET : PLAYERBOT_YSHOP_TARGET;
	}

	int GetPlayerBotYshopLow(bool power)
	{
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		if (!power)
			return PLAYERBOT_YSHOP_RESIST_LOW;
#endif
		return power ? PLAYERBOT_YSHOP_LOW : PLAYERBOT_YSHOP_LOW;
	}

	struct TPlayerBotYoharaShopNeed
	{
		DWORD dwAt;
		long lMap;
		int iMaterials, iDust;	// inputs wanted (ten an elixir short of the target, capped)
		bool bLow;	// a needed kind under PLAYERBOT_YSHOP_LOW
		bool abResist[PLAYERBOT_YOHARA_ELEMENTS], abPower[PLAYERBOT_YOHARA_ELEMENTS];
		TPlayerBotYoharaShopNeed() : dwAt(0), lMap(0), iMaterials(0), iDust(0), bLow(false)
		{
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				abResist[e] = abPower[e] = false;
		}
	};
	std::map<DWORD, TPlayerBotYoharaShopNeed> s_mapPlayerBotYoharaShopNeed;

	struct TPlayerBotYoharaShopBot
	{
		DWORD dwNextTick, dwLastErrand, dwKeptAt, dwWillAt, dwNextDressLook;
		int iDressed;	// -1 unknown, 0 world, 1 Sung Ma
		std::set<DWORD> setKept;	// world set and jade kept, item ids
		int aiWillDelta[4];
		DWORD dwWantedLogAt;	// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: the last "errand wanted" line
		TPlayerBotYoharaShopBot() : dwNextTick(0), dwLastErrand(0), dwKeptAt(0), dwWillAt(0), dwNextDressLook(0), iDressed(-1),
			dwWantedLogAt(0)
		{
			for (int i = 0; i < 4; ++i)
				aiWillDelta[i] = 0;
		}
	};
	std::map<DWORD, TPlayerBotYoharaShopBot> s_mapPlayerBotYoharaShopBot;

	struct TPlayerBotYoharaShopStats
	{
		unsigned int resistMade, powerMade, materialsPaid, dustPaid, errands, dustBought, materialsBought, swaps;
		DWORD dwCensusAt;
		TPlayerBotYoharaShopStats() : resistMade(0), powerMade(0), materialsPaid(0), dustPaid(0), errands(0), dustBought(0),
			materialsBought(0), swaps(0), dwCensusAt(0) {}
	};
	TPlayerBotYoharaShopStats s_kPlayerBotYoharaShopStats;
	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: the dress a score is asked for (0 where the bot stands, 1 Sung Ma, 2 the world).
	int s_iPlayerBotYoharaDressForce = 0;

	// ------------------------------------------------------------ who, and what it needs

	bool IsPlayerBotYoharaShopUser(LPCHARACTER ch)
	{
		return ch && IsPlayerBotSungmaWillUser(ch) && ch->IsItemLoaded() && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

#ifdef MT2009_PLUS_BOT_DUST_MARKET_V1
	// ------------------------------------------------------------ MT2009_PLUS_BOT_DUST_MARKET_V1: producers and the census

	// The census of 31 October (BOTY-YOHARA-ANALIZA-v2.md, item 12; the syslogs of 31.10 10-15h): the Alchemist made 158
	// dust in five hours in the whole world (59 exchanges; most of his 1 000+ visits were for the energy scrap alone),
	// every bot of level 30 and up kept a hundred of it for a marble and spent it on marbles and bonus stones, the G0
	// savers of 110+ kept 400 - not one line of 30360 went up (no "cut a line vnum=30360"), and the Champions'
	// dust_bought stayed 0. Materialy Rzemieslnicze were made (15 750 out of the Dozorca on channel 1 game1) and cut into
	// lines 2 115 times an hour, but the ledger's supply of them stayed 0: the cut lines stood at a counter's yang cap and
	// were poured back (playerbot_offline_shop.h, the room). A producer is a bot of level
	// PLAYERBOT_DUST_PRODUCER_MAX_LEVEL or under without a Champion level - none of the dust's uses is its own (the G0 is
	// the 110+ savers', the elixirs the Champions') - and it lists every unit.
	bool IsPlayerBotDustProducer(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() &&
				(int)ch->GetLevel() <= PLAYERBOT_DUST_PRODUCER_MAX_LEVEL && GetPlayerBotChampionLevel(ch) < 1 &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	bool IsPlayerBotDustMarketGoodsVnum(DWORD vnum)
	{
		return vnum == PLAYERBOT_MAGIC_DUST_VNUM || vnum == PLAYERBOT_YSHOP_MATERIAL_VNUM || vnum == PLAYERBOT_POLISHED_SHELL_VNUM ||
				IsPlayerBotPolishedPearlVnum(vnum);
	}

	enum { PLAYERBOT_DMK_DUST, PLAYERBOT_DMK_MATERIAL, PLAYERBOT_DMK_SHELL, PLAYERBOT_DMK_PEARL, PLAYERBOT_DMK_KINDS };
	const char* const PLAYERBOT_DMK_NAMES[PLAYERBOT_DMK_KINDS] = { "dust", "material", "shell", "pearl" };

	int GetPlayerBotDustMarketKind(DWORD vnum)
	{
		if (vnum == PLAYERBOT_MAGIC_DUST_VNUM)
			return PLAYERBOT_DMK_DUST;
		if (vnum == PLAYERBOT_YSHOP_MATERIAL_VNUM)
			return PLAYERBOT_DMK_MATERIAL;
		if (vnum == PLAYERBOT_POLISHED_SHELL_VNUM)
			return PLAYERBOT_DMK_SHELL;
		return IsPlayerBotPolishedPearlVnum(vnum) ? PLAYERBOT_DMK_PEARL : -1;
	}

	struct TPlayerBotDustMarketStats
	{
		unsigned int auListedUnits[PLAYERBOT_DMK_KINDS], auListedLines[PLAYERBOT_DMK_KINDS];
		unsigned int auYangCapped[PLAYERBOT_DMK_KINDS], auYangRoom[PLAYERBOT_DMK_KINDS];
		unsigned int priceRefused, purseRefused;
		TPlayerBotDustMarketStats() : priceRefused(0), purseRefused(0)
		{
			for (int k = 0; k < PLAYERBOT_DMK_KINDS; ++k)
				auListedUnits[k] = auListedLines[k] = auYangCapped[k] = auYangRoom[k] = 0;
		}
	};
	TPlayerBotDustMarketStats s_kPlayerBotDustMarketStats;

	// A line of the goods put up on a counter (the offline shop's create and add).
	void NotePlayerBotDustMarketListed(DWORD vnum, int units)
	{
		const int k = GetPlayerBotDustMarketKind(vnum);
		if (k < 0 || units <= 0)
			return;
		s_kPlayerBotDustMarketStats.auListedUnits[k] += (unsigned int)units;
		++s_kPlayerBotDustMarketStats.auListedLines[k];
	}

	// A line of the goods refused at a counter's yang cap; room: the counter's dearest line went home for it.
	void NotePlayerBotDustMarketYangCap(DWORD vnum, bool room)
	{
		const int k = GetPlayerBotDustMarketKind(vnum);
		if (k < 0)
			return;
		++s_kPlayerBotDustMarketStats.auYangCapped[k];
		if (room)
			++s_kPlayerBotDustMarketStats.auYangRoom[k];
	}

	// A Champion's look at a dust line refused: over the price cap (price), or over its purse's share.
	void NotePlayerBotDustMarketRefused(bool price)
	{
		if (price)
			++s_kPlayerBotDustMarketStats.priceRefused;
		else
			++s_kPlayerBotDustMarketStats.purseRefused;
	}

	// PLAYERBOT_SHOP2: market census - since the core's start: the goods' lines and units put up on this core's
	// counters, refused at the yang cap and the room made for them; the ledger's units on the counters now; the dust
	// and materials the Champions bought (the G0's and the power elixir's, the G0 / SHOP2 counts) and their refused
	// looks; this core's producers, those holding dust and their dust (it should go to 0 between two counter visits),
	// and the shells in the bags.
	void LogPlayerBotDustMarketCensus()
	{
		const TPlayerBotDustMarketStats& m = s_kPlayerBotDustMarketStats;
		unsigned int producers = 0, holders = 0, held = 0, shells = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded())
				continue;
			shells += (unsigned int)ch->CountSpecifyItem(PLAYERBOT_POLISHED_SHELL_VNUM);
			if (!IsPlayerBotDustProducer(ch))
				continue;
			++producers;
			const int dust = (int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM);
			if (dust > 0)
			{
				++holders;
				held += (unsigned int)dust;
			}
		}
		std::string kinds;
		for (int k = 0; k < PLAYERBOT_DMK_KINDS; ++k)
		{
			DWORD supply = 0;
			if (k == PLAYERBOT_DMK_PEARL)
			{
				for (DWORD v = PLAYERBOT_POLISHED_PEARL_FIRST_VNUM; v <= PLAYERBOT_POLISHED_PEARL_LAST_VNUM; ++v)
				{
					const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(v);
					supply += e ? e->dwSupplyUnits : 0;
				}
			}
			else
			{
				const DWORD v = k == PLAYERBOT_DMK_DUST ? PLAYERBOT_MAGIC_DUST_VNUM
						: (k == PLAYERBOT_DMK_MATERIAL ? PLAYERBOT_YSHOP_MATERIAL_VNUM : PLAYERBOT_POLISHED_SHELL_VNUM);
				const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(v);
				supply = e ? e->dwSupplyUnits : 0;
			}
			char one[160];
			snprintf(one, sizeof(one), " %s=[listed=%u lines=%u on_counters=%u yang_capped=%u yang_room=%u]", PLAYERBOT_DMK_NAMES[k],
					m.auListedUnits[k], m.auListedLines[k], (unsigned int)supply, m.auYangCapped[k], m.auYangRoom[k]);
			kinds += one;
		}
		sys_log(0, "PLAYERBOT_SHOP2: market census%s champion_dust_bought=[g0=%u power=%u] champion_materials_bought=%u "
				"dust_refused=[price=%u purse=%u] producers=%u producers_with_dust=%u producers_dust=%u shells_in_bags=%u",
				kinds.c_str(), s_kPlayerBotG0Stats.dustBought, s_kPlayerBotYoharaShopStats.dustBought,
				s_kPlayerBotYoharaShopStats.materialsBought, m.priceRefused, m.purseRefused, producers, holders, held, shells);
	}
#endif

	int GetPlayerBotYoharaShopDustFree(LPCHARACTER ch)
	{
		return ch ? std::max(0, (int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM) - GetPlayerBotG0DustReserve(ch)) : 0;
	}

	const TPlayerBotYoharaShopNeed* GetPlayerBotYoharaShopNeed(LPCHARACTER ch)
	{
		if (!IsPlayerBotYoharaShopUser(ch))
			return NULL;
		const long map = GetPlayerBotYoharaElementMap(ch);
		if (map == 0)
			return NULL;
		const DWORD now = get_dword_time();
		TPlayerBotYoharaShopNeed& n = s_mapPlayerBotYoharaShopNeed[ch->GetPlayerID()];
		if (n.dwAt != 0 && n.lMap == map && now - n.dwAt < PLAYERBOT_YSHOP_NEED_MS)
			return &n;
		n = TPlayerBotYoharaShopNeed();
		n.dwAt = now ? now : 1;
		n.lMap = map;
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYoharaMapShares(map, share);
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: a bot with a hunt element stocks that element's elixirs only.
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		int resistShort = 0, powerShort = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			if (hunt >= 0 ? e != hunt : share[e] < PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT)
				continue;
			n.abResist[e] = true;
			const int resist = (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]);
			resistShort += std::max(0, GetPlayerBotYshopTarget(false) - resist);
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
			n.abPower[e] = true;
			const int power = (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[e]);
			powerShort += std::max(0, GetPlayerBotYshopTarget(true) - power);
			if (power < GetPlayerBotYshopLow(true))
				n.bLow = true;
#endif
			if (resist < GetPlayerBotYshopLow(false))
				n.bLow = true;
		}
		n.iMaterials = std::min(PLAYERBOT_YSHOP_INPUT_MAX, resistShort * PLAYERBOT_YSHOP_RATE);
		n.iDust = std::min(PLAYERBOT_YSHOP_INPUT_MAX, powerShort * PLAYERBOT_YSHOP_RATE);
		return &n;
	}

	void ForgetPlayerBotYoharaShopNeed(LPCHARACTER ch)
	{
		if (ch)
			s_mapPlayerBotYoharaShopNeed.erase(ch->GetPlayerID());
	}

	int GetPlayerBotYoharaShopMaterialsWanted(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		return n ? n->iMaterials : 0;
	}

	// The dust over the G0 reserve kept off the counters, the marbles and the bonus stones.
	int GetPlayerBotYoharaShopDustKeep(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		return n ? n->iDust : 0;
	}

	bool IsPlayerBotYoharaElixirVnum(DWORD vnum)
	{
		return vnum >= 50830 && vnum <= 50841;
	}

	// ------------------------------------------------------------ the market

	bool WantsPlayerBotYoharaShopDustOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || offer->GetVnum() != PLAYERBOT_MAGIC_DUST_VNUM || IsPlayerBotG0DustHunter(ch))
			return false;
		const int want = GetPlayerBotYoharaShopDustKeep(ch);
		const int have = GetPlayerBotYoharaShopDustFree(ch);
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
		if (!AllowsPlayerBotPowerDustMarket(ch, (int)offer->GetCount()))	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the budget
			return false;
#endif
		return want > 0 && have < want && (int)offer->GetCount() <= want - have + PLAYERBOT_YSHOP_LINE_SLACK;
	}

	bool CanPlayerBotPayForYoharaShopDust(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long units = std::max<long long>(1, (long long)item->GetCount());
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
		// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the G0 dust's price cap, and the day's units and the counters' floor
		if (!AllowsPlayerBotPowerDustMarket(ch, (int)units))
			return false;
		const long long cap = (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_PRIOR_MAGIC_DUST) * PLAYERBOT_G0_DUST_PRICE_CAP_PCT / 100;
#else
		const long long cap = (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_PRIOR_MAGIC_DUST) * PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT / 100;
#endif
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
#ifdef MT2009_PLUS_BOT_DUST_MARKET_V1
		// MT2009_PLUS_BOT_DUST_MARKET_V1: the refusals counted for the market census
		if (price > cap * units)
		{
			NotePlayerBotDustMarketRefused(true);
			return false;
		}
		if (price > spare * PLAYERBOT_YSHOP_DUST_PURSE_PCT / 100)
		{
			NotePlayerBotDustMarketRefused(false);
			return false;
		}
		return true;
#else
		return price <= cap * units && price <= spare * PLAYERBOT_YSHOP_DUST_PURSE_PCT / 100;
#endif
	}

	bool PlayerBotYoharaShopWantsDustFromMarket(LPCHARACTER ch)
	{
		if (IsPlayerBotG0DustHunter(ch) || GetPlayerBotYoharaShopDustFree(ch) >= GetPlayerBotYoharaShopDustKeep(ch))
			return false;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
		if (!AllowsPlayerBotPowerDustMarket(ch, 1))	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the budget and the floor
			return false;
#endif
		const TPlayerBotMarketLedgerEntry* dust = GetPlayerBotMarketLedgerEntry(PLAYERBOT_MAGIC_DUST_VNUM);
		return dust && dust->dwSupplyUnits > 0;
	}

	// A trade trip's "buy": a kind is low, and the market holds the input that is short.
	bool PlayerBotYoharaShopWantsMarket(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n || !n->bLow)
			return false;
		if (PlayerBotYoharaShopWantsDustFromMarket(ch))
			return true;
		if ((int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM) < n->iMaterials)
		{
			const TPlayerBotMarketLedgerEntry* mats = GetPlayerBotMarketLedgerEntry(PLAYERBOT_YSHOP_MATERIAL_VNUM);
			return mats && mats->dwSupplyUnits > 0;
		}
		return false;
	}

	void NotePlayerBotYoharaShopBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!ch || (vnum != PLAYERBOT_MAGIC_DUST_VNUM && vnum != PLAYERBOT_YSHOP_MATERIAL_VNUM) || !IsPlayerBotYoharaShopUser(ch))
			return;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n || (vnum == PLAYERBOT_MAGIC_DUST_VNUM ? n->iDust : n->iMaterials) <= 0)
			return;
		if (vnum == PLAYERBOT_MAGIC_DUST_VNUM)
		{
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
			// MT2009_PLUS_BOT_G0_DUST_RULE_V1: a G0 saver's dust is the G0's line (NotePlayerBotG0DustBought), not the
			// power elixir's budget
			if (GetPlayerBotG0DustReserve(ch) > 0)
				return;
			NotePlayerBotPowerDustMarket(ch, (int)count);
#endif
			s_kPlayerBotYoharaShopStats.dustBought += count;
		}
		else
			s_kPlayerBotYoharaShopStats.materialsBought += count;
		sys_log(0, "PLAYERBOT_SHOP2: %s bought pid=%u name=%s count=%u price=%lld have=%d want=%d",
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? "dust" : "material", ch->GetPlayerID(), ch->GetName(), (unsigned int)count, price,
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? GetPlayerBotYoharaShopDustFree(ch) : (int)ch->CountSpecifyItem(vnum),
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? n->iDust : n->iMaterials);
	}

	// ------------------------------------------------------------ the exchange at Handlarka Roznosci

	// The materials the exchange may take: the bag's, less what the horse still keeps.
	int GetPlayerBotYoharaShopMaterialsFree(LPCHARACTER ch)
	{
		const int held = (int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM);
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: a bot with a hunt element - its elixir first
		if (GetPlayerBotHuntElement(ch) > 0)
			return held;
		const int others = std::max(0, GetPlayerBotCraftMaterialsWanted(ch, false) - GetPlayerBotYoharaShopMaterialsWanted(ch));
		return std::max(0, held - others);
	}

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	// A bag stack of the elixir at the exchange's values (20% / 600 s) with room for one more, NULL for none.
	LPITEM FindPlayerBotElixirStack(LPCHARACTER ch, DWORD elixir)
	{
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && item->GetVnum() == elixir && item->GetType() == ITEM_BLEND &&
					!item->isLocked() && item->GetSocket(1) == 20 && item->GetSocket(2) == 600 &&
					item->GetCount() > 0 && item->GetCount() < item->GetMaxStack())
				return item;
		}
		return NULL;
	}
#endif

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V4 (the census of 28 October 14:51: fire stock_avg 5.4, elixir_up 73%, no_stock 791
	// against 85-95% elsewhere). Not the errand: a bot living on Dongan goes to Handlarka as any other (its potion errands
	// ran the exchange and filled its stock to 16 - DIABELLEKv3 13:40). The fire bots without elixirs were the older
	// bots that live on Dongan with a full bag (2090, 2172, 619, 238, ...: "bag full" every few minutes, 0-3 free
	// cells): the errand for the exchange was never asked for (more than PLAYERBOT_YSHOP_FREE_CELLS free cells wanted),
	// and their potion errands' exchange made nothing ("exchange none ... free_cells=0 elixirs=0"). The elixir does not
	// stack (item_proto stack 1 for 50830-50841 - V3's stacking never happened), so every one needs a cell. Now:
	//   * the hunt element's resistance elixir takes the bag's last free cells, and at Handlarka the cheapest thing in
	//     the bag is sold for a cell (the rule of the cohort's potion cell, RestockPlayerBotYohara) - at most the
	//     target's count of things an exchange;
	//   * the errand for it is asked for with a full bag when such a thing is there;
	//   * the errand's gap (PLAYERBOT_YSHOP_ERRAND_GAP_MS) runs from an errand that started
	//     (NotePlayerBotYoharaShopErrandStarted) - the ask set it before, and a bot in a fight at the look (the errand
	//     put off) waited 30 minutes for the next ask: 60-85% of the asks on every map started no errand.
	// Other kinds (the power elixirs, a bot's second element) keep the bag's reserve.
	bool IsPlayerBotYoharaJadeVnum(DWORD vnum);
	bool IsPlayerBotYoharaShopKept(LPCHARACTER ch, LPITEM item);

	// Room in the bag for one more of an elixir: its stack, or a free cell - the hunt element's resistance down to the
	// last one, the rest over the reserve.
	bool HasPlayerBotYshopRoom(LPCHARACTER ch, DWORD elixir, bool hunt)
	{
		if (FindPlayerBotElixirStack(ch, elixir))
			return true;
		return CountPlayerBotFreeInventoryCells(ch) > (hunt ? 0 : PLAYERBOT_YSHOP_FREE_CELLS);
	}

	// The cheapest thing in the bag that may be sold for a cell: never worn, locked, a quest item, a potion, the watch,
	// a kept or policy item, the second set, a sidekick's - nor the exchange's inputs and elixirs, a jade or the world
	// set, a kept talisman or craft material. NULL for none.
	LPITEM FindPlayerBotYshopCellToFree(LPCHARACTER ch, long long& price)
	{
		LPITEM cheapest = NULL;
		price = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->isLocked() || item->GetType() == ITEM_QUEST ||
					item->GetVnum() == PLAYERBOT_YOHARA_SZC_WATCH || (item->GetVnum() >= 27001 && item->GetVnum() <= 27008) ||
					item->GetVnum() == PLAYERBOT_YSHOP_MATERIAL_VNUM || item->GetVnum() == PLAYERBOT_MAGIC_DUST_VNUM ||
					IsPlayerBotYoharaElixirVnum(item->GetVnum()) || IsPlayerBotYoharaJadeVnum(item->GetVnum()) ||
					GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE || IsPlayerBotMlodziKept(ch, item) ||
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
					IsPlayerBotSecondSetStored(ch, item) ||
#endif
					IsPlayerBotYoharaShopKept(ch, item) || IsPlayerBotKeptTalisman(ch, item) ||
					IsPlayerBotKeptCraftMaterial(ch, item) || IsPlayerBotSidekickLockedItem(ch, item) ||
					IsPlayerBotSidekickPinned(ch, item))
				continue;
			const long long p = GetPlayerBotJunkSalePrice(item);
			if (!cheapest || p < price)
			{
				cheapest = item;
				price = p;
			}
		}
		return cheapest;
	}

	// At Handlarka: the cheapest thing sold for a cell, at the merchant's price. True when a cell is free after.
	bool FreePlayerBotYshopCell(LPCHARACTER ch, DWORD npc, int e)
	{
		for (int tries = 0; tries < 2 && CountPlayerBotFreeInventoryCells(ch) <= 0; ++tries)
		{
			long long price = 0;
			LPITEM item = FindPlayerBotYshopCellToFree(ch, price);
			if (!item)
				break;
			sys_log(0, "PLAYERBOT_SHOP2: cell freed pid=%u name=%s npc=%u element=%s vnum=%u count=%u gold=%lld elixirs=%d",
					ch->GetPlayerID(), ch->GetName(), npc, PLAYERBOT_YOHARA_ELEMENT_NAMES[e], item->GetVnum(),
					(unsigned int)item->GetCount(), price, (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]));
			PlayerBotChangeGold(ch, price);
			ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_SHOP2_CELL");
		}
		return CountPlayerBotFreeInventoryCells(ch) > 0;
	}
#endif

	// One kind filled towards the target from one input; the elixirs made.
	int ExchangePlayerBotYoharaShopKind(LPCHARACTER ch, long map, int e, bool power, DWORD npc)
	{
		const DWORD elixir = power ? PLAYERBOT_YOHARA_POWER_ELIXIRS[e] : PLAYERBOT_YOHARA_RESIST_ELIXIRS[e];
		const DWORD input = power ? PLAYERBOT_MAGIC_DUST_VNUM : PLAYERBOT_YSHOP_MATERIAL_VNUM;
		int made = 0;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: the hunt element's resistance into the last free cell, and a cell sold free
		const bool hunt = !power && e == (int)GetPlayerBotHuntElement(ch) - 1;
		int freed = 0;
		while ((int)ch->CountSpecifyItem(elixir) < GetPlayerBotYshopTarget(power) &&
				(power ? GetPlayerBotYoharaShopDustFree(ch) : GetPlayerBotYoharaShopMaterialsFree(ch)) >= PLAYERBOT_YSHOP_RATE)
		{
			if (!HasPlayerBotYshopRoom(ch, elixir, hunt))
			{
				if (!hunt || freed >= GetPlayerBotYshopTarget(false) || !FreePlayerBotYshopCell(ch, npc, e))
					break;
				++freed;
			}
#else
		while ((int)ch->CountSpecifyItem(elixir) < GetPlayerBotYshopTarget(power) &&
				(power ? GetPlayerBotYoharaShopDustFree(ch) : GetPlayerBotYoharaShopMaterialsFree(ch)) >= PLAYERBOT_YSHOP_RATE &&
				CountPlayerBotFreeInventoryCells(ch) > PLAYERBOT_YSHOP_FREE_CELLS)
		{
#endif
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: onto a stack of the same elixir at 20% / 10 minutes when the bag holds
			// one with room (the engine stacks a blend item only of equal sockets, and the new one is set to them after
			// it is given - every elixir took a cell of its own, and a stock of 16 would be 16 cells).
			LPITEM stack = FindPlayerBotElixirStack(ch, elixir);
			if (stack)
			{
				ch->RemoveSpecifyItem(input, PLAYERBOT_YSHOP_RATE);
				stack->SetCount(stack->GetCount() + 1);
				LPITEM item = stack;
				++made;
				if (power)
				{
					++s_kPlayerBotYoharaShopStats.powerMade;
					s_kPlayerBotYoharaShopStats.dustPaid += PLAYERBOT_YSHOP_RATE;
				}
				else
				{
					++s_kPlayerBotYoharaShopStats.resistMade;
					s_kPlayerBotYoharaShopStats.materialsPaid += PLAYERBOT_YSHOP_RATE;
				}
				sys_log(0, "PLAYERBOT_SHOP2: exchange pid=%u name=%s npc=%u map=%ld for_map=%ld kind=%s element=%s paid=%d paid_vnum=%u got=%u value=%ld seconds=%ld have=%d input_left=%d stacked=1",
						ch->GetPlayerID(), ch->GetName(), npc, ch->GetMapIndex(), map, power ? "power" : "resist",
						PLAYERBOT_YOHARA_ELEMENT_NAMES[e], PLAYERBOT_YSHOP_RATE, input, elixir, (long)item->GetSocket(1),
						(long)item->GetSocket(2), (int)ch->CountSpecifyItem(elixir), (int)ch->CountSpecifyItem(input));
				continue;
			}
#endif
			ch->RemoveSpecifyItem(input, PLAYERBOT_YSHOP_RATE);
			LPITEM item = ch->AutoGiveItem(elixir, 1, -1, false);
			if (!item)
			{
				ch->AutoGiveItem(input, PLAYERBOT_YSHOP_RATE, -1, false);	// no room after all: the input back
				break;
			}
			// MT2009_PLUS_BOT_YOHARA_SHOP_V2: the bots' elixir at its best, always (the owner, 22 October: "dla botow tylko
			// maksymalne wartosci, czyli 20% i 10 minut") - the rolled value and time set to the cube's top (socket 1 the
			// percent, socket 2 the seconds; socket 0, the point, as made).
			item->SetSocket(1, 20);
			item->SetSocket(2, 600);
			LogManager::instance().ItemLog(ch, item, "PLAYERBOT_SHOP2", power ? "dust" : "materials");
			++made;
			if (power)
			{
				++s_kPlayerBotYoharaShopStats.powerMade;
				s_kPlayerBotYoharaShopStats.dustPaid += PLAYERBOT_YSHOP_RATE;
			}
			else
			{
				++s_kPlayerBotYoharaShopStats.resistMade;
				s_kPlayerBotYoharaShopStats.materialsPaid += PLAYERBOT_YSHOP_RATE;
			}
			sys_log(0, "PLAYERBOT_SHOP2: exchange pid=%u name=%s npc=%u map=%ld for_map=%ld kind=%s element=%s paid=%d paid_vnum=%u got=%u value=%ld seconds=%ld have=%d input_left=%d",
					ch->GetPlayerID(), ch->GetName(), npc, ch->GetMapIndex(), map, power ? "power" : "resist",
					PLAYERBOT_YOHARA_ELEMENT_NAMES[e], PLAYERBOT_YSHOP_RATE, input, elixir, (long)item->GetSocket(1),
					(long)item->GetSocket(2), (int)ch->CountSpecifyItem(elixir), (int)ch->CountSpecifyItem(input));
		}
		return made;
	}

	// At Dongan's Handlarka Roznosci (Dongan's errand, playerbot_yohara_sungma.h): every needed kind filled towards the
	// target - the map's top element first, resistance before power. The elixirs made.
	int RunPlayerBotYoharaShopExchange(LPCHARACTER ch, DWORD npc)
	{
		if (npc != PLAYERBOT_YSHOP_NPC || !ch || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() ||
				GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) != GetPlayerBotYoharaElementSlot(PLAYERBOT_MAP_SUNGMA_DONGAN))
			return 0;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n)
			return 0;
		const long map = n->lMap;
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYoharaMapShares(map, share);
		int order[PLAYERBOT_YOHARA_ELEMENTS];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			order[e] = e;
		for (int i = 1; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			for (int j = i; j > 0 && share[order[j]] > share[order[j - 1]]; --j)
				std::swap(order[j], order[j - 1]);
		bool resist[PLAYERBOT_YOHARA_ELEMENTS], power[PLAYERBOT_YOHARA_ELEMENTS];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			resist[e] = n->abResist[e];
			power[e] = n->abPower[e];
		}
		int made = 0;
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			if (resist[order[i]])
				made += ExchangePlayerBotYoharaShopKind(ch, map, order[i], false, npc);
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			if (power[order[i]])
				made += ExchangePlayerBotYoharaShopKind(ch, map, order[i], true, npc);
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: why a bot low on its hunt element's elixir got none
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		if (made == 0 && hunt >= 0 && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[hunt]) < GetPlayerBotYshopLow(false))
			PlayerBotLogThrottled("yshop_exchange_none", get_dword_time(),
					"PLAYERBOT_SHOP2: exchange none pid=%u name=%s for_map=%ld element=%s materials=%d materials_free=%d free_cells=%d elixirs=%d",
					ch->GetPlayerID(), ch->GetName(), map, PLAYERBOT_YOHARA_ELEMENT_NAMES[hunt],
					(int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM), GetPlayerBotYoharaShopMaterialsFree(ch),
					CountPlayerBotFreeInventoryCells(ch), (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[hunt]));
		ForgetPlayerBotYoharaShopNeed(ch);
		if (made > 0)
			sys_log(0, "PLAYERBOT_SHOP2: exchange done pid=%u name=%s for_map=%ld made=%d materials=%d dust=%d dust_reserve=%d",
					ch->GetPlayerID(), ch->GetName(), map, made, (int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM),
					(int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM), GetPlayerBotG0DustReserve(ch));
		return made;
	}

	// Dongan's errand for the exchange (GetPlayerBotSungmaErrandNeed): on its Sung Ma map, a needed kind under the low
	// mark with the input for one of it, room in the bag, not more often than PLAYERBOT_YSHOP_ERRAND_GAP_MS.
	bool PlayerBotYoharaShopWantsErrand(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch || GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) < 0)
			return false;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: the room asked for each kind below (a full bag no bar to the hunt element's)
		if (!n || !n->bLow)
			return false;
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		long long cellPrice = 0;
#else
		if (!n || !n->bLow || CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_YSHOP_FREE_CELLS)
			return false;
#endif
		TPlayerBotYoharaShopBot& b = s_mapPlayerBotYoharaShopBot[ch->GetPlayerID()];
		if (b.dwLastErrand != 0 && dwNow - b.dwLastErrand < PLAYERBOT_YSHOP_ERRAND_GAP_MS)
			return false;
		const bool materials = GetPlayerBotYoharaShopMaterialsFree(ch) >= PLAYERBOT_YSHOP_RATE;
		const bool dust = GetPlayerBotYoharaShopDustFree(ch) >= PLAYERBOT_YSHOP_RATE;
		const char* kind = NULL;
		const char* element = NULL;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS && !kind; ++e)
		{
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
			if (materials && n->abResist[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]) < GetPlayerBotYshopLow(false) &&
					(HasPlayerBotYshopRoom(ch, PLAYERBOT_YOHARA_RESIST_ELIXIRS[e], e == hunt) ||
					 (e == hunt && FindPlayerBotYshopCellToFree(ch, cellPrice) != NULL)))
				kind = "resist", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
			else if (dust && n->abPower[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[e]) < GetPlayerBotYshopLow(true) &&
					HasPlayerBotYshopRoom(ch, PLAYERBOT_YOHARA_POWER_ELIXIRS[e], false))
				kind = "power", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
#else
			if (materials && n->abResist[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]) < GetPlayerBotYshopLow(false))
				kind = "resist", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
			else if (dust && n->abPower[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[e]) < GetPlayerBotYshopLow(true))
				kind = "power", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
#endif
		}
		if (!kind)
			return false;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: asked again at every look until the errand goes (a fight puts it off); its
		// line once in PLAYERBOT_YSHOP_WANTED_LOG_MS a bot
		if (b.dwWantedLogAt != 0 && dwNow - b.dwWantedLogAt < PLAYERBOT_YSHOP_WANTED_LOG_MS)
			return true;
		b.dwWantedLogAt = dwNow ? dwNow : 1;
		sys_log(0, "PLAYERBOT_SHOP2: errand wanted pid=%u name=%s map=%ld for_map=%ld kind=%s element=%s materials=%d dust_free=%d free_cells=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), n->lMap, kind, element,
				(int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM), GetPlayerBotYoharaShopDustFree(ch),
				CountPlayerBotFreeInventoryCells(ch));
		return true;
#else
		b.dwLastErrand = dwNow ? dwNow : 1;
		++s_kPlayerBotYoharaShopStats.errands;
		sys_log(0, "PLAYERBOT_SHOP2: errand wanted pid=%u name=%s map=%ld for_map=%ld kind=%s element=%s materials=%d dust_free=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), n->lMap, kind, element,
				(int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM), GetPlayerBotYoharaShopDustFree(ch));
		return true;
#endif
	}

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: Dongan's errand started with the exchange in its need (ManagePlayerBotSungmaErrand)
	// - the errand's gap from now.
	void NotePlayerBotYoharaShopErrandStarted(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		s_mapPlayerBotYoharaShopBot[ch->GetPlayerID()].dwLastErrand = dwNow ? dwNow : 1;
		++s_kPlayerBotYoharaShopStats.errands;
	}
#endif

	// ------------------------------------------------------------ the world set (item 24)

	bool IsPlayerBotYoharaJadeVnum(DWORD vnum)
	{
		return (vnum >= 14580 && vnum <= 14619) || (vnum >= 16580 && vnum <= 16619) || (vnum >= 17570 && vnum <= 17609);
	}

	// Whether the bot dresses for the Sung Ma maps (its Will counts): standing on one of them - or asked so.
	bool IsPlayerBotDressedForSungma(LPCHARACTER ch)
	{
		if (s_iPlayerBotYoharaDressForce != 0)
			return s_iPlayerBotYoharaDressForce == 1;
		return ch && GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) >= 0;
	}

	long long ScorePlayerBotYoharaDress(LPCHARACTER ch, LPITEM item, int dress)
	{
		const int was = s_iPlayerBotYoharaDressForce;
		s_iPlayerBotYoharaDressForce = dress;
		const long long score = GetPlayerBotEquipmentScore(item, ch);
		s_iPlayerBotYoharaDressForce = was;
		return score;
	}

	// The best piece of a jewellery slot the bot owns (worn or in the bag) for a dress (1 Sung Ma, 2 the world, 0 where
	// it stands); family 0 any, 1 jade only, 2 no jade.
	LPITEM FindPlayerBotYoharaJewel(LPCHARACTER ch, BYTE wear, int dress, int family, long long* scoreOut)
	{
		LPITEM best = NULL;
		long long bestScore = 0;
		LPITEM worn = ch->GetWear(wear);
		for (int cell = -1; cell < (int)PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = cell < 0 ? worn : ch->GetInventoryItem((WORD)cell);
			if (!item || (cell >= 0 && (item->GetCell() != cell || item->IsEquipped())))
				continue;
			const bool jade = IsPlayerBotYoharaJadeVnum(item->GetVnum());
			if ((family == 1 && !jade) || (family == 2 && jade))
				continue;
			if (cell >= 0 && (item->GetType() != ITEM_ARMOR || !IsPlayerBotEquipmentCandidate(ch, item) ||
					item->GetLevelLimit() > ch->GetLevel() || item->FindEquipCell(ch) != wear))
				continue;
			const long long score = ScorePlayerBotYoharaDress(ch, item, dress);
			// the worn piece wins a tie
			if (!best || score > bestScore || (score == bestScore && item == worn))
			{
				best = item;
				bestScore = score;
			}
		}
		if (scoreOut)
			*scoreOut = bestScore;
		return best;
	}

	bool OwnsPlayerBotYoharaJade(LPCHARACTER ch, BYTE wear)
	{
		return FindPlayerBotYoharaJewel(ch, wear, 1, 1, NULL) != NULL;
	}

	TPlayerBotYoharaShopBot& GetPlayerBotYoharaShopBot(LPCHARACTER ch)
	{
		return s_mapPlayerBotYoharaShopBot[ch->GetPlayerID()];
	}

	// The kept pieces of a Champion with jade: per jewellery slot with a jade piece, its best jade (Sung Ma's score) and
	// its best other piece (the world's score). Refreshed every half minute.
	const std::set<DWORD>& GetPlayerBotYoharaKeptJewels(LPCHARACTER ch)
	{
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		const DWORD now = get_dword_time();
		if (b.dwKeptAt != 0 && now - b.dwKeptAt < PLAYERBOT_YSHOP_NEED_MS)
			return b.setKept;
		b.dwKeptAt = now ? now : 1;
		b.setKept.clear();
		if (!IsPlayerBotYoharaShopUser(ch))
			return b.setKept;
		for (int i = 0; i < 3; ++i)
		{
			LPITEM jade = FindPlayerBotYoharaJewel(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i], 1, 1, NULL);
			if (!jade)
				continue;
			b.setKept.insert(jade->GetID());
			LPITEM world = FindPlayerBotYoharaJewel(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i], 2, 2, NULL);
			if (world)
				b.setKept.insert(world->GetID());
		}
		return b.setKept;
	}

	// Kept off the merchant, the counters and the other bots: the world set and its jade (above), the elixirs of Yohara
	// up to PLAYERBOT_YSHOP_KEEP_MAX of a vnum, the materials the exchange wants (the dust has the counters' dust keep).
	bool IsPlayerBotYoharaShopKept(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotYoharaShopUser(ch))
			return false;
		const DWORD vnum = item->GetVnum();
		if (IsPlayerBotYoharaElixirVnum(vnum))
			return CountPlayerBotVnumUnitsAhead(ch, item) < PLAYERBOT_YSHOP_KEEP_MAX;
		if (vnum == PLAYERBOT_YSHOP_MATERIAL_VNUM)
		{
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: a bot with a hunt element keeps its elixirs' stock
			const int keep = std::max(GetPlayerBotYoharaShopMaterialsWanted(ch),
					GetPlayerBotHuntElement(ch) > 0 ? PLAYERBOT_YSHOP_HUNT_MATERIAL_KEEP : 0);
			return keep > 0 && CountPlayerBotVnumUnitsAhead(ch, item) < keep;
		}
		if (item->GetType() != ITEM_ARMOR || (item->GetSubType() != ARMOR_WRIST && item->GetSubType() != ARMOR_NECK &&
				item->GetSubType() != ARMOR_EAR))
			return false;
		return GetPlayerBotYoharaKeptJewels(ch).count(item->GetID()) != 0;
	}

	// The G0 sale (IsPlayerBotG0PieceReplaced): a kept jade piece is not replaced, whatever the dress.
	bool IsPlayerBotYoharaWorldSetKeptJade(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && IsPlayerBotYoharaJadeVnum(item->GetVnum()) && IsPlayerBotYoharaShopKept(ch, item);
	}

	// GetPlayerBotSungmaWill: while dressed for the world, the Will the jade in the bag would bring back on a Sung Ma
	// map (its lines over the worn piece's, per jewellery slot), with the Will's per cent bonus.
	int GetPlayerBotYoharaWorldSetWillDelta(LPCHARACTER ch, int what)
	{
		if (what < 0 || what > 3 || !ch || IsPlayerBotDressedForSungma(ch) || !IsPlayerBotYoharaShopUser(ch))
			return 0;
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		const DWORD now = get_dword_time();
		if (b.dwWillAt == 0 || now - b.dwWillAt >= PLAYERBOT_YSHOP_TICK_MS)
		{
			b.dwWillAt = now ? now : 1;
			static const BYTE s_aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
			for (int k = 0; k < 4; ++k)
				b.aiWillDelta[k] = 0;
			for (int i = 0; i < 3; ++i)
			{
				const BYTE wear = PLAYERBOT_YSHOP_JEWEL_WEARS[i];
				LPITEM worn = ch->GetWear(wear);
				LPITEM best = FindPlayerBotYoharaJewel(ch, wear, 1, 0, NULL);
				if (!best || best == worn)
					continue;
				for (int k = 0; k < 4; ++k)
					b.aiWillDelta[k] += (int)SumPlayerBotItemLines(best, s_aPoint[k]) - (worn ? (int)SumPlayerBotItemLines(worn, s_aPoint[k]) : 0);
			}
			for (int k = 0; k < 4; ++k)
			{
				const int pct = std::max(-100, (int)ch->GetPoint(POINT_SUNGMA_PER_STR + k));
				b.aiWillDelta[k] = b.aiWillDelta[k] * (100 + pct) / 100;
			}
		}
		return b.aiWillDelta[what];
	}

	// The swap: each jewellery slot to its best piece for where the bot stands (the equipment pass's score), at once.
	int WearPlayerBotYoharaDress(LPCHARACTER ch, bool sungma)
	{
		int swapped = 0;
		for (int i = 0; i < 3; ++i)
		{
			const BYTE wear = PLAYERBOT_YSHOP_JEWEL_WEARS[i];
			LPITEM worn = ch->GetWear(wear);
			long long bestScore = 0;
			LPITEM best = FindPlayerBotYoharaJewel(ch, wear, 0, 0, &bestScore);
			if (!best || best == worn)
				continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
			// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1: the element set's worn jewellery stays until the set swap
			if (worn && IsPlayerBotSecondSetWornLocked(ch, worn))
				continue;
#endif
			if (worn && (IsPlayerBotSidekickLockedItem(ch, worn) || ch->GetEmptyInventory(worn->GetSize()) < 0 ||
					!ch->UnequipItem(worn) || worn->IsEquipped()))
				continue;
			if (!ch->EquipItem(best))
			{
				if (worn && !worn->IsEquipped())
					ch->EquipItem(worn);
				continue;
			}
			++swapped;
			++s_kPlayerBotYoharaShopStats.swaps;
			sys_log(0, "PLAYERBOT_SHOP2: worldset swap pid=%u name=%s map=%ld dress=%s wear=%d vnum=%u old=%u",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), sungma ? "sungma" : "world", (int)wear, best->GetVnum(),
					worn ? worn->GetVnum() : 0);
		}
		return swapped;
	}

	void LogPlayerBotYoharaShopCensus()
	{
		const TPlayerBotYoharaShopStats& s = s_kPlayerBotYoharaShopStats;
		sys_log(0, "PLAYERBOT_SHOP2: census resist_made=%u power_made=%u materials_paid=%u dust_paid=%u errands=%u dust_bought=%u materials_bought=%u worldset_swaps=%u bots=%u",
				s.resistMade, s.powerMade, s.materialsPaid, s.dustPaid, s.errands, s.dustBought, s.materialsBought, s.swaps,
				(unsigned int)s_mapPlayerBotYoharaShopBot.size());
#ifdef MT2009_PLUS_BOT_DUST_MARKET_V1
		LogPlayerBotDustMarketCensus();	// MT2009_PLUS_BOT_DUST_MARKET_V1
#endif
	}

	// The AI's tick (playerbot_manager.cpp, beside the G0 look; never owns the tick): the world set's dress on the bot's
	// own clock, out of a fight. A dress changed asks the equipment pass too.
	void ManagePlayerBotYoharaShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_kPlayerBotYoharaShopStats.dwCensusAt == 0 || (int)(dwNow - s_kPlayerBotYoharaShopStats.dwCensusAt) >= 0)
		{
			if (s_kPlayerBotYoharaShopStats.dwCensusAt != 0)
				LogPlayerBotYoharaShopCensus();
			s_kPlayerBotYoharaShopStats.dwCensusAt = dwNow + PLAYERBOT_YSHOP_CENSUS_MS;
		}
		if (!IsPlayerBotYoharaShopUser(ch) || ch->IsDead())
			return;
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		if (b.dwNextTick != 0 && (int)(dwNow - b.dwNextTick) < 0)
			return;
		b.dwNextTick = dwNow + PLAYERBOT_YSHOP_TICK_MS;
		if (state.dwTargetVID != 0 || ch->GetVictim() || ch->GetExchange() || ch->GetMyShop() || IsPlayerBotGearFrozen(ch))
			return;
		const bool sungma = IsPlayerBotDressedForSungma(ch);
		const int dress = sungma ? 1 : 0;
		const bool changed = b.iDressed != dress;
		if (!changed && (int)(dwNow - b.dwNextDressLook) < 0)
			return;
		b.dwNextDressLook = dwNow + PLAYERBOT_YSHOP_DRESS_LOOK_MS;
		if (changed)
		{
			b.iDressed = dress;
			b.dwKeptAt = 0;
			b.dwWillAt = 0;
		}
		bool jade = false;
		for (int i = 0; i < 3 && !jade; ++i)
			jade = OwnsPlayerBotYoharaJade(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i]);
		if (jade && WearPlayerBotYoharaDress(ch, sungma) > 0)
		{
			b.dwWillAt = 0;
			state.bEquipPending = true;
			state.dwNextEquipmentCheckTime = 0;
		}
	}
}

#endif
