// MT2009_PLUS_REMOTE_CALL_V1: Enasir - Dozorca / Handlarz (the remote call of a storeroom keeper and a merchant; the owner,
// 5 November 2026: "Dodaj jeszcze to"). The idea of Khaled's / LungSam's "Official Remote Call" package, rebuilt for
// MT2009 PLUS 3.x (server-patches/remotecall/README.md has the whole picture), as pl-wiki "System Enasira" describes it:
//   * the items 72368 Dozorca Enasir, 72369 Handlarz Enasir and their tradeable "(h)" twins 72370 / 72371 (remote_call.sql):
//     used, each adds its time (value1 seconds, 7 days; socket0 when an item carries its own) to the character's
//     storeroom / shop service - real time (it runs offline too), up to 1000 days. The end times are quest flags
//     (remote_call.safebox_end / remote_call.shop_end), not affects: no buff icon, kept through death and logout;
//   * the button by the inventory (client) asks for Enasir (CG 190 SUMMON): he stands by the character for 3 minutes,
//     only its owner sees him (CHARACTER::EncodeInsertPacket asks RemoteCallVisibleTo), and goes when the owner walks
//     5 000 away, changes map / channel or logs out, when the time is up or when he is sent away; 10 s before the next;
//     never in instances, dungeons, war / arena / Sung Zi maps, the OX map;
//   * a click on him is quest remote_call: "Otworz Magazyn" (the password dialog, then the storeroom - titled Enasir's in
//     the client: GC 190 SAFEBOX), "Otworz sklep" (the General Store's (9003) shop; Enasir takes 10 % of every sale -
//     RemoteCallSellFee in CShopManager::Sell), "Odeslij Enasira";
//   * CG 190 / GC 190 (packet.h) - free here, in the exe and on every branch; the client says hello (CG HELLO) at every
//     game phase and only a client that did gets GC 190: an older exe never sees it, bots never say it.
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "packet.h"
#include "questmanager.h"
#include "questlua.h"
#include "shop.h"
#include "shop_manager.h"
#include "threeway_war.h"
#include "arena.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>

namespace remote_call
{
	enum
	{
		MOB_VNUM = 20874,				// Enasir (mob_proto, client npclist peddler_call)
		SHOP_NPC_VNUM = 9003,			// Handlarka Roznosci - her shop is the one he opens (pl-wiki)
		ITEM_SAFEBOX = 72368,			// Dozorca Enasir
		ITEM_SHOP = 72369,				// Handlarz Enasir
		ITEM_SAFEBOX_TRADE = 72370,		// Dozorca Enasir (h)
		ITEM_SHOP_TRADE = 72371,		// Handlarz Enasir (h)
		ITEM_DEFAULT_SEC = 604800,		// 7 days (the GF item's value)
		MAX_BUFF_SEC = 86400000,		// 1000 days (pl-wiki)
		SUMMON_SEC = 180,				// 3 minutes (pl-wiki)
		COOLTIME_SEC = 10,				// 10 s between two summons (pl-wiki)
		SPAWN_OFFSET = 200,				// beside the character
		MAX_DISTANCE = 5000,			// further away he goes
		SELL_FEE_PCT = 10,				// his fee on a sale (pl-wiki)
		MAP_OX = 113,
	};

	enum EBuff { BUFF_SAFEBOX = 0, BUFF_SHOP = 1, BUFF_COUNT = 2 };

	enum ECG { CG_HELLO = 0, CG_SUMMON = 1, CG_UNSUMMON = 2 };
	enum EGC { GC_STATE = 0, GC_SUMMONED = 1, GC_GONE = 2, GC_MESSAGE = 3, GC_SAFEBOX = 4 };

	enum EMessage
	{
		MSG_NOT_HERE = 1,
		MSG_COOLTIME = 2,
		MSG_NO_BUFF = 3,
		MSG_DEAD = 4,
		MSG_ALREADY = 5,
		MSG_SPAWN_FAIL = 6,
		MSG_BUFF_MAX = 7,
		MSG_BUFF_ADDED = 8,
		MSG_NOT_NOW = 9,
	};

