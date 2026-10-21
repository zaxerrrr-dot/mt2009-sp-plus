#!/usr/bin/env python3
"""gen_edits.py [<game/src>] -- writes edits.json of server-patches/buffi (README.md, MT2009_PLUS_BUFFI_V1: Buffi, the
support shaman of Ameria Project); with a game/src dir it also checks that each edit's code is there exactly once (or
its marker already is)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_BUFFI_V1'
EDITS = []


def edit(file, tag, old, new):
    EDITS.append(dict(file=file, marker='%s (%s)' % (M, tag), old=old, new=new))


# the seals 61025/61026 and the name scroll 61030, after the Monster Cards (their hook's code is the anchor)
edit('char_item.cpp', 'use',
     '\t\t\treturn iMonsterCardUse != 0;\n\t}\n',
     '\t\t\treturn iMonsterCardUse != 0;\n\t}\n'
     '\t// ' + M + ' (use): the Buffi seals 61025/61026 and the name scroll 61030 (playerbot_buffi.cpp)\n'
     '\t{\n'
     '\t\tint BuffiUseItem(LPCHARACTER ch, LPITEM item);\n'
     '\t\tconst int iBuffiUse = BuffiUseItem(this, item);\n'
     '\t\tif (iBuffiUse >= 0)\n'
     '\t\t\treturn iBuffiUse != 0;\n'
     '\t}\n')

# the buffi's skills 164-167 for every class (Ameria's CanLearn): the books 61035-61038 and Kamien Duszy Buffi
edit('char_skill.cpp', 'learnable',
     '\t// MT2009_PLUS_RIPOSTY_V1 (learnable): a riposte / boost grows once its Podrecznik taught it (playerbot_riposty.cpp).\n',
     '\t// ' + M + ' (learnable): the Buffi\'s skills 164-167 for every class, with a path (playerbot_buffi.cpp).\n'
     '\t{\n'
     '\t\tint BuffiLearnable(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = BuffiLearnable(this, dwSkillVnum);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n'
     '\t// MT2009_PLUS_RIPOSTY_V1 (learnable): a riposte / boost grows once its Podrecznik taught it (playerbot_riposty.cpp).\n')

# a skill reset keeps them (books and soul stones, not skill points)
edit('char_skill.cpp', 'reset',
     '\t\t\tvec.emplace_back(dwPassive, m_pSkillLevels[dwPassive]);\n',
     '\t\t\tvec.emplace_back(dwPassive, m_pSkillLevels[dwPassive]);\n'
     '\t// ' + M + ' (reset): the Buffi\'s skills 164-167 are kept (books and Kamien Duszy Buffi, not skill points)\n'
     '\tfor (DWORD dwBuffi = 164; dwBuffi <= 167; ++dwBuffi)\n'
     '\t\tvec.emplace_back(dwBuffi, m_pSkillLevels[dwBuffi]);\n')

# a seal called before brings its buffi back
edit('input_login.cpp', 'login',
     '\t{ void MonsterCardOnLogin(LPCHARACTER); MonsterCardOnLogin(ch); }\n',
     '\t{ void MonsterCardOnLogin(LPCHARACTER); MonsterCardOnLogin(ch); }\n'
     '\t// ' + M + ' (login): a Buffi seal called before brings its buffi back (playerbot_buffi.cpp).\n'
     '\t{ void BuffiOnLogin(LPCHARACTER); BuffiOnLogin(ch); }\n')

# the buffi is an NPC here and a female shaman (type PC, race 3) in the clients - no exe change
edit('char.cpp', 'insert',
     '\tpack.wRaceNum\t= GetRaceNum();\n',
     '\tpack.wRaceNum\t= GetRaceNum();\n'
     '\t// ' + M + ' (insert): a Buffi is shown as a female shaman, type PC and race 3 (playerbot_buffi.cpp)\n'
     '\t{ bool BuffiInsertLook(LPCHARACTER, BYTE&, DWORD&); BuffiInsertLook(this, pack.bType, pack.wRaceNum); }\n')

edit('char.cpp', 'level',
     '\t\tif (false)\n\t\t{\n\t\t\tLPCHARACTER ch = (LPCHARACTER) entity;\n',
     '\t\t// ' + M + ' (level): no level over a Buffi\'s head (playerbot_buffi.cpp)\n'
     '\t\t{ bool BuffiIsShaman(LPCHARACTER); if (BuffiIsShaman(this)) addPacket.dwLevel = 0; }\n\n'
     '\t\tif (false)\n\t\t{\n\t\t\tLPCHARACTER ch = (LPCHARACTER) entity;\n')

# the window's command
edit('cmd.cpp', 'declare',
     'ACMD(do_cardmonster);\t// MT2009_PLUS_MONSTER_CARDS_V1 (declare): Karty Potworow (Autor: Digi Rasta), playerbot_monster_card.h\n',
     'ACMD(do_cardmonster);\t// MT2009_PLUS_MONSTER_CARDS_V1 (declare): Karty Potworow (Autor: Digi Rasta), playerbot_monster_card.h\n'
     'ACMD(do_buffi);\t// ' + M + ' (declare): Buffi, root/uibuffi.py (playerbot_buffi.cpp)\n')
edit('cmd.cpp', 'table',
     '\t{ "cardmonster",\tdo_cardmonster,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_MONSTER_CARDS_V1 (table)\n',
     '\t{ "cardmonster",\tdo_cardmonster,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_MONSTER_CARDS_V1 (table)\n'
     '\t{ "buffi",\tdo_buffi,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// ' + M + ' (table)\n')


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, indent=1, ensure_ascii=False)
        f.write('\n')
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('%s: %s already there' % (e['file'], e['marker']))
            elif text.count(e['old']) != 1:
                print('%s: %s - anchor found %d times' % (e['file'], e['marker'], text.count(e['old'])))
                bad += 1
        print('edits %d, bad anchors %d' % (len(EDITS), bad))
        sys.exit(1 if bad else 0)
    print('edits %d' % len(EDITS))


if __name__ == '__main__':
    main()
