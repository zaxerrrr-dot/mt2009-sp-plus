#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/mikstury (MT2009_PLUS_MIKSTURY_V1, README.md) from
the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied LAST (after skillcolor): the anchors are the patched
tree's lines (the wide-attr WORD points, the Flower Event's use block).

The rule (the owner, 4 November 2026, M1): different bonuses always run together - no group caps and no cross-family
blocks; the same bonus (affect type + point) from the same kind of item is refreshed or replaced by an equal or stronger
one, a weaker one is refused. MiksturyMayRefresh (char_affect.cpp) is that rule for one (type, point); every buff path of
UseItemEx asks it and then adds with override + per point (IsCube), so a new record replaces the old one."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_MIKSTURY_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


T6 = '\t' * 6
T7 = '\t' * 7
T8 = '\t' * 8
T9 = '\t' * 9

# --- char_affect.cpp: the rule, before AddAffect
SIG = ('bool CHARACTER::AddAffect(DWORD dwType, WORD bApplyOn, long lApplyValue, DWORD dwFlag, long lDuration, '
       'long lSPCost, bool bOverride, bool IsCube, DWORD itemVnum) // MT2009_PLUS_WIDE_ATTR_V1\n')
add('char_affect.cpp', 'rule', SIG,
    '// ' + M + ' (rule): one bonus (affect type + point) of a potion, a juice, a water, a dew, an elixir or an\n'
    '// ItemShop buff (server-patches/mikstury/README.md; the owner, 4 November 2026). Nothing of that type and point on:\n'
    '// yes. A stronger one on: no ("Silniejszy efekt..."). The same value on and lasting at least as long as the new one\n'
    '// would: no - the item would be spent for nothing. Otherwise yes: the caller adds with override + per point, so the\n'
    '// new value and time replace the old (a refresh, or an upgrade). Different points / types never meet here.\n'
    'bool MiksturyMayRefresh(LPCHARACTER ch, DWORD dwType, WORD wPoint, long lValue, long lDuration)\n'
    '{\n'
    '\tif (!ch)\n'
    '\t\treturn false;\n'
    '\tconst CAffect* pkAff = ch->FindAffect(dwType, wPoint);\n'
    '\tif (!pkAff)\n'
    '\t\treturn true;\n'
    '\tif (pkAff->lApplyValue > lValue)\n'
    '\t{\n'
    '\t\tch->ChatPacket(CHAT_TYPE_INFO, "Silniejszy efekt tego rodzaju ju\\277 dzia\\263a.");\n'
    '\t\treturn false;\n'
    '\t}\n'
    '\tif (pkAff->lApplyValue == lValue && pkAff->lDuration >= lDuration)\n'
    '\t{\n'
    '\t\tch->ChatPacket(CHAT_TYPE_INFO, "Ten efekt ju\\277 dzia\\263a i potrwa d\\263u\\277ej ni\\277 nowy.");\n'
    '\t\treturn false;\n'
    '\t}\n'
    '\treturn true;\n'
    '}\n'
    '\n' + SIG)

# --- char_item.cpp: its declaration
add('char_item.cpp', 'decl', '#define ENABLE_UNIQUE_ITEM_AUTOSPLIT\n',
    '#define ENABLE_UNIQUE_ITEM_AUTOSPLIT\n'
    '// ' + M + ' (decl): the stacking rule of the buff items (char_affect.cpp)\n'
    'bool MiksturyMayRefresh(LPCHARACTER ch, DWORD dwType, WORD wPoint, long lValue, long lDuration);\n')

# 1. the juices and waters 50801-50820, USE_ABILITY_UP (AFFECT_EXP_BONUS_EURO_FREE per point): was "already activated"
#    whatever the value - now refresh / upgrade (the AddAffect calls below already override per point)
add('char_item.cpp', 'juice',
    T6 + 'case USE_ABILITY_UP:\n'
    + T7 + 'if (FindAffect(affect_type, apply_type))\n'
    + T7 + '{\n'
    + T8 + 'ChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    + T8 + 'return false;\n'
    + T7 + '}\n',
    T6 + 'case USE_ABILITY_UP:\n'
    + T7 + '// ' + M + ' (juice): the same bonus refreshes or upgrades, a weaker one is refused\n'
    + T7 + 'if (!MiksturyMayRefresh(this, affect_type, apply_type, apply_value, apply_duration))\n'
    + T8 + 'return false;\n')

