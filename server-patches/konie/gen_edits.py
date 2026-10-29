#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/konie (MT2009_PLUS_HORSE40_V1, README.md). Every "old" is the
test tree's code with LF line ends (apply_konie.py matches it with CRLF where the file has CRLF); each edit carries
its own marker in "new" so a second run of apply_konie.py skips it. Rerun after a change and apply on a clean tree."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_HORSE40_V1"
edits = []


def edit(f, tag, old, new):
    marker = "%s (%s)" % (M, tag)
    assert marker in new, marker
    edits.append({"file": f, "marker": marker, "old": old, "new": new})


# ---------------------------------------------------------------- horse_rider.h / .cpp: levels 31-40, the wiki's stats
edit("horse_rider.h", "max level",
     "const int HORSE_MAX_LEVEL = 30;",
     "const int HORSE_MAX_LEVEL = 40; // MT2009_PLUS_HORSE40_V1 (max level): the wiki's 40 (server-patches/konie)")

OLD_ROWS = [
    (36, 125, 55, 74, 37, 0, 86, 68, 103, 51),
    (37, 130, 57, 76, 38, 0, 88, 70, 105, 52),
    (38, 135, 59, 78, 39, 0, 90, 72, 108, 54),
    (40, 140, 60, 80, 40, 0, 91, 72, 109, 54),
    (42, 145, 61, 81, 40, 0, 92, 73, 110, 55),
    (44, 150, 62, 83, 42, 0, 94, 75, 112, 56),
    (46, 160, 63, 84, 42, 0, 95, 76, 114, 57),
    (48, 170, 65, 87, 43, 0, 97, 77, 116, 58),
    (50, 200, 67, 89, 45, 0, 99, 79, 118, 59),
]
# the wiki ("Zmiana punktow statusu na roznych poziomach konia": VIT, INT, STR, DEX) for 22-30; health, stamina,
# damage and armour as they were
WIKI = {22: (37, 18, 55, 74), 23: (38, 19, 57, 76), 24: (39, 20, 60, 78), 25: (40, 20, 61, 80), 26: (40, 20, 61, 81),
        27: (42, 21, 62, 83), 28: (42, 21, 63, 84), 29: (43, 22, 65, 87), 30: (63, 61, 67, 90)}


def row(r):
    return "\t{ 50,\t20107,\t%s }" % ",\t".join(str(x) for x in r)


old = ",\n".join(row(r) for r in OLD_ROWS) + "\n};\n"
new_rows = []
for i, r in enumerate(OLD_ROWS):
    lv = 22 + i
    ht, iq, st, dx = WIKI[lv]
    new_rows.append(row((r[0], r[1], st, dx, ht, iq) + r[6:]))
# 31-40: the package's health / stamina / damage / armour steps, the wiki's level 30 VIT and INT, STR and DEX
# rising as the package's (the Sung Ma of these levels: konie_rozwoj.cpp)
for i in range(10):
    new_rows.append(row((52 + 2 * i, 210 + 10 * i, 68 + i, 90 + 2 * i, 63, 61, 100 + i, 80 + i, 120 + i, 60 + i)))
new = (",\n".join(new_rows[:9]) + ", // 22-30: MT2009_PLUS_HORSE40_V1 (stats) - the pl-wiki's table\n"
       + ",\n".join(new_rows[9:]) + " // 31-40\n};\n")
edit("horse_rider.cpp", "stats", old, new)

edit("horse_rider.cpp", "grade",
     "\tif (GetHorseLevel())\n\t\tgrade = (GetHorseLevel() - 1) / 10 + 1;\n",
     "\tif (GetHorseLevel())\n\t\tgrade = (GetHorseLevel() - 1) / 10 + 1;\n"
     "\t// MT2009_PLUS_HORSE40_V1 (grade): 31-40 stay the military horse's grade (its book 50053, its feed and herb,\n"
     "\t// its skills) - Potezny Kon Wojskowy is a look (konie_rozwoj.cpp Mt2009KonieHorseVnum), not a fourth grade\n"
     "\tif (grade > 3)\n\t\tgrade = 3;\n")

# ---------------------------------------------------------------- char_horse.cpp
edit("char_horse.cpp", "horse vnum",
     "\tif (GetHorseLevel() >= 30)\n\t\treturn 20119;\n",
     "\t// MT2009_PLUS_HORSE40_V1 (horse vnum): Potezny Kon Wojskowy (20149-20151) for a horse of 31+ whose rider has\n"
     "\t// the Zlota Ksiega Konia (konie_rozwoj.cpp)\n"
     "\t{\n\t\tDWORD Mt2009KonieHorseVnum(const CHARACTER* ch, int delta);\n"
     "\t\tconst DWORD dwKonie = Mt2009KonieHorseVnum(this, delta);\n\t\tif (dwKonie)\n\t\t\treturn dwKonie;\n\t}\n"
     "\tif (GetHorseLevel() >= 30)\n\t\treturn 20119;\n")