	const char* const FLAG[BUFF_COUNT] = { "remote_call.safebox_end", "remote_call.shop_end" };
	const char* const BUFF_NAME[BUFF_COUNT] = { "Magazyn", "Sklep" };

	struct SState
	{
		bool hello = false;
		DWORD npcVID = 0;
		DWORD summonEnd = 0;
		DWORD coolEnd = 0;
		bool remoteSafebox = false;
	};

	std::unordered_map<DWORD, SState> s_state;		// pid -> state (players of this core)
	std::unordered_map<DWORD, DWORD> s_npcOwner;	// Enasir's vid -> his owner's pid
	LPEVENT s_tick = NULL;

	bool IsPlayer(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	SState* StateOf(LPCHARACTER ch, bool create)
	{
		if (!IsPlayer(ch))
			return NULL;
		auto it = s_state.find(ch->GetPlayerID());
		if (it != s_state.end())
			return &it->second;
		if (!create)
			return NULL;
		return &s_state[ch->GetPlayerID()];
	}

	DWORD Now()
	{
		return (DWORD) get_global_time();
	}

	// the seconds left of a service (0 none)
	DWORD BuffLeft(LPCHARACTER ch, int kind)
	{
		if (!ch || kind < 0 || kind >= BUFF_COUNT)
			return 0;
		const int end = ch->GetQuestFlag(FLAG[kind]);
		const DWORD now = Now();
		return end > 0 && (DWORD) end > now ? (DWORD) end - now : 0;
	}

	std::string Duration(DWORD sec)
	{
		char buf[64];
		const DWORD days = sec / 86400, hours = sec % 86400 / 3600, minutes = sec % 3600 / 60;
		if (days)
			snprintf(buf, sizeof(buf), "%u dni %u godz.", days, hours);
		else if (hours)
			snprintf(buf, sizeof(buf), "%u godz. %u min", hours, minutes);
		else
			snprintf(buf, sizeof(buf), "%u min", minutes ? minutes : 1);
		return buf;
	}

	void Send(LPCHARACTER ch, BYTE sub, DWORD v0 = 0, DWORD v1 = 0, DWORD v2 = 0)
	{
		SState* st = StateOf(ch, false);
		if (!st || !st->hello || !ch->GetDesc())
			return;
		TPacketGCRemoteCall p;
		p.bHeader = HEADER_GC_REMOTE_CALL;
		p.bSubHeader = sub;
		p.dwValue0 = v0;
		p.dwValue1 = v1;
		p.dwValue2 = v2;
		ch->GetDesc()->Packet(&p, sizeof(p));
	}

	bool AllowedHere(LPCHARACTER ch)
	{
		const long map = ch->GetMapIndex();
		if (map >= 10000 || map == MAP_OX)
			return false;
		if (ch->GetDungeon() || ch->GetWarMap())
			return false;
		if (CThreeWayWar::instance().IsSungZiMapIndex(map))
			return false;
		if (CArenaManager::instance().IsArenaMap(map))
			return false;
		return true;
	}

	void SendState(LPCHARACTER ch)
	{
		Send(ch, GC_STATE, BuffLeft(ch, BUFF_SAFEBOX), BuffLeft(ch, BUFF_SHOP), AllowedHere(ch) ? 1 : 0);
	}

	void Message(LPCHARACTER ch, BYTE code, const char* text)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", text);
		Send(ch, GC_MESSAGE, code);
	}

	EVENTINFO(remote_call_tick_info)
	{
	};

	void Unsummon(DWORD pid, SState& st, bool notify);

