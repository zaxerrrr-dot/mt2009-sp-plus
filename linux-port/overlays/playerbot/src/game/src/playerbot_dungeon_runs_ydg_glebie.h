#ifndef __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_GLEBIE_H__
#define __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_GLEBIE_H__

// MT2009_PLUS_BOT_GLEBIE_V1 - the bots' runs of Glebie Polnocnego Wiatru (395, ymaps3_glebie.quest): Alastor, the weak
// and the strong one (the owner, night of 5/6 November 2026: "Naucz boty chodzic na Glebie Polnocnego Wiatru (Alastor
// slaby i silny) ... masz pelne pozwolenie na zmiany botow"; the dungeon itself stays as it is).
//
// Two rows of PLAYERBOT_DGRUN_DEFS / PLAYERBOT_YDG_DEFS (kind DGRUN_KIND_YDG, boss YDG_GLEBIE): glebie_slaby, glebie_silny.
// The gathering is the dungeon panel's entrance - Upiorny Straznik (20815) in Zejscie Polnocnego Wiatru (394, 383,614).
// What a person's party needs at the guard, a bots' party needs here:
//   * level 120 and a Champion level each (IsPlayerBotGlebieEntryOk - the clock's draw, the training's choice), the
//     strong one after three weak ones won (the quest's pc flag ymaps3_glebie.weak_done, which its Alastor kill counts
//     for the bots as for the people);
//   * three Zamarzniete Klucze (70410) each (ChargePlayerBotGlebieKeys): its own, else the missing ones bought (the
//     market's price, PLAYERBOT_GLEBIE_KEY_PRICE each), else let go (logged let_go - the YDG book's rule);
//   * 1-8 in a party (the quest), no day's count and no rest (the quest has none).
// The quest's bots' half (MT2009_PLUS_BOT_GLEBIE_V1 in ymaps3_glebie.quest): the core makes the instance (flag
// mt2009_dgrun), sets "kind" (1 weak, 2 strong) and the players p1..p8 - the bots are the quest's players, so the ice
// spikes, the Deadly Cold and its frost, the waves and the reward are theirs as a person's - and the timer
// ymaps3_glebie_dgrun runs the quest's init(); ymaps3_glebie_dgrun_next is the leader's touch of the White Dragon Egg
// (Alastor wakes); the kill sets "won". The chests (8 Biale Smocze Skrzynie, 70411 / 70412) the quest leaves at Upiorny
// Straznik ("Odbierz nagrode", pc flag ymaps3_glebie.reward) are taken at the run's end (NotePlayerBotGlebieRunEnd).
//
// Inside (stage 1 before Alastor, 2 Alastor, 3 won):
//   * stage 1: with egg duty on (below) the party breaks the Krysztal Pln. Wiatru (3971 - its portal 3972 leads to the
//     egg chamber), then waits by the egg; the leader wakes Alastor (ShouldPlayerBotGlebieWake) when the crystal is
//     down, PLAYERBOT_GLEBIE_WAKE_S after the start (default 0: at once - the quest's three Wraths heal Alastor at
//     2:30 / 5:00 / 7:30 after the START, so an early wake spends them, and the eggs' berserks, early) and the leader
//     stands by its party;
//   * stage 2: Alastor is the objective; the waves (a minute each, the Wraths' and the berserk's) are the threats the
//     pack fights; PLAYERBOT_GLEBIE_EGG_BOTS members (default: one in a party of six or more; Ninja, Sura, Warrior
//     first, never the leader or the healing Shaman) go through the portal to the chamber and break the White Dragon
//     Eggs (8635 / 8636: every one delays the Cold by 20 s, too many alive throw Alastor into a berserk); a member
//     without the duty that finds itself in the chamber goes back by its portal (3973);
//   * every member (DodgePlayerBotGlebieZones, before anything else): the ground zones of d.zone_attack stand on the
//     invisible marker 3975 - the spikes under everybody every 15 s (red circle, 1.8 s, 50% of max HP) and the lasting
//     white circles of the Deadly Cold (15 000 / 20 000 HP every 2 s, the frost); a bot inside PLAYERBOT_GLEBIE_ZONE_AVOID
//     of one steps out to the nearest safe ground by its fight, as a person does.
// The YDG run bonuses (BuffPlayerBotYdgMember) are theirs as every YDG run's; nothing of the dungeon is changed.
//
// The log: BOT_GLEBIE lines (keys, run start with kind, weak_done and the Sung Ma stats against the map's, wake,
// boss every minute: Alastor's health, berserk, wrath, colds, eggs alive; egg duty, portal, dodge counts, run end with
// the chests taken) beside BOT_YDG / BOT_DGRUN. The training: "auto <n> <size> glebie_slaby,glebie_silny" in
// playerbot_ydg_train (a party goes strong once each of it has three weak wins).
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h, after playerbot_dungeon_runs_ydg.h.

namespace
{
	const long PLAYERBOT_GLEBIE_MAP = 395;
	const DWORD PLAYERBOT_GLEBIE_KEY = 70410;		// Zamarzniety Klucz
	const int PLAYERBOT_GLEBIE_KEYS = 3;
	const int PLAYERBOT_GLEBIE_MIN_LEVEL = 120;
	const int PLAYERBOT_GLEBIE_WEAK_NEEDED = 3;
	const long long PLAYERBOT_GLEBIE_KEY_PRICE = 2000000LL;
	const DWORD PLAYERBOT_GLEBIE_BOSS[3] = { 0, 6790, 6791 };
	const DWORD PLAYERBOT_GLEBIE_EGG[3] = { 0, 8635, 8636 };
	const DWORD PLAYERBOT_GLEBIE_REWARD[3] = { 0, 70411, 70412 };
	const int PLAYERBOT_GLEBIE_REWARD_COUNT = 8;
	const DWORD PLAYERBOT_GLEBIE_CRYSTAL = 3971;
	const DWORD PLAYERBOT_GLEBIE_PORTAL_IN = 3972;	// at the crystal's spot once it broke -> the chamber (415,136)
	const DWORD PLAYERBOT_GLEBIE_PORTAL_OUT = 3973;	// in the chamber (426,134) -> the hall (94,139)
	const DWORD PLAYERBOT_GLEBIE_ZONE_MARK = 3975;
	// cells off the map's base (the quest's cfg())
	const long PLAYERBOT_GLEBIE_CHAMBER_X = 384, PLAYERBOT_GLEBIE_CHAMBER_Y = 131;
	const long PLAYERBOT_GLEBIE_CHAMBER_IN_X = 415, PLAYERBOT_GLEBIE_CHAMBER_IN_Y = 136;
	const long PLAYERBOT_GLEBIE_HALL_IN_X = 94, PLAYERBOT_GLEBIE_HALL_IN_Y = 139;
	const long PLAYERBOT_GLEBIE_CAMP_X = 132, PLAYERBOT_GLEBIE_CAMP_Y = 150;
	const long PLAYERBOT_GLEBIE_CHAMBER_FROM_X = 300;	// a cell x from here on is the egg chamber
	const int PLAYERBOT_GLEBIE_PORTAL_TOUCH = 220;
	const DWORD PLAYERBOT_GLEBIE_CRYSTAL_WAIT_S = 240;	// the crystal not down by then: Alastor all the same
	const DWORD PLAYERBOT_GLEBIE_GATHER_WAIT_S = 120;	// the leader alone by the egg: woken all the same
	const DWORD PLAYERBOT_GLEBIE_BOSS_LOG_MS = 60 * 1000;
	const DWORD PLAYERBOT_GLEBIE_DODGE_MS = 2500;
	const int PLAYERBOT_GLEBIE_MARK_SCAN = 2200;

