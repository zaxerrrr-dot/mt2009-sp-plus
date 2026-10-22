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
//     MT2009_PLUS_BOT_YOHARA_MAPS_V1 (22 October): the Hydra's cohort, and the
//     Sung Ma maps for a bot Champion of level 120 - purpose "yohara",
//     playerbot_yohara_sungma.h (the refusal lets such a bot through).
//
// The switches (.env / the Seban panel's env page; docker-compose passes them
// to the game container): PLAYERBOT_HANDOVER (1), PLAYERBOT_HANDOVER_CHANNELS
// ("1"), PLAYERBOT_ZAKLETY_MAX (30 a channel), PLAYERBOT_ZAKLETY_MIN_LEVEL
// (97), PLAYERBOT_SZC_MAX (18), PLAYERBOT_SZC_PARTIES (2), PLAYERBOT_LOOTRUN_MAX
// (6), PLAYERBOT_LOOTRUN_MAPS ("303,304" - the grids of 301/302 are 160/125
// MB). The event flag m2_bot_handover_off (a GM's /e, the panel's flags)
// stops every new handover and sends every resident home.
//
// MT2009_PLUS_BOT_HYDRA_COHORT_V1 (22 October): the Hydra - a purpose of its own ("hydra"): the bots wait on
// the pier of Port Nowego Kontynentu (368) and go onto the ship (367) in their cohort's fixed parties of eight
// (playerbot_dungeon_runs.h, the row "hydra"; PLAYERBOT_HYDRA_MAX, PLAYERBOT_HYDRA_PARTIES); on the pier their
// marbles and ice elixirs are kept up (RestockPlayerBotYoharaHydra).
//
// MT2009_PLUS_BOT_YOHARA_COHORT_V1 (21 October, night): Wezowe Pole (80) and Kraina Gigantow (70) on
// game2 are purposes too (their frontier bands, the draw's quarter each; PLAYERBOT_SNAKEFIELD_MAX,
// PLAYERBOT_GIANTLAND_MAX, PLAYERBOT_WZ_STAY_MIN), and the night's cohorts - see "the cohorts" below
// (PLAYERBOT_COHORT*, the event flag m2_bot_cohort_off).
//
// The log: PLAYERBOT_HANDOVER (out, claimed, arrived, home, refused, cancel,
// census), PLAYERBOT_YOHARA (the temple, the stay, the restock, the loot runs,
// the Time Rift). The operator's hook: the file playerbot_yohara_test in the
// core's directory (RunPlayerBotYoharaTestFile).
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
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole (80) and Kraina Gigantow (70) on game2.
		YOHARA_PURPOSE_SNAKEFIELD,
		YOHARA_PURPOSE_GIANTLAND,
		YOHARA_PURPOSE_HYDRA,	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the pier of the port (368), the ship (367)
		YOHARA_PURPOSE_SUNGMA,	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Sung Ma maps of the Champions (playerbot_yohara_sungma.h)
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
			case YOHARA_PURPOSE_SNAKEFIELD: return "snakefield";	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
			case YOHARA_PURPOSE_GIANTLAND: return "giantland";
			case YOHARA_PURPOSE_HYDRA: return "hydra";	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
			case YOHARA_PURPOSE_SUNGMA: return "yohara";	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
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
		int szcMax, szcParties;
		int lootMax;
		std::vector<long> lootMaps;
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole / Kraina Gigantow, and the cohorts.
		int snakeMax, giantMax, wzStayMin;
		bool cohortOn, cohortExclusive;
		int cohortStayMin, cohortDispatch, cohortRestMin, cohortDeathRestMin;
		int hydraMax, hydraParties;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Sung Ma maps - the channel's limit, a map's, the stay, the maps switched on.
		int sungmaMax, sungmaMapMax, sungmaStayMin;
		std::vector<long> sungmaMaps;
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
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: the test of 21 October - two warriors of 97/101 with 11 250 /
		// 11 550 health died at once; the forest's packs are 3-5 En-Tai of 100-108 (179-290 a blow).
		s_cfg.zakletyMinHp = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MIN_HP", 20000, 0, 1000000);
		s_cfg.szcMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SZC_MAX", 18, 0, 200);
		s_cfg.szcParties = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SZC_PARTIES", 2, 0, 20);
		s_cfg.lootMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_LOOTRUN_MAX", 6, 0, 200);
		std::vector<long> maps;
		ReadPlayerBotYoharaEnvList("PLAYERBOT_LOOTRUN_MAPS", "303,304", maps);
		for (size_t i = 0; i < maps.size(); ++i)
			if (maps[i] >= 301 && maps[i] <= 304 &&
					std::find(s_cfg.lootMaps.begin(), s_cfg.lootMaps.end(), maps[i]) == s_cfg.lootMaps.end())
				s_cfg.lootMaps.push_back(maps[i]);
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: the owner, 21 October (night): "Wezowe Pole i Kraina
		// Gigantow: wlaczyc" - their bands are the frontier's (63-78, 63-80), through the handover to
		// game2; and the night's cohorts (common.playerbot_yohara_cohort, tools/yohara_bot_cohort.py).
		s_cfg.snakeMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SNAKEFIELD_MAX", 50, 0, 300);
		s_cfg.giantMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_GIANTLAND_MAX", 50, 0, 300);
		s_cfg.wzStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_WZ_STAY_MIN", 120, 20, 600);
		s_cfg.cohortOn = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT", 1, 0, 1) != 0;
		s_cfg.cohortExclusive = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT_EXCLUSIVE", 1, 0, 1) != 0;
		s_cfg.cohortStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT_STAY_MIN", 720, 20, 1440);
		s_cfg.cohortDispatch = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT_DISPATCH", 6, 1, 50);
		s_cfg.cohortRestMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT_REST_MIN", 10, 1, 600);
		s_cfg.cohortDeathRestMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_COHORT_DEATH_REST_MIN", 60, 1, 1440);
		// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the owner, 22 October - four parties of eight on the Hydra.
		s_cfg.hydraMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_HYDRA_MAX", 32, 0, 200);
		// MT2009_PLUS_BOT_HYDRA_PAIRS_V1: sixteen pairs, all at once (one ship each).
		s_cfg.hydraParties = ReadPlayerBotYoharaEnvInt("PLAYERBOT_HYDRA_PARTIES", 16, 0, 32);
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the owner, 22 October - 100 bots onto the Yohara maps (the cohort "yohara" and
		// the Champions of the population). PLAYERBOT_SUNGMA_MAPS: the maps of the table switched on (a grid each, built
		// where a bot stands - 18-160 MB, playerbot_navigation.h).
		s_cfg.sungmaMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SUNGMA_MAX", 120, 0, 600);
		s_cfg.sungmaMapMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SUNGMA_MAP_MAX", 30, 0, 300);
		s_cfg.sungmaStayMin = ReadPlayerBotYoharaEnvInt("PLAYERBOT_SUNGMA_STAY_MIN", 240, 20, 1440);
		{
			std::vector<long> sm;
			ReadPlayerBotYoharaEnvList("PLAYERBOT_SUNGMA_MAPS", "374,373,376,377,385,388,389,393,394", sm);
			for (size_t i = 0; i < sm.size(); ++i)
				if (IsPlayerBotSungmaBotMap(sm[i]) && sm[i] < PLAYERBOT_INSTANCE_MAP_INDEX_MIN &&
						std::find(s_cfg.sungmaMaps.begin(), s_cfg.sungmaMaps.end(), sm[i]) == s_cfg.sungmaMaps.end())
					s_cfg.sungmaMaps.push_back(sm[i]);
		}
		std::string chans, loot, sungma;
		for (std::set<int>::const_iterator i = s_cfg.channels.begin(); i != s_cfg.channels.end(); ++i)
			chans += (chans.empty() ? "" : ",") + std::to_string(*i);
		for (size_t i = 0; i < s_cfg.lootMaps.size(); ++i)
			loot += (loot.empty() ? "" : ",") + std::to_string(s_cfg.lootMaps[i]);
		for (size_t i = 0; i < s_cfg.sungmaMaps.size(); ++i)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
			sungma += (sungma.empty() ? "" : ",") + std::to_string(s_cfg.sungmaMaps[i]);
		sys_log(0, "PLAYERBOT_HANDOVER: config on=%d channels=%s zaklety_max=%d zaklety_min_level=%d zaklety_stay_min=%d "
				"zaklety_min_hp=%d szc_max=%d szc_parties=%d loot_max=%d loot_maps=%s snakefield_max=%d giantland_max=%d "
				"wz_stay_min=%d cohort=%d cohort_exclusive=%d cohort_stay_min=%d cohort_dispatch=%d cohort_rest_min=%d "
				"cohort_death_rest_min=%d hydra_max=%d hydra_parties=%d sungma_max=%d sungma_map_max=%d sungma_stay_min=%d "
				"sungma_maps=%s channel_here=%u",
				s_cfg.on ? 1 : 0, chans.c_str(), s_cfg.zakletyMax, s_cfg.zakletyMinLevel, s_cfg.zakletyStayMin, s_cfg.zakletyMinHp,
				s_cfg.szcMax, s_cfg.szcParties, s_cfg.lootMax, loot.c_str(), s_cfg.snakeMax, s_cfg.giantMax, s_cfg.wzStayMin,
				s_cfg.cohortOn ? 1 : 0, s_cfg.cohortExclusive ? 1 : 0, s_cfg.cohortStayMin, s_cfg.cohortDispatch,
				s_cfg.cohortRestMin, s_cfg.cohortDeathRestMin, s_cfg.hydraMax, s_cfg.hydraParties, s_cfg.sungmaMax,
				s_cfg.sungmaMapMax, s_cfg.sungmaStayMin, sungma.c_str(), (unsigned int)g_bChannel);
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

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a purpose's map (the loot runs have several: 0), the
	// purpose of a map, its limit a channel and its band.
	long GetPlayerBotYoharaPurposeMap(int purpose)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY: return PLAYERBOT_MAP_ZAKLETY;
			case YOHARA_PURPOSE_SZC: return PLAYERBOT_MAP_SZC_PLATEAU;
			case YOHARA_PURPOSE_SNAKEFIELD: return PLAYERBOT_MAP_SNAKEFIELD;
			case YOHARA_PURPOSE_GIANTLAND: return PLAYERBOT_MAP_GIANTLAND;
			case YOHARA_PURPOSE_HYDRA: return PLAYERBOT_MAP_HYDRA_PORT;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
			default: return 0;
		}
	}

	int GetPlayerBotYoharaMapPurpose(long base)
	{
		if (base == PLAYERBOT_MAP_ZAKLETY)
			return YOHARA_PURPOSE_ZAKLETY;
		if (base == PLAYERBOT_MAP_SZC_PLATEAU)
			return YOHARA_PURPOSE_SZC;
		if (base == PLAYERBOT_MAP_SNAKEFIELD)
			return YOHARA_PURPOSE_SNAKEFIELD;
		if (base == PLAYERBOT_MAP_GIANTLAND)
			return YOHARA_PURPOSE_GIANTLAND;
		if (base == PLAYERBOT_MAP_HYDRA_PORT)	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
			return YOHARA_PURPOSE_HYDRA;
		if (IsPlayerBotYoharaLootMap(base))
			return YOHARA_PURPOSE_LOOT;
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a Sung Ma map of the bots' table that is switched on
		if (IsPlayerBotSungmaBotMap(base) && std::find(GetPlayerBotYoharaConfig().sungmaMaps.begin(),
				GetPlayerBotYoharaConfig().sungmaMaps.end(), base) != GetPlayerBotYoharaConfig().sungmaMaps.end())
			return YOHARA_PURPOSE_SUNGMA;
		return YOHARA_PURPOSE_NONE;
	}

	int GetPlayerBotYoharaCap(int purpose)
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY: return cfg.zakletyMax;
			case YOHARA_PURPOSE_SZC: return cfg.szcMax;
			case YOHARA_PURPOSE_LOOT: return cfg.lootMax;
			case YOHARA_PURPOSE_SNAKEFIELD: return cfg.snakeMax;
			case YOHARA_PURPOSE_GIANTLAND: return cfg.giantMax;
			case YOHARA_PURPOSE_HYDRA: return cfg.hydraMax;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
			case YOHARA_PURPOSE_SUNGMA: return cfg.sungmaMax;	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
			default: return 0;
		}
	}

	bool IsPlayerBotYoharaInBand(int purpose, int level)
	{
		switch (purpose)
		{
			case YOHARA_PURPOSE_ZAKLETY:
				return level >= GetPlayerBotYoharaConfig().zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL;
			case YOHARA_PURPOSE_SZC:
				return level >= PLAYERBOT_SZC_MIN_LEVEL && level <= PLAYERBOT_SZC_MAX_LEVEL;
			case YOHARA_PURPOSE_SNAKEFIELD:
				return level >= PLAYERBOT_SNAKEFIELD_MIN_LEVEL && level <= PLAYERBOT_SNAKEFIELD_MAX_LEVEL;
			case YOHARA_PURPOSE_GIANTLAND:
				return level >= PLAYERBOT_GIANTLAND_MIN_LEVEL && level <= PLAYERBOT_GIANTLAND_MAX_LEVEL;
			case YOHARA_PURPOSE_LOOT:
				return level >= PLAYERBOT_YOHARA_LOOT_MIN_LEVEL;
			case YOHARA_PURPOSE_HYDRA:	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
				return level >= PLAYERBOT_HYDRA_MIN_LEVEL;
			case YOHARA_PURPOSE_SUNGMA:	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the server's top level (and a Champion - the map's pick)
				return level >= gPlayerMaxLevel;
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
		DWORD dwArrived, dwLastRun, dwNextRestock, dwOffRunSince;
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: the stay's deaths (counted by the poll, outside a dungeon run).
		bool bDead;
		int iDeaths, iDeathsWindowed;
		DWORD dwWindowStart;
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: the experience the poll last saw (a cohort's EXP an hour).
		int iLastLevel;
		DWORD dwLastExp, dwLastNeed;
		long long llExpUnsaved;	// written to the cohort's row at the census
		DWORD dwNextTidy;	// a member's bag: its junk sold where it stands
		DWORD dwNextKit;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's marbles and elixirs looked at
		TPlayerBotYoharaResident() : iPurpose(0), lMap(0), dwArrived(0), dwLastRun(0), dwNextRestock(0), dwOffRunSince(0),
			bDead(false), iDeaths(0), iDeathsWindowed(0), dwWindowStart(0), iLastLevel(0), dwLastExp(0), dwLastNeed(0),
			llExpUnsaved(0), dwNextTidy(0), dwNextKit(0) {}
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

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: the cohorts, below.
	bool IsPlayerBotYoharaCohortHeld(DWORD pid);

	bool IsPlayerBotYoharaAway(DWORD pid)
	{
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: claimed by this core - its Spawn is the claim's.
		if (s_mapPlayerBotYoharaArrival.count(pid) != 0)
			return false;
		return s_setPlayerBotYoharaAway.count(pid) != 0 || s_mapPlayerBotYoharaOut.count(pid) != 0 ||
				s_mapPlayerBotYoharaLeaving.count(pid) != 0 ||
				IsPlayerBotYoharaCohortHeld(pid);	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
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

	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: a bot the handover brought to the port for the Hydra.
	bool IsPlayerBotYoharaHydraResident(DWORD pid)
	{
		std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.find(pid);
		return r != s_mapPlayerBotYoharaResident.end() && r->second.iPurpose == YOHARA_PURPOSE_HYDRA;
	}

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a cohort's bot stays its own (long) time; Wezowe Pole and
	// Kraina Gigantow are expeditions too (a trip there is a handover each way).
	bool IsPlayerBotYoharaCohortPID(DWORD pid);

	DWORD GetPlayerBotYoharaStayMs(LPCHARACTER ch, long mapIndex)
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		DWORD ms = 0;
		if (mapIndex == PLAYERBOT_MAP_ZAKLETY)
			ms = (DWORD)cfg.zakletyStayMin * 60000U;
		else if ((mapIndex == PLAYERBOT_MAP_SNAKEFIELD || mapIndex == PLAYERBOT_MAP_GIANTLAND) && ch &&
				FindPlayerBotYoharaResident(ch->GetPlayerID()))
			ms = (DWORD)cfg.wzStayMin * 60000U;
		else if (IsPlayerBotSungmaBotMap(mapIndex) && ch && FindPlayerBotYoharaResident(ch->GetPlayerID()))	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
			ms = (DWORD)cfg.sungmaStayMin * 60000U;
		if (ms != 0 && ch && IsPlayerBotYoharaCohortPID(ch->GetPlayerID()))
			ms = std::max<DWORD>(ms, (DWORD)cfg.cohortStayMin * 60000U);
		return ms;
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
		return mapIndex == PLAYERBOT_MAP_ZAKLETY || mapIndex == PLAYERBOT_MAP_SZC_PLATEAU || IsPlayerBotYoharaLootMap(mapIndex) ||
				mapIndex == PLAYERBOT_MAP_SNAKEFIELD || mapIndex == PLAYERBOT_MAP_GIANTLAND ||	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
				mapIndex == PLAYERBOT_MAP_HYDRA_PORT ||	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
				GetPlayerBotYoharaMapPurpose(mapIndex) == YOHARA_PURPOSE_SUNGMA;	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
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

	// ------------------------------------------------------------ the cohorts

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1 - the owner, 21 October 2026 (night): "Kohorty na noc: 100
	// botow Zaklety Las (super EQ, rozne klasy), 100 botow lvl 110 na SZC Zaklety Las, 2 x 50 botow:
	// Wezowe Pole i Kraina Gigantow. Cala noc." The members are rows of common.playerbot_yohara_cohort
	// (pid, purpose, channel, rest_until and the night's counters), written - with their level, gear
	// and skills - by tools/yohara_bot_cohort.py's SQL while the game is stopped; deleting the rows
	// dissolves the cohorts (the event flag m2_bot_cohort_off, or PLAYERBOT_COHORT=0, sets them aside
	// without touching the table).
	//
	//   * A member never loads on its home core while the cohorts are on: it is "held" there
	//     (IsPlayerBotYoharaAway - Spawn and the top-up step over it), and that core's dispatcher
	//     writes its handover row straight away (state 1, ready at once) - the other core claims it
	//     and loads it on its purpose's map. A member that is online at home (it was when the
	//     cohort was made, or the cohorts were off) is handed over from where it stands, the
	//     Temple of Ochao left out. game1 of the first channel is at its 4 GB limit: a member costs
	//     it nothing.
	//   * There it stays PLAYERBOT_COHORT_STAY_MIN; what would send another resident home (the
	//     stay over, its deaths, the band) logs it out where it is instead - "rest out", the row
	//     gone and rest_until set (PLAYERBOT_COHORT_REST_MIN, after its deaths
	//     PLAYERBOT_COHORT_DEATH_REST_MIN) - and the dispatcher sends it again after the rest. A
	//     full bag is no reason for it (the belt is kept full where it stands, its gold is the
	//     cohort's), only no weapon, no armour, no arrows.
	//   * A purpose with members is theirs alone while PLAYERBOT_COHORT_EXCLUSIVE: the population's
	//     own bots are not drawn to it.
	//   * Never rested by the life schedule, retired, renamed a Legend, taken for a companion or
	//     an idle reserve; always an alchemy user.
	//   * The log: PLAYERBOT_COHORT (loaded, dispatch, rest out, census per purpose - members,
	//     resting, here, in the map, on a run, staying on the channel's other cores, sent, arrived,
	//     deaths, runs, rest-outs, levels and experience gained here and the experience an hour).

	struct TPlayerBotYoharaCohortMember
	{
		int iPurpose;
		int iChannel;
		bool bResting;
		int iLevel;	// player.player's: the db core's last save
		int iParty;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's fixed party (1-4), 0 for none
		// MT2009_PLUS_BOT_CHAMPION_V1: the Hydra's runs won (the row's wins) and the statue's errand (the row's
		// champion: YOHARA_CHAMPION_*).
		int iWins, iChampion;
		int iChampionLevel;	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: player.player's conqueror_level (the dispatcher's band)
		TPlayerBotYoharaCohortMember() : iPurpose(0), iChannel(0), bResting(false), iLevel(0), iParty(0), iWins(0), iChampion(0),
			iChampionLevel(0) {}
	};
	struct TPlayerBotYoharaCohortStats
	{
		unsigned int sent, arrived, deaths, runs, restOuts, levels;
		unsigned int wins;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's runs won (member-runs)
		long long exp, expAtCensus;
		TPlayerBotYoharaCohortStats() : sent(0), arrived(0), deaths(0), runs(0), restOuts(0), levels(0), wins(0), exp(0), expAtCensus(0) {}
	};

	const DWORD PLAYERBOT_YOHARA_COHORT_LOAD_MS = 60000;
	const DWORD PLAYERBOT_YOHARA_COHORT_TIDY_MS = 5 * 60 * 1000;
	// An online member at home whose bag or belt its own visit is sorting out: handed over anyway after this.
	const DWORD PLAYERBOT_YOHARA_COHORT_HOME_PATIENCE_MS = 15 * 60 * 1000;
	std::map<DWORD, TPlayerBotYoharaCohortMember> s_mapPlayerBotYoharaCohort;
	int s_aiPlayerBotYoharaCohortSize[YOHARA_PURPOSE_MAX] = { 0 };
	TPlayerBotYoharaCohortStats s_aPlayerBotYoharaCohortStats[YOHARA_PURPOSE_MAX];
	std::map<DWORD, DWORD> s_mapPlayerBotYoharaCohortHomeSince;
	bool s_bPlayerBotYoharaCohortTableReady = false;
	bool s_bPlayerBotYoharaCohortHydraColumns = false;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: party, wins
	bool s_bPlayerBotYoharaCohortChampionColumns = false;	// MT2009_PLUS_BOT_CHAMPION_V1: champion, champion_at
	bool s_bPlayerBotYoharaCohortLoaded = false;
	DWORD s_dwPlayerBotYoharaCohortNextLoad = 0;
	DWORD s_dwPlayerBotYoharaCohortLastCensus = 0;
	size_t s_uPlayerBotYoharaCohortCursor = 0;

	bool EnsurePlayerBotYoharaCohortTable()
	{
		if (s_bPlayerBotYoharaCohortTableReady)
			return true;
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS common.playerbot_yohara_cohort ("
				"pid INT UNSIGNED NOT NULL PRIMARY KEY, purpose VARCHAR(16) NOT NULL, "
				"channel TINYINT UNSIGNED NOT NULL DEFAULT 1, rest_until DATETIME NULL, "
				"created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
				"level_start TINYINT UNSIGNED NOT NULL DEFAULT 0, exp_start INT UNSIGNED NOT NULL DEFAULT 0, "
				"sent INT UNSIGNED NOT NULL DEFAULT 0, arrived INT UNSIGNED NOT NULL DEFAULT 0, "
				"deaths INT UNSIGNED NOT NULL DEFAULT 0, runs INT UNSIGNED NOT NULL DEFAULT 0, "
				"rest_outs INT UNSIGNED NOT NULL DEFAULT 0, exp_gained BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"last_map INT NOT NULL DEFAULT 0, last_seen DATETIME NULL, applied_at DATETIME NULL, "
				"party TINYINT UNSIGNED NOT NULL DEFAULT 0, wins INT UNSIGNED NOT NULL DEFAULT 0, "
				"champion TINYINT UNSIGNED NOT NULL DEFAULT 0, champion_at DATETIME NULL, "	// MT2009_PLUS_BOT_CHAMPION_V1
				"KEY purpose (purpose)) ENGINE=InnoDB"));
		s_bPlayerBotYoharaCohortTableReady = msg.get() && msg->uiSQLErrno == 0;
		// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's fixed party and its wins on a table of the night before (the
		// cohort tool's SQL adds them too); without them the cohorts load as before, every party 0.
		if (s_bPlayerBotYoharaCohortTableReady)
		{
			std::unique_ptr<SQLMsg> alter(AccountDB::instance().DirectQuery(
					"ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS party TINYINT UNSIGNED NOT NULL DEFAULT 0, "
					"ADD COLUMN IF NOT EXISTS wins INT UNSIGNED NOT NULL DEFAULT 0"));
			// (another core's ALTER at the same moment may fail this one: the columns are what counts)
			std::unique_ptr<SQLMsg> cols(AccountDB::instance().DirectQuery(
					"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'common' AND "
					"table_name = 'playerbot_yohara_cohort' AND column_name IN ('party', 'wins')"));
			MYSQL_ROW crow = cols.get() && cols->uiSQLErrno == 0 && cols->Get() && cols->Get()->pSQLResult
					? mysql_fetch_row(cols->Get()->pSQLResult) : NULL;
			s_bPlayerBotYoharaCohortHydraColumns = crow && crow[0] && atoi(crow[0]) == 2;
			if (!s_bPlayerBotYoharaCohortHydraColumns)
				sys_err("PLAYERBOT_COHORT: common.playerbot_yohara_cohort has no party/wins columns - the Hydra's parties by kingdom only");
			// MT2009_PLUS_BOT_CHAMPION_V1: the statue's errand of the Hydra's members (0 the Hydra, 1 the errand ahead,
			// 2 a Champion, 3 done without it) - the cohort tool's --hydra-end sets 1, the core that hosts the statue
			// writes 2/3 and champion_at.
			std::unique_ptr<SQLMsg> alter2(AccountDB::instance().DirectQuery(
					"ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS champion TINYINT UNSIGNED NOT NULL DEFAULT 0, "
					"ADD COLUMN IF NOT EXISTS champion_at DATETIME NULL"));
			std::unique_ptr<SQLMsg> cols2(AccountDB::instance().DirectQuery(
					"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'common' AND "
					"table_name = 'playerbot_yohara_cohort' AND column_name IN ('champion', 'champion_at')"));
			MYSQL_ROW crow2 = cols2.get() && cols2->uiSQLErrno == 0 && cols2->Get() && cols2->Get()->pSQLResult
					? mysql_fetch_row(cols2->Get()->pSQLResult) : NULL;
			s_bPlayerBotYoharaCohortChampionColumns = s_bPlayerBotYoharaCohortHydraColumns && crow2 && crow2[0] && atoi(crow2[0]) == 2;
			if (!s_bPlayerBotYoharaCohortChampionColumns)
				sys_err("PLAYERBOT_COHORT: common.playerbot_yohara_cohort has no champion columns - the Hydra's end by the event flag only");
		}
		if (!s_bPlayerBotYoharaCohortTableReady)
			sys_err("PLAYERBOT_COHORT: common.playerbot_yohara_cohort cannot be made");
		return s_bPlayerBotYoharaCohortTableReady;
	}

	void LoadPlayerBotYoharaCohort(DWORD dwNow, bool force)
	{
		if (!force && s_bPlayerBotYoharaCohortLoaded && (int)(dwNow - s_dwPlayerBotYoharaCohortNextLoad) < 0)
			return;
		s_bPlayerBotYoharaCohortLoaded = true;
		s_dwPlayerBotYoharaCohortNextLoad = dwNow + PLAYERBOT_YOHARA_COHORT_LOAD_MS;
		if (!GetPlayerBotYoharaConfig().cohortOn || !EnsurePlayerBotYoharaCohortTable())
		{
			if (GetPlayerBotYoharaConfig().cohortOn)
				s_dwPlayerBotYoharaCohortNextLoad = dwNow + PLAYERBOT_YOHARA_POLL_MS;	// the database not there yet
			s_mapPlayerBotYoharaCohort.clear();
			for (int p = 0; p < YOHARA_PURPOSE_MAX; ++p)
				s_aiPlayerBotYoharaCohortSize[p] = 0;
			return;
		}
		// MT2009_PLUS_BOT_CHAMPION_V1: the wins and the statue's errand too.
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(s_bPlayerBotYoharaCohortChampionColumns
				? "SELECT c.pid, c.purpose, c.channel, IFNULL(c.rest_until > NOW(), 0), IFNULL(p.level, 0), c.party, c.wins, c.champion, "
				  "IFNULL(p.conqueror_level, 0) "	// MT2009_PLUS_BOT_YOHARA_MAPS_V1 (czempion.sql's column)
				  "FROM common.playerbot_yohara_cohort AS c LEFT JOIN player.player AS p ON p.id = c.pid"
				: s_bPlayerBotYoharaCohortHydraColumns
				? "SELECT c.pid, c.purpose, c.channel, IFNULL(c.rest_until > NOW(), 0), IFNULL(p.level, 0), c.party, c.wins, 0 "
				  "FROM common.playerbot_yohara_cohort AS c LEFT JOIN player.player AS p ON p.id = c.pid"
				: "SELECT c.pid, c.purpose, c.channel, IFNULL(c.rest_until > NOW(), 0), IFNULL(p.level, 0), 0, 0, 0 "
				  "FROM common.playerbot_yohara_cohort AS c LEFT JOIN player.player AS p ON p.id = c.pid"));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
		{
			s_dwPlayerBotYoharaCohortNextLoad = dwNow + PLAYERBOT_YOHARA_POLL_MS;
			return;
		}
		std::map<DWORD, TPlayerBotYoharaCohortMember> fresh;
		int size[YOHARA_PURPOSE_MAX] = { 0 };
		int resting = 0;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			DWORD pid = 0;
			if (row[0])
				str_to_number(pid, row[0]);
			const int purpose = ParsePlayerBotYoharaPurpose(row[1]);
			if (pid == 0 || purpose == YOHARA_PURPOSE_NONE || purpose == YOHARA_PURPOSE_HOME || purpose == YOHARA_PURPOSE_LOOT)
				continue;
			TPlayerBotYoharaCohortMember& m = fresh[pid];
			m.iPurpose = purpose;
			m.iChannel = row[2] ? atoi(row[2]) : 0;
			m.bResting = row[3] && atoi(row[3]) != 0;
			m.iLevel = row[4] ? atoi(row[4]) : 0;
			m.iParty = row[5] ? atoi(row[5]) : 0;	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
			m.iWins = row[6] ? atoi(row[6]) : 0;	// MT2009_PLUS_BOT_CHAMPION_V1
			m.iChampion = row[7] ? atoi(row[7]) : 0;
			m.iChampionLevel = mysql_num_fields(msg->Get()->pSQLResult) > 8 && row[8] ? atoi(row[8]) : 0;	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
			++size[purpose];
			resting += m.bResting ? 1 : 0;
		}
		const bool changed = fresh.size() != s_mapPlayerBotYoharaCohort.size();
		s_mapPlayerBotYoharaCohort.swap(fresh);
		for (int p = 0; p < YOHARA_PURPOSE_MAX; ++p)
			s_aiPlayerBotYoharaCohortSize[p] = size[p];
		if (changed)
			sys_log(0, "PLAYERBOT_COHORT: loaded members=%u (zaklety=%d szc=%d snakefield=%d giantland=%d hydra=%d yohara=%d) resting=%d channel_here=%u",
					(unsigned int)s_mapPlayerBotYoharaCohort.size(), size[YOHARA_PURPOSE_ZAKLETY], size[YOHARA_PURPOSE_SZC],
					size[YOHARA_PURPOSE_SNAKEFIELD], size[YOHARA_PURPOSE_GIANTLAND], size[YOHARA_PURPOSE_HYDRA],
					size[YOHARA_PURPOSE_SUNGMA], resting, (unsigned int)g_bChannel);
	}

	bool IsPlayerBotYoharaCohortOn()
	{
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		return cfg.on && cfg.cohortOn && quest::CQuestManager::instance().GetEventFlag("m2_bot_cohort_off") == 0;
	}

	// ------------------------------------------------------------ the Hydra's end (MT2009_PLUS_BOT_CHAMPION_V1)

	// The owner, 22 October: "Kiedy beda wyniki Hydry, konczymy testowanie Hydry i teraz spraw, zeby boty poszly
	// do posagu po poziom Czempiona." The Hydra ends for the cohort by the event flag m2_bot_hydra_end (a GM's /e,
	// the panel's flags), PLAYERBOT_HYDRA_END=1, or a member's row (champion 1 - the cohort tool's --hydra-end SQL,
	// read every minute). An ended member is called for no ship; one with a won run and no Champion level yet goes to
	// the statue (ManagePlayerBotYoharaChampion) - and is the cohort's until it has been there; every other ended
	// member is an ordinary bot again (not held, not sent, back home through the handover).
	enum
	{
		YOHARA_CHAMPION_HYDRA = 0,		// the Hydra goes on
		YOHARA_CHAMPION_PENDING = 1,	// the Hydra ended: the statue's errand ahead
		YOHARA_CHAMPION_UNLOCKED = 2,	// a Champion (the statue's, or already one)
		YOHARA_CHAMPION_SKIPPED = 3,	// done without it (no won run, the statue refused)
	};

	bool IsPlayerBotHydraEndSwitched()
	{
		static int s_iEnv = -1;
		if (s_iEnv < 0)
			s_iEnv = ReadPlayerBotYoharaEnvInt("PLAYERBOT_HYDRA_END", 0, 0, 1);
		return s_iEnv != 0 || quest::CQuestManager::instance().GetEventFlag("m2_bot_hydra_end") != 0;
	}

	bool IsPlayerBotYoharaHydraMemberEnded(const TPlayerBotYoharaCohortMember& m)
	{
		return m.iPurpose == YOHARA_PURPOSE_HYDRA && (m.iChampion != YOHARA_CHAMPION_HYDRA || IsPlayerBotHydraEndSwitched());
	}

	// The statue's errand still ahead: the Hydra ended for it, a run won, no Champion level (its own, while it is
	// in this world).
	bool IsPlayerBotYoharaChampionPending(DWORD pid, const TPlayerBotYoharaCohortMember& m)
	{
		if (!IsPlayerBotYoharaHydraMemberEnded(m) || m.iChampion >= YOHARA_CHAMPION_UNLOCKED || m.iWins < 1)
			return false;
#ifdef ENABLE_CONQUEROR_LEVEL
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (ch && ch->GetConquerorLevel() >= 1)
			return false;
#endif
		return true;
	}

	const TPlayerBotYoharaCohortMember* FindPlayerBotYoharaCohortMember(DWORD pid)
	{
		if (!s_bPlayerBotYoharaCohortLoaded)
			LoadPlayerBotYoharaCohort(get_dword_time(), true);
		if (s_mapPlayerBotYoharaCohort.empty())
			return NULL;
		std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator it = s_mapPlayerBotYoharaCohort.find(pid);
		if (it == s_mapPlayerBotYoharaCohort.end() || !IsPlayerBotYoharaCohortOn())
			return NULL;
		// MT2009_PLUS_BOT_CHAMPION_V1: an ended Hydra member with no errand ahead is an ordinary bot again.
		if (IsPlayerBotYoharaHydraMemberEnded(it->second) && !IsPlayerBotYoharaChampionPending(pid, it->second))
			return NULL;
		return &it->second;
	}

	// The Hydra ended for this bot (a member's row, or the switch): no ship for it (PlanPlayerBotHydraRuns), the
	// statue's errand on the pier (ManagePlayerBotYoharaTravel).
	bool IsPlayerBotYoharaHydraEndedFor(DWORD pid)
	{
		if (IsPlayerBotHydraEndSwitched())
			return true;
		std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator it = s_mapPlayerBotYoharaCohort.find(pid);
		return it != s_mapPlayerBotYoharaCohort.end() && IsPlayerBotYoharaHydraMemberEnded(it->second);
	}

	bool IsPlayerBotYoharaCohortPID(DWORD pid)
	{
		return FindPlayerBotYoharaCohortMember(pid) != NULL;
	}

	int GetPlayerBotYoharaCohortPurpose(DWORD pid)
	{
		const TPlayerBotYoharaCohortMember* m = FindPlayerBotYoharaCohortMember(pid);
		return m ? m->iPurpose : YOHARA_PURPOSE_NONE;
	}

	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's fixed party of a member (0: none, or not of the Hydra's cohort),
	// the runs at once on this core.
	int GetPlayerBotYoharaHydraParty(DWORD pid)
	{
		const TPlayerBotYoharaCohortMember* m = FindPlayerBotYoharaCohortMember(pid);
		return m && m->iPurpose == YOHARA_PURPOSE_HYDRA ? m->iParty : 0;
	}

	int GetPlayerBotYoharaHydraParties()
	{
		return GetPlayerBotYoharaConfig().hydraParties;
	}

	// Not to be loaded here: a member of this channel's cohorts, not in this world, while the
	// handover of this channel is on (the dispatcher writes its row; a claim's Spawn passes).
	bool IsPlayerBotYoharaCohortHeld(DWORD pid)
	{
		const TPlayerBotYoharaCohortMember* m = FindPlayerBotYoharaCohortMember(pid);
		return m && m->iChannel == (int)g_bChannel && IsPlayerBotYoharaOn() &&
				CHARACTER_MANAGER::instance().FindByPID(pid) == NULL;
	}

	// MT2009_PLUS_BOT_YOHARA_COHORT_PIN_V1: the channel coordinator's moves pass the members by -
	// on the first night's run it sent them to channel 2 by the dozen, and each came back at the
	// next dispatch to be sent away again. A clause for its UPDATEs ("" with no cohorts).
	std::string PlayerBotYoharaCohortChannelPin()
	{
		if (s_mapPlayerBotYoharaCohort.empty() || !IsPlayerBotYoharaCohortOn())
			return "";
		return " AND pid NOT IN (SELECT pid FROM common.playerbot_yohara_cohort)";
	}

	// A purpose with members is theirs alone.
	bool IsPlayerBotYoharaPurposeReserved(int purpose)
	{
		return purpose > 0 && purpose < YOHARA_PURPOSE_MAX && s_aiPlayerBotYoharaCohortSize[purpose] > 0 &&
				GetPlayerBotYoharaConfig().cohortExclusive && IsPlayerBotYoharaCohortOn();
	}

	// The purpose a member goes for at this level: its own, or from 110 the Time Rift for one of the
	// forest's (the owner's route) - NONE when neither fits.
	int GetPlayerBotYoharaCohortPurposeAt(int purpose, int level)
	{
		if (IsPlayerBotYoharaInBand(purpose, level))
			return purpose;
		if (purpose == YOHARA_PURPOSE_ZAKLETY && IsPlayerBotYoharaInBand(YOHARA_PURPOSE_SZC, level))
			return YOHARA_PURPOSE_SZC;
		return YOHARA_PURPOSE_NONE;
	}

	// One of the night's counters in the table (the summary script reads them).
	void NotePlayerBotYoharaCohortDb(DWORD pid, const char* column, long long add, long mapIndex)
	{
		if (!s_bPlayerBotYoharaCohortTableReady || !column)
			return;
		char q[256];
		snprintf(q, sizeof(q), "UPDATE common.playerbot_yohara_cohort SET %s = %s + %lld, last_map = %ld, last_seen = NOW() "
				"WHERE pid = %u", column, column, add, mapIndex, pid);
		RunPlayerBotYoharaSql(q);
	}

	// The experience of a member staying here since the last poll (the level's own need for a level-up).
	void TrackPlayerBotYoharaCohortExp(LPCHARACTER ch, TPlayerBotYoharaResident& r)
	{
		if (!ch || !IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) || r.iPurpose <= 0 || r.iPurpose >= YOHARA_PURPOSE_MAX)
			return;
		const int level = ch->GetLevel();
		const DWORD exp = ch->GetExp();
		if (r.iLastLevel == 0)
		{
			r.iLastLevel = level;
			r.dwLastExp = exp;
			r.dwLastNeed = ch->GetNextExp();
			return;
		}
		long long gained = 0;
		if (level == r.iLastLevel)
			gained = exp > r.dwLastExp ? (long long)(exp - r.dwLastExp) : 0;
		else if (level > r.iLastLevel)
		{
			gained = (r.dwLastNeed > r.dwLastExp ? (long long)(r.dwLastNeed - r.dwLastExp) : 0) + (long long)exp;
			s_aPlayerBotYoharaCohortStats[r.iPurpose].levels += (unsigned int)(level - r.iLastLevel);
			sys_log(0, "PLAYERBOT_COHORT: level up pid=%u name=%s purpose=%s level=%d->%d map=%ld",
					ch->GetPlayerID(), ch->GetName(), PlayerBotYoharaPurposeName(r.iPurpose), r.iLastLevel, level,
					ch->GetMapIndex());
		}
		if (gained > 0)
		{
			s_aPlayerBotYoharaCohortStats[r.iPurpose].exp += gained;
			r.llExpUnsaved += gained;
		}
		r.iLastLevel = level;
		r.dwLastExp = exp;
		r.dwLastNeed = ch->GetNextExp();
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

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member's way "home" - out of the world where it stands, its
	// row gone, a rest written to its cohort row; its home core's dispatcher sends it again after it.
	bool IsPlayerBotYoharaDeathsOver(const TPlayerBotYoharaResident& r);

	bool RestOutPlayerBotYoharaCohort(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow, const char* why)
	{
		if (!ch)
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (s_mapPlayerBotYoharaLeaving.count(pid))
			return true;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		std::map<DWORD, TPlayerBotYoharaResident>::iterator r = s_mapPlayerBotYoharaResident.find(pid);
		const bool deaths = r != s_mapPlayerBotYoharaResident.end() && IsPlayerBotYoharaDeathsOver(r->second);
		const int purpose = r != s_mapPlayerBotYoharaResident.end() ? r->second.iPurpose : GetPlayerBotYoharaCohortPurpose(pid);
		const int restMin = deaths ? cfg.cohortDeathRestMin : cfg.cohortRestMin;
		char q[256];
		snprintf(q, sizeof(q), "UPDATE common.playerbot_yohara_cohort SET rest_until = DATE_ADD(NOW(), INTERVAL %d MINUTE), "
				"rest_outs = rest_outs + 1, exp_gained = exp_gained + %lld, last_map = %ld, last_seen = NOW() WHERE pid = %u",
				restMin, r != s_mapPlayerBotYoharaResident.end() ? r->second.llExpUnsaved : 0LL, ch->GetMapIndex(), pid);
		RunPlayerBotYoharaSql(q);
		if (r != s_mapPlayerBotYoharaResident.end())
			r->second.llExpUnsaved = 0;
		snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid = %u", pid);
		RunPlayerBotYoharaSql(q);
		std::map<DWORD, TPlayerBotYoharaCohortMember>::iterator m = s_mapPlayerBotYoharaCohort.find(pid);
		if (m != s_mapPlayerBotYoharaCohort.end())
			m->second.bResting = true;
		if (purpose > 0 && purpose < YOHARA_PURPOSE_MAX)
			++s_aPlayerBotYoharaCohortStats[purpose].restOuts;
		if (ch->GetParty())
			LeavePlayerBotParty(ch);
		ClosePlayerBotShop(ch, state, dwNow, "cohort_rest");
		ClearPlayerBotRoute(state, true);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		TPlayerBotYoharaLeave& leave = s_mapPlayerBotYoharaLeaving[pid];
		leave.lMap = 0;
		leave.iPurpose = YOHARA_PURPOSE_HOME;
		sys_log(0, "PLAYERBOT_COHORT: rest out pid=%u name=%s level=%u map=%ld purpose=%s stay_s=%u rest_min=%d why=%s",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), PlayerBotYoharaPurposeName(purpose),
				r != s_mapPlayerBotYoharaResident.end() && r->second.dwArrived ? (dwNow - r->second.dwArrived) / 1000 : 0,
				restMin, why ? why : "-");
		return true;
	}

	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Sung Ma maps - their table, the pick, the points, the stay, the census.
	bool IsPlayerBotYoharaFightStopped(LPCHARACTER ch, const TPlayerBotYoharaResident& r, DWORD dwNow);
