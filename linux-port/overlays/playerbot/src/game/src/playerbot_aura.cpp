// MT2009_PLUS_AURA_V1: Szata Aury (the aura outfit system of the pl-wiki "System Szat Aury"; Owsap v6.2.6
// __AURA_COSTUME_SYSTEM__, char_aura.cpp, Autor: Owsap - its rules and numbers). server-patches/aura/README.md.
// New file outside the engine's own; the hooks are server-patches/aura (edits.json), which also defines
// ENABLE_AURA_COSTUME_SYSTEM (WEAR_COSTUME_AURA 27, COSTUME_AURA 5).
//
// The outfit (49101-49106, grade = vnum - 49100: Zwyczajna .. Promienista) is worn in its own costume slot and
// keeps two sockets (Owsap's):
//   socket 0  the vnum of the jewel / shield whose bonuses it took (0: none yet)
//   socket 1  (1000 + level) * 100000 + exp in the level; 0 (a new outfit) = the grade's first level, no exp
// Worn, it gives level / 10 % (level 250: 25%) of the absorbed item's base bonuses (item_proto, the item's extra
// lines, a shield's defence) and of the bonuses copied onto it (attributes, all seven); a line under 1 rounds up
// to 1 (Owsap). CItem::ModifyPoints hands an outfit here and does nothing else with it.
//
// MT2009_PLUS_AURA_NAMES_V1: the owner's names - growth (runes) is "rozwoj", evolution "ewolucja".
// Theowahdan's (60003) three windows - Owsap's packets replaced by chat commands, like Transmutacja:
//   client -> "/aura in <slot> <cell>" (slot 0 the outfit, 1 the jewel / rune / material), "/aura out <slot>",
//             "/aura accept", "/aura cancel"
//   server -> "AURA open <type>" (0 absorb, 1 growth, 2 evolution), "AURA set <slot> <cell> <vnum> <count>",
//             "AURA del <slot>", "AURA close", "AURA done"
// The window holds item ids; "accept" checks everything again (an item moved, worn, traded or locked is refused).
//   absorb     an outfit without bonuses + a bracelet / necklace / earrings / shield: its bonuses go onto the
//              outfit, the item is destroyed (Swiadectwo Aury+ 89999 clears an outfit again)
//   growth     an outfit + Lodowa / Ognista Runa Aury (49990-49995: 1, 10, 50, 100, 250, 500 exp): runes one by one
//              until the level's top (49, 99, 149, 199, 249) is full; only the runes used are taken
//   evolution  a full outfit at the top of its grade + the grade's material and Yang (pl-wiki: Agat x10 5 mln,
//              Prosty / Ladny Kamien Chaosu x10 5 mln, Wspanialy x10 8 mln, Wspanialy x20 10 mln; always succeeds):
//              the next outfit, the level + 1, the bonuses kept
// What the others see: "AURA view <vid> <vnum>" (0: none) - the 3.0 exe's chrmgr.SetAura draws the outfit's effect
// (root/uiaura.py); sent when a character comes into view and when its outfit changes (CHARACTER::UpdatePacket,
// once per change), nothing for a character without one. A hidden outfit (the costume window's eye, quest flag
// costume_option.hide_aura - playerbot_hidecostume.cpp) or a polymorph shows none.
// Lodowa Runa Aury drops from every monster (pl-wiki: "Drop alternatywny"): event flag aura_rune_drop = per mille
// (0: 30, below 0: none), 1-3 runes, the monster at most 15 levels under the killer.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "playerbot_engine_compat.h"	// PlayerBotChangeGold (MT2009_PLUS_GOLD_CHANGE_FIX_V1)
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
#include "playerbot_item_extra_apply.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <map>

#ifdef ENABLE_AURA_COSTUME_SYSTEM

static_assert(WEAR_COSTUME_AURA == 27, "WEAR_COSTUME_AURA must stay 27 (root/uiaura.py: EQUIPMENT_SLOT_START + 27)");
static_assert(COSTUME_AURA == 5, "COSTUME_AURA must stay 5 (the item_proto rows, root/uiaura.py)");

