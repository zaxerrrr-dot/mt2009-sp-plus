#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/ysets (MT2009_PLUS_YOHARA_SETS_V1) from the code below and the
random bonus tables of tools/ysets/ysets_random.json (tools/ysets/gen_ysets.py); the developer's tool (the apply
scripts read edits.json only). Every anchor is checked against a patched engine tree when one is given:

  python3 gen_edits.py [<engine game/src dir to check the anchors against>]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
M = 'MT2009_PLUS_YOHARA_SETS_V1'


def cstr(s):
    """a Polish text as a C string literal of cp1250 bytes (the sources are latin-1; the client reads cp1250)"""
    out = []
    for b in s.encode('cp1250'):
        if b == 0x22 or b == 0x5c:
            out.append('\\' + chr(b))
        elif 0x20 <= b < 0x7f:
            out.append(chr(b))
        else:
            out.append('\\%03o' % b)
    return '"' + ''.join(out) + '"'


def tables():
    d = json.load(open(os.path.join(REPO, 'tools', 'ysets', 'ysets_random.json'), encoding='utf-8'))
    L = []
    counts = []
    names = []
    for k, kind in (('w', 0), ('a', 1)):
        cl = []
        for line, opts in enumerate(d['groups'][k]):
            nm = 's_aYSets%s%d' % (k.upper(), line)
            names.append(nm)
            cl.append(len(opts))
            L.append('static const SMt2009YSetsOption %s[] = {' % nm)
            for o in opts:
                rows = o['rows'] + [o['rows'][-1]] * (5 - len(o['rows']))
                L.append('\t{ %d, %d, { %s } },' % (o['point'], len(o['rows']), ', '.join(
                    '{ %s }' % ', '.join(str(v) for v in r) for r in rows)))
            L.append('};')
        counts.append(cl)
    fam = sorted((int(b), 0 if k == 'w' else 1) for b, k in d['families'].items())
    L.append('static const SMt2009YSetsOption* const s_apYSetsLines[2][3] = { { %s }, { %s } };' % (
        ', '.join(names[:3]), ', '.join(names[3:])))
    L.append('static const BYTE s_abYSetsLineCount[2][3] = { { %s }, { %s } };' % (
        ', '.join(str(c) for c in counts[0]), ', '.join(str(c) for c in counts[1])))
    L.append('static const DWORD s_adwYSetsFamily[] = { %s };' % ', '.join(str(b) for b, _k in fam))
    L.append('static const BYTE s_abYSetsFamilyKind[] = { %s };' % ', '.join(str(k) for _b, k in fam))
    bon = []
    for s in d['sets']:
        for pieces, bl in sorted(s['bonuses'].items()):
            for point, value in bl:
                bon.append('{ %d, %s, %d, %d }' % (s['value'], pieces, point, value))
    L.append('static const SMt2009YSetsBonus s_aYSetsBonus[] = { %s };' % ', '.join(bon))
    L.append('static const char* const s_aszYSetsName[6] = { "", %s };' % ', '.join(cstr(s['name']) for s in d['sets']))
    return '\n'.join(L)