#include "playerbot_yohara_sungma.h"

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
			// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member rests out where it stands instead - also when
			// m2_bot_handover_off sends every resident home (game1 of the first channel has no room
			// for 300 more at once).
			if (IsPlayerBotYoharaCohortPID(pid))
				return RestOutPlayerBotYoharaCohort(ch, state, dwNow, reason ? reason : "home") ? 1 : 0;
			return RequestPlayerBotYoharaHandover(ch, state, base, targetX, targetY, YOHARA_PURPOSE_HOME,
					reason ? reason : "home", dwNow) ? 1 : 0;
		}
		if (!IsPlayerBotYoharaOn())
			return -1;
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole and Kraina Gigantow join the purposes.
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
			// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member goes straight there.
			if (IsPlayerBotYoharaCohortPID(pid))
				return RequestPlayerBotYoharaHandover(ch, state, base, PLAYERBOT_ZAKLETY_ARRIVAL_X,
						PLAYERBOT_ZAKLETY_ARRIVAL_Y, purpose, "cohort", dwNow) ? 1 : 0;
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
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a Sung Ma map's own room too
		if (purpose == YOHARA_PURPOSE_SUNGMA)
		{
			const int slot = GetPlayerBotSungmaSlot(base);
			if (slot < 0 || !HasPlayerBotSungmaRoom(slot, 0))
			{
				s_mapPlayerBotYoharaCooldown[pid] = dwNow + PLAYERBOT_YOHARA_REFUSED_COOLDOWN_MS;
				PlayerBotLogThrottled("handover_sungma_cap", dwNow, "PLAYERBOT_HANDOVER: refused pid=%u name=%s to=%ld purpose=yohara why=map_cap",
						pid, ch->GetName(), base);
				s_szPlayerBotTransitionRefusal = "yohara_cap";
				return 0;
			}
			++s_aiPlayerBotSungmaMapCensus[slot];
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
				case YOHARA_PURPOSE_SZC:
					return level >= PLAYERBOT_SZC_MIN_LEVEL && level <= PLAYERBOT_SZC_MAX_LEVEL &&
							IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SZC_PLATEAU) ? PLAYERBOT_MAP_SZC_PLATEAU : 0;
				case YOHARA_PURPOSE_LOOT:
					return IsPlayerBotMapHostedHere(r->lMap) && dwNow - r->dwArrived < PLAYERBOT_YOHARA_LOOT_STAY_MS
							? r->lMap : 0;
				// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole / Kraina Gigantow, while the band lasts.
				case YOHARA_PURPOSE_SNAKEFIELD:
				case YOHARA_PURPOSE_GIANTLAND:
				case YOHARA_PURPOSE_HYDRA:	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the pier, while the band lasts
				{
					const long m = GetPlayerBotYoharaPurposeMap(r->iPurpose);
					return IsPlayerBotYoharaInBand(r->iPurpose, level) && IsPlayerBotMapHostedHere(m) ? m : 0;
				}
				// MT2009_PLUS_BOT_YOHARA_MAPS_V1: its Sung Ma map (ManagePlayerBotSungmaResident moves it between them)
				case YOHARA_PURPOSE_SUNGMA:
					return IsPlayerBotYoharaInBand(r->iPurpose, level) && IsPlayerBotMapHostedHere(r->lMap) ? r->lMap : 0;
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
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member of a cohort, online at home: its purpose, no draw
		// (the dispatcher hands it over; this keeps its own travel pointed there meanwhile).
		{
			const int cohort = GetPlayerBotYoharaCohortPurpose(pid);
			if (cohort != YOHARA_PURPOSE_NONE)
			{
				const int p = GetPlayerBotYoharaCohortPurposeAt(cohort, level);
				if (p == YOHARA_PURPOSE_SUNGMA)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the map by its Champion level and Will
					return s_aiPlayerBotYoharaCensus[p] < GetPlayerBotYoharaCap(p) ? PickPlayerBotSungmaMap(ch, 0) : 0;
				if (p != YOHARA_PURPOSE_NONE && s_aiPlayerBotYoharaCensus[p] < GetPlayerBotYoharaCap(p))
					return GetPlayerBotYoharaPurposeMap(p);
				return 0;
			}
		}
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a Champion of the top level - the Sung Ma maps (its map by its Champion level
		// and Will), while the channel has room and no cohort holds them.
		if (IsPlayerBotSungmaCandidate(ch) && s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SUNGMA] < cfg.sungmaMax &&
				!IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_SUNGMA))
		{
			const long sungma = PickPlayerBotSungmaMap(ch, 0);
			if (sungma != 0)
				return sungma;
		}
		// A loot run now and then (in a village, at most every half hour a bot).
		const long loot = GetPlayerBotYoharaLootPlan(ch, dwNow);
		if (loot != 0)
			return loot;
		// The Time Rift: three in four of the band, while there is room.
		if (level >= PLAYERBOT_SZC_MIN_LEVEL && level <= PLAYERBOT_SZC_MAX_LEVEL && cfg.szcMax > 0 &&
				s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SZC] < cfg.szcMax &&
				!IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_SZC) &&	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
				PlayerBotNavHash(pid ^ 0x535a4331U) % 4U != 0)
			return PLAYERBOT_MAP_SZC_PLATEAU;
		// Zaklety Las: two in three of the band, while there is room (and a
		// bot already on its way through the temple keeps it).
		const bool inTemple = s_mapPlayerBotYoharaTemple.count(pid) != 0;
		// MT2009_PLUS_BOT_YOHARA_FIX_V1: strong enough for the forest's packs (PLAYERBOT_ZAKLETY_MIN_HP).
		if (level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL && ch->GetMaxHP() < cfg.zakletyMinHp)
			PlayerBotLogThrottled("zaklety_weak", dwNow, "PLAYERBOT_YOHARA: too weak for the forest pid=%u name=%s level=%d max_hp=%d need=%d",
					pid, ch->GetName(), level, (int)ch->GetMaxHP(), cfg.zakletyMinHp);
		if (level >= cfg.zakletyMinLevel && level <= PLAYERBOT_ZAKLETY_MAX_LEVEL && cfg.zakletyMax > 0 &&
				ch->GetMaxHP() >= cfg.zakletyMinHp && IsPlayerBotOchaoHosted() &&
				(inTemple || (s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_ZAKLETY] < cfg.zakletyMax &&
				 !IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_ZAKLETY))) &&	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
				PlayerBotNavHash(pid ^ 0x5a4b4c53U) % 3U != 0)
			return PLAYERBOT_MAP_ZAKLETY;
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole (80) and Kraina Gigantow (70) on game2 - the
		// quarter of the draw each that playerbot_travel.h gives them on a core hosting them (the same
		// hash), here through the handover, within PLAYERBOT_SNAKEFIELD_MAX / PLAYERBOT_GIANTLAND_MAX.
		{
			const DWORD wz = PlayerBotNavHash(pid ^ 0x575a4d50U) % 4U;
			if (wz == 1 && !stoneHunter && IsPlayerBotYoharaInBand(YOHARA_PURPOSE_SNAKEFIELD, level) && cfg.snakeMax > 0 &&
					s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SNAKEFIELD] < cfg.snakeMax &&
					!IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_SNAKEFIELD) &&
					!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SNAKEFIELD))
				return PLAYERBOT_MAP_SNAKEFIELD;
			if (wz == 2 && IsPlayerBotYoharaInBand(YOHARA_PURPOSE_GIANTLAND, level) && cfg.giantMax > 0 &&
					s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_GIANTLAND] < cfg.giantMax &&
					!IsPlayerBotYoharaPurposeReserved(YOHARA_PURPOSE_GIANTLAND) &&
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
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member never goes to town for its bag (the cohorts' bags are full -
		// 170 things in some on the test world): its junk is sold at the merchants' price where it stands, by
		// the town visit's own rule, once in PLAYERBOT_YOHARA_COHORT_TIDY_MS while no column of three is free.
		if (IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) && (int)(dwNow - r.dwNextTidy) >= 0)
		{
			r.dwNextTidy = dwNow + PLAYERBOT_YOHARA_COHORT_TIDY_MS;
			if (ch->GetEmptyInventory(3) < 0)
			{
				SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_MISC, "cohort_misc");
				SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_WEAPON, "cohort_weapon");
				SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_ARMOR, "cohort_armor");
				if (ch->GetEmptyInventory(1) < 0)
					PlayerBotLogThrottled("cohort_bag", dwNow, "PLAYERBOT_COHORT: bag still full pid=%u name=%s map=%ld",
							ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex());
			}
		}
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		// MT2009_PLUS_BOT_YOHARA_COHORT_POTIONS_V1: a member short of potions with no free cell for them makes
		// one - its junk first, then the cheapest thing in the bag (never worn, locked, a potion, a quest item
		// or a watch), sold where it stands. On the first cohort night 76 of the forest's 198 rest-outs in two
		// hours were bots that arrived with a full bag and few reds: the restock could not buy and the potion
		// check sent them to rest at once (stay 0-22 s).
		if (IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) && red < PLAYERBOT_YOHARA_BELT_RED && ch->GetEmptyInventory(1) < 0)
		{
			SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_MISC, "cohort_misc");
			SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_WEAPON, "cohort_weapon");
			SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_ARMOR, "cohort_armor");
			for (int freed = 0; freed < 2 && ch->GetEmptyInventory(1) < 0; ++freed)
			{
				LPITEM cheapest = NULL;
				long long cheapestPrice = 0;
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
				{
					LPITEM item = ch->GetInventoryItem(cell);
					if (!item || item->IsEquipped() || item->isLocked() || item->GetType() == ITEM_QUEST ||
							item->GetVnum() == PLAYERBOT_YOHARA_SZC_WATCH ||
							(item->GetVnum() >= 27001 && item->GetVnum() <= 27008) ||
							GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE)
						continue;
					const long long price = GetPlayerBotJunkSalePrice(item);
					if (!cheapest || price < cheapestPrice)
					{
						cheapest = item;
						cheapestPrice = price;
					}
				}
				if (!cheapest)
					break;
				sys_log(0, "PLAYERBOT_COHORT: cell freed for potions pid=%u name=%s vnum=%u count=%u gold=%lld",
						ch->GetPlayerID(), ch->GetName(), cheapest->GetVnum(), (unsigned int)cheapest->GetCount(), cheapestPrice);
				PlayerBotChangeGold(ch, cheapestPrice);
				ITEM_MANAGER::instance().RemoveItem(cheapest, "PLAYERBOT_COHORT_SELL");
			}
		}
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

	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's kit kept up on the pier - an Archer Ninja's Marmur Polimorfii
	// (70104, socket 0 its monster: Dziki Sluga / Ork / Trujacy Pajak by its pid, or the one it already carries) at
	// PLAYERBOT_YOHARA_HYDRA_MARBLES, and every member's two ice elixirs (Eliksir Mroznej Mocy 50831 - Sila Lodu,
	// Eliksir Odp. na Lod 50837) at PLAYERBOT_YOHARA_HYDRA_ELIXIRS, at their best (20% for 10 minutes: the
	// sockets the brewing would roll, blend.eliksiry.txt), and an archer's arrows. The owner, 22 October: "Mozesz im dac tez mikstury lodu
	// z Yohary" - given, not bought (the cohort's kit, like its gear).
	const int PLAYERBOT_YOHARA_HYDRA_MARBLES = 3;
	const int PLAYERBOT_YOHARA_HYDRA_ELIXIRS = 10;
	const int PLAYERBOT_YOHARA_HYDRA_ARROWS = 400;
	const DWORD PLAYERBOT_YOHARA_HYDRA_ARROW = 8005;	// Srebrna Strzala
	const DWORD PLAYERBOT_YOHARA_HYDRA_KIT_MS = 60000;

	void RestockPlayerBotYoharaHydra(LPCHARACTER ch, TPlayerBotYoharaResident& r, DWORD dwNow)
	{
		if ((int)(dwNow - r.dwNextKit) < 0 || ch->IsDead() || !ch->IsItemLoaded())
			return;
		r.dwNextKit = dwNow + PLAYERBOT_YOHARA_HYDRA_KIT_MS;
		int marbles = 0, elixirs = 0;
		if (IsPlayerBotHydraPolymorpher(ch))
		{
			DWORD mob = PLAYERBOT_HYDRA_POLY_MOBS[ch->GetPlayerID() % 3];
			const int have = CountPlayerBotHydraMarbles(ch);
			const int cell = FindPlayerBotHydraMarble(ch);
			if (cell >= 0)
				mob = (DWORD)ch->GetInventoryItem(cell)->GetSocket(0);
			for (int n = have; n < PLAYERBOT_YOHARA_HYDRA_MARBLES && ch->GetEmptyInventory(1) >= 0; ++n)
			{
				LPITEM m = ch->AutoGiveItem(PLAYERBOT_HYDRA_MARBLE, 1, -1, false);
				if (!m)
					break;
				m->SetSocket(0, mob);
				++marbles;
			}
		}
		// An archer's arrows (Srebrna Strzala), two hundred more under PLAYERBOT_YOHARA_HYDRA_ARROWS.
		int arrows = 0;
		if (IsPlayerBotHydraPolymorpher(ch) && CountPlayerBotArrows(ch) < PLAYERBOT_YOHARA_HYDRA_ARROWS && ch->GetEmptyInventory(1) >= 0 &&
				ch->AutoGiveItem(PLAYERBOT_YOHARA_HYDRA_ARROW, 200, -1, false))
			arrows = 200;
		static const DWORD vnums[2] = { PLAYERBOT_HYDRA_ELIXIR_POWER, PLAYERBOT_HYDRA_ELIXIR_RESIST };
		static const long points[2] = { POINT_ENCHANT_ICE, POINT_RESIST_ICE };
		for (int i = 0; i < 2; ++i)
		{
			const int have = (int)ch->CountSpecifyItem(vnums[i]);
			if (have >= PLAYERBOT_YOHARA_HYDRA_ELIXIRS / 2 || ch->GetEmptyInventory(1) < 0)
				continue;
			LPITEM it = ch->AutoGiveItem(vnums[i], PLAYERBOT_YOHARA_HYDRA_ELIXIRS - have, -1, false);
			if (!it)
				continue;
			it->SetSocket(0, points[i]);
			it->SetSocket(1, 20);
			it->SetSocket(2, 600);
			elixirs += PLAYERBOT_YOHARA_HYDRA_ELIXIRS - have;
		}
		if (marbles || elixirs || arrows)
			sys_log(0, "PLAYERBOT_HYDRA: kit pid=%u name=%s party=%d marbles+=%d elixirs+=%d arrows+=%d marbles=%d", ch->GetPlayerID(),
					ch->GetName(), GetPlayerBotYoharaHydraParty(ch->GetPlayerID()), marbles, elixirs, arrows,
					CountPlayerBotHydraMarbles(ch));
	}

	// ------------------------------------------------------------ the statue (MT2009_PLUS_BOT_CHAMPION_V1)

	// The champion's errand of a Hydra member whose Hydra ended (IsPlayerBotYoharaHydraEndedFor), on the pier of
	// Port Nowego Kontynentu (368, this core: the Hydra's residents live there). A player's way, done for the bot:
	//   * the Hydra's flags: obrona_statku.quest's mark_done gives a person at the Hydra's death completed (+1),
	//     completed_at and, from level 120, completed_at_120 (champion::HYDRA_DONE_FLAG, what the statue asks) -
	//     the quest leaves bots out, so they are set here once, completed raised by the member's won runs;
	//   * the walk to Posag Wojownika (20433, czempion.quest; npc.txt of the port: cells 241,574), found on the map
	//     (else its npc.txt spot); a walk that has not got there in PLAYERBOT_CHAMPION_WALK_MS is put beside it;
	//   * the statue's own path: champion::UnlockState (level 120, the Hydra's flag, a full bubble of experience)
	//     and champion::Unlock (pc.set_conqueror - Champion level 1, its experience and points 0, saved,
	//     CHAMPION_UNLOCK in the log, the blue level over its head);
	//   * the member's row: champion 2 (or 3: no won run, the statue refused) and champion_at - from then on an
	//     ordinary bot (FindPlayerBotYoharaCohortMember), sent home by the handover; the bot keeps level and gear.
	// The log: PLAYERBOT_CHAMPION (start, flags, arrived, unlocked, refused, skip, census).
	const DWORD PLAYERBOT_CHAMPION_STATUE = 20433;
	const long PLAYERBOT_CHAMPION_STATUE_X = (1280 + 241) * 100;	// the port's base 128000,563200 (Town.txt)
	const long PLAYERBOT_CHAMPION_STATUE_Y = (5632 + 574) * 100;
	const int PLAYERBOT_CHAMPION_STATUE_USE = 450;
	const DWORD PLAYERBOT_CHAMPION_WALK_MS = 4 * 60 * 1000;

	struct TPlayerBotChampionErrand
	{
		DWORD dwStart, dwWalkSince;
		bool bArrived;
		TPlayerBotChampionErrand() : dwStart(0), dwWalkSince(0), bArrived(false) {}
	};
	std::map<DWORD, TPlayerBotChampionErrand> s_mapPlayerBotChampionErrand;
	unsigned int s_uPlayerBotChampionUnlocked = 0, s_uPlayerBotChampionRefused = 0, s_uPlayerBotChampionSkipped = 0;

	struct FPlayerBotFindStatue
	{
		LPCHARACTER m_found;
		FPlayerBotFindStatue() : m_found(NULL) {}
		void operator()(LPENTITY entity)
		{
			if (m_found || !entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER npc = static_cast<LPCHARACTER>(entity);
			if (!npc->IsPC() && npc->GetRaceNum() == PLAYERBOT_CHAMPION_STATUE)
				m_found = npc;
		}
	};

	// The errand's end in the member's row and in this core's copy of it (ended: an ordinary bot from now on).
	void FinishPlayerBotChampionErrand(LPCHARACTER ch, int result, const char* why)
	{
		const DWORD pid = ch->GetPlayerID();
		s_mapPlayerBotChampionErrand.erase(pid);
		std::map<DWORD, TPlayerBotYoharaCohortMember>::iterator m = s_mapPlayerBotYoharaCohort.find(pid);
		if (m != s_mapPlayerBotYoharaCohort.end() && m->second.iPurpose == YOHARA_PURPOSE_HYDRA)
		{
			m->second.iChampion = result;
			if (s_bPlayerBotYoharaCohortChampionColumns)
			{
				char q[192];
				snprintf(q, sizeof(q), "UPDATE common.playerbot_yohara_cohort SET champion = %d, champion_at = NOW(), "
						"last_seen = NOW() WHERE pid = %u", result, pid);
				RunPlayerBotYoharaSql(q);
			}
		}
		if (result == YOHARA_CHAMPION_UNLOCKED)
			++s_uPlayerBotChampionUnlocked;
		else if (!strcmp(why, "refused"))
			++s_uPlayerBotChampionRefused;
		else
			++s_uPlayerBotChampionSkipped;
	}

	// -1 nothing here, 0/1 the travel pass's answer (ManagePlayerBotYoharaTravel's Hydra case).
	int ManagePlayerBotYoharaChampion(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		const long mapIndex = ch->GetMapIndex();
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator m = s_mapPlayerBotYoharaCohort.find(pid);
		const int wins = m != s_mapPlayerBotYoharaCohort.end() ? m->second.iWins : 0;
#ifndef ENABLE_CONQUEROR_LEVEL
		sys_log(0, "PLAYERBOT_CHAMPION: skip pid=%u name=%s why=no_champion_system", pid, ch->GetName());
		FinishPlayerBotChampionErrand(ch, YOHARA_CHAMPION_SKIPPED, "no_champion_system");
		return SendPlayerBotYoharaHome(ch, state, dwNow, "hydra_end") ? 1 : 0;
#else
		// Already a Champion, or nothing to go there for: done, home.
		const char* skip = NULL;
		int result = YOHARA_CHAMPION_SKIPPED;
		if (ch->GetConquerorLevel() >= 1)
		{
			skip = "already";
			result = YOHARA_CHAMPION_UNLOCKED;
		}
		else if (m == s_mapPlayerBotYoharaCohort.end() || m->second.iPurpose != YOHARA_PURPOSE_HYDRA)
			skip = "not_member";
		else if (wins < 1)
			skip = "no_win";
		else if (ch->GetLevel() < gPlayerMaxLevel)
			skip = "level";
		if (skip)
		{
			sys_log(0, "PLAYERBOT_CHAMPION: skip pid=%u name=%s level=%u conqueror_level=%u wins=%d why=%s",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetConquerorLevel(), wins, skip);
			FinishPlayerBotChampionErrand(ch, result, skip);
			return SendPlayerBotYoharaHome(ch, state, dwNow, "hydra_end") ? 1 : 0;
		}
		// Off the pier's map (a ship left by no run): the pier first.
		if (base != PLAYERBOT_MAP_HYDRA_PORT)
			return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_HYDRA_PORT, PLAYERBOT_HYDRA_PORT_X,
					PLAYERBOT_HYDRA_PORT_Y, dwNow, "champion_to_port") ? 1 : 0;
		TPlayerBotChampionErrand& e = s_mapPlayerBotChampionErrand[pid];
		if (e.dwStart == 0)
		{
			e.dwStart = dwNow ? dwNow : 1;
			if (ch->GetParty())
				LeavePlayerBotParty(ch);
			sys_log(0, "PLAYERBOT_CHAMPION: start pid=%u name=%s level=%u wins=%d map=%ld pos=(%ld,%ld)",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), wins, mapIndex, ch->GetX(), ch->GetY());
		}
		// The Hydra's flags, as obrona_statku.quest's mark_done gives them to a person (once).
		if (ch->GetQuestFlag(champion::HYDRA_DONE_FLAG) <= 0)
		{
			const int completed = MAX(0, ch->GetQuestFlag("obrona_statku.completed")) + wins;
			ch->SetQuestFlag("obrona_statku.completed", completed);
			ch->SetQuestFlag("obrona_statku.completed_at", (int)get_global_time());
			ch->SetQuestFlag(champion::HYDRA_DONE_FLAG, 1);
			sys_log(0, "PLAYERBOT_CHAMPION: flags pid=%u name=%s completed=%d %s=1", pid, ch->GetName(), completed,
					champion::HYDRA_DONE_FLAG);
		}
		// The statue.
		long sx = PLAYERBOT_CHAMPION_STATUE_X, sy = PLAYERBOT_CHAMPION_STATUE_Y;
		{
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(mapIndex);
			FPlayerBotFindStatue f;
			if (pMap)
				pMap->for_each(f);
			if (f.m_found)
			{
				sx = f.m_found->GetX();
				sy = f.m_found->GetY();
			}
		}
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		const int d = DISTANCE_APPROX(ch->GetX() - sx, ch->GetY() - sy);
		if (d > PLAYERBOT_CHAMPION_STATUE_USE)
		{
			if (e.dwWalkSince == 0)
				e.dwWalkSince = dwNow ? dwNow : 1;
			if (dwNow - e.dwWalkSince >= PLAYERBOT_CHAMPION_WALK_MS)
			{
				sys_log(0, "PLAYERBOT_CHAMPION: walk too long, put beside the statue pid=%u name=%s pos=(%ld,%ld) statue=(%ld,%ld) after_s=%u",
						pid, ch->GetName(), ch->GetX(), ch->GetY(), sx, sy, (dwNow - e.dwWalkSince) / 1000);
				ch->Stop();
				ch->Show(mapIndex, sx + 200, sy + 200, 0);
				e.dwWalkSince = dwNow ? dwNow : 1;
				return 1;
			}
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBot(ch, sx, sy, dwNow, 6, true, false, false, false);
			return 1;
		}
		ch->Stop();
		if (!e.bArrived)
		{
			e.bArrived = true;
			sys_log(0, "PLAYERBOT_CHAMPION: arrived pid=%u name=%s pos=(%ld,%ld) statue=(%ld,%ld) found=%d walk_s=%u",
					pid, ch->GetName(), ch->GetX(), ch->GetY(), sx, sy,
					(sx != PLAYERBOT_CHAMPION_STATUE_X || sy != PLAYERBOT_CHAMPION_STATUE_Y) ? 1 : 0,
					e.dwWalkSince ? (dwNow - e.dwWalkSince) / 1000 : 0);
		}
		// czempion.quest: "Zostan Czempionem" - pc.get_conqueror_unlock_state, then pc.set_conqueror.
		const int st = champion::UnlockState(ch);
		if (st == 0 && champion::Unlock(ch))
		{
			sys_log(0, "PLAYERBOT_CHAMPION: unlocked pid=%u name=%s level=%u conqueror_level=%u wins=%d took_s=%u",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetConquerorLevel(), wins,
					(dwNow - e.dwStart) / 1000);
			FinishPlayerBotChampionErrand(ch, YOHARA_CHAMPION_UNLOCKED, "unlocked");
		}
		else
		{
			sys_log(0, "PLAYERBOT_CHAMPION: refused pid=%u name=%s level=%u state=%d exp=%u next_exp=%u flag=%d",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), st, (unsigned int)ch->GetExp(),
					(unsigned int)ch->GetNextExp(), ch->GetQuestFlag(champion::HYDRA_DONE_FLAG));
			FinishPlayerBotChampionErrand(ch, YOHARA_CHAMPION_SKIPPED, "refused");
		}
		// Done: an ordinary bot again (the Yohara maps come later) - home by the handover.
		return SendPlayerBotYoharaHome(ch, state, dwNow, "champion_done") ? 1 : 0;
