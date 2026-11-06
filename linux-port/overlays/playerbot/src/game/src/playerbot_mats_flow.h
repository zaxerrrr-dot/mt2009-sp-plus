#ifndef __INC_METIN2_PLAYERBOT_MATS_FLOW_H__
#define __INC_METIN2_PLAYERBOT_MATS_FLOW_H__

// MT2009_PLUS_BOT_MATS_FLOW_V1 - the bots' refine materials on the move (the owner, 6 November 2026, the 4-server analysis,
// decision B):
//   "Boty moga wymieniac 15 materialow rzemieslniczych na dowolny ulepszacz, ktory leci na mapach do 75 poziomu. Czyli
//    zeby orka, rybie osci itd. - to, co im brakuje."
//   Bots with spare Orc Teeth (their storage boxes too) sell them on the market; bots missing them go and farm them "o ile
//   maja wystarczajaco niski lvl, aby te kly jeszcze lecialy"; the belts' materials (copper, the pearls) come out of the
//   boxes to the market and to the belt makers.
//
//   * The swap (bot-only, at the Dozorca 9005 - the NPC whose exchange makes the Materialy Rzemieslnicze 30378 out of refine
//     goods, playerbot_craft_exchange.h): PLAYERBOT_MATS_SWAP_RATE (15) Materialy Rzemieslnicze for 1 refine material the
//     next step of a worn piece lacks (its recipe's count over the bag, the Biologist's share aside), when that material
//     is "of the maps up to 75": the drop knowledge (playerbot_dropknow.h) knows a monster of level PLAYERBOT_MATS_SWAP_MAX_LEVEL
//     (75) or lower that drops it on a map that is no dungeon's. Up to PLAYERBOT_MATS_SWAP_VISIT_MAX (4) pieces a visit.
//     What the swap still needs counts as the bot's wanted materials (GetPlayerBotCraftMaterialsWanted): its 30378 stay
//     off its counter, the Dozorca takes its spare refine goods for more, the market's 30378 are bought for it. A Champion's
//     materials for Dongan's elixirs (GetPlayerBotYoharaShopMaterialsWanted) are never swapped away.
//   * The scarce materials' boxes (PLAYERBOT_MATS_SCARCE_VNUMS, "30006" - Zab Orka): at a safebox visit of a bot with a
//     counter, before the box's ordinary pass (which takes six things a visit from the first cells, so a tooth deep in a
//     box never came out), a stack of it comes out for the counter while the bot's teeth (bag + box) are over its keep:
//     its anvil's reserve, and the Biologist's share only while the bot still gets the specimen's drop (the level gap -
//     a bot past it would never finish the row). The counter lists what is over the anvil's reserve as before; the price
//     is the market's (decision E is another pass).
//   * The farm: a bot whose need pass (playerbot_dropknow.h) cannot pay the market's last ask for a material it lacks
//     (lack x ask over PLAYERBOT_MATS_AFFORD_PURSE_PCT of its spare purse) takes the drop knowledge's source instead of
//     "market"; and a farm order of a material of PLAYERBOT_MATS_FARM_VNUMS ("30006") names the bot's hunting map
//     (GetPlayerBotFrontierMapForLevelRaw, after a guild's errand) - only while the drop still pays at its level
//     (PERCENT_LVDELTA >= PLAYERBOT_MATS_FARM_MIN_DROP_PCT, 50), the map is a frontier this core hosts, the bot is still
//     short and at most PLAYERBOT_MATS_FARM_MAX (200) bots of the core farm so at once.
//   * The belts' materials (the recipes' metals and pearls, PLAYERBOT_BELT_RECIPES): at the same safebox visit a belt
//     maker takes out what its target recipe lacks; a bot with a counter takes out what is over its own keep (the crafts'
//     keep, the anvil's, its jewellery's sockets) while its bag holds none of it over the keep - for the counter.
//
// Switches (event flags, looked at once a second): m2_bot_mats_off 1 - all of it; m2_bot_mats_swap_off,
// m2_bot_mats_scarce_off, m2_bot_mats_farm_off, m2_bot_mats_belts_off - one part. The numbers: env (read once) as above,
// plus PLAYERBOT_MATS_BOX_STACKS (3: the stacks a visit takes this way).
// The log: BOT_MATS lines - eligible (the swap's materials, at each drop-knowledge build), swap (a bot's swap), farm (a bot's
// farm map, once an order), status (every 10 minutes beside BOT_DROPKNOW's) - and the safebox's own "safebox withdraw ...
// reason=mats_scarce / mats_belt_craft / mats_belt_market" lines.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_dropki.h, in the anonymous namespace; its
// hooks are declared where they are asked (playerbot_travel.h, playerbot_town.h, playerbot_craft_exchange.h,
// playerbot_dropknow.h).

