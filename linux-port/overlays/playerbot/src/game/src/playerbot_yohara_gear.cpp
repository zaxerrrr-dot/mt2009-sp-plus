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
#include "db.h"

#include <algorithm>
#include <vector>

// The numbers the Yohara exe has (client-patches/exe/Server/common/length.h, item_length.h; UserInterface/
// Mt2009Champion.cpp asserts the same): a mismatch does not build on either side.
static_assert(POINT_PACKET_NUM == 193, "the points packet keeps 193 points (no protocol change)");
static_assert(POINT_SUNGMA_PER_STR == 193 && POINT_SUNGMA_PER_IMMUNE == 196, "POINT_SUNGMA_PER_* 193-196 (exe)");
// MT2009_PLUS_BONUS67_V1 (points): the server's points go on to 251 (the 6th/7th bonuses of the wiki,
// playerbot_bonus67.cpp) - none of them is ever sent as a point, so the exe's POINT_MAX_NUM stays 198.
static_assert(POINT_HIT_PCT == 197 && POINT_HIT_PCT + 1 == POINT_HIT_BUFF_ENCHANT_FIRE, "POINT_HIT_PCT (Precyzja) 197 (exe)");
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

	// ---- Obrecze / Kolie / Klipsy Jadeitu --------------------------------------------------------------------------
	// pl-wiki "Obrecz Jadeitu Mgly" (and Slonca, Nocy, Dymu), "Kolia Jadeitu ...", "Klipsy Jadeitu ...": Precyzja and
	// the Will of the jade, +0 .. +9. MT2009_PLUS_JADE_JEWELLERY_V1: the earrings' pages give their own Will ranges
	// at +1 .. +5 (the necklaces' the bracelets'; Kolia Jadeitu Dymu's page alone the earrings' - taken as its
	// three sisters' and Owsap's one table, ApplyRandomValue6).
	const short s_aJadePrecision[10][2] = { { 1, 2 }, { 2, 3 }, { 3, 4 }, { 4, 5 }, { 5, 6 }, { 6, 7 }, { 7, 8 }, { 8, 10 },
			{ 9, 11 }, { 10, 14 } };
	const short s_aJadeWill[10][2] = { { 1, 2 }, { 3, 4 }, { 5, 6 }, { 7, 8 }, { 9, 10 }, { 11, 12 }, { 13, 14 }, { 15, 17 },
			{ 18, 20 }, { 21, 24 } };
	const short s_aJadeEarWill[10][2] = { { 1, 2 }, { 2, 4 }, { 3, 6 }, { 5, 8 }, { 7, 10 }, { 9, 12 }, { 13, 14 },
			{ 15, 17 }, { 18, 20 }, { 21, 24 } };
	// the jade in the k-th socket (the wiki's "Verb<bonus>-<socket>-<level>"): what it adds to a line the item has
	const short s_aJadeSocketPrecision[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 }, { 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 },
			{ 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 } };
	const short s_aJadeSocketWill[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 }, { 1, 1, 1, 1, 1, 1, 1, 2, 2, 2 },
			{ 1, 1, 1, 1, 1, 2, 3, 3, 4, 4 } };
	// the necklaces and earrings: Precyzja +2 only in the 3rd socket at +9; the earrings' Will +1 in the 1st at +9
	const short s_aJadeNeckEarSocketPrecision[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 },
			{ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 }, { 1, 1, 1, 1, 1, 1, 1, 1, 1, 2 } };
	const short s_aJadeEarSocketWill[3][10] = { { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 }, { 1, 1, 1, 1, 1, 1, 1, 2, 2, 2 },
			{ 1, 1, 1, 1, 1, 2, 3, 3, 4, 4 } };

	// the tables of each kind of jade jewellery (Mt2009JadeBraceletType - server-patches/obreczjadeitu - tells the
	// vnums and the Will; the kind is the armour subtype)
	struct JadeKind
	{
		BYTE bSubType;
		const short (*pWill)[2];
		const short (*pSocketPrecision)[10];
		const short (*pSocketWill)[10];
	};
	const JadeKind s_aJadeKinds[] = {
		{ ARMOR_WRIST, s_aJadeWill, s_aJadeSocketPrecision, s_aJadeSocketWill },
		{ ARMOR_NECK, s_aJadeWill, s_aJadeNeckEarSocketPrecision, s_aJadeSocketWill },
		{ ARMOR_EAR, s_aJadeEarWill, s_aJadeNeckEarSocketPrecision, s_aJadeEarSocketWill },
	};

	const JadeKind* JadeKindOf(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_ARMOR)
			return NULL;
		for (size_t i = 0; i < sizeof(s_aJadeKinds) / sizeof(s_aJadeKinds[0]); ++i)
			if (s_aJadeKinds[i].bSubType == item->GetSubType())
				return &s_aJadeKinds[i];
		return NULL;
	}
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

