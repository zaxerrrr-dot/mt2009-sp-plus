#ifndef __INC_METIN2_PLAYERBOT_DEATHLOOP_H__
#define __INC_METIN2_PLAYERBOT_DEATHLOOP_H__

// MT2009_PLUS_BOT_DEATHLOOP_V1 - the death loop, the 2.x port (release 2.42.0) of the Yohara branch's dbe79ab2 + 07bc759b
// (the analysis of 83.168.110.166, 6 November 2026, dist/aktualizacje/test-plus/ANALIZA-BOTOW-83.168.110.166-2026-11-06.md):
// 9 838 "death detected" an hour on ch2, 9 828 of them "revived at same position" - every bot of every level stood up
// where it fell, with 20% of its health, among the monsters that had just killed it, healed invisibly a step off the
// body and fell again (a level-49 bot on map 109: 159 deaths in one hour; 88 bots of 30+ an hour; 4 868 of them in the
// Monkey maps 108/109 - bots of 33-35 on 108 and of 46-54 on 109).
//
// V2 (the owner, 6 November 2026: "niech wstaje blisko i od razu ucieka w bezpieczne miejsce, zanim zrobi sie widoczny
// dla potworow"):
// 1. The flee (HandleDeath, playerbot_survival.h): the bot stands up by its body (50% health and mana -
//    PLAYERBOT_REVIVE_HP_PCT) and, when the body's ground is not safe (a monster on somebody within
//    PLAYERBOT_DEATHLOOP_FIGHT_RADIUS, or an aggressive one within its own aggressive sight + PLAYERBOT_DEATHLOOP_SIGHT_PAD)
//    or it fell on this spot (PLAYERBOT_DEATHLOOP_SPOT_RADIUS) before within PLAYERBOT_DEATHLOOP_WINDOW_MIN minutes, it
//    runs at once to the nearest safe point: rings of PLAYERBOT_DEATHLOOP_RING_STEP round the body up to
//    PLAYERBOT_DEATHLOOP_FLEE_MAX (6 000 = 60 m), twelve directions, the ones away from the pack's centre first, safe by
//    the same test and reachable on the navigation grid. On the way it carries AFFECT_REVIVE_INVISIBLE (the engine's
//    revive protection: the monsters' FindVictim and battle_is_attackable skip it; to a person it is the usual
//    after-revive look) for up to PLAYERBOT_DEATHLOOP_HIDE_S (8) seconds; it shows itself when it gets there or the time
//    is up. Then the recovery goes on visibly (the rest-heal and the potions) and it hunts again from there - the same
//    ground, no long walk. No safe point found: the map's restart-in-town point (its kingdom's recall point; a Monkey
//    map's arrival; the map's arrival), as before.
// 2. The loop: more than eight deaths (PLAYERBOT_SURVIVE_DEATHS_H, 9 - one number with the step down of
//    playerbot_survive.h, which does the 2.x hunting maps itself) on one map within an hour: the map is avoided for
//    PLAYERBOT_DEATHLOOP_AVOID_MIN minutes - a Monkey map is not chosen by the medal errand (GetPlayerBotMonkeyMapFor)
//    - and the spot is the persona's avoided spot (the targeting and the hub choice leave it alone) unless a
//    capitulation already holds one.
// 3. The pin: a bot the Law of Advancement pinned after its deaths (3 in 30 min, NotePlayerBotPersonaDeath) has the pin
//    cleared once it stands on the easier map (the step down's map, or another hunting ground after a loop's).
// 4. The Monkey maps by the level alone (playerbot_types.h GetPlayerBotMonkeyMinLevel: 108 from 36, 109 from 55).
//
// Not touched: the Zodiac temple's revive, the companion held in it, a dungeon instance (any map of
// PLAYERBOT_INSTANCE_MAP_INDEX_MIN and up) or the Demon Tower's business, a guild war.
// Switches: event flag m2_bot_deathloop_off 1 - all of it off (the 50% revive stays); m2_bot_deathloop_monkey_off 1 -
// the Monkey level bands alone. Env PLAYERBOT_DEATHLOOP_HIDE_S (8), _FLEE_MAX (6000), _RING_STEP (750),
// _FIGHT_RADIUS (1500), _SIGHT_PAD (400), _SPOT_RADIUS (3000), _WINDOW_MIN (10), _AVOID_MIN (60);
// PLAYERBOT_MONKEY2_MIN_LEVEL (36), PLAYERBOT_MONKEY3_MIN_LEVEL (55); PLAYERBOT_SURVIVE_DEATHS_H (9);
// PLAYERBOT_REVIVE_HP_PCT (50).
// The log: PLAYERBOT_DEATHLOOP: flee / town revive / loop / pin cleared (throttled), census every 10 minutes.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_survive.h; the earlier headers ask its
// hooks through declarations (playerbot_survival.h, playerbot_travel.h).

