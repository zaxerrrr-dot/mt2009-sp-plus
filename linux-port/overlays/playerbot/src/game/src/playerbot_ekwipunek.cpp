// MT2009_PLUS_EKWIPUNEK_V1: Dodatkowy ekwipunek - Ameria Project's special storage (srcs/server/game char_item.cpp,
// item.cpp, cmd_general.cpp under ENABLE_SPECIAL_STORAGE; root/uispecialinventory.py, uispecialstorage.py), ported for
// Yohara 3.0 (the owner, 21 October 2026: "Dodaj okno dodatkowego ekwipunku z Amerii, z automatycznym wpadaniem
// przedmiotow do danych kategorii"). server-patches/ekwipunek/README.md has the whole picture; the engine's hooks are
// server-patches/ekwipunek (edits.json) and call the methods and free functions of this file.
//
// Ameria's storage, as here: windows of their own in the item position (Ameria UPGRADE_INVENTORY .. CHEST_INVENTORY;
// here appended after the Ikarus shop's windows, 11-15, so player.item.window keeps every old number - the DB enum is
// appended the same way, ekwipunek.sql), four pages of 5 x 9 cells each (SPECIAL_INVENTORY_MAX_NUM 180), items of one
// category only:
//   UPGRADE_INVENTORY  ITEM_MATERIAL / MATERIAL_LEATHER (the refine materials) and Ameria's 27987, 27799, 70031,
//                      27992-27994;
//   BOOK_INVENTORY     ITEM_SKILLBOOK and Ameria's extra books 50301-50303;
//   STONE_INVENTORY    ITEM_METIN / METIN_NORMAL (the soul stones);
//   CHANGE_INVENTORY   ITEM_USE / USE_CHANGE_ATTRIBUTE (Zaczarowanie przedmiotu) and Ameria's 72346;
//   CHEST_INVENTORY    ITEM_GIFTBOX (the chests).
// Ameria's sixth window, COSTUME_INVENTORY, is left out: its CItem::IsCostume() returns false before anything else
// ("when create false for to inv"), so Ameria never fills it.
//
// What a real player picks up, is given (quests, chests, AutoGiveItem), buys in an NPC shop, takes in a trade or from
// an offline shop goes straight into its category's storage (GetEmptyInventoryRouted) and joins the stacks there
// first (Mt2009EkwAutoStack*). Unlike Ameria, a full storage is no refusal: the item goes into the bag as before.
// Only a client that said so routes ("/ekwipunek hello", root/uiekwipunek.py with the 3.0 exe that knows the windows)
// - an old exe would not show these windows, so its player's items stay in the bag. Bots never route: their AI scans
// INVENTORY only (selling, storing, crafting), so a bot's items stay where it looks for them.
//
// Back out: a drag into the bag (MoveItem), a use from the storage (UseItem takes any window), the refine materials and
// quest items counted and taken from the storages too (CountSpecifyItem / RemoveSpecifyItem), the NPC shop's sale
// ("/ekwipunek sprzedaj"), the safebox both ways, a trade, the crafting window ("/ekwipunek kostka"). Items already in
// a bag stay there - Ameria has no button that moves them (a drag does).
//
// Commands (root/uiekwipunek.py):
//   /ekwipunek hello                              this client knows the windows - route from now on
//   /ekwipunek sortuj <window>                    Ameria's two buttons in one: stacks joined, then sorted by kind
//   /ekwipunek sprzedaj <window> <cell> <count>   the NPC shop's sale from a storage (CShopManager::Sell)
//   /ekwipunek kostka <cube index> <window> <cell> an item of a storage into the crafting window (Cube_add_item)
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "shop.h"
#include "shop_manager.h"
#include "cube.h"
#include "cmd.h"
#include "../../common/PulseManager.h"

#include <algorithm>
#include <cstdlib>
#include <vector>

// The DB enum (ekwipunek.sql) and the client's windows (client-patches/exe) count on these numbers.
static_assert(UPGRADE_INVENTORY == 11 && CHEST_INVENTORY == 15, "MT2009_PLUS_EKWIPUNEK_V1: the storages are windows 11-15");
static_assert(SPECIAL_INVENTORY_WINDOW_COUNT == CHEST_INVENTORY - UPGRADE_INVENTORY + 1, "MT2009_PLUS_EKWIPUNEK_V1: window count");

