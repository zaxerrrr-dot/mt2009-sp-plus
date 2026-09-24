#!/usr/bin/env python3
"""apply_magicattper.py <engine game/src dir> -- Linux/VPS twin of
Apply-MagicAttPerPatch.ps1 (same edit, same marker). A pet whose bonus is
POINT_MAGIC_ATT_BONUS_PER (131, magic attack %) never got it:
CHARACTER::PointChange had no case for the point ("unknown point change type
131", a thousand a day once the bots bought pets), though the magic damage
formula reads it (char_battle.cpp). It is handled like its twin
POINT_MELEE_MAGIC_ATT_BONUS_PER (132), capped at 100. Applied once, the line
added with the line ending of the one it follows; a file without the
expected code stops with an error, changing nothing."""
import os
import re
import sys

MARK = "MT2009_PLUS_MAGIC_ATT_PER_V1"
RE = re.compile(r"(\t\tcase POINT_MELEE_MAGIC_ATT_BONUS_PER:(\r?\n))")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("magicattper: already applied")
        return
    if len(RE.findall(text)) != 1:
        sys.exit("magicattper: expected code not found in " + path)
    text = RE.sub(lambda m: m.group(1) + "\t\tcase POINT_MAGIC_ATT_BONUS_PER: // " + MARK + m.group(2), text, count=1)
    open(path, "wb").write(text.encode("latin-1"))
    print("magicattper: applied")


if __name__ == "__main__":
    main()
