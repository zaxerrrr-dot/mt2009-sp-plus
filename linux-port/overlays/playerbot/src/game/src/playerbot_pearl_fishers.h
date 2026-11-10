#ifndef __INC_METIN2_PLAYERBOT_PEARL_FISHERS_H__
#define __INC_METIN2_PLAYERBOT_PEARL_FISHERS_H__

// MT2009_PLUS_BOT_PEARL_FISHERS_V1 / MT2009_PLUS_BOT_VILLAGE70_V1 (the owner, 10 November 2026, on the bots' report of the
// same day - dist/aktualizacje/test-plus/RAPORT-ROZWOJ-BOTOW-2026-11-10.md, 3.4 / 3.12 / 4):
//
// 1. "Kanal 1 marnuje czas - ogarnij to". A bot of 70+ on the first channel stood in a village half of the time (419 of
//    819 at 18:20; 169 of 579 on the second) and made ~75 M exp an hour against ~196 M on the second. Measured from the
//    map changes of 10 November 06:00-12:00 (bots 70+, the time from an arrival in a village to the next map change):
//    channel 1 34.1 % of the time in a village - after a stall service 14.0 %, the Alchemist 5.7 %, the first village's
//    services 4.1 %, the river 2.5 %; channel 2 25.6 % - the services 6.9 %, the Alchemist 6.4 %, the river 5.1 %. The
//    stall visits were 8 222 in the six hours (1.7 an hour a bot), most of them one take-off of a line from an expired
//    stand and back out, the renewal never reached (the take-offs come first and end the visit; the expired stand calls
//    its owner again a quarter of an hour later). The lada (playerbot_lada.h) feeds a running stand from anywhere and
//    the fair price edits its lines from the stand's core, so a running stand rarely needs its owner. For a bot of
//    m2_bot_village70_level (70) and up:
//      * the stall's far round is m2_bot_village70_stall_min (120) minutes instead of 45, and a slipped price does not
//        call the owner from afar while the lada is on (the lada's own repricing reaches the line);
//      * an expired stand is renewed first, on the visit's first step - the take-offs wait for a later visit, so a
//        renewal costs one visit, not one a line;
//      * the trip to the Alchemist (alchemy_to_alchemist, the dragon stones' elixir and refine) from outside a first
//        village waits m2_bot_village70_alch_min (180) minutes since the last such trip; a bot that arrives in a first
//        village for anything else (its stall, a service) does the Alchemist's work there at once (its clock cleared on
//        the arrival) - the work goes with another errand;
//      * a stock to clear (sash goods, another build's books) waits the same long round, not a quarter of an hour;
//      * it does not fish, unless it is a designated pearl fisher (2.).
//    Expected (the same six hours replayed with the stall trips held to the long round and a renewal - four in six
//    hours a bot -, two Alchemist trips, no river for the hunters): channel 1 34.1 % -> ~24 %, channel 2 25.6 % ->
//    ~18 % of the 70+ bots' time in a village; the census's village70 share_pm measures it live.
// 2. "Perly jako czesc dynamicznego rynku: kiedy jest taki brak, wiecej botow zostaje rybakami, otwiera ryby, otwiera
//    malze i wystawia perly. Im wiekszy brak, tym wiecej rybakow na serwerze." The world made ~220 pearls a day; 262-294
//    bots wanted a white pearl on the board and the supply was zero.
//    The market (every m2_bot_pearl_pass_s, 180 s, each core): the materials' board (playerbot_mats_board.h) gives per
//    kind k the demand D (the worn steps' lack) and the bags' surplus S of the bots of this core; every core writes its
//    row to player.playerbot_pearl_market (keyed by its p2p port) and sums the rows of the last ten minutes - the world.
//    The listed units L = max(the board's count of the shop channel's stands, the fair price's stock of every stand).
//        short_k = max(0, D_k - L_k - S_k)                      k = white 27992, blue 27993, red 27994, Malz 27987
//        U       = sum w_k x short_k x p_k                       w = 1, 2, 3, 0.2 (a blue is two whites' worth of
//                                                                fishing, a red three; a clam a fifth); p_k = the
//                                                                fair ratio of the kind (its price over its
//                                                                reference), clamped to 1.0 .. 2.0
//        share   = min + (max - min) x U / (U + H)               min m2_bot_pearl_fisher_min_pm (5 permille), max
//                                                                m2_bot_pearl_fisher_max_pm (120), H
//                                                                m2_bot_pearl_fisher_half (60 units)
//        target  = min(cap, round(eligible bots of the world x share))   cap m2_bot_pearl_fisher_cap (300)
//    moved at most max(3, 15 %) a pass toward the computed number. With no shortage the share is the minimum; the
//    bigger the shortage, the closer to the maximum.
//    Who fishes: a bot's weight w_b (permille) - 0 for a dropper, a companion, a party member, a bot under level 30 or
//    at m2_bot_pearl_fisher_max_level (95) and up, one the young heroes' weapon holds; else 1500 under 70, 1000 at
//    70-84, 400 at 85 and up (the strongest hunters last), x2 an exp-locked bot (its exp waits anyway), x0.5 a bot the
//    progression checklist holds with something missing (it has work). A bot fishes when
//        hash(pid, the day) < target x w_b / (the world's sum of w)      (the hash uniform in [0, 1))
//    so every core decides the same for the same bot, the expected count is the target, the lower levels and the idle
//    go first, and the set turns over every day. A designated fisher goes to the river from anywhere, stays the hour
//    (PLAYERBOT_RYBAK_MAX_SESSION), rests m2_bot_pearl_fisher_rest_min (5) minutes between sessions, opens every live
//    fish (as every bot), and opens its clams over its keep (PLAYERBOT_SHELLFISH_KEEP, or the anvil's reserve when it
//    needs clams itself) while pearls are short more than clams are (U of the pearls > the clams' share of U); one
//    pearl a pearl kind short on the board makes its counter due (IsPlayerBotMatsBoardCounterDue), and the lada lists
//    the pearls and clams over its keep. When the supply recovers, U falls and so does the target.
// 3. "Pieczenie ryb dla botow jest darmowe": the campfire's Wysuszone Drzewo is given to a bot that roasts, not bought
//    (BuyPlayerBotFishWood; m2_bot_fish_wood_free_off 1 - bought again, through the hourly cap). Still the valuable
//    kinds only (playerbot_fish_roast.h).
// 4. Census "PLAYERBOT_PEARL:" every 10 minutes, each core: the world's fishers against the target (designated, at the
//    water), the share and U, per kind demand / supply / listed / short; the core's clams caught and opened, pearls
//    made by kind (by designated fishers / by others), listed and sold on the stands (units, yang); the bots of 70+
//    of this core sampled every minute - in a village (the share), at the water, at a stall, at an Alchemist; their
//    trips into a village by kind; the held trips (Alchemist, slip calls due from afar), the renew-first visits, the
//    Alchemist looks batched into an arrival, and hunter_no_fish (the angler checks a 70+ hunter was refused - checks,
//    not bots).
//    The channel's number is the sum of its cores' lines (ch=).
//
// Switches (event flags, read once a second; 0 / unset is the default):
//   m2_bot_village70_off 1          1. off - the old stall round, take-offs first, the Alchemist on its own clock, 70+
//                                   bots fish by their moods;
//   m2_bot_village70_level          the level of 1. (default 70, 30..120);
//   m2_bot_village70_stall_min      the far round, minutes (default 120, 45..480);
//   m2_bot_village70_alch_min       the Alchemist's trip gap, minutes (default 180, 30..720);
//   m2_bot_pearl_fishers_off 1      2. off - no designated fisher (the 70+ do not fish at all while 1. is on);
//   m2_bot_pearl_fisher_min_pm / _max_pm / _half / _cap / _max_level / _rest_min / _pass_s - the numbers above;
//   m2_bot_fish_wood_free_off 1     3. off.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_lada.h, in the anonymous namespace; its
// hooks are declared where they are asked (playerbot_activities.h, playerbot_offline_shop.h, playerbot_alchemy.h,
// playerbot_travel.h, playerbot_mats_board.h).