#endif
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
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member - only what stops the fight (the bag is no reason).
		if (IsPlayerBotYoharaCohortPID(ch->GetPlayerID()))
			return false;
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
			// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole / Kraina Gigantow - frontiers of game2, as the forest.
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
				else if (dwNow - res.dwArrived >= (IsPlayerBotYoharaCohortPID(pid)	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
						? (DWORD)GetPlayerBotYoharaConfig().cohortStayMin * 60000U : PLAYERBOT_YOHARA_SZC_STAY_MS))
					why = "szc_stay_over";
				else if (dwNow - idleFrom >= PLAYERBOT_YOHARA_SZC_IDLE_MS)
					why = "szc_no_party";
				else if (IsPlayerBotYoharaFightStopped(ch, res, dwNow))
					why = "szc_blocked";
				else if (IsPlayerBotYoharaDeathsOver(res))
					why = "szc_deaths";
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
			// MT2009_PLUS_BOT_HYDRA_COHORT_V1: the pier between the runs, the ship in them (the Time Rift's way).
			case YOHARA_PURPOSE_HYDRA:
			{
				if (IsPlayerBotOnDungeonRun(pid))
				{
					res.dwLastRun = dwNow;
					res.dwOffRunSince = 0;
					return 0;
				}
				// MT2009_PLUS_BOT_CHAMPION_V1: the Hydra ended for it - the statue, then home.
				if (IsPlayerBotYoharaHydraEndedFor(pid))
					return ManagePlayerBotYoharaChampion(ch, state, res, dwNow);
				// the kit first: an archer short of arrows is given them here, not sent home for them
				RestockPlayerBotYoharaHydra(ch, res, dwNow);
				const DWORD idleFrom = res.dwLastRun ? res.dwLastRun : res.dwArrived;
				const char* why = NULL;
				if (!IsPlayerBotYoharaInBand(YOHARA_PURPOSE_HYDRA, level))
					why = "hydra_level";
				else if (dwNow - res.dwArrived >= (DWORD)GetPlayerBotYoharaConfig().cohortStayMin * 60000U)
					why = "hydra_stay_over";
				else if (dwNow - idleFrom >= PLAYERBOT_YOHARA_SZC_IDLE_MS)
					why = "hydra_no_party";
				else if (IsPlayerBotYoharaFightStopped(ch, res, dwNow))
					why = "hydra_blocked";
				if (why)
					return SendPlayerBotYoharaHome(ch, state, dwNow, why) ? 1 : 0;
				if (base == PLAYERBOT_MAP_HYDRA_PORT)
				{
					res.dwOffRunSince = 0;
					return 0;	// on the pier till its party is called
				}
				// Left on a ship by no run, or somewhere else of this core: back to the pier.
				if (res.dwOffRunSince == 0)
					res.dwOffRunSince = dwNow;
				if (base == PLAYERBOT_MAP_HYDRA_SHIP && dwNow - res.dwOffRunSince < PLAYERBOT_YOHARA_SZC_LOST_MS)
					return 0;
				return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_HYDRA_PORT, PLAYERBOT_HYDRA_PORT_X,
						PLAYERBOT_HYDRA_PORT_Y, dwNow, "hydra_to_pier") ? 1 : 0;
			}
			// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Sung Ma maps (playerbot_yohara_sungma.h)
			case YOHARA_PURPOSE_SUNGMA:
				return ManagePlayerBotSungmaResident(ch, state, res, dwNow);
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
				// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member's arrival.
				if (IsPlayerBotYoharaCohortPID(a->first))
				{
					++s_aPlayerBotYoharaCohortStats[res.iPurpose].arrived;
					NotePlayerBotYoharaCohortDb(a->first, "arrived", 1, ch->GetMapIndex());
					TrackPlayerBotYoharaCohortExp(ch, res);
				}
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

	// ------------------------------------------------------------ the operator

	// The test hook: a file "playerbot_yohara_test" in the core's directory, read at the poll and
	// renamed to .done (the Ochao/Arezzo tests' way):
	//     send <n> zaklety|szc|loot [map]   n bots of this core of the purpose's band straight to the
	//                                       other core (the temple's road left out: a test of the handover)
	//     home <n|all>                      residents of this core sent home
	//     status                            the census and every resident here, one line each
	//     cohort                            common.playerbot_yohara_cohort read again (MT2009_PLUS_BOT_YOHARA_COHORT_V1)
	//     (send takes snakefield|giantland too, and hydra - MT2009_PLUS_BOT_HYDRA_COHORT_V1; and yohara - the Champions,
	//      each to its Sung Ma map - MT2009_PLUS_BOT_YOHARA_MAPS_V1)
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
						: GetPlayerBotYoharaPurposeMap(purpose);	// MT2009_PLUS_BOT_YOHARA_COHORT_V1 (snakefield, giantland)
				int sent = 0, looked = 0;
				// MT2009_PLUS_BOT_YOHARA_MAPS_V1: "send <n> yohara" - each Champion to its own Sung Ma map
				const bool sungma = purpose == YOHARA_PURPOSE_SUNGMA;
				if (sungma)
					map = 1;
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
					const long target = sungma ? PickPlayerBotSungmaMap(ch, 0) : map;	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
					if (target == 0)
						continue;
					long x = 0, y = 0;
					GetPlayerBotFrontierArrival(target, x, y);
					if (RequestPlayerBotYoharaHandover(ch, st->second, target, x, y, purpose, "test_send", dwNow))
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
			// MT2009_PLUS_BOT_YOHARA_COHORT_V1: "cohort" - the table read again now.
			else if (!strcmp(cmd, "cohort"))
			{
				LoadPlayerBotYoharaCohort(dwNow, true);
				s_dwPlayerBotYoharaNextCensusLog = 0;
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

	// ------------------------------------------------------------ the dispatcher

	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: on the core that hosts a member's first village (its home),
	// at the poll: up to PLAYERBOT_COHORT_DISPATCH members a poll whose purpose has room and who are
	// not on their way, staying, resting or cooling down - an offline one by a row written here (the
	// claim loads it on the other core; never in this world), an online one from where it stands.
	void DispatchPlayerBotYoharaCohort(DWORD dwNow, const std::set<DWORD>& seen, const std::set<DWORD>& live,
			int (&census)[YOHARA_PURPOSE_MAX])
	{
		if (s_mapPlayerBotYoharaCohort.empty() || !IsPlayerBotYoharaOn() || !IsPlayerBotYoharaCohortOn())
			return;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		CPlayerBotManager& mgr = CPlayerBotManager::instance();
		static const long PLAYERBOT_YOHARA_FIRST_VILLAGE[4] = { 0, 1, 21, 41 };
		std::vector<DWORD> pids;
		pids.reserve(s_mapPlayerBotYoharaCohort.size());
		for (std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator i = s_mapPlayerBotYoharaCohort.begin();
				i != s_mapPlayerBotYoharaCohort.end(); ++i)
			pids.push_back(i->first);
		const size_t n = pids.size();
		int sent = 0;
		size_t k = 0;
		for (; k < n && sent < cfg.cohortDispatch; ++k)
		{
			const DWORD pid = pids[(s_uPlayerBotYoharaCohortCursor + k) % n];
			const TPlayerBotYoharaCohortMember& m = s_mapPlayerBotYoharaCohort[pid];
			// MT2009_PLUS_BOT_CHAMPION_V1: after the Hydra only a member with the statue's errand ahead goes there.
			if (IsPlayerBotYoharaHydraMemberEnded(m) && !IsPlayerBotYoharaChampionPending(pid, m))
				continue;
			if (m.iChannel != (int)g_bChannel || m.bResting || live.count(pid) || s_mapPlayerBotYoharaOut.count(pid) ||
					s_mapPlayerBotYoharaLeaving.count(pid) || s_mapPlayerBotYoharaArrival.count(pid) ||
					s_mapPlayerBotYoharaResident.count(pid) || !mgr.IsRegisteredBotPID(pid))
				continue;
			const BYTE empire = mgr.GetRegisteredEmpire(pid);
			if (empire < 1 || empire > 3 || !IsPlayerBotMapHostedHere(PLAYERBOT_YOHARA_FIRST_VILLAGE[empire]))
				continue;
			std::map<DWORD, DWORD>::iterator cd = s_mapPlayerBotYoharaCooldown.find(pid);
			if (cd != s_mapPlayerBotYoharaCooldown.end())
			{
				if ((int)(cd->second - dwNow) > 0)
					continue;
				s_mapPlayerBotYoharaCooldown.erase(cd);
			}
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			const int level = ch ? (int)ch->GetLevel() : m.iLevel;
			const int purpose = GetPlayerBotYoharaCohortPurposeAt(m.iPurpose, level);
			if (purpose == YOHARA_PURPOSE_NONE)
			{
				PlayerBotLogThrottled("cohort_band", dwNow, "PLAYERBOT_COHORT: out of its band pid=%u purpose=%s level=%d",
						pid, PlayerBotYoharaPurposeName(m.iPurpose), level);
				continue;
			}
			if (census[purpose] >= GetPlayerBotYoharaCap(purpose))
				continue;
			// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a Sung Ma member's map - by its Champion level and Will online, by the
			// band offline (the cohort tool gave it the Will of its band's map).
			const long map = purpose != YOHARA_PURPOSE_SUNGMA ? GetPlayerBotYoharaPurposeMap(purpose)
					: (ch ? PickPlayerBotSungmaMap(ch, 0) : PickPlayerBotSungmaMapByBand(m.iChampionLevel));
			long x = 0, y = 0;
			if (map == 0 || !GetPlayerBotFrontierArrival(map, x, y))
				continue;
			if (ch)
			{
				TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pid);
				if (st == s_mapPlayerBotAIStates.end() || ch->IsDead() || !ch->GetSectree() || !IsPlayerBotYoharaEligible(ch) ||
						IsPlayerBotOnDungeonRun(pid))
					continue;
				DWORD& since = s_mapPlayerBotYoharaCohortHomeSince[pid];
				if (since == 0)
					since = dwNow;
				// Its own town visit first (a bag to sell, a belt to buy), for a while.
				if (BlocksPlayerBotTravel(ch) && dwNow - since < PLAYERBOT_YOHARA_COHORT_HOME_PATIENCE_MS)
					continue;
				if (!RequestPlayerBotYoharaHandover(ch, st->second, map, x, y, purpose, "cohort", dwNow))
					continue;
				s_mapPlayerBotYoharaCohortHomeSince.erase(pid);
			}
			else
			{
				if (P2P_MANAGER::instance().FindByPID(pid))
					continue;
				// A stay row nobody refreshes any more (its core gone): not a stay.
				char q[640];
				if (seen.count(pid))
				{
					snprintf(q, sizeof(q), "DELETE FROM common.playerbot_core_handover WHERE pid = %u AND state = 2 AND "
							"updated_at < DATE_SUB(NOW(), INTERVAL %d SECOND)", pid, PLAYERBOT_YOHARA_STALE_S);
					if (RunPlayerBotYoharaSql(q) != 1)
						continue;
				}
				// One statement: no row while its rest lasts (another core's rest-out writes it first).
				snprintf(q, sizeof(q),
						"INSERT IGNORE INTO common.playerbot_core_handover (pid, channel, target_map, x, y, from_map, purpose, "
						"state, reason, ready_at, updated_at) SELECT %u, %u, %ld, %ld, %ld, 0, '%s', 1, 'cohort', NOW(), NOW() "
						"FROM common.playerbot_yohara_cohort WHERE pid = %u AND (rest_until IS NULL OR rest_until <= NOW())",
						pid, (unsigned int)g_bChannel, map, x, y, PlayerBotYoharaPurposeName(purpose), pid);
				if (RunPlayerBotYoharaSql(q) != 1)
					continue;
				TPlayerBotYoharaOut& out = s_mapPlayerBotYoharaOut[pid];
				out.dwAt = dwNow;
				out.iPurpose = purpose;
				out.lMap = map;
				++s_aiPlayerBotYoharaCensus[purpose];
				++s_uPlayerBotYoharaOutCount;
			}
			++census[purpose];
			if (purpose == YOHARA_PURPOSE_SUNGMA && GetPlayerBotSungmaSlot(map) >= 0 && !ch)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
				++s_aiPlayerBotSungmaMapCensus[GetPlayerBotSungmaSlot(map)];
			++sent;
			++s_aPlayerBotYoharaCohortStats[purpose].sent;
			NotePlayerBotYoharaCohortDb(pid, "sent", 1, map);
			sys_log(0, "PLAYERBOT_COHORT: dispatch pid=%u name=%s level=%d purpose=%s to=%ld online_here=%d census=%d/%d",
					pid, ch ? ch->GetName() : "-", level, PlayerBotYoharaPurposeName(purpose), map, ch ? 1 : 0, census[purpose],
					GetPlayerBotYoharaCap(purpose));
		}
		s_uPlayerBotYoharaCohortCursor = n ? (s_uPlayerBotYoharaCohortCursor + k) % n : 0;
	}

	// The census of the cohorts on this core (every PLAYERBOT_YOHARA_CENSUS_LOG_MS): a line a purpose.
	void LogPlayerBotYoharaCohortCensus(DWORD dwNow, const int (&staying)[YOHARA_PURPOSE_MAX], const int (&onWay)[YOHARA_PURPOSE_MAX])
	{
		if (s_mapPlayerBotYoharaCohort.empty())
			return;
		int members[YOHARA_PURPOSE_MAX] = { 0 }, resting[YOHARA_PURPOSE_MAX] = { 0 };
		int here[YOHARA_PURPOSE_MAX] = { 0 }, inMap[YOHARA_PURPOSE_MAX] = { 0 }, onRun[YOHARA_PURPOSE_MAX] = { 0 };
		int lvSum[YOHARA_PURPOSE_MAX] = { 0 };
		std::string expCase, expPids;	// one UPDATE for the experience of all of them
		for (std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator i = s_mapPlayerBotYoharaCohort.begin();
				i != s_mapPlayerBotYoharaCohort.end(); ++i)
		{
			++members[i->second.iPurpose];
			resting[i->second.iPurpose] += i->second.bResting ? 1 : 0;
		}
		for (std::map<DWORD, TPlayerBotYoharaResident>::iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
		{
			const int p = r->second.iPurpose;
			if (p <= 0 || p >= YOHARA_PURPOSE_MAX || !s_mapPlayerBotYoharaCohort.count(r->first))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(r->first);
			if (!ch)
				continue;
			++here[p];
			lvSum[p] += ch->GetLevel();
			const long base = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
			if (base == GetPlayerBotYoharaPurposeMap(p) || (p == YOHARA_PURPOSE_SZC && base == PLAYERBOT_MAP_SZC) ||
					(p == YOHARA_PURPOSE_HYDRA && base == PLAYERBOT_MAP_HYDRA_SHIP))	// MT2009_PLUS_BOT_HYDRA_COHORT_V1
				++inMap[p];
			if (IsPlayerBotOnDungeonRun(r->first))
				++onRun[p];
			// The experience it made, into its row.
			if (r->second.llExpUnsaved > 0)
			{
				expCase += " WHEN " + std::to_string(r->first) + " THEN " + std::to_string(r->second.llExpUnsaved);
				expPids += (expPids.empty() ? "" : ",") + std::to_string(r->first);
				r->second.llExpUnsaved = 0;
			}
		}
		if (!expPids.empty() && s_bPlayerBotYoharaCohortTableReady)
		{
			const std::string q = "UPDATE common.playerbot_yohara_cohort SET exp_gained = exp_gained + CASE pid" + expCase +
					" ELSE 0 END, last_seen = NOW() WHERE pid IN (" + expPids + ")";
			RunPlayerBotYoharaSql(q.c_str());
		}
		const DWORD span = s_dwPlayerBotYoharaCohortLastCensus ? dwNow - s_dwPlayerBotYoharaCohortLastCensus : 0;
		for (int p = YOHARA_PURPOSE_ZAKLETY; p < YOHARA_PURPOSE_MAX; ++p)
		{
			TPlayerBotYoharaCohortStats& st = s_aPlayerBotYoharaCohortStats[p];
			if (members[p] == 0 && here[p] == 0)
				continue;
			const long long expH = span > 0 ? (st.exp - st.expAtCensus) * 3600000LL / (long long)span : 0;
			sys_log(0, "PLAYERBOT_COHORT: census channel=%u purpose=%s members=%d resting=%d channel_staying=%d channel_on_way=%d "
					"here=%d in_map=%d on_run=%d avg_level=%d sent=%u arrived=%u deaths=%u runs=%u rest_outs=%u levels=%u "
					"exp=%lld exp_h=%lld wins=%u",
					(unsigned int)g_bChannel, PlayerBotYoharaPurposeName(p), members[p], resting[p], staying[p], onWay[p],
					here[p], inMap[p], onRun[p], here[p] ? lvSum[p] / here[p] : 0, st.sent, st.arrived, st.deaths, st.runs,
					st.restOuts, st.levels, st.exp, expH, st.wins);
			st.expAtCensus = st.exp;
		}
		// MT2009_PLUS_BOT_CHAMPION_V1: the Hydra's end and the statue - the rows' states, this core's errands.
		{
			int hydra = 0, pending = 0, unlocked = 0, skipped = 0, ended = 0;
			for (std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator i = s_mapPlayerBotYoharaCohort.begin();
					i != s_mapPlayerBotYoharaCohort.end(); ++i)
			{
				if (i->second.iPurpose != YOHARA_PURPOSE_HYDRA)
					continue;
				++hydra;
				ended += IsPlayerBotYoharaHydraMemberEnded(i->second) ? 1 : 0;
				if (i->second.iChampion == YOHARA_CHAMPION_UNLOCKED)
					++unlocked;
				else if (i->second.iChampion == YOHARA_CHAMPION_SKIPPED)
					++skipped;
				else if (IsPlayerBotYoharaChampionPending(i->first, i->second))
					++pending;
			}
			if (hydra > 0 && (ended > 0 || !s_mapPlayerBotChampionErrand.empty()))
				sys_log(0, "PLAYERBOT_CHAMPION: census channel=%u switch=%d members=%d ended=%d pending=%d unlocked=%d skipped=%d "
						"errands_here=%u unlocked_here=%u refused_here=%u skipped_here=%u",
						(unsigned int)g_bChannel, IsPlayerBotHydraEndSwitched() ? 1 : 0, hydra, ended, pending, unlocked, skipped,
						(unsigned int)s_mapPlayerBotChampionErrand.size(), s_uPlayerBotChampionUnlocked,
						s_uPlayerBotChampionRefused, s_uPlayerBotChampionSkipped);
		}
		s_dwPlayerBotYoharaCohortLastCensus = dwNow;
	}

	// The Time Rift's runs (playerbot_dungeon_runs.h): a line at the start and at the end, the end
	// counted for the cohort's members in it.
	void NotePlayerBotYoharaSzcRun(bool start, int runId, long instance, const std::vector<DWORD>& members,
			const char* result, DWORD tookS)
	{
		int cohort = 0;
		std::string list;
		for (size_t i = 0; i < members.size(); ++i)
		{
			if (!IsPlayerBotYoharaCohortPID(members[i]))
				continue;
			++cohort;
			list += (list.empty() ? "" : ",") + std::to_string(members[i]);
		}
		if (start)
		{
			sys_log(0, "PLAYERBOT_YOHARA: szc run start run=%d instance=%ld members=%u cohort=%d", runId, instance,
					(unsigned int)members.size(), cohort);
			return;
		}
		sys_log(0, "PLAYERBOT_YOHARA: szc run end run=%d instance=%ld result=%s took_s=%u members=%u cohort=%d", runId,
				instance, result ? result : "-", tookS, (unsigned int)members.size(), cohort);
		if (cohort == 0 || !result || strcmp(result, "aborted") == 0 || tookS < 60)
			return;
		s_aPlayerBotYoharaCohortStats[YOHARA_PURPOSE_SZC].runs += (unsigned int)cohort;
		if (s_bPlayerBotYoharaCohortTableReady)
		{
			const std::string q = "UPDATE common.playerbot_yohara_cohort SET runs = runs + 1, last_seen = NOW() WHERE pid IN (" +
					list + ")";
			RunPlayerBotYoharaSql(q.c_str());
		}
	}

	// MT2009_PLUS_BOT_HYDRA_COHORT_V1: a Hydra run's end (playerbot_dungeon_runs.h, LogPlayerBotHydraRunEnd) counted
	// for the cohort's members in it - runs, and wins - and a member's death on the ship.
	void NotePlayerBotYoharaHydraRunEnd(const std::vector<DWORD>& members, bool won)
	{
		std::string list;
		int cohort = 0;
		for (size_t i = 0; i < members.size(); ++i)
		{
			// MT2009_PLUS_BOT_CHAMPION_V1: a Hydra member whose Hydra ended under it (an ordinary bot by now, with no
			// win yet) still has this run counted - its win sends it to the statue.
			std::map<DWORD, TPlayerBotYoharaCohortMember>::iterator m = s_mapPlayerBotYoharaCohort.find(members[i]);
			const bool hydraRow = m != s_mapPlayerBotYoharaCohort.end() && m->second.iPurpose == YOHARA_PURPOSE_HYDRA &&
					IsPlayerBotYoharaCohortOn();
			if (!hydraRow && !IsPlayerBotYoharaCohortPID(members[i]))
				continue;
			if (hydraRow && won)
				++m->second.iWins;
			++cohort;
			list += (list.empty() ? "" : ",") + std::to_string(members[i]);
		}
		if (cohort == 0)
			return;
		s_aPlayerBotYoharaCohortStats[YOHARA_PURPOSE_HYDRA].runs += (unsigned int)cohort;
		if (won)
			s_aPlayerBotYoharaCohortStats[YOHARA_PURPOSE_HYDRA].wins += (unsigned int)cohort;
		if (s_bPlayerBotYoharaCohortTableReady && s_bPlayerBotYoharaCohortHydraColumns)
		{
			const std::string q = std::string("UPDATE common.playerbot_yohara_cohort SET runs = runs + 1, wins = wins + ") +
					(won ? "1" : "0") + ", last_seen = NOW() WHERE pid IN (" + list + ")";
			RunPlayerBotYoharaSql(q.c_str());
		}
	}

	void NotePlayerBotYoharaHydraDeath(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotYoharaCohortPID(ch->GetPlayerID()))
			return;
		++s_aPlayerBotYoharaCohortStats[YOHARA_PURPOSE_HYDRA].deaths;
		NotePlayerBotYoharaCohortDb(ch->GetPlayerID(), "deaths", 1, ch->GetMapIndex());
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
				s_mapPlayerBotChampionErrand.erase(i->first);	// MT2009_PLUS_BOT_CHAMPION_V1
				s_mapPlayerBotSungma.erase(i->first);	// MT2009_PLUS_BOT_YOHARA_MAPS_V1 (its "not now" maps go with the stay)
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
		LoadPlayerBotYoharaCohort(dwNow, false);	// MT2009_PLUS_BOT_YOHARA_COHORT_V1
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
		int sungmaMaps[PLAYERBOT_SUNGMA_MAP_COUNT] = { 0 };	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: the rows a Sung Ma map
		for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
			if (r->second.iPurpose > 0 && r->second.iPurpose < YOHARA_PURPOSE_MAX)
				++residentsHere[r->second.iPurpose];
		std::set<DWORD> away;
		std::set<DWORD> seen;
		std::set<DWORD> live;	// MT2009_PLUS_BOT_YOHARA_COHORT_V1: on its way, or a stay refreshed
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: the cohorts' members on the channel's cores / on their way.
		int cohortStaying[YOHARA_PURPOSE_MAX] = { 0 }, cohortOnWay[YOHARA_PURPOSE_MAX] = { 0 };
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TRow& t = rows[i];
			seen.insert(t.pid);
			if (t.state == 1 || (t.state == 2 && t.fresh))
				live.insert(t.pid);
			if (t.purpose > 0 && t.purpose < YOHARA_PURPOSE_MAX && s_mapPlayerBotYoharaCohort.count(t.pid))
			{
				if (t.state == 2 && t.fresh)
					++cohortStaying[t.purpose];
				else if (t.state == 1)
					++cohortOnWay[t.purpose];
			}
			const bool hostedHere = t.map > 0 && IsPlayerBotMapHostedHere(t.map);
			if (t.state == 1 && t.purpose > 0 && t.purpose < YOHARA_PURPOSE_MAX && t.purpose != YOHARA_PURPOSE_HOME)
				++census[t.purpose];
			else if (t.state == 2 && t.fresh && t.purpose > 0 && t.purpose < YOHARA_PURPOSE_MAX)
				++census[t.purpose];
			if (t.purpose == YOHARA_PURPOSE_SUNGMA && (t.state == 1 || (t.state == 2 && t.fresh)) &&
					GetPlayerBotSungmaSlot(t.map) >= 0)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
				++sungmaMaps[GetPlayerBotSungmaSlot(t.map)];
			// A claim for this core.
			if (t.state == 1 && hostedHere && t.ready && !s_mapPlayerBotYoharaLeaving.count(t.pid) &&
					!s_mapPlayerBotYoharaArrival.count(t.pid))
			{
				if (CHARACTER_MANAGER::instance().FindByPID(t.pid) || P2P_MANAGER::instance().FindByPID(t.pid))
					continue;	// still logged in somewhere: the next poll
				// MT2009_PLUS_BOT_YOHARA_COHORT_V1: every purpose's limit (Wezowe Pole / Kraina too).
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
				// MT2009_PLUS_BOT_CHAMPION_V1: a member coming home - its row read again first (the statue's core may
				// have just ended its errand: it must not be sent back at once on a minute-old copy).
				if (t.purpose == YOHARA_PURPOSE_HOME && s_mapPlayerBotYoharaCohort.count(t.pid))
					LoadPlayerBotYoharaCohort(dwNow, true);
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
		for (int i = 0; i < PLAYERBOT_SUNGMA_MAP_COUNT; ++i)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
			s_aiPlayerBotSungmaMapCensus[i] = sungmaMaps[i];
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
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: the members this core is home to, sent.
		DispatchPlayerBotYoharaCohort(dwNow, seen, live, census);
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
					// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member's death, counted for its cohort.
					if (IsPlayerBotYoharaCohortPID(r->first) && r->second.iPurpose > 0 && r->second.iPurpose < YOHARA_PURPOSE_MAX)
					{
						++s_aPlayerBotYoharaCohortStats[r->second.iPurpose].deaths;
						NotePlayerBotYoharaCohortDb(r->first, "deaths", 1, rc->GetMapIndex());
					}
					if (r->second.iPurpose == YOHARA_PURPOSE_SUNGMA)	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
						NotePlayerBotSungmaDeath(rc);
					sys_log(0, "PLAYERBOT_YOHARA: died pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) purpose=%s deaths=%d windowed=%d max_hp=%d",
							r->first, rc->GetName(), (unsigned int)rc->GetLevel(), rc->GetMapIndex(), rc->GetX(), rc->GetY(),
							PlayerBotYoharaPurposeName(r->second.iPurpose), r->second.iDeaths, r->second.iDeathsWindowed,
							(int)rc->GetMaxHP());
				}
				r->second.bDead = dead;
				// MT2009_PLUS_BOT_YOHARA_COHORT_V1: its experience since the last poll.
				TrackPlayerBotYoharaCohortExp(rc, r->second);
				// MT2009_PLUS_BOT_YOHARA_MAPS_V1: and a Sung Ma map's census (experience, champion experience, level-ups, stuck).
				if (r->second.iPurpose == YOHARA_PURPOSE_SUNGMA)
					TrackPlayerBotSungma(rc);
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
			// MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole / Kraina Gigantow in it, and the cohorts' lines.
			sys_log(0, "PLAYERBOT_HANDOVER: census channel=%u on=%d zaklety=%d/%d szc=%d/%d loot=%d/%d snakefield=%d/%d "
					"giantland=%d/%d hydra=%d/%d yohara=%d/%d residents_here=%u (zaklety=%d szc=%d loot=%d snakefield=%d giantland=%d "
					"hydra=%d yohara=%d) away=%u requests=%u out=%u in=%u home=%u refused=%u cancel=%u",
					(unsigned int)g_bChannel, IsPlayerBotYoharaOn() ? 1 : 0,
					census[YOHARA_PURPOSE_ZAKLETY], cfg.zakletyMax, census[YOHARA_PURPOSE_SZC], cfg.szcMax,
					census[YOHARA_PURPOSE_LOOT], cfg.lootMax, census[YOHARA_PURPOSE_SNAKEFIELD], cfg.snakeMax,
					census[YOHARA_PURPOSE_GIANTLAND], cfg.giantMax, census[YOHARA_PURPOSE_HYDRA], cfg.hydraMax,
					census[YOHARA_PURPOSE_SUNGMA], cfg.sungmaMax,	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
					(unsigned int)s_mapPlayerBotYoharaResident.size(),
					residentsHere[YOHARA_PURPOSE_ZAKLETY], residentsHere[YOHARA_PURPOSE_SZC], residentsHere[YOHARA_PURPOSE_LOOT],
					residentsHere[YOHARA_PURPOSE_SNAKEFIELD], residentsHere[YOHARA_PURPOSE_GIANTLAND], residentsHere[YOHARA_PURPOSE_HYDRA],
					residentsHere[YOHARA_PURPOSE_SUNGMA],
					(unsigned int)s_setPlayerBotYoharaAway.size(), (unsigned int)s_mapPlayerBotYoharaOut.size(),
					s_uPlayerBotYoharaOutCount, s_uPlayerBotYoharaInCount, s_uPlayerBotYoharaHomeCount,
					s_uPlayerBotYoharaRefusedCount, s_uPlayerBotYoharaCancelCount);
			LogPlayerBotYoharaCohortCensus(dwNow, cohortStaying, cohortOnWay);
			LogPlayerBotSungmaCensus(dwNow);	// MT2009_PLUS_BOT_YOHARA_MAPS_V1
		}
	}
}

#endif