// The NPC shop's sale and the crafting window take their item from this window while the command runs
// (shop_manager.cpp, cube.cpp - MT2009_PLUS_EKWIPUNEK_V1 (sell) / (cube)); INVENTORY at any other time.
BYTE g_bMt2009EkwSellWindow = INVENTORY;
BYTE g_bMt2009EkwCubeWindow = INVENTORY;

static const ePulse MT2009_PLUS_PULSE_EKW_SORT = static_cast<ePulse>(0x4D540E01);

static inline int EkwBase(BYTE bWindow)
{
	return (bWindow - UPGRADE_INVENTORY) * SPECIAL_INVENTORY_MAX_NUM;
}

// The category of an item kind: its storage's window, 0 for none (Ameria's CItem::IsUpgradeItem / IsBook / IsStone /
// IsChange / IsChest).
BYTE Mt2009EkwCategoryOf(BYTE bType, BYTE bSubType, DWORD dwVnum)
{
	switch (dwVnum)
	{
		case 27987:
		case 27799:
		case 70031:
		case 27992:
		case 27993:
		case 27994:
			return UPGRADE_INVENTORY;
		case 50301:
		case 50302:
		case 50303:
			return BOOK_INVENTORY;
		case 72346:
			return CHANGE_INVENTORY;
	}

	if (bType == ITEM_MATERIAL && bSubType == MATERIAL_LEATHER)
		return UPGRADE_INVENTORY;
	if (bType == ITEM_SKILLBOOK)
		return BOOK_INVENTORY;
	if (bType == ITEM_METIN && bSubType == METIN_NORMAL)
		return STONE_INVENTORY;
	if (bType == ITEM_USE && bSubType == USE_CHANGE_ATTRIBUTE)
		return CHANGE_INVENTORY;
	if (bType == ITEM_GIFTBOX)
		return CHEST_INVENTORY;
	return 0;
}

BYTE Mt2009EkwCategoryOfItem(LPITEM item)
{
	if (!item || item->IsDragonSoul())
		return 0;
	return Mt2009EkwCategoryOf(item->GetType(), item->GetSubType(), item->GetVnum());
}

bool CHARACTER::IsSpecialStorageClient() const
{
	return m_PlayerSlots && m_PlayerSlots->bSpecialStorageClient;
}

void CHARACTER::SetSpecialStorageClient(bool bOn)
{
	if (m_PlayerSlots)
		m_PlayerSlots->bSpecialStorageClient = bOn;
}

// Whether this character's items of a category go into its storage: a real player whose client knows the windows.
bool CHARACTER::Mt2009EkwRoutes() const
{
	return IsSpecialStorageClient() && GetDesc() && !GetDesc()->IsBot();
}

BYTE CHARACTER::GetSpecialWindowFor(LPITEM item) const
{
	if (!Mt2009EkwRoutes())
		return 0;
	return Mt2009EkwCategoryOfItem(item);
}

LPITEM CHARACTER::Mt2009SpecialGetItem(BYTE bWindow, WORD wCell) const
{
	if (!m_PlayerSlots || !Mt2009IsSpecialWindow(bWindow) || wCell >= SPECIAL_INVENTORY_MAX_NUM)
		return NULL;
	return m_PlayerSlots->pSpecialItems[EkwBase(bWindow) + wCell];
}

