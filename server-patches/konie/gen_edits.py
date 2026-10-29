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

# 1-21: the wiki's INT column (ours had 0); STR / DEX / VIT as they were (the wiki's level 3 STR 27 and level 20 DEX 63
# are one under the level before - kept ours, 28 and 64)
WIKI_IQ = {1: 9, 2: 9, 3: 9, 4: 10, 5: 10, 6: 10, 7: 11, 8: 11, 9: 11, 10: 12, 11: 13, 12: 14, 13: 14, 14: 14, 15: 15,
           16: 15, 17: 15, 18: 15, 19: 16, 20: 16, 21: 18}
LOW_ROWS = [
    (25, 20101, 3, 4, 26, 35, 18, 0, 54, 43, 64, 32), (25, 20101, 4, 4, 27, 36, 18, 0, 55, 44, 66, 33),
    (25, 20101, 5, 5, 28, 38, 19, 0, 56, 44, 67, 33), (25, 20101, 7, 5, 29, 39, 19, 0, 57, 45, 68, 34),
    (25, 20101, 8, 6, 30, 40, 20, 0, 58, 46, 69, 34), (25, 20101, 9, 6, 31, 41, 21, 0, 59, 47, 70, 35),
    (25, 20101, 11, 7, 32, 42, 21, 0, 60, 48, 72, 36), (25, 20101, 12, 7, 33, 44, 22, 0, 61, 48, 73, 36),
    (25, 20101, 13, 8, 34, 45, 22, 0, 62, 49, 74, 37), (25, 20101, 15, 10, 35, 46, 23, 0, 63, 50, 75, 37),
    (35, 20104, 18, 30, 40, 53, 27, 0, 69, 55, 82, 41), (35, 20104, 19, 35, 41, 54, 27, 0, 70, 56, 84, 42),
    (35, 20104, 21, 40, 42, 56, 28, 0, 71, 56, 85, 42), (35, 20104, 22, 50, 43, 57, 28, 0, 72, 57, 86, 43),
    (35, 20104, 24, 55, 44, 58, 29, 0, 73, 58, 87, 43), (35, 20104, 25, 60, 44, 59, 30, 0, 74, 59, 88, 44),
    (35, 20104, 27, 65, 45, 60, 30, 0, 75, 60, 90, 45), (35, 20104, 28, 70, 46, 62, 31, 0, 76, 60, 91, 45),
    (35, 20104, 30, 80, 47, 63, 31, 0, 77, 61, 92, 46), (35, 20104, 32, 100, 48, 64, 32, 0, 78, 62, 93, 46),
    (50, 20107, 35, 120, 53, 71, 36, 0, 84, 67, 100, 50),
]


def low_row(r, lv, iq):
    c = list(r)
    c[7] = iq
    sep = "\t" if c[3] >= 100 else "\t\t"     # the source's columns (a 3-digit stamina takes one tab)
    return "\t{ %d,\t%d,\t%d,\t%d,%s%s }" % (c[0], c[1], c[2], c[3], sep, ",\t".join(str(x) for x in c[4:]))


def low_text(iqs):
    out = []
    for i, r in enumerate(LOW_ROWS):
        lv = i + 1
        line = low_row(r, lv, iqs[lv]) + ","
        if lv in (1, 11, 21):
            line += " // %d" % lv
        out.append(line)
    return "\n".join(out) + "\n"


