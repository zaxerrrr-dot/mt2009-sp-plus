// MT2009 PLUS Battle Pass (the operator, 28 September: "battle pass z oknem i
// przyciskiem w gui, boty nie korzystaja, zamiast biletu - nagroda kupon SM
// 50, postep w bazie"; the missions are set afterwards).
//
// No ticket: every player (not a bot) takes part. A season is a calendar
// month of the server's clock (YYYYMM), so progress starts again on the
// first; nothing has to be deleted. Everything lives in the database:
//   player.battlepass_mission  - the missions, the operator's to fill: type,
//                                target (0 = any), count, up to three rewards
//                                of its own (given the moment the mission is
//                                done), an optional name and description (raw
//                                CP1250; an empty name is worded by the client
//                                from the type, "//" breaks a description);
//   player.battlepass_progress - pid, season, mission, progress, claimed;
//                                mission 0 is the season's final reward.
// Finishing every mission of the season gives the final reward: up to three
// items of player.battlepass_config, a Kupon SM (50) - 80017 - at first.
// The advanced panel (Seban Panel, Battle Pass page) edits both tables; the
// game reads them again every 30 seconds.
//
// Mission types (the window words them, uibattlepass.py):
//   1 monsters killed   2 Metin stones   3 bosses        4 fish caught
//   5 refines that took 6 yang picked up 7 chests opened 8 herbs picked
//   9 ore mined        10 dungeons done 11 mission books 12 minutes played
//  13 items used (target = the vnum)
// 1-3 and 13 honour the target vnum; a companion's kill is its owner's, as
// for the quests. The engine calls in through server-patches/playerqol
// (MT2009_PLUS_BATTLE_PASS_V1): the kill, AddPlayerStat, UseItem and the
// /battlepass command.
//
// The database is the truth. A player's character moves between cores (each
// hosts other maps), so a core never writes a total: it counts in memory and
// adds its count to the row (progress = progress + delta) every minute, and
// at once when a mission may be done; the window reads the rows again. A
// reward is taken with a conditional UPDATE, so no two cores give it.
namespace mt2009_battlepass
{
	enum EType
	{
		TYPE_MONSTER = 1,
		TYPE_METIN = 2,
		TYPE_BOSS = 3,
		TYPE_FISH = 4,
		TYPE_REFINE = 5,
		TYPE_YANG = 6,
		TYPE_CHEST = 7,
		TYPE_HERB = 8,
		TYPE_MINING = 9,
		TYPE_DUNGEON = 10,
		TYPE_QUESTBOOK = 11,
		TYPE_PLAYTIME = 12,
		TYPE_USE_ITEM = 13,
	};

	// The season's final reward: up to three items, player.battlepass_config
	// (the advanced panel's Battle Pass page); a Kupon SM (50) - 80017 - until
	// the operator sets another.
	const DWORD FINAL_REWARD_VNUM = 80017;
	const DWORD FINAL_REWARD_COUNT = 1;
	// The panel's changes reach the game within this.
	const DWORD MISSIONS_RELOAD_MS = 30 * 1000;

	struct Mission
	{
		DWORD id;
		BYTE type;
		DWORD target;
		DWORD count;
		DWORD rewardVnum[3];
		DWORD rewardCount[3];
		std::string nameHex;
		std::string descHex;
	};

	// What this core knows of one mission of one player: the total the
	// database had at the last read, and what this core counted since. The
	// database is the truth - a player's characters move between cores (every
	// core hosts other maps), and each core only ever adds its own count to it
	// (progress = progress + delta), never writes a total over another core's.
	struct Progress
	{
		DWORD value;
		DWORD delta;
		bool claimed;
		Progress() : value(0), delta(0), claimed(false) {}
	};

	struct Cache
	{
		DWORD season;
		std::map<DWORD, Progress> missions;
		Progress final;
		Cache() : season(0) {}
	};

	std::vector<Mission> s_vecMissions;
	DWORD s_adwFinalVnum[3] = { FINAL_REWARD_VNUM, 0, 0 };
	DWORD s_adwFinalCount[3] = { FINAL_REWARD_COUNT, 0, 0 };
	DWORD s_dwMissionsLoadedAt = 0;
	bool s_bMissionsLoaded = false;
	bool s_bTables = false;
	std::map<DWORD, Cache> s_mapCaches;
	LPEVENT s_pkTick = NULL;

