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
// Finishing every mission of the season gives the final reward, a Kupon SM
// (50) - 80017.
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
// Progress is kept per player in memory and written every minute, when it
// changed, and at a claim.
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

	const DWORD FINAL_REWARD_VNUM = 80017; // Kupon SM (50)
	const DWORD FINAL_REWARD_COUNT = 1;
	const DWORD MISSIONS_RELOAD_MS = 5 * 60 * 1000;

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

	struct Progress
	{
		DWORD value;
		bool claimed;
		bool dirty;
		Progress() : value(0), claimed(false), dirty(false) {}
	};

	struct Cache
	{
		DWORD season;
		std::map<DWORD, Progress> missions;
		Progress final;
		Cache() : season(0) {}
	};

	std::vector<Mission> s_vecMissions;
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
		s_vecMissions.swap(fresh);
		s_bMissionsLoaded = true;
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
		if (!EnsureTables())
			return cache;
		char query[160];
		snprintf(query, sizeof(query),
				"SELECT mission, progress, claimed FROM player.battlepass_progress WHERE pid=%u AND season=%u",
				pid, season);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (msg.get() && msg->uiSQLErrno == 0 && msg->Get() && msg->Get()->pSQLResult)
		{
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
		return cache;
	}

	void SaveProgress(DWORD pid, DWORD season, DWORD mission, Progress& p)
	{
		DBManager::instance().Query(
				"INSERT INTO player.battlepass_progress (pid, season, mission, progress, claimed) VALUES (%u, %u, %u, %u, %u) "
				"ON DUPLICATE KEY UPDATE progress=VALUES(progress), claimed=VALUES(claimed)",
				pid, season, mission, p.value, p.claimed ? 1 : 0);
		p.dirty = false;
	}

	void Flush(DWORD pid, Cache& cache)
	{
		for (std::map<DWORD, Progress>::iterator it = cache.missions.begin(); it != cache.missions.end(); ++it)
			if (it->second.dirty)
				SaveProgress(pid, cache.season, it->first, it->second);
		if (cache.final.dirty)
			SaveProgress(pid, cache.season, 0, cache.final);
	}

	bool AllDone(Cache& cache)
	{
		if (s_vecMissions.empty())
			return false;
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			std::map<DWORD, Progress>::const_iterator it = cache.missions.find(m.id);
			if (it == cache.missions.end() || it->second.value < m.count)
				return false;
		}
		return true;
	}

	void EnsureTick();

	bool HasReward(const Mission& m)
	{
		return m.rewardVnum[0] || m.rewardVnum[1] || m.rewardVnum[2];
	}

	// A mission's own rewards, the moment it is done (as the window the
	// operator chose has it: no button for them).
	void GiveRewards(LPCHARACTER ch, Cache& cache, const Mission& m, Progress& p)
	{
		if (p.claimed || !HasReward(m))
			return;
		p.claimed = true;
		SaveProgress(ch->GetPlayerID(), cache.season, m.id, p);
		for (int r = 0; r < 3; ++r)
			if (m.rewardVnum[r])
				ch->AutoGiveItem(m.rewardVnum[r], (ITEM_COUNT)std::max<DWORD>(1, m.rewardCount[r]));
		sys_log(0, "BATTLEPASS: %s done mission %u, rewards given", ch->GetName(), m.id);
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
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			if (m.type != type || (m.target != 0 && m.target != target))
				continue;
			Progress& p = cache.missions[m.id];
			if (p.value >= m.count)
				continue;
			const long long next = (long long)p.value + amount;
			p.value = next >= (long long)m.count ? m.count : (DWORD)next;
			p.dirty = true;
			if (p.value >= m.count)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: misja ukonczona!%s",
						HasReward(m) ? " Nagroda trafila do ekwipunku." : "");
				GiveRewards(ch, cache, m, p);
				if (AllDone(cache) && !cache.final.claimed)
					ch->ChatPacket(CHAT_TYPE_INFO, "Battle Pass: wszystkie misje sezonu ukonczone - odbierz nagrode koncowa!");
				ch->ChatPacket(CHAT_TYPE_COMMAND, "BPUpdate");
			}
		}
	}

	EVENTINFO(battlepass_tick_info)
	{
		int dummy;
	};

	// Every minute: a minute played for everybody in the game on this core,
	// what changed written, the departed forgotten, the missions re-read.
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
			Flush(it->first, it->second);
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
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BPBegin %u %d %u %u %d %u", cache.season, DaysLeft(),
				FINAL_REWARD_VNUM, FINAL_REWARD_COUNT, cache.final.claimed ? 1 : 0, (unsigned int)s_vecMissions.size());
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			const Progress& p = cache.missions[m.id];
			ch->ChatPacket(CHAT_TYPE_COMMAND, "BPMission %u %u %u %u %u %d %u %u %u %u %u %u %s", m.id,
					(unsigned int)m.type, m.target, m.count, p.value, p.claimed ? 1 : 0,
					m.rewardVnum[0], m.rewardCount[0], m.rewardVnum[1], m.rewardCount[1], m.rewardVnum[2], m.rewardCount[2],
					m.nameHex.empty() ? "-" : m.nameHex.c_str());
			// The description on a line of its own: a chat command is at most
			// 512 bytes, and hex doubles it.
			if (!m.descHex.empty())
				ch->ChatPacket(CHAT_TYPE_COMMAND, "BPDesc %u %s", m.id, m.descHex.substr(0, 440).c_str());
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BPEnd %d", AllDone(cache) ? 1 : 0);
	}

	void Claim(LPCHARACTER ch, DWORD missionId)
	{
		LoadMissions(false);
		Cache& cache = GetCache(ch);
		for (size_t i = 0; i < s_vecMissions.size(); ++i)
		{
			const Mission& m = s_vecMissions[i];
			if (m.id != missionId)
				continue;
			Progress& p = cache.missions[m.id];
			if (p.value < m.count)
				return;
			GiveRewards(ch, cache, m, p);
			SendWindow(ch);
			return;
		}
	}

	void ClaimFinal(LPCHARACTER ch)
	{
		LoadMissions(false);
		Cache& cache = GetCache(ch);
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
		cache.final.claimed = true;
		cache.final.value = 1;
		SaveProgress(ch->GetPlayerID(), cache.season, 0, cache.final);
		ch->AutoGiveItem(FINAL_REWARD_VNUM, FINAL_REWARD_COUNT);
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
