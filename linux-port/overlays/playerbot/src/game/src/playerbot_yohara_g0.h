#ifndef __INC_METIN2_PLAYERBOT_YOHARA_G0_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_G0_H__

// MT2009_PLUS_BOT_YOHARA_G0_V1 - the Yohara starter package G0 of the bot Champions (plan cache/yohara/plan-boty-yohara.md
// 6.1-6.4; the owner, 22 October 2026: "bot dostaje go dopiero, gdy ma 400 Magicznych Pylow (bot oddaje 400 pylow w zamian
// za pakiet). Sprzet z pakietu jest przypisany do konta: bot moze go ulepszac, ale nie moze wyrzucic, przekazac w handlu
// ani sprzedac graczom - moze sprzedac tylko innym botom"; "dotyczy botow, ktore dojda do Czempiona naturalnie (nie
// obecnej setki)"; and later: "Czempion bez 400 pylow ma je aktywnie zdobywac, a jego rozwoj nie moze stanac").
//
// Who: a bot of the server's top level with a Champion level, of the ordinary population (IsPlayerBotYoharaEligible),
// no member of a cohort (the 100 of the Yohara cohort wear the Hydra's gear), no package yet (the quest flag
// mt2009_g0.given) and no Sung Ma glove or jade jewellery of its own (worn or in the bag).
//
// The package (each piece +3, made new - its Will lines are the items' own, rolled as for anybody): Rekawice Mocy +3
// (23003, Sila Sung Ma), the three pieces of jade jewellery - Obrecz (14580-14619), Kolia (16580-16619), Klipsy
// (17570-17609) Jadeitu +3 - and a Talizman Woli +3 (81000 SILA / 81300 WIT / 81250 ODP). The jade's and the
// talisman's kind is the bot's need: the Will of Namgan (377, the end of the plan's stage A, sungma_table.txt) minus what
// the bot has (its points and items) and the glove's Sila, one piece at a time to the kind lacking most - Dymu Sila,
// Nocy Witalnosc, Mgly Odpornosc (POINT_SUNGMA_MOVE).
//
// Where and when: in a village of whichever core it is on (in practice its first village, between its trips; the
// Alchemist who made its dust stands there), at its look every minute (ManagePlayerBotG0, beside the Alchemist's
// errand in the AI's tick): 400 Magiczny Pyl (30360) go, the five pieces come, bound to the account
// (playerbot_yohara_g0.cpp, server-patches/g0bind). The equipment pass puts them on (the Will's weight below).
//
// Without the 400 dust its development goes on (the Sung Ma maps, levels, the hunt - no block), and the dust is
// sought besides: the dust it holds is kept (the counters' keep and the marbles' / bonus stones' spending, both asked
// GetPlayerBotG0DustReserve), it is bought on the market (bots' stalls and the offline shops of bots and players, at
// most PLAYERBOT_G0_DUST_PRICE_CAP_PCT of the price the bots make dust at, out of half the spare purse), and from the
// village one draw in two every half hour is a trip to Zaklety Las (353, its Metins' soul stones, made dust at the
// Alchemist at home) - a trip the forest's band (97-109) would refuse a bot of 120: a G0 hunter stays while it lacks
// the dust (IsPlayerBotG0ZakletyStay; the forest's own stay and deaths rules as ever).
//
// The binding: the pieces cannot be dropped, traded, given or put on any shop (the engine's anti flags of the
// instance); a refine carries it. A bot whose piece was replaced by a better one sells it to another bot that wants it
// (a Champion whose slot it betters, with the gold and a free cell) - a direct move between the two bots for gold
// (PLAYERBOT_G0_SALE_PRICE*), never on a counter people see.
//
// MT2009_PLUS_BOT_YOHARA_G0_V2 (the owner, 22 October: "Moze sprzedac NPC, jesli go nie potrzebuje"; "Bot zaczyna
// zbierac pyl dopiero od 110 poziomu; gdy ma 400, zostawia je u dozorcy"): a replaced piece no bot bought in
// PLAYERBOT_G0_NPC_AFTER_LOOKS sale looks (half an hour) goes to the merchant at the merchant's price on the next town
// visit (SellPlayerBotJunkAtMerchant, logged sold-to-npc) - never one the bot wears or would wear. And the dust is
// sought from level PLAYERBOT_G0_SAVE_MIN_LEVEL (a saver: the same keep, market and trips as a Champion short of it);
// a saver with 400 that is no Champion of the top level yet puts the 400 in its safebox at the storekeeper (the town
// visit's safebox phase, RunPlayerBotG0Safebox; the quest flag mt2009_g0.banked) and stops seeking; the box's dust of
// such a bot never comes out for anything else (IsPlayerBotG0BoxDust). Once it qualifies, the next visit takes the 400
// out and the package is given as before. A bot that qualifies with the 400 in the bag gets the package straight away.
//
// The gear's score: a Sung Ma Will line of a Champion of the top level weighs PLAYERBOT_G0_WILL_WEIGHT a point
// (Inteligencja a tenth of it) - the jade replaces the Emerald set of a Yohara-going Champion only (nobody else counts
// Will); a Talizman Woli is worn over the element's talisman while the bot, without its pendant's Will, is short of the
// Will of the map its Champion level reaches (the owner's D15), the element's talisman wins otherwise.
//
// The log: PLAYERBOT_G0 (given, waiting with the dust held and needed and where it came from, dust bought / made, dust
// trip planned, sold-to-bot, bound carried by a refine, census every ten minutes). The operator's test file
// playerbot_g0_test in the core's directory: "dust <n>" fills the bags of up to n bots waiting for the package on this
// core to 400 dust, "status" logs each such bot.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_bots.h (the Sung Ma maps'
// table and the Champion's helpers come from there), in the anonymous namespace.

