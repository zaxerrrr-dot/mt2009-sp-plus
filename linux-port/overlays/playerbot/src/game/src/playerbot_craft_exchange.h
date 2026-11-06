#ifndef __INC_METIN2_PLAYERBOT_CRAFT_EXCHANGE_H__
#define __INC_METIN2_PLAYERBOT_CRAFT_EXCHANGE_H__

// The Dozorca's exchange (MT2009 Plus): refine goods into Materialy Rzemieslnicze, and the materials' economy.
//
//   * xyz_refine_exchange.quest, the Dozorca (9005): refine goods (30000-30092,
//     30192-30199, 30343-30359, 30367) into Materialy Rzemieslnicze (30378),
//     1000 yang a piece, 55 in a hundred come out (item_exchange.lua; the
//     world's difficulty may change that, GetPlayerBotExchangeChance).
//
// The window is a client's, so the pass does server-side what the quest
// does, with its numbers (the Alchemist's exchange in playerbot_town.h is the
// same shape). What a bot keeps, buys and exchanges for is its horse
// training's materials (playerbot_horse30.h) and a Champion's elixirs of
// resistance (playerbot_yohara_shop.h); the refine goods its counters did not
// sell go to the Dozorca instead of staying, and the materials over its own
// go on its counter at PLAYERBOT_CRAFT_MATERIAL_PRICE a piece.
// (MT2009_PLUS_HORSE40_V3: the horse bags and the bots' rows of them are gone
// from Yohara - the owner, 30 October 2026.)

namespace
{
	const DWORD PLAYERBOT_CRAFT_MATERIAL_VNUM = 30378;
	const DWORD PLAYERBOT_CRAFT_MATERIAL_PRICE = 100000;
	const long long PLAYERBOT_CRAFT_EXCHANGE_FEE = 1000;
	// A trip to the Dozorca for fewer goods than this is not worth the walk -
	// unless the bot is short of materials.
	const int PLAYERBOT_CRAFT_EXCHANGE_MIN_UNITS = 10;
	// A refine-goods line on an offline counter this long unsold comes home to
	// be exchanged (BotOfflineUnwantedLine).
	const DWORD PLAYERBOT_CRAFT_UNSOLD_RECALL_MS = PLAYERBOT_CRAFT_UNSOLD_RECALL_MS_PRE;
	// And a line of the classic stall that came home unsold this many times.
	const int PLAYERBOT_CRAFT_UNSOLD_STANDS = 2;
	const DWORD PLAYERBOT_CRAFT_CHECK_MIN_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_CRAFT_CHECK_MAX_MS = 9 * 60 * 1000;
	// A material off a counter: at most this a piece.
	const long long PLAYERBOT_CRAFT_MATERIAL_MAX_BUY = 150000;
	const int PLAYERBOT_CRAFT_MATERIAL_PURSE_PERCENT = 40;
	// MT2009_PLUS_CRAFT_MATERIAL_MARKET_V1: with this many pieces on the counters
	// of the world the market is full, and a bot buys for everything it still
	// wants (not only the next step) out of a larger share of its purse.
	const DWORD PLAYERBOT_CRAFT_MATERIAL_MARKET_FULL_UNITS = 400;
	const int PLAYERBOT_CRAFT_MATERIAL_FULL_PURSE_PERCENT = 60;

	enum
	{
		PLAYERBOT_CRAFT_ERRAND_NONE,
		PLAYERBOT_CRAFT_ERRAND_DOZORCA,
	};

	struct TPlayerBotCraftStats
	{
		unsigned exchanges;
		unsigned long long unitsIn;
		unsigned long long materialsOut;
		unsigned recalled;
		unsigned materialsBought;
		unsigned medalsBought;
		unsigned goodsBought;
		// MT2009_PLUS_CRAFT_MATERIAL_MARKET_V1: the materials' census - pieces and
		// yang asked for, and the lines a bot wanted but let stand.
		unsigned long long materialUnitsBought;
		unsigned long long materialYang;
		unsigned materialRefusedCap;
		unsigned materialRefusedPurse;
	};
	TPlayerBotCraftStats s_kPlayerBotCraftStats = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
	// Refine-goods lines that came home unsold from an offline counter, by
	// item id: the Dozorca's, not the counter's again.
	std::set<DWORD> s_setPlayerBotCraftRecalled;

	// MT2009_PLUS_BOT_MATS_FLOW_V1: the swap at the Dozorca (playerbot_mats_flow.h, later) - 15 of these for a refine
	// material of the maps up to 75 that a worn piece's next step lacks.
	int GetPlayerBotMatsSwapWanted(LPCHARACTER ch);
	bool IsPlayerBotMatsSwapDue(LPCHARACTER ch);
	int SwapPlayerBotMaterials(LPCHARACTER ch, int budget);
	int GetPlayerBotMatsCfgVisitMax();

