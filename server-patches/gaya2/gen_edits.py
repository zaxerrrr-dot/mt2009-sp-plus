#!/usr/bin/env python3
# writes server-patches/gaya2/edits.json (MT2009_PLUS_GAYA_CURRENCY_V1): python3 gen_edits.py edits.json
import json
import sys

M = 'MT2009_PLUS_GAYA_CURRENCY_V1'
E = []


def edit(file, tag, old, new):
    marker = '%s (%s)' % (M, tag)
    assert marker in new, marker
    E.append(dict(file=file, marker=marker, old=old, new=new))


# ---------------------------------------------------------------- common / db
edit('../../common/tables.h', 'player table',
     '\n} TPlayerTable;',
     '\n\t// MT2009_PLUS_GAYA_CURRENCY_V1 (player table): the Gaya of the character, a currency as on the global servers\n'
     '\t// (player.player.gaya of gaya2.sql; server-patches/gaya2). At the end: db and game are built from this header.\n'
     '\tint\t\tgaya;\n'
     '} TPlayerTable;')

edit('../../db/src/ClientManagerPlayer.cpp', 'select',
     '",conqueror_level,conqueror_level_step,conqueror_exp,conqueror_point,sungma_str,sungma_hp,sungma_move,sungma_immune"\n',
     '",conqueror_level,conqueror_level_step,conqueror_exp,conqueror_point,sungma_str,sungma_hp,sungma_move,sungma_immune"\n'
     '\t\t\t\t",gaya" // MT2009_PLUS_GAYA_CURRENCY_V1 (select): right after the champion columns (CreatePlayerTableFromRes)\n')

edit('../../db/src/ClientManagerPlayer.cpp', 'load',
     '\t\tstr_to_number(pkTab->sungma_immune, row[col++]);\n\t}\n',
     '\t\tstr_to_number(pkTab->sungma_immune, row[col++]);\n\t}\n'
     '\t// MT2009_PLUS_GAYA_CURRENCY_V1 (load): player.gaya, the column of the select above.\n'
     '\tif (col < (int)mysql_num_fields(res))\n'
     '\t\tstr_to_number(pkTab->gaya, row[col++]);\n')

edit('../../db/src/ClientManagerPlayer.cpp', 'save',
     '\tstatic char text[8192 + 1];\n',
     '\t// MT2009_PLUS_GAYA_CURRENCY_V1 (save): the Gaya of the character (gaya2.sql).\n'
     '\tqueryLen += snprintf(pszQuery + queryLen, querySize - queryLen, "gaya = %d, ", pkTab->gaya);\n'
     '\n'
     '\tstatic char text[8192 + 1];\n')

# ---------------------------------------------------------------- game: char
edit('char.h', 'char',
     '\t\tvoid\t\t\tCreatePlayerProto(TPlayerTable & tab);\n',
     '\t\tvoid\t\t\tCreatePlayerProto(TPlayerTable & tab);\n'
     '\t\t// MT2009_PLUS_GAYA_CURRENCY_V1 (char): Gaya is a currency of the character, as on the global servers\n'
     '\t\t// (server-patches/gaya2): player.gaya, at most 999 999, shown next to the Yang (the client\'s "GAYA <total>\n'
     '\t\t// <change>" line). The item Gaya (95927) becomes Gaya wherever it reaches a character (char.cpp).\n'
     '\t\tenum { MT2009_GAYA_MAX = 999999, MT2009_GAYA_ITEM_VNUM = 95927 };\n'
     '\t\tint\t\t\tGetGaya() const { return m_iMt2009Gaya; }\n'
     '\t\tbool\t\t\tChangeGaya(int iDelta, const char * c_pszWhy);\n'
     '\t\tvoid\t\t\tSendGaya(int iDelta = 0);\n'
     '\t\tvoid\t\t\tMt2009GayaSweep();\n'
     '\t\tvoid\t\t\tMt2009GayaEnter();\n'
     '\t\tint\t\t\tm_iMt2009Gaya = 0;\n'
     '\t\tint\t\t\tm_iMt2009GayaMoved = 0;\t// moved from items while the client was still loading - said on entering\n')