	struct TPlayerBotGlebieRun
	{
		int iKind;
		int iEggWanted;
		std::set<DWORD> eggBots;
		bool bEggPicked, bWakeAsked;
		DWORD dwNextBossLog;
		int iBossLow, iBerserk, iWrath, iColds, iEggsMax, iDodges, iPortals, iEggKillsSeen;
		TPlayerBotGlebieRun() : iKind(0), iEggWanted(0), bEggPicked(false), bWakeAsked(false), dwNextBossLog(0), iBossLow(100),
				iBerserk(0), iWrath(0), iColds(0), iEggsMax(0), iDodges(0), iPortals(0), iEggKillsSeen(0) {}
	};
	std::map<int, TPlayerBotGlebieRun> s_mapPlayerBotGlebieRuns;	// run id -> record

	struct TPlayerBotGlebieDodge
	{
		long x, y;
		DWORD dwUntil, dwNextMove;
		TPlayerBotGlebieDodge() : x(0), y(0), dwUntil(0), dwNextMove(0) {}
	};
	std::map<DWORD, TPlayerBotGlebieDodge> s_mapPlayerBotGlebieDodge;	// pid -> the step out of a circle

	int GetPlayerBotGlebieKind(const TPlayerBotDgRunDef& def)
	{
		if (!def.szKey)
			return 0;
		if (!strcmp(def.szKey, "glebie_slaby"))
			return 1;
		if (!strcmp(def.szKey, "glebie_silny"))
			return 2;
		return 0;
	}

	int GetPlayerBotGlebieRunKind(const TPlayerBotDgRun& run)
	{
		return run.iDef >= 0 && run.iDef < PLAYERBOT_DGRUN_DEF_COUNT ? GetPlayerBotGlebieKind(PLAYERBOT_DGRUN_DEFS[run.iDef]) : 0;
	}

	int GetPlayerBotGlebieDKind(LPDUNGEON d)
	{
		return d && d->GetFlag("kind") == 2 ? 2 : 1;
	}