// MT2009_PLUS_GLOVE_BASE_V1 (the owner, 20 Oct: "Rekawice maja 5 bonusow, ktore mozna dodac standardowo, i 6-7 bonus,
// ktory dodaje sie za odlamki i suplementy"): the glove's Will SungMa is its base attribute ("Atrybuty podstawowe"), no
// longer its 6th bonus - slots 6 and 7 are the 6/7 system's (Seon-Hae, 71051 / 71052: Bonus67GloveRare, the pool's
// glove column). The Will is kept in the item's yextra (server-patches/ysets: player.item_yextra by item id, read when
// the item is loaded): bits 8-15 its value (its kind is the glove's, by the vnum); bits 0-3 (a set) stay 0 on a glove.
// The client hears it by "YITEM" like a serpent piece's base bonuses (the same notify paths) and draws it as the
// glove's own line. POINT_GLOVE_BASE_ATTR_PCT (a 6/7 line of the glove) raises it.
namespace
{
	const DWORD GLOVE_BASE_SHIFT = 8;
	const DWORD GLOVE_BASE_MASK = 0xFF00;

	int GloveBase(LPITEM item)
	{
		return (int) ((item->GetYExtra() & GLOVE_BASE_MASK) >> GLOVE_BASE_SHIFT);
	}

	void GloveBaseSave(LPITEM item)
	{
		if (!item->GetID())
			return;
		if (item->GetYExtra())
			DBManager::instance().DirectQuery("REPLACE INTO item_yextra (id, yextra) VALUES (%u, %u)", item->GetID(), item->GetYExtra());
		else
			DBManager::instance().DirectQuery("DELETE FROM item_yextra WHERE id = %u", item->GetID());
	}

	// the value alone (no points, no save, no client) - a new glove, a loaded one
	void GloveBaseStore(LPITEM item, int iValue)
	{
		item->SetYExtra((item->GetYExtra() & ~GLOVE_BASE_MASK) | ((DWORD) MINMAX(0, iValue, 255) << GLOVE_BASE_SHIFT));
	}

	void GloveBaseNotify(LPITEM item)
	{
		LPCHARACTER ch = item->GetOwner();
		if (ch && (item->GetWindow() == INVENTORY || item->GetWindow() == EQUIPMENT))
			Mt2009YSetsNotify(ch, 1, item->GetCell(), item->GetYExtra());
	}

	// a 6th/7th line of the glove's own Will kind (POINT_SUNGMA_*, flat): the Will as MT2009_PLUS_GLOVES_V1 kept it.
	// The pool's glove column has no such line (Bonus67GloveRare never gives it), so it is always the old Will.
	int GloveLegacySlot(LPITEM item, BYTE bWillType)
	{
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
			if (item->GetAttributeType(i) == bWillType)
				return i;
		return -1;
	}

	// the old Will line out of the bonus slots (the 6/7 lines after it move up); its value, -1 when there was none
	int GloveTakeLegacy(LPITEM item, BYTE bWillType)
	{
		const int iSlot = GloveLegacySlot(item, bWillType);
		if (iSlot < 0)
			return -1;
		const int iValue = item->GetAttributeValue(iSlot);
		int iTo = ITEM_ATTRIBUTE_RARE_START;
		TPlayerItemAttribute aKeep[ITEM_ATTRIBUTE_RARE_NUM];
		memset(aKeep, 0, sizeof(aKeep));
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
			if (item->GetAttributeType(i) && item->GetAttributeType(i) != bWillType)
				aKeep[iTo++ - ITEM_ATTRIBUTE_RARE_START] = item->GetAttribute(i);
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		{
			const TPlayerItemAttribute& a = aKeep[i - ITEM_ATTRIBUTE_RARE_START];
			if (item->GetAttributeType(i) != a.bType || item->GetAttributeValue(i) != a.sValue)
				item->SetForceAttribute(i, a.bType, a.sValue);
		}
		return iValue;
	}