	DWORD CurrentSeason()
	{
		const time_t now = time(NULL);
		struct tm local;
		localtime_r(&now, &local);
		return (DWORD)((local.tm_year + 1900) * 100 + local.tm_mon + 1);
	}

	int DaysLeft()
	{
		const time_t now = time(NULL);
		struct tm local;
		localtime_r(&now, &local);
		struct tm next = local;
		next.tm_mday = 1;
		next.tm_hour = next.tm_min = next.tm_sec = 0;
		next.tm_mon += 1;
		next.tm_isdst = -1;
		const time_t end = mktime(&next);
		return end > now ? (int)((end - now + 86399) / 86400) : 0;
	}

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	bool EnsureTables()
	{
		if (s_bTables)
			return true;
		std::unique_ptr<SQLMsg> m(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.battlepass_mission ("
				"id INT UNSIGNED NOT NULL PRIMARY KEY, "
				"type TINYINT UNSIGNED NOT NULL, "
				"target INT UNSIGNED NOT NULL DEFAULT 0, "
				"count INT UNSIGNED NOT NULL DEFAULT 1, "
				"reward_vnum INT UNSIGNED NOT NULL DEFAULT 0, "
				"reward_count INT UNSIGNED NOT NULL DEFAULT 0, "
				"name VARBINARY(96) NOT NULL DEFAULT '', "
				"active TINYINT UNSIGNED NOT NULL DEFAULT 1) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> more(AccountDB::instance().DirectQuery(
				"ALTER TABLE player.battlepass_mission "
				"ADD COLUMN IF NOT EXISTS reward2_vnum INT UNSIGNED NOT NULL DEFAULT 0 AFTER reward_count, "
				"ADD COLUMN IF NOT EXISTS reward2_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER reward2_vnum, "
				"ADD COLUMN IF NOT EXISTS reward3_vnum INT UNSIGNED NOT NULL DEFAULT 0 AFTER reward2_count, "
				"ADD COLUMN IF NOT EXISTS reward3_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER reward3_vnum, "
				"ADD COLUMN IF NOT EXISTS description VARBINARY(255) NOT NULL DEFAULT '' AFTER name"));
		std::unique_ptr<SQLMsg> p(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.battlepass_progress ("
				"pid INT UNSIGNED NOT NULL, "
				"season INT UNSIGNED NOT NULL, "
				"mission INT UNSIGNED NOT NULL, "
				"progress INT UNSIGNED NOT NULL DEFAULT 0, "
				"claimed TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"PRIMARY KEY (pid, season, mission)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> config(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.battlepass_config ("
				"id TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
				"final1_vnum INT UNSIGNED NOT NULL DEFAULT 0, final1_count INT UNSIGNED NOT NULL DEFAULT 0, "
				"final2_vnum INT UNSIGNED NOT NULL DEFAULT 0, final2_count INT UNSIGNED NOT NULL DEFAULT 0, "
				"final3_vnum INT UNSIGNED NOT NULL DEFAULT 0, final3_count INT UNSIGNED NOT NULL DEFAULT 0) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> configRow(AccountDB::instance().DirectQuery(
				"INSERT IGNORE INTO player.battlepass_config (id, final1_vnum, final1_count) VALUES (1, 80017, 1)"));
		s_bTables = m.get() && m->uiSQLErrno == 0 && p.get() && p->uiSQLErrno == 0;
		if (!s_bTables)
		{
			sys_err("BATTLEPASS: no tables errno=%u/%u", m.get() ? m->uiSQLErrno : 0U, p.get() ? p->uiSQLErrno : 0U);
			return false;
		}
		// Three to see the window with until the operator writes the season's
		// own (only into an empty table, once).
		std::unique_ptr<SQLMsg> seeded(AccountDB::instance().DirectQuery(
				"INSERT INTO player.battlepass_mission (id, type, target, count) "
				"SELECT t.id, t.type, t.target, t.count FROM (SELECT 1 AS id, 1 AS type, 0 AS target, 1000 AS count "
				"UNION ALL SELECT 2, 2, 0, 30 UNION ALL SELECT 3, 4, 0, 50) AS t "
				"WHERE NOT EXISTS (SELECT 1 FROM player.battlepass_mission)"));
		return true;
	}

	std::string HexOf(const char* data, size_t len)
	{
		static const char* const digits = "0123456789abcdef";
		std::string out;
		for (size_t i = 0; i < len; ++i)
		{
			const unsigned char c = (unsigned char)data[i];
			out += digits[c >> 4];
			out += digits[c & 15];
		}
		return out;
	}

	void LoadMissions(bool force)
	{
		const DWORD now = get_dword_time();
		if (!force && s_bMissionsLoaded && now - s_dwMissionsLoadedAt < MISSIONS_RELOAD_MS)
			return;
		s_dwMissionsLoadedAt = now;
		if (!EnsureTables())
			return;
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"SELECT id, type, target, count, reward_vnum, reward_count, reward2_vnum, reward2_count, "
				"reward3_vnum, reward3_count, name, description FROM player.battlepass_mission "
				"WHERE active <> 0 ORDER BY id"));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		std::vector<Mission> fresh;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			unsigned long* lengths = mysql_fetch_lengths(msg->Get()->pSQLResult);
			Mission m;
			unsigned int type = 0;
			str_to_number(m.id, row[0]);
			str_to_number(type, row[1]);
			str_to_number(m.target, row[2]);
			str_to_number(m.count, row[3]);
			for (int r = 0; r < 3; ++r)
			{
				m.rewardVnum[r] = m.rewardCount[r] = 0;
				str_to_number(m.rewardVnum[r], row[4 + r * 2]);
				str_to_number(m.rewardCount[r], row[5 + r * 2]);
			}
			m.type = (BYTE)type;
			if (m.id == 0 || m.count == 0 || m.type < TYPE_MONSTER || m.type > TYPE_USE_ITEM)
				continue;
			if (row[10] && lengths && lengths[10] > 0)
				m.nameHex = HexOf(row[10], lengths[10]);
			if (row[11] && lengths && lengths[11] > 0)
				m.descHex = HexOf(row[11], lengths[11]);
			fresh.push_back(m);
		}
		if (!s_bMissionsLoaded || fresh.size() != s_vecMissions.size())
			sys_log(0, "BATTLEPASS: %u missions", (unsigned int)fresh.size());
		std::unique_ptr<SQLMsg> config(AccountDB::instance().DirectQuery(
				"SELECT final1_vnum, final1_count, final2_vnum, final2_count, final3_vnum, final3_count "
				"FROM player.battlepass_config WHERE id=1"));
		if (config.get() && config->uiSQLErrno == 0 && config->Get() && config->Get()->pSQLResult)
		{
			MYSQL_ROW crow = mysql_fetch_row(config->Get()->pSQLResult);
			if (crow)
				for (int r = 0; r < 3; ++r)
				{
					s_adwFinalVnum[r] = s_adwFinalCount[r] = 0;
					str_to_number(s_adwFinalVnum[r], crow[r * 2]);
					str_to_number(s_adwFinalCount[r], crow[r * 2 + 1]);
				}
		}
		s_vecMissions.swap(fresh);
		s_bMissionsLoaded = true;
	}

	const Mission* FindMission(DWORD id)
	{
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
			if (s_vecMissions[i].id == id)
				return &s_vecMissions[i];
		return NULL;
	}

	// The player's rows of this season, read again; this core's own counts
	// not yet written stay on top of them.
	void ReadProgress(DWORD pid, Cache& cache)
	{
		for (std::map<DWORD, Progress>::iterator it = cache.missions.begin(); it != cache.missions.end(); ++it)
		{
			it->second.value = 0;
			it->second.claimed = false;
		}
		cache.final.value = 0;
		cache.final.claimed = false;
		char query[160];
		snprintf(query, sizeof(query),
				"SELECT mission, progress, claimed FROM player.battlepass_progress WHERE pid=%u AND season=%u",
				pid, cache.season);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			DWORD mission = 0, progress = 0, claimed = 0;
			str_to_number(mission, row[0]);
			str_to_number(progress, row[1]);
			str_to_number(claimed, row[2]);
			Progress& p = mission == 0 ? cache.final : cache.missions[mission];
			p.value = progress;
			p.claimed = claimed != 0;
		}
	}

	Cache& GetCache(LPCHARACTER ch)
	{
		const DWORD pid = ch->GetPlayerID();
		const DWORD season = CurrentSeason();
		std::map<DWORD, Cache>::iterator it = s_mapCaches.find(pid);
		if (it != s_mapCaches.end() && it->second.season == season)
			return it->second;
		Cache& cache = s_mapCaches[pid];
		cache = Cache();
		cache.season = season;
		if (EnsureTables())
			ReadProgress(pid, cache);
		return cache;
	}

	// This core's counts into the database, added to what is there (capped at
	// the mission's count). Synchronous when a decision hangs on the result.
	void WriteDeltas(DWORD pid, Cache& cache, bool now)
	{
		for (std::map<DWORD, Progress>::iterator it = cache.missions.begin(); it != cache.missions.end(); ++it)
		{
			Progress& p = it->second;
			if (!p.delta)
				continue;
			const Mission* m = FindMission(it->first);
			const DWORD cap = m ? m->count : 0xFFFFFFFFu;
			char query[320];
			snprintf(query, sizeof(query),
					"INSERT INTO player.battlepass_progress (pid, season, mission, progress, claimed) "
					"VALUES (%u, %u, %u, LEAST(%u, %u), 0) "
					"ON DUPLICATE KEY UPDATE progress = LEAST(%u, progress + %u)",
					pid, cache.season, it->first, cap, p.delta, cap, p.delta);
			if (now)
			{
				std::unique_ptr<SQLMsg> done(AccountDB::instance().DirectQuery(query));
			}
			else
				DBManager::instance().Query("%s", query);
			p.value = std::min<DWORD>(cap, p.value + p.delta);
			p.delta = 0;
		}
	}

	// Marks a reward as taken in the database, once: the core whose UPDATE
	// changes the row gives it, a second core (or a second click) finds it
	// taken. mission 0 is the season's final reward.
	bool TakeClaim(DWORD pid, DWORD season, DWORD mission)
	{
		char query[256];
		snprintf(query, sizeof(query),
				"INSERT IGNORE INTO player.battlepass_progress (pid, season, mission, progress, claimed) "
				"VALUES (%u, %u, %u, 0, 0)", pid, season, mission);
		std::unique_ptr<SQLMsg> ensure(AccountDB::instance().DirectQuery(query));
		snprintf(query, sizeof(query),
				"UPDATE player.battlepass_progress SET claimed=1 WHERE pid=%u AND season=%u AND mission=%u AND claimed=0",
				pid, season, mission);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		return msg.get() && msg->uiSQLErrno == 0 && msg->Get() && msg->Get()->uiAffectedRows == 1;
	}

	bool AllDone(Cache& cache)
	{
		if (s_vecMissions.empty())
			return false;
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			std::map<DWORD, Progress>::const_iterator it = cache.missions.find(m.id);
			if (it == cache.missions.end() || it->second.value + it->second.delta < m.count)
				return false;
		}
		return true;
	}

	void EnsureTick();

	bool HasReward(const Mission& m)
	{
		return m.rewardVnum[0] || m.rewardVnum[1] || m.rewardVnum[2];
	}

	// The database brought up to date for this player, then every mission
	// done and not yet rewarded rewarded - once, whichever core gets there.
	void Settle(LPCHARACTER ch, Cache& cache, bool announce)
	{
		const DWORD pid = ch->GetPlayerID();
		WriteDeltas(pid, cache, true);
		ReadProgress(pid, cache);
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			Progress& p = cache.missions[m.id];
			if (p.value < m.count || p.claimed)
				continue;
			if (!TakeClaim(pid, cache.season, m.id))
			{
				p.claimed = true;
				continue;
			}
			p.claimed = true;
			if (announce)
				ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: misja ukonczona!%s",
						HasReward(m) ? " Nagroda trafila do ekwipunku." : "");
			for (int r = 0; r < 3; ++r)
				if (m.rewardVnum[r])
					ch->AutoGiveItem(m.rewardVnum[r], (ITEM_COUNT)std::max<DWORD>(1, m.rewardCount[r]));
			sys_log(0, "BATTLEPASS: %s done mission %u", ch->GetName(), m.id);
			if (announce && AllDone(cache) && !cache.final.claimed)
				ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: wszystkie misje sezonu ukonczone - odbierz nagrode koncowa!");
		}
	}

	void Add(LPCHARACTER ch, BYTE type, DWORD target, long long amount)
	{
		if (amount <= 0 || !Eligible(ch))
			return;
		LoadMissions(false);
		bool any = false;
		for (size_t i = 0; i < s_vecMissions.size() && !any; ++i)
			any = s_vecMissions[i].type == type;
		if (!any)
			return;
		EnsureTick();
		Cache& cache = GetCache(ch);
		bool reached = false;
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			if (m.type != type || (m.target != 0 && m.target != target))
				continue;
			Progress& p = cache.missions[m.id];
			const DWORD have = p.value + p.delta;
			if (have >= m.count)
				continue;
			const long long room = (long long)(m.count - have);
			p.delta += (DWORD)(amount >= room ? room : amount);
			if (p.value + p.delta >= m.count)
				reached = true;
		}
		if (reached)
		{
			Settle(ch, cache, true);
			ch->ChatPacket(CHAT_TYPE_COMMAND, "BPUpdate");
		}
	}

	EVENTINFO(battlepass_tick_info)
	{
		int dummy;
	};

	// Every minute: a minute played for everybody in the game on this core,
	// this core's counts written, the departed forgotten, the missions re-read.
	EVENTFUNC(battlepass_tick)
	{
		LoadMissions(false);
		bool playtime = false;
		for (size_t i = 0; i < s_vecMissions.size() && !playtime; ++i)
			playtime = s_vecMissions[i].type == TYPE_PLAYTIME;
		if (playtime)
		{
			const DESC_MANAGER::DESC_SET& descs = DESC_MANAGER::instance().GetClientSet();
			for (DESC_MANAGER::DESC_SET::const_iterator it = descs.begin(); it != descs.end(); ++it)
			{
				LPDESC d = *it;
				LPCHARACTER ch = d ? d->GetCharacter() : NULL;
				if (ch && Eligible(ch) && ch->GetSectree())
					Add(ch, TYPE_PLAYTIME, 0, 1);
			}
		}
		for (std::map<DWORD, Cache>::iterator it = s_mapCaches.begin(); it != s_mapCaches.end(); )
		{
			WriteDeltas(it->first, it->second, false);
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first))
				s_mapCaches.erase(it++);
			else
				++it;
		}
		return PASSES_PER_SEC(60);
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		battlepass_tick_info* info = AllocEventInfo<battlepass_tick_info>();
		s_pkTick = event_create(battlepass_tick, info, PASSES_PER_SEC(60));
	}

	void SendWindow(LPCHARACTER ch)
	{
		LoadMissions(false);
		EnsureTick();
		Cache& cache = GetCache(ch);
		// What the other cores counted too, and anything done rewarded.
		Settle(ch, cache, true);
		// The final reward's first item where it always was, the other two after
		// the mission count (a window older than them reads the first alone).
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BPBegin %u %d %u %u %d %u %u %u %u %u", cache.season, DaysLeft(),
				s_adwFinalVnum[0], s_adwFinalCount[0], cache.final.claimed ? 1 : 0, (unsigned int)s_vecMissions.size(),
				s_adwFinalVnum[1], s_adwFinalCount[1], s_adwFinalVnum[2], s_adwFinalCount[2]);
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			const Progress& p = cache.missions[m.id];
			ch->ChatPacket(CHAT_TYPE_COMMAND, "BPMission %u %u %u %u %u %d %u %u %u %u %u %u %s", m.id,
					(unsigned int)m.type, m.target, m.count, std::min<DWORD>(m.count, p.value + p.delta),
					p.claimed ? 1 : 0,
					m.rewardVnum[0], m.rewardCount[0], m.rewardVnum[1], m.rewardCount[1], m.rewardVnum[2], m.rewardCount[2],
					m.nameHex.empty() ? "-" : m.nameHex.c_str());
			// The description on a line of its own: a chat command is at most
			// 512 bytes, and hex doubles it.
			if (!m.descHex.empty())
				ch->ChatPacket(CHAT_TYPE_COMMAND, "BPDesc %u %s", m.id, m.descHex.substr(0, 440).c_str());
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BPEnd %d", AllDone(cache) ? 1 : 0);
	}

	void Claim(LPCHARACTER ch, DWORD)
	{
		LoadMissions(false);
		Settle(ch, GetCache(ch), true);
		SendWindow(ch);
	}

	void ClaimFinal(LPCHARACTER ch)
	{
		LoadMissions(false);
		Cache& cache = GetCache(ch);
		Settle(ch, cache, false);
		if (cache.final.claimed)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: nagroda koncowa tego sezonu jest juz odebrana.");
			return;
		}
		if (!AllDone(cache))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: najpierw ukoncz wszystkie misje sezonu.");
			return;
		}
		if (!TakeClaim(ch->GetPlayerID(), cache.season, 0))
		{
			cache.final.claimed = true;
			ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: nagroda koncowa tego sezonu jest juz odebrana.");
			return;
		}
		cache.final.claimed = true;
		for (int r = 0; r < 3; ++r)
			if (s_adwFinalVnum[r])
				ch->AutoGiveItem(s_adwFinalVnum[r], (ITEM_COUNT)std::max<DWORD>(1, s_adwFinalCount[r]));
		sys_log(0, "BATTLEPASS: %s claimed the final reward of %u", ch->GetName(), cache.season);
		SendWindow(ch);
	}
}

