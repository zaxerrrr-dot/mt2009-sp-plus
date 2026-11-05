#ifndef __INC_METIN2_PLAYERBOT_DGRUN_EREBU_H__
#define __INC_METIN2_PLAYERBOT_DGRUN_EREBU_H__

// MT2009_PLUS_BOT_EREBU_V1 - Erebu (353, erebu.quest), Jotun Thrym's dungeon in Zaklety Las, as a bots' run.
//
// The owner, 5 November 2026: "nauczmy boty korzystac z dungeonow Yohary" - and the same night: the bots must
// learn Erebu on the test server till 07:00, in fixed parties of five and more of the bots best suited for it;
// their gear may be better (the test server only), the dungeon is never made weaker.
//
// The dungeon (erebu.quest): Przywodca Strazy Lasu (20412, Zaklety Las 615,108) lets a party of 5-8 in, each of
// level 95 with a Kamien Driad (30613 - the forest's seven missions at Badacz Lasu, zaklety_las.quest; used at
// the way in); inside Bagjanamu (6408, level 120), a minute after him Jotun Thrym (6192, 123 - he calls the
// Uzdrowiciele Ochao, 6409); 30 minutes; after the win 3 minutes for the loot, then everybody out; again 2 hours
// after the end (erebu.end). The quest's stage flag (1 Bagjanamu, 2 Thrym, 3 won) and its erebu_dgrun timer are
// this run's (the quest's MT2009_PLUS_BOT_EREBU_V1 lines).
//
// The bots' part (the row "erebu" of PLAYERBOT_DGRUN_DEFS, kind DGRUN_KIND_EREBU):
//   - the clock's runs as every dungeon's: the band 95-110 (the rule's), six called, five to go in, a Shaman
//     that can heal always, the 2 hours of erebu.end as the bots' rest, two runs at once on the core hosting 353
//     (game3) - none while the training below is on;
//   - the ticket: a Kamien Driad from the bag at the way in; a bot with none did the forest's missions for it
//     first (it is given one, logged "stone given source=forest_missions");
//   - inside: the leader goes for the Uzdrowiciele while they stand, else Bagjanamu, else Thrym; the boss's
//     health is never held for a bots' Erebu (HoldPlayerBotArzDgBossRegen is left out - the dungeon as it is).
//
// The training (MT2009_PLUS_BOT_EREBU_TRAIN_V1) - fixed parties that run Erebu again and again:
//   - the event flag m2_bot_erebu_train N (a GM's /e, the panel's flags): N parties on each core that hosts 353
//     (m2_bot_erebu_train_ch C: only on channel C), formed of the free bots of this core best suited - level 95+,
//     a weapon and an armour on, by level, Champion level, health and attack - one kingdom a party, a healing
//     Shaman in each, a Warrior first as its leader, no class over its third; m2_bot_erebu_train_size the
//     party's size (6, 5-8); m2_bot_erebu_train_cd 1 keeps the players' 2 hours between the runs (default: a
//     party goes again after PLAYERBOT_EREBU_TRAIN_REST_MS); m2_bot_erebu_train_runs the runs at once (N);
//     0 dissolves the parties (the runs under way end as they would);
//   - the operator's lines in playerbot_dungeon_runs_test: "erebu_party <pid,pid,...>" a party of these bots
//     (the first leads), "erebu_clear" every party gone, "erebu_status" the parties and their runs;
//   - a party is called whole when all of it is free (or after PLAYERBOT_EREBU_TRAIN_WAIT_MS with five), out of
//     the core's cap of runs; a member gone (logged out, another core) for PLAYERBOT_EREBU_TRAIN_REFILL_MS is
//     replaced by the best free bot of its kingdom;
//   - the trainees answer no other call (the clock's, the replacements').
//
// The log: PLAYERBOT_EREBU (party formed / replaced / dissolved, run start with the party's mix and levels, boss
// up / down with the seconds, boss health every minute, run end: result, seconds, stage, deaths, wipes, the
// bosses' health, the loot taken - the items and the yang the members gained), the file playerbot_erebu_runs.tsv
// (one row a run), and the BOT_DGRUN lines of every run.
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h, whose state it uses.

namespace
{
	const DWORD PLAYERBOT_EREBU_STONE = 30613;		// Kamien Driad
	const DWORD PLAYERBOT_EREBU_BAGJANAMU = 6408;
	const DWORD PLAYERBOT_EREBU_THRYM = 6192;
	const DWORD PLAYERBOT_EREBU_HEALER = 6409;		// Uzdrowiciel Ochao (Thrym's SummonVnum)
	const long PLAYERBOT_EREBU_MAP = 353;
	// Przywodca Strazy Lasu (cells off the map's base 7680,14080: 611,107 - the dungeon panel's entrance)
	const long PLAYERBOT_EREBU_GATHER_X = (7680 + 611) * 100;
	const long PLAYERBOT_EREBU_GATHER_Y = (14080 + 107) * 100;
	const int PLAYERBOT_EREBU_MIN_LEVEL = 95;
	const DWORD PLAYERBOT_EREBU_TRAIN_PLAN_MS = 10000;
	const DWORD PLAYERBOT_EREBU_TRAIN_WAIT_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_EREBU_TRAIN_REFILL_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_EREBU_TRAIN_REST_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_EREBU_TRAIN_REST_SPREAD_MS = 60 * 1000;
	const DWORD PLAYERBOT_EREBU_STATUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_EREBU_HP_LOG_MS = 60 * 1000;
	const char* const PLAYERBOT_EREBU_RUNS_FILE = "playerbot_erebu_runs.tsv";

	struct TPlayerBotErebuParty
	{
		int iId;
		BYTE bEmpire;
		std::vector<DWORD> pids;	// the leader first
		DWORD dwWaitSince, dwShortSince, dwRestUntil;
		int iRun;			// its run now, or 0
		int iRuns, iWins, iDeaths;
		DWORD dwBestS;
		bool bManual;			// the operator's pids
		TPlayerBotErebuParty() : iId(0), bEmpire(0), dwWaitSince(0), dwShortSince(0), dwRestUntil(0), iRun(0), iRuns(0),
				iWins(0), iDeaths(0), dwBestS(0), bManual(false) {}
	};