	bool GetPlayerBotGlebieLocal(LPCHARACTER ch, long& lx, long& ly)
	{
		LPSECTREE_MAP pMap = ch ? SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex()) : NULL;
		if (!pMap)
			return false;
		lx = (ch->GetX() - pMap->m_setting.iBaseX) / 100;
		ly = (ch->GetY() - pMap->m_setting.iBaseY) / 100;
		return true;
	}

	bool GetPlayerBotGlebieWorld(long instance, long cx, long cy, long& x, long& y)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		if (!pMap)
			return false;
		x = pMap->m_setting.iBaseX + cx * 100;
		y = pMap->m_setting.iBaseY + cy * 100;
		return true;
	}

	// The nearest living one of this race in the instance (NULL: none).
	LPCHARACTER FindPlayerBotGlebieRace(LPCHARACTER ch, DWORD race)
	{
		LPSECTREE_MAP pMap = ch ? SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex()) : NULL;
		if (!pMap)
			return NULL;
		FPlayerBotYdgNpc finder(ch, race, NULL);
		pMap->for_each(finder);
		return finder.m_found;
	}

	bool IsPlayerBotGlebieStanding(long instance, DWORD race)
	{
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(instance, get_dword_time());
		for (size_t i = 0; i < scan.foes.size(); ++i)
			if (scan.foes[i].dwRace == race)
				return true;
		return false;
	}

	// ------------------------------------------------------------ the strength gate

	// MT2009_PLUS_BOT_YDG_GATE_V1 (the owner, 6 November 2026, after the night's report: "musisz poprawic quest i ogolnie
	// poprawic boty"): only parties that can win go to Swiatynia Wezy and Glebie; the weaker bots grow elsewhere first.
	// The night's 21:54-05:45 runs (BOT_YDG run start gear_avg / mix "gNNN+P" = GetPlayerBotYdgGearLevel of the weapon,
	// the armour and the helmet, and their plus):
	//   * Swiatynia: 7 wins, every one a party of average gear 96-103 with 3-5 members of "g103+9"; the 05:20 wave of
	//     g77-80 parties (none of 103+9) never broke the 3rd level's Metins (8.5M, regen 1% / 5 s) - timeouts;
	//   * Glebie weak: 15 wins of ~50, all parties of 7-8 with average 99-103 and 6-8 of 103+9; no party of 4-5 ever won
	//     (20+ wipes), nor the g80 parties of 05:20;
	//   * Glebie strong: the one win - 8 of 103+9 (average 103); parties of 4-5 wiped or timed out.
	// So: each member of the dungeon's floor (iBotGear), the party's average at iAvgGear or more and iStrong members of
	// PLAYERBOT_YDG_GATE_STRONG_GEAR+PLAYERBOT_YDG_GATE_STRONG_PLUS (fewer in a smaller party: all of them). The party
	// sizes are the rules' (playerbot_dungeon_runs_rules.h: Glebie 7 / 8 at the entrance). Every figure an env
	// (PLAYERBOT_WEZE_GATE_*, PLAYERBOT_GLEBIE_WEAK_GATE_*, PLAYERBOT_GLEBIE_STRONG_GATE_*); PLAYERBOT_YDG_GATE=0 is off.
	// The clock's calls draw from the bots of the average or more (strict), the training's and Dropki's parties are
	// looked at whole (the floor each, the average and the strong ones together); an "auto" training party that falls
	// short is not formed (its bots stay free for the rest of the game).
	struct TPlayerBotYdgGate
	{
		int iBotGear, iAvgGear, iStrong;
	};

	bool GetPlayerBotYdgGate(const TPlayerBotDgRunDef& def, TPlayerBotYdgGate& g)
	{
		if (!def.szKey || def.bKind != DGRUN_KIND_YDG || GetPlayerBotYdgEnv("PLAYERBOT_YDG_GATE", 1, 0, 1) == 0)
			return false;
		if (!strcmp(def.szKey, "swiatynia"))
		{
			g.iBotGear = GetPlayerBotYdgEnv("PLAYERBOT_WEZE_GATE_BOT_GEAR", 80, 0, 250);
			g.iAvgGear = GetPlayerBotYdgEnv("PLAYERBOT_WEZE_GATE_AVG_GEAR", 96, 0, 250);
			g.iStrong = GetPlayerBotYdgEnv("PLAYERBOT_WEZE_GATE_STRONG", 3, 0, 8);
			return true;
		}
		const int kind = GetPlayerBotGlebieKind(def);
		if (kind == 1)
		{
			g.iBotGear = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_WEAK_GATE_BOT_GEAR", 80, 0, 250);
			g.iAvgGear = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_WEAK_GATE_AVG_GEAR", 99, 0, 250);
			g.iStrong = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_WEAK_GATE_STRONG", 6, 0, 8);
			return true;
		}
		if (kind == 2)
		{
			g.iBotGear = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_STRONG_GATE_BOT_GEAR", 91, 0, 250);
			g.iAvgGear = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_STRONG_GATE_AVG_GEAR", 101, 0, 250);
			g.iStrong = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_STRONG_GATE_STRONG", 7, 0, 8);
			return true;
		}
		return false;
	}

	// The night's "g103+9": the weapon, the armour and the helmet of 103 on average at +9 on average.
	bool IsPlayerBotYdgGateStrong(LPCHARACTER ch)
	{
		int plus = 0;
		const int gear = GetPlayerBotYdgGearLevel(ch, &plus);
		return gear >= GetPlayerBotYdgEnv("PLAYERBOT_YDG_GATE_STRONG_GEAR", 103, 0, 250) &&
				plus >= GetPlayerBotYdgEnv("PLAYERBOT_YDG_GATE_STRONG_PLUS", 9, 0, 15);
	}

	// One bot: the floor (strict: the party's average - the clock's draw, whose parties are random).
	bool IsPlayerBotYdgGateBotOk(const TPlayerBotDgRunDef& def, LPCHARACTER ch, bool strict)
	{
		TPlayerBotYdgGate g;
		if (!GetPlayerBotYdgGate(def, g))
			return true;
		if (!ch)
			return false;
		return GetPlayerBotYdgGearLevel(ch, NULL) >= (strict ? std::max(g.iBotGear, g.iAvgGear) : g.iBotGear);
	}

	// A party: the average and the strong ones (why: "gate(avg=.. strong=..)" when it falls short).
	bool IsPlayerBotYdgGatePartyOk(const TPlayerBotDgRunDef& def, const std::vector<DWORD>& pids, std::string* why)
	{
		TPlayerBotYdgGate g;
		if (!GetPlayerBotYdgGate(def, g))
			return true;
		int n = 0, sum = 0, strong = 0;
		for (size_t i = 0; i < pids.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
			if (!c)
				continue;
			++n;
			sum += GetPlayerBotYdgGearLevel(c, NULL);
			strong += IsPlayerBotYdgGateStrong(c) ? 1 : 0;
		}
		const int avg = n ? sum / n : 0;
		const bool ok = n > 0 && avg >= g.iAvgGear && strong >= std::min(g.iStrong, n);
		if (!ok && why && why->size() < 400)
		{
			char buf[128];
			snprintf(buf, sizeof(buf), "%s_gate(n=%d,avg=%d/%d,strong=%d/%d)", def.szKey, n, avg, g.iAvgGear, strong, std::min(g.iStrong, n));
			*why += std::string(why->empty() ? "" : ",") + buf;
		}
		return ok;
	}

	// ------------------------------------------------------------ what the guard asks

	bool IsPlayerBotGlebieEntryOk(const TPlayerBotDgRunDef& def, LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_YDG_GATE_V1: the floor of the gear (Swiatynia Wezy's too - this is every YDG row's check)
		if (!IsPlayerBotYdgGateBotOk(def, ch, false))
			return false;
		const int kind = GetPlayerBotGlebieKind(def);
		if (!kind)
			return true;
		if (!ch || (int)ch->GetLevel() < PLAYERBOT_GLEBIE_MIN_LEVEL || ch->GetConquerorLevel() < 1)
			return false;
		return kind == 1 || ch->GetQuestFlag("ymaps3_glebie.weak_done") >= PLAYERBOT_GLEBIE_WEAK_NEEDED;
	}

	// A training (Dropki) party's members for Glebie and Swiatynia Wezy (the others' rows: true).
	bool IsPlayerBotGlebiePartyOk(int def, const std::vector<playerbot_dgrun::TCand>& free, std::string& why)
	{
		if (def < 0 || def >= PLAYERBOT_DGRUN_DEF_COUNT)
			return true;
		TPlayerBotYdgGate g;
		if (!GetPlayerBotGlebieKind(PLAYERBOT_DGRUN_DEFS[def]) && !GetPlayerBotYdgGate(PLAYERBOT_DGRUN_DEFS[def], g))
			return true;
		bool ok = true;
		std::vector<DWORD> pids;
		for (size_t i = 0; i < free.size(); ++i)
		{
			pids.push_back(free[i].pid);
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(free[i].pid);
			if (c && IsPlayerBotGlebieEntryOk(PLAYERBOT_DGRUN_DEFS[def], c))
				continue;
			ok = false;
			if (why.size() < 400)
				why += std::string(why.empty() ? "" : ",") + (c ? c->GetName() : "?") + ":" + PLAYERBOT_DGRUN_DEFS[def].szKey + "_req";
		}
		// MT2009_PLUS_BOT_YDG_GATE_V1: the party together
		if (ok && !IsPlayerBotYdgGatePartyOk(PLAYERBOT_DGRUN_DEFS[def], pids, &why))
			ok = false;
		return ok;
	}

	// An "auto" line of Glebie alone takes the bots that may go in (120, a Champion level).
	// MT2009_PLUS_BOT_YDG_GATE_V1: a line of the gated rows alone (Glebie, Swiatynia Wezy) takes the bots that one of
	// them lets in (the gear's floor; the weak Glebie for the strong one's weak runs).
	bool IsPlayerBotGlebieAutoOk(LPCHARACTER ch, const std::vector<int>& defs)
	{
		if (defs.empty())
			return true;
		TPlayerBotYdgGate g;
		for (size_t i = 0; i < defs.size(); ++i)
			if (defs[i] < 0 || defs[i] >= PLAYERBOT_DGRUN_DEF_COUNT ||
					(!GetPlayerBotGlebieKind(PLAYERBOT_DGRUN_DEFS[defs[i]]) && !GetPlayerBotYdgGate(PLAYERBOT_DGRUN_DEFS[defs[i]], g)))
				return true;
		if (!ch)
			return false;
		for (size_t i = 0; i < defs.size(); ++i)
		{
			const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[defs[i]];
			if (GetPlayerBotGlebieKind(def) == 2)
			{
				// the strong one's party goes weak while a member lacks the weak wins - the strong floor of the gear
				if (IsPlayerBotYdgGateBotOk(def, ch, false) && (int)ch->GetLevel() >= PLAYERBOT_GLEBIE_MIN_LEVEL &&
						ch->GetConquerorLevel() >= 1)
					return true;
			}
			else if (IsPlayerBotGlebieEntryOk(def, ch))
				return true;
		}
		return false;
	}

	// An "auto" party of the gated rows alone that none of them lets in (the party's average, its strong ones) is not
	// formed - true: it may go somewhere of its line (or the line has an ungated row).
	bool IsPlayerBotYdgGateAutoPartyOk(const std::vector<int>& defs, const std::vector<DWORD>& pids, std::string& why)
	{
		TPlayerBotYdgGate g;
		bool weakOrOther = false;
		for (size_t i = 0; i < defs.size(); ++i)
		{
			if (defs[i] < 0 || defs[i] >= PLAYERBOT_DGRUN_DEF_COUNT)
				return true;
			const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[defs[i]];
			if (!GetPlayerBotYdgGate(def, g))
				return true;
			// the strong Glebie only after the weak runs - beside the weak one its party is judged by the weak one's gate
			if (GetPlayerBotGlebieKind(def) == 2)
				continue;
			weakOrOther = true;
			if (IsPlayerBotYdgGatePartyOk(def, pids, &why))
				return true;
		}
		if (!weakOrOther)	// a line of the strong Glebie alone
			for (size_t i = 0; i < defs.size(); ++i)
				if (IsPlayerBotYdgGatePartyOk(PLAYERBOT_DGRUN_DEFS[defs[i]], pids, &why))
					return true;
		return false;
	}

	// At the way in (the bot in the instance already): the quest's players and kind, and the three keys.
	long long ChargePlayerBotGlebieKeys(LPCHARACTER ch, const TPlayerBotDgRunDef& def)
	{
		const int kind = GetPlayerBotGlebieKind(def);
		if (!ch || !kind)
			return 0;
		LPDUNGEON d = CDungeonManager::instance().FindByMapIndex(ch->GetMapIndex());
		int slot = 0;
		if (d)
		{
			if (d->GetFlag("kind") == 0)
				d->SetFlag("kind", kind);
			const int pid = (int)ch->GetPlayerID();
			for (int i = 1; i <= 8 && !slot; ++i)
			{
				char key[8];
				snprintf(key, sizeof(key), "p%d", i);
				const int p = d->GetFlag(key);
				if (p == pid)
					slot = i;
				else if (p == 0)
				{
					d->SetFlag(key, pid);
					slot = i;
				}
			}
		}
		const int have = ch->IsItemLoaded() ? (int)ch->CountSpecifyItem(PLAYERBOT_GLEBIE_KEY) : 0;
		const int own = std::min(have, PLAYERBOT_GLEBIE_KEYS);
		const int missing = PLAYERBOT_GLEBIE_KEYS - own;
		long long paid = 0;
		const long long price = (long long)GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_KEY_PRICE", (int)PLAYERBOT_GLEBIE_KEY_PRICE, 0, 2000000000);
		bool letGo = false;
		if (missing > 0)
		{
			// Bought from a player on the market (Wodz Wojenny Schronienia's drop, one a kill).
			if (price > 0 && (long long)ch->GetGold() >= price * missing)
			{
				paid = price * missing;
				PlayerBotChangeGold(ch, -paid);
			}
			else
				letGo = true;
		}
		if (own > 0)
			ch->RemoveSpecifyItem(PLAYERBOT_GLEBIE_KEY, (ITEM_COUNT)own);
		sys_log(0, "BOT_GLEBIE: keys pid=%u name=%s dungeon=%s own=%d bought=%d paid=%lld let_go=%d gold=%lld slot=%d weak_done=%d",
				ch->GetPlayerID(), ch->GetName(), def.szKey, own, letGo ? 0 : missing, paid, letGo ? 1 : 0, (long long)ch->GetGold(),
				slot, ch->GetQuestFlag("ymaps3_glebie.weak_done"));
		return paid;
	}

	// ------------------------------------------------------------ the quest's flags

	int GetPlayerBotGlebieStage(LPDUNGEON d)
	{
		if (!d || d->GetFlag("init") != 1)
			return 0;
		if (d->GetFlag("won") == 1)
			return 3;
		return d->GetFlag("awake") == 1 ? 2 : 1;
	}

	long long GetPlayerBotGlebieSignature(LPDUNGEON d)
	{
		if (!d || d->GetFlag("init") != 1 || d->GetFlag("p1") == 0)
			return 0;
		static const char* const flags[] = { "awake", "berserk", "wrath", "colds", "eggs", "won" };
		long long sig = 0;
		for (size_t i = 0; i < sizeof(flags) / sizeof(flags[0]); ++i)
			sig = sig * 31LL + d->GetFlag(flags[i]);
		return sig;
	}

	int GetPlayerBotGlebieEggWanted(long instance)
	{
		for (std::map<int, TPlayerBotGlebieRun>::const_iterator it = s_mapPlayerBotGlebieRuns.begin(); it != s_mapPlayerBotGlebieRuns.end(); ++it)
		{
			std::map<int, TPlayerBotDgRun>::const_iterator r = s_mapPlayerBotDgRuns.find(it->first);
			if (r != s_mapPlayerBotDgRuns.end() && r->second.lInstance == instance)
				return it->second.iEggWanted;
		}
		return 0;
	}

	void GetPlayerBotGlebieObjectives(const TPlayerBotDgRunDef& def, LPDUNGEON d, const TPlayerBotArzDgScan& scan,
			std::vector<DWORD>& out)
	{
		const int stage = GetPlayerBotGlebieStage(d);
		if (stage == 1)
		{
			// the crystal (the egg chamber's way) only when somebody will break the eggs
			if (GetPlayerBotGlebieEggWanted(d->GetMapIndex()) > 0)
				out.push_back(PLAYERBOT_GLEBIE_CRYSTAL);
		}
		else if (stage == 2)
			out.push_back(PLAYERBOT_GLEBIE_BOSS[GetPlayerBotGlebieDKind(d)]);
		(void)def;
		(void)scan;
	}

	// Before Alastor: by the egg, where he wakes.
	bool GetPlayerBotGlebieCamp(LPDUNGEON d, long& x, long& y)
	{
		if (GetPlayerBotGlebieStage(d) != 1)
			return false;
		return GetPlayerBotGlebieWorld(d->GetMapIndex(), PLAYERBOT_GLEBIE_CAMP_X, PLAYERBOT_GLEBIE_CAMP_Y, x, y);
	}

	// ------------------------------------------------------------ the leader's touch, and the boss's minute

	bool ShouldPlayerBotGlebieWake(const TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		std::map<int, TPlayerBotGlebieRun>::iterator gi = s_mapPlayerBotGlebieRuns.find(run.iId);
		if (!d || gi == s_mapPlayerBotGlebieRuns.end() || d->GetFlag("init") != 1)
			return false;
		TPlayerBotGlebieRun& gr = gi->second;
		const int kind = GetPlayerBotGlebieDKind(d);
		// the boss's minute (and what the quest did meanwhile)
		gr.iBerserk = d->GetFlag("berserk");
		gr.iWrath = d->GetFlag("wrath");
		gr.iColds = d->GetFlag("colds");
		gr.iEggsMax = std::max(gr.iEggsMax, d->GetFlag("eggs"));
		if (d->GetFlag("awake") == 1 && d->GetFlag("closed") == 0)
		{
			LPCHARACTER boss = CHARACTER_MANAGER::instance().Find(d->GetUniqueVid("alastor"));
			const int pct = boss && boss->GetMaxHP() > 0 ? (int)((long long)boss->GetHP() * 100 / boss->GetMaxHP()) : -1;
			if (pct >= 0)
				gr.iBossLow = std::min(gr.iBossLow, pct);
			if (gr.dwNextBossLog == 0 || (int)(dwNow - gr.dwNextBossLog) >= 0)
			{
				gr.dwNextBossLog = dwNow + PLAYERBOT_GLEBIE_BOSS_LOG_MS;
				int alive = 0, inside = 0;
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (!c || c->GetMapIndex() != run.lInstance)
						continue;
					++inside;
					alive += c->IsDead() ? 0 : 1;
				}
				sys_log(0, "BOT_GLEBIE: boss run=%d kind=%d hp=%d%% low=%d%% spent_s=%d berserk=%d wrath=%d colds=%d eggs=%d inside=%d alive=%d "
						"deaths=%d dodges=%d egg_bots=%u", run.iId, kind, pct, gr.iBossLow, get_global_time() - d->GetFlag("start"), gr.iBerserk,
						gr.iWrath, gr.iColds, d->GetFlag("eggs"), inside, alive, run.iDeaths, gr.iDodges, (unsigned int)gr.eggBots.size());
			}
		}
		if (d->GetFlag("awake") != 0 || d->GetFlag("closed") == 1)
			return false;
		const int spent = get_global_time() - d->GetFlag("start");
		const int wakeAt = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_WAKE_S", 0, 0, 1500);
		if (spent < wakeAt)
			return false;
		const char* why = "ready";
		if (gr.iEggWanted > 0 && IsPlayerBotGlebieStanding(run.lInstance, PLAYERBOT_GLEBIE_CRYSTAL))
		{
			if (spent < wakeAt + (int)PLAYERBOT_GLEBIE_CRYSTAL_WAIT_S)
				return false;
			why = "crystal_standing";
		}
		// the leader by the egg with its pack (the leader holds the others; a pack that cannot come is not waited for)
		LPCHARACTER lead = run.dwLeader ? CHARACTER_MANAGER::instance().FindByPID(run.dwLeader) : NULL;
		long ex = 0, ey = 0;
		GetPlayerBotGlebieWorld(run.lInstance, PLAYERBOT_GLEBIE_CAMP_X, PLAYERBOT_GLEBIE_CAMP_Y, ex, ey);
		int inside = 0, near = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->GetMapIndex() != run.lInstance || c->IsDead())
				continue;
			++inside;
			if (DISTANCE_APPROX(c->GetX() - ex, c->GetY() - ey) <= 1500)
				++near;
		}
		const bool leadReady = lead && !lead->IsDead() && lead->GetMapIndex() == run.lInstance &&
				DISTANCE_APPROX(lead->GetX() - ex, lead->GetY() - ey) <= 1500;
		if (!leadReady || near * 2 < inside)
		{
			if (spent < wakeAt + (int)PLAYERBOT_GLEBIE_CRYSTAL_WAIT_S + (int)PLAYERBOT_GLEBIE_GATHER_WAIT_S)
				return false;
			why = "waited";
		}
		if (!gr.bWakeAsked)
			sys_log(0, "BOT_GLEBIE: wake run=%d kind=%d spent_s=%d inside=%d near=%d why=%s leader=%s", run.iId, kind, spent, inside, near,
					why, lead ? lead->GetName() : "-");
		gr.bWakeAsked = true;
		return true;
	}

	// ------------------------------------------------------------ the ground zones

	struct FPlayerBotGlebieMarks
	{
		long m_lMap, m_lX, m_lY;
		int m_iRange;
		std::vector<std::pair<long, long> > m_pts;
		FPlayerBotGlebieMarks(LPCHARACTER ch, int range) : m_lMap(ch->GetMapIndex()), m_lX(ch->GetX()), m_lY(ch->GetY()), m_iRange(range) {}
		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER c = (LPCHARACTER)ent;
			if (c->IsPC() || c->GetRaceNum() != PLAYERBOT_GLEBIE_ZONE_MARK || c->GetMapIndex() != m_lMap)
				return;
			if (DISTANCE_APPROX(c->GetX() - m_lX, c->GetY() - m_lY) <= m_iRange)
				m_pts.push_back(std::make_pair(c->GetX(), c->GetY()));
		}
	};

	int GetPlayerBotGlebieNearestMark(const std::vector<std::pair<long, long> >& pts, long x, long y)
	{
		int best = INT_MAX;
		for (size_t i = 0; i < pts.size(); ++i)
			best = std::min(best, DISTANCE_APPROX(pts[i].first - x, pts[i].second - y));
		return best;
	}

	// The step out of a ground zone alone (no run bonus): a bots' run's member after its rebuff below, and
	// MT2009_PLUS_NAJEMNICY_V4 a player's mercenary in its owner's Glebie (playerbot_najemnicy.h - its owner's run, no bonus).
	bool DodgePlayerBotGlebieZonesOnly(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !ch->GetSectree() || !GetPlayerBotGlebieRunKind(run))
			return false;
		const int avoid = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_ZONE_AVOID", 620, 0, 1500);
		if (avoid <= 0)
			return false;
		FPlayerBotGlebieMarks marks(ch, PLAYERBOT_GLEBIE_MARK_SCAN);
		ch->GetSectree()->ForEachAround(marks);
		TPlayerBotGlebieDodge& dg = s_mapPlayerBotGlebieDodge[ch->GetPlayerID()];
		const int here = GetPlayerBotGlebieNearestMark(marks.m_pts, ch->GetX(), ch->GetY());
		// a step under way: on to its spot while the spot is still clear
		if (dg.dwUntil && (int)(dg.dwUntil - dwNow) > 0 && DISTANCE_APPROX(ch->GetX() - dg.x, ch->GetY() - dg.y) > 150 &&
				GetPlayerBotGlebieNearestMark(marks.m_pts, dg.x, dg.y) > avoid)
		{
			if ((int)(dwNow - dg.dwNextMove) >= 0)
			{
				dg.dwNextMove = dwNow + 400;
				MovePlayerBot(ch, dg.x, dg.y, dwNow, 2, true, false);
			}
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			return true;
		}
		dg.dwUntil = 0;
		if (here > avoid)
			return false;
		// the nearest safe ground by the fight: the bot's target, else the leader, else where it stands
		LPCHARACTER anchor = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		if (!anchor || anchor->IsDead() || anchor->GetMapIndex() != ch->GetMapIndex())
			anchor = run.dwLeader && run.dwLeader != ch->GetPlayerID() ? CHARACTER_MANAGER::instance().FindByPID(run.dwLeader) : NULL;
		if (anchor && anchor->GetMapIndex() != ch->GetMapIndex())
			anchor = NULL;
		const long ax = anchor ? anchor->GetX() : ch->GetX(), ay = anchor ? anchor->GetY() : ch->GetY();
		static const int dirX[16] = { 1000, 924, 707, 383, 0, -383, -707, -924, -1000, -924, -707, -383, 0, 383, 707, 924 };
		static const int dirY[16] = { 0, 383, 707, 924, 1000, 924, 707, 383, 0, -383, -707, -924, -1000, -924, -707, -383 };
		static const int rings[4] = { 750, 1000, 1300, 1700 };
		long bx = 0, by = 0;
		long long bestScore = -1;
		for (int r = 0; r < 4; ++r)
			for (int k = 0; k < 16; ++k)
			{
				const long px = ch->GetX() + (long)dirX[k] * (avoid + rings[r] - 620) / 1000;
				const long py = ch->GetY() + (long)dirY[k] * (avoid + rings[r] - 620) / 1000;
				if (!SECTREE_MANAGER::instance().IsMovablePosition(ch->GetMapIndex(), px, py))
					continue;
				if (GetPlayerBotGlebieNearestMark(marks.m_pts, px, py) <= avoid + 120)
					continue;
				const long long score = (long long)DISTANCE_APPROX(px - ax, py - ay) + (long long)rings[r];
				if (bestScore < 0 || score < bestScore)
				{
					bestScore = score;
					bx = px;
					by = py;
				}
			}
		if (bestScore < 0)
			return false;
		dg.x = bx;
		dg.y = by;
		dg.dwUntil = dwNow + PLAYERBOT_GLEBIE_DODGE_MS;
		dg.dwNextMove = dwNow + 400;
		ch->SetVictim(NULL);
		ClearPlayerBotRoute(state, false);
		MovePlayerBot(ch, bx, by, dwNow, 2, true, false);
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		std::map<int, TPlayerBotGlebieRun>::iterator gi = s_mapPlayerBotGlebieRuns.find(run.iId);
		if (gi != s_mapPlayerBotGlebieRuns.end())
			++gi->second.iDodges;
		PlayerBotLogThrottled("glebie_dodge", dwNow, "BOT_GLEBIE: dodge run=%d name=%s marks=%u nearest=%d to=(%ld,%ld) hp=%d%%",
				run.iId, ch->GetName(), (unsigned int)marks.m_pts.size(), here, bx, by,
				ch->GetMaxHP() > 0 ? (int)((long long)ch->GetHP() * 100 / ch->GetMaxHP()) : 0);
		return true;
	}

	bool DodgePlayerBotGlebieZones(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !ch->GetSectree() || !GetPlayerBotGlebieRunKind(run))
			return false;
		// MT2009_PLUS_BOT_GLEBIE_REBUFF_V1 (night 6/7 November): a death clears the run's bonuses (BuffPlayerBotYdgMember,
		// the Sung Ma Will) - with 100+ deaths a fight most of the party fought Alastor without them after the first
		// minutes (Alastor back at 97-100% after the berserks, 2 of 2 weak runs wiped at 22:40-23:30). Given again on the
		// first tick standing, as the Gnolle and the Wieza do. Off: event flag m2_bot_glebie_rebuff_off.
		if (!ch->FindAffect(AFFECT_PLAYERBOT_YDG_MONSTER) &&
				quest::CQuestManager::instance().GetEventFlag("m2_bot_glebie_rebuff_off") == 0)
		{
			BuffPlayerBotYdgMember(ch);
			BuffPlayerBotYdgSungma(ch, PLAYERBOT_GLEBIE_MAP);
			PlayerBotLogThrottled("glebie_rebuff", dwNow, "BOT_GLEBIE: rebuff run=%d name=%s hp=%d/%d", run.iId, ch->GetName(),
					ch->GetHP(), ch->GetMaxHP());
		}
		return DodgePlayerBotGlebieZonesOnly(ch, state, run, dwNow);
	}

	// ------------------------------------------------------------ the egg chamber

	void PickPlayerBotGlebieEggBots(TPlayerBotDgRun& run, TPlayerBotGlebieRun& gr)
	{
		gr.bEggPicked = true;
		if (gr.iEggWanted <= 0)
			return;
		// Ninja, Sura, Warrior; never the leader or a healing Shaman
		// MT2009_PLUS_BOT_GLEBIE_EGGS_V2: within a class the strongest first (ScorePlayerBotYdg - the eggs are 4.5 / 6 M)
		static const int order[3] = { JOB_ASSASSIN, JOB_SURA, JOB_WARRIOR };
		for (int o = 0; o < 3 && (int)gr.eggBots.size() < gr.iEggWanted; ++o)
		{
			std::vector<std::pair<long long, DWORD> > cands;
			for (size_t i = 0; i < run.members.size(); ++i)
			{
				const DWORD pid = run.members[i];
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pid);
				if (!c || pid == run.dwLeader || gr.eggBots.count(pid) || (int)(c->GetJob() % 4) != order[o] ||
						c->GetMapIndex() != run.lInstance)
					continue;
				cands.push_back(std::make_pair(ScorePlayerBotYdg(c), pid));
			}
			std::sort(cands.begin(), cands.end(), [](const std::pair<long long, DWORD>& a, const std::pair<long long, DWORD>& b)
					{ return a.first > b.first; });
			for (size_t i = 0; i < cands.size() && (int)gr.eggBots.size() < gr.iEggWanted; ++i)
			{
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(cands[i].second);
				gr.eggBots.insert(cands[i].second);
				sys_log(0, "BOT_GLEBIE: egg duty run=%d name=%s job=%u gear=%d", run.iId, c ? c->GetName() : "?",
						c ? (unsigned int)c->GetJob() : 0, c ? GetPlayerBotYdgGearLevel(c, NULL) : 0);
			}
		}
	}

	// MT2009_PLUS_BOT_GLEBIE_EGGS_V2: the egg killers' egg - the most hurt one (the least health left), ties the nearest:
	// two killers on one egg finish it (an egg dead delays the Deadly Cold by 20 s and takes one off the berserk count),
	// two on two eggs spread their blows and the night's eggs_max grew 3 a minute unbroken.
	LPCHARACTER FindPlayerBotGlebieEggFocus(LPCHARACTER ch, DWORD race)
	{
		LPSECTREE_MAP pMap = ch ? SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex()) : NULL;
		if (!pMap)
			return NULL;
		struct FEgg
		{
			DWORD race;
			long map, x, y;
			long long hp;
			int dist;
			LPCHARACTER found;
			void operator()(LPENTITY ent)
			{
				if (!ent || !ent->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER c = (LPCHARACTER)ent;
				if (c->IsPC() || c->IsDead() || c->GetRaceNum() != race || c->GetMapIndex() != map)
					return;
				const long long h = (long long)c->GetHP();
				const int dd = DISTANCE_APPROX(c->GetX() - x, c->GetY() - y);
				if (!found || h < hp || (h == hp && dd < dist))
				{
					found = c;
					hp = h;
					dist = dd;
				}
			}
		} f = { race, ch->GetMapIndex(), ch->GetX(), ch->GetY(), 0, 0, NULL };
		pMap->for_each(f);
		return f.found;
	}

	// Through a GOTO portal of the instance - what its warp event does for a person standing on it.
	bool UsePlayerBotGlebiePortal(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, DWORD portalRace, long toX,
			long toY, DWORD dwNow)
	{
		LPCHARACTER portal = FindPlayerBotGlebieRace(ch, portalRace);
		if (!portal)
			return false;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (DISTANCE_APPROX(ch->GetX() - portal->GetX(), ch->GetY() - portal->GetY()) > PLAYERBOT_GLEBIE_PORTAL_TOUCH)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			if (dwNow >= state.dwNextTowerMoveTime)
			{
				state.dwNextTowerMoveTime = dwNow + 800;
				MovePlayerBot(ch, portal->GetX(), portal->GetY(), dwNow, 2, true, false);
			}
			return true;
		}
		long x = 0, y = 0;
		if (!GetPlayerBotGlebieWorld(ch->GetMapIndex(), toX, toY, x, y))
			return false;
		if (ch->IsStateMove())
			ch->Stop();
		ClearPlayerBotRoute(state, true);
		playerbot_monkey::NoteGotoCrossing(ch->GetPlayerID(), dwNow);	// the portal's own event leaves it be now
		ch->Show(ch->GetMapIndex(), x, y);
		ch->Stop();
		std::map<int, TPlayerBotGlebieRun>::iterator gi = s_mapPlayerBotGlebieRuns.find(run.iId);
		if (gi != s_mapPlayerBotGlebieRuns.end())
			++gi->second.iPortals;
		sys_log(0, "BOT_GLEBIE: portal run=%d name=%s portal=%u to=(%ld,%ld)", run.iId, ch->GetName(), (unsigned int)portalRace, toX, toY);
		return true;
	}

	bool ManagePlayerBotGlebieBot(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		std::map<int, TPlayerBotGlebieRun>::iterator gi = s_mapPlayerBotGlebieRuns.find(run.iId);
		if (gi == s_mapPlayerBotGlebieRuns.end())
			return false;
		TPlayerBotGlebieRun& gr = gi->second;
		long lx = 0, ly = 0;
		if (!GetPlayerBotGlebieLocal(ch, lx, ly))
			return false;
		const bool inChamber = lx >= PLAYERBOT_GLEBIE_CHAMBER_FROM_X;
		const int stage = GetPlayerBotGlebieStage(d);
		if (stage == 2 && !gr.bEggPicked)
			PickPlayerBotGlebieEggBots(run, gr);
		const bool eggBot = stage == 2 && gr.eggBots.count(ch->GetPlayerID()) != 0;
		if (!eggBot)
		{
			// back to the hall by the chamber's portal
			if (inChamber && stage >= 1 && stage <= 2)
				return UsePlayerBotGlebiePortal(ch, state, run, PLAYERBOT_GLEBIE_PORTAL_OUT, PLAYERBOT_GLEBIE_HALL_IN_X,
						PLAYERBOT_GLEBIE_HALL_IN_Y, dwNow);
			return false;
		}
		const DWORD eggRace = PLAYERBOT_GLEBIE_EGG[GetPlayerBotGlebieDKind(d)];
		if (!inChamber)
		{
			if (UsePlayerBotGlebiePortal(ch, state, run, PLAYERBOT_GLEBIE_PORTAL_IN, PLAYERBOT_GLEBIE_CHAMBER_IN_X,
					PLAYERBOT_GLEBIE_CHAMBER_IN_Y, dwNow))
				return true;
			LPCHARACTER crystal = FindPlayerBotGlebieRace(ch, PLAYERBOT_GLEBIE_CRYSTAL);
			if (crystal && IsPlayerBotPdgFoe(ch, crystal))
				return FightPlayerBotTowerObjective(ch, state, crystal, dwNow);
			return false;	// no way in: with the pack
		}
		// in the chamber: what attacks it, then the eggs, else by the chamber's middle
		LPCHARACTER threat = FindPlayerBotDgRunThreat(ch, run.iId);
		if (threat && threat->GetVictim() == ch)
			return FightPlayerBotTowerObjective(ch, state, threat, dwNow);
		LPCHARACTER egg = FindPlayerBotGlebieEggFocus(ch, eggRace);	// MT2009_PLUS_BOT_GLEBIE_EGGS_V2: one egg at a time
		if (egg && IsPlayerBotPdgFoe(ch, egg))
		{
			PlayerBotLogThrottled("glebie_egg", dwNow, "BOT_GLEBIE: egg run=%d name=%s eggs=%d", run.iId, ch->GetName(), d->GetFlag("eggs"));
			return FightPlayerBotTowerObjective(ch, state, egg, dwNow);
		}
		if (threat)
			return FightPlayerBotTowerObjective(ch, state, threat, dwNow);
		long cx = 0, cy = 0;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (GetPlayerBotGlebieWorld(ch->GetMapIndex(), PLAYERBOT_GLEBIE_CHAMBER_X, PLAYERBOT_GLEBIE_CHAMBER_Y, cx, cy) &&
				DISTANCE_APPROX(ch->GetX() - cx, ch->GetY() - cy) > 600)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			if (dwNow >= state.dwNextTowerMoveTime)
			{
				state.dwNextTowerMoveTime = dwNow + 1500;
				MovePlayerBot(ch, cx, cy, dwNow, 6, true, false);
			}
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// ------------------------------------------------------------ the run's start and end

	void NotePlayerBotGlebieRunStart(const TPlayerBotDgRun& run)
	{
		const int kind = GetPlayerBotGlebieRunKind(run);
		if (!kind)
			return;
		TPlayerBotGlebieRun& gr = s_mapPlayerBotGlebieRuns[run.iId];
		gr = TPlayerBotGlebieRun();
		gr.iKind = kind;
		const int env = GetPlayerBotYdgEnv("PLAYERBOT_GLEBIE_EGG_BOTS", -1, -1, 3);
		// MT2009_PLUS_BOT_GLEBIE_EGGS_V2 (6 November): one killer alone broke next to no egg (eggs_max 33-77 in the
		// long fights, 3 a minute unbroken) - two in a party of seven or more (the gated parties), focused on one egg.
		gr.iEggWanted = env >= 0 ? env : (run.members.size() >= 7 ? 2 : (run.members.size() >= 5 ? 1 : 0));
		const champion::SungmaRequirement* req = champion::MapRequirement(PLAYERBOT_GLEBIE_MAP);
		std::string mix;
		int meets = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			const int s = yohara_gear::SungmaEffective(c, POINT_SUNGMA_STR), h = yohara_gear::SungmaEffective(c, POINT_SUNGMA_HP);
			const int m = yohara_gear::SungmaEffective(c, POINT_SUNGMA_MOVE), n = yohara_gear::SungmaEffective(c, POINT_SUNGMA_IMMUNE);
			const bool ok = !req || (s >= req->str && h >= req->hp && m >= req->move && n >= req->immune);
			meets += ok ? 1 : 0;
			char buf[128];
			snprintf(buf, sizeof(buf), "%s%s:c%d/w%d/sm%d-%d-%d-%d%s", mix.empty() ? "" : ",", c->GetName(), (int)c->GetConquerorLevel(),
					c->GetQuestFlag("ymaps3_glebie.weak_done"), s, h, m, n, ok ? "" : "!");
			mix += buf;
		}
		sys_log(0, "BOT_GLEBIE: run start run=%d kind=%d instance=%ld egg_bots=%d sungma_req=%d-%d-%d-%d meets=%d/%u members=%s", run.iId,
				kind, run.lInstance, gr.iEggWanted, req ? req->str : 0, req ? req->hp : 0, req ? req->move : 0, req ? req->immune : 0,
				meets, (unsigned int)run.members.size(), mix.c_str());
	}

	// The chests the quest leaves at Upiorny Straznik for each player of the instance ("Odbierz nagrode").
	void NotePlayerBotGlebieRunEnd(const TPlayerBotDgRun& run)
	{
		const int kind = GetPlayerBotGlebieRunKind(run);
		if (!kind)
			return;
		std::string got;
		int chests = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || !c->IsItemLoaded())
				continue;
			s_mapPlayerBotGlebieDodge.erase(run.members[i]);
			const int reward = c->GetQuestFlag("ymaps3_glebie.reward");
			if (reward != 1 && reward != 2)
				continue;
			MakePlayerBotYdgRoom(c, "glebie_chests");
			c->SetQuestFlag("ymaps3_glebie.reward", 0);
			LPITEM item = c->AutoGiveItem(PLAYERBOT_GLEBIE_REWARD[reward], PLAYERBOT_GLEBIE_REWARD_COUNT, -1, false);
			chests += item ? PLAYERBOT_GLEBIE_REWARD_COUNT : 0;
			if (got.size() < 300)
				got += std::string(got.empty() ? "" : ",") + c->GetName() + ":" + std::to_string(c->GetQuestFlag("ymaps3_glebie.weak_done"));
		}
		std::map<int, TPlayerBotGlebieRun>::iterator gi = s_mapPlayerBotGlebieRuns.find(run.iId);
		const TPlayerBotGlebieRun gr = gi != s_mapPlayerBotGlebieRuns.end() ? gi->second : TPlayerBotGlebieRun();
		sys_log(0, "BOT_GLEBIE: run end run=%d kind=%d won=%d result=%s stage=%d boss_low=%d%% berserk=%d wrath=%d colds=%d eggs_max=%d "
				"deaths=%d wipes=%d dodges=%d portals=%d egg_bots=%u chests=%d weak_done=%s", run.iId, kind, run.dwFinishedAt ? 1 : 0,
				run.szResult ? run.szResult : "-", run.iStage, gr.iBossLow, gr.iBerserk, gr.iWrath, gr.iColds, gr.iEggsMax, run.iDeaths,
				run.iWipes, gr.iDodges, gr.iPortals, (unsigned int)gr.eggBots.size(), chests, got.empty() ? "-" : got.c_str());
		if (gi != s_mapPlayerBotGlebieRuns.end())
			s_mapPlayerBotGlebieRuns.erase(gi);
	}
}

#endif
