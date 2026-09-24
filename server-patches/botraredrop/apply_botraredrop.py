#!/usr/bin/env python3
"""apply_botraredrop.py <engine game/src dir> -- Linux/VPS twin of
Apply-BotRareDropPatch.ps1 (same replacements, same markers). Three steps,
each applied once: V1 lets a bot's kill roll the Cor Draconis and the sash
(into its bag), V2 gives bots their own chances (Cor 5%, sash 3%), V3 keeps
a bot's drop off the ground when its bag is full. A file
whose expected code is missing stops with an error, changing nothing.
Line endings (CRLF/LF) are kept as they were."""
import os
import sys

MARK = "MT2009_PLUS_BOT_RARE_DROP_V1"
MARK_V2 = "MT2009_PLUS_BOT_RARE_DROP_V2"
MARK_V3 = "MT2009_PLUS_BOT_RARE_DROP_V3"
# A bot's own chance, percent (operator, 24 Sep 2026); players keep theirs
# (Cor Draconis: stone 50, boss 80; sash: boss 80).
BOT_COR_CHANCE = 5
BOT_SASH_CHANCE = 3

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

# V2: the bots' own chances, on top of V1.
ITEM_MANAGER_V2 = [
    ("szansa Cor Draconis dla bota",
     "\t\tif (corChance > 0)\n"
     "\t\t{\n"
     "\t\t\tint roll = number(1, 100);\n",
     "\t\t// " + MARK_V2 + ": a bot's kill rolls at a bot's own chance.\n"
     "\t\tif (corChance > 0 && pkKiller->GetDesc()->IsBot())\n"
     "\t\t\tcorChance = %d;\n"
     "\n"
     "\t\tif (corChance > 0)\n"
     "\t\t{\n"
     "\t\t\tint roll = number(1, 100);\n" % BOT_COR_CHANCE),
    ("szansa szarfy dla bota",
     "\t\tconst int szarfaChance = 80;\n",
     "\t\t// " + MARK_V2 + ": a bot's own chance; a player keeps 80.\n"
     "\t\tconst int szarfaChance = pkKiller->GetDesc()->IsBot() ? %d : 80;\n" % BOT_SASH_CHANCE),
]

# V3: CHARACTER::AutoGiveItem puts an item on the ground when the bag is
# full, and a bot may not pick a Cor Draconis up again (char_item.cpp,
# PickupItem): after a minute it was anybody's. A bot with no room gets
# nothing instead.
ITEM_MANAGER_V3 = [
    ("Cor Draconis przy pelnym plecaku bota",
     "\t\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t\t\tpkKiller->AutoGiveItem(cor);\n",
     "\t\t\t\t\t// " + MARK_V3 + ": a full bag gets nothing, never the ground.\n"
     "\t\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t\t{\n"
     "\t\t\t\t\t\tif (pkKiller->GetEmptyInventoryEx(cor) != -1)\n"
     "\t\t\t\t\t\t\tpkKiller->AutoGiveItem(cor);\n"
     "\t\t\t\t\t\telse\n"
     "\t\t\t\t\t\t\tM2_DESTROY_ITEM(cor);\n"
     "\t\t\t\t\t}\n"),
    ("szarfa przy pelnym plecaku bota",
     "\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t\tpkKiller->AutoGiveItem(szarfa);\n",
     "\t\t\t\t// " + MARK_V3 + ": a full bag gets nothing, never the ground.\n"
     "\t\t\t\tif (pkKiller->GetDesc()->IsBot())\n"
     "\t\t\t\t{\n"
     "\t\t\t\t\tif (pkKiller->GetEmptyInventoryEx(szarfa) != -1)\n"
     "\t\t\t\t\t\tpkKiller->AutoGiveItem(szarfa);\n"
     "\t\t\t\t\telse\n"
     "\t\t\t\t\t\tM2_DESTROY_ITEM(szarfa);\n"
     "\t\t\t\t}\n"),
]


def patch(path, steps):
    """steps: [(marker, blocks), ...] -- each step is applied once, in order."""
    raw = open(path, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    applied = []
    for marker, blocks in steps:
        if marker in text:
            continue
        for name, old, new in blocks:
            if text.count(old) != 1:
                sys.exit("botraredrop: nie znaleziono oczekiwanego kodu (%s) w %s -- nic nie zmieniono"
                         % (name, os.path.basename(path)))
        for name, old, new in blocks:
            text = text.replace(old, new, 1)
        applied.append(marker)
    if not applied:
        print("  already applied: %s" % os.path.basename(path))
        return False
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("utf-8"))
    print("  applied: %s (%s)" % (os.path.basename(path), ", ".join(applied)))
    return True


def main():
    src = sys.argv[1]
    patch(os.path.join(src, "item_manager.cpp"), [(MARK, ITEM_MANAGER), (MARK_V2, ITEM_MANAGER_V2),
                                                     (MARK_V3, ITEM_MANAGER_V3)])


if __name__ == "__main__":
    main()