	int CountPlayerBotCraftMaterials(LPCHARACTER ch)
	{
		return ch ? (int)ch->CountSpecifyItem(PLAYERBOT_CRAFT_MATERIAL_VNUM) : 0;
	}

	// MT2009_PLUS_HORSE30_V1: every bot's horse training takes materials
	// (5 / 10 / 20 a level, playerbot_horse30.h) - what a bot keeps, buys and
	// exchanges for.
	int GetPlayerBotCraftMaterialsWanted(LPCHARACTER ch, bool nextOnly)
	{
		return GetPlayerBotHorseGoodsMaterialsWanted(ch, nextOnly) + // MT2009_PLUS_HORSE_GOODS_MARKET_V1
				GetPlayerBotYoharaShopMaterialsWanted(ch) + // MT2009_PLUS_BOT_YOHARA_SHOP_V1: a Champion's elixirs of resistance (Dongan's exchange)
				GetPlayerBotMatsSwapWanted(ch) + // MT2009_PLUS_BOT_MATS_FLOW_V1: the swap's materials
				GetPlayerBotBeltSwapWanted(ch); // MT2009_PLUS_BOT_BELT_MATS_V1: a belt maker's metal and pearl
	}

	bool IsPlayerBotCraftExchangeVnum(DWORD vnum)
	{
		return (vnum >= 30000 && vnum <= 30092) || (vnum >= 30192 && vnum <= 30199) ||
				(vnum >= 30343 && vnum <= 30359) || vnum == 30367;
	}

	void NotePlayerBotCraftRecalled(DWORD pid, DWORD itemId)
	{
		if (s_setPlayerBotCraftRecalled.insert(itemId).second)
		{
			++s_kPlayerBotCraftStats.recalled;
			if (s_setPlayerBotCraftRecalled.size() > 200000)
				s_setPlayerBotCraftRecalled.clear();
		}
	}

	bool IsPlayerBotCraftUnsold(LPCHARACTER ch, LPITEM item)
	{
		if (s_setPlayerBotCraftRecalled.count(item->GetID()))
			return true;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (st == s_mapPlayerBotAIStates.end())
			return false;
		std::map<DWORD, BYTE>::const_iterator unsold = st->second.mapStallUnsold.find(item->GetID());
		return unsold != st->second.mapStallUnsold.end() && unsold->second >= PLAYERBOT_CRAFT_UNSOLD_STANDS;
	}

	// MT2009_PLUS_BOT_BAG_CLEANUP_V1: how much of one refine good a bag keeps
	// for good - its anvil's reserve (GetPlayerBotRefineMaterialReserve: twice
	// the largest recipe count among the pieces it would raise), and never
	// under PLAYERBOT_BAG_MATERIAL_KEEP. What is over that is a hoard: it
	// waits PLAYERBOT_BAG_MATERIAL_HOARD_WAIT_MS for the counter, which lists
	// it as before (ScorePlayerBotShopStock, at the ledger's price), and what
	// is still in the bag after that goes to the Dozorca for Materialy
	// Rzemieslnicze - never to the merchant (the owner, 6 October). The bags
	// of the test world held 320 000 exchangeable refine goods, 186 000 of
	// them past ten of a kind in a bag (7 630 bot-kinds over ten, 1 387 over
	// fifty): a counter cuts a material one or two at a time, and only what
	// went up and came home unsold ever reached the Dozorca.
	const int PLAYERBOT_BAG_MATERIAL_KEEP = 10;
	const DWORD PLAYERBOT_BAG_MATERIAL_HOARD_WAIT_MS = 6 * 60 * 60 * 1000;
	const size_t PLAYERBOT_BAG_MATERIAL_HOARD_SINCE_MAX = 200000;
	// When each bot's hoard of each kind was first seen, by (pid, vnum); gone
	// as soon as the bag is back under its keep. Not kept over a restart: the
	// wait starts again then, once.
	std::map<std::pair<DWORD, DWORD>, DWORD> s_mapPlayerBotMaterialHoardSince;

	int GetPlayerBotMaterialHoardKeep(LPCHARACTER ch, DWORD vnum)
	{
		return std::max(PLAYERBOT_BAG_MATERIAL_KEEP, GetPlayerBotRefineMaterialReserve(ch, vnum));
	}

