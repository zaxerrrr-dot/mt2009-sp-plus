// MT2009_PLUS_GLOVES_V1 / MT2009_PLUS_PRECISION_V1 / MT2009_PLUS_JADE_BRACELET_V2 - playerbot_yohara_gear.h.
// New file outside the engine's own (the overlay's playerbot_* files build with every game core); the hooks are the
// edits of server-patches/precyzja, rekawice and obreczjadeitu2 (each declares what it calls).
#include "stdafx.h"
#include "playerbot_yohara_gear.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "log.h"

#include <algorithm>
#include <vector>

// The numbers the Yohara exe has (client-patches/exe/Server/common/length.h, item_length.h; UserInterface/
// Mt2009Champion.cpp asserts the same): a mismatch does not build on either side.
static_assert(POINT_PACKET_NUM == 193, "the points packet keeps 193 points (no protocol change)");
static_assert(POINT_SUNGMA_PER_STR == 193 && POINT_SUNGMA_PER_IMMUNE == 196, "POINT_SUNGMA_PER_* 193-196 (exe)");
static_assert(POINT_HIT_PCT == 197 && POINT_MAX_NUM == 198, "POINT_HIT_PCT (Precyzja) 197, POINT_MAX_NUM 198 (exe)");
static_assert(METIN_SUNGMA == 2, "METIN_SUNGMA (Kamien Demonow) is subtype 2 (exe)");
static_assert(WEAR_GLOVE == 26 && ARMOR_GLOVE == 8 && WEARABLE_GLOVE == (1 << 13), "the glove's numbers (exe)");
static_assert(FLY_CONQUEROR_EXP == 30, "FLY_CONQUEROR_EXP is 30 (exe)");

namespace
{
	enum { ITEM_BROKEN_METIN = 28960 };	// char_item.cpp ITEM_BROKEN_METIN_VNUM (Pekniety Kamien)

	int EventPct(const char* c_pszFlag, int iDefault)
	{
		// the panel's event flags (0 = the default)
		const int iFlag = quest::CQuestManager::instance().GetEventFlag(c_pszFlag);
		return iFlag > 0 ? MIN(iFlag, 100) : iDefault;
	}

	int RandomIn(const short* r)
	{
		return number(r[0], r[1]);
	}

	// a line's value carried to a new level: the same place in the new range (its lowest value stays the lowest,
	// its highest the highest)
	int Carry(int iOld, const short* rOld, const short* rNew)
	{
		const int iOldSpan = rOld[1] - rOld[0], iNewSpan = rNew[1] - rNew[0];
		const int iPos = MINMAX(0, iOld - rOld[0], iOldSpan);
		const int iNew = iOldSpan > 0 ? rNew[0] + (iPos * iNewSpan + iOldSpan / 2) / iOldSpan : rNew[0];
		return MINMAX((int) rNew[0], iNew, (int) rNew[1]);
	}

	// ---- Rekawice Sung Ma ---------------------------------------------------------------------------------------
	// pl-wiki "Rekawice Mocy" / "Zwinne Rekawice" / "Pancerne Rekawice" / "Ochronne Rekawice": Wola SungMa of the glove
	// +0 3-7 ... +9 58-63 (Owsap's APPLY_RANDOM 1-4).
	const short s_aGloveWill[10][2] = { { 3, 7 }, { 5, 11 }, { 9, 17 }, { 14, 22 }, { 19, 28 }, { 24, 34 }, { 29, 40 },
			{ 34, 46 }, { 39, 52 }, { 58, 63 } };
	// pl-wiki "Kamien Mocy": a stone's Will +0 1, +1 3, +2 6, +3 9, +4 15 (Owsap's bDefaultValues); a Kamien Mocy
	// Demonow (value5 2) may give twice as much.
	const int s_aiStoneWill[5] = { 1, 3, 6, 9, 15 };

