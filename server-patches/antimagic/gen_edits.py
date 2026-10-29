#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/antimagic (MT2009_PLUS_ANTI_RESIST_MAGIC_V1, README.md)
from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied last (after npcloc); its anchors are
bonusy67's length.h / char.cpp lines and droppreview's list in item_manager.cpp."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_ANTI_RESIST_MAGIC_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


add('../../common/length.h', 'point',
    "\tPOINT_GLOVE_BASE_ATTR_PCT,\t// 251 the glove's built-in Will line +x%\n"
    "\tPOINT_MAX_NUM,\t// 252 (an item keeps its bonus type in one byte: at most 256)\n",
    "\tPOINT_GLOVE_BASE_ATTR_PCT,\t// 251 the glove's built-in Will line +x%\n"
    "\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (point): Kamien Antymagii (28044/28045 +0..+9, the \"Anti Magic penetrate stone\"\n"
    "\t// package's APPLY_ANTI_RESIST_MAGIC) - a player's magic skill ignores x points of another player's magic\n"
    "\t// resistance (char_skill.cpp; a Sura gets half, char.cpp). An apply is a point here: 252 is the stones' applytype,\n"
    "\t// the 252nd value of item_attr's apply enum; unlike 198-251 it goes to the client as a point change (the exe's\n"
    "\t// POINT_MAX_NUM is 253 with it - client-patches/exe/Server/common/length.h; the window's \"Antymagia\" line).\n"
    "#define MT2009_PLUS_ANTI_RESIST_MAGIC\n"
    "\tPOINT_ANTI_RESIST_MAGIC,\t// 252\n"
    "\tPOINT_MAX_NUM,\t// 253 (an item keeps its bonus type in one byte: at most 256)\n")

add('char.cpp', 'point change',
    "\t\t\t// END_OF_DEPEND_BONUS_ATTRIBUTES\n",
    "\t\t\t// END_OF_DEPEND_BONUS_ATTRIBUTES\n\n"
    "\t\tcase POINT_ANTI_RESIST_MAGIC: // MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (point change): Kamien Antymagii - a Sura gets half\n"
    "\t\t\tif (GetJob() == JOB_SURA)\t// of every stone (the package's 0.2), so the point (and the client's line) is what works\n"
    "\t\t\t\tamount /= 2;\n"
    "\t\t\tSetPoint(type, GetPoint(type) + amount);\n"
    "\t\t\tval = GetPoint(type);\n"
    "\t\t\tbreak;\n")

add('char.cpp', 'point packet',
    "(type >= POINT_SUNGMA_PER_STR && type <= POINT_HIT_PCT)))",
    "(type >= POINT_SUNGMA_PER_STR && type <= POINT_HIT_PCT) || type == POINT_ANTI_RESIST_MAGIC /* MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (point packet): 252 to the client (exe POINT_MAX_NUM 253) */))")

add('char.cpp', 'login points',
    "\tGetDesc()->Packet(pack);\n}\n\nbool CHARACTER::ChangeSex()",
    "\tGetDesc()->Packet(pack);\n\n"
    "\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (login points): the points after the packet's POINT_PACKET_NUM that the client\n"
    "\t// shows (Sung Ma per cent 193-196, Precyzja 197, Antymagia 252) went to it only as a point change when they changed:\n"
    "\t// without such an item the client never heard them and its never-set slot read as garbage in the bonus window\n"
    "\t// (\"Antymagia -415579686%\" = the exe's XOR key 0xe73ac1da over a zeroed slot). Every points packet sends them too\n"
    "\t// (a change during the loading phase is lost on the client - no main instance yet - so Entergame sends one more).\n"
    "\tstatic const BYTE abExtraPoints[] = { POINT_SUNGMA_PER_STR, POINT_SUNGMA_PER_HP, POINT_SUNGMA_PER_MOVE,\n"
    "\t\tPOINT_SUNGMA_PER_IMMUNE, POINT_HIT_PCT, POINT_ANTI_RESIST_MAGIC };\n"
    "\tfor (BYTE bType : abExtraPoints)\n"
    "\t{\n"
    "\t\tstruct packet_point_change ppc;\n"
    "\t\tppc.header = HEADER_GC_CHARACTER_POINT_CHANGE;\n"
    "\t\tppc.dwVID = m_vid;\n"
    "\t\tppc.type = bType;\n"
    "\t\tppc.amount = 0;\n"
    "\t\tppc.value = GetPoint(bType);\n"
    "\t\tGetDesc()->Packet(ppc);\n"
    "\t}\n"
    "}\n\nbool CHARACTER::ChangeSex()")