edit('char.cpp', 'save',
     '\ttab.horse = GetHorseData();\n}\n',
     '\ttab.horse = GetHorseData();\n'
     '\ttab.gaya = m_iMt2009Gaya; // MT2009_PLUS_GAYA_CURRENCY_V1 (save)\n'
     '}\n')

edit('char.cpp', 'load',
     '\tSetConquerorLevel(MIN(t->conqueror_level, (BYTE)30));\n',
     '\tm_iMt2009Gaya = MINMAX(0, t->gaya, (int)MT2009_GAYA_MAX); // MT2009_PLUS_GAYA_CURRENCY_V1 (load)\n'
     '\tSetConquerorLevel(MIN(t->conqueror_level, (BYTE)30));\n')

CODE = r'''// MT2009_PLUS_GAYA_CURRENCY_V1 (code): Gaya as a currency of the character, as on the global servers (the owner,
// 28 October 2026: "the counter with the icon next to the Yang, not slots in the inventory"; server-patches/gaya2).
// The value is player.gaya (TPlayerTable::gaya); every change goes through ChangeGaya (never below 0 nor above
// 999 999, a char log line "GAYA", the client's line "GAYA <total> <change>" - root/game.py; an older client only
// writes it to its syserr). The item Gaya (95927) of before is changed into it once, wherever it is:
//   - in the bag or a storage of the extra inventory: CItem::AddToCharacter (item.cpp) asks for a sweep one pulse
//     later (Mt2009GayaSweep) - the login's item load, a pick-up through a companion, a quest's or a chest's item,
//     a cube's result, a move out of the warehouse - so the caller still holds a live item;
//   - on the ground: PickupItem takes it straight into the counter (Mt2009GayaPickup, no free cell needed);
//   - in the warehouse or the ItemShop storage: when it is opened (Mt2009GayaTakeStored, char.cpp LoadSafebox /
//     LoadMall) - the stored row is deleted, the counter gets the count.
// What would go above 999 999 stays an item (and is said in the log).
EVENTINFO(mt2009_gaya_sweep_info)
{
	DWORD pid;

	mt2009_gaya_sweep_info() : pid(0) {}
};

static std::set<DWORD> s_setMt2009GayaSweep;

EVENTFUNC(mt2009_gaya_sweep_event)
{
	mt2009_gaya_sweep_info* info = dynamic_cast<mt2009_gaya_sweep_info*>(event->info);
	if (!info)
		return 0;
	s_setMt2009GayaSweep.erase(info->pid);
	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(info->pid);
	if (ch)
		ch->Mt2009GayaSweep();
	return 0;
}

void Mt2009GayaScheduleSweep(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetPlayerID())
		return;
	if (!s_setMt2009GayaSweep.insert(ch->GetPlayerID()).second)
		return;	// one is coming already
	mt2009_gaya_sweep_info* info = AllocEventInfo<mt2009_gaya_sweep_info>();
	info->pid = ch->GetPlayerID();
	event_create(mt2009_gaya_sweep_event, info, 1);
}

static bool Mt2009GayaClientReady(LPCHARACTER ch)
{
	return ch->GetDesc() && !ch->GetDesc()->IsBot() && ch->GetDesc()->IsPhase(PHASE_GAME);
}

static void Mt2009GayaSayMoved(LPCHARACTER ch, int iMoved)
{
	if (iMoved <= 0)
		return;
	if (!Mt2009GayaClientReady(ch))
	{
		ch->m_iMt2009GayaMoved += iMoved;	// said on entering the game (Mt2009GayaEnter)
		return;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, "Gaya jest teraz walut\271: %d Gaya trafi\263o na tw\363j licznik Gaya (obok Yang w ekwipunku).", iMoved);
}

bool CHARACTER::ChangeGaya(int iDelta, const char * c_pszWhy)
{
	if (!IsPC())
		return false;
	if (iDelta == 0)
		return true;
	const long long llNew = (long long)m_iMt2009Gaya + iDelta;
	if (llNew < 0 || llNew > MT2009_GAYA_MAX)
		return false;
	m_iMt2009Gaya = (int)llNew;
	sys_log(0, "GAYA: %s pid=%u %+d -> %d (%s)", GetName(), GetPlayerID(), iDelta, m_iMt2009Gaya, c_pszWhy ? c_pszWhy : "");
	LogManager::instance().CharLog(this, iDelta, "GAYA", c_pszWhy ? c_pszWhy : "");
	SendGaya(iDelta);
	Save();
	return true;
}

void CHARACTER::SendGaya(int iDelta)
{
	if (Mt2009GayaClientReady(this))
		ChatPacket(CHAT_TYPE_COMMAND, "GAYA %d %d", m_iMt2009Gaya, iDelta);
}

void CHARACTER::Mt2009GayaEnter()
{
	SendGaya(0);
	if (m_iMt2009GayaMoved > 0 && Mt2009GayaClientReady(this))
	{
		const int iMoved = m_iMt2009GayaMoved;
		m_iMt2009GayaMoved = 0;
		Mt2009GayaSayMoved(this, iMoved);
	}
}

void CHARACTER::Mt2009GayaSweep()
{
	if (!IsPC())
		return;
	const int iRoom = MT2009_GAYA_MAX - m_iMt2009Gaya;
	int iMoved = 0;
	int iKept = 0;
	for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = GetInventoryItem(i);
		if (!item || item->GetVnum() != MT2009_GAYA_ITEM_VNUM)
			continue;
		if (m_pkMyShop && m_pkMyShop->IsSellingItem(item->GetID()))
			continue;
		const int n = (int)item->GetCount();
		const int iTake = MIN(n, iRoom - iMoved);
		if (iTake <= 0)
		{
			iKept += n;
			continue;
		}
		if (iTake >= n)
			ITEM_MANAGER::instance().RemoveItem(item, "GAYA_CURRENCY");
		else
		{
			item->SetCount(n - iTake);
			iKept += n - iTake;
		}
		iMoved += iTake;
	}
	// the storages of the extra inventory (MT2009_PLUS_EKWIPUNEK_V1): what their remove took, exactly
	const ITEM_COUNT stored = Mt2009SpecialCountItem(MT2009_GAYA_ITEM_VNUM);
	if (stored)
	{
		const ITEM_COUNT want = MIN(stored, (ITEM_COUNT)MAX(0, iRoom - iMoved));
		const ITEM_COUNT left = want ? Mt2009SpecialRemoveItem(MT2009_GAYA_ITEM_VNUM, want) : 0;
		iMoved += (int)(want - left);
		iKept += (int)(stored - (want - left));
	}
	if (iKept)
		sys_log(0, "GAYA: %s pid=%u keeps %d Gaya item(s) - the counter would go above %d", GetName(), GetPlayerID(), iKept, (int)MT2009_GAYA_MAX);
	if (iMoved <= 0)
		return;
	ChangeGaya(iMoved, "ITEM");
	Mt2009GayaSayMoved(this, iMoved);
}

// a Gaya on the ground: straight into the counter (1), refused at the maximum (-1), not Gaya (0)
int Mt2009GayaPickup(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || item->GetVnum() != CHARACTER::MT2009_GAYA_ITEM_VNUM || !ch->IsPC())
		return 0;
	const int n = (int)item->GetCount();
	if ((long long)ch->GetGaya() + n > CHARACTER::MT2009_GAYA_MAX)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Masz ju\277 najwi\352cej Gaya, ile mo\277na mie\346 (999 999).");
		return -1;
	}
	LogManager::instance().ItemLog(ch, item, "GAYA_PICKUP", item->GetName());
	item->RemoveFromGround();
	M2_DESTROY_ITEM(item);
	ch->ChangeGaya(n, "PICKUP");
	if (Mt2009GayaClientReady(ch))
		ch->ChatPacket(CHAT_TYPE_INFO, "Otrzymujesz %d Gaya.", n);
	return 1;
}

// a Gaya of the warehouse / the ItemShop storage as it is loaded: into the counter, its row deleted (true)
static bool Mt2009GayaTakeStored(LPCHARACTER ch, LPITEM item, const char * c_pszWhere)
{
	if (!ch || !item || item->GetVnum() != CHARACTER::MT2009_GAYA_ITEM_VNUM || !ch->IsPC())
		return false;
	const int n = (int)item->GetCount();
	if ((long long)ch->GetGaya() + n > CHARACTER::MT2009_GAYA_MAX)
	{
		sys_log(0, "GAYA: %s pid=%u: %d Gaya stay in the %s (item id %u) - the counter would go above %d", ch->GetName(),
				ch->GetPlayerID(), n, c_pszWhere, item->GetID(), (int)CHARACTER::MT2009_GAYA_MAX);
		return false;
	}
	sys_log(0, "GAYA: %s pid=%u: %d Gaya from the %s (item id %u) into the counter", ch->GetName(), ch->GetPlayerID(), n,
			c_pszWhere, item->GetID());
	LogManager::instance().ItemLog(ch, item, "GAYA_CURRENCY", c_pszWhere);
	M2_DESTROY_ITEM(item);	// not skip-saved yet: the stored row goes (HEADER_GD_ITEM_DESTROY)
	ch->ChangeGaya(n, c_pszWhere);
	Mt2009GayaSayMoved(ch, n);
	return true;
}

'''