	// ---- Obrecze Jadeitu ----------------------------------------------------------------------------------------
	// pl-wiki "Obrecz Jadeitu Mgly" (and Slonca, Nocy, Dymu): Precyzja and the Will of the jade, +0 .. +9.
	const short s_aJadePrecision[10][2] = { { 1, 2 }, { 2, 3 }, { 3, 4 }, { 4, 5 }, { 5, 6 }, { 6, 7 }, { 7, 8 }, { 8, 10 },
			{ 9, 11 }, { 10, 14 } };
	const short s_aJadeWill[10][2] = { { 1, 2 }, { 3, 4 }, { 5, 6 }, { 7, 8 }, { 9, 10 }, { 11, 12 }, { 13, 14 }, { 15, 17 },
			{ 18, 20 }, { 21, 24 } };
	// the jade in the k-th socket (the wiki's "Verb<bonus>-<socket>-<level>"): what it adds to a line the bracelet has
	const short s_aJadeSocketPrecision[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 }, { 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 },
			{ 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 } };
	const short s_aJadeSocketWill[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 }, { 1, 1, 1, 1, 1, 1, 1, 2, 2, 2 },
			{ 1, 1, 1, 1, 1, 2, 3, 3, 4, 4 } };
}

namespace yohara_gear
{
	int SungmaEffective(const CHARACTER* ch, unsigned char bPoint)
	{
		if (!ch || bPoint < POINT_SUNGMA_STR || bPoint > POINT_SUNGMA_IMMUNE)
			return 0;
		const int iBase = ch->GetPoint(bPoint);
		const int iPct = MAX(-100, (int) ch->GetPoint(POINT_SUNGMA_PER_STR + (bPoint - POINT_SUNGMA_STR)));
		return iBase * (100 + iPct) / 100;
	}

	bool DecodeSungmaSocket(long lSocket, unsigned char& bPoint, int& iValue)
	{
		if (lSocket < SUNGMA_SOCKET_MIN)
			return false;
		const long lApply = (lSocket / 10000) % 1000;
		if (lApply < POINT_SUNGMA_STR || lApply > POINT_SUNGMA_IMMUNE)
			return false;
		bPoint = (unsigned char) lApply;
		iValue = (int) (lSocket % 100);
		return iValue > 0;
	}
}

// ==== the gloves ====================================================================================================

// 23000-23009 Rekawice Mocy (SILA), 23010-23019 Zwinne Rekawice (ODP), 23020-23029 Pancerne Rekawice (WIT),
// 23030-23039 Ochronne Rekawice (INT) - the wiki's Will of each glove.
bool Mt2009GloveType(DWORD dwVnum, BYTE& bWillType)
{
	switch (dwVnum - dwVnum % 10)
	{
		case 23000: bWillType = POINT_SUNGMA_STR; return true;
		case 23010: bWillType = POINT_SUNGMA_MOVE; return true;
		case 23020: bWillType = POINT_SUNGMA_HP; return true;
		case 23030: bWillType = POINT_SUNGMA_IMMUNE; return true;
	}
	return false;
}

static void Mt2009GloveWrite(LPITEM item, int iValue)
{
	BYTE bWillType;
	if (!Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	item->SetForceAttribute(ITEM_ATTRIBUTE_RARE_START, bWillType, (short) iValue);
	for (int i = ITEM_ATTRIBUTE_RARE_START + 1; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		if (item->GetAttributeType(i))
			item->SetForceAttribute(i, 0, 0);
}

// ITEM_MANAGER::CreateItem (a new item): the glove's Will, a random value of its level's range - always there
// (the wiki gives every glove its Will line).
void Mt2009GloveCreate(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	Mt2009GloveWrite(item, RandomIn(s_aGloveWill[item->GetVnum() % 10]));
}

// CItem::CopyAttributeTo (a refine): the Will at the same place of the new level's range; a missing one rolled.
void Mt2009GloveRefine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	if (!pOld || !pNew || !Mt2009GloveType(pOld->GetVnum(), bWillType) || !Mt2009GloveType(pNew->GetVnum(), bNewWillType)
			|| bWillType != bNewWillType)
		return;
	const short* rOld = s_aGloveWill[pOld->GetVnum() % 10];
	const short* rNew = s_aGloveWill[pNew->GetVnum() % 10];
	int iValue = -1;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END && iValue < 0; ++i)
		if (pOld->GetAttributeType(i) == bWillType)
			iValue = Carry(pOld->GetAttributeValue(i), rOld, rNew);
	Mt2009GloveWrite(pNew, iValue >= 0 ? iValue : RandomIn(rNew));
}

