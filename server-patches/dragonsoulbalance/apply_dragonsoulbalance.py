#!/usr/bin/env python3
"""apply_dragonsoulbalance.py <engine game/src dir> -- Linux/VPS twin of
Apply-DragonSoulBalancePatch.ps1 (same replacements, same marker). The
engine half of the alchemy balance (README.md): the apply names
dragon_soul_table.txt may use. "Wartosc ataku"/"Obrona" were the percent
multipliers POINT_ATT_BONUS/POINT_DEF_BONUS (a Myth Ruby +6 gave +480%
attack) and now are the flat values an item bonus gives; the magic ones go
through their *_BONUS points like an item's; the race, monster, critical
and piercing bonuses become known names. Applied once; a file without the
expected code stops with an error, changing nothing. CRLF/LF is kept."""
import os
import sys

MARK = "MT2009_PLUS_DS_APPLYS_V1"

BLOCKS = [
    ("atak i obrona",
     '\t\t{ "ATT_BONUS",\t\t\tPOINT_ATT_BONUS },\n'
     '\t\t{ "DEF_BONUS",\t\t\tPOINT_DEF_BONUS },\n'
     '\t\t{ "MAGIC_ATT_GRADE",\t\tPOINT_MAGIC_ATT_GRADE },\n'
     '\t\t{ "MAGIC_DEF_GRADE",\t\tPOINT_MAGIC_DEF_GRADE },\n',
     '\t\t// ' + MARK + ' (server-patches/dragonsoulbalance): the flat\n'
     '\t\t// values an item bonus gives. POINT_ATT_BONUS/POINT_DEF_BONUS are\n'
     '\t\t// percent multipliers (battle.cpp, char.cpp GetArmour...), and the\n'
     '\t\t// *_GRADE points are recomputed from level and stats.\n'
     '\t\t{ "ATT_BONUS",\t\t\tPOINT_ATT_GRADE_BONUS },\n'
     '\t\t{ "DEF_BONUS",\t\t\tPOINT_DEF_GRADE_BONUS },\n'
     '\t\t{ "MAGIC_ATT_GRADE",\t\tPOINT_MAGIC_ATT_GRADE_BONUS },\n'
     '\t\t{ "MAGIC_DEF_GRADE",\t\tPOINT_MAGIC_DEF_GRADE_BONUS },\n'),
    ("bonusy na rasy",
     '\t\t{ "ATTBONUS_STONE",\t\tPOINT_ATTBONUS_STONE },\n',
     '\t\t{ "ATTBONUS_STONE",\t\tPOINT_ATTBONUS_STONE },\n'
     '\t\t// ' + MARK + ': the race bonuses in place of the elemental ones,\n'
     '\t\t// and the Amethyst\'s monster, critical and piercing bonuses.\n'
     '\t\t{ "ATTBONUS_HUMAN",\t\tPOINT_ATTBONUS_HUMAN },\n'
     '\t\t{ "ATTBONUS_ANIMAL",\t\tPOINT_ATTBONUS_ANIMAL },\n'
     '\t\t{ "ATTBONUS_ORC",\t\tPOINT_ATTBONUS_ORC },\n'
     '\t\t{ "ATTBONUS_MILGYO",\t\tPOINT_ATTBONUS_MILGYO },\n'
     '\t\t{ "ATTBONUS_UNDEAD",\t\tPOINT_ATTBONUS_UNDEAD },\n'
     '\t\t{ "ATTBONUS_MONSTER",\t\tPOINT_ATTBONUS_MONSTER },\n'
     '\t\t{ "CRITICAL_PCT",\t\tPOINT_CRITICAL_PCT },\n'
     '\t\t{ "PENETRATE_PCT",\t\tPOINT_PENETRATE_PCT },\n'),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "dragon_soul_table.cpp")
    with open(path, "rb") as f:
        raw = f.read().decode("latin-1")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    if MARK in text:
        print("dragonsoulbalance: already applied")
        return
    for name, old, _ in BLOCKS:
        if text.count(old) != 1:
            sys.exit("dragonsoulbalance: expected code not found (%s) in %s" % (name, path))
    for _, old, new in BLOCKS:
        text = text.replace(old, new, 1)
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "wb") as f:
        f.write(text.encode("latin-1"))
    print("dragonsoulbalance: applied")


if __name__ == "__main__":
    main()
