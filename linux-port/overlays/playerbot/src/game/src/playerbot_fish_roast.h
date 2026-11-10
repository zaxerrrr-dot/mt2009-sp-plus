// MT2009_PLUS_BOT_FISH_ROAST_V1 (the owner, 10 November 2026, the fish sheet's last column):
//   "Zawsze otwieraja ryby" - a live fish a bot catches is opened (killed) at once (ProcessPlayerBotCatch, as before);
//   "Zawsze przepalaja ryby na ognisku - ale tylko te, ktore maja wartosc" - the dead fish whose ROASTED form has a value
//     on his sheet (PLAYERBOT_ROASTED_FISH_PRICES, playerbot_price_tables.h) go on a campfire (Wysuszone Drzewo 27600,
//     bought at the Fisherman 9009 when the bot has none);
//   "Ryby, ktore sa oznaczone jako smieci - sprzedaja u NPC po otwarciu" - the dead fish of a "smieci" kind are sold to
//     the NPC right after the opening: at once when the bot stands at a fishing bank (the Fisherman's), else at the
//     next merchant visit (the junk rule, IsPlayerBotJunkItem); never roasted, never listed;
//   "Ryby, ktore maja wartosc - maja wartosc po przepaleniu" - the price is the roasted fish's: a valuable roasted fish
//     goes on the lada at the owner's number (unscaled; the glut tiers and the market floor apply), past the small
//     reserve of the buff fish a bot eats itself (GetPlayerBotLadaFishKeep). A dead fish of a valuable kind is not
//     sold - it is roasted.
//
// The kinds, from fishing.cpp's table and fishing::Grill (a dead fish + 30, a live one + 60) and the item_proto:
// kind n = 0..24 is live 27803+n, dead 27833+n, roasted 27863+n. Piskorz (n 14: 27817 / 27847 / 27877) is not caught
// on this world (4 November) and has no value on the sheet: it is junk like the "smieci" kinds. 27828-27830 and
// 27858-27860 are not fish of this proto; nothing here names them.
//
// Switches (event flags, read once a second):
//   m2_bot_fish_roast_off        1: the whole rule off - the old fish handling (the proto-gold lada floor, the ten
//                                cheap dead fish kept for the fire, every dead fish on the fire, the sheet's scaling);
//   m2_bot_fish_wood_cap         the firewood a core buys in an hour, all bots together (default 600, 1..100000);
//                                MT2009_PLUS_BOT_PEARL_FISHERS_V1 (the owner, 10 November 2026: "pieczenie ryb dla botow
//                                jest darmowe"): the wood is given, not bought, and no cap applies (the census's
//                                wood_free) - m2_bot_fish_wood_free_off 1 buys it again (playerbot_activities.h,
//                                BuyPlayerBotFishWood);
//   m2_bot_fish_roast_min        the valuable dead fish a bot that is not fishing holds before it lights a fire of its
//                                own (default 1 - the cheapest roasted value, 40 000, is twice the wood's 20 000);
//   m2_bot_fish_roast_check_min  how often such a bot looks, minutes (default 10, 1..240): the catch of a lada
//                                withdrawal or a trade is roasted in one fire, not one fish a fire.
// Census: "PLAYERBOT_FISHROAST: census" every 10 minutes (each core): opened, fires, roasted (and per kind), junk sold
// at the bank / at a merchant (units, yang), roasted listed / sold on the lada (lines, units, yang), firewood bought /
// refused by the cap / unaffordable.
#ifndef __INC_METIN2_PLAYERBOT_FISH_ROAST_H__
#define __INC_METIN2_PLAYERBOT_FISH_ROAST_H__

namespace
{
	const DWORD PLAYERBOT_FISH_KIND_LIVE_FIRST = 27803;
	const DWORD PLAYERBOT_FISH_KIND_DEAD_FIRST = 27833;
	const DWORD PLAYERBOT_FISH_KIND_ROAST_FIRST = 27863;
	const int PLAYERBOT_FISH_KIND_COUNT = 25;
	const DWORD PLAYERBOT_FISH_ROAST_CENSUS_MS = 10 * 60 * 1000;

