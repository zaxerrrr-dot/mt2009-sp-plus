#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/tytuly (MT2009_PLUS_TITLES_V1, README.md) from the
code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied LAST (after skillcolor): the packet, login, insert
and destroy anchors are skill colour's lines. The logic is the overlay's playerbot_titles.cpp (every declaration below
has its definition there)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_TITLES_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


# --- packet.h: the headers - the package's numbers, free in our packet.h and in the exe's Packet.h (client-patches/exe)
add('packet.h', 'cg header',
    "\tHEADER_CG_SKILL_COLOR\t\t\t= 56,\n",
    "\tHEADER_CG_SKILL_COLOR\t\t\t= 56,\n"
    "\t// " + M + " (cg header): Tytuly - the client's hello / the title window (playerbot_titles.cpp)\n"
    "\tHEADER_CG_TITLE\t\t\t\t\t= 185,\n")
add('packet.h', 'gc header',
    "\tHEADER_GC_SKILL_COLOR\t\t\t\t\t= 59,\n",
    "\tHEADER_GC_SKILL_COLOR\t\t\t\t\t= 59,\n"
    "\t// " + M + " (gc header): Tytuly - the catalogue, the owned titles, notices, who wears what (dynamic)\n"
    "\tHEADER_GC_TITLE\t\t\t\t\t\t\t= 189,\n")
add('packet.h', 'structs',
    'static_assert(sizeof(TPacketCGSkillColor) == 23 && sizeof(TPacketGCSkillColor) == 28, "skill colour packets (exe the same)");\n',
    'static_assert(sizeof(TPacketCGSkillColor) == 23 && sizeof(TPacketGCSkillColor) == 28, "skill colour packets (exe the same)");\n'
    '\n'
    '// ' + M + ' (structs): Tytuly (server-patches/tytuly/README.md). CG 185: a sub-header (OPEN = the hello / refresh,\n'
    '// EQUIP, UNEQUIP) and a title. GC 189 is dynamic: TPacketGCTitle, then wCount rows (TABLE: TPacketGCTitleRow, PLAYER:\n'
    '// TPacketGCTitleOwned) or one record (EQUIPPED: DWORD, NOTIFY: TPacketGCTitleNotify, VISUAL: TPacketGCTitleVisual).\n'
    '// The exe has the same (client-patches/exe UserInterface/Packet.h, the same static_assert).\n'
    'enum\n'
    '{\n'
    '\tTITLE_CG_OPEN = 0,\n'
    '\tTITLE_CG_EQUIP = 1,\n'
    '\tTITLE_CG_UNEQUIP = 2,\n'
    '\tTITLE_GC_TABLE = 0,\n'
    '\tTITLE_GC_PLAYER = 1,\n'
    '\tTITLE_GC_EQUIPPED = 2,\n'
    '\tTITLE_GC_NOTIFY = 3,\n'
    '\tTITLE_GC_VISUAL = 4,\n'
    '\tTITLE_NAME_LEN = 32,\n'
    '\tTITLE_CONDITION_LEN = 160,\n'
    '\tTITLE_EFFECT_LEN = 96,\n'
    '};\n'
    '\n'
    'typedef struct SPacketCGTitle\n'
    '{\n'
    '\tBYTE\tbHeader;\n'
    '\tBYTE\tbSubHeader;\n'
    '\tDWORD\tdwTitle;\n'
    '} TPacketCGTitle;\n'
    '\n'
    'typedef struct SPacketGCTitle\n'
    '{\n'
    '\tBYTE\tbHeader;\n'
    '\tWORD\twSize;\n'
    '\tBYTE\tbSubHeader;\n'
    '\tWORD\twCount;\n'
    '} TPacketGCTitle;\n'
    '\n'
    'typedef struct SPacketGCTitleRow\n'
    '{\n'
    '\tDWORD\tdwTitle;\n'
    '\tBYTE\tbType;\t\t\t// 1 the name only, 3 an effect over the head, 4 the name on a plate\n'
    '\tBYTE\tbPermanent;\n'
    '\tWORD\twResource;\t\t// d:/ymir work/ui/game/title/titles/title_<wResource>.sub\n'
    '\tDWORD\tdwDuration;\t\t// a timed title\'s default time (s)\n'
    '\tDWORD\tdwColor;\t\t// the name\'s colour (ARGB)\n'
    '\tshort\tsEffectZ;\t\t// the effect\'s height over the head (added to the exe\'s default)\n'
    '\tchar\tszName[TITLE_NAME_LEN + 1];\n'
    '\tchar\tszCondition[TITLE_CONDITION_LEN + 1];\n'
    '\tchar\tszEffect[TITLE_EFFECT_LEN + 1];\n'
    '} TPacketGCTitleRow;\n'
    '\n'
    'typedef struct SPacketGCTitleOwned\n'
    '{\n'
    '\tDWORD\tdwTitle;\n'
    '\tDWORD\tdwEndTime;\t\t// 0 = for good\n'
    '} TPacketGCTitleOwned;\n'
    '\n'
    'typedef struct SPacketGCTitleNotify\n'
    '{\n'
    '\tBYTE\tbMessage;\n'
    '\tDWORD\tdwTitle;\n'
    '} TPacketGCTitleNotify;\n'
    '\n'
    'typedef struct SPacketGCTitleVisual\n'
    '{\n'
    '\tDWORD\tdwVID;\n'
    '\tDWORD\tdwTitle;\t\t// 0 = none\n'
    '} TPacketGCTitleVisual;\n'
    '\n'
    'static_assert(sizeof(TPacketCGTitle) == 6 && sizeof(TPacketGCTitle) == 6 && sizeof(TPacketGCTitleRow) == 309 &&\n'
    '\tsizeof(TPacketGCTitleOwned) == 8 && sizeof(TPacketGCTitleNotify) == 5 && sizeof(TPacketGCTitleVisual) == 8,\n'
    '\t"title packets (exe the same)");\n')

