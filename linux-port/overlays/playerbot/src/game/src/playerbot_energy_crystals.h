#ifndef __INC_METIN2_PLAYERBOT_ENERGY_CRYSTALS_H__
#define __INC_METIN2_PLAYERBOT_ENERGY_CRYSTALS_H__

// MT2009_PLUS_BOT_ENERGY_CRYSTALS_V1 - the bots make, use and sell Krysztaly Energii (51002) (the owner, 10 November 2026:
// "Naucz boty robic krysztaly energii, uzywac je, a nadmiar krysztalow sprzedawac na rynku. Teraz jest sens przerabiac
// zlom na odlamki energii, a potem na krysztaly energii").
//
// The players' way (MT2009_PLUS_ENERGY_V1, server-patches/energia):
//   * the shards (energia_alchemik.quest): a weapon (no arrow) or an armour / jewel of level 35+, dragged onto the
//     Alchemist (20001) by a player of 35+, is dismantled into 0-15 Odlamki Energii (51001) by the item's level band
//     (35-50 / 51-70 / 71+, the official tables) - no fee. A bot does that since MT2009_PLUS_BOT_ENERGY_SHARDS_V1 with
//     the merchant's scrap (playerbot_energy_shards.h); now only the scrap whose expected shards are worth more than the
//     merchant pays for it (IsPlayerBotEnergyScrapWorthIt) - the expectation of the quest's own table x the shard's sheet
//     price against GetPlayerBotJunkSalePrice;
//   * the crystal (energia_krysztal.quest, "Zloz Krysztal Energii"): 30 shards + 1 000 Yang from level 35; a character's
//     first crystal always succeeds (quest flag energia_krysztal.pierwszy), every next one 30 % - a failed try takes the
//     shards and the Yang too. Its value (1/3/5/7/10 %) is blend.txt's, drawn when the item is made (Blend_Item_set_value
//     in ITEM_MANAGER::CreateItem - the bot's AutoGiveItem goes the same way);
//   * the use: POINT_ENERGY for 7200 s of play (AFFECT_BLEND), the worn items' bonuses up by the value; used again while
//     it runs only a stronger one is taken (MiksturyMayRefresh).
//
// The bots:
//   * craft at the Alchemist's counter (ManagePlayerBotAlchemist, playerbot_town.h) - the same visit as the scrap, or
//     its own on the Alchemist's 5-10 minute clock when WantsPlayerBotEnergyCrystalCraft - while the crystals held (the
//     bag and the own counter) are under the target (the reserve + m2_bot_energy_craft_extra for the market), with the
//     shards over the belt maker's keep, the quest's Yang and the quest's odds, the first one sure;
//   * keep m2_bot_energy_craft_shards (60) shards off the counter while short of crystals (their keep for the next
//     visit, added to the belt keep, GetPlayerBotEnergyShardKeep); the rest goes up in packs of ten as before, up to
//     the world's m2_bot_energy_shard_market (1000) on the bots' counters - a supply for the Kolekcjoner Najemnikow's
//     1000 shards;
//   * use one while hunting (UsePlayerBotBoosters, playerbot_consumables.h) from level m2_bot_energy_min_level (35, the
//     crystal's own level) - the strongest held, never while the energy runs;
//   * keep ceil(m2_bot_energy_reserve_h / 2) crystals (the next hours of their own use; 4 h - 2 crystals) and list the
//     rest at the sheet's price (PLAYERBOT_EXTRA_MATERIAL_PRICES: 3 000 000 - 100 shards, the expected cost of one at
//     30 %, through the yang-rate curve like the shard's 30 000), one crystal a line, through the lada (an ordinary
//     kind there - the keep is GetPlayerBotStallBaseKeepRules') or the visit, up to m2_bot_energy_crystal_market (300)
//     on the bots' counters of the world. Never the merchant's (IsPlayerBotJunkItem).
//
// Flags (event flags; 0 - the default): m2_bot_energy_off (all of this, the scrap's worth test included),
// m2_bot_energy_craft_off, m2_bot_energy_use_off, m2_bot_energy_sell_off (crystals never listed), m2_bot_energy_value_off
// (the scrap's worth test off: every scrap piece goes to the Alchemist as before), m2_bot_energy_reserve_h (4, 1..48),
// m2_bot_energy_craft_extra (2, 0..50; -1: none), m2_bot_energy_craft_shards (60, 30..600; -1: none),
// m2_bot_energy_shard_market (1000, 10..20000), m2_bot_energy_crystal_market (300, 1..20000), m2_bot_energy_min_level
// (35, 35..120).
//
// Log: "PLAYERBOT_ENERGY:" crafted / used (sys_log 0), the census "PLAYERBOT_ENERGY_CENSUS:" every 10 minutes.
//
// An implementation fragment in the sense playerbot_types.h describes: included once, from playerbot_manager.cpp, right
// after playerbot_energy_shards.h and before playerbot_economy.h.

