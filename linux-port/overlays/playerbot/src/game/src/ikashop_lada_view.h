// MT2009_PLUS_BOT_LADA_VIEW_V1 - a new engine file kept in the overlay, like ikashop_qol.h; server-patches/ladaview
// includes it from ikarus_shop_manager.cpp and ikarus_shop.cpp, and playerbot_lada.h reads its counters for the census.
//
// The owner, 8 November 2026: "Nie limituj pozycji na bota" - a bot's counter (its "lada", playerbot_lada.h) has no
// number of lines any more, so whatever carries every line of a shop to a person's client is bounded here, in the
// game core, and not in the client:
//   * the stand's window (SUBHEADER_GC_SHOP_OPEN, CShopManager::SendShopOpenClientPacket - a guest's open and every
//     refresh of its view) and the owner's own window (SUBHEADER_GC_SHOP_OPEN_OWNER) carry only the lines of the
//     window's pages: pos < VISIBLE_CELLS (four pages of SHOP_PLAYER_WIDTH x SHOP_PLAYER_HEIGHT = 320 cells, the bots'
//     pages - a person's shop has two at most, so its window loses nothing) and at most VISIBLE_LINES of them. A line
//     at 320 and up (the lada's) is found and bought through the searches, which carry it one result at a time;
//   * a line added past the pages refreshes nobody's view (CShop::AddItem): no guest sees it, and every lada add on
//     every core of every channel rebuilt the whole window for every guest of that stand;
//   * the shop safebox (SUBHEADER_GC_SHOP_SAFEBOX_REFRESH) carries at most SAFEBOX_SEND_MAX items (the engine never
//     bounded what the db core puts in it);
//   * none of the three is built for a bot's descriptor (DESC::Packet drops a bot's packets anyway).
// Sizes (g++ -m32, the engine's packed structs, 8 November 2026): TShopItem 75 bytes, TShopPlayerItem 67, the open's
// header 6 + 80, the client's receive buffer max(set, 600 KB) (PythonNetworkStreamModule.cpp netSetTCPRecvBufferSize
// with ENABLE_LARGE_DYNAMIC_PACKETS) - so the window's packet is at most 86 + 320 x 75 = 24 086 bytes, the safebox's at
// most 4000 x 67 + its header = 268 KB; unbounded, 8190 lines of a counter would already have been one packet the
// client could never read whole (the connection then stalls).
// The searches were bounded before: the Dom Towarowy's fill at 6000 results sent 100 a packet
// (MT2009_PLUS_FLEA_MARKET_BOUND_V1, 100 x 113 = 11 300 bytes), the filter search at OFFLINESHOP_MAX_SEARCH_RESULT 2500
// in one packet (2500 x 113 = 282 500 bytes), the stand search at 400 shops.
#pragma once

#include <algorithm>

namespace ikashop_lada_view
{
	constexpr int VISIBLE_CELLS = SHOP_PLAYER_WIDTH * SHOP_PLAYER_HEIGHT * 4;
	constexpr unsigned int VISIBLE_LINES = 320;
	constexpr unsigned int SAFEBOX_SEND_MAX = 4000;

	// What the windows sent (the census of playerbot_lada.h reads and resets these).
	inline unsigned int maxSent = 0;		// the most lines one window packet carried
	inline unsigned int maxHeld = 0;		// the most lines the shop of that packet held
	inline unsigned long long views = 0;	// window packets built
	inline unsigned long long hidden = 0;	// lines left out of them (past the pages)
	inline unsigned long long refreshSkipped = 0;	// adds past the pages that refreshed no view

	inline bool IsShownPos(int pos)
	{
		return pos >= 0 && pos < VISIBLE_CELLS;
	}

	template <typename TItems>
	inline unsigned int CountShown(const TItems& items)
	{
		unsigned int shown = 0;
		for (const auto& [id, item] : items)
			if (item && IsShownPos((int) item->GetInfo().pos) && shown < VISIBLE_LINES)
				++shown;
		return shown;
	}

	inline void NoteView(unsigned int sent, unsigned int held)
	{
		++views;
		hidden += held > sent ? held - sent : 0;
		if (sent > maxSent)
			maxSent = sent;
		if (held > maxHeld)
			maxHeld = held;
	}

	// The lines a window packet carries, in the shop's own order, the first VISIBLE_LINES of the pages.
	template <typename TItems, typename TWrite>
	inline unsigned int WriteShown(const TItems& items, TWrite write)
	{
		unsigned int sent = 0;
		for (const auto& [id, item] : items)
		{
			if (!item || !IsShownPos((int) item->GetInfo().pos))
				continue;
			if (sent >= VISIBLE_LINES)
				break;
			write(item->GetInfo());
			++sent;
		}
		NoteView(sent, (unsigned int) items.size());
		return sent;
	}
}
