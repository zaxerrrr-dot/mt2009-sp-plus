#!/usr/bin/env python3
"""apply_dungeonhp.py <engine game/src dir> -- Linux/VPS twin of
Apply-DungeonHpPatch.ps1 (same replacements, same marker).
Two quest functions for a dungeon's own monster health (the owner, 2 October,
the Biblioteka Wiedzy): d.count_players() - the players (bots included) in
the selected instance - and d.mob_hp_percent(vnum, percent) - every living
monster or stone of that vnum in the instance gets its max HP times percent
and keeps its share of health; it answers how many. The world's copies of
the same vnum are untouched, and the world-health flag (server-patches/mobhp)
leaves a monster rescaled here alone. Applied once; a file without the
expected code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_DUNGEON_MOB_HP_V1"
FUNCS = (
    "\t// " + MARK + " (server-patches/dungeonhp): the players in the selected\n"
    "\t// instance, bots included - a dungeon sizes its boss by them.\n"
    "\tALUA(dungeon_count_players)\n"
    "\t{\n"
    "\t\tCQuestManager& q = CQuestManager::instance();\n"
    "\t\tLPDUNGEON pDungeon = q.GetCurrentDungeon();\n"
    "\t\tint n = 0;\n"
    "\t\tif (pDungeon)\n"
    "\t\t{\n"
    "\t\t\tconst long lMapIndex = pDungeon->GetMapIndex();\n"
    "\t\t\tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())\n"
    "\t\t\t{\n"
    "\t\t\t\tLPCHARACTER ch = kv.second;\n"
    "\t\t\t\tif (ch && ch->IsPC() && ch->GetMapIndex() == lMapIndex)\n"
    "\t\t\t\t\t++n;\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t\tlua_pushnumber(L, n);\n"
    "\t\treturn 1;\n"
    "\t}\n"
    "\n"
    "\t// " + MARK + " (percent): d.mob_hp_percent(vnum, percent) - every living\n"
    "\t// monster or stone of the vnum in the instance, max HP times percent\n"
    "\t// (1..1000), its share of health kept. The real point moves too, so the\n"
    "\t// world-health flag (MT2009_PLUS_MOB_HP_V1) sees it set by somebody else.\n"
    "\tALUA(dungeon_mob_hp_percent)\n"
    "\t{\n"
    "\t\tCQuestManager& q = CQuestManager::instance();\n"
    "\t\tLPDUNGEON pDungeon = q.GetCurrentDungeon();\n"
    "\t\tif (!pDungeon || !lua_isnumber(L, 1) || !lua_isnumber(L, 2))\n"
    "\t\t{\n"
    "\t\t\tlua_pushnumber(L, 0);\n"
    "\t\t\treturn 1;\n"
    "\t\t}\n"
    "\t\tconst DWORD dwVnum = (DWORD) lua_tonumber(L, 1);\n"
    "\t\tconst int iPct = MINMAX(1, (int) lua_tonumber(L, 2), 1000);\n"
    "\t\tconst long lMapIndex = pDungeon->GetMapIndex();\n"
    "\t\tint n = 0;\n"
    "\t\tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())\n"
    "\t\t{\n"
    "\t\t\tLPCHARACTER ch = kv.second;\n"
    "\t\t\tif (!ch || ch->IsPC() || ch->IsDead() || ch->GetRaceNum() != dwVnum || ch->GetMapIndex() != lMapIndex)\n"
    "\t\t\t\tcontinue;\n"
    "\t\t\tconst int oldMax = ch->GetMaxHP();\n"
    "\t\t\tif (oldMax <= 0)\n"
    "\t\t\t\tcontinue;\n"
    "\t\t\tconst int hp = ch->GetHP();\n"
    "\t\t\tlong long newMax = (long long) oldMax * iPct / 100;\n"
    "\t\t\tif (newMax < 1)\n"
    "\t\t\t\tnewMax = 1;\n"
    "\t\t\tif (newMax > INT_MAX)\n"
    "\t\t\t\tnewMax = INT_MAX;\n"
    "\t\t\tch->SetRealPoint(POINT_MAX_HP, (int) newMax);\n"
    "\t\t\tch->PointChange(POINT_MAX_HP, 0);\n"
    "\t\t\tconst int max = ch->GetMaxHP();\n"
    "\t\t\tlong long newHp = (long long) hp * max / oldMax;\n"
    "\t\t\tif (hp > 0 && newHp < 1)\n"
    "\t\t\t\tnewHp = 1;\n"
    "\t\t\tif (newHp > max)\n"
    "\t\t\t\tnewHp = max;\n"
    "\t\t\tch->SetHP((int) newHp);\n"
    "\t\t\tch->BroadcastTargetPacket();\n"
    "\t\t\t++n;\n"
    "\t\t}\n"
    "\t\tsys_log(0, \"DUNGEON_MOB_HP: map %ld vnum %u x%d%%, %d rescaled\", lMapIndex, dwVnum, iPct, n);\n"
    "\t\tlua_pushnumber(L, n);\n"
    "\t\treturn 1;\n"
    "\t}\n"
    "\n"
)
EDITS = [
    ("questlua_dungeon.cpp",
     "\tALUA(dungeon_spawn_mob)\n\t{\n",
     FUNCS + "\tALUA(dungeon_spawn_mob)\n\t{\n"),
    ("questlua_dungeon.cpp",
     "\t\t\t{ \"spawn_mob\",\t\tdungeon_spawn_mob\t},\n",
     "\t\t\t{ \"spawn_mob\",\t\tdungeon_spawn_mob\t},\n"
     "\t\t\t{ \"count_players\",\tdungeon_count_players\t},\t// " + MARK + " (register)\n"
     "\t\t\t{ \"mob_hp_percent\",\tdungeon_mob_hp_percent\t},\n"),
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
            sys.exit("dungeonhp: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("dungeonhp: %s applied" % os.path.basename(path))
        else:
            print("dungeonhp: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
