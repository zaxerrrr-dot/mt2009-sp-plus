#ifndef __INC_METIN2_PLAYERBOT_LADA_H__
#define __INC_METIN2_PLAYERBOT_LADA_H__

#include <deque>
#include <unordered_set>
#include "ikashop_lada_view.h"	// MT2009_PLUS_BOT_LADA_VIEW_V1: the engine's window bound and its counters (server-patches/ladaview)

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
// m2_bot_lada_cap (0: none - MT2009_PLUS_BOT_LADA_NOCAP_V1; the window's packet is bounded in the engine,
// server-patches/ladaview, ikashop_lada_view.h), m2_bot_lada_world_cap (120000 lines of every shop a search walks,
// PLAYERBOT_LADA_WORLD_CAP_DEFAULT), the bot's 2 bn per counter.
// The lada's kinds (IsPlayerBotLadaKindItem) are the ordinary goods; the dragon stones, soul stones, energy shards,
// Cors, Materialy Rzemieslnicze, Moonlight chests, horse medals, SM coupons, refine scrolls, mission books, rare
// goods, belts, sashes, talismans, costumes, potions and the low gear under its cap stay with the visit's own rules -
// the visit no longer lists, cuts or restacks the lada's kinds while the lada is on.
// MT2009_PLUS_BOT_LADA_FISH_V1 (10 November 2026): the fish family (alive, dead, grilled - the EXP food too) and
// Baek-Go's potions are lada kinds over the cheap floor (m2_bot_lada_min_cheap, 1000 yang of the proto's gold a unit);
// no basic shop potion (anything an NPC sells, the packed green / purple, the personal buff reserve), and no weapon or
// armour piece whose reference ask a unit is under m2_bot_lada_min_gear (50 000) - those keep the old handling. A fish
// keeps what the bot uses of it (GetPlayerBotLadaFishKeep, playerbot_economy.h); census4 counts them.
//
// The price: new lines at the visit's listing price (GetPlayerBotListingPrice, the floor) - or, a glutted kind, the
// tier the line ranks into (MT2009_PLUS_BOT_LADA_TIER_XCH_V1, any channel); the glut's tiers
// (playerbot_market_clearing.h, m2_bot_lada_price_off 1: the old clearing of every line) - the glutted kinds and their
// clearing asks published by one shop-channel core (player.playerbot_lada_tier) and read by every other, every core of
// every channel ranks every line of each glutted kind by its unit price (every PLAYERBOT_LADA_TIER_RANK_MS), the
// cheapest 10 % of the units 950 permille, the next 10 % 970, and every PLAYERBOT_LADA_TIER_MS edits the bot lines of
// the stands this core hosts to BotOfflineRepriceTarget (which applies the tier) - PLAYERBOT_LADA_TIER_EDITS_PER_S a
// second. The safebox (MT2009_PLUS_BOT_LADA_BOX_V1, below): a stand keeper's box gives the lada its goods, all but the
// spare gear and the keeps.
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
	// MT2009_PLUS_BOT_LADA_VIEW_V1: the lada stands where the engine's window bound stops showing lines.
	static_assert(PLAYERBOT_LADA_POS_BASE == ikashop_lada_view::VISIBLE_CELLS, "the lada starts past the window's pages");
	const size_t PLAYERBOT_LADA_CENSUS_KINDS = 8;

	// MT2009_PLUS_BOT_LADA_NOCAP_V1 (the owner, 8 November 2026: "Nie limituj pozycji na bota"): no number of lines a
	// bot - m2_bot_lada_cap 0 (the default) is no cap, a value over 0 caps it again (20..60000). What the cap guarded is
	// guarded in the engine now (server-patches/ladaview, ikashop_lada_view.h): the stand's window carries only the
	// lines of its pages, whatever the counter holds. The world's cap stays, for the searches' walk: it counts every
	// line of every shop this core's copy holds (a person's too - the search walks them all), default
	// PLAYERBOT_LADA_WORLD_CAP_DEFAULT.
	// The world's cap: the Dom Towarowy's fill and the filter search walk every line of the copy, a name match each
	// (MatchItemName lowers the name into a new string). Measured 8 November 2026 on vps1 (Xeon E-2236, g++ -m32 -O2,
	// the engine's walk rebuilt - std::map of shops, std::map of lines, the proto's unordered_map, the lowered name, the
	// 113-byte result and the 6000-result trim): 12 086 lines (the test world's now) 2.4-2.9 ms, 60 000 13-16 ms,
	// 100 000 22-30 ms, 150 000 31-42 ms, 200 000 43-53 ms - 0.20-0.30 us a line on a quiet core. With the author's
	// 0.4 us a line for a busy core's cold caches, 120 000 lines walk in ~48 ms: the search stays under 50 ms.
	const int PLAYERBOT_LADA_WORLD_CAP_DEFAULT = 120000;

	struct TPlayerBotLadaCfg
	{
		bool on, tiers, xch, junk, box;
		int intervalMin, cap, worldCap, rate, passOps, boxStacks, boxRate, boxGapMin, floorPct;
		int minCheap, minGear;	// MT2009_PLUS_BOT_LADA_FISH_V1
		TPlayerBotLadaCfg() : on(true), tiers(true), xch(true), junk(false), box(true), intervalMin(30), cap(0),
				worldCap(PLAYERBOT_LADA_WORLD_CAP_DEFAULT), rate(6), passOps(24), boxStacks(12), boxRate(120), boxGapMin(30),
				floorPct(90), minCheap(1000), minGear(50000) {}
	};
	TPlayerBotLadaCfg s_kPlayerBotLadaCfg;
	unsigned int s_uPlayerBotLadaGearFloorRefused = 0;	// MT2009_PLUS_BOT_LADA_FISH_V1: gear under m2_bot_lada_min_gear asked

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
			c.box = c.on && q.GetEventFlag("m2_bot_lada_box_off") == 0;	// MT2009_PLUS_BOT_LADA_BOX_V1
			auto value = [&q](const char* flag, int def, int lo, int hi) {
				const int v = q.GetEventFlag(flag);
				return v <= 0 ? def : std::max(lo, std::min(hi, v));
			};
			c.intervalMin = value("m2_bot_lada_min", 30, 5, 240);
			c.cap = value("m2_bot_lada_cap", 0, 20, PLAYERBOT_LADA_POS_MAX);	// MT2009_PLUS_BOT_LADA_NOCAP_V1: 0 no cap
			c.worldCap = value("m2_bot_lada_world_cap", PLAYERBOT_LADA_WORLD_CAP_DEFAULT, 1000, 400000);
			c.rate = value("m2_bot_lada_rate", 6, 1, 50);
			c.passOps = value("m2_bot_lada_pass_ops", 24, 1, 200);
			c.boxStacks = value("m2_bot_lada_box_stacks", 12, 1, 90);		// MT2009_PLUS_BOT_LADA_BOX_V1: stacks a visit
			c.boxRate = value("m2_bot_lada_box_rate", 120, 1, 2000);		// stacks a minute, a core
			c.boxGapMin = value("m2_bot_lada_box_gap_min", 30, 5, 720);	// a bot's visits for it
			// MT2009_PLUS_BOT_LADA_FIX_V1: the clearing ask never under this percent of the normal price (50..100)
			c.floorPct = value("m2_bot_market_floor_pct", 90, 50, 100);
			s_iPlayerBotMarketFloorPct = c.floorPct;
			// MT2009_PLUS_BOT_LADA_FISH_V1: the lada's value floors - a fish or a potion by its proto's gold a unit
			// (1..1000000, default 1000), a weapon or an armour piece by its reference ask a unit (1..100000000, default
			// 50 000). Under them the item keeps its old handling (the merchant, its use, the visit's pages).
			c.minCheap = value("m2_bot_lada_min_cheap", 1000, 1, 1000000);
			c.minGear = value("m2_bot_lada_min_gear", 50000, 1, 100000000);
			s_iPlayerBotLadaMinCheap = c.minCheap;
			s_iPlayerBotLadaMinGear = c.minGear;
			s_bPlayerBotLadaTiers = c.tiers;
			if (was.on != c.on || was.tiers != c.tiers || was.xch != c.xch || was.junk != c.junk || was.intervalMin != c.intervalMin ||
					was.cap != c.cap || was.worldCap != c.worldCap || was.rate != c.rate || was.passOps != c.passOps ||
					was.box != c.box || was.boxStacks != c.boxStacks || was.boxRate != c.boxRate || was.boxGapMin != c.boxGapMin ||
					was.floorPct != c.floorPct || was.minCheap != c.minCheap || was.minGear != c.minGear)
				sys_log(0, "PLAYERBOT_LADA: config on=%d tiers=%d cross_channel=%d junk=%d interval_min=%d cap=%d (0: none) world_cap=%d rate=%d "
						"pass_ops=%d box=%d box_stacks=%d box_rate=%d box_gap_min=%d market_floor_pct=%d min_cheap=%d min_gear=%d",
						c.on ? 1 : 0, c.tiers ? 1 : 0, c.xch ? 1 : 0, c.junk ? 1 : 0, c.intervalMin, c.cap, c.worldCap, c.rate,
						c.passOps, c.box ? 1 : 0, c.boxStacks, c.boxRate, c.boxGapMin, c.floorPct, c.minCheap, c.minGear);
		}
		return s_kPlayerBotLadaCfg;
	}

	bool IsPlayerBotLadaOn()
	{
		return GetPlayerBotLadaCfg().on;
	}

	// ------------------------------------------------------------------------------------------------ the kinds
	// MT2009_PLUS_BOT_LADA_FISH_V1: a potion - ITEM_POTION, or ITEM_USE drunk (USE_POTION / _NODELAY / _CONTINUE).
	bool IsPlayerBotLadaPotionKindOf(const TItemTable* t)
	{
		return t && (t->bType == ITEM_POTION || (t->bType == ITEM_USE && (t->bSubType == USE_POTION ||
				t->bSubType == USE_POTION_NODELAY || t->bSubType == USE_POTION_CONTINUE)));
	}

	// MT2009_PLUS_BOT_LADA_FISH_V1: the potions the lada carries (the fish family aside, IsPlayerBotLadaFishOf) -
	// Baek-Go's juices, waters and mixtures over the cheap floor (m2_bot_lada_min_cheap, the proto's gold a unit).
	// Never a basic shop potion: nothing an NPC's shop sells (the reds and blues 27001-27008, the General Store's
	// green and purple, Baek-Go's sold waters), the green / purple mixtures in their packs (the visit's rule), the
	// personal buff reserve (27101 / 27104), the withdrawn ones.
	bool IsPlayerBotLadaPotionOf(DWORD vnum, const TItemTable* t)
	{
		if (!IsPlayerBotLadaPotionKindOf(t))
			return false;
		if ((long long)t->dwGold < (long long)s_iPlayerBotLadaMinCheap)
			return false;
		if ((vnum >= 27100 && vnum <= 27105) || (vnum >= 27110 && vnum <= 27115) || IsPlayerBotPersonalBuffPotion(vnum) ||
				IsPlayerBotWithdrawnPotion(vnum))
			return false;
		return GetPlayerBotNpcShopUnitPrice(vnum) <= 0;
	}

	// The goods the lada lists, merges and takes back - by the proto (a line's and a bag item's alike).
	bool IsPlayerBotLadaKindOf(DWORD vnum, const TItemTable* t)
	{
		if (!t || vnum == 0)
			return false;
		switch (t->bType)
		{
			case ITEM_DS: case ITEM_SPECIAL_DS: case ITEM_METIN: case ITEM_COSTUME: case ITEM_BELT: case ITEM_QUEST:
				return false;
			default:
				break;
		}
		// MT2009_PLUS_BOT_LADA_FISH_V1: the fish family and the potions by their own rules (ITEM_POTION and the
		// USE_POTION subtypes were left out whole - Pieczony Rak Niebieski is ITEM_POTION, Pieczony Karas USE_POTION).
		if (IsPlayerBotFishFamilyOf(vnum, t))
		{
			if (!IsPlayerBotLadaFishOf(vnum, t))
				return false;
		}
		else if (IsPlayerBotLadaPotionKindOf(t))
		{
			if (!IsPlayerBotLadaPotionOf(vnum, t))
				return false;
		}
		if (t->bType == ITEM_USE && t->bSubType == USE_TUNING)
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
		// MT2009_PLUS_BOT_LADA_FISH_V1: a crafted potion over the floor is the lada's now (IsPlayerBotLadaKindOf); the
		// packed green and purple stay the visit's.
		if (IsPlayerBotPackedPotion(item))
			return false;
		// MT2009_PLUS_BOT_LADA_FISH_V1: no junk gear - a weapon or an armour piece whose reference ask a unit (the
		// asking price every buyer reads: the sheet, its lines, the market's memory) is under m2_bot_lada_min_gear
		// (50 000) keeps the old handling. Asked read-only: a look is no counter's ask (s_bPlayerBotAskStepReadOnly).
		if (item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR)
		{
			const bool wasReadOnly = s_bPlayerBotAskStepReadOnly;
			s_bPlayerBotAskStepReadOnly = true;
			const long long ask = (long long)GetPlayerBotShopAskingPrice(item);
			s_bPlayerBotAskStepReadOnly = wasReadOnly;
			if (ask / std::max<long long>(1, (long long)item->GetCount()) < (long long)s_iPlayerBotLadaMinGear)
			{
				++s_uPlayerBotLadaGearFloorRefused;
				return false;
			}
		}
		return true;
	}

	// MT2009_PLUS_BOT_LADA_FISH_V1 (playerbot_economy.h's junk rule): a bot with a stand standing the lada serves.
	bool IsPlayerBotLadaFishKeeper(LPCHARACTER ch)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		if (!c.on || !ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				IsPlayerBotSidekickServing(ch))
			return false;
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		return shop && shop->GetDuration() > 0 && (c.xch || (int)shop->GetSpawn().channel == (int)g_bChannel);
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
		// MT2009_PLUS_BOT_LADA_TIER_XCH_V1: the shared glut map (published / read), the new lines listed into a tier
		unsigned int tierPublished = 0, tierRead = 0, tierReadFailed = 0, newTier = 0, newTierCh2 = 0;
		// MT2009_PLUS_BOT_LADA_BOX_V1: the safebox's goods for the lada
		unsigned int boxVisits = 0, boxTaken = 0, boxKept = 0, boxRoom = 0, boxRate = 0, boxLeft = 0, boxDepositHeld = 0;
		unsigned long long boxUnits = 0;
		// MT2009_PLUS_BOT_LADA_FIX_V1: the repair of the crashed lines (queued, looked at, edited up, the yang they came
		// up by) and, at the last tier pass, the bot lines of a clearing good still under the floor
		unsigned int repairQueued = 0, repairLooked = 0, repairEdited = 0, crashedLines = 0, normalKinds = 0;
		unsigned long long repairYang = 0, crashedUnits = 0;
		// MT2009_PLUS_BOT_LADA_FISH_V1: the fish and the potions listed since the last census
		unsigned int fishListed = 0, potionListed = 0;
		unsigned long long fishListedUnits = 0, potionListedUnits = 0;
	};
	TPlayerBotLadaCensus s_kPlayerBotLadaCensus;

	// The world's lines, counted once a minute off this core's copy of every shop.
	struct TPlayerBotLadaWorld
	{
		unsigned int botShops = 0, botLines = 0, ladaLines = 0, allLines = 0, maxLines = 0, maxLada = 0;
		unsigned long long botUnits = 0, maxUnits = 0;
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
		// MT2009_PLUS_BOT_LADA_NOCAP_V1: no cap a bot unless the flag sets one; the world's counts every line a search walks
		if (c.cap > 0 && (int)shop->GetItems().size() >= c.cap)
		{
			++k.refusedCap;
			return false;
		}
		if ((int)s_kPlayerBotLadaWorld.allLines >= c.worldCap)
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
		// MT2009_PLUS_BOT_LADA_TIER_XCH_V1: a new line of a glutted kind asks the tier it ranks into - the same ranking
		// and the same shared clearing ask on every core of every channel (the line is not ranked yet: its id is new).
		int newTier = 0;
		if (item->GetRefineLevel() == 0 && item->GetCount() > 0 && price.yang > 0)
		{
			const DWORD units = (DWORD)item->GetCount();
			newTier = GetPlayerBotLadaNewLineTier(item->GetVnum(), (unsigned long long)price.yang * 1000ULL / units, units);
			if (newTier > 0)
				price.yang = GetPlayerBotLadaTierPrice(item->GetVnum(), (long long)units, (long long)price.yang, newTier);
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
		if (newTier > 0)
		{
			// this core prices it by its tier until its next ranking takes the line in
			s_mapPlayerBotLadaTier[id] = (WORD)newTier;
			NotePlayerBotLadaNewTierUnits(vnum, count);
			++k.newTier;
			if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
				++k.newTierCh2;
		}
		// the world's counts until the next count (the caps between two counts)
		++s_kPlayerBotLadaWorld.allLines;
		++s_kPlayerBotLadaWorld.botLines;
		++k.listed;
		k.listedUnits += count;
		// MT2009_PLUS_BOT_LADA_FISH_V1: the fish and the potions among them
		if (const TItemTable* lt = ITEM_MANAGER::instance().GetTable(vnum))
		{
			if (IsPlayerBotFishFamilyOf(vnum, lt))
			{
				++k.fishListed;
				k.fishListedUnits += count;
				NotePlayerBotFishRoastListed(vnum, (unsigned int)count);	// MT2009_PLUS_BOT_FISH_ROAST_V1
			}
			else if (IsPlayerBotLadaPotionKindOf(lt))
			{
				++k.potionListed;
				k.potionListedUnits += count;
			}
		}
		PlayerBotLogThrottled("lada_list", now,
				"PLAYERBOT_LADA: list pid=%u name=%s item=%u vnum=%u count=%u price=%lld pos=%d lines=%u ch=%u stand_ch=%u junk=%d tier=%d",
				pid, ch->GetName(), id, vnum, (unsigned int)count, (long long)price.yang, pos,
				(unsigned int)shop->GetItems().size() + 1, (unsigned int)g_bChannel, (unsigned int)shop->GetSpawn().channel,
				junk ? 1 : 0, newTier);
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
			if ((c.cap > 0 && (int)shop->GetItems().size() >= c.cap) || (int)s_kPlayerBotLadaWorld.allLines >= c.worldCap)
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

	// ------------------------------------------------------------------------------------------------ the safebox
	// MT2009_PLUS_BOT_LADA_BOX_V1 (the owner, 8 November 2026: why is the safebox not emptied down to the spare gear?):
	// a bot with a stand standing (IsPlayerBotLadaBoxKeeper - the lada's own test: any channel unless
	// m2_bot_lada_xch_off) takes the lada's goods out of its safebox at a storekeeper's visit (WithdrawPlayerBotLadaBox,
	// after the box's own withdrawal, the horse bags' review and before the G0 dust; the engine loads a safebox only
	// through the DB core's answer to a load at the keeper, so not remotely) and the lada's next pass, brought forward to
	// a minute away, lists them as it lists the bag. What stays in the box:
	//   * every weapon and armour piece - the spare gear: the element and resistance sets, the second set
	//     (IsPlayerBotSecondSetStored), the map gear and the families Iwakura's list keeps, the buff set; the box's own
	//     rules (lpp_released, own_gear, spare_goods, stalki) still take out the gear they let go of;
	//   * what is no lada kind (IsPlayerBotLadaKindItem: soul and dragon stones, shards, Cors, Materialy Rzemieslnicze,
	//     chests, medals, SM coupons, refine scrolls, mission books, rare goods, belts, sashes, talismans, costumes,
	//     potions, policy items), the treasure keys (kept for a chest that may drop), the G0 package's dust;
	//   * of every kind, its keep: the units the box holds stay while bag keep + box < the largest keep of the kind -
	//     the anvil's reserve, the herb's, the counter's (GetPlayerBotStallBaseKeep / the books' counted keep), the scarce
	//     materials' (mats_flow, the Biologist's share), the belts' - a stack comes out only when the rest covers it;
	//   * a kind the deposit put down in the last PLAYERBOT_SAFEBOX_PINGPONG_MS, and a kind this visit put down.
	// Into a bag that stays clear of the pressure the deposit waits for; at most m2_bot_lada_box_stacks (12) stacks a
	// visit and m2_bot_lada_box_rate (120) a minute a core; a bot calls for it every m2_bot_lada_box_gap_min (30)
	// minutes while its box holds goods (3 h once it holds none), never a companion, never while gambling. The herbs'
	// deposit (CollectPlayerBotSafeboxHerbs) no longer puts a stand keeper's spare herbs down while its bag is clear of
	// pressure - they are the lada's (m2_bot_lada_box_off 1: all of it off).
	const DWORD PLAYERBOT_LADA_BOX_EMPTY_GAP_MS = 3 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_LADA_BOX_PASS_SOON_MS = 60 * 1000;

	struct TPlayerBotLadaBox
	{
		DWORD nextAt = 0;
		int left = -1;	// the goods' stacks the last visit left in the box, -1 not looked yet
	};
	std::unordered_map<DWORD, TPlayerBotLadaBox> s_mapPlayerBotLadaBox;

	bool IsPlayerBotLadaBoxKeeper(LPCHARACTER ch)
	{
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		if (!c.on || !c.box || !ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				IsPlayerBotSidekickServing(ch))
			return false;
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		return shop && shop->GetDuration() > 0 && (c.xch || (int)shop->GetSpawn().channel == (int)g_bChannel);
	}

	// A bag that takes a piece of `size` cells and stays clear of the deposit's pressure.
	bool IsPlayerBotLadaBoxBagClear(LPCHARACTER ch, int size)
	{
		const int freeAfter = CountPlayerBotFreeInventoryCells(ch) - std::max(1, size);
		return freeAfter > PLAYERBOT_BAG_PRESSURE_FREE_CELLS &&
				(PLAYERBOT_BAG_CELLS - freeAfter) * 100 < PLAYERBOT_BAG_CELLS * PLAYERBOT_BAG_FULL_PERCENT;
	}

	// The storekeeper's errand for it (playerbot_town.h, the visit's bTownNeedSafebox).
	bool PlayerBotWantsLadaBox(LPCHARACTER ch, DWORD now)
	{
		if (!IsPlayerBotLadaBoxKeeper(ch) || ch->GetQuestFlag(PLAYERBOT_SAFEBOX_PAID_FLAG) <= 0 ||
				IsPlayerBotSafeboxIdle(ch->GetPlayerID(), now))
			return false;
		TPlayerBotLadaBox& b = s_mapPlayerBotLadaBox[ch->GetPlayerID()];
		if (b.nextAt == 0)
		{
			// the first call spread over the gap by the bot's id, so a core's keepers do not all walk to the keeper at once
			const DWORD gap = (DWORD)GetPlayerBotLadaCfg().boxGapMin * 60000U;
			b.nextAt = now + 60000U + (DWORD)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x424F5841U) % gap);
			return false;
		}
		// the gap does the pacing: 30 minutes while the box held goods, 3 h after a visit that found none
		return (int)(now - b.nextAt) >= 0 && IsPlayerBotLadaBoxBagClear(ch, 3);
	}

	// The goods of the box for the lada, whole stacks: is this one, and is it over the kind's keep?
	bool IsPlayerBotLadaBoxGoods(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR || item->GetType() == ITEM_TREASURE_KEY)
			return false;