edit("char_horse.cpp", "stop riding",
     "void CHARACTER::OnStopRiding()\n{\n",
     "void CHARACTER::OnStopRiding()\n{\n"
     "\t{ // MT2009_PLUS_HORSE40_V1 (stop riding): the riding horse skills' timed effects end (konie_rozwoj.cpp)\n"
     "\t\tvoid Mt2009KonieStopRiding(LPCHARACTER ch);\n\t\tMt2009KonieStopRiding(this);\n\t}\n")

# ---------------------------------------------------------------- char.cpp: ComputePoints
edit("char.cpp", "compute",
     "\t\tMt2009YSetsRefresh(this);\n\t}\n\n\tComputeBattlePoints();\n",
     "\t\tMt2009YSetsRefresh(this);\n\t}\n\n"
     "\t// MT2009_PLUS_HORSE40_V1 (compute): the Sung Ma minima of a horse of 31+ and the constant horse skills while\n"
     "\t// riding (konie_rozwoj.cpp)\n"
     "\t{ void Mt2009KonieComputePoints(LPCHARACTER ch); Mt2009KonieComputePoints(this); }\n\n"
     "\tComputeBattlePoints();\n")

# ---------------------------------------------------------------- char_battle.cpp
edit("char_battle.cpp", "damage",
     "\t// MT2009_PLUS_SUNGMA_V1 (damage): a person's blow at a monster of a Sung Ma map",
     "\t// MT2009_PLUS_HORSE40_V1 (damage): the horse skills - Niesmiertelnosc blocks, Jazda (umiej. konne) adds to a\n"
     "\t// horse skill's blow, a blow starts the timed ones (konie_rozwoj.cpp)\n"
     "\t{\n\t\tint Mt2009KonieDamage(LPCHARACTER, LPCHARACTER, int, DWORD);\n"
     "\t\tdam = Mt2009KonieDamage(this, pAttacker, dam, dwUsedSkill);\n\t\tif (dam < 0)\n\t\t{\n"
     "\t\t\tif (pAttacker)\n\t\t\t\tSendDamagePacket(pAttacker, 0, DAMAGE_BLOCK);\n\t\t\treturn false;\n\t\t}\n\t}\n\n"
     "\t// MT2009_PLUS_SUNGMA_V1 (damage): a person's blow at a monster of a Sung Ma map")
edit("char_battle.cpp", "push",
     "\tif (IsAffectFlag(AFF_SKILL_STRONG_BODY))\n\t\treturn true;\n",
     "\tif (IsAffectFlag(AFF_SKILL_STRONG_BODY))\n\t\treturn true;\n"
     "\t{ // MT2009_PLUS_HORSE40_V1 (push): Jazda (Brak Odrzutu) while it lasts (konie_rozwoj.cpp)\n"
     "\t\tbool Mt2009KonieResistPush(LPCHARACTER ch);\n\t\tif (Mt2009KonieResistPush(this))\n\t\t\treturn true;\n\t}\n")

# ---------------------------------------------------------------- char_skill.cpp: the mighty military horse's mount type
edit("char_skill.cpp", "mount type",
     "\t\tcase 20107: // normal military horse (no guild)\n",
     "\t\tcase 20149: // MT2009_PLUS_HORSE40_V1 (mount type): Potezny Kon Wojskowy (no guild) - the military horse's\n"
     "\t\tcase 20150: // (guild member)\n\t\tcase 20151: // (guild master)\n"
     "\t\tcase 20107: // normal military horse (no guild)\n")

# ---------------------------------------------------------------- char_item.cpp: feeding the horse of 30+
edit("char_item.cpp", "can feed",
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3)\n",
     "\t\t// MT2009_PLUS_HORSE40_V1 (can feed): the Black Steed (30) and Potezny Kon Wojskowy (31+) eat Czerwony\n"
     "\t\t// Zen-szen and Czer. Zen-szen (premium) 50047 (the wiki)\n"
     "\t\tcase 20119:\n\t\tcase 20149:\n\t\tcase 20150:\n\t\tcase 20151:\n"
     "\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3 || item->GetVnum() == 50047)\n\t\t\t{\n"
     "\t\t\t\tif (IsDead())\n\t\t\t\t{\n"
     "\t\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, LC_TEXT(\"You cannot feed a dead Horse.\"));\n"
     "\t\t\t\t\treturn false;\n\t\t\t\t}\n\t\t\t\treturn true;\n\t\t\t}\n"
     "\t\t\telse if (item->GetVnum() == ITEM_HORSE_FOOD_1 || item->GetVnum() == ITEM_HORSE_FOOD_2)\n"
     "\t\t\t{\n\t\t\t\treturn false;\n\t\t\t}\n\t\t\tbreak;\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3)\n")