#include <initializer_list>
#include <unordered_map>

namespace
{
	// Defined further down the unit (playerbot_economy.h, playerbot_town.h).
	long long GetPlayerBotJunkSalePrice(LPITEM item);
	DWORD GetPlayerBotMaterialAskingBase(DWORD dwVnum);

	const DWORD PLAYERBOT_ENERGY_CRYSTAL_VNUM = 51002;
	const int PLAYERBOT_ENERGY_CRYSTAL_SHARDS = 30;			// energia_krysztal.quest: need
	const long long PLAYERBOT_ENERGY_CRYSTAL_FEE = 1000;	// energia_krysztal.quest: charge
	const int PLAYERBOT_ENERGY_CRYSTAL_CHANCE = 30;			// every crystal after the first
	const int PLAYERBOT_ENERGY_CRYSTAL_HOURS = 2;			// 7200 s a crystal
	const char* const PLAYERBOT_ENERGY_FIRST_FLAG = "energia_krysztal.pierwszy";
	const DWORD PLAYERBOT_ENERGY_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ENERGY_MARKET_SCAN_MS = 60 * 1000;
	const DWORD PLAYERBOT_ENERGY_UPTIME_SAMPLE_MS = 60 * 1000;
	const int PLAYERBOT_ENERGY_CRAFTS_A_VISIT = 20;			// at most this many tries at one counter

	struct TPlayerBotEnergyCfg
	{
		bool on, craft, use, sell, value;
		int reserveH, craftExtra, craftShards, shardMarket, crystalMarket, minLevel;
		TPlayerBotEnergyCfg() : on(true), craft(true), use(true), sell(true), value(true), reserveH(4), craftExtra(2),
				craftShards(60), shardMarket(PLAYERBOT_ENERGY_SHARD_MARKET_UNITS), crystalMarket(300), minLevel(35) {}
	};
	TPlayerBotEnergyCfg s_kPlayerBotEnergyCfg;

