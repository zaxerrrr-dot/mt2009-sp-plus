#!/usr/bin/env python3
"""apply_botrareshare.py <engine game/src dir> -- Linux/VPS twin of
Apply-BotRareSharePatch.ps1 (same replacement, same marker). When a Metin or
a boss drops several items, CHARACTER::Reward (char_battle.cpp) hands them
round the characters that did a tenth of the damage - bots included. A Cor
Draconis or a sash that fell to a bot lay on the ground under its name: a
bot may not pick a Cor up (char_item.cpp, PickupItem) and a player could
not until the ownership ran out. It goes into the bot's bag now, as its own
kill's does (lost when the bag is full). Applied once; a file without the
expected code stops with an error, changing nothing. Only the block changes, in its own line ending."""
import os
import sys

MARK = 'MT2009_PLUS_BOT_RARE_SHARE_V1'
OLD = '\t\t\t\t\tif (it == v.end())\n\t\t\t\t\t\tit = v.begin();\n\n#ifdef ENABLE_DICE_SYSTEM\n\t\t\t\t\tif (ch->GetParty())\n'
NEW = '\t\t\t\t\tif (it == v.end())\n\t\t\t\t\t\tit = v.begin();\n\n\t\t\t\t\t// MT2009_PLUS_BOT_RARE_SHARE_V1 (server-patches/botrareshare): a Cor Draconis or\n\t\t\t\t\t// a sash whose share of a many-item drop falls to a bot goes into\n\t\t\t\t\t// its bag, as a bot\'s own kill\'s does (item_manager.cpp,\n\t\t\t\t\t// MT2009_PLUS_BOT_RARE_DROP_V3): on the ground, owned by a bot that\n\t\t\t\t\t// may not pick a Cor up (char_item.cpp, PickupItem), it lay there\n\t\t\t\t\t// out of every player\'s reach until the ownership ran out.\n\t\t\t\t\tif (ch->GetDesc() && ch->GetDesc()->IsBot() && (item->GetVnum() == 50255\n#ifdef ENABLE_ACCE_COSTUME_SYSTEM\n\t\t\t\t\t\t\t|| (item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_ACCE)\n#endif\n\t\t\t\t\t\t\t))\n\t\t\t\t\t{\n\t\t\t\t\t\titem->RemoveFromGround();\n\t\t\t\t\t\tsys_log(0, "[DS_COR_DROP] share to bag: bot pid=%u name=%s vnum=%u id=%u room=%d",\n\t\t\t\t\t\t\t\tch->GetPlayerID(), ch->GetName(), item->GetVnum(), item->GetID(),\n\t\t\t\t\t\t\t\tch->GetEmptyInventoryEx(item) != -1 ? 1 : 0);\n\t\t\t\t\t\tif (ch->GetEmptyInventoryEx(item) != -1)\n\t\t\t\t\t\t\tch->AutoGiveItem(item);\n\t\t\t\t\t\telse\n\t\t\t\t\t\t\tM2_DESTROY_ITEM(item);\n\t\t\t\t\t\tcontinue;\n\t\t\t\t\t}\n\n#ifdef ENABLE_DICE_SYSTEM\n\t\t\t\t\tif (ch->GetParty())\n'


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_battle.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("botrareshare: already applied")
        return
    # Edited in place, in the line ending the block has: the file mixes
    # CRLF and LF lines, and nothing else in it may change.
    for old, new in ((OLD.replace("\n", "\r\n"), NEW.replace("\n", "\r\n")), (OLD, NEW)):
        if text.count(old) == 1:
            text = text.replace(old, new, 1)
            break
    else:
        sys.exit("botrareshare: expected code not found in " + path)
    open(path, "wb").write(text.encode("latin-1"))
    print("botrareshare: applied")


if __name__ == "__main__":
    main()