namespace
{
	const DWORD PLAYERBOT_G0_GLOVE_VNUM = 23003;	// Rekawice Mocy+3 (Sila Sung Ma)
	// a kind: 0 Sila, 1 Witalnosc, 2 Odpornosc (POINT_SUNGMA_STR, _HP, _MOVE)
	const DWORD PLAYERBOT_G0_BRACELET_VNUMS[3] = { 14613, 14603, 14583 };	// Obrecz Jadeitu Dymu / Nocy / Mgly +3
	const DWORD PLAYERBOT_G0_NECKLACE_VNUMS[3] = { 16613, 16603, 16583 };	// Kolia Jadeitu Dymu / Nocy / Mgly +3
	const DWORD PLAYERBOT_G0_EARRINGS_VNUMS[3] = { 17603, 17593, 17573 };	// Klipsy Jadeitu Dymu / Nocy / Mgly +3
	const DWORD PLAYERBOT_G0_TALISMAN_VNUMS[3] = { 81003, 81303, 81253 };	// Talizman Woli SILA / WIT / ODP +3
	const char* const PLAYERBOT_G0_KIND_NAMES[3] = { "sila", "witalnosc", "odpornosc" };
	// the Will a +3 piece brings, for the kinds' choice (the glove's 14-22, the jade's 7-8, the talisman's 5)
	const int PLAYERBOT_G0_GLOVE_WILL = 18;
	const int PLAYERBOT_G0_JADE_WILL = 8;
	const int PLAYERBOT_G0_TALISMAN_WILL = 5;
	const long PLAYERBOT_G0_KIND_MAP = 377;	// Namgan: the kinds are chosen for its Will
	const int PLAYERBOT_G0_KIND_MAP_REQ[3] = { 25, 15, 25 };	// its sungma_table.txt row, if the table has no Namgan

	const int PLAYERBOT_G0_DUST = 400;
	// MT2009_PLUS_BOT_YOHARA_G0_V2: the dust is sought from this level, and the 400 wait in the safebox (the flag
	// holds how many went down; cleared when they come out)
	const int PLAYERBOT_G0_SAVE_MIN_LEVEL = 110;
	const char* const PLAYERBOT_G0_BANKED_FLAG = "mt2009_g0.banked";
	// MT2009_PLUS_BOT_YOHARA_G0_V2: a replaced piece goes to the merchant after this many sale looks without a bot buyer
	const int PLAYERBOT_G0_NPC_AFTER_LOOKS = 3;
	const char* const PLAYERBOT_G0_GIVEN_FLAG = "mt2009_g0.given";
	const char* const PLAYERBOT_G0_GIVEN_AT_FLAG = "mt2009_g0.given_at";
	const DWORD PLAYERBOT_G0_LOOK_MS = 60 * 1000;
	const DWORD PLAYERBOT_G0_WAIT_LOG_MS = 30 * 60 * 1000;
	const int PLAYERBOT_G0_FREE_CELLS = 6;	// five pieces and a cell to spare

	// the dust's market: at most this per cent of the bots' own price of a dust (PLAYERBOT_PRIOR_MAGIC_DUST, scaled),
	// out of this per cent of the spare purse
	const int PLAYERBOT_G0_DUST_PRICE_CAP_PCT = 150;
	const int PLAYERBOT_G0_DUST_PURSE_PCT = 50;
	// the dust's trip: a roll in a village every half hour, one in two to Zaklety Las; the plan holds for the way there
	const DWORD PLAYERBOT_G0_TRIP_ROLL_MS = 30 * 60 * 1000;
	const int PLAYERBOT_G0_TRIP_CHANCE = 50;
	const DWORD PLAYERBOT_G0_TRIP_PLAN_MS = 45 * 60 * 1000;

	// the score of a Will point for a Champion (a jade +3's 8 points: 120 000 - over an Emerald piece +9 with its five
	// lines); Inteligencja's (its penalty only halves the poison / fire / bleeding of the bot's blows) a tenth
	const long long PLAYERBOT_G0_WILL_WEIGHT = 15000;
	const long long PLAYERBOT_G0_WILL_WEIGHT_IMMUNE = 1500;
	// a Talizman Woli while the Will is short: over any element's talisman (GetPlayerBotTalismanScore: up to ~2e7)
	const long long PLAYERBOT_G0_WILL_TALISMAN_SHORT_SCORE = 1000000000000LL;

	// the bot-to-bot sale of a replaced piece: this much and this much more a plus, looked at every ten minutes
	const long long PLAYERBOT_G0_SALE_PRICE_BASE = 1000000;
	const long long PLAYERBOT_G0_SALE_PRICE_PER_PLUS = 1000000;
	const DWORD PLAYERBOT_G0_SALE_LOOK_MS = 10 * 60 * 1000;

	const DWORD PLAYERBOT_G0_CENSUS_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_G0_TEST_FILE = "playerbot_g0_test";

	struct TPlayerBotG0
	{
		DWORD dwNextLook, dwNextManage, dwNextWaitLog, dwNextSaleLook, dwTripRolled, dwTripUntil;
		bool bNeeder;
		bool bSaver;	// MT2009_PLUS_BOT_YOHARA_G0_V2: from level 110, the package not yet given (a needer is a saver too)
		int iBought, iMade, iTrips;
		long long llSpent;
		TPlayerBotG0() : dwNextLook(0), dwNextManage(0), dwNextWaitLog(0), dwNextSaleLook(0), dwTripRolled(0), dwTripUntil(0), bNeeder(false),
			bSaver(false), iBought(0), iMade(0), iTrips(0), llSpent(0) {}
	};
	std::map<DWORD, TPlayerBotG0> s_mapPlayerBotG0;
	// MT2009_PLUS_BOT_YOHARA_G0_V2: a replaced bound piece's sale looks without a bot buyer, by item id
	std::map<DWORD, int> s_mapPlayerBotG0NoBuyer;

	struct TPlayerBotG0Stats
	{
		unsigned int given, sold, trips, dustBought, dustMade;
		unsigned int soldNpc, deposited, withdrawn;	// MT2009_PLUS_BOT_YOHARA_G0_V2
		long long spent;
		DWORD dwLastCensus, dwLastTestLook;
		TPlayerBotG0Stats() : given(0), sold(0), trips(0), dustBought(0), dustMade(0), soldNpc(0), deposited(0), withdrawn(0), spent(0),
			dwLastCensus(0), dwLastTestLook(0) {}
	};
	TPlayerBotG0Stats s_kPlayerBotG0Stats;

	// ------------------------------------------------------------ who

	// A Champion of the server's top level, a bot: the one whose gear the Will counts for.
	bool IsPlayerBotSungmaWillUser(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && (int)ch->GetLevel() >= gPlayerMaxLevel &&
				GetPlayerBotChampionLevel(ch) >= 1;
	}