// CHARACTER::UseItemEx, ITEM_METIN: a Kamien (Mocy) Demonow (METIN_SUNGMA) - only into a glove - or anything into a
// glove. The engine's own rules for a stone (not into an equipped or traded item, a free socket) and the wiki's: it
// may fail and leave a Pekniety Kamien (glove_stone_pct, default 30 - the official chance of a stone); it gives one
// of the four Wills the glove's other stones do not have; a Kamien Mocy Demonow may give twice the value
// (glove_stone_double_pct, default 30). Returns what UseItemEx returns.
bool Mt2009GloveUseStone(LPCHARACTER ch, LPITEM stone, LPITEM glove)
{
	if (!ch || !stone || !glove)
		return false;
	const bool bSungmaStone = stone->GetType() == ITEM_METIN && stone->GetSubType() == METIN_SUNGMA;
	const bool bGlove = glove->GetType() == ITEM_ARMOR && glove->GetSubType() == ARMOR_GLOVE;
	if (!bSungmaStone)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Do rekawic pasuja tylko Kamienie Demonow.");
		return false;
	}
	if (!bGlove)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Kamien Demonow pasuje tylko do rekawic.");
		return false;
	}
	if (glove->IsExchanging() || glove->IsEquipped())
		return false;

	int iSlot = -1;
	bool aUsed[4] = { false, false, false, false };
	for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
	{
		const long lSocket = glove->GetSocket(i);
		BYTE bPoint;
		int iValue;
		if (yohara_gear::DecodeSungmaSocket(lSocket, bPoint, iValue))
			aUsed[bPoint - POINT_SUNGMA_STR] = true;
		else if (iSlot < 0 && lSocket >= 1 && lSocket <= 2)
			iSlot = i;
	}
	if (iSlot < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "W tych rekawicach nie ma wolnego miejsca na kamien.");
		return false;
	}

	if (number(1, 100) <= EventPct("glove_stone_pct", 30))
	{
		std::vector<int> free;
		for (int i = 0; i < 4; ++i)
			if (!aUsed[i])
				free.push_back(i);
		if (free.empty())
			for (int i = 0; i < 4; ++i)
				free.push_back(i);
		const int iWill = free[number(0, (int) free.size() - 1)];
		const int iLevel = MINMAX(0, (int) stone->GetValue(0), 4);
		const int iKind = MINMAX(1, (int) stone->GetValue(5), 9);
		int iValue = s_aiStoneWill[iLevel];
		if (iKind == 2 && number(1, 100) <= EventPct("glove_stone_double_pct", 30))
		{
			iValue *= 2;
			ch->ChatPacket(CHAT_TYPE_INFO, "Doskonale! Kamien Mocy Demonow dal podwojna wartosc.");
		}
		const long lSocket = (long) (POINT_SUNGMA_STR + iWill) * 10000 + iLevel * 1000 + iKind * 100 + MIN(iValue, 99);
		glove->SetSocket(iSlot, lSocket, true, "SOCKET_SUNGMA");
		ch->ChatPacket(CHAT_TYPE_INFO, "Kamien Demonow osadzony.");
		LogManager::instance().ItemLog(ch, glove, "SOCKET_SUNGMA_SUCCESS", stone->GetName());
	}
	else
	{
		glove->SetSocket(iSlot, ITEM_BROKEN_METIN, true, "SOCKET_SUNGMA");
		ch->ChatPacket(CHAT_TYPE_INFO, "Kamien Demonow pekl przy osadzaniu.");
		LogManager::instance().ItemLog(ch, glove, "SOCKET_SUNGMA_FAIL", stone->GetName());
	}
	stone->SetCount(stone->GetCount() - 1);
	return true;
}

// CItem::ModifyPoints, the socket loop of a weapon or armour: a Sung Ma stone's socket gives its Will (true: done -
// no item table is looked for that number).
bool Mt2009GearSocketPoints(LPCHARACTER owner, long lSocket, bool bAdd)
{
	BYTE bPoint;
	int iValue;
	if (!yohara_gear::DecodeSungmaSocket(lSocket, bPoint, iValue))
		return lSocket >= yohara_gear::SUNGMA_SOCKET_MIN;	// another big number: nothing (never an item table)
	if (owner)
		owner->PointChange(bPoint, bAdd ? iValue : -iValue);
	return true;
}

