#ifndef __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_H__
#define __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_YDG_H__

// MT2009_PLUS_BOT_YDG_V1 - the bots' runs of the Yohara dungeons of Plaskowyz Iluzji (the owner, 5 November 2026:
// "nauczmy boty korzystac z dungeonow Yohary"; that night: "boty maja sie nauczyc tych dungeonow do 7:00").
//
// Seven rows of PLAYERBOT_DGRUN_DEFS (kind DGRUN_KIND_YDG), all on the Yohara core with their gathering at the
// dungeon panel's entrance on Plaskowyz Iluzji (397):
//   * the Time Rifts (Statua Szczeliny Czasu, ticket Zegarek Kieszonkowy 31147 - ChargePlayerBotYoharaSzcWatch):
//     beran_szc (405), razador_szc (406), nemere_szc (407) - the full dungeons, as their PB twins (the quests are
//     generated from them, tools/yohara_crack2); Zaklety Las (SZC) stays the hunt of DGRUN_KIND_SZC;
//   * the Awakened Bosses (Statua Przebudzenia, ticket Ksiazka Przebudzenia 31146 - the bot's own book, else bought
//     on the market for PLAYERBOT_YDG_BOOK_PRICE): beran_pb (398), razador_pb (369), nemere_pb (370), jotun_pb (371).
// The quests carry a bots' half (MT2009_PLUS_BOT_YDG_V1 in them): <q>_dgrun runs init() for an instance with the
// dungeon flag mt2009_dgrun, <q>_dgrun_next does what the leader's talk does (Gardziel Am-heha's next lock and the
// boss hall; Lodowy Lew's start and the throne room; Duch Sura's temple once the core has taken each member's three
// Krete Klucze; Przywodca Strazy Lasu's Erebu once the forest's seven tasks are done - one party count, d flag bst),
// and the boss's kill sets the d flag won. Inside:
//   * the leader's objectives (GetPlayerBotYdgObjectives): the Ignator, the Metin of Purgatory, Razador; the Metin
//     of Frost, the Szels, the Pillar, Nemere; the Yonghans for the keys, the four Metins, Beran-Setaou; the forest's
//     warriors, druids, Metins, destroyers, the Lord, Bagjanamu and Jotun Thrym - else the nearest monster;
//   * the items (ManagePlayerBotYdgItems): the Golden Cog to the Stele, the Maat stones and the North Stars to the
//     steles / cubes - a wrong one remembered for that turn of the hidden order, as a player does; the Frost Key used
//     by a Shaman, the Ice Flower Key by a Ninja or a Shaman - a member of another class hands it over (a trade);
//   * the stage, the progress and the win from the quests' own flags.
// The Nemere ones want a Ninja and a Shaman in the party (as the statues' rule for people); every row a Shaman.
//
// Training parties (the owner's night of 5/6 November - "pick the bots best suited, several fixed parties, all
// night"): the file playerbot_ydg_train in the core's directory (read every 30 s when it changed; kept):
//     party <dungeons> <pid> <pid> ...    a fixed party (the first pid leads)
//     auto <parties> <size> [<dungeons>]  that many parties formed of this core's best bots of 110+ (level, champion
//                                         level, the gear's level), a Shaman and a Ninja in each where there are any
//     # ...                               a comment
// <dungeons>: any, pb, szc or keys joined by commas (beran_szc,razador_pb,...). Such a party runs its dungeons in
// turn, one run after another (a rest of PLAYERBOT_YDG_TRAIN_REST_*), off the clock's draw and the core's cap (its
// own: PLAYERBOT_YDG_TRAIN_MAX_RUNS), its members out of every other call and kept on the core by the Yohara
// residents' pass. The event flag m2_bot_ydg_train_off 1 stops new calls. The test file's "now <key>" calls one
// dungeon from the free bots as before.
//
// The log: BOT_YDG lines (train load/party/called/rest, run start with the class mix and the gear, handed in / used /
// traded / picked / keys pooled / next, run end with result, won, time, stage, deaths, wipes, the gold, experience,
// levels and items gained) and playerbot_ydg_runs.tsv: unix time, run, dungeon, training party, result, won,
// seconds, stage, stage seconds, deaths, wipes, members, lowest and highest level, gold, experience, levels, items,
// names. BOT_DGRUN lines as every run.
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h, in the anonymous namespace.

namespace
{
	enum EPlayerBotYdgBoss
	{
		YDG_RAZADOR = 1,
		YDG_NEMERE,
		YDG_BERAN,
		YDG_JOTUN,
		YDG_WEZE,	// MT2009_PLUS_BOT_YDG_WEZE_V1: Swiatynia Wezy (391) - playerbot_dungeon_runs_ydg_weze.h
		YDG_GLEBIE		// MT2009_PLUS_BOT_GLEBIE_V1: Alastor (playerbot_dungeon_runs_ydg_glebie.h)
	};

	struct TPlayerBotYdgDef
	{
		const char* szKey;
		int iBoss;
		bool bSzc;
	};

	const TPlayerBotYdgDef PLAYERBOT_YDG_DEFS[] = {
		{ "beran_szc", YDG_BERAN, true },
		{ "razador_szc", YDG_RAZADOR, true },
		{ "nemere_szc", YDG_NEMERE, true },
		{ "beran_pb", YDG_BERAN, false },
		{ "razador_pb", YDG_RAZADOR, false },
		{ "nemere_pb", YDG_NEMERE, false },
		{ "jotun_pb", YDG_JOTUN, false },
		{ "swiatynia", YDG_WEZE, false },	// MT2009_PLUS_BOT_YDG_WEZE_V1
		{ "glebie_slaby", YDG_GLEBIE, false },	// MT2009_PLUS_BOT_GLEBIE_V1
		{ "glebie_silny", YDG_GLEBIE, false },
	};
	const size_t PLAYERBOT_YDG_DEF_COUNT = sizeof(PLAYERBOT_YDG_DEFS) / sizeof(PLAYERBOT_YDG_DEFS[0]);

	const DWORD PLAYERBOT_YDG_BOOK = 31146;		// Ksiazka Przebudzenia
	const long long PLAYERBOT_YDG_BOOK_PRICE = 2000000LL;
	const int PLAYERBOT_YDG_KEYS_EACH = 3;		// Duch Sura: three Krete Klucze a member
	const DWORD PLAYERBOT_YDG_ITEM_SCAN_MS = 1000;
	const DWORD PLAYERBOT_YDG_ITEM_RETRY_MS = 3000;
	const int PLAYERBOT_YDG_ITEM_RANGE = 2500;
	const int PLAYERBOT_YDG_GIVE_DISTANCE = 700;
	const int PLAYERBOT_YDG_PICKUP_DISTANCE = 200;
	const DWORD PLAYERBOT_YDG_NEXT_MS = 6000;
	const DWORD PLAYERBOT_YDG_TRAIN_PLAN_MS = 10000;
	const DWORD PLAYERBOT_YDG_TRAIN_FILE_MS = 30000;
	const DWORD PLAYERBOT_YDG_TRAIN_REST_MIN_MS = 60 * 1000;
	const DWORD PLAYERBOT_YDG_TRAIN_REST_SPREAD_MS = 60 * 1000;
	const DWORD PLAYERBOT_YDG_STATUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_YDG_TRAIN_WAIT_MS = 3 * 60 * 1000;
	const int PLAYERBOT_YDG_MIN_LEVEL = 110;
	const char* const PLAYERBOT_YDG_TRAIN_FILE = "playerbot_ydg_train";
	const char* const PLAYERBOT_YDG_RUNS_FILE = "playerbot_ydg_runs.tsv";

	const TPlayerBotYdgDef* FindPlayerBotYdgDef(const char* key)
	{
		if (!key)
			return NULL;
		for (size_t i = 0; i < PLAYERBOT_YDG_DEF_COUNT; ++i)
			if (!strcmp(PLAYERBOT_YDG_DEFS[i].szKey, key))
				return &PLAYERBOT_YDG_DEFS[i];
		return NULL;
	}

	// The SZC twin's vnum of a PB one (tools/yohara_crack2/ycrack2_data.py, PB_TO_SZC).
	DWORD PlayerBotYdgVnum(const TPlayerBotYdgDef& y, DWORD pb)
	{
		if (!y.bSzc)
			return pb;
		if (pb >= 4280 && pb <= 4329)
			return pb - 80;
		if (pb >= 4410 && pb <= 4412)
			return pb - 10;
		if (pb >= 8130 && pb <= 8135)
			return pb - 10;
		if (pb >= 20530 && pb <= 20538)
			return pb - 20;
		if (pb == 31180 || (pb >= 31187 && pb <= 31191))
			return pb - 20;
		if (pb == PLAYERBOT_YDG_BOOK)
			return 31147;
		return pb;
	}

	int GetPlayerBotYdgEnv(const char* name, int def, int lo, int hi)
	{
		return ReadPlayerBotYoharaEnvInt(name, def, lo, hi);
	}

	// MT2009_PLUS_BOT_YDG_WEZE_V1: Swiatynia Wezy's own (playerbot_dungeon_runs_ydg_weze.h, included after this file).
	int GetPlayerBotWezeStage(LPDUNGEON d);
	long long GetPlayerBotWezeSignature(LPDUNGEON d);
	void GetPlayerBotWezeObjectives(LPDUNGEON d, std::vector<DWORD>& out);
	bool IsPlayerBotWezeItem(DWORD vnum);
	bool ManagePlayerBotWezeItems(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow);
	void UpdatePlayerBotWezeInside(TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow);
	bool IsPlayerBotWezeNextWanted(LPDUNGEON d);
	long long ChargePlayerBotWezeEntry(LPCHARACTER ch);
	void FinishPlayerBotWezeMember(LPCHARACTER ch, int runId);
	void ForgetPlayerBotWeze(long instance);
	int GetPlayerBotYdgDefMinLevel(int def);
	// MT2009_PLUS_BOT_GLEBIE_V1: playerbot_dungeon_runs_ydg_glebie.h (included after this file).
	int GetPlayerBotGlebieStage(LPDUNGEON d);
	long long GetPlayerBotGlebieSignature(LPDUNGEON d);
	void GetPlayerBotGlebieObjectives(const TPlayerBotDgRunDef& def, LPDUNGEON d, const TPlayerBotArzDgScan& scan,
			std::vector<DWORD>& out);
	bool GetPlayerBotGlebieCamp(LPDUNGEON d, long& x, long& y);
	bool ManagePlayerBotGlebieBot(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow);
	bool ShouldPlayerBotGlebieWake(const TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow);
	long long ChargePlayerBotGlebieKeys(LPCHARACTER ch, const TPlayerBotDgRunDef& def);
	bool IsPlayerBotGlebiePartyOk(int def, const std::vector<playerbot_dgrun::TCand>& free, std::string& why);
	bool IsPlayerBotGlebieAutoOk(LPCHARACTER ch, const std::vector<int>& defs);
	bool IsPlayerBotYdgGateAutoPartyOk(const std::vector<int>& defs, const std::vector<DWORD>& pids, std::string& why);	// MT2009_PLUS_BOT_YDG_GATE_V1
	void NotePlayerBotGlebieRunStart(const TPlayerBotDgRun& run);
	void NotePlayerBotGlebieRunEnd(const TPlayerBotDgRun& run);

	// ------------------------------------------------------------ the quests' flags

	int GetPlayerBotYdgStage(const TPlayerBotDgRunDef& def, LPDUNGEON d, int previous)
	{
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		if (!y || !d || d->GetFlag("init") != 1)
			return y && d ? 0 : previous;
		const int level = d->GetFlag("level");
		switch (y->iBoss)
		{
			case YDG_RAZADOR:	// 1-6 the locks, 7 Razador
				return level == 17 ? 7 : std::max(1, d->GetFlag("done"));
			case YDG_NEMERE:	// the floor, 1-10
				return std::max(1, level);
			case YDG_BERAN:		// 1 the keys, 2 the Metins, 3 Beran-Setaou
				return level == 2 ? (d->GetFlag("shield_off") == 1 ? 3 : 2) : 1;
			case YDG_JOTUN:		// 1-8 the forest's tasks, 9 Erebu
				return level == 2 ? 9 : std::max(1, d->GetFlag("bst"));
			case YDG_WEZE:		// MT2009_PLUS_BOT_YDG_WEZE_V1: 1 the Portal, 2-7 the temple's levels, 8 Nethis
				return GetPlayerBotWezeStage(d);
			case YDG_GLEBIE:	// MT2009_PLUS_BOT_GLEBIE_V1: 1 before Alastor wakes, 2 Alastor, 3 won
				return GetPlayerBotGlebieStage(d);
			default:
				return previous;
		}
	}

