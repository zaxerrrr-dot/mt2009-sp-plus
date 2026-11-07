#pragma once
// MT2009_PLUS_PVPFAN_V1: "PVP Fan" - bot wars for fun (the owner, 7 November 2026: "w panelu Seban kategoria PVP Fan
// ... tworzysz boty - 10, 100, 500 - ktorych jedynym zadaniem jest walczyc ze soba, jak wojna dla botow ... np. 50
// Wojownikow Cialo vs 50 Szamanow Smok ... /pvp start <kategoria> ... wszystkie boty sie loguja, teleportuja i czekaja
// ... /pvp ready ... walcza az wszyscy z jednej strony padna"). "/pvp" is the engine's duel command, so the GM's
// command is "/pvpfan".
//
// What it is:
//   * a category (player.pvpfan_category, made in the Seban panel's "PVP Fan" page, pvpfan.py): a name, a code for
//     the command, the arena (map + centre, how far the teams start from it, the arena's leash), the channel, the
//     countdown, the time limit, whether people may join in and whether the bots drink potions;
//   * its teams (2..8, player.pvpfan_team) and their slots (player.pvpfan_slot: N characters of a class, path, sex,
//     level, skill level, stats and an equipment set - player.pvpfan_set / _set_item, the panel's configurator; set
//     0 = the class's preset);
//   * its characters (player.pvpfan_char): dedicated identities the PANEL makes while the world runs - an account
//     playerbot_pfNNNN (password '!', status BLOCK: no person logs in there), the character, its player_index row.
//     They are not in common.playerbot_seed_state, so the population's registry never knows them: no hunting,
//     trading, market, quests, cohorts, Dropki, rankings, SM grants or chat. They are offline unless a war runs.
//
// The war, on the core that hosts the category's map on its channel (one core; any other core's "/pvpfan start"
// and the panel's buttons go through player.pvpfan_command, polled every PVPFAN_COMMAND_POLL_MS):
//   starting  - the roster read once (category, teams, slots, characters, sets), each fighter's spot worked out (the
//               team's own point or a circle round the centre, a formation of rows facing the centre, snapped to open
//               ground), the bots logged in PVPFAN_SPAWN_PER_SEC a second (M2_PVPFAN_SPAWN_PER_SEC) straight onto
//               their spot (CPlayerBotManager::PlaceLoadingBot asks PlacePlayerBotPvpFanLoading first); as each one's
//               bag arrives its level, stats, path, skills (all of the path's skills at the slot's skill level), gear
//               (everything worn and carried is destroyed and the set made new: refine = the vnum, stones, the seven
//               bonus lines incl. 6/7, costumes, sash, talisman, gloves, alchemy deck 1 when the set has stones),
//               potions, alignment 0, full HP/SP;
//   waiting   - everybody in (or failed): they stand on their spots, buff, are kept whole and strike nobody;
//   countdown - "/pvpfan gotowi <kod>": countdown_sec notices on the arena map, then
//   fighting  - each bot fights the other teams' bots only (PvpFanAttackable, server-patches/pvpfan battle.cpp: a
//               team's members never hit each other, nobody else hits them and they hit nobody else - people only
//               with allow_players), kingdom, guild, party and PK mode do not matter; a target is picked by distance
//               and how many already fight it, the fight is the duel's and the guild war's (buffs, gap closers,
//               casters from range, archers from 800, potions per potions); a bot that strays past arena_radius walks
//               back; the fallen stay down (their dead event is cancelled - no restart, no experience lost) and a
//               death is no murder (PvpFanDeath, char_battle.cpp: no alignment, no dropped item). When at most one
//               team stands - or after max_minutes, the team with more standing (then more kills) - the result goes
//               to everybody (BroadcastNotice) and to player.pvpfan_war / _war_team (the panel's history);
//   finished  - exit_sec later the fallen stand up and everybody logs off, staggered; the category is idle again.
//   "/pvpfan stop <kod>" ends any phase the same way, without a result.
// A core restarted in the middle sets its categories back to idle at its first poll.
//
// Commands (GM_HIGH_WIZARD, cmd.cpp "pvpfan"): /pvpfan [lista] | start <kod> | gotowi <kod> (ready) | stop <kod> |
// status <kod> | tu <kod> [druzyna] (here: the arena centre or a team's point from the GM's position) | pozycja (the
// GM's position for the panel's hint).
//
// Switches: env M2_PVPFAN (1 by default; 0 = the module does nothing, the hooks answer "not mine"), the event flag
// m2_pvpfan_off (game flag or the player.quest row the panel writes - no new war, running ones stopped), caps
// M2_PVPFAN_MAX_CATEGORY (500) and M2_PVPFAN_MAX_TOTAL (1000, per core), M2_PVPFAN_SPAWN_PER_SEC (20). Logs:
// "PVPFAN:" lines, a census a minute while a war runs.
//
// An implementation fragment in the sense playerbot_types.h describes: included once, after playerbot_petmat.h.
#include <unordered_map>
#include <cmath>

int PvpFanAttackable(LPCHARACTER ch, LPCHARACTER victim);
bool PvpFanDeath(LPCHARACTER victim, LPCHARACTER killer);
void PlayerBotPvpFanCommand(LPCHARACTER ch, const char* argument);

namespace
{
	const DWORD PVPFAN_TICK_MS = 250;
	const DWORD PVPFAN_COMMAND_POLL_MS = 3000;
	const DWORD PVPFAN_FLAG_POLL_MS = 10000;
	const DWORD PVPFAN_CENSUS_MS = 60000;
	const DWORD PVPFAN_LOAD_TIMEOUT_MS = 45000;
	const DWORD PVPFAN_START_TIMEOUT_MS = 4 * 60 * 1000;
	// MT2009_PLUS_PVPFAN_TIME_FIX_V1 (the first test, 7 November 2026): the tick's dwNow is read before the queue's
	// command sets stateAt with a later get_dword_time(), so dwNow - stateAt wrapped round to ~4 billion and a war
	// stopped "after 4 minutes" in its first second. Every elapsed time here: 0 while the mark is still ahead.
	inline DWORD PvpFanSince(DWORD dwNow, DWORD at)
	{
		return (int)(dwNow - at) > 0 ? dwNow - at : 0;
	}
	const DWORD PVPFAN_WAIT_TIMEOUT_MS = 45 * 60 * 1000;
	const DWORD PVPFAN_RETARGET_MS = 1500;
	const DWORD PVPFAN_STATE_WRITE_MS = 5000;
	const int PVPFAN_EXIT_PER_TICK = 25;
	const int PVPFAN_SPACING = 140;
	const int PVPFAN_ROW = 10;
	const int PVPFAN_MAX_TEAMS = 8;

	enum EPvpFanState
	{
		PVPFAN_IDLE = 0,
		PVPFAN_STARTING,
		PVPFAN_WAITING,
		PVPFAN_COUNTDOWN,
		PVPFAN_FIGHTING,
		PVPFAN_FINISHED,
		PVPFAN_STOPPING,
	};

	enum EPvpFanPhase
	{
		PVPFAN_F_QUEUED = 0,
		PVPFAN_F_LOADING,
		PVPFAN_F_LOADED,
		PVPFAN_F_READY,
		PVPFAN_F_FAILED,
		PVPFAN_F_OUT,
	};

	const char* PvpFanStateCode(int s)
	{
		switch (s)
		{
			case PVPFAN_STARTING: return "starting";
			case PVPFAN_WAITING: return "waiting";
			case PVPFAN_COUNTDOWN: return "countdown";
			case PVPFAN_FIGHTING: return "fighting";
			case PVPFAN_FINISHED: return "finished";
			case PVPFAN_STOPPING: return "stopping";
			default: return "idle";
		}
	}

	const char* PvpFanStateText(int s)
	{
		switch (s)
		{
			case PVPFAN_STARTING: return "boty wchodza";
			case PVPFAN_WAITING: return "czekaja na sygnal";
			case PVPFAN_COUNTDOWN: return "odliczanie";
			case PVPFAN_FIGHTING: return "walka";
			case PVPFAN_FINISHED: return "koniec, boty wychodza";
			case PVPFAN_STOPPING: return "zatrzymywanie";
			default: return "bezczynna";
		}
	}

	struct TPvpFanItem
	{
		std::string slot;
		DWORD vnum = 0;
		int count = 1;
		long socket[3] = { 0, 0, 0 };
		WORD attrType[7] = { 0, 0, 0, 0, 0, 0, 0 };
		short attrValue[7] = { 0, 0, 0, 0, 0, 0, 0 };
	};

	struct TPvpFanSet
	{
		DWORD id = 0;
		std::string presetKey;
		DWORD redVnum = 27003, blueVnum = 27006;
		int redCount = 400, blueCount = 400;
		std::vector<TPvpFanItem> items;
	};

	struct TPvpFanFighter
	{
		DWORD pid = 0, accountId = 0;
		std::string login, name;
		BYTE empire = 1;
		int team = 0;
		DWORD slotId = 0;
		BYTE job = 0, group = 1;
		int level = 120;
		BYTE skillLevel = 40;
		int st = 0, ht = 0, dx = 0, iq = 0;
		DWORD setId = 0;
		long x = 0, y = 0;
		// runtime
		BYTE phase = PVPFAN_F_QUEUED;
		DWORD askedAt = 0;
		int tries = 0;
		bool dead = false;
		DWORD deadAt = 0;
		unsigned int kills = 0;
		DWORD retargetAt = 0;
		DWORD targetPid = 0;
		long lastX = 0, lastY = 0;
		DWORD equipRetryAt = 0;		// MT2009_PLUS_PVPFAN_EQUIP_RETRY_V1
		int equipRetries = 0;
	};

	struct TPvpFanTeam
	{
		DWORD id = 0;
		int idx = 0;
		std::string name;
		BYTE empire = 1;
		long x = 0, y = 0;
		unsigned int fighters = 0, ready = 0, alive = 0, kills = 0, deaths = 0;
	};

	struct TPvpFanWar
	{
		DWORD catId = 0;
		std::string code, name;
		long map = 0, cx = 0, cy = 0, radius = 1500, arenaRadius = 5000;
		BYTE channel = 1;
		int countdown = 5, maxMinutes = 15, exitSec = 20;
		bool allowPlayers = false, potions = true;
		int state = PVPFAN_IDLE;
		DWORD stateAt = 0;
		DWORD warRowId = 0;
		std::string startedBy;
		std::vector<TPvpFanTeam> teams;
		std::vector<TPvpFanFighter> fighters;
		std::map<DWORD, TPvpFanSet> sets;
		DWORD countdownEnd = 0;
		int countdownSaid = -1;
		DWORD fightAt = 0;
		DWORD nextEval = 0;
		DWORD nextStateWrite = 0;
		bool firstBlood = false;
		std::string result;
		// The targets' crowd, refreshed every evaluation: pid -> how many fight it.
		std::unordered_map<DWORD, int> crowd;
	};

	std::map<DWORD, TPvpFanWar> s_mapPvpFanWars;
	// Every fighter of a war on this core, pid -> (category, index into its war's fighters).
	std::unordered_map<DWORD, std::pair<DWORD, size_t> > s_mapPvpFanPid;
	DWORD s_dwPvpFanLastTick = 0;
	DWORD s_dwPvpFanNextPoll = 0;
	DWORD s_dwPvpFanNextFlagPoll = 0;
	DWORD s_dwPvpFanNextCensus = 0;
	bool s_bPvpFanDbFlagOff = false;
	bool s_bPvpFanRecovered = false;
	bool s_bPvpFanTablesMissing = false;

	// ------------------------------------------------------------------ switches

	int GetPvpFanEnvInt(const char* name, int fallback, int low, int high)
	{
		const char* v = std::getenv(name);
		if (!v || !*v)
			return fallback;
		return MINMAX(low, std::atoi(v), high);
	}

