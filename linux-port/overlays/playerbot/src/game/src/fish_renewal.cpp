// MT2009_PLUS_FISHING_RENEWAL_V1 - the fishing minigame of the "fishing renewal" (the owner, 3 November 2026:
// "Nasza mini gre wedkarska zastap ta wersja", github.com/amun3808/metin2-fishing-renewal; server-patches/fishren,
// README.md). It replaces our bar minigame (fishing.cpp's fishing_event, GC 155 FISHING_GAME) for every client that
// knows the new window; the official 2022 renewal as pl-wiki "Lowienie" describes it:
//   cast the rod (space) -> "po chwili" a fish bites -> the window: a fish swims in the water, click it three times
//   while it is inside (or on the edge of) the circle in the middle, within 15 s; a miss costs a second of the timer;
//   three hits -> "sprobujesz zlapac rybe (nadal mozesz jej uniknac)" - the rod's chance (Rybie Wnetrznosci, the
//   Zloty Tunczyk premium) decides; the time out, the window closed or the rod pulled out -> the bait is lost.
//
// NO NEW EXE. The renewal needs one (a third byte in CG 82 FISHING for the result, wndMgr.AniImageSetRotation, a
// fishing cursor, a fail emoticon, two python calls from RecvFishing); ours does it all over the chat command channel
// every python-only system here uses, and the rod's motions are the exe's own GC 89 FISHING packets:
//   client -> server  "/fishren hello"                 this client has the window (root uifishingrenewal.py; every
//                                                      login and warp, game.py's hello block)
//                     "/fishren end <token> <hits>"    the game is over: the hits the player made (0-3)
//   server -> client  "FISHREN start <token> <seconds> <hits needed>"   a fish bit - open the window
//                     "FISHREN stop"                                     the cast is over - close it
// A client that never said hello (the old root, every playerbot) keeps the bar minigame of fishing.cpp untouched.
//
// The cast lives in CHARACTER::m_pkPreFishingEvent with its own event info (TFishRenInfo), so every "is he fishing"
// test of the engine and the bots (char_horse.cpp, char_item.cpp, playerbot_addeq.cpp) sees it; CHARACTER::fishing()
// hands a renewal cast to Mt2009FishRenPull before its own take (server-patches/fishren, char.cpp).
//
// The renewal itself trusts the client completely ("Validation? ... OF COURSE NOT", its Readme). Here: a random token
// per bite, the result only while that bite's game runs, three hits no sooner than MIN_GAME_MS after the window
// opened (the window allows a hit a second), no later than the limit + GRACE_MS, and the catch itself is still the
// server's chance roll - a forged "3 hits" is no more than a player who plays well.
//
// Tunable (event flags, 0 = the default): fishren_bite_min / fishren_bite_max - seconds from the cast to the bite
// (default 5-10; the old bar minigame bit after 17 s), fishren_time - the game's seconds (15), fishren_hits (3).
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "char_manager.h"
#include "item.h"
#include "packet.h"
#include "questmanager.h"
#include "utils.h"
#include "fishing.h"

#include <cstring>
#include <map>

// fishing.cpp (namespace fishing, external linkage, not in fishing.h)
namespace fishing
{
	int GetFishingChance(LPCHARACTER ch, LPITEM rod);
	void FishingReact(LPCHARACTER ch);
	void FishingFail(LPCHARACTER ch);
	void FishingPractice(LPCHARACTER ch, bool is_simulation);
	void SaveEndFishingTime(LPCHARACTER ch);
	void ProcessFishingGameSuccess(LPCHARACTER ch);
	LPITEM CheckRod(LPCHARACTER ch);
}

namespace fishren
{
	enum
	{
		STEP_WAIT_BITE = 0,
		STEP_GAME = 1,
		DEFAULT_BITE_MIN = 5,
		DEFAULT_BITE_MAX = 10,
		DEFAULT_TIME = 15,
		DEFAULT_HITS = 3,
		GRACE_MS = 3000,		// the result's way back (ping, a frame or two)
		MIN_GAME_MS = 2000,		// three hits, a second apart at the least (uifishingrenewal.HIT_WAIT)
		FISHING_QUEST_STATE_SUCCESS = 1,
		FISHING_QUEST_STATE_PREDICT = 2,
	};

