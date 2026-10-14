// MT2009_PLUS_CHANGE_LOOK_V1: Transmutacja (Owsap v6.2.6 __CHANGE_LOOK_SYSTEM__, Autor: blackdragonx61 / Mali; the
// rules of the pl-wiki "Transmutacja"). server-patches/transmutacja/README.md. New file outside the engine's own; the
// hooks are server-patches/transmutacja (edits.json), which also defines ENABLE_CHANGELOOK_SYSTEM.
//
// The look is the vnum of another item, kept in the item (CItem::m_dwTransmutation, player.item.transmutation,
// TPlayerItem::dwTransmutation) and shown everywhere the item is drawn on a character (the parts, below) and in the
// owner's item packets (the tooltip). Owsap's window works on its own packets; ours speaks chat commands, so the exe
// only learns the look of an item:
//   client -> "/transmutacja in <slot> <cell>" (slot 0 the item that gets the look, 1 the item whose look is taken,
//             2 the ticket), "/transmutacja out <slot>", "/transmutacja accept", "/transmutacja cancel"
//   server -> "ChangeLookOpen <type>", "ChangeLookSet <slot> <cell> <vnum>", "ChangeLookDel <slot>",
//             "ChangeLookClose", "ChangeLookDone"
// The window is opened by Teowaden (quest transmutacja, game.open_changelook(0|1)). Everything is checked again at
// "accept" by the item ids the window holds: an item that moved, went into a trade or a shop, or was taken off is
// refused there, not trusted from the check-in.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "questlua.h"
#include "log.h"
#include "utils.h"
#include "cmd.h"
#include "packet.h"

#include <cstdio>
#include <cstring>
#include <map>

#ifdef ENABLE_CHANGELOOK_SYSTEM

namespace changelook
{
	enum { TYPE_ITEM = 0, TYPE_MOUNT = 1 };
	enum { SLOT_LEFT = 0, SLOT_RIGHT = 1, SLOT_PASS = 2, SLOT_MAX = 3 };

	// the official vnums (GF 26.1.11 item_list.txt, Owsap unique_item.h)
	const DWORD ITEM_REVERSAL = 72325;			// Anulacja Transmutacji
	const DWORD ITEM_TICKET_1 = 72326;			// Bilet Transmutacji
	const DWORD ITEM_TICKET_2 = 72341;			// Bilet Transmutacji (tradeable)
	const DWORD ITEM_MOUNT_REVERSAL = 72343;	// Anulacja Polimorfii Wierzchowca
	const DWORD ITEM_MOUNT_TICKET = 72344;		// Bilet Polimorfii Wierzchowca

	const int PRICE_ITEM = 50000000;			// 50 mln Yang (pl-wiki)
	const int PRICE_MOUNT = 30000000;			// 30 mln Yang (pl-wiki)
	const int MAX_DISTANCE = 1500;				// from where the window was opened (the client closes it at 1000)

	struct TSession
	{
		BYTE type;
		DWORD item[SLOT_MAX];	// item ids
		long map;
		long x, y;
	};

	std::map<DWORD, TSession> s_sessions;	// by player id

	TSession* Find(LPCHARACTER ch)
	{
		std::map<DWORD, TSession>::iterator it = s_sessions.find(ch->GetPlayerID());
		return it == s_sessions.end() ? NULL : &it->second;
	}

	bool IsWeaponLook(LPITEM item)
	{
		if (item->GetType() != ITEM_WEAPON)
			return false;
		switch (item->GetSubType())
		{
			case WEAPON_ARROW:
			case WEAPON_MOUNT_SPEAR:
#ifdef ENABLE_QUIVER_SYSTEM
			case WEAPON_QUIVER:
#endif
				return false;
		}
		return true;
	}

