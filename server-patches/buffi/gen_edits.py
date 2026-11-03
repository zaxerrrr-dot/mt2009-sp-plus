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


# ---------------------------------------------------------------------- MT2009_PLUS_BUFFI_V2: Ameria's four costume
# slots of the buffi (outfit, hairstyle, weapon, sash) - the free wear cells 28-31 under WEAR_MAX 32 (no cell layout,
# packet or database change; the exe's Server/common/length.h has the same numbers, client-patches/exe)
M2 = 'MT2009_PLUS_BUFFI_V2'


def edit2(file, tag, old, new):
    EDITS.append(dict(file=file, marker='%s (%s)' % (M2, tag), old=old, new=new))


edit2('../../common/length.h', 'wear',
      '\tWEAR_MAX = 32\n};',
      '\t// ' + M2 + ' (wear): Buffi\'s costume slots (Ameria\'s WEAR_BUFFI_*; playerbot_buffi.cpp) - fixed numbers, the\n'
      '\t// free cells under WEAR_MAX whatever the costume systems above\n'
      '\tWEAR_BUFFI_BODY = 28,\n'
      '\tWEAR_BUFFI_HEAD = 29,\n'
      '\tWEAR_BUFFI_WEAPON = 30,\n'
      '\tWEAR_BUFFI_SASH = 31,\n'
      '\n'
      '\tWEAR_MAX = 32\n};')

# where a costume goes: onto the buffi when dragged onto its slot or used with the Buffi window open
edit2('item.cpp', 'cell',
      'int CItem::FindEquipCell(LPCHARACTER ch, int iCandidateCell)\n{\n',
      'int CItem::FindEquipCell(LPCHARACTER ch, int iCandidateCell)\n{\n'
      '\t// ' + M2 + ' (cell): a costume for Buffi\'s slots, one worn there (playerbot_buffi.cpp)\n'
      '\t{\n'
      '\t\tint Mt2009BuffiFindEquipCell(LPCHARACTER, CItem*, int);\n'
      '\t\tconst int iBuffiCell = Mt2009BuffiFindEquipCell(ch, this, iCandidateCell);\n'
      '\t\tif (iBuffiCell != -2)\n'
      '\t\t\treturn iBuffiCell;\n'
      '\t}\n')

# a costume on the buffi gives its owner nothing (no bonus, no part of the owner's look)
edit2('item.cpp', 'points',
      'void CItem::ModifyPoints(bool bAdd)\n{\n',
      'void CItem::ModifyPoints(bool bAdd)\n{\n'
      '\t// ' + M2 + ' (points): a costume worn on Buffi gives its owner nothing (playerbot_buffi.cpp)\n'
      '\t{\n'
      '\t\tbool Mt2009BuffiWornItem(CItem*);\n'
      '\t\tif (Mt2009BuffiWornItem(this))\n'
      '\t\t\treturn;\n'
      '\t}\n')

# the cell the client named, for CanEquipNow and the sex check
edit2('char_item.cpp', 'begin',
      'bool CHARACTER::EquipItem(LPITEM item, int iCandidateCell)\n{\n',
      'bool CHARACTER::EquipItem(LPITEM item, int iCandidateCell)\n{\n'
      '\t// ' + M2 + ' (begin): the cell named, for Buffi\'s costume slots (playerbot_buffi.cpp)\n'
      '\t{ void Mt2009BuffiEquipBegin(LPCHARACTER, LPITEM, int); Mt2009BuffiEquipBegin(this, item, iCandidateCell); }\n')

edit2('char_item.cpp', 'swap',
      '\t\tif (false == CanUnequipNow(item2) || false == CanEquipNow(item1))\n\t\t\treturn false;\n\n'
      '\t\tif (bEquipCell != item1->FindEquipCell(this))\n',
      '\t\t// ' + M2 + ' (swap): a costume swapped with one on Buffi\'s slot goes onto that slot (playerbot_buffi.cpp)\n'
      '\t\t{ void Mt2009BuffiEquipBegin(LPCHARACTER, LPITEM, int); Mt2009BuffiEquipBegin(this, item1, bEquipCell); }\n'
      '\t\tif (false == CanUnequipNow(item2) || false == CanEquipNow(item1))\n\t\t\treturn false;\n\n'
      '\t\tif (bEquipCell != item1->FindEquipCell(this, bEquipCell))\n')

# a costume for the buffi: the shaman's class, not the owner's
edit2('char_item.cpp', 'job',
      '\t//BYTE itemSubType = item->GetSubType();\n\n\tswitch (GetJob())\n',
      '\t//BYTE itemSubType = item->GetSubType();\n\n'
      '\t// ' + M2 + ' (job): a costume for Buffi - a shaman\'s, whatever its owner\'s class (playerbot_buffi.cpp)\n'
      '\tint iBuffiEquip = -1;\n'
      '\t{\n'
      '\t\tint Mt2009BuffiCanEquip(LPCHARACTER, LPITEM);\n'
      '\t\tiBuffiEquip = Mt2009BuffiCanEquip(this, item);\n'
      '\t\tif (iBuffiEquip == 0)\n'
      '\t\t\treturn false;\n'
      '\t}\n'
      '\tif (iBuffiEquip < 0)\n'
      '\tswitch (GetJob())\n')

# a costume for the buffi: a woman's
edit2('char_item.cpp', 'sex',
      'static bool FN_check_item_sex(LPCHARACTER ch, LPITEM item)\n{\n',
      'static bool FN_check_item_sex(LPCHARACTER ch, LPITEM item)\n{\n'
      '\t// ' + M2 + ' (sex): a costume for Buffi - a woman\'s (playerbot_buffi.cpp)\n'
      '\t{\n'
      '\t\tint Mt2009BuffiCheckSex(LPCHARACTER, LPITEM);\n'
      '\t\tconst int iBuffiSex = Mt2009BuffiCheckSex(ch, item);\n'
      '\t\tif (iBuffiSex >= 0)\n'
      '\t\t\treturn iBuffiSex != 0;\n'
      '\t}\n')


# MT2009_PLUS_BUFFI_PASS_V1 (the owner, 3 November 2026: "przez Buffi mozna przechodzic jak przez stara towarzyszke"):
# a Buffi coming into a player's view is named to that client ("BuffiMark <vid>"), which walks through it as through
# the old companion (root/sidekickcollision.py) - after the boss skull of server-patches/enginefixes (its anchor).
EDITS.append(dict(file='char.cpp', marker='MT2009_PLUS_BUFFI_PASS_V1 (insert)',
     old='\t\tch->ChatPacket(CHAT_TYPE_COMMAND, "BossMark %u", (DWORD) m_vid);\n',
     new='\t\tch->ChatPacket(CHAT_TYPE_COMMAND, "BossMark %u", (DWORD) m_vid);\n'
     '\n'
     '\t// MT2009_PLUS_BUFFI_PASS_V1 (insert): a Buffi comes into a player\'s view with "BuffiMark <vid>" - the client walks\n'
     '\t// through it as through the old companion (playerbot_buffi.cpp, root/sidekickcollision.py).\n'
     '\tif (ch && ch->IsPC() && !d->IsBot())\n'
     '\t{\n'
     '\t\tvoid BuffiOnInsert(LPCHARACTER, LPCHARACTER);\n'
     '\t\tBuffiOnInsert(this, ch);\n'
     '\t}\n'))


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
