#ifndef __INC_METIN2_PLAYERBOT_ZODIAC_RUNS_H__
#define __INC_METIN2_PLAYERBOT_ZODIAC_RUNS_H__

// MT2009_PLUS_ZODIAC_RUNS_V1 - the bots' own runs of the Swiatynia Zodiaku
// (MT2009_PLUS_ZODIAC_V1, Autor: Digi Rasta; server-patches/zodiak/README.md).
//
// The owner, 8 October: the temple tested tonight, "put bots in there with
// good test gear and teach them to clear every Zodiac". A run, end to end:
//
//   - the call (the operator's file, below; "loop on" calls the next sign
//     whenever no run is under way): ZRUN_SIZE free bots of one kingdom of
//     ZRUN_MIN_LEVEL or more on this core (free: the dungeon finder's
//     GetPlayerBotLfgRefusal, and on no other run), a Shaman with a skill
//     group first when one is free, the highest level the leader;
//   - the gathering: each is put at the portal of its sign on 358 (the
//     portal's cell from data/dungeon/zodiac/days/7-sunday.txt), the leader
//     makes the party there (a bot party is made after the warps, which would
//     break it), and the test's supplies are handed out: red and blue potions,
//     ZRUN_PRISMS Prisms (33025) for the revives, and the "good test gear" -
//     three hidden affects for the run (597 max HP %, 598 strong against
//     monsters %, 599 defence), ZRUN_BOOST each (0: none). The Anima Spheres
//     are the operator's (a test run pays none);
//   - the way in: what the portal's dialog does for a party leader -
//     CZodiacManager::StartTemple(leader, sign), which jumps the party from 358
//     onto the temple's first floor (through WarpBot: the party is kept);
//   - inside, the leader goes for the floor's objective: a Metin (2900-2908)
//     first, else the nearest monster or boss, else a statue (20452-20463: a
//     blow can raise a Metin; the floors that want Metins have them) - never
//     the cannon; the others fight round the leader as a person's party bots
//     fight round the person (FightPlayerBotPartyDungeon). A floor done (the
//     temple's "next floor" state), the leader asks for the next one as the
//     button does ("/jumpfloor": the floor the time earned); at ZRUN_FLOOR the
//     run ends itself (the temple's exit). A dead bot stands up with its
//     prisms (playerbot_zodiac_bots.h);
//   - the way out: the temple's exit (time up, the end, the run's own), or
//     ZRUN_STALL_MS without a new floor; then each goes back to where it
//     stood before the call, the party goes, the test's affects and leftover
//     prisms go.
//
// The operator's file "playerbot_zodiac_test" in the core's directory, read
// every 5 s and renamed to .done:
//     now <sign 1-12|any> [n]   a run of that sign now (n: bots, default size)
//     loop on|off               a run after a run, the twelve signs in turn
//     size <n> | level <n> | floor <n> | boost <pct> | prisms <n> | gap <s>
//     allportals 1|0            every portal every day (event flag
//                               zodiac_all_portals, spawned again now)
//     abort                     every run out now
//     status                    ZODIAC_RUN status and one line per sign
// The settings are kept in event flags (zrun_*), so a restart keeps them.
//
// The log: ZODIAC_RUN lines in syslog (called, gathered, entered, floor,
// next, finished, stalled, out, home, status) and one row a run in
// playerbot_zodiac_runs.tsv: unix time, run, sign, portal, instance, kingdom,
// members, lowest and highest level, result, highest floor, seconds, each
// floor's seconds ("floor:s,..."), deaths, prism revives, free revives, the
// leader and the names.
//
// MT2009_PLUS_ZODIAC_RUNS_V7 - the owner, 23 October: "bots must do the Zodiac
// on their own like players". Two kinds of run now: the operator's test run
// above (now/loop: the boost, the prisms and the potions handed out, nothing
// paid) and the bots' own run ("own"), called on a clock:
//
//   - the call (PlanOwnZrun, every ZRUN_OWN_PLAN_MS with the bots' dungeon
//     runs switched on - IsPlayerBotDgRunOn: the panel's "Dungeony botow" and
//     the file playerbot_dungeon_runs_off - and the event flag zrun_own not
//     -1): a sign whose portal stands on 358 today (the day's
//     data/dungeon/zodiac/days/* file, CZodiacManager::Spawn - the portal NPC
//     20438+sign is there or not), the least run first; a kingdom with
//     ZRUN_OWN_MIN free bots that want to go (the dungeon runs' refusal, rest,
//     share by personality and the kingdom's shout gap) and that are ready -
//     GetZrunReadyFloor: the bot's level, held to its real power (its
//     strength + 5, MT2009_PLUS_ZODIAC_STRENGTH_V2), against the floors' monster
//     levels (MobLevels/OfficerLevels): floor 6 at 45 ... floor 39 at 110 - and
//     hold the entry, 12 Anima Spheres (player.bead: 36 to begin with, one an
//     hour up to 36 - BeadTime, the login's count, asked once an hour a bot -
//     or a Pergamin Sfer 72329/72327 used, +30; or the Znak Straznika's
//     affect). The run's floor is the lowest ready floor of the party; at most
//     zrun_own_max own runs at once (2) and all the bots' runs of the core
//     within the dungeon runs' cap (GetPlayerBotDgRunCap: PLAYERBOT_DGRUN_* of
//     the panel). The leader calls on the kingdom's shout.
//   - the way in: as the portal's dialog for a party (zodiac_temples.quest):
//     12 Anima Spheres off each member (SetAnimaSphere(-12)) - one that cannot
//     pay goes home - then StartTemple. No boost, no prisms or potions given.
//   - inside as a test run; a death is paid with the bot's own Prisms (33025,
//     33032; 1/2/4/8/10) and with too few the bot is out of the temple
//     (playerbot_zodiac_bots.h - no free stand-up for a paying run).
//   - the end: the temple's own. Floor 39 done (a Metin of it broken) sends
//     everybody out with "the temple completed" (CZodiacManager::DeadMob);
//     floor 40, which a lucky Metin of 35-39 jumps to, is the Kupiec Zodiaku's
//     (20451, shop 41) - the bots buy there (ShopZrunBot: one Pergamin Sfer,
//     Prisms (Q) 33032 up to ZRUN_OWN_PRISMS, the shop's prices) and the run
//     leaves; a run whose ready floor is lower leaves when that floor is done
//     ("target"). V1-V6 read either end as "time_up" (the temple's exit under
//     way), and on floor 40 nobody shopped and nobody left: the run stood the
//     floor's five minutes ("floor=40 next=0/40 mobs=0" in every tick) until
//     the temple's time sent it out - 458 runs, finished=0.
//   - the rewards: the floors' gifts are the temple's (AutoGiveItem to every
//     character on the floor, bots too); the chests (33026-33028, 33033) are
//     opened by the bots' chest pass; at the end on 358 the Mnich Milbon's
//     part, as a player gets it: the Prisms (Q) of zodiac_prism_mission.quest
//     (200 once the first floor is done, 20 a day - the quest's ten Metins
//     read as a run past floor 8) and his exchange of ten Insignia of a kind
//     for a Kwiat Zywiolu (95500, the talismans' flower, which the bots use).
//     The temple's ranking is "Jeszcze nieaktywne" (zodiac_milbon.quest).
//
// The operator's file, added: own <sign 1-12|any> [n] (an own run now, off the
// clock and its caps), own on|off, ownmax <n>.

namespace
{
	const char* const ZRUN_TEST_FILE = "playerbot_zodiac_test";
	const char* const ZRUN_RUNS_FILE = "playerbot_zodiac_runs.tsv";
	const DWORD ZRUN_AFFECT_HP = 597;
	const DWORD ZRUN_AFFECT_ATT = 598;
	const DWORD ZRUN_AFFECT_DEF = 599;
	const DWORD ZRUN_GATHER_MS = 30000;
	const DWORD ZRUN_ENTER_MS = 30000;
	const DWORD ZRUN_STALL_MS = 15 * 60 * 1000;
	const DWORD ZRUN_EMPTY_MS = 20000;
	const DWORD ZRUN_HOME_MS = 4000;
	const DWORD ZRUN_STATUS_MS = 120000;
	const DWORD ZRUN_PRISM = 33025;
	// MT2009_PLUS_ZODIAC_RUNS_V2: this many deaths a bot on one floor and the run is pulled ("wipe").
	const int ZRUN_WIPE_DEATHS_PER_BOT = 4;
	// MT2009_PLUS_ZODIAC_RUNS_V3: the floors where one death sends the whole party out
	// (CZodiacManager::DeadPC: 6, 12, 19, 24 - run 3 of 9 October ended so on floor 12, seconds in).
	bool IsZrunNoDeathFloor(int floor)
	{
		return floor == 6 || floor == 12 || floor == 19 || floor == 24;
	}
	// MT2009_PLUS_ZODIAC_RUNS_V4: the floors whose mission is the Metins (ZodiacFloorMessage: 7, 8, 13, 14,
	// 18, 21, 27-30, 35-39). Every bot of the party breaks the leader's Metin, the monsters round it only
	// when they hold it - 9 October: on floor 8 the others fought the 80-90 monsters (39 000 HP each,
	// level 50-58, a flat +level x5 a blow in the temple) while the leader broke the stones alone, and
	// every sign's run died there (20-21 deaths, "wipe").
	bool IsZrunMetinFloor(int floor)
	{
		return floor == 7 || floor == 8 || floor == 13 || floor == 14 || floor == 18 || floor == 21 ||
				(floor >= 27 && floor <= 30) || (floor >= 35 && floor <= 39);
	}
	const int ZRUN_RED_POTION = 27003;
	const int ZRUN_BLUE_POTION = 27006;
	const char* const ZRUN_SIGN[13] = { "", "zi", "chou", "yin", "mao", "chen", "si", "wu", "wei", "shen", "yu", "xu", "hai" };
	// The portals' cells on 358 (data/dungeon/zodiac/days/7-sunday.txt), sign 1-12.
	const int ZRUN_PORTAL_CELL[13][2] = { { 260, 230 },
		{ 274, 226 }, { 290, 235 }, { 300, 253 }, { 301, 274 }, { 289, 290 }, { 273, 303 },
		{ 252, 303 }, { 234, 292 }, { 223, 274 }, { 223, 253 }, { 233, 235 }, { 249, 225 } };

	// MT2009_PLUS_ZODIAC_RUNS_V7: the bots' own runs (the header).
	const int ZRUN_SPHERE_COST = 12;		// zodiac_temples.quest: 12 Anima Spheres a member
	const DWORD ZRUN_PARCHMENT = 72329;		// Pergamin Sfer: +30 Anima Spheres (char_item.cpp hook (48))
	const DWORD ZRUN_PARCHMENT_TRADE = 72327;	// Pergamin Sfer (handel), the same
	const DWORD ZRUN_PRISM_Q = 33032;		// Pryzmat Ozywienia (Q): the merchant's, Milbon's
	const DWORD ZRUN_MERCHANT = 20451;		// Kupiec Zodiaku, floor 40 (zodiac_seller.txt)
	const DWORD ZRUN_MERCHANT_SHOP = 41;
	const DWORD ZRUN_FLOWER = 95500;		// Kwiat Zywiolu (zodiac_milbon.quest's exchange)
	const DWORD ZRUN_PORTAL_NPC_BASE = 20438;	// the portal of sign s: 20438 + s (20439-20450)
	const int ZRUN_OWN_MIN = 4;			// an own run's party, at least
	const int ZRUN_OWN_MIN_FLOOR = 6;		// a bot ready for less does not go
	const int ZRUN_OWN_PRISMS = 30;			// the Prisms a bot tops up to at the merchant
	const int ZRUN_OWN_CHECKS = 24;			// the Anima Spheres looked up a kingdom a call, at most
	const DWORD ZRUN_OWN_PLAN_MS = 3 * 60 * 1000;
	const DWORD ZRUN_SHOP_MS = 60000;		// floor 40: the merchant's minute, then out
	const DWORD ZRUN_BEAD_CHECK_MS = 3600 * 1000;
	const int ZRUN_SHOP_RANGE = 350;

	enum { ZRUN_PHASE_GATHER, ZRUN_PHASE_ENTER, ZRUN_PHASE_INSIDE, ZRUN_PHASE_OUT };

	struct TZrunHome
	{
		long lMap, lX, lY;
		int iPrismsBefore;
		TZrunHome() : lMap(0), lX(0), lY(0), iPrismsBefore(0) {}
	};