bool Mt2009HideCostumeIsHidden(LPCHARACTER ch, BYTE bSubType); // playerbot_hidecostume.cpp (global)

namespace aura
{
	enum { TYPE_ABSORB = 0, TYPE_GROWTH = 1, TYPE_EVOLVE = 2, TYPE_MAX = 3 };
	enum { SLOT_MAIN = 0, SLOT_SUB = 1, SLOT_MAX = 2 };
	enum { SOCKET_DRAIN = 0, SOCKET_LEVEL = 1 };

	const DWORD VNUM_FIRST = 49101;		// Zwyczajna Szata Aury (grade 1) .. 49106 Promienista (grade 6)
	const DWORD VNUM_LAST = 49106;
	const DWORD ITEM_CLEAR = 89999;		// Swiadectwo Aury+
	const DWORD RUNE_ICE = 49990;		// Lodowa Runa Aury
	const int MAX_LEVEL = 250;
	const int MAX_DISTANCE = 1500;		// from where the window was opened (the client closes it at 1000)

	struct TGrade
	{
		int minLevel, maxLevel, exp;				// exp: one level of this grade
		DWORD material; int materialCount, gold;	// the evolution into the next grade
	};

	// Owsap's s_aiAuraRefineTable = the pl-wiki "System Szat Aury"
	const TGrade GRADES[6] =
	{
		{ 1, 49, 1000, 30617, 10, 5000000 },		// Zwyczajna -> Prosta: Agat x10
		{ 50, 99, 2000, 31136, 10, 5000000 },		// Prosta -> Szlachetna: Prosty Kamien Chaosu x10
		{ 100, 149, 4000, 31137, 10, 5000000 },		// Szlachetna -> Blyszczaca: Ladny Kamien Chaosu x10
		{ 150, 199, 8000, 31138, 10, 8000000 },		// Blyszczaca -> Wytworna: Wspanialy Kamien Chaosu x10
		{ 200, 249, 16000, 31138, 20, 10000000 },	// Wytworna -> Promienista: Wspanialy Kamien Chaosu x20
		{ 250, 250, 0, 0, 0, 0 },					// Promienista: the end
	};

	struct TState { int level, exp; };

	bool IsAuraVnum(DWORD vnum) { return vnum >= VNUM_FIRST && vnum <= VNUM_LAST; }
	bool IsAura(LPITEM item) { return item && item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_AURA; }
	int GradeOf(DWORD vnum) { return IsAuraVnum(vnum) ? (int) (vnum - VNUM_FIRST) : 0; }	// 0..5

	int RuneExp(DWORD vnum)
	{
		switch (vnum)
		{
			case 49990: return 1;
			case 49991: return 10;
			case 49992: return 50;
			case 49993: return 100;
			case 49994: return 250;
			case 49995: return 500;
		}
		return 0;
	}

	TState Decode(DWORD vnum, long socket)
	{
		const TGrade& g = GRADES[GradeOf(vnum)];
		TState s;
		if (socket < 100000000L)	// a new outfit: the grade's first level
		{
			s.level = g.minLevel;
			s.exp = 0;
			return s;
		}
		s.level = MINMAX(g.minLevel, (int) (socket / 100000) - 1000, g.maxLevel);
		s.exp = MINMAX(0, (int) (socket % 100000), g.exp);
		return s;
	}

	long Encode(const TState& s) { return (1000L + s.level) * 100000L + s.exp; }

	TState StateOf(LPITEM item) { return Decode(item->GetVnum(), item->GetSocket(SOCKET_LEVEL)); }

	// at the top of its grade with the level's exp full: only an evolution goes on
	bool IsFull(DWORD vnum, const TState& s)
	{
		const TGrade& g = GRADES[GradeOf(vnum)];
		return s.level >= g.maxLevel && s.exp >= g.exp;
	}

