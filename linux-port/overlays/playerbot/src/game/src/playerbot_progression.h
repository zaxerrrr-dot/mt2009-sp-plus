#ifndef __INC_METIN2_PLAYERBOT_PROGRESSION_H__
#define __INC_METIN2_PLAYERBOT_PROGRESSION_H__

// MT2009_PLUS_PROGRESSION_V1: the engine's half of playerbot_progression_rules.h
// - the file the Seban panel writes, the checklist held against every ordinary
// bot, the push towards what it lacks, the fishing cap, and the status file
// the panel reads back ("kto stoi i dlaczego").
//
// The hold is the engine's AFFECT_EXP_BLOCK through ManagePlayerBotExpLock,
// the same lock a dropper and a Grinder at its tier carry: a bot may reach a
// gate's level and earns no experience there until the gate's requirements
// are met. Not for a player's companion (it follows its owner), a shouter, a
// dropper (its own lock), the operator's medal cohort, the Arezzo and Ochao
// test cohorts.
//
// So that the world never freezes on a requirement nobody can meet - an empty
// market, a map another core hosts - a bot that has stood timeoutMin minutes
// of play at one gate is let through, the gate written down as given up in
// its quest flags (playerbot.prog_waived) and logged.
//
// What a held bot does about it (the push), by requirement:
//   gear (weapon/armour/... level and plus) - its ambition becomes EQUIPMENT,
//     so the planner offers the blacksmith; REFINE's weight gate is open for
//     it; the equipment, weapon-goal and market passes do the buying as ever;
//   hp from items - EQUIPMENT as well, and a worn piece that can take a health
//     line (body, boots, bracelet, necklace) and has none is one the bonus pass
//     wants to change (PlayerBotWantsBonusChange);
//   skills - SKILLS; it buys the books of its own skills whatever its gear
//     (PlayerBotStudiesBooks) and SKILL's gate is open;
//   horse - HORSE; the medal hunt and the battle/military horse trials are
//     the stable's own (playerbot_battle_horse.h);
//   Metins - METINS, and a Metin expedition starts at once where the map has
//     stones;
//   Orc Teeth - BIOLOGIST; the Biologist's row already takes the bot to the
//     valley (GetPlayerBotFrontierMapForLevelRaw), BIOLOG's gate is open;
//   a quest flag, yang - nothing particular: the bot plays on and the timeout
//     answers it.
// While held with something missing it does not fish, dig or pick herbs
// unless the operator says so (fishWhenHeld, sideWhenHeld).
//
// MT2009_PLUS_PROGRESSION_V3: and it does not stand in a village. The fresh
// test world (2 October, 8.6 h, 2000 bots) held 831 bots at thirty-five, most
// of them in M1 on a Biologist herb row with 0-1 Metins and no horse. Now a
// held bot has a farm goal (GetPlayerBotProgressionFarmGoal): the Metins on
// the frontier of its level (the visit clock does not send it home, only its
// needs do), the medal in the Monkey Dungeon with no roll - by half-hour
// windows when it lacks both - or the gear (the push above). The herb rows
// wait for the gate, and the change of goal is logged ("PLAYERBOT_PROGRESSION:
// held bot farms ...").
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_shouters.h - it asks every cohort and the
// whole bag.

namespace
{
	BYTE GetPlayerBotStableAmbition(LPCHARACTER ch, BYTE personality);
	// MT2009_PLUS_BOT_PET_GATE_V1 (playerbot_pet_gate.h, included later): the element pet at the arrival, the credit
	// for one owned and not out, the arrival's age, the re-hold census
	void SummonPlayerBotPetOnArrival(LPCHARACTER ch, DWORD dwNow);
	int GetPlayerBotGatePendingPetResist(LPCHARACTER ch, int e, DWORD dwNow);
	DWORD GetPlayerBotArrivalAgeMs(LPCHARACTER ch, DWORD dwNow);
	bool IsPlayerBotGateToleranceOn(DWORD* pGraceMs, DWORD* pReholdMs);
	void NotePlayerBotGateRehold(bool waited);

	const char* const PLAYERBOT_PROGRESSION_PATH = "/opt/m2spool/playerbot_progression.tsv";
	const char* const PLAYERBOT_PROGRESSION_STATUS_PATH = "playerbot_progression_status.tsv";
	const char* const PLAYERBOT_PROGRESSION_FLAG_WAIVED = "playerbot.prog_waived";
	const char* const PLAYERBOT_PROGRESSION_FLAG_GATE = "playerbot.prog_gate";
	const char* const PLAYERBOT_PROGRESSION_FLAG_HELD = "playerbot.prog_held_s";
	// MT2009_PLUS_BOT_PET_GATE_V1: the gate last passed (or found met) and the minutes stood at it before the pass
	const char* const PLAYERBOT_PROGRESSION_FLAG_PASSED = "playerbot.prog_passed";
	const char* const PLAYERBOT_PROGRESSION_FLAG_PASSED_HELD = "playerbot.prog_passed_held_s";
	const DWORD PLAYERBOT_PROGRESSION_EVAL_MS = 15000;
	const DWORD PLAYERBOT_PROGRESSION_LOG_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_PROGRESSION_STATUS_MS = 30000;
	const DWORD PLAYERBOT_PROGRESSION_CENSUS_MS = 5000;

	time_t s_tPlayerBotProgressionMtime = 0;
	long s_lPlayerBotProgressionSize = -1;
	DWORD s_dwPlayerBotProgressionNextCheck = 0;
	bool s_bPlayerBotProgressionApplied = false;

	struct TPlayerBotProgress
	{
		DWORD dwSeen;
		DWORD dwLastTick;
		DWORD dwNextEval;
		DWORD dwNextLog;
		DWORD dwHeldMs;
		BYTE bLevel;
		BYTE bGate;
		BYTE bWaived;
		bool bLoaded;
		bool bEligible;
		bool bFishing;
		bool bHeld;
		bool bAmbition;
		BYTE bFarm; // MT2009_PLUS_PROGRESSION_V3: the farm goal last logged
		int iNeeds;
		std::string strWhy;
		std::string strName;
		// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1: the unmet rows of the gate held at (the first row of each piece, as the
		// weighing adjusted it - the horse's cap, the slot's best level) - what playerbot_progression_shop.h buys for
		std::vector<playerbot_progression::TReq> vecShort;
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: the level-55 gate's look at the last weighing (PLAYERBOT_GATE55_PATH_*) and
		// the fire resistance then
		BYTE bGate55Path;
		int iGate55Fire;
		// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1: where the weapon row's piece came from at the last weighing
		// (PLAYERBOT_PROG_WSRC_*) and, held for it, why (PLAYERBOT_PROG_WSHORT_*)
		BYTE bWeaponSrc;
		BYTE bWeaponShort;
		// MT2009_PLUS_BOT_GATE_TRIAL_V1: the gate trial (below)
		bool bTrial;			// a trial running
		BYTE bTrialGate;		// its gate
		DWORD dwTrialStart;		// get_dword_time() at the start
		DWORD dwTrialHuntMs;		// the minutes of hunting it has had (the trial's clock)
		long lTrialFromMap;		// the map it stood on at the start
		long lTrialLastHuntMap;		// the last hunting map it was seen on in the trial
		unsigned int uTrialKills, uTrialDeaths, uTrialRetreats;
		long long llTrialPvpDeaths;	// PLAYER_STATS_DEATH_FROM_PLAYER_FLAG at the last look (a player's kill is no test)
		long lTrialCooldownUntil;	// get_global_time(): no new trial before it (unless the bot grew)
		BYTE bTrialCooldownGate;
		unsigned int uTrialCount;	// trials at this gate (since the login)
		bool bTrialSig;			// the failed trial's look at the bot, for "it grew since"
		long long llSigPlus, llSigLevel, llSigSkills, llSigHp;
		int iSigFire;
		DWORD dwTrialLastEnd;
		// MT2009_PLUS_BOT_PET_GATE_V1: the gate passed (PLAYERBOT_PROGRESSION_FLAG_PASSED) and since when a weighing
		// finds it short again (0: met)
		BYTE bPassedGate;
		DWORD dwShortSince;
		TPlayerBotProgress() : dwSeen(0), dwLastTick(0), dwNextEval(0), dwNextLog(0), dwHeldMs(0),
			bLevel(0), bGate(0), bWaived(0), bLoaded(false), bEligible(false), bFishing(false),
			bHeld(false), bAmbition(false), bFarm(0), iNeeds(0), bGate55Path(0), iGate55Fire(0),
			bWeaponSrc(0), bWeaponShort(0), bTrial(false), bTrialGate(0), dwTrialStart(0), dwTrialHuntMs(0),
			lTrialFromMap(0), lTrialLastHuntMap(0), uTrialKills(0), uTrialDeaths(0), uTrialRetreats(0),
			llTrialPvpDeaths(-1), lTrialCooldownUntil(0), bTrialCooldownGate(0), uTrialCount(0), bTrialSig(false),
			llSigPlus(0), llSigLevel(0), llSigSkills(0), llSigHp(0), iSigFire(0), dwTrialLastEnd(0),
			bPassedGate(0), dwShortSince(0) {}
	};
	std::map<DWORD, TPlayerBotProgress> s_mapPlayerBotProgress;

	// MT2009_PLUS_BOT_GATE55_FIRE_V1 (the owner, 8 November 2026): the level-55 gate's helmet / armour / shield rows met
	// as written (+6) or by the alternative - fire resistance >= m2_bot_gate55_fire_min (50) with the three at
	// m2_bot_gate55_fire_plus (+4), the weapon and every other row unchanged (playerbot_progression_rules.h,
	// FireAltLook; the switches GetPlayerBotGate55Fire, playerbot_element_maps.h). A bot held there with the three short
	// of +6 aims at the cheaper path: its unmet rows (the progression shop's scrolls) are the pieces under +4 and the
	// fire row, and its element goal is fire at the minimum (GetPlayerBotGate55FireGoal -> GetPlayerBotElementMapGoal:
	// the element shop's target 52, not the progression's 40 + 2). The status file carries both ("... albo ogien 50%+
	// i zbroja/helm/tarcza +4 (ma ...)") and an "alt" line for the panel; PLAYERBOT_PROGRESS: gate55 passed_by=... is
	// logged (throttled) at every pass of a held bot; the progression shop's census counts the paths.
	enum { PLAYERBOT_GATE55_PATH_NONE = 0, PLAYERBOT_GATE55_PATH_PLUS6, PLAYERBOT_GATE55_PATH_FIRE,
		PLAYERBOT_GATE55_PATH_HELD_FIRE, PLAYERBOT_GATE55_PATH_HELD_GEAR, PLAYERBOT_GATE55_PATH_HELD_BOTH,
		PLAYERBOT_GATE55_PATH_HELD_OTHER, PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE };
	struct TPlayerBotGate55Stats
	{
		unsigned int passedFire, passedPlus6;	// held bots let through, by the path (the census period)
		unsigned long long passedFireMin, passedPlus6Min;
		TPlayerBotGate55Stats() : passedFire(0), passedPlus6(0), passedFireMin(0), passedPlus6Min(0) {}
	};
	TPlayerBotGate55Stats s_kPlayerBotGate55;

	// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1 (the owner, 8 November 2026: "jak botom moze brakowac broni jak maja bron mlodego
	// bohatera?"). The test world's census of 13:37 held 128 bots at 45 / 55 on the weapon row. The logs of 13:00-13:51
	// (both channels, 2090 "held at" lines) and the DB after the 13:51 stop answer why: of the 330 bots held there on
	// the weapon row in that hour, 238 wore a young heroes' weapon at the save and 92 held a TOOL in the hand - 85 a
	// fishing rod, 5 the herbalist's knife, 2 a pickaxe - each with a valid young heroes' weapon of its tier in the bag;
	// not one held a real weapon of its own choice. Of the 119 still held on the weapon row at the end of the hour,
	// 109 had last put a rod in the hand, 3 a pickaxe, 2 the knife, 1 had its young weapon run out (a real weapon of
	// 45+3 prepared: a true short), 4 a knife between picks. A rod, a pickaxe or the knife takes the weapon's cell, so
	// the morning's fix (a WORN young weapon is the one read) did not see it, and GetPlayerBotHandWeapon answered the
	// real weapon prepared in the bag ("bron lv30+7 (ma lv45+3)"): the bot flipped held / passed with every fishing
	// session and every herb pick (1076 "passed" lines in that hour), its exp lock on and off and its gate clock reset
	// at each pass. No class or level lacks a young weapon (jobs 0-7 all hold one), its +9 has no level limit (the
	// bot's own level, GetPlayerBotWeaponEffective) and none was under the row's level. Now, with a tool or nothing in
	// the hand, the weapon that goes back into it is read - the young heroes' weapon of the bag the equipment pass would
	// put on (FindPlayerBotMlodziHeld: valid, of its class and level) - before the prepared real weapon.
	// Event flag m2_bot_prog_mlodzi_tool_off 1: as before.
	enum { PLAYERBOT_PROG_WSRC_NONE = 0, PLAYERBOT_PROG_WSRC_MLODZI_WORN, PLAYERBOT_PROG_WSRC_MLODZI_BAG,
		PLAYERBOT_PROG_WSRC_REAL_HAND, PLAYERBOT_PROG_WSRC_REAL_BAG, PLAYERBOT_PROG_WSRC_COUNT };
	const char* const PLAYERBOT_PROG_WSRC_NAMES[PLAYERBOT_PROG_WSRC_COUNT] = { "none", "mlodzi_worn", "mlodzi_bag_tool",
		"real_hand", "real_bag" };
	enum { PLAYERBOT_PROG_WSHORT_MET = 0, PLAYERBOT_PROG_WSHORT_NONE, PLAYERBOT_PROG_WSHORT_LEVEL,
		PLAYERBOT_PROG_WSHORT_PLUS, PLAYERBOT_PROG_WSHORT_BOTH, PLAYERBOT_PROG_WSHORT_COUNT };

	// ======================================================================================================================
	// MT2009_PLUS_BOT_GATE_TRIAL_V1 (the owner, 8 November 2026: "bot idzie najpierw, probuje czy daje rade na danej mapie,
	// jesli nie, wraca i blokada nadal jest aktualna dopoki nie minie czas albo sie nie rozwinie"). Every gate, always:
	//   * a held bot (eligible as for the gates - no dropper, companion or cohort) held m2_bot_gate_trial_after_min (5)
	//     minutes gets a trial: its exp lock is lifted up to the gate's level + m2_bot_gate_trial_levels (1) - then
	//     locked again while the trial goes on - its farm goal (Metins, horse medals) gives way to its frontier, the
	//     ground its level draws, i.e. the next band's maps (at 35 Orc Valley opens at 36);
	//   * it is judged with the element progression's coping numbers (MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1), on any map:
	//     m2_bot_gate_trial_deaths (3) deaths to monsters or m2_bot_gate_trial_retreats (8) HP retreats in the trial fail it
	//     at once; after m2_bot_gate_trial_min (40) minutes of hunting (the trial's clock runs only on a hunting map, not
	//     in a village, with no rod / pickaxe / knife in the hand and no fishing) it passes with at least
	//     m2_bot_gate_trial_kills (25) kills a 30 minutes, else fails for slow kills; with no such clock in
	//     m2_bot_gate_trial_wall_x (3) times the trial's length it fails for no_hunt;
	//   * passed: the gate counts as passed (the "given up" flag playerbot.prog_waived takes it, as a timeout does, and
	//     playerbot.prog_trial_pass) and the bot goes on - "PLAYERBOT_PROGRESS: passed ... passed_by=trial";
	//   * failed: the exp lock is back, the gate holds on until its rows are met or its timeout (180 min) runs out - the
	//     timeout counts through the trial - and the map it failed on is marked hard for it for the cooldown
	//     (MarkPlayerBotSurviveHardMap - the survive step-down: the frontier draw answers the easier ground where the
	//     materials it lacks drop, "wraca na inna mape i zbiera materialy na rozwoj"). A new trial after
	//     m2_bot_gate_trial_cooldown (90) minutes, or - at least PLAYERBOT_GATE_TRIAL_MIN_GAP_MS after the last - as soon
	//     as the bot grew since the failure: more plus or item levels on its eight slots, more skill levels, 5+ fire
	//     resistance or 500+ HP from items.
	// The experience of a trial: up to the gate + 1 and no further (the levels flag; 0 keeps it locked at the gate and
	// tests survival only: m2_bot_gate_trial_survival_only 1). The +1 is the better of the two: a trial is the real hunt - the bot earns while it proves
	// itself, and passing loses it nothing; the one level stays well inside the gate's retro window (9), so a failed
	// trial leaves the bot held at the same gate, never past it, and no second trial adds more (the cap is the gate's,
	// not the trial's); and at 35 the +1 is what opens Orc Valley (36), the next band's ground the trial is about. A
	// lock kept at the gate would test the very ground the held bot already stands on, for nothing.
	// Event flags: m2_bot_gate_trial_off 1 - no trials (as before); _min (10-180), _cooldown (10-1440), _after_min (1-180),
	// _deaths (1-50), _retreats (1-100), _kills (1-1000, a 30 minutes), _levels (1-3), _survival_only 1, _wall_x (2-10). The log: "PLAYERBOT_PROGRESS: trial start / trial end", the census every 10 minutes
	// ("PLAYERBOT_PROGRESS: trial census gate=..." and "PLAYERBOT_PROGRESS: weapon_row gate=...").
	// ======================================================================================================================
	const DWORD PLAYERBOT_GATE_TRIAL_MIN_GAP_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_GATE_TRIAL_CENSUS_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD = "playerbot.prog_trial_cd";
	const char* const PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD_GATE = "playerbot.prog_trial_cdg";
	const char* const PLAYERBOT_PROGRESSION_FLAG_TRIAL_PASS = "playerbot.prog_trial_pass";

	struct TPlayerBotGateTrialCfg
	{
		bool on;
		int trialMin, cooldownMin, afterMin, deaths, retreats, kills, levels, wallX;
	};

	int ReadPlayerBotGateTrialFlag(const char* name, int def, int lo, int hi)
	{
		const int v = quest::CQuestManager::instance().GetEventFlag(name);
		return v >= lo && v <= hi ? v : def;
	}

