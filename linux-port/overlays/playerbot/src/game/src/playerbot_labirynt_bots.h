#ifndef __INC_METIN2_PLAYERBOT_LABIRYNT_BOTS_H__
#define __INC_METIN2_PLAYERBOT_LABIRYNT_BOTS_H__

// MT2009_PLUS_BOT_LABIRYNT_V1 - the bots go through Labirynt (map 79, labirynth.quest), as a player does
// ("nauczmy boty korzystac z dungeonow Yohary", the owner, 5 November 2026).
//
// The quest: Min-Sun (20402) on Pustynia Yongbi (63, 1467,1365) lets in a character with the Demon Tower's sixth
// floor done (deviltower_zone.6_done), alone (no party), once (labirynth.complete; the state "complete" after it):
// d.join(79) - a new instance, the map's Town.txt spot (12,10) - and at the login inside Min-Sun stands at the maze's
// heart (131,126), the way back is set to 63 (3513,6224) and ten minutes run. The one who reaches him and talks is
// done (complete = 1, d.exit_all); back on 63 the reward state opens his shop for good.
//
// A bot (one at a time a core, PLAYERBOT_LABIRYNT_MAX; a call every PLAYERBOT_LABIRYNT_PLAN_MS with
// PLAYERBOT_LABIRYNT_PLAN_CHANCE):
//   * who: a bot of this core (it hosts 63 and 79 - game1) with the sixth floor done, the quest not complete, in no
//     party, free (GetPlayerBotLfgRefusal) and out of its rest;
//   * the way: to Min-Sun on the desert (the map change every move of the AI is, then a walk), then what his dialog
//     does - a new instance of 79, the bot at its Town.txt spot, Min-Sun put at the heart, the way back set;
//   * inside: the bot walks the maze to Min-Sun (the navigation's route through the corridors); within
//     PLAYERBOT_LABIRYNT_TALK_RANGE of him it is done - the quest's flag and state as the dialog and the login on 63
//     set them - and it goes back to 63 by the quest's own way back. Ten minutes (and a margin) without him: out the
//     same way, nothing gained, and a rest of PLAYERBOT_LABIRYNT_REST_FAIL_MS before it tries again.
//   * it is a run to every other pass (IsPlayerBotOnDungeonRun), so nothing else takes it away meanwhile; the
//     DUNGEONS switch of the bots' dungeon runs (IsPlayerBotDgRunOn) stops new calls.
//
// The log: PLAYERBOT_LABIRYNT lines - called, entered, done, timeout, refused, out; a census every 30 minutes
// (candidates, done in all, runs).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_dungeon_runs.h (its switch and
// the finder's refusal).

namespace
{
	const long PLAYERBOT_LABIRYNT_MAP = 79;
	const long PLAYERBOT_LABIRYNT_DESERT = 63;
	const DWORD PLAYERBOT_LABIRYNT_NPC = 20402;
	// Min-Sun on the desert (cells: the map's base 2048,4864 + 1467,1365) and the quest's way back (3513,6224).
	const long PLAYERBOT_LABIRYNT_NPC_X = (2048 + 1467) * 100;
	const long PLAYERBOT_LABIRYNT_NPC_Y = (4864 + 1365) * 100;
	const long PLAYERBOT_LABIRYNT_BACK_CX = 3513;
	const long PLAYERBOT_LABIRYNT_BACK_CY = 6224;
	// Min-Sun at the maze's heart (local cells, the quest's d.spawn_mob).
	const long PLAYERBOT_LABIRYNT_HEART_LX = 131;
	const long PLAYERBOT_LABIRYNT_HEART_LY = 126;
	const int PLAYERBOT_LABIRYNT_TALK_RANGE = 300;
	const int PLAYERBOT_LABIRYNT_MAX = 1;
	const DWORD PLAYERBOT_LABIRYNT_PLAN_MS = 3 * 60 * 1000;
	const int PLAYERBOT_LABIRYNT_PLAN_CHANCE = 60;
	const DWORD PLAYERBOT_LABIRYNT_FIRST_PLAN_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_LABIRYNT_WALK_MS = 4 * 60 * 1000;		// to Min-Sun on the desert
	const DWORD PLAYERBOT_LABIRYNT_LIMIT_MS = 10 * 60 * 1000 + 30 * 1000;	// the quest's ten minutes, and a margin
	const DWORD PLAYERBOT_LABIRYNT_REST_FAIL_MS = 3 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_LABIRYNT_REST_REFUSED_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_LABIRYNT_CENSUS_MS = 30 * 60 * 1000;