	bool IsArmourBody(LPITEM item) { return item->GetType() == ITEM_ARMOR && item->GetSubType() == ARMOR_BODY; }
	bool IsCostumeBody(LPITEM item) { return item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_BODY; }
	bool IsCostumeWeapon(LPITEM item)
	{
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
		return item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_WEAPON;
#else
		return false;
#endif
	}
	bool IsMount(LPITEM item)
	{
#ifdef ENABLE_MOUNT_COSTUME_SYSTEM
		return item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_MOUNT && item->GetValue(1) != 0;
#else
		return false;
#endif
	}

	// Owsap's CanAddItem: what can take a look (and give one) in this window.
	bool CanTakeLook(BYTE type, LPITEM item)
	{
		if (type == TYPE_MOUNT)
			return IsMount(item);
		return IsWeaponLook(item) || IsArmourBody(item) || IsCostumeBody(item) || IsCostumeWeapon(item);
	}

	// Owsap's CheckItem: the look of `right` fits `left` (pl-wiki: a one-handed weapon only from a one-handed one,
	// armour and costumes between themselves, a weapon skin with the weapons of its kind, a mount from a mount).
	bool LookFits(BYTE type, LPITEM left, LPITEM right)
	{
		if (left == right || left->GetVnum() == right->GetVnum())
			return false;
		if (!CanTakeLook(type, right))
			return false;
		if (type == TYPE_MOUNT)
			return true;

		if (left->GetType() != right->GetType())
		{
			if ((IsCostumeBody(right) && IsArmourBody(left)) || (IsArmourBody(right) && IsCostumeBody(left)))
				return true;
			if (IsCostumeWeapon(right) && IsWeaponLook(left) && right->GetValue(3) == left->GetSubType())
				return true;
			if (IsWeaponLook(right) && IsCostumeWeapon(left) && right->GetSubType() == left->GetValue(3))
				return true;
			return false;
		}

		if (left->GetSubType() != right->GetSubType())
			return false;
		if (left->GetType() == ITEM_ARMOR || left->GetType() == ITEM_WEAPON)
			if (left->GetAntiFlag() != right->GetAntiFlag())
				return false;
		if (IsCostumeBody(left))
		{
			if ((IS_SET(right->GetAntiFlag(), ITEM_ANTIFLAG_FEMALE) && IS_SET(left->GetAntiFlag(), ITEM_ANTIFLAG_MALE)) ||
					(IS_SET(right->GetAntiFlag(), ITEM_ANTIFLAG_MALE) && IS_SET(left->GetAntiFlag(), ITEM_ANTIFLAG_FEMALE)))
				return false;
		}
		if (IsCostumeWeapon(left) && left->GetValue(3) != right->GetValue(3))
			return false;
		return true;
	}

	bool IsPass(BYTE type, DWORD vnum)
	{
		if (type == TYPE_MOUNT)
			return vnum == ITEM_MOUNT_TICKET;
		return vnum == ITEM_TICKET_1 || vnum == ITEM_TICKET_2;
	}

	// An item of the character's bag (not worn, not traded, not locked); NULL otherwise.
	LPITEM BagItem(LPCHARACTER ch, DWORD id)
	{
		if (!id)
			return NULL;
		LPITEM item = ITEM_MANAGER::instance().Find(id);
		if (!item || item->GetOwner() != ch || item->GetWindow() != INVENTORY || item->IsEquipped())
			return NULL;
		if (item->IsExchanging() || item->isLocked())
			return NULL;
		return item;
	}

	void Del(LPCHARACTER ch, TSession& s, int slot)
	{
		if (!s.item[slot])
			return;
		s.item[slot] = 0;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookDel %d", slot);
	}

	bool Busy(LPCHARACTER ch)
	{
		return ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen()
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
			|| ch->IsAcceOpened()
#endif
			;
	}

	int Price(const TSession& s)
	{
		if (s.item[SLOT_PASS])
			return 0;
		return s.type == TYPE_MOUNT ? PRICE_MOUNT : PRICE_ITEM;
	}