	// Owsap: (value * level / 10 / 100), under 1 -> 1, else cut
	int Drain(long value, int level)
	{
		if (value <= 0 || level <= 0)
			return 0;
		const double v = (double) value * level / 1000.0;
		return v < 1.0 ? (int) ceil(v) : (int) v;
	}

	bool IsAbsorbable(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_ARMOR)
			return false;
		switch (item->GetSubType())
		{
			case ARMOR_SHIELD:
			case ARMOR_WRIST:
			case ARMOR_NECK:
			case ARMOR_EAR:
				return true;
		}
		return false;
	}

	// ---- what the others see ------------------------------------------------------------------------------------

	std::map<DWORD, DWORD> s_shown;	// by VID: the outfit last sent around (none: nothing sent, 0)

	DWORD ShownVnum(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || ch->IsPolymorphed())
			return 0;
		LPITEM item = ch->GetWear(WEAR_COSTUME_AURA);
		if (!item || !IsAura(item))
			return 0;
#ifdef ENABLE_HIDE_COSTUME_SYSTEM
		if (::Mt2009HideCostumeIsHidden(ch, COSTUME_AURA))
			return 0;
#endif
		return item->GetVnum();
	}

	void SendAround(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch->GetSectree())
			return;
		char command[64];
		int len = snprintf(command, sizeof(command), "AURA view %u %u", (unsigned int) ch->GetVID(), (unsigned int) vnum);
		if (len <= 0 || len >= (int) sizeof(command))
			return;
		++len;	// the trailing NUL every chat packet carries
		TPacketGCChat pack;
		pack.header = HEADER_GC_CHAT;
		pack.size = sizeof(TPacketGCChat) + len;
		pack.type = CHAT_TYPE_COMMAND;
		pack.id = 0;
		pack.bEmpire = 0;
		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(TPacketGCChat));
		buf.write(command, len);
		ch->PacketAround(buf.read_peek(), buf.size());
	}

	// ---- the window -----------------------------------------------------------------------------------------------

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

	bool Busy(LPCHARACTER ch)
	{
		return ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen()
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
			|| ch->IsAcceOpened()
#endif
			;
	}

	void Del(LPCHARACTER ch, TSession& s, int slot)
	{
		if (!s.item[slot])
			return;
		s.item[slot] = 0;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA del %d", slot);
	}

	void Set(LPCHARACTER ch, TSession& s, int slot, LPITEM item)
	{
		s.item[slot] = item->GetID();
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA set %d %d %u %u", slot, (int) item->GetCell(), item->GetVnum(), (unsigned int) item->GetCount());
	}

	void Open(LPCHARACTER ch, BYTE type)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc())
			return;
		if (type >= TYPE_MAX)
			type = TYPE_ABSORB;
		if (Busy(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw zamknij inne okna (handel, sklep, magazyn, szarfy).");
			return;
		}
		TSession s;
		memset(&s, 0, sizeof(s));
		s.type = type;
		s.map = ch->GetMapIndex();
		s.x = ch->GetX();
		s.y = ch->GetY();
		s_sessions[ch->GetPlayerID()] = s;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA open %d", type);
	}

	void Close(LPCHARACTER ch, bool bTellClient)
	{
		if (s_sessions.erase(ch->GetPlayerID()) && bTellClient)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA close");
	}

	// Whether `item` may go into `slot` of this window (with `main` the outfit already there); says why not.
	bool Fits(LPCHARACTER ch, BYTE type, int slot, LPITEM item, LPITEM main)
	{
		if (slot == SLOT_MAIN)
		{
			if (!IsAura(item) || !IsAuraVnum(item->GetVnum()))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Tu mo\xbfna w\xb3o\xbfy\xe6 tylko szat\xea aury.");
				return false;
			}
			const TState st = StateOf(item);
			switch (type)
			{
				case TYPE_ABSORB:
					if (item->GetSocket(SOCKET_DRAIN))
					{
						ch->ChatPacket(CHAT_TYPE_INFO, "Ta szata ma ju\xbf przeniesione parametry. Wyczy\x9c\xe6 j\xb9 \x8cwiadectwem Aury+.");
						return false;
					}
					break;
				case TYPE_GROWTH:
					if (GradeOf(item->GetVnum()) == 5 || st.level >= MAX_LEVEL)
					{
						ch->ChatPacket(CHAT_TYPE_INFO, "Ta szata aury ma ju\xbf najwy\xbfszy poziom.");
						return false;
					}
					if (IsFull(item->GetVnum(), st))
					{
						ch->ChatPacket(CHAT_TYPE_INFO, "Ta szata jest na szczycie swojego rodzaju - teraz ewolucja (Szata aury: ewolucja).");	// MT2009_PLUS_AURA_NAMES_V1
						return false;
					}
					break;
				case TYPE_EVOLVE:
					if (GradeOf(item->GetVnum()) == 5 || st.level >= MAX_LEVEL)
					{
						ch->ChatPacket(CHAT_TYPE_INFO, "Ta szata aury ma ju\xbf najwy\xbfszy poziom.");
						return false;
					}
					if (!IsFull(item->GetVnum(), st))
					{
						ch->ChatPacket(CHAT_TYPE_INFO, "Ewolucja jest mo\xbfliwa dopiero na poziomie %d ze 100%% do\x9cwiadczenia.",
								GRADES[GradeOf(item->GetVnum())].maxLevel);
						return false;
					}
					break;
			}
			return true;
		}

		if (!main)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw w\xb3\xf3\xbf szat\xea aury.");
			return false;
		}
		switch (type)
		{
			case TYPE_ABSORB:
				if (!IsAbsorbable(item))
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "Parametry mo\xbfna przenie\x9c\xe6 tylko z bransolety, naszyjnika, kolczyk\xf3w albo tarczy.");
					return false;
				}
				break;
			case TYPE_GROWTH:
				if (!RuneExp(item->GetVnum()))
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "Tu mo\xbfna w\xb3o\xbfy\xe6 tylko Lodow\xb9 albo Ognist\xb9 Run\xea Aury.");
					return false;
				}
				break;
			case TYPE_EVOLVE:
			{
				const TGrade& g = GRADES[GradeOf(main->GetVnum())];
				if (item->GetVnum() != g.material)
				{
					const TItemTable* t = ITEM_MANAGER::instance().GetTable(g.material);
					ch->ChatPacket(CHAT_TYPE_INFO, "Do ewolucji tej szaty potrzeba: %s x%d.", t ? t->szLocaleName : "?", g.materialCount);
					return false;
				}
				if (ch->CountSpecifyItem(g.material) < (ITEM_COUNT) g.materialCount)
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "Masz za ma\xb3o materia\xb3u (potrzeba %d).", g.materialCount);
					return false;
				}
				break;
			}
		}
		return true;
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
		LPITEM main = slot == SLOT_SUB ? BagItem(ch, s.item[SLOT_MAIN]) : NULL;
		if (!Fits(ch, s.type, slot, item, main))
			return;
		Set(ch, s, slot, item);
	}

	void CheckOut(LPCHARACTER ch, TSession& s, int slot)
	{
		if (slot < 0 || slot >= SLOT_MAX)
			return;
		Del(ch, s, slot);
		if (slot == SLOT_MAIN)	// the second item was chosen for this outfit
			Del(ch, s, SLOT_SUB);
	}

	// The runes used of `count` worth `exp` each and the state after them (the window's preview does the same:
	// root/uiaura.py Grow).
	int Grow(DWORD vnum, TState& st, int count, int exp)
	{
		const TGrade& g = GRADES[GradeOf(vnum)];
		int used = 0;
		while (used < count && !IsFull(vnum, st) && g.exp > 0)
		{
			++used;
			st.exp += exp;
			while (st.exp >= g.exp && st.level < g.maxLevel)
			{
				st.exp -= g.exp;
				++st.level;
			}
			if (st.level >= g.maxLevel && st.exp >= g.exp)
				st.exp = g.exp;
		}
		return used;
	}

	void Finish(LPCHARACTER ch, TSession& s)
	{
		for (int i = 0; i < SLOT_MAX; ++i)
			Del(ch, s, i);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA done");
	}

	void AcceptAbsorb(LPCHARACTER ch, TSession& s, LPITEM main, LPITEM sub)
	{
		char hint[96];
		snprintf(hint, sizeof(hint), "absorb %u (%s)", sub->GetVnum(), sub->GetName());
		sub->CopyAttributeTo(main);
		main->SetSocket(SOCKET_DRAIN, sub->GetVnum());
		main->UpdatePacket();
		main->Save();
		LogManager::instance().ItemLog(ch, main, "AURA_ABSORB", hint);
		ITEM_MANAGER::instance().RemoveItem(sub, "AURA_ABSORB_SOURCE");
		Finish(ch, s);
		ch->ChatPacket(CHAT_TYPE_INFO, "Parametry przeniesione na szat\xea aury.");
	}

	void AcceptGrowth(LPCHARACTER ch, TSession& s, LPITEM main, LPITEM sub)
	{
		TState st = StateOf(main);
		const int used = Grow(main->GetVnum(), st, (int) sub->GetCount(), RuneExp(sub->GetVnum()));
		if (used <= 0)
		{
			Del(ch, s, SLOT_SUB);
			return;
		}
		char hint[96];
		snprintf(hint, sizeof(hint), "growth %d x %u -> level %d exp %d", used, sub->GetVnum(), st.level, st.exp);
		main->SetSocket(SOCKET_LEVEL, Encode(st));
		main->UpdatePacket();
		main->Save();
		LogManager::instance().ItemLog(ch, main, "AURA_GROWTH", hint);
		sub->SetCount(sub->GetCount() - used);
		Finish(ch, s);
		if (IsFull(main->GetVnum(), st) && GradeOf(main->GetVnum()) < 5)
			ch->ChatPacket(CHAT_TYPE_INFO, "Rozw\xf3j udany. Teraz mo\xbfliwa jest ewolucja szaty (Szata aury: ewolucja).");
		else
			ch->ChatPacket(CHAT_TYPE_INFO, "Rozw\xf3j udany: poziom %d.", st.level);
	}

	void AcceptEvolve(LPCHARACTER ch, TSession& s, LPITEM main, LPITEM sub)
	{
		const int grade = GradeOf(main->GetVnum());
		const TGrade& g = GRADES[grade];
		const TState st = StateOf(main);
		if (grade >= 5 || !IsFull(main->GetVnum(), st) || sub->GetVnum() != g.material)
		{
			Del(ch, s, SLOT_SUB);
			return;
		}
		if (ch->CountSpecifyItem(g.material) < (ITEM_COUNT) g.materialCount)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz za ma\xb3o materia\xb3u (potrzeba %d).", g.materialCount);
			return;
		}
		if (ch->GetGold() < g.gold)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz za ma\xb3o Yang (potrzeba %d).", g.gold);
			return;
		}
		LPITEM item = ITEM_MANAGER::instance().CreateItem(main->GetVnum() + 1, 1, 0, false);
		if (!item)
		{
			sys_err("aura: cannot create %u for %s", main->GetVnum() + 1, ch->GetName());
			return;
		}
		item->SetSockets(main->GetSockets());
		main->CopyAttributeTo(item);
		TState next;
		next.level = st.level + 1;
		next.exp = 0;
		item->SetSocket(SOCKET_LEVEL, Encode(next));

		PlayerBotChangeGold(ch, -(long long)g.gold);	// MT2009_PLUS_GOLD_CHANGE_FIX_V1
		ch->RemoveSpecifyItem(g.material, g.materialCount);

		char hint[96];
		snprintf(hint, sizeof(hint), "evolve %u -> %u level %d gold %d", main->GetVnum(), item->GetVnum(), next.level, g.gold);
		const WORD cell = main->GetCell();
		LogManager::instance().ItemLog(ch, main, "AURA_EVOLVE", hint);
		ITEM_MANAGER::instance().RemoveItem(main, "AURA_EVOLVE_OLD");
		item->AddToCharacter(ch, TItemPos(INVENTORY, cell));
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		LogManager::instance().ItemLog(ch, item, "AURA_EVOLVE_NEW", hint);
		Finish(ch, s);
		ch->ChatPacket(CHAT_TYPE_INFO, "Ewolucja udana: %s, poziom %d.", item->GetName(), next.level);
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
		LPITEM main = BagItem(ch, s.item[SLOT_MAIN]);
		LPITEM sub = BagItem(ch, s.item[SLOT_SUB]);
		if (!main || !sub)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "W\xb3\xf3\xbf oba przedmioty.");
			if (!main) Del(ch, s, SLOT_MAIN);
			if (!sub) Del(ch, s, SLOT_SUB);
			return;
		}
		if (!Fits(ch, s.type, SLOT_MAIN, main, NULL))
		{
			CheckOut(ch, s, SLOT_MAIN);
			return;
		}
		if (!Fits(ch, s.type, SLOT_SUB, sub, main))
		{
			Del(ch, s, SLOT_SUB);
			return;
		}
		switch (s.type)
		{
			case TYPE_ABSORB:	AcceptAbsorb(ch, s, main, sub); break;
			case TYPE_GROWTH:	AcceptGrowth(ch, s, main, sub); break;
			case TYPE_EVOLVE:	AcceptEvolve(ch, s, main, sub); break;
		}
	}

	// ---- Lodowa Runa Aury ---------------------------------------------------------------------------------------

	void DropRune(LPCHARACTER killer, LPCHARACTER victim)
	{
		int permille = quest::CQuestManager::instance().GetEventFlag("aura_rune_drop");
		if (permille < 0)
			return;
		if (permille == 0)
			permille = 30;
		if (number(1, 1000) > permille)
			return;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(RUNE_ICE, number(1, 3));
		if (!item)
			return;
		PIXEL_POSITION pos;
		pos.x = victim->GetX() + number(-100, 100);
		pos.y = victim->GetY() + number(-100, 100);
		item->SetOwnership(killer, 120);
		if (!item->AddToGround(victim->GetMapIndex(), pos))
		{
			M2_DESTROY_ITEM(item);
			return;
		}
		item->StartDestroyEvent();
	}
}

