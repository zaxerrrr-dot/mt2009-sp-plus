#!/usr/bin/env python3
"""gen_edits.py -> edits.json (MT2009_PLUS_ARROWS_GLOBAL_V1, README.md). Rerun after a change here."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_ARROWS_GLOBAL_V1"

NERF_OLD = """\t// ogolny nerf obrazen ze zwyklych strzal dla archera
\tif (dwSkill == 0 &&
\t\tpkVictim != pkAttacker->GetTarget() && pkVictim->IsNPC() &&
\t\tvictimCount > 1)
\t{
\t\tif (pkVictim->GetMobRank() < MOB_RANK_BOSS)
\t\t{
\t\t\tint max_damage_reduction = 30;
\t\t\tint min_damage_reduction = 10;
\t\t\tint delta_damage_reduction = max_damage_reduction - min_damage_reduction;
\t\t\tint progress = MIN(pkAttacker->GetLevel()*100 / 60, 100);

\t\t\tint reduction = max_damage_reduction - delta_damage_reduction * progress / 100;

\t\t\tif (victimCount == 2)
\t\t\t\treduction /= 2;

\t\t\tiAtk = iAtk * (100 - reduction) / 100;
\t\t}
\t}
"""

NERF_NEW = """\t// %s (no mob cut): the package cut an Archer's plain shot at a
\t// monster other than the target by 10-30 per cent (30 at level 1, 10 from
\t// level 60, half that with two victims) whenever the shot had more than one
\t// victim - every extra arrow of MT2009_PLUS_ARCHER_MULTISHOT. The global
\t// server has no such cut: each arrow strikes a monster at full strength (the
\t// owner, 5 November 2026: "nie ograniczaj ataku w moby jak dotychczas").
\t// victimCount stays in the signature for the callers (players' FuncShoot,
\t// the bots' extra arrows in playerbot_targeting.h).
\t(void) victimCount;
""" % M

edits = [
    {"file": "battle.cpp", "marker": M + " (no mob cut)", "old": NERF_OLD, "new": NERF_NEW},
]
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1, ensure_ascii=False)
print("edits.json: %d edit(s)" % len(edits))