# --- packet_info.cpp: the fixed size, with the sequence byte (the exe's Send + SendSequence)
add('packet_info.cpp', 'size',
    '\tSet(HEADER_CG_SKILL_COLOR, sizeof(TPacketCGSkillColor), "SkillColor", true);\t// MT2009_PLUS_SKILL_COLOR_V1 (size): 23 bytes\n',
    '\tSet(HEADER_CG_SKILL_COLOR, sizeof(TPacketCGSkillColor), "SkillColor", true);\t// MT2009_PLUS_SKILL_COLOR_V1 (size): 23 bytes\n'
    '\tSet(HEADER_CG_TITLE, sizeof(TPacketCGTitle), "Title", true);\t// ' + M + ' (size): 6 bytes\n')

# --- input_main.cpp: the hello and the window
add('input_main.cpp', 'packet',
    "\t\tcase HEADER_CG_SKILL_COLOR:\n"
    "\t\t\t{\n"
    "\t\t\t\tvoid SkillColorPacket(LPCHARACTER ch, const char* data);\n"
    "\t\t\t\tSkillColorPacket(ch, c_pData);\n"
    "\t\t\t}\n"
    "\t\t\tbreak;\n",
    "\t\tcase HEADER_CG_SKILL_COLOR:\n"
    "\t\t\t{\n"
    "\t\t\t\tvoid SkillColorPacket(LPCHARACTER ch, const char* data);\n"
    "\t\t\t\tSkillColorPacket(ch, c_pData);\n"
    "\t\t\t}\n"
    "\t\t\tbreak;\n"
    "\n"
    "\t\t// " + M + " (packet): Tytuly - the client's hello, the title window (playerbot_titles.cpp)\n"
    "\t\tcase HEADER_CG_TITLE:\n"
    "\t\t\t{\n"
    "\t\t\t\tvoid TitleSystemPacket(LPCHARACTER ch, const char* data);\n"
    "\t\t\t\tTitleSystemPacket(ch, c_pData);\n"
    "\t\t\t}\n"
    "\t\t\tbreak;\n")