	void Open(LPCHARACTER ch, BYTE type)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc())
			return;
		if (type != TYPE_ITEM && type != TYPE_MOUNT)
			type = TYPE_ITEM;
		if (Busy(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw zamknij inne okna (handel, sklep, magazyn).");
			return;
		}
		TSession s;
		memset(&s, 0, sizeof(s));
		s.type = type;
		s.map = ch->GetMapIndex();
		s.x = ch->GetX();
		s.y = ch->GetY();
		s_sessions[ch->GetPlayerID()] = s;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookOpen %d", type);
	}

	void Close(LPCHARACTER ch, bool bTellClient)
	{
		if (s_sessions.erase(ch->GetPlayerID()) && bTellClient)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookClose");
	}

	void CheckIn(LPCHARACTER ch, TSession& s, int slot, int cell)
	{
		if (slot < 0 || slot >= SLOT_MAX || s.item[slot])
			return;
		if (cell < 0 || cell >= INVENTORY_MAX_NUM)
			return;
		LPITEM item = ch->GetInventoryItem(cell);
		if (!item || !BagItem(ch, item->GetID()))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Tego przedmiotu nie mo\xbfna teraz u\xbfy\xe6 (za\xb3o\xbfony, w handlu albo zablokowany).");
			return;
		}
		for (int i = 0; i < SLOT_MAX; ++i)
			if (s.item[i] == item->GetID())
				return;

		if (slot == SLOT_PASS)
		{
			if (!IsPass(s.type, item->GetVnum()))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "To nie jest bilet do tej przemiany.");
				return;
			}
		}
		else if (slot == SLOT_LEFT)
		{
			if (!CanTakeLook(s.type, item))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, s.type == TYPE_MOUNT ? "Polimorfia dzia\xb3" "a tylko na wierzchowcach."
						: "Transmutacji podlegaj\xb9 tylko bronie, zbroje, kostiumy i wizerunki broni.");
				return;
			}
		}
		else
		{
			LPITEM left = BagItem(ch, s.item[SLOT_LEFT]);
			if (!left)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw w\xb3\xf3\xbf przedmiot, kt\xf3ry ma dosta\xe6 nowy wygl\xb9" "d.");
				return;
			}
			if (!LookFits(s.type, left, item))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Ten wygl\xb9" "d nie pasuje do tego przedmiotu.");
				return;
			}
		}
		s.item[slot] = item->GetID();
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookSet %d %d %u", slot, cell, item->GetVnum());
	}

	void CheckOut(LPCHARACTER ch, TSession& s, int slot)
	{
		if (slot < 0 || slot >= SLOT_MAX)
			return;
		Del(ch, s, slot);
		if (slot == SLOT_LEFT)	// the look's item was chosen for this one
			Del(ch, s, SLOT_RIGHT);
	}

	void Accept(LPCHARACTER ch, TSession& s)
	{
		if (ch->IsDead() || Busy(ch))
			return;
		if (ch->GetMapIndex() != s.map || DISTANCE_APPROX(ch->GetX() - s.x, ch->GetY() - s.y) > MAX_DISTANCE)
		{
			Close(ch, true);
			return;
		}
		LPITEM left = BagItem(ch, s.item[SLOT_LEFT]);
		LPITEM right = BagItem(ch, s.item[SLOT_RIGHT]);
		if (!left || !right)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "W\xb3\xf3\xbf oba przedmioty.");
			if (!left) Del(ch, s, SLOT_LEFT);
			if (!right) Del(ch, s, SLOT_RIGHT);
			return;
		}
		if (!CanTakeLook(s.type, left) || !LookFits(s.type, left, right))
		{
			Del(ch, s, SLOT_RIGHT);
			return;
		}
		LPITEM pass = NULL;
		if (s.item[SLOT_PASS])
		{
			pass = BagItem(ch, s.item[SLOT_PASS]);
			if (!pass || !IsPass(s.type, pass->GetVnum()))
			{
				Del(ch, s, SLOT_PASS);
				return;
			}
		}

		const int price = Price(s);
		if (price > 0 && ch->GetGold() < price)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz za ma\xb3o Yang (potrzeba %d).", price);
			return;
		}
		if (price > 0)
			ch->PointChange(POINT_GOLD, -price);

		char hint[96];
		snprintf(hint, sizeof(hint), "look %u (%s) was %u price %d pass %u", right->GetVnum(), right->GetName(),
				left->GetTransmutation(), price, pass ? pass->GetVnum() : 0);
		left->SetTransmutation(right->GetVnum());
		left->UpdatePacket();
		left->Save();
		LogManager::instance().ItemLog(ch, left, "TRANSMUTATION", hint);

		for (int i = 0; i < SLOT_MAX; ++i)
			Del(ch, s, i);

		// the item whose look was taken is gone (pl-wiki: "zostanie zniszczony")
		ITEM_MANAGER::instance().RemoveItem(right, "TRANSMUTATION_SOURCE");
		if (pass)
		{
			LogManager::instance().ItemLog(ch, pass, "TRANSMUTATION_TICKET", pass->GetName());
			pass->SetCount(pass->GetCount() - 1);
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookDone");
		ch->ChatPacket(CHAT_TYPE_INFO, s.type == TYPE_MOUNT ? "Polimorfia wierzchowca zako\xf1" "czona." : "Transmutacja zako\xf1" "czona.");
	}
}

