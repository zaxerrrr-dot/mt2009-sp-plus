// MT2009 PLUS Seon-Hae: the 6th and 7th bonus - MT2009_PLUS_SEONHAE_V1
// (the owner, 30 September: "ONLY the Seon-Hae version (NPC 20095), not the
// classic 71051 toggle"; 1 October: no new exe for this one).
//
// Owsap v6.2.6's __ATTR_6TH_7TH__ (CHARACTER::Attr67Add, questlua_attr67add.cpp,
// add_attr67.quest, uiattr67add.py) on our chat-command protocol - no packet,
// no NPC_STORAGE window, nothing in the client's exe:
//  - talking to Seon-Hae (20095, the first villages) is the quest seonhae: it
//    writes seonhae.npc_vid / seonhae.npc_time and sends "SEONHAE open"; the
//    client's window (uiseonhae.py) answers "/seonhae open".
//  - the player puts a weapon or an armour/jewel with all five ordinary bonuses
//    and fewer than two extra ones, 1-10 Powershards of the item's level band
//    (the band table below - Owsap's item_proto column 67AttrMaterial, which our
//    protos have not) and 0-5 Additives (72064-72067: 5/10/20/50) and sends
//    "/seonhae add <cell> <shards> <additive cell> <additives>". The chance is
//    Owsap's: shards x 2 + additive% x additives x shards / 50, at most 100
//    (10 shards 20 %, with 5 Power Additives 70 %).
//  - everything is checked here again (the client's window is only a form):
//    the NPC by its vid on the same map within 25 m, the flag, no other window
//    or trade, the item's cell, type, bonuses, the rare pool, the shard vnum by
//    the item's level, the counts against the caps and against what the
//    inventory holds, the additive by its vnum (never a proto value). Owsap's
//    holes: uncapped shard / additive counts, any item as an "additive",
//    shards taken before the last check, a 7-bonus item eaten - all closed.
//  - Seon-Hae keeps the item while he works (Owsap: 24 h; here the panel's
//    m2_seonhae_wait_min, 0 = 1440). The item leaves the inventory and lives in
//    the player's quest flags (vnum, count, 3 sockets, 7 bonuses - every field
//    the item table has), so there is no new window type, no DB enum, nothing
//    stuck when the quest is off: "/seonhae collect" at the NPC remakes the
//    item (a new id) once the time is up. The roll is made at hand-in and kept
//    in seonhae.result; the bonus itself is added to the remade item
//    (AddRareAttribute2, as 71051 with ENABLE_ITEM_RARE_ATTR_LEVEL_PCT).
//    Order for a crash: at hand-in the item's destroy reaches the db core at
//    once and the flags right after it (ch->Save()); at collection the cleared
//    flags go first and the remade item after them - at worst an item is lost,
//    never doubled.
//  - the switch: event flag m2_seonhae_on (1 on; apply.sh from M2_SEONHAE,
//    default 0; the classic panel's "Seon-Hae" page, web_admin.quest SEONHAE).
//    Off stops new hand-ins only - an item already with Seon-Hae can always be
//    collected.
//  - bots never: every command needs a real descriptor (not IsBot), the quest
//    skips pc.is_bot().
//
// To the client (game.py "SEONHAE", uiseonhae.py):
//   SEONHAE cfg <on>                                         (the quest, at login)
//   SEONHAE open                                             (the quest, at the NPC)
//   SEONHAE state <on> <holding> <vnum> <seconds left> <wait minutes>
//   SEONHAE item <vnum> <s0> <s1> <s2> <t0> <v0> ... <t6> <v6> (the item he keeps)
//   SEONHAE close                                            (handed in)
//   SEONHAE done <1 bonus added | 2 not this time> <vnum>
//   SEONHAE msg <id> <data>
// From the client: "/seonhae open|add|collect|close", for a GM "/seonhae gm now"
// (the time of the item he keeps to zero, Owsap's GM question).
#include "item_manager.h"
#include "char_manager.h"
#include "questmanager.h"
#include "log.h"
#include "constants.h"

namespace mt2009_seonhae
{
	const DWORD NPC_VNUM = 20095;
	const int NPC_RANGE = 2500;				// server units from Seon-Hae (Owsap's window closes at 10 m from where it opened)
	const int NPC_TALK_SECONDS = 1800;		// the quest's npc_time is that fresh at most
	const int MATERIAL_MAX = 10;			// ATTR67_MATERIAL_MAX_COUNT
	const int SUPPORT_MAX = 5;				// ATTR67_SUPPORT_MAX_COUNT
	const int PCT_PER_MATERIAL = 2;			// ATTR67_SUCCESS_PER_MATERIAL
	const int DEFAULT_WAIT_MIN = 1440;		// ATTR67_ADD_WAIT_TIME (24 h)
	const int WAIT_MIN_MAX = 7 * 1440;

