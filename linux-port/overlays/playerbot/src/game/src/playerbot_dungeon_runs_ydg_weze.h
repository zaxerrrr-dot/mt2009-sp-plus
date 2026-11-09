#ifndef __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_WEZE_H__
#define __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_WEZE_H__

// MT2009_PLUS_BOT_YDG_WEZE_V1 - Swiatynia Wezy (391, swiatynia_wezy.quest) as a bots' run (the owner, night of 5/6
// November 2026: "Naucz boty chodzic do: ... Swiatynia Wezy (7 poziomow) ... Masz moje pelne pozwolenie na zmiany
// botow, zeby mogly robic te dungeony"). The dungeon is never made weaker: no monster, boss, time or order changed -
// the bots do what a party of people does, by the quest's own flags.
//
// The row "swiatynia" of PLAYERBOT_DGRUN_DEFS (kind DGRUN_KIND_YDG, boss YDG_WEZE), so the YDG machinery carries it:
// the clock's calls (band 120+, rule "swiatynia": five called, four in, a Shaman), the training file
// playerbot_ydg_train ("auto 10 5 swiatynia", "party swiatynia <pids>"; "any" / "pb" leave the temple out), the run
// bonuses, the sticky objectives, the BOT_YDG / BOT_DGRUN lines and playerbot_ydg_runs.tsv.
//
// The way in (as a person's party at Statua Wezy, 390): level 120 (the panel's row and the rule's band; a training
// party's members under it stay out of this dungeon's call), the quest's five entries a day - the core counts them
// in swiatynia_wezy.day/runs as the quest's login does, and over them the bot renews them with a Wejscie do Swiatyni
// Wezy (70430: its own, else bought on the market for PLAYERBOT_WEZE_ENTRY_PRICE; a bot that cannot pay is let go,
// logged, as the YDG book), no fee. The quest's bots' half (MT2009_PLUS_BOT_YDG_WEZE_V1 in it): swiatynia_wezy_dgrun
// does the first login's init (the Portal, the hour's keep), swiatynia_wezy_dgrun_next the two talks a leader has -
// the Portal's "Rozpocznij walke!" (the time drawn, 10-60 minutes, the elements' order) and the Smith's "Przejdz na
// 7. poziom" - and Nethis's kill sets the d flag won. The bots are registered in the quest's p1..p8, so the surface
// attack strikes them and the reward is theirs, as a person's.
//
// Inside, the levels by the quest's flags (lvl, o1..o4, next, m1..m6, extra, opened, smith, turned, nethis):
//   1 (started 0): the leader's talk at once;
//   - Pyl Wezowy (70428): from the start the members use it (their own, else bought for PLAYERBOT_WEZE_DUST_PRICE
//     each - the market's) until the clock stands at the quest's 60 minutes, a minute a dust, the quest's use;
//   2: six minutes of groups - fought (the order of the first four elements is the quest's o1..o4, remembered);
//   3: the four Metins Wezowe in the order of o1..o4: the leader's objective is the next one, the other three are no
//      foe for any bot (IsPlayerBotWezeNoTarget - a wrong one brings back the fallen ones);
//   4: the Time Metins (8634), then the Warriors (6765, 6755 and its 0-3 more) - objectives;
//   5: the monsters drop Klucze Wezowe (70422): picked up and handed to the Kolumna Wezy standing where the 4th
//      level's Metin of that turn stood (m<opened+1>) - never a wrong one;
//   6: Klucze do Wiezienia (70427, from the 5th and 6th level) handed to the caged smiths (40% each frees one); after
//      the eight groups the Kowal Swiatyni Wezy - the leader's second talk;
//   7: Odlamki Weza (70423-70426) picked up; the one of the turn's element (o shifted left by the extra Warriors)
//      handed to its Glowa Weza, the others kept for their turn; then Nethis (6756) - the objective.
// At the run's end each member that was inside at Nethis's fall (the quest's reward flag) gets the statue's reward -
// 8 Skarb Wezy (70429) and the armour piece of its class (21326/21346/21366/21386) - and the temple's keys and shards
// leave its bag. The log: BOT_YDG: weze ... (registered, dust, entry, handed in, picked up, progress, reward).
//
// An implementation fragment: included after playerbot_dungeon_runs_ydg.h (whose helpers it uses), at the end of
// playerbot_dungeon_runs.h, in the anonymous namespace.