	// Whether this bot's hoard of the kind has waited its time for the counter.
	bool IsPlayerBotMaterialHoardDue(LPCHARACTER ch, DWORD vnum)
	{
		const std::pair<DWORD, DWORD> key(ch->GetPlayerID(), vnum);
		if ((int)ch->CountSpecifyItem(vnum) <= GetPlayerBotMaterialHoardKeep(ch, vnum))
		{
			s_mapPlayerBotMaterialHoardSince.erase(key);
			return false;
		}
		const DWORD now = get_dword_time() != 0 ? get_dword_time() : 1;
		if (s_mapPlayerBotMaterialHoardSince.size() > PLAYERBOT_BAG_MATERIAL_HOARD_SINCE_MAX)
		{
			for (std::map<std::pair<DWORD, DWORD>, DWORD>::iterator it = s_mapPlayerBotMaterialHoardSince.begin();
					it != s_mapPlayerBotMaterialHoardSince.end(); )
			{
				if ((DWORD)(now - it->second) >= 2 * PLAYERBOT_BAG_MATERIAL_HOARD_WAIT_MS)
					s_mapPlayerBotMaterialHoardSince.erase(it++);
				else
					++it;
			}
			if (s_mapPlayerBotMaterialHoardSince.size() > PLAYERBOT_BAG_MATERIAL_HOARD_SINCE_MAX)
				s_mapPlayerBotMaterialHoardSince.clear();
		}
		DWORD& since = s_mapPlayerBotMaterialHoardSince[key];
		if (since == 0)
			since = now;
		return (DWORD)(now - since) >= PLAYERBOT_BAG_MATERIAL_HOARD_WAIT_MS;
	}

