#ifndef __INC_METIN2_PLAYERBOT_ERRANDS_H__
#define __INC_METIN2_PLAYERBOT_ERRANDS_H__

// MT2009_PLUS_BOT_ERRAND_BATCH_V1 / MT2009_PLUS_BOT_WEAPON_ERRAND_V1 / MT2009_PLUS_BOT_SM_HP70_V1 (the owner's decisions of
// 6 November 2026 evening, the second pass of the bot analysis, points 5, 6 and 7 -
// cache/yohara/drugie-podejscie-2026-11-06-brief.md).
//
// 7. Errand batching ("przenosiny dopiero przy >=2 sprawach albo po 60 min; bot na kanale 1 zalatwia wszystko naraz").
//    The stands are the shop channel's alone, so every bot of channel 2+ with one thing to buy asked to be moved there
//    and was sent back soon after - ~400 moves an hour a core at 485 bots, each one losing the bot's target, route and
//    party. Now a bot off the shop channel notes its errands by kind (PassPlayerBotShopErrand: a weapon, an armour, a
//    book, materials, a Kupon SM, a potion, its own stand, anything else - the kind of the line it picked) and asks
//    to be moved only when PLAYERBOT_ERRAND_BATCH_MIN (2) kinds are open, or the oldest open one has waited
//    PLAYERBOT_ERRAND_BATCH_WAIT_MIN (60) minutes, or one is a potion (at once). A kind not noted again within
//    PLAYERBOT_ERRAND_TTL_MS is gone. Once let through, the bot keeps asking (the request must stand) until the move.
//    On the shop channel a bot that arrived there (first seen PLAYERBOT_ERRAND_WARMUP_MS after this core started) is
//    pinned against the coordinator's drain and swaps while its errands run - its first PLAYERBOT_ERRAND_ARRIVAL_PIN_MS,
//    and after that while it shops (a pick, a market or progression trip, a stand visit within
//    PLAYERBOT_ERRAND_ACTIVITY_MS), at most PLAYERBOT_ERRAND_PIN_MAX_MS; for its first hour it costs the coordinator
//    more to move ("busy"), so it does not go back the same hour. And it starts its progression trip at once rather
//    than after the first trip's 1-30 minutes of a fresh core's state, past the trips' cap.
// 5. Weapon errand: a bot whose look at its first village's stands (LookPlayerBotWeaponUpgrade, playerbot_gear_upgrade.h)
//    found a better weapon it can pay for, and which is off the shop channel and free (no party, no dungeon, no fight),
//    notes a "weapon" errand (point 7 decides when it is moved); on the shop channel the progression trip takes it to
//    the first village (playerbot_progression_needs.h). The weapon census says why the wanting bots did not buy
//    (ReportPlayerBotWeaponUpgrades: map, channel, pay, bag, claimed, nav, gone, not_tried, offline).
// 6. HP of the bots of 70+: their max HP sampled here (every PLAYERBOT_HP70_SAMPLE_MS) by bands of five levels; a bot
//    under its band's median (IsPlayerBotUnderHpMedian) - the ItemShop's bonus_add / bonus_change for an armour,
//    shield or necklace with no HP or defence line counts as urgent inside the current week's pool
//    (IsPlayerBotSmPoolUrgent, playerbot_ishop3_goals.h). The weekly grant itself is unchanged. And an exp-locked bot
//    (IsPlayerBotExpLocked - it does not need Smocze Monety now) with a counter lists its Kupon SM there instead of
//    cashing them (IsPlayerBotLockedCouponSeller; playerbot_itemshop.h), so the bots short of coins find some.
//
// Switches (event flags, read once a second): m2_bot_errand_batch_off 1 - every bot asks at once as before, no pin;
// m2_bot_weapon_errand_off 1 - no weapon errand; m2_bot_sm_hp70_off 1 - no HP urgency; m2_bot_locked_coupons_off 1 -
// exp-locked bots cash their coupons as before. Env: PLAYERBOT_ERRAND_BATCH_MIN
// (2), PLAYERBOT_ERRAND_BATCH_WAIT_MIN (60), PLAYERBOT_SM_HP70_MIN_LEVEL (70).
// The log: PLAYERBOT_ERRAND: held / released / weapon errand / arrival trip (throttled), census every ten minutes;
// PLAYERBOT_ISHOP3: hp70 urgent (throttled, playerbot_ishop3_goals.h).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_gear_upgrade.h, in the anonymous
// namespace.

#if defined(PLAYERBOT_ENGINE_MT2009)