namespace
{
	const DWORD PLAYERBOT_MATS_CRAFT_VNUM = 30378;	// Materialy Rzemieslnicze
	const DWORD PLAYERBOT_MATS_NEED_CACHE_MS = 60 * 1000;
	const DWORD PLAYERBOT_MATS_FARM_CACHE_MS = 30 * 1000;
	const DWORD PLAYERBOT_MATS_FARMER_WINDOW_MS = 10 * 60 * 1000;

	struct TPlayerBotMatsCfg
	{
		bool read;
		int swapRate, swapMaxLevel, swapVisitMax, boxStacks, farmMinDropPct, farmMax, affordPurse;
		std::set<DWORD> scarce, farmVnums;
		TPlayerBotMatsCfg() : read(false), swapRate(15), swapMaxLevel(75), swapVisitMax(4), boxStacks(3), farmMinDropPct(50),
				farmMax(200), affordPurse(60) {}
	};
	TPlayerBotMatsCfg s_kPlayerBotMatsCfg;

	void ReadPlayerBotMatsVnums(const char* name, const char* def, std::set<DWORD>& out)
	{
		std::vector<long> list;
		ReadPlayerBotYoharaEnvList(name, def, list);
		out.clear();
		for (size_t i = 0; i < list.size(); ++i)
			if (list[i] > 0)
				out.insert((DWORD)list[i]);
	}

	const TPlayerBotMatsCfg& GetPlayerBotMatsCfg()
	{
		TPlayerBotMatsCfg& c = s_kPlayerBotMatsCfg;
		if (!c.read)
		{
			c.read = true;
			c.swapRate = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_SWAP_RATE", 15, 2, 200);
			c.swapMaxLevel = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_SWAP_MAX_LEVEL", 75, 1, 120);
			c.swapVisitMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_SWAP_VISIT_MAX", 4, 1, 50);
			c.boxStacks = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_BOX_STACKS", 3, 0, PLAYERBOT_SAFEBOX_WITHDRAW_MAX);
			c.farmMinDropPct = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_FARM_MIN_DROP_PCT", 50, 1, 100);
			c.farmMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_FARM_MAX", 200, 0, 5000);
			c.affordPurse = ReadPlayerBotYoharaEnvInt("PLAYERBOT_MATS_AFFORD_PURSE_PCT", 60, 1, 100);
			ReadPlayerBotMatsVnums("PLAYERBOT_MATS_SCARCE_VNUMS", "30006", c.scarce);
			ReadPlayerBotMatsVnums("PLAYERBOT_MATS_FARM_VNUMS", "30006", c.farmVnums);
			sys_log(0, "BOT_MATS: config swap_rate=%d swap_max_level=%d swap_visit_max=%d box_stacks=%d farm_min_drop_pct=%d "
					"farm_max=%d afford_purse_pct=%d scarce=%u farm_vnums=%u", c.swapRate, c.swapMaxLevel, c.swapVisitMax,
					c.boxStacks, c.farmMinDropPct, c.farmMax, c.affordPurse, (unsigned int)c.scarce.size(),
					(unsigned int)c.farmVnums.size());
		}
		return c;
	}