	enum EPlayerBotLabiryntPhase
	{
		LABIRYNT_PHASE_WALK = 1,	// to Min-Sun on the desert
		LABIRYNT_PHASE_MAZE,		// in the maze
		LABIRYNT_PHASE_OUT		// done or out of time: the way back
	};

	struct TPlayerBotLabiryntRun
	{
		BYTE bPhase;
		DWORD dwCalledAt, dwPhaseSince, dwNextMove;
		long lInstance;
		long lHeartX, lHeartY;
		bool bDone;
		int iBestDist;
		DWORD dwBestAt;
		TPlayerBotLabiryntRun() : bPhase(LABIRYNT_PHASE_WALK), dwCalledAt(0), dwPhaseSince(0), dwNextMove(0), lInstance(0),
				lHeartX(0), lHeartY(0), bDone(false), iBestDist(INT_MAX), dwBestAt(0) {}
	};
	std::map<DWORD, TPlayerBotLabiryntRun> s_mapPlayerBotLabirynt;
	std::map<DWORD, DWORD> s_mapPlayerBotLabiryntRest;
	unsigned int s_uPlayerBotLabiryntCalled = 0, s_uPlayerBotLabiryntDone = 0, s_uPlayerBotLabiryntTimeout = 0;

	bool IsPlayerBotOnLabiryntRun(DWORD pid)
	{
		return !s_mapPlayerBotLabirynt.empty() && s_mapPlayerBotLabirynt.count(pid) != 0;
	}

	int GetPlayerBotLabiryntCompleteState()
	{
		static int s_iState = -2;
		if (s_iState == -2)
		{
			const int idx = quest::CQuestManager::instance().GetQuestStateIndex("labirynth", "complete");
			s_iState = idx > 0 ? idx : -1;
		}
		return s_iState;
	}

	// The quest done once: the state "complete", or the flag of a talk not yet rewarded.
	bool HasPlayerBotLabiryntDone(LPCHARACTER ch)
	{
		const int complete = GetPlayerBotLabiryntCompleteState();
		if (complete > 0 && ch->GetQuestFlag("labirynth.__status") == complete)
			return true;
		return ch->GetQuestFlag("labirynth.complete") > 0;
	}

