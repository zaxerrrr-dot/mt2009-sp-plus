#ifndef __INC_METIN2_PLAYERBOT_YOHARA_BOTS_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_BOTS_H__

// MT2009_PLUS_BOT_YOHARA_HANDOVER_V1 - the bots between the game cores of one
// channel, and the owner's levelling route over them (21 October 2026, the
// decisions on plan-boty-yohara.md: "D1 - tak, zacznij od D1"; "do 110 lvl exp
// w Zakletym Lesie; mapy na 90 lvl tylko drop - Metiny i bossowie; 110-120 exp
// w Szczelinie Czasu - Zaklety Las").
//
// MT2009_PLUS_237_ZAKLETY_LAS_V1 / MT2009_PLUS_237_MAPS90_V1 - the 2.x line (2.37) takes this file over
// from the Yohara line (claude/yohara-3, as of 44bbdc76: the handover, Zaklety Las with the fixes of 21-22
// October - MT2009_PLUS_BOT_YOHARA_FIX_V1, MT2009_PLUS_BOT_ZAKLETY_SPOTS_V2 - and the loot runs) for the
// owner's order of 22 October 2026 ("the new Zaklety Las for bots and players; the level-90 maps"). On the
// 2.x line Zaklety Las (353) and 301-304 stand on game3, a core of their own in every channel
// (MT2009_PLUS_237_NEWCORE_V1, bin/m2-render-config; game2 with M2_MAP_CORE=0), and the bots live on game1 -
// so the same handover takes them there. It routes by MAP_ALLOW (IsPlayerBotMapHostedHere), not by a core's name. Left out: the Time Rift (SZC, 404 -
// no such map on 2.x), the night cohorts (a Yohara test tool), Hydra and the Sung Ma maps.
//
// MT2009_PLUS_MAPS_WZ_BOTS_V1 (the 2.x line, 26 October 2026 - the owner: "do 2.x dodaj wezowe pole i kraine
// gigantow"): Wezowe Pole (80) and Kraina Gigantow (70) on game3 are purposes too (snakefield, giantland), the Yohara
// line's MT2009_PLUS_BOT_YOHARA_COHORT_V1 parts without its cohorts: their frontier bands 63-78 / 63-80, a quarter of
// the draw each (the hash of playerbot_travel.h's in-core draw), PLAYERBOT_SNAKEFIELD_MAX / PLAYERBOT_GIANTLAND_MAX
// (50 a channel) and a stay of PLAYERBOT_WZ_STAY_MIN (120); the arrival / exit / hubs / grid of MT2009_PLUS_MAPS_WZ_BOTS_V1
// (playerbot_types.h, playerbot_wandering.h, playerbot_navigation.h).
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
//   * Zaklety Las (353, game3 - on the 2.x line too since MT2009_PLUS_237_NEWCORE_V1), PLAYERBOT_ZAKLETY_MIN_LEVEL (100) to 109: the
//     players' road - Orc Valley, the temple's guard (playerbot_ochao_bots.h),
//     the Temple of Ochao, the En-Tai Guardian (fought) and his Portal - and
//     the handover at the Portal; after PLAYERBOT_YOHARA_TEMPLE_WAIT_MS in the
//     temple with no Portal the bot takes the handover where it stands (the
//     Guardian falls rarely: 0 kills on the test server 19-21 October). In the
//     forest it hunts 24 spots (tools/arezzo_bot_map.py), its belt kept full
//     (the Las rule of 1 October: an expedition) and stays
//     PLAYERBOT_ZAKLETY_STAY_MIN; the frontier's exit (its Teleporter) is the
//     way home.
//   * loot runs (301-304): from 95, now and then, a bot leaves its village for
//     a 90-level map and breaks its Metins and fights its bosses, nothing else
//     (the combat policy's SERVICE_ONLY for the ordinary monsters), for
//     PLAYERBOT_YOHARA_LOOT_STAY_MS.
//   * Hydra and the Sung Ma maps stay closed (TransitionPlayerBotMap's
//     sungma_map refusal is before this file's route).
//
// The switches (.env / the Seban panel's env page; docker-compose passes them
// to the game container): PLAYERBOT_HANDOVER (1), PLAYERBOT_HANDOVER_CHANNELS
// ("1" on the Yohara line's test; every channel on the 2.x line), PLAYERBOT_ZAKLETY_MAX
// (30 a channel), PLAYERBOT_ZAKLETY_MIN_LEVEL (100), PLAYERBOT_ZAKLETY_STAY_MIN (120),
// PLAYERBOT_ZAKLETY_MIN_HP (20000), PLAYERBOT_LOOTRUN_MAX (6), PLAYERBOT_LOOTRUN_MAPS
// ("301,302,303,304" since MT2009_PLUS_237_NEWCORE_V1 - the grids: 301 ~160 MB, 302 ~125, 303 ~80, 304 ~107,
// on game3). The event flag m2_bot_handover_off
// (a GM's /e, the panel's flags) stops every new handover and sends every resident home.
//
// The log: PLAYERBOT_HANDOVER (out, claimed, arrived, home, refused, cancel,
// census), PLAYERBOT_YOHARA (the temple, the stay, the restock, the loot runs).
// The operator's hook: the file playerbot_yohara_test in the core's directory
// (RunPlayerBotYoharaTestFile).
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
	// MT2009_PLUS_BOT_YOHARA_FIX_V1: a stay ended by its deaths - no new trip for this long, and the
	// deaths that end it: this many in PLAYERBOT_YOHARA_DEATH_WINDOW_MS, or this many in the stay.
	const DWORD PLAYERBOT_YOHARA_DEATHS_COOLDOWN_MS = 3 * 60 * 60 * 1000;
	const int PLAYERBOT_YOHARA_DEATHS_WINDOWED = 3;
	const DWORD PLAYERBOT_YOHARA_DEATH_WINDOW_MS = 30 * 60 * 1000;
	const int PLAYERBOT_YOHARA_DEATHS_STAY = 5;
	// MT2009_PLUS_BOT_YOHARA_FIX_V1: what is not a reason to go home in the first minutes of a stay
	// (a bag with no free column, a short belt the restock fills) - only the gear is.
	const DWORD PLAYERBOT_YOHARA_SETTLE_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_REFUSED_COOLDOWN_MS = 20 * 60 * 1000;
	// The temple: no Portal in this long since the bot came in for the forest -
	// it takes the handover where it stands.
	const DWORD PLAYERBOT_YOHARA_TEMPLE_WAIT_MS = 20 * 60 * 1000;
	const int PLAYERBOT_YOHARA_PORTAL_USE = 700;
	const int PLAYERBOT_YOHARA_PORTAL_NEAR = 2500;
	const int PLAYERBOT_YOHARA_PORTAL_WALK_MAX = 12000;
	const int PLAYERBOT_YOHARA_GUARDIAN_NEAR = 1500;
	// The stays.
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

	enum EPlayerBotYoharaPurpose
	{
		YOHARA_PURPOSE_NONE = 0,
		YOHARA_PURPOSE_HOME,
		YOHARA_PURPOSE_ZAKLETY,
		YOHARA_PURPOSE_LOOT,
		YOHARA_PURPOSE_SNAKEFIELD,	// MT2009_PLUS_MAPS_WZ_BOTS_V1
		YOHARA_PURPOSE_GIANTLAND,
		YOHARA_PURPOSE_MAX
	};

	const char* PlayerBotYoharaPurposeName(int purpose)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_HOME: return "home";
			case YOHARA_PURPOSE_ZAKLETY: return "zaklety";
			case YOHARA_PURPOSE_LOOT: return "loot";
			case YOHARA_PURPOSE_SNAKEFIELD: return "snakefield";	// MT2009_PLUS_MAPS_WZ_BOTS_V1
			case YOHARA_PURPOSE_GIANTLAND: return "giantland";
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
		int zakletyMax, zakletyMinLevel, zakletyStayMin, zakletyMinHp;
		int lootMax;
		std::vector<long> lootMaps;
		int snakeMax, giantMax, wzStayMin;	// MT2009_PLUS_MAPS_WZ_BOTS_V1
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
		// MT2009_PLUS_237_ZAKLETY_LAS_V1: every channel by default - the forest is no test here.
		ReadPlayerBotYoharaEnvList("PLAYERBOT_HANDOVER_CHANNELS", "1,2,3,4,5,6", ch);
		for (size_t i = 0; i < ch.size(); ++i)
			s_cfg.channels.insert((int)ch[i]);
		s_cfg.zakletyMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MAX", 30, 0, 300);
		s_cfg.zakletyMinLevel = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MIN_LEVEL", PLAYERBOT_ZAKLETY_MIN_LEVEL,
				PLAYERBOT_OCHAO_MIN_LEVEL, PLAYERBOT_ZAKLETY_MAX_LEVEL);
		s_cfg.zakletyStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_STAY_MIN", 120, 20, 600);
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: the test of 21 October - two warriors of 97/101 with 11 250 /
		// 11 550 health died at once; the forest's packs are 3-5 En-Tai of 100-108 (179-290 a blow).
		s_cfg.zakletyMinHp = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MIN_HP", 20000, 0, 1000000);
		s_cfg.lootMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_LOOTRUN_MAX", 6, 0, 200);
		std::vector<long> maps;
		// MT2009_PLUS_237_NEWCORE_V1: all four (the owner, 22 October 2026) - on game3 with the forest now.
		ReadPlayerBotYoharaEnvList("PLAYERBOT_LOOTRUN_MAPS", "301,302,303,304", maps);
		for (size_t i = 0; i < maps.size(); ++i)
			if (maps[i] >= 301 && maps[i] <= 304 &&
					std::find(s_cfg.lootMaps.begin(), s_cfg.lootMaps.end(), maps[i]) == s_cfg.lootMaps.end())
				s_cfg.lootMaps.push_back(maps[i]);
		// MT2009_PLUS_MAPS_WZ_BOTS_V1: Wezowe Pole / Kraina Gigantow (game3), a channel's limits and the stay.
		s_cfg.snakeMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SNAKEFIELD_MAX", 50, 0, 300);
		s_cfg.giantMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_GIANTLAND_MAX", 50, 0, 300);
		s_cfg.wzStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_WZ_STAY_MIN", 120, 20, 600);
		std::string chans, loot;
		for (std::set<int>::const_iterator i = s_cfg.channels.begin(); i != s_cfg.channels.end(); ++i)
			chans += (chans.empty() ? "" : ",") + std::to_string(*i);
		for (size_t i = 0; i < s_cfg.lootMaps.size(); ++i)
			loot += (loot.empty() ? "" : ",") + std::to_string(s_cfg.lootMaps[i]);
		sys_log(0, "PLAYERBOT_HANDOVER: config on=%d channels=%s zaklety_max=%d zaklety_min_level=%d zaklety_stay_min=%d "
				"zaklety_min_hp=%d loot_max=%d loot_maps=%s snakefield_max=%d giantland_max=%d wz_stay_min=%d channel_here=%u",
				s_cfg.on ? 1 : 0, chans.c_str(), s_cfg.zakletyMax, s_cfg.zakletyMinLevel, s_cfg.zakletyStayMin, s_cfg.zakletyMinHp,
				s_cfg.lootMax, loot.c_str(), s_cfg.snakeMax, s_cfg.giantMax, s_cfg.wzStayMin, (unsigned int)g_bChannel);
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

	// A purpose's map (the loot runs have several: 0), the purpose of a map, its limit a channel
	// and its band.
	long GetPlayerBotYoharaPurposeMap(int purpose)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY: return PLAYERBOT_MAP_ZAKLETY;
			case YOHARA_PURPOSE_SNAKEFIELD: return PLAYERBOT_MAP_SNAKEFIELD;	// MT2009_PLUS_MAPS_WZ_BOTS_V1
			case YOHARA_PURPOSE_GIANTLAND: return PLAYERBOT_MAP_GIANTLAND;
			default: return 0;
		}
	}

	int GetPlayerBotYoharaMapPurpose(long base)
	{
		if (base == PLAYERBOT_MAP_ZAKLETY)
			return YOHARA_PURPOSE_ZAKLETY;
		if (base == PLAYERBOT_MAP_SNAKEFIELD)	// MT2009_PLUS_MAPS_WZ_BOTS_V1
			return YOHARA_PURPOSE_SNAKEFIELD;
		if (base == PLAYERBOT_MAP_GIANTLAND)
			return YOHARA_PURPOSE_GIANTLAND;
		if (IsPlayerBotYoharaLootMap(base))
			return YOHARA_PURPOSE_LOOT;
		return YOHARA_PURPOSE_NONE;
	}

	int GetPlayerBotYoharaCap(int purpose)
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY: return cfg.zakletyMax;
			case YOHARA_PURPOSE_LOOT: return cfg.lootMax;
			case YOHARA_PURPOSE_SNAKEFIELD: return cfg.snakeMax;	// MT2009_PLUS_MAPS_WZ_BOTS_V1
			case YOHARA_PURPOSE_GIANTLAND: return cfg.giantMax;
			default: return 0;
		}
	}

	bool IsPlayerBotYoharaInBand(int purpose, int level)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY:
				return level >= GetPlayerBotYoharaConfig().zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL;
			case YOHARA_PURPOSE_LOOT:
				return level >= PLAYERBOT_YOHARA_LOOT_MIN_LEVEL;
			case YOHARA_PURPOSE_SNAKEFIELD:	// MT2009_PLUS_MAPS_WZ_BOTS_V1
				return level >= PLAYERBOT_SNAKEFIELD_MIN_LEVEL && level <= PLAYERBOT_SNAKEFIELD_MAX_LEVEL;
			case YOHARA_PURPOSE_GIANTLAND:
				return level >= PLAYERBOT_GIANTLAND_MIN_LEVEL && level <= PLAYERBOT_GIANTLAND_MAX_LEVEL;
			default:
				return false;
		}
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
		bool bDeaths;	// MT2009_PLUS_BOT_YOHARA_FIX_V1: a way home its deaths asked for (the long rest)
		TPlayerBotYoharaArrival() : lMap(0), lX(0), lY(0), iPurpose(0), dwAt(0), bDeaths(false) {}
	};
	// A bot living on this core for a purpose (this core is not its home).
	struct TPlayerBotYoharaResident
	{
		int iPurpose;
		long lMap;
		DWORD dwArrived, dwNextRestock;
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: the stay's deaths (counted by the poll, outside a dungeon run).
		bool bDead;
		int iDeaths, iDeathsWindowed;
		DWORD dwWindowStart;
		TPlayerBotYoharaResident() : iPurpose(0), lMap(0), dwArrived(0), dwNextRestock(0),
			bDead(false), iDeaths(0), iDeathsWindowed(0), dwWindowStart(0) {}
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
		// Claimed by this core - its Spawn is the claim's.
		if (s_mapPlayerBotYoharaArrival.count(pid) != 0)
			return false;
		return s_setPlayerBotYoharaAway.count(pid) != 0 || s_mapPlayerBotYoharaOut.count(pid) != 0 ||
				s_mapPlayerBotYoharaLeaving.count(pid) != 0;
	}

	bool IsPlayerBotYoharaLeaving(DWORD pid)
	{
		return s_mapPlayerBotYoharaLeaving.count(pid) != 0;
	}

	// Zaklety Las is an expedition: its stay (the frontier visit's clock, playerbot_travel.h).
	// MT2009_PLUS_MAPS_WZ_BOTS_V1: Wezowe Pole and Kraina Gigantow too, for a bot the handover brought.
	DWORD GetPlayerBotYoharaStayMs(LPCHARACTER ch, long mapIndex)
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		if (mapIndex == PLAYERBOT_MAP_ZAKLETY)
			return (DWORD)cfg.zakletyStayMin * 60000U;
		if ((mapIndex == PLAYERBOT_MAP_SNAKEFIELD || mapIndex == PLAYERBOT_MAP_GIANTLAND) && ch &&
				FindPlayerBotYoharaResident(ch->GetPlayerID()))
			return (DWORD)cfg.wzStayMin * 60000U;
		return 0;
	}

	// A map of another core this core's bots go to (GetPlayerBotFrontierMapForLevel's filter).
	bool IsPlayerBotYoharaRemoteFrontier(long mapIndex)
	{
		if (!IsPlayerBotYoharaOn() || IsPlayerBotMapHostedHere(mapIndex))
			return false;
		return mapIndex == PLAYERBOT_MAP_ZAKLETY || IsPlayerBotYoharaLootMap(mapIndex) ||
				mapIndex == PLAYERBOT_MAP_SNAKEFIELD || mapIndex == PLAYERBOT_MAP_GIANTLAND;	// MT2009_PLUS_MAPS_WZ_BOTS_V1
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
		{
			return RequestPlayerBotYoharaHandover(ch, state, base, targetX, targetY, YOHARA_PURPOSE_HOME,
					reason ? reason : "home", dwNow) ? 1 : 0;
		}
		if (!IsPlayerBotYoharaOn())
			return -1;
		const int purpose = GetPlayerBotYoharaMapPurpose(base);
		const int cap = GetPlayerBotYoharaCap(purpose);
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
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: never with a bag, a belt or gear its town visit has to sort out
		// first (21 October: Hyuuga left with a full bag and was sent home at the arrival).
		if (BlocksPlayerBotTravel(ch))
			return 0;
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
				case YOHARA_PURPOSE_LOOT:
					return IsPlayerBotMapHostedHere(r->lMap) && dwNow - r->dwArrived < PLAYERBOT_YOHARA_LOOT_STAY_MS
							? r->lMap : 0;
				// MT2009_PLUS_MAPS_WZ_BOTS_V1: Wezowe Pole / Kraina Gigantow, while the band lasts.
				case YOHARA_PURPOSE_SNAKEFIELD:
				case YOHARA_PURPOSE_GIANTLAND:
				{
					const long m = GetPlayerBotYoharaPurposeMap(r->iPurpose);
					return IsPlayerBotYoharaInBand(r->iPurpose, level) && IsPlayerBotMapHostedHere(m) ? m : 0;
				}
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
		// Zaklety Las: two in three of the band, while there is room (and a
		// bot already on its way through the temple keeps it).
		const bool inTemple = s_mapPlayerBotYoharaTemple.count(pid) != 0;
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: strong enough for the forest's packs (PLAYERBOT_ZAKLETY_MIN_HP).
		if (level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL && ch->GetMaxHP() < cfg.zakletyMinHp)
			PlayerBotLogThrottled("zaklety_weak", dwNow, "PLAYERBOT_YOHARA: too weak for the forest pid=%u name=%s level=%d max_hp=%d need=%d",
					pid, ch->GetName(), level, (int)ch->GetMaxHP(), cfg.zakletyMinHp);
		if (level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL && cfg.zakletyMax > 0 &&
				ch->GetMaxHP() >= cfg.zakletyMinHp && IsPlayerBotOchaoHosted() &&
				(inTemple || s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_ZAKLETY] < cfg.zakletyMax) &&
				PlayerBotNavHash(pid ^ 0x5a4b4c53U) % 3U != 0)
			return PLAYERBOT_MAP_ZAKLETY;
		// MT2009_PLUS_MAPS_WZ_BOTS_V1: Wezowe Pole (80) and Kraina Gigantow (70) on game3 - the quarter of the
		// draw each that playerbot_travel.h gives them on a core hosting them (the same hash), here through the
		// handover, within PLAYERBOT_SNAKEFIELD_MAX / PLAYERBOT_GIANTLAND_MAX.
		{
			const DWORD wz = PlayerBotNavHash(pid ^ 0x575a4d50U) % 4U;
			if (wz == 1 && !stoneHunter && IsPlayerBotYoharaInBand(YOHARA_PURPOSE_SNAKEFIELD, level) && cfg.snakeMax > 0 &&
					s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SNAKEFIELD] < cfg.snakeMax &&
					!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SNAKEFIELD))
				return PLAYERBOT_MAP_SNAKEFIELD;
			if (wz == 2 && IsPlayerBotYoharaInBand(YOHARA_PURPOSE_GIANTLAND, level) && cfg.giantMax > 0 &&
					s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_GIANTLAND] < cfg.giantMax &&
					!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_GIANTLAND))
				return PLAYERBOT_MAP_GIANTLAND;
		}
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
	// MT2009_PLUS_BOT_YOHARA_FIX_V1: each spot's floor by the En-Tai within 3 600 of it (the regen's groups
	// 6311-6317 and their members): 100-102 only (the two by the arrival) from 95, to 104-105 from 99, the
	// ones with Niszczyciel En-Tai (108) from 103 - a bot starts by the arrival and moves out as it grows.
	// MT2009_PLUS_BOT_ZAKLETY_SPOTS_V2: the night of 21/22 October (~65 bots of 102-109, 22-26k HP, 924 deaths
	// in 8.7 h) - 432 of the 769 deaths to monsters at the nine spots within 2 700 of a Niszczyciel pack
	// (group 6317: the 108 with two Uzdrowiciele and two Bojownicy, the southern strip y 1413 000-1452 000),
	// 16.6-22.1 deaths per bot and 10 h at the busy ones against 10.1 at the rest, and the dying bots of
	// every level up to 109: those nine are for a party of three now (from 105). The densest spot (27 lines,
	// 19.2) from 107, the two next worst (14.7, and 13.0 by an Uzdrowiciel pack) from 105. 15 spots stay
	// for the lone bots (crowd-shared, ~7 bots a spot at 100 bots).
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_ZAKLETY_HUBS[] = {
		{ 827350, 1465350, 107, 255, false, 0 },	// 27 spawn lines, to 104-105 (V2: densest, from 107)
		{ 805650, 1420250, 105, 255, true, 0 },	// 23 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 824750, 1483050, 99, 255, false, 0 },	// 19 spawn lines, to 104-105
		{ 784650, 1469750, 99, 255, false, 0 },	// 19 spawn lines, to 104-105
		{ 821550, 1461350, 105, 255, false, 0 },	// 13 spawn lines, to 104-105 (V2: from 105)
		{ 831150, 1447350, 99, 255, false, 0 },	// 13 spawn lines, to 104-105
		{ 787750, 1477250, 99, 255, false, 0 },	// 13 spawn lines, to 104-105
		{ 804450, 1497550, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 12 spawn lines, 100-102 only - by the arrival
		{ 793650, 1433850, 105, 255, true, 0 },	// 12 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 778750, 1450950, 105, 255, true, 0 },	// 12 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 808750, 1447450, 105, 255, true, 0 },	// 11 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 818250, 1444850, 99, 255, false, 0 },	// 11 spawn lines, to 104-105
		{ 795750, 1486050, 99, 255, false, 0 },	// 9 spawn lines, to 104-105
		{ 829450, 1434550, 99, 255, false, 0 },	// 9 spawn lines, to 104-105
		{ 790950, 1470550, 99, 255, false, 0 },	// 9 spawn lines, to 104-105
		{ 799850, 1442250, 105, 255, true, 0 },	// 9 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 777850, 1439350, 105, 255, true, 0 },	// 9 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 826050, 1417450, 105, 255, true, 0 },	// 8 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 827350, 1473850, 99, 255, false, 0 },	// 7 spawn lines, to 104-105
		{ 827850, 1454750, 99, 255, false, 0 },	// 7 spawn lines, to 104-105
		{ 812950, 1493050, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },	// 6 spawn lines, 100-102 only - by the arrival
		{ 795350, 1457050, 105, 255, false, 0 },	// 6 spawn lines, to 104-105 (V2: Uzdrowiciel pack, from 105)
		{ 802150, 1426150, 105, 255, true, 0 },	// 6 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 801350, 1450550, 105, 255, true, 0 },	// 5 spawn lines, En-Tai to 108 (V2: Niszczyciel pack, party only)
		{ 826700, 1417700, 105, 255, true, 6407 },	// Wladca En-Tai (boss.txt)
	};

	// MT2009_PLUS_BOT_YOHARA_LOOTRUN_V1: the 90-level maps' Metins (stone.txt) and bosses (boss.txt),
	// tools/yohara_bot_lootrun_map.py with the container's group.txt (21 October) - a boss row (the group's
	// leader) is chosen while its boss stands.
	const TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_301[] = {
		{ 1111750, 1725450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3090 },	// boss 3090 cell 881,614
		{ 1067450, 1701450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3091 },	// boss 3091 cell 434,374
		{ 1134650, 1695950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3290 },	// boss 3290 cell 1106,319
		{ 1109150, 1701650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3291 },	// boss 3291 cell 839,380
		{ 1162650, 1796550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3590 },	// boss 3590 cell 1386,1325
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
		{ 1318750, 1699750, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3890 },	// boss 3890 cell 1411,357
		{ 1327450, 1686650, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3891 },	// boss 3891 cell 1498,226
		{ 1279950, 1733250, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3390 },	// boss 3390 cell 1023,692
		{ 1255250, 1699050, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3391 },	// boss 3391 cell 776,351
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
		{ 1073450, 1596850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3490 },	// boss 3490 cell 238,864
		{ 1064250, 1599950, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3491 },	// boss 3491 cell 146,895
		{ 1078450, 1556150, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3690 },	// boss 3690 cell 288,457
		{ 1070550, 1546350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3691 },	// boss 3691 cell 209,359
		{ 1112250, 1621450, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3590 },	// boss 3590 cell 626,1110
		{ 1115550, 1552850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3591 },	// boss 3591 cell 659,424
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
		{ 1164050, 1619850, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3595 },	// boss 3595 cell 376,1094
		{ 1161050, 1594550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3596 },	// boss 3596 cell 346,841
		{ 1137750, 1521350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3790 },	// boss 3790 cell 113,109
		{ 1187550, 1624350, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3791 },	// boss 3791 cell 611,1139
		{ 1179750, 1590550, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3190 },	// boss 3190 cell 533,801
		{ 1217450, 1519250, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, 3191 },	// boss 3191 cell 910,88
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

	// MT2009_PLUS_BOT_YOHARA_FIX_V1: what sends a resident home before its time - no weapon or
	// armour, the arrows; the belt only when the restock could not fill it; the bag and the rest only
	// once it has settled in. BlocksPlayerBotTravel at the arrival sent a loot runner home in 0 s.
	bool IsPlayerBotYoharaFightStopped(LPCHARACTER ch, const TPlayerBotYoharaResident& r, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		if (ch->GetWear(WEAR_WEAPON) == NULL || ch->GetWear(WEAR_BODY) == NULL || NeedsPlayerBotArrows(ch))
			return true;
		if (dwNow - r.dwArrived < PLAYERBOT_YOHARA_SETTLE_MS)
			return false;
		return BlocksPlayerBotTravel(ch);
	}

	bool IsPlayerBotYoharaDeathsOver(const TPlayerBotYoharaResident& r)
	{
		return r.iDeaths >= PLAYERBOT_YOHARA_DEATHS_STAY || r.iDeathsWindowed >= PLAYERBOT_YOHARA_DEATHS_WINDOWED;
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
				// MT2009_PLUS_BOT_YOHARA_FIX_V1: too many deaths - out of the forest, back in three hours.
				if (IsPlayerBotYoharaDeathsOver(res))
					return SendPlayerBotYoharaHome(ch, state, dwNow, "zaklety_deaths") ? 1 : 0;
				// The forest is a frontier: its visit, its band and its exit are the frontier's.
				if (base == PLAYERBOT_MAP_ZAKLETY)
					return -1;
				return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_ZAKLETY, PLAYERBOT_ZAKLETY_ARRIVAL_X,
						PLAYERBOT_ZAKLETY_ARRIVAL_Y, dwNow, "zaklety_back") ? 1 : 0;
			// MT2009_PLUS_MAPS_WZ_BOTS_V1: Wezowe Pole / Kraina Gigantow - frontiers of game3, as the forest.
			case YOHARA_PURPOSE_SNAKEFIELD:
			case YOHARA_PURPOSE_GIANTLAND:
			{
				if (IsPlayerBotYoharaDeathsOver(res))
					return SendPlayerBotYoharaHome(ch, state, dwNow, "wz_deaths") ? 1 : 0;
				if (base == res.lMap)
					return -1;
				long x = 0, y = 0;
				if (!GetPlayerBotFrontierArrival(res.lMap, x, y))
					return SendPlayerBotYoharaHome(ch, state, dwNow, "wz_no_arrival") ? 1 : 0;
				return TransitionPlayerBotMap(ch, state, res.lMap, x, y, dwNow, "wz_back") ? 1 : 0;
			}
			case YOHARA_PURPOSE_LOOT:
			{
				const char* why = NULL;
				if (base != res.lMap)
					why = "loot_off_map";
				else if (dwNow - res.dwArrived >= PLAYERBOT_YOHARA_LOOT_STAY_MS)
					why = "loot_done";
				else if (IsPlayerBotYoharaFightStopped(ch, res, dwNow))
					why = "loot_blocked";
				else if (IsPlayerBotYoharaDeathsOver(res))
					why = "loot_deaths";
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
				s_mapPlayerBotYoharaCooldown[a->first] = dwNow + (a->second.bDeaths ? PLAYERBOT_YOHARA_DEATHS_COOLDOWN_MS
						: PLAYERBOT_YOHARA_TRIP_COOLDOWN_MS);
			sys_log(0, "PLAYERBOT_HANDOVER: arrived pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) purpose=%s took_ms=%u",
					a->first, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), ch->GetX(), ch->GetY(),
					PlayerBotYoharaPurposeName(a->second.iPurpose), dwNow - a->second.dwAt);
			s_mapPlayerBotYoharaArrival.erase(a++);
		}
	}

	// ------------------------------------------------------------ the operator

	// The test hook: a file "playerbot_yohara_test" in the core's directory, read at the poll and
	// renamed to .done (the Ochao/Arezzo tests' way):
	//     send <n> zaklety|loot|snakefield|giantland [map]
	//                                       n bots of this core of the purpose's band straight to the
	//                                       other core (the temple's road left out: a test of the handover)
	//     home <n|all>                      residents of this core sent home
	//     status                            the census and every resident here, one line each
	const char* const PLAYERBOT_YOHARA_TEST_FILE = "playerbot_yohara_test";

	void RunPlayerBotYoharaTestFile(DWORD dwNow)
	{
		FILE* fp = fopen(PLAYERBOT_YOHARA_TEST_FILE, "r");
		if (!fp)
			return;
		char line[128];
		std::vector<std::string> lines;
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_YOHARA_TEST_FILE);
		rename(PLAYERBOT_YOHARA_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "", arg[32] = "", what[32] = "";
			long mapArg = 0;
			if (sscanf(lines[l].c_str(), "%31s %31s %31s %ld", cmd, arg, what, &mapArg) < 1)
				continue;
			const int n = !strcmp(arg, "all") ? 100000 : atoi(arg);
			if (!strcmp(cmd, "send"))
			{
				const int purpose = ParsePlayerBotYoharaPurpose(what);
				long map = purpose == YOHARA_PURPOSE_LOOT ? (mapArg >= 301 && mapArg <= 304 ? mapArg :
							(GetPlayerBotYoharaConfig().lootMaps.empty() ? 303 : GetPlayerBotYoharaConfig().lootMaps[0]))
						: GetPlayerBotYoharaPurposeMap(purpose);
				int sent = 0, looked = 0;
				for (TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.begin();
						map != 0 && st != s_mapPlayerBotAIStates.end() && sent < n; ++st)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
					if (!ch || ch->IsDead() || !IsPlayerBotYoharaEligible(ch) || IsPlayerBotYoharaLeaving(st->first) ||
							FindPlayerBotYoharaResident(st->first) || IsPlayerBotOnDungeonRun(st->first))
						continue;
					const int level = ch->GetLevel();
					const bool band = IsPlayerBotYoharaInBand(purpose, level) &&
							(purpose != YOHARA_PURPOSE_ZAKLETY || ch->GetMaxHP() >= GetPlayerBotYoharaConfig().zakletyMinHp);
					++looked;
					if (!band)
						continue;
					long x = 0, y = 0;
					GetPlayerBotFrontierArrival(map, x, y);
					if (RequestPlayerBotYoharaHandover(ch, st->second, map, x, y, purpose, "test_send", dwNow))
						++sent;
				}
				sys_log(0, "PLAYERBOT_YOHARA: test send purpose=%s map=%ld asked=%d sent=%d looked=%d",
						PlayerBotYoharaPurposeName(purpose), map, n, sent, looked);
			}
			else if (!strcmp(cmd, "home"))
			{
				int sent = 0;
				std::vector<DWORD> pids;
				for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
						r != s_mapPlayerBotYoharaResident.end(); ++r)
					pids.push_back(r->first);
				for (size_t i = 0; i < pids.size() && sent < n; ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
					TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pids[i]);
					if (ch && st != s_mapPlayerBotAIStates.end() && SendPlayerBotYoharaHome(ch, st->second, dwNow, "test_home"))
						++sent;
				}
				sys_log(0, "PLAYERBOT_YOHARA: test home asked=%d sent=%d residents=%u", n, sent, (unsigned int)pids.size());
			}
			else if (!strcmp(cmd, "status"))
			{
				s_dwPlayerBotYoharaNextCensusLog = 0;
				for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
						r != s_mapPlayerBotYoharaResident.end(); ++r)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(r->first);
					sys_log(0, "PLAYERBOT_YOHARA: status resident pid=%u name=%s level=%d purpose=%s map=%ld pos=(%ld,%ld) stay_s=%u run=%d",
							r->first, ch ? ch->GetName() : "-", ch ? (int)ch->GetLevel() : 0,
							PlayerBotYoharaPurposeName(r->second.iPurpose), ch ? ch->GetMapIndex() : 0L,
							ch ? ch->GetX() : 0L, ch ? ch->GetY() : 0L, (dwNow - r->second.dwArrived) / 1000,
							IsPlayerBotOnDungeonRun(r->first) ? 1 : 0);
				}
			}
		}
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
		RunPlayerBotYoharaTestFile(dwNow);
		char query[512];
		snprintf(query, sizeof(query),
				"SELECT pid, state, target_map, x, y, purpose, ready_at <= NOW(), "
				"updated_at > DATE_SUB(NOW(), INTERVAL %d SECOND), reason LIKE '%%deaths%%' "
				"FROM common.playerbot_core_handover WHERE channel=%u",
				PLAYERBOT_YOHARA_STALE_S, (unsigned int)g_bChannel);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		struct TRow { DWORD pid; int state; long map, x, y; int purpose; bool ready, fresh, deaths; };
		std::vector<TRow> rows;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			TRow t;
			t.pid = 0; t.state = 0; t.map = t.x = t.y = 0; t.ready = t.fresh = t.deaths = false;
			if (row[0]) str_to_number(t.pid, row[0]);
			if (row[1]) str_to_number(t.state, row[1]);
			if (row[2]) str_to_number(t.map, row[2]);
			if (row[3]) str_to_number(t.x, row[3]);
			if (row[4]) str_to_number(t.y, row[4]);
			t.purpose = ParsePlayerBotYoharaPurpose(row[5]);
			t.ready = row[6] && atoi(row[6]) != 0;
			t.fresh = row[7] && atoi(row[7]) != 0;
			t.deaths = row[8] && atoi(row[8]) != 0;
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
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TRow& t = rows[i];
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
				const bool refused = t.purpose != YOHARA_PURPOSE_HOME && t.purpose != YOHARA_PURPOSE_NONE &&
						residentsHere[t.purpose] >= GetPlayerBotYoharaCap(t.purpose);
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
				a.lMap = t.map; a.lX = t.x; a.lY = t.y; a.iPurpose = t.purpose; a.dwAt = dwNow; a.bDeaths = t.deaths;
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
			// Away from this core: on its way to another, staying there - or on its way here and
			// not ready yet (the other core's save first; the claim above takes it when it is).
			if (CHARACTER_MANAGER::instance().FindByPID(t.pid))
				continue;
			if (t.state == 1 || (t.state == 2 && t.fresh))
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
			// MT2009_PLUS_BOT_YOHARA_FIX_V1: the stay's deaths (a dungeon run counts its own).
			{
				LPCHARACTER rc = CHARACTER_MANAGER::instance().FindByPID(r->first);
				const bool dead = rc && rc->IsDead() && !IsPlayerBotOnDungeonRun(r->first);
				if (dead && !r->second.bDead)
				{
					if (r->second.dwWindowStart == 0 || dwNow - r->second.dwWindowStart > PLAYERBOT_YOHARA_DEATH_WINDOW_MS)
					{
						r->second.dwWindowStart = dwNow;
						r->second.iDeathsWindowed = 0;
					}
					++r->second.iDeaths;
					++r->second.iDeathsWindowed;
					sys_log(0, "PLAYERBOT_YOHARA: died pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) purpose=%s deaths=%d windowed=%d max_hp=%d",
							r->first, rc->GetName(), (unsigned int)rc->GetLevel(), rc->GetMapIndex(), rc->GetX(), rc->GetY(),
							PlayerBotYoharaPurposeName(r->second.iPurpose), r->second.iDeaths, r->second.iDeathsWindowed,
							(int)rc->GetMaxHP());
				}
				r->second.bDead = dead;
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
			sys_log(0, "PLAYERBOT_HANDOVER: census channel=%u on=%d zaklety=%d/%d loot=%d/%d snakefield=%d/%d giantland=%d/%d "
					"residents_here=%u (zaklety=%d loot=%d snakefield=%d giantland=%d) away=%u requests=%u out=%u in=%u home=%u "
					"refused=%u cancel=%u",
					(unsigned int)g_bChannel, IsPlayerBotYoharaOn() ? 1 : 0,
					census[YOHARA_PURPOSE_ZAKLETY], cfg.zakletyMax, census[YOHARA_PURPOSE_LOOT], cfg.lootMax,
					census[YOHARA_PURPOSE_SNAKEFIELD], cfg.snakeMax, census[YOHARA_PURPOSE_GIANTLAND], cfg.giantMax,
					(unsigned int)s_mapPlayerBotYoharaResident.size(),
					residentsHere[YOHARA_PURPOSE_ZAKLETY], residentsHere[YOHARA_PURPOSE_LOOT],
					residentsHere[YOHARA_PURPOSE_SNAKEFIELD], residentsHere[YOHARA_PURPOSE_GIANTLAND],
					(unsigned int)s_setPlayerBotYoharaAway.size(), (unsigned int)s_mapPlayerBotYoharaOut.size(),
					s_uPlayerBotYoharaOutCount, s_uPlayerBotYoharaInCount, s_uPlayerBotYoharaHomeCount,
					s_uPlayerBotYoharaRefusedCount, s_uPlayerBotYoharaCancelCount);
		}
	}
}

#endif
