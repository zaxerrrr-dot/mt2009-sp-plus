#!/usr/bin/env python3
"""apply_raretoggle.py <engine game/src dir> -- Linux/VPS twin of
Apply-RareTogglePatch.ps1 (same replacements, same marker). The world's two
switches for the rare goods: event flag m2_alchemy_off stops the Cor Draconis
from Metins and bosses (item_manager.cpp, ITEM_MANAGER::CreateDropItem), and
m2_sash_off the sash from bosses (same function) and from boss chests
(char_item.cpp, the treasure box and key). Set from .env (M2_ALCHEMY,
M2_SASHES) by the start migration and live from the admin panel. What a
player already has is untouched. Applied once, after rarelevel; a file
without the expected code stops with an error, changing nothing."""
import os
import sys

MARK = 'MT2009_PLUS_RARE_TOGGLE_V1'
FILES = {
    "item_manager.cpp": [
        ('\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)\n\t{\n\t\tint corChance = 0;\n',
         '\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15 &&\n\t\t// MT2009_PLUS_RARE_TOGGLE_V1 (server-patches/raretoggle): no Cor Draconis\n\t\t// while the world has the alchemy switched off (M2_ALCHEMY=0, the panel).\n\t\tquest::CQuestManager::instance().GetEventFlag("m2_alchemy_off") == 0)\n\t{\n\t\tint corChance = 0;\n'),
        ('\t\t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.\n\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)\n',
         '\t\t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.\n\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + 15 &&\n\t\t// MT2009_PLUS_RARE_TOGGLE_V1: no sash while the world has them switched off.\n\t\tquest::CQuestManager::instance().GetEventFlag("m2_sash_off") == 0)\n'),
    ],
    "char_item.cpp": [
        ('\t\t\t\t\t\tif (GetDesc() && !GetDesc()->IsBot())\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\t// 85104 (Death Ruler Wings +3)',
         '\t\t\t\t\t\t// MT2009_PLUS_RARE_TOGGLE_V1 (server-patches/raretoggle): no sash from a\n\t\t\t\t\t\t// boss chest while the world has them switched off (M2_SASHES=0).\n\t\t\t\t\t\tif (GetDesc() && !GetDesc()->IsBot() &&\n\t\t\t\t\t\t\t\tquest::CQuestManager::instance().GetEventFlag("m2_sash_off") == 0)\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\t// 85104 (Death Ruler Wings +3)'),
    ],
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    texts = {}
    for name, pairs in FILES.items():
        path = os.path.join(sys.argv[1], name)
        text = open(path, "rb").read().decode("latin-1")
        if MARK in text:
            continue
        crlf = "\r\n" in text
        for old, new in pairs:
            if crlf:
                old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
            if text.count(old) != 1:
                sys.exit("raretoggle: expected code not found in " + path)
            text = text.replace(old, new, 1)
        texts[path] = text
    if not texts:
        print("raretoggle: already applied")
        return
    for path, text in texts.items():
        open(path, "wb").write(text.encode("latin-1"))
    print("raretoggle: applied")


if __name__ == "__main__":
    main()