	struct TZrun
	{
		int iId;
		BYTE bSign;
		BYTE bPhase;
		BYTE bEmpire;
		DWORD dwLeader;
		std::vector<DWORD> members;
		std::map<DWORD, TZrunHome> homes;
		long lInstance;
		DWORD dwCalledAt, dwPhaseAt, dwEnteredAt, dwFloorAt, dwLastProgress, dwEmptySince, dwNextJump;
		BYTE bFloor, bMaxFloor;
		std::string floors;
		int iDeaths, iPrismRevives, iFreeRevives, iMinLevel, iMaxLevel, iTargetFloor;
		const char* szResult;
		// MT2009_PLUS_ZODIAC_RUNS_V2: where the floor began (the leader on the floor's first second), the
		// deaths on this floor, the next heartbeat.
		long lFloorX, lFloorY;
		int iFloorDeaths;
		DWORD dwNextBeat;
		std::set<DWORD> dead;	// V4: the members lying dead now (a death counted when it is seen)
		// V7: an own run (paid, no boost), and what it paid, bought and got; floor 40's first second and who shopped.
		bool bOwn;
		int iSpheres, iPrismsBought, iParchments, iFlowers, iMilbonPrisms, iDeathOuts;
		DWORD dwShopSince;
		std::set<DWORD> shopped;
		std::set<DWORD> outs;	// sent out of the temple by a death it could not pay for: no way back in
		TZrun() : lFloorX(0), lFloorY(0), iFloorDeaths(0), dwNextBeat(0), iId(0), bSign(0), bPhase(ZRUN_PHASE_GATHER), bEmpire(0), dwLeader(0), lInstance(0), dwCalledAt(0),
				dwPhaseAt(0), dwEnteredAt(0), dwFloorAt(0), dwLastProgress(0), dwEmptySince(0), dwNextJump(0), bFloor(0),
				bMaxFloor(0), iDeaths(0), iPrismRevives(0), iFreeRevives(0), iMinLevel(0), iMaxLevel(0), iTargetFloor(40),
				szResult(NULL), bOwn(false), iSpheres(0), iPrismsBought(0), iParchments(0), iFlowers(0), iMilbonPrisms(0),
				iDeathOuts(0), dwShopSince(0) {}
	};

	struct TZrunSignStats
	{
		unsigned int uRuns, uFinished, uBestFloor, uFloorSum, uDeaths;
		TZrunSignStats() : uRuns(0), uFinished(0), uBestFloor(0), uFloorSum(0), uDeaths(0) {}
	};

	std::map<int, TZrun> s_mapZruns;
	std::map<DWORD, int> s_mapZrunBots;
	TZrunSignStats s_aZrunStats[13];
	int s_iZrunNextId = 1;
	BYTE s_bZrunNextSign = 1;
	DWORD s_dwZrunNextLoop = 0;

	int GetZrunSetting(const char* name, int def)
	{
		const int v = quest::CQuestManager::instance().GetEventFlag(name);
		return v != 0 ? v : def;
	}
	int ZrunSize() { return std::max(1, std::min(8, GetZrunSetting("zrun_size", 5))); }
	int ZrunMinLevel() { return GetZrunSetting("zrun_level", 75); }
	int ZrunTargetFloor() { return std::max(1, std::min(40, GetZrunSetting("zrun_floor", 40))); }
	int ZrunBoost() { const int v = GetZrunSetting("zrun_boost", 30); return v < 0 ? 0 : v; }	// -1: none
	int ZrunPrisms() { const int v = GetZrunSetting("zrun_prisms", 30); return v < 0 ? 0 : v; }
	// V6: deaths a bot on one floor before the run is pulled ("wipe"; the test's "wipe <n>").
	int ZrunWipe() { return std::max(1, GetZrunSetting("zrun_wipe", ZRUN_WIPE_DEATHS_PER_BOT)); }
	// MT2009_PLUS_ZODIAC_WALL_V1 (10 November 2026, the test world: 318 own runs of mao / yin today, none past floor
	// 13, 499 of 520 deaths on floor 8 - its 8 Metins and 108-142 monsters of level 59 at the floor's first second - the
	// party of 7 bots of 89-94 (14-16k HP, defence ~390) down in 20 s, 20 deaths and 16 Prisms a run, 56 % "wipe"):
	//   - an own run pays its Prisms: pulled at ZRUN_OWN_WIPE_DEATHS_PER_BOT deaths a bot on a floor (zrun_own_wipe), not
	//     the test's four - the revive is where the floor began, in the same pack;
	//   - the wall: ZRUN_WALL_FAILS own runs of the core ended on one floor short of their target (wipe, leader_out,
	//     expelled, stalled) within ZRUN_WALL_MEMORY_MS make it a wall - the next own runs go to the floor under it
	//     ("target", the floors' gifts without the deaths) until a party of ZRUN_WALL_LEVEL_MARGIN levels over the
	//     strongest that failed comes, or the memory runs out (one probe a ZRUN_WALL_MEMORY_MS; a failure arms it
	//     again). A run past the floor clears it. zrun_wall -1: off; "status" lists the walls.
	const int ZRUN_OWN_WIPE_DEATHS_PER_BOT = 2;
	const int ZRUN_WALL_FAILS = 3;
	const DWORD ZRUN_WALL_MEMORY_MS = 3 * 60 * 60 * 1000;
	const int ZRUN_WALL_LEVEL_MARGIN = 3;
	int ZrunOwnWipe() { return std::max(1, GetZrunSetting("zrun_own_wipe", ZRUN_OWN_WIPE_DEATHS_PER_BOT)); }
	bool ZrunWallOn() { return GetZrunSetting("zrun_wall", 1) > 0; }
	struct TZrunWall
	{
		int iFails;
		int iBestMinLevel;	// the strongest party's lowest level that failed there
		DWORD dwLastAt;
		TZrunWall() : iFails(0), iBestMinLevel(0), dwLastAt(0) {}
	};
	TZrunWall s_aZrunWall[41];
	unsigned int s_uZrunWallCapped = 0;

	// The lowest wall at or under `target` for a party whose lowest level is minLevel; 0 none.
	int GetZrunWallFloor(int target, int minLevel, DWORD dwNow)
	{
		if (!ZrunWallOn())
			return 0;
		for (int f = 1; f <= std::min(40, target); ++f)
		{
			const TZrunWall& w = s_aZrunWall[f];
			if (w.iFails >= ZRUN_WALL_FAILS && dwNow - w.dwLastAt < ZRUN_WALL_MEMORY_MS &&
					minLevel < w.iBestMinLevel + ZRUN_WALL_LEVEL_MARGIN)
				return f;
		}
		return 0;
	}

	void NoteZrunWall(int floor, int target, const char* result, int minLevel, DWORD dwNow)
	{
		if (!result || floor <= 0 || floor > 40)
			return;
		const bool failed = floor < target && (!strcmp(result, "wipe") || !strcmp(result, "leader_out") ||
				!strcmp(result, "expelled") || !strcmp(result, "stalled"));
		if (!failed)
		{
			// a floor gone past (or the run's own end on it) is no wall
			for (int f = 1; f < floor || (f == floor && (!strcmp(result, "target") || !strcmp(result, "finished"))); ++f)
				s_aZrunWall[f] = TZrunWall();
			return;
		}
		TZrunWall& w = s_aZrunWall[floor];
		if (w.dwLastAt != 0 && dwNow - w.dwLastAt >= ZRUN_WALL_MEMORY_MS)
			w = TZrunWall();
		++w.iFails;
		w.iBestMinLevel = std::max(w.iBestMinLevel, minLevel);
		w.dwLastAt = dwNow ? dwNow : 1;
		if (w.iFails == ZRUN_WALL_FAILS)
			sys_log(0, "ZODIAC_RUN: wall floor=%d fails=%d best_min_level=%d - own runs stop at %d", floor, w.iFails,
					w.iBestMinLevel, floor - 1);
	}
	// V6: the test's "mixed 1": a party of the three kingdoms (more bots of the band; a test only).
	bool ZrunMixed() { return quest::CQuestManager::instance().GetEventFlag("zrun_mixed") > 0; }
	int ZrunGapSeconds() { return std::max(10, GetZrunSetting("zrun_gap", 60)); }
	bool ZrunLoop() { return quest::CQuestManager::instance().GetEventFlag("zrun_loop") != 0; }
	// V7: the bots' own runs on the clock (the test's "own on|off": on unless -1), and how many at once.
	bool ZrunOwn() { return GetZrunSetting("zrun_own", 1) > 0; }
	int ZrunOwnMax() { return std::max(1, std::min(10, GetZrunSetting("zrun_own_max", 2))); }

	// ------------------------------------------------------------ the questions others ask

	bool IsPlayerBotOnZodiacRun(DWORD pid)
	{
		return pid != 0 && !s_mapZrunBots.empty() && s_mapZrunBots.find(pid) != s_mapZrunBots.end();
	}

	// A run's moves (to the portal, into the temple, home) are its own.
	bool IsPlayerBotZodiacRunMove(LPCHARACTER ch, long targetMap)
	{
		(void)targetMap;
		return ch && IsPlayerBotOnZodiacRun(ch->GetPlayerID());
	}

	TZrun* FindZrunOf(DWORD pid)
	{
		std::map<DWORD, int>::const_iterator b = s_mapZrunBots.find(pid);
		if (b == s_mapZrunBots.end())
			return NULL;
		std::map<int, TZrun>::iterator r = s_mapZruns.find(b->second);
		return r == s_mapZruns.end() ? NULL : &r->second;
	}

	// V7: a bot of an own run pays its revives as a player (playerbot_zodiac_bots.h).
	bool IsPlayerBotZodiacPaidRun(DWORD pid)
	{
		const TZrun* run = pid ? FindZrunOf(pid) : NULL;
		return run && run->bOwn;
	}

	int CountOwnZruns()
	{
		int n = 0;
		for (std::map<int, TZrun>::const_iterator r = s_mapZruns.begin(); r != s_mapZruns.end(); ++r)
			if (r->second.bOwn)
				++n;
		return n;
	}

	// V7: playerbot_zodiac_bots.h - a paying bot without the Prisms is out of the temple.
	void NotePlayerBotZodiacRunDeathOut(DWORD pid)
	{
		TZrun* run = FindZrunOf(pid);
		if (run && run->outs.insert(pid).second)
			++run->iDeathOuts;
	}

	// From playerbot_zodiac_bots.h's revive.
	void NotePlayerBotZodiacRunRevive(DWORD pid, bool prisms)
	{
		TZrun* run = FindZrunOf(pid);
		if (!run)
			return;
		if (run->dead.insert(pid).second)	// a death the monitor had not seen yet
		{
			++run->iDeaths;
			++run->iFloorDeaths;
		}
		if (prisms)
			++run->iPrismRevives;
		else
			++run->iFreeRevives;
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (!ch)
			return;
		// V2: who stood round it (the first night's run 1 died 108 times on what the log never said).
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(ch->GetMapIndex(), get_dword_time());
		std::string near;
		int shown = 0;
		for (size_t i = 0; i < scan.foes.size() && shown < 4; ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!c || DISTANCE_APPROX(c->GetX() - ch->GetX(), c->GetY() - ch->GetY()) > 1500)
				continue;
			char part[64];
			snprintf(part, sizeof(part), "%s%u/lv%u/%d%%%s", near.empty() ? "" : ",", (unsigned int)c->GetRaceNum(),
					(unsigned int)c->GetLevel(), c->GetMaxHP() > 0 ? (int)((long long)c->GetHP() * 100 / c->GetMaxHP()) : 0,
					c->GetVictim() == ch ? "*" : "");
			near += part;
			++shown;
		}
		sys_log(0, "ZODIAC_RUN: death run=%d pid=%u name=%s floor=%u floor_deaths=%d deaths=%d maxhp=%d def=%d prisms=%d near=%s",
				run->iId, pid, ch->GetName(), (unsigned int)run->bFloor, run->iFloorDeaths, run->iDeaths, ch->GetMaxHP(),
				ch->GetPoint(POINT_DEF_GRADE), prisms ? 1 : 0, near.empty() ? "-" : near.c_str());
		// Up again where the floor began, not in the pack that felled it.
		if (run->lFloorX && run->lFloorY && ch->GetMapIndex() == run->lInstance)
		{
			ch->Show(run->lInstance, run->lFloorX, run->lFloorY, 0);
			ch->Stop();
		}
	}

	// ------------------------------------------------------------ the call

	struct TZrunCand
	{
		DWORD pid;
		int level;
		bool healer;
		int ready;	// V7: the floor it is ready for (an own run's), 0 for a test run
		int strength;	// MT2009_PLUS_ZODIAC_STRENGTH_V1/_V2: its level held to its real power (GetZrunStrength)
		TZrunCand(DWORD p, int l, bool h, int r = 0, int s = 0) : pid(p), level(l), healer(h), ready(r), strength(s) {}
	};

	// V7: the run of a drawn party (the leader first): the gathering at the sign's portal. StartZrun's own
	// second half, and an own run's (PlanOwnZrun).
	bool OpenZrun(BYTE sign, BYTE empire, const std::vector<TZrunCand>& picked, bool own, int targetFloor, size_t pool,
			DWORD dwNow, const char* why)
	{
		if (picked.empty())
			return false;
		TZrun run;
		run.iId = s_iZrunNextId++;
		run.bSign = sign;
		run.bEmpire = empire;
		run.bOwn = own;
		run.dwCalledAt = run.dwPhaseAt = run.dwLastProgress = dwNow;
		run.iTargetFloor = targetFloor;
		run.dwLeader = picked[0].pid;
		run.iMinLevel = 999;
		std::string names;
		const long portalX = 307200 + ZRUN_PORTAL_CELL[sign][0] * 100L;
		const long portalY = 1408000 + ZRUN_PORTAL_CELL[sign][1] * 100L;
		// A step from the portal towards the courtyard's middle.
		const long gatherX = portalX + (333200 - portalX) / 6;
		const long gatherY = portalY + (1431000 - portalY) / 6;
		for (size_t i = 0; i < picked.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(picked[i].pid);
			TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(picked[i].pid);
			if (!ch || st == s_mapPlayerBotAIStates.end())
				continue;
			TZrunHome home;
			home.lMap = ch->GetMapIndex();
			home.lX = ch->GetX();
			home.lY = ch->GetY();
			home.iPrismsBefore = (int)ch->CountSpecifyItem(ZRUN_PRISM);
			run.homes[picked[i].pid] = home;
			run.members.push_back(picked[i].pid);
			s_mapZrunBots[picked[i].pid] = run.iId;
			run.iMinLevel = std::min(run.iMinLevel, (int)ch->GetLevel());
			run.iMaxLevel = std::max(run.iMaxLevel, (int)ch->GetLevel());
			if (!names.empty())
				names += ",";
			names += ch->GetName();
			const int k = (int)i;
			const long x = gatherX + ((k % 3) - 1) * 150, y = gatherY + ((k / 3) - 1) * 150;
			s_szPlayerBotTransitionRefusal = NULL;
			if (ch->GetMapIndex() != PLAYERBOT_ZODIAC_MAP || DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y) > 800)
			{
				if (!TransitionPlayerBotMap(ch, st->second, PLAYERBOT_ZODIAC_MAP, x, y, dwNow, "zodiac_run"))
					sys_log(0, "ZODIAC_RUN: gather refused run=%d pid=%u name=%s why=%s", run.iId, ch->GetPlayerID(),
							ch->GetName(), s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "?");
			}
			st->second.dwTargetVID = 0;
		}
		if (run.members.empty())
			return false;
		sys_log(0, "ZODIAC_RUN: called run=%d sign=%u (%s) why=%s kind=%s kingdom=%d members=%u levels=%d-%d free=%u target_floor=%d names=%s",
				run.iId, (unsigned int)sign, ZRUN_SIGN[sign], why, own ? "own" : "test", (int)empire,
				(unsigned int)run.members.size(), run.iMinLevel, run.iMaxLevel, (unsigned int)pool, run.iTargetFloor,
				names.c_str());
		s_mapZruns[run.iId] = run;
		return true;
	}

	bool StartZrun(BYTE sign, int want, DWORD dwNow, const char* why)
	{
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_ZODIAC_MAP))
		{
			sys_log(0, "ZODIAC_RUN: call refused sign=%u - 358 is not on this core", (unsigned int)sign);
			return false;
		}
