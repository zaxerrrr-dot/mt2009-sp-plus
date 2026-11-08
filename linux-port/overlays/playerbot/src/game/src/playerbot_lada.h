#ifndef __INC_METIN2_PLAYERBOT_LADA_H__
#define __INC_METIN2_PLAYERBOT_LADA_H__

#include <deque>
#include <unordered_set>

// MT2009_PLUS_BOT_LADA_V1 - the bots' "lada": a counter with no limit, fed from anywhere (the owner, 8 November 2026:
// "Dzialaj z tym systemem" - lada bez limitu, plynna; boty dokladaja z kazdego miejsca i kanalu, wiekszosc dropu idzie
// na lade, lada jest magazynem; stosy sie lacza, zwrot czesciowy, wystawianie co ~30 minut; cena spada tylko przy
// nadmiarze i slabej sprzedazy, i tylko tanim liniom).
//
// What the ikashop is (read for this, 8 November 2026 - the engine's game core ikarus_shop*.cpp, the db core's
// ClientManagerIkarusShop.cpp / IkarusShopCache.cpp):
//   * the db core is the one authority: m_offlineshopShopCache holds every shop and line, each line with its buy
//     lock; every game core of every channel holds a full copy (CShopManager::m_mapShops) that the db core's
//     broadcasts keep (DG_ADD_ITEM, DG_REMOVE_ITEM, DG_EDIT_ITEM, DG_BUY_ITEM to every peer); the stand's entity is on
//     the one core hosting its map and channel. A line is a row of player.item in the window IKASHOP_OFFLINESHOP (the
//     price in its ikashop_data), written straight by the db core (QUERY_ITEM_SAVE bypasses the item cache for it);
//   * no number of lines is held anywhere but the add's own grid test on the game core (the bot's four pages, 320
//     cells, RecvShopAddItemClientPacket / playerbot_offline::FitsOnPage); the db core and CShop::AddItem take a line at
//     any pos (a WORD). What bounds a counter is the open packet (every line, ~100 bytes each, under the client's
//     600 KB receive buffer), the per-shop sum of prices (PLAYERBOT_GOLD_MAX, 2 bn for a bot) and the cost of the scans;
//   * the add moves the bag item into the shop window (saved, the instance destroyed) and asks the db core, which
//     writes the price and tells every core; the remove asks the db core, which refuses a locked line and tells every
//     core, the asking core alone creating the piece again in the owner's bag (or the shop safebox); the buy locks the
//     line in the db core (seen price checked), the buyer's core charges, the db core settles - the whole line, or a
//     part (MT2009_PLUS_SHOP_PART_STACK_V1: count and price of the line lowered in place, ceil(price x part / count));
//   * none of the three needs the stand's core: the shop handle is on every core and the db core answers whoever asks,
//     so a bot of the second channel can add to and take from its counter of the first. The distance and the open
//     board are only the client handlers' tests;
//   * the search (the Dom Towarowy fill, the filter search) walks every line of every shop of the asking core's copy -
//     linear in the world's lines, a name match on each, at most 6000 / 2500 results; the stand search walks the
//     stands of the map in reach.
//
// So every lada mutation here is one of the engine's three db requests - add, remove, edit - and goes through the db
// core and the bot's request journal (playerbot_offline::Begin / Sent / Complete: one request in flight a bot), never
// through a pointer of a line. Nothing is made: a merge is a remove and an add, a take-back of a part is a take-back of
// the line and the rest added again, a sale is the engine's buy. Equipment worn or reserved, the operator's policy, the
// SM coupons (their own rule, playerbot_sm_market_rule.h, on the visit's road), companions and players take no part.
//
// The pass: every bot with a stand standing (duration > 0), wherever it is, on any channel ("m2_bot_lada_xch_off" 1:
// only on the stand's channel), every PLAYERBOT_LADA interval (m2_bot_lada_min, 30 minutes, spread by the bot's id),
// takes up to m2_bot_lada_pass_ops (24) steps, one request each, waiting for the db core's answer between them, out of a
// core's bucket (m2_bot_lada_rate a second, 6):
//   1. a piece of its counter it should wear comes home (BotOfflineReclaimLine, the visit's own rule);
//   2. a kind its bag holds less of than its keep (the anvil's reserve, the herb's, the book's count - the visit's own
//      keeps) comes home from the counter, the whole line: the spare over the keep goes up again in the same pass;
//   3. the bag's goods (CollectPlayerBotShopItems with no "plenty" hold-back, the extra inventory's goods fetched
//      first) go up, best first: the spare over the keep, whole. A stackable kind whose counter holds a line short of
//      a full stack takes that line home first (merge), and the merged stack goes up as one;
//   4. two short lines of a kind on the counter with nothing of it in the bag: the smaller comes home (merge).
// A lada line stands past the visit's pages (pos 320 and up, its first byte off the locked and premium cells the
// engine's renewal checks): the stand's window shows the pages, the searches find everything. Caps:
// m2_bot_lada_cap (300) lines a bot, m2_bot_lada_world_cap (60000) bot lines in the world, the bot's 2 bn per counter.
// The lada's kinds (IsPlayerBotLadaKindItem) are the ordinary goods; the dragon stones, soul stones, energy shards,
// Cors, Materialy Rzemieslnicze, Moonlight chests, horse medals, SM coupons, refine scrolls, mission books, rare
// goods, belts, sashes, talismans, costumes, potions and the low gear under its cap stay with the visit's own rules -
// the visit no longer lists, cuts or restacks the lada's kinds while the lada is on.
//
// The price: new lines at the visit's listing price (GetPlayerBotListingPrice, the floor); the glut's tiers
// (playerbot_market_clearing.h, m2_bot_lada_price_off 1: the old clearing of every line) - a pass every
// PLAYERBOT_LADA_TIER_MS on the shop channel's cores ranks every line of each glutted kind by its unit price, the
// cheapest 10 % of the units 950 permille, the next 10 % 970, and edits the bot lines of the stands this core hosts to
// BotOfflineRepriceTarget (which applies the tier) - PLAYERBOT_LADA_TIER_EDITS_PER_S a second.
//
// Junk (what only the merchant takes) stays with the merchant unless m2_bot_lada_junk_on 1: then up to
// PLAYERBOT_LADA_JUNK_LINES lines of it a bot, back home after PLAYERBOT_LADA_JUNK_STALE_MS unsold (the merchant's
// yang is a bot's income).
//
// Log: "PLAYERBOT_LADA:" - pass (throttled), list / merge / take (throttled), stuck, census every 10 minutes (bot
// shops, lines, units, past-pages lines, the world's lines a search walks, the biggest counter, what the passes did,
// sales of the counters whose owners are here, the tiers) and its "kind" lines (the kinds of the most lines).

