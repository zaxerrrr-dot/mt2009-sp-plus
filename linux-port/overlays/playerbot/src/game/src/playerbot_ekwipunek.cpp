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
//                      27992-27994, the aura runes; the refine scrolls (ITEM_USE / USE_TUNING) went here from
//                      MT2009_PLUS_EKWIPUNEK_REFINE_V1 until MT2009_PLUS_EKWIPUNEK_CATS_V2 (3 November 2026: in the bag);
//   BOOK_INVENTORY     ITEM_SKILLBOOK and Ameria's extra books 50301-50303, every read book, the herbalism recipes;
//   STONE_INVENTORY    ITEM_METIN / METIN_NORMAL (the soul stones);
//   CHANGE_INVENTORY   ITEM_USE / USE_CHANGE_ATTRIBUTE (Zaczarowanie przedmiotu) and Ameria's 72346; since
//                      MT2009_PLUS_EKWIPUNEK_CATS_V2 also the Pozwolenia, Marmur Blogoslawienstwa, Blogoslawienstwo
//                      Przedmiotu, the 6/7 shards and supplements, Wzmocnienie Przedmiotu, Zielona Sila and the costume
//                      enchant / transform (Mt2009EkwCategoryOf);
//   CHEST_INVENTORY    ITEM_GIFTBOX (the chests).
// Ameria's sixth window, COSTUME_INVENTORY, is left out: its CItem::IsCostume() returns false before anything else
// ("when create false for to inv"), so Ameria never fills it.
//
// What a real player picks up, is given (quests, chests, AutoGiveItem), buys in an NPC shop, takes in a trade or from
// an offline shop goes straight into its category's storage (GetEmptyInventoryRouted) and joins the stacks there
// first (Mt2009EkwAutoStack*). Unlike Ameria, a full storage is no refusal: the item goes into the bag as before.
// Only a client that said so routes ("/ekwipunek hello", root/uiekwipunek.py with the 3.0 exe that knows the windows)
// - an old exe would not show these windows, so its player's items stay in the bag. Bots never routed: their AI scanned
// INVENTORY only (selling, storing, crafting), so a bot's items stayed where it looked for them.
// MT2009_PLUS_BOT_EKW_ROUTE_V1 (the owner, 31 October 2026 - boty-decyzje-2026-10-31.md, point 1: "podnoszone
// materialy/ksiegi/kamienie/zaczarowania/skrzynie trafiaja do okien jak u gracza"): a bot routes too, by its own rule
// (PlayerBotEkwRouteWindow, playerbot_ekwipunek_bots.h): its goods of a category straight into the storage, its working
// stock (the refine scrolls, the change stones, its own books, the soul stones it seats, its alchemy's Cors) into the
// bag while the bag holds no full stack of the kind - the passes that use those take them from a bag cell. Never a
// companion serving its owner; "m2_ekw_bots_off" / "m2_ekw_bots_route_off" (event flags) stop it.
//
// Back out: a drag into the bag (MoveItem), a use from the storage (UseItem takes any window), the refine materials and
// quest items counted and taken from the storages too (CountSpecifyItem / RemoveSpecifyItem), the NPC shop's sale
// ("/ekwipunek sprzedaj"), the safebox both ways, a trade, the crafting window ("/ekwipunek kostka"). Items already in
// a bag stay there - Ameria has no button that moves them (a drag does).
// MT2009_PLUS_EKWIPUNEK_HANDEL_V1 (the owner, 3 November 2026: "Z dodatkowego EQ mozna dawac przedmioty bezposrednio
// na handel i na tobol (sklep offline)"): the trade (CExchange - GetItem by the window, SetExchanging, Done routes) and
// the offline shop (CHARACTER::OpenMyShop -> OpenOfflineShop, the Ikarus shop's add-item: GetItem by the window,
// CheckItem, the line moved out of the storage at once) take a storage's item straight from its cell; the client offers
// it now (root/uiekwipunek.py QuickAdd / InUse, uiexchange.py, offlineshopbuilder.py, offlineshopmanage.py,
// offlineshopui.py). A stack in the trade is not joined by pickups (Mt2009EkwAutoStack*), an old-style stall's sale
// leaves the bag's quickslot alone and the price hint (/flea_price) reads the storages (server-patches/ekwipunek
// "HANDEL" edits).
//
// Commands (root/uiekwipunek.py):
//   /ekwipunek hello                              this client knows the windows - route from now on (and the stored
//                                                 items whose category moved go to their storage, Mt2009EkwRecategorize)
//   /ekwipunek sortuj <window>|wszystko           Ameria's two buttons in one: stacks joined, then sorted by kind (every
//                                                 storage at once with "wszystko", MT2009_PLUS_EKWIPUNEK_CATS_V2)
//   /ekwipunek doekw <cell>                       Ctrl + right click on a bag item with the window open: into its
//                                                 storage (MT2009_PLUS_EKWIPUNEK_CATS_V2)
//   /ekwipunek sprzedaj <window> <cell> <count>   the NPC shop's sale from a storage (CShopManager::Sell)
//   /ekwipunek kostka <cube index> <window> <cell> an item of a storage into the crafting window (Cube_add_item)
//   /ekwipunek stos <window>                      Ameria's "stack" button: the stacks joined (MT2009_PLUS_EKWIPUNEK_LOOK_V1)
//   /ekwipunek dotorby <window> <cell>            a right click: the stack into the bag (MT2009_PLUS_EKWIPUNEK_TOBAG_V1)
//   /ekwipunek przenies [keep=<hex>]              the bag's items of a category into their storages (the inventory's
//                                                 sort menu, "Przenies do extra EQ"; MT2009_PLUS_EKWIPUNEK_MOVE_V1)
//
// Refining (MT2009_PLUS_EKWIPUNEK_REFINE_V1, server-patches/ekwipunek "REFINE" edits): a scroll in the materials'
// storage used on an item, an item of a storage given to the blacksmith (a soul stone's next grade) or a scroll used
// on it - the refine window keeps the item's and the scroll's windows (RefineInformation, CInputMain::Refine), the
// result goes back into the item's cell (Mt2009EkwRefinePlace), the materials come from the bag and the storages
// (CountSpecifyItem / RemoveSpecifyItem).
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

	// MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner's list of 3 November 2026, section B): the categories as the owner sorts
	// them. Kept with root/uiekwipunek.py (CategoryOf, CHANGE_VNUMS, UPGRADE_VNUMS, BAG_VNUMS) in step.
	//  - Zaczarowanie (CHANGE_INVENTORY): besides the change stones (USE_CHANGE_ATTRIBUTE) the Pozwolenia 30368-30370,
	//    Marmur Blogoslawienstwa (USE_ADD_ATTRIBUTE2), Blogoslawienstwo Przedmiotu 71052, the 6/7 bonus shards
	//    39070-39081 (every colour, the shining ones and Swiety), the Seon-Hae supplements 72064-72067, Wzmocnienie
	//    Przedmiotu and Zielona Sila (USE_ADD_ATTRIBUTE), Zaczaruj / Transformuj kostium (USE_CHANGE_COSTUME_ATTR /
	//    USE_RESET_COSTUME_ATTR). The Pozwolenia, shards and supplements are ITEM_MATERIAL - they went with the refine
	//    materials before; Mt2009EkwRecategorize moves those already stored there.
	//  - Ulepszacze (UPGRADE_INVENTORY): the aura runes 49990-49995 by name (they are ITEM_MATERIAL as well); the refine
	//    scrolls (USE_TUNING: Zwoj Blogoslawienstwa, Zwoj Boga Smokow, Magiczny Kamien...) and Kamien Runiczny 31225
	//    stay in the bag - "zostaja w glownym EQ"; those stored before stay where they are and are dragged out.
	//  - Ksiegi (BOOK_INVENTORY): the herbalism recipes (USE_CRAFT_RECIPE 50909-50947) and Losowa Receptura 50910.
	if ((dwVnum >= 30368 && dwVnum <= 30370)	// Pozwolenie na Wzmocnienie (x2) / na Zaczarowanie Przedmiotu
		|| dwVnum == 71052	// Blogoslawienstwo Przedmiotu
		|| (dwVnum >= 39070 && dwVnum <= 39081)	// the 6/7 bonus shards (Szary .. Teczowy, Lsniace, Swiety)
		|| (dwVnum >= 72064 && dwVnum <= 72067))	// Maly / Sredni / Duzy / Silny Suplement
		return CHANGE_INVENTORY;
	if (bType == ITEM_USE && (bSubType == USE_ADD_ATTRIBUTE || bSubType == USE_ADD_ATTRIBUTE2
			|| bSubType == USE_CHANGE_COSTUME_ATTR || bSubType == USE_RESET_COSTUME_ATTR))
		return CHANGE_INVENTORY;
	if (dwVnum >= 49990 && dwVnum <= 49995)	// Lodowa / Ognista Runa Aury
		return UPGRADE_INVENTORY;
	if (dwVnum == 31225)	// Kamien Runiczny
		return 0;
	if ((bType == ITEM_USE && bSubType == USE_CRAFT_RECIPE) || dwVnum == 50910)
		return BOOK_INVENTORY;

	// MT2009_PLUS_EKWIPUNEK_BOOKS_V1: every book that is read goes with the books (the owner, 21 October 2026: "Ksiegi
	// Precyzji nie wchodza do dodatkowego ekwipunku" - Ameria's rule, ITEM_SKILLBOOK and 50301-50303, missed the books
	// our client and Yohara have of other types). Kept with root/uiekwipunek.py (CategoryOf, BOOK_VNUMS) in step.
	// Left where they were: the refine and quest materials named "Ksiega" (ITEM_MATERIAL - Ksiega Klatw, Ksiega Uriela,
	// Ksiega Mlodego Zwierza...: counted for refines from the materials' storage), the refine scroll Podrecznik Kowala
	// (USE_TUNING), Ksiega Obrobki Kamienia (used on an item), the worn Ksiazka Lidera (ITEM_UNIQUE), the chests of
	// books (ITEM_GIFTBOX) and Mikstura Talentu (a potion).
	if (bType == ITEM_SKILLFORGET)		// Ksiega Zapomnienia 70037
		return BOOK_INVENTORY;
	if ((dwVnum >= 50304 && dwVnum <= 50306)	// Sztuka Combo x3
		|| (dwVnum >= 50307 && dwVnum <= 50310) || (dwVnum >= 50317 && dwVnum <= 50321) || dwVnum == 50336
		|| (dwVnum >= 71088 && dwVnum <= 71090)	// Ksiega Misji
		|| (dwVnum >= 50311 && dwVnum <= 50313)	// Jezyk Shinsoo / Chunjo / Jinno
		|| (dwVnum >= 50314 && dwVnum <= 50316) || dwVnum == 71092	// Ksiega Polimorfii
		|| dwVnum == 50325	// Ksiega Precyzji
		|| (dwVnum >= 50338 && dwVnum <= 50343)	// Charyzma / Inspiracja
		|| dwVnum == 50514 || dwVnum == 50515	// Podrecznik: Dopalacz / Riposta
		|| dwVnum == 50052 || dwVnum == 50053 || dwVnum == 50060	// the horse books (Ksiega Opanc. / Wojskowego Konia, Instr. Jazdy Konnej)
		|| (dwVnum >= 55050 && dwVnum <= 55067)	// Jazda ... (the horse skills' books)
		|| (dwVnum >= 55010 && dwVnum <= 55031))	// the pet's skill books (Sztuka ...)
		return BOOK_INVENTORY;

	if (bType == ITEM_MATERIAL && bSubType == MATERIAL_LEATHER)
		return UPGRADE_INVENTORY;
	// MT2009_PLUS_EKWIPUNEK_REFINE_V1 (category) put the refine scrolls (ITEM_USE / USE_TUNING) with the materials; since
	// MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner, 3 November 2026: "Zwoj Blogoslawienstwa, Zwoj Boga Smokow, Kamien Runiczny
	// i inne ulepszajace zostaja w glownym EQ") they stay in the bag. A scroll already in the storage still refines from
	// there (the REFINE edits) and is dragged or right-clicked out into the bag.
	if (bType == ITEM_SKILLBOOK)
		return BOOK_INVENTORY;
	if (bType == ITEM_METIN && bSubType == METIN_NORMAL)
		return STONE_INVENTORY;
	if (bType == ITEM_USE && bSubType == USE_CHANGE_ATTRIBUTE)
		return CHANGE_INVENTORY;
	// MT2009_PLUS_EKWIPUNEK_STARTER_V1 (the owner, 27 October 2026): the level chests of a new character (Skrzynia
	// Ucznia I-III, Eksperta I-III, Mistrza I-III, Arcymistrza: 50187-50196, 50212, 50213 - special_item_group.starter.txt)
	// stay in the bag, where the player sees the next one come and opens it at its level. Kept with
	// root/uiekwipunek.py (STARTER_CHESTS) in step.
	if ((dwVnum >= 50187 && dwVnum <= 50196) || dwVnum == 50212 || dwVnum == 50213)
		return 0;
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