	const TPlayerBotGateTrialCfg& GetPlayerBotGateTrialCfg()
	{
		static TPlayerBotGateTrialCfg s_kCfg;
		static DWORD s_dwAt = 0;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			s_kCfg.on = quest::CQuestManager::instance().GetEventFlag("m2_bot_gate_trial_off") == 0;
			s_kCfg.trialMin = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_min", 40, 10, 180);
			s_kCfg.cooldownMin = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_cooldown", 90, 10, 24 * 60);
			s_kCfg.afterMin = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_after_min", 5, 1, 180);
			s_kCfg.deaths = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_deaths", 3, 1, 50);
			s_kCfg.retreats = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_retreats", 8, 1, 100);
			s_kCfg.kills = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_kills", 25, 1, 1000);
			// m2_bot_gate_trial_levels 1-3 (default 1); m2_bot_gate_trial_survival_only 1 - 0 levels (locked at the gate)
			s_kCfg.levels = quest::CQuestManager::instance().GetEventFlag("m2_bot_gate_trial_survival_only") != 0 ? 0
					: ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_levels", 1, 1, 3);
			s_kCfg.wallX = ReadPlayerBotGateTrialFlag("m2_bot_gate_trial_wall_x", 3, 2, 10);
		}
		return s_kCfg;
	}

	enum { PLAYERBOT_GATE_TRIAL_END_PASSED = 0, PLAYERBOT_GATE_TRIAL_END_DEATHS, PLAYERBOT_GATE_TRIAL_END_RETREATS,
		PLAYERBOT_GATE_TRIAL_END_SLOW_KILLS, PLAYERBOT_GATE_TRIAL_END_NO_HUNT, PLAYERBOT_GATE_TRIAL_END_GATE_MET,
		PLAYERBOT_GATE_TRIAL_END_TIMEOUT, PLAYERBOT_GATE_TRIAL_END_OTHER, PLAYERBOT_GATE_TRIAL_END_COUNT };
	const char* const PLAYERBOT_GATE_TRIAL_END_NAMES[PLAYERBOT_GATE_TRIAL_END_COUNT] = { "passed", "deaths",
		"hp_retreats", "slow_kills", "no_hunt", "gate_met", "timeout", "released" };

	struct TPlayerBotGateTrialStats
	{
		unsigned int started, early, cooldownWaits;
		unsigned int ends[PLAYERBOT_GATE_TRIAL_END_COUNT];
		TPlayerBotGateTrialStats() : started(0), early(0), cooldownWaits(0) { memset(ends, 0, sizeof(ends)); }
	};
	std::map<BYTE, TPlayerBotGateTrialStats> s_mapPlayerBotGateTrialStats;	// per gate, the census period
	unsigned int s_uPlayerBotWeaponRowMlodziBag = 0;	// weighings whose weapon row a bag young weapon met (period)

	bool IsPlayerBotGate55Gate(const playerbot_progression::TGate& gate)
	{
		return gate.level == PLAYERBOT_GATE55_FIRE_LEVEL && GetPlayerBotGate55Fire();
	}

	int GetPlayerBotGate55FireGoal(LPCHARACTER ch)
	{
		int fireMin = 0;
		if (!ch || !GetPlayerBotGate55Fire(&fireMin))
			return 0;
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotProgress.end() || !it->second.bEligible)
			return 0;
		const BYTE path = it->second.bGate55Path;
		// MT2009_PLUS_BOT_PET_GATE_V1: or a bot that passed it waiting out a shortfall (rehold_wait) - the element shop
		// still builds (and calls the pet for) the fire it lacks
		const bool held = ((it->second.bHeld && it->second.bGate == PLAYERBOT_GATE55_FIRE_LEVEL) ||
					(!it->second.bHeld && it->second.dwShortSince != 0 &&
					 it->second.bPassedGate == PLAYERBOT_GATE55_FIRE_LEVEL)) &&
				(path == PLAYERBOT_GATE55_PATH_HELD_FIRE || path == PLAYERBOT_GATE55_PATH_HELD_GEAR ||
				 path == PLAYERBOT_GATE55_PATH_HELD_BOTH || path == PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE);
		return held || path == PLAYERBOT_GATE55_PATH_FIRE ? fireMin : 0;
	}

	// The fishing census by ten-level band (index level / 10).
	int s_aiPlayerBotProgressLive[26];
	int s_aiPlayerBotProgressAnglers[26];
	DWORD s_dwPlayerBotProgressNextCensus = 0;

	// The tables playerbot_persona reads - the Grinder's tiers and the law.
	void ApplyPlayerBotProgressionToPersona()
	{
		const playerbot_progression::TConfig& c = playerbot_progression::Config();
		for (unsigned int i = 0; i < playerbot_persona::GRINDER_TIER_COUNT && i < playerbot_progression::TIER_ROWS; ++i)
		{
			playerbot_persona::TGrinderTier& t = playerbot_persona::GRINDER_TIERS[i];
			const playerbot_progression::TTierRow& r = c.tiers[i];
			t.minLevel = r.bandFrom;
			t.maxLevel = r.bandTo;
			t.lockMin = r.lockFrom;
			t.lockMax = r.lockTo;
			playerbot_persona::GRINDER_TIER_HOLDS[i] = r.on;
		}
		playerbot_persona::GRINDER_TIER1_SKIP_PERCENT = (uint8_t)c.tier1SkipPct;
		playerbot_persona::AWANS_LAW_COUNT = std::min<unsigned int>(c.lawCount, playerbot_persona::AWANS_LAW_MAX);
		for (unsigned int i = 0; i < playerbot_persona::AWANS_LAW_COUNT; ++i)
		{
			playerbot_persona::AWANS_LAW[i].fromLevel = c.laws[i].fromLevel;
			playerbot_persona::AWANS_LAW[i].weapon = c.laws[i].weapon;
			playerbot_persona::AWANS_LAW[i].armour = c.laws[i].armour;
			playerbot_persona::AWANS_LAW[i].shield = c.laws[i].shield;
			playerbot_persona::AWANS_LAW[i].helmet = c.laws[i].helmet;
		}
		playerbot_persona::AWANS_LEVEL_WINDOW = (uint8_t)c.lawWindow;
		playerbot_persona::AWANS_PREMIUM_LEVEL_WINDOW = (uint8_t)c.lawPremiumWindow;
		s_bPlayerBotProgressionApplied = true;
	}

	void ReadPlayerBotProgressionFile(const char* path)
	{
		playerbot_progression::TConfig c = playerbot_progression::Defaults();
		playerbot_progression::TParseState st;
		FILE* fp = fopen(path, "r");
		if (fp)
		{
			char line[512];
			while (fgets(line, sizeof(line), fp))
				playerbot_progression::ParseLine(c, st, line);
			fclose(fp);
		}
		playerbot_progression::SortGates(c);
		playerbot_progression::Config() = c;
		ApplyPlayerBotProgressionToPersona();
		// Everybody is weighed again against the new table at once.
		for (std::map<DWORD, TPlayerBotProgress>::iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); ++it)
			it->second.dwNextEval = 0;
		sys_log(0, "PLAYERBOT_PROGRESS: table read from %s rows=%d checklist=%d gates=%u timeout_min=%u retro=%u fish_cap=%u%% laws=%u",
				path, st.rows, c.enabled ? 1 : 0, (unsigned)c.gates.size(), c.timeoutMin, c.retro,
				c.fishCapPct, c.lawCount);
	}

	void UpdatePlayerBotProgressCensus(DWORD dwNow)
	{
		if (dwNow < s_dwPlayerBotProgressNextCensus)
			return;
		s_dwPlayerBotProgressNextCensus = dwNow + PLAYERBOT_PROGRESSION_CENSUS_MS;
		memset(s_aiPlayerBotProgressLive, 0, sizeof(s_aiPlayerBotProgressLive));
		memset(s_aiPlayerBotProgressAnglers, 0, sizeof(s_aiPlayerBotProgressAnglers));
		for (std::map<DWORD, TPlayerBotProgress>::iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); )
		{
			// A bot gone for ten minutes is forgotten; its flags keep what matters.
			if (dwNow - it->second.dwSeen > 600000U)
			{
				s_mapPlayerBotProgress.erase(it++);
				continue;
			}
			if (dwNow - it->second.dwSeen <= 60000U)
			{
				const int band = std::min(25, (int)it->second.bLevel / 10);
				++s_aiPlayerBotProgressLive[band];
				if (it->second.bFishing)
					++s_aiPlayerBotProgressAnglers[band];
			}
			++it;
		}
	}

	void WritePlayerBotProgressionStatus(DWORD dwNow);
	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1: a gate passed or given up (playerbot_progression_shop.h, its census)
	void NotePlayerBotProgShopGateEnd(DWORD pid, BYTE gate, unsigned int heldMin, bool givenUp);
	// MT2009_PLUS_BOT_MOUNT_GATE_V1: the horse row met by a riding mount, and its result for the census
	// (playerbot_mount_gate.h)
	bool IsPlayerBotMountGateMet(LPCHARACTER ch);
	void NotePlayerBotMountGateRow(DWORD pid, BYTE how, DWORD dwNow);
	// MT2009_PLUS_BOT_GATE_TRIAL_V1: a failed trial's map marked hard (playerbot_survive.h, included later)
	bool MarkPlayerBotSurviveHardMap(LPCHARACTER ch, long map, int minutes);
	void ReportPlayerBotGateTrials(DWORD dwNow);

	// Once a manager tick: the file (a stat every five seconds), the census,
	// the status file.
	void RefreshPlayerBotProgression(DWORD dwNow)
	{
		if (!s_bPlayerBotProgressionApplied)
			ApplyPlayerBotProgressionToPersona();
		UpdatePlayerBotProgressCensus(dwNow);
		WritePlayerBotProgressionStatus(dwNow);
		ReportPlayerBotGateTrials(dwNow);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
		if (dwNow < s_dwPlayerBotProgressionNextCheck)
			return;
		s_dwPlayerBotProgressionNextCheck = dwNow + 5000;
		struct stat st;
		if (stat(PLAYERBOT_PROGRESSION_PATH, &st) != 0)
		{
			if (s_lPlayerBotProgressionSize >= 0)
			{
				sys_log(0, "PLAYERBOT_PROGRESS: %s is gone, built-in defaults", PLAYERBOT_PROGRESSION_PATH);
				s_tPlayerBotProgressionMtime = 0;
				s_lPlayerBotProgressionSize = -1;
				ReadPlayerBotProgressionFile(PLAYERBOT_PROGRESSION_PATH);
			}
			return;
		}
		if (st.st_mtime == s_tPlayerBotProgressionMtime && (long)st.st_size == s_lPlayerBotProgressionSize)
			return;
		s_tPlayerBotProgressionMtime = st.st_mtime;
		s_lPlayerBotProgressionSize = (long)st.st_size;
		ReadPlayerBotProgressionFile(PLAYERBOT_PROGRESSION_PATH);
	}

	// Who the checklist is for.
	bool IsPlayerBotProgressionEligible(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch)
			return false;
		const DWORD pid = ch->GetPlayerID();
		return !IsPlayerBotSidekickPID(pid) && !IsPlayerBotShouterPID(pid) &&
				!IsPlayerBotDropper(state.bPersonality) &&
				!CPlayerBotManager::instance().IsMedalDropperCohortPID(pid) &&
				!IsPlayerBotArezzoCohortPID(pid) && !IsPlayerBotArezzoBound(ch) &&
				!IsPlayerBotArezzoDungeonCohortPID(pid) && !IsPlayerBotOchaoForced(ch) &&
				!IsPlayerBotYoharaCohortPID(pid);	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
	}

	// The Orc Tooth row of the Biologist done with its teeth: in its key
	// phase or complete. A core that hosts no Orc stands it as met - it is a
	// requirement nobody here could ever fulfil.
	bool HasPlayerBotHandedOrcTeeth(LPCHARACTER ch)
	{
		for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i)
		{
			const TPlayerBotBiologistMission& m = PLAYERBOT_BIOLOGIST_MISSIONS[i];
			if (m.itemVnum != PLAYERBOT_ORC_TOOTH_VNUM)
				continue;
			if (!IsPlayerBotHuntingMobHosted(m.mobVnum))
				return true;
			return IsPlayerBotBiologistMissionComplete(ch, i) || IsPlayerBotBiologistKeyPhase(ch, i);
		}
		return true;
	}

	void MeasurePlayerBotProgress(LPCHARACTER ch, playerbot_progression::TSnapshot& s, BYTE* pWeaponSrc = NULL)
	{
		if (pWeaponSrc)
			*pWeaponSrc = PLAYERBOT_PROG_WSRC_NONE;
		s.level = (uint8_t)std::min<int>(255, ch->GetLevel());
		static const BYTE slots[playerbot_progression::SLOT_COUNT] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		for (int i = 0; i < playerbot_progression::SLOT_COUNT; ++i)
		{
			// The hand's weapon, not a rod or a pickaxe a session put there.
			LPITEM item = i == 0 ? GetPlayerBotHandWeapon(ch) : ch->GetWear(slots[i]);
			// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1: a young heroes' weapon WORN is the weapon the gate reads. With one in the
			// hand GetPlayerBotHandWeapon answers the real weapon prepared in the bag (MT2009_PLUS_BOT_MLODZI_V1, the
			// weapon planning's hand), so the +9 rule below (MT2009_PLUS_MLODZI_WEAPON_EFFECTIVE_V1, the owner, 28 October
			// 2026) never fired: on the test world of 8 November every bot held at 45 / 55 wore one (603 of 603 sampled)
			// and was held for "bron lv25+7 (ma lv45+2)" - the prepared weapon's plus. Event flag
			// m2_bot_prog_mlodzi_hand_off 1: as before.
			if (i == 0 && IsPlayerBotMlodziWeapon(ch->GetWear(WEAR_WEAPON)) &&
					quest::CQuestManager::instance().GetEventFlag("m2_bot_prog_mlodzi_hand_off") == 0)
				item = ch->GetWear(WEAR_WEAPON);
			// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1: a rod, a pickaxe, the knife or nothing in the hand - the young heroes'
			// weapon that goes back into it (above, by the census).
			if (i == 0)
			{
				LPITEM hand = ch->GetWear(WEAR_WEAPON);
				BYTE src = PLAYERBOT_PROG_WSRC_NONE;
				if (hand && hand->GetType() == ITEM_WEAPON)
					src = item == hand ? (IsPlayerBotMlodziWeapon(hand) ? PLAYERBOT_PROG_WSRC_MLODZI_WORN
							: PLAYERBOT_PROG_WSRC_REAL_HAND) : (item ? PLAYERBOT_PROG_WSRC_REAL_BAG : PLAYERBOT_PROG_WSRC_NONE);
				else
				{
					LPITEM back = quest::CQuestManager::instance().GetEventFlag("m2_bot_prog_mlodzi_tool_off") == 0
							? FindPlayerBotMlodziHeld(ch, NULL) : NULL;
					if (back)
					{
						item = back;
						src = PLAYERBOT_PROG_WSRC_MLODZI_BAG;
					}
					else if (item)
						src = PLAYERBOT_PROG_WSRC_REAL_BAG;
				}
				if (pWeaponSrc)
					*pWeaponSrc = src;
			}
			if (!item)
				continue;
			s.slot[i].present = true;
			// MT2009_PLUS_MLODZI_WEAPON_EFFECTIVE_V1 (the owner, 28 October 2026): a young heroes' weapon is a +9 weapon of the bot's own
			// level for the "weapon" and "all worn" rows (GetPlayerBotWeaponEffective).
			if (i == 0 && IsPlayerBotMlodziWeapon(item))
			{
				int l = 0, p = 0;
				GetPlayerBotWeaponEffective(ch, &l, &p, item);
				s.slot[i].level = (uint8_t)std::max(0, std::min(255, l));
				s.slot[i].plus = (uint8_t)std::max(0, std::min(255, p));
				continue;
			}
			s.slot[i].level = GetPlayerBotPersonaLevelLimit(item);
			s.slot[i].plus = (uint8_t)std::max(0, std::min(255, (int)item->GetRefineLevel()));
		}
		s.wantsShield = PlayerBotWantsShield(ch);
		long long hp = 0;
		for (int w = 0; w < WEAR_MAX_NUM; ++w)
		{
			LPITEM item = ch->GetWear((BYTE)w);
			if (!item)
				continue;
			for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
				if (item->GetAttributeType(a) == APPLY_MAX_HP && item->GetAttributeValue(a) > 0)
					hp += item->GetAttributeValue(a);
			const TItemTable* proto = item->GetProto();
			for (int a = 0; proto && a < ITEM_APPLY_MAX_NUM; ++a)
				if (proto->aApplies[a].bType == APPLY_MAX_HP && proto->aApplies[a].lValue > 0)
					hp += proto->aApplies[a].lValue;
		}
		s.hp = hp;
		s.skillCount = 0;
		if (ch->GetSkillGroup() != 0)
		{
			const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
			for (BYTE i = 0; i < build.bSkillCount && s.skillCount < 16; ++i)
				if (build.dwSkills[i] != 0)
					s.skills[s.skillCount++] = (uint8_t)std::max(0, std::min(255, ch->GetSkillLevel(build.dwSkills[i])));
		}
		s.horse = ch->GetHorseLevel();
#if defined(PLAYERBOT_ENGINE_MT2009)
		// The engine's own count (char_battle.cpp, AddPlayerStat on a stone's
		// death): kept with the character, in player_special_flag.
		s.metins = ch->GetSpecialFlag((DWORD)PLAYER_STATS_STONE_FLAG);
#else
		s.metins = 0;
#endif
		s.orcTeeth = HasPlayerBotHandedOrcTeeth(ch);
		s.gold = (long long)ch->GetGold();
		s.fire = GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_FIRE);	// MT2009_PLUS_BOT_GATE55_FIRE_V1
		// MT2009_PLUS_BOT_PET_GATE_V1: the bot's own fire pet not out yet (a login, a channel change) counts as out
		s.fire = std::min(PLAYERBOT_ELEMENT_MAP_RESIST_CAP,
				s.fire + GetPlayerBotGatePendingPetResist(ch, PLAYERBOT_EM_FIRE, get_dword_time()));
	}

	// The horse a gate asks for, as far as this core can give it: the battle
	// horse's trial is in the desert and the military one's in the Demon
	// Tower, and a core hosting neither holds a horse at the step below.
	long long GetPlayerBotProgressHorseCap(long long wanted)
	{
		if (wanted >= PLAYERBOT_MILITARY_HORSE_LEVEL && !IsPlayerBotHorseTrialOpenHere(PLAYERBOT_MAP_DEMON_TOWER))
			wanted = PLAYERBOT_MILITARY_HORSE_FROM_HORSE_LEVEL;
		if (wanted >= PLAYERBOT_BATTLE_HORSE_LEVEL && !IsPlayerBotHorseTrialOpenHere(PLAYERBOT_MAP_DESERT))
			wanted = PLAYERBOT_BATTLE_HORSE_FROM_HORSE_LEVEL;
		return wanted;
	}

	bool IsPlayerBotProgressionHeld(DWORD pid)
	{
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(pid);
		return it != s_mapPlayerBotProgress.end() && it->second.bHeld && it->second.bEligible;
	}

	// MT2009_PLUS_BOT_GATE_TRIAL_V1: the exp lock's question (ManagePlayerBotExpLock) - held, and not in a gate trial
	// under its level cap (the gate + m2_bot_gate_trial_levels).
	bool IsPlayerBotProgressionExpHeld(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotProgress.end() || !it->second.bHeld || !it->second.bEligible)
			return false;
		const TPlayerBotProgress& e = it->second;
		if (!e.bTrial)
			return true;
		return (int)ch->GetLevel() >= (int)e.bTrialGate + GetPlayerBotGateTrialCfg().levels;
	}

	bool IsPlayerBotGateTrialRunning(DWORD pid)
	{
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(pid);
		return it != s_mapPlayerBotProgress.end() && it->second.bHeld && it->second.bTrial;
	}

	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1: the held bot's record (NULL: not held) - its gate, minutes and unmet rows.
	const TPlayerBotProgress* FindPlayerBotHeldProgress(DWORD pid)
	{
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(pid);
		return it != s_mapPlayerBotProgress.end() && it->second.bHeld && it->second.bEligible ? &it->second : NULL;
	}

	int GetPlayerBotProgressionNeeds(DWORD pid)
	{
		std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.find(pid);
		return it != s_mapPlayerBotProgress.end() && it->second.bHeld && it->second.bEligible
				? it->second.iNeeds : 0;
	}

	// The weight gates (IsPlayerBotWeightGateOpen): open for what a held bot
	// lacks, closed for the veins and the board while it lacks anything.
	bool PlayerBotProgressionWeightGate(DWORD pid, BYTE weight, bool& open)
	{
		const int needs = GetPlayerBotProgressionNeeds(pid);
		if (needs == 0)
			return false;
		switch (weight)
		{
			case PLAYERBOT_WEIGHT_REFINE:
				if (needs & (playerbot_progression::NEED_GEAR | playerbot_progression::NEED_HP)) { open = true; return true; }
				return false;
			case PLAYERBOT_WEIGHT_SKILL:
				if (needs & playerbot_progression::NEED_SKILLS) { open = true; return true; }
				return false;
			case PLAYERBOT_WEIGHT_BIOLOG:
				if (needs & playerbot_progression::NEED_ORC_TEETH) { open = true; return true; }
				return false;
			case PLAYERBOT_WEIGHT_HORSE:
				if (needs & playerbot_progression::NEED_HORSE) { open = true; return true; }
				return false;
			case PLAYERBOT_WEIGHT_METIN:
				if (needs & playerbot_progression::NEED_METINS) { open = true; return true; }
				return false;
			case PLAYERBOT_WEIGHT_MINING:
			case PLAYERBOT_WEIGHT_HERB:
				if (!playerbot_progression::Config().sideWhenHeld) { open = false; return true; }
				return false;
			default:
				return false;
		}
	}

	// Whether this bot may start for the water (IsPlayerBotAngler): not while
	// held with something missing (unless the operator allows it), and not
	// once its ten-level band has its share at the water. A bot already at
	// the water or on its way is counted and goes on.
	bool PlayerBotProgressionBlocksFishing(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.bFishingSession ||
				(state.persona.dwRybakTripUntil != 0 && dwNow < state.persona.dwRybakTripUntil))
			return false;
		const playerbot_progression::TConfig& c = playerbot_progression::Config();
		if (!c.fishWhenHeld && GetPlayerBotProgressionNeeds(ch->GetPlayerID()) != 0)
			return true;
		// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: nor while its young heroes' weapon is running out (playerbot_mlodzi_bots.h).
		if (PlayerBotMlodziBlocksLeisure(ch->GetPlayerID()))
			return true;
		if (c.fishCapPct >= 100)
			return false;
		const int band = std::min(25, (int)ch->GetLevel() / 10);
		const int live = s_aiPlayerBotProgressLive[band];
		if (live <= 0)
			return false;
		const int cap = (int)((long long)live * (long long)c.fishCapPct / 100LL);
		if (s_aiPlayerBotProgressAnglers[band] < std::max(c.fishCapPct > 0 ? 1 : 0, cap))
			return false;
		PlayerBotLogThrottledEvery("progress_fish_cap", dwNow, 600000,
				"PLAYERBOT_PROGRESS: fishing cap pid=%u name=%s level=%u band=%d anglers=%d live=%d cap_pct=%u",
				ch->GetPlayerID(), ch->GetName(), (unsigned)ch->GetLevel(), band * 10,
				s_aiPlayerBotProgressAnglers[band], live, c.fishCapPct);
		return true;
	}

	BYTE GetPlayerBotProgressAmbition(int needs)
	{
		if (needs & playerbot_progression::NEED_HORSE)
			return BOT_AMBITION_HORSE;
		if (needs & playerbot_progression::NEED_ORC_TEETH)
			return BOT_AMBITION_BIOLOGIST;
		if (needs & playerbot_progression::NEED_METINS)
			return BOT_AMBITION_METINS;
		if (needs & playerbot_progression::NEED_SKILLS)
			return BOT_AMBITION_SKILLS;
		if (needs & (playerbot_progression::NEED_GEAR | playerbot_progression::NEED_HP))
			return BOT_AMBITION_EQUIPMENT;
		return 0xFF;
	}

	// MT2009_PLUS_PROGRESSION_V3: what a held bot works on. The horse when a
	// medal would raise it and a Monkey Dungeon takes the bot; the Metins; and
	// both by half-hour windows spread by pid, so the stones are not left for
	// the whole of a horse's ladder. The gear when nothing else is missing -
	// the refine and the market passes do that work wherever it stands.
	const DWORD PLAYERBOT_PROGRESS_FARM_WINDOW_MS = 30 * 60 * 1000;

	BYTE GetPlayerBotProgressionFarmGoal(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return PLAYERBOT_PROGRESS_FARM_NONE;
		const int needs = GetPlayerBotProgressionNeeds(ch->GetPlayerID());
		if (needs == 0)
			return PLAYERBOT_PROGRESS_FARM_NONE;
		// MT2009_PLUS_BOT_GATE_TRIAL_V1: in a trial the bot hunts the ground its level draws, not a farm's
		if (IsPlayerBotGateTrialRunning(ch->GetPlayerID()))
			return PLAYERBOT_PROGRESS_FARM_NONE;
		// MT2009_PLUS_HORSE30_V1: the Monkey Dungeon only while the next paid
		// training lacks medals - with them in the bag it is the yang and the
		// materials it lacks, which the Metin window and the ordinary hunting
		// bring (the Dozorca and the counters the materials).
		const bool horse = (needs & playerbot_progression::NEED_HORSE) != 0 &&
				CanPlayerBotAdvanceHorse(ch) && GetPlayerBotMonkeyMapFor(ch) != 0 &&
				(int)ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) <
					GetPlayerBotHorseTrainingMedals(ch, 1);
		const bool metins = (needs & playerbot_progression::NEED_METINS) != 0;
		if (horse && metins)
			return ((dwNow / PLAYERBOT_PROGRESS_FARM_WINDOW_MS + ch->GetPlayerID()) & 1U) != 0
					? PLAYERBOT_PROGRESS_FARM_METINS : PLAYERBOT_PROGRESS_FARM_HORSE;
		if (horse)
			return PLAYERBOT_PROGRESS_FARM_HORSE;
		if (metins)
			return PLAYERBOT_PROGRESS_FARM_METINS;
		if (needs & (playerbot_progression::NEED_GEAR | playerbot_progression::NEED_HP))
			return PLAYERBOT_PROGRESS_FARM_GEAR;
		return PLAYERBOT_PROGRESS_FARM_NONE;
	}

	const char* GetPlayerBotProgressionFarmName(BYTE farm)
	{
		switch (farm)
		{
			case PLAYERBOT_PROGRESS_FARM_METINS: return "metins";
			case PLAYERBOT_PROGRESS_FARM_HORSE: return "horse_medals";
			case PLAYERBOT_PROGRESS_FARM_GEAR: return "gear";
			default: return "nothing";
		}
	}

	// ---------------------------------------------------------------- MT2009_PLUS_BOT_GATE_TRIAL_V1

	// A death, an HP retreat or a kill of a bot in a trial (the element progression's hooks, playerbot_element_maps.h).
	// A kill counts for the party members in a trial near the killer too (an assisting member lands few last hits).
	void NotePlayerBotGateTrialOne(LPCHARACTER ch, int kind)
	{
		if (!ch || s_mapPlayerBotProgress.empty())
			return;
		std::map<DWORD, TPlayerBotProgress>::iterator it = s_mapPlayerBotProgress.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotProgress.end() || !it->second.bTrial || !it->second.bHeld)
			return;
		TPlayerBotProgress& e = it->second;
		switch (kind)
		{
			case PLAYERBOT_GATE_TRIAL_EV_KILL:
				++e.uTrialKills;
				break;
			case PLAYERBOT_GATE_TRIAL_EV_DEATH:
			{
				// a player's kill (a war, a duel, the arena) is no test of the ground
				TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
				if (st != s_mapPlayerBotAIStates.end() && st->second.dwGuildWarEnemyGID != 0)
					return;
#if defined(PLAYERBOT_ENGINE_MT2009)
				const long long pvp = ch->GetSpecialFlag((DWORD)PLAYER_STATS_DEATH_FROM_PLAYER_FLAG);
				const bool byPlayer = e.llTrialPvpDeaths >= 0 && pvp > e.llTrialPvpDeaths;
				e.llTrialPvpDeaths = pvp;
				if (byPlayer)
					return;
#endif
				++e.uTrialDeaths;
				break;
			}
			case PLAYERBOT_GATE_TRIAL_EV_RETREAT:
				++e.uTrialRetreats;
				break;
		}
	}

	struct FPlayerBotGateTrialPartyKill
	{
		LPCHARACTER m_pKiller;
		explicit FPlayerBotGateTrialPartyKill(LPCHARACTER killer) : m_pKiller(killer) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member == m_pKiller || member->GetMapIndex() != m_pKiller->GetMapIndex() ||
					DISTANCE_APPROX(member->GetX() - m_pKiller->GetX(), member->GetY() - m_pKiller->GetY()) >
						PLAYERBOT_EPROG_PARTY_KILL_RANGE)
				return;
			NotePlayerBotGateTrialOne(member, PLAYERBOT_GATE_TRIAL_EV_KILL);
		}
	};

	void NotePlayerBotGateTrialEvent(LPCHARACTER ch, int kind, DWORD now)
	{
		(void)now;
		if (!ch || !ch->IsPC() || s_mapPlayerBotProgress.empty())
			return;
		NotePlayerBotGateTrialOne(ch, kind);
		if (kind == PLAYERBOT_GATE_TRIAL_EV_KILL && ch->GetParty())
		{
			FPlayerBotGateTrialPartyKill f(ch);
			ch->GetParty()->ForEachOnMapMember(f, ch->GetMapIndex());
		}
	}

	// The trial's clock runs while the bot hunts: on a map outside the villages, alive, no tool in the hand, not fishing.
	bool IsPlayerBotGateTrialHunting(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->IsDead() || state.bFishingSession || IsPlayerBotVillageMap(ch->GetMapIndex()))
			return false;
		LPITEM hand = ch->GetWear(WEAR_WEAPON);
		return !hand || hand->GetType() == ITEM_WEAPON;
	}

	// The bot's growth since a failed trial: the eight slots' plus and levels, the skills, fire, the HP from items.
	void SignPlayerBotGateTrial(const playerbot_progression::TSnapshot& snap, long long& plus, long long& level,
			long long& skills, long long& hp, int& fire)
	{
		plus = level = skills = 0;
		for (int i = 0; i < playerbot_progression::SLOT_COUNT; ++i)
			if (snap.slot[i].present)
			{
				plus += snap.slot[i].plus;
				level += snap.slot[i].level;
			}
		for (int i = 0; i < snap.skillCount && i < 16; ++i)
			skills += snap.skills[i];
		hp = snap.hp;
		fire = snap.fire;
	}

	const char* PlayerBotGateTrialGrewWhy(const TPlayerBotProgress& e, const playerbot_progression::TSnapshot& snap)
	{
		if (!e.bTrialSig)
			return NULL;
		long long plus = 0, level = 0, skills = 0, hp = 0;
		int fire = 0;
		SignPlayerBotGateTrial(snap, plus, level, skills, hp, fire);
		if (plus > e.llSigPlus)
			return "plus";
		if (level > e.llSigLevel)
			return "item_level";
		if (skills > e.llSigSkills)
			return "skills";
		if (fire >= e.iSigFire + 5)
			return "fire";
		if (hp >= e.llSigHp + 500)
			return "hp";
		return NULL;
	}

	void EndPlayerBotGateTrial(LPCHARACTER ch, TPlayerBotProgress& e, int why, const playerbot_progression::TSnapshot* snap,
			DWORD dwNow)
	{
		if (!e.bTrial)
			return;
		const TPlayerBotGateTrialCfg& cfg = GetPlayerBotGateTrialCfg();
		const BYTE gate = e.bTrialGate;
		if (why >= 0 && why < PLAYERBOT_GATE_TRIAL_END_COUNT)
			++s_mapPlayerBotGateTrialStats[gate].ends[why];
		const bool failed = why == PLAYERBOT_GATE_TRIAL_END_DEATHS || why == PLAYERBOT_GATE_TRIAL_END_RETREATS ||
				why == PLAYERBOT_GATE_TRIAL_END_SLOW_KILLS || why == PLAYERBOT_GATE_TRIAL_END_NO_HUNT;
		long hardMap = 0;
		bool stepped = false;
		if (failed && ch)
		{
			e.lTrialCooldownUntil = (long)get_global_time() + (long)cfg.cooldownMin * 60L;
			e.bTrialCooldownGate = gate;
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD, (int)e.lTrialCooldownUntil);
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD_GATE, gate);
			if (snap)
			{
				SignPlayerBotGateTrial(*snap, e.llSigPlus, e.llSigLevel, e.llSigSkills, e.llSigHp, e.iSigFire);
				e.bTrialSig = true;
			}
			// back to easier ground for the cooldown: the map it failed on (the one it stands on, else the last it hunted)
			hardMap = IsPlayerBotVillageMap(ch->GetMapIndex()) ? e.lTrialLastHuntMap : ch->GetMapIndex();
			stepped = MarkPlayerBotSurviveHardMap(ch, hardMap, cfg.cooldownMin);
		}
		sys_log(0, "PLAYERBOT_PROGRESS: trial end pid=%u name=%s level=%u gate=%u result=%s hunt_min=%u wall_min=%u "
				"kills=%u deaths=%u hp_retreats=%u from_map=%ld map=%ld held_min=%u%s%s cooldown_min=%d step_down=%ld trial_no=%u",
				ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "-", ch ? (unsigned)ch->GetLevel() : 0U, (unsigned)gate,
				why >= 0 && why < PLAYERBOT_GATE_TRIAL_END_COUNT ? PLAYERBOT_GATE_TRIAL_END_NAMES[why] : "?",
				e.dwTrialHuntMs / 60000U, (dwNow - e.dwTrialStart) / 60000U, e.uTrialKills, e.uTrialDeaths, e.uTrialRetreats,
				e.lTrialFromMap, ch ? ch->GetMapIndex() : 0L, e.dwHeldMs / 60000U, failed ? " failed=1" : "",
				why == PLAYERBOT_GATE_TRIAL_END_PASSED ? " passed_by=trial" : "", failed ? cfg.cooldownMin : 0,
				stepped ? hardMap : 0L, e.uTrialCount);
		e.bTrial = false;
		e.dwTrialLastEnd = dwNow ? dwNow : 1;
		e.dwNextEval = 0;	// the exp lock and the farm goal at once
	}

	// The trial's turn at a weighing of a held bot (holdGate its gate): true when the trial passed the gate (the caller
	// releases the bot and returns).
	bool ManagePlayerBotGateTrial(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotProgress& e, BYTE holdGate,
			const playerbot_progression::TSnapshot& snap, DWORD dwNow)
	{
		const TPlayerBotGateTrialCfg& cfg = GetPlayerBotGateTrialCfg();
		if (e.bTrial && (!cfg.on || e.bTrialGate != holdGate))
		{
			EndPlayerBotGateTrial(ch, e, PLAYERBOT_GATE_TRIAL_END_OTHER, NULL, dwNow);
			return false;
		}
		if (!cfg.on)
			return false;
		const DWORD trialMs = (DWORD)cfg.trialMin * 60000U;
		if (e.bTrial)
		{
			if (!IsPlayerBotVillageMap(ch->GetMapIndex()))
				e.lTrialLastHuntMap = ch->GetMapIndex();
			int why = -1;
			if ((int)e.uTrialDeaths >= cfg.deaths)
				why = PLAYERBOT_GATE_TRIAL_END_DEATHS;
			else if ((int)e.uTrialRetreats >= cfg.retreats)
				why = PLAYERBOT_GATE_TRIAL_END_RETREATS;
			else if (e.dwTrialHuntMs >= trialMs)
			{
				// the kill rate: cfg.kills a 30 minutes of the trial's clock
				const unsigned long long need = (unsigned long long)cfg.kills * (unsigned long long)(e.dwTrialHuntMs / 60000U) / 30ULL;
				why = (unsigned long long)e.uTrialKills >= need ? PLAYERBOT_GATE_TRIAL_END_PASSED : PLAYERBOT_GATE_TRIAL_END_SLOW_KILLS;
			}
			else if (dwNow - e.dwTrialStart >= trialMs * (DWORD)cfg.wallX)
				why = PLAYERBOT_GATE_TRIAL_END_NO_HUNT;
			if (why < 0)
				return false;
			EndPlayerBotGateTrial(ch, e, why, &snap, dwNow);
			if (why != PLAYERBOT_GATE_TRIAL_END_PASSED)
				return false;
			e.bWaived = holdGate;
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_WAIVED, holdGate);
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_TRIAL_PASS, holdGate);
			return true;
		}
		// a new trial?
		if (e.dwHeldMs < (DWORD)cfg.afterMin * 60000U)
			return false;
		const char* grew = NULL;
		if (e.lTrialCooldownUntil != 0 && e.bTrialCooldownGate == holdGate && (long)get_global_time() < e.lTrialCooldownUntil)
		{
			grew = e.dwTrialLastEnd == 0 || dwNow - e.dwTrialLastEnd >= PLAYERBOT_GATE_TRIAL_MIN_GAP_MS
					? PlayerBotGateTrialGrewWhy(e, snap) : NULL;
			if (!grew)
			{
				++s_mapPlayerBotGateTrialStats[holdGate].cooldownWaits;
				return false;
			}
			++s_mapPlayerBotGateTrialStats[holdGate].early;
		}
		e.bTrial = true;
		e.bTrialGate = holdGate;
		e.dwTrialStart = dwNow ? dwNow : 1;
		e.dwTrialHuntMs = 0;
		e.lTrialFromMap = ch->GetMapIndex();
		e.lTrialLastHuntMap = IsPlayerBotVillageMap(ch->GetMapIndex()) ? 0 : ch->GetMapIndex();
		e.uTrialKills = e.uTrialDeaths = e.uTrialRetreats = 0;