FUNCS = r'''// MT2009_PLUS_YOHARA_SETS_V1 (server-patches/ysets, README.md): the Yohara gear's random base bonuses and the
// equipment set effects (pl-wiki "Zestaw Ekwipunku", "Miecz Wezowy" ... "BronieWezoweWartosci"; Owsap's
// __SET_ITEM__ / __ITEM_APPLY_RANDOM__). An item's own data beside player.item: its "yextra" (player.item_yextra by
// item id - read when the item is loaded, written when it changes): bits 0-3 the set (1 Swiety, 2 Okazaly,
// 3 Rycerski, 4 Ksiazecy, 5 Majestatyczny), bits 8-31 the three random base bonuses of a serpent piece (a byte
// each: the bonus of its line 1-15 | the wiki's value row 0-4 << 4). The client hears it by "YITEM <window> <cell>
// <yextra>" (1 = the inventory and the equipment, 3 = the storehouse) and shows it in the tooltip.
#include "db.h"

struct SMt2009YSetsOption
{
	BYTE	bPoint;
	BYTE	bRows;
	short	asValue[5][16];
};

struct SMt2009YSetsBonus
{
	BYTE	bSet;
	BYTE	bPieces;
	BYTE	bPoint;
	int		iValue;
};

@TABLES@

bool Mt2009YSetsRandomFamily(DWORD dwVnum, int& iKind, int& iLevel)
{
	for (size_t i = 0; i < sizeof(s_adwYSetsFamily) / sizeof(s_adwYSetsFamily[0]); ++i)
	{
		if (dwVnum >= s_adwYSetsFamily[i] && dwVnum < s_adwYSetsFamily[i] + 16)
		{
			iKind = s_abYSetsFamilyKind[i];
			iLevel = dwVnum - s_adwYSetsFamily[i];
			return true;
		}
	}
	return false;
}

// 1 weapon, 2 armour, 3 helmet of level 75 or more (pl-wiki: a set goes on these three; de-wiki "ab Level 75"), else 0
int Mt2009YSetsPart(LPITEM item)
{
	if (!item || !item->GetProto())
		return 0;
	int iPart = 0;
	if (item->GetType() == ITEM_WEAPON && item->GetSubType() != WEAPON_ARROW
#ifdef ENABLE_QUIVER_SYSTEM
			&& item->GetSubType() != WEAPON_QUIVER
#endif
			)
		iPart = 1;
	else if (item->GetType() == ITEM_ARMOR && item->GetSubType() == ARMOR_BODY)
		iPart = 2;
	else if (item->GetType() == ITEM_ARMOR && item->GetSubType() == ARMOR_HEAD)
		iPart = 3;
	if (!iPart || item->GetLevelLimit() < 75)
		return 0;
	return iPart;
}

static bool Mt2009YSetsTracked(LPITEM item)
{
	int iKind, iLevel;
	return Mt2009YSetsPart(item) != 0 || Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel);
}

static void Mt2009YSetsSave(LPITEM item)
{
	if (!item->GetID())
		return;
	if (item->GetYExtra())
		DBManager::instance().DirectQuery("REPLACE INTO item_yextra (id, yextra) VALUES (%u, %u)", item->GetID(), item->GetYExtra());
	else
		DBManager::instance().DirectQuery("DELETE FROM item_yextra WHERE id = %u", item->GetID());
}

static void Mt2009YSetsRoll(LPITEM item, int iKind)
{
	DWORD dwExtra = item->GetYExtra() & 0xFF;
	for (int iLine = 0; iLine < 3; ++iLine)
	{
		const int iOpt = number(0, s_abYSetsLineCount[iKind][iLine] - 1);
		const int iRow = number(0, s_apYSetsLines[iKind][iLine][iOpt].bRows - 1);
		dwExtra |= (DWORD)((iOpt + 1) | (iRow << 4)) << (8 + 8 * iLine);
	}
	item->SetYExtra(dwExtra);
}

// ITEM_MANAGER::CreateItem: a loaded item gets its yextra back, a new serpent piece rolls its three bonuses
void Mt2009YSetsCreate(LPITEM item, bool bIsNewItem, bool bSkipSave)
{
	if (!item || !Mt2009YSetsTracked(item))
		return;
	int iKind, iLevel;
	if (bIsNewItem)
	{
		if (!Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))
			return;
		Mt2009YSetsRoll(item, iKind);
		if (!bSkipSave)
			Mt2009YSetsSave(item);
		return;
	}
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT yextra FROM item_yextra WHERE id = %u", item->GetID()));
	SQLResult* pRes = pMsg ? pMsg->Get() : NULL;
	if (pRes && pRes->uiNumRows > 0)
	{
		MYSQL_ROW row = mysql_fetch_row(pRes->pSQLResult);
		DWORD dwExtra = 0;
		if (row && row[0])
			str_to_number(dwExtra, row[0]);
		item->SetYExtra(dwExtra);
	}
	else if (Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))
	{
		// a serpent piece made before its bonuses existed (an item of a GM, an old copy): it rolls them now
		Mt2009YSetsRoll(item, iKind);
		if (!bSkipSave)
			Mt2009YSetsSave(item);
	}
}

// CItem::CopyAttributeTo (a refine and the like): the set goes on the new piece, the random bonuses of a serpent
// piece go on its next level (the same lines and rows)
void Mt2009YSetsCopy(LPITEM pFrom, LPITEM pTo)
{
	if (!pFrom || !pTo || pFrom == pTo || !pFrom->GetYExtra() || !Mt2009YSetsTracked(pTo))
		return;
	int iKindFrom, iKindTo, iLevel;
	DWORD dwExtra = pTo->GetYExtra();
	if (Mt2009YSetsPart(pTo))
		dwExtra = (dwExtra & ~0xFU) | (pFrom->GetYExtra() & 0xFU);
	if (Mt2009YSetsRandomFamily(pFrom->GetVnum(), iKindFrom, iLevel) && Mt2009YSetsRandomFamily(pTo->GetVnum(), iKindTo, iLevel)
			&& iKindFrom == iKindTo && (pFrom->GetYExtra() >> 8))
		dwExtra = (dwExtra & 0xFFU) | (pFrom->GetYExtra() & ~0xFFU);
	if (dwExtra == pTo->GetYExtra())
		return;
	pTo->SetYExtra(dwExtra);
	Mt2009YSetsSave(pTo);
}

// CItem::ModifyPoints: the three random base bonuses at the piece's refine level
void Mt2009YSetsItemPoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	int iKind, iLevel;
	if (!owner || !item->GetYExtra() || !Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))
		return;
	for (int iLine = 0; iLine < 3; ++iLine)
	{
		const BYTE b = (item->GetYExtra() >> (8 + 8 * iLine)) & 0xFF;
		const int iOpt = (b & 0x0F) - 1;
		const int iRow = b >> 4;
		if (iOpt < 0 || iOpt >= s_abYSetsLineCount[iKind][iLine])
			continue;
		const SMt2009YSetsOption& o = s_apYSetsLines[iKind][iLine][iOpt];
		if (iRow >= o.bRows)
			continue;
		const int iValue = o.asValue[iRow][iLevel];
		owner->PointChange(o.bPoint, bAdd ? iValue : -iValue);
	}
}

// the client's copy of an item's yextra (the tooltip): only when it has one, or the cell's old item had one
void Mt2009YSetsNotify(LPCHARACTER ch, int iWindow, int iCell, DWORD dwExtra)
{
	if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsPhase(PHASE_GAME) || ch->GetDesc()->IsBot())
		return;
	ch->ChatPacket(CHAT_TYPE_COMMAND, "YITEM %d %d %u", iWindow, iCell, dwExtra);
}

// Entergame: every item of the inventory and the equipment with a yextra (SetItem told nothing while loading)
void Mt2009YSetsSendAll(LPCHARACTER ch)
{
	if (!ch)
		return;
	Mt2009YSetsNotify(ch, 0, 0, 0);            // the client forgets what it heard before (a warp is a new login)
	for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetInventoryItem(i);
		if (item && item->GetCell() == i && item->GetYExtra())
			Mt2009YSetsNotify(ch, 1, i, item->GetYExtra());
	}
	for (int i = 0; i < WEAR_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetWear(i);
		if (item && item->GetYExtra())
			Mt2009YSetsNotify(ch, 1, INVENTORY_MAX_NUM + i, item->GetYExtra());
	}
}

// the worn set: the set of the most pieces among the weapon, the armour and the helmet (two or three)
static void Mt2009YSetsWorn(LPCHARACTER ch, BYTE& bSet, BYTE& bPieces)
{
	BYTE abCount[6] = { 0, 0, 0, 0, 0, 0 };
	const int aiWear[3] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD };
	for (int i = 0; i < 3; ++i)
	{
		LPITEM item = ch->GetWear(aiWear[i]);
		if (!item || !Mt2009YSetsPart(item))
			continue;
		const BYTE s = item->GetYExtra() & 0x0F;
		if (s >= 1 && s <= 5)
			++abCount[s];
	}
	bSet = 0;
	bPieces = 0;
	for (BYTE s = 1; s <= 5; ++s)
		if (abCount[s] >= 2 && abCount[s] > bPieces)
		{
			bSet = s;
			bPieces = abCount[s];
		}
}

static void Mt2009YSetsApplyTier(LPCHARACTER ch, BYTE bSet, BYTE bPieces, bool bAdd)
{
	if (!bSet)
		return;
	for (size_t i = 0; i < sizeof(s_aYSetsBonus) / sizeof(s_aYSetsBonus[0]); ++i)
	{
		const SMt2009YSetsBonus& b = s_aYSetsBonus[i];
		if (b.bSet == bSet && b.bPieces == bPieces)
			ch->PointChange(b.bPoint, bAdd ? b.iValue : -b.iValue);
	}
}

static bool Mt2009YSetsHasTier(BYTE bSet, BYTE bPieces)
{
	for (size_t i = 0; i < sizeof(s_aYSetsBonus) / sizeof(s_aYSetsBonus[0]); ++i)
		if (s_aYSetsBonus[i].bSet == bSet && s_aYSetsBonus[i].bPieces == bPieces)
			return true;
	return false;
}

// CItem::EquipTo / Unequip and CHARACTER::ComputePoints: the set bonus of what is worn now in the points
void Mt2009YSetsRefresh(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;
	BYTE bSet, bPieces;
	Mt2009YSetsWorn(ch, bSet, bPieces);
	if (bSet && !Mt2009YSetsHasTier(bSet, bPieces))
		bSet = bPieces = 0;              // the princely / majestic sets have no two-piece bonus
	if (bSet == ch->m_bYSetApplied && bPieces == ch->m_bYSetAppliedCount)
		return;
	Mt2009YSetsApplyTier(ch, ch->m_bYSetApplied, ch->m_bYSetAppliedCount, false);
	Mt2009YSetsApplyTier(ch, bSet, bPieces, true);
	const bool bTell = bSet != ch->m_bYSetApplied || bPieces != ch->m_bYSetAppliedCount;
	ch->m_bYSetApplied = bSet;
	ch->m_bYSetAppliedCount = bPieces;
	if (bTell && bSet && ch->GetDesc() && ch->GetDesc()->IsPhase(PHASE_GAME) && !ch->GetDesc()->IsBot())
		ch->ChatPacket(CHAT_TYPE_INFO, "%s: %d/3 " @ACTIVE@, s_aszYSetsName[bSet], bPieces);
}

// CHARACTER::ComputePoints rebuilt the points from nothing: nothing of a set is in them
void Mt2009YSetsReset(LPCHARACTER ch)
{
	if (!ch)
		return;
	ch->m_bYSetApplied = 0;
	ch->m_bYSetAppliedCount = 0;
}

// the set blacksmiths' cube: the piece the set goes on (one of the cube's items, not a material)
LPITEM Mt2009YSetsCubeGear(LPITEM* items, int iCount, int iPart)
{
	for (int i = 0; i < iCount; ++i)
	{
		LPITEM item = items[i];
		if (!item || item->IsEquipped() || Mt2009YSetsPart(item) != iPart || item->GetRefineLevel() < 7)
			continue;
		return item;
	}
	return NULL;
}

void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet)
{
	item->SetYExtra((item->GetYExtra() & ~0xFU) | (bSet & 0x0F));
	Mt2009YSetsSave(item);
	if (ch && item->GetOwner() == ch && (item->GetWindow() == INVENTORY || item->GetWindow() == EQUIPMENT))
		Mt2009YSetsNotify(ch, 1, item->GetCell(), item->GetYExtra());
}

'''

