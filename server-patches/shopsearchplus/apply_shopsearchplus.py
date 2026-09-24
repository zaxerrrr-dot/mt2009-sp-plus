#!/usr/bin/env python3
"""apply_shopsearchplus.py <engine game/src dir> -- Linux/VPS twin of
Apply-ShopSearchPlusPatch.ps1 (same files, same replacements, same marker).

Target Drop Info and the private shop search, ported onto the MT2009 PLUS
engine: copies src/shop_search_plus.h/.cpp next to the engine sources and
hooks them in: packet headers (packet.h), their sizes (packet_info.cpp), the
dispatch (input_main.cpp) and the two search glasses 60004/60005
(char_item.cpp). Applied once; a file without the expected code stops with
an error before anything is written. Each hook keeps its file's line ending."""
import os
import shutil
import sys

MARK = 'MT2009_PLUS_SHOP_SEARCH_PLUS_V1'
HERE = os.path.dirname(os.path.abspath(__file__))

HOOKS = {
    "packet.h": [
        ("\tHEADER_CG_STATE_CHECKER\t\t\t= 206,\n",
         "\tHEADER_CG_STATE_CHECKER\t\t\t= 206,\n"
         "\t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)\n"
         "\tHEADER_CG_TARGET_DROP\t\t\t= 151,\n"
         "\tHEADER_CG_PRIVATE_SHOP_SEARCH\t= 216,\n"
         "\tHEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE\t= 217,\n"
         "\tHEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM\t= 218,\n"),
        ("\tHEADER_GC_RESPOND_CHANNELSTATUS\t\t\t\t= 210,\n",
         "\tHEADER_GC_RESPOND_CHANNELSTATUS\t\t\t\t= 210,\n"
         "\t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)\n"
         "\tHEADER_GC_TARGET_DROP\t\t\t\t\t\t= 160,\n"
         "\tHEADER_GC_PRIVATE_SHOP_SEARCH\t\t\t\t= 216,\n"
         "\tHEADER_GC_PRIVATE_SHOP_SEARCH_OPEN\t\t\t= 217,\n"
         "\tHEADER_GC_PRIVATE_SHOP_SEARCH_MARK\t\t\t= 218,\n"),
    ],
    "packet_info.cpp": [
        ('#include "packet_info.h"\n',
         '#include "packet_info.h"\n#include "shop_search_plus.h" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1\n'),
        ('\tSet(HEADER_CG_STATE_CHECKER, sizeof(BYTE), "ServerStateCheck", false);\n',
         '\tSet(HEADER_CG_STATE_CHECKER, sizeof(BYTE), "ServerStateCheck", false);\n'
         '\t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)\n'
         '\tSet(HEADER_CG_TARGET_DROP, sizeof(TPacketCGTargetDrop), "TargetDrop", false);\n'
         '\tSet(HEADER_CG_PRIVATE_SHOP_SEARCH, sizeof(TPacketCGPrivateShopSearch), "PrivateShopSearch", false);\n'
         '\tSet(HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE, sizeof(TPacketCGPrivateShopSearchClose), "PrivateShopSearchClose", false);\n'
         '\tSet(HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM, sizeof(TPacketCGPrivateShopSearchBuyItem), "PrivateShopSearchBuyItem", false);\n'),
    ],
    "input_main.cpp": [
        ('#include "input.h"\n',
         '#include "input.h"\n#include "shop_search_plus.h" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1\n'),
        ("#ifdef ENABLE_IKASHOP_RENEWAL\n\t\tcase HEADER_CG_NEW_OFFLINESHOP:\n",
         "\t\t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)\n"
         "\t\tcase HEADER_CG_TARGET_DROP:\n\t\t\tshop_search_plus::RecvTargetDrop(ch);\n\t\t\tbreak;\n"
         "\t\tcase HEADER_CG_PRIVATE_SHOP_SEARCH:\n\t\t\tshop_search_plus::RecvSearch(ch, c_pData);\n\t\t\tbreak;\n"
         "\t\tcase HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE:\n\t\t\tshop_search_plus::RecvClose(ch);\n\t\t\tbreak;\n"
         "\t\tcase HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM:\n\t\t\tshop_search_plus::RecvBuy(ch, c_pData);\n\t\t\tbreak;\n"
         "#ifdef ENABLE_IKASHOP_RENEWAL\n\t\tcase HEADER_CG_NEW_OFFLINESHOP:\n"),
    ],
    "char_item.cpp": [
        ('#include "PetSystem.h"\n',
         '#include "PetSystem.h"\n#include "shop_search_plus.h" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1\n'),
        ("\t\t\t\t\t\t\tcase UNIQUE_ITEM_CAPE_OF_COURAGE:\n",
         "\t\t\t\t\t\t\t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1: Lupa / Lupa Handlarza open the shop search.\n"
         "\t\t\t\t\t\t\tcase SHOP_SEARCH_LOOKING_GLASS:\n"
         "\t\t\t\t\t\t\tcase SHOP_SEARCH_TRADING_GLASS:\n"
         "\t\t\t\t\t\t\t\tshop_search_plus::UseGlass(this, item);\n"
         "\t\t\t\t\t\t\t\tbreak;\n\n"
         "\t\t\t\t\t\t\tcase UNIQUE_ITEM_CAPE_OF_COURAGE:\n"),
    ],
}


def patch(text, old, new):
    for o, n in ((old.replace("\n", "\r\n"), new.replace("\n", "\r\n")), (old, new)):
        if text.count(o) == 1:
            return text.replace(o, n, 1)
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    texts = {}
    for name, pairs in HOOKS.items():
        path = os.path.join(src, name)
        text = open(path, "rb").read().decode("latin-1")
        if MARK in text:
            continue
        for old, new in pairs:
            text = patch(text, old, new)
            if text is None:
                sys.exit("shopsearchplus: expected code not found in " + path)
        texts[path] = text
    for name in ("shop_search_plus.h", "shop_search_plus.cpp"):
        shutil.copyfile(os.path.join(HERE, "src", name), os.path.join(src, name))
    for path, text in texts.items():
        open(path, "wb").write(text.encode("latin-1"))
    print("shopsearchplus: " + ("applied" if texts else "already applied") + " (sources copied)")


if __name__ == "__main__":
    main()