namespace
{
	const DWORD PLAYERBOT_PEARL_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_PEARL_SAMPLE_MS = 60 * 1000;
	const DWORD PLAYERBOT_PEARL_ROW_FRESH_S = 600;
	const int PLAYERBOT_PEARL_KINDS = 4;	// white, blue, red, the clam
	const DWORD PLAYERBOT_PEARL_KIND_VNUM[PLAYERBOT_PEARL_KINDS] = { 27992, 27993, 27994, 27987 };
	const int PLAYERBOT_PEARL_KIND_WEIGHT_PM[PLAYERBOT_PEARL_KINDS] = { 1000, 2000, 3000, 200 };
	const char* const PLAYERBOT_PEARL_KIND_NAME[PLAYERBOT_PEARL_KINDS] = { "white", "blue", "red", "clam" };

	struct TPlayerBotPearlCfg
	{
		bool v70On, fishersOn, woodFree;
		int v70Level, stallMin, alchMin, minPm, maxPm, half, cap, maxLevel, restMin, passS;
		TPlayerBotPearlCfg() : v70On(true), fishersOn(true), woodFree(true), v70Level(70), stallMin(120), alchMin(180),
				minPm(5), maxPm(120), half(60), cap(300), maxLevel(95), restMin(5), passS(180) {}
		bool operator!=(const TPlayerBotPearlCfg& o) const
		{
			return v70On != o.v70On || fishersOn != o.fishersOn || woodFree != o.woodFree || v70Level != o.v70Level ||
					stallMin != o.stallMin || alchMin != o.alchMin || minPm != o.minPm || maxPm != o.maxPm || half != o.half ||
					cap != o.cap || maxLevel != o.maxLevel || restMin != o.restMin || passS != o.passS;
		}
	};
	TPlayerBotPearlCfg s_kPlayerBotPearlCfg;