DECL = '''
// MT2009_PLUS_YOHARA_SETS_V1 (declare): server-patches/ysets (item.cpp)
bool Mt2009YSetsRandomFamily(DWORD dwVnum, int& iKind, int& iLevel);
int Mt2009YSetsPart(LPITEM item);
void Mt2009YSetsCreate(LPITEM item, bool bIsNewItem, bool bSkipSave);
void Mt2009YSetsCopy(LPITEM pFrom, LPITEM pTo);
void Mt2009YSetsItemPoints(LPITEM item, LPCHARACTER owner, bool bAdd);
void Mt2009YSetsNotify(LPCHARACTER ch, int iWindow, int iCell, DWORD dwExtra);
void Mt2009YSetsSendAll(LPCHARACTER ch);
void Mt2009YSetsRefresh(LPCHARACTER ch);
void Mt2009YSetsReset(LPCHARACTER ch);
LPITEM Mt2009YSetsCubeGear(LPITEM* items, int iCount, int iPart);
void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet);

#endif
'''

CUBE_MAKE = r'''// MT2009_PLUS_YOHARA_SETS_V1 (cube set): a set blacksmith's recipe (set_value / set_part) puts the set on the piece
// in the cube - the materials and the Yang go either way, the piece stays (pl-wiki "Zestaw Ekwipunku": a failure
// does not harm it); nothing is given
static bool Mt2009YSetsCubeMake(LPCHARACTER ch, CUBE_DATA* cube_proto, LPITEM* items)
{
	LPITEM gear = Mt2009YSetsCubeGear(items, CUBE_MAX_NUM, cube_proto->set_part);
	if (!gear)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, @NOGEAR@);
		return false;
	}
	if ((gear->GetYExtra() & 0x0F) == (DWORD)cube_proto->set_value)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, @HASSET@);
		return false;
	}
	if (cube_proto->gold < 0 || ch->GetGold() < cube_proto->gold)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, @NOGOLD@);
		return false;
	}
	cube_proto->remove_material(ch);
	if (0 < cube_proto->gold)
		ch->ChangeGold(-(cube_proto->gold));
	if (number(1, 100) <= cube_proto->percent)
	{
		for (int i = 0; i < CUBE_MAX_NUM; ++i)    // the client empties its window after a success (a failure keeps it)
			if (items[i] == gear)
				items[i] = NULL;
		Mt2009YSetsSetValue(ch, gear, (BYTE)cube_proto->set_value);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "cube success %u %d", gear->GetVnum(), 1);
		ch->ChatPacket(CHAT_TYPE_INFO, @SUCCESS@, gear->GetName());
		LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), gear->GetVnum(), gear->GetID(), cube_proto->set_value, 1);
		return true;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, @FAIL@);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "cube fail");
	LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), gear->GetVnum(), 0, cube_proto->set_value, 0);
	return false;
}

// return new item
bool Cube_make (LPCHARACTER ch)
'''