	// The glove's Will from now on: iValue >= 0 sets it, an old 6th/7th Will line (MT2009_PLUS_GLOVES_V1) wins over it
	// and leaves the bonus slots. A worn glove gives the new value at once; saved and told to the client.
	void GloveBaseApply(LPITEM item, BYTE bWillType, int iValue)
	{
		const bool bLegacy = GloveLegacySlot(item, bWillType) >= 0;
		if (!bLegacy && (iValue < 0 || iValue == GloveBase(item)))
			return;
		const bool bWorn = item->IsEquipped() && item->GetOwner();
		if (bWorn)
			item->ModifyPoints(false);
		const int iOld = GloveTakeLegacy(item, bWillType);
		GloveBaseStore(item, iOld > 0 ? iOld : (iValue >= 0 ? iValue : GloveBase(item)));
		if (bWorn)
			item->ModifyPoints(true);
		GloveBaseSave(item);
		GloveBaseNotify(item);
		if (bLegacy)
			sys_log(0, "GLOVE_BASE: glove %u (id %u) - its 6th-slot Will %d is its base attribute now", item->GetVnum(),
					item->GetID(), iOld);
	}

	// "Atrybuty podstawowe rekawic +x%" - the glove's own 6th/7th lines
	int GloveBasePct(LPITEM item)
	{
		int iPct = 0;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
			if (item->GetAttributeType(i) == POINT_GLOVE_BASE_ATTR_PCT)
				iPct += item->GetAttributeValue(i);
		return iPct;
	}
}

// ITEM_MANAGER::CreateItem (a new item): the glove's Will, a random value of its level's range - always there
// (the wiki gives every glove its Will). Saved by Mt2009GloveLoad (it knows whether the item is saved at all).
void Mt2009GloveCreate(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	GloveBaseStore(item, RandomIn(s_aGloveWill[item->GetVnum() % 10]));
}

// MT2009_PLUS_GLOVE_BASE_V1 (load): ITEM_MANAGER::CreateItem, after the ysets' own yextra - a new glove's Will is
// saved, a loaded glove's read back; a loaded glove without one (made again by a system that copies only the sockets
// and the bonuses) gets its level's random value, as a new one.
void Mt2009GloveLoad(LPITEM item, bool bIsNewItem, bool bSkipSave)
{
	Mt2009AccountBoundLoad(item, bIsNewItem);	// MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1 (load): a G0 piece's binding (playerbot_yohara_g0.cpp)
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	if (!bIsNewItem)
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT yextra FROM item_yextra WHERE id = %u", item->GetID()));
		SQLResult* pRes = pMsg ? pMsg->Get() : NULL;
		MYSQL_ROW row = pRes && pRes->uiNumRows > 0 ? mysql_fetch_row(pRes->pSQLResult) : NULL;
		DWORD dwExtra = 0;
		if (row && row[0])
			str_to_number(dwExtra, row[0]);
		item->SetYExtra(dwExtra);
		if (GloveBase(item) > 0)
			return;
		GloveBaseStore(item, RandomIn(s_aGloveWill[item->GetVnum() % 10]));
	}
	if (!bSkipSave)
		GloveBaseSave(item);
}

// MT2009_PLUS_GLOVE_BASE_V1 (after created): CItem::OnAfterCreatedItem (a loaded item with its sockets and bonuses) - a
// glove still holding its Will as the 6th bonus (a copy older than the migration: the mall, a held item) moves it to
// its base attribute.
void Mt2009GloveAfterCreated(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	GloveBaseApply(item, bWillType, -1);
}

// A glove made again from what a system kept of it (Seon-Hae's hold): its Will (the kept yextra) back, an old 6th-slot
// Will moved to it.
void Mt2009GloveRestore(LPITEM item, DWORD dwYExtra)
{
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return;
	const int iKept = (int) ((dwYExtra & GLOVE_BASE_MASK) >> GLOVE_BASE_SHIFT);
	GloveBaseApply(item, bWillType, iKept > 0 ? iKept : -1);
}

// MT2009_PLUS_GLOVE_BASE_V1 (points): CItem::ModifyPoints - the glove's Will, raised by its "Atrybuty podstawowe
// rekawic +x%" lines.
void Mt2009GloveBasePoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	BYTE bWillType;
	int iValue;
	if (!owner || !item || (iValue = Mt2009GloveBaseWill(item, bWillType)) <= 0)
		return;
	owner->PointChange(bWillType, bAdd ? iValue : -iValue);
}

