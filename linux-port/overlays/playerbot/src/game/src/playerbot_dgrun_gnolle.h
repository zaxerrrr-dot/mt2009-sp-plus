#ifndef __INC_METIN2_PLAYERBOT_DGRUN_GNOLLE_H__
#define __INC_METIN2_PLAYERBOT_DGRUN_GNOLLE_H__

// MT2009_PLUS_BOT_GNOLLE_V1 - Jaskinie Gnolli 1-3 (382-384, jaskinie_gnolli.quest) as a bots' run.
//
// The owner, night of 5/6 November 2026: "Teach the bots to go to ... Jaskinie Gnolli 1-3. Prepare 10 groups per
// dungeon ... You have my full permission to change the bots so they can do these dungeons." The dungeon is never
// made weaker: no monster, boss, spawn or quest change - the bots only play it as players do.
//
// The caves (jaskinie_gnolli.quest, yohara_dung4/README.md): three open maps (no instance), each the official maze of
// GOTO portals (10901-10924, 10931-10954, 10961-10984 - the NPC's name is its landing cell, as in the Monkey Dungeon);
// Halabardnik (20836) in Dongan (373) lets in from level 120 and the first Champion level, for one Przepustka (71095,
// or the tradable 71130) each, onto level 1 at (213,110); Odcinek 2 (20838, level 1, cell 600,560) and Odcinek 3
// (20839, level 2) lead one level down with no way back, Dongan (20840, level 3) and Wyjscie (20837) back to Dongan;
// whoever dies is sent to Dongan as it stands up (the quest's die/timer); the bosses stand in their rooms - level 1
// Mistrz Gnolli 6804 / Gnoll Kapitan 6805 every hour, level 2 the Ahtrin Kapitans 6814/6815 every 2 hours, level 3
// Mistrz Ahtrin 6819 / Ahtrin Wielki Mistrz 6820 every 3 hours (boss.txt) - shared with every player on the map.
//
// A run (the row "gnolle" of PLAYERBOT_DGRUN_DEFS, kind DGRUN_KIND_GNOLLE; the clock's 120-135 band with the first
// Champion level, two at once, and the YDG training file's "gnolle" parties):
//   - the gathering by Halabardnik (the dungeon panel's entrance, map 373); the way in is the guard's: each member of
//     120+ with a Champion level pays a Przepustka (its own, else one bought on the market for
//     PLAYERBOT_GNOLLE_TICKET_PRICE; a poorer one is let go, logged) and is warped to level 1 (213,110); a member
//     short of the levels is turned away (not_fit), as the quest does;
//   - on a level the leader goes for the level's boss when one stands (through the maze: a route of GOTO portals by
//     the doors' components, FindPlayerBotGnolleDoorStep), else hunts the rooms nearest by portals for
//     PLAYERBOT_GNOLLE_HUNT_S, then walks to the level's way down (Odcinek 2 / Odcinek 3; on level 3 the exit to
//     Dongan) and the party goes down together (each member's warp the NPC's dialog would make);
//   - a member that dies is out of the caves (the quest sends it to Dongan); on level 1 it comes back in with
//     another Przepustka (up to PLAYERBOT_GNOLLE_REENTRIES times), from level 2 on it is out of the run;
//   - the others fight round the leader (what attacks them or the leader, the leader's focus - a boss - and the
//     nearest in the same room), a member left in another room is put beside the leader (the party pass's catch-up);
//     no monster is ever moved and no boss's health is held (the caves are everybody's);
//   - won: the party went out by level 3's exit (the three levels passed). The bosses killed are counted.
// The YDG run bonuses (BuffPlayerBotYdgMember), the bag room and the gains' log of BOT_YDG are the training's.
// The caves are Sung Ma maps (champion/sungma_table.txt: 25/15/20/25, 55/35/45/45, 75/60/65/65, Precyzja 20): a bot
// short of them fights as a player short of them does - nothing here lowers them; the travel's Sung Ma gate lets a run's
// member in (IsPlayerBotSungmaEntryAllowed -> IsPlayerBotDungeonRunMove: the run's level is run.lInstance).
//
// The log: BOT_GNOLLE lines (in, door, boss up/down, level, progress every 2 min, died out / back in, run end) and
// the file playerbot_gnolle_runs.tsv (one row a run); BOT_DGRUN / BOT_YDG lines as every run.
//
// MT2009_PLUS_BOT_GNOLLE_V2 - the day of 6 November (the night: 71 runs, 1 won; parties wandering level 1 for 20 minutes,
// dying out on levels 2 and 3, ten parties after the same shared bosses). The owner: "mniej druzyn, i wyzsze lvl na 2 i 3
// poziom". Nothing of the caves changes - only the bots:
//   - the queue (IsPlayerBotGnolleOpenOk, every caller - the clock, the Dropki, the training): at most "gnolle max"
//     (default 3) parties in the caves, and a new one only while a level-1 boss stands that no party on level 1 has yet
//     ("gnolle bosses 1"; the bosses' board scanned from the maps every 5 s, its changes logged) - a party does not go
//     in to find the bosses dead; on a level the leader leaves a boss another party is on (a claim) and walks on;
//   - the route: the shortest chain of portals of each level (worked out of the maps' server_attr and the portals' landing
//     cells - the three levels are one layout, 11 rooms, both bosses of a level on the way: the first by the last portal,
//     the second in the way down's room), PLAYERBOT_GNOLLE_ROUTE; the leader takes the route's portal of the room it stands
//     in (the maze's search when it stands off the route), fights what attacks, a boss of its own room and what stands
//     close in its room (up to PLAYERBOT_GNOLLE_CLEAR_MS a room) - the old hunt of the rooms nearest by portals is off
//     (PLAYERBOT_GNOLLE_HUNT_S, default now 0);
//   - the strength to go down (GatePlayerBotGnolleWayDown, "gnolle l2" / "gnolle l3"): a member short of it (Champion
//     level, gear level and plus, the run's max health) goes out to Dongan instead of dying below; the party goes on with
//     enough members, a healer and the gear's average, else it leaves the caves (aborted) - no more suicides on level 2;
//   - the run's bonuses (BuffPlayerBotYdgMember, the Sung Ma Will) again for a member back in after a death (a death
//     clears the affects - the night's re-entered members fought levels 2/3 with half their health) and at every level;
//   - the retreat: a member under "gnolle retreat" (45%) of its health drinks, and with the potion not enough steps back
//     hidden to the pack (the run's break-off) before the 30% the other runs use.
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h (after the YDG one), in its anonymous
// namespace.

namespace
{
	const long PLAYERBOT_GNOLLE_MAP_FIRST = 382;	// level 1; 383 level 2, 384 level 3
	const long PLAYERBOT_GNOLLE_DONGAN = 373;
	// jaskinie_gnolli.quest cfg().dongan (by Halabardnik), world units / 100
	const long PLAYERBOT_GNOLLE_DONGAN_X = 11476, PLAYERBOT_GNOLLE_DONGAN_Y = 5327;
	const long PLAYERBOT_GNOLLE_ENTRY_CX = 213, PLAYERBOT_GNOLLE_ENTRY_CY = 110;	// every level's way in (cells)
	const long PLAYERBOT_GNOLLE_WAY_CX = 600, PLAYERBOT_GNOLLE_WAY_CY = 560;	// 20838 / 20839 / 20840 (npc.txt)
	const DWORD PLAYERBOT_GNOLLE_WAY_NPC[3] = { 20838, 20839, 20840 };
	const DWORD PLAYERBOT_GNOLLE_BOSSES[3][2] = { { 6804, 6805 }, { 6814, 6815 }, { 6819, 6820 } };
	const DWORD PLAYERBOT_GNOLLE_TICKETS[2] = { 71095, 71130 };	// Przepustka, Przepustka (zdatna do handlu)
	const int PLAYERBOT_GNOLLE_MIN_LEVEL = 120;
	const int PLAYERBOT_GNOLLE_MIN_CHAMPION = 1;
	const long long PLAYERBOT_GNOLLE_TICKET_PRICE = 4540000LL;	// playerbot_price_tables.h: 71130
	const int PLAYERBOT_GNOLLE_REENTRIES = 2;
	const int PLAYERBOT_GNOLLE_MAX_DOORS = 40;
	const int PLAYERBOT_GNOLLE_DOOR_USE = 250;		// within this of a portal: through it
	const int PLAYERBOT_GNOLLE_WAY_REACH = 600;		// the leader by the way down
	const int PLAYERBOT_GNOLLE_WAY_GATHER = 2500;		// the others by it before the party goes down
	const DWORD PLAYERBOT_GNOLLE_WAY_WAIT_MS = 20000;	// at most this long for them
	const int PLAYERBOT_GNOLLE_FIGHT_RANGE = 2500;		// a foe of the leader's own room fought straight away
	const int PLAYERBOT_GNOLLE_FOLLOW_RANGE = 2000;		// a follower's foes round the leader
	const DWORD PLAYERBOT_GNOLLE_HUNT_PICK_MS = 2000;
	const DWORD PLAYERBOT_GNOLLE_BEHIND_MS = 15000;	// a member alive on another level that long: out
	const DWORD PLAYERBOT_GNOLLE_PROGRESS_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_GNOLLE_PULL_GRACE_MS = 60000;
	const DWORD PLAYERBOT_GNOLLE_MAZE_RETRY_MS = 5000;
	const char* const PLAYERBOT_GNOLLE_RUNS_FILE = "playerbot_gnolle_runs.tsv";
	// MT2009_PLUS_BOT_GNOLLE_V2
	const int PLAYERBOT_GNOLLE_CLEAR_RANGE = 1500;		// a foe this close in the leader's room: fought on the way
	const DWORD PLAYERBOT_GNOLLE_CLEAR_MS = 90000;		// at most this long a room (the regen never ends)
	const DWORD PLAYERBOT_GNOLLE_BOARD_MS = 5000;		// the bosses' board
	const DWORD PLAYERBOT_GNOLLE_CLAIM_MS = 20000;		// a boss a party's leader went for: its, this long after
	const DWORD PLAYERBOT_GNOLLE_BOSS_STALE_MS = 75 * 60 * 1000;	// no level-1 boss seen this long: the queue lets one in
	const int PLAYERBOT_GNOLLE_ROUTE_REACH = 300;		// a route cell matches the portal standing this near it
	// The route of each level: its portals' cells in turn (from the way in at 213,110 to the way down's room). The maps'
	// server_attr flooded into rooms (11 a level) joined by the portals' landing cells (mob_proto names), the shortest
	// chain: level 1 10901 10903 10913 10922 10916 10924; level 2 10931 10932 10934 10940 10946 10950 10949 10954;
	// level 3 10961 10962 10964 10969 10975 10979 10983 10984. Mistrz (6804/6814/6819) stands by the last portal,
	// Kapitan / Wielki Mistrz (6805/6815/6820) in the way down's room.
	const long PLAYERBOT_GNOLLE_ROUTE[3][9][2] = {
		{ { 320, 238 }, { 210, 495 }, { 528, 415 }, { 553, 291 }, { 82, 746 }, { 597, 331 }, { 0, 0 } },
		{ { 320, 238 }, { 350, 361 }, { 421, 272 }, { 65, 434 }, { 82, 746 }, { 541, 40 }, { 278, 705 }, { 597, 331 }, { 0, 0 } },
		{ { 320, 238 }, { 350, 361 }, { 421, 272 }, { 70, 368 }, { 101, 547 }, { 278, 705 }, { 626, 296 }, { 597, 331 }, { 0, 0 } },
	};