#ifdef ENABLE_SOULBIND_SYSTEM
		if (item->IsSealed())
			return false;
#endif
		if (IsPlayerBotG0BoxDust(ch, item) || IsPlayerBotBuffSetPiece(ch, item))
			return false;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		if (IsPlayerBotSecondSetStored(ch, item))
			return false;
#endif
		return IsPlayerBotLadaKindItem(item);
	}

	int GetPlayerBotLadaBoxKeep(LPCHARACTER ch, LPITEM item, int& stallKeep)
	{
		const bool counted = IsPlayerBotCountedSingleGoods(item);
		stallKeep = counted ? GetPlayerBotCountedGoodsKeep(ch, item) : GetPlayerBotStallBaseKeep(ch, item);
		int keep = std::max(stallKeep, GetPlayerBotMatsScarceKeep(ch, item->GetVnum()));
		if (IsPlayerBotMatsBeltVnum(item->GetVnum()))
			keep = std::max(keep, GetPlayerBotMatsBeltKeep(ch, item));
		if (IsPlayerBotHerbalismHerb(item->GetVnum()))
			keep = std::max(keep, GetPlayerBotHerbKeep(ch, item->GetVnum()));
		return keep;
	}

	// The core's bucket of stacks taken out (m2_bot_lada_box_rate a minute).
	bool PlayerBotLadaBoxBudget(DWORD now)
	{
		static double s_tokens = 0;
		static DWORD s_at = 0;
		const double perMs = GetPlayerBotLadaCfg().boxRate / 60000.0;
		const double cap = std::max(1.0, GetPlayerBotLadaCfg().boxRate / 4.0);
		if (s_at == 0)
		{
			s_at = now ? now : 1;
			s_tokens = cap;
		}
		s_tokens = std::min(cap, s_tokens + (double)(now - s_at) * perMs);
		s_at = now ? now : 1;
		if (s_tokens < 1.0)
			return false;
		s_tokens -= 1.0;
		return true;
	}

	int WithdrawPlayerBotLadaBox(LPCHARACTER ch, CSafebox* box, const std::set<DWORD>* pJustDeposited, bool gambling)
	{
		if (!ch || !box || gambling || !IsPlayerBotLadaBoxKeeper(ch))
			return 0;
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		const DWORD pid = ch->GetPlayerID();
		const DWORD now = get_dword_time();
		++k.boxVisits;
		// what the box holds of each kind (the keep is weighed against it)
		std::map<DWORD, long long> inBox;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			LPITEM item = box->IsValidPosition(pos) ? box->Get(pos) : NULL;
			if (item)
				inBox[item->GetVnum()] += std::max<int>(1, (int)item->GetCount());
		}
		int taken = 0, left = 0;
		unsigned long long units = 0;
		bool stopped = false;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			LPITEM item = box->IsValidPosition(pos) ? box->Get(pos) : NULL;
			if (!item || !IsPlayerBotLadaBoxGoods(ch, item))
				continue;
			const DWORD vnum = item->GetVnum();
			if ((pJustDeposited && pJustDeposited->count(vnum)) ||
					WasPlayerBotBoxMovedRecently(s_mapPlayerBotBoxPutAt, pid, vnum, now))
			{
				++left;	// the deposit's, for now: the next visit's
				continue;
			}
			const long long count = std::max<int>(1, (int)item->GetCount());
			int stallKeep = 0;
			const int keep = GetPlayerBotLadaBoxKeep(ch, item, stallKeep);
			if (inBox[vnum] - count < (long long)std::max(0, keep - stallKeep))
			{
				++k.boxKept;
				continue;
			}
			if (stopped)
			{
				++left;
				continue;
			}
			if (taken >= c.boxStacks)
			{
				stopped = true;
				++left;
				continue;
			}
			const int cell = IsPlayerBotLadaBoxBagClear(ch, item->GetSize()) ? ch->GetEmptyInventory(item->GetSize()) : -1;
			if (cell < 0)
			{
				++k.boxRoom;
				stopped = true;
				++left;
				continue;
			}
			if (!PlayerBotLadaBoxBudget(now))
			{
				++k.boxRate;
				stopped = true;
				++left;
				continue;
			}
			char szHint[128];
			snprintf(szHint, sizeof(szHint), "%s %u", item->GetName(), (unsigned int)item->GetCount());
			box->Remove(pos);
			item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			FlushPlayerBotItemRow(item);	// the row now, as CInputMain::SafeboxCheckout writes it (WithdrawPlayerBotSafebox)
			LogManager::instance().ItemLog(ch, item, "SAFEBOX GET", szHint);
			NotePlayerBotBoxMove(s_mapPlayerBotBoxTakenAt, pid, vnum, now);
			inBox[vnum] -= count;
			++taken;
			units += (unsigned long long)count;
			PlayerBotLogThrottled("lada_box_take", now,
					"PLAYERBOT_LADA: box take pid=%u name=%s vnum=%u count=%lld keep=%d stall_keep=%d box_left_kind=%lld free_cells=%d ch=%u",
					pid, ch->GetName(), vnum, count, keep, stallKeep, inBox[vnum], CountPlayerBotFreeInventoryCells(ch),
					(unsigned int)g_bChannel);
		}
		k.boxTaken += (unsigned int)taken;
		k.boxUnits += units;
		k.boxLeft += (unsigned int)left;
		TPlayerBotLadaBox& b = s_mapPlayerBotLadaBox[pid];
		b.left = left;
		b.nextAt = now + (left > 0 ? (DWORD)c.boxGapMin * 60000U : PLAYERBOT_LADA_BOX_EMPTY_GAP_MS);
		if (taken > 0)
		{
			// the lada's next pass lists them, a minute away
			TPlayerBotLada& L = s_mapPlayerBotLada[pid];
			if (!L.active && (L.nextPass == 0 || (int)(L.nextPass - (now + PLAYERBOT_LADA_BOX_PASS_SOON_MS)) > 0))
				L.nextPass = now + PLAYERBOT_LADA_BOX_PASS_SOON_MS;
			PlayerBotLogThrottled("lada_box_visit", now,
					"PLAYERBOT_LADA: box visit pid=%u name=%s taken=%d units=%llu left=%d next_min=%u",
					pid, ch->GetName(), taken, units, left, (unsigned int)((b.nextAt - now) / 60000U));
		}
		return taken;
	}

	// The herbs' deposit of a stand keeper with a bag clear of pressure: none - its spare herbs are the lada's.
	bool IsPlayerBotLadaHerbDepositHeld(LPCHARACTER ch)
	{
		if (!IsPlayerBotLadaBoxKeeper(ch) || IsPlayerBotBagFull(ch) ||
				CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_BAG_PRESSURE_FREE_CELLS)
			return false;
		++s_kPlayerBotLadaCensus.boxDepositHeld;
		return true;
	}

	// ------------------------------------------------------------------------------------------------ the core
	struct TPlayerBotLadaTierEdit
	{
		DWORD owner, item;
		bool repair;	// MT2009_PLUS_BOT_LADA_FIX_V1: a line under the market floor, not a tier line
	};
	// MT2009_PLUS_BOT_LADA_FIX_V1: the repair sweep - at most this many lines a tier pass, a line looked at once an hour
	const unsigned int PLAYERBOT_LADA_REPAIR_PER_PASS = 3000;
	const DWORD PLAYERBOT_LADA_REPAIR_AGAIN_MS = 60 * 60 * 1000;
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotLadaRepairSeen;	// line id -> when the sweep queued it
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
			unsigned int lada = 0;
			unsigned long long units = 0;
			for (const auto& [id, line] : shop->GetItems())
				if (line)
				{
					units += line->GetInfo().count;
					if ((int)line->GetInfo().pos >= PLAYERBOT_LADA_POS_BASE)
						++lada;
				}
			w.botUnits += units;
			w.ladaLines += lada;
			if (lines > w.maxLines)
			{
				w.maxLines = lines;
				w.maxOwner = shop->GetOwnerPID();
				w.maxLada = lada;
				w.maxUnits = units;
			}
		}
		s_kPlayerBotLadaWorld = w;
	}

	// ------------------------------------------------------------------------------------------------ the shared tiers
	// MT2009_PLUS_BOT_LADA_TIER_XCH_V1 (playerbot_market_clearing.h): the glut's kinds and clearing asks, one writer.
	const DWORD PLAYERBOT_LADA_TIER_RANK_MS = 60 * 1000;		// every core ranks the lines this often (the edits every TIER_MS)
	const unsigned int PLAYERBOT_LADA_TIER_SHARED_MAX_AGE_S = 15 * 60;	// a writer's rows older than this are let go
	const size_t PLAYERBOT_LADA_TIER_ROWS_A_QUERY = 80;	// DBManager::Query formats into 4096 bytes: ~41 a row

	struct TPlayerBotLadaTierShared
	{
		bool writer = false, tableReady = false;
		const char* source = "none";	// own (the writer), shared (read), none
		unsigned int kinds = 0, writerPort = 0;
		DWORD readAt = 0;
	};
	TPlayerBotLadaTierShared s_kPlayerBotLadaTierShared;

	// The writer is one core of the shop channel, the same answer on every core from the full copy: the core hosting
	// the map of the shop channel's standing stand of the lowest owner pid (a person's or a bot's - every core sees the
	// same shops; the bots' registry is a core's own).
	bool IsPlayerBotLadaTierWriter()
	{
		if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
			return false;
		DWORD lowest = 0;
		int map = 0;
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
			if (shop && shop->GetDuration() > 0 && (int)shop->GetSpawn().channel == playerbot_channel_rules::SHOP_CHANNEL &&
					(lowest == 0 || shop->GetOwnerPID() < lowest))
			{
				lowest = shop->GetOwnerPID();
				map = shop->GetSpawn().map;
			}
		return lowest != 0 && IsPlayerBotMapHostedHere(map);
	}

	bool EnsurePlayerBotLadaTierTable()
	{
		TPlayerBotLadaTierShared& s = s_kPlayerBotLadaTierShared;
		if (s.tableReady)
			return true;
		std::unique_ptr<SQLMsg> create(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_lada_tier ("
				"vnum INT UNSIGNED NOT NULL PRIMARY KEY, "
				"clear_unit INT UNSIGNED NOT NULL DEFAULT 0, "
				"port SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
				"updated INT UNSIGNED NOT NULL DEFAULT 0, "
				"KEY updated (updated)) ENGINE=InnoDB"));
		s.tableReady = create && create->Get();
		return s.tableReady;
	}

	// The writer's rows: every glutted kind of its clearing, stamped; what it no longer clears goes (async, in order).
	void PublishPlayerBotLadaTiers(const std::unordered_map<DWORD, DWORD>& glut)
	{
		if (!EnsurePlayerBotLadaTierTable())
			return;
		const unsigned int stamp = (unsigned int)get_global_time();
		std::string rows;
		size_t n = 0;
		auto flush = [&]() {
			if (rows.empty())
				return;
			DBManager::instance().Query("REPLACE INTO player.playerbot_lada_tier (vnum, clear_unit, port, updated) VALUES %s",
					rows.c_str());
			rows.clear();
			n = 0;
		};
		for (const auto& [vnum, unit] : glut)
		{
			char row[96];
			snprintf(row, sizeof(row), "%s(%u,%u,%u,%u)", rows.empty() ? "" : ",", vnum, unit, (unsigned int)mother_port, stamp);
			rows += row;
			if (++n >= PLAYERBOT_LADA_TIER_ROWS_A_QUERY)
				flush();
		}
		flush();
		DBManager::instance().Query("DELETE FROM player.playerbot_lada_tier WHERE updated < %u", stamp);
		++s_kPlayerBotLadaCensus.tierPublished;
	}

	// Every other core: the writer's rows, fresh ones only (a writer gone leaves no tiers rather than old ones).
	bool ReadPlayerBotLadaTiers(std::unordered_map<DWORD, DWORD>& glut)
	{
		glut.clear();
		if (!EnsurePlayerBotLadaTierTable())
			return false;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT vnum, clear_unit, port FROM player.playerbot_lada_tier WHERE updated >= %u AND clear_unit > 0",
				(unsigned int)get_global_time() - PLAYERBOT_LADA_TIER_SHARED_MAX_AGE_S));
		if (!msg || !msg->Get())
			return false;
		if (msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				DWORD vnum = 0, unit = 0;
				unsigned int port = 0;
				str_to_number(vnum, row[0]);
				str_to_number(unit, row[1]);
				str_to_number(port, row[2]);
				if (vnum && unit)
					glut[vnum] = unit;
				s_kPlayerBotLadaTierShared.writerPort = port;
			}
		}
		return true;
	}

	// The tiers' input, every PLAYERBOT_LADA_TIER_MS: the writer's own clearing (published), or the writer's rows.
	void RefreshPlayerBotLadaTierInput(DWORD now)
	{
		TPlayerBotLadaTierShared& s = s_kPlayerBotLadaTierShared;
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		std::unordered_map<DWORD, DWORD> glut;
		s.writer = IsPlayerBotLadaTierWriter();
		if (s.writer)
		{
			if (s_bPlayerBotLadaTiers)
				for (const auto& [vnum, kind] : s_mapPlayerBotClear)
					if (kind.clearUnit != 0)
						glut[vnum] = kind.clearUnit;
			PublishPlayerBotLadaTiers(glut);
			s.source = "own";
			s.writerPort = (unsigned int)mother_port;
		}
		else if (s_bPlayerBotLadaTiers)
		{
			if (ReadPlayerBotLadaTiers(glut))
			{
				++k.tierRead;
				s.source = glut.empty() ? "none" : "shared";
			}
			else
			{
				++k.tierReadFailed;
				glut = s_mapPlayerBotLadaTierClear;	// the last read stands until a read works
			}
		}
		else
			s.source = "none";
		s.kinds = (unsigned int)glut.size();
		s.readAt = now ? now : 1;
		s_mapPlayerBotLadaTierClear.swap(glut);
	}

	// MT2009_PLUS_BOT_LADA_FIX_V1: the normal price of every clearing good (s_mapPlayerBotMarketNormalRef: the 60th
	// percentile of its units on the shop channel's stands - the median of what stands above the tiers' fifth) and the
	// repair of the bot lines the old tiers crashed: a bot line of a clearing good on a stand this core hosts, not in a
	// tier now, asking under m2_bot_market_floor_pct of its kind's normal price, is queued for the tier edits, which
	// price it by BotOfflineRepriceTarget (its ordinary price; the tier's 5 / 3 % off once it ranks into one) - its own
	// owner's line only, the host core's edit as every tier edit. The census counts what is still under the floor.
	void RepairPlayerBotLadaCrashedLines(DWORD now, const std::unordered_map<DWORD, WORD>& tiers)
	{
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		struct TUnits { unsigned long long unitMilli; DWORD count; };
		std::unordered_map<DWORD, bool> goods;
		std::unordered_map<DWORD, std::vector<TUnits> > byKind;
		auto isGoods = [&goods](DWORD vnum) {
			auto it = goods.find(vnum);
			if (it == goods.end())
				it = goods.emplace(vnum, IsPlayerBotClearingGoods(vnum)).first;
			return it->second;
		};
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || shop->GetDuration() == 0 || (int)shop->GetSpawn().channel != playerbot_channel_rules::SHOP_CHANNEL)
				continue;
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || line->GetInfo().count == 0 || !isGoods(line->GetInfo().vnum))
					continue;
				const long long yang = (long long)line->GetPrice().GetTotalYangAmount();
				if (yang > 0)
					byKind[line->GetInfo().vnum].push_back(TUnits{ (unsigned long long)yang * 1000ULL / line->GetInfo().count,
							(DWORD)line->GetInfo().count });
			}
		}
		std::unordered_map<DWORD, DWORD> refs;
		for (auto& [vnum, lines] : byKind)
		{
			std::sort(lines.begin(), lines.end(), [](const TUnits& a, const TUnits& b) { return a.unitMilli < b.unitMilli; });
			unsigned long long units = 0;
			for (const TUnits& l : lines)
				units += l.count;
			const unsigned long long at = units * 6ULL / 10ULL;
			unsigned long long before = 0;
			for (const TUnits& l : lines)
			{
				before += l.count;
				if (before > at)
				{
					refs[vnum] = (DWORD)std::min<unsigned long long>(0xFFFFFFFFULL, std::max<unsigned long long>(1ULL, l.unitMilli / 1000ULL));
					break;
				}
			}
		}
		s_mapPlayerBotMarketNormalRef.swap(refs);
		k.normalKinds = (unsigned int)s_mapPlayerBotMarketNormalRef.size();

		// the sweep's memory: what it queued in the last hour is not queued again
		for (auto it = s_mapPlayerBotLadaRepairSeen.begin(); it != s_mapPlayerBotLadaRepairSeen.end(); )
			if (now - it->second >= PLAYERBOT_LADA_REPAIR_AGAIN_MS)
				it = s_mapPlayerBotLadaRepairSeen.erase(it);
			else
				++it;
		CPlayerBotManager& bots = CPlayerBotManager::instance();
		unsigned int crashed = 0, queued = 0;
		unsigned long long crashedUnits = 0;
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || shop->GetDuration() == 0 || (int)shop->GetSpawn().channel != playerbot_channel_rules::SHOP_CHANNEL)
				continue;
			const DWORD owner = shop->GetOwnerPID();
			if (!bots.IsRegisteredBotPID(owner) || IsPlayerBotSidekickPID(owner))
				continue;
			const bool hosted = (int)shop->GetSpawn().channel == (int)g_bChannel && IsPlayerBotMapHostedHere(shop->GetSpawn().map);
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || line->GetInfo().count == 0 || !isGoods(line->GetInfo().vnum))
					continue;
				const unsigned long long floor = GetPlayerBotMarketFloorUnit(line->GetInfo().vnum, now);
				const long long yang = (long long)line->GetPrice().GetTotalYangAmount();
				if (floor == 0 || yang <= 0 || (unsigned long long)yang >= floor * (unsigned long long)line->GetInfo().count)
					continue;
				++crashed;
				crashedUnits += line->GetInfo().count;
				if (!hosted || tiers.count(id) || queued >= PLAYERBOT_LADA_REPAIR_PER_PASS ||
						s_mapPlayerBotLadaRepairSeen.count(id))
					continue;
				s_mapPlayerBotLadaRepairSeen[id] = now ? now : 1;
				s_dequePlayerBotLadaTierEdits.push_back(TPlayerBotLadaTierEdit{ owner, id, true });
				++queued;
			}
		}
		k.crashedLines = crashed;
		k.crashedUnits = crashedUnits;
		k.repairQueued += queued;
	}

	// The glut's tiers (playerbot_market_clearing.h): every core of every channel ranks the shop channel's stands' lines
	// of the shared glutted kinds every PLAYERBOT_LADA_TIER_RANK_MS (the same lines, the same input: the same tiers
	// everywhere), and every PLAYERBOT_LADA_TIER_MS queues the edits of the stands this core hosts.
	void RankPlayerBotLadaTiers(DWORD now, bool queueEdits)
	{
		TPlayerBotLadaCensus& k = s_kPlayerBotLadaCensus;
		std::unordered_map<DWORD, WORD> tiers;
		std::unordered_map<DWORD, DWORD> owners;
		std::unordered_map<DWORD, TPlayerBotLadaTierCurve> curves;
		if (s_bPlayerBotLadaTiers && !s_mapPlayerBotLadaTierClear.empty())
		{
			struct TLine { unsigned long long unitMilli; DWORD id, count, owner; };
			std::map<DWORD, std::vector<TLine> > byKind;
			for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
			{
				if (!shop || shop->GetDuration() == 0 || (int)shop->GetSpawn().channel != playerbot_channel_rules::SHOP_CHANNEL)
					continue;
				for (const auto& [id, line] : shop->GetItems())
				{
					if (!line || line->GetInfo().count == 0 || !s_mapPlayerBotLadaTierClear.count(line->GetInfo().vnum))
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
				TPlayerBotLadaTierCurve& curve = curves[vnum];
				curve.unitMilli.reserve(lines.size());
				curve.unitsTo.reserve(lines.size());
				unsigned long long units = 0;
				for (const TLine& l : lines)
				{
					units += l.count;
					curve.unitMilli.push_back(l.unitMilli);
					curve.unitsTo.push_back(units);
				}
				curve.units = units;
				if (units == 0)
					continue;
				if (queueEdits)
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
					if (!queueEdits)
						continue;
					if (share < 100)
						++k.tier1;
					else
						++k.tier2;
				}
			}
		}
		if (queueEdits)
		{
			// The bot lines of the stands this core hosts whose tier came or went (or stays: the clearing ask moves)
			// are edited to their target - by this core alone: the stand's host, as before.
			CPlayerBotManager& bots = CPlayerBotManager::instance();
			auto queue = [&](DWORD id, DWORD owner) {
				if (!bots.IsRegisteredBotPID(owner) || IsPlayerBotSidekickPID(owner))
					return;
				auto shop = ikashop::GetManager().GetShopByOwnerID(owner);
				if (!shop || (int)shop->GetSpawn().channel != (int)g_bChannel || !IsPlayerBotMapHostedHere(shop->GetSpawn().map))
					return;
				s_dequePlayerBotLadaTierEdits.push_back(TPlayerBotLadaTierEdit{ owner, id, false });
			};
			s_dequePlayerBotLadaTierEdits.clear();
			for (const auto& [id, owner] : owners)
				queue(id, owner);
			for (const auto& [id, owner] : s_mapPlayerBotLadaTierOwner)
				if (!owners.count(id))
					queue(id, owner);
			s_mapPlayerBotLadaTierOwner.swap(owners);
			++k.tierPasses;
			RepairPlayerBotLadaCrashedLines(now, tiers);
		}
		s_mapPlayerBotLadaTier.swap(tiers);
		s_mapPlayerBotLadaTierCurve.swap(curves);
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
			if (e.repair)
				++k.repairLooked;
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
			if (e.repair && target.price > asked)
			{
				++k.repairEdited;
				k.repairYang += (unsigned long long)(target.price - asked);
				PlayerBotLogThrottled("lada_repair", now,
						"PLAYERBOT_LADA: repair owner=%u item=%u vnum=%u count=%lld asked=%lld price=%lld normal_unit=%u",
						e.owner, e.item, vnum, count, asked, (long long)target.price, GetPlayerBotMarketNormalUnit(vnum, now));
			}
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
		// MT2009_PLUS_BOT_LADA_NOCAP_V1 / _VIEW_V1 / _TIER_XCH_V1 / _BOX_V1: the second line (the log's lines end at 1 KB) -
		// the biggest counter, what the stand windows carried, the shared tiers, the safebox's goods.
		sys_log(0, "PLAYERBOT_LADA: census2 ch=%u max_lines=%u max_lada_lines=%u max_units=%llu max_owner=%u cap=%d world_lines=%u "
				"world_cap=%d view_max_sent=%u view_max_held=%u views=%llu view_hidden=%llu view_refresh_skipped=%llu tier_src=%s "
				"tier_writer=%d tier_writer_port=%u tier_kinds_shared=%u tier_published=%u tier_read=%u tier_read_failed=%u "
				"new_looked=%u new_tier=%u ch2_tier_hits=%u box_visits=%u box_taken=%u box_units=%llu box_kept=%u box_room=%u "
				"box_rate=%u box_left=%u box_deposit_held=%u",
				(unsigned int)g_bChannel, w.maxLines, w.maxLada, w.maxUnits, w.maxOwner, c.cap, w.allLines, c.worldCap,
				ikashop_lada_view::maxSent, ikashop_lada_view::maxHeld, ikashop_lada_view::views, ikashop_lada_view::hidden,
				ikashop_lada_view::refreshSkipped, s_kPlayerBotLadaTierShared.source, s_kPlayerBotLadaTierShared.writer ? 1 : 0,
				s_kPlayerBotLadaTierShared.writerPort, s_kPlayerBotLadaTierShared.kinds, k.tierPublished, k.tierRead,
				k.tierReadFailed, s_uPlayerBotLadaNewLooked, k.newTier, k.newTierCh2, k.boxVisits, k.boxTaken, k.boxUnits,
				k.boxKept, k.boxRoom, k.boxRate, k.boxLeft, k.boxDepositHeld);
		// MT2009_PLUS_BOT_LADA_FIX_V1: the market floor and the repair of the crashed lines
		sys_log(0, "PLAYERBOT_LADA: census3 ch=%u market_floor_pct=%d normal_kinds=%u crashed_lines=%u crashed_units=%llu "
				"repair_queued=%u repair_looked=%u repair_edited=%u repair_yang=%llu sales_clamped=%u",
				(unsigned int)g_bChannel, c.floorPct, k.normalKinds, k.crashedLines, k.crashedUnits, k.repairQueued,
				k.repairLooked, k.repairEdited, k.repairYang, s_uPlayerBotSaleSignalClamped);
		// MT2009_PLUS_BOT_LADA_FISH_V1: the fish and the potions on the bots' counters (this core's copy), the crayfish
		// (27827 / 27857 / 27887) apart, what was listed of them since the last census, the gear the value floor left out.
		{
			unsigned int fishLines = 0, fishLada = 0, potionLines = 0, potionLada = 0, crayLines = 0;
			unsigned long long fishUnits = 0, potionUnits = 0, crayUnits = 0;
			CPlayerBotManager& reg = CPlayerBotManager::instance();
			for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
			{
				if (!shop || !reg.IsRegisteredBotPID(shop->GetOwnerPID()))
					continue;
				for (const auto& [id, line] : shop->GetItems())
				{
					if (!line || !line->GetTable())
						continue;
					const DWORD v = line->GetInfo().vnum;
					const bool lada = (int)line->GetInfo().pos >= PLAYERBOT_LADA_POS_BASE;
					if (IsPlayerBotFishFamilyOf(v, line->GetTable()))
					{
						++fishLines;
						fishUnits += line->GetInfo().count;
						if (lada)
							++fishLada;
						if (v == 27827 || v == 27857 || v == 27887)
						{
							++crayLines;
							crayUnits += line->GetInfo().count;
						}
					}
					else if (IsPlayerBotLadaPotionKindOf(line->GetTable()))
					{
						++potionLines;
						potionUnits += line->GetInfo().count;
						if (lada)
							++potionLada;
					}
				}
			}
			sys_log(0, "PLAYERBOT_LADA: census4 ch=%u min_cheap=%d min_gear=%d fish_lines=%u fish_units=%llu fish_lada_lines=%u "
					"crayfish_lines=%u crayfish_units=%llu potion_lines=%u potion_units=%llu potion_lada_lines=%u "
					"fish_listed=%u fish_listed_units=%llu potion_listed=%u potion_listed_units=%llu gear_floor_refused=%u",
					(unsigned int)g_bChannel, c.minCheap, c.minGear, fishLines, fishUnits, fishLada, crayLines, crayUnits,
					potionLines, potionUnits, potionLada, k.fishListed, k.fishListedUnits, k.potionListed, k.potionListedUnits,
					s_uPlayerBotLadaGearFloorRefused);
			s_uPlayerBotLadaGearFloorRefused = 0;
		}
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
		s_uPlayerBotLadaNewLooked = 0;
		s_uPlayerBotSaleSignalClamped = 0;
		ikashop_lada_view::maxSent = ikashop_lada_view::maxHeld = 0;
		ikashop_lada_view::views = ikashop_lada_view::hidden = ikashop_lada_view::refreshSkipped = 0;
		(void)now;
	}

	// The core's clocks, from any bot's tick.
	void ManagePlayerBotLadaCore(DWORD now)
	{
		static DWORD s_dwAt = 0, s_dwWorld = 0, s_dwTier = 0, s_dwRank = 0, s_dwCensus = 0;
		if (s_dwAt != 0 && now - s_dwAt < 1000)
			return;
		s_dwAt = now ? now : 1;
		const TPlayerBotLadaCfg& c = GetPlayerBotLadaCfg();
		if (s_dwWorld == 0 || now - s_dwWorld >= 60000)
		{
			s_dwWorld = now ? now : 1;
			CountPlayerBotLadaWorld();
		}
		// The tiers on (and off: the lines edited back once), on every core of every channel
		// (MT2009_PLUS_BOT_LADA_TIER_XCH_V1): the input (published by the writer, read by the others) and the ranking
		// with the edits every PLAYERBOT_LADA_TIER_MS, the ranking alone every PLAYERBOT_LADA_TIER_RANK_MS between them.
		const bool tierWork = c.tiers || !s_mapPlayerBotLadaTier.empty() || !s_mapPlayerBotLadaTierOwner.empty() ||
				!s_mapPlayerBotLadaTierClear.empty() || s_kPlayerBotLadaTierShared.writer;
		if (tierWork && (s_dwTier == 0 || now - s_dwTier >= PLAYERBOT_LADA_TIER_MS))
		{
			s_dwTier = s_dwRank = now ? now : 1;
			RefreshPlayerBotLadaTierInput(now);
			RankPlayerBotLadaTiers(now, true);
		}
		else if (tierWork && now - s_dwRank >= PLAYERBOT_LADA_TIER_RANK_MS)
		{
			s_dwRank = now ? now : 1;
			RankPlayerBotLadaTiers(now, false);
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
