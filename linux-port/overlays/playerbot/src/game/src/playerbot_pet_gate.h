#ifndef __INC_METIN2_PLAYERBOT_PET_GATE_H__
#define __INC_METIN2_PLAYERBOT_PET_GATE_H__

// MT2009_PLUS_BOT_PET_GATE_V1 - the element pet at a bot's arrival and the gate's look at it (the night supervisor, 8
// November 2026: about 200 bots flipped 2-6 times in 40 minutes between "passed" and "held at 55").
//
// The cause: a bot's character is made anew at every login and channel change, and the engine's restore of the pet
// that was out (CHARACTER::EnterPet, USE_PET_SEAL_ON_LOGIN) runs at ENTERGAME - before a bot's items are loaded, so
// its list (m_loadedPetItems) is filled after it ran and nobody calls the pet. Maly Zywiolak's +10 resistance is
// counted only while the pet is out (CPetSystem::RefreshBuff), so the fire of a bot that passed gate 55 by fire read
// 45 in place of 55 at its first weighing; the gate held it, logged "held at 55 ... held_min=0", and the element
// shop (MT2009_PLUS_BOT_ELEMENT_SHOP_V1: "again" under its gate) called the pet ~30 s later and the gate let it pass.
// Measured on the test world (ch1+ch2, 19:03-20:24): 252 of 441 bots at gate 55 passed it two times or more, 472
// re-holds after a pass, 342 of them with fire under 50 (257 at exactly 45), 287 of those within 60 s of the bot's
// "entered game"; the pet came out a median 33 s after the re-hold (p90 65 s); 110 re-holds threw away the minutes
// already stood (1552 in all).
//
// What:
//   * the arrival (SummonPlayerBotPetOnArrival): a new character object of the bot on this core (a login, a channel
//     change) is an arrival; once its items are loaded and no pet is out, its element pet (Maly Zywiolak, 53290-53295)
//     is called from the bag - the seal that was out when it left (the seal's active socket), else the one of its
//     element goal (the progression's map goal, the Sung Ma hunt element), else the fire one - before the first gate
//     weighing (called from the per-bot pass and from ManagePlayerBotProgression right before the snapshot). A few
//     tries, PLAYERBOT_PETGATE_TRY_MS apart, within the grace window;
//   * the gate's credit (GetPlayerBotGatePendingPetResist): an element pet the bot owns (in the bag) and that is not
//     out counts its resistance in the gate's snapshot (playerbot_progression.h, s.fire) while no other pet is out or
//     the bot is in its arrival window - the element shop's own look is unchanged (the real resistance), so it still
//     calls the pet when it is missing;
//   * the tolerance (playerbot_progression.h): a bot that passed a gate (quest flag playerbot.prog_passed, kept over
//     logins) is not held there again for the grace window after its arrival, nor before the shortfall has lasted
//     m2_bot_gate_rehold_s; a re-hold that does come carries on the minutes stood before the pass
//     (playerbot.prog_passed_held_s), never 0.
// Event flags: m2_bot_pet_arrival_off 1 - no arrival call; m2_bot_gate_petcredit_off 1 - no credit;
// m2_bot_gate_tolerance_off 1 - no grace / debounce (the old re-hold); m2_bot_gate_grace_s N (0-3600, default 180);
// m2_bot_gate_rehold_s N (0-3600, default 120).
// The log: PLAYERBOT_PETGATE: arrival_pet (out / cannot), and PLAYERBOT_PROGRESS: rehold_wait / rehold (the
// progression's), a census every PLAYERBOT_PETGATE_CENSUS_MS.
//
// An implementation fragment (playerbot_types.h): included once from playerbot_manager.cpp after
// playerbot_element_shop.h (the element pet's vnums and its summoned seal); playerbot_progression.h declares what it
// asks of it.

#include <map>