	EVENTINFO(TFishRenInfo)
	{
		DWORD	pid;
		int		step;
		DWORD	token;
		DWORD	gameStart;	// get_dword_time() of the bite
		int		seconds;
		int		hits;

		TFishRenInfo() : pid(0), step(STEP_WAIT_BITE), token(0), gameStart(0), seconds(DEFAULT_TIME), hits(DEFAULT_HITS) {}
	};

	// pid -> the descriptor handle of the connection that said hello: a relog (a new handle) with an old client
	// is not taken for a new one, and nothing has to be cleaned up at logout.
	static std::map<DWORD, DWORD> s_mapHello;

	static int Flag(const char* name, int def, int lo, int hi)
	{
		const int v = quest::CQuestManager::instance().GetEventFlag(name);
		return v > 0 ? MINMAX(lo, v, hi) : def;
	}

	static bool HasHello(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc())
			return false;
		std::map<DWORD, DWORD>::const_iterator it = s_mapHello.find(ch->GetPlayerID());
		return it != s_mapHello.end() && it->second == ch->GetDesc()->GetHandle();
	}

	static TFishRenInfo* Info(LPCHARACTER ch)
	{
		if (!ch || !ch->m_pkPreFishingEvent)
			return NULL;
		return dynamic_cast<TFishRenInfo*>(ch->m_pkPreFishingEvent->info);
	}

	static void SendStop(LPCHARACTER ch)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "FISHREN stop");
	}

	static void StopMotion(LPCHARACTER ch)
	{
		TPacketGCFishing p;
		p.header = HEADER_GC_FISHING;
		p.subheader = FISHING_SUBHEADER_GC_STOP;
		p.info = ch->GetVID();
		p.dir = 0;
		ch->PacketAround(&p, sizeof(p));
	}

	// The cast is over without a catch: the rod's FAIL motion (and the client's "fishing failed" line), the bait gone.
	// bPractice: the game was played to its end (as the bar minigame lost - the rod's fishing points may rise).
	static void Lose(LPCHARACTER ch, bool bPractice)
	{
		fishing::FishingFail(ch);
		LPITEM rod = fishing::CheckRod(ch);
		if (rod)
		{
			if (bPractice)
				fishing::FishingPractice(ch, false);
			else
				rod->SetSocket(2, 0, true, "SOCKET_FISHING");
		}
		fishing::SaveEndFishingTime(ch);
		SendStop(ch);
	}

	EVENTFUNC(fishren_event)
	{
		TFishRenInfo* info = dynamic_cast<TFishRenInfo*>(event->info);
		if (!info)
		{
			sys_err("fishren_event> <Factor> Null pointer");
			return 0;
		}

		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(info->pid);
		if (!ch)
			return 0;

		if (!fishing::CheckRod(ch))
		{
			// the rod taken off or a horse mounted: the cast just ends (as fishing.cpp's pre_fishing_event)
			ch->m_pkPreFishingEvent = NULL;
			StopMotion(ch);
			SendStop(ch);
			return 0;
		}

		if (info->step == STEP_WAIT_BITE)
		{
			// the bite: the quest picks the fish now (fishing_manage.predict_fish), the rod jerks with the "!" emoticon
			quest::CQuestManager::instance().Fishing(ch->GetPlayerID(), FISHING_QUEST_STATE_PREDICT);
			ch->m_bPlayerFishReactTime = get_dword_time();
			fishing::FishingReact(ch);

			info->step = STEP_GAME;
			info->token = (DWORD)number(1, 999999999);
			info->gameStart = get_dword_time();
			info->seconds = Flag("fishren_time", DEFAULT_TIME, 5, 60);
			info->hits = Flag("fishren_hits", DEFAULT_HITS, 1, 10);
			ch->ChatPacket(CHAT_TYPE_COMMAND, "FISHREN start %u %d %d", info->token, info->seconds, info->hits);
			return PASSES_PER_SEC(info->seconds) + PASSES_PER_SEC(GRACE_MS / 1000);
		}

		// no answer within the game's time: the fish is gone with the bait
		ch->m_pkPreFishingEvent = NULL;
		Lose(ch, false);
		return 0;
	}
}

