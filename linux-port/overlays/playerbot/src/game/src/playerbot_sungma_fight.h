#ifndef __INC_METIN2_PLAYERBOT_SUNGMA_FIGHT_H__
#define __INC_METIN2_PLAYERBOT_SUNGMA_FIGHT_H__

// MT2009_PLUS_BOT_YOHARA_FIGHT_V1 - the fight on the Sung Ma maps of Yohara (the owner, 22 October 2026, night: "Faza 5 -
// walka: druzyny botow na rdzeniu Yohary na bossow i posterunki, wybor celow, wycofywanie sie"). Plan:
// cache/yohara/plan-boty-yohara.md 7.2-7.4; the doc for the owner: cache/yohara/boty-mapy-yohary.md, section 11.
//
// What a resident of a Sung Ma map weighs before and during a fight - the packs, its strength, its party round it, the
// monsters' elements - and the way it breaks off one:
//   * the pack: a monster struck calls its group (the engine's monster party) and every aggressive monster in sight of
//     the striker; a bot counts the idle monsters round a candidate (PLAYERBOT_SUNGMA_PACK_RADIUS, the aggressive ones
//     out to PLAYERBOT_SUNGMA_AGGRO_RADIUS) and takes the edge of a crowd, never more than its capacity
//     (GetPlayerBotSungmaCapacity: its health, its belt, the party members by it);
//   * the target (PickPlayerBotSungmaTarget, playerbot_targeting.h): a party leader with three ready members by it takes
//     the stone or the boss in reach first; everyone else the monster of its band (the map's weakest level plus a level
//     for every three Champion levels over the band's floor), the edge of a pack, the element its talisman bites;
//   * the retreat (CheckPlayerBotSungmaRetreat / HandlePlayerBotSungmaRetreat): by the health and the number of the
//     attackers, away from the pack and toward the map's safe point (PLAYERBOT_SUNGMA_SAFE_POINTS), the belt drunk at
//     PLAYERBOT_SUNGMA_POTION_PERCENT, back to the hunt once healed; a lone bot that pulled too much leaves the spot
//     (PLAYERBOT_SUNGMA_AVOID_MS) - its next spot is another;
//   * the deaths (NotePlayerBotSungmaFallen): each one's cause - the walk to a portal, Dongan's errand, a fall soon
//     after the last, a stone, a boss, a pack, a lone or a party's fight - for the census (PLAYERBOT_SUNGMA: fight).
// The parties themselves (who joins whom, the regroup, the errands' clean leave) are playerbot_yohara_sungma_party.h's.
//
// MT2009_PLUS_BOT_SUNGMA_NEST_V1 (the owner, 27 October 2026: "Czy boty daja sobie rade na yoharze?" - only the Twierdza
// and Yilad did): the safe point had become a nest of the packs the retreats led to it (the clean ground, below); the
// revival, the retreat and the landing go to the cleanest ground by it; a retreat leads no pack toward it; a lost
// retreat ends in an escape (the teleport a person takes); the aggressive monsters are counted out to their real 2 000;
// a map asks a maximum health (playerbot_yohara_sungma.h, PLAYERBOT_SUNGMA_HP_FLOORS); Namgan's dense spots a party's.
//
// An implementation fragment: included by playerbot_manager.cpp before playerbot_survival.h, in the anonymous
// namespace.

namespace
{

	// ------------------------------------------------------------ the numbers
	const int PLAYERBOT_SUNGMA_PACK_RADIUS = 900;		// a monster's group round it (the regen's groups spread 300-700)
	// An aggressive idle monster this near the fight joins it. MT2009_PLUS_BOT_SUNGMA_NEST_V1: 2000, the engine's own
	// reach (StateIdle -> FindVictim(this, mob_proto.aggressive_sight)) - aggressive_sight is 2000 for every aggressive
	// monster the nine maps spawn (player.mob_proto, 27 October: 100 such rows of 6684-6900; the 15 of 60000 are the
	// snake temple's and Alastor's); 1400 left a ring of 600 units of aggressive monsters out
	// of every pack count, and the "pulled" retreats (attackers >= capacity + 2: 1 611 of 6 407 retreats on 27 October
	// 20:15-21:06, Wawoz 283, Rozpadlina 270, Schronienie 315) were the packs the count had called small.
	const int PLAYERBOT_SUNGMA_AGGRO_RADIUS = 2000;
	const int PLAYERBOT_SUNGMA_NEAR_LOG_RADIUS = 1400;	// the "near" of the fallen line (kept, the logs compare)
	const int PLAYERBOT_SUNGMA_SCAN_RADIUS = 4500;		// the monsters a bot looks at round itself
	const int PLAYERBOT_SUNGMA_ATTACKER_RADIUS = 2500;	// a monster hitting the bot
	const int PLAYERBOT_SUNGMA_PARTY_NEAR = 3000;		// a party member "by" the bot (the stones, the bosses, the capacity)
	const int PLAYERBOT_SUNGMA_PARTY_READY_HP = 55;		// ...and ready for an objective
	// How many monsters a bot takes at once: alone 3 (2 under 70% health, 1 under 50% or with under
	// PLAYERBOT_SUNGMA_CAPACITY_LOW_RED potions), and 2 more for each ready member by it, to PLAYERBOT_SUNGMA_CAPACITY_MAX;
	// one fewer alone where the weakest monsters are PLAYERBOT_SUNGMA_CAPACITY_HARD_LEVEL or more (Yilad on: aggressive,
	// 125-190 k health, against 64-147 k of the four maps before).
	const int PLAYERBOT_SUNGMA_CAPACITY_LONE = 3;
	const int PLAYERBOT_SUNGMA_CAPACITY_HARD_LEVEL = 122;
	const int PLAYERBOT_SUNGMA_CAPACITY_MEMBER = 2;
	const int PLAYERBOT_SUNGMA_CAPACITY_MAX = 11;
	const size_t PLAYERBOT_SUNGMA_CAPACITY_LOW_RED = 15;
	// The belt: drunk from this health on a Sung Ma map (elsewhere PLAYERBOT_POTION_HP_PERCENT, 65) - one blow of a
	// berserk 125 takes 15-25% of a cohort bot's 23-33 k.
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: 85 - the belt is the fight's, not the retreat's (see the FIGHT2 numbers below).
	const int PLAYERBOT_SUNGMA_POTION_PERCENT = 85;
	// The retreat: at this health alone / in a party by it; at PLAYERBOT_SUNGMA_RETREAT_PACK_HP with more attackers
	// than its capacity; at any health under PLAYERBOT_SUNGMA_RETREAT_PULLED_HP with PLAYERBOT_SUNGMA_PULLED_EXTRA over
	// its capacity (pulled too much). Over at PLAYERBOT_SUNGMA_RETREAT_END_HP with nobody on it, or after
	// PLAYERBOT_SUNGMA_RETREAT_MAX_MS.
	// (MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the fight's own floor and pull replace _LONE_HP, _PARTY_HP, _PULLED_*, _FALL_* and
	// _END_HP below - PLAYERBOT_SUNGMA_F2_*; _PACK_HP stays the clock's line, kept for the logs' history.)
	const int PLAYERBOT_SUNGMA_RETREAT_LONE_HP = 45;
	const int PLAYERBOT_SUNGMA_RETREAT_PARTY_HP = 35;
	const int PLAYERBOT_SUNGMA_RETREAT_PACK_HP = 60;
	const int PLAYERBOT_SUNGMA_RETREAT_PULLED_HP = 90;
	const int PLAYERBOT_SUNGMA_PULLED_EXTRA = 2;
	const int PLAYERBOT_SUNGMA_RETREAT_END_HP = 80;
	// And the fall's speed: PLAYERBOT_SUNGMA_RETREAT_FALL_PERCENT of its health lost within PLAYERBOT_SUNGMA_RETREAT_FALL_MS,
	// with two on it, under PLAYERBOT_SUNGMA_RETREAT_FALL_HP. The test of 22 October (19:43-20:00, game3): a cohort bot
	// lost 25-30% a second to three monsters of Rozpadlina (11 907 -> 5 119 of 23 607 between two potions) - the generic
	// retreat at 35% left it a second and a half; 50 of 684 retreats ended in a death, 130 began under 20%.
	const int PLAYERBOT_SUNGMA_RETREAT_FALL_PERCENT = 25;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_FALL_MS = 2500;
	const int PLAYERBOT_SUNGMA_RETREAT_FALL_HP = 70;
	// A new fight (nothing on it) only from this health: the belt (PLAYERBOT_SUNGMA_POTION_PERCENT) tops it up first. The
	// same test: 17 of 68 deaths came within 90 s of the last - revived, at 75% "recovered", straight back into a pack.
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: 60 (was 75) - the belt (85%) tops it up in the fight; the waits for 75 were a
	// third of the bots' hour.
	const int PLAYERBOT_SUNGMA_ENGAGE_HP = 60;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_MAX_MS = 120 * 1000;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_MOVE_MS = 1500;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_LOOK_MS = 700;
	const int PLAYERBOT_SUNGMA_RETREAT_STEP = 1500;
	const int PLAYERBOT_SUNGMA_SAFE_REACHED = 1500;
	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the escape out of a lost retreat (HandlePlayerBotSungmaRetreat).
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the escape at the bot's own danger floor (GetPlayerBotSungmaFloorHp) or
	// _ESCAPE_HP, whichever is higher, after 1.5 s (was 3 s at 30%) - a step of 1 500 units outruns nothing.
	const int PLAYERBOT_SUNGMA_ESCAPE_ATTACKERS = 2;
	const int PLAYERBOT_SUNGMA_ESCAPE_HP = 30;
	const DWORD PLAYERBOT_SUNGMA_ESCAPE_AFTER_MS = 1500;
	const DWORD PLAYERBOT_SUNGMA_ESCAPE_GAP_MS = 2 * 60 * 1000;	// a ring's cooldown - not every retreat
	const int PLAYERBOT_SUNGMA_ESCAPE_MIN_DIST = 5000;			// past the 4 000 a monster chases to
	const int PLAYERBOT_SUNGMA_SAFE_MAX = 40000;		// farther than this the safe point is no direction (the way crosses the map)
	// The spot a lone bot pulled too much on: no target, no hub within PLAYERBOT_SUNGMA_AVOID_RADIUS for this long.
	const DWORD PLAYERBOT_SUNGMA_AVOID_MS = 10 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_AVOID_RADIUS = 2500;
	// Every pack round it too big this many picks running (within PLAYERBOT_SUNGMA_REFUSED_MS): the spot is avoided the
	// same way and the bot moves on to another.
	const int PLAYERBOT_SUNGMA_REFUSED_MOVE_ON = 4;
	const DWORD PLAYERBOT_SUNGMA_REFUSED_MS = 90 * 1000;
	// The edge of a pack over the whole of it: a monster that wakes one more is worth this much less, and one over the
	// level the band fights PLAYERBOT_SUNGMA_LEVEL_PENALTY a level; the element the bot bites (its power) and resists.
	const int PLAYERBOT_SUNGMA_WAKE_PENALTY = 60000;
	const int PLAYERBOT_SUNGMA_LEVEL_PENALTY = 40000;
	const int PLAYERBOT_SUNGMA_ELEMENT_POWER_SCORE = 1000;	// a point of power, to 200
	const int PLAYERBOT_SUNGMA_ELEMENT_RESIST_SCORE = 2000;	// a point of resistance, to 50
	// A death this soon after the last one (or an emergency rest) is the revival's (the cause "again").
	const DWORD PLAYERBOT_SUNGMA_DEATH_AGAIN_MS = 90 * 1000;
	// The monsters of each map's weakest level (mob_proto of the regen's monsters, 22 October) - the band's floor fights
	// these; every PLAYERBOT_SUNGMA_LEVEL_PER_CHAMPION Champion levels over the floor one level more.
	const int PLAYERBOT_SUNGMA_LEVEL_PER_CHAMPION = 3;
	struct TPlayerBotSungmaMobFloor { long lMap; int iLevel; };
	const TPlayerBotSungmaMobFloor PLAYERBOT_SUNGMA_MOB_FLOORS[] = {
		{ 374, 119 }, { 373, 119 }, { 376, 119 }, { 377, 119 }, { 385, 122 }, { 388, 123 }, { 389, 123 }, { 393, 124 },
		{ 394, 125 },
	};
	// The elements: a monster's race flag, the bot's power against it, its resistance to it.
	struct TPlayerBotSungmaElement { DWORD dwFlag; BYTE bEnchant; BYTE bResist; };
	const TPlayerBotSungmaElement PLAYERBOT_SUNGMA_ELEMENTS[] = {
		{ RACE_FLAG_ATT_ELEC, POINT_ENCHANT_ELECT, POINT_RESIST_ELEC },
		{ RACE_FLAG_ATT_FIRE, POINT_ENCHANT_FIRE, POINT_RESIST_FIRE },
		{ RACE_FLAG_ATT_ICE, POINT_ENCHANT_ICE, POINT_RESIST_ICE },
		{ RACE_FLAG_ATT_TEMPLE, POINT_ENCHANT_WIND, POINT_RESIST_WIND },
		{ RACE_FLAG_ATT_EARTH, POINT_ENCHANT_EARTH, POINT_RESIST_EARTH },
		{ RACE_FLAG_ATT_DARK, POINT_ENCHANT_DARK, POINT_RESIST_DARK },
	};

