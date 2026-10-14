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
