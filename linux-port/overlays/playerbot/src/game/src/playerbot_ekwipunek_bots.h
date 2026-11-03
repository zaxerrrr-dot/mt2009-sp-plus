#ifndef PLAYERBOT_EKWIPUNEK_BOTS_H
#define PLAYERBOT_EKWIPUNEK_BOTS_H

// MT2009_PLUS_BOT_EKWIPUNEK_V1: the bots use the extra inventory (Dodatkowy ekwipunek - the five category storages of
// playerbot_ekwipunek.cpp, windows UPGRADE_INVENTORY .. CHEST_INVENTORY, 4 pages x 45 each). The owner, 27 October
// 2026: "Naucz boty korzystac z dodatkowego EQ aby mialy wiecej miejsca na zlom w swoim eq."
//
// MT2009_PLUS_BOT_EKW_ROUTE_V1 (31 October 2026): the engine routes a bot's items now, by the bots' rule - see that
// section below (PlayerBotEkwRouteWindow); what follows is the lending as it was before, still the bots' way with
// "m2_ekw_bots_route_off", and its parts the routing keeps (the working stock's refill, the fetches, the stash).
// The engine still never routes a bot's item (CHARACTER::Mt2009EkwRoutes stays false for a bot): its AI finds, counts,
// uses, sells, lists, deposits and trades by the bag's cells in some hundred places, and an item that dropped straight
// into a storage would be lost to all of them. Instead the bot keeps its bag as it was and lends the storages its
// overflow, on a clock of its own (ManagePlayerBotEkwipunek, every PLAYERBOT_EKW_PASS_MS, never in the middle of an
// errand, a trade, a shop, a safebox or a refine):
//
//   stash    only while the bag is short of room (fewer than PLAYERBOT_EKW_STASH_BELOW free cells):
//            (A) a kind's extra stacks: the bag keeps its biggest stack of every kind (vnum and sockets), topped up from
//                the others, the rest goes to the storage - the bag's own count of a kind stays min(total, a full
//                stack), so no rule that counts the bag (the scroll, book and stone keeps) sees less than before;
//            (B) then, until PLAYERBOT_EKW_STASH_TARGET cells are free, whole stacks of goods - what the bot does not
//                work with itself: materials (every rule that needs them counts and takes them with
//                CountSpecifyItem / RemoveSpecifyItem, which read the storages too), books of skills that are not its
//                own, soul stones it cannot seat, chests that are not its alchemy's Cors.
//            Never stashed whole: its working stock - the refine scrolls (USE_TUNING), the change stones (71084 and
//            the like), its own skills' books and the other read books, the soul stones it can seat or take through
//            the Ritual of Awakening, its alchemy's Cors. Never moved at all: worn, locked, in a trade or on sale
//            in its shop.
//   refill   the working stock comes back as soon as the bag lacks it (a kind used up, a stack run low) and has
//            PLAYERBOT_EKW_WORK_REFILL_MIN_FREE free cells; everything else when the bag is roomy again (more than
//            PLAYERBOT_EKW_REFILL_ABOVE free cells - after the town's sale), so the counter, the merchant and the
//            market get their goods as before, only later.
//   fetch    PlayerBotEkwFetchVnum: one kind back into the bag on the spot (FindPlayerBotBagItem's miss).
//
// The storages are saved like the bag (the item table's windows, ekwipunek.sql; the db core's load and delete take
// them since MT2009_PLUS_EKWIPUNEK_V1). A companion serving its owner never stashes: its bag is its owner's errand.
// "m2_ekw_bots_off" (event flag) stops every pass; the stored items then wait (a later pass with the flag off brings
// them back as the bag allows). Logged: PLAYERBOT_EKW.

// playerbot_ekwipunek.cpp: the item's storage window, 0 for none.
BYTE Mt2009EkwCategoryOfItem(LPITEM item);
BYTE Mt2009EkwCategoryOf(BYTE bType, BYTE bSubType, DWORD dwVnum);	// MT2009_PLUS_BOT_EKW_ROUTE_V1: a proto's

namespace
{
	const int PLAYERBOT_EKW_STASH_BELOW = 10;
	const int PLAYERBOT_EKW_STASH_TARGET = 16;
	const int PLAYERBOT_EKW_REFILL_ABOVE = 22;
	const int PLAYERBOT_EKW_WORK_REFILL_MIN_FREE = 3;
	const DWORD PLAYERBOT_EKW_PASS_MS = 15000;
	const int PLAYERBOT_EKW_MAX_MOVES = 60;

	struct TPlayerBotEkwStats
	{
		int stashSurplus = 0;	// (A) a kind's extra stack into its storage
		int stashGoods = 0;		// (B) a stack of goods into its storage
		int joined = 0;			// units joined to a stack (bag's biggest or the storage's)
		int refillWork = 0;		// working stock back into the bag
		int topUp = 0;			// a bag stack topped up from the storage
		int refillGoods = 0;	// goods back into a roomy bag
		int fetched = 0;		// PlayerBotEkwFetchVnum
		int recategorized = 0;	// MT2009_PLUS_EKWIPUNEK_CATS_V2: a stored item whose category moved
	};