	const TPlayerBotPearlCfg& GetPlayerBotPearlCfg()
	{
		static DWORD s_dwAt = 0;
		static bool s_bLogged = false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			TPlayerBotPearlCfg& c = s_kPlayerBotPearlCfg;
			const TPlayerBotPearlCfg was = c;
			auto value = [&q](const char* flag, int def, int lo, int hi) {
				const int v = q.GetEventFlag(flag);
				return v <= 0 ? def : std::max(lo, std::min(hi, v));
			};
			c.v70On = q.GetEventFlag("m2_bot_village70_off") == 0;
			c.fishersOn = q.GetEventFlag("m2_bot_pearl_fishers_off") == 0;
			c.woodFree = q.GetEventFlag("m2_bot_fish_wood_free_off") == 0;
			c.v70Level = value("m2_bot_village70_level", 70, 30, 120);
			c.stallMin = value("m2_bot_village70_stall_min", 120, 45, 480);
			c.alchMin = value("m2_bot_village70_alch_min", 180, 30, 720);
			c.minPm = value("m2_bot_pearl_fisher_min_pm", 5, 1, 500);
			c.maxPm = std::max(c.minPm, value("m2_bot_pearl_fisher_max_pm", 120, 1, 500));
			c.half = value("m2_bot_pearl_fisher_half", 60, 1, 100000);
			c.cap = value("m2_bot_pearl_fisher_cap", 300, 1, 5000);
			c.maxLevel = value("m2_bot_pearl_fisher_max_level", 95, 31, 121);
			c.restMin = value("m2_bot_pearl_fisher_rest_min", 5, 1, 120);
			c.passS = value("m2_bot_pearl_pass_s", 180, 30, 3600);
			if (!s_bLogged || was != c)
			{
				s_bLogged = true;
				sys_log(0, "PLAYERBOT_PEARL: config village70=%d level=%d stall_min=%d alch_min=%d fishers=%d min_pm=%d "
						"max_pm=%d half=%d cap=%d max_level=%d rest_min=%d pass_s=%d wood_free=%d",
						c.v70On ? 1 : 0, c.v70Level, c.stallMin, c.alchMin, c.fishersOn ? 1 : 0, c.minPm, c.maxPm, c.half,
						c.cap, c.maxLevel, c.restMin, c.passS, c.woodFree ? 1 : 0);
			}
		}
		return s_kPlayerBotPearlCfg;
	}

	// BuyPlayerBotFishWood's question (playerbot_activities.h).
	bool IsPlayerBotFishWoodFree()
	{
		return GetPlayerBotPearlCfg().woodFree;
	}

	// A designated fisher's rest between two sessions (EndPlayerBotFishingSession).
	DWORD GetPlayerBotPearlFisherRestMs()
	{
		return (DWORD)GetPlayerBotPearlCfg().restMin * 60000U;
	}

	bool IsPlayerBotPearlBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	// ------------------------------------------------------------------------------------------------ the census

	enum EPlayerBotV70Trip
	{
		V70_TRIP_STALL = 0,
		V70_TRIP_ALCH,
		V70_TRIP_FISH,
		V70_TRIP_SERVICES,
		V70_TRIP_OTHER,
		V70_TRIP_KINDS
	};
	const char* const PLAYERBOT_V70_TRIP_NAMES[V70_TRIP_KINDS] = { "stall", "alchemist", "fishing", "services", "other" };

	struct TPlayerBotPearlCensus
	{
		unsigned int clamsCaught = 0, clamsOpened = 0, clamsOpenedFisher = 0;
		unsigned int pearls[3] = { 0, 0, 0 }, pearlsFisher[3] = { 0, 0, 0 };
		unsigned int samples = 0, sVillage = 0, sFishing = 0, sStall = 0, sAlch = 0;
		unsigned int sFisherDesignated = 0, sFisherFishing = 0;
		unsigned int trips[V70_TRIP_KINDS] = { 0, 0, 0, 0, 0 };
		unsigned int alchHeld = 0, alchBatched = 0, slipHeld = 0, renewFirst = 0, hunterNoFish = 0;
	};
	TPlayerBotPearlCensus s_kPlayerBotPearlCensus;

	// The pearls and clams put up on the lada / sold off the stands (playerbot_lada.h, playerbot_offline_shop.h),
	// declared in playerbot_fish_roast.h beside the fish's own: s_kPlayerBotPearlStallCensus.

	// ------------------------------------------------------------------------------------------------ the market

	struct TPlayerBotPearlWorld
	{
		long long demand[PLAYERBOT_PEARL_KINDS], supply[PLAYERBOT_PEARL_KINDS], listed[PLAYERBOT_PEARL_KINDS],
				shortage[PLAYERBOT_PEARL_KINDS];
		int ratioPm[PLAYERBOT_PEARL_KINDS];
		long long poolPm;	// the world's sum of the weights
		int eligible, fishers, fishing, cores;
		long long unitsPm;	// U x 1000
		int sharePm, computed, target;
		bool openClams;
		DWORD at;
		TPlayerBotPearlWorld() : poolPm(0), eligible(0), fishers(0), fishing(0), cores(0), unitsPm(0), sharePm(0),
				computed(0), target(0), openClams(false), at(0)
		{
			for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
			{
				demand[i] = supply[i] = listed[i] = shortage[i] = 0;
				ratioPm[i] = 1000;
			}
		}
	};
	TPlayerBotPearlWorld s_kPlayerBotPearlWorld;
	bool s_bPlayerBotPearlTable = false;

	// The day of the designation's hash: the set of fishers turns over once a day.
	DWORD GetPlayerBotPearlDay()
	{
		return (DWORD)(get_global_time() / 86400);
	}

	// The weight of a bot for the fishers' draw, permille (0: never a designated fisher).
	int GetPlayerBotPearlFisherWeightPm(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		const TPlayerBotPearlCfg& c = GetPlayerBotPearlCfg();
		if (!IsPlayerBotPearlBot(ch) || IsPlayerBotSidekickServing(ch) || IsPlayerBotDropper(state.bPersonality) ||
				ch->GetParty() != NULL)
			return 0;
		const int level = (int)ch->GetLevel();
		if (level < (int)PLAYERBOT_FISHING_MIN_LEVEL || level >= c.maxLevel)
			return 0;
		if (PlayerBotMlodziBlocksLeisure(ch->GetPlayerID()))
			return 0;
		int w = level < 70 ? 1500 : (level < 85 ? 1000 : 400);
		if (IsPlayerBotExpLocked(ch))
			w *= 2;
		if (GetPlayerBotProgressionNeeds(ch->GetPlayerID()) != 0)
			w /= 2;
		return w;
	}

	// A designated pearl fisher now: the market's draw (see the head of the file).
	bool IsPlayerBotPearlFisherOf(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		const TPlayerBotPearlCfg& c = GetPlayerBotPearlCfg();
		const TPlayerBotPearlWorld& w = s_kPlayerBotPearlWorld;
		if (!c.fishersOn || w.target <= 0 || w.poolPm <= 0)
			return false;
		const int weight = GetPlayerBotPearlFisherWeightPm(ch, state);
		if (weight <= 0)
			return false;
		const unsigned long long draw = (unsigned long long)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x5045524cU ^
				(GetPlayerBotPearlDay() * 2654435761U)) % 1000000U);
		const unsigned long long bar = (unsigned long long)w.target * (unsigned long long)weight * 1000000ULL /
				(unsigned long long)w.poolPm;
		return draw < bar;
	}

	bool IsPlayerBotPearlFisher(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return it != s_mapPlayerBotAIStates.end() && IsPlayerBotPearlFisherOf(ch, it->second);
	}

	// ------------------------------------------------------------------------------------------------ 1. the 70+

	bool IsPlayerBotVillage70(LPCHARACTER ch)
	{
		const TPlayerBotPearlCfg& c = GetPlayerBotPearlCfg();
		return c.v70On && IsPlayerBotPearlBot(ch) && (int)ch->GetLevel() >= c.v70Level;
	}

	// IsPlayerBotAngler's question: a hunter of 70+ that is no designated fisher does not fish.
	bool IsPlayerBotHunterNoFish(LPCHARACTER ch)
	{
		if (!IsPlayerBotVillage70(ch) || IsPlayerBotPearlFisher(ch))
			return false;
		++s_kPlayerBotPearlCensus.hunterNoFish;
		return true;
	}

	// The stall's far round (playerbot_offline_shop.h).
	DWORD GetPlayerBotOfflineFarServiceMs(LPCHARACTER ch)
	{
		if (IsPlayerBotVillage70(ch))
			return (DWORD)GetPlayerBotPearlCfg().stallMin * 60000U;
		return PLAYERBOT_OFFLINE_FAR_SERVICE_MIN_MS;
	}

	// A slipped price calls its owner from afar - not a bot of 70+ while the lada is on.
	bool PlayerBotSlipCallsFromAfar(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (IsPlayerBotVillage70(ch) && IsPlayerBotLadaOn())
		{
			++s_kPlayerBotPearlCensus.slipHeld;
			return false;
		}
#else
		(void)ch;
#endif
		return true;
	}

	// An expired stand of a bot of 70+ is renewed before any take-off - the whole visit (its start's stamp); one that
	// is expired again within PLAYERBOT_V70_RENEW_RETRY_MS of such a visit did not take, and goes the old way.
	const DWORD PLAYERBOT_V70_RENEW_RETRY_MS = 30 * 60 * 1000;
	struct TPlayerBotV70Renew
	{
		DWORD at, visit;
	};
	std::map<DWORD, TPlayerBotV70Renew> s_mapPlayerBotV70Renew;

	bool PlayerBotStallRenewFirst(LPCHARACTER ch, DWORD visitStarted)
	{
		if (!IsPlayerBotVillage70(ch))
			return false;
		const DWORD now = get_dword_time();
		std::map<DWORD, TPlayerBotV70Renew>::iterator it = s_mapPlayerBotV70Renew.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotV70Renew.end())
		{
			if (it->second.visit == visitStarted)
				return true;
			if (now - it->second.at < PLAYERBOT_V70_RENEW_RETRY_MS)
				return false;
		}
		TPlayerBotV70Renew r = { now ? now : 1, visitStarted };
		s_mapPlayerBotV70Renew[ch->GetPlayerID()] = r;
		++s_kPlayerBotPearlCensus.renewFirst;
		return true;
	}

	// The Alchemist's trips from outside a first village: pid -> the last one's time.
	std::map<DWORD, DWORD> s_mapPlayerBotV70AlchTrip;

	// True: the trip waits (playerbot_alchemy.h, before "alchemy_to_alchemist").
	bool PlayerBotVillage70HoldsAlchemistTrip(LPCHARACTER ch, DWORD dwNow)
	{
		if (!IsPlayerBotVillage70(ch))
			return false;
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotV70AlchTrip.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotV70AlchTrip.end())
		{
			// The first look after a start (or after this core first saw the bot) is spread over the gap.
			const DWORD gap = (DWORD)GetPlayerBotPearlCfg().alchMin * 60000U;
			s_mapPlayerBotV70AlchTrip[ch->GetPlayerID()] = dwNow - PlayerBotNavHash(ch->GetPlayerID() ^ 0x414c4348U) % gap;
			++s_kPlayerBotPearlCensus.alchHeld;
			return true;
		}
		if (dwNow - it->second < (DWORD)GetPlayerBotPearlCfg().alchMin * 60000U)
		{
			++s_kPlayerBotPearlCensus.alchHeld;
			return true;
		}
		return false;
	}

	void NotePlayerBotVillage70AlchemistTrip(LPCHARACTER ch, DWORD dwNow)
	{
		if (ch && IsPlayerBotVillage70(ch))
			s_mapPlayerBotV70AlchTrip[ch->GetPlayerID()] = dwNow ? dwNow : 1;
	}

	// TransitionPlayerBotMap's line (playerbot_travel.h): a bot of 70+ into a village, by the kind of trip.
	void NotePlayerBotVillage70Trip(LPCHARACTER ch, long targetMap, const char* reason)
	{
		if (!ch || !IsPlayerBotVillageMap(targetMap) || !IsPlayerBotPearlBot(ch) ||
				(int)ch->GetLevel() < GetPlayerBotPearlCfg().v70Level)
			return;
		int kind = V70_TRIP_OTHER;
		if (reason)
		{
			if (strstr(reason, "offline_shop_service"))
				kind = V70_TRIP_STALL;
			else if (strstr(reason, "alchem"))
				kind = V70_TRIP_ALCH;
			else if (strstr(reason, "fishing"))
				kind = V70_TRIP_FISH;
			else if (strstr(reason, "services"))
				kind = V70_TRIP_SERVICES;
		}
		++s_kPlayerBotPearlCensus.trips[kind];
	}

	// ------------------------------------------------------------------------------------------------ 2. the clams

	// ProcessPlayerBotCatch's question (playerbot_activities.h): a designated fisher opens its clams over its keep
	// while pearls are shorter than clams. Returns the keep, or -1: the ordinary rules.
	int GetPlayerBotPearlFisherClamKeep(LPCHARACTER ch)
	{
		if (!s_kPlayerBotPearlWorld.openClams || !IsPlayerBotPearlFisher(ch))
			return -1;
		if (PlayerBotNeedsRefineMaterial(ch, PLAYERBOT_SHELLFISH_VNUM))
			return std::max(PLAYERBOT_SHELLFISH_KEEP, GetPlayerBotRefineMaterialReserve(ch, PLAYERBOT_SHELLFISH_VNUM));
		return PLAYERBOT_SHELLFISH_KEEP;
	}

	// A live fish gave a clam / a clam was opened (outcome: PLAYERBOT_SHELL_*).
	void NotePlayerBotPearlClamCaught()
	{
		++s_kPlayerBotPearlCensus.clamsCaught;
	}

	void NotePlayerBotPearlClamOpened(LPCHARACTER ch, int outcome)
	{
		const bool fisher = IsPlayerBotPearlFisher(ch);
		TPlayerBotPearlCensus& k = s_kPlayerBotPearlCensus;
		++k.clamsOpened;
		if (fisher)
			++k.clamsOpenedFisher;
		const int kind = outcome == PLAYERBOT_SHELL_WHITE ? 0 : (outcome == PLAYERBOT_SHELL_BLUE ? 1 :
				(outcome == PLAYERBOT_SHELL_RED ? 2 : -1));
		if (kind < 0)
			return;
		++k.pearls[kind];
		if (fisher)
			++k.pearlsFisher[kind];
	}

	// IsPlayerBotMatsBoardCounterDue's weight (playerbot_mats_board.h): a pearl kind short on the board in a designated
	// fisher's surplus makes the counter due by itself.
	bool IsPlayerBotPearlFisherPearlVnum(LPCHARACTER ch, DWORD vnum)
	{
		return vnum >= 27992 && vnum <= 27994 && IsPlayerBotPearlFisher(ch);
	}

	// ------------------------------------------------------------------------------------------------ the pass

	bool EnsurePlayerBotPearlTable()
	{
		if (s_bPlayerBotPearlTable)
			return true;
		std::unique_ptr<SQLMsg> a(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_pearl_market ("
				"port SMALLINT UNSIGNED NOT NULL PRIMARY KEY, channel TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"d_w INT NOT NULL DEFAULT 0, d_b INT NOT NULL DEFAULT 0, d_r INT NOT NULL DEFAULT 0, d_c INT NOT NULL DEFAULT 0, "
				"s_w INT NOT NULL DEFAULT 0, s_b INT NOT NULL DEFAULT 0, s_r INT NOT NULL DEFAULT 0, s_c INT NOT NULL DEFAULT 0, "
				"l_w INT NOT NULL DEFAULT 0, l_b INT NOT NULL DEFAULT 0, l_r INT NOT NULL DEFAULT 0, l_c INT NOT NULL DEFAULT 0, "
				"pool_pm BIGINT NOT NULL DEFAULT 0, eligible INT NOT NULL DEFAULT 0, fishers INT NOT NULL DEFAULT 0, "
				"fishing INT NOT NULL DEFAULT 0, target INT NOT NULL DEFAULT 0, updated INT UNSIGNED NOT NULL DEFAULT 0, "
				"KEY updated (updated)) ENGINE=InnoDB"));
		s_bPlayerBotPearlTable = a && a->Get();
		return s_bPlayerBotPearlTable;
	}

	// The fair price's ratio of a kind, permille (1000 when unknown or the fair price is off).
	int GetPlayerBotPearlFairRatioPm(DWORD vnum)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (!IsPlayerBotFairPriceOn())
			return 1000;
		std::unordered_map<DWORD, TPlayerBotFairRow>::const_iterator it = s_mapPlayerBotFairShared.find(vnum);
		if (it == s_mapPlayerBotFairShared.end() || it->second.ratioPm == 0)
			return 1000;
		return (int)std::max<DWORD>(1000U, std::min<DWORD>(2000U, it->second.ratioPm));