// CHARACTER::SetItem's part for a storage: the item at its cell, its size down one column in the grid (cell + 1 there).
void CHARACTER::Mt2009SpecialSetItem(BYTE bWindow, WORD wCell, LPITEM pItem)
{
	if (!m_PlayerSlots || !Mt2009IsSpecialWindow(bWindow) || wCell >= SPECIAL_INVENTORY_MAX_NUM)
		return;

	const int base = EkwBase(bWindow);
	LPITEM pOld = m_PlayerSlots->pSpecialItems[base + wCell];
	if (pOld)
	{
		for (int i = 0; i < pOld->GetSize(); ++i)
		{
			const int p = wCell + i * SPECIAL_INVENTORY_PAGE_COLUMN;
			if (p >= SPECIAL_INVENTORY_MAX_NUM)
				continue;
			if (m_PlayerSlots->pSpecialItems[base + p] && m_PlayerSlots->pSpecialItems[base + p] != pOld)
				continue;
			m_PlayerSlots->wSpecialItemGrid[base + p] = 0;
		}
	}

	if (pItem)
	{
		for (int i = 0; i < pItem->GetSize(); ++i)
		{
			const int p = wCell + i * SPECIAL_INVENTORY_PAGE_COLUMN;
			if (p >= SPECIAL_INVENTORY_MAX_NUM)
				continue;
			m_PlayerSlots->wSpecialItemGrid[base + p] = wCell + 1;
		}
	}

	m_PlayerSlots->pSpecialItems[base + wCell] = pItem;
}

// IsEmptyItemGrid's part for a storage: bSize cells down one column, all on the cell's own page, free or the
// iExceptionCell item's own.
bool CHARACTER::Mt2009SpecialIsEmptyGrid(BYTE bWindow, WORD wCell, BYTE bSize, int iExceptionCell) const
{
	if (!m_PlayerSlots || !Mt2009IsSpecialWindow(bWindow) || wCell >= SPECIAL_INVENTORY_MAX_NUM || bSize < 1)
		return false;

	const int row = (wCell % SPECIAL_INVENTORY_PAGE_SIZE) / SPECIAL_INVENTORY_PAGE_COLUMN;
	if (row + bSize > SPECIAL_INVENTORY_PAGE_ROW)
		return false;

	const int base = EkwBase(bWindow);
	const int except = iExceptionCell + 1;
	for (int i = 0; i < bSize; ++i)
	{
		const int p = wCell + i * SPECIAL_INVENTORY_PAGE_COLUMN;
		const WORD w = m_PlayerSlots->wSpecialItemGrid[base + p];
		if (w && (except <= 0 || w != except))
			return false;
	}
	return true;
}

int CHARACTER::GetEmptySpecialInventory(BYTE bWindow, BYTE bSize) const
{
	if (!Mt2009IsSpecialWindow(bWindow))
		return -1;
	for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		if (Mt2009SpecialIsEmptyGrid(bWindow, i, bSize, -1))
			return i;
	return -1;
}

// GetEmptyInventoryEx with the storages: the cell and the window it is in - the Alchemy's for a dragon stone, the
// category's storage for a real player's item of a category while the storage has room, else the bag.
int CHARACTER::GetEmptyInventoryRouted(LPITEM item, BYTE& bWindow)
{
	bWindow = INVENTORY;
	if (!item)
		return -1;

	if (item->IsDragonSoul())
	{
		bWindow = DRAGON_SOUL_INVENTORY;
		return GetEmptyDragonSoulInventory(item);
	}

	if (BYTE bSpecial = GetSpecialWindowFor(item))
	{
		const int cell = GetEmptySpecialInventory(bSpecial, item->GetSize());
		if (cell >= 0)
		{
			bWindow = bSpecial;
			return cell;
		}
	}

	return GetEmptyInventory(item->GetSize());
}

void CHARACTER::Mt2009SpecialClearItems()
{
	for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
	{
		for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = Mt2009SpecialGetItem(w, i);
			if (!item)
				continue;
			item->SetSkipSave(true);
			ITEM_MANAGER::instance().FlushDelayedSave(item);
			item->RemoveFromCharacter();
			M2_DESTROY_ITEM(item);
		}
	}
}

ITEM_COUNT CHARACTER::Mt2009SpecialCountItem(DWORD dwVnum) const
{
	if (!m_PlayerSlots)
		return 0;

	ITEM_COUNT count = 0;
	for (LPITEM item : m_PlayerSlots->pSpecialItems)
	{
		if (!item || item->GetVnum() != dwVnum)
			continue;
		if (m_pkMyShop && m_pkMyShop->IsSellingItem(item->GetID()))
			continue;
		count += item->GetCount();
	}
	return count;
}

