#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/bonusy67b (MT2009_PLUS_BONUS67_WIKI_V1, README.md)
from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied after antimagic (its anchors are bonusy67's
and antimagic's lines: the last three point numbers 253-255 follow POINT_ANTI_RESIST_MAGIC 252); the logic is the
overlay's playerbot_bonus67.cpp (every declaration below has its signature there)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_BONUS67_WIKI_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


# the last three numbers an item's one-byte bonus type has (POINT_MAX_NUM 256)
add('../../common/length.h', 'points',
    "\tPOINT_ANTI_RESIST_MAGIC,\t// 252\n"
    "\tPOINT_MAX_NUM,\t// 253 (an item keeps its bonus type in one byte: at most 256)\n",
    "\tPOINT_ANTI_RESIST_MAGIC,\t// 252\n"
    "\t// MT2009_PLUS_BONUS67_WIKI_V1 (points): the 6th/7th bonuses of the wiki round 2 (the owner, 3 November 2026;\n"
    "\t// server-patches/bonusy67b, playerbot_bonus67.cpp) - the last three numbers an item's bonus type (one byte) has.\n"
    "\t// Sent to the client as point changes (an exe with POINT_MAX_NUM 256 shows them in the bonus window; an older\n"
    "\t// one drops a type >= its 253 in CPythonPlayer::SetStatus); the item tooltip names them (root/localeinfo_point.py).\n"
    "#define MT2009_PLUS_BONUS67_WIKI\n"
    "\tPOINT_RESIST_COMBAT,\t// 253 \"Jesli masz powyzej 90% PZ, doznajesz obrazenia nizsze o x%\" (body armour)\n"
    "\tPOINT_BLEEDING_PCT,\t// 254 \"Atak krwawienia +x%\" - x% chance a normal hit makes the victim bleed\n"
    "\tPOINT_BLEEDING_REDUCE,\t// 255 \"Odpornosc na atak krwawienia +x%\" - the bleeding's damage x 2% lower\n"
    "\tPOINT_MAX_NUM,\t// 256 (an item keeps its bonus type in one byte: all 256 taken)\n")

# an item's line changes the point like any other bonus
add('char.cpp', 'point change',
    "\t\tcase POINT_GLOVE_BASE_ATTR_PCT:\n\t\tcase POINT_RESIST_HUMAN:\n",
    "\t\tcase POINT_GLOVE_BASE_ATTR_PCT:\n"
    "\t\t// " + M + " (point change): the 6th/7th bonuses of the wiki round 2 (253-255)\n"
    "\t\tcase POINT_RESIST_COMBAT:\n\t\tcase POINT_BLEEDING_PCT:\n\t\tcase POINT_BLEEDING_REDUCE:\n"
    "\t\tcase POINT_RESIST_HUMAN:\n")

# they go to the client (its bonus window, once its exe knows them)
add('char.cpp', 'point packet',
    "type == POINT_ANTI_RESIST_MAGIC /* MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (point packet): 252 to the client (exe POINT_MAX_NUM 253) */",
    "type == POINT_ANTI_RESIST_MAGIC /* MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (point packet): 252 to the client (exe POINT_MAX_NUM 253) */"
    " || type == POINT_RESIST_COMBAT || type == POINT_BLEEDING_PCT || type == POINT_BLEEDING_REDUCE /* " + M
    + " (point packet): 253-255 too (an older exe drops them) */")
add('char.cpp', 'login points',
    "\t\tPOINT_SUNGMA_PER_IMMUNE, POINT_HIT_PCT, POINT_ANTI_RESIST_MAGIC };\n",
    "\t\tPOINT_SUNGMA_PER_IMMUNE, POINT_HIT_PCT, POINT_ANTI_RESIST_MAGIC,\n"
    "\t\tPOINT_RESIST_COMBAT, POINT_BLEEDING_PCT, POINT_BLEEDING_REDUCE }; // " + M + " (login points)\n")

# a normal hit: the bleeding next to the poison
add('battle.cpp', 'bleeding',
    "\tif (pkAttacker->GetPoint(POINT_POISON_PCT) && !pkVictim->IsAffectFlag(AFF_POISON))\n"
    "\t{\n"
    "\t\tif (number(1, 100) <= pkAttacker->GetPoint(POINT_POISON_PCT))\n"
    "\t\t\tpkVictim->AttackedByPoison(pkAttacker);\n"
    "\t}\n",
    "\tif (pkAttacker->GetPoint(POINT_POISON_PCT) && !pkVictim->IsAffectFlag(AFF_POISON))\n"
    "\t{\n"
    "\t\tif (number(1, 100) <= pkAttacker->GetPoint(POINT_POISON_PCT))\n"
    "\t\t\tpkVictim->AttackedByPoison(pkAttacker);\n"
    "\t}\n"
    "\t{ // " + M + " (bleeding): \"Atak krwawienia\" of the 6th/7th bonuses (playerbot_bonus67.cpp)\n"
    "\t\tvoid Bonus67Bleeding(LPCHARACTER pkAttacker, LPCHARACTER pkVictim);\n"
    "\t\tBonus67Bleeding(pkAttacker, pkVictim);\n"
    "\t}\n")

# the wiki: the bleeding stops the HP regeneration (as the poison does)
add('char.cpp', 'regen npc',
    "\t\tif (ch->IsAffectFlag(AFF_POISON))\n"
    "\t\t\treturn PASSES_PER_SEC(MAX(1, ch->GetMobTable().bRegenCycle));\n",
    "\t\tif (ch->IsAffectFlag(AFF_POISON))\n"
    "\t\t\treturn PASSES_PER_SEC(MAX(1, ch->GetMobTable().bRegenCycle));\n"
    "\t\t{ // " + M + " (regen npc): a bleeding monster does not regenerate (playerbot_bonus67.cpp)\n"
    "\t\t\tbool Bonus67IsBleeding(const CHARACTER* ch);\n"
    "\t\t\tif (Bonus67IsBleeding(ch))\n"
    "\t\t\t\treturn PASSES_PER_SEC(MAX(1, ch->GetMobTable().bRegenCycle));\n"
    "\t\t}\n")
add('char.cpp', 'regen pc',
    "\t\tif (ch->IsAffectFlag(AFF_POISON) == true)\n"
    "\t\t{\n"
    "\t\t\treturn 3;\n"
    "\t\t}\n",
    "\t\tif (ch->IsAffectFlag(AFF_POISON) == true)\n"
    "\t\t{\n"
    "\t\t\treturn 3;\n"
    "\t\t}\n"
    "\t\t{ // " + M + " (regen pc): a bleeding character does not regenerate (playerbot_bonus67.cpp)\n"
    "\t\t\tbool Bonus67IsBleeding(const CHARACTER* ch);\n"
    "\t\t\tif (Bonus67IsBleeding(ch))\n"
    "\t\t\t\treturn 3;\n"
    "\t\t}\n")


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(E))
    if len(sys.argv) > 1:
        bad = 0
        for e in E:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('  there:  %s' % e['marker'])
            elif text.count(e['old']) != 1:
                print('  MISSING (%d): %s' % (text.count(e['old']), e['marker']))
                bad += 1
            else:
                print('  ok:     %s' % e['marker'])
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
