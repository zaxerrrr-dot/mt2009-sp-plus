#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/skillcolor (MT2009_PLUS_SKILL_COLOR_V1, README.md)
from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied LAST (after bonusy67c): the packet anchors are
the fish puzzle's lines, the login anchor the skill hack's. The logic is the overlay's playerbot_skillcolor.cpp (every
declaration below has its definition there)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_SKILL_COLOR_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


# --- packet.h: the headers (free in our packet.h and in the exe's Packet.h - client-patches/exe, both checked)
add('packet.h', 'cg header',
    "\tHEADER_CG_FISH_EVENT_SEND\t\t= 219,\t// MT2009_PLUS_FISH_PUZZLE_V2 (cg header): fish puzzle - fish_puzzle.cpp\n",
    "\tHEADER_CG_FISH_EVENT_SEND\t\t= 219,\t// MT2009_PLUS_FISH_PUZZLE_V2 (cg header): fish puzzle - fish_puzzle.cpp\n"
    "\t// " + M + " (cg header): Kolor umiejetnosci - the colour window's choice for one skill (playerbot_skillcolor.cpp);\n"
    "\t// the package's number, free here and in the exe\n"
    "\tHEADER_CG_SKILL_COLOR\t\t\t= 56,\n")
add('packet.h', 'gc header',
    "\tHEADER_GC_FISH_EVENT_INFO\t\t\t\t= 223,\t// MT2009_PLUS_FISH_PUZZLE_V2 (gc header): fish puzzle - fish_puzzle.cpp\n",
    "\tHEADER_GC_FISH_EVENT_INFO\t\t\t\t= 223,\t// MT2009_PLUS_FISH_PUZZLE_V2 (gc header): fish puzzle - fish_puzzle.cpp\n"
    "\t// " + M + " (gc header): one skill's colour of a character (after its add packet, when it changes)\n"
    "\tHEADER_GC_SKILL_COLOR\t\t\t\t\t= 59,\n")
add('packet.h', 'structs',
    'static_assert(sizeof(TPacketCGFishEvent) == 2 && sizeof(TPacketGCFishEventInfo) == 10, "fish event packets");\n',
    'static_assert(sizeof(TPacketCGFishEvent) == 2 && sizeof(TPacketGCFishEventInfo) == 10, "fish event packets");\n'
    '\n'
    '// ' + M + ' (structs): Kolor umiejetnosci (server-patches/skillcolor/README.md). A colour is 0 (the effect\'s own)\n'
    '// or 0xFFrrggbb; layer n colours the effect\'s particle system n (the 5th also every later one). The exe has the same\n'
    '// (client-patches/exe UserInterface/Packet.h, the same static_assert).\n'
    'enum\n'
    '{\n'
    '\tSKILL_COLOR_LAYERS = 5,\n'
    '\tSKILL_COLOR_TYPE_OWN = 0,\t// the character\'s own colour of the skill (player.skill_color)\n'
    '\tSKILL_COLOR_TYPE_BUFF = 1,\t// the colour of the shaman buff it carries (its caster\'s; 94/95/96/110/111)\n'
    '};\n'
    '\n'
    'typedef struct SPacketCGSkillColor\n'
    '{\n'
    '\tBYTE\tbHeader;\n'
    '\tWORD\twSkillVnum;\n'
    '\tDWORD\tadwColor[SKILL_COLOR_LAYERS];\n'
    '} TPacketCGSkillColor;\n'
    '\n'
    'typedef struct SPacketGCSkillColor\n'
    '{\n'
    '\tBYTE\tbHeader;\n'
    '\tDWORD\tdwVID;\n'
    '\tBYTE\tbType;\n'
    '\tWORD\twSkillVnum;\n'
    '\tDWORD\tadwColor[SKILL_COLOR_LAYERS];\n'
    '} TPacketGCSkillColor;\n'
    '\n'
    'static_assert(sizeof(TPacketCGSkillColor) == 23 && sizeof(TPacketGCSkillColor) == 28, "skill colour packets (exe the same)");\n')

# --- packet_info.cpp: the fixed size, with the sequence byte (the exe's Send + SendSequence)
add('packet_info.cpp', 'size',
    '\tSet(HEADER_CG_FISH_EVENT_SEND, sizeof(TPacketCGFishEvent), "FishEvent", true);\t// MT2009_PLUS_FISH_PUZZLE_V2 (size)\n',
    '\tSet(HEADER_CG_FISH_EVENT_SEND, sizeof(TPacketCGFishEvent), "FishEvent", true);\t// MT2009_PLUS_FISH_PUZZLE_V2 (size)\n'
    '\tSet(HEADER_CG_SKILL_COLOR, sizeof(TPacketCGSkillColor), "SkillColor", true);\t// ' + M + ' (size): 23 bytes\n')