	// The kind of a Talizman Woli (0 Sila, 1 Witalnosc, 2 Odpornosc, 3 Inteligencja; -1 none).
	int GetPlayerBotWillTalismanKind(DWORD vnum)
	{
		switch (vnum - vnum % 10)
		{
			case 81000: return 0;
			case 81300: return 1;
			case 81250: return 2;
			case 81550: return 3;
		}
		return -1;
	}

	// A Sung Ma glove or a piece of jade jewellery (the package's families but the talisman).
	bool IsPlayerBotYoharaGearVnum(DWORD vnum)
	{
		return Mt2009AccountBoundFamily(vnum) && GetPlayerBotWillTalismanKind(vnum) < 0;
	}

	bool HasPlayerBotYoharaGear(LPCHARACTER ch)
	{
		for (int w = 0; w < WEAR_MAX_NUM; ++w)
		{
			LPITEM worn = ch->GetWear(w);
			if (worn && IsPlayerBotYoharaGearVnum(worn->GetVnum()))
				return true;
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotYoharaGearVnum(item->GetVnum()))
				return true;
		}
		return false;
	}

	// MT2009_PLUS_BOT_YOHARA_G0_V2: a bot of level 110 or more the package will be for, still without it - it saves
	// the dust.
	bool IsPlayerBotG0Saver(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || (int)ch->GetLevel() < PLAYERBOT_G0_SAVE_MIN_LEVEL ||
				!ch->IsItemLoaded() || !IsPlayerBotYoharaEligible(ch) || IsPlayerBotYoharaCohortPID(ch->GetPlayerID()))
			return false;
		if (ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) != 0)
			return false;
		return !HasPlayerBotYoharaGear(ch);
	}

	// The bot the package is for, still without it.
	bool IsPlayerBotG0Needer(LPCHARACTER ch)
	{
		return IsPlayerBotSungmaWillUser(ch) && IsPlayerBotG0Saver(ch);
	}

	// MT2009_PLUS_BOT_YOHARA_G0_V2: its 400 lie in the safebox (or what of them went down, a box short of room).
	bool IsPlayerBotG0DustBanked(LPCHARACTER ch)
	{
		return ch && ch->GetQuestFlag(PLAYERBOT_G0_BANKED_FLAG) > 0;
	}

	// The bot's entry, its look refreshed once a minute (on whichever core it is).
	TPlayerBotG0* LookPlayerBotG0(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch || (int)ch->GetLevel() < PLAYERBOT_G0_SAVE_MIN_LEVEL || !ch->GetDesc() || !ch->GetDesc()->IsBot())	// MT2009_PLUS_BOT_YOHARA_G0_V2
			return NULL;
		TPlayerBotG0& b = s_mapPlayerBotG0[ch->GetPlayerID()];
		if ((int)(b.dwNextLook - dwNow) <= 0)
		{
			b.dwNextLook = dwNow + PLAYERBOT_G0_LOOK_MS;
			b.bSaver = IsPlayerBotG0Saver(ch);	// MT2009_PLUS_BOT_YOHARA_G0_V2
			b.bNeeder = b.bSaver && IsPlayerBotSungmaWillUser(ch);
		}
		return &b;
	}

	int GetPlayerBotG0DustHeld(LPCHARACTER ch)
	{
		return ch ? (int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM) : 0;
	}

	// MT2009_PLUS_BOT_YOHARA_G0_V2: a saver's from level 110, until its 400 lie in the safebox (a banked bot's bag dust
	// is its own again; the 400 taken out for the package clear the flag and are kept again until given).
	int GetPlayerBotG0DustReserve(LPCHARACTER ch)
	{
		const TPlayerBotG0* b = LookPlayerBotG0(ch, get_dword_time());
		return b && b->bSaver && !IsPlayerBotG0DustBanked(ch) ? PLAYERBOT_G0_DUST : 0;
	}

	bool IsPlayerBotG0DustHunter(LPCHARACTER ch)
	{
		return GetPlayerBotG0DustReserve(ch) > 0 && GetPlayerBotG0DustHeld(ch) < PLAYERBOT_G0_DUST;
	}

	// ------------------------------------------------------------ the dust: market, Alchemist, trip

	bool WantsPlayerBotG0DustOffer(LPCHARACTER ch, LPITEM offer)
	{
		return ch && offer && offer->GetVnum() == PLAYERBOT_MAGIC_DUST_VNUM && IsPlayerBotG0DustHunter(ch);
	}

	bool CanPlayerBotPayForG0Dust(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long units = std::max<long long>(1, (long long)item->GetCount());
		const long long cap = (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_PRIOR_MAGIC_DUST) * PLAYERBOT_G0_DUST_PRICE_CAP_PCT / 100;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return price <= cap * units && price <= spare * PLAYERBOT_G0_DUST_PURSE_PCT / 100;
	}

	bool WantsPlayerBotG0DustFromMarket(LPCHARACTER ch)
	{
		if (!IsPlayerBotG0DustHunter(ch))
			return false;
		const TPlayerBotMarketLedgerEntry* dust = GetPlayerBotMarketLedgerEntry(PLAYERBOT_MAGIC_DUST_VNUM);
		return dust && dust->dwSupplyUnits > 0;
	}

	void NotePlayerBotG0DustBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!ch || vnum != PLAYERBOT_MAGIC_DUST_VNUM)
			return;
		std::map<DWORD, TPlayerBotG0>::iterator it = s_mapPlayerBotG0.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotG0.end() || !it->second.bSaver)	// MT2009_PLUS_BOT_YOHARA_G0_V2: from level 110
			return;
		it->second.iBought += (int)count;
		it->second.llSpent += price;
		s_kPlayerBotG0Stats.dustBought += count;
		s_kPlayerBotG0Stats.spent += price;
		sys_log(0, "PLAYERBOT_G0: dust bought pid=%u name=%s count=%u price=%lld have=%d need=%d source=market",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)count, price, GetPlayerBotG0DustHeld(ch), PLAYERBOT_G0_DUST);
	}

	void NotePlayerBotG0DustMade(LPCHARACTER ch, int made)
	{
		if (!ch || made <= 0)
			return;
		std::map<DWORD, TPlayerBotG0>::iterator it = s_mapPlayerBotG0.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotG0.end() || !it->second.bSaver)	// MT2009_PLUS_BOT_YOHARA_G0_V2: from level 110
			return;
		it->second.iMade += made;
		s_kPlayerBotG0Stats.dustMade += made;
		sys_log(0, "PLAYERBOT_G0: dust made pid=%u name=%s made=%d have=%d need=%d source=alchemist",
				ch->GetPlayerID(), ch->GetName(), made, GetPlayerBotG0DustHeld(ch), PLAYERBOT_G0_DUST);
	}

	// GetPlayerBotYoharaFrontier's home draw: Zaklety Las for a G0 hunter, one roll in two every half hour from a village
	// (0: no trip - the usual draw, the Sung Ma maps first).
	long GetPlayerBotG0DustTrip(LPCHARACTER ch, DWORD dwNow)
	{
		if (!IsPlayerBotG0DustHunter(ch))
			return 0;
		TPlayerBotG0& b = s_mapPlayerBotG0[ch->GetPlayerID()];
		if (b.dwTripUntil != 0 && (int)(b.dwTripUntil - dwNow) > 0)
			return PLAYERBOT_MAP_ZAKLETY;
		b.dwTripUntil = 0;
		if (!IsPlayerBotVillageMap(ch->GetMapIndex()) || BlocksPlayerBotTravel(ch))
			return 0;
		if (b.dwTripRolled != 0 && (int)(dwNow - b.dwTripRolled) < (int)PLAYERBOT_G0_TRIP_ROLL_MS)
			return 0;
		b.dwTripRolled = dwNow;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		if (cfg.zakletyMax <= 0 || s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_ZAKLETY] >= cfg.zakletyMax ||
				IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_ZAKLETY) || !IsPlayerBotOchaoHosted() ||
				ch->GetMaxHP() < cfg.zakletyMinHp || number(1, 100) > PLAYERBOT_G0_TRIP_CHANCE)
			return 0;
		b.dwTripUntil = dwNow + PLAYERBOT_G0_TRIP_PLAN_MS;
		++b.iTrips;
		++s_kPlayerBotG0Stats.trips;
		sys_log(0, "PLAYERBOT_G0: dust trip planned pid=%u name=%s champion=%d have=%d need=%d to=%ld census=%d/%d trips=%d",
				ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), GetPlayerBotG0DustHeld(ch), PLAYERBOT_G0_DUST,
				PLAYERBOT_MAP_ZAKLETY, s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_ZAKLETY], cfg.zakletyMax, b.iTrips);
		return PLAYERBOT_MAP_ZAKLETY;
	}

	// A bot over the forest's band staying there for the dust (the forest's resident draw).
	bool IsPlayerBotG0ZakletyStay(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() > (int)PLAYERBOT_ZAKLETY_MAX_LEVEL && IsPlayerBotG0DustHunter(ch);
	}

	// ------------------------------------------------------------ the gear's score

	long long GetPlayerBotSungmaWillWeight(LPCHARACTER ch, BYTE bType)
	{
		if (bType < POINT_SUNGMA_STR || bType > POINT_SUNGMA_IMMUNE || !IsPlayerBotSungmaWillUser(ch))
			return -1;
		return bType == POINT_SUNGMA_IMMUNE ? PLAYERBOT_G0_WILL_WEIGHT_IMMUNE : PLAYERBOT_G0_WILL_WEIGHT;
	}

	// The map the bot's Champion level reaches (its band's top map switched on; the lowest one on below every band).
	int GetPlayerBotG0BandSlot(LPCHARACTER ch)
	{
		const int champion = GetPlayerBotChampionLevel(ch);
		int lowest = -1;
		for (int i = PLAYERBOT_SUNGMA_MAP_COUNT - 1; i >= 0; --i)
		{
			if (!IsPlayerBotSungmaMapOn(PLAYERBOT_SUNGMA_MAPS[i].lMap))
				continue;
			lowest = i;
			if (champion >= (int)PLAYERBOT_SUNGMA_MAPS[i].bChampionMin)
				return i;
		}
		return lowest;
	}

	// D15: a Talizman Woli over the element's talisman while the bot, its pendant's Will taken out, lacks that Will
	// for the map of its band - the same answer whichever of the two it wears (no swapping back and forth).
	bool GetPlayerBotG0WillTalismanScore(LPCHARACTER ch, LPITEM item, long long& score)
	{
		const int kind = item ? GetPlayerBotWillTalismanKind(item->GetVnum()) : -1;
		if (kind < 0 || kind > 2 || !IsPlayerBotSungmaWillUser(ch))
			return false;
		const int slot = GetPlayerBotG0BandSlot(ch);
		if (slot < 0)
			return false;
		static const BYTE s_aPoint[3] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE };
		long will = GetPlayerBotSungmaWill(ch, kind);
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (worn)
			will -= SumPlayerBotItemLines(worn, s_aPoint[kind]);
		const long need = (long)GetPlayerBotSungmaReq(slot, kind) - will;
		if (need <= 0)
			return false;
		const long own = SumPlayerBotItemLines(item, s_aPoint[kind]);
		score = PLAYERBOT_G0_WILL_TALISMAN_SHORT_SCORE + (long long)std::min(own, need) * 1000 + (long long)(item->GetVnum() % 10);
		return true;
	}

	// ------------------------------------------------------------ the package

	// The kinds of the jade and the talisman: Namgan's Will minus the bot's and the glove's, to the kind lacking most.
	void ChoosePlayerBotG0Kinds(LPCHARACTER ch, int kinds[4])
	{
		int need[3];
		const int slot = GetPlayerBotSungmaSlot(PLAYERBOT_G0_KIND_MAP);
		for (int i = 0; i < 3; ++i)
			need[i] = (slot >= 0 ? GetPlayerBotSungmaReq(slot, i) : PLAYERBOT_G0_KIND_MAP_REQ[i]) - GetPlayerBotSungmaWill(ch, i);
		need[0] -= PLAYERBOT_G0_GLOVE_WILL;
		for (int p = 0; p < 4; ++p)
		{
			int best = 0;
			for (int i = 1; i < 3; ++i)
				if (need[i] > need[best])
					best = i;
			kinds[p] = best;
			need[best] -= p < 3 ? PLAYERBOT_G0_JADE_WILL : PLAYERBOT_G0_TALISMAN_WILL;
		}
	}

	bool GivePlayerBotG0(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotG0& b, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		const int dustBefore = GetPlayerBotG0DustHeld(ch);
		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_G0_FREE_CELLS)
		{
			PlayerBotLogThrottled("g0_bag_full", dwNow, "PLAYERBOT_G0: no room for the package pid=%u name=%s free=%d have=%d",
					pid, ch->GetName(), CountPlayerBotFreeInventoryCells(ch), dustBefore);
			return false;
		}
		int kinds[4];
		ChoosePlayerBotG0Kinds(ch, kinds);
		const DWORD vnums[5] = { PLAYERBOT_G0_GLOVE_VNUM, PLAYERBOT_G0_BRACELET_VNUMS[kinds[0]], PLAYERBOT_G0_NECKLACE_VNUMS[kinds[1]],
				PLAYERBOT_G0_EARRINGS_VNUMS[kinds[2]], PLAYERBOT_G0_TALISMAN_VNUMS[kinds[3]] };
		ch->RemoveSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM, PLAYERBOT_G0_DUST);
		int made = 0;
		for (int i = 0; i < 5; ++i)
		{
			LPITEM item = ch->AutoGiveItem(vnums[i], 1, -1, false);
			if (!item)
			{
				sys_err("PLAYERBOT_G0: piece not made pid=%u name=%s vnum=%u", pid, ch->GetName(), vnums[i]);
				continue;
			}
			Mt2009AccountBoundMark(item, pid, "g0");
			LogManager::instance().ItemLog(ch, item, "PLAYERBOT_G0", item->GetName());
			++made;
		}
		ch->SetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG, 1);
		ch->SetQuestFlag(PLAYERBOT_G0_GIVEN_AT_FLAG, (int)time(0));
		b.bNeeder = false;
		b.bSaver = false;	// MT2009_PLUS_BOT_YOHARA_G0_V2
		b.dwTripUntil = 0;
		++s_kPlayerBotG0Stats.given;
		state.dwNextEquipmentCheckTime = dwNow;	// the equipment pass puts them on now
		sys_log(0, "PLAYERBOT_G0: given pid=%u name=%s level=%u champion=%d map=%ld dust=%d->%d pieces=%d glove=%u "
				"bracelet=%u(%s) necklace=%u(%s) earrings=%u(%s) talisman=%u(%s) bought=%d made_at_alchemist=%d trips=%d",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), ch->GetMapIndex(), dustBefore,
				GetPlayerBotG0DustHeld(ch), made, vnums[0], vnums[1], PLAYERBOT_G0_KIND_NAMES[kinds[0]], vnums[2],
				PLAYERBOT_G0_KIND_NAMES[kinds[1]], vnums[3], PLAYERBOT_G0_KIND_NAMES[kinds[2]], vnums[4],
				PLAYERBOT_G0_KIND_NAMES[kinds[3]], b.iBought, b.iMade, b.iTrips);
		return true;
	}

	// ------------------------------------------------------------ the bot-to-bot sale

	long long GetPlayerBotG0SalePrice(LPITEM item)
	{
		return PLAYERBOT_G0_SALE_PRICE_BASE + PLAYERBOT_G0_SALE_PRICE_PER_PLUS * (long long)(item->GetVnum() % 10);
	}

	// The best Talizman Woli of a kind the bot owns (worn or in the bag), but `except`.
	int GetPlayerBotBestWillTalismanPlus(LPCHARACTER ch, int kind, LPITEM except)
	{
		int best = -1;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (worn && worn != except && GetPlayerBotWillTalismanKind(worn->GetVnum()) == kind)
			best = (int)(worn->GetVnum() % 10);
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item != except && item->GetCell() == cell && GetPlayerBotWillTalismanKind(item->GetVnum()) == kind)
				best = std::max(best, (int)(item->GetVnum() % 10));
		}
		return best;
	}

	// A bound piece in the bag the bot has bettered: the worn piece of its slot scores more (a talisman: a higher one
	// of its kind is owned).
	bool IsPlayerBotG0PieceReplaced(LPCHARACTER ch, LPITEM item)
	{
		const int kind = GetPlayerBotWillTalismanKind(item->GetVnum());
		if (kind >= 0)
			return GetPlayerBotBestWillTalismanPlus(ch, kind, item) > (int)(item->GetVnum() % 10);
		const int wearCell = item->FindEquipCell(ch);
		if (wearCell < 0 || wearCell >= WEAR_MAX_NUM)
			return false;
		LPITEM worn = ch->GetWear(wearCell);
		return worn && worn != item && GetPlayerBotEquipmentScore(worn, ch) > GetPlayerBotEquipmentScore(item, ch);
	}

	// A bot that wants the piece: a Champion whose slot it betters (a talisman: none as high of its kind), not holding
	// one like it in the bag already, with the gold and a free cell.
	bool WantsPlayerBotG0Piece(LPCHARACTER buyer, LPITEM item, long long price)
	{
		if (!IsPlayerBotSungmaWillUser(buyer) || !buyer->IsItemLoaded() || buyer->IsDead() || buyer->GetExchange() ||
				buyer->GetMyShop() || !IsPlayerBotYoharaEligible(buyer) || item->GetLevelLimit() > (int)buyer->GetLevel() ||
				!item->CanUsedBy(buyer))
			return false;
		if ((long long)buyer->GetGold() - GetPlayerBotReservedGold(buyer) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR < price ||
				buyer->GetEmptyInventory(item->GetSize()) < 0)
			return false;
		const int kind = GetPlayerBotWillTalismanKind(item->GetVnum());
		if (kind >= 0)
			return GetPlayerBotBestWillTalismanPlus(buyer, kind, NULL) < (int)(item->GetVnum() % 10);
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM held = buyer->GetInventoryItem(cell);
			if (held && held->GetType() == item->GetType() && held->GetSubType() == item->GetSubType() &&
					IsPlayerBotYoharaGearVnum(held->GetVnum()))
				return false;
		}
		const int wearCell = item->FindEquipCell(buyer);
		if (wearCell < 0 || wearCell >= WEAR_MAX_NUM)
			return false;
		LPITEM worn = buyer->GetWear(wearCell);
		return !worn || GetPlayerBotEquipmentScore(item, buyer) > GetPlayerBotEquipmentScore(worn, buyer);
	}

	// One replaced piece a look to a bot of this core that wants it: moved between the two bags, the gold the other way.
	bool SellPlayerBotG0Spare(LPCHARACTER ch)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->isLocked() || item->IsExchanging() ||
					!Mt2009AccountBound(item) || !IsPlayerBotG0PieceReplaced(ch, item))
				continue;
			const long long price = GetPlayerBotG0SalePrice(item);
			for (TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
			{
				if (st->first == ch->GetPlayerID())
					continue;
				LPCHARACTER buyer = CHARACTER_MANAGER::instance().FindByPID(st->first);
				if (!buyer || !WantsPlayerBotG0Piece(buyer, item, price))
					continue;
				const int to = buyer->GetEmptyInventory(item->GetSize());
				if (to < 0)
					continue;
				const DWORD vnum = item->GetVnum(), id = item->GetID();
				item->RemoveFromCharacter();
				item->AddToCharacter(buyer, TItemPos(INVENTORY, to));
				ITEM_MANAGER::instance().FlushDelayedSave(item);
				Mt2009AccountBoundOwner(item, buyer->GetPlayerID());
				PlayerBotChangeGold(buyer, -price);
				PlayerBotChangeGold(ch, price);
				LogManager::instance().ItemLog(buyer, item, "PLAYERBOT_G0_SOLD_TO_BOT", ch->GetName());
				s_mapPlayerBotG0NoBuyer.erase(id);	// MT2009_PLUS_BOT_YOHARA_G0_V2
				++s_kPlayerBotG0Stats.sold;
				sys_log(0, "PLAYERBOT_G0: sold-to-bot seller=%u name=%s buyer=%u name=%s item=%u vnum=%u price=%lld",
						ch->GetPlayerID(), ch->GetName(), buyer->GetPlayerID(), buyer->GetName(), id, vnum, price);
				return true;
			}
			// MT2009_PLUS_BOT_YOHARA_G0_V2: no bot wanted it this look - after PLAYERBOT_G0_NPC_AFTER_LOOKS of them
			// the merchant takes it (IsPlayerBotG0NpcSaleDue).
			int& misses = s_mapPlayerBotG0NoBuyer[item->GetID()];
			if (++misses == PLAYERBOT_G0_NPC_AFTER_LOOKS)
				sys_log(0, "PLAYERBOT_G0: no bot buyer pid=%u name=%s item=%u vnum=%u looks=%d - for the merchant",
						ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetVnum(), misses);
		}
		return false;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_YOHARA_G0_V2: the merchant

	// A replaced bound piece in the bag no bot bought in PLAYERBOT_G0_NPC_AFTER_LOOKS looks, still replaced now (the
	// bot wears a better one of its slot, or owns a higher talisman of its kind) - never a worn piece.
	bool IsPlayerBotG0NpcSaleDue(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || s_mapPlayerBotG0NoBuyer.empty() || item->IsEquipped() || item->isLocked() || item->IsExchanging() ||
				item->GetWindow() != INVENTORY)
			return false;
		std::map<DWORD, int>::const_iterator it = s_mapPlayerBotG0NoBuyer.find(item->GetID());
		if (it == s_mapPlayerBotG0NoBuyer.end() || it->second < PLAYERBOT_G0_NPC_AFTER_LOOKS || !Mt2009AccountBound(item))
			return false;
		return IsPlayerBotSungmaWillUser(ch) && IsPlayerBotG0PieceReplaced(ch, item);
	}

	// SellPlayerBotJunkAtMerchant, before the item goes.
	void NotePlayerBotG0SoldToNpc(LPCHARACTER ch, LPITEM item, long long price, const char* merchantName)
	{
		if (!ch || !item)
			return;
		const DWORD id = item->GetID();
		std::map<DWORD, int>::iterator it = s_mapPlayerBotG0NoBuyer.find(id);
		const int looks = it != s_mapPlayerBotG0NoBuyer.end() ? it->second : 0;
		if (it != s_mapPlayerBotG0NoBuyer.end())
			s_mapPlayerBotG0NoBuyer.erase(it);
		DBManager::instance().DirectQuery("DELETE FROM item_account_bound WHERE id = %u", id);
		LogManager::instance().ItemLog(ch, item, "PLAYERBOT_G0_SOLD_TO_NPC", merchantName ? merchantName : "merchant");
		++s_kPlayerBotG0Stats.soldNpc;
		sys_log(0, "PLAYERBOT_G0: sold-to-npc pid=%u name=%s item=%u vnum=%u price=%lld merchant=%s looks_without_bot=%d",
				ch->GetPlayerID(), ch->GetName(), id, item->GetVnum(), price, merchantName ? merchantName : "merchant", looks);
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_YOHARA_G0_V2: the safebox

	// The dust in a banked bot's box: its G0 package's, out for nothing else.
	bool IsPlayerBotG0BoxDust(LPCHARACTER ch, LPITEM item)
	{
		return item && item->GetVnum() == PLAYERBOT_MAGIC_DUST_VNUM && IsPlayerBotG0DustBanked(ch);
	}

	// The town visit's safebox phase is wanted: a saver short of the top level with its 400 in the bag (in), or a
	// bot the package is for now with them in the box and room for them and the package (out).
	bool PlayerBotG0WantsSafebox(LPCHARACTER ch)
	{
		const TPlayerBotG0* b = LookPlayerBotG0(ch, get_dword_time());
		if (!b || !b->bSaver || IsPlayerBotSidekickServing(ch))
			return false;
		if (IsPlayerBotG0DustBanked(ch))
			return b->bNeeder && CountPlayerBotFreeInventoryCells(ch) >= PLAYERBOT_G0_FREE_CELLS + 2;
		return !b->bNeeder && GetPlayerBotG0DustHeld(ch) >= PLAYERBOT_G0_DUST;
	}

	int CountPlayerBotG0BoxDust(CSafebox* box)
	{
		int units = 0;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (item && item->GetVnum() == PLAYERBOT_MAGIC_DUST_VNUM)
				units += (int)item->GetCount();
		}
		return units;
	}

	// The open box (BOT_TOWN_PHASE_SAFEBOX_WAIT, after the visit's own deposit and withdrawal): the 400 down, or out.
	// Returns the units moved.
	int RunPlayerBotG0Safebox(LPCHARACTER ch, CSafebox* box)
	{
		if (!ch || !box)
			return 0;
		const TPlayerBotG0* b = LookPlayerBotG0(ch, get_dword_time());
		if (!b || !b->bSaver || IsPlayerBotSidekickServing(ch))
			return 0;
		const DWORD pid = ch->GetPlayerID();
		if (!IsPlayerBotG0DustBanked(ch))
		{
			// In: a saver short of the top level with its 400 (a needer gets the package for them instead).
			if (b->bNeeder || GetPlayerBotG0DustHeld(ch) < PLAYERBOT_G0_DUST)
				return 0;
			// The bag's stacks, the last cut to what is left; first the box's room for all of them.
			std::vector<WORD> cells;
			int counted = 0;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && counted < PLAYERBOT_G0_DUST; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->GetVnum() != PLAYERBOT_MAGIC_DUST_VNUM || item->isLocked() ||
						item->IsExchanging())
					continue;
				cells.push_back(cell);
				counted += (int)item->GetCount();
			}
			int room = 0;
			for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
				if (box->IsValidPosition(pos) && box->IsEmpty(pos, 1))
					++room;
			if (counted < PLAYERBOT_G0_DUST || room < (int)cells.size() || (counted > PLAYERBOT_G0_DUST && ch->GetEmptyInventory(1) < 0))
			{
				sys_log(0, "PLAYERBOT_G0: dust not deposited pid=%u name=%s have=%d stacks=%u box_room=%d",
						pid, ch->GetName(), counted, (unsigned int)cells.size(), room);
				return 0;
			}
			int left = PLAYERBOT_G0_DUST;
			for (size_t i = 0; i < cells.size() && left > 0; ++i)
			{
				LPITEM item = ch->GetInventoryItem(cells[i]);
				if (!item)
					continue;
				if ((int)item->GetCount() > left)
				{
					const int to = ch->GetEmptyInventory(1);
					if (to < 0 || !ch->MoveItem(TItemPos(INVENTORY, cells[i]), TItemPos(INVENTORY, (WORD)to), left))
						break;
					item = ch->GetInventoryItem(to);
					if (!item || item->GetVnum() != PLAYERBOT_MAGIC_DUST_VNUM)
						break;
				}
				bool placed = false;
				for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM && !placed; ++pos)
				{
					if (!box->IsValidPosition(pos) || !box->IsEmpty(pos, 1))
						continue;
					char szHint[128];
					snprintf(szHint, sizeof(szHint), "%s %u", item->GetName(), (unsigned int)item->GetCount());
					LogManager::instance().ItemLog(ch, item, "SAFEBOX PUT", szHint);
					left -= (int)item->GetCount();
					item->RemoveFromCharacter();
					box->Add(pos, item);
					placed = true;
				}
				if (!placed)
					break;
			}
			const int deposited = PLAYERBOT_G0_DUST - left;
			if (deposited > 0)
				ch->SetQuestFlag(PLAYERBOT_G0_BANKED_FLAG, deposited);
			if (deposited >= PLAYERBOT_G0_DUST)
				++s_kPlayerBotG0Stats.deposited;
			sys_log(0, "PLAYERBOT_G0: dust deposited pid=%u name=%s level=%u champion=%d count=%d bag_left=%d box=%d",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), deposited,
					GetPlayerBotG0DustHeld(ch), CountPlayerBotG0BoxDust(box));
			return deposited;
		}
		// Out: the package is for it now.
		if (!b->bNeeder)
			return 0;
		int left = PLAYERBOT_G0_DUST;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM && left > 0; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (!item || item->GetVnum() != PLAYERBOT_MAGIC_DUST_VNUM)
				continue;
			if ((int)item->GetCount() > left)
			{
				if (ch->GetEmptyInventory(1) < 0)
					break;
				item->SetCount(item->GetCount() - left);
				ITEM_MANAGER::instance().FlushDelayedSave(item);
				ch->AutoGiveItem(PLAYERBOT_MAGIC_DUST_VNUM, left, -1, false);
				left = 0;
				break;
			}
			const int cell = ch->GetEmptyInventory(item->GetSize());
			if (cell < 0)
				break;
			char szHint[128];
			snprintf(szHint, sizeof(szHint), "%s %u", item->GetName(), (unsigned int)item->GetCount());
			left -= (int)item->GetCount();
			box->Remove(pos);
			item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			FlushPlayerBotItemRow(item);
			LogManager::instance().ItemLog(ch, item, "SAFEBOX GET", szHint);
		}
		const int withdrawn = PLAYERBOT_G0_DUST - left;
		// Out as far as the box had them: the flag goes (the package waits for the rest the usual way).
		if (left == 0 || CountPlayerBotG0BoxDust(box) == 0)
		{
			ch->SetQuestFlag(PLAYERBOT_G0_BANKED_FLAG, 0);
			++s_kPlayerBotG0Stats.withdrawn;
		}
		sys_log(0, "PLAYERBOT_G0: dust withdrawn pid=%u name=%s level=%u champion=%d count=%d have=%d box_left=%d",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), withdrawn,
				GetPlayerBotG0DustHeld(ch), CountPlayerBotG0BoxDust(box));
		return withdrawn;
	}

	// ------------------------------------------------------------ the operator's test file, the census

	void RunPlayerBotG0TestFile(DWORD dwNow)
	{
		if (dwNow - s_kPlayerBotG0Stats.dwLastTestLook < 10000)
			return;
		s_kPlayerBotG0Stats.dwLastTestLook = dwNow;
		FILE* fp = fopen(PLAYERBOT_G0_TEST_FILE, "r");
		if (!fp)
			return;
		char line[128];
		std::vector<std::string> lines;
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_G0_TEST_FILE);
		rename(PLAYERBOT_G0_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "", arg[32] = "";
			if (sscanf(lines[l].c_str(), "%31s %31s", cmd, arg) < 1)
				continue;
			const int n = !strcmp(arg, "all") ? 100000 : atoi(arg);
			int done = 0, looked = 0;
			for (TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
				if (!ch || !IsPlayerBotG0Needer(ch))
					continue;
				++looked;
				const int have = GetPlayerBotG0DustHeld(ch);
				if (!strcmp(cmd, "dust") && done < n)
				{
					if (have < PLAYERBOT_G0_DUST)
						ch->AutoGiveItem(PLAYERBOT_MAGIC_DUST_VNUM, PLAYERBOT_G0_DUST - have, -1, false);
					++done;
					sys_log(0, "PLAYERBOT_G0: test dust pid=%u name=%s have=%d->%d map=%ld", ch->GetPlayerID(), ch->GetName(),
							have, GetPlayerBotG0DustHeld(ch), ch->GetMapIndex());
				}
				else if (!strcmp(cmd, "status"))
					sys_log(0, "PLAYERBOT_G0: test status pid=%u name=%s level=%u champion=%d have=%d need=%d map=%ld",
							ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), have,
							PLAYERBOT_G0_DUST, ch->GetMapIndex());
			}
			sys_log(0, "PLAYERBOT_G0: test %s asked=%d done=%d waiting_here=%d", cmd, n, done, looked);
		}
	}

	void LogPlayerBotG0Census(DWORD dwNow)
	{
		if (s_kPlayerBotG0Stats.dwLastCensus != 0 && dwNow - s_kPlayerBotG0Stats.dwLastCensus < PLAYERBOT_G0_CENSUS_MS)
			return;
		s_kPlayerBotG0Stats.dwLastCensus = dwNow;
		int needers = 0, ready = 0, savers = 0, banked = 0;
		for (std::map<DWORD, TPlayerBotG0>::const_iterator it = s_mapPlayerBotG0.begin(); it != s_mapPlayerBotG0.end(); ++it)
		{
			if (!it->second.bSaver)	// MT2009_PLUS_BOT_YOHARA_G0_V2
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch)
				continue;
			if (IsPlayerBotG0DustBanked(ch))
				++banked;
			if (!it->second.bNeeder)
			{
				++savers;
				continue;
			}
			++needers;
			if (GetPlayerBotG0DustHeld(ch) >= PLAYERBOT_G0_DUST)
				++ready;
		}
		sys_log(0, "PLAYERBOT_G0: census waiting=%d with_dust=%d savers=%d banked=%d given=%u sold_to_bot=%u sold_to_npc=%u "
				"deposited=%u withdrawn=%u trips=%u dust_bought=%u spent=%lld dust_made=%u",
				needers, ready, savers, banked, s_kPlayerBotG0Stats.given, s_kPlayerBotG0Stats.sold, s_kPlayerBotG0Stats.soldNpc,
				s_kPlayerBotG0Stats.deposited, s_kPlayerBotG0Stats.withdrawn, s_kPlayerBotG0Stats.trips,
				s_kPlayerBotG0Stats.dustBought, s_kPlayerBotG0Stats.spent, s_kPlayerBotG0Stats.dustMade);
	}

	// ------------------------------------------------------------ the tick

	// The AI's tick, beside the Alchemist's errand: true when it did something this tick (the package, a sale).
	bool ManagePlayerBotG0(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		RunPlayerBotG0TestFile(dwNow);
		LogPlayerBotG0Census(dwNow);
		if (!ch || ch->IsDead() || !ch->IsItemLoaded())
			return false;
		TPlayerBotG0* b = LookPlayerBotG0(ch, dwNow);
		if (!b || (int)(b->dwNextManage - dwNow) > 0)
			return false;
		b->dwNextManage = dwNow + PLAYERBOT_G0_LOOK_MS;
		// MT2009_PLUS_BOT_YOHARA_G0_V3: a bot that got its Yohara gear another way (a cohort's, its own glove or jade)
		// counts as having had the package (the owner, 22 October: "wtedy bot traktuje to, ze juz otrzymal pakiet") -
		// the flag set, and the dust it banked is its own again (out of the box by the usual withdrawal, sold or used).
		if (!b->bSaver && ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) == 0 &&
				(IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) || HasPlayerBotYoharaGear(ch)))
		{
			ch->SetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG, 1);
			ch->SetQuestFlag(PLAYERBOT_G0_GIVEN_AT_FLAG, (int)get_global_time());
			const bool banked = IsPlayerBotG0DustBanked(ch);
			if (banked)
				ch->SetQuestFlag(PLAYERBOT_G0_BANKED_FLAG, 0);
			sys_log(0, "PLAYERBOT_G0: counted as given pid=%u name=%s level=%u cohort=%d yohara_gear=%d banked_dust_freed=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(),
					IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) ? 1 : 0, HasPlayerBotYoharaGear(ch) ? 1 : 0, banked ? 1 : 0);
			return false;
		}
		const bool village = IsPlayerBotVillageMap(ch->GetMapIndex()) && !ch->GetExchange() && !ch->GetMyShop();
		if (b->bSaver)	// MT2009_PLUS_BOT_YOHARA_G0_V2: a saver from level 110 too
		{
			const int have = GetPlayerBotG0DustHeld(ch);
			const bool banked = IsPlayerBotG0DustBanked(ch);
			if (b->bNeeder && !banked && have >= PLAYERBOT_G0_DUST && village)
				return GivePlayerBotG0(ch, state, *b, dwNow);
			if ((int)(b->dwNextWaitLog - dwNow) <= 0)
			{
				b->dwNextWaitLog = dwNow + PLAYERBOT_G0_WAIT_LOG_MS;
				sys_log(0, "PLAYERBOT_G0: waiting for dust pid=%u name=%s level=%u champion=%d stage=%s have=%d need=%d banked=%d "
						"bought=%d made_at_alchemist=%d trips=%d map=%ld gold=%lld",
						ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch),
						b->bNeeder ? (banked ? "to_withdraw" : "needer") : (banked ? "banked" : (have >= PLAYERBOT_G0_DUST ? "to_deposit" : "saver")),
						have, PLAYERBOT_G0_DUST, ch->GetQuestFlag(PLAYERBOT_G0_BANKED_FLAG), b->iBought, b->iMade, b->iTrips,
						ch->GetMapIndex(), (long long)ch->GetGold());
			}
		}
		if (village && IsPlayerBotSungmaWillUser(ch) && (int)(b->dwNextSaleLook - dwNow) <= 0)
		{
			b->dwNextSaleLook = dwNow + PLAYERBOT_G0_SALE_LOOK_MS;
			return SellPlayerBotG0Spare(ch);
		}
		return false;
	}
}

#endif