	// ------------------------------------------------------------ MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the numbers
	// The owner, 28 October 2026: "mniej ucieczek, walka grupami w gestszych miejscach". The night of 28 October (00-08,
	// game3, 400 bots of Champion 1-30 in G0 gear): 13 300 retreats an hour on the nine maps (54 a bot an hour on
	// Seoganland, Wawoz and Rozpadlina), 15-35 s each, ending "healed" 98% of the time - 35-45% of a bot's hour. A retreat
	// did not shake its pack off: the monsters kept on it while the bot drank a red potion (27003, 1 200 HP) a second and
	// struck nothing (a bot of 30 k held 22-24 k for 48 s of a "pulled" retreat begun at 85%). The "pulled" retreat began
	// at a median of 80% health, "pack" and "fall" at 54-55%, "hp" at 34%; 225 000 red potions an hour were drunk on the
	// core anyway. So the bot fights through on its belt and runs only at a real danger floor:
	//   * the floor (GetPlayerBotSungmaFloorHp): _FLOOR_LONE alone, _FLOOR_PARTY with a member by it, + the map's
	//     difficulty (PLAYERBOT_SUNGMA_F2_DIFFICULTY: the night's kills per death 4-9 on Dongan, Namgan, Wawoz,
	//     Rozpadlina), + _FLOOR_WEAK under _WEAK_MAX_HP maximum health, - _FLOOR_BAND_HIGH _BAND_HIGH_LEVELS Champion levels
	//     over the band's floor; with fewer than PLAYERBOT_SUNGMA_CAPACITY_LOW_RED reds the old _FLOOR_NO_RED;
	//   * "pack" (more on it than it takes) at floor + _PACK_OVER, "pulled" (_PULLED_EXTRA over) at floor + _PULLED_OVER,
	//     "fall" (_FALL_PERCENT lost in 2.5 s with two on it) at floor + _FALL_OVER;
	//   * a retreat its pack keeps up with is turned into a fight again (_TURN_*): still held after _TURN_AFTER_MS, health
	//     at floor + _TURN_OVER or more and no more than its capacity + 1 on it - for _TURN_HOLD_MS after it only the floor
	//     and the fall send it off again;
	//   * the retreat is over at _END_HP with nobody on it (was 80).
	const int PLAYERBOT_SUNGMA_F2_FLOOR_LONE = 28;
	const int PLAYERBOT_SUNGMA_F2_FLOOR_PARTY = 22;
	const int PLAYERBOT_SUNGMA_F2_FLOOR_NO_RED = 45;
	const int PLAYERBOT_SUNGMA_F2_FLOOR_WEAK = 5;
	const int PLAYERBOT_SUNGMA_F2_WEAK_MAX_HP = 20000;
	const int PLAYERBOT_SUNGMA_F2_FLOOR_BAND_HIGH = 3;
	const int PLAYERBOT_SUNGMA_F2_BAND_HIGH_LEVELS = 5;
	const int PLAYERBOT_SUNGMA_F2_PACK_OVER = 15;
	const int PLAYERBOT_SUNGMA_F2_PULLED_OVER = 30;
	const int PLAYERBOT_SUNGMA_F2_PULLED_EXTRA = 3;
	const int PLAYERBOT_SUNGMA_F2_FALL_PERCENT = 30;
	const int PLAYERBOT_SUNGMA_F2_FALL_OVER = 20;
	const DWORD PLAYERBOT_SUNGMA_F2_TURN_AFTER_MS = 5000;
	const int PLAYERBOT_SUNGMA_F2_TURN_OVER = 15;
	const DWORD PLAYERBOT_SUNGMA_F2_TURN_HOLD_MS = 20 * 1000;
	const int PLAYERBOT_SUNGMA_F2_END_HP = 65;
	// The map's difficulty (added to the floor), by the night's kills per death: Dongan 4, Namgan 6, Wawoz 8,
	// Rozpadlina 9 (+6); Seoganland 11, Schronienie 20, Zejscie 26 (+3); the Twierdza 26, Yilad 87 (0).
	struct TPlayerBotSungmaDifficulty { long lMap; int iFloorAdd; };
	const TPlayerBotSungmaDifficulty PLAYERBOT_SUNGMA_F2_DIFFICULTY[] = {
		{ 374, 0 }, { 373, 6 }, { 376, 3 }, { 377, 6 }, { 385, 0 }, { 388, 6 }, { 389, 6 }, { 393, 3 }, { 394, 3 },
	};
	const int PLAYERBOT_SUNGMA_F2_HARD = 6;
	// The pull (GetPlayerBotSungmaLoneCapacity): what a bot takes alone by its maximum health (_CAP_HP_*), one fewer on a
	// hard map, more with its defence read live (the owner's word of 28 October: a Yohara monster hits for 400-500 and
	// ~5 000 with a piercing blow - a pull is safe by block, dodge, the piercing resistance and the element's
	// resistance, not by the gear of today): armour = block + dodge / 2 + piercing resistance + the element's
	// resistance / 2; +1 from _CAP_ARMOUR_1, +2 from _CAP_ARMOUR_2. Never under 2 or over _CAP_LONE_MAX.
	const int PLAYERBOT_SUNGMA_F2_CAP_HP_3 = 18000;
	const int PLAYERBOT_SUNGMA_F2_CAP_HP_4 = 27000;
	const int PLAYERBOT_SUNGMA_F2_CAP_ARMOUR_1 = 25;
	const int PLAYERBOT_SUNGMA_F2_CAP_ARMOUR_2 = 50;
	const int PLAYERBOT_SUNGMA_F2_CAP_LONE_MAX = 5;
	// A Sung Ma fighter's skill gap (PLAYERBOT_SKILL_ATTACK_INTERVAL / the Shaman's) times this per cent: the night's
	// bots cast a skill every 20 s; the skills' own cooldowns still hold (IsPlayerBotSkillReady).
	const int PLAYERBOT_SUNGMA_F2_SKILL_GAP_PERCENT = 60;
	// The area skills first with this many monsters by the target (PLAYERBOT_SUNGMA_F2_AREA_RADIUS of it).
	const int PLAYERBOT_SUNGMA_F2_AREA_MIN = 2;
	const int PLAYERBOT_SUNGMA_F2_AREA_RADIUS = 500;
	// The hunt element (the owner, 28 October: one element a bot, its map's majority, the gear for it, the spots of it):
	// a monster of it is worth this much more as a target; a hub's score + _HUB_ELEMENT_PERCENT x the share of its
	// monsters of it, and for a party's leader + _HUB_DENSE_PERCENT a monster round it (to _HUB_DENSE_MAX).
	const int PLAYERBOT_SUNGMA_F2_ELEMENT_MATCH_SCORE = 120000;
	const int PLAYERBOT_SUNGMA_F2_HUB_RADIUS = 2500;
	const int PLAYERBOT_SUNGMA_F2_HUB_ELEMENT_PERCENT = 80;
	const int PLAYERBOT_SUNGMA_F2_HUB_DENSE_PERCENT = 5;
	const int PLAYERBOT_SUNGMA_F2_HUB_DENSE_MAX = 30;
	// A member (not the leader) takes no monster farther than this from its leader unless it is on the member - the
	// party fights one spot (the night: 15 452 regroups an hour on the Twierdza for 21 parties, 400-520 "far" leaves an
	// hour on Seoganland, Yilad, Wawoz, Rozpadlina).
	const int PLAYERBOT_SUNGMA_F2_TETHER = 2200;
	// The census's fight2 line once an hour (LogPlayerBotSungmaFightCensus).
	const DWORD PLAYERBOT_SUNGMA_F2_CENSUS_MS = 60 * 60 * 1000;

	// ------------------------------------------------------------ the state and the census

	struct TPlayerBotSungmaFight
	{
		bool bRetreat;				// a retreat this file runs (HandlePlayerBotSungmaRetreat)
		char szRetreatWhy[12];
		int iRetreatAttackers;
		long lAvoidMap, lAvoidX, lAvoidY;
		DWORD dwAvoidUntil;
		DWORD dwLastDown;			// its last death or emergency rest (the cause "again")
		DWORD dwNextRetreatLook;
		int iRefused;				// the target picks refused in a row (every pack too big for it)
		DWORD dwRefusedSince;
		int iHpSeen;				// its health (per cent) at the last look, and when (the fall's speed)
		DWORD dwHpSeenAt;
		DWORD dwLastEscape;			// MT2009_PLUS_BOT_SUNGMA_NEST_V1: its last escape out of a lost retreat
		DWORD dwTurnHoldUntil;		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: turned to fight - only the floor and the fall till then
		// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the re-arm (HoldPlayerBotSungmaRearm) - 0 none, 1 after a death or an emergency
		// rest, 2 after a healed retreat; pending until the recovery is over, then held until dwRearmUntil
		BYTE bRearm;
		bool bRearmPending;
		DWORD dwRearmSince, dwRearmUntil, dwRearmNextCast;
		DWORD dwRetreatCounted;		// the retreat (its start time) the class census has counted
		TPlayerBotSungmaFight() : bRetreat(false), iRetreatAttackers(0), lAvoidMap(0), lAvoidX(0), lAvoidY(0), dwAvoidUntil(0),
			dwLastDown(0), dwNextRetreatLook(0), iRefused(0), dwRefusedSince(0), iHpSeen(100), dwHpSeenAt(0), dwLastEscape(0),
			dwTurnHoldUntil(0), bRearm(0), bRearmPending(false), dwRearmSince(0), dwRearmUntil(0), dwRearmNextCast(0),
			dwRetreatCounted(0)
		{ szRetreatWhy[0] = '\0'; }
	};
	std::map<DWORD, TPlayerBotSungmaFight> s_mapPlayerBotSungmaFight;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: a map's kills per death x10 of its last fight2 line (0: no line or no deaths yet)
	int s_aiPlayerBotSungmaF2Kpd10[9] = { 0 };
#endif

	// The census's fight counters a map (the slot of PLAYERBOT_SUNGMA_MAPS - the same nine, in the same order).
	enum EPlayerBotSungmaDeathCause
	{
		SUNGMA_DEATH_PORTAL, SUNGMA_DEATH_ERRAND, SUNGMA_DEATH_AGAIN, SUNGMA_DEATH_RETREAT, SUNGMA_DEATH_STONE,
		SUNGMA_DEATH_BOSS, SUNGMA_DEATH_PACK, SUNGMA_DEATH_FIGHT, SUNGMA_DEATH_CAUSES
	};
	const char* const PLAYERBOT_SUNGMA_DEATH_CAUSE_NAMES[SUNGMA_DEATH_CAUSES] = {
		"portal", "errand", "again", "retreat", "stone", "boss", "pack", "fight"
	};
	struct TPlayerBotSungmaFightStats
	{
		unsigned int deaths[SUNGMA_DEATH_CAUSES];
		unsigned int deathsLone, deathsParty;
		unsigned int retreatsHp, retreatsPack, retreatsPulled, retreatsSafe, avoids;
		unsigned int targetsPicked, targetsElement, targetsEdge, packRefused, partyObjectives;
		unsigned int partyForms, partyJoins, partyLeaves, partyErrandLeaves, regroups, revivesInParty;
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the escapes out of a lost retreat, the revivals and landings moved off a
		// crowded safe point, the moves refused for the bot's health (PLAYERBOT_SUNGMA_HP_FLOORS)
		unsigned int escapes, nestMoves, hpRefused;
		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: every retreat ended and its time, the potions drunk, the retreats turned into a
		// fight, the picks of the hunt element; the fight2 line's last snapshot (kills, deaths, these) and the bots seen
		unsigned int retreatsEnded, turns, potions, huntElementPicks;
		unsigned long long retreatMs;
		DWORD f2Since;
		unsigned int f2Kills, f2Deaths, f2Retreats, f2Turns, f2Potions, f2Escapes, f2Samples, f2BotSum;
		unsigned long long f2RetreatMs;
		TPlayerBotSungmaFightStats() : deathsLone(0), deathsParty(0), retreatsHp(0), retreatsPack(0), retreatsPulled(0),
			retreatsSafe(0), avoids(0), targetsPicked(0), targetsElement(0), targetsEdge(0), packRefused(0), partyObjectives(0),
			partyForms(0), partyJoins(0), partyLeaves(0), partyErrandLeaves(0), regroups(0), revivesInParty(0),
			escapes(0), nestMoves(0), hpRefused(0), retreatsEnded(0), turns(0), potions(0), huntElementPicks(0), retreatMs(0),
			f2Since(0), f2Kills(0), f2Deaths(0), f2Retreats(0), f2Turns(0), f2Potions(0), f2Escapes(0), f2Samples(0),
			f2BotSum(0), f2RetreatMs(0)
		{
			for (int i = 0; i < SUNGMA_DEATH_CAUSES; ++i)
				deaths[i] = 0;
		}
	};
	TPlayerBotSungmaFightStats s_aPlayerBotSungmaFightStats[9];

	TPlayerBotSungmaFightStats* GetPlayerBotSungmaFightStats(long mapIndex)
	{
		const int slot = GetPlayerBotSungmaSlot(mapIndex);
		return slot >= 0 && slot < 9 ? &s_aPlayerBotSungmaFightStats[slot] : NULL;
	}

	// A bot of the Sung Ma maps standing on one: the rules of this file are its.
	bool IsPlayerBotSungmaFighter(LPCHARACTER ch)
	{
		return ch && IsPlayerBotSungmaBotMap(ch->GetMapIndex()) && IsPlayerBotSungmaResidentPID(ch->GetPlayerID()) &&
				!IsPlayerBotHumanLedParty(ch->GetParty());
	}

