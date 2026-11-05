#!/usr/bin/env python3
"""gen_edits.py [<engine game/src dir>] -- writes edits.json of server-patches/remotecall (MT2009_PLUS_REMOTE_CALL_V1,
README.md) and, given the engine's game/src (every other patch applied), checks that each edit's old code is there
exactly once (or its marker already is)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_REMOTE_CALL_V1"

EDITS = [
    ("packet.h", "cg header",
     "\tHEADER_CG_TITLE\t\t\t\t\t= 185,\n",
     "\tHEADER_CG_TITLE\t\t\t\t\t= 185,\n"
     "\t// %s (cg header): Enasir - the client's hello, summon, send away (remote_call.cpp)\n"
     "\tHEADER_CG_REMOTE_CALL\t\t\t= 190,\n" % M),
    ("packet.h", "gc header",
     "\tHEADER_GC_TITLE\t\t\t\t\t\t\t= 189,\n",
     "\tHEADER_GC_TITLE\t\t\t\t\t\t\t= 189,\n"
     "\t// %s (gc header): Enasir - the services' times, summoned, gone, a message, Enasir's storeroom\n"
     "\tHEADER_GC_REMOTE_CALL\t\t\t\t\t= 190,\n" % M),
    ("packet.h", "structs",
     "\t\"title packets (exe the same)\");\n",
     "\t\"title packets (exe the same)\");\n\n"
     "// %s (structs): Enasir (server-patches/remotecall/README.md). CG 190: a sub-header (0 HELLO - the state, at every\n"
     "// game phase; 1 SUMMON; 2 UNSUMMON). GC 190 (static): 0 STATE (value0/1 the storeroom / shop service's seconds left,\n"
     "// value2 bit0 summoning allowed here), 1 SUMMONED (seconds he stays, his VID), 2 GONE (the cool-down's seconds),\n"
     "// 3 MESSAGE (a code), 4 SAFEBOX (the next storeroom is Enasir's). The exe has the same (client-patches/exe Packet.h).\n"
     "typedef struct SPacketCGRemoteCall\n{\n\tBYTE\tbHeader;\n\tBYTE\tbSubHeader;\n} TPacketCGRemoteCall;\n\n"
     "typedef struct SPacketGCRemoteCall\n{\n\tBYTE\tbHeader;\n\tBYTE\tbSubHeader;\n\tDWORD\tdwValue0;\n\tDWORD\tdwValue1;\n"
     "\tDWORD\tdwValue2;\n} TPacketGCRemoteCall;\n\n"
     "static_assert(sizeof(TPacketCGRemoteCall) == 2 && sizeof(TPacketGCRemoteCall) == 14, \"remote call packets (exe the same)\");\n"
     % M),
    ("packet_info.cpp", "size",
     "\tSet(HEADER_CG_TITLE, sizeof(TPacketCGTitle), \"Title\", true);\t// MT2009_PLUS_TITLES_V1 (size): 6 bytes\n",
     "\tSet(HEADER_CG_TITLE, sizeof(TPacketCGTitle), \"Title\", true);\t// MT2009_PLUS_TITLES_V1 (size): 6 bytes\n"
     "\tSet(HEADER_CG_REMOTE_CALL, sizeof(TPacketCGRemoteCall), \"RemoteCall\", true);\t// %s (size): 2 bytes\n" % M),
    ("input_main.cpp", "packet",
     "\t\t\t\tvoid TitleSystemPacket(LPCHARACTER ch, const char* data);\n"
     "\t\t\t\tTitleSystemPacket(ch, c_pData);\n"
     "\t\t\t}\n"
     "\t\t\tbreak;\n",
     "\t\t\t\tvoid TitleSystemPacket(LPCHARACTER ch, const char* data);\n"
     "\t\t\t\tTitleSystemPacket(ch, c_pData);\n"
     "\t\t\t}\n"
     "\t\t\tbreak;\n\n"
     "\t\t// %s (packet): Enasir - hello, summon, send away (remote_call.cpp)\n"
     "\t\tcase HEADER_CG_REMOTE_CALL:\n"
     "\t\t\t{\n"
     "\t\t\t\tvoid RemoteCallPacket(LPCHARACTER ch, const char* data);\n"
     "\t\t\t\tRemoteCallPacket(ch, c_pData);\n"
     "\t\t\t}\n"
     "\t\t\tbreak;\n" % M),
    ("char.cpp", "insert",
     "\tif (d != GetDesc() && ch && !ch->IsGM() && !IsEntityViewSendable())\n\t\treturn;\n",
     "\tif (d != GetDesc() && ch && !ch->IsGM() && !IsEntityViewSendable())\n\t\treturn;\n"
     "\t// %s (insert): a summoned Enasir is seen by his owner only (remote_call.cpp)\n"
     "\tif (d != GetDesc() && !IsPC() && GetRaceNum() == 20874)\n"
     "\t{\n"
     "\t\tbool RemoteCallVisibleTo(LPCHARACTER npc, LPCHARACTER viewer);\n"
     "\t\tif (!RemoteCallVisibleTo(this, ch))\n"
     "\t\t\treturn;\n"
     "\t}\n" % M),
    ("char.cpp", "destroy",
     "\t{ void TitleSystemOnDestroy(LPCHARACTER); TitleSystemOnDestroy(this); }\t// MT2009_PLUS_TITLES_V1 (destroy)\n",
     "\t{ void TitleSystemOnDestroy(LPCHARACTER); TitleSystemOnDestroy(this); }\t// MT2009_PLUS_TITLES_V1 (destroy)\n"
     "\t{ void RemoteCallOnDestroy(LPCHARACTER); RemoteCallOnDestroy(this); }\t// %s (destroy)\n" % M),
    ("char.cpp", "safebox close",
     "\tChatPacket(CHAT_TYPE_COMMAND, \"CloseSafebox\");\n",
     "\tChatPacket(CHAT_TYPE_COMMAND, \"CloseSafebox\");\n"
     "\t{ void RemoteCallOnSafeboxClose(LPCHARACTER); RemoteCallOnSafeboxClose(this); }\t// %s (safebox close)\n" % M),
    ("char_item.cpp", "use",
     "\t\tif (iTitleUse >= 0)\n\t\t\treturn iTitleUse != 0;\n\t}\n",
     "\t\tif (iTitleUse >= 0)\n\t\t\treturn iTitleUse != 0;\n\t}\n"
     "\t// %s (use): Dozorca / Handlarz Enasir 72368-72371 - the service's time (remote_call.cpp)\n"
     "\t{\n"
     "\t\tint RemoteCallUseItem(LPCHARACTER ch, LPITEM item);\n"
     "\t\tconst int iRemoteCallUse = RemoteCallUseItem(this, item);\n"
     "\t\tif (iRemoteCallUse >= 0)\n"
     "\t\t\treturn iRemoteCallUse != 0;\n"
     "\t}\n" % M),
    ("shop_manager.cpp", "sell fee",
     "\tdwTax = dwPrice * iVal/100;\n\tdwPrice -= dwTax;\n",
     "\tdwTax = dwPrice * iVal/100;\n\tdwPrice -= dwTax;\n"
     "\t// %s (sell fee): a sale at a summoned Enasir leaves him 10 %% (pl-wiki; remote_call.cpp)\n"
     "\t{ YANG RemoteCallSellFee(LPCHARACTER ch, YANG price); dwPrice -= RemoteCallSellFee(ch, dwPrice); }\n" % M),
    ("questlua.cpp", "lua",
     "\t\t{ void RegisterTitleFunctionTable(); RegisterTitleFunctionTable(); }\n",
     "\t\t{ void RegisterTitleFunctionTable(); RegisterTitleFunctionTable(); }\n"
     "\t\t// %s (lua): remote_call.* - Enasir's quest (remote_call.cpp, defined in namespace quest).\n"
     "\t\t{ void RegisterRemoteCallFunctionTable(); RegisterRemoteCallFunctionTable(); }\n" % M),
    ("cmd.cpp", "command declare",
     "ACMD(do_title_system)\n{\n\tTitleSystemCommand(ch, argument);\n}\n",
     "ACMD(do_title_system)\n{\n\tTitleSystemCommand(ch, argument);\n}\n"
     "// %s (command declare): \"/enasir\" - Enasir's services for a GM's own character (remote_call.cpp)\n"
     "void RemoteCallCommand(LPCHARACTER ch, const char* argument);\n"
     "ACMD(do_remote_call)\n{\n\tRemoteCallCommand(ch, argument);\n}\n" % M),
    ("cmd.cpp", "command table",
     "\t{ \"title_system\",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t},\n",
     "\t{ \"title_system\",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t},\n"
     "\t{ \"enasir\",\tdo_remote_call,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t}, // %s (command table)\n" % M),
]


def main():
    edits = []
    for f, tag, old, new in EDITS:
        marker = "%s (%s)" % (M, tag)
        assert marker in new, marker
        edits.append({"file": f, "marker": marker, "old": old, "new": new})
    with open(os.path.join(HERE, "edits.json"), "w") as fp:
        json.dump(edits, fp, indent=1)
        fp.write("\n")
    if len(sys.argv) > 1:
        bad = 0
        for e in edits:
            text = open(os.path.join(sys.argv[1], e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
            if e["marker"] in text:
                continue
            n = text.count(e["old"])
            if n != 1:
                print("%s: %s - old code found %d times" % (e["file"], e["marker"], n))
                bad += 1
        print("remotecall: %d edits, %d anchors wrong" % (len(edits), bad))
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