	const TPlayerBotEnergyCfg& GetPlayerBotEnergyCfg()
	{
		static DWORD s_dwAt = 0;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			TPlayerBotEnergyCfg& c = s_kPlayerBotEnergyCfg;
			const TPlayerBotEnergyCfg was = c;
			c.on = q.GetEventFlag("m2_bot_energy_off") == 0;
			c.craft = c.on && q.GetEventFlag("m2_bot_energy_craft_off") == 0;
			c.use = c.on && q.GetEventFlag("m2_bot_energy_use_off") == 0;
			c.sell = c.on && q.GetEventFlag("m2_bot_energy_sell_off") == 0;
			c.value = c.on && q.GetEventFlag("m2_bot_energy_value_off") == 0;
			auto value = [&q](const char* flag, int def, int lo, int hi) {
				const int v = q.GetEventFlag(flag);
				return v == 0 ? def : (v < 0 ? -1 : std::max(lo, std::min(hi, v)));
			};
			c.reserveH = std::max(1, value("m2_bot_energy_reserve_h", 4, 1, 48));
			c.craftExtra = std::max(0, value("m2_bot_energy_craft_extra", 2, 0, 50));
			c.craftShards = std::max(0, value("m2_bot_energy_craft_shards", 60, PLAYERBOT_ENERGY_CRYSTAL_SHARDS, 600));
			c.shardMarket = std::max(10, value("m2_bot_energy_shard_market", PLAYERBOT_ENERGY_SHARD_MARKET_UNITS, 10, 20000));
			c.crystalMarket = std::max(1, value("m2_bot_energy_crystal_market", 300, 1, 20000));
			c.minLevel = std::max(35, value("m2_bot_energy_min_level", 35, 35, 120));
			if (was.on != c.on || was.craft != c.craft || was.use != c.use || was.sell != c.sell || was.value != c.value ||
					was.reserveH != c.reserveH || was.craftExtra != c.craftExtra || was.craftShards != c.craftShards ||
					was.shardMarket != c.shardMarket || was.crystalMarket != c.crystalMarket || was.minLevel != c.minLevel)
				sys_log(0, "PLAYERBOT_ENERGY: config on=%d craft=%d use=%d sell=%d value=%d reserve_h=%d craft_extra=%d "
						"craft_shards=%d shard_market=%d crystal_market=%d min_level=%d",
						c.on ? 1 : 0, c.craft ? 1 : 0, c.use ? 1 : 0, c.sell ? 1 : 0, c.value ? 1 : 0, c.reserveH,
						c.craftExtra, c.craftShards, c.shardMarket, c.crystalMarket, c.minLevel);
		}
		return s_kPlayerBotEnergyCfg;
	}

	bool IsPlayerBotEnergyCrystalVnum(DWORD vnum)
	{
		return vnum == PLAYERBOT_ENERGY_CRYSTAL_VNUM;
	}

	// The world's cap of shards on the bots' counters (was PLAYERBOT_ENERGY_SHARD_MARKET_UNITS alone).
	int GetPlayerBotEnergyShardMarketUnits()
	{
		return GetPlayerBotEnergyCfg().shardMarket;
	}

	// ------------------------------------------------------------------------------------------------ the census
	struct TPlayerBotEnergyCensus
	{
		unsigned int scrapPieces = 0, scrapEmpty = 0, scrapSkippedValue = 0, crafts = 0, crystalsMade = 0, firstCrystals = 0,
				craftsFailed = 0, crystalsUsed = 0, useRefused = 0, listedLines = 0, listedUnits = 0, soldLines = 0, soldUnits = 0;
		unsigned long long shardsMade = 0, shardsSpent = 0;
		long long craftYang = 0, soldYang = 0;
		unsigned int uptimeSamples = 0, uptimeOn = 0;
	};
	TPlayerBotEnergyCensus s_kPlayerBotEnergyCensus;	// since the last census line
	TPlayerBotEnergyCensus s_kPlayerBotEnergyTotal;	// since the core started

	void NotePlayerBotEnergyDismantled(int pieces, int empty, int shards)
	{
		for (TPlayerBotEnergyCensus* k : { &s_kPlayerBotEnergyCensus, &s_kPlayerBotEnergyTotal })
		{
			k->scrapPieces += (unsigned int)std::max(0, pieces);
			k->scrapEmpty += (unsigned int)std::max(0, empty);
			k->shardsMade += (unsigned long long)std::max(0, shards);
		}
	}

	// A line of the bot's own put up by the visit (BotOfflinePrepareLine's add, playerbot_offline_shop.h).
	void NotePlayerBotEnergyLineListed(DWORD vnum, int units)
	{
		if (!IsPlayerBotEnergyCrystalVnum(vnum))
			return;
		for (TPlayerBotEnergyCensus* k : { &s_kPlayerBotEnergyCensus, &s_kPlayerBotEnergyTotal })
		{
			++k->listedLines;
			k->listedUnits += (unsigned int)std::max(0, units);
		}
	}

	// A crystal line of a bot's counter sold (BotOfflineDrainSales).
	void NotePlayerBotEnergyLineSold(DWORD vnum, int units, long long price)
	{
		if (!IsPlayerBotEnergyCrystalVnum(vnum))
			return;
		for (TPlayerBotEnergyCensus* k : { &s_kPlayerBotEnergyCensus, &s_kPlayerBotEnergyTotal })
		{
			++k->soldLines;
			k->soldUnits += (unsigned int)std::max(0, units);
			k->soldYang += price;
		}
	}

	// The bots' counters of the world: the shard and crystal units on them, counted at most once a minute.
	struct TPlayerBotEnergyMarket
	{
		DWORD at = 0;
		int shardUnits = 0, shardShops = 0, crystalUnits = 0, crystalShops = 0;
	};
	TPlayerBotEnergyMarket s_kPlayerBotEnergyMarket;

	const TPlayerBotEnergyMarket& GetPlayerBotEnergyMarket(DWORD now)
	{
		TPlayerBotEnergyMarket& m = s_kPlayerBotEnergyMarket;
		if (m.at != 0 && now - m.at < PLAYERBOT_ENERGY_MARKET_SCAN_MS)
			return m;
		m.at = now ? now : 1;
		m.shardUnits = m.shardShops = m.crystalUnits = m.crystalShops = 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		for (const auto& [owner, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || shop->GetDuration() == 0 ||
					!CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID()))
				continue;
			int shards = 0, crystals = 0;
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line)
					continue;
				if (IsPlayerBotEnergyShardVnum(line->GetInfo().vnum))
					shards += (int)line->GetInfo().count;
				else if (IsPlayerBotEnergyCrystalVnum(line->GetInfo().vnum))
					crystals += (int)line->GetInfo().count;
			}
			m.shardUnits += shards;
			m.crystalUnits += crystals;
			if (shards > 0)
				++m.shardShops;
			if (crystals > 0)
				++m.crystalShops;
		}
