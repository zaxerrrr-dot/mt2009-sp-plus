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
// Not here yet: the bots' own calls on the clock (with the Anima Spheres and
// the prisms paid), the merchant.

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
	const int ZRUN_RED_POTION = 27003;
	const int ZRUN_BLUE_POTION = 27006;
	const char* const ZRUN_SIGN[13] = { "", "zi", "chou", "yin", "mao", "chen", "si", "wu", "wei", "shen", "yu", "xu", "hai" };
	// The portals' cells on 358 (data/dungeon/zodiac/days/7-sunday.txt), sign 1-12.
	const int ZRUN_PORTAL_CELL[13][2] = { { 260, 230 },
		{ 274, 226 }, { 290, 235 }, { 300, 253 }, { 301, 274 }, { 289, 290 }, { 273, 303 },
		{ 252, 303 }, { 234, 292 }, { 223, 274 }, { 223, 253 }, { 233, 235 }, { 249, 225 } };

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
		TZrun() : iId(0), bSign(0), bPhase(ZRUN_PHASE_GATHER), bEmpire(0), dwLeader(0), lInstance(0), dwCalledAt(0),
				dwPhaseAt(0), dwEnteredAt(0), dwFloorAt(0), dwLastProgress(0), dwEmptySince(0), dwNextJump(0), bFloor(0),
				bMaxFloor(0), iDeaths(0), iPrismRevives(0), iFreeRevives(0), iMinLevel(0), iMaxLevel(0), iTargetFloor(40),
				szResult(NULL) {}
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
	int ZrunGapSeconds() { return std::max(10, GetZrunSetting("zrun_gap", 60)); }
	bool ZrunLoop() { return quest::CQuestManager::instance().GetEventFlag("zrun_loop") != 0; }

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

	// From playerbot_zodiac_bots.h's revive.
	void NotePlayerBotZodiacRunRevive(DWORD pid, bool prisms)
	{
		TZrun* run = FindZrunOf(pid);
		if (!run)
			return;
		++run->iDeaths;
		if (prisms)
			++run->iPrismRevives;
		else
			++run->iFreeRevives;
	}

	// ------------------------------------------------------------ the call

	struct TZrunCand
	{
		DWORD pid;
		int level;
		bool healer;
		TZrunCand(DWORD p, int l, bool h) : pid(p), level(l), healer(h) {}
	};

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

		TZrun run;
		run.iId = s_iZrunNextId++;
		run.bSign = sign;
		run.bEmpire = (BYTE)empire;
		run.dwCalledAt = run.dwPhaseAt = run.dwLastProgress = dwNow;
		run.iTargetFloor = ZrunTargetFloor();
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
		sys_log(0, "ZODIAC_RUN: called run=%d sign=%u (%s) why=%s kingdom=%d members=%u levels=%d-%d free=%u names=%s",
				run.iId, (unsigned int)sign, ZRUN_SIGN[sign], why, empire, (unsigned int)run.members.size(), run.iMinLevel,
				run.iMaxLevel, (unsigned int)pool.size(), names.c_str());
		s_mapZruns[run.iId] = run;
		return true;