	struct TPlayerBotFishRoastCfg
	{
		bool on;
		int woodCapHour, minBatch, checkMin;
		TPlayerBotFishRoastCfg() : on(true), woodCapHour(600), minBatch(1), checkMin(10) {}
	};
	TPlayerBotFishRoastCfg s_kPlayerBotFishRoastCfg;

	const TPlayerBotFishRoastCfg& GetPlayerBotFishRoastCfg()
	{
		static DWORD s_dwAt = 0;
		static bool s_bLogged = false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			TPlayerBotFishRoastCfg& c = s_kPlayerBotFishRoastCfg;
			const TPlayerBotFishRoastCfg was = c;
			auto value = [&q](const char* flag, int def, int lo, int hi) {
				const int v = q.GetEventFlag(flag);
				return v <= 0 ? def : std::max(lo, std::min(hi, v));
			};
			c.on = q.GetEventFlag("m2_bot_fish_roast_off") == 0;
			c.woodCapHour = value("m2_bot_fish_wood_cap", 600, 1, 100000);
			c.minBatch = value("m2_bot_fish_roast_min", 1, 1, 200);
			c.checkMin = value("m2_bot_fish_roast_check_min", 10, 1, 240);
			if (!s_bLogged || was.on != c.on || was.woodCapHour != c.woodCapHour || was.minBatch != c.minBatch ||
					was.checkMin != c.checkMin)
			{
				s_bLogged = true;
				sys_log(0, "PLAYERBOT_FISHROAST: config on=%d wood_cap_hour=%d roast_min=%d check_min=%d",
						c.on ? 1 : 0, c.woodCapHour, c.minBatch, c.checkMin);
			}
		}
		return s_kPlayerBotFishRoastCfg;
	}

	bool IsPlayerBotFishRoastOn()
	{
		return GetPlayerBotFishRoastCfg().on;
	}

	// The owner's price of a roasted fish, yang a piece (PLAYERBOT_ROASTED_FISH_PRICES), or 0: not a valuable roasted
	// kind, or the rule is off.
	DWORD GetPlayerBotRoastedFishOwnerPrice(DWORD vnum)
	{
		if (vnum < PLAYERBOT_FISH_KIND_ROAST_FIRST || vnum >= PLAYERBOT_FISH_KIND_ROAST_FIRST + PLAYERBOT_FISH_KIND_COUNT ||
				!IsPlayerBotFishRoastOn())
			return 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_ROASTED_FISH_PRICES) / sizeof(PLAYERBOT_ROASTED_FISH_PRICES[0]); ++i)
			if (PLAYERBOT_ROASTED_FISH_PRICES[i].dwVnum == vnum)
				return PLAYERBOT_ROASTED_FISH_PRICES[i].dwPrice;
		return 0;
	}

	bool IsPlayerBotDeadFishKindVnum(DWORD vnum)
	{
		return vnum >= PLAYERBOT_FISH_KIND_DEAD_FIRST && vnum < PLAYERBOT_FISH_KIND_DEAD_FIRST + PLAYERBOT_FISH_KIND_COUNT;
	}

	// A dead fish whose roasted form has a value: the fire's (rule on).
	bool IsPlayerBotValuableDeadFish(DWORD vnum)
	{
		return IsPlayerBotDeadFishKindVnum(vnum) &&
				GetPlayerBotRoastedFishOwnerPrice(vnum - PLAYERBOT_FISH_KIND_DEAD_FIRST + PLAYERBOT_FISH_KIND_ROAST_FIRST) > 0;
	}

	// A dead fish of a "smieci" kind (Piskorz too): the NPC's right after the opening (rule on).
	bool IsPlayerBotJunkDeadFish(DWORD vnum)
	{
		return IsPlayerBotDeadFishKindVnum(vnum) && IsPlayerBotFishRoastOn() && !IsPlayerBotValuableDeadFish(vnum);
	}

	// ------------------------------------------------------------------------------------------------ the census
	struct TPlayerBotFishRoastCensus
	{
		unsigned int opened = 0, fires = 0, fireRefused = 0, roasted = 0;
		unsigned int roastedKind[PLAYERBOT_FISH_KIND_COUNT] = {};
		unsigned int junkNowUnits = 0, junkMerchantUnits = 0;
		unsigned long long junkNowYang = 0, junkMerchantYang = 0;
		unsigned int listedLines = 0, soldLines = 0;
		unsigned long long listedUnits = 0, soldUnits = 0, soldYang = 0;
		unsigned int woodBought = 0, woodCapped = 0, woodNoGold = 0, woodFree = 0;	// woodFree: MT2009_PLUS_BOT_PEARL_FISHERS_V1
		unsigned long long woodYang = 0;
	};
	TPlayerBotFishRoastCensus s_kPlayerBotFishRoastCensus;
	// The firewood bought this hour on this core (m2_bot_fish_wood_cap).
	DWORD s_dwPlayerBotFishWoodHourAt = 0;
	int s_iPlayerBotFishWoodThisHour = 0;

	void NotePlayerBotFishOpened()
	{
		++s_kPlayerBotFishRoastCensus.opened;
	}

	void NotePlayerBotFishRoasted(DWORD deadVnum, int count)
	{
		if (!IsPlayerBotDeadFishKindVnum(deadVnum) || count <= 0)
			return;
		s_kPlayerBotFishRoastCensus.roasted += (unsigned int)count;
		s_kPlayerBotFishRoastCensus.roastedKind[deadVnum - PLAYERBOT_FISH_KIND_DEAD_FIRST] += (unsigned int)count;
	}

	void NotePlayerBotFishJunkSold(int units, long long yang, bool atBank)
	{
		if (units <= 0)
			return;
		TPlayerBotFishRoastCensus& k = s_kPlayerBotFishRoastCensus;
		(atBank ? k.junkNowUnits : k.junkMerchantUnits) += (unsigned int)units;
		(atBank ? k.junkNowYang : k.junkMerchantYang) += (unsigned long long)std::max(0LL, yang);
	}

	// A lada line of a valuable roasted fish put up (playerbot_lada.h) / sold (playerbot_offline_shop.h).
	void NotePlayerBotFishRoastListed(DWORD vnum, unsigned int count)
	{
		if (GetPlayerBotRoastedFishOwnerPrice(vnum) == 0)
			return;
		++s_kPlayerBotFishRoastCensus.listedLines;
		s_kPlayerBotFishRoastCensus.listedUnits += count;
	}

	void NotePlayerBotFishRoastSold(DWORD vnum, unsigned int count, long long price)
	{
		if (GetPlayerBotRoastedFishOwnerPrice(vnum) == 0)
			return;
		++s_kPlayerBotFishRoastCensus.soldLines;
		s_kPlayerBotFishRoastCensus.soldUnits += count;
		s_kPlayerBotFishRoastCensus.soldYang += (unsigned long long)std::max(0LL, price);
	}

	// One more piece of firewood bought this hour, if the core's cap allows it.
	bool ReservePlayerBotFishWood(DWORD dwNow)
	{
		if (s_dwPlayerBotFishWoodHourAt == 0 || dwNow - s_dwPlayerBotFishWoodHourAt >= 60U * 60U * 1000U)
		{
			s_dwPlayerBotFishWoodHourAt = dwNow ? dwNow : 1;
			s_iPlayerBotFishWoodThisHour = 0;
		}
		if (s_iPlayerBotFishWoodThisHour >= GetPlayerBotFishRoastCfg().woodCapHour)
		{
			++s_kPlayerBotFishRoastCensus.woodCapped;
			return false;
		}
		++s_iPlayerBotFishWoodThisHour;
		return true;
	}

	// MT2009_PLUS_BOT_PEARL_FISHERS_V1: the pearls (27992-27994) and the clam (27987) put up on the lada / sold off the
	// stands, by kind (white, blue, red, clam) - logged and cleared by the pearls' census (playerbot_pearl_fishers.h).
	struct TPlayerBotPearlStallCensus
	{
		unsigned int listedUnits[4] = { 0, 0, 0, 0 }, soldUnits[4] = { 0, 0, 0, 0 };
		unsigned long long soldYang[4] = { 0, 0, 0, 0 };
	};
	TPlayerBotPearlStallCensus s_kPlayerBotPearlStallCensus;

	int GetPlayerBotPearlStallKind(DWORD vnum)
	{
		if (vnum >= 27992 && vnum <= 27994)
			return (int)(vnum - 27992);
		return vnum == 27987 ? 3 : -1;
	}

	void NotePlayerBotPearlListed(DWORD vnum, unsigned int count)
	{
		const int kind = GetPlayerBotPearlStallKind(vnum);
		if (kind >= 0)
			s_kPlayerBotPearlStallCensus.listedUnits[kind] += count;
	}

	void NotePlayerBotPearlSold(DWORD vnum, unsigned int count, long long price)
	{
		const int kind = GetPlayerBotPearlStallKind(vnum);
		if (kind < 0)
			return;
		s_kPlayerBotPearlStallCensus.soldUnits[kind] += count;
		s_kPlayerBotPearlStallCensus.soldYang[kind] += (unsigned long long)std::max(0LL, price);
	}

	void LogPlayerBotFishRoastCensus(DWORD dwNow)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = dwNow ? dwNow : 1;
			return;
		}
		if (dwNow - s_dwAt < PLAYERBOT_FISH_ROAST_CENSUS_MS)
			return;
		s_dwAt = dwNow ? dwNow : 1;
		TPlayerBotFishRoastCensus& k = s_kPlayerBotFishRoastCensus;
		char kinds[512];
		kinds[0] = '\0';
		size_t used = 0;
		for (int i = 0; i < PLAYERBOT_FISH_KIND_COUNT && used + 24 < sizeof(kinds); ++i)
		{
			if (k.roastedKind[i] == 0)
				continue;
			const int n = snprintf(kinds + used, sizeof(kinds) - used, "%s%u:%u", used ? "," : "",
					(unsigned int)(PLAYERBOT_FISH_KIND_ROAST_FIRST + i), k.roastedKind[i]);
			if (n <= 0)
				break;
			used += (size_t)n;
		}
		sys_log(0, "PLAYERBOT_FISHROAST: census on=%d opened=%u fires=%u fire_refused=%u roasted=%u roasted_kinds=%s "
				"junk_bank_units=%u junk_bank_yang=%llu junk_merchant_units=%u junk_merchant_yang=%llu "
				"listed_lines=%u listed_units=%llu sold_lines=%u sold_units=%llu sold_yang=%llu "
				"wood_bought=%u wood_yang=%llu wood_capped=%u wood_no_gold=%u wood_this_hour=%d wood_free=%u",
				IsPlayerBotFishRoastOn() ? 1 : 0, k.opened, k.fires, k.fireRefused, k.roasted, used ? kinds : "-",
				k.junkNowUnits, k.junkNowYang, k.junkMerchantUnits, k.junkMerchantYang,
				k.listedLines, k.listedUnits, k.soldLines, k.soldUnits, k.soldYang,
				k.woodBought, k.woodYang, k.woodCapped, k.woodNoGold, s_iPlayerBotFishWoodThisHour, k.woodFree);
		k = TPlayerBotFishRoastCensus();
	}
}

#endif