	// The units of this stack past the keep, counted in cell order: the first
	// stacks of a kind hold the keep, the rest of the kind is the hoard.
	int GetPlayerBotMaterialHoardUnits(LPCHARACTER ch, LPITEM item)
	{
		const DWORD vnum = item->GetVnum();
		int ahead = 0;
		for (WORD cell = 0; cell < item->GetCell() && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other != item && other->GetCell() == cell && other->GetVnum() == vnum)
				ahead += std::max<int>(1, (int)other->GetCount());
		}
		const int count = std::max<int>(1, (int)item->GetCount());
		const int over = ahead + count - GetPlayerBotMaterialHoardKeep(ch, vnum);
		return std::max(0, std::min(count, over));
	}

	// Refine goods for the Dozorca: never what the bot's own anvil needs, never
	// what the operator put a policy on. For every bot: what came home unsold,
	// and under bag pressure a spare nobody on the market is short of (what
	// used to go down to the safebox). For a bot short of materials: any spare. How many units of the stack go: the whole stack, or - for a
	// hoard that waited its time in vain (MT2009_PLUS_BOT_BAG_CLEANUP_V1) -
	// only what is over the keep. Zero when the stack is no stock at all.
	int GetPlayerBotCraftExchangeUnits(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->IsEquipped() || item->isLocked() || item->IsExchanging() ||
				(item->GetWindow() == INVENTORY && item->GetCell() >= PLAYERBOT_BAG_CELLS) ||	// MT2009_PLUS_BOT_EKW_ROUTE_V1
				(item->GetWindow() != INVENTORY && item->GetWindow() != UPGRADE_INVENTORY) ||
				!IsPlayerBotCraftExchangeVnum(item->GetVnum()) ||
				!IsPlayerBotTradeableMaterial(item))
			return 0;
		// MT2009_PLUS_SIDEKICK_KEEP_VALUABLES_V1: a companion's materials are
		// its owner's, not the Dozorca's.
		if (IsPlayerBotSidekickServing(ch))
			return 0;
		if (GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE ||
				PlayerBotNeedsRefineMaterial(ch, item->GetVnum()))
			return 0;
		const int whole = std::max<int>(1, (int)item->GetCount());
		if (IsPlayerBotCraftUnsold(ch, item))
			return whole;
		// A bot short of materials (its horse training's, MT2009_PLUS_HORSE30_V1)
		// takes every one its anvil does not need - the ones it bought off the
		// counters for this among them.
		if (CountPlayerBotCraftMaterials(ch) < GetPlayerBotCraftMaterialsWanted(ch, false))
			return whole;
		if (IsPlayerBotSurplusMaterial(ch, item) &&
				GetPlayerBotLedgerDemand(item->GetVnum()) == 0 && IsPlayerBotBagUnderPressure(ch))
			return whole;
		// MT2009_PLUS_BOT_BAG_CLEANUP_V1: the hoard past its wait.
		if (IsPlayerBotMaterialHoardDue(ch, item->GetVnum()))
			return GetPlayerBotMaterialHoardUnits(ch, item);
		return 0;
	}

	bool IsPlayerBotCraftExchangeStock(LPCHARACTER ch, LPITEM item)
	{
		return GetPlayerBotCraftExchangeUnits(ch, item) > 0;
	}

	int CollectPlayerBotCraftExchangeStock(LPCHARACTER ch, std::vector<std::pair<LPITEM, int> >* out, long long* fee)
	{
		int units = 0;
		const long long spendable = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch);
		// MT2009_PLUS_BOT_EKW_ROUTE_V1: the bag's refine goods, then the materials' storage's (where a routing bot's go)
		const int scope = PLAYERBOT_BAG_CELLS + (IsPlayerBotEkwPagesOn(ch) ? SPECIAL_INVENTORY_MAX_NUM : 0);
		for (int at = 0; at < scope; ++at)
		{
			const WORD cell = (WORD)(at < PLAYERBOT_BAG_CELLS ? at : at - PLAYERBOT_BAG_CELLS);
			LPITEM item = at < PLAYERBOT_BAG_CELLS ? ch->GetInventoryItem(cell) : ch->Mt2009SpecialGetItem(UPGRADE_INVENTORY, cell);
			if (!item || item->GetCell() != cell ||
					IsPlayerBotSidekickLockedItem(ch, item))	// MT2009_PLUS_SIDEKICK_EQUIP_LOCK_V1
				continue;
			const int count = GetPlayerBotCraftExchangeUnits(ch, item);
			if (count <= 0)
				continue;
			if ((long long)(units + count) * PLAYERBOT_CRAFT_EXCHANGE_FEE > spendable)
				continue;
			units += count;
			if (out)
				out->push_back(std::make_pair(item, count));
		}
		if (fee)
			*fee = (long long)units * PLAYERBOT_CRAFT_EXCHANGE_FEE;
		return units;
	}

	// A bot's materials are its own up to what its horse training (and a
	// Champion's elixirs) still take; past that they are goods.
	bool IsPlayerBotKeptCraftMaterial(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetVnum() != PLAYERBOT_CRAFT_MATERIAL_VNUM)
			return false;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: a Yohara bot's elixir stock (playerbot_yohara_shop.h)
		if (IsPlayerBotYoharaShopKept(ch, item))
			return true;
		const int wanted = GetPlayerBotCraftMaterialsWanted(ch, false); // MT2009_PLUS_HORSE30_V1
		if (wanted <= 0)
			return false;
		// Counted in cell order, like the other stocks: the first `wanted`
		// pieces are kept.
		// MT2009_PLUS_BOT_EKW_ROUTE_V1: the bag's cells first, then the materials' storage (UPGRADE_INVENTORY) - an item
		// there has the whole bag ahead of it
		const bool stored = item->GetWindow() == UPGRADE_INVENTORY;
		int ahead = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && (stored || cell < item->GetCell()); ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other != item && other->GetCell() == cell &&
					other->GetVnum() == PLAYERBOT_CRAFT_MATERIAL_VNUM)
				ahead += (int)other->GetCount();
		}
		for (WORD cell = 0; stored && cell < item->GetCell() && cell < SPECIAL_INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM other = ch->Mt2009SpecialGetItem(UPGRADE_INVENTORY, cell);
			if (other && other != item && other->GetCell() == cell &&
					other->GetVnum() == PLAYERBOT_CRAFT_MATERIAL_VNUM)
				ahead += (int)other->GetCount();
		}
		return ahead < wanted;
	}

	// ------------------------------------------------------------ the market

	// MT2009_PLUS_CRAFT_MATERIAL_MARKET_V1: whether the counters of the world are
	// full of materials (the ledger's supply, as the price curve reads it).
	bool IsPlayerBotCraftMaterialMarketFull()
	{
		return GetPlayerBotOperatorGoodsSupply(PLAYERBOT_CRAFT_MATERIAL_VNUM) >= PLAYERBOT_CRAFT_MATERIAL_MARKET_FULL_UNITS;
	}

	// The materials a bot buys towards: the next step's, or with a full
	// market everything it still wants.
	int GetPlayerBotCraftMaterialBuyTarget(LPCHARACTER ch)
	{
		return GetPlayerBotCraftMaterialsWanted(ch, !IsPlayerBotCraftMaterialMarketFull()); // MT2009_PLUS_HORSE30_V1
	}

	bool WantsPlayerBotCraftMaterialOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || offer->GetVnum() != PLAYERBOT_CRAFT_MATERIAL_VNUM)
			return false;
		const int want = GetPlayerBotCraftMaterialBuyTarget(ch);
		const int have = CountPlayerBotCraftMaterials(ch);
		// A line no bigger than what is missing and one line's worth more: a
		// bot short of five does not buy a stack of two hundred.
		return want > 0 && have < want &&
				(int)offer->GetCount() <= want - have + PLAYERBOT_CRAFT_MATERIAL_LINE_UNITS;
	}

	// Refine goods off a counter, for the Dozorca: a bot short of materials
	// for its next step buys the cheap ones its anvil does not need
	// (operator: "niech skupuja ulepszacze"). Two of them make a material on
	// average, which the market sells at PLAYERBOT_CRAFT_MATERIAL_PRICE.
	const long long PLAYERBOT_CRAFT_GOODS_MAX_UNIT = 20000;
	const int PLAYERBOT_CRAFT_GOODS_PURSE_PERCENT = 20;

	bool WantsPlayerBotCraftGoodsOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || !IsPlayerBotCraftExchangeVnum(offer->GetVnum()) ||
				!IsPlayerBotTradeableMaterial(offer) || PlayerBotNeedsRefineMaterial(ch, offer->GetVnum()))
			return false;
		const int want = GetPlayerBotCraftMaterialsWanted(ch, true); // MT2009_PLUS_HORSE30_V1
		return want > 0 && CountPlayerBotCraftMaterials(ch) < want &&
				CountPlayerBotFreeInventoryCells(ch) > 6;
	}

	bool CanPlayerBotPayForCraftGoods(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long unit = price / std::max<long long>(1, (long long)item->GetCount());
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return unit <= PLAYERBOT_CRAFT_GOODS_MAX_UNIT &&
				price <= spare * PLAYERBOT_CRAFT_GOODS_PURSE_PERCENT / 100;
	}

	bool CanPlayerBotPayForCraftMaterial(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long unit = price / std::max<long long>(1, (long long)item->GetCount());
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		// MT2009_PLUS_OWNER_PRICES_V2: the curve's piece for this line, for a
		// bot of this level (playerbot_town.h), where that is over the cap.
		const long long cap = std::max<long long>(PLAYERBOT_CRAFT_MATERIAL_MAX_BUY *
				GetPlayerBotOperatorLevelPercent((int)ch->GetLevel()) / 100,
				GetPlayerBotOperatorBuyCap(ch, item->GetVnum(), PLAYERBOT_CRAFT_MATERIAL_UNIT_PRICE,
					(DWORD)std::max<int>(1, (int)item->GetCount())));
		// MT2009_PLUS_CRAFT_MATERIAL_MARKET_V1: a full market, a larger share.
		const int purse = IsPlayerBotCraftMaterialMarketFull() ? PLAYERBOT_CRAFT_MATERIAL_FULL_PURSE_PERCENT
				: PLAYERBOT_CRAFT_MATERIAL_PURSE_PERCENT;
		if (unit > cap)
		{
			++s_kPlayerBotCraftStats.materialRefusedCap;
			return false;
		}
		if (price > spare * purse / 100)
		{
			++s_kPlayerBotCraftStats.materialRefusedPurse;
			return false;
		}
		return true;
	}

	// Asked before a market walk without reading a counter.
	bool PlayerBotWantsCraftGoods(LPCHARACTER ch)
	{
		// MT2009_PLUS_HORSE30_V1: the materials of the horse's next training.
		// MT2009_PLUS_BOT_YOHARA_SHOP_V1: and a Champion's materials for Dongan's exchange.
		if (GetPlayerBotHorseTrainingMaterialsWanted(ch) <= 0 && GetPlayerBotYoharaShopMaterialsWanted(ch) <= 0)
			return false;
		const int want = GetPlayerBotCraftMaterialBuyTarget(ch); // MT2009_PLUS_CRAFT_MATERIAL_MARKET_V1
		if (want > 0 && CountPlayerBotCraftMaterials(ch) < want)
		{
			const TPlayerBotMarketLedgerEntry* mats = GetPlayerBotMarketLedgerEntry(PLAYERBOT_CRAFT_MATERIAL_VNUM);
			if (mats && mats->dwSupplyUnits > 0)
				return true;
		}
		return false;
	}

	void NotePlayerBotCraftMaterialBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (vnum == PLAYERBOT_CRAFT_MATERIAL_VNUM)
		{
			++s_kPlayerBotCraftStats.materialsBought;
			s_kPlayerBotCraftStats.materialUnitsBought += count;
			s_kPlayerBotCraftStats.materialYang += (unsigned long long)std::max<long long>(0, price);
			sys_log(0, "PLAYERBOT_CRAFT: material bought pid=%u name=%s units=%u price=%lld have=%d want=%d market_full=%d supply=%u",
					ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "", (unsigned int)count, price,
					CountPlayerBotCraftMaterials(ch), GetPlayerBotCraftMaterialBuyTarget(ch),
					IsPlayerBotCraftMaterialMarketFull() ? 1 : 0,
					(unsigned int)GetPlayerBotOperatorGoodsSupply(PLAYERBOT_CRAFT_MATERIAL_VNUM));
			return;
		}
		else if (IsPlayerBotCraftExchangeVnum(vnum) && GetPlayerBotCraftMaterialsWanted(ch, true) > 0)
			++s_kPlayerBotCraftStats.goodsBought;
		// MT2009_PLUS_HORSE_ECONOMY_V1: every medal bought off a counter is
		// counted (the horse's).
		else if (vnum == PLAYERBOT_HORSE_MEDAL_VNUM)
			++s_kPlayerBotCraftStats.medalsBought;
		else
			return;
		sys_log(0, "PLAYERBOT_CRAFT: bought pid=%u name=%s vnum=%u price=%lld",
				ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "", vnum, price);
	}

	// ------------------------------------------------------------ the errand

	// The Dozorca's side of item_exchange.lua: the goods out, the fee, a roll
	// a piece, the materials in.
	int ExchangePlayerBotCraftGoods(LPCHARACTER ch)
	{
		std::vector<std::pair<LPITEM, int> > goods;
		long long fee = 0;
		const int units = CollectPlayerBotCraftExchangeStock(ch, &goods, &fee);
		if (units <= 0 || CountPlayerBotFreeInventoryCells(ch) < 2)
			return 0;
		int hoardUnits = 0;
		for (size_t i = 0; i < goods.size(); ++i)
		{
			LPITEM item = goods[i].first;
			const int take = goods[i].second;
			// MT2009_PLUS_BOT_BAG_CLEANUP_V1: a hoard gives only what is over
			// its keep; the keep stays in the stack.
			if (take < (int)item->GetCount())
			{
				hoardUnits += take;
				item->SetCount(item->GetCount() - take);
				continue;
			}
			s_setPlayerBotCraftRecalled.erase(item->GetID());
			ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_CRAFT_EXCHANGE");
		}
		if (hoardUnits > 0)
			sys_log(0, "PLAYERBOT_BAG_CLEANUP: hoard to the Dozorca pid=%u name=%s units=%d",
					ch->GetPlayerID(), ch->GetName(), hoardUnits);
		PlayerBotChangeGold(ch, -fee);
		// MT2009_PLUS_EXCHANGE_CHANCE_V1: the players' chance, the world's
		// difficulty (55 in a hundred on every preset; custom's own).
		const int chance = GetPlayerBotExchangeChance(PLAYERBOT_NPC_EXCHANGE_MATERIAL);
		int made = 0;
		for (int i = 0; i < units; ++i)
			if (chance >= 100 || number(1, 100) <= chance)
				++made;
		for (int left = made; left > 0; )
		{
			const int chunk = std::min(left, (int)ITEM_MAX_COUNT);
			ch->AutoGiveItem(PLAYERBOT_CRAFT_MATERIAL_VNUM, chunk, -1, false);
			left -= chunk;
		}
		++s_kPlayerBotCraftStats.exchanges;
		s_kPlayerBotCraftStats.unitsIn += units;
		s_kPlayerBotCraftStats.materialsOut += made;
		sys_log(0, "PLAYERBOT_CRAFT: exchanged pid=%u name=%s stacks=%u units=%d made=%d fee=%lld have=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(),
				(unsigned int)goods.size(), units, made, fee, CountPlayerBotCraftMaterials(ch),
				(long long)ch->GetGold());
		return made;
	}

	void EndPlayerBotCraftErrand(TPlayerBotAIState& state, DWORD dwNow)
	{
		state.bCraftErrand = PLAYERBOT_CRAFT_ERRAND_NONE;
		state.dwNextCraftActionTime = 0;
		state.dwNextCraftCheckTime = dwNow + number(PLAYERBOT_CRAFT_CHECK_MIN_MS, PLAYERBOT_CRAFT_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
	}

	// The tick: the Dozorca's exchange, local to the village the bot stands in
	// (the Dozorca is in all six), walked and done like the Alchemist's.
	bool ManagePlayerBotCraftExchange(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;
		if (state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bVisitingUriel ||
				state.bFishingSession || state.bMarketTrip)
			return false;
		if (state.bCraftErrand == PLAYERBOT_CRAFT_ERRAND_NONE && dwNow < state.dwNextCraftCheckTime)
			return false;

		playerbot_empire_rules::TTownServices svc;
		if (!playerbot_empire_rules::GetTownServices(ch->GetMapIndex(), svc) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				IsPlayerBotHeldForCompany(ch) || ch->GetMyShop() != NULL)
		{
			if (state.bCraftErrand != PLAYERBOT_CRAFT_ERRAND_NONE)
				EndPlayerBotCraftErrand(state, dwNow);
			else
				state.dwNextCraftCheckTime = dwNow + number(PLAYERBOT_CRAFT_CHECK_MIN_MS, PLAYERBOT_CRAFT_CHECK_MAX_MS);
			return false;
		}

		if (state.bCraftErrand == PLAYERBOT_CRAFT_ERRAND_NONE)
		{
			state.dwNextCraftCheckTime = dwNow + number(PLAYERBOT_CRAFT_CHECK_MIN_MS, PLAYERBOT_CRAFT_CHECK_MAX_MS);
			if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
				return false;
			long long fee = 0;
			const int units = CollectPlayerBotCraftExchangeStock(ch, NULL, &fee);
			// MT2009_PLUS_HORSE30_V1: a horse training's materials count.
			const bool shortOfMaterials =
					CountPlayerBotCraftMaterials(ch) < GetPlayerBotCraftMaterialsWanted(ch, true);
			// MT2009_PLUS_BOT_MATS_FLOW_V1: or the swap alone - the materials for a piece its anvil lacks.
			const bool swapDue = IsPlayerBotMatsSwapDue(ch) ||
					IsPlayerBotBeltSwapDue(ch);	// MT2009_PLUS_BOT_BELT_MATS_V1: or a belt maker's metal and pearl
			if ((units <= 0 && !swapDue) || (units < PLAYERBOT_CRAFT_EXCHANGE_MIN_UNITS && !shortOfMaterials && !swapDue) ||
					CountPlayerBotFreeInventoryCells(ch) < 2)
				return false;
			state.bCraftErrand = PLAYERBOT_CRAFT_ERRAND_DOZORCA;
			state.dwNextCraftActionTime = 0;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_CRAFT: going to the Dozorca pid=%u name=%s lv=%d units=%d materials=%d swap=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), units, CountPlayerBotCraftMaterials(ch), swapDue ? 1 : 0);
		}

		const playerbot_empire_rules::TPoint npc = svc.storekeeper;
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), npc.x, npc.y, 0x444f5a4fU, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > PLAYERBOT_STABLE_ARRIVE_DISTANCE)
		{
			if (!MovePlayerBotTownLeg(ch, state, dwNow, approachX, approachY, PLAYERBOT_STABLE_ARRIVE_DISTANCE) &&
					state.bStuckCounter >= 6)
			{
				sys_err("PLAYERBOT_CRAFT: route failed pid=%u name=%s map=%ld to=dozorca from=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
				EndPlayerBotCraftErrand(state, dwNow);
				return false;
			}
			return true;
		}

		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (state.dwNextCraftActionTime == 0)
		{
			state.dwNextCraftActionTime = dwNow + number(3000, 8000);
			return true;
		}
		if (dwNow < state.dwNextCraftActionTime)
			return true;

		// MT2009_PLUS_BOT_MATS_FLOW_V1: the swap before the exchange (its path "any" takes 15 surplus goods for a piece,
		// where the exchange would make ~8 materials of them), and again after it with what the exchange made.
		const int swappedFirst = SwapPlayerBotMaterials(ch, GetPlayerBotMatsCfgVisitMax());
		ExchangePlayerBotCraftGoods(ch);
		if (swappedFirst < GetPlayerBotMatsCfgVisitMax())
			SwapPlayerBotMaterials(ch, GetPlayerBotMatsCfgVisitMax() - swappedFirst);
		// MT2009_PLUS_BOT_BELT_MATS_V1: a belt maker's metal and pearl, out of what is left over every other want.
		SwapPlayerBotBeltMaterials(ch);
		EndPlayerBotCraftErrand(state, dwNow);
		return false;
	}

	void LogPlayerBotCraftCensus()
	{
		// MT2009_PLUS_HORSE_ECONOMY_V1: the horses of every bot - how many at
		// each stage, the medals in bags, and who holds medals it could hand in.
		{
			// MT2009_PLUS_HORSE30_V1: to thirty.
			unsigned stage[8] = { 0 };   // 0, 1-9, 10, 11-19, 20, 21-28, 29, 30
			unsigned bots = 0, medalHolders = 0, canAdvance = 0, canWithMedal = 0, candidates = 0;
			// MT2009_PLUS_BOT_HORSE_PROGRESS_V2: what a horse that could train
			// waits for - the goods, or with the goods in the bag only the yang.
			unsigned shortGoods = 0, shortYang = 0;
			unsigned shortMedals = 0, shortMaterials = 0;	// MT2009_PLUS_BOT_HORSE_AFFORD_V1
			unsigned healthZero = 0, healthLow = 0;
			unsigned long long savingYang = 0;
			unsigned long long medals = 0, horseSum = 0;
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
					it != s_mapPlayerBotAIStates.end(); ++it)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (!ch || ch->GetLevel() < PLAYERBOT_HORSE_REQUIRED_LEVEL)
					continue;
				++bots;
				const int h = ch->GetHorseLevel();
				horseSum += h;
				if (h > 0 && ch->GetHorseHealth() <= 0)
					++healthZero;
				else if (h > 0 && ch->GetHorseHealth() * 2 < ch->GetHorseMaxHealth())
					++healthLow;
				++stage[h <= 0 ? 0 : h < 10 ? 1 : h == 10 ? 2 : h < 20 ? 3 : h == 20 ? 4 : h < 29 ? 5 : h == 29 ? 6 : 7];
				const int held = (int)ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM);
				medals += held;
				if (held > 0)
					++medalHolders;
				const bool can = CanPlayerBotAdvanceHorse(ch);
				if (can)
					++canAdvance;
				if (can && CanPlayerBotPayHorseTraining(ch)) // MT2009_PLUS_HORSE30_V1
					++canWithMedal;
				else if (can)
				{
					const long long saving = GetPlayerBotHorseSavingsGold(ch);
					if (saving > 0)
					{
						++shortYang;
						savingYang += (unsigned long long)saving;
					}
					else
					{
						++shortGoods;
						// MT2009_PLUS_BOT_HORSE_AFFORD_V1: which of the goods
						TPlayerBotHorseTraining next;
						if (GetPlayerBotNextHorseTraining(ch, next))
						{
							if ((int)ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) < next.medals)
								++shortMedals;
							if ((int)ch->CountSpecifyItem(PLAYERBOT_HORSE_TRAINING_MATERIAL_VNUM) < next.materials)
								++shortMaterials;
						}
					}
				}
				if (IsPlayerBotBattleHorseCandidate(ch))
					++candidates;
			}
			sys_log(0, "PLAYERBOT_HORSE: census bots_25plus=%u avg_horse=%.1f stages(0/1-9/10/11-19/20/21-28/29/30)=%u/%u/%u/%u/%u/%u/%u/%u medals_in_bags=%llu medal_holders=%u can_advance=%u can_pay_training=%u short_goods=%u short_yang=%u saving_yang=%llu battle_candidates=%u medals_bought=%u",
					bots, bots ? (double)horseSum / bots : 0.0, stage[0], stage[1], stage[2], stage[3], stage[4], stage[5],
					stage[6], stage[7],
					medals, medalHolders, canAdvance, canWithMedal, shortGoods, shortYang, savingYang,
					candidates, s_kPlayerBotCraftStats.medalsBought);
			// MT2009_PLUS_BOT_HORSE_AFFORD_V1: what the goods short ones lack, and the trainings that paid goods in yang
			// since the core started.
			sys_log(0, "BOT_HORSE_AFFORD: census on=%d yang_pct=%d material_yang=%lld medal_yang=%lld short_goods=%u short_medals=%u "
					"short_materials=%u short_yang=%u afford_trainings=%u afford_yang=%llu health_zero=%u health_low=%u fed=%u revived=%u",
					IsPlayerBotSmallFixOn(SMALLFIX_HORSE) ? 1 : 0, GetPlayerBotHorseTrainingYangPercent(),
					GetPlayerBotHorseAffordMaterialYang(), GetPlayerBotHorseAffordMedalYang(), shortGoods, shortMedals,
					shortMaterials, shortYang, s_dwPlayerBotHorseAffordTrainings, s_ullPlayerBotHorseAffordYang,
					healthZero, healthLow, s_dwPlayerBotHorseAffordFed, s_dwPlayerBotHorseAffordRevived);
		}
		sys_log(0, "PLAYERBOT_CRAFT: census exchanges=%u units_in=%llu materials_out=%llu recalled=%u bought_materials=%u bought_medals=%u bought_goods=%u material_units=%llu material_yang=%llu material_refused_cap=%u material_refused_purse=%u material_supply=%u market_full=%d",
				s_kPlayerBotCraftStats.exchanges,
				s_kPlayerBotCraftStats.unitsIn, s_kPlayerBotCraftStats.materialsOut,
				s_kPlayerBotCraftStats.recalled, s_kPlayerBotCraftStats.materialsBought,
				s_kPlayerBotCraftStats.medalsBought, s_kPlayerBotCraftStats.goodsBought,
				s_kPlayerBotCraftStats.materialUnitsBought, s_kPlayerBotCraftStats.materialYang,
				s_kPlayerBotCraftStats.materialRefusedCap, s_kPlayerBotCraftStats.materialRefusedPurse,
				(unsigned int)GetPlayerBotOperatorGoodsSupply(PLAYERBOT_CRAFT_MATERIAL_VNUM),
				IsPlayerBotCraftMaterialMarketFull() ? 1 : 0);
	}
}

#endif