// ---- hooks (server-patches/aura) ------------------------------------------------------------------------------------

// item.cpp, CItem::ModifyPoints: true for an aura outfit - its points are here and nothing else of the engine's
// applies to it (its attributes are the absorbed item's, at the outfit's rate).
bool Mt2009AuraModifyPoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	if (!aura::IsAura(item))
		return false;
	if (!owner || !aura::IsAuraVnum(item->GetVnum()))
		return true;
	const int level = aura::StateOf(item).level;
	const DWORD drained = (DWORD) item->GetSocket(aura::SOCKET_DRAIN);
	const TItemTable* t = drained ? ITEM_MANAGER::instance().GetTable(drained) : NULL;
	if (t && t->bType == ITEM_ARMOR)
	{
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
		{
			const WORD type = t->aApplies[i].bType; // MT2009_PLUS_WIDE_ATTR_V1
			if (type == POINT_NONE || owner->IsUtilityPoint(type) || type == POINT_MOV_SPEED)
				continue;
			const int value = aura::Drain(t->aApplies[i].lValue, level);
			if (!value)
				continue;
			if (type == POINT_SKILL)
				owner->PointChange(type, bAdd ? value : value ^ 0x00800000);
			else
				owner->PointChange(type, bAdd ? value : -value);
		}
		if (const std::vector<TItemApply>* extra = GetMt2009ItemExtraApplies(drained))
		{
			for (const TItemApply& apply : *extra)
			{
				if (apply.bType == POINT_NONE || owner->IsUtilityPoint(apply.bType) || apply.bType == POINT_MOV_SPEED)
					continue;
				const int value = aura::Drain(apply.lValue, level);
				if (value)
					owner->PointChange(apply.bType, bAdd ? value : -value);
			}
		}
		if (t->bSubType == ARMOR_SHIELD)	// Owsap: the shield's defence too
		{
			const int def = aura::Drain(t->alValues[1] + t->alValues[5] * 2, level);
			if (def)
				owner->PointChange(POINT_DEF_GRADE_BONUS, bAdd ? def : -def);
		}
	}
	for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
	{
		const WORD type = item->GetAttributeType(i); // MT2009_PLUS_WIDE_ATTR_V1
		if (!type || owner->IsUtilityPoint(type))
			continue;
		const int value = aura::Drain(item->GetAttribute(i).sValue, level);
		if (value)
			owner->PointChange(type, bAdd ? value : -value);
	}
	return true;
}