	EVENTFUNC(remote_call_tick_event)
	{
		const DWORD now = Now();
		// the summoned ones whose time is up, whose owner is away or gone
		std::vector<DWORD> gone;
		for (auto& it : s_state)
		{
			SState& st = it.second;
			if (!st.npcVID)
				continue;
			LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(it.first);
			LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(st.npcVID);
			if (!owner || !npc || now >= st.summonEnd || npc->GetMapIndex() != owner->GetMapIndex() ||
				DISTANCE_APPROX(owner->GetX() - npc->GetX(), owner->GetY() - npc->GetY()) > MAX_DISTANCE)
				gone.push_back(it.first);
		}
		for (DWORD pid : gone)
		{
			auto it = s_state.find(pid);
			if (it != s_state.end())
				Unsummon(pid, it->second, true);
		}
		if (s_npcOwner.empty())
		{
			s_tick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(1);
	}

	void Unsummon(DWORD pid, SState& st, bool notify)
	{
		if (!st.npcVID)
			return;
		const DWORD vid = st.npcVID;
		s_npcOwner.erase(vid);
		st.npcVID = 0;
		st.summonEnd = 0;
		st.coolEnd = Now() + COOLTIME_SEC;
		LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(pid);
		LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(vid);
		if (owner)
		{
			if (npc && owner->GetShopOwner() == npc)
				CShopManager::instance().StopShopping(owner);
			if (st.remoteSafebox && owner->GetSafebox())
				owner->CloseSafebox();
		}
		st.remoteSafebox = false;
		if (npc)
			M2_DESTROY_CHARACTER(npc);
		if (notify && owner)
		{
			owner->ChatPacket(CHAT_TYPE_INFO, "Enasir odszed\xb3.");
			Send(owner, GC_GONE, COOLTIME_SEC);
		}
	}

	bool Summon(LPCHARACTER ch)
	{
		SState* st = StateOf(ch, true);
		if (!st)
			return false;
		if (st->npcVID)
		{
			Message(ch, MSG_ALREADY, "Enasir ju\xbf jest przy tobie.");
			return false;
		}
		if (ch->IsDead())
		{
			Message(ch, MSG_DEAD, "Nie mo\xbf""esz przywo\xb3""a\xe6 Enasira, gdy jeste\x9c martwy.");
			return false;
		}
		const DWORD now = Now();
		if (now < st->coolEnd)
		{
			char buf[128];
			snprintf(buf, sizeof(buf), "Enasira mo\xbf""esz przywo\xb3""a\xe6 ponownie za %u s.", st->coolEnd - now);
			Message(ch, MSG_COOLTIME, buf);
			return false;
		}
		if (!BuffLeft(ch, BUFF_SAFEBOX) && !BuffLeft(ch, BUFF_SHOP))
		{
			Message(ch, MSG_NO_BUFF, "Aby przywo\xb3""a\xe6 Enasira, u\xbfyj najpierw przedmiotu Dozorca Enasir albo Handlarz Enasir.");
			return false;
		}
		if (!AllowedHere(ch))
		{
			Message(ch, MSG_NOT_HERE, "Enasira nie mo\xbfna przywo\xb3""a\xe6 w tym miejscu.");
			return false;
		}
		if (ch->IsBusy(BUSY_SHOP) || ch->GetExchange())
		{
			Message(ch, MSG_NOT_NOW, "Zamknij najpierw inne okno.");
			return false;
		}

		long x = ch->GetX() + SPAWN_OFFSET;
		long y = ch->GetY();
		LPCHARACTER npc = CHARACTER_MANAGER::instance().SpawnMob(MOB_VNUM, ch->GetMapIndex(), x, y, 0, false, -1, false);
		if (!npc)
		{
			Message(ch, MSG_SPAWN_FAIL, "Przywo\xb3""anie nie powiod\xb3o si\xea. Spr\xf3""buj ponownie za chwil\xea.");
			return false;
		}
		// his owner is known before he is shown: EncodeInsertPacket hides him from everyone else
		s_npcOwner[npc->GetVID()] = ch->GetPlayerID();
		if (!npc->Show(ch->GetMapIndex(), x, y, 0, false))
		{
			x = ch->GetX();
			if (!npc->Show(ch->GetMapIndex(), x, y, 0, false))
			{
				s_npcOwner.erase(npc->GetVID());
				M2_DESTROY_CHARACTER(npc);
				Message(ch, MSG_SPAWN_FAIL, "Przywo\xb3""anie nie powiod\xb3o si\xea. Spr\xf3""buj ponownie za chwil\xea.");
				return false;
			}
		}
		npc->SetRotationToXY(ch->GetX(), ch->GetY());
		st->npcVID = npc->GetVID();
		st->summonEnd = now + SUMMON_SEC;
		st->remoteSafebox = false;
		if (!s_tick)
			s_tick = event_create(remote_call_tick_event, AllocEventInfo<remote_call_tick_info>(), PASSES_PER_SEC(1));
		ch->ChatPacket(CHAT_TYPE_INFO, "Enasir b\xea""dzie przy tobie przez 3 minuty. Zniknie, je\x9cli si\xea oddalisz albo zmienisz map\xea.");
		Send(ch, GC_SUMMONED, SUMMON_SEC, st->npcVID);
		return true;
	}

	// the clicked Enasir is this character's (quest remote_call)
	LPCHARACTER OwnNpc(LPCHARACTER ch, LPCHARACTER npc)
	{
		if (!ch || !npc || npc->IsPC() || npc->GetRaceNum() != MOB_VNUM)
			return NULL;
		auto it = s_npcOwner.find(npc->GetVID());
		if (it == s_npcOwner.end() || it->second != ch->GetPlayerID())
			return NULL;
		return npc;
	}

	int ItemBuff(DWORD vnum)
	{
		switch (vnum)
		{
			case ITEM_SAFEBOX:
			case ITEM_SAFEBOX_TRADE:
				return BUFF_SAFEBOX;
			case ITEM_SHOP:
			case ITEM_SHOP_TRADE:
				return BUFF_SHOP;
		}
		return -1;
	}

	// adds sec to a service; false when it would pass 1000 days
	bool AddBuff(LPCHARACTER ch, int kind, DWORD sec)
	{
		const DWORD left = BuffLeft(ch, kind);
		if ((unsigned long long) left + sec > MAX_BUFF_SEC)
			return false;
		ch->SetQuestFlag(FLAG[kind], (int) (Now() + left + sec));
		return true;
	}
}

// char.cpp (MT2009_PLUS_REMOTE_CALL_V1 (insert)): Enasir is shown to his owner only
bool RemoteCallVisibleTo(LPCHARACTER npc, LPCHARACTER viewer)
{
	using namespace remote_call;
	auto it = s_npcOwner.find(npc->GetVID());
	if (it == s_npcOwner.end())
		return true;
	return viewer && viewer->IsPC() && viewer->GetPlayerID() == it->second;
}

// char.cpp (MT2009_PLUS_REMOTE_CALL_V1 (destroy)): a player going (logout, warp) takes his Enasir along; an Enasir going
// (purged, a map closed) is forgotten by his owner
void RemoteCallOnDestroy(LPCHARACTER ch)
{
	using namespace remote_call;
	if (!ch)
		return;
	if (ch->IsPC())
	{
		auto it = s_state.find(ch->GetPlayerID());
		if (it == s_state.end())
			return;
		if (it->second.npcVID)
		{
			const DWORD vid = it->second.npcVID;
			s_npcOwner.erase(vid);
			it->second.npcVID = 0;
			LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(vid);
			if (npc)
				M2_DESTROY_CHARACTER(npc);
		}
		s_state.erase(it);
		return;
	}
	if (ch->GetRaceNum() != MOB_VNUM)
		return;
	auto o = s_npcOwner.find(ch->GetVID());
	if (o == s_npcOwner.end())
		return;
	const DWORD pid = o->second;
	s_npcOwner.erase(o);
	auto it = s_state.find(pid);
	if (it == s_state.end() || it->second.npcVID != (DWORD) ch->GetVID())
		return;
	SState& st = it->second;
	st.npcVID = 0;
	st.summonEnd = 0;
	st.coolEnd = Now() + COOLTIME_SEC;
	LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(pid);
	if (owner)
	{
		if (owner->GetShopOwner() == ch)
			CShopManager::instance().StopShopping(owner);
		if (st.remoteSafebox && owner->GetSafebox())
			owner->CloseSafebox();
		st.remoteSafebox = false;
		owner->ChatPacket(CHAT_TYPE_INFO, "Enasir odszed\xb3.");
		Send(owner, GC_GONE, COOLTIME_SEC);
	}
}

// char.cpp (MT2009_PLUS_REMOTE_CALL_V1 (safebox close)): the storeroom open now is not Enasir's any more
void RemoteCallOnSafeboxClose(LPCHARACTER ch)
{
	remote_call::SState* st = remote_call::StateOf(ch, false);
	if (st)
		st->remoteSafebox = false;
}

// input_main.cpp (MT2009_PLUS_REMOTE_CALL_V1 (packet)): CG 190 - hello, summon, send away
void RemoteCallPacket(LPCHARACTER ch, const char* data)
{
	using namespace remote_call;
	SState* st = StateOf(ch, true);
	if (!st)
		return;
	const TPacketCGRemoteCall* p = (const TPacketCGRemoteCall*) data;
	switch (p->bSubHeader)
	{
		case CG_HELLO:
			st->hello = true;
			SendState(ch);
			if (st->npcVID)
				Send(ch, GC_SUMMONED, st->summonEnd > Now() ? st->summonEnd - Now() : 0, st->npcVID);
			break;
		case CG_SUMMON:
			if (st->hello)
				Summon(ch);
			break;
		case CG_UNSUMMON:
			if (st->npcVID)
				Unsummon(ch->GetPlayerID(), *st, true);
			break;
		default:
			break;
	}
}

// char_item.cpp (MT2009_PLUS_REMOTE_CALL_V1 (use)): Dozorca / Handlarz Enasir (and "(h)") - -1 not one, 0 refused, 1 used
int RemoteCallUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace remote_call;
	if (!ch || !item)
		return -1;
	const int kind = ItemBuff(item->GetVnum());
	if (kind < 0)
		return -1;
	if (!IsPlayer(ch))
		return 0;
	if (item->IsExchanging() || item->isLocked())
		return 0;
	long sec = item->GetSocket(0) > 0 ? item->GetSocket(0) : item->GetValue(1);
	if (sec <= 0)
		sec = ITEM_DEFAULT_SEC;
	const bool extended = BuffLeft(ch, kind) > 0;
	if (!AddBuff(ch, kind, (DWORD) sec))
	{
		Message(ch, MSG_BUFF_MAX, "Tej us\xb3ugi Enasira nie mo\xbfna ju\xbf przed\xb3u\xbfy\xe6 - najwy\xbf""ej do 1000 dni.");
		return 0;
	}
	item->SetCount(item->GetCount() - 1);
	char buf[256];
	snprintf(buf, sizeof(buf), extended ? "Przed\xb3u\xbfono us\xb3ug\xea Enasira: %s. Pozosta\xb3y czas: %s." :
		"Mo\xbf""esz przywo\xb3""a\xe6 Enasira (%s) przyciskiem przy ekwipunku. Pozosta\xb3y czas: %s.",
		BUFF_NAME[kind], Duration(BuffLeft(ch, kind)).c_str());
	ch->ChatPacket(CHAT_TYPE_INFO, "%s", buf);
	SState* st = StateOf(ch, true);
	if (st && st->hello)
	{
		Send(ch, GC_MESSAGE, MSG_BUFF_ADDED, kind);
		SendState(ch);
	}
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "Przycisk przywo\xb3""ania Enasira wymaga nowej wersji klienta - zaktualizuj gr\xea.");
	return 1;
}