	int GetPlayerBotGnolleLevel(long map)
	{
		return map >= PLAYERBOT_GNOLLE_MAP_FIRST && map <= PLAYERBOT_GNOLLE_MAP_FIRST + 2 ? (int)(map - PLAYERBOT_GNOLLE_MAP_FIRST) + 1 : 0;
	}

	// The quest's 120 and the first Champion level; a bot onto a Sung Ma map besides (IsPlayerBotSungmaEntryAllowed) needs the
	// world's top level, the same 120 here.
	bool IsPlayerBotGnolleFit(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() >= std::max(PLAYERBOT_GNOLLE_MIN_LEVEL, (int)gPlayerMaxLevel) &&
				ch->GetConquerorLevel() >= PLAYERBOT_GNOLLE_MIN_CHAMPION;
	}

	bool IsPlayerBotGnolleDef(int def)
	{
		return def >= 0 && def < PLAYERBOT_DGRUN_DEF_COUNT && PLAYERBOT_DGRUN_DEFS[def].bKind == DGRUN_KIND_GNOLLE;
	}

	int FindPlayerBotGnolleDgRunDef()
	{
		for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
			if (PLAYERBOT_DGRUN_DEFS[i].bKind == DGRUN_KIND_GNOLLE)
				return i;
		return -1;
	}