// The engine's calls (server-patches/playerqol, MT2009_PLUS_BATTLE_PASS_V1).
void BattlePassOnKill(LPCHARACTER killer, LPCHARACTER victim)
{
	if (!killer || !victim || victim->IsPC() || !mt2009_battlepass::Eligible(killer))
		return;
	const DWORD race = victim->GetRaceNum();
	if (victim->IsStone())
		mt2009_battlepass::Add(killer, mt2009_battlepass::TYPE_METIN, race, 1);
	else
	{
		mt2009_battlepass::Add(killer, mt2009_battlepass::TYPE_MONSTER, race, 1);
		if (victim->GetMobRank() >= MOB_RANK_BOSS)
			mt2009_battlepass::Add(killer, mt2009_battlepass::TYPE_BOSS, race, 1);
	}
}

void BattlePassOnStat(LPCHARACTER ch, DWORD stat, long long value)
{
	using namespace mt2009_battlepass;
	BYTE type = 0;
	switch (stat)
	{
		case PLAYER_STATS_FISHING_FLAG: type = TYPE_FISH; break;
		case PLAYER_STATS_REFINE_SUCCESS_FLAG: type = TYPE_REFINE; break;
		case PLAYER_STATS_GOLD_FLAG: type = TYPE_YANG; break;
		case PLAYER_STATS_CHEST_FLAG: type = TYPE_CHEST; break;
		case PLAYER_STATS_HERBALISM_FLAG: type = TYPE_HERB; break;
		case PLAYER_STATS_MINING_FLAG: type = TYPE_MINING; break;
		case PLAYER_STATS_DUNGEON_FLAG: type = TYPE_DUNGEON; break;
		case PLAYER_STATS_QUESTBOOK_FLAG: type = TYPE_QUESTBOOK; break;
		default: return;
	}
	Add(ch, type, 0, value);
}