// char.cpp, CHARACTER::UpdatePacket: the outfit the others see, sent around when it changed (worn, taken off,
// hidden, polymorph); "Ukryj cudze"'s refresh (g_pkMt2009PlusLooksOnlyTo) gets it to that viewer alone.
void Mt2009AuraOnUpdatePacket(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;
	extern LPCHARACTER g_pkMt2009PlusLooksOnlyTo;
	const DWORD vnum = aura::ShownVnum(ch);
	if (g_pkMt2009PlusLooksOnlyTo)
	{
		if (vnum && g_pkMt2009PlusLooksOnlyTo->GetDesc() && !g_pkMt2009PlusLooksOnlyTo->GetDesc()->IsBot())
			g_pkMt2009PlusLooksOnlyTo->ChatPacket(CHAT_TYPE_COMMAND, "AURA view %u %u", (unsigned int) ch->GetVID(), vnum);
		return;
	}
	std::map<DWORD, DWORD>::iterator it = aura::s_shown.find((DWORD) ch->GetVID());
	const DWORD before = it == aura::s_shown.end() ? 0 : it->second;
	if (before == vnum)
		return;
	if (aura::s_shown.size() > 50000)	// the VIDs of characters long gone
		aura::s_shown.clear();
	if (vnum)
		aura::s_shown[(DWORD) ch->GetVID()] = vnum;
	else if (it != aura::s_shown.end())
		aura::s_shown.erase(it);
	aura::SendAround(ch, vnum);
}