	bool IsPlayerBotYdgWon(LPDUNGEON d)
	{
		return d && d->GetFlag("won") == 1;
	}

	long long GetPlayerBotYdgSignature(LPDUNGEON d)
	{
		if (!d)
			return 0;
		static const char* const flags[] = { "level", "done", "maat_next", "cube_next", "jumping", "pillar", "metin6",
				"key2_used", "key8_used", "wave4", "bst", "bcnt", "sk1", "sk2", "sk3", "sk4", "shield_off", "bot_keys", "won",
				"task1", "task2", "task3", "task4", "task5", "task6" };
		long long sig = 0;
		for (size_t i = 0; i < sizeof(flags) / sizeof(flags[0]); ++i)
			sig = sig * 31LL + d->GetFlag(flags[i]);
		sig = sig * 31LL + GetPlayerBotWezeSignature(d);	// MT2009_PLUS_BOT_YDG_WEZE_V1 (0 off its map)
		sig = sig * 31LL + GetPlayerBotGlebieSignature(d);	// MT2009_PLUS_BOT_GLEBIE_V1
		return sig;
	}

	// The Krete Klucze of the run's members inside: three each is the temple (the update's pooling).
	std::map<long, bool> s_mapPlayerBotYdgKeysReady;

	void GetPlayerBotYdgObjectives(const TPlayerBotDgRunDef& def, LPDUNGEON d, const TPlayerBotArzDgScan& scan,
			std::vector<DWORD>& out)
	{
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		if (!y || !d)
			return;
		const int level = d->GetFlag("level");
		switch (y->iBoss)
		{
			case YDG_RAZADOR:
				if (level == 14)
					out.push_back(PlayerBotYdgVnum(*y, 4309));
				else if (level == 16)
					out.push_back(PlayerBotYdgVnum(*y, 8134));
				else if (level == 17)
					out.push_back(PlayerBotYdgVnum(*y, 4411));
				break;
			case YDG_NEMERE:
				if (d->GetFlag("jumping") == 1)
					break;
				if (level == 6)
					out.push_back(PlayerBotYdgVnum(*y, 8135));
				else if (level == 7)
					out.push_back(PlayerBotYdgVnum(*y, 4329));
				else if (level == 9 && d->GetFlag("pillar") == 0)
					out.push_back(PlayerBotYdgVnum(*y, 20538));
				else if (level == 10)
					out.push_back(PlayerBotYdgVnum(*y, 4412));
				break;
			case YDG_BERAN:
				if (level == 0)
				{
					std::map<long, bool>::const_iterator k = s_mapPlayerBotYdgKeysReady.find(d->GetMapIndex());
					// V2: in the SZC cave only General Yonghan (SZC) 4210 leaves a key (beran_szc.quest), and Captain
					// 4208's fall brings one where it fell - the others (4207 -> 4209, no key) only cost the party;
					// the PB one's every Yonghan does. (The night's party found the loop at 4208's spot: a key a minute.)
					if ((k == s_mapPlayerBotYdgKeysReady.end() || !k->second) && y->bSzc)
					{
						out.push_back(PlayerBotYdgVnum(*y, 4290));
						out.push_back(PlayerBotYdgVnum(*y, 4288));
					}
					else if (k == s_mapPlayerBotYdgKeysReady.end() || !k->second)
						for (DWORD v = 4287; v <= 4290; ++v)
							out.push_back(PlayerBotYdgVnum(*y, v));
				}
				else if (level == 2)
				{
					bool stones = false;
					for (size_t i = 0; i < scan.foes.size() && !stones; ++i)
						stones = scan.foes[i].dwRace >= PlayerBotYdgVnum(*y, 8130) && scan.foes[i].dwRace <= PlayerBotYdgVnum(*y, 8133);
					if (stones)
						for (DWORD v = 8130; v <= 8133; ++v)
							out.push_back(PlayerBotYdgVnum(*y, v));
					else
						out.push_back(PlayerBotYdgVnum(*y, 4410));
				}
				break;
			case YDG_JOTUN:
				if (level == 2)
				{
					out.push_back(4352);
					out.push_back(4413);
					break;
				}
				switch (d->GetFlag("bst"))
				{
					case 1: out.push_back(4340); break;
					case 2: out.push_back(4342); break;
					case 4: out.push_back(8136); break;
					case 5: out.push_back(4344); break;
					case 6:
					case 7: out.push_back(4345); break;
					default: break;
				}
				break;
			case YDG_WEZE:	// MT2009_PLUS_BOT_YDG_WEZE_V1
				GetPlayerBotWezeObjectives(d, out);
				break;
			case YDG_GLEBIE:	// MT2009_PLUS_BOT_GLEBIE_V1
				GetPlayerBotGlebieObjectives(def, d, scan, out);
				break;
			default:
				break;
		}
	}

	// V3: the SZC cave's two key spots (regen.txt 'm' lines, cells): Captain 4208 at (1092, 152) - its fall brings the
	// key's General 4210 there - and a General 4210 of its own at (709, 237); both back 70 s after their fall. They are
	// ~2 500 cells of walk apart (the navigation's plan) and the parties went from one to the other and back, a key in
	// 20 minutes. The first one the leader reaches is the run's spot: it waits there (GetPlayerBotYdgCamp) and the
	// Yonghans far from it are no objective (IsPlayerBotYdgGoalAway).
	const long PLAYERBOT_YDG_SZC_SPOTS[2][2] = { { 1092, 152 }, { 709, 237 } };
	const int PLAYERBOT_YDG_SZC_SPOT_REACHED = 3000;
	const int PLAYERBOT_YDG_SZC_SPOT_RANGE = 8000;
	std::map<long, int> s_mapPlayerBotYdgSzcSpot;	// instance -> spot + 1