	int GetPlayerBotSungmaHpPercent(LPCHARACTER ch)
	{
		return ch && ch->GetMaxHP() > 0 ? (int)((long long)ch->GetHP() * 100 / ch->GetMaxHP()) : 100;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the fighter's build
	//
	// The owner, 28 October 2026 (approved points 1 and 7): a Sung Ma fight that knows the bot's build. The game3 syslog
	// of 28 October (00:00-17:50, the hours 10 and 13 missing): 14 203 "fallen" lines of 440 residents, the build of
	// each from player.player (job, skill_group). Deaths a bot, and normalised - the deaths over the deaths its time on
	// each map would bring at the map's average deaths per bot-hour (the bots' map time from PLAYERBOT_WORLD
	// transitioned / ENTERGAME / DISCONNECT; Dongan 6.0 deaths a bot-hour, Namgan 4.2, Seoganland 2.9, Wawoz 2.1,
	// Rozpadlina 2.0, the Twierdza 1.4, Schronienie 1.3, Zejscie 1.3, Yilad 0.7):
	//   build              deaths/bot  normalised  "again"   died in a retreat / retreats begun
	//   Black-magic Sura      54.0        2.06       71%       11.4%
	//   Body Warrior          34.3        1.07       43%        3.6%
	//   Dragon Shaman         32.9        0.89       45%        3.5%
	//   Blade Ninja           31.7        0.89       45%        3.4%
	//   Healing Shaman        28.3        0.82       41%        2.8%
	//   Mental Warrior        28.1        0.79       37%        3.1%
	//   Weaponry Sura         25.3        0.72       36%        3.0%
	// The Black-magic Sura's spiral: 1 408 emergency rests in the night (00-08), 1 347 of them begun inside a retreat
	// (the 20% rest of playerbot_manager.cpp starts under a running retreat), and 661 of them ended in its death, at a
	// median of 3 s - not one of the 11 771 emergency rests of the other six builds did. The rest is invisible
	// (ReviveInvisible) and nothing of the bot's own is cast in it (no "used attack skill", no buff); what the Black-magic
	// Sura alone carries into it is Flame Spirit (Ognisty Duch, skill 78), a toggle aura whose engine event
	// (char_skill.cpp skill_muyoung_event) strikes the nearest monster within 800 every 3 s - its target or any monster
	// FFindNearVictim finds, an idle one too - for as long as the affect lasts: through the retreat (4x the deaths of a
	// retreat of the other builds: it keeps its pack and wakes the next) and through the "invisible" rest (the 3 s of
	// the median). 22% of its deaths on the Twierdza are its time there (31% of its hours against 18-23% - the deaths'
	// step down sends it to the easiest map): per bot-hour it dies 2-4x the others on every map. Its mana adds to it:
	// Dark Protection (79) takes a share of every blow from the mana (char_battle.cpp, damage_convertion_rate) and the
	// aura's cost runs on, while the blue potion waited for 30% (PLAYERBOT_POTION_SP_PERCENT) - its last mana before an
	// "again" death was a median 14%, and restart_here gives no mana back.
	// So (this file and the tick):
	//   * the aura comes off when a Sung Ma retreat or an emergency rest begins and stays off through them
	//     (DropPlayerBotSungmaAura); the fight's buff pass puts it back on the next target;
	//   * after a death or an emergency rest (and, shorter, after a healed retreat) a resident re-arms before it takes a
	//     new fight (HoldPlayerBotSungmaRearm): health to PLAYERBOT_SUNGMA_CLASS_REARM_HP, mana to its build's floor, its
	//     self-buffs back up (Dark Protection, the armours, Strong Body, Blessing...), standing still on its clean ground
	//     - over when it is ready, when a monster is on it, or after _REARM_MAX_MS;
	//   * a caster's blue potion at its build's mana floor on a Sung Ma map (GetPlayerBotSungmaManaPercent);
	//   * the lone pull and the danger floor by the build (GetPlayerBotSungmaClassCapacity / _ClassFloor).
	// The census: PLAYERBOT_SUNGMA: class, once an hour, a line a build (LogPlayerBotSungmaClassCensus).
#define MT2009_PLUS_BOT_SUNGMA_CLASS_V1 1
	enum EPlayerBotSungmaClass
	{
		SUNGMA_CLASS_BODY_WARRIOR, SUNGMA_CLASS_MENTAL_WARRIOR, SUNGMA_CLASS_BLADE_NINJA, SUNGMA_CLASS_ARCHER_NINJA,
		SUNGMA_CLASS_WEAPON_SURA, SUNGMA_CLASS_BM_SURA, SUNGMA_CLASS_DRAGON_SHAMAN, SUNGMA_CLASS_HEAL_SHAMAN,
		SUNGMA_CLASS_LYCAN, SUNGMA_CLASS_NONE, SUNGMA_CLASS_COUNT
	};
	const char* const PLAYERBOT_SUNGMA_CLASS_NAMES[SUNGMA_CLASS_COUNT] = {
		"body_warrior", "mental_warrior", "blade_ninja", "archer_ninja", "weapon_sura", "bm_sura", "dragon_shaman",
		"heal_shaman", "lycan", "none"
	};
	// The lone pull a build (GetPlayerBotSungmaLoneCapacity): the owner's approved steps, tuned by the normalised deaths
	// above - the Weaponry Sura (0.72) +1; the Mental Warrior (0.79, high defence, no knockback) +1 with Strong Body
	// up, else 0; the Dragon Shaman +1 with Blessing up on it (0.89 - its deaths came with the Blessing mostly up, so
	// nothing without it); the Body Warrior (1.07) and the Blade Ninja (0.89, the lightest armour) -1, the Lycan -1;
	// the Healing Shaman and the Black-magic Sura 0 (the Sura's 2.06 is the aura's, fixed below - its pull is
	// re-judged on the class census of the next night).
	const int PLAYERBOT_SUNGMA_CLASS_CAP[SUNGMA_CLASS_COUNT] = { -1, 0, -1, 0, 1, 0, 0, 0, -1, 0 };
	const int PLAYERBOT_SUNGMA_CLASS_CAP_BUFFED = 1;	// the Mental Warrior's Strong Body, the Dragon Shaman's Blessing
	// The danger floor a build (GetPlayerBotSungmaFloorHp, per cent of health; the floors are 15-45): small and in the
	// same spirit - the Body Warrior +3, the Blade Ninja +2, the Lycan +3; the Weaponry Sura -2, the Mental Warrior -2
	// with Strong Body up; the Dragon Shaman, the Healing Shaman and the Black-magic Sura 0 (the Dragon's normalised
	// 0.89 is the Blade's - no lower floor for it).
	const int PLAYERBOT_SUNGMA_CLASS_FLOOR[SUNGMA_CLASS_COUNT] = { 3, 0, 2, 0, -2, 0, 0, 0, 3, 0 };
	const int PLAYERBOT_SUNGMA_CLASS_FLOOR_BUFFED = -2;	// the Mental Warrior with Strong Body up
	// The skills of the builds the rules above read (skill.h).
	const DWORD PLAYERBOT_SUNGMA_SKILL_FLAME_SPIRIT = 78;
	const DWORD PLAYERBOT_SUNGMA_SKILL_BLESSING = 94;
	// The blue potion on a Sung Ma map (GetPlayerBotSungmaManaPercent): the Black-magic Sura at 60% (Dark Protection
	// lives off its mana), the other Suras and the Shamans at 45%, the rest at the caller's 30%.
	const int PLAYERBOT_SUNGMA_CLASS_MANA_BM = 60;
	const int PLAYERBOT_SUNGMA_CLASS_MANA_CASTER = 45;
	// The re-arm (HoldPlayerBotSungmaRearm): after a death or an emergency rest to _REARM_HP health and its build's mana
	// (_REARM_SP_BM / _REARM_SP_CASTER), its self-buffs up, at most _REARM_MAX_MS; after a healed retreat the mana and
	// the buffs only, at most _REARM_RETREAT_MS. A cast every _REARM_CAST_MS at most; the rest's heal 3% a second.
	const int PLAYERBOT_SUNGMA_CLASS_REARM_HP = 85;
	const int PLAYERBOT_SUNGMA_CLASS_REARM_SP_BM = 70;
	const int PLAYERBOT_SUNGMA_CLASS_REARM_SP_CASTER = 50;
	const DWORD PLAYERBOT_SUNGMA_CLASS_REARM_MAX_MS = 25 * 1000;
	const DWORD PLAYERBOT_SUNGMA_CLASS_REARM_RETREAT_MS = 8 * 1000;
	const DWORD PLAYERBOT_SUNGMA_CLASS_REARM_CAST_MS = 1500;
	// The class census once an hour.
	const DWORD PLAYERBOT_SUNGMA_CLASS_CENSUS_MS = 60 * 60 * 1000;

	int GetPlayerBotSungmaClass(LPCHARACTER ch)
	{
		if (!ch)
			return SUNGMA_CLASS_NONE;
		const BYTE group = ch->GetSkillGroup();
		switch (ch->GetJob())
		{
			case JOB_WARRIOR: return group == 1 ? SUNGMA_CLASS_BODY_WARRIOR : (group == 2 ? SUNGMA_CLASS_MENTAL_WARRIOR : SUNGMA_CLASS_NONE);
			case JOB_ASSASSIN: return group == 1 ? SUNGMA_CLASS_BLADE_NINJA : (group == 2 ? SUNGMA_CLASS_ARCHER_NINJA : SUNGMA_CLASS_NONE);
			case JOB_SURA: return group == 1 ? SUNGMA_CLASS_WEAPON_SURA : (group == 2 ? SUNGMA_CLASS_BM_SURA : SUNGMA_CLASS_NONE);
			case JOB_SHAMAN: return group == 1 ? SUNGMA_CLASS_DRAGON_SHAMAN : (group == 2 ? SUNGMA_CLASS_HEAL_SHAMAN : SUNGMA_CLASS_NONE);
#ifdef ENABLE_WOLFMAN_CHARACTER
			case JOB_WOLFMAN: return SUNGMA_CLASS_LYCAN;
#endif
			default: return SUNGMA_CLASS_NONE;
		}
	}

	// The build's own buff that earns it the buffed step (Strong Body, Blessing on itself).
	bool IsPlayerBotSungmaClassBuffed(LPCHARACTER ch, int cls)
	{
		if (cls == SUNGMA_CLASS_MENTAL_WARRIOR)
			return ch->IsAffectFlag(AFF_CHEONGEUN);
		if (cls == SUNGMA_CLASS_DRAGON_SHAMAN)
			return IsPlayerBotBuffAffectOn(ch, PLAYERBOT_SUNGMA_SKILL_BLESSING);
		return false;
	}

	int GetPlayerBotSungmaClassCapacity(LPCHARACTER ch)
	{
		const int cls = GetPlayerBotSungmaClass(ch);
		int mod = PLAYERBOT_SUNGMA_CLASS_CAP[cls];
		if ((cls == SUNGMA_CLASS_MENTAL_WARRIOR || cls == SUNGMA_CLASS_DRAGON_SHAMAN) && IsPlayerBotSungmaClassBuffed(ch, cls))
			mod += PLAYERBOT_SUNGMA_CLASS_CAP_BUFFED;
		return mod;
	}

	int GetPlayerBotSungmaClassFloor(LPCHARACTER ch)
	{
		const int cls = GetPlayerBotSungmaClass(ch);
		int mod = PLAYERBOT_SUNGMA_CLASS_FLOOR[cls];
		if (cls == SUNGMA_CLASS_MENTAL_WARRIOR && IsPlayerBotSungmaClassBuffed(ch, cls))
			mod += PLAYERBOT_SUNGMA_CLASS_FLOOR_BUFFED;
		return mod;
	}

	// The class census's counters (LogPlayerBotSungmaClassCensus); c0*: the last line's snapshot.
	struct TPlayerBotSungmaClassStats
	{
		unsigned int kills, deaths, again, retreats, retreatDeaths, auraDrops, rearms, rearmsReady, rearmsAttacked,
				rearmsTimeout;
		unsigned int c0Kills, c0Deaths, c0Again, c0Retreats, c0RetreatDeaths, c0AuraDrops, c0Rearms, c0RearmsReady,
				c0RearmsAttacked, c0RearmsTimeout;
		unsigned int samples, botSum;
		TPlayerBotSungmaClassStats() : kills(0), deaths(0), again(0), retreats(0), retreatDeaths(0), auraDrops(0), rearms(0),
			rearmsReady(0), rearmsAttacked(0), rearmsTimeout(0), c0Kills(0), c0Deaths(0), c0Again(0), c0Retreats(0),
			c0RetreatDeaths(0), c0AuraDrops(0), c0Rearms(0), c0RearmsReady(0), c0RearmsAttacked(0), c0RearmsTimeout(0),
			samples(0), botSum(0) {}
	};
	TPlayerBotSungmaClassStats s_aPlayerBotSungmaClassStats[SUNGMA_CLASS_COUNT];
	DWORD s_dwPlayerBotSungmaClassCensusSince = 0;
	DWORD s_dwPlayerBotSungmaClassLastSample = 0;

	TPlayerBotSungmaClassStats& GetPlayerBotSungmaClassStats(LPCHARACTER ch)
	{
		return s_aPlayerBotSungmaClassStats[GetPlayerBotSungmaClass(ch)];
	}

	// Flame Spirit off (see above): its aura strikes on through a retreat and an invisible rest. True when it was on.
	bool DropPlayerBotSungmaAura(LPCHARACTER ch, const char* why)
	{
		if (!ch || !ch->IsAffectFlag(AFF_MUYEONG))
			return false;
		ch->RemoveAffect(PLAYERBOT_SUNGMA_SKILL_FLAME_SPIRIT);
		++GetPlayerBotSungmaClassStats(ch).auraDrops;
		sys_log(0, "PLAYERBOT_SUNGMA: aura off pid=%u name=%s map=%ld why=%s hp=%d/%d sp=%d/%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), why ? why : "-", ch->GetHP(), ch->GetMaxHP(), ch->GetSP(),
				ch->GetMaxSP());
		return true;
	}

	// The blue potion's mana per cent (UseManaPotion): a Sung Ma fighter's build floor, else the caller's.
	int GetPlayerBotSungmaManaPercent(LPCHARACTER ch, int otherwise)
	{
		if (!IsPlayerBotSungmaFighter(ch))
			return otherwise;
		const int cls = GetPlayerBotSungmaClass(ch);
		if (cls == SUNGMA_CLASS_BM_SURA)
			return std::max(otherwise, PLAYERBOT_SUNGMA_CLASS_MANA_BM);
		if (cls == SUNGMA_CLASS_WEAPON_SURA || cls == SUNGMA_CLASS_DRAGON_SHAMAN || cls == SUNGMA_CLASS_HEAL_SHAMAN)
			return std::max(otherwise, PLAYERBOT_SUNGMA_CLASS_MANA_CASTER);
		return otherwise;
	}

	// The re-arm's mana target of a build (0: no wait for mana).
	int GetPlayerBotSungmaRearmSp(LPCHARACTER ch)
	{
		const int cls = GetPlayerBotSungmaClass(ch);
		if (cls == SUNGMA_CLASS_BM_SURA)
			return PLAYERBOT_SUNGMA_CLASS_REARM_SP_BM;
		if (cls == SUNGMA_CLASS_WEAPON_SURA || cls == SUNGMA_CLASS_DRAGON_SHAMAN || cls == SUNGMA_CLASS_HEAL_SHAMAN)
			return PLAYERBOT_SUNGMA_CLASS_REARM_SP_CASTER;
		return 0;
	}

	// A re-arm owed (NotePlayerBotSungmaFallen / _Down: after a death or an emergency rest, kind 1; a healed retreat,
	// kind 2). It begins on the first tick the recovery is over (HoldPlayerBotSungmaRearm).
	void QueuePlayerBotSungmaRearm(TPlayerBotSungmaFight& f, BYTE kind)
	{
		if (kind == 2 && f.bRearmPending && f.bRearm == 1)
			return;	// a death's re-arm is not shortened by a retreat's
		f.bRearm = kind;
		f.bRearmPending = true;
		f.dwRearmUntil = 0;
	}

	// ------------------------------------------------------------ the party by the bot

	struct FCountPlayerBotSungmaPartyNear
	{
		LPCHARACTER m_ch;
		int m_radius, m_minHp, m_count;
		FCountPlayerBotSungmaPartyNear(LPCHARACTER ch, int radius, int minHp) : m_ch(ch), m_radius(radius), m_minHp(minHp), m_count(0) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member->IsDead() || GetPlayerBotSungmaHpPercent(member) < m_minHp)
				return;
			if (member != m_ch && DISTANCE_APPROX(member->GetX() - m_ch->GetX(), member->GetY() - m_ch->GetY()) > m_radius)
				return;
			++m_count;
		}
	};

	// The bot and its party's members on its map within radius (alive, at minHp% health or more) - 1 alone.
	int CountPlayerBotSungmaPartyNear(LPCHARACTER ch, int radius, int minHp = 0)
	{
		if (!ch)
			return 0;
		LPPARTY party = ch->GetParty();
		if (!party)
			return 1;
		FCountPlayerBotSungmaPartyNear f(ch, radius, minHp);
		party->ForEachOnMapMember(f, ch->GetMapIndex());
		return std::max(1, f.m_count);
	}

	// The parties of the Sung Ma maps (playerbot_yohara_sungma_party.h): three to five, the objectives' three by the bot.
	const int PLAYERBOT_SUNGMA_PARTY_MIN = 3;
	const int PLAYERBOT_SUNGMA_PARTY_MAX = 5;
	// A member revived stands up where it fell (its party's fight goes on) with this many of them alive this near and no
	// more than PLAYERBOT_SUNGMA_REVIVE_PACK_MAX monsters awake on the spot; else at the safe point.
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: one member alive by it is enough (2 with itself, was 3), within 2 000 (was 1 500):
	// 4 225 of 4 961 revivals of the night of 28 October (00-08, game3) were "at the safe point", 20-40 k units' walk
	// back to the party, and the walk's leave ("far") followed.
	const int PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS = 2000;
	const int PLAYERBOT_SUNGMA_REVIVE_PACK_MAX = 3;
	const int PLAYERBOT_SUNGMA_REVIVE_PARTY_MIN = 2;

	struct FFindPlayerBotSungmaObjective
	{
		LPCHARACTER m_ch;
		bool m_found;
		explicit FFindPlayerBotSungmaObjective(LPCHARACTER ch) : m_ch(ch), m_found(false) {}
		void operator()(LPCHARACTER member)
		{
			if (m_found || !member || member->IsDead() ||
					DISTANCE_APPROX(member->GetX() - m_ch->GetX(), member->GetY() - m_ch->GetY()) > PLAYERBOT_SUNGMA_PARTY_NEAR)
				return;
			TPlayerBotAIStateMap::const_iterator s = s_mapPlayerBotAIStates.find(member->GetPlayerID());
			if (s == s_mapPlayerBotAIStates.end() || s->second.dwTargetVID == 0)
				return;
			LPCHARACTER t = CHARACTER_MANAGER::instance().Find(s->second.dwTargetVID);
			if (t && !t->IsDead() && (t->IsStone() || (t->IsMonster() && t->GetMobRank() >= MOB_RANK_BOSS)))
				m_found = true;
		}
	};

	// The party by the bot is on a stone or a boss (the errands wait for it, unless the belt is empty).
	bool IsPlayerBotSungmaPartyOnObjective(LPCHARACTER ch)
	{
		if (!ch || !ch->GetParty())
			return false;
		FFindPlayerBotSungmaObjective f(ch);
		ch->GetParty()->ForEachOnMapMember(f, ch->GetMapIndex());
		return f.m_found;
	}

	// Out of its party, the engine's way (LeavePlayerBotParty: a leader's going ends it, a pair's too), counted and said.
	void LeavePlayerBotSungmaParty(LPCHARACTER ch, const char* why, bool errand)
	{
		LPPARTY party = ch ? ch->GetParty() : NULL;
		if (!party)
			return;
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
		{
			++st->partyLeaves;
			if (errand)
				++st->partyErrandLeaves;
		}
		sys_log(0, "PLAYERBOT_SUNGMA: party leave pid=%u name=%s map=%ld why=%s members=%u leader=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), why ? why : "-", (unsigned int)party->GetMemberCount(),
				party->GetLeaderPID() == ch->GetPlayerID() ? 1 : 0);
		LeavePlayerBotParty(ch);
	}

	// ------------------------------------------------------------ the monsters round the bot

	struct TPlayerBotSungmaMob
	{
		LPCHARACTER mob;
		long x, y;
		bool aggressive, idle, onMe, boss;
	};

	class FCollectPlayerBotSungmaMobs
	{
		public:
			FCollectPlayerBotSungmaMobs(LPCHARACTER ch, long cx, long cy, int radius, std::vector<TPlayerBotSungmaMob>& out) :
				m_ch(ch), m_cx(cx), m_cy(cy), m_radius(radius), m_out(out) {}
			void operator()(LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
				if (!mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_ch->GetMapIndex() ||
						DISTANCE_APPROX(mob->GetX() - m_cx, mob->GetY() - m_cy) > m_radius)
					return;
				TPlayerBotSungmaMob m;
				m.mob = mob;
				m.x = mob->GetX();
				m.y = mob->GetY();
				m.aggressive = IS_SET(mob->GetMobTable().dwAIFlag, AIFLAG_AGGRESSIVE) != 0;
				m.idle = mob->GetVictim() == NULL;
				m.onMe = mob->GetVictim() == m_ch;
				m.boss = mob->GetMobRank() >= MOB_RANK_BOSS;
				m_out.push_back(m);
			}
		private:
			LPCHARACTER m_ch;
			long m_cx, m_cy;
			int m_radius;
			std::vector<TPlayerBotSungmaMob>& m_out;
	};

	void CollectPlayerBotSungmaMobs(LPCHARACTER ch, int radius, std::vector<TPlayerBotSungmaMob>& out)
	{
		out.clear();
		if (!ch || !ch->GetSectree())
			return;
		FCollectPlayerBotSungmaMobs f(ch, ch->GetX(), ch->GetY(), radius, out);
		ch->GetSectree()->ForEachAround(f);
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_SUNGMA_NEST_V1: the clean ground

	// The test of 27 October (20:15-21:06, game3, 400 cohort bots and the 100 of Hydra's gear): 2 424 deaths, 1 539 of
	// them "again" (a fall within 90 s of the last one). On Namgan, Wawoz, Rozpadlina, Schronienie and Zejscie 70-100% of
	// the deaths came within 3 000 units of the map's safe point (Wawoz 322 of 406 of the cohort and 59 of 59 of
	// Hydra's bots, Rozpadlina 290/373 and 65/69, Schronienie 205/265 and 32/33, Namgan 154/220 and 44/48), with 20-49
	// monsters within 1 400 of the body. The safe point had become a nest: a retreat ran to it with its pack behind
	// (the step's score pulled toward it twice as hard as away from the pack), a monster that loses or kills its victim
	// stays where it stands (StateBattle: SetVictim(NULL), no way home without AIFLAG_RETURN; KILL_AND_GO only wanders
	// 400-1 500 round the body), and every revival stood up into the pack the last one had brought. So the point a
	// revived or retreating bot (and a bot landing on the map) is sent to is the cleanest ground by the safe point at
	// the moment: the safe point itself while nothing stands round it, else the least crowded of the rings round it
	// (PLAYERBOT_SUNGMA_CLEAN_RINGS x 8 directions), reachable from it; looked at once a map every _CLEAN_CACHE_MS.
	const int PLAYERBOT_SUNGMA_CLEAN_RADIUS = 2500;		// the monsters counted round a candidate
	const int PLAYERBOT_SUNGMA_CLEAN_RINGS[] = { 3000, 6000, 9000, 12000 };
	const DWORD PLAYERBOT_SUNGMA_CLEAN_CACHE_MS = 10 * 1000;
	// a monster's weight: awake (on somebody) 6, aggressive and idle 3, any other 1; a ring's distance 1 a ring
	const int PLAYERBOT_SUNGMA_CLEAN_AWAKE = 6;
	const int PLAYERBOT_SUNGMA_CLEAN_AGGRESSIVE = 3;

	class FScorePlayerBotSungmaGround
	{
		public:
			FScorePlayerBotSungmaGround(long mapIndex, long x, long y) : m_map(mapIndex), m_x(x), m_y(y), m_score(0), m_count(0) {}
			void operator()(LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
				if (!mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_map ||
						DISTANCE_APPROX(mob->GetX() - m_x, mob->GetY() - m_y) > PLAYERBOT_SUNGMA_CLEAN_RADIUS)
					return;
				++m_count;
				if (mob->GetVictim() != NULL)
					m_score += PLAYERBOT_SUNGMA_CLEAN_AWAKE;
				else if (IS_SET(mob->GetMobTable().dwAIFlag, AIFLAG_AGGRESSIVE))
					m_score += PLAYERBOT_SUNGMA_CLEAN_AGGRESSIVE;
				else
					++m_score;
			}
			long m_map, m_x, m_y;
			int m_score, m_count;
	};

	// The crowd round (x, y) of a map of this core (the weights above; -1: no ground there).
	int ScorePlayerBotSungmaGround(long mapIndex, long x, long y, int* count = NULL)
	{
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(mapIndex, x, y);
		if (!tree)
			return -1;
		FScorePlayerBotSungmaGround f(mapIndex, x, y);
		tree->ForEachAround(f);
		if (count)
			*count = f.m_count;
		return f.m_score;
	}

	struct TPlayerBotSungmaCleanPoint
	{
		long x, y;
		int score, safeScore;
		DWORD dwAt;
		TPlayerBotSungmaCleanPoint() : x(0), y(0), score(0), safeScore(0), dwAt(0) {}
	};
	std::map<long, TPlayerBotSungmaCleanPoint> s_mapPlayerBotSungmaCleanPoint;

	// The cleanest ground by a Sung Ma map's safe point now (see above); the safe point's own crowd in safeScore.
	bool GetPlayerBotSungmaCleanPoint(long mapIndex, long& x, long& y, int* score = NULL, int* safeScore = NULL)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		long sx = 0, sy = 0;
		if (base != mapIndex || !GetPlayerBotSungmaSafePoint(base, sx, sy))
			return false;
		const DWORD dwNow = get_dword_time();
		TPlayerBotSungmaCleanPoint& c = s_mapPlayerBotSungmaCleanPoint[base];
		if (c.dwAt == 0 || dwNow - c.dwAt >= PLAYERBOT_SUNGMA_CLEAN_CACHE_MS)
		{
			c.dwAt = dwNow ? dwNow : 1;
			c.x = sx;
			c.y = sy;
			c.safeScore = c.score = std::max(0, ScorePlayerBotSungmaGround(base, sx, sy));
			CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(base);
			if (c.score > 0 && navigation.Init(base))
			{
				static const int dirX[8] = { 1000, 707, 0, -707, -1000, -707, 0, 707 };
				static const int dirY[8] = { 0, 707, 1000, 707, 0, -707, -1000, -707 };
				const int rings = (int)(sizeof(PLAYERBOT_SUNGMA_CLEAN_RINGS) / sizeof(PLAYERBOT_SUNGMA_CLEAN_RINGS[0]));
				for (int r = 0; r < rings; ++r)
					for (int d = 0; d < 8; ++d)
					{
						const long px = sx + (long)dirX[d] * PLAYERBOT_SUNGMA_CLEAN_RINGS[r] / 1000;
						const long py = sy + (long)dirY[d] * PLAYERBOT_SUNGMA_CLEAN_RINGS[r] / 1000;
						if (!SECTREE_MANAGER::instance().IsMovablePosition(base, px, py) || !navigation.CanReach(sx, sy, px, py))
							continue;
						const int g = ScorePlayerBotSungmaGround(base, px, py);
						if (g < 0 || g + r + 1 >= c.score)
							continue;
						c.score = g + r + 1;
						c.x = px;
						c.y = py;
					}
			}
		}
		x = c.x;
		y = c.y;
		if (score)
			*score = c.score;
		if (safeScore)
			*safeScore = c.safeScore;
		return true;
	}

	// The idle monsters a blow at (x, y) wakes besides the one struck: its neighbours (the group) and the aggressive ones
	// in sight of the fight. skip: the one struck.
	int CountPlayerBotSungmaWake(const std::vector<TPlayerBotSungmaMob>& mobs, long x, long y, LPCHARACTER skip)
	{
		int n = 0;
		for (size_t i = 0; i < mobs.size(); ++i)
		{
			const TPlayerBotSungmaMob& m = mobs[i];
			if (m.mob == skip || !m.idle)
				continue;
			const int d = DISTANCE_APPROX(m.x - x, m.y - y);
			if (d <= PLAYERBOT_SUNGMA_PACK_RADIUS || (m.aggressive && d <= PLAYERBOT_SUNGMA_AGGRO_RADIUS))
				++n;
		}
		return n;
	}

	// The monsters on the bot now (centroid and the nearest).
	int CountPlayerBotSungmaAttackers(LPCHARACTER ch, const std::vector<TPlayerBotSungmaMob>& mobs, long& cx, long& cy,
			LPCHARACTER* nearest)
	{
		int n = 0, best = INT_MAX;
		long long sx = 0, sy = 0;
		if (nearest)
			*nearest = NULL;
		for (size_t i = 0; i < mobs.size(); ++i)
		{
			const TPlayerBotSungmaMob& m = mobs[i];
			if (!m.onMe)
				continue;
			const int d = DISTANCE_APPROX(m.x - ch->GetX(), m.y - ch->GetY());
			if (d > PLAYERBOT_SUNGMA_ATTACKER_RADIUS)
				continue;
			++n;
			sx += m.x;
			sy += m.y;
			if (nearest && d < best)
			{
				best = d;
				*nearest = m.mob;
			}
		}
		cx = n ? (long)(sx / n) : ch->GetX();
		cy = n ? (long)(sy / n) : ch->GetY();
		return n;
	}

	// The weakest monsters' level of a Sung Ma map (0: none).
	int GetPlayerBotSungmaMobFloor(long mapIndex)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_MOB_FLOORS) / sizeof(PLAYERBOT_SUNGMA_MOB_FLOORS[0]); ++i)
			if (PLAYERBOT_SUNGMA_MOB_FLOORS[i].lMap == base)
				return PLAYERBOT_SUNGMA_MOB_FLOORS[i].iLevel;
		return 0;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the floor, the pull, the element

	int GetPlayerBotSungmaDifficulty(long mapIndex)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_F2_DIFFICULTY) / sizeof(PLAYERBOT_SUNGMA_F2_DIFFICULTY[0]); ++i)
			if (PLAYERBOT_SUNGMA_F2_DIFFICULTY[i].lMap == base)
				return PLAYERBOT_SUNGMA_F2_DIFFICULTY[i].iFloorAdd;
		return 0;
	}

	// The health (per cent) the bot runs at: its real danger floor (see PLAYERBOT_SUNGMA_F2_FLOOR_*). partyNear: the bot
	// and its members by it (CountPlayerBotSungmaPartyNear).
	int GetPlayerBotSungmaFloorHp(LPCHARACTER ch, int partyNear)
	{
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		if (red < PLAYERBOT_SUNGMA_CAPACITY_LOW_RED)
			return PLAYERBOT_SUNGMA_F2_FLOOR_NO_RED;
		int floorHp = (partyNear >= 2 ? PLAYERBOT_SUNGMA_F2_FLOOR_PARTY : PLAYERBOT_SUNGMA_F2_FLOOR_LONE) +
				GetPlayerBotSungmaDifficulty(ch->GetMapIndex());
		if (ch->GetMaxHP() < PLAYERBOT_SUNGMA_F2_WEAK_MAX_HP)
			floorHp += PLAYERBOT_SUNGMA_F2_FLOOR_WEAK;
		int champion = 0;
#ifdef ENABLE_CONQUEROR_LEVEL
		champion = (int)ch->GetConquerorLevel();
#endif
		const long base = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		const int bandFloor = GetPlayerBotSungmaBandFloor(base);
		if (bandFloor > 0 && champion - bandFloor >= PLAYERBOT_SUNGMA_F2_BAND_HIGH_LEVELS)
			floorHp -= PLAYERBOT_SUNGMA_F2_FLOOR_BAND_HIGH;
		floorHp += GetPlayerBotSungmaClassFloor(ch);	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the build's step
		return std::max(15, std::min(floorHp, PLAYERBOT_SUNGMA_F2_FLOOR_NO_RED));
	}

	// The generic retreat's health on a Sung Ma map (playerbot_manager.cpp's tick): the fighter's floor, else the caller's.
	int GetPlayerBotSungmaRetreatPercent(LPCHARACTER ch, int otherwise)
	{
		if (!IsPlayerBotSungmaFighter(ch))
			return otherwise;
		// over the highest floor there is no retreat to weigh (the bag's potions are not counted every tick)
		if (GetPlayerBotSungmaHpPercent(ch) > PLAYERBOT_SUNGMA_F2_FLOOR_NO_RED)
			return 0;
		return GetPlayerBotSungmaFloorHp(ch, CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR, 30));
	}

	// The element of a monster, 0-5 in PLAYERBOT_SUNGMA_ELEMENTS' order (lightning, fire, ice, wind, earth, dark -
	// playerbot_yohara_elements.h's), -1 none.
	bool IsPlayerBotSungmaMobOfElement(LPCHARACTER mob, int element)
	{
		return mob && element >= 0 && element < (int)(sizeof(PLAYERBOT_SUNGMA_ELEMENTS) / sizeof(PLAYERBOT_SUNGMA_ELEMENTS[0])) &&
				mob->IsRaceFlag(PLAYERBOT_SUNGMA_ELEMENTS[element].dwFlag);
	}

	// GetPlayerBotHuntElement's answer as an index of PLAYERBOT_SUNGMA_ELEMENTS (-1 none). Its encoding: 1-6 in the order
	// above (0 none); a POINT_ENCHANT_* or POINT_RESIST_* of an element is read as that element too.
	int DecodePlayerBotSungmaHuntElement(BYTE element)
	{
		if (element == 0)
			return -1;
		const int count = (int)(sizeof(PLAYERBOT_SUNGMA_ELEMENTS) / sizeof(PLAYERBOT_SUNGMA_ELEMENTS[0]));
		if (element <= count)
			return element - 1;
		for (int i = 0; i < count; ++i)
			if (element == PLAYERBOT_SUNGMA_ELEMENTS[i].bEnchant || element == PLAYERBOT_SUNGMA_ELEMENTS[i].bResist)
				return i;
		return -1;
	}

	// The element the bot hunts: a party member its leader's (the party fights one spot), else its own; -1 none.
	int GetPlayerBotSungmaHuntElement(LPCHARACTER ch)
	{
		if (!ch)
			return -1;
		LPPARTY party = ch->GetParty();
		LPCHARACTER leader = party ? party->GetLeaderCharacter() : NULL;
		if (leader && leader != ch && leader->GetMapIndex() == ch->GetMapIndex() && leader->GetDesc() && leader->GetDesc()->IsBot())
		{
			const int e = DecodePlayerBotSungmaHuntElement(GetPlayerBotHuntElement(leader));
			if (e >= 0)
				return e;
		}
		return DecodePlayerBotSungmaHuntElement(GetPlayerBotHuntElement(ch));
	}

	// The bot's armour against a monster (see PLAYERBOT_SUNGMA_F2_CAP_ARMOUR_*): block + dodge / 2 + the piercing
	// resistance + its resistance to the monster's element / 2 (to its hunt element's, mob NULL).
	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1 (the owner's point 7, 28 October 2026): + the average-damage resistance (POINT_
	// NORMAL_HIT_DEFEND_BONUS: a per cent off every normal blow, char_battle.cpp - a monster's ordinary hit is one) + the
	// Blessing's damage resistance / 2 (POINT_RESIST_NORMAL_DAMAGE, counted by the engine only under the Blessing) + the
	// skill-damage resistance / 2 (POINT_SKILL_DEFEND_BONUS: the monsters' skills come seldom) + the defence per cent / 4
	// (POINT_DEF_BONUS, the per cent on the defence value). Today these come from the alchemy (SKILL_DEFEND 10,
	// NORMAL_HIT_DEFEND 10, RESIST_PENETRATE 8 a stone, dragon_soul_table.txt), the Blessing and the shop's items - no
	// ordinary bonus line rolls them (world.item_attr, both modes).
	const int PLAYERBOT_SUNGMA_CLASS_ARMOUR_SKILL_DIV = 2;
	const int PLAYERBOT_SUNGMA_CLASS_ARMOUR_BLESSING_DIV = 2;
	const int PLAYERBOT_SUNGMA_CLASS_ARMOUR_DEF_PCT_DIV = 4;
	int GetPlayerBotSungmaArmour(LPCHARACTER ch, LPCHARACTER mob)
	{
		int resist = 0;
		const int count = (int)(sizeof(PLAYERBOT_SUNGMA_ELEMENTS) / sizeof(PLAYERBOT_SUNGMA_ELEMENTS[0]));
		if (mob)
		{
			for (int i = 0; i < count; ++i)
				if (mob->IsRaceFlag(PLAYERBOT_SUNGMA_ELEMENTS[i].dwFlag))
					resist = std::max(resist, (int)ch->GetPoint(PLAYERBOT_SUNGMA_ELEMENTS[i].bResist));
		}
		else
		{
			const int e = GetPlayerBotSungmaHuntElement(ch);
			if (e >= 0)
				resist = (int)ch->GetPoint(PLAYERBOT_SUNGMA_ELEMENTS[e].bResist);
		}
		int armour = std::max(0, (int)ch->GetPoint(POINT_BLOCK)) + std::max(0, (int)ch->GetPoint(POINT_DODGE)) / 2 +
				std::max(0, (int)ch->GetPoint(POINT_RESIST_PENETRATE)) + std::max(0, resist) / 2;
		// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the damage resistances and the defence per cent (above)
		armour += std::max(0, std::min(99, (int)ch->GetPoint(POINT_NORMAL_HIT_DEFEND_BONUS)));
		armour += std::max(0, std::min(99, (int)ch->GetPoint(POINT_SKILL_DEFEND_BONUS))) / PLAYERBOT_SUNGMA_CLASS_ARMOUR_SKILL_DIV;
		if (ch->IsAffectFlag(AFF_HOSIN))
			armour += std::max(0, (int)ch->GetPoint(POINT_RESIST_NORMAL_DAMAGE)) / PLAYERBOT_SUNGMA_CLASS_ARMOUR_BLESSING_DIV;
		armour += std::max(0, (int)ch->GetPoint(POINT_DEF_BONUS)) / PLAYERBOT_SUNGMA_CLASS_ARMOUR_DEF_PCT_DIV;
		return armour;
	}

	// What the bot takes alone at full health (see PLAYERBOT_SUNGMA_F2_CAP_*): its maximum health, the map, its armour.
	int GetPlayerBotSungmaLoneCapacity(LPCHARACTER ch, LPCHARACTER mob = NULL)
	{
		int cap = ch->GetMaxHP() >= PLAYERBOT_SUNGMA_F2_CAP_HP_4 ? 4 : (ch->GetMaxHP() >= PLAYERBOT_SUNGMA_F2_CAP_HP_3 ? 3 : 2);
		if (GetPlayerBotSungmaDifficulty(ch->GetMapIndex()) >= PLAYERBOT_SUNGMA_F2_HARD ||
				GetPlayerBotSungmaMobFloor(ch->GetMapIndex()) >= PLAYERBOT_SUNGMA_CAPACITY_HARD_LEVEL)
			--cap;
		const int armour = GetPlayerBotSungmaArmour(ch, mob);
		if (armour >= PLAYERBOT_SUNGMA_F2_CAP_ARMOUR_2)
			cap += 2;
		else if (armour >= PLAYERBOT_SUNGMA_F2_CAP_ARMOUR_1)
			++cap;
		cap += GetPlayerBotSungmaClassCapacity(ch);	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the build's step
		return std::max(2, std::min(cap, PLAYERBOT_SUNGMA_F2_CAP_LONE_MAX));
	}

	// A Sung Ma fighter's gap between two skills (ExecutePlayerBotAttackSkill), else the caller's.
	DWORD GetPlayerBotSungmaSkillGap(LPCHARACTER ch, DWORD gap)
	{
		return IsPlayerBotSungmaFighter(ch) ? gap * PLAYERBOT_SUNGMA_F2_SKILL_GAP_PERCENT / 100 : gap;
	}

	struct FCountPlayerBotSungmaAround
	{
		LPCHARACTER m_ch, m_target;
		int m_count;
		FCountPlayerBotSungmaAround(LPCHARACTER ch, LPCHARACTER target) : m_ch(ch), m_target(target), m_count(0) {}
		void operator()(LPENTITY entity)
		{
			if (!entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
			if (mob == m_target || !mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_ch->GetMapIndex() ||
					DISTANCE_APPROX(mob->GetX() - m_target->GetX(), mob->GetY() - m_target->GetY()) > PLAYERBOT_SUNGMA_F2_AREA_RADIUS)
				return;
			++m_count;
		}
	};

	// The area skills first (ExecutePlayerBotAttackSkill): a Sung Ma fighter at a monster with company.
	bool WantsPlayerBotSungmaAreaSkills(LPCHARACTER ch, LPCHARACTER target)
	{
		if (!target || !target->IsMonster() || !IsPlayerBotSungmaFighter(ch) || !target->GetSectree())
			return false;
		FCountPlayerBotSungmaAround f(ch, target);
		target->GetSectree()->ForEachAround(f);
		return f.m_count + 1 >= PLAYERBOT_SUNGMA_F2_AREA_MIN;
	}

	struct FCountPlayerBotSungmaHubMobs
	{
		long m_map, m_x, m_y;
		int m_element, m_count, m_hunt;
		FCountPlayerBotSungmaHubMobs(long mapIndex, long x, long y, int element) : m_map(mapIndex), m_x(x), m_y(y),
			m_element(element), m_count(0), m_hunt(0) {}
		void operator()(LPENTITY entity)
		{
			if (!entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
			if (!mob->IsMonster() || mob->IsDead() || mob->IsStone() || mob->GetMapIndex() != m_map ||
					mob->GetMobRank() >= MOB_RANK_BOSS ||
					DISTANCE_APPROX(mob->GetX() - m_x, mob->GetY() - m_y) > PLAYERBOT_SUNGMA_F2_HUB_RADIUS)
				return;
			++m_count;
			if (IsPlayerBotSungmaMobOfElement(mob, m_element))
				++m_hunt;
		}
	};

	// ChoosePlayerBotHuntingHub's score of an ordinary Sung Ma spot (playerbot_wandering.h): the monsters standing there
	// now - those of the bot's hunt element (PLAYERBOT_SUNGMA_F2_HUB_ELEMENT_PERCENT x their share), and for a party's
	// leader with two members or more the crowd itself (PLAYERBOT_SUNGMA_F2_HUB_DENSE_*): the party goes where it is
	// densest, a lone bot where its edge-of-the-pack rule has work.
	int AdjustPlayerBotSungmaHubScore(LPCHARACTER ch, long x, long y, int score)
	{
		if (!ch || score <= 0 || !IsPlayerBotSungmaFighter(ch))
			return score;
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(ch->GetMapIndex(), x, y);
		if (!tree)
			return score;
		const int element = GetPlayerBotSungmaHuntElement(ch);
		FCountPlayerBotSungmaHubMobs f(ch->GetMapIndex(), x, y, element);
		tree->ForEachAround(f);
		long long adjusted = score;
		if (element >= 0 && f.m_count > 0)
			adjusted = adjusted * (100 + PLAYERBOT_SUNGMA_F2_HUB_ELEMENT_PERCENT * f.m_hunt / f.m_count) / 100;
		LPPARTY party = ch->GetParty();
		if (party && party->GetLeaderPID() == ch->GetPlayerID() && party->GetMemberCount() >= 3)
			adjusted = adjusted * (100 + PLAYERBOT_SUNGMA_F2_HUB_DENSE_PERCENT * std::min(f.m_count, PLAYERBOT_SUNGMA_F2_HUB_DENSE_MAX)) / 100;
		return (int)std::min<long long>(adjusted, INT_MAX / 2);
	}

	// A red potion drunk by a Sung Ma fighter (the census's potions).
	void NotePlayerBotSungmaPotion(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotSungmaBotMap(ch->GetMapIndex()) || !IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
			return;
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			++st->potions;
	}

	// How many monsters at once the bot takes (see PLAYERBOT_SUNGMA_CAPACITY_*).
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: alone GetPlayerBotSungmaLoneCapacity (2-5, was 3 or 2 on the hard maps).
	int GetPlayerBotSungmaCapacity(LPCHARACTER ch, int partyNear)
	{
		const int hp = GetPlayerBotSungmaHpPercent(ch);
		const int lone = GetPlayerBotSungmaLoneCapacity(ch);
		int cap = hp >= 70 ? lone : (hp >= 50 ? lone - 1 : 1);
		cap = std::max(cap, 1);
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		if (red < PLAYERBOT_SUNGMA_CAPACITY_LOW_RED)
			cap = std::min(cap, 1);
		cap += std::max(0, partyNear - 1) * PLAYERBOT_SUNGMA_CAPACITY_MEMBER;
		return std::min(cap, PLAYERBOT_SUNGMA_CAPACITY_MAX);
	}

	// The level the bot's band fights on its map (see PLAYERBOT_SUNGMA_MOB_FLOORS).
	int GetPlayerBotSungmaBandMobLevel(LPCHARACTER ch)
	{
		const long base = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		const int floorLevel = GetPlayerBotSungmaMobFloor(base);
		if (!floorLevel)
			return (int)ch->GetLevel();
		int champion = 0;
#ifdef ENABLE_CONQUEROR_LEVEL
		champion = (int)ch->GetConquerorLevel();
#endif
		return floorLevel + std::max(0, champion - GetPlayerBotSungmaBandFloor(base)) / PLAYERBOT_SUNGMA_LEVEL_PER_CHAMPION;
	}

	// The bot's power against the monster's element (its talisman's and the rest - the enchant points), and its
	// resistance to the element the monster strikes with. 0/0: no element.
	void GetPlayerBotSungmaElementEdge(LPCHARACTER ch, LPCHARACTER mob, int& power, int& resist)
	{
		power = resist = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_ELEMENTS) / sizeof(PLAYERBOT_SUNGMA_ELEMENTS[0]); ++i)
		{
			const TPlayerBotSungmaElement& e = PLAYERBOT_SUNGMA_ELEMENTS[i];
			if (!mob->IsRaceFlag(e.dwFlag))
				continue;
			power = std::max(power, (int)ch->GetPoint(e.bEnchant));
			resist = std::max(resist, (int)ch->GetPoint(e.bResist));
		}
	}

	// MovePlayerBotSungmaRevived: a member stands up where it fell (see PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS).
	bool IsPlayerBotSungmaRevivedInParty(LPCHARACTER ch)
	{
		if (!ch || !ch->GetParty() ||
				CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS, 30) < PLAYERBOT_SUNGMA_REVIVE_PARTY_MIN)
			return false;
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_AGGRO_RADIUS, mobs);
		int awake = 0;
		for (size_t i = 0; i < mobs.size(); ++i)
			if (mobs[i].onMe || (mobs[i].idle && mobs[i].aggressive))
				++awake;
		return awake <= PLAYERBOT_SUNGMA_REVIVE_PACK_MAX;
	}

	// ------------------------------------------------------------ the spot it pulled too much on

	bool IsPlayerBotSungmaSpotAvoided(LPCHARACTER ch, long x, long y, DWORD dwNow)
	{
		if (!ch)
			return false;
		std::map<DWORD, TPlayerBotSungmaFight>::const_iterator f = s_mapPlayerBotSungmaFight.find(ch->GetPlayerID());
		if (f == s_mapPlayerBotSungmaFight.end() || f->second.dwAvoidUntil == 0 || (int)(f->second.dwAvoidUntil - dwNow) <= 0 ||
				f->second.lAvoidMap != ch->GetMapIndex())
			return false;
		return DISTANCE_APPROX(x - f->second.lAvoidX, y - f->second.lAvoidY) <= PLAYERBOT_SUNGMA_AVOID_RADIUS;
	}

	// ------------------------------------------------------------ the belt and the retreat

	// The health the belt is drunk at (UseHealthPotion): a Sung Ma fighter's, else the caller's.
	int GetPlayerBotSungmaPotionPercent(LPCHARACTER ch, int otherwise)
	{
		return IsPlayerBotSungmaFighter(ch) ? std::max(otherwise, PLAYERBOT_SUNGMA_POTION_PERCENT) : otherwise;
	}

	// Whether the bot breaks off its fight now (the tick's survival pass, before the generic 35%): the threat to run from,
	// or NULL. A stone nearly broken is finished (bFinishingStone, the caller's).
	LPCHARACTER CheckPlayerBotSungmaRetreat(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!IsPlayerBotSungmaFighter(ch) || state.bTacticalRetreat || state.bRecoveringAfterDeath || ch->IsDead())
			return NULL;
		// looked at every PLAYERBOT_SUNGMA_RETREAT_LOOK_MS (the scan of the sectors round it), each tick once it is low
		TPlayerBotSungmaFight& f = s_mapPlayerBotSungmaFight[ch->GetPlayerID()];
		const int hp = GetPlayerBotSungmaHpPercent(ch);
		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: over 60% nothing sends it off but a pull of more than it takes - looked at on
		// the clock; under it every tick
		if ((int)(dwNow - f.dwNextRetreatLook) < 0 && hp > PLAYERBOT_SUNGMA_RETREAT_PACK_HP)
			return NULL;
		f.dwNextRetreatLook = dwNow + PLAYERBOT_SUNGMA_RETREAT_LOOK_MS;
		// the fall since the last look (kept for PLAYERBOT_SUNGMA_RETREAT_FALL_MS, then the look starts again)
		int fall = 0;
		if (f.dwHpSeenAt != 0 && dwNow - f.dwHpSeenAt <= PLAYERBOT_SUNGMA_RETREAT_FALL_MS)
			fall = f.iHpSeen - hp;
		else
		{
			f.iHpSeen = hp;
			f.dwHpSeenAt = dwNow ? dwNow : 1;
		}
		if (hp > f.iHpSeen)
		{
			f.iHpSeen = hp;
			f.dwHpSeenAt = dwNow ? dwNow : 1;
		}
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_ATTACKER_RADIUS, mobs);
		long cx = 0, cy = 0;
		LPCHARACTER nearest = NULL;
		const int attackers = CountPlayerBotSungmaAttackers(ch, mobs, cx, cy, &nearest);
		if (attackers == 0 || !nearest)
			return NULL;
		const int partyNear = CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR, 30);
		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the bot's own floor and pull (PLAYERBOT_SUNGMA_F2_*), not the fixed 45/35%,
		// 60% with a pack, 90% when pulled and 70% on a fall of the first fight rules
		const int fullCap = GetPlayerBotSungmaLoneCapacity(ch, nearest) +
				std::max(0, partyNear - 1) * PLAYERBOT_SUNGMA_CAPACITY_MEMBER;
		const int floorHp = GetPlayerBotSungmaFloorHp(ch, partyNear);
		const bool turned = f.dwTurnHoldUntil != 0 && (int)(dwNow - f.dwTurnHoldUntil) < 0;
		const char* why = NULL;
		if (hp <= floorHp)
			why = "hp";
		else if (!turned && attackers > fullCap && hp <= floorHp + PLAYERBOT_SUNGMA_F2_PACK_OVER)
			why = "pack";
		else if (!turned && attackers >= fullCap + PLAYERBOT_SUNGMA_F2_PULLED_EXTRA && hp <= floorHp + PLAYERBOT_SUNGMA_F2_PULLED_OVER)
			why = "pulled";
		else if (attackers >= 2 && fall >= PLAYERBOT_SUNGMA_F2_FALL_PERCENT && hp <= floorHp + PLAYERBOT_SUNGMA_F2_FALL_OVER)
			why = "fall";
		if (!why)
			return NULL;
		f.bRetreat = true;
		strlcpy(f.szRetreatWhy, why, sizeof(f.szRetreatWhy));
		f.iRetreatAttackers = attackers;
		TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex());
		if (st)
		{
			if (why[0] == 'h' || why[0] == 'f')
				++st->retreatsHp;
			else if (why[1] == 'a')
				++st->retreatsPack;
			else
				++st->retreatsPulled;
		}
		// Too much for a lone bot (or a party that came apart): that ground is left for a while.
		if ((why[0] == 'p') && partyNear < PLAYERBOT_SUNGMA_PARTY_MIN)
		{
			f.lAvoidMap = ch->GetMapIndex();
			f.lAvoidX = cx;
			f.lAvoidY = cy;
			f.dwAvoidUntil = dwNow + PLAYERBOT_SUNGMA_AVOID_MS;
			if (st)
				++st->avoids;
		}
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		sys_log(0, "PLAYERBOT_SUNGMA: retreat pid=%u name=%s map=%ld why=%s hp=%d/%d fall=%d attackers=%d party_near=%d red=%u pos=(%ld,%ld) pack=(%ld,%ld)",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), why, ch->GetHP(), ch->GetMaxHP(), fall, attackers, partyNear,
				(unsigned int)red, ch->GetX(), ch->GetY(), cx, cy);
		f.dwHpSeenAt = 0;
		return nearest;
	}

	// The emergency rest (20% health, no monster holding the bot) on a Sung Ma map: with a monster awake or an aggressive
	// one in sight it is a retreat instead (the threat - the nearest), not an invisible rest on the spot. The test of
	// 22 October (19:44-20:15, game3): of 217 deaths 89 came in a retreat and 31 within a minute of an emergency rest -
	// on Dongan, Wawoz, Rozpadlina and Schronienie the usual death was "retreat, emergency rest, dead" (51 of 152), the
	// aggressive packs waiting out the five invisible seconds beside it.
	LPCHARACTER FindPlayerBotSungmaDanger(LPCHARACTER ch, DWORD dwNow)
	{
		if (!IsPlayerBotSungmaFighter(ch) || ch->IsDead())
			return NULL;
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_AGGRO_RADIUS + PLAYERBOT_SUNGMA_PACK_RADIUS, mobs);
		LPCHARACTER best = NULL;
		int bestDist = INT_MAX;
		for (size_t i = 0; i < mobs.size(); ++i)
		{
			const TPlayerBotSungmaMob& m = mobs[i];
			const int d = DISTANCE_APPROX(m.x - ch->GetX(), m.y - ch->GetY());
			if ((m.onMe || (m.idle && m.aggressive && d <= PLAYERBOT_SUNGMA_AGGRO_RADIUS)) && d < bestDist)
			{
				best = m.mob;
				bestDist = d;
			}
		}
		if (!best)
			return NULL;
		TPlayerBotSungmaFight& f = s_mapPlayerBotSungmaFight[ch->GetPlayerID()];
		f.bRetreat = true;
		strlcpy(f.szRetreatWhy, "low", sizeof(f.szRetreatWhy));
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			++st->retreatsHp;
		f.dwLastDown = dwNow ? dwNow : 1;
		sys_log(0, "PLAYERBOT_SUNGMA: retreat pid=%u name=%s map=%ld why=low hp=%d/%d danger=%s dist=%d pos=(%ld,%ld)",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetHP(), ch->GetMaxHP(), best->GetName(), bestDist,
				ch->GetX(), ch->GetY());
		return best;
	}

	// HandlePlayerBotTacticalRetreat's part for a Sung Ma fighter (any retreat it is in): -1 not its, 0 the retreat over,
	// 1 the tick is the retreat's. Away from the monsters on it, toward its map's safe point, past no idle aggressive
	// pack; resting (Stop, the same 3% a second as the generic retreat) once nobody is on it, until healed.
	int HandlePlayerBotSungmaRetreat(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!state.bTacticalRetreat || !IsPlayerBotSungmaFighter(ch))
			return -1;
		TPlayerBotSungmaFight& f = s_mapPlayerBotSungmaFight[ch->GetPlayerID()];
		SetPlayerBotAction(state, BOT_ACTION_RECOVER, dwNow);
		// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: a retreat of the class census (once), and no Flame Spirit through it - its aura
		// strikes the pack the bot runs from every 3 s (see the class section)
		if (state.dwRetreatStartedTime != 0 && f.dwRetreatCounted != state.dwRetreatStartedTime)
		{
			f.dwRetreatCounted = state.dwRetreatStartedTime;
			++GetPlayerBotSungmaClassStats(ch).retreats;
		}
		DropPlayerBotSungmaAura(ch, f.szRetreatWhy[0] ? f.szRetreatWhy : "retreat");
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_ATTACKER_RADIUS + PLAYERBOT_SUNGMA_RETREAT_STEP, mobs);
		long cx = 0, cy = 0;
		const int attackers = CountPlayerBotSungmaAttackers(ch, mobs, cx, cy, NULL);
		const int hp = GetPlayerBotSungmaHpPercent(ch);
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the cleanest ground by the safe point, not the safe point itself (the nest)
		long sx = 0, sy = 0;
		const bool safe = GetPlayerBotSungmaCleanPoint(ch->GetMapIndex(), sx, sy) &&
				DISTANCE_APPROX(ch->GetX() - sx, ch->GetY() - sy) <= PLAYERBOT_SUNGMA_SAFE_MAX;
		const int toSafe = safe ? DISTANCE_APPROX(ch->GetX() - sx, ch->GetY() - sy) : INT_MAX;
		const DWORD el = state.dwRetreatStartedTime ? dwNow - state.dwRetreatStartedTime : 0;
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: a lost retreat - still held by two or more after _ESCAPE_AFTER_MS, at
		// _ESCAPE_HP% or under - ends the way a person ends it, by the teleport (the scroll / the ring home): onto the clean
		// ground, out of the pack's chase (StateBattle gives a victim up at 4 000 units), the pack left where it stood. The
		// test of 27 October: 589 of 2 424 deaths came in a retreat (the cause "retreat"), most of the "again" ones after
		// a retreat that had led the pack to the safe point; a step of 1 500 units every 1.5 s does not outrun monsters of
		// move_speed 100 that hit for 25-30% of a cohort bot a second.
		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the escape at the bot's floor (or _ESCAPE_HP, the higher)
		const int partyNear = CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR, 30);
		const int floorHp = GetPlayerBotSungmaFloorHp(ch, partyNear);
		long ex = 0, ey = 0;
		if (attackers >= PLAYERBOT_SUNGMA_ESCAPE_ATTACKERS && hp <= std::max(PLAYERBOT_SUNGMA_ESCAPE_HP, floorHp) &&
				el >= PLAYERBOT_SUNGMA_ESCAPE_AFTER_MS &&
				(f.dwLastEscape == 0 || dwNow - f.dwLastEscape >= PLAYERBOT_SUNGMA_ESCAPE_GAP_MS) &&
				GetPlayerBotSungmaCleanPoint(ch->GetMapIndex(), ex, ey) &&
				DISTANCE_APPROX(ch->GetX() - ex, ch->GetY() - ey) >= PLAYERBOT_SUNGMA_ESCAPE_MIN_DIST)
		{
			long ox = 0, oy = 0;
			GetPlayerBotStableOffset(ch->GetPlayerID(), 0x45534350U, 50, 300, ox, oy);
			f.dwLastEscape = dwNow ? dwNow : 1;
			if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
				++st->escapes;
			sys_log(0, "PLAYERBOT_SUNGMA: escape pid=%u name=%s map=%ld why=%s hp=%d/%d attackers=%d took_s=%u from=(%ld,%ld) to=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), f.szRetreatWhy[0] ? f.szRetreatWhy : "generic", ch->GetHP(),
					ch->GetMaxHP(), attackers, el / 1000, ch->GetX(), ch->GetY(), ex + ox, ey + oy);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			ch->Show(ch->GetMapIndex(), ex + ox, ey + oy, 0);
			state.dwNextRetreatMoveTime = dwNow + PLAYERBOT_SUNGMA_RETREAT_MOVE_MS;
			return 1;
		}
		// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: a retreat its pack keeps up with is a fight again (see PLAYERBOT_SUNGMA_F2_TURN_*):
		// the potions hold it either way, and only a fight kills the pack.
		const bool turn = attackers > 0 && el >= PLAYERBOT_SUNGMA_F2_TURN_AFTER_MS &&
				hp >= floorHp + PLAYERBOT_SUNGMA_F2_TURN_OVER &&
				attackers <= GetPlayerBotSungmaLoneCapacity(ch) + std::max(0, partyNear - 1) * PLAYERBOT_SUNGMA_CAPACITY_MEMBER + 1;
		if ((attackers == 0 && hp >= PLAYERBOT_SUNGMA_F2_END_HP) || turn || el >= PLAYERBOT_SUNGMA_RETREAT_MAX_MS)
		{
			sys_log(0, "PLAYERBOT_SUNGMA: retreat over pid=%u name=%s map=%ld why=%s hp=%d/%d attackers=%d took_s=%u at_safe=%d reason=%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), f.szRetreatWhy[0] ? f.szRetreatWhy : "generic", ch->GetHP(),
					ch->GetMaxHP(), attackers, el / 1000, toSafe <= PLAYERBOT_SUNGMA_SAFE_REACHED ? 1 : 0,
					attackers == 0 ? "healed" : (turn ? "turn" : "timeout"));
			if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			{
				if (toSafe <= PLAYERBOT_SUNGMA_SAFE_REACHED)
					++st->retreatsSafe;
				++st->retreatsEnded;
				st->retreatMs += el;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
				NotePlayerBotG0StruggleRetreat(ch, el);	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the bot's own window
#endif
				if (turn && attackers > 0)
					++st->turns;
			}
			if (turn && attackers > 0)
				f.dwTurnHoldUntil = dwNow + PLAYERBOT_SUNGMA_F2_TURN_HOLD_MS;
			// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: healed with nobody on it - its mana and its buffs before the next fight
			else if (attackers == 0)
				QueuePlayerBotSungmaRearm(f, 2);
			f.bRetreat = false;
			f.szRetreatWhy[0] = '\0';
			state.bTacticalRetreat = false;
			state.dwRetreatStartedTime = 0;
			state.dwRetreatThreatVID = 0;
			state.dwNextRetreatMoveTime = 0;
			ClearPlayerBotRoute(state, true);
			return 0;
		}
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		// Nobody on it: rest where it is unless an idle aggressive monster is in sight of it.
		int wakeHere = 0;
		for (size_t i = 0; i < mobs.size(); ++i)
			if (mobs[i].idle && mobs[i].aggressive &&
					DISTANCE_APPROX(mobs[i].x - ch->GetX(), mobs[i].y - ch->GetY()) <= PLAYERBOT_SUNGMA_AGGRO_RADIUS)
				++wakeHere;
		if (attackers == 0 && wakeHere == 0)
		{
			if (dwNow >= state.dwNextRecoveryHealTime)
			{
				const int heal = std::max(1, ch->GetMaxHP() * 3 / 100);
				ch->PointChange(POINT_HP, std::min(heal, ch->GetMaxHP() - ch->GetHP()));
				state.dwNextRecoveryHealTime = dwNow + 1000;
			}
			if (ch->IsStateMove())
				ch->Stop();
			return 1;
		}
		if (dwNow < state.dwNextRetreatMoveTime)
			return 1;
		state.dwNextRetreatMoveTime = dwNow + PLAYERBOT_SUNGMA_RETREAT_MOVE_MS;
		// Eight steps round it: the farthest from the monsters on it, the nearest to the safe point, the fewest idle
		// aggressive monsters by the step.
		static const int dirX[8] = { 1000, 707, 0, -707, -1000, -707, 0, 707 };
		static const int dirY[8] = { 0, 707, 1000, 707, 0, -707, -1000, -707 };
		long bestX = 0, bestY = 0;
		long long bestScore = LLONG_MIN;
		for (int i = 0; i < 8; ++i)
		{
			const long x = ch->GetX() + dirX[i] * PLAYERBOT_SUNGMA_RETREAT_STEP / 1000;
			const long y = ch->GetY() + dirY[i] * PLAYERBOT_SUNGMA_RETREAT_STEP / 1000;
			if (!IsPlayerBotReachable(ch->GetMapIndex(), ch->GetX(), ch->GetY(), x, y))
				continue;
			long long score = attackers ? (long long)DISTANCE_APPROX(x - cx, y - cy) : 0;
			// MT2009_PLUS_BOT_SUNGMA_NEST_V1: toward the safe ground only with nobody on it - a pack led there stays there
			if (safe && attackers == 0)
				score += (long long)(toSafe - DISTANCE_APPROX(x - sx, y - sy)) * 2;
			for (size_t m = 0; m < mobs.size(); ++m)
				if (mobs[m].idle && mobs[m].aggressive &&
						DISTANCE_APPROX(mobs[m].x - x, mobs[m].y - y) <= PLAYERBOT_SUNGMA_AGGRO_RADIUS)
					score -= 1500;
			score += (long long)(PlayerBotNavHash(ch->GetPlayerID() ^ (DWORD)i) % 100U);
			if (score > bestScore)
			{
				bestScore = score;
				bestX = x;
				bestY = y;
			}
		}
		if (bestScore != LLONG_MIN)
			MovePlayerBot(ch, bestX, bestY, dwNow, 16, true);
		else
			ch->Stop();
		return 1;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the re-arm

	// One missing self-buff of the build cast on the bot itself (the re-arm's): not Flame Spirit (the aura pulls - the
	// fight's buff pass casts it on a target) nor Cure; a buff still cooling down is not waited for. 1 a cast went (or the
	// bot climbed down for it), 0 nothing is missing that could go now, -1 a buff waits for the mana.
	int CastPlayerBotSungmaSelfBuff(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->GetSkillGroup() == 0 || IsPlayerBotFightingAsMonster(ch))
			return 0;
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
		int waiting = 0;
		for (size_t i = 0; i < sizeof(build.dwBuffSkills) / sizeof(build.dwBuffSkills[0]); ++i)
		{
			const DWORD vnum = build.dwBuffSkills[i];
			if (vnum == 0 || vnum == PLAYERBOT_SUNGMA_SKILL_FLAME_SPIRIT || vnum == 109 || ch->GetSkillLevel(vnum) == 0 ||
					IsPlayerBotBuffAffectOn(ch, vnum) || !IsPlayerBotSkillReady(state, vnum, dwNow))
				continue;
			if (ch->GetSP() < GetPlayerBotSkillSPCost(ch, vnum))
			{
				waiting = -1;
				continue;
			}
			if (ch->IsRiding() && !IsPlayerBotOnStandingMount(ch))
			{
				SetPlayerBotRidingForTravel(ch, state, false, dwNow, "buff");
				return 1;
			}
			if (!PlayerBotUseSkill(ch, state, vnum, ch, dwNow))
				continue;
			SendPlayerBotSkillPacket(ch, vnum);
			state.dwLastBotSkillTime = dwNow;
			state.dwNextAttackTime = dwNow + PLAYERBOT_SKILL_ANIMATION_LOCK;
			state.mapBuffActiveUntil[vnum] = dwNow + PLAYERBOT_BUFF_FALLBACK_DURATION;
			sys_log(0, "PLAYERBOT_SUNGMA: rearm buff pid=%u name=%s map=%ld vnum=%u sp=%d/%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), vnum, ch->GetSP(), ch->GetMaxSP());
			return 1;
		}
		return waiting;
	}

	void EndPlayerBotSungmaRearm(LPCHARACTER ch, TPlayerBotSungmaFight& f, DWORD dwNow, const char* why)
	{
		TPlayerBotSungmaClassStats& cs = GetPlayerBotSungmaClassStats(ch);
		if (why[0] == 'r')
			++cs.rearmsReady;
		else if (why[0] == 'a')
			++cs.rearmsAttacked;
		else if (why[0] == 't')
			++cs.rearmsTimeout;
		sys_log(0, "PLAYERBOT_SUNGMA: rearm over pid=%u name=%s map=%ld class=%s kind=%u why=%s took_ms=%u hp=%d/%d sp=%d/%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), PLAYERBOT_SUNGMA_CLASS_NAMES[GetPlayerBotSungmaClass(ch)],
				(unsigned int)f.bRearm, why, f.dwRearmSince ? dwNow - f.dwRearmSince : 0, ch->GetHP(), ch->GetMaxHP(), ch->GetSP(),
				ch->GetMaxSP());
		f.bRearm = 0;
		f.bRearmPending = false;
		f.dwRearmUntil = 0;
	}

	// The tick, after the recovery and the retreat (playerbot_manager.cpp): a resident that owes a re-arm (see the class
	// section) stands on its ground, drinks to its build's mana (the belt's red at PLAYERBOT_SUNGMA_POTION_PERCENT is
	// the tick's), rest-heals and puts its self-buffs back on before a new fight. True: the tick is the re-arm's.
	bool HoldPlayerBotSungmaRearm(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || state.bTacticalRetreat || state.bRecoveringAfterDeath)
			return false;
		std::map<DWORD, TPlayerBotSungmaFight>::iterator it = s_mapPlayerBotSungmaFight.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSungmaFight.end() || it->second.bRearm == 0)
			return false;
		TPlayerBotSungmaFight& f = it->second;
		if (!IsPlayerBotSungmaFighter(ch))
		{
			f.bRearm = 0;
			f.bRearmPending = false;
			return false;
		}
		if (f.bRearmPending)
		{
			f.bRearmPending = false;
			f.dwRearmSince = dwNow ? dwNow : 1;
			f.dwRearmUntil = dwNow + (f.bRearm == 1 ? PLAYERBOT_SUNGMA_CLASS_REARM_MAX_MS : PLAYERBOT_SUNGMA_CLASS_REARM_RETREAT_MS);
			f.dwRearmNextCast = 0;
			++GetPlayerBotSungmaClassStats(ch).rearms;
		}
		// a monster on it: the hold is a fight now
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_ATTACKER_RADIUS, mobs);
		long cx = 0, cy = 0;
		if (CountPlayerBotSungmaAttackers(ch, mobs, cx, cy, NULL) > 0)
		{
			EndPlayerBotSungmaRearm(ch, f, dwNow, "attacked");
			return false;
		}
		const int hp = GetPlayerBotSungmaHpPercent(ch);
		const int spTarget = GetPlayerBotSungmaRearmSp(ch);
		const int sp = ch->GetMaxSP() > 0 ? (int)((long long)ch->GetSP() * 100 / ch->GetMaxSP()) : 100;
		if (spTarget > 0 && sp < spTarget)
			UseManaPotion(ch, state, dwNow, spTarget);
		int buff = 0;
		if (dwNow >= state.dwNextAttackTime && (int)(dwNow - f.dwRearmNextCast) >= 0)
		{
			buff = CastPlayerBotSungmaSelfBuff(ch, state, dwNow);
			if (buff > 0)
				f.dwRearmNextCast = dwNow + PLAYERBOT_SUNGMA_CLASS_REARM_CAST_MS;
		}
		else
			buff = 1;	// a cast under way: its result is the next look's
		const bool hpReady = f.bRearm != 1 || hp >= PLAYERBOT_SUNGMA_CLASS_REARM_HP;
		const bool spReady = spTarget <= 0 || sp >= spTarget;
		// a buff short of mana with the build's mana reached (or none asked) is not waited for
		if (hpReady && spReady && buff <= 0)
		{
			EndPlayerBotSungmaRearm(ch, f, dwNow, "ready");
			return false;
		}
		if ((int)(dwNow - f.dwRearmUntil) >= 0)
		{
			EndPlayerBotSungmaRearm(ch, f, dwNow, "timeout");
			return false;
		}
		// standing, resting: the retreat's rest heal (3% a second), no target
		SetPlayerBotAction(state, BOT_ACTION_RECOVER, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (hp < 100 && dwNow >= state.dwNextRecoveryHealTime)
		{
			const int heal = std::max(1, ch->GetMaxHP() * 3 / 100);
			ch->PointChange(POINT_HP, std::min(heal, ch->GetMaxHP() - ch->GetHP()));
			state.dwNextRecoveryHealTime = dwNow + 1000;
		}
		if (ch->IsStateMove())
			ch->Stop();
		return true;
	}

	// ------------------------------------------------------------ the deaths

	// HandleDeath, the tick the bot is found dead (its retreat, target and last death not reset yet): the cause.
	void NotePlayerBotSungmaFallen(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !IsPlayerBotSungmaBotMap(ch->GetMapIndex()) || !IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
			return;
		TPlayerBotSungmaFight& f = s_mapPlayerBotSungmaFight[ch->GetPlayerID()];
		std::vector<TPlayerBotSungmaMob> mobs;
		CollectPlayerBotSungmaMobs(ch, PLAYERBOT_SUNGMA_ATTACKER_RADIUS, mobs);
		long cx = 0, cy = 0;
		const int attackers = CountPlayerBotSungmaAttackers(ch, mobs, cx, cy, NULL);
		int near = 0, boss = 0;
		for (size_t i = 0; i < mobs.size(); ++i)
		{
			const int d = DISTANCE_APPROX(mobs[i].x - ch->GetX(), mobs[i].y - ch->GetY());
			if (d <= PLAYERBOT_SUNGMA_NEAR_LOG_RADIUS)
				++near;
			if (mobs[i].boss && d <= PLAYERBOT_SUNGMA_NEAR_LOG_RADIUS)
				++boss;
		}
		LPCHARACTER target = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		const int partyNear = CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR);
		const int activity = GetPlayerBotSungmaActivity(ch->GetPlayerID());
		int cause = SUNGMA_DEATH_FIGHT;
		if (activity == 1)
			cause = SUNGMA_DEATH_PORTAL;
		else if (activity == 2)
			cause = SUNGMA_DEATH_ERRAND;
		else if (f.dwLastDown && dwNow - f.dwLastDown < PLAYERBOT_SUNGMA_DEATH_AGAIN_MS)
			cause = SUNGMA_DEATH_AGAIN;
		else if (state.bTacticalRetreat)
			cause = SUNGMA_DEATH_RETREAT;
		else if (target && target->IsStone())
			cause = SUNGMA_DEATH_STONE;
		else if (boss || (target && target->IsMonster() && target->GetMobRank() >= MOB_RANK_BOSS))
			cause = SUNGMA_DEATH_BOSS;
		else if (std::max(attackers, near) > PLAYERBOT_SUNGMA_CAPACITY_LONE)
			cause = SUNGMA_DEATH_PACK;
		f.dwLastDown = dwNow ? dwNow : 1;
		f.bRetreat = false;
		// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the build's census and the re-arm after the revival
		{
			TPlayerBotSungmaClassStats& cs = GetPlayerBotSungmaClassStats(ch);
			++cs.deaths;
			if (cause == SUNGMA_DEATH_AGAIN)
				++cs.again;
			if (state.bTacticalRetreat)
				++cs.retreatDeaths;
			QueuePlayerBotSungmaRearm(f, 1);
		}
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
		{
			++st->deaths[cause];
			if (partyNear >= 2)
				++st->deathsParty;
			else
				++st->deathsLone;
		}
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		int champion = 0;
#ifdef ENABLE_CONQUEROR_LEVEL
		champion = (int)ch->GetConquerorLevel();