edit('char.cpp', 'code',
     'void CHARACTER::LoadSafebox(int iSize, YANG dwGold, int iItemCount, TPlayerItem * pItems)\n{\n',
     CODE + 'void CHARACTER::LoadSafebox(int iSize, YANG dwGold, int iItemCount, TPlayerItem * pItems)\n{\n')

LOADED = ('\t\t\tLPITEM item = ITEM_MANAGER::instance().CreateItem(pItems->vnum, pItems->count, pItems->id);\n\n'
          '\t\t\tif (!item)\n\t\t\t{\n'
          '\t\t\t\tsys_err("cannot create item vnum %d id %u (name: %s)", pItems->vnum, pItems->id, GetName());\n'
          '\t\t\t\tcontinue;\n\t\t\t}\n')
for box, where in (('m_pkSafebox', 'SAFEBOX'), ('m_pkMall', 'MALL')):
    head = '\t\t\tif (!%s->IsValidPosition(pItems->pos))\n\t\t\t\tcontinue;\n\n' % box
    tag = 'load %s' % where.lower()
    edit('char.cpp', tag, head + LOADED,
         head + LOADED +
         '\t\t\tif (Mt2009GayaTakeStored(this, item, "%s")) // MT2009_PLUS_GAYA_CURRENCY_V1 (%s): Gaya into the counter\n'
         '\t\t\t\tcontinue;\n' % (where, tag))