namespace
{
	const long PLAYERBOT_WEZE_MAP = 391;
	const int PLAYERBOT_WEZE_MIN_LEVEL = 120;
	const int PLAYERBOT_WEZE_DAILY = 5;
	const int PLAYERBOT_WEZE_LIMIT_MAX_S = 3600;		// cfg(): the Portal's 60 minutes at most
	const DWORD PLAYERBOT_WEZE_METIN_BASE = 8629;		// + the element (1 fire, 2 ice, 3 wind, 4 earth)
	const DWORD PLAYERBOT_WEZE_TIME_METIN = 8634;
	const DWORD PLAYERBOT_WEZE_WARRIOR_EARTH = 6765;
	const DWORD PLAYERBOT_WEZE_WARRIOR_ICE = 6755;
	const DWORD PLAYERBOT_WEZE_NETHIS = 6756;
	const DWORD PLAYERBOT_WEZE_COLUMN = 6757;
	const DWORD PLAYERBOT_WEZE_CAGED = 20842;
	const DWORD PLAYERBOT_WEZE_KEY = 70422;			// Klucz Wezowy
	const DWORD PLAYERBOT_WEZE_SHARD_BASE = 70422;		// + the element: Odlamek Weza 70423-70426
	const DWORD PLAYERBOT_WEZE_PRISON_KEY = 70427;		// Klucz do Wiezienia
	const DWORD PLAYERBOT_WEZE_DUST = 70428;		// Pyl Wezowy
	const DWORD PLAYERBOT_WEZE_TREASURE = 70429;		// Skarb Wezy
	const DWORD PLAYERBOT_WEZE_ENTRY = 70430;		// Wejscie do Swiatyni Wezy
	const int PLAYERBOT_WEZE_TREASURES = 8;
	const long long PLAYERBOT_WEZE_DUST_PRICE = 2500LL;	// playerbot_price_tables.h
	const long long PLAYERBOT_WEZE_ENTRY_PRICE = 9410000LL;	// playerbot_price_tables.h
	// cfg(): the element's Glowa Weza (el[i].head) and the class's armour piece (armour[job]).
	const DWORD PLAYERBOT_WEZE_HEADS[5] = { 0, 4025, 4024, 4026, 4027 };
	const DWORD PLAYERBOT_WEZE_ARMOUR[4] = { 21326, 21346, 21366, 21386 };
	// cfg(): the rooms (cells off the map's base) and the six places round a room's middle.
	const long PLAYERBOT_WEZE_ROOMS[8][2] = { { 0, 0 }, { 127, 127 }, { 127, 127 }, { 383, 127 }, { 639, 127 }, { 383, 383 },
			{ 639, 383 }, { 127, 642 } };
	const long PLAYERBOT_WEZE_SIX[7][2] = { { 0, 0 }, { 35, -35 }, { -35, -35 }, { -35, 35 }, { 35, 35 }, { 35, 0 }, { -35, 0 } };
	const int PLAYERBOT_WEZE_COLUMN_RANGE = 1500;		// a Kolumna this near its place (the six are 3 500 apart)

	struct TPlayerBotWezeInstance
	{
		DWORD dwProgressAt;
		int iDustUsed, iDustFails, iDustBought;
		bool bDustDone;
		TPlayerBotWezeInstance() : dwProgressAt(0), iDustUsed(0), iDustFails(0), iDustBought(0), bDustDone(false) {}
	};
	std::map<long, TPlayerBotWezeInstance> s_mapPlayerBotWeze;

	bool IsPlayerBotWezeInstance(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN && mapIndex / 10000 == PLAYERBOT_WEZE_MAP;
	}

	bool IsPlayerBotWezeDungeon(LPDUNGEON d)
	{
		return d && IsPlayerBotWezeInstance(d->GetMapIndex());
	}

	int GetPlayerBotYdgDefMinLevel(int def)
	{
		if (def >= 0 && def < PLAYERBOT_DGRUN_DEF_COUNT && PLAYERBOT_DGRUN_DEFS[def].lMap == PLAYERBOT_WEZE_MAP)
			return PLAYERBOT_WEZE_MIN_LEVEL;
		return PLAYERBOT_YDG_MIN_LEVEL;
	}

	// The element of an order's flag (o1..o4), 1-4, or 0.
	int GetPlayerBotWezeOrder(LPDUNGEON d, int turn)
	{
		if (!d || turn < 1 || turn > 4)
			return 0;
		char name[8];
		snprintf(name, sizeof(name), "o%d", turn);
		const int e = d->GetFlag(name);
		return e >= 1 && e <= 4 ? e : 0;
	}

	// The 7th level's element now: level 2's order shifted left by the 4th level's extra Warriors.
	int GetPlayerBotWezeHeadWanted(LPDUNGEON d)
	{
		const int n = d->GetFlag("turned") + 1;
		if (n < 1 || n > 4)
			return 0;
		return GetPlayerBotWezeOrder(d, (n - 1 + d->GetFlag("extra")) % 4 + 1);
	}