// ---- hooks (server-patches/transmutacja) --------------------------------------------------------------------------

// quest: game.open_changelook(0 items | 1 mounts) at Teowaden (transmutacja.quest)
namespace
{
	int game_open_changelook(lua_State* L)
	{
		LPCHARACTER ch = quest::CQuestManager::instance().GetCurrentCharacterPtr();
		const int type = lua_isnumber(L, 1) ? (int) lua_tonumber(L, 1) : 0;
		if (ch)
			changelook::Open(ch, (BYTE) type);
		return 0;
	}

	// item.get_changelook_vnum() - Owsap's name; the look of the quest's current item (0: none)
	int item_get_changelook_vnum(lua_State* L)
	{
		LPITEM item = quest::CQuestManager::instance().GetCurrentItem();
		lua_pushnumber(L, item ? item->GetTransmutation() : 0);
		return 1;
	}

	void ChangeLookAddToTable(lua_State* L, const char* c_pszTable, const luaL_reg* pReg)
	{
		lua_getglobal(L, c_pszTable);
		if (!lua_istable(L, -1))
		{
			lua_pop(L, 1);
			lua_newtable(L);
			lua_pushvalue(L, -1);
			lua_setglobal(L, c_pszTable);
		}
		for (; pReg->name; ++pReg)
		{
			lua_pushstring(L, pReg->name);
			lua_pushcfunction(L, pReg->func);
			lua_rawset(L, -3);
		}
		lua_pop(L, 1);
	}
}

namespace quest
{
	// questlua.cpp: { void RegisterChangeLookFunctions(); RegisterChangeLookFunctions(); } inside namespace quest
	void RegisterChangeLookFunctions()
	{
		static const luaL_reg game_add[] =
		{
			{ "open_changelook",	game_open_changelook },
			{ NULL, NULL }
		};
		static const luaL_reg item_add[] =
		{
			{ "get_changelook_vnum",	item_get_changelook_vnum },
			{ NULL, NULL }
		};
		lua_State* L = CQuestManager::instance().GetLuaState();
		ChangeLookAddToTable(L, "game", game_add);
		ChangeLookAddToTable(L, "item", item_add);
	}
}

