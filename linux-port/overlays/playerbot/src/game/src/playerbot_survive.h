#ifndef __INC_METIN2_PLAYERBOT_SURVIVE_H__
#define __INC_METIN2_PLAYERBOT_SURVIVE_H__

// MT2009_PLUS_BOT_SURVIVE_V1 - survival and boosts of the bots of 60+ (the owner's decisions of 6 November 2026, section D
// of cache/yohara/boty-ekonomia-2026-11-06-brief.md, after the four servers' analysis: bots of 70-79 died 12.1 times an
// hour on the supporters' world, wearing a body armour of level 54 and earrings of 38, with 838 million experience lost
// in one hour; 333 exp-locked bots held an Experience Ring nobody could buy; nobody but the Sung Ma hunters bought the
// Dragon God boosters):
//
// 1. Tier gear ("Zbroja 61/66 i lepsza bizuteria 54-62 dla botow 60+"). The ladders already name these pieces, but no
//    merchant sells them and the market's armour rule bought only a piece whose clean score beat the owned one by a tenth
//    - a body armour of 61 at +0..+4 never beats a 54 at +9 - and a 61 refined to +7 in the bag was "goods" for the
//    counter while the worn 54+9 still scored more (IsPlayerBotFinishedSpareGoods). Now, for a bot of
//    PLAYERBOT_SURVIVE_TIER_MIN_LEVEL and up: a stand's body armour of 61 / 66, bracelet / necklace / earrings of 54 and
//    up or boots of 51 and up, of a level over the best piece of its slot the bot owns (worn or in the bag), counts as an
//    upgrade (GetPlayerBotSurviveTierScore: the score of PLAYERBOT_SURVIVE_TIER_GAIN over the owned one) - the anvil then
//    takes it on as the higher-tier spare (IsPlayerBotHigherTierSpare) and the equipment pass puts it on once its own
//    numbers win; and a body armour of that tier at +7/+8 stays the anvil's project (IsPlayerBotSurviveTierProject), not
//    the counter's goods.
// 2. Step down ("po kilku zgonach na godzine zejdz na latwiejsza mape i zbieraj tam materialy"). PLAYERBOT_SURVIVE_DEATHS_H
//    deaths to monsters within an hour on one hunting map of the 2.x world mark that map hard for the bot for
//    PLAYERBOT_SURVIVE_STEPDOWN_MIN minutes: its frontier draw then answers an easier map (a lower entry level, open to
//    its level, hosted here, under its ceiling, passing the element gate and the Spider Dungeons' gear) - the one the
//    drop knowledge says drops a refine / craft material the bot is short of first, and a farm order for that monster
//    (s_mapPlayerBotDkFarm: the fight and the hunt take it as a material target). Errands that name a map are not asked.
// 3. Exp rings ("po prostu niech sprzedaja go na rynku"): an exp-locked bot puts its Experience Rings on its offline
//    counter first (HoistPlayerBotSurviveExpRings) - the levelling bots buy them there (PLAYERBOT_TIMED_UNIQUE_*).
// 4. Dragon God boosters ("kupuja Atak/Obrone Boga Smokow przed polowaniem"): a bot of PLAYERBOT_SURVIVE_BOOSTER_MIN_LEVEL
//    and up on (or bound for) a 2.x hunting map buys Atak (71028) and Obrona (71030) Boga Smokow in the ItemShop V3 for
//    Smocze Znaki (a daily budget of a quarter of the marks over PLAYERBOT_SURVIVE_BOOSTER_MARKS_RESERVE, at most
//    PLAYERBOT_SURVIVE_BOOSTER_DAY_MAX) and drinks them as it arrives on the hunting ground, outside a safe zone - the
//    defence first after a death in the last hour. Sung Ma hunters keep their own boosters (playerbot_yohara_guides.h).
//
// Switches: event flag m2_bot_survive_off 1 - all four off; m2_bot_survive_tier_off / _stepdown_off / _ring_off /
// _booster_off - one; env PLAYERBOT_SURVIVE_TIER_MIN_LEVEL (60), PLAYERBOT_SURVIVE_DEATHS_H (9),
// PLAYERBOT_SURVIVE_STEPDOWN_MIN (120), PLAYERBOT_SURVIVE_BOOSTER_MIN_LEVEL (50), PLAYERBOT_SURVIVE_BOOSTER_DAY_MAX (400).
// The log: PLAYERBOT_SURVIVE: lines - step down / step back (each), tier pick (throttled), ring listed (throttled),
// booster bought / drunk (throttled), census every PLAYERBOT_SURVIVE_CENSUS_MS.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_dropki.h (the market, the ItemShop V3,
// the drop knowledge before it), in the anonymous namespace; the early headers ask its hooks through declarations.