	bool GetPlayerBotYdgSzcSpotXY(long instance, int spot, long& x, long& y)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		if (!pMap || spot < 0 || spot > 1)
			return false;
		x = pMap->m_setting.iBaseX + PLAYERBOT_YDG_SZC_SPOTS[spot][0] * 100;
		y = pMap->m_setting.iBaseY + PLAYERBOT_YDG_SZC_SPOTS[spot][1] * 100;
		return true;
	}

	bool IsPlayerBotYdgSzcKeysStage(const TPlayerBotDgRunDef& def, LPDUNGEON d)
	{
		const TPlayerBotYdgDef* yd = FindPlayerBotYdgDef(def.szKey);
		if (!yd || !d || !yd->bSzc || yd->iBoss != YDG_BERAN || d->GetFlag("level") != 0)
			return false;
		std::map<long, bool>::const_iterator k = s_mapPlayerBotYdgKeysReady.find(d->GetMapIndex());
		return k == s_mapPlayerBotYdgKeysReady.end() || !k->second;
	}

	void UpdatePlayerBotYdgSzcSpot(const TPlayerBotDgRunDef& def, LPDUNGEON d, LPCHARACTER leader)
	{
		if (!leader || !IsPlayerBotYdgSzcKeysStage(def, d) || s_mapPlayerBotYdgSzcSpot.count(d->GetMapIndex()))
			return;
		for (int i = 0; i < 2; ++i)
		{
			long x = 0, y = 0;
			if (GetPlayerBotYdgSzcSpotXY(d->GetMapIndex(), i, x, y) &&
					DISTANCE_APPROX(leader->GetX() - x, leader->GetY() - y) <= PLAYERBOT_YDG_SZC_SPOT_REACHED)
			{
				s_mapPlayerBotYdgSzcSpot[d->GetMapIndex()] = i + 1;
				sys_log(0, "BOT_YDG: szc key spot instance=%ld spot=%d (%ld,%ld) leader=%s", d->GetMapIndex(), i,
						PLAYERBOT_YDG_SZC_SPOTS[i][0], PLAYERBOT_YDG_SZC_SPOTS[i][1], leader->GetName());
				return;
			}
		}
	}

	bool IsPlayerBotYdgGoalAway(long instance, LPCHARACTER c)
	{
		std::map<long, int>::const_iterator it = s_mapPlayerBotYdgSzcSpot.find(instance);
		if (!c || it == s_mapPlayerBotYdgSzcSpot.end())
			return false;
		long x = 0, y = 0;
		if (!GetPlayerBotYdgSzcSpotXY(instance, it->second - 1, x, y))
			return false;
		return DISTANCE_APPROX(c->GetX() - x, c->GetY() - y) > PLAYERBOT_YDG_SZC_SPOT_RANGE;
	}

	bool GetPlayerBotYdgCamp(const TPlayerBotDgRunDef& def, LPDUNGEON d, long& x, long& y)
	{
		const TPlayerBotYdgDef* gl = FindPlayerBotYdgDef(def.szKey);	// MT2009_PLUS_BOT_GLEBIE_V1: by the egg till Alastor wakes
		if (gl && gl->iBoss == YDG_GLEBIE)
			return GetPlayerBotGlebieCamp(d, x, y);
		if (!IsPlayerBotYdgSzcKeysStage(def, d))
			return false;
		std::map<long, int>::const_iterator it = s_mapPlayerBotYdgSzcSpot.find(d->GetMapIndex());
		if (it == s_mapPlayerBotYdgSzcSpot.end())
			return false;	// not reached yet: the route-nearest objective leads there
		return GetPlayerBotYdgSzcSpotXY(d->GetMapIndex(), it->second - 1, x, y);
	}

	// ------------------------------------------------------------ the items

	struct TPlayerBotYdgItem
	{
		DWORD dwPbVnum;
		int iBoss;
		int iLevel;		// the quest's level the item is for
		bool bUse;		// used (its quest's use handler) - else handed to dwPbNpc
		DWORD dwPbNpc;
		int iJobs;		// the classes that may hold it (a bit a job), 0: any
		const char* szOrder;	// the flag of a hidden order (a wrong NPC remembered for its turn), or NULL
	};
	const TPlayerBotYdgItem PLAYERBOT_YDG_ITEMS[] = {
		{ 31187, YDG_RAZADOR, 12, false, 20533, 0, NULL },		// Zlota Zebatka -> Stela Isfet
		{ 31188, YDG_RAZADOR, 15, false, 20533, 0, "maat_next" },	// Kamien Maat -> the seven Stele
		{ 31189, YDG_NEMERE, 2, true, 0, 1 << JOB_SHAMAN, NULL },	// Mrozny Klucz: a Shaman's
		{ 31190, YDG_NEMERE, 5, false, 20537, 0, "cube_next" },	// Gwiazda Polnocy -> the five Arktyczne Kostki
		{ 31191, YDG_NEMERE, 8, true, 0, (1 << JOB_ASSASSIN) | (1 << JOB_SHAMAN), NULL },	// Klucz Lod. Kwiatu
		{ 31180, YDG_BERAN, 0, false, 0, 0, NULL },			// Kręty Klucz: kept for Duch Sura
	};
	const size_t PLAYERBOT_YDG_ITEM_COUNT = sizeof(PLAYERBOT_YDG_ITEMS) / sizeof(PLAYERBOT_YDG_ITEMS[0]);

	std::map<DWORD, DWORD> s_mapPlayerBotYdgItemAt;
	// (instance, the order's turn) -> the NPCs that turned out wrong for it.
	std::map<std::pair<long, int>, std::set<DWORD> > s_mapPlayerBotYdgWrong;

	struct FPlayerBotYdgNpc
	{
		LPCHARACTER m_me;
		DWORD m_dwRace;
		const std::set<DWORD>* m_pSkip;
		LPCHARACTER m_found;
		int m_iBest;
		FPlayerBotYdgNpc(LPCHARACTER me, DWORD race, const std::set<DWORD>* skip) : m_me(me), m_dwRace(race), m_pSkip(skip),
				m_found(NULL), m_iBest(INT_MAX) {}
		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER c = (LPCHARACTER)ent;
			if (c->IsPC() || c->IsDead() || c->GetRaceNum() != m_dwRace || c->GetMapIndex() != m_me->GetMapIndex())
				return;
			if (m_pSkip && m_pSkip->count((DWORD)c->GetVID()))
				return;
			const int d = DISTANCE_APPROX(c->GetX() - m_me->GetX(), c->GetY() - m_me->GetY());
			if (d < m_iBest)
			{
				m_iBest = d;
				m_found = c;
			}
		}
	};

	struct FPlayerBotYdgGround
	{
		LPCHARACTER m_me;
		std::vector<DWORD> m_vnums;
		LPITEM m_found;
		int m_iBest;
		explicit FPlayerBotYdgGround(LPCHARACTER me) : m_me(me), m_found(NULL), m_iBest(PLAYERBOT_YDG_ITEM_RANGE + 1) {}
		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_ITEM))
				return;
			LPITEM item = (LPITEM)ent;
			if (!item->GetSectree() || item->GetMapIndex() != m_me->GetMapIndex() || !item->IsOwnership(m_me) ||
					std::find(m_vnums.begin(), m_vnums.end(), item->GetVnum()) == m_vnums.end())
				return;
			const int d = DISTANCE_APPROX(item->GetX() - m_me->GetX(), item->GetY() - m_me->GetY());
			if (d < m_iBest)
			{
				m_iBest = d;
				m_found = item;
			}
		}
	};

	bool IsPlayerBotYdgJobOk(LPCHARACTER ch, int jobs)
	{
		return jobs == 0 || (ch && (jobs & (1 << (ch->GetJob() % 4))) != 0);
	}

	// A member of the run inside the instance, alive, that may hold the item (the first one standing nearest).
	LPCHARACTER FindPlayerBotYdgHolder(const TPlayerBotDgRun& run, LPCHARACTER ch, int jobs)
	{
		LPCHARACTER best = NULL;
		int dBest = INT_MAX;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c == ch || c->IsDead() || c->GetMapIndex() != run.lInstance || !IsPlayerBotYdgJobOk(c, jobs))
				continue;
			const int d = DISTANCE_APPROX(c->GetX() - ch->GetX(), c->GetY() - ch->GetY());
			if (d < dBest)
			{
				dBest = d;
				best = c;
			}
		}
		return best;
	}

	// MT2009_PLUS_BOT_YDG_TRAIN_V2: a bag cell for a run's item (a key, a cog, a stone) - the night of 5 November the
	// Beran parties' bags were full ("PLAYERBOT_LOOT: bag full") and no Krety Klucz was ever picked up. The storage
	// pages take something first, else the cheapest junk is sold, else the cheapest spare weapon or armour piece.
	// A run's item (either twin's vnum), a ticket, a quest item: never sold for room (05:36-05:48, 5 November: the
	// first version sold Ebola's Krety Klucz (SZC) as junk each time it picked up the next one).
	bool IsPlayerBotYdgKeptItem(LPITEM item)
	{
		if (!item)
			return true;
		const DWORD v = item->GetVnum();
		if (item->GetType() == ITEM_QUEST || v == PLAYERBOT_YDG_BOOK || v == 31147)
			return true;
		if (IsPlayerBotWezeItem(v))	// MT2009_PLUS_BOT_YDG_WEZE_V1: its keys, shards, dust and entry
			return true;
		for (size_t i = 0; i < PLAYERBOT_YDG_ITEM_COUNT; ++i)
			for (size_t k = 0; k < PLAYERBOT_YDG_DEF_COUNT; ++k)
				if (v == PlayerBotYdgVnum(PLAYERBOT_YDG_DEFS[k], PLAYERBOT_YDG_ITEMS[i].dwPbVnum))
					return true;
		return false;
	}

	// A stack of this vnum in the bag with room for one more (no new cell needed).
	bool HasPlayerBotYdgStackRoom(LPCHARACTER ch, DWORD vnum)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && item->GetVnum() == vnum && item->IsStackable() &&
					item->GetCount() < item->GetMaxStack())
				return true;
		}
		return false;
	}

	bool MakePlayerBotYdgRoom(LPCHARACTER ch, const char* why)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		if (ch->GetEmptyInventory(1) >= 0)
			return true;
		// MT2009_PLUS_NAJEMNICY_V3: a player's mercenary's bag is its owner's - nothing moved or sold for room.
		if (IsPlayerBotNajemnikPID(ch->GetPlayerID()))
			return false;
		if (PlayerBotEkwMakeBagRoom(ch, 1, NULL) && ch->GetEmptyInventory(1) >= 0)
		{
			sys_log(0, "BOT_YDG: room made pid=%u name=%s how=storage why=%s", ch->GetPlayerID(), ch->GetName(), why);
			return true;
		}
		for (int pass = 0; pass < 2; ++pass)
		{
			LPITEM pick = NULL;
			long long pickValue = 0;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->GetWindow() != INVENTORY || item->IsEquipped() ||
						item->isLocked() || IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_SELL) || IsPlayerBotYdgKeptItem(item))
					continue;
				if (pass == 0 && !IsPlayerBotJunkItem(ch, item))
					continue;
				if (pass == 1 && item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR)
					continue;
				const long long value = pass == 0 ? GetPlayerBotJunkSalePrice(item) : (long long)item->GetShopBuyPrice() * item->GetCount();
				if (pick && value >= pickValue)
					continue;
				pick = item;
				pickValue = value;
			}
			if (!pick)
				continue;
			sys_log(0, "BOT_YDG: room made pid=%u name=%s how=%s vnum=%u count=%u gold=%lld why=%s", ch->GetPlayerID(), ch->GetName(),
					pass == 0 ? "junk_sold" : "spare_sold", pick->GetVnum(), (unsigned int)pick->GetCount(), std::max(0LL, pickValue), why);
			if (pickValue > 0)
				PlayerBotChangeGold(ch, pickValue);
			ITEM_MANAGER::instance().RemoveItem(pick, "PLAYERBOT_YDG_ROOM");
			if (ch->GetEmptyInventory(1) >= 0)
				return true;
		}
		return ch->GetEmptyInventory(1) >= 0;
	}

	bool ManagePlayerBotYdgItems(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		if (!y || !d || ch->IsDead() || state.bRecoveringAfterDeath || !ch->IsItemLoaded() || !ch->GetSectree())
			return false;
		if (y->iBoss == YDG_WEZE)	// MT2009_PLUS_BOT_YDG_WEZE_V1: the keys, the cages, the heads (their orders)
			return ManagePlayerBotWezeItems(ch, state, run, d, dwNow);
		if (y->iBoss == YDG_GLEBIE)	// MT2009_PLUS_BOT_GLEBIE_V1: the egg chamber's members, the halls' portals
			return ManagePlayerBotGlebieBot(ch, state, run, d, dwNow);
		DWORD& next = s_mapPlayerBotYdgItemAt[ch->GetPlayerID()];
		if (next != 0 && (int)(next - dwNow) > 0)
			return false;
		next = dwNow + PLAYERBOT_YDG_ITEM_SCAN_MS;
		const long map = ch->GetMapIndex();
		const int level = d->GetFlag("level");
		const bool jumping = d->GetFlag("jumping") == 1;
		FPlayerBotYdgGround ground(ch);
		for (size_t i = 0; i < PLAYERBOT_YDG_ITEM_COUNT; ++i)
		{
			const TPlayerBotYdgItem& it = PLAYERBOT_YDG_ITEMS[i];
			if (it.iBoss != y->iBoss)
				continue;
			const DWORD vnum = PlayerBotYdgVnum(*y, it.dwPbVnum);
			if (it.iLevel == level && !jumping && IsPlayerBotYdgJobOk(ch, it.iJobs))
				ground.m_vnums.push_back(vnum);
			const int cell = FindPlayerBotTowerItemCell(ch, vnum);
			if (cell < 0)
				continue;
			// Not this class's: to one whose it is (a trade between the members).
			if (!IsPlayerBotYdgJobOk(ch, it.iJobs))
			{
				LPCHARACTER to = FindPlayerBotYdgHolder(run, ch, it.iJobs);
				if (!to)
					continue;
				const int n = (int)ch->CountSpecifyItem(vnum);
				ch->RemoveSpecifyItem(vnum, (ITEM_COUNT)n);
				LPITEM given = to->AutoGiveItem(vnum, (ITEM_COUNT)n, -1, false);
				sys_log(0, "BOT_YDG: traded run=%d dungeon=%s vnum=%u count=%d from=%s to=%s job_to=%u ok=%d", run.iId, def.szKey,
						(unsigned int)vnum, n, ch->GetName(), to->GetName(), (unsigned int)to->GetJob(), given ? 1 : 0);
				return true;
			}
			if (it.iLevel != level || jumping)
				continue;
			if (it.bUse)
			{
				next = dwNow + PLAYERBOT_YDG_ITEM_RETRY_MS;
				if (ch->IsStateMove())
					ch->Stop();
				const int before = d->GetFlag("level") * 100 + d->GetFlag("jumping") * 10 + d->GetFlag("key2_used") + d->GetFlag("key8_used");
				const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)cell));
				const int after = d->GetFlag("level") * 100 + d->GetFlag("jumping") * 10 + d->GetFlag("key2_used") + d->GetFlag("key8_used");
				sys_log(0, "BOT_YDG: used run=%d dungeon=%s pid=%u name=%s job=%u vnum=%u level=%d ok=%d right=%d", run.iId, def.szKey,
						ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetJob(), (unsigned int)vnum, level, ok ? 1 : 0,
						after != before ? 1 : 0);
				return true;
			}
			if (!it.dwPbNpc)
				continue;
			const DWORD npcRace = PlayerBotYdgVnum(*y, it.dwPbNpc);
			const int turn = it.szOrder ? d->GetFlag(it.szOrder) : 0;
			const std::pair<long, int> key(map, level * 100 + turn);
			const std::set<DWORD>* skip = it.szOrder ? &s_mapPlayerBotYdgWrong[key] : NULL;
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(map);
			if (!pMap)
				return false;
			FPlayerBotYdgNpc finder(ch, npcRace, skip);
			pMap->for_each(finder);
			if (!finder.m_found)
			{
				// Every one tried wrong for this turn (a turn whose stele was struck by another): from the start.
				if (it.szOrder && skip && !skip->empty())
					s_mapPlayerBotYdgWrong.erase(key);
				continue;
			}
			LPCHARACTER npc = finder.m_found;
			if (finder.m_iBest > PLAYERBOT_YDG_GIVE_DISTANCE)
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
			const DWORD npcVid = (DWORD)npc->GetVID();
			const int levelBefore = level;
			const bool ok = ch->GiveItem(npc, TItemPos(INVENTORY, (WORD)cell));
			// npc may be gone now (a right one is purged by its quest)
			int right = -1;
			if (it.szOrder)
			{
				const bool moved = d->GetFlag("level") != levelBefore || d->GetFlag(it.szOrder) != turn || d->GetFlag("jumping") == 1;
				right = moved ? 1 : 0;
				if (!moved && ok)
					s_mapPlayerBotYdgWrong[key].insert(npcVid);
			}
			sys_log(0, "BOT_YDG: handed in run=%d dungeon=%s pid=%u name=%s vnum=%u npc=%u turn=%d ok=%d right=%d tried_wrong=%u",
					run.iId, def.szKey, ch->GetPlayerID(), ch->GetName(), (unsigned int)vnum, (unsigned int)npcRace, turn, ok ? 1 : 0,
					right, it.szOrder ? (unsigned int)s_mapPlayerBotYdgWrong[key].size() : 0U);
			return true;
		}
		// One lying about: the bot's class's, its quest's turn.
		if (ground.m_vnums.empty())
			return false;
		ch->GetSectree()->ForEachAround(ground);
		if (!ground.m_found)
			return false;
		// Not far away from what attacks it (V2: one close by is picked up all the same - a dungeon whose monsters
		// never stop coming, as Beran's cave, never let a key be picked up).
		if (ground.m_iBest > 800 && ch->GetVictim() && !ch->GetVictim()->IsDead() && ch->GetVictim()->GetVictim() == ch)
			return false;
		if (ch->GetEmptyInventory(1) < 0 && !HasPlayerBotYdgStackRoom(ch, ground.m_found->GetVnum()) &&
				!MakePlayerBotYdgRoom(ch, "ground"))
		{
			PlayerBotLogThrottled("ydg_no_room", dwNow, "BOT_YDG: no room run=%d dungeon=%s pid=%u name=%s vnum=%u", run.iId,
					def.szKey, ch->GetPlayerID(), ch->GetName(), (unsigned int)ground.m_found->GetVnum());
			return false;
		}
		LPITEM item = ground.m_found;
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
		sys_log(0, "BOT_YDG: picked up run=%d dungeon=%s pid=%u name=%s vnum=%u ok=%d", run.iId, def.szKey, ch->GetPlayerID(),
				ch->GetName(), (unsigned int)vnum, ok ? 1 : 0);
		return true;
	}

	// The run's items out of a member's bag at the end (the quests take them from a person at the next entry).
	void DropPlayerBotYdgItems(LPCHARACTER ch, const TPlayerBotYdgDef& y)
	{
		if (!ch || !ch->IsItemLoaded())
			return;
		if (y.iBoss == YDG_WEZE)	// MT2009_PLUS_BOT_YDG_WEZE_V1: the statue's reward, the temple's keys and shards out
		{
			FinishPlayerBotWezeMember(ch, 0);
			return;
		}
		for (size_t i = 0; i < PLAYERBOT_YDG_ITEM_COUNT; ++i)
		{
			if (PLAYERBOT_YDG_ITEMS[i].iBoss != y.iBoss)
				continue;
			const DWORD vnum = PlayerBotYdgVnum(y, PLAYERBOT_YDG_ITEMS[i].dwPbVnum);
			const int n = (int)ch->CountSpecifyItem(vnum);
			if (n > 0)
				ch->RemoveSpecifyItem(vnum, (ITEM_COUNT)n);
		}
	}

	// ------------------------------------------------------------ the leader's talks

	std::map<int, DWORD> s_mapPlayerBotYdgNextAt;

	// Duch Sura wants three keys of every member inside: the members pool theirs (a trade) when the party holds them.
	bool PoolPlayerBotYdgKeys(TPlayerBotDgRun& run, const TPlayerBotYdgDef& y, bool take)
	{
		const DWORD key = PlayerBotYdgVnum(y, 31180);
		std::vector<LPCHARACTER> in;
		int total = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c || c->GetMapIndex() != run.lInstance || !c->IsItemLoaded())
				continue;
			in.push_back(c);
			total += (int)c->CountSpecifyItem(key);
		}
		const int need = PLAYERBOT_YDG_KEYS_EACH * (int)in.size();
		if (in.empty() || total < need)
			return false;
		if (!take)
			return true;
		for (size_t i = 0; i < in.size(); ++i)
		{
			const int n = (int)in[i]->CountSpecifyItem(key);
			if (n > 0)
				in[i]->RemoveSpecifyItem(key, (ITEM_COUNT)n);
		}
		if (total > need)
			in[0]->AutoGiveItem(key, (ITEM_COUNT)(total - need), -1, false);
		sys_log(0, "BOT_YDG: keys pooled run=%d dungeon=%s members=%u keys=%d taken=%d", run.iId,
				PLAYERBOT_DGRUN_DEFS[run.iDef].szKey, (unsigned int)in.size(), total, need);
		return true;
	}

	// Every second of a run inside: what the leader's talk would do, when its time has come.
	void UpdatePlayerBotYdgInside(TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		if (!y || !d || run.dwFinishedAt || run.szResult || d->GetFlag("init") != 1 || d->GetFlag("closed") == 1)
			return;
		const int level = d->GetFlag("level");
		if (y->iBoss == YDG_BERAN && level == 0)
			s_mapPlayerBotYdgKeysReady[run.lInstance] = PoolPlayerBotYdgKeys(run, *y, false);
		if (y->iBoss == YDG_WEZE)	// MT2009_PLUS_BOT_YDG_WEZE_V1: the members registered, the dust, its progress line
			UpdatePlayerBotWezeInside(run, d, dwNow);
		// V2: a progress line every two minutes (the flags, the keys held, where the leader stands, its target).
		{
			static std::map<int, DWORD> s_mapProgressAt;
			DWORD& p = s_mapProgressAt[run.iId];
			if (p == 0 || (int)(dwNow - p) >= 0)
			{
				p = dwNow + 120000;
				int keys = 0, inside = 0, alive = 0;
				for (size_t i = 0; i < run.members.size(); ++i)
				{
					LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (!c || c->GetMapIndex() != run.lInstance)
						continue;
					++inside;
					alive += c->IsDead() ? 0 : 1;
					if (c->IsItemLoaded())
						keys += (int)c->CountSpecifyItem(PlayerBotYdgVnum(*y, 31180));
				}
				LPCHARACTER lead = run.dwLeader ? CHARACTER_MANAGER::instance().FindByPID(run.dwLeader) : NULL;
				LPCHARACTER tgt = lead && lead->GetVictim() ? lead->GetVictim() : NULL;
				LPCHARACTER foc = run.dwFocusVID ? CHARACTER_MANAGER::instance().Find(run.dwFocusVID) : NULL;
				// the stage's objectives alive on the map, the nearest to the leader; members near the leader
				const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
				std::vector<DWORD> goals;
				GetPlayerBotYdgObjectives(def, d, scan, goals);
				int goalsAlive = 0, goalNear = -1, near = 0;
				for (size_t i = 0; i < scan.foes.size(); ++i)
				{
					LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
					if (!c || c->IsDead() || std::find(goals.begin(), goals.end(), c->GetRaceNum()) == goals.end())
						continue;
					++goalsAlive;
					if (lead)
					{
						const int dd = DISTANCE_APPROX(c->GetX() - lead->GetX(), c->GetY() - lead->GetY());
						goalNear = goalNear < 0 || dd < goalNear ? dd : goalNear;
					}
				}
				for (size_t i = 0; lead && i < run.members.size(); ++i)
				{
					LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
					if (c && c != lead && !c->IsDead() && c->GetMapIndex() == lead->GetMapIndex() &&
							DISTANCE_APPROX(c->GetX() - lead->GetX(), c->GetY() - lead->GetY()) <= 1500)
						++near;
				}
				sys_log(0, "BOT_YDG: progress run=%d dungeon=%s stage=%d level=%d done=%d bst=%d bcnt=%d jumping=%d keys=%d inside=%d alive=%d "
						"leader=%s(%ld,%ld,hp%d%%) near=%d target=%u(%d%%) focus=%u(%u,%d%%,d%d) goals=%d nearest_goal=%d fallback=%d",
						run.iId, def.szKey, run.iStage, level, d->GetFlag("done"),
						d->GetFlag("bst"), d->GetFlag("bcnt"), d->GetFlag("jumping"), keys, inside, alive, lead ? lead->GetName() : "-",
						lead ? lead->GetX() : 0L, lead ? lead->GetY() : 0L,
						lead && lead->GetMaxHP() > 0 ? (int)((long long)lead->GetHP() * 100 / lead->GetMaxHP()) : 0, near,
						tgt ? (unsigned int)tgt->GetRaceNum() : 0U,
						tgt && tgt->GetMaxHP() > 0 ? (int)((long long)tgt->GetHP() * 100 / tgt->GetMaxHP()) : 0,
						run.dwFocusVID, foc ? (unsigned int)foc->GetRaceNum() : 0U,
						foc && foc->GetMaxHP() > 0 ? (int)((long long)foc->GetHP() * 100 / foc->GetMaxHP()) : -1,
						foc && lead ? DISTANCE_APPROX(foc->GetX() - lead->GetX(), foc->GetY() - lead->GetY()) : -1,
						goalsAlive, goalNear, run.bFallback ? 1 : 0);
				if (lead)
				{
					const TPlayerBotAIState* st = GetPlayerBotDgRunState(lead->GetPlayerID());
					std::map<DWORD, TPlayerBotDgRunBot>::const_iterator lb = s_mapPlayerBotDgRunBots.find(lead->GetPlayerID());
					sys_log(0, "BOT_YDG: progress2 run=%d action=%d nav=%d target_vid=%u hold_s=%u unreachable=%u moving=%d",
							run.iId, st ? (int)st->bCurrentAction : -1, st ? (int)st->bLastNavOutcome : -1,
							st ? (unsigned int)st->dwTargetVID : 0U,
							lb != s_mapPlayerBotDgRunBots.end() && lb->second.dwHoldSince ? (dwNow - lb->second.dwHoldSince) / 1000 : 0U,
							lb != s_mapPlayerBotDgRunBots.end() ? (unsigned int)lb->second.unreachable.size() : 0U,
							lead->IsStateMove() ? 1 : 0);
				}
			}
		}
		DWORD& at = s_mapPlayerBotYdgNextAt[run.iId];
		if (at != 0 && (int)(at - dwNow) > 0)
			return;
		at = dwNow + PLAYERBOT_YDG_NEXT_MS;
		bool ask = false;
		switch (y->iBoss)
		{
			case YDG_RAZADOR:
				ask = level == 0;
				break;
			case YDG_NEMERE:
				ask = d->GetFlag("jumping") == 0 && (level == 0 || (level == 9 && d->GetFlag("pillar") == 1));
				break;
			case YDG_BERAN:
				if (level == 0 && d->GetFlag("bot_keys") == 0 && PoolPlayerBotYdgKeys(run, *y, true))
					d->SetFlag("bot_keys", 1);
				ask = level == 0 && d->GetFlag("bot_keys") == 1;
				break;
			case YDG_JOTUN:
				ask = level == 0 && d->GetFlag("bst") == 8;
				break;
			case YDG_WEZE:	// MT2009_PLUS_BOT_YDG_WEZE_V1: the Portal's start, the Smith's way to the 7th level
				ask = IsPlayerBotWezeNextWanted(d);
				break;
			case YDG_GLEBIE:	// MT2009_PLUS_BOT_GLEBIE_V1: the leader touches the egg - Alastor wakes
				ask = ShouldPlayerBotGlebieWake(run, d, dwNow);
				break;
			default:
				break;
		}
		if (!ask || !def.szNextTimer)
			return;
		CallPlayerBotDgRunTimer(def.szNextTimer, run.lInstance);
		PlayerBotLogThrottled("ydg_next", dwNow, "BOT_YDG: next run=%d dungeon=%s level=%d done=%d bst=%d", run.iId, def.szKey,
				level, d->GetFlag("done"), d->GetFlag("bst"));
	}

	// ------------------------------------------------------------ the ticket

	long long ChargePlayerBotYdgTicket(LPCHARACTER ch, const TPlayerBotDgRunDef& def)
	{
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		if (!y || !ch)
			return 0;
		if (y->iBoss == YDG_WEZE)	// MT2009_PLUS_BOT_YDG_WEZE_V1: no ticket - the day's five (Wejscie do Swiatyni Wezy)
			return ChargePlayerBotWezeEntry(ch);
		if (y->iBoss == YDG_GLEBIE)	// MT2009_PLUS_BOT_GLEBIE_V1: three Zamarzniete Klucze
			return ChargePlayerBotGlebieKeys(ch, def);
		if (y->bSzc)
			return ChargePlayerBotYoharaSzcWatch(ch);
		if (ch->CountSpecifyItem(PLAYERBOT_YDG_BOOK) > 0)
		{
			ch->RemoveSpecifyItem(PLAYERBOT_YDG_BOOK, 1);
			sys_log(0, "BOT_YDG: ticket pid=%u name=%s dungeon=%s book=own", ch->GetPlayerID(), ch->GetName(), def.szKey);
			return 0;
		}
		// Bought from a player on the market (the book is the daily mission's reward of the statue's people).
		const long long price = (long long)GetPlayerBotYdgEnv("PLAYERBOT_YDG_BOOK_PRICE", (int)PLAYERBOT_YDG_BOOK_PRICE, 0, 2000000000);
		if (price > 0 && (long long)ch->GetGold() >= price)
		{
			PlayerBotChangeGold(ch, -price);
			sys_log(0, "BOT_YDG: ticket pid=%u name=%s dungeon=%s book=bought price=%lld gold=%lld", ch->GetPlayerID(),
					ch->GetName(), def.szKey, price, (long long)ch->GetGold());
			return price;
		}
		sys_log(0, "BOT_YDG: ticket pid=%u name=%s dungeon=%s book=let_go gold=%lld", ch->GetPlayerID(), ch->GetName(), def.szKey,
				(long long)ch->GetGold());
		return 0;
	}

	// ------------------------------------------------------------ the gear

	// The worn weapon's, armour's and helmet's level (the item's level limit) and their plus.
	int GetPlayerBotYdgGearLevel(LPCHARACTER ch, int* plus)
	{
		static const int wears[3] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD };
		int sum = 0, n = 0, p = 0;
		for (int i = 0; i < 3; ++i)
		{
			LPITEM item = ch ? ch->GetWear(wears[i]) : NULL;
			if (!item)
				continue;
			sum += item->GetLevelLimit();
			p += item->GetRefineLevel();
			++n;
		}
		if (plus)
			*plus = n ? p / n : 0;
		return n ? sum / n : 0;
	}

	// The clock's call: the weapon and the armour of PLAYERBOT_YDG_MIN_GEAR_LEVEL or more (the training parties are
	// the operator's choice).
	bool IsPlayerBotYdgGearOk(LPCHARACTER ch)
	{
		static int s_min = -1;
		if (s_min < 0)
			s_min = GetPlayerBotYdgEnv("PLAYERBOT_YDG_MIN_GEAR_LEVEL", 75, 0, 250);
		LPITEM w = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		LPITEM b = ch ? ch->GetWear(WEAR_BODY) : NULL;
		return w && b && w->GetLevelLimit() >= s_min && b->GetLevelLimit() >= s_min;
	}

	// ------------------------------------------------------------ the training parties

	struct TPlayerBotYdgTrainParty
	{
		int iId;
		std::vector<DWORD> pids;
		std::vector<int> defs;		// PLAYERBOT_DGRUN_DEFS indices, in turn
		size_t next;
		int iRun;
		DWORD dwRestUntil;
		unsigned int runs, wins;
		std::string last;
		DWORD dwWaitSince;	// V2: waiting for its members since (0: not)
		TPlayerBotYdgTrainParty() : iId(0), next(0), iRun(0), dwRestUntil(0), runs(0), wins(0), dwWaitSince(0) {}
	};

	std::vector<TPlayerBotYdgTrainParty> s_vecPlayerBotYdgTrain;
	std::set<DWORD> s_setPlayerBotYdgTrainees;
	std::map<int, int> s_mapPlayerBotYdgRunParty;	// run -> training party id
	time_t s_tPlayerBotYdgTrainMtime = 0;
	bool s_bPlayerBotYdgTrainFile = false;
	std::vector<std::string> s_vecPlayerBotYdgAutoLines;
	// V3: the file's "cap <total> <per_dungeon>" - the training runs at once in all and in one dungeon (0: the
	// defaults, PLAYERBOT_YDG_TRAIN_MAX_RUNS and the dungeon's clock cap + 2). The clock's own caps stay.
	int s_iPlayerBotYdgTrainCapTotal = 0, s_iPlayerBotYdgTrainCapPerDg = 0;

	// MT2009_PLUS_BOT_GNOLLE_V2: Jaskinie Gnolli's own lines of the file (the owner, 6 November: "mniej druzyn, i wyzsze
	// lvl na 2 i 3 poziom"). The defaults hold without the file and for every caller (the clock, the Dropki, the training):
	//     gnolle max <n>            parties in the caves at once, all callers together (default 3; 0 = none)
	//     gnolle bosses <0|1>       a new party only while a level-1 boss stands that no party on level 1 has (default 1)
	//     gnolle retreat <pct>      a member under this much health drinks and steps back (default 45)
	//     gnolle l2 k=v ...         the strength to go down to level 2 (members champion gear plus hp healer avg)
	//     gnolle l3 k=v ...         the same for level 3
	// The night of 5/6 November's only win (run 17: 5 members, Champion 5-10, gear 80+6..103+9 - avg 93, max health in the
	// run 18 144-24 377, two Shamans, 0 deaths) gave the defaults: level 2 - 4 members, each Champion 5, gear 80 (+6), 18 000
	// health, a healer, the party's gear 85 on average; level 3 - the same with 5 members and 90 on average.
	struct TPlayerBotGnolleGate
	{
		int members, champion, gear, plus, hp, avg;
		bool healer;
	};
	struct TPlayerBotGnolleCfg
	{
		int iMax;
		bool bBosses;
		int iRetreatHp;
		TPlayerBotGnolleGate gate[2];	// [0] level 2, [1] level 3
		TPlayerBotGnolleCfg() : iMax(3), bBosses(true), iRetreatHp(45)
		{
			const TPlayerBotGnolleGate l2 = { 4, 5, 80, 6, 18000, 85, true };
			const TPlayerBotGnolleGate l3 = { 5, 5, 80, 6, 18000, 90, true };
			gate[0] = l2;
			gate[1] = l3;
		}
	};
	TPlayerBotGnolleCfg s_kPlayerBotGnolleCfg;

	void LogPlayerBotGnolleCfg()
	{
		const TPlayerBotGnolleCfg& c = s_kPlayerBotGnolleCfg;
		sys_log(0, "BOT_GNOLLE: config max=%d bosses=%d retreat=%d l2=m%d/c%d/g%d+%d/hp%d/avg%d/healer%d "
				"l3=m%d/c%d/g%d+%d/hp%d/avg%d/healer%d", c.iMax, c.bBosses ? 1 : 0, c.iRetreatHp, c.gate[0].members,
				c.gate[0].champion, c.gate[0].gear, c.gate[0].plus, c.gate[0].hp, c.gate[0].avg, c.gate[0].healer ? 1 : 0,
				c.gate[1].members, c.gate[1].champion, c.gate[1].gear, c.gate[1].plus, c.gate[1].hp, c.gate[1].avg,
				c.gate[1].healer ? 1 : 0);
	}

	bool ParsePlayerBotGnolleTrainLine(const std::vector<std::string>& w)
	{
		TPlayerBotGnolleCfg& c = s_kPlayerBotGnolleCfg;
		if (w.size() < 3)
			return false;
		if (w[1] == "max")
			c.iMax = std::max(0, std::min(atoi(w[2].c_str()), 10));
		else if (w[1] == "bosses")
			c.bBosses = atoi(w[2].c_str()) != 0;
		else if (w[1] == "retreat")
			c.iRetreatHp = std::max(0, std::min(atoi(w[2].c_str()), 90));
		else if (w[1] == "l2" || w[1] == "l3")
		{
			TPlayerBotGnolleGate& g = c.gate[w[1] == "l2" ? 0 : 1];
			for (size_t i = 2; i < w.size(); ++i)
			{
				const size_t eq = w[i].find('=');
				if (eq == std::string::npos)
					continue;
				const std::string k = w[i].substr(0, eq);
				const int v = atoi(w[i].c_str() + eq + 1);
				if (k == "members")
					g.members = std::max(1, std::min(v, (int)playerbot_dgrun::PARTY_MAX));
				else if (k == "champion")
					g.champion = std::max(0, std::min(v, 100));
				else if (k == "gear")
					g.gear = std::max(0, std::min(v, 200));
				else if (k == "plus")
					g.plus = std::max(0, std::min(v, 15));
				else if (k == "hp")
					g.hp = std::max(0, std::min(v, 1000000));
				else if (k == "avg")
					g.avg = std::max(0, std::min(v, 200));
				else if (k == "healer")
					g.healer = v != 0;
			}
		}
		else
			return false;
		return true;
	}

	bool IsPlayerBotYdgTrainee(DWORD pid)
	{
		// MT2009_PLUS_BOT_DROPKI_V1: an active Dropki is held for its dungeon as a training member (playerbot_dropki.h)
		// MT2009_PLUS_BOT_WIEZA_V1: and a bot of the tower's training (playerbot_wieza_train)
		return (!s_setPlayerBotYdgTrainees.empty() && s_setPlayerBotYdgTrainees.count(pid) != 0) || IsPlayerBotDropkiActive(pid) ||
				IsPlayerBotWiezaTrainee(pid);
	}

	int GetPlayerBotYdgDgRunDef(const char* key)
	{
		for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
			if (PLAYERBOT_DGRUN_DEFS[i].bKind == DGRUN_KIND_YDG && !strcmp(PLAYERBOT_DGRUN_DEFS[i].szKey, key))
				return i;
		return -1;
	}

	// "any", "pb", "szc" or keys joined by commas.
	void ParsePlayerBotYdgDungeons(const std::string& spec, std::vector<int>& out)
	{
		out.clear();
		size_t s = 0;
		while (s <= spec.size())
		{
			size_t e = spec.find(',', s);
			if (e == std::string::npos)
				e = spec.size();
			const std::string k = spec.substr(s, e - s);
			for (size_t i = 0; i < PLAYERBOT_YDG_DEF_COUNT; ++i)
			{
				const TPlayerBotYdgDef& y = PLAYERBOT_YDG_DEFS[i];
				// MT2009_PLUS_BOT_YDG_WEZE_V1: "any" and "pb" stay the seven of Plaskowyz Iluzji - the temple by its key
				const bool plateau = y.iBoss <= YDG_JOTUN;
				if ((k == "any" && plateau) || (k == "pb" && !y.bSzc && plateau) || (k == "szc" && y.bSzc) || k == y.szKey)
				{
					const int def = GetPlayerBotYdgDgRunDef(y.szKey);
					if (def >= 0 && std::find(out.begin(), out.end(), def) == out.end())
						out.push_back(def);
				}
			}
			// MT2009_PLUS_BOT_GNOLLE_V1: Jaskinie Gnolli by its key only ("any" stays the seven of the plateau).
			if (k == "gnolle")
				for (int d = 0; d < PLAYERBOT_DGRUN_DEF_COUNT; ++d)
					if (PLAYERBOT_DGRUN_DEFS[d].bKind == DGRUN_KIND_GNOLLE && std::find(out.begin(), out.end(), d) == out.end())
						out.push_back(d);
			s = e + 1;
		}
	}

	struct TPlayerBotYdgPick
	{
		DWORD pid;
		long long score;
		int job;
		bool healer;
	};

	long long ScorePlayerBotYdg(LPCHARACTER ch)
	{
		int plus = 0;
		const int gear = GetPlayerBotYdgGearLevel(ch, &plus);
		// V2: health, attack and defence too (the night's second parties - 17 thousand health - died every 20 s).
		return (long long)ch->GetLevel() * 1000LL + (long long)ch->GetConquerorLevel() * 400LL + gear * 20LL + plus * 30LL +
				(long long)ch->GetMaxHP() / 5 + (long long)ch->GetPoint(POINT_ATT_GRADE) * 2 + (long long)ch->GetPoint(POINT_DEF_GRADE) * 2;
	}

	// The best bots of this core for "auto": parties of `size` in one kingdom each, a Shaman and a Ninja first.
	// V2: an "auto" line short of its parties (the core just started, the bots still logging in) is formed again.
	struct TPlayerBotYdgAutoPending
	{
		int missing, size;
		std::vector<int> defs;
	};
	std::vector<TPlayerBotYdgAutoPending> s_vecPlayerBotYdgAutoPending;
	DWORD s_dwPlayerBotYdgAutoRetryAt = 0;
	const DWORD PLAYERBOT_YDG_AUTO_RETRY_MS = 90 * 1000;

	int FormPlayerBotYdgAutoParties(int parties, int size, const std::vector<int>& defs, DWORD dwNow)
	{
		std::vector<TPlayerBotYdgPick> pool[4];
		// MT2009_PLUS_BOT_YDG_WEZE_V1: the lowest level of the line's dungeons (Swiatynia Wezy: 120)
		int minLevel = 0;
		for (size_t i = 0; i < defs.size(); ++i)
			minLevel = minLevel == 0 ? GetPlayerBotYdgDefMinLevel(defs[i]) : std::min(minLevel, GetPlayerBotYdgDefMinLevel(defs[i]));
		minLevel = std::max(minLevel, PLAYERBOT_YDG_MIN_LEVEL);
		bool gnolleOnly = false;	// MT2009_PLUS_BOT_GNOLLE_V1: a line with Jaskinie Gnolli among its dungeons
		for (size_t i = 0; i < defs.size(); ++i)
			gnolleOnly = gnolleOnly || PLAYERBOT_DGRUN_DEFS[defs[i]].bKind == DGRUN_KIND_GNOLLE;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			const DWORD pid = it->first;
			if (s_setPlayerBotYdgTrainees.count(pid) || IsPlayerBotYoharaHydraResident(pid) || IsPlayerBotErebuTrainee(pid) ||
					IsPlayerBotDropkiActive(pid) || IsPlayerBotWiezaTrainee(pid))	// MT2009_PLUS_BOT_DROPKI_V1, MT2009_PLUS_BOT_WIEZA_V1
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch || ch->GetLevel() < minLevel || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
				continue;
			if (!IsPlayerBotGlebieAutoOk(ch, defs))	// MT2009_PLUS_BOT_GLEBIE_V1: 120 and a Champion level for Glebie alone
				continue;
			// MT2009_PLUS_BOT_GNOLLE_V1: a party for Jaskinie Gnolli only of those Halabardnik lets in (120, a Champion).
			if (gnolleOnly && !IsPlayerBotGnolleFit(ch))
				continue;
			// MT2009_PLUS_BOT_GNOLLE_V2: and strong enough for level 2 (its Champion level and gear; the health is the run's)
			if (gnolleOnly && !IsPlayerBotGnolleStrong(ch, 0, false))
				continue;
			const char* refusal = GetPlayerBotDgRunRefusal(ch, it->second, dwNow);
			if (refusal && strcmp(refusal, "dungeon_run"))
				continue;
			TPlayerBotYdgPick p;
			p.pid = pid;
			p.score = ScorePlayerBotYdg(ch);
			p.job = ch->GetJob() % 4;
			p.healer = p.job == JOB_SHAMAN && ch->GetSkillGroup() != 0;
			pool[ch->GetEmpire()].push_back(p);
		}
		for (int e = 1; e <= 3; ++e)
			std::sort(pool[e].begin(), pool[e].end(), [](const TPlayerBotYdgPick& a, const TPlayerBotYdgPick& b)
					{ return a.score > b.score; });
		int made = 0;
		for (int round = 0; made < parties && round < parties * 3; ++round)
		{
			// The kingdom with the most left.
			int e = 0;
			for (int k = 1; k <= 3; ++k)
				if ((int)pool[k].size() >= size && (e == 0 || pool[k].size() > pool[e].size()))
					e = k;
			if (e == 0)
				break;
			std::vector<TPlayerBotYdgPick>& v = pool[e];
			std::vector<TPlayerBotYdgPick> party;
			for (int want = 0; want < 2; ++want)	// a healing Shaman, a Ninja
				for (size_t i = 0; i < v.size(); ++i)
					if ((want == 0 && v[i].healer) || (want == 1 && v[i].job == JOB_ASSASSIN))
					{
						party.push_back(v[i]);
						v.erase(v.begin() + i);
						break;
					}
			int perJob[4] = { 0, 0, 0, 0 };
			for (size_t i = 0; i < party.size(); ++i)
				++perJob[party[i].job];
			const int cap = std::max(2, (size + 2) / 3);
			for (size_t i = 0; i < v.size() && (int)party.size() < size;)
			{
				if (perJob[v[i].job] < cap)
				{
					++perJob[v[i].job];
					party.push_back(v[i]);
					v.erase(v.begin() + i);
				}
				else
					++i;
			}
			while ((int)party.size() < size && !v.empty())
			{
				party.push_back(v.front());
				v.erase(v.begin());
			}
			// MT2009_PLUS_BOT_YDG_GATE_V1: a party of Swiatynia Wezy / Glebie alone too weak for all of its line is not
			// formed - its bots stay free (the weaker ones grow elsewhere first); the pool goes on weaker still.
			{
				std::vector<DWORD> pids;
				for (size_t i = 0; i < party.size(); ++i)
					pids.push_back(party[i].pid);
				std::string gate;
				if (!IsPlayerBotYdgGateAutoPartyOk(defs, pids, gate))
				{
					PlayerBotLogThrottled("ydg_gate_auto", dwNow, "BOT_YDG: train auto party not formed empire=%d members=%u - too weak for its line: %s",
							e, (unsigned int)pids.size(), gate.c_str());
					continue;
				}
			}
			// The leader: the strongest that is no Shaman.
			std::stable_sort(party.begin(), party.end(), [](const TPlayerBotYdgPick& a, const TPlayerBotYdgPick& b)
					{ return (a.job != JOB_SHAMAN) > (b.job != JOB_SHAMAN) || ((a.job != JOB_SHAMAN) == (b.job != JOB_SHAMAN) && a.score > b.score); });
			TPlayerBotYdgTrainParty tp;
			tp.iId = (int)s_vecPlayerBotYdgTrain.size() + 1;
			tp.defs = defs;
			tp.next = (size_t)number(0, std::max(0, (int)defs.size() - 1));
			std::string names;
			for (size_t i = 0; i < party.size(); ++i)
			{
				tp.pids.push_back(party[i].pid);
				s_setPlayerBotYdgTrainees.insert(party[i].pid);
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(party[i].pid);
				char buf[64];
				snprintf(buf, sizeof(buf), "%s%s(%u/%d/j%d)", names.empty() ? "" : ",", c ? c->GetName() : "?", party[i].pid,
						c ? (int)c->GetLevel() : 0, party[i].job);
				names += buf;
			}
			s_vecPlayerBotYdgTrain.push_back(tp);
			++made;
			sys_log(0, "BOT_YDG: train party=%d auto empire=%d members=%u dungeons=%u names=%s", tp.iId, e,
					(unsigned int)tp.pids.size(), (unsigned int)tp.defs.size(), names.c_str());
		}
		if (made < parties)
			sys_log(0, "BOT_YDG: train auto made %d of %d parties of %d (not enough free bots of %d+ in one kingdom on this core)",
					made, parties, size, minLevel);
		return made;
	}

	void LoadPlayerBotYdgTrainFile(DWORD dwNow, bool force)
	{
		struct stat st;
		if (stat(PLAYERBOT_YDG_TRAIN_FILE, &st) != 0)
		{
			if (s_bPlayerBotYdgTrainFile)
			{
				sys_log(0, "BOT_YDG: train file gone - the training parties dissolved");
				s_vecPlayerBotYdgTrain.clear();
				s_setPlayerBotYdgTrainees.clear();
				s_vecPlayerBotYdgAutoPending.clear();
				s_kPlayerBotGnolleCfg = TPlayerBotGnolleCfg();	// MT2009_PLUS_BOT_GNOLLE_V2: the defaults again
			}
			s_bPlayerBotYdgTrainFile = false;
			return;
		}
		if (!force && s_bPlayerBotYdgTrainFile && st.st_mtime == s_tPlayerBotYdgTrainMtime)
			return;
		s_bPlayerBotYdgTrainFile = true;
		s_tPlayerBotYdgTrainMtime = st.st_mtime;
		FILE* fp = fopen(PLAYERBOT_YDG_TRAIN_FILE, "r");
		if (!fp)
			return;
		// The runs under way finish; their parties are new ones from here.
		s_vecPlayerBotYdgTrain.clear();
		s_setPlayerBotYdgTrainees.clear();
		s_vecPlayerBotYdgAutoPending.clear();
		s_iPlayerBotYdgTrainCapTotal = s_iPlayerBotYdgTrainCapPerDg = 0;
		s_kPlayerBotGnolleCfg = TPlayerBotGnolleCfg();	// MT2009_PLUS_BOT_GNOLLE_V2: the defaults unless the file says
		char line[1024];
		std::vector<std::string> autos;
		while (fgets(line, sizeof(line), fp))
		{
			std::vector<std::string> w;
			char* save = NULL;
			for (char* tok = strtok_r(line, " \t\r\n", &save); tok; tok = strtok_r(NULL, " \t\r\n", &save))
				w.push_back(tok);
			if (w.empty() || w[0][0] == '#')
				continue;
			if (w[0] == "party" && w.size() >= 3)
			{
				TPlayerBotYdgTrainParty tp;
				tp.iId = (int)s_vecPlayerBotYdgTrain.size() + 1;
				ParsePlayerBotYdgDungeons(w[1], tp.defs);
				for (size_t i = 2; i < w.size() && tp.pids.size() < (size_t)playerbot_dgrun::PARTY_MAX; ++i)
				{
					const DWORD pid = (DWORD)strtoul(w[i].c_str(), NULL, 10);
					if (pid && !s_setPlayerBotYdgTrainees.count(pid))
					{
						tp.pids.push_back(pid);
						s_setPlayerBotYdgTrainees.insert(pid);
					}
				}
				tp.next = (size_t)number(0, std::max(0, (int)tp.defs.size() - 1));
				if (tp.defs.empty() || tp.pids.empty())
				{
					sys_log(0, "BOT_YDG: train line refused (no dungeon or no pid): %s %s", w[0].c_str(), w[1].c_str());
					continue;
				}
				s_vecPlayerBotYdgTrain.push_back(tp);
				sys_log(0, "BOT_YDG: train party=%d fixed members=%u dungeons=%s", tp.iId, (unsigned int)tp.pids.size(), w[1].c_str());
			}
			else if (w[0] == "cap" && w.size() >= 3)
			{
				s_iPlayerBotYdgTrainCapTotal = std::max(0, std::min(atoi(w[1].c_str()), 40));
				s_iPlayerBotYdgTrainCapPerDg = std::max(0, std::min(atoi(w[2].c_str()), 20));
				sys_log(0, "BOT_YDG: train cap total=%d per_dungeon=%d", s_iPlayerBotYdgTrainCapTotal, s_iPlayerBotYdgTrainCapPerDg);
			}
			else if (w[0] == "auto" && w.size() >= 3)
				autos.push_back(w[1] + " " + w[2] + " " + (w.size() >= 4 ? w[3] : std::string("any")));
			else if (w[0] == "gnolle")	// MT2009_PLUS_BOT_GNOLLE_V2
			{
				if (!ParsePlayerBotGnolleTrainLine(w))
					sys_log(0, "BOT_YDG: train line unknown: gnolle %s", w.size() > 1 ? w[1].c_str() : "-");
			}
			else
				sys_log(0, "BOT_YDG: train line unknown: %s", w[0].c_str());
		}
		fclose(fp);
		LogPlayerBotGnolleCfg();	// MT2009_PLUS_BOT_GNOLLE_V2
		for (size_t i = 0; i < autos.size(); ++i)
		{
			int parties = 0, size = 0;
			char spec[256] = "any";
			if (sscanf(autos[i].c_str(), "%d %d %255s", &parties, &size, spec) < 2)
				continue;
			std::vector<int> defs;
			ParsePlayerBotYdgDungeons(spec, defs);
			const int want = std::max(0, std::min(parties, 40));
			const int sz = std::max(2, std::min(size, playerbot_dgrun::PARTY_MAX));
			const int made = FormPlayerBotYdgAutoParties(want, sz, defs, dwNow);
			if (made < want)
			{
				TPlayerBotYdgAutoPending pend;
				pend.missing = want - made;
				pend.size = sz;
				pend.defs = defs;
				s_vecPlayerBotYdgAutoPending.push_back(pend);
				s_dwPlayerBotYdgAutoRetryAt = dwNow + PLAYERBOT_YDG_AUTO_RETRY_MS;
			}
		}
		sys_log(0, "BOT_YDG: train file loaded parties=%u trainees=%u", (unsigned int)s_vecPlayerBotYdgTrain.size(),
				(unsigned int)s_setPlayerBotYdgTrainees.size());
	}

	bool IsPlayerBotYdgNemere(int def)
	{
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(PLAYERBOT_DGRUN_DEFS[def].szKey);
		return y && y->iBoss == YDG_NEMERE;
	}

	int CountPlayerBotYdgTrainRuns()
	{
		int n = 0;
		for (std::map<int, int>::const_iterator it = s_mapPlayerBotYdgRunParty.begin(); it != s_mapPlayerBotYdgRunParty.end(); ++it)
			if (s_mapPlayerBotDgRuns.count(it->first))
				++n;
		return n;
	}

	// V3: the training runs of one dungeon under way.
	int CountPlayerBotYdgTrainRunsOf(int def)
	{
		int n = 0;
		for (std::map<int, int>::const_iterator it = s_mapPlayerBotYdgRunParty.begin(); it != s_mapPlayerBotYdgRunParty.end(); ++it)
		{
			std::map<int, TPlayerBotDgRun>::const_iterator r = s_mapPlayerBotDgRuns.find(it->first);
			if (r != s_mapPlayerBotDgRuns.end() && r->second.iDef == def)
				++n;
		}
		return n;
	}

	void PlanPlayerBotYdgTraining(DWORD dwNow)
	{
		static DWORD s_dwNextFile = 0, s_dwNextPlan = 0, s_dwNextStatus = 0;
		if (s_dwNextFile == 0 || (int)(dwNow - s_dwNextFile) >= 0)
		{
			s_dwNextFile = dwNow + PLAYERBOT_YDG_TRAIN_FILE_MS;
			LoadPlayerBotYdgTrainFile(dwNow, false);
		}
		// The ended runs' parties free again.
		for (std::map<int, int>::iterator it = s_mapPlayerBotYdgRunParty.begin(); it != s_mapPlayerBotYdgRunParty.end();)
		{
			if (!s_mapPlayerBotDgRuns.count(it->first))
				s_mapPlayerBotYdgRunParty.erase(it++);
			else
				++it;
		}
		// V2: the auto lines' missing parties, again a while later (up to every PLAYERBOT_YDG_AUTO_RETRY_MS).
		if (!s_vecPlayerBotYdgAutoPending.empty() && (int)(dwNow - s_dwPlayerBotYdgAutoRetryAt) >= 0)
		{
			s_dwPlayerBotYdgAutoRetryAt = dwNow + PLAYERBOT_YDG_AUTO_RETRY_MS;
			for (size_t i = 0; i < s_vecPlayerBotYdgAutoPending.size();)
			{
				TPlayerBotYdgAutoPending& pend = s_vecPlayerBotYdgAutoPending[i];
				pend.missing -= FormPlayerBotYdgAutoParties(pend.missing, pend.size, pend.defs, dwNow);
				if (pend.missing <= 0)
					s_vecPlayerBotYdgAutoPending.erase(s_vecPlayerBotYdgAutoPending.begin() + i);
				else
					++i;
			}
		}
		if (s_vecPlayerBotYdgTrain.empty())
			return;
		if (s_dwNextStatus == 0 || (int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_YDG_STATUS_MS;
			for (size_t i = 0; i < s_vecPlayerBotYdgTrain.size(); ++i)
			{
				const TPlayerBotYdgTrainParty& tp = s_vecPlayerBotYdgTrain[i];
				int online = 0;
				for (size_t k = 0; k < tp.pids.size(); ++k)
					online += CHARACTER_MANAGER::instance().FindByPID(tp.pids[k]) ? 1 : 0;
				sys_log(0, "BOT_YDG: train status party=%d members=%u online=%d runs=%u wins=%u running=%d last=%s", tp.iId,
						(unsigned int)tp.pids.size(), online, tp.runs, tp.wins, tp.iRun && s_mapPlayerBotDgRuns.count(tp.iRun) ? 1 : 0,
						tp.last.empty() ? "-" : tp.last.c_str());
			}
		}
		if (s_dwNextPlan != 0 && (int)(dwNow - s_dwNextPlan) < 0)
			return;
		s_dwNextPlan = dwNow + PLAYERBOT_YDG_TRAIN_PLAN_MS;
		if (!IsPlayerBotDgRunOn(dwNow) || quest::CQuestManager::instance().GetEventFlag("m2_bot_ydg_train_off") != 0)
			return;
		const int maxRuns = s_iPlayerBotYdgTrainCapTotal > 0 ? s_iPlayerBotYdgTrainCapTotal :
				GetPlayerBotYdgEnv("PLAYERBOT_YDG_TRAIN_MAX_RUNS", 6, 0, 50);
		int running = CountPlayerBotYdgTrainRuns();
		for (size_t i = 0; i < s_vecPlayerBotYdgTrain.size() && running < maxRuns; ++i)
		{
			TPlayerBotYdgTrainParty& tp = s_vecPlayerBotYdgTrain[i];
			if ((tp.iRun && s_mapPlayerBotDgRuns.count(tp.iRun)) || (tp.dwRestUntil && (int)(tp.dwRestUntil - dwNow) > 0) ||
					tp.defs.empty())
				continue;
			tp.iRun = 0;
			// The members free on this core.
			std::vector<playerbot_dgrun::TCand> free;
			BYTE empire = 0;
			bool ninja = false, shaman = false;
			int away = 0;
			int ofEmpire[4] = { 0, 0, 0, 0 };	// MT2009_PLUS_BOT_GNOLLE_WHOLE_V1: the party's members online, by kingdom
			std::string why;
			for (size_t k = 0; k < tp.pids.size(); ++k)
			{
				const DWORD pid = tp.pids[k];
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
				TPlayerBotAIState* state = GetPlayerBotDgRunState(pid);
				if (!ch || !state || !ch->GetDesc() || !ch->GetDesc()->IsBot())
				{
					++away;
					continue;
				}
				if (ch->GetEmpire() >= 1 && ch->GetEmpire() <= 3)
					++ofEmpire[ch->GetEmpire()];
				if (s_mapPlayerBotDgRunBots.count(pid) || ch->IsDead())
				{
					why += std::string(why.empty() ? "" : ",") + ch->GetName() + (ch->IsDead() ? ":dead" : ":in_run");
					continue;
				}
				if (const char* refusal = GetPlayerBotDgRunRefusal(ch, *state, dwNow))
				{
					// V2: a fight, its health, an afk moment - broken off for the party (free at the next look).
					const bool broke = BreakOffPlayerBotDgRunTrainee(ch, *state, refusal, dwNow);
					why += std::string(why.empty() ? "" : ",") + ch->GetName() + ":" + refusal + (broke ? "(broken_off)" : "");
					continue;
				}
				if (empire == 0)
					empire = ch->GetEmpire();
				if (ch->GetEmpire() != empire)
					continue;	// a party is one kingdom's
				const bool healer = ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0;
				ninja = ninja || ch->GetJob() == JOB_ASSASSIN;
				shaman = shaman || ch->GetJob() == JOB_SHAMAN;
				free.push_back(playerbot_dgrun::TCand(pid, ch->GetLevel(), ch->GetJob(), 10 + (int)(tp.pids.size() - k), healer));
			}
			if (empire < 1 || empire > 3)
				continue;
			// V2: the whole party, not those free at the first look - up to PLAYERBOT_YDG_TRAIN_WAIT_MS for the others.
			if ((int)free.size() + away < (int)tp.pids.size())
			{
				if (tp.dwWaitSince == 0)
					tp.dwWaitSince = dwNow;
				if (dwNow - tp.dwWaitSince < PLAYERBOT_YDG_TRAIN_WAIT_MS)
				{
					PlayerBotLogThrottled("ydg_train_short", dwNow, "BOT_YDG: train party=%d waits for its members free=%u of %u away=%d not_free=%s",
							tp.iId, (unsigned int)free.size(), (unsigned int)tp.pids.size(), away, why.c_str());
					continue;
				}
			}
			// The next dungeon of its turn that this party can go to now.
			int def = -1;
			for (size_t t = 0; t < tp.defs.size() && def < 0; ++t)
			{
				const int cand = tp.defs[(tp.next + t) % tp.defs.size()];
				const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[cand];
				const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor(info.szKey);
				if (!IsPlayerBotMapHostedHere(info.lMap) || !SECTREE_MANAGER::instance().GetMap(info.lMap))
					continue;
				if (s_iPlayerBotYdgTrainCapPerDg > 0 ? CountPlayerBotYdgTrainRunsOf(cand) >= s_iPlayerBotYdgTrainCapPerDg :
						CountPlayerBotDgRuns(cand) >= GetPlayerBotDgRunDefCap(cand) + 2)
					continue;
				if ((int)free.size() < rule.startMin || (IsPlayerBotYdgNemere(cand) && !(ninja && shaman)))
					continue;
				// MT2009_PLUS_BOT_GNOLLE_WHOLE_V1 (night 6/7 November): a Gnolle training party goes whole (up to 5) - parties
				// called with 3 of 5 (two "afk(broken_off)" after the last run) reached the level-2 gate with 3 fit of the 4 it
				// asks and turned back (7 of 8 runs "aborted" 19:00-22:00). Off: event flag m2_bot_gnolle_whole_off. Whole = the
				// members of the called kingdom (a party of mixed kingdoms waited for ever for the other kingdom's three).
				if (PLAYERBOT_DGRUN_DEFS[cand].bKind == DGRUN_KIND_GNOLLE &&
						quest::CQuestManager::instance().GetEventFlag("m2_bot_gnolle_whole_off") == 0 &&
						(int)free.size() < std::min<int>(5, ofEmpire[empire]))
				{
					PlayerBotLogThrottled("gnolle_whole", dwNow, "BOT_GNOLLE: train party=%d waits to go whole free=%u of %u",
							tp.iId, (unsigned int)free.size(), (unsigned int)tp.pids.size());
					continue;
				}
				// MT2009_PLUS_BOT_YDG_WEZE_V1: a dungeon of a higher level (the temple's 120) - enough members of it
				{
					int ofLevel = 0;
					for (size_t f = 0; f < free.size(); ++f)
						ofLevel += free[f].level >= GetPlayerBotYdgDefMinLevel(cand) ? 1 : 0;
					if (ofLevel < rule.startMin)
						continue;
				}
				if (!IsPlayerBotGlebiePartyOk(cand, free, why))	// MT2009_PLUS_BOT_GLEBIE_V1: 120, a Champion level, strong: 3 weak
					continue;
				// MT2009_PLUS_BOT_GNOLLE_V2: the caves' own queue (parties at once, a level-1 boss for it) - the next dungeon
				if (PLAYERBOT_DGRUN_DEFS[cand].bKind == DGRUN_KIND_GNOLLE && !IsPlayerBotGnolleOpenOk(dwNow, "ydg_train"))
					continue;
				def = cand;
				tp.next = (tp.next + t + 1) % tp.defs.size();
			}
			if (def < 0)
			{
				PlayerBotLogThrottled("ydg_train_wait", dwNow, "BOT_YDG: train party=%d waits - free=%u away=%d ninja=%d shaman=%d",
						tp.iId, (unsigned int)free.size(), away, ninja ? 1 : 0, shaman ? 1 : 0);
				continue;
			}
			const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
			// MT2009_PLUS_BOT_YDG_WEZE_V1: the members under the dungeon's level stay out (the statue's rule)
			const int defMinLevel = GetPlayerBotYdgDefMinLevel(def);
			for (size_t f = 0; f < free.size();)
			{
				if (free[f].level < defMinLevel)
				{
					why += std::string(why.empty() ? "" : ",") + "pid" + std::to_string(free[f].pid) + ":level";
					free.erase(free.begin() + f);
				}
				else
					++f;
			}
			TPlayerBotDgRunSlot slot;
			slot.lvMin = defMinLevel;
			slot.lvMax = gPlayerMaxLevel;
			slot.partyMin = 2;
			slot.partyMax = playerbot_dgrun::PARTY_MAX;
			slot.panel = mt2009_dpanel::FindKey(info.szKey);
			if (!ResolvePlayerBotLfgPlace(info.szKey, 0, empire, PLAYERBOT_YDG_MIN_LEVEL, slot.place[empire]))
			{
				PlayerBotLogThrottled("ydg_train_place", dwNow, "BOT_YDG: train party=%d dungeon=%s - no entrance here (panel row, plateau)",
						tp.iId, info.szKey);
				continue;
			}
			slot.ok = slot.empireOk[empire] = true;
			const int id = OpenPlayerBotDgRun(def, empire, free, slot, free.size(), dwNow, "ydg_train");
			if (id == 0)
				continue;
			tp.iRun = id;
			tp.dwWaitSince = 0;
			s_mapPlayerBotYdgRunParty[id] = tp.iId;
			++running;
			sys_log(0, "BOT_YDG: train party=%d called run=%d dungeon=%s members=%u of %u away=%d running=%d/%d not_free=%s", tp.iId, id,
					info.szKey, (unsigned int)free.size(), (unsigned int)tp.pids.size(), away, running, maxRuns,
					why.empty() ? "-" : why.c_str());
		}
	}

	// ------------------------------------------------------------ the run's start and end

	struct TPlayerBotYdgSnap
	{
		long long gold;
		long long exp;
		int level, conqueror, items;
	};
	std::map<int, std::map<DWORD, TPlayerBotYdgSnap> > s_mapPlayerBotYdgSnaps;

	int CountPlayerBotYdgBagItems(LPCHARACTER ch)
	{
		int n = 0;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && (int)item->GetCell() == cell)
				n += (int)item->GetCount();
		}
		return n;
	}

	TPlayerBotYdgSnap SnapPlayerBotYdg(LPCHARACTER ch)
	{
		TPlayerBotYdgSnap s;
		s.gold = (long long)ch->GetGold();
		s.exp = (long long)ch->GetExp();
		s.level = ch->GetLevel();
		s.conqueror = ch->GetConquerorLevel();
		s.items = CountPlayerBotYdgBagItems(ch);
		return s;
	}

	int GetPlayerBotYdgTrainParty(int runId)
	{
		std::map<int, int>::const_iterator it = s_mapPlayerBotYdgRunParty.find(runId);
		return it != s_mapPlayerBotYdgRunParty.end() ? it->second : 0;
	}

	// MT2009_PLUS_BOT_YDG_TRAIN_V2: the bots stronger, not the dungeons weaker (the owner, 5 November: better gear,
	// bonuses, potions for these bots). The Yonghans of Beran's cave (600-800 thousand health, REVIVE) win back 2-4.5%
	// of it every second - the night's parties held a Captain at 100% for minutes. A poisoned or bleeding monster does
	// not regenerate (recovery_event), so each member gets for the run what a player's 6/7 bonuses and weapon give:
	// poison and bleeding chances and strength against monsters (affects of their own, for the run's hour).
	const DWORD AFFECT_PLAYERBOT_YDG_POISON = 861;
	const DWORD AFFECT_PLAYERBOT_YDG_BLEED = 862;
	const DWORD AFFECT_PLAYERBOT_YDG_MONSTER = 863;
	const DWORD AFFECT_PLAYERBOT_YDG_HP = 864;
	const DWORD AFFECT_PLAYERBOT_YDG_CRIT = 865;
	const DWORD AFFECT_PLAYERBOT_YDG_PIERCE = 866;
	const DWORD AFFECT_PLAYERBOT_YDG_MOVE = 867;
	const DWORD AFFECT_PLAYERBOT_YDG_ATTSPD = 868;
	// The night of 5/6 November: Glebie's parties (395: 60/50/60/65) came in with Sung Ma of 22-58 - every member's blows
	// and health halved (ChampionDamage / ChampionMaxHP), Alastor at 96-99% after 5 minutes. A member short of the
	// dungeon's Sung Ma requirement gets the missing Will for the run (what a player's Sung Ma stones would give) -
	// the bots stronger, the dungeon unchanged.
	const DWORD AFFECT_PLAYERBOT_YDG_SUNGMA[4] = { 869, 870, 871, 872 };	// Sila, Witalnosc, Odpornosc, Inteligencja

	void BuffPlayerBotYdgMember(LPCHARACTER c)
	{
		if (!c)
			return;
		const long dur = 3700;
		const int poison = GetPlayerBotYdgEnv("PLAYERBOT_YDG_POISON_PCT", 15, 0, 50);
		const int bleed = GetPlayerBotYdgEnv("PLAYERBOT_YDG_BLEED_PCT", 15, 0, 50);
		const int monster = GetPlayerBotYdgEnv("PLAYERBOT_YDG_MONSTER_PCT", 50, 0, 80);
		// the 5 November night: one Yonghan down in 27 minutes with the first three - a gear's critical and
		// piercing hits as well
		const int crit = GetPlayerBotYdgEnv("PLAYERBOT_YDG_CRIT_PCT", 30, 0, 50);
		const int pierce = GetPlayerBotYdgEnv("PLAYERBOT_YDG_PIERCE_PCT", 25, 0, 50);
		if (crit > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_CRIT, POINT_CRITICAL_PCT, crit, 0, dur, 0, true);
		if (pierce > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_PIERCE, POINT_PENETRATE_PCT, pierce, 0, dur, 0, true);
		// V3: the SZC cave's route to the key's Yonghans is ~2 400 cells of walk (the navigation's plan, 5 November) -
		// a speed potion's and a fast weapon's worth of movement and attack speed.
		const int move = GetPlayerBotYdgEnv("PLAYERBOT_YDG_MOVE_SPEED", 80, 0, 100);
		const int attspd = GetPlayerBotYdgEnv("PLAYERBOT_YDG_ATT_SPEED", 30, 0, 50);
		if (move > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_MOVE, POINT_MOV_SPEED, move, 0, dur, 0, true);
		if (attspd > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_ATTSPD, POINT_ATT_SPEED, attspd, 0, dur, 0, true);
		if (poison > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_POISON, POINT_POISON_PCT, poison, 0, dur, 0, true);
		if (bleed > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_BLEED, POINT_BLEEDING_PCT, bleed, 0, dur, 0, true);
		if (monster > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_MONSTER, POINT_ATTBONUS_MONSTER, monster, 0, dur, 0, true);
		const int hp = GetPlayerBotYdgEnv("PLAYERBOT_YDG_HP_PCT", 20, 0, 50);
		if (hp > 0)
			c->AddAffect(AFFECT_PLAYERBOT_YDG_HP, POINT_MAX_HP_PCT, hp, 0, dur, 0, true);
	}

	// The run's dungeon's Sung Ma requirement filled up (see AFFECT_PLAYERBOT_YDG_SUNGMA); the added Will logged.
	std::string BuffPlayerBotYdgSungma(LPCHARACTER c, long lMap)
	{
		const champion::SungmaRequirement* req = c && lMap > 0 && GetPlayerBotYdgEnv("PLAYERBOT_YDG_SUNGMA", 1, 0, 1) ?
				champion::MapRequirement(lMap) : NULL;
		if (!req)
			return "";
		int want[4] = { req->str, req->hp, req->move, req->immune };
		// Jaskinie Gnolli: the run walks 382 -> 383 -> 384 (25/15/20/25 .. 75/60/65/65) - the deepest maze's Will
		for (long m = lMap + 1; lMap == 382 && m <= 384; ++m)
		{
			const champion::SungmaRequirement* r = champion::MapRequirement(m);
			if (!r)
				continue;
			want[0] = std::max(want[0], (int)r->str);
			want[1] = std::max(want[1], (int)r->hp);
			want[2] = std::max(want[2], (int)r->move);
			want[3] = std::max(want[3], (int)r->immune);
		}
		std::string added;
		for (int k = 0; k < 4; ++k)
		{
			const BYTE point = (BYTE)(POINT_SUNGMA_STR + k);
			const int have = yohara_gear::SungmaEffective(c, point);
			if (have >= want[k])
				continue;
			const int pct = MAX(-99, (int)c->GetPoint(POINT_SUNGMA_PER_STR + k));
			const int add = (want[k] - have) * 100 / (100 + pct) + 1;
			c->AddAffect(AFFECT_PLAYERBOT_YDG_SUNGMA[k], point, add, 0, 3700, 0, true);
			added += (added.empty() ? "" : "/") + std::to_string(k) + "+" + std::to_string(add);
		}
		return added;
	}

	void NotePlayerBotYdgRunStart(const TPlayerBotDgRun& run)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		static const char* const cls[4] = { "W", "N", "S", "Sh" };
		std::map<DWORD, TPlayerBotYdgSnap>& snaps = s_mapPlayerBotYdgSnaps[run.iId];
		snaps.clear();
		std::string mix;
		int gearSum = 0, n = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			MakePlayerBotYdgRoom(c, "run_start");	// V2: a cell for the run's items
			BuffPlayerBotYdgMember(c);
			{
				const std::string sm = BuffPlayerBotYdgSungma(c, def.lMap);
				if (!sm.empty())
					sys_log(0, "BOT_YDG: sungma run=%d pid=%u name=%s map=%ld added=%s", run.iId, c->GetPlayerID(), c->GetName(),
							def.lMap, sm.c_str());
			}
			snaps[run.members[i]] = SnapPlayerBotYdg(c);
			int plus = 0;
			const int gear = GetPlayerBotYdgGearLevel(c, &plus);
			gearSum += gear;
			++n;
			char buf[96];
			snprintf(buf, sizeof(buf), "%s%s:%s%d/%d/c%d/g%d+%d", mix.empty() ? "" : ",", c->GetName(), cls[c->GetJob() % 4],
					(int)c->GetSkillGroup(), (int)c->GetLevel(), (int)c->GetConquerorLevel(), gear, plus);
			mix += buf;
		}
		sys_log(0, "BOT_YDG: run start run=%d dungeon=%s instance=%ld train_party=%d members=%d gear_avg=%d mix=%s", run.iId,
				def.szKey, run.lInstance, GetPlayerBotYdgTrainParty(run.iId), n, n ? gearSum / n : 0, mix.c_str());
		NotePlayerBotGlebieRunStart(run);	// MT2009_PLUS_BOT_GLEBIE_V1
	}

	void NotePlayerBotYdgRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(def.szKey);
		const bool won = run.dwFinishedAt != 0;
		const int party = GetPlayerBotYdgTrainParty(run.iId);
		NotePlayerBotGlebieRunEnd(run);	// MT2009_PLUS_BOT_GLEBIE_V1: the chests at Upiorny Straznik, the members' marks
		for (size_t i = 0; i < s_vecPlayerBotYdgTrain.size(); ++i)
			if (s_vecPlayerBotYdgTrain[i].iId == party)
			{
				TPlayerBotYdgTrainParty& tp = s_vecPlayerBotYdgTrain[i];
				if (entered)
					++tp.runs;
				if (won)
					++tp.wins;
				char buf[96];
				snprintf(buf, sizeof(buf), "%s:%s:%us:st%d", def.szKey, result ? result : "-", tookS, run.iStage);
				tp.last = buf;
				tp.dwRestUntil = get_dword_time() + PLAYERBOT_YDG_TRAIN_REST_MIN_MS + (DWORD)number(0, (int)PLAYERBOT_YDG_TRAIN_REST_SPREAD_MS);
			}
		long long gold = 0, exp = 0;
		int levels = 0, conq = 0, items = 0, lvLow = 0, lvHigh = 0;
		std::string names;
		std::map<DWORD, TPlayerBotYdgSnap>& snaps = s_mapPlayerBotYdgSnaps[run.iId];
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!c)
				continue;
			if (y)
				DropPlayerBotYdgItems(c, *y);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_POISON);	// V2: the run's bonuses end with it
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_BLEED);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MONSTER);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_HP);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_CRIT);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_PIERCE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MOVE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_ATTSPD);
			for (int k = 0; k < 4; ++k)
				c->RemoveAffect(AFFECT_PLAYERBOT_YDG_SUNGMA[k]);
			const int lv = c->GetLevel();
			lvLow = lvLow == 0 || lv < lvLow ? lv : lvLow;
			lvHigh = std::max(lvHigh, lv);
			if (names.size() < 200)
				names += (names.empty() ? "" : ",") + std::string(c->GetName());
			std::map<DWORD, TPlayerBotYdgSnap>::const_iterator s = snaps.find(run.members[i]);
			if (s == snaps.end())
				continue;
			const TPlayerBotYdgSnap now = SnapPlayerBotYdg(c);
			gold += now.gold - s->second.gold;
			levels += now.level - s->second.level;
			conq += now.conqueror - s->second.conqueror;
			items += now.items - s->second.items;
			if (now.level == s->second.level)
				exp += now.exp - s->second.exp;
		}
		s_mapPlayerBotYdgSnaps.erase(run.iId);
		s_mapPlayerBotYdgNextAt.erase(run.iId);
		s_mapPlayerBotYdgSticky.erase(run.iId);
		s_mapPlayerBotYdgRoutePlanAt.erase(run.iId);
		if (run.lInstance)
			ForgetPlayerBotWeze(run.lInstance);	// MT2009_PLUS_BOT_YDG_WEZE_V1
		if (run.lInstance)
		{
			s_mapPlayerBotYdgKeysReady.erase(run.lInstance);
			s_mapPlayerBotYdgSzcSpot.erase(run.lInstance);
			for (std::map<std::pair<long, int>, std::set<DWORD> >::iterator w = s_mapPlayerBotYdgWrong.begin(); w != s_mapPlayerBotYdgWrong.end();)
			{
				if (w->first.first == run.lInstance)
					s_mapPlayerBotYdgWrong.erase(w++);
				else
					++w;
			}
		}
		sys_log(0, "BOT_YDG: run end run=%d dungeon=%s train_party=%d result=%s won=%d entered=%d took_s=%u stage=%d stage_s=%s "
				"deaths=%d wipes=%d break_offs=%d members=%u levels=%d-%d gold=%lld exp=%lld level_ups=%d champion_ups=%d items=%d",
				run.iId, def.szKey, party, result ? result : "-", won ? 1 : 0, entered ? 1 : 0, tookS, run.iStage,
				run.stageSecs.empty() ? "-" : run.stageSecs.c_str(), run.iDeaths, run.iWipes, run.iBreakOffs,
				(unsigned int)run.members.size(), lvLow, lvHigh, gold, exp, levels, conq, items);
		FILE* fp = fopen(PLAYERBOT_YDG_RUNS_FILE, "a");
		if (fp)
		{
			fprintf(fp, "%ld\t%d\t%s\t%d\t%s\t%d\t%u\t%d\t%s\t%d\t%d\t%u\t%d\t%d\t%lld\t%lld\t%d\t%d\t%s\n", (long)time(0), run.iId,
					def.szKey, party, result ? result : "-", won ? 1 : 0, tookS, run.iStage,
					run.stageSecs.empty() ? "-" : run.stageSecs.c_str(), run.iDeaths, run.iWipes, (unsigned int)run.members.size(),
					lvLow, lvHigh, gold, exp, levels, items, names.empty() ? "-" : names.c_str());
			fclose(fp);
		}
	}

	// A training party's members rest briefly - they are there for it.
	DWORD AdjustPlayerBotYdgRest(const TPlayerBotDgRun& run, DWORD rest)
	{
		if (GetPlayerBotYdgTrainParty(run.iId) == 0)
			return rest;
		return PLAYERBOT_YDG_TRAIN_REST_MIN_MS + (DWORD)number(0, (int)PLAYERBOT_YDG_TRAIN_REST_SPREAD_MS);
	}
}

#endif