	const char* const E_ON = "m2_seonhae_on";
	const char* const E_WAIT = "m2_seonhae_wait_min";

	// the player's flags (quest seonhae: pc.getqf("vnum") reads seonhae.vnum)
	const char* const F_NPC_VID = "seonhae.npc_vid";
	const char* const F_NPC_TIME = "seonhae.npc_time";
	const char* const F_VNUM = "seonhae.vnum";
	const char* const F_COUNT = "seonhae.count";
	const char* const F_READY = "seonhae.ready";
	const char* const F_RESULT = "seonhae.result";	// 1 success, 2 failure
	const char* const F_PCT = "seonhae.pct";
	const char* const F_SOCKET[ITEM_SOCKET_MAX_NUM] = { "seonhae.s0", "seonhae.s1", "seonhae.s2" };
	const char* const F_ATTR[ITEM_ATTRIBUTE_MAX_NUM] = { "seonhae.a0", "seonhae.a1", "seonhae.a2", "seonhae.a3",
		"seonhae.a4", "seonhae.a5", "seonhae.a6" };

	enum
	{
		RESULT_SUCCESS = 1,
		RESULT_FAIL = 2,
	};

	enum
	{
		MSG_OFF = 1,
		MSG_FAR = 2,
		MSG_BUSY = 3,
		MSG_HOLDING = 4,
		MSG_BAD_ITEM = 5,
		MSG_NEED_FIVE = 6,
		MSG_HAS_TWO = 7,
		MSG_ITEM_LOCKED = 8,
		MSG_NO_MATERIAL = 9,		// data: the shard's vnum
		MSG_MATERIAL_COUNT = 10,
		MSG_BAD_SUPPORT = 11,
		MSG_NO_SUPPORT = 12,		// data: the additive's vnum
		MSG_HANDED_IN = 13,			// data: minutes
		MSG_NOT_READY = 14,			// data: seconds left
		MSG_NO_SPACE = 15,
		MSG_NOTHING = 18,
		MSG_ERROR = 19,
		MSG_NO_POOL = 20,
	};

	// Owsap's 67AttrMaterial by the item's level (its item_proto, weapons and
	// armours): Grey 0-29, White 30-39, Green 40-49, Yellow 50-59, Blue 60-74,
	// Purple 75-89, Red 90-104, Rainbow 105-119, Holy 120+. The Lucent shards
	// (39078-39080) belong to Owsap's special sets, which this world has not.
	DWORD MaterialVnum(LPITEM item)
	{
		int level = 0;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (item->GetLimitType(i) == LIMIT_LEVEL)
				level = item->GetLimitValue(i);
		if (level < 30) return 39070;
		if (level < 40) return 39071;
		if (level < 50) return 39072;
		if (level < 60) return 39073;
		if (level < 75) return 39074;
		if (level < 90) return 39075;
		if (level < 105) return 39076;
		if (level < 120) return 39077;
		return 39081;
	}

	// The Additives by vnum - the bonus is never read from a proto or the client.
	int SupportPct(DWORD vnum)
	{
		switch (vnum)
		{
			case 72064: return 5;
			case 72065: return 10;
			case 72066: return 20;
			case 72067: return 50;
		}
		return 0;
	}

	int ChancePct(int materials, int supportPct, int supports)
	{
		int pct = materials * PCT_PER_MATERIAL;
		if (supports > 0 && supportPct > 0)
			pct += supportPct * supports * materials / (MATERIAL_MAX * SUPPORT_MAX);
		return std::max(0, std::min(100, pct));
	}

	bool IsOn()
	{
		return quest::CQuestManager::instance().GetEventFlag(E_ON) == 1;
	}

