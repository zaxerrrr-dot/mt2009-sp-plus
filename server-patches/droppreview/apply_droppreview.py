#!/usr/bin/env python3
"""apply_droppreview.py <engine game/src dir> -- Linux/VPS twin of
Apply-DropPreviewPatch.ps1 (same replacements, same marker). The drop preview
(/mob_drop, ITEM_MANAGER::GetPossibleMobDropItems in item_manager.cpp) listed
every item whose chance came out at 1 in 4 000 000 or more, so a level-35
player saw +2 weapons and +4 bracelets on a level-1 wild dog (the common drop
goes by the killer's level). Now an item rolled against iRandRange is listed
only at 1 in 10 000 kills or better. The drop itself is unchanged. Applied
once; a file without the expected code stops with an error, changing nothing.
Only the preview's lines change, in the file's own line ending."""
import os
import sys

MARK = 'MT2009_PLUS_DROP_PREVIEW_MIN_V1'
PAIRS = [
    ('\t\tout_complete = false;\n\t\treturn;\n\t}\n\n\tint iLevel = pkKiller->GetLevel();\n\tBYTE bRank = pkChr->GetMobRank();\n',
     '\t\tout_complete = false;\n\t\treturn;\n\t}\n\n\t// MT2009_PLUS_DROP_PREVIEW_MIN_V1 (server-patches/droppreview): an item\n\t// rolled against iRandRange is listed only at 1 in 10 000 kills or better,\n\t// not at 1 in 4 000 000 - the common drop goes by the killer\'s level, and a\n\t// level-35 player saw +2 weapons on a level-1 dog. The drop is unchanged.\n\tconst int iPreviewMinPercent = MAX(1, iRandRange / 10000);\n\n\tint iLevel = pkKiller->GetLevel();\n\tBYTE bRank = pkChr->GetMobRank();\n'),
    ('\t\t\tint iPercent = (info.m_iPercent * iDeltaPercent) / 100;\n\t\t\tif (iPercent < 1)\n',
     '\t\t\tint iPercent = (info.m_iPercent * iDeltaPercent) / 100;\n\t\t\tif (iPercent < iPreviewMinPercent)\n'),
    ('\t\t\t\tint iPercent = (info.dwPct * iDeltaPercent) / 100;\n\t\t\t\tif (iPercent < 1)\n',
     '\t\t\t\tint iPercent = (info.dwPct * iDeltaPercent) / 100;\n\t\t\t\tif (iPercent < iPreviewMinPercent)\n'),
    ('\t\t\t\t\tint iPercent = (vec[i].dwPct * iDeltaPercent) / 100;\n\t\t\t\t\tif (iPercent >= 1)\n',
     '\t\t\t\t\tint iPercent = (vec[i].dwPct * iDeltaPercent) / 100;\n\t\t\t\t\tif (iPercent >= iPreviewMinPercent)\n'),
    ('\t\t\tint iPercent = (it->second * iDeltaPercent) / 100;\n\t\t\tif (iPercent >= 1)\n\t\t\t\tout_vnums.insert(pkChr->GetMobDropItemVnum());\n',
     '\t\t\tint iPercent = (it->second * iDeltaPercent) / 100;\n\t\t\tif (iPercent >= iPreviewMinPercent)\n\t\t\t\tout_vnums.insert(pkChr->GetMobDropItemVnum());\n'),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "item_manager.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("droppreview: already applied")
        return
    crlf = "\r\n" in text
    for old, new in PAIRS:
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("droppreview: expected code not found in " + path)
        text = text.replace(old, new, 1)
    open(path, "wb").write(text.encode("latin-1"))
    print("droppreview: applied")


if __name__ == "__main__":
    main()