	// One run's own record: its party, the members' bags at the way in, the bosses seen.
	struct TPlayerBotErebuRun
	{
		int iParty;
		std::map<DWORD, std::map<DWORD, int> > bags;
		std::map<DWORD, long long> gold;
		DWORD dwBagjanamuUp, dwBagjanamuDown, dwThrymUp, dwThrymDown, dwNextHpLog;
		int iBagjanamuLow, iThrymLow, iHealersSeen;
		std::set<DWORD> healerVids;
		TPlayerBotErebuRun() : iParty(0), dwBagjanamuUp(0), dwBagjanamuDown(0), dwThrymUp(0), dwThrymDown(0), dwNextHpLog(0),
				iBagjanamuLow(100), iThrymLow(100), iHealersSeen(0) {}
	};

	std::map<int, TPlayerBotErebuParty> s_mapPlayerBotErebuParties;
	std::map<DWORD, int> s_mapPlayerBotErebuTrainee;	// pid -> party
	std::map<int, TPlayerBotErebuRun> s_mapPlayerBotErebuRuns;	// run id -> record (every Erebu run)
	int s_iPlayerBotErebuNextParty = 1;

	// ------------------------------------------------------------ small things

	int GetPlayerBotErebuFlag(const char* name)
	{
		return quest::CQuestManager::instance().GetEventFlag(name);
	}

	int FindPlayerBotErebuDef()
	{
		for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
			if (PLAYERBOT_DGRUN_DEFS[i].bKind == DGRUN_KIND_EREBU)
				return i;
		return -1;
	}

