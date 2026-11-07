// MT2009_PLUS_BOT_SUNGMA_STALL_TRIP_V1 (the owner, 7 November 2026: "przeciez tak mialo byc - boty wracaja do M1,
// wystawiaja sklep i ida z powrotem na Dongan / inna mape expic"): the stall trip of a Sung Ma resident.
//
// What it mends. The counter's trips home (MT2009_PLUS_BOT_SUNGMA_TRIPS_V2: "bag", "goods", "shop", "routine") shared one
// cap with every other trip home of the core (PLAYERBOT_SUNGMA_TRADE_MAX, 6) - and the Dropki's sale trips, which write
// into the same table and are never taken off it by the Meley count, held it full: "trade trip waits ... away=68 max=6"
// on game3 on 7 November, m1_counter=3 in a census while 328 bags were full. And the ~40 % of the trips that did go came
// back with no counter at all ("trade trip back ... took_s=183 served=0 counter=0"): the bot landed on the ring of the
// first village, went hunting at once (the 120 s after a load are the counter's refusal anyway), and the three minutes'
// minimum stay sent it back before it ever stood at its pitch. So:
//   * a stall trip (the reasons "bag", "goods", "shop", "routine" of GetPlayerBotSungmaTradeReason) has a cap of its own,
//     m2_bot_sungma_stall_trip_max a core (default PLAYERBOT_SUNGMA_STALL_MAX_DEFAULT), counted from its own table; the
//     "buy", "meley" and Dropki trips keep PLAYERBOT_SUNGMA_TRADE_MAX as before;
//   * one stall trip a bot every m2_bot_sungma_stall_trip_gap_min minutes (default PLAYERBOT_SUNGMA_STALL_GAP_DEFAULT_MIN,
//     counted from its arrival on the map or its last trip home of any kind) - a bag under pressure (no free column of
//     three, or fewer than PLAYERBOT_SUNGMA_GOODS_FREE cells free, with nothing Dongan's merchants take and goods for a
//     counter) goes after PLAYERBOT_SUNGMA_TRADE_BAG_GAP_MS (30 min) instead;
//   * never from a fight, a retreat, a party on a stone or a boss, a dungeon run (StartPlayerBotSungmaTradeTrip's own
//     gate); a member of a plain hunting party leaves it cleanly, as every trip home does
//     (m2_bot_sungma_stall_trip_party_off 1: never out of any party);
//   * it lands on its own pitch of the first village (the stall's offset, 0x4d4b5450 - the one ManagePlayerBotPrivateShop
//     walks to), on the first channel (the Sung Ma maps are channel 1's; the counters are the shop channel's), and is
//     held there (HoldPlayerBotSungmaStallVisitor, the manager's tick after the stall pass) until its counter stands -
//     opened, or an old one found - for at most PLAYERBOT_SUNGMA_STALL_OPEN_MAX_MS, or until the stall pass refuses it
//     (nothing worth a stand, no yang for the fee, the pitch unreachable: "open_refused");
//   * then its town life as any bot's (the counter's service: stock, collect, renew - nudged at the arrival; potions,
//     the stands' browse), and the way back to its Sung Ma map once its counter was served or opened a minute ago -
//     at most PLAYERBOT_SUNGMA_STALL_HOME_MAX_MS at home (IsPlayerBotSungmaStallHomeDone);
//   * the merchant's sale of the goods (MT2009_PLUS_BOT_SUNGMA_BAG_GOODS_V1) is the fallback only: the stall trips off,
//     the handover off, no first village to go to, the bot's last stall trip failed (no counter after it, or lost - for
//     PLAYERBOT_SUNGMA_STALL_FAIL_HOLD_MS), never out of a party (the switch above) while in one, or a bag full for
//     PLAYERBOT_SUNGMA_STALL_FULL_WAIT_MS with no trip (the cap, a party's objective). m2_bot_sungma_goods_sale_always 1:
//     the sale as V1 had it (whenever the junk is not enough).
// Event flag m2_bot_sungma_stall_trip_off 1: all of it off - the trips home as MT2009_PLUS_BOT_SUNGMA_TRIPS_V2 had them
// (one shared cap, no hold), the merchant sale as V1.
// Log: PLAYERBOT_SUNGMA_STALL: trip start / trip waits / landed / failed / home / counter open / hold released / back /
// ends at home / fallback sale; and every 10 minutes "PLAYERBOT_SUNGMA_STALL: census" (side=trips on the Sung Ma core,
// side=home on the first villages' core).
//
// An implementation fragment: included by playerbot_yohara_sungma.h inside its namespace, after the counter's helpers
// (CountPlayerBotSungmaTradeGoods, HasPlayerBotSungmaCounter), before the trade trip's reason.

	const int PLAYERBOT_SUNGMA_STALL_GAP_DEFAULT_MIN = 150;
	const int PLAYERBOT_SUNGMA_STALL_MAX_DEFAULT = 24;
	const DWORD PLAYERBOT_SUNGMA_STALL_OPEN_MAX_MS = 9 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_HOME_MAX_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_FAIL_HOLD_MS = 3 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_FULL_WAIT_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_REFUSED_AFTER_MS = 125 * 1000;	// past the counter's 120 s after a load
	const DWORD PLAYERBOT_SUNGMA_STALL_REFUSED_SEEN_MS = 20 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_OPENED_SETTLE_MS = 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_STALL_PITCH_SALT = 0x4d4b5450U;	// the stall's own (ManagePlayerBotPrivateShop)

	enum
	{
		PLAYERBOT_SUNGMA_STALL_FAIL_NO_COUNTER,	// the Sung Ma core: back with no counter
		PLAYERBOT_SUNGMA_STALL_FAIL_LOST,	// the Sung Ma core: not back in PLAYERBOT_SUNGMA_TRADE_LOST_MS
		PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED,	// home: the stall pass refused the counter
		PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_TIMEOUT,	// home: no counter in PLAYERBOT_SUNGMA_STALL_OPEN_MAX_MS
		PLAYERBOT_SUNGMA_STALL_FAIL_LOGGED_OUT,	// home: gone (a rest, a channel move) before the way back
		PLAYERBOT_SUNGMA_STALL_FAIL_STRANDED,	// home: no way back (no room, not a champion, the handover off)
		PLAYERBOT_SUNGMA_STALL_FAIL_MAX
	};
	const char* const PLAYERBOT_SUNGMA_STALL_FAIL_NAMES[PLAYERBOT_SUNGMA_STALL_FAIL_MAX] = {
		"no_counter", "lost", "open_refused", "open_timeout", "logged_out", "stranded"
	};
	const char* const PLAYERBOT_SUNGMA_STALL_WHY[4] = { "bag", "goods", "shop", "routine" };

	struct TPlayerBotSungmaStallStats
	{
		// the Sung Ma core
		unsigned int started = 0, startedWhy[4] = {}, fullBefore = 0, waitsCap = 0, waitsParty = 0;
		unsigned int landed = 0, fullAfter = 0, landedCounter = 0;
		unsigned long long tripMs = 0;
		unsigned int saleSkipped = 0, fallbackSales = 0, fallbackPieces = 0;
		long long fallbackGold = 0;
		// the home core
		unsigned int arrived = 0, hadCounter = 0, opened = 0, served = 0, back = 0;
		int goodsListed = 0;
		long long yangCollected = 0;
		unsigned long long homeMs = 0;
		unsigned int failed[PLAYERBOT_SUNGMA_STALL_FAIL_MAX] = {};
	};
	TPlayerBotSungmaStallStats s_kPlayerBotSungmaStall;
	DWORD s_dwPlayerBotSungmaStallCensus = 0;

	struct TPlayerBotSungmaStallOut
	{
		DWORD dwAt = 0;
		bool bFull = false;
		int iGoods = 0;
		char szWhy[16] = {};
	};
	std::map<DWORD, TPlayerBotSungmaStallOut> s_mapPlayerBotSungmaStallOut;	// the Sung Ma core: out on a stall trip
	std::map<DWORD, DWORD> s_mapPlayerBotSungmaStallFailUntil;	// the Sung Ma core: the merchant fallback until
	std::map<DWORD, DWORD> s_mapPlayerBotSungmaBagFullSince;	// the Sung Ma core: no free column of three since

	struct TPlayerBotSungmaStallHome
	{
		DWORD dwSince = 0, dwOpenedAt = 0, dwRefusedSeen = 0;
		bool bHadCounter = false, bReleased = false, bOpenFailed = false, bReasonAsked = false;
		int iGoods = 0;
		long long llBoxYang = 0, llGold = 0;
		const char* pszRelease = "-";
	};
	std::map<DWORD, TPlayerBotSungmaStallHome> s_mapPlayerBotSungmaStallHome;	// the home core: stall visitors

	int GetPlayerBotSungmaStallFlag(const char* name)
	{
		return quest::CQuestManager::instance().GetEventFlag(name);
	}

	bool IsPlayerBotSungmaStallOn()
	{
		return GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_off") == 0 && GetPlayerBotYoharaConfig().sungmaTradeMax > 0;
	}

	DWORD GetPlayerBotSungmaStallGapMs()
	{
		int minutes = GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_gap_min");
		if (minutes <= 0)
			minutes = PLAYERBOT_SUNGMA_STALL_GAP_DEFAULT_MIN;
		minutes = std::max(30, std::min(1440, minutes));
		return (DWORD)minutes * 60000U;
	}

	int GetPlayerBotSungmaStallMax()
	{
		const int v = GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_max");
		return v <= 0 ? PLAYERBOT_SUNGMA_STALL_MAX_DEFAULT : std::min(v, 300);
	}

	int GetPlayerBotSungmaStallWhyIndex(const char* why)
	{
		for (int i = 0; why && i < 4; ++i)
			if (!strcmp(why, PLAYERBOT_SUNGMA_STALL_WHY[i]))
				return i;
		return -1;
	}

	long long GetPlayerBotSungmaStallBoxYang(DWORD pid)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		auto box = ikashop::GetManager().GetShopSafeboxByOwnerID(pid);
		return box ? (long long)box->GetValutes().yang : 0;