// char.cpp, EncodeInsertPacket: a character with an outfit coming into a player's view (the player too).
void Mt2009AuraOnInsert(LPCHARACTER shown, LPCHARACTER viewer)
{
	if (!shown || !viewer || !shown->IsPC() || !viewer->GetDesc() || viewer->GetDesc()->IsBot())
		return;
	const DWORD vnum = aura::ShownVnum(shown);
	if (vnum)
		viewer->ChatPacket(CHAT_TYPE_COMMAND, "AURA view %u %u", (unsigned int) shown->GetVID(), vnum);
}

// char_battle.cpp, a monster's death: Lodowa Runa Aury (pl-wiki "Drop alternatywny").
void Mt2009AuraOnKill(LPCHARACTER killer, LPCHARACTER victim)
{
	if (!killer || !victim || !killer->IsPC() || victim->IsPC() || !victim->IsMonster())
		return;
	if (!killer->GetDesc() || killer->GetDesc()->IsBot())
		return;
	if (victim->GetLevel() + 15 < killer->GetLevel())
		return;
	// MT2009_PLUS_HYDRA_NO_DROP_V1: not from the Hydra - it dies in the sea (playerbot_ship_defense.cpp).
	bool ShipDefense_NoDrop(LPCHARACTER victim);
	if (ShipDefense_NoDrop(victim))
		return;
	aura::DropRune(killer, victim);
}