// shop_manager.cpp (MT2009_PLUS_REMOTE_CALL_V1 (sell fee)): a sale to Enasir's shop leaves him 10 % (pl-wiki)
YANG RemoteCallSellFee(LPCHARACTER ch, YANG price)
{
	using namespace remote_call;
	if (!ch || price <= 0 || !OwnNpc(ch, ch->GetShopOwner()))
		return 0;
	const YANG fee = price * SELL_FEE_PCT / 100;
	if (fee > 0)
		ch->ChatPacket(CHAT_TYPE_INFO, "Enasir pobra\xb3 op\xb3""at\xea za us\xb3ug\xea: %lld Yang (10%%).", (long long) fee);
	return fee;
}

// cmd.cpp (MT2009_PLUS_REMOTE_CALL_V1 (command)), GM:
//   /enasir                          the services' times and Enasir
//   /enasir daj <magazyn|sklep> <dni> a service for yourself (days added, at most 1000 in all)
//   /enasir zabierz                  both services taken away (and Enasir sent away)
void RemoteCallCommand(LPCHARACTER ch, const char* argument)
{
	using namespace remote_call;
	if (!ch)
		return;
	char a1[64], a2[64], a3[64];
	const char* rest = two_arguments(argument, a1, sizeof(a1), a2, sizeof(a2));
	one_argument(rest, a3, sizeof(a3));
	if (!*a1)
	{
		const SState* st = StateOf(ch, false);
		ch->ChatPacket(CHAT_TYPE_INFO, "Enasir: Magazyn %s, Sklep %s, przywo\xb3""any: %s, tu wolno: %s.",
			BuffLeft(ch, BUFF_SAFEBOX) ? Duration(BuffLeft(ch, BUFF_SAFEBOX)).c_str() : "brak",
			BuffLeft(ch, BUFF_SHOP) ? Duration(BuffLeft(ch, BUFF_SHOP)).c_str() : "brak",
			st && st->npcVID ? "tak" : "nie", AllowedHere(ch) ? "tak" : "nie");
		return;
	}
	if (!strcmp(a1, "daj"))
	{
		const int kind = !strcmp(a2, "magazyn") ? BUFF_SAFEBOX : !strcmp(a2, "sklep") ? BUFF_SHOP : -1;
		int days = 0;
		if (kind < 0 || !str_to_number(days, a3) || days <= 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "/enasir daj <magazyn|sklep> <dni>");
			return;
		}
		if (!AddBuff(ch, kind, (DWORD) days * 86400))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najwy\xbf""ej 1000 dni.");
			return;
		}
		ch->ChatPacket(CHAT_TYPE_INFO, "Enasir: %s - pozosta\xb3y czas %s.", BUFF_NAME[kind], Duration(BuffLeft(ch, kind)).c_str());
		SendState(ch);
		return;
	}
	if (!strcmp(a1, "zabierz"))
	{
		ch->SetQuestFlag(FLAG[BUFF_SAFEBOX], 0);
		ch->SetQuestFlag(FLAG[BUFF_SHOP], 0);
		SState* st = StateOf(ch, false);
		if (st && st->npcVID)
			Unsummon(ch->GetPlayerID(), *st, true);
		SendState(ch);
		ch->ChatPacket(CHAT_TYPE_INFO, "Enasir: us\xb3ugi zabrane.");
		return;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, "/enasir | /enasir daj <magazyn|sklep> <dni> | /enasir zabierz");
}

