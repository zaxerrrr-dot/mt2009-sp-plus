#!/usr/bin/env python3
"""apply_botsashdrop.py <engine game/src dir> -- Linux/VPS twin of
Apply-BotSashDropPatch.ps1 (same replacements, same marker). A bot rolls the
sash of a boss kill at a player's chance, 80% (it was 3%, botraredrop V2), and
a bot opening a boss chest rolls its unique sash like a player - into its bag,
or nowhere when the bag is full ("zwiekszyc drop na szarfy dla botow - tyle
samo co dla gracza", operator, 26 September 2026).
Needs botraredrop applied first. Applied once; a file without the expected
code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_BOT_SASH_DROP_V1"
EDITS = [
    ("item_manager.cpp",
     "\t\t// MT2009_PLUS_BOT_RARE_DROP_V2: a bot's own chance; a player keeps 80.\n"
     "\t\tconst int szarfaChance = pkKiller->GetDesc()->IsBot() ? 3 : 80;\n",
     "\t\t// " + MARK + " (server-patches/botsashdrop): a bot rolls at a\n"
     "\t\t// player's chance (it was 3, MT2009_PLUS_BOT_RARE_DROP_V2).\n"
     "\t\tconst int szarfaChance = 80;\n"),
    ("char_item.cpp",
     "\t\t\t\t\t\tif (GetDesc() && !GetDesc()->IsBot() &&\n",
     "\t\t\t\t\t\t// " + MARK + " (server-patches/botsashdrop): a bot's chest too.\n"
     "\t\t\t\t\t\tif (GetDesc() &&\n"),
    ("char_item.cpp",
     "\t\t\t\t\t\t\t\tif (szarfa)\n"
     "\t\t\t\t\t\t\t\t\tAutoGiveItem(szarfa, true);\n",
     "\t\t\t\t\t\t\t\t// " + MARK + ": a bot's full bag gets nothing, never the ground.\n"
     "\t\t\t\t\t\t\t\tif (szarfa && GetDesc()->IsBot() && GetEmptyInventoryEx(szarfa) == -1)\n"
     "\t\t\t\t\t\t\t\t\tM2_DESTROY_ITEM(szarfa);\n"
     "\t\t\t\t\t\t\t\telse if (szarfa)\n"
     "\t\t\t\t\t\t\t\t\tAutoGiveItem(szarfa, true);\n"),
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
        if MARK in text and new.split("\n")[0] in text:
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("botsashdrop: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("botsashdrop: %s applied" % os.path.basename(path))
        else:
            print("botsashdrop: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