#endif
		sys_log(0, "PLAYERBOT_SUNGMA: fallen pid=%u name=%s map=%ld cause=%s champion=%d attackers=%d near=%d boss=%d party=%d party_near=%d "
				"red=%u retreat=%d retreat_why=%s target=%u pos=(%ld,%ld) max_hp=%d sp=%d/%d class=%s",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), PLAYERBOT_SUNGMA_DEATH_CAUSE_NAMES[cause], champion, attackers,
				near, boss, ch->GetParty() ? (int)ch->GetParty()->GetMemberCount() : 0, partyNear, (unsigned int)red,
				state.bTacticalRetreat ? 1 : 0, f.szRetreatWhy[0] ? f.szRetreatWhy : "-", target ? target->GetRaceNum() : 0,
				ch->GetX(), ch->GetY(), ch->GetMaxHP(), ch->GetSP(), ch->GetMaxSP(),
				PLAYERBOT_SUNGMA_CLASS_NAMES[GetPlayerBotSungmaClass(ch)]);	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: sp, class
		f.szRetreatWhy[0] = '\0';
	}

	// The emergency rest (20% health, nobody holding it) counts as a fall for the cause "again".
	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: and the aura off for the invisible rest (the Black-magic Sura's spiral), the
	// re-arm after it.
	void NotePlayerBotSungmaDown(LPCHARACTER ch, DWORD dwNow)
	{
		if (ch && IsPlayerBotSungmaBotMap(ch->GetMapIndex()) && IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
		{
			TPlayerBotSungmaFight& f = s_mapPlayerBotSungmaFight[ch->GetPlayerID()];
			f.dwLastDown = dwNow ? dwNow : 1;
			DropPlayerBotSungmaAura(ch, "rest");
			QueuePlayerBotSungmaRearm(f, 1);
		}
	}

	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: a monster killed by a Sung Ma fighter (BattlePassOnKill) - its build's kill.
	void NotePlayerBotSungmaClassKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || !killer->IsPC() || !killer->GetDesc() || !killer->GetDesc()->IsBot() ||
				!IsPlayerBotSungmaBotMap(killer->GetMapIndex()) || !IsPlayerBotSungmaResidentPID(killer->GetPlayerID()))
			return;
		++GetPlayerBotSungmaClassStats(killer).kills;
	}

	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the class census - a sample of the fighters by build every census pass, and once
	// an hour a line a build: the bots (the samples' average), kills and deaths an hour, a bot's kills and deaths an
	// hour, the share of "again" deaths and of deaths in a retreat, retreats an hour, the aura drops and the re-arms
	// (ready / attacked / timeout).
	void LogPlayerBotSungmaClassCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotSungmaClassLastSample != 0 && dwNow - s_dwPlayerBotSungmaClassLastSample < 1000)
			return;	// one sample a census pass (every map's fight line calls this)
		s_dwPlayerBotSungmaClassLastSample = dwNow ? dwNow : 1;
		int here[SUNGMA_CLASS_COUNT] = { 0 };
		for (std::map<DWORD, TPlayerBotSungmaFight>::const_iterator i = s_mapPlayerBotSungmaFight.begin();
				i != s_mapPlayerBotSungmaFight.end(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(i->first);
			if (ch && IsPlayerBotSungmaBotMap(ch->GetMapIndex()) && IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
				++here[GetPlayerBotSungmaClass(ch)];
		}
		for (int c = 0; c < SUNGMA_CLASS_COUNT; ++c)
		{
			++s_aPlayerBotSungmaClassStats[c].samples;
			s_aPlayerBotSungmaClassStats[c].botSum += (unsigned int)here[c];
		}
		if (s_dwPlayerBotSungmaClassCensusSince == 0)
		{
			s_dwPlayerBotSungmaClassCensusSince = dwNow ? dwNow : 1;
			for (int c = 0; c < SUNGMA_CLASS_COUNT; ++c)
			{
				TPlayerBotSungmaClassStats& cs = s_aPlayerBotSungmaClassStats[c];
				cs.c0Kills = cs.kills; cs.c0Deaths = cs.deaths; cs.c0Again = cs.again; cs.c0Retreats = cs.retreats;
				cs.c0RetreatDeaths = cs.retreatDeaths; cs.c0AuraDrops = cs.auraDrops; cs.c0Rearms = cs.rearms;
				cs.c0RearmsReady = cs.rearmsReady; cs.c0RearmsAttacked = cs.rearmsAttacked; cs.c0RearmsTimeout = cs.rearmsTimeout;
				cs.samples = 1;
				cs.botSum = (unsigned int)here[c];
			}
			return;
		}
		const DWORD span = dwNow - s_dwPlayerBotSungmaClassCensusSince;
		if (span < PLAYERBOT_SUNGMA_CLASS_CENSUS_MS)
			return;
		const long long ms = (long long)span;
		for (int c = 0; c < SUNGMA_CLASS_COUNT; ++c)
		{
			TPlayerBotSungmaClassStats& cs = s_aPlayerBotSungmaClassStats[c];
			const long long bots10 = cs.samples ? (long long)cs.botSum * 10 / cs.samples : 0;
			const unsigned int deaths = cs.deaths - cs.c0Deaths;
			if (bots10 > 0 || deaths > 0)
			{
				const long long killsH = (long long)(cs.kills - cs.c0Kills) * 3600000LL / ms;
				const long long deathsH = (long long)deaths * 3600000LL / ms;
				const long long killsBot10 = bots10 > 0 ? killsH * 100 / bots10 : 0;
				const long long deathsBot100 = bots10 > 0 ? deathsH * 1000 / bots10 : 0;
				const unsigned int again = cs.again - cs.c0Again;
				const unsigned int inRetreat = cs.retreatDeaths - cs.c0RetreatDeaths;
				sys_log(0, "PLAYERBOT_SUNGMA: class channel=%u name=%s span_s=%u bots=%lld.%lld kills_h=%lld deaths_h=%lld "
						"kills_bot_h=%lld.%lld deaths_bot_h=%lld.%02lld again_pct=%u retreat_death_pct=%u retreats_h=%lld "
						"aura_drops=%u rearms=%u rearm_ready=%u rearm_attacked=%u rearm_timeout=%u",
						(unsigned int)g_bChannel, PLAYERBOT_SUNGMA_CLASS_NAMES[c], (unsigned int)(span / 1000), bots10 / 10, bots10 % 10,
						killsH, deathsH, killsBot10 / 10, killsBot10 % 10, deathsBot100 / 100, deathsBot100 % 100,
						deaths ? again * 100 / deaths : 0, deaths ? inRetreat * 100 / deaths : 0,
						(long long)(cs.retreats - cs.c0Retreats) * 3600000LL / ms, cs.auraDrops - cs.c0AuraDrops,
						cs.rearms - cs.c0Rearms, cs.rearmsReady - cs.c0RearmsReady, cs.rearmsAttacked - cs.c0RearmsAttacked,
						cs.rearmsTimeout - cs.c0RearmsTimeout);
			}
			cs.c0Kills = cs.kills; cs.c0Deaths = cs.deaths; cs.c0Again = cs.again; cs.c0Retreats = cs.retreats;
			cs.c0RetreatDeaths = cs.retreatDeaths; cs.c0AuraDrops = cs.auraDrops; cs.c0Rearms = cs.rearms;
			cs.c0RearmsReady = cs.rearmsReady; cs.c0RearmsAttacked = cs.rearmsAttacked; cs.c0RearmsTimeout = cs.rearmsTimeout;
			cs.samples = 0;
			cs.botSum = 0;
		}
		s_dwPlayerBotSungmaClassCensusSince = dwNow ? dwNow : 1;
	}

	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the hourly fight2 line of a map - kills, deaths, retreats, potions, turns and
	// escapes an hour, the bots seen (the census's average), kills a bot an hour, kills per death and the share of the
	// bots' time spent in a retreat. kills / deaths: the map's census counters (playerbot_yohara_sungma.h).
	void LogPlayerBotSungmaFight2(int slot, long mapIndex, const char* key, int here, unsigned int kills, unsigned int deaths,
			DWORD dwNow)
	{
		TPlayerBotSungmaFightStats& st = s_aPlayerBotSungmaFightStats[slot];
		++st.f2Samples;
		st.f2BotSum += (unsigned int)std::max(0, here);
		if (st.f2Since == 0)
		{
			st.f2Since = dwNow ? dwNow : 1;
			st.f2Kills = kills;
			st.f2Deaths = deaths;
			st.f2Retreats = st.retreatsEnded;
			st.f2RetreatMs = st.retreatMs;
			st.f2Turns = st.turns;
			st.f2Potions = st.potions;
			st.f2Escapes = st.escapes;
			st.f2Samples = 1;
			st.f2BotSum = (unsigned int)std::max(0, here);
			return;
		}
		const DWORD span = dwNow - st.f2Since;
		if (span < PLAYERBOT_SUNGMA_F2_CENSUS_MS)
			return;
		const long long ms = (long long)span;
		const long long killsH = (long long)(kills - st.f2Kills) * 3600000LL / ms;
		const long long deathsH = (long long)(deaths - st.f2Deaths) * 3600000LL / ms;
		const long long retreatsH = (long long)(st.retreatsEnded - st.f2Retreats) * 3600000LL / ms;
		const long long potionsH = (long long)(st.potions - st.f2Potions) * 3600000LL / ms;
		const long long turnsH = (long long)(st.turns - st.f2Turns) * 3600000LL / ms;
		const long long escapesH = (long long)(st.escapes - st.f2Escapes) * 3600000LL / ms;
		const long long bots10 = st.f2Samples ? (long long)st.f2BotSum * 10 / st.f2Samples : 0;	// the average, x10
		const long long killsBot10 = bots10 > 0 ? killsH * 100 / bots10 : 0;
		const long long kpd10 = deathsH > 0 ? killsH * 10 / deathsH : killsH * 10;
		const long long retreatPct = bots10 > 0 ? (long long)(st.retreatMs - st.f2RetreatMs) * 1000 / (ms * bots10) : 0;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
		// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the map's last kills per death (x10, with deaths; 0 none) - a bot's own is
		// judged against it (IsPlayerBotG0Struggling)
		s_aiPlayerBotSungmaF2Kpd10[slot] = deathsH > 0 ? (int)std::min<long long>(kpd10, 1000000) : 0;
#endif
		sys_log(0, "PLAYERBOT_SUNGMA: fight2 channel=%u map=%ld name=%s span_s=%u bots=%lld.%lld kills_h=%lld deaths_h=%lld retreats_h=%lld "
				"potions_h=%lld turns_h=%lld escapes_h=%lld kills_bot_h=%lld.%lld kills_per_death=%lld.%lld retreat_time_pct=%lld",
				(unsigned int)g_bChannel, mapIndex, key, (unsigned int)(span / 1000), bots10 / 10, bots10 % 10, killsH, deathsH,
				retreatsH, potionsH, turnsH, escapesH, killsBot10 / 10, killsBot10 % 10, kpd10 / 10, kpd10 % 10, retreatPct);
		st.f2Since = dwNow ? dwNow : 1;
		st.f2Kills = kills;
		st.f2Deaths = deaths;
		st.f2Retreats = st.retreatsEnded;
		st.f2RetreatMs = st.retreatMs;
		st.f2Turns = st.turns;
		st.f2Potions = st.potions;
		st.f2Escapes = st.escapes;
		st.f2Samples = 0;
		st.f2BotSum = 0;
	}

	// The census's fight line of a map (LogPlayerBotSungmaCensus).
	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: here, kills and deaths for the hourly fight2 line.
	void LogPlayerBotSungmaFightCensus(int slot, long mapIndex, const char* key, int parties, int inParty, int lone,
			int here, unsigned int kills, unsigned int deaths)
	{
		if (slot < 0 || slot >= 9)
			return;
		LogPlayerBotSungmaFight2(slot, mapIndex, key, here, kills, deaths, get_dword_time());
		LogPlayerBotSungmaClassCensus(get_dword_time());	// MT2009_PLUS_BOT_SUNGMA_CLASS_V1: the class line, hourly
		const TPlayerBotSungmaFightStats& st = s_aPlayerBotSungmaFightStats[slot];
		char causes[160];
		int len = 0;
		causes[0] = '\0';
		for (int i = 0; i < SUNGMA_DEATH_CAUSES && len < (int)sizeof(causes) - 1; ++i)
			len += snprintf(causes + len, sizeof(causes) - len, "%s%s=%u", i ? " " : "", PLAYERBOT_SUNGMA_DEATH_CAUSE_NAMES[i], st.deaths[i]);
		sys_log(0, "PLAYERBOT_SUNGMA: fight channel=%u map=%ld name=%s parties=%d in_party=%d lone=%d party_forms=%u party_joins=%u "
				"party_leaves=%u party_errand_leaves=%u regroups=%u revives_in_party=%u party_objectives=%u picks=%u element_picks=%u "
				"edge_picks=%u pack_refused=%u retreats_hp=%u retreats_pack=%u retreats_pulled=%u retreats_safe=%u avoids=%u "
				"deaths_lone=%u deaths_party=%u %s escapes=%u nest_moves=%u hp_refused=%u turns=%u potions=%u hunt_element_picks=%u",
				(unsigned int)g_bChannel, mapIndex, key, parties, inParty, lone, st.partyForms, st.partyJoins, st.partyLeaves,
				st.partyErrandLeaves, st.regroups, st.revivesInParty, st.partyObjectives, st.targetsPicked, st.targetsElement,
				st.targetsEdge, st.packRefused, st.retreatsHp, st.retreatsPack, st.retreatsPulled, st.retreatsSafe, st.avoids,
				st.deathsLone, st.deathsParty, causes, st.escapes, st.nestMoves, st.hpRefused, st.turns, st.potions,
				st.huntElementPicks);
	}
}

#endif