namespace
{
	const DWORD PLAYERBOT_PETGATE_TRY_MS = 3000;
	const BYTE PLAYERBOT_PETGATE_TRIES = 8;
	const DWORD PLAYERBOT_PETGATE_GRACE_MS = 180 * 1000;
	const DWORD PLAYERBOT_PETGATE_REHOLD_MS = 120 * 1000;
	const DWORD PLAYERBOT_PETGATE_CENSUS_MS = 10 * 60 * 1000;

	struct TPlayerBotPetGateConfig
	{
		bool arrival, credit, tolerance;
		DWORD graceMs, reholdMs;
		TPlayerBotPetGateConfig() : arrival(true), credit(true), tolerance(true), graceMs(PLAYERBOT_PETGATE_GRACE_MS),
			reholdMs(PLAYERBOT_PETGATE_REHOLD_MS) {}
	};

	const TPlayerBotPetGateConfig& GetPlayerBotPetGateConfig()
	{
		static DWORD s_dwAt = 0;
		static TPlayerBotPetGateConfig s_kConfig;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			s_kConfig.arrival = q.GetEventFlag("m2_bot_pet_arrival_off") == 0;
			s_kConfig.credit = q.GetEventFlag("m2_bot_gate_petcredit_off") == 0;
			s_kConfig.tolerance = q.GetEventFlag("m2_bot_gate_tolerance_off") == 0;
			const int grace = q.GetEventFlag("m2_bot_gate_grace_s");
			s_kConfig.graceMs = grace > 0 && grace <= 3600 ? (DWORD)grace * 1000U : PLAYERBOT_PETGATE_GRACE_MS;
			const int rehold = q.GetEventFlag("m2_bot_gate_rehold_s");
			s_kConfig.reholdMs = rehold > 0 && rehold <= 3600 ? (DWORD)rehold * 1000U : PLAYERBOT_PETGATE_REHOLD_MS;
		}
		return s_kConfig;
	}

	struct TPlayerBotPetArrival
	{
		DWORD dwVid;		// the character object it was seen as (a new one: an arrival)
		DWORD dwArrived;
		DWORD dwNextTry;
		DWORD dwSeen;
		BYTE bTries;
		bool bDone;
		TPlayerBotPetArrival() : dwVid(0), dwArrived(0), dwNextTry(0), dwSeen(0), bTries(0), bDone(false) {}
	};
	std::map<DWORD, TPlayerBotPetArrival> s_mapPlayerBotPetArrival;

	struct TPlayerBotPetGateStats
	{
		unsigned int arrivals, petOut, petCannot, petAlready, petNone, credited, reholdWait, rehold;
		TPlayerBotPetGateStats() : arrivals(0), petOut(0), petCannot(0), petAlready(0), petNone(0), credited(0),
			reholdWait(0), rehold(0) {}
	};
	TPlayerBotPetGateStats s_kPlayerBotPetGate;
	DWORD s_dwPlayerBotPetGateCensus = 0;

	TPlayerBotPetArrival& TouchPlayerBotPetArrival(LPCHARACTER ch, DWORD dwNow)
	{
		TPlayerBotPetArrival& a = s_mapPlayerBotPetArrival[ch->GetPlayerID()];
		const DWORD vid = (DWORD)ch->GetVID();
		if (a.dwVid != vid)
		{
			a = TPlayerBotPetArrival();
			a.dwVid = vid;
			a.dwArrived = dwNow ? dwNow : 1;
			++s_kPlayerBotPetGate.arrivals;
		}
		a.dwSeen = dwNow;
		return a;
	}

	// How long the bot has been on this core as the character it is now (its login or channel change).
	DWORD GetPlayerBotArrivalAgeMs(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return 0xFFFFFFFFU;
		const TPlayerBotPetArrival& a = TouchPlayerBotPetArrival(ch, dwNow);
		return dwNow - a.dwArrived;
	}

	bool IsPlayerBotElementPetVnum(DWORD vnum, int* pElement)
	{
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (PLAYERBOT_ELEMPET_VNUMS[e] == vnum)
			{
				if (pElement)
					*pElement = e;
				return true;
			}
		return false;
	}

	// The bag's seal of the element (index of PLAYERBOT_ELEMPET_VNUMS, the PLAYERBOT_EM_* order), NULL for none.
	LPITEM FindPlayerBotOwnedElementPetSeal(LPCHARACTER ch, int e)
	{
		if (!ch || e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS)
			return NULL;
		return FindPlayerBotBagElementPet(ch, PLAYERBOT_ELEMPET_VNUMS[e]);
	}

	// The gate's credit: the resistance of element e the bot's own element pet gives once out, when it is not out yet
	// (none out, or the bot in its arrival window). 0 otherwise.
	int GetPlayerBotGatePendingPetResist(LPCHARACTER ch, int e, DWORD dwNow)
	{
		if (!ch || e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS || !GetPlayerBotPetGateConfig().credit || !ch->IsItemLoaded())
			return 0;
#if defined(__PET_SYSTEM__)
		LPITEM seal = FindPlayerBotOwnedElementPetSeal(ch, e);
		if (!seal)
			return 0;
		LPITEM out = FindPlayerBotSummonedPetSeal(ch);
		if (out == seal || (out && out->GetVnum() == seal->GetVnum()))
			return 0;	// out: the engine counts it already
		CPetSystem* pets = ch->GetPetSystem();
		const bool anyOut = out != NULL || (pets && pets->CountSummoned() > 0);
		if (anyOut && GetPlayerBotArrivalAgeMs(ch, dwNow) >= GetPlayerBotPetGateConfig().graceMs)
			return 0;	// another pet chosen out: the element shop's look decides
		const int gain = GetPlayerBotElementMapPieceValue(seal, PLAYERBOT_ELEMENT_MAP_POINTS[e]);
		if (gain > 0)
			++s_kPlayerBotPetGate.credited;
		return std::max(0, gain);
#else
		(void)dwNow;
		return 0;
#endif
	}

	// The element pet to call at the arrival: the seal out at the logout, else the goal's element, else fire.
	LPITEM PickPlayerBotArrivalElementPet(LPCHARACTER ch)
	{
		LPITEM first = NULL;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->isLocked() || item->IsExchanging() || !IsPlayerBotElementPetVnum(item->GetVnum(), NULL))
				continue;
			if (item->GetSocket(PET_SEAL_ACTIVE_SOCKET_IDX) == 1)
				return item;	// the one out when it left (USE_ACTIVE_PET_SEAL_EFFECT keeps the socket over a logout)
			if (!first)
				first = item;
		}
		if (!first)
			return NULL;
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		if (LPITEM s = FindPlayerBotOwnedElementPetSeal(ch, hunt))
			return s;
		TPlayerBotElementMapView v;
		if (GetPlayerBotElementMapGoal(ch, v))
			if (LPITEM s = FindPlayerBotOwnedElementPetSeal(ch, v.iElement))
				return s;
		if (LPITEM s = FindPlayerBotOwnedElementPetSeal(ch, PLAYERBOT_EM_FIRE))
			return s;
		return first;
	}

	// Every tick from the per-bot pass and right before the progression's snapshot: cheap but in the arrival window.
	void SummonPlayerBotPetOnArrival(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		TPlayerBotPetArrival& a = TouchPlayerBotPetArrival(ch, dwNow);
		if (a.bDone)
			return;
		const TPlayerBotPetGateConfig& c = GetPlayerBotPetGateConfig();
		if (!c.arrival || dwNow - a.dwArrived >= c.graceMs || a.bTries >= PLAYERBOT_PETGATE_TRIES)
		{
			a.bDone = true;
			return;
		}
		if (!ch->IsItemLoaded() || ch->IsDead() || !ch->GetSectree() || (a.dwNextTry != 0 && (int)(dwNow - a.dwNextTry) < 0))
			return;
		a.dwNextTry = dwNow + PLAYERBOT_PETGATE_TRY_MS;
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
		CPetSystem* pets = ch->GetPetSystem();
		if (!pets)
			return;
		if (pets->CountSummoned() > 0)
		{
			// a pet out already (its own pass, the look's): left as it is - the element passes replace it
			++s_kPlayerBotPetGate.petAlready;
			a.bDone = true;
			return;
		}
		LPITEM seal = PickPlayerBotArrivalElementPet(ch);
		if (!seal)
		{
			++s_kPlayerBotPetGate.petNone;
			a.bDone = true;
			return;
		}
		if (ch->GetExchange() || ch->GetMyShop() || !ch->CanHandleItem())
			return;	// the next try
		++a.bTries;
		if (ch->SummonPetFromItem(seal) && FindPlayerBotSummonedPetSeal(ch) == seal)
		{
			a.bDone = true;
			++s_kPlayerBotPetGate.petOut;
			int e = -1;
			IsPlayerBotElementPetVnum(seal->GetVnum(), &e);
			sys_log(0, "PLAYERBOT_PETGATE: arrival_pet out pid=%u name=%s lv=%d vnum=%u element=%s after_ms=%u resist=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), seal->GetVnum(),
					e >= 0 ? GetPlayerBotElementMapElementName(e) : "-", dwNow - a.dwArrived,
					e >= 0 ? GetPlayerBotElementMapResist(ch, e) : 0);
		}
		else
		{
			++s_kPlayerBotPetGate.petCannot;
			PlayerBotLogThrottled("petgate_arrival", dwNow,
					"PLAYERBOT_PETGATE: arrival_pet cannot pid=%u name=%s vnum=%u try=%u", ch->GetPlayerID(), ch->GetName(),
					seal->GetVnum(), (unsigned)a.bTries);
		}
#else
		a.bDone = true;
#endif
	}

	// playerbot_progression.h: the tolerance on (m2_bot_gate_tolerance_off 0), its windows
	bool IsPlayerBotGateToleranceOn(DWORD* pGraceMs, DWORD* pReholdMs)
	{
		const TPlayerBotPetGateConfig& c = GetPlayerBotPetGateConfig();
		if (pGraceMs)
			*pGraceMs = c.graceMs;
		if (pReholdMs)
			*pReholdMs = c.reholdMs;
		return c.tolerance;
	}

	void NotePlayerBotGateRehold(bool waited)
	{
		++(waited ? s_kPlayerBotPetGate.reholdWait : s_kPlayerBotPetGate.rehold);
	}

	// The census, and the stale records swept.
	void TickPlayerBotPetGateCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotPetGateCensus == 0)
		{
			s_dwPlayerBotPetGateCensus = dwNow + PLAYERBOT_PETGATE_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwPlayerBotPetGateCensus) < 0)
			return;
		s_dwPlayerBotPetGateCensus = dwNow + PLAYERBOT_PETGATE_CENSUS_MS;
		for (std::map<DWORD, TPlayerBotPetArrival>::iterator it = s_mapPlayerBotPetArrival.begin();
				it != s_mapPlayerBotPetArrival.end();)
		{
			if (dwNow - it->second.dwSeen > 60U * 60U * 1000U)
				s_mapPlayerBotPetArrival.erase(it++);
			else
				++it;
		}
		const TPlayerBotPetGateStats& s = s_kPlayerBotPetGate;
		sys_log(0, "PLAYERBOT_PETGATE: census arrivals=%u pet_out=%u pet_cannot=%u pet_already=%u no_element_pet=%u "
				"credited_weighings=%u rehold_waits=%u reholds=%u", s.arrivals, s.petOut, s.petCannot, s.petAlready,
				s.petNone, s.credited, s.reholdWait, s.rehold);
		s_kPlayerBotPetGate = TPlayerBotPetGateStats();
	}
}

#endif