// MT2009_PLUS_BOT_EKW_ROUTE_V1: the bots' own rule (playerbot_ekwipunek_bots.h, the playerbot unit): the item's storage
// window or 0 (the bag); with no item, the proto's (AutoStackItemProto - which stacks a vnum given by count joins).
BYTE PlayerBotEkwRouteWindow(LPCHARACTER ch, LPITEM item, const TItemTable* proto, DWORD dwVnum);

BYTE CHARACTER::GetSpecialWindowFor(LPITEM item) const
{
	if (Mt2009EkwRoutes())
		return Mt2009EkwCategoryOfItem(item);
	if (item && GetDesc() && GetDesc()->IsBot())	// MT2009_PLUS_BOT_EKW_ROUTE_V1
		return PlayerBotEkwRouteWindow(const_cast<CHARACTER*>(this), item, NULL, 0);
	return 0;
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

// MT2009_PLUS_EKWIPUNEK_REFINE_V1: the refine window's window of an item - its category storage, else the bag (also an
// item of the bag's horse pages or a stray window: the refine code read those by a bag cell before as well).
BYTE CHARACTER::Mt2009EkwWindowOf(LPITEM item) const
{
	if (item && Mt2009IsSpecialWindow(item->GetWindow()))
		return item->GetWindow();
	return INVENTORY;
}

// MT2009_PLUS_EKWIPUNEK_REFINE_V1: the free cell the rest of a refined stack goes to (DigiStackRefineAllowed / Split):
// a storage's stack keeps it in its storage while there is room, else - and for the bag's stack always - the bag.
int CHARACTER::Mt2009EkwRefineRestCell(LPITEM item, BYTE* pbWindow)
{
	if (pbWindow)
		*pbWindow = INVENTORY;
	if (!item)
		return -1;

	if (Mt2009IsSpecialWindow(item->GetWindow()))
	{
		const int cell = GetEmptySpecialInventory(item->GetWindow(), item->GetSize());
		if (cell >= 0)
		{
			if (pbWindow)
				*pbWindow = item->GetWindow();
			return cell;
		}
	}
	return GetEmptyInventory(item->GetSize());
}

// MT2009_PLUS_EKWIPUNEK_REFINE_V1: a refine's result (DoRefine, DoRefineWithScroll) into the cell of the item it was
// made from - in the bag as before; in a storage when it is still of that storage's category and fits there, else
// wherever a new item of its kind goes (its storage, the bag; the ground with this player's ownership when all are
// full - AutoGiveItem keeps the item, the caller goes on using it).
void CHARACTER::Mt2009EkwRefinePlace(LPITEM pkNewItem, BYTE bWindow, WORD wCell)
{
	if (!pkNewItem)
		return;

	if (!Mt2009IsSpecialWindow(bWindow))
	{
		pkNewItem->AddToCharacter(this, TItemPos(INVENTORY, wCell));
		return;
	}

	if (Mt2009EkwCategoryOfItem(pkNewItem) == bWindow && Mt2009SpecialIsEmptyGrid(bWindow, wCell, pkNewItem->GetSize(), -1))
	{
		pkNewItem->AddToCharacter(this, TItemPos(bWindow, wCell));
		return;
	}

	AutoGiveItem(pkNewItem, true);
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
			// MT2009_PLUS_EKWIPUNEK_HANDEL_V1: a stack in the trade keeps the count both sides were shown (a pickup
			// joined it, and the trade handed over more than was offered)
			if (item2->GetCount() >= item2->GetMaxStack() || item2->IsExchanging())
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
	if (!p)
		return NULL;
	BYTE bWindow = 0;
	if (Mt2009EkwRoutes())
		bWindow = Mt2009EkwCategoryOf(p->bType, p->bSubType, dwItemVnum);
	else if (GetDesc() && GetDesc()->IsBot())	// MT2009_PLUS_BOT_EKW_ROUTE_V1: a bot's rule for the proto
		bWindow = PlayerBotEkwRouteWindow(this, NULL, p, dwItemVnum);
	if (!bWindow || p->bType == ITEM_DS || p->bType == ITEM_SPECIAL_DS)
		return NULL;

	if (((p->dwFlags & ITEM_FLAG_STACKABLE) && !IS_SET(p->dwAntiFlags, ITEM_ANTIFLAG_STACK)) || EkwCorStack(dwItemVnum))
	{
		for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = Mt2009SpecialGetItem(bWindow, i);
			if (!item || item->GetVnum() != dwItemVnum || !EkwProtoSockets(item))
				continue;
			if (item->IsExchanging())	// MT2009_PLUS_EKWIPUNEK_HANDEL_V1: a stack in the trade keeps its count
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
// MT2009_PLUS_EKWIPUNEK_LOOK_V1: the stacks alone - Ameria's "stack" button ("/ekwipunek stos"); "sortuj" does this first.
static void EkwJoinStacks(LPCHARACTER ch, BYTE bWindow)
{
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
}

static void EkwSort(LPCHARACTER ch, BYTE bWindow)
{
	// join the stacks
	EkwJoinStacks(ch, bWindow);

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

// MT2009_PLUS_EKWIPUNEK_MOVE_V1: "Przenies do extra EQ" - the third choice of the inventory's sort button
// (root/inventoryarrange.py; the owner, 21 October 2026: "tak, jako trzecia opcja w sortowaniu EQ"). Every item of the
// bag that belongs to a category goes into its storage: first into the storage's stacks of the same item, then into a
// free cell. Left in the bag: worn items, locked ones, those in a trade or on sale in the player's shop, the cells
// locked against sorting (Alt + click, inventorysortlock.py - "keep=<hex>", four cells a digit) and whatever its full
// storage has no room for.
static bool EkwKeptCell(const std::string& mask, int cell)
{
	const size_t digit = cell / 4;
	if (digit >= mask.size())
		return false;
	const char c = mask[digit];
	int v = 0;
	if (c >= '0' && c <= '9')
		v = c - '0';
	else if (c >= 'a' && c <= 'f')
		v = c - 'a' + 10;
	else if (c >= 'A' && c <= 'F')
		v = c - 'A' + 10;
	return (v >> (cell % 4)) & 1;
}

static const char* EkwStorageName(BYTE bWindow)
{
	switch (bWindow)
	{
		case UPGRADE_INVENTORY:	return "Materia\263y ulepsze\361";
		case BOOK_INVENTORY:	return "Ksi\352gi";
		case STONE_INVENTORY:	return "Kamienie Duszy";
		case CHANGE_INVENTORY:	return "Zaczarowania";
		case CHEST_INVENTORY:	return "Skrzynie";
	}
	return "?";
}

static void EkwMoveBagToStorages(LPCHARACTER ch, const std::string& keep)
{
	int moved = 0, joined = 0, left = 0;
	bool full[SPECIAL_INVENTORY_WINDOW_COUNT] = {};
	LPSHOP pkMyShop = ch->GetMyShop();

	for (int i = 0; i < ch->GetInventoryMaxCount() && i < INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetInventoryItem(i);
		if (!item || item->GetCell() != i)
			continue;
		if (item->IsEquipped() || item->isLocked() || item->IsExchanging())
			continue;
		if (pkMyShop && pkMyShop->IsSellingItem(item->GetID()))
			continue;
		if (!keep.empty() && EkwKeptCell(keep, i))
			continue;

		const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
		if (!bWindow)
			continue;

		// the storage's stacks of the same item first
		if (EkwStacks(item))
		{
			for (WORD j = 0; j < SPECIAL_INVENTORY_MAX_NUM && item->GetCount() > 0; ++j)
			{
				LPITEM item2 = ch->Mt2009SpecialGetItem(bWindow, j);
				if (!item2 || item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
					continue;
				if (item2->isLocked() || item2->IsExchanging() || item2->GetCount() >= item2->GetMaxStack())
					continue;

				const ITEM_COUNT add = MIN(item2->GetMaxStack() - item2->GetCount(), item->GetCount());
				item2->SetCount(item2->GetCount() + add);
				if (add >= item->GetCount())
				{
					++joined;
					item->SetCount(0);	// gone - SetCount clears its quickslot and destroys it
					item = NULL;
					break;
				}
				item->SetCount(item->GetCount() - add);
			}
			if (!item)
				continue;
		}

		const int cell = ch->GetEmptySpecialInventory(bWindow, item->GetSize());
		if (cell < 0)
		{
			full[bWindow - UPGRADE_INVENTORY] = true;
			++left;
			continue;
		}

		ch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, i, 255);
		item->RemoveFromCharacter();
		item->AddToCharacter(ch, TItemPos(bWindow, cell));
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		++moved;
	}

	if (!moved && !joined && !left)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "W ekwipunku nie ma przedmiot\363w do dodatkowego ekwipunku.");
		return;
	}

	if (moved || joined)
		ch->ChatPacket(CHAT_TYPE_INFO, "Przeniesiono do dodatkowego ekwipunku: %d (do\263\271czono do stos\363w: %d).", moved + joined, joined);

	if (left)
	{
		std::string names;
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
		{
			if (!full[w - UPGRADE_INVENTORY])
				continue;
			if (!names.empty())
				names += ", ";
			names += EkwStorageName(w);
		}
		ch->ChatPacket(CHAT_TYPE_INFO, "Zosta\263o w ekwipunku: %d - brak miejsca w kategorii: %s.", left, names.c_str());
	}
}

// MT2009_PLUS_EKWIPUNEK_CATS_V2: the storages' items whose category moved (the owner, 3 November 2026: the Pozwolenia,
// shards and supplements "lezace w Ulepszaczach przeniesc" to Zaczarowanie) go to their new storage - into its stacks of
// the same item first, then a free cell; what has no room there stays. An item of no category any more (a refine
// scroll) stays where it is - the owner: "te, ktore juz sa w Ulepszaczach - mozna przeciagnac do plecaka". Run at every
// "/ekwipunek hello" (login and every warp; a few hundred cells, nothing to do once sorted), so a later category change
// sorts itself too. Returns the items moved.
int Mt2009EkwRecategorize(LPCHARACTER ch)
{
	if (!ch)
		return 0;
	LPSHOP pkMyShop = ch->GetMyShop();
	int moved = 0;
	for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
	{
		for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = ch->Mt2009SpecialGetItem(w, i);
			if (!item || item->GetCell() != i || item->isLocked() || item->IsExchanging())
				continue;
			if (pkMyShop && pkMyShop->IsSellingItem(item->GetID()))
				continue;
			const BYTE bTarget = Mt2009EkwCategoryOfItem(item);
			if (!bTarget || bTarget == w)
				continue;

			if (EkwStacks(item))
			{
				for (WORD j = 0; j < SPECIAL_INVENTORY_MAX_NUM && item; ++j)
				{
					LPITEM item2 = ch->Mt2009SpecialGetItem(bTarget, j);
					if (!item2 || item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
						continue;
					if (item2->isLocked() || item2->IsExchanging() || item2->GetCount() >= item2->GetMaxStack())
						continue;
					const ITEM_COUNT add = MIN(item2->GetMaxStack() - item2->GetCount(), item->GetCount());
					item2->SetCount(item2->GetCount() + add);
					if (add >= item->GetCount())
					{
						item->SetCount(0);	// all of it joined - SetCount destroys it
						item = NULL;
						++moved;
						break;
					}
					item->SetCount(item->GetCount() - add);
				}
				if (!item)
					continue;
			}

			const int cell = ch->GetEmptySpecialInventory(bTarget, item->GetSize());
			if (cell < 0)
				continue;
			item->RemoveFromCharacter();
			item->AddToCharacter(ch, TItemPos(bTarget, cell));
			ITEM_MANAGER::instance().FlushDelayedSave(item);
			++moved;
		}
	}
	if (moved)
		sys_log(0, "EKWIPUNEK: recategorized pid=%u name=%s moved=%d", ch->GetPlayerID(), ch->GetName(), moved);
	return moved;
}

// MT2009_PLUS_EKWIPUNEK_CATS_V2: Ctrl + right click on an item of the bag while the extra inventory's window is open
// (root/uiinventory.py; the owner, 3 November 2026: "Ctrl+PPM w plecaku przy otwartym oknie dodatkowego EQ przenosi do
// kategorii (skrzynie tez - przenoszone, nie otwierane)") - "Przenies do extra EQ" for that one cell: into its storage's
// stacks first, then a free cell; a full storage says so.
static void EkwMoveCellToStorage(LPCHARACTER ch, int iCell)
{
	if (iCell < 0 || iCell >= ch->GetInventoryMaxCount() || iCell >= INVENTORY_MAX_NUM)
		return;
	LPITEM item = ch->GetInventoryItem(iCell);
	if (!item || item->GetCell() != iCell || item->IsEquipped() || item->isLocked() || item->IsExchanging())
		return;
	LPSHOP pkMyShop = ch->GetMyShop();
	if (pkMyShop && pkMyShop->IsSellingItem(item->GetID()))
		return;
	const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
	if (!bWindow)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot nie nale\277y do \277adnej kategorii dodatkowego ekwipunku.");
		return;
	}

	if (EkwStacks(item))
	{
		for (WORD j = 0; j < SPECIAL_INVENTORY_MAX_NUM; ++j)
		{
			LPITEM item2 = ch->Mt2009SpecialGetItem(bWindow, j);
			if (!item2 || item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
				continue;
			if (item2->isLocked() || item2->IsExchanging() || item2->GetCount() >= item2->GetMaxStack())
				continue;
			const ITEM_COUNT add = MIN(item2->GetMaxStack() - item2->GetCount(), item->GetCount());
			item2->SetCount(item2->GetCount() + add);
			if (add >= item->GetCount())
			{
				item->SetCount(0);	// gone - SetCount clears its quickslot and destroys it
				return;
			}
			item->SetCount(item->GetCount() - add);
		}
	}

	const int cell = ch->GetEmptySpecialInventory(bWindow, item->GetSize());
	if (cell < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Brak miejsca w kategorii: %s.", EkwStorageName(bWindow));
		return;
	}
	ch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, iCell, 255);
	item->RemoveFromCharacter();
	item->AddToCharacter(ch, TItemPos(bWindow, cell));
	ITEM_MANAGER::instance().FlushDelayedSave(item);
}

// MT2009_PLUS_EKWIPUNEK_TOBAG_V1: a right click on an item of the extra inventory (root/uiekwipunek.py; the owner,
// 21 October 2026: "prawy klik w dodatkowym ekwipunku ma przenosic przedmiot do glownego ekwipunku") - the whole stack
// into the bag: first into the bag's stacks of the same item (same sockets), then the rest into the bag's first free
// cell. What has no room stays where it was ("Brak miejsca w ekwipunku").
static void EkwMoveToBag(LPCHARACTER ch, BYTE bWindow, WORD wCell)
{
	LPITEM item = ch->Mt2009SpecialGetItem(bWindow, wCell);
	if (!item || item->GetCell() != wCell)
		return;
	if (item->isLocked() || item->IsExchanging())
		return;
	LPSHOP pkMyShop = ch->GetMyShop();
	if (pkMyShop && pkMyShop->IsSellingItem(item->GetID()))
		return;

	if (EkwStacks(item))
	{
		for (int i = 0; i < ch->GetInventoryMaxCount() && i < INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item2 = ch->GetInventoryItem(i);
			if (!item2 || item2 == item || item2->GetCell() != i)
				continue;
			if (item2->GetVnum() != item->GetVnum() || !EkwSameSockets(item, item2))
				continue;
			if (item2->isLocked() || item2->IsExchanging() || item2->GetCount() >= item2->GetMaxStack())
				continue;
			if (pkMyShop && pkMyShop->IsSellingItem(item2->GetID()))
				continue;

			const ITEM_COUNT add = MIN(item2->GetMaxStack() - item2->GetCount(), item->GetCount());
			item2->SetCount(item2->GetCount() + add);
			if (add >= item->GetCount())
			{
				item->SetCount(0);	// all of it joined - SetCount destroys it
				return;
			}
			item->SetCount(item->GetCount() - add);
		}
	}

	const int cell = ch->GetEmptyInventory(item->GetSize());
	if (cell < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Brak miejsca w ekwipunku.");
		return;
	}

	item->RemoveFromCharacter();
	item->AddToCharacter(ch, TItemPos(INVENTORY, cell));
	ITEM_MANAGER::instance().FlushDelayedSave(item);
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
		if (ch->IsItemLoaded() && ch->CanHandleItem() && !ch->GetExchange() && !ch->GetShop() && !ch->IsCubeOpen())
			Mt2009EkwRecategorize(ch);	// MT2009_PLUS_EKWIPUNEK_CATS_V2: the items whose category moved
		return;
	}

	// MT2009_PLUS_EKWIPUNEK_CATS_V2: "/ekwipunek doekw <cell>" - Ctrl + right click on a bag item with the window open
	if (sub == "doekw")
	{
		int cell = -1;
		if (!ch->Mt2009EkwRoutes() || !EkwParseInt(arg2, cell))
			return;
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->IsCubeOpen() || !ch->CanHandleItem())
			return;
		EkwMoveCellToStorage(ch, cell);
		return;
	}

	if (sub == "sortuj")
	{
		// MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner, 3 November 2026: "Sortuj sortuje wszystkie kategorie naraz"):
		// "/ekwipunek sortuj wszystko" - every storage in one go (one 3 s clock for all of them)
		const bool bAll = !strcmp(arg2, "wszystko");
		BYTE bWindow = 0;
		if (!bAll && !EkwParseWindow(arg2, bWindow))
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
		if (bAll)
		{
			for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
				EkwSort(ch, w);
		}
		else
			EkwSort(ch, bWindow);
		return;
	}

	// MT2009_PLUS_EKWIPUNEK_LOOK_V1: Ameria's "stack" button - the stacks joined, the order kept.
	if (sub == "stos")
	{
		BYTE bWindow = 0;
		if (!EkwParseWindow(arg2, bWindow))
			return;
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->IsOpenSafebox() || ch->IsCubeOpen() || !ch->CanHandleItem())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby po\263\271czy\346 stosy w dodatkowym ekwipunku.");
			return;
		}
		if (!PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), MT2009_PLUS_PULSE_EKW_SORT, std::chrono::milliseconds(3000)))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "\243\271czy\346 stosy mo\277na raz na 3 sekundy.");
			return;
		}
		EkwJoinStacks(ch, bWindow);
		return;
	}

	// MT2009_PLUS_EKWIPUNEK_TOBAG_V1: a right click in the extra inventory - the stack into the bag.
	if (sub == "dotorby")
	{
		BYTE bWindow = 0;
		int cell = -1;
		if (!EkwParseWindow(arg2, bWindow) || !EkwParseInt(arg3, cell) || cell < 0 || cell >= SPECIAL_INVENTORY_MAX_NUM)
			return;
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->IsCubeOpen() || !ch->CanHandleItem())
			return;
		EkwMoveToBag(ch, bWindow, (WORD) cell);
		return;
	}

	// MT2009_PLUS_EKWIPUNEK_MOVE_V1: "Przenies do extra EQ" (root/inventoryarrange.py)
	if (sub == "przenies")
	{
		if (!ch->Mt2009EkwRoutes())
			return;
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->IsOpenSafebox() || ch->IsCubeOpen() || !ch->CanHandleItem())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby przenie\234\346 przedmioty do dodatkowego ekwipunku.");
			return;
		}
		if (!PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), MT2009_PLUS_PULSE_EKW_SORT, std::chrono::milliseconds(3000)))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Przenosi\346 mo\277na raz na 3 sekundy.");
			return;
		}
		std::string keep;
		if (!strncmp(arg2, "keep=", 5))
			keep = arg2 + 5;
		EkwMoveBagToStorages(ch, keep);
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