	bool IsPlayerBotPvpFanEnabled()
	{
		static int s_iOn = -1;
		if (s_iOn < 0)
		{
			s_iOn = GetPvpFanEnvInt("M2_PVPFAN", 1, 0, 1);
			sys_log(0, "PVPFAN: config on=%d max_category=%d max_total=%d spawn_per_sec=%d", s_iOn,
					GetPvpFanEnvInt("M2_PVPFAN_MAX_CATEGORY", 500, 2, 1000),
					GetPvpFanEnvInt("M2_PVPFAN_MAX_TOTAL", 1000, 2, 3000),
					GetPvpFanEnvInt("M2_PVPFAN_SPAWN_PER_SEC", 20, 1, 100));
		}
		return s_iOn != 0;
	}

	bool IsPlayerBotPvpFanFlagOff()
	{
		return s_bPvpFanDbFlagOff || quest::CQuestManager::instance().GetEventFlag("m2_pvpfan_off") != 0;
	}

	int GetPvpFanMaxCategory() { return GetPvpFanEnvInt("M2_PVPFAN_MAX_CATEGORY", 500, 2, 1000); }
	int GetPvpFanMaxTotal() { return GetPvpFanEnvInt("M2_PVPFAN_MAX_TOTAL", 1000, 2, 3000); }
	int GetPvpFanSpawnPerSec() { return GetPvpFanEnvInt("M2_PVPFAN_SPAWN_PER_SEC", 20, 1, 100); }

	// ------------------------------------------------------------------ lookups

	bool IsPlayerBotPvpFanPID(DWORD pid)
	{
		return !s_mapPvpFanPid.empty() && s_mapPvpFanPid.find(pid) != s_mapPvpFanPid.end();
	}

	TPvpFanFighter* FindPlayerBotPvpFanFighter(DWORD pid, TPvpFanWar** outWar)
	{
		if (s_mapPvpFanPid.empty())
			return NULL;
		std::unordered_map<DWORD, std::pair<DWORD, size_t> >::iterator it = s_mapPvpFanPid.find(pid);
		if (it == s_mapPvpFanPid.end())
			return NULL;
		std::map<DWORD, TPvpFanWar>::iterator w = s_mapPvpFanWars.find(it->second.first);
		if (w == s_mapPvpFanWars.end() || it->second.second >= w->second.fighters.size())
			return NULL;
		if (outWar)
			*outWar = &w->second;
		return &w->second.fighters[it->second.second];
	}

	size_t CountPlayerBotPvpFanFighters()
	{
		return s_mapPvpFanPid.size();
	}

	// ------------------------------------------------------------------ database

	std::unique_ptr<SQLMsg> PvpFanQuery(const char* fmt, ...)
	{
		char buf[4096];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		return std::unique_ptr<SQLMsg>(DBManager::instance().DirectQuery("%s", buf));
	}

	bool PvpFanOk(const std::unique_ptr<SQLMsg>& m)
	{
		return m.get() && m->uiSQLErrno == 0 && m->Get();
	}

	void PvpFanExec(const char* fmt, ...)
	{
		char buf[4096];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		DBManager::instance().Query("%s", buf);
	}

	std::string PvpFanEscape(const std::string& s)
	{
		std::vector<char> out(s.size() * 2 + 1);
		DBManager::instance().EscapeString(&out[0], out.size(), s.c_str(), s.size());
		return std::string(&out[0]);
	}

	long PvpFanLong(const char* v)
	{
		return v ? std::atol(v) : 0;
	}

	std::string PvpFanCoreName()
	{
		char buf[32];
		snprintf(buf, sizeof(buf), "ch%u:%u", (unsigned int)g_bChannel, (unsigned int)mother_port);
		return buf;
	}

	void WritePlayerBotPvpFanState(TPvpFanWar& war, const std::string& note)
	{
		unsigned int online = 0;
		std::string alive;
		for (size_t i = 0; i < war.teams.size(); ++i)
		{
			char part[96];
			snprintf(part, sizeof(part), "%s%s %u/%u", i ? " | " : "", war.teams[i].name.c_str(),
					war.state == PVPFAN_FIGHTING || war.state == PVPFAN_FINISHED ? war.teams[i].alive : war.teams[i].ready,
					war.teams[i].fighters);
			alive += part;
		}
		for (size_t i = 0; i < war.fighters.size(); ++i)
			if (war.fighters[i].phase == PVPFAN_F_READY || war.fighters[i].phase == PVPFAN_F_LOADED)
				++online;
		PvpFanExec("UPDATE player.pvpfan_category SET state='%s', state_note='%s', state_at=NOW(), core='%s', online=%u, "
				"alive_text='%s' WHERE id=%u", PvpFanStateCode(war.state), PvpFanEscape(note.substr(0, 250)).c_str(),
				PvpFanCoreName().c_str(), online, PvpFanEscape(alive.substr(0, 250)).c_str(), war.catId);
		war.nextStateWrite = get_dword_time() + PVPFAN_STATE_WRITE_MS;
	}

	void SetPlayerBotPvpFanState(TPvpFanWar& war, int state, const std::string& note)
	{
		war.state = state;
		war.stateAt = get_dword_time();
		WritePlayerBotPvpFanState(war, note);
		sys_log(0, "PVPFAN: category=%u code=%s state=%s note=%s", war.catId, war.code.c_str(), PvpFanStateCode(state),
				note.c_str());
	}

	// ------------------------------------------------------------------ the roster

	std::string PlayerBotPvpFanPresetKey(BYTE job, BYTE group)
	{
		static const char* const keys[4] = { "w", "n", "s", "sh" };
		char buf[8];
		snprintf(buf, sizeof(buf), "%s%u", keys[job % 4], (unsigned int)(group == 2 ? 2 : 1));
		return buf;
	}