namespace
{
	const DWORD PLAYERBOT_DEATHLOOP_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_DEATHLOOP_MAP_WINDOW_MS = 60 * 60 * 1000;
	const size_t PLAYERBOT_DEATHLOOP_MAX_DEATHS_KEPT = 64;
	const int PLAYERBOT_DEATHLOOP_DIRECTIONS = 12;
	const int PLAYERBOT_DEATHLOOP_REACH_TESTS = 12;
	const int PLAYERBOT_DEATHLOOP_ARRIVED = 300;

	bool IsPlayerBotDeathloopOn()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			s_bOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_deathloop_off") == 0;
		}
		return s_bOn;
	}

	struct TPlayerBotDeathloopConfig
	{
		int hideMs, fleeMax, ringStep, fightRadius, sightPad, spotRadius;
		DWORD windowMs, avoidMs;
	};

	const TPlayerBotDeathloopConfig& GetPlayerBotDeathloopConfig()
	{
		static bool s_bRead = false;
		static TPlayerBotDeathloopConfig c;
		if (!s_bRead)
		{
			s_bRead = true;
			c.hideMs = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_HIDE_S", 8, 1, 30) * 1000;
			c.fleeMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_FLEE_MAX", 6000, 1000, 20000);
			c.ringStep = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_RING_STEP", 750, 200, 5000);
			c.fightRadius = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_FIGHT_RADIUS", 1500, 300, 6000);
			c.sightPad = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_SIGHT_PAD", 400, 0, 5000);
			c.spotRadius = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_SPOT_RADIUS", 3000, 300, 20000);
			c.windowMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_WINDOW_MIN", 10, 1, 120) * 60000U;
			c.avoidMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_AVOID_MIN", 60, 5, 24 * 60) * 60000U;
		}
		return c;
	}

	struct TPlayerBotDeathloopDeath
	{
		DWORD at;
		long map, x, y;
	};

	struct TPlayerBotDeathloopBot
	{
		std::deque<TPlayerBotDeathloopDeath> deaths;	// the monster deaths of the last hour
		bool bRepeat;			// this death on a spot it fell on in the window
		int iMobs;			// the unsafe monsters round the body when it fell
		// the flee
		bool bFleeing, bShown;		// bShown: the flee is over, this recovery goes on visibly
		long lFleeMap, lFleeX, lFleeY, lFleeFromX, lFleeFromY;
		DWORD dwFleeStart, dwFleeUntil;
		int iFleeDist;
		std::map<long, DWORD> avoid;	// map -> until
		long lLoopMap;			// the map of the last loop, for the pin
		int iLoopMapLevel;		// its survive row's entry level (-1: none)
		TPlayerBotDeathloopBot() : bRepeat(false), iMobs(0), bFleeing(false), bShown(false), lFleeMap(0), lFleeX(0), lFleeY(0),
				lFleeFromX(0), lFleeFromY(0), dwFleeStart(0), dwFleeUntil(0), iFleeDist(0), lLoopMap(0), iLoopMapLevel(-1) {}
	};
	std::map<DWORD, TPlayerBotDeathloopBot> s_mapPlayerBotDeathloop;

	struct TPlayerBotDeathloopStats
	{
		unsigned int deaths, inPlace, flee, fleeReached, fleeTimedOut, fleeFailed, town, loops, pinsCleared;
		TPlayerBotDeathloopStats() : deaths(0), inPlace(0), flee(0), fleeReached(0), fleeTimedOut(0), fleeFailed(0), town(0),
				loops(0), pinsCleared(0) {}
	};
	TPlayerBotDeathloopStats s_kPlayerBotDeathloop;

	// The monsters that make (x, y) unsafe for a bot standing up there: one on somebody within the fight radius, or an
	// aggressive one that would see it (its aggressive sight + the pad). Their count and their centre.
	class FPlayerBotDeathloopDanger
	{
		public:
			FPlayerBotDeathloopDanger(long map, long x, long y) : m_map(map), m_x(x), m_y(y), m_count(0), m_sx(0), m_sy(0)
			{
				const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
				m_fight = c.fightRadius;
				m_pad = c.sightPad;
			}
			void operator()(LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
				if (!mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_map)
					return;
				const int d = DISTANCE_APPROX(mob->GetX() - m_x, mob->GetY() - m_y);
				bool unsafe = mob->GetVictim() != NULL && d <= m_fight;
				if (!unsafe && IS_SET(mob->GetMobTable().dwAIFlag, AIFLAG_AGGRESSIVE))
					unsafe = d <= (int)mob->GetMobTable().wAggressiveSight + m_pad;
				if (!unsafe)
					return;
				++m_count;
				m_sx += mob->GetX();
				m_sy += mob->GetY();
			}
			long m_map, m_x, m_y;
			int m_fight, m_pad, m_count;
			long long m_sx, m_sy;
	};

	int ScanPlayerBotDeathloopDanger(long map, long x, long y, long* cx = NULL, long* cy = NULL)
	{
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(map, x, y);
		if (!tree)
			return -1;
		FPlayerBotDeathloopDanger f(map, x, y);
		tree->ForEachAround(f);
		if (f.m_count > 0 && cx && cy)
		{
			*cx = (long)(f.m_sx / f.m_count);
			*cy = (long)(f.m_sy / f.m_count);
		}
		return f.m_count;
	}

	// Whose deaths this is about: not a dungeon instance's, the Demon Tower's or a guild war's.
	bool IsPlayerBotDeathloopCase(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		return ch && IsPlayerBotDeathloopOn() && !IsPlayerBotInDungeonBusiness(ch, state) &&
				state.dwGuildWarEnemyGID == 0 && ch->GetMapIndex() < PLAYERBOT_INSTANCE_MAP_INDEX_MIN;
	}

	// The nearest safe point round (x, y), the ones away from the pack's centre (cx, cy) first; false: none.
	bool FindPlayerBotDeathloopSafePoint(LPCHARACTER ch, long x, long y, bool hasCentre, long cx, long cy, long& outX,
			long& outY)
	{
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		const long map = ch->GetMapIndex();
		double awayX = 0.0, awayY = 0.0;
		if (hasCentre)
		{
			awayX = (double)(x - cx);
			awayY = (double)(y - cy);
			const double len = std::sqrt(awayX * awayX + awayY * awayY);
			if (len > 1.0)
			{
				awayX /= len;
				awayY /= len;
			}
			else
				awayX = awayY = 0.0;
		}
		struct TCand { double score; long x, y; int ring; };
		std::vector<TCand> cands;
		const int rings = std::max(1, c.fleeMax / c.ringStep);
		const double first = (double)(ch->GetPlayerID() % PLAYERBOT_DEATHLOOP_DIRECTIONS);
		for (int r = 1; r <= rings; ++r)
			for (int k = 0; k < PLAYERBOT_DEATHLOOP_DIRECTIONS; ++k)
			{
				const double a = (first + k) * 2.0 * M_PI / PLAYERBOT_DEATHLOOP_DIRECTIONS;
				const double dx = std::cos(a), dy = std::sin(a);
				const double cosAway = dx * awayX + dy * awayY;	// 1 straight away from the pack, -1 into it
				TCand cand;
				cand.ring = r;
				cand.x = x + (long)(dx * r * c.ringStep);
				cand.y = y + (long)(dy * r * c.ringStep);
				// a ring further out is worth turning away from the pack by about half a circle
				cand.score = (double)r + (1.0 - cosAway) * 1.5;
				cands.push_back(cand);
			}
		std::sort(cands.begin(), cands.end(), [](const TCand& l, const TCand& r) { return l.score < r.score; });
		int reachTests = 0;
		for (size_t i = 0; i < cands.size() && reachTests < PLAYERBOT_DEATHLOOP_REACH_TESTS; ++i)
		{
			const TCand& cand = cands[i];
			if (SECTREE_MANAGER::instance().GetMapIndex(cand.x, cand.y) != map)
				continue;
			if (ScanPlayerBotDeathloopDanger(map, cand.x, cand.y) != 0)	// -1: no ground there
				continue;
			++reachTests;
			if (!IsPlayerBotReachable(map, x, y, cand.x, cand.y))
				continue;
			outX = cand.x;
			outY = cand.y;
			return true;
		}
		return false;
	}

	// The map's restart-in-town point for this bot, on the same map (the flee's fallback).
	bool GetPlayerBotDeathloopTownPoint(LPCHARACTER ch, long& x, long& y)
	{
		const long map = ch->GetMapIndex();
		if (IsPlayerBotMonkeyMap(map) && GetPlayerBotMonkeyArrival(map, x, y))
			return true;
		PIXEL_POSITION pos;
		if (SECTREE_MANAGER::instance().GetRecallPositionByEmpire(map, ch->GetEmpire(), pos) &&
				SECTREE_MANAGER::instance().GetMapIndex(pos.x, pos.y) == map)
		{
			x = pos.x;
			y = pos.y;
			return true;
		}
		return GetPlayerBotFrontierArrivalFor(ch, map, x, y) && SECTREE_MANAGER::instance().GetMapIndex(x, y) == map;
	}

	// More than eight deaths on the map in the hour: the map avoided (a Monkey map by the medal errand; a 2.x hunting map
	// is the step down's own - playerbot_survive.h counts the same deaths with the same number) and the spot.
	void MarkPlayerBotDeathloopAvoid(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDeathloopBot& b, long map, long x,
			long y, int deathsOnMap, DWORD dwNow)
	{
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		b.avoid[map] = dwNow + c.avoidMs;
		b.lLoopMap = map;
		b.iLoopMapLevel = GetPlayerBotSurviveMapLevel(map);
		TPlayerBotPersona& p = state.persona;
		if (p.dwAvoidSpotUntil == 0 || (int)(dwNow - p.dwAvoidSpotUntil) >= 0)
		{
			p.lAvoidSpotMap = map;
			p.lAvoidSpotX = x;
			p.lAvoidSpotY = y;
			p.dwAvoidSpotUntil = dwNow + c.avoidMs;
		}
		state.dwHubChosenTime = 0;
		state.dwNextWanderTime = dwNow;
		++s_kPlayerBotDeathloop.loops;
		PlayerBotLogThrottled("deathloop_loop", dwNow,
				"PLAYERBOT_DEATHLOOP: loop pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) deaths_h=%d avoid_min=%u step_down_map=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), map, x, y, deathsOnMap,
				(unsigned int)(c.avoidMs / 60000U), b.iLoopMapLevel >= 0 ? 1 : 0);
	}

	// HandleDeath, the tick a death is noticed (after the step down's own count).
	void NotePlayerBotDeathloopDeath(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return;
		TPlayerBotDeathloopBot& b = s_mapPlayerBotDeathloop[ch->GetPlayerID()];
		b.bFleeing = false;
		b.bShown = false;
		b.bRepeat = false;
		b.iMobs = 0;
		if (!IsPlayerBotDeathloopCase(ch, state))
			return;
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		++s_kPlayerBotDeathloop.deaths;
		const long map = ch->GetMapIndex(), x = ch->GetX(), y = ch->GetY();
		while (!b.deaths.empty() && (dwNow - b.deaths.front().at >= PLAYERBOT_DEATHLOOP_MAP_WINDOW_MS ||
				b.deaths.size() >= PLAYERBOT_DEATHLOOP_MAX_DEATHS_KEPT))
			b.deaths.pop_front();
		b.iMobs = std::max(0, ScanPlayerBotDeathloopDanger(map, x, y));
		// a death with no monster round the body is a player's (the arena, a duel, a kingdom's war): not counted
		if (b.iMobs <= 0)
			return;
		int here = 0, onMap = 0;
		for (size_t i = 0; i < b.deaths.size(); ++i)
		{
			if (b.deaths[i].map != map)
				continue;
			++onMap;
			if (dwNow - b.deaths[i].at < c.windowMs &&
					DISTANCE_APPROX(b.deaths[i].x - x, b.deaths[i].y - y) <= c.spotRadius)
				++here;
		}
		TPlayerBotDeathloopDeath d;
		d.at = dwNow;
		d.map = map;
		d.x = x;
		d.y = y;
		b.deaths.push_back(d);
		++onMap;
		b.bRepeat = here > 0;
		if (onMap >= GetPlayerBotSurviveDeathsPerHour())
		{
			MarkPlayerBotDeathloopAvoid(ch, state, b, map, x, y, onMap, dwNow);
			// counted once: the next loop needs its own deaths
			std::deque<TPlayerBotDeathloopDeath> rest;
			for (size_t i = 0; i < b.deaths.size(); ++i)
				if (b.deaths[i].map != map)
					rest.push_back(b.deaths[i]);
			b.deaths.swap(rest);
		}
	}

	// HandleDeath, the bot just stood up by its body: the flee to a safe point when the ground is not safe or it fell
	// here before (hidden on the way), the town point when no safe point is found. True when moved there at once (the
	// town point); the flee itself walks in the recovery (ManagePlayerBotDeathloopFlee).
	bool MovePlayerBotDeathloopRevived(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead())
			return false;
		std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDeathloop.end() || !IsPlayerBotDeathloopCase(ch, state))
			return false;
		TPlayerBotDeathloopBot& b = it->second;
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		const long map = ch->GetMapIndex(), x = ch->GetX(), y = ch->GetY();
		long cx = 0, cy = 0;
		const int danger = ScanPlayerBotDeathloopDanger(map, x, y, &cx, &cy);
		if (danger <= 0 && !b.bRepeat)
		{
			++s_kPlayerBotDeathloop.inPlace;
			return false;
		}
		long sx = 0, sy = 0;
		if (FindPlayerBotDeathloopSafePoint(ch, x, y, danger > 0, cx, cy, sx, sy))
		{
			b.bFleeing = true;
			b.bShown = false;
			b.lFleeMap = map;
			b.lFleeX = sx;
			b.lFleeY = sy;
			b.lFleeFromX = x;
			b.lFleeFromY = y;
			b.dwFleeStart = dwNow;
			b.dwFleeUntil = dwNow + (DWORD)c.hideMs;
			b.iFleeDist = DISTANCE_APPROX(sx - x, sy - y);
			b.iMobs = std::max(b.iMobs, danger);
			ch->ReviveInvisible((c.hideMs + 999) / 1000);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			++s_kPlayerBotDeathloop.flee;
			return false;
		}
		++s_kPlayerBotDeathloop.fleeFailed;
		long tx = 0, ty = 0;
		if (!GetPlayerBotDeathloopTownPoint(ch, tx, ty))
		{
			PlayerBotLogThrottled("deathloop_flee_failed", dwNow,
					"PLAYERBOT_DEATHLOOP: flee failed pid=%u name=%s map=%ld pos=(%ld,%ld) mobs=%d town=0",
					ch->GetPlayerID(), ch->GetName(), map, x, y, danger);
			return false;
		}
		long ox = 0, oy = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x444c4f50U, 50, 250, ox, oy);
		++s_kPlayerBotDeathloop.town;
		PlayerBotLogThrottled("deathloop_town", dwNow,
				"PLAYERBOT_DEATHLOOP: flee failed, town revive pid=%u name=%s level=%u map=%ld from=(%ld,%ld) to=(%ld,%ld) mobs=%d repeat=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), map, x, y, tx + ox, ty + oy, danger,
				b.bRepeat ? 1 : 0);
		ch->Stop();
		ch->Show(map, tx + ox, ty + oy, 0);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		return true;
	}

	// HandlePostDeathRecovery (playerbot_survival.h): the flee's run, hidden; it shows itself at the safe point or when
	// the hide window ends. True while it runs (the tick is the flee's).
	bool ManagePlayerBotDeathloopFlee(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDeathloop.end() || !it->second.bFleeing)
			return false;
		TPlayerBotDeathloopBot& b = it->second;
		const int left = DISTANCE_APPROX(ch->GetX() - b.lFleeX, ch->GetY() - b.lFleeY);
		const bool reached = left <= PLAYERBOT_DEATHLOOP_ARRIVED;
		if (!reached && (int)(dwNow - b.dwFleeUntil) < 0 && ch->GetMapIndex() == b.lFleeMap)
		{
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			MovePlayerBot(ch, b.lFleeX, b.lFleeY, dwNow, 16, true, true);
			return true;
		}
		b.bFleeing = false;
		b.bShown = true;
		ch->RemoveAffect(AFFECT_REVIVE_INVISIBLE);
		if (reached)
		{
			++s_kPlayerBotDeathloop.fleeReached;
			ch->Stop();
		}
		else
			++s_kPlayerBotDeathloop.fleeTimedOut;
		PlayerBotLogThrottled("deathloop_flee", dwNow,
				"PLAYERBOT_DEATHLOOP: flee pid=%u name=%s level=%u map=%ld from=(%ld,%ld) to=(%ld,%ld) dist=%d mobs=%d repeat=%d "
				"hidden_ms=%u reached=%d left=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), b.lFleeFromX, b.lFleeFromY,
				b.lFleeX, b.lFleeY, b.iFleeDist, b.iMobs, b.bRepeat ? 1 : 0, dwNow - b.dwFleeStart, reached ? 1 : 0, left);
		return false;
	}

	// The recovery after a flee goes on visibly (no renewed revive protection): the safe point is the protection.
	bool IsPlayerBotDeathloopRecoveryShown(DWORD pid)
	{
		std::map<DWORD, TPlayerBotDeathloopBot>::const_iterator it = s_mapPlayerBotDeathloop.find(pid);
		return it != s_mapPlayerBotDeathloop.end() && (it->second.bShown || it->second.bFleeing);
	}

	// The Monkey map's errand: a map the bot loops on (GetPlayerBotMonkeyMapFor). The level bands are
	// GetPlayerBotMonkeyMinLevel's (playerbot_types.h).
	bool IsPlayerBotDeathloopMonkeyBlocked(LPCHARACTER ch, long map)
	{
		if (!ch || !IsPlayerBotDeathloopOn())
			return false;
		std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDeathloop.end())
			return false;
		std::map<long, DWORD>::iterator a = it->second.avoid.find(map);
		if (a == it->second.avoid.end())
			return false;
		if ((int)(get_dword_time() - a->second) < 0)
			return true;
		it->second.avoid.erase(a);
		return false;
	}

	// The tick: the Law of Advancement's death pin cleared once the bot stands on the easier map; the census.
	void ManagePlayerBotDeathloop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		static DWORD s_dwNextCensus = 0;
		if (s_dwNextCensus == 0)
			s_dwNextCensus = dwNow + PLAYERBOT_DEATHLOOP_CENSUS_MS;
		if ((int)(dwNow - s_dwNextCensus) >= 0)
		{
			s_dwNextCensus = dwNow + PLAYERBOT_DEATHLOOP_CENSUS_MS;
			unsigned int avoiding = 0;
			for (std::map<DWORD, TPlayerBotDeathloopBot>::const_iterator it = s_mapPlayerBotDeathloop.begin();
					it != s_mapPlayerBotDeathloop.end(); ++it)
				avoiding += it->second.avoid.empty() ? 0U : 1U;
			const TPlayerBotDeathloopStats& s = s_kPlayerBotDeathloop;
			sys_log(0, "PLAYERBOT_DEATHLOOP: census on=%d deaths=%u revived_in_place=%u flee=%u flee_reached=%u "
					"flee_timed_out=%u flee_failed=%u town=%u loops=%u avoiding_now=%u pins_cleared=%u monkey_medium_min=%d "
					"monkey_hard_min=%d deaths_h=%d",
					IsPlayerBotDeathloopOn() ? 1 : 0, s.deaths, s.inPlace, s.flee, s.fleeReached, s.fleeTimedOut, s.fleeFailed,
					s.town, s.loops, avoiding, s.pinsCleared, GetPlayerBotMonkeyMinLevel(false), GetPlayerBotMonkeyMinLevel(true),
					GetPlayerBotSurviveDeathsPerHour());
			s_kPlayerBotDeathloop = TPlayerBotDeathloopStats();
		}
		if (!ch || ch->IsDead())
			return;
		// a recovery that is over ends the flee's visible rest
		if (!state.bRecoveringAfterDeath)
		{
			std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
			if (it != s_mapPlayerBotDeathloop.end())
				it->second.bShown = it->second.bFleeing = false;
		}
		if (!IsPlayerBotDeathloopOn())
			return;
		TPlayerBotPersona& p = state.persona;
		if (!p.bLockPinned || p.bAdvanced)
			return;
		const long here = ch->GetMapIndex();
		if (here >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return;
		const char* how = NULL;
		long from = 0;
		// the step down's easier map
		std::map<DWORD, TPlayerBotSurviveBot>::const_iterator sv = s_mapPlayerBotSurvive.find(ch->GetPlayerID());
		if (sv != s_mapPlayerBotSurvive.end() && !sv->second.hard.empty() && sv->second.lStepMap != 0 &&
				sv->second.lStepMap == here)
		{
			how = "step_down";
			from = sv->second.lStepFrom;
		}
		// a loop's map left for another hunting ground, not a harder one
		if (!how)
		{
			std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
			if (it != s_mapPlayerBotDeathloop.end() && it->second.lLoopMap != 0 && it->second.lLoopMap != here)
			{
				const int hereLevel = GetPlayerBotSurviveMapLevel(here);
				const bool easier = hereLevel >= 0 && (it->second.iLoopMapLevel < 0 || hereLevel < it->second.iLoopMapLevel);
				if (easier && !IsPlayerBotSafeZone(here, ch->GetX(), ch->GetY()))
				{
					how = "loop_left";
					from = it->second.lLoopMap;
					it->second.lLoopMap = 0;
				}
			}
		}
		if (!how)
			return;
		p.bLockPinned = false;
		p.bDirty = true;
		++s_kPlayerBotDeathloop.pinsCleared;
		PlayerBotLogThrottled("deathloop_pin", dwNow,
				"PLAYERBOT_DEATHLOOP: pin cleared pid=%u name=%s level=%u lock=%u map=%ld from=%ld how=%s",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)p.bLockLevel, here, from, how);
	}
}

#endif