// The glove's Will as worn (its base attribute + "Atrybuty podstawowe rekawic +x%"), 0 for anything else - the points
// and the bots' gear scoring.
int Mt2009GloveBaseWill(LPITEM item, BYTE& bWillType)
{
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return 0;
	const int iBase = GloveBase(item);
	const int iPct = GloveBasePct(item);
	return iPct > 0 ? iBase + iBase * iPct / 100 : iBase;
}

// CItem::CopyAttributeTo (a refine): the Will at the same place of the new level's range (an old 6th-slot Will too);
// the 6/7 lines the engine copied stay; an old Will line copied with them leaves the new glove's bonus slots.
void Mt2009GloveRefine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	if (!pOld || !pNew || !Mt2009GloveType(pOld->GetVnum(), bWillType) || !Mt2009GloveType(pNew->GetVnum(), bNewWillType)
			|| bWillType != bNewWillType)
		return;
	const short* rOld = s_aGloveWill[pOld->GetVnum() % 10];
	const short* rNew = s_aGloveWill[pNew->GetVnum() % 10];
	int iOld = GloveBase(pOld);
	if (iOld <= 0)
	{
		const int iSlot = GloveLegacySlot(pOld, bWillType);
		iOld = iSlot >= 0 ? pOld->GetAttributeValue(iSlot) : 0;
	}
	GloveTakeLegacy(pNew, bWillType);
	GloveBaseStore(pNew, iOld > 0 ? Carry(iOld, rOld, rNew) : RandomIn(rNew));
	GloveBaseSave(pNew);
	GloveBaseNotify(pNew);
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

// ==== the jade bracelets (V2), necklaces and earrings (MT2009_PLUS_JADE_JEWELLERY_V1) ===============================

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

// ITEM_MANAGER::CreateItem: Precyzja at will_tal_line_pct (80), with a random value of the level's range.
// MT2009_PLUS_JADE_BRACELET_V3 (bug list 15.10 #9): the Will of the jade is the item's base bonus and is always there
// (like the gloves' and - MT2009_PLUS_WILL_TALISMAN_V2 - the Will talismans'); before, it too was at 80% and a new
// bracelet / necklace / earrings could come out of a chest, a drop or a shop with no Will.
void Mt2009JadeBraceletV2Create(LPITEM item)
{
	BYTE bWillType;
	const JadeKind* pKind = JadeKindOf(item);
	if (!pKind || !Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	const int iLevel = item->GetVnum() % 10;
	const int iLinePct = EventPct("will_tal_line_pct", 80);
	const int iPrecision = number(1, 100) <= iLinePct ? RandomIn(s_aJadePrecision[iLevel]) : 0;
	const int iWill = RandomIn(pKind->pWill[iLevel]);
	Mt2009JadeBraceletV2Write(item, iPrecision, iWill);
}

// CItem::CopyAttributeTo: both lines at the same place of the new level's range (a V1 bracelet's Will - one line,
// its common/rare value - too); a missing line is added, as the Will talismans do.
void Mt2009JadeBraceletV2Refine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	const JadeKind* pKind = JadeKindOf(pOld);
	if (!pKind || !pNew || !Mt2009JadeBraceletType(pOld->GetVnum(), bWillType) ||
			!Mt2009JadeBraceletType(pNew->GetVnum(), bNewWillType) || bWillType != bNewWillType ||
			JadeKindOf(pNew) != pKind)
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
			iWill = Carry(iValue, pKind->pWill[iOld], pKind->pWill[iNew]);
	}
	if (!iPrecision)
		iPrecision = RandomIn(s_aJadePrecision[iNew]);
	if (!iWill)
		iWill = RandomIn(pKind->pWill[iNew]);
	Mt2009JadeBraceletV2Write(pNew, iPrecision, iWill);
}

// CItem::ModifyPoints: the jade in the Diamond's sockets (the engine's accessory sockets, socket 0 = how many are
// filled) adds the wiki's values (of the item's kind) to the lines the bracelet / necklace / earrings have - they add up.
void Mt2009JadeBraceletSocketPoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	BYTE bWillType;
	const JadeKind* pKind = JadeKindOf(item);
	if (!pKind || !owner || !Mt2009JadeBraceletType(item->GetVnum(), bWillType))
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
		iPrecision += pKind->pSocketPrecision[k][iLevel];
		iWill += pKind->pSocketWill[k][iLevel];
	}
	if (bPrecision && iPrecision)
		owner->PointChange(POINT_HIT_PCT, bAdd ? iPrecision : -iPrecision);
	if (bWill && iWill)
		owner->PointChange(bWillType, bAdd ? iWill : -iWill);
}