add('input_login.cpp', 'enter points',
    "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip's set / random bonuses\n",
    "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip's set / random bonuses\n"
    "\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (enter points): the points once more now that the client has the character - the\n"
    "\t// point changes of the loading phase (items' Antymagia / Sung Ma % / Precyzja) never reached its status table\n"
    "\tch->PointsPacket();\n")

add('char.cpp', 'metin stones',
    "\t\t28043,\n#if defined(ENABLE_MAGIC_REDUCTION_SYSTEM) && defined(USE_MAGIC_REDUCTION_STONES)\n\t\t28044,\n",
    "\t\t28043,\n"
    "\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (metin stones): Kamien Antymagii (bron 28044, zbroja 28045) - one kind more of the\n"
    "\t// draw, the same chance and grades as every other kind (item_manager.cpp's preview list has them too)\n"
    "#if (defined(ENABLE_MAGIC_REDUCTION_SYSTEM) && defined(USE_MAGIC_REDUCTION_STONES)) || defined(MT2009_PLUS_ANTI_RESIST_MAGIC)\n"
    "\t\t28044,\n")

add('item_manager.cpp', 'preview stones',
    "\t28037, 28038, 28039, 28040, 28041, 28042, 28043,\n#if defined(ENABLE_MAGIC_REDUCTION_SYSTEM) && defined(USE_MAGIC_REDUCTION_STONES)\n",
    "\t28037, 28038, 28039, 28040, 28041, 28042, 28043,\n"
    "\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (preview stones): Kamien Antymagii, as CHARACTER::DetermineDropMetinStone\n"
    "#if (defined(ENABLE_MAGIC_REDUCTION_SYSTEM) && defined(USE_MAGIC_REDUCTION_STONES)) || defined(MT2009_PLUS_ANTI_RESIST_MAGIC)\n")

add('char_skill.cpp', 'magic',
    "#else\n\t\t\t\tiDam = iDam * (100 - pkChrVictim->GetResistPoint(POINT_RESIST_MAGIC, m_pkChr)) / 100;\n#endif\n",
    "#else\n"
    "\t\t\t\t{\n"
    "\t\t\t\t\tint iResistMagic = pkChrVictim->GetResistPoint(POINT_RESIST_MAGIC, m_pkChr);\n"
    "#ifdef MT2009_PLUS_ANTI_RESIST_MAGIC\n"
    "\t\t\t\t\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (magic): PvP only (the owner, 28.10.2026) - a player's magic skill on\n"
    "\t\t\t\t\t// another player ignores x points of the victim's magic resistance (Kamien Antymagii, POINT_ANTI_RESIST_MAGIC):\n"
    "\t\t\t\t\t// resistance = max(0, min(resistance, 100) - x) (a Sura's point is half already, char.cpp). Bots never seat it.\n"
    "\t\t\t\t\tif (iResistMagic > 0 && m_pkChr->IsPC() && pkChrVictim->IsPC())\n"
    "\t\t\t\t\t{\n"
    "\t\t\t\t\t\tconst int iAntiMagic = m_pkChr->GetPoint(POINT_ANTI_RESIST_MAGIC);\n"
    "\t\t\t\t\t\tif (iAntiMagic > 0)\n"
    "\t\t\t\t\t\t\tiResistMagic = MAX(0, MIN(iResistMagic, 100) - iAntiMagic);\n"
    "\t\t\t\t\t}\n"
    "#endif\n"
    "\t\t\t\t\tiDam = iDam * (100 - iResistMagic) / 100;\n"
    "\t\t\t\t}\n"
    "#endif\n")

