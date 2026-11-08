#!/usr/bin/env python3
"""gen_edits.py [game/src] -- writes edits.json of server-patches/gmpanelbonus (MT2009_PLUS_GMPANEL_POINT_BONUS_V1) and
checks every anchor is found exactly once in the given engine tree (default: the test tree, already patched by every
other server patch). cmd_gm.cpp of this engine is double-spaced in do_gmpanel_createitem's part (a blank line after
every line), so the anchors carry those blank lines."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/game/src"
M = "MT2009_PLUS_GMPANEL_POINT_BONUS_V1"

edits = []


def edit(file, tag, old, new):
    edits.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# 1. the map: a POINT_* number sent as 1000 + point (the client's F9 panel, interfacemodule.py GMPanelPointItems) is
#    taken as it is - every bonus incl. the 6th/7th ones (points 193-318, two-byte since wideattr); the result is a WORD
edit("cmd_gm.cpp", "point",
     "static BYTE GMPanelClassicApplyToPoint(int classicApply)\n\n{\n\n",
     "// MT2009_PLUS_GMPANEL_POINT_BONUS_V1 (point): zgloszenie #25 (8 Nov 2026) - the panel (interfacemodule.py\n"
     "// GMPanelPointItems) sends a POINT_* number as 1000 + point: every bonus of this engine, the 6th/7th ones too\n"
     "// (193-318 - two-byte since wideattr, so the result is a WORD); a classic number (1-91, an older client) still goes\n"
     "// through the table below.\n"
     "static WORD GMPanelClassicApplyToPoint(int classicApply)\n\n{\n\n"
     "\tif (classicApply >= 1000)\n"
     "\t{\n"
     "\t\tconst int iPoint = classicApply - 1000;\n"
     "\t\treturn (iPoint > POINT_NONE && iPoint < POINT_MAX_NUM) ? (WORD) iPoint : (WORD) POINT_NONE;\n"
     "\t}\n")

# 2. the classic table's item bonuses: APPLY_MAGIC_ATT_GRADE / MAGIC_DEF_GRADE / DEF_GRADE give the item's *_BONUS
#    points (what world.item_attr_rare and the tooltip use - "Wartosc ataku magicznego"), not the character's own
#    POINT_MAGIC_ATT_GRADE 22 / MAGIC_DEF_GRADE 23 / DEF_GRADE 16, which the tooltip cannot name ("UNKNOWN_TYPE[22]")
edit("cmd_gm.cpp", "grade",
     "POINT_ATT_GRADE_BONUS, POINT_DEF_GRADE_BONUS, POINT_MAGIC_ATT_GRADE,\n\n\t\tPOINT_MAGIC_DEF_GRADE, POINT_CURSE_PCT,",
     "POINT_ATT_GRADE_BONUS, POINT_DEF_GRADE_BONUS, POINT_MAGIC_ATT_GRADE_BONUS, // MT2009_PLUS_GMPANEL_POINT_BONUS_V1 (grade)\n\n"
     "\t\tPOINT_MAGIC_DEF_GRADE_BONUS, POINT_CURSE_PCT,")
edit("cmd_gm.cpp", "def grade",
     "POINT_RESIST_SHAMAN, POINT_ENERGY, POINT_DEF_GRADE,",
     "POINT_RESIST_SHAMAN, POINT_ENERGY, POINT_DEF_GRADE_BONUS, // MT2009_PLUS_GMPANEL_POINT_BONUS_V1 (def grade)")

# 3. the caller keeps the two-byte type
edit("cmd_gm.cpp", "type",
     "\t\tconst BYTE bType = GMPanelClassicApplyToPoint(atoi(fields[10 + i * 2]));\n",
     "\t\tconst WORD bType = GMPanelClassicApplyToPoint(atoi(fields[10 + i * 2])); // MT2009_PLUS_GMPANEL_POINT_BONUS_V1 (type)\n")

texts = {}
ok = True
for e in edits:
    if e["file"] not in texts:
        texts[e["file"]] = open(os.path.join(SRC, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
    text = texts[e["file"]]
    if e["marker"] in text:
        print("already applied: %s" % e["marker"])
        continue
    n = text.count(e["old"])
    if n != 1:
        print("ANCHOR %s: found %d times" % (e["marker"], n))
        ok = False
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1)
print("%d edits written%s" % (len(edits), "" if ok else " - ANCHORS MISSING"))
sys.exit(0 if ok else 1)
