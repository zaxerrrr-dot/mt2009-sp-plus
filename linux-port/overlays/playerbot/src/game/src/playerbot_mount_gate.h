#ifndef __INC_METIN2_PLAYERBOT_MOUNT_GATE_H__
#define __INC_METIN2_PLAYERBOT_MOUNT_GATE_H__

// MT2009_PLUS_BOT_MOUNT_GATE_V1 - the horse row of the progression checklist (playerbot_progression.h) answered by a
// riding mount, for the bots (the owner, 8 November 2026: "Dwie opcje rozwoju: (1) Bot ma dostep do ItemShopa -> kupuje
// wierzchowca -> nie musi miec konia. (2) Bot nie ma dostepu do ItemShopa -> nie ma SM na wierzchowca -> robi konia. Ale
// jesli ma SM i ma wierzchowca, do lvl 95 niech i tak robi powoli konia, na przyklad jeden poziom dziennie / dwa poziomy
// dziennie"). A player's checklist, horse and shop are untouched; no coin is added anywhere.
//
// The measure that asked for it (the test world after the 23:07 reset of 7 November, 2000 bots of ~100 000 SM each): at
// gate 45 631 of the 633 held bots failed "kon poz. 12" - the horse training short of yang (534) and of goods (488) -
// and the ItemShop sells no horse medal and no horse book.
//
// What a mount is here (IsPlayerBotGateMountItem): an item of ITEM_COSTUME / COSTUME_MOUNT with a race in value 1 (what
// CMountSystem summons and the bots' riding code puts on, WEAR_COSTUME_MOUNT - the same definition the look pass and the
// catalogue's mount list use), of a level the bot may wear, worn or in the bag, and lasting: no time limit at all, or at
// least m2_bot_mountgate_min_days days (default PLAYERBOT_MOUNTGATE_MIN_DAYS = 10) left. The starter Appaloosa (56000,
// Skrzynia Ucznia: a 7-day REAL_TIME seal; Przekaska Appaloosa 38103 adds 7 days once it has under 48 h - so never over
// ~9 days) does NOT count: it is a starter's loan, not the mount option 1 buys, and it would run out a week after the
// gate it let through. A V3-bought mount (a 30-day line, or a permanent one) does.
//
// The ItemShop's mounts (itemshop3.shop, category 9 "Mounty", Smocze Monety, test DB 8 November 2026): 71115-71128 (the
// old "ride tickets": Dzik/Wilk/Tygrys/Lew niebieski 71115/71117/71119/71121 lv75/80, Bialy Lew 71124 lv0, Dzik Wojenny /
// Wilk Wojenny / Szarzujacy Tygrys / Waleczny Lew 71125-71128 lv20) at 100 SM with no time on the line and none in the
// proto - PERMANENT; every other mount (52001-52118 the summon seals, 56000 Appaloosa, 70614, 71134-71288 ...) 299 SM for
// 43 200 minutes (30 days). The pick (PickPlayerBotGateMountLine): a permanent line before a timed one, the longer before
// the shorter, the cheaper before the dearer, one of the equal best by the bot's pid - so a bot of 20+ buys one of the
// five permanent 100 SM mounts once and never again.
//
// The purchase (ManagePlayerBotProgShopMount, from the progression shop's step - PLAYERBOT_PSHOP_STEP_MS, while the bot is
// held with the horse row unmet): one mount, reason "progshop_mount" - urgent in the day's pool and inside the gate's
// progression-shop budget (GetPlayerBotProgShopPoolRoom). It is functional, not a cosmetic: the monthly cosmetics rule
// (MT2009_PLUS_BOT_LOOK_MONTHLY_V1) neither blocks it nor is started by it (the reason is no look kind); and it never
// buys while the bot holds a counting mount (worn or in the bag). The mount goes on at once in place of whatever the
// slot holds (the Appaloosa goes to the bag) - ManagePlayerBotMountGate, every PLAYERBOT_MOUNTGATE_WEAR_MS - and the
// riding code rides the worn seal as before (playerbot_movement.h). A bot with no V3 access (ISHOP_SOURCE != 2, the shop
// off, a companion) or short of SM / pool / budget keeps the horse row as today and trains the horse.
//
// The slow horse (IsPlayerBotHorseDayCapped): a bot holding a counting mount under level m2_bot_mountgate_slow_level
// (default 95) still raises its horse, but at most m2_bot_mountgate_horse_per_day levels (default 1, 1-10) a Polish day
// (Europe/Warsaw). The day's start level is kept in the bot's quest flags (playerbot.mg_hday / playerbot.mg_hbase), so a
// restart forgets nothing, and every way up counts (the trainings, the trials' collection, the 21+ feed tries). Over the
// cap the stable pass does not start a visit (ManagePlayerBotHorse) and the horse's planning answers "nothing to advance"
// (CanPlayerBotAdvanceHorse: no medal hunt, no medal buying, no savings) - so the yang is not drained.
//
// Switches (event flags): m2_bot_mountgate_off 1 - all of it off (the horse row needs the horse, no purchase, no cap);
// m2_bot_mountgate_buy_off 1 - no purchase (a held mount still counts); m2_bot_mountgate_slow_off 1 - no daily cap;
// m2_bot_mountgate_min_days N (1-90); m2_bot_mountgate_horse_per_day N (1-10); m2_bot_mountgate_slow_level N (1-250).
// The log: "PLAYERBOT_MOUNTGATE: bought ..." / "worn ..." / "buy failed ..." / "horse day cap ..." (throttled) and the
// census every PLAYERBOT_MOUNTGATE_CENSUS_MS: "PLAYERBOT_MOUNTGATE: census ..." - the horse rows weighed by result (met by
// the horse / by the mount / unmet), the bots held by the horse row now, the mounts bought (and SM), the purchase
// refusals by reason, the bots with a counting mount under the slow level, their horse levels gained today and the bots
// at the cap.
//
// An implementation fragment: included once from playerbot_manager.cpp right after playerbot_progression_shop.h (the
// gate's record and budget); playerbot_activities.h, playerbot_progression.h and playerbot_progression_shop.h call it
// through forward declarations.

