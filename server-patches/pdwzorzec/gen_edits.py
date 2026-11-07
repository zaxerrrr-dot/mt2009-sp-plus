#!/usr/bin/env python3
"""gen_edits.py -- writes edits.json of server-patches/pdwzorzec (README.md): MT2009_PLUS_EXP_REFERENCE_V1
(the owner, 7 November 2026, after cache ANALIZA-EXP-ZAKLETY-LAS-2026-11-07.md):
  constants.cpp  aiPercentExperienceByDeltaLev - a monster above the player gives the reference table's percent
                 (105, 110 .. 170, 180 - Owsap's aiPercentByDeltaLev_euckr) instead of ours (102, 105 .. 145); the
                 penalty for a monster below the player is the same in both and stays. The old table is kept as
                 aiPercentExperienceByDeltaLevOld.
  char_battle.cpp GiveExp (ENABLE_NEWEXP_CALCULATION) - the event flag exp_reference_off = 1 takes the old table.
  party.cpp      CParty::GetExpBonusPercent - the party bonus (12% for two near members .. 100% for eight, +5% after
                 an hour, +30% with all classes, +30% from the leader's ring) also in the "by level" mode
                 (PARTY_EXP_DISTRIBUTION_NON_PARITY, the default), as the reference; exp_reference_off = 1 restores 0.
Anchors: the engine after every patch of the deploy list (none of them touches these lines); pdwzorzec goes last."""
import json
import os

E = []
M = "MT2009_PLUS_EXP_REFERENCE_V1"


def edit(file, marker, old, new):
    E.append({"file": file, "marker": M + " (" + marker + ")", "old": old, "new": new})


BELOW = [(1, -15, 0), (5, -14, 1), (10, -13, 2), (20, -12, 3), (30, -11, 4), (50, -10, 5), (70, -9, 6), (80, -8, 7),
         (85, -7, 8), (90, -6, 9), (92, -5, 10), (94, -4, 11), (96, -3, 12), (98, -2, 13)]
OLD_ABOVE = [102, 105, 108, 111, 114, 117, 120, 123, 126, 130, 133, 136, 139, 142, 145]
NEW_ABOVE = [105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 180]


def engine_table():
    """The table exactly as the engine has it (the anchor)."""
    s = "// EXPERIENCE BONUS LV DELTA TABLE\nextern const int aiPercentExperienceByDeltaLev[MAX_EXP_DELTA_OF_LEV] =\n{\n"
    for v, d, i in BELOW:
        s += "\t%s //  %-3d %d\n" % ((str(v) + ",").ljust(3), d, i)
    s += "\t100,    //  -1  14\n\t100,    //  0   15\n"
    for n, v in enumerate(OLD_ABOVE, 1):
        s += "\t%d,    //  %-3d %d\n" % (v, n, 15 + n)
    return s + "};\n"


def table(name, above, comment):
    s = comment + "extern const int %s[MAX_EXP_DELTA_OF_LEV] =\n{\n" % name
    for v, d, i in BELOW:
        s += "\t%s //  %-3d %d\n" % ((str(v) + ",").ljust(3), d, i)
    s += "\t100,    //  -1  14\n\t100,    //  0   15\n"
    for n, v in enumerate(above, 1):
        s += "\t%d,%s//  %-3d %d\n" % (v, " " * 4, n, 15 + n)
    return s + "};\n"


OLD = engine_table()
NEW = (table("aiPercentExperienceByDeltaLev", NEW_ABOVE,
             "// EXPERIENCE BONUS LV DELTA TABLE\n"
             "// MT2009_PLUS_EXP_REFERENCE_V1 (delta table): a monster above the player - the reference's +5% a level, 180%\n"
             "// at +15 (the owner, 7 November 2026; ours was 102 .. 145). Below the player - unchanged (the same in both).\n")
       + table("aiPercentExperienceByDeltaLevOld", OLD_ABOVE,
               "// The table before (102 .. 145) - GiveExp takes it while the event flag exp_reference_off is 1.\n"))
assert OLD.count("\n") == 35, OLD

edit("constants.cpp", "delta table", OLD, NEW)

# ---------------------------------------------------------------- char_battle.cpp
DEF = ("#define NEW_GET_LVDELTA(me, victim) aiPercentExperienceByDeltaLev"
       "[MINMAX(0, (victim + 15) - me, MAX_EXP_DELTA_OF_LEV - 1)]\n")
edit("char_battle.cpp", "old table",
     DEF,
     DEF +
     "// MT2009_PLUS_EXP_REFERENCE_V1 (old table): the table before (constants.cpp), for exp_reference_off = 1\n"
     "extern const int aiPercentExperienceByDeltaLevOld[MAX_EXP_DELTA_OF_LEV];\n"
     "#define OLD_GET_LVDELTA(me, victim) aiPercentExperienceByDeltaLevOld"
     "[MINMAX(0, (victim + 15) - me, MAX_EXP_DELTA_OF_LEV - 1)]\n")
edit("char_battle.cpp", "delta switch",
     "\tint lvDelta = NEW_GET_LVDELTA(toLevel, fromLevel);\n",
     "\t// MT2009_PLUS_EXP_REFERENCE_V1 (delta switch): the reference table (constants.cpp); the event flag\n"
     "\t// exp_reference_off = 1 brings the old one back without a build.\n"
     "\tint lvDelta = quest::CQuestManager::instance().GetEventFlag(\"exp_reference_off\")\n"
     "\t\t? OLD_GET_LVDELTA(toLevel, fromLevel) : NEW_GET_LVDELTA(toLevel, fromLevel);\n")

# ---------------------------------------------------------------- party.cpp
edit("party.cpp", "include",
     '#include "unique_item.h"\n#include "log.h"\n',
     '#include "unique_item.h"\n#include "log.h"\n'
     '#include "questmanager.h" // MT2009_PLUS_EXP_REFERENCE_V1 (include): exp_reference_off\n')
edit("party.cpp", "party bonus",
     "\tif (GetExpDistributionMode() == PARTY_EXP_DISTRIBUTION_NON_PARITY)\n\t\treturn 0;\n\n"
     "\treturn m_iExpBonus + m_iLongTimeExpBonus + m_iEveryClassExpBonus;\n",
     "\t// MT2009_PLUS_EXP_REFERENCE_V1 (party bonus): the bonus in both modes, as the reference (the owner,\n"
     "\t// 7 November 2026) - \"by level\" (NON_PARITY, the default) got 0 before. The event flag\n"
     "\t// exp_reference_off = 1 brings the old rule back.\n"
     "\tif (GetExpDistributionMode() == PARTY_EXP_DISTRIBUTION_NON_PARITY\n"
     "\t\t&& quest::CQuestManager::instance().GetEventFlag(\"exp_reference_off\"))\n"
     "\t\treturn 0;\n\n"
     "\treturn m_iExpBonus + m_iLongTimeExpBonus + m_iEveryClassExpBonus;\n")

json.dump(E, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edits.json"), "w"), indent=2)
print("%d edits" % len(E))
