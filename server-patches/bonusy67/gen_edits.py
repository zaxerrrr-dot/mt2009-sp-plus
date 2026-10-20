#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/bonusy67 (MT2009_PLUS_BONUS67_V1, README.md) from the
code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied after server-patches/precyzja and rekawice (it
changes their lines); the logic is the overlay's playerbot_bonus67.cpp (playerbot_bonus67.h - every declaration
below has its signature: BYTE is unsigned char, DWORD unsigned int)."""
import json
import os
import sys

M = 'MT2009_PLUS_BONUS67_V1'

# The new points, 198-251, in their order (the numbers the items keep, item_attr's apply ENUM of apply.sh, the
# client's root/localeinfo_point.py, the panel's dbeditor/items.py - all four the same list).
POINTS = [
    'POINT_HIT_BUFF_ENCHANT_FIRE', 'POINT_HIT_BUFF_ENCHANT_ICE', 'POINT_HIT_BUFF_ENCHANT_ELEC',
    'POINT_HIT_BUFF_ENCHANT_WIND', 'POINT_HIT_BUFF_ENCHANT_DARK', 'POINT_HIT_BUFF_ENCHANT_EARTH',
    'POINT_HIT_BUFF_RESIST_FIRE', 'POINT_HIT_BUFF_RESIST_ICE', 'POINT_HIT_BUFF_RESIST_ELEC',
    'POINT_HIT_BUFF_RESIST_WIND', 'POINT_HIT_BUFF_RESIST_DARK', 'POINT_HIT_BUFF_RESIST_EARTH',
    'POINT_ATTBONUS_PER_MONSTER', 'POINT_ATTBONUS_PER_STONE', 'POINT_ATTBONUS_PER_CZ', 'POINT_ATTBONUS_PER_MILGYO',
    'POINT_ATTBONUS_PER_ORC', 'POINT_ATTBONUS_PER_DEVIL', 'POINT_ATTBONUS_PER_INSECT', 'POINT_ATTBONUS_PER_ANIMAL',
    'POINT_ENCHANT_PER_ELECT', 'POINT_ENCHANT_PER_FIRE', 'POINT_ENCHANT_PER_ICE', 'POINT_ENCHANT_PER_WIND',
    'POINT_ENCHANT_PER_EARTH', 'POINT_ENCHANT_PER_DARK',
    'POINT_RESIST_PER_HUMAN', 'POINT_RESIST_PER_MAGIC', 'POINT_RESIST_PER_ELEC', 'POINT_RESIST_PER_FIRE',
    'POINT_RESIST_PER_ICE', 'POINT_RESIST_PER_WIND', 'POINT_RESIST_PER_EARTH', 'POINT_RESIST_PER_DARK',
    'POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE', 'POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE',
    'POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE', 'POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE',
    'POINT_FIRST_ATTRIBUTE_BONUS', 'POINT_SECOND_ATTRIBUTE_BONUS', 'POINT_THIRD_ATTRIBUTE_BONUS',
    'POINT_FOURTH_ATTRIBUTE_BONUS', 'POINT_FIFTH_ATTRIBUTE_BONUS',
    'POINT_GLOVE_FALL_RESIST', 'POINT_GLOVE_LIGHTNING',
    'POINT_GLOVE_COOLDOWN_FINISH', 'POINT_GLOVE_COOLDOWN_ILGWANGPYO', 'POINT_GLOVE_COOLDOWN_PUNGLOEPO',
    'POINT_GLOVE_COOLDOWN_GEOMAGGWI', 'POINT_GLOVE_COOLDOWN_MABEOBAGGWI', 'POINT_GLOVE_COOLDOWN_METEO',
    'POINT_GLOVE_COOLDOWN_CHEONUN', 'POINT_GLOVE_COOLDOWN_ILIPUNGU',
    'POINT_GLOVE_BASE_ATTR_PCT',
]
FIRST = 198
assert len(POINTS) == 54 and FIRST + len(POINTS) == 252

COMMENTS = {
    'POINT_HIT_BUFF_ENCHANT_FIRE': 'a blow dealt: the element power for x s',
    'POINT_HIT_BUFF_RESIST_FIRE': 'a blow taken: the element resistance for x s',
    'POINT_ATTBONUS_PER_MONSTER': '+x% of the whole bonus',
    'POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE': 'against / from a boss',
    'POINT_FIRST_ATTRIBUTE_BONUS': "the item's 1st..5th normal bonus +x%",
    'POINT_GLOVE_FALL_RESIST': 'the gloves (Yohara): fall resistance in combat, x% (60 s)',
    'POINT_GLOVE_LIGHTNING': 'lightning on the monsters around (15 s)',
    'POINT_GLOVE_COOLDOWN_FINISH': 'x%: the next cooldown 5 s shorter (SKILL_FINISH .. SKILL_ILIPUNGU)',
    'POINT_GLOVE_BASE_ATTR_PCT': "the glove's built-in Will line +x%",
}


def points_block():
    lines = []
    for i, name in enumerate(POINTS):
        c = COMMENTS.get(name)
        lines.append('\t%s,\t// %d%s\n' % (name, FIRST + i, (' ' + c) if c else ''))
    return ''.join(lines)


def glove_guard(tag, mode, table):
    old = ('\tif (Mt2009GloveType(GetVnum(), bWillTalismanType)) // MT2009_PLUS_GLOVES_V1 (%s): the glove\'s Will line\n'
           '\t\treturn false;\n') % tag
    new = ('\t{ // %s (%s): a glove takes its 7th line from the pool (its 6th is its Will line)\n'
           '\t\tint Bonus67GloveRare(LPITEM item, int iMode, const int* aiPct);\n'
           '\t\tconst int iGlove = Bonus67GloveRare(this, %d, %s);\n'
           '\t\tif (iGlove >= 0)\n'
           '\t\t\treturn iGlove > 0;\n'
           '\t}\n') % (M, tag, mode, table) + old
    return dict(file='item_attribute.cpp', marker='%s (%s)' % (M, tag), old=old, new=new)


CASES = ''.join('\t\tcase %s:\n' % p for p in POINTS)

EDITS = [
    # the points 198-251 (POINT_MAX_NUM 252: an item keeps the type in one byte)
    dict(file='../../common/length.h', marker=M + ' (points)',
         old='\tPOINT_HIT_PCT,\t// 197 Precyzja\n\tPOINT_MAX_NUM,\t// 198\n};\n',
         new='\tPOINT_HIT_PCT,\t// 197 Precyzja\n'
             '\t// ' + M + ' (points): the 6th/7th bonuses of the wiki the engine lacked (server-patches/bonusy67,\n'
             '\t// playerbot_bonus67.cpp) - server-only like the element powers: never in a point packet (the Yohara exe\n'
             '\t// has POINT_MAX_NUM 198), the item tooltip names them (root/localeinfo_point.py).\n'
             + points_block() +
             '\tPOINT_MAX_NUM,\t// 252 (an item keeps its bonus type in one byte: at most 256)\n};\n'),
    # an item's or affect's line changes the point like any other bonus
    dict(file='char.cpp', marker=M + ' (point change)',
         old='\t\tcase POINT_HIT_PCT:\n\t\tcase POINT_RESIST_HUMAN:\n',
         new='\t\tcase POINT_HIT_PCT:\n'
             '\t\t// ' + M + ' (point change): the 6th/7th bonuses of the wiki (198-251)\n' + CASES +
             '\t\tcase POINT_RESIST_HUMAN:\n'),
    # none of them goes to the client (the exe's points end at 197)
    dict(file='char.cpp', marker=M + ' (point packet)',
         old='if (GetDesc() && (type < POINT_PACKET_NUM || (type >= POINT_SUNGMA_PER_STR && type < POINT_MAX_NUM)))',
         new='if (GetDesc() && (type < POINT_PACKET_NUM || (type >= POINT_SUNGMA_PER_STR && type <= POINT_HIT_PCT))) /* '
             + M + ' (point packet): 198-251 stay on the server */'),
    # a resistance: its hit buff and its "+x% of the total" line
    dict(file='char.cpp', marker=M + ' (resist)',
         old='\tif (GetPoint(idx) <= 0)\n\t\treturn GetPoint(idx);\n\n\tint value = MAX(GetPoint(idx) - break_resist_value, 0);\n',
         new='\t// ' + M + ' (resist): the hit buff and the "+x% of the total" line of a resistance (playerbot_bonus67.cpp)\n'
             '\tint Bonus67Total(const CHARACTER* ch, unsigned char bPoint);\n'
             '\tconst int iResistTotal = Bonus67Total(this, idx);\n'
             '\tif (iResistTotal <= 0)\n\t\treturn iResistTotal;\n\n'
             '\tint value = MAX(iResistTotal - break_resist_value, 0);\n'),
    # the race bonuses against a monster: their "+x% of the total" lines
    dict(file='battle.cpp', marker=M + ' (att bonus)',
         old='\t\tiAtk += (iAtk * point_value) / 100;\n',
         new='\t\t{ // ' + M + ' (att bonus): the "+x% of the total" lines of these bonuses (playerbot_bonus67.cpp)\n'
             '\t\t\tint Bonus67AttBonus(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, int iPointValue);\n'
             '\t\t\tpoint_value = Bonus67AttBonus(pkAttacker, pkVictim, point_value);\n'
             '\t\t}\n'
             '\t\tiAtk += (iAtk * point_value) / 100;\n'),
    # the boss lines; the hit buffs, the gloves' fall resistance and lightning start here
    dict(file='char_battle.cpp', marker=M + ' (damage)',
         old='\tif (pAttacker && IsNPC() && (IsStone() || GetMobRank() >= MOB_RANK_BOSS && !IsStone() || IsMiniBoss(GetRaceNum())))\n',
         new='\tif (pAttacker) // ' + M + ' (damage): the boss lines, the hit buffs, the gloves (playerbot_bonus67.cpp)\n'
             '\t{\n'
             '\t\tint Bonus67Damage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iType, int iDam);\n'
             '\t\tdam = Bonus67Damage(this, pAttacker, (int) type, dam);\n'
             '\t}\n\n'
             '\tif (pAttacker && IsNPC() && (IsStone() || GetMobRank() >= MOB_RANK_BOSS && !IsStone() || IsMiniBoss(GetRaceNum())))\n'),
    dict(file='char_battle.cpp', marker=M + ' (push)',
         old='bool CHARACTER::IsResistPush()\n{\n',
         new='bool CHARACTER::IsResistPush()\n{\n'
             '\t{ // ' + M + ' (push): the gloves\' fall resistance in combat (playerbot_bonus67.cpp)\n'
             '\t\tbool Bonus67FallResist(const CHARACTER* ch);\n'
             '\t\tif (Bonus67FallResist(this))\n\t\t\treturn true;\n'
             '\t}\n'),
    # the gloves' 5 s shorter next cooldown of a champion skill
    dict(file='char_skill.cpp', marker=M + ' (cooldown)',
         old='\t// anti cheat fix error\n\tif (HasPlayerData() && dwVnum == SKILL_HORSE_WILDATTACK)\n',
         new='\tif (false == m_bDisableCooltime) // ' + M + ' (cooldown): the gloves\' line of a champion skill\n'
             '\t{\n'
             '\t\tunsigned int Bonus67SkillCooldown(LPCHARACTER ch, unsigned int dwVnum, unsigned int dwNextUsable);\n'
             '\t\tm_SkillUseInfo[dwVnum].dwNextSkillUsableTime = Bonus67SkillCooldown(this, dwVnum, m_SkillUseInfo[dwVnum].dwNextSkillUsableTime);\n'
             '\t}\n\n'
             '\t// anti cheat fix error\n\tif (HasPlayerData() && dwVnum == SKILL_HORSE_WILDATTACK)\n'),
    # an attribute as worn: FIRST..FIFTH_ATTRIBUTE_BONUS of the item, the glove's Will line +x%
    dict(file='item.cpp', marker=M + ' (attr value)',
         old='\t\t\t\tif (m_pOwner->IsUtilityPoint(ia.bType))\n\t\t\t\t\tcontinue;\n\n'
             '\t\t\t\tm_pOwner->PointChange(ia.bType, bAdd ? value : -value);\n',
         new='\t\t\t\tif (m_pOwner->IsUtilityPoint(ia.bType))\n\t\t\t\t\tcontinue;\n\n'
             '\t\t\t\t{ // ' + M + ' (attr value): "1./2./3./4./5. dodany bonus +x%", the glove\'s built-in line +x%\n'
             '\t\t\t\t\tint Bonus67AttrValue(LPITEM item, int iSlot, unsigned char bType, int iValue);\n'
             '\t\t\t\t\tvalue = Bonus67AttrValue(this, i, ia.bType, value);\n'
             '\t\t\t\t}\n'
             '\t\t\t\tm_pOwner->PointChange(ia.bType, bAdd ? value : -value);\n'),
    glove_guard('change rare', 2, 'NULL'),
    glove_guard('change rare 2', 3, 'NULL'),
    glove_guard('add rare', 0, 'NULL'),
    glove_guard('add rare 2', 1, 'aiAttrPercentTable'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(EDITS))
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
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