namespace
{
	enum EPlayerBotErrandKind
	{
		PLAYERBOT_ERRAND_POTION = 0,
		PLAYERBOT_ERRAND_WEAPON,
		PLAYERBOT_ERRAND_ARMOUR,
		PLAYERBOT_ERRAND_BOOK,
		PLAYERBOT_ERRAND_MATERIAL,
		PLAYERBOT_ERRAND_COUPON,
		PLAYERBOT_ERRAND_STAND,
		PLAYERBOT_ERRAND_OTHER,
		PLAYERBOT_ERRAND_KINDS
	};

	const char* const PLAYERBOT_ERRAND_NAMES[PLAYERBOT_ERRAND_KINDS] = {
		"potion", "weapon", "armour", "book", "material", "coupon", "stand", "other" };

	const DWORD PLAYERBOT_ERRAND_TTL_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_RELEASE_HOLD_MS = 20 * 60 * 1000;	// a let-through bot keeps asking this long
	const DWORD PLAYERBOT_ERRAND_WARMUP_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_ARRIVAL_PIN_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_ACTIVITY_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_PIN_MAX_MS = 45 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_STAY_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_TICK_MS = 30 * 1000;
	const DWORD PLAYERBOT_ERRAND_WEAPON_ASK_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_ERRAND_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_HP70_SAMPLE_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_HP70_SAMPLE_TTL_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_HP70_MEDIAN_MS = 10 * 60 * 1000;
	const int PLAYERBOT_HP70_BAND_LEVELS = 5;
	const int PLAYERBOT_HP70_MIN_SAMPLES = 5;
	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2: from 50 (was 60) - the Wukong gate reads the bands of 50-59 too; the HP
	// urgency still starts at PLAYERBOT_SM_HP70_MIN_LEVEL (70).
	const int PLAYERBOT_HP70_SAMPLE_FROM_LEVEL = 50;

	int ReadPlayerBotYoharaEnvInt(const char* name, int def, int lo, int hi);	// playerbot_yohara_bots.h

	// The switches: 0 batching, 1 weapon errand, 2 HP urgency, 3 an exp-locked bot's coupons on its counter.
	bool IsPlayerBotErrandSwitchOn(int which)
	{
		static const char* const s_flags[4] = { "m2_bot_errand_batch_off", "m2_bot_weapon_errand_off", "m2_bot_sm_hp70_off",
				"m2_bot_locked_coupons_off" };
		static DWORD s_dwAt = 0;
		static bool s_bOn[4] = { true, true, true, true };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			for (int i = 0; i < 4; ++i)
				s_bOn[i] = quest::CQuestManager::instance().GetEventFlag(s_flags[i]) == 0;
		}
		return which >= 0 && which < 4 && s_bOn[which];
	}

	int GetPlayerBotErrandBatchMin()
	{
		static int s_i = -1;
		if (s_i < 0)
			s_i = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ERRAND_BATCH_MIN", 2, 1, PLAYERBOT_ERRAND_KINDS);
		return s_i;
	}

	DWORD GetPlayerBotErrandBatchWaitMs()
	{
		static int s_i = -1;
		if (s_i < 0)
			s_i = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ERRAND_BATCH_WAIT_MIN", 60, 1, 24 * 60);
		return (DWORD)s_i * 60U * 1000U;
	}

	struct TPlayerBotErrandBot
	{
		DWORD first[PLAYERBOT_ERRAND_KINDS];
		DWORD last[PLAYERBOT_ERRAND_KINDS];
		DWORD dwReleasedAt;	// let through: keeps asking until the move
		DWORD dwNextTick;
		DWORD dwArrivedAt;	// the shop channel: first seen here after the warm-up (0: not an arrival)
		DWORD dwLastActivity;	// the shop channel: the last shopping seen
		DWORD dwNextWeaponAsk;
		DWORD dwPresenceSeen;	// MT2009_PLUS_BOT_ERRAND_PRESENCE_V1: the channel census saw it in the game on this core
		DWORD dwFirstPresence;	// MT2009_PLUS_BOT_ERRAND_PRESENCE_V1: ... for the first time
		bool bSeen;
		bool bTripStarted;

		TPlayerBotErrandBot() : dwReleasedAt(0), dwNextTick(0), dwArrivedAt(0), dwLastActivity(0), dwNextWeaponAsk(0),
				dwPresenceSeen(0), dwFirstPresence(0), bSeen(false), bTripStarted(false)
		{
			for (int i = 0; i < PLAYERBOT_ERRAND_KINDS; ++i)
				first[i] = last[i] = 0;
		}
	};
	std::map<DWORD, TPlayerBotErrandBot> s_mapPlayerBotErrands;

	struct TPlayerBotErrandStats
	{
		unsigned int held, releasedBatch, releasedWait, releasedUrgent, releasedAgain, weaponErrands, arrivals,
				arrivalTrips, pinned, stayBusy;
		unsigned int noted[PLAYERBOT_ERRAND_KINDS];
		TPlayerBotErrandStats()
		{
			memset(this, 0, sizeof(*this));
		}
	};
	TPlayerBotErrandStats s_kPlayerBotErrandStats;
	DWORD s_dwPlayerBotErrandCoreStart = 0;
	DWORD s_dwPlayerBotErrandNextCensus = 0;

	int ClassifyPlayerBotErrandTable(const TItemTable* table)
	{
		if (!table)
			return PLAYERBOT_ERRAND_OTHER;
		if (IsPlayerBotSmCouponVnum(table->dwVnum))
			return PLAYERBOT_ERRAND_COUPON;
		switch (table->bType)
		{
			case ITEM_WEAPON:
				return PLAYERBOT_ERRAND_WEAPON;
			case ITEM_ARMOR:
				return PLAYERBOT_ERRAND_ARMOUR;
			case ITEM_SKILLBOOK:
				return PLAYERBOT_ERRAND_BOOK;
			case ITEM_MATERIAL:
			case ITEM_METIN:
				return PLAYERBOT_ERRAND_MATERIAL;
			case ITEM_USE:
				if (table->bSubType == USE_POTION || table->bSubType == USE_POTION_NODELAY ||
						table->bSubType == USE_POTION_CONTINUE)
					return PLAYERBOT_ERRAND_POTION;
				return PLAYERBOT_ERRAND_OTHER;
			default:
				return PLAYERBOT_ERRAND_OTHER;
		}
	}

