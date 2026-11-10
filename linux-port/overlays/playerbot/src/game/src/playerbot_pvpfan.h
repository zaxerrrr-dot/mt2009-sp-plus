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
//               with allow_players), kingdom, guild, party and PK mode do not matter; MT2009_PLUS_PVPFAN_WARSTYLE_V1
//               (the owner, 10 November 2026): the fight is a guild war's - each bot draws a random enemy near it
//               (near ones likelier, a light spread), keeps it until it falls, gets away or 8-15 s pass, chases it
//               without a stop and strikes as the duel and the guild war do (buffs, gap closers, casters from range,
//               archers from 800 with a step back, the due skills in a random order, potions per potions), shamans
//               heal and buff now and then (see "the fight" above FightPlayerBotPvpFanWarStyle); a bot that strays
//               past arena_radius walks back; the fallen stay down (their dead event is cancelled - no restart, no experience lost) and a
//               death is no murder (PvpFanDeath, char_battle.cpp: no alignment, no dropped item). When at most one
//               team stands - or after max_minutes, the team with more standing (then more kills) - the result goes
//               to everybody (BroadcastNotice) and to player.pvpfan_war / _war_team (the panel's history);
//               MT2009_PLUS_PVPFAN_TACTICS_V1 (the owner, 8 November 2026: "a real war, not two blobs"; experimental
//               since 10 November - it stuttered): with the category's tactics = 2 the teams start as squads side by
//               side and fight as squads - objectives
//               spread over the enemy front, shared focus, flanks, ranged that keep their range and kite, melee that
//               peel and chase casters, healers behind, wounded that retreat and drink, squads that regroup and come
//               back; the whole design is at "tactics: roles, squads, the formation" below;
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
// M2_PVPFAN_MAX_CATEGORY (500) and M2_PVPFAN_MAX_TOTAL (1000, per core), M2_PVPFAN_SPAWN_PER_SEC (20). The
// experimental squads: pvpfan_category.tactics = 2 (0 and 1: the guild war's fight, the default), squad_size (5),
// kite_distance (400, 0 = no kiting), retreat_hp (35, 0 = no retreats) - read only with tactics = 2; the event flag
// m2_pvpfan_tactics_off (game flag or player.quest row) puts every war on the guild war's fight. Logs: "PVPFAN:"
// lines, a census a minute while a war runs ("census fight": foes drawn and let go, the spread over targets, the
// fighters' tick gaps; with the squads also "census tactics") and a "fight summary" / "tactics summary" at the result.
//
// An implementation fragment in the sense playerbot_types.h describes: included once, after playerbot_petmat.h.
#include <unordered_map>
#include <cmath>

int PvpFanAttackable(LPCHARACTER ch, LPCHARACTER victim);
bool PvpFanDeath(LPCHARACTER victim, LPCHARACTER killer);
void PlayerBotPvpFanCommand(LPCHARACTER ch, const char* argument);

namespace
{
	const DWORD PVPFAN_TICK_MS = 200;	// MT2009_PLUS_PVPFAN_WARSTYLE_V1: under the bot-manager's ~240 ms, so every tick
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

	// MT2009_PLUS_PVPFAN_WARSTYLE_V1 (the owner, 10 November 2026): the default fight is a guild war's - see "the fight"
	// above FightPlayerBotPvpFanWarStyle. Distances in world units (100 = 1 m).
	const DWORD PVPFAN_BOT_TICK_MIN_MS = 150;		// the fighters' own pass, every bot-manager tick (~240 ms), not oftener
	const int PVPFAN_PICK_RADIUS = 1800;			// a new foe drawn from the enemies this near (the grid)
	const int PVPFAN_KEEP_RANGE = 2600;				// a foe further than this has got away: draw another
	const DWORD PVPFAN_KEEP_MIN_MS = 8000;			// a foe is kept 8-15 s (drawn per pick), then another is drawn
	const DWORD PVPFAN_KEEP_MAX_MS = 15000;
	const DWORD PVPFAN_LOOK_MS = 600;				// nobody near: look again after this
	const DWORD PVPFAN_LOOK_FAR_MS = 2000;			// ... and over the whole arena no oftener than this
	const int PVPFAN_PICK_FALLOFF = 450;			// the draw's weight 1 / (1 + d / falloff)^2: near ones far likelier
	const int PVPFAN_PICK_CROWD = 2;				// ... divided by (1 + crowd / this): a light spread over the enemies
	const DWORD PVPFAN_CHASE_MS = 500;				// a chase's new goal at most this often (the light tick's pace)
	const int PVPFAN_CHASE_DRIFT = 120;				// ... and only when the foe has moved this far from the last one
	const DWORD PVPFAN_SUPPORT_MIN_MS = 1500;		// a shaman's look at its mates: every 1.5-2.5 s ("now and then")
	const DWORD PVPFAN_SUPPORT_MAX_MS = 2500;

	// MT2009_PLUS_PVPFAN_TACTICS_V1 - experimental since MT2009_PLUS_PVPFAN_WARSTYLE_V1 (pvpfan_category.tactics = 2):
	// see "tactics" above FightPlayerBotPvpFanTactics.
	const DWORD PVPFAN_GRID_MS = 500;				// the spatial grid's rebuild
	const DWORD PVPFAN_SQUAD_DECIDE_MS = 1000;		// every squad's decision
	const int PVPFAN_SQUAD_SPACING = 160;			// between two members of a formation
	const int PVPFAN_SQUAD_GAP = 320;				// between two squads at the start
	const int PVPFAN_ENGAGE_RANGE = 1400;			// a squad this near its objective is in the skirmish
	const int PVPFAN_DISENGAGE_RANGE = 2800;		// an objective this far: advance (pursue) again
	const int PVPFAN_SEARCH_RADIUS = 1800;			// a member's look for a foe in the skirmish
	const int PVPFAN_CONTACT_MELEE = 750;			// a member on the march takes a foe this near
	const int PVPFAN_ADVANCE_LEAD = 650;			// how far the rally point leads the marching squad
	const int PVPFAN_FLANK_OFFSET = 1100;			// a flanking squad's swing to the side
	const int PVPFAN_FLANK_UNTIL = 2200;			// ... until this near its objective
	const int PVPFAN_REGROUP_BACK = 1000;			// a regrouping squad falls back this far toward its side
	const int PVPFAN_REGROUP_SPREAD = 1900;			// a squad scattered wider than this regroups
	const int PVPFAN_OUTNUMBER_RANGE = 1300;		// enemies counted round a squad's centroid
	const int PVPFAN_REGROUP_HP = 45;				// a squad's mean HP % under which it falls back
	const int PVPFAN_RETURN_HP = 75;				// HP % a retreat / regroup waits for
	const DWORD PVPFAN_ENGAGE_MIN_MS = 10000;		// a skirmish lasts at least this before a regroup
	const DWORD PVPFAN_REGROUP_MIN_MS = 3500;
	const DWORD PVPFAN_REGROUP_MAX_MS = 9000;
	const DWORD PVPFAN_REGROUP_COOLDOWN_MS = 30000;
	const DWORD PVPFAN_OBJECTIVE_KEEP_MS = 4000;	// a squad's objective is looked at again after this
	const int PVPFAN_OBJECTIVE_CLAIM = 1200;		// an enemy squad already taken by one of ours counts this much further
	const DWORD PVPFAN_RETREAT_MAX_MS = 15000;
	const DWORD PVPFAN_RETREAT_COOLDOWN_MS = 25000;
	const int PVPFAN_RETREAT_STEP = 800;
	const DWORD PVPFAN_KITE_WINDOW_MS = 6000;		// at most PVPFAN_KITE_MAX kites in it, then the bot stands and fights
	const int PVPFAN_KITE_MAX = 2;
	const int PVPFAN_KITE_STEP = 480;
	const DWORD PVPFAN_THREAT_LOOK_MS = 400;
	const int PVPFAN_CASTER_HOLD = 520;				// a caster's distance while it waits for its next spell
	const int PVPFAN_BOW_HOLD = 720;
	const DWORD PVPFAN_CAST_FAIL_MS = 2500;			// a caster with nothing to cast closes in for the blows
	const int PVPFAN_CROWD_PENALTY = 300;
	const int PVPFAN_CROWD_CAP = 4;					// more on one foe than this costs PVPFAN_CROWD_OVER
	const int PVPFAN_CROWD_OVER = 3000;
	const int PVPFAN_FOCUS_BONUS = 900;				// the squad's shared target
	const int PVPFAN_PEEL_BONUS = 1300;				// a melee bot's pull to the enemy at its own back line
	const int PVPFAN_CHASE_CASTER_BONUS = 450;		// a melee bot's pull to a ranged / support foe
	const int PVPFAN_PEEL_RANGE = 450;
	const int PVPFAN_SUPPORT_BACK = 300;			// a support bot's place behind its squad's formation
	const int PVPFAN_HEAL_HP = 60;
	const DWORD PVPFAN_SUPPORT_LOOK_MS = 1200;
	const int PVPFAN_SUPPORT_REACH = 1000;
	const int PVPFAN_SKIRMISH_JOIN = 1500;			// two skirmishing squads this near are one skirmish spot (census)

	enum EPvpFanRole
	{
		PVPFAN_ROLE_MELEE = 0,	// warriors, the dagger ninja, the weapon sura: close the gap, peel, chase casters
		PVPFAN_ROLE_RANGED,		// the archer, the magic sura, the dragon shaman: keep range, kite melee
		PVPFAN_ROLE_SUPPORT,	// the healing shaman: behind the squad, heal and buff, kite melee
	};