// What the bag could not give of RemoveSpecifyItem's count, taken from the storages; returns what is still missing.
ITEM_COUNT CHARACTER::Mt2009SpecialRemoveItem(DWORD dwVnum, ITEM_COUNT count)
{
	if (!m_PlayerSlots)
		return count;

	for (size_t i = 0; count > 0 && i < m_PlayerSlots->pSpecialItems.size(); ++i)
	{
		LPITEM item = m_PlayerSlots->pSpecialItems[i];
		if (!item || item->GetVnum() != dwVnum)
			continue;
		if (m_pkMyShop && m_pkMyShop->IsSellingItem(item->GetID()))
			continue;

		if (count >= item->GetCount())
		{
			count -= item->GetCount();
			item->SetCount(0);
		}
		else
		{
			item->SetCount(item->GetCount() - count);
			count = 0;
		}
	}
	return count;
}

// MoveItem's rule for the storages (Ameria's: a storage takes only its category, an item of a category goes back to
// the bag): into a storage only its own items, from the bag (not worn) or from itself; out of a storage only into the
// bag. A move between two windows checks the target cells itself - IsEmptyItemGrid's exception cell is a cell of the
// source window, which the target's grid knows nothing of.
bool CHARACTER::Mt2009SpecialMoveAllowed(LPITEM item, const TItemPos& Cell, const TItemPos& DestCell)
{
	const bool bSrc = Mt2009IsSpecialWindow(Cell.window_type);
	const bool bDst = Mt2009IsSpecialWindow(DestCell.window_type);
	if (!bSrc && !bDst)
		return true;

	if (bDst)
	{
		if (Cell.window_type != DestCell.window_type && Cell.window_type != INVENTORY)
			return false;
		if (item->IsEquipped() || Cell.IsEquipPosition())
			return false;
		if (Mt2009EkwCategoryOfItem(item) != DestCell.window_type)
		{
			ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot nie pasuje do tej kategorii dodatkowego ekwipunku.");
			return false;
		}
	}
	else if (DestCell.window_type != INVENTORY)
		return false;

	if (Cell.window_type != DestCell.window_type)
	{
		LPITEM pDest = GetItem(DestCell);
		if (pDest && pDest != item && pDest->GetVnum() == item->GetVnum())
			return true;	// MoveItem joins the stacks
		if (!IsEmptyItemGrid(DestCell, item->GetSize(), -1))
			return false;
	}
	return true;
}

// A safebox's or the item mall's item taken out into a storage: only its own category (SafeboxCheckout).
bool CHARACTER::Mt2009SpecialCheckoutAllowed(LPITEM item, const TItemPos& DestCell)
{
	if (!Mt2009IsSpecialWindow(DestCell.window_type))
		return true;
	if (Mt2009EkwCategoryOfItem(item) == DestCell.window_type)
		return true;
	ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot nie pasuje do tej kategorii dodatkowego ekwipunku.");
	return false;
}

namespace
{
	// char_item.cpp's IsStackableCorDraconisVnum (static there; the same list): a Cor Draconis stacks whatever its
	// proto says, in a storage as in the bag.
	bool EkwCorStack(DWORD vnum)
	{
		switch (vnum)
		{
			case 50252: case 50255: case 50256: case 50257: case 50258: case 50259: case 50260:
			case 51501: case 51502: case 51503: case 51504: case 51505: case 51506: case 51507: case 51508: case 51509: case 51510:
			case 51541: case 51548: case 51549: case 51562: case 51569: case 51576: case 51583: case 51590: case 51597:
			case 51604: case 51611: case 51618: case 51625: case 51632: case 76040:
				return true;
		}
		return false;
	}

	bool EkwStacks(LPITEM item)
	{
		return (item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK)) || EkwCorStack(item->GetVnum());
	}

	bool EkwSameSockets(LPITEM a, LPITEM b)
	{
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			if (a->GetSocket(i) != b->GetSocket(i))
				return false;
		return true;
	}

	bool EkwProtoSockets(LPITEM item)
	{
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			if (item->GetSocket(i) != item->GetProto()->alSockets[i])
				return false;
		return true;
	}
}