# ---------------------------------------------------------------- game: item add, pick-up, login
edit('item.cpp', 'add',
     '\tif (ch->GetDesc())\n\t\tm_dwLastOwnerPID = ch->GetPlayerID();\n\n\tevent_cancel(&m_pkDestroyEvent);\n',
     '\tif (ch->GetDesc())\n\t\tm_dwLastOwnerPID = ch->GetPlayerID();\n\n\tevent_cancel(&m_pkDestroyEvent);\n'
     '\t// MT2009_PLUS_GAYA_CURRENCY_V1 (add): the item Gaya becomes the character\'s Gaya a pulse later (char.cpp)\n'
     '\tif (GetVnum() == 95927)\n'
     '\t{\n'
     '\t\tvoid Mt2009GayaScheduleSweep(LPCHARACTER ch);\n'
     '\t\tMt2009GayaScheduleSweep(ch);\n'
     '\t}\n')

edit('char_item.cpp', 'pickup',
     '\tif (item->IsOwnership(this))\n\t{\n\t\tif (item->GetType() == ITEM_ELK)\n',
     '\tif (item->IsOwnership(this))\n\t{\n'
     '\t\t// MT2009_PLUS_GAYA_CURRENCY_V1 (pickup): Gaya goes straight into the counter, as Yang does (char.cpp)\n'
     '\t\t{\n'
     '\t\t\tint Mt2009GayaPickup(LPCHARACTER ch, LPITEM item);\n'
     '\t\t\tconst int iGaya = Mt2009GayaPickup(this, item);\n'
     '\t\t\tif (iGaya)\n'
     '\t\t\t\treturn iGaya > 0;\n'
     '\t\t}\n'
     '\t\tif (item->GetType() == ITEM_ELK)\n')