	bool ArePlayerBotEkwOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_ekw_bots_off") != 0;
	}

	bool PlayerBotEkwStacks(LPITEM item)
	{
		if (!item)
			return false;
		if (item->GetMaxStack() <= 1)
			return false;
		return (item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK)) ||
				IsPlayerBotOpenableCorVnum(item->GetVnum());
	}

	// One kind: the vnum and the sockets (a skill book's skill, a stack's own) - what the engine stacks together.
	bool PlayerBotEkwSameKind(LPITEM a, LPITEM b)
	{
		if (!a || !b || a->GetVnum() != b->GetVnum())
			return false;
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			if (a->GetSocket(i) != b->GetSocket(i))
				return false;
		return true;
	}

	// What may move at all: the bot's own, still, not worn, not locked, not in a trade, not on sale.
	bool IsPlayerBotEkwMovable(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetOwner() != ch || item->IsEquipped() || item->isLocked() || item->IsExchanging())
			return false;
		if (ch->GetMyShop() && ch->GetMyShop()->IsSellingItem(item->GetID()))
			return false;
		return true;
	}

	// The bot works with these itself, by the bag's cells: never stashed whole, back as soon as the bag lacks them.
	bool IsPlayerBotEkwWorkingStock(LPCHARACTER ch, LPITEM item, BYTE bWindow)
	{
		if (!ch || !item)
			return true;
		switch (bWindow)
		{
			case UPGRADE_INVENTORY:
				// the refine scrolls and Ameria's extra vnums; the materials are counted and taken from the storages
				return item->GetType() != ITEM_MATERIAL;
			case BOOK_INVENTORY:
				if (item->GetType() == ITEM_SKILLBOOK)
				{
					const DWORD skill = GetPlayerBotSkillBookSkillVnum(item);
					return skill != 0 && IsPlayerBotOwnSkill(ch, skill);
				}
				// MT2009_PLUS_EKWIPUNEK_CATS_V2: the herbalism recipes are goods (no bot learns them)
				if (item->GetType() == ITEM_USE)
					return false;
				return true;	// the general, horse, pet, mission books and the Forgetting Scroll
			case STONE_INVENTORY:
			{
				// one it would seat, or one the Ritual of Awakening takes to the next grade (playerbot_awakening.h)
				int grade = 0, kind = 0;
				return CanPlayerBotSeatSoulStone(ch, item->GetVnum(), (DWORD)item->GetValue(5)) ||
						(mt2009_awakening::IsRefinableStone(item->GetVnum(), grade, kind) &&
						 kind < mt2009_awakening::STONE_KINDS);	// MT2009_PLUS_ANTI_RESIST_MAGIC_V1: no step of Kamien Antymagii
			}
			case CHANGE_INVENTORY:
				// MT2009_PLUS_EKWIPUNEK_CATS_V2: the change and add stones, the marbles, 71052 and the costume stones are
				// used by the bag's cells; the Pozwolenia, 6/7 shards and supplements (ITEM_MATERIAL, with the refine
				// materials before) are counted / fetched where they lie (CountSpecifyItem, FetchPlayerBotShopAidBagItem)
				return item->GetType() != ITEM_MATERIAL;
			case CHEST_INVENTORY:
				return IsPlayerBotKeptCor(ch, item);
		}
		return true;
	}

	// MT2009_PLUS_BOT_EKW_ROUTE_V1: the same rule for a vnum given by count (AutoGiveItem's stacks, before an item exists):
	// a skill book's skill is not known yet - goods here, the item's own rule places what is left of it.
	bool IsPlayerBotEkwWorkingStockProto(LPCHARACTER ch, const TItemTable* proto, DWORD vnum, BYTE bWindow)
	{
		if (!ch || !proto)
			return true;
		switch (bWindow)
		{
			case UPGRADE_INVENTORY:
				return proto->bType != ITEM_MATERIAL;
			case BOOK_INVENTORY:
				return proto->bType != ITEM_SKILLBOOK && proto->bType != ITEM_USE;	// MT2009_PLUS_EKWIPUNEK_CATS_V2: recipes
			case STONE_INVENTORY:
			{
				int grade = 0, kind = 0;
				return CanPlayerBotSeatSoulStone(ch, vnum, (DWORD)proto->alValues[5]) ||
						(mt2009_awakening::IsRefinableStone(vnum, grade, kind) && kind < mt2009_awakening::STONE_KINDS);
			}
			case CHANGE_INVENTORY:
				return proto->bType != ITEM_MATERIAL;	// MT2009_PLUS_EKWIPUNEK_CATS_V2
			case CHEST_INVENTORY:
				return IsPlayerBotOpenableCorVnum(vnum) && IsPlayerBotAlchemyUser(ch);
		}
		return true;
	}

	int PlayerBotEkwFindBagCell(LPCHARACTER ch, BYTE bSize)
	{
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			if (ch->IsEmptyItemGrid(TItemPos(INVENTORY, (WORD)cell), bSize))
				return cell;
		return -1;
	}

	// The bag's stack of this kind with the most units (not the item itself), or NULL.
	LPITEM PlayerBotEkwBagStackOf(LPCHARACTER ch, LPITEM item)
	{
		LPITEM best = NULL;
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM other = ch->GetInventoryItem((WORD)cell);
			if (!other || other == item || other->GetCell() != cell || !PlayerBotEkwSameKind(item, other))
				continue;
			if (!IsPlayerBotEkwMovable(ch, other))
				continue;
			if (!best || other->GetCount() > best->GetCount())
				best = other;
		}
		return best;
	}

	// Units of src onto dst (same kind, stackable) up to a full stack. Returns true when src is gone (destroyed).
	bool PlayerBotEkwJoin(LPITEM dst, LPITEM src, TPlayerBotEkwStats& st)
	{
		if (!dst || !src || dst == src || dst->GetCount() >= dst->GetMaxStack())
			return false;
		const ITEM_COUNT add = (ITEM_COUNT)MIN((DWORD)(dst->GetMaxStack() - dst->GetCount()), (DWORD)src->GetCount());
		if (add == 0)
			return false;
		dst->SetCount(dst->GetCount() + add);
		st.joined += (int)add;
		if (add >= src->GetCount())
		{
			src->SetCount(0);	// all of it joined - SetCount destroys it
			return true;
		}
		src->SetCount(src->GetCount() - add);
		return false;
	}

	// A bag item into its storage: the storage's stacks of its kind first, then a free cell. False: it stayed
	// (no room) - or it is gone into the stacks (bGone).
	bool PlayerBotEkwToStorage(LPCHARACTER ch, LPITEM item, BYTE bWindow, TPlayerBotEkwStats& st, bool& bGone)
	{
		bGone = false;
		const WORD wFromCell = item->GetCell();
		if (PlayerBotEkwStacks(item))
		{
			for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
			{
				LPITEM stack = ch->Mt2009SpecialGetItem(bWindow, i);
				if (!stack || stack->GetCell() != i || !PlayerBotEkwSameKind(item, stack) || !IsPlayerBotEkwMovable(ch, stack))
					continue;
				if (PlayerBotEkwJoin(stack, item, st))
				{
					bGone = true;
					return true;
				}
			}
		}
		const int cell = ch->GetEmptySpecialInventory(bWindow, item->GetSize());
		if (cell < 0)
			return false;
		if (item->GetWindow() == INVENTORY)	// MT2009_PLUS_EKWIPUNEK_CATS_V2: a storage's item (recategorized) has no quickslot
			ch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, wFromCell, 255);
		item->RemoveFromCharacter();
		if (!item->AddToCharacter(ch, TItemPos(bWindow, (WORD)cell)))
		{
			// cannot happen (the cell was asked for); the bag or the ground keeps it
			sys_err("PLAYERBOT_EKW: storage refused pid=%u vnum=%u window=%u cell=%d", ch->GetPlayerID(), item->GetVnum(),
					(unsigned)bWindow, cell);
			ch->AutoGiveItem(item, true);
			return false;
		}
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		return true;
	}

	// A storage item back into the bag: the bag's stack of its kind first, then a free bag cell (the four pages).
	// False: it stayed (no room).
	bool PlayerBotEkwToBag(LPCHARACTER ch, LPITEM item, TPlayerBotEkwStats& st, bool& bGone)
	{
		bGone = false;
		if (PlayerBotEkwStacks(item))
		{
			LPITEM stack = PlayerBotEkwBagStackOf(ch, item);
			if (stack && PlayerBotEkwJoin(stack, item, st))
			{
				bGone = true;
				return true;
			}
		}
		const int cell = PlayerBotEkwFindBagCell(ch, item->GetSize());
		if (cell < 0)
			return false;
		const BYTE bWindow = item->GetWindow();
		const WORD wFrom = item->GetCell();
		item->RemoveFromCharacter();
		if (!item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell)))
		{
			sys_err("PLAYERBOT_EKW: bag refused pid=%u vnum=%u from=%u/%u cell=%d", ch->GetPlayerID(), item->GetVnum(),
					(unsigned)bWindow, (unsigned)wFrom, cell);
			ch->AutoGiveItem(item, true);
			return false;
		}
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		return true;
	}

	int CountPlayerBotEkwStoredCells(LPCHARACTER ch)
	{
		int n = 0;
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
			for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
			{
				LPITEM item = ch->Mt2009SpecialGetItem(w, i);
				if (item && item->GetCell() == i)
					++n;
			}
		return n;
	}

	// The storages' items, each once (an item taller than one cell is in the grid at every cell it covers).
	void CollectPlayerBotEkwStored(LPCHARACTER ch, std::vector<LPITEM>& out)
	{
		out.clear();
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
			for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
			{
				LPITEM item = ch->Mt2009SpecialGetItem(w, i);
				if (item && item->GetCell() == i && item->GetWindow() == w)
					out.push_back(item);
			}
	}

	// ---- MT2009_PLUS_BOT_EKW_PAGES_V1 (the owner, 28 October 2026): the storages are more pages of the bot's bag.
	// The searches for goods to sell, give or use (the whispered deals and the meetings, "do you have X", the market's
	// "holds none of the kind", the alchemy's Cors and beans) look at the bag and the storages together
	// (CollectPlayerBotOwnedItems). The engine never sees a storage item: what a deal puts in the trade window, what
	// the alchemy uses, comes into a bag cell first (PlayerBotEkwBringToBag, PlayerBotEkwFetchMatching), and a full
	// bag first lends the storages something else (PlayerBotEkwMakeBagRoom: a kind's extra stack, then goods - the
	// pass's own rules). A counter's service visit and a town visit take the stored goods into the bag's spare room
	// first (PlayerBotEkwFetchGoods), so the counter and the merchants find them where they always looked. What came
	// back this way is held in the bag for PLAYERBOT_EKW_HOLD_MS (no pass stashes it again before it is sold or used).
	// The engine's CountSpecifyItem / RemoveSpecifyItem read the storages already (MT2009_PLUS_EKWIPUNEK_V1).
	// "m2_ekw_bots_off" and a companion serving its owner: the bag alone, as before. Logged: PLAYERBOT_EKW pages.
	const DWORD PLAYERBOT_EKW_HOLD_MS = 180000;
	const DWORD PLAYERBOT_EKW_PREFETCH_GAP_MS = 300000;
	const int PLAYERBOT_EKW_ROOM_MAX_STASH = 6;
	const DWORD PLAYERBOT_EKW_PAGES_REPORT_MS = 600000;

	struct TPlayerBotEkwPagesStats
	{
		int brought = 0;		// a storage item into a bag cell for a deal, a use, a sale
		int roomStash = 0;		// a bag item lent to the storages to make that room
		int noRoom = 0;			// a bring that found no room
		int fetchRuns = 0;		// PlayerBotEkwFetchMatching calls that brought something
		int prefetchRuns = 0;	// visits that took stored goods into the bag
		int prefetched = 0;		// the items of those visits
	};
	TPlayerBotEkwPagesStats s_kPlayerBotEkwPagesStats;
	std::map<DWORD, DWORD> s_mapPlayerBotEkwHeld;	// item id -> held in the bag until

	void HoldPlayerBotEkwItem(LPITEM item, DWORD dwNow)
	{
		if (!item)
			return;
		if (s_mapPlayerBotEkwHeld.size() > 4096)
			for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotEkwHeld.begin(); it != s_mapPlayerBotEkwHeld.end(); )
				if ((int)(dwNow - it->second) >= 0)
					s_mapPlayerBotEkwHeld.erase(it++);
				else
					++it;
		s_mapPlayerBotEkwHeld[item->GetID()] = dwNow + PLAYERBOT_EKW_HOLD_MS;
	}

	bool IsPlayerBotEkwHeld(LPITEM item, DWORD dwNow)
	{
		if (!item)
			return false;
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotEkwHeld.find(item->GetID());
		if (it == s_mapPlayerBotEkwHeld.end())
			return false;
		if ((int)(dwNow - it->second) < 0)
			return true;
		s_mapPlayerBotEkwHeld.erase(it);
		return false;
	}

	bool IsPlayerBotEkwWindow(BYTE bWindow)
	{
		return bWindow >= UPGRADE_INVENTORY && bWindow <= CHEST_INVENTORY;
	}

	// A bot whose storages count as its bag's pages: not with the kill switch, never a companion serving its owner.
	bool IsPlayerBotEkwPagesOn(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && ch->IsItemLoaded() && !ArePlayerBotEkwOff() &&
				!IsPlayerBotSidekickServing(ch) && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	// Everything the bot owns to sell, give or use: the bag's four pages (each item once), then the storages.
	void CollectPlayerBotOwnedItems(LPCHARACTER ch, std::vector<LPITEM>& out)
	{
		out.clear();
		if (!ch || !ch->IsItemLoaded())
			return;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell)
				out.push_back(item);
		}
		if (!IsPlayerBotEkwPagesOn(ch))
			return;
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		out.insert(out.end(), stored.begin(), stored.end());
	}

	// A bag cell of bSize for an item coming back: while there is none, the storages take (A) a kind's extra stack
	// (not its biggest), then (B) a stack of goods - never keep's kind, never what was just brought back (held),
	// never the working stock. True when the bag has the cell.
	bool PlayerBotEkwMakeBagRoom(LPCHARACTER ch, BYTE bSize, LPITEM keep)
	{
		if (!ch || bSize < 1)
			return false;
		if (PlayerBotEkwFindBagCell(ch, bSize) >= 0)
			return true;
		if (!IsPlayerBotEkwPagesOn(ch))
			return false;
		const DWORD dwNow = get_dword_time();
		TPlayerBotEkwStats st;
		int stashed = 0;
		for (int pass = 0; pass < 2 && stashed < PLAYERBOT_EKW_ROOM_MAX_STASH; ++pass)
		{
			for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && stashed < PLAYERBOT_EKW_ROOM_MAX_STASH; ++cell)
			{
				LPITEM item = ch->GetInventoryItem((WORD)cell);
				if (!item || item->GetCell() != cell || item == keep || !IsPlayerBotEkwMovable(ch, item))
					continue;
				if ((keep && item->GetVnum() == keep->GetVnum()) || IsPlayerBotEkwHeld(item, dwNow))
					continue;
				const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
				if (!bWindow)
					continue;
				if (pass == 0)
				{
					// a kind's extra stack: the bag keeps a bigger one of the kind
					if (!PlayerBotEkwStacks(item))
						continue;
					LPITEM bigger = PlayerBotEkwBagStackOf(ch, item);
					if (!bigger || bigger->GetCount() < item->GetCount())
						continue;
				}
				else if (IsPlayerBotEkwWorkingStock(ch, item, bWindow))
					continue;
				bool bGone = false;
				if (!PlayerBotEkwToStorage(ch, item, bWindow, st, bGone))
					continue;
				++stashed;
				++s_kPlayerBotEkwPagesStats.roomStash;
				if (PlayerBotEkwFindBagCell(ch, bSize) >= 0)
					return true;
			}
		}
		return PlayerBotEkwFindBagCell(ch, bSize) >= 0;
	}

	// A storage item into a bag cell of its own, as it is (no stack joins it, so the caller's pointer and count stay
	// true), room made first when the bag has none. True when the item is in the bag (or already was).
	bool PlayerBotEkwBringToBag(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetOwner() != ch)
			return false;
		const BYTE bWindow = item->GetWindow();
		if (bWindow == INVENTORY)
			return true;
		if (!IsPlayerBotEkwWindow(bWindow) || !IsPlayerBotEkwPagesOn(ch) || !IsPlayerBotEkwMovable(ch, item))
			return false;
		int cell = PlayerBotEkwFindBagCell(ch, item->GetSize());
		if (cell < 0 && PlayerBotEkwMakeBagRoom(ch, item->GetSize(), item))
			cell = PlayerBotEkwFindBagCell(ch, item->GetSize());
		if (cell < 0)
		{
			++s_kPlayerBotEkwPagesStats.noRoom;
			return false;
		}
		const WORD wFrom = item->GetCell();
		item->RemoveFromCharacter();
		if (!item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell)))
		{
			sys_err("PLAYERBOT_EKW: pages bag refused pid=%u vnum=%u from=%u/%u cell=%d", ch->GetPlayerID(), item->GetVnum(),
					(unsigned)bWindow, (unsigned)wFrom, cell);
			ch->AutoGiveItem(item, true);
			return false;
		}
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		HoldPlayerBotEkwItem(item, get_dword_time());
		++s_kPlayerBotEkwPagesStats.brought;
		return true;
	}

	// The stored items that match, brought into the bag until the bag holds needUnits of them (the bag's own count
	// first). Returns the units brought.
	int PlayerBotEkwFetchMatching(LPCHARACTER ch, TPlayerBotEkwMatch match, const void* ctx, int needUnits)
	{
		if (!match || needUnits <= 0 || !IsPlayerBotEkwPagesOn(ch))
			return 0;
		int have = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && match(ch, item, ctx))
				have += (int)item->GetCount();
		}
		if (have >= needUnits)
			return 0;
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		int brought = 0;
		for (size_t i = 0; i < stored.size() && have < needUnits; ++i)
		{
			LPITEM item = stored[i];
			if (!match(ch, item, ctx) || !IsPlayerBotEkwMovable(ch, item))
				continue;
			const int units = (int)item->GetCount();
			if (!PlayerBotEkwBringToBag(ch, item))
				break;	// no room
			have += units;
			brought += units;
		}
		if (brought > 0)
			++s_kPlayerBotEkwPagesStats.fetchRuns;
		return brought;
	}

	// Before a counter's service visit or a town visit: the stored goods (not the working stock, which comes back on
	// its own) into the bag's spare room - never below PLAYERBOT_EKW_STASH_BELOW free cells, so no pass stashes them
	// straight back - once in PLAYERBOT_EKW_PREFETCH_GAP_MS. Returns the items brought.
	int PlayerBotEkwFetchGoods(LPCHARACTER ch, const char* why)
	{
		static std::map<DWORD, DWORD> s_next;
		if (!IsPlayerBotEkwPagesOn(ch) || ch->GetExchange() || ch->IsOpenSafebox() || ch->IsCubeOpen())
			return 0;
		const DWORD dwNow = get_dword_time();
		std::map<DWORD, DWORD>::iterator next = s_next.find(ch->GetPlayerID());
		if (next != s_next.end() && (int)(dwNow - next->second) < 0)
			return 0;
		s_next[ch->GetPlayerID()] = dwNow + PLAYERBOT_EKW_PREFETCH_GAP_MS;
		int freeNow = CountPlayerBotFreeInventoryCells(ch);
		if (freeNow <= PLAYERBOT_EKW_STASH_BELOW)
			return 0;
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		int n = 0;
		for (size_t i = 0; i < stored.size(); ++i)
		{
			LPITEM item = stored[i];
			if (!IsPlayerBotEkwMovable(ch, item) || IsPlayerBotEkwWorkingStock(ch, item, item->GetWindow()))
				continue;
			if (freeNow - (int)item->GetSize() < PLAYERBOT_EKW_STASH_BELOW || PlayerBotEkwFindBagCell(ch, item->GetSize()) < 0)
				continue;
			if (!PlayerBotEkwBringToBag(ch, item))
				continue;
			++n;
			freeNow = CountPlayerBotFreeInventoryCells(ch);
		}
		if (n > 0)
		{
			++s_kPlayerBotEkwPagesStats.prefetchRuns;
			s_kPlayerBotEkwPagesStats.prefetched += n;
			sys_log(0, "PLAYERBOT_EKW: pages goods pid=%u name=%s why=%s items=%d free=%d stored_cells=%d", ch->GetPlayerID(),
					ch->GetName(), why ? why : "-", n, freeNow, CountPlayerBotEkwStoredCells(ch));
		}
		return n;
	}

	void ReportPlayerBotEkwPages(DWORD dwNow)
	{
		static DWORD s_next = 0;
		if (s_next != 0 && (int)(dwNow - s_next) < 0)
			return;
		s_next = dwNow + PLAYERBOT_EKW_PAGES_REPORT_MS;
		TPlayerBotEkwPagesStats& s = s_kPlayerBotEkwPagesStats;
		if (s.brought || s.roomStash || s.noRoom || s.prefetchRuns)
			sys_log(0, "PLAYERBOT_EKW: pages report brought=%d room_stash=%d no_room=%d fetch_runs=%d prefetch_runs=%d "
					"prefetched=%d held=%u", s.brought, s.roomStash, s.noRoom, s.fetchRuns, s.prefetchRuns, s.prefetched,
					(unsigned)s_mapPlayerBotEkwHeld.size());
		s = TPlayerBotEkwPagesStats();
	}

	// One kind back into the bag on the spot, a stack of it (FindPlayerBotBagItem's miss, or any rule that needs it
	// now). True when the bag now holds some.
	bool PlayerBotEkwFetchVnum(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || !vnum || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded() ||
				ch->GetExchange() || ch->IsOpenSafebox() || ch->IsCubeOpen())
			return false;
		if (!IsPlayerBotEkwPagesOn(ch))	// MT2009_PLUS_BOT_EKW_PAGES_V1: the kill switch, a serving companion
			return false;
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		LPITEM best = NULL;
		for (size_t i = 0; i < stored.size(); ++i)
			if (stored[i]->GetVnum() == vnum && IsPlayerBotEkwMovable(ch, stored[i]) &&
					(!best || stored[i]->GetCount() > best->GetCount()))
				best = stored[i];
		if (!best)
			return false;
		TPlayerBotEkwStats st;
		bool bGone = false;
		const ITEM_COUNT count = best->GetCount();
		// MT2009_PLUS_BOT_EKW_PAGES_V1: a full bag lends the storages something else first; what came back is held
		if (!PlayerBotEkwToBag(ch, best, st, bGone))
		{
			if (!PlayerBotEkwMakeBagRoom(ch, best->GetSize(), best) || !PlayerBotEkwToBag(ch, best, st, bGone))
			{
				++s_kPlayerBotEkwPagesStats.noRoom;
				return false;
			}
		}
		if (!bGone)
			HoldPlayerBotEkwItem(best, get_dword_time());
		sys_log(0, "PLAYERBOT_EKW: fetch pid=%u name=%s vnum=%u count=%u joined=%d free=%d", ch->GetPlayerID(), ch->GetName(),
				vnum, (unsigned)count, st.joined, CountPlayerBotFreeInventoryCells(ch));
		return true;
	}

	// ---- MT2009_PLUS_BOT_EKW_ROUTE_V1 (the owner, 31 October 2026 - boty-decyzje-2026-10-31.md, point 1: "Dodatkowy
	// ekwipunek: boty maja z niego korzystac - podnoszone materialy/ksiegi/kamienie/zaczarowania/skrzynie trafiaja do
	// okien jak u gracza; sprzedaz, stragan, ulepszanie, skrzynie, ksiegi czytaja tez z okien; jednorazowe przeniesienie
	// tego, co juz lezy w torbach").
	//
	// The engine routes a bot's item as a player's (CHARACTER::GetSpecialWindowFor / Mt2009EkwAutoStackProto ask
	// PlayerBotEkwRouteWindow, below): what it picks up, is given, buys at an NPC, a counter or the ItemShop, takes in a
	// trade - by its category into its storage, joined to the storage's stacks first. One exception keeps the passes that
	// use an item by its bag cell whole (the refine scrolls on the anvil, the change stones of the bonus pass, the books
	// read, the soul stones seated, the Cors the Alchemist opens): the bot's working stock (IsPlayerBotEkwWorkingStock)
	// goes into the bag while the bag holds none of the kind or a stack of it with room, and into the storage once the
	// bag's stack is full - the bag keeps one stack of each kind it works with, the pass below tops it up from the storage.
	// Where the storage is full the engine puts the item into the bag as before (no refusal).
	//
	// Read from the storages where they lie: the merchants' junk sale - in a village and the remote one where the bot
	// stands (SellPlayerBotJunkAtMerchant, HasPlayerBotJunkForMerchant, CountPlayerBotJunkItems), the chest pass
	// (ManagePlayerBotChests: the storage's chests used in their cell - UseItem takes any window), the loot's room
	// (PlayerBotBagTakesDrop) and the ItemShop's room (PlayerBotEkwHasRoomForVnum); the counts of every rule
	// (CountSpecifyItem / RemoveSpecifyItem: the refine materials, the Handlarka's and the Dozorca's inputs, the G0 dust -
	// the engine's MT2009_PLUS_EKWIPUNEK_V1 count / remove), the Yohara bonus plan's change stones
	// (ReadPlayerBotYoharaBonusBag), the deals' and the market's searches (CollectPlayerBotOwnedItems). Brought into the
	// bag before the engine works on them in a bag cell (MT2009_PLUS_BOT_EKW_PAGES_V1, unchanged): the counter's goods at
	// its service visit and a town visit (PlayerBotEkwFetchGoods), a deal's piece (PlayerBotEkwFetchMatching), a kind a
	// rule misses in the bag (PlayerBotEkwFetchVnum). The safebox's deposits stay the bag's (books, materials, dead stock
	// it has no room for) - the storages are room of their own, nothing in them presses on the bag.
	//
	// The pass (ManagePlayerBotEkwipunek) with routing on: the goods are no longer brought back into a roomy bag; a
	// kind's extra stacks and the goods that came into the bag (a full storage, a fetch whose hold ran out) go to the
	// storages whatever the bag's room; once, the first time a bot's pass runs with routing on, everything of a category
	// already in its bag is moved (its working stock down to one stack of a kind) - quest flag PLAYERBOT_EKW_MOVED_FLAG,
	// the log's "PLAYERBOT_EKW: moved once"; at most PLAYERBOT_EKW_MOVE_BOTS_PER_MIN bots a core a minute. Census every
	// ten minutes: "PLAYERBOT_EKW: route report" (routed by window, the working stock kept in the bag, a full storage's
	// fallback, the one-time moves). Off: event flag "m2_ekw_bots_route_off" (the old lending only) or "m2_ekw_bots_off"
	// (nothing).
	const char* PLAYERBOT_EKW_MOVED_FLAG = "playerbot.ekw_moved";
	const DWORD PLAYERBOT_EKW_ROUTE_REPORT_MS = 600000;
	const int PLAYERBOT_EKW_MOVE_BOTS_PER_MIN = 30;

	struct TPlayerBotEkwRouteStats
	{
		unsigned int routed[SPECIAL_INVENTORY_WINDOW_COUNT] = {};	// an item (or a count's stacks) to its storage
		unsigned int workToBag = 0;		// working stock into the bag (no stack of it there, or one with room)
		unsigned int storageFull = 0;	// routed, but the storage had no cell: the bag took it
		unsigned int movedBots = 0;		// bots whose one-time move ran
		unsigned int movedItems = 0;	// stacks of those moves into the storages
		unsigned int movedLeft = 0;		// what those moves left in the bag (a storage full)
		unsigned int stashedRouted = 0;	// routed passes' stashes after the move (goods that came into the bag)
	};
	TPlayerBotEkwRouteStats s_kPlayerBotEkwRouteStats;
	DWORD s_dwPlayerBotEkwRouteLastItem = 0, s_dwPlayerBotEkwRouteLastPid = 0;

	bool IsPlayerBotEkwRouteOn(LPCHARACTER ch)
	{
		return IsPlayerBotEkwPagesOn(ch) && quest::CQuestManager::instance().GetEventFlag("m2_ekw_bots_route_off") == 0;
	}

	// The bag's stacks of a kind (the item's vnum and sockets; a vnum alone for a count): any at all, one with room.
	void PlayerBotEkwBagKindState(LPCHARACTER ch, DWORD vnum, LPITEM item, bool& any, bool& room)
	{
		any = room = false;
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && !room; ++cell)
		{
			LPITEM other = ch->GetInventoryItem((WORD)cell);
			if (!other || other == item || other->GetCell() != cell || other->GetVnum() != vnum)
				continue;
			if (item && !PlayerBotEkwSameKind(item, other))
				continue;
			any = true;
			if (PlayerBotEkwStacks(other) && other->GetCount() < other->GetMaxStack())
				room = true;
		}
	}

	BYTE PlayerBotEkwRouteDecide(LPCHARACTER ch, LPITEM item, const TItemTable* proto, DWORD vnum, bool census)
	{
		if (!ch || (!item && !proto) || !IsPlayerBotEkwRouteOn(ch))
			return 0;
		BYTE bWindow = 0;
		bool work = false;
		if (item)
		{
			if (item->GetOwner() == ch)
				return 0;	// an item of the bot's own on the move: the engine's call, not one coming in
			bWindow = Mt2009EkwCategoryOfItem(item);
			if (!bWindow)
				return 0;
			vnum = item->GetVnum();
			work = IsPlayerBotEkwWorkingStock(ch, item, bWindow);
		}
		else
		{
			if (proto->bType == ITEM_DS || proto->bType == ITEM_SPECIAL_DS)
				return 0;
			bWindow = Mt2009EkwCategoryOf(proto->bType, proto->bSubType, vnum);
			if (!bWindow)
				return 0;
			work = IsPlayerBotEkwWorkingStockProto(ch, proto, vnum, bWindow);
		}
		// the census once an item (the engine asks twice for one: its stacks, then its cell); never for a probe
		const bool fresh = census && (!item || item->GetID() != s_dwPlayerBotEkwRouteLastItem ||
				ch->GetPlayerID() != s_dwPlayerBotEkwRouteLastPid);
		if (item && census)
		{
			s_dwPlayerBotEkwRouteLastItem = item->GetID();
			s_dwPlayerBotEkwRouteLastPid = ch->GetPlayerID();
		}
		if (work)
		{
			bool any = false, room = false;
			PlayerBotEkwBagKindState(ch, vnum, item, any, room);
			if (!any || room)
			{
				if (fresh)
					++s_kPlayerBotEkwRouteStats.workToBag;
				return 0;
			}
		}
		if (fresh)
		{
			const int size = item ? (int)item->GetSize() : (int)proto->bSize;
			if (ch->GetEmptySpecialInventory(bWindow, (BYTE)std::max(1, size)) < 0)
				++s_kPlayerBotEkwRouteStats.storageFull;
			else
				++s_kPlayerBotEkwRouteStats.routed[bWindow - UPGRADE_INVENTORY];
		}
		return bWindow;
	}

	// The room a purchase of chunks stacks of vnum finds: its category's storage when the bot routes it there, else the
	// bag (the ItemShop's purchase: MT2009_PLUS_BOT_EKW_ROUTE_V1 - a bag short of room no longer refuses a Cor or a stone).
	bool PlayerBotEkwHasRoomForVnum(LPCHARACTER ch, DWORD vnum, int chunks)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!ch || !proto || chunks < 1)
			return false;
		const int size = std::max<int>(1, proto->bSize);
		BYTE bWindow = 0;
		if (IsPlayerBotEkwRouteOn(ch) && proto->bType != ITEM_DS && proto->bType != ITEM_SPECIAL_DS)
		{
			bWindow = Mt2009EkwCategoryOf(proto->bType, proto->bSubType, vnum);
			if (bWindow && IsPlayerBotEkwWorkingStockProto(ch, proto, vnum, bWindow))
			{
				bool any = false, room = false;
				PlayerBotEkwBagKindState(ch, vnum, NULL, any, room);
				if (!any || room)
					bWindow = 0;
			}
		}
		if (bWindow)
		{
			int free = 0;
			for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM && free < chunks; ++i)
				if (ch->Mt2009SpecialIsEmptyGrid(bWindow, i, (BYTE)size, -1))
					++free;
			if (free >= chunks)
				return true;
		}
		return chunks == 1 ? ch->GetEmptyInventory((BYTE)size) >= 0
				: CountPlayerBotFreeInventoryCells(ch) >= chunks * size + 1;
	}

	void ReportPlayerBotEkwRoute(DWORD dwNow)
	{
		static DWORD s_next = 0;
		if (s_next != 0 && (int)(dwNow - s_next) < 0)
			return;
		s_next = dwNow + PLAYERBOT_EKW_ROUTE_REPORT_MS;
		TPlayerBotEkwRouteStats& s = s_kPlayerBotEkwRouteStats;
		const unsigned int total = s.routed[0] + s.routed[1] + s.routed[2] + s.routed[3] + s.routed[4];
		if (total || s.workToBag || s.storageFull || s.movedBots || s.stashedRouted)
			sys_log(0, "PLAYERBOT_EKW: route report routed=%u upgrade=%u book=%u stone=%u change=%u chest=%u work_to_bag=%u "
					"storage_full=%u moved_bots=%u moved_items=%u moved_left=%u stashed=%u", total, s.routed[0], s.routed[1],
					s.routed[2], s.routed[3], s.routed[4], s.workToBag, s.storageFull, s.movedBots, s.movedItems, s.movedLeft,
					s.stashedRouted);
		s = TPlayerBotEkwRouteStats();
	}

	// The one-time move: everything of a category in the bag into its storage - a kind's stacks joined into the
	// storage's, the working stock down to the bag's biggest stack of the kind (topped up from the others first). Not
	// worn, locked, in a trade or on sale. Returns false while the bot is not ready for it (the flag stays unset).
	bool MovePlayerBotBagToEkwOnce(LPCHARACTER ch)
	{
		TPlayerBotEkwStats st;
		int moved = 0, left = 0, joined = 0;
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem((WORD)cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotEkwMovable(ch, item))
				continue;
			const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
			if (!bWindow)
				continue;
			if (IsPlayerBotEkwWorkingStock(ch, item, bWindow))
			{
				LPITEM keep = PlayerBotEkwStacks(item) ? PlayerBotEkwBagStackOf(ch, item) : NULL;
				bool kept = false;
				if (!keep)
					kept = true;	// the bag's only stack (or piece) of its kind stays
				else if (keep->GetCount() < item->GetCount() ||
						(keep->GetCount() == item->GetCount() && keep->GetCell() > item->GetCell()))
					kept = true;	// this one is the kind's biggest: it stays, the others come to it or go
				if (!kept && !PlayerBotEkwStacks(item))
				{
					// a single piece of working stock (a book that does not stack): one of the kind stays
					bool another = false;
					for (int c2 = 0; c2 < cell && !another; ++c2)
					{
						LPITEM other = ch->GetInventoryItem((WORD)c2);
						another = other && other->GetCell() == c2 && PlayerBotEkwSameKind(item, other);
					}
					kept = !another;
				}
				if (kept)
					continue;
				if (keep && PlayerBotEkwJoin(keep, item, st))
				{
					++joined;
					continue;
				}
			}
			bool bGone = false;
			if (PlayerBotEkwToStorage(ch, item, bWindow, st, bGone))
				++moved;
			else
				++left;
		}
		ch->SetQuestFlag(PLAYERBOT_EKW_MOVED_FLAG, 1);
		++s_kPlayerBotEkwRouteStats.movedBots;
		s_kPlayerBotEkwRouteStats.movedItems += (unsigned int)moved;
		s_kPlayerBotEkwRouteStats.movedLeft += (unsigned int)left;
		sys_log(0, "PLAYERBOT_EKW: moved once pid=%u name=%s lv=%d moved=%d joined=%d left=%d joined_units=%d free=%d "
				"stored_cells=%d map=%ld", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), moved, joined, left, st.joined,
				CountPlayerBotFreeInventoryCells(ch), CountPlayerBotEkwStoredCells(ch), ch->GetMapIndex());
		return true;
	}

	// Whether the bot is in the middle of something that works with its bag's cells: no pass then.
	bool IsPlayerBotEkwBusy(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->GetMyShop() || ch->IsOpenSafebox() ||
				ch->IsCubeOpen() || !ch->CanHandleItem())
			return true;
		if (state.bVisitingShop || state.bMarketTrip || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingAlchemist || state.bVisitingUriel || state.bCraftErrand != 0 || state.bVisitingDsAlchemist ||
				state.bVisitingStable || state.bTownVisitPhase != BOT_TOWN_PHASE_NONE)
			return true;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		// its counter's service visit takes goods from the bag over several steps
		if (state.offlineShop.visitUntil != 0 && (int)(dwNow - state.offlineShop.visitUntil) < 0)
			return true;