// AutoStackItem's first part for a routed item: the stacks of its storage take it. Returns the stack that took all of
// it (the item is destroyed then, as AutoStackItem does); bSkipBag says the rest has a cell in the storage, so the bag's
// stacks are left alone.
LPITEM CHARACTER::Mt2009EkwAutoStack(LPITEM item, bool& bSkipBag)
{
	bSkipBag = false;
	const BYTE bWindow = GetSpecialWindowFor(item);
	if (!bWindow)
		return NULL;

	if (EkwStacks(item))
	{
		ITEM_COUNT bCount = item->GetCount();
		for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item2 = Mt2009SpecialGetItem(bWindow, i);
			if (!item2 || item2 == item || item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
				continue;
			if (item2->GetCount() >= item2->GetMaxStack())
				continue;

			const ITEM_COUNT bCount2 = MIN(item2->GetMaxStack() - item2->GetCount(), bCount);
			bCount -= bCount2;
			item2->SetCount(item2->GetCount() + bCount2);
			if (bCount == 0)
			{
				M2_DESTROY_ITEM(item);
				return item2;
			}
		}
		item->SetCount(bCount);
	}

	bSkipBag = GetEmptySpecialInventory(bWindow, item->GetSize()) >= 0;
	return NULL;
}

// AutoStackItemProto's first part (AutoGiveItem by vnum): the same for a vnum and a count, the stacks with the proto's
// sockets only, the count raised to the proto's value1 for a MAKECOUNT item, as there.
LPITEM CHARACTER::Mt2009EkwAutoStackProto(const TItemTable* p, DWORD dwItemVnum, ITEM_COUNT& bCount, bool& bSkipBag)
{
	bSkipBag = false;
	if (!p || !Mt2009EkwRoutes())
		return NULL;
	const BYTE bWindow = Mt2009EkwCategoryOf(p->bType, p->bSubType, dwItemVnum);
	if (!bWindow || p->bType == ITEM_DS || p->bType == ITEM_SPECIAL_DS)
		return NULL;

	if (((p->dwFlags & ITEM_FLAG_STACKABLE) && !IS_SET(p->dwAntiFlags, ITEM_ANTIFLAG_STACK)) || EkwCorStack(dwItemVnum))
	{
		for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = Mt2009SpecialGetItem(bWindow, i);
			if (!item || item->GetVnum() != dwItemVnum || !EkwProtoSockets(item))
				continue;

			if (IS_SET(p->dwFlags, ITEM_FLAG_MAKECOUNT) && bCount < (ITEM_COUNT) p->alValues[1])
				bCount = p->alValues[1];

			if (item->GetCount() >= item->GetMaxStack())
				continue;

			const ITEM_COUNT bCount2 = MIN(item->GetMaxStack() - item->GetCount(), bCount);
			bCount -= bCount2;
			item->SetCount(item->GetCount() + bCount2);
			if (bCount == 0)
				return item;
		}
	}

	bSkipBag = GetEmptySpecialInventory(bWindow, p->bSize) >= 0;
	return NULL;
}