#ifdef ENABLE_12ZI
		// The candidates by kingdom.
		std::vector<TZrunCand> byEmpire[4];
		const int minLevel = ZrunMinLevel();
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (IsPlayerBotOnZodiacRun(it->first) || IsPlayerBotOnDungeonRun(it->first))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || ch->IsDead() || !ch->GetDesc() || !ch->GetDesc()->IsPhase(PHASE_GAME) || (int)ch->GetLevel() < minLevel ||
					ch->GetEmpire() < 1 || ch->GetEmpire() > 3 || ch->IsWarping())
				continue;
			if (GetPlayerBotLfgRefusal(ch, it->second, dwNow))
				continue;
			byEmpire[ch->GetEmpire()].push_back(TZrunCand(it->first, ch->GetLevel(),
					ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0));
		}
		if (ZrunMixed())
			for (int e = 2; e <= 3; ++e)
			{
				byEmpire[1].insert(byEmpire[1].end(), byEmpire[e].begin(), byEmpire[e].end());
				byEmpire[e].clear();
			}
		int empire = 0;
		for (int e = 1; e <= 3; ++e)
			if (!byEmpire[e].empty() && (empire == 0 || byEmpire[e].size() > byEmpire[empire].size()))
				empire = e;
		if (empire == 0)
		{
			sys_log(0, "ZODIAC_RUN: call refused sign=%u (%s) - no free bot of %d+", (unsigned int)sign, ZRUN_SIGN[sign], minLevel);
			return false;
		}
		std::vector<TZrunCand>& pool = byEmpire[empire];
		// The highest first; a Shaman with a skill group in it when one is free.
		std::sort(pool.begin(), pool.end(), [](const TZrunCand& a, const TZrunCand& b) { return a.level > b.level; });
		std::vector<TZrunCand> picked;
		for (size_t i = 0; i < pool.size() && picked.empty(); ++i)
			if (pool[i].healer)
				picked.push_back(pool[i]);
		for (size_t i = 0; i < pool.size() && (int)picked.size() < want; ++i)
			if (picked.empty() || pool[i].pid != picked[0].pid)
				picked.push_back(pool[i]);
		std::sort(picked.begin(), picked.end(), [](const TZrunCand& a, const TZrunCand& b) { return a.level > b.level; });
		return OpenZrun(sign, (BYTE)empire, picked, false, ZrunTargetFloor(), pool.size(), dwNow, why);
#else
		(void)want;
		(void)dwNow;
		(void)why;
		return false;
#endif
	}

	// ------------------------------------------------------------ V7: the bots' own call

	// MT2009_PLUS_ZODIAC_STRENGTH_V1 (the owner, 6 November 2026: only parties of sufficient strength go in).
	// On the floors 6, 12, 19 and 24 one death sends the whole party out (CZodiacManager::DeadPC) - "expelled"
	// was 88% of the failed own runs on the supporters' world (1 202 of 1 308 a week) and 1 012 of 1 132 on
	// vps3, nearly all of them on floor 6. Counted over the test world's 2 976 own runs (6 November) floor 6
	// throws out a party whose weakest member is of 45-59 in 27% of the runs, 60-64 20%, 65-69 15%, 70-74 11%,
	// 75-79 5%, 80+ 1% - the weakest member is the one who dies. So a party goes in only when, for each of
	// those floors on its way, its weakest member's strength (GetZrunStrength, below) is at least the floor's
	// mark and the party's average the mark + zrun_str_avg (5); its run ends before the first floor it is too
	// weak for, and a party too weak for floor 6 does not go (the weakest dropped first while more than
	// ZRUN_OWN_MIN remain). The marks are the event flags zrun_str6/12/19/24 (65/75/85/100); zrun_strength -1
	// switches the gate off. The operator's forced call ("own" in the test file) is not gated.
	//
	// MT2009_PLUS_ZODIAC_STRENGTH_V2 (the owner, 6 November 2026, as MT2009_PLUS_BOT_WUKONG_STRENGTH_V2: a
	// level-30 weapon with a good average-damage line, or a young heroes' weapon, is strong - the item level is
	// no measure). V1 held the strength to the gear's level (the weapon's and the armour's level + plus +
	// zrun_str_gear) and the ready floor to it + 15; neither reads an item level any more. A bot's strength is
	// its level - "the level it fights like" - unless its real blow (GetPlayerBotRealAttack: the hand's weapon
	// through the damage model) is under zrun_atk_pct (70) % or its max HP under zrun_hp_pct (70) % of the
	// medians of the bots of its band of five levels (GetPlayerBotBandMedians, sampled from level 50 by the
	// errands). Such a bot is held back in level units, so the marks keep their meaning (levels):
	//   q        = the worse of (blow / band's blow) / zrun_atk_pct and (HP / band's HP) / zrun_hp_pct, in %
	//   strength = min(level - zrun_str_gear, level * q / 100)          (only when q < 100)
	// - at least zrun_str_gear (10; now the held-back bot's least step down, about one mark: the marks lie
	// 10-15 apart) and deeper the further it lags: a 90 at 69% of its band's blow is 80 (to floor 18), at 49% is
	// 63 (not even floor 6). The ready floor is the strength + 5 (at most the level), as V1's gear + 15 was its
	// gear + 10. A band with too few samples (PLAYERBOT_HP70_MIN_SAMPLES) lets the bot through on its level
	// alone; no weapon in a sampled band is a blow of 0 (strength 0). The own call's refusals by level/atk/hp and
	// the held-back bots are counted: "ZODIAC_RUN: strength census" (throttled, and in "status").
	bool ZrunStrengthOn() { return GetZrunSetting("zrun_strength", 1) > 0; }
	int ZrunStrengthGear() { const int v = GetZrunSetting("zrun_str_gear", 10); return v < 0 ? 0 : v; }
	int ZrunStrengthAvg() { const int v = GetZrunSetting("zrun_str_avg", 5); return v < 0 ? 0 : v; }
	int ZrunStrengthPct(const char* name) { const int v = GetZrunSetting(name, 70); return v < 1 ? 70 : std::min(200, v); }
	int ZrunStrengthMark(int floor)
	{
		switch (floor)
		{
			case 6: return GetZrunSetting("zrun_str6", 65);
			case 12: return GetZrunSetting("zrun_str12", 75);
			case 19: return GetZrunSetting("zrun_str19", 85);
			case 24: return GetZrunSetting("zrun_str24", 100);
			default: return 0;
		}
	}

	// MT2009_PLUS_ZODIAC_STRENGTH_V2: why a bot's strength is what it is, and the census of the own call (bot
	// looks since the core started, a plan pass each).
	enum { ZRUN_POWER_OK = 0, ZRUN_POWER_NO_MEDIAN, ZRUN_POWER_ATK, ZRUN_POWER_HP };
	struct TZrunStrengthCensus
	{
		unsigned int looks, passed, noMedian, heldAtk, heldHp, refusedLevel, refusedAtk, refusedHp, trimmed, partyRefused;
	};
	TZrunStrengthCensus s_kZrunStrengthCensus = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };

	// The bot's strength (the level it fights like, above); why out: ZRUN_POWER_*.
	int GetZrunStrength(LPCHARACTER ch, int* pWhy = NULL)
	{
		if (pWhy)
			*pWhy = ZRUN_POWER_OK;
		if (!ch)
			return 0;
		const int level = ch->GetLevel();
		long long hpMedian = 0, atkMedian = 0;
		if (!GetPlayerBotBandMedians(level, &hpMedian, &atkMedian))
		{
			if (pWhy)
				*pWhy = ZRUN_POWER_NO_MEDIAN;
			return level;
		}
		long long qAtk = 100, qHp = 100;
		if (atkMedian > 0)
			qAtk = GetPlayerBotRealAttack(ch) * 10000 / (atkMedian * ZrunStrengthPct("zrun_atk_pct"));
		if (hpMedian > 0)
			qHp = (long long)ch->GetMaxHP() * 10000 / (hpMedian * ZrunStrengthPct("zrun_hp_pct"));
		const long long q = std::max(0LL, std::min(qAtk, qHp));
		if (q >= 100)
			return level;
		if (pWhy)
			*pWhy = qAtk <= qHp ? ZRUN_POWER_ATK : ZRUN_POWER_HP;
		return std::max(0, std::min(level - ZrunStrengthGear(), (int)((long long)level * q / 100)));
	}

	// The highest floor a level (or a strength) is ready for, against the floors' monsters (MobLevels: 1-3 up to
	// 30, 4-6 45, 7-9 60, 10-12 75, 13-15 80, 16-21 85, 22-28 100, 29-34 135; the Metins of 35-39 at
	// OfficerLevels, 120-135). 39 is the whole temple (40 follows it).
	int GetZrunReadyFloorOf(int e)
	{
		static const int s_aiReady[][2] = { { 110, 39 }, { 105, 34 }, { 100, 28 }, { 85, 21 }, { 80, 15 }, { 75, 12 },
			{ 60, 9 }, { 45, 6 } };
		for (size_t i = 0; i < sizeof(s_aiReady) / sizeof(s_aiReady[0]); ++i)
			if (e >= s_aiReady[i][0])
				return s_aiReady[i][1];
		return 0;
	}

	// The highest floor a bot is ready for: its level, held to its real power (V2: its strength + 5).
	int GetZrunReadyFloor(LPCHARACTER ch, int strength)
	{
		if (!ch)
			return 0;
		return GetZrunReadyFloorOf(std::min((int)ch->GetLevel(), strength + 5));
	}

	void LogZrunStrengthCensus(DWORD dwNow, bool throttled)
	{
		const TZrunStrengthCensus& c = s_kZrunStrengthCensus;
		char line[400];
		snprintf(line, sizeof(line), "looks=%u passed=%u no_median=%u held atk=%u hp=%u refused level=%u atk=%u hp=%u "
				"trimmed=%u party_refused=%u (gate=%d atk_pct=%d hp_pct=%d step=%d marks=%d/%d/%d/%d avg=+%d)",
				c.looks, c.passed, c.noMedian, c.heldAtk, c.heldHp, c.refusedLevel, c.refusedAtk, c.refusedHp, c.trimmed,
				c.partyRefused, ZrunStrengthOn() ? 1 : 0, ZrunStrengthPct("zrun_atk_pct"), ZrunStrengthPct("zrun_hp_pct"),
				ZrunStrengthGear(), ZrunStrengthMark(6), ZrunStrengthMark(12), ZrunStrengthMark(19), ZrunStrengthMark(24),
				ZrunStrengthAvg());
		if (throttled)
			PlayerBotLogThrottled("zrun_strength_census", dwNow, "ZODIAC_RUN: strength census %s", line);
		else
			sys_log(0, "ZODIAC_RUN: strength census %s", line);
	}

	// The last floor the party is strong enough to go to (39: the whole temple); the floor it stops before,
	// its weakest member's strength and the average, for the log.
	int GetZrunStrengthFloor(const std::vector<TZrunCand>& party, int* pStopAt = NULL, int* pMin = NULL, int* pAvg = NULL)
	{
		int weakest = 0, sum = 0;
		for (size_t i = 0; i < party.size(); ++i)
		{
			weakest = i == 0 ? party[i].strength : std::min(weakest, party[i].strength);
			sum += party[i].strength;
		}
		const int avg = party.empty() ? 0 : sum / (int)party.size();
		if (pMin)
			*pMin = weakest;
		if (pAvg)
			*pAvg = avg;
		if (pStopAt)
			*pStopAt = 0;
		static const int s_aiFloors[] = { 6, 12, 19, 24 };
		for (size_t i = 0; i < sizeof(s_aiFloors) / sizeof(s_aiFloors[0]); ++i)
		{
			const int mark = ZrunStrengthMark(s_aiFloors[i]);
			if (mark > 0 && (party.empty() || weakest < mark || avg < mark + ZrunStrengthAvg()))
			{
				if (pStopAt)
					*pStopAt = s_aiFloors[i];
				return s_aiFloors[i] - 1;
			}
		}
		return 39;
	}

	// The kingdom's party made strong enough for ZRUN_OWN_MIN_FLOOR: the weakest dropped (the one Shaman kept)
	// while more than ZRUN_OWN_MIN remain. The last floor it may go to, or 0 when it stays too weak.
	int TrimZrunPartyToStrength(std::vector<TZrunCand>& party, int empire, DWORD dwNow)
	{
		int stopAt = 0, weakest = 0, avg = 0;
		int floor = GetZrunStrengthFloor(party, &stopAt, &weakest, &avg);
		const size_t before = party.size();
		while (floor < ZRUN_OWN_MIN_FLOOR && (int)party.size() > ZRUN_OWN_MIN)
		{
			int healers = 0;
			for (size_t i = 0; i < party.size(); ++i)
				healers += party[i].healer ? 1 : 0;
			size_t drop = party.size();
			for (size_t i = 0; i < party.size(); ++i)
			{
				if (party[i].healer && healers == 1)
					continue;
				if (drop == party.size() || party[i].strength < party[drop].strength)
					drop = i;
			}
			if (drop == party.size())
				break;
			party.erase(party.begin() + drop);
			++s_kZrunStrengthCensus.trimmed;	// MT2009_PLUS_ZODIAC_STRENGTH_V2
			floor = GetZrunStrengthFloor(party, &stopAt, &weakest, &avg);
		}
		if (floor < ZRUN_OWN_MIN_FLOOR)
		{
			++s_kZrunStrengthCensus.partyRefused;	// MT2009_PLUS_ZODIAC_STRENGTH_V2
			PlayerBotLogThrottled("zrun_strength_refused", dwNow,
					"ZODIAC_RUN: strength gate refused empire=%d party=%u (of %u) weakest=%d avg=%d floor=%d needs=%d/%d",
					empire, (unsigned int)party.size(), (unsigned int)before, weakest, avg, stopAt,
					ZrunStrengthMark(stopAt), ZrunStrengthMark(stopAt) + ZrunStrengthAvg());
			return 0;
		}
		if (party.size() != before || floor < 39)
			PlayerBotLogThrottled("zrun_strength_capped", dwNow,
					"ZODIAC_RUN: strength gate empire=%d party=%u (of %u) weakest=%d avg=%d last_floor=%d",
					empire, (unsigned int)party.size(), (unsigned int)before, weakest, avg, floor);
		return floor;
	}

	// A Pergamin Sfer from the bag used as a player uses it (+30 Anima Spheres); true when one was.
	bool UseZrunParchment(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || (item->GetVnum() != ZRUN_PARCHMENT && item->GetVnum() != ZRUN_PARCHMENT_TRADE) || item->isLocked())
				continue;
			const DWORD vnum = item->GetVnum();
			if (ch->UseItem(TItemPos(INVENTORY, cell)))
			{
				sys_log(0, "ZODIAC_RUN: parchment used pid=%u name=%s vnum=%u", ch->GetPlayerID(), ch->GetName(), vnum);
				return true;
			}
			return false;
		}
		return false;
	}

	std::map<DWORD, DWORD> s_mapZrunBeadChecked;
	DWORD s_dwZrunOwnLastCall = 0;

	// The bot's Anima Spheres: the login's count (BeadTime: 36 the first time, one an hour since) once an hour,
	// a parchment used when short. 999 under the Znak Straznika (the entry free for its three hours).
	int GetZrunSpheres(LPCHARACTER ch, DWORD dwNow)
	{
#ifdef ENABLE_12ZI
		if (!ch)
			return 0;
		if (ch->IsAffectFlag(AFF_CZ_UNLIMIT_ENTER))
			return 999;
		DWORD& at = s_mapZrunBeadChecked[ch->GetPlayerID()];
		if (at == 0 || dwNow - at >= ZRUN_BEAD_CHECK_MS)
		{
			at = dwNow ? dwNow : 1;
			ch->BeadTime();
		}
		int n = ch->GetAnimaSphere();
		if (n < ZRUN_SPHERE_COST && UseZrunParchment(ch))
			n = ch->GetAnimaSphere();
		return n;
#else
		(void)ch;
		(void)dwNow;
		return 0;
#endif
	}

	// The entry paid as zodiac_temples.quest's DeletePartyAnimaSphere does; false when it cannot be.
	bool PayZrunEntry(LPCHARACTER ch, TZrun& run, DWORD dwNow)
	{
#ifdef ENABLE_12ZI
		if (!ch)
			return false;
		if (ch->IsAffectFlag(AFF_CZ_UNLIMIT_ENTER))
			return true;
		if (GetZrunSpheres(ch, dwNow) < ZRUN_SPHERE_COST)
			return false;
		ch->SetAnimaSphere(-ZRUN_SPHERE_COST);
		run.iSpheres += ZRUN_SPHERE_COST;
		return true;
#else
		(void)ch;
		(void)run;
		(void)dwNow;
		return false;
#endif
	}

	// The portal of the sign stands on 358 now (today's portals, or every one under zodiac_all_portals).
	bool IsZrunPortalOpen(BYTE sign)
	{
		CharacterVectorInteractor found;
		if (sign < 1 || sign > 12 || !CHARACTER_MANAGER::instance().GetCharactersByRaceNum(ZRUN_PORTAL_NPC_BASE + sign, found))
			return false;
		for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end(); ++it)
			if (*it && (*it)->GetMapIndex() == PLAYERBOT_ZODIAC_MAP)
				return true;
		return false;
	}

	// The call's line on the kingdom's shout.
	void ShoutZrunCall(LPCHARACTER leader, BYTE sign, int need, int targetFloor)
	{
		if (!leader)
			return;
		char text[128];
		switch (number(0, 2))
		{
			case 0:
				snprintf(text, sizeof(text), "zbieram pt do swiatyni zodiaku (%s), jeszcze %d osob, idziemy na %d pietro", ZRUN_SIGN[sign],
						need, targetFloor);
				break;
			case 1:
				snprintf(text, sizeof(text), "zodiak %s, %d wolnych miejsc, kto ma animosfery?", ZRUN_SIGN[sign], need);
				break;
			default:
				snprintf(text, sizeof(text), "pt na zodiaka %s, wbijac pod portal na dziedzincu", ZRUN_SIGN[sign]);
				break;
		}
		ShoutPlayerBotDgRun(leader, text, "zodiac_call");
	}

	// An own run's call: sign 0 - an open portal's, the least run first; forced (the operator's "own") - off the
	// clock, the caps, the rests, the shares and the shout gap; want - the party's size (0: 5-8).
	bool PlanOwnZrun(BYTE sign, int want, bool forced, DWORD dwNow, const char* why)
	{
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_ZODIAC_MAP))
		{
			if (forced)
				sys_log(0, "ZODIAC_RUN: own call refused - 358 is not on this core");
			return false;
		}
