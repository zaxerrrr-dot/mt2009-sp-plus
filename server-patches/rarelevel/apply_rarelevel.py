#!/usr/bin/env python3
"""apply_rarelevel.py <engine game/src dir> -- Linux/VPS twin of
Apply-RareLevelPatch.ps1 (same replacements, same marker). The Cor Draconis
and sash drops of Metins and bosses (item_manager.cpp,
ITEM_MANAGER::CreateDropItem) had no level check: a level 90 breaking a level
5 stone got a sash. Now neither drops from a monster more than 15 levels below
the killer; one above the killer drops with no limit. Applied once; a file
without the expected code stops with an error, changing nothing. Only the two
blocks change, in the file's own line ending."""
import os
import sys

MARK = 'MT2009_PLUS_RARE_LEVEL_V1'
PAIRS = [('\tif (pkKiller &&\n\t\tpkKiller->IsPC() &&\n\t\tpkKiller->GetDesc())\n\t{\n\t\tint corChance = 0;\n', '\t// MT2009_PLUS_RARE_LEVEL_V1 (server-patches/rarelevel): no Cor Draconis from a\n\t// Metin or boss more than 15 levels below the killer (a level 90 at a level\n\t// 5 stone); a stronger one drops with no limit.\n\tif (pkKiller &&\n\t\tpkKiller->IsPC() &&\n\t\tpkKiller->GetDesc() &&\n\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)\n\t{\n\t\tint corChance = 0;\n'), ('\t\tpkKiller->GetDesc() &&\n\t\tpkChr->GetMobRank() >= MOB_RANK_BOSS)\n\t{\n', '\t\tpkKiller->GetDesc() &&\n\t\tpkChr->GetMobRank() >= MOB_RANK_BOSS &&\n\t\t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.\n\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)\n\t{\n')]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "item_manager.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("rarelevel: already applied")
        return
    crlf = "\r\n" in text
    for old, new in PAIRS:
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("rarelevel: expected code not found in " + path)
        text = text.replace(old, new, 1)
    open(path, "wb").write(text.encode("latin-1"))
    print("rarelevel: applied")


if __name__ == "__main__":
    main()