add('cmd_gm.cpp', 'state',
    '\tch->ChatPacket(CHAT_TYPE_INFO, "   INSECT:%3d%% DESERT:%3d%%",\n',
    '#ifdef MT2009_PLUS_ANTI_RESIST_MAGIC\n'
    '\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (state): Kamien Antymagii - ignores x points of a player\'s magic resistance (PvP)\n'
    '\tch->ChatPacket(CHAT_TYPE_INFO, "   ANTI-MAGIC:%3d%%", tch->GetPoint(POINT_ANTI_RESIST_MAGIC));\n'
    '#endif\n\n'
    '\tch->ChatPacket(CHAT_TYPE_INFO, "   INSECT:%3d%% DESERT:%3d%%",\n')

add('../../db/src/ProtoReader.cpp', 'proto reader',
    '\tstring arApplyType[] = {"APPLY_NONE",',
    '#ifdef MT2009_PLUS_ANTI_RESIST_MAGIC\n'
    '\t// MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (proto reader): the package\'s name of the stones\' bonus, our point 252 (the array\n'
    '\t// below counts the old APPLY_* numbers, not our points - the same reason as APPLY_ACCEDRAIN_RATE above)\n'
    '\tif (trim(inputString) == "APPLY_ANTI_RESIST_MAGIC")\n'
    '\t\treturn POINT_ANTI_RESIST_MAGIC;\n'
    '#endif\n'
    '\tstring arApplyType[] = {"APPLY_NONE",')

add('char_item.cpp', 'tuning +3',
    "\t\t\t\t\t\t\tif (item2->GetVnum() >= 28330 && item2->GetVnum() <= 28343)\n",
    "\t\t\t\t\t\t\tif (item2->GetVnum() >= 28330 && item2->GetVnum() <= 28345) // MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (tuning +3): Antymagii +3 too\n")

add('char_item.cpp', 'tuning +4',
    "\t\t\t\t\t\t\tif (item2->GetVnum() >= 28430 && item2->GetVnum() <= 28443)\n",
    "\t\t\t\t\t\t\tif (item2->GetVnum() >= 28430 && item2->GetVnum() <= 28445) // MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (tuning +4): Antymagii +4 too\n")

add('ikarus_shop.cpp', 'shop search',
    "if (item->GetVnum() >= (28030+100*level) && item->GetVnum() <= (28043 + 100 * level))",
    "if (item->GetVnum() >= (28030+100*level) && item->GetVnum() <= (28045 + 100 * level)) // MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (shop search): 28g44 / 28g45 too")

add('ikarus_shop_manager.cpp', 'shop search lines',
    "if (item && item->GetVnum() >= (28030 + 100 * level) && item->GetVnum() <= (28043 + 100 * level))",
    "if (item && item->GetVnum() >= (28030 + 100 * level) && item->GetVnum() <= (28045 + 100 * level)) // MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (shop search lines): 28g44 / 28g45 too")

json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
print('antimagic: %d edits' % len(E))
if len(sys.argv) > 1:
    bad = 0
    for e in E:
        t = open(os.path.join(sys.argv[1], e['file']), encoding='latin-1').read().replace('\r\n', '\n')
        if e['marker'] not in t and t.count(e['old']) != 1:
            print('%s: %s - the code is there %d times' % (e['file'], e['marker'], t.count(e['old'])))
            bad += 1
    print('check: %s' % ('OK' if not bad else '%d problem(s)' % bad))
    sys.exit(1 if bad else 0)
