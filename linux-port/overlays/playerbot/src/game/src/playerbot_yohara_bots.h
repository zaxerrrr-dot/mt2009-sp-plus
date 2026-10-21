#ifndef __INC_METIN2_PLAYERBOT_YOHARA_BOTS_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_BOTS_H__

// MT2009_PLUS_BOT_YOHARA_HANDOVER_V1 - the bots between the game cores of one
// channel, and the owner's levelling route over them (21 October 2026, the
// decisions on plan-boty-yohara.md: "D1 - tak, zacznij od D1"; "do 110 lvl exp
// w Zakletym Lesie; mapy na 90 lvl tylko drop - Metiny i bossowie; 110-120 exp
// w Szczelinie Czasu - Zaklety Las").
//
// What there was: a bot lived on the core that logged it in (game1, the one
// that hosts the kingdoms' villages) and changed maps with ch->Show, which
// reaches only the maps of that process. The one thing that crossed was a
// player's companion (playerbot_sidekick.h): logged out where its owner was
// gone from and loaded by the core the owner stood on, placed on the owner's
// map by the load hook (CPlayerBotManager::PlaceLoadingSidekick, playerbotify's
// apply_sidekick_load_beside_owner). The channel moves do the same between the
// channels (common.playerbot_channel_assignment, ready_at). The test server,
// 19-21 October: 0 PLAYERBOT lines but the start-up ones in the syslog of
// game2 and game3 of both channels, no bot saved on any map of game2, game3 or
// the first core, and the companion followed its owner once (game1 only).
//
// The handover is that road for the population, through a table every core of
// the channel reads - common.playerbot_core_handover (pid, channel, the map and
// spot asked for, the purpose, a state, ready_at, updated_at):
//
//   * out: TransitionPlayerBotMap onto a map this core does not host - asked
//     by the bot's own plans (Zaklety Las, the Time Rift's plateau, a loot
//     map; from such a core, its way home) - becomes a row (state 1, ready in
//     PLAYERBOT_YOHARA_READY_S) and the bot logs out here at the top of the
//     next Update (saved by the engine as on any log-out). It is "away" here
//     until another core has it: Spawn and the top-up step over it.
//   * in: every PLAYERBOT_YOHARA_POLL_MS each core reads the channel's rows;
//     a ready row whose map this core hosts is claimed (state 2 for a stay,
//     the row deleted for a way home - one UPDATE/DELETE, so two cores never
//     both claim it) and the bot spawned. The load finds the bot saved on a
//     map this core does not host and asks PlaceLoadingSidekick, which gives
//     it the row's spot (PlacePlayerBotYoharaArrival). Home, the engine's own
//     rule puts it in its kingdom's first village (GetValidLocation fails on a
//     map not hosted here: EMPIRE_START_MAP).
//   * the stay: the core hosting a resident refreshes its row (updated_at)
//     every PLAYERBOT_YOHARA_HEARTBEAT_MS; a row not refreshed for
//     PLAYERBOT_YOHARA_STALE_S is no longer "away" anywhere - a resident that
//     logged out over there (the life schedule, a channel move, a crash) comes
//     back through its home core's top-up, in its first village.
//   * the belt: P2P_MANAGER::FindByPID in Spawn as ever, the claim's single
//     row, ready_at past the save.
//
// The route (the owner's):
//   * Zaklety Las (353, game3), PLAYERBOT_ZAKLETY_MIN_LEVEL (97) to 109: the
//     players' road - Orc Valley, the temple's guard (playerbot_ochao_bots.h),
//     the Temple of Ochao, the En-Tai Guardian (fought) and his Portal - and
//     the handover at the Portal; after PLAYERBOT_YOHARA_TEMPLE_WAIT_MS in the
//     temple with no Portal the bot takes the handover where it stands (the
//     Guardian falls rarely: 0 kills on the test server 19-21 October). In the
//     forest it hunts 24 spots (tools/arezzo_bot_map.py), its belt kept full
//     (the Las rule of 1 October: an expedition) and stays
//     PLAYERBOT_ZAKLETY_STAY_MIN; the frontier's exit (its Teleporter) is the
//     way home.
//   * Szczelina Czasu - Zaklety Las (SZC, 404), 110-119: the bot goes to
//     Plaskowyz Iluzji (397) by the handover and lives there between the
//     runs; the bots' dungeon runs on game3 (playerbot_dungeon_runs.h, the row
//     "jotun_szc") make parties of them at Statua Szczeliny Czasu, pay the
//     Zegarek Kieszonkowy (one from the bag, or its price), and inside they
//     only hunt - Metins and monsters, no missions, no keys (the owner's
//     correction of 21 October); the quest's hour ends the run, and after a
//     short rest the next one is called.
//   * loot runs (301-304): from 95, now and then, a bot leaves its village for
//     a 90-level map and breaks its Metins and fights its bosses, nothing else
//     (the combat policy's SERVICE_ONLY for the ordinary monsters), for
//     PLAYERBOT_YOHARA_LOOT_STAY_MS.
//   * Hydra and the Sung Ma maps stay closed (TransitionPlayerBotMap's
//     sungma_map refusal is before this file's route).
//
// The switches (.env / the Seban panel's env page; docker-compose passes them
// to the game container): PLAYERBOT_HANDOVER (1), PLAYERBOT_HANDOVER_CHANNELS
// ("1"), PLAYERBOT_ZAKLETY_MAX (30 a channel), PLAYERBOT_ZAKLETY_MIN_LEVEL
// (97), PLAYERBOT_SZC_MAX (18), PLAYERBOT_SZC_PARTIES (2), PLAYERBOT_LOOTRUN_MAX
// (6), PLAYERBOT_LOOTRUN_MAPS ("303,304" - the grids of 301/302 are 160/125
// MB). The event flag m2_bot_handover_off (a GM's /e, the panel's flags)
// stops every new handover and sends every resident home.
//
// The log: PLAYERBOT_HANDOVER (out, claimed, arrived, home, refused, cancel,
// census), PLAYERBOT_YOHARA (the temple, the stay, the restock, the loot runs,
// the Time Rift).
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it once, last (after playerbot_dungeon_runs.h and playerbot_ochao_bots.h).

namespace
{
	// ------------------------------------------------------------ the numbers

	const DWORD PLAYERBOT_YOHARA_POLL_MS = 5000;
	const DWORD PLAYERBOT_YOHARA_HEARTBEAT_MS = 60000;
	const int PLAYERBOT_YOHARA_STALE_S = 180;
	// A row is ready this long after it was written: the engine's save of the
	// log-out is through the db core before the other core asks for the load.
	const int PLAYERBOT_YOHARA_READY_S = 5;
	// A request nobody claimed is taken back after this (no core hosts the map,
	// the other core is full or down): the bot is this core's again.
	const DWORD PLAYERBOT_YOHARA_CLAIM_TIMEOUT_MS = 90000;
	// After a stay, a refused or taken-back request: no new trip for this long.
	const DWORD PLAYERBOT_YOHARA_TRIP_COOLDOWN_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_REFUSED_COOLDOWN_MS = 20 * 60 * 1000;
	// The temple: no Portal in this long since the bot came in for the forest -
	// it takes the handover where it stands.
	const DWORD PLAYERBOT_YOHARA_TEMPLE_WAIT_MS = 20 * 60 * 1000;
	const int PLAYERBOT_YOHARA_PORTAL_USE = 700;
	const int PLAYERBOT_YOHARA_PORTAL_NEAR = 2500;
	const int PLAYERBOT_YOHARA_PORTAL_WALK_MAX = 12000;
	const int PLAYERBOT_YOHARA_GUARDIAN_NEAR = 1500;
	// The stays.
	const DWORD PLAYERBOT_YOHARA_SZC_STAY_MS = 4 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_SZC_IDLE_MS = 40 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_SZC_LOST_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_LOOT_STAY_MS = 40 * 60 * 1000;
	// A loot run's draw in a village: at most once in this long a bot, this
	// many in a hundred, the plan kept this long for the road.
	const DWORD PLAYERBOT_YOHARA_LOOT_ROLL_MS = 30 * 60 * 1000;
	const int PLAYERBOT_YOHARA_LOOT_CHANCE = 15;
	const DWORD PLAYERBOT_YOHARA_LOOT_PLAN_MS = 20 * 60 * 1000;
	// The belt on the other core: kept at these (in stacks of 200).
	const size_t PLAYERBOT_YOHARA_BELT_RED = 200;
	const size_t PLAYERBOT_YOHARA_BELT_BLUE = 200;
	const DWORD PLAYERBOT_YOHARA_RESTOCK_MS = 10000;
	const DWORD PLAYERBOT_YOHARA_CENSUS_LOG_MS = 5 * 60 * 1000;
	// Zegarek Kieszonkowy (31147), 25 000 Yang at Handlarka Iluzji (yohara_crack.sql).
	const DWORD PLAYERBOT_YOHARA_SZC_WATCH = 31147;
	const long long PLAYERBOT_YOHARA_SZC_WATCH_PRICE = 25000LL;