	int WaitMinutes()
	{
		const int m = quest::CQuestManager::instance().GetEventFlag(E_WAIT);
		return m > 0 ? std::min(m, WAIT_MIN_MAX) : DEFAULT_WAIT_MIN;
	}

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	void Cmd(LPCHARACTER ch, const char* format, ...)
	{
		if (!Eligible(ch))
			return;
		char buf[480];
		va_list args;
		va_start(args, format);
		vsnprintf(buf, sizeof(buf), format, args);
		va_end(args);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "SEONHAE %s", buf);
	}

	void Msg(LPCHARACTER ch, int id, long data = 0)
	{
		Cmd(ch, "msg %d %ld", id, data);
	}

	bool Holding(LPCHARACTER ch)
	{
		return ch->GetQuestFlag(F_VNUM) != 0;
	}

	// Seon-Hae by the vid the quest wrote, on this map, close enough, talked to lately.
	bool NearNpc(LPCHARACTER ch)
	{
		const DWORD vid = (DWORD)ch->GetQuestFlag(F_NPC_VID);
		const int talked = ch->GetQuestFlag(F_NPC_TIME);
		if (!vid || !talked || (int)get_global_time() - talked > NPC_TALK_SECONDS || (int)get_global_time() < talked)
			return false;
		LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(vid);
		if (!npc || !npc->IsNPC() || npc->GetRaceNum() != NPC_VNUM || npc->GetMapIndex() != ch->GetMapIndex())
			return false;
		return DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY()) <= NPC_RANGE;
	}

	bool Busy(LPCHARACTER ch)
	{
		return ch->IsDead() || !ch->CanHandleItem() || ch->GetExchange() || ch->GetShop() || ch->GetMyShop() ||
			ch->IsOpenSafebox() || ch->IsCubeOpen();
	}

	// An extra bonus this item's set can still get (PutRareAttributeWithLevel's own test).
	bool RarePoolHasRoom(LPITEM item)
	{
		const int set = item->GetAttributeSetIndex();
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM)
			return false;
		for (TItemAttrMap::const_iterator it = g_map_itemRare.begin(); it != g_map_itemRare.end(); ++it)
			if (it->second.bMaxLevelBySet[set] > 0 && it->second.dwProb > 0 && !item->HasRareAttr((BYTE)it->first))
				return true;
		return false;
	}

	int CheckItem(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->GetOwner() != ch || item->GetWindow() != INVENTORY)
			return MSG_BAD_ITEM;
		if (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR)
			return MSG_BAD_ITEM;
		if (item->GetAttributeSetIndex() < 0)
			return MSG_BAD_ITEM;
		if (item->IsEquipped() || item->IsExchanging() || item->isLocked() || item->IsChangingAttr() || item->GetCount() != 1)
			return MSG_ITEM_LOCKED;
		if (IS_SET(item->GetFlag(), ITEM_FLAG_UNIQUE))
			return MSG_ITEM_LOCKED;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE t = item->GetLimitType(i);
			if (t == LIMIT_REAL_TIME || t == LIMIT_REAL_TIME_START_FIRST_USE || t == LIMIT_TIMER_BASED_ON_WEAR)
				return MSG_ITEM_LOCKED;
		}
		if (item->GetAttributeCount() < ITEM_ATTRIBUTE_NORM_NUM)
			return MSG_NEED_FIVE;
		if (item->GetRareAttrCount() >= ITEM_ATTRIBUTE_RARE_NUM)
			return MSG_HAS_TWO;
		if (!RarePoolHasRoom(item))
			return MSG_NO_POOL;
		return 0;
	}

	void SendState(LPCHARACTER ch)
	{
		const DWORD vnum = (DWORD)ch->GetQuestFlag(F_VNUM);
		int left = 0;
		if (vnum)
			left = std::max(0, ch->GetQuestFlag(F_READY) - (int)get_global_time());
		Cmd(ch, "state %d %d %u %d %d", IsOn() ? 1 : 0, vnum ? 1 : 0, vnum, left, WaitMinutes());
		if (!vnum)
			return;
		char buf[400];
		int len = snprintf(buf, sizeof(buf), "item %u", vnum);
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM && len > 0 && len < (int)sizeof(buf); ++i)
			len += snprintf(buf + len, sizeof(buf) - len, " %d", ch->GetQuestFlag(F_SOCKET[i]));
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM && len > 0 && len < (int)sizeof(buf); ++i)
		{
			const unsigned int packed = (unsigned int)ch->GetQuestFlag(F_ATTR[i]);
			len += snprintf(buf + len, sizeof(buf) - len, " %u %d", (packed >> 16) & 0xFF, (int)(short)(packed & 0xFFFF));
		}
		Cmd(ch, "%s", buf);
	}

	void Open(LPCHARACTER ch)
	{
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		SendState(ch);
	}

	void Add(LPCHARACTER ch, const char* argument)
	{
		char a1[16], a2[16], a3[16], a4[16];
		const char* rest = one_argument(argument, a1, sizeof(a1));
		rest = one_argument(rest, a2, sizeof(a2));
		rest = one_argument(rest, a3, sizeof(a3));
		one_argument(rest, a4, sizeof(a4));
		if (!*a1 || !*a2 || !*a3 || !*a4)
			return;
		const int cell = atoi(a1);
		const int materials = atoi(a2);
		const int supportCell = atoi(a3);
		const int supports = atoi(a4);

		if (!IsOn())
			return Msg(ch, MSG_OFF);
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		if (Holding(ch))
			return Msg(ch, MSG_HOLDING);
		if (cell < 0 || cell >= INVENTORY_MAX_NUM)
			return Msg(ch, MSG_BAD_ITEM);
		LPITEM item = ch->GetInventoryItem((WORD)cell);
		if (const int bad = CheckItem(ch, item))
			return Msg(ch, bad);

		const DWORD materialVnum = MaterialVnum(item);
		if (materials < 1 || materials > MATERIAL_MAX)
			return Msg(ch, MSG_MATERIAL_COUNT);
		if (ch->CountSpecifyItem(materialVnum) < (ITEM_COUNT)materials)
			return Msg(ch, MSG_NO_MATERIAL, (long)materialVnum);

		DWORD supportVnum = 0;
		int supportPct = 0;
		if (supports < 0 || supports > SUPPORT_MAX)
			return Msg(ch, MSG_BAD_SUPPORT);
		if (supports > 0)
		{
			if (supportCell < 0 || supportCell >= INVENTORY_MAX_NUM || supportCell == cell)
				return Msg(ch, MSG_BAD_SUPPORT);
			LPITEM support = ch->GetInventoryItem((WORD)supportCell);
			if (!support || support->IsExchanging() || support->isLocked())
				return Msg(ch, MSG_BAD_SUPPORT);
			supportVnum = support->GetVnum();
			supportPct = SupportPct(supportVnum);
			if (!supportPct)
				return Msg(ch, MSG_BAD_SUPPORT);
			if (ch->CountSpecifyItem(supportVnum) < (ITEM_COUNT)supports)
				return Msg(ch, MSG_NO_SUPPORT, (long)supportVnum);
		}

		// Every check passed: from here on nothing refuses.
		const int pct = ChancePct(materials, supportPct, supports);
		const bool success = number(1, 100) <= pct;
		const int wait = WaitMinutes();

		ch->RemoveSpecifyItem(materialVnum, (ITEM_COUNT)materials);
		if (supports > 0)
			ch->RemoveSpecifyItem(supportVnum, (ITEM_COUNT)supports);

		const DWORD vnum = item->GetVnum();
		char hint[96];
		snprintf(hint, sizeof(hint), "%u shards %u x%d additive %u x%d pct %d %s", vnum, materialVnum, materials,
				supportVnum, supports, pct, success ? "OK" : "FAIL");
		LogManager::instance().ItemLog(ch, item, "SEONHAE_HOLD", hint);

		ch->SetQuestFlag(F_COUNT, (int)item->GetCount());
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			ch->SetQuestFlag(F_SOCKET[i], (int)item->GetSocket(i));
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE t = item->GetAttributeType(i);
			const short v = item->GetAttributeValue(i);
			ch->SetQuestFlag(F_ATTR[i], t ? (int)(((unsigned int)t << 16) | (unsigned short)v) : 0);
		}
		ch->SetQuestFlag(F_PCT, pct);
		ch->SetQuestFlag(F_RESULT, success ? RESULT_SUCCESS : RESULT_FAIL);
		ch->SetQuestFlag(F_READY, (int)get_global_time() + wait * 60);
		ch->SetQuestFlag(F_VNUM, (int)vnum);

		ITEM_MANAGER::instance().RemoveItem(item, "SEONHAE_HOLD");
		ch->Save();

		sys_log(0, "SEONHAE: %s handed in %u (%s), chance %d%%, %s, ready in %d min", ch->GetName(), vnum, hint, pct,
				success ? "success" : "failure", wait);
		Msg(ch, MSG_HANDED_IN, wait);
		Cmd(ch, "close");
	}

	void ClearHold(LPCHARACTER ch)
	{
		ch->SetQuestFlag(F_VNUM, 0);
		ch->SetQuestFlag(F_COUNT, 0);
		ch->SetQuestFlag(F_READY, 0);
		ch->SetQuestFlag(F_RESULT, 0);
		ch->SetQuestFlag(F_PCT, 0);
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			ch->SetQuestFlag(F_SOCKET[i], 0);
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			ch->SetQuestFlag(F_ATTR[i], 0);
	}

	void Collect(LPCHARACTER ch)
	{
		if (!Holding(ch))
			return Msg(ch, MSG_NOTHING);
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		const int left = ch->GetQuestFlag(F_READY) - (int)get_global_time();
		if (left > 0)
			return Msg(ch, MSG_NOT_READY, left);

		const DWORD vnum = (DWORD)ch->GetQuestFlag(F_VNUM);
		const int count = std::max(1, ch->GetQuestFlag(F_COUNT));
		LPITEM item = ITEM_MANAGER::instance().CreateItem(vnum, (ITEM_COUNT)count, 0, false);
		if (!item)
		{
			sys_err("SEONHAE: %s cannot remake %u - the item stays with Seon-Hae", ch->GetName(), vnum);
			return Msg(ch, MSG_ERROR);
		}
		long sockets[ITEM_SOCKET_MAX_NUM];
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			sockets[i] = ch->GetQuestFlag(F_SOCKET[i]);
		TPlayerItemAttribute attrs[ITEM_ATTRIBUTE_MAX_NUM];
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const unsigned int packed = (unsigned int)ch->GetQuestFlag(F_ATTR[i]);
			attrs[i].bType = (BYTE)((packed >> 16) & 0xFF);
			attrs[i].sValue = attrs[i].bType ? (short)(packed & 0xFFFF) : 0;
		}
		item->SetSockets(sockets);
		item->SetAttributes(attrs);

		const int cell = ch->GetEmptyInventoryEx(item);
		if (cell < 0)
		{
			M2_DESTROY_ITEM(item);
			return Msg(ch, MSG_NO_SPACE);
		}

		const int result = ch->GetQuestFlag(F_RESULT);
		const int pct = ch->GetQuestFlag(F_PCT);
		// The flags leave first (ch->Save()), the item after them: a crash in
		// between loses the item rather than doubling it.
		ClearHold(ch);
		ch->Save();
		item->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), cell));

		bool added = false;
		if (result == RESULT_SUCCESS)
		{
			const int before = item->GetRareAttrCount();
			if (before < ITEM_ATTRIBUTE_RARE_NUM && RarePoolHasRoom(item))
			{
				item->AddRareAttribute2();
				added = item->GetRareAttrCount() > before;
			}
			if (!added)
				sys_err("SEONHAE: %s won %u but no extra bonus could be put on it", ch->GetName(), vnum);
		}
		item->UpdatePacket();
		ITEM_MANAGER::instance().FlushDelayedSave(item);

		char hint[64];
		snprintf(hint, sizeof(hint), "%u pct %d %s", vnum, pct, added ? "ADDED" : "NONE");
		LogManager::instance().ItemLog(ch, item, added ? "SEONHAE_ADD_RARE" : "SEONHAE_RETURN", hint);
		sys_log(0, "SEONHAE: %s collected %u (new id %u): %s", ch->GetName(), vnum, item->GetID(), added ? "extra bonus" : "no bonus");
		Cmd(ch, "done %d %u", added ? RESULT_SUCCESS : RESULT_FAIL, vnum);
		SendState(ch);
	}

	std::map<DWORD, DWORD> s_mapLastCommand;

	bool TooSoon(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
		if (last && now - last < 300)
			return true;
		last = now;
		return false;
	}
}