// cmd.cpp: "/transmutacja in <slot> <cell> | out <slot> | accept | cancel"
ACMD(do_changelook)
{
	char arg1[32], arg2[32], arg3[32];
	const char* rest = one_argument(argument, arg1, sizeof(arg1));
	two_arguments(rest, arg2, sizeof(arg2), arg3, sizeof(arg3));
	if (!ch || !ch->IsPC())
		return;

	changelook::TSession* s = changelook::Find(ch);
	if (!s)
	{
		if (strcmp(arg1, "cancel"))
			ch->ChatPacket(CHAT_TYPE_COMMAND, "ChangeLookClose");
		return;
	}
	if (!strcmp(arg1, "cancel"))
		changelook::Close(ch, false);
	else if (!strcmp(arg1, "in"))
	{
		int slot = -1, cell = -1;
		str_to_number(slot, arg2);
		str_to_number(cell, arg3);
		changelook::CheckIn(ch, *s, slot, cell);
	}
	else if (!strcmp(arg1, "out"))
	{
		int slot = -1;
		str_to_number(slot, arg2);
		changelook::CheckOut(ch, *s, slot);
	}
	else if (!strcmp(arg1, "accept"))
		changelook::Accept(ch, *s);
}

// The item worn or the look of a worn item changed: PART_MAIN / PART_WEAPON from the looks of what is worn (a
// costume over the armour / weapon, as the engine does). `leaving` is an item on its way off. Only when a look is
// involved, so nothing changes for anybody without a transmuted item; called at the end of CItem::ModifyPoints.
void Mt2009ChangeLookRefreshParts(LPCHARACTER ch, LPITEM self, LPITEM leaving)
{
	if (!ch || !ch->IsPC() || ch->IsPolymorphed())
		return;
	LPITEM body = ch->GetWear(WEAR_BODY);
	LPITEM costumeBody = ch->GetWear(WEAR_COSTUME_BODY);
	LPITEM weapon = ch->GetWear(WEAR_WEAPON);
	LPITEM costumeWeapon = NULL;
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
	costumeWeapon = ch->GetWear(WEAR_COSTUME_WEAPON);
#endif
	const bool bLook = (self && self->GetTransmutation()) || (body && body->GetTransmutation()) ||
		(costumeBody && costumeBody->GetTransmutation()) || (weapon && weapon->GetTransmutation()) ||
		(costumeWeapon && costumeWeapon->GetTransmutation());
	if (!bLook)
		return;
	if (body == leaving) body = NULL;
	if (costumeBody == leaving) costumeBody = NULL;
	if (weapon == leaving) weapon = NULL;
	if (costumeWeapon == leaving) costumeWeapon = NULL;

	const DWORD dwMain = costumeBody ? costumeBody->GetLookVnum() : (body ? body->GetLookVnum() : ch->GetOriginalPart(PART_MAIN));
	const DWORD dwWeapon = costumeWeapon ? costumeWeapon->GetLookVnum() : (weapon ? weapon->GetLookVnum() : 0);
	if (ch->GetPart(PART_MAIN) == dwMain && ch->GetPart(PART_WEAPON) == dwWeapon)
		return;
	ch->SetPart(PART_MAIN, dwMain);
	ch->SetPart(PART_WEAPON, dwWeapon);
	ch->UpdatePacket();
}

// A mount seal's mount: the look's (a mount "polymorphed" into another, pl-wiki) or its own. Every place that
// summons, rides or sends away a seal's mount asks this, so the actor and the rider agree (MountSystem.cpp,
// cmd_general.cpp do_ride, char_item.cpp EquipItem).
DWORD Mt2009MountMobVnum(LPITEM seal)
{
	if (!seal)
		return 0;
	const DWORD dwLook = seal->GetTransmutation();
	if (dwLook)
	{
		const TItemTable* t = ITEM_MANAGER::instance().GetTable(dwLook);
		if (t && t->bType == ITEM_COSTUME && t->alValues[1] != 0)
			return (DWORD) t->alValues[1];
	}
	return (DWORD) seal->GetValue(1);
}