// char_item.cpp, UseItemEx: Swiadectwo Aury+ (89999) dragged onto an outfit in the bag clears its bonuses (the level
// stays). true: handled (`bResult` is UseItemEx's answer).
bool Mt2009AuraUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell, bool& bResult)
{
	if (!item || item->GetVnum() != aura::ITEM_CLEAR)
		return false;
	bResult = false;
	LPITEM target = NULL;
	if (!ch->IsValidItemPosition(DestCell) || !(target = ch->GetItem(DestCell)) || target == item || !aura::IsAura(target))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Przeci\xb9gnij \x8cwiadectwo Aury+ na szat\xea aury.");
		return true;
	}
	if (target->IsEquipped() || target->IsExchanging() || target->isLocked() || target->GetWindow() != INVENTORY)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zdejmij szat\xea i we\x9f j\xb9 do ekwipunku.");
		return true;
	}
	if (aura::Find(ch))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw zamknij okno szaty aury.");
		return true;
	}
	if (!target->GetSocket(aura::SOCKET_DRAIN) && !target->GetAttributeCount())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ta szata nie ma przeniesionych parametr\xf3w.");
		return true;
	}
	char hint[64];
	snprintf(hint, sizeof(hint), "cleared %ld by %u", target->GetSocket(aura::SOCKET_DRAIN), item->GetVnum());
	target->ClearAttribute();
	target->SetSocket(aura::SOCKET_DRAIN, 0);
	target->UpdatePacket();
	target->Save();
	LogManager::instance().ItemLog(ch, target, "AURA_CLEAR", hint);
	item->SetCount(item->GetCount() - 1);
	ch->ChatPacket(CHAT_TYPE_INFO, "Parametry szaty aury usuni\xeate - mo\xbf" "esz przenie\x9c\xe6 nowe.");
	bResult = true;
	return true;
}