#endif
		return m;
	}

	// The crystals on this bot's own counter (any channel: the shop handle is on every core).
	int CountPlayerBotEnergyCrystalsOnCounter(LPCHARACTER ch)
	{
		int units = 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (!ch)
			return 0;
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		if (!shop)
			return 0;
		for (const auto& [id, line] : shop->GetItems())
			if (line && IsPlayerBotEnergyCrystalVnum(line->GetInfo().vnum))
				units += (int)line->GetInfo().count;
#else
		(void)ch;
#endif
		return units;
	}

	int CountPlayerBotEnergyCrystals(LPCHARACTER ch)
	{
		return ch && ch->IsItemLoaded() ? (int)ch->CountSpecifyItem(PLAYERBOT_ENERGY_CRYSTAL_VNUM) : 0;
	}

	bool IsPlayerBotEnergyUser(LPCHARACTER ch)
	{
		const TPlayerBotEnergyCfg& c = GetPlayerBotEnergyCfg();
		return ch && c.on && (int)ch->GetLevel() >= c.minLevel && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	// The crystals a bot keeps for its own next hours (none under the level: those are all goods).
	int GetPlayerBotEnergyCrystalReserve(LPCHARACTER ch)
	{
		if (!IsPlayerBotEnergyUser(ch) || !GetPlayerBotEnergyCfg().use)
			return 0;
		const int h = GetPlayerBotEnergyCfg().reserveH;
		return (h + PLAYERBOT_ENERGY_CRYSTAL_HOURS - 1) / PLAYERBOT_ENERGY_CRYSTAL_HOURS;
	}

	// What the counters may not have of the bag's crystals (GetPlayerBotStallBaseKeepRules): the reserve, or every one
	// while selling is off; the world's crystal cap full - every one too, the rest waits in the bag.
	int GetPlayerBotEnergyCrystalKeep(LPCHARACTER ch)
	{
		const TPlayerBotEnergyCfg& c = GetPlayerBotEnergyCfg();
		if (!ch)
			return 0;
		// (the count itself, never more: the lada's take-home of a kind short of its keep stays quiet)
		if (!c.sell || GetPlayerBotEnergyMarket(get_dword_time()).crystalUnits >= c.crystalMarket)
			return CountPlayerBotEnergyCrystals(ch);
		return GetPlayerBotEnergyCrystalReserve(ch);
	}

	int GetPlayerBotEnergyCrystalsForSale(LPCHARACTER ch)
	{
		return std::max(0, CountPlayerBotEnergyCrystals(ch) - GetPlayerBotEnergyCrystalKeep(ch));
	}

	// The crystals this bot still makes: its reserve and the extra for the market, less what the bag and its own counter
	// hold - a crystal sold is made again, a crystal standing is not made twice.
	int GetPlayerBotEnergyCrystalDeficit(LPCHARACTER ch)
	{
		const TPlayerBotEnergyCfg& c = GetPlayerBotEnergyCfg();
		if (!ch || !c.craft || (int)ch->GetLevel() < std::max(c.minLevel, PLAYERBOT_ENERGY_MIN_LEVEL) ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		int target = GetPlayerBotEnergyCrystalReserve(ch);
		if (c.sell && GetPlayerBotEnergyMarket(get_dword_time()).crystalUnits < c.crystalMarket)
			target += c.craftExtra;
		return std::max(0, target - CountPlayerBotEnergyCrystals(ch) - CountPlayerBotEnergyCrystalsOnCounter(ch));
	}

	// The shards held off the counter for the next crystals, beside the belt maker's keep (GetPlayerBotEnergyShardKeep).
	int GetPlayerBotEnergyCraftShardKeep(LPCHARACTER ch)
	{
		const int keep = GetPlayerBotEnergyCfg().craftShards;
		if (keep <= 0 || GetPlayerBotEnergyCrystalDeficit(ch) <= 0)
			return 0;
		return keep;
	}

	// The tries the shards (over the belt keep) and the purse pay for, the deficit at most.
	int GetPlayerBotEnergyCraftTries(LPCHARACTER ch)
	{
		const int deficit = GetPlayerBotEnergyCrystalDeficit(ch);
		if (deficit <= 0)
			return 0;
		const int shards = CountPlayerBotEnergyShards(ch) - GetPlayerBotEnergyBeltShardKeep(ch);
		const long long byGold = (long long)ch->GetGold() / PLAYERBOT_ENERGY_CRYSTAL_FEE;
		return (int)std::max<long long>(0, std::min<long long>(std::min(shards / PLAYERBOT_ENERGY_CRYSTAL_SHARDS,
				PLAYERBOT_ENERGY_CRAFTS_A_VISIT), byGold));
	}

	// Asked on the Alchemist's clock (ManagePlayerBotAlchemist): a crystal to make.
	bool WantsPlayerBotEnergyCrystalCraft(LPCHARACTER ch)
	{
		return ch && ch->IsItemLoaded() && GetPlayerBotEnergyCraftTries(ch) > 0;
	}

	// At the Alchemist's counter, after the scrap: energia_krysztal.quest's tries, one after another while the crystals
	// are short and the shards and the Yang last - the fee and the shards taken for every try, the first crystal sure.
	int CraftPlayerBotEnergyCrystals(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return 0;
		int made = 0, tries = 0, failed = 0, first = 0;
		long long yang = 0;
		for (int guard = 0; guard < PLAYERBOT_ENERGY_CRAFTS_A_VISIT; ++guard)
		{
			if (GetPlayerBotEnergyCraftTries(ch) <= 0)
				break;
			// The crystal needs a cell unless it joins a stack of its value; one free cell is asked always.
			if (ch->GetEmptyInventory(1) < 0)
				break;
			PlayerBotChangeGold(ch, -PLAYERBOT_ENERGY_CRYSTAL_FEE);
			ch->RemoveSpecifyItem(PLAYERBOT_ENERGY_SHARD_VNUM, PLAYERBOT_ENERGY_CRYSTAL_SHARDS);
			yang += PLAYERBOT_ENERGY_CRYSTAL_FEE;
			++tries;
			bool ok = false;
			if (ch->GetQuestFlag(PLAYERBOT_ENERGY_FIRST_FLAG) == 0)
			{
				ch->SetQuestFlag(PLAYERBOT_ENERGY_FIRST_FLAG, 1);
				ok = true;
				++first;
			}
			else
				ok = number(1, 100) <= PLAYERBOT_ENERGY_CRYSTAL_CHANCE;
			if (!ok)
			{
				++failed;
				continue;
			}
			LPITEM crystal = ch->AutoGiveItem(PLAYERBOT_ENERGY_CRYSTAL_VNUM, 1, -1, false);
			if (crystal)
				++made;
		}
		if (tries == 0)
			return 0;
		for (TPlayerBotEnergyCensus* k : { &s_kPlayerBotEnergyCensus, &s_kPlayerBotEnergyTotal })
		{
			k->crafts += (unsigned int)tries;
			k->crystalsMade += (unsigned int)made;
			k->craftsFailed += (unsigned int)failed;
			k->firstCrystals += (unsigned int)first;
			k->shardsSpent += (unsigned long long)tries * PLAYERBOT_ENERGY_CRYSTAL_SHARDS;
			k->craftYang += yang;
		}
		sys_log(0, "PLAYERBOT_ENERGY: crystals at the Alchemist pid=%u name=%s level=%u tries=%d made=%d failed=%d first=%d "
				"yang=%lld shards_left=%d crystals=%d on_counter=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), tries, made, failed, first, yang,
				CountPlayerBotEnergyShards(ch), CountPlayerBotEnergyCrystals(ch), CountPlayerBotEnergyCrystalsOnCounter(ch),
				(long long)ch->GetGold());
		return made;
	}

	// ------------------------------------------------------------------------------------------------ the scrap's worth
	// The expected shards of a piece of this level, by energia_alchemik.quest's table (r = 1..100, getItemNum).
	double GetPlayerBotEnergyScrapExpectedShards(int levelLimit)
	{
		static const int s_acc[3][10] = {
			{ 30, 55, 70, 80, 90, 95, 97, 98, 99, 100 },
			{ 20, 40, 60, 75, 85, 91, 96, 98, 99, 100 },
			{ 10, 25, 45, 65, 80, 88, 94, 97, 99, 100 },
		};
		static const int s_num[10] = { 0, 1, 2, 3, 4, 6, 8, 10, 12, 15 };
		const int band = levelLimit <= 50 ? 0 : (levelLimit <= 70 ? 1 : 2);
		int sum = 0;
		for (int r = 1; r <= 100; ++r)
			for (int i = 0; i < 10; ++i)
				if (r < s_acc[band][i])
				{
					sum += s_num[i];
					break;
				}
		return sum / 100.0;
	}

	// The Alchemist takes the piece only when its expected shards, at the shard's sheet price, beat the merchant's yang.
	bool IsPlayerBotEnergyScrapWorthIt(LPCHARACTER ch, LPITEM item, bool note)
	{
		if (!ch || !item)
			return false;
		const TPlayerBotEnergyCfg& c = GetPlayerBotEnergyCfg();
		if (!c.on)
			return false;
		if (!c.value)
			return true;
		const double shards = GetPlayerBotEnergyScrapExpectedShards(item->GetLevelLimit());
		const double worth = shards * (double)GetPlayerBotMaterialAskingBase(PLAYERBOT_ENERGY_SHARD_VNUM);
		const long long npc = GetPlayerBotJunkSalePrice(item);
		if (worth > (double)npc)
			return true;
		if (note)
		{
			++s_kPlayerBotEnergyCensus.scrapSkippedValue;
			++s_kPlayerBotEnergyTotal.scrapSkippedValue;
		}
		return false;
	}

	// ------------------------------------------------------------------------------------------------ the use
	bool IsPlayerBotEnergyRunning(LPCHARACTER ch)
	{
		return ch && ch->FindAffect(AFFECT_BLEND, POINT_ENERGY) != NULL;
	}

	// While hunting (UsePlayerBotBoosters): the strongest crystal of the bag when no energy runs. The same or a weaker
	// one would be refused by the engine anyway; a stronger one is not worth the reserve while one runs.
	bool UsePlayerBotEnergyCrystal(LPCHARACTER ch)
	{
		const TPlayerBotEnergyCfg& c = GetPlayerBotEnergyCfg();
		if (!c.use || !IsPlayerBotEnergyUser(ch) || !ch->IsItemLoaded() || IsPlayerBotEnergyRunning(ch))
			return false;
		LPITEM best = NULL;
		long bestValue = -1;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotEnergyCrystalVnum(item->GetVnum()) || item->isLocked() ||
					GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE)
				continue;
			if ((long)item->GetSocket(1) > bestValue)
			{
				best = item;
				bestValue = (long)item->GetSocket(1);
			}
		}
		if (!best)
			return false;
		const WORD cell = best->GetCell();
		if (!ch->UseItem(TItemPos(INVENTORY, cell)) || !IsPlayerBotEnergyRunning(ch))
		{
			++s_kPlayerBotEnergyCensus.useRefused;
			++s_kPlayerBotEnergyTotal.useRefused;
			return false;
		}
		++s_kPlayerBotEnergyCensus.crystalsUsed;
		++s_kPlayerBotEnergyTotal.crystalsUsed;
		sys_log(0, "PLAYERBOT_ENERGY: crystal used pid=%u name=%s level=%u value=%ld left=%d map=%ld",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), bestValue,
				CountPlayerBotEnergyCrystals(ch), ch->GetMapIndex());
		return true;
	}

	// ------------------------------------------------------------------------------------------------ the uptime
	std::unordered_map<DWORD, DWORD> s_mapPlayerBotEnergySampleAt;

	void LogPlayerBotEnergyCensus(DWORD now)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = now ? now : 1;
			return;
		}
		if (now - s_dwAt < PLAYERBOT_ENERGY_CENSUS_MS)
			return;
		s_dwAt = now ? now : 1;
		const TPlayerBotEnergyCensus& k = s_kPlayerBotEnergyCensus;
		const TPlayerBotEnergyCensus& t = s_kPlayerBotEnergyTotal;
		const TPlayerBotEnergyMarket& m = GetPlayerBotEnergyMarket(now);
		const int uptime = k.uptimeSamples ? (int)(k.uptimeOn * 100ULL / k.uptimeSamples) : -1;
		sys_log(0, "PLAYERBOT_ENERGY_CENSUS: scrap_pieces=%u scrap_empty=%u scrap_to_merchant_by_value=%u shards_from_scrap=%llu "
				"crafts=%u crystals_made=%u failed=%u first=%u shards_spent=%llu craft_yang=%lld used=%u use_refused=%u "
				"listed_lines=%u listed_units=%u sold_lines=%u sold_units=%u sold_yang=%lld "
				"counters_shards=%d shard_shops=%d counters_crystals=%d crystal_shops=%d uptime_pct=%d samples=%u min_level=%d "
				"total_shards_from_scrap=%llu total_crystals_made=%u total_used=%u total_sold_units=%u",
				k.scrapPieces, k.scrapEmpty, k.scrapSkippedValue, k.shardsMade,
				k.crafts, k.crystalsMade, k.craftsFailed, k.firstCrystals, k.shardsSpent, k.craftYang, k.crystalsUsed, k.useRefused,
				k.listedLines, k.listedUnits, k.soldLines, k.soldUnits, k.soldYang,
				m.shardUnits, m.shardShops, m.crystalUnits, m.crystalShops, uptime, k.uptimeSamples, GetPlayerBotEnergyCfg().minLevel,
				t.shardsMade, t.crystalsMade, t.crystalsUsed, t.soldUnits);
		s_kPlayerBotEnergyCensus = TPlayerBotEnergyCensus();
		if (s_mapPlayerBotEnergySampleAt.size() > 50000)
			s_mapPlayerBotEnergySampleAt.clear();
	}

	// Once a minute a bot of the energy level says whether its energy runs; the census line reads the share.
	void SamplePlayerBotEnergyUptime(LPCHARACTER ch, DWORD now)
	{
		LogPlayerBotEnergyCensus(now);
		if (!IsPlayerBotEnergyUser(ch) || ch->IsDead())
			return;
		DWORD& at = s_mapPlayerBotEnergySampleAt[ch->GetPlayerID()];
		if (at != 0 && now - at < PLAYERBOT_ENERGY_UPTIME_SAMPLE_MS)
			return;
		at = now ? now : 1;
		++s_kPlayerBotEnergyCensus.uptimeSamples;
		++s_kPlayerBotEnergyTotal.uptimeSamples;
		if (IsPlayerBotEnergyRunning(ch))
		{
			++s_kPlayerBotEnergyCensus.uptimeOn;
			++s_kPlayerBotEnergyTotal.uptimeOn;
		}
	}
}

#endif
