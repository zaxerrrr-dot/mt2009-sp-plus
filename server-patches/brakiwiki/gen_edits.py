#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/brakiwiki (MT2009_PLUS_BRAKI_WIKI_V1) from the code below; the
developer's tool (the apply scripts read edits.json only)."""
import json
import os

M = 'MT2009_PLUS_BRAKI_WIKI_V1'

FUNCS = r'''// MT2009_PLUS_BRAKI_WIKI_V1 (server-patches/brakiwiki): Tajemniczy Talizman (81560-81569, the pl-wiki "Tajemniczy
// Talizman" / "Talizmany", Owsap's APPLY_RANDOM 28 / 29 and apply_random_table ApplyRandomValue28 / 29): the talisman's
// two base lines - the Will SungMa of a RANDOM stat (SILA / WIT / ODP / INT; common 1 / rare 2 at +0 .. 21 / 24 at +9)
// and the power of a random element (eleven rows: 1% .. 30% at +0, 9% .. 69% at +9 - "w rzadkich przypadkach 1-30% mocy
// zywiolu w +0"). They are the 6th/7th bonus slots like a Talizman Woli's: a new talisman gets each line or not ("z
// podstawowym bonusem lub bez niego", will_tal_line_pct 80), the higher rows are rare (will_tal_rare_pct 10: the
// Will's rare row; the element's rows 2-11 evenly, row 1 otherwise); a refine carries each line at the new level's value
// of its row, a missing line may come ("moga pojawic sie po podniesieniu", will_tal_line_pct); no 6/7 changer touches
// them.
static const short s_aiMysteryTalismanWill[2][10] = { { 1, 1, 3, 5, 7, 9, 11, 14, 17, 21 }, { 2, 3, 4, 6, 8, 10, 13, 16, 19, 24 } };
static const short s_aiMysteryTalismanElement[11][10] = {
	{ 1, 1, 2, 3, 4, 5, 6, 7, 8, 9 }, { 3, 4, 5, 6, 7, 8, 9, 10, 11, 15 }, { 6, 7, 8, 9, 10, 11, 12, 13, 14, 21 },
	{ 9, 10, 11, 12, 13, 14, 15, 16, 17, 27 }, { 12, 13, 14, 15, 16, 17, 18, 19, 20, 33 },
	{ 15, 16, 17, 18, 19, 20, 21, 22, 23, 39 }, { 18, 19, 20, 21, 22, 23, 24, 25, 26, 45 },
	{ 21, 22, 23, 24, 25, 26, 27, 28, 29, 51 }, { 24, 25, 26, 27, 28, 29, 30, 31, 32, 57 },
	{ 27, 28, 29, 30, 31, 32, 33, 34, 35, 63 }, { 30, 31, 32, 33, 34, 36, 59, 62, 65, 69 } };

bool Mt2009MysteryTalisman(DWORD dwVnum)
{
	return dwVnum >= 81560 && dwVnum <= 81569;
}

static int Mt2009MysteryTalismanElementRow()
{
	return number(1, 100) <= Mt2009WillTalismanPct("will_tal_rare_pct", 10) ? number(1, 10) : 0;
}

static void Mt2009MysteryTalismanWrite(LPITEM item, BYTE bWillType, int iWillRow, BYTE bElement, int iElementRow)
{
	if (!Mt2009MysteryTalisman(item->GetVnum()))
		return;
	const int iLevel = item->GetVnum() % 10;
	int iSlot = ITEM_ATTRIBUTE_RARE_START;
	if (bWillType && iWillRow >= 0)
		item->SetForceAttribute(iSlot++, bWillType, s_aiMysteryTalismanWill[MINMAX(0, iWillRow, 1)][iLevel]);
	if (bElement)
		item->SetForceAttribute(iSlot++, bElement, s_aiMysteryTalismanElement[MINMAX(0, iElementRow, 10)][iLevel]);
	for (; iSlot < ITEM_ATTRIBUTE_RARE_END; ++iSlot)
		if (item->GetAttributeType(iSlot))
			item->SetForceAttribute(iSlot, 0, 0);
}

static BYTE Mt2009MysteryTalismanRandomWill()
{
	static const BYTE s_abWill[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
	return s_abWill[number(0, 3)];
}

// a new talisman (ITEM_MANAGER::CreateItem): each line at will_tal_line_pct (80), the Will's stat and the element at
// random
void Mt2009MysteryTalismanCreate(LPITEM item)
{
	if (!item || !Mt2009MysteryTalisman(item->GetVnum()))
		return;
	const int iLinePct = Mt2009WillTalismanPct("will_tal_line_pct", 80);
	const BYTE bWill = number(1, 100) <= iLinePct ? Mt2009MysteryTalismanRandomWill() : 0;
	const BYTE bElement = number(1, 100) <= iLinePct ? (BYTE) (POINT_ENCHANT_ELECT + number(0, 5)) : 0;
	Mt2009MysteryTalismanWrite(item, bWill, bWill ? Mt2009WillTalismanRollRow() : -1, bElement,
			bElement ? Mt2009MysteryTalismanElementRow() : 0);
}

// a refine (CopyAttributeTo, after the attributes are copied): the old talisman's lines at the new level - the row each
// had (its value against the old level's column) -, a missing line at will_tal_line_pct
static void Mt2009MysteryTalismanRefine(LPITEM pOld, LPITEM pNew)
{
	if (!pOld || !pNew || !Mt2009MysteryTalisman(pOld->GetVnum()) || !Mt2009MysteryTalisman(pNew->GetVnum()))
		return;
	const int iOld = pOld->GetVnum() % 10;
	BYTE bWill = 0, bElement = 0;
	int iWillRow = -1, iElementRow = 0;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
	{
		const int iType = pOld->GetAttributeType(i);
		const short sValue = pOld->GetAttributeValue(i);
		if (!bWill && (iType == POINT_SUNGMA_STR || iType == POINT_SUNGMA_HP || iType == POINT_SUNGMA_MOVE ||
					iType == POINT_SUNGMA_IMMUNE))
		{
			bWill = (BYTE) iType;
			iWillRow = sValue >= s_aiMysteryTalismanWill[1][iOld] ? 1 : 0;
		}
		else if (!bElement && iType >= POINT_ENCHANT_ELECT && iType <= POINT_ENCHANT_DARK)
		{
			bElement = (BYTE) iType;
			for (int r = 10; r >= 0; --r)
				if (sValue >= s_aiMysteryTalismanElement[r][iOld])
				{
					iElementRow = r;
					break;
				}
		}
	}
	const int iLinePct = Mt2009WillTalismanPct("will_tal_line_pct", 80);
	if (!bWill && number(1, 100) <= iLinePct)
	{
		bWill = Mt2009MysteryTalismanRandomWill();
		iWillRow = Mt2009WillTalismanRollRow();
	}
	if (!bElement && number(1, 100) <= iLinePct)
	{
		bElement = (BYTE) (POINT_ENCHANT_ELECT + number(0, 5));
		iElementRow = Mt2009MysteryTalismanElementRow();
	}
	Mt2009MysteryTalismanWrite(pNew, bWill, iWillRow, bElement, iElementRow);
}

'''