// quest: game.open_aura(0 absorb | 1 growth | 2 evolution) at Theowahdan (szata_aury.quest)
namespace
{
	int game_open_aura(lua_State* L)
	{
		LPCHARACTER ch = quest::CQuestManager::instance().GetCurrentCharacterPtr();
		const int type = lua_isnumber(L, 1) ? (int) lua_tonumber(L, 1) : 0;
		if (ch)
			aura::Open(ch, (BYTE) type);
		return 0;
	}

	void AuraAddToTable(lua_State* L, const char* c_pszTable, const luaL_reg* pReg)
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
	// questlua.cpp: { void RegisterAuraFunctions(); RegisterAuraFunctions(); } inside namespace quest
	void RegisterAuraFunctions()
	{
		static const luaL_reg game_add[] =
		{
			{ "open_aura",	game_open_aura },
			{ NULL, NULL }
		};
		AuraAddToTable(CQuestManager::instance().GetLuaState(), "game", game_add);
	}
}

// cmd.cpp: "/aura in <slot> <cell> | out <slot> | accept | cancel"
ACMD(do_aura)
{
	char arg1[32], arg2[32], arg3[32];
	const char* rest = one_argument(argument, arg1, sizeof(arg1));
	two_arguments(rest, arg2, sizeof(arg2), arg3, sizeof(arg3));
	if (!ch || !ch->IsPC())
		return;

	aura::TSession* s = aura::Find(ch);
	if (!s)
	{
		if (strcmp(arg1, "cancel"))
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AURA close");
		return;
	}
	if (!strcmp(arg1, "cancel"))
		aura::Close(ch, false);
	else if (!strcmp(arg1, "in"))
	{
		int slot = -1, cell = -1;
		str_to_number(slot, arg2);
		str_to_number(cell, arg3);
		aura::CheckIn(ch, *s, slot, cell);
	}
	else if (!strcmp(arg1, "out"))
	{
		int slot = -1;
		str_to_number(slot, arg2);
		aura::CheckOut(ch, *s, slot);
	}
	else if (!strcmp(arg1, "accept"))
		aura::Accept(ch, *s);
}

#endif // ENABLE_AURA_COSTUME_SYSTEM