	bool IsPlayerBotLabiryntCandidate(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || ch->GetParty() || ch->GetLevel() < 40)
			return false;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotLabiryntRest.find(pid);
		if (rest != s_mapPlayerBotLabiryntRest.end() && (int)(dwNow - rest->second) < 0)
			return false;
		if (ch->GetQuestFlag("deviltower_zone.6_done") < 1 || HasPlayerBotLabiryntDone(ch))
			return false;
		if (IsPlayerBotOnDungeonRun(pid) || IsPlayerBotYoharaCohortPID(pid))
			return false;
		return GetPlayerBotLfgRefusal(ch, state, dwNow) == NULL;
	}

	void EndPlayerBotLabirynt(LPCHARACTER ch, const char* result, DWORD restMs, DWORD dwNow)
	{
		if (!ch)
			return;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotLabiryntRun>::iterator it = s_mapPlayerBotLabirynt.find(pid);
		if (it == s_mapPlayerBotLabirynt.end())
			return;
		sys_log(0, "PLAYERBOT_LABIRYNT: over pid=%u name=%s level=%u result=%s took_s=%u map=%ld",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), result,
				it->second.dwCalledAt ? (dwNow - it->second.dwCalledAt) / 1000 : 0, ch->GetMapIndex());
		s_mapPlayerBotLabirynt.erase(it);
		if (restMs)
			s_mapPlayerBotLabiryntRest[pid] = dwNow + restMs;
	}

	// What Min-Sun's dialog does for a player: a new maze, the bot at its spot, Min-Sun at the heart, the way back.
	bool EnterPlayerBotLabirynt(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotLabiryntRun& run, DWORD dwNow)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(PLAYERBOT_LABIRYNT_MAP);
		if (!pMap)
			return false;
		LPDUNGEON d = CDungeonManager::instance().Create(PLAYERBOT_LABIRYNT_MAP);
		if (!d)
		{
			PlayerBotLogThrottled("labirynt_create", dwNow, "PLAYERBOT_LABIRYNT: instance refused pid=%u name=%s",
					ch->GetPlayerID(), ch->GetName());
			return false;
		}
		const long instance = d->GetMapIndex();
		ch->SetWarpLocation(PLAYERBOT_LABIRYNT_DESERT, PLAYERBOT_LABIRYNT_BACK_CX, PLAYERBOT_LABIRYNT_BACK_CY);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ClearPlayerBotRoute(state, true);
		s_szPlayerBotTransitionRefusal = NULL;
		run.lInstance = instance;	// the move's own check (IsPlayerBotOwnLairRunMove) reads it
		if (!CPlayerBotManager::instance().WarpBot(ch, pMap->m_setting.posSpawn.x, pMap->m_setting.posSpawn.y, instance) ||
				ch->GetMapIndex() != instance)
		{
			sys_log(0, "PLAYERBOT_LABIRYNT: way in refused pid=%u name=%s instance=%ld refused=%s", ch->GetPlayerID(),
					ch->GetName(), instance, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "?");
			s_szPlayerBotTransitionRefusal = NULL;
			run.lInstance = 0;
			CDungeonManager::instance().Destroy(d->GetId());
			return false;
		}
		s_szPlayerBotTransitionRefusal = NULL;
		d->SpawnMob(PLAYERBOT_LABIRYNT_NPC, PLAYERBOT_LABIRYNT_HEART_LX, PLAYERBOT_LABIRYNT_HEART_LY);
		run.lHeartX = pMap->m_setting.iBaseX + PLAYERBOT_LABIRYNT_HEART_LX * 100;
		run.lHeartY = pMap->m_setting.iBaseY + PLAYERBOT_LABIRYNT_HEART_LY * 100;
		run.bPhase = LABIRYNT_PHASE_MAZE;
		run.dwPhaseSince = dwNow;
		run.iBestDist = INT_MAX;
		run.dwBestAt = dwNow;
		sys_log(0, "PLAYERBOT_LABIRYNT: entered pid=%u name=%s level=%u instance=%ld", ch->GetPlayerID(), ch->GetName(),
				(unsigned int)ch->GetLevel(), instance);
		return true;
	}

	// The quest's end for the one who reached Min-Sun: complete, and the reward state's step (his shop) done.
	void FinishPlayerBotLabiryntQuest(LPCHARACTER ch)
	{
		const int complete = GetPlayerBotLabiryntCompleteState();
		quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
		if (pc && complete > 0)
		{
			pc->SetQuestState("labirynth", complete);
			ch->SetQuestFlag("labirynth.complete", 0);
		}
		else
			ch->SetQuestFlag("labirynth.complete", 1);
	}

	// The tick: true while it holds the bot.
	bool ManagePlayerBotLabiryntBot(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || s_mapPlayerBotLabirynt.empty())
			return false;
		std::map<DWORD, TPlayerBotLabiryntRun>::iterator it = s_mapPlayerBotLabirynt.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotLabirynt.end())
			return false;
		TPlayerBotLabiryntRun& run = it->second;
		if (ch->IsDead())
			return false;
		state.dwLastMeaningfulActivityTime = dwNow;
		const long map = ch->GetMapIndex();
		switch (run.bPhase)
		{
			case LABIRYNT_PHASE_WALK:
			{
				if (dwNow - run.dwPhaseSince > PLAYERBOT_LABIRYNT_WALK_MS || ch->GetParty())
				{
					EndPlayerBotLabirynt(ch, ch->GetParty() ? "party" : "walk_timeout", PLAYERBOT_LABIRYNT_REST_REFUSED_MS, dwNow);
					return false;
				}
				if (map != PLAYERBOT_LABIRYNT_DESERT)
				{
					if ((int)(dwNow - run.dwNextMove) < 0)
						return true;
					run.dwNextMove = dwNow + 5000;
					if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_LABIRYNT_DESERT, PLAYERBOT_LABIRYNT_NPC_X - 300,
							PLAYERBOT_LABIRYNT_NPC_Y - 300, dwNow, "labirynt_go"))
					{
						EndPlayerBotLabirynt(ch, "go_refused", PLAYERBOT_LABIRYNT_REST_REFUSED_MS, dwNow);
						return false;
					}
					return true;
				}
				const int d = DISTANCE_APPROX(ch->GetX() - PLAYERBOT_LABIRYNT_NPC_X, ch->GetY() - PLAYERBOT_LABIRYNT_NPC_Y);
				if (d > PLAYERBOT_LABIRYNT_TALK_RANGE)
				{
					SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
					MovePlayerBot(ch, PLAYERBOT_LABIRYNT_NPC_X, PLAYERBOT_LABIRYNT_NPC_Y, dwNow, 6, true, false);
					return true;
				}
				if (ch->IsStateMove())
					ch->Stop();
				if (!EnterPlayerBotLabirynt(ch, state, run, dwNow))
				{
					EndPlayerBotLabirynt(ch, "enter_refused", PLAYERBOT_LABIRYNT_REST_REFUSED_MS, dwNow);
					return false;
				}
				return true;
			}
			case LABIRYNT_PHASE_MAZE:
			{
				if (map != run.lInstance)
				{
					// Out by another way (the quest's d.exit_all, a GM): over.
					EndPlayerBotLabirynt(ch, run.bDone ? "done" : "left", run.bDone ? 0 : PLAYERBOT_LABIRYNT_REST_FAIL_MS, dwNow);
					return false;
				}
				const int d = DISTANCE_APPROX(ch->GetX() - run.lHeartX, ch->GetY() - run.lHeartY);
				if (d < run.iBestDist - 200)
				{
					run.iBestDist = d;
					run.dwBestAt = dwNow;
				}
				if (d <= PLAYERBOT_LABIRYNT_TALK_RANGE)
				{
					if (ch->IsStateMove())
						ch->Stop();
					run.bDone = true;
					FinishPlayerBotLabiryntQuest(ch);
					++s_uPlayerBotLabiryntDone;
					sys_log(0, "PLAYERBOT_LABIRYNT: done pid=%u name=%s level=%u took_s=%u done_total=%u", ch->GetPlayerID(),
							ch->GetName(), (unsigned int)ch->GetLevel(), (dwNow - run.dwPhaseSince) / 1000, s_uPlayerBotLabiryntDone);
					run.bPhase = LABIRYNT_PHASE_OUT;
					run.dwPhaseSince = dwNow;
					run.dwNextMove = dwNow + 2000;	// a word with Min-Sun first
					return true;
				}
				if (dwNow - run.dwPhaseSince > PLAYERBOT_LABIRYNT_LIMIT_MS)
				{
					++s_uPlayerBotLabiryntTimeout;
					sys_log(0, "PLAYERBOT_LABIRYNT: timeout pid=%u name=%s level=%u distance=%d best=%d timeouts=%u",
							ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), d, run.iBestDist,
							s_uPlayerBotLabiryntTimeout);
					run.bPhase = LABIRYNT_PHASE_OUT;
					run.dwPhaseSince = dwNow;
					run.dwNextMove = dwNow;
					return true;
				}
				if (dwNow - run.dwBestAt > 90 * 1000)
				{
					PlayerBotLogThrottled("labirynt_stuck", dwNow,
							"PLAYERBOT_LABIRYNT: no nearer for 90 s pid=%u name=%s pos=(%ld,%ld) distance=%d",
							ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY(), d);
					run.dwBestAt = dwNow;
					ClearPlayerBotRoute(state, false);
					state.dwNextNavPlanTime = 0;
				}
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				MovePlayerBot(ch, run.lHeartX, run.lHeartY, dwNow, 4, true, false);
				return true;
			}
			case LABIRYNT_PHASE_OUT:
			default:
			{
				if (map < PLAYERBOT_INSTANCE_MAP_INDEX_MIN || map / 10000 != PLAYERBOT_LABIRYNT_MAP)
				{
					EndPlayerBotLabirynt(ch, run.bDone ? "done" : "timeout", run.bDone ? 0 : PLAYERBOT_LABIRYNT_REST_FAIL_MS, dwNow);
					return false;
				}
				if ((int)(dwNow - run.dwNextMove) < 0)
				{
					if (ch->IsStateMove())
						ch->Stop();
					SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
					return true;
				}
				run.dwNextMove = dwNow + 5000;
				if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_LABIRYNT_DESERT, PLAYERBOT_LABIRYNT_BACK_CX * 100,
						PLAYERBOT_LABIRYNT_BACK_CY * 100, dwNow, "labirynt_out"))
					PlayerBotLogThrottled("labirynt_out_failed", dwNow, "PLAYERBOT_LABIRYNT: cannot leave pid=%u name=%s map=%ld",
							ch->GetPlayerID(), ch->GetName(), map);
				return true;
			}
		}
	}

	// The calls, the census - from CPlayerBotManager's update.
	void ManagePlayerBotLabiryntRuns(DWORD dwNow)
	{
		static DWORD s_dwStart = 0, s_dwNextPlan = 0, s_dwNextCensus = 0;
		if (s_dwStart == 0)
		{
			s_dwStart = dwNow ? dwNow : 1;
			s_dwNextPlan = dwNow + PLAYERBOT_LABIRYNT_FIRST_PLAN_MS;
			s_dwNextCensus = dwNow + PLAYERBOT_LABIRYNT_CENSUS_MS;
		}
		// A run whose bot is gone (logged out, another core): over.
		for (std::map<DWORD, TPlayerBotLabiryntRun>::iterator it = s_mapPlayerBotLabirynt.begin(); it != s_mapPlayerBotLabirynt.end();)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || dwNow - it->second.dwCalledAt > PLAYERBOT_LABIRYNT_WALK_MS + PLAYERBOT_LABIRYNT_LIMIT_MS + 5 * 60 * 1000)
			{
				sys_log(0, "PLAYERBOT_LABIRYNT: over pid=%u result=%s", it->first, ch ? "stale" : "gone");
				s_mapPlayerBotLabiryntRest[it->first] = dwNow + PLAYERBOT_LABIRYNT_REST_REFUSED_MS;
				s_mapPlayerBotLabirynt.erase(it++);
				continue;
			}
			++it;
		}
		const bool census = (int)(dwNow - s_dwNextCensus) >= 0;
		const bool plan = (int)(dwNow - s_dwNextPlan) >= 0;
		if (!census && !plan)
			return;
		if (plan)
			s_dwNextPlan = dwNow + PLAYERBOT_LABIRYNT_PLAN_MS;
		if (census)
			s_dwNextCensus = dwNow + PLAYERBOT_LABIRYNT_CENSUS_MS;
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_LABIRYNT_MAP) || !IsPlayerBotMapHostedHere(PLAYERBOT_LABIRYNT_DESERT) ||
				!SECTREE_MANAGER::instance().GetMap(PLAYERBOT_LABIRYNT_MAP))
			return;
		const bool on = IsPlayerBotDgRunOn(dwNow);
		const bool call = plan && on && (int)s_mapPlayerBotLabirynt.size() < PLAYERBOT_LABIRYNT_MAX &&
				number(1, 100) <= PLAYERBOT_LABIRYNT_PLAN_CHANCE;
		if (!call && !census)
			return;
		std::vector<DWORD> candidates;
		int done = 0, towerSix = 0;
		for (TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
			if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot())
				continue;
			if (census)
			{
				if (ch->GetQuestFlag("deviltower_zone.6_done") > 0)
					++towerSix;
				if (HasPlayerBotLabiryntDone(ch))
					++done;
			}
			if (IsPlayerBotLabiryntCandidate(ch, st->second, dwNow))
				candidates.push_back(st->first);
		}
		if (census)
			sys_log(0, "PLAYERBOT_LABIRYNT: census tower6=%d done=%d candidates=%u running=%u called=%u done_total=%u timeouts=%u on=%d",
					towerSix, done, (unsigned int)candidates.size(), (unsigned int)s_mapPlayerBotLabirynt.size(),
					s_uPlayerBotLabiryntCalled, s_uPlayerBotLabiryntDone, s_uPlayerBotLabiryntTimeout, on ? 1 : 0);
		if (!call || candidates.empty())
			return;
		const DWORD pid = candidates[number(0, (int)candidates.size() - 1)];
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (!ch)
			return;
		TPlayerBotLabiryntRun& run = s_mapPlayerBotLabirynt[pid];
		run = TPlayerBotLabiryntRun();
		run.dwCalledAt = dwNow;
		run.dwPhaseSince = dwNow;
		++s_uPlayerBotLabiryntCalled;
		sys_log(0, "PLAYERBOT_LABIRYNT: called pid=%u name=%s level=%u map=%ld candidates=%u called_total=%u", pid,
				ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), (unsigned int)candidates.size(),
				s_uPlayerBotLabiryntCalled);
	}

	bool IsPlayerBotLabiryntRunMove(LPCHARACTER ch, long targetMap)
	{
		if (!ch || s_mapPlayerBotLabirynt.empty())
			return false;
		std::map<DWORD, TPlayerBotLabiryntRun>::const_iterator it = s_mapPlayerBotLabirynt.find(ch->GetPlayerID());
		return it != s_mapPlayerBotLabirynt.end() && it->second.lInstance != 0 && targetMap == it->second.lInstance;
	}
}

#endif