TEXTS = dict(ACTIVE=cstr(u'części - efekt zestawu aktywny'),
             NOGEAR=cstr(u'Połóż w oknie broń, zbroję albo hełm od 75. poziomu, ulepszony co najmniej do +7.'),
             HASSET=cstr(u'Ten przedmiot ma już ten efekt zestawu.'),
             NOGOLD=cstr(u'Masz za mało Yang.'),
             SUCCESS=cstr(u'Efekt zestawu nadany: %s.'),
             FAIL=cstr(u'Nie udało się nadać efektu zestawu. Przedmiot pozostał nienaruszony.'))


def sub(s):
    for k, v in TEXTS.items():
        s = s.replace('@%s@' % k, v)
    return s


EDITS = [
    # -- item.h: the yextra member, the declarations --
    dict(file='item.h', marker=M + ' (item member)',
         old='\t\tvoid\t\tSetSkipSave(bool b)\t{ m_bSkipSave = b; }\n',
         new='\t\tDWORD\t\tGetYExtra() const\t{ return m_dwYExtra; } // ' + M + ' (item member): the set / random bonuses\n'
             '\t\tvoid\t\tSetYExtra(DWORD dw)\t{ m_dwYExtra = dw; }\n'
             '\t\tvoid\t\tSetSkipSave(bool b)\t{ m_bSkipSave = b; }\n'),
    dict(file='item.h', marker=M + ' (item field)',
         old='\t\tbool\t\tm_bSkipSave;\n\n\t\tbool\t\tm_isLocked;\n',
         new='\t\tbool\t\tm_bSkipSave;\n\t\tDWORD\t\tm_dwYExtra = 0; // ' + M + ' (item field)\n\n\t\tbool\t\tm_isLocked;\n'),
    dict(file='item.h', marker=M + ' (declare)',
         old='\titem_vid_event_info()\n\t: item_vid( 0 )\n\t{\n\t}\n};\n\n#endif\n',
         new='\titem_vid_event_info()\n\t: item_vid( 0 )\n\t{\n\t}\n};\n' + DECL),
    # -- item.cpp: reset, the functions, the random bonuses in the points, the set on equip / unequip --
    dict(file='item.cpp', marker=M + ' (init)',
         old='\tm_bSkipSave = false;\n\tm_dwLastOwnerPID = 0;\n}\n',
         new='\tm_bSkipSave = false;\n\tm_dwLastOwnerPID = 0;\n\tm_dwYExtra = 0; // ' + M + ' (init)\n}\n'),
    dict(file='item.cpp', marker=M + ' (server-patches/ysets, README.md)',
         old='int CItem::GetWindowInventoryEx()\n{\n',
         new=sub(FUNCS).replace('@TABLES@', tables()) + 'int CItem::GetWindowInventoryEx()\n{\n'),
    dict(file='item.cpp', marker=M + ' (points)',
         old='\t\t\tm_pOwner->PointChange(apply.bType, bAdd ? value : -value);\n\t\t}\n\t}\n\n#ifdef ENABLE_ACCE_COSTUME_SYSTEM\n'
             '\tif (GetType() == ITEM_COSTUME && GetSubType() == COSTUME_ACCE)\n',
         new='\t\t\tm_pOwner->PointChange(apply.bType, bAdd ? value : -value);\n\t\t}\n\t}\n\n'
             '\tMt2009YSetsItemPoints(this, m_pOwner, bAdd); // ' + M + ' (points): a serpent piece\'s random base bonuses\n\n'
             '#ifdef ENABLE_ACCE_COSTUME_SYSTEM\n\tif (GetType() == ITEM_COSTUME && GetSubType() == COSTUME_ACCE)\n'),
    dict(file='item.cpp', marker=M + ' (equip)',
         old='\tm_pOwner->ComputeBattlePoints();\n\n\tm_pOwner->UpdatePacket();\n\n#ifdef ENABLE_HIGHLIGHT_NEW_ITEM\n\tSetLastOwnerPID(m_pOwner->GetPlayerID());\n',
         new='\tMt2009YSetsRefresh(m_pOwner); // ' + M + ' (equip): the worn set\'s bonus\n\n'
             '\tm_pOwner->ComputeBattlePoints();\n\n\tm_pOwner->UpdatePacket();\n\n#ifdef ENABLE_HIGHLIGHT_NEW_ITEM\n\tSetLastOwnerPID(m_pOwner->GetPlayerID());\n'),
    dict(file='item.cpp', marker=M + ' (unequip)',
         old='\tm_pOwner->SetWear(GetCell() - INVENTORY_MAX_NUM, NULL);\n',
         new='\tm_pOwner->SetWear(GetCell() - INVENTORY_MAX_NUM, NULL);\n\tMt2009YSetsRefresh(m_pOwner); // ' + M + ' (unequip): the worn set\'s bonus\n'),
    # -- item_manager.cpp: load / roll --
    dict(file='item_manager.cpp', marker=M + ' (create)',
         old='\t\tDSManager::instance().RepairZeroAttributeItem(item);\n\t}\n\treturn item;\n}\n',
         new='\t\tDSManager::instance().RepairZeroAttributeItem(item);\n\t}\n'
             '\tMt2009YSetsCreate(item, bIsNewItem, bSkipSave); // ' + M + ' (create): its set / random bonuses\n\treturn item;\n}\n'),
    # -- item_attribute.cpp: a refine carries them --
    dict(file='item_attribute.cpp', marker=M + ' (copy)',
         old='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n',
         new='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n\tMt2009YSetsCopy(this, pItem); // ' + M + ' (copy): the set and the random bonuses\n'),
    # -- char.h / char.cpp: the set bonus in the points --
    dict(file='char.h', marker=M + ' (char)',
         old='\tprotected:\n\t\tDWORD\t\t\tm_dwPolymorphRace;\n',
         new='\tpublic:\n\t\tBYTE\t\t\tm_bYSetApplied = 0; // ' + M + ' (char): the set whose bonus is in the points now\n'
             '\t\tBYTE\t\t\tm_bYSetAppliedCount = 0;\n\n\tprotected:\n\t\tDWORD\t\t\tm_dwPolymorphRace;\n'),
    dict(file='char.cpp', marker=M + ' (init)',
         old='\tm_bCharType = CHAR_TYPE_MONSTER;\n\n\tSetPosition(POS_STANDING);\n',
         new='\tm_bCharType = CHAR_TYPE_MONSTER;\n\tm_bYSetApplied = m_bYSetAppliedCount = 0; // ' + M + ' (init)\n\n\tSetPosition(POS_STANDING);\n'),
    dict(file='char.cpp', marker=M + ' (compute)',
         old='\t\t\t\t\tif (DSManager::instance().IsTimeLeftDragonSoul(pItem))\n\t\t\t\t\t\tpItem->ModifyPoints(true);\n'
             '\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\n\tComputeBattlePoints();\n',
         new='\t\t\t\t\tif (DSManager::instance().IsTimeLeftDragonSoul(pItem))\n\t\t\t\t\t\tpItem->ModifyPoints(true);\n'
             '\t\t\t\t}\n\t\t\t}\n\t\t}\n\n\t\tMt2009YSetsReset(this); // ' + M + ' (compute): the worn set\'s bonus on the new points\n'
             '\t\tMt2009YSetsRefresh(this);\n\t}\n\n\tComputeBattlePoints();\n'),
    # -- char_item.cpp: the client's copy --
    dict(file='char_item.cpp', marker=M + ' (old)',
         old='\tWORD wCell = Cell.cell;\n\tBYTE window_type = Cell.window_type;\n\tif ((unsigned long)((CItem*)pItem) == 0xff',
         new='\tWORD wCell = Cell.cell;\n\tBYTE window_type = Cell.window_type;\n'
             '\tLPITEM pYSetsOld = ((window_type == INVENTORY || window_type == EQUIPMENT) && wCell < INVENTORY_AND_EQUIP_SLOT_MAX) ? m_PlayerSlots->pItems[wCell] : NULL; // ' + M + ' (old)\n'
             '\tif ((unsigned long)((CItem*)pItem) == 0xff'),
    dict(file='char_item.cpp', marker=M + ' (notify)',
         old='\t\t\tGetDesc()->Packet(&pack, sizeof(TPacketGCItemDelDeprecated));\n\t\t}\n\t}\n',
         new='\t\t\tGetDesc()->Packet(&pack, sizeof(TPacketGCItemDelDeprecated));\n\t\t}\n\n'
             '\t\t// ' + M + ' (notify): the set / random bonuses of the item now in the cell (the tooltip)\n'
             '\t\tif ((window_type == INVENTORY || window_type == EQUIPMENT) && ((pItem && pItem->GetYExtra()) || (pYSetsOld && pYSetsOld != pItem && pYSetsOld->GetYExtra())))\n'
             '\t\t\tMt2009YSetsNotify(this, 1, wCell, pItem ? pItem->GetYExtra() : 0);\n\t}\n'),
    dict(file='input_login.cpp', marker=M + ' (enter)',
         old='\td->SetPhase(PHASE_GAME);\n\n\tif (ch->HasPlayerData())\n',
         new='\td->SetPhase(PHASE_GAME);\n\tMt2009YSetsSendAll(ch); // ' + M + ' (enter): the tooltip\'s set / random bonuses\n\n\tif (ch->HasPlayerData())\n'),
    # -- safebox.cpp: the storehouse's tooltip --
    dict(file='safebox.cpp', marker=M + ' (safebox add)',
         old='\tm_pkChrOwner->GetDesc()->Packet(&pack, sizeof(pack));\n\tsys_log(1, "SAFEBOX: ADD %s %s count %d"',
         new='\tm_pkChrOwner->GetDesc()->Packet(&pack, sizeof(pack));\n'
             '\tif (m_bWindowMode == SAFEBOX && pkItem->GetYExtra()) // ' + M + ' (safebox add)\n'
             '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, pkItem->GetYExtra());\n'
             '\tsys_log(1, "SAFEBOX: ADD %s %s count %d"'),
    dict(file='safebox.cpp', marker=M + ' (safebox remove)',
         old='\tm_pkChrOwner->GetDesc()->Packet(&pack, sizeof(pack));\n\tsys_log(1, "SAFEBOX: REMOVE %s %s count %d"',
         new='\tm_pkChrOwner->GetDesc()->Packet(&pack, sizeof(pack));\n'
             '\tif (m_bWindowMode == SAFEBOX && pkItem->GetYExtra()) // ' + M + ' (safebox remove)\n'
             '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, 0);\n'
             '\tsys_log(1, "SAFEBOX: REMOVE %s %s count %d"'),
    # -- cube: the set blacksmiths' recipes --
    dict(file='cube.h', marker=M + ' (cube data)',
         old='\tint\t\t\t\t\t\tpercent;\n\tYANG\t\t\t\t\tgold;\n',
         new='\tint\t\t\t\t\t\tpercent;\n\tYANG\t\t\t\t\tgold;\n'
             '\tint\t\t\t\t\t\tset_value = 0; // ' + M + ' (cube data): a set blacksmith\'s recipe - the set\n'
             '\tint\t\t\t\t\t\tset_part = 0; // 1 weapon, 2 armour, 3 helmet\n'),
    dict(file='cube.cpp', marker=M + ' (cube load)',
         old='\t\telse TOKEN("gold")\n\t\t{\n\t\t\tcube_data->gold = value1;\n\t\t}\n',
         new='\t\telse TOKEN("gold")\n\t\t{\n\t\t\tcube_data->gold = value1;\n\t\t}\n'
             '\t\telse TOKEN("set_value") // ' + M + ' (cube load)\n\t\t{\n\t\t\tcube_data->set_value = value1;\n\t\t}\n'
             '\t\telse TOKEN("set_part")\n\t\t{\n\t\t\tcube_data->set_part = value1;\n\t\t}\n'),
    dict(file='cube.cpp', marker=M + ' (cube can make)',
         old='\treturn true;\n}\n\nCUBE_VALUE* CUBE_DATA::reward_value ()',
         new='\tif (this->set_value && !Mt2009YSetsCubeGear(items, CUBE_MAX_NUM, this->set_part)) // ' + M + ' (cube can make)\n'
             '\t\treturn false;\n\n\treturn true;\n}\n\nCUBE_VALUE* CUBE_DATA::reward_value ()'),
    dict(file='cube.cpp', marker=M + ' (cube set)',
         old='// return new item\nbool Cube_make (LPCHARACTER ch)\n',
         new=sub(CUBE_MAKE)),
    dict(file='cube.cpp', marker=M + ' (cube make)',
         old='\tYANG cube_gold = cube_proto->gold;\n',
         new='\tif (cube_proto->set_value) // ' + M + ' (cube make): a set blacksmith\n'
             '\t\treturn Mt2009YSetsCubeMake(ch, cube_proto, items);\n\n\tYANG cube_gold = cube_proto->gold;\n'),
]