	// The training wanted on this core: the parties asked for (0: none).
	int GetPlayerBotErebuTrainWanted()
	{
		const int n = GetPlayerBotErebuFlag("m2_bot_erebu_train");
		if (n <= 0)
			return 0;
		const int ch = GetPlayerBotErebuFlag("m2_bot_erebu_train_ch");
		if (ch > 0 && ch != (int)g_bChannel)
			return 0;
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_EREBU_MAP))
			return 0;
		return std::min(n, 40);
	}

	bool IsPlayerBotErebuTraining()
	{
		return GetPlayerBotErebuTrainWanted() > 0 || !s_mapPlayerBotErebuParties.empty();
	}

	bool IsPlayerBotErebuTrainee(DWORD pid)
	{
		return !s_mapPlayerBotErebuTrainee.empty() && s_mapPlayerBotErebuTrainee.count(pid) != 0;
	}

	bool IsPlayerBotErebuTrainRun(int runId)
	{
		std::map<int, TPlayerBotErebuRun>::const_iterator r = s_mapPlayerBotErebuRuns.find(runId);
		return r != s_mapPlayerBotErebuRuns.end() && r->second.iParty > 0;
	}

	int GetPlayerBotErebuTrainSize()
	{
		const int s = GetPlayerBotErebuFlag("m2_bot_erebu_train_size");
		return s <= 0 ? 6 : std::max(5, std::min(s, playerbot_dgrun::PARTY_MAX));
	}

	const char* PlayerBotErebuJob(LPCHARACTER c)
	{
		static const char* const cls[4] = { "W", "N", "S", "Sh" };
		return c ? cls[c->GetJob() % 4] : "?";
	}

	// A bot's worth for Erebu: level, Champion level, health, attack and defence.
	long long ScorePlayerBotErebu(LPCHARACTER ch)
	{
		return (long long)ch->GetLevel() * 100000LL + (long long)GetPlayerBotChampionLevel(ch) * 20000LL +
				(long long)ch->GetMaxHP() / 10 + (long long)ch->GetPoint(POINT_ATT_GRADE) * 4 + ch->GetPoint(POINT_DEF_GRADE) * 2;
	}

	bool IsPlayerBotErebuHealer(LPCHARACTER ch)
	{
		return ch && ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0;
	}

	// ------------------------------------------------------------ the dungeon's own

	// The leader's goals: the Uzdrowiciele while they stand, else the stage's boss.
	void GetPlayerBotErebuObjectives(LPDUNGEON d, const TPlayerBotArzDgScan& scan, std::vector<DWORD>& out)
	{
		bool healers = false;
		for (size_t i = 0; i < scan.foes.size() && !healers; ++i)
			healers = scan.foes[i].dwRace == PLAYERBOT_EREBU_HEALER;
		if (healers)
			out.push_back(PLAYERBOT_EREBU_HEALER);
		const int s = d->GetFlag("stage");
		if (s == 1)
			out.push_back(PLAYERBOT_EREBU_BAGJANAMU);
		else if (s == 2)
			out.push_back(PLAYERBOT_EREBU_THRYM);
	}

	// The ticket: a Kamien Driad. A bot with none did the forest's missions for one first.
	long long ChargePlayerBotErebuStone(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		if (ch->CountSpecifyItem(PLAYERBOT_EREBU_STONE) <= 0)
		{
			LPITEM it = ch->GetEmptyInventory(1) >= 0 ? ch->AutoGiveItem(PLAYERBOT_EREBU_STONE, 1, -1, false) : NULL;
			sys_log(0, "PLAYERBOT_EREBU: stone given pid=%u name=%s source=forest_missions ok=%d", ch->GetPlayerID(), ch->GetName(),
					it ? 1 : 0);
		}
		if (ch->CountSpecifyItem(PLAYERBOT_EREBU_STONE) > 0)
		{
			ch->RemoveSpecifyItem(PLAYERBOT_EREBU_STONE, 1);
			sys_log(0, "PLAYERBOT_EREBU: stone used pid=%u name=%s left=%d", ch->GetPlayerID(), ch->GetName(),
					(int)ch->CountSpecifyItem(PLAYERBOT_EREBU_STONE));
		}
		else
			sys_log(0, "PLAYERBOT_EREBU: no stone pid=%u name=%s (a full bag) - in all the same", ch->GetPlayerID(), ch->GetName());
		return 0;
	}

	// The members' bags (vnum -> count) and yang: the loot is what they gained.
	void SnapPlayerBotErebuBag(LPCHARACTER ch, std::map<DWORD, int>& out)
	{
		out.clear();
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item)
				out[item->GetVnum()] += (int)item->GetCount();
		}
	}

	std::string DescribePlayerBotErebuParty(const TPlayerBotDgRun& run, int& lvMin, int& lvMax, int& chMin, int& chMax, int& healers)
	{
		std::map<std::string, int> mix;
		lvMin = chMin = INT_MAX;
		lvMax = chMax = healers = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			char key[8];
			snprintf(key, sizeof(key), "%s%d", PlayerBotErebuJob(c), (int)c->GetSkillGroup());
			++mix[key];
			lvMin = std::min(lvMin, (int)c->GetLevel());
			lvMax = std::max(lvMax, (int)c->GetLevel());
			chMin = std::min(chMin, GetPlayerBotChampionLevel(c));
			chMax = std::max(chMax, GetPlayerBotChampionLevel(c));
			healers += IsPlayerBotErebuHealer(c) ? 1 : 0;
		}
		if (lvMin == INT_MAX)
			lvMin = chMin = 0;
		std::string out;
		for (std::map<std::string, int>::const_iterator i = mix.begin(); i != mix.end(); ++i)
			out += (out.empty() ? "" : ",") + i->first + ":" + std::to_string(i->second);
		return out.empty() ? "-" : out;
	}

	// The way in (UpdatePlayerBotDgRunGather's "entered"): the bags and the party's line.
	void NotePlayerBotErebuRunStart(const TPlayerBotDgRun& run)
	{
		TPlayerBotErebuRun& er = s_mapPlayerBotErebuRuns[run.iId];
		std::string names;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			SnapPlayerBotErebuBag(c, er.bags[run.members[i]]);
			er.gold[run.members[i]] = (long long)c->GetGold();
			char one[96];
			snprintf(one, sizeof(one), "%s%s(%s%d,%d,c%d,hp%d)", names.empty() ? "" : " ", c->GetName(), PlayerBotErebuJob(c),
					(int)c->GetSkillGroup(), (int)c->GetLevel(), GetPlayerBotChampionLevel(c), (int)c->GetMaxHP());
			if (names.size() < 600)
				names += one;
		}
		int lvMin = 0, lvMax = 0, chMin = 0, chMax = 0, healers = 0;
		const std::string mix = DescribePlayerBotErebuParty(run, lvMin, lvMax, chMin, chMax, healers);
		sys_log(0, "PLAYERBOT_EREBU: run start run=%d party=%d instance=%ld empire=%u members=%u mix=%s levels=%d-%d champion=%d-%d healers=%d bots=%s",
				run.iId, er.iParty, run.lInstance, (unsigned int)run.bEmpire, (unsigned int)run.members.size(), mix.c_str(), lvMin,
				lvMax, chMin, chMax, healers, names.c_str());
	}

	// Once a second inside (UpdatePlayerBotDgRunInside): the bosses up and down, their health every minute.
	void UpdatePlayerBotErebuRun(TPlayerBotDgRun& run, LPDUNGEON d, int inside, int alive, DWORD dwNow)
	{
		if (!d)
			return;
		TPlayerBotErebuRun& er = s_mapPlayerBotErebuRuns[run.iId];
		const TPlayerBotArzDgScan& sc = ScanPlayerBotArzDg(run.lInstance, dwNow);
		LPCHARACTER bag = NULL, thrym = NULL;
		int healers = 0;
		for (size_t i = 0; i < sc.foes.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(sc.foes[i].dwVID);
			if (!c || c->IsDead())
				continue;
			if (sc.foes[i].dwRace == PLAYERBOT_EREBU_BAGJANAMU)
				bag = c;
			else if (sc.foes[i].dwRace == PLAYERBOT_EREBU_THRYM)
				thrym = c;
			else if (sc.foes[i].dwRace == PLAYERBOT_EREBU_HEALER)
			{
				++healers;
				if (er.healerVids.insert(sc.foes[i].dwVID).second)
					++er.iHealersSeen;
			}
		}
		const DWORD at = run.dwEnteredAt ? (dwNow - run.dwEnteredAt) / 1000 : 0;
		if (bag && !er.dwBagjanamuUp)
		{
			er.dwBagjanamuUp = dwNow;
			sys_log(0, "PLAYERBOT_EREBU: boss up run=%d boss=bagjanamu after_s=%u inside=%d", run.iId, at, inside);
		}
		if (thrym && !er.dwThrymUp)
		{
			er.dwThrymUp = dwNow;
			sys_log(0, "PLAYERBOT_EREBU: boss up run=%d boss=thrym after_s=%u inside=%d alive=%d", run.iId, at, inside, alive);
		}
		if (bag && bag->GetMaxHP() > 0)
			er.iBagjanamuLow = std::min(er.iBagjanamuLow, (int)((long long)bag->GetHP() * 100 / bag->GetMaxHP()));
		if (thrym && thrym->GetMaxHP() > 0)
			er.iThrymLow = std::min(er.iThrymLow, (int)((long long)thrym->GetHP() * 100 / thrym->GetMaxHP()));
		if (!er.dwBagjanamuDown && d->GetFlag("stage") >= 2)
		{
			er.dwBagjanamuDown = dwNow;
			er.iBagjanamuLow = 0;
			sys_log(0, "PLAYERBOT_EREBU: boss down run=%d boss=bagjanamu after_s=%u fight_s=%u deaths=%d", run.iId, at,
					er.dwBagjanamuUp ? (dwNow - er.dwBagjanamuUp) / 1000 : 0, run.iDeaths);
		}
		if (!er.dwThrymDown && d->GetFlag("won") == 1)
		{
			er.dwThrymDown = dwNow;
			er.iThrymLow = 0;
			sys_log(0, "PLAYERBOT_EREBU: boss down run=%d boss=thrym after_s=%u fight_s=%u deaths=%d healers_seen=%d", run.iId, at,
					er.dwThrymUp ? (dwNow - er.dwThrymUp) / 1000 : 0, run.iDeaths, er.iHealersSeen);
		}
		if ((bag || thrym) && dwNow >= er.dwNextHpLog)
		{
			er.dwNextHpLog = dwNow + PLAYERBOT_EREBU_HP_LOG_MS;
			LPCHARACTER b = thrym ? thrym : bag;
			sys_log(0, "PLAYERBOT_EREBU: fight run=%d boss=%s hp=%d%% after_s=%u inside=%d alive=%d fit=%d healers=%d deaths=%d wipes=%d fallback=%d",
					run.iId, thrym ? "thrym" : "bagjanamu", b->GetMaxHP() > 0 ? (int)((long long)b->GetHP() * 100 / b->GetMaxHP()) : -1,
					at, inside, alive, run.iFit, healers, run.iDeaths, run.iWipes, run.bFallback ? 1 : 0);
		}
	}

	// The run over (ClosePlayerBotDgRun, before the members go): its line, its row, the party's count.
	void LogPlayerBotErebuRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS)
	{
		std::map<int, TPlayerBotErebuRun>::iterator it = s_mapPlayerBotErebuRuns.find(run.iId);
		TPlayerBotErebuRun er = it != s_mapPlayerBotErebuRuns.end() ? it->second : TPlayerBotErebuRun();
		if (it != s_mapPlayerBotErebuRuns.end())
			s_mapPlayerBotErebuRuns.erase(it);
		const bool won = result && !strcmp(result, "finished");
		// The loot: what the members' bags and purses gained since the way in.
		std::map<DWORD, int> gained;
		long long yang = 0;
		for (size_t i = 0; i < run.members.size() && entered; ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			std::map<DWORD, int> now;
			SnapPlayerBotErebuBag(c, now);
			const std::map<DWORD, int>& before = er.bags[run.members[i]];
			for (std::map<DWORD, int>::const_iterator n = now.begin(); n != now.end(); ++n)
			{
				std::map<DWORD, int>::const_iterator b = before.find(n->first);
				const int diff = n->second - (b != before.end() ? b->second : 0);
				if (diff > 0)
					gained[n->first] += diff;
			}
			std::map<DWORD, long long>::const_iterator g = er.gold.find(run.members[i]);
			if (g != er.gold.end() && (long long)c->GetGold() > g->second)
				yang += (long long)c->GetGold() - g->second;
		}
		std::string loot;
		for (std::map<DWORD, int>::const_iterator g = gained.begin(); g != gained.end() && loot.size() < 400; ++g)
			loot += (loot.empty() ? "" : ",") + std::to_string(g->first) + "x" + std::to_string(g->second);
		int lvMin = 0, lvMax = 0, chMin = 0, chMax = 0, healers = 0;
		const std::string mix = DescribePlayerBotErebuParty(run, lvMin, lvMax, chMin, chMax, healers);
		const DWORD bagS = er.dwBagjanamuDown && run.dwEnteredAt ? (er.dwBagjanamuDown - run.dwEnteredAt) / 1000 : 0;
		const DWORD thrymS = er.dwThrymDown && run.dwEnteredAt ? (er.dwThrymDown - run.dwEnteredAt) / 1000 : 0;
		sys_log(0, "PLAYERBOT_EREBU: run end run=%d party=%d result=%s won=%d took_s=%u stage=%d bagjanamu_down_s=%u thrym_down_s=%u "
				"bagjanamu_low=%d thrym_low=%d healers_seen=%d deaths=%d wipes=%d break_offs=%d fallbacks=%d members=%u mix=%s "
				"levels=%d-%d champion=%d-%d entered=%d yang=%lld loot=%s",
				run.iId, er.iParty, result ? result : "-", won ? 1 : 0, tookS, run.iStage, bagS, thrymS, er.iBagjanamuLow,
				er.iThrymLow, er.iHealersSeen, run.iDeaths, run.iWipes, run.iBreakOffs, run.iFallbacks,
				(unsigned int)run.members.size(), mix.c_str(), lvMin, lvMax, chMin, chMax, entered ? 1 : 0, yang,
				loot.empty() ? "-" : loot.c_str());
		FILE* fp = fopen(PLAYERBOT_EREBU_RUNS_FILE, "a");
		if (fp)
		{
			fprintf(fp, "%ld\t%d\t%d\t%u\t%s\t%u\t%d\t%u\t%u\t%d\t%d\t%d\t%d\t%u\t%s\t%d-%d\t%d-%d\t%lld\t%s\n", (long)time(0), run.iId,
					er.iParty, (unsigned int)run.bEmpire, result ? result : "-", tookS, run.iStage, bagS, thrymS, er.iBagjanamuLow,
					er.iThrymLow, run.iDeaths, run.iWipes, (unsigned int)run.members.size(), mix.c_str(), lvMin, lvMax, chMin,
					chMax, yang, loot.empty() ? "-" : loot.c_str());
			fclose(fp);
		}
		std::map<int, TPlayerBotErebuParty>::iterator p = s_mapPlayerBotErebuParties.find(er.iParty);
		if (p != s_mapPlayerBotErebuParties.end() && p->second.iRun == run.iId)
		{
			p->second.iRun = 0;
			p->second.dwWaitSince = 0;
			if (entered)
			{
				++p->second.iRuns;
				p->second.iDeaths += run.iDeaths;
				if (won)
				{
					++p->second.iWins;
					if (thrymS > 0 && (p->second.dwBestS == 0 || thrymS < p->second.dwBestS))
						p->second.dwBestS = thrymS;
				}
			}
		}
	}

	// The rest after an Erebu run: a training party's is short (unless m2_bot_erebu_train_cd keeps the players' 2 hours).
	DWORD GetPlayerBotErebuRest(const TPlayerBotDgRun& run, DWORD rest)
	{
		if (!IsPlayerBotErebuTrainRun(run.iId))
			return rest;
		return PLAYERBOT_EREBU_TRAIN_REST_MS + (DWORD)number(0, (int)PLAYERBOT_EREBU_TRAIN_REST_SPREAD_MS);
	}

	// A trainee between its runs on Zaklety Las: by Przywodca Strazy Lasu, drinking, fighting off what comes, waiting
	// for its party's next call (ManagePlayerBotDungeonRun, before the run's own pass) - no walk back to its Sung Ma
	// map for the two minutes and no new claim on it.
	bool HoldPlayerBotErebuTrainee(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || s_mapPlayerBotErebuTrainee.empty() || ch->IsDead() || state.bRecoveringAfterDeath ||
				ch->GetMapIndex() != PLAYERBOT_EREBU_MAP)
			return false;
		std::map<DWORD, int>::const_iterator t = s_mapPlayerBotErebuTrainee.find(ch->GetPlayerID());
		if (t == s_mapPlayerBotErebuTrainee.end() || s_mapPlayerBotDgRunBots.count(ch->GetPlayerID()))
			return false;
		std::map<int, TPlayerBotErebuParty>::const_iterator p = s_mapPlayerBotErebuParties.find(t->second);
		if (p == s_mapPlayerBotErebuParties.end())
			return false;
		state.dwLastMeaningfulActivityTime = dwNow;
		if (KeepPlayerBotTowerAlive(ch, state, dwNow, PLAYERBOT_PDG_POTION_HP, PLAYERBOT_PDG_POTION_SP))
			return true;
		LPCHARACTER threat = FindPlayerBotDgRunThreat(ch, 0);
		if (threat)
			return FightPlayerBotTowerObjective(ch, state, threat, dwNow);
		if (HandleLoot(ch, state, dwNow))
			return true;
		size_t idx = 0;
		while (idx < p->second.pids.size() && p->second.pids[idx] != ch->GetPlayerID())
			++idx;
		static const int kSide[8][2] = { { 3, 0 }, { 2, 2 }, { 0, 3 }, { -2, 2 }, { -3, 0 }, { -2, -2 }, { 0, -3 }, { 2, -2 } };
		const long x = PLAYERBOT_EREBU_GATHER_X + kSide[idx % 8][0] * 100 + (long)(p->first % 5) * 60;
		const long y = PLAYERBOT_EREBU_GATHER_Y + kSide[idx % 8][1] * 100 + 250;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y) > 300)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			if (dwNow >= state.dwNextTowerMoveTime)
			{
				state.dwNextTowerMoveTime = dwNow + 2000;
				MovePlayerBot(ch, x, y, dwNow, 6, true, false);
			}
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// ------------------------------------------------------------ the training's parties

	struct TPlayerBotErebuCand
	{
		DWORD pid;
		BYTE empire;
		int job;
		bool healer;
		long long score;
	};

	// A bot of this core free for the training: level 95+, armed, no claim on it, nobody's trainee yet.
	bool IsPlayerBotErebuCandidate(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_EREBU_MIN_LEVEL || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotErebuTrainee(pid) || s_mapPlayerBotDgRunBots.count(pid) || IsPlayerBotYoharaHydraResident(pid) ||
				IsPlayerBotYoharaSzcResident(pid) || IsPlayerBotYoharaLeaving(pid))
			return false;
		return GetPlayerBotDgRunRefusal(ch, state, dwNow) == NULL;
	}

	void GatherPlayerBotErebuCands(std::vector<TPlayerBotErebuCand> out[4], DWORD dwNow)
	{
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!IsPlayerBotErebuCandidate(ch, it->second, dwNow))
				continue;
			TPlayerBotErebuCand c;
			c.pid = it->first;
			c.empire = ch->GetEmpire();
			c.job = ch->GetJob() % 4;
			c.healer = IsPlayerBotErebuHealer(ch) && ch->GetSkillLevel(PLAYERBOT_DGRUN_CURE_SKILL) > 0;
			c.score = ScorePlayerBotErebu(ch);
			out[c.empire].push_back(c);
		}
		for (int e = 1; e <= 3; ++e)
			std::stable_sort(out[e].begin(), out[e].end(), [](const TPlayerBotErebuCand& a, const TPlayerBotErebuCand& b)
					{ return a.score > b.score; });
	}

	void LogPlayerBotErebuParty(const TPlayerBotErebuParty& p, const char* what)
	{
		std::string names;
		for (size_t i = 0; i < p.pids.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(p.pids[i]);
			char one[80];
			if (c)
				snprintf(one, sizeof(one), "%s%s(%u,%s%d,%d,c%d)", names.empty() ? "" : " ", c->GetName(), p.pids[i], PlayerBotErebuJob(c),
						(int)c->GetSkillGroup(), (int)c->GetLevel(), GetPlayerBotChampionLevel(c));
			else
				snprintf(one, sizeof(one), "%s%u(offline)", names.empty() ? "" : " ", p.pids[i]);
			names += one;
		}
		sys_log(0, "PLAYERBOT_EREBU: party %s party=%d empire=%u manual=%d size=%u runs=%d wins=%d bots=%s", what, p.iId,
				(unsigned int)p.bEmpire, p.bManual ? 1 : 0, (unsigned int)p.pids.size(), p.iRuns, p.iWins, names.c_str());
	}

	// Up to `size` of the kingdom's candidates (best first): a healing Shaman, a Warrior to lead, no class over its third.
	bool DrawPlayerBotErebuParty(std::vector<TPlayerBotErebuCand>& pool, int size, std::vector<DWORD>& out)
	{
		out.clear();
		if ((int)pool.size() < size)
			return false;
		std::vector<bool> taken(pool.size(), false);
		int perJob[4] = { 0, 0, 0, 0 };
		const int cap = std::max(2, (size + 2) / 3);
		int heal = -1, lead = -1;
		for (size_t i = 0; i < pool.size() && heal < 0; ++i)
			if (pool[i].healer)
				heal = (int)i;
		if (heal < 0)
			return false;
		for (size_t i = 0; i < pool.size() && lead < 0; ++i)
			if (pool[i].job == JOB_WARRIOR)
				lead = (int)i;
		if (lead < 0)
			lead = heal == 0 ? 1 : 0;
		out.push_back(pool[lead].pid);
		taken[lead] = true;
		++perJob[pool[lead].job & 3];
		out.push_back(pool[heal].pid);
		taken[heal] = true;
		++perJob[pool[heal].job & 3];
		for (int pass = 0; pass < 2 && (int)out.size() < size; ++pass)
			for (size_t i = 0; i < pool.size() && (int)out.size() < size; ++i)
			{
				if (taken[i] || (pass == 0 && perJob[pool[i].job & 3] >= cap))
					continue;
				out.push_back(pool[i].pid);
				taken[i] = true;
				++perJob[pool[i].job & 3];
			}
		std::vector<TPlayerBotErebuCand> rest;
		for (size_t i = 0; i < pool.size(); ++i)
			if (!taken[i])
				rest.push_back(pool[i]);
		pool.swap(rest);
		return (int)out.size() >= size;
	}

	void AddPlayerBotErebuParty(BYTE empire, const std::vector<DWORD>& pids, bool manual)
	{
		TPlayerBotErebuParty p;
		p.iId = s_iPlayerBotErebuNextParty++;
		p.bEmpire = empire;
		p.pids = pids;
		p.bManual = manual;
		for (size_t i = 0; i < pids.size(); ++i)
			s_mapPlayerBotErebuTrainee[pids[i]] = p.iId;
		s_mapPlayerBotErebuParties[p.iId] = p;
		LogPlayerBotErebuParty(p, "formed");
	}

	void DissolvePlayerBotErebuParty(int id, const char* why)
	{
		std::map<int, TPlayerBotErebuParty>::iterator p = s_mapPlayerBotErebuParties.find(id);
		if (p == s_mapPlayerBotErebuParties.end())
			return;
		LogPlayerBotErebuParty(p->second, why);
		for (size_t i = 0; i < p->second.pids.size(); ++i)
			s_mapPlayerBotErebuTrainee.erase(p->second.pids[i]);
		s_mapPlayerBotErebuParties.erase(p);
	}

	// The parties asked for: formed from the best free bots, kingdom by kingdom (the most candidates first).
	void FormPlayerBotErebuParties(int wanted, DWORD dwNow)
	{
		int automatic = 0;
		for (std::map<int, TPlayerBotErebuParty>::const_iterator p = s_mapPlayerBotErebuParties.begin(); p != s_mapPlayerBotErebuParties.end(); ++p)
			automatic += p->second.bManual ? 0 : 1;
		if (automatic >= wanted)
			return;
		static DWORD s_dwNextTry = 0;
		if (s_dwNextTry != 0 && (int)(dwNow - s_dwNextTry) < 0)
			return;
		s_dwNextTry = dwNow + 60000;
		const int size = GetPlayerBotErebuTrainSize();
		std::vector<TPlayerBotErebuCand> pools[4];
		GatherPlayerBotErebuCands(pools, dwNow);
		int formed = 0;
		while (automatic < wanted)
		{
			int best = 0;
			for (int e = 1; e <= 3; ++e)
				if ((int)pools[e].size() >= size && (best == 0 || pools[e].size() > pools[best].size()))
					best = e;
			std::vector<DWORD> pids;
			if (best == 0 || !DrawPlayerBotErebuParty(pools[best], size, pids))
			{
				// no kingdom has another party's worth with a healing Shaman: the rest wait for the next try
				bool any = false;
				for (int e = 1; e <= 3 && !any; ++e)
				{
					if ((int)pools[e].size() < size)
						continue;
					if (DrawPlayerBotErebuParty(pools[e], size, pids))
					{
						AddPlayerBotErebuParty((BYTE)e, pids, false);
						++automatic;
						++formed;
						any = true;
					}
				}
				if (!any)
					break;
				continue;
			}
			AddPlayerBotErebuParty((BYTE)best, pids, false);
			++automatic;
			++formed;
		}
		if (automatic < wanted)
			PlayerBotLogThrottled("erebu_short", dwNow, "PLAYERBOT_EREBU: parties %d of %d - the free bots of 95+ (a healing Shaman each, %d a party) are %u/%u/%u",
					automatic, wanted, size, (unsigned int)pools[1].size(), (unsigned int)pools[2].size(), (unsigned int)pools[3].size());
		(void)formed;
	}

	// A member gone for PLAYERBOT_EREBU_TRAIN_REFILL_MS (logged out, another core): the best free bot of the kingdom.
	void RefillPlayerBotErebuParty(TPlayerBotErebuParty& p, DWORD dwNow)
	{
		std::vector<DWORD> gone;
		for (size_t i = 0; i < p.pids.size(); ++i)
			if (!CHARACTER_MANAGER::instance().FindByPID(p.pids[i]))
				gone.push_back(p.pids[i]);
		if (gone.empty())
		{
			p.dwShortSince = 0;
			return;
		}
		if (p.dwShortSince == 0)
			p.dwShortSince = dwNow ? dwNow : 1;
		if (dwNow - p.dwShortSince < PLAYERBOT_EREBU_TRAIN_REFILL_MS)
			return;
		p.dwShortSince = 0;
		std::vector<TPlayerBotErebuCand> pools[4];
		GatherPlayerBotErebuCands(pools, dwNow);
		std::vector<TPlayerBotErebuCand>& pool = pools[p.bEmpire < 4 ? p.bEmpire : 0];
		bool healerLeft = false;
		for (size_t i = 0; i < p.pids.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(p.pids[i]);
			healerLeft = healerLeft || IsPlayerBotErebuHealer(c);
		}
		for (size_t g = 0; g < gone.size(); ++g)
		{
			std::vector<DWORD>::iterator m = std::find(p.pids.begin(), p.pids.end(), gone[g]);
			if (m == p.pids.end())
				continue;
			int pick = -1;
			for (size_t i = 0; i < pool.size() && pick < 0; ++i)
				if (healerLeft || pool[i].healer)
					pick = (int)i;
			if (pick < 0 && !pool.empty())
				pick = 0;
			s_mapPlayerBotErebuTrainee.erase(gone[g]);
			if (pick < 0)
			{
				p.pids.erase(m);
				continue;
			}
			*m = pool[pick].pid;
			healerLeft = healerLeft || pool[pick].healer;
			s_mapPlayerBotErebuTrainee[pool[pick].pid] = p.iId;
			pool.erase(pool.begin() + pick);
		}
		LogPlayerBotErebuParty(p, "refilled");
	}

	// A party's run: the free of it, the leader first, at Przywodca Strazy Lasu.
	int CallPlayerBotErebuParty(TPlayerBotErebuParty& p, int def, DWORD dwNow, bool forced)
	{
		const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor("erebu");
		std::vector<playerbot_dgrun::TCand> free;
		int online = 0;
		for (size_t i = 0; i < p.pids.size(); ++i)
		{
			const DWORD pid = p.pids[i];
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch)
				continue;
			++online;
			if (s_mapPlayerBotDgRunBots.count(pid) || ch->IsDead())
				continue;
			std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotDgRunRest.find(pid);
			if (rest != s_mapPlayerBotDgRunRest.end() && (int)(rest->second - dwNow) > 0)
				continue;
			TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(pid);
			if (st == s_mapPlayerBotAIStates.end() || GetPlayerBotDgRunRefusal(ch, st->second, dwNow))
				continue;
			const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey("erebu");
			if (GetPlayerBotErebuFlag("m2_bot_erebu_train_cd") > 0 && panel && mt2009_dpanel::CooldownLeft(ch, *panel) > 0)
				continue;
			free.push_back(playerbot_dgrun::TCand(pid, ch->GetLevel(), ch->GetJob() % 4, 10, ch->GetSkillGroup() != 0));
		}
		if ((int)free.size() < rule.startMin || (rule.needHealer && !playerbot_dgrun::HasHealer(free)))
		{
			if (forced)
				sys_log(0, "PLAYERBOT_EREBU: no call party=%d - free=%u online=%d of %u (healer=%d)", p.iId, (unsigned int)free.size(),
						online, (unsigned int)p.pids.size(), playerbot_dgrun::HasHealer(free) ? 1 : 0);
			p.dwWaitSince = 0;
			return 0;
		}
		if (p.dwWaitSince == 0)
			p.dwWaitSince = dwNow ? dwNow : 1;
		if (!forced && (int)free.size() < online && dwNow - p.dwWaitSince < PLAYERBOT_EREBU_TRAIN_WAIT_MS)
			return 0;
		p.dwWaitSince = 0;
		TPlayerBotDgRunSlot slot;
		slot.lvMin = PLAYERBOT_EREBU_MIN_LEVEL;
		slot.lvMax = gPlayerMaxLevel;
		slot.partyMin = rule.startMin;
		slot.partyMax = playerbot_dgrun::PARTY_MAX;
		slot.panel = mt2009_dpanel::FindKey("erebu");
		const BYTE empire = p.bEmpire >= 1 && p.bEmpire <= 3 ? p.bEmpire : 1;
		slot.ok = slot.empireOk[empire] = true;
		TPlayerBotLfgPlace& place = slot.place[empire];
		if (!ResolvePlayerBotLfgPlace("erebu", 0, empire, PLAYERBOT_EREBU_MIN_LEVEL, place))
		{
			place = TPlayerBotLfgPlace();
			place.key = "erebu";
			place.map = PLAYERBOT_EREBU_MAP;
			place.x = PLAYERBOT_EREBU_GATHER_X;
			place.y = PLAYERBOT_EREBU_GATHER_Y;
		}
		place.lvMin = slot.lvMin;
		place.lvMax = slot.lvMax;
		if ((int)free.size() > playerbot_dgrun::PARTY_MAX)
			free.resize(playerbot_dgrun::PARTY_MAX);
		const int id = OpenPlayerBotDgRun(def, empire, free, slot, p.pids.size(), dwNow, forced ? "test" : "erebu_train");
		if (id == 0)
			return 0;
		p.iRun = id;
		s_mapPlayerBotErebuRuns[id].iParty = p.iId;
		sys_log(0, "PLAYERBOT_EREBU: party called run=%d party=%d empire=%u free=%u of=%u", id, p.iId, (unsigned int)empire,
				(unsigned int)free.size(), (unsigned int)p.pids.size());
		return id;
	}

	void LogPlayerBotErebuStatus()
	{
		int running = 0;
		for (std::map<int, TPlayerBotErebuParty>::const_iterator p = s_mapPlayerBotErebuParties.begin(); p != s_mapPlayerBotErebuParties.end(); ++p)
		{
			running += p->second.iRun ? 1 : 0;
			int online = 0;
			for (size_t i = 0; i < p->second.pids.size(); ++i)
				online += CHARACTER_MANAGER::instance().FindByPID(p->second.pids[i]) ? 1 : 0;
			sys_log(0, "PLAYERBOT_EREBU: status party=%d empire=%u size=%u online=%d run=%d runs=%d wins=%d deaths=%d best_s=%u manual=%d",
					p->first, (unsigned int)p->second.bEmpire, (unsigned int)p->second.pids.size(), online, p->second.iRun,
					p->second.iRuns, p->second.iWins, p->second.iDeaths, p->second.dwBestS, p->second.bManual ? 1 : 0);
		}
		sys_log(0, "PLAYERBOT_EREBU: status parties=%u wanted=%d size=%d running=%d cd=%d channel=%u hosted=%d",
				(unsigned int)s_mapPlayerBotErebuParties.size(), GetPlayerBotErebuTrainWanted(), GetPlayerBotErebuTrainSize(), running,
				GetPlayerBotErebuFlag("m2_bot_erebu_train_cd"), (unsigned int)g_bChannel,
				IsPlayerBotMapHostedHere(PLAYERBOT_EREBU_MAP) ? 1 : 0);
	}

	// Every PLAYERBOT_EREBU_TRAIN_PLAN_MS (ManagePlayerBotDungeonRuns): the parties formed, refilled, called.
	void PlanPlayerBotErebuTraining(DWORD dwNow, bool forced)
	{
		static DWORD s_dwNext = 0, s_dwNextStatus = 0;
		if (!forced && s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_EREBU_TRAIN_PLAN_MS;
		const int def = FindPlayerBotErebuDef();
		if (def < 0)
			return;
		const int wanted = GetPlayerBotErebuTrainWanted();
		// The flag off (or lowered): the automatic parties over the count go; the operator's stay till erebu_clear.
		if (wanted == 0 || !IsPlayerBotDgRunOn(dwNow))
		{
			std::vector<int> drop;
			for (std::map<int, TPlayerBotErebuParty>::const_iterator p = s_mapPlayerBotErebuParties.begin(); p != s_mapPlayerBotErebuParties.end(); ++p)
				if (!p->second.bManual && p->second.iRun == 0)
					drop.push_back(p->first);
			for (size_t i = 0; i < drop.size(); ++i)
				DissolvePlayerBotErebuParty(drop[i], "dissolved");
			if (wanted == 0 && s_mapPlayerBotErebuParties.empty())
				return;
		}
		else
			FormPlayerBotErebuParties(wanted, dwNow);
		if (s_mapPlayerBotErebuParties.empty())
			return;
		if (s_dwNextStatus == 0 || (int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_EREBU_STATUS_MS;
			LogPlayerBotErebuStatus();
		}
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_EREBU_MAP) || !SECTREE_MANAGER::instance().GetMap(PLAYERBOT_EREBU_MAP) ||
				!IsPlayerBotDgRunOn(dwNow))
			return;
		int running = 0;
		for (std::map<int, TPlayerBotErebuParty>::iterator p = s_mapPlayerBotErebuParties.begin(); p != s_mapPlayerBotErebuParties.end(); ++p)
		{
			if (p->second.iRun && !s_mapPlayerBotDgRuns.count(p->second.iRun))
				p->second.iRun = 0;
			running += p->second.iRun ? 1 : 0;
		}
		const int capFlag = GetPlayerBotErebuFlag("m2_bot_erebu_train_runs");
		const int cap = capFlag > 0 ? capFlag : std::max<int>(1, (int)s_mapPlayerBotErebuParties.size());
		for (std::map<int, TPlayerBotErebuParty>::iterator p = s_mapPlayerBotErebuParties.begin();
				p != s_mapPlayerBotErebuParties.end() && running < cap; ++p)
		{
			if (p->second.iRun)
				continue;
			RefillPlayerBotErebuParty(p->second, dwNow);
			if (CallPlayerBotErebuParty(p->second, def, dwNow, forced))
				++running;
		}
	}

	// The operator's lines (RunPlayerBotDgRunTestFile): erebu_party, erebu_clear, erebu_status.
	bool RunPlayerBotErebuTestLine(const char* cmd, const std::string& line, DWORD dwNow)
	{
		if (!strcmp(cmd, "erebu_status"))
		{
			LogPlayerBotErebuStatus();
			return true;
		}
		if (!strcmp(cmd, "erebu_clear"))
		{
			std::vector<int> ids;
			for (std::map<int, TPlayerBotErebuParty>::const_iterator p = s_mapPlayerBotErebuParties.begin(); p != s_mapPlayerBotErebuParties.end(); ++p)
				ids.push_back(p->first);
			for (size_t i = 0; i < ids.size(); ++i)
				DissolvePlayerBotErebuParty(ids[i], "cleared");
			return true;
		}
		if (!strcmp(cmd, "erebu_train"))
		{
			PlanPlayerBotErebuTraining(dwNow, true);
			return true;
		}
		if (strcmp(cmd, "erebu_party"))
			return false;
		// the pids after the command, by commas or spaces
		std::vector<DWORD> pids;
		const size_t from = line.find("erebu_party") + strlen("erebu_party");
		DWORD n = 0;
		bool in = false;
		for (size_t i = from; i <= line.size(); ++i)
		{
			const char c = i < line.size() ? line[i] : ' ';
			if (c >= '0' && c <= '9')
			{
				n = n * 10 + (DWORD)(c - '0');
				in = true;
			}
			else if (in)
			{
				if (std::find(pids.begin(), pids.end(), n) == pids.end())
					pids.push_back(n);
				n = 0;
				in = false;
			}
		}
		BYTE empire = 0;
		std::vector<DWORD> ok;
		for (size_t i = 0; i < pids.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
			const char* why = NULL;
			if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot())
				why = "not_a_bot_here";
			else if (IsPlayerBotErebuTrainee(pids[i]))
				why = "trainee_already";
			else if (ch->GetLevel() < PLAYERBOT_EREBU_MIN_LEVEL)
				why = "level";
			if (why)
			{
				sys_log(0, "PLAYERBOT_EREBU: erebu_party pid=%u left out why=%s", pids[i], why);
				continue;
			}
			if (empire == 0)
				empire = ch->GetEmpire();
			ok.push_back(pids[i]);
		}
		if (ok.size() < 2)
		{
			sys_log(0, "PLAYERBOT_EREBU: erebu_party refused - %u of the bots here", (unsigned int)ok.size());
			return true;
		}
		AddPlayerBotErebuParty(empire, ok, true);
		return true;
	}
}

#endif
