#ifndef __INC_METIN2_PLAYERBOT_DGRUN_MELEY_H__
#define __INC_METIN2_PLAYERBOT_DGRUN_MELEY_H__

// MT2009_PLUS_BOT_MELEY_RUNS_V1 - the bots' runs of Schronienie Meley (356), demand-driven by the helmets of level 100
// (the owner's order of 5/6 November 2026; cache/yohara/noc-2026-11-06-lochy-brief.md; the bot trainer's report of
// 4 November: ~200 GEAR2 plans - Jaharr's helmets - wait for Czerwony Smoczy Rog / Czerwona Smocza Luska / Plan Zbroi:
// Helm (30620-30622), which drop only from the lair's magma monsters - tools/yohara_meley/gen_ymeley.py drops()).
//
// Why no run started (the test server, 5 November: "meley running=0 called=0 started=0 ... free=0/1/0" all day):
//   * the band: RUN_RULES' meley row starts at 95 and BandMax adds LEVEL_SPAN (15) - 95-110; the bots that need the
//     helmet are 100-120 and most of the strong ones of game1 are 111-120 (Nemere's 105-120 runs took them), so the
//     band held one or two bots a kingdom;
//   * the core: 356 sits on game1 (its quest's NPC Dolnarr stands on 62 - d.new_jump makes the instance on the NPC's
//     core, bin/m2-render-config), while the ~400 Sung Ma bots with the plans live on game3 (the Yohara core) and come
//     to game1 only on their trade trips (playerbot_yohara_sungma.h), and then never into a run's pool;
//   * the rest: a bot's rest after any run is 40-80 minutes, the panel's 3 h cooldown for bots on top, and the
//     clock's one call per pass over all the dungeons, the kingdom's shout gap and the core's cap of 4 runs shared with
//     Nemere, the Ruins and the Zodiac temples (meley's own cap was 1).
//
// What this does:
//   * game1 (the core hosting 356): PlanPlayerBotMeleyRuns, its own clock (PLAYERBOT_MELEY_PLAN_MS), outside the core's
//     cap and the clock's draw - the meley row of the clock's pass is left to it. Up to GetPlayerBotMeleyRunCap() runs
//     at once; each kingdom's pool of the free bots of 95+ (no level top - the dungeon has none for people either):
//     the Sung Ma visitors who came for it first, then the bots whose GEAR2 helmet waits for the lair's materials,
//     then the strongest (ScorePlayerBotYdg: level, champion level, gear, health, attack, defence). A party: a healing
//     Shaman (the rule), no class over its third, `size` members (6). The players' rules: level 90+ (95 for the
//     bots), the fee (7 500 000, paid by a bot holding three of it - ChargePlayerBotDgRunEntry), 5 runs a day
//     (meley_dungeon.day/.runs); the bots' 3 h cooldown (the panel's flag) on the clock, off in training (people
//     have none - MT2009_PLUS_DUNGEON_NO_PLAYER_COOLDOWN_V1).
//   * game3 (and every core not hosting 356): a Sung Ma resident whose helmet waits for the lair's materials goes home
//     to its first village on game1 on a trade trip of its own reason "meley" (GetPlayerBotSungmaTradeReason), up to
//     GetPlayerBotMeleyTripCap() bots away at once, outside the trade trips' own cap; at home it is held
//     (IsPlayerBotSungmaTradeHomeDone) until it ran the lair (PLAYERBOT_MELEY_VISIT_RUNS, training: more while it still
//     needs and has runs left today) or PLAYERBOT_MELEY_VISIT_MAX_MS passed, then its trip goes back as every one.
//   * the loot: the members' own drops (HandleLoot); every PLAYERBOT_MELEY_SHARE_MS inside and at the end a member's
//     lair materials beyond its own helmet's need go to the member who lacks most (a trade between the members).
//   * the fight: the members get the YDG run's bonuses for the hour (BuffPlayerBotYdgMember - the bots stronger, the
//     lair unchanged: no monster, statue, egg or quest changed) and a bag cell (MakePlayerBotYdgRoom).
//
// The operator: the file playerbot_meley_train in the core's directory (read every 30 s when it changed; kept), the
// same line on game1 and game3:
//     parties <n> [size]   n runs at once on game1 (the 3 h rest off, a short rest after a run), parties of size
//                          (5-8, default 6); on game3 up to n * size Sung Ma visitors away at once
//     trips <n>            the visitors' cap, whatever parties says
//     # ...                a comment
// Without the file: PLAYERBOT_MELEY_RUNS (.env, default 2) runs at once and PLAYERBOT_MELEY_TRIPS (default 12)
// visitors. The event flag m2_bot_meley_off 1 stops new calls and trips. The test file playerbot_dungeon_runs_test:
// "now meley" calls at once (this pass, forced), "meley_status" logs the pools.
//
// The log: BOT_MELEY lines (train, pool, called, share, run start / end with the materials gained, trip out / home /
// held / released, status every PLAYERBOT_MELEY_STATUS_MS) besides the BOT_DGRUN ones of every run.
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h, in the anonymous namespace, after the
// YDG one (its bonuses, room and score); the Sung Ma hooks (playerbot_yohara_sungma.h) and the gear2 need
// (playerbot_yohara_gear2.h) come later in the same translation unit.