edit("char_item.cpp", "feed",
     "\t\tcase 20101:\n\t\tcase 20102:\n\t\tcase 20103:\n\t\tcase 20104:\n\t\tcase 20105:\n\t\tcase 20106:\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_1 ||\n",
     "\t\t// MT2009_PLUS_HORSE40_V1 (feed): the Black Steed and Potezny Kon Wojskowy (CanReceiveItem above)\n"
     "\t\tcase 20119:\n\t\tcase 20149:\n\t\tcase 20150:\n\t\tcase 20151:\n"
     "\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3 || item->GetVnum() == 50047)\n\t\t\t{\n"
     "\t\t\t\tfrom->FeedHorse();\n"
     "\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, LC_TEXT(\"You have fed the Horse.\"));\n"
     "\t\t\t\titem->SetCount(item->GetCount()-1);\n\t\t\t\tEffectPacket(SE_HPUP_RED);\n\t\t\t}\n\t\t\tbreak;\n\n"
     "\t\tcase 20101:\n\t\tcase 20102:\n\t\tcase 20103:\n\t\tcase 20104:\n\t\tcase 20105:\n\t\tcase 20106:\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_1 ||\n")

# ---------------------------------------------------------------- item_manager.cpp: 50047 / 50046 drops
edit("item_manager.cpp", "drop",
     "\tint iAddRarePct = pkKiller->GetPoint(POINT_DROP_RARE);\n",
     "\t// MT2009_PLUS_HORSE40_V1 (drop): Czer. Zen-szen (premium) on the Sung Ma maps, Szlachetna Trawa from Ahtrin\n"
     "\t// Wielki Mistrz (konie_rozwoj.cpp)\n"
     "\t{ void Mt2009KonieDrop(LPCHARACTER, LPCHARACTER, std::vector<LPITEM>&); Mt2009KonieDrop(pkChr, pkKiller, vec_item); }\n\n"
     "\tint iAddRarePct = pkKiller->GetPoint(POINT_DROP_RARE);\n")

# ---------------------------------------------------------------- cmd.cpp: /konie_rozwoj
edit("cmd.cpp", "command declare",
     "struct command_info cmd_info[] =\n",
     "// MT2009_PLUS_HORSE40_V1 (command declare): \"/konie_rozwoj\" - the Stajenny's horse window (konie_rozwoj.cpp)\n"
     "ACMD(do_konie_rozwoj);\n"
     "struct command_info cmd_info[] =\n")
edit("cmd.cpp", "command table",
     "\t{ \"\\n\",\t\tNULL,\t\t\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t}\n};\n",
     "\t{ \"konie_rozwoj\",\tdo_konie_rozwoj,\t0,\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_HORSE40_V1 (command table)\n"
     "\t{ \"\\n\",\t\tNULL,\t\t\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t}\n};\n")

# ---------------------------------------------------------------- questlua_horse.cpp: horse.konie_*
edit("questlua_horse.cpp", "quest functions",
     "\t\tCQuestManager::instance().AddLuaFunctionTable(\"horse\", horse_functions);\n",
     "\t\tCQuestManager::instance().AddLuaFunctionTable(\"horse\", horse_functions);\n"
     "\t\t// MT2009_PLUS_HORSE40_V1 (quest functions): horse.konie_otworz / konie_naucz / konie_zapomnij / konie_slot /\n"
     "\t\t// konie_odswiez (konie_rozwoj.cpp; quest konie_rozwoj)\n"
     "\t\tvoid Mt2009KonieRegisterLua();\n\t\tMt2009KonieRegisterLua();\n")

# ---------------------------------------------------------------- cmd_gm.cpp: the GM panel's horse level
edit("cmd_gm.cpp", "gm panel",
     "value = MINMAX(0, value, 30); // HORSE_MAX_LEVEL, horse_rider.h",
     "value = MINMAX(0, value, HORSE_MAX_LEVEL); // MT2009_PLUS_HORSE40_V1 (gm panel): horse_rider.h")

json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1)
print("edits.json: %d edits" % len(edits))