	enum EPvpFanSquadMode
	{
		PVPFAN_SQ_ADVANCE = 0,	// in formation toward its objective (on a flank when it is a flanker)
		PVPFAN_SQ_ENGAGE,		// the skirmish: each member on its foe, by its role's technique
		PVPFAN_SQ_REGROUP,		// fallen back toward its side, gathered, potions and heals, then advance again
		PVPFAN_SQ_GONE,			// nobody of it stands (or it was merged into another)
	};

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
		// MT2009_PLUS_PVPFAN_TACTICS_V1: the squad, the role and the techniques' clocks (see "tactics" below).
		int squad = -1;
		BYTE role = 0;				// PVPFAN_ROLE_*
		int slotSide = 0, slotBack = 0;	// the place in the squad's formation, from its rally point
		int hpPct = 100;
		bool engaged = false;		// has a foe within reach now (the squad's ADVANCE -> ENGAGE)
		bool retreating = false;
		DWORD retreatUntil = 0, retreatCdUntil = 0;
		DWORD kiteWindowAt = 0;
		int kiteCount = 0;
		DWORD threatLookAt = 0, supportLookAt = 0, castFailUntil = 0, kiteMoveUntil = 0, foeLookAt = 0;
		long retreatX = 0, retreatY = 0;
		// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the foe's keep, the chase's last goal, the archer's steps back, the tick's clock.
		DWORD keepUntil = 0, chaseAt = 0, lookFarAt = 0, stepWindowAt = 0, tickAt = 0;
		long chaseX = 0, chaseY = 0;
		int steps = 0;
	};

	// MT2009_PLUS_PVPFAN_TACTICS_V1: a squad - 3..12 bots of one team that move, engage, regroup and pick their
	// objective together (DecidePlayerBotPvpFanSquads, once a second for the whole war).
	struct TPvpFanSquad
	{
		int team = 0;
		int idx = 0;
		std::vector<size_t> members;	// indices into the war's fighters
		int mode = 0;					// PVPFAN_SQ_*
		DWORD modeAt = 0;
		DWORD engageAt = 0;
		DWORD regroupCdUntil = 0;
		long cx = 0, cy = 0;			// the centroid of the living
		long rallyX = 0, rallyY = 0;	// where the formation stands / goes
		double fwdX = 1.0, fwdY = 0.0;	// the formation's facing
		long lane = 0;					// the lateral offset it started at (its flank)
		bool flanker = false;
		int alive = 0, hpPct = 100, engagedN = 0, supportAlive = 0, nonSupportAlive = 0;
		long spread = 0;				// the mean distance of the living from the centroid
		int objective = -1;				// an enemy squad's index
		DWORD objectiveAt = 0;
		DWORD focusPid = 0;				// the shared target in the objective squad
		DWORD peelPid = 0;				// the enemy at this squad's back line, for its melee
		int nearFoes = 0;				// enemies within PVPFAN_OUTNUMBER_RANGE of the centroid
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
		// MT2009_PLUS_PVPFAN_TACTICS_V1: the category's switches (pvpfan_category.tactics, squad_size, kite_distance,
		// retreat_hp), the event flag's verdict, the squads, the spatial grid and the census' counters.
		bool tactics = false;		// MT2009_PLUS_PVPFAN_WARSTYLE_V1: experimental, pvpfan_category.tactics = 2
		bool tacticsOn = false;
		int squadSize = 5, kiteDist = 400, retreatHp = 35;
		std::vector<TPvpFanSquad> squads;
		DWORD nextGrid = 0, nextSquads = 0;
		long gridX0 = 0, gridY0 = 0, gridCell = 500;
		int gridDim = 0;
		std::vector<std::vector<int> > grid;
		unsigned int kitesMin = 0, kitesTotal = 0, retreatsMin = 0, retreatsTotal = 0, regroupsMin = 0,
				regroupsTotal = 0, mergesTotal = 0, engagesMin = 0, healsMin = 0, healsTotal = 0, peelsMin = 0;
		unsigned long long engMsMin = 0, engMsTotal = 0;
		unsigned int engEndsMin = 0, engEndsTotal = 0;
		// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the census of the default fight (per minute / whole war) and the fighters'
		// tick gaps (the stutter's measure: the time between two ticks of one bot).
		unsigned int picksMin = 0, picksTotal = 0, endDeadMin = 0, endFledMin = 0, endTimeMin = 0, stepsMin = 0;
		unsigned long long gapSumMs = 0;
		unsigned int gapN = 0, gapMaxMs = 0, gapOver600 = 0;
	};

	std::map<DWORD, TPvpFanWar> s_mapPvpFanWars;
	// Every fighter of a war on this core, pid -> (category, index into its war's fighters).
	std::unordered_map<DWORD, std::pair<DWORD, size_t> > s_mapPvpFanPid;
	DWORD s_dwPvpFanLastTick = 0;
	DWORD s_dwPvpFanNextPoll = 0;
	DWORD s_dwPvpFanNextFlagPoll = 0;
	DWORD s_dwPvpFanNextCensus = 0;
	bool s_bPvpFanDbFlagOff = false;
	bool s_bPvpFanDbTacticsOff = false;	// MT2009_PLUS_PVPFAN_TACTICS_V1: the player.quest row of m2_pvpfan_tactics_off
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

	// MT2009_PLUS_PVPFAN_TACTICS_V1: "m2_pvpfan_tactics_off" (game flag or the player.quest row) - every war fights
	// the guild war's way, the experimental squads too (a running war switches at its next evaluation).
	bool IsPlayerBotPvpFanTacticsFlagOff()
	{
		return s_bPvpFanDbTacticsOff || quest::CQuestManager::instance().GetEventFlag("m2_pvpfan_tactics_off") != 0;
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
	void PlacePlayerBotPvpFanTeamPoints(TPvpFanWar& war)
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
	}

	void PlacePlayerBotPvpFanSpots(TPvpFanWar& war)
	{
		const size_t n = war.teams.size();
		PlacePlayerBotPvpFanTeamPoints(war);
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

	// ------------------------------------------------------------------ tactics: roles, squads, the formation
	// MT2009_PLUS_PVPFAN_TACTICS_V1 - the owner, 8 November 2026: a war, not two blobs running into each other. The
	// whole of it:
	//   roles      - melee (warriors, the dagger ninja, the weapon sura), ranged (the archer, the magic sura, the dragon
	//                shaman), support (the healing shaman) - PvpFanRoleOf, from the slot's class and path;
	//   squads     - each team dealt, role by role, into squads of squad_size (3-6 typical): every squad the same mix
	//                (BuildPlayerBotPvpFanSquads); at the start they stand side by side across the team's front, two
	//                lines of squads where the front is narrow, each a small block: melee in front, ranged behind,
	//                support at the back (PlacePlayerBotPvpFanSquadSpots);
	//   decisions  - once a second for the whole war (DecidePlayerBotPvpFanSquads, O(fighters + squads^2)): each squad's
	//                centroid, HP, spread; its objective - the nearest enemy squad that not too many of its own team
	//                already took (the targets spread over the enemy front, several skirmishes at once); its shared
	//                focus (the weakest of the objective, healers and casters first) and the enemy at its own back line
	//                (its melee peel for its ranged); its mode:
	//                  ADVANCE  - in formation behind a rally point that leads it toward the objective, an outer squad
	//                             swinging out on its flank until it is close;
	//                  ENGAGE   - the skirmish (objective within PVPFAN_ENGAGE_RANGE or half of it in contact);
	//                  REGROUP  - after PVPFAN_ENGAGE_MIN_MS of skirmish: hurt (mean HP < PVPFAN_REGROUP_HP while
	//                             potions or a healer can mend it), scattered (> PVPFAN_REGROUP_SPREAD) or outnumbered
	//                             two to one - back toward its side, gathered, mended, then ADVANCE again;
	//                a squad down to a third or less joins the nearest one of its team;
	//   each bot   - (FightPlayerBotPvpFanTactics) wounded under retreat_hp: retreats to its squad's healer or toward
	//                its side, drinks (potions on), comes back at PVPFAN_RETURN_HP or after PVPFAN_RETREAT_MAX_MS;
	//                support: heals the lowest of its squad, buffs it; ranged and support: kite_distance from a melee foe
	//                means a step away (sideways, toward its squad, kept inside the arena), PVPFAN_KITE_MAX in
	//                PVPFAN_KITE_WINDOW_MS, then it stands and fights; ranged hold their range and cast/shoot from it;
	//                melee close the gap (the duel's gap closers), go for the squad's focus, peel for their back line
	//                and chase casters; the foe from the spatial grid near the bot (never a scan of the whole war).
	// The bow, the casts, the blows and the buffs are the duel's and the guild war's (StrikePlayerBotPvpFanFoe) - the
	// fight is not softer, it moves.

	BYTE PvpFanRoleOf(BYTE job, BYTE group)
	{
		switch (playerbot_war_rules::KindOf(job, group))
		{
			case playerbot_war_rules::KIND_NINJA_ARCHER:
			case playerbot_war_rules::KIND_SURA_MAGIC:
			case playerbot_war_rules::KIND_SHAMAN_DRAGON:
				return PVPFAN_ROLE_RANGED;
			case playerbot_war_rules::KIND_SHAMAN_HEAL:
				return PVPFAN_ROLE_SUPPORT;
			default:
				return PVPFAN_ROLE_MELEE;
		}
	}

	const char* PvpFanSquadModeCode(int m)
	{
		switch (m)
		{
			case PVPFAN_SQ_ADVANCE: return "advance";
			case PVPFAN_SQ_ENGAGE: return "engage";
			case PVPFAN_SQ_REGROUP: return "regroup";
			default: return "gone";
		}
	}

	// The formation's columns: three abreast (fewer for a squad of two).
	int PvpFanSquadCols(size_t members)
	{
		return members < 3 ? (int)std::max<size_t>(members, 1) : 3;
	}

	// Each member's place in its squad's block, from the rally point: the list is melee first (the dealing below
	// keeps the roster's role order), so the front row is the melee and the back rows the ranged and the support.
	void SetPlayerBotPvpFanSquadSlots(TPvpFanWar& war, TPvpFanSquad& sq)
	{
		const int cols = PvpFanSquadCols(sq.members.size());
		for (size_t j = 0; j < sq.members.size(); ++j)
		{
			TPvpFanFighter& f = war.fighters[sq.members[j]];
			const int col = (int)j % cols, row = (int)j / cols;
			f.slotSide = (int)((col - (cols - 1) / 2.0) * PVPFAN_SQUAD_SPACING);
			f.slotBack = row * PVPFAN_SQUAD_SPACING * 13 / 10 + (f.role == PVPFAN_ROLE_SUPPORT ? PVPFAN_SUPPORT_BACK / 2 : 0);
		}
	}

	// Each team dealt into ceil(n / squad_size) squads, role by role, so every squad gets the same mix.
	void BuildPlayerBotPvpFanSquads(TPvpFanWar& war)
	{
		war.squads.clear();
		const int size = std::max(2, war.squadSize);
		for (size_t t = 0; t < war.teams.size(); ++t)
		{
			std::vector<size_t> roster;
			for (int role = PVPFAN_ROLE_MELEE; role <= PVPFAN_ROLE_SUPPORT; ++role)
				for (size_t i = 0; i < war.fighters.size(); ++i)
					if (war.fighters[i].team == (int)t && war.fighters[i].role == role)
						roster.push_back(i);
			if (roster.empty())
				continue;
			const size_t k = (roster.size() + size - 1) / size;
			const size_t first = war.squads.size();
			for (size_t q = 0; q < k; ++q)
			{
				TPvpFanSquad sq;
				sq.team = (int)t;
				sq.idx = (int)(first + q);
				war.squads.push_back(sq);
			}
			for (size_t j = 0; j < roster.size(); ++j)
			{
				TPvpFanSquad& sq = war.squads[first + j % k];
				sq.members.push_back(roster[j]);
				war.fighters[roster[j]].squad = sq.idx;
			}
			for (size_t q = 0; q < k; ++q)
				SetPlayerBotPvpFanSquadSlots(war, war.squads[first + q]);
		}
	}

	// The start: each team's squads side by side across its front (as many abreast as the arena's width allows, the
	// rest a line behind), facing the centre, every bot on open ground near its place. A squad at either end of a
	// front of three or more is a flanker.
	void PlacePlayerBotPvpFanSquadSpots(TPvpFanWar& war)
	{
		PlacePlayerBotPvpFanTeamPoints(war);
		std::vector<int> perTeam(war.teams.size(), 0), seen(war.teams.size(), 0);
		for (size_t q = 0; q < war.squads.size(); ++q)
			++perTeam[war.squads[q].team];
		const long frontMax = std::min<long>(war.radius * 2 + 1000, war.arenaRadius * 16 / 10);
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			TPvpFanSquad& sq = war.squads[q];
			const TPvpFanTeam& team = war.teams[sq.team];
			const int k = seen[sq.team]++;
			const int cols = PvpFanSquadCols(sq.members.size());
			const long width = cols * PVPFAN_SQUAD_SPACING + PVPFAN_SQUAD_GAP;
			const long rows = ((long)sq.members.size() + cols - 1) / cols;
			const long depth = rows * PVPFAN_SQUAD_SPACING * 13 / 10 + PVPFAN_SUPPORT_BACK + PVPFAN_SQUAD_GAP;
			const int abreast = MINMAX(1, (int)(frontMax / width), std::max(1, perTeam[sq.team]));
			double fx = (double)(war.cx - team.x), fy = (double)(war.cy - team.y);
			double len = sqrt(fx * fx + fy * fy);
			if (len < 1.0)
			{
				fx = 1.0;
				fy = 0.0;
				len = 1.0;
			}
			fx /= len;
			fy /= len;
			const int inRow = std::min(abreast, perTeam[sq.team] - (k / abreast) * abreast);
			const long side = (long)((k % abreast - (inRow - 1) / 2.0) * width);
			const long back = (long)(k / abreast) * depth;
			sq.lane = side;
			sq.flanker = inRow >= 3 && (k % abreast == 0 || k % abreast == inRow - 1);
			sq.fwdX = fx;
			sq.fwdY = fy;
			sq.rallyX = team.x + (long)(-fy * side - fx * back);
			sq.rallyY = team.y + (long)(fx * side - fy * back);
			sq.cx = sq.rallyX;
			sq.cy = sq.rallyY;
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				TPvpFanFighter& f = war.fighters[sq.members[j]];
				const long sx = sq.rallyX + (long)(-fy * f.slotSide - fx * f.slotBack);
				const long sy = sq.rallyY + (long)(fx * f.slotSide - fy * f.slotBack);
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
	}

	bool LoadPlayerBotPvpFanWar(DWORD catId, TPvpFanWar& war, std::string& err)
	{
		// MT2009_PLUS_PVPFAN_TACTICS_V1: the tactics' columns (pvpfan.sql); a core ahead of its migrator reads the
		// first version's and fights with the defaults.
		std::unique_ptr<SQLMsg> cat = PvpFanQuery(
				"SELECT id, code, name, enabled, map_index, x, y, radius, arena_radius, channel, countdown_sec, max_minutes, "
				"exit_sec, allow_players, potions, tactics, squad_size, kite_distance, retreat_hp "
				"FROM player.pvpfan_category WHERE id=%u", catId);
		bool tacticsColumns = PvpFanOk(cat);
		if (!tacticsColumns)
			cat = PvpFanQuery(
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
		if (tacticsColumns)
		{
			// MT2009_PLUS_PVPFAN_WARSTYLE_V1: only 2 is the experimental squads; 0 and 1 (the old default) the guild
			// war's fight
			war.tactics = PvpFanLong(row[15]) == 2;
			war.squadSize = MINMAX(2, (int)PvpFanLong(row[16]), 12);
			war.kiteDist = PvpFanLong(row[17]) <= 0 ? 0 : MINMAX(150, (int)PvpFanLong(row[17]), 900);
			war.retreatHp = PvpFanLong(row[18]) <= 0 ? 0 : MINMAX(5, (int)PvpFanLong(row[18]), 80);
		}
		war.tacticsOn = war.tactics && !IsPlayerBotPvpFanTacticsFlagOff();
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
		for (size_t i = 0; i < war.fighters.size(); ++i)
			war.fighters[i].role = PvpFanRoleOf(war.fighters[i].job, war.fighters[i].group);
		if (war.tactics)
			BuildPlayerBotPvpFanSquads(war);
		if (war.tacticsOn && !war.squads.empty())
			PlacePlayerBotPvpFanSquadSpots(war);
		else
			PlacePlayerBotPvpFanSpots(war);
		sys_log(0, "PVPFAN: fight category=%u code=%s style=%s (experimental column=%d flag_off=%d) squad_size=%d "
				"squads=%u kite=%d retreat_hp=%d", war.catId, war.code.c_str(),
				war.tacticsOn && !war.squads.empty() ? "squads-experimental" : "guild-war", war.tactics ? 1 : 0,
				IsPlayerBotPvpFanTacticsFlagOff() ? 1 : 0, war.squadSize, (unsigned int)war.squads.size(), war.kiteDist,
				war.retreatHp);
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
					// MT2009_PLUS_DS_DISTINCT_ATTR_V1 (pvpfan): ClearAttribute() stops at slot 5 - the 6th/7th
					// (a new Dragon Stone's third additional bonus) would stay beside the set's own bonuses
					for (int a = ITEM_ATTRIBUTE_NORM_NUM; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
						item->ClearAttribute(a);
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

	bool IsPlayerBotPvpFanFoeUp(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch, LPCHARACTER foe)
	{
		if (!foe || foe->IsDead() || foe->GetHP() <= 0 || !foe->IsPC() || foe->GetMapIndex() != ch->GetMapIndex())
			return false;
		TPvpFanWar* fw = NULL;
		TPvpFanFighter* e = FindPlayerBotPvpFanFighter(foe->GetPlayerID(), &fw);
		return e && fw == &war && e->team != f.team && !e->dead;
	}

	// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the duel's / guild war's cast with the due skills in a random order.
	bool CastPlayerBotPvpFanSkill(LPCHARACTER ch, LPCHARACTER foe, TPlayerBotAIState& state, DWORD dwNow)
	{
		s_bPlayerBotShuffleAttackSkills = true;
		const bool cast = CastPlayerBotDuelSkill(ch, foe, state, dwNow);
		s_bPlayerBotShuffleAttackSkills = false;
		return cast;
	}

	// The blow itself - the fight a duel and a guild war are: the aura first, a caster from its range, a warrior across
	// the gap, a blade from where it reaches, the bow from 800. holdRange (MT2009_PLUS_PVPFAN_TACTICS_V1, the ranged
	// and the support): a caster waiting for its next spell stands at its range instead of walking into the blades,
	// and a bow walks only to the edge of its reach; a caster with nothing to cast closes in for PVPFAN_CAST_FAIL_MS.
	void StrikePlayerBotPvpFanFoe(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			LPCHARACTER foe, DWORD dwNow, bool holdRange)
	{
		const int distance = DISTANCE_APPROX(ch->GetX() - foe->GetX(), ch->GetY() - foe->GetY());
		state.dwTargetVID = (DWORD)foe->GetVID();
		f.targetPid = foe->GetPlayerID();
		ch->SetVictim(foe);
		ch->SetRotationToXY(foe->GetX(), foe->GetY());
		SetPlayerBotAction(state, BOT_ACTION_FIGHT, dwNow);
		if (distance <= PLAYERBOT_DUEL_BUFF_RANGE && ManagePlayerBotCombatBuffs(ch, state, dwNow, true))
			return;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		const bool isBow = weapon && weapon->GetType() == ITEM_WEAPON && weapon->GetSubType() == WEAPON_BOW;
		const int combatRange = isBow ? 800 : PLAYERBOT_DUEL_MELEE_RANGE;
		// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the guild war's casters (ManagePlayerBotGuildWar): the dragon shaman goes in
		// for its splash like a fighter; the experimental squads (holdRange) keep it a caster.
		const bool caster = (ch->GetJob() == JOB_SHAMAN && (holdRange || playerbot_war_rules::KindOf(ch->GetJob(),
				ch->GetSkillGroup()) != playerbot_war_rules::KIND_SHAMAN_DRAGON)) ||
				(ch->GetJob() == JOB_SURA && ch->GetSkillGroup() == 2);
		if (distance > combatRange)
		{
			if (!isBow && caster && distance <= PLAYERBOT_DUEL_CASTER_RANGE && dwNow >= state.dwNextSkillCastTime)
			{
				if (ch->IsStateMove())
					ch->Stop();
				if (CastPlayerBotPvpFanSkill(ch, foe, state, dwNow))
					return;
				if (holdRange)
					f.castFailUntil = dwNow + PVPFAN_CAST_FAIL_MS;
			}
			if (!isBow && distance <= PLAYERBOT_SEARCH_RANGE && TryPlayerBotDuelGapCloser(ch, foe, state, dwNow, distance))
				return;
			if (holdRange && (isBow || (caster && dwNow >= f.castFailUntil)))
			{
				const int hold = isBow ? PVPFAN_BOW_HOLD : PVPFAN_CASTER_HOLD;
				if (!isBow && distance <= PLAYERBOT_DUEL_CASTER_RANGE + 40)
				{
					if (ch->IsStateMove())
						ch->Stop();
					return;
				}
				if (dwNow >= state.dwNextGuildWarMoveTime)
				{
					state.dwNextGuildWarMoveTime = dwNow + 700;
					const double dx = (double)(ch->GetX() - foe->GetX()), dy = (double)(ch->GetY() - foe->GetY());
					const double len = std::max(1.0, sqrt(dx * dx + dy * dy));
					MovePlayerBot(ch, foe->GetX() + (long)(dx / len * hold), foe->GetY() + (long)(dy / len * hold), dwNow, 4,
							true, false);
				}
				return;
			}
			// MT2009_PLUS_PVPFAN_WARSTYLE_V1: one continuous chase - a new goal when the foe has moved off the last
			// one (at most every PVPFAN_CHASE_MS), at once when the walk has ended; never a Stop on the way.
			const bool walking = ch->IsStateMove();
			if (!walking ? PvpFanSince(dwNow, f.chaseAt) >= 200
					: PvpFanSince(dwNow, f.chaseAt) >= PVPFAN_CHASE_MS &&
						DISTANCE_APPROX(foe->GetX() - f.chaseX, foe->GetY() - f.chaseY) > PVPFAN_CHASE_DRIFT)
			{
				f.chaseAt = dwNow;
				f.chaseX = foe->GetX();
				f.chaseY = foe->GetY();
				MovePlayerBot(ch, f.chaseX, f.chaseY, dwNow, 4, false, false);
			}
			return;
		}
		if (ch->IsStateMove())
			ch->Stop();
		ch->SetPosition(POS_FIGHTING);
		if (!CastPlayerBotPvpFanSkill(ch, foe, state, dwNow))
			ExecutePlayerBotBasicAttack(ch, foe, state, dwNow);
	}

	// ------------------------------------------------------------------ tactics: the grid
	// MT2009_PLUS_PVPFAN_TACTICS_V1: every standing fighter of a war in square cells, rebuilt every PVPFAN_GRID_MS from
	// the characters' positions (lastX/lastY, hpPct): "who is near" is a look at a few cells, never a pass over the war.
	// A bot beyond the grid (it is 1.25 arena radii and more) counts in the edge cell; the distance check sorts it out.
	int PvpFanGridAxis(const TPvpFanWar& war, long v, long origin)
	{
		return MINMAX(0, (int)((v - origin) / war.gridCell), war.gridDim - 1);
	}

	void BuildPlayerBotPvpFanGrid(TPvpFanWar& war)
	{
		const long reach = war.arenaRadius * 5 / 4 + 500;
		war.gridCell = std::max(500L, reach * 2 / 100);
		war.gridDim = (int)(reach * 2 / war.gridCell) + 1;
		war.gridX0 = war.cx - reach;
		war.gridY0 = war.cy - reach;
		const size_t cells = (size_t)war.gridDim * (size_t)war.gridDim;
		if (war.grid.size() != cells)
			war.grid.assign(cells, std::vector<int>());
		else
			for (size_t c = 0; c < cells; ++c)
				war.grid[c].clear();
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			TPvpFanFighter& f = war.fighters[i];
			if (f.phase != PVPFAN_F_READY || f.dead)
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(f.pid);
			if (!ch || ch->IsDead() || ch->GetMapIndex() != war.map)
				continue;
			f.lastX = ch->GetX();
			f.lastY = ch->GetY();
			f.hpPct = ch->GetMaxHP() > 0 ? (int)((long long)MAX(0, ch->GetHP()) * 100 / ch->GetMaxHP()) : 0;
			war.grid[(size_t)PvpFanGridAxis(war, f.lastY, war.gridY0) * war.gridDim +
					PvpFanGridAxis(war, f.lastX, war.gridX0)].push_back((int)i);
		}
	}

	// fn(index, fighter) for every fighter of the grid within r of (x, y) - its position of the last rebuild.
	template <class F> void ForEachPlayerBotPvpFanNear(TPvpFanWar& war, long x, long y, long r, F fn)
	{
		if (war.gridDim <= 0 || war.grid.empty())
			return;
		const int x0 = PvpFanGridAxis(war, x - r, war.gridX0), x1 = PvpFanGridAxis(war, x + r, war.gridX0);
		const int y0 = PvpFanGridAxis(war, y - r, war.gridY0), y1 = PvpFanGridAxis(war, y + r, war.gridY0);
		for (int gy = y0; gy <= y1; ++gy)
			for (int gx = x0; gx <= x1; ++gx)
			{
				const std::vector<int>& cell = war.grid[(size_t)gy * war.gridDim + gx];
				for (size_t k = 0; k < cell.size(); ++k)
				{
					TPvpFanFighter& e = war.fighters[cell[k]];
					if (!e.dead && DISTANCE_APPROX(e.lastX - x, e.lastY - y) <= r)
						fn(cell[k], e);
				}
			}
	}

	// A point kept inside permille of the arena's radius.
	void ClampPlayerBotPvpFanToArena(const TPvpFanWar& war, long& x, long& y, int permille = 900)
	{
		const double lim = (double)war.arenaRadius * permille / 1000.0;
		const double dx = (double)(x - war.cx), dy = (double)(y - war.cy);
		const double len = sqrt(dx * dx + dy * dy);
		if (len > lim && len >= 1.0)
		{
			x = war.cx + (long)(dx / len * lim);
			y = war.cy + (long)(dy / len * lim);
		}
	}

	// ------------------------------------------------------------------ tactics: the squads' decisions

	void EndPlayerBotPvpFanEngagement(TPvpFanWar& war, TPvpFanSquad& sq, DWORD dwNow)
	{
		if (sq.mode == PVPFAN_SQ_ENGAGE && sq.engageAt)
		{
			const DWORD ms = PvpFanSince(dwNow, sq.engageAt);
			war.engMsMin += ms;
			war.engMsTotal += ms;
			++war.engEndsMin;
			++war.engEndsTotal;
		}
		sq.engageAt = 0;
	}

	void SetPlayerBotPvpFanSquadMode(TPvpFanWar& war, TPvpFanSquad& sq, int mode, DWORD dwNow, const char* why)
	{
		if (sq.mode == mode)
			return;
		EndPlayerBotPvpFanEngagement(war, sq, dwNow);
		if (mode == PVPFAN_SQ_ENGAGE)
		{
			sq.engageAt = dwNow;
			++war.engagesMin;
		}
		else if (mode == PVPFAN_SQ_REGROUP)
		{
			++war.regroupsMin;
			++war.regroupsTotal;
			sq.regroupCdUntil = dwNow + PVPFAN_REGROUP_COOLDOWN_MS;
		}
		PlayerBotLogThrottled("pvpfan_squad", dwNow,
				"PVPFAN: squad category=%u squad=%d team=%s %s->%s alive=%d hp=%d spread=%ld near_foes=%d objective=%d why=%s",
				war.catId, sq.idx, war.teams[sq.team].name.c_str(), PvpFanSquadModeCode(sq.mode), PvpFanSquadModeCode(mode),
				sq.alive, sq.hpPct, sq.spread, sq.nearFoes, sq.objective, why);
		sq.mode = mode;
		sq.modeAt = dwNow;
	}

	// The formation's places, the living only (a fallen one's place closes), melee first.
	void ResetPlayerBotPvpFanSquadSlots(TPvpFanWar& war, TPvpFanSquad& sq)
	{
		std::vector<size_t> living;
		for (int role = PVPFAN_ROLE_MELEE; role <= PVPFAN_ROLE_SUPPORT; ++role)
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				const TPvpFanFighter& f = war.fighters[sq.members[j]];
				if (!f.dead && f.phase == PVPFAN_F_READY && f.role == role)
					living.push_back(sq.members[j]);
			}
		TPvpFanSquad tmp;
		tmp.members.swap(living);
		SetPlayerBotPvpFanSquadSlots(war, tmp);
	}

	// Once a second for the whole war: O(fighters + squads^2 + the grid's looks of the back lines).
	void DecidePlayerBotPvpFanSquads(TPvpFanWar& war, DWORD dwNow)
	{
		const int size = std::max(2, war.squadSize);
		// 1. each squad's state
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			TPvpFanSquad& sq = war.squads[q];
			if (sq.mode == PVPFAN_SQ_GONE)
				continue;
			long sx = 0, sy = 0;
			int alive = 0, hp = 0, engaged = 0, support = 0;
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				const TPvpFanFighter& f = war.fighters[sq.members[j]];
				if (f.dead || f.phase != PVPFAN_F_READY)
					continue;
				sx += f.lastX;
				sy += f.lastY;
				++alive;
				hp += f.hpPct;
				if (f.engaged)
					++engaged;
				if (f.role == PVPFAN_ROLE_SUPPORT)
					++support;
			}
			sq.alive = alive;
			if (alive == 0)
			{
				SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_GONE, dwNow, "wiped");
				continue;
			}
			sq.cx = sx / alive;
			sq.cy = sy / alive;
			sq.hpPct = hp / alive;
			sq.engagedN = engaged;
			sq.supportAlive = support;
			sq.nonSupportAlive = alive - support;
			long spread = 0;
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				const TPvpFanFighter& f = war.fighters[sq.members[j]];
				if (!f.dead && f.phase == PVPFAN_F_READY)
					spread += DISTANCE_APPROX(f.lastX - sq.cx, f.lastY - sq.cy);
			}
			sq.spread = spread / alive;
		}
		// 2. a remnant (a third of a squad or less) joins the nearest squad of its team that has room
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			TPvpFanSquad& sq = war.squads[q];
			if (sq.mode == PVPFAN_SQ_GONE || sq.alive > std::max(1, size / 3))
				continue;
			int best = -1;
			long bestD = 4000;
			for (size_t o = 0; o < war.squads.size(); ++o)
			{
				const TPvpFanSquad& other = war.squads[o];
				if (o == q || other.team != sq.team || other.mode == PVPFAN_SQ_GONE || other.alive + sq.alive > size + size / 2)
					continue;
				const long d = DISTANCE_APPROX(other.cx - sq.cx, other.cy - sq.cy);
				if (d < bestD)
				{
					bestD = d;
					best = (int)o;
				}
			}
			if (best < 0)
				continue;
			TPvpFanSquad& other = war.squads[best];
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				TPvpFanFighter& f = war.fighters[sq.members[j]];
				if (f.dead || f.phase != PVPFAN_F_READY)
					continue;
				f.squad = other.idx;
				other.members.push_back(sq.members[j]);
			}
			other.alive += sq.alive;
			++war.mergesTotal;
			PlayerBotLogThrottled("pvpfan_merge", dwNow, "PVPFAN: squad category=%u squad=%d (%d left) joins squad=%d team=%s",
					war.catId, sq.idx, sq.alive, other.idx, war.teams[sq.team].name.c_str());
			sq.alive = 0;
			SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_GONE, dwNow, "merged");
			sq.members.clear();
		}
		// 3. objectives: kept ones claim first, then the rest pick - the nearest enemy squad, one already claimed by
		// a squad of the same team counting PVPFAN_OBJECTIVE_CLAIM further each time, so the fronts spread
		std::vector<int> claims(war.squads.size(), 0);
		std::vector<char> pick(war.squads.size(), 0);
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			TPvpFanSquad& sq = war.squads[q];
			if (sq.mode == PVPFAN_SQ_GONE)
				continue;
			const bool valid = sq.objective >= 0 && sq.objective < (int)war.squads.size() &&
					war.squads[sq.objective].mode != PVPFAN_SQ_GONE && war.squads[sq.objective].alive > 0;
			if (valid && PvpFanSince(dwNow, sq.objectiveAt) < PVPFAN_OBJECTIVE_KEEP_MS)
				++claims[sq.objective];
			else
				pick[q] = 1;
		}
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			if (!pick[q])
				continue;
			TPvpFanSquad& sq = war.squads[q];
			int best = -1;
			long bestCost = LONG_MAX;
			for (size_t o = 0; o < war.squads.size(); ++o)
			{
				const TPvpFanSquad& e = war.squads[o];
				if (e.team == sq.team || e.mode == PVPFAN_SQ_GONE || e.alive <= 0)
					continue;
				long cost = DISTANCE_APPROX(e.cx - sq.cx, e.cy - sq.cy) + claims[o] * PVPFAN_OBJECTIVE_CLAIM +
						(long)(playerbot_war_rules::Mix((unsigned int)sq.idx + 1, (unsigned int)o + 1) % 300);
				if ((int)o == sq.objective)
					cost -= 600;
				if (e.hpPct < 50)
					cost -= 300;
				if (cost < bestCost)
				{
					bestCost = cost;
					best = (int)o;
				}
			}
			sq.objective = best;
			sq.objectiveAt = dwNow;
			if (best >= 0)
				++claims[best];
		}
		// 4. modes, rally points, the shared focus and the peel
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			TPvpFanSquad& sq = war.squads[q];
			if (sq.mode == PVPFAN_SQ_GONE)
				continue;
			ResetPlayerBotPvpFanSquadSlots(war, sq);
			const TPvpFanSquad* obj = sq.objective >= 0 ? &war.squads[sq.objective] : NULL;
			const long dObj = obj ? DISTANCE_APPROX(obj->cx - sq.cx, obj->cy - sq.cy) : LONG_MAX;
			const bool canMend = war.potions || sq.supportAlive > 0;
			sq.nearFoes = 0;
			ForEachPlayerBotPvpFanNear(war, sq.cx, sq.cy, PVPFAN_OUTNUMBER_RANGE, [&](int, TPvpFanFighter& e)
			{
				if (e.team != sq.team && e.phase == PVPFAN_F_READY)
					++sq.nearFoes;
			});
			const TPvpFanTeam& team = war.teams[sq.team];
			switch (sq.mode)
			{
				case PVPFAN_SQ_ADVANCE:
					if (obj && (dObj <= PVPFAN_ENGAGE_RANGE || sq.engagedN * 2 >= sq.alive))
						SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_ENGAGE, dwNow, "contact");
					break;
				case PVPFAN_SQ_ENGAGE:
				{
					if (!obj && sq.engagedN == 0)
					{
						SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_ADVANCE, dwNow, "no objective");
						break;
					}
					if (obj && dObj > PVPFAN_DISENGAGE_RANGE && sq.engagedN == 0)
					{
						SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_ADVANCE, dwNow, "pursuit");
						break;
					}
					if (PvpFanSince(dwNow, sq.engageAt) < PVPFAN_ENGAGE_MIN_MS || (int)(dwNow - sq.regroupCdUntil) < 0 ||
							war.teams[sq.team].alive <= 2)
						break;
					const char* why = canMend && sq.hpPct < PVPFAN_REGROUP_HP ? "hurt"
							: sq.spread > PVPFAN_REGROUP_SPREAD ? "scattered"
							: sq.nearFoes >= sq.alive * 2 + 1 ? "outnumbered" : NULL;
					if (!why)
						break;
					// back toward its side, never out of the arena
					const double hx = (double)(team.x - sq.cx), hy = (double)(team.y - sq.cy);
					const double hl = sqrt(hx * hx + hy * hy);
					const double back = std::min<double>(hl, PVPFAN_REGROUP_BACK);
					sq.rallyX = sq.cx + (hl >= 1.0 ? (long)(hx / hl * back) : 0);
					sq.rallyY = sq.cy + (hl >= 1.0 ? (long)(hy / hl * back) : 0);
					ClampPlayerBotPvpFanToArena(war, sq.rallyX, sq.rallyY, 850);
					long gx = sq.rallyX, gy = sq.rallyY;
					if (FindPlayerBotWarGround(war.map, sq.rallyX, sq.rallyY, 400, gx, gy))
					{
						sq.rallyX = gx;
						sq.rallyY = gy;
					}
					SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_REGROUP, dwNow, why);
					break;
				}
				case PVPFAN_SQ_REGROUP:
				{
					const DWORD since = PvpFanSince(dwNow, sq.modeAt);
					if (since >= PVPFAN_REGROUP_MAX_MS || (since >= PVPFAN_REGROUP_MIN_MS &&
							(!canMend || sq.hpPct >= PVPFAN_RETURN_HP) && sq.spread < 700))
						SetPlayerBotPvpFanSquadMode(war, sq, PVPFAN_SQ_ADVANCE, dwNow, "regrouped");
					break;
				}
				default:
					break;
			}
			// the rally point and the facing
			long goalX = obj ? obj->cx : war.cx, goalY = obj ? obj->cy : war.cy;
			if (sq.mode == PVPFAN_SQ_ADVANCE)
			{
				if (sq.flanker && obj && dObj > PVPFAN_FLANK_UNTIL)
				{
					// the outer squads swing out along their own side of the team's axis
					double ax = (double)(war.cx - team.x), ay = (double)(war.cy - team.y);
					const double al = std::max(1.0, sqrt(ax * ax + ay * ay));
					ax /= al;
					ay /= al;
					const double sign = sq.lane >= 0 ? 1.0 : -1.0;
					goalX += (long)(-ay * sign * PVPFAN_FLANK_OFFSET);
					goalY += (long)(ax * sign * PVPFAN_FLANK_OFFSET);
				}
				double dx = (double)(goalX - sq.cx), dy = (double)(goalY - sq.cy);
				const double len = sqrt(dx * dx + dy * dy);
				if (len >= 1.0)
				{
					sq.fwdX = dx / len;
					sq.fwdY = dy / len;
				}
				const double lead = std::min<double>(len, PVPFAN_ADVANCE_LEAD);
				sq.rallyX = sq.cx + (long)(sq.fwdX * lead);
				sq.rallyY = sq.cy + (long)(sq.fwdY * lead);
				ClampPlayerBotPvpFanToArena(war, sq.rallyX, sq.rallyY);
			}
			else
			{
				if (sq.mode == PVPFAN_SQ_ENGAGE)
				{
					sq.rallyX = sq.cx;
					sq.rallyY = sq.cy;
				}
				const double dx = (double)(goalX - sq.cx), dy = (double)(goalY - sq.cy);
				const double len = sqrt(dx * dx + dy * dy);
				if (len >= 1.0)
				{
					sq.fwdX = dx / len;
					sq.fwdY = dy / len;
				}
			}
			// the shared focus: the weakest of the objective near it, healers and casters first
			sq.focusPid = 0;
			if (obj && sq.mode != PVPFAN_SQ_REGROUP && dObj <= PVPFAN_ENGAGE_RANGE * 2)
			{
				long best = LONG_MAX;
				for (size_t j = 0; j < obj->members.size(); ++j)
				{
					const TPvpFanFighter& e = war.fighters[obj->members[j]];
					if (e.dead || e.phase != PVPFAN_F_READY)
						continue;
					const long score = (long)e.hpPct * 15 + DISTANCE_APPROX(e.lastX - sq.cx, e.lastY - sq.cy) -
							(e.role == PVPFAN_ROLE_SUPPORT ? 700 : e.role == PVPFAN_ROLE_RANGED ? 350 : 0);
					if (score < best)
					{
						best = score;
						sq.focusPid = e.pid;
					}
				}
			}
			// the peel: the nearest enemy blade at one of this squad's ranged or support
			sq.peelPid = 0;
			if (sq.alive > sq.supportAlive)
				for (size_t j = 0; j < sq.members.size() && !sq.peelPid; ++j)
				{
					const TPvpFanFighter& f = war.fighters[sq.members[j]];
					if (f.dead || f.phase != PVPFAN_F_READY || f.role == PVPFAN_ROLE_MELEE)
						continue;
					long bestD = LONG_MAX;
					ForEachPlayerBotPvpFanNear(war, f.lastX, f.lastY, PVPFAN_PEEL_RANGE, [&](int, TPvpFanFighter& e)
					{
						if (e.team == sq.team || e.phase != PVPFAN_F_READY || e.role != PVPFAN_ROLE_MELEE)
							return;
						const long d = DISTANCE_APPROX(e.lastX - f.lastX, e.lastY - f.lastY);
						if (d < bestD)
						{
							bestD = d;
							sq.peelPid = e.pid;
						}
					});
				}
		}
	}

	// ------------------------------------------------------------------ tactics: each bot

	// The squad's formation: its place from the rally point, the support further back while the squad has others.
	void MovePlayerBotPvpFanToSlot(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			const TPvpFanSquad& sq, DWORD dwNow)
	{
		const long back = f.slotBack + (f.role == PVPFAN_ROLE_SUPPORT && sq.nonSupportAlive > 0 ? PVPFAN_SUPPORT_BACK : 0);
		long tx = sq.rallyX + (long)(-sq.fwdY * f.slotSide - sq.fwdX * back);
		long ty = sq.rallyY + (long)(sq.fwdX * f.slotSide - sq.fwdY * back);
		ClampPlayerBotPvpFanToArena(war, tx, ty);
		const int d = DISTANCE_APPROX(ch->GetX() - tx, ch->GetY() - ty);
		if (d > 200)
		{
			if (dwNow >= state.dwNextGuildWarMoveTime)
			{
				state.dwNextGuildWarMoveTime = dwNow + 800;
				MovePlayerBot(ch, tx, ty, dwNow, 4, true, false);
			}
			return;
		}
		if (ch->IsStateMove() && d <= 120)
			ch->Stop();
		if (!ch->IsStateMove())
			ch->SetRotationToXY(sq.rallyX + (long)(sq.fwdX * 1000), sq.rallyY + (long)(sq.fwdY * 1000));
	}

	// The foe from the grid within radius: distance, the crowd on it (and the cap), the squad's focus, the peel and
	// the chase of casters for a melee bot, the guild war's role lists (playerbot_war_rules::FocusBonus, halved).
	LPCHARACTER FindPlayerBotPvpFanTacticsFoe(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch, const TPvpFanSquad& sq,
			long radius)
	{
		const playerbot_war_rules::ERole wrole = playerbot_war_rules::RoleOf(
				playerbot_war_rules::KindOf(f.job, f.group), playerbot_war_rules::PATTERN_CLASSIC, f.pid);
		long best = LONG_MAX;
		int bestI = -1;
		ForEachPlayerBotPvpFanNear(war, ch->GetX(), ch->GetY(), radius, [&](int i, TPvpFanFighter& e)
		{
			if (e.team == f.team || e.phase != PVPFAN_F_READY)
				return;
			long cost = DISTANCE_APPROX(e.lastX - ch->GetX(), e.lastY - ch->GetY());
			std::unordered_map<DWORD, int>::const_iterator c = war.crowd.find(e.pid);
			int crowd = c != war.crowd.end() ? c->second : 0;
			if (e.pid == f.targetPid && crowd > 0)
				--crowd;	// itself, and the keep of the foe in hand
			cost += crowd * PVPFAN_CROWD_PENALTY + (crowd >= PVPFAN_CROWD_CAP ? PVPFAN_CROWD_OVER : 0);
			if (e.pid == f.targetPid)
				cost -= 300;
			cost += (long)((e.pid ^ f.pid) % 97) * 3;
			if (e.pid == sq.focusPid)
				cost -= PVPFAN_FOCUS_BONUS;
			if (f.role == PVPFAN_ROLE_MELEE)
			{
				if (e.pid == sq.peelPid)
					cost -= PVPFAN_PEEL_BONUS;
				if (e.role != PVPFAN_ROLE_MELEE)
					cost -= PVPFAN_CHASE_CASTER_BONUS;
			}
			cost -= playerbot_war_rules::FocusBonus(wrole, playerbot_war_rules::PATTERN_CLASSIC,
					playerbot_war_rules::KindOf(e.job, e.group)) / 2;
			if (cost < best)
			{
				best = cost;
				bestI = i;
			}
		});
		if (bestI < 0)
			return NULL;
		const TPvpFanFighter& e = war.fighters[bestI];
		if (f.role == PVPFAN_ROLE_MELEE && e.pid == sq.peelPid && e.pid != f.targetPid)
			++war.peelsMin;
		LPCHARACTER foe = CHARACTER_MANAGER::instance().FindByPID(e.pid);
		return foe && !foe->IsDead() && foe->GetMapIndex() == ch->GetMapIndex() ? foe : NULL;
	}

	// Wounded under retreat_hp: to its squad's healer, else back toward its side; potions on the way (when the
	// category allows them); back at PVPFAN_RETURN_HP or after PVPFAN_RETREAT_MAX_MS. Only where it can mend - potions
	// or a healer of its squad - and never the last two of a team (that is no retreat, that is the end).
	bool RetreatPlayerBotPvpFan(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			const TPvpFanSquad& sq, DWORD dwNow)
	{
		const int pct = ch->GetMaxHP() > 0 ? (int)((long long)MAX(0, ch->GetHP()) * 100 / ch->GetMaxHP()) : 100;
		if (!f.retreating)
		{
			if (war.retreatHp <= 0 || pct >= war.retreatHp || (int)(dwNow - f.retreatCdUntil) < 0 ||
					!(war.potions || sq.supportAlive > (f.role == PVPFAN_ROLE_SUPPORT ? 1 : 0)) ||
					war.teams[f.team].alive <= 2)
				return false;
			f.retreating = true;
			f.retreatUntil = dwNow + PVPFAN_RETREAT_MAX_MS;
			const TPvpFanTeam& team = war.teams[f.team];
			const double hx = (double)(team.x - ch->GetX()), hy = (double)(team.y - ch->GetY());
			const double hl = sqrt(hx * hx + hy * hy);
			const double back = std::min<double>(hl, PVPFAN_RETREAT_STEP * 3 / 2);
			f.retreatX = ch->GetX() + (hl >= 1.0 ? (long)(hx / hl * back) : 0);
			f.retreatY = ch->GetY() + (hl >= 1.0 ? (long)(hy / hl * back) : 0);
			ClampPlayerBotPvpFanToArena(war, f.retreatX, f.retreatY, 850);
			++war.retreatsMin;
			++war.retreatsTotal;
			PlayerBotLogThrottled("pvpfan_retreat", dwNow, "PVPFAN: retreat category=%u pid=%u name=%s team=%s hp=%d squad=%d "
					"healer=%d potions=%d", war.catId, f.pid, ch->GetName(), war.teams[f.team].name.c_str(), pct, f.squad,
					sq.supportAlive, war.potions ? 1 : 0);
		}
		if (pct >= PVPFAN_RETURN_HP || (int)(dwNow - f.retreatUntil) >= 0)
		{
			f.retreating = false;
			f.retreatCdUntil = dwNow + PVPFAN_RETREAT_COOLDOWN_MS;
			return false;
		}
		if (war.potions)
			UseHealthPotion(ch, state, dwNow, 90);
		long tx = f.retreatX, ty = f.retreatY;
		if (f.role != PVPFAN_ROLE_SUPPORT)
			for (size_t j = 0; j < sq.members.size(); ++j)
			{
				const TPvpFanFighter& h = war.fighters[sq.members[j]];
				if (h.role == PVPFAN_ROLE_SUPPORT && !h.dead && h.phase == PVPFAN_F_READY && !h.retreating)
				{
					tx = h.lastX;
					ty = h.lastY;
					break;
				}
			}
		if (DISTANCE_APPROX(ch->GetX() - tx, ch->GetY() - ty) > 200)
		{
			state.dwTargetVID = 0;
			f.targetPid = 0;
			f.engaged = false;
			if (ch->GetVictim())
				ch->SetVictim(NULL);
			if (dwNow >= state.dwNextGuildWarMoveTime)
			{
				state.dwNextGuildWarMoveTime = dwNow + 800;
				MovePlayerBot(ch, tx, ty, dwNow, 4, true, false);
			}
			return true;
		}
		// There: it mends, and strikes back at what comes at it.
		LPCHARACTER foe = FindPlayerBotPvpFanTacticsFoe(war, f, ch, sq, 300);
		if (foe)
		{
			StrikePlayerBotPvpFanFoe(ch, state, war, f, foe, dwNow, f.role != PVPFAN_ROLE_MELEE);
			return true;
		}
		state.dwTargetVID = 0;
		f.targetPid = 0;
		if (ch->IsStateMove())
			ch->Stop();
		return true;
	}

	// A shaman's part for its squad: the healer cures the lowest under PVPFAN_HEAL_HP, both paths put their buffs on
	// the squad (CastPlayerBotSupportBuff, the guild war's and the party's). Its own squad only - O(squad).
	bool SupportPlayerBotPvpFanSquad(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			const TPvpFanSquad& sq, DWORD dwNow)
	{
		if (ch->GetJob() != JOB_SHAMAN || ch->GetSkillGroup() == 0 || (int)(dwNow - f.supportLookAt) < 0)
			return false;
		f.supportLookAt = dwNow + PVPFAN_SUPPORT_LOOK_MS + f.pid % 300;
		std::vector<LPCHARACTER> mates;
		LPCHARACTER low = NULL;
		int lowPct = PVPFAN_HEAL_HP + 1;
		for (size_t j = 0; j < sq.members.size(); ++j)
		{
			const TPvpFanFighter& e = war.fighters[sq.members[j]];
			if (e.dead || e.phase != PVPFAN_F_READY)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(e.pid);
			if (!c || c->IsDead() || c->GetMapIndex() != ch->GetMapIndex() || c->GetMaxHP() <= 0 ||
					DISTANCE_APPROX(c->GetX() - ch->GetX(), c->GetY() - ch->GetY()) > PVPFAN_SUPPORT_REACH)
				continue;
			mates.push_back(c);
			const int pct = (int)((long long)MAX(0, c->GetHP()) * 100 / c->GetMaxHP());
			if (pct < lowPct)
			{
				lowPct = pct;
				low = c;
			}
		}
		if (f.role == PVPFAN_ROLE_SUPPORT && low && ch->GetSkillLevel(109) > 0 &&
				CanPlayerBotAffordSkill(ch, state, 109, dwNow) && PlayerBotUseSkill(ch, state, 109, low, dwNow))
		{
			SendPlayerBotSkillPacket(ch, 109);
			state.dwLastBotSkillTime = dwNow;
			state.dwNextAttackTime = dwNow + PLAYERBOT_SKILL_ANIMATION_LOCK;
			++war.healsMin;
			++war.healsTotal;
			PlayerBotLogThrottled("pvpfan_heal", dwNow, "PVPFAN: healed category=%u pid=%u name=%s fellow=%s hp_pct=%d",
					war.catId, f.pid, ch->GetName(), low->GetName(), lowPct);
			return true;
		}
		if (mates.empty())
			return false;
		std::sort(mates.begin(), mates.end(), [ch](LPCHARACTER a, LPCHARACTER b)
		{
			return DISTANCE_APPROX(ch->GetX() - a->GetX(), ch->GetY() - a->GetY()) <
					DISTANCE_APPROX(ch->GetX() - b->GetX(), ch->GetY() - b->GetY());
		});
		LPCHARACTER target = NULL;
		DWORD vnum = 0;
		return CastPlayerBotSupportBuff(ch, state, dwNow, mates, true, "pvpfan", target, vnum) != 0;
	}

	// A ranged or support bot with a melee foe within kite_distance: a step away - sideways a little (so it circles
	// rather than runs in a line), toward its squad when the squad is not behind the threat, along the edge where the
	// arena ends. PVPFAN_KITE_MAX in a PVPFAN_KITE_WINDOW_MS, then it stands and fights: kiting moves the fight, it
	// does not stop it.
	bool KitePlayerBotPvpFan(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			const TPvpFanSquad& sq, DWORD dwNow)
	{
		if (war.kiteDist <= 0 || f.role == PVPFAN_ROLE_MELEE || (int)(dwNow - f.threatLookAt) < 0)
			return false;
		f.threatLookAt = dwNow + PVPFAN_THREAT_LOOK_MS + f.pid % 100;
		if (PvpFanSince(dwNow, f.kiteWindowAt) > PVPFAN_KITE_WINDOW_MS)
		{
			f.kiteWindowAt = dwNow;
			f.kiteCount = 0;
		}
		if (f.kiteCount >= PVPFAN_KITE_MAX)
			return false;
		int best = -1;
		long bestD = LONG_MAX;
		ForEachPlayerBotPvpFanNear(war, ch->GetX(), ch->GetY(), war.kiteDist + 150, [&](int i, TPvpFanFighter& e)
		{
			if (e.team == f.team || e.phase != PVPFAN_F_READY || e.role != PVPFAN_ROLE_MELEE)
				return;
			const long d = DISTANCE_APPROX(e.lastX - ch->GetX(), e.lastY - ch->GetY());
			if (d < bestD)
			{
				bestD = d;
				best = i;
			}
		});
		if (best < 0)
			return false;
		LPCHARACTER threat = CHARACTER_MANAGER::instance().FindByPID(war.fighters[best].pid);
		if (!threat || threat->IsDead() ||
				DISTANCE_APPROX(threat->GetX() - ch->GetX(), threat->GetY() - ch->GetY()) > war.kiteDist)
			return false;
		double ax = (double)(ch->GetX() - threat->GetX()), ay = (double)(ch->GetY() - threat->GetY());
		double al = sqrt(ax * ax + ay * ay);
		if (al < 1.0)
		{
			ax = (double)(sq.cx - threat->GetX());
			ay = (double)(sq.cy - threat->GetY());
			al = std::max(1.0, sqrt(ax * ax + ay * ay));
		}
		ax /= al;
		ay /= al;
		const double side = ((f.pid + f.kiteCount) & 1) ? 0.55 : -0.55;
		double dx = ax - ay * side, dy = ay + ax * side;
		const long dSq = DISTANCE_APPROX(sq.cx - ch->GetX(), sq.cy - ch->GetY());
		if (dSq > 500)
		{
			double sx = (double)(sq.cx - ch->GetX()), sy = (double)(sq.cy - ch->GetY());
			const double sl = std::max(1.0, sqrt(sx * sx + sy * sy));
			sx /= sl;
			sy /= sl;
			if (sx * ax + sy * ay > -0.3)
			{
				dx += sx * 0.6;
				dy += sy * 0.6;
			}
		}
		double dl = std::max(1e-6, sqrt(dx * dx + dy * dy));
		dx /= dl;
		dy /= dl;
		long tx = ch->GetX() + (long)(dx * PVPFAN_KITE_STEP), ty = ch->GetY() + (long)(dy * PVPFAN_KITE_STEP);
		if (DISTANCE_APPROX(tx - war.cx, ty - war.cy) > war.arenaRadius * 9 / 10)
		{
			// along the edge, the way that is away from the threat, and a little inward
			double rx = (double)(ch->GetX() - war.cx), ry = (double)(ch->GetY() - war.cy);
			const double rl = std::max(1.0, sqrt(rx * rx + ry * ry));
			rx /= rl;
			ry /= rl;
			double txd = -ry, tyd = rx;
			if (txd * ax + tyd * ay < 0)
			{
				txd = -txd;
				tyd = -tyd;
			}
			tx = ch->GetX() + (long)((txd - rx * 0.3) * PVPFAN_KITE_STEP);
			ty = ch->GetY() + (long)((tyd - ry * 0.3) * PVPFAN_KITE_STEP);
		}
		ClampPlayerBotPvpFanToArena(war, tx, ty);
		long gx = tx, gy = ty;
		if (!FindPlayerBotWarGround(war.map, tx, ty, 300, gx, gy) ||
				DISTANCE_APPROX(gx - ch->GetX(), gy - ch->GetY()) < PVPFAN_KITE_STEP / 3)
			return false;
		++f.kiteCount;
		++war.kitesMin;
		++war.kitesTotal;
		f.kiteMoveUntil = dwNow + 650;
		state.dwNextGuildWarMoveTime = dwNow + 650;
		MovePlayerBot(ch, gx, gy, dwNow, 4, false, false);
		PlayerBotLogThrottled("pvpfan_kite", dwNow, "PVPFAN: kite category=%u pid=%u name=%s from=%s dist=%d kites=%d",
				war.catId, f.pid, ch->GetName(), threat->GetName(),
				DISTANCE_APPROX(threat->GetX() - ch->GetX(), threat->GetY() - ch->GetY()), f.kiteCount);
		return true;
	}

	// MT2009_PLUS_PVPFAN_TACTICS_V1: a bot's tick in the fight with tactics on (riding, potions and the arena's leash
	// are done by the caller).
	void FightPlayerBotPvpFanTactics(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			DWORD dwNow)
	{
		const TPvpFanSquad& sq = war.squads[f.squad];
		// a kite's step is not cut short by the next blow
		if ((int)(dwNow - f.kiteMoveUntil) < 0)
			return;
		if (RetreatPlayerBotPvpFan(ch, state, war, f, sq, dwNow))
			return;
		if (SupportPlayerBotPvpFanSquad(ch, state, war, f, sq, dwNow))
			return;
		const bool regroup = sq.mode == PVPFAN_SQ_REGROUP;
		const long radius = regroup ? 350
				: sq.mode == PVPFAN_SQ_ENGAGE ? PVPFAN_SEARCH_RADIUS
				: f.role == PVPFAN_ROLE_MELEE ? PVPFAN_CONTACT_MELEE : PVPFAN_BOW_HOLD + 300;
		LPCHARACTER foe = NULL;
		if (state.dwTargetVID != 0)
		{
			LPCHARACTER held = CHARACTER_MANAGER::instance().Find(state.dwTargetVID);
			if (IsPlayerBotPvpFanFoeUp(war, f, ch, held) &&
					DISTANCE_APPROX(held->GetX() - ch->GetX(), held->GetY() - ch->GetY()) <= radius * 3 / 2)
				foe = held;
		}
		// a bot with nobody in reach looks again every PVPFAN_THREAT_LOOK_MS, not every tick
		if ((int)(dwNow - f.retargetAt) >= 0 || (!foe && (int)(dwNow - f.foeLookAt) >= 0))
		{
			f.retargetAt = dwNow + PVPFAN_RETARGET_MS + f.pid % 700;
			f.foeLookAt = dwNow + PVPFAN_THREAT_LOOK_MS + f.pid % 150;
			LPCHARACTER chosen = FindPlayerBotPvpFanTacticsFoe(war, f, ch, sq, radius);
			if (chosen)
				foe = chosen;
		}
		if (!foe)
		{
			f.engaged = false;
			state.dwTargetVID = 0;
			f.targetPid = 0;
			if (ch->GetVictim())
				ch->SetVictim(NULL);
			// the skirmish goes on where the objective stands
			if (sq.mode == PVPFAN_SQ_ENGAGE && sq.objective >= 0)
			{
				const TPvpFanSquad& o = war.squads[sq.objective];
				if (DISTANCE_APPROX(ch->GetX() - o.cx, ch->GetY() - o.cy) > 300)
				{
					if (dwNow >= state.dwNextGuildWarMoveTime)
					{
						state.dwNextGuildWarMoveTime = dwNow + 800;
						long tx = o.cx, ty = o.cy;
						ClampPlayerBotPvpFanToArena(war, tx, ty);
						MovePlayerBot(ch, tx, ty, dwNow, 4, true, false);
					}
					return;
				}
			}
			MovePlayerBotPvpFanToSlot(ch, state, war, f, sq, dwNow);
			return;
		}
		f.engaged = true;
		if (KitePlayerBotPvpFan(ch, state, war, f, sq, dwNow))
			return;
		StrikePlayerBotPvpFanFoe(ch, state, war, f, foe, dwNow, f.role != PVPFAN_ROLE_MELEE);
	}

	// ------------------------------------------------------------------ the fight (the guild war's)
	// MT2009_PLUS_PVPFAN_WARSTYLE_V1 - the owner, 10 November 2026, after watching the squads: "it lags and jumps -
	// three steps, stop, three steps, a skill, stop; it must fight like normal bot PvP or a guild war: attack skills in
	// a random way, random enemies, not assigned ones, and they spread out naturally". The default fight of every
	// category (pvpfan_category.tactics 0 or 1; the squads only with 2, "eksperymentalne"):
	//   the foe   - drawn at random from the enemies within PVPFAN_PICK_RADIUS (the spatial grid, never the whole war),
	//               a near one far likelier (1 / (1 + d / PVPFAN_PICK_FALLOFF)^2) and one many already fight a little
	//               less likely (/ (1 + crowd / PVPFAN_PICK_CROWD)); kept until it falls, gets away (further than
	//               PVPFAN_KEEP_RANGE or out of the arena) or 8-15 s pass, then another is drawn. Nobody near: the
	//               nearest enemy anywhere (looked for every PVPFAN_LOOK_FAR_MS), else the arena's centre;
	//   the blow  - the guild war's (StrikePlayerBotPvpFanFoe): buffs, a caster's spell from 600, a warrior's gap
	//               closer, the bow from 800, the blade in reach; the due attack skills in a random order
	//               (CastPlayerBotPvpFanSkill); one continuous chase (a new goal only when the foe has moved);
	//   the bow   - steps back from a foe nearer than PLAYERBOT_GUILD_WAR_ARCHER_KEEP_AWAY, at most
	//               PLAYERBOT_GUILD_WAR_ARCHER_STEPS_MAX in PLAYERBOT_GUILD_WAR_ARCHER_STEP_WINDOW_MS, as at a guild war;
	//   the dagger- goes in unseen (the guild war's Stealth);
	//   shamans   - every 1.5-2.5 s a look at their mates within reach (the grid): the healer cures the lowest under
	//               PVPFAN_HEAL_HP, both paths put a buff on a mate; otherwise they fight like anybody else.
	// The spread comes from the random foes and the arena; nothing assigns, gathers or holds a bot anywhere.
	// The fighters' tick is their own pass (TickPlayerBotPvpFanBots, every bot-manager tick), not the population's
	// budgeted sweep - that sweep reached them once in ~2 s on a busy core, the stutter's cause.

	// The draw: one of the enemies within radius of the bot, weighted; NULL when nobody stands there.
	LPCHARACTER DrawPlayerBotPvpFanFoe(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch, long radius)
	{
		std::vector<std::pair<int, double> > pool;
		double sum = 0.0;
		ForEachPlayerBotPvpFanNear(war, ch->GetX(), ch->GetY(), radius, [&](int i, TPvpFanFighter& e)
		{
			if (e.team == f.team || e.phase != PVPFAN_F_READY)
				return;
			const double d = (double)DISTANCE_APPROX(e.lastX - ch->GetX(), e.lastY - ch->GetY());
			std::unordered_map<DWORD, int>::const_iterator c = war.crowd.find(e.pid);
			const int crowd = c != war.crowd.end() ? c->second : 0;
			const double near = 1.0 + d / (double)PVPFAN_PICK_FALLOFF;
			const double w = 1.0 / (near * near) / (1.0 + (double)crowd / (double)PVPFAN_PICK_CROWD);
			pool.push_back(std::make_pair(i, w));
			sum += w;
		});
		while (!pool.empty() && sum > 0.0)
		{
			double r = (double)number(0, 999999) / 1000000.0 * sum;
			size_t k = 0;
			for (; k + 1 < pool.size(); ++k)
			{
				r -= pool[k].second;
				if (r < 0.0)
					break;
			}
			LPCHARACTER foe = CHARACTER_MANAGER::instance().FindByPID(war.fighters[pool[k].first].pid);
			if (IsPlayerBotPvpFanFoeUp(war, f, ch, foe))
				return foe;
			sum -= pool[k].second;
			pool.erase(pool.begin() + k);
		}
		return NULL;
	}

	// The nearest enemy anywhere in the arena (the grid over its whole reach) - for a bot with nobody near.
	LPCHARACTER FindPlayerBotPvpFanNearestFoe(TPvpFanWar& war, TPvpFanFighter& f, LPCHARACTER ch)
	{
		long best = LONG_MAX;
		int bestI = -1;
		ForEachPlayerBotPvpFanNear(war, ch->GetX(), ch->GetY(), war.arenaRadius * 5 / 2, [&](int i, TPvpFanFighter& e)
		{
			if (e.team == f.team || e.phase != PVPFAN_F_READY)
				return;
			const long d = DISTANCE_APPROX(e.lastX - ch->GetX(), e.lastY - ch->GetY());
			if (d < best)
			{
				best = d;
				bestI = i;
			}
		});
		if (bestI < 0)
			return NULL;
		LPCHARACTER foe = CHARACTER_MANAGER::instance().FindByPID(war.fighters[bestI].pid);
		return IsPlayerBotPvpFanFoeUp(war, f, ch, foe) ? foe : NULL;
	}

	// A shaman now and then: the healer cures the lowest mate in reach under PVPFAN_HEAL_HP, both paths buff a mate
	// (CastPlayerBotSupportBuff, the guild war's and the party's). The mates from the grid - O(the cells near it).
	bool SupportPlayerBotPvpFanMates(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			DWORD dwNow, bool heal)
	{
		if (ch->GetJob() != JOB_SHAMAN || ch->GetSkillGroup() == 0 || (int)(dwNow - f.supportLookAt) < 0)
			return false;
		f.supportLookAt = dwNow + (DWORD)number((int)PVPFAN_SUPPORT_MIN_MS, (int)PVPFAN_SUPPORT_MAX_MS);
		std::vector<LPCHARACTER> mates;
		LPCHARACTER low = NULL;
		int lowPct = PVPFAN_HEAL_HP + 1;
		ForEachPlayerBotPvpFanNear(war, ch->GetX(), ch->GetY(), PVPFAN_SUPPORT_REACH, [&](int, TPvpFanFighter& e)
		{
			if (e.team != f.team || e.phase != PVPFAN_F_READY || mates.size() >= 16)
				return;
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(e.pid);
			if (!c || c->IsDead() || c->GetMapIndex() != ch->GetMapIndex() || c->GetMaxHP() <= 0)
				return;
			mates.push_back(c);
			const int pct = (int)((long long)MAX(0, c->GetHP()) * 100 / c->GetMaxHP());
			if (pct < lowPct)
			{
				lowPct = pct;
				low = c;
			}
		});
		if (heal && low && playerbot_war_rules::KindOf(ch->GetJob(), ch->GetSkillGroup()) ==
				playerbot_war_rules::KIND_SHAMAN_HEAL && ch->GetSkillLevel(109) > 0 &&
				CanPlayerBotAffordSkill(ch, state, 109, dwNow) && PlayerBotUseSkill(ch, state, 109, low, dwNow))
		{
			SendPlayerBotSkillPacket(ch, 109);
			state.dwLastBotSkillTime = dwNow;
			state.dwNextAttackTime = dwNow + PLAYERBOT_SKILL_ANIMATION_LOCK;
			++war.healsMin;
			++war.healsTotal;
			PlayerBotLogThrottled("pvpfan_heal", dwNow, "PVPFAN: healed category=%u pid=%u name=%s fellow=%s hp_pct=%d",
					war.catId, f.pid, ch->GetName(), low->GetName(), lowPct);
			return true;
		}
		if (mates.empty())
			return false;
		std::sort(mates.begin(), mates.end(), [ch](LPCHARACTER a, LPCHARACTER b)
		{
			return DISTANCE_APPROX(ch->GetX() - a->GetX(), ch->GetY() - a->GetY()) <
					DISTANCE_APPROX(ch->GetX() - b->GetX(), ch->GetY() - b->GetY());
		});
		LPCHARACTER target = NULL;
		DWORD vnum = 0;
		return CastPlayerBotSupportBuff(ch, state, dwNow, mates, true, "pvpfan", target, vnum) != 0;
	}

	// The bow's step back, as at a guild war (StepPlayerBotWarArcherBack, without its camps): away from the foe that
	// came too close, toward the arena's centre when it stands on the archer, inside the arena, a few in a while.
	bool StepPlayerBotPvpFanArcherBack(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			LPCHARACTER foe, DWORD dwNow)
	{
		if (PvpFanSince(dwNow, f.stepWindowAt) > PLAYERBOT_GUILD_WAR_ARCHER_STEP_WINDOW_MS)
		{
			f.stepWindowAt = dwNow;
			f.steps = 0;
		}
		if (f.steps >= PLAYERBOT_GUILD_WAR_ARCHER_STEPS_MAX || (int)(dwNow - state.dwNextGuildWarMoveTime) < 0)
			return false;
		long toX = 0, toY = 0;
		playerbot_war_rules::StepAway(ch->GetX(), ch->GetY(), foe->GetX(), foe->GetY(), war.cx, war.cy,
				PLAYERBOT_GUILD_WAR_ARCHER_STEP, toX, toY);
		ClampPlayerBotPvpFanToArena(war, toX, toY);
		if (DISTANCE_APPROX(toX - ch->GetX(), toY - ch->GetY()) < PLAYERBOT_GUILD_WAR_ARCHER_STEP / 3)
			return false;
		long spotX = toX, spotY = toY;
		if (!FindPlayerBotWarGround(war.map, toX, toY, 300, spotX, spotY) ||
				DISTANCE_APPROX(spotX - ch->GetX(), spotY - ch->GetY()) < PLAYERBOT_GUILD_WAR_ARCHER_STEP / 3)
			return false;
		++f.steps;
		++war.stepsMin;
		state.dwNextGuildWarMoveTime = dwNow + 700;
		f.chaseAt = dwNow;
		MovePlayerBot(ch, spotX, spotY, dwNow, 4, false, false);
		return true;
	}

	void DropPlayerBotPvpFanFoe(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanFighter& f)
	{
		state.dwTargetVID = 0;
		f.targetPid = 0;
		if (ch->GetVictim())
			ch->SetVictim(NULL);
	}

	// A bot's tick in the default fight (riding, potions and the arena's leash are done by the caller).
	void FightPlayerBotPvpFanWarStyle(LPCHARACTER ch, TPlayerBotAIState& state, TPvpFanWar& war, TPvpFanFighter& f,
			DWORD dwNow)
	{
		const playerbot_war_rules::EKind kind = playerbot_war_rules::KindOf(f.job, f.group);
		if (SupportPlayerBotPvpFanMates(ch, state, war, f, dwNow, true))
			return;
		// The foe in hand, while it stands, is near enough, inside the arena and its keep has not run out.
		LPCHARACTER foe = NULL;
		if (f.targetPid != 0)
		{
			LPCHARACTER held = CHARACTER_MANAGER::instance().FindByPID(f.targetPid);
			if (!IsPlayerBotPvpFanFoeUp(war, f, ch, held))
				++war.endDeadMin;
			else if (DISTANCE_APPROX(held->GetX() - ch->GetX(), held->GetY() - ch->GetY()) > PVPFAN_KEEP_RANGE ||
					DISTANCE_APPROX(held->GetX() - war.cx, held->GetY() - war.cy) > war.arenaRadius)
				++war.endFledMin;
			else if ((int)(dwNow - f.keepUntil) >= 0)
				++war.endTimeMin;
			else
				foe = held;
			if (!foe)
			{
				DropPlayerBotPvpFanFoe(ch, state, f);
				f.foeLookAt = dwNow;
			}
		}
		if (!foe && (int)(dwNow - f.foeLookAt) >= 0)
		{
			f.foeLookAt = dwNow + PVPFAN_LOOK_MS + f.pid % 200;
			foe = DrawPlayerBotPvpFanFoe(war, f, ch, PVPFAN_PICK_RADIUS);
			if (!foe && (int)(dwNow - f.lookFarAt) >= 0)
			{
				f.lookFarAt = dwNow + PVPFAN_LOOK_FAR_MS + f.pid % 500;
				foe = FindPlayerBotPvpFanNearestFoe(war, f, ch);
			}
			if (foe)
			{
				f.keepUntil = dwNow + (DWORD)number((int)PVPFAN_KEEP_MIN_MS, (int)PVPFAN_KEEP_MAX_MS);
				f.targetPid = foe->GetPlayerID();
				f.chaseAt = dwNow - PVPFAN_CHASE_MS;	// the chase's first goal at once (never 0: see PvpFanSince)
				++war.picksMin;
				++war.picksTotal;
				// the crowd counts it at once, not at the next evaluation: the next draw of a mate sees it
				++war.crowd[f.targetPid];
			}
		}
		if (!foe)
		{
			DropPlayerBotPvpFanFoe(ch, state, f);
			// nobody near: toward the middle, where the fight is
			if (DISTANCE_APPROX(ch->GetX() - war.cx, ch->GetY() - war.cy) > 600)
			{
				if (!ch->IsStateMove() && PvpFanSince(dwNow, f.chaseAt) >= 1000)
				{
					f.chaseAt = dwNow;
					MovePlayerBot(ch, war.cx, war.cy, dwNow, 8, true, false);
				}
			}
			else if (ch->IsStateMove())
				ch->Stop();
			return;
		}
		const int distance = DISTANCE_APPROX(ch->GetX() - foe->GetX(), ch->GetY() - foe->GetY());
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		const bool isBow = weapon && weapon->GetType() == ITEM_WEAPON && weapon->GetSubType() == WEAPON_BOW;
		if (kind == playerbot_war_rules::KIND_NINJA_DAGGER && distance > PLAYERBOT_GUILD_WAR_ASSASSIN_STEALTH_RANGE &&
				TryPlayerBotWarStealth(ch, state, dwNow))
			return;
		if (isBow && distance < PLAYERBOT_GUILD_WAR_ARCHER_KEEP_AWAY &&
				StepPlayerBotPvpFanArcherBack(ch, state, war, f, foe, dwNow))
			return;
		// an archer's step is walked to its end, then it shoots
		if (isBow && ch->IsStateMove() && (int)(dwNow - state.dwNextGuildWarMoveTime) < 0 && distance <= 800)
			return;
		StrikePlayerBotPvpFanFoe(ch, state, war, f, foe, dwNow, false);
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
			f.engaged = false;
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
		// MT2009_PLUS_PVPFAN_TACTICS_V1: the experimental squads (pvpfan_category.tactics = 2, unless
		// m2_pvpfan_tactics_off); every other war fights the guild war's way (MT2009_PLUS_PVPFAN_WARSTYLE_V1).
		if (war.tacticsOn && f.squad >= 0 && f.squad < (int)war.squads.size())
		{
			FightPlayerBotPvpFanTactics(ch, state, war, f, dwNow);
			return;
		}
		FightPlayerBotPvpFanWarStyle(ch, state, war, f, dwNow);
	}

	// Every tick of a bot of a war on this core - the whole of it: nothing of the population's AI runs for it.
	// MT2009_PLUS_PVPFAN_WARSTYLE_V1: called from the fighters' own pass (TickPlayerBotPvpFanBots), every bot-manager
	// tick; the population's sweep only leaves them alone (ManagePlayerBotPvpFanBot).
	bool TickPlayerBotPvpFanBot(LPDESC d, LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
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
			f->supportLookAt = dwNow;	// MT2009_PLUS_PVPFAN_TACTICS_V1: the squad's buffs on the spot
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
				// MT2009_PLUS_PVPFAN_TACTICS_V1: a shaman buffs its squad on its spot, as a guild war's camp does
				// (MT2009_PLUS_PVPFAN_WARSTYLE_V1: its mates near it, from the grid, outside the squads).
				if (war->state != PVPFAN_STARTING && DISTANCE_APPROX(ch->GetX() - f->x, ch->GetY() - f->y) <= 400 &&
						(war->tacticsOn && f->squad >= 0 && f->squad < (int)war->squads.size()
							? SupportPlayerBotPvpFanSquad(ch, state, *war, *f, war->squads[f->squad], dwNow)
							: SupportPlayerBotPvpFanMates(ch, state, *war, *f, dwNow, false)))
					break;
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

	// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the population's sweep (CPlayerBotManager::Update) runs inside a time budget and
	// on a busy core reaches a bot once in several of its passes - on the test core with ~1200 bots 225 of 256 passes
	// a minute ran out of it, a sweep took ~2 s - and a war's bots were left out of the light tick in between, so each
	// moved, struck or cast once in ~2 s: "three steps, stop, three steps, a skill, stop". The sweep now only leaves
	// them alone; their tick is TickPlayerBotPvpFanBots below, every bot-manager tick.
	bool ManagePlayerBotPvpFanBot(LPDESC d, LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		(void)d;
		(void)state;
		(void)dwNow;
		return !s_mapPvpFanPid.empty() && ch && IsPlayerBotPvpFanPID(ch->GetPlayerID());
	}

	// Every fighter of every war on this core that is in the game, each bot-manager tick (~240 ms, at most every
	// PVPFAN_BOT_TICK_MIN_MS). In the fight the gap between two ticks of one bot is counted for the census.
	void TickPlayerBotPvpFanBots(DWORD dwNow)
	{
		static DWORD s_dwLast = 0;
		if (s_mapPvpFanWars.empty() || (s_dwLast && PvpFanSince(dwNow, s_dwLast) < PVPFAN_BOT_TICK_MIN_MS))
			return;
		s_dwLast = dwNow;
		for (std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.begin(); it != s_mapPvpFanWars.end(); ++it)
		{
			TPvpFanWar& war = it->second;
			for (size_t i = 0; i < war.fighters.size(); ++i)
			{
				TPvpFanFighter& f = war.fighters[i];
				if (f.phase != PVPFAN_F_LOADED && f.phase != PVPFAN_F_READY)
					continue;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(f.pid);
				if (!ch)
					continue;
				TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(f.pid);
				if (st == s_mapPlayerBotAIStates.end())
					continue;
				if (war.state == PVPFAN_FIGHTING && !f.dead && f.phase == PVPFAN_F_READY)
				{
					if (f.tickAt)
					{
						const DWORD gap = PvpFanSince(dwNow, f.tickAt);
						war.gapSumMs += gap;
						++war.gapN;
						war.gapMaxMs = std::max(war.gapMaxMs, (unsigned int)gap);
						if (gap > 600)
							++war.gapOver600;
					}
					f.tickAt = dwNow;
				}
				TickPlayerBotPvpFanBot(ch->GetDesc(), ch, st->second, dwNow);
			}
		}
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
		// MT2009_PLUS_PVPFAN_TACTICS_V1: what the war's tactics did, in one line.
		if (war.tactics && !war.squads.empty())
		{
			for (size_t q = 0; q < war.squads.size(); ++q)
				EndPlayerBotPvpFanEngagement(war, war.squads[q], dwNow);
			sys_log(0, "PVPFAN: tactics summary category=%u code=%s war=%u on=%d secs=%u squads=%u kites=%u retreats=%u "
					"regroups=%u heals=%u merges=%u skirmishes=%u skirmish_avg_s=%.1f", war.catId, war.code.c_str(),
					war.warRowId, war.tacticsOn ? 1 : 0, secs, (unsigned int)war.squads.size(), war.kitesTotal,
					war.retreatsTotal, war.regroupsTotal, war.healsTotal, war.mergesTotal, war.engEndsTotal,
					war.engEndsTotal ? war.engMsTotal / 1000.0 / war.engEndsTotal : 0.0);
		}
		else
			// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the default fight's summary (the last minute's tick gaps)
			sys_log(0, "PVPFAN: fight summary category=%u code=%s war=%u style=guild-war secs=%u picks=%u heals=%u "
					"tick_gap_avg_ms=%llu tick_gap_max_ms=%u tick_gaps_over_600=%u/%u", war.catId, war.code.c_str(),
					war.warRowId, secs, war.picksTotal, war.healsTotal, war.gapN ? war.gapSumMs / war.gapN : 0ULL,
					war.gapMaxMs, war.gapOver600, war.gapN);
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

	// MT2009_PLUS_PVPFAN_TACTICS_V1: the tactics' part of the census, once a minute while a war with tactics fights:
	// squads standing (by mode), skirmish spots (skirmishing squads within PVPFAN_SKIRMISH_JOIN of each other are one
	// spot), the mean pairwise distance of every standing fighter (a sample of 20000 pairs past 200 fighters), the
	// squads' own mean spread, the kites, retreats, regroups, heals, peels and merges of the minute (and of the war),
	// and the mean skirmish (ENGAGE) length - of those that ended in the minute, and of those running now.
	void LogPlayerBotPvpFanTacticsCensus(TPvpFanWar& war, DWORD dwNow)
	{
		unsigned int modes[4] = { 0, 0, 0, 0 };
		std::vector<std::pair<long, long> > spots;
		long squadSpread = 0;
		unsigned int squadsUp = 0;
		unsigned long long runningMs = 0;
		unsigned int running = 0;
		for (size_t q = 0; q < war.squads.size(); ++q)
		{
			const TPvpFanSquad& sq = war.squads[q];
			++modes[MINMAX(0, sq.mode, 3)];
			if (sq.mode == PVPFAN_SQ_GONE)
				continue;
			++squadsUp;
			squadSpread += sq.spread;
			if (sq.mode != PVPFAN_SQ_ENGAGE)
				continue;
			if (sq.engageAt)
			{
				runningMs += PvpFanSince(dwNow, sq.engageAt);
				++running;
			}
			bool joined = false;
			for (size_t k = 0; k < spots.size() && !joined; ++k)
				joined = DISTANCE_APPROX(spots[k].first - sq.cx, spots[k].second - sq.cy) <= PVPFAN_SKIRMISH_JOIN;
			if (!joined)
				spots.push_back(std::make_pair(sq.cx, sq.cy));
		}
		std::vector<std::pair<long, long> > pos;
		unsigned int roles[3] = { 0, 0, 0 }, retreating = 0;
		for (size_t i = 0; i < war.fighters.size(); ++i)
		{
			const TPvpFanFighter& f = war.fighters[i];
			if (f.dead || f.phase != PVPFAN_F_READY)
				continue;
			pos.push_back(std::make_pair(f.lastX, f.lastY));
			++roles[MIN(2, (int)f.role)];
			if (f.retreating)
				++retreating;
		}
		unsigned long long pairSum = 0, pairs = 0;
		if (pos.size() <= 200)
		{
			for (size_t a = 0; a < pos.size(); ++a)
				for (size_t b = a + 1; b < pos.size(); ++b)
				{
					pairSum += DISTANCE_APPROX(pos[a].first - pos[b].first, pos[a].second - pos[b].second);
					++pairs;
				}
		}
		else
		{
			unsigned int r = dwNow | 1;
			for (int k = 0; k < 20000; ++k)
			{
				r = r * 1664525u + 1013904223u;
				const size_t a = (r >> 8) % pos.size();
				r = r * 1664525u + 1013904223u;
				const size_t b = (r >> 8) % pos.size();
				if (a == b)
					continue;
				pairSum += DISTANCE_APPROX(pos[a].first - pos[b].first, pos[a].second - pos[b].second);
				++pairs;
			}
		}
		const unsigned int fightSec = war.fightAt ? PvpFanSince(dwNow, war.fightAt) / 1000 : 0;
		sys_log(0, "PVPFAN: census tactics category=%u code=%s t=%u:%02u squads=%u/%u advance=%u engage=%u regroup=%u "
				"skirmish_spots=%u spread_pair=%llu spread_squad=%ld melee=%u ranged=%u support=%u retreating_now=%u "
				"kites=%u/%u retreats=%u/%u regroups=%u/%u heals=%u/%u peels=%u engages=%u merges=%u "
				"skirmish_avg_s=%.1f(n%u) running_avg_s=%.1f(n%u) war_avg_s=%.1f(n%u)",
				war.catId, war.code.c_str(), fightSec / 60, fightSec % 60, squadsUp, (unsigned int)war.squads.size(),
				modes[PVPFAN_SQ_ADVANCE], modes[PVPFAN_SQ_ENGAGE], modes[PVPFAN_SQ_REGROUP], (unsigned int)spots.size(),
				pairs ? pairSum / pairs : 0ULL, squadsUp ? squadSpread / (long)squadsUp : 0L, roles[0], roles[1], roles[2],
				retreating, war.kitesMin, war.kitesTotal, war.retreatsMin, war.retreatsTotal, war.regroupsMin,
				war.regroupsTotal, war.healsMin, war.healsTotal, war.peelsMin, war.engagesMin, war.mergesTotal,
				war.engEndsMin ? war.engMsMin / 1000.0 / war.engEndsMin : 0.0, war.engEndsMin,
				running ? runningMs / 1000.0 / running : 0.0, running,
				war.engEndsTotal ? war.engMsTotal / 1000.0 / war.engEndsTotal : 0.0, war.engEndsTotal);
		war.kitesMin = war.retreatsMin = war.regroupsMin = war.healsMin = war.peelsMin = war.engagesMin = war.engEndsMin = 0;
		war.engMsMin = 0;
	}

	// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the default fight's minute - foes drawn, foes let go (fell / got away / kept
	// long enough), how the war is spread over its targets (from the crowd of the last evaluation), the archers'
	// steps, the heals, and the fighters' tick gaps (avg / max / over 600 ms: the stutter's measure, in both styles).
	void LogPlayerBotPvpFanFightCensus(TPvpFanWar& war, DWORD dwNow)
	{
		unsigned int targets = 0, attacking = 0, busiest = 0;
		for (std::unordered_map<DWORD, int>::const_iterator c = war.crowd.begin(); c != war.crowd.end(); ++c)
			if (c->second > 0)
			{
				++targets;
				attacking += (unsigned int)c->second;
				busiest = std::max(busiest, (unsigned int)c->second);
			}
		const unsigned int fightSec = war.fightAt ? PvpFanSince(dwNow, war.fightAt) / 1000 : 0;
		sys_log(0, "PVPFAN: census fight category=%u code=%s style=%s t=%u:%02u picks=%u/%u ends_fell=%u ends_fled=%u "
				"ends_time=%u targets=%u attacking=%u busiest=%u archer_steps=%u heals=%u/%u tick_gap_avg_ms=%llu "
				"tick_gap_max_ms=%u tick_gaps_over_600=%u/%u", war.catId, war.code.c_str(),
				war.tacticsOn && !war.squads.empty() ? "squads-experimental" : "guild-war", fightSec / 60, fightSec % 60,
				war.picksMin, war.picksTotal, war.endDeadMin, war.endFledMin, war.endTimeMin, targets, attacking, busiest,
				war.stepsMin, war.healsMin, war.healsTotal, war.gapN ? war.gapSumMs / war.gapN : 0ULL, war.gapMaxMs,
				war.gapOver600, war.gapN);
		war.picksMin = war.endDeadMin = war.endFledMin = war.endTimeMin = war.stepsMin = 0;
		war.gapSumMs = 0;
		war.gapN = war.gapMaxMs = war.gapOver600 = 0;
	}

	void LogPlayerBotPvpFanCensus(DWORD dwNow)
	{
		if (s_mapPvpFanWars.empty() || (s_dwPvpFanNextCensus && (int)(dwNow - s_dwPvpFanNextCensus) < 0))
			return;
		s_dwPvpFanNextCensus = dwNow + PVPFAN_CENSUS_MS;
		for (std::map<DWORD, TPvpFanWar>::iterator it = s_mapPvpFanWars.begin(); it != s_mapPvpFanWars.end(); ++it)
		{
			TPvpFanWar& war = it->second;
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
			if (war.state != PVPFAN_FIGHTING)
				continue;
			// before the tactics census, which zeroes the heals of the minute
			LogPlayerBotPvpFanFightCensus(war, dwNow);
			if (war.tacticsOn && !war.squads.empty())
				LogPlayerBotPvpFanTacticsCensus(war, dwNow);
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
					"SELECT szName, lValue FROM player.quest WHERE dwPID=0 AND szName IN ('m2_pvpfan_off','m2_pvpfan_tactics_off')");
			MYSQL_ROW row;
			bool off = false, tacticsOff = false;
			if (PvpFanOk(flag) && flag->Get()->pSQLResult)
				while (NULL != (row = mysql_fetch_row(flag->Get()->pSQLResult)))
				{
					const bool on = PvpFanLong(row[1]) != 0;
					if (row[0] && std::strcmp(row[0], "m2_pvpfan_off") == 0)
						off = on;
					else
						tacticsOff = on;
				}
			s_bPvpFanDbFlagOff = off;
			s_bPvpFanDbTacticsOff = tacticsOff;
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
	void ManagePlayerBotPvpFanWars(DWORD dwNow)
	{
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
				// MT2009_PLUS_PVPFAN_TACTICS_V1: the flag switches a running war at once (both ways).
				const bool tacticsOn = war.tactics && !war.squads.empty() && !IsPlayerBotPvpFanTacticsFlagOff();
				if (tacticsOn != war.tacticsOn)
				{
					sys_log(0, "PVPFAN: tactics category=%u code=%s %s (m2_pvpfan_tactics_off)", war.catId, war.code.c_str(),
							tacticsOn ? "on again" : "off - the guild war's fight");
					war.tacticsOn = tacticsOn;
					war.nextGrid = war.nextSquads = dwNow;
				}
				EvaluatePlayerBotPvpFanWar(war, dwNow);
			}
			// MT2009_PLUS_PVPFAN_WARSTYLE_V1: the spatial grid for every war on its spots and in the fight (the foes'
			// draw, the shamans' mates), every PVPFAN_GRID_MS.
			if ((war.state == PVPFAN_WAITING || war.state == PVPFAN_COUNTDOWN || war.state == PVPFAN_FIGHTING) &&
					(int)(dwNow - war.nextGrid) >= 0)
			{
				war.nextGrid = dwNow + PVPFAN_GRID_MS;
				BuildPlayerBotPvpFanGrid(war);
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
							war.fighters[i].engaged = war.fighters[i].retreating = false;
							// every tactics clock compared as (int)(dwNow - at) starts now, never at 0 (a 0 would read as
							// "ahead" once the core's clock passes 2^31 ms)
							war.fighters[i].retreatCdUntil = war.fighters[i].kiteMoveUntil = war.fighters[i].retargetAt = dwNow;
							war.fighters[i].threatLookAt = war.fighters[i].supportLookAt = war.fighters[i].foeLookAt = dwNow;
							war.fighters[i].castFailUntil = dwNow;
							// MT2009_PLUS_PVPFAN_WARSTYLE_V1
							war.fighters[i].keepUntil = war.fighters[i].chaseAt = war.fighters[i].lookFarAt = dwNow;
							war.fighters[i].stepWindowAt = dwNow;
							war.fighters[i].tickAt = 0;
							war.fighters[i].targetPid = 0;
							war.fighters[i].steps = 0;
						}
						// MT2009_PLUS_PVPFAN_TACTICS_V1: every squad marches first; the grid and the decisions at once.
						for (size_t q = 0; q < war.squads.size(); ++q)
						{
							war.squads[q].mode = war.squads[q].members.empty() ? PVPFAN_SQ_GONE : PVPFAN_SQ_ADVANCE;
							war.squads[q].modeAt = dwNow;
							war.squads[q].engageAt = 0;
							war.squads[q].regroupCdUntil = dwNow;
							war.squads[q].objective = -1;
						}
						war.nextGrid = war.nextSquads = dwNow;
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
					// MT2009_PLUS_PVPFAN_TACTICS_V1: the squads' decisions every second (experimental; the grid above).
					if (war.tacticsOn && !war.squads.empty())
					{
						if ((int)(dwNow - war.nextSquads) >= 0)
						{
							war.nextSquads = dwNow + PVPFAN_SQUAD_DECIDE_MS;
							DecidePlayerBotPvpFanSquads(war, dwNow);
						}
					}
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

	// The wars (their own clock, PVPFAN_TICK_MS), then their fighters (MT2009_PLUS_PVPFAN_WARSTYLE_V1).
	void ManagePlayerBotPvpFan(DWORD dwNow)
	{
		if (!IsPlayerBotPvpFanEnabled())
			return;
		ManagePlayerBotPvpFanWars(dwNow);
		TickPlayerBotPvpFanBots(dwNow);
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