namespace
{
	const DWORD PLAYERBOT_SURVIVE_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_SURVIVE_TIER_GAIN = PLAYERBOT_ARMOUR_UPGRADE_BIG_GAIN_PERCENT;	// the bought tier's budget share
	const int PLAYERBOT_SURVIVE_BODY_FLOOR = 61;
	const int PLAYERBOT_SURVIVE_JEWEL_FLOOR = 54;
	const int PLAYERBOT_SURVIVE_BOOTS_FLOOR = 51;
	const DWORD PLAYERBOT_SURVIVE_DEATH_WINDOW_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_SURVIVE_REPICK_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SURVIVE_FARM_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_SURVIVE_BOOSTER_LOOK_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_SURVIVE_BOOSTER_DAY_MS = 24 * 60 * 60 * 1000;
	const int PLAYERBOT_SURVIVE_BOOSTER_MARKS_RESERVE = 400;
	const int PLAYERBOT_SURVIVE_RINGS_A_VISIT = 2;
	const DWORD PLAYERBOT_SURVIVE_ATTACK = 71028, PLAYERBOT_SURVIVE_DEFENCE = 71030;

	enum EPlayerBotSurviveKind
	{
		SURVIVE_TIER = 0,
		SURVIVE_STEPDOWN,
		SURVIVE_RING,
		SURVIVE_BOOSTER,
		SURVIVE_KINDS
	};

