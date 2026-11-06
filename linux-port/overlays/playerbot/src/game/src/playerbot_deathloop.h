#ifndef __INC_METIN2_PLAYERBOT_DEATHLOOP_H__
#define __INC_METIN2_PLAYERBOT_DEATHLOOP_H__

// MT2009_PLUS_BOT_DEATHLOOP_V1 - the death loop (the analysis of 83.168.110.166, 6 November 2026,
// dist/aktualizacje/test-plus/ANALIZA-BOTOW-83.168.110.166-2026-11-06.md): 9 838 "death detected" an hour on ch2, 9 828
// of them "revived at same position" - every bot of every level stood up where it fell, with 20% of its health, among the
// monsters that had just killed it, and fell again ~11 s later (a level-49 bot on map 109: 159 deaths in one hour; 88
// bots of 30+ an hour; 4 868 of them in the Monkey Dungeons 108/109, where the medal droppers of 33-35 stood in the
// medium one). Sung Ma residents had their own pack check (MovePlayerBotSungmaRevived, 1499e511); nobody else had any.
//
// 1. The revive (HandleDeath, playerbot_survival.h): before a bot stands up where it lies, the monsters round the body
//    are counted - awake (on anybody) or aggressive and idle, within PLAYERBOT_DEATHLOOP_MOB_RADIUS. More than
//    PLAYERBOT_DEATHLOOP_MOBS_MAX of them, or the PLAYERBOT_DEATHLOOP_TOWN_DEATHS-th death on the same spot
//    (PLAYERBOT_DEATHLOOP_SPOT_RADIUS) within PLAYERBOT_DEATHLOOP_WINDOW_MIN minutes: it stands up at the map's
//    restart-in-town point instead (the map's recall point of its kingdom - town.txt, what restart_town uses; a Monkey
//    Dungeon's arrival by its exit; else the map's arrival), on the same map, as a person's "restart in town" there.
// 2. The loop (PLAYERBOT_DEATHLOOP_AVOID_DEATHS deaths on the same spot in the window): the map is avoided for
//    PLAYERBOT_DEATHLOOP_AVOID_MIN minutes - on a 2.x hunting map through the step down of playerbot_survive.h (the map
//    marked hard: its frontier draw answers an easier map at once, with the materials order there, instead of after
//    PLAYERBOT_SURVIVE_DEATHS_H deaths an hour); a Monkey Dungeon is not chosen by the medal errand
//    (GetPlayerBotMonkeyMapFor); and the spot itself is the persona's avoided spot (the targeting and the hub choice
//    leave it alone) unless a capitulation already holds one.
// 3. The pin: a bot the Law of Advancement pinned after its deaths (3 in 30 min, NotePlayerBotPersonaDeath) has the pin
//    cleared once it stands on the easier map (the step down's map, or any other hunting ground after a loop's) - the
//    deaths that pinned it were the map's, not its gear's.
// 4. The Monkey Dungeons alone (GetPlayerBotMonkeyMapFor): a bot under PLAYERBOT_DEATHLOOP_MONKEY2_MIN (36) is not sent
//    to the medium one (108), nor one under PLAYERBOT_DEATHLOOP_MONKEY3_MIN (55) to the hard one (109), unless it is in a
//    party - the band's next lower dungeon instead.
//
// Not touched: the Zodiac temple's revive, the companion held in it, a dungeon instance or the Demon Tower's business,
// a guild war, a Sung Ma resident (its own pack check and safe point).
// Switches: event flag m2_bot_deathloop_off 1 - all of it off (in-place revival as before); m2_bot_deathloop_monkey_off
// 1 - the Monkey Dungeon level gate alone. Env PLAYERBOT_DEATHLOOP_MOB_RADIUS (1500), _MOBS_MAX (3), _SPOT_RADIUS
// (3000), _WINDOW_MIN (10), _TOWN_DEATHS (2), _AVOID_DEATHS (3), _AVOID_MIN (60), _MONKEY2_MIN (36), _MONKEY3_MIN (55).
// The log: PLAYERBOT_DEATHLOOP: lines - town revive / loop / pin cleared (throttled), census every 10 minutes.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_survive.h; the earlier headers ask its
// hooks through declarations (playerbot_survival.h, playerbot_travel.h).

