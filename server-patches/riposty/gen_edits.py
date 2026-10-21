#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/riposty (MT2009_PLUS_RIPOSTY_V1, README.md) from
the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied after server-patches/bonusy67 (the last
patch before it) - its anchors are skill9's and precyzja's code."""
import json
import os
import sys

M = 'MT2009_PLUS_RIPOSTY_V1'
# a riposte or a boost (both vnum ranges) - written out at every hook (no helper in the shared headers)
PASSIVE = ('((%(v)s >= SKILL_ANTI_PALBANG && %(v)s <= SKILL_ANTI_BYEURAK) || '
           '(%(v)s >= SKILL_HELP_PALBANG && %(v)s <= SKILL_HELP_BYEURAK))')


def passive(v):
    return PASSIVE % {'v': v}


EDITS = [
    # GF's vnums (Owsap's skill.h __7AND8TH_SKILLS__; the Lycan's 229 / 244 left out - no Lycan here)
    dict(file='../../common/skill_length.h', marker=M + ' (vnum)',
         old='\tSKILL_PRECISION = 246,\n',
         new='\tSKILL_PRECISION = 246,\n'
             '\t// ' + M + ' (vnum): Riposty (7th) and Dopalacze (8th), the passive skills of every character - GF\'s\n'
             '\t// vnums (server-patches/riposty, playerbot_riposty.cpp); 229 / 244 are the Lycan\'s (no Lycan here)\n'
             '\tSKILL_ANTI_PALBANG = 221,\t// Riposta: Wir Miecza\n'
             '\tSKILL_ANTI_AMSEOP = 222,\t// Riposta: Zasadzka\n'
             '\tSKILL_ANTI_SWAERYUNG = 223,\t// Riposta: Uderzenie Palcem\n'
             '\tSKILL_ANTI_YONGBI = 224,\t// Riposta: Strzelajacy Smok\n'
             '\tSKILL_ANTI_GIGONGCHAM = 225,\t// Riposta: Duchowe Uderzenie\n'
             '\tSKILL_ANTI_HWAJO = 226,\t// Riposta: Ognista Strzala\n'
             '\tSKILL_ANTI_MARYUNG = 227,\t// Riposta: Mroczne Uderzenie\n'
             '\tSKILL_ANTI_BYEURAK = 228,\t// Riposta: Przywolanie Blyskawicy\n'
             '\tSKILL_HELP_PALBANG = 236,\t// Dopalacz: Wir Miecza\n'
             '\tSKILL_HELP_AMSEOP = 237,\t// Dopalacz: Zasadzka\n'
             '\tSKILL_HELP_SWAERYUNG = 238,\t// Dopalacz: Uderzenie Palcem\n'
             '\tSKILL_HELP_YONGBI = 239,\t// Dopalacz: Strzelajacy Smok\n'
             '\tSKILL_HELP_GIGONGCHAM = 240,\t// Dopalacz: Duchowe Uderzenie\n'
             '\tSKILL_HELP_HWAJO = 241,\t// Dopalacz: Ognista Strzala\n'
             '\tSKILL_HELP_MARYUNG = 242,\t// Dopalacz: Mroczne Uderzenie\n'
             '\tSKILL_HELP_BYEURAK = 243,\t// Dopalacz: Przywolanie Blyskawicy\n'),
    # who can grow one: a known riposte, the class's own known boost (level 0: only its Podrecznik, quest riposty)
    dict(file='char_skill.cpp', marker=M + ' (learnable)',
         old='\t// MT2009_PLUS_SKILL9_V1 (learnable): a 9th skill belongs to one class AND specialisation (playerbot_skill9.cpp).\n',
         new='\t// ' + M + ' (learnable): a riposte / boost grows once its Podrecznik taught it (playerbot_riposty.cpp).\n'
             '\t{\n'
             '\t\tint RipostyLearnable(const CHARACTER*, unsigned int);\n'
             '\t\tconst int r = RipostyLearnable(this, dwSkillVnum);\n'
             '\t\tif (r >= 0)\n'
             '\t\t\treturn r != 0;\n'
             '\t}\n'
             '\t// MT2009_PLUS_SKILL9_V1 (learnable): a 9th skill belongs to one class AND specialisation (playerbot_skill9.cpp).\n'),
    # the books: why one cannot be read, in Polish (before the generic "You cannot train this skill.")
    dict(file='char_skill.cpp', marker=M + ' (book check)',
         old='\tif (!IsLearnableSkill(dwSkillVnum))\n'
             '\t{\n'
             '\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill."));\n'
             '\t\treturn false;\n'
             '\t}\n'
             '\n'
             '\t// MT2009_PLUS_SKILL9_V1 (book check)',
         new='\t// ' + M + ' (book check): a riposte\'s / boost\'s book - its Podrecznik first, one riposte, the class\'s boost\n'
             '\t{\n'
             '\t\tint RipostyBookCheck(CHARACTER*, unsigned int);\n'
             '\t\tif (!RipostyBookCheck(this, dwSkillVnum))\n'
             '\t\t\treturn false;\n'
             '\t}\n'
             '\n'
             '\tif (!IsLearnableSkill(dwSkillVnum))\n'
             '\t{\n'
             '\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill."));\n'
             '\t\treturn false;\n'
             '\t}\n'
             '\n'
             '\t// MT2009_PLUS_SKILL9_V1 (book check)'),
    # from 1 to M1 the books work too (the wiki: "nie gwarantuje zwiekszenia poziomu"); Owsap: SKILL_BOOK_TYPE_PASSIVE
    dict(file='char_skill.cpp', marker=M + ' (book grade)',
         old='\tif (pkSk->dwType != 0 && !(dwSkillVnum >= SKILL_FINISH && dwSkillVnum <= SKILL_CHEONUN && GetSkillMasterType(dwSkillVnum) == SKILL_NORMAL))\n',
         new='\t// ' + M + ' (book grade): a riposte\'s / boost\'s books from level 1 to M1 as well (a level a successful read)\n'
             '\tif (pkSk->dwType != 0 && !(dwSkillVnum >= SKILL_FINISH && dwSkillVnum <= SKILL_CHEONUN && GetSkillMasterType(dwSkillVnum) == SKILL_NORMAL)\n'
             '\t\t&& !(' + passive('dwSkillVnum') + ' && GetSkillMasterType(dwSkillVnum) == SKILL_NORMAL))\n'),
    dict(file='char_skill.cpp', marker=M + ' (level up book)',
         old='\t\tif (pkSk->dwType != 0 && !(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN))\n',
         new='\t\t// ' + M + ' (level up book): a riposte / boost goes up by its books below M too\n'
             '\t\tif (pkSk->dwType != 0 && !(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN) &&\n'
             '\t\t\t!' + passive('pkSk->dwVnum') + ')\n'),
    # 17-19: no "use a reset scroll" stop (a reset keeps them) - the classic roll for M up to 20
    dict(file='char_skill.cpp', marker=M + ' (level up stop)',
         old='\t\t!(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN) && // MT2009_PLUS_SKILL9_V1 (level up stop)\n',
         new='\t\t!(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN) && // MT2009_PLUS_SKILL9_V1 (level up stop)\n'
             '\t\t!' + passive('pkSk->dwVnum') + ' && // ' + M + ' (level up stop)\n'),
    dict(file='char_skill.cpp', marker=M + ' (level up roll)',
         old='\t\t\t\tif (pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN)\n'
             '\t\t\t\t{\n'
             '\t\t\t\t\tif (GetSkillLevel(pkSk->dwVnum) >= 17 && number(1, 21 - MIN(20, GetSkillLevel(pkSk->dwVnum))) == 1)\n',
         new='\t\t\t\t// ' + M + ' (level up roll): a riposte / boost as well (the wiki: M1 "gdy osiagnie poziom od 17 do 20")\n'
             '\t\t\t\tif ((pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN) || ' + passive('pkSk->dwVnum') + ')\n'
             '\t\t\t\t{\n'
             '\t\t\t\t\tif (GetSkillLevel(pkSk->dwVnum) >= 17 && number(1, 21 - MIN(20, GetSkillLevel(pkSk->dwVnum))) == 1)\n'),
    # a point into a riposte / boost is remembered (ClearSkill below keeps it spent, Zwoj Zmiany Treningu gives it back)
    dict(file='char_skill.cpp', marker=M + ' (points)',
         old='\t\tPointChange(idx, -1);\n'
             '\t}\n'
             '\n'
             '\tint SkillPointBefore = GetSkillLevel(pkSk->dwVnum);\n',
         new='\t\tPointChange(idx, -1);\n'
             '\t\t// ' + M + ' (points): a riposte\'s / boost\'s point is remembered (a skill reset keeps them spent)\n'
             '\t\t{ void RipostyPointSpent(CHARACTER*, unsigned int); RipostyPointSpent(this, pkSk->dwVnum); }\n'
             '\t}\n'
             '\n'
             '\tint SkillPointBefore = GetSkillLevel(pkSk->dwVnum);\n'),
    # a skill reset (scrolls, a new road) keeps them - the wiki: only Zwoj Zmiany Treningu resets them
    dict(file='char_skill.cpp', marker=M + ' (reset)',
         old='\tvec.emplace_back(SKILL_PRECISION, m_pSkillLevels[SKILL_PRECISION]);\n',
         new='\tvec.emplace_back(SKILL_PRECISION, m_pSkillLevels[SKILL_PRECISION]);\n'
             '\t// ' + M + ' (reset): the riposte and boost are kept too (Zwoj Zmiany Treningu removes them)\n'
             '\tfor (DWORD dwPassive = SKILL_ANTI_PALBANG; dwPassive <= SKILL_HELP_BYEURAK; ++dwPassive)\n'
             '\t\tif (dwPassive <= SKILL_ANTI_BYEURAK || dwPassive >= SKILL_HELP_PALBANG)\n'
             '\t\t\tvec.emplace_back(dwPassive, m_pSkillLevels[dwPassive]);\n'),
    dict(file='char_skill.cpp', marker=M + ' (clear)',
         old='\tPointChange(POINT_SKILL, 4 + (GetLevel() - 5) - GetPoint(POINT_SKILL));\n',
         new='\t// ' + M + ' (clear): the points of the riposte and boost the reset keeps stay spent\n'
             '\t{\n'
             '\t\tint RipostyKeptPoints(CHARACTER*);\n'
             '\t\tPointChange(POINT_SKILL, 4 + (GetLevel() - 5) - RipostyKeptPoints(this) - GetPoint(POINT_SKILL));\n'
             '\t}\n'),
    dict(file='char_skill.cpp', marker=M + ' (level down)',
         old='\tif (dwVnum >= SKILL_FINISH && dwVnum <= SKILL_CHEONUN)\n'
             '\t\treturn false;\n'
             '\n'
             '\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_NORMAL)\n',
         new='\tif (dwVnum >= SKILL_FINISH && dwVnum <= SKILL_CHEONUN)\n'
             '\t\treturn false;\n'
             '\t// ' + M + ' (level down): no point back from a riposte / boost (Zwoj Zmiany Treningu gives them back)\n'
             '\tif ' + passive('dwVnum') + '\n'
             '\t\treturn false;\n'
             '\n'
             '\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_NORMAL)\n'),
    # the effect: the splash damage of an attack skill (where the old 112-119 anti skills sit), before Damage
    dict(file='char_skill.cpp', marker=M + ' (damage)',
         old='\t\tif (m_pkSk->dwVnum == SKILL_FLAME_SPIRIT)\n'
             '\t\t{\n'
             '\t\t\tif (distance > 0)\n',
         new='\t\t// ' + M + ' (damage): the attacker\'s boost of this skill adds, the victim\'s riposte against it takes away\n'
             '\t\t{\n'
             '\t\t\tint RipostyDamage(CHARACTER*, CHARACTER*, unsigned int, int);\n'
             '\t\t\tiDam = RipostyDamage(m_pkChr, pkChrVictim, m_pkSk->dwVnum, iDam);\n'
             '\t\t}\n'
             '\n'
             '\t\tif (m_pkSk->dwVnum == SKILL_FLAME_SPIRIT)\n'
             '\t\t{\n'
             '\t\t\tif (distance > 0)\n'),
    # a new specialisation: a known boost becomes the new one's
    dict(file='char_skill.cpp', marker=M + ' (group)',
         old='\tm_points.skill_group = bSkillGroup;\n'
             '\n'
             '\tTPacketGCChangeSkillGroup p;\n',
         new='\tm_points.skill_group = bSkillGroup;\n'
             '\t// ' + M + ' (group): a known boost moves to the new specialisation\'s (playerbot_riposty.cpp)\n'
             '\t{ void RipostyGroupChanged(CHARACTER*); RipostyGroupChanged(this); }\n'
             '\n'
             '\tTPacketGCChangeSkillGroup p;\n'),
    # the skill window's plus: CanUseSkill is false for a passive skill
    dict(file='cmd_general.cpp', marker=M + ' (skillup)',
         old='\tif (true == ch->CanUseSkill(vnum))\n'
             '\t{\n'
             '\t\tch->SkillLevelUp(vnum);\n'
             '\t}\n',
         new='\t// ' + M + ' (skillup): a riposte / boost takes the class skill points (the skill window\'s plus)\n'
             '\tif ' + passive('vnum') + '\n'
             '\t{\n'
             '\t\tch->SkillLevelUp(vnum);\n'
             '\t\treturn;\n'
             '\t}\n'
             '\n'
             '\tif (true == ch->CanUseSkill(vnum))\n'
             '\t{\n'
             '\t\tch->SkillLevelUp(vnum);\n'
             '\t}\n'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    markers = [e['marker'] for e in EDITS]
    assert len(set(markers)) == len(markers), markers
    for e in EDITS:
        assert e['marker'] in e['new'], e['marker']
    if len(sys.argv) > 1:
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1')
            n = text.count(e['old']) + (text.count(e['old'].replace('\n', '\r\n')) if '\n' in e['old'] else 0)
            assert e['marker'] in text or n == 1, (e['marker'], n)
        print('anchors ok')
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')


if __name__ == '__main__':
    main()