namespace
{
	const long PLAYERBOT_MELEY_MAP = 356;
	const int PLAYERBOT_MELEY_MIN_LEVEL = 95;
	const DWORD PLAYERBOT_MELEY_MATS[3] = { 30620, 30621, 30622 };	// Czerwony Smoczy Rog, Czerwona Smocza Luska, Plan Zbroi: Helm
	const DWORD PLAYERBOT_MELEY_PLAN_MS = 20 * 1000;
	const DWORD PLAYERBOT_MELEY_FILE_MS = 30 * 1000;
	const DWORD PLAYERBOT_MELEY_STATUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_MELEY_SHARE_MS = 30 * 1000;
	const DWORD PLAYERBOT_MELEY_TRAIN_REST_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_MELEY_TRAIN_REST_SPREAD_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_MELEY_VISIT_MAX_MS = 100 * 60 * 1000;	// a run's hour, the gathering, the wait for a party
	const DWORD PLAYERBOT_MELEY_VISIT_MIN_STAY_MS = 5 * 60 * 1000;	// on its Sung Ma map before a trip
	const DWORD PLAYERBOT_MELEY_TRIP_GAP_MS = 30 * 60 * 1000;	// between two trips of one bot
	const DWORD PLAYERBOT_MELEY_TRIP_LOST_MS = 150 * 60 * 1000;
	const int PLAYERBOT_MELEY_VISIT_RUNS = 1;
	const int PLAYERBOT_MELEY_VISIT_RUNS_TRAIN = 3;
	const int PLAYERBOT_MELEY_CALLS_A_PASS = 2;
	const char* const PLAYERBOT_MELEY_TRAIN_FILE = "playerbot_meley_train";

	// playerbot_yohara_gear2.h (later in this unit): how many of a material the bot's targets take, one attempt.
	int GetPlayerBotGear2MaterialNeed(LPCHARACTER ch, DWORD vnum);

	struct TPlayerBotMeleyTrain
	{
		int parties;	// 0: no training (the defaults)
		int size;
		int trips;	// -1: by parties
		TPlayerBotMeleyTrain() : parties(0), size(6), trips(-1) {}
	};
	TPlayerBotMeleyTrain s_kPlayerBotMeleyTrain;

	// The visitors at home (this core hosts 356): since when, the runs of this visit.
	struct TPlayerBotMeleyVisit
	{
		DWORD dwSince;
		int iRuns;
		bool bReleased;
		TPlayerBotMeleyVisit() : dwSince(0), iRuns(0), bReleased(false) {}
	};
	std::map<DWORD, TPlayerBotMeleyVisit> s_mapPlayerBotMeleyVisit;
	// The trips out (a core without 356): pid -> when it left.
	std::map<DWORD, DWORD> s_mapPlayerBotMeleyTripOut;
	std::map<DWORD, DWORD> s_mapPlayerBotMeleyTripLast;
	// This planner's runs: run id -> the members' materials at the start (pid -> horn/scale/plan).
	struct TPlayerBotMeleyRun
	{
		bool bTrain;
		int iNeeders, iVisitors;
		DWORD dwNextShare;
		int iShared;
		std::map<DWORD, std::vector<int> > start;
		TPlayerBotMeleyRun() : bTrain(false), iNeeders(0), iVisitors(0), dwNextShare(0), iShared(0) {}
	};
	std::map<int, TPlayerBotMeleyRun> s_mapPlayerBotMeleyRuns;
	struct TPlayerBotMeleyStats
	{
		unsigned int called, entered, won, mats, shared, tripsOut, visitsHome, visitsReleased;
		TPlayerBotMeleyStats() : called(0), entered(0), won(0), mats(0), shared(0), tripsOut(0), visitsHome(0), visitsReleased(0) {}
	};
	TPlayerBotMeleyStats s_kPlayerBotMeleyStats;

	bool IsPlayerBotMeleyOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_meley_off") != 0;
	}

	int FindPlayerBotMeleyDef()
	{
		for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
			if (PLAYERBOT_DGRUN_DEFS[i].bKind == DGRUN_KIND_MELEY)
				return i;
		return -1;
	}

	bool IsPlayerBotMeleyTraining()
	{
		return s_kPlayerBotMeleyTrain.parties > 0;
	}

	int GetPlayerBotMeleyRunCap()
	{
		if (IsPlayerBotMeleyTraining())
			return s_kPlayerBotMeleyTrain.parties;
		static int s_iCap = -1;
		if (s_iCap < 0)
			s_iCap = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MELEY_RUNS", 2, 0, 20);
		return s_iCap;
	}

	int GetPlayerBotMeleyTripCap()
	{
		if (s_kPlayerBotMeleyTrain.trips >= 0)
			return s_kPlayerBotMeleyTrain.trips;
		static int s_iTrips = -1;
		if (s_iTrips < 0)
			s_iTrips = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MELEY_TRIPS", 12, 0, 96);
		if (IsPlayerBotMeleyTraining())
			return std::min(96, std::max(s_iTrips, s_kPlayerBotMeleyTrain.parties * s_kPlayerBotMeleyTrain.size));
		return s_iTrips;
	}

	// The file, read when it changed (its mtime).
	void ReadPlayerBotMeleyTrainFile(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		static time_t s_tMtime = (time_t)-1;
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_MELEY_FILE_MS;
		struct stat st;
		const time_t mtime = stat(PLAYERBOT_MELEY_TRAIN_FILE, &st) == 0 ? st.st_mtime : (time_t)0;
		if (mtime == s_tMtime)
			return;
		s_tMtime = mtime;
		TPlayerBotMeleyTrain t;
		FILE* fp = mtime ? fopen(PLAYERBOT_MELEY_TRAIN_FILE, "r") : NULL;
		if (fp)
		{
			char line[160];
			while (fgets(line, sizeof(line), fp))
			{
				char cmd[32] = "";
				int a = 0, b = 0;
				const int got = sscanf(line, "%31s %d %d", cmd, &a, &b);
				if (got < 1 || cmd[0] == '#')
					continue;
				if (!strcmp(cmd, "parties") && got >= 2)
				{
					t.parties = std::max(0, std::min(20, a));
					if (got >= 3)
						t.size = std::max(5, std::min(playerbot_dgrun::PARTY_MAX, b));
				}
				else if (!strcmp(cmd, "trips") && got >= 2)
					t.trips = std::max(0, std::min(96, a));
				else
					sys_log(0, "BOT_MELEY: train unknown line=%s", line);
			}
			fclose(fp);
		}
		s_kPlayerBotMeleyTrain = t;
		sys_log(0, "BOT_MELEY: train load parties=%d size=%d trips=%d (cap runs=%d trips=%d) hosted=%d", t.parties, t.size, t.trips,
				GetPlayerBotMeleyRunCap(), GetPlayerBotMeleyTripCap(), IsPlayerBotMapHostedHere(PLAYERBOT_MELEY_MAP) ? 1 : 0);
	}

	// ------------------------------------------------------------ the need

	int CountPlayerBotMeleyMats(LPCHARACTER ch, int* each = NULL)
	{
		int sum = 0;
		for (int m = 0; m < 3; ++m)
		{
			const int n = ch && ch->IsItemLoaded() ? (int)ch->CountSpecifyItem(PLAYERBOT_MELEY_MATS[m]) : 0;
			if (each)
				each[m] = n;
			sum += n;
		}
		return sum;
	}

	// How many of the lair's materials the bot's GEAR2 helmet still lacks (one attempt), all three together.
	int GetPlayerBotMeleyLack(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return 0;
		int lack = 0;
		for (int m = 0; m < 3; ++m)
		{
			const int need = GetPlayerBotGear2MaterialNeed(ch, PLAYERBOT_MELEY_MATS[m]);
			if (need > 0)
				lack += std::max(0, need - (int)ch->CountSpecifyItem(PLAYERBOT_MELEY_MATS[m]));
		}
		return lack;
	}

	bool IsPlayerBotMeleyNeeder(LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_DROPKNOW_V1: or the drop knowledge sends it here for another item of its plans (no counter holds it)
		return GetPlayerBotMeleyLack(ch) > 0 || (ch && IsPlayerBotDropKnowDemander(ch->GetPlayerID(), FindPlayerBotMeleyDef()));
	}

	// The players' gates for a run now: the day's five, and (not in training) the bots' 3 h of the panel.
	bool IsPlayerBotMeleyDayOk(LPCHARACTER ch, const mt2009_dpanel::Def* panel, bool training)
	{
		const int def = FindPlayerBotMeleyDef();
		if (def < 0 || !ch)
			return false;
		const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
		if (info.iDaily > 0 && GetPlayerBotDgRunRunsToday(ch, info) >= info.iDaily)
			return false;
		if (!training && panel && mt2009_dpanel::CooldownLeft(ch, *panel) > 0)
			return false;
		return true;
	}

	// ------------------------------------------------------------ the visitors (the core of 356)

	bool IsPlayerBotMeleyVisitor(DWORD pid)
	{
		std::map<DWORD, TPlayerBotMeleyVisit>::const_iterator v = s_mapPlayerBotMeleyVisit.find(pid);
		return v != s_mapPlayerBotMeleyVisit.end() && !v->second.bReleased;
	}

	// playerbot_yohara_sungma.h, StartPlayerBotSungmaTradeHome: a trade trip of the reason "meley" arrived.
	void NotePlayerBotMeleyVisitorHome(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		TPlayerBotMeleyVisit& v = s_mapPlayerBotMeleyVisit[ch->GetPlayerID()];
		v = TPlayerBotMeleyVisit();
		v.dwSince = dwNow ? dwNow : 1;
		++s_kPlayerBotMeleyStats.visitsHome;
		int each[3];
		CountPlayerBotMeleyMats(ch, each);
		sys_log(0, "BOT_MELEY: visitor home pid=%u name=%s level=%u champion=%d empire=%u map=%ld lack=%d have=%d/%d/%d gold=%lld runs_today=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), (unsigned int)ch->GetEmpire(),
				ch->GetMapIndex(), GetPlayerBotMeleyLack(ch), each[0], each[1], each[2], (long long)ch->GetGold(),
				FindPlayerBotMeleyDef() >= 0 ? GetPlayerBotDgRunRunsToday(ch, PLAYERBOT_DGRUN_DEFS[FindPlayerBotMeleyDef()]) : 0);
	}

	void ReleasePlayerBotMeleyVisitor(DWORD pid, TPlayerBotMeleyVisit& v, const char* why, DWORD dwNow)
	{
		if (v.bReleased)
			return;
		v.bReleased = true;
		++s_kPlayerBotMeleyStats.visitsReleased;
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		sys_log(0, "BOT_MELEY: visitor released pid=%u name=%s why=%s runs=%d after_s=%u lack=%d", pid, ch ? ch->GetName() : "-", why,
				v.iRuns, (dwNow - v.dwSince) / 1000, ch ? GetPlayerBotMeleyLack(ch) : -1);
	}

	// playerbot_yohara_sungma.h, IsPlayerBotSungmaTradeHomeDone: true while the visitor stays for the lair.
	bool IsPlayerBotMeleyVisitHeld(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return false;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotMeleyVisit>::iterator v = s_mapPlayerBotMeleyVisit.find(pid);
		if (v == s_mapPlayerBotMeleyVisit.end() || v->second.bReleased)
			return false;
		if (IsPlayerBotOnDungeonRun(pid))
			return true;
		const char* why = NULL;
		const int def = FindPlayerBotMeleyDef();
		const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey("meley");
		const int runs = IsPlayerBotMeleyTraining() ? PLAYERBOT_MELEY_VISIT_RUNS_TRAIN : PLAYERBOT_MELEY_VISIT_RUNS;
		if (def < 0 || IsPlayerBotMeleyOff() || !IsPlayerBotDgRunOn(dwNow) || !IsPlayerBotMapHostedHere(PLAYERBOT_MELEY_MAP))
			why = "off";
		else if (dwNow - v->second.dwSince >= PLAYERBOT_MELEY_VISIT_MAX_MS)
			why = "timeout";
		else if (v->second.iRuns >= runs)
			why = "runs";
		else if (!IsPlayerBotMeleyNeeder(ch))
			why = "has_all";
		else if (!IsPlayerBotMeleyDayOk(ch, panel, IsPlayerBotMeleyTraining()))
			why = "day";
		if (!why)
			return true;
		ReleasePlayerBotMeleyVisitor(pid, v->second, why, dwNow);
		return false;
	}

	void PrunePlayerBotMeleyVisitors(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotMeleyVisit>::iterator v = s_mapPlayerBotMeleyVisit.begin(); v != s_mapPlayerBotMeleyVisit.end();)
		{
			// gone (back to its Sung Ma map, logged out) or released long ago
			if (!CHARACTER_MANAGER::instance().FindByPID(v->first) ||
					(v->second.bReleased && dwNow - v->second.dwSince >= PLAYERBOT_MELEY_VISIT_MAX_MS * 2))
				s_mapPlayerBotMeleyVisit.erase(v++);
			else
				++v;
		}
	}

	// ------------------------------------------------------------ the trips (a core without 356)

	int CountPlayerBotMeleyTripsOut(DWORD dwNow)
	{
		for (std::map<DWORD, DWORD>::iterator t = s_mapPlayerBotMeleyTripOut.begin(); t != s_mapPlayerBotMeleyTripOut.end();)
		{
			const DWORD away = dwNow - t->second;
			// back here (a minute after the handover took it) or lost
			if (away >= PLAYERBOT_MELEY_TRIP_LOST_MS || (away >= 60000 && CHARACTER_MANAGER::instance().FindByPID(t->first)))
				s_mapPlayerBotMeleyTripOut.erase(t++);
			else
				++t;
		}
		return (int)s_mapPlayerBotMeleyTripOut.size();
	}

	// playerbot_yohara_sungma.h, GetPlayerBotSungmaTradeReason: a Sung Ma resident goes home for the lair now.
	bool WantsPlayerBotMeleyTrip(LPCHARACTER ch, DWORD dwArrived, DWORD dwNow)
	{
		if (!ch || IsPlayerBotMeleyOff() || IsPlayerBotMapHostedHere(PLAYERBOT_MELEY_MAP) || (int)ch->GetLevel() < PLAYERBOT_MELEY_MIN_LEVEL)
			return false;
		const int cap = GetPlayerBotMeleyTripCap();
		if (cap <= 0 || dwNow - dwArrived < PLAYERBOT_MELEY_VISIT_MIN_STAY_MS)
			return false;
		std::map<DWORD, DWORD>::const_iterator last = s_mapPlayerBotMeleyTripLast.find(ch->GetPlayerID());
		if (last != s_mapPlayerBotMeleyTripLast.end() && dwNow - last->second < PLAYERBOT_MELEY_TRIP_GAP_MS)
			return false;
		if (!ch->GetWear(WEAR_WEAPON) || !ch->GetWear(WEAR_BODY) || !IsPlayerBotMeleyNeeder(ch))
			return false;
		if (!IsPlayerBotMeleyDayOk(ch, mt2009_dpanel::FindKey("meley"), IsPlayerBotMeleyTraining()))
			return false;
		if (CountPlayerBotMeleyTripsOut(dwNow) >= cap)
		{
			PlayerBotLogThrottled("meley_trip_cap", dwNow, "BOT_MELEY: trip waits pid=%u name=%s away=%u cap=%d", ch->GetPlayerID(),
					ch->GetName(), (unsigned int)s_mapPlayerBotMeleyTripOut.size(), cap);
			return false;
		}
		return true;
	}

	// playerbot_yohara_sungma.h, StartPlayerBotSungmaTradeTrip: the handover asked for.
	void NotePlayerBotMeleyTripOut(LPCHARACTER ch, DWORD dwNow)
	{
		const DWORD at = dwNow ? dwNow : 1;
		s_mapPlayerBotMeleyTripOut[ch->GetPlayerID()] = at;
		s_mapPlayerBotMeleyTripLast[ch->GetPlayerID()] = at;
		++s_kPlayerBotMeleyStats.tripsOut;
		int each[3];
		CountPlayerBotMeleyMats(ch, each);
		sys_log(0, "BOT_MELEY: trip out pid=%u name=%s level=%u champion=%d empire=%u map=%ld lack=%d have=%d/%d/%d away=%u cap=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch),
				(unsigned int)ch->GetEmpire(), ch->GetMapIndex(), GetPlayerBotMeleyLack(ch), each[0], each[1], each[2],
				(unsigned int)s_mapPlayerBotMeleyTripOut.size(), GetPlayerBotMeleyTripCap());
	}

	// ------------------------------------------------------------ the loot

	// A member's lair materials beyond its own helmet's need, to the member who lacks most (one material a call).
	int SharePlayerBotMeleyLoot(const TPlayerBotDgRun& run, const char* when)
	{
		std::vector<LPCHARACTER> in;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (c && c->IsItemLoaded() && !c->IsDead())
				in.push_back(c);
		}
		int moved = 0;
		for (int m = 0; m < 3; ++m)
		{
			const DWORD vnum = PLAYERBOT_MELEY_MATS[m];
			for (int guard = 0; guard < 8; ++guard)
			{
				LPCHARACTER giver = NULL, taker = NULL;
				int spare = 0, lack = 0;
				for (size_t i = 0; i < in.size(); ++i)
				{
					const int have = (int)in[i]->CountSpecifyItem(vnum);
					const int need = GetPlayerBotGear2MaterialNeed(in[i], vnum);
					if (have - need > spare)
					{
						spare = have - need;
						giver = in[i];
					}
					if (need - have > lack)
					{
						lack = need - have;
						taker = in[i];
					}
				}
				if (!giver || !taker || giver == taker || spare <= 0 || lack <= 0)
					break;
				const int n = std::min(spare, lack);
				giver->RemoveSpecifyItem(vnum, (ITEM_COUNT)n);
				LPITEM given = taker->AutoGiveItem(vnum, (ITEM_COUNT)n, -1, false);
				moved += n;
				s_kPlayerBotMeleyStats.shared += (unsigned int)n;
				sys_log(0, "BOT_MELEY: share run=%d when=%s vnum=%u count=%d from=%s to=%s lack_to=%d ok=%d", run.iId, when,
						(unsigned int)vnum, n, giver->GetName(), taker->GetName(), lack, given ? 1 : 0);
			}
		}
		return moved;
	}

	// ------------------------------------------------------------ the run (playerbot_dungeon_runs.h's hooks)

	bool IsPlayerBotMeleyPlannedRun(int runId)
	{
		return s_mapPlayerBotMeleyRuns.count(runId) != 0;
	}

	// A member of a run this planner called (held at the call as the YDG / Erebu trainees are).
	bool IsPlayerBotMeleyRunHeld(DWORD pid)
	{
		std::map<DWORD, TPlayerBotDgRunBot>::const_iterator b = s_mapPlayerBotDgRunBots.find(pid);
		return b != s_mapPlayerBotDgRunBots.end() && IsPlayerBotMeleyPlannedRun(b->second.iRun);
	}

	void NotePlayerBotMeleyRunStart(const TPlayerBotDgRun& run)
	{
		TPlayerBotMeleyRun& mr = s_mapPlayerBotMeleyRuns[run.iId];
		mr.start.clear();
		++s_kPlayerBotMeleyStats.entered;
		static const char* const cls[4] = { "W", "N", "S", "Sh" };
		std::string mix;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			MakePlayerBotYdgRoom(c, "meley_start");
			BuffPlayerBotYdgMember(c);
			std::vector<int>& v = mr.start[run.members[i]];
			v.assign(3, 0);
			CountPlayerBotMeleyMats(c, &v[0]);
			char buf[96];
			snprintf(buf, sizeof(buf), "%s%s:%s%d/c%d/lack%d%s", mix.empty() ? "" : ",", c->GetName(), cls[c->GetJob() % 4],
					(int)c->GetLevel(), (int)c->GetConquerorLevel(), GetPlayerBotMeleyLack(c),
					IsPlayerBotMeleyVisitor(run.members[i]) ? "/v" : "");
			if (mix.size() < 400)
				mix += buf;
		}
		sys_log(0, "BOT_MELEY: run start run=%d instance=%ld empire=%u train=%d members=%u mix=%s", run.iId, run.lInstance,
				(unsigned int)run.bEmpire, mr.bTrain ? 1 : 0, (unsigned int)run.members.size(), mix.c_str());
	}

	// Every second of a run inside (UpdatePlayerBotDgRun): the materials shared now and then, a bag cell kept.
	void UpdatePlayerBotMeleyInside(TPlayerBotDgRun& run, DWORD dwNow)
	{
		std::map<int, TPlayerBotMeleyRun>::iterator mr = s_mapPlayerBotMeleyRuns.find(run.iId);
		if (mr == s_mapPlayerBotMeleyRuns.end())
		{
			// a run called by the test file or a recruit of the clock's (not this planner's): its record now
			mr = s_mapPlayerBotMeleyRuns.insert(std::make_pair(run.iId, TPlayerBotMeleyRun())).first;
		}
		// the night of 5/6 November: a progress line every 2 minutes (the stage, the statues' health and locks, the eggs)
		{
			static std::map<int, DWORD> s_next;
			DWORD& at = s_next[run.iId];
			LPDUNGEON d = run.lInstance ? CDungeonManager::instance().FindByMapIndex(run.lInstance) : NULL;
			if (d && (at == 0 || (int)(dwNow - at) >= 0))
			{
				at = dwNow + 120 * 1000;
				std::string st;
				for (int i = 1; i <= 4; ++i)
				{
					char key[16], buf[32];
					snprintf(key, sizeof(key), "stone%d", i);
					const int pct = d->IsUniqueDead(key) ? -1 : (int)d->GetUniqueHpPerc(key);
					snprintf(key, sizeof(key), "lock%d", i);
					snprintf(buf, sizeof(buf), "%s%d%s", st.empty() ? "" : ",", pct, d->GetFlag(key) == 1 ? "L" : "");
					st += buf;
				}
				int alive = 0, inside = 0;
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (c && c->GetMapIndex() == run.lInstance)
					{
						++inside;
						alive += c->IsDead() ? 0 : 1;
					}
				}
				const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
				int eggs = 0, idall = 0, others = 0;
				for (size_t i = 0; i < scan.foes.size(); ++i)
				{
					const DWORD r = scan.foes[i].dwRace;
					eggs += r == 20422 ? 1 : 0;
					idall += r == 6116 ? 1 : 0;
					others += (r != 20422 && r != 6116 && r != 6118) ? 1 : 0;
				}
				sys_log(0, "BOT_MELEY: progress run=%d stage=%d statues=%s eggs=%d idall=%d others=%d inside=%d alive=%d deaths=%d",
						run.iId, d->GetFlag("stage"), st.c_str(), eggs, idall, others, inside, alive, run.iDeaths);
			}
		}
		if (mr->second.dwNextShare != 0 && (int)(dwNow - mr->second.dwNextShare) < 0)
			return;
		mr->second.dwNextShare = dwNow + PLAYERBOT_MELEY_SHARE_MS;
		mr->second.iShared += SharePlayerBotMeleyLoot(run, "inside");
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (c && c->IsItemLoaded() && !c->IsDead() && c->GetEmptyInventory(1) < 0)
				MakePlayerBotYdgRoom(c, "meley_loot");
		}
	}

	// The run closed (ClosePlayerBotDgRun, the members still the run's): the last share, the bonuses off, the gain
	// logged, the visitors' count; the rest after it (a training run's is short).
	DWORD NotePlayerBotMeleyRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS, DWORD rest)
	{
		std::map<int, TPlayerBotMeleyRun>::iterator mr = s_mapPlayerBotMeleyRuns.find(run.iId);
		const bool train = mr != s_mapPlayerBotMeleyRuns.end() && mr->second.bTrain;
		const int shared = SharePlayerBotMeleyLoot(run, "end") + (mr != s_mapPlayerBotMeleyRuns.end() ? mr->second.iShared : 0);
		int gained[3] = { 0, 0, 0 }, needersLeft = 0, visitors = 0;
		std::string per;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			const DWORD pid = run.members[i];
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!c)
				continue;
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_POISON);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_BLEED);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MONSTER);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_HP);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_CRIT);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_PIERCE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MOVE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_ATTSPD);
			int now[3];
			CountPlayerBotMeleyMats(c, now);
			if (mr != s_mapPlayerBotMeleyRuns.end())
			{
				std::map<DWORD, std::vector<int> >::const_iterator s = mr->second.start.find(pid);
				for (int m = 0; m < 3 && s != mr->second.start.end() && s->second.size() == 3; ++m)
					gained[m] += now[m] - s->second[m];
			}
			const int lack = GetPlayerBotMeleyLack(c);
			needersLeft += lack > 0 ? 1 : 0;
			char buf[64];
			snprintf(buf, sizeof(buf), "%s%s:%d/%d/%d", per.empty() ? "" : ",", c->GetName(), now[0], now[1], now[2]);
			if (per.size() < 400)
				per += buf;
			std::map<DWORD, TPlayerBotMeleyVisit>::iterator v = s_mapPlayerBotMeleyVisit.find(pid);
			if (v != s_mapPlayerBotMeleyVisit.end() && !v->second.bReleased)
			{
				++visitors;
				if (entered)
					++v->second.iRuns;
			}
		}
		const bool won = run.dwFinishedAt != 0;
		if (won)
			++s_kPlayerBotMeleyStats.won;
		const int sum = std::max(0, gained[0]) + std::max(0, gained[1]) + std::max(0, gained[2]);
		s_kPlayerBotMeleyStats.mats += (unsigned int)sum;
		sys_log(0, "BOT_MELEY: run end run=%d result=%s won=%d entered=%d took_s=%u stage=%d deaths=%d train=%d members=%u visitors=%d "
				"gained=%d/%d/%d shared=%d needers_left=%d have=%s",
				run.iId, result ? result : "-", won ? 1 : 0, entered ? 1 : 0, tookS, run.iStage, run.iDeaths, train ? 1 : 0,
				(unsigned int)run.members.size(), visitors, gained[0], gained[1], gained[2], shared, needersLeft, per.c_str());
		if (mr != s_mapPlayerBotMeleyRuns.end())
			s_mapPlayerBotMeleyRuns.erase(mr);
		if (train || visitors > 0)
			return PLAYERBOT_MELEY_TRAIN_REST_MIN_MS + (DWORD)number(0, (int)PLAYERBOT_MELEY_TRAIN_REST_SPREAD_MS);
		return rest;
	}

	// ------------------------------------------------------------ the planner (the core of 356)

	struct TPlayerBotMeleyCand
	{
		DWORD pid;
		long long score;
		int job;
		bool healer, needer, visitor;
	};

	struct TPlayerBotMeleyPool
	{
		std::vector<TPlayerBotMeleyCand> cands[4];
		int band, needers, visitors, inRun, resting, refused, day, share, trainee;
		std::map<std::string, int> why;
		TPlayerBotMeleyPool() : band(0), needers(0), visitors(0), inRun(0), resting(0), refused(0), day(0), share(0), trainee(0) {}
	};

	void GatherPlayerBotMeleyPool(TPlayerBotMeleyPool& pool, DWORD dwNow)
	{
		const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey("meley");
		const bool training = IsPlayerBotMeleyTraining();
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			const DWORD pid = it->first;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch || (int)ch->GetLevel() < PLAYERBOT_MELEY_MIN_LEVEL || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
				continue;
			++pool.band;
			const bool visitor = IsPlayerBotMeleyVisitor(pid);
			const bool needer = IsPlayerBotMeleyNeeder(ch);
			pool.visitors += visitor ? 1 : 0;
			pool.needers += needer ? 1 : 0;
			if (s_mapPlayerBotDgRunBots.count(pid))
			{
				++pool.inRun;
				continue;
			}
			std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotDgRunRest.find(pid);
			if (rest != s_mapPlayerBotDgRunRest.end() && (int)(rest->second - dwNow) > 0)
			{
				++pool.resting;
				continue;
			}
			if (IsPlayerBotYoharaHydraResident(pid) || IsPlayerBotYoharaSzcResident(pid) || IsPlayerBotErebuTrainee(pid) ||
					IsPlayerBotYdgTrainee(pid))
			{
				++pool.trainee;
				continue;
			}
			const char* refusal = GetPlayerBotDgRunRefusal(ch, it->second, dwNow);
			if (refusal)
			{
				++pool.refused;
				++pool.why[refusal];
				continue;
			}
			if (!IsPlayerBotMeleyDayOk(ch, panel, training))
			{
				++pool.day;
				continue;
			}
			// the clock's share by personality - not for those who need the lair or came for it
			if (!visitor && !needer && !training && !playerbot_dgrun::IsDungeonGoer(pid, GetPlayerBotDgRunShare(it->second)))
			{
				++pool.share;
				continue;
			}
			TPlayerBotMeleyCand c;
			c.pid = pid;
			c.score = ScorePlayerBotYdg(ch) + (needer ? 1000000000LL : 0LL) + (visitor ? 2000000000LL : 0LL);
			c.job = ch->GetJob() % 4;
			c.healer = c.job == JOB_SHAMAN && ch->GetSkillGroup() != 0;
			c.needer = needer;
			c.visitor = visitor;
			pool.cands[ch->GetEmpire()].push_back(c);
		}
		for (int e = 1; e <= 3; ++e)
			std::sort(pool.cands[e].begin(), pool.cands[e].end(), [](const TPlayerBotMeleyCand& a, const TPlayerBotMeleyCand& b)
					{ return a.score > b.score; });
	}

	void LogPlayerBotMeleyPool(const TPlayerBotMeleyPool& pool, const char* when)
	{
		std::string why;
		for (std::map<std::string, int>::const_iterator w = pool.why.begin(); w != pool.why.end(); ++w)
		{
			char buf[48];
			snprintf(buf, sizeof(buf), "%s%s:%d", why.empty() ? "" : ",", w->first.c_str(), w->second);
			why += buf;
		}
		int healers[4] = { 0, 0, 0, 0 }, needers[4] = { 0, 0, 0, 0 };
		for (int e = 1; e <= 3; ++e)
			for (size_t i = 0; i < pool.cands[e].size(); ++i)
			{
				healers[e] += pool.cands[e][i].healer ? 1 : 0;
				needers[e] += pool.cands[e][i].needer ? 1 : 0;
			}
		const int def = FindPlayerBotMeleyDef();
		sys_log(0, "BOT_MELEY: pool when=%s free=%u/%u/%u healers=%d/%d/%d needers_free=%d/%d/%d band95=%d needers=%d visitors=%d in_run=%d "
				"resting=%d trainees=%d day_or_cd=%d share=%d refused=%d (%s) running=%d cap=%d train=%d size=%d",
				when, (unsigned int)pool.cands[1].size(), (unsigned int)pool.cands[2].size(), (unsigned int)pool.cands[3].size(),
				healers[1], healers[2], healers[3], needers[1], needers[2], needers[3], pool.band, pool.needers, pool.visitors,
				pool.inRun, pool.resting, pool.trainee, pool.day, pool.share, pool.refused, why.empty() ? "-" : why.c_str(),
				def >= 0 ? CountPlayerBotDgRuns(def) : 0, GetPlayerBotMeleyRunCap(), s_kPlayerBotMeleyTrain.parties,
				s_kPlayerBotMeleyTrain.size);
	}

	// One kingdom's party: a healing Shaman, then by the order (visitors, needers, the strongest), no class over a third.
	bool DrawPlayerBotMeleyParty(std::vector<TPlayerBotMeleyCand>& v, int size, std::vector<TPlayerBotMeleyCand>& party)
	{
		party.clear();
		for (size_t i = 0; i < v.size(); ++i)
			if (v[i].healer)
			{
				party.push_back(v[i]);
				v.erase(v.begin() + i);
				break;
			}
		if (party.empty())
			return false;
		int perJob[4] = { 0, 0, 0, 0 };
		++perJob[party[0].job & 3];
		const int cap = std::max(2, (size + 2) / 3);
		for (size_t i = 0; i < v.size() && (int)party.size() < size;)
		{
			if (perJob[v[i].job & 3] >= cap)
			{
				++i;
				continue;
			}
			++perJob[v[i].job & 3];
			party.push_back(v[i]);
			v.erase(v.begin() + i);
		}
		// the leader: the strongest who is no Shaman (the order without the bonus of the need)
		size_t lead = 0;
		long long best = -1;
		for (size_t i = 0; i < party.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(party[i].pid);
			const long long s = c ? ScorePlayerBotYdg(c) : 0;
			if (party[i].job != JOB_SHAMAN && s > best)
			{
				best = s;
				lead = i;
			}
		}
		std::swap(party[0], party[lead]);
		return true;
	}

	int CallPlayerBotMeleyParty(int def, BYTE empire, const std::vector<TPlayerBotMeleyCand>& party, size_t poolSize, DWORD dwNow,
			bool forced)
	{
		TPlayerBotDgRunSlot slot;
		slot.lvMin = PLAYERBOT_MELEY_MIN_LEVEL;
		slot.lvMax = gPlayerMaxLevel;
		slot.partyMin = playerbot_dgrun::RuleFor("meley").startMin;
		slot.partyMax = playerbot_dgrun::PARTY_MAX;
		slot.panel = mt2009_dpanel::FindKey("meley");
		slot.ok = slot.empireOk[empire] = true;
		TPlayerBotLfgPlace& place = slot.place[empire];
		if (!ResolvePlayerBotLfgPlace("meley", 0, empire, PLAYERBOT_MELEY_MIN_LEVEL, place))
		{
			// the dungeon panel's entrance: Straznik Smokow Dolnarr on Doyyumhwaji (dungeon_info.txt, 5972 6997)
			place = TPlayerBotLfgPlace();
			place.key = "meley";
			place.map = 62;
			place.x = 597200;
			place.y = 699700;
		}
		place.lvMin = slot.lvMin;
		place.lvMax = slot.lvMax;
		std::vector<playerbot_dgrun::TCand> picked;
		int needers = 0, visitors = 0;
		for (size_t i = 0; i < party.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(party[i].pid);
			if (!c)
				continue;
			picked.push_back(playerbot_dgrun::TCand(party[i].pid, c->GetLevel(), party[i].job, 10, party[i].healer));
			needers += party[i].needer ? 1 : 0;
			visitors += party[i].visitor ? 1 : 0;
		}
		const int id = OpenPlayerBotDgRun(def, empire, picked, slot, poolSize, dwNow, forced ? "test" : "meley_plan");
		if (id == 0)
			return 0;
		TPlayerBotMeleyRun& mr = s_mapPlayerBotMeleyRuns[id];
		mr.bTrain = IsPlayerBotMeleyTraining();
		mr.iNeeders = needers;
		mr.iVisitors = visitors;
		++s_kPlayerBotMeleyStats.called;
		sys_log(0, "BOT_MELEY: called run=%d empire=%u party=%u needers=%d visitors=%d pool=%u train=%d", id, (unsigned int)empire,
				(unsigned int)picked.size(), needers, visitors, (unsigned int)poolSize, mr.bTrain ? 1 : 0);
		return id;
	}

	void LogPlayerBotMeleyStatus()
	{
		const TPlayerBotMeleyStats& s = s_kPlayerBotMeleyStats;
		sys_log(0, "BOT_MELEY: status hosted=%d running=%d cap=%d train=%d size=%d trips_cap=%d trips_out=%u visitors=%u called=%u "
				"entered=%u won=%u mats=%u shared=%u trips=%u visits_home=%u visits_released=%u off=%d",
				IsPlayerBotMapHostedHere(PLAYERBOT_MELEY_MAP) ? 1 : 0,
				FindPlayerBotMeleyDef() >= 0 ? CountPlayerBotDgRuns(FindPlayerBotMeleyDef()) : 0, GetPlayerBotMeleyRunCap(),
				s_kPlayerBotMeleyTrain.parties, s_kPlayerBotMeleyTrain.size, GetPlayerBotMeleyTripCap(),
				(unsigned int)s_mapPlayerBotMeleyTripOut.size(), (unsigned int)s_mapPlayerBotMeleyVisit.size(), s.called, s.entered,
				s.won, s.mats, s.shared, s.tripsOut, s.visitsHome, s.visitsReleased, IsPlayerBotMeleyOff() ? 1 : 0);
	}

	// Every PLAYERBOT_MELEY_PLAN_MS (ManagePlayerBotDungeonRuns) - forced: the test file's "now meley".
	void PlanPlayerBotMeleyRuns(DWORD dwNow, bool forced)
	{
		static DWORD s_dwNext = 0, s_dwNextStatus = 0, s_dwStart = 0;
		ReadPlayerBotMeleyTrainFile(dwNow);
		if (s_dwStart == 0)
			s_dwStart = dwNow ? dwNow : 1;
		if (!forced && s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_MELEY_PLAN_MS;
		PrunePlayerBotMeleyVisitors(dwNow);
		const int def = FindPlayerBotMeleyDef();
		const bool hosted = def >= 0 && IsPlayerBotMapHostedHere(PLAYERBOT_MELEY_MAP) && SECTREE_MANAGER::instance().GetMap(PLAYERBOT_MELEY_MAP);
		if (s_dwNextStatus == 0 || (int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_MELEY_STATUS_MS;
			LogPlayerBotMeleyStatus();
			if (hosted)
			{
				TPlayerBotMeleyPool pool;
				GatherPlayerBotMeleyPool(pool, dwNow);
				LogPlayerBotMeleyPool(pool, "status");
			}
		}
		if (!hosted)
			return;
		const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey("meley");
		if (!panel || mt2009_dpanel::Hidden(*panel) || !IsPlayerBotDgRunOn(dwNow) || IsPlayerBotMeleyOff())
		{
			if (forced)
				sys_log(0, "BOT_MELEY: no call (test) - panel=%d hidden=%d on=%d off_flag=%d", panel ? 1 : 0,
						panel && mt2009_dpanel::Hidden(*panel) ? 1 : 0, IsPlayerBotDgRunOn(dwNow) ? 1 : 0, IsPlayerBotMeleyOff() ? 1 : 0);
			return;
		}
		// the world settles first (the bots log in, the YDG and Erebu trainings pick theirs)
		if (!forced && dwNow - s_dwStart < 3 * 60 * 1000)
			return;
		const int cap = GetPlayerBotMeleyRunCap();
		int running = CountPlayerBotDgRuns(def);
		if (running >= cap && !forced)
			return;
		TPlayerBotMeleyPool pool;
		GatherPlayerBotMeleyPool(pool, dwNow);
		const int size = IsPlayerBotMeleyTraining() ? s_kPlayerBotMeleyTrain.size : 6;
		const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor("meley");
		const int least = std::max(rule.startMin, std::min(size, rule.preferMin));
		int calls = 0;
		while ((running < cap || (forced && calls == 0)) && calls < PLAYERBOT_MELEY_CALLS_A_PASS)
		{
			// the kingdom with the most visitors and needers free, then the most free
			int e = 0;
			long long best = -1;
			for (int k = 1; k <= 3; ++k)
			{
				if ((int)pool.cands[k].size() < least)
					continue;
				long long w = (long long)pool.cands[k].size();
				for (size_t i = 0; i < pool.cands[k].size(); ++i)
					w += (pool.cands[k][i].visitor ? 1000 : 0) + (pool.cands[k][i].needer ? 100 : 0);
				if (w > best)
				{
					best = w;
					e = k;
				}
			}
			if (e == 0)
				break;
			const size_t poolSize = pool.cands[e].size();
			std::vector<TPlayerBotMeleyCand> party;
			if (!DrawPlayerBotMeleyParty(pool.cands[e], size, party) || (int)party.size() < least)
			{
				// no healing Shaman, or the classes' third left too few: this kingdom waits
				pool.cands[e].clear();
				continue;
			}
			if (!CallPlayerBotMeleyParty(def, (BYTE)e, party, poolSize, dwNow, forced))
				break;
			++running;
			++calls;
		}
		if (calls == 0 && (forced || running < cap))
		{
			if (forced)
				LogPlayerBotMeleyPool(pool, "test_no_call");
			else
			{
				static DWORD s_dwNextShort = 0;
				if (s_dwNextShort == 0 || (int)(dwNow - s_dwNextShort) >= 0)
				{
					s_dwNextShort = dwNow + PLAYERBOT_MELEY_STATUS_MS;
					LogPlayerBotMeleyPool(pool, "short");
				}
			}
		}
	}

	// The operator's lines (RunPlayerBotDgRunTestFile): meley_status.
	bool RunPlayerBotMeleyTestLine(const char* cmd, DWORD dwNow)
	{
		if (strcmp(cmd, "meley_status"))
			return false;
		LogPlayerBotMeleyStatus();
		TPlayerBotMeleyPool pool;
		GatherPlayerBotMeleyPool(pool, dwNow);
		LogPlayerBotMeleyPool(pool, "test");
		return true;
	}
}

#endif
