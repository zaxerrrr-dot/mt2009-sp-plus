#!/usr/bin/env python3
"""gen_edits.py [<engine game/src dir>] -- writes edits.json of the Dodatkowy ekwipunek
(MT2009_PLUS_EKWIPUNEK_V1, README.md). With a game/src dir, also checks that every edit's
old code is there exactly once (or its marker already is)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_EKWIPUNEK_V1"
WINDOWS = "\tcase UPGRADE_INVENTORY:\n\tcase BOOK_INVENTORY:\n\tcase STONE_INVENTORY:\n\tcase CHANGE_INVENTORY:\n\tcase CHEST_INVENTORY:\n"


def ind(text, n):
	return "".join(("\t" * n + l) if l else l for l in text.splitlines(True))


E = []


def edit(file, tag, old, new):
	E.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# ---------------------------------------------------------------- common/length.h
L = "../../common/length.h"
edit(L, "sizes", "enum EWindows\n{\n",
	"// " + M + " (sizes): Dodatkowy ekwipunek (Ameria's special storage) - five category storages of four pages\n"
	"// 5 x 9 each (playerbot_ekwipunek.cpp, the client's exe the same).\n"
	"enum EMt2009SpecialStorage\n{\n"
	"\tSPECIAL_INVENTORY_PAGE_COLUMN = 5,\n"
	"\tSPECIAL_INVENTORY_PAGE_ROW = 9,\n"
	"\tSPECIAL_INVENTORY_PAGE_SIZE = SPECIAL_INVENTORY_PAGE_COLUMN * SPECIAL_INVENTORY_PAGE_ROW,\n"
	"\tSPECIAL_INVENTORY_PAGE_COUNT = 4,\n"
	"\tSPECIAL_INVENTORY_MAX_NUM = SPECIAL_INVENTORY_PAGE_SIZE * SPECIAL_INVENTORY_PAGE_COUNT,\n"
	"\tSPECIAL_INVENTORY_WINDOW_COUNT = 5,\n"
	"};\n\n"
	"enum EWindows\n{\n")
edit(L, "windows", "\tIKASHOP_AUCTION,\n#endif\n\tWINDOW_TYPE_MAX,\n",
	"\tIKASHOP_AUCTION,\n#endif\n"
	"\t// " + M + " (windows): the category storages, 11-15 - after every old window, so player.item.window (an enum\n"
	"\t// appended the same way, ekwipunek.sql) and the client keep their numbers\n"
	"\tUPGRADE_INVENTORY,\n\tBOOK_INVENTORY,\n\tSTONE_INVENTORY,\n\tCHANGE_INVENTORY,\n\tCHEST_INVENTORY,\n"
	"\tWINDOW_TYPE_MAX,\n")
edit(L, "is special", "typedef struct SItemPos\n{\n",
	"// " + M + " (is special): one of the category storages\n"
	"inline bool Mt2009IsSpecialWindow(BYTE bWindow)\n{\n"
	"\treturn bWindow >= UPGRADE_INVENTORY && bWindow <= CHEST_INVENTORY;\n}\n\n"
	"typedef struct SItemPos\n{\n")
edit(L, "valid pos",
	"\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\treturn cell < (DRAGON_SOUL_INVENTORY_MAX_NUM);\n\n\t\tcase SAFEBOX:\n\t\tcase MALL:\n\t\t\treturn false;\n",
	"\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\treturn cell < (DRAGON_SOUL_INVENTORY_MAX_NUM);\n"
	"\t\t// " + M + " (valid pos)\n" + ind(WINDOWS, 1) +
	"\t\t\treturn cell < SPECIAL_INVENTORY_MAX_NUM;\n\n\t\tcase SAFEBOX:\n\t\tcase MALL:\n\t\t\treturn false;\n")

# ---------------------------------------------------------------- char.h
H = "char.h"
edit(H, "slots", "\tstd::array<WORD,DRAGON_SOUL_INVENTORY_MAX_NUM> wDSItemGrid;\n",
	"\tstd::array<WORD,DRAGON_SOUL_INVENTORY_MAX_NUM> wDSItemGrid;\n"
	"\t// " + M + " (slots): the five category storages, window by window (UPGRADE_INVENTORY first), and whether the\n"
	"\t// client said it knows them (\"/ekwipunek hello\" - only then does anything go there)\n"
	"\tstd::array<LPITEM,SPECIAL_INVENTORY_MAX_NUM * SPECIAL_INVENTORY_WINDOW_COUNT> pSpecialItems{};\n"
	"\tstd::array<WORD,SPECIAL_INVENTORY_MAX_NUM * SPECIAL_INVENTORY_WINDOW_COUNT> wSpecialItemGrid{};\n"
	"\tbool bSpecialStorageClient{false};\n")
edit(H, "methods", "\t\tint\t\t\t\tGetEmptyInventoryEx(LPITEM item);\n",
	"\t\tint\t\t\t\tGetEmptyInventoryEx(LPITEM item);\n"
	"\t\t// " + M + " (methods): Dodatkowy ekwipunek, playerbot_ekwipunek.cpp\n"
	"\t\tint\t\t\t\tGetEmptyInventoryRouted(LPITEM item, BYTE& bWindow);\n"
	"\t\tint\t\t\t\tGetEmptySpecialInventory(BYTE bWindow, BYTE bSize) const;\n"
	"\t\tBYTE\t\t\tGetSpecialWindowFor(LPITEM item) const;\n"
	"\t\tbool\t\t\tIsSpecialStorageClient() const;\n"
	"\t\tvoid\t\t\tSetSpecialStorageClient(bool bOn);\n"
	"\t\tbool\t\t\tMt2009EkwRoutes() const;\n"
	"\t\tLPITEM\t\t\tMt2009SpecialGetItem(BYTE bWindow, WORD wCell) const;\n"
	"\t\tvoid\t\t\tMt2009SpecialSetItem(BYTE bWindow, WORD wCell, LPITEM pItem);\n"
	"\t\tbool\t\t\tMt2009SpecialIsEmptyGrid(BYTE bWindow, WORD wCell, BYTE bSize, int iExceptionCell) const;\n"
	"\t\tvoid\t\t\tMt2009SpecialClearItems();\n"
	"\t\tITEM_COUNT\t\tMt2009SpecialCountItem(DWORD dwVnum) const;\n"
	"\t\tITEM_COUNT\t\tMt2009SpecialRemoveItem(DWORD dwVnum, ITEM_COUNT count);\n"
	"\t\tbool\t\t\tMt2009SpecialMoveAllowed(LPITEM item, const TItemPos& Cell, const TItemPos& DestCell);\n"
	"\t\tbool\t\t\tMt2009SpecialCheckoutAllowed(LPITEM item, const TItemPos& DestCell);\n"
	"\t\tLPITEM\t\t\tMt2009EkwAutoStack(LPITEM item, bool& bSkipBag);\n"
	"\t\tLPITEM\t\t\tMt2009EkwAutoStackProto(const TItemTable* p, DWORD dwItemVnum, ITEM_COUNT& bCount, bool& bSkipBag);\n")

# ---------------------------------------------------------------- char_item.cpp
C = "char_item.cpp"
edit(C, "get", "\t\treturn m_PlayerSlots->pDSItems[wCell];\n\n\tdefault:\n\t\treturn NULL;\n\t}\n\treturn NULL;\n}\n",
	"\t\treturn m_PlayerSlots->pDSItems[wCell];\n\n"
	"\t// " + M + " (get): the category storages\n" + WINDOWS +
	"\t\treturn Mt2009SpecialGetItem(window_type, wCell);\n\n"
	"\tdefault:\n\t\treturn NULL;\n\t}\n\treturn NULL;\n}\n")
edit(C, "set", "\t\t\tm_PlayerSlots->pDSItems[wCell] = pItem;\n\t\t}\n\t\tbreak;\n\tdefault:\n\t\tsys_err (\"Invalid Inventory type %d\", window_type);\n",
	"\t\t\tm_PlayerSlots->pDSItems[wCell] = pItem;\n\t\t}\n\t\tbreak;\n"
	"\t// " + M + " (set): the category storages - an item takes its size down one column, as in the bag\n" + WINDOWS +
	"\t\tif (wCell >= SPECIAL_INVENTORY_MAX_NUM)\n\t\t{\n"
	"\t\t\tsys_err(\"CHARACTER::SetItem: invalid special storage cell %d\", wCell);\n\t\t\treturn;\n\t\t}\n"
	"\t\tMt2009SpecialSetItem(window_type, wCell, pItem);\n\t\tbreak;\n"
	"\tdefault:\n\t\tsys_err (\"Invalid Inventory type %d\", window_type);\n")
edit(C, "set window", "\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\tpItem->SetWindow(DRAGON_SOUL_INVENTORY);\n\t\t\tbreak;\n\t\t}\n\t}\n",
	"\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\tpItem->SetWindow(DRAGON_SOUL_INVENTORY);\n\t\t\tbreak;\n"
	"\t\t// " + M + " (set window)\n" + ind(WINDOWS, 1) +
	"\t\t\tpItem->SetWindow(window_type);\n\t\t\tbreak;\n\t\t}\n\t}\n")
edit(C, "clear", "\t\t\titem->RemoveFromCharacter();\n\t\t\tM2_DESTROY_ITEM(item);\n\t\t}\n\t}\n}\n\nbool CHARACTER::IsEmptyItemGrid",
	"\t\t\titem->RemoveFromCharacter();\n\t\t\tM2_DESTROY_ITEM(item);\n\t\t}\n\t}\n"
	"\tMt2009SpecialClearItems(); // " + M + " (clear): the category storages\n"
	"}\n\nbool CHARACTER::IsEmptyItemGrid")
edit(C, "grid", "\t\t\t\treturn true;\n\t\t\t}\n\t\t}\n\t}\n\treturn false;\n}\n\nbool CHARACTER::HasSlotForItem",
	"\t\t\t\treturn true;\n\t\t\t}\n\t\t}\n"
	"\t// " + M + " (grid): the category storages - on the cell's own page\n" + WINDOWS +
	"\t\treturn Mt2009SpecialIsEmptyGrid(Cell.window_type, Cell.cell, bSize, iExceptionCell);\n"
	"\t}\n\treturn false;\n}\n\nbool CHARACTER::HasSlotForItem")
edit(C, "valid pos",
	"\tcase DRAGON_SOUL_INVENTORY:\n\t\treturn cell < (DRAGON_SOUL_INVENTORY_MAX_NUM);\n\n\tcase SAFEBOX:\n\t\tif (NULL != m_pkSafebox)\n",
	"\tcase DRAGON_SOUL_INVENTORY:\n\t\treturn cell < (DRAGON_SOUL_INVENTORY_MAX_NUM);\n\n"
	"\t// " + M + " (valid pos): the category storages\n" + WINDOWS +
	"\t\treturn cell < SPECIAL_INVENTORY_MAX_NUM;\n\n"
	"\tcase SAFEBOX:\n\t\tif (NULL != m_pkSafebox)\n")
edit(C, "move", "\t\telse if (DRAGON_SOUL_INVENTORY == DestCell.window_type)\n\t\t\treturn false;\n\n\t\tLPITEM item2;\n",
	"\t\telse if (DRAGON_SOUL_INVENTORY == DestCell.window_type)\n\t\t\treturn false;\n\n"
	"\t\t// " + M + " (move): a storage takes only its category, from the bag or itself; out of it only into the bag\n"
	"\t\tif (!Mt2009SpecialMoveAllowed(item, Cell, DestCell))\n\t\t\treturn false;\n\n"
	"\t\tLPITEM item2;\n")
edit(C, "move quickslot",
	"\t\t\tif (INVENTORY == Cell.window_type && INVENTORY == DestCell.window_type)\n\t\t\t\tSyncQuickslot(QUICKSLOT_TYPE_ITEM, Cell.cell, DestCell.cell);\n",
	"\t\t\tif (INVENTORY == Cell.window_type && INVENTORY == DestCell.window_type)\n\t\t\t\tSyncQuickslot(QUICKSLOT_TYPE_ITEM, Cell.cell, DestCell.cell);\n"
	"\t\t\telse if (INVENTORY == Cell.window_type && Mt2009IsSpecialWindow(DestCell.window_type)) // " + M + " (move quickslot)\n"
	"\t\t\t\tSyncQuickslot(QUICKSLOT_TYPE_ITEM, Cell.cell, 255);\n")
edit(C, "drop quickslot", "\tSyncQuickslot(QUICKSLOT_TYPE_ITEM, Cell.cell, 255);\n\n\tLPITEM pkItemToDrop;\n",
	"\tif (!Mt2009IsSpecialWindow(Cell.window_type)) // " + M + " (drop quickslot): a storage's cell is no bag cell\n"
	"\t\tSyncQuickslot(QUICKSLOT_TYPE_ITEM, Cell.cell, 255);\n\n\tLPITEM pkItemToDrop;\n")
edit(C, "pickup cell",
	"\t\t\tint iEmptyCell = GetEmptyInventoryEx(item);\n\t\t\tif (iEmptyCell == -1)\n\t\t\t{\n\t\t\t\tsys_log(0, \"No empty inventory pid %u size %ud itemid %u\"",
	"\t\t\tBYTE bEkwWindow = INVENTORY; // " + M + " (pickup cell): a real player's item of a category into its storage\n"
	"\t\t\tint iEmptyCell = GetEmptyInventoryRouted(item, bEkwWindow);\n\t\t\tif (iEmptyCell == -1)\n\t\t\t{\n\t\t\t\tsys_log(0, \"No empty inventory pid %u size %ud itemid %u\"")
edit(C, "pickup add",
	"\t\t\titem->AddToCharacter(this, TItemPos(item->GetWindowInventoryEx(), iEmptyCell));\n\n\t\t\tchar szHint[32+1];\n",
	"\t\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell)); // " + M + " (pickup add)\n\n\t\t\tchar szHint[32+1];\n")
edit(C, "party cell",
	"\t\tint iEmptyCell = -1;\n\t\tif (!(owner && (iEmptyCell = owner->GetEmptyInventoryEx(item)) != -1))\n",
	"\t\tint iEmptyCell = -1;\n\t\tBYTE bEkwWindow = INVENTORY; // " + M + " (party cell): the owner's storage\n"
	"\t\tif (!(owner && (iEmptyCell = owner->GetEmptyInventoryRouted(item, bEkwWindow)) != -1))\n")
edit(C, "party add",
	"\t\titem->AddToCharacter(owner, TItemPos(item->GetWindowInventoryEx(), iEmptyCell));\n",
	"\t\titem->AddToCharacter(owner, TItemPos(bEkwWindow, iEmptyCell)); // " + M + " (party add)\n")
edit(C, "stack proto",
	"std::pair<bool, LPITEM> CHARACTER::AutoStackItemProto(DWORD dwItemVnum, ITEM_COUNT& bCount)\n{\n\tTItemTable * p = ITEM_MANAGER::instance().GetTable(dwItemVnum);\n\tif (!p)\n\t\treturn {false, nullptr};\n",
	"std::pair<bool, LPITEM> CHARACTER::AutoStackItemProto(DWORD dwItemVnum, ITEM_COUNT& bCount)\n{\n\tTItemTable * p = ITEM_MANAGER::instance().GetTable(dwItemVnum);\n\tif (!p)\n\t\treturn {false, nullptr};\n"
	"\t// " + M + " (stack proto): a routed item joins its storage's stacks; the bag's only when the storage is full\n"
	"\t{\n\t\tbool bEkwSkipBag = false;\n"
	"\t\tif (LPITEM pEkw = Mt2009EkwAutoStackProto(p, dwItemVnum, bCount, bEkwSkipBag))\n\t\t\treturn {true, pEkw};\n"
	"\t\tif (bEkwSkipBag)\n\t\t\treturn {true, nullptr};\n\t}\n")
edit(C, "stack", "LPITEM CHARACTER::AutoStackItem(LPITEM item)\n{\n",
	"LPITEM CHARACTER::AutoStackItem(LPITEM item)\n{\n"
	"\t// " + M + " (stack): a routed item joins its storage's stacks; the bag's only when the storage is full\n"
	"\t{\n\t\tbool bEkwSkipBag = false;\n"
	"\t\tif (LPITEM pEkw = Mt2009EkwAutoStack(item, bEkwSkipBag))\n\t\t\treturn pEkw;\n"
	"\t\tif (bEkwSkipBag)\n\t\t\treturn nullptr;\n\t}\n")
edit(C, "give",
	"\tint cell = GetEmptyInventoryEx(item);\n\tif (cell != -1)\n\t{\n\t\titem->AddToCharacter(this, TItemPos(item->GetWindowInventoryEx(), cell));\n",
	"\tBYTE bEkwWindow = INVENTORY; // " + M + " (give): a real player's item of a category into its storage\n"
	"\tint cell = GetEmptyInventoryRouted(item, bEkwWindow);\n\tif (cell != -1)\n\t{\n\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, cell));\n")
edit(C, "give vnum",
	"\tint iEmptyCell = GetEmptyInventoryEx(item);\n\tif (iEmptyCell != -1)\n\t{\n\t\tif (bMsg)\n\t\t\tChatPacketRecieveItem(this, item, original_count);\n\n\t\titem->AddToCharacter(this, TItemPos(item->GetWindowInventoryEx(), iEmptyCell));\n",
	"\tBYTE bEkwWindow = INVENTORY; // " + M + " (give vnum): a real player's item of a category into its storage\n"
	"\tint iEmptyCell = GetEmptyInventoryRouted(item, bEkwWindow);\n\tif (iEmptyCell != -1)\n\t{\n\t\tif (bMsg)\n\t\t\tChatPacketRecieveItem(this, item, original_count);\n\n"
	"\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell));\n")
edit(C, "count",
	"\t\t\t\tcount += item->GetCount();\n\t\t\t}\n\t\t}\n\t}\n\n\treturn count;\n}\n\nvoid CHARACTER::RemoveSpecifyItem(DWORD vnum, ITEM_COUNT count)\n",
	"\t\t\t\tcount += item->GetCount();\n\t\t\t}\n\t\t}\n\t}\n\n"
	"\tcount += Mt2009SpecialCountItem(vnum); // " + M + " (count): the category storages\n"
	"\treturn count;\n}\n\nvoid CHARACTER::RemoveSpecifyItem(DWORD vnum, ITEM_COUNT count)\n")
edit(C, "remove",
	"\tif (count)\n\t\tsys_log(0, \"CHARACTER::RemoveSpecifyItem cannot remove enough item vnum %u, still remain %d\", vnum, count);\n",
	"\tcount = Mt2009SpecialRemoveItem(vnum, count); // " + M + " (remove): what the bag lacked, from the storages\n"
	"\tif (count)\n\t\tsys_log(0, \"CHARACTER::RemoveSpecifyItem cannot remove enough item vnum %u, still remain %d\", vnum, count);\n")
edit(C, "npc refine",
	"void CHARACTER::ReceiveItem(LPCHARACTER from, LPITEM item)\n{\n\tif (IsPC())\n\t\treturn;\n",
	"void CHARACTER::ReceiveItem(LPCHARACTER from, LPITEM item)\n{\n\tif (IsPC())\n\t\treturn;\n"
	"\t// " + M + " (npc refine): the refine window reads its item by a bag cell - a storage's item goes to the bag first\n"
	"\tif (item && Mt2009IsSpecialWindow(item->GetWindow()))\n\t{\n\t\tswitch (GetRaceNum())\n\t\t{\n"
	"\t\t\tcase fishing::FISHER_MOB:\n\t\t\tcase HERB_BLACKSMITH:\n\t\t\tcase PICKAXE_BLACKSMITH:\n"
	"\t\t\tcase DEVILTOWER_BLACKSMITH_WEAPON_MOB:\n\t\t\tcase DEVILTOWER_BLACKSMITH_ARMOR_MOB:\n\t\t\tcase DEVILTOWER_BLACKSMITH_ACCESSORY_MOB:\n"
	"\t\t\tcase BLACKSMITH_MOB:\n\t\t\tcase BLACKSMITH2_MOB:\n\t\t\tcase BLACKSMITH_WEAPON_MOB:\n\t\t\tcase BLACKSMITH_ARMOR_MOB:\n\t\t\tcase BLACKSMITH_ACCESSORY_MOB:\n"
	"\t\t\t\tfrom->ChatPacket(CHAT_TYPE_INFO, \"Przenies przedmiot z dodatkowego ekwipunku do zwyklego, aby go ulepszyc.\");\n"
	"\t\t\t\treturn;\n\t\t}\n\t}\n")
edit(C, "scroll refine",
	"bool CHARACTER::RefineItem(LPITEM pkItem, LPITEM pkTarget)\n{\n\tif (!CanHandleItem())\n\t\treturn false;\n",
	"bool CHARACTER::RefineItem(LPITEM pkItem, LPITEM pkTarget)\n{\n\tif (!CanHandleItem())\n\t\treturn false;\n"
	"\t// " + M + " (scroll refine): the refine window reads both items by bag cells\n"
	"\tif ((pkItem && Mt2009IsSpecialWindow(pkItem->GetWindow())) || (pkTarget && Mt2009IsSpecialWindow(pkTarget->GetWindow())))\n\t{\n"
	"\t\tChatPacket(CHAT_TYPE_INFO, \"Przenies przedmiot z dodatkowego ekwipunku do zwyklego, aby go ulepszyc.\");\n"
	"\t\treturn false;\n\t}\n")

# ---------------------------------------------------------------- item.cpp
I = "item.cpp"
edit(I, "remove",
	"\t\t\t\t\tpOwner->SetItem(TItemPos(m_bWindow, m_wCell), NULL);\n\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\tTItemPos cell(INVENTORY, m_wCell);\n",
	"\t\t\t\t\tpOwner->SetItem(TItemPos(m_bWindow, m_wCell), NULL);\n\t\t\t}\n"
	"\t\t\t// " + M + " (remove): an item of a category storage leaves its own window, not the bag's cell of that number\n"
	"\t\t\telse if (Mt2009IsSpecialWindow(m_bWindow))\n\t\t\t{\n"
	"\t\t\t\tif (m_wCell >= SPECIAL_INVENTORY_MAX_NUM)\n"
	"\t\t\t\t\tsys_err(\"CItem::RemoveFromCharacter: pos >= SPECIAL_INVENTORY_MAX_NUM\");\n"
	"\t\t\t\telse\n\t\t\t\t\tpOwner->SetItem(TItemPos(m_bWindow, m_wCell), NULL);\n\t\t\t}\n"
	"\t\t\telse\n\t\t\t{\n\t\t\t\tTItemPos cell(INVENTORY, m_wCell);\n")
edit(I, "count quickslot",
	"\t\t\tif (!IsDragonSoul())\n\t\t\t{\n\t\t\t\tm_pOwner->SyncQuickslot(QUICKSLOT_TYPE_ITEM, m_wCell, 255);\n",
	"\t\t\tif (!IsDragonSoul() && !Mt2009IsSpecialWindow(GetWindow())) // " + M + " (count quickslot)\n"
	"\t\t\t{\n\t\t\t\tm_pOwner->SyncQuickslot(QUICKSLOT_TYPE_ITEM, m_wCell, 255);\n")

# ---------------------------------------------------------------- item_manager.cpp
edit("item_manager.cpp", "remove quickslot",
	"\t\telse\n\t\t{\n\t\t\to->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);\n\t\t\titem->RemoveFromCharacter();\n",
	"\t\telse\n\t\t{\n"
	"\t\t\tif (!Mt2009IsSpecialWindow(item->GetWindow())) // " + M + " (remove quickslot): a storage's cell is no bag cell\n"
	"\t\t\t\to->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);\n\t\t\titem->RemoveFromCharacter();\n")

# ---------------------------------------------------------------- input_db.cpp
edit("input_db.cpp", "load",
	"\t\t\t\tcase INVENTORY:\n\t\t\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\t\t\titem->AddToCharacter(ch, TItemPos(p->window, p->pos));\n\t\t\t\t\tbreak;\n",
	"\t\t\t\tcase INVENTORY:\n\t\t\t\tcase DRAGON_SOUL_INVENTORY:\n\t\t\t\t\titem->AddToCharacter(ch, TItemPos(p->window, p->pos));\n\t\t\t\t\tbreak;\n\n"
	"\t\t\t\t// " + M + " (load): the category storages - a taken or broken cell gives the item a bag cell below\n" +
	ind(WINDOWS, 3) +
	"\t\t\t\t\tif (p->pos >= SPECIAL_INVENTORY_MAX_NUM || ch->GetItem(TItemPos(p->window, p->pos)))\n"
	"\t\t\t\t\t\tv.emplace_back(item);\n\t\t\t\t\telse\n"
	"\t\t\t\t\t\titem->AddToCharacter(ch, TItemPos(p->window, p->pos));\n\t\t\t\t\tbreak;\n")

# ---------------------------------------------------------------- input_main.cpp
edit("input_main.cpp", "safebox in",
	"\tpkItem->RemoveFromCharacter();\n\tif (!pkItem->IsDragonSoul())\n\t\tch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, p->ItemPos.cell, 255);\n",
	"\tpkItem->RemoveFromCharacter();\n"
	"\tif (!pkItem->IsDragonSoul() && !Mt2009IsSpecialWindow(p->ItemPos.window_type)) // " + M + " (safebox in)\n"
	"\t\tch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, p->ItemPos.cell, 255);\n")
edit("input_main.cpp", "safebox out",
	"\tif (!ch->IsEmptyItemGrid(p->ItemPos, pkItem->GetSize()))\n\t\treturn;\n\n\tif (pkItem->IsDragonSoul())\n",
	"\tif (!ch->IsEmptyItemGrid(p->ItemPos, pkItem->GetSize()))\n\t\treturn;\n\n"
	"\t// " + M + " (safebox out): into a category storage only its own items\n"
	"\tif (!ch->Mt2009SpecialCheckoutAllowed(pkItem, p->ItemPos))\n\t\treturn;\n\n"
	"\tif (pkItem->IsDragonSoul())\n")

# ---------------------------------------------------------------- exchange.cpp
X = "exchange.cpp"
edit(X, "done cell",
	"\t\tif (item->IsDragonSoul())\n\t\t\tempty_pos = victim->GetEmptyDragonSoulInventory(item);\n\t\telse\n\t\t\tempty_pos = victim->GetEmptyInventory(item->GetSize());\n",
	"\t\t// " + M + " (done cell): the Alchemy's, a real player's category storage or the bag\n"
	"\t\tBYTE bEkwWindow = INVENTORY;\n"
	"\t\tempty_pos = victim->GetEmptyInventoryRouted(item, bEkwWindow);\n")
edit(X, "done add",
	"\t\tm_pOwner->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);\n\n\t\titem->RemoveFromCharacter();\n\t\titem->AddToCharacter(victim, TItemPos(item->GetWindowInventoryEx(), empty_pos));\n",
	"\t\tif (!Mt2009IsSpecialWindow(item->GetWindow())) // " + M + " (done add)\n"
	"\t\t\tm_pOwner->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);\n\n"
	"\t\titem->RemoveFromCharacter();\n\t\titem->AddToCharacter(victim, TItemPos(bEkwWindow, empty_pos));\n")

# ---------------------------------------------------------------- shop.cpp (an NPC's and the old player shop's buy)
S = "shop.cpp"
edit(S, "buy cell",
	"\tint iEmptyPos = ch->GetEmptyInventoryEx(item);\n\tif (iEmptyPos < 0)\n\t{\n\t\tif (m_pkPC)\n",
	"\tBYTE bEkwWindow = INVENTORY; // " + M + " (buy cell): a real player's item of a category into its storage\n"
	"\tint iEmptyPos = ch->GetEmptyInventoryRouted(item, bEkwWindow);\n\tif (iEmptyPos < 0)\n\t{\n\t\tif (m_pkPC)\n")
edit(S, "buy add pc",
	"\t\t\titem->RemoveFromCharacter();\n\t\t\titem->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), iEmptyPos));\n",
	"\t\t\titem->RemoveFromCharacter();\n\t\t\titem->AddToCharacter(ch, TItemPos(bEkwWindow, iEmptyPos)); // " + M + " (buy add pc)\n")
edit(S, "buy add",
	"\t\titem->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), iEmptyPos));\n\t\tITEM_MANAGER::instance().FlushDelayedSave(item);\n\t\tLogManager::instance().ItemLog(ch, item, \"BUY\", item->GetName());\n",
	"\t\titem->AddToCharacter(ch, TItemPos(bEkwWindow, iEmptyPos)); // " + M + " (buy add)\n"
	"\t\tITEM_MANAGER::instance().FlushDelayedSave(item);\n\t\tLogManager::instance().ItemLog(ch, item, \"BUY\", item->GetName());\n")

# ---------------------------------------------------------------- shop_manager.cpp (the sale from a storage)
edit("shop_manager.cpp", "sell",
	"\tLPITEM item = ch->GetInventoryItem(bCell);\n",
	"\t// " + M + " (sell): \"/ekwipunek sprzedaj\" sells from a category storage (playerbot_ekwipunek.cpp)\n"
	"\textern BYTE g_bMt2009EkwSellWindow;\n"
	"\tLPITEM item = ch->GetItem(TItemPos(g_bMt2009EkwSellWindow, bCell));\n")

# ---------------------------------------------------------------- cube.cpp (an item of a storage in the crafting window)
edit("cube.cpp", "cube add",
	"\titem = ch->GetInventoryItem(inven_index);\n",
	"\t// " + M + " (cube add): \"/ekwipunek kostka\" takes it from a category storage (playerbot_ekwipunek.cpp)\n"
	"\textern BYTE g_bMt2009EkwCubeWindow;\n"
	"\titem = ch->GetItem(TItemPos(g_bMt2009EkwCubeWindow, inven_index));\n")

# ---------------------------------------------------------------- char.cpp (the offline shop's items back)
edit("char.cpp", "ikashop",
	"\t\tpos->cell = emptyPos = GetEmptyInventory(item->GetSize());\n\t\tpos->window_type = INVENTORY;\n",
	"\t\t// " + M + " (ikashop): a real player's item of a category into its storage\n"
	"\t\tBYTE bEkwWindow = INVENTORY;\n"
	"\t\tpos->cell = emptyPos = GetEmptyInventoryRouted(item, bEkwWindow);\n\t\tpos->window_type = bEkwWindow;\n")

# ---------------------------------------------------------------- cmd_gm.cpp (/item)
edit("cmd_gm.cpp", "gm item",
	"\t\tint iEmptyPos = ch->GetEmptyInventoryEx(item);\n\t\tif (iEmptyPos != -1)\n\t\t{\n\t\t\titem->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), iEmptyPos));\n\t\t\tLogManager::instance().ItemLog(ch, item, \"GM\", item->GetName());\n",
	"\t\tBYTE bEkwWindow = INVENTORY; // " + M + " (gm item): as a pickup, into the category's storage\n"
	"\t\tint iEmptyPos = ch->GetEmptyInventoryRouted(item, bEkwWindow);\n\t\tif (iEmptyPos != -1)\n\t\t{\n"
	"\t\t\titem->AddToCharacter(ch, TItemPos(bEkwWindow, iEmptyPos));\n\t\t\tLogManager::instance().ItemLog(ch, item, \"GM\", item->GetName());\n")

# ---------------------------------------------------------------- cmd.cpp
edit("cmd.cpp", "declare",
	"ACMD(do_buffi);\t// MT2009_PLUS_BUFFI_V1 (declare): Buffi, root/uibuffi.py (playerbot_buffi.cpp)\n",
	"ACMD(do_buffi);\t// MT2009_PLUS_BUFFI_V1 (declare): Buffi, root/uibuffi.py (playerbot_buffi.cpp)\n"
	"ACMD(do_ekwipunek);\t// " + M + " (declare): Dodatkowy ekwipunek, root/uiekwipunek.py (playerbot_ekwipunek.cpp)\n")
edit("cmd.cpp", "table",
	"\t{ \"buffi\",\tdo_buffi,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_BUFFI_V1 (table)\n",
	"\t{ \"buffi\",\tdo_buffi,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_BUFFI_V1 (table)\n"
	"\t{ \"ekwipunek\",\tdo_ekwipunek,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// " + M + " (table)\n")

# ---------------------------------------------------------------- db ClientManagerPlayer.cpp
D = "../../db/src/ClientManagerPlayer.cpp"
OLDW = "('INVENTORY','EQUIPMENT','DRAGON_SOUL_INVENTORY','BELT_INVENTORY')"
NEWW = "('INVENTORY','EQUIPMENT','DRAGON_SOUL_INVENTORY','BELT_INVENTORY','UPGRADE_INVENTORY','BOOK_INVENTORY','STONE_INVENTORY','CHANGE_INVENTORY','CHEST_INVENTORY')"
for tag, lead in (("select 1", "\t\t\t\t\t"), ("select 2", "\t\t\t\t")):
	edit(D, tag,
		"transmutation \" // MT2009_PLUS_CHANGE_LOOK_V1 (%s)\n%s\"FROM item%%s WHERE owner_id=%%d AND (`window` in %s)\",\n" % (tag, lead, OLDW),
		"transmutation \" // MT2009_PLUS_CHANGE_LOOK_V1 (%s)\n%s\"FROM item%%s WHERE owner_id=%%d AND (`window` in %s)\", // %s (%s): the category storages\n" % (tag, lead, NEWW, M, tag))
edit(D, "delete",
	"\"DELETE FROM item%%s WHERE owner_id=%%d AND (`window` in %s)\", GetTablePostfix(), pi->player_id);\n" % OLDW,
	"\"DELETE FROM item%%s WHERE owner_id=%%d AND (`window` in %s)\", GetTablePostfix(), pi->player_id); // %s (delete)\n" % (NEWW, M))


def main():
	json.dump(E, open(os.path.join(HERE, "edits.json"), "w"), indent=1)
	print("ekwipunek: %d edit(s) written" % len(E))
	if len(sys.argv) > 1:
		bad = 0
		for e in E:
			text = open(os.path.join(sys.argv[1], e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
			if e["marker"] in text:
				continue
			n = text.count(e["old"])
			if n != 1:
				bad += 1
				print("  %s %s: old found %d time(s)" % (e["file"], e["marker"], n))
		print("check: %s" % ("ok" if not bad else "%d bad" % bad))


if __name__ == "__main__":
	main()
