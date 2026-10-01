#!/usr/bin/env python3
"""apply_chestsash.py <engine game/src dir> -- Linux/VPS twin of
Apply-ChestSashPatch.ps1 (same replacement, same marker).
The unique sash a box opened with its key may give (char_item.cpp, the boss
chests' roll of 17 September) is for the bosses' chests only: the Gold and
Silver Caskets (50006, 50007 and their "+" twins 50012, 50013) are opened with
a key too and gave it as well (a player on 1 October, also after the goblin
event). Applied once; a file without the expected code stops with an error,
changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_CHEST_SASH_BOSS_ONLY_V1"
OLD = ("\t\t\t\t\t\tif (GetDesc() &&\n"
       "\t\t\t\t\t\t\t\tquest::CQuestManager::instance().GetEventFlag(\"m2_sash_off\") == 0)\n")
NEW = ("\t\t\t\t\t\t// " + MARK + " (server-patches/chestsash): not from the Gold and\n"
       "\t\t\t\t\t\t// Silver Caskets (50006, 50007, 50012, 50013), only the bosses' chests.\n"
       "\t\t\t\t\t\tif (GetDesc() && dwBoxVnum != 50006 && dwBoxVnum != 50007 &&\n"
       "\t\t\t\t\t\t\t\tdwBoxVnum != 50012 && dwBoxVnum != 50013 &&\n"
       "\t\t\t\t\t\t\t\tquest::CQuestManager::instance().GetEventFlag(\"m2_sash_off\") == 0)\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_item.cpp")
    raw = open(path, "rb").read().decode("latin-1")
    text = raw.replace("\r\n", "\n")
    if MARK in text:
        return
    if text.count(OLD) != 1:
        sys.exit("apply_chestsash: the expected code is not in char_item.cpp")
    text = text.replace(OLD, NEW)
    if "\r\n" in raw:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("chestsash: applied")


if __name__ == "__main__":
    main()