def guard(tag):
    old = ('\tif (Mt2009WillTalismanType(GetVnum(), bWillTalismanType)) // MT2009_PLUS_WILL_TALISMAN_V1 (%s): its standard'
           ' lines\n\t\treturn false;\n' % tag)
    return dict(file='item_attribute.cpp', marker='%s (%s)' % (M, tag), old=old,
                new=old + '\tif (Mt2009MysteryTalisman(GetVnum())) // %s (%s): Tajemniczy Talizman\'s base lines\n'
                          '\t\treturn false;\n' % (M, tag))


ARMOR_OLD = ('\t\t\t\tif (pkItem->GetSubType() == ARMOR_BODY || pkItem->GetSubType() == ARMOR_HEAD || '
             'pkItem->GetSubType() == ARMOR_FOOTS || pkItem->GetSubType() == ARMOR_SHIELD)\n')

EDITS = [
    dict(file='item_attribute.cpp', marker=M + ' (server-patches/brakiwiki)',
         old='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n',
         new=FUNCS + 'void CItem::CopyAttributeTo(LPITEM pItem)\n{\n'),
    dict(file='item_attribute.cpp', marker=M + ' (refine)',
         old='\tMt2009WillTalismanRefine(this, pItem); // MT2009_PLUS_WILL_TALISMAN_V1 (refine)\n',
         new='\tMt2009WillTalismanRefine(this, pItem); // MT2009_PLUS_WILL_TALISMAN_V1 (refine)\n'
             '\tMt2009MysteryTalismanRefine(this, pItem); // ' + M + ' (refine): Tajemniczy Talizman\n'),
    guard('change rare'),
    guard('change rare 2'),
    guard('add rare'),
    guard('add rare 2'),
    dict(file='item_manager.cpp', marker=M + ' (declare)',
         old='void Mt2009WillTalismanCreate(LPITEM item); // MT2009_PLUS_WILL_TALISMAN_V1 (declare): item_attribute.cpp\n',
         new='void Mt2009WillTalismanCreate(LPITEM item); // MT2009_PLUS_WILL_TALISMAN_V1 (declare): item_attribute.cpp\n'
             'void Mt2009MysteryTalismanCreate(LPITEM item); // ' + M + ' (declare): item_attribute.cpp\n'),
    dict(file='item_manager.cpp', marker=M + ' (new)',
         old='\t\tMt2009WillTalismanCreate(item); // MT2009_PLUS_WILL_TALISMAN_V1 (new): a Talizman Woli\'s standard lines\n',
         new='\t\tMt2009WillTalismanCreate(item); // MT2009_PLUS_WILL_TALISMAN_V1 (new): a Talizman Woli\'s standard lines\n'
             '\t\tMt2009MysteryTalismanCreate(item); // ' + M + ' (new): Tajemniczy Talizman\'s base lines\n'),
    # Rekawice Weza (23050-23089): the wiki's Obrona (15-17 .. 55-57) - value1 + 2 x value5 like the other armour
    # pieces; the Sung Ma gloves have both at 0 (no change for them)
    dict(file='char.cpp', marker=M + ' (glove armour)',
         old=ARMOR_OLD,
         new='\t\t\t\t// ' + M + ' (glove armour): a glove\'s Obrona too (Rekawice Weza - value1 + 2 x value5)\n'
             '\t\t\t\tif (pkItem->GetSubType() == ARMOR_BODY || pkItem->GetSubType() == ARMOR_HEAD || '
             'pkItem->GetSubType() == ARMOR_FOOTS || pkItem->GetSubType() == ARMOR_SHIELD || '
             'pkItem->GetSubType() == ARMOR_GLOVE)\n'),
]

if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edits.json'), 'w', encoding='utf-8',
              newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits %d' % len(EDITS))