void SeonHaeCommand(LPCHARACTER ch, const char* argument)
{
	using namespace mt2009_seonhae;
	if (!Eligible(ch))
		return;
	char sub[32], arg[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	if (strcmp(sub, "gm") && strcmp(sub, "close") && TooSoon(ch))
		return;
	if (!strcmp(sub, "open"))
		Open(ch);
	else if (!strcmp(sub, "add"))
		Add(ch, rest);
	else if (!strcmp(sub, "collect"))
		Collect(ch);
	else if (!strcmp(sub, "close"))
		;	// the window closed; nothing is held open on this side
	else if (!strcmp(sub, "gm") && ch->GetGMLevel() > GM_PLAYER)
	{
		one_argument(rest, arg, sizeof(arg));
		if (!strcmp(arg, "now") && Holding(ch))
		{
			ch->SetQuestFlag(F_READY, (int)get_global_time());
			ch->ChatPacket(CHAT_TYPE_INFO, "Seon-Hae: czas ustawiony na zero.");
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, "Seon-Hae: %s, czas %d min, trzymany przedmiot %d, wynik %d, szansa %d%%. /seonhae gm now",
					IsOn() ? "wlaczony" : "wylaczony", WaitMinutes(), ch->GetQuestFlag(F_VNUM), ch->GetQuestFlag(F_RESULT),
					ch->GetQuestFlag(F_PCT));
	}
}
