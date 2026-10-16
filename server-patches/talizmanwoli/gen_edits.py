#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/talizmanwoli (MT2009_PLUS_WILL_TALISMAN_V1) from the code
below; the developer's tool (the apply scripts read edits.json only)."""
import json
import os

M = 'MT2009_PLUS_WILL_TALISMAN_V1'
M2 = 'MT2009_PLUS_WILL_TALISMAN_V2'

FUNCS = r'''// MT2009_PLUS_WILL_TALISMAN_V1 (server-patches/talizmanwoli): Talizmany Woli (81000-81009 SILA, 81250-81259 ODP,
// 81300-81309 WIT, 81550-81559 INT) with the two standard bonus lines of the wiki (pl/de "Talizman Woli SILA",
// Owsap's apply_random_table ApplyRandomType10-14): the talisman's Sung Ma Will (common / rare value) and the power of
// a random element (common 1% / rare 2% at +0). They are the 6th/7th bonus slots (ITEM_ATTRIBUTE_RARE_START): a new
// talisman gets each line or not ("z podstawowym bonusem lub bez niego"), a refine carries them at the new level's
// value of the same row and adds a missing one ("receives the missing bonuses on refine"). No 6/7 changer touches them.
static const short s_aiWillTalismanWill[2][10] = { { 1, 1, 3, 5, 7, 9, 11, 14, 17, 21 }, { 2, 3, 4, 6, 8, 10, 12, 16, 19, 24 } };
static const short s_aiWillTalismanElement[2][10] = { { 1, 2, 3, 4, 5, 6, 7, 8, 9, 15 }, { 2, 3, 4, 5, 6, 7, 8, 9, 10, 17 } };

bool Mt2009WillTalismanType(DWORD dwVnum, BYTE& bWillType)
{
	switch (dwVnum - dwVnum % 10)
	{
		case 81000: bWillType = POINT_SUNGMA_STR; return true;
		case 81250: bWillType = POINT_SUNGMA_MOVE; return true;
		case 81300: bWillType = POINT_SUNGMA_HP; return true;
		case 81550: bWillType = POINT_SUNGMA_IMMUNE; return true;
	}
	return false;
}

static int Mt2009WillTalismanPct(const char* c_pszFlag, int iDefault)
{
	// the panel's event flags (0 = the default): will_tal_line_pct - a new talisman's chance of each line,
	// will_tal_rare_pct - the chance of the rare (higher) row of a line
	const int iFlag = quest::CQuestManager::instance().GetEventFlag(c_pszFlag);
	return iFlag > 0 ? MIN(iFlag, 100) : iDefault;
}

static int Mt2009WillTalismanRollRow()
{
	return number(1, 100) <= Mt2009WillTalismanPct("will_tal_rare_pct", 10) ? 1 : 0;
}

static void Mt2009WillTalismanWrite(LPITEM item, int iWillRow, BYTE bElement, int iElementRow)
{
	BYTE bWillType;
	if (!Mt2009WillTalismanType(item->GetVnum(), bWillType))
		return;
	const int iLevel = item->GetVnum() % 10;
	int iSlot = ITEM_ATTRIBUTE_RARE_START;
	if (iWillRow >= 0)
		item->SetForceAttribute(iSlot++, bWillType, s_aiWillTalismanWill[iWillRow][iLevel]);
	if (bElement)
		item->SetForceAttribute(iSlot++, bElement, s_aiWillTalismanElement[iElementRow][iLevel]);
	for (; iSlot < ITEM_ATTRIBUTE_RARE_END; ++iSlot)
		if (item->GetAttributeType(iSlot))
			item->SetForceAttribute(iSlot, 0, 0);
}

// a new talisman (ITEM_MANAGER::CreateItem): each line at will_tal_line_pct (80), the element at random
void Mt2009WillTalismanCreate(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009WillTalismanType(item->GetVnum(), bWillType))
		return;
	const int iLinePct = Mt2009WillTalismanPct("will_tal_line_pct", 80);
	const int iWillRow = number(1, 100) <= iLinePct ? Mt2009WillTalismanRollRow() : -1;
	const BYTE bElement = number(1, 100) <= iLinePct ? (BYTE) (POINT_ENCHANT_ELECT + number(0, 5)) : 0;
	Mt2009WillTalismanWrite(item, iWillRow, bElement, bElement ? Mt2009WillTalismanRollRow() : 0);
}

// a refine (CopyAttributeTo, after the attributes are copied): the lines of the old talisman at the new level, the
// row each had (its value against the old level's rare value), a missing line added
static void Mt2009WillTalismanRefine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	if (!pOld || !pNew || !Mt2009WillTalismanType(pOld->GetVnum(), bWillType) ||
			!Mt2009WillTalismanType(pNew->GetVnum(), bNewWillType) || bWillType != bNewWillType)
		return;
	const int iOldLevel = pOld->GetVnum() % 10;
	int iWillRow = -1, iElementRow = 0;
	BYTE bElement = 0;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
	{
		const BYTE bType = pOld->GetAttributeType(i);
		const short sValue = pOld->GetAttributeValue(i);
		if (bType == bWillType && iWillRow < 0)
			iWillRow = sValue >= s_aiWillTalismanWill[1][iOldLevel] ? 1 : 0;
		else if (bType >= POINT_ENCHANT_ELECT && bType <= POINT_ENCHANT_DARK && !bElement)
		{
			bElement = bType;
			iElementRow = sValue >= s_aiWillTalismanElement[1][iOldLevel] ? 1 : 0;
		}
	}
	if (iWillRow < 0)
		iWillRow = Mt2009WillTalismanRollRow();
	if (!bElement)
	{
		bElement = (BYTE) (POINT_ENCHANT_ELECT + number(0, 5));
		iElementRow = Mt2009WillTalismanRollRow();
	}
	Mt2009WillTalismanWrite(pNew, iWillRow, bElement, iElementRow);
}

'''