#ifdef ENABLE_12ZI
		// Within the core's cap of the bots' runs - above it by the dungeon runs' starved allowance when no own
		// run of the temple was called for PLAYERBOT_DGRUN_STARVED_MS (the dungeons keep the cap full).
		const int own = CountOwnZruns();
		const int all = CountPlayerBotDgRuns(-1) + own;
		const bool starved = own == 0 && (s_dwZrunOwnLastCall == 0 || dwNow - s_dwZrunOwnLastCall >= PLAYERBOT_DGRUN_STARVED_MS);
		if (!forced && (own >= ZrunOwnMax() || all >= GetPlayerBotDgRunCap() + (starved ? PLAYERBOT_DGRUN_STARVED_OVER_CAP : 0)))
			return false;
		if (sign == 0)
		{
			std::vector<BYTE> open;
			for (BYTE s = 1; s <= 12; ++s)
				if (IsZrunPortalOpen(s))
					open.push_back(s);
			if (open.empty())
			{
				if (forced)
					sys_log(0, "ZODIAC_RUN: own call refused (%s) - no portal stands on 358 now", why);
				return false;
			}
			// The least run of them, a random one of those.
			const size_t first = (size_t)number(0, (int)open.size() - 1);
			sign = open[first];
			for (size_t k = 1; k < open.size(); ++k)
			{
				const BYTE s = open[(first + k) % open.size()];
				if (s_aZrunStats[s].uRuns < s_aZrunStats[sign].uRuns)
					sign = s;
			}
		}
		else if (!forced && !IsZrunPortalOpen(sign))
			return false;
		if (want <= 0)
			want = number(5, 8);
		want = std::max(1, std::min(8, want));
		std::vector<TZrunCand> byEmpire[4];
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			const DWORD pid = it->first;
			if (IsPlayerBotOnZodiacRun(pid) || IsPlayerBotOnDungeonRun(pid))
				continue;
			if (!forced)
			{
				std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotDgRunRest.find(pid);
				if (rest != s_mapPlayerBotDgRunRest.end() && (int)(rest->second - dwNow) > 0)
					continue;
				if (!playerbot_dgrun::IsDungeonGoer(pid, GetPlayerBotDgRunShare(it->second)))
					continue;
			}
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch || ch->IsDead() || !ch->GetDesc() || !ch->GetDesc()->IsPhase(PHASE_GAME) || ch->IsWarping() ||
					ch->GetEmpire() < 1 || ch->GetEmpire() > 3 || !ch->IsItemLoaded())
				continue;
			if (!forced && s_adwPlayerBotDgRunShoutAt[ch->GetEmpire()] != 0 &&
					dwNow - s_adwPlayerBotDgRunShoutAt[ch->GetEmpire()] < PLAYERBOT_DGRUN_SHOUT_GAP_MS)
				continue;
			// MT2009_PLUS_ZODIAC_STRENGTH_V2: the strength and the ready floor of the real power; counted.
			int why = ZRUN_POWER_OK;
			const int strength = GetZrunStrength(ch, &why);
			const int ready = GetZrunReadyFloor(ch, strength);
			TZrunStrengthCensus& census = s_kZrunStrengthCensus;
			if (!forced)
				++census.looks;
			if (ready < ZRUN_OWN_MIN_FLOOR)
			{
				if (!forced)
				{
					if (GetZrunReadyFloorOf(ch->GetLevel()) < ZRUN_OWN_MIN_FLOOR)
						++census.refusedLevel;
					else if (why == ZRUN_POWER_ATK)
						++census.refusedAtk;
					else
						++census.refusedHp;
				}
				continue;
			}
			if (!forced)
			{
				++census.passed;
				if (why == ZRUN_POWER_NO_MEDIAN)
					++census.noMedian;
				else if (why == ZRUN_POWER_ATK)
					++census.heldAtk;
				else if (why == ZRUN_POWER_HP)
					++census.heldHp;
			}
			if (GetPlayerBotDgRunRefusal(ch, it->second, dwNow))
				continue;
			byEmpire[ch->GetEmpire()].push_back(TZrunCand(pid, ch->GetLevel(), ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0,
					ready, strength));
		}
		if (!forced)
			LogZrunStrengthCensus(dwNow, true);	// MT2009_PLUS_ZODIAC_STRENGTH_V2
		// Each kingdom's readiest first; the Anima Spheres asked of those (a query each) until the party is there.
		std::vector<TZrunCand> payers[4];
		size_t pools[4] = { 0, 0, 0, 0 };
		int strengthFloor[4] = { 39, 39, 39, 39 };	// MT2009_PLUS_ZODIAC_STRENGTH_V1
		int best = 0;
		for (int e = 1; e <= 3; ++e)
		{
			std::vector<TZrunCand>& pool = byEmpire[e];
			pools[e] = pool.size();
			if ((int)pool.size() < (forced ? 1 : ZRUN_OWN_MIN))
				continue;
			std::sort(pool.begin(), pool.end(), [](const TZrunCand& a, const TZrunCand& b)
					{ return a.ready != b.ready ? a.ready > b.ready : a.level > b.level; });
			bool healer = false;
			for (size_t i = 0, checks = 0; i < pool.size() && checks < (size_t)ZRUN_OWN_CHECKS &&
					((int)payers[e].size() < want || !healer); ++i)
			{
				// A full party without a Shaman looks further only for one.
				if ((int)payers[e].size() >= want && !pool[i].healer)
					continue;
				++checks;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pool[i].pid);
				if (!ch || GetZrunSpheres(ch, dwNow) < ZRUN_SPHERE_COST)
					continue;
				if ((int)payers[e].size() >= want)
					payers[e].pop_back();	// the last of the readiest gives way to the Shaman
				payers[e].push_back(pool[i]);
				healer = healer || pool[i].healer;
			}
			// MT2009_PLUS_ZODIAC_STRENGTH_V1: a party too weak for floor 6 stays out.
			strengthFloor[e] = 39;
			if (!forced && ZrunStrengthOn() && (int)payers[e].size() >= ZRUN_OWN_MIN)
			{
				strengthFloor[e] = TrimZrunPartyToStrength(payers[e], e, dwNow);
				if (strengthFloor[e] == 0)
					payers[e].clear();
			}
			if ((int)payers[e].size() >= (forced ? 1 : ZRUN_OWN_MIN) &&
					(best == 0 || payers[e].size() > payers[best].size()))
				best = e;
		}
		if (best == 0)
		{
			if (forced)
				sys_log(0, "ZODIAC_RUN: own call refused (%s) sign=%s - no kingdom has %d free, ready (floor %d+) bots holding %d Anima Spheres (free: %u/%u/%u)",
						why, ZRUN_SIGN[sign], forced ? 1 : ZRUN_OWN_MIN, ZRUN_OWN_MIN_FLOOR, ZRUN_SPHERE_COST,
						(unsigned int)pools[1], (unsigned int)pools[2], (unsigned int)pools[3]);
			return false;
		}
		std::vector<TZrunCand>& picked = payers[best];
		// The highest level leads; the run goes as far as its least ready member is ready for.
		std::sort(picked.begin(), picked.end(), [](const TZrunCand& a, const TZrunCand& b) { return a.level > b.level; });
		int target = strengthFloor[best];	// MT2009_PLUS_ZODIAC_STRENGTH_V1: no further than its strength goes
		for (size_t i = 0; i < picked.size(); ++i)
			target = std::min(target, picked[i].ready);
		if (target >= 39)
			target = 40;
		// MT2009_PLUS_ZODIAC_WALL_V1: no further than the floor under a wall this party is no stronger for.
		if (!forced)
		{
			int minLevel = 0;
			for (size_t i = 0; i < picked.size(); ++i)
				minLevel = i == 0 ? (int)picked[i].level : std::min(minLevel, (int)picked[i].level);
			const int wall = GetZrunWallFloor(target, minLevel, dwNow);
			if (wall > 0)
			{
				++s_uZrunWallCapped;
				PlayerBotLogThrottled("zrun_wall_cap", dwNow,
						"ZODIAC_RUN: own call held under the wall sign=%s kingdom=%d target=%d wall=%d min_level=%d best_failed=%d capped=%u",
						ZRUN_SIGN[sign], best, target, wall, minLevel, s_aZrunWall[wall].iBestMinLevel, s_uZrunWallCapped);
				if (wall - 1 < ZRUN_OWN_MIN_FLOOR)
					return false;
				target = wall - 1;
			}
		}
		if (!OpenZrun(sign, (BYTE)best, picked, true, target, pools[best], dwNow, why))
			return false;
		ShoutZrunCall(CHARACTER_MANAGER::instance().FindByPID(picked[0].pid), sign, (int)picked.size() - 1, target);
		s_dwZrunOwnLastCall = dwNow ? dwNow : 1;
		s_adwPlayerBotDgRunShoutAt[best] = dwNow ? dwNow : 1;
		return true;