// ==== the jade bracelets (V2) =======================================================================================

bool Mt2009JadeBraceletType(DWORD dwVnum, BYTE& bWillType);	// server-patches/obreczjadeitu (item_attribute.cpp)

static void Mt2009JadeBraceletV2Write(LPITEM item, int iPrecision, int iWill)
{
	BYTE bWillType;
	if (!Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	int iSlot = ITEM_ATTRIBUTE_RARE_START;
	if (iPrecision > 0)
		item->SetForceAttribute(iSlot++, POINT_HIT_PCT, (short) iPrecision);
	if (iWill > 0)
		item->SetForceAttribute(iSlot++, bWillType, (short) iWill);
	for (; iSlot < ITEM_ATTRIBUTE_RARE_END; ++iSlot)
		if (item->GetAttributeType(iSlot))
			item->SetForceAttribute(iSlot, 0, 0);
}

// ITEM_MANAGER::CreateItem: each line at will_tal_line_pct (80) - "istnieje prawdopodobienstwo, ze nie bedzie
// zadnego z nich" - with a random value of the level's range.
void Mt2009JadeBraceletV2Create(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	const int iLevel = item->GetVnum() % 10;
	const int iLinePct = EventPct("will_tal_line_pct", 80);
	const int iPrecision = number(1, 100) <= iLinePct ? RandomIn(s_aJadePrecision[iLevel]) : 0;
	const int iWill = number(1, 100) <= iLinePct ? RandomIn(s_aJadeWill[iLevel]) : 0;
	Mt2009JadeBraceletV2Write(item, iPrecision, iWill);
}

// CItem::CopyAttributeTo: both lines at the same place of the new level's range (a V1 bracelet's Will - one line,
// its common/rare value - too); a missing line is added, as the Will talismans do.
void Mt2009JadeBraceletV2Refine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	if (!pOld || !pNew || !Mt2009JadeBraceletType(pOld->GetVnum(), bWillType) ||
			!Mt2009JadeBraceletType(pNew->GetVnum(), bNewWillType) || bWillType != bNewWillType)
		return;
	const int iOld = pOld->GetVnum() % 10, iNew = pNew->GetVnum() % 10;
	int iPrecision = 0, iWill = 0;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
	{
		const BYTE bType = pOld->GetAttributeType(i);
		const int iValue = pOld->GetAttributeValue(i);
		if (bType == POINT_HIT_PCT && !iPrecision)
			iPrecision = Carry(iValue, s_aJadePrecision[iOld], s_aJadePrecision[iNew]);
		else if (bType == bWillType && !iWill)
			iWill = Carry(iValue, s_aJadeWill[iOld], s_aJadeWill[iNew]);
	}
	if (!iPrecision)
		iPrecision = RandomIn(s_aJadePrecision[iNew]);
	if (!iWill)
		iWill = RandomIn(s_aJadeWill[iNew]);
	Mt2009JadeBraceletV2Write(pNew, iPrecision, iWill);
}

// CItem::ModifyPoints: the jade in the Diamond's sockets (the engine's accessory sockets, socket 0 = how many are
// filled) adds the wiki's values to the lines the bracelet has - they add up.
void Mt2009JadeBraceletSocketPoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	BYTE bWillType;
	if (!item || !owner || !Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	const int iLevel = item->GetVnum() % 10;
	const int iFilled = MINMAX(0, item->GetAccessorySocketGrade(), (int) yohara_gear::JADE_SOCKET_MAX);
	bool bPrecision = false, bWill = false;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
	{
		if (item->GetAttributeType(i) == POINT_HIT_PCT)
			bPrecision = true;
		else if (item->GetAttributeType(i) == bWillType)
			bWill = true;
	}
	int iPrecision = 0, iWill = 0;
	for (int k = 0; k < iFilled; ++k)
	{
		iPrecision += s_aJadeSocketPrecision[k][iLevel];
		iWill += s_aJadeSocketWill[k][iLevel];
	}
	if (bPrecision && iPrecision)
		owner->PointChange(POINT_HIT_PCT, bAdd ? iPrecision : -iPrecision);
	if (bWill && iWill)
		owner->PointChange(bWillType, bAdd ? iWill : -iWill);
}