	bool PlayerBotGnolleCell(long map, long cx, long cy, long& x, long& y)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(map);
		if (!pMap)
			return false;
		x = pMap->m_setting.iBaseX + cx * 100;
		y = pMap->m_setting.iBaseY + cy * 100;
		return true;
	}

	// ------------------------------------------------------------ the maze

	struct TPlayerBotGnolleDoor
	{
		long lFromX, lFromY, lToX, lToY;
		DWORD dwFrom, dwTo;	// the navigation's components of its two ends
		DWORD dwVnum;
	};

	struct TPlayerBotGnolleMaze
	{
		bool bReady;
		DWORD dwNextTry;
		std::vector<TPlayerBotGnolleDoor> doors;
		TPlayerBotGnolleMaze() : bReady(false), dwNextTry(0) {}
	};
	std::map<long, TPlayerBotGnolleMaze> s_mapPlayerBotGnolleMaze;

	struct FPlayerBotGnolleDoors
	{
		std::vector<TPlayerBotGnolleDoor>* out;
		long lBaseX, lBaseY;
		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER npc = (LPCHARACTER)ent;
			if (!npc->IsGoto() || out->size() >= (size_t)PLAYERBOT_GNOLLE_MAX_DOORS)
				return;
			char tmp[64];
			long tx = 0, ty = 0;
			// CHARACTER's FuncCheckWarp reads the landing cell out of the NPC's name (". 333 358"); so does this.
			if (3 != sscanf(npc->GetName(), " %63s %ld %ld ", tmp, &tx, &ty))
				return;
			for (size_t i = 0; i < out->size(); ++i)
				if ((*out)[i].lFromX == npc->GetX() && (*out)[i].lFromY == npc->GetY())
					return;
			TPlayerBotGnolleDoor d;
			d.lFromX = npc->GetX();
			d.lFromY = npc->GetY();
			d.lToX = lBaseX + tx * 100;
			d.lToY = lBaseY + ty * 100;
			d.dwFrom = d.dwTo = 0;
			d.dwVnum = npc->GetRaceNum();
			out->push_back(d);
		}
	};

	// The level's portals and the rooms (navigation components) they join - read once the NPCs stand.
	const TPlayerBotGnolleMaze* GetPlayerBotGnolleMaze(long map, DWORD dwNow)
	{
		if (GetPlayerBotGnolleLevel(map) == 0)
			return NULL;
		TPlayerBotGnolleMaze& m = s_mapPlayerBotGnolleMaze[map];
		if (m.bReady)
			return &m;
		if (m.dwNextTry != 0 && (int)(dwNow - m.dwNextTry) < 0)
			return NULL;
		m.dwNextTry = dwNow + PLAYERBOT_GNOLLE_MAZE_RETRY_MS;
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(map);
		if (!pMap)
			return NULL;
		CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(map);
		if (!nav.Init(map))
			return NULL;
		m.doors.clear();
		FPlayerBotGnolleDoors f;
		f.out = &m.doors;
		f.lBaseX = pMap->m_setting.iBaseX;
		f.lBaseY = pMap->m_setting.iBaseY;
		pMap->for_each(f);
		if (m.doors.empty())
		{
			PlayerBotErrThrottled("gnolle_no_doors", dwNow, "BOT_GNOLLE: no portals found map=%ld", map);
			return NULL;
		}
		int joined = 0;
		std::set<DWORD> rooms;
		for (size_t i = 0; i < m.doors.size(); ++i)
		{
			TPlayerBotGnolleDoor& d = m.doors[i];
			d.dwFrom = nav.GetComponentAtWorld(d.lFromX, d.lFromY, 12);
			d.dwTo = nav.GetComponentAtWorld(d.lToX, d.lToY, 12);
			if (d.dwFrom && d.dwTo && d.dwFrom != d.dwTo)
				++joined;
			if (d.dwFrom)
				rooms.insert(d.dwFrom);
			if (d.dwTo)
				rooms.insert(d.dwTo);
		}
		m.bReady = true;
		sys_log(0, "BOT_GNOLLE: maze map=%ld portals=%u joining=%d rooms=%u", map, (unsigned int)m.doors.size(), joined,
				(unsigned int)rooms.size());
		return &m;
	}

	struct TPlayerBotGnolleHop
	{
		int hops;
		int door;	// the first portal on the way there (-1: here)
	};

	// Every room the portals reach from `start`, with the hops and the first portal.
	void MapPlayerBotGnolleRooms(const TPlayerBotGnolleMaze& m, DWORD start, std::map<DWORD, TPlayerBotGnolleHop>& out)
	{
		out.clear();
		if (start == 0)
			return;
		TPlayerBotGnolleHop h0 = { 0, -1 };
		out[start] = h0;
		std::queue<DWORD> open;
		open.push(start);
		while (!open.empty())
		{
			const DWORD cur = open.front();
			open.pop();
			const TPlayerBotGnolleHop hc = out[cur];
			for (size_t i = 0; i < m.doors.size(); ++i)
			{
				const TPlayerBotGnolleDoor& d = m.doors[i];
				if (d.dwFrom != cur || d.dwTo == 0 || out.count(d.dwTo))
					continue;
				TPlayerBotGnolleHop h = { hc.hops + 1, hc.door < 0 ? (int)i : hc.door };
				out[d.dwTo] = h;
				open.push(d.dwTo);
			}
		}
	}

	DWORD GetPlayerBotGnolleRoom(long map, long x, long y)
	{
		CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(map);
		if (!nav.Init(map))
			return 0;
		return nav.GetComponentAtWorld(x, y, 6);
	}

	// ------------------------------------------------------------ the run's own record

	struct TPlayerBotGnolleRun
	{
		int iLevel;
		DWORD dwLevelSince, dwWaySince, dwNextProgress, dwPullSince;
		int iDoors, iBossKills, iReentries, iDiedOut;
		std::string bosses;			// "L1:6804,L3:6820"
		std::map<DWORD, DWORD> bossFought;	// boss vid -> race (the leader's focus once)
		std::map<DWORD, int> reentries;		// pid -> times back in
		std::map<DWORD, DWORD> behindSince;	// pid -> alive on another level since
		std::set<DWORD> inCaves;		// went in
		DWORD dwHuntVid, dwHuntAt;
		bool bExit;
		// MT2009_PLUS_BOT_GNOLLE_V2: the room the leader stands in (since), the route's portal it goes for, retreats
		DWORD dwRoom, dwRoomSince;
		int iRouteDoor, iRetreats, iNotStrong;
		TPlayerBotGnolleRun() : iLevel(1), dwLevelSince(0), dwWaySince(0), dwNextProgress(0), dwPullSince(0), iDoors(0),
				iBossKills(0), iReentries(0), iDiedOut(0), dwHuntVid(0), dwHuntAt(0), bExit(false), dwRoom(0), dwRoomSince(0),
				iRouteDoor(-1), iRetreats(0), iNotStrong(0) {}
	};
	std::map<int, TPlayerBotGnolleRun> s_mapPlayerBotGnolleRuns;

	DWORD GetPlayerBotGnolleHuntMs()
	{
		// MT2009_PLUS_BOT_GNOLLE_V2: off by default - the route (the night's hunt took the parties all over level 1)
		return (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_GNOLLE_HUNT_S", 0, 0, 3600) * 1000U;
	}

	DWORD GetPlayerBotGnolleLevelMaxMs()
	{
		return (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_GNOLLE_LEVEL_MAX_S", 1200, 300, 7200) * 1000U;
	}

	bool IsPlayerBotGnolleBoss(int level, DWORD race)
	{
		return level >= 1 && level <= 3 && (race == PLAYERBOT_GNOLLE_BOSSES[level - 1][0] || race == PLAYERBOT_GNOLLE_BOSSES[level - 1][1]);
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_GNOLLE_V2: the queue, the strength

	// The bosses standing on each level (-1: the level is not on this core), scanned every PLAYERBOT_GNOLLE_BOARD_MS.
	struct TPlayerBotGnolleBoard
	{
		DWORD dwAt;
		int up[3];
		DWORD dwLastUp[3];	// a boss of the level seen standing (or the board's first look)
		TPlayerBotGnolleBoard() : dwAt(0)
		{
			for (int i = 0; i < 3; ++i)
			{
				up[i] = -1;
				dwLastUp[i] = 0;
			}
		}
	};
	TPlayerBotGnolleBoard s_kPlayerBotGnolleBoard;

	const TPlayerBotGnolleBoard& ReadPlayerBotGnolleBoard(DWORD dwNow)
	{
		TPlayerBotGnolleBoard& b = s_kPlayerBotGnolleBoard;
		if (b.dwAt != 0 && dwNow - b.dwAt < PLAYERBOT_GNOLLE_BOARD_MS)
			return b;
		b.dwAt = dwNow;
		for (int l = 0; l < 3; ++l)
		{
			const long map = PLAYERBOT_GNOLLE_MAP_FIRST + l;
			int up = -1;
			if (IsPlayerBotMapHostedHere(map) && SECTREE_MANAGER::instance().GetMap(map))
			{
				up = 0;
				const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
				for (size_t i = 0; i < scan.foes.size(); ++i)
					if (scan.foes[i].dwRace == PLAYERBOT_GNOLLE_BOSSES[l][0] || scan.foes[i].dwRace == PLAYERBOT_GNOLLE_BOSSES[l][1])
					{
						LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
						up += c && !c->IsDead() ? 1 : 0;
					}
			}
			if (up > 0 || (up == 0 && b.dwLastUp[l] == 0))
				b.dwLastUp[l] = dwNow;
			if (up != b.up[l])
				sys_log(0, "BOT_GNOLLE: bosses level=%d up=%d (was %d)", l + 1, up, b.up[l]);
			b.up[l] = up;
		}
		return b;
	}

	// The caves' queue for a new party (every caller - OpenPlayerBotDgRun, the training's choice): "gnolle max" parties
	// at once, and a level-1 boss standing for each party on level 1 (or about to go in) - "gnolle bosses".
	bool IsPlayerBotGnolleOpenOk(DWORD dwNow, const char* why)
	{
		const TPlayerBotGnolleCfg& cfg = s_kPlayerBotGnolleCfg;
		int running = 0, onFirst = 0;
		for (std::map<int, TPlayerBotDgRun>::const_iterator it = s_mapPlayerBotDgRuns.begin(); it != s_mapPlayerBotDgRuns.end(); ++it)
		{
			if (it->second.iDef < 0 || it->second.iDef >= PLAYERBOT_DGRUN_DEF_COUNT ||
					PLAYERBOT_DGRUN_DEFS[it->second.iDef].bKind != DGRUN_KIND_GNOLLE)
				continue;
			++running;
			std::map<int, TPlayerBotGnolleRun>::const_iterator g = s_mapPlayerBotGnolleRuns.find(it->first);
			if (g == s_mapPlayerBotGnolleRuns.end() || (g->second.iLevel <= 1 && !g->second.bExit))
				++onFirst;
		}
		if (running >= cfg.iMax)
		{
			PlayerBotLogThrottled("gnolle_queue_full", dwNow, "BOT_GNOLLE: queue - %d parties in (max %d), no new one (%s)", running,
					cfg.iMax, why ? why : "-");
			return false;
		}
		if (!cfg.bBosses)
			return true;
		const TPlayerBotGnolleBoard& b = ReadPlayerBotGnolleBoard(dwNow);
		if (b.up[0] < 0 || b.up[0] > onFirst)
			return true;
		if (onFirst == 0 && b.dwLastUp[0] != 0 && dwNow - b.dwLastUp[0] >= PLAYERBOT_GNOLLE_BOSS_STALE_MS)
		{
			PlayerBotLogThrottled("gnolle_queue_stale", dwNow, "BOT_GNOLLE: queue - no level-1 boss seen for %u min, one party in (%s)",
					(dwNow - b.dwLastUp[0]) / 60000, why ? why : "-");
			return true;
		}
		PlayerBotLogThrottled("gnolle_queue_bosses", dwNow, "BOT_GNOLLE: queue - waits for a level-1 boss up=%d on_level1=%d running=%d "
				"(level 2 up=%d, level 3 up=%d) (%s)", b.up[0], onFirst, running, b.up[1], b.up[2], why ? why : "-");
		return false;
	}

	// The strength for level 2 (gate 0) or 3 (gate 1): the Champion level, the gear's level and plus
	// (GetPlayerBotYdgGearLevel: the weapon, armour and helmet) and - in the run, with its bonuses - the max health.
	const char* GetPlayerBotGnolleWeakness(LPCHARACTER ch, int gate, bool withHp)
	{
		if (!ch || gate < 0 || gate > 1)
			return "none";
		const TPlayerBotGnolleGate& g = s_kPlayerBotGnolleCfg.gate[gate];
		int plus = 0;
		const int gear = GetPlayerBotYdgGearLevel(ch, &plus);
		if (ch->GetConquerorLevel() < g.champion)
			return "champion";
		if (gear < g.gear)
			return "gear";
		if (plus < g.plus)
			return "plus";
		if (withHp && ch->GetMaxHP() < g.hp)
			return "hp";
		return NULL;
	}

	bool IsPlayerBotGnolleStrong(LPCHARACTER ch, int gate, bool withHp)
	{
		return GetPlayerBotGnolleWeakness(ch, gate, withHp) == NULL;
	}

	// The boss a party's leader went for: its for PLAYERBOT_GNOLLE_CLAIM_MS (refreshed while it fights it).
	std::map<DWORD, std::pair<int, DWORD> > s_mapPlayerBotGnolleClaims;

	bool IsPlayerBotGnolleBossTaken(DWORD vid, int runId, DWORD dwNow)
	{
		std::map<DWORD, std::pair<int, DWORD> >::iterator it = s_mapPlayerBotGnolleClaims.find(vid);
		if (it == s_mapPlayerBotGnolleClaims.end() || it->second.first == runId)
			return false;
		if (dwNow - it->second.second >= PLAYERBOT_GNOLLE_CLAIM_MS || !s_mapPlayerBotDgRuns.count(it->second.first))
		{
			s_mapPlayerBotGnolleClaims.erase(it);
			return false;
		}
		return true;
	}

	// The run's bonuses again (a death took them; a new level's hour).
	void RebuffPlayerBotGnolleMember(LPCHARACTER ch, const TPlayerBotDgRun& run, const char* why)
	{
		if (!ch)
			return;
		BuffPlayerBotYdgMember(ch);
		const std::string sm = BuffPlayerBotYdgSungma(ch, PLAYERBOT_DGRUN_DEFS[run.iDef].lMap);
		sys_log(0, "BOT_GNOLLE: bonuses again pid=%u name=%s run=%d why=%s sungma=%s max_hp=%d", ch->GetPlayerID(), ch->GetName(),
				run.iId, why, sm.empty() ? "-" : sm.c_str(), ch->GetMaxHP());
	}

	// ------------------------------------------------------------ the ticket

	// Halabardnik's price: a Przepustka. The bot's own, else bought from a player on the market.
	long long ChargePlayerBotGnolleTicket(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		for (int i = 0; i < 2; ++i)
			if (ch->CountSpecifyItem(PLAYERBOT_GNOLLE_TICKETS[i]) > 0)
			{
				ch->RemoveSpecifyItem(PLAYERBOT_GNOLLE_TICKETS[i], 1);
				sys_log(0, "BOT_GNOLLE: ticket pid=%u name=%s pass=own vnum=%u", ch->GetPlayerID(), ch->GetName(),
						(unsigned int)PLAYERBOT_GNOLLE_TICKETS[i]);
				return 0;
			}
		const long long price = (long long)ReadPlayerBotYoharaEnvInt("PLAYERBOT_GNOLLE_TICKET_PRICE", (int)PLAYERBOT_GNOLLE_TICKET_PRICE, 0,
				2000000000);
		if (price > 0 && (long long)ch->GetGold() >= price)
		{
			PlayerBotChangeGold(ch, -price);
			sys_log(0, "BOT_GNOLLE: ticket pid=%u name=%s pass=bought price=%lld gold=%lld", ch->GetPlayerID(), ch->GetName(), price,
					(long long)ch->GetGold());
			return price;
		}
		sys_log(0, "BOT_GNOLLE: ticket pid=%u name=%s pass=let_go gold=%lld", ch->GetPlayerID(), ch->GetName(), (long long)ch->GetGold());
		return 0;
	}

	// ------------------------------------------------------------ the way in, the way down

	// A member onto a level's way in (the quest's pc.warp; a bot's WarpSet is WarpBot). The way out: Dongan.
	bool PutPlayerBotGnolleOnLevel(LPCHARACTER ch, int level, size_t idx)
	{
		const long map = PLAYERBOT_GNOLLE_MAP_FIRST + level - 1;
		long x = 0, y = 0;
		if (!PlayerBotGnolleCell(map, PLAYERBOT_GNOLLE_ENTRY_CX, PLAYERBOT_GNOLLE_ENTRY_CY, x, y))
			return false;
		x += (long)(idx % 3) * 150 - 150;
		y += (long)((idx / 3) % 3) * 150 - 75;
		ch->SetWarpLocation(PLAYERBOT_GNOLLE_DONGAN, PLAYERBOT_GNOLLE_DONGAN_X, PLAYERBOT_GNOLLE_DONGAN_Y);
		TPlayerBotAIState* state = GetPlayerBotDgRunState(ch->GetPlayerID());
		if (state)
		{
			state->dwTargetVID = 0;
			ClearPlayerBotRoute(*state, true);
		}
		ch->SetVictim(NULL);
		s_szPlayerBotTransitionRefusal = NULL;
		const bool ok = ch->WarpSet(x, y) && ch->GetMapIndex() == map;
		if (!ok)
			sys_log(0, "BOT_GNOLLE: warp refused pid=%u name=%s level=%d refused=%s", ch->GetPlayerID(), ch->GetName(), level,
					s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "?");
		s_szPlayerBotTransitionRefusal = NULL;
		return ok;
	}

	// The gathered party past Halabardnik: those of the levels, a Przepustka each, onto level 1.
	bool StartPlayerBotGnolleRun(TPlayerBotDgRun& run, DWORD dwNow)
	{
		const long map = PLAYERBOT_GNOLLE_MAP_FIRST;
		if (!SECTREE_MANAGER::instance().GetMap(map))
			return false;
		TPlayerBotGnolleRun& gr = s_mapPlayerBotGnolleRuns[run.iId];
		gr = TPlayerBotGnolleRun();
		gr.iLevel = 1;
		gr.dwLevelSince = gr.dwNextProgress = dwNow;
		run.lInstance = map;	// before the warps: the run's moves are let through to its level
		PlayerBotGnolleCell(map, PLAYERBOT_GNOLLE_ENTRY_CX, PLAYERBOT_GNOLLE_ENTRY_CY, run.lCampX, run.lCampY);
		const std::vector<DWORD> members = run.members;
		size_t in = 0;
		for (size_t i = 0; i < members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(members[i]);
			if (!ch || ch->IsDead())
			{
				DropPlayerBotDgRunMember(run, members[i], dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "not_ready");
				continue;
			}
			if (!IsPlayerBotGnolleFit(ch))
			{
				sys_log(0, "BOT_GNOLLE: turned away pid=%u name=%s level=%d champion=%d run=%d", members[i], ch->GetName(),
						(int)ch->GetLevel(), (int)ch->GetConquerorLevel(), run.iId);
				DropPlayerBotDgRunMember(run, members[i], dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "not_fit");
				continue;
			}
			if (!PutPlayerBotGnolleOnLevel(ch, 1, in))
			{
				DropPlayerBotDgRunMember(run, members[i], dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "jump_refused");
				continue;
			}
			run.llFees += ChargePlayerBotDgRunEntry(ch, PLAYERBOT_DGRUN_DEFS[run.iDef]);
			gr.inCaves.insert(members[i]);
			++in;
		}
		if (in == 0)
		{
			run.lInstance = 0;
			s_mapPlayerBotGnolleRuns.erase(run.iId);
			return false;
		}
		sys_log(0, "BOT_GNOLLE: in run=%d members=%u fees=%lld", run.iId, (unsigned int)in, run.llFees);
		return true;
	}

	// ------------------------------------------------------------ the walk

	// Towards (tx, ty) on the bot's level: straight in its own room, else to the first portal of the way and through.
	// V2: forceDoor - the route's portal of this room (FindPlayerBotGnolleRouteDoor), walked to and through.
	bool WalkPlayerBotGnolle(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotGnolleRun& gr, long tx, long ty, DWORD dwNow,
			const char* what, int forceDoor = -1)
	{
		const long map = ch->GetMapIndex();
		const TPlayerBotGnolleMaze* m = GetPlayerBotGnolleMaze(map, dwNow);
		long gx = tx, gy = ty;
		int door = -1;
		if (m && forceDoor >= 0 && forceDoor < (int)m->doors.size())
		{
			door = forceDoor;
			gx = m->doors[door].lFromX;
			gy = m->doors[door].lFromY;
		}
		else if (m)
		{
			const DWORD from = GetPlayerBotGnolleRoom(map, ch->GetX(), ch->GetY());
			const DWORD to = GetPlayerBotGnolleRoom(map, tx, ty);
			if (from && to && from != to)
			{
				std::map<DWORD, TPlayerBotGnolleHop> rooms;
				MapPlayerBotGnolleRooms(*m, from, rooms);
				std::map<DWORD, TPlayerBotGnolleHop>::const_iterator h = rooms.find(to);
				if (h != rooms.end() && h->second.door >= 0)
				{
					door = h->second.door;
					gx = m->doors[door].lFromX;
					gy = m->doors[door].lFromY;
				}
				else
					PlayerBotLogThrottled("gnolle_no_way", dwNow, "BOT_GNOLLE: no way by the portals map=%ld from_room=%u to_room=%u what=%s",
							map, (unsigned int)from, (unsigned int)to, what);
			}
		}
		if (door >= 0 && DISTANCE_APPROX(ch->GetX() - gx, ch->GetY() - gy) <= PLAYERBOT_GNOLLE_DOOR_USE)
		{
			// Through the portal, as warp_npc_event moves a player standing on it (it leaves a bot be for a while after
			// its last one - playerbot_monkey_policy.h - and this crossing is the bot's own choice).
			const TPlayerBotGnolleDoor& d = m->doors[door];
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			if (ch->IsStateMove())
				ch->Stop();
			const bool ok = CPlayerBotManager::instance().WarpBot(ch, d.lToX, d.lToY, map);
			playerbot_monkey::NoteGotoCrossing(ch->GetPlayerID(), dwNow);
			++gr.iDoors;
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(map);
			const long bx = pMap ? pMap->m_setting.iBaseX : 0, by = pMap ? pMap->m_setting.iBaseY : 0;
			sys_log(0, "BOT_GNOLLE: door pid=%u name=%s map=%ld portal=%u (%ld,%ld)->(%ld,%ld) for=%s ok=%d", ch->GetPlayerID(),
					ch->GetName(), map, (unsigned int)d.dwVnum, (d.lFromX - bx) / 100, (d.lFromY - by) / 100, (d.lToX - bx) / 100,
					(d.lToY - by) / 100, what, ok ? 1 : 0);
			return true;
		}
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		if (dwNow >= state.dwNextTowerMoveTime)
		{
			state.dwNextTowerMoveTime = dwNow + 1000;
			MovePlayerBot(ch, gx, gy, dwNow, door >= 0 ? 3 : 8, true, false);
		}
		return true;
	}

	// MT2009_PLUS_BOT_GNOLLE_V2: the route's portal of the room `here` (PLAYERBOT_GNOLLE_ROUTE), or -1 (off the route).
	int FindPlayerBotGnolleRouteDoor(const TPlayerBotGnolleMaze& m, long map, DWORD here)
	{
		const int level = GetPlayerBotGnolleLevel(map);
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(map);
		if (level < 1 || !pMap || here == 0)
			return -1;
		for (int k = 0; k < 9 && PLAYERBOT_GNOLLE_ROUTE[level - 1][k][0] != 0; ++k)
		{
			const long wx = pMap->m_setting.iBaseX + PLAYERBOT_GNOLLE_ROUTE[level - 1][k][0] * 100;
			const long wy = pMap->m_setting.iBaseY + PLAYERBOT_GNOLLE_ROUTE[level - 1][k][1] * 100;
			for (size_t i = 0; i < m.doors.size(); ++i)
			{
				const TPlayerBotGnolleDoor& d = m.doors[i];
				if (d.dwFrom == here && labs(d.lFromX - wx) <= PLAYERBOT_GNOLLE_ROUTE_REACH && labs(d.lFromY - wy) <= PLAYERBOT_GNOLLE_ROUTE_REACH)
					return (int)i;
			}
		}
		return -1;
	}

	// ------------------------------------------------------------ the leader

	// The level's hunt: the foe of the room fewest portals away (and nearest in it), chosen every few seconds.
	LPCHARACTER PickPlayerBotGnolleHunt(LPCHARACTER ch, TPlayerBotGnolleRun& gr, TPlayerBotDgRunBot& rb, const TPlayerBotArzDgScan& scan,
			DWORD dwNow)
	{
		LPCHARACTER kept = gr.dwHuntVid ? CHARACTER_MANAGER::instance().Find(gr.dwHuntVid) : NULL;
		if (kept && (!IsPlayerBotPdgFoe(ch, kept) || IsPlayerBotDgRunUnreachable(rb, gr.dwHuntVid, dwNow)))
			kept = NULL;
		if (kept && dwNow - gr.dwHuntAt < PLAYERBOT_GNOLLE_HUNT_PICK_MS)
			return kept;
		gr.dwHuntAt = dwNow;
		const long map = ch->GetMapIndex();
		const TPlayerBotGnolleMaze* m = GetPlayerBotGnolleMaze(map, dwNow);
		const DWORD here = GetPlayerBotGnolleRoom(map, ch->GetX(), ch->GetY());
		std::map<DWORD, TPlayerBotGnolleHop> rooms;
		if (m)
			MapPlayerBotGnolleRooms(*m, here, rooms);
		LPCHARACTER best = NULL;
		long long bestScore = -1;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			if (scan.foes[i].dwRace >= 20000)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c) || IsPlayerBotDgRunUnreachable(rb, scan.foes[i].dwVID, dwNow))
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			int hops = 0;
			if (m && here)
			{
				std::map<DWORD, TPlayerBotGnolleHop>::const_iterator h = rooms.find(GetPlayerBotGnolleRoom(map, c->GetX(), c->GetY()));
				if (h == rooms.end())
					continue;	// a room no portal of ours reaches
				hops = h->second.hops;
			}
			const long long score = (long long)hops * 1000000LL + dist;
			if (bestScore < 0 || score < bestScore)
			{
				bestScore = score;
				best = c;
			}
		}
		gr.dwHuntVid = best ? (DWORD)best->GetVID() : 0;
		return best;
	}

	// Fought at once when it is in the leader's own room and close, else walked to through the maze.
	bool GoForPlayerBotGnolleFoe(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotGnolleRun& gr, TPlayerBotDgRunBot& rb,
			LPCHARACTER foe, DWORD dwNow, const char* what)
	{
		const long map = ch->GetMapIndex();
		const int dist = DISTANCE_APPROX(ch->GetX() - foe->GetX(), ch->GetY() - foe->GetY());
		const DWORD here = GetPlayerBotGnolleRoom(map, ch->GetX(), ch->GetY());
		const DWORD there = GetPlayerBotGnolleRoom(map, foe->GetX(), foe->GetY());
		if (dist > PLAYERBOT_GNOLLE_FIGHT_RANGE || (here && there && here != there))
			return WalkPlayerBotGnolle(ch, state, gr, foe->GetX(), foe->GetY(), dwNow, what);
		state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
		const bool fought = FightPlayerBotTowerObjective(ch, state, foe, dwNow);
		if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
		{
			// Never moved: the caves are everybody's. Left alone a while.
			state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
			rb.unreachable[(DWORD)foe->GetVID()] = dwNow + PLAYERBOT_DGRUN_UNREACHABLE_MS;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			if (gr.dwHuntVid == (DWORD)foe->GetVID())
				gr.dwHuntVid = 0;
		}
		return fought;
	}

	bool DrivePlayerBotGnolleLeader(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotDgRunBot& rb,
			TPlayerBotGnolleRun& gr, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		const int level = GetPlayerBotGnolleLevel(map);
		if (KeepPlayerBotTowerAlive(ch, state, dwNow, PLAYERBOT_PDG_POTION_HP, PLAYERBOT_PDG_POTION_SP))
			return true;
		if (BreakOffPlayerBotArzDgBoss(ch, state, map, dwNow))
			return true;
		if (ch->IsRiding() && !HasPlayerBotBattleHorse(ch))
		{
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "dungeon_run");
			return true;
		}
		if (BuffPlayerBotTowerFellows(ch, state, dwNow))
			return true;
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
		LPCHARACTER threat = NULL, boss = NULL;
		int dThreat = INT_MAX, dBoss = INT_MAX;
		const DWORD here = GetPlayerBotGnolleRoom(map, ch->GetX(), ch->GetY());
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c))
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			// V2: a boss of the leader's own room (the route passes both of a level's), not another party's
			if (IsPlayerBotGnolleBoss(level, c->GetRaceNum()) && !IsPlayerBotDgRunUnreachable(rb, (DWORD)c->GetVID(), dwNow) &&
					dist < dBoss && (here ? GetPlayerBotGnolleRoom(map, c->GetX(), c->GetY()) == here : dist <= PLAYERBOT_GNOLLE_FIGHT_RANGE))
			{
				if (IsPlayerBotGnolleBossTaken((DWORD)c->GetVID(), run.iId, dwNow))
					PlayerBotLogThrottled("gnolle_boss_taken", dwNow, "BOT_GNOLLE: boss left to another party run=%d level=%d race=%u",
							run.iId, level, (unsigned int)c->GetRaceNum());
				else
				{
					boss = c;
					dBoss = dist;
				}
			}
			if (dist > PLAYERBOT_DGRUN_THREAT_RANGE || c->GetRaceNum() >= 20000)
				continue;
			LPCHARACTER v = c->GetVictim();
			if ((v == ch || IsPlayerBotDgRunMemberOf(v, run.iId)) && dist < dThreat &&
					(!here || GetPlayerBotGnolleRoom(map, c->GetX(), c->GetY()) == here))
			{
				threat = c;
				dThreat = dist;
			}
		}
		// A boss no portal of ours reaches is none of this level's (logged once a while).
		if (boss)
		{
			const TPlayerBotGnolleMaze* m = GetPlayerBotGnolleMaze(map, dwNow);
			const DWORD there = GetPlayerBotGnolleRoom(map, boss->GetX(), boss->GetY());
			if (m && here && there && here != there)
			{
				std::map<DWORD, TPlayerBotGnolleHop> rooms;
				MapPlayerBotGnolleRooms(*m, here, rooms);
				if (!rooms.count(there))
				{
					PlayerBotLogThrottled("gnolle_boss_away", dwNow, "BOT_GNOLLE: boss out of the portals' reach run=%d race=%u", run.iId,
							(unsigned int)boss->GetRaceNum());
					rb.unreachable[(DWORD)boss->GetVID()] = dwNow + PLAYERBOT_DGRUN_UNREACHABLE_MS;
					boss = NULL;
				}
			}
		}
		run.dwFocusVID = 0;
		// Nothing new pulled while the leader is hurt or alone (as every run's leader) - what is on it is fought.
		{
			int others = 0, nearBy = 0;
			LPCHARACTER mate = CountPlayerBotDgRunPack(run, ch, PLAYERBOT_DGRUN_PACK_NEAR, others, nearBy);
			const bool hurt = ch->GetMaxHP() > 0 &&
					(long long)ch->GetHP() * 100 < (long long)ch->GetMaxHP() * PLAYERBOT_DGRUN_LEADER_HOLD_HP;
			const bool alone = others > 0 && nearBy < std::min(others, 2);
			if (!alone)
				rb.dwHoldSince = 0;
			else if (rb.dwHoldSince == 0)
				rb.dwHoldSince = dwNow;
			const bool waited = alone && dwNow - rb.dwHoldSince > PLAYERBOT_DGRUN_REGROUP_MAX_MS;
			if ((hurt || (alone && !waited)) && !(threat && dThreat <= PLAYERBOT_DGRUN_HOLD_THREAT_RANGE))
			{
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
				if (!hurt && mate && mate->GetMapIndex() == map &&
						GetPlayerBotGnolleRoom(map, mate->GetX(), mate->GetY()) == here &&
						DISTANCE_APPROX(mate->GetX() - ch->GetX(), mate->GetY() - ch->GetY()) > PLAYERBOT_DGRUN_PACK_NEAR / 2)
				{
					SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
					if (dwNow >= state.dwNextTowerMoveTime)
					{
						state.dwNextTowerMoveTime = dwNow + 1500;
						MovePlayerBot(ch, mate->GetX(), mate->GetY(), dwNow, 6, true, false);
					}
					return true;
				}
				if (ch->IsStateMove())
					ch->Stop();
				SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
				return true;
			}
		}
		if (threat)
			return GoForPlayerBotGnolleFoe(ch, state, gr, rb, threat, dwNow, "threat");
		if (boss)
		{
			if (!gr.bossFought.count((DWORD)boss->GetVID()))
			{
				gr.bossFought[(DWORD)boss->GetVID()] = boss->GetRaceNum();
				sys_log(0, "BOT_GNOLLE: boss up run=%d level=%d race=%u hp=%d/%d distance=%d", run.iId, level,
						(unsigned int)boss->GetRaceNum(), boss->GetHP(), boss->GetMaxHP(), dBoss);
			}
			if (dBoss <= PLAYERBOT_GNOLLE_FIGHT_RANGE)
				run.dwFocusVID = (DWORD)boss->GetVID();
			s_mapPlayerBotGnolleClaims[(DWORD)boss->GetVID()] = std::make_pair(run.iId, dwNow);	// V2: this party's
			return GoForPlayerBotGnolleFoe(ch, state, gr, rb, boss, dwNow, "boss");
		}
		const bool hunting = dwNow - gr.dwLevelSince < GetPlayerBotGnolleHuntMs();
		if (hunting)
		{
			LPCHARACTER foe = PickPlayerBotGnolleHunt(ch, gr, rb, scan, dwNow);
			if (foe)
				return GoForPlayerBotGnolleFoe(ch, state, gr, rb, foe, dwNow, "hunt");
		}
		// V2: what stands close in the leader's room, on the way (a room's while at most) - no walk to other rooms.
		if (here != gr.dwRoom)
		{
			gr.dwRoom = here;
			gr.dwRoomSince = dwNow;
		}
		if (here && dwNow - gr.dwRoomSince < PLAYERBOT_GNOLLE_CLEAR_MS)
		{
			LPCHARACTER nearFoe = NULL;
			int dNear = PLAYERBOT_GNOLLE_CLEAR_RANGE + 1;
			for (size_t i = 0; i < scan.foes.size(); ++i)
			{
				if (scan.foes[i].dwRace >= 20000)
					continue;
				const int dist = DISTANCE_APPROX(ch->GetX() - scan.foes[i].lX, ch->GetY() - scan.foes[i].lY);
				if (dist >= dNear || IsPlayerBotDgRunUnreachable(rb, scan.foes[i].dwVID, dwNow))
					continue;
				LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
				if (!IsPlayerBotPdgFoe(ch, c) || GetPlayerBotGnolleRoom(map, c->GetX(), c->GetY()) != here)
					continue;
				nearFoe = c;
				dNear = dist;
			}
			if (nearFoe)
				return GoForPlayerBotGnolleFoe(ch, state, gr, rb, nearFoe, dwNow, "clear");
		}
		// What lies about, then the way down.
		if (HandleLoot(ch, state, dwNow))
			return true;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		long wx = 0, wy = 0;
		if (!PlayerBotGnolleCell(map, PLAYERBOT_GNOLLE_WAY_CX, PLAYERBOT_GNOLLE_WAY_CY, wx, wy))
			return true;
		if (DISTANCE_APPROX(ch->GetX() - wx, ch->GetY() - wy) <= PLAYERBOT_GNOLLE_WAY_REACH)
		{
			if (gr.dwWaySince == 0)
			{
				gr.dwWaySince = dwNow;
				sys_log(0, "BOT_GNOLLE: at the way down run=%d level=%d after_s=%u", run.iId, level, (dwNow - gr.dwLevelSince) / 1000);
			}
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		// V2: the route - this room's portal of it; off the route (or the maze not read yet) the maze's own search.
		{
			const TPlayerBotGnolleMaze* m = GetPlayerBotGnolleMaze(map, dwNow);
			if (m && here && here != GetPlayerBotGnolleRoom(map, wx, wy))
			{
				const int door = FindPlayerBotGnolleRouteDoor(*m, map, here);
				if (door >= 0)
				{
					if (gr.iRouteDoor != door)
					{
						gr.iRouteDoor = door;
						sys_log(0, "BOT_GNOLLE: route run=%d level=%d room=%u portal=%u level_s=%u", run.iId, level, (unsigned int)here,
								(unsigned int)m->doors[door].dwVnum, (dwNow - gr.dwLevelSince) / 1000);
					}
					return WalkPlayerBotGnolle(ch, state, gr, wx, wy, dwNow, "route", door);
				}
				PlayerBotLogThrottled("gnolle_off_route", dwNow, "BOT_GNOLLE: off the route run=%d level=%d room=%u - the maze's way",
						run.iId, level, (unsigned int)here);
			}
		}
		return WalkPlayerBotGnolle(ch, state, gr, wx, wy, dwNow, "way_down");
	}

	// ------------------------------------------------------------ the others

	bool FightPlayerBotGnolleFollower(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotDgRunBot& rb,
			LPCHARACTER anchor, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		if (KeepPlayerBotTowerAlive(ch, state, dwNow, PLAYERBOT_PDG_POTION_HP, PLAYERBOT_PDG_POTION_SP))
			return true;
		if (BreakOffPlayerBotArzDgBoss(ch, state, map, dwNow))
			return true;
		if (BuffPlayerBotTowerFellows(ch, state, dwNow))
			return true;
		const DWORD mine = GetPlayerBotGnolleRoom(map, ch->GetX(), ch->GetY());
		const DWORD lead = GetPlayerBotGnolleRoom(map, anchor->GetX(), anchor->GetY());
		const int toLeader = DISTANCE_APPROX(ch->GetX() - anchor->GetX(), ch->GetY() - anchor->GetY());
		// In another room than the leader's (a portal it went through), or far: beside it (the party pass's catch-up).
		if ((mine && lead && mine != lead) || toLeader > PLAYERBOT_PDG_CATCH_UP_DISTANCE)
		{
			if (dwNow >= rb.pdg.dwNextCatchUp && !anchor->IsWarping() && !anchor->IsDead())
			{
				rb.pdg.dwNextCatchUp = dwNow + PLAYERBOT_PDG_CATCH_UP_RETRY_MS;
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
				ClearPlayerBotRoute(state, true);
				if (PutPlayerBotBesidePdgPerson(ch, anchor))
				{
					// Set down by the leader, who came through a portal: not sent back by the one beside it.
					playerbot_monkey::NoteGotoCrossing(ch->GetPlayerID(), dwNow);
					PlayerBotLogThrottled("gnolle_catch_up", dwNow, "BOT_GNOLLE: caught up pid=%u name=%s run=%d distance=%d other_room=%d",
							ch->GetPlayerID(), ch->GetName(), run.iId, toLeader, mine != lead ? 1 : 0);
					return true;
				}
			}
			if (mine && lead && mine != lead)
			{
				// Waiting for the catch-up: only what attacks it.
				LPCHARACTER t = FindPlayerBotDgRunThreat(ch, run.iId);
				if (t)
					return FightPlayerBotTowerObjective(ch, state, t, dwNow);
				if (ch->IsStateMove())
					ch->Stop();
				SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
				return true;
			}
		}
		// The leader's focus (a boss), for everybody not hurt.
		if (run.dwFocusVID != 0 && ch->GetMaxHP() > 0 && !IsPlayerBotKillRewardless(ch) &&
				(long long)ch->GetHP() * 100 >= (long long)ch->GetMaxHP() * PLAYERBOT_DGRUN_FOCUS_HP)
		{
			LPCHARACTER focus = CHARACTER_MANAGER::instance().Find(run.dwFocusVID);
			if (IsPlayerBotPdgFoe(ch, focus) && GetPlayerBotGnolleRoom(map, focus->GetX(), focus->GetY()) == mine)
				return FightPlayerBotTowerObjective(ch, state, focus, dwNow);
		}
		// What attacks it or the leader, what the leader hits, else the nearest round the leader - in its own room.
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
		LPCHARACTER threat = NULL, aimed = NULL, any = NULL;
		int dThreat = INT_MAX, dAny = INT_MAX;
		LPCHARACTER leaderVictim = anchor->GetVictim();
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			if (scan.foes[i].dwRace >= 20000)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c) || IsPlayerBotDgRunUnreachable(rb, scan.foes[i].dwVID, dwNow))
				continue;
			const int toAnchor = DISTANCE_APPROX(anchor->GetX() - c->GetX(), anchor->GetY() - c->GetY());
			if (toAnchor > PLAYERBOT_GNOLLE_FOLLOW_RANGE)
				continue;
			if (mine && GetPlayerBotGnolleRoom(map, c->GetX(), c->GetY()) != mine)
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			LPCHARACTER v = c->GetVictim();
			if ((v == ch || v == anchor) && dist < dThreat)
			{
				threat = c;
				dThreat = dist;
			}
			if (c == leaderVictim)
				aimed = c;
			if (dist < dAny)
			{
				any = c;
				dAny = dist;
			}
		}
		LPCHARACTER foe = threat ? threat : (aimed ? aimed : any);
		if (foe)
		{
			state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
			const bool fought = FightPlayerBotTowerObjective(ch, state, foe, dwNow);
			if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
			{
				state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
				rb.unreachable[(DWORD)foe->GetVID()] = dwNow + PLAYERBOT_DGRUN_UNREACHABLE_MS;
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
			}
			return fought;
		}
		if (HandleLoot(ch, state, dwNow))
			return true;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		const int stay = PLAYERBOT_PDG_STAY_DISTANCE - (int)(ch->GetPlayerID() % 4) * 50;
		if (toLeader > stay)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			if (dwNow >= state.dwNextTowerMoveTime)
			{
				state.dwNextTowerMoveTime = dwNow + 1000;
				MovePlayerBot(ch, anchor->GetX(), anchor->GetY(), dwNow, 6, true, false);
			}
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// MT2009_PLUS_BOT_GNOLLE_V2: under "gnolle retreat" of its health a member drinks; the potion not enough, it steps back
	// as the run's break-off does (hidden a few seconds, to the pack, healed) - before the 30% of the other runs: a death
	// here is the caves' end for it.
	bool RetreatPlayerBotGnolle(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotGnolleRun& gr, DWORD dwNow)
	{
		const int pct = s_kPlayerBotGnolleCfg.iRetreatHp;
		if (pct <= 0 || state.bRecoveringAfterDeath || ch->IsDead() || ch->GetMaxHP() <= 0 ||
				(long long)ch->GetHP() * 100 > (long long)ch->GetMaxHP() * pct)
			return false;
		UseHealthPotion(ch, state, dwNow, 100);
		if (((long long)ch->GetHP() + ch->GetPoint(POINT_HP_RECOVERY)) * 100 > (long long)ch->GetMaxHP() * pct)
			return false;
		state.bRecoveringAfterDeath = true;
		state.dwLastDeathTime = dwNow;
		state.lDeathX = 0;
		state.lDeathY = 0;
		state.dwNextRecoveryHealTime = dwNow;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ClearPlayerBotRoute(state, true);
		ch->ReviveInvisible(5);
		state.dwNextRecoveryProtectionTime = dwNow + PLAYERBOT_RECOVERY_PROTECTION_INTERVAL;
		++run.iBreakOffs;
		++gr.iRetreats;
		PlayerBotLogThrottled("gnolle_retreat", dwNow, "BOT_GNOLLE: retreat pid=%u name=%s run=%d level=%d hp=%d/%d", ch->GetPlayerID(),
				ch->GetName(), run.iId, gr.iLevel, ch->GetHP(), ch->GetMaxHP());
		return true;
	}

	// ------------------------------------------------------------ the bot's tick

	// A member on the run's level (ManagePlayerBotDungeonRun, DGRUN_PHASE_INSIDE).
	bool ManagePlayerBotGnolleInside(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotDgRunBot& rb,
			DWORD dwNow)
	{
		std::map<int, TPlayerBotGnolleRun>::iterator g = s_mapPlayerBotGnolleRuns.find(run.iId);
		if (g == s_mapPlayerBotGnolleRuns.end())
			return false;
		TPlayerBotGnolleRun& gr = g->second;
		state.lLastX = ch->GetX();
		state.lLastY = ch->GetY();
		// A portal or the way down moved it: the route and the target of the room before go.
		if (rb.lLastX != 0 && DISTANCE_APPROX(ch->GetX() - rb.lLastX, ch->GetY() - rb.lLastY) > 3000)
		{
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			if (ch->IsStateMove())
				ch->Stop();
		}
		rb.lLastX = ch->GetX();
		rb.lLastY = ch->GetY();
		if (rb.pdg.lInstance != run.lInstance)
		{
			rb.pdg.lInstance = run.lInstance;
			rb.pdg.dwEnteredAt = dwNow;
		}
		RestockPlayerBotArzDg(ch, rb.arz, dwNow);
		if (gr.bExit)
		{
			// The run is over: standing while the monitor takes everybody out.
			if (ch->IsStateMove())
				ch->Stop();
			return true;
		}
		if (!state.bRecoveringAfterDeath && !FindPlayerBotDgRunThreat(ch, run.iId) && HandleLoot(ch, state, dwNow))
			return true;
		if (RetreatPlayerBotGnolle(ch, state, run, gr, dwNow))	// MT2009_PLUS_BOT_GNOLLE_V2
			return true;
		if (KeepPlayerBotDgRunAlive(ch, state, run, dwNow))
			return true;
		if (HealPlayerBotDgRunFellow(ch, state, run, dwNow))
			return true;
		if (run.bFallback)
			return FallBackPlayerBotDgRun(ch, state, run, dwNow);
		LPCHARACTER anchor = run.dwAnchor ? CHARACTER_MANAGER::instance().FindByPID(run.dwAnchor) : NULL;
		if (!anchor || anchor == ch || anchor->GetMapIndex() != ch->GetMapIndex())
			return DrivePlayerBotGnolleLeader(ch, state, run, rb, gr, dwNow);
		return FightPlayerBotGnolleFollower(ch, state, run, rb, anchor, dwNow);
	}

	// ------------------------------------------------------------ the monitor

	// One member out to Dongan, by the gathering spot: the engine's warp, else the run's own move (Dongan is a Sung Ma map
	// too - a bot's plain "warpset" onto it may be refused, "dungeon_run_out" is the run's).
	bool SendPlayerBotGnolleOut(TPlayerBotDgRun& run, LPCHARACTER ch, DWORD dwNow, const char* why)
	{
		s_szPlayerBotTransitionRefusal = NULL;
		bool ok = ch->WarpSet(run.place.x, run.place.y) && GetPlayerBotGnolleLevel(ch->GetMapIndex()) == 0;
		if (!ok)
		{
			TPlayerBotAIState* state = GetPlayerBotDgRunState(ch->GetPlayerID());
			if (state)
				ok = TransitionPlayerBotMap(ch, *state, run.place.map, run.place.x, run.place.y, dwNow, "dungeon_run_out");
		}
		sys_log(0, "BOT_GNOLLE: out pid=%u name=%s run=%d now_on=%ld why=%s ok=%d refused=%s", ch->GetPlayerID(), ch->GetName(),
				run.iId, ch->GetMapIndex(), why, ok ? 1 : 0, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "-");
		s_szPlayerBotTransitionRefusal = NULL;
		return ok;
	}

	// Everybody alive in the caves (any level) out to Dongan, by the gathering spot.
	void PullPlayerBotGnolleRun(TPlayerBotDgRun& run, TPlayerBotGnolleRun& gr, const char* why, DWORD dwNow)
	{
		if (!run.szResult)
			run.szResult = why;
		if (gr.dwPullSince == 0)
			gr.dwPullSince = dwNow;
		gr.bExit = true;
		if (dwNow < run.dwNextPull)
			return;
		run.dwNextPull = dwNow + PLAYERBOT_DGRUN_PULL_RETRY_MS;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!ch || ch->IsDead() || GetPlayerBotGnolleLevel(ch->GetMapIndex()) == 0)
				continue;
			SendPlayerBotGnolleOut(run, ch, dwNow, why);
		}
	}

	// MT2009_PLUS_BOT_GNOLLE_V2: the strength for the next level ("gnolle l2" / "gnolle l3"). A member short of it goes out
	// to Dongan; the party goes on with enough members, a healer and the gear's average - else everybody out (aborted).
	// False: the run is over.
	bool GatePlayerBotGnolleWayDown(TPlayerBotDgRun& run, TPlayerBotGnolleRun& gr, DWORD dwNow)
	{
		const int next = gr.iLevel + 1;
		if (next < 2 || next > 3)
			return true;
		const int gate = next - 2;
		const TPlayerBotGnolleGate& g = s_kPlayerBotGnolleCfg.gate[gate];
		std::vector<DWORD> weak;
		std::string weakNames;
		int fit = 0, gearSum = 0;
		bool healer = false;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->IsDead() || c->GetMapIndex() != run.lInstance)
				continue;
			const char* why = GetPlayerBotGnolleWeakness(c, gate, true);
			if (why)
			{
				weak.push_back(run.members[i]);
				if (weakNames.size() < 200)
				{
					char buf[96];
					snprintf(buf, sizeof(buf), "%s%s:%s(c%d/hp%d)", weakNames.empty() ? "" : ",", c->GetName(), why,
							(int)c->GetConquerorLevel(), c->GetMaxHP());
					weakNames += buf;
				}
				continue;
			}
			int plus = 0;
			gearSum += GetPlayerBotYdgGearLevel(c, &plus);
			++fit;
			healer = healer || (c->GetJob() == JOB_SHAMAN && c->GetSkillGroup() != 0);
		}
		const int avg = fit > 0 ? gearSum / fit : 0;
		const bool ok = fit >= g.members && (!g.healer || healer) && avg >= g.avg;
		sys_log(0, "BOT_GNOLLE: gate run=%d to_level=%d fit=%d (needs %d) healer=%d gear_avg=%d (needs %d) ok=%d weak=%s", run.iId,
				next, fit, g.members, healer ? 1 : 0, avg, g.avg, ok ? 1 : 0, weakNames.empty() ? "-" : weakNames.c_str());
		if (!ok)
		{
			sys_log(0, "BOT_GNOLLE: stop run=%d level=%d - not strong enough for level %d, out of the caves", run.iId, gr.iLevel, next);
			PullPlayerBotGnolleRun(run, gr, "aborted", dwNow);
			return false;
		}
		for (size_t i = 0; i < weak.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(weak[i]);
			if (c)
				SendPlayerBotGnolleOut(run, c, dwNow, "not_strong");
			++gr.iNotStrong;
			DropPlayerBotDgRunMember(run, weak[i], dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "not_strong");
		}
		return true;
	}

	// The party down to the next level (each one's warp, the dialog's), or out by level 3's exit.
	void TakePlayerBotGnolleWayDown(TPlayerBotDgRun& run, TPlayerBotGnolleRun& gr, DWORD dwNow)
	{
		const int level = gr.iLevel;
		const long from = run.lInstance;
		char buf[16];
		snprintf(buf, sizeof(buf), "%s%u", run.stageSecs.empty() ? "" : ",", (dwNow - gr.dwLevelSince) / 1000);
		if (run.stageSecs.size() < 120)
			run.stageSecs += buf;
		if (level >= 3)
		{
			run.dwFinishedAt = dwNow;
			sys_log(0, "BOT_DGRUN: finished run=%d dungeon=%s took_s=%u deaths=%d wipes=%d bosses=%d", run.iId,
					PLAYERBOT_DGRUN_DEFS[run.iDef].szKey, (dwNow - run.dwEnteredAt) / 1000, run.iDeaths, run.iWipes, gr.iBossKills);
			sys_log(0, "BOT_GNOLLE: out by level 3's exit run=%d took_s=%u bosses=%d (%s)", run.iId, (dwNow - run.dwEnteredAt) / 1000,
					gr.iBossKills, gr.bosses.empty() ? "-" : gr.bosses.c_str());
			PullPlayerBotGnolleRun(run, gr, "finished", dwNow);
			return;
		}
		const int next = level + 1;
		run.lInstance = PLAYERBOT_GNOLLE_MAP_FIRST + next - 1;	// before the warps
		int moved = 0, left = 0;
		size_t idx = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!ch || ch->GetMapIndex() != from)
				continue;
			if (ch->IsDead())
			{
				++left;
				continue;
			}
			if (PutPlayerBotGnolleOnLevel(ch, next, idx++))
			{
				++moved;
				RebuffPlayerBotGnolleMember(ch, run, "level");	// MT2009_PLUS_BOT_GNOLLE_V2: the bonuses' hour again
			}
			else
				++left;
		}
		gr.iLevel = next;
		gr.dwLevelSince = dwNow;
		gr.dwWaySince = 0;
		gr.dwHuntVid = 0;
		gr.dwRoom = gr.dwRoomSince = 0;	// MT2009_PLUS_BOT_GNOLLE_V2
		gr.iRouteDoor = -1;
		run.iStage = next;
		run.dwStageSince = dwNow;
		run.dwLastProgress = dwNow;
		run.dwFocusVID = 0;
		run.bFallback = false;
		run.bAllDead = false;
		PlayerBotGnolleCell(run.lInstance, PLAYERBOT_GNOLLE_ENTRY_CX, PLAYERBOT_GNOLLE_ENTRY_CY, run.lCampX, run.lCampY);
		sys_log(0, "BOT_DGRUN: stage run=%d dungeon=%s instance=%ld stage=%d after_s=%u inside=%d alive=%d", run.iId,
				PLAYERBOT_DGRUN_DEFS[run.iDef].szKey, run.lInstance, next, (dwNow - run.dwEnteredAt) / 1000, moved + left, moved);
		sys_log(0, "BOT_GNOLLE: level run=%d level=%d moved=%d left_behind=%d after_s=%u", run.iId, next, moved, left,
				(dwNow - run.dwEnteredAt) / 1000);
	}

	// One second of a run in the caves: false when it is over (closed here).
	bool UpdatePlayerBotGnolleRun(TPlayerBotDgRun& run, DWORD dwNow)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		TPlayerBotGnolleRun& gr = s_mapPlayerBotGnolleRuns[run.iId];
		if (gr.dwLevelSince == 0)
			gr.dwLevelSince = gr.dwNextProgress = dwNow;
		run.iStage = gr.iLevel;
		int inside = 0, alive = 0, fit = 0, caves = 0;
		long long sx = 0, sy = 0;
		run.dwAnchor = 0;
		DWORD standIn = 0;
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwLeader);
		if (leader && leader->GetMapIndex() == run.lInstance && !leader->IsDead())
		{
			if (!IsPlayerBotDgRunRecovering(run.dwLeader))
				run.dwAnchor = run.dwLeader;
			else
				standIn = run.dwLeader;
		}
		const std::vector<DWORD> members = run.members;
		for (size_t i = 0; i < members.size(); ++i)
		{
			const DWORD pid = members[i];
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch)
			{
				DropPlayerBotDgRunMember(run, pid, dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "offline");
				continue;
			}
			const long map = ch->GetMapIndex();
			const bool wasDead = run.dead.count(pid) != 0;
			// Stood up in the caves after a death: to Dongan, as the quest sends a player (its die/timer does it for a
			// bot as well when the move is let through - this makes sure of it).
			if (wasDead && !ch->IsDead() && GetPlayerBotGnolleLevel(map) > 0 && !gr.bExit && !run.szResult)
			{
				run.dead.erase(pid);
				SendPlayerBotGnolleOut(run, ch, dwNow, "died");
				continue;
			}
			if (GetPlayerBotGnolleLevel(map) > 0)
			{
				++caves;
				if (ch->IsDead() && !wasDead)
				{
					run.dead.insert(pid);
					++run.iDeaths;
					++s_aPlayerBotDgRunStats[run.iDef].dwDeaths;
					sys_log(0, "BOT_DGRUN: died pid=%u name=%s run=%d dungeon=%s stage=%d level=%u", pid, ch->GetName(), run.iId,
							def.szKey, gr.iLevel, (unsigned int)ch->GetLevel());
				}
			}
			if (map != run.lInstance)
			{
				if (gr.bExit)
					continue;
				if (GetPlayerBotGnolleLevel(map) > 0)
				{
					// Alive on another level (the party went down without it): out after a while.
					if (ch->IsDead())
						continue;
					DWORD& since = gr.behindSince[pid];
					if (since == 0)
						since = dwNow;
					if (dwNow - since >= PLAYERBOT_GNOLLE_BEHIND_MS)
					{
						gr.behindSince.erase(pid);
						SendPlayerBotGnolleOut(run, ch, dwNow, "left_behind");
						DropPlayerBotDgRunMember(run, pid, dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "left_behind");
					}
					continue;
				}
				// Out of the caves: the quest's way after a death (Dongan), or anything else that took it.
				if (!gr.inCaves.count(pid) || ch->IsDead() || ch->IsWarping())
					continue;
				run.dead.erase(pid);
				int& back = gr.reentries[pid];
				if (gr.iLevel == 1 && back < PLAYERBOT_GNOLLE_REENTRIES && !run.dwFinishedAt && !run.szResult &&
						IsPlayerBotGnolleFit(ch))
				{
					// Level 1: back in as a player does - another Przepustka at Halabardnik.
					if (PutPlayerBotGnolleOnLevel(ch, 1, (size_t)(pid % 9)))
					{
						++back;
						++gr.iReentries;
						run.llFees += ChargePlayerBotGnolleTicket(ch);
						// MT2009_PLUS_BOT_GNOLLE_V2: the death cleared the run's bonuses (half the health on the Sung Ma maps)
						RebuffPlayerBotGnolleMember(ch, run, "back_in");
						sys_log(0, "BOT_GNOLLE: back in pid=%u name=%s run=%d times=%d from=%ld", pid, ch->GetName(), run.iId, back, map);
						continue;
					}
				}
				++gr.iDiedOut;
				sys_log(0, "BOT_GNOLLE: died out pid=%u name=%s run=%d level=%d map=%ld back_in=%d", pid, ch->GetName(), run.iId,
						gr.iLevel, map, back);
				DropPlayerBotDgRunMember(run, pid, dwNow, PLAYERBOT_DGRUN_REST_REFUSED_MS, "died_out");
				continue;
			}
			gr.behindSince.erase(pid);
			++inside;
			if (ch->IsDead())
				continue;
			if (wasDead)
				run.dead.erase(pid);
			++alive;
			sx += ch->GetX();
			sy += ch->GetY();
			if (IsPlayerBotDgRunFit(ch))
				++fit;
			if (run.dwAnchor == 0 && !IsPlayerBotDgRunRecovering(pid))
				run.dwAnchor = pid;
			if (standIn == 0)
				standIn = pid;
		}
		if (run.dwAnchor == 0)
			run.dwAnchor = standIn;
		run.iPackN = alive;
		run.iFit = fit;
		if (alive > 0)
		{
			run.lPackX = (long)(sx / alive);
			run.lPackY = (long)(sy / alive);
		}
		// The ends: out of the caves, everybody.
		if (gr.bExit || run.szResult)
		{
			if (caves == 0 || run.members.empty() || (gr.dwPullSince && dwNow - gr.dwPullSince >= PLAYERBOT_GNOLLE_PULL_GRACE_MS))
			{
				ClosePlayerBotDgRun(run, run.dwFinishedAt ? "finished" : (run.szResult ? run.szResult : "lost"), dwNow);
				return false;
			}
			PullPlayerBotGnolleRun(run, gr, run.szResult ? run.szResult : "finished", dwNow);
			return true;
		}
		if (run.members.empty())
		{
			ClosePlayerBotDgRun(run, "lost", dwNow);
			return false;
		}
		if (inside == 0)
		{
			if (run.dwOutSince == 0)
				run.dwOutSince = dwNow;
			if (dwNow - run.dwOutSince >= PLAYERBOT_GNOLLE_BEHIND_MS + 5000)
			{
				PullPlayerBotGnolleRun(run, gr, "lost", dwNow);
				return true;
			}
			return true;
		}
		run.dwOutSince = 0;
		if (alive == 0 && !run.bAllDead)
		{
			++run.iWipes;
			run.dwLastWipeAt = dwNow;
			sys_log(0, "BOT_DGRUN: wipe run=%d dungeon=%s stage=%d inside=%d wipes=%d after_s=%u", run.iId, def.szKey, gr.iLevel,
					inside, run.iWipes, (dwNow - run.dwEnteredAt) / 1000);
		}
		run.bAllDead = alive == 0;
		// The camp (the leader's last quiet spot, or where a portal put it) and the fallback to it.
		{
			LPCHARACTER a = run.dwAnchor ? CHARACTER_MANAGER::instance().FindByPID(run.dwAnchor) : NULL;
			if (a && !a->IsDead() && a->GetMapIndex() == run.lInstance && !IsPlayerBotDgRunRecovering(run.dwAnchor))
			{
				bool quiet = true;
				const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
				for (size_t i = 0; i < scan.foes.size() && quiet; ++i)
					quiet = scan.foes[i].dwRace >= 8000 ||
							DISTANCE_APPROX(scan.foes[i].lX - a->GetX(), scan.foes[i].lY - a->GetY()) > PLAYERBOT_DGRUN_QUIET_RANGE;
				const bool jumped = run.lCampX != 0 &&
						GetPlayerBotGnolleRoom(run.lInstance, run.lCampX, run.lCampY) != GetPlayerBotGnolleRoom(run.lInstance, a->GetX(), a->GetY());
				if (quiet || jumped || run.lCampX == 0)
				{
					run.lCampX = a->GetX();
					run.lCampY = a->GetY();
				}
			}
			if (!run.bFallback)
			{
				if (inside >= 3 && alive > 0 && fit * 2 < inside && dwNow >= run.dwFallbackRestUntil)
				{
					run.bFallback = true;
					run.dwFallbackSince = dwNow;
					++run.iFallbacks;
					sys_log(0, "BOT_DGRUN: fallback run=%d dungeon=%s stage=%d inside=%d alive=%d fit=%d", run.iId, def.szKey,
							gr.iLevel, inside, alive, fit);
				}
			}
			else if (alive == 0 || fit * 4 >= inside * 3 || dwNow - run.dwFallbackSince >= PLAYERBOT_DGRUN_FALLBACK_MAX_MS)
			{
				run.bFallback = false;
				run.dwFallbackRestUntil = dwNow + PLAYERBOT_DGRUN_FALLBACK_REST_MS;
			}
		}
		// The bosses the leader went for: down when gone from the level.
		if (!gr.bossFought.empty())
		{
			const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
			for (std::map<DWORD, DWORD>::iterator b = gr.bossFought.begin(); b != gr.bossFought.end();)
			{
				bool up = false;
				for (size_t i = 0; i < scan.foes.size() && !up; ++i)
					up = scan.foes[i].dwVID == b->first;
				if (up)
				{
					++b;
					continue;
				}
				++gr.iBossKills;
				char bb[24];
				snprintf(bb, sizeof(bb), "%sL%d:%u", gr.bosses.empty() ? "" : ",", gr.iLevel, (unsigned int)b->second);
				if (gr.bosses.size() < 100)
					gr.bosses += bb;
				run.dwLastProgress = dwNow;
				sys_log(0, "BOT_GNOLLE: boss down run=%d level=%d race=%u after_s=%u", run.iId, gr.iLevel, (unsigned int)b->second,
						(dwNow - gr.dwLevelSince) / 1000);
				gr.bossFought.erase(b++);
			}
		}
		// The way down: the leader by it, the others with it (or a while gone).
		if (gr.dwWaySince != 0)
		{
			long wx = 0, wy = 0;
			PlayerBotGnolleCell(run.lInstance, PLAYERBOT_GNOLLE_WAY_CX, PLAYERBOT_GNOLLE_WAY_CY, wx, wy);
			int by = 0;
			for (size_t i = 0; i < run.members.size(); ++i)
			{
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
				if (c && !c->IsDead() && c->GetMapIndex() == run.lInstance &&
						DISTANCE_APPROX(c->GetX() - wx, c->GetY() - wy) <= PLAYERBOT_GNOLLE_WAY_GATHER)
					++by;
			}
			if ((by >= alive && dwNow - gr.dwWaySince >= 3000) || dwNow - gr.dwWaySince >= PLAYERBOT_GNOLLE_WAY_WAIT_MS)
			{
				if (gr.iLevel < 3 && !GatePlayerBotGnolleWayDown(run, gr, dwNow))	// MT2009_PLUS_BOT_GNOLLE_V2
					return true;
				TakePlayerBotGnolleWayDown(run, gr, dwNow);
				return true;
			}
		}
		if (dwNow >= gr.dwNextProgress)
		{
			gr.dwNextProgress = dwNow + PLAYERBOT_GNOLLE_PROGRESS_MS;
			LPCHARACTER a = run.dwAnchor ? CHARACTER_MANAGER::instance().FindByPID(run.dwAnchor) : NULL;
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(run.lInstance);
			const long bx = pMap ? pMap->m_setting.iBaseX : 0, by = pMap ? pMap->m_setting.iBaseY : 0;
			sys_log(0, "BOT_GNOLLE: progress run=%d level=%d level_s=%u inside=%d alive=%d fit=%d members=%u deaths=%d died_out=%d "
					"back_in=%d doors=%d bosses=%d focus=%u leader=%s@(%ld,%ld) room=%u way=%d retreats=%d", run.iId, gr.iLevel,
					(dwNow - gr.dwLevelSince) / 1000, inside, alive, fit, (unsigned int)run.members.size(), run.iDeaths, gr.iDiedOut,
					gr.iReentries, gr.iDoors, gr.iBossKills, (unsigned int)run.dwFocusVID, a ? a->GetName() : "-",
					a ? (a->GetX() - bx) / 100 : 0, a ? (a->GetY() - by) / 100 : 0,
					a ? (unsigned int)GetPlayerBotGnolleRoom(run.lInstance, a->GetX(), a->GetY()) : 0U, gr.dwWaySince ? 1 : 0, gr.iRetreats);
		}
		if (run.iDeaths >= PLAYERBOT_DGRUN_MAX_DEATHS)
		{
			sys_log(0, "BOT_DGRUN: given up after %d deaths run=%d dungeon=%s stage=%d", run.iDeaths, run.iId, def.szKey, gr.iLevel);
			PullPlayerBotGnolleRun(run, gr, "wipe", dwNow);
			return true;
		}
		if (dwNow - gr.dwLevelSince >= GetPlayerBotGnolleLevelMaxMs())
		{
			sys_log(0, "BOT_DGRUN: abandoned run=%d dungeon=%s stage=%d after_s=%u (the level's time)", run.iId, def.szKey, gr.iLevel,
					(dwNow - run.dwEnteredAt) / 1000);
			PullPlayerBotGnolleRun(run, gr, "abandoned", dwNow);
			return true;
		}
		if (dwNow - run.dwEnteredAt >= (DWORD)def.iLimitMin * 60000U + PLAYERBOT_DGRUN_LIMIT_MARGIN_MS)
		{
			PullPlayerBotGnolleRun(run, gr, "timeout", dwNow);
			return true;
		}
		return true;
	}

	// ------------------------------------------------------------ the run's end

	void NotePlayerBotGnolleRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS)
	{
		std::map<int, TPlayerBotGnolleRun>::iterator g = s_mapPlayerBotGnolleRuns.find(run.iId);
		TPlayerBotGnolleRun gr = g != s_mapPlayerBotGnolleRuns.end() ? g->second : TPlayerBotGnolleRun();
		if (g != s_mapPlayerBotGnolleRuns.end())
			s_mapPlayerBotGnolleRuns.erase(g);
		// MT2009_PLUS_BOT_GNOLLE_V2: its bosses free for the others
		for (std::map<DWORD, std::pair<int, DWORD> >::iterator c = s_mapPlayerBotGnolleClaims.begin(); c != s_mapPlayerBotGnolleClaims.end();)
		{
			if (c->second.first == run.iId)
				s_mapPlayerBotGnolleClaims.erase(c++);
			else
				++c;
		}
		const bool won = run.dwFinishedAt != 0;
		const int party = GetPlayerBotYdgTrainParty(run.iId);
		std::string names;
		for (size_t i = 0; i < run.members.size() && names.size() < 200; ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (c)
				names += (names.empty() ? "" : ",") + std::string(c->GetName());
		}
		sys_log(0, "BOT_GNOLLE: run end run=%d train_party=%d result=%s won=%d entered=%d took_s=%u level=%d level_s=%s deaths=%d "
				"wipes=%d died_out=%d back_in=%d doors=%d bosses=%d (%s) members=%u fees=%lld retreats=%d not_strong=%d", run.iId, party,
				result ? result : "-",
				won ? 1 : 0, entered ? 1 : 0, tookS, entered ? gr.iLevel : 0, run.stageSecs.empty() ? "-" : run.stageSecs.c_str(),
				run.iDeaths, run.iWipes, gr.iDiedOut, gr.iReentries, gr.iDoors, gr.iBossKills, gr.bosses.empty() ? "-" : gr.bosses.c_str(),
				(unsigned int)run.members.size(), run.llFees, gr.iRetreats, gr.iNotStrong);
		FILE* fp = fopen(PLAYERBOT_GNOLLE_RUNS_FILE, "a");
		if (fp)
		{
			fprintf(fp, "%ld\t%d\t%d\t%s\t%d\t%u\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%u\t%lld\t%s\n", (long)time(0), run.iId, party,
					result ? result : "-", won ? 1 : 0, tookS, entered ? gr.iLevel : 0, run.stageSecs.empty() ? "-" : run.stageSecs.c_str(),
					run.iDeaths, run.iWipes, gr.iDiedOut, gr.iReentries, gr.iDoors, gr.iBossKills, gr.bosses.empty() ? "-" : gr.bosses.c_str(),
					(unsigned int)run.members.size(), run.llFees, names.empty() ? "-" : names.c_str());
			fclose(fp);
		}
	}
}

#endif
