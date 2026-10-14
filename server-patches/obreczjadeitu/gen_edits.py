#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/obreczjadeitu (MT2009_PLUS_JADE_BRACELET_V1) from the code
below; the developer's tool (the apply scripts read edits.json only). Applied AFTER server-patches/talizmanwoli: the
edits sit next to its code (its functions, its refine call, its guards, its CreateItem call)."""
import json
import os

M = 'MT2009_PLUS_JADE_BRACELET_V1'
T = 'MT2009_PLUS_WILL_TALISMAN_V1'

FUNCS = r'''// MT2009_PLUS_JADE_BRACELET_V1 (server-patches/obreczjadeitu): Obrecze Jadeitu (14580-14589 Mgly, 14590-14599
// Slonca, 14600-14609 Nocy, 14610-14619 Dymu; the pl-wiki "Obrecz Jadeitu ...", Owsap's APPLY_RANDOM 5 + 6..9 and
// apply_random_table ApplyRandomValue6): the bracelet's Sung Ma Will (Mgly ODP, Slonca INT, Nocy WIT, Dymu SILA),
// common or rare, in the 6th bonus slot (ITEM_ATTRIBUTE_RARE_START) - a new bracelet gets it or not ("istnieje
// prawdopodobienstwo, ze nie bedzie zadnego"), a refine carries it at the new level's value of the same row and adds
// a missing one, no 6/7 changer touches it. The wiki's second line, Precyzja (APPLY_HIT_PCT), has no point in this
// engine. The chances are the Will talismans' panel flags (will_tal_line_pct 80, will_tal_rare_pct 10).
static const short s_aiJadeBraceletWill[2][10] = { { 1, 3, 5, 7, 9, 11, 13, 15, 18, 21 }, { 2, 4, 6, 8, 10, 12, 14, 17, 20, 24 } };

bool Mt2009JadeBraceletType(DWORD dwVnum, BYTE& bWillType)
{
	switch (dwVnum - dwVnum % 10)
	{
		case 14580: bWillType = POINT_SUNGMA_MOVE; return true;
		case 14590: bWillType = POINT_SUNGMA_IMMUNE; return true;
		case 14600: bWillType = POINT_SUNGMA_HP; return true;
		case 14610: bWillType = POINT_SUNGMA_STR; return true;
	}
	return false;
}

static void Mt2009JadeBraceletWrite(LPITEM item, int iWillRow)
{
	BYTE bWillType;
	if (!Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	int iSlot = ITEM_ATTRIBUTE_RARE_START;
	if (iWillRow >= 0)
		item->SetForceAttribute(iSlot++, bWillType, s_aiJadeBraceletWill[iWillRow][item->GetVnum() % 10]);
	for (; iSlot < ITEM_ATTRIBUTE_RARE_END; ++iSlot)
		if (item->GetAttributeType(iSlot))
			item->SetForceAttribute(iSlot, 0, 0);
}

// a new bracelet (ITEM_MANAGER::CreateItem): the line at will_tal_line_pct (80)
void Mt2009JadeBraceletCreate(LPITEM item)
{
	BYTE bWillType;
	if (!item || !Mt2009JadeBraceletType(item->GetVnum(), bWillType))
		return;
	Mt2009JadeBraceletWrite(item, number(1, 100) <= Mt2009WillTalismanPct("will_tal_line_pct", 80) ?
		Mt2009WillTalismanRollRow() : -1);
}

// a refine (CopyAttributeTo, after the attributes are copied): the old bracelet's line at the new level, its row
// (its value against the old level's rare value), a missing line added
static void Mt2009JadeBraceletRefine(LPITEM pOld, LPITEM pNew)
{
	BYTE bWillType, bNewWillType;
	if (!pOld || !pNew || !Mt2009JadeBraceletType(pOld->GetVnum(), bWillType) ||
			!Mt2009JadeBraceletType(pNew->GetVnum(), bNewWillType) || bWillType != bNewWillType)
		return;
	int iWillRow = -1;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END && iWillRow < 0; ++i)
		if (pOld->GetAttributeType(i) == bWillType)
			iWillRow = pOld->GetAttributeValue(i) >= s_aiJadeBraceletWill[1][pOld->GetVnum() % 10] ? 1 : 0;
	if (iWillRow < 0)
		iWillRow = Mt2009WillTalismanRollRow();
	Mt2009JadeBraceletWrite(pNew, iWillRow);
}

'''


def guard(tag):
    old = '\tif (Mt2009WillTalismanType(GetVnum(), bWillTalismanType)) // %s (%s): its standard lines\n\t\treturn false;\n' % (T, tag)
    new = old + ('\tif (Mt2009JadeBraceletType(GetVnum(), bWillTalismanType)) // %s (%s): its Will line\n'
                 '\t\treturn false;\n') % (M, tag)
    return dict(file='item_attribute.cpp', marker='%s (%s)' % (M, tag), old=old, new=new)


EDITS = [
    dict(file='item_attribute.cpp', marker=M + ' (server-patches/obreczjadeitu)',
         old='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n',
         new=FUNCS + 'void CItem::CopyAttributeTo(LPITEM pItem)\n{\n'),
    dict(file='item_attribute.cpp', marker=M + ' (refine)',
         old='\tMt2009WillTalismanRefine(this, pItem); // ' + T + ' (refine)\n',
         new='\tMt2009WillTalismanRefine(this, pItem); // ' + T + ' (refine)\n'
             '\tMt2009JadeBraceletRefine(this, pItem); // ' + M + ' (refine)\n'),
    guard('change rare'),
    guard('change rare 2'),
    guard('add rare'),
    guard('add rare 2'),
    dict(file='item_manager.cpp', marker=M + ' (declare)',
         old='void Mt2009WillTalismanCreate(LPITEM item); // ' + T + ' (declare): item_attribute.cpp\n',
         new='void Mt2009WillTalismanCreate(LPITEM item); // ' + T + ' (declare): item_attribute.cpp\n'
             'void Mt2009JadeBraceletCreate(LPITEM item); // ' + M + ' (declare): item_attribute.cpp\n'),
    dict(file='item_manager.cpp', marker=M + ' (new)',
         old='\t\tMt2009WillTalismanCreate(item); // ' + T + ' (new): a Talizman Woli\'s standard lines\n',
         new='\t\tMt2009WillTalismanCreate(item); // ' + T + ' (new): a Talizman Woli\'s standard lines\n'
             '\t\tMt2009JadeBraceletCreate(item); // ' + M + ' (new): an Obrecz Jadeitu\'s Will line\n'),
]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(EDITS, f, ensure_ascii=False, indent=1)
    f.write('\n')
