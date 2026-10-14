#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/precyzja (MT2009_PLUS_PRECISION_V1, README.md) from
the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied after server-patches/szczelina (the last
Yohara patch before it) - its anchors are czempion's and zywioly's code."""
import json
import os
import sys

M = 'MT2009_PLUS_PRECISION_V1'

EDITS = [
    # the five new points after POINT_PACKET_NUM: the points packet keeps 193 points (no protocol change), the point
    # change carries them (below), POINT_MAX_NUM 198 = the exe's
    dict(file='../../common/length.h', marker=M + ' (points)',
         old='\tPOINT_PACKET_NUM,\n\tPOINT_MAX_NUM = POINT_PACKET_NUM,\n};\n',
         new='\tPOINT_PACKET_NUM,\n'
             '\t// ' + M + ' (points): the Sung Ma per cent bonuses (GF\'s APPLY_SUNGMA_PER_*, "Wola SungMa +x%") and\n'
             '\t// Precyzja (GF\'s APPLY_HIT_PCT: a Yohara map\'s monsters are missed by a person with less) - an apply is a\n'
             '\t// point here. After POINT_PACKET_NUM: the points packet keeps its 193 points, the point change and\n'
             '\t// champion::SendInfo carry them (the Yohara exe has POINT_MAX_NUM 198 too; server-patches/precyzja).\n'
             '\tPOINT_SUNGMA_PER_STR = POINT_PACKET_NUM,\t// 193\n'
             '\tPOINT_SUNGMA_PER_HP,\t// 194\n'
             '\tPOINT_SUNGMA_PER_MOVE,\t// 195\n'
             '\tPOINT_SUNGMA_PER_IMMUNE,\t// 196\n'
             '\tPOINT_HIT_PCT,\t// 197 Precyzja\n'
             '\tPOINT_MAX_NUM,\t// 198\n'
             '};\n'),
    dict(file='../../common/length.h', marker=M + ' (fly)',
         old='\tFLY_SKILL_FLAME_SPIRIT,\n#ifdef ENABLE_QUIVER_SYSTEM\n\tFLY_QUIVER_ATTACK_NORMAL,\n#endif\n};\n',
         new='\tFLY_SKILL_FLAME_SPIRIT,\n#ifdef ENABLE_QUIVER_SYSTEM\n\tFLY_QUIVER_ATTACK_NORMAL,\n#endif\n'
             '\t// ' + M + ' (fly): champion experience (GF\'s FLY_CONQUEROR_EXP, the orange "ga_piece" - the exe registers\n'
             '\t// it under the same number; an older exe only logs an unknown fly)\n'
             '\tFLY_CONQUEROR_EXP = 30,\n'
             '};\n'),
    dict(file='char.cpp', marker=M + ' (point change)',
         old='\t\tcase POINT_SUNGMA_IMMUNE:\n\t\tcase POINT_RESIST_HUMAN:\n',
         new='\t\tcase POINT_SUNGMA_IMMUNE:\n'
             '\t\tcase POINT_SUNGMA_PER_STR: // ' + M + ' (point change): the Sung Ma per cent bonuses and Precyzja\n'
             '\t\tcase POINT_SUNGMA_PER_HP:\n'
             '\t\tcase POINT_SUNGMA_PER_MOVE:\n'
             '\t\tcase POINT_SUNGMA_PER_IMMUNE:\n'
             '\t\tcase POINT_HIT_PCT:\n'
             '\t\tcase POINT_RESIST_HUMAN:\n'),
    dict(file='char.cpp', marker=M + ' (point packet)',
         old='\tif (GetDesc() && type < POINT_PACKET_NUM) // MT2009_PLUS_ELEMENTS_V1 (no point packet): the element powers stay on the server\n',
         new='\t// ' + M + ' (point packet): POINT_SUNGMA_PER_* and POINT_HIT_PCT (after POINT_PACKET_NUM) go to the client too\n'
             '\tif (GetDesc() && (type < POINT_PACKET_NUM || (type >= POINT_SUNGMA_PER_STR && type < POINT_MAX_NUM))) // MT2009_PLUS_ELEMENTS_V1 (no point packet): the element powers stay on the server\n'),
]

# MT2009_PLUS_PRECISION_SKILL_V1: the passive skill Precyzja (pl-wiki "Precyzja", "Ksiega Precyzji") - SKILL_PRECISION
# 246 (GF's vnum: its client's skilltable row 246, icon hit_attribute), read from Ksiega Precyzji (50325) from champion
# level 1, 0 -> P; its bonus (the wiki's table) is part of POINT_HIT_PCT. Logic: playerbot_champion.cpp
# (PrecisionReadBook, PrecisionSkillBonus); data: linux-port/docker/mariadb/playerbot/precyzja_skill.sql.
S = 'MT2009_PLUS_PRECISION_SKILL_V1'
EDITS += [
    dict(file='../../common/skill_length.h', marker=S + ' (vnum)',
         old='\tSKILL_ILIPUNGU = 183,\t\t// Burza Szponow (Likan - no Lycan here)\n',
         new='\tSKILL_ILIPUNGU = 183,\t\t// Burza Szponow (Likan - no Lycan here)\n'
             '\t// ' + S + ' (vnum): the passive skill Precyzja of every character (GF\'s 246; server-patches/precyzja)\n'
             '\tSKILL_PRECISION = 246,\n'),
    # the book: its own case before the old polymorph-like one (that one sent 50325 to SKILL_RESIST_PENETRATE 142 with
    # the item's value0 1 as the lowest level - the book could never be read)
    dict(file='char_item.cpp', marker=S + ' (book)',
         old='\t\t\t\t\t\t\tcase 50314: case 50315: case 50316:\n'
             '\t\t\t\t\t\t\tcase 50323: case 50324:\n'
             '\t\t\t\t\t\t\tcase 50325: case 50326:\n',
         new='\t\t\t\t\t\t\tcase 50325: // ' + S + ' (book): Ksiega Precyzji - the passive skill Precyzja (playerbot_champion.cpp)\n'
             '\t\t\t\t\t\t\t\t{\n'
             '\t\t\t\t\t\t\t\t\tint PrecisionReadBook(CHARACTER*);\n'
             '\t\t\t\t\t\t\t\t\tif (PrecisionReadBook(this))\n'
             '\t\t\t\t\t\t\t\t\t{\n'
             '#ifdef ENABLE_BOOKS_STACKFIX\n'
             '\t\t\t\t\t\t\t\t\t\titem->SetCount(item->GetCount() - 1);\n'
             '#else\n'
             '\t\t\t\t\t\t\t\t\t\tITEM_MANAGER::instance().RemoveItem(item);\n'
             '#endif\n'
             '\t\t\t\t\t\t\t\t\t}\n'
             '\t\t\t\t\t\t\t\t}\n'
             '\t\t\t\t\t\t\t\tbreak;\n'
             '\n'
             '\t\t\t\t\t\t\tcase 50314: case 50315: case 50316:\n'
             '\t\t\t\t\t\t\tcase 50323: case 50324:\n'
             '\t\t\t\t\t\t\tcase 50326:\n'),
    # a skill reset (scrolls, a new road) keeps it - books, not skill points
    dict(file='char_skill.cpp', marker=S + ' (reset)',
         old='\tfor (DWORD dwNinth = SKILL_FINISH; dwNinth <= SKILL_CHEONUN; ++dwNinth)\n'
             '\t\tvec.emplace_back(dwNinth, m_pSkillLevels[dwNinth]);\n',
         new='\tfor (DWORD dwNinth = SKILL_FINISH; dwNinth <= SKILL_CHEONUN; ++dwNinth)\n'
             '\t\tvec.emplace_back(dwNinth, m_pSkillLevels[dwNinth]);\n'
             '\t// ' + S + ' (reset): Precyzja is kept as well (Ksiega Precyzji only)\n'
             '\tvec.emplace_back(SKILL_PRECISION, m_pSkillLevels[SKILL_PRECISION]);\n'),
    # the bonus: on the cleared points before the items' and affects' Precyzja come on top (a point change - the
    # client gets POINT_HIT_PCT, which is not in the points packet)
    dict(file='char.cpp', marker=S + ' (compute)',
         old='\tSetPoint(POINT_SUNGMA_IMMUNE, GetRealPoint(POINT_SUNGMA_IMMUNE));\n',
         new='\tSetPoint(POINT_SUNGMA_IMMUNE, GetRealPoint(POINT_SUNGMA_IMMUNE));\n'
             '\t// ' + S + ' (compute): the passive skill Precyzja\'s bonus (playerbot_champion.cpp); items add below\n'
             '\tif (IsPC())\n'
             '\t{\n'
             '\t\tint PrecisionSkillBonus(const CHARACTER*);\n'
             '\t\tconst int iPrecisionSkill = PrecisionSkillBonus(this);\n'
             '\t\tif (iPrecisionSkill)\n'
             '\t\t\tPointChange(POINT_HIT_PCT, iPrecisionSkill);\n'
             '\t}\n'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
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
