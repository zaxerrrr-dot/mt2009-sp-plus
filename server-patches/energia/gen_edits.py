#!/usr/bin/env python3
"""gen_edits.py -> edits.json (MT2009_PLUS_ENERGY_V1, README.md). Rerun after a change here."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_ENERGY_V1"

MEMBER_OLD = """\t\ttypedef std::map <BYTE, CBuffOnAttributes*> TMapBuffOnAttrs;
\t\tTMapBuffOnAttrs m_map_buff_on_attrs;
"""
MEMBER_NEW = MEMBER_OLD + """\t\t// MT2009_PLUS_ENERGY_V1 (member): what the energy of a Krysztal Energii gave on top of the worn items' bonuses
\t\t// (point -> value; energia.cpp, Mt2009EnergyRefresh takes it back before it gives the new share)
\t\tstd::map<WORD, int> m_mapMt2009EnergyApplied;
"""

COMPUTE_OLD = """\tmemset(m_pointsInstant.points, 0, sizeof(m_pointsInstant.points));
\tm_SkillDamageBonus.clear();
"""
COMPUTE_NEW = COMPUTE_OLD + """\t// MT2009_PLUS_ENERGY_V1 (compute): every point is zero again, so is the energy's share (energia.cpp); the
\t// RefreshAffect below gives it again after the worn items
\tm_mapMt2009EnergyApplied.clear();
"""

POINT_OLD = """\t\tcase POINT_MOUNT:
\t\t\tSetPoint(type, GetPoint(type) + amount);
\t\t\tval = GetPoint(type);
\t\t\tMountVnum(val);
\t\t\tbreak;
"""
POINT_NEW = """\t\t// MT2009_PLUS_ENERGY_V1 (point change): the energy of a Krysztal Energii (the affect's 1-10 %) - kept, sent to the
\t\t// client's energy bar, and the worn items' bonuses raised by it (energia.cpp; it was an unknown point before)
\t\tcase POINT_ENERGY:
\t\t\tSetPoint(type, GetPoint(type) + amount);
\t\t\tval = GetPoint(type);
\t\t\t{ void Mt2009EnergyRefresh(LPCHARACTER ch); Mt2009EnergyRefresh(this); }
\t\t\tbreak;

""" + POINT_OLD

EQUIP_OLD = "\tMt2009YSetsRefresh(m_pOwner); // MT2009_PLUS_YOHARA_SETS_V1 (equip): the worn set's bonus\n"
EQUIP_NEW = EQUIP_OLD + ("\t{ void Mt2009EnergyRefresh(LPCHARACTER ch); Mt2009EnergyRefresh(m_pOwner); } "
                         "// MT2009_PLUS_ENERGY_V1 (equip): the energy on the item's bonuses\n")

UNEQUIP_OLD = "\tMt2009YSetsRefresh(m_pOwner); // MT2009_PLUS_YOHARA_SETS_V1 (unequip): the worn set's bonus\n"
UNEQUIP_NEW = UNEQUIP_OLD + ("\t{ void Mt2009EnergyRefresh(LPCHARACTER ch); Mt2009EnergyRefresh(m_pOwner); } "
                             "// MT2009_PLUS_ENERGY_V1 (unequip): the energy without the item\n")

BLEND_OLD = """\t\t\t\tint\t\tapply_type\t\t= item->GetSocket(0);
\t\t\t\tint\t\tapply_value\t\t= item->GetSocket(1);
\t\t\t\tint\t\tapply_duration\t= item->GetSocket(2);
"""
BLEND_NEW = BLEND_OLD + """
\t\t\t\t// MT2009_PLUS_ENERGY_V1 (crystal): Krysztal Energii is always the energy for 2 hours (the pl-wiki); blend.txt had
\t\t\t\t// "ENERGY" (read as 0, no point) and 1800 s - a crystal made before the fix works the same
\t\t\t\tif (item->GetVnum() == 51002)
\t\t\t\t{
\t\t\t\t\tapply_type = POINT_ENERGY;
\t\t\t\t\tapply_duration = 7200;
\t\t\t\t\tif (apply_value <= 0 || apply_value > 10)
\t\t\t\t\t\tapply_value = 1;
\t\t\t\t}
"""

edits = [
    {"file": "char.h", "marker": M + " (member)", "old": MEMBER_OLD, "new": MEMBER_NEW},
    {"file": "char.cpp", "marker": M + " (compute)", "old": COMPUTE_OLD, "new": COMPUTE_NEW},
    {"file": "char.cpp", "marker": M + " (point change)", "old": POINT_OLD, "new": POINT_NEW},
    {"file": "item.cpp", "marker": M + " (equip)", "old": EQUIP_OLD, "new": EQUIP_NEW},
    {"file": "item.cpp", "marker": M + " (unequip)", "old": UNEQUIP_OLD, "new": UNEQUIP_NEW},
    {"file": "char_item.cpp", "marker": M + " (crystal)", "old": BLEND_OLD, "new": BLEND_NEW},
]
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1, ensure_ascii=False)
print("edits.json: %d edit(s)" % len(edits))