void BattlePassOnUse(LPCHARACTER ch, DWORD vnum)
{
	mt2009_battlepass::Add(ch, mt2009_battlepass::TYPE_USE_ITEM, vnum, 1);
}

// "/battlepass" (the window), "/battlepass odbierz <id>", "/battlepass nagroda",
// and for a GM "/battlepass przeladuj" (the missions table read now).
void BattlePassCommand(LPCHARACTER ch, const char* argument)
{
	if (!mt2009_battlepass::Eligible(ch))
		return;
	char sub[32], arg[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	one_argument(rest, arg, sizeof(arg));
	if (!*sub || !strcmp(sub, "otworz"))
		mt2009_battlepass::SendWindow(ch);
	else if (!strcmp(sub, "odbierz"))
	{
		DWORD id = 0;
		str_to_number(id, arg);
		mt2009_battlepass::Claim(ch, id);
	}
	else if (!strcmp(sub, "nagroda"))
		mt2009_battlepass::ClaimFinal(ch);
	else if (!strcmp(sub, "przeladuj") && ch->GetGMLevel() > GM_PLAYER)
	{
		mt2009_battlepass::LoadMissions(true);
		ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: misje wczytane ponownie (%u).",
				(unsigned int)mt2009_battlepass::s_vecMissions.size());
	}
}