old_low = low_text(dict((lv, 0) for lv in range(1, 22)))
new_low = low_text(WIKI_IQ).replace(" // 1\n", " // 1 - MT2009_PLUS_HORSE40_V1 (stats 1-21): the pl-wiki's INT\n", 1)
edit("horse_rider.cpp", "stats 1-21", old_low, new_low)

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
edit("char.cpp", "floors",
     "\t\t{\n\t\t\tif (GetHorseST() > GetPoint(POINT_ST))\n\t\t\t\tPointChange(POINT_ST, GetHorseST() - GetPoint(POINT_ST));\n\n"
     "\t\t\tif (GetHorseDX() > GetPoint(POINT_DX))\n\t\t\t\tPointChange(POINT_DX, GetHorseDX() - GetPoint(POINT_DX));\n\n"
     "\t\t\tif (GetHorseHT() > GetPoint(POINT_HT))\n\t\t\t\tPointChange(POINT_HT, GetHorseHT() - GetPoint(POINT_HT));\n\n"
     "\t\t\tif (GetHorseIQ() > GetPoint(POINT_IQ))\n\t\t\t\tPointChange(POINT_IQ, GetHorseIQ() - GetPoint(POINT_IQ));\n\t\t}\n",
     "\t\t{\n\t\t\t// MT2009_PLUS_HORSE40_V1 (floors): the wiki's table is the LEAST a rider has of each stat - max(own, table),\n"
     "\t\t\t// never on top. It is taken after the equipment (Mt2009KonieComputePoints below, konie_rozwoj.cpp), so the\n"
     "\t\t\t// worn items count as the rider's own; here nothing any more.\n\t\t}\n")
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
MSG_PREMIUM = "Pot\\352\\277ny Ko\\361 Wojskowy je tylko Czer. \\257e\\361-sze\\361 (premium)."
edit("char_item.cpp", "can feed",
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3)\n",
     "\t\t// MT2009_PLUS_HORSE40_V1 (can feed): the Black Steed (30) eats Czerwony Zen-szen; Potezny Kon Wojskowy - a horse\n"
     "\t\t// of 31+, whatever its look - only Czer. Zen-szen (premium) 50047 (the wiki; the owner, 30 October 2026)\n"
     "\t\tcase 20119:\n\t\tcase 20149:\n\t\tcase 20150:\n\t\tcase 20151:\n"
     "\t\t\t{\n"
     "\t\t\t\tconst DWORD dwKonieFood = from->GetHorseLevel() >= 31 ? 50047 : ITEM_HORSE_FOOD_3;\n"
     "\t\t\t\tif (item->GetVnum() == dwKonieFood)\n\t\t\t\t{\n"
     "\t\t\t\t\tif (IsDead())\n\t\t\t\t\t{\n"
     "\t\t\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, LC_TEXT(\"You cannot feed a dead Horse.\"));\n"
     "\t\t\t\t\t\treturn false;\n\t\t\t\t\t}\n\t\t\t\t\treturn true;\n\t\t\t\t}\n"
     "\t\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_1 || item->GetVnum() == ITEM_HORSE_FOOD_2 ||\n"
     "\t\t\t\t\t\titem->GetVnum() == ITEM_HORSE_FOOD_3 || item->GetVnum() == 50047)\n\t\t\t\t{\n"
     "\t\t\t\t\tif (dwKonieFood == 50047)\n"
     "\t\t\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, \"" + MSG_PREMIUM + "\");\n"
     "\t\t\t\t\treturn false;\n\t\t\t\t}\n\t\t\t}\n\t\t\tbreak;\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_3)\n")
edit("char_item.cpp", "feed",
     "\t\tcase 20101:\n\t\tcase 20102:\n\t\tcase 20103:\n\t\tcase 20104:\n\t\tcase 20105:\n\t\tcase 20106:\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_1 ||\n",
     "\t\t// MT2009_PLUS_HORSE40_V1 (feed): the Black Steed and Potezny Kon Wojskowy (CanReceiveItem above)\n"
     "\t\tcase 20119:\n\t\tcase 20149:\n\t\tcase 20150:\n\t\tcase 20151:\n"
     "\t\t\tif (item->GetVnum() == (from->GetHorseLevel() >= 31 ? 50047 : ITEM_HORSE_FOOD_3))\n\t\t\t{\n"
     "\t\t\t\tfrom->FeedHorse();\n"
     "\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, LC_TEXT(\"You have fed the Horse.\"));\n"
     "\t\t\t\titem->SetCount(item->GetCount()-1);\n\t\t\t\tEffectPacket(SE_HPUP_RED);\n\t\t\t}\n\t\t\tbreak;\n\n"
     "\t\tcase 20101:\n\t\tcase 20102:\n\t\tcase 20103:\n\t\tcase 20104:\n\t\tcase 20105:\n\t\tcase 20106:\n"
     "\t\tcase 20107:\n\t\tcase 20108:\n\t\tcase 20109:\n\t\t\tif (item->GetVnum() == ITEM_HORSE_FOOD_1 ||\n")
edit("questlua_horse.cpp", "feed",
     "\t\tif (ch->GetHorseLevel() > 0 && ch->GetHorseHealth() > 0)\n\t\t{\n\t\t\tch->FeedHorse();\n\t\t}\n",
     "\t\t// MT2009_PLUS_HORSE40_V1 (feed): a horse of 31+ eats only Czer. Zen-szen (premium) - horse.konie_karm (quest\n"
     "\t\t// konie_rozwoj). The stock horse_menu took its Czerwony Zen-szen (the grade's feed) before this: given back.\n"
     "\t\tif (ch->GetHorseLevel() >= 31)\n\t\t{\n"
     "\t\t\tch->ChatPacket(CHAT_TYPE_INFO, \"" + MSG_PREMIUM + "\");\n"
     "\t\t\tch->AutoGiveItem(50056, 1); // Czerwony Zen-szen (ITEM_HORSE_FOOD_3)\n\t\t\treturn 0;\n\t\t}\n"
     "\t\tif (ch->GetHorseLevel() > 0 && ch->GetHorseHealth() > 0)\n\t\t{\n\t\t\tch->FeedHorse();\n\t\t}\n")

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