edit('input_login.cpp', 'enter',
     "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip's set / random bonuses\n",
     "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip's set / random bonuses\n"
     "\tch->Mt2009GayaEnter(); // MT2009_PLUS_GAYA_CURRENCY_V1 (enter): the counter next to the Yang\n")

# ---------------------------------------------------------------- game: cube
edit('cube.cpp', 'cube check',
     '\tif (cube->gaya <= 0 || ch->CountSpecifyItem(MT2009_GAYA_VNUM) >= (ITEM_COUNT)cube->gaya)\n',
     '\tif (cube->gaya <= 0 || ch->GetGaya() >= cube->gaya) // MT2009_PLUS_GAYA_CURRENCY_V1 (cube check): the counter\n')
edit('cube.cpp', 'cube take',
     '\t\tch->RemoveSpecifyItem(MT2009_GAYA_VNUM, (ITEM_COUNT)cube->gaya);\n',
     '\t\tch->ChangeGaya(-cube->gaya, "CUBE"); // MT2009_PLUS_GAYA_CURRENCY_V1 (cube take): from the counter\n')

# ---------------------------------------------------------------- game: quest functions
QF = r'''	// MT2009_PLUS_GAYA_CURRENCY_V1 (quest functions): pc.get_gaya() - the character's Gaya; pc.change_gaya(n) - adds n
	// (a cost: -n); true when done, false (nothing changes) when it would go below 0 or above 999 999 (server-patches/gaya2)
	int pc_get_gaya(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushnumber(L, ch ? ch->GetGaya() : 0);
		return 1;
	}

	int pc_change_gaya(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch || !lua_isnumber(L, 1))
		{
			lua_pushboolean(L, 0);
			return 1;
		}
		lua_pushboolean(L, ch->ChangeGaya((int)lua_tonumber(L, 1), "QUEST") ? 1 : 0);
		return 1;
	}

'''
edit('questlua_pc.cpp', 'quest functions',
     '\tvoid RegisterPCFunctionTable()\n\t{\n',
     QF + '\tvoid RegisterPCFunctionTable()\n\t{\n')
edit('questlua_pc.cpp', 'quest table',
     '\t\t\t{ "change_money",\t\tpc_change_money\t\t},\n',
     '\t\t\t{ "change_money",\t\tpc_change_money\t\t},\n'
     '\t\t\t{ "get_gaya",\t\tpc_get_gaya\t\t},\t// MT2009_PLUS_GAYA_CURRENCY_V1 (quest table)\n'
     '\t\t\t{ "change_gaya",\t\tpc_change_gaya\t\t},\n')

json.dump(E, open(sys.argv[1], 'w'), indent=1, ensure_ascii=True)
open(sys.argv[1], 'a').write('\n')
print(len(E), 'edits')
