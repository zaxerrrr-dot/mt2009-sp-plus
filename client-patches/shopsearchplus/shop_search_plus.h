// MT2009 PLUS: Target Drop Info and the private shop search (server-patches/shopsearchplus).
// Both are separate from the older "/mob_drop" preview and the Ikarus item finder,
// which keep working. The packets are described in server-patches/shopsearchplus/README.md
// and must match the client byte for byte.
#pragma once

#include "packet.h"

#pragma pack(push, 1)

enum
{
	TARGET_DROP_ITEM_MAX = 70,
	SHOP_SEARCH_LOOKING_GLASS = 60004,	// marks a found shop on the map
	SHOP_SEARCH_TRADING_GLASS = 60005,	// buys from a found shop from anywhere
};

// HEADER_CG_TARGET_DROP (151): "what can my target drop?"
struct TPacketCGTargetDrop
{
	BYTE	header;
};

// HEADER_GC_TARGET_DROP (160): the answer, the layout of the Target Drop Info mod.
struct TPacketGCTargetDrop
{
	BYTE	header;
	WORD	raceVnum;
	WORD	size;						// items used, at most TARGET_DROP_ITEM_MAX
	DWORD	items[TARGET_DROP_ITEM_MAX];
};

// HEADER_CG_PRIVATE_SHOP_SEARCH (216)
struct TPacketCGPrivateShopSearch
{
	BYTE	header;
	BYTE	bJob;						// JOB_WARRIOR..JOB_SHAMAN, anything else: every class
	BYTE	bMaskType;					// item type, 0 (ITEM_NONE): every type
	int		iMaskSub;					// item subtype, -1: every subtype
	int		iMinRefine;
	int		iMaxRefine;
	int		iMinLevel;
	int		iMaxLevel;
	long long	llMinGold;
	long long	llMaxGold;
	char	szItemName[ITEM_NAME_MAX_LEN + 1];	// part of the name, case-insensitive; empty: any
};

// HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE (217)
struct TPacketCGPrivateShopSearchClose
{
	BYTE	header;
};

// HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM (218)
struct TPacketCGPrivateShopSearchBuyItem
{
	BYTE	header;
	DWORD	dwShopPID;					// the shop owner's player id, from a result
	DWORD	dwItemID;					// the shop item id, from a result
	long long	llSeenPrice;			// the price the client showed; a changed price is refused
};

// One result of HEADER_GC_PRIVATE_SHOP_SEARCH.
struct TPacketGCPrivateShopSearchItem
{
	packet_shop_item	item;			// vnum, price, count, display_pos, sockets, attributes
	char	szSellerName[CHARACTER_NAME_MAX_LEN + 1];
	DWORD	dwShopPID;
	DWORD	dwItemID;
	long	lMapIndex;
	long	lX;
	long	lY;
	BYTE	bChannel;
};

// HEADER_GC_PRIVATE_SHOP_SEARCH (216): header, size, then the results.
struct TPacketGCPrivateShopSearch
{
	BYTE	header;
	WORD	size;						// the whole packet, results included
};

// HEADER_GC_PRIVATE_SHOP_SEARCH_OPEN (217): open the window.
struct TPacketGCPrivateShopSearchOpen
{
	BYTE	header;
	BYTE	bMode;						// 1: Lupa (mark on the map), 2: Lupa Handlarza (buy)
};

// HEADER_GC_PRIVATE_SHOP_SEARCH_MARK (218): mark this shop on the minimap.
struct TPacketGCPrivateShopSearchMark
{
	BYTE	header;
	DWORD	dwShopVID;
	long	lX;
	long	lY;
};

#pragma pack(pop)

// The client depends on these sizes byte for byte (client-patches/shopsearchplus/INSTRUKCJA.md).
static_assert(sizeof(TPacketGCTargetDrop) == 285, "TPacketGCTargetDrop");
static_assert(sizeof(TPacketCGPrivateShopSearch) == 72, "TPacketCGPrivateShopSearch");
static_assert(sizeof(TPacketCGPrivateShopSearchBuyItem) == 17, "TPacketCGPrivateShopSearchBuyItem");
static_assert(sizeof(TPacketGCPrivateShopSearchItem) == 96, "TPacketGCPrivateShopSearchItem");
static_assert(sizeof(TPacketGCPrivateShopSearch) == 3, "TPacketGCPrivateShopSearch");
static_assert(sizeof(TPacketGCPrivateShopSearchOpen) == 2, "TPacketGCPrivateShopSearchOpen");
static_assert(sizeof(TPacketGCPrivateShopSearchMark) == 13, "TPacketGCPrivateShopSearchMark");

namespace shop_search_plus
{
	void RecvTargetDrop(LPCHARACTER ch);
	void RecvSearch(LPCHARACTER ch, const char* data);
	void RecvClose(LPCHARACTER ch);
	void RecvBuy(LPCHARACTER ch, const char* data);
	// true when the item was a search glass (and so was handled).
	bool UseGlass(LPCHARACTER ch, LPITEM item);
}
