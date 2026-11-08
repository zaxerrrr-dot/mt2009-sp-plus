#!/usr/bin/env python3
"""gen_edits.py [game/src] -- writes edits.json of server-patches/ladaview (MT2009_PLUS_BOT_LADA_VIEW_V1) and checks
every anchor is found exactly once in the given engine tree (default: the test tree, already patched by every other
server patch - ladaview goes last)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/game/src"
M = "MT2009_PLUS_BOT_LADA_VIEW_V1"

edits = []


def edit(file, tag, old, new):
    edits.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# 1. the header, in the shop manager
edit("ikarus_shop_manager.cpp", "include",
     '#include "ikashop_qol.h" // MT2009_PLUS_SHOP_QOL_V2 (include) - Autor: Vekirion (server-patches/shopqol)\n',
     '#include "ikashop_qol.h" // MT2009_PLUS_SHOP_QOL_V2 (include) - Autor: Vekirion (server-patches/shopqol)\n'
     '#include "ikashop_lada_view.h" // MT2009_PLUS_BOT_LADA_VIEW_V1 (include) (server-patches/ladaview)\n')

# 2. the stand's window: only the lines of its pages
edit("ikarus_shop_manager.cpp", "open",
     "\tvoid CShopManager::SendShopOpenClientPacket(LPCHARACTER ch, ikashop::CShop* shop)\n"
     "\t{\n"
     "\t\tif (!ch->GetDesc())\n"
     "\t\t\treturn;\n",
     "\tvoid CShopManager::SendShopOpenClientPacket(LPCHARACTER ch, ikashop::CShop* shop)\n"
     "\t{\n"
     "\t\tif (!ch->GetDesc())\n"
     "\t\t\treturn;\n"
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (open): nothing built for a bot (DESC::Packet drops it), and below only the\n"
     "\t\t// lines of the window's pages - a bot's counter has no number of lines (ikashop_lada_view.h)\n"
     "\t\tif (ch->GetDesc()->IsBot())\n"
     "\t\t\treturn;\n")
edit("ikarus_shop_manager.cpp", "open size",
     "\t\tpack.subheader\t= SUBHEADER_GC_SHOP_OPEN;\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopOpen) + sizeof(TShopItem)* items.size();\n",
     "\t\tpack.subheader\t= SUBHEADER_GC_SHOP_OPEN;\n"
     "\t\tconst unsigned int shown = ikashop_lada_view::CountShown(items); // MT2009_PLUS_BOT_LADA_VIEW_V1 (open size)\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopOpen) + sizeof(TShopItem) * shown;\n")
edit("ikarus_shop_manager.cpp", "open count",
     "\t\tsubpack.isOwnerOnline = shop->IsOwnerOnline();\n"
     "\t\tsubpack.shop.count = shop->GetItems().size();\n",
     "\t\tsubpack.isOwnerOnline = shop->IsOwnerOnline();\n"
     "\t\tsubpack.shop.count = shown; // MT2009_PLUS_BOT_LADA_VIEW_V1 (open count)\n")
edit("ikarus_shop_manager.cpp", "open lines",
     "\t\tbuff.write(&pack, sizeof(pack));\n"
     "\t\tbuff.write(&subpack, sizeof(subpack));\n"
     "\n"
     "\t\tfor (auto& [id, item] : items)\n"
     "\t\t{\n"
     "\t\t\tauto& itemInfo = item->GetInfo();\n"
     "\t\t\tbuff.write(&itemInfo, sizeof(itemInfo));\n"
     "\t\t}\n",
     "\t\tbuff.write(&pack, sizeof(pack));\n"
     "\t\tbuff.write(&subpack, sizeof(subpack));\n"
     "\n"
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (open lines): the same lines CountShown counted\n"
     "\t\tikashop_lada_view::WriteShown(items, [&buff](const TShopItem& itemInfo) { buff.write(&itemInfo, sizeof(itemInfo)); });\n")

# 3. the owner's own window
edit("ikarus_shop_manager.cpp", "owner",
     "\t\tauto shop = ch->GetIkarusShop();\n"
     "\t\tauto owner = ch->GetPlayerID();\n"
     "\n"
     "\t\tconst auto& items = shop->GetItems();\n"
     "\n"
     "\t\tTPacketGCNewIkarusShop pack{};\n"
     "\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n"
     "\t\tpack.subheader\t= SUBHEADER_GC_SHOP_OPEN_OWNER;\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopOpenOwner) + sizeof(TShopItem) * items.size();\n",
     "\t\tauto shop = ch->GetIkarusShop();\n"
     "\t\tauto owner = ch->GetPlayerID();\n"
     "\n"
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (owner): nothing built for a bot, and only the lines of the window's pages\n"
     "\t\tif (ch->GetDesc()->IsBot())\n"
     "\t\t\treturn;\n"
     "\t\tconst auto& items = shop->GetItems();\n"
     "\t\tconst unsigned int shown = ikashop_lada_view::CountShown(items);\n"
     "\n"
     "\t\tTPacketGCNewIkarusShop pack{};\n"
     "\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n"
     "\t\tpack.subheader\t= SUBHEADER_GC_SHOP_OPEN_OWNER;\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopOpenOwner) + sizeof(TShopItem) * shown;\n")
edit("ikarus_shop_manager.cpp", "owner count",
     "\t\tsubpack.shop.count = items.size();\n"
     "\t\tsubpack.shop.duration = shop->GetDuration();\n"
     "\t\tsubpack.shop.ownerid = owner;\n",
     "\t\tsubpack.shop.count = shown; // MT2009_PLUS_BOT_LADA_VIEW_V1 (owner count)\n"
     "\t\tsubpack.shop.duration = shop->GetDuration();\n"
     "\t\tsubpack.shop.ownerid = owner;\n")
edit("ikarus_shop_manager.cpp", "owner lines",
     "\t\tbuff.write(&subpack, sizeof(subpack));\t\t\n"
     "\n"
     "\t\tfor (auto& [id, item] : items)\n"
     "\t\t{\t\t\t\n"
     "\t\t\tauto& itemInfo = item->GetInfo();\n"
     "\t\t\tbuff.write(&itemInfo, sizeof(itemInfo));\n"
     "\t\t}\n",
     "\t\tbuff.write(&subpack, sizeof(subpack));\n"
     "\n"
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (owner lines)\n"
     "\t\tikashop_lada_view::WriteShown(items, [&buff](const TShopItem& itemInfo) { buff.write(&itemInfo, sizeof(itemInfo)); });\n")

# 4. the shop safebox
edit("ikarus_shop_manager.cpp", "safebox",
     "\t\tTPacketGCNewIkarusShop pack{};\n"
     "\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopSafeboxRefresh) + sizeof(TShopPlayerItem) * vec.size();\n"
     "\t\tpack.subheader = SUBHEADER_GC_SHOP_SAFEBOX_REFRESH;\n"
     "\n"
     "\t\tTSubPacketGCShopSafeboxRefresh subpack{};\n"
     "\t\tsubpack.itemcount = vec.size();\n",
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (safebox): nothing built for a bot, and at most SAFEBOX_SEND_MAX items\n"
     "\t\tif (ch->GetDesc()->IsBot())\n"
     "\t\t\treturn;\n"
     "\t\tconst size_t shown = std::min<size_t>(vec.size(), ikashop_lada_view::SAFEBOX_SEND_MAX);\n"
     "\t\tTPacketGCNewIkarusShop pack{};\n"
     "\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n"
     "\t\tpack.size = sizeof(pack) + sizeof(TSubPacketGCShopSafeboxRefresh) + sizeof(TShopPlayerItem) * shown;\n"
     "\t\tpack.subheader = SUBHEADER_GC_SHOP_SAFEBOX_REFRESH;\n"
     "\n"
     "\t\tTSubPacketGCShopSafeboxRefresh subpack{};\n"
     "\t\tsubpack.itemcount = shown;\n")
edit("ikarus_shop_manager.cpp", "safebox lines",
     "\t\tfor (auto& sitem : vec)\n"
     "\t\t{\n"
     "\t\t\tauto& info = static_cast<const TShopPlayerItem&>(sitem->GetInfo());\n"
     "\t\t\tbuff.write(&info, sizeof(info));\n"
     "\t\t}\n",
     "\t\tfor (size_t i = 0; i < shown; ++i) // MT2009_PLUS_BOT_LADA_VIEW_V1 (safebox lines)\n"
     "\t\t{\n"
     "\t\t\tauto& info = static_cast<const TShopPlayerItem&>(vec[i]->GetInfo());\n"
     "\t\t\tbuff.write(&info, sizeof(info));\n"
     "\t\t}\n")

# 5. a line past the pages refreshes nobody's view
edit("ikarus_shop.cpp", "include",
     '#include "ikarus_shop.h"\n#include "ikarus_shop_manager.h"\n',
     '#include "ikarus_shop.h"\n#include "ikarus_shop_manager.h"\n'
     '#include "ikashop_lada_view.h" // MT2009_PLUS_BOT_LADA_VIEW_V1 (include) (server-patches/ladaview)\n')
edit("ikarus_shop.cpp", "add",
     "\t\t// forwarding update to guests\n"
     "\t\tif (updateGuestView)\n"
     "\t\t\t_RefreshViews();\n",
     "\t\t// forwarding update to guests\n"
     "\t\t// MT2009_PLUS_BOT_LADA_VIEW_V1 (add): not for a line past the window's pages, which no view shows\n"
     "\t\tif (updateGuestView && !ikashop_lada_view::IsShownPos((int) item.pos))\n"
     "\t\t\t++ikashop_lada_view::refreshSkipped;\n"
     "\t\telse if (updateGuestView)\n"
     "\t\t\t_RefreshViews();\n")

bad = 0
for e in edits:
    text = open(os.path.join(SRC, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
    n = text.count(e["old"])
    if e["marker"] in text:
        print("already there: %s" % e["marker"])
    elif n != 1:
        print("ANCHOR x%d: %s" % (n, e["marker"]))
        bad += 1
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1)
print("ladaview: %d edits written, %d bad anchors" % (len(edits), bad))
sys.exit(1 if bad else 0)
