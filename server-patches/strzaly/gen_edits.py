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

FALLOFF_OLD = """\tint minDistance = pkArrow->GetValue(4) + pkAttacker->GetPoint(POINT_BOW_DISTANCE) * 100;
\tint maxDistance = pkArrow->GetValue(5) + pkAttacker->GetPoint(POINT_BOW_DISTANCE) * 100;

\tint iPercent = 100;
\t// MT2009_PLUS_ARROW_RANGE_V1: the fade below runs from value4 (full
\t// strength) to value5 (value2 per cent, twice that against a monster). The
\t// elemental arrows - Ognista, Trujaca, Lodowa, Przekleta Strzala (8006-8009)
\t// - carry 0 in all three, so every shot of theirs past point-blank came to
\t// 0 per cent: an archer with one of them dealt no damage at all. An arrow
\t// without a fade range (value5 not past value4) strikes at full strength,
\t// as a silver arrow does against a monster at any distance.
\tif (pkArrow->GetValue(5) > pkArrow->GetValue(4) && iDist > minDistance)
\t{
\t\tint arrow_damage_percent = pkArrow->GetValue(2);
\t\tint minDamagePercent = pkVictim->IsNPC() ? MIN(arrow_damage_percent * 2, 100) : arrow_damage_percent;
\t\tif (iDist >= maxDistance)
\t\t\tiPercent = minDamagePercent;
\t\telse
\t\t{
\t\t\tint distDelta = maxDistance - minDistance;
\t\t\tint distProgress = ((iDist - minDistance) * 100) / distDelta;

\t\t\tint percentDelta = 100 - minDamagePercent;
\t\t\tiPercent = MAX(100 - percentDelta * distProgress / 100, minDamagePercent);
\t\t}
\t}
"""

FALLOFF_NEW = """\t// MT2009_PLUS_ARROWS_GLOBAL_V2 (falloff): the global server's fade (the owner, 5 November 2026; as Owsap's
\t// CalcArrowDamage): full strength up to 5 m (500) plus the bow's reach bonus (POINT_BOW_DISTANCE, in metres),
\t// then 5 per cent less for every further full metre - 50 per cent at 15 m, nothing from 25 m - against a monster
\t// and a player alike, whatever the arrow. A quiver - an arrow with a real-time limit, Kolczan 8010-8012
\t// (server-patches/quiver) - does not fade. It replaces MT2009_PLUS_ARROW_RANGE_V1's fade by the arrow's
\t// value2 / value4 / value5 (all 0 now, strzaly_global.sql).
\tbool bMt2009Quiver = false;
\tfor (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
\t\tif (pkArrow->GetLimitType(i) == LIMIT_REAL_TIME)
\t\t\tbMt2009Quiver = true;
\tint iGap = (iDist / 100) - 5 - pkAttacker->GetPoint(POINT_BOW_DISTANCE);
\tint iPercent = bMt2009Quiver ? 100 : 100 - (iGap * 5);
"""

edits = [
    {"file": "battle.cpp", "marker": M + " (no mob cut)", "old": NERF_OLD, "new": NERF_NEW},
    {"file": "battle.cpp", "marker": "MT2009_PLUS_ARROWS_GLOBAL_V2 (falloff)", "old": FALLOFF_OLD, "new": FALLOFF_NEW},
]
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1, ensure_ascii=False)
print("edits.json: %d edit(s)" % len(edits))
