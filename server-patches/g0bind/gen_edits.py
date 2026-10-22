#!/usr/bin/env python3
"""gen_edits.py -- writes edits.json of server-patches/g0bind (README.md, MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1).

Account-bound item instances: a flag on CItem (not on the proto) that adds ITEM_ANTIFLAG_DROP / GIVE / MYSHOP / PKDROP
to the item's GetAntiFlag() (not SELL: the owner, 22 Oct - a bot may sell an unneeded piece to the NPC merchant), so every engine path that already asks the instance's anti flags refuses the item;
the two shop paths that asked the proto's flags ask the instance's now, the old stall skips a bound item, and a refine
(CopyAttributeTo) carries the flag to the new item. The flag's store (player.item_account_bound), its load and the
carry's row are the overlay's (playerbot_yohara_g0.cpp)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1"

edits = [
    {
        "file": "item.h",
        "marker": M + " (antiflag)",
        "old": "\t\tDWORD\t\tGetAntiFlag()\t\t{ return m_pProto ? m_pProto->dwAntiFlags : 0; }\n",
        "new": "\t\t// " + M + " (antiflag): an account-bound item (the bots' G0 package, playerbot_yohara_g0.cpp) is never dropped,\n"
               "\t\t// given, traded or put in a shop (an NPC merchant may buy it) - the proto's flags and the instance's\n"
               "\t\tDWORD\t\tGetAntiFlag()\t\t{ return (m_pProto ? m_pProto->dwAntiFlags : 0) | (m_bAccountBound ? (DWORD) (ITEM_ANTIFLAG_DROP |\n"
               "\t\t\t\t\tITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP | ITEM_ANTIFLAG_PKDROP) : 0); }\n",
    },
    {
        "file": "item.h",
        "marker": M + " (item member)",
        "old": "\t\tvoid\t\tSetYExtra(DWORD dw)\t{ m_dwYExtra = dw; }\n",
        "new": "\t\tvoid\t\tSetYExtra(DWORD dw)\t{ m_dwYExtra = dw; }\n"
               "\t\t// " + M + " (item member): bound to its owner's account - see GetAntiFlag; the overlay keeps the row\n"
               "#define " + M + "\n"
               "\t\tbool\t\tIsAccountBound() const\t{ return m_bAccountBound; }\n"
               "\t\tvoid\t\tSetAccountBound(bool b)\t{ m_bAccountBound = b; }\n",
    },
    {
        "file": "item.h",
        "marker": M + " (item field)",
        "old": "\t\tDWORD\t\tm_dwYExtra = 0; // MT2009_PLUS_YOHARA_SETS_V1 (item field)\n",
        "new": "\t\tDWORD\t\tm_dwYExtra = 0; // MT2009_PLUS_YOHARA_SETS_V1 (item field)\n"
               "\t\tbool\t\tm_bAccountBound = false; // " + M + " (item field)\n",
    },
    {
        "file": "item.cpp",
        "marker": M + " (init)",
        "old": "\tm_dwYExtra = 0; // MT2009_PLUS_YOHARA_SETS_V1 (init)\n",
        "new": "\tm_dwYExtra = 0; // MT2009_PLUS_YOHARA_SETS_V1 (init)\n"
               "\tm_bAccountBound = false; // " + M + " (init)\n",
    },
    {
        "file": "item_attribute.cpp",
        "marker": M + " (declare)",
        "old": "void Mt2009GloveRefine(LPITEM pOld, LPITEM pNew);\n",
        "new": "void Mt2009GloveRefine(LPITEM pOld, LPITEM pNew);\n"
               "void Mt2009AccountBoundCarry(LPITEM pOld, LPITEM pNew); // " + M + " (declare): playerbot_yohara_g0.cpp\n",
    },
    {
        "file": "item_attribute.cpp",
        "marker": M + " (refine)",
        "old": "\t(void) Mt2009JadeBraceletRefine; // MT2009_PLUS_JADE_BRACELET_V1 (refine): replaced by V2\n",
        "new": "\t(void) Mt2009JadeBraceletRefine; // MT2009_PLUS_JADE_BRACELET_V1 (refine): replaced by V2\n"
               "\tif (IsAccountBound()) // " + M + " (refine): the new item is bound too (its row follows it)\n"
               "\t{\n"
               "\t\tpItem->SetAccountBound(true);\n"
               "\t\tMt2009AccountBoundCarry(this, pItem);\n"
               "\t}\n",
    },
    {
        "file": "char_shop.cpp",
        "marker": M + " (shop)",
        "old": "\t\tif (item_table && (IS_SET(item_table->dwAntiFlags, ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP)))\n",
        "new": "\t\t// " + M + " (shop): the item's own flags (an account-bound item's too), not only its proto's\n"
               "\t\tif (item_table && (IS_SET(pkItem->GetAntiFlag(), ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP)))\n",
    },
    {
        "file": "ikarus_shop_manager.cpp",
        "marker": M + " (auction)",
        "old": "\t\tif(IS_SET(table->dwAntiFlags, ITEM_ANTIFLAG_GIVE) || IS_SET(table->dwAntiFlags , ITEM_ANTIFLAG_MYSHOP))\n",
        "new": "\t\t// " + M + " (auction): the item's own flags (an account-bound item's too), not only its proto's\n"
               "\t\tif(IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE) || IS_SET(item->GetAntiFlag() , ITEM_ANTIFLAG_MYSHOP))\n",
    },
    {
        "file": "shop.cpp",
        "marker": M + " (stall)",
        "old": "\t\t\titem_table = pkItem->GetProto();\n",
        "new": "\t\t\titem_table = pkItem->GetProto();\n"
               "\t\t\tif (pkItem->IsAccountBound()) // " + M + " (stall): never on an old-style stall\n"
               "\t\t\t{\n"
               "\t\t\t\tsys_err(\"MyShop: an account-bound item on pos (%d, %d) left out (name: %s)\", pTable->pos.window_type, pTable->pos.cell, m_pkPC->GetName());\n"
               "\t\t\t\t++pTable;\n"
               "\t\t\t\tcontinue;\n"
               "\t\t\t}\n",
    },
]

with open(os.path.join(HERE, "edits.json"), "w", encoding="utf-8") as f:
    json.dump(edits, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("edits.json: %d edit(s)" % len(edits))