# 2. Woda Sim / Woda Dok (USE_AFFECT on AFFECT_EXP_BONUS_EURO_FREE)
add('char_item.cpp', 'water',
    T7 + 'if (FindAffect(AFFECT_EXP_BONUS_EURO_FREE, item->GetValue(1)))\n'
    + T7 + '{\n'
    + T8 + 'ChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    + T7 + '}\n'
    + T7 + 'else\n'
    + T7 + '{\n'
    + T8 + 'AddAffect(AFFECT_EXP_BONUS_EURO_FREE, item->GetValue(1), item->GetValue(2), 0, item->GetValue(3), 0, false, true, item->GetVnum());\n'
    + T8 + 'item->SetCount(item->GetCount() - 1);\n'
    + T7 + '}\n',
    T7 + '// ' + M + ' (water): refresh / upgrade, override per point\n'
    + T7 + 'if (MiksturyMayRefresh(this, AFFECT_EXP_BONUS_EURO_FREE, item->GetValue(1), item->GetValue(2), item->GetValue(3)))\n'
    + T7 + '{\n'
    + T8 + 'AddAffect(AFFECT_EXP_BONUS_EURO_FREE, item->GetValue(1), item->GetValue(2), 0, item->GetValue(3), 0, true, true, item->GetVnum());\n'
    + T8 + 'item->SetCount(item->GetCount() - 1);\n'
    + T7 + '}\n')

# 3. the generic USE_ABILITY_UP (Zielona / Fioletowa Mikstura, Mikstura Szybkosci, the sushi): a weak speed potion
#    overwrote a strong one, and every stat shared one AFFECT_STR record (Sushi z Lososia took Sushi z Suma off)
add('char_item.cpp', 'speed mov',
    T8 + 'case POINT_MOV_SPEED:\n'
    + T9 + 'AddAffect(AFFECT_MOV_SPEED, POINT_MOV_SPEED, item->GetValue(2), AFF_MOV_SPEED_POTION, item->GetValue(1), 0, true);\n',
    T8 + 'case POINT_MOV_SPEED:\n'
    + T9 + '// ' + M + ' (speed mov): a weaker speed potion no longer overwrites a stronger one\n'
    + T9 + 'if (!MiksturyMayRefresh(this, AFFECT_MOV_SPEED, POINT_MOV_SPEED, item->GetValue(2), item->GetValue(1)))\n'
    + T9 + '\treturn false;\n'
    + T9 + 'AddAffect(AFFECT_MOV_SPEED, POINT_MOV_SPEED, item->GetValue(2), AFF_MOV_SPEED_POTION, item->GetValue(1), 0, true);\n')
add('char_item.cpp', 'speed att',
    T8 + 'case POINT_ATT_SPEED:\n'
    + T9 + 'AddAffect(AFFECT_ATT_SPEED, POINT_ATT_SPEED, item->GetValue(2), AFF_ATT_SPEED_POTION, item->GetValue(1), 0, true);\n',
    T8 + 'case POINT_ATT_SPEED:\n'
    + T9 + '// ' + M + ' (speed att): a weaker attack-speed potion no longer overwrites a stronger one\n'
    + T9 + 'if (!MiksturyMayRefresh(this, AFFECT_ATT_SPEED, POINT_ATT_SPEED, item->GetValue(2), item->GetValue(1)))\n'
    + T9 + '\treturn false;\n'
    + T9 + 'AddAffect(AFFECT_ATT_SPEED, POINT_ATT_SPEED, item->GetValue(2), AFF_ATT_SPEED_POTION, item->GetValue(1), 0, true);\n')