# -- MT2009_PLUS_YOHARA_SETS_V2: fixes of the 3.0 test (cache/yohara/bledy-3.0.md #3, #16) - edits on top of V1 --
M2 = 'MT2009_PLUS_YOHARA_SETS_V2'

RESEND = '// ' + M2 + r''' (resend): fix 3.0 #16 - "/yitem": the client asks when a tooltip shows a serpent piece whose
// random bonuses it has not heard (they were rolled, only the client's copy was missing) - everything again
// (Mt2009YSetsSendAll), at most once a second a character
void Mt2009YSetsResend(LPCHARACTER ch)
{
	static std::map<DWORD, DWORD> s_mapLast;
	if (!ch || !ch->IsPC() || !ch->GetDesc())
		return;
	const DWORD dwNow = get_dword_time();
	DWORD& rdwLast = s_mapLast[ch->GetPlayerID()];
	if (rdwLast && dwNow - rdwLast < 1000)
		return;
	rdwLast = dwNow;
	Mt2009YSetsSendAll(ch);
}

void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet)
{
'''

CUBE_LIST = '// ' + M2 + r''' (cube set list): fix 3.0 #3 - a set blacksmith's window lists, as the official one (pl-wiki
// "Zestaw Ekwipunku", the blacksmiths' pictures), the pieces it can work on - here the player's own: every weapon /
// armour / helmet of level 75+ at +7 or more in the inventory without this set yet. A result is the piece itself, its
// materials the piece + the recipe's (the shards, the Projekt, the moon stone), its Yang the recipe's. (The static
// list showed the recipes' "reward" - the Projekt, with the same Projekt among its materials.) Cube_make is unchanged:
// the recipe of the part matches the shards and the Projekt, the piece lies beside them (Mt2009YSetsCubeMake).
static std::map<DWORD, std::vector<std::pair<DWORD, CUBE_DATA*> > > s_mapMt2009YSetsCubeList;

static bool Mt2009YSetsSmithRecipes(DWORD npcVNUM, CUBE_DATA** apRecipe)
{
	bool bSmith = false;
	for (size_t i = 0; i < s_cube_proto.size(); ++i)
	{
		CUBE_DATA* pCube = s_cube_proto[i];
		if (!pCube->set_value || pCube->set_part < 1 || pCube->set_part > 3)
			continue;
		bool bNpc = false;
		for (size_t j = 0; j < pCube->npc_vnum.size(); ++j)
			if (pCube->npc_vnum[j] == npcVNUM)
				bNpc = true;
		if (!bNpc)
			continue;
		if (!apRecipe[pCube->set_part - 1])
			apRecipe[pCube->set_part - 1] = pCube;
		bSmith = true;
	}
	return bSmith;
}

static bool Mt2009YSetsCubeResultList(LPCHARACTER ch, DWORD npcVNUM)
{
	CUBE_DATA* apRecipe[3] = { NULL, NULL, NULL };
	if (!Mt2009YSetsSmithRecipes(npcVNUM, apRecipe))
		return false;
	std::vector<std::pair<DWORD, CUBE_DATA*> >& rList = s_mapMt2009YSetsCubeList[ch->GetPlayerID()];
	rList.clear();
	std::string strText;
	for (int iPart = 1; iPart <= 3; ++iPart)
	{
		CUBE_DATA* pRecipe = apRecipe[iPart - 1];
		if (!pRecipe)
			continue;
		for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = ch->GetInventoryItem(i);
			if (!item || item->GetCell() != i || item->IsEquipped() || Mt2009YSetsPart(item) != iPart || item->GetRefineLevel() < 7)
				continue;
			if ((item->GetYExtra() & 0x0F) == (DWORD)pRecipe->set_value)
				continue;
			bool bHave = false;
			for (size_t j = 0; j < rList.size(); ++j)
				if (rList[j].first == item->GetVnum())
					bHave = true;
			if (bHave)
				continue;
			char szEntry[32];
			snprintf(szEntry, sizeof(szEntry), "%u,1/", item->GetVnum());
			if (strText.size() + strlen(szEntry) + 48 >= CHAT_MAX_LEN)
				break;
			strText += szEntry;
			rList.push_back(std::make_pair(item->GetVnum(), pRecipe));
		}
	}
	if (rList.empty())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, @NOPIECE@);
		return true;
	}
	strText.erase(strText.size() - 1);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "cube r_list %u %u %s", npcVNUM, (unsigned int)rList.size(), strText.c_str());
	return true;
}

static bool Mt2009YSetsCubeMaterialInfo(LPCHARACTER ch, DWORD npcVNUM, int iStart, int iCount)
{
	CUBE_DATA* apRecipe[3] = { NULL, NULL, NULL };
	if (!Mt2009YSetsSmithRecipes(npcVNUM, apRecipe))
		return false;
	std::map<DWORD, std::vector<std::pair<DWORD, CUBE_DATA*> > >::const_iterator it = s_mapMt2009YSetsCubeList.find(ch->GetPlayerID());
	if (it == s_mapMt2009YSetsCubeList.end() || iStart < 0 || iCount <= 0)
		return true;
	std::string strText;
	for (int i = iStart; i < iStart + iCount && i < (int)it->second.size(); ++i)
	{
		const CUBE_DATA* pRecipe = it->second[i].second;
		char szPart[64];
		snprintf(szPart, sizeof(szPart), "%u,1", it->second[i].first);
		std::string strOne = szPart;
		for (size_t j = 0; j < pRecipe->item.size(); ++j)
		{
			snprintf(szPart, sizeof(szPart), "&%u,%d", pRecipe->item[j].vnum, pRecipe->item[j].count);
			strOne += szPart;
		}
		if (pRecipe->gold > 0)
		{
			snprintf(szPart, sizeof(szPart), "/%lld", (long long)pRecipe->gold);
			strOne += szPart;
		}
		strText += strOne + "@";
	}
	if (strText.empty())
		return true;
	strText.erase(strText.size() - 1);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "cube m_info %d %d %s", iStart, iCount, strText.c_str());
	return true;
}

void Cube_request_result_list(LPCHARACTER ch)
{
	RETURN_IF_CUBE_IS_NOT_OPENED(ch);

	LPCHARACTER	npc = ch->GetQuestNPC();
	if (NULL == npc)
		return;

	DWORD npcVNUM = npc->GetRaceNum();
	if (Mt2009YSetsCubeResultList(ch, npcVNUM)) // ''' + M2 + ''' (cube set list)
		return;
'''