#else
		(void)sign;
		(void)want;
		(void)forced;
		(void)dwNow;
		(void)why;
		return false;
#endif
	}

	// ------------------------------------------------------------ the supplies

	void SupplyZrunBot(LPCHARACTER ch, const TZrun& run)
	{
		if (!ch || !ch->IsItemLoaded())
			return;
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		if (red < 150 && ch->GetEmptyInventory(1) >= 0)
			ch->AutoGiveItem(ZRUN_RED_POTION, 200);
		if (blue < 100 && ch->GetEmptyInventory(1) >= 0)
			ch->AutoGiveItem(ZRUN_BLUE_POTION, 200);
		const int prisms = ZrunPrisms();
		const int have = (int)ch->CountSpecifyItem(ZRUN_PRISM);
		if (have < prisms && ch->GetEmptyInventory(1) >= 0)
			ch->AutoGiveItem(ZRUN_PRISM, prisms - have);
		const int boost = ZrunBoost();
		if (boost > 0)
		{
			const long seconds = 3 * 3600;
			ch->RemoveAffect(ZRUN_AFFECT_HP);
			ch->RemoveAffect(ZRUN_AFFECT_ATT);
			ch->RemoveAffect(ZRUN_AFFECT_DEF);
			// V5: flat max HP - POINT_MAX_HP_PCT is capped at +3500 HP by CHARACTER::ComputePoints, so the
			// night's boost 40/60/150 all gave the same 27 000 HP.
			const long extraHp = (long)ch->GetMaxHP() * boost / 100;
			ch->AddAffect(ZRUN_AFFECT_HP, POINT_MAX_HP, extraHp, 0, seconds, 0, true);
			ch->AddAffect(ZRUN_AFFECT_ATT, POINT_ATTBONUS_MONSTER, boost, 0, seconds, 0, true);
			ch->AddAffect(ZRUN_AFFECT_DEF, POINT_DEF_GRADE_BONUS, (long)ch->GetLevel() * boost / 10, 0, seconds, 0, true);
			ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		}
		(void)run;
	}

	void UnsupplyZrunBot(LPCHARACTER ch, const TZrunHome& home)
	{
		if (!ch)
			return;
		ch->RemoveAffect(ZRUN_AFFECT_HP);
		ch->RemoveAffect(ZRUN_AFFECT_ATT);
		ch->RemoveAffect(ZRUN_AFFECT_DEF);
		const int now = ch->IsItemLoaded() ? (int)ch->CountSpecifyItem(ZRUN_PRISM) : 0;
		if (now > home.iPrismsBefore)
			ch->RemoveSpecifyItem(ZRUN_PRISM, now - home.iPrismsBefore);
	}

	// ------------------------------------------------------------ V7: what an own run pays and gets

	// The spare purse (the bots' shopping rule: the reserved gold and the floor kept).
	long long GetZrunSpare(LPCHARACTER ch)
	{
		return ch ? (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR : 0;
	}

	// The Kupiec Zodiaku's price of one piece: the shop's line over its count (MT2009_PLUS_ZODIAC_MERCHANT_V1: the line of
	// Pryzmaty (Q) is x200 for 3 000 000 Yang - a bot buying a few paid the whole line for each), else the item's.
	long long GetZrunShopPrice(DWORD vnum)
	{
		if (LPSHOP shop = CShopManager::instance().Get(ZRUN_MERCHANT_SHOP))
		{
			const std::vector<CShop::SHOP_ITEM>& offers = shop->GetItemVector();
			for (size_t i = 0; i < offers.size(); ++i)
				if (offers[i].vnum == vnum && offers[i].price > 0)
					return std::max<long long>(1, (long long)offers[i].price / std::max<long long>(1, (long long)offers[i].count));
		}
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto ? (long long)proto->dwGold : 0;
	}

	LPCHARACTER FindZrunMerchant(long instance)
	{
		CharacterVectorInteractor found;
		if (!CHARACTER_MANAGER::instance().GetCharactersByRaceNum(ZRUN_MERCHANT, found))
			return NULL;
		for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end(); ++it)
			if (*it && (*it)->GetMapIndex() == instance)
				return *it;
		return NULL;
	}

	// Floor 40: to the merchant, then what a player buys there - one Pergamin Sfer (the shop's limit of a visit)
	// and the Prisms (Q) up to ZRUN_OWN_PRISMS (the shop's limit 200), out of half the spare purse.
	bool ShopZrunBot(LPCHARACTER ch, TPlayerBotAIState& state, TZrun& run, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (run.shopped.count(pid))
		{
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		LPCHARACTER npc = FindZrunMerchant(run.lInstance);
		if (!npc)
		{
			run.shopped.insert(pid);
			return true;
		}
		if (DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY()) > ZRUN_SHOP_RANGE)
		{
			MovePlayerBot(ch, npc->GetX(), npc->GetY(), dwNow, 24, true, false);
			return true;
		}
		run.shopped.insert(pid);
		if (ch->IsStateMove())
			ch->Stop();
		long long budget = GetZrunSpare(ch) / 2;
		int parchments = 0, prisms = 0;
		const long long parchmentPrice = GetZrunShopPrice(ZRUN_PARCHMENT);
		if (parchmentPrice > 0 && parchmentPrice <= budget && ch->GetEmptyInventory(1) >= 0)
		{
			PlayerBotChangeGold(ch, -parchmentPrice);
			ch->AutoGiveItem(ZRUN_PARCHMENT, 1, -1, false);
			budget -= parchmentPrice;
			parchments = 1;
		}
		const long long prismPrice = GetZrunShopPrice(ZRUN_PRISM_Q);
		const int have = (int)(ch->CountSpecifyItem(ZRUN_PRISM) + ch->CountSpecifyItem(ZRUN_PRISM_Q));
		if (prismPrice > 0 && have < ZRUN_OWN_PRISMS && ch->GetEmptyInventory(1) >= 0)
		{
			prisms = (int)std::min<long long>(std::min(ZRUN_OWN_PRISMS - have, 200), budget / prismPrice);
			if (prisms > 0)
			{
				PlayerBotChangeGold(ch, -(long long)prisms * prismPrice);
				ch->AutoGiveItem(ZRUN_PRISM_Q, (ITEM_COUNT)prisms, -1, false);
			}
			else
				prisms = 0;
		}
		run.iParchments += parchments;
		run.iPrismsBought += prisms;
		sys_log(0, "ZODIAC_RUN: merchant run=%d pid=%u name=%s parchment=%d prisms=%d (had %d) gold=%lld", run.iId, pid,
				ch->GetName(), parchments, prisms, have, (long long)ch->GetGold());
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// Out of the temple, on 358: Mnich Milbon's part (zodiac_prism_mission.quest, zodiac_milbon.quest) as a player
	// gets it - the Prisms (Q): 200 the first time a floor is done, 20 a day after the Metins (read: a run past
	// floor 8); the Insignia exchanged ten of a kind for a Kwiat Zywiolu.
	void RewardZrunBotAtMilbon(LPCHARACTER ch, TZrun& run)
	{
		if (!ch || !ch->IsItemLoaded() || ch->GetMapIndex() != PLAYERBOT_ZODIAC_MAP)
			return;
		int milbon = 0;
		if (run.bMaxFloor >= 2 && ch->GetQuestFlag("zrun_bot.milbon_first") == 0 && ch->GetEmptyInventory(1) >= 0)
		{
			ch->AutoGiveItem(ZRUN_PRISM_Q, 200, -1, false);
			ch->SetQuestFlag("zrun_bot.milbon_first", 1);
			milbon += 200;
		}
		const int today = (int)(get_global_time() / 86400);
		if (run.bMaxFloor >= 9 && ch->GetQuestFlag("zodiac_prism_mission.prism_timestamp") != today &&
				ch->GetEmptyInventory(1) >= 0)
		{
			ch->AutoGiveItem(ZRUN_PRISM_Q, 20, -1, false);
			ch->SetQuestFlag("zodiac_prism_mission.prism_timestamp", today);
			milbon += 20;
		}
		int flowers = 0;
		for (DWORD vnum = 33001; vnum <= 33024; ++vnum)
		{
			const int tens = std::min(200, (int)ch->CountSpecifyItem(vnum) / 10);
			if (tens <= 0 || ch->GetEmptyInventory(1) < 0)
				continue;
			ch->RemoveSpecifyItem(vnum, tens * 10);
			ch->AutoGiveItem(ZRUN_FLOWER, (ITEM_COUNT)tens, -1, false);
			flowers += tens;
		}
		run.iMilbonPrisms += milbon;
		run.iFlowers += flowers;
		if (milbon || flowers)
			sys_log(0, "ZODIAC_RUN: milbon run=%d pid=%u name=%s prisms=%d flowers=%d", run.iId, ch->GetPlayerID(), ch->GetName(),
					milbon, flowers);
	}

	// An own run's member who cannot go in (the Anima Spheres): home, and the run without it.
	void ReleaseZrunMember(TZrun& run, DWORD pid, DWORD dwNow, const char* why)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pid);
		const TZrunHome& home = run.homes[pid];
		if (ch && st != s_mapPlayerBotAIStates.end() && home.lMap > 0 && home.lMap < PLAYERBOT_INSTANCE_MAP_INDEX_MIN &&
				home.lMap != PLAYERBOT_ZODIAC_MAP && IsPlayerBotMapHostedHere(home.lMap) && !IsPlayerBotZodiacInstance(ch->GetMapIndex()))
			TransitionPlayerBotMap(ch, st->second, home.lMap, home.lX, home.lY, dwNow, "zodiac_run_home");
		sys_log(0, "ZODIAC_RUN: released run=%d pid=%u name=%s why=%s", run.iId, pid, ch ? ch->GetName() : "?", why);
		run.members.erase(std::remove(run.members.begin(), run.members.end(), pid), run.members.end());
		s_mapZrunBots.erase(pid);
	}

	// ------------------------------------------------------------ the party

	void MakeZrunParty(TZrun& run)
	{
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwLeader);
		if (!leader)
			return;
		LPPARTY party = leader->GetParty();
		if (party && party->GetLeaderPID() != leader->GetPlayerID())
		{
			LeavePlayerBotParty(leader);
			party = NULL;
		}
		if (!party)
		{
			party = CPartyManager::instance().CreateParty(leader);
			if (!party)
				return;
			party->Link(leader);
			party->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
		}
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			if (run.members[i] == run.dwLeader)
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!ch || ch->GetParty() == party || (ch->GetEmpire() != leader->GetEmpire() && !ZrunMixed()))
				continue;
			if (ch->GetParty())
				LeavePlayerBotParty(ch);
			party->Join(ch->GetPlayerID());
			party->Link(ch);
		}
	}

	// ------------------------------------------------------------ inside

	// The floor's objective for the leader: a Metin, else the nearest monster
	// or boss, else a statue; never the cannon.
	// V5: the floor's mission (ZodiacFloorMessage): a boss floor (6, 11, 17, 22) is the bosses, a Metin
	// floor the Metins, any other the monsters - a Metin hit there only calls more monsters (7 in 160 a
	// blow), and on floors 11 and 17 the night's runs broke Metins while the bosses' guards killed them.
	bool IsZrunBossFloor(int floor)
	{
		return floor == 6 || floor == 11 || floor == 17 || floor == 22;
	}

	LPCHARACTER PickZrunObjective(LPCHARACTER ch, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
		const TZrun* run = FindZrunOf(ch->GetPlayerID());
		const int floor = run ? run->bFloor : 0;
		LPCHARACTER metin = NULL, mob = NULL, statue = NULL, boss = NULL;
		int dMetin = INT_MAX, dMob = INT_MAX, dStatue = INT_MAX, dBoss = INT_MAX;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD race = scan.foes[i].dwRace;
			if (race == 20464)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c))
				continue;
			const int d = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			if (race >= 20452 && race <= 20463)
			{
				if (d < dStatue)
				{
					statue = c;
					dStatue = d;
				}
			}
			else if (c->IsStone())
			{
				if (d < dMetin)
				{
					metin = c;
					dMetin = d;
				}
			}
			else
			{
				if (race >= 2750 && race <= 2862 && d < dBoss)
				{
					boss = c;
					dBoss = d;
				}
				if (d < dMob)
				{
					mob = c;
					dMob = d;
				}
			}
		}
		if (IsZrunBossFloor(floor))
		{
			// The boss; its guards only when they stand between (nearer than a third of the way).
			if (boss)
				return (mob && mob != boss && dMob * 3 < dBoss) ? mob : boss;
			return mob ? mob : metin;
		}
		if (!IsZrunMetinFloor(floor) && floor != 0)
			return mob ? mob : (metin ? metin : statue);
		if (metin)
			return metin;
		// The target in hand kept while it lives (no flipping between two).
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (st != s_mapPlayerBotAIStates.end() && st->second.dwTargetVID)
		{
			LPCHARACTER cur = CHARACTER_MANAGER::instance().Find(st->second.dwTargetVID);
			if (IsPlayerBotPdgFoe(ch, cur) && !cur->IsStone() && cur->GetRaceNum() != 20464)
				return cur;
		}
		return mob ? mob : statue;
	}

	bool FightZrunLeader(LPCHARACTER ch, TPlayerBotAIState& state, TZrun& run, DWORD dwNow)
	{
		if (KeepPlayerBotTowerAlive(ch, state, dwNow, 75, 40))
			return true;
		if (BuffPlayerBotTowerFellows(ch, state, dwNow))
			return true;
		LPCHARACTER foe = PickZrunObjective(ch, dwNow);
		if (foe)
		{
			state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
			const bool fought = FightPlayerBotTowerObjective(ch, state, foe, dwNow);
			if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
			{
				state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
				ClearPlayerBotRoute(state, false);
				state.dwNextNavPlanTime = 0;
				MovePlayerBot(ch, foe->GetX(), foe->GetY(), dwNow, 24, true, false);
				if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
					UnstickPlayerBotArzDgFoe(ch, foe, ch->GetX(), ch->GetY(), dwNow);
			}
			return fought;
		}
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		(void)run;
		return true;
	}

	// The tick of a bot of a run (playerbot_manager.cpp, ahead of the bots'
	// dungeon runs and the party dungeon pass): true when it took it.
	bool ManagePlayerBotZodiacRun(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || s_mapZrunBots.empty() || ch->IsDead())
			return false;
		TZrun* run = FindZrunOf(ch->GetPlayerID());
		if (!run)
			return false;
		state.dwLastMeaningfulActivityTime = dwNow;
		state.lLastX = ch->GetX();
		state.lLastY = ch->GetY();
		const long map = ch->GetMapIndex();
		if (run->bPhase == ZRUN_PHASE_OUT)
			return false;
		if (!IsPlayerBotZodiacInstance(map))
		{
			// At the portal, waiting: drinking, standing.
			KeepPlayerBotTowerAlive(ch, state, dwNow, 90, 60);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			// Inside already, the run: after the leader.
			if (run->bPhase == ZRUN_PHASE_INSIDE && run->lInstance && ch->GetPlayerID() != run->dwLeader &&
					!run->outs.count(ch->GetPlayerID()))
			{
				LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run->dwLeader);
				TPlayerBotPdgBot& b = s_mapPlayerBotPdg[ch->GetPlayerID()];
				if (leader && leader->GetMapIndex() == run->lInstance && !leader->IsWarping() && dwNow >= b.dwNextFollow)
				{
					b.dwNextFollow = dwNow + PLAYERBOT_PDG_FOLLOW_RETRY_MS;
					PutPlayerBotBesidePdgPerson(ch, leader);
				}
			}
			return true;
		}
		// V2: the break-off - invisible, healing (HandlePostDeathRecovery) - as the bots' dungeon runs do;
		// V3: under 40%, and under 65% (drinking from 90%) on a floor where a death ends the run.
		const bool noDeath = IsZrunNoDeathFloor(run->bFloor);
		if (noDeath && ch->GetMaxHP() > 0 && (long long)ch->GetHP() * 100 < (long long)ch->GetMaxHP() * 90)
			UseHealthPotion(ch, state, dwNow, 90);
		if (!state.bRecoveringAfterDeath && ch->GetMaxHP() > 0 &&
				(long long)ch->GetHP() * 100 < (long long)ch->GetMaxHP() * (noDeath ? 65 : 40))
		{
			UseHealthPotion(ch, state, dwNow);
			state.bRecoveringAfterDeath = true;
			state.dwLastDeathTime = dwNow;
			state.lDeathX = ch->GetX();
			state.lDeathY = ch->GetY();
			state.dwNextRecoveryHealTime = dwNow;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			ch->ReviveInvisible(5);
			state.dwNextRecoveryProtectionTime = dwNow + PLAYERBOT_RECOVERY_PROTECTION_INTERVAL;
			sys_log(0, "ZODIAC_RUN: break-off run=%d pid=%u name=%s floor=%u hp=%d/%d", run->iId, ch->GetPlayerID(),
					ch->GetName(), (unsigned int)run->bFloor, ch->GetHP(), ch->GetMaxHP());
			return true;
		}
		// V7: floor 40, the merchant's: an own run's bots buy, a test run's stand (the run leaves).
		if (run->bFloor >= 40)
		{
			if (run->bOwn)
				return ShopZrunBot(ch, state, *run, dwNow);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		if (ch->GetPlayerID() == run->dwLeader)
			return FightZrunLeader(ch, state, *run, dwNow);
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run->dwLeader);
		if (!leader || leader->GetMapIndex() != map || leader->IsDead())
			return FightZrunLeader(ch, state, *run, dwNow);
		TPlayerBotPdgBot& b = s_mapPlayerBotPdg[ch->GetPlayerID()];
		if (b.lInstance != map)
		{
			b.lInstance = map;
			b.dwEnteredAt = dwNow;
			b.dwKills = 0;
		}
		// V4: on a Metin floor the leader's Metin (or the nearest one), whatever else attacks.
		if (IsZrunMetinFloor(run->bFloor) && !state.bRecoveringAfterDeath)
		{
			if (KeepPlayerBotTowerAlive(ch, state, dwNow, 75, 40))
				return true;
			LPCHARACTER metin = NULL;
			TPlayerBotAIStateMap::const_iterator ls = s_mapPlayerBotAIStates.find(leader->GetPlayerID());
			if (ls != s_mapPlayerBotAIStates.end() && ls->second.dwTargetVID)
			{
				LPCHARACTER t = CHARACTER_MANAGER::instance().Find(ls->second.dwTargetVID);
				if (IsPlayerBotPdgFoe(ch, t) && t->IsStone() && !IsPlayerBotZodiacLeftToPerson(t->GetRaceNum()))
					metin = t;
			}
			if (!metin)
			{
				LPCHARACTER o = PickZrunObjective(ch, dwNow);
				if (o && o->IsStone() && !IsPlayerBotZodiacLeftToPerson(o->GetRaceNum()))
					metin = o;
			}
			if (metin)
				return FightPlayerBotTowerObjective(ch, state, metin, dwNow);
		}
		return FightPlayerBotPartyDungeon(ch, state, b, leader, dwNow);
	}

	// ------------------------------------------------------------ the monitor

	void LogZrunRow(const TZrun& run, DWORD dwNow)
	{
		std::string names;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!names.empty())
				names += ",";
			names += ch ? ch->GetName() : "?";
		}
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwLeader);
		FILE* fp = fopen(ZRUN_RUNS_FILE, "a");
		if (fp)
		{
			// V7: the kind (own/test), the target floor, the Anima Spheres paid, the Prisms and parchments bought,
			// Milbon's Prisms, the flowers and the deaths that sent a bot out, at the row's end.
			fprintf(fp, "%ld\t%d\t%s\t%u\t%ld\t%u\t%u\t%d\t%d\t%s\t%u\t%u\t%s\t%d\t%d\t%d\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
					(long)get_global_time(), run.iId, ZRUN_SIGN[run.bSign], (unsigned int)run.bSign, run.lInstance,
					(unsigned int)run.bEmpire, (unsigned int)run.members.size(), run.iMinLevel, run.iMaxLevel,
					run.szResult ? run.szResult : "?", (unsigned int)run.bMaxFloor, (dwNow - run.dwCalledAt) / 1000,
					run.floors.empty() ? "-" : run.floors.c_str(), run.iDeaths, run.iPrismRevives, run.iFreeRevives,
					leader ? leader->GetName() : "?", names.c_str(), run.bOwn ? "own" : "test", run.iTargetFloor, run.iSpheres,
					run.iPrismsBought, run.iParchments, run.iMilbonPrisms, run.iFlowers, run.iDeathOuts);
			fclose(fp);
		}
		TZrunSignStats& st = s_aZrunStats[run.bSign];
		++st.uRuns;
		if (run.szResult && (!strcmp(run.szResult, "finished") || !strcmp(run.szResult, "target")))	// V7: its floor too
			++st.uFinished;
		st.uBestFloor = std::max<unsigned int>(st.uBestFloor, run.bMaxFloor);
		st.uFloorSum += run.bMaxFloor;
		st.uDeaths += run.iDeaths;
		if (run.bOwn)
			NoteZrunWall((int)run.bMaxFloor, run.iTargetFloor, run.szResult, run.iMinLevel, dwNow);	// MT2009_PLUS_ZODIAC_WALL_V1
		sys_log(0, "ZODIAC_RUN: closed run=%d sign=%s kind=%s result=%s floor=%u target=%d seconds=%u floors=%s deaths=%d prism_revives=%d free_revives=%d death_outs=%d spheres=%d prisms_bought=%d parchments=%d milbon_prisms=%d flowers=%d",
				run.iId, ZRUN_SIGN[run.bSign], run.bOwn ? "own" : "test", run.szResult ? run.szResult : "?",
				(unsigned int)run.bMaxFloor, run.iTargetFloor, (dwNow - run.dwCalledAt) / 1000,
				run.floors.empty() ? "-" : run.floors.c_str(), run.iDeaths, run.iPrismRevives, run.iFreeRevives, run.iDeathOuts,
				run.iSpheres, run.iPrismsBought, run.iParchments, run.iMilbonPrisms, run.iFlowers);
	}

	void NoteZrunFloor(TZrun& run, BYTE floor, DWORD dwNow)
	{
		if (floor == run.bFloor)
			return;
		if (run.bFloor != 0)
		{
			char part[24];
			snprintf(part, sizeof(part), "%s%u:%u", run.floors.empty() ? "" : ",", (unsigned int)run.bFloor,
					(dwNow - run.dwFloorAt) / 1000);
			run.floors += part;
		}
		sys_log(0, "ZODIAC_RUN: floor run=%d sign=%s floor=%u from=%u after_s=%u deaths=%d", run.iId, ZRUN_SIGN[run.bSign],
				(unsigned int)floor, (unsigned int)run.bFloor, run.bFloor ? (dwNow - run.dwFloorAt) / 1000 : 0, run.iDeaths);
		run.bFloor = floor;
		run.bMaxFloor = std::max(run.bMaxFloor, floor);
		run.dwFloorAt = dwNow;
		run.dwLastProgress = dwNow;
		run.iFloorDeaths = 0;
		run.lFloorX = run.lFloorY = 0;	// taken from the leader a moment later (the floor's jump)
	}

	// Everybody of the run out of the temple (the temple's own exit, or this).
	void PullZrun(TZrun& run, const char* result)
	{
		if (!run.szResult)
			run.szResult = result;
#ifdef ENABLE_12ZI
		LPZODIAC z = run.lInstance ? CZodiacManager::instance().FindByMapIndex(run.lInstance) : NULL;
		if (z)
			z->ExitTemple();
#endif
		sys_log(0, "ZODIAC_RUN: pulled run=%d sign=%s result=%s floor=%u", run.iId, ZRUN_SIGN[run.bSign], result,
				(unsigned int)run.bFloor);
	}

	// The run's bots home and free; false when the run is over.
	bool FinishZrun(TZrun& run, DWORD dwNow)
	{
		bool waiting = false;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			const DWORD pid = run.members[i];
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pid);
			if (!ch || st == s_mapPlayerBotAIStates.end())
			{
				s_mapZrunBots.erase(pid);
				continue;
			}
			if (IsPlayerBotZodiacInstance(ch->GetMapIndex()) || ch->IsWarping())
			{
				waiting = true;
				continue;
			}
			if (!s_mapZrunBots.count(pid))
				continue;
			const TZrunHome& home = run.homes[pid];
			// V7: an own run keeps its Prisms (its own and bought), gets Milbon's part, and rests as after a
			// dungeon run; a test run's supplies go.
			if (run.bOwn)
			{
				RewardZrunBotAtMilbon(ch, run);
				RestPlayerBotDgRun(pid, dwNow, PLAYERBOT_DGRUN_REST_MIN_MS + (DWORD)number(0, (int)PLAYERBOT_DGRUN_REST_SPREAD_MS));
			}
			else
				UnsupplyZrunBot(ch, home);
			if (ch->GetParty() && !IsPlayerBotHumanLedParty(ch->GetParty()))
				LeavePlayerBotParty(ch);
			if (ch->IsDead())
			{
				waiting = true;
				continue;
			}
			bool sent = false;
			if (home.lMap > 0 && home.lMap < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && home.lMap != PLAYERBOT_ZODIAC_MAP &&
					IsPlayerBotMapHostedHere(home.lMap))
				sent = TransitionPlayerBotMap(ch, st->second, home.lMap, home.lX, home.lY, dwNow, "zodiac_run_home");
			sys_log(0, "ZODIAC_RUN: home run=%d pid=%u name=%s to=%ld sent=%d", run.iId, pid, ch->GetName(), home.lMap,
					sent ? 1 : 0);
			s_mapZrunBots.erase(pid);
		}
		if (waiting && dwNow - run.dwPhaseAt < 60000)
			return true;
		// Whoever is still somewhere is let go.
		for (size_t i = 0; i < run.members.size(); ++i)
			s_mapZrunBots.erase(run.members[i]);
		LogZrunRow(run, dwNow);
		return false;
	}

	// One run's second; false when it is over.
	bool UpdateZrun(TZrun& run, DWORD dwNow)
	{
		if (run.bPhase == ZRUN_PHASE_OUT)
			return FinishZrun(run, dwNow);
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwLeader);
		if (run.bPhase == ZRUN_PHASE_GATHER)
		{
			int there = 0;
			for (size_t i = 0; i < run.members.size(); ++i)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
				if (ch && ch->GetMapIndex() == PLAYERBOT_ZODIAC_MAP && !ch->IsWarping() && !ch->IsDead())
					++there;
			}
			const bool leaderThere = leader && leader->GetMapIndex() == PLAYERBOT_ZODIAC_MAP && !leader->IsWarping();
			if (leaderThere && ((size_t)there == run.members.size() || (dwNow - run.dwPhaseAt > ZRUN_GATHER_MS && there >= 1)) &&
					dwNow - run.dwPhaseAt > 3000)
			{
#ifdef ENABLE_12ZI
				// V7: an own run pays at the portal as a party does (12 Anima Spheres each); one that cannot
				// goes home, a leader that cannot ends the call. A test run is supplied instead.
				if (run.bOwn)
				{
					const std::vector<DWORD> members = run.members;
					for (size_t i = 0; i < members.size(); ++i)
					{
						LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(members[i]);
						if (PayZrunEntry(ch, run, dwNow))
							continue;
						if (members[i] == run.dwLeader)
						{
							run.szResult = "no_spheres";
							run.bPhase = ZRUN_PHASE_OUT;
							run.dwPhaseAt = dwNow;
							sys_log(0, "ZODIAC_RUN: leader cannot pay run=%d pid=%u", run.iId, members[i]);
							return true;
						}
						ReleaseZrunMember(run, members[i], dwNow, "no_spheres");
					}
				}
				MakeZrunParty(run);
				for (size_t i = 0; i < run.members.size() && !run.bOwn; ++i)
					SupplyZrunBot(CHARACTER_MANAGER::instance().FindByPID(run.members[i]), run);
				sys_log(0, "ZODIAC_RUN: gathered run=%d sign=%s kind=%s there=%d/%u party=%u boost=%d prisms=%d target_floor=%d spheres_paid=%d",
						run.iId, ZRUN_SIGN[run.bSign], run.bOwn ? "own" : "test", there, (unsigned int)run.members.size(),
						leader->GetParty() ? (unsigned int)leader->GetParty()->GetMemberCount() : 0U, run.bOwn ? 0 : ZrunBoost(),
						run.bOwn ? 0 : ZrunPrisms(), run.iTargetFloor, run.iSpheres);
				CZodiacManager::instance().StartTemple(leader, run.bSign);
#endif
				run.bPhase = ZRUN_PHASE_ENTER;
				run.dwPhaseAt = dwNow;
				return true;
			}
			if (dwNow - run.dwPhaseAt > ZRUN_GATHER_MS * 2)
			{
				run.szResult = "no_gathering";
				run.bPhase = ZRUN_PHASE_OUT;
				run.dwPhaseAt = dwNow;
			}
			return true;
		}
		if (run.bPhase == ZRUN_PHASE_ENTER)
		{
			if (leader && IsPlayerBotZodiacInstance(leader->GetMapIndex()))
			{
				run.lInstance = leader->GetMapIndex();
				run.bPhase = ZRUN_PHASE_INSIDE;
				run.dwPhaseAt = run.dwEnteredAt = run.dwLastProgress = dwNow;
				int inside = 0;
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (ch && ch->GetMapIndex() == run.lInstance)
						++inside;
				}
				sys_log(0, "ZODIAC_RUN: entered run=%d sign=%s instance=%ld inside=%d/%u", run.iId, ZRUN_SIGN[run.bSign],
						run.lInstance, inside, (unsigned int)run.members.size());
				return true;
			}
			if (dwNow - run.dwPhaseAt > ZRUN_ENTER_MS)
			{
				run.szResult = "no_entry";
				run.bPhase = ZRUN_PHASE_OUT;
				run.dwPhaseAt = dwNow;
			}
			return true;
		}
		// Inside.