GUARD = '\tif (Mt2009WillTalismanType(GetVnum(), bWillTalismanType)) // MT2009_PLUS_WILL_TALISMAN_V1 (%s): its standard lines\n\t\treturn false;\n'


def guard(tag):
    return '\tBYTE bWillTalismanType;\n' + GUARD % tag


EDITS = [
    dict(file='item_attribute.cpp', marker=M + ' (server-patches/talizmanwoli)',
         old='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n',
         new=FUNCS + 'void CItem::CopyAttributeTo(LPITEM pItem)\n{\n'),
    dict(file='item_attribute.cpp', marker=M + ' (refine)',
         old='\t\tpItem->SetForceAttribute(5, newApply.bType, static_cast<short>(newApply.lValue));\n\t}\n}\n',
         new='\t\tpItem->SetForceAttribute(5, newApply.bType, static_cast<short>(newApply.lValue));\n\t}\n\n'
             '\tMt2009WillTalismanRefine(this, pItem); // ' + M + ' (refine)\n}\n'),
    dict(file='item_attribute.cpp', marker=M + ' (change rare)',
         old='bool CItem::ChangeRareAttribute()\n{\n',
         new='bool CItem::ChangeRareAttribute()\n{\n' + guard('change rare')),
    dict(file='item_attribute.cpp', marker=M + ' (change rare 2)',
         old='bool CItem::ChangeRareAttribute2()\n{\n',
         new='bool CItem::ChangeRareAttribute2()\n{\n' + guard('change rare 2')),
    dict(file='item_attribute.cpp', marker=M + ' (add rare)',
         old='bool CItem::AddRareAttribute()\n{\n',
         new='bool CItem::AddRareAttribute()\n{\n' + guard('add rare')),
    dict(file='item_attribute.cpp', marker=M + ' (add rare 2)',
         old='bool CItem::AddRareAttribute2(const int * aiAttrPercentTable)\n{\n',
         new='bool CItem::AddRareAttribute2(const int * aiAttrPercentTable)\n{\n' + guard('add rare 2')),
    dict(file='item_manager.cpp', marker=M + ' (declare)',
         old='LPITEM ITEM_MANAGER::CreateItem(DWORD vnum, ITEM_COUNT count, DWORD id, bool bTryMagic, int iRarePct, bool bSkipSave, int addRarePct)\n{\n',
         new='void Mt2009WillTalismanCreate(LPITEM item); // ' + M + ' (declare): item_attribute.cpp\n\n'
             'LPITEM ITEM_MANAGER::CreateItem(DWORD vnum, ITEM_COUNT count, DWORD id, bool bTryMagic, int iRarePct, bool bSkipSave, int addRarePct)\n{\n'),
    dict(file='item_manager.cpp', marker=M + ' (new)',
         old='\t\t\t\titem->SetForceAttribute(5, randomPoint, apply.lValue); // ustawiamy jako 6 bonus\n\t\t}\n',
         new='\t\t\t\titem->SetForceAttribute(5, randomPoint, apply.lValue); // ustawiamy jako 6 bonus\n\t\t}\n\n'
             '\t\tMt2009WillTalismanCreate(item); // ' + M + ' (new): a Talizman Woli\'s standard lines\n'),
    # MT2009_PLUS_WILL_TALISMAN_V2 (bug list 15.10 #9): the Will line is the talisman's base bonus and is always
    # there (owner: a Talizman Woli INT from Skrzynia Labiryntowa had only "Sila Mroku +1%"); the element line keeps
    # will_tal_line_pct, the Will's row keeps will_tal_rare_pct. A new edit - V1's marker is on the trees already.
    dict(file='item_attribute.cpp', marker=M2 + ' (will always)',
         old='\tconst int iWillRow = number(1, 100) <= iLinePct ? Mt2009WillTalismanRollRow() : -1;\n',
         new='\tconst int iWillRow = Mt2009WillTalismanRollRow(); // ' + M2 + ' (will always): the base bonus, every talisman\n'),
]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(EDITS, f, ensure_ascii=False, indent=1)
    f.write('\n')
