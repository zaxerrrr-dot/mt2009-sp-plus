#!/usr/bin/env python3
"""apply_dsqualification.py <engine game/src dir> -- Linux/VPS twin of
Apply-DsQualificationPatch.ps1 (same replacement, same marker). Every real
player gets the Dragon Soul qualification when his affects load at login,
so the alchemy inventory works without the level-30 quest: a Cor Draconis
opens, its stone goes into the alchemy inventory instead of onto the ground,
a stone on the ground can be picked up. Bots are left as they are. Applied
once; a file without the expected code stops with an error, changing
nothing. CRLF/LF is kept."""
import os
import sys

MARK = "MT2009_PLUS_DS_QUALIFY_ON_LOGIN_V1"

OLD = ("\tm_bIsLoadedAffect = true;\n"
       "\n"
       "\tComputePoints(); // @fixme156\n"
       "\tDragonSoul_Initialize();\n")
NEW = ("\tm_bIsLoadedAffect = true;\n"
       "\n"
       "\t// " + MARK + " (server-patches/dsqualification): every real\n"
       "\t// player is qualified for the Dragon Soul alchemy from the start, not\n"
       "\t// after the level-30 quest: without it a stone from a Cor Draconis\n"
       "\t// fell to the ground (GetEmptyDragonSoulInventory) and could not be\n"
       "\t// picked up. The affect is the quest's own (ds.give_qualification),\n"
       "\t// so the client sees the same thing; bots are left as they are.\n"
       "\tif (IsPC() && GetDesc() && !GetDesc()->IsBot() && NULL == FindAffect(AFFECT_DRAGON_SOUL_QUALIFIED))\n"
       "\t\tDragonSoul_GiveQualification();\n"
       "\n"
       "\tComputePoints(); // @fixme156\n"
       "\tDragonSoul_Initialize();\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_affect.cpp")
    raw = open(path, "rb").read().decode("latin-1")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    if MARK in text:
        print("dsqualification: already applied")
        return
    if text.count(OLD) != 1:
        sys.exit("dsqualification: expected code not found in " + path)
    text = text.replace(OLD, NEW, 1)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("dsqualification: applied")


if __name__ == "__main__":
    main()