#ifdef ENABLE_12ZI
		LPZODIAC z = CZodiacManager::instance().FindByMapIndex(run.lInstance);
		int inside = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (ch && ch->GetMapIndex() == run.lInstance)
				++inside;
		}
		// V4: the deaths, counted as they are seen - also one the temple's exit warps out before its revive.
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			const bool isDead = ch && ch->IsDead() && IsPlayerBotZodiacInstance(ch->GetMapIndex());
			if (isDead && run.dead.insert(run.members[i]).second)
			{
				++run.iDeaths;
				++run.iFloorDeaths;
			}
			else if (!isDead)
				run.dead.erase(run.members[i]);
		}
		if (z)
		{
			if (!run.szResult)	// V7: not after the run's own end (a pulled run's floor stays 0)
				NoteZrunFloor(run, z->GetFloor(), dwNow);
			if (z->IsNextFloor() && leader && leader->GetMapIndex() == run.lInstance && !leader->IsDead() &&
					(int)dwNow - (int)run.dwNextJump >= 0)
			{
				run.dwNextJump = dwNow + 4000;
				if ((int)run.bFloor >= run.iTargetFloor)
				{
					// V7: the run's own floor done - the whole temple only at 39/40 (the temple's end does those).
					NoteZrunFloor(run, 0, dwNow);
					PullZrun(run, run.iTargetFloor >= 39 ? "finished" : "target");
				}
				else
				{
					// V3: a jump onto a floor where one death ends the run is left for the step up,
					// when the step up is not such a floor itself.
					// V7: nor a jump past the run's own floor (an own run is ready up to it).
					const bool step = z->GetNextFloor() != run.bFloor + 1 &&
							((IsZrunNoDeathFloor(z->GetNextFloor()) && !IsZrunNoDeathFloor(run.bFloor + 1)) ||
							(run.bOwn && (int)z->GetNextFloor() > run.iTargetFloor && run.iTargetFloor < 39));
					sys_log(0, "ZODIAC_RUN: next run=%d sign=%s floor=%u to=%u how=%s", run.iId, ZRUN_SIGN[run.bSign],
							(unsigned int)run.bFloor, step ? (unsigned int)(run.bFloor + 1) : (unsigned int)z->GetNextFloor(),
							step ? "step" : "jump");
					if (step)
						interpret_command(leader, "nextfloor", strlen("nextfloor"));
					else
						interpret_command(leader, "jumpfloor", strlen("jumpfloor"));
				}
			}
			if (dwNow - run.dwLastProgress > ZRUN_STALL_MS && !run.szResult)
				PullZrun(run, "stalled");
			// V7: floor 40, the Kupiec Zodiaku's - an own run's bots buy (ShopZrunBot), then the run leaves; a
			// test run leaves at once. V1-V6 stood here till the floor's time sent them out ("time_up").
			if (z->GetFloor() >= 40 && !run.szResult)
			{
				run.dwLastProgress = dwNow;
				if (!run.dwShopSince)
					run.dwShopSince = dwNow ? dwNow : 1;
				bool shopped = true;
				for (size_t i = 0; i < run.members.size() && run.bOwn; ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (ch && ch->GetMapIndex() == run.lInstance && !ch->IsDead() && !run.shopped.count(run.members[i]))
						shopped = false;
				}
				if (shopped || dwNow - run.dwShopSince > ZRUN_SHOP_MS)
				{
					NoteZrunFloor(run, 0, dwNow);
					PullZrun(run, "finished");
				}
			}
			// V3: the temple's own way out under way - why, for the row.
			// V7: floor 39 done (a Metin of it broken: "completed_floor" 39) is the temple's end, not its time.
			LPCHARACTER flagOf = leader && leader->GetMapIndex() == run.lInstance ? leader : NULL;
			if (z->IsExiting() && !run.szResult && run.bFloor >= 39 && flagOf &&
					flagOf->GetQuestFlag("12zi_temple.completed_floor") >= 39)
			{
				run.szResult = "finished";
				sys_log(0, "ZODIAC_RUN: temple completed run=%d sign=%s floor=%u", run.iId, ZRUN_SIGN[run.bSign],
						(unsigned int)run.bFloor);
			}
			if (z->IsExiting() && !run.szResult)
			{
				// MT2009_PLUS_ZODIAC_DIAG_V1 (the second bot analysis, point 3a/3b): V3-V8 called every way out on
				// 6/12/19/24 "expelled" - the floor's time too (the failed runs left after 297-354 s on average:
				// the floor's limit, not a death). Now the temple's own note says why (CZodiac::NoteExit): a
				// death -> "expelled", the time -> "time_up", the end -> "finished"; without a note (zodiac_diag
				// -1) the old guess. The line adds the boss still standing (race, HP %), the bosses and monsters
				// left, the dead person, and each member's distance to the boss, HP % and state.
				const CZodiac::TExitNote& note = z->GetExitNote();
				if (note.bCause == CZodiac::ZODIAC_EXIT_DEATH)
					run.szResult = "expelled";
				else if (note.bCause == CZodiac::ZODIAC_EXIT_TIME)
					run.szResult = "time_up";
				else if (note.bCause == CZodiac::ZODIAC_EXIT_COMPLETED)
					run.szResult = "finished";
				else
					run.szResult = IsZrunNoDeathFloor(run.bFloor) ? "expelled" : "time_up";
				std::string who;
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					char buf[96];
					if (!ch || ch->GetMapIndex() != run.lInstance)
						snprintf(buf, sizeof(buf), "%s%u:out", who.empty() ? "" : ",", (unsigned int)run.members[i]);
					else
						snprintf(buf, sizeof(buf), "%s%u:L%d:hp%d:%s:d%d", who.empty() ? "" : ",", (unsigned int)run.members[i],
								(int)ch->GetLevel(),
								ch->GetMaxHP() > 0 ? (int)((long long)ch->GetHP() * 100 / ch->GetMaxHP()) : -1,
								ch->IsDead() ? "dead" : "up",
								note.dwBossRace ? DISTANCE_APPROX(ch->GetX() - note.lBossX, ch->GetY() - note.lBossY) : -1);
					who += buf;
				}
				sys_log(0, "ZODIAC_RUN: temple exit run=%d sign=%s floor=%u result=%s cause=%s floor_s=%u deaths=%d floor_deaths=%d boss=%u boss_hp=%d bosses=%d mobs=%d dead_pid=%u members=%s",
						run.iId, ZRUN_SIGN[run.bSign], (unsigned int)run.bFloor, run.szResult, CZodiac::ExitCauseName(note.bCause),
						(unsigned int)((dwNow - run.dwFloorAt) / 1000), run.iDeaths, run.iFloorDeaths,
						(unsigned int)note.dwBossRace, note.iBossHpPct, note.iBosses, note.iMobs, (unsigned int)note.dwDeadPid,
						who.c_str());
			}
			// V2: the floor's first point (where the temple jumped everybody), once the jump is over.
			if (!run.lFloorX && run.bFloor && leader && leader->GetMapIndex() == run.lInstance && !leader->IsDead() &&
					dwNow - run.dwFloorAt > 2000)
			{
				run.lFloorX = leader->GetX();
				run.lFloorY = leader->GetY();
			}
			// V2: a floor that kills the party over and over is over; so is a temple whose first floor never came.
			// MT2009_PLUS_ZODIAC_WALL_V1: an own run (paid Prisms) at fewer.
			if (!run.szResult && run.iFloorDeaths >= (run.bOwn ? ZrunOwnWipe() : ZrunWipe()) * (int)run.members.size())
				PullZrun(run, "wipe");
			if (!run.szResult && run.bFloor == 0 && dwNow - run.dwEnteredAt > 120000)
				PullZrun(run, "no_floor");
			// V7: the party's leader (the only one the floor's button answers) out without its Prisms - the
			// run is over as a party's whose leader left.
			if (!run.szResult && run.outs.count(run.dwLeader))
				PullZrun(run, "leader_out");
			if ((int)(dwNow - run.dwNextBeat) >= 0)
			{
				run.dwNextBeat = dwNow + 20000;
				const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
				int mobs = 0, metins = 0, statues = 0, bosses = 0, alive = 0;
				for (size_t i = 0; i < scan.foes.size(); ++i)
				{
					const DWORD race = scan.foes[i].dwRace;
					if (race >= 20452 && race <= 20464)
						++statues;
					else if (race >= 2900 && race <= 2937)
						++metins;
					else if (race >= 2750 && race <= 2862)
						++bosses;
					else
						++mobs;
				}
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (ch && ch->GetMapIndex() == run.lInstance && !ch->IsDead())
						++alive;
				}
				LPCHARACTER tgt = NULL;
				if (leader)
				{
					TPlayerBotAIStateMap::const_iterator ls = s_mapPlayerBotAIStates.find(leader->GetPlayerID());
					if (ls != s_mapPlayerBotAIStates.end() && ls->second.dwTargetVID)
						tgt = CHARACTER_MANAGER::instance().Find(ls->second.dwTargetVID);
				}
				sys_log(0, "ZODIAC_RUN: tick run=%d sign=%s floor=%u next=%d/%u mobs=%d metins=%d statues=%d bosses=%d alive=%d/%u inside=%d deaths=%d floor_deaths=%d leader_hp=%d target=%u dist=%d pos=(%ld,%ld)",
						run.iId, ZRUN_SIGN[run.bSign], (unsigned int)z->GetFloor(), z->IsNextFloor() ? 1 : 0,
						(unsigned int)z->GetNextFloor(), mobs, metins, statues, bosses, alive, (unsigned int)run.members.size(),
						inside, run.iDeaths, run.iFloorDeaths,
						leader && leader->GetMaxHP() > 0 ? (int)((long long)leader->GetHP() * 100 / leader->GetMaxHP()) : -1,
						tgt ? (unsigned int)tgt->GetRaceNum() : 0U,
						tgt && leader ? DISTANCE_APPROX(tgt->GetX() - leader->GetX(), tgt->GetY() - leader->GetY()) : -1,
						leader ? leader->GetX() : 0L, leader ? leader->GetY() : 0L);
			}
		}
		if (!z || inside == 0)
		{
			if (run.dwEmptySince == 0)
				run.dwEmptySince = dwNow;
			if (!z || dwNow - run.dwEmptySince > ZRUN_EMPTY_MS)
			{
				if (run.bFloor)
					NoteZrunFloor(run, 0, dwNow);
				if (!run.szResult)
					run.szResult = run.bMaxFloor >= 40 ? "finished" : "out";
				sys_log(0, "ZODIAC_RUN: out run=%d sign=%s result=%s floor=%u temple=%s", run.iId, ZRUN_SIGN[run.bSign],
						run.szResult, (unsigned int)run.bMaxFloor, z ? "alive" : "gone");
				run.bPhase = ZRUN_PHASE_OUT;
				run.dwPhaseAt = dwNow + ZRUN_HOME_MS;
			}
		}
		else
			run.dwEmptySince = 0;
