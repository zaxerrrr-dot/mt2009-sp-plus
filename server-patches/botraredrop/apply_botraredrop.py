#!/usr/bin/env python3
"""apply_botraredrop.py <engine game/src dir> -- Linux/VPS twin of
Apply-BotRareDropPatch.ps1 (same replacements, same marker). Idempotent:
a file that already carries MT2009_PLUS_BOT_RARE_DROP_V1 is left alone, and
a file whose expected code is missing stops with an error, changing nothing.
Line endings (CRLF/LF) are kept as they were."""
import os
import sys

MARK = "MT2009_PLUS_BOT_RARE_DROP_V1"

ITEM_MANAGER = [
    ("warunek dropu Cor Draconis",
     "\tif (pkKiller &&\n"
     "\t\tpkKiller->IsPC() &&\n"
     "\t\tpkKiller->GetDesc() &&\n"
     "\t\t!pkKiller->GetDesc()->IsBot())\n"
     "\t{\n"
     "\t\tint corChance = 0;\n",
     "\t// " + MARK + " (server-patches/botraredrop): a bot's kill rolls the\n"
     "\t// Cor Draconis like a player's; the bot lists it on its counter.\n"
     "\tif (pkKiller &&\n"
     "\t\tpkKiller->IsPC() &&\n"
     "\t\tpkKiller->GetDesc())\n"
     "\t{\n"
     "\t\tint corChance = 0;\n"),
    ("Cor Draconis do plecaka bota",
     "\t\t\t\tif (cor)\n"
     "\t\t\t\t\tvec_item.push_back(cor);\n",
     "\t\t\t\t// A bot's own Cor Draconis goes straight into its bag: a bot may\n"
     "\t\t\t\t// not pick one up off the ground (char_item.cpp, PickupItem).\n"
     "\t\t\t\tif (cor)\n"
     "\t\t\t\t{\n"
     "\t\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t\t\tpkKiller->AutoGiveItem(cor);\n"
     "\t\t\t\t\telse\n"
     "\t\t\t\t\t\tvec_item.push_back(cor);\n"
     "\t\t\t\t}\n"),
    ("warunek dropu szarfy",
     "\tif (pkKiller &&\n"
     "\t\tpkKiller->IsPC() &&\n"
     "\t\tpkKiller->GetDesc() &&\n"
     "\t\t!pkKiller->GetDesc()->IsBot() &&\n"
     "\t\tpkChr->GetMobRank() >= MOB_RANK_BOSS)\n",
     "\t// " + MARK + ": a bot's boss kill rolls the sash too.\n"
     "\tif (pkKiller &&\n"
     "\t\tpkKiller->IsPC() &&\n"
     "\t\tpkKiller->GetDesc() &&\n"
     "\t\tpkChr->GetMobRank() >= MOB_RANK_BOSS)\n"),
    ("szarfa do plecaka bota",
     "\t\t\tif (szarfa)\n"
     "\t\t\t\tvec_item.push_back(szarfa);\n",
     "\t\t\tif (szarfa)\n"
     "\t\t\t{\n"
     "\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t\tpkKiller->AutoGiveItem(szarfa);\n"
     "\t\t\t\telse\n"
     "\t\t\t\t\tvec_item.push_back(szarfa);\n"
     "\t\t\t}\n"),
]


def patch(path, blocks):
    raw = open(path, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    if MARK in text:
        print("  already applied: %s" % os.path.basename(path))
        return False
    for name, old, new in blocks:
        if text.count(old) != 1:
            sys.exit("botraredrop: nie znaleziono oczekiwanego kodu (%s) w %s -- nic nie zmieniono"
                     % (name, os.path.basename(path)))
    for name, old, new in blocks:
        text = text.replace(old, new, 1)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("utf-8"))
    print("  applied: %s (%d zmian)" % (os.path.basename(path), len(blocks)))
    return True


def main():
    src = sys.argv[1]
    patch(os.path.join(src, "item_manager.cpp"), ITEM_MANAGER)


if __name__ == "__main__":
    main()