# --- input_main.cpp: the window's choice
add('input_main.cpp', 'packet',
    "\t\tcase HEADER_CG_USE_SKILL:\n\t\t\tif (!ch->IsObserverMode())\n\t\t\t\tUseSkill(ch, c_pData);\n\t\t\tbreak;\n",
    "\t\tcase HEADER_CG_USE_SKILL:\n\t\t\tif (!ch->IsObserverMode())\n\t\t\t\tUseSkill(ch, c_pData);\n\t\t\tbreak;\n"
    "\n"
    "\t\t// " + M + " (packet): Kolor umiejetnosci - one skill's colour from the window (playerbot_skillcolor.cpp)\n"
    "\t\tcase HEADER_CG_SKILL_COLOR:\n"
    "\t\t\t{\n"
    "\t\t\t\tvoid SkillColorPacket(LPCHARACTER ch, const char* data);\n"
    "\t\t\t\tSkillColorPacket(ch, c_pData);\n"
    "\t\t\t}\n"
    "\t\t\tbreak;\n")

# --- char.cpp: the colours after a character's add packets, one viewer; the VID's state goes with the character
add('char.cpp', 'insert',
    "\t\td->Packet(addPacket);\n\t}\n\n\tif (iDur)\n",
    "\t\td->Packet(addPacket);\n"
    "\t\t// " + M + " (insert): its skill colours to this viewer (none for a character without any - bots)\n"
    "\t\t{ void SkillColorEncodeInsert(LPCHARACTER ch, LPDESC d); SkillColorEncodeInsert(this, d); }\n"
    "\t}\n\n\tif (iDur)\n")
add('char.cpp', 'destroy',
    "\ts_mapM2RegenBaseMaxHP.erase((DWORD) GetVID());\t// MT2009_PLUS_DUNGEON_MOB_HP_V2 (destroy)\n",
    "\ts_mapM2RegenBaseMaxHP.erase((DWORD) GetVID());\t// MT2009_PLUS_DUNGEON_MOB_HP_V2 (destroy)\n"
    "\t{ void SkillColorOnDestroy(LPCHARACTER); SkillColorOnDestroy(this); }\t// " + M + " (destroy)\n")

# --- char_skill.cpp: a shaman buff wears its caster's colour (before its affect: the client attaches it in it)
add('char_skill.cpp', 'buff',
    "\tif (IS_SET(pkSk->dwFlag, SKILL_FLAG_SELFONLY))\n\t\tpkVictim = GetSelfOnlySkillVictim(this, dwVnum, pkVictim);\n\n"
    "\t// MT2009_PLUS_DRAGON_ROAR_EFFECT_V1",
    "\tif (IS_SET(pkSk->dwFlag, SKILL_FLAG_SELFONLY))\n\t\tpkVictim = GetSelfOnlySkillVictim(this, dwVnum, pkVictim);\n\n"
    "\t// " + M + " (buff): Blogoslawienstwo / Odbicie / Pomoc Smoka / Zwinnosc / Zwiekszenie Ataku on pkVictim (himself,\n"
    "\t// a party member, another player) in the caster's colour (playerbot_skillcolor.cpp)\n"
    "\t{ void SkillColorOnBuff(LPCHARACTER caster, LPCHARACTER victim, DWORD dwVnum); SkillColorOnBuff(this, pkVictim, dwVnum); }\n\n"
    "\t// MT2009_PLUS_DRAGON_ROAR_EFFECT_V1")

# --- input_login.cpp: the character's row, read at every login (after the skill hack's tab)
add('input_login.cpp', 'login',
    "\t{ void Skill2OnLogin(CHARACTER*); Skill2OnLogin(ch); }\n",
    "\t{ void Skill2OnLogin(CHARACTER*); Skill2OnLogin(ch); }\n"
    "\t// " + M + " (login): its skill colours (player.skill_color) to it and everyone around (playerbot_skillcolor.cpp)\n"
    "\t{ void SkillColorOnLogin(LPCHARACTER); SkillColorOnLogin(ch); }\n")


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