#endif
		return true;
	}

	void LogZrunStatus()
	{
		for (int s = 1; s <= 12; ++s)
		{
			const TZrunSignStats& st = s_aZrunStats[s];
			sys_log(0, "ZODIAC_RUN: status sign=%s runs=%u finished=%u best_floor=%u avg_floor=%u deaths=%u", ZRUN_SIGN[s],
					st.uRuns, st.uFinished, st.uBestFloor, st.uRuns ? st.uFloorSum / st.uRuns : 0U, st.uDeaths);
		}
		std::string open;
		for (BYTE s = 1; s <= 12; ++s)
			if (IsZrunPortalOpen(s))
			{
				open += open.empty() ? "" : ",";
				open += ZRUN_SIGN[s];
			}
		sys_log(0, "ZODIAC_RUN: status runs=%u own_runs=%d bots=%u loop=%d own=%d own_max=%d core_runs=%d/%d portals=%s size=%d level=%d floor=%d boost=%d prisms=%d gap=%d next_sign=%u",
				(unsigned int)s_mapZruns.size(), CountOwnZruns(), (unsigned int)s_mapZrunBots.size(), ZrunLoop() ? 1 : 0,
				ZrunOwn() ? 1 : 0, ZrunOwnMax(), CountPlayerBotDgRuns(-1) + CountOwnZruns(), GetPlayerBotDgRunCap(),
				open.empty() ? "-" : open.c_str(), ZrunSize(), ZrunMinLevel(), ZrunTargetFloor(), ZrunBoost(), ZrunPrisms(),
				ZrunGapSeconds(), (unsigned int)s_bZrunNextSign);
		LogZrunStrengthCensus(get_dword_time(), false);	// MT2009_PLUS_ZODIAC_STRENGTH_V2
		// MT2009_PLUS_ZODIAC_WALL_V1: the walls the own runs stop under.
		const DWORD now = get_dword_time();
		std::string walls;
		for (int f = 1; f <= 40; ++f)
		{
			const TZrunWall& w = s_aZrunWall[f];
			if (w.iFails <= 0 || now - w.dwLastAt >= ZRUN_WALL_MEMORY_MS)
				continue;
			char part[64];
			snprintf(part, sizeof(part), "%s%d:%d/lv%d/%umin", walls.empty() ? "" : ",", f, w.iFails, w.iBestMinLevel,
					(unsigned int)((now - w.dwLastAt) / 60000));
			walls += part;
		}
		sys_log(0, "ZODIAC_RUN: status walls on=%d fails_for_wall=%d own_wipe=%d capped=%u floors=%s", ZrunWallOn() ? 1 : 0,
				ZRUN_WALL_FAILS, ZrunOwnWipe(), s_uZrunWallCapped, walls.empty() ? "-" : walls.c_str());
	}

	BYTE ParseZrunSign(const char* arg)
	{
		const int n = atoi(arg);
		if (n >= 1 && n <= 12)
			return (BYTE)n;
		for (int s = 1; s <= 12; ++s)
			if (!strcasecmp(arg, ZRUN_SIGN[s]))
				return (BYTE)s;
		return 0;
	}

	void SetZrunSetting(const char* name, int value)
	{
		quest::CQuestManager::instance().RequestSetEventFlag(name, value);
		sys_log(0, "ZODIAC_RUN: test %s=%d", name, value);
	}

	void RunZrunTestFile(DWORD dwNow)
	{
		FILE* fp = fopen(ZRUN_TEST_FILE, "r");
		if (!fp)
			return;
		std::vector<std::string> lines;
		char line[128];
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", ZRUN_TEST_FILE);
		rename(ZRUN_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "", arg[32] = "";
			int value = 0;
			const int got = sscanf(lines[l].c_str(), "%31s %31s %d", cmd, arg, &value);
			if (got < 1 || cmd[0] == '#')
				continue;
			if (!strcmp(cmd, "status"))
				LogZrunStatus();
			else if (!strcmp(cmd, "now"))
			{
				BYTE sign = got >= 2 && strcmp(arg, "any") ? ParseZrunSign(arg) : s_bZrunNextSign;
				if (sign == 0)
				{
					sys_log(0, "ZODIAC_RUN: test now - no sign %s", arg);
					continue;
				}
				if (got < 2 || !strcmp(arg, "any"))
					s_bZrunNextSign = (BYTE)(sign % 12 + 1);
				StartZrun(sign, got >= 3 && value > 0 ? value : ZrunSize(), dwNow, "test");
			}
			// V7: an own (paid) run now, off the clock and its caps; the clock's own runs on or off; how many at once.
			else if (!strcmp(cmd, "own") && got >= 2 && (!strcmp(arg, "on") || !strcmp(arg, "off")))
				SetZrunSetting("zrun_own", !strcmp(arg, "on") ? 1 : -1);
			else if (!strcmp(cmd, "own"))
			{
				const BYTE sign = got >= 2 && strcmp(arg, "any") ? ParseZrunSign(arg) : 0;
				if (got >= 2 && strcmp(arg, "any") && sign == 0)
				{
					sys_log(0, "ZODIAC_RUN: test own - no sign %s", arg);
					continue;
				}
				PlanOwnZrun(sign, got >= 3 && value > 0 ? value : 0, true, dwNow, "test_own");
			}
			else if (!strcmp(cmd, "ownmax") && got >= 2)
				SetZrunSetting("zrun_own_max", std::max(1, atoi(arg)));
			else if (!strcmp(cmd, "loop") && got >= 2)
				SetZrunSetting("zrun_loop", !strcmp(arg, "on") || !strcmp(arg, "1") ? 1 : 0);
			else if ((!strcmp(cmd, "size") || !strcmp(cmd, "level") || !strcmp(cmd, "floor") || !strcmp(cmd, "boost") ||
					!strcmp(cmd, "prisms") || !strcmp(cmd, "gap") || !strcmp(cmd, "wipe") || !strcmp(cmd, "mixed")) && got >= 2)
			{
				char flag[48];
				snprintf(flag, sizeof(flag), "zrun_%s", cmd);
				const int v = atoi(arg);
				SetZrunSetting(flag, v == 0 ? -1 : v);
			}
			else if (!strcmp(cmd, "allportals") && got >= 2)
			{
				SetZrunSetting("zodiac_all_portals", atoi(arg) ? 1 : 0);
				s_dwZrunNextLoop = dwNow + 3000;	// the flag reaches this core first; the portals then
#ifdef ENABLE_12ZI
				// The db core answers the flag back in a moment; the spawn reads it then.
				quest::CQuestManager::instance().SetEventFlag("zodiac_all_portals", atoi(arg) ? 1 : 0);
				CZodiacManager::instance().Spawn();
#endif
			}
			else if (!strcmp(cmd, "abort"))
			{
				for (std::map<int, TZrun>::iterator r = s_mapZruns.begin(); r != s_mapZruns.end(); ++r)
				{
					if (r->second.bPhase == ZRUN_PHASE_INSIDE)
						PullZrun(r->second, "aborted");
					else if (r->second.bPhase != ZRUN_PHASE_OUT)
					{
						r->second.szResult = "aborted";
						r->second.bPhase = ZRUN_PHASE_OUT;
						r->second.dwPhaseAt = dwNow;
					}
				}
				SetZrunSetting("zrun_loop", 0);
			}
			else
				sys_log(0, "ZODIAC_RUN: test unknown line=%s", lines[l].c_str());
		}
	}

	// The world's pass, once a second (playerbot_manager.cpp).
	void ManagePlayerBotZodiacRuns(DWORD dwNow)
	{
		static DWORD s_dwNext = 0, s_dwNextFile = 0, s_dwNextStatus = 0;
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + 1000;
		if ((int)(dwNow - s_dwNextFile) >= 0)
		{
			s_dwNextFile = dwNow + 5000;
			RunZrunTestFile(dwNow);
		}
		for (std::map<int, TZrun>::iterator r = s_mapZruns.begin(); r != s_mapZruns.end();)
		{
			if (r->second.bPhase == ZRUN_PHASE_OUT && (int)(dwNow - r->second.dwPhaseAt) < 0)
			{
				++r;
				continue;
			}
			if (UpdateZrun(r->second, dwNow))
				++r;
			else
			{
				s_mapZruns.erase(r++);
				s_dwZrunNextLoop = dwNow + ZrunGapSeconds() * 1000;
			}
		}
		// V7: the test loop waits for its own run only (the bots' own runs go on beside it).
		if ((int)s_mapZruns.size() == CountOwnZruns() && ZrunLoop() && (int)(dwNow - s_dwZrunNextLoop) >= 0)
		{
			s_dwZrunNextLoop = dwNow + 30000;
			const BYTE sign = s_bZrunNextSign;
			if (StartZrun(sign, ZrunSize(), dwNow, "loop"))
				s_bZrunNextSign = (BYTE)(sign % 12 + 1);
		}
		// V7: the bots' own calls - with the bots' dungeon runs on, not while the operator's loop tests, not in
		// the core's first minutes.
		{
			static DWORD s_dwNextOwn = 0;
			if (s_dwNextOwn == 0)
				s_dwNextOwn = dwNow + PLAYERBOT_DGRUN_FIRST_PLAN_MS;
			if ((int)(dwNow - s_dwNextOwn) >= 0)
			{
				s_dwNextOwn = dwNow + ZRUN_OWN_PLAN_MS;
				if (ZrunOwn() && !ZrunLoop() && IsPlayerBotDgRunOn(dwNow))
					PlanOwnZrun(0, 0, false, dwNow, "clock");
			}
		}
		if ((int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + ZRUN_STATUS_MS;
			if (!s_mapZruns.empty() || ZrunLoop())
				LogZrunStatus();
		}
	}
}

#endif