	bool IsPlayerBotSurviveOn(int kind)
	{
		static const char* const s_flags[SURVIVE_KINDS] = {
			"m2_bot_survive_tier_off", "m2_bot_survive_stepdown_off", "m2_bot_survive_ring_off", "m2_bot_survive_booster_off" };
		static DWORD s_dwAt = 0;
		static bool s_bOn[SURVIVE_KINDS] = { true, true, true, true };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			const bool all = quest::CQuestManager::instance().GetEventFlag("m2_bot_survive_off") == 0;
			for (int i = 0; i < SURVIVE_KINDS; ++i)
				s_bOn[i] = all && quest::CQuestManager::instance().GetEventFlag(s_flags[i]) == 0;
		}
		return kind >= 0 && kind < SURVIVE_KINDS && s_bOn[kind];
	}

	int GetPlayerBotSurviveEnv(const char* name, int def, int lo, int hi)
	{
		return ReadPlayerBotYoharaEnvInt(name, def, lo, hi);
	}

	struct TPlayerBotSurviveStats
	{
		unsigned int tierPicks, tierProjects, stepDowns, stepBacks, ringsListed, boostersBought, boostersDrunk, budgetHits,
				farmOrders;
		TPlayerBotSurviveStats() : tierPicks(0), tierProjects(0), stepDowns(0), stepBacks(0), ringsListed(0),
				boostersBought(0), boostersDrunk(0), budgetHits(0), farmOrders(0) {}
	};
	TPlayerBotSurviveStats s_kPlayerBotSurvive;

	struct TPlayerBotSurviveBot
	{
		std::deque<std::pair<DWORD, long> > deaths;	// (when, map) of the monster deaths in the window
		std::map<long, DWORD> hard;			// map -> until
		long lStepMap;					// the easier map picked, and when
		DWORD dwStepAt;
		long lStepFrom;
		long long llPlayerDeaths;			// PLAYER_STATS_DEATH_FROM_PLAYER_FLAG at the last death (-1 unknown)
		DWORD dwNextBoosterLook, dwBoosterDay;
		int iBoosterSpent;
		TPlayerBotSurviveBot() : lStepMap(0), dwStepAt(0), lStepFrom(0), llPlayerDeaths(-1), dwNextBoosterLook(0),
				dwBoosterDay(0), iBoosterSpent(0) {}
	};
	std::map<DWORD, TPlayerBotSurviveBot> s_mapPlayerBotSurvive;

	// ------------------------------------------------------------ 1. tier gear

	// The level a slot's piece of the tier must have for this bot (the armour upgrade's slots: 0 body, 3 wrist, 4 boots,
	// 5 necklace, 6 earrings), or 0 - no tier rule for the slot or the bot.
	int GetPlayerBotSurviveTierFloor(LPCHARACTER ch, int slot)
	{
		if (!ch || !IsPlayerBotSurviveOn(SURVIVE_TIER))
			return 0;
		static int s_iMin = -1;
		if (s_iMin < 0)
			s_iMin = GetPlayerBotSurviveEnv("PLAYERBOT_SURVIVE_TIER_MIN_LEVEL", 60, 1, 250);
		const int level = (int)ch->GetLevel();
		if (level < s_iMin)
			return 0;
		int floor = 0;
		switch (slot)
		{
			case 0: floor = PLAYERBOT_SURVIVE_BODY_FLOOR; break;
			case 3: case 5: case 6: floor = PLAYERBOT_SURVIVE_JEWEL_FLOOR; break;
			case 4: floor = PLAYERBOT_SURVIVE_BOOTS_FLOOR; break;
			default: return 0;
		}
		return level >= floor ? floor : 0;
	}

	// The highest level of a piece of each armour-upgrade slot the bot owns and can wear now, worn or in the bag.
	void ReadPlayerBotSurviveOwnedLevels(LPCHARACTER ch, int levels[PLAYERBOT_ARMOUR_UPGRADE_SLOTS])
	{
		for (int i = 0; i < PLAYERBOT_ARMOUR_UPGRADE_SLOTS; ++i)
			levels[i] = -1;
		if (!ch || !ch->IsItemLoaded())
			return;
		for (int slot = 0; slot < PLAYERBOT_ARMOUR_UPGRADE_SLOTS; ++slot)
		{
			LPITEM worn = ch->GetWear(PLAYERBOT_ARMOUR_UPGRADE_WEARS[slot]);
			if (worn && worn->GetType() == ITEM_ARMOR)
				levels[slot] = std::max<int>(levels[slot], worn->GetLevelLimit());
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->GetType() != ITEM_ARMOR)
				continue;
			const int slot = GetPlayerBotArmourUpgradeSlot(item->GetSubType());
			if (slot < 0 || item->GetLevelLimit() > ch->GetLevel() || !IsPlayerBotEquipmentCandidate(ch, item) ||
					item->FindEquipCell(ch) != PLAYERBOT_ARMOUR_UPGRADE_WEARS[slot])
				continue;
			levels[slot] = std::max<int>(levels[slot], item->GetLevelLimit());
		}
	}

	int ReadPlayerBotSurviveOwnedLevel(LPCHARACTER ch, int slot)
	{
		int levels[PLAYERBOT_ARMOUR_UPGRADE_SLOTS];
		ReadPlayerBotSurviveOwnedLevels(ch, levels);
		return slot >= 0 && slot < PLAYERBOT_ARMOUR_UPGRADE_SLOTS ? levels[slot] : -1;
	}

	// The score the armour rule weighs a candidate by: its own, or - for a piece of the tier (its level at the slot's
	// floor or over, over every piece of the slot the bot owns) - the owned one's raised by PLAYERBOT_SURVIVE_TIER_GAIN,
	// so the rule buys it to be refined.
	long long GetPlayerBotSurviveTierScore(LPCHARACTER ch, int slot, int candLevel, long long score, long long ownedScore,
			int ownedLevel)
	{
		const int floor = GetPlayerBotSurviveTierFloor(ch, slot);
		if (floor <= 0 || candLevel < floor || candLevel <= ownedLevel || candLevel > (int)ch->GetLevel() || ownedScore <= 0)
			return score;
		return std::max(score, ownedScore * (100 + PLAYERBOT_SURVIVE_TIER_GAIN) / 100 + 1);
	}

	// The same for one candidate: the owned level read only when the tier could apply to it.
	long long GetPlayerBotSurviveTierScoreFor(LPCHARACTER ch, int slot, int candLevel, long long score, long long ownedScore)
	{
		const int floor = GetPlayerBotSurviveTierFloor(ch, slot);
		if (floor <= 0 || candLevel < floor || candLevel > (int)ch->GetLevel())
			return score;
		return GetPlayerBotSurviveTierScore(ch, slot, candLevel, score, ownedScore, ReadPlayerBotSurviveOwnedLevel(ch, slot));
	}

	void NotePlayerBotSurviveTierPick(LPCHARACTER ch, DWORD vnum, int slot, long long price)
	{
		++s_kPlayerBotSurvive.tierPicks;
		PlayerBotLogThrottled("survive_tier_pick", get_dword_time(),
				"PLAYERBOT_SURVIVE: tier pick pid=%u name=%s level=%u slot=%d vnum=%u price=%lld",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), slot, vnum, price);
	}

	// A body armour of the tier in the bag, of a level over the worn one's: the anvil's project to +9, not the counter's
	// goods while the worn piece still scores more.
	bool IsPlayerBotSurviveTierProject(LPCHARACTER ch, LPITEM item, LPITEM worn)
	{
		if (!ch || !item || !worn || item->GetType() != ITEM_ARMOR || item->GetSubType() != ARMOR_BODY)
			return false;
		const int floor = GetPlayerBotSurviveTierFloor(ch, 0);
		if (floor <= 0 || (int)item->GetLevelLimit() < floor || item->GetLevelLimit() <= worn->GetLevelLimit() ||
				item->GetLevelLimit() > ch->GetLevel() || item->GetRefineLevel() >= 9 || item->GetRefinedVnum() == 0)
			return false;
		++s_kPlayerBotSurvive.tierProjects;
		return true;
	}

	// ------------------------------------------------------------ 2. step down

	// The 2.x hunting maps by their entry level (the operator's rows); a map not here is not stepped down from.
	struct TPlayerBotSurviveRow { long map; int minLevel; };

	int GetPlayerBotSurviveRows(TPlayerBotSurviveRow* rows, int max)
	{
		using namespace playerbot_progression;
		const TPlayerBotSurviveRow all[] = {
			{ PLAYERBOT_MAP_GROTTO_V2, MapFrom(MAP_GROTTO2) },
			{ PLAYERBOT_MAP_GROTTO_V1, MapFrom(MAP_GROTTO1) },
			{ PLAYERBOT_MAP_RED_FOREST, MapFrom(MAP_RED_FOREST) },
			{ PLAYERBOT_MAP_FIRE_LAND, MapFrom(MAP_FIRE_LAND) },
			{ PLAYERBOT_MAP_FOREST, MapFrom(MAP_FOREST) },
			{ PLAYERBOT_MAP_DEMON_TOWER, MapFrom(MAP_DEMON_TOWER) },
			{ PLAYERBOT_MAP_SPIDER_V2, MapFrom(MAP_SPIDER2) },
			{ PLAYERBOT_MAP_HWANG, MapFrom(MAP_HWANG) },
			{ PLAYERBOT_MAP_SPIDER_V1, MapFrom(MAP_SPIDER1) },
			{ PLAYERBOT_MAP_SOHAN, MapFrom(MAP_SOHAN) },
			{ PLAYERBOT_MAP_ORC_VALLEY, MapFrom(MAP_ORC_VALLEY) },
			{ PLAYERBOT_MAP_DESERT, MapFrom(MAP_DESERT) },
		};
		int n = 0;
		for (size_t i = 0; i < sizeof(all) / sizeof(all[0]) && n < max; ++i)
			rows[n++] = all[i];
		return n;
	}

	int GetPlayerBotSurviveMapLevel(long map)
	{
		TPlayerBotSurviveRow rows[16];
		const int n = GetPlayerBotSurviveRows(rows, 16);
		for (int i = 0; i < n; ++i)
			if (rows[i].map == map)
				return rows[i].minLevel;
		return -1;
	}

	// MT2009_PLUS_BOT_DEATHLOOP_V1 (the owner, 6 November 2026: "trzy smierci to za malo - jak ginie powyzej 8 razy"): the
	// deaths an hour on one map that send a bot to an easier one - here, and the death loop's map avoid
	// (playerbot_deathloop.h) reads the same number. Env PLAYERBOT_SURVIVE_DEATHS_H (9, was 4).
	int GetPlayerBotSurviveDeathsPerHour()
	{
		static int s_iDeaths = -1;
		if (s_iDeaths < 0)
			s_iDeaths = GetPlayerBotSurviveEnv("PLAYERBOT_SURVIVE_DEATHS_H", 9, 2, 100);
		return s_iDeaths;
	}

	// A death, on the tick it is noticed (playerbot_survival.h, after the persona's). Only a monster's, on a 2.x hunting
	// map, outside a dungeon's or a war's business.
	void NotePlayerBotSurviveDeath(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return;
		TPlayerBotSurviveBot& b = s_mapPlayerBotSurvive[ch->GetPlayerID()];
		bool byPlayer = false;
#if defined(PLAYERBOT_ENGINE_MT2009)
		{
			const long long now = ch->GetSpecialFlag((DWORD)PLAYER_STATS_DEATH_FROM_PLAYER_FLAG);
			// no baseline yet (ManagePlayerBotSurvive sets it): not counted
			byPlayer = b.llPlayerDeaths < 0 || now > b.llPlayerDeaths;
			b.llPlayerDeaths = now;
		}
#endif
		if (byPlayer || !IsPlayerBotSurviveOn(SURVIVE_STEPDOWN))
			return;
		const long map = ch->GetMapIndex();
		if (GetPlayerBotSurviveMapLevel(map) < 0 || IsPlayerBotInDungeonBusiness(ch, state) || state.dwGuildWarEnemyGID != 0)
			return;
		while (!b.deaths.empty() && dwNow - b.deaths.front().first >= PLAYERBOT_SURVIVE_DEATH_WINDOW_MS)
			b.deaths.pop_front();
		b.deaths.push_back(std::make_pair(dwNow, map));
		int onMap = 0;
		for (size_t i = 0; i < b.deaths.size(); ++i)
			onMap += b.deaths[i].second == map ? 1 : 0;
		static int s_iMin = -1;
		if (s_iMin < 0)
			s_iMin = GetPlayerBotSurviveEnv("PLAYERBOT_SURVIVE_STEPDOWN_MIN", 120, 10, 24 * 60);
		if (onMap < GetPlayerBotSurviveDeathsPerHour())
			return;
		b.hard[map] = dwNow + (DWORD)s_iMin * 60000U;
		b.dwStepAt = 0;	// pick again
		std::deque<std::pair<DWORD, long> > rest;
		for (size_t i = 0; i < b.deaths.size(); ++i)
			if (b.deaths[i].second != map)
				rest.push_back(b.deaths[i]);
		b.deaths.swap(rest);
		++s_kPlayerBotSurvive.stepDowns;
		sys_log(0, "PLAYERBOT_SURVIVE: step down pid=%u name=%s level=%u map=%ld deaths_h=%d hp=%d for_min=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), map, onMap, ch->GetMaxHP(), s_iMin);
	}

	// Whether a map of the drop knowledge has a monster in this bot's drop window that gives one of the wanted items;
	// the monster and the item it gives.
	bool FindPlayerBotSurviveMaterialMob(LPCHARACTER ch, long map, const std::set<DWORD>& wanted, DWORD& mobOut,
			DWORD& itemOut)
	{
		mobOut = itemOut = 0;
		if (wanted.empty() || !s_kPlayerBotDropKnow.bBuilt || IsPlayerBotDropKnowOff())
			return false;
		std::map<long, std::vector<DWORD> >::const_iterator mobs = s_kPlayerBotDropKnow.mapMobs.find(map);
		if (mobs == s_kPlayerBotDropKnow.mapMobs.end())
			return false;
		float best = 0.0f;
		for (size_t i = 0; i < mobs->second.size(); ++i)
		{
			const DWORD race = mobs->second[i];
			const int mobLevel = PlayerBotDkMobLevel(race);
			if (mobLevel <= 0 || PERCENT_LVDELTA(ch->GetLevel(), mobLevel) < PLAYERBOT_MATERIAL_MIN_DROP_PERCENT)
				continue;
			std::map<DWORD, std::vector<TPlayerBotDkDrop> >::const_iterator drops = s_kPlayerBotDropKnow.byMob.find(race);
			if (drops == s_kPlayerBotDropKnow.byMob.end())
				continue;
			for (size_t d = 0; d < drops->second.size(); ++d)
			{
				if (!wanted.count(drops->second[d].dwItem))
					continue;
				const float eff = drops->second[d].fChance * PERCENT_LVDELTA(ch->GetLevel(), mobLevel) / 100.0f;
				if (eff > best)
				{
					best = eff;
					mobOut = race;
					itemOut = drops->second[d].dwItem;
				}
			}
		}
		return mobOut != 0;
	}

	// The easier map for a bot whose draw named a map it is dying on.
	long PickPlayerBotSurviveEasierMap(LPCHARACTER ch, TPlayerBotSurviveBot& b, long hardMap, DWORD dwNow)
	{
		int ceiling = GetPlayerBotSurviveMapLevel(hardMap);
		for (std::map<long, DWORD>::const_iterator it = b.hard.begin(); it != b.hard.end(); ++it)
		{
			const int lv = GetPlayerBotSurviveMapLevel(it->first);
			if ((int)(it->second - dwNow) > 0 && lv >= 0 && lv < ceiling)
				ceiling = lv;
		}
		const int level = (int)ch->GetLevel();
		TPlayerBotSurviveRow rows[16];
		const int n = GetPlayerBotSurviveRows(rows, 16);
		std::vector<long> candidates;	// highest first
		for (int i = 0; i < n; ++i)
		{
			const long map = rows[i].map;
			if (rows[i].minLevel >= ceiling || level < rows[i].minLevel || IsPlayerBotMapOverCeiling(map, level) ||
					!IsPlayerBotMapHostedHere(map) || IsPlayerBotSidekickTripBlocked(ch, map))
				continue;
			std::map<long, DWORD>::const_iterator h = b.hard.find(map);
			if (h != b.hard.end() && (int)(h->second - dwNow) > 0)
				continue;
			if (IsPlayerBotSpiderMap(map) && (!IsPlayerBotSpiderGearReady(ch, map) || IsPlayerBotMetinologNow(ch)))
				continue;
			if (map == PLAYERBOT_MAP_DEMON_TOWER)
				continue;	// a dungeon's road, not a ground to settle on
			if (!PassPlayerBotElementMapGate(ch, map, NULL, NULL))
				continue;
			candidates.push_back(map);
		}
		if (candidates.empty())
			return 0;
		// the drop knowledge's farm order on one of them, else the highest that gives a wanted material, else the highest
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotDkFarm>::const_iterator farm = s_mapPlayerBotDkFarm.find(pid);
		if (farm != s_mapPlayerBotDkFarm.end() && (int)(farm->second.dwUntil - dwNow) > 0 &&
				std::find(candidates.begin(), candidates.end(), farm->second.lMap) != candidates.end())
			return farm->second.lMap;
		std::set<DWORD> wanted;
		if (!IsPlayerBotDropKnowOff())
		{
			CollectPlayerBotWantedMaterials(ch, wanted);
			std::map<DWORD, int> craft;
			CollectPlayerBotCraftMissing(ch, craft, 1);
			for (std::map<DWORD, int>::const_iterator it = craft.begin(); it != craft.end(); ++it)
				if (it->second > 0)
					wanted.insert(it->first);
		}
		for (size_t i = 0; i < candidates.size(); ++i)
		{
			DWORD mob = 0, item = 0;
			if (!FindPlayerBotSurviveMaterialMob(ch, candidates[i], wanted, mob, item))
				continue;
			if (farm == s_mapPlayerBotDkFarm.end() || (int)(farm->second.dwUntil - dwNow) <= 0)
			{
				TPlayerBotDkFarm& f = s_mapPlayerBotDkFarm[pid];
				f.lMap = candidates[i];
				f.dwMob = mob;
				f.dwVnum = item;
				f.dwUntil = dwNow + PLAYERBOT_SURVIVE_FARM_MS;
				++s_kPlayerBotSurvive.farmOrders;
			}
			PlayerBotLogThrottled("survive_farm", dwNow,
					"PLAYERBOT_SURVIVE: materials on the easier map pid=%u name=%s level=%u map=%ld mob=%u item=%u(%s)",
					pid, ch->GetName(), (unsigned int)level, candidates[i], mob, item, PlayerBotDkItemName(item));
			return candidates[i];
		}
		return candidates.front();
	}

	// The frontier draw's map, or the easier one while the bot is stepped down from it (GetPlayerBotFrontierMapForLevel).
	long ApplyPlayerBotSurviveStepDown(LPCHARACTER ch, long map)
	{
		if (!ch || map == 0 || !IsPlayerBotSurviveOn(SURVIVE_STEPDOWN))
			return map;
		std::map<DWORD, TPlayerBotSurviveBot>::iterator it = s_mapPlayerBotSurvive.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSurvive.end() || it->second.hard.empty())
			return map;
		TPlayerBotSurviveBot& b = it->second;
		const DWORD now = get_dword_time();
		for (std::map<long, DWORD>::iterator h = b.hard.begin(); h != b.hard.end(); )
		{
			if ((int)(h->second - now) <= 0)
			{
				++s_kPlayerBotSurvive.stepBacks;
				sys_log(0, "PLAYERBOT_SURVIVE: step back pid=%u name=%s level=%u map=%ld",
						ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), h->first);
				b.hard.erase(h++);
				b.dwStepAt = 0;
			}
			else
				++h;
		}
		std::map<long, DWORD>::const_iterator h = b.hard.find(map);
		if (h == b.hard.end())
			return map;
		if (b.dwStepAt == 0 || b.lStepFrom != map || now - b.dwStepAt >= PLAYERBOT_SURVIVE_REPICK_MS)
		{
			const long before = b.lStepMap;
			b.lStepMap = PickPlayerBotSurviveEasierMap(ch, b, map, now);
			b.lStepFrom = map;
			b.dwStepAt = now ? now : 1;
			if (b.lStepMap != before)
				sys_log(0, "PLAYERBOT_SURVIVE: easier map pid=%u name=%s level=%u from=%ld to=%ld left_min=%d",
						ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), map, b.lStepMap,
						(int)((h->second - now) / 60000U));
		}
		return b.lStepMap != 0 ? b.lStepMap : map;
	}

	bool IsPlayerBotSurviveSteppedDown(DWORD pid)
	{
		std::map<DWORD, TPlayerBotSurviveBot>::const_iterator it = s_mapPlayerBotSurvive.find(pid);
		return it != s_mapPlayerBotSurvive.end() && !it->second.hard.empty();
	}

	// ------------------------------------------------------------ 3. exp rings

	// An exp-locked bot's Experience Rings first on its offline counter (playerbot_offline_shop.h, after the candidates
	// are scored): at most PLAYERBOT_SURVIVE_RINGS_A_VISIT a visit, ahead of everything but a prepared line.
	void HoistPlayerBotSurviveExpRings(LPCHARACTER ch, std::vector<std::pair<int, WORD> >& scored)
	{
		if (!ch || !ch->IsItemLoaded() || !IsPlayerBotSurviveOn(SURVIVE_RING) || !IsPlayerBotExpLocked(ch))
			return;
		int hoisted = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && hoisted < PLAYERBOT_SURVIVE_RINGS_A_VISIT; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->isLocked() || item->IsExchanging() ||
					item->GetType() != ITEM_UNIQUE || !IsPlayerBotExpRing(item->GetVnum()) ||
					IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP) ||
					IsPlayerBotKeptTimedUnique(ch, item) || IsPlayerBotSidekickHeld(ch, item))
				continue;
			for (size_t i = 0; i < scored.size(); ++i)
				if (scored[i].second == cell)
				{
					scored.erase(scored.begin() + i);
					break;
				}
			scored.insert(scored.begin(), std::make_pair(PLAYERBOT_SHOP_PRIZE_SCORE + 1, cell));
			++hoisted;
			++s_kPlayerBotSurvive.ringsListed;
			PlayerBotLogThrottled("survive_ring", get_dword_time(),
					"PLAYERBOT_SURVIVE: exp ring to the counter pid=%u name=%s level=%u vnum=%u",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), item->GetVnum());
		}
	}

	// ------------------------------------------------------------ 4. Dragon God boosters

	bool IsPlayerBotSurviveBoosterRunning(LPCHARACTER ch, DWORD vnum)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto && ch->FindAffect((DWORD)proto->alValues[0], (BYTE)proto->alValues[1]) != NULL;
	}

	// The 2.x hunting ground the bot is on (outside a safe zone) or bound for; a Sung Ma map is its guides'.
	bool IsPlayerBotSurviveHunter(LPCHARACTER ch, const TPlayerBotAIState& state, bool& onGround)
	{
		onGround = false;
		if (IsPlayerBotInDungeonBusiness(ch, state) || state.dwGuildWarEnemyGID != 0 ||
				GetPlayerBotSungmaSlot(ch->GetMapIndex()) >= 0)
			return false;
		const long here = ch->GetMapIndex();
		if (GetPlayerBotSurviveMapLevel(here) >= 0)
		{
			onGround = !IsPlayerBotSafeZone(here, ch->GetX(), ch->GetY()) && !state.bVisitingShop && !state.bMarketTrip;
			return true;
		}
		return GetPlayerBotSurviveMapLevel(GetPlayerBotFrontierMapForLevel(ch)) >= 0;
	}

	void ManagePlayerBotSurviveBoosters(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		if (!IsPlayerBotSurviveOn(SURVIVE_BOOSTER))
			return;
		static int s_iMin = -1, s_iDayMax = -1;
		if (s_iMin < 0)
		{
			s_iMin = GetPlayerBotSurviveEnv("PLAYERBOT_SURVIVE_BOOSTER_MIN_LEVEL", 50, 1, 250);
			s_iDayMax = GetPlayerBotSurviveEnv("PLAYERBOT_SURVIVE_BOOSTER_DAY_MAX", 400, 0, 100000);
		}
		if ((int)ch->GetLevel() < s_iMin || ch->IsDead() || !ch->IsItemLoaded() || !ch->CanHandleItem() ||
				ch->GetExchange() || ch->GetMyShop())
			return;
		TPlayerBotSurviveBot& b = s_mapPlayerBotSurvive[ch->GetPlayerID()];
		if ((int)(dwNow - b.dwNextBoosterLook) < 0)
			return;
		b.dwNextBoosterLook = dwNow + PLAYERBOT_SURVIVE_BOOSTER_LOOK_MS + (DWORD)number(0, 30000);
		bool onGround = false;
		if (!IsPlayerBotSurviveHunter(ch, state, onGround))
			return;
		// a death in the last hour: the defence first
		while (!b.deaths.empty() && dwNow - b.deaths.front().first >= PLAYERBOT_SURVIVE_DEATH_WINDOW_MS)
			b.deaths.pop_front();
		const bool struggling = !b.deaths.empty() || !b.hard.empty();
		const DWORD order[2] = { struggling ? PLAYERBOT_SURVIVE_DEFENCE : PLAYERBOT_SURVIVE_ATTACK,
				struggling ? PLAYERBOT_SURVIVE_ATTACK : PLAYERBOT_SURVIVE_DEFENCE };
		// drunk on the hunting ground, before the first blow (the fight's own pass drinks what is left)
		if (onGround)
			for (int i = 0; i < 2; ++i)
			{
				if (IsPlayerBotSurviveBoosterRunning(ch, order[i]))
					continue;
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
				{
					LPITEM item = ch->GetInventoryItem(cell);
					if (!item || item->GetVnum() != order[i] || item->isLocked() || IsPlayerBotSidekickHeld(ch, item))
						continue;
					if (ch->UseItem(TItemPos(INVENTORY, cell)))
					{
						++s_kPlayerBotSurvive.boostersDrunk;
						PlayerBotLogThrottled("survive_booster_drunk", dwNow,
								"PLAYERBOT_SURVIVE: booster drunk pid=%u name=%s level=%u map=%ld vnum=%u",
								ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), order[i]);
					}
					break;
				}
			}
		if (GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled())
			return;
		if (dwNow - b.dwBoosterDay >= PLAYERBOT_SURVIVE_BOOSTER_DAY_MS)
		{
			b.dwBoosterDay = dwNow ? dwNow : 1;
			b.iBoosterSpent = 0;
		}
		bool refreshed = false;
		for (int i = 0; i < 2; ++i)
		{
			const DWORD vnum = order[i];
			if (ch->CountSpecifyItem(vnum) > 0 || IsPlayerBotSurviveBoosterRunning(ch, vnum))
				continue;
			if (!refreshed)
			{
				RefreshPlayerBotItemShopCatalogue(dwNow);
				EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
				refreshed = true;
			}
			std::vector<const TPlayerBotItemShopEntry*> lines;
			SortPlayerBotIshop3Lines(ch, vnum, true, lines);
			if (lines.empty())
				continue;
			const int budget = std::min(s_iDayMax, std::max(0, (state.iDragonMarks - PLAYERBOT_SURVIVE_BOOSTER_MARKS_RESERVE) / 4));
			if (b.iBoosterSpent + (int)lines[0]->dwPrice > budget)
			{
				++s_kPlayerBotSurvive.budgetHits;
				return;
			}
			if (!BuyPlayerBotIshop3Line(ch, state, *lines[0], vnum, true, 1, "survive_booster", dwNow))
				return;
			b.iBoosterSpent += (int)lines[0]->dwPrice;
			++s_kPlayerBotSurvive.boostersBought;
			PlayerBotLogThrottled("survive_booster_bought", dwNow,
					"PLAYERBOT_SURVIVE: booster bought pid=%u name=%s level=%u vnum=%u why=%s spent_today=%d budget=%d marks=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), vnum, struggling ? "deaths" : "hunt",
					b.iBoosterSpent, budget, state.iDragonMarks);
		}