#if defined(PLAYERBOT_ENGINE_MT2009)
		e.llTrialPvpDeaths = ch->GetSpecialFlag((DWORD)PLAYER_STATS_DEATH_FROM_PLAYER_FLAG);
#endif
		++e.uTrialCount;
		++s_mapPlayerBotGateTrialStats[holdGate].started;
		// the farm goal gives way to the frontier at once
		if (e.bFarm != PLAYERBOT_PROGRESS_FARM_NONE && e.bAmbition)
			state.bAmbition = GetPlayerBotStableAmbition(ch, state.bPersonality);
		sys_log(0, "PLAYERBOT_PROGRESS: trial start pid=%u name=%s level=%u gate=%u held_min=%u map=%ld frontier=%ld "
				"trial_min=%d level_cap=%d trial_no=%u%s%s missing: %s",
				ch->GetPlayerID(), ch->GetName(), (unsigned)ch->GetLevel(), (unsigned)holdGate, e.dwHeldMs / 60000U,
				ch->GetMapIndex(), GetPlayerBotFrontierMapForLevel(ch), cfg.trialMin, (int)holdGate + cfg.levels,
				e.uTrialCount, grew ? " early_retry=" : "", grew ? grew : "", e.strWhy.c_str());
		return false;
	}

	// The census: per gate the trials of the period and the held bots now - in a trial, waiting out a cooldown - and the
	// weapon row's reasons of the bots held on it.
	void ReportPlayerBotGateTrials(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		if (s_dwNext == 0)
			s_dwNext = dwNow + PLAYERBOT_GATE_TRIAL_CENSUS_MS;
		if ((int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_GATE_TRIAL_CENSUS_MS;
		struct TNow
		{
			unsigned int held, running, cooldown, wshort;
			unsigned int wrow[PLAYERBOT_PROG_WSHORT_COUNT], wsrc[PLAYERBOT_PROG_WSRC_COUNT];
			TNow() : held(0), running(0), cooldown(0), wshort(0) { memset(wrow, 0, sizeof(wrow)); memset(wsrc, 0, sizeof(wsrc)); }
		};
		std::map<BYTE, TNow> now;
		const long gnow = (long)get_global_time();
		for (std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); ++it)
		{
			const TPlayerBotProgress& e = it->second;
			if (dwNow - e.dwSeen > 60000U || !e.bHeld || !e.bEligible)
				continue;
			TNow& n = now[e.bGate];
			++n.held;
			if (e.bTrial)
				++n.running;
			else if (e.lTrialCooldownUntil != 0 && e.bTrialCooldownGate == e.bGate && gnow < e.lTrialCooldownUntil)
				++n.cooldown;
			if (e.bWeaponShort != PLAYERBOT_PROG_WSHORT_MET && e.bWeaponShort < PLAYERBOT_PROG_WSHORT_COUNT)
			{
				++n.wshort;
				++n.wrow[e.bWeaponShort];
				if (e.bWeaponSrc < PLAYERBOT_PROG_WSRC_COUNT)
					++n.wsrc[e.bWeaponSrc];
			}
		}
		std::set<BYTE> gates;
		for (std::map<BYTE, TNow>::const_iterator it = now.begin(); it != now.end(); ++it)
			gates.insert(it->first);
		for (std::map<BYTE, TPlayerBotGateTrialStats>::const_iterator it = s_mapPlayerBotGateTrialStats.begin();
				it != s_mapPlayerBotGateTrialStats.end(); ++it)
			gates.insert(it->first);
		const TPlayerBotGateTrialCfg& cfg = GetPlayerBotGateTrialCfg();
		for (std::set<BYTE>::const_iterator g = gates.begin(); g != gates.end(); ++g)
		{
			const TNow& n = now[*g];
			const TPlayerBotGateTrialStats& t = s_mapPlayerBotGateTrialStats[*g];
			sys_log(0, "PLAYERBOT_PROGRESS: trial census gate=%u on=%d held=%u running=%u cooldown=%u | period: started=%u "
					"early_retry=%u passed_by_trial=%u failed_deaths=%u failed_hp_retreats=%u failed_slow_kills=%u "
					"failed_no_hunt=%u ended_gate_met=%u ended_timeout=%u ended_other=%u cooldown_waits=%u | trial_min=%d "
					"cooldown_min=%d after_min=%d deaths=%d retreats=%d kills30=%d levels=%d wall_x=%d",
					(unsigned)*g, cfg.on ? 1 : 0, n.held, n.running, n.cooldown, t.started, t.early,
					t.ends[PLAYERBOT_GATE_TRIAL_END_PASSED], t.ends[PLAYERBOT_GATE_TRIAL_END_DEATHS],
					t.ends[PLAYERBOT_GATE_TRIAL_END_RETREATS], t.ends[PLAYERBOT_GATE_TRIAL_END_SLOW_KILLS],
					t.ends[PLAYERBOT_GATE_TRIAL_END_NO_HUNT], t.ends[PLAYERBOT_GATE_TRIAL_END_GATE_MET],
					t.ends[PLAYERBOT_GATE_TRIAL_END_TIMEOUT], t.ends[PLAYERBOT_GATE_TRIAL_END_OTHER], t.cooldownWaits,
					cfg.trialMin, cfg.cooldownMin, cfg.afterMin, cfg.deaths, cfg.retreats, cfg.kills, cfg.levels, cfg.wallX);
			if (n.held != 0)
				sys_log(0, "PLAYERBOT_PROGRESS: weapon_row gate=%u held=%u short=%u no_weapon=%u level=%u plus=%u level_plus=%u "
						"| src mlodzi_worn=%u mlodzi_bag_tool=%u real_hand=%u real_bag=%u none=%u | period met_by_mlodzi_bag=%u",
						(unsigned)*g, n.held, n.wshort, n.wrow[PLAYERBOT_PROG_WSHORT_NONE], n.wrow[PLAYERBOT_PROG_WSHORT_LEVEL],
						n.wrow[PLAYERBOT_PROG_WSHORT_PLUS], n.wrow[PLAYERBOT_PROG_WSHORT_BOTH],
						n.wsrc[PLAYERBOT_PROG_WSRC_MLODZI_WORN], n.wsrc[PLAYERBOT_PROG_WSRC_MLODZI_BAG],
						n.wsrc[PLAYERBOT_PROG_WSRC_REAL_HAND], n.wsrc[PLAYERBOT_PROG_WSRC_REAL_BAG],
						n.wsrc[PLAYERBOT_PROG_WSRC_NONE], s_uPlayerBotWeaponRowMlodziBag);
		}
		s_mapPlayerBotGateTrialStats.clear();
		s_uPlayerBotWeaponRowMlodziBag = 0;
	}

	// MT2009_PLUS_BOT_PET_GATE_V1: the gate written down as passed (kept over logins), the minutes stood at it kept for a
	// re-hold
	void MarkPlayerBotGatePassed(LPCHARACTER ch, TPlayerBotProgress& e, BYTE gate, DWORD heldS)
	{
		e.dwShortSince = 0;
		if (!ch || gate == 0)
			return;
		if (e.bPassedGate != gate)
		{
			e.bPassedGate = gate;
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED, gate);
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED_HELD, (int)heldS);
		}
		else if (heldS > 0)
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED_HELD, (int)heldS);
	}

	void ReleasePlayerBotProgress(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotProgress& e)
	{
		e.bHeld = false;
		e.bTrial = false;	// MT2009_PLUS_BOT_GATE_TRIAL_V1 (ended by the caller)
		e.iNeeds = 0;
		e.strWhy.clear();
		e.vecShort.clear();	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
		e.dwHeldMs = 0;
		e.bGate = 0;
		e.bFarm = PLAYERBOT_PROGRESS_FARM_NONE;
		if (e.bAmbition && ch)
			state.bAmbition = GetPlayerBotStableAmbition(ch, state.bPersonality);
		e.bAmbition = false;
		if (ch)
		{
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_GATE, 0);
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_HELD, 0);
		}
	}

	// Every tick, before ManagePlayerBotExpLock: cheap but for the weighing,
	// which runs every PLAYERBOT_PROGRESSION_EVAL_MS and on a level change.
	void ManagePlayerBotProgression(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotProgress& e = s_mapPlayerBotProgress[pid];
		const DWORD dt = e.dwLastTick != 0 ? dwNow - e.dwLastTick : 0;
		e.dwLastTick = dwNow;
		e.dwSeen = dwNow;
		if (e.strName.empty())
			e.strName = ch->GetName();
		const BYTE level = (BYTE)std::min<int>(255, ch->GetLevel());
		if (level != e.bLevel)
			e.dwNextEval = 0;
		e.bLevel = level;
		e.bFishing = state.bFishingSession ||
				(state.persona.dwRybakTripUntil != 0 && dwNow < state.persona.dwRybakTripUntil);
		const playerbot_progression::TConfig& c = playerbot_progression::Config();
		e.bEligible = IsPlayerBotProgressionEligible(ch, state);
		if (!e.bEligible || !c.enabled || c.gates.empty() ||
				(IsPlayerBotPersonaEnabled() && !state.persona.bRestored))
		{
			if (e.bHeld)
			{
				sys_log(0, "PLAYERBOT_PROGRESS: released pid=%u name=%s level=%u gate=%u why=%s",
						pid, ch->GetName(), (unsigned)level, (unsigned)e.bGate,
						!e.bEligible ? "not_eligible" : "checklist_off");
				EndPlayerBotGateTrial(ch, e, PLAYERBOT_GATE_TRIAL_END_OTHER, NULL, dwNow);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
				ReleasePlayerBotProgress(ch, state, e);
			}
			return;
		}
		// Play time at the gate; a long gap is a logout, not play.
		if (e.bHeld && dt < 60000U)
			e.dwHeldMs += dt;
		// MT2009_PLUS_BOT_GATE_TRIAL_V1: the trial's clock - its hunting time
		if (e.bTrial && e.bHeld && dt < 60000U && IsPlayerBotGateTrialHunting(ch, state))
			e.dwTrialHuntMs += dt;
		if (e.dwNextEval != 0 && dwNow < e.dwNextEval)
			return;
		// MT2009_PLUS_BOT_PET_GATE_V1: never weighed on a bag not loaded yet (a login's first ticks)
		if (!ch->IsItemLoaded())
			return;
		e.dwNextEval = dwNow + PLAYERBOT_PROGRESSION_EVAL_MS + pid % 3000U;
		if (!e.bLoaded)
		{
			e.bLoaded = true;
			e.bWaived = (BYTE)std::max(0, std::min(255, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_WAIVED)));
			// MT2009_PLUS_BOT_GATE_TRIAL_V1: a failed trial's cooldown outlives a logout
			e.lTrialCooldownUntil = (long)ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD);
			e.bTrialCooldownGate = (BYTE)std::max(0, std::min(255, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_TRIAL_CD_GATE)));
			// MT2009_PLUS_BOT_PET_GATE_V1: a gate passed in an earlier session (or on another core)
			e.bPassedGate = (BYTE)std::max(0, std::min(255, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED)));
		}
		// MT2009_PLUS_BOT_PET_GATE_V1: the element pet out before the snapshot, at the arrival (playerbot_pet_gate.h)
		SummonPlayerBotPetOnArrival(ch, dwNow);

		playerbot_progression::TSnapshot snap;
		BYTE weaponSrc = PLAYERBOT_PROG_WSRC_NONE;	// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1
		MeasurePlayerBotProgress(ch, snap, &weaponSrc);
		e.bWeaponSrc = weaponSrc;
		e.bWeaponShort = PLAYERBOT_PROG_WSHORT_MET;
		bool weaponRowMet = false;
		BYTE holdGate = 0;
		int needs = 0;
		std::string why;
		std::vector<playerbot_progression::TReq> shortReqs;	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
		BYTE gate55Path = PLAYERBOT_GATE55_PATH_NONE;	// MT2009_PLUS_BOT_GATE55_FIRE_V1
		BYTE topGate = 0;	// MT2009_PLUS_BOT_PET_GATE_V1: the highest gate weighed (all met: the gate passed)
		for (size_t g = 0; g < c.gates.size() && holdGate == 0; ++g)
		{
			const playerbot_progression::TGate& gate = c.gates[g];
			if (gate.level > level || (unsigned)level > (unsigned)gate.level + c.retro || gate.level <= e.bWaived)
				continue;
			topGate = std::max(topGate, gate.level);
			// MT2009_PLUS_BOT_GATE55_FIRE_V1: the rows as weighed (below), then the level-55 alternative's look at them
			std::vector<playerbot_progression::TReq> rows;
			rows.reserve(gate.reqs.size());
			for (size_t r = 0; r < gate.reqs.size(); ++r)
			{
				playerbot_progression::TReq req = gate.reqs[r];
				if (req.on)
				{
					if (req.type == playerbot_progression::REQ_HORSE)
						req.a = GetPlayerBotProgressHorseCap(req.a);
					// MT2009_PLUS_BOT_LAW_NO_BETTER_V1: a gate never asks for a piece
					// of a higher level than the game has for the bot's slot at its
					// level - the best there is counts.
					if (req.type >= playerbot_progression::REQ_WEAPON && req.type <= playerbot_progression::REQ_EARRINGS &&
							req.a > 0 && IsPlayerBotLawNoBetterOn())
					{
						static const int s_aiCell[] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS,
							WEAR_WRIST, WEAR_NECK, WEAR_EAR };
						const int best = GetPlayerBotBestSlotLevelInGame(ch, s_aiCell[req.type - playerbot_progression::REQ_WEAPON]);
						if (best >= 0 && req.a > best)
							req.a = best;
					}
				}
				rows.push_back(req);
			}
			playerbot_progression::TFireAltLook alt;
			if (IsPlayerBotGate55Gate(gate))
			{
				int fireMin = 0, firePlus = 0;
				bool anyLevel = true;	// MT2009_PLUS_BOT_GATE55_FIRE_ANYLEVEL_V1
				GetPlayerBotGate55Fire(&fireMin, &firePlus, &anyLevel);
				alt = playerbot_progression::FireAltLook(rows, snap, fireMin, firePlus, anyLevel);
			}
			bool groupShort = false;	// a helmet / armour / shield row short of its plus as written
			std::string groupWhy;
			int groupNeeds = 0;
			std::vector<playerbot_progression::TReq> groupShortReqs;
			const BYTE holdBefore = holdGate;
			for (size_t r = 0; r < gate.reqs.size(); ++r)
			{
				playerbot_progression::TReq req = rows[r];
				if (!req.on)
					continue;
				const bool group = alt.applies && playerbot_progression::IsFireAltPiece(req.type);
				long long flagValue = 0;
				if (req.type == playerbot_progression::REQ_QUEST_FLAG)
					flagValue = ch->GetQuestFlag(req.flag);
				std::string one;
				if (playerbot_progression::Meets(req, snap, flagValue, one))
				{
					if (req.type == playerbot_progression::REQ_HORSE)
						NotePlayerBotMountGateRow(pid, 1, dwNow);	// MT2009_PLUS_BOT_MOUNT_GATE_V1: met by the horse
					if (req.type == playerbot_progression::REQ_WEAPON)
						weaponRowMet = true;
					continue;
				}
				// MT2009_PLUS_PROGRESSION_V2: one of the piece's other rows.
				if (playerbot_progression::MeetsAlternative(gate, r, snap))
				{
					if (req.type == playerbot_progression::REQ_WEAPON)
						weaponRowMet = true;
					continue;
				}
				// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1: why the weapon row holds (the census)
				if (req.type == playerbot_progression::REQ_WEAPON && playerbot_progression::IsFirstOfPiece(gate, r))
				{
					const playerbot_progression::TPiece& wp = snap.slot[0];
					const bool lv = (long long)wp.level < req.a, pl = (int)wp.plus < req.b;
					e.bWeaponShort = !wp.present ? PLAYERBOT_PROG_WSHORT_NONE : lv && pl ? PLAYERBOT_PROG_WSHORT_BOTH
							: lv ? PLAYERBOT_PROG_WSHORT_LEVEL : PLAYERBOT_PROG_WSHORT_PLUS;
				}
				// MT2009_PLUS_BOT_MOUNT_GATE_V1 (the owner, 8 November 2026): a bot with a riding mount (an ItemShop mount
				// worn or in the bag, permanent or with m2_bot_mountgate_min_days left - not the starter Appaloosa) needs no
				// horse for the row (playerbot_mount_gate.h; m2_bot_mountgate_off 1: as before)
				if (req.type == playerbot_progression::REQ_HORSE)
				{
					if (IsPlayerBotMountGateMet(ch))
					{
						NotePlayerBotMountGateRow(pid, 2, dwNow);
						continue;
					}
					NotePlayerBotMountGateRow(pid, 3, dwNow);
				}
				// MT2009_PLUS_BOT_GATE55_FIRE_V1: a helmet / armour / shield row short is weighed with the alternative
				// after the rows
				if (group)
				{
					groupShort = true;
					if (!playerbot_progression::IsFirstOfPiece(gate, r))
						continue;
					groupNeeds |= playerbot_progression::NeedOf(req.type);
					groupShortReqs.push_back(req);
					if (!groupWhy.empty())
						groupWhy += ", ";
					groupWhy += one;
					continue;
				}
				holdGate = gate.level;
				if (!playerbot_progression::IsFirstOfPiece(gate, r))
					continue;
				needs |= playerbot_progression::NeedOf(req.type);
				shortReqs.push_back(req);	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
				if (!why.empty())
					why += ", ";
				why += one;
			}
			// MT2009_PLUS_BOT_GATE55_FIRE_V1: the three pieces short of +6 - met by the alternative, else held for them with
			// the alternative's rows as the bot's work (the cheaper path: the pieces to +4 and the fire)
			if (alt.applies)
			{
				if (groupShort && !alt.Met())
				{
					holdGate = gate.level;
					needs |= groupNeeds | playerbot_progression::NEED_GEAR;
					for (size_t i = 0; i < alt.shortRows.size(); ++i)
						shortReqs.push_back(alt.shortRows[i]);
					if (!why.empty())
						why += ", ";
					why += groupWhy;
					why += ", ";
					why += alt.why;
				}
				const bool heldHere = holdGate == gate.level && holdBefore == 0;
				if (!heldHere)
					gate55Path = groupShort ? PLAYERBOT_GATE55_PATH_FIRE : PLAYERBOT_GATE55_PATH_PLUS6;
				else if (!groupShort)
					gate55Path = PLAYERBOT_GATE55_PATH_HELD_OTHER;
				else if (alt.Met())
					gate55Path = PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE;	// the three met by the fire, held by another row
				else if (!alt.fireMet && !alt.gearMet)
					gate55Path = PLAYERBOT_GATE55_PATH_HELD_BOTH;
				else
					gate55Path = !alt.fireMet ? PLAYERBOT_GATE55_PATH_HELD_FIRE : PLAYERBOT_GATE55_PATH_HELD_GEAR;
			}
		}
		e.bGate55Path = gate55Path;
		e.iGate55Fire = snap.fire;
		if (weaponRowMet && weaponSrc == PLAYERBOT_PROG_WSRC_MLODZI_BAG)
			++s_uPlayerBotWeaponRowMlodziBag;	// MT2009_PLUS_BOT_PROG_MLODZI_TOOL_V1

		if (holdGate == 0)
		{
			// MT2009_PLUS_BOT_PET_GATE_V1: met - the shortfall's clock off, the gate written down as passed
			e.dwShortSince = 0;
			if (e.bHeld && e.bGate != 0)
				MarkPlayerBotGatePassed(ch, e, e.bGate, e.dwHeldMs / 1000U);
			else if (topGate != 0 && topGate > e.bPassedGate)
				MarkPlayerBotGatePassed(ch, e, topGate, 0);
			if (e.bHeld)
			{
				EndPlayerBotGateTrial(ch, e, PLAYERBOT_GATE_TRIAL_END_GATE_MET, &snap, dwNow);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
				sys_log(0, "PLAYERBOT_PROGRESS: passed pid=%u name=%s level=%u gate=%u held_min=%u passed_by=requirements weapon_src=%s",
						pid, ch->GetName(), (unsigned)level, (unsigned)e.bGate, e.dwHeldMs / 60000U,
						PLAYERBOT_PROG_WSRC_NAMES[weaponSrc < PLAYERBOT_PROG_WSRC_COUNT ? weaponSrc : 0]);
				// MT2009_PLUS_BOT_GATE55_FIRE_V1: the level-55 gate's path
				if (e.bGate == PLAYERBOT_GATE55_FIRE_LEVEL &&
						(gate55Path == PLAYERBOT_GATE55_PATH_FIRE || gate55Path == PLAYERBOT_GATE55_PATH_PLUS6))
				{
					const bool byFire = gate55Path == PLAYERBOT_GATE55_PATH_FIRE;
					const unsigned int heldMin = e.dwHeldMs / 60000U;
					++(byFire ? s_kPlayerBotGate55.passedFire : s_kPlayerBotGate55.passedPlus6);
					(byFire ? s_kPlayerBotGate55.passedFireMin : s_kPlayerBotGate55.passedPlus6Min) += heldMin;
					PlayerBotLogThrottled("gate55_pass", dwNow,
							"PLAYERBOT_PROGRESS: gate55 passed_by=%s pid=%u name=%s level=%u held_min=%u fire=%d "
							"armour=+%u helmet=+%u shield=%s+%u weapon=lv%u+%u",
							byFire ? "fire" : "plus6", pid, ch->GetName(), (unsigned)level, heldMin, snap.fire,
							(unsigned)snap.slot[1].plus, (unsigned)snap.slot[2].plus, snap.wantsShield ? "" : "(none)",
							(unsigned)snap.slot[3].plus, (unsigned)snap.slot[0].level, (unsigned)snap.slot[0].plus);
				}
				NotePlayerBotProgShopGateEnd(pid, e.bGate, e.dwHeldMs / 60000U, false);	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
				ReleasePlayerBotProgress(ch, state, e);
			}
			return;
		}

		// MT2009_PLUS_BOT_PET_GATE_V1: a gate the bot passed is not held again on a passing shortfall - the element pet
		// not called yet after a login or a channel change, a piece off for its rerolls, the hand's weapon swapped:
		// not within the arrival's grace, nor before the shortfall has lasted m2_bot_gate_rehold_s
		DWORD graceMs = 0, reholdMs = 0;
		const bool rehold = !e.bHeld && holdGate == e.bPassedGate && IsPlayerBotGateToleranceOn(&graceMs, &reholdMs);
		if (rehold)
		{
			if (e.dwShortSince == 0)
				e.dwShortSince = dwNow ? dwNow : 1;
			const DWORD shortMs = dwNow - e.dwShortSince;
			const DWORD arrivalMs = GetPlayerBotArrivalAgeMs(ch, dwNow);
			if (arrivalMs < graceMs || shortMs < reholdMs)
			{
				NotePlayerBotGateRehold(true);
				PlayerBotLogThrottled("prog_rehold_wait", dwNow,
						"PLAYERBOT_PROGRESS: rehold_wait pid=%u name=%s level=%u gate=%u why=%s arrival_s=%u short_s=%u fire=%d "
						"missing: %s", pid, ch->GetName(), (unsigned)level, (unsigned)holdGate,
						arrivalMs < graceMs ? "arrival" : "debounce", arrivalMs / 1000U, shortMs / 1000U, snap.fire, why.c_str());
				return;
			}
			NotePlayerBotGateRehold(false);
			sys_log(0, "PLAYERBOT_PROGRESS: rehold pid=%u name=%s level=%u gate=%u short_s=%u held_min_kept=%d fire=%d missing: %s",
					pid, ch->GetName(), (unsigned)level, (unsigned)holdGate, shortMs / 1000U,
					std::max(0, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED_HELD)) / 60, snap.fire, why.c_str());
		}
		if (e.bGate != holdGate)
		{
			// Back at the same gate after a login: the minutes already stood.
			const int savedGate = ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_GATE);
			e.dwHeldMs = savedGate == (int)holdGate
					? (DWORD)std::max(0, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_HELD)) * 1000U : 0U;
			// MT2009_PLUS_BOT_PET_GATE_V1: held again at the gate it passed - the minutes stood before the pass, not 0
			if (savedGate != (int)holdGate && holdGate == e.bPassedGate)
				e.dwHeldMs = (DWORD)std::max(0, ch->GetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_PASSED_HELD)) * 1000U;
			e.bGate = holdGate;
			e.dwNextLog = 0;
		}
		if (e.dwHeldMs >= c.timeoutMin * 60000U)
		{
			sys_log(0, "PLAYERBOT_PROGRESS: gate given up pid=%u name=%s level=%u gate=%u held_min=%u missing=%s",
					pid, ch->GetName(), (unsigned)level, (unsigned)holdGate, e.dwHeldMs / 60000U, why.c_str());
			NotePlayerBotProgShopGateEnd(pid, holdGate, e.dwHeldMs / 60000U, true);	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
			EndPlayerBotGateTrial(ch, e, PLAYERBOT_GATE_TRIAL_END_TIMEOUT, &snap, dwNow);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
			e.bWaived = holdGate;
			ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_WAIVED, holdGate);
			ReleasePlayerBotProgress(ch, state, e);
			e.dwNextEval = 0;
			return;
		}
		const bool fresh = !e.bHeld;
		e.bHeld = true;
		e.iNeeds = needs;
		e.strWhy = why;
		e.vecShort.swap(shortReqs);	// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1
		ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_GATE, holdGate);
		ch->SetQuestFlag(PLAYERBOT_PROGRESSION_FLAG_HELD, (int)(e.dwHeldMs / 1000U));
		if (fresh || dwNow >= e.dwNextLog)
		{
			e.dwNextLog = dwNow + PLAYERBOT_PROGRESSION_LOG_MS;
			sys_log(0, "PLAYERBOT_PROGRESS: held at %u pid=%u name=%s level=%u held_min=%u missing: %s",
					(unsigned)holdGate, pid, ch->GetName(), (unsigned)level, e.dwHeldMs / 60000U, why.c_str());
		}

		// MT2009_PLUS_BOT_GATE_TRIAL_V1: the trial - started, judged, passed
		if (ManagePlayerBotGateTrial(ch, state, e, holdGate, snap, dwNow))
		{
			MarkPlayerBotGatePassed(ch, e, holdGate, e.dwHeldMs / 1000U);	// MT2009_PLUS_BOT_PET_GATE_V1
			sys_log(0, "PLAYERBOT_PROGRESS: passed pid=%u name=%s level=%u gate=%u held_min=%u passed_by=trial missing: %s",
					pid, ch->GetName(), (unsigned)level, (unsigned)holdGate, e.dwHeldMs / 60000U, why.c_str());
			NotePlayerBotProgShopGateEnd(pid, holdGate, e.dwHeldMs / 60000U, false);
			ReleasePlayerBotProgress(ch, state, e);
			e.dwNextEval = 0;
			return;
		}

		// The push.
		// MT2009_PLUS_PROGRESSION_V3: the farm goal names the ambition while it
		// is the Metins or the horse, so the two take turns by its windows.
		const BYTE farm = GetPlayerBotProgressionFarmGoal(ch, dwNow);
		BYTE ambition = GetPlayerBotProgressAmbition(needs);
		if (farm == PLAYERBOT_PROGRESS_FARM_METINS)
			ambition = BOT_AMBITION_METINS;
		else if (farm == PLAYERBOT_PROGRESS_FARM_HORSE)
			ambition = BOT_AMBITION_HORSE;
		if (ambition != 0xFF && state.bAmbition != ambition)
		{
			state.bAmbition = ambition;
			e.bAmbition = true;
		}
		if (farm != e.bFarm)
		{
			e.bFarm = farm;
			const long frontier = GetPlayerBotFrontierMapForLevel(ch);
			sys_log(0, "PLAYERBOT_PROGRESSION: held bot farms %s pid=%u name=%s level=%u gate=%u map=%ld goal_map=%ld metins=%lld horse=%d missing: %s",
					GetPlayerBotProgressionFarmName(farm), pid, ch->GetName(), (unsigned)level,
					(unsigned)holdGate, ch->GetMapIndex(),
					farm == PLAYERBOT_PROGRESS_FARM_HORSE ? GetPlayerBotMonkeyMapFor(ch) : frontier,
					snap.metins, (int)ch->GetHorseLevel(), why.c_str());
		}
		// MT2009_PLUS_PROGRESSION_V3: the expedition starts on a map whose stones
		// are of the bot's level - not in a first village, whose stones a bot of
		// thirty-five has outgrown (IsPlayerBotMetinWorthFighting); from there
		// ShouldPlayerBotLeaveForFrontier sends it out first. The Orc Teeth
		// still go first, as before.
		if (farm == PLAYERBOT_PROGRESS_FARM_METINS && state.dwMetinExpeditionUntil == 0 &&
				!(needs & playerbot_progression::NEED_ORC_TEETH) &&
				PlayerBotMapHasMetinStones(ch->GetMapIndex()) && !IsPlayerBotVillageMap(ch->GetMapIndex()))
		{
			state.dwMetinExpeditionUntil = dwNow + PLAYERBOT_METIN_EXPEDITION_DURATION;
			state.dwHubChosenTime = 0;
			sys_log(0, "PLAYERBOT_METIN: expedition start pid=%u name=%s level=%u map=%ld minutes=%u why=progression",
					pid, ch->GetName(), (unsigned)level, ch->GetMapIndex(), PLAYERBOT_METIN_EXPEDITION_DURATION / 60000);
		}
	}

	// The panel's "kto stoi i dlaczego": counts per gate and per requirement,
	// the fishing census and the longest-held bots, every half minute.
	void WritePlayerBotProgressionStatus(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		if (dwNow < s_dwNext)
			return;
		s_dwNext = dwNow + PLAYERBOT_PROGRESSION_STATUS_MS;
		const playerbot_progression::TConfig& c = playerbot_progression::Config();
		std::map<int, int> perGate;
		std::map<std::pair<int, std::string>, int> perReq;
		std::vector<std::pair<DWORD, DWORD> > held;  // held ms, pid
		int eligible = 0, heldCount = 0, waived = 0;
		int paths[PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE + 1] = { 0 };	// MT2009_PLUS_BOT_GATE55_FIRE_V1
		for (std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); ++it)
		{
			const TPlayerBotProgress& e = it->second;
			if (dwNow - e.dwSeen > 60000U)
				continue;
			if (e.bEligible)
				++eligible;
			if (e.bEligible && e.bGate55Path <= PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE)
				++paths[e.bGate55Path];
			if (e.bWaived != 0)
				++waived;
			if (!e.bHeld || !e.bEligible)
				continue;
			++heldCount;
			++perGate[e.bGate];
			// The requirement words up to the first space and digit run, so
			// "bron lv25+7 (ma lv20+5)" counts as "bron".
			size_t start = 0;
			while (start < e.strWhy.size())
			{
				size_t end = e.strWhy.find(", ", start);
				if (end == std::string::npos)
					end = e.strWhy.size();
				std::string part = e.strWhy.substr(start, end - start);
				const size_t paren = part.find(" (");
				if (paren != std::string::npos)
					part = part.substr(0, paren);
				++perReq[std::make_pair((int)e.bGate, part)];
				start = end + 2;
			}
			held.push_back(std::make_pair(e.dwHeldMs, it->first));
		}
		std::sort(held.rbegin(), held.rend());
		const char* tmp = "playerbot_progression_status.tsv.tmp";
		FILE* fp = fopen(tmp, "wb");
		if (!fp)
			return;
		fprintf(fp, "# MT2009_PLUS_PROGRESSION_V1 status, written %ld\n", (long)time(0));
		fprintf(fp, "summary\t%d\t%d\t%d\t%d\t%u\t%u\n", eligible, heldCount, waived,
				c.enabled ? 1 : 0, c.timeoutMin, c.fishCapPct);
		for (std::map<int, int>::const_iterator it = perGate.begin(); it != perGate.end(); ++it)
			fprintf(fp, "gate\t%d\t%d\n", it->first, it->second);
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: alt <gate> <on> <fire min> <plus> <bots past it by +6> <by fire> <held: fire
		// short> <+4 short> <both> <another row, the three by +6> <another row, the three by fire>
		{
			int fireMin = 0, firePlus = 0;
			const bool on = GetPlayerBotGate55Fire(&fireMin, &firePlus);
			fprintf(fp, "alt\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", PLAYERBOT_GATE55_FIRE_LEVEL, on ? 1 : 0, fireMin,
					firePlus, paths[PLAYERBOT_GATE55_PATH_PLUS6], paths[PLAYERBOT_GATE55_PATH_FIRE],
					paths[PLAYERBOT_GATE55_PATH_HELD_FIRE], paths[PLAYERBOT_GATE55_PATH_HELD_GEAR],
					paths[PLAYERBOT_GATE55_PATH_HELD_BOTH], paths[PLAYERBOT_GATE55_PATH_HELD_OTHER],
					paths[PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE]);
		}
		for (std::map<std::pair<int, std::string>, int>::const_iterator it = perReq.begin(); it != perReq.end(); ++it)
			fprintf(fp, "req\t%d\t%s\t%d\n", it->first.first, it->first.second.c_str(), it->second);
		for (int band = 0; band < 26; ++band)
			if (s_aiPlayerBotProgressLive[band] > 0)
				fprintf(fp, "fish\t%d\t%d\t%d\n", band * 10, s_aiPlayerBotProgressLive[band], s_aiPlayerBotProgressAnglers[band]);
		for (size_t i = 0; i < held.size() && i < 300; ++i)
		{
			const TPlayerBotProgress& e = s_mapPlayerBotProgress[held[i].second];
			std::string why = e.strWhy;
			std::replace(why.begin(), why.end(), '\t', ' ');
			fprintf(fp, "bot\t%u\t%s\t%u\t%u\t%u\t%s\n", held[i].second, e.strName.c_str(),
					(unsigned)e.bLevel, (unsigned)e.bGate, held[i].first / 60000U, why.c_str());
		}
		fclose(fp);
		rename(tmp, PLAYERBOT_PROGRESSION_STATUS_PATH);
	}
}

#endif