# --- char.cpp: the worn title after a character's add packets, one viewer; the VID's state goes with the character
add('char.cpp', 'insert',
    "\t\t{ void SkillColorEncodeInsert(LPCHARACTER ch, LPDESC d); SkillColorEncodeInsert(this, d); }\n",
    "\t\t{ void SkillColorEncodeInsert(LPCHARACTER ch, LPDESC d); SkillColorEncodeInsert(this, d); }\n"
    "\t\t// " + M + " (insert): its worn title to this viewer (none for a character without one - bots)\n"
    "\t\t{ void TitleSystemEncodeInsert(LPCHARACTER ch, LPDESC d); TitleSystemEncodeInsert(this, d); }\n")
add('char.cpp', 'destroy',
    "\t{ void SkillColorOnDestroy(LPCHARACTER); SkillColorOnDestroy(this); }\t// MT2009_PLUS_SKILL_COLOR_V1 (destroy)\n",
    "\t{ void SkillColorOnDestroy(LPCHARACTER); SkillColorOnDestroy(this); }\t// MT2009_PLUS_SKILL_COLOR_V1 (destroy)\n"
    "\t{ void TitleSystemOnDestroy(LPCHARACTER); TitleSystemOnDestroy(this); }\t// " + M + " (destroy)\n")

# --- input_login.cpp: the character's rows, read at every login (after skill colour's)
add('input_login.cpp', 'login',
    "\t{ void SkillColorOnLogin(LPCHARACTER); SkillColorOnLogin(ch); }\n",
    "\t{ void SkillColorOnLogin(LPCHARACTER); SkillColorOnLogin(ch); }\n"
    "\t// " + M + " (login): its titles (player.player_title), the worn one to everyone around (playerbot_titles.cpp)\n"
    "\t{ void TitleSystemOnLogin(LPCHARACTER); TitleSystemOnLogin(ch); }\n")

# --- char_item.cpp: the certificates 57000-57002, before the item's own limits and type (as the other uses)
add('char_item.cpp', 'use',
    "\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n",
    "\t// " + M + " (use): Certyfikat Tytulu 57000-57002 - its title (value0) for its time (value1), playerbot_titles.cpp\n"
    "\t{\n"
    "\t\tint TitleSystemUseItem(LPCHARACTER ch, LPITEM item);\n"
    "\t\tconst int iTitleUse = TitleSystemUseItem(this, item);\n"
    "\t\tif (iTitleUse >= 0)\n"
    "\t\t\treturn iTitleUse != 0;\n"
    "\t}\n"
    "\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n")

# --- cmd.cpp: the GM command (also under the package's name)
add('cmd.cpp', 'command declare',
    "ACMD(do_fishpuzzle)\n",
    "// " + M + " (command declare): \"/tytul\" (and the package's \"/title_system\") - playerbot_titles.cpp\n"
    "void TitleSystemCommand(LPCHARACTER ch, const char* argument);\n"
    "ACMD(do_title_system)\n"
    "{\n"
    "\tTitleSystemCommand(ch, argument);\n"
    "}\n"
    "ACMD(do_fishpuzzle)\n")
add('cmd.cpp', 'command table',
    '\t{ "fishpuzzle",\tdo_fishpuzzle,\t0,\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_FISH_PUZZLE_V1 (command table)\n',
    '\t{ "fishpuzzle",\tdo_fishpuzzle,\t0,\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_FISH_PUZZLE_V1 (command table)\n'
    '\t{ "tytul",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t}, // ' + M + ' (command table)\n'
    '\t{ "title_system",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t},\n')

# --- questlua.cpp: the quests' "title" module
add('questlua.cpp', 'lua',
    "\t\t{ void RegisterMlodziFunctionTable(); RegisterMlodziFunctionTable(); }\n",
    "\t\t{ void RegisterMlodziFunctionTable(); RegisterMlodziFunctionTable(); }\n"
    "\t\t// " + M + " (lua): title.give / has / remove / equipped - Tytuly (playerbot_titles.cpp).\n"
    "\t\t{ void RegisterTitleFunctionTable(); RegisterTitleFunctionTable(); }\n")


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