#else
		(void)pid;
		return 0;
#endif
	}

	// The goods of its bag a counter would take (-1: no state, the items not loaded).
	int CountPlayerBotSungmaStallGoods(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return -1;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return st == s_mapPlayerBotAIStates.end() ? -1 : CountPlayerBotSungmaTradeGoods(ch, st->second);
	}

	// ------------------------------------------------------------ the Sung Ma core

	// Its stall trips out and not back (lost after PLAYERBOT_SUNGMA_TRADE_LOST_MS: failed, the merchant's fallback a while).
	int CountPlayerBotSungmaStallAway(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotSungmaStallOut>::iterator i = s_mapPlayerBotSungmaStallOut.begin();
				i != s_mapPlayerBotSungmaStallOut.end();)
		{
			if (dwNow - i->second.dwAt >= PLAYERBOT_SUNGMA_TRADE_LOST_MS)
			{
				++s_kPlayerBotSungmaStall.failed[PLAYERBOT_SUNGMA_STALL_FAIL_LOST];
				s_mapPlayerBotSungmaStallFailUntil[i->first] = dwNow + PLAYERBOT_SUNGMA_STALL_FAIL_HOLD_MS;
				sys_log(0, "PLAYERBOT_SUNGMA_STALL: failed pid=%u why=lost trip_why=%s away_min=%u", i->first, i->second.szWhy,
						(dwNow - i->second.dwAt) / 60000U);
				s_mapPlayerBotSungmaStallOut.erase(i++);
				continue;
			}
			++i;
		}
		return (int)s_mapPlayerBotSungmaStallOut.size();
	}

	// The bag's clock (TidyPlayerBotSungmaBag): since when it has had no free column of three.
	void NotePlayerBotSungmaStallBag(LPCHARACTER ch, DWORD dwNow)
	{
		if (ch->GetEmptyInventory(3) >= 0)
			s_mapPlayerBotSungmaBagFullSince.erase(ch->GetPlayerID());
		else if (!s_mapPlayerBotSungmaBagFullSince.count(ch->GetPlayerID()))
			s_mapPlayerBotSungmaBagFullSince[ch->GetPlayerID()] = dwNow ? dwNow : 1;
	}

	// StartPlayerBotSungmaTradeTrip: may this stall trip go now (its own cap, the party switch). Logs the wait.
	bool AllowPlayerBotSungmaStallTrip(LPCHARACTER ch, const char* why, int goods, DWORD dwNow)
	{
		if (ch->GetParty() && GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_party_off") != 0)
		{
			++s_kPlayerBotSungmaStall.waitsParty;
			PlayerBotLogThrottled("sungma_stall_party", dwNow, "PLAYERBOT_SUNGMA_STALL: trip waits pid=%u name=%s why=%s wait=party goods=%d",
					ch->GetPlayerID(), ch->GetName(), why, goods);
			return false;
		}
		const int away = CountPlayerBotSungmaStallAway(dwNow);
		const int max = GetPlayerBotSungmaStallMax();
		if (away >= max)
		{
			++s_kPlayerBotSungmaStall.waitsCap;
			PlayerBotLogThrottled("sungma_stall_cap", dwNow, "PLAYERBOT_SUNGMA_STALL: trip waits pid=%u name=%s why=%s wait=cap away=%d max=%d goods=%d",
					ch->GetPlayerID(), ch->GetName(), why, away, max, goods);
			return false;
		}
		return true;
	}

	// StartPlayerBotSungmaTradeTrip: the handover asked for.
	void NotePlayerBotSungmaStallOut(LPCHARACTER ch, const char* why, int goods, long home, DWORD dwNow)
	{
		TPlayerBotSungmaStallOut& o = s_mapPlayerBotSungmaStallOut[ch->GetPlayerID()];
		o.dwAt = dwNow ? dwNow : 1;
		o.bFull = ch->GetEmptyInventory(3) < 0;
		o.iGoods = goods;
		strlcpy(o.szWhy, why, sizeof(o.szWhy));
		++s_kPlayerBotSungmaStall.started;
		const int w = GetPlayerBotSungmaStallWhyIndex(why);
		if (w >= 0)
			++s_kPlayerBotSungmaStall.startedWhy[w];
		if (o.bFull)
			++s_kPlayerBotSungmaStall.fullBefore;
		sys_log(0, "PLAYERBOT_SUNGMA_STALL: trip start pid=%u name=%s map=%ld home=%ld why=%s goods=%d free_cells=%d free3=%d "
				"counter=%d party=%u away=%d max=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), home, why, goods, CountPlayerBotFreeInventoryCells(ch),
				o.bFull ? 0 : 1, HasPlayerBotSungmaCounter(ch) ? 1 : 0,
				ch->GetParty() ? (unsigned int)ch->GetParty()->GetMemberCount() : 0,
				(int)s_mapPlayerBotSungmaStallOut.size(), GetPlayerBotSungmaStallMax());
	}

	// NotePlayerBotSungmaTradeLanded: back on its Sung Ma map. No counter after the trip: failed, and the merchant's
	// fallback for PLAYERBOT_SUNGMA_STALL_FAIL_HOLD_MS.
	void NotePlayerBotSungmaStallLanded(LPCHARACTER ch, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSungmaStallOut>::iterator o = s_mapPlayerBotSungmaStallOut.find(ch->GetPlayerID());
		if (o == s_mapPlayerBotSungmaStallOut.end())
			return;
		const DWORD took = dwNow - o->second.dwAt;
		const bool full = ch->IsItemLoaded() && ch->GetEmptyInventory(3) < 0;
		const bool counter = HasPlayerBotSungmaCounter(ch);
		TPlayerBotSungmaStallStats& s = s_kPlayerBotSungmaStall;
		++s.landed;
		s.tripMs += took;
		if (full)
			++s.fullAfter;
		if (counter)
		{
			++s.landedCounter;
			s_mapPlayerBotSungmaStallFailUntil.erase(ch->GetPlayerID());
		}
		else
		{
			++s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_NO_COUNTER];
			s_mapPlayerBotSungmaStallFailUntil[ch->GetPlayerID()] = dwNow + PLAYERBOT_SUNGMA_STALL_FAIL_HOLD_MS;
		}
		sys_log(0, "PLAYERBOT_SUNGMA_STALL: landed pid=%u name=%s map=%ld why=%s took_min=%u counter=%d goods=%d->%d free3=%d->%d%s",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), o->second.szWhy, took / 60000U, counter ? 1 : 0,
				o->second.iGoods, CountPlayerBotSungmaStallGoods(ch),
				o->second.bFull ? 0 : 1, full ? 0 : 1, counter ? "" : " failed=no_counter");
		s_mapPlayerBotSungmaStallOut.erase(o);
	}

	// SellPlayerBotSungmaBagGoods: NULL while the stall trips carry this bot's goods (no sale), else why the merchant's
	// sale is the fallback.
	const char* GetPlayerBotSungmaGoodsSaleFallback(LPCHARACTER ch, DWORD dwNow)
	{
		if (GetPlayerBotSungmaStallFlag("m2_bot_sungma_goods_sale_always") != 0)
			return "always";
		if (!IsPlayerBotSungmaStallOn())
			return "stall_off";
		if (!IsPlayerBotYoharaOn())
			return "handover_off";
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::iterator f = s_mapPlayerBotSungmaStallFailUntil.find(pid);
		if (f != s_mapPlayerBotSungmaStallFailUntil.end())
		{
			if ((int)(f->second - dwNow) > 0)
				return "trip_failed";
			s_mapPlayerBotSungmaStallFailUntil.erase(f);
		}
		if (ch->GetParty() && GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_party_off") != 0)
			return "party";
		long home = 0, x = 0, y = 0;
		if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, home, x, y) || IsPlayerBotMapHostedHere(home))
			return "no_home";
		std::map<DWORD, DWORD>::const_iterator full = s_mapPlayerBotSungmaBagFullSince.find(pid);
		if (full != s_mapPlayerBotSungmaBagFullSince.end() && dwNow - full->second >= PLAYERBOT_SUNGMA_STALL_FULL_WAIT_MS)
			return "full_wait";
		return NULL;
	}

	void NotePlayerBotSungmaStallSaleSkipped()
	{
		++s_kPlayerBotSungmaStall.saleSkipped;
	}

	void NotePlayerBotSungmaStallFallbackSale(int pieces, long long gold)
	{
		++s_kPlayerBotSungmaStall.fallbackSales;
		s_kPlayerBotSungmaStall.fallbackPieces += (unsigned int)std::max(0, pieces);
		s_kPlayerBotSungmaStall.fallbackGold += gold;
	}

	// ------------------------------------------------------------ the home core

	// StartPlayerBotSungmaTradeHome: a stall trip's bot in its first village.
	void StartPlayerBotSungmaStallHome(LPCHARACTER ch, const char* why, DWORD dwNow)
	{
		if (GetPlayerBotSungmaStallWhyIndex(why) < 0 || !IsPlayerBotSungmaStallOn())
			return;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotSungmaStallHome& h = s_mapPlayerBotSungmaStallHome[pid];
		h = TPlayerBotSungmaStallHome();
		h.dwSince = dwNow ? dwNow : 1;
		h.bHadCounter = HasPlayerBotSungmaCounter(ch);
		h.iGoods = CountPlayerBotSungmaStallGoods(ch);
		h.llBoxYang = GetPlayerBotSungmaStallBoxYang(pid);
		h.llGold = (long long)ch->GetGold();
		++s_kPlayerBotSungmaStall.arrived;
		if (h.bHadCounter)
			++s_kPlayerBotSungmaStall.hadCounter;
		sys_log(0, "PLAYERBOT_SUNGMA_STALL: home pid=%u name=%s map=%ld channel=%u pos=(%ld,%ld) why=%s counter=%d goods=%d box_yang=%lld gold=%lld",
				pid, ch->GetName(), ch->GetMapIndex(), (unsigned int)g_bChannel, ch->GetX(), ch->GetY(), why, h.bHadCounter ? 1 : 0,
				h.iGoods, h.llBoxYang, h.llGold);
	}

	void ReleasePlayerBotSungmaStallHold(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotSungmaStallHome& h, const char* why,
			int fail, DWORD dwNow)
	{
		h.bReleased = true;
		h.pszRelease = why;
		if (fail >= 0)
		{
			h.bOpenFailed = true;
			++s_kPlayerBotSungmaStall.failed[fail];
		}
		PlayerBotLogThrottled("sungma_stall_release", dwNow, "PLAYERBOT_SUNGMA_STALL: hold released pid=%u name=%s why=%s after_s=%u "
				"next_keep_s=%d gold=%lld goods=%d",
				ch->GetPlayerID(), ch->GetName(), why, (dwNow - h.dwSince) / 1000,
				(int)(state.dwNextShopKeepTime - dwNow) / 1000, (long long)ch->GetGold(), CountPlayerBotSungmaStallGoods(ch));
	}

	// The manager's tick, after the stall pass (ManagePlayerBotPrivateShop): a stall visitor whose counter does not stand
	// yet is held at its pitch - walked back to the ring, else standing - so the stall pass opens it there (its
	// "already at the pitch"), rather than riding off to hunt. True: the tick is the hold's.
	bool HoldPlayerBotSungmaStallVisitor(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (s_mapPlayerBotSungmaStallHome.empty() || !ch)
			return false;
		std::map<DWORD, TPlayerBotSungmaStallHome>::iterator it = s_mapPlayerBotSungmaStallHome.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSungmaStallHome.end() || it->second.bReleased || !ch->IsItemLoaded())
			return false;
		TPlayerBotSungmaStallHome& h = it->second;
		const DWORD el = dwNow - h.dwSince;
		if (HasPlayerBotSungmaCounter(ch))
		{
			if (!h.dwOpenedAt)
			{
				h.dwOpenedAt = dwNow ? dwNow : 1;
				if (!h.bHadCounter)
					++s_kPlayerBotSungmaStall.opened;
				sys_log(0, "PLAYERBOT_SUNGMA_STALL: counter open pid=%u name=%s map=%ld after_s=%u new=%d", ch->GetPlayerID(), ch->GetName(),
						ch->GetMapIndex(), el / 1000, h.bHadCounter ? 0 : 1);
			}
			h.bReleased = true;
			h.pszRelease = "counter";
			return false;
		}
		if (GetPlayerBotSungmaStallFlag("m2_bot_sungma_stall_trip_off") != 0)
		{
			h.bReleased = true;
			h.pszRelease = "off";
			return false;
		}
		if (el >= PLAYERBOT_SUNGMA_STALL_OPEN_MAX_MS)
		{
			ReleasePlayerBotSungmaStallHold(ch, state, h, "open_timeout", PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_TIMEOUT, dwNow);
			return false;
		}
		if (ch->IsDead() || state.bRecoveringAfterDeath || state.bTacticalRetreat || ch->GetVictim() != NULL ||
				state.bVisitingShop || state.bMarketTrip || state.offlineShop.visiting)
			return false;
		// the stall pass's refusal: its clock set far ahead with no counter on the way (a create sent sets it too, but
		// its request stays open until the answer)
		const bool pending = playerbot_offline::requests.count(ch->GetPlayerID()) != 0;
		// no reason for a counter at all (the stall pass asks it without a word): asked once, past the 120 s
		if (!pending && !h.bReasonAsked && el >= PLAYERBOT_SUNGMA_STALL_REFUSED_AFTER_MS)
		{
			h.bReasonAsked = true;
			if (GetPlayerBotShopReason(ch, state) == PLAYERBOT_SHOP_REASON_NONE)
			{
				ReleasePlayerBotSungmaStallHold(ch, state, h, "no_reason", PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED, dwNow);
				return false;
			}
		}
		if (!pending && el >= PLAYERBOT_SUNGMA_STALL_REFUSED_AFTER_MS && state.dwNextShopKeepTime != 0 &&
				(int)(state.dwNextShopKeepTime - dwNow) > 30000)
		{
			if (!h.dwRefusedSeen)
				h.dwRefusedSeen = dwNow ? dwNow : 1;
			else if (dwNow - h.dwRefusedSeen >= PLAYERBOT_SUNGMA_STALL_REFUSED_SEEN_MS)
			{
				ReleasePlayerBotSungmaStallHold(ch, state, h, "open_refused", PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED, dwNow);
				return false;
			}
		}
		else
			h.dwRefusedSeen = 0;
		long px = 0, py = 0;
		if (!GetPlayerBotShopCentre(ch->GetMapIndex(), px, py) || !IsPlayerBotShopMapAllowed(ch->GetMapIndex()))
		{
			ReleasePlayerBotSungmaStallHold(ch, state, h, "no_pitch", PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED, dwNow);
			return false;
		}
		if (DISTANCE_APPROX(ch->GetX() - px, ch->GetY() - py) > PLAYERBOT_SHOP_RING_RADIUS + PLAYERBOT_MARKET_ARRIVE - 100)
		{
			long ox = 0, oy = 0;
			GetPlayerBotStableOffset(ch->GetPlayerID(), PLAYERBOT_SUNGMA_STALL_PITCH_SALT, PLAYERBOT_SHOP_RING_MIN,
					PLAYERBOT_SHOP_RING_RADIUS, ox, oy);
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBotTownLeg(ch, state, dwNow, px + ox, py + oy, PLAYERBOT_MARKET_ARRIVE);
			return true;
		}
		SetPlayerBotAction(state, BOT_ACTION_TOWN_REST, dwNow);
		return true;
