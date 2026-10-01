#!/usr/bin/env python3
"""apply_soulstonewait.py <engine game/src dir> -- Linux/VPS twin of
Apply-SoulStoneWaitPatch.ps1 (same replacements, same marker).
The wait between two Soul Stones (Kamien Duchowy, 50513, G1 -> P) follows the
world's difficulty like the skill books' wait (the event flag m2_book_wait):
easy none, medium 7 h, hard 12 h as the package, custom the books' hours - at
most the package's 12 hours every time. The package's
training_grandmaster_skill.quest keeps its next_time flag at twelve hours; the
engine's pc.getqf/pc.setqf cap that one flag at now plus the world's wait, so a
wait already stored on a character shortens at the next stone. The bots' own
wait is playerbot_config.h's GetPlayerBotSoulStoneWaitSeconds (the overlay).
Applied once; a file without the expected code stops with an error, changing
nothing."""
import os
import sys

MARK = "MT2009_PLUS_SOUL_STONE_WAIT_V1"
EDITS = [
    ("char_skill.cpp",
     "\treturn wait > 0 ? wait : SKILLBOOK_LEARN_DELAY;\n}\n",
     "\treturn wait > 0 ? wait : SKILLBOOK_LEARN_DELAY;\n}\n"
     "\n"
     "// " + MARK + " (server-patches/soulstonewait): the wait between two Soul\n"
     "// Stones (G1 -> P) is the books' wait, at most the package's 12 hours.\n"
     "int M2SoulStoneWait()\n"
     "{\n"
     "\tconst int wait = M2SkillBookLearnDelay();\n"
     "\treturn wait <= 0 ? 0 : (wait > 12 * 3600 ? 12 * 3600 : wait);\n"
     "}\n"),
    ("questlua_pc.cpp",
     "const int ITEM_BROKEN_METIN_VNUM = 28960;\n",
     "const int ITEM_BROKEN_METIN_VNUM = 28960;\n"
     "\n"
     "// " + MARK + " (declare): training_grandmaster_skill.quest's next_time,\n"
     "// never later than the world's Soul Stone wait from now (char_skill.cpp).\n"
     "extern int M2SoulStoneWait();\n"
     "static int M2SoulStoneQuestFlag(const std::string& flag, int value)\n"
     "{\n"
     "\tif (flag != \"training_grandmaster_skill.next_time\")\n"
     "\t\treturn value;\n"
     "\tconst int cap = get_global_time() + M2SoulStoneWait();\n"
     "\treturn value > cap ? cap : value;\n"
     "}\n"),
    ("questlua_pc.cpp",
     "\t\t\tlua_pushnumber(L,pPC->GetFlag(pPC->GetCurrentQuestName() + \".\"+sz));\n",
     "\t\t\t// " + MARK + " (get)\n"
     "\t\t\tconst std::string qf = pPC->GetCurrentQuestName() + \".\" + sz;\n"
     "\t\t\tlua_pushnumber(L, M2SoulStoneQuestFlag(qf, pPC->GetFlag(qf)));\n"),
    ("questlua_pc.cpp",
     "\t\t\tpPC->SetFlag(pPC->GetCurrentQuestName()+\".\"+sz, int(rint(lua_tonumber(L,2))));\n",
     "\t\t\t// " + MARK + " (set)\n"
     "\t\t\tconst std::string qf = pPC->GetCurrentQuestName() + \".\" + sz;\n"
     "\t\t\tpPC->SetFlag(qf, M2SoulStoneQuestFlag(qf, int(rint(lua_tonumber(L,2)))));\n"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    files = {}
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        if path not in files:
            files[path] = open(path, "rb").read().decode("latin-1")
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        text = files[path]
        marked = [l for l in new.split("\n") if MARK in l]
        if marked and marked[0] in text.replace("\r\n", "\n"):
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("soulstonewait: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("soulstonewait: %s applied" % os.path.basename(path))
        else:
            print("soulstonewait: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