#else
		(void)vnum;
		return 1000;
#endif
	}

	void RunPlayerBotPearlPass(DWORD dwNow)
	{
		const TPlayerBotPearlCfg& c = GetPlayerBotPearlCfg();
		TPlayerBotPearlWorld& w = s_kPlayerBotPearlWorld;
		// this core: the board's numbers, the stands' (the board's count and the fair price's, the larger), the pool
		long long d[PLAYERBOT_PEARL_KINDS], s[PLAYERBOT_PEARL_KINDS], l[PLAYERBOT_PEARL_KINDS];
		for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
		{
			const TPlayerBotMatsBoardEntry* e = GetPlayerBotMatsBoardEntry(PLAYERBOT_PEARL_KIND_VNUM[i]);
			d[i] = e ? e->demand : 0;
			s[i] = e ? e->supply : 0;
			l[i] = std::max<long long>(e ? e->listed : 0, (long long)GetPlayerBotFairStockUnits(PLAYERBOT_PEARL_KIND_VNUM[i]));
		}
		long long poolPm = 0;
		int eligible = 0, fishers = 0, fishing = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded())
				continue;
			const int weight = GetPlayerBotPearlFisherWeightPm(ch, it->second);
			if (weight <= 0)
				continue;
			poolPm += weight;
			++eligible;
			if (IsPlayerBotPearlFisherOf(ch, it->second))
			{
				++fishers;
				if (it->second.bFishingSession)
					++fishing;
			}
		}
		const DWORD nowS = (DWORD)get_global_time();
		// the world: every core's row of the last ten minutes (this one's written first)
		long long wd[PLAYERBOT_PEARL_KINDS] = { 0, 0, 0, 0 }, ws[PLAYERBOT_PEARL_KINDS] = { 0, 0, 0, 0 },
				wl[PLAYERBOT_PEARL_KINDS] = { 0, 0, 0, 0 };
		long long wPool = poolPm;
		int wEligible = eligible, wFishers = fishers, wFishing = fishing, cores = 1;
		bool fromDb = false;
		if (EnsurePlayerBotPearlTable())
		{
			std::unique_ptr<SQLMsg> put(DBManager::instance().DirectQuery(
					"REPLACE INTO player.playerbot_pearl_market (port, channel, d_w, d_b, d_r, d_c, s_w, s_b, s_r, s_c, "
					"l_w, l_b, l_r, l_c, pool_pm, eligible, fishers, fishing, target, updated) VALUES "
					"(%u, %u, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %lld, %d, %d, %d, %d, %u)",
					(unsigned int)p2p_port, (unsigned int)g_bChannel, d[0], d[1], d[2], d[3], s[0], s[1], s[2], s[3],
					l[0], l[1], l[2], l[3], poolPm, eligible, fishers, fishing, w.target, nowS));
			std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
					"SELECT COUNT(*), SUM(d_w), SUM(d_b), SUM(d_r), SUM(d_c), SUM(s_w), SUM(s_b), SUM(s_r), SUM(s_c), "
					"MAX(l_w), MAX(l_b), MAX(l_r), MAX(l_c), SUM(pool_pm), SUM(eligible), SUM(fishers), SUM(fishing) "
					"FROM player.playerbot_pearl_market WHERE updated >= %u", nowS - PLAYERBOT_PEARL_ROW_FRESH_S));
			if (msg && msg->Get() && msg->Get()->uiNumRows > 0)
			{
				MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
				const int n = row && row[0] ? atoi(row[0]) : 0;
				if (row && n > 0)
				{
					fromDb = true;
					cores = n;
					for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
					{
						wd[i] = row[1 + i] ? strtoll(row[1 + i], NULL, 10) : 0;
						ws[i] = row[5 + i] ? strtoll(row[5 + i], NULL, 10) : 0;
						wl[i] = row[9 + i] ? strtoll(row[9 + i], NULL, 10) : 0;
					}
					wPool = row[13] ? strtoll(row[13], NULL, 10) : 0;
					wEligible = row[14] ? atoi(row[14]) : 0;
					wFishers = row[15] ? atoi(row[15]) : 0;
					wFishing = row[16] ? atoi(row[16]) : 0;
				}
			}
		}
		if (!fromDb)
			for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
			{
				wd[i] = d[i];
				ws[i] = s[i];
				wl[i] = l[i];
			}
		// U, the share, the target
		long long unitsPm = 0, pearlPm = 0;
		for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
		{
			w.demand[i] = wd[i];
			w.supply[i] = ws[i];
			w.listed[i] = wl[i];
			w.shortage[i] = std::max(0LL, wd[i] - wl[i] - ws[i]);
			w.ratioPm[i] = GetPlayerBotPearlFairRatioPm(PLAYERBOT_PEARL_KIND_VNUM[i]);
			const long long part = w.shortage[i] * PLAYERBOT_PEARL_KIND_WEIGHT_PM[i] * w.ratioPm[i] / 1000;
			unitsPm += part;
			if (i < 3)
				pearlPm += part;
		}
		w.unitsPm = unitsPm;
		w.poolPm = wPool;
		w.eligible = wEligible;
		w.fishers = wFishers;
		w.fishing = wFishing;
		w.cores = cores;
		w.openClams = pearlPm > unitsPm - pearlPm;
		const long long halfPm = (long long)c.half * 1000;
		w.sharePm = c.minPm + (int)((long long)(c.maxPm - c.minPm) * unitsPm / (unitsPm + halfPm));
		w.computed = (int)std::min<long long>(c.cap, ((long long)wEligible * w.sharePm + 500) / 1000);
		if (!c.fishersOn)
			w.target = 0;
		else if (w.at == 0)
			w.target = w.computed;
		else
		{
			const int step = std::max(3, w.target * 15 / 100);
			w.target = w.computed > w.target ? std::min(w.computed, w.target + step) : std::max(w.computed, w.target - step);
		}
		w.at = dwNow ? dwNow : 1;
		PlayerBotLogThrottledEvery("pearl_pass", dwNow, 10 * 60 * 1000,
				"PLAYERBOT_PEARL: pass ch=%u port=%u cores=%d db=%d U=%lld.%03lld share_pm=%d computed=%d target=%d "
				"eligible=%d pool_pm=%lld fishers=%d fishing=%d here_eligible=%d here_fishers=%d open_clams=%d",
				(unsigned int)g_bChannel, (unsigned int)p2p_port, cores, fromDb ? 1 : 0, unitsPm / 1000, unitsPm % 1000,
				w.sharePm, w.computed, w.target, wEligible, wPool, wFishers, wFishing, eligible, fishers, w.openClams ? 1 : 0);
	}

	// Every minute: the bots of 70+ of this core, where they are and what they do.
	void SamplePlayerBotVillage70()
	{
		TPlayerBotPearlCensus& k = s_kPlayerBotPearlCensus;
		const int level = GetPlayerBotPearlCfg().v70Level;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !IsPlayerBotPearlBot(ch))
				continue;
			const TPlayerBotAIState& st = it->second;
			if (IsPlayerBotPearlFisherOf(ch, st))
			{
				++k.sFisherDesignated;
				if (st.bFishingSession)
					++k.sFisherFishing;
			}
			if ((int)ch->GetLevel() < level)
				continue;
			++k.samples;
			if (!IsPlayerBotVillageMap(ch->GetMapIndex()))
				continue;
			++k.sVillage;
			if (st.bFishingSession)
				++k.sFishing;
			else if (st.offlineShop.visiting)
				++k.sStall;
			else if (st.bVisitingDsAlchemist || st.bVisitingAlchemist)
				++k.sAlch;
		}
	}

	void LogPlayerBotPearlCensus()
	{
		TPlayerBotPearlCensus& k = s_kPlayerBotPearlCensus;
		const TPlayerBotPearlWorld& w = s_kPlayerBotPearlWorld;
		const TPlayerBotPearlStallCensus& st = s_kPlayerBotPearlStallCensus;
		const unsigned int minutes = std::max<unsigned int>(1, PLAYERBOT_PEARL_CENSUS_MS / PLAYERBOT_PEARL_SAMPLE_MS);
		sys_log(0, "PLAYERBOT_PEARL: census ch=%u port=%u world fishers=%d fishing=%d target=%d computed=%d share_pm=%d "
				"U=%lld.%03lld eligible=%d cores=%d open_clams=%d here designated=%u fishing=%u (bot-minutes / %u)",
				(unsigned int)g_bChannel, (unsigned int)p2p_port, w.fishers, w.fishing, w.target, w.computed, w.sharePm,
				w.unitsPm / 1000, w.unitsPm % 1000, w.eligible, w.cores, w.openClams ? 1 : 0, k.sFisherDesignated,
				k.sFisherFishing, minutes);
		for (int i = 0; i < PLAYERBOT_PEARL_KINDS; ++i)
			sys_log(0, "PLAYERBOT_PEARL: kind ch=%u port=%u %s vnum=%u demand=%lld supply=%lld listed=%lld short=%lld "
					"fair_ratio_pm=%d listed_lada_units=%u sold_units=%u sold_yang=%llu",
					(unsigned int)g_bChannel, (unsigned int)p2p_port, PLAYERBOT_PEARL_KIND_NAME[i],
					(unsigned int)PLAYERBOT_PEARL_KIND_VNUM[i], w.demand[i], w.supply[i], w.listed[i], w.shortage[i],
					w.ratioPm[i], st.listedUnits[i], st.soldUnits[i], st.soldYang[i]);
		sys_log(0, "PLAYERBOT_PEARL: produced ch=%u port=%u clams_caught=%u clams_opened=%u by_fishers=%u "
				"pearls=%u/%u/%u by_fishers=%u/%u/%u",
				(unsigned int)g_bChannel, (unsigned int)p2p_port, k.clamsCaught, k.clamsOpened, k.clamsOpenedFisher,
				k.pearls[0], k.pearls[1], k.pearls[2], k.pearlsFisher[0], k.pearlsFisher[1], k.pearlsFisher[2]);
		const unsigned int villagePm = k.samples ? (unsigned int)((unsigned long long)k.sVillage * 1000ULL / k.samples) : 0;
		sys_log(0, "PLAYERBOT_PEARL: village70 ch=%u port=%u on=%d level=%d bot_minutes=%u in_village=%u share_pm=%u "
				"fishing=%u stall=%u alchemist=%u trips stall=%u alchemist=%u fishing=%u services=%u other=%u "
				"alch_held=%u alch_batched=%u slip_held=%u renew_first=%u hunter_no_fish=%u",
				(unsigned int)g_bChannel, (unsigned int)p2p_port, GetPlayerBotPearlCfg().v70On ? 1 : 0,
				GetPlayerBotPearlCfg().v70Level, k.samples, k.sVillage, villagePm, k.sFishing, k.sStall, k.sAlch,
				k.trips[V70_TRIP_STALL], k.trips[V70_TRIP_ALCH], k.trips[V70_TRIP_FISH], k.trips[V70_TRIP_SERVICES],
				k.trips[V70_TRIP_OTHER], k.alchHeld, k.alchBatched, k.slipHeld, k.renewFirst, k.hunterNoFish);
		k = TPlayerBotPearlCensus();
		s_kPlayerBotPearlStallCensus = TPlayerBotPearlStallCensus();
	}

	// The core's clocks, from the bots' tick (ManagePlayerBotPearlBot).
	void ManagePlayerBotPearlCore(DWORD dwNow)
	{
		static DWORD s_dwNextPass = 0, s_dwNextSample = 0, s_dwNextCensus = 0;
		if (s_dwNextCensus == 0)
		{
			s_dwNextCensus = dwNow + PLAYERBOT_PEARL_CENSUS_MS;
			s_dwNextSample = dwNow + PLAYERBOT_PEARL_SAMPLE_MS;
			s_dwNextPass = dwNow + 90000;	// the board's first pass is a minute after the start
		}
		if ((int)(dwNow - s_dwNextPass) >= 0)
		{
			s_dwNextPass = dwNow + (DWORD)GetPlayerBotPearlCfg().passS * 1000U;
			RunPlayerBotPearlPass(dwNow);
		}
		if ((int)(dwNow - s_dwNextSample) >= 0)
		{
			s_dwNextSample = dwNow + PLAYERBOT_PEARL_SAMPLE_MS;
			SamplePlayerBotVillage70();
		}
		if ((int)(dwNow - s_dwNextCensus) >= 0)
		{
			s_dwNextCensus = dwNow + PLAYERBOT_PEARL_CENSUS_MS;
			LogPlayerBotPearlCensus();
		}
	}

	// The last map a bot of this core was seen on: an arrival in a first village batches the Alchemist's work.
	std::map<DWORD, long> s_mapPlayerBotPearlLastMap;

	// The bot's tick (playerbot_manager.cpp, beside the fish roast): the core's clocks, and a bot of 70+ arriving in a
	// first village has its Alchemist's look now, while it is there.
	void ManagePlayerBotPearlBot(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		ManagePlayerBotPearlCore(dwNow);
		if (!ch)
			return;
		const long map = ch->GetMapIndex();
		long& last = s_mapPlayerBotPearlLastMap[ch->GetPlayerID()];
		if (last == map)
			return;
		last = map;
		if (!IsPlayerBotM1Map(map) || !IsPlayerBotVillage70(ch) || state.bVisitingDsAlchemist)
			return;
		if (state.dwNextDsCheckTime > dwNow)
		{
			state.dwNextDsCheckTime = dwNow;
			++s_kPlayerBotPearlCensus.alchBatched;
		}
		if (state.dwNextAlchemistCheckTime > dwNow)
			state.dwNextAlchemistCheckTime = dwNow;
	}
}

#endif