// Ameria's "stack" and "sort" buttons (do_sort_special_storage, do_real_sort_items) in one: the stacks of one vnum and
// the same sockets joined, then every item put back from the first cell on, ordered by type, subtype and vnum.
static void EkwSort(LPCHARACTER ch, BYTE bWindow)
{
	// join the stacks
	for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->Mt2009SpecialGetItem(bWindow, i);
		if (!item || item->isLocked() || item->IsExchanging())
			continue;
		if (!EkwStacks(item))
			continue;

		for (WORD j = i + 1; j < SPECIAL_INVENTORY_MAX_NUM && item->GetCount() < item->GetMaxStack(); ++j)
		{
			LPITEM item2 = ch->Mt2009SpecialGetItem(bWindow, j);
			if (!item2 || item2 == item || item2->isLocked() || item2->IsExchanging())
				continue;
			if (item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
				continue;

			const ITEM_COUNT add = MIN(item->GetMaxStack() - item->GetCount(), item2->GetCount());
			item->SetCount(item->GetCount() + add);
			item2->SetCount(item2->GetCount() - add);
		}
	}

	// sort
	std::vector<LPITEM> items;
	for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->Mt2009SpecialGetItem(bWindow, i);
		if (!item || item->isLocked() || item->IsExchanging())
			continue;
		items.push_back(item);
	}
	if (items.empty())
		return;

	for (LPITEM item : items)
		item->RemoveFromCharacter();

	std::stable_sort(items.begin(), items.end(), [](LPITEM a, LPITEM b)
	{
		if (a->GetType() != b->GetType())
			return a->GetType() < b->GetType();
		if (a->GetSubType() != b->GetSubType())
			return a->GetSubType() < b->GetSubType();
		return a->GetVnum() < b->GetVnum();
	});

	for (LPITEM item : items)
	{
		const int cell = ch->GetEmptySpecialInventory(bWindow, item->GetSize());
		if (cell >= 0)
		{
			item->AddToCharacter(ch, TItemPos(bWindow, cell));
			continue;
		}
		// a locked item left where it was can take a cell the order needed - the bag or the ground then
		const int bag = ch->GetEmptyInventory(item->GetSize());
		if (bag >= 0)
			item->AddToCharacter(ch, TItemPos(INVENTORY, bag));
		else
			ch->AutoGiveItem(item, true);
	}
}

static bool EkwParseInt(const char* arg, int& out)
{
	if (!arg || !*arg)
		return false;
	char* end = NULL;
	const long v = strtol(arg, &end, 10);
	if (!end || *end)
		return false;
	out = (int) v;
	return true;
}

static bool EkwParseWindow(const char* arg, BYTE& bWindow)
{
	int w = 0;
	if (!EkwParseInt(arg, w))
		return false;
	if (w < UPGRADE_INVENTORY || w > CHEST_INVENTORY)
		return false;
	bWindow = (BYTE) w;
	return true;
}

ACMD(do_ekwipunek)
{
	char arg1[256], arg2[256], arg3[256], arg4[256];
	const char* rest = two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	two_arguments(rest, arg3, sizeof(arg3), arg4, sizeof(arg4));

	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;

	const std::string sub = arg1;

	if (sub == "hello")
	{
		ch->SetSpecialStorageClient(true);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ekwipunek_ok %d", (int) SPECIAL_INVENTORY_PAGE_COUNT);
		return;
	}

	if (sub == "sortuj")
	{
		BYTE bWindow = 0;
		if (!EkwParseWindow(arg2, bWindow))
			return;
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->IsOpenSafebox() || ch->IsCubeOpen() || !ch->CanHandleItem())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby posortowac dodatkowy ekwipunek.");
			return;
		}
		if (!PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), MT2009_PLUS_PULSE_EKW_SORT, std::chrono::milliseconds(3000)))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Sortowac mozna raz na 3 sekundy.");
			return;
		}
		EkwSort(ch, bWindow);
		return;
	}

	if (sub == "sprzedaj")
	{
		BYTE bWindow = 0;
		int cell = -1, count = 0;
		if (!EkwParseWindow(arg2, bWindow) || !EkwParseInt(arg3, cell) || cell < 0 || cell >= SPECIAL_INVENTORY_MAX_NUM)
			return;
		if (*arg4 && !EkwParseInt(arg4, count))
			return;
		if (count < 0)
			count = 0;
		g_bMt2009EkwSellWindow = bWindow;
		CShopManager::instance().Sell(ch, (WORD) cell, (ITEM_COUNT) count);
		g_bMt2009EkwSellWindow = INVENTORY;
		return;
	}

	if (sub == "kostka")
	{
		int cubeIndex = -1, cell = -1;
		BYTE bWindow = 0;
		if (!EkwParseInt(arg2, cubeIndex) || !EkwParseWindow(arg3, bWindow) || !EkwParseInt(arg4, cell))
			return;
		if (cell < 0 || cell >= SPECIAL_INVENTORY_MAX_NUM)
			return;
		g_bMt2009EkwCubeWindow = bWindow;
		Cube_add_item(ch, cubeIndex, cell);
		g_bMt2009EkwCubeWindow = INVENTORY;
		return;
	}
}