	enum EPlayerBotMatsPart
	{
		MATS_PART_SWAP = 0,
		MATS_PART_SCARCE,
		MATS_PART_FARM,
		MATS_PART_BELTS,
		MATS_PART_COUNT
	};

	// The event flags, once a second.
	bool IsPlayerBotMatsOff(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[MATS_PART_COUNT] = { false, false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_mats_off") != 0;
			s_abOff[MATS_PART_SWAP] = all || q.GetEventFlag("m2_bot_mats_swap_off") != 0;
			s_abOff[MATS_PART_SCARCE] = all || q.GetEventFlag("m2_bot_mats_scarce_off") != 0;
			s_abOff[MATS_PART_FARM] = all || q.GetEventFlag("m2_bot_mats_farm_off") != 0;
			s_abOff[MATS_PART_BELTS] = all || q.GetEventFlag("m2_bot_mats_belts_off") != 0;
		}
		return part < 0 || part >= MATS_PART_COUNT || s_abOff[part];
	}

	struct TPlayerBotMatsStats
	{
		unsigned swaps, swapUnits, swapBots;
		unsigned long long swapMaterials;
		unsigned boxScarce, boxBeltCraft, boxBeltMarket;
		unsigned long long boxScarceUnits;
		unsigned farmOrders, unaffordable;
	};
	TPlayerBotMatsStats s_kPlayerBotMatsStats = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
	std::set<DWORD> s_setPlayerBotMatsSwapBots;

	// ------------------------------------------------------------ the swap

	// The refine materials of the maps up to PLAYERBOT_MATS_SWAP_MAX_LEVEL, from the drop knowledge (rebuilt with it).
	struct TPlayerBotMatsEligible
	{
		DWORD dwBuiltAt;
		std::set<DWORD> vnums;
		TPlayerBotMatsEligible() : dwBuiltAt(0) {}
	};
	TPlayerBotMatsEligible s_kPlayerBotMatsEligible;

	const std::set<DWORD>& GetPlayerBotMatsSwapEligible()
	{
		TPlayerBotMatsEligible& e = s_kPlayerBotMatsEligible;
		const TPlayerBotDropKnow& k = s_kPlayerBotDropKnow;
		if (!k.bBuilt || e.dwBuiltAt == k.dwBuiltAt)
			return e.vnums;
		e.dwBuiltAt = k.dwBuiltAt;
		e.vnums.clear();
		const int maxLevel = GetPlayerBotMatsCfg().swapMaxLevel;
		const std::set<DWORD>& materials = GetPlayerBotRefineMaterialVnums();
		std::string list;
		for (std::set<DWORD>::const_iterator v = materials.begin(); v != materials.end(); ++v)
		{
			const DWORD vnum = *v;
			if (vnum == PLAYERBOT_MATS_CRAFT_VNUM || vnum == PLAYERBOT_HEAVEN_OIL_VNUM || IsPlayerBotSafeRefineScroll(vnum) ||
					IsPlayerBotNonGearMaterial(vnum))
				continue;
			std::map<DWORD, std::vector<TPlayerBotDkSource> >::const_iterator src = k.byItem.find(vnum);
			if (src == k.byItem.end())
				continue;
			bool found = false;
			for (size_t i = 0; i < src->second.size() && !found; ++i)
			{
				const TPlayerBotDkSource& s = src->second[i];
				if (s.bKind != DROPKNOW_MOB)
					continue;
				const int level = PlayerBotDkMobLevel(s.dwFrom);
				if (level <= 0 || level > maxLevel)
					continue;
				std::map<DWORD, std::vector<long> >::const_iterator maps = k.mobMaps.find(s.dwFrom);
				if (maps == k.mobMaps.end())
					continue;
				for (size_t m = 0; m < maps->second.size() && !found; ++m)
					found = maps->second[m] < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && !k.mapDefs.count(maps->second[m]);
			}
			if (!found)
				continue;
			e.vnums.insert(vnum);
			if (list.size() < 700)
			{
				char buf[24];
				snprintf(buf, sizeof(buf), "%s%u", list.empty() ? "" : ",", vnum);
				list += buf;
			}
		}
		sys_log(0, "BOT_MATS: eligible kinds=%u max_level=%d of=%u list=%s", (unsigned int)e.vnums.size(), maxLevel,
				(unsigned int)materials.size(), list.empty() ? "-" : list.c_str());
		return e.vnums;
	}