#else
		(void)ch;
		(void)state;
		(void)dwNow;
#endif
	}

	// ------------------------------------------------------------ the tick and the census

	void ManagePlayerBotDeathloop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow);	// playerbot_deathloop.h

	void ReportPlayerBotSurvive(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		if (s_dwNext == 0)
			s_dwNext = dwNow + PLAYERBOT_SURVIVE_CENSUS_MS;
		if ((int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_SURVIVE_CENSUS_MS;
		unsigned int stepped = 0;
		for (std::map<DWORD, TPlayerBotSurviveBot>::const_iterator it = s_mapPlayerBotSurvive.begin();
				it != s_mapPlayerBotSurvive.end(); ++it)
			stepped += it->second.hard.empty() ? 0U : 1U;
		const TPlayerBotSurviveStats& s = s_kPlayerBotSurvive;
		sys_log(0, "PLAYERBOT_SURVIVE: census tier=%d stepdown=%d ring=%d booster=%d tier_picks=%u tier_project_hits=%u "
				"step_downs=%u step_backs=%u stepped_now=%u farm_orders=%u rings_listed=%u boosters_bought=%u "
				"boosters_drunk=%u booster_budget_hits=%u",
				IsPlayerBotSurviveOn(SURVIVE_TIER) ? 1 : 0, IsPlayerBotSurviveOn(SURVIVE_STEPDOWN) ? 1 : 0,
				IsPlayerBotSurviveOn(SURVIVE_RING) ? 1 : 0, IsPlayerBotSurviveOn(SURVIVE_BOOSTER) ? 1 : 0,
				s.tierPicks, s.tierProjects, s.stepDowns, s.stepBacks, stepped, s.farmOrders, s.ringsListed,
				s.boostersBought, s.boostersDrunk, s.budgetHits);
		s_kPlayerBotSurvive = TPlayerBotSurviveStats();
	}

	void ManagePlayerBotSurvive(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		ReportPlayerBotSurvive(dwNow);
		if (!ch)
			return;
#if defined(PLAYERBOT_ENGINE_MT2009)
		// the deaths at a player's hands so far, so the first death after a start is told apart too
		{
			TPlayerBotSurviveBot& b = s_mapPlayerBotSurvive[ch->GetPlayerID()];
			if (b.llPlayerDeaths < 0 && !ch->IsDead())
				b.llPlayerDeaths = ch->GetSpecialFlag((DWORD)PLAYER_STATS_DEATH_FROM_PLAYER_FLAG);
		}
#endif
		ManagePlayerBotSurviveBoosters(ch, state, dwNow);
		ManagePlayerBotDeathloop(ch, state, dwNow);	// MT2009_PLUS_BOT_DEATHLOOP_V1 (playerbot_deathloop.h, next)
	}
}

#endif
