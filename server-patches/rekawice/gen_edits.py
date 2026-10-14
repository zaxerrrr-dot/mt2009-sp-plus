#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/rekawice (MT2009_PLUS_GLOVES_V1, README.md) from the
code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied after server-patches/precyzja; the logic is the
overlay's playerbot_yohara_gear.cpp (Mt2009Glove*, Mt2009GearSocketPoints)."""
import json
import os
import sys

M = 'MT2009_PLUS_GLOVES_V1'
T = 'MT2009_PLUS_WILL_TALISMAN_V1'
J = 'MT2009_PLUS_JADE_BRACELET_V1'


def guard(tag):
    old = ('\tif (Mt2009JadeBraceletType(GetVnum(), bWillTalismanType)) // %s (%s): its Will line\n'
           '\t\treturn false;\n') % (J, tag)
    new = old + ('\tif (Mt2009GloveType(GetVnum(), bWillTalismanType)) // %s (%s): the glove\'s Will line\n'
                 '\t\treturn false;\n') % (M, tag)
    return dict(file='item_attribute.cpp', marker='%s (%s)' % (M, tag), old=old, new=new)


EDITS = [
    # the glove slot (WEAR_GLOVE 26), ARMOR_GLOVE's bonus set (item_attr.glove - read by the db core), the wear cell
    dict(file='../../common/CommonDefines.h', marker=M + ' (define)',
         old='//#define ENABLE_GLOVE_SYSTEM\n',
         new='#define ENABLE_GLOVE_SYSTEM // ' + M + ' (define): Rekawice Sung Ma - WEAR_GLOVE 26, ATTRIBUTE_SET_GLOVE '
             '(item_attr.glove; server-patches/rekawice)\n'),
    dict(file='../../common/item_length.h', marker=M + ' (metin)',
         old='enum EMetinSubTypes\n{\n\tMETIN_NORMAL,\n\tMETIN_GOLD,\n};\n',
         new='enum EMetinSubTypes\n{\n\tMETIN_NORMAL,\n\tMETIN_GOLD,\n'
             '\tMETIN_SUNGMA, // ' + M + ' (metin): Kamien (Mocy) Demonow - a glove\'s stone (the exe\'s number too)\n'
             '};\n'),
    # a Sung Ma stone's socket gives its Will, no item table is looked for its number
    dict(file='item.cpp', marker=M + ' (declare)',
         old='void CItem::ModifyPoints(bool bAdd)\n{\n',
         new='bool Mt2009GearSocketPoints(LPCHARACTER owner, long lSocket, bool bAdd); // ' + M + ' (declare): '
             'playerbot_yohara_gear.cpp\n\nvoid CItem::ModifyPoints(bool bAdd)\n{\n'),
    dict(file='item.cpp', marker=M + ' (socket points)',
         old='\t\t\t\tif ((dwVnum = GetSocket(i)) <= 2)\n\t\t\t\t\tcontinue;\n'
             '\t\t\t\t// MT2009_PLUS_QUIVER_V1 (sockets)',
         new='\t\t\t\tif ((dwVnum = GetSocket(i)) <= 2)\n\t\t\t\t\tcontinue;\n'
             '\t\t\t\tif (Mt2009GearSocketPoints(m_pOwner, (long) dwVnum, bAdd)) // ' + M + ' (socket points): a Kamien Demonow\'s Will\n'
             '\t\t\t\t\tcontinue;\n'
             '\t\t\t\t// MT2009_PLUS_QUIVER_V1 (sockets)'),
    # the glove's Will line: rolled for a new glove, carried by a refine, no 6/7 changer touches it
    dict(file='item_manager.cpp', marker=M + ' (declare)',
         old='void Mt2009WillTalismanCreate(LPITEM item); // ' + T + ' (declare): item_attribute.cpp\n',
         new='void Mt2009WillTalismanCreate(LPITEM item); // ' + T + ' (declare): item_attribute.cpp\n'
             'void Mt2009GloveCreate(LPITEM item); // ' + M + ' (declare): playerbot_yohara_gear.cpp\n'),
    dict(file='item_manager.cpp', marker=M + ' (new)',
         old='\t\tMt2009WillTalismanCreate(item); // ' + T + ' (new): a Talizman Woli\'s standard lines\n',
         new='\t\tMt2009WillTalismanCreate(item); // ' + T + ' (new): a Talizman Woli\'s standard lines\n'
             '\t\tMt2009GloveCreate(item); // ' + M + ' (new): a Sung Ma glove\'s Will line\n'),
    dict(file='item_attribute.cpp', marker=M + ' (declare)',
         old='void CItem::CopyAttributeTo(LPITEM pItem)\n{\n',
         new='bool Mt2009GloveType(DWORD dwVnum, BYTE& bWillType); // ' + M + ' (declare): playerbot_yohara_gear.cpp\n'
             'void Mt2009GloveRefine(LPITEM pOld, LPITEM pNew);\n\n'
             'void CItem::CopyAttributeTo(LPITEM pItem)\n{\n'),
    dict(file='item_attribute.cpp', marker=M + ' (refine)',
         old='\tMt2009WillTalismanRefine(this, pItem); // ' + T + ' (refine)\n',
         new='\tMt2009WillTalismanRefine(this, pItem); // ' + T + ' (refine)\n'
             '\tMt2009GloveRefine(this, pItem); // ' + M + ' (refine)\n'),
    guard('change rare'),
    guard('change rare 2'),
    guard('add rare'),
    guard('add rare 2'),
    # a Kamien Demonow (METIN_SUNGMA) and anything put into a glove: playerbot_yohara_gear.cpp Mt2009GloveUseStone
    dict(file='char_item.cpp', marker=M + ' (stone)',
         old='\t\tcase ITEM_METIN:\n\t\t\t{\n\t\t\t\tLPITEM item2;\n\n'
             '\t\t\t\tif (!IsValidItemPosition(DestCell) || !(item2 = GetItem(DestCell)))\n\t\t\t\t\treturn false;\n',
         new='\t\tcase ITEM_METIN:\n\t\t\t{\n\t\t\t\tLPITEM item2;\n\n'
             '\t\t\t\tif (!IsValidItemPosition(DestCell) || !(item2 = GetItem(DestCell)))\n\t\t\t\t\treturn false;\n\n'
             '\t\t\t\t// ' + M + ' (stone): a Kamien (Mocy) Demonow goes into a glove only, a glove takes nothing else\n'
             '\t\t\t\tif (item->GetSubType() == METIN_SUNGMA || (item2->GetType() == ITEM_ARMOR && item2->GetSubType() == ARMOR_GLOVE))\n'
             '\t\t\t\t{\n'
             '\t\t\t\t\tbool Mt2009GloveUseStone(LPCHARACTER, LPITEM, LPITEM);\n'
             '\t\t\t\t\treturn Mt2009GloveUseStone(this, item, item2);\n'
             '\t\t\t\t}\n'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for e in EDITS:
        assert e['marker'] in e['new'], e['marker']
    if len(sys.argv) > 1:
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1')
            n = text.count(e['old']) + text.count(e['old'].replace('\n', '\r\n'))
            assert e['marker'] in text or n == 1, (e['marker'], n)
        print('anchors ok')
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')


if __name__ == '__main__':
    main()