	// What the next steps of the worn pieces lack of the eligible materials, by vnum.
	void CollectPlayerBotMatsSwapMissing(LPCHARACTER ch, std::map<DWORD, int>& out)
	{
		out.clear();
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return;
		const std::set<DWORD>& eligible = GetPlayerBotMatsSwapEligible();
		if (eligible.empty())
			return;
		const BYTE wears[] = { WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR };
		std::map<DWORD, int> need;
		for (size_t i = 0; i < sizeof(wears) / sizeof(wears[0]); ++i)
		{
			LPITEM piece = ch->GetWear(wears[i]);
			if (!piece || piece->GetRefinedVnum() == 0 || piece->GetRefineLevel() >= GetPlayerBotRefineTarget(ch, piece) ||
					IsPlayerBotOutdatedGear(ch, piece))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(piece->GetRefineSet());
			for (int m = 0; recipe && m < recipe->material_count; ++m)
				if (recipe->materials[m].vnum != 0 && recipe->materials[m].count > 0 && eligible.count(recipe->materials[m].vnum))
					need[recipe->materials[m].vnum] += (int)recipe->materials[m].count;
		}
		for (std::map<DWORD, int>::const_iterator it = need.begin(); it != need.end(); ++it)
		{
			const int have = (int)ch->CountSpecifyItem(it->first) - GetPlayerBotBiologistReserve(ch, it->first);
			if (have < it->second)
				out[it->first] = it->second - std::max(0, have);
		}
	}

	struct TPlayerBotMatsNeed
	{
		DWORD at;
		int units;	// the pieces the swap still makes, capped by a visit's
	};
	std::map<DWORD, TPlayerBotMatsNeed> s_mapPlayerBotMatsNeed;