#else
		(void)ch; (void)state; (void)dwNow;
		return false;
#endif
	}

	// IsPlayerBotSungmaTradeHomeDone for a stall visitor: -1 not one (the trade trip's own test), 0 not yet, 1 done.
	int IsPlayerBotSungmaStallHomeDone(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSungmaStallHome>::const_iterator it = s_mapPlayerBotSungmaStallHome.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSungmaStallHome.end())
			return -1;
		const TPlayerBotSungmaStallHome& h = it->second;
		const DWORD el = dwNow - h.dwSince;
		if (el >= PLAYERBOT_SUNGMA_STALL_HOME_MAX_MS)
			return 1;
		if (el < PLAYERBOT_SUNGMA_TRADE_HOME_MIN_MS || state.bVisitingShop || state.bMarketTrip)
			return 0;
		if (IsPlayerBotGear2ErrandBusy(ch->GetPlayerID()) || WantsPlayerBotGear2TradeTrip(ch))
			return 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		const playerbot_offline::State& o = state.offlineShop;
		if (o.visiting || o.buyOwner || playerbot_offline::requests.count(ch->GetPlayerID()))
			return 0;
		if (!HasPlayerBotSungmaCounter(ch))
			return h.bReleased ? 1 : 0;	// the hold gave it up (refused, timed out): home with what it has
		const bool served = o.lastServedAt != 0 && (int)(o.lastServedAt - h.dwSince) >= 0;
		const bool settled = h.dwOpenedAt != 0 && !h.bHadCounter && dwNow - h.dwOpenedAt >= PLAYERBOT_SUNGMA_STALL_OPENED_SETTLE_MS;
		return served || settled ? 1 : 0;