namespace
{
	const DWORD PLAYERBOT_LADA_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_LADA_TIER_MS = 5 * 60 * 1000;
	const int PLAYERBOT_LADA_TIER_EDITS_PER_S = 20;
	const DWORD PLAYERBOT_LADA_PASS_MAX_MS = 5 * 60 * 1000;		// a pass that cannot finish gives up
	const DWORD PLAYERBOT_LADA_STUCK_MS = 60 * 1000;			// the lada's own request unanswered this long is let go
	const DWORD PLAYERBOT_LADA_HOLD_OFF_MS = 6 * 60 * 60 * 1000;	// a visit's take-off stays off this long
	const DWORD PLAYERBOT_LADA_JUNK_STALE_MS = 48U * 60 * 60 * 1000;
	const int PLAYERBOT_LADA_JUNK_LINES = 40;
	const int PLAYERBOT_LADA_POS_BASE = SHOP_PLAYER_WIDTH * SHOP_PLAYER_HEIGHT * playerbot_offline::BOT_SHOP_PAGES;
	const int PLAYERBOT_LADA_POS_MAX = 60000;
	const size_t PLAYERBOT_LADA_CENSUS_KINDS = 8;

	struct TPlayerBotLadaCfg
	{
		bool on, tiers, xch, junk;
		int intervalMin, cap, worldCap, rate, passOps;
		TPlayerBotLadaCfg() : on(true), tiers(true), xch(true), junk(false), intervalMin(30), cap(300), worldCap(60000),
				rate(6), passOps(24) {}
	};
	TPlayerBotLadaCfg s_kPlayerBotLadaCfg;

