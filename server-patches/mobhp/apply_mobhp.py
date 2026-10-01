#!/usr/bin/env python3
"""apply_mobhp.py <engine game/src dir> -- Linux/VPS twin of
Apply-MobHpPatch.ps1 (same replacements, same marker).
The health of monsters, bosses and Metin stones as a percent of their
mob_proto max_hp (the operator, 30 September 2026, for Frelik's proposal
"latwy 80%"): the event flag m2_mob_hp, 10..300, 100 or 0 the game as it was
made. A monster or a stone takes it when it spawns (ComputePoints), and when
the flag moves every one standing is rescaled and keeps its share of health
(CQuestManager::SetEventFlag), so the classic panel's card is live at once.
NPCs, ore veins, herb bushes, doors and the still monsters with no attack
(the dungeons' gates) keep their health; experience and drops are untouched.
Applied once; a file without the expected code stops with an error, changing
nothing."""
import os
import sys

MARK = "MT2009_PLUS_MOB_HP_V1"
HELPERS = (
    "// " + MARK + " (server-patches/mobhp): the health of monsters, bosses and\n"
    "// Metin stones, a percent of mob_proto's max_hp - the event flag m2_mob_hp\n"
    "// (10..300; 0 or 100 = the game as it was made), which the launcher's\n"
    "// difficulty window and the classic panel's card set. NPCs, ore veins, herb\n"
    "// bushes, doors and a still monster with no attack (a dungeon's gate) keep\n"
    "// their own.\n"
    "static int s_iM2MobHpPercent = 100;\n"
    "\n"
    "static bool M2MobHpApplies(const CHARACTER* ch, const TMobTable& t)\n"
    "{\n"
    "\tif (!ch || ch->IsPC())\n"
    "\t\treturn false;\n"
    "\tif (ch->IsStone())\n"
    "\t\treturn true;\n"
    "\tif (!ch->IsMonster())\n"
    "\t\treturn false;\n"
    "\treturn !(IS_SET(t.dwAIFlag, AIFLAG_NOMOVE) && t.dwDamageRange[1] == 0);\n"
    "}\n"
    "\n"
    "static int M2MobScaledMaxHP(DWORD base, int pct)\n"
    "{\n"
    "\tlong long v = (long long)base * pct / 100;\n"
    "\tif (v < 1)\n"
    "\t\tv = 1;\n"
    "\tif (v > INT_MAX)\n"
    "\t\tv = INT_MAX;\n"
    "\treturn (int)v;\n"
    "}\n"
    "\n"
    "// The flag moved (CQuestManager::SetEventFlag, on every core): the monsters\n"
    "// and stones standing take the new health and keep their share of it. One\n"
    "// whose max_hp somebody else set (a dungeon's UniqueSetMaxHP) is left alone.\n"
    "void M2ApplyMobHpPercent(int value)\n"
    "{\n"
    "\tconst int pct = value <= 0 ? 100 : (value < 10 ? 10 : (value > 300 ? 300 : value));\n"
    "\tconst int prev = s_iM2MobHpPercent;\n"
    "\tif (pct == prev)\n"
    "\t\treturn;\n"
    "\ts_iM2MobHpPercent = pct;\n"
    "\tint changed = 0;\n"
    "\tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())\n"
    "\t{\n"
    "\t\tLPCHARACTER ch = kv.second;\n"
    "\t\tif (!ch || ch->IsPC() || ch->IsPet() || ch->IsDead())\n"
    "\t\t\tcontinue;\n"
    "\t\tconst TMobTable& t = ch->GetMobTable();\n"
    "\t\tif (!M2MobHpApplies(ch, t))\n"
    "\t\t\tcontinue;\n"
    "\t\tconst int real = ch->GetRealPoint(POINT_MAX_HP);\n"
    "\t\tconst int oldMax = ch->GetMaxHP();\n"
    "\t\tif (real != M2MobScaledMaxHP(t.dwMaxHP, prev) || oldMax < real || oldMax <= 0)\n"
    "\t\t\tcontinue;\n"
    "\t\tconst int hp = ch->GetHP();\n"
    "\t\tch->SetRealPoint(POINT_MAX_HP, M2MobScaledMaxHP(t.dwMaxHP, pct));\n"
    "\t\tch->PointChange(POINT_MAX_HP, 0);\n"
    "\t\tconst int newMax = ch->GetMaxHP();\n"
    "\t\tlong long newHp = (long long)hp * newMax / oldMax;\n"
    "\t\tif (hp > 0 && newHp < 1)\n"
    "\t\t\tnewHp = 1;\n"
    "\t\tif (newHp > newMax)\n"
    "\t\t\tnewHp = newMax;\n"
    "\t\tch->SetHP((int)newHp);\n"
    "\t\tch->BroadcastTargetPacket();\n"
    "\t\t++changed;\n"
    "\t}\n"
    "\tsys_log(0, \"MOB_HP: %d%% -> %d%% of max_hp, %d standing rescaled\", prev, pct, changed);\n"
    "}\n"
    "\n"
)
EDITS = [
    ("char.cpp",
     "void CHARACTER::SetProto(const CMob * pkMob)\n{\n",
     HELPERS + "void CHARACTER::SetProto(const CMob * pkMob)\n{\n"),
    ("char.cpp",
     "\t\tiMaxHP = m_pkMobData->m_table.dwMaxHP;\n",
     "\t\tiMaxHP = m_pkMobData->m_table.dwMaxHP;\n"
     "\t\t// " + MARK + " (spawn): the world's monster health.\n"
     "\t\tif (s_iM2MobHpPercent != 100 && M2MobHpApplies(this, m_pkMobData->m_table))\n"
     "\t\t\tiMaxHP = M2MobScaledMaxHP(m_pkMobData->m_table.dwMaxHP, s_iM2MobHpPercent);\n"),
    ("questmanager.cpp",
     "#include \"event_helper.h\"\n\nDWORD g_GoldDropTimeLimitValue = 0;\n",
     "#include \"event_helper.h\"\n\n"
     "// " + MARK + " (declare): char.cpp, server-patches/mobhp.\n"
     "extern void M2ApplyMobHpPercent(int value);\n\n"
     "DWORD g_GoldDropTimeLimitValue = 0;\n"),
    ("questmanager.cpp",
     "\t\tm_mapEventFlag[name] = value;\n\n\t\tif (name == \"mob_item\")\n",
     "\t\tm_mapEventFlag[name] = value;\n\n"
     "\t\t// " + MARK + " (flag): the monsters' health is live on every core.\n"
     "\t\tif (name == \"m2_mob_hp\")\n"
     "\t\t\t::M2ApplyMobHpPercent(value);\n\n"
     "\t\tif (name == \"mob_item\")\n"),
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
        marked = [l for l in new.split("\n") if MARK in l]
        if marked and marked[0] in text.replace("\r\n", "\n"):
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("mobhp: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("mobhp: %s applied" % os.path.basename(path))
        else:
            print("mobhp: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
