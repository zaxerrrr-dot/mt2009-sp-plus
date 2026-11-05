#!/usr/bin/env python3
"""gen_edits.py [<engine game/src dir>] -- writes edits.json of server-patches/language (MT2009_PLUS_LANGUAGE_V1,
README.md) and, given the engine's game/src (every other patch applied), checks that each edit's old code is there
exactly once (or its marker already is)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_LANGUAGE_V1"
Q = "MT2009_PLUS_LANGUAGE_QUESTINFO_V1"

EDITS = [
    ("char.cpp", "include",
     "#include \"char.h\"\n",
     "#include \"char.h\"\n"
     "#include \"mt2009_language.h\" // %s (include): the reader's language (mt2009_language.cpp)\n" % M),
    ("char.cpp", "chat",
     "void CHARACTER::ChatPacket(BYTE type, const char * format, ...)\n"
     "{\n"
     "\tLPDESC d = GetDesc();\n"
     "\n"
     "\tif (!d || !format)\n"
     "\t\treturn;\n"
     "\n"
     "\tchar chatbuf[CHAT_MAX_LEN + 1];\n"
     "\tva_list args;\n"
     "\n"
     "\tva_start(args, format);\n"
     "\tint len = vsnprintf(chatbuf, sizeof(chatbuf), format, args);\n"
     "\tva_end(args);\n",
     "void CHARACTER::ChatPacket(BYTE type, const char * format, ...)\n"
     "{\n"
     "\tLPDESC d = GetDesc();\n"
     "\n"
     "\tif (!d || !format)\n"
     "\t\treturn;\n"
     "\n"
     "\tchar chatbuf[CHAT_MAX_LEN + 1];\n"
     "\tva_list args;\n"
     "\n"
     "\t// %s (chat): a line in the reader's language - the Polish format's translation (the same conversions), else\n"
     "\t// the whole line looked up (a notice, a quest's syschat); never the client's commands, never players' chat.\n"
     "\tconst char* langFormat = Mt2009LanguageChatFormat(this, type, format);\n"
     "\tva_start(args, format);\n"
     "\tint len = vsnprintf(chatbuf, sizeof(chatbuf), langFormat, args);\n"
     "\tva_end(args);\n"
     "\tlen = Mt2009LanguageChatResult(this, type, langFormat != format, chatbuf, sizeof(chatbuf), len);\n" % M),
    ("input_login.cpp", "enter",
     "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter)",
     "\t{ void Mt2009LanguageOnEnterGame(LPCHARACTER); Mt2009LanguageOnEnterGame(ch); } // %s (enter): player.language,\n"
     "\t// before the login quests run (mt2009_language.cpp)\n"
     "\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter)" % M),
    ("questlua.cpp", "lua",
     "\t\t{ void RegisterRemoteCallFunctionTable(); RegisterRemoteCallFunctionTable(); }\n",
     "\t\t{ void RegisterRemoteCallFunctionTable(); RegisterRemoteCallFunctionTable(); }\n"
     "\t\t// %s (lua): pc.get_language / set_language, mt2009_tr, mt2009_item_name, mt2009_mob_name, mt2009_languages\n"
     "\t\t// (mt2009_language.cpp, defined in namespace quest).\n"
     "\t\t{ void RegisterMt2009LanguageFunctions(); RegisterMt2009LanguageFunctions(); }\n" % M),
    ("questlua.cpp", "lua load",
     "\t\t// END_OF_LUA_INIT_ERROR_MESSAGE\n",
     "\t\t// %s (lua load): quest/mt2009_language.lua - the quests' texts in the reader's language; not fatal\n"
     "\t\t{ void LoadMt2009LanguageLua(lua_State*); LoadMt2009LanguageLua(L); }\n"
     "\t\t// END_OF_LUA_INIT_ERROR_MESSAGE\n" % M),
    ("cmd.cpp", "command declare",
     "ACMD(do_title_system)\n{\n\tTitleSystemCommand(ch, argument);\n}\n",
     "ACMD(do_title_system)\n{\n\tTitleSystemCommand(ch, argument);\n}\n"
     "// %s (command declare): \"/lang <code>\" - the client names its language (mt2009_language.cpp)\n"
     "void Mt2009LanguageCommand(LPCHARACTER ch, const char* argument);\n"
     "ACMD(do_mt2009_lang)\n{\n\tMt2009LanguageCommand(ch, argument);\n}\n" % M),
    ("cmd.cpp", "command table",
     "\t{ \"title_system\",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t},\n",
     "\t{ \"title_system\",\tdo_title_system,\t0,\tPOS_DEAD,\tGM_LOW_WIZARD\t},\n"
     "\t{ \"lang\",\tdo_mt2009_lang,\t0,\tPOS_DEAD,\tGM_PLAYER\t}, // %s (command table)\n" % M),
    # MT2009_PLUS_LANGUAGE_QUESTINFO_V1: the quest window's texts in the reader's language when the packet is made (the
    # quest keeps them in Polish, so "/lang" can send them again), and the code page's safety net for text packets.
    ("questpc.cpp", "include",
     "#include \"questevent.h\"\n",
     "#include \"questevent.h\"\n"
     "#include \"mt2009_language.h\" // %s (include): the quest window in the reader's language\n" % Q),
    ("questpc.cpp", "title",
     "\t\t\tconstexpr auto TitleSize = 30+1;\n"
     "\t\t\tm_RunningQuestState->_title.reserve(TitleSize);\n"
     "\t\t\tbuf.write(m_RunningQuestState->_title.c_str(), TitleSize);\n",
     "\t\t\tconstexpr auto TitleSize = 30+1;\n"
     "\t\t\t// %s (title): the Polish title in the reader's language, cut to the field, NUL-filled\n"
     "\t\t\tchar title[TitleSize];\n"
     "\t\t\tMt2009QuestInfoText(CQuestManager::instance().GetCurrentCharacterPtr(), m_RunningQuestState->_title, title, sizeof(title));\n"
     "\t\t\tbuf.write(title, TitleSize);\n" % Q),
    ("questpc.cpp", "clock",
     "\t\t\tconstexpr auto ClockSize = 16+1;\n"
     "\t\t\tm_RunningQuestState->_clock_name.reserve(ClockSize);\n"
     "\t\t\tbuf.write(m_RunningQuestState->_clock_name.c_str(), ClockSize);\n",
     "\t\t\tconstexpr auto ClockSize = 16+1;\n"
     "\t\t\t// %s (clock): the clock's name in the reader's language\n"
     "\t\t\tchar clockName[ClockSize];\n"
     "\t\t\tMt2009QuestInfoText(CQuestManager::instance().GetCurrentCharacterPtr(), m_RunningQuestState->_clock_name, clockName, sizeof(clockName));\n"
     "\t\t\tbuf.write(clockName, ClockSize);\n" % Q),
    ("questpc.cpp", "counter",
     "\t\t\tconstexpr auto CounterSize = 16+1;\n"
     "\t\t\tm_RunningQuestState->_counter_name.reserve(CounterSize);\n"
     "\t\t\tbuf.write(m_RunningQuestState->_counter_name.c_str(), CounterSize);\n",
     "\t\t\tconstexpr auto CounterSize = 16+1;\n"
     "\t\t\t// %s (counter): the counter's name in the reader's language\n"
     "\t\t\tchar counterName[CounterSize];\n"
     "\t\t\tMt2009QuestInfoText(CQuestManager::instance().GetCurrentCharacterPtr(), m_RunningQuestState->_counter_name, counterName, sizeof(counterName));\n"
     "\t\t\tbuf.write(counterName, CounterSize);\n" % Q),
    ("desc.cpp", "packet",
     "\t\t\tc_pvData = buffer_read_peek(m_lpBufferedOutputBuffer);\n"
     "\t\t\tiSize = buffer_size(m_lpBufferedOutputBuffer);\n"
     "\t\t}\n",
     "\t\t\tc_pvData = buffer_read_peek(m_lpBufferedOutputBuffer);\n"
     "\t\t\tiSize = buffer_size(m_lpBufferedOutputBuffer);\n"
     "\t\t}\n"
     "\t\t// %s (packet): a text packet's Polish words without diacritics for a client whose code page is not\n"
     "\t\t// cp1250 (mt2009_language.cpp); the packet itself for anything else.\n"
     "\t\t{ const void* Mt2009LanguagePacketOut(LPCHARACTER, const void*, int); c_pvData = Mt2009LanguagePacketOut(GetCharacter(), c_pvData, iSize); }\n" % Q),
]


def main():
    edits = []
    for f, tag, old, new in EDITS:
        marker = "%s (%s)" % (Q if Q in new else M, tag)
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
        print("language: %d edits, %d anchors wrong" % (len(edits), bad))
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