	enum EPlayerBotYoharaPurpose
	{
		YOHARA_PURPOSE_NONE = 0,
		YOHARA_PURPOSE_HOME,
		YOHARA_PURPOSE_ZAKLETY,
		YOHARA_PURPOSE_SZC,
		YOHARA_PURPOSE_LOOT,
		YOHARA_PURPOSE_MAX
	};

	const char* PlayerBotYoharaPurposeName(int purpose)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_HOME: return "home";
			case YOHARA_PURPOSE_ZAKLETY: return "zaklety";
			case YOHARA_PURPOSE_SZC: return "szc";
			case YOHARA_PURPOSE_LOOT: return "loot";
			default: return "none";
		}
	}

	int ParsePlayerBotYoharaPurpose(const char* s)
	{
		if (!s)
			return YOHARA_PURPOSE_NONE;
		for (int i = YOHARA_PURPOSE_HOME; i < YOHARA_PURPOSE_MAX; ++i)
			if (!strcmp(s, PlayerBotYoharaPurposeName(i)))
				return i;
		return YOHARA_PURPOSE_NONE;
	}

	// ------------------------------------------------------------ the switches

	struct TPlayerBotYoharaConfig
	{
		bool on;
		std::set<int> channels;
		int zakletyMax, zakletyMinLevel, zakletyStayMin;
		int szcMax, szcParties;
		int lootMax;
		std::vector<long> lootMaps;
	};

	int ReadPlayerBotYoharaEnvInt(const char* name, int def, int lo, int hi)
	{
		const char* v = std::getenv(name);
		if (!v || !*v)
			return def;
		const int n = atoi(v);
		return n < lo ? lo : (n > hi ? hi : n);
	}

	void ReadPlayerBotYoharaEnvList(const char* name, const char* def, std::vector<long>& out)
	{
		const char* v = std::getenv(name);
		const std::string s = v && *v ? v : def;
		long n = -1;
		for (size_t i = 0; i <= s.size(); ++i)
		{
			if (i < s.size() && s[i] >= '0' && s[i] <= '9')
				n = (n < 0 ? 0 : n * 10) + (s[i] - '0');
			else if (n >= 0)
			{
				out.push_back(n);
				n = -1;
			}
		}
	}

	const TPlayerBotYoharaConfig& GetPlayerBotYoharaConfig()
	{
		static TPlayerBotYoharaConfig s_cfg;
		static bool s_loaded = false;
		if (s_loaded)
			return s_cfg;
		s_loaded = true;
		s_cfg.on = ReadPlayerBotYoharaEnvInt("PLAYERBOT_HANDOVER", 1, 0, 1) != 0;
		std::vector<long> ch;
		ReadPlayerBotYoharaEnvList("PLAYERBOT_HANDOVER_CHANNELS", "1", ch);
		for (size_t i = 0; i < ch.size(); ++i)
			s_cfg.channels.insert((int)ch[i]);
		s_cfg.zakletyMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MAX", 30, 0, 300);
		s_cfg.zakletyMinLevel = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MIN_LEVEL", PLAYERBOT_ZAKLETY_MIN_LEVEL,
				PLAYERBOT_OCHAO_MIN_LEVEL, PLAYERBOT_ZAKLETY_MAX_LEVEL);
		s_cfg.zakletyStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_STAY_MIN", 120, 20, 600);
		s_cfg.szcMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SZC_MAX", 18, 0, 200);
		s_cfg.szcParties = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SZC_PARTIES", 2, 0, 20);
		s_cfg.lootMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_LOOTRUN_MAX", 6, 0, 200);
		std::vector<long> maps;
		ReadPlayerBotYoharaEnvList("PLAYERBOT_LOOTRUN_MAPS", "303,304", maps);
		for (size_t i = 0; i < maps.size(); ++i)
			if (maps[i] >= 301 && maps[i] <= 304 &&
					std::find(s_cfg.lootMaps.begin(), s_cfg.lootMaps.end(), maps[i]) == s_cfg.lootMaps.end())
				s_cfg.lootMaps.push_back(maps[i]);
		std::string chans, loot;
		for (std::set<int>::const_iterator i = s_cfg.channels.begin(); i != s_cfg.channels.end(); ++i)
			chans += (chans.empty() ? "" : ",") + std::to_string(*i);
		for (size_t i = 0; i < s_cfg.lootMaps.size(); ++i)
			loot += (loot.empty() ? "" : ",") + std::to_string(s_cfg.lootMaps[i]);
		sys_log(0, "PLAYERBOT_HANDOVER: config on=%d channels=%s zaklety_max=%d zaklety_min_level=%d zaklety_stay_min=%d "
				"szc_max=%d szc_parties=%d loot_max=%d loot_maps=%s channel_here=%u",
				s_cfg.on ? 1 : 0, chans.c_str(), s_cfg.zakletyMax, s_cfg.zakletyMinLevel, s_cfg.zakletyStayMin,
				s_cfg.szcMax, s_cfg.szcParties, s_cfg.lootMax, loot.c_str(), (unsigned int)g_bChannel);
		return s_cfg;
	}

	bool IsPlayerBotYoharaSwitchedOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_handover_off") != 0;
	}

	// New trips out of this core: the switch, this channel, and no event flag.
	bool IsPlayerBotYoharaOn()
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		return cfg.on && cfg.channels.count((int)g_bChannel) != 0 && !IsPlayerBotYoharaSwitchedOff();
	}

	bool IsPlayerBotYoharaLootMap(long mapIndex)
	{
		const std::vector<long>& maps = GetPlayerBotYoharaConfig().lootMaps;
		return std::find(maps.begin(), maps.end(), mapIndex) != maps.end();
	}

	// ------------------------------------------------------------ the state

	// A request out of this core, until another core has the bot (or not).
	struct TPlayerBotYoharaOut
	{
		DWORD dwAt;
		int iPurpose;
		long lMap;
		TPlayerBotYoharaOut() : dwAt(0), iPurpose(0), lMap(0) {}
	};
	// A bot this core claimed and spawned, until it stands here.
	struct TPlayerBotYoharaArrival
	{
		long lMap, lX, lY;
		int iPurpose;
		DWORD dwAt;
		TPlayerBotYoharaArrival() : lMap(0), lX(0), lY(0), iPurpose(0), dwAt(0) {}
	};
	// A bot living on this core for a purpose (this core is not its home).
	struct TPlayerBotYoharaResident
	{
		int iPurpose;
		long lMap;
		DWORD dwArrived, dwLastRun, dwNextRestock, dwOffRunSince;
		TPlayerBotYoharaResident() : iPurpose(0), lMap(0), dwArrived(0), dwLastRun(0), dwNextRestock(0), dwOffRunSince(0) {}
	};
	// A bot on its way into Zaklety Las through the temple (the home core).
	struct TPlayerBotYoharaTemple
	{
		DWORD dwSince, dwLastLog;
		DWORD dwPortalVID;
		BYTE bPhase;
		TPlayerBotYoharaTemple() : dwSince(0), dwLastLog(0), dwPortalVID(0), bPhase(0) {}
	};
	struct TPlayerBotYoharaLootPlan
	{
		long lMap;
		DWORD dwUntil;
		TPlayerBotYoharaLootPlan() : lMap(0), dwUntil(0) {}
	};
	struct TPlayerBotYoharaLeave
	{
		long lMap;
		int iPurpose;
		TPlayerBotYoharaLeave() : lMap(0), iPurpose(0) {}
	};

	std::map<DWORD, TPlayerBotYoharaOut> s_mapPlayerBotYoharaOut;
	std::map<DWORD, TPlayerBotYoharaArrival> s_mapPlayerBotYoharaArrival;
	std::map<DWORD, TPlayerBotYoharaResident> s_mapPlayerBotYoharaResident;
	std::map<DWORD, TPlayerBotYoharaTemple> s_mapPlayerBotYoharaTemple;
	std::map<DWORD, TPlayerBotYoharaLootPlan> s_mapPlayerBotYoharaLootPlan;
	std::map<DWORD, DWORD> s_mapPlayerBotYoharaLootRolled;
	std::map<DWORD, DWORD> s_mapPlayerBotYoharaCooldown;
	std::map<DWORD, TPlayerBotYoharaLeave> s_mapPlayerBotYoharaLeaving;
	// The channel's rows as the last poll read them: away from this core (on
	// another one, or on the way) - Spawn and the top-up step over these.
	std::set<DWORD> s_setPlayerBotYoharaAway;
	// The channel's count a purpose, the last poll's: requested + staying.
	int s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_MAX] = { 0 };
	bool s_bPlayerBotYoharaTableReady = false;
	DWORD s_dwPlayerBotYoharaNextPoll = 0;
	DWORD s_dwPlayerBotYoharaNextHeartbeat = 0;
	DWORD s_dwPlayerBotYoharaNextCensusLog = 0;
	unsigned int s_uPlayerBotYoharaOutCount = 0, s_uPlayerBotYoharaInCount = 0, s_uPlayerBotYoharaHomeCount = 0;
	unsigned int s_uPlayerBotYoharaRefusedCount = 0, s_uPlayerBotYoharaCancelCount = 0;

	// A bot of this core's claims that stands here is a resident from its first
	// tick (SettlePlayerBotYoharaArrivals does the rest at the top of Update).
	TPlayerBotYoharaResident* FindPlayerBotYoharaResident(DWORD pid)
	{
		std::map<DWORD, TPlayerBotYoharaResident>::iterator r = s_mapPlayerBotYoharaResident.find(pid);
		if (r != s_mapPlayerBotYoharaResident.end())
			return &r->second;
		std::map<DWORD, TPlayerBotYoharaArrival>::const_iterator a = s_mapPlayerBotYoharaArrival.find(pid);
		if (a == s_mapPlayerBotYoharaArrival.end() || a->second.iPurpose == YOHARA_PURPOSE_HOME)
			return NULL;
		TPlayerBotYoharaResident& res = s_mapPlayerBotYoharaResident[pid];
		res.iPurpose = a->second.iPurpose;
		res.lMap = a->second.lMap;
		res.dwArrived = get_dword_time();
		return &res;
	}

	bool IsPlayerBotYoharaAway(DWORD pid)
	{
		return s_setPlayerBotYoharaAway.count(pid) != 0 || s_mapPlayerBotYoharaOut.count(pid) != 0 ||
				s_mapPlayerBotYoharaLeaving.count(pid) != 0;
	}

	bool IsPlayerBotYoharaLeaving(DWORD pid)
	{
		return s_mapPlayerBotYoharaLeaving.count(pid) != 0;
	}

	bool IsPlayerBotYoharaSzcResident(DWORD pid)
	{
		std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.find(pid);
		return r != s_mapPlayerBotYoharaResident.end() && r->second.iPurpose == YOHARA_PURPOSE_SZC;
	}

	DWORD GetPlayerBotYoharaStayMs(long mapIndex)
	{
		return mapIndex == PLAYERBOT_MAP_ZAKLETY ? (DWORD)GetPlayerBotYoharaConfig().zakletyStayMin * 60000U : 0;
	}

	// The Time Rift's runs at once on this core (playerbot_dungeon_runs.h).
	int GetPlayerBotYoharaSzcParties()
	{
		return GetPlayerBotYoharaConfig().szcParties;
	}

	// A map of another core this core's bots go to (GetPlayerBotFrontierMapForLevel's filter).
	bool IsPlayerBotYoharaRemoteFrontier(long mapIndex)
	{
		if (!IsPlayerBotYoharaOn() || IsPlayerBotMapHostedHere(mapIndex))
			return false;
		return mapIndex == PLAYERBOT_MAP_ZAKLETY || mapIndex == PLAYERBOT_MAP_SZC_PLATEAU || IsPlayerBotYoharaLootMap(mapIndex);
	}

	// Who may cross: the population's ordinary bots, not with a person.
	bool IsPlayerBotYoharaEligible(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotSidekickPID(pid) || IsPlayerBotShouterPID(pid) || IsPlayerBotMedalShouterPID(pid) ||
				IsPlayerBotTakeoverHold(pid) || IsPlayerBotRetiring(pid) ||
				IsPlayerBotArezzoDungeonReservedPID(pid) || IsPlayerBotArezzoCohortPID(pid))
			return false;
		if (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()))
			return false;
		return ch->GetGMLevel() <= GM_PLAYER;
	}

	// This core is the bot's home: it hosts the bot's first village.
	bool IsPlayerBotYoharaHomeCore(LPCHARACTER ch)
	{
		return ch && IsPlayerBotMapHostedHere(GetPlayerBotHomeMap(ch, playerbot_empire_rules::MAP_ROLE_M1));
	}

	// ------------------------------------------------------------ the table

	bool EnsurePlayerBotYoharaTable()
	{
		if (s_bPlayerBotYoharaTableReady)
			return true;
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS common.playerbot_core_handover ("
				"pid INT UNSIGNED NOT NULL PRIMARY KEY, channel TINYINT UNSIGNED NOT NULL, "
				"target_map INT NOT NULL, x INT NOT NULL, y INT NOT NULL, from_map INT NOT NULL DEFAULT 0, "
				"purpose VARCHAR(16) NOT NULL DEFAULT '', state TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"reason VARCHAR(48) NOT NULL DEFAULT '', ready_at DATETIME NOT NULL, "
				"updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
				"KEY channel_state (channel, state)) ENGINE=InnoDB"));
		s_bPlayerBotYoharaTableReady = msg.get() && msg->uiSQLErrno == 0;
		if (!s_bPlayerBotYoharaTableReady)
			sys_err("PLAYERBOT_HANDOVER: common.playerbot_core_handover cannot be made");
		return s_bPlayerBotYoharaTableReady;
	}

	unsigned int RunPlayerBotYoharaSql(const char* query)
	{
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get())
			return 0;
		return (unsigned int)msg->Get()->uiAffectedRows;
	}

	// ------------------------------------------------------------ out

	// The bot asked for a map another core hosts: the row, out of its party
	// and its stall, and out of this core at the top of the next Update.
	bool RequestPlayerBotYoharaHandover(LPCHARACTER ch, TPlayerBotAIState& state, long targetMap, long x, long y,
			int purpose, const char* reason, DWORD dwNow)
	{
		if (!ch || !EnsurePlayerBotYoharaTable())
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (s_mapPlayerBotYoharaLeaving.count(pid))
			return true;
		char safeReason[48];
		strlcpy(safeReason, reason ? reason : "?", sizeof(safeReason));
		for (char* c = safeReason; *c; ++c)
			if (!isalnum((unsigned char)*c) && *c != '_' && *c != ':' && *c != '-')
				*c = '_';
		char query[640];
		snprintf(query, sizeof(query),
				"REPLACE INTO common.playerbot_core_handover (pid, channel, target_map, x, y, from_map, purpose, state, reason, "
				"ready_at, updated_at) VALUES (%u, %u, %ld, %ld, %ld, %ld, '%s', 1, '%s', "
				"DATE_ADD(NOW(), INTERVAL %d SECOND), NOW())",
				pid, (unsigned int)g_bChannel, targetMap, x, y, ch->GetMapIndex(), PlayerBotYoharaPurposeName(purpose),
				safeReason, PLAYERBOT_YOHARA_READY_S);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0)
		{
			PlayerBotLogThrottled("handover_sql", dwNow, "PLAYERBOT_HANDOVER: request not written pid=%u name=%s to=%ld",
					pid, ch->GetName(), targetMap);
			return false;
		}
		if (ch->GetParty())
			LeavePlayerBotParty(ch);
		ClosePlayerBotShop(ch, state, dwNow, "core_handover");
		ClearPlayerBotRoute(state, true);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		TPlayerBotYoharaLeave& leave = s_mapPlayerBotYoharaLeaving[pid];
		leave.lMap = targetMap;
		leave.iPurpose = purpose;
		if (purpose != YOHARA_PURPOSE_HOME)
		{
			TPlayerBotYoharaOut& out = s_mapPlayerBotYoharaOut[pid];
			out.dwAt = dwNow;
			out.iPurpose = purpose;
			out.lMap = targetMap;
			++s_aiPlayerBotYoharaCensus[purpose];
			s_mapPlayerBotYoharaLootPlan.erase(pid);
		}
		s_mapPlayerBotYoharaTemple.erase(pid);
		++s_uPlayerBotYoharaOutCount;
		sys_log(0, "PLAYERBOT_HANDOVER: out pid=%u name=%s level=%u channel=%u from=%ld pos=(%ld,%ld) to=%ld spot=(%ld,%ld) purpose=%s reason=%s",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)g_bChannel, ch->GetMapIndex(),
				ch->GetX(), ch->GetY(), targetMap, x, y, PlayerBotYoharaPurposeName(purpose), safeReason);
		return true;
	}

	// A resident's way home: its second village (the frontier's exit), by the
	// handover the route makes of it.
	bool SendPlayerBotYoharaHome(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow, const char* why)
	{
		long destMap = 0, destX = 0, destY = 0;
		if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M2, destMap, destX, destY))
			return false;
		std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.find(ch->GetPlayerID());
		sys_log(0, "PLAYERBOT_YOHARA: goes home pid=%u name=%s level=%u map=%ld purpose=%s stay_s=%u why=%s",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(),
				r != s_mapPlayerBotYoharaResident.end() ? PlayerBotYoharaPurposeName(r->second.iPurpose) : "-",
				r != s_mapPlayerBotYoharaResident.end() && r->second.dwArrived ? (dwNow - r->second.dwArrived) / 1000 : 0,
				why);
		return TransitionPlayerBotMap(ch, state, destMap, destX, destY, dwNow, why);
	}

	// ------------------------------------------------------------ the route

	int RoutePlayerBotYoharaTransition(LPCHARACTER ch, TPlayerBotAIState& state, long targetMap,
			long targetX, long targetY, DWORD dwNow, const char* reason)
	{
		if (!ch || targetMap <= 0)
			return -1;
		const long base = targetMap >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? targetMap / 10000 : targetMap;
		if (IsPlayerBotMapHostedHere(base) || !IsPlayerBotYoharaEligible(ch))
			return -1;
		const DWORD pid = ch->GetPlayerID();
		// A resident (or a bot standing on a core that is not its home): every
		// map it cannot reach here is the way home.
		if (FindPlayerBotYoharaResident(pid) || !IsPlayerBotYoharaHomeCore(ch))
			return RequestPlayerBotYoharaHandover(ch, state, base, targetX, targetY, YOHARA_PURPOSE_HOME,
					reason ? reason : "home", dwNow) ? 1 : 0;
		if (!IsPlayerBotYoharaOn())
			return -1;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		int purpose = YOHARA_PURPOSE_NONE;
		int cap = 0;
		if (base == PLAYERBOT_MAP_ZAKLETY)
		{
			purpose = YOHARA_PURPOSE_ZAKLETY;
			cap = cfg.zakletyMax;
		}
		else if (base == PLAYERBOT_MAP_SZC_PLATEAU)
		{
			purpose = YOHARA_PURPOSE_SZC;
			cap = cfg.szcMax;
		}
		else if (IsPlayerBotYoharaLootMap(base))
		{
			purpose = YOHARA_PURPOSE_LOOT;
			cap = cfg.lootMax;
		}
		if (purpose == YOHARA_PURPOSE_NONE)
			return -1;
		if (s_aiPlayerBotYoharaCensus[purpose] >= cap)
		{
			s_mapPlayerBotYoharaCooldown[pid] = dwNow + PLAYERBOT_YOHARA_REFUSED_COOLDOWN_MS;
			s_mapPlayerBotYoharaLootPlan.erase(pid);
			s_mapPlayerBotYoharaTemple.erase(pid);
			PlayerBotLogThrottled("handover_cap", dwNow, "PLAYERBOT_HANDOVER: refused pid=%u name=%s to=%ld purpose=%s why=cap census=%d cap=%d",
					pid, ch->GetName(), base, PlayerBotYoharaPurposeName(purpose), s_aiPlayerBotYoharaCensus[purpose], cap);
			s_szPlayerBotTransitionRefusal = "yohara_cap";
			return 0;
		}
		if (purpose == YOHARA_PURPOSE_ZAKLETY)
		{
			// The forest only through the temple's Portal (or its wait), from the temple.
			if (ch->GetMapIndex() == PLAYERBOT_MAP_OCHAO)
			{
				if (reason && (!strcmp(reason, "zaklety_portal") || !strcmp(reason, "zaklety_temple_wait")))
					return RequestPlayerBotYoharaHandover(ch, state, base, PLAYERBOT_ZAKLETY_ARRIVAL_X,
							PLAYERBOT_ZAKLETY_ARRIVAL_Y, purpose, reason, dwNow) ? 1 : 0;
				return 1;	// the temple pass walks it to the Guardian and his Portal
			}
			if (!IsPlayerBotOchaoHosted())
				return -1;
			return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_OCHAO, PLAYERBOT_OCHAO_ARRIVAL_X,
					PLAYERBOT_OCHAO_ARRIVAL_Y, dwNow, "zaklety_via_ochao") ? 1 : 0;
		}
		long x = targetX, y = targetY;
		GetPlayerBotFrontierArrival(base, x, y);
		return RequestPlayerBotYoharaHandover(ch, state, base, x, y, purpose, reason, dwNow) ? 1 : 0;
	}

	// ------------------------------------------------------------ the draw

	long GetPlayerBotYoharaLootPlan(LPCHARACTER ch, DWORD dwNow)
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotYoharaLootPlan>::iterator plan = s_mapPlayerBotYoharaLootPlan.find(pid);
		if (plan != s_mapPlayerBotYoharaLootPlan.end())
		{
			if ((int)(plan->second.dwUntil - dwNow) > 0 && IsPlayerBotYoharaLootMap(plan->second.lMap))
				return plan->second.lMap;
			s_mapPlayerBotYoharaLootPlan.erase(plan);
		}
		if (cfg.lootMax <= 0 || cfg.lootMaps.empty() || ch->GetLevel() < PLAYERBOT_YOHARA_LOOT_MIN_LEVEL ||
				!IsPlayerBotVillageMap(ch->GetMapIndex()) || s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_LOOT] >= cfg.lootMax)
			return 0;
		DWORD& rolled = s_mapPlayerBotYoharaLootRolled[pid];
		if (rolled != 0 && (int)(dwNow - rolled) < (int)PLAYERBOT_YOHARA_LOOT_ROLL_MS)
			return 0;
		rolled = dwNow;
		if (number(1, 100) > PLAYERBOT_YOHARA_LOOT_CHANCE)
			return 0;
		TPlayerBotYoharaLootPlan& p = s_mapPlayerBotYoharaLootPlan[pid];
		p.lMap = cfg.lootMaps[number(0, (int)cfg.lootMaps.size() - 1)];
		p.dwUntil = dwNow + PLAYERBOT_YOHARA_LOOT_PLAN_MS;
		sys_log(0, "PLAYERBOT_YOHARA: loot run planned pid=%u name=%s level=%u map=%ld census=%d/%d",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), p.lMap, s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_LOOT],
				cfg.lootMax);
		return p.lMap;
	}

	// The frontier draw's answer for the owner's route (GetPlayerBotFrontierMapForLevelRaw),
	// or 0 for the usual draw.
	long GetPlayerBotYoharaFrontier(LPCHARACTER ch, bool stoneHunter)
	{
		if (!ch)
			return 0;
		const DWORD pid = ch->GetPlayerID();
		const int level = ch->GetLevel();
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		const DWORD dwNow = get_dword_time();
		// On the other core: the purpose it came for, while it lasts.
		const TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(pid);
		if (r)
		{
			if (!cfg.on || IsPlayerBotYoharaSwitchedOff())
				return 0;
			switch (r->iPurpose)
			{
				case YOHARA_PURPOSE_ZAKLETY:
					return level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL &&
							IsPlayerBotMapHostedHere(PLAYERBOT_MAP_ZAKLETY) ? PLAYERBOT_MAP_ZAKLETY : 0;
				case YOHARA_PURPOSE_SZC:
					return level >= PLAYERBOT_SZC_MIN_LEVEL && level <= PLAYERBOT_SZC_MAX_LEVEL &&
							IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SZC_PLATEAU) ? PLAYERBOT_MAP_SZC_PLATEAU : 0;
				case YOHARA_PURPOSE_LOOT:
					return IsPlayerBotMapHostedHere(r->lMap) && dwNow - r->dwArrived < PLAYERBOT_YOHARA_LOOT_STAY_MS
							? r->lMap : 0;
				default:
					return 0;
			}
		}
		if (!IsPlayerBotYoharaOn() || !IsPlayerBotYoharaHomeCore(ch) || !IsPlayerBotYoharaEligible(ch))
			return 0;
		std::map<DWORD, DWORD>::iterator cd = s_mapPlayerBotYoharaCooldown.find(pid);
		if (cd != s_mapPlayerBotYoharaCooldown.end())
		{
			if ((int)(cd->second - dwNow) > 0)
				return 0;
			s_mapPlayerBotYoharaCooldown.erase(cd);
		}
		// A loot run now and then (in a village, at most every half hour a bot).
		const long loot = GetPlayerBotYoharaLootPlan(ch, dwNow);
		if (loot != 0)
			return loot;
		// The Time Rift: three in four of the band, while there is room.
		if (level >= PLAYERBOT_SZC_MIN_LEVEL && level <= PLAYERBOT_SZC_MAX_LEVEL && cfg.szcMax > 0 &&
				s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SZC] < cfg.szcMax &&
				PlayerBotNavHash(pid ^ 0x535a4331U) % 4U != 0)
			return PLAYERBOT_MAP_SZC_PLATEAU;
		// Zaklety Las: two in three of the band, while there is room (and a
		// bot already on its way through the temple keeps it).
		const bool inTemple = s_mapPlayerBotYoharaTemple.count(pid) != 0;
		if (level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL && cfg.zakletyMax > 0 &&
				IsPlayerBotOchaoHosted() &&
				(inTemple || s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_ZAKLETY] < cfg.zakletyMax) &&
				PlayerBotNavHash(pid ^ 0x5a4b4c53U) % 3U != 0)
			return PLAYERBOT_MAP_ZAKLETY;
		(void)stoneHunter;
		return 0;
	}

	bool IsPlayerBotYoharaBoundForZaklety(LPCHARACTER ch)
	{
		return ch && !IsPlayerBotMapHostedHere(PLAYERBOT_MAP_ZAKLETY) && IsPlayerBotYoharaOn() &&
				GetPlayerBotFrontierMapForLevel(ch) == PLAYERBOT_MAP_ZAKLETY;
	}

	bool IsPlayerBotYoharaLootRunHere(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		const TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(ch->GetPlayerID());
		return r && r->iPurpose == YOHARA_PURPOSE_LOOT && ch->GetMapIndex() == r->lMap;
	}

	// ------------------------------------------------------------ the hubs

	// tools/arezzo_bot_map.py gen metin2_map_dawnmist_dungeon_01 353 (21 October; walkable 16.7 %, one piece
	// holding 98.8 % of it; the walk 1.51 times the straight line at the median, 2.09 at p90 - ridges and
	// gullies): the regen's 346 spawn lines in 24 spots, densest first, each with five open cells all round;
	// the last row Wladca En-Tai (6407, boss 112, group 6318, boss.txt 587,97) for a party.
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_ZAKLETY_HUBS[] = {
		{ 827350, 1465350, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 27 spawn lines
		{ 805650, 1420250, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 23 spawn lines
		{ 824750, 1483050, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 19 spawn lines
		{ 784650, 1469750, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 19 spawn lines
		{ 821550, 1461350, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 13 spawn lines
		{ 831150, 1447350, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 13 spawn lines
		{ 787750, 1477250, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 13 spawn lines
		{ 804450, 1497550, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 12 spawn lines
		{ 793650, 1433850, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 12 spawn lines
		{ 778750, 1450950, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 12 spawn lines
		{ 808750, 1447450, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 11 spawn lines
		{ 818250, 1444850, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 11 spawn lines
		{ 795750, 1486050, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 9 spawn lines
		{ 829450, 1434550, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 9 spawn lines
		{ 790950, 1470550, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 9 spawn lines
		{ 799850, 1442250, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 9 spawn lines
		{ 777850, 1439350, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 9 spawn lines
		{ 826050, 1417450, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 8 spawn lines
		{ 827350, 1473850, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 7 spawn lines
		{ 827850, 1454750, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 7 spawn lines
		{ 812950, 1493050, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 6 spawn lines
		{ 795350, 1457050, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 6 spawn lines
		{ 802150, 1426150, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 6 spawn lines
		{ 801350, 1450550, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 5 spawn lines
		{ 826700, 1417700, PLAYERBOT_OCHAO_MIN_LEVEL, 255, true, 6407 },	// Wladca En-Tai (boss.txt)
	};

	// MT2009_PLUS_BOT_YOHARA_LOOTRUN_V1: the 90-level maps' Metins (stone.txt) and bosses (boss.txt),
	// tools/yohara_bot_lootrun_map.py (21 October) - a boss row is chosen while its boss stands.
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_301[] = {
		{ 1111750, 1725450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3008 },	// boss 3008 cell 881,614
		{ 1067450, 1701450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3009 },	// boss 3009 cell 434,374
		{ 1134650, 1695950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3028 },	// boss 3028 cell 1106,319
		{ 1109150, 1701650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3029 },	// boss 3029 cell 839,380
		{ 1162650, 1796550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3058 },	// boss 3058 cell 1386,1325
		{ 1047750, 1739650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8051 cell 237,756
		{ 1069050, 1706350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8051 cell 450,423
		{ 1113050, 1723950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8051 cell 890,599
		{ 1048650, 1692550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8051 cell 246,285
		{ 1156150, 1688450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 1321,244
		{ 1161350, 1791050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 1373,1270
		{ 1138450, 1750950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 1144,869
		{ 1064350, 1748050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 403,840
		{ 1079850, 1721750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 558,577
		{ 1128250, 1789050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1042,1250
		{ 1158850, 1766750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1348,1027
		{ 1155850, 1684950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1318,209
		{ 1050350, 1713050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 263,490
		{ 1094750, 1747050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 707,830
		{ 1145250, 1789650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1212,1256
		{ 1163150, 1749750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1391,857
		{ 1141050, 1740950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1170,769
	};
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_302[] = {
		{ 1318750, 1699750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3098 },	// boss 3098 cell 1411,357
		{ 1327450, 1686650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3099 },	// boss 3099 cell 1498,226
		{ 1279950, 1733250, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3038 },	// boss 3038 cell 1023,692
		{ 1255250, 1699050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3039 },	// boss 3039 cell 776,351
		{ 1193350, 1692650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8054 cell 157,286
		{ 1332650, 1740150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 1550,761
		{ 1324050, 1687350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 1469,229
		{ 1234850, 1746950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 572,829
		{ 1283050, 1688950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 1054,249
		{ 1255050, 1702550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 774,385
		{ 1277850, 1745950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8056 cell 1002,819
		{ 1281150, 1683950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1035,199
		{ 1321350, 1699350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1437,353
		{ 1276650, 1744150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 990,801
		{ 1231450, 1746050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 538,820
		{ 1191450, 1684750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 138,207
		{ 1298150, 1696950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1205,329
		{ 1332050, 1736150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 1544,721
		{ 1251650, 1736050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 740,720
		{ 1205750, 1723350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 281,593
		{ 1224450, 1682650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 468,186
	};
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_303[] = {
		{ 1073450, 1596850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3048 },	// boss 3048 cell 238,864
		{ 1064250, 1599950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3049 },	// boss 3049 cell 146,895
		{ 1078450, 1556150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3078 },	// boss 3078 cell 288,457
		{ 1070550, 1546350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3079 },	// boss 3079 cell 209,359
		{ 1112250, 1621450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3058 },	// boss 3058 cell 626,1110
		{ 1115550, 1552850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3059 },	// boss 3059 cell 659,424
		{ 1097650, 1527150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 480,167
		{ 1101850, 1551550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 522,411
		{ 1103450, 1581850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 538,714
		{ 1110150, 1622150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8052 cell 605,1117
		{ 1069250, 1533650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8053 cell 196,232
		{ 1068650, 1568450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8053 cell 190,580
		{ 1067350, 1619150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8053 cell 177,1087
		{ 1108350, 1525550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 587,151
		{ 1082050, 1537150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 324,267
		{ 1110450, 1598550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 608,881
		{ 1095750, 1645450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 461,1350
		{ 1114450, 1552650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 648,422
		{ 1105350, 1577750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 557,673
		{ 1092550, 1614150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 429,1037
		{ 1113050, 1649650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 634,1392
		{ 1081150, 1641550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 315,1311
	};
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_304[] = {
		{ 1164050, 1619850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3068 },	// boss 3068 cell 376,1094
		{ 1161050, 1594550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3069 },	// boss 3069 cell 346,841
		{ 1137750, 1521350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3088 },	// boss 3088 cell 113,109
		{ 1187550, 1624350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3089 },	// boss 3089 cell 611,1139
		{ 1179750, 1590550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3018 },	// boss 3018 cell 533,801
		{ 1217450, 1519250, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3019 },	// boss 3019 cell 910,88
		{ 1141750, 1530850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8055 cell 153,204
		{ 1149750, 1563550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8055 cell 233,531
		{ 1190650, 1623350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8055 cell 642,1129
		{ 1217050, 1645450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8055 cell 906,1350
		{ 1214350, 1522450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8054 cell 879,120
		{ 1217250, 1568050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8054 cell 908,576
		{ 1199550, 1573650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 8054 cell 731,632
		{ 1142550, 1646750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 141,1343
		{ 1149050, 1589750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 226,793
		{ 1151550, 1522850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 251,124
		{ 1217950, 1525750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 915,153
		{ 1197450, 1651750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 710,1413
		{ 1147150, 1623450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 207,1130
		{ 1150750, 1555250, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 243,448
		{ 1183950, 1527150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 575,167
		{ 1204950, 1612850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 785,1024
		{ 1190650, 1579150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 0 },	// stone 2008 cell 642,687
	};

	const TPlayerBotHuntingHub* GetPlayerBotYoharaHubs(long mapIndex, size_t& count)
	{
		count = 0;
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_ZAKLETY:
				count = sizeof(PLAYERBOT_YOHARA_ZAKLETY_HUBS) / sizeof(PLAYERBOT_YOHARA_ZAKLETY_HUBS[0]);
				return PLAYERBOT_YOHARA_ZAKLETY_HUBS;
			case 301:
				count = sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_301) / sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_301[0]);
				return PLAYERBOT_YOHARA_LOOT_HUBS_301;
			case 302:
				count = sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_302) / sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_302[0]);
				return PLAYERBOT_YOHARA_LOOT_HUBS_302;
			case 303:
				count = sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_303) / sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_303[0]);
				return PLAYERBOT_YOHARA_LOOT_HUBS_303;
			case 304:
				count = sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_304) / sizeof(PLAYERBOT_YOHARA_LOOT_HUBS_304[0]);
				return PLAYERBOT_YOHARA_LOOT_HUBS_304;
			default:
				return NULL;
		}
	}

	// ------------------------------------------------------------ the temple

	enum { YOHARA_TEMPLE_HUNT = 0, YOHARA_TEMPLE_GUARDIAN, YOHARA_TEMPLE_PORTAL };

	// In the Temple of Ochao, a bot bound for Zaklety Las: the Portal while it
	// stands within reach, else the Guardian - walked to by the labyrinth's
	// corners and fought - else the temple's own hunting while he is away
	// (0: the travel pass does nothing more). The players' road: the quest's
	// Portal (20415) leads to the forest (temple_of_the_ochao.quest).
	int ManagePlayerBotYoharaTemple(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotYoharaTemple& t = s_mapPlayerBotYoharaTemple[pid];
		if (t.dwSince == 0)
		{
			t.dwSince = dwNow;
			sys_log(0, "PLAYERBOT_YOHARA: temple crossing begins pid=%u name=%s level=%u pos=(%ld,%ld)",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetX(), ch->GetY());
		}
		if (ch->IsDead() || state.bRecoveringAfterDeath)
			return 0;
		// No Portal in all this time: the forest anyway, from where it stands.
		if (dwNow - t.dwSince >= PLAYERBOT_YOHARA_TEMPLE_WAIT_MS)
		{
			sys_log(0, "PLAYERBOT_YOHARA: temple wait over, to the forest pid=%u name=%s after_s=%u",
					pid, ch->GetName(), (dwNow - t.dwSince) / 1000);
			return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_ZAKLETY, PLAYERBOT_ZAKLETY_ARRIVAL_X,
					PLAYERBOT_ZAKLETY_ARRIVAL_Y, dwNow, "zaklety_temple_wait") ? 1 : 0;
		}
		BYTE phase = YOHARA_TEMPLE_HUNT;
		int result = 0;
		LPCHARACTER portal = FindPlayerBotOchaoPortal();
		LPCHARACTER guardian = mt2009_ochao::FindOnMap(mt2009_ochao::s_dwGuardianVID);
		if (!portal)
			t.dwPortalVID = 0;
		// Set out for a Portal once, while it is within the walk or right by
		// the bot, and keep to it until it closes.
		else if (t.dwPortalVID != (DWORD)portal->GetVID() &&
				(DISTANCE_APPROX(ch->GetX() - portal->GetX(), ch->GetY() - portal->GetY()) <= PLAYERBOT_YOHARA_PORTAL_NEAR ||
				 GetPlayerBotOchaoWalk(ch, portal->GetX(), portal->GetY()) <= PLAYERBOT_YOHARA_PORTAL_WALK_MAX))
		{
			t.dwPortalVID = (DWORD)portal->GetVID();
			sys_log(0, "PLAYERBOT_YOHARA: temple takes the portal pid=%u name=%s pos=(%ld,%ld) portal=(%ld,%ld) after_s=%u",
					pid, ch->GetName(), ch->GetX(), ch->GetY(), portal->GetX(), portal->GetY(), (dwNow - t.dwSince) / 1000);
		}
		if (portal && t.dwPortalVID == (DWORD)portal->GetVID())
		{
			phase = YOHARA_TEMPLE_PORTAL;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			const int d = DISTANCE_APPROX(ch->GetX() - portal->GetX(), ch->GetY() - portal->GetY());
			CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(PLAYERBOT_MAP_OCHAO);
			if (d <= PLAYERBOT_YOHARA_PORTAL_USE)
			{
				// Beside it: the quest's first choice, "Zaklety Las".
				ch->Stop();
				if (TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_ZAKLETY, PLAYERBOT_ZAKLETY_ARRIVAL_X,
						PLAYERBOT_ZAKLETY_ARRIVAL_Y, dwNow, "zaklety_portal"))
					return 1;
				result = 1;
			}
			else if (d <= PLAYERBOT_YOHARA_PORTAL_NEAR && nav.Init(PLAYERBOT_MAP_OCHAO) &&
					nav.SegmentClearWorld(ch->GetX(), ch->GetY(), portal->GetX(), portal->GetY()))
			{
				MovePlayerBot(ch, portal->GetX(), portal->GetY(), dwNow, 8, true, false, false, false);
				result = 1;
			}
			else
				result = WalkPlayerBotInOchao(ch, state, portal->GetX(), portal->GetY(), dwNow) ? 1 : 0;
		}
		else if (guardian && !guardian->IsDead())
		{
			phase = YOHARA_TEMPLE_GUARDIAN;
			const int d = DISTANCE_APPROX(ch->GetX() - guardian->GetX(), ch->GetY() - guardian->GetY());
			if (d > PLAYERBOT_YOHARA_GUARDIAN_NEAR)
			{
				// What attacks it on the way is fought where it comes.
				LPCHARACTER victim = ch->GetVictim();
				if (victim && !victim->IsDead() && victim->GetVictim() == ch &&
						DISTANCE_APPROX(ch->GetX() - victim->GetX(), ch->GetY() - victim->GetY()) < 800)
					result = 0;
				else
					result = WalkPlayerBotInOchao(ch, state, guardian->GetX(), guardian->GetY(), dwNow) ? 1 : 0;
			}
			else
				result = FightPlayerBotTowerObjective(ch, state, guardian, dwNow) ? 1 : 0;
		}
		if (phase != t.bPhase)
		{
			if (t.dwLastLog == 0 || dwNow - t.dwLastLog >= 60000)
			{
				sys_log(0, "PLAYERBOT_YOHARA: temple %s pid=%u name=%s pos=(%ld,%ld) after_s=%u",
						phase == YOHARA_TEMPLE_PORTAL ? "walks to the portal" :
						(phase == YOHARA_TEMPLE_GUARDIAN ? "goes for the guardian" : "hunts while the guardian is away"),
						pid, ch->GetName(), ch->GetX(), ch->GetY(), (dwNow - t.dwSince) / 1000);
				t.dwLastLog = dwNow;
			}
			t.bPhase = phase;
		}
		return result;
	}

	// ------------------------------------------------------------ the stay

	// The belt on the other core, where no merchant of the bot's stands: kept
	// full at the merchant's price, as the Arezzo forest's expedition was.
	void RestockPlayerBotYohara(LPCHARACTER ch, TPlayerBotYoharaResident& r, DWORD dwNow)
	{
		if ((int)(dwNow - r.dwNextRestock) < 0 || ch->IsDead() || !ch->IsItemLoaded())
			return;
		r.dwNextRestock = dwNow + PLAYERBOT_YOHARA_RESTOCK_MS;
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		const bool big = ch->GetLevel() >= PLAYERBOT_BIG_POTION_MIN_LEVEL;
		const bool caster = ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA;
		int boughtRed = 0, boughtBlue = 0;
		for (int i = 0; i < 2 && red + boughtRed < PLAYERBOT_YOHARA_BELT_RED && ch->GetEmptyInventory(1) >= 0; ++i)
		{
			const long long cost = 200LL * (big ? 40 : 20);
			if ((long long)ch->GetGold() < cost * 2)
				break;
			PlayerBotChangeGold(ch, -cost);
			ch->AutoGiveItem(big ? 27003 : 27002, 200);
			boughtRed += 200;
		}
		for (int i = 0; caster && i < 2 && blue + boughtBlue < PLAYERBOT_YOHARA_BELT_BLUE && ch->GetEmptyInventory(1) >= 0; ++i)
		{
			const long long cost = 200LL * (big ? 64 : 32);
			if ((long long)ch->GetGold() < cost * 2)
				break;
			PlayerBotChangeGold(ch, -cost);
			ch->AutoGiveItem(big ? 27006 : 27005, 200);
			boughtBlue += 200;
		}
		if (boughtRed || boughtBlue)
			sys_log(0, "PLAYERBOT_YOHARA: restock pid=%u name=%s map=%ld red=%u blue=%u bought_red=%d bought_blue=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (unsigned int)red, (unsigned int)blue,
					boughtRed, boughtBlue, (long long)ch->GetGold());
	}

	// The travel pass's part (ManagePlayerBotWorldTravel, before the frontier):
	// -1 nothing here, 0/1 its answer.
	int ManagePlayerBotYoharaTravel(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return -1;
		const DWORD pid = ch->GetPlayerID();
		if (s_mapPlayerBotYoharaLeaving.count(pid))
			return 1;
		const long mapIndex = ch->GetMapIndex();
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(pid);
		// The home core: the temple's road into the forest.
		if (!r)
		{
			if (mapIndex == PLAYERBOT_MAP_OCHAO && IsPlayerBotYoharaEligible(ch) && !BlocksPlayerBotTravel(ch) &&
					!IsPlayerBotOchaoLeaveOrdered(ch) && IsPlayerBotYoharaBoundForZaklety(ch))
				return ManagePlayerBotYoharaTemple(ch, state, dwNow);
			s_mapPlayerBotYoharaTemple.erase(pid);
			return -1;
		}
		TPlayerBotYoharaResident& res = *r;
		if (!GetPlayerBotYoharaConfig().on || IsPlayerBotYoharaSwitchedOff())
			return SendPlayerBotYoharaHome(ch, state, dwNow, "yohara_switched_off") ? 1 : 0;
		if (ch->IsDead() || state.bRecoveringAfterDeath)
			return -1;
		RestockPlayerBotYohara(ch, res, dwNow);
		const int level = ch->GetLevel();
		switch (res.iPurpose)
		{
			case YOHARA_PURPOSE_ZAKLETY:
				// The forest is a frontier: its visit, its band and its exit are the frontier's.
				if (base == PLAYERBOT_MAP_ZAKLETY)
					return -1;
				return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_ZAKLETY, PLAYERBOT_ZAKLETY_ARRIVAL_X,
						PLAYERBOT_ZAKLETY_ARRIVAL_Y, dwNow, "zaklety_back") ? 1 : 0;
			case YOHARA_PURPOSE_SZC:
			{
				if (IsPlayerBotOnDungeonRun(pid))
				{
					res.dwLastRun = dwNow;
					res.dwOffRunSince = 0;
					return 0;
				}
				const DWORD idleFrom = res.dwLastRun ? res.dwLastRun : res.dwArrived;
				const char* why = NULL;
				if (level < PLAYERBOT_SZC_MIN_LEVEL || level > PLAYERBOT_SZC_MAX_LEVEL)
					why = "szc_level";
				else if (dwNow - res.dwArrived >= PLAYERBOT_YOHARA_SZC_STAY_MS)
					why = "szc_stay_over";
				else if (dwNow - idleFrom >= PLAYERBOT_YOHARA_SZC_IDLE_MS)
					why = "szc_no_party";
				else if (BlocksPlayerBotTravel(ch))
					why = "szc_blocked";
				if (why)
					return SendPlayerBotYoharaHome(ch, state, dwNow, why) ? 1 : 0;
				if (base == PLAYERBOT_MAP_SZC_PLATEAU)
				{
					res.dwOffRunSince = 0;
					return 0;	// beside the statue till a run calls it
				}
				// Left in the dungeon by no run, or somewhere else of this core: back to the statue.
				if (res.dwOffRunSince == 0)
					res.dwOffRunSince = dwNow;
				if (base == PLAYERBOT_MAP_SZC && dwNow - res.dwOffRunSince < PLAYERBOT_YOHARA_SZC_LOST_MS)
					return 0;
				return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SZC_PLATEAU, PLAYERBOT_SZC_PLATEAU_X,
						PLAYERBOT_SZC_PLATEAU_Y, dwNow, "szc_to_statue") ? 1 : 0;
			}
			case YOHARA_PURPOSE_LOOT:
			{
				const char* why = NULL;
				if (base != res.lMap)
					why = "loot_off_map";
				else if (dwNow - res.dwArrived >= PLAYERBOT_YOHARA_LOOT_STAY_MS)
					why = "loot_done";
				else if (BlocksPlayerBotTravel(ch))
					why = "loot_blocked";
				if (why)
					return SendPlayerBotYoharaHome(ch, state, dwNow, why) ? 1 : 0;
				return 0;	// the Metins and the bosses (the hubs, the combat policy)
			}
			default:
				return SendPlayerBotYoharaHome(ch, state, dwNow, "yohara_no_purpose") ? 1 : 0;
		}
	}

	// ------------------------------------------------------------ in

	// The load's spot for a bot this core claimed (CPlayerBotManager::PlaceLoadingSidekick).
	bool PlacePlayerBotYoharaArrival(DWORD pid, long& lMapIndex, long& x, long& y)
	{
		std::map<DWORD, TPlayerBotYoharaArrival>::const_iterator a = s_mapPlayerBotYoharaArrival.find(pid);
		if (a == s_mapPlayerBotYoharaArrival.end() || !IsPlayerBotMapHostedHere(a->second.lMap))
			return false;
		lMapIndex = a->second.lMap;
		x = a->second.lX;
		y = a->second.lY;
		sys_log(0, "PLAYERBOT_HANDOVER: loads here pid=%u map=%ld spot=(%ld,%ld) purpose=%s", pid, lMapIndex, x, y,
				PlayerBotYoharaPurposeName(a->second.iPurpose));
		return true;
	}

	// The claimed ones that stand here now become residents.
	void SettlePlayerBotYoharaArrivals(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotYoharaArrival>::iterator a = s_mapPlayerBotYoharaArrival.begin();
				a != s_mapPlayerBotYoharaArrival.end();)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(a->first);
			if (!ch || !ch->GetSectree())
			{
				// A load that never came: the row goes, the bot is its home's again.
				if (dwNow - a->second.dwAt > 60000)
				{
					char q[160];
					snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid=%u AND state=2", a->first);
					RunPlayerBotYoharaSql(q);
					sys_log(0, "PLAYERBOT_HANDOVER: load lost pid=%u map=%ld purpose=%s", a->first, a->second.lMap,
							PlayerBotYoharaPurposeName(a->second.iPurpose));
					s_mapPlayerBotYoharaArrival.erase(a++);
					continue;
				}
				++a;
				continue;
			}
			if (a->second.iPurpose != YOHARA_PURPOSE_HOME)
			{
				TPlayerBotYoharaResident& res = s_mapPlayerBotYoharaResident[a->first];
				res = TPlayerBotYoharaResident();
				res.iPurpose = a->second.iPurpose;
				res.lMap = a->second.lMap;
				res.dwArrived = dwNow;
			}
			else
				s_mapPlayerBotYoharaCooldown[a->first] = dwNow + PLAYERBOT_YOHARA_TRIP_COOLDOWN_MS;
			sys_log(0, "PLAYERBOT_HANDOVER: arrived pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) purpose=%s took_ms=%u",
					a->first, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), ch->GetX(), ch->GetY(),
					PlayerBotYoharaPurposeName(a->second.iPurpose), dwNow - a->second.dwAt);
			s_mapPlayerBotYoharaArrival.erase(a++);
		}
	}

	// The SZC's ticket for a bots' run (playerbot_dungeon_runs.h): a Zegarek
	// Kieszonkowy from the bag, or its price at Handlarka Iluzji. The yang paid.
	long long ChargePlayerBotYoharaSzcWatch(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		if (ch->CountSpecifyItem(PLAYERBOT_YOHARA_SZC_WATCH) > 0)
		{
			ch->RemoveSpecifyItem(PLAYERBOT_YOHARA_SZC_WATCH, 1);
			sys_log(0, "PLAYERBOT_YOHARA: szc watch used pid=%u name=%s", ch->GetPlayerID(), ch->GetName());
			return 0;
		}
		if ((long long)ch->GetGold() < PLAYERBOT_YOHARA_SZC_WATCH_PRICE)
			return 0;
		PlayerBotChangeGold(ch, -PLAYERBOT_YOHARA_SZC_WATCH_PRICE);
		sys_log(0, "PLAYERBOT_YOHARA: szc watch bought pid=%u name=%s price=%lld gold=%lld", ch->GetPlayerID(),
				ch->GetName(), PLAYERBOT_YOHARA_SZC_WATCH_PRICE, (long long)ch->GetGold());
		return PLAYERBOT_YOHARA_SZC_WATCH_PRICE;
	}

	// ------------------------------------------------------------ the pass

	// From CPlayerBotManager::Update, before the bots' tick: the departures
	// out, the channel's rows read, the claims spawned, the stays refreshed.
	void ManagePlayerBotYoharaHandover(DWORD dwNow)
	{
		// The departures: logged out here (the engine saves them).
		if (!s_mapPlayerBotYoharaLeaving.empty())
		{
			std::map<DWORD, TPlayerBotYoharaLeave> leaving;
			leaving.swap(s_mapPlayerBotYoharaLeaving);
			for (std::map<DWORD, TPlayerBotYoharaLeave>::const_iterator i = leaving.begin(); i != leaving.end(); ++i)
			{
				s_mapPlayerBotYoharaResident.erase(i->first);
				s_mapPlayerBotYoharaTemple.erase(i->first);
				const bool gone = CPlayerBotManager::instance().Despawn(i->first, playerbot_session_rules::OUT_CHANNEL);
				sys_log(0, "PLAYERBOT_HANDOVER: logged out here pid=%u to=%ld purpose=%s ok=%d", i->first, i->second.lMap,
						PlayerBotYoharaPurposeName(i->second.iPurpose), gone ? 1 : 0);
			}
		}
		SettlePlayerBotYoharaArrivals(dwNow);
		if (s_dwPlayerBotYoharaNextPoll != 0 && (int)(dwNow - s_dwPlayerBotYoharaNextPoll) < 0)
			return;
		s_dwPlayerBotYoharaNextPoll = dwNow + PLAYERBOT_YOHARA_POLL_MS;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		// A channel without the handover reads nothing - unless it still has
		// residents or requests of its own (switched off under them).
		if ((!cfg.on || !cfg.channels.count((int)g_bChannel)) && s_mapPlayerBotYoharaResident.empty() &&
				s_mapPlayerBotYoharaOut.empty())
			return;
		if (!EnsurePlayerBotYoharaTable())
			return;
		char query[512];
		snprintf(query, sizeof(query),
				"SELECT pid, state, target_map, x, y, purpose, ready_at <= NOW(), "
				"updated_at > DATE_SUB(NOW(), INTERVAL %d SECOND) FROM common.playerbot_core_handover WHERE channel=%u",
				PLAYERBOT_YOHARA_STALE_S, (unsigned int)g_bChannel);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		struct TRow { DWORD pid; int state; long map, x, y; int purpose; bool ready, fresh; };
		std::vector<TRow> rows;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			TRow t;
			t.pid = 0; t.state = 0; t.map = t.x = t.y = 0; t.ready = t.fresh = false;
			if (row[0]) str_to_number(t.pid, row[0]);
			if (row[1]) str_to_number(t.state, row[1]);
			if (row[2]) str_to_number(t.map, row[2]);
			if (row[3]) str_to_number(t.x, row[3]);
			if (row[4]) str_to_number(t.y, row[4]);
			t.purpose = ParsePlayerBotYoharaPurpose(row[5]);
			t.ready = row[6] && atoi(row[6]) != 0;
			t.fresh = row[7] && atoi(row[7]) != 0;
			if (t.pid != 0)
				rows.push_back(t);
		}
		int census[YOHARA_PURPOSE_MAX] = { 0 };
		int residentsHere[YOHARA_PURPOSE_MAX] = { 0 };
		for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
			if (r->second.iPurpose > 0 && r->second.iPurpose < YOHARA_PURPOSE_MAX)
				++residentsHere[r->second.iPurpose];
		std::set<DWORD> away;
		std::set<DWORD> seen;
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TRow& t = rows[i];
			seen.insert(t.pid);
			const bool hostedHere = t.map > 0 && IsPlayerBotMapHostedHere(t.map);
			if (t.state == 1 && t.purpose > 0 && t.purpose < YOHARA_PURPOSE_MAX && t.purpose != YOHARA_PURPOSE_HOME)
				++census[t.purpose];
			else if (t.state == 2 && t.fresh && t.purpose > 0 && t.purpose < YOHARA_PURPOSE_MAX)
				++census[t.purpose];
			// A claim for this core.
			if (t.state == 1 && hostedHere && t.ready && !s_mapPlayerBotYoharaLeaving.count(t.pid) &&
					!s_mapPlayerBotYoharaArrival.count(t.pid))
			{
				if (CHARACTER_MANAGER::instance().FindByPID(t.pid) || P2P_MANAGER::instance().FindByPID(t.pid))
					continue;	// still logged in somewhere: the next poll
				bool refused = false;
				if (t.purpose == YOHARA_PURPOSE_ZAKLETY && residentsHere[t.purpose] >= cfg.zakletyMax)
					refused = true;
				else if (t.purpose == YOHARA_PURPOSE_SZC && residentsHere[t.purpose] >= cfg.szcMax)
					refused = true;
				else if (t.purpose == YOHARA_PURPOSE_LOOT && residentsHere[t.purpose] >= cfg.lootMax)
					refused = true;
				char q[192];
				if (refused || t.purpose == YOHARA_PURPOSE_HOME || t.purpose == YOHARA_PURPOSE_NONE)
					snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid=%u AND state=1", t.pid);
				else
					snprintf(q, sizeof(q), "UPDATE common.playerbot_core_handover SET state=2, updated_at=NOW() "
							"WHERE pid=%u AND state=1", t.pid);
				if (RunPlayerBotYoharaSql(q) != 1)
					continue;	// another core was first
				if (refused)
				{
					++s_uPlayerBotYoharaRefusedCount;
					sys_log(0, "PLAYERBOT_HANDOVER: refused here pid=%u map=%ld purpose=%s residents=%d",
							t.pid, t.map, PlayerBotYoharaPurposeName(t.purpose), residentsHere[t.purpose]);
					continue;
				}
				s_setPlayerBotYoharaAway.erase(t.pid);
				s_mapPlayerBotYoharaOut.erase(t.pid);
				TPlayerBotYoharaArrival& a = s_mapPlayerBotYoharaArrival[t.pid];
				a.lMap = t.map; a.lX = t.x; a.lY = t.y; a.iPurpose = t.purpose; a.dwAt = dwNow;
				CPlayerBotManager& mgr = CPlayerBotManager::instance();
				const bool sent = mgr.Spawn(t.pid, mgr.GetRegisteredEmpire(t.pid));
				if (t.purpose == YOHARA_PURPOSE_HOME)
					++s_uPlayerBotYoharaHomeCount;
				else
				{
					++s_uPlayerBotYoharaInCount;
					++residentsHere[t.purpose];
				}
				sys_log(0, "PLAYERBOT_HANDOVER: claimed pid=%u map=%ld spot=(%ld,%ld) purpose=%s spawn=%d",
						t.pid, t.map, t.x, t.y, PlayerBotYoharaPurposeName(t.purpose), sent ? 1 : 0);
				if (!sent)
				{
					s_mapPlayerBotYoharaArrival.erase(t.pid);
					if (t.purpose != YOHARA_PURPOSE_HOME)
					{
						snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid=%u AND state=2", t.pid);
						RunPlayerBotYoharaSql(q);
					}
				}
				continue;
			}
			// Away from this core: on its way to another, or staying there.
			if (CHARACTER_MANAGER::instance().FindByPID(t.pid))
				continue;
			if ((t.state == 1 && !hostedHere) || (t.state == 2 && t.fresh))
				away.insert(t.pid);
		}
		s_setPlayerBotYoharaAway.swap(away);
		for (int p = 0; p < YOHARA_PURPOSE_MAX; ++p)
			s_aiPlayerBotYoharaCensus[p] = census[p];
		// This core's requests: claimed (a stay row, or gone with the bot in
		// another core's world), or taken back.
		for (std::map<DWORD, TPlayerBotYoharaOut>::iterator o = s_mapPlayerBotYoharaOut.begin(); o != s_mapPlayerBotYoharaOut.end();)
		{
			const DWORD pid = o->first;
			int st = 0;
			for (size_t i = 0; i < rows.size(); ++i)
				if (rows[i].pid == pid)
					st = rows[i].state;
			if (st == 2 || (st == 0 && P2P_MANAGER::instance().FindByPID(pid)))
			{
				s_mapPlayerBotYoharaOut.erase(o++);
				continue;
			}
			if (st == 1 && dwNow - o->second.dwAt < PLAYERBOT_YOHARA_CLAIM_TIMEOUT_MS)
			{
				++o;
				continue;
			}
			if (st == 0 && dwNow - o->second.dwAt < 30000)
			{
				++o;
				continue;
			}
			bool back = true;
			if (st == 1)
			{
				char q[160];
				snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid=%u AND state=1", pid);
				back = RunPlayerBotYoharaSql(q) == 1;
			}
			if (back)
			{
				++s_uPlayerBotYoharaCancelCount;
				s_setPlayerBotYoharaAway.erase(pid);
				s_mapPlayerBotYoharaCooldown[pid] = dwNow + PLAYERBOT_YOHARA_REFUSED_COOLDOWN_MS;
				sys_log(0, "PLAYERBOT_HANDOVER: cancel pid=%u to=%ld purpose=%s state=%d after_s=%u - the bot is this core's again",
						pid, o->second.lMap, PlayerBotYoharaPurposeName(o->second.iPurpose), st, (dwNow - o->second.dwAt) / 1000);
			}
			s_mapPlayerBotYoharaOut.erase(o++);
		}
		// The residents: gone from this core without a handover (a rest, a
		// channel move, a GM) - their rows go too.
		std::string gone, stay;
		for (std::map<DWORD, TPlayerBotYoharaResident>::iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end();)
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(r->first))
			{
				gone += (gone.empty() ? "" : ",") + std::to_string(r->first);
				sys_log(0, "PLAYERBOT_HANDOVER: resident gone pid=%u purpose=%s stay_s=%u", r->first,
						PlayerBotYoharaPurposeName(r->second.iPurpose), (dwNow - r->second.dwArrived) / 1000);
				s_mapPlayerBotYoharaResident.erase(r++);
				continue;
			}
			stay += (stay.empty() ? "" : ",") + std::to_string(r->first);
			++r;
		}
		if (!gone.empty())
		{
			const std::string q = "DELETE FROM common.playerbot_core_handover WHERE state=2 AND pid IN (" + gone + ")";
			RunPlayerBotYoharaSql(q.c_str());
		}
		if (!stay.empty() && (s_dwPlayerBotYoharaNextHeartbeat == 0 || (int)(dwNow - s_dwPlayerBotYoharaNextHeartbeat) >= 0))
		{
			s_dwPlayerBotYoharaNextHeartbeat = dwNow + PLAYERBOT_YOHARA_HEARTBEAT_MS;
			const std::string q = "UPDATE common.playerbot_core_handover SET updated_at=NOW() WHERE state=2 AND pid IN (" + stay + ")";
			RunPlayerBotYoharaSql(q.c_str());
		}
		if (s_dwPlayerBotYoharaNextCensusLog == 0 || (int)(dwNow - s_dwPlayerBotYoharaNextCensusLog) >= 0)
		{
			s_dwPlayerBotYoharaNextCensusLog = dwNow + PLAYERBOT_YOHARA_CENSUS_LOG_MS;
			// The old rows of a stay nobody refreshes (the core gone with them).
			RunPlayerBotYoharaSql("DELETE FROM common.playerbot_core_handover WHERE state=2 AND updated_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)");
			sys_log(0, "PLAYERBOT_HANDOVER: census channel=%u on=%d zaklety=%d/%d szc=%d/%d loot=%d/%d residents_here=%u "
					"(zaklety=%d szc=%d loot=%d) away=%u requests=%u out=%u in=%u home=%u refused=%u cancel=%u",
					(unsigned int)g_bChannel, IsPlayerBotYoharaOn() ? 1 : 0,
					census[YOHARA_PURPOSE_ZAKLETY], cfg.zakletyMax, census[YOHARA_PURPOSE_SZC], cfg.szcMax,
					census[YOHARA_PURPOSE_LOOT], cfg.lootMax, (unsigned int)s_mapPlayerBotYoharaResident.size(),
					residentsHere[YOHARA_PURPOSE_ZAKLETY], residentsHere[YOHARA_PURPOSE_SZC], residentsHere[YOHARA_PURPOSE_LOOT],
					(unsigned int)s_setPlayerBotYoharaAway.size(), (unsigned int)s_mapPlayerBotYoharaOut.size(),
					s_uPlayerBotYoharaOutCount, s_uPlayerBotYoharaInCount, s_uPlayerBotYoharaHomeCount,
					s_uPlayerBotYoharaRefusedCount, s_uPlayerBotYoharaCancelCount);
		}
	}
}

#endif