#else
		(void)dwNow;
#endif
		return false;
	}

	void ManagePlayerBotEkwipunek(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		static std::map<DWORD, DWORD> s_next;
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded())
			return;
		const DWORD pid = ch->GetPlayerID();
		DWORD& next = s_next[pid];
		if (next == 0)
			next = dwNow + (pid % PLAYERBOT_EKW_PASS_MS);	// staggered over the bots
		if ((int)(dwNow - next) < 0)
			return;
		next = dwNow + PLAYERBOT_EKW_PASS_MS;
		ReportPlayerBotEkwPages(dwNow);	// MT2009_PLUS_BOT_EKW_PAGES_V1
		ReportPlayerBotEkwRoute(dwNow);	// MT2009_PLUS_BOT_EKW_ROUTE_V1

		if (ArePlayerBotEkwOff() || IsPlayerBotSidekickServing(ch) || IsPlayerBotSidekickPID(pid))
			return;
		if (IsPlayerBotEkwBusy(ch, state, dwNow))
			return;

		// MT2009_PLUS_BOT_EKW_ROUTE_V1: the bot routes - its bag's items of a category moved once, the goods stay in the
		// storages (no refill into a roomy bag), what comes into the bag goes to them whatever the bag's room
		const bool routed = IsPlayerBotEkwRouteOn(ch);
		if (routed && ch->GetQuestFlag(PLAYERBOT_EKW_MOVED_FLAG) == 0)
		{
			// a core's moves spread over time (every moved stack is a save to the db core): PLAYERBOT_EKW_MOVE_BOTS_PER_MIN
			// bots a minute, the others wait for a later pass with their bags as they are
			static DWORD s_dwMoveMinute = 0;
			static int s_iMovesThisMinute = 0;
			if (s_dwMoveMinute == 0 || dwNow - s_dwMoveMinute >= 60000)
			{
				s_dwMoveMinute = dwNow ? dwNow : 1;
				s_iMovesThisMinute = 0;
			}
			if (s_iMovesThisMinute < PLAYERBOT_EKW_MOVE_BOTS_PER_MIN)
			{
				++s_iMovesThisMinute;
				MovePlayerBotBagToEkwOnce(ch);
			}
			return;
		}

		TPlayerBotEkwStats st;
		int moves = 0;
		const int freeBefore = CountPlayerBotFreeInventoryCells(ch);
		int freeNow = freeBefore;

		// ---- refill: the working stock (a kind the bag lacks or holds less than a stack of), then goods in a roomy bag
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		for (size_t i = 0; i < stored.size() && moves < PLAYERBOT_EKW_MAX_MOVES; ++i)
		{
			LPITEM item = stored[i];
			if (!IsPlayerBotEkwMovable(ch, item))
				continue;
			// MT2009_PLUS_EKWIPUNEK_CATS_V2 (3 November 2026): a stored item whose category moved - the Pozwolenia, shards
			// and supplements from the materials' storage to Zaczarowanie, the refine scrolls (no category now) to the bag
			{
				const BYTE bNow = Mt2009EkwCategoryOfItem(item);
				if (bNow != item->GetWindow())
				{
					bool bGone = false;
					const bool bMoved = bNow ? PlayerBotEkwToStorage(ch, item, bNow, st, bGone)
							: (freeNow >= PLAYERBOT_EKW_WORK_REFILL_MIN_FREE && PlayerBotEkwToBag(ch, item, st, bGone));
					if (bMoved)
					{
						++moves;
						++st.recategorized;
						freeNow = CountPlayerBotFreeInventoryCells(ch);
					}
					continue;
				}
			}
			const BYTE bWindow = item->GetWindow();
			const bool work = IsPlayerBotEkwWorkingStock(ch, item, bWindow);
			LPITEM bagStack = PlayerBotEkwStacks(item) ? PlayerBotEkwBagStackOf(ch, item) : NULL;
			if (work && bagStack)
			{
				if (bagStack->GetCount() < bagStack->GetMaxStack())
				{
					PlayerBotEkwJoin(bagStack, item, st);
					++st.topUp;
					++moves;
				}
				continue;
			}
			bool bagHasKind = bagStack != NULL;
			if (work && !bagHasKind && !PlayerBotEkwStacks(item))
			{
				// a single piece of working stock: back when the bag holds none of its kind
				for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && !bagHasKind; ++cell)
				{
					LPITEM other = ch->GetInventoryItem((WORD)cell);
					bagHasKind = other && other->GetCell() == cell && PlayerBotEkwSameKind(item, other);
				}
			}
			const bool want = work ? (!bagHasKind && freeNow >= PLAYERBOT_EKW_WORK_REFILL_MIN_FREE)
					: (!routed && freeNow - (int)item->GetSize() >= PLAYERBOT_EKW_REFILL_ABOVE);
			if (!want)
				continue;
			bool bGone = false;
			if (!PlayerBotEkwToBag(ch, item, st, bGone))
				continue;
			++moves;
			if (work)
				++st.refillWork;
			else
				++st.refillGoods;
			freeNow = CountPlayerBotFreeInventoryCells(ch);
		}

		// ---- stash: only a bag short of room
		// MT2009_PLUS_BOT_EKW_ROUTE_V1: a routing bot's whatever its room (the goods' place is the storage)
		const int stashBefore = st.stashSurplus + st.stashGoods;
		if (routed || freeNow < PLAYERBOT_EKW_STASH_BELOW)
		{
			// (A) a kind's extra stacks: the biggest stays (topped up), the rest into the storage
			for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && moves < PLAYERBOT_EKW_MAX_MOVES; ++cell)
			{
				LPITEM item = ch->GetInventoryItem((WORD)cell);
				if (!item || item->GetCell() != cell || !IsPlayerBotEkwMovable(ch, item) || !PlayerBotEkwStacks(item) ||
						IsPlayerBotEkwHeld(item, dwNow))	// MT2009_PLUS_BOT_EKW_PAGES_V1: just brought back
					continue;
				const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
				if (!bWindow)
					continue;
				LPITEM keep = PlayerBotEkwBagStackOf(ch, item);
				if (!keep || keep->GetCount() < item->GetCount() ||
						(keep->GetCount() == item->GetCount() && keep->GetCell() > item->GetCell()))
					continue;	// this one is the kind's biggest stack (the first of equals): it stays
				if (PlayerBotEkwJoin(keep, item, st))
				{
					++moves;
					continue;
				}
				bool bGone = false;
				if (PlayerBotEkwToStorage(ch, item, bWindow, st, bGone))
				{
					++st.stashSurplus;
					++moves;
				}
			}
			freeNow = CountPlayerBotFreeInventoryCells(ch);

			// (B) whole stacks of goods until the bag has its target (a routing bot's: all of them)
			for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && moves < PLAYERBOT_EKW_MAX_MOVES &&
					(routed || freeNow < PLAYERBOT_EKW_STASH_TARGET); ++cell)
			{
				LPITEM item = ch->GetInventoryItem((WORD)cell);
				if (!item || item->GetCell() != cell || !IsPlayerBotEkwMovable(ch, item))
					continue;
				const BYTE bWindow = Mt2009EkwCategoryOfItem(item);
				if (!bWindow || IsPlayerBotEkwWorkingStock(ch, item, bWindow) || IsPlayerBotEkwHeld(item, dwNow))
					continue;
				bool bGone = false;
				if (PlayerBotEkwToStorage(ch, item, bWindow, st, bGone))
				{
					++st.stashGoods;
					++moves;
					freeNow = CountPlayerBotFreeInventoryCells(ch);
				}
			}
		}

		if (routed)
			s_kPlayerBotEkwRouteStats.stashedRouted += (unsigned int)(st.stashSurplus + st.stashGoods - stashBefore);
		if (moves == 0)
			return;
		const int freeAfter = CountPlayerBotFreeInventoryCells(ch);
		sys_log(0, "PLAYERBOT_EKW: pass pid=%u name=%s lv=%d free_before=%d free_after=%d stash_surplus=%d stash_goods=%d "
				"joined_units=%d refill_work=%d topup=%d refill_goods=%d recategorized=%d stored_cells=%d map=%ld",
				pid, ch->GetName(), ch->GetLevel(), freeBefore, freeAfter, st.stashSurplus, st.stashGoods, st.joined,
				st.refillWork, st.topUp, st.refillGoods, st.recategorized, CountPlayerBotEkwStoredCells(ch), ch->GetMapIndex());
	}
}

// MT2009_PLUS_BOT_EKW_ROUTE_V1: the engine's question (playerbot_ekwipunek.cpp, CHARACTER::GetSpecialWindowFor and
// Mt2009EkwAutoStackProto, for a bot's descriptor only): the storage window an item - or a vnum given by count - goes
// to, 0 for the bag. This unit holds the bots' rules; the engine's unit only asks.
BYTE PlayerBotEkwRouteWindow(LPCHARACTER ch, LPITEM item, const TItemTable* proto, DWORD dwVnum)
{
	return PlayerBotEkwRouteDecide(ch, item, proto, dwVnum, true);
}

#endif
