#!/usr/bin/env python3
"""apply_dungeonhp.py <engine game/src dir> -- Linux/VPS twin of
Apply-DungeonHpPatch.ps1 (same replacements, same marker).
Two quest functions for a dungeon's own monster health (the owner, 2 October,
the Biblioteka Wiedzy): d.count_players() - the players (bots included) in
the selected instance - and d.mob_hp_percent(vnum, percent) - every living
monster or stone of that vnum in the instance gets its max HP times percent
and keeps its share of health; it answers how many. The world's copies of
the same vnum are untouched, and the world-health flag (server-patches/mobhp)
leaves a monster rescaled here alone. MT2009_PLUS_DUNGEON_MOB_HP_V2 (the owner,
2 October): a monster raised here heals as many points a tick as before it - its
regen_percent counts from the max HP it had before the first raise (char.cpp,
the monsters' recovery); a lowered one heals a percent of its new max HP. Applied once; a file without the
expected code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_DUNGEON_MOB_HP_V1"
MARK2 = "MT2009_PLUS_DUNGEON_MOB_HP_V2"
REGEN_HELPERS = (
    "// " + MARK2 + " (server-patches/dungeonhp): a monster whose max HP a\n"
    "// dungeon rescaled (d.mob_hp_percent) heals as many points a tick as it did\n"
    "// before: the max HP it had before the first rescale, by its VID.\n"
    "static std::unordered_map<DWORD, int> s_mapM2RegenBaseMaxHP;\n"
    "\n"
    "void M2SetRegenBaseMaxHP(DWORD dwVID, int iBaseMaxHP)\n"
    "{\n"
    "\tif (iBaseMaxHP > 0)\n"
    "\t\ts_mapM2RegenBaseMaxHP.emplace(dwVID, iBaseMaxHP);\n"
    "}\n"
    "\n"
    "static int M2RegenMaxHP(const CHARACTER* ch)\n"
    "{\n"
    "\tif (!s_mapM2RegenBaseMaxHP.empty())\n"
    "\t{\n"
    "\t\tauto it = s_mapM2RegenBaseMaxHP.find((DWORD) ch->GetVID());\n"
    "\t\tif (it != s_mapM2RegenBaseMaxHP.end())\n"
    "\t\t\treturn it->second;\n"
    "\t}\n"
    "\treturn ch->GetMaxHP();\n"
    "}\n"
    "\n"
)
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


EDITS += [
    ("questlua_dungeon.cpp",
     "\ntemplate <class Func> Func CDungeon::ForEachMember(Func f)\n",
     "\n// " + MARK2 + " (declare): char.cpp, server-patches/dungeonhp.\n"
     "extern void M2SetRegenBaseMaxHP(DWORD dwVID, int iBaseMaxHP);\n"
     "\ntemplate <class Func> Func CDungeon::ForEachMember(Func f)\n"),
    ("questlua_dungeon.cpp",
     "\t\t\tconst int hp = ch->GetHP();\n\t\t\tlong long newMax = (long long) oldMax * iPct / 100;\n",
     "\t\t\tconst int hp = ch->GetHP();\n"
     "\t\t\tif (iPct > 100)\t// " + MARK2 + " (base): a raised one only\n"
     "\t\t\t\t::M2SetRegenBaseMaxHP((DWORD) ch->GetVID(), oldMax);\n"
     "\t\t\tlong long newMax = (long long) oldMax * iPct / 100;\n"),
    ("char.cpp",
     "void CHARACTER::Destroy()\n{\n",
     REGEN_HELPERS + "void CHARACTER::Destroy()\n{\n"
     "\ts_mapM2RegenBaseMaxHP.erase((DWORD) GetVID());\t// " + MARK2 + " (destroy)\n"),
    ("char.cpp",
     "\t\t\tch->MonsterLog(\"HP_REGEN +%d\", MAX(1, (ch->GetMaxHP() * ch->GetMobTable().bRegenPercent) / 100));\n"
     "\t\t\tch->PointChange(POINT_HP, MAX(1, (ch->GetMaxHP() * ch->GetMobTable().bRegenPercent) / 100));\n",
     "\t\t\t// " + MARK2 + " (regen): the max HP before a dungeon's rescale.\n"
     "\t\t\tconst int iRegenMaxHP = M2RegenMaxHP(ch);\n"
     "\t\t\tch->MonsterLog(\"HP_REGEN +%d\", MAX(1, (iRegenMaxHP * ch->GetMobTable().bRegenPercent) / 100));\n"
     "\t\t\tch->PointChange(POINT_HP, MAX(1, (iRegenMaxHP * ch->GetMobTable().bRegenPercent) / 100));\n"),
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
        marked = [l for l in new.split("\n") if MARK in l or MARK2 in l]
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
