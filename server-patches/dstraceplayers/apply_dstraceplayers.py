#!/usr/bin/env python3
"""apply_dstraceplayers.py <engine game/src dir> -- Linux/VPS twin of
Apply-DsTracePlayersPatch.ps1 (same replacement, same marker). The Dragon
Stone equip trace in CHARACTER::EquipItem (char_item.cpp, [DS_EQUIP_TRACE],
eight syserr lines an equip) runs for players only, not for bots.
Applied once; a file without the expected code stops with an error."""
import os
import sys

MARK = 'MT2009_PLUS_DS_TRACE_PLAYERS_V1'
OLD = '\tconst bool bDSTrace = (item->GetType() == ITEM_DS || item->GetType() == ITEM_SPECIAL_DS);\n'
NEW = '\t// MT2009_PLUS_DS_TRACE_PLAYERS_V1 (server-patches/dstraceplayers): the Dragon\n\t// Stone equip trace is for players; bots wear stones all day (playerbot_alchemy.h)\n\t// and eight syserr lines a stone buried everything else.\n\tconst bool bDSTrace = (item->GetType() == ITEM_DS || item->GetType() == ITEM_SPECIAL_DS) &&\n\t\t!(GetDesc() && GetDesc()->IsBot());\n'


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_item.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("dstraceplayers: already applied")
        return
    old, new = OLD, NEW
    if "\r\n" in text:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if text.count(old) != 1:
        sys.exit("dstraceplayers: expected code not found in " + path)
    open(path, "wb").write(text.replace(old, new, 1).encode("latin-1"))
    print("dstraceplayers: applied")


if __name__ == "__main__":
    main()