namespace
{
	const DWORD PLAYERBOT_DEATHLOOP_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_DEATHLOOP_MAX_DEATHS_KEPT = 8;

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

	bool IsPlayerBotDeathloopMonkeyGateOn()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			s_bOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_deathloop_monkey_off") == 0;
		}
		return s_bOn && IsPlayerBotDeathloopOn();
	}

	struct TPlayerBotDeathloopConfig
	{
		int mobRadius, mobsMax, spotRadius, townDeaths, avoidDeaths, monkey2Min, monkey3Min;
		DWORD windowMs, avoidMs;
	};

	const TPlayerBotDeathloopConfig& GetPlayerBotDeathloopConfig()
	{
		static bool s_bRead = false;
		static TPlayerBotDeathloopConfig c;
		if (!s_bRead)
		{
			s_bRead = true;
			c.mobRadius = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_MOB_RADIUS", 1500, 300, 6000);
			c.mobsMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_MOBS_MAX", 3, 0, 50);
			c.spotRadius = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_SPOT_RADIUS", 3000, 300, 20000);
			c.windowMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_WINDOW_MIN", 10, 1, 120) * 60000U;
			c.townDeaths = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_TOWN_DEATHS", 2, 2, 10);
			c.avoidDeaths = std::max(c.townDeaths, ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_AVOID_DEATHS", 3, 2, 20));
			c.avoidMs = (DWORD)ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_AVOID_MIN", 60, 5, 24 * 60) * 60000U;
			c.monkey2Min = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_MONKEY2_MIN", 36, 1, 250);
			c.monkey3Min = ReadPlayerBotYoharaEnvInt("PLAYERBOT_DEATHLOOP_MONKEY3_MIN", 55, 1, 250);
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
		std::deque<TPlayerBotDeathloopDeath> deaths;
		bool bTownNext;			// the next stand-up is at the town point (decided on the death's tick)
		const char* szWhy;
		int iMobs;
		std::map<long, DWORD> avoid;	// map -> until
		long lLoopMap;			// the map of the last loop, for the pin
		int iLoopMapLevel;		// its survive row's entry level (-1: none)
		TPlayerBotDeathloopBot() : bTownNext(false), szWhy(""), iMobs(0), lLoopMap(0), iLoopMapLevel(-1) {}
	};
	std::map<DWORD, TPlayerBotDeathloopBot> s_mapPlayerBotDeathloop;

	struct TPlayerBotDeathloopStats
	{
		unsigned int deaths, inPlace, townMobs, townRepeat, townFailed, loops, pinsCleared, monkeyGateHits;
		TPlayerBotDeathloopStats() : deaths(0), inPlace(0), townMobs(0), townRepeat(0), townFailed(0), loops(0),
				pinsCleared(0), monkeyGateHits(0) {}
	};
	TPlayerBotDeathloopStats s_kPlayerBotDeathloop;

	// The monsters round (x, y) that would be on a bot standing up there: awake (on anybody) or aggressive.
	class FCountPlayerBotDeathloopMobs
	{
		public:
			FCountPlayerBotDeathloopMobs(long map, long x, long y, int radius) : m_map(map), m_x(x), m_y(y), m_radius(radius),
					m_count(0) {}
			void operator()(LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER))
					return;
				LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
				if (!mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_map ||
						DISTANCE_APPROX(mob->GetX() - m_x, mob->GetY() - m_y) > m_radius)
					return;
				if (mob->GetVictim() != NULL || IS_SET(mob->GetMobTable().dwAIFlag, AIFLAG_AGGRESSIVE))
					++m_count;
			}
			long m_map, m_x, m_y;
			int m_radius, m_count;
	};

	int CountPlayerBotDeathloopMobs(long map, long x, long y)
	{
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(map, x, y);
		if (!tree)
			return 0;
		FCountPlayerBotDeathloopMobs f(map, x, y, GetPlayerBotDeathloopConfig().mobRadius);
		tree->ForEachAround(f);
		return f.m_count;
	}

	// Whose deaths this is about: not a dungeon instance's, the Demon Tower's, a guild war's or a Sung Ma resident's.
	bool IsPlayerBotDeathloopCase(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		return ch && IsPlayerBotDeathloopOn() && !IsPlayerBotInDungeonBusiness(ch, state) &&
				state.dwGuildWarEnemyGID == 0 && !IsPlayerBotSungmaResidentPID(ch->GetPlayerID());
	}

	// The map's restart-in-town point for this bot, on the same map.
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

	// The map marked avoided: the step down's hard map on a 2.x hunting map (playerbot_survive.h), the persona's
	// avoided spot, the Monkey Dungeon's errand.
	void MarkPlayerBotDeathloopAvoid(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDeathloopBot& b, long map, long x,
			long y, int deathsHere, DWORD dwNow)
	{
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		b.avoid[map] = dwNow + c.avoidMs;
		b.lLoopMap = map;
		b.iLoopMapLevel = GetPlayerBotSurviveMapLevel(map);
		const bool stepped = MarkPlayerBotSurviveHard(ch, map, c.avoidMs, "deathloop");
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
				"PLAYERBOT_DEATHLOOP: loop pid=%u name=%s level=%u map=%ld pos=(%ld,%ld) deaths_here=%d avoid_min=%u step_down=%d party=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), map, x, y, deathsHere,
				(unsigned int)(c.avoidMs / 60000U), stepped ? 1 : 0, ch->GetParty() ? 1 : 0);
	}

	// HandleDeath, the tick a death is noticed (after the step down's own count).
	void NotePlayerBotDeathloopDeath(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!IsPlayerBotDeathloopCase(ch, state))
			return;
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		TPlayerBotDeathloopBot& b = s_mapPlayerBotDeathloop[ch->GetPlayerID()];
		++s_kPlayerBotDeathloop.deaths;
		const long map = ch->GetMapIndex(), x = ch->GetX(), y = ch->GetY();
		while (!b.deaths.empty() && (dwNow - b.deaths.front().at >= c.windowMs ||
				b.deaths.size() >= (size_t)PLAYERBOT_DEATHLOOP_MAX_DEATHS_KEPT))
			b.deaths.pop_front();
		const int mobs = CountPlayerBotDeathloopMobs(map, x, y);
		// a death with no monster round the body is a player's (the arena, a duel, a kingdom's war): no loop of ours
		int here = 0;
		if (mobs > 0)
		{
			TPlayerBotDeathloopDeath d;
			d.at = dwNow;
			d.map = map;
			d.x = x;
			d.y = y;
			b.deaths.push_back(d);
			for (size_t i = 0; i < b.deaths.size(); ++i)
				if (b.deaths[i].map == map &&
						DISTANCE_APPROX(b.deaths[i].x - x, b.deaths[i].y - y) <= c.spotRadius)
					++here;
		}
		b.iMobs = mobs;
		b.bTownNext = false;
		if (here >= c.townDeaths)
		{
			b.bTownNext = true;
			b.szWhy = "repeat";
		}
		else if (mobs > c.mobsMax)
		{
			b.bTownNext = true;
			b.szWhy = "mobs";
		}
		if (here >= c.avoidDeaths)
		{
			MarkPlayerBotDeathloopAvoid(ch, state, b, map, x, y, here, dwNow);
			// counted once: the next loop needs its own deaths
			std::deque<TPlayerBotDeathloopDeath> rest;
			for (size_t i = 0; i < b.deaths.size(); ++i)
				if (b.deaths[i].map != map)
					rest.push_back(b.deaths[i]);
			b.deaths.swap(rest);
		}
	}

	// HandleDeath, the bot just stood up where it lay: true when it was moved to the town point instead.
	bool MovePlayerBotDeathloopRevived(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead())
			return false;
		std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDeathloop.end() || !it->second.bTownNext || !IsPlayerBotDeathloopCase(ch, state))
		{
			++s_kPlayerBotDeathloop.inPlace;
			return false;
		}
		TPlayerBotDeathloopBot& b = it->second;
		b.bTownNext = false;
		long tx = 0, ty = 0;
		if (!GetPlayerBotDeathloopTownPoint(ch, tx, ty))
		{
			++s_kPlayerBotDeathloop.townFailed;
			PlayerBotLogThrottled("deathloop_no_town", dwNow,
					"PLAYERBOT_DEATHLOOP: no town point pid=%u name=%s map=%ld pos=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
			return false;
		}
		long ox = 0, oy = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x444c4f50U, 50, 250, ox, oy);
		if (strcmp(b.szWhy, "repeat") == 0)
			++s_kPlayerBotDeathloop.townRepeat;
		else
			++s_kPlayerBotDeathloop.townMobs;
		PlayerBotLogThrottled("deathloop_town", dwNow,
				"PLAYERBOT_DEATHLOOP: town revive pid=%u name=%s level=%u map=%ld from=(%ld,%ld) to=(%ld,%ld) why=%s mobs=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), ch->GetX(), ch->GetY(),
				tx + ox, ty + oy, b.szWhy, b.iMobs);
		ch->Stop();
		ch->Show(ch->GetMapIndex(), tx + ox, ty + oy, 0);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		return true;
	}

	// The Monkey Dungeon's errand: a map the bot loops on, or one its level is held out of alone (GetPlayerBotMonkeyMapFor).
	bool IsPlayerBotDeathloopMonkeyBlocked(LPCHARACTER ch, long map)
	{
		if (!ch || !IsPlayerBotDeathloopOn())
			return false;
		std::map<DWORD, TPlayerBotDeathloopBot>::iterator it = s_mapPlayerBotDeathloop.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotDeathloop.end())
		{
			std::map<long, DWORD>::iterator a = it->second.avoid.find(map);
			if (a != it->second.avoid.end())
			{
				if ((int)(get_dword_time() - a->second) < 0)
					return true;
				it->second.avoid.erase(a);
			}
		}
		if (!IsPlayerBotDeathloopMonkeyGateOn() || ch->GetParty())
			return false;
		const TPlayerBotDeathloopConfig& c = GetPlayerBotDeathloopConfig();
		const int level = (int)ch->GetLevel();
		const bool gated = (map == PLAYERBOT_MAP_MONKEY_MEDIUM && level < c.monkey2Min) ||
				(map == PLAYERBOT_MAP_MONKEY_HARD && level < c.monkey3Min);
		if (gated)
			++s_kPlayerBotDeathloop.monkeyGateHits;
		return gated;
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
			sys_log(0, "PLAYERBOT_DEATHLOOP: census on=%d monkey_gate=%d deaths=%u revived_in_place=%u town_mobs=%u "
					"town_repeat=%u town_failed=%u loops=%u avoiding_now=%u pins_cleared=%u monkey_gate_hits=%u",
					IsPlayerBotDeathloopOn() ? 1 : 0, IsPlayerBotDeathloopMonkeyGateOn() ? 1 : 0, s.deaths, s.inPlace,
					s.townMobs, s.townRepeat, s.townFailed, s.loops, avoiding, s.pinsCleared, s.monkeyGateHits);
			s_kPlayerBotDeathloop = TPlayerBotDeathloopStats();
		}
		if (!ch || ch->IsDead() || !IsPlayerBotDeathloopOn())
			return;
		TPlayerBotPersona& p = state.persona;
		if (!p.bLockPinned || p.bAdvanced)
			return;
		const long here = ch->GetMapIndex();
		if (here >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return;
		const char* how = NULL;
		long from = 0;
		// the step down's easier map (its own deaths an hour, or a loop's mark)
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