	const TPlayerBotLadaCfg& GetPlayerBotLadaCfg()
	{
		static DWORD s_dwAt = 0;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			TPlayerBotLadaCfg& c = s_kPlayerBotLadaCfg;
			const TPlayerBotLadaCfg was = c;
			c.on = q.GetEventFlag("m2_bot_lada_off") == 0;
			c.tiers = c.on && q.GetEventFlag("m2_bot_lada_price_off") == 0;
			c.xch = q.GetEventFlag("m2_bot_lada_xch_off") == 0;
			c.junk = q.GetEventFlag("m2_bot_lada_junk_on") != 0;
			auto value = [&q](const char* flag, int def, int lo, int hi) {
				const int v = q.GetEventFlag(flag);
				return v <= 0 ? def : std::max(lo, std::min(hi, v));
			};
			c.intervalMin = value("m2_bot_lada_min", 30, 5, 240);
			c.cap = value("m2_bot_lada_cap", 300, 20, 2000);
			c.worldCap = value("m2_bot_lada_world_cap", 60000, 1000, 400000);
			c.rate = value("m2_bot_lada_rate", 6, 1, 50);
			c.passOps = value("m2_bot_lada_pass_ops", 24, 1, 200);
			s_bPlayerBotLadaTiers = c.tiers;
			if (was.on != c.on || was.tiers != c.tiers || was.xch != c.xch || was.junk != c.junk || was.intervalMin != c.intervalMin ||
					was.cap != c.cap || was.worldCap != c.worldCap || was.rate != c.rate || was.passOps != c.passOps)
				sys_log(0, "PLAYERBOT_LADA: config on=%d tiers=%d cross_channel=%d junk=%d interval_min=%d cap=%d world_cap=%d rate=%d pass_ops=%d",
						c.on ? 1 : 0, c.tiers ? 1 : 0, c.xch ? 1 : 0, c.junk ? 1 : 0, c.intervalMin, c.cap, c.worldCap, c.rate,
						c.passOps);
		}
		return s_kPlayerBotLadaCfg;
	}

	bool IsPlayerBotLadaOn()
	{
		return GetPlayerBotLadaCfg().on;
	}

	// ------------------------------------------------------------------------------------------------ the kinds
	// The goods the lada lists, merges and takes back - by the proto (a line's and a bag item's alike).
	bool IsPlayerBotLadaKindOf(DWORD vnum, const TItemTable* t)
	{
		if (!t || vnum == 0)
			return false;
		switch (t->bType)
		{
			case ITEM_DS: case ITEM_SPECIAL_DS: case ITEM_METIN: case ITEM_COSTUME: case ITEM_BELT: case ITEM_QUEST:
			case ITEM_POTION:
				return false;
			default:
				break;
		}
		if (t->bType == ITEM_USE && (t->bSubType == USE_POTION || t->bSubType == USE_POTION_NODELAY ||
				t->bSubType == USE_POTION_CONTINUE || t->bSubType == USE_TUNING))
			return false;
		if (IS_SET(t->dwAntiFlags, ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP))
			return false;
		if (IsPlayerBotEnergyShardVnum(vnum) || IsPlayerBotCorVnum(vnum) || vnum == PLAYERBOT_CRAFT_MATERIAL_VNUM_PRICED ||
				vnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM || vnum == PLAYERBOT_HORSE_MEDAL_VNUM || IsPlayerBotSmCouponVnum(vnum) ||
				IsPlayerBotRefineScroll(vnum) || IsPlayerBotMissionBook(vnum) || IsPlayerBotAwakeningGoods(vnum) ||
				GetPlayerBotRareGoodsKind(vnum) != PLAYERBOT_RARE_GOODS_NONE || IsPlayerBotBeltVnum(vnum) ||
				IsPlayerBotSashVnum(vnum) || IsPlayerBotFixedPriceTalismanVnum(vnum) || IsPlayerBotGuildBuildMaterial(vnum) ||
				IsPlayerBotPersonalBuffPotion(vnum))
			return false;
		return GetPlayerBotItemPolicyOf(vnum, t->bType) == PLAYERBOT_ITEM_POLICY_NONE;
	}

	bool IsPlayerBotLadaKindItem(LPITEM item)
	{
		if (!item || !IsPlayerBotLadaKindOf(item->GetVnum(), item->GetProto()))
			return false;
		if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP))
			return false;
		if (GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE)
			return false;
		if (IsPlayerBotPlainLowGearPiece(item) || CountsAgainstPlayerBotLowGearCap(item))
			return false;
		if (IsPlayerBotPackedPotion(item) || IsPlayerBotCraftedPotion(item))
			return false;
		return true;
	}

	bool IsPlayerBotLadaStackableOf(const TItemTable* t)
	{
		return t && IS_SET(t->dwFlags, ITEM_FLAG_STACKABLE) && !IS_SET(t->dwAntiFlags, ITEM_ANTIFLAG_STACK);
	}

	// A counter line the bag stack pours into: the same vnum, every socket equal (PlayerBotStacksTogether's rule).
	bool PlayerBotLadaLineStacksWith(const ikashop::CShopItem& line, LPITEM item)
	{
		const auto& info = line.GetInfo();
		if (!item || info.vnum != item->GetVnum() || !IsPlayerBotLadaStackableOf(line.GetTable()))
			return false;
		for (int s = 0; s < ITEM_SOCKET_MAX_NUM; ++s)
			if (info.alSockets[s] != item->GetSocket(s))
				return false;
		return true;
	}

	// ------------------------------------------------------------------------------------------------ state
	struct TPlayerBotLada
	{
		DWORD nextPass = 0, passUntil = 0, opAt = 0, opItem = 0;
		bool active = false;
		int ops = 0;
		DWORD reclaim = 0;
		std::vector<DWORD> need;		// lines to come home for the keep, read at the pass's start
		std::vector<DWORD> junkStale;	// junk lines unsold too long (m2_bot_lada_junk_on)
		std::set<DWORD> mergedKinds;	// stack keys merged this pass (one merge run a kind a pass)
	};
	std::unordered_map<DWORD, TPlayerBotLada> s_mapPlayerBotLada;
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotLadaHeldOff;	// item id -> not listed again before
	std::unordered_set<DWORD> s_setPlayerBotLadaJunkLines;			// line ids the lada put up as junk (this core)

	struct TPlayerBotLadaCensus
	{
		unsigned int passes = 0, listed = 0, splits = 0, merges = 0, takeNeed = 0, takeReclaim = 0, takeJunk = 0, junkListed = 0;
		unsigned long long listedUnits = 0;
		unsigned int refusedCap = 0, refusedWorld = 0, refusedYang = 0, refusedBudget = 0, refusedBusy = 0, stuck = 0;
		unsigned int tierPasses = 0, tierKinds = 0, tier1 = 0, tier2 = 0, tierEdits = 0, tierLooked = 0;
		unsigned int budgetGranted = 0;
	};
	TPlayerBotLadaCensus s_kPlayerBotLadaCensus;

	// The world's lines, counted once a minute off this core's copy of every shop.
	struct TPlayerBotLadaWorld
	{
		unsigned int botShops = 0, botLines = 0, ladaLines = 0, allLines = 0, maxLines = 0;
		unsigned long long botUnits = 0;
		DWORD maxOwner = 0;
	};
	TPlayerBotLadaWorld s_kPlayerBotLadaWorld;

	void NotePlayerBotLadaHeldOff(DWORD itemid, DWORD now)
	{
		if (!itemid)
			return;
		if (s_mapPlayerBotLadaHeldOff.size() > 20000)
			for (auto it = s_mapPlayerBotLadaHeldOff.begin(); it != s_mapPlayerBotLadaHeldOff.end(); )
				if ((int)(now - it->second) >= 0)
					it = s_mapPlayerBotLadaHeldOff.erase(it);
				else
					++it;
		s_mapPlayerBotLadaHeldOff[itemid] = now + PLAYERBOT_LADA_HOLD_OFF_MS;
	}

	bool IsPlayerBotLadaHeldOff(DWORD itemid, DWORD now)
	{
		auto it = s_mapPlayerBotLadaHeldOff.find(itemid);
		if (it == s_mapPlayerBotLadaHeldOff.end())
			return false;
		if ((int)(now - it->second) < 0)
			return true;
		s_mapPlayerBotLadaHeldOff.erase(it);
		return false;
	}

	// The core's bucket of lada requests (the visit's own bucket, BotOfflineBudget, stays the visit's).
	bool PlayerBotLadaBudget(DWORD now)
	{
		static double s_tokens = 0;
		static DWORD s_at = 0;
		const int rate = GetPlayerBotLadaCfg().rate;
		if (s_at == 0)
		{
			s_at = now ? now : 1;
			s_tokens = rate;
		}
		s_tokens = std::min<double>(rate * 2.0, s_tokens + (double)(now - s_at) * rate / 1000.0);
		s_at = now ? now : 1;
		if (s_tokens < 1.0)
		{
			++s_kPlayerBotLadaCensus.refusedBudget;
			return false;
		}
		s_tokens -= 1.0;
		++s_kPlayerBotLadaCensus.budgetGranted;
		return true;
	}

	// A pos past the visit's pages no line takes, whose every row's first byte (the engine's renewal asks
	// CanPlaceItemOnShopSlot of a BYTE) is off the locked and premium cells of a person's first page.
	int PlayerBotLadaPos(const ikashop::CShopManager::SHOP_HANDLE& shop, int size)
	{
		std::unordered_set<int> used;
		for (const auto& [id, line] : shop->GetItems())
		{
			if (!line)
				continue;
			const int pos = (int)line->GetInfo().pos;
			if (pos < PLAYERBOT_LADA_POS_BASE)
				continue;
			const int h = line->GetTable() ? std::max<int>(1, line->GetTable()->bSize) : 1;
			for (int i = 0; i < h; ++i)
				used.insert(pos + i * SHOP_PLAYER_WIDTH);
		}
		for (int pos = PLAYERBOT_LADA_POS_BASE; pos < PLAYERBOT_LADA_POS_MAX; ++pos)
		{
			bool ok = true;
			for (int i = 0; i < size && ok; ++i)
			{
				const int cell = pos + i * SHOP_PLAYER_WIDTH;
				const BYTE b = (BYTE)cell;
				ok = !used.count(cell) && !(b < SHOP_PLAYER_WIDTH * SHOP_PLAYER_HEIGHT && b % SHOP_PLAYER_WIDTH >= SHOP_PLAYER_PREMIUM_X_START);
			}
			if (ok)
				return pos;
		}
		return -1;
	}

	// The bot's keep of a kind - the visit's keeps - and what of it is over the keep, of this stack.
	int PlayerBotLadaSpare(LPCHARACTER ch, LPITEM item, int& keep)
	{
		keep = 0;
		if (!item)
			return 0;
		const int count = (int)item->GetCount();
		if (!IsPlayerBotLadaStackableOf(item->GetProto()))
			return count;
		int total = 0;
		if (IsPlayerBotCountedSingleGoods(item))
		{
			keep = GetPlayerBotCountedGoodsKeep(ch, item);
			total = CountPlayerBotStallKindUnits(ch, item);
		}
		else
		{
			keep = GetPlayerBotStallBaseKeep(ch, item);
			total = (int)ch->CountSpecifyItem(item->GetVnum());
		}
		return std::max(0, std::min(count, total - keep));
	}

	// Why the bot's items cannot be touched now, or NULL.
	const char* PlayerBotLadaBusy(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || !ch->IsItemLoaded())
			return "loading";
		if (ch->GetExchange() || ch->GetShop() || ch->GetMyShop() || ch->IsOpenSafebox() || ch->IsCubeOpen() || ch->IsBusy())
			return "window";
		if (state.offlineShop.visiting)
			return "visit";
		return NULL;
	}

	// ------------------------------------------------------------------------------------------------ the add
	// One stack of the bag up, past the pages: the engine's add without the board and the distance - ProcessAddItemToShop
	// (the piece into the shop window, the instance gone) and the db core's add, through the bot's journal.
	bool PlayerBotLadaAdd(LPCHARACTER ch, TPlayerBotAIState& state, const ikashop::CShopManager::SHOP_HANDLE& shop, LPITEM item,
			DWORD now, bool junk)
	{
		using namespace playerbot_offline;
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		if (!item || item->GetOwner() != ch || item->IsEquipped() || item->isLocked() || item->GetWindow() != INVENTORY)
			return false;
#ifdef ENABLE_SOULBIND_SYSTEM
		if (item->IsSealed())
			return false;
#endif
		if (IsPlayerBotBuffSetPiece(ch, item))
			return false;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		if (IsPlayerBotSecondSetStored(ch, item))
			return false;
#endif
		if ((int)shop->GetItems().size() >= c.cap)
		{
			++k.refusedCap;
			return false;
		}
		if ((int)s_kPlayerBotLadaWorld.botLines >= c.worldCap)
		{
			++k.refusedWorld;
			return false;
		}
		const int pos = PlayerBotLadaPos(shop, std::max<int>(1, item->GetSize()));
		if (pos < 0)
		{
			++k.refusedCap;
			return false;
		}
		ikashop::TPriceInfo price{};
		{
			int markup = 0;
			const DWORD listing = GetPlayerBotListingPrice(item, GetPlayerBotShopAskingPrice(item), 0, &markup);
			const DWORD floor = GetPlayerBotListingFloor(item);
			price.yang = std::max(listing, floor);
		}
		const long long total = (long long)shop->GetTotalYangValue();
		if (price.yang <= 0 || price.yang >= PLAYERBOT_GOLD_MAX || total >= PLAYERBOT_GOLD_MAX - (long long)price.yang)
		{
			++k.refusedYang;
			PlayerBotLogThrottled("lada_yang_cap", now,
					"PLAYERBOT_LADA: yang cap pid=%u name=%s vnum=%u count=%u price=%lld total=%lld lines=%u",
					ch->GetPlayerID(), ch->GetName(), item->GetVnum(), (unsigned int)item->GetCount(), (long long)price.yang,
					total, (unsigned int)shop->GetItems().size());
			return false;
		}
		// Read while the piece is in hand: the add destroys the instance.
		const DWORD id = item->GetID();
		const DWORD vnum = item->GetVnum();
		const DWORD count = item->GetCount();
		const uint32_t skill = item->GetType() == ITEM_SKILLBOOK ? (uint32_t)item->GetSocket(0) : 0u;
		const uint8_t refine = (uint8_t)item->GetRefineLevel();
		const DWORD pid = ch->GetPlayerID();
		if (!Begin(pid, Add, id, now))
			return false;
		auto& manager = ikashop::GetManager();
		ikashop::TShopItem sitem{};
		manager.ProcessAddItemToShop(sitem, ch, item, (WORD)pos, price);
		item = NULL;
		manager.SendShopAddItemDBPacket(pid, sitem);
		if (!EndCall(pid))
			return false;
		TPlayerBotLada& L = s_mapPlayerBotLada[pid];
		L.opAt = now ? now : 1;
		L.opItem = id;
		// The bookkeeping of a visit's add.
		state.offlineShop.listed[id] = playerbot_offline::ListedLine{ vnum, skill, now, refine };
		const long long globalNow = (long long)get_global_time();
		DBManager::instance().Query(
				"REPLACE INTO ikashop_item_meta (item_id, owner, since, ap_anchor, ap_pct, ap_hours, ap_min) VALUES (%u, %u, %lld, %lld, 0, 0, 0)",
				id, pid, globalNow, globalNow);
		s_mapBotOfflineLineSince[id] = globalNow;
		AddPlayerBotMarketSupply(vnum, (WORD)std::min<DWORD>(count, 65535), shop->GetSpawn().map);
		NotePlayerBotCappedLineOnCounter(vnum, (int)count);
		NotePlayerBotPetMatListed(ch, vnum, (int)count);
		QueuePlayerBotListingEvent(id, pid, vnum, count, per::EVENT_LIST_ADD, (long long)price.yang, 0, "", 0, 0, 0);
		if (junk)
		{
			s_setPlayerBotLadaJunkLines.insert(id);
			++k.junkListed;
		}
		++k.listed;
		k.listedUnits += count;
		PlayerBotLogThrottled("lada_list", now,
				"PLAYERBOT_LADA: list pid=%u name=%s item=%u vnum=%u count=%u price=%lld pos=%d lines=%u ch=%u stand_ch=%u junk=%d",
				pid, ch->GetName(), id, vnum, (unsigned int)count, (long long)price.yang, pos,
				(unsigned int)shop->GetItems().size() + 1, (unsigned int)g_bChannel, (unsigned int)shop->GetSpawn().channel,
				junk ? 1 : 0);
		return true;
	}

	// A line home from wherever the bot is (the visit's BotOfflineTakeOff and its bookkeeping, the remote remove).
	bool PlayerBotLadaTakeBack(LPCHARACTER ch, TPlayerBotAIState& state, DWORD itemid, DWORD now, const char* why)
	{
		s_bPlayerBotLadaRemote = true;
		const bool ok = BotOfflineTakeOff(ch, state, itemid, 0, now, why);
		s_bPlayerBotLadaRemote = false;
		if (ok)
		{
			TPlayerBotLada& L = s_mapPlayerBotLada[ch->GetPlayerID()];
			L.opAt = now ? now : 1;
			L.opItem = itemid;
			s_setPlayerBotLadaJunkLines.erase(itemid);
		}
		return ok;
	}

	// ------------------------------------------------------------------------------------------------ the pass
	void StartPlayerBotLadaPass(LPCHARACTER ch, TPlayerBotAIState& state, const ikashop::CShopManager::SHOP_HANDLE& shop,
			TPlayerBotLada& L, DWORD now)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		L.active = true;
		L.ops = 0;
		L.passUntil = now + PLAYERBOT_LADA_PASS_MAX_MS;
		L.need.clear();
		L.junkStale.clear();
		L.mergedKinds.clear();
		++s_kPlayerBotLadaCensus.passes;
		// The extra inventory's goods into the bag (its own gap of five minutes), so the scan sees them.
		PlayerBotEkwFetchGoods(ch, "lada");
		// 1. a piece to wear (the visit's own rule).
		long long gain = 0;
		L.reclaim = BotOfflineReclaimLine(ch, state, shop, now, gain);
		// 2. the keep's lines, and the junk's unsold ones.
		for (const auto& [id, line] : shop->GetItems())
		{
			if (!line || !line->GetTable())
				continue;
			const DWORD vnum = line->GetInfo().vnum;
			if (c.junk && s_setPlayerBotLadaJunkLines.count(id) &&
					BotOfflineLineAgeMs(state, id, vnum, now) >= PLAYERBOT_LADA_JUNK_STALE_MS)
			{
				L.junkStale.push_back(id);
				continue;
			}
			if (!IsPlayerBotLadaStackableOf(line->GetTable()) || !IsPlayerBotLadaKindOf(vnum, line->GetTable()))
				continue;
			LPITEM preview = BotOfflinePreview(*line);
			if (!preview)
				continue;
			// What the bot holds of the kind (the bag and the extra inventory; the line is not the bot's item) against its keep.
			const bool counted = IsPlayerBotCountedSingleGoods(preview);
			const int keep = counted ? GetPlayerBotCountedGoodsKeep(ch, preview) : GetPlayerBotStallBaseKeep(ch, preview);
			const int have = counted ? CountPlayerBotStallKindUnits(ch, preview) : (int)ch->CountSpecifyItem(vnum);
			M2_DELETE(preview);
			if (keep > 0 && have < keep)
				L.need.push_back(id);
		}
	}

	void EndPlayerBotLadaPass(LPCHARACTER ch, TPlayerBotLada& L, DWORD now, const char* why)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		const DWORD interval = (DWORD)c.intervalMin * 60000U;
		L.active = false;
		L.nextPass = now + interval * 8 / 10 + (DWORD)number(0, (int)(interval * 4 / 10));
		if (L.nextPass == 0)
			L.nextPass = 1;
		if (L.ops > 0)
			PlayerBotLogThrottled("lada_pass", now, "PLAYERBOT_LADA: pass pid=%u name=%s ops=%d why=%s next_min=%u",
					ch->GetPlayerID(), ch->GetName(), L.ops, why, (unsigned int)((L.nextPass - now) / 60000U));
	}

	// One step of the pass: true when a request went to the db core.
	bool StepPlayerBotLadaPass(LPCHARACTER ch, TPlayerBotAIState& state, const ikashop::CShopManager::SHOP_HANDLE& shop,
			TPlayerBotLada& L, DWORD now)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		const auto& items = shop->GetItems();
		// 1. a piece to wear.
		if (L.reclaim)
		{
			const DWORD id = L.reclaim;
			L.reclaim = 0;
			if (items.count(id))
			{
				s_bPlayerBotLadaRemote = true;
				const bool ok = BotOfflineReclaim(ch, state, id, 1, now);
				s_bPlayerBotLadaRemote = false;
				if (ok)
				{
					L.opAt = now ? now : 1;
					L.opItem = id;
					++k.takeReclaim;
					return true;
				}
			}
		}
		// 2. the keep's lines, the junk's unsold ones.
		while (!L.need.empty())
		{
			const DWORD id = L.need.back();
			L.need.pop_back();
			if (items.count(id) && PlayerBotLadaTakeBack(ch, state, id, now, "lada_need"))
			{
				++k.takeNeed;
				return true;
			}
		}
		while (!L.junkStale.empty())
		{
			const DWORD id = L.junkStale.back();
			L.junkStale.pop_back();
			if (items.count(id) && PlayerBotLadaTakeBack(ch, state, id, now, "lada_junk_stale"))
			{
				NotePlayerBotLadaHeldOff(id, now);	// for the merchant
				++k.takeJunk;
				return true;
			}
		}
		// 3. the bag's goods, best first; a kind with a short line on the counter merges first.
		MergePlayerBotStacks(ch, 8);
		std::vector<std::pair<int, WORD> > scored;
		s_bPlayerBotLadaScan = true;
		CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state), 0, true);
		s_bPlayerBotLadaScan = false;
		const int bagFree = CountPlayerBotFreeInventoryCells(ch);
		auto tryItem = [&](LPITEM item, bool junk) -> int {	// 1 sent, 0 next, -1 stop
			if (!item || !IsPlayerBotLadaKindItem(item) || IsPlayerBotEkwHeld(item, now) || IsPlayerBotLadaHeldOff(item->GetID(), now))
				return 0;
			int keep = 0;
			const int take = PlayerBotLadaSpare(ch, item, keep);
			if (take <= 0)
				return 0;
			if (IsPlayerBotLadaStackableOf(item->GetProto()))
			{
				const DWORD key = BotOfflineStackKey(item);
				if (!L.mergedKinds.count(key))
				{
					// The counter's short line of this stack, smallest first, comes home to be poured in.
					DWORD mergeId = 0;
					DWORD mergeCount = 0;
					for (const auto& [id, line] : items)
						if (line && (int)line->GetInfo().count < (int)item->GetMaxStack() && PlayerBotLadaLineStacksWith(*line, item) &&
								(!mergeId || line->GetInfo().count < mergeCount))
						{
							mergeId = id;
							mergeCount = line->GetInfo().count;
						}
					if (mergeId && bagFree > PLAYERBOT_SHOP_SPLIT_KEEP_FREE_CELLS && items.size() > 1 &&
							PlayerBotLadaTakeBack(ch, state, mergeId, now, "lada_merge"))
					{
						++k.merges;
						PlayerBotLogThrottled("lada_merge", now,
								"PLAYERBOT_LADA: merge pid=%u name=%s line=%u vnum=%u line_count=%u bag_spare=%d",
								ch->GetPlayerID(), ch->GetName(), mergeId, item->GetVnum(), (unsigned int)mergeCount, take);
						return 1;
					}
					// No short line, or it cannot come home now: the stack goes up as it is.
					L.mergedKinds.insert(key);
				}
			}
			LPITEM line = item;
			if (take < (int)item->GetCount())
			{
				// The spare cut off its stack; the keep stays where it is.
				if (bagFree <= PLAYERBOT_SHOP_SPLIT_KEEP_FREE_CELLS)
					return 0;
				const int to = ch->GetEmptyInventory(item->GetSize());
				if (to < 0 || !ch->MoveItem(TItemPos(INVENTORY, item->GetCell()), TItemPos(INVENTORY, (WORD)to), take))
					return 0;
				line = ch->GetInventoryItem((WORD)to);
				if (!line || (int)line->GetCount() != take)
					return 0;
				++k.splits;
			}
			if (PlayerBotLadaAdd(ch, state, shop, line, now, junk))
				return 1;
			if ((int)shop->GetItems().size() >= c.cap || (int)s_kPlayerBotLadaWorld.botLines >= c.worldCap)
				return -1;
			return 0;
		};
		for (const auto& [score, cell] : scored)
		{
			const int r = tryItem(ch->GetInventoryItem(cell), false);
			if (r > 0)
				return true;
			if (r < 0)
				return false;
		}
		// The junk (m2_bot_lada_junk_on): what only the merchant takes, behind the goods, under its cap.
		if (c.junk)
		{
			int junkLines = 0;
			for (const auto& [id, line] : items)
				if (s_setPlayerBotLadaJunkLines.count(id))
					++junkLines;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && junkLines < PLAYERBOT_LADA_JUNK_LINES; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->IsEquipped() || item->isLocked())
					continue;
				s_bPlayerBotLadaScan = true;
				const bool goods = ScorePlayerBotShopStockRules(ch, item, true, false) <= 0 ||
						ScorePlayerBotShopStock(ch, item, false, false) > 0;
				s_bPlayerBotLadaScan = false;
				if (goods)	// nothing the merchant takes, or goods the scan above had
					continue;
				const int r = tryItem(item, true);
				if (r > 0)
					return true;
				if (r < 0)
					return false;
			}
		}
		// 4. two short lines of a kind with nothing of it in the bag: the smaller comes home.
		{
			std::map<std::pair<DWORD, long>, std::pair<int, std::pair<DWORD, DWORD> > > shortLines;	// (vnum, socket0) -> lines, smallest
			for (const auto& [id, line] : items)
			{
				if (!line || !line->GetTable() || !IsPlayerBotLadaStackableOf(line->GetTable()) ||
						!IsPlayerBotLadaKindOf(line->GetInfo().vnum, line->GetTable()) ||
						line->GetInfo().count >= line->GetTable()->dwMaxStack)
					continue;
				auto& e = shortLines[std::make_pair(line->GetInfo().vnum, (long)line->GetInfo().alSockets[0])];
				++e.first;
				if (!e.second.first || line->GetInfo().count < e.second.second)
					e.second = std::make_pair(id, (DWORD)line->GetInfo().count);
			}
			for (const auto& [kind, e] : shortLines)
				if (e.first >= 2 && !L.mergedKinds.count(kind.first) && bagFree > PLAYERBOT_SHOP_SPLIT_KEEP_FREE_CELLS &&
						items.size() > 2)
				{
					L.mergedKinds.insert(kind.first);
					if (PlayerBotLadaTakeBack(ch, state, e.second.first, now, "lada_merge"))
					{
						++k.merges;
						return true;
					}
				}
		}
		return false;
	}

	// The lada's own request unanswered for a minute: the db core refused it (a line a purchase held locked, a shop
	// gone) and answers nobody then. A remove asks again safely (the db core refuses a line it no longer has), and an
	// add cannot be asked twice (the piece left the bag) - so the journal lets it go, logged.
	void ResolvePlayerBotLadaStuck(LPCHARACTER ch, TPlayerBotLada& L, DWORD now)
	{
		if (!L.opItem)
			return;
		auto it = playerbot_offline::requests.find(ch->GetPlayerID());
		if (it == playerbot_offline::requests.end() || it->second.item != L.opItem)
		{
			L.opItem = 0;
			return;
		}
		if (it->second.done || now - L.opAt < PLAYERBOT_LADA_STUCK_MS)
			return;
		++s_kPlayerBotLadaCensus.stuck;
		PlayerBotLogThrottled("lada_stuck", now,
				"PLAYERBOT_LADA: stuck request let go pid=%u name=%s op=%u item=%u sent=%d age_s=%u",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)it->second.op, it->second.item, it->second.sent ? 1 : 0,
				(unsigned int)((now - L.opAt) / 1000U));
		playerbot_offline::requests.erase(it);
		L.opItem = 0;
	}

	// ------------------------------------------------------------------------------------------------ the core
	struct TPlayerBotLadaTierEdit
	{
		DWORD owner, item;
	};
	std::deque<TPlayerBotLadaTierEdit> s_dequePlayerBotLadaTierEdits;
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotLadaTierOwner;	// tier line -> its owner (the edit back after it)

	void CountPlayerBotLadaWorld()
	{
		TPlayerBotLadaWorld w;
		CPlayerBotManager& bots = CPlayerBotManager::instance();
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop)
				continue;
			const unsigned int lines = (unsigned int)shop->GetItems().size();
			w.allLines += lines;
			if (!bots.IsRegisteredBotPID(shop->GetOwnerPID()))
				continue;
			++w.botShops;
			w.botLines += lines;
			if (lines > w.maxLines)
			{
				w.maxLines = lines;
				w.maxOwner = shop->GetOwnerPID();
			}
			for (const auto& [id, line] : shop->GetItems())
				if (line)
				{
					w.botUnits += line->GetInfo().count;
					if ((int)line->GetInfo().pos >= PLAYERBOT_LADA_POS_BASE)
						++w.ladaLines;
				}
		}
		s_kPlayerBotLadaWorld = w;
	}

	// The glut's tiers (playerbot_market_clearing.h): on the shop channel's cores, every PLAYERBOT_LADA_TIER_MS.
	void RankPlayerBotLadaTiers(DWORD now)
	{
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		std::unordered_map<DWORD, WORD> tiers;
		std::unordered_map<DWORD, DWORD> owners;
		if (s_bPlayerBotLadaTiers && g_bChannel == playerbot_channel_rules::SHOP_CHANNEL)
		{
			std::set<DWORD> glut;
			for (const auto& [vnum, kind] : s_mapPlayerBotClear)
				if (kind.clearUnit != 0)
					glut.insert(vnum);
			if (!glut.empty())
			{
				struct TLine { unsigned long long unitMilli; DWORD id, count, owner; };
				std::map<DWORD, std::vector<TLine> > byKind;
				for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
				{
					if (!shop || shop->GetDuration() == 0 || (int)shop->GetSpawn().channel != playerbot_channel_rules::SHOP_CHANNEL)
						continue;
					for (const auto& [id, line] : shop->GetItems())
					{
						if (!line || !glut.count(line->GetInfo().vnum) || line->GetInfo().count == 0)
							continue;
						const long long yang = (long long)line->GetPrice().GetTotalYangAmount();
						if (yang <= 0)
							continue;
						byKind[line->GetInfo().vnum].push_back(TLine{ (unsigned long long)yang * 1000ULL / line->GetInfo().count, id,
								(DWORD)line->GetInfo().count, shop->GetOwnerPID() });
					}
				}
				for (auto& [vnum, lines] : byKind)
				{
					std::sort(lines.begin(), lines.end(), [](const TLine& a, const TLine& b) {
						return a.unitMilli != b.unitMilli ? a.unitMilli < b.unitMilli : a.id < b.id; });
					unsigned long long units = 0;
					for (const TLine& l : lines)
						units += l.count;
					if (units == 0)
						continue;
					++k.tierKinds;
					unsigned long long before = 0;
					for (const TLine& l : lines)
					{
						const unsigned long long share = before * 1000ULL / units;
						before += l.count;
						if (share >= 200)
							break;
						tiers[l.id] = share < 100 ? 950 : 970;
						owners[l.id] = l.owner;
						if (share < 100)
							++k.tier1;
						else
							++k.tier2;
					}
				}
			}
		}
		// The bot lines of the stands this core hosts whose tier came or went (or stays: the clearing ask moves) are
		// edited to their target.
		CPlayerBotManager& bots = CPlayerBotManager::instance();
		auto queue = [&](DWORD id, DWORD owner) {
			if (!bots.IsRegisteredBotPID(owner) || IsPlayerBotSidekickPID(owner))
				return;
			auto shop = ikashop::GetManager().GetShopByOwnerID(owner);
			if (!shop || (int)shop->GetSpawn().channel != (int)g_bChannel || !IsPlayerBotMapHostedHere(shop->GetSpawn().map))
				return;
			s_dequePlayerBotLadaTierEdits.push_back(TPlayerBotLadaTierEdit{ owner, id });
		};
		s_dequePlayerBotLadaTierEdits.clear();
		for (const auto& [id, owner] : owners)
			queue(id, owner);
		for (const auto& [id, owner] : s_mapPlayerBotLadaTierOwner)
			if (!owners.count(id))
				queue(id, owner);
		s_mapPlayerBotLadaTier.swap(tiers);
		s_mapPlayerBotLadaTierOwner.swap(owners);
		++k.tierPasses;
		(void)now;
	}

	void PumpPlayerBotLadaTierEdits(DWORD now)
	{
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		auto& manager = ikashop::GetManager();
		for (int n = 0; n < PLAYERBOT_LADA_TIER_EDITS_PER_S && !s_dequePlayerBotLadaTierEdits.empty(); )
		{
			const TPlayerBotLadaTierEdit e = s_dequePlayerBotLadaTierEdits.front();
			s_dequePlayerBotLadaTierEdits.pop_front();
			auto shop = manager.GetShopByOwnerID(e.owner);
			auto line = shop ? shop->GetItem(e.item) : nullptr;
			if (!line || shop->GetDuration() == 0 || shop->IsEditMode() || playerbot_offline::requests.count(e.owner))
				continue;
			LPITEM preview = BotOfflinePreview(*line);
			if (!preview)
				continue;
			++k.tierLooked;
			TPlayerBotPricingKeeper pricing(e.owner);
			TPlayerBotPriceTraceScope priceTrace;
			std::map<uint32_t, playerbot_offline::ListedLine> scratch;
			TPlayerBotAIStateMap::iterator keeper = s_mapPlayerBotAIStates.find(e.owner);
			std::map<uint32_t, playerbot_offline::ListedLine>* listed =
					keeper != s_mapPlayerBotAIStates.end() ? &keeper->second.offlineShop.listed : &scratch;
			const TBotOfflineRepriceTarget target = BotOfflineRepriceTarget(preview, e.item, listed, now, priceTrace, false);
			const DWORD vnum = preview->GetVnum();
			const long long count = preview->GetCount();
			M2_DELETE(preview);
			const long long asked = (long long)line->GetPrice().yang;
			if (!IsPlayerBotRepriceWorthEdit(asked, target.price, target.floor))
				continue;
			ikashop::TPriceInfo price{};
			price.yang = target.price;
			manager.SendShopEditItemDBPacket(e.owner, e.item, price);
			QueuePlayerBotListingEvent(e.item, e.owner, vnum, count, per::EVENT_REPRICE, target.price, asked, "", 0, 0, 0);
			++k.tierEdits;
			++n;
		}
	}

	void LogPlayerBotLadaCensus(DWORD now)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		const TPlayerBotLadaWorld& w = s_kPlayerBotLadaWorld;
		unsigned int active = 0, waiting = 0;
		for (const auto& [pid, L] : s_mapPlayerBotLada)
			(L.active ? active : waiting)++;
		sys_log(0, "PLAYERBOT_LADA: census on=%d tiers=%d ch=%u bot_shops=%u bot_lines=%u bot_units=%llu lada_lines=%u "
				"world_lines=%u (a search walks these) max_lines=%u max_owner=%u cap=%d world_cap=%d bots_here=%u passing=%u "
				"passes=%u listed=%u listed_units=%llu splits=%u merges=%u take_need=%u take_reclaim=%u take_junk=%u junk_listed=%u "
				"refused_cap=%u refused_world=%u refused_yang=%u refused_budget=%u remote_refused=%u stuck=%u budget_granted=%u "
				"sold_lines=%llu sold_units=%llu sold_parts=%llu sold_yang=%lld tier_passes=%u tier_kinds=%u tier1_lines=%u "
				"tier2_lines=%u tier_now=%u tier_looked=%u tier_edits=%u tier_priced=%u edits_queued=%u",
				c.on ? 1 : 0, c.tiers ? 1 : 0, (unsigned int)g_bChannel, w.botShops, w.botLines, w.botUnits, w.ladaLines, w.allLines,
				w.maxLines, w.maxOwner, c.cap, c.worldCap, waiting + active, active, k.passes, k.listed, k.listedUnits, k.splits,
				k.merges, k.takeNeed, k.takeReclaim, k.takeJunk, k.junkListed, k.refusedCap, k.refusedWorld, k.refusedYang,
				k.refusedBudget, s_uPlayerBotLadaRemoteRefused, k.stuck, k.budgetGranted,
				(unsigned long long)playerbot_offline::ladaSoldLines, (unsigned long long)playerbot_offline::ladaSoldUnits,
				(unsigned long long)playerbot_offline::ladaSoldParts, playerbot_offline::ladaSoldYang, k.tierPasses, k.tierKinds,
				k.tier1, k.tier2, (unsigned int)s_mapPlayerBotLadaTier.size(), k.tierLooked, k.tierEdits,
				s_uPlayerBotLadaTierPriced, (unsigned int)s_dequePlayerBotLadaTierEdits.size());
		// The kinds of the most bot lines: lines, units, bots, the lada's lines of them, the tier lines.
		struct TKind { unsigned int lines = 0, lada = 0, owners = 0, tiered = 0; unsigned long long units = 0; DWORD lastOwner = 0; };
		std::map<DWORD, TKind> kinds;
		CPlayerBotManager& bots = CPlayerBotManager::instance();
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || !bots.IsRegisteredBotPID(shop->GetOwnerPID()))
				continue;
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line)
					continue;
				TKind& e = kinds[line->GetInfo().vnum];
				++e.lines;
				e.units += line->GetInfo().count;
				if ((int)line->GetInfo().pos >= PLAYERBOT_LADA_POS_BASE)
					++e.lada;
				if (s_mapPlayerBotLadaTier.count(id))
					++e.tiered;
				if (e.lastOwner != shop->GetOwnerPID())
				{
					e.lastOwner = shop->GetOwnerPID();
					++e.owners;
				}
			}
		}
		std::vector<std::pair<unsigned int, DWORD> > ranked;
		for (const auto& [vnum, e] : kinds)
			ranked.push_back(std::make_pair(e.lines, vnum));
		std::sort(ranked.rbegin(), ranked.rend());
		for (size_t i = 0; i < ranked.size() && i < PLAYERBOT_LADA_CENSUS_KINDS; ++i)
		{
			const TKind& e = kinds[ranked[i].second];
			sys_log(0, "PLAYERBOT_LADA: kind vnum=%u lines=%u units=%llu bots=%u lada_lines=%u tier_lines=%u clear_unit=%u",
					ranked[i].second, e.lines, e.units, e.owners, e.lada, e.tiered, GetPlayerBotClearingUnit(ranked[i].second));
		}
		s_kPlayerBotLadaCensus = TPlayerBotLadaCensus();
		playerbot_offline::ladaSoldLines = playerbot_offline::ladaSoldUnits = playerbot_offline::ladaSoldParts = 0;
		playerbot_offline::ladaSoldYang = 0;
		s_uPlayerBotLadaTierPriced = 0;
		s_uPlayerBotLadaRemoteRefused = 0;
		(void)now;
	}

	// The core's clocks, from any bot's tick.
	void ManagePlayerBotLadaCore(DWORD now)
	{
		static DWORD s_dwAt = 0, s_dwWorld = 0, s_dwTier = 0, s_dwCensus = 0;
		if (s_dwAt != 0 && now - s_dwAt < 1000)
			return;
		s_dwAt = now ? now : 1;
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		if (s_dwWorld == 0 || now - s_dwWorld >= 60000)
		{
			s_dwWorld = now ? now : 1;
			CountPlayerBotLadaWorld();
		}
		// The tiers on (and off: the lines edited back once), on the shop channel's cores.
		if (g_bChannel == playerbot_channel_rules::SHOP_CHANNEL &&
				(s_dwTier == 0 || now - s_dwTier >= PLAYERBOT_LADA_TIER_MS) &&
				(c.tiers || !s_mapPlayerBotLadaTier.empty() || !s_mapPlayerBotLadaTierOwner.empty()))
		{
			s_dwTier = now ? now : 1;
			RankPlayerBotLadaTiers(now);
		}
		if (!s_dequePlayerBotLadaTierEdits.empty())
			PumpPlayerBotLadaTierEdits(now);
		if (s_dwCensus == 0)
			s_dwCensus = now ? now : 1;
		else if (now - s_dwCensus >= PLAYERBOT_LADA_CENSUS_MS)
		{
			s_dwCensus = now ? now : 1;
			LogPlayerBotLadaCensus(now);
		}
	}

	// The bot's tick (playerbot_manager.cpp, ahead of the offline service): never claims it.
	void ManagePlayerBotLada(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		ManagePlayerBotLadaCore(now);
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		if (!c.on || !ch || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotSidekickPID(pid) || IsPlayerBotSidekickServing(ch))
			return;
		auto shop = ikashop::GetManager().GetShopByOwnerID(pid);
		if (!shop)
			return;
		TPlayerBotLada& L = s_mapPlayerBotLada[pid];
		ResolvePlayerBotLadaStuck(ch, L, now);
		if (L.nextPass == 0)
		{
			// The first pass spread over the interval by the bot's id, so a core's bots do not all come at once.
			const DWORD interval = (DWORD)c.intervalMin * 60000U;
			L.nextPass = now + 60000U + (DWORD)(PlayerBotNavHash(pid ^ 0x4C414441U) % interval);
			return;
		}
		if (!L.active && (int)(now - L.nextPass) < 0)
			return;
		if (BotOfflinePoll(ch, now))	// a request of the bot in flight (the lada's or the visit's): its answer first
			return;
		if (shop->GetDuration() == 0 || shop->GetItems().empty() ||
				(!c.xch && (int)shop->GetSpawn().channel != (int)g_bChannel))
		{
			EndPlayerBotLadaPass(ch, L, now, shop->GetDuration() == 0 ? "stand_closed" : "channel");
			return;
		}
		if (PlayerBotLadaBusy(ch, state))
		{
			++s_kPlayerBotLadaCensus.refusedBusy;
			if (L.active && (int)(now - L.passUntil) >= 0)
				EndPlayerBotLadaPass(ch, L, now, "busy");
			return;
		}
		if (!L.active)
			StartPlayerBotLadaPass(ch, state, shop, L, now);
		if (L.ops >= c.passOps || (int)(now - L.passUntil) >= 0)
		{
			EndPlayerBotLadaPass(ch, L, now, L.ops >= c.passOps ? "ops" : "time");
			return;
		}
		if (!PlayerBotLadaBudget(now))
			return;
		if (StepPlayerBotLadaPass(ch, state, shop, L, now))
			++L.ops;
		else
			EndPlayerBotLadaPass(ch, L, now, "done");
	}
}

#endif