	int GetPlayerBotMatsSwapUnits(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotMatsOff(MATS_PART_SWAP) || !s_kPlayerBotDropKnow.bBuilt)
			return 0;
		const DWORD now = get_dword_time();
		TPlayerBotMatsNeed& n = s_mapPlayerBotMatsNeed[ch->GetPlayerID()];
		if (n.at != 0 && now - n.at < PLAYERBOT_MATS_NEED_CACHE_MS)
			return n.units;
		if (s_mapPlayerBotMatsNeed.size() > 30000)
		{
			s_mapPlayerBotMatsNeed.clear();
			return 0;
		}
		n.at = now ? now : 1;
		std::map<DWORD, int> missing;
		CollectPlayerBotMatsSwapMissing(ch, missing);
		int units = 0;
		for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end(); ++it)
			units += it->second;
		n.units = std::min(units, GetPlayerBotMatsCfg().swapVisitMax);
		return n.units;
	}

	// GetPlayerBotCraftMaterialsWanted's share: the Materialy Rzemieslnicze the swap still takes.
	int GetPlayerBotMatsSwapWanted(LPCHARACTER ch)
	{
		return GetPlayerBotMatsSwapUnits(ch) * GetPlayerBotMatsCfg().swapRate;
	}

	int GetPlayerBotMatsSwapUsable(LPCHARACTER ch)
	{
		return std::max(0, (int)ch->CountSpecifyItem(PLAYERBOT_MATS_CRAFT_VNUM) - GetPlayerBotYoharaShopMaterialsWanted(ch));
	}

	// A walk to the Dozorca for the swap alone: a piece to make and the materials for it.
	bool IsPlayerBotMatsSwapDue(LPCHARACTER ch)
	{
		return ch && GetPlayerBotMatsSwapUnits(ch) > 0 && GetPlayerBotMatsSwapUsable(ch) >= GetPlayerBotMatsCfg().swapRate;
	}

	// At the Dozorca: the materials out, the pieces in. Returns the pieces made.
	int SwapPlayerBotMaterials(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotMatsOff(MATS_PART_SWAP) || IsPlayerBotSidekickServing(ch))
			return 0;
		const TPlayerBotMatsCfg& c = GetPlayerBotMatsCfg();
		std::map<DWORD, int> missing;
		CollectPlayerBotMatsSwapMissing(ch, missing);
		s_mapPlayerBotMatsNeed.erase(ch->GetPlayerID());
		int made = 0;
		for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end() && made < c.swapVisitMax; ++it)
		{
			const int usable = GetPlayerBotMatsSwapUsable(ch);
			const int units = std::min(std::min(it->second, c.swapVisitMax - made), usable / c.swapRate);
			if (units <= 0)
				break;
			if (CountPlayerBotFreeInventoryCells(ch) < 1 && ch->CountSpecifyItem(it->first) == 0)
				break;
			ch->RemoveSpecifyItem(PLAYERBOT_MATS_CRAFT_VNUM, (ITEM_COUNT)(units * c.swapRate));
			ch->AutoGiveItem(it->first, (ITEM_COUNT)units, -1, false);
			made += units;
			++s_kPlayerBotMatsStats.swaps;
			s_kPlayerBotMatsStats.swapUnits += units;
			s_kPlayerBotMatsStats.swapMaterials += (unsigned long long)(units * c.swapRate);
			if (s_setPlayerBotMatsSwapBots.insert(ch->GetPlayerID()).second)
				++s_kPlayerBotMatsStats.swapBots;
			sys_log(0, "BOT_MATS: swap pid=%u name=%s level=%d item=%u(%s) units=%d lack=%d materials=%d left=%d",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), it->first, PlayerBotDkItemName(it->first), units,
					it->second, units * c.swapRate, (int)ch->CountSpecifyItem(PLAYERBOT_MATS_CRAFT_VNUM));
		}
		return made;
	}

	// ------------------------------------------------------------ the boxes

	// The Biologist's share of a scarce material, while the bot still gets its specimen's drop.
	int GetPlayerBotMatsBiologistKeep(LPCHARACTER ch, DWORD vnum)
	{
		const int reserve = GetPlayerBotBiologistReserve(ch, vnum);
		if (reserve <= 0)
			return 0;
		const int minPct = GetPlayerBotMatsCfg().farmMinDropPct;
		for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i)
		{
			const TPlayerBotBiologistMission& mission = PLAYERBOT_BIOLOGIST_MISSIONS[i];
			if (mission.itemVnum != vnum)
				continue;
			const int mobLevel = PlayerBotDkMobLevel(mission.mobVnum);
			if (mobLevel > 0 && PERCENT_LVDELTA(ch->GetLevel(), mobLevel) >= minPct)
				return reserve;
		}
		return 0;
	}

	int GetPlayerBotMatsScarceKeep(LPCHARACTER ch, DWORD vnum)
	{
		return GetPlayerBotRefineMaterialReserve(ch, vnum) + GetPlayerBotMatsBiologistKeep(ch, vnum);
	}

	bool IsPlayerBotMatsBeltVnum(DWORD vnum)
	{
		if (vnum == 0 || IsPlayerBotBeltGoodsVnum(vnum))	// the shards and the bosses' parts: plenty, or not from a box
			return false;
		for (int i = 0; i < PLAYERBOT_BELT_RECIPE_COUNT; ++i)
			for (int m = 0; m < 4; ++m)
				if (PLAYERBOT_BELT_RECIPES[i].mats[m].vnum == vnum)
					return true;
		return false;
	}

	// The bot's own keep of a belt material: the crafts', the anvil's and - a metal or a gem - its jewellery's sockets.
	int GetPlayerBotMatsBeltKeep(LPCHARACTER ch, LPITEM sample)
	{
		const DWORD vnum = sample->GetVnum();
		int keep = std::max(GetPlayerBotCraftMaterialKeep(ch, vnum), GetPlayerBotRefineMaterialReserve(ch, vnum));
		if (IsPlayerBotAccessoryStone(sample))
			keep = std::max(keep, GetPlayerBotAccessoryStoneKeep(ch, sample));
		return keep;
	}

	// WithdrawPlayerBotSafebox's first pass (playerbot_town.h): up to `budget` stacks of the scarce materials and the belts'
	// for the counter / the belt maker, before the box's ordinary pass. Returns the stacks taken.
	int WithdrawPlayerBotMatsPriority(LPCHARACTER ch, CSafebox* box, int budget, const std::set<DWORD>* pJustDeposited)
	{
		if (!ch || !box || IsPlayerBotSidekickServing(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		const TPlayerBotMatsCfg& c = GetPlayerBotMatsCfg();
		budget = std::min(budget, c.boxStacks);
		const bool scarceOn = !IsPlayerBotMatsOff(MATS_PART_SCARCE) && !c.scarce.empty();
		const bool beltsOn = !IsPlayerBotMatsOff(MATS_PART_BELTS);
		if (budget <= 0 || (!scarceOn && !beltsOn))
			return 0;
		const bool counter = PlayerBotHasCounter(ch);
		std::map<DWORD, int> beltMissing;
		if (beltsOn)
			CollectPlayerBotBeltMissing(ch, beltMissing);
		if (!counter && beltMissing.empty())
			return 0;
		// what the box holds of the kinds asked
		std::map<DWORD, int> inBox;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (item && ((scarceOn && c.scarce.count(item->GetVnum())) || (beltsOn && IsPlayerBotMatsBeltVnum(item->GetVnum()))))
				inBox[item->GetVnum()] += std::max<int>(1, (int)item->GetCount());
		}
		if (inBox.empty())
			return 0;
		const DWORD now = get_dword_time();
		int taken = 0;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM && taken < budget; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (!item)
				continue;
			const DWORD vnum = item->GetVnum();
			if (!inBox.count(vnum) || (pJustDeposited && pJustDeposited->count(vnum)) ||
					WasPlayerBotBoxMovedRecently(s_mapPlayerBotBoxPutAt, ch->GetPlayerID(), vnum, now))
				continue;
			const int count = std::max<int>(1, (int)item->GetCount());
			const int bag = (int)ch->CountSpecifyItem(vnum);
			const int freeAfter = CountPlayerBotFreeInventoryCells(ch) - (int)item->GetSize();
			const bool clear = freeAfter > PLAYERBOT_BAG_PRESSURE_FREE_CELLS &&
					(PLAYERBOT_BAG_CELLS - freeAfter) * 100 < PLAYERBOT_BAG_CELLS * PLAYERBOT_BAG_FULL_PERCENT;
			const char* why = NULL;
			if (scarceOn && c.scarce.count(vnum))
			{
				// over the keep, bag and box together, and no spare of it in the bag yet (that one is the counter's now)
				const int keep = GetPlayerBotMatsScarceKeep(ch, vnum);
				if (counter && clear && bag + inBox[vnum] > keep && bag <= keep)
					why = "mats_scarce";
			}
			else if (beltsOn)
			{
				std::map<DWORD, int>::const_iterator lack = beltMissing.find(vnum);
				const int keep = GetPlayerBotMatsBeltKeep(ch, item);
				if (lack != beltMissing.end() && lack->second > 0 && freeAfter > PLAYERBOT_BAG_PRESSURE_FREE_CELLS)
					why = "mats_belt_craft";
				else if (counter && clear && bag + inBox[vnum] > keep && bag <= keep)
					why = "mats_belt_market";
			}
			if (!why)
				continue;
			const int cell = ch->GetEmptyInventory(item->GetSize());
			if (cell < 0)
				break;
			char szHint[128];
			snprintf(szHint, sizeof(szHint), "%s %u", item->GetName(), (unsigned int)item->GetCount());
			box->Remove(pos);
			item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			FlushPlayerBotItemRow(item);
			LogManager::instance().ItemLog(ch, item, "SAFEBOX GET", szHint);
			sys_log(0, "PLAYERBOT_TOWN: safebox withdraw pid=%u name=%s vnum=%u count=%u reason=%s bag_before=%d box=%d",
					ch->GetPlayerID(), ch->GetName(), vnum, (unsigned int)item->GetCount(), why, bag, inBox[vnum]);
			NotePlayerBotBoxMove(s_mapPlayerBotBoxTakenAt, ch->GetPlayerID(), vnum, now);
			inBox[vnum] -= count;
			if (!strcmp(why, "mats_scarce"))
			{
				++s_kPlayerBotMatsStats.boxScarce;
				s_kPlayerBotMatsStats.boxScarceUnits += count;
			}
			else if (!strcmp(why, "mats_belt_craft"))
			{
				++s_kPlayerBotMatsStats.boxBeltCraft;
				beltMissing[vnum] -= count;
			}
			else
				++s_kPlayerBotMatsStats.boxBeltMarket;
			++taken;
		}
		return taken;
	}

	// ------------------------------------------------------------ the market and the farm

	// playerbot_dropknow.h's need pass: a market whose last ask for the lack is over the bot's purse share is no source.
	bool IsPlayerBotMatsMarketUnaffordable(LPCHARACTER ch, DWORD vnum, int lack)
	{
		if (!ch || IsPlayerBotMatsOff(MATS_PART_FARM))
			return false;
		const DWORD ask = GetPlayerBotLastAsk(vnum, 0, get_dword_time());
		if (ask == 0)
			return false;
		const long long spare = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		const bool dear = (long long)ask * std::max(1, lack) > std::max(0LL, spare) * GetPlayerBotMatsCfg().affordPurse / 100;
		if (dear)
			++s_kPlayerBotMatsStats.unaffordable;
		return dear;
	}

	struct TPlayerBotMatsFarmAnswer
	{
		DWORD at;
		long map;
		DWORD until;	// the order it answered
	};
	std::map<DWORD, TPlayerBotMatsFarmAnswer> s_mapPlayerBotMatsFarm;
	std::map<DWORD, DWORD> s_mapPlayerBotMatsFarmers;	// pid -> last answered with a map

	long DecidePlayerBotMatsFarmMap(LPCHARACTER ch, const TPlayerBotDkFarm& f)
	{
		const TPlayerBotMatsCfg& c = GetPlayerBotMatsCfg();
		if (!c.farmVnums.count(f.dwVnum) || !PlayerBotNeedsRefineMaterial(ch, f.dwVnum))
			return 0;
		const int mobLevel = PlayerBotDkMobLevel(f.dwMob);
		if (mobLevel <= 0 || PERCENT_LVDELTA(ch->GetLevel(), mobLevel) < c.farmMinDropPct)
			return 0;
		if (!IsPlayerBotFrontierMapIndex(f.lMap) || !IsPlayerBotMapHostedHere(f.lMap))
			return 0;
		return f.lMap;
	}

	// GetPlayerBotFrontierMapForLevelRaw's hook (playerbot_travel.h): the map of the bot's farm order, or 0.
	long GetPlayerBotMatsFarmMap(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotMatsOff(MATS_PART_FARM) || IsPlayerBotDropKnowOff() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotDkFarm>::const_iterator f = s_mapPlayerBotDkFarm.find(pid);
		const DWORD now = get_dword_time();
		if (f == s_mapPlayerBotDkFarm.end() || (int)(f->second.dwUntil - now) <= 0)
		{
			s_mapPlayerBotMatsFarm.erase(pid);
			s_mapPlayerBotMatsFarmers.erase(pid);
			return 0;
		}
		TPlayerBotMatsFarmAnswer& a = s_mapPlayerBotMatsFarm[pid];
		if (a.at != 0 && now - a.at < PLAYERBOT_MATS_FARM_CACHE_MS && a.until == f->second.dwUntil)
			return a.map;
		const bool fresh = a.until != f->second.dwUntil;
		a.at = now ? now : 1;
		a.until = f->second.dwUntil;
		a.map = DecidePlayerBotMatsFarmMap(ch, f->second);
		if (a.map != 0 && !s_mapPlayerBotMatsFarmers.count(pid))
		{
			// the farmers of the core at once
			for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotMatsFarmers.begin(); it != s_mapPlayerBotMatsFarmers.end();)
			{
				if (now - it->second >= PLAYERBOT_MATS_FARMER_WINDOW_MS)
					s_mapPlayerBotMatsFarmers.erase(it++);
				else
					++it;
			}
			if ((int)s_mapPlayerBotMatsFarmers.size() >= GetPlayerBotMatsCfg().farmMax)
				a.map = 0;
		}
		if (a.map != 0)
			s_mapPlayerBotMatsFarmers[pid] = now ? now : 1;
		else
			s_mapPlayerBotMatsFarmers.erase(pid);
		if (fresh && a.map != 0)
		{
			++s_kPlayerBotMatsStats.farmOrders;
			sys_log(0, "BOT_MATS: farm pid=%u name=%s level=%d item=%u(%s) mob=%u mob_level=%d drop_pct=%d map=%ld from=%ld farmers=%u",
					pid, ch->GetName(), (int)ch->GetLevel(), f->second.dwVnum, PlayerBotDkItemName(f->second.dwVnum),
					f->second.dwMob, PlayerBotDkMobLevel(f->second.dwMob),
					(int)PERCENT_LVDELTA(ch->GetLevel(), PlayerBotDkMobLevel(f->second.dwMob)), a.map, ch->GetMapIndex(),
					(unsigned int)s_mapPlayerBotMatsFarmers.size());
		}
		const long answer = a.map;
		if (s_mapPlayerBotMatsFarm.size() > 30000)
			s_mapPlayerBotMatsFarm.clear();
		return answer;
	}

	// ------------------------------------------------------------ the status

	// With BOT_DROPKNOW's status (every PLAYERBOT_DROPKNOW_STATUS_MS).
	void LogPlayerBotMatsStatus()
	{
		const TPlayerBotMatsStats& s = s_kPlayerBotMatsStats;
		sys_log(0, "BOT_MATS: status eligible=%u swaps=%u swap_units=%u swap_materials=%llu swap_bots=%u box_scarce=%u "
				"box_scarce_units=%llu box_belt_craft=%u box_belt_market=%u farm_orders=%u farmers=%u unaffordable=%u "
				"off(swap/scarce/farm/belts)=%d/%d/%d/%d",
				(unsigned int)GetPlayerBotMatsSwapEligible().size(), s.swaps, s.swapUnits, s.swapMaterials, s.swapBots,
				s.boxScarce, s.boxScarceUnits, s.boxBeltCraft, s.boxBeltMarket, s.farmOrders,
				(unsigned int)s_mapPlayerBotMatsFarmers.size(), s.unaffordable,
				IsPlayerBotMatsOff(MATS_PART_SWAP) ? 1 : 0, IsPlayerBotMatsOff(MATS_PART_SCARCE) ? 1 : 0,
				IsPlayerBotMatsOff(MATS_PART_FARM) ? 1 : 0, IsPlayerBotMatsOff(MATS_PART_BELTS) ? 1 : 0);
		if (s_setPlayerBotMatsSwapBots.size() > 50000)
			s_setPlayerBotMatsSwapBots.clear();
	}
}

#endif