namespace
{
	const int PLAYERBOT_MOUNTGATE_MIN_DAYS = 10;
	const int PLAYERBOT_MOUNTGATE_HORSE_PER_DAY = 1;
	const int PLAYERBOT_MOUNTGATE_SLOW_LEVEL = 95;
	const DWORD PLAYERBOT_MOUNTGATE_CACHE_MS = 20000;
	const DWORD PLAYERBOT_MOUNTGATE_WEAR_MS = 10000;
	const DWORD PLAYERBOT_MOUNTGATE_CENSUS_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_MOUNTGATE_FLAG_DAY = "playerbot.mg_hday";
	const char* const PLAYERBOT_MOUNTGATE_FLAG_BASE = "playerbot.mg_hbase";

	enum
	{
		PLAYERBOT_MOUNTGATE_ROW_HORSE = 1,	// the horse level met the row
		PLAYERBOT_MOUNTGATE_ROW_MOUNT = 2,	// the horse short, the mount met it
		PLAYERBOT_MOUNTGATE_ROW_UNMET = 3,	// neither
	};

	struct TPlayerBotMountGateCfg
	{
		bool on, buy, slow;
		int minDays, perDay, slowLevel;
	};

	const TPlayerBotMountGateCfg& GetPlayerBotMountGateCfg()
	{
		static DWORD s_dwAt = 0;
		static TPlayerBotMountGateCfg s_kCfg = { true, true, true, PLAYERBOT_MOUNTGATE_MIN_DAYS,
			PLAYERBOT_MOUNTGATE_HORSE_PER_DAY, PLAYERBOT_MOUNTGATE_SLOW_LEVEL };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			s_kCfg.on = q.GetEventFlag("m2_bot_mountgate_off") == 0;
			s_kCfg.buy = q.GetEventFlag("m2_bot_mountgate_buy_off") == 0;
			s_kCfg.slow = q.GetEventFlag("m2_bot_mountgate_slow_off") == 0;
			const int days = q.GetEventFlag("m2_bot_mountgate_min_days");
			s_kCfg.minDays = days >= 1 && days <= 90 ? days : PLAYERBOT_MOUNTGATE_MIN_DAYS;
			const int per = q.GetEventFlag("m2_bot_mountgate_horse_per_day");
			s_kCfg.perDay = per >= 1 && per <= 10 ? per : PLAYERBOT_MOUNTGATE_HORSE_PER_DAY;
			const int lvl = q.GetEventFlag("m2_bot_mountgate_slow_level");
			s_kCfg.slowLevel = lvl >= 1 && lvl <= 250 ? lvl : PLAYERBOT_MOUNTGATE_SLOW_LEVEL;
		}
		return s_kCfg;
	}

	struct TPlayerBotMountGateStats
	{
		unsigned int bought, buyNoLine, buyNoCoins, buyBudget, buyFailed, worn, wearFailed;
		long long sm;
		std::map<DWORD, unsigned int> boughtVnums;
		TPlayerBotMountGateStats() : bought(0), buyNoLine(0), buyNoCoins(0), buyBudget(0), buyFailed(0), worn(0),
			wearFailed(0), sm(0) {}
	};
	TPlayerBotMountGateStats s_kPlayerBotMountGate;
	unsigned int s_uPlayerBotMountGateBoughtEver = 0;

	// pid -> (the last horse row's result, when)
	std::map<DWORD, std::pair<BYTE, DWORD> > s_mapPlayerBotMountGateRow;
	// pid -> (has a counting mount, until when the answer holds)
	std::map<DWORD, std::pair<bool, DWORD> > s_mapPlayerBotMountGateHas;
	// pid -> the next wear check
	std::map<DWORD, DWORD> s_mapPlayerBotMountGateWearAt;

	// The day of Polish time (Europe/Warsaw: CEST from the last Sunday of March 01:00 UTC to the last Sunday of October
	// 01:00 UTC, CET otherwise) as a day number.
	time_t PlayerBotMountGateLastSunday(int year, int monthAfter0)
	{
		struct tm a;
		memset(&a, 0, sizeof(a));
		a.tm_year = year - 1900;
		a.tm_mon = monthAfter0;
		a.tm_mday = 1;
		const time_t last = timegm(&a) - 86400;
		struct tm b;
		gmtime_r(&last, &b);
		return last - (time_t)b.tm_wday * 86400;
	}

	int GetPlayerBotMountGateWarsawDay()
	{
		const time_t t = (time_t)get_global_time();
		struct tm g;
		gmtime_r(&t, &g);
		const int y = g.tm_year + 1900;
		const time_t from = PlayerBotMountGateLastSunday(y, 3) + 3600;
		const time_t to = PlayerBotMountGateLastSunday(y, 10) + 3600;
		const time_t w = t + ((t >= from && t < to) ? 7200 : 3600);
		return (int)(w / 86400);
	}

	// Seconds a mount seal has left (LONG_MAX: no time limit). A first-use seal not used yet holds its duration in
	// socket 0 (a small value) or already its end date (a big one), as the engine reads it (MT2009_PLUS_REALTIME_FIRSTUSE_V1).
	long GetPlayerBotMountSecondsLeft(LPITEM item)
	{
		if (!item || !item->GetProto())
			return 0;
		const TItemTable* proto = item->GetProto();
		const long now = (long)get_global_time();
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE type = proto->aLimits[i].bType;
			const long s0 = item->GetSocket(0);
			if (type == LIMIT_REAL_TIME)
				return s0 > 0 ? s0 - now : 0;
			if (type == LIMIT_REAL_TIME_START_FIRST_USE)
			{
				if (s0 >= 1000000000L)
					return s0 - now;
				if (s0 > 0)
					return s0;
				return proto->aLimits[i].lValue > 0 ? proto->aLimits[i].lValue : 7L * 24 * 60 * 60;
			}
			if (type == LIMIT_TIMER_BASED_ON_WEAR)
				return s0;
		}
		return LONG_MAX;
	}

	bool IsPlayerBotGateMountProto(LPCHARACTER ch, const TItemTable* proto)
	{
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
		return ch && proto && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_MOUNT && proto->alValues[1] != 0 &&
				IsPlayerBotLookLevelReached(ch, proto) && IsPlayerBotProtoForCharacter(ch, proto);
#else
		(void)ch;
		(void)proto;
		return false;
#endif
	}

	// A mount that answers the horse row (see the header).
	bool IsPlayerBotGateMountItem(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->isLocked() || item->IsExchanging() || !IsPlayerBotGateMountProto(ch, item->GetProto()))
			return false;
		const long left = GetPlayerBotMountSecondsLeft(item);
		return left == LONG_MAX || left >= (long)GetPlayerBotMountGateCfg().minDays * 86400L;
	}

	// The counting mount worn (preferred) or in the bag; NULL none.
	LPITEM FindPlayerBotGateMount(LPCHARACTER ch, bool* pWorn)
	{
		if (pWorn)
			*pWorn = false;
		if (!ch || !ch->IsItemLoaded())
			return NULL;
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
		LPITEM worn = ch->GetWear(WEAR_COSTUME_MOUNT);
		if (worn && IsPlayerBotGateMountItem(ch, worn))
		{
			if (pWorn)
				*pWorn = true;
			return worn;
		}
		LPITEM best = NULL;
		long bestLeft = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotGateMountItem(ch, item))
				continue;
			const long left = GetPlayerBotMountSecondsLeft(item);
			if (!best || left > bestLeft)
			{
				best = item;
				bestLeft = left;
			}
		}
		return best;
