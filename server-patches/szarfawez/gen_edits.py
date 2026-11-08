#!/usr/bin/env python3
"""gen_edits.py [game/src] -- writes edits.json of server-patches/szarfawez (MT2009_PLUS_SASH_SERPENT_V1) and checks
every anchor is found exactly once in the given engine tree (default: the test tree, already patched by every other
server patch - szarfawez goes last; its anchors are ysets' and zywiolbroni's code)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/game/src"
M = "MT2009_PLUS_SASH_SERPENT_V1"

edits = []


def edit(file, tag, old, new):
    edits.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# 1. a sash keeps a yextra too (read when it is loaded, saved when it changes): the absorbed serpent piece's three
#    random base bonuses (bits 8-31, as the piece had them)
edit("item.cpp", "tracked",
     "static bool Mt2009YSetsTracked(LPITEM item)\n"
     "{\n"
     "\tint iKind, iLevel;\n"
     "\treturn Mt2009YSetsPart(item) != 0 || Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel);\n"
     "}\n",
     "// MT2009_PLUS_SASH_SERPENT_V1 (tracked): a sash (Szarfa) keeps the random base bonuses of the serpent weapon or armour\n"
     "// it absorbed in its own yextra (bits 8-31, the piece's bytes as they were; bits 0-7 unused on a sash) - the owner,\n"
     "// 8 Nov 2026: \"Bronie wezowe po absorpcji bonusow do szarfy nie daja bonusow ktore sa wbudowane w bron\". The sash\n"
     "// gives them at its absorption rate (CalcAcceBonus), at the absorbed piece's refine level (ACCE_ABSORBED_SOCKET).\n"
     "static bool Mt2009YSetsIsSash(LPITEM item)\n"
     "{\n"
     "\treturn item && item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_ACCE;\n"
     "}\n"
     "\n"
     "static bool Mt2009YSetsTracked(LPITEM item)\n"
     "{\n"
     "\tint iKind, iLevel;\n"
     "\treturn Mt2009YSetsPart(item) != 0 || Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel) || Mt2009YSetsIsSash(item);\n"
     "}\n")

# 2. the sash's absorbed family, the lines of a sash absorbed before this fix (its piece's bytes were lost - rolled
#    once, as a serpent piece made before its bonuses existed is), and the detach
edit("item.cpp", "helpers",
     "// ITEM_MANAGER::CreateItem: a loaded item gets its yextra back, a new serpent piece rolls its three bonuses\n",
     "// MT2009_PLUS_SASH_SERPENT_V1 (helpers): the serpent family of the piece a sash absorbed (the hood is a helmet: never)\n"
     "static bool Mt2009YSetsSashFamily(LPITEM sash, int& iKind, int& iLevel)\n"
     "{\n"
     "\tconst long lVnum = sash->GetSocket(ACCE_ABSORBED_SOCKET);\n"
     "\tif (lVnum <= 0 || !Mt2009YSetsRandomFamily((DWORD) lVnum, iKind, iLevel))\n"
     "\t\treturn false;\n"
     "\treturn iKind != YSETS_HOOD_KIND;\n"
     "}\n"
     "\n"
     "// a sash that absorbed a serpent piece before MT2009_PLUS_SASH_SERPENT_V1 has no lines (the piece and its yextra are\n"
     "// gone): it rolls them once, for the absorbed piece's kind - before its points are added, never while they are on\n"
     "static void Mt2009YSetsSashLegacy(LPITEM sash)\n"
     "{\n"
     "\tint iKind, iLevel;\n"
     "\tif (!Mt2009YSetsIsSash(sash) || !sash->GetID() || (sash->GetYExtra() >> 8) || !Mt2009YSetsSashFamily(sash, iKind, iLevel))\n"
     "\t\treturn;\n"
     "\tMt2009YSetsRoll(sash, iKind);\n"
     "\tMt2009YSetsSave(sash);\n"
     "\tsys_log(0, \"SASH_SERPENT: sash %u (absorbed %ld) had no lines - rolled %08x\", sash->GetID(),\n"
     "\t\t\tsash->GetSocket(ACCE_ABSORBED_SOCKET), sash->GetYExtra());\n"
     "\tif (sash->GetOwner() && (sash->GetWindow() == INVENTORY || sash->GetWindow() == EQUIPMENT))\n"
     "\t\tMt2009YSetsNotify(sash->GetOwner(), 1, sash->GetCell(), sash->GetYExtra());\n"
     "}\n"
     "\n"
     "// char.cpp CleanAcceAttr (USE_DETACHMENT on a sash): the absorbed piece goes, its lines with it\n"
     "void Mt2009YSetsSashClear(LPITEM sash)\n"
     "{\n"
     "\tif (!Mt2009YSetsIsSash(sash) || !(sash->GetYExtra() >> 8))\n"
     "\t\treturn;\n"
     "\tsash->SetYExtra(sash->GetYExtra() & 0xFFU);\n"
     "\tMt2009YSetsSave(sash);\n"
     "\tif (sash->GetOwner() && (sash->GetWindow() == INVENTORY || sash->GetWindow() == EQUIPMENT))\n"
     "\t\tMt2009YSetsNotify(sash->GetOwner(), 1, sash->GetCell(), sash->GetYExtra());\n"
     "}\n"
     "\n"
     "// ITEM_MANAGER::CreateItem: a loaded item gets its yextra back, a new serpent piece rolls its three bonuses\n")

# 3. the absorption (CopyAttributeTo of the piece onto the sash, before ACCE_ABSORBED_SOCKET is set) and a combine
#    (CopyAllAttrTo of the first sash onto the new one): the lines go onto the sash
edit("item.cpp", "copy",
     "\tif (!pFrom || !pTo || pFrom == pTo || !pFrom->GetYExtra() || !Mt2009YSetsTracked(pTo))\n"
     "\t\treturn;\n"
     "\tint iKindFrom, iKindTo, iLevel;\n",
     "\tif (!pFrom || !pTo || pFrom == pTo || !pFrom->GetYExtra() || !Mt2009YSetsTracked(pTo))\n"
     "\t\treturn;\n"
     "\tif (Mt2009YSetsIsSash(pTo)) // MT2009_PLUS_SASH_SERPENT_V1 (copy): a serpent piece absorbed, a sash combined\n"
     "\t{\n"
     "\t\tint iKindSash, iLevelSash;\n"
     "\t\tif (!Mt2009YSetsIsSash(pFrom) && (!Mt2009YSetsRandomFamily(pFrom->GetVnum(), iKindSash, iLevelSash) || iKindSash == YSETS_HOOD_KIND))\n"
     "\t\t\treturn;\n"
     "\t\tconst DWORD dwSash = (pTo->GetYExtra() & 0xFFU) | (pFrom->GetYExtra() & ~0xFFU);\n"
     "\t\tif (dwSash == pTo->GetYExtra())\n"
     "\t\t\treturn;\n"
     "\t\tpTo->SetYExtra(dwSash);\n"
     "\t\tMt2009YSetsSave(pTo);\n"
     "\t\tif (pTo->GetOwner() && (pTo->GetWindow() == INVENTORY || pTo->GetWindow() == EQUIPMENT))\n"
     "\t\t\tMt2009YSetsNotify(pTo->GetOwner(), 1, pTo->GetCell(), dwSash);\n"
     "\t\treturn;\n"
     "\t}\n"
     "\tint iKindFrom, iKindTo, iLevel;\n")

# 4. the points: a sash gives the absorbed piece's three lines at its absorption rate
edit("item.cpp", "points",
     "\tint iKind, iLevel;\n"
     "\tif (!owner || !item->GetYExtra() || !Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))\n"
     "\t\treturn;\n",
     "\tint iKind, iLevel;\n"
     "\tconst bool bSash = Mt2009YSetsIsSash(item); // MT2009_PLUS_SASH_SERPENT_V1 (points): the absorbed piece's lines\n"
     "\tif (bSash)\n"
     "\t{\n"
     "\t\tif (!owner || !Mt2009YSetsSashFamily(item, iKind, iLevel))\n"
     "\t\t\treturn;\n"
     "\t\tif (bAdd)\n"
     "\t\t\tMt2009YSetsSashLegacy(item);\n"
     "\t\tif (!(item->GetYExtra() >> 8))\n"
     "\t\t\treturn;\n"
     "\t}\n"
     "\telse if (!owner || !item->GetYExtra() || !Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))\n"
     "\t\treturn;\n")
edit("item.cpp", "points value",
     "\t\tconst int iValue = o.asValue[iRow][iLevel];\n",
     "\t\tint iValue = o.asValue[iRow][iLevel];\n"
     "\t\tif (bSash) // MT2009_PLUS_SASH_SERPENT_V1 (points value): at the sash's absorption rate, as its other absorbed lines\n"
     "\t\t{\n"
     "\t\t\tiValue = item->CalcAcceBonus(iValue);\n"
     "#ifdef USE_ACCE_ABSORB_WITH_NO_NEGATIVE_BONUS\n"
     "\t\t\tif (iValue < 0)\n"
     "\t\t\t\tcontinue;\n"
     "#endif\n"
     "\t\t}\n")

# 5. the entry to the game and "/yitem": a sash of the bag absorbed before this fix gets its lines for the tooltip
edit("item.cpp", "send all",
     "\t\tLPITEM item = ch->GetInventoryItem(i);\n"
     "\t\tif (item && item->GetCell() == i && item->GetYExtra())\n"
     "\t\t\tMt2009YSetsNotify(ch, 1, i, item->GetYExtra());\n",
     "\t\tLPITEM item = ch->GetInventoryItem(i);\n"
     "\t\tif (item && item->GetCell() == i)\n"
     "\t\t\tMt2009YSetsSashLegacy(item); // MT2009_PLUS_SASH_SERPENT_V1 (send all): not worn - no points on yet\n"
     "\t\tif (item && item->GetCell() == i && item->GetYExtra())\n"
     "\t\t\tMt2009YSetsNotify(ch, 1, i, item->GetYExtra());\n")

# 6. the detach
edit("char.cpp", "detach",
     "\t{ void Mt2009WElemClear(LPITEM); Mt2009WElemClear(pkTarget); } // MT2009_PLUS_WEAPON_ELEMENT_V1 (detach): the absorbed weapon's element\n",
     "\t{ void Mt2009WElemClear(LPITEM); Mt2009WElemClear(pkTarget); } // MT2009_PLUS_WEAPON_ELEMENT_V1 (detach): the absorbed weapon's element\n"
     "\t{ void Mt2009YSetsSashClear(LPITEM); Mt2009YSetsSashClear(pkTarget); } // MT2009_PLUS_SASH_SERPENT_V1 (detach): its serpent lines\n")

bad = 0
for e in edits:
    text = open(os.path.join(SRC, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
    if e["marker"] in text:
        continue
    n = text.count(e["old"])
    if n != 1:
        print("%s: %s found %d times" % (e["marker"], e["file"], n))
        bad += 1
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1)
print("szarfawez: %d edit(s) written, %d bad anchor(s)" % (len(edits), bad))
sys.exit(1 if bad else 0)
