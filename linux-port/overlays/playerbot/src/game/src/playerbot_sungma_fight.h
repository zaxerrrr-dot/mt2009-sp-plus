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
	const int PLAYERBOT_SUNGMA_POTION_PERCENT = 80;
	// The retreat: at this health alone / in a party by it; at PLAYERBOT_SUNGMA_RETREAT_PACK_HP with more attackers
	// than its capacity; at any health under PLAYERBOT_SUNGMA_RETREAT_PULLED_HP with PLAYERBOT_SUNGMA_PULLED_EXTRA over
	// its capacity (pulled too much). Over at PLAYERBOT_SUNGMA_RETREAT_END_HP with nobody on it, or after
	// PLAYERBOT_SUNGMA_RETREAT_MAX_MS.
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
	const int PLAYERBOT_SUNGMA_ENGAGE_HP = 75;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_MAX_MS = 120 * 1000;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_MOVE_MS = 1500;
	const DWORD PLAYERBOT_SUNGMA_RETREAT_LOOK_MS = 700;
	const int PLAYERBOT_SUNGMA_RETREAT_STEP = 1500;
	const int PLAYERBOT_SUNGMA_SAFE_REACHED = 1500;
	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the escape out of a lost retreat (HandlePlayerBotSungmaRetreat).
	const int PLAYERBOT_SUNGMA_ESCAPE_ATTACKERS = 2;
	const int PLAYERBOT_SUNGMA_ESCAPE_HP = 30;
	const DWORD PLAYERBOT_SUNGMA_ESCAPE_AFTER_MS = 3000;
	const DWORD PLAYERBOT_SUNGMA_ESCAPE_GAP_MS = 3 * 60 * 1000;	// a ring's cooldown - not every retreat
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
		TPlayerBotSungmaFight() : bRetreat(false), iRetreatAttackers(0), lAvoidMap(0), lAvoidX(0), lAvoidY(0), dwAvoidUntil(0),
			dwLastDown(0), dwNextRetreatLook(0), iRefused(0), dwRefusedSince(0), iHpSeen(100), dwHpSeenAt(0), dwLastEscape(0)
		{ szRetreatWhy[0] = '\0'; }
	};
	std::map<DWORD, TPlayerBotSungmaFight> s_mapPlayerBotSungmaFight;

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
		TPlayerBotSungmaFightStats() : deathsLone(0), deathsParty(0), retreatsHp(0), retreatsPack(0), retreatsPulled(0),
			retreatsSafe(0), avoids(0), targetsPicked(0), targetsElement(0), targetsEdge(0), packRefused(0), partyObjectives(0),
			partyForms(0), partyJoins(0), partyLeaves(0), partyErrandLeaves(0), regroups(0), revivesInParty(0),
			escapes(0), nestMoves(0), hpRefused(0)
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
	const int PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS = 1500;
	const int PLAYERBOT_SUNGMA_REVIVE_PACK_MAX = 3;

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

	// How many monsters at once the bot takes (see PLAYERBOT_SUNGMA_CAPACITY_*).
	int GetPlayerBotSungmaCapacity(LPCHARACTER ch, int partyNear)
	{
		const int hp = GetPlayerBotSungmaHpPercent(ch);
		const int lone = PLAYERBOT_SUNGMA_CAPACITY_LONE - (GetPlayerBotSungmaMobFloor(ch->GetMapIndex()) >= PLAYERBOT_SUNGMA_CAPACITY_HARD_LEVEL ? 1 : 0);
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
				CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS, 30) < PLAYERBOT_SUNGMA_PARTY_MIN)
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
		const int fullCap = PLAYERBOT_SUNGMA_CAPACITY_LONE -
				(GetPlayerBotSungmaMobFloor(ch->GetMapIndex()) >= PLAYERBOT_SUNGMA_CAPACITY_HARD_LEVEL ? 1 : 0) +
				std::max(0, partyNear - 1) * PLAYERBOT_SUNGMA_CAPACITY_MEMBER;
		const char* why = NULL;
		if (hp <= (partyNear >= 2 ? PLAYERBOT_SUNGMA_RETREAT_PARTY_HP : PLAYERBOT_SUNGMA_RETREAT_LONE_HP))
			why = "hp";
		else if (attackers > fullCap && hp <= PLAYERBOT_SUNGMA_RETREAT_PACK_HP)
			why = "pack";
		else if (attackers >= fullCap + PLAYERBOT_SUNGMA_PULLED_EXTRA && hp < PLAYERBOT_SUNGMA_RETREAT_PULLED_HP)
			why = "pulled";
		else if (attackers >= 2 && fall >= PLAYERBOT_SUNGMA_RETREAT_FALL_PERCENT && hp <= PLAYERBOT_SUNGMA_RETREAT_FALL_HP)
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
		long ex = 0, ey = 0;
		if (attackers >= PLAYERBOT_SUNGMA_ESCAPE_ATTACKERS && hp <= PLAYERBOT_SUNGMA_ESCAPE_HP && el >= PLAYERBOT_SUNGMA_ESCAPE_AFTER_MS &&
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
		if ((attackers == 0 && hp >= PLAYERBOT_SUNGMA_RETREAT_END_HP) || el >= PLAYERBOT_SUNGMA_RETREAT_MAX_MS)
		{
			sys_log(0, "PLAYERBOT_SUNGMA: retreat over pid=%u name=%s map=%ld why=%s hp=%d/%d attackers=%d took_s=%u at_safe=%d reason=%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), f.szRetreatWhy[0] ? f.szRetreatWhy : "generic", ch->GetHP(),
					ch->GetMaxHP(), attackers, el / 1000, toSafe <= PLAYERBOT_SUNGMA_SAFE_REACHED ? 1 : 0,
					attackers == 0 ? "healed" : "timeout");
			if (toSafe <= PLAYERBOT_SUNGMA_SAFE_REACHED)
				if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
					++st->retreatsSafe;
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
				"red=%u retreat=%d retreat_why=%s target=%u pos=(%ld,%ld) max_hp=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), PLAYERBOT_SUNGMA_DEATH_CAUSE_NAMES[cause], champion, attackers,
				near, boss, ch->GetParty() ? (int)ch->GetParty()->GetMemberCount() : 0, partyNear, (unsigned int)red,
				state.bTacticalRetreat ? 1 : 0, f.szRetreatWhy[0] ? f.szRetreatWhy : "-", target ? target->GetRaceNum() : 0,
				ch->GetX(), ch->GetY(), ch->GetMaxHP());
		f.szRetreatWhy[0] = '\0';
	}

	// The emergency rest (20% health, nobody holding it) counts as a fall for the cause "again".
	void NotePlayerBotSungmaDown(LPCHARACTER ch, DWORD dwNow)
	{
		if (ch && IsPlayerBotSungmaBotMap(ch->GetMapIndex()) && IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
			s_mapPlayerBotSungmaFight[ch->GetPlayerID()].dwLastDown = dwNow ? dwNow : 1;
	}

	// The census's fight line of a map (LogPlayerBotSungmaCensus).
	void LogPlayerBotSungmaFightCensus(int slot, long mapIndex, const char* key, int parties, int inParty, int lone)
	{
		if (slot < 0 || slot >= 9)
			return;
		const TPlayerBotSungmaFightStats& st = s_aPlayerBotSungmaFightStats[slot];
		char causes[160];
		int len = 0;
		causes[0] = '\0';
		for (int i = 0; i < SUNGMA_DEATH_CAUSES && len < (int)sizeof(causes) - 1; ++i)
			len += snprintf(causes + len, sizeof(causes) - len, "%s%s=%u", i ? " " : "", PLAYERBOT_SUNGMA_DEATH_CAUSE_NAMES[i], st.deaths[i]);
		sys_log(0, "PLAYERBOT_SUNGMA: fight channel=%u map=%ld name=%s parties=%d in_party=%d lone=%d party_forms=%u party_joins=%u "
				"party_leaves=%u party_errand_leaves=%u regroups=%u revives_in_party=%u party_objectives=%u picks=%u element_picks=%u "
				"edge_picks=%u pack_refused=%u retreats_hp=%u retreats_pack=%u retreats_pulled=%u retreats_safe=%u avoids=%u "
				"deaths_lone=%u deaths_party=%u %s escapes=%u nest_moves=%u hp_refused=%u",
				(unsigned int)g_bChannel, mapIndex, key, parties, inParty, lone, st.partyForms, st.partyJoins, st.partyLeaves,
				st.partyErrandLeaves, st.regroups, st.revivesInParty, st.partyObjectives, st.targetsPicked, st.targetsElement,
				st.targetsEdge, st.packRefused, st.retreatsHp, st.retreatsPack, st.retreatsPulled, st.retreatsSafe, st.avoids,
				st.deathsLone, st.deathsParty, causes, st.escapes, st.nestMoves, st.hpRefused);
	}
}

#endif