namespace quest
{
	// remote_call.* - quest remote_call (Enasir's click); for the quest's character and the clicked NPC.
	static LPCHARACTER remote_call_npc()
	{
		CQuestManager& q = CQuestManager::instance();
		return remote_call::OwnNpc(q.GetCurrentCharacterPtr(), q.GetCurrentNPCCharacterPtr());
	}

	// remote_call.is_owner() -> the clicked Enasir is the character's
	static int remote_call_is_owner(lua_State* L)
	{
		lua_pushboolean(L, remote_call_npc() != NULL);
		return 1;
	}

	// remote_call.has_safebox() / has_shop() -> the service is on
	static int remote_call_has_safebox(lua_State* L)
	{
		lua_pushboolean(L, remote_call::BuffLeft(CQuestManager::instance().GetCurrentCharacterPtr(), remote_call::BUFF_SAFEBOX) > 0);
		return 1;
	}

	static int remote_call_has_shop(lua_State* L)
	{
		lua_pushboolean(L, remote_call::BuffLeft(CQuestManager::instance().GetCurrentCharacterPtr(), remote_call::BUFF_SHOP) > 0);
		return 1;
	}

	// remote_call.open_safebox() -> the storeroom's password dialog (Enasir's); false when he cannot
	static int remote_call_open_safebox(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		LPCHARACTER npc = remote_call_npc();
		remote_call::SState* st = remote_call::StateOf(ch, false);
		if (!npc || !st || !remote_call::BuffLeft(ch, remote_call::BUFF_SAFEBOX) || ch->GetSafebox())
		{
			lua_pushboolean(L, 0);
			return 1;
		}
		if (g_bChannel > 90)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Na tym kanale magazyn jest niedost\xeapny.");
			lua_pushboolean(L, 0);
			return 1;
		}
		ch->SetSafeboxOpenPosition();
		st->remoteSafebox = true;
		remote_call::Send(ch, remote_call::GC_SAFEBOX, 1);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ShowMeSafeboxPassword");
		lua_pushboolean(L, 1);
		return 1;
	}

	// remote_call.open_shop() -> the General Store's shop at Enasir; false when he cannot
	static int remote_call_open_shop(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		LPCHARACTER npc = remote_call_npc();
		if (!npc || !remote_call::BuffLeft(ch, remote_call::BUFF_SHOP))
		{
			lua_pushboolean(L, 0);
			return 1;
		}
		LPSHOP shop = CShopManager::instance().GetByNPCVnum(remote_call::SHOP_NPC_VNUM);
		lua_pushboolean(L, shop && CShopManager::instance().StartShopping(ch, npc, shop->GetVnum()));
		return 1;
	}

	// remote_call.unsummon() -> Enasir sent away
	static int remote_call_unsummon(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		remote_call::SState* st = remote_call::StateOf(ch, false);
		if (st && st->npcVID)
			remote_call::Unsummon(ch->GetPlayerID(), *st, true);
		return 0;
	}

	// remote_call.time_left() -> the seconds he stays
	static int remote_call_time_left(lua_State* L)
	{
		remote_call::SState* st = remote_call::StateOf(CQuestManager::instance().GetCurrentCharacterPtr(), false);
		const DWORD now = remote_call::Now();
		lua_pushnumber(L, st && st->npcVID && st->summonEnd > now ? st->summonEnd - now : 0);
		return 1;
	}

	// questlua.cpp (MT2009_PLUS_REMOTE_CALL_V1 (lua)) - defined in namespace quest: the call there is a block-scope
	// declaration inside namespace quest, so it names quest::RegisterRemoteCallFunctionTable
	void RegisterRemoteCallFunctionTable()
	{
		luaL_reg remote_call_functions[] =
		{
			{ "is_owner",		remote_call_is_owner		},
			{ "has_safebox",	remote_call_has_safebox		},
			{ "has_shop",		remote_call_has_shop		},
			{ "open_safebox",	remote_call_open_safebox	},
			{ "open_shop",		remote_call_open_shop		},
			{ "unsummon",		remote_call_unsummon		},
			{ "time_left",		remote_call_time_left		},
			{ NULL,				NULL						}
		};
		CQuestManager::instance().AddLuaFunctionTable("remote_call", remote_call_functions);
	}
}