NOPIECE = cstr(u'Nie masz w ekwipunku broni, zbroi ani hełmu od 75. poziomu ulepszonych co najmniej do +7 (bez efektu '
               u'zestawu tego kowala). Połóż przedmiot w oknie razem z odłamkami i Projektem Zestawu.')

EDITS += [
    dict(file='item.h', marker=M2 + ' (declare)',
         old='void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet);\n',
         new='void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet);\n'
             'void Mt2009YSetsResend(LPCHARACTER ch); // ' + M2 + ' (declare): "/yitem"\n'),
    dict(file='item.cpp', marker=M2 + ' (resend)',
         old='void Mt2009YSetsSetValue(LPCHARACTER ch, LPITEM item, BYTE bSet)\n{\n',
         new=RESEND),
    # a copy onto a piece the player holds already: the client hears the new yextra
    dict(file='item.cpp', marker=M2 + ' (copy notify)',
         old='\tpTo->SetYExtra(dwExtra);\n\tMt2009YSetsSave(pTo);\n}\n',
         new='\tpTo->SetYExtra(dwExtra);\n\tMt2009YSetsSave(pTo);\n'
             '\tif (pTo->GetOwner() && (pTo->GetWindow() == INVENTORY || pTo->GetWindow() == EQUIPMENT)) // ' + M2 + ' (copy notify)\n'
             '\t\tMt2009YSetsNotify(pTo->GetOwner(), 1, pTo->GetCell(), dwExtra);\n}\n'),
    # an item put into the inventory / equipment (GM /item, a pick-up, a chest, the cube, a trade, the storehouse):
    # its yextra once more when the item is the character's (SetItem told it already; this one is after the owner)
    dict(file='item.cpp', marker=M2 + ' (add)',
         old='\tm_pOwner = ch;\n\n#ifdef USE_PET_SEAL_ON_LOGIN\n',
         new='\tm_pOwner = ch;\n'
             '\tif ((window_type == INVENTORY || window_type == EQUIPMENT) && GetYExtra()) // ' + M2 + ' (add)\n'
             '\t\tMt2009YSetsNotify(ch, 1, pos, GetYExtra());\n\n#ifdef USE_PET_SEAL_ON_LOGIN\n'),
    dict(file='cmd.cpp', marker=M2 + ' (command declare)',
         old='struct command_info cmd_info[] =\n',
         new='// ' + M2 + ' (command declare): "/yitem" - the client asks for its items\' set / random bonuses again\n'
             'void Mt2009YSetsResend(LPCHARACTER ch);\n'
             'ACMD(do_yitem)\n{\n\tMt2009YSetsResend(ch);\n}\n'
             'struct command_info cmd_info[] =\n'),
    dict(file='cmd.cpp', marker=M2 + ' (command table)',
         old='\t{ "\\n",\t\tNULL,\t\t\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t}\n};\n',
         new='\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // ' + M2 + ' (command table)\n'
             '\t{ "\\n",\t\tNULL,\t\t\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t}\n};\n'),
    dict(file='cube.cpp', marker=M2 + ' (cube set list)',
         old='void Cube_request_result_list(LPCHARACTER ch)\n{\n\tRETURN_IF_CUBE_IS_NOT_OPENED(ch);\n\n'
             '\tLPCHARACTER\tnpc = ch->GetQuestNPC();\n\tif (NULL == npc)\n\t\treturn;\n\n\tDWORD npcVNUM = npc->GetRaceNum();\n',
         new=CUBE_LIST.replace('@NOPIECE@', NOPIECE)),
    dict(file='cube.cpp', marker=M2 + ' (cube set materials)',
         old='void Cube_request_material_info(LPCHARACTER ch, int requestStartIndex, int requestCount)\n{\n'
             '\tRETURN_IF_CUBE_IS_NOT_OPENED(ch);\n\n\tLPCHARACTER\tnpc = ch->GetQuestNPC();\n\tif (NULL == npc)\n\t\treturn;\n\n'
             '\tDWORD npcVNUM = npc->GetRaceNum();\n',
         new='void Cube_request_material_info(LPCHARACTER ch, int requestStartIndex, int requestCount)\n{\n'
             '\tRETURN_IF_CUBE_IS_NOT_OPENED(ch);\n\n\tLPCHARACTER\tnpc = ch->GetQuestNPC();\n\tif (NULL == npc)\n\t\treturn;\n\n'
             '\tDWORD npcVNUM = npc->GetRaceNum();\n'
             '\tif (Mt2009YSetsCubeMaterialInfo(ch, npcVNUM, requestStartIndex, requestCount)) // ' + M2 + ' (cube set materials)\n'
             '\t\treturn;\n'),
]


def check(src):
    ok = True
    texts = {}
    for e in EDITS:
        if e['file'] not in texts:
            texts[e['file']] = open(os.path.join(src, e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
        t = texts[e['file']]
        n = t.count(e['old'])
        if e['marker'] in t:
            print('already: %s %s' % (e['file'], e['marker']))
        elif n != 1:
            print('ANCHOR x%d: %s %s' % (n, e['file'], e['marker']))
            ok = False
        else:
            texts[e['file']] = t.replace(e['old'], e['new'])
    return ok


def main():
    if len(sys.argv) > 1 and not check(sys.argv[1]):
        sys.exit('anchors do not match - edits.json not written')
    for e in EDITS:
        e['new'].encode('latin-1')
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(EDITS))


if __name__ == '__main__':
    main()