// "/fishren hello | end <token> <hits>" (cmd.cpp, server-patches/fishren)
void Mt2009FishRenCommand(LPCHARACTER ch, const char* argument)
{
	using namespace fishren;
	if (!ch || !ch->IsPC() || !ch->GetDesc())
		return;

	char sub[32] = { 0 };
	const char* p = one_argument(argument, sub, sizeof(sub));
	if (!strcmp(sub, "hello"))
	{
		s_mapHello[ch->GetPlayerID()] = ch->GetDesc()->GetHandle();
		return;
	}
	if (strcmp(sub, "end"))
		return;

	char tok[32] = { 0 }, hit[32] = { 0 };
	two_arguments(p, tok, sizeof(tok), hit, sizeof(hit));
	DWORD token = 0;
	int hits = 0;
	if (!*tok || !str_to_number(token, tok) || !str_to_number(hits, hit))
		return;

	TFishRenInfo* info = Info(ch);
	if (!info || info->step != STEP_GAME || info->token != token || !HasHello(ch))
		return;

	const DWORD elapsed = get_dword_time() - info->gameStart;
	const int need = info->hits;
	const DWORD limit = (DWORD)info->seconds * 1000 + GRACE_MS;
	event_cancel(&ch->m_pkPreFishingEvent);

	LPITEM rod = fishing::CheckRod(ch);
	if (!rod)
	{
		StopMotion(ch);
		SendStop(ch);
		return;
	}

	if (hits < need || elapsed > limit || (need > 1 && elapsed < (DWORD)MIN_GAME_MS))
	{
		if (hits >= need)
			sys_log(0, "FISHREN: %s pid=%u result refused (hits=%d elapsed=%u ms)", ch->GetName(), ch->GetPlayerID(), hits, elapsed);
		Lose(ch, true);
		return;
	}

	// the fish is hooked - the rod's chance with fishing.cpp's pity bonus (fishing::Take, the bar minigame's roll)
	const int chance = fishing::GetFishingChance(ch, rod);
	ch->m_iFishingChanceBonus = MIN(ch->m_iFishingChanceBonus, MAX(25 - chance / 2, 0));
	if (number(1, 100) <= chance + ch->m_iFishingChanceBonus)
	{
		// the catch: quest fishing_manage.success (the fish), the SUCCESS motion, the fishing puzzle event's box
		// (MT2009_PLUS_FISH_PUZZLE_V1 hooks fishing::ProcessFishingGameSuccess) - exactly the bar minigame's win
		fishing::ProcessFishingGameSuccess(ch);
		fishing::FishingPractice(ch, false);
		fishing::SaveEndFishingTime(ch);
		SendStop(ch);
		return;
	}

	ch->m_iFishingChanceBonus += 2;
	ch->ChatPacket(CHAT_TYPE_INFO, "Ryba si\xea zerwa\xb3a z haczyka.");
	Lose(ch, true);
}

// CHARACTER::fishing(), the cast (char.cpp): a client with the window gets the renewal's cast; NULL - the old one.
LPEVENT Mt2009FishRenCast(LPCHARACTER ch)
{
	using namespace fishren;
	if (!HasHello(ch))
		return NULL;

	TFishRenInfo* info = AllocEventInfo<TFishRenInfo>();
	info->pid = ch->GetPlayerID();
	info->step = STEP_WAIT_BITE;

	int lo = Flag("fishren_bite_min", DEFAULT_BITE_MIN, 1, 60);
	int hi = Flag("fishren_bite_max", DEFAULT_BITE_MAX, 1, 60);
	if (hi < lo)
		hi = lo;

	TPacketGCFishing p;
	p.header = HEADER_GC_FISHING;
	p.subheader = FISHING_SUBHEADER_GC_START;
	p.info = ch->GetVID();
	p.dir = (BYTE)(ch->GetRotation() / 5);
	ch->PacketAround(&p, sizeof(TPacketGCFishing));

	return event_create(fishren_event, info, PASSES_PER_SEC(number(lo, hi)));
}

// CHARACTER::fishing() while a cast runs (char.cpp): the fishing key / a move pulls the rod out. A renewal cast
// ends without a catch (before the bite, or during the game - as the renewal's fishing(0)); true - it was one.
bool Mt2009FishRenPull(LPCHARACTER ch)
{
	using namespace fishren;
	TFishRenInfo* info = Info(ch);
	if (!info)
		return false;

	event_cancel(&ch->m_pkPreFishingEvent);
	if (!fishing::CheckRod(ch))
	{
		StopMotion(ch);
		SendStop(ch);
		return true;
	}
	Lose(ch, false);
	return true;
}
