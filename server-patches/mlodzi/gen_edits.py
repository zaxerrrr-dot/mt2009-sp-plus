#!/usr/bin/env python3
"""gen_edits.py - writes edits.json (MT2009_PLUS_MLODZI_BOHATEROWIE_V1, README.md). Edit this file, run it again.
Each edit: file (relative to game/src), marker (an edit whose marker is in the file is skipped), old (exactly once),
new (contains the marker)."""
import json
import os

M = 'MT2009_PLUS_MLODZI_BOHATEROWIE_V1'
E = []


def edit(file, tag, old, new):
    marker = '%s (%s)' % (M, tag)
    assert marker in new, tag
    E.append(dict(file=file, marker=marker, old=old, new=new))


# 1) the quests' "mlodzi" module (playerbot_mlodzi.cpp)
edit('questlua.cpp', 'lua',
     '\t\t{ void RegisterShipDefenseFunctionTable(); RegisterShipDefenseFunctionTable(); }\n',
     '\t\t{ void RegisterShipDefenseFunctionTable(); RegisterShipDefenseFunctionTable(); }\n'
     '\t\t// %s (lua): the quests\' "mlodzi" module - Bronie dla Mlodych Bohaterow (playerbot_mlodzi.cpp).\n'
     '\t\t{ void RegisterMlodziFunctionTable(); RegisterMlodziFunctionTable(); }\n' % M)

# 2) nothing used ON a young heroes' weapon: change / add bonus (1-5 and 6/7), soul stones, socket cleaning, refine
#    scrolls, sash skins, the transmutation's cancel ticket ... - an item of another kind dragged onto it; putting a
#    weapon / armour / costume on (the target cell is a worn one) is not refused
edit('char_item.cpp', 'use on',
     'bool CHARACTER::UseItemEx(LPITEM item, TItemPos DestCell)\n{\n',
     'bool CHARACTER::UseItemEx(LPITEM item, TItemPos DestCell)\n{\n'
     '\t// %s (use on): nothing is used on a young heroes\' weapon - no bonus change or addition (1-5, 6/7),\n'
     '\t// no soul stone, no scroll, no skin (playerbot_mlodzi.cpp); a weapon, armour or costume put on is not refused.\n'
     '\tif (item && item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR && item->GetType() != ITEM_COSTUME &&\n'
     '\t\tIsValidItemPosition(DestCell))\n'
     '\t{\n'
     '\t\tbool MlodziRefuseChange(CHARACTER* ch, CItem* item);\n'
     '\t\tLPITEM pkMlodziTarget = GetItem(DestCell);\n'
     '\t\tif (pkMlodziTarget && pkMlodziTarget != item && MlodziRefuseChange(this, pkMlodziTarget))\n'
     '\t\t\treturn false;\n'
     '\t}\n' % M)

# 3) the item's own bonus functions - every path (the switchbot, Seon-Hae, the quests' item.*, the bots) ends here
DECL = '\tbool MlodziIsWeaponVnum(unsigned int vnum);\n'
for sig, first, ret, tag in (
        ('void CItem::ChangeAttribute(const int* aiChangeProb)\n{\n', '\tSetChangingAttr(true);\n', 'return;', 'change'),
        ('void CItem::AddAttribute()\n{\n', '\tstatic const int aiItemAddAttributePercent[ITEM_ATTRIBUTE_MAX_LEVEL] =\n',
         'return;', 'add'),
        ('void CItem::AddAttribute(BYTE bApply, short sValue)\n{\n', '\tif (HasAttr(bApply))\n', 'return;', 'add one'),
        ('bool CItem::ChangeRareAttribute()\n{\n', '\tBYTE bWillTalismanType;\n', 'return false;', 'change rare'),
        ('bool CItem::ChangeRareAttribute2()\n{\n', '\tBYTE bWillTalismanType;\n', 'return false;', 'change rare 2'),
        ('bool CItem::AddRareAttribute()\n{\n', '\tBYTE bWillTalismanType;\n', 'return false;', 'add rare'),
        ('bool CItem::AddRareAttribute2(const int * aiAttrPercentTable)\n{\n', '\tBYTE bWillTalismanType;\n',
         'return false;', 'add rare 2')):
    edit('item_attribute.cpp', tag, sig + first,
         sig + '\t{ // %s (%s): a young heroes\' weapon keeps its bonuses as given\n' % (M, tag) + '\t' + DECL
         + '\t\tif (MlodziIsWeaponVnum(GetVnum()))\n\t\t\t' + ret + '\n\t}\n' + first)

# 4) the sash's absorption: a young heroes' weapon gives a sash no bonuses
edit('char.cpp', 'sash decl',
     'void CHARACTER::AddAcceMaterial(TItemPos tPos, BYTE bPos)\n{\n',
     'bool MlodziRefuseChange(CHARACTER* ch, CItem* item); // %s (sash decl): playerbot_mlodzi.cpp\n'
     'void CHARACTER::AddAcceMaterial(TItemPos tPos, BYTE bPos)\n{\n' % M)
edit('char.cpp', 'sash',
     '\tLPITEM pkItem = GetItem(tPos);\n\tif (!pkItem)\n\t\treturn;\n'
     '\telse if ((pkItem->GetCell() >= INVENTORY_MAX_NUM) || (pkItem->IsEquipped()) || (tPos.IsBeltInventoryPosition()) || (pkItem->IsDragonSoul()))\n'
     '\t\treturn;\n',
     '\tLPITEM pkItem = GetItem(tPos);\n\tif (!pkItem)\n\t\treturn;\n'
     '\telse if ((pkItem->GetCell() >= INVENTORY_MAX_NUM) || (pkItem->IsEquipped()) || (tPos.IsBeltInventoryPosition()) || (pkItem->IsDragonSoul()))\n'
     '\t\treturn;\n'
     '\t// %s (sash): a young heroes\' weapon gives a sash no bonuses (playerbot_mlodzi.cpp)\n'
     '\telse if (m_bAcceAbsorption && MlodziRefuseChange(this, pkItem))\n'
     '\t\treturn;\n' % M)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edits.json'), 'w', newline='\n') as f:
    json.dump(E, f, indent=2)
    f.write('\n')
print('%d edits' % len(E))