#else
		return NULL;
#endif
	}

	// Whether the bot holds a counting mount (cached PLAYERBOT_MOUNTGATE_CACHE_MS; a purchase or a wear drops the cache).
	bool HasPlayerBotGateMount(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded())
			return false;
		const DWORD now = get_dword_time();
		std::pair<bool, DWORD>& c = s_mapPlayerBotMountGateHas[ch->GetPlayerID()];
		if (c.second != 0 && (int)(now - c.second) < 0)
			return c.first;
		c.first = FindPlayerBotGateMount(ch, NULL) != NULL;
		c.second = (now ? now : 1) + PLAYERBOT_MOUNTGATE_CACHE_MS;
		return c.first;
	}

	void ForgetPlayerBotGateMountCache(DWORD pid)
	{
		s_mapPlayerBotMountGateHas.erase(pid);
	}

	// playerbot_progression.h: the horse row met by a mount (a bot's - never a player's companion).
	bool IsPlayerBotMountGateMet(LPCHARACTER ch)
	{
		return ch && GetPlayerBotMountGateCfg().on && !IsPlayerBotSidekickPID(ch->GetPlayerID()) && HasPlayerBotGateMount(ch);
	}

	// playerbot_progression.h: a horse row weighed - its result for the census.
	void NotePlayerBotMountGateRow(DWORD pid, BYTE how, DWORD dwNow)
	{
		s_mapPlayerBotMountGateRow[pid] = std::make_pair(how, dwNow ? dwNow : 1);
	}

	// The horse levels gained this Polish day (the day's start kept in the quest flags).
	int GetPlayerBotHorseLevelsToday(LPCHARACTER ch)
	{
		const int day = GetPlayerBotMountGateWarsawDay();
		const int horse = (int)ch->GetHorseLevel();
		if (ch->GetQuestFlag(PLAYERBOT_MOUNTGATE_FLAG_DAY) != day)
		{
			ch->SetQuestFlag(PLAYERBOT_MOUNTGATE_FLAG_DAY, day);
			ch->SetQuestFlag(PLAYERBOT_MOUNTGATE_FLAG_BASE, horse);
			return 0;
		}
		return std::max(0, horse - ch->GetQuestFlag(PLAYERBOT_MOUNTGATE_FLAG_BASE));
	}

	// Whether the slow-horse rule applies to this bot now (a counting mount, under the slow level).
	bool IsPlayerBotSlowHorseBot(LPCHARACTER ch)
	{
		const TPlayerBotMountGateCfg& c = GetPlayerBotMountGateCfg();
		return ch && ch->IsPC() && ch->IsItemLoaded() && c.on && c.slow && (int)ch->GetLevel() < c.slowLevel &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID()) && HasPlayerBotGateMount(ch);
	}

	// playerbot_activities.h: the horse's day is done for a mounted bot under the slow level.
	bool IsPlayerBotHorseDayCapped(LPCHARACTER ch)
	{
		if (!IsPlayerBotSlowHorseBot(ch))
			return false;
		const int today = GetPlayerBotHorseLevelsToday(ch);
		if (today < GetPlayerBotMountGateCfg().perDay)
			return false;
		PlayerBotLogThrottledEvery("mountgate_horse_cap", get_dword_time(), 600000,
				"PLAYERBOT_MOUNTGATE: horse day cap pid=%u name=%s lv=%d horse=%d today=%d cap=%d", ch->GetPlayerID(),
				ch->GetName(), ch->GetLevel(), (int)ch->GetHorseLevel(), today, GetPlayerBotMountGateCfg().perDay);
		return true;
	}

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)
	// The V3 line a bot buys for the gate (see the header); NULL none it may buy. pVnum: the line's item.
	const TPlayerBotItemShopEntry* PickPlayerBotGateMountLine(LPCHARACTER ch, DWORD* pVnum)
	{
		const long minSecs = (long)GetPlayerBotMountGateCfg().minDays * 86400L;
		std::vector<std::pair<const TPlayerBotItemShopEntry*, DWORD> > best;
		long bestSecs = 0;
		DWORD bestPrice = 0;
		for (size_t i = 0; i < s_vecPlayerBotItemShopMount.size(); ++i)
		{
			const DWORD vnum = s_vecPlayerBotItemShopMount[i];
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
			if (!IsPlayerBotGateMountProto(ch, proto))
				continue;
			TPlayerBotItemShopTable::const_iterator it = s_mapPlayerBotItemShopCoins.find(vnum);
			if (it == s_mapPlayerBotItemShopCoins.end())
				continue;
			for (size_t l = 0; l < it->second.size(); ++l)
			{
				const TPlayerBotItemShopEntry& line = it->second[l];
				if (line.dwCount == 0 || line.dwPrice == 0 || ch->GetLevel() < line.bMinLevel)
					continue;
				long secs = line.dwMinutes > 0 ? (long)line.dwMinutes * 60L : GetPlayerBotLookSeconds(proto);
				if (secs == 0)
					secs = LONG_MAX;	// no time on the line nor in the proto: for good
				if (secs < minSecs + 86400L)	// it would stop counting within a day
					continue;
				const bool better = best.empty() || secs > bestSecs || (secs == bestSecs && line.dwPrice < bestPrice);
				const bool equal = !best.empty() && secs == bestSecs && line.dwPrice == bestPrice;
				if (better)
				{
					best.clear();
					bestSecs = secs;
					bestPrice = line.dwPrice;
				}
				if (better || equal)
					best.push_back(std::make_pair(&line, vnum));
			}
		}
		if (best.empty())
			return NULL;
		const size_t pick = (size_t)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x4d4f554eU) % (DWORD)best.size());
		if (pVnum)
			*pVnum = best[pick].second;
		return best[pick].first;
	}

	// playerbot_progression_shop.h (the REQ_HORSE row of a held bot, its step): one mount bought. True: bought, or a
	// counting mount already held (the wear pass puts it on); false: the horse row stays the horse's (counted).
	bool ManagePlayerBotProgShopMount(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotPShopRecord& rec, DWORD dwNow)
	{
		const TPlayerBotMountGateCfg& cfg = GetPlayerBotMountGateCfg();
		if (!ch || !cfg.on || !cfg.buy || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		if (FindPlayerBotGateMount(ch, NULL))
			return true;
		DWORD vnum = 0;
		const TPlayerBotItemShopEntry* line = PickPlayerBotGateMountLine(ch, &vnum);
		if (!line)
		{
			++s_kPlayerBotMountGate.buyNoLine;
			return false;
		}
		if ((long long)line->dwPrice > GetPlayerBotProgShopBudget() - rec.llSpent)
		{
			++s_kPlayerBotMountGate.buyBudget;
			return false;
		}
		if (state.iDragonCoins < (int)line->dwPrice)
		{
			++s_kPlayerBotMountGate.buyNoCoins;
			PlayerBotLogThrottled("mountgate_no_coins", dwNow,
					"PLAYERBOT_MOUNTGATE: buy failed pid=%u name=%s lv=%d gate=%u vnum=%u price=%u why=no_coins coins=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)rec.bGate, vnum, line->dwPrice,
					state.iDragonCoins);
			return false;
		}
		const int coins = state.iDragonCoins;
		if (!BuyPlayerBotIshop3Line(ch, state, *line, vnum, false, 1, "progshop_mount", dwNow))
		{
			++s_kPlayerBotMountGate.buyFailed;
			PlayerBotLogThrottled("mountgate_buy_failed", dwNow,
					"PLAYERBOT_MOUNTGATE: buy failed pid=%u name=%s lv=%d gate=%u vnum=%u line=%u price=%u why=shop coins=%d "
					"(pool / bag / balance - see PLAYERBOT_ISHOP3)", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
					(unsigned int)rec.bGate, vnum, line->dwIndex, line->dwPrice, state.iDragonCoins);
			return false;
		}
		const long long sm = std::max(0LL, (long long)coins - (long long)state.iDragonCoins);
		rec.llSpent += sm;
		rec.bBought = true;
		s_kPlayerBotPShop.sm += sm;
		++s_kPlayerBotMountGate.bought;
		++s_uPlayerBotMountGateBoughtEver;
		s_kPlayerBotMountGate.sm += sm;
		++s_kPlayerBotMountGate.boughtVnums[vnum];
		ForgetPlayerBotGateMountCache(ch->GetPlayerID());
		s_mapPlayerBotMountGateWearAt[ch->GetPlayerID()] = 0;	// on at the next tick
		PlayerBotLogThrottled("mountgate_bought", dwNow,
				"PLAYERBOT_MOUNTGATE: bought pid=%u name=%s lv=%d gate=%u horse=%d vnum=%u line=%u minutes=%u sm=%lld gate_sm=%lld "
				"coins=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)rec.bGate, (int)ch->GetHorseLevel(),
				vnum, line->dwIndex, line->dwMinutes, sm, rec.llSpent, state.iDragonCoins);
		return true;
	}
#endif

	// The census line (see the header).
	void TickPlayerBotMountGateCensus(DWORD dwNow)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = dwNow + PLAYERBOT_MOUNTGATE_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwAt) < 0)
			return;
		s_dwAt = dwNow + PLAYERBOT_MOUNTGATE_CENSUS_MS;
		const TPlayerBotMountGateCfg& cfg = GetPlayerBotMountGateCfg();
		unsigned int rowHorse = 0, rowMount = 0, rowUnmet = 0;
		for (std::map<DWORD, std::pair<BYTE, DWORD> >::iterator it = s_mapPlayerBotMountGateRow.begin();
				it != s_mapPlayerBotMountGateRow.end();)
		{
			if (dwNow - it->second.second > 120000U)
			{
				s_mapPlayerBotMountGateRow.erase(it++);
				continue;
			}
			if (it->second.first == PLAYERBOT_MOUNTGATE_ROW_HORSE)
				++rowHorse;
			else if (it->second.first == PLAYERBOT_MOUNTGATE_ROW_MOUNT)
				++rowMount;
			else
				++rowUnmet;
			++it;
		}
		// the held bots whose unmet rows hold the horse's, per gate
		std::map<int, int> heldHorse;
		for (std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); ++it)
		{
			const TPlayerBotProgress& e = it->second;
			if (!e.bHeld || !e.bEligible || dwNow - e.dwSeen > 60000U)
				continue;
			for (size_t r = 0; r < e.vecShort.size(); ++r)
				if (e.vecShort[r].type == playerbot_progression::REQ_HORSE)
				{
					++heldHorse[e.bGate];
					break;
				}
		}
		std::string held;
		for (std::map<int, int>::const_iterator it = heldHorse.begin(); it != heldHorse.end(); ++it)
		{
			char one[32];
			snprintf(one, sizeof(one), "%s%d:%d", held.empty() ? "" : ",", it->first, it->second);
			held += one;
		}
		// the mounted bots under the slow level: their horse levels today, and those at the cap
		unsigned int mounted = 0, mountedSlow = 0, capped = 0, levelsToday = 0, bots = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(it->first))
				continue;
			++bots;
			if (!HasPlayerBotGateMount(ch))
				continue;
			++mounted;
			if (!IsPlayerBotSlowHorseBot(ch))
				continue;
			++mountedSlow;
			const int today = GetPlayerBotHorseLevelsToday(ch);
			levelsToday += (unsigned int)today;
			if (today >= cfg.perDay)
				++capped;
		}
		std::string vnums;
		for (std::map<DWORD, unsigned int>::const_iterator it = s_kPlayerBotMountGate.boughtVnums.begin();
				it != s_kPlayerBotMountGate.boughtVnums.end(); ++it)
		{
			char one[32];
			snprintf(one, sizeof(one), "%s%u:%u", vnums.empty() ? "" : ",", it->first, it->second);
			vnums += one;
		}
		TPlayerBotMountGateStats& s = s_kPlayerBotMountGate;
		sys_log(0, "PLAYERBOT_MOUNTGATE: census on=%d buy=%d slow=%d min_days=%d per_day=%d slow_level=%d | horse_rows met_by_horse=%u "
				"met_by_mount=%u unmet=%u held_by_horse_row=[%s] | bought=%u (ever %u) sm=%lld vnums=[%s] refused no_line=%u "
				"no_coins=%u budget=%u shop=%u | worn=%u wear_failed=%u | bots=%u mounted=%u mounted_below_slow=%u "
				"horse_levels_today=%u at_day_cap=%u",
				cfg.on ? 1 : 0, cfg.buy ? 1 : 0, cfg.slow ? 1 : 0, cfg.minDays, cfg.perDay, cfg.slowLevel, rowHorse, rowMount,
				rowUnmet, held.c_str(), s.bought, s_uPlayerBotMountGateBoughtEver, s.sm, vnums.empty() ? "-" : vnums.c_str(),
				s.buyNoLine, s.buyNoCoins, s.buyBudget, s.buyFailed, s.worn, s.wearFailed, bots, mounted, mountedSlow,
				levelsToday, capped);
		s = TPlayerBotMountGateStats();
		for (std::map<DWORD, std::pair<bool, DWORD> >::iterator it = s_mapPlayerBotMountGateHas.begin();
				it != s_mapPlayerBotMountGateHas.end();)
		{
			if ((int)(dwNow - it->second.second) > 600000)
				s_mapPlayerBotMountGateHas.erase(it++);
			else
				++it;
		}
		for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotMountGateWearAt.begin(); it != s_mapPlayerBotMountGateWearAt.end();)
		{
			if (it->second != 0 && (int)(dwNow - it->second) > 600000)
				s_mapPlayerBotMountGateWearAt.erase(it++);
			else
				++it;
		}
	}

	// The per-bot tick (beside the progression shop's): the census, and a counting mount in the bag put on in place of a
	// seal that does not count (or an empty slot), every PLAYERBOT_MOUNTGATE_WEAR_MS.
	void ManagePlayerBotMountGate(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		(void)state;
		TickPlayerBotMountGateCensus(dwNow);
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead() || !GetPlayerBotMountGateCfg().on ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return;
		DWORD& at = s_mapPlayerBotMountGateWearAt[ch->GetPlayerID()];
		if (at != 0 && (int)(dwNow - at) < 0)
			return;
		at = dwNow + PLAYERBOT_MOUNTGATE_WEAR_MS + ch->GetPlayerID() % 1000U;
		if (ch->IsBusy() || ch->GetMyShop() || ch->GetExchange() || !ch->CanHandleItem() || IsPlayerBotOnBattleHorseTrial(ch))
			return;
		bool worn = false;
		LPITEM mount = FindPlayerBotGateMount(ch, &worn);
		if (!mount || worn)
			return;
		LPITEM old = ch->GetWear(WEAR_COSTUME_MOUNT);
		const DWORD oldVnum = old ? old->GetVnum() : 0;
		// off the old seal's saddle first - the swap under a rider would leave it on an animal it no longer wears
		if (old && IsPlayerBotOnCostumeMount(ch))
			DismountPlayerBotCostume(ch);
		if (ch->EquipItem(mount) && ch->GetWear(WEAR_COSTUME_MOUNT) == mount)
		{
			++s_kPlayerBotMountGate.worn;
			ForgetPlayerBotGateMountCache(ch->GetPlayerID());
			PlayerBotLogThrottled("mountgate_worn", dwNow,
					"PLAYERBOT_MOUNTGATE: worn pid=%u name=%s lv=%d vnum=%u old=%u left_s=%ld", ch->GetPlayerID(), ch->GetName(),
					ch->GetLevel(), mount->GetVnum(), oldVnum, GetPlayerBotMountSecondsLeft(mount));
		}
		else
			++s_kPlayerBotMountGate.wearFailed;
#else
		(void)ch;
#endif
	}
}

#endif