	bool LoadPlayerBotPvpFanSets(TPvpFanWar& war, std::string& err)
	{
		std::set<DWORD> ids;
		std::set<std::string> presets;
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			if (war.fighters[i].setId)
				ids.insert(war.fighters[i].setId);
			else
				presets.insert(PlayerBotPvpFanPresetKey(war.fighters[i].job, war.fighters[i].group));
		}
		std::string where;
		for (std::set<DWORD>::iterator it = ids.begin(); it != ids.end(); ++it)
		{
			char part[24];
			snprintf(part, sizeof(part), "%s%u", where.empty() ? "" : ",", *it);
			where += part;
		}
		std::string presetWhere;
		for (std::set<std::string>::iterator it = presets.begin(); it != presets.end(); ++it)
			presetWhere += (presetWhere.empty() ? "'" : ",'") + *it + "'";
		if (where.empty() && presetWhere.empty())
			return true;
		std::string q = "SELECT id, preset_key, red_vnum, red_count, blue_vnum, blue_count FROM player.pvpfan_set WHERE ";
		if (!where.empty())
			q += "id IN (" + where + ")";
		if (!presetWhere.empty())
			q += std::string(where.empty() ? "" : " OR ") + "preset_key IN (" + presetWhere + ")";
		q += " ORDER BY id";
		std::unique_ptr<SQLMsg> msg = PvpFanQuery("%s", q.c_str());
		if (!PvpFanOk(msg))
		{
			err = "nie mozna odczytac zestawow (player.pvpfan_set)";
			return false;
		}
		std::map<std::string, DWORD> presetIds;
		MYSQL_ROW row;
		if (msg->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				TPvpFanSet set;
				set.id = (DWORD)PvpFanLong(row[0]);
				set.presetKey = row[1] ? row[1] : "";
				set.redVnum = (DWORD)PvpFanLong(row[2]);
				set.redCount = (int)PvpFanLong(row[3]);
				set.blueVnum = (DWORD)PvpFanLong(row[4]);
				set.blueCount = (int)PvpFanLong(row[5]);
				if (!set.presetKey.empty() && presetIds.find(set.presetKey) == presetIds.end())
					presetIds[set.presetKey] = set.id;
				war.sets[set.id] = set;
			}
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			if (f.setId == 0)
			{
				std::map<std::string, DWORD>::iterator p = presetIds.find(PlayerBotPvpFanPresetKey(f.job, f.group));
				f.setId = p != presetIds.end() ? p->second : 0;
			}
			else if (war.sets.find(f.setId) == war.sets.end())
				f.setId = 0;
		}
		if (war.sets.empty())
			return true;
		std::string all;
		for (std::map<DWORD, TPvpFanSet>::iterator it = war.sets.begin(); it != war.sets.end(); ++it)
		{
			char part[24];
			snprintf(part, sizeof(part), "%s%u", all.empty() ? "" : ",", it->first);
			all += part;
		}
		std::unique_ptr<SQLMsg> items = PvpFanQuery(
				"SELECT set_id, slot, vnum, count, socket0, socket1, socket2, attrtype0, attrvalue0, attrtype1, attrvalue1, "
				"attrtype2, attrvalue2, attrtype3, attrvalue3, attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6 "
				"FROM player.pvpfan_set_item WHERE set_id IN (%s) AND vnum > 0 ORDER BY set_id, id", all.c_str());
		if (!PvpFanOk(items))
		{
			err = "nie mozna odczytac przedmiotow zestawow (player.pvpfan_set_item)";
			return false;
		}
		if (items->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(items->Get()->pSQLResult)))
			{
				std::map<DWORD, TPvpFanSet>::iterator set = war.sets.find((DWORD)PvpFanLong(row[0]));
				if (set == war.sets.end())
					continue;
				TPvpFanItem item;
				item.slot = row[1] ? row[1] : "";
				item.vnum = (DWORD)PvpFanLong(row[2]);
				item.count = MINMAX(1, (int)PvpFanLong(row[3]), 200);
				for (int s = 0; s < 3; ++s)
					item.socket[s] = PvpFanLong(row[4 + s]);
				for (int a = 0; a < 7; ++a)
				{
					item.attrType[a] = (WORD)PvpFanLong(row[7 + a * 2]);
					item.attrValue[a] = (short)PvpFanLong(row[8 + a * 2]);
				}
				set->second.items.push_back(item);
			}
		return true;
	}

	// The fighters' spots: each team's point (its own, or on a circle round the centre), rows of PVPFAN_ROW facing the
	// centre PVPFAN_SPACING apart, each on open ground near its place.
	void PlacePlayerBotPvpFanSpots(TPvpFanWar& war)
	{
		const size_t n = war.teams.size();
		for (size_t t = 0; t < n; ++t)
		{
			TPvpFanTeam& team = war.teams[t];
			if (team.x == 0 || team.y == 0)
			{
				const double angle = 3.14159265358979 + 2.0 * 3.14159265358979 * (double)t / (double)std::max<size_t>(n, 1);
				team.x = war.cx + (long)(cos(angle) * war.radius);
				team.y = war.cy + (long)(sin(angle) * war.radius);
			}
			long gx = team.x, gy = team.y;
			if (FindPlayerBotWarGround(war.map, team.x, team.y, 1500, gx, gy))
			{
				team.x = gx;
				team.y = gy;
			}
		}
		std::vector<int> seen(n, 0);
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			const TPvpFanTeam& team = war.teams[f.team];
			const int j = seen[f.team]++;
			double dxc = (double)(war.cx - team.x), dyc = (double)(war.cy - team.y);
			double len = sqrt(dxc * dxc + dyc * dyc);
			if (len < 1.0)
			{
				dxc = 1.0;
				dyc = 0.0;
				len = 1.0;
			}
			dxc /= len;
			dyc /= len;
			const double col = (double)(j % PVPFAN_ROW) - (PVPFAN_ROW - 1) / 2.0;
			const double rowBack = (double)(j / PVPFAN_ROW);
			const long sx = team.x + (long)(-dyc * col * PVPFAN_SPACING - dxc * rowBack * PVPFAN_SPACING);
			const long sy = team.y + (long)(dxc * col * PVPFAN_SPACING - dyc * rowBack * PVPFAN_SPACING);
			long ox = sx, oy = sy;
			if (FindPlayerBotWarGround(war.map, sx, sy, 600, ox, oy))
			{
				f.x = ox;
				f.y = oy;
			}
			else
			{
				f.x = team.x;
				f.y = team.y;
			}
		}
	}

	bool LoadPlayerBotPvpFanWar(DWORD catId, TPvpFanWar& war, std::string& err)
	{
		std::unique_ptr<SQLMsg> cat = PvpFanQuery(
				"SELECT id, code, name, enabled, map_index, x, y, radius, arena_radius, channel, countdown_sec, max_minutes, "
				"exit_sec, allow_players, potions FROM player.pvpfan_category WHERE id=%u", catId);
		MYSQL_ROW row;
		if (!PvpFanOk(cat) || !cat->Get()->pSQLResult || !(row = mysql_fetch_row(cat->Get()->pSQLResult)))
		{
			err = "nie ma takiej kategorii";
			return false;
		}
		war.catId = (DWORD)PvpFanLong(row[0]);
		war.code = row[1] ? row[1] : "";
		war.name = row[2] && *row[2] ? row[2] : war.code;
		if (PvpFanLong(row[3]) == 0)
		{
			err = "kategoria jest wylaczona w panelu";
			return false;
		}
		war.map = PvpFanLong(row[4]);
		war.cx = PvpFanLong(row[5]);
		war.cy = PvpFanLong(row[6]);
		war.radius = MINMAX(200L, PvpFanLong(row[7]), 20000L);
		war.arenaRadius = MINMAX(1000L, PvpFanLong(row[8]), 50000L);
		war.channel = (BYTE)PvpFanLong(row[9]);
		war.countdown = MINMAX(0, (int)PvpFanLong(row[10]), 60);
		war.maxMinutes = MINMAX(1, (int)PvpFanLong(row[11]), 180);
		war.exitSec = MINMAX(0, (int)PvpFanLong(row[12]), 600);
		war.allowPlayers = PvpFanLong(row[13]) != 0;
		war.potions = PvpFanLong(row[14]) != 0;
		if (war.map <= 0 || war.cx <= 0 || war.cy <= 0)
		{
			err = "arena nie jest ustawiona (mapa i x,y w panelu albo /pvpfan tu)";
			return false;
		}
		if (!map_allow_find(war.map))
		{
			err = "ten rdzen nie obsluguje mapy areny";
			return false;
		}
		if (war.arenaRadius < war.radius + 1000)
			war.arenaRadius = war.radius + 1000;

		std::unique_ptr<SQLMsg> teams = PvpFanQuery(
				"SELECT id, idx, name, empire, x, y FROM player.pvpfan_team WHERE category_id=%u ORDER BY idx, id LIMIT %d",
				catId, PVPFAN_MAX_TEAMS);
		if (!PvpFanOk(teams) || !teams->Get()->pSQLResult)
		{
			err = "nie mozna odczytac druzyn";
			return false;
		}
		std::map<DWORD, int> teamIndex;
		while (NULL != (row = mysql_fetch_row(teams->Get()->pSQLResult)))
		{
			TPvpFanTeam team;
			team.id = (DWORD)PvpFanLong(row[0]);
			team.idx = (int)war.teams.size();
			team.name = row[2] && *row[2] ? row[2] : "Druzyna";
			const long empire = PvpFanLong(row[3]);
			team.empire = (BYTE)(empire >= 1 && empire <= 3 ? empire : (team.idx % 3 == 0 ? 1 : (team.idx % 3 == 1 ? 3 : 2)));
			team.x = PvpFanLong(row[4]);
			team.y = PvpFanLong(row[5]);
			teamIndex[team.id] = team.idx;
			war.teams.push_back(team);
		}
		if (war.teams.size() < 2)
		{
			err = "kategoria musi miec co najmniej 2 druzyny";
			return false;
		}

		std::unique_ptr<SQLMsg> chars = PvpFanQuery(
				"SELECT c.pid, c.account_id, a.login, p.name, c.team_id, c.slot_id, s.job, s.skill_group, s.level, s.skill_level, "
				"s.st, s.ht, s.dx, s.iq, s.set_id, IFNULL(pi.empire,0), p.job "
				"FROM player.pvpfan_char c JOIN player.pvpfan_slot s ON s.id=c.slot_id "
				"JOIN player.player p ON p.id=c.pid JOIN account.account a ON a.id=c.account_id AND a.id=p.account_id "
				"LEFT JOIN player.player_index pi ON pi.id=c.account_id "
				"WHERE c.category_id=%u AND c.retired=0 ORDER BY c.team_id, s.sort, c.slot_id, c.seq", catId);
		if (!PvpFanOk(chars) || !chars->Get()->pSQLResult)
		{
			err = "nie mozna odczytac postaci (player.pvpfan_char)";
			return false;
		}
		const int maxCat = GetPvpFanMaxCategory();
		const int maxTotal = GetPvpFanMaxTotal() - (int)CountPlayerBotPvpFanFighters();
		int skipped = 0;
		while (NULL != (row = mysql_fetch_row(chars->Get()->pSQLResult)))
		{
			TPvpFanFighter f;
			f.pid = (DWORD)PvpFanLong(row[0]);
			f.accountId = (DWORD)PvpFanLong(row[1]);
			f.login = row[2] ? row[2] : "";
			f.name = row[3] ? row[3] : "";
			std::map<DWORD, int>::iterator team = teamIndex.find((DWORD)PvpFanLong(row[4]));
			// Only the panel's own identities: an account playerbot_pf..., never a person's character.
			if (team == teamIndex.end() || f.pid == 0 || f.login.compare(0, 12, "playerbot_pf") != 0 ||
					(int)PvpFanLong(row[16]) % 4 != (int)PvpFanLong(row[6]) % 4)
			{
				++skipped;
				continue;
			}
			if ((int)war.fighters.size() >= maxCat || (int)war.fighters.size() >= maxTotal)
			{
				++skipped;
				continue;
			}
			f.team = team->second;
			f.slotId = (DWORD)PvpFanLong(row[5]);
			f.job = (BYTE)(PvpFanLong(row[6]) % 4);
			f.group = (BYTE)(PvpFanLong(row[7]) == 2 ? 2 : 1);
			f.level = MINMAX(1, (int)PvpFanLong(row[8]), gPlayerMaxLevel);
			f.skillLevel = (BYTE)MINMAX(0, (int)PvpFanLong(row[9]), 40);
			f.st = (int)PvpFanLong(row[10]);
			f.ht = (int)PvpFanLong(row[11]);
			f.dx = (int)PvpFanLong(row[12]);
			f.iq = (int)PvpFanLong(row[13]);
			f.setId = (DWORD)PvpFanLong(row[14]);
			const long empire = PvpFanLong(row[15]);
			f.empire = (BYTE)(empire >= 1 && empire <= 3 ? empire : war.teams[f.team].empire);
			if (s_mapPvpFanPid.find(f.pid) != s_mapPvpFanPid.end())
			{
				++skipped;
				continue;
			}
			++war.teams[f.team].fighters;
			war.fighters.push_back(f);
		}
		int teamsWithFighters = 0;
		for (size_t t = 0; t < war.teams.size(); ++t)
			if (war.teams[t].fighters > 0)
				++teamsWithFighters;
		if (teamsWithFighters < 2)
		{
			err = "za malo postaci - wygeneruj postacie w panelu (Generuj postacie)";
			return false;
		}
		if (skipped)
			sys_log(0, "PVPFAN: category=%u skipped %d character(s) (caps %d/%d, foreign or busy rows)", catId, skipped,
					maxCat, GetPvpFanMaxTotal());
		if (!LoadPlayerBotPvpFanSets(war, err))
			return false;
		PlacePlayerBotPvpFanSpots(war);
		return true;
	}

	// ------------------------------------------------------------------ the loadout

	void ClearPlayerBotPvpFanBelongings(LPCHARACTER ch)
	{
		for (int wear = 0; wear < WEAR_MAX_NUM; ++wear)
		{
			LPITEM worn = ch->GetWear(wear);
			if (worn)
				ITEM_MANAGER::instance().RemoveItem(worn, "PVPFAN_RESET");
		}
		for (int cell = DRAGON_SOUL_EQUIP_SLOT_START; cell < DRAGON_SOUL_EQUIP_SLOT_END; ++cell)
		{
			LPITEM ds = ch->GetInventoryItem(cell);
			if (ds)
				ITEM_MANAGER::instance().RemoveItem(ds, "PVPFAN_RESET");
		}
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell)
				ITEM_MANAGER::instance().RemoveItem(item, "PVPFAN_RESET");
		}
	}

	void GetPlayerBotPvpFanPresetStats(BYTE job, BYTE group, int& st, int& ht, int& dx, int& iq)
	{
		switch (job)
		{
			case JOB_WARRIOR:
				st = 90; ht = 90; dx = group == 2 ? 46 : 60; iq = group == 2 ? 60 : 46;
				break;
			case JOB_ASSASSIN:
				dx = 90; st = group == 2 ? 70 : 90; ht = group == 2 ? 80 : 60; iq = 46;
				break;
			case JOB_SURA:
				if (group == 2) { iq = 90; ht = 90; st = 60; dx = 46; }
				else { st = 90; iq = 70; ht = 80; dx = 46; }
				break;
			default:
				iq = 90; ht = 90; dx = 60; st = 46;
				break;
		}
	}

	int GetPlayerBotPvpFanEquipCell(const std::string& slot)
	{
		if (slot == "ring1") return WEAR_UNIQUE1;
		if (slot == "ring2") return WEAR_UNIQUE2;
		if (slot == "arrow") return WEAR_ARROW;
		return -1;
	}

	// MT2009_PLUS_PVPFAN_EQUIP_RETRY_V1 (the first test, 7 November 2026: 20 of 20 bots stood with items=11 worn=0 -
	// the gear went into the bag right after the load and EquipItem refused it): while the bot waits for the signal its
	// set's pieces still in the bag are put on again every 2 s (up to 30 tries); a refusal says why once.
	int RetryPlayerBotPvpFanEquip(LPCHARACTER ch, const TPvpFanWar& war, TPvpFanFighter& f, bool logWhy)
	{
		std::map<DWORD, TPvpFanSet>::const_iterator set = war.sets.find(f.setId);
		if (set == war.sets.end())
			return 0;
		int worn = 0;
		for (size_t i = 0; i < set->second.items.size(); ++i)
		{
			const TPvpFanItem& it = set->second.items[i];
			LPITEM item = NULL;
			for (int cell = 0; cell < ch->GetInventoryMaxCount() && !item; ++cell)
			{
				LPITEM c = ch->GetInventoryItem(cell);
				if (c && c->GetVnum() == it.vnum && !c->IsEquipped())
					item = c;
			}
			if (!item)
				continue;
			if (PlayerBotEquipItem(ch, item, GetPlayerBotPvpFanEquipCell(it.slot)) && item->IsEquipped())
				++worn;
			else if (logWhy)
				sys_log(0, "PVPFAN: wear refused pid=%u name=%s vnum=%u slot=%s level=%d stun=%d busy=%d equipable=%d can=%d "
						"dead=%d window=%u cell=%u", f.pid, ch->GetName(), it.vnum, it.slot.c_str(), ch->GetLevel(),
						ch->IsStun() ? 1 : 0, ch->IsBusy() ? 1 : 0, item->IsEquipable() ? 1 : 0,
						ch->CanEquipNow(item) ? 1 : 0, ch->IsDead() ? 1 : 0, (unsigned int)item->GetWindow(),
						(unsigned int)item->GetCell());
		}
		return worn;
	}

	void ApplyPlayerBotPvpFanLoadout(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f)
	{
		if (ch->IsRiding())
			ch->StopRiding();
		if (ch->GetHorse())
			ch->HorseSummon(false);
		// MT2009_PLUS_PVPFAN_V1: an arena bot a bot guild master once took in (the first test) leaves that guild
		if (CGuild* g = ch->GetGuild())
			g->RequestRemoveMember(ch->GetPlayerID());
		// The level and the stats - the way a stat reset and pc.set_level make a level.
		if (ch->GetLevel() != f.level)
		{
			ch->SetExp(0);
			ch->ResetPoint(f.level);
		}
		int st = f.st, ht = f.ht, dx = f.dx, iq = f.iq;
		if (st <= 0 || ht <= 0 || dx <= 0 || iq <= 0)
		{
			int pst = 0, pht = 0, pdx = 0, piq = 0;
			GetPlayerBotPvpFanPresetStats(f.job, f.group, pst, pht, pdx, piq);
			if (st <= 0) st = pst;
			if (ht <= 0) ht = pht;
			if (dx <= 0) dx = pdx;
			if (iq <= 0) iq = piq;
		}
		const int stats[4] = { MINMAX(1, st, 90), MINMAX(1, ht, 90), MINMAX(1, dx, 90), MINMAX(1, iq, 90) };
		const WORD points[4] = { POINT_ST, POINT_HT, POINT_DX, POINT_IQ };
		for (int i = 0; i < 4; ++i)
		{
			ch->SetRealPoint(points[i], stats[i]);
			ch->SetPoint(points[i], stats[i]);
		}
		if (ch->GetPoint(POINT_STAT) > 0)
			ch->PointChange(POINT_STAT, -ch->GetPoint(POINT_STAT));
		// The path and every skill of it at the slot's level.
		if (ch->GetJob() == f.job)
		{
			if (ch->GetSkillGroup() != f.group)
			{
				ch->ClearSkill();
				ch->SetSkillGroup(f.group);
			}
			const TJobSkillBuild build = GetPlayerBotSkillBuild(f.job, f.group, f.pid);
			for (int i = 0; i < build.bSkillCount && i < 6; ++i)
				if (build.dwSkills[i])
					ch->SetSkillLevel(build.dwSkills[i], f.skillLevel);
			ch->SkillLevelPacket();
		}
		else
			sys_err("PVPFAN: pid=%u name=%s is class %u, its slot says %u - no skills set (generate the characters again)",
					f.pid, ch->GetName(), (unsigned int)ch->GetJob(), (unsigned int)f.job);
		// The gear.
		std::map<DWORD, TPvpFanSet>::const_iterator set = war.sets.find(f.setId);
		int made = 0, worn = 0;
		if (set != war.sets.end())
		{
			ClearPlayerBotPvpFanBelongings(ch);
			bool anyDs = false;
			// The alchemy's qualification before a stone is worn (the deck is switched on after them).
			for (size_t i = 0; i < set->second.items.size(); ++i)
				if (set->second.items[i].slot.compare(0, 2, "ds") == 0)
				{
					ch->DragonSoul_GiveQualification();
					break;
				}
			for (size_t i = 0; i < set->second.items.size(); ++i)
			{
				const TPvpFanItem& it = set->second.items[i];
				LPITEM item = ITEM_MANAGER::instance().CreateItem(it.vnum, it.count, 0, false);
				if (!item)
				{
					sys_err("PVPFAN: set=%u slot=%s vnum=%u cannot be made", set->first, it.slot.c_str(), it.vnum);
					continue;
				}
				for (int s = 0; s < 3; ++s)
					if (it.socket[s] != 0)
						item->SetSocket(s, it.socket[s]);
				bool anyAttr = false;
				for (int a = 0; a < 7; ++a)
					if (it.attrType[a] != 0 && it.attrValue[a] != 0)
						anyAttr = true;
				if (anyAttr)
				{
					item->ClearAttribute();
					for (int a = 0; a < 7; ++a)
						if (it.attrType[a] != 0 && it.attrValue[a] != 0)
							item->SetForceAttribute(a, it.attrType[a], it.attrValue[a]);
				}
				ch->AutoGiveItem(item, false);
				++made;
				if (item->GetOwner() != ch)
					continue;
				if (item->IsDragonSoul())
					anyDs = true;
				if (PlayerBotEquipItem(ch, item, GetPlayerBotPvpFanEquipCell(it.slot)) && item->IsEquipped())
					++worn;
				else if (!item->IsDragonSoul() || !item->IsEquipped())
					PlayerBotLogThrottled("pvpfan_equip", get_dword_time(),
							"PVPFAN: pid=%u name=%s could not wear vnum=%u (%s) - wrong class, level or slot?", f.pid,
							ch->GetName(), it.vnum, it.slot.c_str());
			}
			if (anyDs)
				ch->DragonSoul_ActivateDeck(0);
			for (int left = set->second.redVnum ? set->second.redCount : 0; left > 0; left -= 200)
				ch->AutoGiveItem(set->second.redVnum, MIN(200, left), -1, false);
			for (int left = set->second.blueVnum ? set->second.blueCount : 0; left > 0; left -= 200)
				ch->AutoGiveItem(set->second.blueVnum, MIN(200, left), -1, false);
		}
		else
			PlayerBotLogThrottled("pvpfan_noset", get_dword_time(),
					"PVPFAN: pid=%u name=%s has no equipment set (slot set 0 and no preset %s) - keeps its own gear", f.pid,
					ch->GetName(), PlayerBotPvpFanPresetKey(f.job, f.group).c_str());
		if (ch->GetAlignment() != 0)
			ch->UpdateAlignment(-ch->GetAlignment());
		ch->ComputePoints();
		ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
		ch->PointsPacket();
		ch->Save();
		state.dwTargetVID = 0;
		sys_log(0, "PVPFAN: ready pid=%u name=%s team=%s level=%d job=%u group=%u skill=%u set=%u items=%d worn=%d hp=%d",
				f.pid, ch->GetName(), war.teams[f.team].name.c_str(), ch->GetLevel(), (unsigned int)f.job,
				(unsigned int)f.group, (unsigned int)f.skillLevel, f.setId, made, worn, ch->GetMaxHP());
	}

	// ------------------------------------------------------------------ the bots' tick

	bool PlacePlayerBotPvpFanAt(LPCHARACTER ch, TPlayerBotAIState& state, long x, long y, DWORD dwNow)
	{
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		ClearPlayerBotRoute(state, true);
		if (!ch->Show(ch->GetMapIndex(), x, y, 0))
			return false;
		ch->Stop();
		ch->SendMovePacket(FUNC_MOVE, 0, x, y, 0, dwNow);
		return true;
	}

	void HoldPlayerBotPvpFanAtSpot(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			DWORD dwNow)
	{
		state.dwTargetVID = 0;
		if (ch->GetVictim())
			ch->SetVictim(NULL);
		if (ch->IsRiding() && !IsPlayerBotOnStandingMount(ch))
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "pvpfan");
		const int dist = DISTANCE_APPROX(ch->GetX() - f.x, ch->GetY() - f.y);
		if (ch->GetMapIndex() == war.map && dist > 400)
		{
			if (dist > 2500)
				PlacePlayerBotPvpFanAt(ch, state, f.x, f.y, dwNow);
			else if (dwNow >= state.dwNextGuildWarMoveTime)
			{
				state.dwNextGuildWarMoveTime = dwNow + 2000;
				MovePlayerBot(ch, f.x, f.y, dwNow, 4, true, false);
			}
			return;
		}
		if (ch->IsStateMove() && dist <= 150)
			ch->Stop();
		// Whole and buffed while they wait: the fight starts from full.
		if (ch->GetHP() < ch->GetMaxHP())
			ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		if (ch->GetSP() < ch->GetMaxSP())
			ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
		if (war.state == PVPFAN_WAITING || war.state == PVPFAN_COUNTDOWN)
			if (ManagePlayerBotCombatBuffs(ch, state, dwNow, true))
				return;
		if (!ch->IsStateMove())
			ch->SetRotationToXY(war.cx, war.cy);
	}

	// The nearest enemy that is up, weighed by how many already fight it - so a crowd spreads over the enemy line.
	LPCHARACTER FindPlayerBotPvpFanFoe(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch)
	{
		long best = LONG_MAX;
		DWORD bestPid = 0;
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			const TPvpFanFighter& e = war.fighters[i];
			if (e.team == f.team || e.dead || e.phase != PVPFAN_F_READY)
				continue;
			const long d = DISTANCE_APPROX(e.lastX - ch->GetX(), e.lastY - ch->GetY());
			std::unordered_map<DWORD, int>::const_iterator c = war.crowd.find(e.pid);
			const long score = d + (c != war.crowd.end() ? c->second : 0) * 250 + (long)((e.pid ^ f.pid) % 97);
			if (score < best)
			{
				best = score;
				bestPid = e.pid;
			}
		}
		if (!bestPid)
			return NULL;
		LPCHARACTER foe = CHARACTER_MANAGER::instance().FindByPID(bestPid);
		return foe && !foe->IsDead() && foe->GetMapIndex() == ch->GetMapIndex() ? foe : NULL;
	}

	bool IsPlayerBotPvpFanFoeUp(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch, LPCHARACTER foe)
	{
		if (!foe || foe->IsDead() || foe->GetHP() <= 0 || !foe->IsPC() || foe->GetMapIndex() != ch->GetMapIndex())
			return false;
		TPvpFanWar* fw = NULL;
		TPvpFanFighter* e = FindPlayerBotPvpFanFighter(foe->GetPlayerID(), &fw);
		return e && fw == &war && e->team != f.team && !e->dead;
	}

	void FightPlayerBotPvpFan(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f, DWORD dwNow)
	{
		if (ch->IsRiding() && !IsPlayerBotOnStandingMount(ch))
		{
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "pvpfan");
			if (ch->GetHorse())
				ch->HorseSummon(false);
			return;
		}
		if (war.potions)
		{
			UseHealthPotion(ch, state, dwNow, 55);
			UseManaPotion(ch, state, dwNow, 30);
		}
		// The arena's leash: a bot past it walks back to the centre and lets its foe go.
		const int fromCentre = DISTANCE_APPROX(ch->GetX() - war.cx, ch->GetY() - war.cy);
		if (fromCentre > war.arenaRadius)
		{
			state.dwTargetVID = 0;
			f.targetPid = 0;
			ch->SetVictim(NULL);
			if (fromCentre > war.arenaRadius * 2)
				PlacePlayerBotPvpFanAt(ch, state, f.x, f.y, dwNow);
			else if (dwNow >= state.dwNextGuildWarMoveTime)
			{
				state.dwNextGuildWarMoveTime = dwNow + 2000;
				MovePlayerBot(ch, war.cx, war.cy, dwNow, 8, true, false);
			}
			return;
		}
		LPCHARACTER foe = NULL;
		if (state.dwTargetVID != 0)
		{
			LPCHARACTER held = CHARACTER_MANAGER::instance().Find(state.dwTargetVID);
			if (IsPlayerBotPvpFanFoeUp(war, f, ch, held))
				foe = held;
		}
		if (!foe || dwNow >= f.retargetAt)
		{
			f.retargetAt = dwNow + PVPFAN_RETARGET_MS + f.pid % 700;
			LPCHARACTER chosen = FindPlayerBotPvpFanFoe(war, f, ch);
			if (chosen && (!foe || DISTANCE_APPROX(chosen->GetX() - ch->GetX(), chosen->GetY() - ch->GetY()) + 300 <
					DISTANCE_APPROX(foe->GetX() - ch->GetX(), foe->GetY() - ch->GetY())))
				foe = chosen;
		}
		if (!foe)
		{
			state.dwTargetVID = 0;
			f.targetPid = 0;
			if (ch->GetVictim())
				ch->SetVictim(NULL);
			if (ch->IsStateMove())
				ch->Stop();
			return;
		}
		const int distance = DISTANCE_APPROX(ch->GetX() - foe->GetX(), ch->GetY() - foe->GetY());
		state.dwTargetVID = (DWORD)foe->GetVID();
		f.targetPid = foe->GetPlayerID();
		ch->SetVictim(foe);
		ch->SetRotationToXY(foe->GetX(), foe->GetY());
		SetPlayerBotAction(state, BOT_ACTION_FIGHT, dwNow);
		// The fight a duel and a guild war are: the aura first, a caster from its range, a warrior across the gap, a
		// blade from where it reaches, the bow from 800.
		if (distance <= PLAYERBOT_DUEL_BUFF_RANGE && ManagePlayerBotCombatBuffs(ch, state, dwNow, true))
			return;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		const bool isBow = weapon && weapon->GetType() == ITEM_WEAPON && weapon->GetSubType() == WEAPON_BOW;
		const int combatRange = isBow ? 800 : PLAYERBOT_DUEL_MELEE_RANGE;
		const bool caster = ch->GetJob() == JOB_SHAMAN || (ch->GetJob() == JOB_SURA && ch->GetSkillGroup() == 2);
		if (distance > combatRange)
		{
			if (!isBow && caster && distance <= PLAYERBOT_DUEL_CASTER_RANGE && dwNow >= state.dwNextSkillCastTime)
			{
				if (ch->IsStateMove())
					ch->Stop();
				if (CastPlayerBotDuelSkill(ch, foe, state, dwNow))
					return;
			}
			if (!isBow && distance <= PLAYERBOT_SEARCH_RANGE && TryPlayerBotDuelGapCloser(ch, foe, state, dwNow, distance))
				return;
			if (dwNow >= state.dwNextGuildWarMoveTime)
			{
				state.dwNextGuildWarMoveTime = dwNow + 700;
				MovePlayerBot(ch, foe->GetX(), foe->GetY(), dwNow, 4, false, false);
			}
			return;
		}
		if (ch->IsStateMove())
			ch->Stop();
		ch->SetPosition(POS_FIGHTING);
		if (!CastPlayerBotDuelSkill(ch, foe, state, dwNow))
			ExecutePlayerBotBasicAttack(ch, foe, state, dwNow);
	}

	// Every tick of a bot of a war on this core - the whole of it: nothing of the population's AI runs for it.
	bool ManagePlayerBotPvpFanBot(LPDESC d, LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_mapPvpFanPid.empty() || !ch)
			return false;
		TPvpFanWar* war = NULL;
		TPvpFanFighter* f = FindPlayerBotPvpFanFighter(ch->GetPlayerID(), &war);
		if (!f)
			return false;
		if (!d || !d->IsPhase(PHASE_GAME))
			return true;
		if (ch->IsDead())
		{
			// Down for the rest of the war: no restart, no penalty (the dead event is what restarts a character).
			// (Counted as fallen by PvpFanDeath and the war's evaluation, not here.)
			// The war's exit stands it up before it logs off (ExitPlayerBotPvpFanFighters).
			if (ch->m_pkDeadEvent)
				event_cancel(&ch->m_pkDeadEvent);
			state.dwTargetVID = 0;
			return true;
		}
		if (ch->GetHP() <= 0)
		{
			if (ch->IsStateMove())
				ch->Stop();
			return true;
		}
		if (f->phase == PVPFAN_F_LOADED)
		{
			if (!ch->IsItemLoaded())
				return true;
			ApplyPlayerBotPvpFanLoadout(ch, state, *war, *f);
			if (ch->GetMapIndex() == war->map)
				PlacePlayerBotPvpFanAt(ch, state, f->x, f->y, dwNow);
			f->phase = PVPFAN_F_READY;
			f->lastX = ch->GetX();
			f->lastY = ch->GetY();
			return true;
		}
		if (f->phase != PVPFAN_F_READY)
			return true;
		switch (war->state)
		{
			case PVPFAN_STARTING:
			case PVPFAN_WAITING:
			case PVPFAN_COUNTDOWN:
				if (f->equipRetries < 30 && (int)(dwNow - f->equipRetryAt) >= 0)
				{
					PlayerBotResetEquipPulse(ch);
					const int worn = RetryPlayerBotPvpFanEquip(ch, *war, *f, f->equipRetries == 2);
					f->equipRetryAt = dwNow + 2000;
					++f->equipRetries;
					if (worn > 0)
					{
						ch->ComputePoints();
						ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
						ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
						sys_log(0, "PVPFAN: wear retry pid=%u name=%s try=%d worn_now=%d hp=%d", f->pid, ch->GetName(),
								f->equipRetries, worn, ch->GetMaxHP());
					}
				}
				HoldPlayerBotPvpFanAtSpot(ch, state, *war, *f, dwNow);
				break;
			case PVPFAN_FIGHTING:
				FightPlayerBotPvpFan(ch, state, *war, *f, dwNow);
				break;
			default:
				state.dwTargetVID = 0;
				if (ch->GetVictim())
					ch->SetVictim(NULL);
				if (ch->IsStateMove())
					ch->Stop();
				break;
		}
		return true;
	}

	// A PvP-fan bot's login (CPlayerBotManager::OnPlayerLoaded).
	void OnPlayerBotPvpFanLoaded(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		TPvpFanWar* war = NULL;
		TPvpFanFighter* f = ch ? FindPlayerBotPvpFanFighter(ch->GetPlayerID(), &war) : NULL;
		if (!f)
			return;
		if (f->phase == PVPFAN_F_LOADING || f->phase == PVPFAN_F_QUEUED)
			f->phase = PVPFAN_F_LOADED;
		state.bBotRole = BOT_ROLE_MOB_GRINDER;
		sys_log(0, "PVPFAN: entered pid=%u name=%s category=%s team=%s map=%ld (%ld,%ld)", f->pid, ch->GetName(),
				war->code.c_str(), war->teams[f->team].name.c_str(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
	}

	// Where a PvP-fan bot loads (CPlayerBotManager::PlaceLoadingBot, before anything else): its spot on the arena.
	bool PlacePlayerBotPvpFanLoading(DWORD pid, long& lMapIndex, long& x, long& y)
	{
		TPvpFanWar* war = NULL;
		TPvpFanFighter* f = FindPlayerBotPvpFanFighter(pid, &war);
		if (!f || !map_allow_find(war->map))
			return false;
		lMapIndex = war->map;
		x = f->x;
		y = f->y;
		return true;
	}

	// ------------------------------------------------------------------ the war

	void AnnouncePlayerBotPvpFanMap(TPvpFanWar& war, const char* text, bool big)
	{
		SendNoticeMap(text, war.map, big);
	}

	void ForgetPlayerBotPvpFanWar(DWORD catId)
	{
		for (std::unordered_map<DWORD, std::pair<DWORD, size_t> >::iterator it = s_mapPvpFanPid.begin();
				it != s_mapPvpFanPid.end();)
		{
			if (it->second.first == catId)
				it = s_mapPvpFanPid.erase(it);
			else
				++it;
		}
		s_mapPvpFanWars.erase(catId);
	}

	std::string StartPlayerBotPvpFanWar(DWORD catId, const std::string& by)
	{
		if (!IsPlayerBotPvpFanEnabled())
			return "PVP Fan jest wylaczony (M2_PVPFAN=0)";
		if (IsPlayerBotPvpFanFlagOff())
			return "PVP Fan jest wylaczony flaga m2_pvpfan_off";
		std::map<DWORD, TPvpFanWar>::iterator running = s_mapPvpFanWars.find(catId);
		if (running != s_mapPvpFanWars.end())
			return std::string("ta kategoria juz trwa: ") + PvpFanStateText(running->second.state);
		TPvpFanWar war;
		std::string err;
		if (!LoadPlayerBotPvpFanWar(catId, war, err))
		{
			PvpFanExec("UPDATE player.pvpfan_category SET state='idle', state_note='%s', state_at=NOW() WHERE id=%u",
					PvpFanEscape(std::string("Start nieudany: ") + err).c_str(), catId);
			return "nie mozna wystartowac: " + err;
		}
		war.startedBy = by;
		const DWORD dwNow = get_dword_time();
		war.state = PVPFAN_STARTING;
		war.stateAt = dwNow;
		std::pair<std::map<DWORD, TPvpFanWar>::iterator, bool> ins = s_mapPvpFanWars.insert(std::make_pair(catId, war));
		TPvpFanWar& w = ins.first->second;
		for (size_t i = 0; i < w.fighters.size(); ++i)
			s_mapPvpFanPid[w.fighters[i].pid] = std::make_pair(catId, i);
		std::string teams;
		for (size_t t = 0; t < w.teams.size(); ++t)
		{
			char part[96];
			snprintf(part, sizeof(part), "%s%u %s", t ? " vs " : "", w.teams[t].fighters, w.teams[t].name.c_str());
			teams += part;
		}
		SetPlayerBotPvpFanState(w, PVPFAN_STARTING, "Boty wchodza: " + teams);
		char text[256];
		snprintf(text, sizeof(text), "PvP Fan \"%s\": %s - boty wchodza na arene!", w.name.c_str(), teams.c_str());
		BroadcastNotice(text);
		sys_log(0, "PVPFAN: start category=%u code=%s by=%s fighters=%u map=%ld centre=(%ld,%ld) teams=%s", catId,
				w.code.c_str(), by.c_str(), (unsigned int)w.fighters.size(), w.map, w.cx, w.cy, teams.c_str());
		return "start: " + teams + " - boty wchodza";
	}

	std::string ReadyPlayerBotPvpFanWar(DWORD catId)
	{
		std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.find(catId);
		if (it == s_mapPvpFanWars.end())
			return "ta kategoria nie jest wystartowana (najpierw /pvpfan start)";
		TPvpFanWar& war = it->second;
		if (war.state == PVPFAN_STARTING)
		{
			unsigned int ready = 0;
			for (size_t i = 0; i < war.fighters.size(); ++i)
				if (war.fighters[i].phase == PVPFAN_F_READY)
					++ready;
			char buf[128];
			snprintf(buf, sizeof(buf), "boty jeszcze wchodza (%u/%u gotowych) - sprobuj za chwile", ready,
					(unsigned int)war.fighters.size());
			return buf;
		}
		if (war.state != PVPFAN_WAITING)
			return std::string("teraz nie: ") + PvpFanStateText(war.state);
		const DWORD dwNow = get_dword_time();
		war.countdownEnd = dwNow + war.countdown * 1000;
		war.countdownSaid = -1;
		SetPlayerBotPvpFanState(war, PVPFAN_COUNTDOWN, "Odliczanie");
		return "odliczanie ruszylo";
	}

	void BeginPlayerBotPvpFanExit(TPvpFanWar& war, int state, const std::string& note)
	{
		SetPlayerBotPvpFanState(war, state, note);
	}

	std::string StopPlayerBotPvpFanWar(DWORD catId, const std::string& by)
	{
		std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.find(catId);
		if (it == s_mapPvpFanWars.end())
		{
			PvpFanExec("UPDATE player.pvpfan_category SET state='idle', state_note='Zatrzymano (nic nie trwalo na %s)', "
					"state_at=NOW() WHERE id=%u", PvpFanCoreName().c_str(), catId);
			return "nic nie trwa - stan wyczyszczony";
		}
		TPvpFanWar& war = it->second;
		if (war.state == PVPFAN_STOPPING)
			return "juz sie zatrzymuje";
		if (war.warRowId && war.state == PVPFAN_FIGHTING)
			PvpFanExec("UPDATE player.pvpfan_war SET state='stopped', ended_at=NOW(), duration_sec=%u, summary='%s' WHERE id=%u",
					(get_dword_time() - war.fightAt) / 1000, PvpFanEscape("Przerwana przez " + by).c_str(), war.warRowId);
		char text[256];
		snprintf(text, sizeof(text), "PvP Fan \"%s\": walka przerwana.", war.name.c_str());
		if (war.state == PVPFAN_FIGHTING || war.state == PVPFAN_COUNTDOWN)
			BroadcastNotice(text);
		BeginPlayerBotPvpFanExit(war, PVPFAN_STOPPING, "Zatrzymano: " + by);
		return "zatrzymuje - boty wychodza";
	}

	void FinishPlayerBotPvpFanWar(TPvpFanWar& war, int winner, bool timeUp)
	{
		const DWORD dwNow = get_dword_time();
		const unsigned int secs = war.fightAt ? PvpFanSince(dwNow, war.fightAt) / 1000 : 0;
		char clock[16];
		snprintf(clock, sizeof(clock), "%u:%02u", secs / 60, secs % 60);
		std::string kills, survivors;
		unsigned int fighters = 0;
		for (size_t t = 0; t < war.teams.size(); ++t)
		{
			char part[96];
			snprintf(part, sizeof(part), "%s%u", t ? ":" : "", war.teams[t].kills);
			kills += part;
			fighters += war.teams[t].fighters;
		}
		char text[512];
		if (winner >= 0)
			snprintf(text, sizeof(text), "PvP Fan \"%s\": wygrywa druzyna %s! Ocalalo %u/%u, czas %s, zabojstwa %s%s",
					war.name.c_str(), war.teams[winner].name.c_str(), war.teams[winner].alive, war.teams[winner].fighters,
					clock, kills.c_str(), timeUp ? " (koniec czasu)" : "");
		else
			snprintf(text, sizeof(text), "PvP Fan \"%s\": remis! Czas %s, zabojstwa %s%s", war.name.c_str(), clock,
					kills.c_str(), timeUp ? " (koniec czasu)" : "");
		war.result = text;
		BroadcastNotice(text);
		AnnouncePlayerBotPvpFanMap(war, winner >= 0 ? "Koniec walki!" : "Remis!", true);
		if (war.warRowId)
		{
			PvpFanExec("UPDATE player.pvpfan_war SET state='%s', ended_at=NOW(), winner_team_id=%u, winner_name='%s', "
					"duration_sec=%u, fighters=%u, summary='%s' WHERE id=%u", winner >= 0 ? "won" : "draw",
					winner >= 0 ? war.teams[winner].id : 0,
					PvpFanEscape(winner >= 0 ? war.teams[winner].name : std::string()).c_str(), secs, fighters,
					PvpFanEscape(std::string(text).substr(0, 500)).c_str(), war.warRowId);
			for (size_t t = 0; t < war.teams.size(); ++t)
				PvpFanExec("REPLACE INTO player.pvpfan_war_team (war_id, team_id, idx, name, fighters, survivors, kills, deaths) "
						"VALUES (%u, %u, %d, '%s', %u, %u, %u, %u)", war.warRowId, war.teams[t].id, war.teams[t].idx + 1,
						PvpFanEscape(war.teams[t].name).c_str(), war.teams[t].fighters, war.teams[t].alive,
						war.teams[t].kills, war.teams[t].deaths);
		}
		sys_log(0, "PVPFAN: result category=%u code=%s war=%u %s", war.catId, war.code.c_str(), war.warRowId, text);
		BeginPlayerBotPvpFanExit(war, PVPFAN_FINISHED, text);
	}

	// Once a second for each war: who stands, whether it is decided, the crowd on each target.
	void EvaluatePlayerBotPvpFanWar(TPvpFanWar& war, DWORD dwNow)
	{
		for (size_t t = 0; t < war.teams.size(); ++t)
			war.teams[t].alive = war.teams[t].ready = 0;
		war.crowd.clear();
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			if (f.phase != PVPFAN_F_READY)
				continue;
			++war.teams[f.team].ready;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(f.pid);
			if (!ch || ch->GetMapIndex() != war.map)
			{
				// Gone from the arena (kicked, logged off by somebody): out of the war.
				if (war.state == PVPFAN_FIGHTING && !f.dead)
				{
					f.dead = true;
					f.deadAt = dwNow;
					++war.teams[f.team].deaths;
				}
				continue;
			}
			// Dead, not merely stunned: the lethal stun's three seconds end in CHARACTER::Dead, whose PvpFanDeath
			// gives the kill to its killer.
			if (war.state == PVPFAN_FIGHTING && !f.dead && ch->IsDead())
			{
				f.dead = true;
				f.deadAt = dwNow;
				++war.teams[f.team].deaths;
			}
			f.lastX = ch->GetX();
			f.lastY = ch->GetY();
			if (!f.dead)
			{
				++war.teams[f.team].alive;
				if (f.targetPid)
					++war.crowd[f.targetPid];
			}
		}
		if (war.state != PVPFAN_FIGHTING)
			return;
		int standing = 0, last = -1;
		for (size_t t = 0; t < war.teams.size(); ++t)
			if (war.teams[t].alive > 0)
			{
				++standing;
				last = (int)t;
			}
		if (standing <= 1)
		{
			FinishPlayerBotPvpFanWar(war, standing == 1 ? last : -1, false);
			return;
		}
		if (PvpFanSince(dwNow, war.fightAt) >= (DWORD)war.maxMinutes * 60 * 1000)
		{
			int best = -1;
			bool tie = false;
			for (size_t t = 0; t < war.teams.size(); ++t)
			{
				if (best < 0 || war.teams[t].alive > war.teams[best].alive ||
						(war.teams[t].alive == war.teams[best].alive && war.teams[t].kills > war.teams[best].kills))
				{
					best = (int)t;
					tie = false;
				}
				else if (war.teams[t].alive == war.teams[best].alive && war.teams[t].kills == war.teams[best].kills)
					tie = true;
			}
			FinishPlayerBotPvpFanWar(war, tie ? -1 : best, true);
		}
	}

	// The logins of a starting war, PVPFAN_SPAWN_PER_SEC a second, and their time-outs.
	void SpawnPlayerBotPvpFanFighters(TPvpFanWar& war, DWORD dwNow, int& budget)
	{
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			if (f.phase == PVPFAN_F_LOADING && PvpFanSince(dwNow, f.askedAt) > PVPFAN_LOAD_TIMEOUT_MS)
			{
				sys_err("PVPFAN: pid=%u login=%s did not load in %u s - out of this war", f.pid, f.login.c_str(),
						PVPFAN_LOAD_TIMEOUT_MS / 1000);
				CPlayerBotManager::instance().Despawn(f.pid, playerbot_session_rules::OUT_GM);
				f.phase = PVPFAN_F_FAILED;
				continue;
			}
			if (f.phase != PVPFAN_F_QUEUED || budget <= 0)
				continue;
			if (f.askedAt && PvpFanSince(dwNow, f.askedAt) < 3000)
				continue;
			--budget;
			f.askedAt = dwNow;
			if (CPlayerBotManager::instance().SpawnPvpFan(f.pid, f.empire, f.accountId, f.login.c_str()))
				f.phase = PVPFAN_F_LOADING;
			else if (++f.tries >= 3)
			{
				sys_err("PVPFAN: pid=%u login=%s refused three times (online elsewhere?) - out of this war", f.pid,
						f.login.c_str());
				f.phase = PVPFAN_F_FAILED;
			}
		}
	}

	// Out of the world after the war, PVPFAN_EXIT_PER_TICK a tick; true when nobody is left.
	bool ExitPlayerBotPvpFanFighters(TPvpFanWar& war)
	{
		int budget = PVPFAN_EXIT_PER_TICK;
		bool left = false;
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			if (f.phase == PVPFAN_F_OUT || f.phase == PVPFAN_F_FAILED || f.phase == PVPFAN_F_QUEUED)
			{
				f.phase = f.phase == PVPFAN_F_QUEUED ? PVPFAN_F_OUT : f.phase;
				continue;
			}
			if (budget <= 0)
			{
				left = true;
				continue;
			}
			--budget;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(f.pid);
			if (ch)
			{
				if (ch->IsDead())
					StandPlayerBotUpHere(ch);
				ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
				ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
				if (ch->GetAlignment() != 0)
					ch->UpdateAlignment(-ch->GetAlignment());
				// MT2009_PLUS_PVPFAN_NO_GEAR_OUT_V1 (the owner, 7 November 2026: "nie ma byc nawet najmniejszej szansy, ze ich
				// ekwipunek trafi na rynek serwera"): the whole set is destroyed before the bot logs off - it is made anew
				// at the next start; the character keeps nothing between wars.
				ClearPlayerBotPvpFanBelongings(ch);
				ch->SetGold(0);
				ch->Save();
			}
			CPlayerBotManager::instance().Despawn(f.pid, playerbot_session_rules::OUT_GM);
			f.phase = PVPFAN_F_OUT;
		}
		return !left;
	}

	void LogPlayerBotPvpFanCensus(DWORD dwNow)
	{
		if (s_mapPvpFanWars.empty() || (s_dwPvpFanNextCensus && (int)(dwNow - s_dwPvpFanNextCensus) < 0))
			return;
		s_dwPvpFanNextCensus = dwNow + PVPFAN_CENSUS_MS;
		for (std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.begin(); it != s_mapPvpFanWars.end(); ++it)
		{
			const TPvpFanWar& war = it->second;
			unsigned int phases[6] = { 0, 0, 0, 0, 0, 0 };
			for (size_t i = 0; i < war.fighters.size(); ++i)
				++phases[MIN(5, (int)war.fighters[i].phase)];
			std::string teams;
			for (size_t t = 0; t < war.teams.size(); ++t)
			{
				char part[96];
				snprintf(part, sizeof(part), " %s=%u/%u(k%u)", war.teams[t].name.c_str(), war.teams[t].alive,
						war.teams[t].fighters, war.teams[t].kills);
				teams += part;
			}
			sys_log(0, "PVPFAN: census category=%u code=%s state=%s fighters=%u queued=%u loading=%u loaded=%u ready=%u "
					"failed=%u out=%u teams:%s", war.catId, war.code.c_str(), PvpFanStateCode(war.state),
					(unsigned int)war.fighters.size(), phases[0], phases[1], phases[2], phases[3], phases[4], phases[5],
					teams.c_str());
		}
	}

	// ------------------------------------------------------------------ the queue and the commands

	DWORD FindPlayerBotPvpFanCategory(const char* key, std::string& name, long& map, BYTE& channel, std::string& state)
	{
		if (!key || !*key)
			return 0;
		std::string safe;
		for (const char* p = key; *p && safe.size() < 32; ++p)
			if ((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z') || (*p >= '0' && *p <= '9') || *p == '_' || *p == '-')
				safe += *p;
		if (safe.empty())
			return 0;
		const unsigned int numeric = (unsigned int)std::strtoul(safe.c_str(), NULL, 10);
		std::unique_ptr<SQLMsg> msg = PvpFanQuery(
				"SELECT id, name, map_index, channel, state FROM player.pvpfan_category WHERE code='%s' OR id=%u "
				"ORDER BY code='%s' DESC LIMIT 1", safe.c_str(), numeric, safe.c_str());
		MYSQL_ROW row;
		if (!PvpFanOk(msg) || !msg->Get()->pSQLResult || !(row = mysql_fetch_row(msg->Get()->pSQLResult)))
			return 0;
		name = row[1] ? row[1] : "";
		map = PvpFanLong(row[2]);
		channel = (BYTE)PvpFanLong(row[3]);
		state = row[4] ? row[4] : "";
		return (DWORD)PvpFanLong(row[0]);
	}

	std::string RunPlayerBotPvpFanCommand(DWORD catId, const std::string& cmd, const std::string& by)
	{
		if (cmd == "start")
			return StartPlayerBotPvpFanWar(catId, by);
		if (cmd == "ready")
			return ReadyPlayerBotPvpFanWar(catId);
		if (cmd == "stop")
			return StopPlayerBotPvpFanWar(catId, by);
		return "nieznane polecenie";
	}

	// A core restarted in the middle of a war: the bots are gone, so are its categories' wars.
	void RecoverPlayerBotPvpFanCategories()
	{
		std::unique_ptr<SQLMsg> msg = PvpFanQuery(
				"SELECT id, map_index, channel FROM player.pvpfan_category WHERE state<>'idle'");
		if (!PvpFanOk(msg) || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			const DWORD id = (DWORD)PvpFanLong(row[0]);
			const long map = PvpFanLong(row[1]);
			if (map > 0 && map_allow_find(map) && (BYTE)PvpFanLong(row[2]) == g_bChannel &&
					s_mapPvpFanWars.find(id) == s_mapPvpFanWars.end())
			{
				PvpFanExec("UPDATE player.pvpfan_category SET state='idle', state_note='Przerwane (restart rdzenia %s)', "
						"state_at=NOW(), online=0 WHERE id=%u", PvpFanCoreName().c_str(), id);
				sys_log(0, "PVPFAN: category=%u was busy at this core's start (a restart in the middle of a war) - idle again", id);
			}
		}
	}

	void PollPlayerBotPvpFanQueue(DWORD dwNow)
	{
		if ((int)(dwNow - s_dwPvpFanNextFlagPoll) >= 0 || s_dwPvpFanNextFlagPoll == 0)
		{
			s_dwPvpFanNextFlagPoll = dwNow + PVPFAN_FLAG_POLL_MS;
			std::unique_ptr<SQLMsg> flag = PvpFanQuery(
					"SELECT lValue FROM player.quest WHERE dwPID=0 AND szName='m2_pvpfan_off' LIMIT 1");
			MYSQL_ROW row;
			s_bPvpFanDbFlagOff = PvpFanOk(flag) && flag->Get()->pSQLResult &&
					(row = mysql_fetch_row(flag->Get()->pSQLResult)) && PvpFanLong(row[0]) != 0;
		}
		if (s_dwPvpFanNextPoll && (int)(dwNow - s_dwPvpFanNextPoll) < 0)
			return;
		s_dwPvpFanNextPoll = dwNow + PVPFAN_COMMAND_POLL_MS;
		std::unique_ptr<SQLMsg> msg = PvpFanQuery(
				"SELECT c.id, c.category_id, c.cmd, c.source, k.map_index, k.channel FROM player.pvpfan_command c "
				"JOIN player.pvpfan_category k ON k.id=c.category_id WHERE c.done=0 ORDER BY c.id LIMIT 20");
		if (!PvpFanOk(msg))
		{
			if (!s_bPvpFanTablesMissing)
				sys_err("PVPFAN: player.pvpfan_command cannot be read (pvpfan.sql not applied?) - asking again in a minute");
			s_bPvpFanTablesMissing = true;
			s_dwPvpFanNextPoll = dwNow + 60000;
			return;
		}
		s_bPvpFanTablesMissing = false;
		if (!s_bPvpFanRecovered)
		{
			s_bPvpFanRecovered = true;
			RecoverPlayerBotPvpFanCategories();
		}
		if (!msg->Get()->pSQLResult)
			return;
		struct TCmd { DWORD id, cat; std::string cmd, source; };
		std::vector<TCmd> mine;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			const long map = PvpFanLong(row[4]);
			if (map <= 0 || !map_allow_find(map) || (BYTE)PvpFanLong(row[5]) != g_bChannel)
				continue;
			TCmd c;
			c.id = (DWORD)PvpFanLong(row[0]);
			c.cat = (DWORD)PvpFanLong(row[1]);
			c.cmd = row[2] ? row[2] : "";
			c.source = row[3] ? row[3] : "";
			mine.push_back(c);
		}
		for (size_t i = 0; i < mine.size(); ++i)
		{
			std::unique_ptr<SQLMsg> claim = PvpFanQuery(
					"UPDATE player.pvpfan_command SET done=1, taken_by='%s', taken_at=NOW() WHERE id=%u AND done=0",
					PvpFanCoreName().c_str(), mine[i].id);
			if (!PvpFanOk(claim) || claim->Get()->uiAffectedRows != 1)
				continue;
			const std::string result = RunPlayerBotPvpFanCommand(mine[i].cat, mine[i].cmd, mine[i].source);
			PvpFanExec("UPDATE player.pvpfan_command SET result='%s' WHERE id=%u", PvpFanEscape(result.substr(0, 250)).c_str(),
					mine[i].id);
			sys_log(0, "PVPFAN: command id=%u category=%u cmd=%s source=%s -> %s", mine[i].id, mine[i].cat,
					mine[i].cmd.c_str(), mine[i].source.c_str(), result.c_str());
		}
	}

	// From Update (and the world clock on a core no bot has woken): the queue, the logins, the countdown, the
	// evaluation, the exits.
	void ManagePlayerBotPvpFan(DWORD dwNow)
	{
		if (!IsPlayerBotPvpFanEnabled())
			return;
		if (s_dwPvpFanLastTick && PvpFanSince(dwNow, s_dwPvpFanLastTick) < PVPFAN_TICK_MS)
			return;
		s_dwPvpFanLastTick = dwNow;
		PollPlayerBotPvpFanQueue(dwNow);
		if (s_mapPvpFanWars.empty())
			return;
		const bool off = IsPlayerBotPvpFanFlagOff();
		int budget = std::max(1, GetPvpFanSpawnPerSec() * (int)PVPFAN_TICK_MS / 1000);
		std::vector<DWORD> done;
		for (std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.begin(); it != s_mapPvpFanWars.end(); ++it)
		{
			TPvpFanWar& war = it->second;
			if (off && war.state != PVPFAN_STOPPING)
			{
				StopPlayerBotPvpFanWar(war.catId, "flaga m2_pvpfan_off");
				continue;
			}
			if (dwNow >= war.nextEval)
			{
				war.nextEval = dwNow + 1000;
				EvaluatePlayerBotPvpFanWar(war, dwNow);
			}
			switch (war.state)
			{
				case PVPFAN_STARTING:
				{
					SpawnPlayerBotPvpFanFighters(war, dwNow, budget);
					bool pending = false;
					std::vector<unsigned int> ready(war.teams.size(), 0);
					for (size_t i = 0; i < war.fighters.size(); ++i)
					{
						const BYTE p = war.fighters[i].phase;
						if (p == PVPFAN_F_QUEUED || p == PVPFAN_F_LOADING || p == PVPFAN_F_LOADED)
							pending = true;
						else if (p == PVPFAN_F_READY)
							++ready[war.fighters[i].team];
					}
					int teamsReady = 0;
					for (size_t t = 0; t < ready.size(); ++t)
						if (ready[t] > 0)
							++teamsReady;
					if (!pending && teamsReady >= 2)
					{
						std::string teams;
						for (size_t t = 0; t < war.teams.size(); ++t)
						{
							char part[96];
							snprintf(part, sizeof(part), "%s%u %s", t ? " vs " : "", ready[t], war.teams[t].name.c_str());
							teams += part;
						}
						SetPlayerBotPvpFanState(war, PVPFAN_WAITING, "Gotowi: " + teams);
						char text[256];
						snprintf(text, sizeof(text), "PvP Fan \"%s\": %s na arenie - czekaja na sygnal (/pvpfan gotowi %s)",
								war.name.c_str(), teams.c_str(), war.code.c_str());
						BroadcastNotice(text);
					}
					else if (!pending)
						StopPlayerBotPvpFanWar(war.catId, "za malo botow weszlo (druzyna bez nikogo)");
					else if (PvpFanSince(dwNow, war.stateAt) > PVPFAN_START_TIMEOUT_MS)
						StopPlayerBotPvpFanWar(war.catId, "boty nie weszly w 4 minuty");
					else if (dwNow >= war.nextStateWrite)
						WritePlayerBotPvpFanState(war, "Boty wchodza");
					break;
				}
				case PVPFAN_WAITING:
					if (PvpFanSince(dwNow, war.stateAt) > PVPFAN_WAIT_TIMEOUT_MS)
						StopPlayerBotPvpFanWar(war.catId, "nikt nie dal sygnalu przez 45 minut");
					else if (dwNow >= war.nextStateWrite)
						WritePlayerBotPvpFanState(war, "Czekaja na sygnal");
					break;
				case PVPFAN_COUNTDOWN:
				{
					const int left = (int)(war.countdownEnd - dwNow) > 0 ? (int)((war.countdownEnd - dwNow + 999) / 1000) : 0;
					if (left > 0 && left != war.countdownSaid)
					{
						war.countdownSaid = left;
						char text[128];
						snprintf(text, sizeof(text), "PvP Fan \"%s\": walka za %d...", war.name.c_str(), left);
						AnnouncePlayerBotPvpFanMap(war, text, left <= 3);
					}
					if (left == 0)
					{
						war.fightAt = dwNow;
						unsigned int fighters = 0;
						for (size_t t = 0; t < war.teams.size(); ++t)
							fighters += war.teams[t].ready;
						std::unique_ptr<SQLMsg> ins = PvpFanQuery(
								"INSERT INTO player.pvpfan_war (category_id, category_name, started_at, fight_at, state, fighters, started_by) "
								"VALUES (%u, '%s', NOW() - INTERVAL %u SECOND, NOW(), 'fighting', %u, '%s')", war.catId,
								PvpFanEscape(war.name).c_str(), PvpFanSince(dwNow, war.stateAt) / 1000 + war.countdown, fighters,
								PvpFanEscape(war.startedBy.substr(0, 46)).c_str());
						war.warRowId = PvpFanOk(ins) ? ins->Get()->uiInsertID : 0;
						for (size_t i = 0; i < war.fighters.size(); ++i)
						{
							war.fighters[i].dead = false;
							war.fighters[i].kills = 0;
						}
						for (size_t t = 0; t < war.teams.size(); ++t)
							war.teams[t].kills = war.teams[t].deaths = 0;
						SetPlayerBotPvpFanState(war, PVPFAN_FIGHTING, "Walka trwa");
						char text[128];
						snprintf(text, sizeof(text), "PvP Fan \"%s\": WALKA!", war.name.c_str());
						AnnouncePlayerBotPvpFanMap(war, text, true);
						BroadcastNotice(text);
					}
					break;
				}
				case PVPFAN_FIGHTING:
					if (dwNow >= war.nextStateWrite)
						WritePlayerBotPvpFanState(war, "Walka trwa");
					break;
				case PVPFAN_FINISHED:
					if (PvpFanSince(dwNow, war.stateAt) < (DWORD)war.exitSec * 1000)
						break;
					// fall through
				case PVPFAN_STOPPING:
					if (ExitPlayerBotPvpFanFighters(war))
						done.push_back(war.catId);
					break;
				default:
					break;
			}
		}
		for (size_t i = 0; i < done.size(); ++i)
		{
			std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.find(done[i]);
			if (it == s_mapPvpFanWars.end())
				continue;
			const std::string note = it->second.result.empty() ? "Zakonczono" : it->second.result;
			PvpFanExec("UPDATE player.pvpfan_category SET state='idle', state_note='%s', state_at=NOW(), online=0, core='' "
					"WHERE id=%u", PvpFanEscape(note.substr(0, 250)).c_str(), done[i]);
			sys_log(0, "PVPFAN: category=%u code=%s over, every bot out", done[i], it->second.code.c_str());
			ForgetPlayerBotPvpFanWar(done[i]);
		}
		LogPlayerBotPvpFanCensus(dwNow);
	}

	// ------------------------------------------------------------------ the GM's command

	void SayPlayerBotPvpFan(LPCHARACTER ch, const char* fmt, ...)
	{
		char buf[512];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		if (ch)
			ch->ChatPacket(CHAT_TYPE_INFO, "[PvP Fan] %s", buf);
	}

	void RecordPlayerBotPvpFanGmPos(LPCHARACTER ch)
	{
		PvpFanExec("REPLACE INTO player.pvpfan_gm_pos (gm_name, map_index, x, y, at) VALUES ('%s', %ld, %ld, %ld, NOW())",
				PvpFanEscape(ch->GetName()).c_str(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
	}

	void ListPlayerBotPvpFan(LPCHARACTER ch)
	{
		std::unique_ptr<SQLMsg> msg = PvpFanQuery(
				"SELECT k.id, k.code, k.name, k.state, k.map_index, k.channel, "
				"(SELECT COUNT(*) FROM player.pvpfan_char c WHERE c.category_id=k.id AND c.retired=0) "
				"FROM player.pvpfan_category k ORDER BY k.id LIMIT 30");
		if (!PvpFanOk(msg) || !msg->Get()->pSQLResult)
		{
			SayPlayerBotPvpFan(ch, "Nie mozna odczytac kategorii (tabele player.pvpfan_*).");
			return;
		}
		MYSQL_ROW row;
		int n = 0;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			++n;
			SayPlayerBotPvpFan(ch, "#%s %s \"%s\" - %s, mapa %s kanal %s, postaci %s", row[0], row[1], row[2] ? row[2] : "",
					row[3] ? row[3] : "", row[4], row[5], row[6]);
		}
		if (!n)
			SayPlayerBotPvpFan(ch, "Brak kategorii - utworz je w panelu Seban: Wydarzenia -> PVP Fan.");
		SayPlayerBotPvpFan(ch, "Komendy: start <kod> | gotowi <kod> | stop <kod> | status <kod> | tu <kod> [druzyna] | pozycja");
	}

	void StatusPlayerBotPvpFan(LPCHARACTER ch, DWORD catId)
	{
		std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.find(catId);
		if (it != s_mapPvpFanWars.end())
		{
			TPvpFanWar& war = it->second;
			SayPlayerBotPvpFan(ch, "\"%s\" (%s): %s, mapa %ld (%ld,%ld), rdzen %s", war.name.c_str(), war.code.c_str(),
					PvpFanStateText(war.state), war.map, war.cx, war.cy, PvpFanCoreName().c_str());
			for (size_t t = 0; t < war.teams.size(); ++t)
				SayPlayerBotPvpFan(ch, "  %s: wszystkich %u, na arenie %u, zywych %u, zabojstw %u, poleglych %u",
						war.teams[t].name.c_str(), war.teams[t].fighters, war.teams[t].ready, war.teams[t].alive,
						war.teams[t].kills, war.teams[t].deaths);
			if (war.state == PVPFAN_FIGHTING)
				SayPlayerBotPvpFan(ch, "  walka od %u s (limit %d min)", (get_dword_time() - war.fightAt) / 1000, war.maxMinutes);
			return;
		}
		std::unique_ptr<SQLMsg> msg = PvpFanQuery(
				"SELECT name, code, state, state_note, alive_text, core, map_index, channel FROM player.pvpfan_category WHERE id=%u",
				catId);
		MYSQL_ROW row;
		if (!PvpFanOk(msg) || !msg->Get()->pSQLResult || !(row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			SayPlayerBotPvpFan(ch, "Nie ma takiej kategorii.");
			return;
		}
		SayPlayerBotPvpFan(ch, "\"%s\" (%s): %s - %s", row[0], row[1], row[2], row[3]);
		SayPlayerBotPvpFan(ch, "  %s | rdzen: %s | mapa %s kanal %s", row[4] && *row[4] ? row[4] : "-",
				row[5] && *row[5] ? row[5] : "-", row[6], row[7]);
	}
}

// ---------------------------------------------------------------------- the engine's hooks

// battle_is_attackable (server-patches/pvpfan, battle.cpp): 1 they may, 0 they may not, -1 not a PvP-fan matter.
int PvpFanAttackable(LPCHARACTER ch, LPCHARACTER victim)
{
	if (s_mapPvpFanPid.empty() || !ch || !victim || ch == victim)
		return -1;
	TPvpFanWar* aw = NULL;
	TPvpFanWar* vw = NULL;
	TPvpFanFighter* a = ch->IsPC() ? FindPlayerBotPvpFanFighter(ch->GetPlayerID(), &aw) : NULL;
	TPvpFanFighter* v = victim->IsPC() ? FindPlayerBotPvpFanFighter(victim->GetPlayerID(), &vw) : NULL;
	if (!a && !v)
		return -1;
	if (ch->IsStun())
		return 0;
	if (a && v)
		return aw == vw && aw->state == PVPFAN_FIGHTING && a->team != v->team && !a->dead && !v->dead &&
				!ch->IsDead() && !victim->IsDead() ? 1 : 0;
	// One side is a PvP-fan bot, the other is not: a person only where the category lets people in.
	TPvpFanWar* war = a ? aw : vw;
	LPCHARACTER other = a ? victim : ch;
	if (war->allowPlayers && war->state == PVPFAN_FIGHTING && other->IsPC() && other->GetDesc() &&
			!other->GetDesc()->IsBot() && !other->IsDead() && !(a ? a->dead : v->dead))
		return 1;
	return 0;
}

// CHARACTER::Dead (server-patches/pvpfan, char_battle.cpp): a PvP-fan bot's death is no murder - true and the engine
// takes it as a guild war's (no alignment, no dropped item); the kill is the war's count.
bool PvpFanDeath(LPCHARACTER victim, LPCHARACTER killer)
{
	if (s_mapPvpFanPid.empty() || !victim || !victim->IsPC())
		return false;
	TPvpFanWar* war = NULL;
	TPvpFanFighter* v = FindPlayerBotPvpFanFighter(victim->GetPlayerID(), &war);
	if (!v)
		return false;
	if (war->state == PVPFAN_FIGHTING && !v->dead)
	{
		v->dead = true;
		v->deadAt = get_dword_time();
		++war->teams[v->team].deaths;
		TPvpFanWar* kw = NULL;
		TPvpFanFighter* k = killer && killer->IsPC() ? FindPlayerBotPvpFanFighter(killer->GetPlayerID(), &kw) : NULL;
		if (k && kw == war && k->team != v->team)
		{
			++k->kills;
			++war->teams[k->team].kills;
		}
		if (!war->firstBlood && killer)
		{
			war->firstBlood = true;
			char text[160];
			snprintf(text, sizeof(text), "Pierwsza krew: %s pokonuje %s!", killer->GetName(), victim->GetName());
			SendNoticeMap(text, war->map, false);
		}
	}
	return true;
}

// "/pvpfan" (server-patches/pvpfan, cmd.cpp; GM_HIGH_WIZARD).
void PlayerBotPvpFanCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch)
		return;
	if (!IsPlayerBotPvpFanEnabled())
	{
		SayPlayerBotPvpFan(ch, "PVP Fan jest wylaczony na tym serwerze (M2_PVPFAN=0).");
		return;
	}
	char sub[32] = "", key[48] = "", extra[32] = "";
	if (argument)
		sscanf(argument, " %31s %47s %31s", sub, key, extra);
	std::string cmd = sub;
	for (size_t i = 0; i < cmd.size(); ++i)
		cmd[i] = (char)tolower((unsigned char)cmd[i]);
	if (cmd.empty() || cmd == "lista" || cmd == "list")
	{
		ListPlayerBotPvpFan(ch);
		return;
	}
	if (cmd == "pozycja" || cmd == "pos")
	{
		RecordPlayerBotPvpFanGmPos(ch);
		SayPlayerBotPvpFan(ch, "Twoja pozycja: mapa %ld, x=%ld y=%ld - zapisana dla panelu (\"Uzyj pozycji GM\").",
				ch->GetMapIndex(), ch->GetX(), ch->GetY());
		return;
	}
	std::string name, state;
	long map = 0;
	BYTE channel = 0;
	const DWORD catId = FindPlayerBotPvpFanCategory(key, name, map, channel, state);
	if (!catId)
	{
		SayPlayerBotPvpFan(ch, "Nie ma kategorii \"%s\" - /pvpfan lista.", key);
		return;
	}
	if (cmd == "status" || cmd == "stan")
	{
		StatusPlayerBotPvpFan(ch, catId);
		return;
	}
	if (cmd == "tu" || cmd == "here")
	{
		RecordPlayerBotPvpFanGmPos(ch);
		const long here = ch->GetMapIndex() >= 10000 ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		if (ch->GetMapIndex() >= 10000)
		{
			SayPlayerBotPvpFan(ch, "To kopia mapy (instancja) - arena musi stac na zwyklej mapie.");
			return;
		}
		if (!extra[0])
		{
			PvpFanExec("UPDATE player.pvpfan_category SET map_index=%ld, x=%ld, y=%ld WHERE id=%u", here, ch->GetX(),
					ch->GetY(), catId);
			SayPlayerBotPvpFan(ch, "Srodek areny \"%s\": mapa %ld, x=%ld y=%ld. Druzyny stana %s.", name.c_str(), here,
					ch->GetX(), ch->GetY(), "wokol (promien w panelu) albo w swoich punktach");
		}
		else
		{
			if (map > 0 && map != here)
			{
				SayPlayerBotPvpFan(ch, "Arena tej kategorii jest na mapie %ld - punkt druzyny musi byc na tej samej mapie.", map);
				return;
			}
			const int idx = std::atoi(extra);
			std::unique_ptr<SQLMsg> upd = PvpFanQuery(
					"UPDATE player.pvpfan_team SET x=%ld, y=%ld WHERE category_id=%u AND idx=%d", ch->GetX(), ch->GetY(), catId,
					idx);
			if (!PvpFanOk(upd) || upd->Get()->uiAffectedRows == 0)
			{
				SayPlayerBotPvpFan(ch, "Nie ma druzyny nr %d w tej kategorii (numery 1, 2, ...).", idx);
				return;
			}
			if (map <= 0)
				PvpFanExec("UPDATE player.pvpfan_category SET map_index=%ld, x=%ld, y=%ld WHERE id=%u", here, ch->GetX(),
						ch->GetY(), catId);
			SayPlayerBotPvpFan(ch, "Punkt startowy druzyny %d w \"%s\": x=%ld y=%ld.", idx, name.c_str(), ch->GetX(), ch->GetY());
		}
		return;
	}
	std::string verb;
	if (cmd == "start")
		verb = "start";
	else if (cmd == "gotowi" || cmd == "ready" || cmd == "walka" || cmd == "go")
		verb = "ready";
	else if (cmd == "stop" || cmd == "koniec")
		verb = "stop";
	else
	{
		SayPlayerBotPvpFan(ch, "Nieznana komenda \"%s\". /pvpfan lista", sub);
		return;
	}
	const std::string by = std::string("gm:") + ch->GetName();
	if (map > 0 && map_allow_find(map) && channel == g_bChannel)
	{
		const std::string result = RunPlayerBotPvpFanCommand(catId, verb, by);
		SayPlayerBotPvpFan(ch, "\"%s\": %s", name.c_str(), result.c_str());
		return;
	}
	if (map <= 0)
	{
		SayPlayerBotPvpFan(ch, "\"%s\": arena nie jest ustawiona (panel albo /pvpfan tu %s).", name.c_str(), key);
		return;
	}
	PvpFanExec("INSERT INTO player.pvpfan_command (category_id, cmd, source) VALUES (%u, '%s', '%s')", catId, verb.c_str(),
			PvpFanEscape(by.substr(0, 46)).c_str());
	SayPlayerBotPvpFan(ch, "\"%s\": arena jest na mapie %ld kanalu %u - polecenie \"%s\" przekazane do tamtego rdzenia "
			"(wynik w ogloszeniu i w /pvpfan status %s).", name.c_str(), map, (unsigned int)channel, verb.c_str(), key);
}