	bool GetPlayerBotWezeSpot(long instance, int level, int six, long& x, long& y)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		if (!pMap || level < 1 || level > 7 || six < 0 || six > 6)
			return false;
		x = pMap->m_setting.iBaseX + (PLAYERBOT_WEZE_ROOMS[level][0] + PLAYERBOT_WEZE_SIX[six][0]) * 100;
		y = pMap->m_setting.iBaseY + (PLAYERBOT_WEZE_ROOMS[level][1] + PLAYERBOT_WEZE_SIX[six][1]) * 100;
		return true;
	}

	// ------------------------------------------------------------ the flags

	int GetPlayerBotWezeStage(LPDUNGEON d)
	{
		if (!d || d->GetFlag("started") != 1)
			return 1;
		const int lvl = std::max(2, std::min(7, d->GetFlag("lvl")));
		return lvl == 7 && d->GetFlag("nethis") == 1 ? 8 : lvl;
	}

	long long GetPlayerBotWezeSignature(LPDUNGEON d)
	{
		if (!IsPlayerBotWezeDungeon(d))
			return 0;
		static const char* const flags[] = { "started", "lvl", "g", "next", "dead_mask", "tm", "warrior", "extra_left", "tw4_n",
				"opened", "freed", "g6", "smith", "turned", "nethis", "limit_at" };
		long long sig = 0;
		for (size_t i = 0; i < sizeof(flags) / sizeof(flags[0]); ++i)
			sig = sig * 31LL + d->GetFlag(flags[i]);
		return sig;
	}

	// The night of 5/6 November (the first runs): the 4th level's Warrior waits for d.count_monster() == 0 and the 6th
	// level's Smith too, but the levels are rooms apart (391's grid: 6 parts) - a group of the 3rd (5th) level still
	// alive when the last Metin falls (the 6th Kolumna opens) stays in the old room for good and the temple stalls
	// ("tm=6 warrior=0" for 10+ minutes, the foes 250 cells away in room 3). A party of people clears the room before
	// the last blow; the bots too: the living monsters of the instance (not the Metins, the Kolumny, the cages).
	int CountPlayerBotWezeAdds(long instance)
	{
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(instance, get_dword_time());
		int n = 0;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD r = scan.foes[i].dwRace;
			if ((r > PLAYERBOT_WEZE_METIN_BASE && r <= PLAYERBOT_WEZE_TIME_METIN) || r == PLAYERBOT_WEZE_COLUMN || r == PLAYERBOT_WEZE_CAGED)
				continue;
			++n;
		}
		return n;
	}

	// The 3rd level's last Metin (next 4) left at a sliver while a group lives: the group first.
	// V2 (23:50): ten runs held for 10+ minutes by a Kappa Czarodziej (6747) the parties did not bring down - the hold
	// lasts PLAYERBOT_WEZE_HOLD_MAX_S at most, then the Metin falls whatever lives (logged).
	const DWORD PLAYERBOT_WEZE_HOLD_MAX_S = 180;
	std::map<long, DWORD> s_mapPlayerBotWezeHoldSince;	// instance -> get_global_time() the hold began

	// V3 (00:20): the parties hit only the turn's Metin and the 3rd level's groups (one every 40 s) piled up to 10-20
	// at 100% by the last Metin - the groups first on the 3rd level too (the Metin's turn kept), the same time limit.
	bool IsPlayerBotWezeAddsFirst(LPDUNGEON d, long instance)
	{
		if (!d || d->GetFlag("lvl") != 3)
			return false;
		const int adds = CountPlayerBotWezeAdds(instance);
		DWORD& since = s_mapPlayerBotWezeHoldSince[instance];
		if (adds <= 0)
		{
			since = 0;
			return false;
		}
		const DWORD now = get_global_time();
		if (since == 0)
			since = now;
		if (now - since > PLAYERBOT_WEZE_HOLD_MAX_S)
		{
			if (since != 1)
				sys_log(0, "BOT_YDG: weze adds-first over instance=%ld adds=%d after_s=%u - the Metin of the turn again", instance, adds, now - since);
			since = 1;	// over for this instance's level 3
			return false;
		}
		return true;
	}

	// V4 (03:35): the last Metin with no time limit - four runs fell into the 4th level with 20+ groups left in room 3
	// after the 180 s and were abandoned there (the Warrior never came); the bots now reach the groups (unstranded).
	// MT2009_PLUS_WEZE_ROOM_PURGE_V1 (6 November, day): the quest empties the room a party leaves (move_to), so the
	// groups of room 3 hold nothing any more - no hold at the last Metin (the groups-first turns above stay: a pile
	// of groups at 100% only hurts), the last Metin is the turn's like the other three.
	bool IsPlayerBotWezeHoldLastMetin(LPDUNGEON d, long instance, int hpPct)
	{
		(void)d;
		(void)instance;
		(void)hpPct;
		return false;
	}

	// The living monsters' races (not the Metins, the Kolumny, the cages) as objectives.
	void AddPlayerBotWezeAddRaces(long instance, std::vector<DWORD>& out)
	{
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(instance, get_dword_time());
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD r = scan.foes[i].dwRace;
			if ((r > PLAYERBOT_WEZE_METIN_BASE && r <= PLAYERBOT_WEZE_TIME_METIN) || r == PLAYERBOT_WEZE_COLUMN || r == PLAYERBOT_WEZE_CAGED ||
					r >= 20000)
				continue;
			if (std::find(out.begin(), out.end(), r) == out.end())
				out.push_back(r);
		}
	}

	// The living monsters of the instance for the progress line (race@cell hp%), at most six.
	std::string DescribePlayerBotWezeAdds(long instance)
	{
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(instance, get_dword_time());
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		std::string out;
		int n = 0;
		for (size_t i = 0; i < scan.foes.size() && pMap; ++i)
		{
			const DWORD r = scan.foes[i].dwRace;
			if ((r > PLAYERBOT_WEZE_METIN_BASE && r <= PLAYERBOT_WEZE_TIME_METIN) || r == PLAYERBOT_WEZE_COLUMN || r == PLAYERBOT_WEZE_CAGED)
				continue;
			if (++n > 6)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			char buf[48];
			snprintf(buf, sizeof(buf), "%s%u@(%ld,%ld)%d", out.empty() ? "" : ",", (unsigned int)r,
					(scan.foes[i].lX - pMap->m_setting.iBaseX) / 100, (scan.foes[i].lY - pMap->m_setting.iBaseY) / 100,
					c && c->GetMaxHP() > 0 ? (int)((long long)c->GetHP() * 100 / c->GetMaxHP()) : -1);
			out += buf;
		}
		if (n > 6)
			out += ",+" + std::to_string(n - 6);
		return out.empty() ? "-" : out;
	}

	void GetPlayerBotWezeObjectives(LPDUNGEON d, std::vector<DWORD>& out)
	{
		if (!d || d->GetFlag("started") != 1)
			return;
		switch (d->GetFlag("lvl"))
		{
			case 3:
			{
				const int e = GetPlayerBotWezeOrder(d, d->GetFlag("next"));
				if (IsPlayerBotWezeAddsFirst(d, d->GetMapIndex()))	// MT2009_PLUS_WEZE_ROOM_PURGE_V1: the 4th Metin's turn as the others
					AddPlayerBotWezeAddRaces(d->GetMapIndex(), out);
				else if (e)
					out.push_back(PLAYERBOT_WEZE_METIN_BASE + e);
				break;
			}
			case 4:	// everything of the room dies before the Warrior comes (d.count_monster() == 0)
				AddPlayerBotWezeAddRaces(d->GetMapIndex(), out);
				out.push_back(PLAYERBOT_WEZE_TIME_METIN);
				out.push_back(PLAYERBOT_WEZE_WARRIOR_EARTH);
				out.push_back(PLAYERBOT_WEZE_WARRIOR_ICE);
				break;
			case 7:
				if (d->GetFlag("nethis") == 1)
					out.push_back(PLAYERBOT_WEZE_NETHIS);
				break;
			default:	// 2, 5, 6: the nearest group (the 5th's and 6th's keys drop from them)
				break;
		}
	}

	// The 3rd level: a Metin Wezowy out of the order is no foe for any bot (its fall brings the fallen ones back).
	bool IsPlayerBotWezeNoTarget(LPCHARACTER c)
	{
		if (!c)
			return false;
		const DWORD race = c->GetRaceNum();
		if (race <= PLAYERBOT_WEZE_METIN_BASE || race > PLAYERBOT_WEZE_METIN_BASE + 4 || !IsPlayerBotWezeInstance(c->GetMapIndex()))
			return false;
		LPDUNGEON d = CDungeonManager::instance().FindByMapIndex(c->GetMapIndex());
		if (!d || d->GetFlag("lvl") != 3)
			return false;
		const int e = GetPlayerBotWezeOrder(d, d->GetFlag("next"));
		if (e != 0 && race == PLAYERBOT_WEZE_METIN_BASE + e && c->GetMaxHP() > 0)
			return IsPlayerBotWezeHoldLastMetin(d, c->GetMapIndex(), (int)((long long)c->GetHP() * 100 / c->GetMaxHP()));
		return e != 0 && race != PLAYERBOT_WEZE_METIN_BASE + e;
	}

	bool IsPlayerBotWezeItem(DWORD vnum)
	{
		return vnum >= PLAYERBOT_WEZE_KEY && vnum <= PLAYERBOT_WEZE_ENTRY && vnum != PLAYERBOT_WEZE_TREASURE;
	}

	bool IsPlayerBotWezeNextWanted(LPDUNGEON d)
	{
		if (!d)
			return false;
		return d->GetFlag("started") == 0 || (d->GetFlag("lvl") == 6 && d->GetFlag("smith") == 1);
	}

	// ------------------------------------------------------------ the way in

	long long ChargePlayerBotWezeEntry(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		long long paid = 0;
		// ChargePlayerBotDgRunEntry has counted this entry (swiatynia_wezy.day / .runs, the quest's login's count).
		const int runs = ch->GetQuestFlag("swiatynia_wezy.runs");
		if (runs > PLAYERBOT_WEZE_DAILY)
		{
			// Over the day's five: a Wejscie do Swiatyni Wezy renews them (its quest use: runs 0) - this entry is the first.
			const char* how = "let_go";
			if (ch->CountSpecifyItem(PLAYERBOT_WEZE_ENTRY) > 0)
			{
				ch->RemoveSpecifyItem(PLAYERBOT_WEZE_ENTRY, 1);
				how = "own";
			}
			else
			{
				const long long price = (long long)GetPlayerBotYdgEnv("PLAYERBOT_WEZE_ENTRY_PRICE", (int)PLAYERBOT_WEZE_ENTRY_PRICE, 0,
						2000000000);
				if ((long long)ch->GetGold() >= price)
				{
					if (price > 0)
						PlayerBotChangeGold(ch, -price);
					paid = price;
					how = "bought";
				}
			}
			if (strcmp(how, "let_go"))
				ch->SetQuestFlag("swiatynia_wezy.runs", 1);
			sys_log(0, "BOT_YDG: weze entry renewed pid=%u name=%s runs=%d how=%s price=%lld gold=%lld", ch->GetPlayerID(), ch->GetName(),
					runs, how, paid, (long long)ch->GetGold());
		}
		// The quest's login's own flags for this expedition (the 11th death sends a person out).
		ch->SetQuestFlag("swiatynia_wezy.idx", ch->GetMapIndex());
		ch->SetQuestFlag("swiatynia_wezy.entry", get_global_time());
		ch->SetQuestFlag("swiatynia_wezy.deaths", 0);
		ch->SetQuestFlag("swiatynia_wezy.logout", 0);
		ch->SetQuestFlag("swiatynia_wezy.reward", 0);
		return paid;
	}

	// ------------------------------------------------------------ inside

	// The run's members in the quest's p1..p8 (the surface attack's choice, the reward's list).
	void RegisterPlayerBotWezeMembers(const TPlayerBotDgRun& run, LPDUNGEON d)
	{
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->GetMapIndex() != run.lInstance)
				continue;
			const int pid = (int)c->GetPlayerID();
			int free = 0;
			bool known = false;
			for (int k = 1; k <= 8 && !known; ++k)
			{
				char name[8];
				snprintf(name, sizeof(name), "p%d", k);
				const int p = d->GetFlag(name);
				known = p == pid;
				if (p == 0 && free == 0)
					free = k;
			}
			if (known || free == 0)
				continue;
			char name[8];
			snprintf(name, sizeof(name), "p%d", free);
			d->SetFlag(name, pid);
			sys_log(0, "BOT_YDG: weze registered run=%d instance=%ld slot=%d pid=%u name=%s", run.iId, run.lInstance, free,
					c->GetPlayerID(), c->GetName());
		}
	}

	// Pyl Wezowy: a minute a dust on the Portal's clock, up to its 60 minutes - the members' own, else bought.
	void UsePlayerBotWezeDust(const TPlayerBotDgRun& run, LPDUNGEON d, TPlayerBotWezeInstance& w)
	{
		if (w.bDustDone)
			return;
		const int start = d->GetFlag("start");
		const int before = d->GetFlag("limit_at");
		const int want = (start + PLAYERBOT_WEZE_LIMIT_MAX_S - before) / 60;
		if (want <= 0 || w.iDustFails >= 10)
		{
			w.bDustDone = true;
			sys_log(0, "BOT_YDG: weze dust done run=%d instance=%ld used=%d bought=%d fails=%d minutes=%d", run.iId, run.lInstance,
					w.iDustUsed, w.iDustBought, w.iDustFails, (before - start) / 60);
			return;
		}
		// A member inside and alive with dust; else the richest buys what is missing.
		LPCHARACTER user = NULL, rich = NULL;
		for (size_t i = 0; i < run.members.size() && !user; ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->IsDead() || c->GetMapIndex() != run.lInstance || !c->IsItemLoaded())
				continue;
			if (c->CountSpecifyItem(PLAYERBOT_WEZE_DUST) > 0)
				user = c;
			else if (!rich || c->GetGold() > rich->GetGold())
				rich = c;
		}
		if (!user && rich)
		{
			const long long price = (long long)GetPlayerBotYdgEnv("PLAYERBOT_WEZE_DUST_PRICE", (int)PLAYERBOT_WEZE_DUST_PRICE, 0, 100000000);
			int n = want;
			while (n > 0 && price * n > (long long)rich->GetGold())
				--n;
			if (n > 0 && (rich->GetEmptyInventory(1) >= 0 || HasPlayerBotYdgStackRoom(rich, PLAYERBOT_WEZE_DUST) ||
					MakePlayerBotYdgRoom(rich, "weze_dust")))
			{
				PlayerBotChangeGold(rich, -price * n);
				rich->AutoGiveItem(PLAYERBOT_WEZE_DUST, (ITEM_COUNT)n, -1, false);
				w.iDustBought += n;
				sys_log(0, "BOT_YDG: weze dust bought run=%d pid=%u name=%s count=%d price=%lld gold=%lld", run.iId, rich->GetPlayerID(),
						rich->GetName(), n, price * n, (long long)rich->GetGold());
				if (rich->CountSpecifyItem(PLAYERBOT_WEZE_DUST) > 0)
					user = rich;
			}
			else
				++w.iDustFails;
		}
		if (!user)
			return;	// nobody inside and alive just now, or no gold for it
		const int cell = FindPlayerBotTowerItemCell(user, PLAYERBOT_WEZE_DUST);
		if (cell < 0)
		{
			++w.iDustFails;
			return;
		}
		const bool ok = user->UseItem(TItemPos(INVENTORY, (WORD)cell));
		const int after = d->GetFlag("limit_at");
		if (after > before)
		{
			++w.iDustUsed;
			w.iDustFails = 0;
		}
		else
		{
			++w.iDustFails;
			sys_log(0, "BOT_YDG: weze dust refused run=%d pid=%u name=%s ok=%d limit_at=%d start=%d fails=%d", run.iId,
					user->GetPlayerID(), user->GetName(), ok ? 1 : 0, after, start, w.iDustFails);
		}
	}

	void UpdatePlayerBotWezeInside(TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		if (!IsPlayerBotWezeDungeon(d) || d->GetFlag("init") != 1 || d->GetFlag("closed") == 1)
			return;
		TPlayerBotWezeInstance& w = s_mapPlayerBotWeze[run.lInstance];
		RegisterPlayerBotWezeMembers(run, d);
		if (d->GetFlag("started") == 1)
			UsePlayerBotWezeDust(run, d, w);
		if (w.dwProgressAt != 0 && (int)(dwNow - w.dwProgressAt) < 0)
			return;
		w.dwProgressAt = dwNow + 120000;
		int keys = 0, prison = 0, shards[5] = { 0, 0, 0, 0, 0 }, dust = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->GetMapIndex() != run.lInstance || !c->IsItemLoaded())
				continue;
			keys += (int)c->CountSpecifyItem(PLAYERBOT_WEZE_KEY);
			prison += (int)c->CountSpecifyItem(PLAYERBOT_WEZE_PRISON_KEY);
			dust += (int)c->CountSpecifyItem(PLAYERBOT_WEZE_DUST);
			for (int e = 1; e <= 4; ++e)
				shards[e] += (int)c->CountSpecifyItem(PLAYERBOT_WEZE_SHARD_BASE + e);
		}
		const int left = d->GetFlag("started") == 1 ? d->GetFlag("limit_at") - (int)get_global_time() : -1;
		sys_log(0, "BOT_YDG: weze progress run=%d instance=%ld started=%d lvl=%d left_s=%d order=%d%d%d%d next=%d tm=%d warrior=%d extra=%d "
				"opened=%d freed=%d g6=%d smith=%d turned=%d want_head=%d nethis=%d keys=%d prison_keys=%d shards=%d/%d/%d/%d dust=%d "
				"dust_used=%d adds=%s", run.iId, run.lInstance, d->GetFlag("started"), d->GetFlag("lvl"), left, d->GetFlag("o1"), d->GetFlag("o2"),
				d->GetFlag("o3"), d->GetFlag("o4"), d->GetFlag("next"), d->GetFlag("tm"), d->GetFlag("warrior"), d->GetFlag("extra"),
				d->GetFlag("opened"), d->GetFlag("freed"), d->GetFlag("g6"), d->GetFlag("smith"), d->GetFlag("turned"),
				GetPlayerBotWezeHeadWanted(d), d->GetFlag("nethis"), keys, prison, shards[1], shards[2], shards[3], shards[4], dust,
				w.iDustUsed, DescribePlayerBotWezeAdds(run.lInstance).c_str());
	}

	// ------------------------------------------------------------ the items

	// The NPC of this race nearest to (x, y) within range (the Kolumna of a place), or nearest to the bot (range 0).
	LPCHARACTER FindPlayerBotWezeNpc(LPCHARACTER ch, DWORD race, long x, long y, int range)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex());
		if (!pMap)
			return NULL;
		if (range <= 0)
		{
			FPlayerBotYdgNpc finder(ch, race, NULL);
			pMap->for_each(finder);
			return finder.m_found;
		}
		struct FAt
		{
			DWORD race;
			long map, x, y;
			int best;
			LPCHARACTER found;
			void operator()(LPENTITY ent)
			{
				if (!ent || !ent->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER c = (LPCHARACTER)ent;
				if (c->IsPC() || c->IsDead() || c->GetRaceNum() != race || c->GetMapIndex() != map)
					return;
				const int dd = DISTANCE_APPROX(c->GetX() - x, c->GetY() - y);
				if (dd < best)
				{
					best = dd;
					found = c;
				}
			}
		} f = { race, ch->GetMapIndex(), x, y, range + 1, NULL };
		pMap->for_each(f);
		return f.found;
	}

	// To the NPC and the item handed in (a quest's take); true while the bot is busy with it.
	bool GivePlayerBotWezeItem(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotDgRun& run, LPDUNGEON d, LPCHARACTER npc,
			DWORD vnum, DWORD& next, DWORD dwNow, const char* what)
	{
		const int cell = FindPlayerBotTowerItemCell(ch, vnum);
		if (!npc || cell < 0)
			return false;
		const int dist = DISTANCE_APPROX(npc->GetX() - ch->GetX(), npc->GetY() - ch->GetY());
		if (dist > PLAYERBOT_YDG_GIVE_DISTANCE)
		{
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			next = dwNow + 500;
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBot(ch, npc->GetX(), npc->GetY(), dwNow, 8, true, false);
			return true;
		}
		next = dwNow + PLAYERBOT_YDG_ITEM_RETRY_MS;
		if (ch->IsStateMove())
			ch->Stop();
		const DWORD race = npc->GetRaceNum();
		const long long before = (long long)d->GetFlag("opened") * 1000 + d->GetFlag("freed") * 100 + d->GetFlag("turned") * 10 + d->GetFlag("lvl");
		const bool ok = ch->GiveItem(npc, TItemPos(INVENTORY, (WORD)cell));	// npc may be gone now (purged by its quest)
		const long long after = (long long)d->GetFlag("opened") * 1000 + d->GetFlag("freed") * 100 + d->GetFlag("turned") * 10 + d->GetFlag("lvl");
		sys_log(0, "BOT_YDG: weze handed in run=%d what=%s pid=%u name=%s vnum=%u npc=%u ok=%d right=%d opened=%d freed=%d turned=%d lvl=%d",
				run.iId, what, ch->GetPlayerID(), ch->GetName(), (unsigned int)vnum, (unsigned int)race, ok ? 1 : 0, after != before ? 1 : 0,
				d->GetFlag("opened"), d->GetFlag("freed"), d->GetFlag("turned"), d->GetFlag("lvl"));
		return true;
	}

	// The night of 5/6 November: the 7th level's arrival (move_to: the room's (0,-50) = (127,592)) is cut off from the
	// room in the bots' grid ("PLAYERBOT_NAV: unreachable from=(89500,1697600)", 37 a minute) - the five parties at the
	// 7th level stood there for 10+ minutes with 40-50 groups alive at 100%. A member whose grid part is not the room's
	// (the six spots') steps into the room - a short move inside the instance, as the portals of Glebie do.
	bool UnstrandPlayerBotWeze(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotDgRun& run, int lvl, DWORD dwNow)
	{
		if (lvl < 3 || lvl > 7 || !run.lInstance || ch->GetMapIndex() != run.lInstance)
			return false;
		// MT2009_PLUS_NAJEMNICY_V4: not a player's mercenary - its owner leads it through the rooms (the catch-up beside
		// the owner), and a hop to a group of another room would take it away from the owner's fight.
		if (IsPlayerBotNajemnikPID(ch->GetPlayerID()))
			return false;
		CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(ch->GetMapIndex());
		if (!nav.Init(ch->GetMapIndex()))
			return false;
		const DWORD mine = nav.GetComponentAtWorld(ch->GetX(), ch->GetY(), 2);
		// V2 (02:25): the six spots' parts said nothing ("foe off the ground, waiting ... from=(89500,1697600)" 300 a
		// minute) - the test is the monsters': none of them on the bot's part, the nearest one's part is the room.
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
		long bestX = 0, bestY = 0;
		DWORD bestPart = 0;
		int bestD = INT_MAX;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD r = scan.foes[i].dwRace;
			if (r == PLAYERBOT_WEZE_COLUMN || r == PLAYERBOT_WEZE_CAGED || r >= 20000)
				continue;
			const DWORD part = nav.GetComponentAtWorld(scan.foes[i].lX, scan.foes[i].lY, 3);
			if (!part)
				continue;
			if (part == mine)
				return false;	// something to fight on its own ground
			const int dd = DISTANCE_APPROX(ch->GetX() - scan.foes[i].lX, ch->GetY() - scan.foes[i].lY);
			if (dd < bestD && dd < 12000)
			{
				bestD = dd;
				bestPart = part;
				bestX = scan.foes[i].lX;
				bestY = scan.foes[i].lY;
			}
		}
		if (!bestPart)
			return false;
		PIXEL_POSITION p;
		p.x = bestX;
		p.y = bestY;
		p.z = 0;
		long tx = bestX, ty = bestY;
		if (nav.FindNearestWalkableWorld(bestX, bestY, 6, p) && nav.GetComponentAtWorld(p.x, p.y, 1) == bestPart)
		{
			tx = p.x;
			ty = p.y;
		}
		// a step of the way only (a few cells off the foe), not onto it
		tx += (long)((long long)(ch->GetX() - tx) * 400 / std::max(1, bestD));
		ty += (long)((long long)(ch->GetY() - ty) * 400 / std::max(1, bestD));
		if (nav.GetComponentAtWorld(tx, ty, 1) != bestPart)
		{
			tx = p.x;
			ty = p.y;
		}
		if (ch->IsStateMove())
			ch->Stop();
		ClearPlayerBotRoute(state, true);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Show(ch->GetMapIndex(), tx, ty);
		ch->Stop();
		PlayerBotLogThrottled("weze_unstrand", dwNow, "BOT_YDG: weze unstranded run=%d name=%s lvl=%d part=%u to_part=%u to=(%ld,%ld) dist=%d",
				run.iId, ch->GetName(), lvl, (unsigned int)mine, (unsigned int)bestPart, tx, ty, bestD);
		return true;
	}

	bool ManagePlayerBotWezeItems(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		if (!IsPlayerBotWezeDungeon(d) || d->GetFlag("started") != 1 || d->GetFlag("closed") == 1)
			return false;
		DWORD& next = s_mapPlayerBotYdgItemAt[ch->GetPlayerID()];
		if (next != 0 && (int)(next - dwNow) > 0)
			return false;
		next = dwNow + PLAYERBOT_YDG_ITEM_SCAN_MS;
		const int lvl = d->GetFlag("lvl");
		if (UnstrandPlayerBotWeze(ch, state, run, lvl, dwNow))
			return true;
		// The hand-ins of this level.
		if (lvl == 5 && ch->CountSpecifyItem(PLAYERBOT_WEZE_KEY) > 0)
		{
			// The Kolumna where the 4th level's Metin of this turn stood (m<opened+1>) - the quest's own check.
			char name[8];
			snprintf(name, sizeof(name), "m%d", d->GetFlag("opened") + 1);
			const int six = d->GetFlag(name);
			long x = 0, y = 0;
			if (six >= 1 && six <= 6 && GetPlayerBotWezeSpot(run.lInstance, 5, six, x, y))
			{
				LPCHARACTER col = FindPlayerBotWezeNpc(ch, PLAYERBOT_WEZE_COLUMN, x, y, PLAYERBOT_WEZE_COLUMN_RANGE);
				// MT2009_PLUS_WEZE_ROOM_PURGE_V1: the 6th Kolumna at once - the quest empties room 5 as the party leaves it,
				// so its groups no longer hold the Smith's count_monster (the hold "weze last column held" is gone)
				if (GivePlayerBotWezeItem(ch, state, run, d, col, PLAYERBOT_WEZE_KEY, next, dwNow, "column"))
					return true;
			}
		}
		else if (lvl == 6 && d->GetFlag("smith") == 0 && ch->CountSpecifyItem(PLAYERBOT_WEZE_PRISON_KEY) > 0)
		{
			LPCHARACTER cage = FindPlayerBotWezeNpc(ch, PLAYERBOT_WEZE_CAGED, 0, 0, 0);
			if (GivePlayerBotWezeItem(ch, state, run, d, cage, PLAYERBOT_WEZE_PRISON_KEY, next, dwNow, "cage"))
				return true;
		}
		else if (lvl == 7 && d->GetFlag("nethis") == 0)
		{
			const int e = GetPlayerBotWezeHeadWanted(d);
			if (e && ch->CountSpecifyItem(PLAYERBOT_WEZE_SHARD_BASE + e) > 0)
			{
				LPCHARACTER head = FindPlayerBotWezeNpc(ch, PLAYERBOT_WEZE_HEADS[e], 0, 0, 0);
				if (GivePlayerBotWezeItem(ch, state, run, d, head, PLAYERBOT_WEZE_SHARD_BASE + e, next, dwNow, "head"))
					return true;
			}
		}
		// One lying about: the level's keys / shards, and the dust anywhere.
		FPlayerBotYdgGround ground(ch);
		ground.m_vnums.push_back(PLAYERBOT_WEZE_DUST);
		if (lvl == 5)
		{
			ground.m_vnums.push_back(PLAYERBOT_WEZE_KEY);
			ground.m_vnums.push_back(PLAYERBOT_WEZE_PRISON_KEY);
		}
		else if (lvl == 6 && d->GetFlag("smith") == 0)
			ground.m_vnums.push_back(PLAYERBOT_WEZE_PRISON_KEY);
		else if (lvl == 7 && d->GetFlag("nethis") == 0)
			for (int e = 1; e <= 4; ++e)
				ground.m_vnums.push_back(PLAYERBOT_WEZE_SHARD_BASE + e);
		ch->GetSectree()->ForEachAround(ground);
		if (!ground.m_found)
			return false;
		// Not far away from what attacks it (one close by all the same - the groups never stop coming).
		if (ground.m_iBest > 800 && ch->GetVictim() && !ch->GetVictim()->IsDead() && ch->GetVictim()->GetVictim() == ch)
			return false;
		LPITEM item = ground.m_found;
		if (ch->GetEmptyInventory(1) < 0 && !HasPlayerBotYdgStackRoom(ch, item->GetVnum()) && !MakePlayerBotYdgRoom(ch, "weze_ground"))
		{
			PlayerBotLogThrottled("weze_no_room", dwNow, "BOT_YDG: weze no room run=%d pid=%u name=%s vnum=%u", run.iId,
					ch->GetPlayerID(), ch->GetName(), (unsigned int)item->GetVnum());
			return false;
		}
		if (ground.m_iBest > PLAYERBOT_YDG_PICKUP_DISTANCE)
		{
			next = dwNow + 400;
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBot(ch, item->GetX(), item->GetY(), dwNow, 2, true, false);
			return true;
		}
		const DWORD vnum = item->GetVnum();
		if (ch->IsStateMove())
			ch->Stop();
		const bool ok = ch->PickupItem(item->GetVID());
		sys_log(0, "BOT_YDG: weze picked up run=%d pid=%u name=%s vnum=%u lvl=%d ok=%d", run.iId, ch->GetPlayerID(), ch->GetName(),
				(unsigned int)vnum, lvl, ok ? 1 : 0);
		return true;
	}

	// ------------------------------------------------------------ the end

	// The statue's reward for a member inside at Nethis's fall (the quest's reward flag), the temple's keys and
	// shards out of the bag (a person's stay with him, worth nothing outside; the bots' are the run's).
	void FinishPlayerBotWezeMember(LPCHARACTER ch, int runId)
	{
		if (!ch || !ch->IsItemLoaded())
			return;
		for (DWORD v = PLAYERBOT_WEZE_KEY; v <= PLAYERBOT_WEZE_PRISON_KEY; ++v)
		{
			const int n = (int)ch->CountSpecifyItem(v);
			if (n > 0)
				ch->RemoveSpecifyItem(v, (ITEM_COUNT)n);
		}
		ch->SetQuestFlag("swiatynia_wezy.idx", 0);
		if (ch->GetQuestFlag("swiatynia_wezy.reward") != 1)
			return;
		ch->SetQuestFlag("swiatynia_wezy.reward", 0);
		int given = 0;
		for (int i = 0; i < PLAYERBOT_WEZE_TREASURES; ++i)
		{
			if (ch->GetEmptyInventory(1) < 0 && !HasPlayerBotYdgStackRoom(ch, PLAYERBOT_WEZE_TREASURE))
				MakePlayerBotYdgRoom(ch, "weze_reward");
			given += ch->AutoGiveItem(PLAYERBOT_WEZE_TREASURE, 1, -1, false) ? 1 : 0;
		}
		const DWORD armour = PLAYERBOT_WEZE_ARMOUR[ch->GetJob() % 4];
		if (ch->GetEmptyInventory(1) < 0)
			MakePlayerBotYdgRoom(ch, "weze_reward");
		const bool armourOk = ch->AutoGiveItem(armour, 1, -1, false) != NULL;
		sys_log(0, "BOT_YDG: weze reward pid=%u name=%s treasures=%d armour=%u ok=%d", ch->GetPlayerID(), ch->GetName(), given,
				(unsigned int)armour, armourOk ? 1 : 0);
		(void)runId;
	}

	void ForgetPlayerBotWeze(long instance)
	{
		s_mapPlayerBotWeze.erase(instance);
	}
}

#endif
