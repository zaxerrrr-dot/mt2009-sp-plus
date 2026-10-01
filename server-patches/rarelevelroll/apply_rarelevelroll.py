#!/usr/bin/env python3
"""apply_rarelevelroll.py <engine game/src dir> -- Linux/VPS twin of
Apply-RareLevelRollPatch.ps1 (same replacement, same marker).
A 6th/7th bonus (CItem::AddRareAttribute: Seon-Hae and the Enchant 71051)
rolls its level lv1..lv5 by the odds in the event flags m2_rare_lv1..5
(the admin panel's Seon-Hae page; all zero = 35/30/20/10/5, the owner,
1 October 2026), never above the bonus's max level for the item type. It
always took level 5 before. An item type with no bonus left returns false
instead of reading past an empty list. Applied once; a file without the
expected code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_RARE_LEVEL_ROLL_V1"
OLD = ("\tconst TItemAttrTable& r = g_map_itemRare[avail[number(0, avail.size() - 1)]];\n"
       "\tint nAttrLevel = 5;\n")
NEW = ("\t// " + MARK + " (server-patches/rarelevelroll): nothing left to add is a\n"
       "\t// refusal, and the level is rolled by the panel's odds (m2_rare_lv1..5).\n"
       "\tif (avail.empty())\n"
       "\t\treturn false;\n"
       "\tconst TItemAttrTable& r = g_map_itemRare[avail[number(0, avail.size() - 1)]];\n"
       "\tint nAttrLevel = 5;\n"
       "\t{\n"
       "\t\tstatic const int s_aiDefault[5] = { 35, 30, 20, 10, 5 };\n"
       "\t\tint aiPct[5];\n"
       "\t\tint iTotal = 0;\n"
       "\t\tfor (int i = 0; i < 5; ++i)\n"
       "\t\t{\n"
       "\t\t\tchar szFlag[16];\n"
       "\t\t\tsnprintf(szFlag, sizeof(szFlag), \"m2_rare_lv%d\", i + 1);\n"
       "\t\t\taiPct[i] = MAX(0, quest::CQuestManager::instance().GetEventFlag(szFlag));\n"
       "\t\t\tiTotal += aiPct[i];\n"
       "\t\t}\n"
       "\t\tif (iTotal <= 0)\n"
       "\t\t{\n"
       "\t\t\tfor (int i = 0; i < 5; ++i)\n"
       "\t\t\t\taiPct[i] = s_aiDefault[i];\n"
       "\t\t\tiTotal = 100;\n"
       "\t\t}\n"
       "\t\tint iRoll = number(1, iTotal);\n"
       "\t\tfor (nAttrLevel = 1; nAttrLevel < 5 && iRoll > aiPct[nAttrLevel - 1]; ++nAttrLevel)\n"
       "\t\t\tiRoll -= aiPct[nAttrLevel - 1];\n"
       "\t}\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "item_attribute.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("rarelevelroll: item_attribute.cpp already applied")
        return
    crlf = "\r\n" in text
    o, n = (OLD.replace("\n", "\r\n"), NEW.replace("\n", "\r\n")) if crlf else (OLD, NEW)
    if text.count(o) != 1:
        sys.exit("rarelevelroll: expected code not found in " + path + " -- nothing changed")
    open(path, "wb").write(text.replace(o, n, 1).encode("latin-1"))
    print("rarelevelroll: item_attribute.cpp applied")


if __name__ == "__main__":
    main()