add('char_item.cpp', 'stats',
    T8 + 'case POINT_DEF_GRADE_BONUS:\n'
    + T9 + 'AddAffect(AFFECT_STR, bPoint, item->GetValue(2), 0, item->GetValue(1), 0, true);\n',
    T8 + 'case POINT_DEF_GRADE_BONUS:\n'
    + T8 + 'case POINT_RESIST_MAGIC:\n'
    + T9 + '// ' + M + ' (stats): one record per stat (IsCube), so two different stats run together\n'
    + T9 + 'if (!MiksturyMayRefresh(this, AFFECT_STR, bPoint, item->GetValue(2), item->GetValue(1)))\n'
    + T9 + '\treturn false;\n'
    + T9 + 'AddAffect(AFFECT_STR, bPoint, item->GetValue(2), 0, item->GetValue(1), 0, true, true, item->GetVnum());\n')

# 4. the generic USE_AFFECT (ItemShop potions, Dlon Krytyka / Przebicia, Smoczy Bog, EXP rings, ...): the same (type,
#    point) refreshes / upgrades; the herbal BOOST cross-block goes
add('char_item.cpp', 'use affect',
    T7 + 'else if (FindAffect(item->GetValue(0), item->GetValue(1)))\n'
    + T7 + '{\n'
    + T8 + 'ChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    + T8 + 'return false;\n'
    + T7 + '}\n'
    + '\n'
    + T7 + 'if (bPoint != POINT_NONE && FindAffect(AFFECT_POTION_BOOST, bPoint))\n'
    + T7 + '{\n'
    + T8 + 'ChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    + T8 + 'return false;\n'
    + T7 + '}\n'
    + '\n'
    + T7 + 'if (addAffect)\n'
    + T7 + '{\n'
    + T8 + 'AddAffect(item->GetValue(0), item->GetValue(1), item->GetValue(2), 0, item->GetValue(3), 0, false, false, item->GetVnum());\n',
    T7 + '// ' + M + ' (use affect): the same (type, point) refreshes or upgrades, a weaker one is refused; a herbal\n'
    + T7 + '// potion of the same point no longer blocks it (another affect type - both run)\n'
    + T7 + 'else if (!MiksturyMayRefresh(this, item->GetValue(0), bPoint, item->GetValue(2), item->GetValue(3)))\n'
    + T8 + 'return false;\n'
    + '\n'
    + T7 + 'if (addAffect)\n'
    + T7 + '{\n'
    + T8 + 'AddAffect(item->GetValue(0), item->GetValue(1), item->GetValue(2), 0, item->GetValue(3), 0, true, true, item->GetVnum());\n')

# 5. ITEM_BLEND (the dews 50821-50826, the elixirs 50830-50853): Woda Mong blocked every one of them; the same point
#    refreshes / upgrades (a golden elixir replaces a normal one of its element)
add('char_item.cpp', 'blend',
    '\t\t\t\tif (FindAffect(affect_type, apply_type))\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    '\t\t\t\t}\n'
    '\t\t\t\telse\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tif (FindAffect(AFFECT_EXP_BONUS_EURO_FREE, POINT_RESIST_MAGIC))\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("This effect is already activated."));\n'
    '\t\t\t\t\t}\n'
    '\t\t\t\t\telse\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\tAddAffect(affect_type, apply_type, apply_value, 0, apply_duration, 0, false);\n'
    '\t\t\t\t\t\titem->SetCount(item->GetCount() - 1);\n'
    '\t\t\t\t\t}\n'
    '\t\t\t\t}\n',
    '\t\t\t\t// ' + M + ' (blend): the same point refreshes or upgrades; Woda Mong no longer blocks the dews and elixirs\n'
    '\t\t\t\tif (MiksturyMayRefresh(this, affect_type, apply_type, apply_value, apply_duration))\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tAddAffect(affect_type, apply_type, apply_value, 0, apply_duration, 0, true, true, item->GetVnum());\n'
    '\t\t\t\t\titem->SetCount(item->GetCount() - 1);\n'
    '\t\t\t\t}\n')


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('mikstury: %d edits written' % len(E))
    if len(sys.argv) > 1:
        bad = 0
        texts = {}
        for e in E:
            if e['file'] not in texts:
                texts[e['file']] = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            t = texts[e['file']]
            n = t.count(e['old'])
            if e['marker'] not in t and n != 1:
                print('  %s: %s found %d times' % (e['file'], e['marker'], n))
                bad += 1
        print('mikstury: %d problem(s)' % bad)
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