// EquipItem: the look must fit the wearer too (Owsap: the class; the gender of a costume look).
bool Mt2009ChangeLookCanEquip(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || !item->GetTransmutation() || !ch->IsPC())
		return true;
	const TItemTable* t = ITEM_MANAGER::instance().GetTable(item->GetTransmutation());
	if (!t)
		return true;
	DWORD dwJobFlag = 0;
	switch (ch->GetJob())
	{
		case JOB_WARRIOR:	dwJobFlag = ITEM_ANTIFLAG_WARRIOR; break;
		case JOB_ASSASSIN:	dwJobFlag = ITEM_ANTIFLAG_ASSASSIN; break;
		case JOB_SURA:		dwJobFlag = ITEM_ANTIFLAG_SURA; break;
		case JOB_SHAMAN:	dwJobFlag = ITEM_ANTIFLAG_SHAMAN; break;
#ifdef ENABLE_WOLFMAN_CHARACTER
		case JOB_WOLFMAN:	dwJobFlag = ITEM_ANTIFLAG_WOLFMAN; break;
#endif
	}
	if (dwJobFlag && IS_SET(t->dwAntiFlags, dwJobFlag))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Wygl\xb9" "d tego przedmiotu nie pasuje do Twojej klasy.");
		return false;
	}
	if (t->bType == ITEM_COSTUME)
	{
		if ((IS_SET(t->dwAntiFlags, ITEM_ANTIFLAG_MALE) && GET_SEX(ch) == SEX_MALE) ||
				(IS_SET(t->dwAntiFlags, ITEM_ANTIFLAG_FEMALE) && GET_SEX(ch) == SEX_FEMALE))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Wygl\xb9" "d tego przedmiotu nie pasuje do Twojej p\xb3" "ci.");
			return false;
		}
	}
	return true;
}

// UseItemEx: Anulacja Transmutacji (72325) / Anulacja Polimorfii Wierzchowca (72343) dragged onto an item of the
// bag takes its look away; the tickets only go into the window. true: handled (`bResult` is UseItemEx's answer).
bool Mt2009ChangeLookUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell, bool& bResult)
{
	const DWORD vnum = item->GetVnum();
	if (vnum == changelook::ITEM_TICKET_1 || vnum == changelook::ITEM_TICKET_2 || vnum == changelook::ITEM_MOUNT_TICKET)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "W\xb3\xf3\xbf bilet w okno transmutacji u Teowadena.");
		bResult = false;
		return true;
	}
	if (vnum != changelook::ITEM_REVERSAL && vnum != changelook::ITEM_MOUNT_REVERSAL)
		return false;

	bResult = false;
	LPITEM target = NULL;
	if (!ch->IsValidItemPosition(DestCell) || !(target = ch->GetItem(DestCell)) || target == item)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Przeci\xb9gnij Anulacj\xea na przedmiot z transmutacj\xb9.");
		return true;
	}
	if (target->IsEquipped() || target->IsExchanging() || target->isLocked() || target->GetWindow() != INVENTORY)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zdejmij przedmiot i we\xbc go do ekwipunku.");
		return true;
	}
	if (!target->GetTransmutation())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot nie ma transmutacji.");
		return true;
	}
	if ((vnum == changelook::ITEM_MOUNT_REVERSAL) != changelook::IsMount(target))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, vnum == changelook::ITEM_MOUNT_REVERSAL ? "Ta Anulacja dzia\xb3" "a tylko na wierzchowcach."
				: "Na wierzchowcu u\xbfyj Anulacji Polimorfii Wierzchowca.");
		return true;
	}
	char hint[64];
	snprintf(hint, sizeof(hint), "look %u removed by %u", target->GetTransmutation(), vnum);
	target->SetTransmutation(0);
	target->UpdatePacket();
	target->Save();
	LogManager::instance().ItemLog(ch, target, "TRANSMUTATION_REMOVE", hint);
	item->SetCount(item->GetCount() - 1);
	ch->ChatPacket(CHAT_TYPE_INFO, "Transmutacja usuni\xeata - przedmiot ma znowu sw\xf3j wygl\xb9" "d.");
	bResult = true;
	return true;
}

#endif // ENABLE_CHANGELOOK_SYSTEM
