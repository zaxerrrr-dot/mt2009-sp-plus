#!/usr/bin/env python3
"""apply_mountreach.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountReachPatch.ps1 (same replacements, same marker).
A normal hit is checked twice for distance: CHARACTER::Attack lets a rider
reach 900 (ATTACK_MELEE_HORSE_MAX_DISTANCE), but battle_melee_attack then
threw away everything past 405 without a word - a mounted player against a
big boss (Razador, 1 October 2026) landed his hits only while the boss stood
close and none while it stepped back. Now battle_melee_attack lets a rider
reach 600, and a boss's or king's body (MOB_RANK_BOSS and up) adds 250 to
both checks for a player. Applied once; a file without the expected code
stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_MOUNT_REACH_V1"
EDITS = {
    "battle.cpp": (
        "\t\t\tif (false == victim->IsPC() && BATTLE_TYPE_MELEE == victim->GetMobBattleType())\n"
        "\t\t\t{\n"
        "\t\t\t\tmax = MAX(405, (int)(victim->GetMobAttackRange() * 1.15f));\n"
        "\t\t\t}\n",
        "\t\t\tif (false == victim->IsPC() && BATTLE_TYPE_MELEE == victim->GetMobBattleType())\n"
        "\t\t\t{\n"
        "\t\t\t\tmax = MAX(405, (int)(victim->GetMobAttackRange() * 1.15f));\n"
        "\t\t\t}\n"
        "\n"
        "\t\t\t// " + MARK + " (server-patches/mountreach): a rider hits from further\n"
        "\t\t\t// away (CHARACTER::Attack lets him reach 900), and a boss's body is big -\n"
        "\t\t\t// past 405 the hit was thrown away without a word.\n"
        "\t\t\tif (ch->IsRiding())\n"
        "\t\t\t\tmax = MAX(max, 600);\n"
        "\t\t\tif (false == victim->IsPC() && victim->GetMobRank() >= MOB_RANK_BOSS)\n"
        "\t\t\t\tmax += 250;\n"),
    "char_battle.cpp": (
        "\tif (distance > maxRadius) {\n"
        "\t\tif (IsPC()) {\n",
        "\t// " + MARK + " (body): a boss's or king's body is big - a player's\n"
        "\t// reach counts from its edge (battle_melee_attack does the same).\n"
        "\tif (IsPC() && false == pkVictim->IsPC() && pkVictim->GetMobRank() >= MOB_RANK_BOSS)\n"
        "\t\tmaxRadius += 250;\n"
        "\n"
        "\tif (distance > maxRadius) {\n"
        "\t\tif (IsPC()) {\n"),
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    todo = []
    for name, (old, new) in EDITS.items():
        path = os.path.join(sys.argv[1], name)
        text = open(path, "rb").read().decode("latin-1")
        if MARK in text:
            print("mountreach: " + name + " already applied")
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("mountreach: expected code not found in " + path + " -- nothing changed")
        todo.append((path, text.replace(o, n, 1)))
    for path, text in todo:
        open(path, "wb").write(text.encode("latin-1"))
        print("mountreach: " + os.path.basename(path) + " applied")


if __name__ == "__main__":
    main()