#else
		return h.bReleased ? 1 : 0;
#endif
	}

	// ManagePlayerBotSungmaTradeHomes: the visit's end (fail < 0: the way back taken).
	void EndPlayerBotSungmaStallHome(DWORD pid, LPCHARACTER ch, int fail, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSungmaStallHome>::iterator it = s_mapPlayerBotSungmaStallHome.find(pid);
		if (it == s_mapPlayerBotSungmaStallHome.end())
			return;
		const TPlayerBotSungmaStallHome& h = it->second;
		TPlayerBotSungmaStallStats& s = s_kPlayerBotSungmaStall;
		const DWORD el = dwNow - h.dwSince;
		if (fail >= 0)
		{
			++s.failed[fail];
			sys_log(0, "PLAYERBOT_SUNGMA_STALL: ends at home pid=%u name=%s why=%s after_s=%u", pid, ch ? ch->GetName() : "-",
					PLAYERBOT_SUNGMA_STALL_FAIL_NAMES[fail], el / 1000);
			s_mapPlayerBotSungmaStallHome.erase(it);
			return;
		}
		int served = 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(pid);
		if (ch && st != s_mapPlayerBotAIStates.end())
		{
			const playerbot_offline::State& o = st->second.offlineShop;
			served = o.lastServedAt != 0 && (int)(o.lastServedAt - h.dwSince) >= 0 ? 1 : 0;
		}
#endif
		const bool counter = ch && HasPlayerBotSungmaCounter(ch);
		const int goods = CountPlayerBotSungmaStallGoods(ch);
		const int listed = h.iGoods >= 0 && goods >= 0 && counter ? std::max(0, h.iGoods - goods) : 0;
		const long long box = GetPlayerBotSungmaStallBoxYang(pid);
		const long long collected = std::max(0LL, h.llBoxYang - box);
		++s.back;
		s.homeMs += el;
		s.served += (unsigned int)served;
		s.goodsListed += listed;
		s.yangCollected += collected;
		sys_log(0, "PLAYERBOT_SUNGMA_STALL: back pid=%u name=%s took_s=%u counter=%d had_counter=%d opened=%d served=%d hold=%s "
				"goods=%d->%d listed=%d box_yang=%lld->%lld collected=%lld gold=%lld->%lld",
				pid, ch ? ch->GetName() : "-", el / 1000, counter ? 1 : 0, h.bHadCounter ? 1 : 0,
				h.dwOpenedAt && !h.bHadCounter ? 1 : 0, served, h.pszRelease, h.iGoods, goods, listed, h.llBoxYang, box, collected,
				h.llGold, ch ? (long long)ch->GetGold() : 0LL);
		s_mapPlayerBotSungmaStallHome.erase(it);
	}

	// ------------------------------------------------------------ the census, every 10 minutes on every core with any of it

	void PrintPlayerBotSungmaStallCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotSungmaStallCensus == 0)
		{
			s_dwPlayerBotSungmaStallCensus = dwNow ? dwNow : 1;
			return;
		}
		if (dwNow - s_dwPlayerBotSungmaStallCensus < PLAYERBOT_SUNGMA_STALL_CENSUS_MS)
			return;
		s_dwPlayerBotSungmaStallCensus = dwNow ? dwNow : 1;
		TPlayerBotSungmaStallStats& s = s_kPlayerBotSungmaStall;
		const int away = CountPlayerBotSungmaStallAway(dwNow);
		const bool trips = s.started || s.landed || s.waitsCap || s.waitsParty || s.saleSkipped || s.fallbackSales || away ||
				s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_NO_COUNTER] || s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_LOST];
		const bool home = s.arrived || s.back || !s_mapPlayerBotSungmaStallHome.empty() ||
				s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED] || s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_TIMEOUT] ||
				s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_LOGGED_OUT] || s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_STRANDED];
		if (trips)
		{
			unsigned int full = 0;
			for (std::map<DWORD, DWORD>::const_iterator f = s_mapPlayerBotSungmaBagFullSince.begin();
					f != s_mapPlayerBotSungmaBagFullSince.end(); ++f)
				full += CHARACTER_MANAGER::instance().FindByPID(f->first) ? 1 : 0;
			sys_log(0, "PLAYERBOT_SUNGMA_STALL: census channel=%u side=trips on=%d started=%u why_bag=%u why_goods=%u why_shop=%u "
					"why_routine=%u full_before=%u waits_cap=%u waits_party=%u away=%d max=%d gap_min=%u landed=%u landed_counter=%u "
					"full_after=%u avg_trip_min=%.1f failed_no_counter=%u failed_lost=%u bags_full_now=%u sale_skipped=%u "
					"fallback_sales=%u fallback_pieces=%u fallback_gold=%lld",
					(unsigned int)g_bChannel, IsPlayerBotSungmaStallOn() ? 1 : 0, s.started, s.startedWhy[0], s.startedWhy[1],
					s.startedWhy[2], s.startedWhy[3], s.fullBefore, s.waitsCap, s.waitsParty, away, GetPlayerBotSungmaStallMax(),
					GetPlayerBotSungmaStallGapMs() / 60000U, s.landed, s.landedCounter, s.fullAfter,
					s.landed ? (double)s.tripMs / (double)s.landed / 60000.0 : 0.0,
					s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_NO_COUNTER], s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_LOST], full, s.saleSkipped,
					s.fallbackSales, s.fallbackPieces, s.fallbackGold);
		}
		if (home)
			sys_log(0, "PLAYERBOT_SUNGMA_STALL: census channel=%u side=home on=%d arrived=%u had_counter=%u opened=%u served=%u "
					"finished=%u avg_home_min=%.1f goods_listed=%d yang_collected=%lld failed_open_refused=%u failed_open_timeout=%u "
					"failed_logged_out=%u failed_stranded=%u at_home=%u",
					(unsigned int)g_bChannel, IsPlayerBotSungmaStallOn() ? 1 : 0, s.arrived, s.hadCounter, s.opened, s.served, s.back,
					s.back ? (double)s.homeMs / (double)s.back / 60000.0 : 0.0, s.goodsListed, s.yangCollected,
					s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_REFUSED], s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_OPEN_TIMEOUT],
					s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_LOGGED_OUT], s.failed[PLAYERBOT_SUNGMA_STALL_FAIL_STRANDED],
					(unsigned int)s_mapPlayerBotSungmaStallHome.size());
		s = TPlayerBotSungmaStallStats();
		// the fallback's and the bag's clocks of bots gone from this core
		for (std::map<DWORD, DWORD>::iterator f = s_mapPlayerBotSungmaBagFullSince.begin(); f != s_mapPlayerBotSungmaBagFullSince.end();)
			if (!CHARACTER_MANAGER::instance().FindByPID(f->first))
				s_mapPlayerBotSungmaBagFullSince.erase(f++);
			else
				++f;
		for (std::map<DWORD, DWORD>::iterator f = s_mapPlayerBotSungmaStallFailUntil.begin(); f != s_mapPlayerBotSungmaStallFailUntil.end();)
			if ((int)(f->second - dwNow) <= 0)
				s_mapPlayerBotSungmaStallFailUntil.erase(f++);
			else
				++f;
	}