#if defined(ENABLE_IKASHOP_RENEWAL)
	// The kind of a stand's line (a pick, a far pick, a haggled deal).
	int ClassifyPlayerBotErrandLine(DWORD ownerPid, DWORD itemId)
	{
		if (!ownerPid || !itemId)
			return PLAYERBOT_ERRAND_OTHER;
		auto shop = ikashop::GetManager().GetShopByOwnerID(ownerPid);
		auto line = shop ? shop->GetItem(itemId) : nullptr;
		return ClassifyPlayerBotErrandTable(line ? line->GetTable() : NULL);
	}
#endif

	bool IsPlayerBotErrandBatchActive()
	{
		return CPlayerBotManager::instance().IsChannelTableMode() &&
				g_bChannel != playerbot_channel_rules::SHOP_CHANNEL && IsPlayerBotErrandSwitchOn(0);
	}

	// Notes the errand and says whether the bot may ask for the shop channel now (point 7, the header).
	bool PassPlayerBotShopErrand(LPCHARACTER ch, int kind, DWORD now)
	{
		if (!ch || !IsPlayerBotErrandBatchActive())
			return true;
		if (kind < 0 || kind >= PLAYERBOT_ERRAND_KINDS)
			kind = PLAYERBOT_ERRAND_OTHER;
		if (!now)
			now = 1;
		TPlayerBotErrandBot& b = s_mapPlayerBotErrands[ch->GetPlayerID()];
		if (b.first[kind] == 0 || now - b.last[kind] >= PLAYERBOT_ERRAND_TTL_MS)
		{
			b.first[kind] = now;
			++s_kPlayerBotErrandStats.noted[kind];
		}
		b.last[kind] = now;
		int open = 0;
		DWORD oldest = 0;
		std::string kinds;
		for (int i = 0; i < PLAYERBOT_ERRAND_KINDS; ++i)
		{
			if (b.first[i] == 0 || now - b.last[i] >= PLAYERBOT_ERRAND_TTL_MS)
				continue;
			++open;
			oldest = std::max<DWORD>(oldest, now - b.first[i]);
			if (!kinds.empty())
				kinds += ",";
			kinds += PLAYERBOT_ERRAND_NAMES[i];
		}
		if (b.dwReleasedAt != 0 && now - b.dwReleasedAt < PLAYERBOT_ERRAND_RELEASE_HOLD_MS)
		{
			++s_kPlayerBotErrandStats.releasedAgain;
			return true;
		}
		// MT2009_PLUS_BOT_STAND_ERRAND_NOW_V1 (the owner, 7 November 2026: "niech boty z ch2 zmieniaja channel na ch1 i
		// tam wystawiaja sklepy - przeciez tak bylo to zaprojektowane"): its own stand moves a bot at once, as a potion
		// (the batch held ~950 bots of channel 2 with their stand alone, ~20 let through in 10 minutes; their goods never
		// reached a counter). The stand's own pass already waits its 45-75 minutes between services. Event flag
		// m2_bot_stand_errand_batch 1: the stand waits in the batch again.
		const bool standNow = kind == PLAYERBOT_ERRAND_STAND &&
				quest::CQuestManager::instance().GetEventFlag("m2_bot_stand_errand_batch") != 1;
		const char* why = kind == PLAYERBOT_ERRAND_POTION ? "urgent" : standNow ? "stand" :
				open >= GetPlayerBotErrandBatchMin() ? "batch" :
				oldest >= GetPlayerBotErrandBatchWaitMs() ? "wait" : NULL;
		if (!why)
		{
			++s_kPlayerBotErrandStats.held;
			PlayerBotLogThrottled("errand_held", now,
					"PLAYERBOT_ERRAND: held pid=%u name=%s channel=%u kinds=%s open=%d oldest_min=%u",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)g_bChannel, kinds.c_str(), open,
					(unsigned int)(oldest / 60000U));
			return false;
		}
		b.dwReleasedAt = now;
		if (why[0] == 'u' || why[0] == 's')
			++s_kPlayerBotErrandStats.releasedUrgent;
		else if (why[0] == 'b')
			++s_kPlayerBotErrandStats.releasedBatch;
		else
			++s_kPlayerBotErrandStats.releasedWait;
		PlayerBotLogThrottled("errand_released", now,
				"PLAYERBOT_ERRAND: released pid=%u name=%s channel=%u why=%s kinds=%s open=%d oldest_min=%u",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)g_bChannel, why, kinds.c_str(), open,
				(unsigned int)(oldest / 60000U));
		return true;
	}

	// The batched request (RequestShopChannel when the errands let the bot through).
	bool RequestPlayerBotShopErrand(LPCHARACTER ch, int kind, DWORD now)
	{
		if (!ch || !PassPlayerBotShopErrand(ch, kind, now))
			return false;
		return CPlayerBotManager::instance().RequestShopChannel(ch->GetPlayerID());
	}

	// The shop channel's side: pinned while its errands run (PublishChannelPresence), and busy for its first hour.
	unsigned int s_uPlayerBotErrandResightKept = 0;

	// MT2009_PLUS_BOT_ERRAND_PRESENCE_V1: the channel census's sighting (PublishChannelPresence).
	// A bot the census sees before its AI pass ever asked for its errands is entered here, so a first errand pass
	// after the warm-up does not make an "arrival" of a bot that was in the game on this core before it.
	void NotePlayerBotErrandPresence(DWORD pid, DWORD now)
	{
		if (!now)
			now = 1;
		if (s_dwPlayerBotErrandCoreStart == 0)
			s_dwPlayerBotErrandCoreStart = now;
		TPlayerBotErrandBot& b = s_mapPlayerBotErrands[pid];
		// first seen, or back after a while away from this core (moved off and back): a new first sighting
		if (b.dwFirstPresence == 0 || (b.dwPresenceSeen != 0 && (int)(now - b.dwPresenceSeen) > (int)(10 * PLAYERBOT_ERRAND_TICK_MS)))
			b.dwFirstPresence = now;
		b.dwPresenceSeen = now;
	}

	bool IsPlayerBotErrandArrivalPinned(DWORD pid, DWORD now, bool& stayBusy)
	{
		stayBusy = false;
		if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL || !IsPlayerBotErrandSwitchOn(0))
			return false;
		std::map<DWORD, TPlayerBotErrandBot>::const_iterator it = s_mapPlayerBotErrands.find(pid);
		if (it == s_mapPlayerBotErrands.end() || it->second.dwArrivedAt == 0)
			return false;
		const TPlayerBotErrandBot& b = it->second;
		const DWORD since = now - b.dwArrivedAt;
		if (since >= PLAYERBOT_ERRAND_STAY_MS)
			return false;
		stayBusy = true;
		const bool pinned = since < PLAYERBOT_ERRAND_PIN_MAX_MS &&
				(since < PLAYERBOT_ERRAND_ARRIVAL_PIN_MS ||
				 (b.dwLastActivity != 0 && now - b.dwLastActivity < PLAYERBOT_ERRAND_ACTIVITY_MS));
		if (pinned)
			++s_kPlayerBotErrandStats.pinned;
		else
			++s_kPlayerBotErrandStats.stayBusy;
		return pinned;
	}

	bool IsPlayerBotErrandArrival(DWORD pid, DWORD now)
	{
		std::map<DWORD, TPlayerBotErrandBot>::const_iterator it = s_mapPlayerBotErrands.find(pid);
		return it != s_mapPlayerBotErrands.end() && it->second.dwArrivedAt != 0 &&
				now - it->second.dwArrivedAt < PLAYERBOT_ERRAND_PIN_MAX_MS;
	}

	// ---------------------------------------------------------------- 6. the HP bands

	struct TPlayerBotHpSample
	{
		int band;
		long long hp;
		long long atk;	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2: GetPlayerBotRealAttack
		DWORD when;
	};
	std::map<DWORD, TPlayerBotHpSample> s_mapPlayerBotHpSamples;
	std::map<int, long long> s_mapPlayerBotHpMedian;
	std::map<int, long long> s_mapPlayerBotAtkMedian;	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2

	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2: the blow the bot really strikes with - the weapon in its hand read by the
	// damage model (GetPlayerBotWeaponHitDamage: its grade, roll, plus, average and skill damage, crit, penetration, a
	// young heroes' "Wartosc ataku"), so a level-30 weapon with a good average-damage line counts for what it does,
	// not for its level. A bot with a young heroes' weapon in the hand is read with that weapon (the hand worn), not
	// the planned one GetPlayerBotHandWeapon gives. No weapon: 0.
	long long GetPlayerBotRealAttack(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return 0;
		LPITEM hand = ch->GetWear(WEAR_WEAPON);
		if (!hand || hand->GetType() != ITEM_WEAPON)
			hand = GetPlayerBotHandWeapon(ch);
		return hand ? GetPlayerBotWeaponHitDamage(hand, ch) : 0;
	}
	DWORD s_dwPlayerBotHpMedianAt = 0;

	int GetPlayerBotHpBand(int level)
	{
		return level / PLAYERBOT_HP70_BAND_LEVELS;
	}

	void RefreshPlayerBotHpMedians(DWORD now)
	{
		if (s_dwPlayerBotHpMedianAt != 0 && now - s_dwPlayerBotHpMedianAt < PLAYERBOT_HP70_MEDIAN_MS)
			return;
		s_dwPlayerBotHpMedianAt = now ? now : 1;
		std::map<int, std::vector<long long> > byBand, atkByBand;
		for (std::map<DWORD, TPlayerBotHpSample>::iterator it = s_mapPlayerBotHpSamples.begin();
				it != s_mapPlayerBotHpSamples.end(); )
		{
			if (now - it->second.when >= PLAYERBOT_HP70_SAMPLE_TTL_MS)
			{
				s_mapPlayerBotHpSamples.erase(it++);
				continue;
			}
			byBand[it->second.band].push_back(it->second.hp);
			atkByBand[it->second.band].push_back(it->second.atk);
			++it;
		}
		s_mapPlayerBotHpMedian.clear();
		for (std::map<int, std::vector<long long> >::iterator it = byBand.begin(); it != byBand.end(); ++it)
		{
			std::vector<long long>& v = it->second;
			if ((int)v.size() < PLAYERBOT_HP70_MIN_SAMPLES)
				continue;
			std::nth_element(v.begin(), v.begin() + v.size() / 2, v.end());
			s_mapPlayerBotHpMedian[it->first] = v[v.size() / 2];
		}
		s_mapPlayerBotAtkMedian.clear();
		for (std::map<int, std::vector<long long> >::iterator it = atkByBand.begin(); it != atkByBand.end(); ++it)
		{
			std::vector<long long>& v = it->second;
			if ((int)v.size() < PLAYERBOT_HP70_MIN_SAMPLES)
				continue;
			std::nth_element(v.begin(), v.begin() + v.size() / 2, v.end());
			s_mapPlayerBotAtkMedian[it->first] = v[v.size() / 2];
		}
	}

	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2: the medians of the band of five levels a level is in (sampled from
	// PLAYERBOT_HP70_SAMPLE_FROM_LEVEL, PLAYERBOT_HP70_MIN_SAMPLES live samples a band at least); false - no median.
	bool GetPlayerBotBandMedians(int level, long long* hpOut, long long* atkOut)
	{
		RefreshPlayerBotHpMedians(get_dword_time());
		const int band = GetPlayerBotHpBand(level);
		std::map<int, long long>::const_iterator h = s_mapPlayerBotHpMedian.find(band);
		std::map<int, long long>::const_iterator a = s_mapPlayerBotAtkMedian.find(band);
		if (h == s_mapPlayerBotHpMedian.end() || a == s_mapPlayerBotAtkMedian.end())
			return false;
		if (hpOut)
			*hpOut = h->second;
		if (atkOut)
			*atkOut = a->second;
		return true;
	}

	int GetPlayerBotHp70MinLevel()
	{
		static int s_i = -1;
		if (s_i < 0)
			s_i = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SM_HP70_MIN_LEVEL", 70, 1, 250);
		return s_i;
	}

	// A bot of PLAYERBOT_SM_HP70_MIN_LEVEL and up whose max HP is under its band's median; the median out.
	bool IsPlayerBotUnderHpMedian(LPCHARACTER ch, long long* medianOut)
	{
		if (medianOut)
			*medianOut = 0;
		if (!ch || !IsPlayerBotErrandSwitchOn(2) || (int)ch->GetLevel() < GetPlayerBotHp70MinLevel())
			return false;
		RefreshPlayerBotHpMedians(get_dword_time());
		std::map<int, long long>::const_iterator it = s_mapPlayerBotHpMedian.find(GetPlayerBotHpBand((int)ch->GetLevel()));
		if (it == s_mapPlayerBotHpMedian.end())
			return false;
		if (medianOut)
			*medianOut = it->second;
		return (long long)ch->GetMaxHP() < it->second;
	}

	// MT2009_PLUS_BOT_SM_HP70_V1: an exp-locked bot's Kupon SM go on its counter (the header).
	bool IsPlayerBotExpLocked(LPCHARACTER ch);	// playerbot_unique_slots.h
	unsigned int s_uPlayerBotLockedCouponKeeps = 0;

	bool IsPlayerBotLockedCouponSeller(LPCHARACTER ch)
	{
		return ch && IsPlayerBotErrandSwitchOn(3) && IsPlayerBotExpLocked(ch);
	}

	// ---------------------------------------------------------------- the per-bot tick

	void WritePlayerBotErrandCensus(DWORD now)
	{
		if (s_dwPlayerBotErrandNextCensus != 0 && (int)(now - s_dwPlayerBotErrandNextCensus) < 0)
			return;
		s_dwPlayerBotErrandNextCensus = now + PLAYERBOT_ERRAND_CENSUS_MS;
		unsigned int waiting = 0, arrivals = 0;
		for (std::map<DWORD, TPlayerBotErrandBot>::iterator it = s_mapPlayerBotErrands.begin(); it != s_mapPlayerBotErrands.end(); )
		{
			TPlayerBotErrandBot& b = it->second;
			bool live = false;
			for (int i = 0; i < PLAYERBOT_ERRAND_KINDS; ++i)
				if (b.first[i] != 0 && now - b.last[i] < PLAYERBOT_ERRAND_TTL_MS)
					live = true;
			if (live)
				++waiting;
			if (b.dwArrivedAt != 0 && now - b.dwArrivedAt < PLAYERBOT_ERRAND_STAY_MS)
				++arrivals;
			// a bot not ticked for an hour is gone from this core
			// MT2009_PLUS_BOT_ERRAND_CLEANUP_FIX_V1 (night of 8 November 2026): dwNextTick is the NEXT tick - up to 30 s
			// ahead - and `now - dwNextTick` unsigned wrapped past an hour for every bot ticked lately: each census (ten
			// minutes) erased nearly every bot's entry, the next pass saw it "first" after the warm-up and made it an
			// arrival - 1197..1319 arrivals a census on channel 1 of ~1250 bots, all pinned against the roam and sent on an
			// arrival trip every ten minutes. Signed now; a census-only entry (never ticked) goes when the census lost it.
			const bool goneTicked = b.dwNextTick != 0 && (int)(now - b.dwNextTick) >= (int)PLAYERBOT_ERRAND_STAY_MS;
			const bool goneSeen = b.dwNextTick == 0 && b.dwPresenceSeen != 0 &&
					(int)(now - b.dwPresenceSeen) >= (int)PLAYERBOT_ERRAND_STAY_MS;
			if (goneTicked || goneSeen)
				s_mapPlayerBotErrands.erase(it++);
			else
				++it;
		}
		std::string noted;
		char buf[32];
		for (int i = 0; i < PLAYERBOT_ERRAND_KINDS; ++i)
		{
			snprintf(buf, sizeof(buf), "%s%s:%u", noted.empty() ? "" : ",", PLAYERBOT_ERRAND_NAMES[i],
					s_kPlayerBotErrandStats.noted[i]);
			noted += buf;
		}
		sys_log(0, "PLAYERBOT_ERRAND: census channel=%u batch=%d with_errands=%u held=%u released_batch=%u released_wait=%u "
				"released_urgent=%u asks_after_release=%u weapon_errands=%u arrivals_hour=%u new_arrivals=%u arrival_trips=%u "
				"pin_census=%u stay_busy_census=%u hp_bands=%u locked_coupon_keeps=%u noted=%s",
				(unsigned int)g_bChannel, IsPlayerBotErrandSwitchOn(0) ? 1 : 0, waiting, s_kPlayerBotErrandStats.held,
				s_kPlayerBotErrandStats.releasedBatch, s_kPlayerBotErrandStats.releasedWait,
				s_kPlayerBotErrandStats.releasedUrgent, s_kPlayerBotErrandStats.releasedAgain,
				s_kPlayerBotErrandStats.weaponErrands, arrivals, s_kPlayerBotErrandStats.arrivals,
				s_kPlayerBotErrandStats.arrivalTrips, s_kPlayerBotErrandStats.pinned, s_kPlayerBotErrandStats.stayBusy,
				(unsigned int)s_mapPlayerBotHpMedian.size(), s_uPlayerBotLockedCouponKeeps, noted.c_str());
		s_kPlayerBotErrandStats = TPlayerBotErrandStats();
		s_uPlayerBotLockedCouponKeeps = 0;
	}

	// Asked for every bot from the AI loop (CPlayerBotManager::Update), next to the day goal.
	void ManagePlayerBotErrands(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!ch || !ch->IsItemLoaded())
			return;
		if (!now)
			now = 1;
		if (s_dwPlayerBotErrandCoreStart == 0)
			s_dwPlayerBotErrandCoreStart = now;
		WritePlayerBotErrandCensus(now);
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotErrandBot& b = s_mapPlayerBotErrands[pid];
		// away from this core for a while (moved off and back): a new sighting
		// MT2009_PLUS_BOT_ERRAND_PRESENCE_V1 (night of 8 November 2026): and not merely a bot whose AI pass skipped this
		// call for five minutes - a Monkey Dungeon run, a dungeon, a duel - while it stood on this core all along: the
		// channel census (every 10 s, every bot in the game) says it never left. 822 of 1197 bots of channel 1 were
		// "arrivals" so, each pinned against the roam for up to 45 minutes and sent on an arrival trip, so the roam
		// brought bots from channel 2 and found none to send back (ch1 1538 / ch2 467 at 01:47 against 60/40).
		// Switch: event flag m2_bot_errand_presence_off 1. Log: PLAYERBOT_ERRAND: resighting kept (throttled).
		const bool tickGap = b.bSeen && b.dwNextTick != 0 && (int)(now - b.dwNextTick) > (int)(10 * PLAYERBOT_ERRAND_TICK_MS);
		const bool stayedHere = tickGap && b.dwPresenceSeen != 0 &&
				(int)(now - b.dwPresenceSeen) <= (int)(10 * PLAYERBOT_ERRAND_TICK_MS) &&
				quest::CQuestManager::instance().GetEventFlag("m2_bot_errand_presence_off") == 0;
		if (stayedHere)
		{
			++s_uPlayerBotErrandResightKept;
			PlayerBotLogThrottled("errand_resight_kept", now,
					"PLAYERBOT_ERRAND: resighting kept pid=%u name=%s gap_s=%u map=%ld kept=%u",
					pid, ch->GetName(), (unsigned int)((now - b.dwNextTick) / 1000U), ch->GetMapIndex(),
					s_uPlayerBotErrandResightKept);
		}
		else if (tickGap)
		{
			b.bSeen = false;
			b.bTripStarted = false;
			b.dwArrivedAt = 0;
			b.dwLastActivity = 0;
			b.dwReleasedAt = 0;
		}
		const bool shopChannel = g_bChannel == playerbot_channel_rules::SHOP_CHANNEL;
		const bool table = CPlayerBotManager::instance().IsChannelTableMode();
		// the shop channel: an arrival is a bot first seen after the core's warm-up (a move, or a login)
		if (!b.bSeen)
		{
			b.bSeen = true;
			if (shopChannel && table && now - s_dwPlayerBotErrandCoreStart >= PLAYERBOT_ERRAND_WARMUP_MS &&
					(b.dwFirstPresence == 0 || b.dwFirstPresence - s_dwPlayerBotErrandCoreStart >= PLAYERBOT_ERRAND_WARMUP_MS ||
					 quest::CQuestManager::instance().GetEventFlag("m2_bot_errand_presence_off") != 0))
			{
				b.dwArrivedAt = now;
				++s_kPlayerBotErrandStats.arrivals;
			}
		}
		if (shopChannel && b.dwArrivedAt != 0 &&
				(state.offlineShop.buyOwner != 0 || state.offlineShop.visiting || state.bMarketTrip ||
				 state.bMarketToJoan || state.bVisitingShop ||
				 (state.dwProgressionTripUntil != 0 && (int)(now - state.dwProgressionTripUntil) < 0)))
			b.dwLastActivity = now;
		if (b.dwNextTick != 0 && (int)(now - b.dwNextTick) < 0)
			return;
		b.dwNextTick = now + PLAYERBOT_ERRAND_TICK_MS;
		// 6. the HP sample of the band
		if ((int)ch->GetLevel() >= PLAYERBOT_HP70_SAMPLE_FROM_LEVEL && !ch->IsDead())
		{
			std::map<DWORD, TPlayerBotHpSample>::iterator s = s_mapPlayerBotHpSamples.find(pid);
			if (s == s_mapPlayerBotHpSamples.end() || now - s->second.when >= PLAYERBOT_HP70_SAMPLE_MS)
			{
				TPlayerBotHpSample& sample = s_mapPlayerBotHpSamples[pid];
				sample.band = GetPlayerBotHpBand((int)ch->GetLevel());
				sample.hp = (long long)ch->GetMaxHP();
				sample.atk = GetPlayerBotRealAttack(ch);	// MT2009_PLUS_BOT_WUKONG_STRENGTH_V2
				sample.when = now;
			}
		}
		if (!table || !IsPlayerBotErrandSwitchOn(0))
			return;
		// 7. an arrival starts its progression trip at once
		if (shopChannel && b.dwArrivedAt != 0 && !b.bTripStarted && now - b.dwArrivedAt < PLAYERBOT_ERRAND_ARRIVAL_PIN_MS)
		{
			b.bTripStarted = true;
			if (state.dwProgressionTripUntil == 0 || (int)(now - state.dwProgressionTripUntil) >= 0)
			{
				state.dwProgressionTripNext = now;
				++s_kPlayerBotErrandStats.arrivalTrips;
				PlayerBotLogThrottled("errand_arrival", now,
						"PLAYERBOT_ERRAND: arrival trip pid=%u name=%s map=%ld level=%u gold=%lld",
						pid, ch->GetName(), ch->GetMapIndex(), (unsigned int)ch->GetLevel(), (long long)ch->GetGold());
			}
		}
		// 5. the weapon errand, off the shop channel, for a free bot
		if (!shopChannel && IsPlayerBotErrandSwitchOn(1) && (b.dwNextWeaponAsk == 0 || (int)(now - b.dwNextWeaponAsk) >= 0) &&
				!ch->IsDead() && !ch->GetParty() && !ch->GetVictim() && !ch->GetExchange() && !ch->GetMyShop() &&
				!IsPlayerBotOnDungeonRun(pid) && !IsPlayerBotInDungeonBusiness(ch, state) &&
				!(state.dwLastCombatActionTime != 0 && now - state.dwLastCombatActionTime < 20000) &&
				state.dwGuildWarEnemyGID == 0 && !IsPlayerBotGearFrozen(ch) && PlayerBotWantsWeaponUpgradeFromMarket(ch))
		{
			b.dwNextWeaponAsk = now + PLAYERBOT_ERRAND_WEAPON_ASK_MS;
			const TPlayerBotWeaponUpgradeLook& look = LookPlayerBotWeaponUpgrade(ch, now);
			++s_kPlayerBotErrandStats.weaponErrands;
			const bool asked = RequestPlayerBotShopErrand(ch, PLAYERBOT_ERRAND_WEAPON, now);
			PlayerBotLogThrottled("errand_weapon", now,
					"PLAYERBOT_ERRAND: weapon errand pid=%u name=%s level=%u channel=%u vnum=%u price=%lld gain=%lld%% asked=%d",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)g_bChannel, look.vnum, look.price,
					look.gain, asked ? 1 : 0);
		}
	}
}

#else

namespace
{
	inline bool IsPlayerBotUnderHpMedian(LPCHARACTER, long long* medianOut)
	{
		if (medianOut)
			*medianOut = 0;
		return false;
	}
}

#endif

#endif