#else
		(void)want;
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
			ch->AddAffect(ZRUN_AFFECT_HP, POINT_MAX_HP_PCT, boost, 0, seconds, 0, true);
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
			if (!ch || ch->GetParty() == party || ch->GetEmpire() != leader->GetEmpire())
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
	LPCHARACTER PickZrunObjective(LPCHARACTER ch, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
		LPCHARACTER metin = NULL, mob = NULL, statue = NULL;
		int dMetin = INT_MAX, dMob = INT_MAX, dStatue = INT_MAX;
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
			else if (d < dMob)
			{
				mob = c;
				dMob = d;
			}
		}
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
			if (run->bPhase == ZRUN_PHASE_INSIDE && run->lInstance && ch->GetPlayerID() != run->dwLeader)
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
			fprintf(fp, "%ld\t%d\t%s\t%u\t%ld\t%u\t%u\t%d\t%d\t%s\t%u\t%u\t%s\t%d\t%d\t%d\t%s\t%s\n",
					(long)get_global_time(), run.iId, ZRUN_SIGN[run.bSign], (unsigned int)run.bSign, run.lInstance,
					(unsigned int)run.bEmpire, (unsigned int)run.members.size(), run.iMinLevel, run.iMaxLevel,
					run.szResult ? run.szResult : "?", (unsigned int)run.bMaxFloor, (dwNow - run.dwCalledAt) / 1000,
					run.floors.empty() ? "-" : run.floors.c_str(), run.iDeaths, run.iPrismRevives, run.iFreeRevives,
					leader ? leader->GetName() : "?", names.c_str());
			fclose(fp);
		}
		TZrunSignStats& st = s_aZrunStats[run.bSign];
		++st.uRuns;
		if (run.szResult && !strcmp(run.szResult, "finished"))
			++st.uFinished;
		st.uBestFloor = std::max<unsigned int>(st.uBestFloor, run.bMaxFloor);
		st.uFloorSum += run.bMaxFloor;
		st.uDeaths += run.iDeaths;
		sys_log(0, "ZODIAC_RUN: closed run=%d sign=%s result=%s floor=%u seconds=%u floors=%s deaths=%d prism_revives=%d free_revives=%d",
				run.iId, ZRUN_SIGN[run.bSign], run.szResult ? run.szResult : "?", (unsigned int)run.bMaxFloor,
				(dwNow - run.dwCalledAt) / 1000, run.floors.empty() ? "-" : run.floors.c_str(), run.iDeaths,
				run.iPrismRevives, run.iFreeRevives);
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
				MakeZrunParty(run);
				for (size_t i = 0; i < run.members.size(); ++i)
					SupplyZrunBot(CHARACTER_MANAGER::instance().FindByPID(run.members[i]), run);
				sys_log(0, "ZODIAC_RUN: gathered run=%d sign=%s there=%d/%u party=%u boost=%d prisms=%d target_floor=%d",
						run.iId, ZRUN_SIGN[run.bSign], there, (unsigned int)run.members.size(),
						leader->GetParty() ? (unsigned int)leader->GetParty()->GetMemberCount() : 0U, ZrunBoost(), ZrunPrisms(),
						run.iTargetFloor);
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
		if (z)
		{
			NoteZrunFloor(run, z->GetFloor(), dwNow);
			if (z->IsNextFloor() && leader && leader->GetMapIndex() == run.lInstance && !leader->IsDead() &&
					(int)dwNow - (int)run.dwNextJump >= 0)
			{
				run.dwNextJump = dwNow + 4000;
				if ((int)run.bFloor >= run.iTargetFloor)
				{
					NoteZrunFloor(run, 0, dwNow);
					PullZrun(run, "finished");
				}
				else
				{
					sys_log(0, "ZODIAC_RUN: next run=%d sign=%s floor=%u to=%u", run.iId, ZRUN_SIGN[run.bSign],
							(unsigned int)run.bFloor, (unsigned int)z->GetNextFloor());
					interpret_command(leader, "jumpfloor", strlen("jumpfloor"));
				}
			}
			if (dwNow - run.dwLastProgress > ZRUN_STALL_MS && !run.szResult)
				PullZrun(run, "stalled");
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
		sys_log(0, "ZODIAC_RUN: status runs=%u bots=%u loop=%d size=%d level=%d floor=%d boost=%d prisms=%d gap=%d next_sign=%u",
				(unsigned int)s_mapZruns.size(), (unsigned int)s_mapZrunBots.size(), ZrunLoop() ? 1 : 0, ZrunSize(),
				ZrunMinLevel(), ZrunTargetFloor(), ZrunBoost(), ZrunPrisms(), ZrunGapSeconds(), (unsigned int)s_bZrunNextSign);
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
			else if (!strcmp(cmd, "loop") && got >= 2)
				SetZrunSetting("zrun_loop", !strcmp(arg, "on") || !strcmp(arg, "1") ? 1 : 0);
			else if ((!strcmp(cmd, "size") || !strcmp(cmd, "level") || !strcmp(cmd, "floor") || !strcmp(cmd, "boost") ||
					!strcmp(cmd, "prisms") || !strcmp(cmd, "gap")) && got >= 2)
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
		if (s_mapZruns.empty() && ZrunLoop() && (int)(dwNow - s_dwZrunNextLoop) >= 0)
		{
			s_dwZrunNextLoop = dwNow + 30000;
			const BYTE sign = s_bZrunNextSign;
			if (StartZrun(sign, ZrunSize(), dwNow, "loop"))
				s_bZrunNextSign = (BYTE)(sign % 12 + 1);
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
