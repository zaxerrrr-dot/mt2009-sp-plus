#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/bonusy67c (MT2009_PLUS_BONUS67_SKILL_V1, README.md)
from the code below and tools/bonusy67/bonusy67c_data.py (the points, their order); the developer's tool (the apply
scripts read edits.json only). With a game/src dir it also checks that every edit's code is there exactly once (or its
marker is). Applied AFTER wideattr (the points go above its POINT_WIDE_END line); the logic is the overlay's
playerbot_bonus67.cpp (every declaration below has its definition there)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'bonusy67'))
import bonusy67c_data as D  # noqa: E402

M = 'MT2009_PLUS_BONUS67_SKILL_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


def ascii_pl(text):
    return text.translate(str.maketrans(u'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', u'acelnoszzACELNOSZZ'))


# the points: from 256 up, in bonusy67c_data.py's order (item_attr ENUM of apply.sh the same)
WIDE_END = "\tPOINT_WIDE_END,\t// 256 - the first free number (not a point)\n"
lines = ("\t// " + M + " (points): the 6th/7th bonuses of the wiki round 3 (the owner, 4 November 2026: every\n"
         "\t// missing one but the Lycan's; server-patches/bonusy67c, tools/bonusy67/bonusy67c_data.py, playerbot_bonus67.cpp) -\n"
         "\t// the first two-byte points. The skill lines name the official APPLY_* (Korean skill names); the item tooltip\n"
         "\t// names them in Polish (root/localeinfo_point.py), they reach the client as point changes (wideattr).\n"
         "#define MT2009_PLUS_BONUS67_SKILL\n")
for p in D.POINTS:
    lines += "\t%s,\t// %d %s\n" % (p[1], p[0], ascii_pl(p[4]).replace('%%', '%').replace('%d', 'x'))
add('../../common/length.h', 'points', WIDE_END,
    lines + WIDE_END.replace('256 - the first free number', '%d - the first free number' % D.WIDE_END))

# an item's line changes the point like any other bonus
add('char.cpp', 'point change',
    "\t\tcase POINT_BLEEDING_REDUCE:\n\t\tcase POINT_RESIST_HUMAN:\n",
    "\t\tcase POINT_BLEEDING_REDUCE:\n"
    "\t\t// " + M + " (point change): the 6th/7th bonuses of the wiki round 3 (256-%d)\n" % (D.WIDE_END - 1)
    + "".join("\t\tcase %s:\n" % p[1] for p in D.POINTS)
    + "\t\tcase POINT_RESIST_HUMAN:\n")

# a skill's blow: the armour's "Obrazenia od <umiejetnosc> +x%" before it, the weapon's HP absorption / stun /
# knockback after it (the HP the victim lost)
add('char_skill.cpp', 'skill hit',
    "\t\tif (!pkChrVictim->Damage(m_pkChr, iDam, dt, m_pkSk->dwVnum, bIgnoreDefense) && !pkChrVictim->IsStun() && !pkChrVictim->IsDead()) // @fixme312 IsDead\n",
    "\t\t// " + M + " (skill hit): the 6th/7th lines of one skill (playerbot_bonus67.cpp) - the body armour's\n"
    "\t\t// \"Obrazenia od <umiejetnosc> +x%\" before the blow; the weapon's HP absorption, stun and knockback after it\n"
    "\t\tint Bonus67SkillHitDamage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, unsigned int dwVnum, int iDam);\n"
    "\t\tvoid Bonus67SkillHitAfter(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, unsigned int dwVnum, int iDealt, bool bDead);\n"
    "\t\tiDam = Bonus67SkillHitDamage(m_pkChr, pkChrVictim, m_pkSk->dwVnum, iDam);\n"
    "\t\tconst int iB67HpBefore = (int) pkChrVictim->GetHP();\n"
    "\t\tconst bool bB67Dead = pkChrVictim->Damage(m_pkChr, iDam, dt, m_pkSk->dwVnum, bIgnoreDefense);\n"
    "\t\tBonus67SkillHitAfter(m_pkChr, pkChrVictim, m_pkSk->dwVnum, bB67Dead ? MAX(0, iB67HpBefore) : MAX(0, iB67HpBefore - (int) pkChrVictim->GetHP()), bB67Dead);\n"
    "\t\tif (!bB67Dead && !pkChrVictim->IsStun() && !pkChrVictim->IsDead()) // @fixme312 IsDead\n")

# "Czas trwania <umiejetnosc> +x sek.": after the items' per cent and the party bonus, plain seconds
add('char_skill.cpp', 'duration',
    "\t//sys_log(0, \"XXX SKILL Calc %d Amount %d\", dwVnum, iAmount);\n",
    "\t{ // " + M + " (duration): \"Czas trwania <umiejetnosc> +x sek.\" (playerbot_bonus67.cpp) - plain seconds\n"
    "\t\tint Bonus67SkillDurationSec(LPCHARACTER ch, unsigned int dwVnum);\n"
    "\t\tconst int iB67Sec = Bonus67SkillDurationSec(this, dwVnum);\n"
    "\t\tif (iB67Sec > 0)\n"
    "\t\t{\n"
    "\t\t\tif (iDur > 0)\n"
    "\t\t\t\tiDur += iB67Sec;\n"
    "\t\t\tif (iDur2 > 0)\n"
    "\t\t\t\tiDur2 += iB67Sec;\n"
    "\t\t}\n"
    "\t}\n"
    "\t//sys_log(0, \"XXX SKILL Calc %d Amount %d\", dwVnum, iAmount);\n")

# a skill line rolls only on an item its class can use (a bow: the archer's, a dagger/sword: never the archer's)
add('item_attribute.cpp', 'rare fits',
    "bool CItem::AddRareAttribute()\n",
    "// " + M + " (rare fits): a 6th/7th line of a skill rolls only on an item of the skill's class (a bow: the archer's\n"
    "// skills only, another weapon: never the archer's) - playerbot_bonus67.cpp\n"
    "bool Bonus67RareFits(CItem* item, int iApply);\n"
    "\n"
    "bool CItem::AddRareAttribute()\n")
add('item_attribute.cpp', 'rare fits add',
    "\t\tif (r.dwApplyIndex != 0 && r.bMaxLevelBySet[nAttrSet] > 0 && HasRareAttr(i) != true)\n",
    "\t\tif (r.dwApplyIndex != 0 && r.bMaxLevelBySet[nAttrSet] > 0 && HasRareAttr(i) != true && Bonus67RareFits(this, i)) // " + M + " (rare fits add)\n")
add('item_attribute.cpp', 'rare fits put',
    "\t\tif (r.bMaxLevelBySet[iAttributeSet] && !HasRareAttr(i))\n",
    "\t\tif (r.bMaxLevelBySet[iAttributeSet] && !HasRareAttr(i) && Bonus67RareFits(this, i)) // " + M + " (rare fits put)\n")

# en-wiki "Strong against Half Humans (1~15%) of total value": a player is a "human" too
add('battle.cpp', 'per human',
    "\t\tint point_value = pkAttacker->GetPoint(POINT_ATTBONUS_HUMAN);\n",
    "\t\tint point_value = pkAttacker->GetPoint(POINT_ATTBONUS_HUMAN);\n"
    "\t\t{ // " + M + " (per human): \"+x% of the total\" of the half humans' bonus against a player too (playerbot_bonus67.cpp)\n"
    "\t\t\tint Bonus67PerHuman(LPCHARACTER pkAttacker, int iValue);\n"
    "\t\t\tpoint_value = Bonus67PerHuman(pkAttacker, point_value);\n"
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
